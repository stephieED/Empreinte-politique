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


def download_with_watchdog(
    url: str,
    dest_path: Path,
    *,
    headers: dict[str, str],
    timeout: Any,
    hard_timeout_seconds: int = DEFAULT_HARD_TIMEOUT_SECONDS,
    chunk_size: int = 1024 * 1024,
) -> None:
    """Télécharge `url` (streaming) vers `dest_path`, protégé par un budget mur
    total indépendant du timeout `requests` passé en argument.

    Écrit d'abord dans un fichier temporaire (`dest_path` + `.part`), renommé
    vers `dest_path` seulement en cas de succès complet : si le budget mur est
    dépassé, le thread démon abandonné peut continuer d'écrire en arrière-plan
    (impossible à interrompre depuis Python) sans jamais corrompre un
    `dest_path` déjà considéré comme absent/en échec par l'appelant.

    Lève l'exception rencontrée (`requests.RequestException`, `OSError`) ou
    `TimeoutError` si le budget mur est dépassé — à l'appelant de catcher,
    même pattern que les appels `requests.get` directs qu'elle remplace.
    """
    tmp_path = dest_path.with_name(dest_path.name + ".part")
    outcome: "queue.Queue[tuple[bool, Any]]" = queue.Queue(maxsize=1)

    def _worker() -> None:
        try:
            with requests.get(url, headers=headers, timeout=timeout, stream=True) as resp:
                resp.raise_for_status()
                with open(tmp_path, "wb") as out:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if chunk:
                            out.write(chunk)
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
