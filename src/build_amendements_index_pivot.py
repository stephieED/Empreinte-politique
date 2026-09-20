#!/usr/bin/env python3
"""build_amendements_index_pivot.py — Construit `pivot_data/amendements/` (#431).

À ne pas confondre avec `build_amendements_index.py`, qui construit l'index
**brut** des archives AN pour le job CI `extract-amendements-an`, ni avec
`build_amendements_index_figees.py`, qui matérialise les législatures closes
sous `raw_data/amendements_an_figes/`. Celui-ci produit la couche **pivot** :
la liste dédupliquée que les profils publiés référencent.

Un amendement est identique pour tous ses signataires, et sa liste de
cosignataires était recopiée dans le profil de chacun d'eux : 77,7 M entrées de
cosignatures pour 4,96 M distinctes, soit 1 083,9 Mo des 1 342,4 Mo que pèse
`amendements[]` dans les profils pivot. Cet index stocke chaque amendement une
seule fois, et les profils n'en gardent que le mapping
`{amendement_id, role_signataire}`.

Écrit **un fichier par législature**, plus un fichier compagnon de cosignatures :

    pivot_data/amendements/17.json
    pivot_data/amendements/17.cosignatures.json

Un fichier global unique pèserait 128,8 Mo, au-delà de la limite GitHub de
100 Mo par blob — voir docs/decisions/normalisation-amendements.md.

Contrairement à l'index des scrutins, la construction n'est **pas** une passe de
corpus : la clé d'un amendement est son `uid` AN, porté par l'enregistrement
lui-même, et sa législature se lit dans cet `uid`. Rien n'a besoin d'être résolu
par jointure — d'où une seule reconstruction par run, après la passe pivot.

Une seule jointure, depuis #639 : le `texte_vise` d'un amendement (uid de
document AN) vers le dossier législatif de ce document, lu dans les archives
déjà en cache (`.cache/dossiers_an/`, restauré par le job `merge-and-pivot`).
Elle est publiée sous forme de **table de fichier** — voir
`amendements_index.resoudre_textes`. `--sans-dossiers` s'en passe : les
rattachements déjà publiés sont alors conservés, aucun n'est ajouté.

Un report nommé, depuis #696 : `amendements_index.backfill_texte_vise` relit
dans les archives figées le `texte_vise` des entrées qui portent un **intitulé**
au lieu de l'uid du document AN — 2 500 des 484 132 amendements publiés,
mesuré le 01/09/2026. La fusion additive ne pouvait pas les corriger seule, et
pouvait même réintroduire l'intitulé : voir la docstring de ce report.
`--sans-report-texte-vise` s'en passe, en comptant ce qu'il laisse.

Usage :
    python3 src/build_amendements_index_pivot.py
    python3 src/build_amendements_index_pivot.py --profils-dir raw_data/profiles --out pivot_data/amendements
    python3 src/build_amendements_index_pivot.py --no-merge     # reconstruction complète
    python3 src/build_amendements_index_pivot.py --sans-dossiers  # sans la jointure dossiers
    python3 src/build_amendements_index_pivot.py --sans-report-texte-vise  # sans le report #696
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from amendements_index import (  # noqa: E402
    DEFAULT_AMENDEMENTS_DIR,
    rafraichir,
)
from textes_dossiers_an import charger_table  # noqa: E402
from textes_vises_figes import lire_textes_vises  # noqa: E402

DEFAUT_PROFILS_DIR = Path("raw_data") / "profiles"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profils-dir", default=str(DEFAUT_PROFILS_DIR),
                        help=f"Profils bruts d'où lire les amendements (défaut : {DEFAUT_PROFILS_DIR}). "
                             "Les profils bruts gardent l'enregistrement complet de l'amendement, "
                             "les pivots n'en ont plus que le mapping.")
    parser.add_argument("--out", default=str(DEFAULT_AMENDEMENTS_DIR),
                        help=f"Dossier d'index à écrire (défaut : {DEFAULT_AMENDEMENTS_DIR}).")
    parser.add_argument("--no-merge", action="store_true",
                        help="Reconstruction complète au lieu d'une fusion additive avec "
                             "l'index existant. À réserver à un corpus COMPLET : sur une "
                             "tranche, les amendements des profils non retraités disparaîtraient "
                             "et leurs mappings pointeraient dans le vide.")
    parser.add_argument("--sans-dossiers", action="store_true",
                        help="N'établit pas la jointure texte → dossier législatif (#639). "
                             "Les rattachements déjà publiés sont conservés, aucun n'est "
                             "ajouté : à réserver aux exécutions sans archives de dossiers.")
    parser.add_argument("--sans-report-texte-vise", action="store_true",
                        help="Ne relit pas dans les archives figées le `texte_vise` des "
                             "amendements qui portent un intitulé au lieu de l'uid du "
                             "document AN (#696). Les entrées fautives sont alors comptées "
                             "et laissées telles quelles : à réserver aux exécutions sans "
                             "raw_data/amendements_an_figes/.")
    args = parser.parse_args(argv)

    table_textes = None if args.sans_dossiers else charger_table()
    if table_textes is not None and not table_textes:
        # Nommer l'absence plutôt que de publier un index muet : sans archive,
        # aucun amendement ne gagne de dossier, et les anciens gardent le leur.
        print("  [!] Archives de dossiers indisponibles : aucun rattachement "
              "texte → dossier ajouté à ce run (les rattachements publiés sont conservés).")

    comptes: dict[str, int] = {}
    index = rafraichir(
        Path(args.profils_dir),
        Path(args.out),
        fusionner=not args.no_merge,
        genere_le=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        table_textes=table_textes,
        lire_textes_vises=None if args.sans_report_texte_vise else lire_textes_vises,
        comptes=comptes,
    )

    print(f"  ✓ {len(index)} amendement(s) distinct(s) → {args.out}")
    for legislature in index.legislatures():
        n = len(index.ids_de_legislature(legislature))
        print(f"      législature {legislature} : {n} amendement(s)")
    if comptes.get("entrees_a_reparer"):
        # Nommé même quand le report ne répare rien : un compte tu est le trou
        # de #510. `entrees_sans_texte_vise` est un sous-ensemble de
        # `entrees_a_reparer` — l'absence et l'intitulé ne se confondent pas.
        print(f"      texte visé (#696) : {comptes['entrees_a_reparer']} entrée(s) sans uid "
              f"de document, dont {comptes['entrees_sans_texte_vise']} sans texte visé du "
              f"tout ; {comptes['entrees_corrigees']} corrigée(s) depuis les archives figées, "
              f"{comptes['entrees_sans_source']} sans valeur sourcée "
              f"({comptes['legislatures_lues']} législature(s) relue(s), "
              f"{comptes['legislatures_sans_source']} sans archive figée exploitable)")
    if "amendements_rattaches" in comptes:
        print(f"      dossiers : {comptes['amendements_rattaches']} amendement(s) rattaché(s), "
              f"{comptes['amendements_sans_dossier']} sans dossier "
              f"({comptes['textes_resolus']} texte(s) résolu(s), "
              f"{comptes['textes_sans_dossier']} sans dossier dans les archives lues)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
