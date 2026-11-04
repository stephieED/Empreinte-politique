<a id="etat-des-sources-page-sources-1389"></a>

# L'état de chaque source s'affiche dans sa fiche, sur la page Sources (#1389) (2026-11-04)

`2026-11-04`

> **En bref** — dernier point de #1389 : montrer au lecteur jusqu'à quand chaque source est à jour, et si sa dernière mise à jour a échoué. Forme A retenue sur maquette par la propriétaire le 04/11/2026 : une ligne **« À jour au »** dans la fiche que chaque source ouvre au survol (souris) ou au toucher (doigt), sous « Mise à jour » ; en cas d'échec, la date de la dernière réussite suivie de « Les mises à jour échouent depuis le … ». Le schéma ne change pas.

## La décision

| Règle | Pourquoi |
| --- | --- |
| Une source réunit toutes ses familles de `fraicheur_sources.json` : la date la plus ancienne, et le début d'échec le plus ancien | la source n'est pas plus à jour que sa partie la moins fraîche (même règle que le pied des bulles, `pied-a-jour-au-par-famille-1389`) |
| `budget_etat`, `drees`, `unedic` se rangent sous « Ministère de l'Économie », « Drees », « Unédic » | leur nom ne commence pas par l'identifiant du schéma |
| Une source sans date n'a pas la ligne | §2 règle 5 |
| Le motif technique de l'échec (`motif_dernier_run`) ne s'affiche pas | vocabulaire du dépôt (`docs/regles/textes-publies.md`) |

## Alternatives écartées (maquette du 04/11/2026)

| Forme | Raison |
| --- | --- |
| B — la date dans chaque case du schéma, à la place du « + » | il fallait une légende pour lire « 03/11 » |
| C — un tableau « À jour au » sous le schéma | recommandée par l’agent, non retenue |

## Ce qui n'a pas de date

Six sources : le Conseil constitutionnel (à venir), Sycomore (citée), l'archive
de l'Assemblée (figée), EuroVoc, Wikipédia et Wikidata. Les trois dernières sont
relues à chaque run mais n'ont pas de famille dans `src/fraicheur_sources.py` :
leur donner une date est un lot Backend.
