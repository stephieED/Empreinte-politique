<a id="vivier-de-points-et-empreinte-de-commission-328"></a>
# « L'essentiel » : un vivier de points garanti par rôle, et une empreinte de commission sourcée (#328, 01/09/2026)

`2026-09-01`

> **En bref** — cinq décisions de la propriétaire sur le bloc d'ouverture livré par #694, dont trois changent ce que la page mesure ; le bloc s'appelle **« L'essentiel »** (« Coup d'œil » promettait de la rapidité, pas du contenu) partout sauf dans `READING_LEVELS`, où « coup d'œil » nomme un des **trois niveaux de lecture** de #326 et non cette section ; les deux moitiés de la phrase d'introduction partagent désormais **une seule classe** (19 px / 500) parce que ce sont les deux termes d'une **opposition** — 17 px gris contre 22 px blanc gras faisait lire la première comme la légende de la seconde —, l'accent portant sur les **deux mots opposés** (*réaction* / *initiative*) et jamais sur une ligne, jamais en jaune signal ; les cinq points sont tirés d'un **vivier de sept** avec **au moins un point par rôle réellement tenu** (option C ; A n'empêche pas le volume d'un rôle d'écraser l'autre, B double la longueur de la section — 283 textes portés chez `edouard-philippe`), le rôle se lisant sur un fait collecté — être **membre** d'un gouvernement, **6 des 13 candidats déclarés**, un parlementaire *en mission* n'en étant pas un — et le rôle de chaque point aussi : les **6 651** dépôts comme auteur principal des 13 portent `type_deposant` `depute` ou `commission_rapporteur` et **jamais** `gouvernement`, aucun ne tombant dans une période d'appartenance gouvernementale ; la **réparation principale** est la scission de « textes portés » par `nature_texte` (#689, renseignée sur **418 des 423**), qui faisait lire les 34 textes de `gabriel-attal` comme 34 actes personnels quand 30 sont des projets de loi du gouvernement — et `institutionDuTexte` lit **`role` avant la nature**, parce qu'il est *rapporteur* d'un projet de loi, un acte parlementaire sur un texte du gouvernement ; **trois états, pas deux** : 4 des 423 ne sont attribués à aucune institution ; la garantie **ne fabrique rien** — un rôle tenu que le vivier ne documente pas se DIT (`laurent-wauquiez`, `segolene-royal`, `xavier-bertrand`) — et **ne déplace aucun point sur les 13 profils publiés aujourd'hui**, ce qui est mesuré et écrit plutôt que tu ; le point « amendements » publie un **couple** regroupé par `dossier_id` — « 25 dossiers législatifs amendés · 2 405 amendements déposés sur eux » — parce que le compte brut mesure la participation à un épisode de dépôt en masse (574 des 2 429 dépôts de `jerome-guedj` sur le seul PLFRSS 2023, médiane de 2,5 à 8 dépôts par dossier sur les quatre profils qui en portent plus de 50), que filtrer sur les adoptés mesure le terrain et repose sur un `sort` **inconnu sur 1 822 de ces 2 831**, et que les `texte_vise` sont des **lectures** (47 chez `jerome-guedj` pour **25** dossiers) ; la clé `dossier_id || texte_vise` publiait « 34 dossiers » là où il y en a 25, le défaut `a or b` de #668 ; l'empreinte thématique est la **commission saisie au fond**, lue sur l'acte `AN1-COM-FOND-SAISIE` des archives AN et résolue par le référentiel des organes — **6 024** dossiers, **0** saisie sans `organeRef`, **0** organe non résolu, **0** divergence entre saisies d'un même dossier —, publiée dans le nouveau `pivot_data/commissions_dossiers.json` et **jamais déduite d'un intitulé**, ce qui serait une classification construite ici (§2 règle 1) ; **aucun seuil** ne décide qu'il y a une tendance : `laurent-wauquiez` a 4 et 4 en tête, c'est la donnée qui n'en produit pas, et la barre le montre en ne montrant rien ; **« Dossiers examinés par », jamais « travaille sur »** (« Lois » couvre l'immigration, la justice et les institutions) ; la **borne se déclare** — chez `jean-luc-melenchon` la répartition repose sur 332 de ses 2 831 dépôts, cause #696, déclarée et non corrigée ici ; le rendu **s'adapte au cas** (barre pour les commissions, podium pour les mandats en commission, liste pour les textes, texte pour un vocabulaire ouvert de 417 points d'ordre du jour), **un seul ton** pour les segments à égalité et **aucun jaune signal** dans la section ; non vérifié et nommé : aucun test n'exécute de JavaScript, le rendu SSR réel des 13 profils ne couvre ni mise en page, ni responsive, ni contraste, ni clavier, et la table des commissions n'apparaîtra qu'au premier run de `merge-and-pivot`.

**Contexte.** Le bloc d'ouverture de la fiche candidat, livré par #694 sous le
titre « Coup d'œil », a été relu par la propriétaire. Cinq décisions en sont
sorties. Deux tiennent en une ligne (le titre, la typographie de la phrase
d'introduction) ; trois changent ce que la page mesure.

Le constat qui a déclenché le lot porte sur `gabriel-attal` : *« les 5 points
marquants d'Attal ont l'air d'être en tant que ministre de l'éducation mais ça a
l'air de minimiser sa carrière »*.

---

## 1. La section s'appelle « L'essentiel »

« Coup d'œil » promettait de la **rapidité**, pas du **contenu**. Le nom est
remplacé partout — libellé publié, classes CSS (`.cp-essentiel*`), export du
module (`essentiel`), clé de la vue (`candidate.essentiel`), tests.

**Une exception, délibérée** : `READING_LEVELS` dans `utils/lecture.js` garde son
premier niveau « Coup d'œil ». Ce n'est pas cette section — c'est le vocabulaire
des **trois niveaux de lecture** de #326 (coup d'œil / lecture / vérification),
et le renommer y redéfinirait un concept du lot 1 sans qu'aucune décision le
demande. Il n'est monté par aucune page aujourd'hui (`NiveauxLecture` est exporté
et jamais instancié).

## 2. Les deux moitiés de la phrase d'introduction ont même poids

> Un vote : une **réaction** à l'ordre du jour d'autrui.
> Un amendement déposé, une commission rejointe, une question posée : à
> l'**initiative** de la personne.

La première ligne était rendue en 17 px / 500 gris, la seconde en 22 px / 800
blanc. Ce sont les **deux termes d'une opposition** : accentuer la seconde seule
faisait lire la première comme sa légende. C'était un défaut de la spécification,
pas du rendu.

Les deux lignes partagent désormais **une seule classe** (`.cp-these-ligne`,
19 px / 500) — deux classes divergent au premier ajustement. L'accent porte sur
les **deux mots opposés**, `réaction` et `initiative`, en graisse 800 et en
blanc plein. Jamais de jaune signal : `DESIGN_SYSTEM` §3 le réserve à la
sélection, à l'action et à la source vérifiée.

## 3. Les cinq points sont choisis dans un vivier, avec une garantie par rôle

### Le défaut est structurel

Les cinq points étaient cinq **catégories fixes** — interventions, amendements,
commissions, questions, textes — qui décrivent le métier d'un⋅e député⋅e. Chez
un⋅e ancien⋅ne ministre, elles se remplissent surtout de ce que son ministère a
produit :

| `gabriel-attal`, avant | Ce que le lecteur lisait |
| --- | --- |
| 34 « textes portés », dont 31 projets de loi | 34 textes personnels, corrigés par une note en bas de point |
| 743 « questions au gouvernement » | des questions posées, alors qu'elles lui étaient posées |
| 49 amendements, 67 mandats en commission | des résidus, à côté des deux précédents |

### L'option retenue est C

Trois options ont été pesées :

| Option | Coût |
| --- | --- |
| **A** — un bloc de 5, chaque point étiqueté de son rôle | n'empêche pas le volume d'un rôle d'écraser l'autre |
| **B** — un bloc par rôle | la section double de longueur ; illisible pour `edouard-philippe` (283 textes portés) |
| **C** — un vivier, garantie d'au moins un point par rôle tenu | **retenue** |

### Le rôle se lit sur un fait collecté, jamais sur une catégorie éditoriale

- **`gouvernement` est tenu** si la personne a été **membre** d'un gouvernement
  (`appartenancesGouvernementales`). Mesuré au SHA `f635cb60`, 01/09/2026 :
  **6 des 13 candidats déclarés** — Bruno Retailleau, Édouard Philippe, Gabriel
  Attal, Laurent Wauquiez, Ségolène Royal, Xavier Bertrand. Un⋅e parlementaire
  **en mission** auprès d'un ministère n'en est pas membre : c'est ce qui écarte
  correctement les 2 mandats « en mission » de `jerome-guedj`.
- **`parlement` est tenu** dès qu'un point du vivier en relève.

### Et le rôle de chaque point aussi

| Point | Rôle | Le fait qui le décide |
| --- | --- | --- |
| `interventions` | banc mesuré | qualité publiée par la source **et** date dans une période de gouvernement, à la majorité (`depuisLeBancDuGouvernement`) |
| `amendements` | parlement | les **6 651** dépôts comme auteur principal des 13 candidats déclarés portent `type_deposant` `depute` (6 645) ou `commission_rapporteur` (6), **jamais** `gouvernement`, et **aucun** ne tombe dans une période d'appartenance gouvernementale |
| `commissions` | parlement | un siège en commission est un mandat parlementaire, rangé sous `mandats` par la source |
| `questions` | banc mesuré | même règle à deux conditions, déjà en place depuis #684 |
| `textes_gouvernement` / `textes_parlement` | **scindés** | `role` d'abord, `nature_texte` (#689) ensuite |
| `qualite` | **aucun** | il compte les qualités d'orateur des deux bancs confondus |

**La scission des textes portés est la réparation principale.** Elle n'est
possible que depuis #689 : `nature_texte` est renseignée sur **418 des 423**
textes portés des 13 candidats déclarés (314 `projet_de_loi`, 78
`proposition_de_loi`, 26 `proposition_de_resolution`, 5 `null`), là où elle
valait `None` partout avant le run `33514676506`.

**Deux champs, pas un.** Gabriel Attal est **rapporteur** d'un projet de loi —
un acte parlementaire sur un texte du gouvernement. Le ranger au gouvernement
sur sa seule nature serait le contresens exact que #689 a corrigé dans l'autre
sens. `institutionDuTexte` lit donc `role` avant `nature_texte`, et
`estProjetDeLoi` répond à une **autre** question (de quelle nature est ce texte)
en restant indifférent au rôle : les deux ne se confondent pas.

**Trois états, pas deux.** Quand ni le rôle ni la nature ne tranchent — 4 des
423, tous `role: auteur` sans nature —, le texte n'est attribué à **aucune**
institution et le compte est publié dans le socle du point. Ranger par défaut au
parlement inventerait une initiative personnelle (§2 règle 5).

### La garantie, et ce qu'elle ne fait pas

`selectionnerPoints(vivier, rolesTenus)` réserve, pour chaque rôle tenu, la place
du **premier** point du vivier qui en relève, **avant** de remplir les places
restantes dans l'ordre. La sélection est ensuite **remise dans l'ordre du
vivier** : la garantie change *qui* est retenu, jamais l'ordre de lecture.

- **Elle ne fabrique rien.** Un rôle tenu dont le vivier ne porte aucun point ne
  reçoit pas de place : la page l'**écrit** (`rolesSansPoint` → « Aucun de ces
  points ne documente son passage au gouvernement : les listes que cette section
  compte y sont vides »). Trois profils sont dans ce cas : `laurent-wauquiez`,
  `segolene-royal`, `xavier-bertrand`.
- **Elle vaut identiquement pour un⋅e député⋅e pur⋅e** : un seul rôle tenu, tous
  les points en relèvent, la garantie retient le premier — c'est-à-dire ce que
  l'ordre fixe aurait donné. **Aucun second gabarit** : mêmes points possibles,
  même ordre, mêmes champs pour les treize.
- **Elle ne déplace aucun point sur les 13 profils publiés aujourd'hui.**
  Vérifié profil par profil au SHA `f635cb60` : sur chacun, les cinq premiers du
  vivier représentent déjà tous les rôles documentés. Elle est écrite quand même,
  parce que c'est elle qui empêche le défaut de revenir quand le vivier ou le
  corpus bouge, et elle est verrouillée sur un cas construit
  (`tests/test_essentiel_328.py`).

### Le rôle ne s'affiche que s'il distingue

`montrerLesRoles` est vrai quand la personne tient plus d'un rôle (6 des 13).
Cinq fois « comme parlementaire » sur un profil qui n'a jamais été ministre est
du bruit ; le champ existe pourtant sur les treize, et son affichage suit le même
fait collecté que la phrase d'introduction — un conditionnel déjà en place depuis
#694 (`aSiegeAuGouvernement`), pas un second gabarit.

### Ce que la scission coûte, et pourquoi c'est accepté

Le vivier de `gabriel-attal` compte 7 points pour 5 places : ses **3 textes
portés comme parlementaire** n'entrent pas, ses **30 projets de loi portés au nom
du gouvernement** oui. L'ordre inverse aurait produit le défaut symétrique — un
ancien Premier ministre dont la page tait 30 projets de loi. Son rôle
parlementaire reste représenté **deux fois** (amendements, commissions), la
garantie est donc satisfaite, et la phrase d'annonce dit qu'il y avait 7 points
possibles. Les textes non retenus ne sont pas cachés : ils sont dans la section
« ce qu'il a proposé ».

**Arbitrage rendu le 01/09/2026, et à ne pas rouvrir.** L'ordre inverse a été
proposé et écarté : taire 30 projets de loi dont 15 promulgués effacerait le cœur
de l'action publique d'un ancien Premier ministre, là où les 3 textes déposés
comme député restent lisibles une section plus bas. Ce qui rend l'arbitrage
tenable, ce n'est pas l'ordre lui-même mais les trois choses qui l'entourent : la
garantie par rôle, qui empêche le rôle parlementaire de disparaître ; la phrase
d'annonce, qui dit combien de points existaient ; et la section « ce qu'il a
proposé », qui publie ce que le résumé ne retient pas. Changer l'ordre sans elles
recréerait le défaut d'origine, dans un sens ou dans l'autre.

## 4. Le point « amendements » : un couple, et une commission sourcée

### Ce qui est écarté, et pourquoi

| Écarté | Raison, mesurée sur les 13 candidats déclarés au SHA `f635cb60` |
| --- | --- |
| **Le compte brut de dépôts** | il ne mesure pas une activité : la médiane de dépôts par dossier va de **2,5 à 8** sur les quatre profils qui en portent plus de 50, et l'écart entre 2 831 et 584 mesure la participation à un **épisode de dépôt en masse** — 574 des 2 429 dépôts de `jerome-guedj` (23,6 %) portent sur le seul PLFRSS 2023, 182 des 584 de `laurent-wauquiez` (31,2 %) sur le seul PLF 2026 |
| **Filtrer sur les adoptés** | le chiffre mesure le **terrain**, pas la personne : `jerome-guedj` (opposition) en fait passer 160, `marine-le-pen` 4. Et le `sort` est **inconnu sur 1 822 des 2 831** dépôts de `jean-luc-melenchon` — un décompte sur un dénominateur amputé de 64 % viole §2 règle 5. `AGENTS.md` §6 interdit par ailleurs tout taux d'adoption entre types de déposants |
| **Compter les `texte_vise` distincts** | ce sont des **lectures**, pas des lois : un PLFSS revenant en nouvelle lecture compte double. `jerome-guedj` passe de **47 lectures à 25 dossiers** |

### Ce qui est retenu : le couple

> **25 dossiers législatifs amendés · 2 405 amendements déposés sur eux**

Le couple décrit une **manière de travailler**, jamais une performance :
`marine-le-pen` fait 83 dossiers pour 685 dépôts (large et léger),
`laurent-wauquiez` 14 pour 326 (l'inverse). Aucun des deux n'est « meilleur », et
c'est ce qui le rend publiable (§2 règle 1). Un nombre seul appellerait un
classement ; deux nombres qui varient en sens inverse appellent une lecture.

**Le regroupement se fait sur `dossier_id` seul.** La clé était
`a.dossier_id || a.texte_vise` — le défaut de clé `a or b` que décrit
`AGENTS.md` §3a (#668) : elle publiait « 34 dossiers législatifs » pour
`jerome-guedj` là où il y en a **25**, plus 9 textes visés orphelins. Les dépôts
sans dossier résolu sont désormais comptés **à part** et déclarés.

**Quand aucun dossier n'est résolu, le point ne disparaît pas** : il dit le
nombre de dépôts et pourquoi il ne peut rien en dire de plus. `xavier-bertrand`
(62 dépôts) et `edouard-philippe` (6) sont dans ce cas — leurs textes visés
relèvent de la XIVe législature, dont l'archive de dossiers n'est pas ingérée.

### Et l'empreinte thématique : la commission saisie au fond

Elle **ne se déduit pas d'un titre**. Bâtir la correspondance intitulé → thème
serait une classification construite par ce dépôt, c'est-à-dire un acte éditorial
— exactement ce que §4 dit des catégories PCS de l'INSEE (#659).

Elle se **lit dans l'archive AN** : chaque `dossierParlementaire` porte un acte
`codeActe: "AN1-COM-FOND-SAISIE"` (« Renvoi en commission au fond ») dont
l'`organeRef` est résolu par le référentiel des organes (#353).

Mesuré le 01/09/2026 sur les trois archives XV/XVI/XVII :

| | Mesure |
| --- | ---: |
| dossiers portant une saisie au fond AN | **6 024** |
| saisies sans `organeRef` | **0** |
| `organeRef` que le référentiel ne résout pas | **0** |
| dossiers où deux saisies au fond désignent des organes différents | **0** |
| types d'organe rencontrés | `COMPER` 6 257, `CNPS` 28 |

`AN1` est la **première lecture** à l'Assemblée : c'est la saisine qui range le
dossier, celles des lectures suivantes la répètent. Les `SN1-COM-FOND-SAISIE`
(Sénat) ne sont pas lus — le Sénat est hors périmètre (#528), et une commission
sénatoriale ne décrit pas le travail d'un⋅e député⋅e.

Répartition mesurée, par **dossiers** et non par dépôts (un dossier très amendé
ne pèse pas plus lourd, sans quoi la barre mesurerait l'épisode de dépôt en
masse) :

| Profil | Dossiers | Avec commission | Trois premières |
| --- | ---: | ---: | --- |
| `jerome-guedj` | 25 | 25 | **16** Affaires sociales · 4 Lois · 3 Finances |
| `marine-le-pen` | 83 | 82 | 31 Lois · 17 Finances · 14 Affaires sociales |
| `laurent-wauquiez` | 14 | 13 | **4** Affaires sociales · **4** Lois · 3 Finances |
| `jean-luc-melenchon` | 23 | 23 | 6 Finances · 6 Lois · 3 Affaires culturelles et éducation |
| `gabriel-attal` | 3 | 3 | 2 Lois · 1 Affaires culturelles et éducation |

### Aucun seuil ne décide qu'il y a une tendance

La contrainte — *une tendance quand elle existe, rien quand elle n'existe pas* —
se règle **sans seuil**, et c'est le point élégant : `laurent-wauquiez` a 4 et 4
à égalité en tête, il n'y a pas de tendance, et ce n'est pas nous qui le
décidons — c'est la donnée qui n'en produit pas. La page affiche la
**répartition** et laisse la forme parler : un long segment chez `jerome-guedj`,
trois comparables chez `marine-le-pen`, deux identiques chez `laurent-wauquiez`.

Le **départage à égalité est alphabétique**, jamais l'ordre d'insertion : celui-ci
ferait lire une égalité comme une avance.

### Deux garde-fous de libellé

- **« Dossiers examinés par », jamais « travaille sur ».** Une commission n'est
  pas un sujet : « Lois » couvre l'immigration, la justice et les institutions.
  Aide à la lecture (§2 règle 8), pas position déclarée.
- **La borne se déclare.** Pour `jean-luc-melenchon`, la répartition repose sur
  **332 de ses 2 831 dépôts** (12 %) : la page l'écrit — « 2 499 autres dépôts
  visent 5 textes que la source ne rattache à aucun dossier » — au lieu de la
  présenter comme complète (§2 règle 5). La cause est l'issue **#696**, traitée
  ailleurs ; elle est **déclarée ici, pas corrigée**.

### Où vit la table

`pivot_data/commissions_dossiers.json` (`commissions-dossiers-v1`), construit par
`src/build_commissions_dossiers.py` depuis `src/commissions_dossiers_an.py`, et
ajouté au `git add` de `merge-and-pivot`.

**Un fichier à part, et pas une colonne de `pivot_data/amendements/`.** La
commission est une propriété du **dossier**, pas du texte visé : la ranger dans
la table `textes` de chaque législature la recopierait une fois par texte visé
(777 entrées pour la seule XVe) et la dupliquerait entre législatures — 47
dossiers de la XVIe sont référencés depuis l'index de la XVIIe.

La fusion est **additive** : un run sans archive lisible conserve la table
publiée. Le `git add` est **conditionné à l'existence du fichier**, pour qu'un run
sans archive ne coûte pas le commit des profils.

## 5. Le visuel s'adapte à chaque point

*« Ne te mets pas de contrainte à utiliser la même solution pour chacun des
points. Il faut que ce soit adapté au cas. »* Trois rendus, vocabulaire fermé
(`RENDUS_POINT`) :

| Point | Rendu | Pourquoi celui-là |
| --- | --- | --- |
| `amendements` | **barre** des trois premières commissions | le vocabulaire des commissions est **fermé** (8 permanentes + spéciales) : trois segments s'y comparent |
| `commissions` | **podium** de trois colonnes | « 27 sur 60 » se compare mal en prose ; trois hauteurs se comparent d'un regard |
| `textes_*` | **liste**, rien de graphique | trois intitulés se lisent |
| `interventions`, `questions` | **texte**, comme avant | 417 points de l'ordre du jour forment un vocabulaire **ouvert** : trois segments sur 417 ne disent rien de la forme, c'est le nombre 417 qui la dit |
| `qualite` | **texte** | même raison |

**Un seul ton pour les segments de la barre**, séparés par un filet de 2 px :
deux commissions à égalité doivent produire deux segments **identiques**. Les
teinter par rang les placerait sur une échelle du plus au moins — exactement ce
que #329 a retiré de la fiche de groupe (§2 règle 1).

**La barre n'est pas normalisée à 100 %** : son dénominateur est le **total des
dossiers amendés**, pas la somme des trois segments montrés. Ce qui reste —
autres commissions, dossiers sans commission publiée — demeure visible comme du
vide, et la légende le chiffre (`DESIGN_SYSTEM` §5).

**Aucun jaune signal nulle part dans la section** : ni filet, ni segment, ni
décor (`DESIGN_SYSTEM` §3).

---

## Ce qui n'est pas vérifié

- **Aucun test n'exécute de JavaScript.** Le dépôt n'a pas de harnais JS —
  `package.json` ne déclare que `dev`, `build`, `lint`, `sync-data` — et
  `tests.yml` n'installe pas Node. `tests/test_essentiel_328.py` lit le **code
  exécuté** (commentaires retirés), pas son comportement.
- **La vérification par rendu réel** (`react-dom/server` sur les 13 profils
  publiés, harnais gardé hors dépôt) couvre les chaînes affichées et rien
  d'autre : ni la mise en page, ni le responsive, ni le contraste, ni le parcours
  clavier.
- **La table des commissions n'est pas encore publiée.** Ce lot ne modifie aucun
  fichier de `pivot_data/` ; `pivot_data/commissions_dossiers.json` apparaîtra au
  premier run de `merge-and-pivot` qui exécute le nouveau step. D'ici là, la
  répartition par commission n'est pas affichée et n'est pas déduite d'autre
  chose. Les chiffres du tableau ci-dessus ont été mesurés en construisant la
  table hors du dépôt, avec le même script.
