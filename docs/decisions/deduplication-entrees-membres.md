<a id="deduplication-entrees-membres"></a>
# `membres[]` publiait deux fois le même fait : dédupliquer sans effacer les changements de portefeuille (#480) (2026-08-20)

`2026-08-20`

> **En bref** — dédupliquer `membres[]` sans effacer un changement de portefeuille.

Mesuré sur `main` à `3a8455a`, en reconstruisant les 10 rosters depuis
`pivot_data/profiles/` — donc **après** [[parlementaire-en-mission-nest-pas-ministre]] :
115 entrées `membres[]` pour 95 personnes, dont **2 entrées strictement
identiques** à une autre — `astrid-panosyan-bouvet` et `marc-ferracci`, mêmes
`membre_id`, `portefeuille`, `debut`, `fin`, `actif` **et** `source_url`, sous
Bayrou.

`build_gouvernement_roster` itère sur les mandats d'appartenance et, pour
chacun, sur les portefeuilles qui le chevauchent. Ces deux personnes portent
deux mandats d'appartenance au gouvernement Bayrou ; le même portefeuille
chevauche les deux, donc la même entrée sort deux fois.
`build_premier_ministre` faisait déjà ce raisonnement pour ses candidats
(« un mandat scindé produit des doublons, pas une ambiguïté ») ;
`build_gouvernement_roster` ne le faisait pas pour ses entrées.

## L'anomalie amont est dans la source, pas dans notre collecte

Le mandat non clos porte `actif: true` pour un gouvernement dont la période
publiée s'achève le 2025-09-09. Deux lectures étaient possibles, et la
correction n'aurait pas été la même : source AN incohérente (à tracer), ou
perte de la date de fin à l'extraction (bug de collecte, à corriger en amont).
**C'est la première**, vérifié dans le zip AMO30 lui-même
(`.cache/acteurs_historique_an/acteurs_historique.zip`, le 20/08/2026) :

| acteur | mandat AN (`uid`) | `organeRef` | `dateDebut` | `dateFin` |
| --- | --- | --- | --- | --- |
| PA795050 (Panosyan-Bouvet) | `PM15855880` | PO855052 | 2024-12-24 | 2025-09-09 |
| PA795050 | `PM15855061` | PO855052 | 2024-12-24 | **absent** |
| PA795884 (Ferracci) | `PM15855886` | PO855052 | 2024-12-24 | 2025-09-09 |
| PA795884 | `PM15855100` | PO855052 | 2024-12-24 | **absent** |

Deux `uid` distincts pour le même organe, la même `dateDebut`, la même
`preseance`, le même `infosQualite` — l'un clos, l'autre non. L'organe lui-même
déclare `viMoDe.dateFin: 2025-09-09` : le mandat jamais clos contredit son
propre organe. Notre extraction
(`candidate_profile._build_acteur_positions_hemicycle_index`) recopie
`dateDebut`/`dateFin` mandat par mandat, sans valeur par défaut ni fusion : elle
ne perd rien, elle reproduit fidèlement une source incohérente. Aucune issue de
collecte à ouvrir ; la déduplication en aval est la bonne correction, et elle
ne masque aucun défaut de chez nous.

## Dédupliquer strictement, jamais par `membre_id`

L'écart 115 → 95 **n'est pas un défaut** : `schema_gouvernement.py` prévoit
« un enregistrement par ministre et par période si changement de portefeuille ».
18 des 20 entrées surnuméraires sont des changements de portefeuille réels
(`david-amiel` sous Lecornu II, `gabriel-attal` sous Borne…). Une déduplication
par `membre_id` seul aurait ramené l'écart à 95 → 95 en effaçant 18 faits
vérifiables (§2.2) — l'erreur exactement inverse, et la plus coûteuse des deux.
Après correction : **113 entrées pour 95 personnes**. Les 10 rosters
reconstruits depuis `pivot_data/profiles/` (`main` à `3a8455a`, le 20/08/2026),
avant et après :

| gouvernement | entrées avant | entrées après | personnes |
| --- | ---: | ---: | ---: |
| FILLON 2 | 5 | 5 | 2 |
| FILLON 3 | 3 | 3 | 1 |
| PHILIPPE | 3 | 3 | 3 |
| PHILIPPE 2 | 9 | 9 | 8 |
| CASTEX | 14 | 14 | 12 |
| BORNE | 31 | 31 | 23 |
| ATTAL | 17 | 17 | 17 |
| BARNIER | 10 | 10 | 10 |
| **BAYROU** | **11** | **9** | 9 |
| LECORNU II | 12 | 12 | 10 |
| **TOTAL** | **115** | **113** | **95** |

Seul Bayrou bouge, de deux entrées : c'est la mesure qui prouve que la
déduplication n'a pas mordu sur les changements de portefeuille. Un
dénombrement par `membre_id` seul aurait ramené la colonne « après » sur la
colonne « personnes », ligne par ligne.

La déduplication porte donc sur l'**entrée entière**, pas sur une clé partielle.
Décidé de ne pas trancher un cas qu'on ne sait pas trancher : deux entrées
identiques sur les cinq champs d'identité (`membre_id`, `portefeuille`, `debut`,
`fin`, `actif`) mais de `source_url` différentes sont **conservées toutes les
deux, avec un warning**. Aucune n'est plus traçable que l'autre — dans le
pipeline actuel, `_source_url_portefeuille` retombe toujours sur l'URL du zip
AMO30 du mandat d'appartenance, donc les deux portent la même valeur et le cas
ne se présente pas — et en choisir une serait un arbitrage silencieux sur une
donnée non résolue (§2.5). Alternative écartée : dédupliquer sur les cinq champs
en gardant la première entrée ; c'est plus court, mais ça fait disparaître sans
bruit une divergence de source le jour où elle apparaît.

Le corollaire de [[test-adosse-au-corpus-vivant]] tient toujours : `membres[]`
dénombre des **entrées**, pas des personnes, et toute vue affichant « N
ministres » devra dédupliquer par `membre_id` à l'affichage. Le tableau de cette
entrée-là (116 entrées, Bayrou à 12) est celui de son époque : il précède #474
puis #480, qui ont retiré respectivement le portefeuille fantôme et les deux
répétitions.

