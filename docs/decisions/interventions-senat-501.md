<a id="interventions-senat-501"></a>
# `extract-senat` ne collecte plus d'interventions : la collecte n'en retenait aucune, par construction (#501) (2026-08-20)

`2026-08-20`

> **En bref** — tout chemin de collecte déclare ce qu'il fait des interventions.

Fait suite à #498/#500, qui a borné la collecte d'interventions d'`extract-an`
par un budget de temps mur. #501 traite le même défaut sur le troisième chemin
de collecte — et arrive à une autre conclusion, parce que la mesure diffère.

## Le défaut : trois jobs, trois comportements, un seul déclaré

Trois jobs lancent `generate_all_profiles.py` sur le réseau. Face au même input
`collect_interventions`, ils faisaient trois choses différentes :

| Job | Interventions | Mécanisme |
| --- | --- | --- |
| `extract-an` | pilotées par l'input | `INTERV_FLAG` |
| `extract-roster-groupes` | jamais | `--skip-interventions` en dur (#357) |
| `extract-senat` | **toujours** | aucun flag, aucune lecture de l'input |

Aucun de ces comportements n'est illégitime. Ce qui l'était, c'est que le
troisième n'était écrit nulle part : la description de l'input annonçait
« Affects extract-an only — the roster job always skips them », soit deux jobs
sur trois. Un opérateur décochant `collect_interventions` obtenait quand même
une collecte sénatoriale complète.

## Deux corrections au diagnostic de l'issue

**1. Le budget de #500 couvre déjà `--source senat`, par construction.**
L'issue le posait en question ouverte. Vérifié sur `b2c34f4` :
`build_profile_any_chambre` instancie le `BudgetCollecte` avant de boucler sur
`chambres`, et `--source senat` passe par exactement le même appel avec
`chambres_fr = ["senateurs"]`. Sur le chemin sénatorial, la section budgétée
« détails d'interventions NosDéputés » est même la seule qui s'exécute : Syceron
et les questions officielles sont gardés par `chambre == "deputes"`. Il ne
manquait donc que le passage du flag CLI par le job — et, la collecte étant
supprimée, il n'y a plus rien à borner.

**2. `extract-senat` n'a jamais été tué par son `timeout-minutes: 90`.** L'issue
décrit un job « tué par son timeout » et un pire cas de 90 min consommées. Les
deux runs les plus longs — `32377092124` (969 s) et `32379928098` (4 482 s) —
se terminent **à la seconde près en même temps qu'`extract-roster-groupes` et
`merge-and-pivot`** : c'est la signature d'une annulation de run. Un
`timeout-minutes: 90` aurait coupé le second à 5 400 s, soit 15 minutes plus
tard. Le constat est plus sévère que celui de l'issue, pas moins : ce plafond
n'a jamais été ce qui arrête ce job.

## La mesure : la collecte sénatoriale retenait zéro, et pas « peu »

`fetch_intervention_details` rattache une intervention à son orateur en lisant
le bloc `div.perso` de la page de séance, dont il tire l'URL depuis la clé
**`url_nosdeputes`** du document. L'API de `archive.nossenateurs.fr` ne publie
jamais cette clé : elle expose **`url_nossenateurs`** (vérifié le 20/08/2026 sur
4 documents — 909543, 843155, 843180, 843226). Sans URL, aucune page n'est
chargée, `speaker_name`/`speaker_url` restent `None`,
`_classify_intervention` rend `mention`, et `_process_search_result` jette le
document. **Toutes les interventions sénatoriales, sans exception.**

Ce que ça donne, population par population :

| Population | Mesure |
| --- | --- |
| 209 profils bruts publiés (`raw_data/profiles/`, `b2c34f4`) | 789 interventions, dont **0** sur un domaine sénatorial (446 `www.nosdeputes.fr`, 293 `questions.assemblee-nationale.fr`, 50 `2017-2022.nosdeputes.fr`) |
| Résumé d'`extract-senat`, 7 runs du 14/08 au 19/08/2026 | « Bruno Retailleau: ok (**0** interventions, senateurs) » — sur les 7, sans exception. C'est le seul sénateur en exercice de `raw_data/candidats.json` |
| Coût payé pour ce zéro, même relevé | jusqu'à **58 pages de recherche et ~2 700 requêtes de détail** par run à `archive.nossenateurs.fr` |

Les 15 interventions que le résumé affiche parfois sur Mélenchon **ne viennent
pas du Sénat** : les 15 URLs pointent sur `questions.assemblee-nationale.fr`,
et `fetch_questions_officielles` est gardé par `chambre == "deputes"`. Elles
sont collectées par le chemin AN et conservées par la fusion additive dans un
profil dont la `chambre` a basculé (#484) — pas collectées par ce job. C'est
exactement le genre de chiffre qui se lit sur la mauvaise population : « 15
interventions sur un profil `Senat` » n'est pas « 15 interventions
sénatoriales ».

## Décision : `--skip-interventions` en dur, comme le job roster

Alignement sur le roster, pas sur l'input — et sur la mesure, pas sur la
symétrie. Obéir à `collect_interventions` (option 1 de l'issue) aurait laissé
un opérateur demander une collecte qui ne peut rien produire : sur les 311
requêtes de l'`extract-senat` du run `32288588518`, **280 (90 %) servaient les
interventions**, pour zéro intervention retenue.

**Effet sur les données publiées : aucun.** `build_profile` rendait déjà `[]`,
et `preserver_collectes_non_vides` (#465) empêche un `[]` d'écraser un fait
acquis, y compris sous `--no-merge`. Le flag supprime des requêtes, pas des
données.

Ce n'est pas la même conclusion que #500 sur le même symptôme, et la raison
tient en une phrase : là-bas la collecte était coûteuse **et** productive, donc
il fallait la borner ; ici elle est coûteuse et stérile, donc il faut la couper.

## Le timeout : 90 → 15 min

Une valeur unique, pas conditionnelle au mode comme `extract-an` : sans
collecte d'interventions, ce job n'a plus deux modes à couvrir.

Dimensionné en suivant la leçon de #498 — `timeout-minutes` borne
`préambule + collecte`, jamais la collecte seule :

- **préambule** : 6 à 170 s sur les 15 derniers runs portant un `extract-senat`
  (14/08 → 20/08/2026) → 240 s provisionnés, comme `extract-an` ;
- **collecte résiduelle** : 4 requêtes par slug résolvable (identité, votes,
  2 législatures de dossiers), soit 32 requêtes pour les 8 slugs de
  `raw_data/candidats.json`. **2,7 s chronométrées** sur `bruno-retailleau` le
  20/08/2026 sur la source saine, ~30 s projetées pour les 8.

15 min laissent donc ~11 min à une collecte mesurée à 30 s. Une source dégradée
coûte au pire 48 s par requête (3 tentatives × `read timeout` 15 s + backoff) :
32 requêtes tenant toutes leur pire cas dépasseraient 15 min, **et c'est voulu**
— une source qui fait expirer ses 32 requêtes est à terre, et attendre 90 min
n'en tirera rien de plus.

Le coût d'une coupure est faible ici, contrairement à `extract-an` : ce job
n'est pas shardé et `_manifest_append` publie candidat par candidat, donc un
timeout ne perd que le candidat en cours. C'est aussi pourquoi aucun
`--budget-interventions-secondes` n'y est posé : sans collecte d'interventions
il n'aurait rien à borner (`build_profile_any_chambre` le neutralise sous
`--skip-interventions`), et la publication incrémentale tient déjà le rôle que
le budget joue sur `extract-an`.

Conséquence sur le plafond de temps mur de l'en-tête du workflow : le Sénat
n'est plus le maillon dimensionnant. La chaîne la plus longue passe par
`extract-an` (30 min d'amendements + 5 min × 8 shards = 70), soit
70 + 60·S + 60 = **190 min à S=1, 610 à S=8** — contre 210 / 630 avant.

## Le garde-fou : un inventaire des chemins de collecte

`tests/test_ci_interventions_par_job.py` énumère **toutes** les invocations de
`generate_all_profiles.py` du workflow et impose que chacune tombe dans
exactement un mode explicite : `--skip-interventions` en dur, un tableau
`INTERV_*` piloté par `inputs.collect_interventions`, `--source ue` (aucune
chambre française, donc aucune intervention possible) ou `--pivot-only` (aucun
appel réseau). L'inventaire des six invocations actuelles est écrit dans le
test : en ajouter une septième sans se prononcer sur les interventions le fait
échouer.

Le test impose aussi que **tout job qui ignore l'input soit nommé dans la
description de cet input** — c'est le lien qui manquait, celui qui a laissé la
description parler de deux jobs sur trois pendant des mois.

Vérifié par mutation, comme l'exige la leçon de #460 (un garde-fou débranché
est pire qu'aucun) : retirer le flag, remonter le timeout à 90, retirer le
Sénat de la description ou ajouter une invocation muette font chacun échouer le
fichier.

## Alternatives écartées

**Aligner sur l'input** (option 1 de l'issue). Cohérente et minimale, mais elle
laisse cochable une collecte dont la mesure dit qu'elle ne peut rien rendre.
Un réglage qui ne produit rien quand on l'active est une valeur par défaut
silencieuse d'un autre genre.

**Laisser tel quel et documenter** (option 3). Écartée par le coût : ~2 700
requêtes par run à une archive publique, pour zéro donnée, n'est pas défendable
même bien documenté — et le projet refuse par ailleurs de malmener ses sources
(temporisation de courtoisie de #467).

**Réparer `fetch_intervention_details` pour lire `url_nossenateurs`.** C'est la
vraie correction, et elle est hors du périmètre de cette issue : elle
ouvrirait la collecte de centaines de documents par candidat dont
l'attribution d'orateur n'est pas vérifiée (le HTML de
`archive.nossenateurs.fr` n'a jamais été confronté à
`_extract_speaker_identity_from_html`), sur un travail sénatorial qu'aucun
agrégat ne consomme aujourd'hui — voir § *Senate votes, amendments, sponsored
texts* et #488. Consigné dans `ROADMAP.md`.
`tests/test_interventions_senat_non_retenues.py` fixait l'asymétrie plutôt que le
zéro. **Ce fichier a été supprimé le 27/08/2026** avec la chaîne qu'il mesurait :
`fetch_intervention_details` n'existe plus, le repli NosDéputés ayant été retiré
du chemin interventions ([#syceron-actif-510](syceron-actif-510.md)). La condition
de réouverture n'en est pas affaiblie mais durcie : il ne s'agirait plus de faire
lire `url_nossenateurs` à un lecteur existant, mais de construire un chemin
d'interventions sénatoriales qui n'existe plus du tout.

