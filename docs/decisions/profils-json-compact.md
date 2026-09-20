<a id="profils-json-compact"></a>
# Profils écrits en JSON compact, groupes et gouvernements indentés (#433) (2026-08-18)

`2026-08-18`

> **En bref** — profils écrits en JSON compact (35 % du volume n'était que de l'indentation) ; groupes et gouvernements restent indentés.

**Contexte** : troisième levier de l'épic volumétrie #429. La mesure sur les 752
profils du roster complet (`audit_volumetrie_profils.py`,
`audit/volumetrie_roster_752.md`) donne 8 093 Mo sur disque pour 5 263 Mo de
contenu réel : **2 830 Mo, soit 35 %, ne sont que de l'indentation**.

C'est le seul levier de l'épic qui ne demande aucun arbitrage : aucun champ
touché, aucun schéma modifié, aucun consommateur à adapter. Tout le pipeline
relit ses fichiers par `json.load()` / `json.loads()` — vérifié sur l'ensemble
des lecteurs, aucun ne procède ligne à ligne, et rien dans `scripts/` ni dans
les workflows ne fait de `grep`/`wc -l` sur un profil.

**Décision** : `json.dumps(..., separators=(",", ":"))` pour les profils
individuels — `raw_data/profiles/` et `pivot_data/profiles/` — via l'helper
partagé `src/json_io.py`. Restent indentés `pivot_data/groupes`,
`pivot_data/gouvernements`, `pivot_data/partis`, les rosters, les rapports
d'audit et le checkpoint de génération : 9,8 Mo au total, effectivement relus à
la main lors des audits.

`ensure_ascii=False` est conservé : l'échappement `\uXXXX` coûterait 6 octets
par caractère accentué et annulerait une part du gain sur des profils français.

## Contrepartie assumée : la lisibilité du diff git

Un profil compact apparaît comme **une seule ligne changée**. L'objection est
réelle, mais l'avantage était déjà perdu : le commit de données du 2026-08-18
affichait 16,6 millions de lignes modifiées sur 239 fichiers — un diff que
personne ne lit. Les profils de gouvernement, eux, ont un vrai intérêt à rester
lisibles, et ils pèsent 0,33 Mo.

## Ce qui aurait pu casser, et pourquoi ça ne casse pas

`preserve_stable_freshness_timestamps` et la comparaison de contenu de #343
travaillent sur la structure **déjà désérialisée** :
`_pivot_content_fingerprint` re-sérialise avec `sort_keys=True` après avoir
retiré `meta.genere_le` et `sources[].synchro_le`. La détection « contenu
identique » est donc indifférente au formatage — un profil indenté sur disque
face à une régénération compacte reste reconnu comme inchangé, et les
horodatages ne ré-avancent pas. Couvert par
`tests/test_json_io.py::test_freshness_preservee_quand_l_ancien_fichier_etait_indente`.

## Pas de commit de reformatage

Les profils déjà commités restent indentés jusqu'à leur prochaine
régénération, que le pipeline effectue de toute façon à chaque run. Un commit
de reformatage en masse serait contre-productif pour l'objectif de l'épic :
il ajouterait ~5 Go de nouveaux blobs à l'historique **sans** retirer les
anciens, donc ferait grossir `.git`. Le gain se matérialise fichier par
fichier, à mesure que le pipeline les réécrit.

**Vérification sur données réelles** : les 378 profils présents dans le dépôt
passent de 2 282 Mo à 1 505 Mo (**34,1 %**), avec égalité sémantique
(`json.loads` avant/après) sur chacun — la projection à 35 % est confirmée.

---
