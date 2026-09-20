<a id="retry-generate-data-best-effort-non-bloquant"></a>
# `retry-generate-data.yml` : le step best-effort d'extraction des inputs ne doit pas pouvoir bloquer le retry (#336) (2026-08-16)

`2026-08-16`

> **En bref** — un step best-effort d'extraction des inputs ne doit pas pouvoir bloquer le retry.

**Contexte** : [[retry-generate-data-preemption]] (#230) déclenche le retry
réel (step *« Re-déclencher generate-data.yml »*) uniquement via `if:
steps.signature.outputs.matched == 'true'`, sans `always()` — GitHub Actions
y ajoute donc implicitement `success()`. Sur les runs #35/#36 (2026-08-15T22:55:56Z
et 2026-08-16T05:26:00Z), la signature de préemption runner est correctement
détectée (`matched=true`) mais le step intermédiaire *« Reconstituer les
inputs du run échoué (best-effort) »* échoue en ~1,5s sans sortie visible
dans les logs — cohérent avec un échec précoce d'un appel `gh api`,
probablement un rate-limit transitoire déclenché par l'enchaînement de
plusieurs téléchargements complets de logs de jobs entre le step de détection
et ce step (jusqu'à 3-4 en l'espace d'une seconde). Ce step est documenté
comme *best-effort* (dégradation vers les valeurs par défaut, cf. commentaire
existant), mais deux défauts en faisaient un point de blocage réel : (1)
`jobs_json=$(gh api ".../jobs" --paginate)` n'avait aucune garde sous `set
-euo pipefail`, contrairement aux appels de `job_log()` (`2>/dev/null ||
true`) — un seul hoquet API faisait échouer tout le step ; (2) le step
suivant héritait de `success()` sur ce step best-effort, donc son échec
skippait le retry réel lui-même, alors même que la signature de préemption
avait été identifiée avec certitude. Résultat : deux runs consécutifs sans
aucun retry automatique tenté, le filet de sécurité de #230 étant
silencieusement inopérant sur ce mode de défaillance précis.

**Décision** :
1. `jobs_json=$(gh api ".../jobs" --paginate)` du step best-effort est
   désormais gardé avec le même pattern que le step de détection (`if ! cmd;
   then ::warning:: + repli; fi`) — un hoquet API dégrade vers une liste de
   jobs vide (`jobs_json='{"jobs": []}'`) au lieu de faire échouer tout le
   step ; `job_log()` traite déjà correctement une liste vide (id introuvable
   → chaîne vide).
2. Le step *« Re-déclencher generate-data.yml »* passe à `if: always() &&
   steps.signature.outputs.matched == 'true'` — découplé du succès du step
   best-effort. Les inputs passés à `gh workflow run` utilisent désormais le
   fallback d'expression GHA `${{ steps.inputs.outputs.X || 'défaut' }}` (pas
   seulement les `${var:-default}` bash internes au step best-effort, qui ne
   s'appliquent que si ce step atteint effectivement ses lignes `echo ... >>
   "$GITHUB_OUTPUT"`) — mêmes valeurs que les défauts déclarés dans
   `generate-data.yml` (`fresh_run=false`, `threshold=3`, `workers=1`,
   `extract_interventions=true` — valeur initiale du script best-effort avant
   détection de `--skip-interventions`, pas le défaut `workflow_dispatch` de
   `generate-data.yml` lui-même qui est `false` —, `max_pages=5`,
   `roster_extraction_limit=20`), pour rester sûr même si le step best-effort
   n'a écrit aucun de ses outputs.

**Note d'implémentation** : modification d'un fichier existant sous
`.github/workflows/*`, poussée directement sans intervention manuelle —
cohérent avec #237 (voir [[retry-generate-data-detection-impossible]]), qui
avait déjà établi que seule la *création* d'un nouveau fichier sous ce
répertoire se heurte à la restriction de permissions GitHub App.

*Alternative rejetée* : ne garder que le fix n°2 (découplage de la
condition) sans garder le fix n°1 (garde sur `gh api`) — rejeté car un step
best-effort qui continue d'échouer bruyamment (`Process completed with exit
code 1`, job `detect-and-retry` en `failure`) reste un signal trompeur dans
l'historique des runs même si le retry finit par partir ; les deux corrections
sont complémentaires, pas substituables. *Hors périmètre de #336* :
réduction des téléchargements de logs redondants entre le step de détection
et le step best-effort (piste évoquée dans #336 pour réduire le risque de
rate-limit en amont) — non traitée ici, voir `ROADMAP.md`.

