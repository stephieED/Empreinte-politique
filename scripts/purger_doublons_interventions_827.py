#!/usr/bin/env python3
"""
purger_doublons_interventions_827.py — Retire les explications de vote publiées
deux fois par le run 34503639092 (#827).

Ce que la clé a fait
--------------------
`_interv_key` passait par `source_url` **avant** le contenu. Les explications de
vote du Parlement européen n'ont pas d'`intervention_id` — ParlTrack ne leur
donne aucune référence — si bien que leur clé était le contenu **avant** #827 et
l'URL **après**. Deux clés pour la même entrée : la fusion additive a ajouté au
lieu de reconnaître.

Résultat publié : **1 462 explications en double**, l'exemplaire d'avant sans
lien, puis le même avec. Même date, même sujet, même texte.

La clé est corrigée dans le même lot (`source_url` retiré de la cascade), ce qui
empêche la récidive — mais la fusion additive ne retirera **jamais** ce qui est
déjà publié. D'où ce script, à passer une fois.

Un seul étage, et c'est mesuré
------------------------------
#729 exige qu'une correction qui **retire** s'applique à `raw_data/profiles/`
**et** à `pivot_data/profiles/`, sans quoi elle ne se pose nulle part. Ici le
premier étage n'a rien : les explications de vote sont posées par
`enrich_pivot_with_parltrack`, appelée sur le profil **pivot**. Vérifié sur le
brut de `marine-le-pen` — il ne contient ni `doceo`, ni aucun texte
d'explication.

Lequel des deux garder
----------------------
**Celui qui porte le lien.** Les deux sont identiques par ailleurs ; l'un a un
`source_url` vérifié au portail, l'autre non. Garder l'autre rejetterait le
travail de #827.

Quand aucun des deux ne porte de lien — les 271 explications dont l'intitulé ne
cite aucun document — le premier rencontré est gardé, les entrées étant
identiques.

Ce que ce script NE touche pas
------------------------------
Les interventions portant un `intervention_id`. Mesuré sur les 1 019 036
interventions publiées : **0** est publiée deux fois sous le même identifiant.
Et leur clé de contenu ne les sépare pas — **902 457** entrées à identifiants
différents la partagent, faute de sujet et de texte en mode thème-seul. Les
dédoublonner sur le contenu détruirait 88 % du corpus.

Usage
-----
    python3 scripts/purger_doublons_interventions_827.py            # mesure seule
    python3 scripts/purger_doublons_interventions_827.py --ecrire   # applique
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from json_io import ecrire_profil_json  # noqa: E402

PROFILS_PAR_DEFAUT = RACINE / "pivot_data" / "profiles"


def cle_de_contenu(intervention: dict) -> tuple:
    """La clé qui aurait dû servir, et qui sert désormais (#827)."""
    return (
        intervention.get("date"),
        intervention.get("sujet"),
        (intervention.get("texte") or "")[:50],
    )


def purger(profil: dict) -> tuple[int, int]:
    """Retire les doublons d'interventions SANS identifiant. Modifie en place.

    Returns:
        `(retirees, restantes)`.
    """
    interventions = profil.get("interventions")
    if not isinstance(interventions, list):
        return 0, 0

    vues: dict[tuple, int] = {}
    gardees: list[dict] = []
    retirees = 0
    for entree in interventions:
        if not isinstance(entree, dict) or entree.get("intervention_id"):
            gardees.append(entree)
            continue
        cle = cle_de_contenu(entree)
        rang = vues.get(cle)
        if rang is None:
            vues[cle] = len(gardees)
            gardees.append(entree)
            continue
        retirees += 1
        # Le lien l'emporte : les deux entrées sont identiques par ailleurs.
        if entree.get("source_url") and not gardees[rang].get("source_url"):
            gardees[rang] = entree
    profil["interventions"] = gardees
    return retirees, len(gardees)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-dir", type=Path, default=PROFILS_PAR_DEFAUT)
    parser.add_argument("--ecrire", action="store_true",
                        help="applique la purge ; sans ce drapeau, mesure seule")
    args = parser.parse_args(argv)

    total_retirees = 0
    touches = 0
    for chemin in sorted(args.profiles_dir.glob("*.json")):
        try:
            with open(chemin, encoding="utf-8") as fh:
                profil = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  [!] {chemin.name} illisible : {exc}")
            continue
        retirees, restantes = purger(profil)
        if not retirees:
            continue
        touches += 1
        total_retirees += retirees
        print(f"  {chemin.name:34s} {retirees:5d} doublon(s) retiré(s), "
              f"{restantes} intervention(s) restantes")
        if args.ecrire:
            ecrire_profil_json(chemin, profil)

    verbe = "retirés" if args.ecrire else "à retirer (mesure seule)"
    print(f"\n{total_retirees} doublon(s) {verbe}, sur {touches} profil(s).")
    if not args.ecrire and total_retirees:
        print("Relancer avec --ecrire pour appliquer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
