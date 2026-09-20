# Un créneau de séance n'est pas un sujet, et le discriminant reste structurel (#710, 02/09/2026)

`2026-09-02`

> **En bref** — `AGENTS.md` §3e réserve `sujet` au `code_grammaire` du point depuis #510, mais `TITRE_TEXTE_DISCUSSION` **n'est pas homogène** : c'est le titre du point d'**ordre du jour**, et l'Assemblée y inscrit tantôt un texte (« Droit à l'aide à mourir ») tantôt un **créneau de séance** (« Questions au gouvernement », « Questions orales sans débat », « Questions au Premier ministre »), d'où un faux thème dans `theme_officiel` puis `tags_thematiques` (§2 règle 8) ; deux causes mesurées sur les **61 109 points** des archives 16 et 17 — **`QPM_1_1` manquait au vocabulaire** (35 points, 629 paragraphes héritant du titre du créneau au lieu de « Parcoursup ») et **un créneau se reconnaît à ce que la source range dessous** (`_creneaux_de_questions` : un `TITRE_TEXTE_DISCUSSION` enfermant des points de question, **279 des 2 138** titrés), passe **préalable** parce que ces points sont des frères XML venant après lui en ordre de document ; **aucune liste de libellés**, et ce n'est pas un principe : la source publie *quatre* variantes typographiques du même créneau sur ces deux seules législatures, un filtre lexical en manquerait trois — défaut de #672 et de #639 —, et un test remplace le libellé par une chaîne sans rapport pour vérifier que le verdict ne bouge pas ; **cinquième occurrence** de la famille #492 / #639 / #641 / #696 : `backfill_sujet_seance` reporte trois champs nommés sur l'entrée déjà collectée, seulement ceux que l'entrée neuve porte (une entrée réduite au thème n'a pas de `sujet`, #657), **sans jamais toucher la clé de fusion** (#668), sur une preuve sourcée différente aux deux étages — la clé `sujet_code_grammaire` au brut, `source.type == "syceron"` au pivot, republier le code coûtant ~48 o sur **636 461** entrées réduites — et c'est le premier de la famille qui **retire** une valeur au lieu d'en poser une ; **`tags_thematiques` devient dérivé** (`schema_pivot.deriver_tags_thematiques`, comme `chambres` et `licence_donnees`) parce que `merge_pivot_profile` **unissait** ancienne et nouvelle liste, ce qui rendait tout tag immortel — le recalcul ne perd rien par lui-même, mesuré **39 782 = 39 782** couples (profil, tag) sur 0 profil d'écart ; effet mesuré, législatures 16-17 seules : **765 interventions publiées corrigées sur 81 des 481 profils** (282 perdent leur sujet, 483 reçoivent celui de la question réellement posée), **93 couples (profil, tag) retirés et 141 ajoutés**, et sur les 5 fiches AN « questions au premier ministre » tombe du **32e rang** de `AN:LR` et du 43e de `AN:SOC` ; **perte sur une liste stable**, donc `allow_declared_losses` au run de remédiation (#460/#470) ; **ce que le critère ne tranche pas est compté** — « Motion de censure » (32 points, 11 665 paragraphes ; 243 profils tagués), « Motions de censure » (192) et « Déclaration du Gouvernement et débat » (125) restent publiés, la source ne portant pour eux **aucune** marque structurelle (`@valeur` remplie sur 1 335 des 2 138 points titrés textes et créneaux confondus, `sousIntitule` à « 0 » sur les 2 138), et un `code_grammaire` absent ou inconnu ne devient **jamais** procédural par défaut, le critère étant positif des deux côtés (**0** point sans code sur 61 109) ; non mesuré et déclaré : la **XVe législature**, absente du cache (`.zip.part`), qui porte **255 993 des 651 695 interventions Syceron publiées (39,3 %)** — tous les chiffres ci-dessus sont des bornes inférieures —, `type_detail` qui garde son repli lexical hors périmètre, et **aucun run lancé** (jointure vérifiée : 388 751 / 388 751 entrées publiées retrouvées dans l'archive rendent exactement le sujet publié avant correction).

## Contexte

`AGENTS.md` §3e pose la règle depuis #510 : « ce qui sépare un sujet d'un
intitulé procédural est **structurel**, pas lexical (le `code_grammaire` du
point) ». #510 l'a tenue pour les points d'article et de procédure —
« article 1er », « suspension et reprise de la séance », « rappel au règlement »
— en réservant `sujet` à trois codes de matière.

