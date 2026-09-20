#!/usr/bin/env python3
"""
parltrack_dumps.py — Accès aux dumps ParlTrack (.zst) pour l'extraction
de données parlementaires européennes par MEP ID.

ParlTrack (https://parltrack.org) publie **huit** dumps JSON compressés
Zstandard. Ce module en lit cinq :

  - ep_dossiers.json.zst           : dossiers législatifs (rapporteurs, comités)
  - ep_plenary_amendments.json.zst : amendements en séance plénière
  - ep_amendments.json.zst         : amendements en commission
  - ep_votes.json.zst              : scrutins nominatifs en séance (#683)
  - ep_mep_activities.json.zst     : interventions, questions, explications de
                                     vote, propositions de résolution (#683)

Les trois autres restent hors périmètre, et pour des raisons mesurées :
`ep_meps` fait doublon avec le portail officiel du PE, d'où le pipeline tire
déjà identité et mandats ; `ep_com_votes` porte **89 scrutins en tout** ;
`ep_comagendas` ne nomme personne.

Les dumps sont mis en cache localement sous .cache/parltrack/ pour éviter
un re-téléchargement complet à chaque exécution.

Licence données ParlTrack : ODbL v1.0 (Open Database License).
Voir https://parltrack.org/dumps pour les informations de fraîcheur.

## Les trois décisions à lire avant de toucher ce module

Cinq le gouvernent (`docs/decisions-par-module.md`) ; ces trois-là suffisent à
ne pas se tromper :

- `docs/decisions/lecture-dumps-parltrack-683.md` — **le format**. Un dump est
  un seul tableau JSON, séparateur en tête de ligne, et l'avoir lu comme du
  NDJSON pendant toute la vie du module a produit des index de 2 octets en face
  de 182 Mio de dumps, sans qu'une ligne d'erreur le dise.
- `docs/decisions/deux-fabriques-textes-portes-europeens-901.md` — pourquoi
  `build_stades_dossiers_index` existe à côté de `build_dossiers_index`, et ce
  que leurs questions ont de différent.
- `docs/decisions/stade-procedural-europeen-901.md` — pourquoi `stade_source`
  est conservé **brut** par l'indexeur : la traduction vers la nomenclature
  pivot est le travail du normaliseur.

Usage (depuis la racine du dépôt) :
    from parltrack_dumps import get_dossiers_for_mep, get_amendments_for_mep
    dossiers = get_dossiers_for_mep(131580)
    amendments = get_amendments_for_mep(131580)
"""

import hashlib
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

import requests
import zstandard as zstd

from download_watchdog import download_with_watchdog
from titres_europeens import titre_sans_boutons  # noqa: F401 (réexportée, ses appelants la lisent ici)

PARLTRACK_DUMPS_BASE = "https://parltrack.org/dumps"

PARLTRACK_CACHE_DIR = Path(".cache") / "parltrack"

_DUMP_DOSSIERS = "ep_dossiers.json.zst"
_DUMP_PLENARY_AMENDMENTS = "ep_plenary_amendments.json.zst"
_DUMP_COMMITTEE_AMENDMENTS = "ep_amendments.json.zst"
_DUMP_VOTES = "ep_votes.json.zst"
_DUMP_ACTIVITIES = "ep_mep_activities.json.zst"

#: Les dumps que ce module lit, dans l'ordre de téléchargement. **Une seule
#: définition**, lue par `extract-parltrack` : recopiée dans le YAML, la liste
#: aurait divergé du jour où un sixième dump entre ici, et le fichier absent
#: serait arrivé à la fusion sous la forme d'une liste vide (#510).
DUMPS_LUS: tuple[str, ...] = (
    _DUMP_DOSSIERS,
    _DUMP_PLENARY_AMENDMENTS,
    _DUMP_COMMITTEE_AMENDMENTS,
    _DUMP_VOTES,
    _DUMP_ACTIVITIES,
)

HEADERS = {
    "User-Agent": "cv-politique-parltrack-dumps/0.1 (usage personnel / non commercial)"
}
TIMEOUT = 120  # Les dumps font plusieurs centaines de Mo


# ---------------------------------------------------------------------------
# Téléchargement et cache
# ---------------------------------------------------------------------------


# Budget mur généreux (#370) : ces dumps font plusieurs centaines de Mo
# (contrairement au défaut de download_with_watchdog, dimensionné pour des
# fichiers de quelques Mo) — 900s laisse la marge nécessaire à un
# téléchargement légitimement long, tout en bornant un blocage silencieux
# qui, avant #370, pouvait durer indéfiniment (aucune protection).
_DUMP_DOWNLOAD_HARD_TIMEOUT_SECONDS = 900


