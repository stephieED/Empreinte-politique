<a id="en-tete-des-fiches-homogene"></a>

# L'en-tête des quatre fiches perd sa ligne en capitales et prend la même hauteur (2026-10-23)

`2026-10-23`

> **En bref** — demandé par la propriétaire : un en-tête homogène, le plus bas possible, sans la ligne en capitales au-dessus du nom (« Candidat déclaré · élection présidentielle 2027 », « Groupe parlementaire · Assemblée nationale », « Gouvernement », « Assemblée nationale »). Le fil d'Ariane dit déjà ce qu'est la fiche. L'en-tête garde le fil, le nom et une ligne d'identité, puis **24 px avant la première section**, sur les quatre fiches. La ligne d'une fiche de groupe ne redit plus le nom quand la lignée n'en a porté qu'un (« Depuis le 29 juin 2022 »). Mesuré du bandeau du site à « En bref », sur ordinateur : candidat 189 → 170 px, groupe 192 → 159, gouvernement et législature 225 → 166 ; sur téléphone, 228 → 209, 293 → 241 (LIOT, titre sur trois lignes), 236 → 177, 209 → 150. Validé sur maquette avant le code.

## Contexte

L'écart entre le titre et « En bref » allait de 96 px (candidat) à 145 px
(gouvernement, législature) : 40 px de marge en plus et le repère « 01 » sur les
deux dernières. La fiche de groupe redisait son nom sous son titre.

## Décision

- `.cp-entete`, `.lp-entete`, `.gvp-entete` : `margin-bottom: 24px`, la ligne
  d'identité sans marge basse, la première section sans marge haute.
- La ligne en capitales (`.cp-sourcil`, `.lp-sourcil`, `.gvp-sourcil`) est retirée
  du code et des feuilles de style.
- La chambre d'une lignée n'est plus écrite sur sa fiche : les 18 lignées publiées
  sont toutes de l'Assemblée. Le jour où une lignée du Sénat paraîtra, la chambre
  devra revenir dans l'en-tête ; `tests/test_garde_fou_chambre.py` ne déclare plus
  la page parmi les lecteurs de la chambre.

## Alternative écartée

Garder la ligne et seulement harmoniser les marges : l'en-tête restait plus haut
que nécessaire, et la ligne redisait le fil d'Ariane sur trois fiches sur quatre.
Sur la fiche candidat, elle seule disait « élection présidentielle 2027 » ; la
mention part avec elle.
