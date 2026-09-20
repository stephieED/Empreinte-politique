# Le run : `generate-data.yml` et sa relance

Ce que fait un **run** — les jobs, leur ordre, les caches, les artifacts, le
formulaire de lancement, le push, et la relance automatique. Ce que devient la
**donnée** est décrit ailleurs : `docs/data-architecture.md`. Les
**règles** que ces mécanismes imposent restent dans `AGENTS.md` §3 ; le
**pourquoi** de chacune est un fichier de `docs/decisions/`.

Ce fichier existe pour être lu **avant** d'ouvrir
`.github/workflows/generate-data.yml`, qui fait plus de 4 000 lignes.

## 1. Les jobs, dans l'ordre

| Job | `needs:` | Consomme | Produit |
|---|---|---|---|
| `rafraichir-candidats` | — | l'article Wikipédia des candidatures, Wikidata (`P4123`) | `raw_data/candidats.json` à jour + `raw_data/resolutions_candidats.json` → artifact `candidats-a-jour` (#757) |
| `prepare-an-matrix` | `rafraichir-candidats` | l'artifact `candidats-a-jour`, à défaut `raw_data/candidats.json` | la matrice `extract-an` (un shard par candidat à slug résolvable, #344) |
| `extract-amendements-an` | — | AN open data (dumps amendements) | artifact `amendements-index-an` + cache `public-data-cache-amendements-<semaine>` |
| `extract-ue-officiel` | — | Europarl Open Data | artifact `raw-profiles-ue-officiel`, cache `public-data-cache-ue-<semaine>` |
| `extract-parltrack` | — | 5 dumps ParlTrack (232 Mio) | artifact `parltrack-dumps`, cache `public-data-cache-parltrack-<semaine>` |
| `prepare-roster-matrix` | — | `raw_data/groupes_reels.json`, l'archive AMO30 | `raw_data/roster_candidats.json` → artifact `roster-candidats`, la matrice roster, et `rosters_bruts.json` — qui porte depuis #996 une clé `gouvernements:`, les membres des 17 gouvernements lus dans AMO30 (`gouvernement_roster_an.py`). **Depuis #996 lot 3 ces membres entrent aussi dans `roster_candidats.json`**, sous `statut: "roster_gouvernement"`, donc les shards les collectent ; les slugs déjà portés par un roster de groupe ne sont pas repris, et restent `roster_groupe`. La passe tourne **après** le portail d'anomalies et **avant** l'écriture des deux fichiers ; `--sans-gouvernements` la débranche, et son échec est non fatal |
| `extract-an` | `extract-amendements-an`, `prepare-an-matrix` | AN open data, Syceron, l'index amendements | un artifact `raw-profiles-an-<slug>` par shard, cache `public-data-cache-an-<semaine>[-interv-<empreinte>]` |
| `extract-roster-groupes` | les quatre `extract-*` + `prepare-roster-matrix` | l'artifact `roster-candidats`, les mêmes sources | un artifact `raw-profiles-roster-groupes-<shard>` par shard |
| `extract-senat` | — | `export_sens.zip` de `data.senat.fr` (#885) | artifact `raw-profiles-senat`, cache `public-data-cache-senat-<date>` |
| `extract-mandats-locaux` | — | le Répertoire national des élus et les sortants 2026, par `tabular-api.data.gouv.fr` (#922) | artifact `raw-profiles-mandats-locaux`, **aucun cache** |
| `merge-and-pivot` | `extract-an`, `extract-ue-officiel`, `extract-parltrack`, `extract-roster-groupes`, `extract-senat` | tous les artifacts ci-dessus, et les **quatre archives de dossiers** (XIV à XVII, deux formats depuis #1019) | le contrôle du transport, la fusion, les deux passes pivot, les fiches de groupe, de lignée et **de gouvernement** (rattachement par `organe_ref`, #996 lot 4), les quatre contrôles, le commit et le push |

Sept jobs n'ont aucun `needs:` et démarrent ensemble (`rafraichir-candidats` en
fait partie depuis #757, `extract-senat` depuis #885, `extract-mandats-locaux`
depuis #922 ; `prepare-an-matrix` attend le premier). Le **chemin critique réel,
ce sont les deux matrices en série** (`extract-an` en `max-parallel: 1`, puis la
matrice roster en `max-parallel: 4`), pas le nombre de jobs.

`extract-an`, `extract-ue-officiel`, `extract-parltrack`,
`extract-amendements-an`, `extract-roster-groupes`, `extract-senat` et
`extract-mandats-locaux` portent
`continue-on-error: true` : leur échec ne bloque pas `merge-and-pivot`, qui
fusionne ce qui a réussi. Les deux jobs avals portent en plus
`if: ${{ !cancelled() }}` — `continue-on-error` transforme un *échec* en
non-bloquant mais ne fait rien contre un maillon amont *skipped* (#412 §2.1).
`prepare-roster-matrix` n'en porte pas et ne doit pas en recevoir : sa sortie
dimensionne la matrice.

### Ce que fait chaque job, et pourquoi comme ça

Ce qu'un job **déclare**, le YAML le dit, et il le dit mieux. Ce qui suit est ce
qu'on ne relira pas dans le YAML dans un an : ce que le job fait, ce qu'il
touche, et les deux ou trois décisions qui expliquent sa forme. Le reste du
« pourquoi » vit dans `docs/decisions/` — chaque job y a des dizaines de
fichiers, et ceux cités ici sont les structurants, pas la liste.

#### `rafraichir-candidats`

Le job qui **décide du périmètre du run** (#757). Il lit l'article Wikipédia des
candidatures, en tire les candidats déclarés, résout l'acteur AN de chacun par
identifiant externe (Wikidata `P4123`), fabrique le slug quand la chaîne aboutit,
et écrit `raw_data/candidats.json` **et** `raw_data/resolutions_candidats.json`.

**Le réseau est ici et nulle part ailleurs.** La passe qui écrit les entrées de
correspondance tourne dans `merge-and-pivot` et reste **hors ligne** : une panne
de source tierce ne doit pas coûter le commit d'un run dont la donnée est bonne
(#524, c'est la forme que #715 s'est donnée).

**Il ne pousse rien.** `merge-and-pivot` annule le commit si `raw_data/*.json` a
bougé sur la branche *pendant* le run (`GENERATION_CODE_CHANGED_DURING_RUN`,
#390/#413) : le fichier voyage donc dans l'artifact et il est committé à la fin,
avec les données qu'il a produites.

**Consomme** `fr.wikipedia.org` et `query.wikidata.org`. **Produit** l'artifact
`candidats-a-jour` (les deux fichiers ensemble — séparés, un run collecterait
d'après l'un sans pouvoir écrire les correspondances de l'autre).

**Ni `continue-on-error`, ni `if:`** : le repli est **explicite, dans le shell**.
Sur un code 1 — collecte incomplète, rien écrit — le run garde la liste
**committée**, qui est un état connu, et l'annonce en `::warning::`. Jamais une
liste vide (AGENTS.md §2 règle 5, le patron de #511).

**Pourquoi comme ça** : la liste était tenue à la main et avait **51 jours** de
retard pour **19 déclarés absents** au 07/09/2026 ; d'ici avril 2027 elle bougera
des dizaines de fois, et un périmètre qui n'avance que lorsqu'une main y pense
est un périmètre en retard
([la boucle du périmètre](decisions/boucle-perimetre-candidats-757.md)). La forme
— une construction par run, publiée en artifact — est celle de
`prepare-roster-matrix`, et pour la raison de
[un roster par run](decisions/roster-unique-par-run-518.md) : deux lectures de la
même liste à deux moments d'un run divergent, et un candidat collecté par l'une
sans être normalisé par l'autre ne fait échouer aucune étape.

#### `prepare-an-matrix`

Lit `raw_data/candidats.json`, en tire la liste des slugs résolvables et la
publie comme matrice d'`extract-an` — **un shard par candidat du périmètre**. Il
ne collecte rien. Le périmètre vient de `src/perimetre_candidats.py`, partagé
avec `generate_all_profiles` : un candidat à `statut: decline` **n'a pas de
shard**, sa fiche restant publiée telle quelle, et il est **nommé**
(`::notice::CANDIDAT_GELE`) là où le périmètre est calculé (#760). Il porte aussi deux garde-fous de lancement : un avertissement au-delà de
16 shards (ils s'exécutent en série, donc 16 shards = 16 fois le timeout d'un
shard), et le décompte chiffré des interventions qu'un run
`existing_profiles=overwrite` sans `collect_interventions` effacerait.

**Son checkout porte une liste blanche (#674).** Il ne lit que
`raw_data/candidats.json`, et son `timeout-minutes: 5` ne survit pas au
checkout complet : le run `33414042623` l'a vu tué à 5 min 00, donc matrice
jamais publiée, donc `extract-an` **skippé** alors qu'il venait d'être réparé.
La règle vaut pour tout job au budget serré, et un test la fait respecter.

**Consomme** l'artifact `candidats-a-jour`, et à défaut le
`raw_data/candidats.json` de son checkout — un artifact absent est **nommé**
(`CANDIDATS_ARTIFACT_ABSENT`), jamais avalé. **Produit** la sortie `slugs`.
**Pas de `continue-on-error`** : un `candidats.json` illisible doit échouer
*ici*, lisiblement. Il porte en revanche un `if: !cancelled()` depuis #757, pour
tourner même quand `rafraichir-candidats` a échoué : le périmètre d'hier vaut
mieux qu'un run sans aucun candidat. Une matrice vide fait *skipper* `extract-an`, et un
job sauté n'est pas un job en échec — `continue-on-error` ne le rattrape pas.

**Pourquoi comme ça** : un runner GitHub peut recevoir un `shutdown signal`
d'infrastructure qui gèle le job entier, steps `if: always()` compris
([résilience au `shutdown signal`](decisions/resilience-generate-data-shutdown-signal.md)) ;
un job séquentiel unique aurait alors perdu la progression de tous les candidats
déjà traités, tandis que le sharding par candidat borne la perte à un seul
([une matrice par candidat](decisions/matrix-extract-an-par-candidat.md)).

#### `extract-amendements-an`

Construit l'index amendements AN **par acteur**, sans condition et
indépendamment de toute liste de candidats :
`python3 src/build_amendements_index.py` sur les législatures
d'`AN_AMENDEMENTS_PATH` (17, 16, 15, 14). Une législature dont l'index est
**figé** — 14, 15 et 16, committés gzippés sous
`raw_data/amendements_an_figes/` — est sautée sans être rechargée : en pratique
la CI ne télécharge que la 17e. Un échec est isolé par législature ; le script
sort en 1 si l'une a échoué, et c'est le `continue-on-error` du job, pas le
script, qui empêche cela de bloquer le run.

**Le job passe `--reconstruire-actives` quand la clé de cache exacte de la
semaine n'a pas été touchée** (`steps.cache_amendements.outputs.cache-hit !=
'true'`, vrai sur un `restore-keys` comme sur un cache absent) : le cache des
législatures **non figées** est alors purgé, ce qui force leur reconstruction —
une par semaine ISO. Sans ce drapeau, le repli par préfixe restaurait la semaine
précédente, le cache n'était jamais absent, et la 17e n'était plus reconstruite
**du tout** : 18 jours mesurés, signalés à chaque run par la §3d du gate
([fraîcheur de l'index](decisions/fraicheur-index-amendements-749.md)). Le log
du step dit lequel des deux a eu lieu — construit, ou servi par le cache.

**Consomme** les archives amendements de l'open data AN. **Produit**
`.cache/amendements_an/` → artifact `amendements-index-an`, et écrit la clé de
cache `public-data-cache-amendements-<semaine>` (§3).

**Pourquoi comme ça** : la construction paresseuse, au niveau candidat, faisait
télécharger 350 à 650 Mo à l'intérieur d'un shard de 5 minutes, à chaque shard
([un job dédié](decisions/amendements-index-job-dedie-ci.md)) ; ses consommateurs
lisent donc `.cache/amendements_an/` en **cache-only** et ne téléchargent plus
jamais, une législature absente produisant un `meta.warnings` et non un
téléchargement
([consommateurs cache-only](decisions/amendements-index-cache-only-consumers.md)) ;
et un dossier législatif clos ne se re-télécharge pas
([législatures figées](decisions/amendements-legislatures-figees.md)).

#### `extract-ue-officiel`

`python3 src/generate_all_profiles.py --source ue --workers 1` : Open Data
Portal du Parlement européen **uniquement**, aucune source française. Écrit les
profils bruts des candidats dont le MEP ID est résolu, et ne publie que ceux
qu'il a **effectivement écrits** (manifeste + `publish-written-profiles`, §4).

**Consomme** l'Open Data Portal EP. **Produit** l'artifact
`raw-profiles-ue-officiel`, et écrit `public-data-cache-ue-<semaine>` sur
`.cache/europarl` **seul** — cacher `.cache` en bloc lui faisait ré-embarquer
les données AN et amendements, et le quota de cache du dépôt étant partagé,
l'entrée surdimensionnée provoquait l'éviction LRU des autres (#424).

**Pourquoi comme ça** : l'API officielle EP ne permet pas d'attribuer rapports
et amendements à un député européen donné — pas de filtre auteur, ~10-15k
documents sans titre dans la réponse de liste, 1 h 30 et plus de scan par run à
la limite de débit ([périmètre écarté](decisions/hors-perimetre.md)). C'est
l'[investigation des sources UE](decisions/investigation-sources-ue.md) qui a
tranché pour les dumps ParlTrack, d'où le job suivant.

#### `extract-parltrack`

Restaure `.cache/parltrack`, puis télécharge **cinq** dumps `.zst` via
`ensure_dump()` de `src/parltrack_dumps.py`. La liste n'est pas dans le YAML :
il itère sur `DUMPS_LUS`, la seule définition, parce qu'une liste recopiée
aurait divergé du jour où le module lit un dump de plus — et un dump absent ne
fait pas échouer la lecture, il rend un index vide (#683, #510).

| Dump | Ce qu'il porte | Poids |
| --- | --- | ---: |
| `ep_dossiers` | dossiers législatifs, rapporteurs | 53 Mio |
| `ep_amendments` | amendements en commission | 114 Mio |
| `ep_plenary_amendments` | amendements en séance | 7 Mio |
| `ep_votes` | 44 648 scrutins nominatifs, 2004 → 26/03/2026 | 11 Mio |
| `ep_mep_activities` | interventions, questions, explications de vote, motions | 47 Mio |

**Il n'écrit aucun profil** — il prépare la matière que `merge-and-pivot`
consomme à la passe pivot (`--enrich-parltrack` →
`src/normalize_parltrack_dumps.py`). Depuis le lot 2 de #683, les cinq dumps
alimentent `votes[]`, `amendements[]`, `textes_portes[]` et `interventions[]`
des **7 candidats déclarés à identifiant européen** — les listes que la fiche a
déjà, jamais un bloc parallèle. L'enrichissement a lieu **dans**
`_normaliser_en_pivot`, avant la dérivation de la couverture : un champ dérivé
ne peut pas décrire des listes qui changent après lui.

**Les trois dumps que ParlTrack publie et que ce job ne prend pas**, chacun pour
une raison mesurée : `ep_meps` fait doublon avec `extract-ue-officiel` ;
`ep_com_votes` porte **89 scrutins en tout** ; `ep_comagendas` ne nomme
personne.

**Consomme** `https://parltrack.org/dumps`. **Produit** l'artifact
`parltrack-dumps` — hors de la famille `raw-profiles-*` exprès, puisqu'il ne
contient pas de profils (#412 §4) — et la clé
`public-data-cache-parltrack-<semaine>`.

**Pourquoi comme ça** : source tierce non officielle, donc traitée comme
faillible de bout en bout. Dumps absents ⇒ la passe pivot ajoute un warning de
repli **déclaré** et n'invente rien. **Dump présent mais illisible ⇒ une panne,
pas une absence** : `DumpParltrackIllisible` (#683) est levée quand un dump
porteur de lignes ne rend aucun enregistrement — sans elle, un changement de
format côté ParlTrack rend des listes vides, et une liste vide se publie comme
un constat sur la personne (#484, #510). C'est exactement ce qui a duré un an ; `--parltrack-status-out` écrit le fichier
JSON que `check_quality_gate.py` §5 relit. La licence est ODbL, ce que
`src/licences.py` répercute dans `meta.licence_donnees`
([licences](decisions/licences.md), [lot 6](decisions/licence-lot-6-530.md)).

#### `prepare-roster-matrix`

Construit **une fois pour tout le run** `raw_data/roster_candidats.json` (la
liste roster-driven, filtrée par sigle) *et* `raw_data/rosters_bruts.json` (la
**même** collecte, avant filtrage), publiés dans **un seul** artifact
`roster-candidats` ; puis calcule la liste des 8 shards roster.

**Consomme** `raw_data/groupes_reels.json` — **12 entrées** depuis #700, dont 10
actives : un fetch de roster par couple `(roster_chambre, législature)`
distinct, donc **deux** côté AN (`("deputes", "16")` et `("deputes", "17")`),
lus dans la **même** archive AMO30 déjà en cache — pas de téléchargement
supplémentaire. **Produit** l'artifact `roster-candidats` et les sorties
`shards` / `shard_total`. Un membre de roster **sans slug** n'entre pas dans
`roster_candidats.json` : il est compté et nommé par l'annotation
`ROSTER_SANS_SLUG` (#527). **Depuis #708** il en reçoit un, fabriqué par
`text_utils.slugify` sur l'état civil AMO30 quand
`raw_data/correspondance_acteurs_an.json` ne le couvre pas, la table gardant la
priorité ; `ROSTER_SANS_SLUG` ne nomme plus que les **collisions** non
tranchées, et son miroir `ROSTER_SLUG_FABRIQUE` (`::notice::`) nomme qui entre
sans correspondance relue. Les 156 des 5 groupes de la XVIIe entrent donc — un
run produira ~1,07 à 1,44 Gio de profils bruts neufs, et la §5b du portail
bloquera leur **publication** tant que leur entrée n'est pas relue. Le filtrage se fait
**sur le code de sortie, dans le shell** : seul le code 2 (« extraction de tous
les groupes suspendue ») est toléré, le code 1 (collecte incomplète) ne l'est
pas — un `continue-on-error: true` avalerait les deux.

**Pourquoi comme ça** : neuf constructions indépendantes du même roster étaient
fragiles et **incorrectes** — les shards se partagent le roster par position,
`merge-and-pivot` normalise **sa** liste, et deux listes divergentes produisent
un « collecté mais non publié » sans qu'aucune étape n'échoue
([un roster par run](decisions/roster-unique-par-run-518.md)) ; le roster brut
voyage dans le même artifact parce que la fiche de groupe était sinon bâtie sur
une composition lue ~7 min après celle qui avait servi à collecter les profils
([plafond roster et commit](decisions/plafond-roster-et-commit-518.md)) ; et un
code de sortie qui distingue « panne » de « rien à collecter » est ce qui permet
au run de conclure vert quand la source est délibérément suspendue
([cloisonnement de la branche roster](decisions/cloisonnement-branche-roster-524.md)).

#### `extract-an`

Un shard par candidat, séquencés un par un (`max-parallel: 1`) :

```
python3 src/generate_all_profiles.py --source an --only <slug> \
  --budget-collecte-secondes 0 --manifest-out _manifest/profils-ecrits.txt \
  [--no-merge] [--skip-interventions] [--budget-interventions-secondes 250]
```

`--source an` force une collecte **Assemblée nationale uniquement**. Un candidat
sans slug est un no-op dans ce scope et n'a donc pas de shard. La chaîne, dans
`src/candidate_profile.py::build_profile(chambre="deputes")` : identité et
mandats depuis le référentiel AMO30 (étape 0, résolue en tout premier),
positions dans l'hémicycle depuis les dumps acteurs historiques, votes depuis
les scrutins nominatifs (législatures 17/16/15/14), amendements lus **en
cache-only** dans `.cache/amendements_an/`, textes portés depuis les dossiers
législatifs (rôle factuel auteur / rapporteur / co-rapporteur), interventions
depuis les comptes rendus Syceron (15/16/17) puis les questions QE/QG/QOSD.
Les URL de jeux de données et les schémas JSON de chacune de ces archives sont
dans [`an-opendata.md`](./sources/an-opendata.md) — référence de la source, qui dérive
avec l'Assemblée et non avec notre code.

**Budget réseau des scrutins, revenu à la normale (#639).** Les trois index
figés committés de `raw_data/scrutins_an_figes/{14,15,16}` ont été reconstruits
le 31/08/2026 et **portent la qualification** : `_load_frozen_scrutins_index` ne
les refuse plus, et les 20,0 Mo d'archives ne sont plus retéléchargés. Relevé le
31/08/2026 — 14 : 1 354 scrutins (`public_ordinaire` 1 213, `solennel` 128,
`tribune` 9, **`motion_censure` 4**) ; 15 : 4 417 (4 288 · 124 · **5**) ; 16 :
4 105 (4 034 · 37 · **34**). Un cache `.cache/scrutins_an` écrit avant #639 reste
refusé, lui, et la première exécution le reconstruit — existence n'est pas
conformité, la règle d'`AGENTS.md` §5.

**Un shard ne matérialise que son propre profil (#674).** Le checkout de ce job
porte une **liste blanche** et `filter: blob:none` : le code, les référentiels de
premier niveau, les index figés, et le seul `raw_data/profiles/<slug>` du shard —
socle et tranches (#580). Le run `33404236969` avait tué ses 13 shards à
5 min 00 **dans `actions/checkout`**, l'étape d'extraction restant `skipped` :
aucun profil écrit, le défaut de #498. L'arbre pesait alors 8 483 Mio, dont
**7 525 pour le seul `raw_data/profiles/`**, quand le plus gros candidat en pèse
16,4. Le `timeout-minutes: 5` n'a **pas** été relevé — le lot supprime la cause.
**Tout nouveau chemin lu par la collecte AN doit entrer dans cette liste** :
oublié, il ne fait pas échouer le checkout, il rend un fichier absent et la
collecte se replie en silence. `tests/test_ci_sparse_checkout_extract_an.py`
échoue localement sur un littéral non couvert, et une étape « Périmètre du
checkout » imprime le poids matérialisé.

**L'AN est source unique, et il n'y a plus aucun repli.** Un slug que le
référentiel AN ne résout pas sort avec `identite: None` et un
`WARNING_PREFIX_IDENTITE_INTROUVABLE` nommant la seule source consultée : il ne
bascule sur rien. Le couple slug ↔ acteur `PA######` est résolu par la table
committée `raw_data/correspondance_acteurs_an.json`, et §5b du garde-fou qualité
échoue déjà sur tout slug publié qui n'y a pas d'entrée.

**Consomme** la matrice de `prepare-an-matrix`, l'open data AN (acteurs actifs et
historiques, scrutins nominatifs, dossiers législatifs, questions, Syceron) et
l'index amendements téléchargé depuis l'artifact `amendements-index-an` — à
défaut, `actions/cache/restore` sur la clé amendements, jamais de sauvegarde,
puisque ce job ne produit pas d'amendements. **Produit** un artifact
`raw-profiles-an-<slug>` par shard, et écrit les clés
`public-data-cache-an-<semaine>[-interv-<empreinte>]` et
`public-data-cache-dossiers-<semaine>`.

**Un profil brut n'est plus un fichier** : `<slug>.json` est le **socle** (le
profil sauf `amendements`), les amendements vivant en tranches sous
`raw_data/profiles/<slug>/<legislature>.json`. L'artifact transporte les deux, et
la relecture passe par `src/profil_brut.py`, jamais par un `json.load` direct
([partition par législature](decisions/partition-profils-legislature-580.md)).

**Pourquoi comme ça** :
[NosDéputés est sorti du pipeline](decisions/retrait-nosdeputes-529.md) — le
profil brut vient entièrement de l'open data AN, et un compteur structurellement
à zéro laissé sous surveillance est un trou muet ;
[Syceron est la seule source de débats](decisions/syceron-actif-510.md) — le
drapeau a été *retiré*, pas baissé, et une collecte vide reste vide en le
déclarant ; [le budget d'interventions](decisions/budget-collecte-interventions.md)
et `timeout-minutes` bougent ensemble, un shard tué par le timeout n'écrivant
**aucun** profil là où un budget épuisé écrit le profil partiel et déclare la
troncature ; et [l'identité AN est primaire](decisions/bascule-identite-an-primaire.md),
adossée à la table [slug ↔ acteur AN](decisions/correspondance-acteurs-an-525.md).

#### `extract-roster-groupes`

La même chaîne de collecte qu'`extract-an`, mais pilotée par la **composition
réelle** des groupes parlementaires (~750 membres) plutôt que par la liste
éditoriale `raw_data/candidats.json` (**32 entrées, dont 13 à slug résolvable**
depuis #753 — seules celles-là ont un shard), et en **mode léger**. Les deux
axes de ce mode léger sont désormais sous le formulaire, et plus rien n'y est
écarté en dur : les interventions suivent `collect_interventions` **depuis
#657**, sous une forme réduite — `--interventions-theme-seul` collecte les
débats Syceron sans leur verbatim et laisse les questions officielles —, et les
dossiers législatifs suivent `collect_dossiers_legislatifs` **depuis #817**.
Les deux étaient posés en dur au même motif, « aucun agrégat de groupe ne les
consomme », faux dans les deux cas. 8 shards découpés par modulo,
`max-parallel: 4`.

**Consomme** l'artifact `roster-candidats` — régénéré seulement s'il manque — et
les mêmes sources qu'`extract-an`, dont les caches AN et amendements en
**restauration seule**. **Produit** un artifact
`raw-profiles-roster-groupes-<shard>` par shard, tous en
`meta.provenance = "roster_groupe"`, une provenance qui ne rétrograde jamais un
profil `candidat_declare` existant à la fusion
([provenance pivot](decisions/provenance-pivot.md)).

**Pourquoi comme ça** : un membre de roster n'alimente que des agrégats de
groupe, qui ne consomment ni dossiers législatifs ni questions officielles
([mode d'extraction léger](decisions/mode-extraction-leger-roster.md)) — mais
**ils consomment bien les interventions**, dont `tags_thematiques` dérive
intégralement, et l'affirmation inverse a laissé l'« empreinte thématique » de
chaque fiche de groupe être celle d'une seule personne
([collecte réduite au thème](decisions/collecte-interventions-reduite-au-theme-657.md)) ;
la
composition vient d'AMO30 et non plus d'un endpoint tiers, `AN_ROSTER_ACTIF`
étant un interrupteur et non un aiguillage
([bascule vers AMO30](decisions/bascule-roster-an-amo30-527.md)) ; et le
découpage en 8 tranches arbitre entre la borne de perte sur préemption et les
frais fixes de `actions/checkout`, pas le temps de calcul
([shardage en 8 tranches](decisions/shardage-extract-roster-groupes.md)).

**Ce job a de la profondeur** — rollout, régénération de l'existant, les six
combinaisons des deux axes du formulaire, les trois codes de sortie du roster :
→ [`extract-roster-groupes.md`](./extract-roster-groupes.md)

#### `merge-and-pivot`

**Le seul job qui écrit dans le dépôt.** Il enchaîne, dans cet ordre : **le contrôle du transport des artifacts** (`verifier_transport_artifacts.py`, #786 — un artifact que le run a publié et qui n'est pas sur le disque est rattrapé par `gh run download`, puis bloque ; une source qui n'a rien publié reste silencieuse, et un inventaire illisible n'échoue pas) ; fusion
additive des profils bruts des trois familles d'artifacts
(`src/merge_profile.py --dirs _artifacts/an _artifacts/ue _artifacts/roster`) —
c'est **elle** qui reconduit le marquage des tranches closes que les shards ont
posé (#691), en lisant l'acteur dans les socles **sources** et jamais dans celui
de la destination, et elle dit ce qu'elle en a fait :

```
· tranches d'amendements : 854 dérivée(s) de l'archive, 509 en fichier, 854 fichier(s) retiré(s) ce run.
```

La ligne n'apparaît **que** s'il y a quelque chose à dire, et le compte de
retraits est **mesuré** (socle relu avant et après écriture), jamais déduit du
nombre de dérivées : un profil déjà basculé au run précédent ne supprime plus
rien. C'est la seule trace observable de la bascule dans un run de test, qui ne
committe pas ;
**première** passe `--pivot-only` sur `raw_data/candidats.json`, avec
`--enrich-parltrack` ; **seconde** passe `--pivot-only` sur le
`roster_candidats.json` du run ; profils de parti ; **la table des commissions
saisies au fond** (`build_commissions_dossiers.py`, #328 — non bloquante, elle
dérive du référentiel et non du corpus) ; profils de groupe parlementaire réel, **fiches de lignée de groupe**
(`generate_lignee_profiles.py`, #836 — lues sur les fiches de groupe que le step
précédent vient d'écrire, jamais du réseau, donc APRÈS lui et insensibles à son
code 2 ; `continue-on-error`, même arbitrage que le step gouvernement, la §4c du
portail hard-failant sur une fiche absente ou invalide ; **104 s et 1 453 Mio de
RSS** mesurés pour les 10 lignées), **la liste des gouvernements lue dans AMO30**
(`gouvernements_amo30.py`, #996 — réécrit `raw_data/gouvernements_reels.json`, 17
gouvernements depuis 2007 ; sans `continue-on-error` : une archive illisible lève
avant toute écriture et la liste committée reste), profils
de gouvernement (`generate_gouvernement_profiles.py` → `gouvernement_profile.py`
+ `gouvernement_roster.py` ; **`--rosters-bruts raw_data/rosters_bruts.json`
depuis #996 lot 4**, qui rattache les membres par `organe_ref` au lieu de
comparer `mandats[].label` au libellé de la config — sans ce fichier le repli
par libellé s'applique et les fiches sont produites quand même, la sortie
disant laquelle des deux voies a servi) ; `check_quality_gate.py` ; les **quatre contrôles** de la §8 ;
la vérification que `src/` et `raw_data/*.json` n'ont pas bougé sur la branche
pendant le run ; le commit et le push ; **le signal disant si ce commit
déclenchera `tests.yml`** (#685, §6) ; la fenêtre de rétention de l'historique
de données ; le déclenchement de `deploy-pages.yml`.

**Quatre archives de dossiers depuis #1019, et deux formats.** `AN_DOSSIERS_ARCHIVES`
(`couverture_dossiers.py`) liste les législatures XIV à XVII. La XIV est
**monolithique** — un seul JSON de 36 Mo décompressés, les objets dans deux
tableaux — là où les autres portent un fichier par objet ;
`gouvernement_textes._entrees_monolithiques` lit cette forme, détectée sur la
FORME de l'archive et jamais sur son numéro. Ce qui en dépend dans ce job : la
table des commissions, celle des scrutins, l'index des textes portés et les
fiches de gouvernement. Conséquence pour le lecteur : la **borne de couverture
recule au 2012-06-20**, et quatre gouvernements cessent de publier `textes: []`.
Les XII et XIII répondent 404 — Fillon I, II et III restent hors couverture.

**Trois index de ce job portent un numéro de version**, et il change dès que
leur CONTENU change, pas seulement leur forme : `index_acteur_textes_v5`,
`index_texte_dossier_v2`, `index_dossier_commission_v2`. Le cache
`.cache/dossiers_an` est restauré d'une semaine sur l'autre par ses
`restore-keys` : un correctif qui ne change pas la clé ne change rien, ce qui a
coûté trois runs sur #997.
→ `docs/decisions/archive-dossiers-xiv-1019.md`,
  `docs/decisions/cle-index-textes-portes-997.md`

**Deux tables se dérivent des mêmes archives de dossiers**, l'une après l'autre.
Après la table des commissions saisies au fond, une seconde étape marche **le
même arbre sur les mêmes archives** pour publier le **rattachement des scrutins à
leur dossier** (`build_scrutins_dossiers.py`, #758) — un scrutin AN ne nomme pas
le texte qu'il tranche, et sans cette table la section « Ce qu'il a voté » ne peut
dire ni sur quoi porte un texte voté ni ce qu'il est devenu. Non bloquante et
additive comme la première ; le `git add` du push la protège par un test
d'existence, l'étape étant `continue-on-error`.

**Et une étape amont, dans les trois jobs qui cachent ces archives**
(`rafraichir_dossiers_actifs.py`, #762) : elle reprend la seule législature
**encore vivante** quand la clé hebdomadaire n'a pas été touchée (`cache-hit !=
'true'`). Sans elle, le `restore-keys` de préfixe ramenait le répertoire de la
semaine d'avant et rien n'était jamais retéléchargé — la rotation se désamorçait
elle-même, comme dans #749. Les législatures dissoutes ne sont jamais reprises :
23 Mo hebdomadaires pour un contenu identique. L'étape est aussi gardée par
`!inputs.cold_start`, le `rm -rf .cache` du démarrage à froid la suivant dans
deux des trois jobs.

**Consomme** tous les artifacts ci-dessus — mais **aucun** pour la ligne de
base : il checkoute le dépôt, et la fusion ne réécrit que les slugs présents
dans les artifacts. Il lit aussi `.cache/dossiers_an` (restauré par son propre
`actions/cache`, §5) : depuis #639, la construction de `pivot_data/amendements/`
y joint chaque `texte_vise` à son dossier législatif, et depuis #328 la table
`pivot_data/commissions_dossiers.json` y lit l'acte `AN1-COM-FOND-SAISIE` de
chaque dossier. Archives absentes → aucun rattachement ajouté, aucun retiré,
aucune commission ajoutée, et le job le dit dans son log ; le `git add` de la
table est conditionné à son existence, pour qu'un run sans archive ne coûte pas
le commit des profils. Il lit aussi `raw_data/amendements_an_figes/` (committé,
pas caché) : depuis #696, la même construction **relit** dans l'archive figée le
`texte_vise` des entrées qui portent un intitulé au lieu de l'uid du document AN
— 2 500 des 484 132 amendements publiés au 01/09/2026, que la fusion additive ne
pouvait pas corriger seule. Aucune archive n'est ouverte pour une législature
sans entrée fautive, et ce que le report ne répare pas est compté dans le log
([report `texte_vise`](decisions/report-texte-vise-source-696.md)). **Produit** le commit de données sur `main`, poussé sous
`secrets.DATA_PUSH_SSH_KEY` — **renseigné depuis le 01/09/2026**, avec sa clé de
déploiement `data-push (#508)` en écriture et son entrée `DeployKey` dans les
`bypass_actors` du ruleset. Le push émet donc bien un événement `push` :
`f635cb60` a déclenché `tests.yml`, qui a réussi. Le check requis
`Suite complète` est posé sur `main` (#693) — il ne bloque pas ce commit, qui
contourne par la clé, mais il rend le refus bruyant `GH013` déclenchable le jour
où la clé casse, ce qui est précisément le silence qui avait laissé passer quinze
commits (#685, §6). C'est le seul job à porter
`permissions: contents: write`.

**Pourquoi comme ça** : les quatre contrôles sont **cloisonnés**, aucune
tolérance ne désarmant celui d'un autre — un contrôle grossier rendu bloquant
forcerait à relancer avec sa tolérance, ce qui désarmerait du même coup les
contrôles précis
([contrôle de perte](decisions/controle-de-perte-avant-commit.md)) ; la fusion
est **additive**, une régénération ne retirant jamais de donnée collectée
([une collecte vide n'écrase jamais](decisions/collecte-vide-necrase-jamais.md)) ;
le push passe par une clé de déploiement parce que le ruleset du dépôt applique
ses `required_status_checks` aux pushes directs et qu'une App Actions ne peut pas
être `bypass_actor` sur un dépôt personnel
([clé de déploiement](decisions/push-donnees-cle-de-deploiement-508.md)) ; et un
build dont les entrées ont changé pendant le run ne se committe pas
([ne jamais committer un build périmé](decisions/ne-jamais-committer-un-build-perime.md)).
Le détail est dans la §8 pour les contrôles, la §6 pour le push,
[la fenêtre de rétention](decisions/fenetre-historique-donnees.md) et
[le déclencheur de déploiement](decisions/deploy-pages-declencheur-donnees.md).

## 2. Le formulaire de lancement

Deux axes **disjoints**, plus le cache à part (#578,
`docs/decisions/deux-axes-formulaire-578.md`) — et, depuis #792, un **mode** au-dessus
d'eux : `test_slugs` ne règle rien, il restreint. Les trois effets qu'il porte vont
ensemble ou pas du tout, deux cases séparées autoriseraient « périmètre réduit ET commit ».


| Champ | Type | Défaut | Ce qu'il commande |
|---|---|---|---|
| `test_slugs` | `string` | vide | **Le mode**, et il est en tête pour ça (#792). Rempli, il réduit la matrice `extract-an` à ces slugs, plafonne le roster à 8 membres sur 1 shard si aucun plafond n'a été demandé, et **désarme le commit**. Vide : run ordinaire, rien ne change. Un slug hors périmètre est nommé (`TEST_SLUG_INTROUVABLE`), un périmètre vide fait échouer le job de matrice. **Mesuré : 51 min contre 1 h 15** — `merge-and-pivot` fait la moitié du run et ne se réduit pas. |
| `existing_profiles` | `choice` : `leave-as-is` / `refresh` / `overwrite` | `refresh` | **Axe 1** — ce qu'on fait des profils DÉJÀ écrits. `overwrite` seul lève `--no-merge`. |
| `add_uncovered_members` | `boolean` | `true` | **Axe 2** — si on écrit un premier profil pour les membres qui n'en ont pas. |
| `cold_start` | `boolean` | `false` | Purge les caches de téléchargement et re-télécharge les sources. Ne dit **rien** de la façon dont les profils sont écrits. |
| `roster_limit` | `number` | `0` | Un plafond, et rien d'autre (`0` = pas de plafond). Ne commande aucune politique de rafraîchissement. |
| `collect_interventions` | `boolean` | `false` | Ajoute les archives Syceron et QE/QG/QOSD à `extract-an`, et les **débats seuls, sans verbatim**, au roster (#657). |
| `collect_dossiers_legislatifs` | `boolean` | `false` | Ajoute les **textes portés** aux membres du roster (#817). 17 profils sur 1 035 en publiaient, tous candidats déclarés ; 887 membres de roster en porteraient, pour 9 895 dossiers. Coût : 3,0 s de construction d'index, une fois par processus. |
| `incomplete_read_threshold` | `number` | `3` | Seuil d'incidents réseau au-delà duquel le quality gate échoue. |
| `allow_declared_losses` | `boolean` | `false` | Tolérance du contrôle de perte (#460). |
| `allow_broken_references` | `boolean` | `false` | Tolérance de l'intégrité référentielle (#485). |
| `allow_unpublished_profiles` | `boolean` | `false` | Tolérance de « collecté = publié » (#511). |
| `allow_publication_gaps` | `boolean` | `false` | Tolérance de « chaque liste porte ce que la collecte a rendu » (#545). |

Les quatre tolérances sont **cloisonnées** : aucune ne désarme le contrôle d'une
autre.

Les `description:` sont les **libellés affichés** : GitHub montre la description
et masque le nom du champ. Ce sont des titres, pas de la documentation.
**`python3 scripts/rendu_formulaire.py` rend le formulaire tel qu'il s'affiche** —
lire le YAML masque exactement le défaut que #578 a corrigé. Verrouillé par
`tests/test_ci_inputs_workflow.py::test_un_libelle_tient_sur_une_ligne`.

`ROSTER_COVERAGE`, `roster_coverage`, `overwrite_profiles` et
`refresh_existing_only` sont des noms **morts** ; le test
`test_les_deux_axes_sont_deux_champs_distincts` échoue si l'un réapparaît dans
les inputs.

## 3. Les caches

Une clé par source, semainière, avec `restore-keys` pour retomber sur l'entrée
la plus proche :

| Clé | Répertoire | Qui l'**écrit** | Qui la **lit seulement** |
|---|---|---|---|
| `public-data-cache-an-<semaine>[-interv-<empreinte>]` | `.cache/acteurs_historique_an`, `.cache/scrutins_an`, `.cache/questions_an/*/index_par_acteur.json`, `.cache/syceron_an/*/index_par_acteur` | `extract-an` (`actions/cache/save`) | `extract-roster-groupes` (`actions/cache/restore`, **même suffixe** depuis #657) |
| `public-data-cache-amendements-<semaine>` | `.cache/amendements_an` | `extract-amendements-an` (`actions/cache`) | `extract-an`, `extract-roster-groupes` (`restore`) |
| `public-data-cache-dossiers-<semaine>` | `.cache/dossiers_an` | `extract-an`, `merge-and-pivot` | `extract-roster-groupes` (`restore`) |
| `public-data-cache-ue-<semaine>` | `.cache/europarl` | `extract-ue-officiel` | — |
| `public-data-cache-parltrack-<semaine>` | `.cache/parltrack` | `extract-parltrack` | — |
| `public-data-cache-senat-<date>` | `.cache/senat` | `extract-senat` | — |

La clé sénatoriale est au **jour**, et non à la semaine comme les quatre autres :
`data.senat.fr` régénère son export chaque nuit (#885).

**La règle du producteur-écrivain** : un job n'écrit jamais une clé pour un
répertoire qu'il ne remplit pas. `actions/cache` saute la sauvegarde post-job
sur un hit exact, donc le premier écrivain gèle l'entrée pour tout le monde. Le
même défaut est passé trois fois (#412 §2.3 → #424 → #505). Deux corollaires :
un job portant un `--skip-*` utilise `actions/cache/restore`, et une clé dont le
**contenu** dépend d'un input porte cet input — d'où le suffixe
`-interv-<empreinte>` quand `collect_interventions` est vrai. Le **consommateur**
doit porter ce suffixe aussi (#657) : sans lui, la clé nue de la semaine — écrite
par n'importe quel run en mode par défaut — fait un *exact key hit*, et
`restore-keys` n'est pas consulté après un hit exact ; les 8 shards roster
repartiraient d'une entrée sans contenu Syceron et reconstruiraient les trois
index chacun. Deux jobs qui partagent une clé partagent aussi le `path:` exact,
la version de l'entrée en étant un hash. Verrouillé par `tests/test_ci_cache_producteur_ecrivain.py`.
Voir `docs/decisions/cache-mode-interventions-505.md`.

## 4. Les artifacts

**Un artifact = la contribution d'un seul job** (#450). Un job d'extraction
publie uniquement les profils qu'il a **effectivement écrits** — jamais
`raw_data/profiles/`, que son `actions/checkout` a aussi rempli avec la ligne de
base committée. Republier la ligne de base faisait refusionner par la fusion
additive la version périmée et la version corrigée d'un même profil (défaisant
`--no-merge`), et faisait entrer en collision les shards sous `merge-multiple`,
si bien qu'un seul shard survivait.

Le mécanisme : `generate_all_profiles.py --manifest-out` +
`.github/actions/publish-written-profiles`. `merge-and-pivot` n'a besoin
d'aucun artifact pour la ligne de base — il checkoute le dépôt, et
`merge_raw_dirs` ne réécrit que les slugs présents dans les artifacts. Gardé par
`tests/test_ci_publication_profils.py`. Voir
`docs/decisions/publication-scopee-artifacts.md`.

Un artifact sert aussi de **transport horizontal** entre jobs :
`amendements-index-an` et `roster-candidats` sont téléchargés par les jobs
avals plutôt que refabriqués — c'est ce qui donne « zéro fetch roster en CI »
(#518) et « un seul roster par run ».

## 5. Budgets et durées

**Référence : ~66 min pour un run complet** (mesuré le 29/08/2026). Les valeurs
de `timeout-minutes` sont des **filets de sécurité**, pas des dimensionnements —
ne pas budgéter un run à partir d'elles.

| Job | `timeout-minutes` |
|---|---|
| `rafraichir-candidats` | 10 |
| `prepare-an-matrix` | 5 |
| `extract-an` (par shard) | 5, ou 10 si `collect_interventions` |
| `extract-ue-officiel` | 60 |
| `extract-parltrack` | 30 (= `env.PARLTRACK_TIMEOUT_MINUTES`) |
| `extract-amendements-an` | 30 |
| `prepare-roster-matrix` | 20 |
| `extract-roster-groupes` (par shard) | 60 |
| `extract-senat` | 15 |
| `extract-mandats-locaux` | 20 |
| `merge-and-pivot` | 120 (60 jusqu'à #827, voir plus bas) |

Mesures utiles : un shard roster ≈ **200 s**, dont ~130 s de frais fixes (~110 s
de `actions/checkout` seul — le dépôt porte les profils) et ~65 s d'extraction
pour 24 membres. Sharder ×8 paie donc huit fois ces 130 s ; c'est pourquoi la
matrice roster est en `max-parallel: 4` (#467,
`docs/decisions/budget-roster-mesure.md`). `merge-and-pivot` : 7,5 min mesuré à
209 profils, **28 min** mesuré le 10/09/2026 sur le run `34472416487`.

**Son plafond est passé de 60 à 120 min avec #827**, et c'est la première
interrogation du portail européen qui l'exige : 1 320 requêtes à 0,6 s plus 13
blocages de 60 s, soit **47 min mesurées** pour les 1 424 documents cités par
les explications de vote. 28 + 47 = 75 : à 60 le job aurait été tué, et le retry
automatique serait reparti pour un second échec. Les runs suivants retombent à
~28 min, le cache `.cache/europarl` étant **restauré du run précédent** — un
document du Parlement européen ne se périme pas, et faire expirer ce cache
hebdomadairement ne rachèterait rien qu'une facture. **La clé change à chaque run
depuis #965** (`…-documents-v3-<run_id>`, repli par préfixe) : fixe, elle n'était
jamais réécrite par `actions/cache`, et chaque run restaurait le cache de sa toute
première sauvegarde — sans titre ni concepts
(`docs/decisions/titre-francais-lu-dans-source-url-901.md`).

La collecte des interventions se borne **elle-même** par
`--budget-interventions-secondes` (240 s en CI, par candidat, partagé entre les
chambres). Les deux plafonds bougent ensemble : un shard tué par
`timeout-minutes` n'écrit **aucun profil**, tandis qu'un budget épuisé écrit le
profil partiel et déclare la troncature dans `meta.warnings[]`. Gardé par
`tests/test_ci_budget_interventions.py`, voir
`docs/decisions/budget-collecte-interventions.md`.

## 6. Le push

`merge-and-pivot` checkoute avec
`ssh-key: ${{ secrets.DATA_PUSH_SSH_KEY }}` — une **clé de déploiement**, pas le
`GITHUB_TOKEN` (#508). Un ruleset du dépôt applique ses
`required_status_checks` aux **pushes directs**, et ce job pousse sur `main`
sans PR : la règle lui est insatisfiable, pas seulement lente. L'app GitHub
Actions ne peut pas être `bypass_actor` sur un dépôt **personnel**, la clé si.

Un push par clé de déploiement **émet un événement `push`**, là où le
`GITHUB_TOKEN` n'en émet aucun : c'est cette bascule qui décide si `tests.yml` et
`deploy-pages.yml` voient passer le commit de données.

**Elle a lieu depuis le 01/09/2026, et c'est mesuré.** Les trois gestes que #685
attendait ont été faits, et ils tiennent ensemble : le secret
`DATA_PUSH_SSH_KEY` existe (créé le 01/09/2026 à 11 h 52), sa clé de déploiement
`data-push (#508)` est en **écriture**, et le check requis `Suite complète` est
posé sur `main` avec `DeployKey` en `bypass_actors`. Le push émet donc un
événement `push` : vérifié le 14/09/2026 sur le commit de données `3e9e9c138`,
qui porte une `Suite complète` **réussie**.

**Ce que cette page disait avant, et pourquoi elle le disait.** Pendant tout
#685, le dépôt n'avait aucune clé, `ssh-key` valait la chaîne vide,
`actions/checkout` retombait sur le `GITHUB_TOKEN` en HTTPS, et **0 des 15**
commits de données arrivés sur `main` depuis que `tests.yml` existe ne portait
de run de la suite. Le refus **bruyant** annoncé sur secret absent ne parlait que
sur un `GH013`, lequel suppose le check requis — absent lui aussi : les deux
omissions se couvraient l'une l'autre. C'est la forme du défaut qu'il faut
retenir, pas son état : **un silence peut être produit par deux garde-fous qui
s'annulent**, et le seul témoin est la mesure. Le déclenchement explicite de
`deploy-pages.yml` par `gh workflow run` (#416) reste en place, et c'est lui qui
avait empêché cette absence de coûter la publication du site.

Le dernier step du job **mesure** donc `git remote get-url origin` après un push
abouti et dit, en annotation et dans le résumé du job, si `tests.yml` tournera —
non bloquant, parce que les trois gestes qui portent le mécanisme (clé, secret,
check requis) vivent hors du dépôt et peuvent en repartir sans qu'un test le
voie. Ce step reste le témoin : c'est lui, pas cette page, qui dit l'état d'un
run donné. Voir
`docs/decisions/push-donnees-cle-de-deploiement-508.md` et
`docs/decisions/identite-du-push-et-declenchement-des-tests-685.md`.

Le workflow porte `permissions: contents: read` au niveau global, et
`contents: write` uniquement sur `merge-and-pivot` (#413 §6). Concurrence :
groupe `generate-data`, `cancel-in-progress: false` — deux runs ne committent
jamais en même temps.

## 7. La relance automatique — le couplage invisible

`.github/workflows/retry-generate-data.yml` se déclenche sur
`workflow_run: [completed]` de « Génération des données », que la conclusion soit
`failure` **ou** `success` (#245 : un job en `continue-on-error` peut échouer
réellement sans faire basculer la conclusion globale).

**Rien dans `generate-data.yml` ne référence la relance, et réciproquement.**
Le couplage est réel et muet, et il a déjà cassé deux fois — un `-f` sans input
correspondant (dispatch en **422**, le jour où une relance était nécessaire), et
une sortie écrite sous un nom mais lue sous un autre, qui faisait repartir la
relance **sur les valeurs par défaut, sans erreur ni trace**.

### Ce qui déclenche

1. **Plafond** : si le run échoué a lui-même été déclenché par la relance
   (`triggering_actor == github-actions[bot]`), on ne retente pas. Le plafond est
   porté par l'identité du déclencheur, pas par un compteur : une relance
   **manuelle** repart avec un plafond neuf (#414 §6).
2. **Classement des échecs**, en une seule collecte (`gh api .../jobs --paginate`
   + un seul téléchargement par log de job en échec, #414 §5) : `matched`
   (signature de préemption du runner), `code_change`, `api_error`,
   `inconclusive`, `no_job_failure`. Seuls `matched` et `code_change` relancent.

### Comment les inputs sont reconstruits

**L'API n'expose pas les inputs d'un run.** Ils sont donc **reconstruits en
analysant les logs** des jobs, puis repassés par
`gh workflow run generate-data.yml -f nom=valeur`.

| Input | Où il est lu | Repli |
|---|---|---|
| `cold_start` | le step « Purge des caches… » d'`extract-an` a-t-il conclu `success` | `false` |
| `collect_interventions` | la valeur substituée dans la condition `[[ "<valeur>" != "true" ]] && INTERV_FLAG` du log `extract-an` | `false` |
| `incomplete_read_threshold` | `Seuil : <n>` dans le log `merge-and-pivot` | `3` |
| `roster_limit` | `ROSTER_LIMIT: <n>` dans le bloc `env:` résolu du step roster ; à défaut le stdout de sélection | `0` |
| `existing_profiles` | `EXISTING_PROFILES: <valeur>` dans le même bloc `env:` | la présence de `--no-merge` dans le log `extract-an` ⇒ `overwrite`, sinon `refresh` |
| `add_uncovered_members` | `ADD_UNCOVERED: <bool>` dans le même bloc `env:` | `true` |

**`test_slugs` n'est PAS reconstruit — il interdit la relance (#792).** Un retry
qui perdrait cette valeur relancerait un run de test en run **complet**, qui
committerait un corpus que personne n'a demandé à publier. Le step de lecture
rend donc `run_de_test` ∈ `false` / `true` / `inconnu` d'après la présence d'un
`TEST_SLUGS: <valeur>` non vide dans le bloc `env:` résolu de
`prepare-an-matrix`, et la relance exige un `false` **explicite** : log
illisible, job absent ou valeur inattendue, on s'abstient et on le dit
(`RETRY_ABANDONNE`). Un retry manqué se rattrape d'un clic ; un commit publié
depuis un périmètre réduit ne se rattrape pas.

Deux pièges qui expliquent la forme de ces greps, et qu'il ne faut pas
« simplifier » :

- le **texte source** `--skip-interventions` est présent dans le log même quand
  la condition était fausse à l'exécution — GitHub journalise le source bash
  substitué, pas la trace d'exécution. Chercher sa seule présence donnerait
  toujours vrai ;
- `roster_limit=0` (le défaut depuis #578) n'émet **aucune** ligne de sélection :
  lire le stdout d'abord faisait retomber tout run complet sur `20`, donc
  relancer un run échantillonné.

Les extractions sont ancrées et restreintes à `[0-9]+` / `(true|false)` pour
qu'une valeur inattendue **échoue la validation** plutôt que d'être transmise
telle quelle, et chaque `grep` porte `|| true` pour qu'une valeur manquante ne
dégrade qu'elle-même au lieu d'avorter tout le step.

Le step de re-déclenchement porte `if: always() && (matched || code_change)`
(#336) : il ne doit pas dépendre du succès du step best-effort qui précède.
Chaque `-f` porte un `|| '<défaut>'` côté expression GHA, aux **mêmes valeurs
par défaut** que celles déclarées dans `generate-data.yml`.

### Les tests qui verrouillent le contrat

Dans `tests/test_ci_inputs_workflow.py` :

- **`test_chaque_input_passe_a_la_relance_existe`** — tout `-f <nom>=` de la
  relance est un input déclaré par `generate-data.yml`. Un `-f` orphelin fait
  échouer le dispatch en 422, jamais avant.
- **`test_chaque_sortie_lue_par_la_relance_est_ecrite`** — tout
  `steps.inputs.outputs.<nom>` lu est un `echo "<nom>=…" >> "$GITHUB_OUTPUT"`
  écrit. Une sortie lue mais jamais écrite vaut la chaîne vide, et la relance
  repart sur les défauts, silencieusement.
- `test_les_deux_axes_sont_propages_par_la_relance` — les deux axes de #578
  passent bien la relance.

Voir `docs/decisions/retry-generate-data-preemption.md`,
`docs/decisions/retry-inputs-appariement-prefixe.md`,
`docs/decisions/retry-generate-data-detection-impossible.md`.

## 8. Les quatre contrôles avant commit, dans `merge-and-pivot`

Les **règles** qu'ils imposent sont dans `AGENTS.md` §3c ; ici, leur ordre, leur
coût et leur placement dans le job. Chacun tourne dans un **processus séparé**,
pour que le pic mémoire du job reste celui du plus gourmand et non leur somme.

| Ordre | Contrôle | Placement | Coût mesuré |
|---|---|---|---|
| 1 | `audit_collecte_non_publiee.py` (#511) | **après les deux passes `--pivot-only`**, celle de `candidats.json` et celle du roster — placé *entre* elles, tout membre de roster serait un faux manque, puisqu'il est alors légitimement sans pivot. Emplacement vérifié par `tests/test_ci_collecte_non_publiee.py::test_le_controle_suit_les_deux_passes_de_normalisation_pivot` | 0,08 s / 13,9 Mio à 752 profils ; ne parse aucun profil (deux listages de noms de fichiers) |
| 2 | `audit_diff_profils.py --ref HEAD` (#460/#470) | après les deux passes, avant le commit, sur **tout** `pivot_data/` | pic du job à 186,6 Mio |
| 3 | `audit_integrite_referentielle.py` (#485) | juste après le contrôle de perte | 3,02 s / 162,0 Mio ; 0 orphelin sur 1 347 451 références à `01ffa7f` |
| 4 | `audit_collecte_vs_publie.py` (#545) | après les deux passes, avant le commit | 58,7 s / 158,2 Mio sur 4,3 Go de profils bruts, sans en matérialiser un seul (`object_pairs_hook`) ; 0 déficit et 0 surplus sur 2 380 paires à `3104e37` |

Quatre inputs de tolérance, **cloisonnés** : `allow_declared_losses`,
`allow_broken_references`, `allow_unpublished_profiles`,
`allow_publication_gaps`. Aucun ne désarme le contrôle d'un autre — et
`allow_declared_losses` en particulier ne désarme **pas** l'intégrité
référentielle : une perte peut être légitime, une référence orpheline non.

Le commit ne part que si `check_quality_gate.py` sort en 0, et le push suit la
§6.


### Ce que `merge-and-pivot` ne produit plus : les fiches de parti (#906)

Le job portait une étape « Générer les profils de parti », retirée le
14/09/2026 avec `src/parti_profile.py`, `src/schema_parti.py` et les 29 fiches.

**La raison n'est pas le poids** — 192 Ko. Aucune ligne de `web/UI_finale` ne les
lisait, `sync-data.mjs` ne les copiait pas, et il n'y a jamais eu d'onglet Partis,
pas même dans `web/old/v7`. Surtout, **25 des 29 fiches n'agrégeaient qu'un seul
candidat déclaré**, et le seul parti qui en avait davantage était dédoublé —
`Parti socialiste` et `Parti Socialiste (PS)`, séparés par une majuscule, faute
d'une normalisation de `parti_nom` que rien n'imposait.

`check_quality_gate.py` perd son `--partis-dir` et `garde_fou_blobs.py` son entrée
de `REPERTOIRES_SURVEILLES` : les deux lisaient ce répertoire **parce qu'il
existait**, pas parce qu'ils en avaient besoin.

**Ce qui n'a pas bougé** : `identite.parti` et le champ `parti` des profils, qui
sont publiés et lus. Une fiche de parti et l'étiquette partisane d'une personne
sont deux choses.

### Les trois index européens, dans `merge-and-pivot` (#901)

Trois étapes, entre les passes pivot et la génération des fiches de groupe.

| Étape | Produit | Volumétrie |
|---|---|---|
| `src/scrutins_europeens.py` | `pivot_data/scrutins_europeens.json` | **5 571** scrutins, 3,8 Mo (14/09/2026) |
| `src/dossiers_europeens.py` | `pivot_data/dossiers_europeens.json` | **389** dossiers (16/09/2026) ; ~**4 642** attendus une fois les dossiers votés inclus (estimation du 17/09/2026 sur le dump du 17/08) |
| `src/documents_europeens.py` | `pivot_data/documents_europeens.json` | **335** documents cités (16/09/2026) |

**Les deux premières ne collectent rien** : les dumps ParlTrack sont déjà en
cache, déposés par `extract-parltrack`. `dossiers_europeens.py` lit pourtant le
dump des dossiers **en entier**, et pas seulement les dossiers cités : le libellé
d'une famille OEIL (`6` → « External relations of the Union ») n'apparaît que sur
437 occurrences des 23 885 dossiers, et il faut le trouver où il est (v3, 17/09/2026).

**Depuis la v4 (17/09/2026), `dossiers_europeens.py` interroge aussi le réseau**,
pour les **domaines EuroVoc** d'un dossier : EuroVoc est attaché à un document, pas
à une procédure. Il lit les documents de séance du dossier dans le dump, demande au
portail du Parlement les concepts du **texte adopté** d'abord (le rapport de
commission n'est presque jamais classé), puis leurs domaines par SPARQL. **Budget : 20 minutes
par run** (`--budget-secondes`, borne haute `--plafond-requetes` 1 500), les dossiers
amendés en premier ; le cache `.cache/europarl`, restauré et cumulé d'un run à
l'autre, répond sans compter. Au-delà du budget, un dossier porte
`domaines_non_resolu.motif = "question_non_posee"` et attend le run suivant.

**Le budget est en temps, et le cache est sauvegardé tout de suite après l'étape.**
Le run `35231390627` (17/09/2026) a consommé 1 500 requêtes en **88 minutes** —
3,5 s par requête en CI, contre 0,9 s depuis un poste —, `merge-and-pivot` a
dépassé ses 120 minutes et a été annulé sans rien commiter, et le cache, que
`actions/cache` n'enregistre qu'en cas de succès, a été perdu. D'où le step
« Sauvegarder le cache du portail européen », en `if: always()`, sous une clé
suffixée `-dossiers`. Au débit mesuré, 20 minutes valent ~340 requêtes.

**La troisième interroge le réseau elle aussi.** Elle lit
`src/europarl_documents.py` pour les concepts EuroVoc d'un document — dans la
réponse que le résolveur télécharge **déjà** pour l'existence et le titre, donc
sans requête de plus au Parlement — puis résout les libellés **et les domaines** chez l'Office des
publications, **par lots SPARQL de 100 concepts** — deux requêtes par lot (v2, 17/09/2026). Si le portail du Parlement se
tait, le disjoncteur arrête la passe après cinq silences consécutifs plutôt que
de payer un `TIMEOUT` par document, et le résumé du job le dit.

**Pourquoi après les passes pivot, et pas avant.** Leur périmètre est *ce que les
profils publiés citent* — les `numero_scrutin` des votes pour le premier, les
`texte_vise` des amendements, **les `reference_dossier` des textes portés et ceux des votes**
pour le deuxième, les `source_url` doceo des textes portés européens pour le
troisième. Les construire avant indexerait le corpus d'hier. C'est le même choix que `pivot_data/scrutins.json` côté Assemblée :
l'index suit le corpus, il ne le précède pas.

**Aucune tolérance.** Un dump indisponible fait échouer l'étape
(`DumpVotesIndisponible`, `DumpDossiersIndisponible`) plutôt que d'écrire un index
vide — qui se lirait comme « aucun scrutin européen », la confusion de #510. Une
référence citée mais absente du dump ne produit **aucune entrée** : elle est
comptée et dite sur la sortie d'erreur, jamais fabriquée.

**Ce qu'ils portent, et ce qu'ils refusent.** Les scrutins portent les effectifs
pour / contre / abstention **ventilés par groupe politique**, jamais de liste
nominative ni de `sort` déduit des totaux — le Parlement vote aussi à la majorité
qualifiée, et le dump ne dit pas quelle règle s'appliquait. Les dossiers portent
titre, type de procédure, stade et **commissions saisies au fond** (341 sur 355).

### `extract-mandats-locaux` — le versant local d'un parcours (#922)

**Ce qu'il fait** (`src/collecte_mandats_locaux.py`, qui lit `src/rne_opendata.py`).
Interroge le Répertoire national des élus et le fichier des
sortants 2020-2026 par `tabular-api.data.gouv.fr`, et écrit le bloc
`mandats_locaux` dans les profils bruts des **candidats déclarés**. Un membre de
roster n'en reçoit pas : ~750 membres × 9 fichiers pour une donnée qu'aucune page
n'affiche.

**Pourquoi aucun cache.** Ce job ne télécharge rien — il pose des requêtes
filtrées côté serveur, contre 76 Mo de CSV. **Leur nombre a doublé le 16/09/2026**
(~24 par candidat au lieu de ~13) : chaque date de naissance est demandée sous
deux formes, parce que le fichier des sortants a daté au XXIᵉ siècle les élus nés
avant 1980, et que la seule date exacte perdait cinq mandats clos. Mesuré avant ce
doublement : 7 min, sous un plafond de 20
(`docs/decisions/sortants-annee-decalee-922.md`). Il n'y a donc rien à mettre en
cache, et une clé hebdomadaire ferait servir un répertoire vide en croyant
servir des données. Le `rid` de chaque fichier est **résolu par le catalogue à
chaque run** : il change à chaque publication trimestrielle.

**Ce qu'il déclare toujours.** Le bloc porte `appariement`, en vocabulaire
fermé, même quand il ne contient aucun mandat — `date_naissance`,
`table_relue`, `ecarte`, `aucun_mandat_trouve`, `non_relu`. Les deux derniers se
ressemblent et ne se confondent pas : l'un est un constat, l'autre un aveu.
Publier l'un pour l'autre ferait dire à une fiche « cette personne n'a pas de
mandat local » alors que nous ne le savons pas (§2 règle 5).

**Sa borne.** `borne_couverture` vaut 2020 et voyage dans chaque bloc, plutôt que
de vivre seulement dans un document : une fiche doit pouvoir dire, sans rien
aller chercher, que rien avant cette date n'a pu être vérifié.

**Ses refus.** `continue-on-error` comme `extract-senat`. Les trois fichiers du
RNE portant des mandats que nous collectons déjà — députés, sénateurs,
représentants au PE — sont refusés **à la lecture** : un filtre à l'affichage
laisserait la donnée dans `raw_data/`, où la fusion additive la garderait
indéfiniment (#729).

### `extract-senat` — les appartenances sénatoriales (#885)

**Ce qu'il fait** (`src/collecte_senat.py`, qui lit `src/senat_opendata.py`).
Télécharge `export_sens.zip` depuis `data.senat.fr`, le
décompresse, et écrit le bloc `mandat_senatorial` dans les profils bruts des
**candidats déclarés appariés** — 2 profils, 133 appartenances au 13/09/2026.

**Les modules du lot, et ce que chacun fait.** Six fichiers, et le nom du job n'en
désigne aucun — les chercher dans 4 000 lignes de YAML est ce qui a coûté une
demi-heure le 15/09/2026 :

| Module | Ce qu'il fait |
| --- | --- |
| `src/collecte_senat.py` | le script d'entrée du job : lit l'export, compose le bloc, écrit les profils du périmètre, tient le manifeste |
| `src/senat_opendata.py` | la lecture de l'export PostgreSQL, et le **refus à l'entrée** des trois tables de présence individuelle (§2 règle 3) |
| `src/appariement_senateurs.py` | **relie un profil publié à son matricule sénatorial** — la question qu'on se pose en premier quand un mandat n'apparaît pas sur une fiche |
| `src/senat_mandats.py` | compose les appartenances d'une personne, datées, nommées à la date du mandat |
| `src/normalize_senat.py` | traduit ces appartenances en mandats pivot ; appelée par `generate_all_profiles` |
| `src/retrait_heritage_senat.py` | ce que la collecte sénatoriale **remplace** — un retrait nommé, la fusion étant additive |

`src/retrait_residus_senat_908.py` n'appartient pas au job : c'est un retrait
ponctuel, celui du dernier reste de Regards Citoyens (#908).

**Ce qu'il consomme.** `raw_data/correspondance_acteurs_an.json`, dont le champ
`identifiants.senat` porte le matricule ; `pivot_data/profiles/` pour lire la
provenance, seule couche qui l'ait (#630).

**Ce que `merge-and-pivot` en fait.** Il télécharge `raw-profiles-mandats-locaux`
vers `_artifacts/mandats-locaux` — optionnel, comme les autres familles : si le job a
échoué, la fusion additive garde ce que le run précédent a publié. Ce répertoire entre
dans le `--dirs` de `merge_profile.py`, jamais dans `raw_data/profiles` directement : un
artifact qui atterrit dans l'arbre court-circuite `merge_raw_dirs` et écrase les
contributions des autres jobs (#450).

**Ce qu'il produit.** L'artifact `raw-profiles-senat`, **scopé au manifeste**
(#450) : uploader `raw_data/profiles/` entier réinjecterait la baseline
committée du checkout. Consommé par `merge-and-pivot` dans `_artifacts/senat`,
répertoire que #528 avait retiré de `merge_raw_dirs` et que ce lot rétablit.

**Cache.** Clé au **jour** (`public-data-cache-senat-<date>`), là où ParlTrack
se contente de la semaine : le Sénat régénère son export chaque nuit.

**Ses refus.** `continue-on-error` comme `extract-parltrack` — une source tierce
indisponible ne coûte pas le run, et la fusion additive garde ce que le run
précédent a publié. Un export de moins d'1 Mo **échoue le step** : l'archive a
déjà été servie vide, 444 octets et 0 table le 13/09/2026 à 03 h 33, avec un
HTTP 200 et un `Content-Type: application/zip`.

**Où ses mandats rejoignent le pivot.** `generate_all_profiles` verse le bloc par
`normalize_senat.normalize_mandats`, puis **recalcule `chambres`** — sans ce recalcul,
un profil AN + Sénat publierait `["AN"]` et effacerait la carrière sénatoriale (#493).
Les mandats locaux du RNE, eux, ne touchent pas `chambres` : voir leur bloc plus haut.

**Ce qu'il ne collecte pas.** L'activité en séance — le jeu ne porte ni
scrutins ni comptes rendus (condition 2 du §7 de #528, **déclarée non
remplie**) — et les trois tables de présence individuelle, refusées à l'entrée
de `senat_opendata` (§2 règle 3).
