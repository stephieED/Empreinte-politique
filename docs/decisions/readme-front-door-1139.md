<a id="readme-front-door-1139"></a>
# Le README tient sur une page, et un test le mesure (#1139) (2026-09-26)

`2026-09-26`

> **En bref** — `AGENTS.md` §8 dit « the front door, one page » depuis longtemps et **rien ne le tenait** : mesuré le 25/09/2026, **341 lignes, 22 736 caractères, 12 sections**, dont une de **114 lignes** qui doublait la page « Sources » du site, et deux chiffres nus déjà faux (`389 397` et `389 456` actes, corpus à 389 506) plus un troisième (`5 041 tests`, la suite en compte plus de 6 000) ; réécrit à **232 lignes, 13 591 caractères, 9 sections**, sans aucun chiffre d'inventaire, et `tests/test_readme_front_door_1139.py` mesure désormais la taille, plafonne les sections et refuse un chiffre sans sa date.

## 1. La dérive, et pourquoi elle ne se voyait pas

Elle est invisible au coup par coup : chaque lot ajoute trois lignes « pour que
ce soit dit quelque part », et personne ne mesure le total. Le 25/09, j'allais
moi-même y ajouter la rubrique du Journal officiel et deux volumétries — le
mauvais réflexe, puisque `docs/sources/jorf-dila.md` et
`docs/data-architecture.md` les portent déjà.

Trois sections doublaient un document dédié :

| Section | Ce qui la portait déjà |
| --- | --- |
| « Ce que la couverture ne couvre pas encore », **114 lignes** | la page « Sources » du site, et `docs/data-architecture.md` |
| « Ce que le Journal officiel ajoute », 19 lignes | `docs/sources/jorf-dila.md`, dont c'est la raison d'être |
| « Les articles », 11 lignes | les articles ont leur propre page publiée |

## 2. Ce qui a été fait

| | Avant | Après |
| --- | --- | --- |
| Lignes | 341 | **232** |
| Caractères | 22 736 | **13 591** |
| Sections | 12 | **9** |
| La plus grosse | 114 lignes | 38 |
| Chiffres d'inventaire | 3 faux | **aucun** |

**Renvoyer n'est pas supprimer**, et c'est la contrainte qui a gouverné la
réécriture : chaque limite de couverture reste **nommée** — groupes, Sénat gelé,
borne du 20/06/2012, Parlement européen, Journal officiel, interventions,
mandats locaux, biais de couverture —, mais d'une ligne chacune, le détail
renvoyant à la page « Sources » et aux décisions. Avant de couper, vérifié que
tout ce détail existait bien ailleurs (`docs/data-architecture.md` et les
décisions), donc que rien ne disparaissait du dépôt.

Deux sections sont **fondues** plutôt que retirées : « Neutralité éditoriale »
disait ce que la première règle dit déjà, et « Les articles » tient en trois
lignes sous la table des renvois.

**Les chiffres partent plutôt qu'ils ne se corrigent.** `389 397 actes` a été lu
comme l'état courant pendant trois jours après avoir cessé de l'être ; le
remplacer par 389 506 aurait seulement remis le compteur à zéro.

## 3. Le garde, et ce qu'il n'est pas

`tests/test_readme_front_door_1139.py`, sur le patron de
`tests/test_agents_sans_etat_courant_chiffre.py` — même mécanique : saut des blocs de
code, motifs nommés, et **un test du motif lui-même**.

| Test | Plafond ou règle |
| --- | --- |
| `test_le_readme_tient_sur_une_page` | 250 lignes, 15 000 caractères |
| `test_le_readme_ne_compte_pas_plus_de_sections_qu_il_n_en_faut` | 10 sections de niveau 2 |
| `test_le_readme_ne_porte_aucun_chiffre_d_inventaire_sans_sa_date` | un nombre à séparateur de milliers, ou à partir de trois chiffres devant une chose que le pipeline produit — **sauf si la ligne porte une date** |
| `test_le_motif_attrape_ce_qui_a_casse_et_epargne_le_reste` | les quatre formes qui ont vieilli ici, et six qu'il doit épargner |

**La marge est étroite exprès.** 232 contre 250 : le plafond ne dit pas « voilà
la place qui reste », il dit qu'au-delà on choisit ce qui part, ou on écrit
ailleurs. Le relever est une décision, pas un ajustement.

**Ce qu'il ne fait pas** : juger le contenu. Ce que le README doit nommer —
chaque source vivante, la licence du code — est déjà tenu par
`test_sources_documentees.py` et `test_licence_du_code_1032.py`. Le dupliquer
ferait deux endroits à corriger pour une même règle.

Le garde a été **vérifié contre l'ancien README** : remis en place, il fait
tomber les trois tests de mesure. Il n'aurait pas laissé passer ce qui est passé.

## 4. Trois chiffres, et non quatre

Le motif descend à **trois chiffres** devant un nom, parce que
« couvriront **305 des 461** membres » n'a pas de séparateur de milliers et
périme exactement comme les autres. Il tolère le gras Markdown entre le nombre
et le nom, `461** membres` étant la forme réellement publiée. Descendre sous
trois attraperait « 8 shards » et les numéros de législature, qui sont de
l'architecture — la même distinction qu'au §« Pourquoi ce test ne cherche pas
les chiffres » de son modèle.

## 5. Ce qui reste hors de portée

**La longueur d'`AGENTS.md`** — 421 lignes — n'est pas mesurée, et ce lot ne la
mesure pas : sa règle porte sur le **contenu**, pas sur la taille, et #737 l'a
déjà fait maigrir en sortant les règles de domaine. Les deux fichiers ne se
jugent pas au même critère.
