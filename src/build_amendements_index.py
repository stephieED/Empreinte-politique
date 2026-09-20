#!/usr/bin/env python3
"""
build_amendements_index.py

Point d'entrée dédié au job CI `extract-amendements-an` (issue #251,
sous-issue 3/6 du plan d'architecture #248) : construit sans condition les
index amendements des 3 législatures de `AN_AMENDEMENTS_PATH`
(candidate_profile.py), indépendamment de toute liste de candidats — à la
différence de `extract-an`/`extract-roster-groupes`, qui ne déclenchent
cette construction que paresseusement, au niveau candidat.

Appelle `_download_and_build_amendement_index` (#250) pour chaque
législature, dans une boucle isolée par try/except — un échec définitif sur
une législature (ex. archive AN indisponible) n'empêche pas la construction
des autres, même pattern d'isolation que `fetch_amendements_officiels`
(#241/#242). Le job CI qui invoque ce script est `continue-on-error: true` ;
ce script reflète malgré tout un échec partiel via son code de sortie (1 si
au moins une législature a échoué), pour rester diagnosticable manuellement
via les logs du step — le `continue-on-error` du job est ce qui évite que
cela bloque le reste du pipeline, pas ce script.

Une législature figée déjà matérialisée (`amendements_index_deja_figee`) est
sautée sans être rechargée : elle ne change plus jamais une fois matérialisée,
et la recharger en mémoire juste pour le confirmer (jusqu'à plusieurs Go en
clair pour une grosse législature) a déclenché l'OOM killer du système en
pratique, empêchant toute législature suivante de la boucle d'être ne
serait-ce que tentée.

`--reconstruire-actives` (#749) purge d'abord le cache des législatures NON
figées, pour forcer leur reconstruction. La CI le passe quand la clé de cache
exacte de la semaine ISO n'a pas été touchée : `restore-keys` ayant restauré la
semaine précédente, le cache n'est jamais absent, donc le court-circuit de
`_download_and_build_amendement_index` ne reconstruisait plus JAMAIS — 18 jours
sans une seule reconstruction de la 17e, alors que la rotation hebdomadaire de
clé (#249) était toute la politique de fraîcheur. Seules les législatures
actives sont visées : une figée n'a rien à rafraîchir, et la re-matérialiser
chaque semaine coûterait la mémoire de [[oom-reconstruction-amendements-figees]].

Usage (depuis la racine du dépôt) :
    python3 src/build_amendements_index.py
    python3 src/build_amendements_index.py --reconstruire-actives
"""

import argparse
import sys

from candidate_profile import (
    AN_AMENDEMENTS_LEGISLATURES_FIGEES,
    AN_AMENDEMENTS_PATH,
    AmendementsIndexError,
    _download_and_build_amendement_index,
    amendements_index_deja_figee,
    amendements_index_en_cache_utilisable,
    purger_cache_amendements_legislature,
)


def purger_legislatures_actives() -> None:
    """Purge le cache des législatures non figées, pour forcer leur reconstruction."""
    for legislature in AN_AMENDEMENTS_PATH:
        if legislature in AN_AMENDEMENTS_LEGISLATURES_FIGEES:
            continue
        if purger_cache_amendements_legislature(legislature):
            print(f"-> Législature {legislature} : cache purgé, reconstruction forcée")
        else:
            print(f"-> Législature {legislature} : aucun cache à purger")


def build_all_amendements_index() -> bool:
    """Construit l'index amendements de chaque législature de
    `AN_AMENDEMENTS_PATH` non déjà figée en cache. Retourne True si toutes
    ont réussi (ou étaient déjà figées), False si au moins une a échoué — un
    échec est isolé par législature (try/except) et n'interrompt jamais la
    boucle, ni ne lève d'exception non gérée."""
    ok = True
    for legislature in AN_AMENDEMENTS_PATH:
        if amendements_index_deja_figee(legislature):
            print(f"-> Législature {legislature} : déjà figée en cache, non rechargée")
            continue
        # #749 — le log DIT lequel des deux a eu lieu. Il annonçait une
        # « Construction » puis un compte d'acteurs pour une exécution de
        # 0,28 s qui ne téléchargeait rien, et c'est ce log qui a rendu
        # invisible 18 jours sans une seule reconstruction.
        en_cache = amendements_index_en_cache_utilisable(legislature)
        if en_cache is not None:
            print(f"-> Législature {legislature} : index déjà en cache, non reconstruit "
                  f"({len(en_cache)} acteur(s))")
            continue
        print(f"-> Construction de l'index amendements, législature {legislature}")
        try:
            index = _download_and_build_amendement_index(legislature)
        except AmendementsIndexError as exc:
            print(f"  [!] Échec pour la législature {legislature} : {exc}", file=sys.stderr)
            ok = False
            continue
        print(f"  -> {len(index)} acteur(s) indexé(s) pour la législature {legislature}")
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    parser.add_argument(
        "--reconstruire-actives", action="store_true",
        help="purge le cache des législatures non figées avant de construire (#749)",
    )
    args = parser.parse_args(argv)
    if args.reconstruire_actives:
        purger_legislatures_actives()
    return 0 if build_all_amendements_index() else 1


if __name__ == "__main__":
    sys.exit(main())
