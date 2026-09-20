<a id="matrix-extract-an-par-candidat"></a>
# `extract-an` en matrix strategy par candidat, pour isoler la perte en cas de shutdown signal runner (#344) (2026-08-16)

`2026-08-16`

> **En bref** — `extract-an` en matrix par candidat, pour isoler la perte en cas de `shutdown signal` runner.

**Contexte** : prolonge l'option 1, différée et non rejetée par
[[resilience-generate-data-shutdown-signal]] (angle mort du `runner shutdown
signal` sur `if: always()`, #228) — un seul `extract-an` séquentiel sur toute
`raw_data/candidats.json` perd la progression de *tous* les candidats déjà
traités ce run dès qu'un `shutdown signal` gèle le runner, pas seulement
celle du candidat en cours. Périmètre volontairement limité à `extract-an`
(liste éditoriale, 13 entrées / 8 à slug résolvable) ; `extract-roster-groupes`
(~750 membres) reste hors périmètre, l'urgence y étant limitée tant que
`roster_extraction_limit` reste à 20 ([[seuil-couverture-groupe]]).

**Décisions, sous-questions par sous-questions** :
1. **Granularité : un job par candidat, pas de lot.** `--only <slug>`
   (`generate_all_profiles.py`) filtre déjà nativement sur un seul candidat —
   aucun changement Python nécessaire. Un lot de 2-3 candidats n'aurait rien
   apporté ici : avec `max-parallel: 1` (décision 2), les shards s'exécutent
   déjà en série, donc le temps mur total est indépendant de la granularité
   (identique en shards de 1 ou de 3) — seule la *perte maximale par
   incident* varie, et un shard de 1 la borne au minimum possible.
2. **`max-parallel: 1`.** Le pic de jobs concurrents a été explicitement
   plafonné à 4 par #222 ([[concurrence-ci-roster]]). `extract-an` fait déjà
   partie de ce pic de 4 (concurrent à Sénat/UE/ParlTrack une fois
   `extract-amendements-an` terminé) : plusieurs shards en parallèle entre
   eux le dépasseraient mécaniquement. `max-parallel: 1` préserve l'invariant
   de #222 à l'identique, au prix du temps mur (accepté explicitement par
   l'issue #344 — "moins de jobs concurrents, plus de temps mur en échange").
   Une valeur plus élevée reste une option future si le pic de 4 est
   lui-même revisité, pas un choix isolé de ce chantier.
3. **Cache AN (`public-data-cache-an-*`) : clé partagée inchangée, pas de
   clé par shard.** La course déjà documentée en #248 sous-issue 4
   ([[amendements-index-budget-ci-cache-granularite]]) n'est pas aggravée :
   `extract-an` reste chaîné après `extract-amendements-an` (`needs:`
   inchangé), et `max-parallel: 1` fait que les shards restaurent/écrivent
   cette clé en série entre eux, pas en concurrence nouvelle.
4. **Nommage des artifacts : `raw-profiles-an-<slug>`, scopés au seul fichier
   du candidat** (`raw_data/profiles/<slug>.json`, pas tout le dossier).
   `merge-and-pivot` reste correct sans dupliquer la baseline dans chacun des
   8 shards : les jobs Sénat/UE/roster uploadent déjà, eux, l'intégralité de
   `raw_data/profiles/` (baseline committée + leur propre mise à jour), donc
   la baseline complète leur parvient toujours par ces 3 autres sources.
   `actions/download-artifact@v7` supporte `pattern: raw-profiles-an-*` +
   `merge-multiple: true` pour aplatir les N artifacts en un seul dossier —
   pas besoin d'un step par shard connu à l'avance.
5. **`needs:` de `extract-roster-groupes`/`merge-and-pivot` : inchangé
   (`needs: [..., extract-an, ...]`), pas de job de synthèse
   intermédiaire.** GitHub Actions résout nativement `needs: [extract-an]`
   comme une dépendance sur la *totalité* du matrix (tous les shards),
   pas sur une seule combinaison — un agrégateur dédié aurait été redondant.
6. **`continue-on-error: true` conservé au niveau du job (donc appliqué par
   shard automatiquement), plus `strategy.fail-fast: false` ajouté.**
   Sémantique identique une fois multiplié : l'échec d'un shard ne bloque
   jamais `merge-and-pivot`. Point de vigilance identifié en écrivant ce
   matrix et absent de la liste initiale de sous-questions : sans
   `fail-fast: false` explicite (le défaut GitHub Actions est `true`), un
   shard en échec aurait annulé tous les shards restants du matrix — ce qui
   aurait annulé l'intégralité du bénéfice d'isolation recherché par #344.
7. **Commentaire de budget mur mis à jour** en tête de `generate-data.yml` :
   timeout 20 min/shard (vs 120 min pour le job unique), 8 shards en série
   (`max-parallel: 1`) → ≈160 min pire cas pour le segment AN (vs 120 min
   avant), total mur pire cas ≈310 min (vs 270 min avant #344) — hausse de
   ~15%, cohérente avec le compromis accepté en décision 2. Formule non
   figée : dépend de `nb_candidats_a_slug`, à recalculer si
   `raw_data/candidats.json` change significativement.

**Job préparatoire ajouté : `prepare-an-matrix`.** Le matrix doit être connu
avant le démarrage du job (limite structurelle de `strategy.matrix` en
GitHub Actions), donc un job amont léger (checkout + un script Python
utilisant uniquement la bibliothèque standard, pas de `pip install`) lit
`raw_data/candidats.json` et expose en sortie (`outputs.slugs`) la liste JSON
des slugs non-null, consommée via
`fromJson(needs.prepare-an-matrix.outputs.slugs)`. Les candidats sans slug
sont exclus du matrix plutôt que de générer un shard qui n'écrirait jamais de
fichier (`--source an` sans slug ne peut interroger aucune chambre FR, et ne
déclenche jamais la recherche UE — voir `process_candidat`/`_fetch_ue` dans
`generate_all_profiles.py`) : comportement équivalent au job séquentiel
précédent, qui traitait ces candidats en no-op silencieux (`statut:
introuvable`, aucun fichier écrit).

*Coût accepté, non optimisé ici* : le step "Download artifact amendements AN
(optionnel)" (cache-only, #251/#252) s'exécute maintenant une fois par shard
au lieu d'une fois par job — léger surcoût réseau répété 8 fois plutôt qu'une,
jugé négligeable (artifact index, pas les dumps AN Open Data volumineux) au
regard du bénéfice d'isolation. *Edge case non géré explicitement* : si
`raw_data/candidats.json` ne contient plus aucun slug résolvable, le matrix
serait vide et `extract-an` ne produirait aucune exécution — scénario jugé
irréaliste en pratique (liste éditoriale activement maintenue, 8/13 slugs
résolvables aujourd'hui) et non traité pour éviter la validation
prématurée que proscrit AGENTS.md.

**Retour d'expérience sur le premier run réel, et correctif appliqué** : ce
premier run s'est terminé `cancelled` après 44m55s, sans jamais atteindre
`merge-and-pivot` (skipped). Sur 8 shards (`max-parallel: 1`, séquentiel) :
2 succès (Bruno Retailleau, Jordan Bardella — tous deux *non* rattachés à
l'Assemblée nationale, `Aucune identité trouvée`, shard fini en ~15-20s
avant toute exposition réelle), 5 échecs par la signature `shutdown signal`
habituelle (1m18s-2m10s chacun, cohérent avec tous les runs déjà observés
avant ce chantier), et 1 blocage anormal (Jérôme Guedj, 20+ min, **sans**
signature `shutdown signal` reconnaissable — logs expirés avant
investigation possible, cause non identifiée) qui a immobilisé tous les
shards suivants derrière lui (séquentiel, décision 2 ci-dessus).

Proposition initiale d'augmenter `max-parallel` (pour réduire le temps mur
et limiter l'impact d'un shard bloqué) — **écartée** sur retour d'expérience
direct de l'utilisatrice : une parallélisation antérieure d'appels vers une
même source de données s'était révélée peu robuste. Risque jugé réel : si
une partie du phénomène `shutdown signal` est liée au volume/à la charge sur
nosdeputes.fr plutôt qu'à un aléa runner pur (question non tranchée, voir le
workflow de debug ci-dessous), plus de parallélisme pourrait aggraver la
fréquence des gels plutôt que la réduire. `max-parallel` reste donc à `1`,
la décision 2 ci-dessus n'est pas remise en cause.

**Correctif retenu et implémenté à la place** : réduire `timeout-minutes`
d'`extract-an` de 20 à 5 min. Preuve à l'appui : tous les shards observés à
ce jour (succès et échecs confondus) se terminent en 1m18s-2m10s, sans
exception sauf le cas anormal de Guedj — 5 min laisse une marge large (>2x
le pire cas normal) tout en bornant à 5 min (au lieu de 20+) l'impact d'un
futur blocage du même type sur le matrix séquentiel. Budget mur en tête de
fichier recalculé en conséquence (décision 7 ci-dessus) :
`max(30+5×8, 90, 60, 30) + 60 + 60 = 190 min` pire cas (contre 310 min avec
l'ancien timeout de 20 min/shard).

**Piste de recherche ouverte en parallèle, non tranchée** : un workflow de
debug dédié (`.github/workflows/debug-network-shutdown-signal.yml`), isolé
de la production (aucun checkout de données, aucun commit, aucun artifact),
compare à volume de requêtes identique un groupe test vers nosdeputes.fr et
un groupe témoin vers `api.github.com` — objectif : déterminer si le
`shutdown signal` est corrélé au volume/temps d'activité réseau soutenue
depuis le runner (indépendamment de la destination) ou spécifique à
nosdeputes.fr. Premier run (20 requêtes/groupe, délai 0,3s) : succès complet
des deux côtés, aucun gel — attendu, le phénomène étant probabiliste ;
plusieurs runs par palier de volume restent nécessaires avant de pouvoir
conclure.

