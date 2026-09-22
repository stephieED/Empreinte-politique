<a id="mandats-agreges-par-appartenance-853"></a>
# Les mandats agrégés d'un groupe sont ceux exercés pendant l'appartenance (#853) (2026-09-22)

`2026-09-22`

> **En bref** — `mandats_agreges` filtrait un mandat sur le seul mandat électif du membre : la carrière entière passait, un groupe d'amitié de 2012 comptait pour un groupe de 2024. Il est désormais borné sur `membres[].periodes`, comme la parole (#1073) : 82 846 → 44 891 entrées sur les 29 fiches AN.

## Constat

Ouvert le 11/09/2026 : 38 835 des 82 233 entrées membre × mandat des 28 fiches
AN n'avaient aucun jour commun avec l'appartenance du membre. Cas réel : Gérald
Darmanin, dans EPR du 19/07/2024 au 23/01/2025, y comptait son groupe d'amitié
France-Ukraine de 2012-2016 — il était député à l'époque, et c'était le seul
filtre (`_member_eligibility_intervals`).

## Décision

Un mandat catégoriel compte s'il chevauche **une période d'appartenance** du
membre (`periodes_d_appartenance`, #1073), en plus du mandat électif. Un membre à
l'appartenance non datée garde le seul filtre électif (§2 règle 5). Les dates
publiées restent celles du mandat. La lignée hérite du bornage par fusion des
fiches.

Tranché d'avance par l'issue et par l'arbitrage du 22/09/2026 sur la parole
(option A, même règle pour tous les agrégats d'une fiche) : borner sur
`periodes` (#809), pas sur l'enveloppe `debut_dans_groupe`/`fin_dans_groupe`.

## Mesuré sur le corpus publié (22/09/2026, recalcul local, 29 fiches AN)

| | Avant | Après |
| --- | ---: | ---: |
| Entrées membre × mandat | 82 846 | 44 891 |
| Membres siégeant à la date de référence (somme) | 30 406 | 30 406 |

Le second compte ne bouge nulle part, et c'est la vérification : un membre
présent à la date de référence y appartient au groupe, donc un mandat ouvert à
cette date chevauche son appartenance. Seul le cumul historique perd la
carrière. Exemples : EPR-17 896 → 388 instances, LR-15 1 400 → 608, LAREM-15
13 231 → 8 727 entrées.

`nb_membres_cumul_historique` change de sens : il compte ceux passés par
l'instance **pendant** qu'ils étaient du groupe.

## Contrôle de perte

`mandats_agreges` est une liste stable du contrôle de perte : le premier run
après ce lot se lance avec `allow_declared_losses=true`, comme pour #1073.

## Alternative rejetée

**Borner sur l'enveloppe** `debut_dans_groupe`/`fin_dans_groupe` : un membre
parti puis revenu y compterait les mandats de son absence.
