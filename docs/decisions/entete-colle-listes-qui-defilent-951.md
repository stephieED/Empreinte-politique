<a id="entete-colle-listes-qui-defilent-951"></a>

# La rangée du logo reste collée, les listes défilent, et la page ne se recompose plus au défilement (#951) (2026-09-16)

`2026-09-16`

> **En bref** — l'en-tête de l'explorateur posé par #324 **retirait les trois listes de la page** au-delà de 180 px de défilement ; la page raccourcissait de **385 px**, le navigateur ramenait le défilement **à 0**, les listes revenaient et la boucle reprenait — mesuré sur la fiche de Jérôme Guedj, défilement par pas de 40 px : à 200 px les listes partent, **22 ms plus tard le défilement est à 0**. La propriétaire l'a signalé : « l'affichage revient en haut puis reste instable ». Retenu sur maquette jouable, après cinq formes figées et deux mécaniques : **la rangée du logo reste collée** (80 px) et porte la barre des pages du site — *Explorateur · Méthodologie · Sources · FAQ*, dans le style discret de la forme B (gris, la page courante soulignée de jaune) — et « Changer de fiche » ; **les listes défilent avec la page**, et franchir leur bas ne change qu'une **visibilité**, celle du bouton, dont la place est réservée. **Sous 720 px les listes quittent la page** : elles y faisaient 1 277 px sur un 390 px de large, deux écrans avant la fiche ; le bandeau seul reste, et la fiche commence à ~200 px au lieu de 1 422. **La position se lit au défilement**, pas par un `IntersectionObserver`, qui ne signale qu'un franchissement : un saut direct passait les listes sans les croiser, et le bouton restait caché — trouvé sur maquette. Le bouton garde **sa largeur** quel que soit son libellé : ses liens voisins glissaient à chaque clic. **Alternative écartée** : la barre réduite en surimpression, qui rendait 24 px de plus à la fiche mais ajoutait un second en-tête. La rangée est **un composant, `EnTeteSite`**, que l'accueil porte aussi, comme la maquette de la forme C l'avait posé. Le symbole mobile portait les traits blancs de la variante pour fond sombre : il ne montrait que le point jaune.

## Le contexte

`ExplorerLayout.jsx` rendait la marque et les trois listes dans la page, puis,
au-delà de `SEUIL_REPLI = 180` px, les **masquait** (`hidden`) et montrait une
barre compacte de 56 px. Masquer 357 px de contenu **déplace tout ce qui suit**
vers le haut. Le seuil étant plus bas que la hauteur retirée, la page se
retrouvait sous le seuil au moment même où elle le franchissait.

Mesuré le 16/09/2026, serveur local sur `origin/main`, Firefox, 1 440 × 900 :

| Instant | Défilement | Hauteur de page | État |
| ---: | ---: | ---: | --- |
| 314 ms | 200 px | 7 525 px | le seuil est franchi |
| 336 ms | **0 px** | 7 140 px | listes masquées, barre compacte |
| 883 ms | 0 px | 7 525 px | listes revenues |
| 1 197 ms | 200 px | 7 525 px | la boucle reprend |

Le même lot devait poser la barre des pages du site sur les fiches (#951).

## La décision

### 1. Une rangée collée, de hauteur fixe

`.entete-site` (`EnTeteSite.jsx`) est collée en haut et **ne change jamais de hauteur** : 80 px,
56 px sous 480 px où le logo n'est plus que le symbole. Elle porte `Brand`,
`NavigationSite` et le bouton « Changer de fiche ».

Le bouton est en `visibility: hidden` tant que le bas des listes est sous la
rangée, et passe visible ensuite. **Rien ne sort du flux** : c'est ce qui rend
la boucle impossible, et un test le tient (`test_la_mise_en_page_ne_change_pas_au_defilement`).

Les deux libellés, « Changer de fiche » et « Masquer les listes », occupent la
même case de grille : la largeur est celle du plus long.

### 2. Les listes redemandées s'ouvrent en panneau

Le panneau est `position: fixed` sous la rangée, opaque, et ne prend aucune place
dans la page. Il se referme au changement de fiche, à Échap, et quand on remonte
jusqu'aux listes de la page — sinon elles seraient deux fois à l'écran.

### 3. Sous 720 px, le bandeau seul

Les liens passent dans un menu, les listes quittent la page, le bouton est là
dès l'arrivée. Mesuré sur la fiche de Jérôme Guedj à 390 px : le contenu de la
fiche commençait à 1 422 px, il commence à 201 px.

### 4. La position se lit à chaque défilement

`getBoundingClientRect()` d'un repère posé sous les listes, lu une fois par
image. Un `IntersectionObserver` ne signale qu'un **franchissement** : sur la
maquette, un saut direct à 2 600 px laissait le repère passer d'en dessous à
au-dessus de l'écran sans l'avoir croisé, et le bouton restait caché.

### 5. La même rangée sur l'accueil

`EnTeteSite` porte le logo et les pages du site ; l'explorateur y ajoute « Changer
de fiche » et son panneau. L'accueil la porte seule, sans page courante marquée,
comme la maquette de l'accueil l'avait posée (forme C, arbitrée le 16/09/2026).
Une seule rangée, pour qu'elle ne diverge pas d'une page à l'autre. La
méthodologie, les mentions légales et la couverture la recevront avec la suite
de #951.

### 6. Deux cibles provisoires

« Sources » mène à `/couverture`, « FAQ » à `/#faq` sur l'accueil, tant que #951
n'a pas créé `/sources` et `/faq`.

### 7. Le symbole pour fond clair

`public/brand/empreinte-symbol-light.svg` portait `stroke="#f7f6f4"`, les traits
de la variante pour fond sombre : sur le fond clair, seul le point jaune restait
visible. Il prend `#17141f`, la valeur de `favicon-on-light.svg` dans le kit de
marque du 15/09/2026 et du lockup déjà en place.

### Ce que #324 garde

Le sommaire de sections, son seuil de 1 440 px, l'ordre candidats · groupes ·
gouvernements, l'opacité de ce qui est collé. Le sommaire se cale sur la nouvelle
hauteur : `top` 76 → 100 px, `SEUIL_LECTURE` 120 → 144, `AVANCE_ANCRE` 90 → 114.

## Alternatives écartées

| Forme | Pourquoi |
| --- | --- |
| Barre réduite en surimpression, listes en place | Même stabilité, 24 px de plus rendus à la fiche une fois défilée, mais deux en-têtes différents selon la position. Maquettée jouable, non retenue |
| Garder l'en-tête de #324 avec un espaceur de même hauteur | Masque le symptôme ; la hauteur des listes dépend de la largeur et du filtre de groupe, l'espaceur l'aurait tôt ou tard ratée |
| Liens en bande au-dessus du logo | +48 px avant la fiche, pour le même contenu |
| Un seul bouton Menu à toutes les largeurs | Un clic de plus partout, et la page courante invisible |
