# Le bloc sombre de « En bref » est retiré — 10/09/2026 (#328)

`2026-09-10`

> **En bref** — `.cp-gc` portait le seul thème sombre de tout `src/`, sans effet possible sous `color-scheme: light` ; le lot institutionnel devait le doubler, il le retire.

## Contexte

`.cp-gc` — le bloc « En bref » de la fiche candidat — était le **seul sélecteur de
tout `web/UI_finale/src/`** à porter un `@media (prefers-color-scheme: dark)` et un
`:root[data-theme='dark']`. Il y définissait douze variables : `--parl`, `--gouv`
et leurs rampes de nuit, `--neutre`, `--rail`, `--gc-ombre`.

Ce fragment ne rend rien. `src/index.css` déclare `color-scheme: light`, qu'un
navigateur honore pour `prefers-color-scheme`, et aucun script ne pose jamais
`data-theme`. `docs/decisions/teintes-des-stades-en-bref-328.md` l'avait mesuré à
la capture — « le rendu est au pixel près identique sous préférence système claire
et sombre » — et avait choisi de le laisser : « c'est du code mort, mais
`test_le_bloc_a_ses_deux_themes` le verrouille délibérément, et le retirer dépasse
ce lot ».

Ce qui a changé : le lot de la dimension institutionnelle ajoute **deux teintes**,
`--pe` et `--senat`, chacune avec sa rampe de quatre valeurs. Étendre le bloc mort
lui ferait porter vingt variables au lieu de douze, et doublerait un vocabulaire
que rien ne lit.

## Décision

Le bloc est retiré, et le commentaire qui prend sa place dit pourquoi. **Un mode
nuit se décide pour la fiche entière ou ne se décide pas** ; il ne se laisse pas
sur un bloc. Les deux nouvelles teintes n'ont donc qu'une seule définition, celle
du jour.

`tests/test_grands_chiffres_328.py::test_le_bloc_a_ses_deux_themes` verrouillait
sa présence ; il verrouille désormais son absence, et l'étend à tout `src/` :
aucun sélecteur ne porte plus de thème sombre. Le test qui vérifiait la cohérence
d'un thème vérifie maintenant la cohérence de son absence — c'est la même
exigence, dans l'autre sens.

## Ce qui n'est pas décidé ici

**Rien contre un mode nuit.** Le jour où il se décide, il se décide sur la fiche
entière, sur `index.css` et sur les six autres feuilles — pas en réanimant douze
variables sur un bloc.

## Alternative écartée

Étendre le bloc à `--pe` et `--senat`, pour ne pas mêler un nettoyage à ce lot.
Écartée parce que le coût n'est pas symétrique : laisser huit lignes mortes est
gratuit, en ajouter huit de plus ancre un vocabulaire que le prochain lot
recopiera à son tour.
