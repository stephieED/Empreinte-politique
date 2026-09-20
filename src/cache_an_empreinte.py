#!/usr/bin/env python3
"""Empreinte de COMPLÉTUDE du cache AN d'interventions (#550).

Pourquoi ce fichier existe
--------------------------
La clé de cache `public-data-cache-an-<semaine>[-interv]` décrit *quand* et
*dans quel mode* une entrée a été écrite. Elle n'a jamais rien dit de ce que
l'entrée CONTIENT réellement.

Mesuré sur le run `33100214165` (27/08/2026, shard `jean-luc-melenchon`,
job 98616438651) : les archives Syceron des 15e et 16e législatures et les
archives de questions des 14e et 15e sont tombées en `IncompleteRead`. Les
gardes de #505/#510 ont fait leur travail — un index construit sur une archive
absente n'est pas mis en cache — et le shard a malgré tout sauvegardé, à
17:55:27, une entrée de 114 481 867 o sous la clé
`public-data-cache-an-2026-W35-interv`, ne contenant que :

    .cache/syceron_an/17/index_par_acteur/
    .cache/questions_an/16/index_par_acteur.json
    .cache/questions_an/17/index_par_acteur.json

Deux heures plus tard, le run `33110395663` a fait un *exact key hit* sur cette
entrée. `actions/cache` saute alors sa sauvegarde de fin de job (« Cache hit
occurred on the primary key public-data-cache-an-2026-W35-interv, not saving
cache », relevé à 20:02:40 dans le job 98652271090) : les index des 15e et 16e
législatures que chacun des 7 shards porteurs a reconstruits — 113 à 219 s par
shard, 40 à 60 % de l'horloge de collecte — ont été jetés sept fois.

Ce que ce module produit
------------------------
Une chaîne courte, lisible dans l'interface Actions, qui dit QUELLES
législatures d'index sont réellement présentes :

    syc15.16.17-q14.15.16.17     (complet)
    syc17-q16.17                 (l'entrée fautive du 27/08)

Suffixée à la clé, elle empêche une entrée partielle d'entrer en collision avec
une entrée complète : le run suivant ne fait plus d'*exact key hit*, restaure
la meilleure entrée disponible par `restore-keys`, complète ce qui manque et
**sauvegarde**. Les entrées partielles ne disparaissent pas — elles servent de
point de départ — mais elles ne se font plus passer pour complètes.

Le refus de mettre en cache une législature illisible n'est PAS touché : il est
juste, et c'est lui qui garantit qu'une législature comptée ici a été lue en
entier (`_build_acteur_questions_index`, `_build_acteur_interventions_syceron_index`).

Ce que l'empreinte NE couvre pas, et pourquoi
---------------------------------------------
`.cache/acteurs_historique_an` et `.cache/scrutins_an`, également couverts par
la même clé, en sont absents. Leur complétude n'est pas observable sur le
disque de la même façon : les législatures figées (`AN_SCRUTINS_LEGISLATURES_FIGEES`)
sont matérialisées **dans le dépôt**, pas dans `.cache`, si bien qu'une absence
sous `.cache/scrutins_an` n'y est pas un manque. Aucun défaut mesuré ne les
implique à ce jour. Étendre l'empreinte à ces deux répertoires demanderait
d'abord d'établir ce qu'y est un état complet — c'est une autre mesure, pas un
ajout gratuit.

L'empreinte est calculée sur **exactement les fichiers que le `path:` du step
de cache capture** (`.cache/questions_an/*/index_par_acteur.json` et
`.cache/syceron_an/*/index_par_acteur`), et non sur ce que le code croit avoir
écrit : c'est la seule façon qu'elle ne puisse pas mentir sur le contenu de
l'entrée. `tests/test_cache_an_empreinte.py` vérifie que les deux listes
coïncident.

Usage
-----
    python3 src/cache_an_empreinte.py --attendue   # complétude visée
    python3 src/cache_an_empreinte.py --disque     # complétude atteinte
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, Optional

import candidate_profile as _cp

# Nom du fichier d'index des questions officielles, écrit par
# `_build_acteur_questions_index` et capté par le `path:` du step de cache. Le
# répertoire d'index Syceron, lui, a déjà sa constante
# (`candidate_profile.SYCERON_INDEX_PAR_ACTEUR_DIRNAME`).
QUESTIONS_INDEX_FILENAME = "index_par_acteur.json"

# Les deux motifs du `path:` du step de cache, repris à l'identique. Le test
# `test_les_globes_correspondent_au_workflow` les compare au workflow : si
# l'un bouge sans l'autre, l'empreinte décrirait un contenu qui n'est pas celui
# de l'entrée.
GLOBE_QUESTIONS = f".cache/questions_an/*/{QUESTIONS_INDEX_FILENAME}"
GLOBE_SYCERON = ".cache/syceron_an/*/index_par_acteur"

_LEGISLATURE = re.compile(r"^\d+$")


def _tri(legislatures: Iterable[str]) -> list[str]:
    return sorted({str(l) for l in legislatures}, key=int)


def legislatures_syceron_attendues() -> list[str]:
    """Les législatures Syceron qu'une collecte complète indexe.

    Lue sur `SYCERON_AVAILABLE_LEGISLATURES`, jamais recopiée : une liste
    recopiée ici deviendrait fausse le jour où la 18e législature s'ouvre, et
    l'empreinte attendue ne serait plus jamais atteinte — donc plus aucun
    *exact key hit*, donc une sauvegarde par shard.
    """
    return _tri(_cp.SYCERON_AVAILABLE_LEGISLATURES)


def legislatures_questions_attendues() -> list[str]:
    """Idem pour les questions officielles, lues sur `AN_QUESTIONS_PATH`."""
    return _tri(_cp.AN_QUESTIONS_PATH)


def legislatures_syceron_indexees(cache_syceron: Optional[Path] = None) -> list[str]:
    """Législatures dont le répertoire de tranches Syceron est publié ET peuplé.

    Un répertoire vide n'est pas compté. `_write_syceron_index_par_acteur`
    publie d'un seul `os.replace` et ne publie jamais un index vide, mais
    l'empreinte décrit le DISQUE, pas le chemin qui l'a produit : un répertoire
    vide laissé par un runner tué compterait sinon pour un index complet.
    """
    base = Path(cache_syceron) if cache_syceron is not None else _cp.SYCERON_CACHE_DIR
    if not base.is_dir():
        return []
    trouvees = []
    for entree in base.iterdir():
        if not _LEGISLATURE.match(entree.name):
            continue
        index_dir = entree / _cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME
        if index_dir.is_dir() and any(index_dir.glob("*.json")):
            trouvees.append(entree.name)
    return _tri(trouvees)


def legislatures_questions_indexees(cache_questions: Optional[Path] = None) -> list[str]:
    """Législatures dont l'index de questions officielles est en cache."""
    base = Path(cache_questions) if cache_questions is not None else _cp.QUESTIONS_CACHE_DIR
    if not base.is_dir():
        return []
    trouvees = [
        entree.name
        for entree in base.iterdir()
        if _LEGISLATURE.match(entree.name) and (entree / QUESTIONS_INDEX_FILENAME).is_file()
    ]
    return _tri(trouvees)


