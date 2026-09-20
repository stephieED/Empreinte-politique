# Un run de test : même workflow, périmètre réduit, jamais de commit (#792)

`2026-09-09`

> **En bref** — deux runs consécutifs ont coûté **1 h 13** et **1 h 15** pour révéler un défaut d'une ligne (#786, puis #788 : **71 minutes** pour apprendre qu'un argument manquait), la boucle « modifier → vérifier » n'ayant aucun cran entre le test unitaire (une demi-seconde) et le run complet ; un champ **en tête** du formulaire — un mode se lit avant les réglages qu'il modifie — réduit la matrice `extract-an` aux slugs saisis, plafonne le roster à **8 membres sur 1 shard** quand aucun plafond n'a été demandé, et **désarme le commit** ; **un champ pour trois effets, délibérément** : deux cases indépendantes autoriseraient « périmètre réduit ET commit », c'est-à-dire publier un corpus connu comme partiel, et c'est le seul des trois qui ne se rattrape pas ; **ce mode ne change ni le workflow, ni le code, ni l'ordre des jobs** — il réduit la matrice et rien d'autre, les quatre garde-fous d'avant-commit tournant normalement puisque c'est eux qu'un run de test vient exercer, et un mode qui divergerait du mode réel ne prouverait rien de ce qu'on lui demande (reproche qui ne se répare pas : on ne sait pas après coup ce qu'il n'a pas exercé) ; **il ne remplace pas les tests** — #788 devait être attrapé en une demi-seconde, ce mode existe pour ce qu'aucun test ne voit, l'orchestration ; un slug mal tapé ou gelé (#760) reçoit son `TEST_SLUG_INTROUVABLE` et un périmètre vide échoue **au job de matrice** (`TEST_PERIMETRE_VIDE`) plutôt qu'après une heure — sans quoi « tu as mal tapé » se lirait « rien à collecter » (#510, #771) ; le plafond roster réutilise la mécanique de #467 (`roster_limit > 0` force un shard, la limite valant par shard) et s'**annonce** à chaque run, un plafond implicite invisible étant un plafond qu'on oublie avoir ; **alternative écartée** : le mode « aval seul », même durée et **aveugle à #786** — sans job d'extraction, aucun artifact à transporter, donc aucun transport à éprouver. 16 tests neufs, suite complète à 4 184, 0 échec.

## Contexte

Deux runs consécutifs ont coûté une heure et quart chacun pour révéler un défaut
d'une ligne :

| Run | Durée | Ce qu'il a révélé |
| --- | ---: | --- |
| `34241352524` | 1 h 13 | quatre 403 avalés par `continue-on-error` (#786) |
| `34264027824` | 1 h 15 | un nom non transmis à `_normaliser_en_pivot` (#788) |

Le second est le plus parlant : **71 minutes** pour apprendre qu'un argument
manquait. La boucle « modifier → vérifier » de ce dépôt n'a pas de cran
intermédiaire entre un test unitaire (une demi-seconde, hors ligne) et un run
complet.

## Décision

Un champ, **en tête** du formulaire — un mode se lit avant les réglages qu'il
modifie :

```
┌─────────────────────────────────────────────────────────────────┐
│Test run — these slugs only (empty = full run, never commits)    │
│[  ]                                                             │
└─────────────────────────────────────────────────────────────────┘
```

Le remplir fait trois choses, et le log les annonce toutes les trois :

1. la matrice `extract-an` se réduit à ces slugs ;
2. le roster est plafonné à **8 membres sur 1 shard** si aucun plafond n'a été
   demandé — un `roster_limit` explicite l'emporte ;
3. **le commit est désarmé.**

Vide : run ordinaire, comportement strictement inchangé.

## Un champ, trois effets — et pourquoi pas trois champs

Deux cases indépendantes autoriseraient la combinaison « périmètre réduit **et**
commit », c'est-à-dire publier un corpus dont on sait qu'il est partiel. Le champ
porte les trois effets ensemble, ou aucun. C'est le seul des trois qui ne se
rattrape pas après coup : une donnée publiée l'est.

## Ce que ce mode ne change pas, et c'est le point

**Ni le workflow, ni le code, ni l'ordre des jobs.** Il réduit la matrice, et
rien d'autre. Les quatre garde-fous d'avant-commit tournent normalement — c'est
précisément ce qu'un run de test vient exercer.

Un mode de test qui divergerait du mode réel ne prouverait rien de ce qu'on lui
demande de prouver, et ce reproche-là ne se répare pas : on ne peut pas savoir
après coup ce que le mode n'a pas exercé.

## Ce qu'il ne remplace pas

#788 devait être attrapé par un **test unitaire**, pas par un run même court :
une demi-seconde contre vingt minutes. Ce mode existe pour ce qu'aucun test ne
peut voir — l'orchestration : le transport des artifacts (#786), l'ordre des
passes, les conditions de jobs, le comportement d'un `continue-on-error`.

## Un slug introuvable est nommé

Mal orthographié, sans slug résolvable, ou gelé par #760 : les trois se
ressemblent sur une intersection, et aucun ne doit disparaître en silence. Chaque
slug demandé hors périmètre reçoit son `::warning::TEST_SLUG_INTROUVABLE`, et un
périmètre entièrement vide fait échouer le job de matrice
(`TEST_PERIMETRE_VIDE`) au lieu de laisser tourner une heure pour rien. Sans ça,
un run qui collecte zéro parce qu'on a écrit `marine-lepen` se lirait comme un
run qui n'a rien trouvé — le patron de #510, et celui de #771 pour l'endroit où
l'échec tombe.

## Le plafond du roster est automatique, et il est annoncé

Sans lui, un run « de test » collecterait quand même les 625 membres du roster :
10 minutes de mur pour vérifier une orchestration qui n'en a pas besoin. La
mécanique existait déjà — `roster_limit > 0` force **un seul shard** et la limite
vaut par shard (#467) —, ce lot ne fait que lui donner une valeur par défaut en
mode test. Le `::notice::` le dit à chaque run, parce qu'un plafond implicite qui
ne se voit pas dans le log est un plafond qu'on oublie avoir.

## Alternative écartée

**Un mode « aval seul »** — sauter les six jobs d'extraction et rejouer fusion,
pivots, agrégats et garde-fous sur le corpus committé. Environ le même temps
(~20 min), et il n'aurait **pas vu #786** : sans job d'extraction, il n'y a pas
d'artifact à transporter, donc pas de transport à éprouver. Le mode qui exécute
le vrai workflow est le seul qui couvre ce que les tests ne couvrent pas.
