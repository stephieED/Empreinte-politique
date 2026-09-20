<a id="retry-generate-data-continue-on-error"></a>
# Étendre `retry-generate-data.yml` aux échecs de job `continue-on-error` masqués par une conclusion de run `success` (#245) (2026-08-13)

`2026-08-13`

> **En bref** — un échec de job `continue-on-error` masqué par une conclusion de run `success` déclenche quand même le retry.

**Contexte** : [[retry-generate-data-preemption]] (#230) détecte la
signature de préemption runner au niveau job, mais le job `detect-and-retry`
n'était invoqué que sur `github.event.workflow_run.conclusion == 'failure'`.
Run #30 (2026-08-13T09:17:33Z,
https://github.com/stephieED/Empreinte-politique-src/actions/runs/31685914622) :
`extract-roster-groupes` (`continue-on-error: true`, choix délibéré #192/#222)
a été tué par la même signature de préemption déjà documentée
([[retry-generate-data-preemption]], #217/#228/#230) — `shutdown signal` à
09:29:44, confirmé `conclusion: "failure"` via `gh api
.../jobs/94402695448` (`started_at 09:21:14`, `completed_at 10:14:16`,
message serveur différent : *"The hosted runner lost communication with the
server"*, 44 min après l'arrêt réel du job). Un job `continue-on-error` en
échec ne fait pas basculer la conclusion globale du run à `failure` : le run
#30 reste `success`, le `workflow_run` déclenché à 10:15:25Z a
`conclusion: success`, et `detect-and-retry` a donc été entièrement
`skipped` — aucune inspection de la liste des jobs, donc aucun retry, et
aucune visibilité (le run s'affiche vert ; seuls les soft warnings du
quality gate sur la couverture groupe, conformes à
[[seuil-couverture-groupe]], révèlent l'échec à qui les lit).
`extract-parltrack` (même configuration, ligne 332 de `generate-data.yml`)
est exposé au même angle mort.

**Décision** :
1. Garde du job `detect-and-retry` élargie à
   `conclusion == 'failure' || conclusion == 'success'` (exclut de fait
   `cancelled`/`skipped`, pour lesquels un retry n'a pas de sens).
2. Step de détection : nouvel output `no_job_failure`, positionné à `true`
   uniquement quand la conclusion du run est `success` **et** qu'aucun job
   de la liste n'a `conclusion == "failure"` — court-circuite la boucle de
   détection existante dans ce seul cas. Sans ce circuit dédié, élargir la
   garde du point 1 aurait fait tomber tout run 100% vert dans la branche
   « signature non reconnue » du résumé (destinée à un vrai échec
   applicatif), un faux signal sur l'immense majorité des runs qui n'ont
   simplement aucun job en échec.
3. La boucle de détection elle-même (filtrage `select(.conclusion==
   "failure")` sur la liste des jobs, puis grep `shutdown signal|The
   operation was canceled\.` sur leurs logs) n'a nécessité **aucune
   modification** : elle opère déjà au niveau job et fonctionne
   correctement dès qu'elle est atteinte — vérifié manuellement contre le
   job réel 94402695448 du run #30.
4. Step Résumé : quatrième branche dédiée à `no_job_failure == 'true'`
   (« run réussi sans échec de job — rien à signaler »), distincte des
   trois branches existantes ([[retry-generate-data-detection-impossible]]).

Portée générique, pas spécifique à `extract-roster-groupes` : le correctif
opère au niveau job (n'importe quel job en échec, `continue-on-error` ou
non), donc `extract-parltrack` en bénéficie sans changement supplémentaire.

*Hors périmètre* : retirer `continue-on-error: true` de
`extract-parltrack`/`extract-roster-groupes` — choix délibéré et correct
(#192/#222), non remis en cause par cette issue (visibilité/retry de
l'échec, pas changement de comportement). Expliquer pourquoi le nettoyage
runner a mis cette fois 44 minutes à se signaler côté serveur (`"lost
communication with the server"` vs terminaison immédiate dans les
incidents précédents) — signal d'infrastructure hors du contrôle du
workflow, cohérent avec [[verification-billing-actions]].

*Alternative rejetée* : ouvrir la garde du job sur toute conclusion
(supprimer le filtre) plutôt que de lister explicitement `failure`/
`success` — rejeté car `cancelled`/`skipped` ne doivent pas déclencher de
tentative de détection (rien à détecter, `workflow_run.id` peut même ne pas
avoir de jobs exploitables), et le lister explicitement documente
l'intention plutôt que de la laisser implicite.

