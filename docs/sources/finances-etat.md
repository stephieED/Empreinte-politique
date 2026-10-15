# `data.economie.gouv.fr` — les finances de l'État

> **Statut : vivante — collectée par le job `extract-finances-etat` depuis #1053**
> (12/10/2026). `src/finances_etat.py` relit à chaque run les grandes lignes et les
> deux derniers exercices ; `raw_data/finances_etat.json` apparaît au premier run
> qui suit la publication du workflow. **Rien n'en est encore publié sur le site.**
> Ce fichier décrit ce que le **fournisseur** publie, et dérive avec lui, non avec
> notre code.

## Producteur et licence

Producteur : **ministères économiques et financiers** (Direction du budget,
DGFiP). **Licence Ouverte 2.0** sur chacun des jeux lus — attribution seule, pas
de partage à l'identique. Mesuré le 08/10/2026 sur le catalogue entier : 562 des
617 jeux du portail la déclarent, 47 ne déclarent rien. **Une licence se vérifie
jeu par jeu**, pas sur le portail. L'étiquette canonique est
`licences.LICENCE_FINANCES_ETAT`, jamais recopiée en dur (AGENTS.md §7).

## Où lire, et où ne pas lire

| Site | Ce que c'est | Se lit par script ? |
| --- | --- | --- |
| `data.economie.gouv.fr` | le portail de données, sous Opendatasoft : `…/api/explore/v2.1/catalog/datasets/<jeu>/records`, `/exports/json`, `/attachments/<pièce>` | oui, sans clé |
| `data.gouv.fr` | le même catalogue, repris sous l'organisation du ministère (661 jeux) ; ses fichiers `static.data.gouv.fr` ont une adresse datée qui ne bouge pas | oui |
| `budget.gouv.fr` | un site éditorial, derrière une protection anti-robots (212 octets rendus à une requête simple). **Jamais contournée.** C'est pourtant le seul endroit où paraît d'abord le projet de loi de finances de l'année | non |

## Ce que le fournisseur publie

### Les grandes lignes — un seul jeu, sans trou

`situations-mensuelles-budgetaires-series-longues` (DGFiP), quatre pièces jointes :

| Pièce | Contenu | Mesure du 12/10/2026 |
| --- | --- | --- |
| `Séries longues SMB_DGFiP_2013-2023.csv`, `Serie longue SMB_DGFiP_2024-xx.csv` | cumul depuis janvier, à chaque fin de mois | 26 lignes × 163 mois, de janvier 2013 à juillet 2026 |
| `textes législatifs open data_2013-2023.csv`, `textes législatifs_2024-xx.csv` | pour les mêmes lignes : `LFI`, `Dernière LFR/LFG`, `Exécution` | 13 exercices, 2013 à 2025 |

Les 26 lignes : recettes par impôt (revenu, sociétés, TVA, TICPE, autres fiscales,
non fiscales), dépenses du budget général par nature (personnel, fonctionnement,
intervention, charge de la dette, investissement, pouvoirs publics, opérations
financières), prélèvements sur recettes, remboursements et dégrèvements, soldes.
**Aucun ministère, aucune mission.** Vérifié sur les 13 exercices : les six postes
de recettes se somment au total des recettes nettes, les natures de dépenses au
total des dépenses nettes.

### Les crédits par programme et par ministère — un fichier par an, onze formats

Budget général, crédits de paiement. Le **voté** vient des jeux de loi de finances
initiale, le **consommé** des jeux de loi de règlement.

