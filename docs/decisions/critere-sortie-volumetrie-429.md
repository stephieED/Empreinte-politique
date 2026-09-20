<a id="critere-sortie-volumetrie-429"></a>
# Le critère de sortie de l'épic volumétrie était écrit sur la mauvaise grandeur (#429) (2026-08-28)

`2026-08-28`

> **En bref** — aucune limite GitHub ne porte sur l'arbre de travail ; le critère est récrit sur le dépôt et le blob.

> **La contrainte de volume a une raison, et elle est écrite depuis le 30/08/2026** :
> [`donnees-versionnees-integrite.md`](donnees-versionnees-integrite.md). Ce critère
> mesure le coût d'une propriété d'intégrité, il ne la remet pas en cause.

L'épic #429 portait ce critère :

> « Profils versionnés **sous 500 Mo à 752 membres** »

Il est écrit sur ①, l'**arbre de travail** — ce que `du -sh` rend. Or aucune limite
GitHub ne porte là-dessus. C'est ce qui a fait recadrer l'épic quatre fois : elle a
confondu des grandeurs différentes jusqu'à finir par les nommer.

| # | Grandeur | Comparée à |
| --- | --- | --- |
| ① | Arbre de travail | **rien chez GitHub** — ni quota ni limite |
| ② | Dépôt après `gc --prune=now` | les 5 Go recommandés |
| ③ | `size` annoncé par l'API GitHub | indicatif — porte les résidus non ramassés |
| ④ | Coût d'un push — le pack réellement transmis | la limite de 2 Go par push |
| ⑤ | Coût par run — ce qu'un commit de données ajoute | la vitesse à laquelle ② et ③ montent |

## La décision

**Le critère est récrit sur ② et ④**, les deux grandeurs que les seuils protègent :

> **Dépôt sous 2 Go après `gc --prune=now`** · **push complet sous 1 Go** ·
> **mapping membre → vote / rôle / mandat intégralement préservé**.