def _download_dump(dump_name: str, dest: Path) -> bool:
    """Télécharge un dump ParlTrack et le sauvegarde localement.

    Returns:
        True si le téléchargement a réussi, False sinon.
    """
    url = f"{PARLTRACK_DUMPS_BASE}/{dump_name}"
    print(f"→ Téléchargement du dump ParlTrack : {url}")
    print("  (peut prendre plusieurs minutes — plusieurs centaines de Mo)")
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        download_with_watchdog(
            url, dest, headers=HEADERS, timeout=TIMEOUT,
            hard_timeout_seconds=_DUMP_DOWNLOAD_HARD_TIMEOUT_SECONDS, chunk_size=1024 * 256,
        )
        print(f"  ✓ Dump sauvegardé : {dest}")
        return True
    except (requests.RequestException, OSError, TimeoutError) as exc:
        print(f"  [!] Échec du téléchargement : {exc}", file=sys.stderr)
        return False


def ensure_dump(dump_name: str, force_download: bool = False) -> Optional[Path]:
    """Assure que le dump est disponible localement.

    Args:
        dump_name: nom du fichier dump (ex. "ep_dossiers.json.zst").
        force_download: si True, re-télécharge même si un cache existe.

    Returns:
        Chemin vers le fichier .zst, ou None si indisponible.
    """
    dest = PARLTRACK_CACHE_DIR / dump_name
    if not force_download and dest.is_file():
        mtime = dest.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        print(f"  Dump {dump_name} en cache (âge : {age_days:.0f} j). "
              "Utiliser force_download=True pour rafraîchir.")
        return dest

    if _download_dump(dump_name, dest):
        return dest
    return None


# ---------------------------------------------------------------------------
# Lecture des dumps .zst (streaming)
# ---------------------------------------------------------------------------


class DumpParltrackIllisible(RuntimeError):
    """Un dump non vide n'a produit aucun enregistrement.

    Levée, jamais avalée : c'est la seule chose qui distingue « ParlTrack ne
    connaît personne » de « nous ne savons plus lire le fichier ». Sans elle,
    la panne se publie comme un constat sur la personne (§2 règle 5, #484).
    """


