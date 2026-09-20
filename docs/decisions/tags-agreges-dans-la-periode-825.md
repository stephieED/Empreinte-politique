# L'empreinte thématique d'une fiche est celle de sa législature (#825)

`2026-09-10`

> **En bref** — `aggregate_tags_thematiques` ne recevait ni législature ni période : l'empreinte d'une fiche de groupe était l'union des étiquettes de ses membres sur **toute leur carrière**, et les **21 fiches AN publiées** en perdent de 41 % à 86 % une fois filtrées — `REN-16` 4 317 → **2 187** (132 738 interventions écartées), `LAREM-15` 4 451 → **640**, `LR-16` 2 631 → **1 265** ; **l'issue croyait la chose impossible** — « `tags_thematiques` est une liste de chaînes, sans provenance : il n'y a rien à filtrer » — ce qui est vrai de la liste et faux du champ : depuis #710 il est **dérivé** des `interventions[]` par une fabrique unique, et rappeler `deriver_tags_thematiques` sur les interventions retenues suffit, **0 écart** entre la liste publiée et ce que la fabrique rend, mesuré sur les 1 035 profils publiés — ce qui referme du même coup la crainte de « rouvrir le repli documenté », lequel est **dans** la fabrique ; la législature se lit sur l'identifiant (`R5L(\d+)`, trois familles : séance, question écrite, Congrès) et **jamais** sur le `source.legislature` de l'entrée, qui manque sur 12 042 interventions et qui, sur 5 168 autres, porte un **terme européen** homonyme d'une législature française — le repli même que #432 a dû lever ; une entrée sans législature lisible est **conservée** et comptée (§2 règle 5), les 5 329 interventions européennes le sont sans effet mesuré puisque **0** ne porte de `theme_officiel` ni de `mots_cles` ; le filtre ne s'arme que si l'appelant nomme une législature, si bien que `parti_profile` garde l'agrégat de carrière. **Deux tests sont tombés et avaient raison de tomber** : ils posaient `tags_thematiques` à la main sur des profils sans aucune intervention — le défaut de #726, une fixture qui décrit le monde comme le code l'imagine. **Écarté** : porter la provenance sur chaque étiquette, qui changerait le schéma des 1 035 profils pour reconstituer ce que le calcul a déjà sous la main. Suite complète à 4 380, 0 échec.

## Contexte

Quatrième occurrence du même motif en une semaine, après #657 (les
interventions écartées au motif qu'aucun agrégat ne les consomme), #817 (les
textes portés écartés au même motif, toujours ouvert) et #821 (les amendements
agrégés sans filtre de période).

`aggregate_tags_thematiques(profils)` ne recevait ni législature ni période.
L'empreinte thématique d'une fiche de groupe était donc l'union des étiquettes
de ses membres sur **toute leur carrière**.

Mesuré le 10/09/2026 sur les **21 fiches de groupe AN publiées**, en
reconstruisant chaque agrégat depuis les profils de ses membres — la colonne
« sans filtre » reproduit exactement le nombre publié, sur les 21 fiches, ce qui
est la preuve que la mesure porte bien sur le calcul en place :

| Fiche | Membres | Publié | Avec le filtre | Interventions écartées |
| --- | ---: | ---: | ---: | ---: |
| `REN-16` | 196 | 4 317 | **2 187** | 132 738 |
| `LAREM-15` | 341 | 4 451 | **640** | 124 631 |
| `LR-16` | 63 | 2 631 | **1 265** | 154 639 |
| `DR-17` | 64 | 2 459 | **1 220** | 93 999 |
| `EPR-17` | 123 | 3 962 | **1 973** | 87 613 |
| `FI-15` | 17 | 1 158 | **195** | 31 980 |

Les 21 fiches perdent entre 41 % et 86 % de leurs étiquettes. `LAREM-15`
publiait 4 451 étiquettes dont **640** relèvent de la XVe : ses 341 membres ont
massivement siégé sous les deux législatures suivantes, et la fiche comptait
tout.

Le champ est par ailleurs en train de devenir **beaucoup plus riche** — #657 a
rendu les interventions des rosters, `ECOLO-16` passant de 64 à 1 306
étiquettes — ce qui rendait l'absence de filtre d'autant plus visible.

## Ce que l'issue croyait impossible, et qui ne l'était pas

#825 posait deux voies, toutes deux « des lots à part entière », parce que
« `tags_thematiques` est une liste de chaînes, sans provenance : il n'y a rien
à filtrer ».

C'est vrai de la **liste**, et faux du **champ**. Depuis #710,
`tags_thematiques` est **dérivé** des `interventions[]` par une fabrique
unique, `deriver_tags_thematiques` — la provenance n'a pas à être portée, elle
est encore là au moment du calcul. Il suffit de rappeler la fabrique sur les
interventions retenues.

