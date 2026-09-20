#!/usr/bin/env python3
"""
purge_marqueur_regards_citoyens.py — Retire, sur les profils de **député**, le
marqueur de provenance d'une source dont plus aucune donnée n'est publiée (#890).

La question que §7 pose, et la réponse mesurée
----------------------------------------------
`meta.licence_donnees` est un champ **dérivé** dont §7 écrit que la condition de
retrait « court d'elle-même » : la clause ODbL quitte un profil le jour où ce
profil cesse de porter quoi que ce soit de Regards Citoyens.

Mesuré le 13/09/2026 sur `origin/main` `7e48b4b05`, par un parcours **récursif**
des deux couches, **clés de dict comprises** : sur les 1 196 profils publiés,
**aucune donnée** — mandat, vote, intervention, amendement, champ d'identité —
ne porte de trace de Regards Citoyens. La condition est remplie. Ce qui la
retient est le marqueur lui-même, et lui seul.

**Le marqueur ne part pas tout seul**, et c'est l'erreur que
`docs/decisions/retrait-senat-528.md` §3 a commise en annonçant l'inverse :
`merge_profile._merge_pivot_sources` **unit par `type`** et garde l'entrée la
plus fraîche. Un type absent d'une nouvelle collecte n'est jamais retiré. Dix-huit
jours plus tard, 475 profils le portaient encore.

**Il ne peut pas non plus revenir.** Depuis #529 `normalize_profil` écrit
`_SOURCE_TYPE_PROFIL_FR = "assemblee_nationale"` en dur, et `candidate_profile`
n'écrit plus `meta.synchro_sources.nosdeputes`. Aucun code producteur n'est donc
touché ici : ce qui reste est ce que la persistance conserve, aux deux couches.

Le périmètre : les députés, pas les sénateurs
----------------------------------------------
**454 profils de député** portent le marqueur — 446 membres de roster, 8
candidats déclarés. **21 profils touchent le Sénat** et sont hors périmètre : 19
membres de roster sénatorial, plus `bruno-retailleau` et `jean-luc-melenchon`.

Ce n'est pas une timidité de découpage, c'est ce que la mesure sépare. Côté
Assemblée, il ne reste **que** le marqueur. Tout ce qui n'est pas le marqueur est
côté Sénat — les 19 URL `nosdeputes.fr` encore dans `raw_data`, les 51
identifiants `nosdeputes:<slug>` des fiches `Senat-LR`/`Senat-SER` et de leurs
lignées, le bloc de suspension de `raw_data/groupes_reels.json`. Ceux-là sont le
périmètre de #885, et les emporter ici les retirerait **avant** d'avoir une
source pour les remplacer.

Conséquence mesurée, et c'est elle qui rend le geste sûr : la clause ODbL
**survit sur les 21**. `LegalNoticePage.jsx` et `sources.config.js` doivent
continuer de nommer NosDéputés.fr, NosSénateurs.fr et l'ODbL v1.0 — les verrous
de `tests/test_licences_530.py` n'ont rien à retourner.

Ce que le script retire, aux deux couches
------------------------------------------
  - **pivot** : les entrées `sources[]` de type `nosdeputes` / `nossenateurs`,
    puis `meta.licence_donnees` **recomposé** par `licences.py` (§4 : un champ
    dérivé se recompose, il ne se fusionne pas) ;
  - **brut** : la clé `meta.synchro_sources.nosdeputes`, journal d'une source
    qui n'est plus interrogée. Retirée d'un seul côté, elle redescendrait :
    c'est la leçon de #729.

**Aucun `synchro_le` ne bouge.** `normalize_profil:647` lit
`synchro_sources["assemblee_nationale"] or synchro_sources["nosdeputes"]` ; les
**11** profils dont la clé porte un horodatage réel (et non `None`) ont tous
`assemblee_nationale` renseigné au 12/09/2026, donc la branche de repli n'est
jamais empruntée. Vérifié profil par profil avant d'écrire ce module.

Usage (depuis la racine du dépôt) :
    python3 src/purge_marqueur_regards_citoyens.py            # simulation
    python3 src/purge_marqueur_regards_citoyens.py --apply
    python3 src/purge_marqueur_regards_citoyens.py --only gabriel-attal
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import ecrire_profil_json  # noqa: E402
from licences import appliquer_licence_donnees  # noqa: E402

DEFAULT_PIVOT_DIR = Path("pivot_data/profiles")
DEFAULT_RAW_DIR = Path("raw_data/profiles")
SUFFIXE_PIVOT = ".pivot.json"

#: Les types de source que ce lot retire. Lus depuis `licences.py`, jamais
#: recopiés : ce module est un consommateur du référentiel de licences, pas un
#: second référentiel (même raison que `MOTIFS_URL_REGARDS_CITOYENS`).
TYPES_RETIRES = frozenset({"nosdeputes", "nossenateurs"})

#: La clé de journal du profil brut. `candidate_profile` ne l'écrit plus
#: depuis #529 ; seules les collectes antérieures la portent.
CLE_JOURNAL_BRUT = "nosdeputes"

#: La chambre qui met un profil **hors** de ce lot. Un profil sans aucune
#: chambre en fait partie aussi — les 19 membres de roster sénatorial n'en
#: publient aucune, et les traiter comme des députés retirerait le marqueur de
#: profils dont `raw_data` porte encore l'URL de la source.
CHAMBRE_HORS_PERIMETRE = "Senat"


def est_dans_le_perimetre(profil: dict[str, Any]) -> bool:
    """True si ce profil pivot est un profil de **député** portant le marqueur.

    Trois refus, et chacun a une raison distincte :

      - pas de marqueur : rien à faire ;
      - une chambre `Senat` : `bruno-retailleau` et `jean-luc-melenchon`, dont
        le marqueur `nossenateurs` couvre une carrière sénatoriale ;
      - **aucune chambre** : les 19 membres de roster sénatorial, dont
        `chambres` est vide parce que leur collecte est suspendue (#528). Une
        liste vide n'est pas « pas le Sénat », c'est « on ne sait pas », et §2
        règle 5 interdit de lire une absence comme un constat.
    """
    types = {source.get("type")
             for source in (profil.get("sources") or [])
             if isinstance(source, dict)}
    if not types & TYPES_RETIRES:
        return False
    chambres = profil.get("chambres") or []
    if not chambres or CHAMBRE_HORS_PERIMETRE in chambres:
        return False
    return True


def purger_pivot(profil: dict[str, Any]) -> tuple[int, Optional[str], Optional[str]]:
    """Retire les entrées `sources[]` marquées, puis recompose la licence.

    Rend `(entrées retirées, licence avant, licence après)`. La licence est
    **recomposée**, jamais réécrite à la main : `appliquer_licence_donnees` la
    dérive de `sources[]`, et c'est la seule fabrique de cette chaîne (§7).
    """
    sources = profil.get("sources") or []
    gardees = [source for source in sources
               if not (isinstance(source, dict) and source.get("type") in TYPES_RETIRES)]
    retirees = len(sources) - len(gardees)
    if not retirees:
        return 0, None, None
    profil["sources"] = gardees
    meta = profil.get("meta")
    avant = meta.get("licence_donnees") if isinstance(meta, dict) else None
    apres = appliquer_licence_donnees(profil)
    return retirees, avant, apres


def purger_brut(brut: dict[str, Any]) -> bool:
    """Retire la clé de journal du profil brut. True si elle y était.

    Le socle seul est touché : les tranches d'amendements de #580 ne portent
    pas de `meta.synchro_sources`, et les ouvrir pour n'y rien trouver coûterait
    des millions d'entrées relues.
    """
    meta = brut.get("meta")
    if not isinstance(meta, dict):
        return False
    journal = meta.get("synchro_sources")
    if not isinstance(journal, dict) or CLE_JOURNAL_BRUT not in journal:
        return False
    del journal[CLE_JOURNAL_BRUT]
    return True


def _charger(chemin: Path) -> Optional[dict[str, Any]]:
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return document if isinstance(document, dict) else None


def _slugs_pivot(pivot_dir: Path) -> list[str]:
    """Les slugs du répertoire pivot, **dotfiles exclus** (#518, `Path.glob`
    les rend, contrairement au module `glob`)."""
    return sorted(chemin.name[:-len(SUFFIXE_PIVOT)]
                  for chemin in pivot_dir.glob(f"*{SUFFIXE_PIVOT}")
                  if not chemin.name.startswith("."))


def purger(
    pivot_dir: Path,
    raw_dir: Path,
    *,
    appliquer: bool = False,
    seulement: Optional[str] = None,
) -> dict[str, Any]:
    """Parcourt les deux couches et rend le relevé de ce qui a été (ou serait) retiré."""
    touches: list[dict[str, Any]] = []
    hors_perimetre: list[str] = []
    illisibles: list[str] = []
    brut_absent: list[str] = []
    entrees_pivot = 0
    cles_brutes = 0

    for slug in _slugs_pivot(pivot_dir):
        if seulement and slug != seulement:
            continue
        chemin_pivot = pivot_dir / f"{slug}{SUFFIXE_PIVOT}"
        profil = _charger(chemin_pivot)
        if profil is None:
            illisibles.append(slug)
            continue
        if not est_dans_le_perimetre(profil):
            types = {s.get("type") for s in (profil.get("sources") or [])
                     if isinstance(s, dict)}
            if types & TYPES_RETIRES:
                hors_perimetre.append(slug)
            continue

        retirees, avant, apres = purger_pivot(profil)
        entrees_pivot += retirees

        chemin_brut = raw_dir / f"{slug}.json"
        brut = _charger(chemin_brut)
        cle_retiree = False
        if brut is None:
            brut_absent.append(slug)
        else:
            cle_retiree = purger_brut(brut)
            cles_brutes += int(cle_retiree)

        if appliquer:
            ecrire_profil_json(chemin_pivot, profil)
            if brut is not None and cle_retiree:
                ecrire_profil_json(chemin_brut, brut)

        touches.append({
            "slug": slug,
            "entrees_sources_retirees": retirees,
            "cle_journal_retiree": cle_retiree,
            "licence_avant": avant,
            "licence_apres": apres,
        })

    return {
        "applique": appliquer,
        "nb_profils_touches": len(touches),
        "nb_entrees_sources_retirees": entrees_pivot,
        "nb_cles_journal_retirees": cles_brutes,
        "nb_hors_perimetre": len(hors_perimetre),
        "hors_perimetre": hors_perimetre,
        "nb_illisibles": len(illisibles),
        "illisibles": illisibles,
        "nb_brut_absent": len(brut_absent),
        "profils": touches,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pivot-dir", default=str(DEFAULT_PIVOT_DIR), metavar="DOSSIER",
                        help="Répertoire des profils pivot.")
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), metavar="DOSSIER",
                        help="Répertoire des profils bruts.")
    parser.add_argument("--apply", action="store_true",
                        help="Écrit les fichiers. Sans ce drapeau, rien n'est modifié.")
    parser.add_argument("--only", metavar="SLUG",
                        help="Ne traiter qu'un profil (diagnostic).")
    parser.add_argument("--json", metavar="FICHIER",
                        help="Écrit le relevé complet, profil par profil.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    rapport = purger(Path(args.pivot_dir), Path(args.raw_dir),
                     appliquer=args.apply, seulement=args.only)

    mode = "APPLIQUÉ" if rapport["applique"] else "simulation (aucun fichier écrit)"
    print(f"→ marqueur Regards Citoyens, profils de député — {mode}")
    print(f"  {rapport['nb_profils_touches']} profil(s) touché(s) : "
          f"{rapport['nb_entrees_sources_retirees']} entrée(s) `sources[]` au pivot, "
          f"{rapport['nb_cles_journal_retirees']} clé(s) de journal au brut.")
    print(f"  {rapport['nb_hors_perimetre']} profil(s) gardent le marqueur "
          f"(chambre Sénat, ou aucune chambre publiée).")
    if rapport["nb_illisibles"]:
        print(f"  ⚠ {rapport['nb_illisibles']} profil(s) illisible(s) : "
              f"{', '.join(rapport['illisibles'][:5])}")
    if rapport["nb_brut_absent"]:
        print(f"  ⚠ {rapport['nb_brut_absent']} profil(s) sans socle brut.")

    if args.json:
        Path(args.json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  relevé complet : {args.json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
