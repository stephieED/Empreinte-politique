# La cascade des textes portés entre dans l'UI, et la section s'aligne sur la maquette (#328), 06/09/2026

`2026-09-06`

> **En bref** — la PR #745 n'avait porté **qu'une pièce** de la maquette validée, le waterfall, laissant **cinq écarts** (cascade absente, ordre des cartes inversé, carte « Auteur d'amendements » en double, chapeau de section, en-tête du waterfall) ; ce lot les ferme : l'ordre suit les **deux populations** — les textes dont il est auteur ou rapporteur, puis les amendements déposés sur les textes **des autres** —, et la cascade est **portée telle quelle**, `d3-sankey` compris, mesurée avant d'être ajoutée (**+19,9 ko brut, +7,2 ko gzip**, dépendance de rendu **et** 394 lignes de mise en page **et** composant) parce que ce qu'elle apporte est load-bearing — nœuds, largeurs, et empilement contigu des **arrivées** — et que seul le **départ** est repris après coup, forcer aussi l'arrivée cassant la **convergence** que la fourche rend possible ; la mise en page vit dans `utils/` et **ne rend rien**, ce qui permet de vérifier hors navigateur la conservation des textes sur les **13 candidats déclarés** × 4 largeurs ; l'échelle des crans est **celle que le corpus remplit** — un cran n'existe que si un texte s'y arrête, ce qui écarte `inscrit_ordre_jour` (**0 des 423** textes) sans le coder en dur et garantit un **préfixe sans trou** ; la matière est celle de la chute (même table, même ordre, même teinte) parce que **les deux figures doivent colorier pareil**, l'absence restant une absence (§2 règle 5) ; la branche basse continue de ne parler que de **crans** et jamais de sort, `textes_portes[].sort` (#743) n'étant pas encore dans `pivot_data/` — le brancher est un lot à part ; un défaut corrigé au passage : sous trois flux, la maquette rendait une carte **vide** (Jérôme Guedj, 2 textes), l'UI écrit désormais pourquoi ; **coût assumé et déclaré** : la barre par législature emporte avec elle la **position déclarée du groupe** et le chapeau emportait sa raison — la donnée reste calculée, la carte est à réécrire.

Ancres : `disposerCascade`, `croise`, `textesDeLaSelection`, `MOT_COURT_STADE`,
`NEGATION_STADE`, `textesPortes`, `cascadeDesTextes`, `Cascade`, `ListeCascade`,
`Propositions`, `STADES_PUBLIES`, `LIBELLE_STADE`, `teinteMatiere`.

## Contexte

La maquette `CONTRECHAMP` de la section « Ce qu'il a proposé » a été validée
commentaire par commentaire le 6 septembre. La PR #745 n'en a porté **qu'une
pièce**, le waterfall des dépôts, et l'a annoncé. Cinq écarts subsistaient
entre ce qui était validé et ce qui était en ligne :

| point | maquette validée | UI avant ce lot |
| --- | --- | --- |
| textes portés | cascade cliquable | barre segmentée + liste nommée |
| ordre des cartes | textes portés **en premier** | textes portés **en dernier** |
| carte « Auteur d'amendements » (barre par législature) | retirée | en tête de section |
| chapeau « Une seule liste, quel que soit le banc… » | retiré | affiché |
| en-tête du waterfall | « Ce qu'il a déposé comme auteur principal » | « Quand il a déposé, et sur quelle matière » |

Un écart qui n'en est pas un, et qui reste : l'UI a **sept** sections et
« Ce qu'il a proposé » y est la **troisième**, derrière « Les gouvernements
dont il a été membre » que la maquette ne porte pas.

## Décision

### L'ordre suit les deux populations, et elles s'emboîtent

D'abord ce que sont devenus les textes dont il est **auteur ou rapporteur**,
ensuite les amendements déposés sur les textes **des autres**. Deux populations
distinctes, jamais additionnées, et la première éclaire la seconde.

### La cascade est portée telle quelle, d3-sankey compris

Elle a été mesurée avant d'être ajoutée : **+19,9 ko brut, +7,2 ko gzip** sur le
bundle (403,08 → 422,95 ko ; 123,14 → 130,37 ko gzip), et ces chiffres couvrent
`d3-sankey` **et** les 394 lignes de mise en page **et** le composant. C'est la
première dépendance de rendu de l'application, dont la chute voisine se passe :
le SVG y est écrit à la main.

