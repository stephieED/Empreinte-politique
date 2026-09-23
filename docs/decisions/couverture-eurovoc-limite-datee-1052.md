<a id="couverture-eurovoc-limite-datee-1052"></a>
# La couverture EuroVoc est plafonnée, et la limite est datée (#1052) (2026-09-23)

`2026-09-23`

> **En bref** — 2 555 des 4 642 dossiers européens portent leurs domaines EuroVoc, et ce chiffre ne montera plus beaucoup : 676 des 2 084 dossiers sans domaine sont des procédures des années 2000, que le Parlement n'indexait pas. Les dossiers jamais interrogés sont épuisés, et 40 dossiers réinterrogés à neuf ne rendent rien de plus. Ce n'est pas un retard de collecte : c'est une limite de la source, et elle se dit par période.

## Ce que #1052 demandait

Suivre la couverture de collecte EuroVoc d'un run à l'autre, pour distinguer une
montée lente d'un plafond. La réponse est mesurée.

## L'état, run après run

| `pivot_data/dossiers_europeens.json` | 22/09 08h38 | 22/09 22h20 | 23/09 02h14 | 23/09 21h |
| --- | ---: | ---: | ---: | ---: |
| Avec domaines | 2 553 | 2 555 | 2 555 | 2 555 |
| `documents_non_classes` — le portail a répondu, il ne classe rien | 1 746 | 2 030 | 2 084 | 2 084 |
| `question_non_posee` — jamais demandé | 340 | 54 | **0** | **0** |
| `aucun_document_de_seance` | 3 | 3 | 3 | 3 |

**Aucun dossier n'est jamais passé de « aucun document classé » à résolu.** Les
286 puis 54 changements d'état sont tous des `question_non_posee` qui ont reçu
leur réponse — 284 puis 54 en « rien à classer », 2 en résolus.

## La limite est datée

| Décennie de la référence de procédure | Dossiers | Avec domaines | % |
| --- | ---: | ---: | ---: |
| 2020s | 1 288 | 1 032 | **80 %** |
| 2010s | 2 667 | 1 514 | 56 % |
| **2000s** | 684 | **8** | **1 %** |
| 1990s | 3 | 1 | 33 % |

676 des 2 084 dossiers sans domaine sont des procédures des années 2000 : le
Parlement a commencé à indexer ses documents avec EuroVoc bien après. Aucune
autre ventilation ne montre de rupture comparable — par type de procédure, de
33 % (consultation) à 69 % (résolutions d'actualité) ; par stade, 55 % sur les
procédures achevées contre 24-25 % sur les caduques et les rejetées.

**Aucune population n'est inatteignable par construction** : 55 % des dossiers
qui ont un texte adopté sont résolus, 31 % de ceux qui n'ont qu'une résolution,
47 % de ceux qui n'ont qu'un rapport de commission.

## Ce qui a été vérifié plutôt que supposé

`ESSAIS_PAR_DOSSIER = 2` porte le commentaire « au-delà, la mesure n'a rien
trouvé de plus ». Remesuré le 23/09/2026, portail interrogé **à neuf, hors
cache** :

- **348 des 2 084** dossiers non classés ont plus de deux documents de séance ;
- sur **25** d'entre eux, tirés au hasard, **tous** leurs documents ont été
  essayés — jusqu'à 10 par dossier : **aucun concept EuroVoc** ;
- sur 15 autres dossiers non classés tirés au hasard, même résultat.

Le plafond de deux essais ne cache donc rien, sur cet échantillon de 40.

## La réserve, et pourquoi elle ne rouvre pas cette issue

Le cache `.cache/europarl` **ne se périme jamais** — « un document du Parlement ne
se périme pas » (#965). En production, un dossier déjà interrogé n'est donc
jamais redemandé : un document classé tardivement par le Parlement ne serait pas
revu. La sonde ci-dessus montre que ce cas ne s'est pas produit, pas qu'il ne
peut pas se produire. C'est un mécanisme de cache, pas un suivi de couverture :
il ne se traite pas ici.

## Ce qui se publie de tout ça

La phrase juste pour un lecteur : **« les dossiers antérieurs à 2010 ne sont
pratiquement pas indexés par le Parlement »**, et non « la couverture est
partielle ». Transmis à l'interface le 23/09/2026 pour la page de couverture.
