<a id="reouverture-partielle-senat-885"></a>
# Le Sénat rentre dans le périmètre pour ses appartenances, pas pour ses scrutins (#885) (2026-09-13)

`2026-09-13`

> **En bref** — le §7 de [`retrait-senat-528`](retrait-senat-528.md) exigeait que la réouverture soit « reprise explicitement, **ici**, avec sa date » : c'est ce fichier, 13/09/2026, décision de la propriétaire. Sa condition 1 est **remplie** — `data.senat.fr` sondé pour de vrai, 55 ressources, producteur Sénat, **Licence Ouverte** (`fr-lo`), plus permissive que l'ODbL ; sa condition 2 est **déclarée non remplie** — ce jeu ne porte ni scrutins (`activite.scrid` pointe vers un référentiel absent) ni comptes rendus, donc aucun `cohesion_votes` sénatorial n'en sortira, et la propriétaire a tranché : « s'il n'y a pas de scrutin, on va l'écrire dans l'UI. Mais on ne va pas jeter à la poubelle les données à cause de ça. » Ce que la prémisse du §7.3 interdisait de plaider — « on perd des données » — est remplacé par ce qu'il exigeait, « on en gagne, et voici lesquelles » : les **10 mandats** qui ne tenaient qu'à NosSénateurs sont **tous** couverts et datés, `jean-luc-melenchon` récupère **trois** mandats sénatoriaux (1986-1995, 1995-2000, 2004-2010) au lieu d'un, et le Sénat publie **ce que l'Assemblée ne peut pas donner** : le nom d'un organe **à la date**, par `libgrppol` (**49 libellés bornés**) et `memgrppol` (**3 213 appartenances datées**, avec le type membre / apparenté / rattaché). En sens inverse, `activite_senateur` porte **11 069 lignes de présence individuelle** que §2 règle 3 interdit de publier : elle se refuse **à l'entrée de la collecte**, pas à l'affichage. Ce lot **remplace #878**, dont la source était la mauvaise.

## 1. Les trois conditions du §7, une par une

| Condition | État au 13/09/2026 |
| --- | --- |
| 1. une source **établie**, sondée, avec ce qu'elle publie et sa licence | **remplie** (§2) |
| 2. au moins **un agrégat publiable** — `cohesion_votes` non nul, ou interventions rattachables | **NON remplie, et déclarée telle** (§4) |
| 3. la décision éditoriale **reprise explicitement, ici, avec sa date** | **ce fichier, 13/09/2026** |

La réouverture est donc **partielle et nommée telle**. La condition 2 n'est pas contournée : son absence devient un fait publié dans l'interface, ce qui est la seule façon honnête de ne pas jeter des appartenances datées au motif que les scrutins manquent.

## 2. La source, mesurée

`data.senat.fr`, producteur **Sénat**, **55 ressources** référencées sur `data.gouv.fr`, licence `fr-lo` — **Licence Ouverte**, attribution seule, réutilisation commerciale autorisée, **pas de partage à l'identique**. Même famille que `data.assemblee-nationale.fr`.

**Deux formes, et la distinction est le piège du lot** : les extraits `ODSEN_*` (CSV/JSON/XLS) ne portent, pour les groupes politiques, que l'appartenance **courante** ; l'export PostgreSQL `export_sens.zip` (8,3 Mo, 58 Mo décompressés) porte l'**historique daté**. Lire les seuls extraits conduit à conclure que l'historique des groupes n'existe pas. Cette erreur a été commise, puis corrigée, en instruisant l'issue.

| Table de l'export | Lignes | Ce qu'elle porte |
| --- | ---: | --- |
| `elusen` | 3 555 | mandats sénatoriaux, avec **motif de début et de fin** |
| `memcom` | 17 042 | commissions et missions, datées |
| `memgrppol` | 3 213 | groupes politiques, datés, avec le **type** d'appartenance |
| `libgrppol` | **49** | **les libellés de groupe, bornés par `datdeb`/`datfin`** |
| `grppol` | 28 | les groupes |
| `memgrpsen` | 30 540 | groupes d'études, d'amitié, **de liaison** |
| `libgrpsen` | 115 | leurs libellés, bornés de même |
| `memextpar` | — | organismes extra-parlementaires (4 551 lignes dans `ODSEN_MEMOEP`) |

## 3. Ce qu'on gagne, et que l'Assemblée ne peut pas donner

