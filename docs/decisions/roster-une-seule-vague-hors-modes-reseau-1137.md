<a id="roster-une-seule-vague-hors-modes-reseau-1137"></a>
# La matrice roster tourne en une seule vague hors des modes qui téléchargent (#1137) (2026-09-25)

`2026-09-25`

> **En bref** — #467 a écrit noir sur blanc pourquoi `extract-roster-groupes` était à 4 et non à 8 : « en `cold_start=true` les steps de cache sont sautés et chaque shard retélécharge ~40 Mo d'archives AN » — un argument **exact**, qui ne parle que de ce mode-là et qui était pourtant appliqué à **tous** les runs ; hors des modes où un shard va chercher quelque chose chez l'AN, les 8 shards restaurent la même entrée immuable de 21 Mo chez GitHub et ne lui demandent rien, donc `max-parallel: 8` — **1 306 s de temps mur mesurées en deux vagues (run `36153601970`) contre ~690 s en une seule, soit ~10 min de chemin critique**, projection assise sur des durées mesurées.

## 1. La mesure

Run `36153601970`, 25/09/2026, mode par défaut :

| Grandeur | Valeur |
| --- | --- |
| Shards | 8 (`ROSTER_SHARDS`), 558 à 676 s chacun |
| Travail cumulé | 4 875 s |
| **Temps mur du groupe** | **1 306 s** (21 min 46), en deux vagues de 4 |
| Le plus long shard | 676 s |
| Pic de jobs simultanés du run entier | 9 |

À `max-parallel: 8`, une seule vague : le temps mur tombe au plus long shard,
~690 s en comptant le décalage de démarrage. **~10 minutes de chemin critique.**

Au passage, une mesure de #467 a vieilli : elle donnait « un shard roster
≈ 200 s ». Ils sont aujourd'hui à 558-676 s. Le roster a grossi ; la projection
de #467 (« ~23 min → ~6 min ») ne tient plus, la structure du raisonnement si.

## 2. Le défaut, et c'est le même qu'au §3 de [[max-parallel-sur-cle-chaude-1137]]

[[budget-execution-pleine-echelle-467]] §5 dit pourquoi 4 :

> *Pourquoi 4 et non 8 : en `fresh_run=true` les steps de cache sont sautés et
> chaque shard retélécharge ~40 Mo d'archives AN (acteurs historiques 13,6 Mo +
> scrutins XVII 26,3 Mo). 4 borne cette rafale à la moitié pour ~3 min de temps
> mur en plus à pleine échelle. Ce dépôt a déjà documenté trois modes de
> défaillance de l'AN (#443) ; on ne va pas les provoquer pour trois minutes.*

L'argument est juste, et il **nomme son mode**. Il était appliqué aux autres.

C'est la même forme de défaut que celui corrigé le même jour sur `extract-an` :
une borne posée pour un cas réel, puis lue comme une constante. La différence
est que celle-ci se lève sans rien sonder — les modes concernés sont des
**inputs du run**, connus avant qu'il démarre.

## 3. Décision

```yaml
max-parallel: ${{ (inputs.cold_start || inputs.collect_dossiers_legislatifs) && 4 || 8 }}
```

**Les deux modes qui gardent 4**, parce qu'un shard y va chercher chez l'AN :

| Mode | Ce qu'un shard télécharge |
| --- | --- |
| `cold_start` | Les steps de cache sont sautés : ~40 Mo d'archives AN par shard. L'argument de #467, à la lettre |
| `collect_dossiers_legislatifs` | Le roster couvre ~750 membres là où `extract-an` en couvre 13 : la part de dossiers qu'il télécharge en plus n'est **jamais persistée**, le job restant en restauration seule (délibéré, #505). Ce qu'un shard demande en plus, il le redemande à chaque run |

Le second n'était pas dans #467 — la case n'existait pas encore, elle est
arrivée avec #817. Il entre ici pour la raison de #467, pas pour une nouvelle.

**Hors de ces deux modes**, le profil réseau d'un shard est celui que #467 a
mesuré : 2 requêtes pour construire le roster, 1 vers
`data.europarl.europa.eu`, **0 par candidat**. Huit shards, c'est huit fois
trois requêtes, une fois par run.

**8 et pas plus** : `prepare-roster-matrix` construit exactement 8 tranches.
Au-delà, `max-parallel` ne fait rien — un test tient les deux valeurs ensemble.

## 4. Ce qui ne bouge pas

Le pic de jobs simultanés. La vague roster est la dernière avant
`merge-and-pivot` : les neuf jobs de tête sont terminés depuis longtemps quand
elle démarre. Le run mesuré plafonnait déjà à 9.

Le cache, à tous les étages : le job reste en **restauration seule** sur les
caches AN, dossiers et amendements, et `extract-an` reste le seul écrivain de la
clé AN. Rien de #424, #505 ou #550 n'est touché.

## 5. L'alternative rejetée

**Ouvrir à 8 sans condition**, en acceptant la rafale des modes réseau. C'est
une ligne de moins, et c'est précisément ce que #467 a refusé avec une mesure à
l'appui : ~40 Mo par shard en `cold_start`, sur une source dont ce dépôt
documente trois modes de défaillance (#443). Un argument mesuré ne se retire pas
parce qu'il gêne un gain projeté ; il se **borne à ce qu'il décrit**.

## 6. Ce qui reste projeté

`max-parallel` ne se teste pas en local — même réserve qu'au §5 de #467 et qu'au
lot principal. Les durées de shard sont mesurées, la recomposition en une vague
ne l'est pas : une vague coûte son shard le plus lent, et la dispersion
observée (558-676 s) est faible, donc l'estimation est serrée. Le premier run
qui le porte tranchera.
