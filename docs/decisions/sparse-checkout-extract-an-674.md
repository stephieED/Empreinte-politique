# Un shard d'extraction ne matérialise que son propre profil (#674) — 31/08/2026

`2026-08-31`

> **En bref** — le run `33404236969` a tué ses **13 shards `extract-an`** l'un après l'autre à 5 min 00 **dans `actions/checkout`**, l'étape d'extraction restant `skipped` : aucun profil écrit, 40 minutes pour rien, le défaut de #498 ; ce n'était pas le réseau — le checkout valait **4 min 52 à 6 min 03 dans tous les jobs du run**, `extract-an` étant seulement le seul à `timeout-minutes: 5` — mais le poids de l'arbre, **8 483 Mio dont 7 525 pour le seul `raw_data/profiles/`** (1 503 fichiers), là où le garde-fou de #580 surveille le plus gros FICHIER et rien du total ; le checkout passe donc en liste blanche avec `filter: blob:none` (patron de `tests.yml`) et ne matérialise que le code, les référentiels, les index figés et **le seul profil du shard** — socle et tranches (#580), 16,4 Mio au pire contre 7 525 —, ce que légitime le fait que `--only` filtre sur `raw_data/candidats.json` et que `slugs_du_repertoire` ne soit appelée que par des scripts de migration et d'audit ; `timeout-minutes` reste à 5, un cas de test échouant si on le relève, parce que relever le plafond ne supprime pas la cause, coûte les ~65 min de checkout des 13 shards en série et tombe sous l'interdit de §3b ; le garde-fou échoue **localement** sur la fermeture des imports du point d'entrée — la prose et les docstrings écartées (le motif attrapait des phrases), le chemin borné au premier caractère non-chemin (des messages nomment un fichier puis continuent la phrase), et un seul bloc `sparse-checkout: |` toléré puisque le parseur rend le premier — parce qu'ici un référentiel absent ne lève pas toujours mais **se replie** (#525) et publie moins sans rien casser ; `extract-roster-groupes` et `merge-and-pivot` paient le même checkout sans en mourir, et le total du dépôt reste sans surveillance : nommés, hors lot.

## Contexte

Le run `33404236969` a tué ses **13 shards `extract-an`** l'un après l'autre à
**5 min 00**, dans `actions/checkout`. L'étape « Extraction AN » est restée
`skipped` sur chacun : **aucun profil écrit**, le défaut nommé en #498 et
rappelé par `AGENTS.md` §3b. Avec `max-parallel: 1`, 40 minutes pour rien.

Ce n'était pas le réseau. Le checkout du même run valait **4 min 52 à 6 min 03
dans tous les jobs** ; `extract-an` est seulement le seul à `timeout-minutes: 5`.

La cause est le **poids de l'arbre**, mesuré à `501c6997` :

| Chemin | Poids | Fichiers |
| --- | ---: | ---: |
| arbre entier | **8 483 Mio** | 2 752 |
| `raw_data/` | 7 566 Mio | 1 522 |
| **`raw_data/profiles/`** | **7 525 Mio** | **1 503** |

Le garde-fou de #580 surveille le **plus gros fichier** — 50 Mio d'alerte,
80 Mio d'échec du commit. **Aucun garde-fou ne surveille le total**, et c'est le
total qui a franchi le seuil. Le franchissement ne s'est signalé nulle part : il
s'est manifesté comme une série d'annulations, c'est-à-dire sous la forme la
plus facile à prendre pour un incident d'infrastructure.

## Décision

