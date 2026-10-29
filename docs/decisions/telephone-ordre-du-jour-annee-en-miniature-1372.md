<a id="telephone-ordre-du-jour-annee-en-miniature-1372"></a>

# Au téléphone, l'ordre du jour montre l'année en miniature, puis le mois en grand (#1372, 2026-10-29)

`2026-10-29`

> **En bref** — Sous 720 px, la vue « Calendrier » de « À l'ordre du jour » (fiche de législature) ne montre plus les douze mois en grand l'un sous l'autre : l'année tient en une miniature de trois colonnes, réduite aux couleurs ; toucher un mois l'ouvre en grand dessous, avec deux flèches pour passer au voisin, puis le détail du jour. Aucun texte nouveau à l'écran ; l'ordinateur ne change pas.

## Le problème

La propriétaire, le 29/10/2026 : « sur mobile, on arrive pas vraiment à voir les agendas dans leur ensemble ». Mesuré à 390 px sur la XVIIe, année 2026 : la vue « Calendrier » empilait les douze mois sur 4 460 px, plus de cinq écrans, et le détail du jour choisi s'affichait après décembre ; la vue « Planning » faisait 8 800 px. L'année ne se voyait jamais d'un coup.

## Ce qui est décidé

Forme **B** de la maquette https://claude.ai/artifact/RBd1fdCNxumWSJ4nMVF6Fj (privée), dans `OrdreDuJour` (`LegislatureProfile.jsx`), derrière `useEcranEtroit()` :

- **La miniature** : les douze mois en trois colonnes ; chaque jour est une case de 11 px qui porte la barre de couleurs du jour (mêmes couleurs, même filtre de légende, mêmes marques « sans texte » et « pas encore fixé »), sans numéro ni semaine. Chaque mois est un bouton ; le mois ouvert est encadré.
- **Le mois en grand** : le rendu de l'ordinateur (`moisEnGrand`), son nom entre deux flèches de 44 px (mois précédent, mois suivant, dans l'année affichée). Par défaut, le mois du jour détaillé.
- **Le détail du jour** suit, inchangé. À 390 px, il commence à 1 030 px du haut de la section au lieu de plus de 4 000.
- Changer d'année referme le mois choisi.

La vue « Planning » n'est pas touchée.

Mesuré le 29/10/2026 dans Chromium : à 390 px, section de 2 037 px (4 460 avant), document large de 390 px ; à 1 280 px, calendrier, détail et commandes identiques au pixel à ceux de `main`.

## Écarté

- **A**, un mois à la fois avec flèches : plus court (détail à 583 px), mais l'année ne se voyait plus d'ensemble — ce que la propriétaire demandait.

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone.
- Les libellés « Mois précédent » et « Mois suivant » ne sont lus que par les lecteurs d'écran (`aria-label`).
