<a id="corroboration-chambres-publiees-486"></a>
# La corroboration porte sur les chambres publiées, pas sur la complétude des mandats — et la condition de retrait de `chambre` devient atteignable (#486) (2026-08-30)

`2026-08-30`

> **En bref** — 30 des 31 occurrences publiées du warning énonçaient un problème que leur propre phrase déniait ; le prédicat cesse de gager le retrait d'un champ de niveau profil sur une complétude de niveau mandat que la fusion additive ne peut pas atteindre (29 des 511 mandats électifs publiés ne sont plus rendus par la source), et la condition de retrait de `chambre` se réduit aux 20 profils que seule une collecte sénatoriale débloque.

Épic **#486**, après #487 (A), #488 (B), #492 (C), #493 (D) et #494 (E), toutes
fermées. Ne touche pas à l'UI (#495, F, ouverte), ne relance aucune collecte, ne
lit ni ne modifie aucun fichier de `pivot_data/` ni de `raw_data/` dans le
pipeline, ne retire pas `chambre`.

## La question posée : la condition de retrait est-elle atteignable ?

[[chambres-profil-derivees]] écrit la condition de retrait de `chambre` en deux
clauses. La seconde est : *« le warning `chambres du profil non corroborée` est
absent de tout le corpus, c'est-à-dire que chaque chambre publiée est étayée par
un `mandat_electif` estampillé »*.

Le texte du warning de #492, lui, affirme qu'un mandat conservé par la fusion
additive et collecté avant l'estampillage **n'est pas reconstituable a
posteriori**. Si c'est vrai et si la condition dépend de ces mandats, alors la
condition est inatteignable sous fusion additive, et seul un run `--no-merge` —
à perte déclarée — la rendrait atteignable.

**Les deux moitiés sont vraies, et la conclusion est fausse.** Mesuré ici, sur
les **481 profils pivot publiés** du 30/08/2026.

## Ce que le warning déclare aujourd'hui : 30 occurrences sur 31 se contredisent

| Ce que dit l'occurrence publiée | Profils, sur les 481 publiés |
| --- | ---: |
| « chambres=['AN'], dont **aucune** sans mandat électif estampillé pour l'étayer, et 1 mandat(s) électif(s) encore sans chambre » | **27** |
| « chambres=**[]**, dont aucune […], et **0** mandat(s) électif(s) encore sans chambre » | **3** (`david-lisnard`, `marine-tondelier`, `nathalie-arthaud`) |
| « chambres=['AN', 'Senat'], dont **['AN']** sans mandat électif estampillé pour l'étayer » | **1** (`bruno-retailleau`) |

Les 27 premières publient une liste **intégralement étayée** sous un titre qui
dit le contraire. Les 3 suivantes ne publient aucune chambre, donc aucune chambre
non étayée : l'avertissement ne nomme aucun problème. **Une seule des 31
occurrences décrit un fait** — et c'est le défaut fondateur de l'épic :
`bruno-retailleau` publie `AN` parce que le jeu de données AN a répondu, quand
son unique `mandat_electif` est estampillé `Senat` et toujours ouvert.

La cause est dans le prédicat, pas dans la formulation. `deriver_chambres`
calculait `corroboree = bool(chambres) and not non_corroborees and not
n_non_estampilles` : trois faits distincts réduits à un booléen, dont deux ne
disent rien de l'étai de la liste publiée.

## Pourquoi ce n'est pas une question de rédaction : la clause de trop est inatteignable

Les **29 `mandat_electif` sans chambre**, sur les 511 publiés par les 481
profils, ne sont pas un reliquat qui s'épuise. Mesuré, mandat par mandat :

| Ce qu'est un `mandat_electif` resté à `chambre: null` | Mandats, sur les 511 publiés |
| --- | ---: |
| doublon d'un mandat que le **même profil** publie déjà, estampillé, sur la même période — la source a déplacé la clé de fusion (`label`, `debut`) | **14** |
| mandat d'une **législature révolue** qu'aucun mandat estampillé ne recouvre — la source ne le rend plus | **15** |

