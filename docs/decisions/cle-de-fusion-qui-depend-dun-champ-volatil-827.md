# Une clé de déduplication ne doit dépendre d'aucun champ qui apparaît (#827)

`2026-09-11`

> **En bref** — #827 a donné un `source_url` aux explications de vote, et le run `34503639092` les a publiées **deux fois** : `_interv_key` était une cascade **exclusive** qui prenait l'URL avant le contenu, or ces entrées n'ont **pas** d'`intervention_id` — leur clé était le contenu avant, l'URL après, donc la fusion additive a ajouté au lieu de reconnaître. **1 462 doublons** sur 4 profils. **Le correctif évident aurait détruit 88 % du corpus** : indexer chaque entrée sur toutes ses clés, contenu compris, fusionnerait les **902 457** entrées à identifiants différents qui partagent déjà une clé de contenu, les interventions en mode thème-seul n'ayant ni sujet ni texte — la mesure a précédé le code et l'a interdit. `source_url` est donc **retiré de la cascade** : l'identifiant quand il existe, le contenu sinon, ni l'un ni l'autre n'apparaissant après coup ; les **3 073** entrées sans identifiant portent **toutes** un sujet ou un texte, **zéro** exception. La purge (`scripts/purger_doublons_interventions_827.py`) garde l'exemplaire **avec** le lien et ne passe que sur le pivot — #729 exige les deux étages, mais le brut n'a rien, l'enrichissement s'appliquant au profil pivot. Après purge : **1 611** explications, le compte d'origine, **1 462** liées, **0** doublon. **Un chiffre corrigé en route** : le premier constat annonçait 1 962 doublons dont 430 `debat` — faux, la mesure groupait sur le contenu **sans distinguer les entrées à identifiant** et comptait des interventions distinctes du même débat ; **0** entrée à identifiant est publiée deux fois. Un témoin lit le corps de `_interv_key` et refuse le retour de `source_url` : le défaut n'apparaît qu'au run **suivant** celui qui pose le champ. Suite complète à 4 453, 0 échec.

## Ce qui s'est passé

#827 a donné un `source_url` aux explications de vote européennes. Le run
`34503639092` les a alors publiées **deux fois** — l'exemplaire d'avant sans
lien, puis le même avec lien. Même date, même sujet, même texte.

**1 462 doublons**, sur 4 profils : `florian-philippot` 725,
`emmanuel-maurel` 624, `marine-le-pen` 65, `jean-luc-melenchon` 48.

## La cause

`_interv_key` était une cascade **exclusive** :

```python
if i.get("intervention_id"): return ("intervention_id", …)
if i.get("source_url"):      return ("source_url", …)
return ("contenu", date, sujet, texte[:50])
```

Les explications de vote n'ont **pas** d'`intervention_id` — ParlTrack ne leur
donne aucune référence. Leur clé était donc le **contenu** avant #827, et
l'**URL** après. Deux clés pour la même entrée : la fusion additive a ajouté au
lieu de reconnaître.

**Une clé de déduplication ne doit dépendre d'aucun champ qui peut apparaître.**
C'est la règle que ce lot pose, et le défaut qu'il corrige.

## Le correctif évident aurait détruit 88 % du corpus

La réaction naturelle — indexer chaque entrée sur **toutes** ses clés possibles,
contenu compris — est fausse, et la mesure le dit avant le code :

| Mesuré sur les 1 019 036 interventions publiées | |
| --- | ---: |
| Entrées à `intervention_id` **différents** partageant une clé de contenu | **902 457** |

Les interventions collectées en mode thème-seul n'ont ni sujet ni texte : leur
clé de contenu est `(date, None, "")`. Rendre cette clé active pour tout le
monde aurait fusionné **88 %** du corpus d'interventions.

## Ce qui est fait

`source_url` est **retiré de la cascade**. L'ordre devient : l'identifiant quand
il existe, le contenu sinon. Ni l'un ni l'autre n'apparaît après coup.

Ce n'est pas une perte de pouvoir discriminant, et c'est mesuré : les **3 073**
entrées sans `intervention_id` portent **toutes** un sujet ou un texte —
**zéro** exception. La clé de contenu les sépare, et c'est exactement elle qui,
appliquée, rend les 1 462 doublons comme doublons.

## La purge, et pourquoi un seul étage

`scripts/purger_doublons_interventions_827.py`, passé une fois. La fusion
additive ne retire **jamais** ce qui est déjà publié : corriger la clé empêche
la récidive, pas le résidu.

**Lequel des deux garder** : celui qui porte le lien. Les deux sont identiques
par ailleurs ; garder l'autre rejetterait le travail de #827.

#729 exige qu'une correction qui **retire** s'applique à `raw_data/profiles/`
**et** à `pivot_data/profiles/`, sans quoi elle ne se pose nulle part. **Ici le
premier étage n'a rien**, et c'est vérifié : les explications sont posées par
`enrich_pivot_with_parltrack`, appelée sur le profil **pivot**. Le brut de
`marine-le-pen` ne contient ni `doceo`, ni aucun texte d'explication.

Résultat, vérifié après purge :

| | |
| --- | ---: |
| Explications publiées | **1 611** — le compte d'origine |
| …avec un lien | **1 462** (90,8 %) |
| Doublons restants | **0** |

## Un chiffre corrigé en cours de route

Le premier constat annonçait **1 962** doublons, dont 430 sur des `debat`. Il
était faux : la mesure groupait sur `(date, sujet, texte)` **sans distinguer les
entrées à identifiant**, et comptait donc comme doublons des interventions
distinctes du même débat, qui n'ont ni sujet ni texte.

Le compte exact est **1 462**, tous des explications de vote. Vérifié : **0**
entrée portant un `intervention_id` est publiée deux fois sous le même
identifiant.

## Le témoin

`test_la_cle_de_fusion_ne_depend_plus_de_source_url` lit le corps de
`_interv_key` et refuse le retour de `source_url` dans la cascade. Sans lui, un
refactor le remettrait sans que rien ne le voie — le défaut n'apparaît qu'au
run **suivant** celui qui pose le champ, et seulement sur les entrées sans
identifiant.

Suite complète à 4 453, 0 échec.
