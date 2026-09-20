#!/usr/bin/env python3
"""
purge_mandats_nosdeputes.py — Retire des profils les mandats écrits par la
collecte NosDéputés, qu'aucune source vivante n'établit (#718).

Contexte
--------
NosDéputés n'est plus interrogé depuis #529, mais la fusion additive a gardé ce
qu'il avait écrit. La première collecte (29/07/2026) rangeait en dur en
`commission` toutes les `responsabilites` de l'API — groupes politiques, missions
et groupes de travail compris —, et publiait un « Mandat parlementaire (groupe) »
par législature. Retrouvé dans l'historique : au commit `0a404f752`, les profils
de `jerome-guedj`, `edouard-philippe`, `marine-le-pen` et `jean-luc-melenchon`
ont pour source `nosdeputes.fr` et portent déjà ces entrées à l'identique.

Mesuré le 17/09/2026 sur `origin/main` `186375320`, au pivot : **331** entrées sur
**32** profils — 57 sur 6 candidats déclarés, 274 sur 26 profils `roster_groupe`.
Elles doublent souvent un mandat que l'AN établit (même organe, même début, avec
une fin décalée d'un jour ou `null`, qui publie un mandat encore en cours) ; les
autres rangent en `commission` des organes qui n'en sont pas.

Leur présence rendait faux `AGENTS.md` §7 (« aucun champ publié ne dérive plus
de NosDéputés ») : #976 avait cherché le nom de la source dans les données, et
ces entrées ne le portent pas.

Signature
---------
Une entrée de `mandats[]` est retirée si et seulement si :
1. elle ne porte pas `categorie_source` — toute source vivante l'écrit (#718) ;
2. sa fonction commence par une **minuscule** — `type` au brut, `fonction` au
   pivot. NosDéputés écrivait `membre`, `président`, `mandat` ; AMO30 écrit
   `Membre`, `Président`.

Les deux conditions ensemble. Les quatre entrées sans estampille dont la fonction
est capitalisée (deux `Gouvernement`, deux missions de 2026) ne sont **pas** de
NosDéputés et ne sont pas touchées. Une fonction absente ne prouve rien : entrée
conservée.

Arbitré le 17/09/2026 : purger, y compris les entrées sans équivalent établi.

Les deux étages (#729)
----------------------
La fusion est additive au brut comme au pivot : le script se lance une fois par
couche. Au pivot, `chambres` est recomposé après le retrait (§4). Les fiches de
groupe et de lignée se recomposent au run suivant.

Usage (depuis la racine du dépôt) :
    python3 src/purge_mandats_nosdeputes.py                                  # rapport seul
    python3 src/purge_mandats_nosdeputes.py --apply                          # brut
    python3 src/purge_mandats_nosdeputes.py \
        --profiles-dir pivot_data/profiles --apply                           # pivot
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from json_io import ecrire_profil_json
from profil_brut import charger_socle
from schema_pivot import appliquer_chambres

DEFAULT_PROFILES_DIR = Path("raw_data") / "profiles"


def porte_la_forme_heritee(mandat: Any) -> bool:
    """Signature d'une entrée écrite par la collecte NosDéputés."""
    if not isinstance(mandat, dict) or mandat.get("categorie_source"):
        return False
    fonction = mandat.get("fonction", mandat.get("type"))
    return isinstance(fonction, str) and fonction[:1].islower()


def purge_profil(profil: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retourne (profil, entrées retirées). Ne modifie `mandats` que s'il y a
    quelque chose à retirer."""
    mandats = profil.get("mandats") or []
    retires = [m for m in mandats if porte_la_forme_heritee(m)]
    if retires:
        profil["mandats"] = [m for m in mandats if not porte_la_forme_heritee(m)]
    return profil, retires


def recomposer_champs_derives(profil: dict[str, Any]) -> list[str]:
    """`chambres` dérive de `mandats` (#493) : recomposé au pivot seulement,
    le socle brut ne le porte pas."""
    if "chambres" in profil:
        appliquer_chambres(profil)
        return ["chambres"]
    return []


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES_DIR), metavar="DOSSIER",
                        help="Couche à traiter : raw_data/profiles (défaut) ou pivot_data/profiles.")
    parser.add_argument("--apply", action="store_true",
                        help="Écrit les profils. Sans cette option, rapport seul.")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic).")
    args = parser.parse_args(argv)

    repertoire = Path(args.profiles_dir)
    if not repertoire.is_dir():
        print(f"[!] Répertoire introuvable : {repertoire}", file=sys.stderr)
        return 2

    total = 0
    touches = 0
    par_categorie: Counter = Counter()
    for chemin in sorted(repertoire.glob("*.json")):
        slug = chemin.name.replace(".pivot.json", "").replace(".json", "")
        if args.only and slug != args.only:
            continue
        try:
            profil = charger_socle(chemin)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  [!] Lecture impossible ({chemin.name}) : {exc}", file=sys.stderr)
            continue
        if not isinstance(profil, dict):
            continue
        profil, retires = purge_profil(profil)
        if not retires:
            continue
        touches += 1
        total += len(retires)
        par_categorie.update(m.get("categorie") for m in retires)
        recomposes = recomposer_champs_derives(profil)
        detail = f" ; dérivés recomposés : {', '.join(recomposes)}" if recomposes else ""
        print(f"  {slug} : {len(retires)} mandat(s) hérité(s) retiré(s){detail}")
        if args.apply:
            ecrire_profil_json(chemin, profil)

    mode = "APPLIQUÉ" if args.apply else "SIMULATION (--apply pour écrire)"
    print(f"\n[{mode}] {repertoire} — {total} mandat(s) retiré(s) sur {touches} profil(s)")
    if par_categorie:
        print("  par catégorie : " + ", ".join(f"{c} {n}" for c, n in par_categorie.most_common()))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
