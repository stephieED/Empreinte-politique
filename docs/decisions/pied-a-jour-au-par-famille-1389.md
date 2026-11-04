<a id="pied-a-jour-au-par-famille-1389"></a>

# Le pied des bulles lit « à jour au » par famille de données, sur les quatre fiches (#1389) (2026-11-04)

`2026-11-04`

> **En bref** — le pied de source des bulles de la fiche candidat (forme B, #1391) affichait « mis à jour le » et lisait `sources[].synchro_le` du profil, qui dit quand la donnée a changé : un profil relu sans changement gardait une date ancienne. La propriétaire a tranché le 29/10/2026 pour **« à jour au »**, la dernière relecture réussie. Le pied lit désormais `fraicheur_sources.json` (`familles[…].a_jour_au`), copié par `sync-data`. Chaque bulle nomme ses familles (« an.votes »), une ligne par source à la date de sa famille **la moins fraîche**, et seules les sources présentes dans `sources[]` du profil ont une ligne.

## La décision

| Règle | Pourquoi |
| --- | --- |
| Une bulle déclare ses familles, ou une source entière (`'an'` = toutes ses familles lues par la fiche, `FAMILLES_PAR_SOURCE`) | « Ce qu'il a voté » n'est pas plus à jour que `an.votes` ; « Ce qu'on n'a pas pu lire » couvre tout |
| Plusieurs familles d'une source dans une bulle : une ligne, la date la plus ancienne | pas de nouveau libellé par famille, et la section n'est pas annoncée plus fraîche que sa partie la moins fraîche |
| Une famille en échec garde sa dernière date réussie | c'est la définition de « à jour au » |
| Une famille sans date, ou absente du fichier : pas de ligne | §2 règle 5 |
| Une source absente de `sources[]` du profil : pas de ligne | relevé au rendu : sans ce filtre, la fiche de Gabriel Attal nommait le Sénat et le Parlement européen, où il n'a pas siégé |
| `a_jour_au` se lit comme une date sans heure | l'ancienne lecture en heure de Paris aurait pu décaler d'un jour |

## Alternative écartée

Une ligne par famille (« Assemblée nationale, votes », « Assemblée nationale,
paroles ») : un libellé de plus par famille, à arrêter avec la propriétaire,
pour une différence d'un jour au plus entre familles d'une même source
(mesuré le 03/11/2026 : les 21 familles sont au 02 ou au 03/11).

## Les trois autres fiches (même lot)

Les fiches de groupe, de gouvernement et de législature portent le même pied,
posé par leur page (`PiedDesBulles`), sans filtre de présence : elles ne sont
pas la fiche d'une personne. Leurs bulles nomment des familles de l'Assemblée,
et `jo.actes` pour les actes du gouvernement.

## Les sources des budgets entrent sur la page Sources (même lot)

La bulle des budgets n'avait pas de pied : ses trois familles (`budget_etat`,
`drees`, `unedic`) n'avaient pas d'entrée sur la page Sources, donc pas de nom.
Ajoutées le 04/11/2026, textes validés par la propriétaire : trois cartes
(« Ministères économiques et financiers », « Drees », « Unédic ») et, au
schéma, trois sources et une ligne « Budgets de l'État et de la sécurité
sociale » reliée à la fiche de gouvernement. Dans le schéma, la première
s'appelle **« Ministère de l'Économie »** : le nom complet débordait de sa
case, à 1 280 comme à 390 px ; nom court retenu par la propriétaire.

## Ce qui reste

L'état de chaque famille (à jour, en échec depuis…) sur la page Sources.
