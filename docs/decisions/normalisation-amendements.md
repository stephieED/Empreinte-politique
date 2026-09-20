<a id="normalisation-amendements"></a>
# Normaliser les amendements : le coût n'est pas l'amendement, c'est sa liste de cosignataires (#431) (2026-08-19)

`2026-08-19`

> **En bref** — mapping par membre, index partagé par législature.

Un amendement est **identique pour tous ses signataires** — `texte_vise`,
`sort`, `date`, `numero`, `type_deposant`, `premier_signataire` et
`co_signataires`. Seul le `role_signataire` est propre au membre.
`_parse_amendement_entry` produit pourtant un enregistrement complet **par
signataire**, chacun portant sa propre copie de la liste des cosignataires.

## Le facteur × 63,3 de l'issue était un artefact de la clé écrasée

L'issue annonçait 4 246 026 paires pour 67 058 amendements distincts. Ce
décompte était fait **par `numero`**, qui repart à chaque texte
([[amendements-cle-uid]]) : il fusionnait des amendements sans rapport et
sous-estimait massivement le nombre de distincts. Redérivé sur `ff3639b`, la
couverture `uid` étant à 100 % :

| | paires | distincts | duplication |
| --- | --- | --- | --- |
| `amendements` | 810 552 | 207 238 | × 3,9 |
| `amendements[].co_signataires` | 77 666 854 | 4 957 807 | **× 15,7** |

**Le vrai coût est `co_signataires`**, pas l'amendement : 23,9 cosignataires en
moyenne, et la liste complète recopiée dans le profil de chacun d'eux — un N².
Elle pèse **1 083,9 Mo des 1 342,4 Mo** d'`amendements[]`.

## Résultat, mesuré sur les 209 profils committés

