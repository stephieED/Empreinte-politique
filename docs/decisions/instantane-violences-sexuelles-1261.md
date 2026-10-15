<a id="instantane-violences-sexuelles-1261"></a>

# L'instantané sur les violences sexuelles et sexistes suit une loi, du dépôt au vote sur l'ensemble (#1261) (2026-10-15)

`2026-10-15`

> **En bref** — Le quatrième article de type instantané, « Les violences sexuelles et sexistes à l'Assemblée » (#1261, PR #1267), ne suit pas un périmètre de mots mais **une proposition de loi**, `DLR5L17N54776`, adoptée en première lecture le 13/10/2026 par 441 voix pour, 0 contre et 59 abstentions (`an:17:8705`). Arbitré par la propriétaire du 08 au 15/10/2026, sur maquette puis sur la page : **la période de l'article est celle de la loi** (11/08 – 13/10/2026), les douze mois de contexte sont nommés dans leur section ; **les effectifs sont pris au jour du vote** ; **en commission, on montre les propositions d'amendement sans leur sort et sans celles des rapporteurs** ; **en séance, le sort reste** ; **l'étape de la loi vient du scrutin sur l'ensemble** quand les données ne l'ont pas encore suivie. Ce fichier **complète** `docs/decisions/instantane-compte-des-personnes-1217.md` et `docs/decisions/instantanes-publies-1029.md`, dont les règles ne bougent pas.

## Le contexte

Mesuré le 14/10/2026 sur `main` 11f104594a (données récupérées du dépôt public
le 14/10), données au 13/10/2026.

| Mesure | Valeur | Population |
| --- | --- | --- |
| Vote sur l'ensemble, 13/10 | 441 pour, 0 contre, 59 abstentions | 574 députés : 563 membres des onze groupes et 11 non-inscrits au 13/10 |
| Amendements en commission | 1 050, dont 207 des rapporteurs | commission spéciale PO884839, 71 membres |
| Amendements en séance | 1 292 | tous de type `depute` : la source ne marque pas le rapporteur en séance |
| Scrutins sur le texte | 230, dont 54 sur un article | 53 articles adoptés ; l'article 46, rejeté le 09/10 (`an:17:8640`), rétabli le 13/10 en seconde délibération (`an:17:8704`) |
| Députés intervenus en séance sur le texte | 171 sur 574 | 169 membres de groupe et 2 non-inscrits |
| Textes déposés sur le sujet | 23 | du 14/10/2025 au 13/10/2026, portés par un membre des profils collectés |

## La décision

- **Les effectifs sont ceux du jour du vote sur l'ensemble** (13/10), non
  ceux d'une date fixe : cinq sièges vides au 05/10 ont été pourvus le 08/10
  (558 → 574 avec les non-inscrits). Les non-inscrits sont une douzième part
  partout où l'hémicycle est dessiné, lus dans `raw_data/non_inscrits.json`
  (#1265).
- **En commission, des propositions, pas leur sort.** La figure compte les
  843 amendements de type `depute`, en une seule teinte neutre, sans les 207
  amendements des rapporteurs. Raison donnée par la propriétaire : « on ne sait
  pas si les amendements rejetés sont vraiment rejetés ou s'ils ont été débattu
  et réécris ». La largeur de chaque part est le nombre de membres du groupe
  dans la commission spéciale (71). L'article le dit dans « Ce que cet article
  ne dit pas ».
- **En séance, le sort reste en couleur** (« Non on ne retire pas les couleurs
  sur la page 3 »). La source ne marque pas les rapporteurs en séance : 165
  amendements de séance ont un rapporteur pour premier signataire dans nos
  données (171 à la source), comptés sous son groupe.
- **Les votes sur les articles** sont les 54 scrutins, une colonne chacun,
  numéros d'article tournés d'un quart de tour. Leur titre et leur chapitre
  sont publiés par `pivot_data/articles_votes.json` (#1264,
  `articles-votes-par-la-seance-1264`) : la limite « le numéro d'un article, pas
  son objet » est retirée de l'article. Le détail d'un article au clic n'est
  pas arbitré.
- **La période de l'article est celle de la loi**, du dépôt (11/08/2026) au
  vote sur l'ensemble (13/10/2026) : sous le titre, dans le cartouche et dans
  l'index des articles. La fenêtre de douze mois (14/10/2025 – 13/10/2026) ne
  sert qu'à la section « Douze mois de débats et de textes », qui la nomme.
  Avant le 15/10, l'article affichait cette fenêtre comme sa période.
- **L'étape de la loi vient du vote sur l'ensemble** quand les données ne
  l'ont pas suivie (option B, 15/10) : au 13/10, ses `textes_portes` portaient
  encore `discute_seance` (mis à jour au 09/10). La liste des textes déposés
  affiche « adoptée en première lecture à l'Assemblée », source `an:17:8705`,
  et le losange reste « en cours d'examen » : le texte part au Sénat. Le
  générateur échoue si la ligne ou le scrutin manque.
- **Un texte est attribué à son auteur, pas au premier signataire lu.** Les
  textes déposés sont relevés dans les `textes_portes` des profils ; un
  co-rapporteur lu avant l'autrice dans l'ordre des fichiers attribuait la loi
  à la Gauche Démocrate et Républicaine au lieu des Socialistes et apparentés.
  Le relevé met en tête les rôles `auteur*`, et ne retombe sur les autres
  que si aucun auteur n'est connu. Seule cette ligne changeait sur les 23.
- **Les prises de parole restent dans l'article** (15/10), alors qu'elles
  sont sorties du carrousel le 14/10 : l'article a la place que le carrousel
  n'a pas.
- **Le fichier porte la date des données** (`2026-10-13-…`), non celle de sa
  rédaction.

## L'alternative écartée

- **Les amendements des rapporteurs dans une part à eux**, la treizième, au
  lieu de leur groupe : maquettée le 14/10, non retenue.
- **Le sort des amendements de commission en couleur**, comme en séance :
  écarté pour la raison citée plus haut.
- **Laisser l'étape des données** (option A) : contredisait le chapeau.
  **Attendre un run** (option C) : suspendait la publication à un run.
- **Les douze mois comme période de l'article** : ils ne disent rien de la
  loi, examinée en deux mois.
- Écartés du carrousel, à ne pas reproposer : la chronologie, la page de la
  commission spéciale et tout encadré de sa composition, la page des sources.

## Ce qui n'a pas été vérifié

- La composition de la commission spéciale (71 membres) a été lue à
  l'Assemblée (AMO30) avant que le dépôt la donne juste : il en donnait 78 le
  17/09, faute de dates de fin.
- L'écart de 165 à 171 amendements de séance déposés par un rapporteur, entre
  nos données et la source, n'est pas expliqué.
- La source n'a pas de champ pour un amendement de synthèse, et
  `amendementParentRef` (sous-amendements : 3 en commission, 68 en séance)
  n'est pas collecté.
