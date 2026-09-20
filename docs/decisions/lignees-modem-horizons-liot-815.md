# Les lignées MoDem, Horizons et LIOT, et un tri qui plantait sur un seul député (#815)

`2026-09-11`

> **En bref** — trois lignées de plus, déclarées sur l'archive AMO30 republiée le 11/09/2026 à 02:34 : **MoDem** `DEM:15 → DEM:16 → DEM:17`, **Horizons** `HOR:16 → HOR:17`, **LIOT** `LIOT:16 → LIOT:17` — **7 fiches**, effectifs 67, 58, 42, 36, 44, 22 et 26, soit **178 personnes distinctes**, dont **37** ont déjà un profil publié et **141** sont à collecter par le run. Le MoDem de la XVe est l'**union de deux organes** — `MODEM` jusqu'au 23/09/2020, `DEM` dès le 24 —, le motif `SOC`/`SOC-A` de la XVIe : sans l'union, trois ans sur cinq disparaîtraient. **La mesure a trouvé un défaut que le run aurait payé** : `fusionner_intervalles`, posé par #809 la veille, triait des couples `(début, fin)` et levait `TypeError` dès que deux mandats de même début avaient l'un une fin, l'autre aucune. **Un seul couple de tout l'index GP** porte cette forme — Stéphane Lenormand, LIOT-17, `2024-07-19 → 2025-02-28` puis `2024-07-19 → ouvert` —, aucun des 21 groupes jusque-là déclarés ne la portait, et c'est pourquoi rien ne l'avait vu ; déclarer LIOT-17 sans corriger aurait fait tomber le roster du run. La clé de tri ne compare plus jamais une fin ouverte à une date. **Non déclarés, et ce n'est pas un oubli** : `LT` (XVe) comme prédécesseur de LIOT, `AGIR-E` (XVe) comme prédécesseur d'Horizons — deux jugements de filiation que personne n'a portés ; l'identifiant de lignée étant déclaré, les ajouter plus tard ne le déplacera pas. UDR, scission, attend toujours sa forme. Suite complète à **4 503**, 0 échec.

## Ce qui a été mesuré, et sur quoi

L'archive AMO30 locale datait du 17/08 ; l'Assemblée l'a republiée le 11/09 à
02:34. Les déclarations sont mesurées sur la **nouvelle**, téléchargée à part
pour ne pas écraser le cache partagé des autres sessions.

| Fiche | Organe(s) | Période | Position AN | Effectif | Table slug |
| --- | --- | --- | --- | ---: | ---: |
| `DEM-15` | PO730970 `MODEM` + PO774834 `DEM` | 2017-06-27 → 2022-06-21 | Minoritaire ×2 | 67 | 11 |
| `DEM-16` | PO800484 `DEM` | 2022-06-28 → 2024-06-09 | Minoritaire | 58 | 5 |
| `DEM-17` | PO845454 `DEM` | 2024-07-18 → en cours | non déclarée | 42 | 6 |
| `HOR-16` | PO800514 `HOR` | 2022-06-28 → 2024-06-09 | Minoritaire | 36 | 12 |
| `HOR-17` | PO845470 `HOR` | 2024-07-18 → en cours | non déclarée | 44 | 14 |
| `LIOT-16` | PO800532 `LIOT` | 2022-06-28 → 2024-06-09 | Opposition | 22 | 5 |
| `LIOT-17` | PO845485 `LIOT` | 2024-07-18 → en cours | non déclarée | 26 | 5 |

**Aucun mandat de transit** sur ces huit organes. Les sept rosters passent la
**vraie chaîne** (`deriver_roster_groupe`, configuration committée comprise) :
effectif attendu = effectif mesuré, organes attendus = organes trouvés, **0**
membre sans slug — les 237 entrées de maillon sans entrée de table reçoivent un slug fabriqué
(#708).

Les sept groupes de la XVIIe déjà déclarés gardent leur effectif **au membre
près** sur l'archive du 11/09 : l'élargissement n'est pas une régression.

## Le tri qui plantait

`fusionner_intervalles` recolle les mandats contigus d'un acteur et garde ses
interruptions (#809). Il triait des couples `(début, fin)` : à début égal,
Python compare les fins, et `None < "2025-02-28"` lève.

La forme existe dans la source pour **un seul** couple (acteur, organe) de
tout l'index GP — un mandat réémis avec la même date de début, l'ancien refermé.
Aucun des 21 groupes AN déclarés avant ce lot ne la portait : les tests de #809
étaient justes, le corpus n'avait simplement jamais présenté le cas. C'est la
mesure sur les **nouveaux** groupes, faite avant d'écrire la déclaration, qui
l'a montré — un run l'aurait montré en tombant.

À début égal, l'ordre est indifférent : la période ouverte absorbe l'autre dans
les deux sens. La clé ne compare donc plus que des chaînes, et place la fin
ouverte après.

## Ce qui n'est pas déclaré, et pourquoi ce n'est pas un trou

- **`LT` → `LIOT`.** « Libertés et Territoires » (XVe, 2018 → 2022) est
  communément présenté comme l'ancêtre de LIOT. Mais `succede_a` est une
  **relecture humaine** : l'Assemblée ouvre et ferme des organes, elle ne les
  chaîne pas (#700), et ni le sigle ni l'organe ne se prolongent.
- **`AGIR-E` → `HOR`.** Même question, même réponse.

Les ajouter plus tard coûte une fiche et un maillon : l'identifiant
`AN:LIGNEE:LIOT` ne bougera pas, c'est précisément pourquoi il est déclaré
plutôt que dérivé de la racine (#836).

## Le coût, pour le run

141 profils neufs à collecter sur 178 personnes ; 87 de ces 141 siègent sous
la XVIIe, donc en collecte complète — les autres sont en législature close et
ne coûtent que leur socle depuis #691. Le run répartit le roster sur les mêmes
8 shards : sa durée croîtra, et c'est le run qui la mesurera.
