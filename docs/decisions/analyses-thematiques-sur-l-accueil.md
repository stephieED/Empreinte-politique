<a id="analyses-thematiques-sur-l-accueil"></a>

# Les analyses thématiques sur l'accueil, et la vignette livrée avec chaque article (2026-10-15)

`2026-10-15`

> **En bref** — L'accueil ne montrait aucun article : on n'y arrivait que par la barre du site. Arbitré sur maquette le 15/10/2026, étape par étape : un **carrousel** au-dessus du pied de page, à la largeur des blocs de l'accueil, haut d'environ la moitié du bloc sombre, une analyse à la fois — la plus récente d'abord, la suivante toutes les six secondes, flèches et points, pause au survol et au clavier, aucune rotation pour qui a demandé moins d'animations. Chaque analyse montre une vignette, l'étiquette « Analyse thématique », sa date, son titre et sa description. **La vignette est livrée avec l'article** (`<même nom>.vignette.jpg`), choisie à la publication : `tests/test_rapports_publies.py` refuse un article sans elle. La liste vient de `public/rapports.json`, écrit par `scripts/index-rapports.mjs` depuis le dossier, comme l'index `/rapports`.

## Le contexte

Quatre articles publiés au 15/10/2026, et aucun chemin vers eux depuis
l'accueil. La propriétaire a demandé « un bandeau déroulant […] comme sur les
pages d'actu ».

## La décision, et ce qui a été écarté en route

| Étape | Retenu | Écarté |
| --- | --- | --- |
| Forme | une analyse à la fois, avec sa figure | le défilement continu des titres (« je n'aime pas le défilement continu ») ; le bandeau à un titre, sans image |
| Place | au-dessus du pied de page | sous la barre du site, entre le bloc sombre et l'exploration, tout en haut de la page |
| Largeur | celle des blocs de l'accueil | de bord à bord, « plus large que le reste » |
| Hauteur | environ la moitié du bloc sombre (163 px pour 297 à 1 300 px) | l'encadré à grande figure, « beaucoup trop gros » |
| Remplissage | la description de l'article sous son titre | une vignette agrandie ; les deux |

Une analyse absente de la liste n'affiche rien : un encart vide dirait qu'il
manque quelque chose là où il n'y a pas d'article (§2 règle 5).

## Les vignettes

Deux voies : une image livrée avec chaque article, ou une capture faite à la
construction du site. La seconde demandait un navigateur dans la construction
et ne sait pas choisir la figure la plus parlante. **La première est retenue** :
le choix reste humain, et le même fichier pourra servir d'aperçu de partage —
ce n'est pas fait ici, faute de demande.

Les quatre premières vignettes sont des captures d'une figure de chaque article,
choisies sur maquette : l'hémicycle du vote (violences sexuelles et sexistes,
budget 2026), la part de l'éducation à chaque séance de questions au
Gouvernement, la chronologie des carburants.
