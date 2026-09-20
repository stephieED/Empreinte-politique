<a id="un-seul-tiroir-pour-choisir-et-chercher-1025"></a>

# Un seul tiroir pour choisir sa fiche et chercher dedans, à la place de l'onglet « Explorateur » (#1025) (2026-09-18)

`2026-09-18`

> **En bref** — trois gestes se chevauchaient dans le bandeau. Les trois listes vivaient **à deux endroits** : dépliées sous la rangée à l'arrivée — **425 px**, et la fiche ne commençait qu'à **577 px** du haut de la page — puis rappelées dans un bouton « Changer de fiche » qui n'apparaissait qu'une fois ces listes passées au défilement. « Rechercher sur cette page » (#979) était, elle, dans le corps de la fiche. Retenu sur maquette jouée dans l'application, quatre formes capturées sur données réelles : **un seul tiroir**, qui porte la recherche en tête puis les trois listes, et dont le bouton **prend la place de l'onglet « Explorateur »** là où cet onglet est la page courante. Cet onglet n'était pas seulement inutile sur une fiche : son clic renvoyait à `/candidats`, **donc à la fiche par défaut, celle de Jean-Luc Mélenchon** — il déplaçait le lecteur vers une fiche que personne n'avait demandée. Il reste un lien partout où il sert (accueil, méthodologie, sources, FAQ). **Le champ n'existe que là où il filtre** : les fiches candidat et de lignée lisent `?mot=`, la fiche de gouvernement pas encore, les pages éditoriales pas du tout — le tiroir s'y renomme « Changer de fiche ». **Plus rien ne lit le défilement** : les listes ayant quitté la page, il n'y a plus de franchissement à mesurer, et l'écouteur de #951 disparaît avec son repère. **Formes écartées** : A, l'onglet devenu bouton, seule à déborder la rangée mobile (379 px sur 390, et elle déborde à 360) et dont le champ ouvert couvrait la marque ; B, le champ visible en permanence, qui mesure 230 px et se replie en loupe sous 720 px — son seul avantage ne valait donc que sur grand écran ; C, le même tiroir mais l'onglet conservé, écartée par la propriétaire : « dans ce cas, le bouton explorateur ne sert plus à rien ». Un seul bouton est rendu, pas un par mise en page.

## Le contexte

Mesuré le 18/09/2026 sur `origin/main` (`b0801efe0`), fiche d'Édouard Philippe,
Firefox, serveur local :

| Geste | Où il vivait | Coût |
| --- | --- | ---: |
| Choisir sa fiche | `.explorer-bars`, dépliées dans la page | 425 px, fiche à 577 px du haut |
| Choisir sa fiche, encore | bouton « Changer de fiche » du bandeau, visible après les listes | les mêmes trois listes |
| Chercher dans la page | `BarreFiltre` dans le corps de la fiche (#979) | hors du bandeau |

Trois demandes de la propriétaire, le 18/09/2026 : que le choix de fiche ne
vive plus qu'en haut ; que « Changer de fiche » rejoigne « Explorateur », ou
fusionne avec lui ; que « Rechercher sur cette page » monte dans le bandeau.

Deux contraintes tenaient d'avance. La rangée est à **hauteur fixe** depuis
#968, et c'est ce qui rend le défilement stable : rien ne doit la faire
grandir. Et sur mobile elle ne portait que deux boutons — « Menu » et
« Changer de fiche » — arbitré le 16/09 : trois gestes devaient tenir dans la
même largeur.

## La décision

### 1. Un tiroir, deux gestes, un seul endroit

Le tiroir (`.explorer-tiroir`) s'ouvre sous la rangée, par-dessus la fiche, et
ne prend aucune place dans la page. Il porte, dans cet ordre :

1. **« Sur cette page »** — le champ `BarreFiltre`, inchangé (#979) ;
2. **« Changer de fiche »** — les trois listes, dans l'ordre candidats,
   groupes, gouvernements.

On cherche dans la page où l'on est avant d'en changer : c'est l'ordre de
lecture, et il donne au tiroir son libellé, « Chercher ou changer de fiche ».

`.explorer-bars` est supprimé. La fiche commence donc là où la rangée finit.

### 2. Le bouton prend la place de l'onglet, il ne s'y ajoute pas

`NavigationSite` accepte un `outilExplorateur` et le rend **à la place** du lien
« Explorateur » quand cette page est la page courante ; replié dans « Menu »,
l'entrée disparaît, le bouton étant à côté du menu, pas dedans. La barre garde
quatre entrées, jamais cinq.

Ce que l'onglet faisait avant, sur une fiche : `/candidats` →
`DEFAULT_CANDIDATE_ID` → la fiche de Jean-Luc Mélenchon. Un onglet souligné
comme « vous êtes ici » qui, cliqué, emmène ailleurs.

### 3. Un seul bouton rendu, deux mises en page

Sous 720 px, les liens passent dans « Menu » (`.nav-site-lien { display: none }`)
et la barre ne porte plus que le bouton, placé **à droite** de « Menu » par
`order`. C'est un seul élément dans le DOM : deux boutons pour un même geste
étaient précisément le défaut à corriger. Son libellé long ne tient pas sur un
mobile — 226 px mesurés sur 390 — et se réduit à « Fiches ».

Mesures de la rangée mobile, dernier objet à droite :

| Forme | 390 px | 360 px |
| --- | ---: | ---: |
| Avant #1025 | 374 px | 344 px |
| A — onglet devenu bouton | 379 px | **379 px, déborde** |
| B — champ permanent | 374 px | 344 px |
| **C′ — retenue** | **374 px** | **344 px** |

### 4. Le champ n'existe que là où il filtre

`FICHES_FILTRABLES = ['/candidats', '/groupes']`. La fiche de gouvernement ne
lit pas `?mot=` — son filtre viendra avec le lot de la session gouvernement —
et les pages éditoriales n'ont pas de filtre. Le tiroir s'y renomme « Changer
de fiche » et ne porte pas de champ : une barre qui ne filtre rien est du
mobilier, et faire semblant contreviendrait à §2 règle 5.

### 5. Ce qui n'a pas bougé : la mécanique du filtre

Le mot vit dans l'adresse (`?mot=carburant`) et c'est **la page** qui le lit,
sur un `useDeferredValue`, avant de reconstruire la vue. Monter le champ dans le
bandeau ne déplace donc qu'un champ. Ce qui change : les deux pages de fiche
n'**écrivent** plus le mot, le tiroir est seul à le faire.

### 6. Plus aucune lecture du défilement

`listesPassees`, l'écouteur `scroll`, le repère et la visibilité conditionnelle
du bouton disparaissent. #951 avait déjà montré qu'un `IntersectionObserver` ne
convenait pas — il ne signale qu'un franchissement, et un saut direct (une
ancre, un lien partagé) passe les listes sans les croiser. Le remplacement est
plus simple que les deux : il n'y a plus rien à franchir.

## Les alternatives écartées

| Forme | Ce qu'elle faisait | Pourquoi écartée |
| --- | --- | --- |
| **A** | L'onglet « Explorateur ▾ » devenait le bouton ; la recherche était une pilule qui ouvrait un champ sur toute la rangée | Seule forme à déborder la rangée mobile (379 px sur 390 ; déborde à 360) ; le champ ouvert couvrait la marque ; un onglet qui garde l'apparence d'un lien sans en être un |
| **B** | « Changer de fiche » collé à l'onglet, champ visible en permanence | Le champ mesure 230 px : sous 720 px il ne tient pas — la rangée dépassait de 103 px — et se replie en loupe. Son seul avantage, se voir sans clic, ne valait que sur grand écran ; sept objets dans la rangée |
| **C** | Le même tiroir, mais l'onglet « Explorateur » conservé à côté | Écartée par la propriétaire : l'onglet ne servait plus à rien, et son clic emmenait vers la fiche par défaut |

## Ce qui reste

La fiche de gouvernement rejoindra `FICHES_FILTRABLES` le jour où elle lira
`?mot=`. Rien d'autre à reprendre : le même test — cette page a-t-elle un
filtre ? — décide du libellé et de la présence du champ.

## Les garde-fous

`tests/test_cadre_fiche_324.py` : les listes ne sont plus dans la page, plus
rien ne lit le défilement, l'outil remplace l'onglet et un seul bouton est
rendu, le champ n'existe que là où il filtre, la barre a quitté le corps des
fiches et les pages n'écrivent plus le mot. Trois garde-fous de #951 y sont
remplacés — ils protégeaient `.explorer-bars` et `.explorer-changer`, qui
n'existent plus.
