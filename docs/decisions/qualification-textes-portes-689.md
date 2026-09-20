<a id="qualification-textes-portes-689"></a>
# Un projet de loi porté au nom du Gouvernement n'est pas une production personnelle (#689) (2026-09-01)

`2026-09-01`

> **En bref** — `textes_portes[]` publiait sous un unique `role: "auteur"` la **proposition de loi** qu'un·e parlementaire dépose ET le **projet de loi** qu'un membre du Gouvernement porte au nom de l'exécutif : mesuré à `e40d0d32`, **316 des 472 entrées publiées** sont des projets de loi, dont **282 des 283 d'`edouard-philippe`** (toutes déposées pendant qu'il était Premier ministre) et **30 des 34 de `gabriel-attal`**, si bien que 283 et 5 se lisaient sous le même nom sans mesurer la même chose ; le croisement date de dépôt × mandats électifs, qui a servi à découvrir le défaut (**304 / 423** chez les 13 candidats déclarés), est un **contrôle et jamais une source** — il manque les 8 textes qu'Attal a portés comme ministre en étant encore député et le seul projet de loi de `bruno-retailleau`, ministre tout en restant sénateur, et il dirait « hors mandat » là où il faut dire « porté au nom du Gouvernement » ; un discriminant tiré du **libellé** est écarté pour la même raison qu'en #672 — les dossiers de la XVe s'intitulent « Bioéthique », « CETA », « Coopération avec le Luxembourg » et un filtre « commence par *Projet de loi* » en manque **283 sur 304** ; la nature se lit donc dans le champ que le dépôt lisait **déjà** pour les fiches de gouvernement (#435/#400), le préfixe de l'uid du document du premier acte de dépôt, promu en `gouvernement_textes.nature_texte_depose` (`PRJL`/`PION`/`PNRE`) dont `_origine` **dérive** désormais au lieu de relire l'archive (verdict identique sur les 10 674 dossiers des trois archives, vérifié dossier à dossier) ; le pivot gagne **`nature_texte`**, le fait sourcé, et **`role` est scindé** en `initiateur_projet_de_loi` / `auteur_proposition_de_loi` / `auteur_proposition_de_resolution`, parce qu'un champ voisin qu'il faut penser à lire n'empêche personne de confondre les deux natures *par défaut* — `auteur` survit et sa définition **rétrécit** aux 5 entrées d'initiateur dont la source n'établit pas la nature (missions d'information, commissions d'enquête, déclaration du Gouvernement), et `validate_profil` refuse toute **contradiction** entre les deux champs, ce qui rend la redondance sûre au lieu d'en faire une seconde vérité (invariant de `chambre`/`chambres[0]`, #493) ; le rôle est **dérivé, jamais fusionné**, et la nature traverse la fusion additive par `backfill_dossier_nature` — sans lui l'entrée ancienne gagne et le brut n'acquiert **jamais** le champ, le trou de #639 et de #492 au même endroit : un filtre posé avant la fusion additive ne filtre rien ; le cache disque passe en `index_acteur_textes_v3.json`, l'existence d'un index n'étant pas la preuve de sa conformité (#440, #639) ; garde-fou **§5c du portail de qualité, soft** — effectifs par rôle, projets de loi portés au nom du Gouvernement, et compteur d'attente qui vaut **451 / 472 au 01/09/2026** parce que la qualification n'atteint une fiche qu'au run réel qui la recollecte (bloquer interdirait les runs censés la propager, #447/#450), avec sa condition de retrait écrite ; **aucune perte à déclarer** — `nature_texte` est un ajout et un changement de valeur de scalaire n'est pas bloquant pour `audit_diff_profils` ; le repli par intitulé de `web/UI_finale` (`estProjetDeLoi`) survit **déclaré**, derrière `nature_texte`, faute de quoi la page afficherait 0 projet de loi là où elle en signale 13.

**Défaut en ligne.** `textes_portes[]` publiait sous un unique `role: "auteur"`
deux actes de nature différente : la **proposition de loi** qu'un·e
parlementaire dépose, et le **projet de loi** qu'un membre du Gouvernement porte
au nom de l'exécutif. Le second n'est pas un acte personnel — il engage un
gouvernement, et un bilan de gouvernement est collectif.

## Mesure de référence

Prise le 01/09/2026 sur `origin/main` (`e40d0d32`), en flux sur les 481 profils
pivot committés, croisée avec les trois archives de dossiers législatifs
(XV/XVI/XVII, 10 674 dossiers).

`textes_portes[]` publiés : **472** entrées sur les 481 profils — 423 chez les
13 candidats déclarés, 49 chez les 468 membres de roster. Ventilation
`role` × nature du texte déposé, corpus entier :

| | `projet_de_loi` | `proposition_de_loi` | `proposition_de_resolution` | nature non établie |
| --- | ---: | ---: | ---: | ---: |
| `auteur` (initiateur) | **316** | 100 | 30 | 5 |
| `rapporteur` | 2 | 3 | 1 | 0 |
| `co-rapporteur` | 8 | 1 | 0 | 6 |

Les 472 `dossier_id` publiés résolvent tous dans les trois archives : **0**
entrée non retrouvée.

Chez les 13 candidats déclarés : **313** projets de loi sur 423 entrées, portés
par trois profils — `edouard-philippe` **282** (sur 283 ; le 283ᵉ est un
engagement de responsabilité, sans nature), `gabriel-attal` **30** (sur 34),
`bruno-retailleau` **1** (sur 36). Sept profils sur treize publient des textes
portés ; **trois portent la totalité de l'anomalie**.

## Le contrôle qui a servi à découvrir le défaut n'est pas la source

Croiser la date de dépôt avec les mandats électifs donne **304 / 423** textes
déposés hors de tout mandat — la mesure de l'issue, reproduite à l'identique.
Elle est un **contrôle**, jamais une source :

| | Croisement date × mandats | Nature lue dans la source |
| --- | ---: | ---: |
| `edouard-philippe` | 282 | 282 |
| `gabriel-attal` | 22 | **30** |
| `bruno-retailleau` | 0 | **1** |
| Total candidats déclarés | 304 | **313** |

Le croisement manque les 8 textes qu'Attal a portés comme ministre alors qu'il
était encore député, et **le seul projet de loi de Retailleau** — ministre de
l'Intérieur tout en restant sénateur. Il dirait « hors mandat » là où il faut
dire « porté au nom du Gouvernement » : deux énoncés différents.

## Ce qui a été rejeté : un discriminant tiré du libellé

Chercher les intitulés commençant par « Projet de loi » trouve 13 textes chez
Attal et **zéro chez Philippe**. Les dossiers de la XVᵉ portent des intitulés
courts et descriptifs — « Bioéthique », « CETA », « Coopération avec le
Luxembourg ». **Un discriminant tiré du libellé en manque 283 sur 304.** C'est
ce que `selection-vote-sur-ensemble-672` vient de corriger ailleurs : une clé
dérivée d'un libellé rouille, et se tait en rouillant.

## Décision 1 — la nature vient du document déposé, et une seule fonction la lit

`gouvernement_textes.nature_texte_depose(dossier)` rend `projet_de_loi` /
`proposition_de_loi` / `proposition_de_resolution` / `None`, depuis le préfixe
de l'uid du document associé à l'acte `*-DEPOT` le plus ancien
(`PRJL`/`PION`/`PNRE`) — le type que l'AN encode elle-même. Repli sur
`procedureParlementaire.code` **seulement** quand aucun document n'est
résolvable, et seulement pour les codes univoques (les codes 5 et 7, « Projet
**ou** proposition de loi organique/constitutionnelle », restent exclus : #400).

C'est le champ que le dépôt lisait **déjà** pour les fiches de gouvernement
(`gouvernement-textes-initiateurs`, #435, et `_origine` depuis #400) et que
`candidate_profile._build_acteur_textes_portes_index` jetait à la collecte.
L'information n'était pas perdue à la source.

**`_origine` en dérive désormais** au lieu de relire l'archive : deux lectures
du même champ auraient fini par diverger. Le verdict est identique sur les
10 674 dossiers des trois archives, vérifié dossier à dossier avant/après. Une
proposition de résolution reste `None` côté origine — elle n'est pas un texte de
loi — mais gagne une valeur propre côté nature, où la distinction compte : une
résolution est une initiative parlementaire personnelle, et la confondre avec
« nature non établie » perdrait 31 des 472 entrées.

## Décision 2 — deux champs, dont un dérivé, qui ne peuvent pas se contredire

`textes_portes[]` gagne **`nature_texte`** (le fait sourcé) et **`role` est
scindé** (le fait dérivé) :

| Nature | `role` publié |
| --- | --- |
| `projet_de_loi` | `initiateur_projet_de_loi` |
| `proposition_de_loi` | `auteur_proposition_de_loi` |
| `proposition_de_resolution` | `auteur_proposition_de_resolution` |
| `null` | `auteur` |
| — (rôle de rapport) | `rapporteur`, `co-rapporteur`, inchangés |

**Le rôle devait changer de nom, et pas seulement gagner un champ voisin.** Un
consommateur qui lit `role` doit cesser de confondre les deux natures *par
défaut* ; un champ supplémentaire qu'il faut penser à lire ne l'y oblige pas.
`auteur` survit et sa définition **rétrécit** : « initiateur déclaré par la
source sur un dossier dont elle n'établit pas la nature » — 5 entrées publiées
(missions d'information, commissions d'enquête, déclaration du Gouvernement,
engagement de responsabilité). Il ne peut plus désigner un projet de loi.

Le rôle est **dérivé**, jamais collecté et jamais fusionné — patron de `chambres`
(#493) et de `meta.licence_donnees` (#530). Et `validate_profil` refuse toute
contradiction entre les deux champs : c'est ce qui rend la redondance sûre au
lieu d'en faire une seconde vérité, exactement comme `chambre` ne peut pas
contredire `chambres[0]`.

**Alternative rejetée — `nature_texte` seul, `role` inchangé.** Elle laisse
`auteur` couvrir les deux natures : la confusion persiste pour qui ne lit pas le
nouveau champ, c'est-à-dire pour tout consommateur écrit avant aujourd'hui.


## Décision 3 — le libellé affiché nomme l'initiative, pas le terme juridique

Le nom technique du rôle ne pouvait pas devenir le nom affiché. Le vocabulaire
officiel est **contre-intuitif** : « projet » et « proposition » ne disent pas
ce qu'on propose mais **qui dépose**, et un lecteur qui ne connaît pas
l'article 39 lit exactement l'inverse. « Résolution » est pire encore — il se
lit comme une partie de loi, alors qu'une résolution ne crée aucune règle. La
propriétaire du dépôt, qui connaît le corpus, a fait les deux contresens en
séance : c'est la mesure qui a décidé.

| `role` | Libellé de `LIBELLE_ROLE_TEXTE` |
| --- | --- |
| `initiateur_projet_de_loi` | Projet de loi à l'initiative du gouvernement |
| `auteur_proposition_de_loi` | Proposition de loi issue d'un(e) parlementaire |
| `auteur_proposition_de_resolution` | Résolution (prise de position ou demande procédurale) |

**Le libellé nomme l'initiative, jamais la chambre de dépôt.** « Issue de
l'Assemblée nationale » avait été envisagé, et la mesure l'écarte : sur les 423
textes portés des 13 candidats déclarés, **122 des 313 projets de loi ont été
déposés au Sénat** sans cesser d'être des textes du gouvernement — c'est le
gouvernement qui choisit la chambre saisie en premier — et **35 des 78
propositions sont sénatoriales** (les 35 de `bruno-retailleau`, sénateur de la
Vendée). Le libellé aurait été faux **157 fois sur 391**.

**La parenthèse de la résolution énumère, elle ne tranche pas.** La source
distingue elle-même deux procédures sur les 26 résolutions publiées, par
`procedureParlementaire.code` : **10** en code 22 (« Résolution Article 34-1 »,
l'Assemblée déclare une position) et **16** en code 8, un libellé générique
dont les intitulés sont des demandes d'enquête. Une prise de position et une
demande de commission d'enquête n'ont pas le même effet ; « prise de position »
seul aurait été faux 16 fois sur 26. Reclasser les 16 depuis leur intitulé est
exclu — c'est la faute que la §1 de cette décision documente (#672).

**« Demande » et non « décision » :** 2 des 26 seulement portent le stade
`adopte` (5 au dépôt, 3 discutées en séance, 16 examinées en commission). Un
texte déposé sans être voté n'a rien décidé, et l'affirmer violerait §2 règle 5.

Trois tests lisent le fichier d'interface exécuté : tout rôle de
`KNOWN_ROLES_TEXTE` a un libellé et réciproquement (le module l'affirmait en
commentaire, rien ne le vérifiait), aucun des deux libellés d'initiative ne
nomme de chambre, et celui de la résolution ne porte pas le mot « décision ».
Le dépôt n'ayant pas de harnais JS, le garde-fou est en Python et **lit** le
fichier au lieu d'en recopier les valeurs.

**Alternative rejetée — scinder `role` sans publier `nature_texte`.** Un seul
champ, aucune redondance, mais deux faits de nature différente soudés dans une
valeur (ce que la personne a fait × ce qu'est le texte), et les 21 entrées de
rapport privées d'une nature que la même lecture rend gratuitement. C'est aussi
le champ dérivé qui deviendrait la seule trace du fait sourcé.

## Décision 3 — la qualification doit traverser la fusion additive

`merge_raw_profile` fusionne `dossiers_legislatifs[]` en additif pur : l'entrée
ancienne gagne. Un champ ajouté à la collecte n'aurait **jamais** atteint les
423 textes déjà collectés, et `normalize_profil` aurait republié `role:
"auteur"` indéfiniment sans qu'aucune étape n'échoue. C'est le trou de #639
(`backfill_vote_qualification`) et celui de #492 (`backfill_mandat_chambre`), au
même endroit et pour la même raison : **un filtre posé avant la fusion additive
ne filtre rien.**

`merge_profile.backfill_dossier_nature` reporte donc `nature_texte` d'une entrée
neuve sur l'entrée ancienne de même clé. Strictement croissant en information :
un seul champ nommé, jamais d'écrasement, jamais de création d'entrée, et
`_dossier_key` **inchangée** — c'est ce qui distingue ce report du défaut de
#668, où c'est la clé elle-même qui avait changé de branche.

## Décision 4 — le cache disque passe en `v3`

`index_acteur_textes_v2.json` ne porte pas `nature_texte`. Le relire
republierait « auteur » sur les 316 projets de loi du corpus, sans qu'aucune
étape n'échoue : **l'existence d'un cache n'est pas la preuve de sa
conformité**, même règle que pour le cache d'amendements (#440) et celui des
scrutins (#639).

## Décision 5 — un garde-fou qui lit le corpus publié, et qui est soft

§5c du portail de qualité : effectifs par rôle, nombre de projets de loi portés
au nom du Gouvernement, et **nombre d'initiateurs sans nature établie** — le
mètre de migration, sur le patron du warning « chambres non corroborée » de
#493. Chaque compte nomme sa population (#630), et aucun ratio n'est calculé
(§2 règle 1).

**Soft, délibérément.** La qualification n'atteint un profil qu'au run réel qui
recollecte ses dossiers législatifs ; bloquer le commit interdirait précisément
les runs censés la propager — le raisonnement de #447, cause #450. Condition de
retrait écrite : la §5c se retire quand le compteur d'attente tombe à 0 et n'y
laisse que les entrées dont la source n'établit pas la nature.

## Ce que ce lot ne fait pas

- **Aucune fiche publiée n'est requalifiée.** Au 01/09/2026 le corpus porte
  **451 initiateurs sans nature sur 472 entrées** : la §5c le dit à chaque
  exécution. Il faut un run réel de collecte des dossiers législatifs.
- **Aucune perte à déclarer.** La correction n'enlève aucune entrée, ne vide
  aucune liste et ne fait régresser aucun scalaire surveillé : `nature_texte`
  est un ajout, et `role` change de valeur — `audit_diff_profils` signale un
  changement de valeur de scalaire sans bloquer. `allow_declared_losses` n'a
  donc pas à être armé.
- **Le repli par intitulé de `web/UI_finale` survit, déclaré.** `estProjetDeLoi`
  lit `nature_texte` dès qu'il est présent, et retombe sur l'expression
  régulière sinon : le retirer aujourd'hui afficherait 0 projet de loi là où la
  page en signale 13. Sa condition de retrait est celle de la §5c.
- **Les 8 dossiers de règlement du budget** typés « Proposition de loi
  ordinaire » à la source alors que leur document est un `PRJL` (#400) restent
  arbitrés en faveur du document. Inchangé.
