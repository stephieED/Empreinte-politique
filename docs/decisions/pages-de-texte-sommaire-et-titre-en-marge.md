<a id="pages-de-texte-sommaire-et-titre-en-marge"></a>

# Les pages de texte : un sommaire à gauche, le titre de chaque carte en marge (2026-10-21)

`2026-10-21`

> **En bref** — dans la colonne commune de 1 600 px (`largeur-commune-des-pages`), une carte de texte bornée à 80 caractères par ligne laissait sa moitié droite vide, sur À propos, Méthodologie, Mentions légales et FAQ. Les pages de texte reprennent donc **le sommaire des fiches à gauche** (204 px, au-delà de 1 440 px de fenêtre) et mettent **le titre de chaque carte dans une colonne de marge** (240 px, au-delà de 1 024 px), le texte à sa droite. Une carte qui porte une figure — la page Sources — garde son titre au-dessus. Arbitré sur maquette entre cinq formes : la forme E. **Écartées** : les cartes côte à côte (B), dont l'ordre de lecture zigzague sur Méthodologie ; le titre en marge sans sommaire (C) ; le sommaire avec des cartes à la largeur du texte (D), qui repoussait le vide hors des cartes.

## La décision

- **`StaticPage` rend le sommaire** et marque chaque carte (`data-section`),
  chaque titre de groupe de Méthodologie (`data-section-groupe`) et chaque bloc
  composé (`titre`). Une section sans ancre en reçoit une, tirée de son titre.
  Une page à venir faite avec ce composant hérite de tout.
- **Les pages qui composent leur propre cadre** (À propos, Sources, Nous
  soutenir) rendent le même sommaire et marquent leurs cartes.
- **Le sommaire affiche les titres de groupe** en encre, et défile seul si la
  fenêtre est trop basse pour la vingtaine d'entrées de Méthodologie.
- **Le bandeau noir d'À propos et de Nous soutenir** (forme C, même jour) :
  son texte garde sa mesure de 40em — du texte clair sur fond sombre fatigue
  au-delà — et ce qui n'est pas du texte passe à droite au-delà de 1 024 px :
  la devise en quatre tuiles (le chiffre en grand, le mot dessous) sur À
  propos, le bouton de don sur Nous soutenir. Les tuiles lisent la devise
  unique de `Baseline.jsx`. Écartées : la devise en grand alignée à droite
  (B), le titre en marge du bandeau (D).
- **Garde-fou** : `tests/test_pages_de_texte.py`.

## Les alternatives écartées

| Forme | Pourquoi |
| --- | --- |
| A — rien changer | La moitié droite de chaque carte vide |
| B — cartes côte à côte | L'ordre de lecture zigzague sur Méthodologie |
| C — titre en marge, sans sommaire | Retenue, puis complétée par le sommaire (E) |
| D — sommaire, cartes à la largeur du texte | Le vide passe hors des cartes |
