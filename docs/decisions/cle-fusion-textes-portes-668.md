<a id="cle-fusion-textes-portes-668"></a>
# Une clé de fusion en `a or b` change d'identité quand `a` se remplit (#668) (2026-08-31)

`2026-08-31`

> **En bref** — le rang 2 de #639 a réparé `source_url`, `null` sur 472 / 472 textes portés, et la clé `source_url or (titre, date_min, legislature)` a basculé de branche sous les entrées déjà publiées : 940 entrées pour 472 dossiers réellement collectés, **468 doublons** en ligne sur 22 profils (l'issue en comptait 471, écart re-mesuré — 3 sont des dossiers distincts partageant un titre, `ludovic-mendes` portant la proposition de loi `DLR5L17N51626` **et** son rapport `DLR5L17N51485`) ; la clé passe sur `dossier_id`, l'identifiant AN publié depuis #639 et déjà porté au brut par `dossiers_legislatifs[].id`, `source_url` en sort (0 repli portant deux `dossier_id` distincts, et 4 entrées identifiées n'ont pas d'URL) ; le `or` subsiste pour les entrées sans identifiant — le supprimer les effondrerait sur une clé `None` (#432) — et ce qui neutralise la bascule est la **reprise**, `clean_stale_textes_portes`, qui existait sous ce nom pour ce motif mais départageait sur un critère de schéma que les deux versions satisfont **et n'était appelée nulle part** : 940 → 472, exactement les 472 dossiers collectés, 468 retirées à déclarer par `allow_declared_losses` ; motif cherché ailleurs et **mesuré** — `_pivot_amendement_key` (6 091 732), `_pivot_vote_key` (1 312 951) et `_pivot_intervention_key` (16 242) sont à 100 % sur leur branche principale, donc aucune ne peut basculer, ce que la mesure constate sans le garantir ; l'extension d'`audit_diff_profils` aux **apparitions** est nommée et laissée hors lot (périmètre #649).

**Régression en ligne.** Introduite par le rang 2 de #639 (PR #651), révélée par
le premier run qui l'exécute (`33395056902`, 31/08/2026), publiée sur le site.

## Mesure de référence

Prise le 31/08/2026 sur `origin/main`, en flux sur les 481 profils pivot
committés et sur les profils bruts correspondants — pas sur une régénération,
pas sur une estimation.

| | |
| --- | ---: |
| Profils publiant des textes portés | 22 sur 481 |
| Entrées publiées | **940** |
| Entrées portant un `dossier_id` | 472 |
| Entrées héritées, sans `dossier_id` | 468 |
| Dossiers réellement collectés (`dossiers_legislatifs` du brut, mêmes 22 profils) | **472** |

| Profil | Publié | Collecté | Après reprise | Retiré |
| --- | ---: | ---: | ---: | ---: |
| `edouard-philippe` | 566 | 283 | 283 | 283 |
| `bruno-retailleau` | 72 | 36 | 36 | 36 |
| `gabriel-attal` | 68 | 34 | 34 | 34 |
| `jean-luc-melenchon` | 66 | 33 | 33 | 33 |
| `marine-le-pen` | 46 | 23 | 23 | 23 |
| `laurent-wauquiez` | 18 | 9 | 9 | 9 |
| `thomas-cazenave` | 13 | 7 | 7 | 6 |
| `pierre-cazeneuve` | 12 | 6 | 6 | 6 |
| `ludovic-mendes` | 11 | 6 | 6 | 5 |
| `stephane-mazars` | 11 | 6 | 6 | 5 |
| `jerome-guedj` | 10 | 5 | 5 | 5 |
| `david-amiel` | 8 | 4 | 4 | 4 |
| `yael-braun-pivet` | 8 | 4 | 4 | 4 |
| `sophie-panonacle` | 6 | 3 | 3 | 3 |
| `yannick-chenevard` | 6 | 3 | 3 | 3 |
| `annie-vidal` | 4 | 2 | 2 | 2 |
| `jean-michel-jacques` | 4 | 2 | 2 | 2 |
| `xavier-roseren` | 3 | 2 | 2 | 1 |
| `charlotte-parmentier-lecocq` | 2 | 1 | 1 | 1 |
| `olivier-dussopt` | 2 | 1 | 1 | 1 |
| `sophie-errante` | 2 | 1 | 1 | 1 |
| `stella-dupont` | 2 | 1 | 1 | 1 |
| **TOTAL, 22 profils porteurs sur 481** | **940** | **472** | **472** | **468** |

Les 459 autres profils publiés ont une liste `textes_portes[]` vide : ils
n'entrent dans aucune colonne.

