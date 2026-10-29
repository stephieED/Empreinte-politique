# « À jour au » : les sources de la fiche candidat (#1389, #1391) (2026-10-29)

`2026-10-29`

> **En bref** — complète `a-jour-au-par-famille-de-donnees-1389` (13 familles, fiches agrégées). La fiche candidat affiche un pied de source par bulle (#1391) et lisait `sources[].synchro_le`, que la propriétaire a décidé de ne pas afficher comme date de relecture : la session interface demande, le 29/10/2026 et à la demande de la propriétaire, des familles pour le Sénat, le Parlement européen, ParlTrack et le Répertoire national des élus. Neuf familles de plus (22 en tout), mêmes règles ; deux nouveautés : une famille **sans fichier témoin** est datée par son relevé (la date du run, si le job a réussi), et le job de fusion relève les documents européens sur place, avant de composer.

## Les familles ajoutées

| Famille | Job (tous `continue-on-error`, sauf la fusion) | Date tirée de |
| --- | --- | --- |
| `sen.mandats` | `extract-senat` | `.cache/senat/export_sens.zip`, l'archive téléchargée par `curl` et gardée à côté du dump (le dump, lui, porte la date de l'export) |
| `pe.mandats` | `extract-ue-officiel` | `.cache/europarl/meps_FR.json` et `organisations.json` |
| `pe.documents` (titres français) | `merge-and-pivot` | la date du run : le cache des documents cumule des documents de dates différentes |
| `pt.votes`, `pt.amendements`, `pt.interventions`, `pt.textes` | `extract-parltrack` | les dumps `ep_votes`, `ep_plenary_amendments` + `ep_amendments`, `ep_mep_activities`, `ep_dossiers` |
| `rne.mandats_locaux` | `extract-mandats-locaux` | la date du run : l'API tabulaire est interrogée à chaque run, sans cache |

## Décision

1. **Une famille sans témoin** (`pe.documents`, `rne.mandats_locaux`) prend la
   date du run si son relevé dit le job réussi. **Sans relevé**, elle est en
   échec : le job n'a rien dit de lui-même.
2. **Le relevé des documents européens** s'écrit dans le job de fusion, après
   `documents_europeens.py`. La composition du fichier est donc déplacée après
   cette étape (elle suivait la construction des législatures).
3. Les sources que la fiche candidat ne cite dans aucune bulle (Sycomore,
   Wikipédia, Wikidata, Conseil constitutionnel) n'ont pas de famille.

## Non vérifié

- Le premier run qui exécute ces relevés, et la présence des témoins
  (`meps_FR.json` notamment) dans les caches restaurés.
