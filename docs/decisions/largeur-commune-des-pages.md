<a id="largeur-commune-des-pages"></a>

# Une seule largeur pour toutes les pages du site (2026-10-21)

`2026-10-21`

> **En bref** — l'accueil, les pages du site, les trois fiches et les articles forment désormais **une même colonne de 1 600 px, centrée**. La largeur vit dans deux jetons de `src/index.css` : `--colonne` (la page) et `--mesure` (80 caractères, une ligne de texte courant). La barre du haut et le pied ont un fond d'un bord à l'autre, mais leur logo et leurs liens s'alignent sur la colonne. **Une page à venir hérite de la largeur sans rien écrire** : elle passe par un des trois cadres, et `tests/test_largeur_commune.py` refuse toute largeur de page écrite en dur. Arbitré sur maquette entre cinq formes : la forme E. **Écartées** : trois centrages des largeurs existantes (A, B, C), qui gardaient six mises en page, et une colonne de 1 368 px (D), qui resserrait l'accueil.

## Le contexte

Chaque page avait reçu sa largeur le jour où elle avait été faite. Mesuré le
21/10/2026 sur un écran de 2 560 px :

| Page | Largeur | Position |
| --- | --- | --- |
| Accueil | 1 600 px, barre du haut comprise | collé à gauche |
| À propos, Méthodologie, FAQ, Nous soutenir | 900 px | centré dans 1 600 px collés à gauche |
| Sources | 1 180 px | idem |
| Fiches candidat et groupe | sommaire 204 px + fiche 1 100 px | à gauche |
| Fiche de gouvernement | 1 100 px | centré |

La cause commune : `max-width: 1600px` sans centrage sur l'enveloppe de
l'accueil et des pages du site, et une largeur propre à chaque fiche.

## La décision

- **`--colonne: 1600px`**, lu par `.landing-main`, `.static-main`,
  `.explorer-corps`, `.pds` et `.entete-site`. Les fiches perdent leur
  plafond de 1 100 px et occupent la colonne à côté du sommaire.
- **`--mesure: 80ch`** borne les paragraphes et les listes des pages du site :
  au-delà, l'œil perd la ligne suivante. Les cartes et les figures prennent
  toute la colonne.
- **La barre du haut** garde un fond d'un bord à l'autre ; son logo et ses
  liens s'alignent sur la colonne (forme C de la maquette).
- **Les articles** (`public/rapports/`, hors de l'application) reçoivent la
  même valeur dans leur barre et leur pied, recopiée par
  `scripts/chrome-instantane.mjs`. Leur texte garde sa largeur de lecture.
- **Le garde-fou** (`tests/test_largeur_commune.py`) : aucune feuille de style
  ne fixe de `width` ni de `max-width` d'au moins 1 000 px ; les cadres lisent
  `--colonne` ; toute page routée par `App.jsx` passe par un cadre ; les
  articles portent la même valeur.

## Pourquoi pas toute la largeur de l'écran

Sur 2 560 px, une ligne de texte compterait plus de 300 caractères, et les
graphiques des fiches s'aplatiraient. Au-delà de 1 600 px, une colonne plus
large n'ajouterait que du vide autour du texte, borné de toute façon par
`--mesure`.

## Ce qui reste

- Le graphique des budgets de la fiche de gouvernement garde sa largeur
  propre et laisse un vide à côté : c'est une figure arbitrée, à redessiner
  sur maquette.
- Les cartes d'À propos s'élargissent, mais leur texte s'arrête à 80
  caractères : un vide à droite, à traiter sur maquette.

## Les alternatives écartées

| Forme | Pourquoi |
| --- | --- |
| A — centrer la page entière dans 1 600 px, largeurs inchangées | Six mises en page demeuraient |
| B — barre pleine largeur, contenu centré, largeurs inchangées | Idem, et le logo s'éloigne du contenu |
| C — barre alignée sur le contenu, largeurs inchangées | Idem ; son alignement de barre est repris dans E |
| D — colonne commune de 1 368 px | Resserrait l'accueil ; la propriétaire a demandé plus large |
