# `debut_dans_groupe` se lit sur le mandat de groupe, plus sur le premier mandat électif (#653) (2026-08-31)

`2026-08-31`

> **En bref** — le champ mesurait le début du **premier mandat électif**, approximation devenue fausse dans l'autre sens depuis #647 (Vincent Rolland publié « LR depuis 2002-06-19 » alors qu'il entre dans le groupe LR de la XVIe le 2022-06-29) ; les dates viennent désormais du **mandat de groupe politique de la législature de la fiche** que le roster AMO30 rend déjà — transit écarté, organes successifs recollés (#526) —, ce qui corrige **451 des 452 dates d'entrée** des 5 fiches AN de la XVIe, dont 8 de 20 ans, sans retirer une seule entrée `membres[]` ni laisser un seul membre sans mandat de groupe identifiable ; sans roster les dates sortent `null` et comptées, **jamais repliées sur le mandat électif** (§2 règle 5) ; `effectif.actuel` est nommé pour ce qu'il compte — les membres sans fin d'appartenance **dans cette législature**, donc 0 sur une législature close — et le roster mono-législature est instruit sans être élargi, faute d'un arbitrage sur la continuité `REN`/`EPR` et sur des dénominateurs de cohésion composites.

`membres[].debut_dans_groupe` ne mesurait pas l'entrée dans le groupe. Il
mesurait le début du **premier mandat électif** de la personne dans la chambre.
La docstring de `_derive_membre_entry` l'écrivait sans détour — « *approximation
correcte pour les cas sans changement de groupe en cours de mandat* » —, le nom
du champ disait l'inverse, et `schema_groupe.py` le commentait « début de
l'appartenance à CE groupe ».

L'approximation tenait tant qu'un profil ne portait **qu'un** mandat électif, le
plus récent. #647 a reconstruit la carrière complète (613 périodes nouvelles sur
393 profils) et le « premier mandat électif » remonte désormais à toute la
carrière. Avant #647 la date était trop récente, après elle est trop ancienne :
dans les deux cas elle ne mesure pas ce que son nom annonce.

## L'écart, mesuré

Sur les **452 entrées `membres[]` des 5 fiches AN de la XVIe législature**
publiées en `3c8e1f0c`, comparées au roster AMO30 dérivé de l'archive du
17/08/2026 :

| Fiche | Membres | `debut` change | `fin` change | Recul médian | Recul max |
| --- | ---: | ---: | ---: | ---: | ---: |
| `groupe-AN-REN-16` | 193 | 193 | 106 | 5,0 ans | 20,0 ans |
| `groupe-AN-RN-16` | 90 | 90 | 80 | 10 jours | 5,0 ans |
| `groupe-AN-LFI-16` | 76 | 76 | 61 | 10 jours | 10,0 ans |
| `groupe-AN-LR-16` | 62 | 61 | 46 | 5,0 ans | 20,0 ans |
| `groupe-AN-SOC-16` | 31 | 31 | 27 | 5,0 ans | 15,0 ans |
| **Total** | **452** | **451** | **320** | | |

