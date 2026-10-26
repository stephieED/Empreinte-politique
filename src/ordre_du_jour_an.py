#!/usr/bin/env python3
"""ordre_du_jour_an.py — L'ordre du jour des séances publiques de l'Assemblée (#1354).

LE BESOIN. La fiche de législature (#1314) montre, jour par jour, les sujets
inscrits à l'ordre du jour des séances publiques, à la couleur de la commission
saisie du texte. La source publie l'ordre du jour, mais rien n'en était publié
dans `pivot_data/` : `articles_votes.py` (#1264) ne s'en sert que pour savoir
quels dossiers une séance a discutés.

LA SOURCE. L'archive Agenda de chaque législature (`vp/reunions/Agenda*.json.zip`),
la même que lit `articles_votes.py`, une réunion par fichier. Une séance publique
de l'Assemblée est une réunion `@xsi:type == "seance_type"` dont l'uid commence
par `RUAN` : l'archive contient aussi des séances du Sénat (`RUSN`), une du
Congrès (`RUCG`), et toutes les réunions de commission. La XIVe n'a pas
d'archive Agenda.

CE QUI EST PUBLIÉ. Un fichier par législature, `pivot_data/ordre_du_jour/<n>.json` :
chaque séance (uid, date, début, fin, état — une séance « Supprimé » ou « Annulé »
garde son état au lieu de disparaître, §2 règle 5), et chacun de ses points
(uid, objet, type, état, procédure, nature, les dossiers que la source lui donne).

LE DOSSIER D'UN POINT. La source ne donne le dossier que sur une partie des
points : à la XVIIe, 942 des 2 498 points sur un texte des séances confirmées
(mesuré le 26/10/2026). Un point sans dossier prend celui d'un autre point de
la MÊME archive dont l'intitulé est le même, une fois retirées la mention de la
discussion, la lecture et les parenthèses — arbitré le 26/10/2026 (option C) :
dans toute la législature, et seulement si cet intitulé ne mène qu'à un seul
dossier. C'est regrouper des faits d'une même source par leur propre libellé,
ce que permet `regrouper-nest-pas-joindre-639` ; jamais une jointure avec une
autre source. Le dossier retrouvé ainsi est publié à part (`dossier_retrouve`),
avec le point qui l'a donné, jamais mêlé aux dossiers de la source. Un point
sans dossier dit pourquoi (`dossier_non_resolu.motif`).

Aucune durée, aucune présence n'est publiée, ni par séance ni par personne
(§2 règle 3) : début et fin sont ceux que la source annonce pour la séance.

Usage :
    python3 src/ordre_du_jour_an.py --telecharger
    python3 src/ordre_du_jour_an.py --agenda 17:Agenda.json.zip --out-dir pivot_data/ordre_du_jour
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import dumps_indente, ecrire_index_json  # noqa: E402
from licences import LICENCE_AN  # noqa: E402

SCHEMA_VERSION = "ordre-du-jour-v1"
DEFAULT_OUT_DIR = Path("pivot_data") / "ordre_du_jour"

#: La séance publique de l'Assemblée, à l'exclusion du Sénat et du Congrès.
TYPE_SEANCE = "seance_type"
PREFIXE_ASSEMBLEE = "RUAN"

#: Comment un point a reçu le dossier qu'aucun champ de la source ne lui donne.
RETROUVE_PAR_INTITULE = "meme_intitule_dans_la_legislature"
#: Pourquoi un point n'a pas de dossier — vocabulaire fermé.
MOTIF_HORS_TEXTE = "point_hors_texte"                 # questions, débats, session : aucun texte nommé
MOTIF_INTITULE_SANS_DOSSIER = "intitule_sans_dossier"  # aucun point de l'archive ne donne ce dossier
MOTIF_INTITULE_AMBIGU = "intitule_a_plusieurs_dossiers"
KNOWN_MOTIFS_DOSSIER_NON_RESOLU: frozenset[str] = frozenset({
    MOTIF_HORS_TEXTE, MOTIF_INTITULE_SANS_DOSSIER, MOTIF_INTITULE_AMBIGU,
})

_RX_TEXTE = re.compile(r"\b(projet|proposition)s?\s+de\s+(loi|résolution)")


def cle_d_intitule(objet: Optional[str]) -> Optional[str]:
    """L'intitulé d'un point réduit au texte qu'il nomme, ou None.

    « Suite de la discussion de la proposition de loi, adoptée par le Sénat,
    visant à … (n° 1234) » et « Discussion de la proposition de loi visant à … »
    donnent la même clé. Retirés : ce qui précède « projet / proposition de loi
    / de résolution » (le type de point), les parenthèses, la navette (« adoptée
    par le Sénat », « en nouvelle lecture », « en lecture définitive »), la
    ponctuation et la casse. Un point qui ne nomme aucun texte n'a pas de clé.
    """
    s = (objet or "").replace("’", "'").replace("\xa0", " ").lower()
    m = _RX_TEXTE.search(s)
    if not m:
        return None
    s = s[m.start():]
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r",?\s*(adopt|modifi|rejet)\w*\s+(par|avec)\s+[^,]*,", ",", s)
    s = re.sub(r",?\s*en\s+(nouvelle|première|deuxième|troisième|lecture)\s*(lecture)?\s*,?", ",", s)
    s = re.sub(r",?\s*en lecture définitive,?", ",", s)
    s = re.sub(r"[^\w']+", " ", s)
    return re.sub(r"\s+", " ", s).strip() or None


def _liste(valeur: Any) -> list:
    if valeur is None:
        return []
    return valeur if isinstance(valeur, list) else [valeur]


def _refs(point: dict[str, Any]) -> list[str]:
    ref = (point.get("dossiersLegislatifsRefs") or {}).get("dossierRef")
    return [r for r in _liste(ref) if isinstance(r, str) and r]


def seances_publiques(zip_path: Path) -> list[dict[str, Any]]:
    """Les séances publiques de l'Assemblée d'une archive Agenda, dans l'ordre
    de leur début, chacune avec ses points dans l'ordre de la source."""
    seances = []
    with zipfile.ZipFile(zip_path) as archive:
        for nom in archive.namelist():
            if not nom.endswith(".json"):
                continue
            reunion = json.loads(archive.read(nom)).get("reunion") or {}
            uid = str(reunion.get("uid") or "")
            if reunion.get("@xsi:type") != TYPE_SEANCE or not uid.startswith(PREFIXE_ASSEMBLEE):
                continue
            debut = reunion.get("timeStampDebut")
            date_seance = ((reunion.get("identifiants") or {}).get("DateSeance") or debut or "")[:10] or None
            points = []
            for point in _liste(((reunion.get("ODJ") or {}).get("pointsODJ") or {}).get("pointODJ")):
                if not isinstance(point, dict):
                    continue
                points.append({
                    "uid": point.get("uid"),
                    "objet": point.get("objet"),
                    "type": point.get("typePointODJ"),
                    "etat": (point.get("cycleDeVie") or {}).get("etat"),
                    "procedure": point.get("procedure"),
                    "nature": point.get("natureTravauxODJ"),
                    "dossiers": _refs(point),
                })
            seances.append({
                "uid": uid,
                "date": date_seance,
                "debut": debut,
                "fin": reunion.get("timeStampFin"),
                "etat": (reunion.get("cycleDeVie") or {}).get("etat"),
                "session_ref": reunion.get("sessionRef"),
                "compte_rendu_ref": reunion.get("compteRenduRef"),
                "points": points,
            })
    return sorted(seances, key=lambda s: (s["debut"] or "", s["uid"]))