**Le chiffre de l'issue ne se reproduit pas tout à fait, et l'écart dit quelque
chose.** #668 annonce 471 doublons, comptés en « entrées moins titres
distincts ». Re-mesuré sur les identifiants : **468**. Les 3 de différence sont
des dossiers **réellement distincts qui partagent un titre** — `ludovic-mendes`
porte la proposition de loi « Convertir des centrales à charbon… »
(`DLR5L17N51626`) *et* le rapport « Proposition de loi visant à convertir des
centrales à charbon… » (`DLR5L17N51485`), deux dossiers, deux dates, deux
`dossier_id`. Le titre n'est pas une identité, y compris pour compter le
défaut : 468 est le chiffre, 471 l'approximation qui l'a fait voir.

## Le défaut

`merge_profile._pivot_texte_key` valait :

```python
return t.get("source_url") or (t.get("titre"), t.get("date_min"), t.get("legislature"))
```

Le rang 2 de #639 a réparé `normalize_profil._normalize_texte_porte`, qui
publiait `source_url: null` sur **472 / 472** entrées : il lisait
`url_source`/`url_institution`, absents de 100 % des entrées brutes, alors que
la collecte AN écrit `source_url` depuis #400. La correction est juste — un fait
publié sans sa source primaire viole §2 règle 2.

| | Entrée publiée avant le run | La même, produite par le run |
| --- | --- | --- |
| `source_url` | `null` | renseignée |
| Branche du `or` empruntée | le repli `(titre, date_min, legislature)` | **`source_url`** |

Les deux clés ne sont pas comparables. `merge_dossier_records` a donc vu deux
dossiers là où il y en avait un, et conservé les deux.

**Ce n'est pas le défaut de #540, c'est son symétrique.** Là, une clé
*collante* — l'URL d'archive Syceron, la même pour toutes les interventions
d'une législature — absorbait des entrées distinctes : 7 767 collectées, 891
publiées. Ici, une clé **volatile** dédouble une même entrée. Dans les deux cas
la cause est la même phrase : *une URL n'est pas un identifiant*. Ce qui a
changé n'est pas la donnée, c'est la branche du `or` que l'objet emprunte.

## La décision

**1. La clé repose sur `dossier_id`.** `DLR5L15N37607`, l'identifiant AN du
dossier, publié depuis #639, et le **même** que `dossiers_legislatifs[].id` au
brut : les deux étages disent désormais la même chose de ce qu'est un dossier,
la seule forme qui garantisse qu'une entrée collectée arrive publiée une fois et
une seule. C'est la leçon de #540, appliquée à l'identique. `source_url` sort de
la clé : mesuré, il ne discrimine rien de plus (0 repli portant deux
`dossier_id` distincts sur les 940 entrées), et 4 des 472 entrées identifiées
ne le portent même pas.

