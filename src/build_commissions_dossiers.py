#!/usr/bin/env python3
"""build_commissions_dossiers.py — Construit `pivot_data/commissions_dossiers.json` (#328).

CE QUE LE FICHIER PORTE. Une entrée par dossier législatif renvoyé en commission
au fond à l'Assemblée : `{dossier_id: {organe_ref, sigle, nom, type}}`, lue
verbatim dans les archives AN (`commissions_dossiers_an.py`). La fiche candidat
s'en sert pour publier, sous « L'essentiel », par quelles commissions les
dossiers qu'une personne a amendés ont été examinés.

POURQUOI UN FICHIER À PART, ET PAS UNE COLONNE DE `pivot_data/amendements/`.
La commission est une propriété du **dossier**, pas du texte visé : la ranger
dans la table `textes` de chaque législature la recopierait une fois par texte
visé (777 entrées pour la seule XVe) au lieu d'une fois par dossier, et la
dupliquerait entre législatures — 47 dossiers de la XVIe sont référencés depuis
l'index de la XVIIe. Un seul fichier, une seule entrée par dossier.

ADDITIF, JAMAIS DESTRUCTEUR. Un run sans archives lisibles rend une table vide,
et le fichier déjà publié est alors **conservé** : une collecte vide n'écrase
jamais une collecte non vide (AGENTS.md §3a, #465). `--no-merge` force la
reconstruction complète, à réserver à un run qui a bien lu les trois archives.

Usage :
    python3 src/build_commissions_dossiers.py
    python3 src/build_commissions_dossiers.py --out pivot_data/commissions_dossiers.json
    python3 src/build_commissions_dossiers.py --no-merge
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from commissions_dossiers_an import charger_table  # noqa: E402
from licences import LICENCE_AN  # noqa: E402

SCHEMA_VERSION = "commissions-dossiers-v1"

DEFAUT_SORTIE = Path("pivot_data") / "commissions_dossiers.json"


def _lire_existant(chemin: Path) -> dict[str, dict]:
    """Table déjà publiée, ou `{}` — un fichier illisible ne fait pas échouer."""
    if not chemin.is_file():
        return {}
    try:
        with open(chemin, encoding="utf-8") as f:
            publie = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    commissions = publie.get("commissions") if isinstance(publie, dict) else None
    return commissions if isinstance(commissions, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out",
        default=str(DEFAUT_SORTIE),
        help=f"Fichier d'index à écrire (défaut : {DEFAUT_SORTIE}).",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Reconstruction complète au lieu d'une fusion additive avec l'index "
             "publié. À réserver à un run qui a lu toutes les archives : sur un run "
             "partiel, les dossiers non revus disparaîtraient.",
    )
    args = parser.parse_args(argv)

    chemin = Path(args.out)
    collectee = charger_table()
    if not collectee:
        # Nommer l'absence plutôt que de publier un index muet.
        print("  [!] Archives de dossiers ou référentiel des organes indisponibles : "
              "aucune commission au fond collectée à ce run.")

    ancienne = {} if args.no_merge else _lire_existant(chemin)
    table = dict(ancienne)
    table.update(collectee)

    if not table:
        print("  [!] Table vide et rien de publié : aucun fichier écrit.")
        return 0

    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(
            {
                "schema_version": SCHEMA_VERSION,
                "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "licence_donnees": LICENCE_AN,
                "commissions": table,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    conservees = len(table) - len(collectee)
    print(f"  ✓ {len(table)} dossier(s) avec commission saisie au fond → {chemin}")
    if conservees > 0:
        print(f"      dont {conservees} conservé(s) d'un run précédent "
              "(non revus par celui-ci)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
