<a id="amendements-index-job-dedie-ci"></a>
# Job CI dédié `extract-amendements-an` : construction inconditionnelle des 3 index de législature (#251) (2026-08-13)

`2026-08-13`

> **En bref** — un job CI dédié construit inconditionnellement les 3 index de législature.

**Contexte** : sous-issue 3/6 du plan d'architecture #248, bloquée par #250
([[amendements-index-cache-only-split]], qui isole
`_download_and_build_amendement_index` comme point d'entrée réseau
appelable indépendamment de tout candidat). Objectif : un job CI qui
construit les 3 index de législature de `AN_AMENDEMENTS_PATH` sans
condition, pour pré-chauffer le cache partagé `.cache/amendements_an/` une
seule fois par run, au lieu de la construction paresseuse actuelle
(déclenchée seulement quand un candidat traité par `extract-an`/
`extract-roster-groupes` en a besoin).

**Décision** :
1. Nouveau point d'entrée `src/build_amendements_index.py`
   (`build_all_amendements_index()` + `main()`) : boucle sur
   `AN_AMENDEMENTS_PATH` (17/16/15), appelle
   `_download_and_build_amendement_index` pour chacune dans un `try/except
   AmendementsIndexError` isolé — un échec sur une législature n'interrompt
   pas la boucle ni ne lève d'exception non gérée, même pattern d'isolation
   que `fetch_amendements_officiels` (#241/#242). Le code de sortie du
   script (1 si au moins une législature a échoué) reste diagnosticable dans
   les logs du step CI ; c'est `continue-on-error: true` sur le job, pas ce
   script, qui empêche qu'un échec bloque le reste du pipeline.
2. Nouveau job `extract-amendements-an` dans `generate-data.yml` : mêmes
   `checkout`/`setup-python`/`pip install` que les autres jobs
   d'extraction, restauration de cache sur la clé hebdomadaire partagée
   `public-data-cache-an-<semaine ISO>` (pas de clé dédiée — déjà tranché
   par #249, voir
   [[amendements-index-budget-ci-cache-granularite]]), exécution du script,
   upload artifact `amendements-index-an` (`path: .cache/amendements_an/`).
   `continue-on-error: true` et `timeout-minutes: 30`, mêmes valeurs que
   `extract-parltrack`/déjà tranchées par #249.
3. **Pas de `needs:`** (exigence explicite de l'issue #251) : ce job tourne
   en parallèle des 4 jobs d'extraction existants et d'
   `extract-roster-groupes`, plutôt que d'être séquencé après eux comme
   `extract-roster-groupes` l'a été pour la clé de cache AN partagée
   (#222, [[concurrence-ci-roster]]). Accepté explicitement : tant que les
   jobs consommateurs (`extract-an`/`extract-roster-groupes`) continuent de
   déclencher leur propre téléchargement paresseux (bascule vers une
   lecture cache-only hors périmètre ici, sous-issue 4 de #248), une course
   sur la clé de cache partagée reste possible si un candidat sollicite une
   législature avant que ce nouveau job ait sauvegardé son cache — pas une
   régression fonctionnelle (le pire cas est un téléchargement dupliqué
   ponctuel, déjà toléré aujourd'hui en l'absence de ce job), seulement un
   gain de pré-chauffage partiel tant que la sous-issue 4 n'est pas faite.

**Tests** : `tests/test_build_amendements_index.py` — appel des 3
législatures dans l'ordre déclaré, isolation d'un échec partiel (une légis
en échec n'empêche pas les autres, pas d'exception non gérée), code de
sortie de `main()` reflétant un échec partiel ou total. Pas de test
automatisé pour le YAML CI (pattern déjà établi dans ce dépôt, cf. les jobs
existants) — validation par `workflow_dispatch` manuel réservée à
@stephieED (vérifier l'artifact `amendements-index-an` et la sauvegarde de
cache sur un run réel).

*Alternative rejetée* : séquencer ce job après les 4 jobs d'extraction
existants (`needs:`), comme `extract-roster-groupes` (#222) — éliminerait la
course décrite au point 3, mais rejeté ici car explicitement hors périmètre
de l'issue #251 (« Le job n'a pas de `needs:` sur les autres jobs
d'extraction — il tourne en parallèle », critère d'acceptation explicite) ;
à réévaluer si la course s'avère coûteuse en pratique une fois la
sous-issue 4 en place.

