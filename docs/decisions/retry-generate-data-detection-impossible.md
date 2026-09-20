<a id="retry-generate-data-detection-impossible"></a>
# Distinguer erreur API et signature absente dans `retry-generate-data.yml` (#237) (2026-08-13)

`2026-08-13`

> **En bref** — distinguer une erreur d'API d'une signature absente : les deux ne se traitent pas pareil.

**Contexte** : [[retry-generate-data-preemption]] (#230) détecte la signature
de préemption runner via deux appels `gh api` (`.../jobs` puis
`.../jobs/<id>/logs`). Sur les runs #26/#27, `gh api .../jobs` a échoué
(erreur transitoire d'API/pagination) sous `set -euo pipefail` sans
fallback : le step entier s'est arrêté immédiatement (`Process completed with
exit code 1`), avant même d'atteindre la boucle de détection — le job
`detect-and-retry` a fini en `failure` sans résumé exploitable. Séparément,
`gh api .../logs` retombait sur `2>/dev/null || true` (#236) : un échec
ponctuel de récupération d'un log individuel produisait un `log=""`, traité
exactement comme une signature absente, donc affiché dans le résumé comme
« probablement un échec applicatif réel » — message trompeur qui a masqué le
bug de listing des jobs pendant trois runs consécutifs (le résumé n'existait
même pas dans ce cas précis, mais le même risque de confusion existe pour
tout échec `.../logs` isolé).

**Décision** : ajoute deux outputs dédiés au step de détection,
`api_error` (échec de `gh api .../jobs`) et `inconclusive` (échec de
`gh api .../jobs/<id>/logs` sur au moins un job candidat), capturés
explicitement (`if ! cmd; then ...; fi`, message `::warning::` avec le détail
de l'erreur) plutôt que laissés remonter via `set -e` ou avalés par
`|| true`. Le step de résumé distingue désormais trois issues au lieu de
deux : retry déclenché (`matched=true`, inchangé), signature non reconnue
sur des logs effectivement lus (`matched=false` et aucune erreur, inchangé),
et détection impossible (`api_error` ou `inconclusive` à `true`, ou
`steps.signature.outcome == 'failure'` en filet de sécurité pour toute
erreur bash non anticipée) — message dédié invitant à une vérification
manuelle du run, explicitement non assimilé à un bug applicatif.

**Note d'implémentation** : contrairement à #228/#230 où l'agent n'avait pas
les permissions GitHub App pour pousser un fichier sous
`.github/workflows/*` (patch livré en commentaire, application manuelle),
le push direct a fonctionné pour ce correctif — la restriction ne semble
plus s'appliquer (ou ne s'appliquait qu'à la création d'un nouveau fichier,
pas à la modification d'un fichier existant). À vérifier si le patch #228
toujours en attente (voir `ROADMAP.md`) peut désormais être appliqué de la
même façon.

*Alternative rejetée* : ne garder qu'un flag booléen unique (« détection
fiable oui/non ») au lieu de deux outputs distincts `api_error`/
`inconclusive` — rejeté pour ne pas perdre, dans les `::warning::` du job,
la distinction entre un échec de listing (affecte toute la détection) et un
échec de log isolé sur un seul job candidat (les autres jobs candidats
restent exploitables), utile pour le diagnostic manuel demandé par le
résumé.

