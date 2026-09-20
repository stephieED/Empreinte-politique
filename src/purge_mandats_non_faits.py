#!/usr/bin/env python3
"""
purge_mandats_non_faits.py — Retire des `mandats[]` les entrées qui ne sont pas
des mandats : les onglets de navigation de l'ancien site, publiés comme des
organes (#839, lot D).

Ce que ce sont
--------------
Mesuré le 12/09/2026 sur `origin/main` : `jean-luc-melenchon` publie cinq
« commissions » nommées `Amendements`, `Interventions`, `Questions`, `Vidéos` et
`Loi ou de résolution`. Ce sont les **onglets de la page** de l'ancien site,
aspirés comme des appartenances. Elles partagent trois propriétés, vérifiées
entrée par entrée et non supposées :

  - aucune date, ni `debut` ni `fin` ;
  - aucun `source_url` ;
  - `actif: true` — la fiche les publie donc comme des appartenances **en
    cours**, alors que le profil a quitté l'Assemblée en 2022.

Elles n'ont aucun équivalent dans AMO30, et le lot B ne pouvait pas les juger :
sans date, rien ne permet de les situer, et il les a déclarées `sans_date`
plutôt qu'introuvables (§2 règle 5).

Ce que ce script ne touche pas
------------------------------
**Les 8 autres entrées sans date, celles de `bruno-retailleau`, sont des organes
réels du Sénat** — commission de la culture, groupes d'études, groupe Chrétiens
d'Orient, commissions extra-parlementaires. Elles ont la même signature de forme
et ne sont pas des non-faits. La propriétaire a posé le 12/09/2026 la réserve
qui les protège : on ne touche pas au résidu du Sénat tant qu'une alternative
n'a pas été creusée (le Sénat est hors périmètre depuis #528, et rien ne
remplacerait ces entrées).

D'où le critère : une **liste close de libellés**, établie par mesure. Un
libellé absent de la liste est conservé, et le script le dit. C'est la même
prudence que #387 : un faux négatif laisse une entrée visible, un faux positif
supprime un mandat réel.

Les deux couches
----------------
La fusion est additive **aux deux étages** : un retrait appliqué au seul brut ne
descend jamais dans `pivot_data/` (#729). Le script prend `--profiles-dir` et se
lance deux fois.

Usage (depuis la racine du dépôt) :
    python3 src/purge_mandats_non_faits.py                                  # rapport seul
    python3 src/purge_mandats_non_faits.py --apply                          # applique au brut
    python3 src/purge_mandats_non_faits.py --profiles-dir pivot_data/profiles --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from json_io import ecrire_profil_json
from profil_brut import charger_socle

DEFAULT_PROFILES_DIR = Path("raw_data") / "profiles"

#: Liste **close** des libellés qui ne désignent pas un organe. Établie par
#: mesure sur le corpus publié, jamais a priori : un libellé qui n'y est pas
#: produit une non-correspondance, donc une entrée conservée.
LIBELLES_DE_NAVIGATION: frozenset[str] = frozenset({
    "Amendements",
    "Interventions",
    "Questions",
    "Vidéos",
    "Loi ou de résolution",
})


def est_un_non_fait(mandat: dict[str, Any]) -> bool:
    """Vrai si l'entrée est un onglet de page, et non un mandat.

    Les quatre conditions sont cumulatives. La dernière — `categorie_source`
    absente — fait que le script ne peut pas toucher une entrée qu'un
    référentiel a établie (#718), même si son libellé figurait dans la liste.
    """
    if not isinstance(mandat, dict):
        return False
    return (
        (mandat.get("label") or "").strip() in LIBELLES_DE_NAVIGATION
        and not mandat.get("debut")
        and not mandat.get("fin")
        and not mandat.get("source_url")
        and mandat.get("categorie_source") is None
    )


def purge_profil(profil: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retourne (profil_modifié, entrées_retirées)."""
    mandats = profil.get("mandats")
    if not isinstance(mandats, list):
        return profil, []
    conserves = [m for m in mandats if not est_un_non_fait(m)]
    retires = [m for m in mandats if est_un_non_fait(m)]
    if retires:
        profil["mandats"] = conserves
    return profil, retires


def _load(path: Path) -> Optional[dict[str, Any]]:
    """Lit le SOCLE, et lui seul (#580) : `mandats` y vit, le manifeste
    `amendements_partitionnes` est round-trippé tel quel."""
    try:
        data = charger_socle(path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [!] Lecture impossible ({path.name}) : {exc}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES_DIR), metavar="DOSSIER",
                        help="Couche à traiter : raw_data/profiles (défaut) ou pivot_data/profiles. "
                             "La fusion étant additive aux deux étages, un retrait doit être appliqué aux deux.")
    parser.add_argument("--apply", action="store_true", help="Écrit les profils. Sans cette option, rapport seul.")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic).")
    args = parser.parse_args(argv)

    repertoire = Path(args.profiles_dir)
    if not repertoire.is_dir():
        print(f"[!] Répertoire introuvable : {repertoire}", file=sys.stderr)
        return 2

    total = 0
    profils_touches = 0
    autres_sans_date = 0
    for chemin in sorted(p for p in repertoire.glob("*.json") if not p.name.endswith(".cosignatures.json")):
        slug = chemin.name.replace(".pivot.json", "").replace(".json", "")
        if args.only and slug != args.only:
            continue
        profil = _load(chemin)
        if profil is None:
            continue
        # Ce que le script laisse : même signature de forme, libellé hors liste.
        autres_sans_date += sum(
            1 for m in (profil.get("mandats") or [])
            if isinstance(m, dict) and m.get("actif") is True
            and not m.get("debut") and not m.get("fin") and not est_un_non_fait(m)
        )
        profil, retires = purge_profil(profil)
        if not retires:
            continue
        profils_touches += 1
        total += len(retires)
        print(f"  {slug} : {len(retires)} entrée(s) retirée(s) — "
              f"{', '.join(sorted((m.get('label') or '') for m in retires))}")
        if args.apply:
            ecrire_profil_json(chemin, profil)

    mode = "APPLIQUÉ" if args.apply else "SIMULATION (--apply pour écrire)"
    print(f"\n[{mode}] {repertoire} — {total} entrée(s) retirée(s) sur {profils_touches} profil(s).")
    print(f"{autres_sans_date} entrée(s) de même forme conservée(s) : libellé hors de la liste close "
          f"— ce sont des organes réels, dont ceux du Sénat (#528).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