Elle ne tient pas pour le point d'**ordre du jour**. `TITRE_TEXTE_DISCUSSION`
est le titre de ce que l'Assemblée a inscrit, et l'Assemblée inscrit tantôt un
texte — « Droit à l'aide à mourir » — tantôt un **créneau de séance** :
« Questions au gouvernement », « Questions orales sans débat », « Questions au
Premier ministre ». Le créneau n'est pas un sujet, et `normalize_profil` en tire
`theme_officiel` puis `tags_thematiques` : un faux thème (§2 règle 8).

## Ce qui est mesuré

**Archive Syceron en cache, législatures 16 et 17** (605 + 601 comptes rendus,
30 787 + 30 322 points ; la XVe n'est pas sur disque — voir « Ce qui n'est pas
mesuré »). Distribution complète des `code_grammaire` de points, prise avant de
choisir :

| `code_grammaire` | Points (16 + 17) | Titrés | Ce que le titre nomme |
| --- | ---: | ---: | --- |
| `DISC_ARTICLES_*` | 42 876 | partiellement | l'article, ou rien |
| `QG_1_1` | 3 708 | 3 708 | **le sujet de la question** |
| `TITRE_TEXTE_DISCUSSION` | 2 138 | 2 138 | **le texte, OU le créneau** |
| `QOSD_1_1` | 1 554 | 1 554 | **le sujet de la question** |
| `RAP_REGLEMENT_1_1` | 1 807 | 1 807 | la procédure (5 libellés) |
| `SUSP_SEANCE_1_1` | 1 553 | 1 553 | la procédure (2 libellés) |
| `SOUS_TITRE_TEXTE_DISCUSSION` | 1 276 | 1 276 | la phase de discussion |
| `QPM_1_1` | 35 | 35 | **le sujet de la question** |
| 53 autres codes | 6 162 | variable | procédure, votes, motions |

Deux constats, et ce sont eux qui décident :

1. **`QPM_1_1` manquait au vocabulaire du parseur.** 35 points, 629 paragraphes
   qui héritaient donc du titre du créneau au lieu de « Parcoursup ».
2. **Le créneau se reconnaît à ce que la source range dessous.** Un
   `TITRE_TEXTE_DISCUSSION` sous lequel des points `QG_1_1` / `QOSD_1_1` /
   `QPM_1_1` sont rangés est un créneau : la source elle-même publie le sujet un
   cran plus bas, un par question. **279** des 2 138 points titrés le sont.

### Sur le corpus publié, à `c13c99f2`

| Population | Mesure |
| --- | ---: |
| interventions publiées, 481 profils | 652 703 |
| … portant un `sujet` | 14 817 |
| … dont le `sujet` change (legs 16-17 seules) | **765** |
| … le sujet est retiré | 282 |
| … le sujet est remplacé par celui de la question réellement posée | 483 |
| profils dont `tags_thematiques` change | **81 / 481** |
| couples (profil, tag) retirés | 93 |
| couples (profil, tag) ajoutés | 141 |

Tags retirés, par nombre de profils porteurs : « questions au premier
ministre » **69**, « questions au gouvernement » **14**, « questions orales sans
débat » **8**, « questions au gouvernement (suite) » **2**.

