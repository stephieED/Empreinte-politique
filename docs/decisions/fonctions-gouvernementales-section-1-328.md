# Une fonction exercée ne l'est pas toujours au Parlement (#328) — 04/09/2026

`2026-09-04`

> **En bref** — « Les fonctions exercées » ne montrait que **sept catégories, toutes parlementaires**, alors qu'un portefeuille ministériel est un siège occupé au même titre qu'une commission — intitulé, dates, durée — et que **6 des 13 candidats déclarés en ont exercé un** (65 des 641 profils publiés) ; `categorie: fonction_gouvernementale` couvre **trois natures** que le champ `fonction` sépare déjà pour `appartenancesGouvernementales`, et le filtre porte sur lui, **jamais sur le libellé** — reconnaître « Gouvernement (…) » dans l'intitulé aurait été la jointure par ressemblance de chaîne que #639 interdit : `membre` est l'**enveloppe** et reste à la frise (la publier doublerait chaque portefeuille d'une ligne qui ne dit pas ce qu'on y faisait — **17 enveloppes pour 18 portefeuilles** sur les 7 profils concernés), `en mission` a son **propre bloc** parce qu'un⋅e parlementaire en mission auprès d'un ministère **reste parlementaire** (la frise lui donne déjà sa piste), et le reste est le portefeuille ; **la marque ne s'applique pas** aux deux blocs gouvernementaux (`sansMarque`) — son dénominateur est le temps de mandat **électif**, et Édouard Philippe a été Premier ministre **trois ans sans siéger** : elle aurait affirmé « plus de la moitié » d'un tout dont il était absent, un ratio sans son dénominateur (§2 règle 7) ; **la couleur dit le BANC, pas la catégorie** — bleu de l'Assemblée, bronze du gouvernement, contour **tireté** pour la mission, soit les trois pistes de la frise et pas une teinte de plus, là où une teinte par catégorie en aurait demandé **neuf** et aurait fait perdre le banc sur un profil qui a connu les deux ; et la couleur **double** l'intitulé du bloc sans le remplacer, la section restant lisible en niveaux de gris ; effet de bord assumé : les deux teintes étaient écrites en littéral à **cinq endroits**, au point qu'un test surveillait que deux d'entre elles n'avaient pas divergé — **une valeur qu'un test doit surveiller pour rester unique est une valeur qui n'aurait pas dû être copiée**, elles vivent désormais sur `.cp-main` et `test_les_colonnes_prennent_la_teinte_de_la_frise` devient `test_la_teinte_d_un_banc_est_declaree_une_seule_fois` ; limite déclarée : **le lot ne retire pas la section « Les gouvernements dont il a été membre »**, qui continue de publier l'appartenance sous une autre forme — sa restructuration est un lot à part, décidé et non implémenté. 11 tests, neuf mutations vérifiées échouantes, suite complète à 3 812, 0 échec.

« Les fonctions exercées » ne montrait que sept catégories, toutes
parlementaires. Un portefeuille ministériel est pourtant un siège occupé — un
intitulé, des dates, une durée, exactement ce que la section mesure — et
**6 des 13 candidats déclarés en ont exercé un** (65 des 641 profils publiés).
La section n'en montrait donc qu'une moitié.

## 1. Trois natures sous une seule catégorie, séparées par un champ sourcé

`categorie: "fonction_gouvernementale"` couvre trois choses que le champ
`fonction` distingue déjà — c'est le discriminant qu'`appartenancesGouvernementales`
utilise depuis toujours :