### 3a. Le nom d'un organe à la date

Le référentiel de l'Assemblée ne porte **qu'un libellé par organe sénatorial — l'actuel** — et un code interne resté à l'ancien nom. Le code est le fossile :

| Organe AMO30 | `libelle` publié | `libelleAbrev` | Nom réel avant |
| --- | --- | --- | --- |
| `PO286005`, depuis le 11/12/2002 | Les Républicains | `UMPPO` | UMP, jusqu'au 30/05/2015 |
| `PO211490`, depuis le 31/12/1899 | Commission de la culture… **et du sport** | `AFCLC` | « affaires culturelles » jusqu'au 02/06/2009 ; « et du sport » ajouté le 12/12/2023 |
| `PO732421`, depuis le 28/06/2017 | RDPI | `LREMP` | La République en marche, jusqu'en octobre 2020 |
| `PO77707`, depuis le 02/10/1992 | CRCE - Kanaky | `CRCPO` | CRC-SPG en 2009 |

Les trois premières dates de renommage sont vérifiées **hors du dépôt** ; la quatrième l'est sur `senat.fr`, qui publie pour `jean-luc-melenchon`, au 07/01/2010, « Groupe Communiste, Républicain, Citoyen et des Sénateurs du Parti de Gauche ».

**L'Assemblée sait pourtant modéliser une réforme** — elle a clos la commission de l'économie le 20/02/2012 pour en ouvrir deux, et les délégations UE et Plan en 2008 et 2009. Elle ne modélise que ça : **19 organes sénatoriaux pour 63 ans**, contre **63** organes de groupe pour l'Assemblée, un par législature. Un renommage y est réécrit en place.

La jointure `memgrppol` × `libgrppol` sur la période qui se chevauche rend le nom à la date. Mesuré sur les deux seuls candidats déclarés concernés :

| Fiche | Période | Le nom à la date, par le Sénat | Ce que l'AN aurait publié |
| --- | --- | --- | --- |
| `jean-luc-melenchon` | 01/10/2004 – 27/11/2008 | Groupe socialiste | Socialiste, Écologiste et Républicain |
| `jean-luc-melenchon` | 28/11/2008 – 07/01/2010 | **Groupe CRC-SPG** | CRCE - Kanaky |
| `bruno-retailleau` | 01/10/2004 – 04/10/2004 | Sénateurs n'appartenant à aucun groupe | rien |
| `bruno-retailleau` | 05/10/2004 – 30/09/2011 | Réunion administrative des non-inscrits | Non inscrits |
| `bruno-retailleau` | 01/10/2011 – 06/11/2012 | Groupe UMP, **rattaché** | Les Républicains |
| `bruno-retailleau` | 07/11/2012 – 21/10/2024 | Groupe UMP, puis Les Républicains au 02/06/2015 | Les Républicains, sur toute la période |
| `bruno-retailleau` | depuis le 13/11/2025 | Groupe Les Républicains | Les Républicains |

Le libellé « Groupe CRC-SPG » commence le **28/11/2008**, jour de l'arrivée de Mélenchon, le groupe ayant été renommé pour l'accueillir. Le Sénat le date au jour près. Et les sigles historiques survivent comme **valeurs distinctes** dans `ODSEN_GENERAL` : RPR, U.R.E.I., U.C.D.P., U.N.R., R.D.E., G.D., G.D.S.R.G., CRCE **et** CRCE-K — huit noms que l'Assemblée a écrasés sous dix.

### 3b. Les dix mandats qui ne tenaient qu'à NosSénateurs

Mesuré sur `origin/main` `79719b29e` : NosSénateurs ne porte plus, seule, que **10 mandats sur 2 profils**, tous deux candidats déclarés. Les dix sont dans `data.senat.fr`, datés, et neuf y gagnent en précision — le mandat ouvert de Retailleau devient trois mandats bornés, sa commission sans date devient huit commissions datées, ses trois organismes extra-parlementaires et ses quatre groupes d'études et d'amitié sont datés avec leurs fonctions (président du groupe Haut-Karabagh **depuis le 05/04/2022**, et non « président » sans date).

