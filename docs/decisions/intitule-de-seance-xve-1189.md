<a id="intitule-de-seance-xve-1189"></a>
# L'intitulé de séance de la XVe était jeté à la normalisation : une entrée Syceron se reconnaît à ce que le parseur a écrit (#1189) (2026-10-04)

`2026-10-04`

> **En bref** — **488 919 des 631 474 prises de parole Syceron de la XVe** portaient leur intitulé au brut et le perdaient au pivot : `normalize_profil` exigeait `seance_ref` ou `session_ref`, que l'archive de la XVe ne publie qu'à partir de mars-avril 2021. Le critère devient `_vient_de_syceron` (référence, code de point ou identifiant), `source` suit sur la forme complète, et un report l'apporte aux entrées déjà publiées. XVIe et XVIIe : aucun écart, avant comme après.

## 1. Le constat, et la mesure qui le rend réel

Signalé par la session qui dessine la fiche de groupe : plus de la moitié des
prises de parole des fiches de groupe n'ont aucun intitulé de débat, presque
toutes sur la XVe, et l'intitulé « apparaît courant 2021 ».

Mesuré le 04/10/2026 sur le privé `40892200f7` (données du public `ea4dfe150c`),
**profils bruts, candidats déclarés et membres de groupe ou de gouvernement
confondus**, en joignant chaque entrée brute à son entrée pivot :

| Législature | Entrées Syceron au brut | avec `sujet` au brut | `sujet` au brut, `theme_officiel` nul au pivot |
| --- | --- | --- | --- |
| XVe | 631 474 | 534 192 | **488 919** |
| XVIe | 304 643 | 285 885 | 0 |
| XVIIe | 288 839 | 256 668 | 0 |

S'y ajoutent 105 entrées de Congrès (`syceron_CRSJOCG…`), même cause.

## 2. La cause

Ce n'est pas un manque de la source. Le parseur actuel, passé sur les 1 562
comptes rendus de l'archive de la XVe, rend un `sujet` sur 129 957 des 157 856
paragraphes de 2020, et le profil brut le porte, avec son `sujet_code_grammaire`.

Il se perdait dans `normalize_profil._normalize_intervention`, qui tenait la
présence de `seance_ref` ou de `session_ref` pour la marque d'une entrée
Syceron. Ce sont des métadonnées de séance, et l'archive de la XVe ne les
publie pas partout — séances qui les portent, sur le total de l'année :

| 2017 | 2018 | 2019 | 2020 | mars 2021 | avril 2021 et après |
| --- | --- | --- | --- | --- | --- |
| 2 / 155 | 1 / 362 | 3 / 333 | 3 / 313 | 16 / 42 | toutes |

Le critère avait été écrit et mesuré sur la XVIIe, où il est vrai partout.

**Effet second, sur la forme complète** (candidats déclarés) : le même critère
gouvernait `source`. Leurs prises de parole de la XVe d'avant cette date sont
publiées avec `source: null` — 14 232 entrées — donc sans attribution dans
l'entrée (§2 règle 2 ; `source_url` restait renseignée), et hors de portée de
`backfill_sujet_seance`, dont la preuve à l'étage pivot est `source.type`.

## 3. La décision

1. **`normalize_profil._vient_de_syceron`** : une entrée brute sort de Syceron si
   elle porte `seance_ref`, `session_ref`, la clé `sujet_code_grammaire` (écrite
   par le parseur depuis #710) ou un identifiant `syceron_…`, que seule la
   collecte Syceron compose. Il gouverne `theme_officiel` sur les deux formes et
   `source` sur la forme complète. `seance` reste `null` là où la source ne
   publie pas la référence (§2 règle 5).
2. **`merge_profile.reporter_source_syceron`**, à l'étage pivot seulement :
   `source` est reportée sur une entrée publiée qui n'en a pas, depuis une
   entrée neuve qui se déclare Syceron. Sans lui, `backfill_sujet_seance`
   aurait écrit l'intitulé sur une entrée restée sans attribution.
3. **L'intitulé lui-même arrive par `backfill_sujet_seance`**, inchangé : la
   passe pivot renormalise tout le brut, donc les entrées déjà publiées le
   reçoivent sans qu'un run recollecte les interventions.

Une question de l'open data (`question_…`) ne satisfait aucune des quatre
preuves : son `sujet` ne devient toujours pas un thème (#657).

## 4. Ce que le correctif change, simulé avant le run

Normalisation puis `merge_pivot_profile` rejouées sur les 2 042 profils du
corpus, sans rien écrire :

| | XVe | XVIe | XVIIe |
| --- | --- | --- | --- |
| Entrées avec intitulé, avant | 45 273 | 285 946 | 256 668 |
| Entrées avec intitulé, après | 534 297 | 285 946 | 256 668 |
| Intitulés perdus ou changés | 0 | 0 | 0 |

Aucune entrée ne disparaît. 669 profils sont touchés : 627 membres de groupe,
32 membres de gouvernement, 10 candidats déclarés.

`tags_thematiques`, dérivé des intitulés, gagne **44 809 étiquettes** sur ces
669 profils. **15 étiquettes changent de forme sur 13 profils**, sans perte de
matière : le repli singulier/pluriel de #1042 retient une autre variante du même
intitulé (« motion de censure » devient « motions de censure », « pénuries de
médicaments » devient « pénurie de médicaments »). Le contrôle de perte les
nommera sans bloquer (#823) : le compte monte sur chaque profil.

**Simulé n'est pas mesuré** : ces chiffres sont ceux d'une fusion rejouée en
local. Le corpus se vérifie après le premier run qui embarque ce lot.

## 5. Alternative rejetée

**Reconnaître l'entrée au seul `sujet_code_grammaire` non nul.** C'est le fait
sourcé derrière le sujet, et il suffit pour l'intitulé. Il ne suffit pas pour
`source` : une prise de parole sous « Article 1er » n'a pas de sujet, donc pas
de code, et resterait publiée sans attribution. L'identifiant `syceron_…`
couvre les deux, et `schema_pivot.url_seance_an` s'y fie déjà.

**Ajouter `source` à `CHAMPS_FAITS_DE_SOURCE`.** La liste est réservée aux faits
lus sur le paragraphe et exclut les champs composés ; `source` est composée par
la normalisation, et le brut porte sous ce nom l'URL de l'archive. Un report
nommé, à l'étage pivot, ne mélange pas les deux.
