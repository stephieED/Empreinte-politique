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
import os
import sys
import time
from pathlib import Path

from amendements_contenu import chemin_cache, chemin_publie, ecrire_contenu_cache
from candidate_profile import (
    AMENDEMENTS_CACHE_DIR,
    AN_AMENDEMENTS_LEGISLATURES_FIGEES,
    AN_AMENDEMENTS_PATH,
    AmendementsIndexError,
    _amendements_zip_url,
    _download_amendements_zip,
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
        if (en_cache is not None and legislature not in AN_AMENDEMENTS_LEGISLATURES_FIGEES
                and not chemin_cache(legislature, AMENDEMENTS_CACHE_DIR).is_file()):
            # #1029 — un index en cache sans son contenu (écrit avant #1029) se
            # reconstruit : c'est la même archive qui donne les deux.
            print(f"-> Législature {legislature} : index en cache SANS contenu (#1029), "
                  "reconstruction")
            purger_cache_amendements_legislature(legislature)
            en_cache = None
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


#: Où l'index publié se lit pendant le run : le dépôt est extrait avant ce job.
DOSSIER_PUBLIE = Path("pivot_data") / "amendements"


#: Plafond du job `extract-amendements-an` dans `.github/workflows/generate-data.yml`.
#: Recopié ici parce que le YAML est lu sur le dépôt PUBLIC et se publie à la
#: main : une valeur lue à l'exécution serait celle d'un autre dépôt. La copie
#: est tenue par `tests/test_budget_archive_figee_1100.py`, qui la compare au
#: `timeout-minutes` du YAML.
JOB_TIMEOUT_MINUTES = 30

#: Ce qu'on garde pour la suite du job après le téléchargement : construire le
#: contenu de la XVe demande ~150 s et 2,7 Go depuis un poste (mesuré le
#: 22/09/2026), et l'artifact reste à téléverser.
MARGE_APRES_TELECHARGEMENT_SECONDES = 420


def budget_telechargement_secondes(maintenant: float | None = None) -> float | None:
    """Le temps qu'il reste au job pour télécharger une archive figée (#1100).

    `JOB_START_EPOCH` est posé par `.github/actions/bootstrap-extraction` au
    début du job. Hors CI, il est absent : le budget est alors `None`, et le
    téléchargeur retombe sur son compte de cycles — hors CI, attendre longtemps
    est précisément le seul remède qui marche, et personne ne tue le processus.

    Rend `None` s'il n'y a rien à borner, `0` s'il ne reste plus rien : dans ce
    cas le téléchargement n'est même pas tenté.
    """
    depart = os.environ.get("JOB_START_EPOCH")
    if not depart:
        return None
    try:
        debut = float(depart)
    except ValueError:
        return None
    fin = debut + JOB_TIMEOUT_MINUTES * 60 - MARGE_APRES_TELECHARGEMENT_SECONDES
    return max(0.0, fin - (time.time() if maintenant is None else maintenant))


def construire_un_contenu_fige(dossier_publie: Path = DOSSIER_PUBLIE) -> bool:
    """Construit le contenu d'UNE législature figée qui n'en a pas encore (#1029).

    Une législature close ne change plus : son contenu se construit une fois,
    puis se lit dans le fichier publié. **Une seule par run** — les trois
    archives pèsent 1,1 Go (XIVe 104 Mo, XVe 649 Mo, XVIe 363 Mo, mesuré le
    22/09/2026) et la XVe demande 2,7 Go de mémoire et 150 s depuis un poste :
    toutes à la fois menaceraient le plafond de 30 minutes du job. Les trois
    sont faites en trois runs, une seule fois.

    Retourne False sur un échec, sans lever : le job ne doit rien perdre d'autre.
    """
    for legislature in sorted(AN_AMENDEMENTS_LEGISLATURES_FIGEES):
        if chemin_publie(legislature, dossier_publie).is_file():
            continue
        if chemin_cache(legislature, AMENDEMENTS_CACHE_DIR).is_file():
            continue
        url = _amendements_zip_url(legislature)
        if not url:
            continue
        zip_path = AMENDEMENTS_CACHE_DIR / legislature / "amendements.zip"
        budget = budget_telechargement_secondes()
        if budget is not None and budget <= 0:
            print(f"  [!] Contenu de la législature {legislature} non tenté : plus de budget "
                  f"dans le job ({JOB_TIMEOUT_MINUTES} min) — reprise au run suivant.",
                  file=sys.stderr)
            return True
        borne = "sans borne de temps" if budget is None else f"budget {budget:.0f}s"
        print(f"-> Contenu des amendements (#1029), législature figée {legislature} "
              f"({borne}) : {url}")
        try:
            _download_amendements_zip(url, zip_path, legislature, budget_secondes=budget)
            ecrire_contenu_cache(legislature, zip_path, AMENDEMENTS_CACHE_DIR)
        except Exception as exc:  # noqa: BLE001 — non bloquant, nommé
            print(f"  [!] Contenu de la législature {legislature} non construit : {exc}",
                  file=sys.stderr)
            return False
        finally:
            zip_path.unlink(missing_ok=True)
        return True
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    parser.add_argument(
        "--reconstruire-actives", action="store_true",
        help="purge le cache des législatures non figées avant de construire (#749)",
    )
    args = parser.parse_args(argv)
    if args.reconstruire_actives:
        purger_legislatures_actives()
    ok = build_all_amendements_index()
    ok = construire_un_contenu_fige() and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
