<a id="telechargement-an-trois-modes-defaillance"></a>
# Régénérer l'existant : `--refresh-existing`, l'inverse de `--skip-existing` (#445) (2026-08-19)

`2026-08-19`

> **En bref** — `--refresh-existing`, l'inverse de `--skip-existing` : régénérer l'existant sans sauter les profils à corriger.

Une correction de fond — la clé `uid` de #440 — ne concerne que les profils
**déjà écrits**. Le job `extract-roster-groupes` posait `--skip-existing` en
dur, et ce flag s'applique **avant** `--no-merge` : un run
`overwrite_profiles=true` sautait donc exactement les profils à corriger. Les
205 profils de roster écrits sur la clé écrasée étaient inatteignables par
toute combinaison d'inputs.

Deux issues supposées, toutes deux fausses à la vérification :

**« Le passage à pleine échelle refermerait le problème de lui-même. »** Non :
sans `--limit`, la condition `args.limit is not None` court-circuite le chemin
de rafraîchissement de #224 (`_select_candidats_couverture`), et
`--skip-existing` saute alors *chaque* profil existant. Un run à
`roster_extraction_limit=0` n'aurait rien corrigé — il aurait seulement étendu
la frontière de conquête de 205 à 752.

**« Lever `--skip-existing` suffit. »** Non plus : avec `--limit`, la sélection
retombe sur les N premiers du shard, et les profils couverts ne forment pas un
préfixe. Mesuré au 19/08/2026, sur les 8 shards de 94 membres :

| shard | couverts | index du dernier couvert |
| --- | --- | --- |
| 3 | 24 | 61 |
| 0 | 24 | 78 |
| 6 | 28 | **93** |
| 7 | 27 | **93** |

La cause est que **l'ordre de `raw_data/roster_candidats.json` n'est pas stable
dans le temps** : le fichier est régénéré par `generate_roster_candidats.py`.
Aucune borne positionnelle ne peut donc désigner les couverts. Le `--limit`
minimal qui les couvrirait tous vaut 94 — le roster entier, avec 547 profils
neufs en prime, c'est-à-dire trancher le dimensionnement de #429 par accident
plutôt que par décision.

## La décision

`--refresh-existing` : sélection strictement inverse de `--skip-existing`, ne
retenant que les candidats dont le profil JSON existe déjà. Appliqué **après**
`--shard` (chaque shard régénère sa tranche) et **avant** `--limit` (qui peut
encore borner un lot d'essai). Exposé par l'input `roster_refresh_existing`.

La combinaison avec `--skip-existing` est **refusée** (`SystemExit`) plutôt que
tolérée : les deux flags s'annulent exactement, et un job qui les recevrait
tournerait huit minutes sans écrire un seul profil, sans erreur — le genre de
panne muette que ce dépôt traite comme un défaut à part entière (cf. §*index
amendements figé au format hérité*).

`roster_refresh_existing` sans `overwrite_profiles` émet un `::warning::` : la
fusion additive conserverait les entrées de l'ancienne clé **à côté** des
corrigées, résultat pire que l'inaction, et indistinguable à l'usage.

## Ce qui a été vérifié avant de conclure

Les 4 slugs présents à la fois dans le roster et dans `candidats.json`
(`gabriel-attal`, `marine-le-pen`, `bruno-retailleau`, `jerome-guedj`) ne
perdent pas leurs interventions ni leurs dossiers législatifs malgré le mode
léger du job roster : `merge-and-pivot` fusionne les artifacts via
`merge_raw_dirs`, additif slug par slug, et non par écrasement de fichier.

`--skip-existing` reste le **défaut** : le déploiement progressif de #224 en
dépend, et le supprimer ferait repayer le réseau pour chaque profil déjà écrit
à chaque run.