**Par groupe**, sur les 5 fiches AN publiées (la XVIe ; les 2 fiches Sénat gelées
n'ont aucun tag) :

| Fiche | Tag retiré | Rang dans l'empreinte | Porteurs |
| --- | --- | ---: | ---: |
| `AN:LR` | questions au premier ministre | **32e** / 2 620 | 22 → 0 |
| `AN:SOC` | questions au premier ministre | **43e** / 1 554 | 8 → 0 |
| `AN:RN` | questions au premier ministre | 79e / 2 595 | 14 → 0 |
| `AN:RN` | questions au gouvernement | 185e | 8 → 0 |
| `AN:REN` | questions au premier ministre | 111e / 4 303 | 15 → 0 |
| `AN:LFI` | questions au premier ministre | 191e / 2 153 | 10 → 0 |

Chaque fiche gagne en échange de vrais sujets de question : 21 tags nouveaux sur
`AN:LR`, 27 sur `AN:REN`, 9 sur `AN:LFI`, 7 sur `AN:RN` et `AN:SOC`.

## Décision

### 1. Le critère

`QPM_1_1` rejoint `_CODE_GRAMMAIRE_SUJET` et
`_TYPE_DETAIL_PAR_CODE_GRAMMAIRE` — même famille, même forme que ses deux
jumeaux.

`parse_syceron._creneaux_de_questions` fait une passe préalable sur `<contenu>`
et retient l'`id_syceron` de tout `TITRE_TEXTE_DISCUSSION` sous lequel la source
range un point de `_CODE_GRAMMAIRE_QUESTION`. `_point_porteur_du_sujet` saute
ces points-là : leur titre ne devient jamais un `sujet`, il reste lisible dans
`point_ordre_du_jour`, qui est du contexte et pas un thème.

La passe est **séparée** parce qu'elle doit avoir lieu **avant** le parcours des
paragraphes : les points de question sont des frères XML du point d'ordre du
jour (`nivpoint` 2 contre 1), donc ils viennent après lui en ordre de document.
Elle applique la même discipline de pile que `_iter_paragraphes`, pour que
« sous » veuille dire la même chose des deux côtés.

`sujet: None`, et rien d'autre — pas de valeur de repli, pas de chaîne vide
(§2 règle 5).

### 2. Aucune liste de libellés, et ce n'est pas une précaution de style

La source publie, sur les seules législatures 16 et 17, **quatre variantes
typographiques du même créneau** : « Questions au gouvernement » (114),
« Questions au Gouvernement » (99), « Questions au Premier ministre » (5),
« Questions au premier ministre », plus « Questions au Gouvernement (suite) ».
Un filtre lexical en manquerait trois. C'est le défaut de #672 (sélection par
sous-chaîne, fausse dans les deux sens) et celui de #639 (clé tirée d'un libellé,
qui rouille en silence : 283 dossiers sur 304 manqués).

`tests/test_sujet_intitule_procedural_710.py` remplace le libellé du créneau par
une chaîne sans rapport dans la réduction verbatim et vérifie que le verdict ne
bouge pas. Une liste de libellés, même exhaustive, ferait échouer ce test.

### 3. Le report nommé — cinquième occurrence de la même famille

