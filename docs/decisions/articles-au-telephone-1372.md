<a id="articles-au-telephone-1372"></a>

# Les articles au téléphone : mise en page redessinée, textes gelés (#1372, 2026-10-29)

`2026-10-29`

> **En bref** — Les quatre articles de `/rapports` sont redessinés pour le téléphone (sous 720 px) : plus rien ne défile de côté, aucun texte sous 13 px, figures redessinées à la largeur selon les principes arbitrés sur les fiches. Autorisation **ponctuelle** de la propriétaire, à une condition : aucun texte, aucun nombre ne change — tenue par `tests/test_instantanes_textes_geles_1372.py`. Une exception accordée : les 34 intitulés des articles du PLF 2026 dans « Votes par article » (budget). Le pied commun des pages statiques prend la forme A′ et ne déborde plus.

## Le problème

Mesuré le 29/10/2026 à 390 px : les quatre articles faisaient 430 px de large (le pied `.pds` déclarait `width:100%` et une marge intérieure sans `box-sizing:border-box` ; à l'ordinateur, 1 360 px pour 1 280) ; onze figures et un tableau défilaient de côté dans leur cadre (budget 2, éducation 3, violences 6) ; des textes descendaient à 5 px dans les SVG réduits.

## La règle, et l'exception

« Un instantané n'est jamais mis à jour » vaut pour ses faits
(`chrome-du-site-sur-les-instantanes-1029`). Le 29/10/2026, la propriétaire
a autorisé **ponctuellement** à redessiner les articles (« je t'autorise
ponctuellement à redesigner les articles »), à condition que leurs textes et
leurs nombres restent identiques. Ce n'est pas une levée générale de la règle.

Elle a accordé une seconde exception le même jour : au téléphone, chaque ligne
de « Votes par article, député par député » (budget 2026) porte l'intitulé de
l'article, tiré du texte du projet de loi (`articles_votes.json`, clé `textes`,
#1352), avec « Article 8 · 13/11 » en petit dessous. 35 lignes, 34 intitulés
distincts.

`tests/test_instantanes_textes_geles_1372.py` fige l'ensemble des chaînes de
texte de chaque article (chrome, `<head>`, styles et scripts exclus) par une
empreinte. Mesuré à l'écriture : aucune chaîne perdue sur les quatre, aucune
nouvelle sauf les 34 intitulés.

## Ce qui est fait

Tout sous `@media (max-width: 720px)` ; à 1 280 px, le contenu de chaque page est identique au pixel (comparaison faite par article sur des copies d'essai) — seul le pied cesse de déborder.

| Article | Ce qui change au téléphone | Maquette (privée) |
| --- | --- | --- |
| Prix des carburants (23/09) | Tableau « Qui en a parlé » en forme B (l'en-tête de la 2ᵉ colonne, trop long, gardé une fois en haut) ; textes à 13 px ; marge des citations retirée | https://claude.ai/artifact/PCwNaEVSSuNUWnTY5kWqYf |
| Budget 2026 (04/10) | Hémicycle au cadre resserré (D1) ; tableau des groupes en forme B ; « Votes par article » en une ligne par scrutin (intitulé, numéro et date, résultat, bande des 566 députés) ; tableau « Avant et après le 21 novembre » laissé en colonnes | idem |
| Éducation (09/10) | Barres des séances de questions redessinées ; hémicycle D1 ; « Panorama des textes déposés » en douze bandes, une par groupe dans l'ordre de l'hémicycle ; frise des textes verticale | idem |
| Violences sexuelles et sexistes (13/10) | Quatre hémicycles et éventails D1 (effectifs des éventails passés dans la liste numérotée) ; grille des 54 votes transposée ; « Douze mois » en temps descendant | idem |
| Pied commun (`scripts/chrome-instantane.mjs`) | `box-sizing:border-box` (toutes largeurs) ; au téléphone, forme A′ comme `PiedDeSite` : titres retirés, liens à la suite, enveloppe « Écrire à Empreinte politique », trois pictogrammes à droite | `Lk9ZutgQaKuG7GQyKLZD8d` |

Une figure de bureau trop large est doublée d'une version réservée au
téléphone (masquée au-delà de 720 px, l'originale masquée en deçà), qui porte les mêmes textes ; les
points des hémicycles et la matrice des votes sont repris par `<use>`, pas
recopiés.

Mesuré le 29/10/2026 dans Chromium : à 360 et 390 px, document à la largeur de l'écran, aucun élément qui défile, plus petit texte 13 px, sur les quatre articles ; à 1 280 px, document de 1 280 px.

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone.
- À 320 px, des textes SVG redescendent sous 13 px (éducation : 11,2 px).
- L'éventail des amendements en séance (violences) reste chargé : sept nombres sur douze ont un trait de rappel.
