#!/usr/bin/env python3
"""
collecte_senat.py — Écrire les appartenances sénatoriales dans `raw_data/` (#885).

Sa place dans la chaîne
------------------------
C'est le pendant sénatorial de ce que `candidate_profile` fait pour
l'Assemblée : il **écrit du brut**, source-near, et ne publie rien. La
traduction en pivot est le travail de `normalize_senat`, appelée par
`generate_all_profiles` comme elle appelle `normalize_europarl`.

Le bloc écrit est calqué sur `mandat_europeen`, et c'est délibéré : deux
sources étrangères au référentiel de l'Assemblée, deux blocs de même forme, un
seul chemin de normalisation à comprendre.

    "mandat_senatorial": {
        "matricule": "04033B",
        "source": "https://data.senat.fr/data/senateurs/export_sens.zip",
        "synchro_le": "2026-09-13T12:42:00+0000",
        "mandats_senatoriaux": [ … ]
    }

Ce qu'il refuse d'écrire
-------------------------
**Un profil hors périmètre.** `normalize_senat.POPULATIONS_PUBLIEES` limite aux
candidats déclarés, et le filtre est ici, **à la collecte** : une donnée qu'on
ne publiera pas ne se collecte pas, et la laisser entrer dans `raw_data/`
suffirait à ce que la fusion additive la garde pour toujours (#729). C'est le
même raisonnement que pour `activite_senateur`.

**Un export vide.** `senat_opendata.lire_tables` lève `ExportSenatVide` avant
que ce module écrive quoi que ce soit — l'archive publiée le 13/09/2026 à
03 h 33 faisait 444 octets et ne portait aucune table, avec un HTTP 200. Un
collecteur qui aurait tourné entre 03 h 33 et 12 h 42 aurait vidé les fiches en
silence.

**Un profil sans matricule apparié.** `identifiants.senat` vaut `null` sur
1 160 des 1 196 entrées, et sur deux d'entre elles c'est une décision — les
homonymes de `beatrice-descamps` et `jean-louis-masson`. Écrire sur un profil
non apparié publierait la carrière de quelqu'un d'autre.

Usage :
    python3 src/collecte_senat.py --export .cache/senat/export_sens.sql
    python3 src/collecte_senat.py --export … --apply
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import ecrire_profil_json  # noqa: E402
from normalize_senat import URL_SOURCE, est_dans_le_perimetre  # noqa: E402
from population_profils import provenance_du_profil  # noqa: E402
from senat_mandats import composer_mandats  # noqa: E402
from senat_opendata import URL_EXPORT, lire_tables  # noqa: E402

DEFAULT_RAW_DIR = Path("raw_data/profiles")
DEFAULT_PIVOT_DIR = Path("pivot_data/profiles")
DEFAULT_CORRESPONDANCE = Path("raw_data/correspondance_acteurs_an.json")

#: La clé du bloc dans le profil brut. Même forme que `mandat_europeen`.
CLE_BLOC = "mandat_senatorial"


def _charger(chemin: Path) -> Optional[dict[str, Any]]:
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) else None


def profils_a_collecter(
    correspondance: dict[str, Any],
    pivot_dir: Path,
) -> tuple[dict[str, str], list[str]]:
    """Rend `({slug: matricule}, hors_perimetre)`.

    La provenance est lue sur le **pivot**, seule couche qui la porte (#630), et
    un profil dont le pivot est illisible est traité comme hors périmètre : une
    provenance qu'on ne peut pas lire n'est pas une provenance publiable
    (§2 règle 5).
    """
    a_collecter: dict[str, str] = {}
    hors: list[str] = []
    for slug, entree in (correspondance.get("correspondances") or {}).items():
        matricule = (entree.get("identifiants") or {}).get("senat")
        if not matricule:
            continue
        profil = _charger(pivot_dir / f"{slug}.pivot.json")
        if profil is None or not est_dans_le_perimetre(provenance_du_profil(profil)):
            hors.append(slug)
            continue
        a_collecter[slug] = matricule
    return a_collecter, sorted(hors)


def composer_bloc(
    tables: dict[str, list[dict[str, Any]]],
    matricule: str,
    synchro_le: str,
) -> dict[str, Any]:
    """Le bloc `mandat_senatorial` d'un matricule."""
    return {
        "matricule": matricule,
        "source": URL_EXPORT,
        "source_portail": URL_SOURCE,
        "synchro_le": synchro_le,
        "mandats_senatoriaux": composer_mandats(tables, matricule),
    }


def collecter(
    export: Path,
    raw_dir: Path = DEFAULT_RAW_DIR,
    pivot_dir: Path = DEFAULT_PIVOT_DIR,
    correspondance: Path = DEFAULT_CORRESPONDANCE,
    *,
    appliquer: bool = False,
    synchro_le: Optional[str] = None,
    manifest_out: Optional[Path] = None,
) -> dict[str, Any]:
    """Écrit (ou simule) le bloc sénatorial des profils du périmètre.

    `manifest_out` consigne **les seuls fichiers que ce job a écrits**, un par
    ligne (#450). La CI uploade ce périmètre-là et jamais `raw_data/profiles/` :
    le répertoire contient la baseline committée récupérée par le checkout, et
    l'uploader entier réinjecterait une copie périmée de tous les autres
    profils — mesuré au run 32277443716, 3 335 amendements sur `antoine-armand`
    dont 1 289 périmés cohabitant avec leurs 2 046 corrigés.
    """
    tables = lire_tables(export)
    document = _charger(correspondance)
    if document is None:
        raise ValueError(f"{correspondance} illisible : la correspondance est le "
                         "seul lien entre un slug et un matricule, et l'inventer "
                         "publierait la carrière de quelqu'un d'autre.")
    horodatage = synchro_le or time.strftime("%Y-%m-%dT%H:%M:%S%z")

    a_collecter, hors = profils_a_collecter(document, pivot_dir)
    ecrits: list[dict[str, Any]] = []
    sans_brut: list[str] = []
    for slug, matricule in sorted(a_collecter.items()):
        chemin = raw_dir / f"{slug}.json"
        brut = _charger(chemin)
        if brut is None:
            # Un profil apparié dont le brut manque n'est pas un profil vide :
            # c'est une collecte qui n'a pas eu lieu, et la fabriquer ici
            # écrirait un socle sans identité (§2 règle 5).
            sans_brut.append(slug)
            continue
        bloc = composer_bloc(tables, matricule, horodatage)
        brut[CLE_BLOC] = bloc
        if appliquer:
            ecrire_profil_json(chemin, brut)
        ecrits.append({"slug": slug, "matricule": matricule,
                       "mandats": len(bloc["mandats_senatoriaux"])})

    if manifest_out is not None and appliquer:
        manifest_out.parent.mkdir(parents=True, exist_ok=True)
        manifest_out.write_text(
            "".join(f"{e['slug']}.json\n" for e in ecrits), encoding="utf-8")

    return {
        "applique": appliquer,
        "nb_profils": len(ecrits),
        "nb_mandats": sum(e["mandats"] for e in ecrits),
        "profils": ecrits,
        "nb_hors_perimetre": len(hors),
        "hors_perimetre": hors,
        "nb_sans_brut": len(sans_brut),
        "sans_brut": sans_brut,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--export", type=Path, required=True,
                        help="Le dump `export_sens.sql` décompressé.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--pivot-dir", type=Path, default=DEFAULT_PIVOT_DIR)
    parser.add_argument("--correspondance", type=Path, default=DEFAULT_CORRESPONDANCE)
    parser.add_argument("--manifest-out", type=Path,
                        help="Consigne les profils écrits par CE job (#450).")
    parser.add_argument("--apply", action="store_true",
                        help="Écrit les profils bruts. Sans ce drapeau, rien n'est modifié.")
    args = parser.parse_args(argv)

    rapport = collecter(args.export, args.raw_dir, args.pivot_dir, args.correspondance,
                        appliquer=args.apply, manifest_out=args.manifest_out)
    mode = "APPLIQUÉ" if rapport["applique"] else "simulation (aucun fichier écrit)"
    print(f"→ collecte sénatoriale — {mode}")
    print(f"  {rapport['nb_profils']} profil(s), {rapport['nb_mandats']} appartenance(s).")
    for entree in rapport["profils"]:
        print(f"     {entree['slug']:28} {entree['matricule']}  {entree['mandats']:4}")
    print(f"  {rapport['nb_hors_perimetre']} apparié(s) hors périmètre "
          f"(membres de roster : le Sénat n'entre que pour les candidats déclarés).")
    if rapport["nb_sans_brut"]:
        print(f"  ⚠ {rapport['nb_sans_brut']} apparié(s) sans profil brut : "
              f"{', '.join(rapport['sans_brut'][:5])}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
