#!/usr/bin/env python3
"""Réduit les profils d'un staging d'artifact aux champs que le job a collectés.

`#450` a rétabli « un artifact = les SLUGS d'un job ». Il restait l'autre
moitié : un job publiait le profil **entier**, donc tous les champs qu'il n'a
pas collectés, recopiés de la baseline de son checkout. Tant que la fusion des
dossiers législatifs était additive, cette copie périmée ne pouvait rien
écraser ; depuis #997, la dernière source l'emporte, et elle a reposé les
vieux stades sur 17 candidats déclarés.

Ce script est appelé par `.github/actions/publish-written-profiles` quand le
job déclare ses champs (`champs:`). Il travaille sur le **staging**, jamais sur
`raw_data/profiles/` : le job garde son profil complet sur disque, seul ce
qu'il publie est réduit.

Usage :
    python3 scripts/projeter_contribution.py _publish/profiles mandats_locaux
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from json_io import ecrire_profil_json  # noqa: E402
from profil_brut import (  # noqa: E402
    CLE_PARTITIONNEE,
    dossier_tranches_du_socle,
    projeter_contribution,
)


def projeter_staging(staging: Path, champs: list[str]) -> tuple[int, int]:
    """`(profils projetés, répertoires de tranches retirés)`.

    Les tranches partent avec les amendements : un socle qui ne porte plus son
    manifeste n'a rien à quoi rattacher des fichiers de tranche, et les laisser
    publierait des amendements que la contribution ne déclare pas.
    """
    projetes = tranches_retirees = 0
    for socle in sorted(staging.glob("*.json")):
        if socle.name.startswith("."):
            continue
        try:
            profil = json.loads(socle.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"::warning::Socle illisible, laissé tel quel : {socle} ({exc})")
            continue
        if not isinstance(profil, dict):
            continue
        ecrire_profil_json(socle, projeter_contribution(profil, champs))
        projetes += 1
        if CLE_PARTITIONNEE not in champs:
            tranches = dossier_tranches_du_socle(socle)
            if tranches.is_dir():
                shutil.rmtree(tranches)
                tranches_retirees += 1
    return projetes, tranches_retirees


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 2:
        print("usage: projeter_contribution.py <staging> <champ> [champ…]", file=sys.stderr)
        return 2
    staging = Path(args[0])
    champs = args[1:]
    if not staging.is_dir():
        print(f"::warning::Staging absent, rien à projeter : {staging}")
        return 0
    projetes, tranches = projeter_staging(staging, champs)
    print(f"Contribution réduite à {', '.join(champs)} : "
          f"{projetes} profil(s), {tranches} répertoire(s) de tranches retiré(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