Le « recul » est la distance entre la date publiée et la date réelle
d'entrée dans le groupe, toujours dans le même sens : la date publiée était
**antérieure** à l'appartenance. 233 des 452 entrées reculent de moins d'un an
(l'élection du 19/06/2022 au lieu de la constitution des groupes du 29/06/2022),
153 de 5 à 6 ans (législature précédente), 8 de 20 ans. Une seule entrée est
inchangée.

Le cas de l'issue se reproduit exactement : **Vincent Rolland**, publié
`2002-06-19 → null, actif`, devient `2022-06-29 → 2024-06-09, inactif`.

**Aucune entrée `membres[]` n'est retirée** — la liste est surveillée par
`audit_diff_profils` et c'est voulu —, et **aucun membre publié n'est sans
mandat de groupe identifiable** : 0 sur 452, sur les cinq fiches.

## La décision

Les dates viennent du **mandat de groupe politique** (`typeOrgane == "GP"`) de
la législature de la fiche, tel qu'`an_roster.deriver_membres_organes` le rend
déjà : mandats de transit écartés (#526, piège 1), organes successifs recollés
(#526, piège 3), période bornée à la législature demandée. Ce n'était pas une
donnée à collecter — elle traversait le pipeline sous `mandat_debut` /
`mandat_fin` et servait uniquement à filtrer.

`build_groupe_profile` reçoit une table `appartenances` (`id du pivot →
{debut, fin}`), construite par `appartenances_depuis_roster`. Elle est indexée
sur l'`id` du pivot **chargé**, pas sur le slug du roster : les deux coïncident
depuis #487, et les indexer sur le slug rendrait le rapprochement muet le jour
où ils divergeraient — ce qui, sur des dates publiées, se lirait « appartenance
non établie » plutôt que comme un défaut.

**Aucun repli sur le mandat électif.** Sans appartenance — aucun roster fourni,
ou membre absent de celui-ci, ce qui est le cas des `recovered_slugs` de
`--merge-existing` — les deux dates sont `null`, `actif` est `false`, et
`meta.warnings` en porte le compte et les noms (AGENTS.md §2 règle 5). Un repli
remettrait la date fausse en place sous un nom exact, c'est-à-dire exactement
l'état que ce lot retire.

## Ce que `effectif.actuel` compte

`effectif.actuel` compte les membres **sans date de fin d'appartenance dans
cette législature**. Ce n'est pas « les membres en fonction aujourd'hui », et ça
ne l'était pas davantage avant : la valeur comptait les membres encore députés à
la date du calcul, sur une fiche qui décrit une législature close.

Une législature achevée referme **toutes** ses appartenances — les 452 mandats
GP de la XVIe se terminent le 2024-06-09 ou avant. `effectif.actuel` passe donc
de `85 / 75 / 60 / 38 / 27` à **0 sur les cinq fiches**, et `periode.actif` à
`false` avec `periode.fin = 2024-06-09`. C'est ce que dit l'archive. Un
avertissement le nomme sur chaque fiche, parce qu'un `0` à côté d'un `membres[]`
de 193 entrées se lit comme une perte s'il n'est pas expliqué (AGENTS.md §2.5).

Deux conséquences mécaniques, à ne pas prendre pour des pertes :

- `periode.debut` avance de `2002-06-19` / `2007-06-20` / `2012-06-20` /
  `2017-06-18` à `2022-06-29` sur les cinq fiches. C'est un scalaire surveillé
  par `audit_diff_profils`, mais un **changement de valeur**, jamais un passage
  à `null` : il est relevé, il ne bloque pas.
- `mandats_agreges[].nb_membres_actifs` tombe à 0 partout, puisqu'il vaut
  `mandat actif ET appartenance active`. L'interface masque déjà la mention
  « · N actifs » quand elle vaut 0 (`GroupProfile.jsx`). `nb_membres`, lui, ne
  bouge pas — l'éligibilité d'un mandat catégoriel se calcule sur les mandats
  électifs, que ce lot ne touche pas.

L'interface ne lit pas `effectif.actuel` pour son compteur d'effectif :
`pivotAdapter.buildGroupView` prend `meta.couverture_roster.roster_total` et ne
retombe sur `effectif.actuel` que si le bloc manque — ce qui n'est le cas
d'aucune fiche AN.

## Le roster mono-législature : instruit, non tranché

`an_roster.organes_du_groupe` filtre les organes sur la législature configurée
et `raw_data/groupes_reels.json` déclare `legislature: "16"` pour les cinq
fiches AN. **Une fiche décrit donc une législature**, ce qui est cohérent avec
`cohesion_votes`, qui ne porte que des scrutins de la XVIe. Ce n'est pas un
défaut, et ce lot ne l'élargit pas.

Ce qu'il faudrait pour suivre un groupe d'une législature à l'autre, dans
l'ordre où ça se heurte :

1. **La table le permet déjà.** `correspondance_sigles_an` décrit ses groupes
   **par législature** et porte déjà les cinq entrées de la XVIIe (`EPR`, `SOC`,
   `RN`, `LFI`, `DR`), avec leurs organes et leur effectif mesurés. Lire les
   mandats GP de plusieurs législatures ne demande aucune collecte nouvelle :
   l'archive AMO30 les porte toutes (Vincent Rolland y a les législatures 12, 15,
   16 et 17).
2. **Mais un sigle n'est pas une continuité.** `REN` de la XVIe et `EPR` de la
   XVIIe sont deux entrées distinctes de la table ; `LR` devient `DR`. Décider
   qu'un groupe « continue » d'une législature à l'autre est un jugement
   éditorial, pas une jointure — et le publier comme un fait est un jugement
   publié (AGENTS.md §2 règle 1).
3. **Et `cohesion_votes` suivrait.** Une fiche multi-législature aurait des
   dénominateurs composites : « X % de cohésion » sur deux législatures dont
   l'une compte 62 membres et l'autre 64 n'est pas un ratio publiable en l'état
   (AGENTS.md §2.7).

**C'est un arbitrage de la propriétaire, pas une suite technique.** Tant qu'il
n'est pas rendu, une représentation de l'effectif dans le temps reste hors
périmètre — et elle l'est désormais **par construction** et non par accident :
avec la date corrigée, tous les membres d'une fiche entrent le même jour, donc
la courbe trompeuse que l'issue décrit ne se calcule plus.

## L'alternative écartée : lire les mandats `groupe_politique` du profil

Un profil pivot porte déjà des mandats `categorie == "groupe_politique"`, écrits
par `fetch_positions_hemicycle_officielles`, avec les bonnes dates. Les lire
aurait évité tout branchement.

Mesuré sur les 452 membres : **402 ont un mandat `groupe_politique` dont les
dates correspondent exactement au roster, 50 non**, dont **les 31 membres de
`AN:SOC`** — le groupe aux deux organes successifs (`PO800496` puis `PO830170`),
que le profil publie en deux périodes séparées quand le roster les recolle. Il
aurait donc fallu reconstruire dans `group_profile` le recollement d'organes que
`an_roster` fait déjà, à partir d'une donnée qui ne porte ni sa législature ni
son organe. La source de vérité reste où elle est.

Cette lecture a par ailleurs une limite propre :
`fetch_positions_hemicycle_officielles` ne couvre que les **législatures
achevées** (l'AN ne qualifie pas `positionPolitique` sur la législature en
cours). Rolland n'y a que ses législatures 15 et 16, pas la 17. Le roster, lui,
lit l'archive directement.
