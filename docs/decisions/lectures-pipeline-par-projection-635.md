<a id="lectures-pipeline-par-projection-635"></a>
# Trois lectures du corpus passent à la projection, et chacune a son plafond dans un test (#635, 2026-08-30)

`2026-08-30`

> **En bref** — les trois accumulations que #628 avait nommées sans les traiter (`gouvernement_roster.load_profils_from_dir`, `audit_pivot_dataset.load_pivot_directory`, la fiche de groupe) rangeaient chaque profil entier : `MemoryError` autour du 370e puis du 300e des 481 profils committés sous un plafond de 2,0 Gio, et près d'un Gio pour la seule fiche LFI ; ramenées à ~140, 22 et 82 Mio par une liste blanche de blocs lus et — pour les listes réellement parcourues — la rétention du seul résultat qu'elles en tirent, sorties prouvées identiques (quatre quarts disjoints du corpus, cinq fiches AN) et trois plafonds déduits du poids sur disque des blocs relâchés.

## Contexte

[[audit-599-projection-blocs-lus-628]] a corrigé une lecture de corpus et, au
passage, **nommé les trois suivantes** : le balayage de `src/` et `scripts/`
qu'il a conduit a trouvé trois accumulations laissées en l'état, mesurées mais
non traitées. Ce lot les traite.

Le motif est le même à chaque fois, et c'est celui de
[[oom-lecture-amendements-par-candidat]] : **623 Mo de JSON sur disque ne
tiennent pas dans 4 Gio**. Une liste de petits dictionnaires occupe bien plus
que le texte qui la décrit — chaque `dict`, chaque clé, chaque chaîne porte son
en-tête Python. Les trois facteurs de gonflement mesurés ici : **× 4,2**, **×
3,95**, **× 4,47**.

## Méthode de mesure, énoncée avant les chiffres

Aucun « avant » n'a été lancé sans plafond. Plusieurs sessions tournent sur
cette machine ; une version qui réclame 2,4 Gio ferait choisir une victime au
noyau, et ce ne serait pas forcément le script mesuré. Donc, à chaque fois :

- un **sous-processus** sous `resource.setrlimit(RLIMIT_AS, plafond)` ;
- le pic relevé par `resource.getrusage(RUSAGE_SELF).ru_maxrss`, **différence**
  entre deux relevés qui encadrent la lecture — jamais un pic absolu, qui
  porterait aussi les imports et les index partagés ;
- quand le plafond est atteint, le **rang** du profil où il l'est, et le facteur
  de gonflement mesuré sur ce qui a été lu jusque-là ; l'extrapolation au corpus
  entier est nommée comme telle ;
- les mesures qui portent sur les index partagés (`pivot_data/amendements/`,
  `pivot_data/scrutins.json`) les chargent **avant** le premier relevé, pour que
  la croissance mesurée soit celle du corpus et pas celle de l'index.

Population de toutes les mesures ci-dessous : les **481 profils de
`pivot_data/profiles/` committés le 30/08/2026**, 651,5 Mo sur disque — 13
candidats déclarés et 468 membres de roster ([[populations-profils-portees-par-les-outils-630]]),
la distinction n'ayant ici aucun effet : les trois lectures les lisent tous.

## Ce que chaque lecture lit réellement

Relevé dans le code de **chaque consommateur** de la valeur retournée, pas dans
l'énoncé de l'issue.

### `src/gouvernement_roster.py:load_profils_from_dir` — `BLOCS_LUS_COMPOSITION`

Trois appelants : `generate_gouvernement_profiles.py`, `gouvernement_profile.py`,
et la CLI du module.

| Bloc | Qui le lit |
| --- | --- |
| `id` | `_derive_membre_entry`, `build_premier_ministre`, `gouvernement_profile._index_acteur_ref_vers_membre` |
| `nom` | les mêmes, plus les warnings qui nomment le profil en cause |
| `mandats` | **parcouru** — `fonction_gouvernementale` et `MINISTERE` ; jamais réduit à un cardinal |
| `identite` | `acteur_ref_depuis_profil`, qui n'y lit que `source_url` |
| `sources` | `gouvernement_profile.build_gouvernement_profile`, agrégat des membres retenus |

