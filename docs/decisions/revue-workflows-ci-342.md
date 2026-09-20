<a id="revue-workflows-ci-342"></a>
# Revue transversale des workflows GitHub Actions : ce qui est gardé, ce qui est corrigé (#342) (2026-08-18)

`2026-08-18`

> **En bref** — revue transversale des workflows : ce qui est gardé, ce qui est corrigé, et par quelles sous-issues.

**Contexte** : `.github/workflows/` a grossi par ajouts successifs, chacun
justifié localement dans sa propre issue (#192, #215, #222, #245, #248, #251,
#344, #390, #394…), sans qu'aucune passe transversale n'ait jamais revérifié la
cohérence de l'ensemble une fois tous les jobs en place. #342 est cette passe :
revue documentaire, job par job et fichier par fichier, **sans modification de
comportement CI** — chaque correction retenue part en sous-issue dédiée, pour
qu'un run de validation puisse être attribué à un changement et un seul.

**Périmètre réellement relu : 6 workflows, pas 5.**
`debug-network-shutdown-signal.yml` a été ajouté après la rédaction de #342 et
n'avait jamais été relu ; il entre dans le périmètre (#416).
`generate-data.yml` compte désormais **9 jobs** (dont 2 jobs préparatoires de
matrix et 2 jobs shardés), pas les 7 que décrit #342.

## Ce qui est gardé tel quel, et pourquoi

- **Les motifs `MERGE_FLAG` / `INTERV_FLAG` / `MAX_PAGES_FLAG` restent
  dupliqués** dans les jobs d'extraction. Raison principale, non évidente et
  jamais écrite jusqu'ici : `retry-generate-data.yml` reconstruit les inputs du
  run échoué en **grepant le texte bash substitué de ces steps** ; les déplacer
  dans une action composite casserait ce couplage. La contrainte doit rester
  visible en commentaire dans le YAML tant que le mécanisme de reconstruction
  n'est pas remplacé (#414).
- **Les steps « Semaine ISO courante » et « Nettoyage complet (fresh_run) »
  restent dupliqués** : 3 à 4 lignes par job, et la seule alternative
  (les exposer depuis un job partagé) ajouterait une arête `needs:` à des jobs
  volontairement indépendants — c'est-à-dire exactement le mode de défaillance
  décrit plus bas pour les jobs préparatoires.
- **Les blocs de diagnostic annulation/échec, eux, sont factorisables** en
  action composite locale : les `if: cancelled()` / `if: failure()` restent
  portés par le step appelant, la sémantique est donc préservée. ~145 lignes de
  duplication pour une indirection d'un seul niveau — retenu (#412), à la
  différence des motifs ci-dessus.
- **L'ordre des étapes de pivot de `merge-and-pivot`** (candidats déclarés
  avant roster) est conservé : il n'est neutre que grâce à la protection de
  provenance de `merge_pivot_profile` ([[provenance-pivot]]), déjà commentée.
  Le double appel de `generate_roster_candidats.py` (une fois par shard, une
  fois au pivot) est également conservé : 2 appels réseau mutualisés, moins
  cher qu'un transit par artifact.
- **Le plafond d'une seule tentative de retry** ([[retry-preemption-logs]])
  reste basé sur `triggering_actor == github-actions[bot]`. Corollaire à
  écrire : une relance **manuelle** après un retry automatique repart avec un
  plafond neuf — comportement voulu, aujourd'hui implicite.
- **L'asymétrie de sandbox entre `claude.yml` et `claude-code-review.yml` est
  volontaire**, contrairement à ce que #342 laissait ouvert : le premier reçoit
  un prompt arbitraire *et* un `WORKFLOW_PAT` en écriture (sandbox bubblewrap +
  allowlist réseau + `--allowed-tools` proportionnés) ; le second tourne un
  prompt fixe avec le token par défaut en lecture seule. Défendable — mais à
  écrire dans les deux fichiers, et sous réserve des deux points traités en
  #415 (le token OAuth Claude est exposé dans les deux, et le marketplace de
  plugins n'est pas épinglé). **Suite donnée en #415**
  ([[workflows-claude-securite]]) : l'asymétrie de `github_token` /
  `permissions` / `--allowed-tools` est confirmée et écrite en en-tête des deux
  fichiers, mais celle du **sandbox est supprimée** — le workflow de review
  reçoit la même isolation réseau, parce qu'il lit du contenu de PR hostile avec
  le token OAuth en mémoire. Le marketplace reste non épinglé, refus argumenté
  (aucune syntaxe de révision n'existe côté action).
- **Le `schedule:` cron reste commenté.** Hors périmètre de #342 (décision
  produit/coût) : la revue constate seulement que rien depuis #192 ne l'a
  reconfirmé, et que la désactivation n'a jamais été justifiée par écrit.

## Ce qui est corrigé, et dans quelle sous-issue