Le checkout d'`extract-an` porte une **liste blanche** et `filter: blob:none`,
sur le patron déjà en place dans `.github/workflows/tests.yml`. Un shard
matérialise le code, les référentiels de premier niveau, les index figés — et
**son seul profil brut**, socle `<slug>.json` plus tranches
`<slug>/<legislature>.json` (#580).

**Le `timeout-minutes: 5` ne bouge pas.** Le lot supprime la cause ; le desserrer
serait soigner le symptôme, et `AGENTS.md` §3b l'interdit isolément (#498). Un
cas de test échoue si quelqu'un le relève.

### Ce qui rend la réduction légitime

`generate_all_profiles.py --source an --only <slug>` filtre les candidats sur
`raw_data/candidats.json`, **jamais sur le répertoire de profils**. La seule
énumération de ce répertoire, `profil_brut.slugs_du_repertoire`, n'est appelée
que par `migrer_absences_publiees_556_558_560.py`,
`migrer_profils_partitionnes_580.py` et `scripts/audit_fusion_blocs_599.py` —
aucun n'est exécuté par le shard.

Le plus gros candidat pèse **16,4 Mio** contre 7 525 pour le répertoire entier.

### Le garde-fou, et pourquoi il ne ressemble pas à celui de `tests.yml`

Le risque de la liste blanche est connu et documenté : un chemin oublié **passe
en local et échoue en CI** — #434, #518 deux fois, #520.

Ici il est pire. Dans `tests.yml`, un fichier absent lève un `FileNotFoundError`,
donc échoue. Dans la collecte, **un référentiel absent se replie** :
`correspondance_acteurs_an.json` a un repli *déclaré* (#525), et une collecte
qui se replie publie moins **sans que rien n'échoue**. C'est la forme silencieuse
du même défaut.

`tests/test_ci_sparse_checkout_extract_an.py` échoue donc **localement**, et il
ne devine pas ce que le shard lit : il calcule la **fermeture des imports** de
`src/generate_all_profiles.py` restreinte à `src/`, puis relève dans ces seuls
modules les littéraux de chemin sous `raw_data/`. Un module de migration n'entre
pas dans le périmètre ; un nouvel import l'y fait entrer tout seul.

Trois précautions valent d'être notées, chacune venue d'un échec observé en
écrivant le test :

1. **La prose est écartée**, docstrings comprises. Les deux premiers chemins
   relevés l'avaient été dans une phrase, pas dans un appel — et un garde-fou
   qui échoue sur une phrase se fait désarmer. Même règle qu'en #529.
2. **Le motif de chemin s'arrête au premier caractère non-chemin.** Plusieurs
   messages destinés à l'utilisatrice nomment un fichier *puis continuent la
   phrase* ; sans cette borne, le chemin relevé était la phrase entière.
3. **Un seul bloc `sparse-checkout: |` est toléré dans le workflow.**
   `_outils_ci.lire_liste_blanche` rend le premier : le jour où un autre job en
   reçoit un, ce test croirait vérifier `extract-an` sans rien dire.

Une étape « Périmètre du checkout » imprime en outre le poids matérialisé et
**échoue** si un référentiel indispensable manque — la liste blanche se relit
donc aussi dans le journal du run, pas seulement dans le YAML.

## Alternative écartée : relever `timeout-minutes`

Écartée pour trois raisons, dans cet ordre.

1. **Elle ne supprime pas la cause.** `raw_data/` grossit à chaque run ; le seuil
   serait refranchi, et le même symptôme reviendrait sous la même forme
   trompeuse.
2. **Elle coûte le temps qu'elle prétend acheter.** À 5-6 min de checkout par
   shard et 13 shards en série, ce sont **~65 minutes de temps mur** dépensées à
   matérialiser 7,5 Gio dont le shard lit quelques mégaoctets.
3. **`AGENTS.md` §3b l'interdit isolément.** Relever `timeout-minutes` sans
   toucher `--budget-interventions-secondes` est précisément ce que #498 a
   consigné, et l'interlock est vérifié par
   `tests/test_ci_budget_interventions.py`.

## Première application incomplète, corrigée le jour même

**La première application n'a couvert qu'`extract-an`, et c'était faux.**
`prepare-an-matrix` porte le même `timeout-minutes: 5` : le run
`33414042623`, lancé une heure après la fusion, l'a vu tué à **5 min 00 dans
`actions/checkout`**, donc matrice jamais publiée, donc `extract-an` **skippé** —
le job réparé n'a même pas démarré, et le run n'a rien collecté côté AN.

L'erreur de raisonnement est nommable : le run précédent avait vu
`prepare-an-matrix` réussir **à 4 min 52**, huit secondes sous le plafond. J'ai
lu ce succès comme une propriété du job alors qu'il n'était qu'une marge, et
j'ai réparé le seul job qui avait échoué. **La cause n'est propre à aucun job**
— c'est le poids de l'arbre, et tout job au budget serré la rencontre.

Le garde-fou en tire la règle générale plutôt que la liste des coupables :
`test_tout_job_au_budget_serre_porte_une_liste_blanche` exige une liste blanche
de **tout** job dont le `timeout-minutes` littéral est ≤ 10 — seuil posé à 10 et
non à 5 pour garder une marge, aucun job ne se situant entre 6 et 15 minutes. Un
`timeout-minutes` calculé par expression n'est pas évaluable là : il est signalé
**non vérifiable** plutôt que supposé conforme.

`prepare-an-matrix` ne lit qu'un fichier, `raw_data/candidats.json`, en `python3`
système, sans dépendance ni action locale.

## Ce que ce lot ne traite pas, et le dit

`extract-roster-groupes` (60 min), `merge-and-pivot` (60), `extract-ue-officiel`
(60), `extract-parltrack` (30), `extract-amendements-an` (30) et
`prepare-roster-matrix` (15) paient le même checkout. Ils y survivent, mais la
dépense est identique, et `prepare-roster-matrix` est le plus proche du seuil.
`merge-and-pivot` a besoin du corpus entier — sa réduction, si elle est possible,
n'est pas la même question. Instruire séparément.

**Et le total du dépôt reste sans garde-fou.** #580 surveille le plus gros
fichier ; personne ne surveille les 8 483 Mio. Ce lot rend le symptôme
inoffensif pour `extract-an` ; il ne rend pas la croissance visible.
