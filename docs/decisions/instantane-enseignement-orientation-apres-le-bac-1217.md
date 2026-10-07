<a id="instantane-enseignement-orientation-apres-le-bac-1217"></a>

# L'instantané sur les conditions d'enseignement retient l'orientation après le bac et Parcoursup (#1217) (2026-10-07)

`2026-10-07`

> **En bref** — L'article « Les conditions d'enseignement, de l'école au lycée » (#1217) écartait tout titre portant « supérieur », « post-bac » ou « université ». La propriétaire a objecté le 07/10/2026 que Parcoursup concerne les lycéens qui passent le bac. Trois cas ont été mesurés et montrés sur maquette ; elle a retenu le troisième : **le mot « Parcoursup » et le débat sur l'orientation après le bac entrent dans le périmètre**, par exception à l'exclusion de l'enseignement supérieur. L'article passe de 44 à 45 intitulés, de 418 à 457 prises de parole, de 100 à 108 députés intervenus et de 15 à 16 textes. Ce fichier **complète** `docs/decisions/instantane-compte-des-personnes-1217.md`, dont les autres règles ne bougent pas.

## Le contexte

`docs/decisions/instantane-compte-des-personnes-1217.md` arrête un périmètre
étroit, les moyens de l'école, et en sort l'enseignement supérieur. La liste
d'exclusion du relevé porte donc « supérieur », « post-bac » et « université ».

Mesuré le 07/10/2026 sur `main` 3c43be5c1, dans tout `pivot_data/`, sur les
1 402 profils (1 166 membres de groupe, 202 membres de gouvernement, 34
candidats déclarés) :

| Où figure « Parcoursup » | Depuis 2017 | Du 04/10/2025 au 04/10/2026 |
| --- | --- | --- |
| Prises de parole dont l'intitulé du débat porte le mot | 783 | 0 |
| Prises de parole dont seul le propos publié le cite | 112 | 23, dont 12 le 10/02/2026 |
| Textes déposés dont le titre le porte | 8 | 1 |
| Actes au Journal officiel dont le titre le porte | 26 | 2 |

Sur la période de l'article, aucun intitulé de débat ne porte le mot : l'ajouter
à la liste ne ramenait qu'un texte. Ce qui parle de Parcoursup sur ces douze
mois est un débat du 10/02/2026, « Limites actuelles et perspectives
d'améliorations du système d'orientation post-bac », écarté par « post-bac ».

## La décision

Trois cas mesurés sur les données du 04/10/2026 (`main` 446cf1b65, celles de
l'article), et montrés page par page sur une maquette du carrousel :

| Mesure | A, l'article d'origine | B, le mot « Parcoursup » | C, le mot et le débat sur l'orientation après le bac |
| --- | --- | --- | --- |
| Intitulés de débat | 44 | 44 | 45 |
| Prises de parole, hors présidence de séance | 418 | 418 | 457 |
| Députés intervenus, sur 567 membres des onze groupes | 100 | 100 | 108 |
| Textes déposés | 15 | 16 | 16 |
| Actes du ministère de l'éducation nationale | 6 | 6 | 6 |

- **C est retenu** (« on part sur C », 07/10/2026). Un titre qui porte
  « parcoursup » ou « orientation post-bac » est retenu **même s'il porte un mot
  de la liste d'exclusion**. Le reste de l'enseignement supérieur reste dehors.
- **Le débat entre sous « Autres intitulés »**, en gris dans l'histogramme : les
  trois couleurs arbitrées (fermetures de classes, postes, bâtiments et chaleur)
  ne changent pas, alors que ce débat compte 39 prises de parole contre 35 pour
  les bâtiments.
- **L'article et le carrousel disent l'exception** là où ils disaient
  l'exclusion : le chapeau, « Ce que cet article ne dit pas », et la page des
  sources du carrousel.
- **La chronologie sous l'histogramme n'emprunte plus ses couleurs** : le prune
  y désignait un texte déposé et, au-dessus, les fermetures de classes. Texte
  déposé et acte du ministère sont au trait noir, vides ; le vert du texte
  adopté reste.

Deux effets mécaniques, non arbitrés un à un : un député passe des fermetures de
classes aux autres sujets dans l'hémicycle (40 → 39), parce qu'il est rangé sous
le sujet où il a le plus pris la parole ; et dans « Ce que le gouvernement a
dit », Philippe Baptiste devient l'un des quatre membres du gouvernement les
plus présents, à la place de Mathieu Lefèvre.

## L'alternative écartée

- **A, ne rien changer.** Recommandé par l'agent : l'orientation n'est pas un
  moyen de l'école, et l'essentiel de la matière sur Parcoursup date de 2018,
  2021 et 2023. Écarté par la propriétaire : la plateforme est utilisée par les
  lycéens.
- **B, le mot seul.** N'ajoute qu'un texte, et demande déjà la même exception à
  l'exclusion de l'enseignement supérieur.

## Ce qui n'a pas été vérifié

- Les deux arrêtés de 2026 dont le titre porte « Parcoursup » n'entrent pas :
  l'article ne garde que les actes du ministère de l'éducation nationale. Leur
  ministère n'a pas été lu.
- Le compte par le propos est un minimum : 78 des 112 prises de parole qui
  citent le mot sans que leur intitulé le porte sont publiées tronquées.
