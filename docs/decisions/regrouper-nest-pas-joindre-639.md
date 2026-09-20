<a id="regrouper-nest-pas-joindre-639"></a>

# Regrouper des faits d'une même source n'est pas les joindre entre sources (#639, #594) (2026-08-31)

`2026-08-31`

> **En bref** — le lien vote → loi existe et se lit (99,4 % des 17 748 scrutins portent un intitulé de texte, pour 1 229 textes distincts) ; ce qui manque est un identifiant, et la distinction sépare deux gestes — regrouper des chaînes d'une même source est permis, décréter qu'un scrutin et un amendement visent le même dossier est une affirmation qu'aucune source ne fait ; corollaire, le rattachement des scrutins attend que `scrutins.json` sache porter une borne datée, l'AN ne renseignant son `dossierRef` que depuis mars 2026 (0 avant, 100 % après, sur les 8 434 scrutins de la XVIIe).

Sortie du temps 2 de l'épic #324. La règle décide de ce qu'une vue peut afficher
**aujourd'hui**, sans clé et sans collecte — et de ce qui, au contraire, exige un
identifiant que la source pose elle-même.

## Le contexte

Les quatre matières du corpus décrivent les mêmes dossiers législatifs et ne
partagent aucune clé. Mesuré le 31/08/2026, en recoupant les libellés normalisés :

| Recoupement | Libellés communs |
| --- | ---: |
| amendements ∩ scrutins | 126 sur 2 243 |
| amendements ∩ interventions | 85 |
| scrutins ∩ interventions | 29 |
| **les trois** | **13** — et ce sont tous des budgets, dont le titre est formulaire |

Le constat a d'abord été lu comme « on ne sait pas relier un vote à une loi ».
**C'est faux, et l'erreur a failli faire différer une vue qui était disponible.**

## Ce que la donnée porte réellement

Chaque scrutin porte son objet en clair : « l'ensemble du projet de loi de
finances pour 2022 ». Une reconnaissance sur ce libellé retrouve un intitulé de
texte sur **17 634 scrutins sur 17 748 (99,4 %)**, pour **1 229 textes distincts**
— un facteur 14 sur les 17 748 scrutins.

Ce qui manque n'est donc pas le lien : c'est un **identifiant que la source pose
elle-même**.

## La décision

**Deux gestes, de nature différente, et un seul est permis sans clé.**

| Geste | Statut | Pourquoi |
| --- | --- | --- |
| **Regrouper** des faits d'une **même** source par leur propre libellé | **permis** | on regroupe des chaînes identiques venant d'une seule source ; on n'affirme rien qu'elle ne dise |
| **Joindre** des faits de **sources différentes** en décrétant qu'ils visent le même objet | **interdit sans clé sourcée** | c'est une affirmation que ni l'une ni l'autre source ne fait — AGENTS.md §2 règle 2 |

Conséquence immédiate : la vue « les grandes lois » d'un profil de candidat —
grouper les votes d'une personne par le texte que le scrutin nomme — **est
disponible sans cette issue**. Le croisement inter-objets — vote ↔ amendement ↔
texte porté — ne l'est pas.

**Deux limites du regroupement, à écrire à l'écran plutôt qu'à taire :** il
**fusionne les lectures successives** d'un même texte (première lecture, CMP,
lecture définitive portent le même intitulé), et **les libellés dérivent** —
« Projet de loi de finances pour 2026 » et « Loi de finances 2020 » coexistent
dans la même source.

## Le corollaire : le rattachement des scrutins est différé, avec sa condition

L'Assemblée a **commencé** à publier un identifiant de dossier sur ses scrutins.
Mesuré sur les 8 434 scrutins de la XVIIe législature :

| Mois | Avec `objet.dossierLegislatif.dossierRef` | Sans |
| --- | ---: | ---: |
| 2025-11 | 0 | 1 117 |
| 2026-02 | 0 | 545 |
| **2026-03** | **129** | **0** |
| 2026-04 → 07 | 2 477 | **0** |

Aucune zone grise : jamais avant mars 2026, toujours après. Ce n'est ni un type de
scrutin — `SPO`, `SPS` et `MOC` se répartissent pareil des deux côtés — ni une
propriété du texte. Les votes à main levée n'y sont pour rien : ils ne sont pas
des scrutins publics et ne figurent pas dans l'archive. **C'est une évolution du
référentiel de l'AN, en cours.**

Publier ce champ ferait qu'une loi de 2023 afficherait « aucun vote rattaché »
**exactement comme** une loi sur laquelle personne n'a voté — le contresens
qu'interdit §2 règle 5.

**Condition de reprise, écrite pour ne pas devenir un transitoire permanent :**
le rattachement des scrutins se publie le jour où `pivot_data/scrutins.json` sait
porter une **borne de couverture datée**. Il n'en a aucune aujourd'hui — il porte
`schema_version`, `genere_le`, `licence_donnees` et la liste.

## L'alternative écartée

**Publier une clé dérivée du libellé**, malgré ses 99,4 %. Écartée pour trois
raisons, dont la première suffit :

1. **Ce n'est pas une clé sourcée.** Déclarer qu'un scrutin et un amendement
   visent le même dossier parce que deux chaînes se ressemblent est une
   affirmation que le corpus ne porte pas.
2. Elle **fusionne les lectures successives** d'un même texte, qu'aucun lecteur ne
   pourrait distinguer ensuite.
3. Elle **rouille** : un libellé qui change casse le rapprochement sans que rien ne
   le signale, contrairement à un identifiant absent, qui se voit.

C'est le même motif qui a fermé l'appariement par nom dans #644 — où un
rapprochement par patronyme attribuait un ministère à *Véronique* de Montchalin
pour *Amélie*.

## Ce que la règle laisse ouvert

Trois objets porteront un identifiant de dossier sourcé, sans qu'aucune borne
nouvelle soit nécessaire : les `textes[]` d'un gouvernement (**725 / 725**, déjà
publié), les `textes_portes[]` d'un profil (#639 rang 2) et les `amendements`
(#639 rang 3, **130 244 rattachés sur 484 132**). Le croisement par loi est donc
constructible sur eux trois, sans toucher aux votes — et donc sans introduire de
faux vide.

Voir [`qualification-scrutins-et-cle-dossier-639`](qualification-scrutins-et-cle-dossier-639.md)
et [`dossier-des-amendements-639`](dossier-des-amendements-639.md).
