<a id="cache-an-du-jour-1261"></a>
# La 17e se réindexe chaque jour, le référentiel des acteurs chaque semaine (#1261) (2026-10-08)

`2026-10-08`

> **En bref** — la séance du 07/10/2026 manquait au run du 08/10 à 18:01. Ce run a restauré l'index des comptes rendus de la 17e sous la clé de la semaine (`public-data-cache-an-2026-W41-interv-…`), construit le 07/10 vers 23:10 sur l'archive de ce moment-là. L'archive mise à jour le 08/10 à 4 h 06, qui porte le 07, n'a jamais été relue. La règle de #555 ne périmait le contenu vivant qu'**au changement de semaine** : une séance tenue en semaine attendait le lundi suivant, même si l'on lançait un run. Arbitrage de la propriétaire, 08/10 (option A) : la clé du cache AN porte le jour, et une entrée de la semaine mais d'un autre jour périme les seules législatures vivantes.

## 1. La décision

- La clé AN devient `public-data-cache-an-<semaine>-j<jour>[-interv-<empreinte>]` (`date +%G-W%V-j%u`, en UTC sur le runner), dans les trois jobs qui la calculent (quatre clés) : `prepare-an-matrix` (sonde), `extract-an` (restauration et sauvegarde), `extract-roster-groupes` (consommateur). Les `restore-keys` passent par la semaine (`…-<semaine>-`) avant le préfixe nu. Les clés des dossiers et des amendements restent hebdomadaires.
- `cache_an_fraicheur.evaluer` rend un verdict de plus, `PERIME_DU_JOUR` : même semaine, autre jour, ou entrée écrite avant cette forme de clé. Il ne périme que les répertoires des législatures non figées (scrutins, questions, Syceron de la 17e) ; `.cache/acteurs_historique_an` reste hebdomadaire.

## 2. Le coût, mesuré et estimé

- Réindexer la 17e : **42 s** (mesure de #550), une fois par jour au premier run.
- **La sonde de #1137 pose la clé du jour** : le premier run de chaque jour en mode par défaut (sans interventions) trouve une clé froide et sérialise `extract-an` (`max-parallel: 1`), au lieu du seul premier run de la semaine. Les runs avec interventions — dont le planifié du soir — ne sont pas sondés et tournent déjà en série : rien ne change pour eux. Mesuré le 08/10 : 32 shards en 48 min (18:01, interventions) et en 32 min (07/10, 23:10).

## 3. Alternatives écartées

- **Un run « à froid » (`cold_start=true`)** : il retélécharge et réindexe tout, et ne corrige rien pour la semaine suivante.
- **Attendre le lundi** : une semaine de séances absente chaque semaine, sur une législature qui siège.
- **Garder la sonde sur la semaine** : des shards parallèles restaureraient l'entrée de la veille et périmeraient chacun la 17e, retéléchargeant chacun l'archive. C'est le défaut de #424, retrouvé.
