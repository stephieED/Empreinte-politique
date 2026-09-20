<a id="pythonunbuffered-generate-data"></a>
# `PYTHONUNBUFFERED` global sur `generate-data.yml` : stdout fiable en CI non-TTY (#259) (2026-08-13)

`2026-08-13`

> **En bref** — CPython bufferise `stdout` dès que la sortie n'est pas un TTY.

**Contexte** : CPython bufferise `stdout` par blocs (pas par ligne) dès qu'il
détecte une sortie non-TTY — le cas de tout step GitHub Actions — alors que
`stderr` n'est jamais bufferisé. Les `print()` de progression (ex.
`candidate_profile.py`, `build_amendements_index.py`) apparaissaient donc en
rafale différée en fin de step dans les logs CI, avec un ordre chronologique
trompeur déjà rencontré au cours des diagnostics #239/#241/#246/#249. Risque
aggravé : en cas de kill du job par timeout/préemption runner (angle mort
déjà documenté en [[ci-cd]]), les lignes encore en buffer stdout ne sont
jamais vidées vers le log — perte pure, contrairement à `stderr`.

**Décision** : ajouter `PYTHONUNBUFFERED: "1"` au bloc `env:` global de
`generate-data.yml`, à côté de `PARLTRACK_TIMEOUT_MINUTES` (déjà hérité par
tous les jobs) — équivalent à `python3 -u` pour tout interpréteur Python
invoqué dans le workflow, sans toucher aux scripts individuels.

**Alternatives rejetées** : `flush=True` sur chaque `print()` du code source
(dizaines de sites d'appel, oubli facile à chaque nouveau `print()`) ;
`sys.stdout.reconfigure(line_buffering=True)` par point d'entrée (même
défaut de maintenance dispersée) ; flag `-u` répété sur chaque `run:` du YAML
(redondant avec la variable d'environnement globale, à répéter sur une
dizaine de lignes). Coût du changement retenu : négligeable — sortie
strictement identique, seul l'ordre d'apparition/flush change.

