# Drees et Unédic — les comptes des caisses sociales

> **Statut : vivante — collectée par le job `extract-finances-etat` depuis #1053**
> (12/10/2026). `src/finances_sociales.py` relit tout à chaque run ;
> `raw_data/finances_sociales.json` apparaît au premier run qui suit la publication
> du workflow. **Rien n'en est encore publié sur le site.** Ce fichier décrit ce que
> les **fournisseurs** publient, et dérive avec eux, non avec notre code.

## Producteurs et licence

Deux producteurs, deux portails sous Opendatasoft, lus sans clé :

| Producteur | Portail | Jeu lu | Licence relevée sur le jeu |
| --- | --- | --- | --- |
| **Drees**, service statistique du ministère de la Santé | `data.drees.solidarites-sante.gouv.fr` | `305_les-comptes-de-la-protection-sociale` | Licence Ouverte v2.0 (Etalab) |
| **Unédic** | `data.unedic.org` | `financement-de-l-assurance-chomage` | Licence Ouverte v2.0 |

Attribution seule, pas de partage à l'identique. Relevé le 12/10/2026 **sur chaque
jeu**, pas sur les portails. L'étiquette canonique est
`licences.LICENCE_FINANCES_SOCIALES`, jamais recopiée en dur (AGENTS.md §7).

## Ce que les fournisseurs publient

### Drees — le classeur joint au jeu

`La protection sociale en France de 1959 à 2024.xlsx`, douze feuilles : deux de
notice, cinq « opérations » (emplois et ressources), cinq « prestations » (par
risque). Les cinq feuilles d'opérations sont lues :

| Feuille | Champ, tel que le sommaire du classeur le nomme | Années | Lignes |
| --- | --- | --- | --- |
| `opérations_1959_2024` | l'ensemble des régimes | 1959 à 2024 | 20 |
| `opérations_ASSO` | les administrations de sécurité sociale | 2020 à 2024 | 18 |
| `opérations_APUC_APUL` | les administrations publiques centrales et locales | 2020 à 2024 | 12 |
| `opérations_SF_SNF` | les sociétés financières et non financières | 2020 à 2024 | 10 |
| `opérations_ISBLSM` | les instituts sans but lucratif au service des ménages | 2020 à 2024 | 5 |

Les ressources par nature : cotisations sociales d'employeurs, de salariés, autres
cotisations, cotisations imputées, impôts et taxes affectés, contributions
publiques, produits financiers, autres recettes, recettes du compte de capital.
Un bloc ne porte que les lignes qui le concernent. Montants en millions d'euros,
**hors transferts** : ce qu'un bloc reverse à un autre n'y figure pas.

**Les quatre blocs font l'ensemble.** Vérifié le 13/10/2026 sur les 20 lignes et
les cinq années 2020 à 2024 : pour chaque ligne, la somme des blocs vaut la ligne
de l'ensemble — c'est ce qui permet de dire quel bloc reçoit quelle ressource. Une
exception, en 2024 : 7 537 M€ de cotisations de salariés sont sur leur ligne dans
un bloc et fondus dans la ligne « employeurs » de l'ensemble ; les deux écarts
s'annulent, et le total des ressources, lui, se recoupe.

Vérifié aussi sur toutes les années des cinq feuilles : le total des ressources
hors transferts vaut la somme des lignes qui le suivent, à moins de 2 M€.

L'en-tête de chaque colonne colle l'année à son statut : `2022DEF` (définitif),
`2023SD` (semi-définitif), `2024PROV` (provisoire).

### Drees — l'API du même jeu

15 654 enregistrements : les **prestations** par année, par poste de la
nomenclature (`ps_niveau`, `ps_code`, `ps_lib`, `risque`) et par régime
(`si_niveau`, `si_code`, `si_nom`, `nom_regime`), montant dans `val`. Seul le
niveau 0 des postes est lu — le total de chaque régime : 1 764 enregistrements,
66 années. En 2023 : un ensemble, 9 secteurs, 34 régimes, dont les caisses
nationales (vieillesse, maladie, allocations familiales, autonomie), l'Unédic, les
retraites complémentaires des salariés.

**L'API ne porte aucune ressource** : uniquement des prestations.

### Unédic — un jeu, une ligne par année

Quinze années, de 2011 à 2025, en millions d'euros. Recettes : total,
contributions principales, CSG, autres. Dépenses : total, allocations et aides,
retraites, activité partielle, financement de France Travail et frais de
recouvrement, autres. Puis solde technique, éléments exceptionnels, solde
financier, dette. Vérifié sur les quinze années : chaque total vaut la somme de ses
lignes à moins de 2 M€.

## Ce qu'aucune des deux ne publie

**Les ressources caisse par caisse** — vieillesse, maladie, famille, retraites
complémentaires. Le classeur les donne par bloc, et le bloc des administrations de
sécurité sociale réunit toutes les caisses, Unédic et retraites complémentaires
comprises, sans les séparer ; l'API ne porte que des prestations ; seule l'assurance chômage a ses deux côtés. Ce détail existe
sans doute dans les annexes des lois de financement de la Sécurité sociale, **non
ouvertes** à la date de ce relevé.

## Les pièges

- **Le classeur change de nom, donc d'identifiant de pièce jointe, à chaque
  édition.** Le retrouver dans la fiche du jeu (`attachments`), par son type. La
  feuille de l'ensemble des régimes porte ses bornes dans son nom et le changera
  aussi.
- **La dernière année est provisoire et moins détaillée.** En 2024, les trois
  cotisations effectives tiennent sur la seule ligne « employeurs » (482 239 M€
  pour l'ensemble des régimes) ; « salariés » et « autres » sont vides. De même les
  prestations en espèces et en nature. Une cellule vide n'est pas un zéro.
- **Les lignes changent de définition dans le temps**, et le disent dans leur
  libellé : « Frais financiers (depuis 1981) », « Recettes du compte de capital
  (depuis 2006) ». Les impôts et taxes affectés sont vides en 1959.
- **Les prestations par régime ne sont complètes que depuis 1990.** Avant 1981 la
  source ne donne que l'ensemble ; de 1981 à 1989 la somme de ses régimes est en
  dessous de son total, de 594 à 1 282 M€.
- **Le libellé du secteur `S13141` est « Régime général de la Sécurité sociale »**
  alors qu'il regroupe aussi l'Unédic et les retraites complémentaires. Se fier au
  code et au nom du régime, pas à ce libellé.
- **Les régimes changent de nom** : les deux associations de retraite
  complémentaire des salariés sont séparées jusqu'en 2017 et réunies ensuite ; la
  caisse de l'autonomie n'apparaît qu'en 2021.
- **La CSG de l'assurance chômage est vide avant 2019**, pas nulle : elle remplace
  alors la part salariale des contributions.
- **Le serveur compresse sans le dire**, comme `data.economie.gouv.fr` : regarder
  les premiers octets.

## Écarté

Le jeu `encaissements-annuels-des-urssaf` du portail de l'Urssaf porte les
cotisations encaissées, mais sous **ODbL** (partage à l'identique), et n'avait pas
été modifié depuis 2023 au 12/10/2026. Non lu.
