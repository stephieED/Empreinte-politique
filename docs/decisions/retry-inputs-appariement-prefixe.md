<a id="retry-inputs-appariement-prefixe"></a>
# `retry-generate-data.yml` : reconstruction des inputs réparée par appariement de préfixe, collecte de jobs unifiée (#414) (2026-08-18)

`2026-08-18`

> **En bref** — le shardage a rendu les noms de jobs dynamiques : la reconstruction des inputs s'apparie sur le préfixe.

**Contexte** : le shardage d'`extract-an` (#344) et d'`extract-roster-groupes`
(#394) a donné à ces jobs un `name:` explicite — `extract-an (<slug>)`,
`extract-roster-groupes (shard N)`. Or le step « Reconstituer les inputs du run
échoué » les identifiait **par nom exact**
(`jq 'select(.name=="extract-an")'`) : plus aucun job ne portant ces noms, la
reconstruction retombait sur les défauts pour cinq des six inputs, sans rien
signaler. Ce que le fichier documentait comme une « dégradation documentée, pas
un blocage » était devenu le **chemin nominal** : un run `fresh_run=true` était
relancé en incrémental, un run `roster_extraction_limit=0` (run complet) relancé
à 20. Seul `threshold` survivait (lu sur `merge-and-pivot`, non shardé).
`workers` était doublement cassé : le matrix a aussi supprimé `--workers` de la
ligne de commande d'`extract-an` (`--only "<slug>"` remplace le parallélisme
inter-candidats), donc le motif n'existait plus, nom de job correct ou non.

**Décision** :
- **Appariement par préfixe** : `job_log()` matche `<préfixe>` ou
  `<préfixe> (…)`, et privilégie un shard dont la `conclusion` est `success` —
  le log d'un shard préempté peut être tronqué avant même la ligne `Run ...`.
  Même règle pour la lecture de `fresh_run` (conclusion du step « Nettoyage
  complet ») sur l'ensemble des shards `extract-an`.
- **`workers` est lu sur `extract-senat`**, seul job non shardé portant encore
  `--source senat --workers N`.
- **`roster_extraction_limit` est lu dans le bloc `env:` résolu**
  (`ROSTER_LIMIT: <valeur>`) plutôt que dans le stdout « Sélection … », qui ne
  rapporte que le nombre de candidats *retenus* (`min(limite, restants)`) et
  n'est pas émis du tout quand la limite vaut 0 — le cas « run complet » était
  donc irrécupérable. Le grep « Sélection » reste en repli.
- **Un seul step de collecte** (`collect`) remplace les trois listings
  `gh api .../jobs --paginate` et classe les deux motifs de relance
  (préemption runner, refus de commit pour code périmé #390) en **un seul
  passage** sur les jobs en échec, avec **un seul téléchargement par log**. La
  liste des jobs et les logs sont mis en cache dans `$RUNNER_TEMP` et réutilisés
  par la reconstruction des inputs. Le rate-limit transitoire diagnostiqué en
  #336 était un risque réel, aggravé par le shardage (8 + 8 jobs).
- Les issues `api_error` / `inconclusive` (#237) **couvrent désormais les deux
  motifs** : la détection #390 redirigeait ses erreurs vers `/dev/null` et
  n'exposait que `matched`, si bien qu'un hoquet de l'API s'y présentait comme
  « pas de #390 » plutôt que « indéterminé ».
- La reconstruction des inputs est conditionnée aux **deux** motifs, comme le
  re-déclenchement : une relance déclenchée par #390 repartait des défauts par
  construction.
- `jq -s '{jobs: [.[].jobs[]]}'` normalise la sortie de `--paginate` : au-delà
  de 100 jobs (atteignable avec le shardage), gh émet plusieurs objets JSON
  concaténés et un comptage `jq` direct produisait une valeur *par page*,
  cassant les comparaisons numériques.

*Alternative rejetée* : publier les inputs en artifact depuis
`generate-data.yml` (`echo '${{ toJson(inputs) }}' > run-inputs.json`) et les
relire via `gh run download`. Exact, insensible aux renommages de jobs et de
flags, et cela supprimerait la contrainte de ne pas factoriser les motifs
`MERGE_FLAG`/`INTERV_FLAG` sous peine de casser les greps. Écarté ici pour ne
pas modifier `generate-data.yml`, qui est le fichier le plus chargé du dépôt et
dont chaque run coûte du temps mur : le correctif reste confiné au workflow de
retry. Le couplage à la mise en forme du YAML et des `print()` Python subsiste
et reste le point faible connu de ce mécanisme.

*Alternative rejetée* : lire `workers` sur `extract-roster-groupes` ou
`merge-and-pivot`, qui portent aussi `--workers`. `extract-senat` est préféré
car non shardé (pas de sélection de shard) et non `continue-on-error` sur le
chemin critique de la relance.