def iter_dump_zst(
    path: Path, lignes: Optional[list[int]] = None
) -> Iterator[dict[str, Any]]:
    """Lit en flux un dump ParlTrack compressé Zstandard.

    ## Le format, et l'incident (#683)

    Ce module a lu ces dumps comme du **NDJSON** — un objet JSON complet par
    ligne — pendant toute sa vie. Ce n'est pas ce que ParlTrack publie. La page
    https://parltrack.org/dumps le dit en toutes lettres :

        « you can read the uncompressed JSON line-by-line, strip of the first
        character and process the rest of the line as JSON, you can stop
        processing if after stripping the first character an empty string
        remains, this means the end of the JSON stream. »

    Un dump est **un seul tableau JSON**, un objet par ligne, le séparateur en
    **tête** de ligne : la première commence par ``[``, les suivantes par ``,``,
    la dernière est ``]`` seul. `json.loads` échouait donc sur chaque ligne, et
    l'échec partait dans un `except JSONDecodeError: continue`. Résultat mesuré
    le 09/09/2026 : `.cache/parltrack/index_*.json` faisaient **2 octets** —
    `{}` — en face de 182 Mio de dumps, et les 7 candidats déclarés à mandat
    européen publiaient « aucune donnée trouvée » **sur eux**.

    Le `continue` sur ligne illisible est conservé — une ligne tronquée ne doit
    pas perdre le dump entier — mais il ne suffit plus : c'est
    `DumpParltrackIllisible`, levée par les indexeurs quand un dump non vide ne
    rend **rien**, qui empêche la panne de repasser pour une absence.

    Args:
        path: le dump `.zst`.
        lignes: compteur à un élément, incrémenté pour chaque ligne PORTANT un
            enregistrement — illisible comprise. C'est lui qui permet à
            `_lire_dump` de distinguer « le dump est vide » de « le dump est
            plein et nous n'y comprenons rien ».

    Yields:
        Un dict Python par enregistrement du tableau.
    """
    if lignes is None:
        lignes = [0]
    dctx = zstd.ZstdDecompressor()
    with open(path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            for ligne in io.TextIOWrapper(reader, encoding="utf-8"):
                brut = ligne.strip()
                if not brut:
                    # Ligne vide : elle ne porte pas de séparateur, donc elle
                    # n'annonce pas la fin du flux. On l'ignore, on ne s'arrête
                    # pas dessus.
                    continue
                enregistrement = brut[1:]
                if not enregistrement or enregistrement == "]":
                    # « ] » seul : fin du tableau, telle que la source la décrit.
                    # « [] » : un dump légitimement vide, dont il reste « ] »
                    # après le retrait du premier caractère. Les deux disent la
                    # même chose — le flux est fini — et aucun n'est une panne.
                    return
                lignes[0] += 1
                try:
                    yield json.loads(enregistrement)
                except json.JSONDecodeError:
                    continue


def _lire_dump(dump_path: Path, dump_name: str) -> Iterator[dict[str, Any]]:
    """`iter_dump_zst`, plus la garde « un dump non vide rend quelque chose ».

    La garde vit ici et pas dans le lecteur parce qu'un générateur qui lève à
    l'épuisement ne dit rien à qui l'interrompt : ce sont les indexeurs, qui
    consomment tout, qui peuvent conclure.
    """
    lignes = [0]
    lus = 0
    for enregistrement in iter_dump_zst(dump_path, lignes):
        lus += 1
        yield enregistrement
    if lus == 0 and lignes[0] > 0:
        raise DumpParltrackIllisible(
            f"{dump_name} : {lignes[0]} ligne(s) porteuse(s), 0 enregistrement lu. "
            "Le format publié par parltrack.org a probablement changé — "
            "voir iter_dump_zst."
        )


# ---------------------------------------------------------------------------
# Résolution des mepref (format numérique + format hash historique)
# ---------------------------------------------------------------------------


def _resolve_mepref_as_int(mepref: Any) -> Optional[int]:
    """Tente de convertir un `mepref` (champ des dossiers ParlTrack) en
    entier UserID.

    ParlTrack contient deux formats :
    - Format moderne (majoritaire) : entier (ex. 131580) ou chaîne entière.
    - Format hash historique : chaîne hexadécimale de 24 caractères (ex.
      "5479da7eb01f9fc4c71bb6a1"), non convertible directement.

    Returns:
        L'entier UserID si convertible, None sinon (hash historique ou
        valeur inattendue).
    """
    if mepref is None:
        return None
    if isinstance(mepref, int):
        return mepref
    try:
        return int(mepref)
    except (ValueError, TypeError):
        return None  # Hash historique non résolvable sans table de correspondance


# ---------------------------------------------------------------------------
# Le périmètre, et pourquoi il est obligatoire (#683)
# ---------------------------------------------------------------------------

#: Périmètre courant : les UserID ParlTrack pour lesquels les index sont
#: construits. `None` signifie « celui que l'appelant demande, et lui seul ».
#:
#: **Ce n'est pas une optimisation, c'est ce qui rend le correctif tenable.**
#: Mesuré le 09/09/2026 sur les dumps publiés : indexer les amendements de
#: TOUS les eurodéputés produit **2 675 293 entrées**, soit ~0,5 Go de JSON
#: écrits dans `.cache/parltrack/`, mis en cache par le workflow et téléversés
#: en artifact à chaque run. Le défaut d'origine ne s'en apercevait pas :
#: l'index sortait vide, donc gratuit.
_PERIMETRE_MEPS: Optional[frozenset[int]] = None


def definir_perimetre_meps(mep_ids: Optional[Iterable[int]]) -> None:
    """Fixe le périmètre d'indexation pour la suite du processus.

    Appelée **une fois** par le pipeline, avec l'ensemble des identifiants
    européens à publier. Sans elle, chaque appelant fait construire un index
    pour lui seul — correct, mais autant de relectures du dump que de personnes.
    """
    global _PERIMETRE_MEPS
    _PERIMETRE_MEPS = None if mep_ids is None else frozenset(int(m) for m in mep_ids)


def _perimetre(mep_id: Optional[int] = None) -> frozenset[int]:
    """Le périmètre effectif : celui qui a été défini, **union** la personne demandée.

    L'union n'est pas une précaution de style. Rendre le périmètre défini tel
    quel ferait qu'une personne absente de ce périmètre — un candidat européen
    déclaré après coup, par exemple — recevrait un index qui ne la contient
    pas, donc une liste vide, donc un constat sur elle (#510). Avec l'union,
    elle coûte une reconstruction d'index ; sans, elle coûte un fait faux.
    """
    demande = frozenset({int(mep_id)}) if mep_id is not None else frozenset()
    return (_PERIMETRE_MEPS or frozenset()) | demande


#: Version du **schéma** des entrées d'index, versée dans le nom du fichier.
#:
#: L'empreinte ne portait que le périmètre, et c'est un cas qu'elle ne couvrait
#: pas : quand une entrée d'index gagne un champ, un cache écrit par la version
#: précédente reste lisible, se relit sans erreur, et rend le nouveau champ
#: **absent partout**. Un stade nul se lirait alors comme « la source ne le
#: publie pas » — le contraire de ce que #901 vient d'établir.
#:
#: L'incrémenter à chaque changement de forme d'une entrée. C'est le même geste
#: que l'empreinte de périmètre : faire rater le cache plutôt que le faire
#: mentir (#510).
#:
#:   2 — #901 : `stade_source` sur les entrées de `build_dossiers_index`.
#:   3 — #901 : `dossiers` sur les entrées de `build_activities_index`. Sans
#:       cette incrémentation le correctif n'atteindrait aucun run : le cache
#:       `public-data-cache-parltrack-<semaine>` restaure l'index déjà bâti, et
#:       `build_activities_index` le relit tant que sa date dépasse celle du
#:       dump — qui, lui, n'est pas retéléchargé. Le code aurait été juste et le
#:       corpus inchangé, une semaine durant.
#:   4 — #901 : le titre d'une activité perd la queue de boutons de
#:       téléchargement que ParlTrack scrape avec lui. Même raison qu'au 3 : un
#:       index caché resservirait les titres pollués.
VERSION_SCHEMA_INDEX = 4


def _empreinte_perimetre(perimetre: frozenset[int]) -> str:
    """Empreinte courte du périmètre et du schéma, portée par le NOM du fichier.

    Même geste qu'au #505 pour les caches de collecte : un index construit pour
    3 personnes et relu pour 7 rendrait quatre listes vides, et quatre listes
    vides se lisent comme quatre constats (#510). L'empreinte fait rater le
    cache au lieu de le faire mentir.
    """
    if not perimetre:
        return f"v{VERSION_SCHEMA_INDEX}-tous"
    empreinte = hashlib.sha256(
        ",".join(str(m) for m in sorted(perimetre)).encode("utf-8")
    ).hexdigest()
    return f"v{VERSION_SCHEMA_INDEX}-{len(perimetre)}-{empreinte[:12]}"


# ---------------------------------------------------------------------------
# Index dossiers (rapporteur) : mep_id → liste de dossiers
# ---------------------------------------------------------------------------


def build_dossiers_index(
    force_download: bool = False,
    perimetre: Optional[frozenset[int]] = None,
) -> dict[int, list[dict[str, Any]]]:
    """Construit un index UserID → liste de dossiers où le MEP est rapporteur.

    L'index est mis en cache sur disque pour éviter de reconstruire à chaque
    appel.

    Returns:
        dict mep_id (int) → liste de dossiers (avec référence, titre, comité,
        date, source_url).
    """
    perimetre = _perimetre() if perimetre is None else perimetre
    index_path = (
        PARLTRACK_CACHE_DIR
        / f"index_dossiers_rapporteur-{_empreinte_perimetre(perimetre)}.json"
    )
    dump_path = ensure_dump(_DUMP_DOSSIERS, force_download)
    if dump_path is None:
        return {}

    if (
        not force_download
        and index_path.is_file()
        and index_path.stat().st_mtime >= dump_path.stat().st_mtime
    ):
        try:
            with open(index_path, encoding="utf-8") as f:
                raw = json.load(f)
            return {int(k): v for k, v in raw.items()}
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    index: dict[int, list[dict[str, Any]]] = {}
    warnings: list[str] = []
    print("→ Indexation des dossiers ParlTrack (rapporteurs)…")
    for dossier in _lire_dump(dump_path, _DUMP_DOSSIERS):
        procedure = dossier.get("procedure") or {}
        reference = procedure.get("reference") or ""
        titre = procedure.get("title") or procedure.get("subject") or ""
        url = dossier.get("meta", {}).get("source") or f"https://parltrack.org/dossier/{reference}"
        committees = dossier.get("committees") or []
        for committee in committees:
            rapporteurs = committee.get("rapporteur") or []
            committee_name = committee.get("committee") or committee.get("committee_full") or ""
            for rap in rapporteurs:
                mepref = rap.get("mepref")
                date = rap.get("date") or ""
                uid = _resolve_mepref_as_int(mepref)
                if uid is None:
                    if mepref:
                        warnings.append(f"mepref non résolvable : {mepref!r} (dossier {reference!r})")
                    continue
                if perimetre and uid not in perimetre:
                    continue
                index.setdefault(uid, []).append({
                    "reference": reference,
                    "titre": titre,
                    "comite": committee_name,
                    "role": "rapporteur",
                    "date": date[:10] if date else None,
                    "source_url": url,
                    # #901 — `procedure.stage_reached`, tel que la source
                    # l'écrit. Il était lu ici puis jeté, et les 383 textes
                    # portés européens publiaient `stade_procedural: null`.
                    # Mesuré le 13/09/2026 sur le dump entier : 20 442 des
                    # 23 885 dossiers en portent un (85,6 %), sur 16 valeurs.
                    # Conservé BRUT : la traduction vers la nomenclature pivot
                    # est le travail du normaliseur, pas de l'indexeur.
                    "stade_source": procedure.get("stage_reached") or None,
                })

    if warnings:
        print(f"  [!] {len(warnings)} mepref non résolvable(s) (format hash historique ignoré).",
              file=sys.stderr)

    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in index.items()}, f, ensure_ascii=False)
        print(f"  ✓ Index dossiers sauvegardé : {index_path}")
    except OSError:
        pass

    return index