Le cas le plus fuyant — **« Groupe Chrétiens d'Orient »**, absent des extraits CSV — est dans `memgrpsen` : du **04/06/2015 au 18/12/2024**, puis depuis le **29/01/2026**. C'est un **groupe de liaison** (`typgrpsencod = LIAISON`), créé le 04/06/2015, de nom complet « Chrétiens d'Orient, minorités au Moyen-Orient et Kurdes ». **Dix sur dix**, et c'est ce chiffre qui a emporté la décision.

### 3c. Dix-huit ans de carrière rendus

`jean-luc-melenchon` publie **une** entrée pour le Sénat, 2004-2010. Il a été sénateur de l'Essonne **de 1986 à 2010**. AMO30 ne descend pas avant 2001 ; `elusen` porte les trois mandats, avec leurs motifs de fin — « Membre Gouvernement » en 2000, « Élu député européen » en 2010. C'est aussi un morceau de #860 que ni AMO30 ni FranceArchives ne remplaçaient.

## 4. Ce qui reste dehors, et se déclare

- **Les scrutins.** `activite` porte 42 601 lignes et une colonne `scrid`, mais **le référentiel des scrutins n'est pas dans ce jeu**. La condition 2 du §7 reste donc non vérifiée et les deux fiches de groupe sénatorial continueront de publier `cohesion_votes: 0`. L'interface **dit** cette absence : c'est l'arbitrage du 13/09/2026.
- **Les comptes rendus des débats.** Annoncés par `data.senat.fr` dans une **autre** catégorie que « Les Sénateurs ». Non sondée : à instruire à part, pas à supposer.
- **La présence individuelle.** `activite_senateur`, **11 069 lignes** de participation nominative. §2 règle 3 l'interdit. Elle se refuse **à l'entrée de la collecte**, avec un test qui échoue si la table entre : un filtre à l'affichage laisserait la donnée dans `raw_data/`, où la fusion additive la garderait — le défaut exact que #729 décrit.

## 5. L'alternative écartée : #878

#878 proposait de publier les **291 mandats sénatoriaux** qu'AMO30 porte sur **33 profils** (31 membres de roster, 2 candidats déclarés), ventilés 111 `COMSENAT`, 72 `SENAT`, 59 `GROUPESENAT`, 49 `DELEGSENAT`. Trois de ses quatre pièces restaient vraies ; sa **source** était la mauvaise (§3a). Trois options avaient été rendues en maquette — tout publier tel que l'AN le nomme, publier le siège sans le nom des organes, ou relire une table de renommage à la main — et la quatrième, qui les périme, est que **le Sénat publie déjà cette table**.

**Deux mesures de #878 doivent lui survivre**, parce qu'elles ont corrigé son propre lot :

1. **Le « doublon hérité » fait 2 entrées, pas 9.** Sur les 84 mandats sans `categorie_source` des 33 profils, seules **2** ont un équivalent AN — les `mandat_electif` `chambre: "Senat"` de Retailleau et de Mélenchon. Les **8 entrées sans date** de Retailleau n'ont **aucun** équivalent dans AMO30 : les retirer aurait vidé sa fiche. C'est `data.senat.fr` qui les date.
2. **La preuve de couverture** est déjà corrigée par [`borne-mandats-acteur-nest-pas-depute`](borne-mandats-acteur-nest-pas-depute.md).

**Rien n'a été écrit sous `src/` pour #878** : la branche est restée vide, la mesure ayant précédé le code et l'ayant interdit.

## 6. Ce que ça ne résout pas

- **Rien avant 2002 pour les mandats de député.** `ODSEN_ELUDEP` publie les mandats de député **des sénateurs**, ce qui ne couvre ni Royal, ni Dupont-Aignan, ni Cazeneuve. La table relue à la main de #860 reste nécessaire.
- **La clause ODbL ne tombe pas.** Sortir de NosSénateurs n'est pas sortir de NosDéputés : **474 profils** portent un marqueur `sources[].type == "nosdeputes"` (465 membres de roster, 9 candidats déclarés) contre **2** pour `nossenateurs` (2 candidats déclarés), sur **1 196 profils publiés**. Décision éditoriale distincte, laissée à la propriétaire (#839 lot C).
- **La teinte du Sénat.** `web/UI_finale/DESIGN_SYSTEM.md` réserve la sarcelle `#169E9E` « pour le jour où sa collecte sera rebranchée » et lui donne `#9A958D`, « l'encre des absences ». Ce jour arrive **à moitié** : les appartenances sont publiées, l'activité non. Arbitrage de direction artistique, à trancher avec la session interface.
