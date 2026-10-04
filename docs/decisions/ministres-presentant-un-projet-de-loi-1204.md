<a id="ministres-presentant-un-projet-de-loi-1204"></a>
# Le ministre qui présente un projet de loi complète `initiateurs`, avec son portefeuille au jour du dépôt (#1204) (2026-10-04)

`2026-10-04`

> **En bref** — pour relier un projet de loi à un ministère, la fiche de gouvernement avait besoin du ministre qui le présente. Le dossier législatif ne le nomme qu'une fois sur deux ; le **document de dépôt** le porte, comme cosignataire. `textes[].initiateurs` est complété depuis ce document : sur les 1 298 projets des fiches, **646 ne portaient qu'un nom ou aucun, 26 après** ; 695 noms ajoutés, tous membres de la fiche. Chaque entrée dit où elle a été lue (`releve_dans`) et porte le `portefeuille` tenu le jour du dépôt.

## 1. Le besoin, et un chiffre de départ faux

Demande de la propriétaire, relayée par la session de l'interface : relier, sur
la fiche de gouvernement, les projets de loi et les actes parus au Journal
officiel par le ministère. Les actes portent le leur ; les projets de loi, non.

Le besoin était arrivé avec une mesure — « sur les 111 projets de la fiche Borne,
`initiateurs` ne porte qu'une personne, Élisabeth Borne pour 110 » — que
l'arbitrage a d'abord reprise telle quelle. **Elle est fausse** : remesurée le
04/10/2026, la fiche Borne porte un seul initiateur sur 46 projets, deux sur 40,
trois ou plus sur 25. La décision de principe a été prise sur le chiffre faux,
puis confirmée par la mesure : le lot ne crée pas le lien ministre → texte, il
le **complète**.

## 2. Ce que la source porte

Un projet de loi est déposé au nom du Premier ministre et présenté par un ou
plusieurs ministres. Deux endroits le disent :

| Où | Ce qu'il porte |
| --- | --- |
| le dossier, `initiateur.acteurs.acteur[]` | le Premier ministre, et les ministres une fois sur deux |
| le document de dépôt, `auteurs` et `coSignataires` | le Premier ministre en auteur, les ministres en cosignataires |

Mesuré sur les quatre archives de dossiers (XIVe à XVIIe), dossiers d'origine
gouvernementale dont le document de dépôt est lu :

| Législature | Dossiers | cosignataires déjà parmi les initiateurs | apportent un nom | aucun cosignataire |
| --- | --- | --- | --- | --- |
| XIVe | 573 | 287 | 281 | 5 |
| XVe | 483 | 257 | 213 | 13 |
| XVIe | 127 | 75 | 49 | 3 |
| XVIIe | 115 | 35 | 77 | 3 |

Un dossier de la XVIIe sur 116 n'a pas de document de dépôt.

## 3. La décision

1. `gouvernement_textes.cosignataires_des_documents` lit les cosignataires des
   documents `PRJL` ; `parse_dossier_gouvernemental` rend ceux du document de
   dépôt sous `presentateurs_acteur_refs`, `None` quand la source ne dit rien.
2. `gouvernement_profile._initiateurs_texte` **complète `initiateurs`** : les
   acteurs du dossier d'abord, puis les cosignataires que le dossier ne nomme
   pas. Personne n'est répété.
3. Deux clés par entrée, **facultatives à la validation** :
   - `releve_dans` — `dossier` ou `document_depot`
     (`KNOWN_RELEVES_INITIATEUR`) ;
   - `portefeuille` — celui que la personne tenait le jour du dépôt, lu dans
     `membres[]` de la même fiche. `null` hors de `membres[]` ou si aucune
     période ne contient la date ; deux périodes qui se touchent le même jour
     rendent la plus récente.

**Pourquoi compléter `initiateurs` et non ouvrir un champ voisin.** La source
elle-même range les ministres parmi les initiateurs une fois sur deux : un champ
voisin aurait coupé le même fait en deux, selon la façon dont l'Assemblée a
rempli le dossier. `releve_dans` garde la trace de l'origine (§2 règle 2).

**Pourquoi le portefeuille est calculé ici.** C'est une dérivation, pas un fait
de la source : elle est écrite à un seul endroit, testée, et l'interface la lit.

## 4. L'effet, simulé sur les fiches publiées

Assemblage rejoué sur les fiches de `pivot_data/gouvernements/` (privé
`bae8d5414`), sans rien écrire :

| | Projets de loi |
| --- | --- |
| retrouvés dans les archives | 1 298 (4 de Lecornu II ne le sont pas) |
| un seul nom ou aucun, avant | 646 |
| un seul nom ou aucun, après | 26 |
| avec au moins un portefeuille autre que celui du Premier ministre, après | 1 265 |

695 noms ajoutés, **tous membres de la fiche**. Aucun lien existant n'est
modifié ; les fiches simulées passent la validation.

**Simulé n'est pas mesuré** : à vérifier sur le corpus après le premier run. Les
fiches de gouvernement sont recomposées à chaque run ; aucun cache n'est à
invalider.

## 5. Ce qui reste déclaré

- 26 projets gardent un seul nom ou aucun : la source n'en dit pas plus.
- 33 projets n'ont aucun portefeuille de ministre : cosignataire hors de
  `membres[]`, ou date de dépôt hors de ses périodes.
- Un cosignataire est tenu pour un ministre présentant le texte parce que les
  695 ajoutés sont membres du gouvernement de la fiche ; ce n'est pas une
  propriété que la source déclare.
