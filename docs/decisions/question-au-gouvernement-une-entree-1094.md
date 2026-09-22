<a id="question-au-gouvernement-une-entree-1094"></a>

# Une question au gouvernement, une entrée sur la fiche candidat (#1094) (2026-09-22)

`2026-09-22`

> **En bref** — deux sources publient la même question au gouvernement : l'acte (questions.assemblee-nationale.fr, avec ministère et réponse, sans texte) et ses tours de parole (compte rendu, avec verbatim). Sur les fiches de candidats, la même question comptait donc deux fois, et l'acte se rangeait sous « Questions écrites et orales ». Backend relie désormais un tour à son acte par `question_ref`, quand le thème le confirme (#1096). Arbitré le 22/09/2026 (option A) : **une entrée par question** dans « Ce qu'il a dit ». Les tours portent le texte, et l'acte leur ajoute « Question au gouvernement · ministère · Voir la question ↗ » avant de se retirer. Un acte qu'aucun tour ne nomme reste seul, rangé sous « Questions au gouvernement ». La mesure de départ (138 doublons) était fausse, gonflée par des intitulés vides ; Backend compte 74 actes reliés sur le corpus du 22/09, 122 attendus après le run.

## Les alternatives écartées

- **L'acte seul** : le texte prononcé disparaît, puisque la source n'en publie pas pour une QG.
- **Les tours seuls** : le ministère interrogé et la page de la question se perdent.