Les deux cas ont la même conséquence et c'est elle qui tranche la question :
**la source ne rend plus ces mandats**. `merge_profile.backfill_mandat_chambre`
ne peut estampiller une entrée ancienne que si le run neuf en produit une de même
clé ; ces 29-là n'en ont aucune. Le cas de `caroline-abadie` le montre en deux
lignes — son profil publie deux fois le même mandat, `2022-06-22 → 2024-06-09`
sans chambre et `2022-06-19 → 2024-06-09` estampillé `AN` : la source a changé la
date de début, la clé a bougé, la fusion additive a gardé les deux.

Sous fusion additive, ces 29 mandats resteront donc à `null` indéfiniment. Une
condition de retrait qui en dépend est inatteignable — et elle porterait de toute
façon sur la mauvaise chose : **`chambre` est un champ de niveau profil, et cette
clause le gageait sur une complétude de niveau mandat.**

## `--no-merge` n'est ni nécessaire ni suffisant

| Effet d'un run `--no-merge` sur les 481 profils publiés | |
| --- | --- |
| supprime les 14 doublons | gain réel, mais un doublon se déduplique, il ne se supprime pas en bloc |
| supprime **15 mandats électifs réels** qui n'existent plus que dans le corpus (dont `gabriel-attal` 2017-2018, `laurent-wauquiez` 2012-2017, `yael-braun-pivet` 2022-2024) | perte nette, contraire à « ajouter, jamais supprimer » |
| ne change **rien** aux 20 profils dont la chambre publiée ne repose que sur le jeu de données qui a répondu | la condition reste hors d'atteinte |

Le repli de collecte est **toujours ajouté** à `chambres` (#493, deux simulations
l'ont imposé), et il survit à la fusion par `_prefer_non_empty` (#494 l'appelle
« la collance »). Un run qui écrase ne le retire pas. **`--no-merge` paie une
perte de 15 mandats pour ne pas atteindre la condition.** Il est donc écarté.

## La décision : `corroboree` ne dit plus qu'une chose

`ChambresDerivees.corroboree` vaut désormais « **chaque chambre publiée dans
`chambres` est étayée par un `mandat_electif` estampillé** », et rien d'autre —
exactement la glose que [[chambres-profil-derivees]] donnait déjà de sa condition
de retrait. Une liste vide est vraie par vacuité : elle ne publie aucune chambre.
Le compte des mandats non estampillés reste dans le NamedTuple, mais ne
conditionne plus le prédicat.

**Rien ne devient muet** (§2.5). Le fait retiré du warning de #493 est déclaré par
celui de #492, `chambre de mandat électif non résolue`, qui existe pour ça, le
nomme et le compte. Ce qui change, c'est qu'il en devient le **seul** porteur —
et c'est ce qui a rendu nécessaire la seconde moitié du lot.

## Le warning de #492 devait d'abord survivre à la fusion

`normalize_profil` le calcule sur les mandats du profil **neuf** ; la fusion
additive en publie un surensemble. Il manquait donc les deux directions que #493
s'était données, et le trou est mesuré : sur les 481 profils publiés, **1**
(`yannick-vaugrenard`) publie un `mandat_electif` à `chambre: null` **sans aucun
avertissement pour le dire** — son pivot est antérieur à #492, la fusion a
conservé le mandat et n'a jamais reconstruit le message. Les 27 autres portaient
un compte juste par coïncidence de périmètre, pas par construction.

`merge_pivot_profile` recalcule donc le message sur les mandats **fusionnés**, et
il s'ajoute quand il est devenu vrai, s'éteint quand il est devenu faux, et
remplace un compte devenu faux — un compte faux fait croire la migration plus
avancée qu'elle n'est. Son préfixe entre par la même occasion dans
`FAMILLES_WARNINGS` : c'est un message **à compteur**, et #600 a posé la règle
que deux comptes contradictoires ne se publient jamais côte à côte. La famille
manquait depuis #600.

## Ce que ça change sur le corpus, mesuré à vide

Simulation **en lecture seule** rejouant `deriver_chambres` sur les mandats
publiés des 481 profils — aucune écriture, aucune collecte, aucun profil
régénéré.