> **Récrit le 29/08/2026 par #580.** Le critère portait une **quatrième**
> clause — « aucun blob au-dessus de 50 Mo » — retirée depuis. Ce n'était pas
> un critère : un critère s'atteint, celui-là se déclenche, et il a été franchi
> le jour même de son écriture. Il est devenu un **garde-fou surveillé, avec
> une conduite à tenir écrite** et un contrôle qui échoue :
> [#garde-fou-blob-580](partition-profils-legislature-580.md#garde-fou-blob-580). Les trois clauses ci-dessus, elles,
> sont des propriétés du dépôt, mesurables — et **atteintes** au 29/08/2026 sur
> le corpus doublé : dépôt **627 Mo** après `gc` (× 8), push **204 Mo** (× 10),
> mapping préservé.

L'alternative — garder le critère et ouvrir une suite sur l'ergonomie du checkout —
a été écartée : elle aurait laissé #192 porter un blocage que la mesure a levé.
Le sujet du checkout est réel mais distinct, et il est suivi par #553.

## Mesuré le 28/08/2026, à 476 profils

La dernière mesure de l'épic datait de **209 profils** ; ces chiffres sont pris sur
la population du jour, pas reportés de l'ancienne. Méthode : ② sur un
`git clone --mirror --no-hardlinks` dans un temporaire suivi d'un `gc --prune=now`,
comme #434 ; ④ par `git pack-objects` sur les blobs exacts du HEAD. Aucun `gc` sur
le dépôt de travail.

| Clause | 209 (20/08) | **476 (28/08)** | Seuil | Marge | |
| --- | ---: | ---: | --- | ---: | --- |
| ② dépôt après `gc` | 294 Mo | **415 Mo** | 2 Go | × 4,9 | ✅ |
| ④ push complet | 44,3 Mo | **110,5 Mo** | 1 Go | × 9,0 | ✅ |
| plus gros blob | 49,8 Mo | **38,6 Mo** (`pivot_data/amendements/15.json`) | 50 Mo | × 1,3 | ✅ |
| mapping préservé | — | aucune suppression de champ (#431, #432) | — | — | ✅ |

Pour mémoire, ① — la grandeur du critère d'origine — vaut **~4,85 Go**
(`raw_data/profiles` 4 321 Mo, `pivot_data/profiles` 359 Mo,
`pivot_data/amendements` 182 Mo, `pivot_data/scrutins.json` 8,3 Mo).

## Deux prédictions de l'épic, vérifiées par cette mesure

**La saturation de l'index partagé.** `pivot_data/scrutins.json` devait plafonner
(× 1,013 de 209 à 752). Il fait **8,3 Mo** à 476 profils — exactement la valeur
projetée à 752. Un index partagé cesse de grandir quand la population couvre déjà
tous les objets.

**Le taux de compression ne se dégrade pas avec l'effectif, il s'améliore** :
`raw_data/profiles` × 46,2 à 209 profils, **× 52,1** à 476 ; `pivot_data/profiles`
× 17,6 → × 19,8 ; `pivot_data/amendements` × 19,7 → × 19,3. Chaque amendement est
recopié chez davantage de signataires, donc se déltifie mieux. Conséquence : la
projection de ④ à 752 tient — ~172 Mo annoncés par l'épic, ~175 Mo extrapolés
depuis les 110,5 Mo mesurés.

## La réserve, sur la clause qui a basculé — et la prévision qui était périmée

« Aucun blob au-dessus de 50 Mo » ne dépend **pas du nombre de profils** : le plus
gros blob est un index d'amendements. Cette section annonçait, le 28/08/2026, que
les index des XIV<sup>e</sup>, XV<sup>e</sup> et XVI<sup>e</sup> ne couvraient que
« 19,5 %, 30,7 % et 29,5 % » des archives figées.

**Ces trois chiffres étaient périmés au moment où ils ont été écrits.** Remesurés
le 29/08/2026 (#580), après le run `33200210924` qui a rattrapé une large part du
retard :

| Lég. | Archive figée | Index publié | Couverture annoncée le 28/08 | **Couverture mesurée le 29/08** |
| --- | ---: | ---: | ---: | ---: |
| XIV | 154 296 | 59 358 | 19,5 % | **38,5 %** |
| XV | 307 644 | 206 771 | 30,7 % | **67,2 %** |
| XVI | 162 240 | 121 110 | 29,5 % | **74,7 %** |
| XVII | *(en cours, pas d'archive figée)* | 96 893 | — | — |

Ce qui reste à collecter — **× 1,5 sur la XV, × 1,3 sur la XVI** — n'est donc plus
un facteur 3 à 5, mais il pèse encore sur une marge devenue mince : au 29/08 le
plus gros blob est un **profil brut** (`raw_data/profiles/mathilde-panot.json`,
56,0 Mo), pas un index, et il n'est qu'à **× 1,79** de la limite dure de 100 Mo.
Achever la collecte des archives consommerait l'essentiel de cette marge.

La clause a donc basculé, et elle a basculé **le jour même de son écriture** :
huit fichiers dépassent 50 Mo au 29/08, cinquante-quatre dépassent 45. Ce n'était
pas un fil de détente, c'était un fil déjà tendu. La suite — pourquoi il sort du
critère, ce qui le remplace, et ce qui a fait tomber ce blob à 23,4 Mo — est
en [#garde-fou-blob-580](partition-profils-legislature-580.md#garde-fou-blob-580) et
[#partition-profils-legislature-580](partition-profils-legislature-580.md).

## Ce qui reste, et qui n'est pas un quota

- **Le temps de checkout CI.** ~4,85 Go d'arbre de travail, c'est le seul coût réel,
  et le remède est écrit : option A de #434 (`--filter=blob:none --sparse`), ce que
  `tests.yml` fait déjà depuis #473. Suivi par #553.
- **La rétention.** Un commit de données coûtait 12,2 Mo à 209 profils, il en coûte
  **22 à 76** aujourd'hui, et il reste deux commits avant que la fenêtre de 30
  de #434 morde. Suivi par #551.

Ni l'un ni l'autre n'est une limite GitHub. Le budget d'exécution à pleine échelle,
lui, **a été mesuré** — 54,9 min contre 630 annoncées, voir
[#budget-execution-pleine-echelle-467](budget-execution-pleine-echelle-467.md) : ne pas
le redire « projeté ».

---