Elle a été ajoutée plutôt que réécrite parce que **ce qu'elle apporte est
load-bearing** — la relaxation itérative qui pose les nœuds, la largeur des
liens, et l'empilement contigu des **arrivées**. Seul le **départ** est repris
après coup : chaque ruban sortant repart de la bande par laquelle sa matière est
entrée. Forcer aussi l'arrivée (`y1 = y0`) figeait chaque matière sur sa voie et
**cassait la convergence** — les barres se lisaient en morceaux disjoints. Ce
qui rend départ corrigé et arrivée libre compatibles, c'est **la fourche** :
la branche basse étant dessinée, ce qui entre égale ce qui sort, et les deux
empilements coïncident matière par matière.

La mise en page vit dans `utils/cascadeTextes.js` et **ne rend rien** : elle
rend des coordonnées. C'est ce qui permet de vérifier la figure hors navigateur
— conservation des textes, branche basse plus fin de course égale le total,
aucun chemin `NaN` — au lieu de la regarder.

### L'échelle des crans est celle que le corpus remplit

Un cran n'existe **que si au moins un texte s'y arrête**. `inscrit_ordre_jour`
est publié par le schéma et porté par **aucun** des 423 textes des 13 candidats
déclarés : le dessiner ouvrirait une colonne que rien ne franchit et que rien ne
quitte. La règle est générale et **non codée en dur** — le jour où un texte s'y
arrête, le cran apparaît, et la négation de la porte précédente devient « non
inscrit à l'ordre du jour » toute seule. Elle garantit accessoirement ce dont la
mise en page a besoin : les crans vifs forment un **préfixe sans trou**, donc
aucun lien ne vise un nœud absent.

C'est pourquoi les mots courts et les négations vivent dans **deux tables
indexées par clé de stade** (`MOT_COURT_STADE`, `NEGATION_STADE`) et non dans
deux tableaux parallèles, qui se seraient décalés en silence ce jour-là.

### La matière est celle de la chute, et pour une raison

`textesPortes` reçoit désormais `commissionDuDossier` — la même table
`commissions_dossiers.json`, la même résolution, le même ordre par volume, donc
la même teinte par `teinteMatiere`. **Les deux figures de la section doivent
colorier pareil**, sinon la section se lit comme deux sections. L'absence de
matière reste une absence (§2 règle 5) : sous « matière non établie », en gris
hors palette, comptée et déclarée sous la figure — 15 des 30 textes de Jean-Luc
Mélenchon, 3 des 34 de Gabriel Attal.

### Ce que la branche basse ne dit pas

Ni « rejeté », ni « abandonné ». `_STADE_RANKS` et `KNOWN_STADES_PROCEDURAUX` ne
connaissent que des valeurs **croissantes**, et un dossier n'en porte qu'une : la
plus avancée atteinte. Aucun champ ne dit qu'un texte a été repoussé, retiré, ou
qu'il attend encore. La branche basse dit donc « non discuté en séance », « non
adopté », « non promulgué » : **aucun acte au-delà à la date du corpus**, et un
texte en navette est dedans.

Le lot #743 a depuis ajouté `textes_portes[].sort`, qui **dit** le sort — 472
entrées, dont 13 `rejete` et 8 `retire`. Il n'est pas encore dans `pivot_data/`
(il faut un run) et la cascade ne l'utilise pas : elle continue de ne parler que
de crans. **Le brancher est un lot à part**, et il changera le vocabulaire de la
branche basse, pas sa géométrie.

### Un défaut corrigé au passage

Avec moins de trois flux, la maquette rendait une carte **vide** — Jérôme Guedj,
2 textes portés, un cadre sans rien dedans. L'UI écrit désormais pourquoi
(« Trop peu de textes pour un diagramme de flux — la liste ci-dessous les porte
tous »).

## Ce que ce lot retire, et qui n'est pas rien

La barre des sorts d'amendement par législature portait la **position déclarée
du groupe**, et le chapeau de section portait sa raison : « un amendement
d'opposition et un amendement de majorité ne sont pas le même acte ». Les deux
partent, parce que la maquette validée ne les porte pas. **La position n'est pas
perdue** — `amendements.legislatures[].position` reste calculé, `Position` reste
un composant, et la remettre est une carte à écrire, pas une donnée à
recollecter. Mais à cette heure, la fiche ne dit plus depuis quel banc les
amendements ont été déposés, et c'est un fait éditorial, pas un détail de mise
en page.

## Alternative écartée

**Réimplémenter le sankey à la main**, pour tenir la promesse « aucune
librairie de graphiques » que la chute a tenue. Écartée : la relaxation
itérative de d3-sankey n'est pas reproductible à l'identique, et l'objet de ce
lot est précisément la **fidélité à ce qui a été validé visuellement**. Une
réécriture aurait été un troisième dessin à faire approuver, pour économiser
7,2 ko gzip.
