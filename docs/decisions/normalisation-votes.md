<a id="normalisation-votes"></a>
# Normaliser les votes : une liste partagée, un mapping, et deux invariants devenus des jointures (#432) (2026-08-19)

`2026-08-19`

> **En bref** — liste partagée, mapping par membre, deux invariants devenus des jointures.

Un scrutin est **identique pour tous ses votants** — `texte`, `date`, `sort`,
`type_vote`, `source_url`. Seule la `position` est propre au membre. Le méta
complet était pourtant recopié dans chaque profil ayant voté : mesuré sur les
209 profils committés, **398 085 paires (membre, vote) pour 17 422 scrutins
distincts**, soit un facteur 22,8 ×.

## Résultat, mesuré sur régénération complète hors dépôt

| | avant | après |
| --- | --- | --- |
| `votes[]` dans les profils pivot | 179,8 Mo | **17,9 Mo** |
| `pivot_data/scrutins.json` | — | **8,1 Mo** |
| **total** | **179,8 Mo** | **26,0 Mo (−85,5 %)** |
| `cohesion_votes` des groupes | 6,23 Mo | **3,41 Mo (−45,3 %)** |

Les 398 085 paires sont **toutes** conservées, et 0 vote reste non résolu.

## Une liste partagée, pas une liste par profil

Les 4 104 scrutins qu'agrègent les profils de groupe sont **intégralement
inclus** dans les 17 422 des profils individuels : zéro scrutin propre aux
groupes. Une seule liste sert donc les deux, sans exception à gérer. Une liste
par profil, elle, ne dédupliquerait qu'à l'intérieur d'un profil — un scrutin
voté par 74 membres y resterait stocké 74 fois.

C'est la **seule dépendance entre fichiers** de `pivot_data/`, et elle est
assumée : un profil ne se lit plus seul pour ses votes. L'UI charge l'index une
fois par session (mémoïsé), `group_profile` une fois pour les 7 groupes.

## L'identifiant porte la législature

`an:<legislature>:<numero_scrutin>` — convention `<source>:<identifiant_source>`
du dépôt. La législature en fait partie parce que le numéro repart à 1 à chaque
législature (AGENTS.md §5) : un identifiant qui ne la porterait pas confondrait
le n° 1000 de la 16e et celui de la 17e. Elle est résolue par
[[resolution-legislature-votes]] avant toute construction d'identifiant.

## Le champ qui coûtait 12,1 Mo de `null`

`groupe_au_moment_du_vote` est propre au membre, donc légitime dans le mapping —
mais il n'est **jamais peuplé** (0 sur 398 085) et l'écrire quand même coûtait
**12,1 Mo, soit 40 % du mapping**. Il n'est donc écrit que s'il est renseigné,
et son absence signifie « non renseigné », exactement comme `null`.

C'est la **seule** exception à la convention « missing = null » d'AGENTS.md §4,
et elle est chiffrée plutôt que décrétée. Le reste du mapping ne l'imite pas :
`position` reste écrit, même à `null`.

## Ce qui n'est pas normalisé, et pourquoi

`raw_data/profiles` garde ses votes dénormalisés. C'est la couche source-near :
elle porte l'enregistrement tel que la collecte l'a produit, et c'est **d'elle**
que l'index est reconstruit. La normaliser ferait perdre la seule copie
complète, et rendrait l'index irreconstructible.

## Deux invariants sont devenus des jointures

`type_scrutin`, `type_vote`, `texte_lie_id` et `sort` ont migré vers l'index :
leur validation a suivi (`validate_scrutins_index`), et s'exécute désormais une
fois par scrutin au lieu d'une fois par votant.

Mais deux règles ne peuvent plus se vérifier sur un profil seul :

1. **qu'un `scrutin_id` référencé existe** — sinon le mapping pointe dans le vide ;
2. **la règle 4** (un 49.3 n'est jamais une position) — le `sort` est sur le
   scrutin, la `position` sur le profil.

`validate_profil(profil, scrutins_index=...)` les vérifie **si** l'index est
fourni, et les **saute** sinon — jamais ne les déclare valides par défaut. C'est
le prix de la normalisation, et il est explicite plutôt que caché.

## Un vote qu'on ne sait pas rattacher n'est ni supprimé ni deviné

`scrutin_id: null` + `scrutin_non_resolu` portant l'enregistrement complet
(date, texte, sort…). Ni supprimé — ce serait une perte —, ni doté d'une clé
inventée (AGENTS.md §2.5). Zéro cas sur les données actuelles ; le chemin existe
pour que le jour où il s'en présente un, il soit visible et non muet.
`validate_profil` refuse d'ailleurs un `scrutin_id` nul **sans** cet
enregistrement.

## Le repli de `_votes_de_legislature`, enfin retiré

`group_profile` conservait un vote sans législature pour **n'importe quelle**
législature de groupe (`v.get("legislature") or legislature`). C'était juste tant
que tous les groupes étaient de la 16e — les 89 687 votes concernés en venaient
tous — mais un groupe de la 17e les aurait absorbés.

Le repli n'est levé **qu'ici**, une fois la législature effectivement résolue
dans les données : le lever plus tôt aurait retiré ces 89 687 votes de la
cohésion de la 16e, ce qui aurait été une régression, pas une correction.

Un vote sans `scrutin_id` est désormais **écarté** de la cohésion — et compté,
puis remonté en `meta.warnings` du groupe. Une exclusion muette transformerait
un dénominateur en donnée fausse (AGENTS.md §2.7).

## Critère d'acceptation : `cohesion_votes` identique

Vérifié en régénérant les 209 pivots hors dépôt, puis en reconstruisant les 5
groupes AN à partir de leurs membres réels et en comparant les 12 champs de
décompte de chaque entrée :

| groupe | scrutins | écarts |
| --- | --- | --- |
| LFI-16 | 1 996 | 0 |
| LR-16 | 2 232 | 0 |
| REN-16 | 4 099 | 0 |
| RN-16 | 3 405 | 0 |
| SOC-16 | 814 | 0 |
| **total** | **12 546** | **0** |

L'ordre chronologique décroissant des entrées est conservé — il est simplement
relu dans l'index, la date n'étant plus dans l'entrée.

## Deux OOM évités, un rappel

La première version chargeait les 209 profils bruts (1,1 Go de JSON) pour les
reparcourir : tuée par l'OOM killer, comme l'index des amendements en #377 et
#392. La construction est donc **en flux et en une seule passe** — seuls les
17 422 scrutins distincts sont retenus, jamais les 398 085 paires. Pic mesuré :
**347 Mio de RSS, 26 s**.

## `votes_source` : le critère était déjà satisfait

L'issue demandait un `votes_source` cohérent avec les législatures réellement
présentes. Vérification faite : **`votes_source` n'existe pas dans le schéma
pivot** — il n'est lu que côté brut, pour décider d'ajouter la source AN à
`sources[]`, et ce test porte sur le domaine, pas sur les numéros de législature.
Les 86 profils bruts dont le texte libre annonce « législature 16 » à tort
n'affectent donc aucune donnée publiée. Constaté, non traité ici : c'est un
défaut de la couche de collecte, sans conséquence sur la couche publiée.

## Ordre des opérations

L'index doit exister **avant** la passe pivot : `generate_all_profiles --pivot`
le reconstruit lui-même depuis `--out-dir`, échoue franchement si un scrutin
reste irrésoluble, et fusionne additivement sauf `--no-merge`. Un run partiel qui
écraserait l'index laisserait les mappings des profils non retraités pointer
dans le vide — c'est la leçon de [[publication-scopee-artifacts]], transposée à
l'index.

