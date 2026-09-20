<a id="index-europeen-lit-aussi-les-textes-portes-901"></a>
# L'index européen ne lisait que les amendements, et 34 références ne résolvaient nulle part (#901) (2026-09-16)

`2026-09-16`

> **En bref** — `references_visees()` construisait le périmètre de
> `dossiers_europeens.json` à partir des seuls `texte_vise` des amendements.
> Les `textes_portes[]` européens publient eux aussi une `reference_dossier`, et
> personne ne la lisait : **34 références distinctes**, soit **54 occurrences**
> sur les fiches, désignaient un dossier absent de l'index. L'index passe de
> **355 à 389** dossiers. Ce n'était pas un filtre par type de procédure — il
> n'y en a jamais eu. **Et comme l'extension n'apportait que 4 commissions au
> fond, l'index publie désormais `matieres` — la classification OEIL, remplie
> sur les 389 dossiers, RSP comprises.**

## Contexte

La question posée était « peut-on afficher la commission d'un texte européen ? ».
La mesure a répondu autre chose.

`pivot_data/dossiers_europeens.json` porte bien une commission au fond, sur 341
des 355 dossiers. Mais sur les **694** textes portés européens des fiches de
candidats déclarés, **12 seulement** résolvaient dans cet index :

| | |
| ---: | --- |
| 628 | sans aucun identifiant de dossier — résolutions individuelles, motif `activite_sans_dossier` |
| 54 | avec un identifiant qui **ne résout pas**, dont 46 en `(RSP)` |
| 12 | résolus |

L'hypothèse de départ — « l'index filtre les `RSP` » — était fausse. Le module
ne filtre rien par type de procédure. Il lit un périmètre, et ce périmètre
n'avait qu'une source : les amendements. Les 10 dossiers `RSP` qui figuraient
déjà dans l'index y étaient entrés **par la bande**, parce qu'un amendement les
visait.

## Décision

`references_visees()` lit les deux sources : le `texte_vise` d'un
`amendement_non_resolu` européen, et la `reference_dossier` d'un `textes_portes[]`
européen. Même critère de tri dans les deux cas — `institution ==
"parlement_europeen"` —, et l'union est dédupliquée.

Mesuré sur le corpus au 16/09/2026, dump `ep_dossiers` du cache :

| | Avant | Après |
| --- | ---: | ---: |
| Références visées | 367 | **401** |
| Dossiers dans l'index | 355 | **389** |
| Textes portés qui résolvent | 12 | **66** |
| Entrées sans commission **ni motif** | 0 | **0** |

Les 12 références encore non résolues sont celles de 2024-2025 déjà connues : le
dump des dossiers est plus ancien que celui des amendements. Absence datée, pas
un trou.

## Ce que ce lot n'apporte pas, et il faut le dire avant qu'une figure soit dessinée

**Élargir le périmètre n'élargit pas l'axe « commission ».** Sur les 34 dossiers
entrés, **4** portent une commission au fond — INTA (×2), AGRI, ECON, LIBE. Les
30 autres sont des `RSP`, et une résolution d'actualité n'a pas de commission
saisie au fond chez la source : ce n'est pas une lacune de collecte, c'est la
nature de la procédure.

Ce que l'extension apporte réellement à une fiche est le **stade procédural** de
54 textes, et un identifiant publié qui résout. Une figure « par commission » sur
une fiche candidat porterait, après ce lot, sur 16 références sur 43 — pas sur
les 694 textes.

## Alternative écartée

**Ajouter les `RSP` par un filtre de type de procédure sur le dump.** C'est ce
que la demande décrivait, et cela aurait marché — en faisant entrer des dossiers
que personne ne cite, et en laissant le vrai défaut en place : les `COD`, `DEA`
et `INS` cités par un texte porté seraient restés non résolus. Le périmètre doit
suivre ce que le corpus cite, pas une liste de types.
