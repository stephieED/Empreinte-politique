<a id="parole-de-gouvernement-retenue-par-les-dates-1206"></a>

# La fiche de gouvernement retient la parole par les dates de fonction, et ne filtre pas sur la fonction déclarée (#1206) (2026-10-04)

`2026-10-04`

> **En bref** — Avec `fonction` publié sur tous les profils (#1200), la fiche
> de gouvernement pouvait ne garder que la parole prononcée « comme membre du
> gouvernement ». Mesuré sur les sept gouvernements qui portent des prises de
> parole : **130 471 sur 130 753** déclarent une fonction gouvernementale, 10
> déclarent « rapporteur », 272 ne déclarent rien, et **aucune** n'est une
> présidence de séance. La propriétaire a tranché : **on garde tout, rapporteur
> compris.** La fiche continue de retenir la parole par les dates de fonction
> de chaque membre. La fiche de groupe, elle, garde son filtre.

## Le contexte

La fiche de gouvernement retient une prise de parole quand elle est datée
pendant les fonctions de la personne dans ce gouvernement
([`revue-ux-de-la-fiche-de-gouvernement`](revue-ux-de-la-fiche-de-gouvernement.md)).
Elle le faisait faute de mieux : `fonction` était vide hors candidats déclarés.
Le champ est arrivé le 04/10/2026.

## La mesure

Prises de parole retenues par les dates, sur `main` (`935f4a6ec`), avec la
règle de `fonctionGouvernementale.js` complétée par #1206 :

| Gouvernement | Retenues | Fonction gouvernementale | Autre fonction | Sans fonction |
| --- | ---: | ---: | ---: | ---: |
| Philippe II | 48 370 | 48 285 | 3 | 82 |
| Borne | 26 034 | 26 028 | 2 | 4 |
| Castex | 19 007 | 18 880 | 3 | 124 |
| Lecornu II | 15 375 | 15 347 | 0 | 28 |
| Bayrou | 9 537 | 9 535 | 1 | 1 |
| Attal | 8 768 | 8 734 | 1 | 33 |
| Barnier | 3 662 | 3 662 | 0 | 0 |
| **Total** | **130 753** | **130 471** | **10** | **272** |

Les dix « autres » sont toutes des paroles de rapporteur. Aucune des 130 753
ne porte `role_seance` : un ministre ne préside pas la séance. Les dix autres
fiches de gouvernement ne portent aucune prise de parole.

## La décision

Aucun filtre sur `fonction`, aucun filtre de présidence : la fiche ne change
pas. Mots de la propriétaire : « On clôt ce sujet. On garde rapporteur. »

## Alternatives écartées

| Voie | Pourquoi elle n'a pas été prise |
| --- | --- |
| Retirer les 10 paroles de rapporteur | Proposée par l'agent ; écartée par la propriétaire |
| Retirer aussi les 272 sans fonction | Le silence du compte rendu ne dit pas en quelle qualité la personne parlait (`AGENTS.md` §2 règle 5) |
| Ajouter le filtre de présidence par précaution | Sans effet aujourd'hui ; sujet clos |

## Ce que cela ne change pas

La fiche de groupe retire toujours la présidence de séance et la parole de
membre du gouvernement (`paroleDeGroupe.js`), règle arbitrée le 02/10/2026.
