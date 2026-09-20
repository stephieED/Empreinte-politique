<a id="trois-saisines-au-fond-europeennes-901"></a>
# Les quatre saisines au fond européennes se distinguent, elles ne se fondent pas (#901) (2026-09-14)

`2026-09-14`

> **En bref** — « Responsible Committee », « Former Responsible Committee »,
> « Joint Responsible Committee » et « Former Joint Committee Responsible » sont
> quatre faits différents. Les écraser publierait comme compétente une commission
> **dessaisie** et effacerait qu'une saisine est **partagée**. Le verbatim reste
> dans `type_source` ; un `statut` fermé le lit, pour qu'aucun consommateur n'ait
> à reconnaître une chaîne anglaise. Et les 14 dossiers sans commission nommée se
> séparent en **8 + 6** : la source n'en publie aucune, ou elle affirme une
> saisine conjointe sans nommer personne.

## Contexte

`dossiers_europeens.json` (#901) publie la commission saisie au fond d'un dossier
européen — le fait équivalent, côté UE, à ce que `commissions_dossiers.json`
porte pour l'Assemblée (#328). Le champ lu est `committees[].type` et non
`responsible: true`, renseigné sur 2,9 % des entrées seulement.

La première version conservait le libellé verbatim dans `type_source` et s'en
tenait là. L'interface a alors demandé de pouvoir répondre à trois questions
sans inférence : quelle commission est compétente **aujourd'hui**, sont-elles
**deux** à l'être, et une commission l'a-t-elle été **sans l'être encore**.

## Ce que la source porte

Mesuré le 14/09/2026 sur les **355 dossiers de l'index** (population : les
références que les amendements européens de nos profils citent, pas les 23 885
dossiers du dump).

| Libellé `committees[].type` | Entrées de la source | Entrées publiées |
| --- | ---: | ---: |
| `Responsible Committee` | 326 | 326 |
| `Former Responsible Committee` | 40 | 40 |
| `Joint Responsible Committee` | 34 | 31 |
| `Former Joint Committee Responsible` | 2 | 4 |

Les deux colonnes ne coïncident pas parce qu'une entrée de la source porte zéro,
un ou plusieurs sigles, aplatis à la publication. **Deux populations, deux
chiffres, tous deux justes** — et c'est la même prudence qui sépare les 347
dossiers dont le *dump* porte une entrée au fond des 341 dont l'*index publié*
nomme au moins une commission.

## Décision

1. **Les quatre libellés se distinguent.** `type_source` garde le verbatim.

2. **`statut` est ce verbatim lu**, en vocabulaire fermé
   (`KNOWN_STATUTS_COMMISSION_AU_FOND`) : `au_fond`, `au_fond_conjointe`,
   `ancienne_au_fond`, `ancienne_au_fond_conjointe`. Sans lui, chaque
   consommateur referait une reconnaissance de chaîne sur de l'anglais pour
   savoir si la commission est compétente — une règle éditoriale recopiée dans
   l'interface est une règle qui divergera.

3. **Un libellé que la table ne connaît pas n'est ni deviné ni jeté** :
   `statut: null` **avec** `statut_non_resolu.valeur`, l'entrée restant publiée.
   Contenir « responsible » est un fait de la source ; le classer est notre
   affirmation. Zéro cas aujourd'hui — c'est un compteur-témoin.

4. **Une liste vide ne dit pas pourquoi elle est vide.**
   `commissions_au_fond_non_resolu.motif` est non nul si et seulement si la liste
   l'est — même contrat que `sort_non_resolu` (#747) :

   | Motif | Dossiers | Ce que c'est |
   | --- | ---: | --- |
   | `source_sans_commission_au_fond` | 8 | le dump ne porte aucune entrée au fond |
   | `saisine_conjointe_sans_commission_nommee` | 6 | la source **affirme** une saisine conjointe et laisse `committee` à la liste vide |

   Un **troisième** cas se lit à l'absence d'entrée dans l'index : la référence
   était citée mais introuvable dans le dump. Rien n'est fabriqué pour elle.
   341 + 6 + 8 = 355.

## L'argument qui a emporté l'arbitrage

**La réversibilité ne joue que dans un sens.** Fondre les quatre libellés plus
tard, à l'affichage, restera toujours possible ; re-séparer ce qu'on a écrasé à
la collecte ne l'est pas. Quand le coût d'une erreur est asymétrique, on retient
la forme qui garde l'autre option ouverte.

## Alternative rejetée

**Un booléen `au_fond`.** Il répondait à la première question et effaçait les
deux autres : une commission dessaisie serait devenue compétente, et une saisine
partagée aurait disparu — une compétence que la source n'établit pas
(`AGENTS.md` §2 règle 2). Les 6 dossiers à saisine conjointe sans nom se
seraient lus comme les 8 sans commission du tout.

## Ce que ça n'est pas

Ce statut **ne classe ni ne hiérarchise** : il recopie une qualification que le
Parlement européen publie lui-même, comme `position_politique` recopie celle de
l'Assemblée (#686). Aucun score, aucun rang (§2 règle 1).