def _instant(valeur: Optional[str]) -> float:
    try:
        return datetime.fromisoformat(valeur).timestamp() if valeur else 0.0
    except ValueError:
        return 0.0


def rattacher_par_intitule(seances: list[dict[str, Any]]) -> None:
    """Pose `dossier_retrouve` et `dossier_non_resolu` sur chaque point, en place.

    L'index des intitulés est fait des points de TOUTES les séances de
    l'archive, quel que soit leur état : le dossier qu'un point porte est un
    fait de la source, même si la séance a été supprimée. Le point qui donne le
    dossier est le plus proche dans le temps de ceux qui le portent.
    """
    index: dict[str, list[tuple[float, str, str]]] = {}
    for seance in seances:
        instant = _instant(seance["debut"])
        for point in seance["points"]:
            cle = cle_d_intitule(point["objet"])
            if cle:
                for ref in point["dossiers"]:
                    index.setdefault(cle, []).append((instant, ref, point["uid"]))
    for seance in seances:
        instant = _instant(seance["debut"])
        for point in seance["points"]:
            point["dossier_retrouve"] = None
            point["dossier_non_resolu"] = None
            if point["dossiers"]:
                continue
            cle = cle_d_intitule(point["objet"])
            porteurs = index.get(cle or "", [])
            dossiers = {ref for _, ref, _ in porteurs}
            if cle is None:
                point["dossier_non_resolu"] = {"motif": MOTIF_HORS_TEXTE}
            elif not dossiers:
                point["dossier_non_resolu"] = {"motif": MOTIF_INTITULE_SANS_DOSSIER}
            elif len(dossiers) > 1:
                point["dossier_non_resolu"] = {"motif": MOTIF_INTITULE_AMBIGU, "dossiers": sorted(dossiers)}
            else:
                _, ref, source = min(porteurs, key=lambda p: (abs(p[0] - instant), p[2] or ""))
                point["dossier_retrouve"] = {"dossier_ref": ref, "par": RETROUVE_PAR_INTITULE,
                                             "point_source": source}


