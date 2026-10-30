# Le premier fichier de fraîcheur complet, et ce qu'il a montré (#1389, #1400) (2026-10-30)

`2026-10-30`

> **En bref** — complète `a-jour-au-par-famille-de-donnees-1389` et `a-jour-au-fiche-candidat-1389`, et **corrige** cette dernière : elle ajoutait **huit** familles et non neuf, soit **21** en tout et non 22. Le premier fichier complet, écrit par le run public `40970208263` (29/10 23 h 01 → 30/10 1 h 34), date les 21 familles, toutes `a_jour`. Mais sept d'entre elles portent le 20/09/2026 : les caches du Sénat, du Parlement européen et de ParlTrack ne se renouvellent plus depuis, ce que rien ne montrait avant ce fichier. Défaut ouvert en #1400.

## Correction

`a-jour-au-fiche-candidat-1389` écrit « Neuf familles de plus (22 en tout) ». Elle en ajoute **huit** : `sen.mandats`, `pe.mandats`, `pe.documents`, `pt.votes`, `pt.amendements`, `pt.interventions`, `pt.textes`, `rne.mandats_locaux`. Le fichier publié en compte **21** (13 + 8). Son tableau, lui, est juste.

## Mesuré sur le premier fichier complet (30/10/2026)

| Familles | « À jour au » | Pourquoi |
| --- | --- | --- |
| `an.gouvernements`, `an.ordre_du_jour`, `an.articles_votes`, `jo.actes`, `budget_etat`, `drees`, `unedic`, `pe.documents`, `rne.mandats_locaux` | 30/10 | relues à ce run, sans cache (date du run) |
| `an.mandats`, `an.votes`, `an.interventions`, `an.questions` | 29/10 | le cache AN quotidien, téléchargé la veille |
| `an.dossiers`, `an.amendements` | 26/10 | leurs caches hebdomadaires, téléchargés ce jour-là |
| `sen.mandats`, `pe.mandats`, `pt.votes`, `pt.amendements`, `pt.interventions`, `pt.textes` | **20/09** | caches jamais renouvelés : voir #1400 |

Les journaux du même run le confirment indépendamment du fichier : `extract-parltrack` écrit « Dump ep_votes.json.zst en cache (âge : 39 j) » pour chacun des cinq dumps, et `extract-senat` « Export déjà en cache, téléchargement sauté ».

## Ce que ça établit

Le fichier date ce que la collecte lit vraiment, et pas ce qu'elle croit lire. Une date ancienne y est une mesure : avant le correctif de #1400, la fiche candidat affichera « à jour au 20/09 » pour ces sources, et c'est exact.

## Non vérifié

- La date réelle à laquelle chacune des trois sources a cessé d'être renouvelée : le 20/09 est celle des fichiers témoins.
