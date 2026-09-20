<a id="amendements-zero-pas-de-hard-fail"></a>
# Quality gate : « 0 amendement collecté » reste non bloquant, mais cesse d'être discret (#378) (2026-08-18)

`2026-08-18`

> **En bref** — « 0 amendement collecté » reste non bloquant, mais cesse d'être discret.

**Contexte** : dernier des 5 fixes de l'investigation de #265 encore ouvert
(les 4 autres tranchés lors du re-check du 2026-08-17, voir
[[amendements-zero-silencieux-acteur-ref]]), sorti en issue dédiée parce qu'il
demandait un arbitrage produit et non un correctif. Les sections 3c (couverture
amendements) et 3d (fraîcheur des index, [[amendements-index-quality-gate-fraicheur]])
de `check_quality_gate.py` ne produisent que des avertissements souples ;
`exit_code` ne vaut 1 que sur `IncompleteRead` au-delà du seuil, structure de
groupe cassée ou structure de gouvernement cassée. Un run avait ainsi committé
28 profils avec `amendements[]` vide **partout** sans que rien ne bloque, alors
que la §3c avait bien détecté et affiché le signal.

**Décision : pas d'escalade en échec dur, dans aucun mode — y compris
`fresh_run=true`.** Aucun flag `--amendements-hard-fail` n'est ajouté. En
revanche le signal global de la §3c est rendu impossible à manquer.

## Pourquoi ne pas bloquer

1. **Le mode d'échec de #265 n'était pas l'absence de blocage, c'était l'absence
   de lecture.** Le signal existait, correct, mais en dernière ligne d'une
   section sur six d'un rapport qui en fait plusieurs centaines. Le rendre
   visible traite la cause ; bloquer traite le symptôme en faisant payer le
   coût à tous les runs suivants.
2. **La collecte dépend d'une source réseau chroniquement défaillante.** La
   législature 17 (active) échoue de façon répétée au téléchargement
   (`IncompleteRead` sur le CDN `data.assemblee-nationale.fr` —
   [[amendements-retry-blocage-legislature]],
   [[amendements-range-download-legislature-isolation]]), problème préexistant
   et hors de notre contrôle. Un run dont l'index n'a pas pu être construit
   produit légitimement zéro amendement : bloquer le commit y ferait perdre
   **tout le reste** du run (mandats, votes, interventions, groupes,
   gouvernements) pour une donnée dont l'absence est déjà tracée. On
   échangerait une donnée manquante contre aucune donnée.
3. **Cohérence avec la dégradation gracieuse déjà tranchée sur toute cette
   chaîne** : `continue-on-error: true` sur le job `extract-amendements-an`
   ([[amendements-index-job-dedie-ci]]), artefact d'index téléchargé en
   optionnel par les consommateurs ([[amendements-index-cache-only-consumers]]),
   retry global qui n'échoue pas sur une extraction partielle
   ([[retry-generate-data-continue-on-error]]). Un échec dur du gate
   contredirait frontalement ces trois décisions pour la même donnée.
4. **Le risque spécifiquement redouté est déjà couvert ailleurs, à la source.**
   Ce qui rendait #265 dangereux, c'est qu'un zéro pouvait être *silencieux*
   (acteurRef introuvable → `[]` sans warning), et qu'un
   `fresh_run=true`/`--no-merge` aurait effacé des amendements ne survivant que
   par la fusion additive. Depuis [[amendements-zero-silencieux-acteur-ref]], ce
   cas émet un warning par candidat : le zéro n'est plus indiscernable d'une
   absence légitime, ce qui était le vrai défaut.

## Ce qui change quand même — la moitié « make it loud » du fix 3

- `_report_amendements_coverage` retourne désormais le signal global à part
  (`regression_globale`), en plus de le laisser dans `soft_warnings` : même
  nature, affichage différent.
- **Affiché en tête de rapport**, avant les six sections : bandeau console juste
  sous la ligne `Quality gate : ✓ COMMIT AUTORISÉ`, et bandeau Markdown juste
  sous le badge dans le GitHub Step Summary.
- Dans la §3c : bloc dédié `🚨 RÉGRESSION PROBABLE DE COLLECTE`, disant
  explicitement que le caractère non bloquant est une **décision** (avec le
  lien vers cette section) et non un oubli. Le message n'est plus répété dans
  la liste des avertissements par candidat, où il se noyait.
- Annotation GHA : conservée au niveau `warning`, préfixée. *Alternative
  rejetée* : `::error::`, qui afficherait une annotation rouge sur un job vert.
  Dans ce script, `error` est réservé aux erreurs qui font effectivement
  `exit 1` (structures de groupe/gouvernement cassées) — le niveau doit rester
  lisible comme « ce run a échoué ».

## Alternatives rejetées

- **Flag `--amendements-hard-fail` désactivé par défaut** (la piste de
  compromis de #378). Rejeté parce qu'il resterait non câblé : le workflow ne
  le passerait jamais, et aucune donnée future ne viendrait changer
  l'arbitrage. C'est la différence avec `--groupe-min-coverage-pct`
  ([[seuil-couverture-groupe]]), option elle aussi désactivée par défaut mais
  qui attend un chiffre précis pour être activée. Une option que rien
  n'activera jamais est du code mort, pas une souplesse.
- **Escalader uniquement en `fresh_run=true`** (« quality gate à tolérance
  zéro » selon la description de l'input). Rejeté : c'est précisément le mode
  où aucun cache n'est restauré et où les trois archives sont retéléchargées —
  donc celui où un zéro d'origine réseau est le **plus** probable. On ferait
  échouer en priorité les runs les plus propres.
- **Escalader le signal par législature de la §3d** (« index jamais
  construit »). Jamais : c'est l'aléa réseau chronique de la 17, il rendrait le
  pipeline définitivement rouge pour une raison étrangère à toute régression.

## Ce qui ferait rouvrir la décision

Que la construction d'index cesse d'échouer de façon chronique — concrètement,
la 17 rapportée « frais » sur une série de runs consécutifs. Un zéro
deviendrait alors une anomalie franche plutôt qu'un état de fait de la source,
et l'escalade redeviendrait discutable.

**Tests** : `tests/test_quality_gate_amendements.py` verrouille les deux
moitiés — la visibilité (signal retourné à part, affiché en tête, non dupliqué)
et l'absence d'échec dur bout en bout (`main()` sort 0 avec `amendements[]` vide
partout, et sort 0 avec un index jamais construit). Suite complète : 1298/1298.