# ---------------------------------------------------------------------------
# Index amendements : mep_id → liste d'amendements
# ---------------------------------------------------------------------------


def _index_amendments_from_dump(
    dump_name: str,
    source_label: str,
    force_download: bool = False,
    perimetre: frozenset[int] = frozenset(),
) -> tuple[dict[int, list[dict[str, Any]]], list[str]]:
    """Construit l'index mep_id → amendements depuis un dump donné.

    Returns:
        (index, warnings) — index dict et liste d'avertissements non bloquants.
    """
    dump_path = ensure_dump(dump_name, force_download)
    if dump_path is None:
        return {}, [f"Dump indisponible : {dump_name}"]

    index: dict[int, list[dict[str, Any]]] = {}
    warnings: list[str] = []
    for amd in _lire_dump(dump_path, dump_name):
        amd_id = amd.get("id") or ""
        reference = amd.get("reference") or ""
        date = amd.get("date") or ""
        committee = None
        if isinstance(amd.get("committee"), list):
            committee = ", ".join(amd["committee"])
        elif isinstance(amd.get("committee"), str):
            committee = amd["committee"]
        source_url = (
            amd.get("meta", {}).get("source")
            or f"https://parltrack.org/amendments/{amd_id}"
        )
        meps = amd.get("meps") or []
        if not isinstance(meps, list):
            meps = [meps]
        signataires = [uid for uid in (_resolve_mepref_as_int(m) for m in meps) if uid is not None]
        for mepref in meps:
            uid = _resolve_mepref_as_int(mepref)
            if uid is None:
                if mepref:
                    warnings.append(f"mepref non résolvable : {mepref!r} (amendement {amd_id!r})")
                continue
            if perimetre and uid not in perimetre:
                continue
            index.setdefault(uid, []).append({
                "id": amd_id,
                "reference": reference,
                "comite": committee,
                "date": date[:10] if date else None,
                "source": source_label,
                "source_url": source_url,
                # #683 — de quoi qualifier la signature SANS inventer : le
                # nombre de signataires, et le nom que la source met en tête.
                # `normalize_parltrack_dumps` en tire `role_signataire`.
                "nb_signataires": len(signataires),
                "premier_auteur": (amd.get("authors") or "").split(",")[0].strip() or None,
            })
    return index, warnings


