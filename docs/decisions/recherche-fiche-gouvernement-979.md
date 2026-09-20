<a id="recherche-fiche-gouvernement-979"></a>

# La recherche arrive sur la fiche de gouvernement, sans rien charger de plus (#979) (2026-09-20)

`2026-09-20`

> **En bref** — Troisième et dernier temps 1 de #979. Sous un mot, « En bref »
> et « Qui le composait » se retirent, « Ce qu'on n'a pas pu lire » reste, et
> les deux sections d'intitulés — les débats, les textes déposés — se
> recalculent. La fiche porte déjà la liste entière des débats : rien ne se
> télécharge en plus, contrairement à la fiche de groupe.

## Contexte

La recherche existe sur la fiche candidat (#993) et sur la fiche de groupe
(#995), et la barre a depuis rejoint le tiroir de l'explorateur (#1025/#1026).
La fiche de gouvernement, livrée par #330, ne lisait pas `?mot=` : son tiroir ne
portait pas de champ, et le code le disait en toutes lettres.

## Décision

| Point | Retenu | Pourquoi |
| --- | --- | --- |
| Sections retirées | « En bref », « Qui le composait » | Ni chiffres ni personnes ne portent d'intitulé — même geste que « Qui sont-ils » sur la lignée |
| « Ce qu'on n'a pas pu lire » | Inchangée | Ses limites portent sur la collecte, jamais sur le mot |
| Les deux sections d'intitulés | Recalculées par `filtrerGouvernement` : débats par leur intitulé, textes par leur titre. La figure des matières et des sorts est dessinée à partir de la liste des textes, donc elle suit | Une figure de tout le mandat au-dessus d'une liste filtrée montrerait deux choses différentes |
| Les débats | **Filtrés sur la liste entière déjà téléchargée** (`paroles.tous`, 1 738 sur la fiche Borne) ; la section continue d'en afficher dix | La fiche porte `tags_thematiques_agreges` en entier : contrairement à la lignée, aucun fichier à ajouter |
| Le pied de la section des débats | Sous un mot, « N débats », sans « sur M » | M serait le nombre de débats qui portent le mot : « 34 sur 34 » n'apprend rien |
| Les effectifs de membres | Inchangés sous un mot | Ce ne sont pas des intitulés ; un numérateur filtré sur un dénominateur filtré ne dirait plus de quoi il est le ratio (§2 règle 7) |
| La liste des textes | Dépliée sous un mot ; un clic dans la figure la restreint encore | Les textes retenus se lisent sans chercher le bon brin |
| La barre | Celle du tiroir : `/gouvernements` rejoint `FICHES_FILTRABLES` | Une seule barre pour les trois fiches |

Mesuré le 20/09/2026 sur la fiche Borne : 1 738 débats et 111 textes ; « santé »
en retient 34 et 3, « agriculture » 7 et 4.

## Alternative écartée

- **Charger `<id>.paroles.json` pour chercher** (2,6 Mo sur Borne) : il porte le
  détail d'un sujet — qui, quand, où le vérifier —, pas ce que le filtre lit.
  Les intitulés sont déjà là.