def empreinte(syceron: Iterable[str], questions: Iterable[str]) -> str:
    """`syc<législatures>-q<législatures>`, triées, jointes par des points.

    Pas un hachage : la clé se lit dans l'interface Actions, et c'est là qu'on
    voit d'un coup d'œil qu'une entrée est partielle et laquelle manque. Le
    format n'utilise que des caractères sûrs pour une clé de cache.
    """
    return f"syc{'.'.join(_tri(syceron))}-q{'.'.join(_tri(questions))}"


def empreinte_attendue() -> str:
    """L'empreinte d'un cache d'interventions COMPLET, dérivée du code."""
    return empreinte(legislatures_syceron_attendues(), legislatures_questions_attendues())


def empreinte_du_disque() -> str:
    """L'empreinte de ce que le disque porte réellement, ici et maintenant."""
    return empreinte(legislatures_syceron_indexees(), legislatures_questions_indexees())


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    groupe = parseur.add_mutually_exclusive_group(required=True)
    groupe.add_argument(
        "--attendue",
        action="store_true",
        help="empreinte d'un cache complet (clé de restauration)",
    )
    groupe.add_argument(
        "--disque",
        action="store_true",
        help="empreinte du cache présent sur le disque (clé de sauvegarde)",
    )
    args = parseur.parse_args(argv)
    print(empreinte_attendue() if args.attendue else empreinte_du_disque())
    return 0


if __name__ == "__main__":  # pragma: no cover - point d'entrée CLI
    raise SystemExit(main())
