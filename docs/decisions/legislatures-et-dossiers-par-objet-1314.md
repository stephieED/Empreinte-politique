<a id="legislatures-et-dossiers-par-objet-1314"></a>
# La fiche d'une législature lit des fichiers par objet, jamais un fichier par législature (#1314, 2026-10-22)

`2026-10-22`

> **En bref** — La fiche d'une législature (#1314) demandait un fichier par législature. Arbitré le 22/10/2026 : un fichier **par objet**, que la fiche filtre et joint par l'uid du dossier. `pivot_data/legislatures.json` porte les bornes, le mode de fin (lu au Journal officiel), le terme prévu (art. LO 121) et les groupes avec leur siège médian ; `pivot_data/dossiers_an/<législature>.json` une ligne par dossier — titre, nature, dépôt, auteurs avec leur qualité et leur groupe au jour du dépôt, sort, étape à l'Assemblée par législature, scrutins, 49.3. Rien de ce que publient déjà `commissions_dossiers.json` et `textes_promulgues.json` n'y est recopié.

## Contexte mesuré

La session interface a remonté le 22/10/2026 le besoin de cinq sections (En bref,
Qui siégeait, Les textes de la législature, Le travail des commissions, Ce qu'on
n'a pas pu lire). Mesuré le même jour sur les quatre archives de dossiers
(XIV à XVII) et l'archive AMO30 courante du 19/10/2026 :

| Mesure | Valeur |
| --- | --- |
| dossiers des archives, dédoublonnés par uid | **14 377** (dont 19 des législatures VIII à XIII, traîne des archives) |
| actes dont l'uid porte la législature (`L16-…`) | **119 431** sur 119 444 |
| références d'auteur (`initiateur.acteurs`) dont le `mandatRef` se résout dans AMO30 | **23 948** sur 23 955 |
| types de ces mandats | `SENAT` 11 874, `ASSEMBLEE` 9 878, `MINISTERE` 2 184, `PRESREP` 12 |
| dossiers sans bloc `initiateur` | 1 580 |
| dossiers dont l'initiateur n'est qu'un organe | 502 |
| un seul fichier, tous dossiers | 16,6 Mo (1,6 Mo compressé) |

Par fichier publié (un dossier paraît dans le fichier de sa législature et dans
celui de chaque législature où l'Assemblée a agi sur lui) :

| Fichier | Dossiers | dont de la législature | Taille | Étape dans la législature : déposé / examiné en commission / débattu en séance / aucun acte AN |
| --- | ---: | ---: | ---: | --- |
| `14.json` | 3 452 | 3 433 | 3,0 Mo | 2 536 / 47 / 660 / 209 |
| `15.json` | 5 068 | 4 982 | 4,8 Mo | 3 511 / 107 / 613 / 837 |
| `16.json` | 2 931 | 2 794 | 3,0 Mo | 2 082 / 99 / 301 / 449 |
| `17.json` | 3 333 | 3 149 | 3,5 Mo | 2 302 / 162 / 363 / 506 |

252 dossiers paraissent dans plus d'un fichier. Recoupé avec la mesure faite hors
dépôt par l'interface sur les 1 506 dossiers XVIe de `commissions_dossiers.json` :
1 233 jamais examinés, 55 examinés, 218 débattus selon elle ; 1 235 (dont 15 sans
aucun acte AN en XVIe, des textes du Sénat transmis en XVIIe), 53 et **218** ici.
L'écart de deux vient de la règle : la législature est celle de l'**acte**, et deux
réunions de commission ont eu lieu en XVIIe.

Pour les législatures, l'organe `ASSEMBLEE` d'AMO30 donne : XIVe 2012-06-20 →
2017-06-20, XVe 2017-06-21 → 2022-06-21, XVIe 2022-06-22 → 2024-06-09, XVIIe
depuis 2024-07-01. Le décret de dissolution du 9 juin 2024
(`JORFTEXT000049689651`) est dans `pivot_data/actes_reglementaires/2024-06.json`.

## Décision

**Un fichier par objet (option B).** La fiche d'une législature lit
`legislatures.json`, le fichier `dossiers_an/<n>.json` de sa législature, et joint
`commissions_dossiers.json` (la commission au fond, #1311) et
`textes_promulgues.json` (la promulgation) par l'uid du dossier. Une seule valeur
existe en deux endroits : `derniere_adoption_an`, calculée pour **tous** les
dossiers par la fonction de #1320, qui ne la publiait que pour les lois — un texte
adopté par l'Assemblée et pas encore loi n'avait nulle part où la porter. Les deux
sont écrites par le même run, par la même fonction.

**Dans `dossiers_an/`** :

- l'étape à l'Assemblée est **par législature**, lue dans l'uid de chaque acte,
  jamais en comparant une date à des bornes : `depose`, `examine_en_commission`
  (réunion ou rapport, règle de #997), `debattu_en_seance`. Un texte resté au
  Sénat a un `etape_an` vide ;
- la **qualité** d'un auteur vient du mandat que le dossier cite (`mandatRef`),
  jamais du préfixe du texte (`PIONAN`, faux pour 30 des 218 textes relus par
  l'interface) ; son **groupe** est le mandat `GP` ou `GROUPESENAT` ouvert le jour
  du dépôt. Un membre du gouvernement n'a pas de groupe, et le motif
  `qualite_sans_groupe` le dit ;
- les noms une fois par fichier (`acteurs`, `organes`), les lignes par référence ;
- les scrutins sont ceux que la source rattache au dossier (`voteRefs`), jamais
  ceux qu'un rapprochement de date et de titre lui prête. Un vote solennel se lit
  dans le `type_scrutin` du corpus ; un scrutin cité et absent du corpus est
  déclaré, jamais rangé « pas solennel » ;
- un 49.3 est un fait de procédure (§2 règle 4) : `engagements_49_3` ne porte
  aucune référence de scrutin.

**Dans `legislatures.json`** :

- les bornes de l'organe, verbatim ;
- le mode de fin **lu** : `dissolution` quand un décret « portant dissolution de
  l'Assemblée nationale » paraît dans les sept jours qui suivent la fin, `terme`
  quand la fin est le terme légal, sinon `null` avec `en_cours` ou
  `fin_non_expliquee` ;
- le terme prévu par l'art. LO 121 du Code électoral (troisième mardi de juin de la
  cinquième année qui suit l'élection), règle publiée à côté. Vérifiée sur les deux
  fins au terme publiées par l'organe ;
- pour chaque groupe, la médiane des sièges de ses membres au jour de référence
  (fin de la législature, ou date de l'archive en cours), lus dans l'archive de la
  législature (#1317). Le fichier publie la médiane ; l'interface choisit le sens.
  La XIVe n'a pas d'archive (404) : ses groupes sont publiés sans siège.

Calculé ainsi, l'ordre XVIe de la gauche vers la droite de l'hémicycle est
LFI-NUPES (602), GDR-NUPES (586,5), SOC-A (509), ECOLO (503), RE, NI, DEM, LIOT,
HOR, LR, RN : celui que la maquette de l'interface avait trouvé à la main.

## Alternative écartée

**Un fichier par législature (option A)**, celui que l'interface proposait. Il
recopiait la commission, l'adoption et la promulgation de chaque dossier : deux
copies d'une même donnée finissent par diverger, et la seconde se corrige sans
la première. Il ne servait qu'à une fiche, quand le titre et l'auteur d'un
dossier servent aussi aux fiches de groupe et de gouvernement.

**Un seul fichier de dossiers.** 16,6 Mo à charger pour une fiche qui en lit un
quart.

**Lire l'ordre des groupes dans les profils publiés.** Les ~600 profils d'une
législature portent déjà leur place (#1317), mais seulement pour les membres des
groupes qui ont une fiche. AMO30 donne tous les députés.

## Ce qui n'a pas été vérifié

- **L'article LO 121 n'a pas été relu en ligne** : Légifrance refuse les requêtes
  non interactives. La règle vient du texte connu, et elle redonne exactement les
  deux fins au terme (20/06/2017, 21/06/2022). Le lien publié va au Code électoral,
  pas à l'article, dont l'identifiant n'a pas pu être relu.
- **Le nom d'un groupe du Sénat est son nom actuel** : AMO30 ne publie qu'un
  libellé par organe, et le groupe `PO286005` s'appelle « Les Républicains » depuis
  2002. Un sénateur UMP de 2012 paraît sous ce nom.
- Les 48 auteurs sans qualité (dont 20 dans le fichier XVIe) n'ont pas été relus un
  par un ; leur motif est `mandat_introuvable`.
- La copie des deux fichiers vers le site (`web/UI_finale/scripts/sync-data.mjs`)
  est à faire côté interface.
