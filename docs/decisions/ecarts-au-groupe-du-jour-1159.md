<a id="ecarts-au-groupe-du-jour-1159"></a>

# Un vote ne se compare qu'au groupe dont la personne était membre ce jour-là (#1159) (2026-10-08)

`2026-10-08`

> **En bref** — La section « écarts avec son groupe » d'une fiche de candidat comparait tous les votes d'une personne à chaque fiche de groupe dont elle avait été membre, y compris après son départ. **La comparaison lit maintenant les périodes d'appartenance que la fiche de groupe publie pour ce membre** (`membres[].periodes`). Delphine Batho passe de 16 écarts affichés à 7, Olivier Becht de 24 à 10 ; les 33 autres fiches de candidats ne changent pas. Ce fichier **complète** `docs/decisions/divergences-avec-le-groupe-328.md`.

## Le contexte

Une fiche de groupe couvre toute une législature. Mesuré le 08/10/2026 sur
`main` 98327b0c0, en exécutant `ecartsAvecLeGroupe` sur les 35 fiches de
candidats, votes en dernière lecture :

| Fiche | Scrutins comparés, avant | Après | Écarts affichés, avant | Après |
| --- | --- | ---: | ---: | ---: |
| Delphine Batho | 132, dont 121 distincts | 101 | 16 | 7 |
| Olivier Becht | 172, dont 132 distincts | 132 | 24 | 10 |

Delphine Batho, sortie du groupe socialiste en mai 2018, y était comparée
jusqu'en 2022 ; Olivier Becht, passé de l'UDI à Agir en mai 2020, aux deux
groupes. Un « écart » avec un groupe dont on n'est plus membre est un fait faux
publié sur une personne (§2 règle 2).

L'issue citait aussi Olivier Faure : il n'était plus touché, ses deux fiches de
groupe de la XVe n'en faisant plus qu'une.

## La décision

- `periodesDansLeGroupe` et `etaitMembreLe`
  (`web/UI_finale/src/utils/appartenanceAuGroupe.js`) : un vote n'entre dans la
  comparaison que si sa date tombe dans une période d'appartenance du membre à
  ce groupe. PR #1257.
- **Entre deux groupes, rien ne se compare**, et la section ne compare rien.
- **Ce qu'on ne sait pas dater n'est pas retiré** : sans période publiée pour le
  membre, la comparaison reste ce qu'elle était.

## Ce qui a été vérifié à côté

La deuxième question de l'issue portait sur les données : `cohesion_votes`
porte-t-il des scrutins hors de la période d'existence du groupe ? Mesuré le
08/10/2026 sur `main` 7700df0e6 : 0 des 160 704 scrutins de cohésion des 31
fiches de groupe tombe hors de `periode` (#1218).

## Ce qui n'a pas été vérifié

Le rendu à l'écran. `ecartsAvecLeGroupe` n'est pas exécutée par les tests du
dépôt, son module n'étant pas importable hors de l'application : la mesure
ci-dessus a été faite hors dépôt.