`merge_profile.backfill_sujet_seance`, sur le patron de `backfill_mandat_chambre`
(#492), `backfill_vote_qualification` (#639), le filtre de publication de #641 et
`backfill_texte_vise` (#696) : **un champ corrigé n'atteint jamais une entrée
déjà collectée tout seul**, et le remède est un report nommé, jamais une fusion
plus permissive.

Il ne touche **que** les champs nommés (`sujet`, `theme_officiel`,
`sujet_code_grammaire`), **que ceux que l'entrée neuve porte** (une entrée pivot
réduite au thème n'a pas de `sujet`, #657), et **jamais la clé de fusion** —
l'élargir est le défaut de #668, 468 doublons sur 940 entrées.

Sa preuve est sourcée, et elle n'est pas la même aux deux étages :

- au **brut**, la présence de la clé `sujet_code_grammaire` — fût-elle à
  `None` : elle n'existe que depuis le parseur corrigé ;
- au **pivot**, `source.type == "syceron"`, déjà publié sur les deux formes
  d'entrée. Y republier le code de point coûterait ~48 octets sur chacune des
  **636 461** entrées pivot réduites au thème, exactement le budget que #657
  est allé chercher.

**Ce report n'est pas monotone, contrairement aux quatre précédents, et c'est le
fait à déclarer.** Ils ne remplissaient qu'un champ absent ; celui-ci retire une
valeur sur 282 des 765 interventions qu'il corrige.

### 4. `tags_thematiques` devient un champ dérivé

Le report ne suffisait pas : `merge_pivot_profile` **unissait** l'ancienne liste
de tags et la neuve. Un tag publié une fois y restait pour toujours, quelle que
soit la correction apportée aux interventions dont il dérive.

`tags_thematiques` se recalcule donc après la fusion, par la fabrique unique
`schema_pivot.deriver_tags_thematiques`, comme `chambres` se recalcule depuis les
mandats fusionnés (#493) et `licence_donnees` depuis `sources[]` (#530).

**Le recalcul ne perd rien par lui-même**, et c'est mesuré : les 39 782 couples
(profil, tag) publiés sont **exactement** ceux que la fabrique rend depuis les
`interventions[]` des 481 profils publiés — 0 profil d'écart. Ce qui change
ensuite ne vient que de la correction des interventions. Et la fusion des
interventions étant additive, un run qui n'en collecte aucune
(`--skip-interventions`) laisse les tags inchangés.

### 5. La perte se déclare

`tags_thematiques` (profils) et `tags_thematiques_agreges` (groupes, partis) sont
des **listes stables** au sens d'`audit_diff_profils` : leur baisse abandonne le
commit (#460, étendu par #470 précisément sur ce champ). Le run de remédiation
passe donc par `allow_declared_losses`, jamais en désarmant le contrôle
(`AGENTS.md` §3c).

## Ce que le critère ne tranche pas, nommé et compté

**Un point d'ordre du jour qui est un moment de séance sans grammaire plus fine
en dessous.** « Motion de censure » (32 points, 11 665 paragraphes sur les
législatures 16-17 ; 320 entrées publiées, tag porté par 243 profils),
« Motions de censure » (13 points ; 520 entrées, 192 profils), « Déclaration du
Gouvernement et débat » (125 profils). La source ne porte, pour eux, **aucune
marque structurelle** :

| Signal examiné | Verdict |
| --- | --- |
| `@valeur` (n° du document) | 1 335 des 2 138 points titrés la remplissent, textes **et** créneaux confondus |
| `<sommaire><titreStruct><sousIntitule>` | vaut « 0 » sur les 2 138 |
| `code_grammaire` d'un point plus profond | `SOUS_TITRE_TEXTE_DISCUSSION` sous « Motion de censure » comme sous un projet de loi |

Ils restent donc publiés. C'est un trou déclaré, pas un trou comblé par un
libellé (§2 règle 5). **La route pour le fermer est nommée** : l'ordre du jour
publié par l'AN (`vp/reunions/`) qualifie ses points ; l'instruire est un autre
lot, avec une source de plus à collecter.

**Un `code_grammaire` absent ou inconnu ne devient pas procédural par défaut.**
Le critère est positif des deux côtés : un point ne porte un sujet que si son
code est dans `_CODE_GRAMMAIRE_SUJET`, et n'est écarté que si la source range
sous lui des points de question. Un code inconnu ne fait ni l'un ni l'autre —
mesuré : 0 point sans `code_grammaire` sur les 61 109 des deux archives.

## Alternatives écartées

| Alternative | Pourquoi non |
| --- | --- |
| Une liste de libellés procéduraux | Quatre variantes du même créneau, mesurées ; #672 et #639 ont déjà payé |
| Retirer `TITRE_TEXTE_DISCUSSION` du vocabulaire | 535 652 des 596 025 paragraphes porteurs de sujet en dépendent : « Droit à l'aide à mourir » **est** le sujet |
| Une fusion « la nouvelle valeur gagne » sur `interventions[]` | La fusion additive protège 652 703 entrées d'une collecte partielle ; on ne l'ouvre pas pour deux champs |
| Publier `sujet_code_grammaire` dans le pivot | ~48 octets × 636 461 entrées réduites, le budget de #657, pour un champ qu'aucun consommateur ne lit |

## Ce qui n'est pas mesuré

- **La XVe législature.** L'archive n'est pas sur disque (`.cache/syceron_an/15/`
  ne contient qu'un `.zip.part` de 3 Mio), et aucun appel réseau n'a été fait.
  Elle porte **255 993 des 651 695 interventions Syceron publiées (39,3 %)** : la
  correction s'y appliquera au prochain run qui la rejoue, et les chiffres de ce
  document sont donc des **bornes inférieures**. Le signe est visible dans la
  mesure elle-même : « questions orales sans débat » passe de 2 à **1** porteur
  sur `AN:LR` et `AN:REN`, le porteur restant tenant son tag d'une législature
  que la mesure ne couvre pas.
- **`type_detail` reste partiellement lexical.** `_TYPE_DETAIL_MAP` cherche des
  regex dans les titres en repli du `code_grammaire`. Ce lot ne l'a pas touché :
  `type_detail` n'alimente pas `tags_thematiques`, et le corriger est un
  périmètre distinct.
- **Aucun run n'a été lancé.** Les 765 corrections sont une simulation : le
  parseur corrigé rejoué sur l'archive, joint aux profils publiés par
  `intervention_id`. La jointure est vérifiée — **388 751 des 388 751** entrées
  publiques retrouvées dans l'archive rendent exactement le sujet publié avant
  correction.
