<a id="mandats-agreges-siege-vs-passe-656"></a>
# `mandats_agreges` : « qui y siège » et « qui y est passé » sont deux nombres, pas un (#656) (2026-08-31)

`2026-08-31`

> **En bref** — `nb_membres` additionnait les passages d'un jour (43 % des 2 708 adhésions de commission publiées, un⋅e député⋅e ne siégeant qu'en une commission permanente à la fois : AMO30 écrit toute bascule temporaire comme un mandat à part entière) : deux compteurs nommés, un dénominateur publié, un tri sur « qui y siège ».

## Le défaut

`mandats_agreges[].nb_membres` additionnait toute présence, si brève soit-elle,
sur toute la période couverte par la fiche. Publier « 67 des 76 membres siègent
à la commission des finances » était faux : ils sont **5**. Et c'est bien ce que
la fiche affichait — `GroupProfile.jsx` rendait `67 / 76 membres`, le compteur
des membres siégeant n'apparaissant qu'en incise, après un point médian.

Mesuré le 31/08/2026 sur `pivot_data/groupes/groupe-AN-LFI-16.json`
(corpus régénéré le 31/08, 76 membres). « ≤ 1 jour » signifie
`fin - debut ≤ 1 jour` ; entre parenthèses, les adhésions qui commencent et
finissent le même jour :

| Commission | cumul | ≤ 1 j | 2-31 j | 32-365 j | > 365 j | fin absente | y siègent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Finances, économie générale et contrôle budgétaire | 67 | **44** (38) | 12 | 6 | 0 | 5 | **5** |
| Affaires sociales | 66 | **46** (36) | 8 | 2 | 1 | 9 | **9** |

`poids_relatif` valait 0,8816 = 67/76 pour la première ligne : le poids d'un
cumul, publié comme s'il pesait un effectif.

Ce n'est pas du bruit réparti : c'est concentré sur `commission`. Sur les
**20 527 adhésions** publiées des 7 fiches :

| Catégorie | Adhésions | dont ≤ 1 j | Part |
| --- | ---: | ---: | ---: |
| **`commission`** | 2 708 | **1 165** | **43 %** |
| `commission_enquete` | 1 838 | 87 | 5 % |
| `delegation` | 667 | 14 | 2 % |
| `mission_information` | 1 344 | 5 | 0 % |
| `groupe_amitie` | 6 491 | 3 | 0 % |
| `groupe_etudes` | 6 331 | 1 | 0 % |
| `extra_parlementaire` | 1 148 | 0 | 0 % |

**43 % contre 0 à 5 % partout ailleurs**, et c'est précisément la catégorie qui
porte le signal — le domaine de travail du groupe. Par fiche, toutes catégories
confondues : `AN:LFI` 362 / 2 384 (15 %), `AN:REN` 691 / 8 453 (8 %), `AN:SOC`
105 / 1 398 (8 %), `AN:LR` 107 / 4 865 (2 %), `AN:RN` 10 / 3 403 (0 %). L'écart
entre groupes n'est pas expliqué, et rien ici n'autorise à l'interpréter.

## La cause, cherchée dans AMO30 et trouvée

Ce n'est ni une anomalie de collecte ni une hypothèse : **un⋅e député⋅e
n'appartient qu'à une commission permanente à la fois**, si bien que le
référentiel modélise tout passage temporaire dans une autre commission comme la
**fin** du mandat en cours et le **début** d'un nouveau. Mesuré sur l'archive
`acteurs_historique_an` (les 452 acteurs AN des 7 fiches, 10 562 mandats
`COMPER`) :

| Mesure | Valeur |
| --- | ---: |
| Mandats `COMPER` de durée ≤ 1 jour | 3 389 / 10 562 (32 %) |
| … dont commençant et finissant le même jour | 2 760 (26 %) |
| Paires de mandats `COMPER` consécutifs (même acteur, même législature) | 9 511 |
| … **contiguës** (fin + 1 jour = début du suivant) | 8 864 (93,2 %) |
| … se chevauchant, **même organe** (renouvellement) | 487 |
| … se chevauchant sur des organes différents, ou sans date de fin | 54 |
| … avec un trou > 1 jour | 106 |
| Acteurs n'ayant jamais 2 commissions permanentes ouvertes le même jour | 440 / 452 |

Exemple verbatim, `PA793756` (François Piquemal), 51 mandats `COMPER` formant
une chaîne sans trou : `PO419610` (Affaires économiques) du 2026-05-12 au
2026-05-26, `PO59048` (Finances) le 2026-05-27, `PO419610` de nouveau à partir
du 2026-05-28.

**Rien dans AMO30 ne distingue le passage du siège** : `nominPrincipale` vaut
`1` dans les deux cas (3 371 des 3 389 mandats courts), et
`infosQualite.codeQualite` vaut `Membre` dans les deux cas (3 369 sur 3 389).
Aucun champ supplémentaire n'apparaît sur les mandats courts. **Seule la durée
le dit** — d'où deux compteurs, et non un filtre.

