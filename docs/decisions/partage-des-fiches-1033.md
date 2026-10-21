<a id="partage-des-fiches-1033"></a>

# Une pastille « Partager cette fiche » flotte sur les trois fiches (#1033) (2026-10-21)

`2026-10-21`

> **En bref** — les trois fiches (candidat, lignée de groupe, gouvernement) portent une pastille ronde « Partager cette fiche », l'icône seule, qui **flotte en bas à droite de l'écran** pendant toute la lecture. Arbitré sur maquette entre sept formes : la forme D (un bouton en bas de la fiche), retenue le 19/10/2026, a été remplacée le 21/10/2026 par la **forme E**, pour que le partage ne demande pas de descendre jusqu'en bas. Au téléphone, elle ouvre le menu de partage du téléphone ; à l'ordinateur, un petit menu : LinkedIn, X, copier le lien. **Seule l'adresse de la fiche est partagée**, celle du site publié, sans message pré-écrit (§2 règle 1) : l'aperçu est celui que la page publie déjà (#1008). **Rien de LinkedIn ni de X n'est chargé** : leurs adresses de partage nues, sans script ni cookie.

## Le contexte

#1033 demandait des boutons de partage vers LinkedIn et X, et laissait ouvert
sur quelles fiches et où. Avant ce lot, aucune fiche n'en portait : un lecteur
copiait l'adresse lui-même.

## La décision

- **Une pastille flottante**, à 20 px du bas et du bord droit de l'écran, la
  même à l'ordinateur et au téléphone. Le libellé « Partager cette fiche » est
  lu par les lecteurs d'écran et s'affiche au survol. Le menu s'ouvre vers le
  haut.
- **Elle passe sous la rangée collée du haut et sous le tiroir « Explorer »**
  (`z-index: 4`, contre 5), et le pied du site garde sous lui la place de la
  pastille, pour qu'elle ne cache pas la fin de la page. Elle n'est pas
  imprimée.
- **Le téléphone se reconnaît au pointeur grossier** (`pointer: coarse`), et non
  à la seule présence de `navigator.share`, que plusieurs navigateurs
  d'ordinateur exposent : la maquette validée y montre le menu du site.
- **L'adresse partagée est `https://empreinte-politique.fr` suivie du chemin**,
  sans ancre ni paramètre : une copie locale ou de prévisualisation partagerait
  sinon une adresse que personne ne peut ouvrir.
- **« Copier le lien »** affiche « Lien copié » au-dessus de la pastille ; si le
  navigateur refuse le presse-papiers, l'adresse s'affiche pour être copiée à
  la main.

## Les alternatives écartées

| Forme | Pourquoi |
| --- | --- |
| A — trois boutons sur une ligne, en bas | Trois gestes de plus sur la fiche, quand un seul suffit |
| B — une carte | Elle se lit comme une section de données |
| C — liens dans la ligne des licences | Le plus sobre, et le plus facile à manquer |
| D — un bouton en bas de la fiche | Retenue le 19/10, puis remplacée : il fallait descendre jusqu'en bas pour la trouver |
| F — un bouton flottant avec son libellé | Au téléphone, il cache le bout de deux lignes de texte |
| G — le libellé à l'ordinateur, la pastille au téléphone | Deux aspects à maintenir pour un seul geste |
| Un bouton dans le bandeau du haut | Le bandeau a été arbitré pour ne pas regagner de geste (#1025) |
