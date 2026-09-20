<a id="taxonomie-mandats-typeorgane-an"></a>
# Taxonomie des mandats : exploitation des `typeOrgane` AN non mappés (#382, option « mixte ») (2026-08-17)

`2026-08-17`

> **En bref** — la moitié du référentiel était inexploitée.

**Contexte** : #369 avait mappé 3 `typeOrgane` sur ~25 (« périmètre
minimal-invasif »). Mesuré sur 65 profils résolus AN, cela laissait
**3 150 mandats inexploités contre 3 273 exploités** — presque la moitié du
référentiel. Ces mandats existaient malgré tout dans les profils, mais
uniquement parce que la fusion additive préservait des entrées héritées de
l'ère NosDéputés, où `_extract_mandats` les mappait **toutes** en dur vers
`commission` : d'où le symptôme de #379 (197 libellés sur 246 classés
« Commission » sans en être).

**Décision — option « mixte » (arbitrée par l'utilisatrice)** : une catégorie
par nature institutionnelle réellement distincte pour le lecteur, pas une par
`typeOrgane`. Ajouts à `schema_pivot.KNOWN_CATEGORIES` :

| Catégorie ajoutée | `typeOrgane` regroupés | Mandats |
|---|---|---|
| `groupe_etudes` | `GE`, `GEVI` | 1185 |
| `commission_enquete` | `CNPE`, `CNPS` | 371 |
| `mission_information` | `MISINFO`, `MISINFOCOM`, `MISINFOPRE` | 348 |
| `delegation` | `DELEG`, `DELEGBUREAU`, `API`, `OFFPAR` | 143 |

Rangés dans l'existant : `COMNL` → `commission` (97) ; `BUREAU`/`CONFPT` →
`autre` (35, deux organes seulement — ne justifient pas une catégorie).

**`MINISTERE` → `fonction_gouvernementale` (79 mandats, 52 intitulés)** :
apporte le **portefeuille ministériel précis** (« Ministère de la cohésion
des territoires », « Secrétariat d'État auprès du ministre de… »), en
complément — non en remplacement — du rattachement au gouvernement produit
par `fetch_positions_hemicycle_officielles` (« Gouvernement (BORNE) »). Ceci
**lève la limitation documentée en [[hors-perimetre]]**, dont l'affirmation
« no open-data source for the precise portfolio has been identified yet »
est désormais factuellement dépassée — la section a été corrigée en
conséquence.

**Exclusions, explicites et justifiées** (`_TYPE_ORGANE_NON_MAPPES`, déclarées
en dur plutôt qu'omises — le silence de #369 sur ces types avait rendu son
propre périmètre difficile à rediscuter) :
- `ASSEMBLEE` : c'est le mandat électif, produit ailleurs.
- `GP`, `GOUVERNEMENT` : **doublons** — déjà collectés par
  `fetch_positions_hemicycle_officielles`.
- `CMP` (616) : organe temporaire créé par texte de loi, une entrée par
  texte — les agréger noierait les instances permanentes sous des centaines
  d'entrées à membre unique.
- `PARPOL` (222) : recoupe le champ `parti` du pivot et `groupe_politique` ;
  mêler appartenance partisane et mandat institutionnel demande son propre
  arbitrage, hors #382.
- Types Sénat (`DELEGSENAT`/`COMSENAT`/`GROUPESENAT`/`SENAT`, 4 mandats) et
  `CJR` (1) : volume négligeable.

**Agrégation de groupe** (`MANDATS_AGREGES_CATEGORIES`) : les 4 nouvelles
catégories sont agrégées — ce sont des instances de travail collectives,
exactement ce que l'agrégat cherche à montrer. Restent exclus
`mandat_electif`/`groupe_politique` (structurels, identiques pour tous les
membres), `fonction_gouvernementale` (individuelle par nature) et `autre`
(fourre-tout sans unité éditoriale, AGENTS.md §2.8).

**UI** : `MANDAT_CATEGORY_LABELS` complété, et **tri par rang de catégorie**
introduit dans `pivotAdapter.js` — à 7 catégories, le tri par `nb_membres`
seul noyait les commissions permanentes sous les groupes d'études, bien plus
nombreux.

**Effet mesuré** : `pascale-boyer` passe de 33 à **82 mandats AN exploités**
(groupe_etudes 29, commission 16, groupe_amitie 16, mission_information 13,
commission_enquete 5, extra_parlementaire 2, delegation 1). Sur les candidats
déclarés : Attal 111 → 134, Édouard Philippe 23 → 31, Le Pen 11 → 16.

**Non traité — migration des entrées héritées (#387)** : les anciennes
entrées NosDéputés mal catégorisées coexistent désormais avec leurs
équivalents AN. Mesuré sur `gabriel-attal` : **10 doublons**, le même organe
apparaissant en `commission` (libellé NosDéputés « Groupe d'études
trufficulture ») et en `groupe_etudes` (libellé AN « Trufficulture »). Les
deux référentiels ne nomment pas les organes de la même façon — l'AN omet le
préfixe de nature — donc aucun appariement exact ne les rapproche. Purge
laissée à #387, qui requiert un arbitrage sur la stratégie d'appariement et
sa tolérance au risque (un faux positif supprime un mandat réel).

**Tests** : chaque `typeOrgane` mappé produit sa catégorie ; les exclusions
ne produisent rien (pas même un fourre-tout) ; garde-fou de cohérence
vérifiant qu'aucun type n'est à la fois mappé et exclu, et que toute
catégorie produite appartient à `KNOWN_CATEGORIES` (sinon `validate_profil`
rejetterait les profils générés). Suite complète : 1160/1160.

