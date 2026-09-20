<a id="integrite-referentielle-pivot"></a>
# Rien ne vérifiait que les clés publiées résolvent : le contrôle d'invariance (#485) (2026-08-20)

`2026-08-20`

> **En bref** — une clé publiée qui ne résout pas est un vote sans objet ; seuil 0 avant commit.

**Il n'y avait aucun défaut.** Mesuré sur `01ffa7f` le 20/08/2026, index et
couches référençantes relevés ensemble :

| Vérification | Résultat |
| --- | ---: |
| Références `votes[].scrutin_id` (profils) | 524 353 |
| Références `cohesion_votes[].scrutin_id` (groupes) | 12 546 |
| Références `amendements[].amendement_id` (profils) | 810 552 |
| **Références orphelines**, les trois renvois confondus | **0 / 1 347 451** |
| Entrées de `scrutins.json` jamais référencées | **0 / 17 535** |
| Entrées de `amendements/` jamais référencées | **0 / 207 238** |

Rien à réparer. Ce qui manquait, c'est qu'**aucun outil ne vérifiait cette
propriété**, devenue structurellement fragile.

## Pourquoi elle est fragile depuis #431 et #432

Ces deux issues ont sorti le détail du scrutin et de l'amendement des profils
pour un index partagé ; les profils n'en gardent qu'une **clé**. La donnée est
passée d'un état **auto-suffisant** — chaque profil portait sa copie complète —
à un état **référentiel** : un vote n'a plus de sens que si sa clé résout.
Trois façons de casser ça, dont **aucune ne bouge un compteur** : une clé qui ne
résout pas, une convention de clé changée, un index publié partiellement.

## Pourquoi ce n'est pas une extension du contrôle de perte

[[controle-de-perte-avant-commit]] compare un **avant** et un **après**. Il
verrait une chute du nombre d'entrées d'un index, mais **pas** une rupture de
correspondance entre deux couches du **même** état : un run où les profils et
l'index seraient tous deux régénérés de façon cohérente-mais-fausse lui
paraîtrait irréprochable. C'est une **invariance dans un état donné**, pas une
variation dans le temps — deux contrôles complémentaires, jamais alternatifs.

`tests/test_audit_integrite_referentielle.py::test_le_controle_de_perte_ne_voit_pas_ce_que_celui_ci_voit`
en fait la démonstration plutôt que de l'affirmer : il réécrit les identifiants
de l'index (`an:` → `an-v2:`) des deux côtés, constate que le contrôle de perte
ne relève **rien** — toutes les cardinalités sont identiques — et que celui-ci
relève chaque référence.

## Le diagnostic de #470 était trop pessimiste, et c'est ce qui débloque le sujet

La section « ce qu'il ne couvre pas » écrivait que l'intégrité référentielle
était « hors de portée d'un contrôle à mémoire bornée : il faudrait tenir les
deux ensembles de clés en mémoire simultanément ». **Non** : il n'en faut qu'un,
et c'est le petit. Les clés d'index tiennent dans un `set` ; le côté
référençant — les 102 Mo de profils, la seule couche qui grossira — se parcourt
**un document à la fois**. Ce renversement est tout le contrôle.

## De quel côté chaque arbitrage penche

Ce code décide si un commit de données part. Faux positif = publication de
données saines bloquée ; faux négatif = incohérence publiée.

**Référence orpheline : bloquant.** Le fichier et la clé sont nommés. Aucun faux
positif possible **par construction** : la propriété est binaire — la clé est
dans l'index ou elle n'y est pas — jamais un seuil ni une comparaison à un état
antérieur. C'est la différence de nature avec toutes les décisions de #470, qui
arbitraient des variations légitimes contre des variations suspectes. §2.5 le
tranche seul : une donnée non résolue échoue bruyamment.

**Index ou shard absent : bloquant, mais rapporté à part.** Le remède n'est pas
le même — publier un fichier, pas corriger des clés — et un shard manquant rend
orphelines toutes les références d'une législature d'un coup. Les énumérer une à
une noierait la cause : le motif est distinct, et le compteur reste juste
pendant que les exemples nommés sont bornés à 20.

**Clé absente sans son enregistrement de repli : bloquant.**
`validate_profil()` l'interdit déjà. **Avec** son `scrutin_non_resolu` /
`amendement_non_resolu` : **non bloquant** — c'est la forme normale d'un
amendement du Parlement européen, que ParlTrack livre sans uid AN. La donnée est
conservée, rien n'est perdu ni inventé.

**Le sens inverse — entrées d'index que personne ne référence : rapporté,
jamais bloquant.** Que ce soit exactement 0 à couverture partielle (209 profils
sur 752) méritait d'être compris avant d'en faire une règle. Ce n'est pas une
coïncidence : les deux index sont **construits depuis** `raw_data/profiles`
(`build_scrutins_index.py`, `build_amendements_index_pivot.py`), donc toute
entrée vient d'un profil, et il y a autant de profils bruts que de pivots (209
et 209). Mais leur fusion est **additive par contrat** — « a partial run must
never drop ballots that other profiles' mappings still point at » (AGENTS.md
§3). Cette additivité **implique** qu'une entrée survive légitimement à son
référent : profil corrigé, membre sorti du corpus, tranche non retraitée.
Bloquer dessus reviendrait à interdire la propriété de sûreté principale du
pipeline. C'est un **compteur de dérive**, pas un verdict.

