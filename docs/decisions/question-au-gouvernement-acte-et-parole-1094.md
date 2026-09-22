<a id="question-au-gouvernement-acte-et-parole-1094"></a>
# Une question au gouvernement : un acte, et ses tours de parole reliés à lui (#1094) (2026-09-22)

`2026-09-22`

> **En bref** — Une QG était publiée deux fois dans `interventions[]` : l'acte venu de questions.an, et ses tours de parole venus de Syceron, sans rien qui les relie. Les deux restent, et chaque tour reçoit `question_ref`, l'identifiant de l'acte, quand le thème confirme le lien — jamais par la date seule. Arbitré le 22/09/2026 (option A). Le lot relit aussi le sujet des questions de la XVe, que le parseur perdait.

## Constat

Signalé par la session interface, remesuré le 22/09/2026 sur les 33 profils
pivot des candidats déclarés : 167 entrées `sous_type: "QG"`, toutes
`type_detail: "question"`, sur 12 profils. Une QG y est :

| Forme | Source | `type_detail` | Date | Grain |
| --- | --- | --- | --- | --- |
| l'acte | questions.assemblee-nationale.fr | `question` | parution au JO (#1044) | une par question |
| la parole | Syceron | `question_gouvernement` | séance | de 1 à 13 par question |

Ce n'est donc pas un doublon 1 ↔ 1 : l'interface comptait l'acte comme une
intervention de plus, et le rangeait sous « Questions écrites et orales ».

Deux faits sont apparus à la mesure :

- **la source des QG ne publie aucune référence de séance** : auteur, sujet,
  ministère, date du JO ; l'appariement ne peut passer que par le sujet et la date ;
- **la XVe range le sujet sous `indexationAN.ANALYSE.ANA`** (52 213 questions sur
  52 213, QE, QG, QOSD), que `_parse_question_entry` ne lisait pas : toutes ses
  questions étaient publiées `sujet: null`. Un premier appariement, qui comparait
  deux chaînes vides, avait compté 147 doublons ; le vrai chiffre est plus bas.

## Décision

1. **Deux formes, reliées** (option A). Chaque tour de parole reçoit
   `question_ref` = l'`intervention_id` de son acte. Un lecteur compte les actes
   sur les QG et la parole sur les tours ; l'acte garde sa source et la réponse
   du ministre, le tour garde son ancre de séance (#1087).
2. **Le lien n'est écrit que si le thème le confirme** : même intitulé (casse,
   accents, apostrophes typographiques et espaces ignorés) entre le `sujet` de
   l'acte et le `theme_officiel` du tour — ou son `sujet` quand le compte rendu
   ne publie pas de thème, comme en XVe —, séance de 0 à 2 jours avant la
   parution. Un tour que deux actes réclameraient n'est rattaché à aucun.
3. **Champ dérivé** (`schema_pivot.rattacher_parole_aux_questions`), recalculé
   par `merge_pivot_profile` sur ses deux chemins, comme `tags_thematiques` :
   il n'a besoin d'aucun retrait nommé, et un lien périmé disparaît seul.
4. **Le sujet de la XVe** est lu sous les deux clés ; `backfill_sujet_question`
   le reporte, aux deux étages, sur la question déjà publiée sans sujet (fusion
   additive : l'entrée ancienne gagne). L'index des questions en cache porte
   une marque de format (`FORMAT_INDEX_QUESTIONS`) : les législatures closes ne
   sont jamais périmées (#555), et sans elle l'index de la XVe écrit par l'ancien
   parseur serait servi indéfiniment. Le nom du fichier ne change pas, parce que
   `generate-data.yml` le cite et se publie à la main.

Mesuré le 22/09/2026 sur les 167 QG : 74 actes reliés (279 tours) sur le corpus
publié ; **122 actes reliés (416 tours)** projetés avec les sujets XVe relus par
le parseur corrigé. Restent sans lien : 28 QG dont la date seule désigne une
séance sans thème pour le confirmer, 5 dont le thème contredit, le reste sans
séance ou indécidable.

## Alternatives rejetées

- **B — retirer l'acte et porter ses champs sur les tours** : la réponse du
  ministre recopiée jusqu'à 13 fois.
- **C — retirer les tours** : perd l'ancre de chaque prise de parole (#1087).
- **Lier par la date seule** (28 QG de plus) : le compte rendu montre des tours
  d'un député dans la QG d'un autre — Fabien Roussel réagit « C'est la fin de la
  turbine à gaz ! » pendant la QG de Nicolas Dupont-Aignan du 25/06/2019. Un lien
  déduit serait notre inférence publiée comme un fait (§2 règle 2).
- **Rapprocher des intitulés voisins** (« ventre » / « vente ») : une forme
  devinée.
- **Changer `type_detail` de l'acte en `question_gouvernement`** : l'acte et ses
  tours deviendraient indiscernables par leur type ; `sous_type: "QG"` dit déjà
  ce qu'est l'acte.
