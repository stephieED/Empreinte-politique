<a id="titres-de-section-b5"></a>

# Titres de section B5 et rangée collée à l'ordinateur (#1372, 2026-10-29)

`2026-10-29`

> **En bref** — À l'ordinateur, la rangée des sections du téléphone vient se coller sous la barre du site et remplace le sommaire de gauche sur les quatre fiches, qui prennent toute la colonne commune. Le titre de section perd la bande J3 (ellipses et point jaune) et prend un trait encre court et épais au-dessus (forme B5). Arbitré sur maquette par la propriétaire ; la pastille comme titre est écartée parce qu'elle « ressemble à un bouton ou un filtre ».

## Le problème

La propriétaire préférait les titres de section du téléphone (#1372) à ceux de l'ordinateur. Mesuré le 29/10/2026 sur la fiche de Jean-Luc Mélenchon à 1 280 px : au milieu d'une section longue, aucun titre n'est à l'écran, et la fiche n'offre aucun moyen d'aller à une autre section. Le sommaire de gauche ne s'affiche qu'au-delà de 1 440 px.

## Ce qui a été arbitré, dans l'ordre

Maquette : https://claude.ai/artifact/BgjHSdoGFxjrMey2JCakd3

| Question | Retenu | Écarté, et pourquoi |
| --- | --- | --- |
| Que reprendre du téléphone ? | **B** : la rangée collée, titres gardés dans la page | A (la pastille seule comme titre) n'oriente pas ; C (titres effacés, comme au téléphone) perd la frontière entre sections, qui s'empilent à l'ordinateur |
| Quel titre dans la page ? | **B5** : trait encre de 64 × 6 px au-dessus d'un titre de 26 px | pastille encre ou claire : « ça ressemble à un bouton ou un filtre » ; bande encre pleine largeur : le fond encre marque déjà ce qui est choisi (onglet courant, période active) ; titre simple sous un filet : frontière discrète ; bande J3 : la propriétaire « n'aime pas le style de section sur ordi » |
| Le sommaire de gauche ? | retiré des quatre fiches ; gardé sur les pages de texte | deux navigations sur un même écran |

La largeur suit d'elle-même. Mesuré à 1 680 px : les cartes de la fiche commençaient à 348 px (sommaire de 268 px compris), elles commencent à 80 px comme sur l'accueil. Sous 1 440 px, rien ne change (40 → 1 240 à 1 280 px).

## Ce qui est fait

- `RangeeSections.jsx` lit les sections de la page (`data-section`, ancres stables), les observe, suit le défilement et fait défiler au clic. Les entrées sont des liens vers les ancres. Les pastilles sont celles du téléphone (`.glisse-onglet`). La rangée s'aligne sur la gouttière lue sur la fiche. Elle ne rend rien sous 721 px : le téléphone garde la sienne.
- Les trois feuilles de titres (candidat, groupe, gouvernement — la législature reprend la dernière) portent le trait B5. Le numéro de section n'est plus affiché. Les jetons `--j3-filigrane` et `--j3-bande` sont retirés.
- Le jaune reste à l'onglet courant (DESIGN_SYSTEM §2 : il marque ce qui est choisi).
- `tests/test_titres_de_section_b5.py` tient la rangée, l'absence de J3, le trait et le numéro masqué. `test_cadre_fiche_324.py` tient la fiche sans sommaire.

Vérifié dans Chromium à 1 680, 1 280, 1 024 et 390 px sur les quatre fiches : rangée présente au-delà de 720 px, absente en dessous, aucune page plus large que l'écran ; pastilles et titres au même bord gauche (80 px à 1 680, 40 px à 1 280). La rangée défile de côté à 1 024 px sur trois fiches. Un clic amène le titre 20 px sous la rangée.

## Ce qui n'est pas vérifié

- Au clavier et au lecteur d'écran, au-delà du `nav` nommé et de `aria-current`.
- Sur Safari et Firefox.