**2. Les entrées sans `dossier_id` gardent le repli** `(titre, date_min,
legislature)`. `date_max` en est exclu : c'est un agrégat qui avance au fil de
la procédure, et l'inclure ferait réapparaître le dossier comme neuf à chaque
étape franchie. Le `or` subsiste donc, et avec lui le risque de bascule — aucune
clé ne peut lire un identifiant qu'une entrée ne porte pas, et le supprimer
réduirait toutes ces entrées à une seule clé `None`, la perte silencieuse que
`_pivot_vote_key` décrit (#432).

**3. Ce qui neutralise la bascule n'est pas la clé, c'est la reprise.**
`clean_stale_textes_portes` écarte une entrée **sans** `dossier_id` quand au
moins une entrée **avec** `dossier_id` porte le même repli. Elle est alors, par
construction, la même entrée avant sa renormalisation : c'est exactement la clé
sous laquelle la fusion l'avait rangée. Sans jumelle identifiée — collecte en
échec, dossier retiré de l'open data, entrée héritée d'une source sans
identifiant — rien n'est écarté (`collecte-vide-necrase-jamais.md`).

C'est le patron de `clean_stale_interventions` (#540), qui est lui-même le
patron de `clean_stale_textes_portes` avant ce lot : la boucle est refermée.

## Deux choses que le dépôt savait déjà, et qui n'ont pas suffi

**La fonction existait, sous ce nom, pour ce motif.** Sa docstring décrivait les
doublons hérités d'une clé incluant `role`. Le raisonnement était juste ; il
visait un champ **du tuple**, pas le cas où le champ **principal** du `or` passe
de `null` à une valeur.

**Et elle n'était appelée nulle part.** Ni par `merge_pivot_profile`, ni par la
passe pivot, ni par un script : seulement importée par un test. Un nettoyage que
rien n'exécute n'a jamais nettoyé quoi que ce soit — c'est la seconde moitié de
la régression, et pourquoi les 468 doublons ont survécu à chaque run. Elle est
désormais appelée à l'emplacement exact où `merge_pivot_profile` appelle
`clean_stale_interventions`.

Son critère de départage a changé avec l'appel. « Conserver l'entrée la plus
complète au sens du schéma » — `type_rapport` et `stade_procedural` présents —
**ne discrimine plus rien** : les 940 entrées publiées portent toutes les deux
clés, et les deux versions d'un même dossier auraient été départagées au hasard
de l'ordre de la liste. Le départage se fait sur l'identifiant.

## Le motif ailleurs : mesuré, pas supposé

Toute clé de fusion en `a or b` porte le même défaut latent. Il ne devient réel
que si le corpus publié **straddle** les deux branches. Mesuré sur `origin/main`
le 31/08/2026, en flux sur les 481 profils :

| Clé | Forme | Entrées publiées | Sur la branche principale | Verdict |
| --- | --- | ---: | ---: | --- |
| `_pivot_texte_key` | `source_url` ou triplet | 940 | 472 (50,2 %) | **le défaut, corrigé ici** |
| `_pivot_amendement_key` | `amendement_id`, puis `uid`/`source_url`/triplet | 6 091 732 | 6 091 732 (**100 %**) | branche de repli jamais atteinte |
| `_pivot_vote_key` | `scrutin_id` ou `("non_resolu", numero, date)` | 1 312 951 | 1 312 951 (**100 %**) | idem |
| `_pivot_intervention_key` | `intervention_id`, puis `source_url`/contenu | 16 242 | 16 242 (**100 %**) | la reprise #540 a fini son travail |

Aux étages bruts, sur les 22 profils porteurs de textes portés :
`_dossier_key` = `(legislature, id)` — pas de `or`, `id` renseigné 472 / 472 ;
`_intervention_key` = `(id, url or url_detail)` — le `or` est **dans** le tuple
et peut donc basculer, mais `id` et `url` sont renseignés 16 242 / 16 242.

**Rien d'autre à corriger aujourd'hui.** Aucune entrée publiée du corpus ne
repose sur une branche de repli, donc aucune ne peut basculer au prochain run.
Ce que la mesure ne dit pas : elle décrit l'état du corpus, pas une garantie de
construction. Une source qui cesserait de fournir `amendement_id`, `scrutin_id`
ou `intervention_id` recréerait exactement ce défaut, et **aucun contrôle ne le
verrait** — c'est le point suivant.

## Ce qui n'a rien vu, et ce qui n'est pas fait ici

`audit_diff_profils` surveille les **disparitions** des listes stables, pas les
**apparitions**. 471 entrées de plus n'ont déclenché aucun contrôle, aucune
annotation, aucune tolérance à cocher. C'est la même famille que #649 — les
agrégats publiés que rien ne regardait — mais dans l'autre sens.

**Étendre `audit_diff_profils` aux apparitions n'est pas fait dans ce lot** :
c'est le périmètre de #649, déjà livré, et une extension serait un autre lot,
avec son propre seuil et sa propre tolérance. Ce lot le nomme sans y toucher.

Une chose l'aurait vu, en revanche, et elle existait : `audit_collecte_vs_publie`
(#545) rapportait un **surplus** de +468 sur `textes_portes` face à la relation
déclarée `dossiers_legislatifs`. Un surplus y est *signalé*, jamais bloquant —
délibérément, parce qu'un pivot peut légitimement enrichir. Après ce lot,
472 = 472 : la relation redevient exacte.

## Ce que coûte la correction

468 entrées retirées d'une liste **stable** au sens d'`audit_diff_profils` : le
prochain run bloquera au commit, et c'est voulu. La perte se déclare par
`allow_declared_losses` avec son motif — « reprise #668 : 468 doublons de
`textes_portes` produits par la bascule de clé du rang 2 de #639, 940 → 472
entrées, égales aux 472 dossiers collectés » — **jamais** en désarmant le
contrôle (AGENTS.md §3c).

## Alternative écartée

**Keyer *toujours* sur le repli `(titre, date_min, legislature)`**, ce qui
supprimerait le `or` par construction. Il est discriminant aujourd'hui : 0
collision sur les 940 entrées. Mais il rend l'identité du dossier otage de son
libellé — une correction typographique du titre à l'AN, ou un `date_min` qui
recule d'un document versé après coup, republierait le dossier comme une entrée
neuve. Le même doublon, sans identifiant pour le rattraper cette fois.

## Références

- `src/merge_profile.py` : `_pivot_texte_key`, `_repli_texte_key`,
  `clean_stale_textes_portes`, son appel dans `merge_pivot_profile`.
- `tests/test_textes_portes_cle_fusion_668.py` : le garde-fou, sur réductions
  verbatim d'entrées publiées (#510).
- `docs/decisions/cle-fusion-interventions-540.md` : le symétrique.
- `docs/decisions/collecte-vide-necrase-jamais.md` : la preuve de non-perte.
