# Brand pack — source, livré le 15/09/2026

Les SVG tels que le brand pack les livre. **Ce dossier n'est pas servi** : Vite
ne publie que `public/`. Ce qui part en production vit dans
`public/brand/`, et en est dérivé.

## Pourquoi une dérivation, et pas une copie

Le pack pose chaque dessin sur une **toile fixe**, centré, avec une marge
généreuse — bon pour un export, faux pour un `<img>` dont la hauteur est
contrainte.

| Fichier source | Toile | Dessin réel | Part de la toile |
|---|---|---|---|
| `logotype-transparent-on-light.svg` | 1200 × 600 | 906 × 215 | 36 % de la hauteur |
| `favicon.svg` | 200 × 200 | ~125 × 100 | 50 % de la hauteur |

`Brand.css` rend le lockup à **58 px**. Copié tel quel, c'est 58 px de *toile* :
la légende « politique » tombe à 21 px, très en dessous du plancher de 50 px que
`DESIGN_SYSTEM.md` §1 pose — et rien à l'écran ne le signale, le logo paraît
seulement petit.

Les fichiers de `public/brand/` ont donc leur **`viewBox` resserrée sur la boîte
du dessin**, plus 2 % de respiration. Le dessin n'est pas retouché : seules les
coordonnées de la fenêtre changent. Le lockup passe ainsi au ratio **3,75**,
contre 3,77 pour le lockup précédent — l'en-tête se rend à 218 × 58 px, à un
pixel près ce qu'il faisait avant.

## Correspondance source → production

| `public/brand/` | Vient de |
|---|---|
| `empreinte-lockup-light.svg` | `logotype-transparent-on-light.svg`, viewBox resserrée |
| `empreinte-symbol-light.svg` | `favicon.svg`, viewBox resserrée |
| `empreinte-favicon-16-light.png` · `-32-` | `export/favicon-16.png` · `favicon-on-light-32.png` |
| `empreinte-app-icon-192-light.png` · `-512-` | `export/avatar-dark-1000.png`, redimensionné |
| `empreinte-avatar-400-light.png` | `export/avatar-transparent-1000.png`, redimensionné |
| `public/apple-touch-icon.png` | `export/apple-touch-icon-180.png` |
| `public/favicon.svg` | `favicon-on-light.svg` |

## L'image Open Graph

Le pack ne la couvrait pas : sa bannière LinkedIn fait 1128 × 191, un autre
cadre, pas un recadrage. Elle a été composée séparément le 15/09/2026, et sa
**source est ici** : `OG Image.dc.html`, 2,3 Ko, qui rend le cadre 1200 × 630
en HTML — fond `#17141f`, arcs du symbole en filigrane à 7 % d'opacité, le
mot-symbole sur deux lignes, tiret jaune `#dfff00` et l'adresse du site.

**C'est elle qu'on modifie**, jamais le PNG : le jour où la charte bouge, ou
si une seconde version est voulue, tout est paramétré là. Elle a besoin de
`support.js`, qui est à côté. `open-graph-1200x630.png` en est le rendu
d'origine ; `public/brand/empreinte-open-graph-1200x630-light.png` est le même,
aplati en RGB — l'alpha était entièrement opaque, et certains robots d'aperçu
gèrent mal le RGBA.

**Ce que l'image NE dit PAS, et qui doit donc être dit ailleurs** : elle porte
le nom et l'adresse, pas la promesse. C'est `og:description` qui porte « Des
faits sourcés, sans note ni classement… ». Retirer cette description viderait
la carte partagée de son sens.

## Ce que le pack ne couvre pas
- **Les variantes sombres** (`*-dark.svg`, `*-on-dark.svg`) ne sont pas
  déployées : `index.css` déclare `color-scheme: light` et l'interface n'a pas
  de mode nuit. Elles sont gardées ici pour le jour où.
- **Le lockup court** (« Empreinte » seul) n'a pas d'équivalent dans le pack.
  Il n'était référencé nulle part dans le code ; il a été retiré.

Chaque SVG porte un manifeste **C2PA** d'environ 8 Ko en métadonnée — l'essentiel
du poids du fichier. Il est conservé : c'est la traçabilité du dessin.
