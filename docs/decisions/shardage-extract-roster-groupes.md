<a id="shardage-extract-roster-groupes"></a>
# Shardage de `extract-roster-groupes` en 8 tranches, découpées par modulo (#394) (2026-08-18)

`2026-08-18`

> **En bref** — `extract-roster-groupes` shardé en 8 tranches par modulo.

**Contexte** : `extract-roster-groupes` traitait les 752 membres du roster dans
un job unique. Après [[index-amendements-sharde-par-acteur]] (#392), le coût
marginal mesuré est de **5,05 s/membre** (contre 11,7 s avant, [[budget-roster-mesure]] #376),
soit **63 min**
pour le roster complet — au-delà du timeout de 60 min, et surtout exposé en
totalité à une préemption runner ([[resilience-generate-data-shutdown-signal]], #228) : une
préemption à la 55ᵉ minute faisait perdre les 752 extractions.

**Décision** : découper le job en une `matrix` de 8 shards (`fail-fast: false`,
`max-parallel: 1`), chacun ~94 membres ≈ 8 min, avec **un artifact par shard**
récupéré par `merge-and-pivot` via `pattern:` + `merge-multiple: true` — le même
schéma que les shards `extract-an` (#344). Une préemption ne coûte donc plus
qu'une tranche.

**Découpage par position modulo, pas par blocs contigus** — le point non
évident. `raw_data/roster_candidats.json` est **trié par groupe parlementaire**
(vérifié : 7 blocs contigus pour 7 groupes distincts, du plus gros au plus
petit). Un découpage en tranches contiguës aurait donné des shards très inégaux
en coût, un seul héritant des ~190 membres du plus gros groupe. Le modulo
(`i % total == index`) répartit les groupes uniformément.

Cette propriété est facile à casser lors d'un refactor **sans qu'aucune
assertion de taille ne s'en aperçoive** : 752/8 = 94 tombe juste, donc un
découpage contigu produit lui aussi 8 tranches de 94. Un test dédié
(`test_select_shard_repartit_les_groupes_contigus`) vérifie donc la vraie
propriété — chaque shard voit *tous* les groupes, aucun au-delà de sa part —
sur une entrée aux tailles de groupes inégales. Vérifié discriminant : réécrit
en découpage contigu, seul ce test échoue.

**Nombre de shards paramétré à un seul endroit** : le job préparatoire
`prepare-roster-matrix` expose deux sorties, `shards` (la liste pour la matrix)
et `shard_total` (le dénominateur passé à `--shard I/N`). Une première version
recalculait le total dans l'expression du flag
(`outputs.shards == '[0]' && 1 || 8`) : dupliquer la logique ainsi garantissait
qu'un changement du nombre de shards produise un `--shard` incohérent, donc des
membres jamais extraits, **silencieusement**.

**Interaction avec le rollout progressif** : quand `roster_extraction_limit > 0`
([[limit-sample]]), le total est forcé à 1 — `--shard 0/1`
retourne la liste entière, et `--limit` s'applique ensuite comme avant. Vérifié
que le mode rollout est **strictement identique** au comportement pré-#394. Le
shardage ne s'active donc que sur un run complet (`limit = 0`), le seul cas où
il sert à quelque chose. À l'inverse, N shards en rollout multiplieraient le
volume traité, puisque `--limit` s'applique *par job*.

`--shard` est appliqué **avant** `--limit`/`--sample`/`--skip-existing`, et est
déterministe à liste source constante : un membre retombe toujours dans le même
shard, condition nécessaire pour que `--skip-existing` garde son sens d'un run
à l'autre.

**Vérification à l'exécution** (`--shard 3/376`, 2 membres) : profils complets,
108 et 115 mandats avec la taxonomie étendue de #382, 3 673 et 35 969
amendements — le chemin shardé ne dégrade rien.

---

