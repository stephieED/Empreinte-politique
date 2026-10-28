<a id="telephone-une-section-par-ecran-1372"></a>

# Au téléphone, une section par écran : on glisse de l'une à l'autre (#1372, 2026-10-28)

`2026-10-28`

> **En bref** — Sous 720 px, les quatre fiches (candidat, groupe, gouvernement, législature) montrent une section à la fois ; on passe à la voisine en glissant le doigt, ou par une rangée d'onglets collée en haut. Arbitré le 28/10/2026 sur prototype (forme A, onglets), avec la base A′ : bandeau « En construction » sur une ligne, partage dans la barre, sections sans carte blanche, aucun texte hors figure sous 13 px. Déclencheur : « Ton formattage est tout cassé ! », sur r/developpeurs. L'ordinateur ne change pas.

## Le problème mesuré

Le 28/10/2026, en production, à 390 px :

| Mesure | Fiche Mélenchon |
| --- | --- |
| Longueur | 13,6 écrans de défilement (11 468 px), 7 sections, aucun moyen d'aller à l'une d'elles |
| Premier écran | Le nom finissait à 331 px sur 844 : bandeau, barre, fil d'Ariane et cases de période prenaient 39 % de l'écran |
| Largeur utile | Texte à 61 px du bord en valeur médiane (carte dans la page, bloc dans la carte) |
| Petits textes | 111 textes sur 446 sous 12 px |
| Bouton de partage | Flottant, il cachait en permanence le bas à droite du contenu |

## Ce qui est décidé

| Point | Choix |
| --- | --- |
| Mécanique | **A, onglets** : une section par écran, glisser à gauche ou à droite, rangée de titres de section qui suit et permet de sauter |
| Écartées | B, « pas à pas » (repères de progression, suivante annoncée en bas) ; C, « sommaire » (aperçu de chaque section, puis feuillet) |
| Base | **A′** : le bandeau sur une ligne qu'on touche pour la déplier (texte inchangé, toujours non refermable) ; le partage dans la barre ; les sections sans carte ; un plancher de 13 px |
| Figures qui défilent de côté | Elles gardent le geste : glisser ailleurs pour changer de section. Choisi plutôt que de les empiler en attendant, puisque le lot 3 de #1372 les redessine |

Prototype : https://claude.ai/artifact/JiCfThd5CNzgpuweLoLitH (privé).

## Comment c'est construit

- **Le composant lit la page** (`GlissementSections.jsx`), comme `SommaireSections` :
  les quatre fiches rangent leurs blocs dans un seul `<main>` et chaque section porte
  `data-section`. Aucune fiche n'a été modifiée.
- **Les blocs des autres sections sont masqués** (`data-glisse-cache`), pas déplacés :
  le DOM reste celui de React. Un `MutationObserver` repose les marques quand une fiche
  re-rend ses blocs.
- **Le document défile toujours verticalement.** Écarté : un conteneur à défilement
  horizontal (`scroll-snap`), comme dans le prototype. Il impose une hauteur fixe par
  section et un défilement vertical dans chacune, qui empêche la barre du navigateur de
  se replier et double les barres de défilement.
- **Le plancher de 13 px est une liste mesurée**, pas 301 règles CSS reprises une à
  une : les classes affichées sous 13 px à 390 px sur dix fiches, moins celles qui
  portent aussi un texte plus grand ailleurs. Le texte des figures SVG n'est pas
  touché : il se règle avec la figure, au lot 3.

## Ce qui n'a pas été vérifié

- Sur un vrai téléphone : tout est mesuré dans Chromium en émulation tactile (390 ×
  844). Le geste, en particulier, n'a été joué que par événements simulés.
- Une classe de texte ajoutée après le 28/10/2026 n'est pas dans la liste du plancher.
- Les 92 constats de la revue (https://claude.ai/artifact/UaZ6kLT56iHox41a33krUT)
  restent ouverts : lots 2 et 3 de #1372.
