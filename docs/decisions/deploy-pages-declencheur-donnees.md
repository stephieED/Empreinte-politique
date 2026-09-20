<a id="deploy-pages-declencheur-donnees"></a>
# Publication du site après un run de données : le commit du bot n'émet aucun événement `push` (#416) (2026-08-18)

`2026-08-18`

> **En bref** — un commit poussé par le `GITHUB_TOKEN` n'émet aucun événement `push` : la publication du site doit être déclenchée autrement.

**Contexte** : les données du site sont figées **au build**. `npm run build`
= `npm run sync-data && vite build`, et `web/UI_finale/scripts/sync-data.mjs`
copie `pivot_data/` + `raw_data/candidats.json` vers
`web/UI_finale/public/data/` (dossier gitignoré) que Vite embarque dans
`dist/` ; le front les lit ensuite à l'exécution via
`fetch('/data/manifest.json')`. Un run de génération qui met à jour les
données n'est donc visible en ligne qu'après un **nouveau build**.

`deploy-pages.yml` ne se déclenchait que sur un `push` sur `main` touchant
`web/UI_finale/**` ou son propre fichier. Le commit produit par
`merge-and-pivot` (`chore: mise à jour automatique des données (…)`) ne touche
que `raw_data/profiles` et
`pivot_data/{profiles,partis,groupes,gouvernements}` — aucun chemin
déclencheur. Constaté le 18/08/2026 : `main` portait un commit de données du
jour, le dernier run `deploy-pages.yml` datait du 2026-08-17T23:53. Les
données finissaient par arriver en production, mais **par coïncidence**, à la
prochaine modification de `web/UI_finale/`.

**Le point non évident** : élargir les `paths:` ne suffit pas. Le push de
`merge-and-pivot` est fait avec le `GITHUB_TOKEN` par défaut (credentials
persistées par `actions/checkout`), et GitHub n'émet **aucun** événement
déclencheur pour une action effectuée avec ce token — protection anti-boucle.
Le commit du bot ne peut donc structurellement pas déclencher un workflow
`on: push`, quels que soient ses `paths:`. Vérifié sur l'historique des runs :
**zéro** run, tous workflows confondus, n'a jamais eu pour déclencheur un
commit `chore: mise à jour automatique des données`. Une correction limitée
aux `paths:` aurait été livrée, mergée, et n'aurait rien changé — sans signal
visible d'échec.

**Décision** — les deux moitiés, complémentaires :

1. `deploy-pages.yml` : ajout de `pivot_data/**` et `raw_data/candidats.json`
   aux `paths:`. Couvre les pushs **humains** (merge de PR) qui touchent les
   données — un cas réel, distinct du commit du bot.
2. `generate-data.yml` (job `merge-and-pivot`) : après un push de données
   réussi, une étape déclenche explicitement
   `gh workflow run deploy-pages.yml --ref main`. `workflow_dispatch` (comme
   `repository_dispatch`) est l'exception documentée à la règle anti-boucle :
   un dispatch émis avec le `GITHUB_TOKEN` démarre bien un run. Même mécanique
   que le re-déclenchement de `generate-data.yml` par
   `retry-generate-data.yml` (voir [[retry-generate-data-preemption]]).

   L'étape est gardée par un output `pushed` du step de commit (`true`
   uniquement si `git push` a réussi ; `false` s'il n'y avait rien à
   committer) **et** par `github.ref == 'refs/heads/main'` — un run de
   génération lancé depuis une branche de travail ne doit jamais publier le
   site de production. L'output est écrit **avant** chaque `exit 0` du step :
   `exit` termine le step immédiatement, une écriture placée après ne serait
   jamais faite.

**Permissions** : `pages: write` et `id-token: write` étaient déclarés au
niveau workflow dans `deploy-pages.yml`, donc hérités par `build`, qui ne fait
que `npm ci && npm run build` + `upload-pages-artifact`. Un job qui exécute
`npm ci` sur des dépendances tierces ne doit pas porter `id-token: write`.
Désormais : `contents: read` au niveau workflow, `contents: read` +
`pages: read` sur `build` (`actions/configure-pages` lit la configuration
Pages du dépôt via l'API — la lecture seule suffit), `pages: write` +
`id-token: write` sur le seul job `deploy` (qui ne checkoute pas, donc pas de
`contents:`). De même, `actions: write` (requis par le `gh workflow run`) est
déclaré sur le seul job `merge-and-pivot` de `generate-data.yml`, pas au
niveau workflow : les jobs d'extraction n'ont aucune raison de pouvoir
déclencher un workflow.

*Question tranchée — pas de `concurrency` distinct pour les runs de données* :
le groupe `pages` avec `cancel-in-progress: false` **sérialise déjà** un
déploiement déclenché par les données et un déploiement déclenché par un
changement d'UI ; ils ne peuvent pas se marcher dessus. Deux groupes séparés
feraient exactement l'inverse — ils autoriseraient deux déploiements
concurrents vers le même site. Conservé tel quel.

*Alternative rejetée* : déclencher `deploy-pages.yml` sur
`workflow_run: [Génération des données]`, comme `retry-generate-data.yml`.
Rejeté : `workflow_run` se déclenche sur la **conclusion du run**, pas sur le
fait qu'un commit de données ait été poussé. Un run réussi sans changement de
données (« Aucun changement de données à committer »), ou dont le commit a été
refusé par la garde de code périmé (#390), lancerait un déploiement inutile.
Le dispatch depuis le step de push est conditionné à ce qui compte réellement :
un push effectif.

*Alternative rejetée* : un PAT à la place du `GITHUB_TOKEN` pour le push, afin
que l'événement `push` soit bien émis. Rejeté : introduit un secret à gérer et
à faire tourner, et rouvre le risque de boucle que la règle GitHub prévient,
pour un gain nul par rapport au dispatch explicite.

`timeout-minutes: 10` ajouté sur les deux jobs de `deploy-pages.yml`
(auparavant le défaut de 360 min), par cohérence avec `generate-data.yml` —
`build` tourne en ~35 s et `deploy` en ~11 s sur les runs récents, la marge
couvre la croissance du volume de `pivot_data` copié dans `dist/`.

**Relu sans changement** : `debug-network-shutdown-signal.yml`, hors de
l'inventaire de #342 (rédigé quand le dossier comptait 5 workflows). Workflow
de diagnostic isolé — `workflow_dispatch` seul, aucune donnée touchée, aucun
commit, aucun `needs` vers le pipeline de production. Rien à corriger.

**À valider par un run réel** : le prochain `generate-data.yml` sur `main` qui
pousse des données doit faire apparaître, dans la foulée, un run
`deploy-pages.yml` déclenché par `workflow_dispatch`.
