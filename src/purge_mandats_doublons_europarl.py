#!/usr/bin/env python3
"""
purge_mandats_doublons_europarl.py — Retire du pivot le mandat européen publié
deux fois, quand la source l'a publié deux fois (#729).

Le défaut
---------
Le portail du Parlement européen rend **deux appartenances pour la même
législature** : l'une `role: MEMBER_PARLIAMENT` sans classification (`type:
"AUTRE"`), l'autre `role: MEMBER` classée `EU_INSTITUTION`. `normalize_europarl`
les rendait fidèlement toutes les deux, et la fiche publiait le même mandat
**deux fois** — une fois en `categorie: "autre"` (fonction « Membre du Parlement
européen »), une fois en `mandat_electif` (fonction « Membre »).

Mesuré le 12/09/2026 sur `origin/main` : **42 doublons sur 29 profils**, et
c'est 42 des 52 entrées que #729 comptait dans une catégorie minoritaire.

La collecte est corrigée dans `normalize_europarl.dedupliquer_appartenances`,
mais **la fusion est additive** : l'entrée déjà publiée resterait. Ce script est
le retrait qui manque, et il ne concerne que le **pivot** — le brut garde les
deux entrées de la source, c'est sa nature de couche source-near (#580).

Le critère
----------
Une entrée est retirée seulement si **toutes** ces conditions tiennent :

  - `categorie: "autre"` et `categorie_source: "europarl"` ;
  - le profil porte, au **même libellé** et à la **même période exacte**, une
    entrée `mandat_electif` également estampillée `europarl` ;
  - les deux fonctions diffèrent — la paire mesurée est « Membre du Parlement
    européen » / « Membre ».

Sans la contrepartie `mandat_electif` dans le profil, rien n'est retiré : c'est
la règle de prudence de #387, un faux négatif laisse un doublon visible, un faux
positif supprime un mandat réel.

Usage (depuis la racine du dépôt) :
    python3 src/purge_mandats_doublons_europarl.py
    python3 src/purge_mandats_doublons_europarl.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from json_io import ecrire_profil_json

DEFAULT_PROFILES_DIR = Path("pivot_data") / "profiles"


def _cle(mandat: dict[str, Any]) -> tuple:
    return ((mandat.get("label") or "").strip(), mandat.get("debut"), mandat.get("fin"))


def purge_profil(profil: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retourne (profil_modifié, doublons retirés)."""
    mandats = profil.get("mandats")
    if not isinstance(mandats, list):
        return profil, []

    electifs = {
        _cle(m): m for m in mandats
        if isinstance(m, dict)
        and m.get("categorie") == "mandat_electif"
        and m.get("categorie_source") == "europarl"
    }

    conserves: list[dict[str, Any]] = []
    retires: list[dict[str, Any]] = []
    for mandat in mandats:
        doublon = (
            isinstance(mandat, dict)
            and mandat.get("categorie") == "autre"
            and mandat.get("categorie_source") == "europarl"
            and _cle(mandat) in electifs
        )
        if doublon:
            # Le libellé de fonction explicite est porté par l'entrée retirée
            # (« Membre du Parlement européen »), la classification par celle qui
            # reste (« Membre »). Le retrait ne doit pas appauvrir la fiche : la
            # même règle que `normalize_europarl.dedupliquer_appartenances`.
            garde = electifs.get(_cle(mandat))
            if garde is not None and (garde.get("fonction") or "") == "Membre" and mandat.get("fonction"):
                garde["fonction"] = mandat["fonction"]
            retires.append(mandat)
        else:
            conserves.append(mandat)

    if retires:
        profil["mandats"] = conserves
    return profil, retires


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES_DIR), metavar="DOSSIER",
                        help="Le pivot, et lui seul : le brut garde les deux entrées de la source.")
    parser.add_argument("--apply", action="store_true", help="Écrit les profils. Sans cette option, rapport seul.")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic).")
    args = parser.parse_args(argv)

    repertoire = Path(args.profiles_dir)
    if not repertoire.is_dir():
        print(f"[!] Répertoire introuvable : {repertoire}", file=sys.stderr)
        return 2

    total = 0
    profils = 0
    for chemin in sorted(repertoire.glob("*.json")):
        if chemin.name.endswith(".cosignatures.json"):
            continue
        slug = chemin.name.replace(".pivot.json", "").replace(".json", "")
        if args.only and slug != args.only:
            continue
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  [!] Lecture impossible ({chemin.name}) : {exc}", file=sys.stderr)
            continue
        if not isinstance(profil, dict):
            continue
        profil, retires = purge_profil(profil)
        if not retires:
            continue
        profils += 1
        total += len(retires)
        print(f"  {slug} : {len(retires)} doublon(s) européen(s) retiré(s)")
        if args.apply:
            ecrire_profil_json(chemin, profil)

    mode = "APPLIQUÉ" if args.apply else "SIMULATION (--apply pour écrire)"
    print(f"\n[{mode}] {repertoire} — {total} doublon(s) retiré(s) sur {profils} profil(s).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
