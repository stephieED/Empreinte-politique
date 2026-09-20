#!/usr/bin/env python3
"""build_scrutins_index.py — Construit `pivot_data/scrutins.json` (#432).

Un scrutin est identique pour tous ses votants : son méta était recopié dans
chacun des profils qui l'ont voté, jusqu'à 74 fois. Cet index le stocke une
seule fois, et les profils n'en gardent que le mapping `{scrutin_id, position}`.

Passe de **corpus**, jamais profil par profil : la législature d'un vote qui
n'en porte pas se résout par jointure avec un jumeau étiqueté vivant dans un
autre profil (`scrutins_legislature`). C'est aussi pourquoi elle est un
préalable à la normalisation des profils, et pas un sous-produit.

Usage :
    python3 src/build_scrutins_index.py
    python3 src/build_scrutins_index.py --profils-dir raw_data/profiles --out pivot_data/scrutins.json
    python3 src/build_scrutins_index.py --no-merge     # reconstruction complète

Code de sortie : 0 si l'index est écrit, 1 si un scrutin est resté sans
législature résoluble — aucune valeur par défaut n'est posée (AGENTS.md §2.5),
donc un index amputé n'est pas écrit silencieusement.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scrutins_index import DEFAULT_SCRUTINS_PATH, rafraichir  # noqa: E402
from scrutins_legislature import LegislatureIrresoluble  # noqa: E402

DEFAUT_PROFILS_DIR = Path("raw_data") / "profiles"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profils-dir", default=str(DEFAUT_PROFILS_DIR),
                        help=f"Profils bruts d'où lire les votes (défaut : {DEFAUT_PROFILS_DIR}). "
                             "Les profils bruts gardent l'enregistrement complet du vote, "
                             "les pivots n'en ont plus que le mapping.")
    parser.add_argument("--out", default=str(DEFAULT_SCRUTINS_PATH),
                        help=f"Fichier d'index à écrire (défaut : {DEFAULT_SCRUTINS_PATH}).")
    parser.add_argument("--no-merge", action="store_true",
                        help="Reconstruction complète au lieu d'une fusion additive avec "
                             "l'index existant. À réserver à un corpus COMPLET : sur une "
                             "tranche, les scrutins des profils non retraités disparaîtraient "
                             "et leurs mappings pointeraient dans le vide.")
    args = parser.parse_args()

    try:
        index, _ = rafraichir(
            Path(args.profils_dir),
            Path(args.out),
            strict=True,
            fusionner=not args.no_merge,
            genere_le=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        )
    except LegislatureIrresoluble as exc:
        print(f"[!] {exc}")
        print("    Index NON écrit : un index amputé produirait des profils dont une partie")
        print("    des votes ne référence rien, sans que rien ne le signale.")
        print("    Diagnostic détaillé : python3 src/audit_legislature_votes.py")
        return 1

    print(f"  ✓ {len(index)} scrutin(s) → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
