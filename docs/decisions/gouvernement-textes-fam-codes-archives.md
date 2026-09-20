<a id="gouvernement-textes-fam-codes-archives"></a>
# `gouvernement_textes` : 3 derniers `fam_code` mappés ; `TSORTF02` tranché sur données réelles (#402) (2026-08-18)

`2026-08-18`

> **En bref** — les 3 derniers `fam_code` mappés, `TSORTF02` tranché sur données réelles plutôt que sur un libellé ambigu.

**Contexte** : l'ingestion des archives XV/XVI (#400) a fait apparaître 3
`fam_code` absents de `_FAM_CODE_STATUT_MAP`. Suite directe de #397, même
nature — mais l'enjeu n'était plus le volume, il était de **ne pas deviner le
sens d'un libellé ambigu**.

**Impact réel** : sur les 726 dossiers gouvernementaux des 3 archives, le
module n'émettait que **4 warnings distincts** et n'excluait que **2 dossiers**
de `textes[]` — pour les autres, la promulgation détermine déjà le statut
(#400). Les « 46 warnings » relevés dans l'audit sont le même constat vu depuis
les profils : chaque profil de gouvernement porte la liste consolidée des
warnings de la collecte, donc les 4 warnings se répliquent sur les 10 profils
(44 warnings `gouvernement_textes` + 2 warnings d'exclusion
`gouvernement_profile`). Les 53 occurrences de `TSORTF02` du dataset, elles,
comptent tous les dossiers : seules 6 sont sur un dossier gouvernemental, et
seules 2 sont en position terminale, donc susceptibles de produire un warning.

| `fam_code` | Libellé AN | Décision |
| --- | --- | --- |
| `TSORTF02` | « adopté avec modifications » | `navette_en_cours` |
| `TSORTF14` | « voté par les deux assemblées du Parlement en termes identiques » | `adopte` |
| `TSORTF13` | « rejeté définitivement » | `rejete` |

## `TSORTF02` : le point à trancher, résolu par les données

L'issue posait la question : « adopté avec modifications » décrit-il une
adoption effective par la chambre, ou la poursuite de la navette comme
`TSORTF05` (« modifié ») ? Le libellé seul ne tranche pas — il commence par
« adopté ». Relevé sur les 53 occurrences des trois archives :

| Position de la décision `TSORTF02` | Cas | Ce qui suit |
| --- | --- | --- |
| Non terminale | 29 | **Toujours** une lecture dans l'autre chambre : « modifié » ×17, « adopté sans modification » ×8, CMP, rejet |
| Terminale, dossier promulgué | 17 | Publication au JO |
| Terminale, jamais promulgué | 7 | Rien — le texte n'est pas devenu loi |

Les 29 cas non terminaux établissent le sens : une chambre adopte un texte
**qu'elle a modifié**, donc l'autre chambre doit le réexaminer. C'est le même
fait procédural que `TSORTF05`, d'où le même statut. Les 7 cas terminaux non
promulgués le confirment *a contrario* : `DLR5L16N47697` (réforme de
l'audiovisuel public, Sénat le 11/07/2025) ou `DLR5L16N49849` ne sont jamais
devenus lois. Les mapper à `adopte` affirmerait une adoption que rien
n'établit — exactement ce qu'interdit §2.5.

Les deux codes restent **mappés séparément** plutôt que fusionnés : le
`fam_code` source est conservé tel quel dans le commentaire du mapping, avec
son libellé propre, de sorte que la relecture de l'archive vérifie la décision.

**Le mapping ne change rien à la sortie actuelle** : les 2 dossiers
gouvernementaux dont la décision terminale est `TSORTF02` portent tous deux un
acte de promulgation (`DLR5L15N42841`, `DLR5L16N48973`), donc la correction de
#400 leur donnait déjà `promulgue`. Le mapping supprime le warning et fixe le
comportement pour les données futures, sans rien réécrire.

## `TSORTF14` : adoption parlementaire ≠ promulgation

Unique occurrence : `DLR5L16N49373`, projet de loi constitutionnelle portant
modification du corps électoral calédonien — Sénat « adopté » le 02/04/2024,
puis AN « voté par les deux assemblées du Parlement en termes identiques » le
14/05/2024. Le vote conforme des deux chambres est une adoption parlementaire
achevée : `adopte`. Le texte n'a jamais été promulgué (Congrès jamais réuni,
dissolution de juin 2024) — c'est précisément la distinction que le statut doit
préserver, et la raison pour laquelle `adopte` n'est pas écrasé par la
promulgation dans `_STATUTS_CORRIGES_PAR_PROMULGATION`.

## `TSORTF13` : un rejet par vote, pas par 49.3

Unique occurrence : `DLR5L16N45929`, règlement du budget 2021 — adopté à l'AN
(13/07/2022), rejeté au Sénat, adopté en nouvelle lecture, rejeté à nouveau au
Sénat, puis **rejeté en lecture définitive** à l'AN le 03/08/2022. Jamais
promulgué. `rejete` avec `sort_49_3 = False` : le rejet est prononcé par un
vote, à la différence de `TSORTF24` (rejet consécutif à l'adoption d'une motion
de censure), qui reste seul à porter `rejete_49_3`.

## Résultat mesuré (726 dossiers gouvernementaux, 3 archives)

| Indicateur | Avant | Après |
| --- | --- | --- |
| Warnings distincts à la collecte | 4 | **0** |
| Warnings cumulés sur les 10 profils de gouvernement | 46 | **0** |
| Dossiers à `statut = None` (exclus de `textes[]`) | 2 | **0** |
| `adopte` | 187 | 188 |
| `rejete` | 8 | 9 |

Les deux textes réintégrés : le règlement du budget 2021 sous Borne
(`rejete`) et le projet de loi constitutionnelle calédonien sous Attal
(`adopte`). Les autres statuts sont inchangés — le mapping de `TSORTF02` ne
réécrit rien, il ferme le trou.

Les 10 `fam_code` observés sur une décision de séance de dossier
gouvernemental (`TSORTF01/02/03/05/06/07/13/14/18/24`) sont désormais tous
mappés, et **aucun code non mappé ne subsiste en position terminale**. La
protection §2.5 reste active et testée : un `fam_code` réellement inconnu
produit toujours `statut = None` et un warning.

---

