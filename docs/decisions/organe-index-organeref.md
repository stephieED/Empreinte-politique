<a id="organe-index-organeref"></a>
# `_build_organe_index` : résoudre `organeRef` via `AMO30` (historique) sans filtrage par `codeType` (#353) (2026-08-16)

`2026-08-16`

> **En bref** — résoudre `organeRef` via `AMO30` historique, sans filtrage par `codeType`.

**Contexte** : sous-issue 2/6 de #351. `mandats[].organes.organeRef` (ex.
`PO59048`) ne référence un organe (commission, groupe politique, groupe
d'amitié, engagement extra-parlementaire...) que par identifiant — aucun nom
lisible sans résolution. Un index partiel existait déjà
(`_build_organe_positions_index`), mais limité aux `codeType` `GP`/
`GOUVERNEMENT`, pour un besoin différent (qualification majorité/opposition/
gouvernement, voir `fetch_positions_hemicycle_officielles`).

**Décision : réutiliser le zip bulk historique (`AMO30`,
`AN_ACTEURS_HISTORIQUE_ZIP_URL`), pas `AMO10` (actifs).** Vérifié par
téléchargement réel (13,6 Mo, 10 812 `json/organe/*.json`, 33 `codeType`
distincts) : `AMO10` (mandats actifs de la législature en cours) ne couvre
qu'un sous-ensemble des organes référencés par des mandats plus anciens —
`AMO30` est nécessaire pour résoudre l'historique complet des mandats d'un
élu, pas seulement ses mandats en cours. `_build_organe_index` indexe donc
`organeRef -> {sigle, nom, type}` = `{libelleAbrege, libelle, codeType}`
sans filtrer par `codeType`, contrairement à `_build_organe_positions_index`
— voir `docs/sources/an-opendata.md`, section "Actors / mandates / bodies", pour le
détail des champs.

**Refactor associé : téléchargement du zip mutualisé.**
`_build_acteur_positions_hemicycle_index` et `_build_organe_index` lisent
tous deux `AN_ACTEURS_HISTORIQUE_ZIP_URL`, mais construisent chacun leur
propre index mis en cache séparément (`index_positions_hemicycle.json` /
`index_organes.json`). Sans mutualisation, les deux fonctions auraient pu
télécharger le zip (~13,6 Mo) chacune de leur côté en cas d'appel concurrent
depuis des threads différents, avec un risque d'écriture concurrente sur le
même fichier zip. Extrait dans
`_ensure_acteurs_historique_zip_downloaded`, verrouillé par un verrou dédié
(`_ACTEURS_HISTORIQUE_ZIP_LOCK`), séparé du verrou de construction de
chaque index (un seul téléchargement, peu importe combien d'index en
dépendent).

**Non traité ici** : le rattachement de `_build_organe_index` aux mandats du
schéma pivot (commissions avec rôle, groupes d'amitié, engagements
extra-parlementaires, groupe politique) — prérequis posé par cette
sous-issue, exploité par les sous-issues suivantes de #351.