def build_amendments_index(
    force_download: bool = False,
    perimetre: Optional[frozenset[int]] = None,
) -> dict[int, list[dict[str, Any]]]:
    """Construit un index UserID → amendements (plénière + comité fusionnés).

    L'index est mis en cache sur disque.

    Returns:
        dict mep_id (int) → liste d'amendements.
    """
    perimetre = _perimetre() if perimetre is None else perimetre
    index_path = (
        PARLTRACK_CACHE_DIR
        / f"index_amendements_par_mep-{_empreinte_perimetre(perimetre)}.json"
    )

    plenary_path = PARLTRACK_CACHE_DIR / _DUMP_PLENARY_AMENDMENTS
    committee_path = PARLTRACK_CACHE_DIR / _DUMP_COMMITTEE_AMENDMENTS

    # Vérification de cache : valide uniquement si plus récent que les deux dumps
    if not force_download and index_path.is_file():
        oldest_dump_mtime = None
        for p in [plenary_path, committee_path]:
            if p.is_file():
                t = p.stat().st_mtime
                if oldest_dump_mtime is None or t < oldest_dump_mtime:
                    oldest_dump_mtime = t
        if oldest_dump_mtime is not None and index_path.stat().st_mtime >= oldest_dump_mtime:
            try:
                with open(index_path, encoding="utf-8") as f:
                    raw = json.load(f)
                return {int(k): v for k, v in raw.items()}
            except (json.JSONDecodeError, OSError, ValueError):
                pass

    print("→ Indexation des amendements ParlTrack (plénière + comité)…")
    index: dict[int, list[dict[str, Any]]] = {}
    all_warnings: list[str] = []

    plenary_idx, pw = _index_amendments_from_dump(
        _DUMP_PLENARY_AMENDMENTS, "plenary", force_download, perimetre
    )
    all_warnings.extend(pw)
    for uid, amds in plenary_idx.items():
        index.setdefault(uid, []).extend(amds)

    committee_idx, cw = _index_amendments_from_dump(
        _DUMP_COMMITTEE_AMENDMENTS, "committee", force_download, perimetre
    )
    all_warnings.extend(cw)
    for uid, amds in committee_idx.items():
        index.setdefault(uid, []).extend(amds)

    if all_warnings:
        print(f"  [!] {len(all_warnings)} mepref non résolvable(s) ignoré(s).",
              file=sys.stderr)

    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in index.items()}, f, ensure_ascii=False)
        print(f"  ✓ Index amendements sauvegardé : {index_path}")
    except OSError:
        pass

    return index


