<a id="methodologie-de-la-fiche-de-legislature-1314"></a>

# La fiche de législature a sa méthodologie, et ses cinq bulles y renvoient (#1314) (2026-10-23)

`2026-10-23`

> **En bref** — complète [`fiche-legislature-1314`](fiche-legislature-1314.md), qui écrivait le 23/10/2026 que « seule « Ce qu'on n'a pas pu lire » renvoie à la méthodologie : aucune section n'y décrit encore les législatures ». C'est faux depuis #1344 : la page de méthodologie porte une famille **« Fiche de législature »** de quatre sections — `leg-bref`, `leg-sieges`, `leg-textes`, `leg-commissions` —, et chacune des quatre bulles de la fiche qui n'avait pas de lien y renvoie ; « Ce qu'on n'a pas pu lire » garde le sien vers `couverture`. Les textes ont été proposés puis repris par la propriétaire, qui en a renvoyé la version publiée.

## Contexte

Les bulles de la fiche ont été codées avant que la méthodologie la décrive. La
décision qui les consigne disait donc l'absence de lien, vraie ce jour-là.

## Décision

- Quatre sections, dans l'ordre des sections de la fiche, sur le modèle de
  celles de la fiche de gouvernement : ce que montre la figure, puis, en gras,
  la lecture à ne pas manquer (« Les chiffres sont ceux du dernier jour. »,
  « La position d'un groupe est celle qu'il déclare à l'Assemblée »,
  « La couleur dit qui a déposé le texte », « Un texte jamais examiné n'a pas
  été rejeté »).
- Chaque bulle porte « Lire la méthode → » vers sa section ;
  `tests/test_pourquoi_en_methodologie_328.py` refuse un renvoi vers une ancre
  qui n'existe pas.

## Ce qui n'a pas été vérifié

Le rendu de la page de méthodologie n'a pas été capturé : l'interface compile
et les tests passent (7 145, le 23/10/2026), mais personne n'a relu les quatre
sections sur la page publiée.
