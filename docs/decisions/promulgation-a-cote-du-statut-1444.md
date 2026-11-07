# La promulgation d'un texte de gouvernement se publie à côté de son statut (#1444) (2026-11-06)

`2026-11-06`

> **En bref** — les fiches de gouvernement sous-comptaient les lois promulguées : 70 affichées pour 665 textes promulgués sur les 12 gouvernements qui en ont (Lecornu II : 1 pour 19). Le statut `promulgue` ne remplace que `navette_en_cours` et `rejete`, et c'est voulu : il ne doit pas effacer le passage en CMP ou par 49.3. Arbitré le 06/11/2026 : chaque texte porte désormais `promulgation` (date, numéro de loi), lue dans `pivot_data/textes_promulgues.json`, et la fiche `comptages.promulgues`. Le statut ne change pas.

## Contexte

Relevé par la vérification des anomalies de l'interface (#1444, 06/11/2026). Remesuré le 06/11/2026 sur les fiches publiées (données du run du 05/11, `3131b99da4`) :

| Population : textes des 12 fiches de gouvernement qui en ont | Textes |
| --- | ---: |
| Tous | 1 308 |
| … présents dans `textes_promulgues.json` | **665** |
| … dont publiés `promulgue` | 70 |
| … dont publiés `adopte` | 406 |
| … dont publiés `adopte_cmp` | 179 |
| … dont publiés `adopte_49_3` | 10 |

Exemple : la loi de finances pour 2026 (`DLR5L17N52428`, loi 2026-103, promulguée le 20/02/2026) restait « adoptée par 49.3 », et Lecornu II affichait 1 loi promulguée pour 19.

La cause est un choix écrit : `docs/decisions/dossiers-multi-archives-origine-document.md` (« Statut `promulgue` ») fait corriger par la promulgation les seuls statuts `navette_en_cours` et `rejete`. Il interdit d'écraser `adopte_cmp` et `adopte_49_3`, qui portent la voie suivie (§2 règle 4). `adopte` n'y est pas nommé, mais il n'était pas corrigé non plus.

## Décision

Arbitrée par la propriétaire le 06/11/2026 (« oui, publie la promulgation à côté »).

| Champ | Ce qu'il porte |
| --- | --- |
| `textes[].statut` | inchangé : la voie suivie |
| `textes[].promulgation` | `{"date", "numero_loi"}` si `textes_promulgues.json` porte le dossier, sinon `null` |
| `textes[].promulgation_non_resolue` | `{"motif": "index_indisponible"}`, seulement quand la table n'a pas été lue |
| `comptages.promulgues` | nombre de textes qui portent une promulgation, quelle que soit la voie ; `null` sans table lue |

`comptages.promulgues` ne s'ajoute pas à `par_statut` : un texte `adopte_cmp` promulgué compte dans les deux. C'est le but.

La table est écrite plus tôt dans le même job (`textes_promulgues.py`, avant `generate_gouvernement_profiles.py`) ; l'option `--textes-promulgues` la désigne, par défaut `pivot_data/textes_promulgues.json`. Le workflow n'a pas changé.

## Alternatives écartées

- **La promulgation remplace le statut.** Elle effacerait le passage en CMP ou par 49.3 de 189 textes, ce que la décision existante interdit.
- **Seuls les `adopte` passent en `promulgue`.** Lecornu II afficherait 11 lois promulguées pour 19, et deux lois promulguées s'afficheraient différemment selon leur voie.

## Ce que ce lot ne fait pas

- **L'interface** n'affiche pas encore `comptages.promulgues` : elle lit `par_statut.promulgue`. C'est à la session interface de le faire.
- **Les deux « adoptés » de la même fiche** (« En bref » compte les promulgués, les colonnes les mettent à part : Bayrou 64 contre 45) restent à trancher par la propriétaire (#1444).
- **Les fiches candidat et législature**, qui lisent peut-être le même statut, ne sont pas vérifiées.

Mesuré le 06/11/2026 : les 70 textes publiés `promulgue` sont tous dans la table. Aucun ne recevra `promulgation: null` avec ce statut.

## Ce qui n'a pas été vérifié

- Le chiffre de 665 est celui de la jointure sur les fiches publiées, pas d'une régénération complète : le premier run après la fusion le dira.
