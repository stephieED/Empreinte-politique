# Empreinte lockup 2 lignes — cotes de reference

Police unique: Manrope (ligne 1: 800, ligne 2: 700).
Texte vectorise (outlines) dans le SVG et le PDF final.

Definition du bloc de texte (2 lignes):
- L1: 'Empreinte' 48 px, tracking -0.07em
- L2: 'POLITIQUE' 12 px, tracking +0.07em
- Delta de baseline L1->L2: 20.00 px
- Hauteur du bloc de texte (sommet capitales L1 -> baseline L2): 54.56 px

Alignement symbole (optique):
- Base de recalage demandee (bbox reel symbole): 26.4 px de hauteur
- Cible appliquee: ~51 px (soit ~90% d'un bloc texte de ~57 px)
- Facteur d'echelle applique globalement: 51 / 26.4 = 1.9318
- Ratio obtenu sur la reference 2 lignes: 51 / 57 = 0.895 (~0.90)
- Hauteur symbole corrigee (reference 2 lignes): 51.00 px
- Position Y symbole corrigee (origine lockup): 5.06 px

Regles d'espacement reproductibles (basees sur le symbole reel):
- Horizontal (texte a droite): espacement = 0.38 x hauteur reelle du symbole
- Empile / vertical (texte dessous): espacement = 0.30 x hauteur reelle du symbole
- Centrage horizontal: centre vertical du symbole aligne sur le centre vertical du bloc texte
- Centrage empile: bloc texte recentre sous le symbole sur l'axe X

Mesures constatees sur la reference 2 lignes:
- Hauteur symbole reelle: 51.00 px
- Espacement horizontal derive: 0.38 x 51.00 = 19.38 px (cible visuelle)

Cadre final de reference (horizontal, mode jour):
- Fichier: `empreinte-lockup-horizontal-empreinte-politique-light.svg`
- ViewBox final: `13.52 -0.73 329.27 87.26`
- Width/height finals: `329.27 x 87.26`
- Marge de protection reelle autour du contenu visible: 16 px sur chaque bord (gauche/haut/droite/bas)

Note petite taille:
- Rendus de verification: `empreinte-lockup-2lignes-mobile-220.png` et `empreinte-lockup-2lignes-mobile-180.png`.
- Favicon: lockup non recommande; utiliser le symbole seul (deja fourni).
