# Un écart d'effectif n'est le nôtre que si nos données diffèrent du référentiel AMO30 (#1248, lot 5) (2026-11-03)

`2026-11-03`

> **En bref** — le compte de membres publié avec chaque scrutin n'est pas la vérité : c'est un instantané du système de vote, qui contredit parfois le référentiel des appartenances (AMO30) dont nos données sont tirées. Le contrôle du lot 5 compare donc trois comptes : un écart n'est **celui de notre collecte** que si nos effectifs diffèrent de ceux d'AMO30 le jour du scrutin ; si nous comptons comme AMO30 et que le scrutin compte autrement, c'est un **désaccord interne à l'Assemblée**, relevé et jamais signalé. Nos données ont **trois états**, et le troisième est nommé : dans un groupe, non-inscrit, ou **sans groupe enregistré**. Mesuré le 03/11/2026 : 19 455 scrutins, 0 écart de notre collecte, 1 046 désaccords internes.

## Contexte

L'examen des 13 jours d'écart du lot 5 a d'abord conduit à une tolérance de trois jours autour d'un changement ([décision](tolerance-de-trois-jours-sur-les-effectifs-1248.md)). Restaient 5 jours, dont 4 d'arrivée d'un député compté non-inscrit par le scrutin et sans groupe chez nous. Proposer de les déduire en non-inscrits, puis de ne les compter ainsi que dans le contrôle, a amené la propriétaire à deux questions : « on est sûr qu'ils sont non inscrits ou est-ce que ça peut être un retard administratif ? », puis « j'ai l'impression qu'il y a quelque chose qui cloche. Quelque chose dans nos critères n'est pas clair ». Elle avait raison, et la lecture du référentiel brut (archive AMO30 du 03/11/2026) l'a montré :

| Cas | AMO30 | Scrutin | Nous |
| --- | --- | --- | --- |
| 01/10/2014, non-inscrits | 9 | 11 | 9 |
| Patrice Prat, non-inscrit | dès le 23/07/2016 | compté non-inscrit dès le 21/07 (deux jours **avant**) | comme AMO30 |
| Alix Fruchon, DR → LIOT | LIOT dès le 31/10/2026 | comptée DR le 02/11 (deux jours **après**) | comme AMO30 |
| Adrien Morenas, retour le 06/04/2021 | mandat le 06/04, LaREM le 07/04, **aucun** non-inscrit entre les deux (alors qu'en 2017 AMO30 l'enregistre du 22 au 24/07) | compté non-inscrit le 06/04 | comme AMO30 |

`datePublication` n'explique pas le décalage : elle égale `dateDebut` sur ces appartenances. Les deux comptes viennent de l'Assemblée, et ils ne concordent pas entre eux. Comparer nos données au seul compte des scrutins jugeait notre collecte sur les désaccords de la source.

## Décision

Arrêtée avec la propriétaire le 03/11/2026 (« Ok », sur la question « J'écris ces critères dans une décision (les trois états, et un écart compté comme le nôtre seulement si nos données diffèrent du référentiel), et le contrôle classe ses écarts en conséquence ? »).

| Nous contre AMO30 | Nous contre le scrutin | Ce que c'est | Traitement |
| --- | --- | --- | --- |
| égaux | égaux | concordant | — |
| égaux | différents | désaccord interne à l'Assemblée | relevé, jamais signalé |
| différents | — | écart de notre collecte | signalé, sans tolérance : nous divergeons de notre propre source |

Le référentiel est lu par `an_roster.charger_index_gp`, l'index que le roster construit déjà (`{organe: [[acteur, début, fin], …]}`, non-inscrits compris) ; l'archive est celle du roster, téléchargée au besoin. S'il ne se lit pas, le contrôle le dit en tête du rapport et se replie sur le compte du scrutin avec trois jours de tolérance.

**Les trois états.** Un député en mandat est dans un groupe, non-inscrit, ou **sans groupe enregistré** : ni AMO30 ni nos données ne lui donnent d'appartenance ce jour-là. 25 députés sur les quatre législatures sont dans ce cas, presque toujours le seul jour de leur arrivée (11 sur un jour, 4 sur deux et un sur quatre en XVe, 6 sur un jour en XVIe, un en XIVe et un en XVIIe ; Gilbert Collard, 214 jours en 2019, fait exception — mesuré sur l'archive AMO30 du 03/11/2026, le mandat partant de la prise de fonction). **Ce troisième état n'est pas déduit en non-inscrit** : formellement, un député sans groupe enregistré est non-inscrit, et le scrutin le compte ainsi ; mais ces jours-là sont un délai d'enregistrement — Morenas revenait à LaREM —, et l'écrire « non-inscrit » tromperait un article. `raw_data/non_inscrits.json` ne porte que ce qu'AMO30 enregistre.

## Mesure (03/11/2026, données de `4e5a709109`, archives du jour)

| Législature | Scrutins | Concordants | Désaccords internes | Écarts de notre collecte |
| --- | ---: | ---: | ---: | ---: |
| XIVe | 1 354 | 1 330 | 20 | 0 |
| XVe | 4 417 | 4 245 | 160 | 0 |
| XVIe | 4 106 | 4 029 | 76 | 0 |
| XVIIe | 9 578 | 8 774 | 790 | 0 |

Le reste de chaque législature est hors comparaison (Congrès, groupes sous `PO0`, groupe absent de la ventilation). 16 s, pic à 100 Mio, hors téléchargement.

## Ce que le contrôle vérifie donc

Que la chaîne AMO30 → roster → fiches de groupe et `non_inscrits.json` n'a perdu ni ajouté personne, à chaque jour de scrutin : un membre écarté par le roster (un acteur sans slug, une collision), une période mal datée, une fiche oubliée. Il ne vérifie plus l'Assemblée contre elle-même : ses désaccords internes sont comptés, pas signalés.

## Alternatives écartées

- **Déduire « non-inscrit » de l'absence de groupe**, dans `non_inscrits.json` : conforme au Règlement, mais faux pour le lecteur (un délai, pas un choix). Proposé puis retiré le 03/11/2026.
- **Ne compter ainsi que dans le contrôle** : reproduisait la convention du scrutin, donc jugeait encore notre collecte sur la source la moins fiable des deux.
- **Garder le seul compte des scrutins avec une tolérance** : elle absorbe les décalages, mais ne sépare pas notre défaut d'un désaccord de l'Assemblée ; elle reste le repli sans référentiel.

## Ce qui n'a pas été vérifié

- Pourquoi le système de vote compte avec un décalage, dans un sens ou dans l'autre.
- Le troisième état n'est pas relevé par le contrôle : il est mesuré ici une fois, à partir de l'archive AMO30.
