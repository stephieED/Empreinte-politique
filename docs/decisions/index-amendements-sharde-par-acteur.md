<a id="index-amendements-sharde-par-acteur"></a>
# Index amendements shardé par acteur (#392) (2026-08-17)

`2026-08-17`

> **En bref** — 93 % du coût d'extraction d'un membre était la relecture de l'index.

**Contexte** : la mesure de [[budget-roster-mesure]] (#376) a montré que **93 %
du coût d'extraction d'un membre du roster** (10,9 s sur 11,7 s) était la
relecture des index amendements — 673 Mo de JSON reparsés à **chaque**
candidat par `fetch_amendements_officiels`, soit ~500 Go sur un run complet,
payés même pour les candidats sans aucun amendement.

**Décision** : le cache runtime passe d'un `index_par_acteur.json` unique par
législature à un **répertoire d'une tranche par acteurRef**
(`index_par_acteur/PA1567.json`). Lire un candidat ne coûte plus que sa
tranche (~285 Ko) au lieu de l'index entier.

**Le store `amendements.json` est mémoïsé** — et cette fois c'est sûr, ce que
les mesures tranchent :

| Ce qui reste résident | RSS |
|---|---|
| Les 4 `index_par_acteur` complets (tentative #377, revertée) | **3,84 Go** |
| Les 4 `amendements.json` seuls (retenu) | **426 Mo** |

Le store est petit parce qu'il est dédupliqué (89 Mo sur disque, ~178 000
amendements uniques) ; c'est `index_par_acteur` qui pesait (580 Mo), et il
n'est plus jamais chargé en entier. La mémoïsation revertée en
[[oom-lecture-amendements-par-candidat]] échouait précisément parce qu'elle
gardait la mauvaise moitié.

**Résultat mesuré** : **0,17 s par candidat** pour 3 législatures, contre
~8,2 s auparavant — **gain ×49**, RSS 347 Mo. Le coût par membre du roster
passe donc de ~11,7 s à ~1 s, ce qui ramène la projection d'un run complet
(752 membres) de ~148 min à ~15 min, largement dans le timeout de 60 min.

**Équivalence fonctionnelle vérifiée** contre la source figée committée
(vérité terrain, indépendante du cache) : `_expand_aggregated_amendements_index`
appliquée aux `.json.gz` committés, comparée entrée par entrée à la lecture
shardée — **0 écart sur 360 acteurs** (120 par législature).

*Piège évité au passage* : ma première comparaison opposait les références
brutes lues au nombre d'amendements du profil committé, et affichait des
écarts partout. C'était un artefact — le profil est dédupliqué par
`merge_profile._amendement_key` sur `(numero, texte_vise, date)`, la lecture
ne l'est pas. La bonne vérité terrain est la source figée, pas le profil.

**Migration** : le répertoire de tranches est exigé en lecture ; un cache
hérité (fichier unique de #377, ou forme plate d'avant) est indiscernable
d'un cache absent et donc reconstruit. L'écriture supprime l'ancien fichier
plat et reconstruit le répertoire **de zéro** — une tranche d'acteur disparu
d'une reconstruction ne doit pas survivre.

**Sécurité** : le nom de tranche dérivant de l'acteurRef, tout identifiant
hors forme `PA<chiffres>` est refusé plutôt qu'assaini — un acteurRef
malformé ne peut jamais désigner un chemin hors du cache.

**Effet de bord sur `_download_and_build_amendement_index`** : sur cache-hit,
la liste des acteurs indexés se déduit désormais des **noms** de tranches
sans en ouvrir aucune. Son unique consommateur (`build_amendements_index.py`)
n'en fait que `len()` ; matérialiser les valeurs coûterait des centaines de
Mo pour une information dont personne ne se sert.

**Tests** : lecture limitée à la tranche demandée (vérifié en corrompant la
tranche d'un *autre* acteur — un parcours de l'index complet échouerait),
refus des acteurRef hors forme, suppression de l'index plat hérité,
reconstruction complète du répertoire, plus la mise à jour des fixtures
existantes et du quality gate §3d (qui doit rendre le même verdict que le
lecteur réel). Suite complète : 1179/1179.

