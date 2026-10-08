<a id="scrutins-europeens-publies-deux-fois-1011"></a>
# Un scrutin européen que ParlTrack publie deux fois n'est compté qu'une fois (#1011) (2026-10-07)

`2026-10-07`

> **En bref** — #1011 décrivait un défaut de forme : 716 des 5 571 scrutins européens publiés portent un numéro composite (`"2018-12-12 00:00:00-13."`) au lieu d'un entier. La mesure a montré un **doublon** : certains jours, ParlTrack publie chaque scrutin deux fois, sous ses deux numéros, et les fiches comptaient ces votes deux fois — **269** votes sur trois fiches de candidats déclarés. Arbitrage de la propriétaire, 07/10/2026 : retirer la copie, garder le numéro tel que la source l'écrit, publier un ordre entier pour l'interface. La correction de forme d'abord validée est abandonnée.

## 1. Le constat

Mesuré le 07/10/2026 sur le privé `72be714b4` et sur le dump `ep_votes` en cache
(12/09/2026) :

| | Mesure |
| --- | ---: |
| Jours de l'index publié portant les deux formes de numéro | 10 |
| Scrutins de ces jours, en numéro entier / en composite | **153 / 153** |
| Jours du dump portant les deux formes | 13 |
| Composites de ces jours ayant un jumeau entier unique à la même seconde | **1 042 sur 1 043** |
| … et les mêmes totaux pour / contre / abstention | 1 041 |
| Jours de l'index où le composite est le seul exemplaire | 62, pour 563 scrutins |

Le composite est horodaté à minuit, et l'heure réelle est recopiée au bout de son
intitulé : `A8-0399/2018 - Siegfried Mureşan - Vote unique 12/12/2018 12:51:11.000`,
jumeau de `97747`, horodaté `2018-12-12T12:51:11`.

## 2. Pourquoi la correction validée d'abord ne tenait pas

Mettre le numéro en entier des deux côtés aurait gardé les doublons, et mêlé dans un
même champ deux sortes de nombres : un identifiant du Parlement (7 649 à 188 564) et un
rang dans la séance (1 à 323). Sur les jours mixtes, l'interface choisissait déjà le
« dernier vote » d'un texte en comparant l'un à l'autre — 257 cas (texte × jour) sur
les fiches de Maurel et Philippot.

## 3. La décision

1. **À l'entrée** : `parltrack_dumps.doublons_de_seance` reconnaît la copie — un
   composite dont l'intitulé donne une heure, qu'un seul scrutin entier du même jour
   porte à la seconde près, avec les mêmes totaux. `build_votes_index` ne l'écrit plus.
   `VERSION_SCHEMA_INDEX` passe à 6, sans quoi un index en cache resservirait les
   copies.
2. **Sur les fiches déjà publiées** : `retirer_votes_publies_deux_fois`, un retrait
   nommé appliqué **après** la fusion, aux deux endroits où l'est `mandats_anterieurs`.
   Il ne lit que le dump déjà présent : il tourne aussi en `--pivot-only`.
3. **Le numéro reste celui de la source.** Le relier par un identifiant
   « explicite » a été écarté en codant : le `scrutin_id` d'un vote européen est nul
   par construction (`normalize_parltrack_dumps._make_vote`, l'espace `an:` est celui
   de l'Assemblée), et l'identifiant de l'index n'est que `pe:` suivi du numéro. Une
   fois les copies retirées, la jointure `(numéro, date)` est univoque.
4. **`ordre_dans_la_seance`** sur chaque entrée de `scrutins_europeens.json` : le
   `voteid` entier, ou le rang que porte le composite. Les deux ne se comparent
   qu'entre scrutins d'une même forme, ce qu'est désormais chaque jour, à un composite
   sans jumeau près. L'interface peut retirer `rangDansLaSeance` et le lire.

## 4. L'effet, simulé sur le corpus publié

Le retrait rejoué sur les 1 402 profils du privé `72be714b4`, avec le dump réel :

| Fiche | Votes avant | Retirés | Jumeau présent, même position |
| --- | ---: | ---: | ---: |
| Emmanuel Maurel | 4 948 | 144 | 144 |
| Florian Philippot | 1 454 | 124 | 124 |
| Raphaël Glucksmann | 1 977 | 1 | 1 |

Aucun autre profil n'est touché. L'index ne citera plus les 153 copies, que plus
aucune fiche régénérée ne porte.

## 5. Ce que cela exige du run

`votes` est une liste stable du contrôle de perte : le run qui porte ce lot verra trois
fiches baisser — 144, 124 et 1 —, et **bloquera**. Il se lance avec
`allow_declared_losses=true` après un run sans la case dont le rapport ne montre que ces
pertes-là (`docs/regles/gardes-avant-commit.md`). Tant que ce run n'a pas eu lieu,
**tout run échoue**, planifié compris.

## 6. Ce qui n'est pas dans ce lot

- **Le contournement de l'interface** (`rangDansLaSeance`) est à retirer côté
  interface, en lisant `ordre_dans_la_seance`.
- **Les fiches gelées** (statut `decline`) ne sont pas régénérées : une copie qu'elles
  porteraient resterait. Mesuré : aucune n'en porte — la simulation a parcouru les
  1 402 fichiers de `pivot_data/profiles/`, `jordan-bardella` compris.
- **L'autre résidu de #1011, les intitulés de scrutin bruts, est accepté comme une
  limite de la source** (arbitrage de la propriétaire, 07/10/2026). Mesuré le 07/10 sur
  `main` : 476 des 5 571 scrutins européens publiés n'ont pas de titre de dossier,
  parce que ParlTrack ne les rattache à aucun dossier ; l'écran montre alors l'intitulé
  du scrutin tel que la source l'écrit. Il ne se résorbera pas run après run, et
  l'interface ne le nettoie pas : déduire un titre d'un intitulé serait inventer
  (§2 règle 2). Seuls 2 de ces intitulés portent encore une heure.
