<a id="telephone-bandeau-du-carrousel-1372"></a>

# Au téléphone, un bandeau fixe rappelle le carrousel des articles (#1372, 2026-10-29)

`2026-10-29`

> **En bref** — Sous 720 px, l'accueil porte un bandeau de 63 px en bas d'écran qui montre la diapositive courante du carrousel des articles (même index, même rythme) : vignette, étiquette et date, titre sur une ligne ; une flèche pour l'article suivant, une croix pour le fermer pendant la visite. Il s'efface quand le carrousel est à l'écran. Forme B+C, arbitrée le 29/10/2026. Aucun texte nouveau à l'écran ; « Fermer » pour les lecteurs d'écran, validé.

## Le problème

Depuis `accueil-telephone-exploration-d-abord-1372`, le carrousel vient après les tuiles : la propriétaire, le 29/10/2026 : « l'idée est que le lecteur ne passe pas à côté s'il ne scroll pas jusqu'en bas », avec un bandeau « pas trop épais ».

## Ce qui est décidé

Forme **B+C** de la maquette https://claude.ai/artifact/9ynQCMbVQan9KL8iDBsah5 (privée), dans `AnalysesThematiques.jsx`, seulement pour l'instance posée après les tuiles au téléphone (`dansHero` et `useEcranEtroit()`) :

- le bandeau lit le **même index** que le carrousel : il change d'article à son rythme (6 s), et sa flèche fait avancer les deux ;
- un `IntersectionObserver` le masque (`hidden`) tant que le carrousel est à l'écran ;
- la croix le ferme pour la visite (`sessionStorage`, lu et écrit sous `try` : sans stockage, il reste fermé jusqu'au départ de la page) ;
- la page réserve 76 px en bas tant que le bandeau existe, pour qu'il ne cache rien — sans saut de mise en page quand il s'efface.

Textes : ceux de la diapositive (« Événement · Jusqu'en mai 2027 », « Analyse thématique · 13 octobre 2026 », le titre). Libellés pour lecteurs d'écran : « Analyse suivante » (déjà celui du carrousel) et « Fermer » (validé le 29/10/2026).

Mesuré le 29/10/2026 dans Chromium à 390 × 844 : bandeau de 63 px, document de 390 px, flèche, effacement au carrousel, fermeture gardée au rechargement ; à 1 280 px, aucun bandeau.

## Écarté

- **A** (toujours affiché, sans bouton), **B** (sans effacement : le carrousel se voyait deux fois), **C** (sans flèche ni fermeture).

## Ce qui n'est pas vérifié

- Au doigt, sur un vrai téléphone, ni avec un lecteur d'écran.
