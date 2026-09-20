#!/usr/bin/env python3
"""
retrait_residus_senat_908.py — Le dernier reste de Regards Citoyens (#908).

Ce que ce script clôt
---------------------
#890 a retiré le marqueur `nosdeputes` / `nossenateurs` des profils de
**député**, et s'est arrêté aux deux profils qui touchent le Sénat :
`bruno-retailleau` et `jean-luc-melenchon`. La raison était juste — leur
marqueur couvrait alors une carrière sénatoriale que rien d'autre ne portait, et
le retirer aurait publié un trou (§2 règle 5).

#885 a branché `data.senat.fr`. La carrière est publiée, datée, sourcée : 133
appartenances sur ces deux profils. La condition que #890 posait est remplie, et
ce script en tire la conséquence.

Ce qu'il retire, aux deux couches
----------------------------------
1. **Les appartenances héritées qu'un organe sénatorial remplace.**
   `retrait_heritage_senat.APPARIEMENTS_HERITES` les nomme une par une, et le
   retrait exige que le remplaçant soit **effectivement publié** sur le profil.
   Le pivot et le brut sont traités séparément, chacun contre sa propre source
   de remplaçants : `audit_collecte_vs_publie` les compare, seuil 0, et retirer
   d'un seul côté bloque le commit (#729).

2. **Le marqueur lui-même** — les entrées `sources[]` au pivot, la clé
   `meta.synchro_sources.nosdeputes` au brut — mais **seulement une fois qu'il
   ne couvre plus rien**. C'est la garde centrale de ce script : tant qu'une
   appartenance héritée subsiste sur le profil, l'attribution ODbL lui reste due
   (§2 règle 2, AGENTS.md §7), et le marqueur reste. La mécanique du retrait est
   celle de #890, réutilisée telle quelle plutôt que réécrite.

`meta.licence_donnees` est **recomposé**, jamais réécrit : c'est un champ dérivé
et `licences.appliquer_licence_donnees` en est la seule fabrique (§7, #909).

Ce qu'il ne touche pas
----------------------
Les **agrégats** — fiches de groupe, de lignée, de parti, de gouvernement. Ils
se recomposent au run suivant à partir des profils, et les réécrire ici ferait
de ce script une seconde fabrique. Même partage que #890, qui n'a touché que les
profils : `docs/decisions/retrait-marqueur-regards-citoyens-deputes-890.md`.

Les **phrases** de `couverture[].preuve` qui nomment la source : elles sont
dérivées par `couverture_profil.deriver` et se recomposent de la même façon. Une
donnée résiduelle et une phrase qui la décrit ne se retirent pas par le même
geste, et les confondre a déjà coûté un lot.

Usage :
    python3 src/retrait_residus_senat_908.py --dry-run
    python3 src/retrait_residus_senat_908.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import ecrire_profil_json  # noqa: E402
from purge_marqueur_regards_citoyens import (  # noqa: E402
    CLE_JOURNAL_BRUT,
    TYPES_RETIRES,
    purger_brut,
    purger_pivot,
)
from retrait_heritage_senat import (  # noqa: E402
    mandats_apparies_remplaces,
    mandats_bruts_apparies_remplaces,
    mandats_senatoriaux_orphelins,
)

DEFAULT_PIVOT_DIR = Path("pivot_data/profiles")
DEFAULT_RAW_DIR = Path("raw_data/profiles")
SUFFIXE_PIVOT = ".pivot.json"


def porte_le_marqueur(profil: dict[str, Any]) -> bool:
    """True si `sources[]` déclare encore une provenance Regards Citoyens."""
    return any(isinstance(s, dict) and s.get("type") in TYPES_RETIRES
               for s in (profil.get("sources") or []))


def porte_la_cle_brute(brut: dict[str, Any]) -> bool:
    """True si le brut porte encore la clé de journal `nosdeputes`.

    Le marqueur a deux formes et une seule se voit d'un parcours de **valeurs** :
    l'entrée `sources[]` au pivot, et cette **clé de dictionnaire** au brut. La
    seconde est celle qu'un `grep` sur les valeurs manque — le piège payé quatre
    fois en instruisant #885.
    """
    journal = (brut.get("meta") or {}).get("synchro_sources")
    return isinstance(journal, dict) and CLE_JOURNAL_BRUT in journal


#: Les champs que la garde ne compte pas, et ils ne sont pas exclus pour la
#: même raison.
#:
#: `sources` et `synchro_sources` **sont** le marqueur : les compter rendrait la
#: garde circulaire, le marqueur se retiendrait lui-même.
#:
#: `couverture` est autre chose — un champ **dérivé**, recomposé à chaque run
#: par `couverture_profil.deriver`, et dont les `preuve` sont des **phrases qui
#: décrivent** la collecte. Celle de `bruno-retailleau` raconte un certificat
#: TLS expiré sur `archive.nossenateurs.fr` ; elle cite un domaine, elle ne
#: publie aucune donnée qui en vienne. Une donnée résiduelle et une phrase qui
#: la décrit ne se retirent pas par le même geste, et l'attribution (§2 règle 2)
#: n'est due que pour la première.
_CHEMINS_DU_MARQUEUR = ("sources", "synchro_sources", "couverture")


def traces_regards_citoyens(document: dict[str, Any]) -> list[str]:
    """Les chemins de champ portant encore une trace de Regards Citoyens.

    ## Pourquoi un parcours, et non l'absence de `categorie_source`

    La première version de cette garde listait les appartenances **non
    estampillées**, et refusait le retrait tant qu'il en restait. C'est trop
    large, et `jean-luc-melenchon` le montre : ses 18 entrées sans
    `categorie_source` sont des mandats de **député** — « Commission des
    affaires étrangères », 2017-2022 — qui ne doivent rien à Regards Citoyens.
    Une estampille absente veut dire « personne n'a établi cette catégorie »
    (#718), jamais « cela vient de NosDéputés ».

    #890 avait tranché sur la bonne mesure : un parcours **récursif**, **clés de
    dict comprises**, de ce que le document porte réellement. C'est celle-là que
    la garde reprend — la même que celle qui a servi à compter les traces
    restantes, pour que la décision et le constat ne divergent pas.

    Les deux champs qui **sont** le marqueur sont exclus : les compter rendrait
    la garde circulaire.

    Returns:
        Les chemins de champ, un par trace. Vide quand le marqueur ne couvre
        plus rien — la condition de son retrait (§2 règle 2).
    """
    trouves: list[str] = []

    def parcourir(noeud: Any, chemin: str) -> None:
        if isinstance(noeud, dict):
            for cle, valeur in noeud.items():
                if cle in _CHEMINS_DU_MARQUEUR:
                    continue
                if isinstance(cle, str) and any(m in cle.lower() for m in TYPES_RETIRES):
                    trouves.append(f"{chemin}.{cle}")
                parcourir(valeur, f"{chemin}.{cle}")
        elif isinstance(noeud, list):
            for element in noeud:
                parcourir(element, f"{chemin}[]")
        elif isinstance(noeud, str) and any(m in noeud.lower() for m in TYPES_RETIRES):
            trouves.append(chemin)

    parcourir(document, "")
    return trouves


def traiter(
    slug: str,
    pivot: dict[str, Any],
    brut: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Applique les deux retraits sur un profil. Rend le compte rendu."""
    rendu: dict[str, Any] = {
        "slug": slug,
        "orphelins": 0,
        "mandats_pivot": 0,
        "mandats_brut": 0,
        "marqueur_retire": False,
        "marqueur_retenu_par": [],
        "licence_avant": None,
        "licence_apres": None,
    }

    # D'ABORD les orphelins : ce sont d'anciennes formes d'entrées que la
    # collecte publie désormais autrement, et les laisser fausserait la garde
    # ci-dessous — une appartenance héritée dont le remplaçant coexiste avec sa
    # propre version périmée resterait retenue par un doublon.
    if brut is not None:
        orphelins = mandats_senatoriaux_orphelins(pivot, brut)
        if orphelins:
            pivot["mandats"] = [m for m in pivot["mandats"] if m not in orphelins]
            rendu["orphelins"] = len(orphelins)

    remplaces = mandats_apparies_remplaces(pivot)
    if remplaces:
        pivot["mandats"] = [m for m in pivot["mandats"] if m not in remplaces]
        rendu["mandats_pivot"] = len(remplaces)

    if brut is not None:
        remplaces_bruts = mandats_bruts_apparies_remplaces(brut)
        if remplaces_bruts:
            brut["mandats"] = [m for m in brut["mandats"] if m not in remplaces_bruts]
            rendu["mandats_brut"] = len(remplaces_bruts)

    # La garde : le marqueur ne part que s'il ne couvre plus rien.
    #
    # Elle ne se prononce que sur un profil qui porte effectivement un marqueur.
    # Sans ce test, le rendu annonçait « marqueur RETENU par 18 appartenances »
    # sur `jean-luc-melenchon`, qui n'en porte aucun côté pivot : ses 18 entrées
    # non estampillées sont des mandats de **député**, sans rapport avec
    # Regards Citoyens. Un rapport qui nomme un marqueur inexistant fait
    # chercher un défaut là où il n'y en a pas.
    if not (porte_le_marqueur(pivot) or (brut is not None and porte_la_cle_brute(brut))):
        return rendu

    restantes = traces_regards_citoyens(pivot)
    if brut is not None:
        restantes += [f"brut{c}" for c in traces_regards_citoyens(brut)]
    if restantes:
        rendu["marqueur_retenu_par"] = restantes
        return rendu

    if porte_le_marqueur(pivot):
        _, avant, apres = purger_pivot(pivot)
        rendu["marqueur_retire"] = True
        rendu["licence_avant"], rendu["licence_apres"] = avant, apres
    if brut is not None and purger_brut(brut):
        rendu["marqueur_retire"] = True
    return rendu


def _charger(chemin: Path) -> Optional[dict[str, Any]]:
    if not chemin.exists():
        return None
    import json
    return json.loads(chemin.read_text(encoding="utf-8"))


def retirer(
    pivot_dir: Path = DEFAULT_PIVOT_DIR,
    raw_dir: Path = DEFAULT_RAW_DIR,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Parcourt les profils, applique, écrit. Rend un compte rendu par profil touché."""
    rendus: list[dict[str, Any]] = []
    for chemin_pivot in sorted(pivot_dir.glob(f"*{SUFFIXE_PIVOT}")):
        slug = chemin_pivot.name[: -len(SUFFIXE_PIVOT)]
        pivot = _charger(chemin_pivot)
        if pivot is None:
            continue
        chemin_brut = raw_dir / f"{slug}.json"
        brut = _charger(chemin_brut)

        rendu = traiter(slug, pivot, brut)
        if not (rendu["orphelins"] or rendu["mandats_pivot"]
                or rendu["mandats_brut"] or rendu["marqueur_retire"]):
            continue
        rendus.append(rendu)
        if dry_run:
            continue
        if rendu["orphelins"] or rendu["mandats_pivot"] or rendu["marqueur_retire"]:
            ecrire_profil_json(chemin_pivot, pivot)
        if brut is not None and (rendu["mandats_brut"] or rendu["marqueur_retire"]):
            ecrire_profil_json(chemin_brut, brut)
    return rendus


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pivot-dir", type=Path, default=DEFAULT_PIVOT_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--dry-run", action="store_true",
                        help="mesure et affiche, n'écrit rien")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rendus = retirer(args.pivot_dir, args.raw_dir, args.dry_run)
    if not rendus:
        print("Aucun profil à traiter — rien d'hérité n'a de remplaçant publié.")
        return 0
    for r in rendus:
        print(f"\n{r['slug']}")
        if r["orphelins"]:
            print(f"  entrées sénatoriales périmées retirées : {r['orphelins']}")
        print(f"  appartenances retirées : {r['mandats_pivot']} au pivot, "
              f"{r['mandats_brut']} au brut")
        if r["marqueur_retire"]:
            print(f"  marqueur retiré — licence : {r['licence_avant']!r}")
            print(f"                       → {r['licence_apres']!r}")
        elif r["marqueur_retenu_par"]:
            print(f"  marqueur RETENU par {len(r['marqueur_retenu_par'])} appartenance(s) "
                  "sans remplaçant :")
            for label in r["marqueur_retenu_par"]:
                print(f"      {label!r}")
    if args.dry_run:
        print("\n(--dry-run : rien n'a été écrit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
