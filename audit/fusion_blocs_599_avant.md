# Lot 0 (#599) — ampleur des blocs pris au dernier écrivain

Mesuré le 2026-08-30T10:27:05+00:00 sur le corpus committé.

## Populations

| Population | Effectif |
| --- | ---: |
| Profils bruts lus (`raw_data/profiles`) | 481 |
| Profils pivot publiés (`pivot_data/profiles`) | 481 |
| Profils comptés à part (identité AN absente **attendue**) | 4 |
| **Population du défaut** (bruts moins ces quatre) | **477** |
| Profils non régénérés par le run du 2026-08-29 | 19 |

Comptés à part : `david-lisnard`, `jordan-bardella`, `marine-tondelier`, `nathalie-arthaud`.

## Mesure 1 — `identite` venue d'un écrivain qui n'avait pas la donnée

Population : les **477** profils bruts hors les quatre comptés à part.

| Constat | Profils | Lesquels |
| --- | ---: | --- |
| Le brut porte l'identité du chemin minimal **et** des données parlementaires | 1 | `jean-luc-melenchon` |
| Le pivot ne publie aucun bloc `identite` alors que le brut en porte un de fond | 0 | — |
| Un champ du pivot est `null` alors que le brut du même slug le renseigne | 0 | — |
| `identite.uri_hatvp` est `null` alors qu'`identifiants.hatvp` du même profil porte l'URI | 0 | — |
| **Union nominative** | **1** | `jean-luc-melenchon` |

## Mesure 2 — `meta` pris au dernier écrivain

Population : les **477** profils bruts hors les quatre comptés à part.

| Constat | Profils | Lesquels |
| --- | ---: | --- |
| `meta.warnings` réduit au seul warning du chemin minimal, sur un profil qui porte des données parlementaires | 1 | `jean-luc-melenchon` |
| Régénéré par le dernier run, données parlementaires, mais pas de `meta.collecte_ecartee` | 1 | `jean-luc-melenchon` |
| **Union nominative** | **1** | `jean-luc-melenchon` |

Warnings portés par un brut et absents de son pivot : **1** profils sur les 481 pivots publiés — `jordan-bardella`.

## Mesure 3 — `synchro_sources` antérieur au profil qui le publie

Population : les **477** profils bruts qui portent un bloc `meta.synchro_sources`, sur 481.

| Lecture | Profils | Lesquels |
| --- | ---: | --- |
| Au moins une synchro antérieure de plus de 0.5 j au `genere_le` du même profil (lecture littérale de #599) | 16 | `alexandra-martin`, `alexandra-martin-1`, `bruno-retailleau`, `christelle-d-intorni`, `christelle-petex-levet`, `claire-pitollat`, `edouard-philippe`, `emmanuel-tache-de-la-pagerie`, `gabriel-attal`, `guillaume-gouffier-cha`, `jean-luc-melenchon`, `jerome-guedj`, `laurent-wauquiez`, `loic-prud-homme`, `marine-le-pen`, `sabrina-agresti-roubache` |
| … dont l'écart ne porte que sur `nosdeputes`, source retirée par #529 : un reliquat exact, **pas un défaut** | 9 | `alexandra-martin`, `alexandra-martin-1`, `christelle-d-intorni`, `christelle-petex-levet`, `claire-pitollat`, `emmanuel-tache-de-la-pagerie`, `guillaume-gouffier-cha`, `loic-prud-homme`, `sabrina-agresti-roubache` |
| … dont l'écart porte sur une source **encore écrite** par le pipeline | 7 | `bruno-retailleau`, `edouard-philippe`, `gabriel-attal`, `jean-luc-melenchon`, `jerome-guedj`, `laurent-wauquiez`, `marine-le-pen` |
| Aucun bloc `synchro_sources` du tout, sur un profil qui porte des données parlementaires (**le `meta` d'un écrivain sans source, pris entier**) | 0 | — |

| Source | Profils dont la synchro précède leur `genere_le` | Retard max | Encore écrite ? |
| --- | ---: | ---: | --- |
| `assemblee_nationale` | 1 | 9.9 j | oui |
| `assemblee_nationale_questions` | 5 | 1.94 j | oui |
| `assemblee_nationale_syceron` | 7 | 1.94 j | oui |
| `nosdeputes` | 11 | 9.79 j | non (#529) |

Détail, sources encore écrites :

| Profil | `genere_le` | Régénéré par le dernier run | Source | Synchro publiée | Écart |
| --- | --- | --- | --- | --- | ---: |
| `bruno-retailleau` | 2026-08-29T16:42:37+0000 | oui | `assemblee_nationale_syceron` | 2026-08-28T19:05:03+0000 | 0.9 j |
| `edouard-philippe` | 2026-08-29T16:33:56+0000 | oui | `assemblee_nationale_syceron` | 2026-08-28T18:55:29+0000 | 0.9 j |
| `gabriel-attal` | 2026-08-29T17:01:25+0000 | oui | `assemblee_nationale_questions` | 2026-08-28T17:22:44+0000 | 0.99 j |
| `gabriel-attal` | 2026-08-29T17:01:25+0000 | oui | `assemblee_nationale_syceron` | 2026-08-28T17:22:42+0000 | 0.99 j |
| `jean-luc-melenchon` | 2026-08-29T16:16:17+0000 | oui | `assemblee_nationale` | 2026-08-19T18:43:46+0000 | 9.9 j |
| `jean-luc-melenchon` | 2026-08-29T16:16:17+0000 | oui | `assemblee_nationale_questions` | 2026-08-27T17:55:16+0000 | 1.93 j |
| `jean-luc-melenchon` | 2026-08-29T16:16:17+0000 | oui | `assemblee_nationale_syceron` | 2026-08-27T20:00:49+0000 | 1.84 j |
| `jerome-guedj` | 2026-08-29T16:57:32+0000 | oui | `assemblee_nationale_questions` | 2026-08-28T17:12:59+0000 | 0.99 j |
| `jerome-guedj` | 2026-08-29T16:57:32+0000 | oui | `assemblee_nationale_syceron` | 2026-08-28T17:12:58+0000 | 0.99 j |
| `laurent-wauquiez` | 2026-08-29T16:45:50+0000 | oui | `assemblee_nationale_questions` | 2026-08-28T19:08:11+0000 | 0.9 j |
| `laurent-wauquiez` | 2026-08-29T16:45:50+0000 | oui | `assemblee_nationale_syceron` | 2026-08-28T19:08:10+0000 | 0.9 j |
| `marine-le-pen` | 2026-08-29T16:57:49+0000 | oui | `assemblee_nationale_questions` | 2026-08-27T18:21:01+0000 | 1.94 j |
| `marine-le-pen` | 2026-08-29T16:57:49+0000 | oui | `assemblee_nationale_syceron` | 2026-08-27T18:20:23+0000 | 1.94 j |