Côté fiche, la forme est la même : les 337 adhésions de commission ≤ 1 jour
d'`AN:LFI` se répartissent sur **137 dates distinctes**, jusqu'à 16 le même jour
(27/05/2026), et portent toutes la fonction `Membre`.

## Décision

`_aggregate_mandats` publie trois champs, aucun nombre unique :

| Champ | Ce qu'il dit |
| --- | --- |
| `nb_membres_actifs` | **Qui y siège** : mandat encore ouvert **et** appartenance au groupe encore active. Déjà calculé depuis [[mandats-agreges-famille-1]], jamais mis en avant. |
| `nb_membres_cumul_historique` | **Qui y est passé** : membres distincts ayant occupé ce mandat au moins une fois, adhésions d'un jour comprises. Remplace `nb_membres`, dont le nom se lisait comme un effectif. |
| `effectif_reference` | Le dénominateur des deux, `len(membres)` — la couverture disponible du groupe, jamais `meta.couverture_roster.roster_total`. |

`poids_relatif` est **retiré**. Il valait exactement `nb_membres / len(membres)`
et, une fois les deux grandeurs séparées, il ne disait plus de laquelle il était
le poids. Publier le dénominateur plutôt qu'un ratio pré-divisé et arrondi à
4 décimales est aussi ce que demande AGENTS.md §2.7 : « 5 / 76 », jamais
« 88 % ». Aucun consommateur ne le lisait.

**Le tri passe sur « qui y siège »** : `nb_membres_actifs` décroissant, puis
`nb_membres_cumul_historique` décroissant, puis `(categorie, label)`. Trier sur
le cumul faisait remonter, sur `AN-LFI-16`, la commission des finances
(5 membres siégeant, 67 passages dont 44 d'une journée ou moins) au-dessus de la
commission des affaires sociales (9 siégeant, 66 passages). Le rang de catégorie
reste le critère primaire côté interface (#382/#386) : le changement joue **au
sein** d'une catégorie.

## Ce qui a été refusé

- **Filtrer les adhésions courtes.** Une adhésion d'un jour est un fait, et
  une bascule de commission en est un aussi. L'écarter en silence recréerait
  le défaut dans l'autre sens. La durée reste lisible entrée par entrée dans
  `membres[].debut` / `fin`.
- **Publier un compteur d'adhésions courtes, ou un « taux de rotation ».** Ce
  serait un indice comparable entre groupes, donc un classement — AGENTS.md
  §2 règle 1. `tests/test_group_profile.py::test_mandats_agreges_ne_publie_aucun_taux_de_rotation`
  verrouille le jeu de clés publiées.
- **Déduire du motif un « remplacement en séance ».** La forme l'évoque ; la
  chaîne contiguë établit la bascule de commission, pas sa raison. Le
  référentiel ne le dit pas, la fiche ne le dira pas non plus.

## Effet mesuré sur les 7 fiches publiées

Le nombre d'entrées de `mandats_agreges` est **inchangé** — la liste est
surveillée par `audit_diff_profils` (`listes_stables`), une variation aurait
bloqué le commit. Seuls l'ordre et le nom des champs changent :

| Fiche | Entrées | Rangs déplacés (tri interface) | Tête de la catégorie `commission`, avant → après |
| --- | ---: | ---: | --- |
| `groupe-AN-LFI-16` | 608 | 529 | Finances (5 siégeant, 67 passages) → Affaires sociales (9, 66) |
| `groupe-AN-LR-16` | 1 109 | 1 011 | Affaires culturelles (4, 38) → Affaires sociales (6, 33) |
| `groupe-AN-REN-16` | 1 153 | 973 | Lois (9, 137) → Affaires culturelles (12, 135) |
| `groupe-AN-RN-16` | 535 | 438 | Finances (8, 33) → Affaires étrangères (13, 29) |
| `groupe-AN-SOC-16` | 615 | 582 | Affaires sociales (3, 27) → Affaires économiques (7, 27) |
| `groupe-Senat-LR` | 12 | 0 | inchangée (extraction suspendue, #516) |
| `groupe-Senat-SER` | 5 | 0 | inchangée (extraction suspendue, #516) |

## Interface

`GroupProfile.jsx` publie désormais deux lignes par carte, la seconde en gris :

```
5 / 76 membres y siègent
67 membres y ont siégé au moins une fois
```

et, quand personne n'y siège plus, `Aucun membre n'y siège actuellement`.
Numérateur et dénominateur, jamais un pourcentage seul
(`web/UI_finale/DESIGN_SYSTEM.md` §6).

## Une mesure de l'issue non reproduite

La colonne « < 1 an » de l'issue (11 pour les deux commissions LFI) ne se
reproduit sous aucune définition de bornes essayée : la ventilation mesurée
ci-dessus somme exactement au cumul (44 + 12 + 6 + 0 + 5 = 67), ce qui ne
laisse pas de place à 11. Toutes les autres mesures de l'issue sont
reproduites à l'identique.
