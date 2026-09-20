<a id="cache-cle-amendements-separee"></a>
# Cache CI : clé propre aux amendements, et chemins énumérés pour les jobs AN (#424) (2026-08-18)

`2026-08-18`

> **En bref** — deux jobs qui partagent une clé se privent mutuellement de sauvegarde.

**Contexte** : `extract-amendements-an`, `extract-an` et `extract-roster-groupes`
partageaient la clé `public-data-cache-an-<semaine>` avec `path: .cache`. Le
premier étant séquencé en tête, il écrivait la **clé exacte** de la semaine ;
les deux autres faisaient alors un *exact key hit*, et `actions/cache` saute sa
sauvegarde post-job dans ce cas.

#412 §2.3 avait posé l'hypothèse sans la corriger, faute de preuve — décision
qui s'est révélée juste, puisqu'elle a produit un critère d'acceptation net.
Le run `32136438841` a fourni la preuve :

```
extract-an (gabriel-attal) | Post Run actions/cache@v5
  Cache hit occurred on the primary key public-data-cache-an-2026-W34, not saving cache.
```

sur **les 8 shards `extract-an` et le shard `extract-roster-groupes`**.

**Coût mesuré sur ce seul run** (rollout progressif, 1 shard roster) : 11
téléchargements de l'archive dossiers XV (14,5 Mo), 9 de la XVI (8,7 Mo) et 8
des scrutins XVII (25,1 Mo), soit **~438 Mo re-téléchargés**. À pleine échelle
du roster, 16 jobs seraient concernés, donc **~780 Mo par run**.

Le coût avait **augmenté après** la rédaction de la réserve : [[dossiers-multi-archives-origine-document]]
(#400) a ajouté les dossiers XV/XVI et #403 les scrutins XIV–XVII à `.cache`.
Une réserve laissée en l'état vieillit mal quand d'autres chantiers alimentent
le répertoire qu'elle concerne.

**Décision** :

- `extract-amendements-an` reçoit sa propre clé `public-data-cache-amendements-*`,
  avec `path: .cache/amendements_an` — le seul répertoire qu'il produise.
- `extract-an` et `extract-roster-groupes` gardent `public-data-cache-an-*` mais
  **énumèrent explicitement** leurs répertoires (`acteurs_historique_an`,
  `dossiers_an`, `scrutins_an`, `questions_an`, `syceron_an`).

**Pourquoi énumérer plutôt que garder `path: .cache`** : `.cache` englobe
`amendements_an`. Conserver le chemin large aurait fait ré-embarquer les
amendements par les jobs AN, déplaçant le problème au lieu de le résoudre —
c'est le piège principal de ce correctif.

**Le revers, et son garde-fou** : un nouveau `.cache/<quelque_chose>` ajouté
côté Python ne serait pas caché, **sans qu'aucun signal ne l'indique** — le
pipeline continuerait de tourner, simplement plus lentement. `tests/test_ci_cache_paths.py`
vérifie donc que tout répertoire `.cache/*` déclaré dans `src/` est couvert par
un `actions/cache`, et que les deux jobs AN cachent **exactement le même
ensemble** (une divergence signifierait que l'un re-télécharge ce que l'autre a
persisté).

Sa première version comparait les répertoires au fichier entier : retirer un
chemin d'**un seul** job passait inaperçu, puisque l'autre le mentionnait
encore. Vérifié par sabotage, corrigé en analyse par job.

**Repli sur l'artifact** : `extract-an` et `extract-roster-groupes` reçoivent
les amendements par l'artifact `amendements-index-an` (#251) et s'appuyaient,
en cas d'absence, sur le cache partagé — qui ne les contient plus. Un
`actions/cache/restore` (lecture seule) a donc été ajouté, **conditionné à
l'échec du téléchargement de l'artifact** : restaurer 676 Mo dans chaque shard
pour un cas rare recréerait le coût que cette issue supprime.

**Effet de bord traité** : `extract-ue-officiel` cachait aussi `.cache` en bloc
sous sa propre clé, y embarquant les données AN et amendements présentes. Le
quota de cache d'un dépôt étant partagé, une entrée surdimensionnée provoque
l'éviction LRU des autres — dont la clé AN que ce correctif vient de réparer.
Son `path` est resserré sur `.cache/europarl`.

`extract-senat` garde `path: .cache` : ce job n'écrit **rien** sous `.cache`,
son entrée ne recopie donc que ce que la restauration y a placé. Laissé en
l'état plutôt que supprimé — retirer une entrée de cache est une décision de
comportement, pas un effet de bord de cette issue.

**Critère d'acceptation** : le post-job de `extract-an` doit afficher
`Cache saved with key: …` et non `not saving cache`. L'hypothèse ayant déjà
survécu une fois à l'analyse statique seule, seul un run réel tranche.

---

