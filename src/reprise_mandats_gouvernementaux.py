#!/usr/bin/env python3
"""
reprise_mandats_gouvernementaux.py — Sort de `commission` les mandats que le
référentiel AN type lui-même comme une appartenance au gouvernement (#730).

    python3 src/reprise_mandats_gouvernementaux.py            # simulation
    python3 src/reprise_mandats_gouvernementaux.py --apply    # applique

Le constat
----------
Huit mandats ministériels sont publiés avec `categorie: "commission"` — tous sur
l'organe `Gouvernement`, avec pour `fonction` un intitulé de portefeuille. Ils
gonflent le bloc « Commissions » de la fiche candidat, où ils n'ont rien à faire.

**Aucun chemin de collecte actuel ne les produit** : `GOUVERNEMENT` est
volontairement absent de `_TYPE_ORGANE_TO_CATEGORIE` (l'appartenance est
collectée ailleurs, en `fonction_gouvernementale`). Ce sont des entrées gelées,
que la fusion additive conserve — la même famille que #718 et #729.

Le critère de détection, et les deux qui ont été écartés par la mesure
------------------------------------------------------------------
**Retenu : le typage du référentiel.** L'index d'organes AN porte, pour chaque
organe, son `type` ; `Gouvernement` y est typé `GOUVERNEMENT`, et c'est le seul
libellé du référentiel dans ce cas. On ne classe donc rien par ressemblance de
libellé — on lit ce que la source déclare de l'organe. Mesuré : **8 entrées**.

**Écarté — le croisement (profil × période) seul** : il capture **1 036**
mandats, pas 8. Un ministre garde ses commissions et ses groupes d'amitié, et
les compter comme ministériels serait un contresens.

**Écarté — le vocabulaire ministériel de #474** (`FONCTIONS_MINISTERIELLES`) : il
capture **0**. Il est fait pour les `libQualite` courts d'AMO30 (« Ministre »,
« Secrétaire d'État »), quand ces entrées portent l'intitulé complet du
portefeuille. Le rapprocher par préfixe serait la classification par libellé que
#639, #718 et #729 écartent toutes les trois.

Le sort de chaque entrée, lui, se décide par le croisement
----------------------------------------------------------
Une fois l'entrée reconnue, ce qu'on en fait dépend de ce que le profil porte
déjà — et c'est là que le croisement (profil × période) trouve sa place :

- **période déjà couverte** par un `fonction_gouvernementale` du même profil :
  l'entrée est **retirée**. Le fait n'est perdu nulle part ;
- **période non couverte** : l'entrée est **requalifiée** en
  `fonction_gouvernementale`. La retirer effacerait du profil une période
  ministérielle réelle — 2 des 8, sur `yael-braun-pivet` et `damien-abad`.

Rien n'est inventé dans les deux cas : la période, le libellé et la fonction
sont ceux que l'entrée portait déjà. Seule la catégorie change, ou l'entrée
disparaît au profit d'une autre qui dit la même chose.

Garde-fous
----------
- `--apply` explicite, simulation par défaut ;
- un profil dont le nom ne figure dans aucune fiche de gouvernement publiée est
  **ignoré** : sans appartenance publiée, le croisement ne peut rien décider, et
  on ne retire jamais sur une absence de référence (résilience #241) ;
- idempotent : une seconde exécution ne trouve plus rien.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import ecrire_profil_json  # noqa: E402

#: L'index d'organes du cache AN, d'où vient le typage.
DEFAUT_INDEX_ORGANES = Path(".cache") / "acteurs_historique_an" / "index_organes_v2.json"
DEFAUT_GOUVERNEMENTS = Path("pivot_data") / "gouvernements"
DEFAUT_PROFILS = Path("raw_data") / "profiles"

#: Le type d'organe que le référentiel donne à une appartenance gouvernementale.
TYPE_ORGANE_GOUVERNEMENT = "GOUVERNEMENT"

CATEGORIE_CIBLE = "fonction_gouvernementale"


def libelles_gouvernementaux(chemin_index: Path) -> set[str]:
    """Libellés d'organe que le RÉFÉRENTIEL type `GOUVERNEMENT`.

    Rend un ensemble vide si l'index est absent ou illisible : sans lui, aucune
    entrée n'est reconnue et la reprise ne fait rien. Un critère qui ne peut pas
    s'établir ne doit jamais se deviner (§2 règle 5).
    """
    try:
        with open(chemin_index, encoding="utf-8") as f:
            index = json.load(f)
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        o["nom"] for o in index.values()
        if isinstance(o, dict) and o.get("type") == TYPE_ORGANE_GOUVERNEMENT and o.get("nom")
    }


def periodes_ministerielles(dossier: Path) -> dict[str, list[tuple[str, str]]]:
    """`membre_id` (le slug) → périodes d'appartenance publiées par les fiches.

    **Le slug, jamais le nom d'affichage.** Un profil brut ne porte pas de champ
    `nom` — il vit dans `identite` —, et apparier deux corpus sur un nom
    d'affichage est le geste que #487 et #668 ont fait payer : un *nom d'usage*
    change, un identifiant non. `membre_id` est le slug du profil, donc son nom
    de fichier.
    """
    periodes: dict[str, list[tuple[str, str]]] = {}
    for chemin in sorted(dossier.glob("*.json")):
        try:
            with open(chemin, encoding="utf-8") as f:
                fiche = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        for membre in fiche.get("membres") or []:
            slug, debut = membre.get("membre_id"), membre.get("debut")
            if slug and debut:
                periodes.setdefault(slug, []).append((debut, membre.get("fin") or "9999-12-31"))
    return periodes


def _chevauchent(d1: Any, f1: Any, d2: str, f2: str) -> bool:
    """Deux intervalles se recouvrent-ils ? Une borne de fin absente est ouverte."""
    if not d1:
        return False
    return d1 <= f2 and d2 <= (f1 or "9999-12-31")


def _couvre(d1: Any, f1: Any, d2: Any, f2: Any) -> bool:
    """`[d1, f1]` contient-il `[d2, f2]` ENTIÈREMENT ?

    Le chevauchement ne suffit pas pour décider qu'une période est « déjà dite »
    par le profil : deux intervalles qui se touchent d'un jour décriraient des
    faits différents, et retirer l'entrée sur cette base perdrait la partie non
    couverte. Le recouvrement complet, lui, garantit que rien ne se perd.
    """
    if not d2:
        return False
    return (d1 or "9999-12-31") <= d2 and (f2 or "9999-12-31") <= (f1 or "9999-12-31")


def reprendre_profil(
    profil: dict[str, Any],
    libelles_gouv: set[str],
    periodes: list[tuple[str, str]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Rend `(profil, retirés, requalifiés)`.

    `periodes` sont les appartenances PUBLIÉES de cette personne : elles servent
    à confirmer que l'entrée décrit bien une période ministérielle, jamais à la
    détecter — le croisement seul capturerait 1 036 mandats.
    """
    mandats = profil.get("mandats") or []
    couvertes = [
        m for m in mandats
        if m.get("categorie") == CATEGORIE_CIBLE
    ]
    conserves: list[dict[str, Any]] = []
    retires: list[dict[str, Any]] = []
    requalifies: list[dict[str, Any]] = []

    for mandat in mandats:
        reconnu = (
            mandat.get("categorie") != CATEGORIE_CIBLE
            and (mandat.get("label") or "") in libelles_gouv
            and any(_chevauchent(mandat.get("debut"), mandat.get("fin"), d, f)
                    for d, f in periodes)
        )
        if not reconnu:
            conserves.append(mandat)
            continue
        deja_dit = any(
            _couvre(c.get("debut"), c.get("fin"), mandat.get("debut"), mandat.get("fin"))
            for c in couvertes
        )
        if deja_dit:
            retires.append(mandat)
        else:
            requalifie = {**mandat, "categorie": CATEGORIE_CIBLE}
            requalifies.append(requalifie)
            conserves.append(requalifie)

    if retires or requalifies:
        profil["mandats"] = conserves
    return profil, retires, requalifies


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--profiles-dir", default=str(DEFAUT_PROFILS), metavar="DOSSIER")
    parser.add_argument("--gouvernements-dir", default=str(DEFAUT_GOUVERNEMENTS), metavar="DOSSIER")
    parser.add_argument("--index-organes", default=str(DEFAUT_INDEX_ORGANES), metavar="FICHIER")
    parser.add_argument("--apply", action="store_true",
                        help="Écrit les profils. Sans lui, simulation.")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic).")
    args = parser.parse_args(argv)

    libelles_gouv = libelles_gouvernementaux(Path(args.index_organes))
    if not libelles_gouv:
        print(
            f"[!] Index d'organes absent ou illisible ({args.index_organes}) : aucune "
            "entrée ne peut être reconnue, rien n'est modifié (#730).",
            file=sys.stderr,
        )
        return 2
    print(f"  -> Libellés d'organe typés {TYPE_ORGANE_GOUVERNEMENT} : {sorted(libelles_gouv)}")

    periodes = periodes_ministerielles(Path(args.gouvernements_dir))
    print(f"  -> Appartenances publiées : {len(periodes)} personne(s).")

    chemins = sorted(p for p in Path(args.profiles_dir).glob("*.json")
                     if not p.name.startswith("."))
    if args.only:
        chemins = [p for p in chemins if p.stem == args.only]

    n_profils = n_retires = n_requalifies = n_ignores = 0
    for chemin in chemins:
        try:
            with open(chemin, encoding="utf-8") as f:
                profil = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        # `<slug>.pivot.json` au pivot, `<slug>.json` au brut : la reprise doit
        # passer aux DEUX étages, parce que `merge_pivot_profile` est additif lui
        # aussi — retirer une entrée du brut ne la retire pas du publié (#729).
        slug = chemin.stem.removesuffix(".pivot")
        if slug not in periodes:
            n_ignores += 1
            continue
        profil, retires, requalifies = reprendre_profil(profil, libelles_gouv, periodes[slug])
        if not retires and not requalifies:
            continue
        n_profils += 1
        n_retires += len(retires)
        n_requalifies += len(requalifies)
        print(f"  {chemin.stem} : {len(retires)} retiré(s), {len(requalifies)} requalifié(s)")
        for m in retires:
            print(f"      − [{m.get('categorie')}] {m.get('label')} — {m.get('fonction') or m.get('type')}")
        for m in requalifies:
            print(f"      ~ [{CATEGORIE_CIBLE}] {m.get('label')} — {m.get('fonction') or m.get('type')}")
        if args.apply:
            ecrire_profil_json(chemin, profil)

    entete = "=== APPLIQUÉ ===" if args.apply else "=== SIMULATION (--apply pour écrire) ==="
    print(f"\n{entete}")
    print(f"  Profils modifiés          : {n_profils}")
    print(f"  Entrées retirées          : {n_retires}")
    print(f"  Entrées requalifiées      : {n_requalifies}")
    print(f"  Ignorés (aucune appartenance publiée) : {n_ignores}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
