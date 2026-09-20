<a id="sigle-groupe-europeen-863"></a>
# Le groupe européen dit son sigle et ce que la source en dit, sans changer de catégorie (#863) (2026-09-12)

`2026-09-12`

> **En bref** — besoin remonté par la session interface : la frise du parcours ne garde, par segment parlementaire, que le **sigle du groupe** et la place dans l'hémicycle ; à l'Assemblée les deux sont publiés, au Parlement européen **aucun des deux** ne l'était — le groupe vivait sous `categorie: "autre"`, au milieu des délégations et du parti national, reconnaissable seulement à la lecture de son intitulé ; **la donnée était déjà collectée** et c'est la normalisation qui la jetait : le brut porte `type` (classification du portail) et `organisation_sigle` sur **63 mandats de groupe, 61 avec un sigle** ; deux champs entrent donc au pivot — `sigle_organe`, le sigle tel que le portail l'écrit (`GUE/NGL`, `S&D`, `Verts/ALE`, `PfE`, `NI`…), et `type_organe_source`, la classification traduite dans une nomenclature **fermée** (`KNOWN_TYPES_ORGANE_SOURCE`) ; **un identifiant n'est pas un sigle** : les 2 mandats de `stephane-le-foll` dont le portail ne résout pas l'organisation (`"2953"`, `organisation_nom` nul) sont publiés `null` avec `sigle_organe_non_resolu` et son motif (§2 règle 5) ; une appartenance que la source **ne classe pas** (`AUTRE`) reste **sans** `type_organe_source`, l'absence disant que la source ne s'est pas prononcée — jamais « autre » ; **la catégorie ne bouge pas**, et c'est l'arbitrage du lot : `_mandat_key` la contient, donc re-ranger l'entrée en `groupe_politique` en **ajouterait** une au lieu de la corriger, 63 doublons — le défaut de #668 ; **septième occurrence de la famille** #492/#639/#641/#696/#710/#718, d'où `backfill_mandat_organe_source` câblé **aux deux étages**, sans quoi le champ atteindrait le brut sans jamais atteindre la couche que `web/` lit ; 9 tests.

## 1. Le besoin, et ce qu'il n'était pas

La session interface l'a formulé ainsi : « le groupe politique au Parlement
européen, identifiable **sans lire son intitulé**, et son sigle ». C'est une
demande de **donnée**, pas d'affichage : ce que le pivot publie, l'interface le
met en forme.

## 2. La donnée était déjà là

| Couche | Ce qu'elle portait avant ce lot |
| --- | --- |
| `raw_data/profiles/<slug>.json` → `mandat_europeen.mandats_europeens[]` | `type: "EU_POLITICAL_GROUP"`, `organisation_sigle: "GUE/NGL"`, `organisation_nom` |
| `pivot_data/profiles/<slug>.pivot.json` → `mandats[]` | `categorie: "autre"`, `label` = l'intitulé, `categorie_source: "europarl"` — **ni type, ni sigle** |

63 mandats de groupe sur 29 profils bruts, **61 avec un sigle résolu**, 19
sigles distincts.

## 3. Deux champs, et ce que chacun dit

| Champ | Ce qu'il dit |
| --- | --- |
| `sigle_organe` | le sigle **tel que le portail l'écrit** — `GUE/NGL`, `S&D`, `Verts/ALE`, `PfE`, `ENF`, `Renew`, `NI`… |
| `type_organe_source` | ce que la **source** dit de l'organe, dans une nomenclature fermée : `groupe_politique_europeen`, `commission_parlementaire_europeenne`, `parti_national_au_parlement_europeen`, `delegation_parlementaire_europeenne`… |

`categorie` répond à « comment le pivot range l'entrée » ; `type_organe_source`
répond à « ce que la source en dit ». Les deux questions sont distinctes, et
c'est la seconde que l'interface pose.

## 4. Ce que le lot refuse de publier

**Un identifiant n'est pas un sigle.** `stephane-le-foll` porte
`organisation_sigle: "2953"` avec `organisation_nom` à `null` : c'est
l'identifiant d'organisation que le collecteur reprend quand la résolution
échoue. Publié tel quel, il passerait pour le sigle d'un groupe. Il devient
`sigle_organe: null` accompagné de `sigle_organe_non_resolu`, qui nomme la
raison — la forme que §2 règle 5 et AGENTS §5 imposent.

**Une appartenance non classée reste sans marqueur.** Le portail publie `type:
"AUTRE"` quand il ne classe pas. La clé est alors **absente**, comme
`categorie_source` l'est quand personne n'a établi la catégorie (#718).

## 5. L'arbitrage : la catégorie ne bouge pas

Ranger `EU_POLITICAL_GROUP` sous la catégorie existante `groupe_politique`
serait sémantiquement juste, et c'est ce qu'une lecture rapide propose.

**C'est impossible sans dégâts** : `_mandat_key` contient `categorie`. Une
entrée neuve rangée autrement porterait donc une **clé différente** de l'entrée
publiée, et la fusion additive l'**ajouterait** au lieu de la remplacer — 63
doublons, exactement le défaut de #668. Le marqueur est un champ neuf, pas une
re-catégorisation.

Une re-catégorisation reste possible plus tard, mais elle demande son propre
retrait des entrées publiées, comme #729 a dû en faire un pour le doublon
européen.

## 6. Le report nommé, aux deux étages

`_mandat_key` ne contient aucun des deux champs neufs : l'entrée neuve qui les
porte a la même clé que l'ancienne, et la fusion garde l'ancienne. Sans report,
le correctif serait **vrai et sans effet** sur le corpus publié — la septième
fois que cette famille se présente (#492, #639, #641, #696, #710, #718).

`backfill_mandat_organe_source` est **monotone** : il ne pose un champ que s'il
est absent, ne reporte que des valeurs renseignées, et laisse muette une entrée
qu'aucune collecte neuve ne couvre. Une entrée sans sigle dit « la source ne
l'a pas classée », jamais « elle n'a pas de sigle ».

## 7. Ce que le lot ne fait pas

- **L'affichage** : la frise, le rendu du sigle et la place dans l'hémicycle
  relèvent de la session interface.
- **Le sigle des groupes de l'Assemblée** : il vit dans l'intitulé
  (`Groupe politique (FI)`), et l'interface le lit déjà. L'uniformiser est un
  autre lot.
