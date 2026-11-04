# Les effectifs confrontés aux scrutins tolèrent trois jours autour d'un changement, et non plus un (#1248, lot 5) (2026-11-03)

`2026-11-03`

> **En bref** — corrige [le lot 5](effectifs-des-groupes-confrontes-aux-scrutins-1248.md), qui tolérait un écart la veille, le jour et le lendemain d'un changement d'appartenance. Les 13 jours restés en écart ont été examinés le 03/11/2026 : 8 suivaient un changement daté 2 ou 3 jours plus tôt ou plus tard dans AMO30. Le compte que l'Assemblée publie avec un scrutin suit le changement avec un décalage ; ce n'est pas une erreur de notre collecte. La tolérance passe à trois jours (`TOLERANCE_JOURS`). Restent 28 scrutins sur 5 jours, tous chez les non-inscrits. **Complétée le même jour** par [le critère du référentiel AMO30](effectifs-juges-par-le-referentiel-amo30-1248.md) : avec lui, la tolérance n'est plus qu'un repli.

## Contexte

Arbitré par la propriétaire le 03/11/2026 (« Oui », sur la question « J'élargis la tolérance à 3 jours autour d'un changement (au lieu d'1), dans la PR #1423 encore ouverte ? »), après l'examen des 13 jours que la première mesure laissait en écart.

## Ce que l'examen a établi

Pour chaque jour, les appartenances du groupe en cause qui changent dans les quinze jours autour de la date, dans nos fiches et dans `raw_data/non_inscrits.json` :

| Famille | Jours | Exemples |
| --- | ---: | --- |
| Changement daté 2 ou 3 jours avant ou après le scrutin | 8 | Alix Fruchon, DR jusqu'au 30/10/2026, LIOT dès le 31/10 ; le scrutin du 02/11 la compte encore à DR. Pierre Moscovici, SRC jusqu'au 31/10/2014, compté le 03/11. Jean-Michel Clément, LaREM jusqu'au 15/06/2018, compté LaREM le 18/06. Grégory Labille, UDI dès le 09/10/2020, pas compté le 12/10. Stéphanie Rist, EPR dès le 27/01/2026, comptée non-inscrite les 28 et 29/01. Dominique Paillat, non-inscrit dès le 24/05/2026, pas compté le 26/05. Patrice Prat, non-inscrit dès le 23/07/2016, déjà compté le 21/07 |
| Nouveau député compté non-inscrit le jour de son arrivée | 1 | Mounir Belhamiti (PA719910) vote comme non-inscrit le 05/10/2018 ; chez nous il entre à LaREM le jour même |
| Décalage de 12 jours | 1 | Olivier Falorni, non-inscrit jusqu'au 28/09/2022 chez nous, compté non-inscrit le 10/10 |
| Sans explication | 3 | non-inscrits, 01/10/2014 (11 contre 9), 06/04/2021 (24 contre 23), 07/06/2021 (25 contre 23) |

La page « fonctions » d'un député sur le site de l'Assemblée donne les dates d'AMO30. Les deux comptes sont ceux de l'Assemblée : le décalage est une convention de sa part, pas une date fausse chez nous.

## Décision

`TOLERANCE_JOURS = 3`. Mesuré le 03/11/2026 sur les 19 455 scrutins : 28 restent en écart, sur 5 jours (les 2 dernières familles du tableau).

## Alternative écartée

- **Consigner les 8 jours un par un** dans `config/ecarts_effectifs_valides.json` : chaque nouveau changement de groupe en ajouterait un, pour la même convention.

## Ce qui n'a pas été vérifié

- Pourquoi l'Assemblée compte avec 2 ou 3 jours de décalage (date de publication au Journal officiel, ou date de la déclaration) : non cherché.
- Les 5 jours restants : ils restent signalés par l'issue de suivi. Belhamiti n'est pas consigné comme écart validé : il n'a pas été arbitré.
