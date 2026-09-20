# Le contrôle de perte nomme ce qui a disparu (#823)

`2026-09-10`

> **En bref** — `audit_diff_profils` relève chaque liste par un **entier** : une entrée remplacée par une autre garde le même compte, et l'échange est **invisible** ; le run `34454305520` l'a payé — `tags_thematiques` montait de 43 811 à 53 581 sur les 953 profils, **aucune perte**, pendant que `REN-16` et `EPR-17` perdaient chacun **une** étiquette d'union et bloquaient le commit, or une union ne perd un élément que si aucun membre ne le porte plus : l'échange naissait à l'étage profil, où rien ne le voyait, et ne se manifestait qu'à l'étage groupe, **où il ne naissait pas** ; le run n'ayant rien committé, sa sortie n'existait plus et l'étiquette **n'a jamais pu être nommée**. Une collection déclare désormais `listes_nommees` — `tags_thematiques` et `tags_thematiques_agreges`, **trois champs** — dont le relevé garde les valeurs : les entrées disparues sont nommées, y compris à compte égal et **même quand le compte monte**, le cas le plus trompeur. Coût mesuré et non supposé : **5 911 valeurs distinctes** pour 53 183 entrées sur les 1 035 profils publiés, 2,6 Mio qui ne quittent jamais la mémoire — le même traitement sur `amendements` coûterait des millions de clés, d'où le choix de déclarer plutôt que de généraliser. **Non bloquant, délibérément** : `tags_thematiques` est un champ DÉRIVÉ recalculé à chaque run (§4), un échange y est le fonctionnement normal — #825 vient d'ailleurs de diviser par deux les agrégats des 21 fiches, volontairement ; ce lot n'ajoute pas un verrou, il ajoute une **explication**, la perte de compte restant bloquante. `_identites()` rend **`None` et non un ensemble vide** sur une liste non nommable, et aucun constat n'est produit si un seul des deux côtés l'est : ne pas savoir n'est pas un fait (§2 règle 5). **Non tranché** : sortir `tags_thematiques` des listes stables, que cette décision rend moins urgent sans le régler. Suite complète à 4 435, 0 échec.

## Contexte

`audit_diff_profils` relève chaque liste surveillée par un **entier** et compare
avant/après. Une liste dont une entrée est **remplacée** par une autre garde le
même compte : l'échange est invisible.

C'est un choix assumé, et il n'est pas remis en cause ici : comparer des
ensembles sur 953 profils dont certains portent des millions d'amendements
coûterait autant de clés que d'entrées. Ce que cette décision corrige, c'est
l'angle mort — pas la méthode.

## Ce que l'angle mort a coûté

Run `34454305520`, artifact `diff-profils` :

| Étage | Champ | Avant | Après | Verdict |
| --- | --- | ---: | ---: | --- |
| profils (953) | `tags_thematiques` | 43 811 | 53 581 | **aucune perte** |
| `groupe-AN-EPR-17` | `tags_thematiques_agreges` | 3 963 | **3 962** | perte bloquante |
| `groupe-AN-REN-16` | `tags_thematiques_agreges` | 4 318 | **4 317** | perte bloquante |

Sur ces deux fiches, rien d'autre n'avait bougé. Une union ne peut perdre un
élément que si aucun de ses membres ne le porte plus — or aucun profil n'avait
perdu en compte. L'échange était donc à l'étage profil, **invisible**, et ne se
voyait qu'à l'étage groupe, **où il ne naissait pas**.

Le run a échoué, et il a eu raison de bloquer une baisse qu'on ne savait pas
expliquer. Ce qui manquait, c'était de quoi l'expliquer **sans le rejouer** :
sa sortie n'existant plus, l'étiquette perdue n'a jamais pu être nommée.

## La décision

Une collection déclare `listes_nommees` : les listes dont le relevé garde les
**valeurs**, pas seulement leur nombre. Trois champs, et trois seulement :

| Collection | Champ nommé |
| --- | --- |
| `profiles` | `tags_thematiques` |
| `groupes` | `tags_thematiques_agreges` |
| `partis` | `tags_thematiques_agreges` |

Le contrôle rapporte alors les entrées disparues **en les nommant**, y compris
quand le compte n'a pas baissé — et même quand il a monté, le cas le plus
trompeur.

## Pourquoi ces trois champs, et pas les autres

`tags_thematiques` est un champ **dérivé** : recalculé à chaque run, jamais
fusionné (§4, avec `chambres`, `licence_donnees`, `meta.avertissements`). Une
recomputation qui remplace une étiquette par une autre est son fonctionnement
normal. Les listes fusionnées additivement sur une clé — `votes`, `mandats`,
`textes_portes`, `interventions` — ne peuvent pas échanger sans que la clé
change : l'angle mort est concentré sur le seul champ dérivé de la liste.

Le coût est mesuré, pas supposé : **5 911 valeurs distinctes** pour les 53 183
`tags_thematiques` des **1 035 profils publiés**, soit **2,6 Mio** de relevé qui
ne quitte jamais la mémoire — `comparer()` rend des constats, pas des relevés.
Le même traitement sur `amendements` coûterait des millions de clés, et c'est
pourquoi nommer n'est **pas** le comportement par défaut.

## Non bloquant, et c'est délibéré

Un échange sur un champ recalculé à chaque run n'est pas un incident. Bloquer
dessus ferait échouer des runs légitimes — et le corpus vient d'en donner
l'exemple : #825 a divisé par deux les `tags_thematiques_agreges` des 21 fiches
de groupe, volontairement.

Ce que ce constat apporte n'est pas un verrou de plus, c'est **une explication**.
La perte de compte, elle, reste bloquante comme avant ; simplement, le rapport
dit maintenant *quelle* entrée a disparu.

## Deux refus de conclure

`_identites()` rend `None` — et non un ensemble vide — quand une liste n'est pas
d'une forme nommable. Un ensemble vide dirait « cette liste ne porte rien », ce
qui ferait passer une lecture impossible pour un fait sur les données (§2
règle 5). Et si l'un des deux côtés n'est pas nommable, **aucun constat n'est
produit** : ne pas savoir n'est pas un fait.

Le rapport plafonne à 20 entrées nommées par fichier, le compte total disant
l'ampleur. Il est lu par quelqu'un qui cherche une cause, pas un inventaire.

## Les deux autres pistes de l'issue

- **Sortir `tags_thematiques` des listes stables** pour le ranger en
  `listes_signalees` : un champ recalculé n'est stable par aucune construction,
  et bloquer sur `-1` coûte un run entier. **Non tranché** — cette décision le
  rend moins urgent, puisqu'un blocage devient explicable en lisant le rapport,
  mais l'arbitrage reste ouvert.
- **Ne rien changer et documenter** : écarté. L'angle mort avait déjà coûté un
  run de deux heures.

Suite complète à 4 435, 0 échec.
