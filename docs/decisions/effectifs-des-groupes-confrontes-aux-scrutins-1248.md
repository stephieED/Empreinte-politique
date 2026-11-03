# Confronter nos effectifs de groupe à ceux de chaque scrutin, à chaque run (#1248, lot 5) (2026-11-03)

`2026-11-03`

> **En bref** — les lots 1 à 4 de #1248 disent si ce que nous publions est juste ; celui-ci dit si nous avons tout, pour la composition de l'Assemblée. Chaque scrutin de l'open data porte, groupe par groupe, le nombre de membres que l'Assemblée compte ce jour-là. À chaque run, **tous** les scrutins des quatre législatures sont comparés aux membres de nos fiches de groupe et de `raw_data/non_inscrits.json`, sans tirage. Un écart un jour de changement (la veille, le jour, le lendemain) est toléré ; un écart examiné se consigne dans `config/ecarts_effectifs_valides.json` et ne revient plus tant que les deux comptes ne bougent pas. Mesuré le 03/11/2026 : 19 455 scrutins, 246 en écart sur 13 jours, à examiner une fois.

## Contexte

La propriétaire a demandé le 03/11/2026 un indicateur de complétude de la collecte, en croisant des totaux (textes, amendements, votes, députés) avec une autre source. Quatre pistes ont été posées : la numérotation des scrutins, les lois promulguées du Journal officiel, l'effectif de l'Assemblée, les bilans statistiques des amendements. Pour les députés, la première proposition comparait nos mandats ouverts aux 577 sièges : ce n'est pas une autre source, et **572** profils avec un mandat de député ouvert au 03/11/2026 ne disent pas lesquels manquent. Sa question suivante, « on n'a pas de compte des effectifs provenant des stat de l'AN ? », a trouvé la source : `ventilationVotes.organe.groupes.groupe[].nombreMembresGroupe`, publié avec chaque scrutin, non-inscrits compris. Sur le scrutin n° 9578 (02/11/2026), l'Assemblée compte 574 députés et nous aussi (563 dans 11 fiches de groupe, 11 non-inscrits). L'écart avec les 572 profils se nomme : **Véronique Besse et Philippe Bonnecarrère**, non-inscrits en exercice, n'ont pas de profil. C'est un défaut distinct, signalé à part.

Les deux comptes viennent de l'Assemblée, mais de deux jeux distincts : les scrutins d'un côté, le référentiel AMO30 des appartenances de l'autre. Le contrôle vérifie notre lecture de l'Assemblée, pas l'Assemblée.

## Décision

| Question | Réponse | Raison |
| --- | --- | --- |
| Tirage ou tout ? | **Tout**, à chaque run | le chiffre est dans l'archive, pas dans une page : aucune requête par scrutin. 14 s et 80 Mo pour les 19 455 scrutins en local, plus le téléchargement de quatre archives (50 Mo) |
| Une validation une fois, puis les seuls scrutins nouveaux ? | **Non** (proposé par la propriétaire, arbitré le 03/11/2026 : « oui, lance le lot 5 » sur la forme ci-dessous) | le passé change sans run à pertes : nos fiches de groupe sont recomposées à chaque run, un correctif comme #1412 a redaté 328 profils sans aucune perte, l'Assemblée corrige ses dates, et le contrôle de perte ne compare que des cardinalités |
| Comment ne pas être dérangée deux fois ? | `config/ecarts_effectifs_valides.json` : un écart examiné s'y consigne avec ses deux comptes | il ne revient plus tant que les comptes restent ceux de la ligne ; un compte qui bouge redevient un écart |
| Bloquer ? | **Non** : un signalement et une issue que le run ne ferme jamais (`effectifs-en-ecart-avec-la-source`), comme les lots 1 à 4 | une archive injoignable est « non vérifiée », jamais un écart (§2 règle 5) |

## Ce que la mesure a corrigé dans la règle

Premier passage sans tolérance, le 03/11/2026 : **823 scrutins en écart sur 62 jours**. Ils se rangeaient en familles :

| Famille | Exemple | Traitement |
| --- | --- | --- |
| Le jour d'un changement de groupe | Jean-Pierre Taite, mandat clos le 08/07/2026, membre de son groupe jusqu'au 09/07 : 578 députés ce jour-là | toléré |
| Le lendemain ou la veille | les ministres du gouvernement Barnier quittent leur groupe le 21/10/2024, leurs suppléants y entrent le 23 : le 22, l'Assemblée compte les uns ou les autres, nous aucun (EPR 94 contre 86) | toléré : un jour de part et d'autre d'un changement |
| Le Congrès | le scrutin n° 1 de l'archive de la XVIe (04/03/2024) compte les groupes du Sénat | hors comparaison |
| Des groupes publiés sous `PO0` | 14 scrutins de la XVIIe : la source ne dit pas quel groupe compte combien | hors comparaison |
| Un groupe absent de la ventilation | le MoDem manque à 12 scrutins de la XVe, et la XIVe en compte 4 de ce type | compté à part, pas un écart |

Restent **246 scrutins sur 13 jours** (3 dans la XIVe, 27 dans la XVe, 2 dans la XVIe, 214 dans la XVIIe), presque tous d'un député, souvent non-inscrit. Ce sont eux que la première issue listera, et que l'examen consignera ou corrigera.

## Alternatives écartées

- **Les 577 sièges** : une constante, pas une source ; ils comptent sans nommer.
- **Le fichier des députés du Répertoire national des élus** : seule liste nominative hors de l'Assemblée, mais refusé à la lecture par `AGENTS.md` §7 pour ne pas collecter deux fois ; l'effectif des scrutins suffit et ne coûte rien.
- **Un tirage de quelques scrutins** (proposé en premier) : il ne voit que les jours qu'il tire, alors que tout relire ne coûte pas davantage.

## Ce qui n'a pas été vérifié

- Qui a raison sur les 13 jours restants : le site de l'Assemblée répondait 503 le 03/11/2026.
- Le passage d'un député de Droite républicaine à LIOT, daté du 31/10/2026 chez nous et pas encore compté par l'Assemblée le 02/11 : un retard de la source ou une date fausse chez nous.
