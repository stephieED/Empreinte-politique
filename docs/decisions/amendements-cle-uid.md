<a id="amendements-cle-uid"></a>
# Amendements : la clé du store est l'`uid`, jamais le `numero` (préalable à #431) (2026-08-18)

`2026-08-18`

> **En bref** — la clé du store d'amendements est l'`uid` AN, jamais le `numero` qui repart à 1.

**Contexte** : #431 (sous-issue de l'épic volumétrie #429) prescrivait de
normaliser `amendements[]` en écrivant dans chaque profil un mapping
`{numero, role_signataire}` pointant vers une liste dédupliquée, en réutilisant
`_aggregate_amendements_index` — le mécanisme qui produit déjà les index des
législatures figées. En vérifiant le point de vigilance noté dans l'issue
(« le `numero` doit rester unique dans la portée choisie »), il s'est avéré
que **la clé était déjà fausse, et l'est dans les données committées**.

**Mesure — archive AN de la législature 17, 18/08/2026** :

| | Valeur |
| --- | --- |
| Amendements dans l'archive (uid distincts) | 121 805 |
| `numeroLong` distincts | 30 616 |
| Amendements perdus par un store keyé `numero` | 91 189 (74,9 %) |
| Paires (acteur, amendement) réelles | 3 216 366 |
| Paires résolues vers un AUTRE amendement que le leur | 1 302 198 (40,5 %) |

Le `numeroLong` de l'AN **repart à chaque texte** : `AE12` est porté par 7
textes sans rapport, `1` et `10 (Rect)` par des dizaines. La législature 14 est
pire encore : 167 420 amendements pour 22 159 `numeroLong` distincts.

Ce n'est pas une simple perte de volume. Un store `numero -> amendement` garde
le premier amendement rencontré ; toutes les références des autres résolvent
alors vers lui, et le profil affiche un amendement **attribué au mauvais
texte, à la mauvaise date, avec le mauvais sort** — un fait faux, indiscernable
d'un fait correct à la lecture (AGENTS.md §2.2, §2.5). Constaté sur les profils
committés : pour les trois membres dont la législature 17 a été collectée
fraîchement, le nombre d'amendements du profil est **exactement** leur nombre de
`numero` distincts, pas leur nombre d'amendements (christophe-bentz : 4 066 dans
le profil, 7 261 dans l'archive).

**Décision** : la clé du store dédupliqué et des références par acteur devient
l'`uid` AN de l'amendement (`AMANR5L17PO59047BTC1376P0D1N000012`), présent sur
chaque amendement des deux schémas AN — moderne (XV/XVI/XVII) et legacy XIV
(vérifié : 167 420 amendements, 167 420 uid distincts). C'est exactement le
choix déjà fait pour les scrutins (`_build_scrutins_index` : store `uid ->
scrutin`, index `acteurRef -> [[uid, position]]`), dont l'uid porte lui aussi la
législature et reste unique toutes législatures confondues. La leçon était donc
**déjà écrite dans ce fichier** — « Déduplication par `uid`, jamais par
`numero` : le numéro de scrutin AN repart de 1 à chaque législature » (voir
[[votes-multi-legislature]]) — mais n'avait pas été transposée aux
amendements, où la collision est pourtant plus large encore : le numéro d'un
amendement ne repart pas seulement à chaque législature, il repart à chaque
texte. `numero` reste
collecté — il est affichable — mais n'identifie plus rien.

**Décision 2 — un index hérité est refusé, jamais relu.** `_load_frozen_amendement_index`
et `_read_cached_amendements_acteur` vérifient que les références portent un
`uid` (`_index_par_acteur_au_format_uid`) et traitent un index au format
`{numero, ...}` comme un cache absent : le pipeline reconstruit. Servir un tel
index serait pire que ne rien servir, puisque rien à l'usage ne distinguerait
ses enregistrements d'enregistrements corrects.

