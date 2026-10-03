# Les groupes et leurs lignées se dérivent d'AMO30 : le calcul retrouve la table (#1168, lot 1)

`2026-10-02`

> **En bref** — `src/groupes_amo30.py` dérive de l'archive AMO30, **sans lire la table écrite à la main**, les groupes de l'Assemblée depuis la XVe, leurs renommages et leurs lignées, par une seule règle appliquée deux fois (personnes communes sur l'effectif du plus petit des deux, à partir de la moitié). Mesuré sur l'archive publiée le 02/10/2026 contre les 32 entrées de `config/groupes_reels.json` : **15 lignées sur 15 identiques**, **30 groupes sur 32**, **15 liens entre législatures sur 16**, et sur les quatre champs écrits à la main des 30 groupes identiques, **un seul écart** — l'effectif de `LIOT-17`, 26 dans la table, 27 dans la source. Les trois différences de structure n'en sont qu'une : `NG` et `SOC` de la XVe, que la règle réunit en un groupe renommé et que la table écrit comme deux groupes. **Ce lot ne change rien à ce qui est publié** : aucun job ne lit le module. Direction donnée par la propriétaire le 02/10/2026 — groupes et lignées calculés dans le run, adresses figées ; le plan en quatre lots est dans #1168.

## Le problème

La liste des groupes, leurs organes successifs, leurs noms, leur position et
leurs liens d'une législature à l'autre sont écrits à la main dans
`config/groupes_reels.json`. Deux faits du 02/10/2026 :

- trois groupes de la XVe n'y étaient pas, sans qu'aucune décision les ait
  écartés (`groupes-xve-manquants-1168`) ;
- la propriétaire a demandé qu'un groupe nouveau s'ajoute seul, et que la lignée
  soit calculée dans le run.

Le dépôt le fait déjà pour les gouvernements : `gouvernements_amo30.py` lit leur
liste dans la même archive (#996, #1129).

## Ce qui est décidé

Un module de dérivation, **pur**, que rien ne lit encore.

| Étage | Règle | Rend |
| --- | --- | --- |
| Renommage, dans une législature | le second organe ouvre au plus tard le lendemain de la fermeture du premier (`an_roster._contigus`), la règle de la moitié passe, et le couple est **seul de son espèce** des deux côtés | un groupe = une chaîne d'organes |
| Filiation, d'une législature à la suivante | la règle de la moitié, entre groupes entiers ; tous les couples qui passent | les liens |
| Lignée | ce que les liens relient | les lignées |

Chaque groupe dérivé porte ce que la table écrit à la main : `organes_an`,
`sigles_an`, `historique_organes_an`, `position_politique_an` (résumée par
`resumer_position_politique`, jamais choisie), `effectif_amo30` (après le filtre
des mandats de transit). Il ne porte **ni `groupe_id`, ni sigle publié, ni
`lignee_id`** : ce sont des noms, et un nom ne se dérive pas. Le lot 2 les tient
dans un registre.

## Ce que la mesure donne

Archive AMO30 publiée le 02/10/2026 à 02:34, `--comparer`, non-inscrits exclus.

| Étage | Dérivé | Table | Identiques |
| --- | ---: | ---: | ---: |
| Lignées | 15 | 15 | **15** |
| Groupes | 31 | 32 | 30 |
| Liens entre législatures | 16 | 16 | 15 |

**Une seule cause pour les trois écarts de structure.** `NG` ferme le 11/09/2018,
`SOC` ouvre le 12 ; 30 personnes communes sur 33. La règle en fait un groupe
renommé, la table deux groupes reliés par un `succede_a`. Le lien vers `SOC-16`
suit : dérivé depuis `NG+SOC`, écrit depuis `SOC` seul. La lignée, elle, est la
même. **À arbitrer par la propriétaire** (point A du plan).

**Les dix couples d'organes contigus des trois législatures** : neuf renommages,
du plus bas à 30 sur 33 (`NG → SOC`) au plus haut à 35 sur 35, et une scission à
10 sur 23 (`UDI-A-I → AGIR-E`). Aucun cas ambigu.

**Champ par champ, sur les 30 groupes identiques** : organes, noms successifs et
leurs dates, position — tous égaux. Un effectif diffère : `LIOT-17`, 26 dans la
table (relevé le 11/09), 27 dans l'archive du 02/10. C'est exactement ce qu'une
table écrite à la main ne peut pas suivre.

Sur l'archive réduite des tests (XVIe et XVIIe) : 11 lignées, 21 groupes et 10
liens, tous identiques, aucun champ différent. C'est ce que la suite tient.

## Ce qui n'est pas tranché n'est pas deviné

- **Deux successeurs contigus au-dessus du seuil** — une scission en deux
  moitiés — ou deux prédécesseurs : aucun n'est réuni, et le cas est nommé dans
  `renommages_ambigus`. Le corpus n'en porte aucun ; un test l'écrit.
- **Un groupe sans membre connu** n'entre dans aucun lien.
- **Avant la XVe** : `PREMIERE_LEGISLATURE = 15` est une borne **déclarée**. AMO30
  porte les groupes depuis la XIIe ; la règle n'y a pas été éprouvée (point C du
  plan).

## Alternatives écartées

- **Étendre l'audit de filiation.** Il compare la table à la composition : il
  part de la table. La dérivation n'en lit pas une ligne, et c'est ce qui lui
  permet de la remplacer.
- **Brancher le run tout de suite.** Cela touche `generate-data.yml`, le roster,
  la génération des fiches et le portail, et suppose le registre des adresses.
  Un lot qui ne change rien de publié se relit sans risque ; l'autre, non.
- **Une tolérance de plusieurs jours pour le renommage.** `_contigus` a mesuré
  qu'aucun écart de 2 à 30 jours n'existe entre deux mandats ; le seul couple à
  deux jours d'écart ici est une scission.

## Ce qui n'a pas été vérifié

- Le coût d'une législature neuve pour la matrice roster (plusieurs centaines de
  personnes à collecter d'un coup).
- Ce que l'interface affiche pour un groupe au sigle brut de l'Assemblée.
