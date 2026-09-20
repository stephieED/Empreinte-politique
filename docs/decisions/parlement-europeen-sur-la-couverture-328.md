# Le Parlement européen prend sa place sur `/couverture`, et cesse de déplacer les bornes de l'Assemblée — 11/09/2026 (#328)

`2026-09-11`

> **En bref** — `/couverture` rangeait le Parlement européen sur une ligne « le mandat est publié, l'activité n'est pas collectée », alors que les fiches de candidats portent ses cinq listes, collectées via ParlTrack ; mesuré le 11/09/2026 sur les 30 fiches de candidats publiées, **160 mandats, 383 textes et 5 329 interventions européens étaient comptés sous l’Assemblée**, et les **11 013 votes et 7 303 amendements n'apparaissaient nulle part** ; pire, la `portee` européenne d'une fiche — de sa première à sa dernière donnée — était lue comme une borne de publication, et **les votes de l'Assemblée commençaient au 15/09/2004 au lieu du 20/06/2012**, ce qui faisait nommer Ségolène Royal, Bernard Cazeneuve et Xavier Bertrand comme des trous dans quatre cases du tableau « Ce qui manque » où leur mandat précède simplement la borne ; le Parlement européen devient une institution de la frise avec **les mêmes sous-parties que l'Assemblée et les mêmes champs quand la donnée a la même nature**, lus sur des marqueurs publiés, sans borne dessinée ; demandé par la propriétaire (« être consistant sur les sous-parties, le niveau de détail et le type de données »).

## Ce que le corpus porte, et où la page le rangeait

| Liste européenne | Marqueur publié | Entrées (30 fiches de candidats publiées) | Rangée avant |
| --- | --- | ---: | --- |
| Mandats et appartenances | `chambre === 'PE'` ou `categorie_source === 'europarl'` | 171 | 160 sous l’Assemblée — les commissions et délégations n’ont pas de `chambre` —, 11 sur la ligne « non collecté » |
| Votes | `scrutin_non_resolu.institution` | 11 013 | nulle part — seul un vote joint à l'index des scrutins de l'Assemblée était lu |
| Amendements | `amendement_non_resolu.institution` | 7 303 | nulle part — seul l'index de l'Assemblée était lu |
| Textes portés | `institution` | 383 | sous l'Assemblée |
| Interventions | `source.institution` | 5 329 | sous l'Assemblée |

## Décision

**Cinq sous-parties, dans l'ordre de l'Assemblée, et les champs communs dans le
même ordre** : date, rattachement au texte ou au dossier, sort, lien vers la
source, puis les champs propres à une institution. Un champ propre à l'Assemblée
— commission saisie au fond, banc déclaré, position majoritaire d'un groupe —
n'a pas d'équivalent européen et n'est pas rendu. Un champ commun que la source
européenne ne remplit pas l'est, à zéro : « 0 sur 7 303 » dit que le sort d'un
amendement européen n'est pas publié. Par symétrie, les votes de l'Assemblée
gagnent le champ « avec un lien vers la source » (170 143 sur 170 143), et le
banc déclaré passe après les champs communs.

**Aucune borne européenne n'est dessinée.** Les `portee` européennes des profils
vont de la première à la dernière donnée de chaque personne : ce sont des faits
sur la personne, pas sur ce que la source publie. `bornesPubliees` les écarte ;
une piste européenne déclare `borne: null` et la frise n'y hachure rien.

**Avant la borne basse de la source, la hachure « non publié ».** Aucun profil
ne la porte : elle est mesurée sur les dumps ParlTrack le 11/09/2026 et écrite,
avec sa mesure, dans `couverture-corpus.mjs` (`BORNES_BASSES_PE`) — votes au
**15/09/2004**, premier des 44 648 scrutins du dump `ep_votes` ; amendements au
**01/02/2008**, premier du dump des commissions. Toutes deux sont postérieures
au début de la frise (2000). Une borne basse d'archive ne vieillit pas comme une
borne de fraîcheur (#484). Interventions et textes n'en ont pas : dans le dump
`ep_mep_activities`, **346 073 des 411 098** activités dont la référence porte
une date de séance sont datées du **22/11/2016**, jour où ParlTrack les a
republiées (`date-type: datePublished`) ; le pipeline a repris cette date (#858), et
**4 344 interventions et 314 textes** européens de Florian Philippot,
Jean-Luc Mélenchon et Marine Le Pen sont datés de ce jour-là.

**Après la dernière parution, la hachure « non publié ».** Le pipeline déclare,
liste par liste et fiche par fiche, la date au-delà de laquelle la source ne
publie plus rien dans ce corpus (`bornes_europeennes`, #683) ; pour le corpus,
c'est la plus tardive — votes 11/03/2026, amendements 08/12/2025, textes
14/01/2026, interventions 14/07/2026. Le « début tardif » des interventions européennes, qui semblait être un manque
de source ou de collecte, est cette date de republication.

**Le tableau « Ce qui manque » ne compte que les entrées de l'Assemblée** : il
est rapporté aux fiches qui y ont siégé, et une fiche dont les seuls votes sont
européens n'en porte aucun de l'Assemblée.

Le Sénat garde sa ligne : le mandat est publié, l'activité est hors périmètre (#528).

## Alternative écartée

**Garder la ligne « non collecté » et corriger seulement les bornes.** Moins de
changement, mais une page dont le rôle est de dire ce que le dépôt porte aurait
continué d'affirmer qu'il ne porte pas 24 199 entrées qu'il publie sur les
fiches.
