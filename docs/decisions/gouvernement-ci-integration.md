<a id="gouvernement-ci-integration"></a>
# Intégration de `generate_gouvernement_profiles.py` dans `generate-data.yml` (#215) (2026-08-14)

`2026-08-14`

> **En bref** — `generate_gouvernement_profiles.py` branché dans `merge-and-pivot`.

**Contexte** : #212 avait explicitement laissé le branchement CI hors
périmètre (voir [[quality-gate-gouvernements]], dernier paragraphe). #215
ajoute l'appel dans le job `merge-and-pivot`, juste après le step groupes
et avant le téléchargement (optionnel) de l'artifact amendements AN.

**Décision** : pas de job dédié, contrairement à `extract-amendements-an`/
`extract-parltrack`. `generate_gouvernement_profiles.py` n'a qu'un seul appel
réseau (le dump AN des dossiers législatifs, `gouvernement_textes.py`,
mutualisé pour tous les gouvernements du batch, ~10 Mo) — mesuré localement
à ~2 s à froid (téléchargement + parsing) et <0.5 s à chaud (cache
`.cache/dossiers_an/dossiers.zip` déjà présent), pour 10 gouvernements
générés à partir de 28 profils pivot locaux. Négligeable face au budget de
60 min de `merge-and-pivot` : mesuré, pas deviné (critère d'acceptation de
#215), aucun ajustement de `timeout-minutes` nécessaire.

Contrairement au step groupes (`--merge-existing` en mode `fresh_run=false`,
résilience réseau sur un roster live), le step gouvernement n'a pas
d'équivalent : `gouvernement_roster.py` n'interroge aucun réseau
(agrégation locale depuis les pivots déjà présents, voir
[[quality-gate-gouvernements]]), donc pas de FRESH-branching — le résultat
est déterministe à partir des données locales à chaque run, que `fresh_run`
soit `true` ou `false`.

`pivot_data/gouvernements` ajouté au `git add` du step de commit final, aux
côtés de `pivot_data/groupes`. La quality gate passait déjà `--gouvernements-dir`/
`--gouvernements-config` avec des défauts qui coïncidaient exactement avec
les valeurs utilisées ici ; ils sont désormais passés explicitement dans le
step CI, par cohérence avec `--groupes-dir`/`--groupes-config` (déjà
explicites) plutôt que de compter silencieusement sur les défauts du script.

*Hors périmètre* (comme #212 le précisait déjà, et non remis en cause ici) :
activation d'un `schedule:` cron pour ce nouvel appel — le `schedule:`
global du workflow reste commenté.