def construire(legislature: str, zip_path: Path, *, source_url: str, genere_le: str) -> dict[str, Any]:
    seances = seances_publiques(zip_path)
    rattacher_par_intitule(seances)
    return {
        "schema_version": SCHEMA_VERSION,
        "legislature": int(legislature),
        "genere_le": genere_le,
        "licence_donnees": LICENCE_AN,
        "source_url": source_url,
        "seances": seances,
    }


def resume(document: dict[str, Any]) -> dict[str, int]:
    """Les décomptes imprimés après l'écriture : séances par état, points par
    origine de leur dossier."""
    compte: dict[str, int] = {}
    for seance in document["seances"]:
        compte[f"séances {seance['etat']}"] = compte.get(f"séances {seance['etat']}", 0) + 1
        for point in seance["points"]:
            if point["dossiers"]:
                cle = "points : dossier de la source"
            elif point["dossier_retrouve"]:
                cle = "points : dossier retrouvé par l'intitulé"
            else:
                cle = f"points : {point['dossier_non_resolu']['motif']}"
            compte[cle] = compte.get(cle, 0) + 1
    return compte


def _ecrire(chemin: Path, document: dict[str, Any]) -> None:
    """Un fichier ne se réécrit que si son contenu change : `genere_le` seul ne
    fait pas un commit (#1075)."""
    if chemin.is_file():
        try:
            ancien = json.loads(chemin.read_text(encoding="utf-8"))
        except ValueError:
            ancien = None
        if isinstance(ancien, dict) and {k: v for k, v in ancien.items() if k != "genere_le"} == {
                k: v for k, v in document.items() if k != "genere_le"}:
            return
    ecrire_index_json(chemin, document, dumps_indente)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--agenda", action="append", default=[], metavar="LEG:ZIP",
                        help="archive Agenda d'une législature (répétable)")
    parser.add_argument("--telecharger", action="store_true",
                        help="lire les archives des XVe-XVIIe, téléchargées ou en cache "
                             "(celles de articles_votes.py)")
    parser.add_argument("--cache-sources", type=Path, default=None)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(list(argv) if argv is not None else None)

    import articles_votes  # noqa: PLC0415 — le téléchargeur et ses caches

    sources: list[tuple[str, Path, str]] = []
    for valeur in args.agenda:
        legislature, chemin = valeur.split(":", 1)
        sources.append((legislature, Path(chemin), Path(chemin).name))
    if args.telecharger:
        cache = args.cache_sources or articles_votes.CACHE_SOURCES
        try:
            for legislature in articles_votes.LEGISLATURES:
                chemin = articles_votes.archive("agenda", legislature, cache)
                url = f"{articles_votes._BASE}/{legislature}/{articles_votes.ARCHIVES['agenda'][legislature]}"
                sources.append((legislature, chemin, url))
        except articles_votes.SourceIndisponible as exc:
            print(f"::error::ORDRE_DU_JOUR_SOURCE_INDISPONIBLE — {exc}. Rien n'est écrit : "
                  "les fichiers publiés restent ceux du run précédent.")
            return 1

    genere_le = time.strftime("%Y-%m-%d")
    for legislature, chemin, url in sources:
        document = construire(legislature, chemin, source_url=url, genere_le=genere_le)
        _ecrire(args.out_dir / f"{legislature}.json", document)
        print(f"  ✓ {legislature}e : {resume(document)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
