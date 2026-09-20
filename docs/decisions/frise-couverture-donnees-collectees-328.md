# La frise de couverture passe à une seule catégorie, « Données collectées », teintée par institution — 11/09/2026 (#328)

`2026-09-11`

> **En bref** — la frise de `/couverture` coloriait chaque trait selon la fiche d'où il venait — candidats `#3F5166`, gouvernements `#8A6B4C`, groupes `#6F5B7A` (`page-couverture-commune-328`) ; depuis `teintes-des-institutions-328`, le bleu ardoise des candidats se lisait comme le bleu de l'Union européenne, et la décision avait laissé l'écart ouvert ; deux reprises aux teintes d'institution ont été rendues sur la vraie page — la population portée par la **clarté** (candidats en teinte pleine, fiches de groupe ou de gouvernement en teinte claire) ou par la **forme** (bande claire et filet foncé) — et la propriétaire a écarté les deux : **tous les faits portés passent sous une seule catégorie « Données collectées »**, d'abord en noir, puis — à sa demande, une fois la fiche d'origine sortie de la couleur — **dans la teinte de leur institution**, les valeurs de la fiche candidat (Assemblée `#803060`, Gouvernement `#85510D`, Parlement européen `#003399`) ; le jaune « non collecté » et la hachure « non publié » ne bougent pas, le survol d'un segment nomme encore sa fiche d'origine, et le paragraphe qui répétait la légende sous le titre est réduit à « Chaque ligne se déplie sur ses champs ».

## Contexte

`page-couverture-commune-328` avait fait de la fiche d'origine une **teinte**,
après avoir écarté une teinte par nature du fait : la question de la page était
« de quelle fiche ce trait vient-il ». `teintes-des-institutions-328` a ensuite
donné l'Union au bleu `#003399`, le Gouvernement à l'ocre, l'Assemblée au prune,
et consigné une divergence assumée : les trois teintes de population
« valaient celles de la fiche ; elles ne les valent plus ».

## Ce qui a été rendu

| Variante | Encodage de la fiche d'origine | Coût mesuré sur le rendu |
| --- | --- | --- |
| A — clarté | teinte de l'institution ; candidats pleins, groupe ou gouvernement clairs, superposés en `multiply` | le recouvrement ne sort que de 1,4:1 des candidats seuls |
| B — forme | bande claire pour les fiches de groupe ou de gouvernement, filet foncé pour les candidats | la frise change de dessin, et les listes portées par les seuls candidats deviennent des filets |

## Décision

**Une seule entrée de légende, « Données collectées », dans la teinte de
l'institution.** La frise dit ce que le dépôt porte et depuis quand ; la fiche
d'origine n'y est plus un encodage. La teinte double la hiérarchie au lieu de
dire autre chose qu'elle : ce n'est pas une information de plus, c'est le code
de la fiche candidat, appris une fois et retrouvé ici. Chaque institution vit
dans son bloc : deux teintes ne se touchent jamais dans un même rail.

Le champ `pop` reste dans `couverture.json` : le survol d'un segment nomme la
fiche d'où il vient, et c'est tout ce qu'il sert.

## Alternative écartée

Les deux variantes ci-dessus, et le statu quo — un bleu qui se lit « Union
européenne » sur une page qui ne parle pas de l'Union.
