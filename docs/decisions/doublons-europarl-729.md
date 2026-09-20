<a id="doublons-europarl-729"></a>
# Le portail européen publie deux fois la même appartenance, et la fiche publiait deux fois le même mandat (#729) (2026-09-12)

`2026-09-12`

> **En bref** — mesuré le 12/09/2026 sur `origin/main` : le portail du Parlement européen rend **deux appartenances pour la même législature** — `type: "AUTRE"` / `role: MEMBER_PARLIAMENT` / « Membre du Parlement européen », et `type: "EU_INSTITUTION"` / `role: MEMBER` / « Membre » — **42 occurrences de chaque forme, toujours appariées**, et la seule organisation concernée est « Mandat de député européen » ; `normalize_europarl` les rendait fidèlement toutes les deux, donc **42 mandats sur 29 profils étaient publiés en double**, une fois en `categorie: "autre"`, une fois en `mandat_electif` — 42 des 52 entrées que #729 comptait dans une catégorie minoritaire ; **`role: MEMBER` ne dit pas « mandat de député »** (les commissions, groupes et délégations le portent aussi) : c'est le `type` qui l'établit, et aucune entrée `EU_INSTITUTION` du corpus ne porte un autre rôle ; la réduction garde donc **la classification de l'entrée classée et le libellé de rôle explicite de l'autre**, tous deux lus dans la source — sans quoi la fiche perdait « Membre du Parlement européen » pour un « Membre » générique ; le critère est **étroit** : même organisation, **même période exacte**, et l'une des deux entrées non classée — deux entrées classées au même organe et à la même période sont **deux fonctions distinctes** (membre et vice-président) et restent ; la fusion étant additive, la collecte corrigée ne suffit pas : `src/purge_mandats_doublons_europarl.py` retire les doublons **déjà publiés**, **41 sur 28 profils**, au **pivot seul** — le brut garde les deux entrées de la source, c'est sa nature (#580) ; le 42e n'est pas retiré, celui de `yannick-vaugrenard`, dont les mandats européens n'ont **pas d'estampille** : il relève de #718, « marquer, jamais supprimer » ; 12 tests, dont un qui a attrapé un défaut réel — le réordonnancement par identité d'objet perdait la copie enrichie, et l'ordre du portail, dont dépend le choix du groupe politique courant, se serait cassé.

## 1. Ce que la source publie

| `type` | `role` | libellé de rôle | Occurrences |
| --- | --- | --- | ---: |
| `AUTRE` | `MEMBER_PARLIAMENT` | Membre du Parlement européen | **42** |
| `EU_INSTITUTION` | `MEMBER` | Membre | **42** |

Toujours appariées, même organisation, même période. Sur les profils bruts, la
seule organisation concernée est « Mandat de député européen ».

## 2. Pourquoi garder l'entrée classée, et ce que ça faillit coûter

La propriétaire a posé la question qui manquait : **« es-tu sûr que `role:
MEMBER` est associé à un mandat de député européen ? »**

Non, pas par lui-même : `MEMBER` est le rôle générique, porté aussi par les
commissions (103 occurrences), les groupes politiques (49) et les délégations
(34). Ce qui établit le mandat, c'est le `type: EU_INSTITUTION`, dont le libellé
de la source est précisément « Mandat de député européen », sur l'organisation
« 8e législature ». Aucune entrée `EU_INSTITUTION` du corpus ne porte un autre
rôle : les 42 sont des `MEMBER`.

**Mais la classification et le libellé explicite ne sont pas portés par la même
entrée.** Garder l'entrée classée sans rien d'autre publiait `fonction:
"Membre"` et jetait « Membre du Parlement européen ». La réduction garde donc
les deux, tous deux lus dans la source, pour la même appartenance — et
`purge_mandats_doublons_europarl.py` applique la même règle au retrait, pour que
le corpus publié dise ce qu'une collecte neuve dirait.

## 3. Le critère, et ce qu'il refuse

Une paire n'est réduite que si :

- même organisation **et même période exacte** ;
- **l'une des deux entrées n'est pas classée** par la source (`type: "AUTRE"`).

**Deux entrées classées au même organe et à la même période restent.** Membre et
vice-président d'une commission, c'est deux faits : les confondre perdrait une
fonction (§2 règle 2). Le corpus en porte un cas, `COMMITTEE_PARLIAMENTARY_STANDING`
`MEMBER` + `MEMBER_SUBSTITUTE`.

## 4. Les deux étages, et celui qu'on ne touche pas

| Couche | Ce qu'elle garde |
| --- | --- |
| `raw_data/profiles/` | **les deux entrées de la source** — couche source-near, aux mêmes octets près (#580) |
| `pivot_data/profiles/` | une seule, classée, au libellé explicite |

La correction de collecte ne suffit pas : la fusion pivot est additive, et
l'entrée déjà publiée resterait (#729). D'où le retrait explicite : **41
doublons sur 28 profils**.

## 5. Le doublon qu'on laisse

`yannick-vaugrenard` porte la même paire pour 2004-2009, mais **sans
`categorie_source`** : ses mandats européens sont antérieurs à l'estampillage de
#718. Le critère exige l'estampille des deux côtés, donc il les conserve.

C'est voulu : #718 a tranché « marquer, jamais supprimer » pour cette famille,
et un retrait fondé sur la seule forme emporterait des entrées que personne n'a
établies.

## 6. L'alternative écartée

**Apparier sur le seul libellé d'organisation**, sans la période ni la
classification. C'est ce qu'une lecture rapide suggère — « Mandat de député
européen » deux fois, donc un doublon. Mais un député européen réélu porte
**plusieurs** mandats du même libellé, une par législature : l'appariement large
en aurait supprimé un sur deux. La période exacte est ce qui sépare le doublon
de la réélection.