| | avant | après |
| --- | --- | --- |
| `amendements[]` dans les profils pivot | 1 342,4 Mo | **73,8 Mo** de mapping |
| `pivot_data/amendements/` (méta) | — | **54,4 Mo** |
| `pivot_data/amendements/` (cosignatures) | — | **75,7 Mo** |
| **total** | **1 342,4 Mo** | **203,8 Mo (−84,8 %)** |
| fichiers pivot, tous champs confondus | 1 601,2 Mo | **332,5 Mo** (+ 130,1 d'index = 462,6 Mo, **−71,1 %**) |

Les 810 552 paires sont **toutes** conservées, 0 amendement reste non résolu, et
les 4 957 807 entrées de cosignatures distinctes sont intégralement présentes
dans l'index.

## Où vit la liste dédupliquée : un fichier par législature, cosignatures à part

L'issue laissait la question ouverte. Elle est tranchée par la mesure, pas par
une préférence — la contrainte est la **limite GitHub de 100 Mo par blob**,
celle-là même qui avait imposé le découpage des index figés
([[amendements-legislatures-figees]]).

**Un fichier global unique est exclu dès aujourd'hui** : 130,1 Mo sur les seuls
209 profils actuels, soit 30 % au-dessus de la limite, et le corpus n'est qu'au
tiers de sa couverture.

**Un fichier par législature contenant aussi les cosignatures est exclu à
couverture complète.** Ce n'est pas une extrapolation : les archives figées
donnent le plafond exact, tous signataires confondus, indépendamment du nombre
de profils suivis.

| législature | amendements (archive complète) | méta | cosignatures | tout-en-un |
| --- | --- | --- | --- | --- |
| XIV | 154 296 | 37,2 Mo | 24,0 Mo | 61,2 Mo |
| XV | 307 644 | **74,9 Mo** | 45,4 Mo | **120,3 Mo** |
| XVI | 162 240 | 39,6 Mo | 48,7 Mo | 88,3 Mo |

La XV<sup>e</sup> dépasserait la limite à elle seule. **Cosignatures dans un
fichier compagnon**, donc : le plus gros blob plafonne alors à 74,9 Mo, avec
25 % de marge. Si elle venait à se réduire, gzip reste disponible — mesuré à
**25:1** sur ces fichiers — mais il n'est pas payé d'avance : `pivot_data/` est
lu par le navigateur, et un `.json.gz` y demanderait un `DecompressionStream`.

```
pivot_data/amendements/15.json                 méta partagé
pivot_data/amendements/15.cosignatures.json    fichier compagnon
```

## Le fichier compagnon n'est pas une mise à l'écart

`co_signataires` n'est lu par **personne** aujourd'hui — ni `group_profile`, ni
l'UI, ni les audits — et pèse 59 % de l'index. L'isoler évite à tous les
consommateurs de télécharger ce qu'aucun n'utilise : `charger(...,
avec_cosignatures=False)` est ce que font tous les appelants du dépôt, et
`sync-data.mjs` ne copie pas ces fichiers vers le site.

Ils ne sont pour autant **jamais** supprimés : un réseau de cosignatures est de
la matière première d'analyse (#324), et le principe directeur de l'épic #429
est « normaliser, jamais supprimer ». `ecrire()` refuse d'ailleurs d'écrire un
index chargé sans elles, plutôt que de les effacer en silence.

## L'identifiant : `an:<uid>`, et rien d'autre

Convention `<source>:<identifiant_source>` du dépôt. L'`uid` AN est la **seule**
clé unique d'un amendement — le `numero` repart à chaque texte, et keyer par lui
écrase 74,9 % des amendements ([[amendements-cle-uid]]). Contrairement à celui
d'un scrutin, l'identifiant n'a pas besoin de porter la législature : l'`uid` la
contient déjà (`AMANR5L17…`), et c'est de là qu'elle est lue pour choisir le
fichier — jamais déduite de la date.

Conséquence sur l'ordre des opérations : la construction de l'index **n'est pas
une passe de corpus**. Là où la législature d'un vote se résout par jointure sur
un jumeau étiqueté vivant dans un autre profil ([[resolution-legislature-votes]]),
tout ce dont un amendement a besoin est dans son propre enregistrement.
`generate_all_profiles --pivot` ne reconstruit donc l'index **qu'une fois**,
après la boucle, au lieu de deux pour les scrutins.

## Le seul champ qui divergeait entre les copies

Sur les 810 552 paires, 8 des 9 champs partagés — `co_signataires` compris —
sont **strictement identiques** d'une copie à l'autre. Un seul divergeait :
`premier_signataire`, que `_normalize_amendement` réécrivait à l'identifiant
pivot du profil lecteur quand celui-ci était l'auteur (44 139 cas). Une valeur
propre au lecteur n'a rien à faire dans une liste partagée : l'index retient la
référence AN (`an:PA…`), la seule que la collecte produise et la seule
indépendante du lecteur. Rien n'est perdu — `role_signataire`, resté dans le
mapping, dit déjà que le membre est l'auteur principal.

## Un invariant devenu jointure, trois qui ont suivi les champs

`type_deposant`, `sort` et `base_juridique_irrecevabilite` ont migré vers
l'index : leur validation les a suivis (`validate_amendements_index`), et
s'exécute désormais **une fois par amendement au lieu d'une fois par
signataire** — 207 238 vérifications au lieu de 810 552.

Une règle ne peut plus se vérifier sur un profil seul : **qu'un `amendement_id`
référencé existe**. `validate_profil(profil, amendements_index=...)` la vérifie
**si** l'index est fourni, et la **saute** sinon — jamais ne la déclare valide
par défaut. C'est le prix de la normalisation, et il est explicite plutôt que
caché.

`role_signataire` reste validé côté profil : c'est le seul champ qui y reste.

## Un amendement qu'on ne sait pas rattacher n'est ni supprimé ni deviné

`amendement_id: null` + `amendement_non_resolu` portant l'enregistrement complet.
Zéro cas côté AN (couverture `uid` à 100 %), mais **c'est la forme normale des
amendements du Parlement européen** : ParlTrack ne fournit pas d'`uid` AN, et lui
en fabriquer un serait inventer une clé (AGENTS.md §2.5). Ils gardent donc leur
enregistrement dans le profil — sans perte, un amendement PE n'étant de toute
façon pas recopié chez ses cosignataires.

## La forme plate n'est jamais re-matérialisée

C'est le critère d'acceptation explicite de l'issue, et la panne a déjà eu lieu :
`_load_frozen_amendement_index` appelait `_expand_aggregated_amendements_index`
« pour que le reste du pipeline n'ait pas à distinguer les deux origines », au
prix d'un facteur ~21 et d'un OOM ([[cache-amendements-forme-dedupliquee]],
#377).

Trois propriétés le verrouillent, chacune testée dans les deux sens
(`tests/test_amendements_index.py`) :

1. `joindre()` est un **générateur**, jamais une liste ;
2. `get()` rend **l'objet partagé lui-même** (`is`), jamais une copie ;
3. le pic d'allocation d'une jointure de 5 000 paires sur 10 amendements reste
   plus de 10 × sous celui de la forme plate équivalente — mesure calibrée par
   un témoin, pour ne pas dépendre de la version de Python.

Côté JS, `joinAmendements` est une fonction génératrice pour la même raison.

## `amendements_agreges` identique avant/après

Critère d'acceptation. Vérifié sur les données réelles, en recalculant
`_aggregate_amendements` deux fois sur les mêmes profils — forme d'origine, puis
forme normalisée jointe à l'index — et en comparant les 20 champs de décompte :

| population | paires | champs divergents |
| --- | --- | --- |
| AN-LR-16 (6 membres) | 32 378 | 0 |
| AN-REN-16 (166 membres) | 621 875 | 0 |
| AN-RN-16 (9 membres) | 117 744 | 0 |
| AN-SOC-16 (1 membre) | 14 335 | 0 |
| **les 209 profils** | **810 552** | **0** |

Un amendement qu'aucune source ne renseigne est **écarté et compté**, puis
remonté en `meta.warnings` du groupe : une exclusion muette transformerait un
dénominateur en donnée fausse (AGENTS.md §2.7).

## Ce qui n'est pas normalisé, et pourquoi

`raw_data/profiles` garde ses amendements dénormalisés. C'est la couche
source-near : elle porte l'enregistrement tel que la collecte l'a produit, et
c'est **d'elle** que l'index est reconstruit. Même décision que pour les votes.

## Construction en flux, comme pour les scrutins

Une seule passe, un profil à la fois, chaînes internées : **43 s et 351 Mio de
RSS** pour les 1,5 Go de `raw_data/profiles`. Charger le corpus d'un bloc, c'est
l'OOM de #377 et #392.

## Un index qui n'est pas committé ne sert à rien

Constaté en passant : `pivot_data/scrutins.json` manquait au `git add` du
workflow depuis #432 — l'index n'aurait jamais atterri sur `main`, et les
mappings des profils auraient pointé dans le vide sans la moindre erreur
visible. Corrigé en même temps que l'ajout de `pivot_data/amendements/`, et
verrouillé par `tests/test_ci_publication_profils.py`.

---
