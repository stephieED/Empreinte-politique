<a id="portail-europeen-hors-chemin-critique-1064"></a>
# Vingt minutes de réseau sortent du chemin critique : le portail européen se réchauffe en parallèle (#1064) (2026-09-21)

`2026-09-21`

> **En bref** — la passe des domaines EuroVoc est un budget réseau, pas un calcul : un job parallèle interroge le portail et `merge-and-pivot` reconstruit l'index sur un cache déjà chaud, budget à zéro.

**Contexte** : mesuré sur le run `35563358605` (21/09/2026), `merge-and-pivot`
dure **52,5 minutes**, et il est séquentiel — c'est le chemin critique, tout le
reste tourne en parallèle.

| Étape | min | part | nature |
| --- | ---: | ---: | --- |
| Générer l'index des dossiers européens | **21,5** | 41 % | **budget réseau** |
| Normalisation pivot + ParlTrack | 7,4 | 14 % | calcul |
| Normalisation pivot roster-driven | 6,8 | 13 % | calcul |
| Fusion des profils bruts | 4,0 | 8 % | calcul |
| Committer et pousser | 3,9 | 7 % | transfert |
| le reste | 8,9 | 17 % | |

Le poste le plus lourd n'est pas un calcul : c'est le budget de 20 minutes que
`dossiers_europeens.py` s'accorde pour interroger le portail du Parlement —
**685 requêtes à 1,85 s l'une**, consommé en entier tant que la file des
dossiers non interrogés n'est pas vidée. Au rythme observé, il reste plus de
cent runs : le problème ne se résorbe pas seul.

**Décision : le job parallèle ne produit pas l'index, il produit le cache.**

`rechauffer-le-portail-europeen` interroge le portail sur les références que
les profils **déjà publiés** citent, et publie `.cache/europarl` en artifact.
`merge-and-pivot` le télécharge, puis reconstruit l'index sur les références de
**ce** run avec `--budget-secondes 0 --plafond-requetes 0` : tout ce que le
portail sait est déjà en cache, et la passe devient instantanée.

**Pourquoi le cache et non l'index.** Un job parallèle qui produirait l'index
le produirait sur les références du run **précédent** ; `merge-and-pivot` devrait
alors soit l'accepter tel quel, soit le refaire. Le cache, lui, n'a pas de
périmètre : il répond à toute question déjà posée, et l'index reste calculé sur
les références du run courant.

**Le décalage d'un run est assumé et déclaré.** Une référence qui apparaît
pendant ce run n'a pas été interrogée quand le job parallèle tournait : elle
sort `question_non_posee` et sera résolue au run suivant (§2 règle 5). Les
références bougent au rythme des dumps ParlTrack, pas à celui des runs.

**Budget à 18 minutes et non 20** : le job doit conclure avant le démarrage de
`merge-and-pivot`, ~27 min après le départ du run, checkout et parsing du dump
compris. Le dépassement ne casse rien — il retarde `merge-and-pivot` du temps
restant, puisque celui-ci l'attend par `needs:`.

**`continue-on-error: true`.** Son échec ne coûte pas le run : `merge-and-pivot`
retombe sur le cache restauré par sa propre clé et sur la reprise des acquis de
l'index publié ([[index-europeen-reprend-ses-acquis-1062]]) — un index plus
pauvre, jamais faux.

**Alternative écartée : réduire le budget** de 20 à 10 minutes. Elle enlève la
moitié du poste sans rien déplacer : la file se vide deux fois moins vite, pour
le même travail total.

**Alternative écartée : un workflow programmé dédié**, qui draguerait la file
indépendamment des runs. Elle découple mieux, et elle ajoute un déclencheur
automatique là où ce dépôt n'en veut pas.

**Ce que ce lot ne fait pas** : les deux passes de normalisation pivot
(7,4 + 6,8 min) restent séquentielles dans `merge-and-pivot`. Elles sont
shardables comme l'extraction l'est déjà, mais leur sortie est un arbre partagé
— c'est un lot à part entière.