| Mesure, sur les 481 profils pivot publiés | Publié au 30/08 | Projeté, ancienne règle | Projeté, nouvelle règle |
| --- | ---: | ---: | ---: |
| `chambres du profil non corroborée` | 31 | **50** | **20** |
| `chambre de mandat électif non résolue` | 27 | 28 | **28** |
| divergences `chambre != chambres[0]` | — | 0 | **0** |

« Publié » est le corpus tel qu'il est ; « projeté » est ce que la dérivation
donnerait après une régénération complète — 19 profils ne portent pas encore la
clé `chambres`, et c'est pourquoi le projeté d'avant (50) dépasse le publié (31).
La ligne de #492 monte de 27 à 28 : c'est `yannick-vaugrenard`, le trou ci-dessus,
qui cesse d'être muet.

Aucun dénominateur publié ne bouge : `corroboree` n'est lu que pour décider d'un
warning, et `check_quality_gate.population_an` comme
`audit_pivot_dataset.MAPPING_CHAMBRE_SOURCES` lisent `lire_chambres()`, que ce
lot ne touche pas.

## La condition de retrait, réécrite — et ce qu'elle vaut

> **`chambre` est retiré du schéma quand les deux conditions sont vraies :**
>
> 1. **les consommateurs ont migré** — inchangée. Le pipeline a migré (#494) ;
>    il reste `pivotAdapter.chambreLabel` dans l'UI (#495).
> 2. **aucune chambre publiée ne repose sur sa seule chambre de collecte** — le
>    warning `chambres du profil non corroborée` est absent de tout le corpus.
>    Elle ne dépend plus de la complétude de `mandats[]`, qui est déclarée par le
>    warning de #492 et suivie séparément.

Elle est désormais **atteignable, et par une seule voie**. Les 20 profils
projetés qui la retiennent sont exactement ceux dont aucun `mandat_electif`
n'étaye la chambre publiée :

| Les 20 profils qui retiennent la condition 2 | Ce qui les débloque |
| --- | --- |
| 18 sénateurs sans aucun `mandat_electif`, publiés `AN` parce que `nosdeputes.fr` a répondu pour eux (`gerard-larcher` compris) — déjà nommés par #493 et #494 | une collecte sénatoriale : jalon *Pipeline sénat* (#596, #591) |
| `yannick-vaugrenard`, dont le seul mandat électif collecté est européen | idem |
| `bruno-retailleau`, sénateur en exercice publié `chambre: "AN"` | idem. Le jeu de données AN a répondu pour lui — son profil brut porte `chambre: "deputes"` — **sans rendre aucun `mandat_electif`** : son unique mandat électif publié vient du côté Sénat, estampillé `Senat` et toujours ouvert. Rien ne peut donc étayer son `AN` tant que sa carrière de député n'est pas collectée |

**Ce n'est donc pas le schéma qui retient le retrait de `chambre`, c'est la
collecte.** La direction éditoriale du 30/08 — *une carrière bicamérale se
collecte des deux côtés, on ne choisit pas une chambre* — est exactement ce qui
lève la condition 2, et #528 §7 en tient les trois conditions de réouverture.

## Ce que ce lot ne fait pas

- **`bruno-retailleau` publie toujours `chambre: "AN"`.** `chambre` vaut
  `chambres[0]` et `ORDRE_CHAMBRES` place `AN` avant `Senat` : le scalaire
  transitoire continue d'affirmer une chambre qu'aucun mandat n'étaye, ce qui est
  une affirmation factuelle fausse pour un sénateur en exercice (§2 règle 1).
  Le warning le déclare, il ne le corrige pas. Trancher la tête du scalaire —
  ou retirer `chambre` avant que la condition 2 ne soit remplie — est un
  arbitrage éditorial, pas une conséquence de cette mesure.
- **Les 14 doublons de `mandat_electif` restent publiés**, sur 14 des 481
  profils. Dédupliquer est une suppression, que le pipeline ne fait pas sans
  décision explicite ; les compter est ce que ce lot apporte.
- **Aucun profil n'est régénéré**, aucune collecte n'est relancée, `chambre`
  n'est pas retiré.
