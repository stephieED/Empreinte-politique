# Un scrutin ne dit pas quel texte il tranche : le lien se lit à l'envers (#758), 07/09/2026

`2026-09-07`

> **En bref** — la section « Ce qu'il a voté » devait montrer **sur quoi portent** les textes votés et **s'ils sont passés** : ni l'un ni l'autre n'était atteignable, `objet.referenceLegislative` étant nul sur **0/18 311** scrutins bruts et le seul sort disponible étant celui du *scrutin* (17 non-adoptés sur 697 textes, presque rien à montrer) ; le lien n'existe qu'**en sens inverse**, dans `actesLegislatifs[].voteRefs` du dossier — ce que `MOTIF_TEXTE_LIE_NON_SOURCE` écrivait déjà en renvoyant au rang 4 de #639, close depuis et donc sans porteur ; `pivot_data/scrutins_dossiers.json` publie le rattachement **et** l'issue du dossier, lus sur le **même arbre et les mêmes archives** que la commission au fond et que le statut des textes de gouvernement — troisième usage du même parcours, coût marginal nul côté réseau ; le lien **se lit et ne se devine jamais** (rapprocher par titre serait la jointure par libellé de #639), l'arbre irrégulier impose de le **marcher** plutôt que d'y suivre un chemin (six formes éprouvées), le statut est republié parce que les dossiers votés débordent les 725 textes de gouvernement mais sort de la **même fonction**, et `texte_lie_id` garde son sens de motion de censure ; **aucun cache disque**, et c'est la leçon de #749 — `.cache/dossiers_an` est restauré entre runs, un index dérivé posé là ne se reconstruirait jamais, et le parcours complet coûtant **1,7 s** le cache achèterait ces 1,7 s au prix d'une donnée qui vieillit en silence ; mesuré : **715 scrutins → 561 dossiers**, soit **423 des 697 textes (61 %)** dont **412 avec une commission (59 %)** — et chez Marine Le Pen, **22 textes votés contre ont été adoptés**, **3 votés pour ont été rejetés**, deux faits jusqu'ici impubliables ; limites déclarées : **39 % sans dossier**, XIVe hors archives, et le fichier n'existe pas tant qu'un run n'a pas eu lieu. 19 tests, trois mutations vérifiées échouantes.

Ancres : `scrutins_dossiers_an.py`, `build_scrutins_dossiers.py`,
`construire_table`, `cle_depuis_uid`, `charger_table`,
`MOTIF_TEXTE_LIE_NON_SOURCE`, `_determine_statut`, `iter_dossiers_bruts`.

## Contexte

La section « Ce qu'il a voté » devait montrer **sur quoi portent** les textes
votés pour, contre, en abstention, et **s'ils sont passés**. Aucune des deux
n'était atteignable.

Un scrutin de l'Assemblée ne porte **aucune référence législative** :
`objet.referenceLegislative` et `demandeur.referenceLegislative` sont nuls sur
**0/18 311** scrutins bruts des législatures 14 à 17. Le dépôt le savait — c'est
écrit dans `scrutins_index.MOTIF_TEXTE_LIE_NON_SOURCE`, qui ajoutait : « le
rattachement au dossier n'existe qu'en lien inverse, depuis
`actesLegislatifs[].voteRefs` du dossier législatif — non collecté (#639,
rang 4) ». #639 a été close, et ce rang 4 n'avait plus de porteur.

Le seul sort disponible était celui du **scrutin** — « l'Assemblée nationale a
adopté » —, pas celui du **texte** : sur les 697 textes en dernière lecture,
**17 seulement** portaient un scrutin non adopté. Il n'y avait presque rien à
montrer.

## Décision

`pivot_data/scrutins_dossiers.json` publie deux tables :

```json
{"scrutins": {"an:17:960": "DLR5L17N51481"},
 "dossiers": {"DLR5L17N51481": {"statut": "adopte", "sort_49_3": false}}}
```

**Le lien se lit, il ne se devine jamais.** Un scrutin porte le titre du texte,
un dossier aussi ; les rapprocher par ressemblance serait la jointure par
libellé que `regrouper-nest-pas-joindre-639` interdit — elle donnerait un
rattachement plausible et faux. Un scrutin qu'aucun dossier ne nomme n'a pas
d'entrée, et c'est une absence déclarée (§2 règle 5).

**Le troisième usage du même parcours.** `commissions_dossiers_an.py` marche
`actesLegislatifs` pour la commission au fond, `gouvernement_textes.py` pour le
statut ; ce module le marche pour `voteRefs`, sur **les mêmes archives déjà
téléchargées**, dans le même cache. Le coût marginal est le parcours, pas le
réseau.

**L'arbre est irrégulier, la lecture l'est aussi.** `voteRefs` est tantôt une
chaîne, tantôt une liste, tantôt `{"voteRef": …}`, à profondeur variable.
Marcher l'arbre entier plutôt que suivre un chemin fixe est ce qui rend la
lecture indifférente à la forme — six formes sont éprouvées par les tests.

**Le statut est republié ici**, alors qu'il existait déjà sur les fiches de
gouvernement. Il y couvrait les seuls textes du gouvernement (725) ; les
dossiers tranchés par un scrutin débordent ce périmètre. Les deux sortent de
`_determine_statut()`, **la même fonction** sur le même arbre : il n'y a qu'un
calcul, donc pas de divergence possible.

**Aucun cache disque, et c'est la leçon de #749.** Le réflexe était d'écrire
l'index dérivé à côté des archives dont il dérive, comme le fait
`commissions_dossiers_an.py`. Or `.cache/dossiers_an` est **restauré entre
runs** en CI — `actions/cache`, clé hebdomadaire avec `restore-keys`. Un index
posé là serait servi depuis le cache de la semaine précédente et **ne se
reconstruirait jamais** : exactement le défaut de #749, où un repli de cache
désamorçait la rotation qu'il devait servir. Le parcours complet des trois
archives coûte **1,7 s** (mesuré, 10 967 dossiers) ; un cache disque
achèterait ces 1,7 s au prix d'une donnée qui vieillit en silence. Seul un mémo
**en process** subsiste, qui ne survit pas au run et ne périme donc rien.

**Un fichier à part, pas un champ sur `scrutins.json`.** Les deux tables ne se
collectent pas au même endroit — les scrutins viennent de `Scrutins.json.zip`,
le rattachement de `dossiers*.zip`. Poser le champ sur le scrutin coupleait
leur construction, et rendrait un `dossier_id: null` indistinguable d'un run
qui n'a pas lu les dossiers. Un fichier à part se lit, ou ne se lit pas.

**`texte_lie_id` n'est ni touché ni recouvert.** Il répond à une autre question
— quel texte une **motion de censure** vise (AGENTS.md §5) — et reste nul
partout ailleurs.

## Ce que ça rend, mesuré

Sur les trois archives (XV, XVI, XVII), au 07/09/2026 :

| | |
| --- | ---: |
| scrutins rattachés | **715** |
| dossiers visés | **561** |
| textes en dernière lecture | 697 |
| → avec un dossier joint | **423 (61 %)** |
| → avec une commission saisie au fond | **412 (59 %)** |

Statuts des 423 : `adopte` 200 · `adopte_cmp` 142 · `promulgue` 51 ·
`navette_en_cours` 19 · **`rejete` 11**.

Matières : Lois 142 · Affaires sociales 90 · Affaires économiques 59 ·
Affaires culturelles et éducation 40 · Finances 28 · Développement durable 21 ·
Affaires étrangères 14 · Défense 5 · Commission spéciale LOLF-LFSS 3.

Ce que ça ouvre, sur un profil — Marine Le Pen, position × sort du **dossier** :
**22 textes votés contre ont été adoptés**, **3 votés pour ont été rejetés**.
Aucun de ces deux faits n'était publiable avant ce lot.

## Limites déclarées

- **39 % des textes en dernière lecture n'ont pas de dossier.** C'est un trou à
  déclarer, jamais à combler : la vue devra les ranger sous une catégorie
  nommée, comme « matière non établie » ailleurs.
- **La XIVe législature n'est pas dans les archives ingérées** — sa couverture
  n'est pas mesurée.
- Le fichier pèse **72 ko** et n'est produit que par un run : il n'existe pas
  tant que `generate-data` n'a pas tourné avec ce lot.

## Alternative écartée

**Rapprocher un scrutin d'un dossier par leur titre.** Le taux de
correspondance serait élevé et la méthode indéfendable : un titre est une
chaîne éditoriale, deux lectures d'un même texte n'ont pas le même libellé, et
deux textes voisins en ont de très proches. C'est exactement la classification
par libellé que #639, #718 et #729 écartent chacune à leur tour.
