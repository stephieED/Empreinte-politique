#!/usr/bin/env python3
"""build_scrutins_dossiers.py — Construit `pivot_data/scrutins_dossiers.json` (#758).

CE QUE LE FICHIER PORTE, ET POURQUOI RIEN NE LE PORTAIT. Un scrutin de
l'Assemblée ne nomme pas le texte qu'il tranche : `objet.referenceLegislative`
et `demandeur.referenceLegislative` sont nuls sur 0/18 311 scrutins bruts des
législatures 14 à 17. Le lien n'existe qu'en sens inverse, dans le dossier —
`actesLegislatifs[].voteRefs`. Ce fichier le publie, et publie avec lui l'issue
du dossier :

    {"scrutins": {"an:17:960": "DLR5L17N51481"},
     "dossiers": {"DLR5L17N51481": {"statut": "adopte", "sort_49_3": false}}}

Ce qu'il débloque : d'un vote publié, la **commission saisie au fond** (par
jointure dans `commissions_dossiers.json`) et le **sort du dossier** — ni l'une
ni l'autre n'étaient atteignables. Le sort du *scrutin* ne disait que si CE
scrutin-là avait adopté : 17 non-adoptés sur les 697 textes en dernière
lecture, contre 32 rejetés côté dossier.

POURQUOI UN FICHIER À PART, ET PAS UN CHAMP SUR `scrutins.json`. Les deux
tables ne se collectent pas au même endroit : les scrutins viennent de
`Scrutins.json.zip`, le rattachement des dossiers de `dossiers*.zip`. Poser le
champ sur le scrutin coupleait la construction des scrutins aux archives de
dossiers, et rendrait un `dossier_id: null` indistinguable d'un run qui n'a pas
lu les dossiers. Un fichier à part se lit — ou ne se lit pas —, et son absence
est alors visible. Même précédent que `commissions_dossiers.json` (#328).

ADDITIF, JAMAIS DESTRUCTEUR. Un run sans archives lisibles rend une table vide,
et le fichier déjà publié est **conservé** : une collecte vide n'écrase jamais
une collecte non vide (AGENTS.md §3a, #465). `--no-merge` force la
reconstruction complète, à réserver à un run qui a bien lu toutes les archives.

Usage :
    python3 src/build_scrutins_dossiers.py
    python3 src/build_scrutins_dossiers.py --out pivot_data/scrutins_dossiers.json
    python3 src/build_scrutins_dossiers.py --no-merge
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from licences import LICENCE_AN  # noqa: E402
from scrutins_dossiers_an import SCHEMA_VERSION, charger_table  # noqa: E402

DEFAUT_SORTIE = Path("pivot_data") / "scrutins_dossiers.json"


def _lire_existant(chemin: Path) -> dict[str, dict]:
    """Tables déjà publiées, ou vides — un fichier illisible ne fait pas échouer."""
    vide: dict[str, dict] = {"scrutins": {}, "dossiers": {}}
    if not chemin.is_file():
        return vide
    try:
        with open(chemin, encoding="utf-8") as f:
            publie = json.load(f)
    except (json.JSONDecodeError, OSError):
        return vide
    if not isinstance(publie, dict):
        return vide
    return {
        cle: (publie.get(cle) if isinstance(publie.get(cle), dict) else {})
        for cle in ("scrutins", "dossiers")
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out",
        default=str(DEFAUT_SORTIE),
        help=f"Fichier à écrire (défaut : {DEFAUT_SORTIE}).",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Reconstruction complète au lieu d'une fusion additive avec ce qui "
             "est publié. À réserver à un run qui a lu toutes les archives : sur "
             "un run partiel, les rattachements non revus disparaîtraient.",
    )
    args = parser.parse_args(argv)

    chemin = Path(args.out)
    collectee = charger_table()
    if not collectee.get("scrutins"):
        # Nommer l'absence plutôt que de publier une table muette.
        print("  [!] Archives de dossiers indisponibles : aucun rattachement "
              "scrutin → dossier collecté à ce run.")

    ancienne = (
        {"scrutins": {}, "dossiers": {}} if args.no_merge else _lire_existant(chemin)
    )
    scrutins = dict(ancienne["scrutins"])
    scrutins.update(collectee.get("scrutins") or {})
    dossiers = dict(ancienne["dossiers"])
    dossiers.update(collectee.get("dossiers") or {})

    if not scrutins:
        print("  [!] Table vide et rien de publié : aucun fichier écrit.")
        return 0

    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": SCHEMA_VERSION,
                "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "licence_donnees": LICENCE_AN,
                "scrutins": scrutins,
                "dossiers": dossiers,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    conservees = len(scrutins) - len(collectee.get("scrutins") or {})
    sans_statut = sum(1 for d in dossiers.values() if not d.get("statut"))
    print(f"  ✓ {len(scrutins)} scrutin(s) rattaché(s) à {len(dossiers)} dossier(s) → {chemin}")
    if sans_statut:
        print(f"      dont {sans_statut} dossier(s) sans statut résolu (absence déclarée)")
    if conservees > 0:
        print(f"      dont {conservees} rattachement(s) conservé(s) d'un run précédent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