# ---------------------------------------------------------------------------
# API publique : extraction par mep_id
# ---------------------------------------------------------------------------


def get_dossiers_for_mep(
    mep_id: int,
    force_download: bool = False,
) -> list[dict[str, Any]]:
    """Retourne la liste des dossiers où le MEP est rapporteur.

    Args:
        mep_id: UserID ParlTrack (entier).
        force_download: re-télécharger les dumps même si un cache existe.

    Returns:
        Liste de dicts dossier (reference, titre, comite, role, date,
        source_url).  Liste vide si aucun dossier trouvé ou dump
        indisponible.
    """
    index = build_dossiers_index(force_download, _perimetre(mep_id))
    return index.get(mep_id, [])


def get_amendments_for_mep(
    mep_id: int,
    force_download: bool = False,
) -> list[dict[str, Any]]:
    """Retourne la liste des amendements signés par le MEP.

    Args:
        mep_id: UserID ParlTrack (entier).
        force_download: re-télécharger les dumps même si un cache existe.

    Returns:
        Liste de dicts amendement (id, reference, comite, date, source,
        source_url).  Liste vide si aucun amendement trouvé ou dump
        indisponible.
    """
    index = build_amendments_index(force_download, _perimetre(mep_id))
    return index.get(mep_id, [])


# ---------------------------------------------------------------------------
# Scrutins nominatifs en séance : mep_id → positions (#683)
# ---------------------------------------------------------------------------

#: `ep_votes` note la position par un signe. Correspondance vers le vocabulaire
#: déjà fermé du schéma (`schema_pivot.KNOWN_POSITIONS`) plutôt qu'un second
#: vocabulaire : un vote européen et un vote de l'Assemblée ne s'additionnent
#: pas, mais « pour » veut dire la même chose des deux côtés.
#:
#: Il n'y a **pas** d'entrée pour l'absence : le dump ne liste que les votants.
#: Un député absent n'y figure pas, et son absence ne se publie donc PAS comme
#: `absent` — ce serait un constat que la source ne porte pas (§2 règle 5), et
#: l'assiduité individuelle n'est de toute façon jamais publiée (§2 règle 3).
_POSITIONS_PARLTRACK: dict[str, str] = {
    "+": "pour",
    "-": "contre",
    "0": "abstention",
}


def build_votes_index(
    force_download: bool = False,
    perimetre: Optional[frozenset[int]] = None,
) -> dict[int, list[dict[str, Any]]]:
    """Construit l'index UserID → positions de vote en séance.

    Mesuré le 09/09/2026 : 44 648 scrutins nominatifs, de 2004 au **26/03/2026**
    — le dump n'a pas été régénéré depuis, là où les autres l'ont été le 24/07.
    Cette borne est une donnée du corpus, pas un détail d'exploitation : elle
    doit se retrouver dans `couverture.votes` du profil.
    """
    perimetre = _perimetre() if perimetre is None else perimetre
    index_path = (
        PARLTRACK_CACHE_DIR / f"index_votes_par_mep-{_empreinte_perimetre(perimetre)}.json"
    )
    dump_path = ensure_dump(_DUMP_VOTES, force_download)
    if dump_path is None:
        return {}

    if (
        not force_download
        and index_path.is_file()
        and index_path.stat().st_mtime >= dump_path.stat().st_mtime
    ):
        try:
            with open(index_path, encoding="utf-8") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    print("→ Indexation des scrutins ParlTrack (séance plénière)…")
    index: dict[int, list[dict[str, Any]]] = {}
    sans_detail = 0
    for scrutin in _lire_dump(dump_path, _DUMP_VOTES):
        positions = scrutin.get("votes")
        if not isinstance(positions, dict):
            # Le scrutin existe, son détail nominatif n'est pas publié : 92 cas
            # sur 44 648. C'est un trou de la source, compté et non deviné.
            sans_detail += 1
            continue
        horodatage = scrutin.get("ts") or ""
        entete = {
            "scrutin_id": scrutin.get("voteid"),
            "titre": scrutin.get("title") or "",
            "date": horodatage[:10] or None,
            "source_url": scrutin.get("url"),
            "reference": scrutin.get("epref") or scrutin.get("doc") or None,
        }
        for signe, bloc in positions.items():
            position = _POSITIONS_PARLTRACK.get(signe)
            if position is None or not isinstance(bloc, dict):
                continue
            groupes = bloc.get("groups")
            # `ep_votes` publie un dict {groupe: [votants]} ; d'autres dumps de
            # la même famille publient une liste. Les deux formes sont lues,
            # aucune n'est supposée.
            paires = (
                groupes.items() if isinstance(groupes, dict)
                else ((g.get("group"), g.get("votes") or []) for g in groupes or [])
                if isinstance(groupes, list) else ()
            )
            for groupe, votants in paires:
                for votant in votants or []:
                    uid = _resolve_mepref_as_int(
                        votant.get("mepid") if isinstance(votant, dict) else votant
                    )
                    if uid is None or (perimetre and uid not in perimetre):
                        continue
                    index.setdefault(uid, []).append(
                        {**entete, "position": position, "groupe": groupe}
                    )

    if sans_detail:
        print(f"  · {sans_detail} scrutin(s) sans détail nominatif dans le dump.")
    _ecrire_index(index_path, index)
    return index