Personne n'ouvre `amendements` (577,3 Mo), `votes` (67,1), `interventions`
(22,2), `couverture` (1,6), `meta`, `textes_portes`, `identifiants`,
`tags_thematiques`, `chambres`, `parti`, `groupe`. **12,9 Mo retenus sur
651,5 — 2,0 %.**

### `src/audit_pivot_dataset.py:load_pivot_directory` — `BLOCS_LUS_AUDIT`

Relevé dans les quinze `compute_*`.

| Bloc | Qui le lit | Forme retenue |
| --- | --- | --- |
| `id` | presque tous les indicateurs | entier |
| `nom` | les deux tableaux croisés | entier |
| `parti`, `groupe` | `compute_taux_remplissage`, `_cle_groupe` | entier |
| `schema_version` | `compute_coherence_schema_version` | entier |
| `chambres`, `chambre` | `schema_pivot.lire_chambres` (les deux : le scalaire est le repli déclaré de #493) | entier |
| `sources` | fraîcheur, validité des dates, cohérence chambre/sources | entier |
| `meta` | provenance, warnings, `schema_version`, `genere_le`, licence | entier |
| `mandats`, `tags_thematiques` | `_est_renseigne` — « y a-t-il quelque chose ? » | **cardinal** |
| `votes`, `amendements`, `interventions`, `textes_portes` | `_taille_liste` **et** `compute_plage_dates_candidats` | **cardinal + plage de dates + nombre de dates illisibles** |

`identite`, `identifiants` et `couverture` ne sont ouverts par aucune mesure.

**Pourquoi une réduction et non une projection par clés.** Les quatre dernières
listes sont **réellement parcourues** : la plage de dates lit chaque entrée. Les
réduire à leur cardinal aurait supprimé une mesure. Mais les projeter par clés
ne servait à rien : réduite à sa seule clé lue, une entrée d'`amendements[]`
pèse encore 184 octets de `dict` plus 85 de chaîne — 1,6 Gio pour les 6,09
millions d'entrées du corpus, contre 1,9 avant. Ce qui tient, c'est de garder
**le résultat** que les mesures en tirent, pas les entrées : `ListeReduite`.

Et pour que ce résultat soit exactement celui des listes entières, `reduire_liste`
**appelle les mesures elles-mêmes** (`_plage_dates_champ_simple`,
`_plage_dates_textes_portes`) au lieu de les réimplémenter.

Conséquence assumée : les index partagés sont désormais chargés **avant** le
corpus, parce que c'est eux qui datent un vote (#432) et un amendement (#431).
Passer les index au chargement et pas à `build_report` — ou l'inverse — ferait
diverger le rapport ; ne rien passer des deux côtés reste cohérent, et c'est ce
que font `audit_pipeline.py` et les tests.

### `src/group_profile.py:generate_groupe_profile_from_roster` — `BLOCS_LUS_MEMBRE`

Relevé dans `build_groupe_profile` et `compute_ecarts_cohesion_internes`.

| Bloc | Qui le lit | Forme retenue |
| --- | --- | --- |
| `id`, `nom` | `_derive_membre_entry`, `_aggregate_mandats`, `meta.profils_sources`, rapport interne | entier |
| `mandats` | **parcouru** — éligibilité (§2 règle 7), mandats agrégés | liste, entrées réduites à `categorie`, `chambre`, `debut`, `fin`, `actif`, `label`, `fonction` |
| `votes` | **parcouru** — cohésion, dénominateurs publiés | liste, entrées réduites à `scrutin_id`, `position` |
| `interventions` | **parcouru** — repli de `tags_thematiques` | liste, entrées réduites à `theme_officiel`, `mots_cles` |
| `amendements` | **parcouru** — `_aggregate_amendements` | **contribution** (compteurs additifs) |
| `tags_thematiques` | `aggregate_tags_thematiques` | entier |
| `sources` | recopiées **telles quelles** dans la fiche publiée | entier, jamais projeté |

CLAUDE.md §3 annonçait qu'`identite` n'est jamais lu pour un membre de roster :
le relevé le confirme, et ajoute `identifiants`, `couverture`, `meta`,
`textes_portes`, `chambres`, `chambre`, `parti`, `groupe`. `schema_version` est
lu **avant** la projection, par `_is_pivot_v1`, et par personne ensuite.

`sources` n'est pas projeté et ce n'est pas un oubli : ses entrées sont
**publiées verbatim** dans la fiche de groupe, `synchro_le` compris. Projeter
une donnée publiée, c'est en perdre une part.

**Pourquoi `amendements[]` est réduit et pas projeté.** Il pèse 577,3 des
651,5 Mo, et l'agrégat n'en tire que des **compteurs additifs**.
`contribution_amendements` les calcule au chargement, membre par membre, et
`_aggregate_amendements` devient leur somme. Additif, donc exact : agréger
membre par membre puis sommer donne les mêmes compteurs que parcourir les
listes concaténées, `taux_adoption` restant calculé **après** la somme —
c'est un quotient, il ne se somme pas.

## Ce que ça change, mesuré

Chaque ligne dit sa méthode. « croissance » = différence de `ru_maxrss`
encadrant la lecture ; « plafond » = `RLIMIT_AS` du sous-processus.

| Lecture | Avant | Après |
| --- | --- | --- |
| `load_profils_from_dir`, 481 profils | `MemoryError` au **362e**, 2 004 Mio de croissance pour 500,9 Mo lus (× 4,2) — **~2,67 Gio** extrapolés ; plafond 2,0 Gio | **133 et 141 Mio** sur deux exécutions, 481/481 |
| `load_pivot_directory`, 481 profils, index partagés chargés | `MemoryError` au **293e**, 1 496,6 Mio pour 397,0 Mo lus (× 3,95) — **~2,5 Gio** extrapolés pour le corpus seul ; plafond 2,0 Gio | **22,1 Mio** de corpus ; pic total 539 Mio, dont **517 d'index des amendements** |
| Fiche de groupe LFI (76 profils, 253,5 Mo), index chargés | **985,8 Mio** | **82,3 Mio** |
| Fiche de groupe REN (193 profils, 97,2 Mo), index chargés | 372,4 Mio | 128,1 Mio |
| Fiche de groupe RN (90 profils, 128,1 Mo), index chargés | 471,7 Mio | 59,7 Mio |

### Le rang du `MemoryError` varie d'une exécution à l'autre, et deux décisions le disaient autrement

Le tableau ci-dessus a d'abord porté **un** rang par lecture, comme s'il en
était une propriété. Il n'en est pas une : le rang atteint est celui où la
**somme** du plafond `RLIMIT_AS` et de l'empreinte de départ du processus est
franchie, et cette empreinte de départ varie — imports, index partagés déjà
chargés, fragmentation de l'espace d'adressage. Deux décisions du dépôt
donnaient donc deux rangs différents pour la même lecture et le même corpus :
**381e** dans [[audit-599-projection-blocs-lus-628]] (× 3,79, ~2,42 Gio),
**362e** ici (× 4,2, ~2,67 Gio).

Rejoué le 31/08/2026 sur le même corpus committé, même méthode, même plafond
de 2,0 Gio :

| Lecture | Rang du `MemoryError` | Croissance / octets lus | Après |
| --- | ---: | --- | ---: |
| `load_profils_from_dir` | **383e** sur 481 | 2 003,2 Mio pour 524,4 Mo (× 3,82) — ~2,46 Gio extrapolés | 481/481, croissance **142,8 et 148,8 Mio**, RSS max 156 et 163 Mio, 6,1 et 6,7 s |
| `load_pivot_directory` | **304e** sur 481 | 1 515,7 Mio pour 418,0 Mo (× 3,63) — ~2,34 Gio extrapolés pour le corpus seul | 481/481, croissance de corpus **11,6 Mio**, pic total 494,9 Mio, 19,3 s |
| Fiche LFI (76 profils, 253,5 Mo) | — | croissance **932,6 Mio**, pic 1 433,4 Mio, 17,2 s | croissance **66,7 Mio**, pic 568,4 Mio, 16,5 s |

Les cinq fiches AN, avant → après, en croissance : LFI 932,6 → 66,7 ; REN
348,3 → 113,0 ; RN 446,6 → 50,1 ; LR 308,6 → 8,7 ; SOC 188,9 → 0,0 Mio.

**Ce qui tient d'une exécution à l'autre**, et c'est ce sur quoi la décision
repose : la lecture d'avant n'atteint jamais le 481e profil sous 2,0 Gio, celle
d'après le fait toujours, et le facteur de gonflement reste entre × 3,6 et
× 4,2. **Ce qui ne tient pas** : le rang exact, à ±6 %, et le facteur au
dixième près — il dépend aussi de la convention d'unités, Mio de RSS divisés
par Mo de JSON. Les rangs cités ailleurs dans le dépôt (docstrings, messages
d'assertion) sont donc à lire comme « autour du 370e », jamais comme un seuil.

## L'identité de sortie est prouvée, pas supposée

Un correctif de mémoire qui change le résultat n'est pas un correctif de
mémoire. Chacune des trois lectures a été rejouée avant/après.

| Lecture | Périmètre exact de la preuve | Résultat |
| --- | --- | --- |
| `gouvernement_roster` | **Quatre quarts disjoints** du corpus (121 + 120 + 120 + 120 = 481, méthode #628, la version d'avant ne tenant pas en entier sous plafond) × les **10** gouvernements de `raw_data/gouvernements_reels.json` : `membres[]`, `premier_ministre`, warnings, index `acteurRef → membre_id`, `sources[]` dédoublonnées. 127 entrées `membres[]`, 3 premiers ministres résolus, 215 sources au total | **identiques** sur les quatre quarts |
| `audit_pivot_dataset` | Les mêmes quatre quarts, **rapport complet** de `build_report` (les quinze indicateurs), avec l'index des scrutins et celui des amendements chargés des deux côtés, `reference_date` figée | **identiques** sur les quatre quarts |
| `group_profile` | Les **5 fiches AN publiées** (LFI 76, REN 193, RN 90, LR 62, SOC 31 profils), fiche complète hors `meta.genere_le` **et** rapport interne d'écarts de cohésion | **identiques** sur les cinq |

Les trois rejeux ont été refaits à l'identique le 31/08/2026, sur le même
corpus committé : quatre quarts × 10 gouvernements (127 entrées `membres[]`,
3 premiers ministres, 215 sources), quatre quarts × le rapport complet de
`build_report`, et les cinq fiches AN avec leur rapport interne — **identiques
octet pour octet** à chaque fois.

Les deux fiches `groupe-Senat-*` sont hors de cette preuve : leur extraction est
suspendue ([[extraction-groupe-suspendue-516]]) et 1 de leurs 20 membres a un
profil publié. Elles ne sont pas régénérées, donc rien de ce lot ne les touche.

## Le plafond est dans un test, et il est déduit d'une règle

Trois tests, un par module, sur le patron de #628 et pour la même raison : sans
test, la propriété repasserait au prochain ajout et on ne l'apprendrait qu'en
relançant l'outil, sur une machine chargée, le jour où on en a besoin.

La règle est la même pour les trois : **la croissance mémoire doit rester sous
le poids en octets, sur disque, de ce que la lecture lit et ne doit pas
garder.** Le raisonnement tient en une ligne — la désérialisation JSON ne
réduit jamais ; si la lecture croît de moins que le texte qu'elle a lu, elle ne
peut pas le détenir. Ce n'est jamais un plafond relevé sur une exécution puis
arrondi, qui suivrait la dérive qu'il doit signaler.

| Test | Ce que le plafond compte | Rejoué sur la version d'avant |
| --- | --- | --- |
| `test_le_pic_memoire_du_chargement_reste_sous_le_plafond_declare` | `amendements` + `votes` + `interventions` des 24 profils-fixtures (63,8 Mio) | **295,3 Mio** — échoue, facteur **4,6** |
| `test_le_pic_memoire_de_l_audit_reste_sous_le_plafond_declare` | les mêmes entrées (64,0 Mio) | **307,2 Mio** — échoue, facteur **4,8** |
| `test_le_pic_memoire_d_une_fiche_de_groupe_reste_sous_le_plafond_declare` | les seuls `amendements` (52,5 Mio), les listes gardées étant volontairement minuscules | **184,4 Mio** — échoue, facteur **3,5** |

Après correction, les trois mesurent **0,0 Mio** de croissance : le pic de la
lecture ne dépasse pas celui de ses propres imports.

Chacun porte un `PLANCHER_POIDS_RELACHE` de 40 Mio, qui refuse le verdict si
quelqu'un rétrécit les fixtures jusqu'à ce que le plafond qu'elles déduisent ne
prouve plus rien. Les entrées des fixtures sont **petites** — un mapping à deux
clés, la forme réelle depuis #431 et #432 — parce que c'est cette forme-là qui
gonfle d'un facteur 4 ; une fixture bâtie sur de longues chaînes ne gonflerait
que d'environ × 1,5 et ne séparerait plus rien.

Chaque module porte en plus un test de **propriété** (« que retient la
projection »), qui ne dépend d'aucune machine : c'est lui qui verrouille
l'invariant, le plafond ne faisant que confirmer qu'il a l'effet annoncé.

## Ce que ces tests ne prouvent pas

- **Ni la vitesse, ni le pic absolu sur le corpus réel.** La CI ne télécharge
  pas `pivot_data` (#473, liste blanche du sparse-checkout de `tests.yml`) : les
  plafonds portent sur des fixtures. Ce qu'ils certifient est la **propriété** —
  aucun document n'est conservé —, qui ne dépend pas de l'échelle : un chargeur
  qui range les documents entiers les range à toutes les tailles.
- **Ni le coût des index partagés.** Le pic de l'audit après correction, 539 Mio,
  est à **517 Mio** l'index des amendements lui-même (116 Mo de JSON hors
  cosignatures, chargé en entier par `amendements_index.charger`). #635 ne le
  touche pas, et aucun test ne le borne. C'est aujourd'hui le premier poste de
  mémoire des trois chemins corrigés.
- **Ni les autres lectures du dépôt.** Le balayage de #628 en avait nommé trois,
  celles-ci ; il n'a pas été refait après ce lot.
- **Ni le cas d'un appelant incohérent** de `load_pivot_directory` ou de
  `load_profil_from_file` qui passerait un index au chargement et un autre à
  l'agrégat. Le contrat est écrit dans les deux docstrings ; rien ne le vérifie
  à l'exécution.

## Deux changements de comportement, petits et déclarés

- `load_profils_from_dir` traite désormais une **racine JSON non-objet** comme
  un fichier illisible (message sur stderr) au lieu de l'ajouter à la liste. Un
  tel document faisait lever un `AttributeError` au premier `profil.get(...)` ;
  il n'y en a aucun dans le corpus committé.
- Dans les CLI de `audit_pivot_dataset.py` et `group_profile.py`, les index
  partagés sont chargés **avant** les profils : les lignes de progression de
  `stderr` changent d'ordre. Aucune sortie de données n'en dépend.

## Alternatives écartées

- **Projeter `amendements[]` par clés** plutôt que le réduire. Mesuré :
  184 octets de `dict` par entrée quelle que soit la clé conservée, soit 1,6 Gio
  pour les 6,09 millions d'entrées du corpus contre 1,9 sans projection — 19 %
  de gain pour le même défaut.
- **Réduire au cardinal les listes réellement parcourues.** Ce serait supprimer
  une mesure publiée : la plage de dates de l'audit est précisément celle qui
  avait montré que le corpus s'arrêtait en juin 2024 ([[votes-multi-legislature]]).
- **Un parseur JSON incrémental** (`ijson`) pour ne désérialiser que les blocs
  utiles. Une dépendance de plus pour un gain que la projection obtient déjà,
  et déjà écartée par #628. Le `json.loads` complet reste nécessaire — un profil
  est écrit compact, sur une seule ligne (#433) ; ce qui change est la **durée
  de vie** du document, locale à la fonction de lecture.
- **Réécrire les quinze `compute_*` de l'audit en accumulateurs** pour streamer
  le corpus. C'est la forme la plus économe, et la plus risquée : quinze mesures
  publiées réécrites d'un coup, sans que la réduction n'apporte moins. Elle
  reste disponible le jour où une mesure demandera autre chose qu'un cardinal et
  une plage.