| Constat | Sous-issue |
|---|---|
| `prepare-an-matrix` / `prepare-roster-matrix` sont des SPOF : leur échec *skippe* toute la chaîne jusqu'à `merge-and-pivot`, que `continue-on-error:` ne protège pas (il couvre l'échec, pas le skip) | #412 |
| Trois commentaires affirment le contraire du YAML (« pas de `needs:` sur `extract-amendements-an` ») | #412 |
| Seul `extract-amendements-an` écrit encore le cache AN hebdomadaire (exact key hit → pas de sauvegarde post-job chez les consommateurs) | #412 |
| Budget de temps mur faux : 210 min réels en rollout, 630 min en run complet, contre 190 annoncés ; libellés « JOB n/4 » périmés | #413 |
| Le garde-fou #390 compare toujours à `origin/main`, donc bloque tout run lancé hors `main` | #413 |
| Le garde-fou #390 ne couvre pas les fichiers de configuration (`groupes_reels.json`…), qui sont pourtant des entrées du build | #413 |
| `raw_data/roster_candidats.json` et `parltrack-status.json` sont trackés alors que le YAML affirme le contraire | #413 |
| `contents: write` accordé aux 9 jobs, alors que seul `merge-and-pivot` en a besoin | #413 |
| La reconstruction best-effort des inputs du retry est morte depuis le shardage (noms de jobs `extract-an (<slug>)`) | #414 |
| Dans la branche #390, la reconstruction des inputs n'est même pas tentée | #414 |
| Aucune garde sur l'auteur du commentaire : sur un dépôt **public**, le commentaire de n'importe qui démarre un runner (l'action refuse ensuite les acteurs sans droit d'écriture — voir [[workflows-claude-securite]]) | #415 |
| Le site Pages ne se redéploie jamais sur un commit de données | #416 |
| `debug-network-shutdown-signal.yml` sans bloc `permissions:` | #416 |

## Questions de #342 refermées sans travail

- **Le fallback `extract_interventions`** cité en exemple par l'epic est déjà
  corrigé (`7debd61`) ; les **six** fallbacks du retry sont alignés sur les
  défauts déclarés dans `generate-data.yml`.
- **Les « 3 blocs de résumé » de `retry-generate-data.yml`** n'existent plus :
  c'est un bloc `if/elif` unique à 6 branches depuis #245/#336.
- **La course d'écriture sur le cache AN partagé**, actée hors périmètre en
  #248 sous-issue 4 ([[amendements-index-budget-ci-cache-granularite]]), est
  **éteinte** : les trois jobs qui écrivent `public-data-cache-an-*` sont
  strictement séquencés depuis #344, et les deux consommateurs sont en lecture
  cache-only depuis #252. Résolue par effet de bord, jamais actée jusqu'ici.
- **Les noms et chemins d'artifacts** sont cohérents, à une exception près
  (`raw-profiles-parltrack` contient des dumps `.zst`, pas des profils).

## Trois conclusions non évidentes, à ne pas re-dériver

1. **Le pic de jobs simultanés n'est plus 4 mais 6.** Six jobs démarrent sans
   `needs:` depuis l'ajout des deux jobs préparatoires de matrix (#344/#394).
   Les commentaires « `max-parallel: 1` préserve le pic de 4 jobs acté par
   #222 » ([[concurrence-ci-roster]]) sont faux depuis.
2. **La justification du plafond de concurrence repose sur une hypothèse
   infirmée.** #222 a réduit le pic en mitigation d'un plafond de dépense
   Actions suspecté — hypothèse explicitement démentie depuis
   ([[verification-billing-actions]]). Ce qui reste valide de #222 est
   l'argument *cache* (ne pas télécharger deux fois les dumps AN), pas
   l'argument *concurrence*. Conséquence concrète : `max-parallel: 1` sur
   `extract-roster-groupes` coûte ~63 min de temps mur en run complet contre
   ~8 min en parallèle ([[budget-roster-mesure]]), pour une contrainte à
   re-trancher (#412).
3. **Les données du site sont figées au build.** `npm run build` exécute
   `sync-data.mjs`, qui copie `pivot_data/` dans `public/data/` (gitignoré) ;
   le front les lit ensuite par `fetch('/data/…')`. Comme `deploy-pages.yml` ne
   se déclenche que sur `web/UI_finale/**`, le commit de données de
   `merge-and-pivot` ne redéploie rien — vérifié le 18/08/2026 : commit de
   données du 18/08 sur `main`, dernier déploiement du 17/08. Les données
   n'atteignent la production qu'à la faveur d'une modification d'interface
   ultérieure (#416).

*Alternative rejetée* : appliquer les correctifs directement dans cette epic —
rejetée par #342 lui-même, et confirmée par la revue : treize corrections
touchant 5 fichiers dans un seul diff CI seraient inattribuables en cas de
régression, alors que chacune demande son propre run de validation
(`workflow_dispatch`).

*Alternative rejetée* : produire la revue sous forme d'un document séparé
(`docs/ci_review.md`) — rejetée pour éviter une deuxième autorité concurrente
de ce fichier ; le détail par fichier vit dans les sous-issues #412-#417, seules
les décisions durables sont ici.

