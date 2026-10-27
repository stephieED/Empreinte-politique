# Sous `textes`, les seuls textes cités par un scrutin : le fichier variait d'un run à l'autre (#1352) (2026-10-27)

`2026-10-27`

> **En bref** — correction de `articles-des-textes-dans-articles-votes-1352` (26/10/2026), qui publiait sous `textes` les articles de chaque texte **lu** portant des intitulés. Le premier run (26/10, `40400118485`) en a publié 97, contre 101 dans la mesure locale faite sur les mêmes scrutins. Les 4 textes manquants n'étaient lus qu'« au passage », comme versions d'un dossier concurrent dans une séance à plusieurs dossiers. Lesquels sont lus dépend de l'ordre dans lequel ces dossiers sont essayés, qui change d'un process à l'autre. Désormais, seuls les textes **cités** par un scrutin d'article, rattaché ou non, sont publiés : 51 textes, 3 924 articles, dont les 90 du PLF 2027, identiques en local et en CI.

## Ce qui a été mesuré (26-27/10/2026)

| | Mesure locale | Run du 26/10 |
| --- | ---: | ---: |
| Textes sous `textes` (règle « lus ») | 101 | 97 |
| … après filtre « cités par un scrutin » | **51** | **51**, les mêmes |
| Articles après filtre | 3 924 | 3 924 |
| Scrutins rattachés / non rattachés | 1 416 / 703 | 1 416 / 703 |

Les 4 textes absents en CI (`PIONANR5L17B1685`, `PIONANR5L17B2608`,
`PIONANR5L17BTC2733`, `PRJLANR5L16BTC1710`) n'étaient cités par aucun scrutin.

## Décision

`articles_des_textes(lus, cites)` ne garde que l'intersection des textes lus et
des `texte_id` du fichier (scrutins rattachés et non rattachés). Un texte que la
publication ne nomme nulle part n'y entre pas, et le fichier ne dépend plus de
l'ordre des essais.

## Alternative écartée

**Rendre l'ordre des essais déterministe** (trier les dossiers concurrents) : le
fichier deviendrait stable, mais il publierait encore des textes que rien
n'explique au lecteur, et il bougerait au premier changement de la règle
d'élimination.

## Non vérifié

- L'effet sur le prochain run : le fichier publié perdra les 46 textes non cités.
  Aucun lecteur n'en dépend aujourd'hui (la session COM lit le PLF 2027, cité).
