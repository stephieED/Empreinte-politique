<a id="ci-cd"></a>
# Angle mort du `runner shutdown signal` sur `if: always()` et la sauvegarde de cache (#228) (2026-08-12)

`2026-08-12`

> **En bref** — angle mort du `shutdown signal` runner sur `if: always()` et sur la sauvegarde de cache.

**Contexte** : #219 a ajouté `if: always()` sur les steps `Upload artifact *`
de `generate-data.yml` pour préserver la progression partielle (profils déjà
écrits sur disque) en cas d'annulation/échec de job. Le run #25
(récidive de #217/#221, https://github.com/stephieED/Empreinte-politique-src/actions/runs/31605692943)
montre empiriquement que ce mécanisme a un angle mort : quand le runner
hébergé GitHub reçoit un `shutdown signal` d'infrastructure (cause retenue
pour #217, voir [[verification-billing-actions]] — préemption transitoire,
indépendante de la facturation), **aucun step suivant ne s'exécute, `if:
always()` inclus**. Dans ce run, `Upload artifact AN`, le `Post Run
actions/cache@v4` (sauvegarde implicite du cache `.cache` en fin de job) et
les deux steps de diagnostic `if: cancelled()`/`if: failure()` de #223 sont
tous `skipped`, alors que le job est en `failure`. Toute la progression du
job (profils + cache) est donc perdue dans ce mode précis, contrairement à ce
que #219 visait à garantir : GitHub Actions tue le process runner lui-même
avant que la couche `if:`/post-step ne puisse s'évaluer, ce qui est différent
d'une annulation ou d'un échec applicatif classique que `always()` couvre
correctement.

**Pistes évaluées** (#228) :
1. Réduire la granularité des jobs d'extraction coûteux (`extract-an`,
   `extract-roster-groupes`) en sous-lots (matrix strategy par tranche de
   candidats/roster), pour borner la perte à un lot plutôt qu'à tout le job.
2. Invoquer `actions/cache/save@v4` à des points de contrôle intermédiaires
   plutôt qu'en post-step implicite de fin de job.
3. Documenter explicitement le blind spot dans `generate-data.yml` (commentaire),
   pour éviter une fausse impression de résilience lors de futures modifications.

**Décision retenue : option 3 seule pour l'instant** (commentaire explicite à
ajouter en tête de `generate-data.yml`, à côté du bloc de commentaires
existant sur les timeouts) — patch fourni en commentaire de #228 pour
application manuelle (voir note d'implémentation ci-dessous). Réduit le risque
de régression silencieuse (un futur changement qui s'appuierait à tort sur
`always()` comme garantie totale) à coût nul, sans toucher au comportement du
workflow.

**Options 1 et 2 différées, pas rejetées** : les deux réduiraient réellement
le blast radius, mais seule l'option 1 (sharding) couvre la perte des *deux*
formes de progression (artifacts de profils **et** cache) — l'option 2 seule
ne couvre que la sauvegarde du cache, pas l'upload d'artifact, tant que
l'extraction reste un unique step long ; elle ne devient réellement utile que
combinée à un découpage en plusieurs steps/lots, c'est-à-dire à l'option 1.
Le sharding matrix a un coût de conception non trivial (clés de cache par lot,
fusion de N artifacts au lieu d'un seul dans `merge-and-pivot`, interaction
avec la réduction du pic de jobs concurrents de #222,
[[concurrence-ci-roster]]) et une urgence limitée tant que
`roster_extraction_limit` reste à 20 (rollout restreint, #192) — l'exposition
réelle grandira surtout au passage à un run à pleine échelle (~750 membres),
pas encore planifié (voir [[seuil-couverture-groupe]]). À concevoir avec cette
recalibration plutôt qu'en réaction isolée à #228.

**Note d'implémentation** : l'agent qui a traité #228 n'a pas pu pousser
directement le commentaire YAML de l'option 3 sous `.github/workflows/*`
(appliqué manuellement à partir du patch fourni en commentaire de résolution
de #228). Restriction d'outillage CI, pas une décision produit — nuancée
depuis par #237 : seule la **création** d'un nouveau fichier sous
`.github/workflows/*` s'est heurtée à la restriction, la **modification**
d'un fichier existant a ensuite fonctionné sans intervention manuelle (détail
et reproduction dans [[retry-generate-data-detection-impossible]]).

