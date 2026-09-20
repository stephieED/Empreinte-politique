<a id="merge-and-pivot-budget-permissions-413"></a>
# `merge-and-pivot` : garde-fou #390 hors `main`, entrées de configuration, budget de temps mur, permissions (#413) (2026-08-18)

`2026-08-18`

> **En bref** — `merge-and-pivot` : garde-fou de code périmé hors `main`, entrées de configuration, budget de temps mur, permissions scopées.

**Contexte** : sous-issue 2/6 de [[revue-workflows-ci-342]], sur le job de fusion
de `generate-data.yml`, le budget annoncé en tête de fichier et le scoping des
permissions. Suite directe de [[concurrence-shards-extraction-412]].

## 1. Le garde-fou #390 empêchait tout commit hors `main`

`git diff "$BASE_SHA" origin/main -- src/` compare **toujours** à `main`, alors
que le workflow est déclenchable par `workflow_dispatch` sur n'importe quelle
ref — et que `retry-generate-data.yml` propage explicitement
`--ref "${{ github.event.workflow_run.head_branch }}"`. Sur un run lancé depuis
`dev` ou une branche de worktree, `$BASE_SHA` est le HEAD de cette branche : le
diff remontait **toutes** les différences entre la branche et `main`, pas les
commits arrivés *pendant* le run. Conséquence : commit annulé,
`GENERATION_CODE_CHANGED_DURING_RUN` émis, retry automatique déclenché qui
échouait à l'identique puis s'arrêtait sur le plafond d'une tentative — un run
hors `main` **ne pouvait jamais committer**, pour une raison étrangère au motif
de #390.

Corrigé en comparant à `origin/${{ github.ref_name }}` (passé par `env:`, jamais
substitué directement dans le script : un nom de branche est contrôlable par qui
déclenche le run).

**Corollaire trouvé au passage** : la boucle de retry du push avait le même
`main` en dur — `git rebase --autostash origin/main` rejouait le commit de
données par-dessus `main` au lieu de la branche poussée. Plus grave que le
garde-fou, puisque celui-ci se contente de refuser. Corrigé de la même façon.

## 2. Le garde-fou ne couvrait pas les entrées de configuration

La condition « volontairement ÉTROITE (`src/` seulement) » se justifiait par
« un commit de doc ou de données ne doit rien déclencher ». Cette phrase
confondait deux natures de données :

- les **dérivées** (`raw_data/profiles/`, `pivot_data/`), régénérées par ce job,
  dont le conflit est traité par la boucle de rebase du push ([[retry-push-merge-and-pivot-bash-e]]) ;
- les **configurations**, qui sont des *entrées* du build :
  `raw_data/candidats.json`, `raw_data/groupes_reels.json`,
  `raw_data/gouvernements_reels.json`. Un merge modifiant `groupes_reels.json`
  pendant le run faisait committer des groupes générés avec l'**ancienne**
  config — exactement le défaut que #390 veut empêcher, et sans aucune alerte.

Périmètre étendu à `src/` **+** `raw_data/*.json` **hors** `raw_data/profiles/`.

**Piège à ne pas re-découvrir** : dans un pathspec git, `*` traverse les
répertoires (pas de `FNM_PATHNAME`). `raw_data/*.json` seul matche donc les ~750
profils bruts, et le garde-fou se déclencherait sur n'importe quel commit de
données. L'exclusion explicite `:(exclude)raw_data/profiles/` n'est pas
cosmétique, elle est ce qui rend la règle utilisable.

*Alternative rejetée* : lister les trois fichiers de configuration en dur. Un
quatrième fichier de config ajouté plus tard échapperait silencieusement au
garde-fou ; le glob + exclusion couvre le cas par construction.

## 3. Le budget de temps mur annoncé était faux (190 min → 210 / 630)

