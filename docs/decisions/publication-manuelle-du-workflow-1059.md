<a id="publication-manuelle-du-workflow-1059"></a>
# Ce qu'un run ne publie pas lui-même : le workflow et l'action de superposition (#1059) (2026-09-21)

`2026-09-21`

> **En bref** — un run publie tout le code avec ses données, sauf ce qui le pilote : une modification du workflow ou de l'action de superposition exige toujours une publication manuelle avant le run.

**Contexte** : [[code-du-prive-dans-le-run-1059]] annonçait que la publication
qui armait le mécanisme serait « la dernière à faire à la main ». **C'est
inexact**, et le jour même l'a montré : le correctif #1067 portait sur la ligne
de commit du workflow, et il a fallu le publier à la main (v1.0.4) avant que le
run suivant puisse s'en servir.

**Ce qui ne voyage pas avec le run, et pourquoi.**

| Fichier | D'où GitHub le lit | Conséquence |
| --- | --- | --- |
| `.github/workflows/generate-data.yml` | **du dépôt public**, au déclenchement | une modification ne vaut qu'une fois publiée |
| `.github/actions/code-du-prive/` | **du checkout public**, avant la superposition — c'est elle qui superpose | idem |
| tout le reste — `src/`, `config/`, `web/`, `tests/`, les autres actions | du privé, par la superposition | voyage avec le run |

**Décision : la règle se dit par ce qui pilote le run, pas par une date.** Toute
PR qui touche l'une des deux premières lignes se publie à la main avant le run
qui doit l'utiliser — récupérer les données d'abord, publier ensuite, comme
toujours. Tout le reste se publie seul, avec les données qu'il a produites.

**Alternative écartée : faire superposer aussi le workflow.** Impossible par
construction : GitHub a déjà lu le fichier quand le premier job démarre.
