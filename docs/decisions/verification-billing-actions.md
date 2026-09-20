<a id="verification-billing-actions"></a>
# Vérification quota/limite de dépense GitHub Actions (#221) : hypothèse infirmée (2026-08-12)

`2026-08-12`

> **En bref** — quota/limite de dépense GitHub Actions : hypothèse vérifiée et infirmée.

**Contexte** : #221, sous-issue du diagnostic #217, vérifiait si l'annulation
des jobs `extract-an`/`extract-roster-groupes` (run #24, récidive sur le run
#25) était due à un plafond de minutes Actions ou à une limite de dépense
atteinte en cours de run sur ce dépôt **privé**, dans un contexte de volume
inhabituellement élevé de runs `Claude Code`/`Claude Code Review` concurrents
ce même jour. Vérification hors périmètre agent (accès au tableau de bord de
facturation requis) — réalisée par @stephieED via Settings → Billing and
plans, capture d'écran "Usage breakdown" et export CSV du cycle en cours
fournis en commentaire.

**Constat (cycle de facturation d'août 2026)** :
- Minutes Actions incluses : 1 511 / 2 000 min utilisées (75 %) — sous quota.
- Stockage Actions inclus : 0,2 / 0,5 GB utilisés (40 %) — sous quota.
- "Usage breakdown" : Actions Linux (1 511 min, $9.07 brut) + Actions storage
  (132,12 GB-h, $0.04 brut) → **montant facturé $0**, entièrement absorbé par
  le quota inclus du plan.
- L'export CSV journalier (`225 min` le 12/08, `discount=0` par ligne) est
  cohérent avec ce total : la déduction du quota inclus n'apparaît qu'au
  niveau agrégé du cycle de facturation, pas ligne à ligne — l'absence de
  remise par jour n'est donc pas un signal de dépassement.

**Conclusion : hypothèse infirmée.** Ni le quota de minutes (marge de 489 min
restante) ni le stockage ne sont dépassés, et rien n'est facturé ce mois-ci
sur ce dépôt. Une limite de dépense à $0 combinée à un quota épuisé
bloquerait le *démarrage* du job (erreur explicite avant exécution), pas un
arrêt en cours de run — or le run #25 montre `The runner has received a
shutdown signal`, un signal d'infrastructure au niveau du runner hébergé,
sans lien avec la facturation. Cause la plus probable retenue pour #217 :
incident/préemption transitoire côté runners hébergés GitHub, indépendante du
statut public/privé du dépôt — passer le dépôt en public n'aurait pas
empêché ce type d'arrêt et n'est donc pas recommandé pour ce problème précis.

*Non vérifié précisément* : la valeur exacte configurée sur *Settings →
Billing and plans → Spending limits* n'a pas été communiquée telle quelle —
seul le résultat ($0 facturé, quota non atteint) est confirmé via le "Usage
breakdown" et le CSV. Suffisant pour trancher #221 (le quota/la dépense n'est
pas la cause de l'annulation), mais à compléter en commentaire si une valeur
précise de configuration est un jour nécessaire.

