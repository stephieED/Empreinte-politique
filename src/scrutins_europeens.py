#!/usr/bin/env python3
"""
scrutins_europeens.py — L'index des scrutins du Parlement européen (#901).

Ce que cet index apporte, et que les profils ne portent pas
------------------------------------------------------------
Un vote européen est déjà publié avec tout ce qu'il faut pour l'afficher :
`scrutin_non_resolu` porte le titre, la nature, la référence de dossier, la
date, le numéro et l'URL du procès-verbal — mesuré le 14/09/2026 sur les
**11 013 votes** des 7 candidats déclarés à mandat européen, renseignés à 100 %
sauf la référence (96 %).

Ce qu'aucun profil ne peut porter, c'est le scrutin **vu d'ensemble** : combien
de voix pour, contre, abstention, et comment chaque groupe politique s'est
réparti. Le dump le publie sur **44 556 des 44 648 scrutins** (99,8 %), et c'est
la seule chose qui manquait vraiment.

Ce que cela permet, et la limite qui l'encadre
-----------------------------------------------
Juxtaposer, **sur un scrutin sourcé**, la position d'un député et la position
majoritaire de son groupe est un fait publiable (`AGENTS.md` §2 règle 7). Ce
que la même règle interdit, et que cet index ne doit jamais servir à fabriquer :
en faire un **compte** — « a voté contre son groupe 47 fois » — qui est l'indice
individuel mesuré contre une moyenne de groupe, réservé au rapport interne.

L'index publie donc des **effectifs par scrutin**, jamais un cumul par personne.

Le sort n'est pas déduit
-------------------------
Les totaux sont publiés bruts. Conclure « adopté » de `pour > contre` serait une
inférence : le Parlement européen vote aussi à la majorité qualifiée des membres
qui le composent, et le dump ne dit pas quelle règle s'appliquait. Un sort
déduit d'une comparaison aurait l'air d'un fait sourcé sans en être un
(§2 règle 5). `sort` reste donc absent, et `totaux` est ce qui le remplace.

L'identifiant
--------------
`pe:<voteid>`. Le `voteid` **vient de la source** — il est sur 100 % des
scrutins du dump — et le préfixe dit de quelle institution. C'est exactement ce
que #431 refusait de faire sous `an:` : ranger un scrutin européen dans un
espace de noms qui annonce l'Assemblée. Le nommer chez lui n'invente rien.

**Le `voteid` a deux formes, et elles sont reprises telles quelles.** Mesuré sur
les 5 571 scrutins cités : **4 855** sont des entiers (`7649`), **716** des
chaînes composites (`'2017-06-01 00:00:00-1.'`), espaces et point final compris.
Normaliser la seconde forme produirait une clé que la source ne connaît pas, et
la jointure depuis un profil se fait de toute façon sur `numero_scrutin`, repris
à l'identique. L'unicité, elle, est vérifiée — 5 571 identifiants distincts sur
5 571 — et un test la gèle : deux scrutins sous une même clé en écraseraient un.

Usage :
    python3 src/scrutins_europeens.py \\
        --profils-dir pivot_data/profiles \\
        --out pivot_data/scrutins_europeens.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from licences import LICENCE_PARLTRACK  # noqa: E402
from parltrack_dumps import ensure_dump, iter_dump_zst  # noqa: E402

#: Le dump que ce module lit. Une seule définition, partagée avec
#: `parltrack_dumps` : deux noms de fichier qui divergent produiraient un index
#: vide sans rien lever.
DUMP_VOTES = "ep_votes.json.zst"

SCHEMA_VERSION = "scrutins-europeens-v1"
DEFAULT_PROFILS_DIR = Path("pivot_data/profiles")
DEFAULT_SORTIE = Path("pivot_data/scrutins_europeens.json")

#: `votes` du dump → le nom publié de la position. Les trois clés que la source
#: emploie, et rien d'autre : une quatrième apparaîtrait sous son propre nom
#: plutôt que d'être rangée dans l'une des trois (§2 règle 5).
POSITIONS = {"+": "pour", "-": "contre", "0": "abstention"}

#: Préfixe de l'identifiant. Le pendant de `an:` pour l'Assemblée.
PREFIXE_ID = "pe"


class DumpVotesIndisponible(RuntimeError):
    """Le dump n'a pas pu être obtenu. Levée, jamais avalée : un index vide se
    lirait comme « aucun scrutin européen », et c'est la confusion que #510 a
    payée."""


def identifiant(voteid: Any) -> str:
    """`pe:<voteid>` — l'identifiant publié d'un scrutin européen."""
    return f"{PREFIXE_ID}:{voteid}"


def _reference(scrutin: dict[str, Any]) -> Optional[str]:
    """La référence de dossier, que la source publie tantôt en liste."""
    brut = scrutin.get("epref")
    if isinstance(brut, list):
        return brut[0] if brut else None
    return brut or None


def _repartition(votes: Any) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    """Les totaux, et leur ventilation par groupe politique.

    Rend `({position: effectif}, {groupe: {position: effectif}})`. Une position
    que la source ne publie pas est **absente** plutôt que valant `0` : « la
    source n'a pas publié ce décompte » et « personne n'a voté ainsi » ne sont
    pas la même chose (§2 règle 5).

    L'effectif par groupe est **recompté sur la liste nominative**, et non lu
    dans un total : la source publie les deux, et seule la liste garantit que le
    chiffre correspond aux personnes effectivement rangées sous ce groupe.
    """
    totaux: dict[str, int] = {}
    par_groupe: dict[str, dict[str, int]] = {}
    if not isinstance(votes, dict):
        return totaux, par_groupe
    for code, bloc in votes.items():
        position = POSITIONS.get(code)
        if position is None or not isinstance(bloc, dict):
            continue
        total = bloc.get("total")
        if isinstance(total, int):
            totaux[position] = total
        for groupe, membres in (bloc.get("groups") or {}).items():
            if not isinstance(membres, list):
                continue
            par_groupe.setdefault(groupe, {})[position] = len(membres)
    return totaux, par_groupe


def numeros_cites(profils_dir: Path) -> set[Any]:
    """Les `numero_scrutin` européens que les profils publiés citent.

    L'index suit le corpus, il ne le précède pas : indexer les 44 648 scrutins
    du dump pour en servir 5 571 ferait porter au dépôt huit fois le poids utile.
    C'est le même choix que `pivot_data/scrutins.json` côté Assemblée.
    """
    cites: set[Any] = set()
    for chemin in sorted(profils_dir.glob("*.pivot.json")):
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for vote in profil.get("votes") or []:
            if not isinstance(vote, dict):
                continue
            non_resolu = vote.get("scrutin_non_resolu")
            if not isinstance(non_resolu, dict):
                continue
            if non_resolu.get("institution") != "parlement_europeen":
                continue
            numero = non_resolu.get("numero_scrutin")
            if numero is not None:
                cites.add(numero)
    return cites


def construire(
    cites: Iterable[Any],
    force_download: bool = False,
    dump_path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Les entrées d'index pour les scrutins cités, dans l'ordre des dates."""
    voulus = set(cites)
    if not voulus:
        return []
    chemin = dump_path or ensure_dump(DUMP_VOTES, force_download)
    if chemin is None:
        raise DumpVotesIndisponible(
            f"{DUMP_VOTES} indisponible : un index vide se lirait comme "
            "« aucun scrutin européen » (#510).")

    entrees: list[dict[str, Any]] = []
    for scrutin in iter_dump_zst(Path(chemin)):
        voteid = scrutin.get("voteid")
        if voteid not in voulus:
            continue
        totaux, par_groupe = _repartition(scrutin.get("votes"))
        entrees.append({
            "id": identifiant(voteid),
            "numero_scrutin": voteid,
            "date": (scrutin.get("ts") or "")[:10] or None,
            "texte": scrutin.get("title") or None,
            "reference_dossier": _reference(scrutin),
            "document": scrutin.get("doc") or None,
            "source_url": scrutin.get("url") or None,
            "totaux": totaux,
            "par_groupe": par_groupe,
        })
    # Le tri passe par `str` : la source publie `voteid` tantôt en entier,
    # tantôt en chaîne, et comparer les deux lève. Un ordre stable compte
    # autant que l'ordre lui-même — `audit_diff_profils` verrait bouger un
    # index que rien n'a fait bouger.
    entrees.sort(key=lambda e: (e["date"] or "", str(e["numero_scrutin"])))
    return entrees


def document(entrees: list[dict[str, Any]]) -> dict[str, Any]:
    """L'index complet, entête comprise — même forme que `scrutins.json`."""
    return {
        "schema_version": SCHEMA_VERSION,
        "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "licence_donnees": LICENCE_PARLTRACK,
        "scrutins": entrees,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profils-dir", type=Path, default=DEFAULT_PROFILS_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_SORTIE)
    parser.add_argument("--force-download", action="store_true",
                        help="re-télécharger le dump même si un cache existe")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    cites = numeros_cites(args.profils_dir)
    print(f"→ {len(cites)} scrutin(s) européen(s) cité(s) par les profils publiés")
    entrees = construire(cites, force_download=args.force_download)
    manquants = len(cites) - len(entrees)
    if manquants:
        print(f"  [!] {manquants} cité(s) absent(s) du dump — publiés nulle part "
              "plutôt que fabriqués (§2 règle 5).", file=sys.stderr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(document(entrees), ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")
    poids = args.out.stat().st_size / 1024 / 1024
    print(f"  ✓ {len(entrees)} scrutin(s) écrit(s) dans {args.out} ({poids:.2f} Mo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
