<a id="accueil-telephone-exploration-d-abord-1372"></a>

# Au téléphone, l'accueil ouvre sur l'exploration, le carrousel vient après (#1372, 2026-10-28)

`2026-10-28`

> **En bref** — Sous 720 px, le carrousel des analyses quitte la carte du haut de l'accueil et se pose après les deux tuiles : « Commencer l'exploration » commence à 328 px au lieu de 577, la frise des législatures et des gouvernements paraît dès l'ouverture. Le titre d'une diapositive ne se coupe plus ; flèches de 44 px, points de 12 px. Aucun texte nouveau ; l'ordinateur ne change pas.

## Le problème

À 390 × 844, l'écran d'ouverture montrait le titre, la devise et le carrousel ; « Commencer l'exploration » commençait à 577 px, sous l'écran. Le menu ne mène à aucune fiche : sans défiler, on n'atteignait que les candidats, par le carrousel. Le titre de la première diapositive était coupé (« Focus sur les candidats à la… »), et les flèches (28 px) et les points (7 px) étaient trop petits pour le doigt. La propriétaire, le 28/10/2026 : c'est surtout le premier point qui l'embêtait.

## Ce qui est décidé

Forme **C** de la maquette https://claude.ai/artifact/RP415jP6zf5y9CXWd1F1dx (privée) :

- `Hero.jsx` ne rend plus le carrousel au téléphone (`useEcranEtroit()`) ; `LandingPage.jsx` le rend après `ExplorerTuiles`, avec son fond sombre.
- `AnalysesThematiques.jsx` : au téléphone, la fenêtre prend la hauteur de la plus haute diapositive et ne coupe plus aucun titre ; à l'ordinateur, l'égalisation par rognage reste.
- `landing.css` : flèches de 44 px, points de 12 px (28 px pour le point courant), sous `@media (max-width: 720px)`.

Mesuré le 28/10/2026 dans Chromium à 390 × 844 : « Commencer l'exploration » à 328 px, document large de 390 px ; à 1 280 px, page identique au pixel à celle d'avant.

## Écarté

- **A** : le haut resserré (titre plus petit, devise retirée) ne gagnait que 48 px.
- **B** et **D** : quatre entrées (Candidats, Groupes, Gouvernements, Législatures) sous le titre — des libellés nouveaux ; B repoussait encore l'exploration (669 px).

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone.
- Le menu ne mène toujours à aucune fiche : constat, hors de ce changement.
