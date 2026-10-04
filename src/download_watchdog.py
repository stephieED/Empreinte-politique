"""Téléchargement de fichier protégé par un budget mur (watchdog) indépendant
du timeout `requests` (#370).

Généralise le pattern déjà en place sur `candidate_profile.py::_get_with_watchdog`
(#340, voir docs/decisions/resilience-generate-data-shutdown-signal.md#get-payload-retry) aux téléchargements
de fichier en streaming, partagé entre les modules qui en ont besoin
(`candidate_profile.py`, `gouvernement_textes.py`, `parltrack_dumps.py`,
`mep_profile.py`, `syceron_debates.py`). Module dédié plutôt que réexporté
depuis l'un des appelants, pour éviter une dépendance circulaire
(`candidate_profile.py` importe déjà `gouvernement_textes.py`/
`syceron_debates.py`).
"""

from __future__ import annotations

import queue
import threading
from pathlib import Path
from typing import Any

import requests

# Budget mur par défaut : suffisant pour un fichier de quelques Mo à
# quelques dizaines de Mo en bande passante CI normale. Les appelants dont le
# fichier attendu fait plusieurs centaines de Mo (ParlTrack, MEP) doivent
# passer un `hard_timeout_seconds` plus généreux explicitement.
DEFAULT_HARD_TIMEOUT_SECONDS = 120


#: Ce qu'une coupure EN COURS de transfert lève : la connexion est rompue alors
#: que des octets sont déjà arrivés. Une erreur HTTP (`HTTPError`) n'en est pas
#: une — reprendre ne la corrigerait pas.
_COUPURES = (
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.ConnectionError,
    requests.exceptions.ReadTimeout,
)


def _taille_annoncee(resp: Any) -> int | None:
    """`Content-Length` d'une réponse complète, ou `None` si le serveur ne
    l'annonce pas ou compresse le corps (la taille lue ne s'y compare plus)."""
    en_tetes = getattr(resp, "headers", None) or {}
    if en_tetes.get("Content-Encoding"):
        return None
    try:
        return int(en_tetes["Content-Length"])
    except (KeyError, TypeError, ValueError):
        return None


def _reprend_a(resp: Any, octet: int) -> bool:
    """Le serveur a-t-il repris EXACTEMENT à `octet` ? (`206` et `Content-Range`)"""
    if getattr(resp, "status_code", None) != 206:
        return False
    plage = (getattr(resp, "headers", None) or {}).get("Content-Range", "")
    return plage.startswith(f"bytes {octet}-")


def download_with_watchdog(
    url: str,
    dest_path: Path,
    *,
    headers: dict[str, str],
    timeout: Any,
    hard_timeout_seconds: int = DEFAULT_HARD_TIMEOUT_SECONDS,
    chunk_size: int = 1024 * 1024,
    reprises: int = 0,
) -> None:
    """Télécharge `url` (streaming) vers `dest_path`, protégé par un budget mur
    total indépendant du timeout `requests` passé en argument.

    Écrit d'abord dans un fichier temporaire (`dest_path` + `.part`), renommé
    vers `dest_path` seulement en cas de succès complet : si le budget mur est
    dépassé, le thread démon abandonné peut continuer d'écrire en arrière-plan
    (impossible à interrompre depuis Python) sans jamais corrompre un
    `dest_path` déjà considéré comme absent/en échec par l'appelant.

    `reprises` (#1202) : nombre de fois où un transfert COUPÉ en cours de route
    est repris là où il s'est arrêté, par `Range: bytes=<déjà écrit>-`, au lieu
    d'être perdu. `0` par défaut : les appelants existants ne changent pas. Le
    budget mur couvre l'ensemble des essais, il ne se multiplie pas. Si le
    serveur ignore `Range` (réponse `200`) ou reprend ailleurs, le fichier
    repart de zéro ; et la taille finale est comparée à celle que le serveur a
    annoncée — un fichier incomplet n'est jamais publié sous `dest_path`.

    Lève l'exception rencontrée (`requests.RequestException`, `OSError`) ou
    `TimeoutError` si le budget mur est dépassé — à l'appelant de catcher,
    même pattern que les appels `requests.get` directs qu'elle remplace.
    """
    tmp_path = dest_path.with_name(dest_path.name + ".part")
    outcome: "queue.Queue[tuple[bool, Any]]" = queue.Queue(maxsize=1)

    def _worker() -> None:
        ecrits = 0                      # octets déjà dans `tmp_path`
        attendus: int | None = None     # taille totale annoncée par le serveur
        essais_restants = reprises
        try:
            while True:
                en_tetes = dict(headers)
                if ecrits:
                    en_tetes["Range"] = f"bytes={ecrits}-"
                try:
                    with requests.get(url, headers=en_tetes, timeout=timeout, stream=True) as resp:
                        resp.raise_for_status()
                        if ecrits and not _reprend_a(resp, ecrits):
                            ecrits = 0          # `Range` ignoré : on repart de zéro
                        if not ecrits:
                            attendus = _taille_annoncee(resp)
                        with open(tmp_path, "ab" if ecrits else "wb") as out:
                            for chunk in resp.iter_content(chunk_size=chunk_size):
                                if chunk:
                                    out.write(chunk)
                                    ecrits += len(chunk)
                    if reprises and attendus is not None and ecrits != attendus:
                        raise requests.exceptions.ChunkedEncodingError(
                            f"transfert incomplet : {ecrits} octets sur {attendus}")
                    break
                except _COUPURES as exc:
                    if essais_restants <= 0:
                        raise
                    essais_restants -= 1
                    print(f"  [i] Transfert coupé à {ecrits} octets ({type(exc).__name__}) : "
                          f"reprise, {essais_restants} essai(s) restant(s).")
            outcome.put((True, None))
        except Exception as exc:  # relayé tel quel au thread appelant
            outcome.put((False, exc))

    threading.Thread(target=_worker, daemon=True).start()
    try:
        ok, err = outcome.get(timeout=hard_timeout_seconds)
    except queue.Empty:
        raise TimeoutError(
            f"Aucune réponse de {url} après {hard_timeout_seconds}s "
            "(budget mur du watchdog dépassé — probable blocage DNS/réseau non "
            "couvert par timeout= de requests)"
        ) from None
    if not ok:
        raise err
    tmp_path.replace(dest_path)