| Exercice | Voté | Consommé |
| --- | --- | --- |
| 2015 | **non publié en données** (le projet seul l'est) | CSV cp1252, quatre lignes de titre, sur `static.data.gouv.fr` ; la mission dans son jumeau `PLR2015-Exec-Msn_CP-BG.csv` |
| 2016, 2017 | CSV cp1252, quatre lignes de titre | idem, jumeau `Msn` compris ; 2017 porte sept colonnes de titres et pas de total, et son jumeau une ligne par catégorie sans lignes de titre |
| 2018 | CSV cp1252, tous budgets | export JSON, ministère « au 1er janvier 2018 », colonnes `code_mission` et `mission` |
| 2019 | export JSON | classeur `.xls`, ministère et mission en code seul, libellés dans un second classeur (lignes `MIN`, `MSN`, `PGM`) |
| 2020 | CSV, ministère en code seul, libellés dans un fichier de nomenclature | classeur `.xls`, idem 2019 |
| 2021, 2022 | CSV cp1252 : projet, amendements et loi votée côte à côte | **PDF seulement** |
| 2023 à 2025 | colonne `LFI` du fichier d'exécution | `Annexe1-Etat_CP-<an>.csv`, UTF-8, virgule décimale, **sans colonne ministère** |

Le code de ministère est stable d'une année à l'autre (1 = Affaires étrangères,
9 = Intérieur, 70 = Armées), son libellé change à chaque remaniement, et la source
l'écrit de quatre façons : `MIN01`, `01`, `1`, `1.0`.

## Les pièges

- **Le serveur compresse sans le dire.** Une même adresse rend tantôt du JSON,
  tantôt du gzip sans en-tête `Content-Encoding` ; deux pièces du jeu mensuel sont
  en UTF-16. Regarder les premiers octets, jamais l'extension.
- **Les fichiers d'exécution de 2023 à 2025 n'ont pas de ministère.** Ils portent
  le programme en fin de libellé (« … - 105 »). Le ministère vient de la
  nomenclature du budget de la même année, où chaque programme relève d'un seul
  ministère — mesuré sur les trois années, zéro programme à deux ministères. Un
  seul programme exécuté n'y figure pas en 2023 et 2024 (le 367, montant nul),
  deux en 2025 (367 et 385, 0,01 Md€).
- **Le jeu 2024 du budget par ministère ne porte pas le code**, seulement le
  libellé.
- **`credits-ae-et-cp-votes-…-lfi-2023` : les colonnes `…_lfi_2023` valent 4.0 sur
  toutes les lignes.** Le jeu ne sert que de nomenclature.
- **La colonne `Exécution` du fichier des textes est décalée d'un an de 2019 à
  2021** : elle porte 329,7 Md€ de dépenses en 2019, qui est le cumul de décembre
  2018. Le cumul de décembre des séries mensuelles est juste.
- **La loi de finances 2015 n'a pas le détail des dépenses par nature** dans le
  fichier des textes (totaux seuls).
- **Le « budget vert » porte une colonne d'exécution 2022 qui ne comble pas le
  trou** : 40 des 48 missions, sans « Remboursements et dégrèvements » (130,6 Md€
  votés), avec une ligne sans mission de −53,1 Md€.
- **La mission de chaque programme est publiée de 2015 à 2020 et de 2023 à 2025**,
  et non « de 2023 à 2025 seulement », comme ce fichier l'a dit du 13 au 15/10/2026
  (#1302). Dans les fichiers d'exécution de 2023 à 2025 : 33 missions par
  exercice. De 2015 à 2017, dans le fichier par mission voisin du fichier par
  ministère ; de 2018 à 2020, dans le fichier déjà lu (le code seul en 2019 et 2020,
  le libellé dans la nomenclature, dont les codes ne sont uniques que par type de
  budget : « ZC » est aussi un compte de concours financiers). Une mission par
  programme partout (zéro programme sous deux missions, mesuré le 13/10/2026 sur
  2023-2025 et le 15/10/2026 sur 2015-2020). En 2015, **dix-neuf programmes**
  du fichier par ministère manquent au fichier par mission, tous à 0 €. Le découpage change d'un budget au suivant : « Travail et
  emploi » devient « Travail, emploi et administration des ministères sociaux » en
  2025 ; la même année, le programme 124 de la mission « Solidarité, insertion et
  égalité des chances » disparaît et un programme 155 apparaît sous la mission
  renommée. Aucune mission n'est
  publiée par mois : un changement de gouvernement en cours d'année n'y laisse
  aucune coupure.
- **Le nom du programme est dans la même colonne que son numéro** : « Charge de
  la dette et trésorerie de l'État (crédits évaluatifs) - 117 ». La collecte
  garde ce qui précède « - 117 » sous `libelle_programme`, et le met à `null` si
  deux lignes du même programme l'écrivent différemment. Relu hors dépôt le
  14/10/2026 sur 2023, 2024 et 2025 : 129, 128 et 127 programmes hors
  « Remboursements et dégrèvements », aucun sans nom.
- **Les deux fichiers du budget ne donnent le même total de dépenses qu'avec une
  ligne de plus.** Le jeu mensuel compte dans ses « dépenses nettes du budget
  général » les remboursements et dégrèvements d'impôts **locaux**, qui ne sont
  dans aucune mission hors « Remboursements et dégrèvements ». Mesuré le
  13/10/2026 sur 2023, 2024 et 2025 : dépenses nettes = somme des missions hors
  « Remboursements et dégrèvements » + cette ligne, à moins de 1 M€ (5,1 Md€ en
  2023, 5,0 en 2024, 4,5 en 2025). L'écart signalé « inexpliqué » le 12/10 est
  celui-là. **De 2015 à 2020, il n'y a pas d'écart** : les dépenses nettes valent
  la somme des missions hors « Remboursements et dégrèvements » à 23 € près
  (mesuré le 15/10/2026) — la ligne des dégrèvements locaux n'y est pas comptée.
- **Une page de présentation n'est pas le jeu.** Des jeux affichent zéro
  enregistrement à l'API et tout leur contenu en pièces jointes.

## Ce que la source ne publie pas

- Rien à la maille du ministère avant 2010, et des libellés abrégés jusqu'en 2014
  (« AffSoc&Santé », « Enseign sup et rech ») : la collecte commence en 2015.
- Aucune recette rattachée à un ministère.
- L'exécution 2021 et 2022 par programme, hors PDF — donc ni ministère ni mission
  pour ces deux années.
- Le budget de l'année en cours sur le portail : en octobre 2026, le projet de loi
  de finances 2026 n'est que sur `budget.gouv.fr`, que ce dépôt ne lit pas.

## Sources écartées, et pourquoi

| Source | Mesure | Raison |
| --- | --- | --- |
| Eurostat (`gov_10a_taxag`, `gov_10a_exp`) | 93 postes d'impôt 1995-2025, 80 fonctions de dépense, annuel | comptabilité nationale, qui ne se recoupe pas avec les lois de finances ; écartée par la propriétaire le 08/10/2026 |
| Insee (`COMPTES-ETAT`) | 4 séries mensuelles depuis 2009 | trop agrégé ; écartée le même jour |
| Cour des comptes (data.gouv.fr) | deux jeux thématiques, 2017 et 2019 | hors sujet, et sous ODbL |
