<a id="logo-en-traces"></a>

# Les lettres du logo sont des tracés, pas du texte (2026-10-21)

`2026-10-21`

> **En bref** — le lockup du site (`public/brand/empreinte-lockup-light.svg`) écrivait « Empreinte politique » en `<text>` Manrope. Servi par `<img>`, un SVG ne voit pas les polices de la page : le logo s'affichait dans la police installée chez le visiteur — **Arial presque partout**, donc hors charte — et, chez qui avait installé Manrope, dans un rendu système assez large pour **couper le « e » final** (constaté par la propriétaire sous Windows). Les lettres sont converties en tracés Manrope 4.504, crénage et espacement du pack compris ; la `viewBox` ne bouge pas. **Écartés** : élargir la `viewBox` (le logo serait resté en Arial) ; inclure le SVG en ligne dans la page pour qu'il voie la police chargée (il aurait dépendu du chargement de Google Fonts, et les articles statiques le servent aussi par `<img>`).

## Mesures

- Manrope 700 à 124 unités, `letter-spacing: -3` : le mot finit à 1 031,5 pour un cadre qui s'arrête à 1 050 — 18 unités de marge, environ 2 %.
- Tracés superposés au rendu Chromium avec la police chargée : 0,85 % des pixels diffèrent, tous en bordure d'anticrénelage.
- Boîte du dessin tracé : 905,2 × 214,3, contre 906 × 215 annoncés par `brand-source/README.md` : la `viewBox` resserrée reste juste.

## Garde-fou

`tests/test_logo_en_traces.py` refuse tout SVG de `public/` qui contient un `<text>`.
