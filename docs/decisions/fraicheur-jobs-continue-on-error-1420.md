# Une famille dont le job peut échouer se date par son relevé, jamais par `needs` (#1420) (2026-11-03)

`2026-11-03`

> **En bref** — corrige `a-jour-au-par-famille-de-donnees-1389`. Sept familles du fichier de fraîcheur lisaient la réussite de leur job dans `needs.<job>.result`. Or `needs` rend `success` pour un job `continue-on-error` qui a échoué. Le 03/11/2026, la DILA et le portail de l'Économie étaient en panne, et quatre familles se disaient « à jour au 03/11 ». Les quatre jobs concernés publient désormais leur relevé avec `job.status`, comme ceux de la fiche candidat depuis #1389. Un test refuse toute famille datée par `needs` seul dont un job peut échouer.

## Contexte mesuré

Run public `41583086678` (03/11/2026, 6 h 18 → 7 h 46), conclu `success` avec deux jobs en échec, tous deux `continue-on-error` :

| Job | Erreur | Familles publiées |
| --- | --- | --- |
| `extract-actes-jo` | « listing DILA injoignable : Remote end closed connection without response » | `jo.actes` : à jour au 03/11, `a_jour` |
| `extract-finances-etat` | « The read operation timed out », `raw_data/finances_etat.json : inchangé` | `budget_etat`, `drees`, `unedic` : à jour au 03/11, `a_jour` |

`#1389` avait protégé de ce piège les familles de la fiche candidat (« le relevé porte l'état réel du job, `needs` n'y suffit pas »), pas celles qu'il avait créées avant elles.

## Décision

Sept familles, et non cinq comme l'issue le disait au départ : le test écrit pour ce lot a trouvé `extract-articles-votes`, `continue-on-error` lui aussi.

| Famille | Job | Avant | Depuis #1420 |
| --- | --- | --- | --- |
| `an.gouvernements` | `extract-gouvernements` | `needs` seul | `needs` (sauté ou non) **et** le relevé du job (réussi ou non) |
| `an.ordre_du_jour`, `an.articles_votes` | `extract-articles-votes` | idem | idem |
| `jo.actes` | `extract-actes-jo` | idem | idem |
| `budget_etat`, `drees`, `unedic` | `extract-finances-etat` | idem | idem |

`needs` reste lu : il distingue un job **sauté** (`non_relue`) d'un job en échec, ce que le relevé seul ne sait pas faire. Un job arrêté avant son relevé est en échec (« aucun relevé publié »), comme pour les familles de la fiche candidat. Sans fichier témoin, la date reste celle du run.

## Ce qui n'est pas corrigé

`extract-finances-etat` échoue en bloc : un seul jeu de données illisible fait passer les trois familles en échec, même si les autres ont été relus. C'est l'état réel du job, et le plus prudent ; une date par jeu de données demanderait un relevé par fichier.