# ---------------------------------------------------------------------------
# Activités : interventions, questions, explications de vote (#683)
# ---------------------------------------------------------------------------

#: Les codes d'activité de `ep_mep_activities`, et leur lecture en français.
#: **Fermé** : un code absent d'ici est ignoré et compté, jamais rangé sous une
#: étiquette approchante — c'est la règle des `frozenset KNOWN_*` (§4).
TYPES_ACTIVITE: dict[str, str] = {
    "CRE": "intervention_seance",
    "WEXP": "explication_de_vote_ecrite",
    "WQ": "question_ecrite",
    "OQ": "question_orale",
    "MINT": "interpellation_majeure",
    "MOTION": "proposition_de_resolution",
    "IMOTION": "proposition_de_resolution_individuelle",
    "WDECL": "declaration_ecrite",
    "REPORT": "rapport",
    "REPORT-SHADOW": "rapport_fictif",
    "COMPARL": "avis_de_commission",
    "COMPARL-SHADOW": "avis_de_commission_fictif",
    "PRUNACT": "activite_anterieure",
}


def build_activities_index(
    force_download: bool = False,
    perimetre: Optional[frozenset[int]] = None,
) -> dict[int, dict[str, list[dict[str, Any]]]]:
    """Construit l'index UserID → activités, groupées par type.

    Une entrée porte sa date, son intitulé et **l'URL du document officiel sur
    europarl.europa.eu** : la traçabilité (§2 règle 2) ne repose donc pas sur
    ParlTrack, qui n'est ici qu'un chemin d'accès au document primaire.
    """
    perimetre = _perimetre() if perimetre is None else perimetre
    index_path = (
        PARLTRACK_CACHE_DIR / f"index_activites_par_mep-{_empreinte_perimetre(perimetre)}.json"
    )
    dump_path = ensure_dump(_DUMP_ACTIVITIES, force_download)
    if dump_path is None:
        return {}

    if (
        not force_download
        and index_path.is_file()
        and index_path.stat().st_mtime >= dump_path.stat().st_mtime
    ):
        try:
            with open(index_path, encoding="utf-8") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except (json.JSONDecodeError, OSError, ValueError):
            pass

    print("→ Indexation des activités ParlTrack…")
    index: dict[int, dict[str, list[dict[str, Any]]]] = {}
    codes_inconnus: dict[str, int] = {}
    for fiche in _lire_dump(dump_path, _DUMP_ACTIVITIES):
        uid = _resolve_mepref_as_int(fiche.get("mep_id"))
        if uid is None or (perimetre and uid not in perimetre):
            continue
        for code, entrees in fiche.items():
            if not isinstance(entrees, list) or not entrees:
                continue
            libelle = TYPES_ACTIVITE.get(code)
            if libelle is None:
                codes_inconnus[code] = codes_inconnus.get(code, 0) + len(entrees)
                continue
            for entree in entrees:
                if not isinstance(entree, dict):
                    continue
                date = entree.get("date") or ""
                index.setdefault(uid, {}).setdefault(libelle, []).append({
                    # Nettoyé ICI, à l'entrée du corpus, et une seule fois :
                    # le faire plus loin laisserait chaque consommateur
                    # réinventer sa propre règle, et masquerait le défaut au
                    # lieu de le corriger.
                    "titre": titre_sans_boutons(entree.get("title")),
                    "date": date[:10] or None,
                    "reference": entree.get("reference"),
                    "source_url": entree.get("url"),
                    "legislature": entree.get("term"),
                    # Seules les explications de vote portent un texte : c'est
                    # la personne qui écrit, pas un compte rendu de tiers.
                    "texte": entree.get("text"),
                    # Les références de PROCÉDURE que l'activité vise
                    # (`["2022/2852(RSP)"]`), à ne pas confondre avec
                    # `reference`, qui est celle du DOCUMENT (`B8-0144/2017`).
                    # C'est la seule clé qui permette de retrouver le stade du
                    # dossier, et cette projection la jetait : `_make_texte_
                    # porte_activite` lit cet index et non le dump, si bien que
                    # les 371 textes portés issus d'activités sortaient tous en
                    # `activite_sans_dossier`. Voir #901 et la note de
                    # `_reference_dossier_activite`.
                    "dossiers": entree.get("dossiers"),
                })

    if codes_inconnus:
        print(
            "  [!] codes d'activité non répertoriés, ignorés : "
            + ", ".join(f"{c} ({n})" for c, n in sorted(codes_inconnus.items())),
            file=sys.stderr,
        )
    _ecrire_index(index_path, index)
    return index


