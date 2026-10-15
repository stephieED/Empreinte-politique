<a id="type-de-resolution-affiche-1276"></a>

# Le type d'une résolution remplace la mention générique, à la même place (#1276) (2026-10-15)

`2026-10-15`

> **En bref** — la collecte lit depuis le 12/10/2026 le type de chaque proposition de résolution de l'Assemblée (`type_resolution`, PR #1277). L'interface l'affiche **à la place** de « Résolution (prise de position ou demande procédurale) », sur la ligne grise de la liste des textes, et en tête de la bulle des carrés — fiche candidat et fiche de groupe. **Variante A**, choisie par la propriétaire le 15/10/2026 sur trois variantes posées dans la fiche réelle de Jean-Luc Mélenchon. **Aucun compte ne change** : une demande de commission d'enquête n'est pas montrée à part (arbitré le même jour). Un type que la source ne donne pas garde la mention générique.

Ancres : `LIBELLE_TYPE_RESOLUTION`, `libelleRoleTexte`, `faitDuTexte`, `textesDuMaillon`.

## Contexte

Une demande de commission d'enquête se publiait par son seul objet (« Groupuscules
d'extrême droite en France »), et se lisait comme un texte sur le fond. La mention
générique énumérait les deux procédures possibles sans trancher.

Mesuré sur `main` le 15/10/2026, lignes de textes affichées par défaut (examen en
commission au moins) sur les 36 profils de candidats déclarés du dépôt : 10 résolutions
de l'article 34-1, 6 sur des travaux européens, 5 demandes de commission d'enquête.

## Décision

| Type (`KNOWN_TYPES_RESOLUTION`) | Libellé |
| --- | --- |
| `article_34_1` | Résolution exprimant un avis de l'Assemblée |
| `travaux_institutions_europeennes` | Résolution sur un texte européen |
| `creation_commission_d_enquete` | Demande de commission d'enquête |
| `modification_reglement_an` | Modification du Règlement de l'Assemblée |
| `mise_en_accusation_president` | Proposition de destitution du Président |
| `suspension_de_poursuites` | Demande de suspension de poursuites |
| `propositions_d_actes_communautaires` | Résolution sur un projet d'acte européen |

Sur la fiche de groupe, la ligne grise ne portait aucun rôle ; elle porte désormais
le type d'une résolution quand il est connu, et rien de plus pour les autres textes.

## Alternatives écartées

- Montrer les demandes de commission d'enquête à part, hors du compte des
  propositions : refusé par la propriétaire.
- Le type au-dessus du titre en petites capitales (B), ou devant le titre (C) :
  écartés sur la maquette ; la place de la mention générique existait déjà.
