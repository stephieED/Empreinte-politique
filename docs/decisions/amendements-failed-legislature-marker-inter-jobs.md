<a id="amendements-failed-legislature-marker-inter-jobs"></a>
# Marqueur disque inter-jobs pour le cache d'échec amendements par législature (#246) (2026-08-13)

`2026-08-13`

> **En bref** — marqueur disque inter-jobs pour l'échec d'une législature d'amendements.

**Contexte** : [[amendements-retry-blocage-legislature]] (#239) mémorise en
mémoire process (`_amendements_failed_legislatures`) qu'une législature
d'amendements a définitivement échoué, pour que seul le premier candidat
rencontrant l'échec paie le cycle complet de retry. Ce cache est scopé au
process Python — or `extract-an` et `extract-roster-groupes` sont deux jobs
CI distincts (deux process), séquencés sur le même cache disque partagé
`public-data-cache-an-*` par [[concurrence-ci-roster]] (#222). Sur le run #30
(https://github.com/stephieED/Empreinte-politique-src/actions/runs/31685914622),
`extract-an` a épuisé ses tentatives dès le premier segment sur les
législatures 17/16/15 (`IncompleteRead` immédiat, aucun `index_par_acteur.json`
mis en cache) sans que `extract-roster-groupes`, quelques minutes plus tard
dans le même run, en garde aucune mémoire : son premier candidat AN a donc
retenté les trois législatures depuis zéro, cette fois en stallant réellement
jusqu'au timeout de lecture (`AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS = 120`
× `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS = 3` ≈ 6 min), consommant l'écart de
6m48s observé avant que le job soit tué par la préemption runner déjà
documentée ([[retry-generate-data-preemption]]). Cause distincte du gap de
visibilité tracé par #245 ([[retry-generate-data-continue-on-error]]) : ici
c'est le temps de blocage lui-même qui est payé deux fois dans le même run.

**Décision** : `_build_acteur_amendement_index` écrit désormais, en plus du
cache mémoire process (#239 conservé tel quel comme raccourci intra-process),
un marqueur disque `.cache/amendements_an/<legislature>/failed_run_id`
contenant `GITHUB_RUN_ID` quand les tentatives sont épuisées pour une
législature. Avant toute tentative réseau, ce marqueur est consulté après le
cache mémoire : s'il existe et référence le `GITHUB_RUN_ID` courant, échec
immédiat identique au cache mémoire de #239 ; s'il référence un
`GITHUB_RUN_ID` différent (résidu d'une semaine ISO précédente via
`restore-keys`), il est ignoré et la législature retentée normalement —
préserve intentionnellement le comportement de #239 (un run suivant repart de
zéro) sans TTL explicite à maintenir. Le marqueur vit dans le même
sous-répertoire que `index_par_acteur.json`, donc profite du même
restore/save de cache disque déjà séquencé par #222 : aucun changement de
workflow CI nécessaire.

*Hors périmètre (reporté)* : réduire davantage
`AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS` (120s → 60s), qui réduirait le
pire cas payé par le *premier* job du run à rencontrer une législature qui
stalle réellement (ce correctif élimine la répétition entre jobs, pas le coût
initial de découverte) — proposé dans l'issue comme optionnel, à évaluer
séparément si ce coût initial redevient un problème en pratique.