**Index figés reconstruits** (`build_amendements_index_figees.py`) :

| Législature | Amendements avant (clé `numero`) | Après (clé `uid`) | Facteur | Liens acteur/amendement | Poids committé |
| --- | --- | --- | --- | --- | --- |
| 14 | 21 624 | **154 296** | × 7,1 | 1 338 262 (inchangé) | 4,4 + 4,1 Mo gz |
| 15 | 68 030 | **307 644** | × 4,5 | 3 098 642 (inchangé) | 5,7 + 10,6 Mo gz |
| 16 | 58 305 | **162 240** | × 2,8 | 3 310 514 (inchangé) | 3,2 + 11,1 Mo gz |

Le nombre de liens ne bouge pas — ce sont les mêmes signatures — mais ils
pointent désormais chacun vers le bon amendement. Tous restent très en deçà de
la limite GitHub de 100 Mo par blob. Le facteur d'écrasement varie fortement
d'une législature à l'autre (× 2,8 à × 7,1) : il dépend du nombre de textes sur
lesquels les numéros se réutilisent, pas d'un taux fixe — citer une moyenne
serait trompeur.

Contrôle de non-régression, via le vrai chemin de lecture
(`_load_frozen_amendement_index` -> cache -> `_read_cached_amendements_acteur`),
sur le plus gros signataire de chaque législature :

| Législature | Acteur | Amendements résolus | `numero` distincts | Exemple de collision |
| --- | --- | --- | --- | --- |
| 14 | PA608416 | 12 216 | 3 871 | n° 8 porté par 57 textes |
| 15 | PA719318 | 25 116 | 9 358 | n° 185 porté par 24 textes |
| 16 | PA722142 | 17 272 | 11 438 | n° AE1 porté par 2 textes |

**Conséquence pour #431** : son constat de départ (4 246 026 paires pour 67 058
amendements distincts, facteur 63,3 ×) est mesuré sur des données écrasées, et
son critère d'acceptation (« `amendements` sous 200 Mo sur 752 profils ») doit
être redérivé une fois les données correctes — corriger la clé **augmente** le
nombre réel de paires. La normalisation elle-même reste à faire, sur cette base
saine, et le mapping y référencera l'`uid`.

**Et cette correction alourdit les profils, elle ne les allège pas.** Un profil
ne contenait qu'une entrée par `numero` distinct (les références en doublon
résolvaient vers le même enregistrement, que la fusion dédoublonnait ensuite) ;
il en contient désormais une par signature réelle. Le facteur mesuré va de
1,7 × (législature 17 : 3 216 366 paires réelles contre 1 914 168 distinguables
par `numero`) à 3,2 × (PA608416 en législature 14 : 12 216 amendements contre
3 871 numéros). Les `amendements[]` pesant déjà 81 % du volume d'un profil,
c'est l'ensemble du jeu de profils qui croît d'autant à la prochaine
régénération complète. #431 n'en devient que plus urgent : c'est lui qui rend
ce volume tenable, et il travaille maintenant sur des faits corrects plutôt que
sur un échantillon écrasé.

**Alternative rejetée** : garder `numero` en le qualifiant par le texte
(`(legislature, texte_vise, numero)`). Trois défauts : `texte_vise` est tantôt
un code source (`PIONANR5L15B4852`), tantôt un titre résolu selon l'état de
l'index des dossiers au moment de la collecte — la clé changerait donc d'un run
à l'autre pour le même amendement ; le triplet reste non unique (396 collisions
mesurées sur la seule législature 17) ; et il pèse plus lourd que l'uid qu'il
cherche à éviter.

**Alternative rejetée** : un identifiant synthétique compact (entier de
position) pour alléger le mapping de #431. Non stable d'une reconstruction à
l'autre, donc incompatible avec la fusion additive et `--skip-existing`, qui
doivent pouvoir rapprocher deux collectes successives.

