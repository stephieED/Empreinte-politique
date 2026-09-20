<a id="retry-generate-data-preemption"></a>
# Retry automatique de `generate-data.yml` sur signature de préemption runner (#230) (2026-08-12)

`2026-08-12`

> **En bref** — retry automatique sur signature de préemption runner.

**Contexte** : #217/#221/#228 (voir [[verification-billing-actions]] et
[[ci-cd]] ci-dessous) ont établi qu'un `generate-data.yml` tué par un
`shutdown signal` runner GitHub (préemption infra transitoire, hors contrôle
du workflow) reste en échec jusqu'à un re-déclenchement manuel — vécu deux
fois de suite sur les runs #24/#25. #230 demande une récupération
automatique de ce mode de défaillance précis, sans masquer un vrai échec
applicatif (#218 : bug de script shell du Quality Gate, qu'un retry
généralisé aurait fait disparaître silencieusement au lieu de le signaler).

**Décision** : un second workflow, déclenché sur `workflow_run` (`types:
[completed]`) ciblant `Génération des données`, qui :
1. **Plafonne à 1 tentative** en vérifiant `github.event.workflow_run
   .triggering_actor.login` — si le run échoué a lui-même été déclenché par
   `github-actions[bot]` (identité utilisée par `gh workflow run` via
   `GITHUB_TOKEN`), c'est déjà une relance automatique : pas de nouvelle
   tentative. Choisi plutôt qu'un compteur externe (variable de dépôt,
   artifact dédié) car il ne nécessite aucun état persistant ni permission
   supplémentaire — l'identité de l'acteur déclencheur suffit à distinguer un
   run humain d'un run auto-relancé.
2. **Détecte la signature précise** via l'API Actions (`gh api .../actions/
   runs/<id>/jobs` puis `.../jobs/<job_id>/logs`) : au moins un job en échec
   dont les steps `if: always()`/`if: failure()` (`Upload artifact *`,
   `Diagnostic — job en échec`) sont `skipped` **et** dont les logs
   contiennent `shutdown signal` / `The operation was canceled.`. Un échec
   applicatif (exception Python, Quality Gate en échec réel) laisse toujours
   ces steps s'exécuter normalement — la combinaison des deux signaux évite
   les faux positifs qu'un simple grep de log seul ne suffirait pas à écarter.
3. **Reconstruit les inputs du run échoué en best-effort** : l'API Actions
   n'expose pas les inputs d'un `workflow_dispatch` passé (pas de champ
   dédié sur l'objet run). `fresh_run` est lu de façon fiable via la
   conclusion du step conditionnel `Nettoyage complet (fresh_run
   uniquement)` (skipped/success reflète directement `inputs.fresh_run`) ;
   `workers`/`extract_interventions`/`max_pages` sont extraits du texte
   résolu du step `Extraction AN` (ces valeurs sont substituées directement
   par `${{ inputs.* }}` dans le script, donc visibles telles quelles dans le
   log) ; `threshold` est lu depuis le rapport stdout de
   `check_quality_gate.py` (`Seuil : N`) ; `roster_extraction_limit` depuis
   le rapport stdout de `generate_all_profiles.py`. En cas d'échec
   d'extraction d'une valeur, repli sur le défaut déclaré de
   `generate-data.yml` pour cet input — dégradation documentée, pas un
   blocage du retry.
4. **Re-déclenche** `generate-data.yml` via `gh workflow run` avec les
   inputs reconstruits, sur la même branche que le run échoué
   (`github.event.workflow_run.head_branch`).
5. **Notifie explicitement** via `$GITHUB_STEP_SUMMARY` (même pattern que
   les steps de diagnostic existants de `generate-data.yml`) : retry
   déclenché, plafond déjà atteint, ou signature non reconnue — dans les
   trois cas, une trace visible plutôt qu'un re-run silencieux ou une
   absence de retry inexpliquée.

**Note d'implémentation** : comme pour #228, l'agent qui a traité #230 n'a
pas pu pousser directement le nouveau fichier `.github/workflows/retry-
generate-data.yml` (créé manuellement à partir du YAML fourni en commentaire
de résolution de #230). Restriction d'outillage CI, pas une décision produit
— nuancée depuis par #237 : seule la **création** d'un nouveau fichier sous
`.github/workflows/*` s'est heurtée à la restriction, la **modification**
d'un fichier existant a ensuite fonctionné sans intervention manuelle (détail
et reproduction dans [[retry-generate-data-detection-impossible]]).

*Alternative rejetée* : retry généralisé sur tout `conclusion: failure`
sans vérification de signature — rejeté explicitement par #230 lui-même
(masquerait une régression applicative réelle comme #218 au lieu de la
signaler). *Alternative rejetée* : plafonner le retry via un nouvel input
`workflow_dispatch` dédié sur `generate-data.yml` (ex. `auto_retry_count`)
plutôt que l'identité de l'acteur déclencheur — rejeté car cela nécessiterait
de modifier `generate-data.yml`, hors de portée de cet agent pour la même
raison que le nouveau fichier lui-même (restriction de permissions
`.github/workflows/*`), et l'identité de l'acteur atteint le même résultat
sans ce besoin.