**Les amendements : traités, pas écartés.** Leur index est shardé par
législature, donc plus exposé à une publication partielle qu'un fichier unique
(#431) — c'était la raison de les inclure, pas de les sauter. Coût mesuré :
+1,2 s et +87 Mio, et l'ensemble reste sous le plafond. `--sans-amendements`
existe comme soupape, et **retire le renvoi du périmètre** au lieu de filtrer
ses constats : le rapport dit alors qu'il n'a pas regardé, plutôt que de
déclarer sain ce qu'il n'a pas lu.

## La tolérance est distincte, et ce n'est pas un détail

`tolerer_references_orphelines` **ne partage rien** avec
`tolerer_pertes_profils`. #470 avait identifié le piège dans l'autre sens :
rendre bloquant un contrôle grossier force l'opérateur à relancer avec la
tolérance, ce qui **désarme du même coup les contrôles précis**. Les fusionner
ferait qu'une perte déclarée légitime publierait au passage des références
cassées. Une perte peut être légitime ; une référence orpheline, non. Ce drapeau
n'a **aucun cas d'emploi normal** : il n'existe que pour qu'une panne de l'outil
lui-même ne puisse pas bloquer indéfiniment toute publication.
`test_la_tolerance_est_distincte_de_celle_du_controle_de_perte` verrouille le
cloisonnement.

## Où il est branché, et pourquoi là

Dans `merge-and-pivot`, **après** le contrôle de perte et **avant** le commit.
L'ordre importe dans un seul sens : l'index doit être écrit avant d'être
vérifié. Il l'est — `generate_all_profiles.py --pivot-only` produit
`scrutins.json` (avant la boucle) et `amendements/` (après), et
`generate_group_profiles.py` produit les `cohesion_votes`. Les trois couches
référençantes et les deux index sont donc sur le disque quand le step tourne, et
`test_le_controle_suit_l_ecriture_des_index` le verrouille.

## Le dimensionnement, qui était le vrai risque

Ce script tourne avant le commit : s'il meurt, rien n'est publié, et un
garde-fou qui meurt est pire qu'un garde-fou absent.
[[controle-de-perte-avant-commit]] s'est déjà fait tuer par l'OOM killer une
fois. Mesuré sur les 209 profils et 7 groupes de `01ffa7f` (`/usr/bin/time`,
médiane de trois exécutions, même machine que #470) :

| | durée | RSS max |
| --- | --- | --- |
| contrôle de perte seul, pour repère | 4,76 s | 186,6 Mio |
| **intégrité référentielle, les deux index** | **3,02 s** | **162,0 Mio** |
| intégrité, `--sans-amendements` | 1,79 s | 74,9 Mio |

Sous les 236 Mio actés par #460, et **sous le contrôle de perte lui-même**. Ce
sont deux **processus successifs**, pas un seul : le pic du job reste celui du
plus coûteux des deux, donc **le plafond ne bouge pas** — 186,6 Mio avant comme
après.

La RSS est **invariante au nombre de profils**. Elle est fixée par le plus gros
shard d'index (`15.json`, 24,7 Mo → ~102 Mio à parser) et par le `set` de clés ;
le côté référençant ne coûte qu'un document (le plus gros profil pèse 2,5 Mo, la
médiane 0,44 Mo). Or les deux index sont **déjà à pleine échelle** : leurs
17 535 scrutins et 207 238 amendements distincts sont construits depuis les
archives AN figées, pas depuis les 209 membres actuels. Le passage à 752 membres
multiplie les **références**, pas l'index.

Seule la durée suit, linéairement, et le détail le montre : **0,79 s** de
lecture d'index (fixe : 0,10 s scrutins + 0,69 s amendements) + **9,1 ms par
profil**. Soit **~7,7 s projetées à 752 profils**, dans un job dont le budget est
de 60 min et la mesure de 47,4.

Une alternative a été écartée : extraire les clés d'un shard sans en construire
les valeurs (lecture ligne à ligne, ou `object_pairs_hook`) ferait tomber le pic
sous les 60 Mio. Refusée — `object_pairs_hook` est appelé de bas en haut et ne
connaît pas sa profondeur, donc ne peut pas garder les clés du **deuxième**
niveau ; et lire un JSON ligne à ligne fait dépendre le contrôle d'un format
d'écriture qui ne porte aucune signification (AGENTS.md §3). Une économie dont on
n'a pas besoin ne vaut pas une fragilité.

## Les fixtures sont figées, et les clés y sont réelles

`tests/fixtures/integrite_referentielle/` : un corpus `sain/` (2 profils, 1
groupe, l'index des scrutins réduit à ses seules entrées référencées, l'index
des amendements shardé sur deux législatures) et six **variantes** qui ne
portent que le fichier qui diffère — orpheline côté profil, côté groupe, côté
amendement, shard absent, clé absente déclarée ou non, entrée d'index dérivée.
Provenance dans `meta.fixture` / `meta_fixture`, sur le modèle de
`tests/fixtures/audit_diff_pertes_reelles/`. Aucun test ne lit le corpus vivant,
absent du disque en CI ([[ci-tests-pytest]]).

Les identifiants sont **extraits du corpus**, pas inventés : une clé fabriquée
ne prouverait rien d'une convention de clé. Seules les clés **cassées** des
variantes sont fabriquées, et elles le sont pour être introuvables.

Vérification que ces tests testent bien quelque chose : le blocage sur
l'orpheline désarmé et la couche `groupes` retirée du périmètre, **15 des 33
tests passent au rouge**.


