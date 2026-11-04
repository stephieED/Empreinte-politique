# Les numéros de scrutin de l'archive confrontés à ceux de notre index, à chaque run (#1248, lot 5 bis) (2026-11-03)

`2026-11-03`

> **En bref** — complète [le lot 5](effectifs-des-groupes-confrontes-aux-scrutins-1248.md), sans le modifier. L'archive de scrutins que le contrôle des effectifs télécharge déjà donne la liste complète des scrutins de chaque législature : ses numéros sont comparés à ceux de `pivot_data/scrutins.json`. Un numéro de l'archive absent de l'index est un scrutin perdu, et il est signalé ; les numéros que l'archive elle-même saute sont un fait de la source, relevé sans être signalé. Mesuré le 03/11/2026 : 19 454 scrutins des deux côtés, aucun absent.

## Contexte

C'est le deuxième des totaux proposés le 03/11/2026 pour un indicateur de complétude de la collecte, après les effectifs. La propriétaire a accepté de l'ajouter au lot 5 (« Oui », le 03/11/2026, sur la question « J'ajoute le contrôle des scrutins au lot 5, dans une petite PR ? »).

La première idée était de contrôler la **numérotation** : les scrutins sont numérotés sans interruption dans une législature, donc un numéro manquant serait un scrutin perdu. La mesure l'a corrigée. Notre index saute les n° 3781 et 3782 de la XVe, **mais l'archive de l'Assemblée les saute aussi** : il manque à la source, pas à notre collecte. Un contrôle de numérotation seul aurait signalé, à chaque run, un défaut qui n'est pas le nôtre.

**Même producteur des deux côtés : c'est un contrôle de notre chaîne, pas un croisement de sources** (précisé avec la propriétaire le 03/11/2026). L'index n'est pas une copie de l'archive : `build_scrutins_index.py` le reconstruit depuis les votes des profils (`raw_data/profiles`), et un scrutin n'y entre que si l'un de nos profils l'a voté. Le contrôle vérifie que la chaîne archive → votes → profils → index n'a rien perdu, y compris un scrutin jamais collecté, que le contrôle de perte (un run contre le précédent) ne voit pas. Pour les scrutins, aucune source indépendante de l'Assemblée n'existe.

## Décision

| Comparaison | Traitement |
| --- | --- |
| Numéro de l'archive absent de notre index | signalé : un scrutin perdu |
| Numéro de notre index absent de l'archive | signalé : un scrutin publié que la source ne porte plus |
| Numéro que l'archive saute | relevé dans le rapport, jamais signalé : un fait de la source |
| Scrutin du Congrès | hors de la numérotation : son n° 1 (04/03/2024) double le n° 1 de la XVIe |

Les deux absences s'ajoutent aux jours d'effectif en écart dans le compte de l'issue de suivi (`a_signaler`), qui reste unique et que le run ne ferme jamais.

Le coût est nul : l'archive est déjà téléchargée et lue pour les effectifs.

## Mesure (03/11/2026, données de `ae0730facc`)

| Législature | Scrutins dans l'archive | Absents de notre index | Absents de l'archive | Numéros que l'archive saute |
| --- | ---: | ---: | ---: | --- |
| XIVe | 1 354 | 0 | 0 | aucun |
| XVe | 4 417 | 0 | 0 | 3781, 3782 |
| XVIe | 4 105 | 0 | 0 | aucun |
| XVIIe | 9 578 | 0 | 0 | aucun |

## Ce qui n'a pas été vérifié

- Si les scrutins n° 3781 et 3782 de la XVe existent sur le site de l'Assemblée : il répondait 503 le 03/11/2026.
- Le contrôle compare des numéros, pas le contenu d'un scrutin : un scrutin présent des deux côtés mais tronqué n'est pas vu ici. Le lot 1 relit les positions.