Vérifié avant d'écrire une ligne, sur les **1 035 profils publiés** : la liste
publiée est exactement ce que la fabrique rend depuis les interventions de ces
mêmes profils, **0 écart**. Le no-op mesuré par #710 sur 481 profils tient
toujours sur 1 035.

Cela referme aussi la crainte de l'issue que la voie 2 « rouvre la question du
repli documenté (`theme_officiel`, puis `mots_cles`) » : ce repli est **dans**
la fabrique. Une fiche de groupe en hérite sans qu'une ligne le réécrive.

**Écarté** : porter la provenance sur chaque étiquette (voie 1 de l'issue).
Cela changerait le schéma pivot des 1 035 profils pour reconstituer une
information que le calcul a déjà sous la main.

## La législature se lit sur l'identifiant, jamais sur le champ `legislature`

Même règle que les votes depuis #403, que les amendements depuis #821 :
`legislature_de_intervention` lit `R5L(\d+)` dans l'`intervention_id`, forme
que trois familles d'identifiants partagent — `syceron_CRSANR5L16S…` (séance),
`question_QANR5L15QE…` (question écrite), `syceron_CRSJOCGR5L16S…` (Congrès).

Ce n'est pas une préférence de style. Les interventions portent **aussi** un
`source.legislature`, et s'y fier serait faux à deux titres, mesuré sur les
937 130 interventions des 1 035 profils publiés :

| | Interventions |
| --- | ---: |
| L'identifiant et `source.legislature` concordent | 919 248 |
| L'identifiant la porte, `source.legislature` est absent | 12 042 |
| `source.legislature` vaut 7, 8 ou 9 — un **terme européen** | 5 168 |
| Ni l'un ni l'autre | 511 |

Le second cas ferait perdre 12 042 interventions. Le troisième est pire : les
termes du Parlement européen et les législatures de l'Assemblée partagent le
même espace de nombres, et un `8` européen se lirait comme une VIIIe
législature. C'est exactement le repli que `_votes_de_legislature` a dû lever
en #432.

Un identifiant qui ne porte pas de législature n'est **pas** écarté : rien ne
prouve qu'il soit hors période, et l'écarter ferait passer une ignorance pour
un fait (§2 règle 5). Il est retenu, compté, et le compte est déclaré dans
`meta.warnings`.

## Les interventions européennes ne sont pas triées à part, et c'est mesuré

Une entrée du Parlement européen a un `intervention_id` que la lecture ne sait
pas décomposer (`europarl_P10_CRE-REV(2024)07-17…`, ou `null` pour les 1 611
explications de vote). Elle est donc comptée parmi les entrées « sans
législature », et retenue.

C'est sans effet, et non par chance : **0 des 5 329 interventions européennes
publiées ne porte de `theme_officiel` ni de `mots_cles`** — `_make_intervention`
les pose à `None` et `[]`, la source du PE ne les donne pas. Elles n'apportent
aucune étiquette, donc elles n'en retirent aucune. Le jour où le corpus
européen en portera, il faudra les trier par `source.institution` : la mesure
est écrite ici pour que ce jour-là on sache pourquoi la question ne s'était pas
posée.

## Ce que le filtre ne fait pas

Il ne s'arme que si l'appelant nomme une législature (#821, même règle).
`parti_profile.py` agrège des candidats déclarés partageant un label de parti —
un échantillon éditorial, qui ne couvre aucune législature en particulier : il
appelle sans législature, et l'agrégat reste celui de la carrière.

Le repli d'origine — `tags_thematiques` du profil, puis `theme_officiel`, puis
`mots_cles` — est **mort sur le corpus publié** : 0 des 1 035 profils a un
`tags_thematiques` vide et des interventions thématisées. Il est conservé pour
ce seul appelant, parce que rien ne prouve qu'il le reste.

## Ce que les tests disaient du monde

Deux tests sont tombés, et ils avaient raison de tomber :
`test_build_groupe_profile_tags` posait `tags_thematiques` à la main sur des
profils **sans aucune intervention**. Il décrivait le monde tel que le code
l'imaginait, et ne pouvait donc pas voir que la fiche comptait la carrière
entière — le défaut que #726 nomme : *une fixture décrivant le monde comme le
code l'imagine ne peut pas révéler que le monde a bougé*. Les fixtures portent
désormais des identifiants de la forme réelle.

Quatre tests ajoutés : l'écart des autres législatures, la conservation d'une
entrée sans législature, l'absence de filtre quand aucune n'est nommée, et la
survie du repli `mots_cles` à travers la fabrique.

Suite complète à 4 380, 0 échec.