L'en-tête publiait `max(30+5×8, 90, 60, 30) + 60 + 60 = 190 min`. Deux erreurs :
`max(70, 90, 60, 30)` vaut **90** (`extract-senat` était oublié du `max`), et le
terme « 60 » du roster n'est le budget que d'**un** shard depuis #394, exécutés
en série (`max-parallel: 1`, conservé en #412).

Chaîne réelle, en sommant les `timeout-minutes` : les 6 jobs sans `needs:`
finissent au plus tard à 90 (Sénat) ; `extract-an` démarre à 30 et finit à 70 ;
`extract-roster-groupes` démarre à 90 et finit à 90 + 60·S ; `merge-and-pivot`
ajoute 60. Soit **210 min** en configuration par défaut (S=1, rollout) et
**630 min (10 h 30)** en run complet (S=8). Aucune limite GitHub n'est atteinte
(6 h par *job* — le plus long est à 90 min —, 35 j par *run*) : ce n'était pas un
blocage, c'était une documentation trompeuse pour qui dimensionne un run complet.

Le commentaire distingue désormais explicitement la **somme des timeouts** (pire
cas théorique) du **temps mur observé**, bien inférieur ([[budget-roster-mesure]],
1m18–2m10 par shard AN). Les libellés `JOB 1/4`…`JOB 4/4` sont remplacés par des
rôles (`JOB PRÉPARATOIRE` / `JOB D'EXTRACTION` / `JOB FUSION`) : la numérotation
était périmée depuis #344/#394 et le redevenait à chaque ajout de job.

## 4. `contents: write` accordé aux 9 jobs

Déclaré au niveau du workflow, donc hérité partout : les 6 jobs d'extraction
exécutaient du code réseau contre des sources tierces (AN Open Data, NosDéputés,
Sénat, Parlement européen, ParlTrack) avec un token en écriture sur le dépôt dont
ils n'avaient aucun usage. Passé à `contents: read` au niveau du workflow, la
surcharge `contents: write` restant sur `merge-and-pivot` — seul job qui pousse,
et qui portait déjà une surcharge `actions: write` depuis #416.

## 5. Deux fichiers générés étaient trackés, contre ce qu'affirmait la doc

`raw_data/roster_candidats.json` et `parltrack-status.json` sont régénérés à
chaque run, et trois documents l'écrivaient noir sur blanc — mais `git ls-files`
les listait, et le step de commit ne les ajoute pas. Ils laissaient donc l'arbre
de travail sale au moment du `git rebase --autostash` du push, et la version
committée dérivait silencieusement de ce que le run venait de produire.

Décision : les **gitignorer et désindexer**, plutôt que les inclure au commit —
c'est le sens que toute la documentation leur donnait déjà, et aucun consommateur
ne les lit depuis le dépôt (`sync-data.mjs` ne copie que `raw_data/candidats.json` ;
le README et les jobs CI régénèrent le roster avant de s'en servir).

*Alternative rejetée* : les committer. Ce sont des sorties de run, pas des
sources ; les publier ajouterait du bruit de diff à chaque run et deux fichiers
générés de plus à arbitrer en cas de conflit de rebase.

## 6. Revue de l'ordre des étapes de pivot : conservé, deux points documentés

L'ordre (fusion brute → pivot candidats déclarés → pivot roster → partis →
groupes → gouvernements → quality gate → garde-fou → commit) est **conservé**.
Deux choses qui n'étaient pas écrites le sont maintenant, dans le YAML :

- **`--enrich-parltrack` seulement au premier passage** : ParlTrack est une
  source UE et le roster ne contient que des membres AN/Sénat — l'enrichissement
  n'aurait aucun pivot à enrichir au second passage. Asymétrie voulue, pas un
  oubli.
- **`merge-and-pivot` télécharge `amendements-index-an` sans `needs:
  extract-amendements-an`** : cela ne marche que par transitivité
  (`extract-roster-groupes` en dépend). Fragile si un `needs:` bouge, et la
  casse serait silencieuse puisque l'artifact est optionnel. Documenté plutôt
  que corrigé : ajouter le `needs:` direct changerait le graphe pour un gain nul
  tant que la chaîne tient.

Restent conservés sans changement, déjà commentés : candidats déclarés avant
roster (neutre grâce à la protection de provenance de `merge_pivot_profile`,
[[provenance-pivot]]) et le double appel de `generate_roster_candidats.py`.

## 7. `--groupe-min-coverage-pct` : pas un réglage en attente d'arbitrage

Le commentaire `# To be set after running and audit of workflow (cf. #193)`
pointait vers une issue **close**, laissant croire qu'un réglage traînait. #193 a
été tranchée par [[seuil-couverture-groupe]] : garder `--groupe-min-members 1`,
et n'activer le seuil relatif que lorsqu'un run à pleine échelle
(`roster_extraction_limit=0`) aura fourni des taux représentatifs — les chiffres
à regarder étant `taux_couverture_pct` dans `coherence.ecart_couverture_roster`
(`audit_groupe_dataset.py`). Le commentaire renvoie désormais à cette décision et
à la donnée qui la débloquera, au lieu d'un chantier terminé.

