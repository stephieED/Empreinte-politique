<a id="date-des-questions-au-gouvernement-1044"></a>
# Une question au gouvernement est datée par la parution de son compte rendu au JO (#1044) (2026-09-22)

`2026-09-22`

> **En bref** — Les 167 questions sans date restées après la reprise des 715 étaient toutes des questions au gouvernement : la source ne publie jamais le texte d'une QG, et c'est là que la date se lisait. Elles reçoivent la date de parution au Journal officiel de leur compte rendu, que la source publie déjà. Arbitré le 22/09/2026.

## Constat

[`dates-des-questions-en-iso-1044`](dates-des-questions-en-iso-1044.md) avait
repris les 715 dates en `JJ/MM/AAAA` et déclaré les 167 dates vides « une
absence que la source ne porte pas ». Remesuré le 22/09/2026 :

| | |
| --- | ---: |
| Questions sans date, profils `candidat_declare` (brut et pivot) | 167 |
| …de `sous_type: "QG"` | **167** |
| QG des candidats déclarés portant une date | **0** |
| QG de l'archive AN (lég. 15 à 17) sans `textesQuestion` | **8 574 sur 8 574** |
| …avec `textesReponse.infoJO.dateJO` | 8 573 |
| Lég. 16 et 17 : cette date = `cloture.dateCloture` = date d'attribution au ministre | 3 718 sur 3 723 |

`_parse_question_entry` lisait la date dans `textesQuestion.texteQuestion.infoJO`,
que la source ne remplit pas pour une QG, posée à l'oral. L'absence n'était donc
pas dans la source : elle était dans le chemin de lecture.

## Décision

Pour une **QG** sans date de question, `date` reçoit la date de parution au JO
de son compte rendu — la même que `date_reponse`. La question et la réponse
paraissent ensemble dans ce compte rendu : c'est la date de parution de la
question elle-même, écrite par la source, pas une déduction.

- À la collecte : `candidate_profile._parse_question_entry`.
- Pour le corpus publié : `merge_profile.normaliser_dates_interventions`, aux
  deux étages, parce que la fusion est additive et que l'entrée ancienne gagne.
  Appliquée au corpus du 22/09/2026 : 167 → 0 au brut comme au pivot.

Une question écrite (QE) ou orale sans débat (QOSD) sans date reste une
absence (§2 règle 5) : sa date de dépôt n'est pas celle de sa réponse.

**Ce que la date n'est pas** : celle de la séance. Le JO paraît en général le
lendemain — les dates tombent un mercredi ou un jeudi, pour des séances de QG
le mardi et le mercredi. L'écart est d'un jour, dans un sens connu.

## Alternatives rejetées

- **Publier le mois et l'année seulement** : 294 QG sur 8 573 ont un JO daté du
  1er du mois, leur séance étant en général la veille ; le mois y serait faux.
  Et une date réduite au mois ne se range pas dans une période qui commence en
  cours de mois — le défaut d'origine de #1044.
- **Laisser `date` vide et faire lire `date_reponse` par l'interface** : la
  règle vivrait dans un seul lecteur du corpus.
- **Retrouver la date de séance dans les comptes rendus Syceron** : plus juste,
  un lot entier, et la couverture n'a pas été mesurée.