| `fonction` | Ce que c'est | Où ça va |
| --- | --- | --- |
| `membre` | l'**appartenance** au gouvernement (`Gouvernement (BORNE)`) | nulle part ici : c'est l'enveloppe, et la frise en fait une piste |
| `en mission` | un⋅e **parlementaire en mission** auprès d'un ministère | son propre bloc |
| le reste | le **portefeuille** (Ministre, Secrétaire d'État, Premier ministre) | le bloc « Portefeuilles ministériels » |

**L'enveloppe est exclue, et ce n'est pas un oubli.** Publier
`Gouvernement (BORNE)` à côté de `Ministère de l'éducation nationale` doublerait
chaque portefeuille d'une ligne qui ne dit pas ce qu'on y faisait — mesuré :
17 enveloppes pour 18 portefeuilles sur les 7 profils concernés.

**Le filtre porte sur `fonction`, jamais sur le libellé.** Reconnaître
« Gouvernement (… ) » dans l'intitulé aurait été une jointure par ressemblance
de chaîne, ce que [`regrouper-nest-pas-joindre-639`](regrouper-nest-pas-joindre-639.md)
interdit.

**La mission n'est pas un ministère.** Un⋅e parlementaire en mission auprès d'un
ministère reste parlementaire : la frise lui donne sa propre piste, et la ranger
avec les ministres serait le contresens que la frise évite déjà. Jérôme Guedj en
a deux, et aucun portefeuille.

## 2. La marque ne s'applique pas aux blocs gouvernementaux

Le filet de la section marque la fonction qui dépasse **la moitié du temps de
mandat électif**. Un portefeuille ne se compare pas à ce tout : Édouard Philippe
a été Premier ministre trois ans **sans siéger**. La marque aurait affirmé
« plus de la moitié » d'un dénominateur dont il était absent — un ratio publié
sans son dénominateur, ce que §2 règle 7 refuse.

Les deux blocs portent donc `sansMarque`, et c'est la seule exception : le reste
de la règle est inchangé.

## 3. La couleur dit le BANC, pas la catégorie — et elle ne prend pas le bord gauche

Chaque bloc porte une **pastille** et un **titre teinté** : bleu pour
l'Assemblée, bronze pour le gouvernement, **pastille au contour tireté** pour la
mission. Ce sont les trois pistes de la frise, sans une teinte de plus.

**Le bord gauche est déjà pris, et il le reste.** Un filet de banc à gauche du
bloc se superposait au filet d'encre de la **marque**, qui signale la fonction
dépassant la moitié du temps de mandat : deux traits verticaux à trois pixels
l'un de l'autre se lisent comme un seul, et la ligne marquée — qui déborde
volontairement jusqu'au bord de la carte — passait par-dessus celui du banc.
Deux faits de nature différente ne partagent pas un bord : **il revient au seul
des deux qui qualifie UNE ligne**.

Le titre y gagne au passage : `--muted` vaut **3,51:1** sur blanc, sous le seuil
AA de 4,5:1 ; le bleu vaut **8,14:1** et le bronze **4,90:1**.

Une teinte par catégorie aurait demandé **neuf** couleurs, en concurrence avec
la seule grammaire de couleurs de la fiche — et sur un profil qui a connu les
deux bancs, c'est le banc qu'on aurait perdu. Ce qui sépare une commission d'un
groupe d'amitié est écrit en toutes lettres au-dessus de chaque bloc : **la
couleur double l'intitulé, elle ne le remplace pas**, et la mission se distingue
aussi par la forme du filet — la section se lit en niveaux de gris.

## 4. Les deux teintes sont désormais déclarées une seule fois

Elles étaient écrites en littéral à **cinq** endroits — la frise, les colonnes
d'« En bref », deux pastilles de position, la marque de projet de loi — au point
qu'un test existait pour vérifier que deux d'entre elles n'avaient pas divergé.

**Une valeur qu'un test doit surveiller pour rester unique est une valeur qui
n'aurait pas dû être copiée.** Elles vivent sur `.cp-main`, et tous leurs
lecteurs les lisent. `test_les_colonnes_prennent_la_teinte_de_la_frise` devient
`test_la_teinte_d_un_banc_est_declaree_une_seule_fois` : il vérifiait que deux
copies coïncidaient, il vérifie qu'il n'y en a plus qu'une. Même leçon que
[`teintes-des-stades-en-bref-328`](teintes-des-stades-en-bref-328.md), un cran
plus haut.

## Alternatives écartées

| Écartée | Pourquoi |
| --- | --- |
| Publier l'appartenance (`Gouvernement (BORNE)`) comme une fonction | Elle ne dit pas ce qu'on y faisait, et double chaque portefeuille |
| Ranger la mission avec les portefeuilles | Un⋅e parlementaire en mission reste parlementaire — la frise le sait déjà |
| Une teinte par catégorie de fonction | Neuf teintes en concurrence avec le code du banc ; sur un profil bicaméral de fait, c'est le banc qu'on perd |
| Une forme de marqueur par catégorie | Demandait d'inventer un vocabulaire de formes qu'il aurait fallu expliquer en légende |
| Appliquer la marque aux portefeuilles | Le dénominateur est le mandat électif ; Philippe a gouverné trois ans sans siéger |

## Ce qui n'est pas vérifié

- **Aucun harnais JS.** Les 11 tests ajoutés lisent le code exécuté,
  commentaires retirés ; **neuf mutations** ont été vérifiées échouantes. Ils ne
  couvrent ni le rendu, ni le parcours clavier. Les trois rapports de contraste
  ci-dessus sont **calculés à la main**, pas par un test : le dépôt n'a pas de
  quoi les mesurer.
- Le rendu a été relu **sur les 7 profils publiés qui portent une fonction
  gouvernementale**, rendus par les composants de l'application.
- **Ce lot ne touche pas la section « Les gouvernements dont il a été membre ».**
  Elle continue de publier l'appartenance sous une autre forme : la
  restructuration qui la retire est un lot à part, décidé mais non implémenté.
