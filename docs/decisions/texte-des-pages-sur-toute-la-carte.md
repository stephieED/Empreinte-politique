<a id="texte-des-pages-sur-toute-la-carte"></a>

# Le texte des pages de texte occupe toute sa carte, comme sur l'accueil et les fiches (2026-10-22)

`2026-10-22`

> **En bref** — Les paragraphes des pages de texte (`/methodologie`, `/a-propos`, `/sources`, `/faq`, `/mentions-legales`) ne s'arrêtent plus à 80 caractères (`--mesure`, posé le 21/10 par `largeur-commune-des-pages`). Ils prennent la largeur de leur carte, pour que ces pages aient la même largeur de contenu que l'accueil et les fiches. Le jeton `--mesure` est retiré, ainsi que les bornes de 72 et 78 caractères de l'introduction et de `/sources`. **Écarté** : borner aussi le tableau de filiation à 80 caractères, qui gardait la règle du 21/10.

## Le contexte

En relisant `/methodologie` après #1333, la propriétaire a relevé la marge
droite entre le texte et le bord de la carte. La carte prend toute la colonne
(1 600 px au plus), le texte s'arrêtait à `--mesure` (80 caractères) : sur un
écran large, le reste de la carte était vide. Le tableau de filiation de #1333,
qui n'était pas borné, allait jusqu'au bord et rendait l'écart visible.

## La décision

Arbitrée le 22/10/2026 : « on élargit pour être consistant avec la largeur du
contenu dans la page d'accueil et sur les fiches ».

- `.static-main :is(p, li)` ne porte plus de `max-width`, et `--mesure`
  disparaît de `src/index.css`, faute d'autre lecteur.
- `.static-intro` (72 caractères) et `.cv-sous`, `.cv-note` de `/sources`
  (78 caractères) perdent aussi leur borne : sans cela, ces pages gardaient deux
  largeurs de texte.
- `--colonne` reste la seule largeur de page, et la règle du 21/10 qui interdit à
  une page de fixer la sienne ne change pas.

Mesuré le 22/10/2026 sur le dernier paragraphe de la section `lignee` de
`/methodologie`, en local : 841 px de large dans une fenêtre de 1 280 px, 933 px
à 1 600 px et 948 px à 2 560 px, soit environ 110 caractères par ligne. La carte
garde son titre en marge (forme E des pages de texte), ce qui plafonne la ligne
bien avant la colonne.

## Alternatives écartées

| Option | Pourquoi écartée |
| --- | --- |
| Borner le tableau de filiation à 80 caractères | gardait la règle du 21/10 et un seul bord droit dans la carte, mais laissait le vide à droite que la propriétaire relevait |
| Rétrécir les cartes à 80 caractères | rouvrait la largeur commune de toutes les pages de texte, et les séparait de l'accueil et des fiches |

Garde : `tests/test_largeur_commune.py::test_le_texte_des_pages_de_texte_occupe_sa_carte`.