def _ecrire_index(index_path: Path, index: dict[int, Any]) -> None:
    """Sauvegarde un index sur disque. Un échec d'écriture ne perd que le cache."""
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in index.items()}, f, ensure_ascii=False)
        print(f"  ✓ Index sauvegardé : {index_path}")
    except OSError:
        pass


def get_votes_for_mep(
    mep_id: int, force_download: bool = False
) -> list[dict[str, Any]]:
    """Les positions de vote en séance de ce député européen."""
    return build_votes_index(force_download, _perimetre(mep_id)).get(mep_id, [])


# ---------------------------------------------------------------------------
# Index des stades de dossier : référence de procédure → stade, tel que la
# source l'écrit
# ---------------------------------------------------------------------------


def build_stades_dossiers_index(force_download: bool = False) -> dict[str, str]:
    """`{reference: stage_reached}` pour tous les dossiers du dump.

    ## Pourquoi cet index existe, alors que `build_dossiers_index` lit déjà ce dump

    Les deux ne répondent pas à la même question. `build_dossiers_index` rend
    « de quels dossiers cette personne est-elle rapporteure », et n'indexe donc
    que ceux où elle l'est. Celui-ci rend « où en est ce dossier », pour une
    référence quelconque — y compris celles que les **activités** citent
    (`REPORT`, `MOTION`, `OPINION`), et dont la personne n'est pas rapporteure
    au sens de `committees[].rapporteur`.

    C'est ce qui manquait à `_make_texte_porte_activite` : elle publiait
    `stade_procedural: None` en dur, et couvrait **371 des 383** textes portés
    européens — 97 %. Le lot du stade (#901) n'avait corrigé que l'autre
    fabrique, celle des dossiers rapporteur, soit 12 entrées.

    L'index est **plat et minuscule** : deux chaînes par dossier, là où
    `build_dossiers_index` garde six champs par entrée. Il n'est pas borné par
    un périmètre de MEP — une référence est une référence.

    Returns:
        `{reference: stade tel que la source l'écrit}`. Une référence sans
        `stage_reached` est **absente** plutôt que rendue avec `None` : la
        distinguer d'une référence inconnue est ce qui permet au normaliseur de
        publier le bon motif (§2 règle 5).
    """
    index_path = (
        PARLTRACK_CACHE_DIR
        / f"index_stades_dossiers-{_empreinte_perimetre(frozenset())}.json"
    )
    dump_path = ensure_dump(_DUMP_DOSSIERS, force_download)
    if dump_path is None:
        return {}
    if index_path.is_file() and index_path.stat().st_mtime >= dump_path.stat().st_mtime:
        try:
            return json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass

    index: dict[str, str] = {}
    print("→ Indexation des stades de dossier ParlTrack…")
    for dossier in _lire_dump(dump_path, _DUMP_DOSSIERS):
        procedure = dossier.get("procedure")
        if not isinstance(procedure, dict):
            continue
        reference = procedure.get("reference")
        stade = procedure.get("stage_reached")
        if reference and stade:
            index[reference] = stade
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ Index stades sauvegardé : {index_path} ({len(index)} dossiers)")
    except OSError:
        pass
    return index


def get_activities_for_mep(
    mep_id: int, force_download: bool = False
) -> dict[str, list[dict[str, Any]]]:
    """Les activités de ce député européen, groupées par type."""
    return build_activities_index(force_download, _perimetre(mep_id)).get(mep_id, {})
