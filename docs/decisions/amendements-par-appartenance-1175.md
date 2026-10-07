<a id="amendements-par-appartenance-1175"></a>
# Les amendements d'un groupe sont ceux que ses membres ont signés pendant qu'ils y siégeaient (#1175) (2026-10-06)

`2026-10-06`

> **En bref** — l'agrégat d'amendements d'une fiche de groupe n'était borné qu'à la **législature** : Écologie Démocratie Solidarité, qui a vécu cinq mois de 2020, publiait **25 903** amendements — ceux que ses 17 membres ont signés de 2017 à 2022 — pour **1 332** déposés pendant qu'ils y siégeaient. Arbitrage de la propriétaire, 06/10/2026 : la règle de la cohésion (#1218) et de la parole (#1073) s'applique aux amendements — une signature compte si l'amendement a été déposé **un jour où son signataire appartenait au groupe**. Simulé sur les 31 fiches de groupe de l'Assemblée : 784 395 amendements publiés deviennent 615 799 ; 13 fiches baissent de plus de 10 %, 9 ne bougent pas.

## 1. Le constat

Relevé de l'issue (02/10/2026), remesuré le 06/10 sur le privé `95fcbfaff`.
`contribution_amendements` écartait une signature dont l'amendement portait une
autre législature que la fiche (#821), et rien d'autre. Un membre passé par deux
groupes dans la législature versait donc tous ses amendements aux deux, et un
groupe né en cours de législature héritait de ce que ses membres avaient signé
avant lui, et après.

La parole (#1073) puis la cohésion (#1218) suivent l'appartenance de chaque
membre. La fiche décrivait deux populations.

## 2. La décision

1. `contribution_amendements` reçoit `periodes`, les périodes d'appartenance du
   membre au groupe de la fiche. Une signature est retenue si la **date de
   dépôt** de l'amendement — `date`, dans l'index des amendements — tombe dans
   l'une d'elles, bornes incluses.
2. **La borne s'applique au chargement** (`load_profil_from_file(…,
   periodes=…)`), parce que c'est là que les entrées d'un membre sont réduites à
   des compteurs (#635) : après, plus rien ne les date. Les périodes sont donc
   lues sur l'entrée du roster (`periodes_depuis_appartenance`), avant que
   `membres[]` existe — même contenu que `periodes_d_appartenance`, un test
   tient l'égalité.
3. Un amendement cosigné reste **un** (#643) : il entre par n'importe quel
   signataire qui siégeait au groupe ce jour-là.
4. **Sans date, la signature est gardée**, et comptée
   (`nb_signatures_sans_date_retenues`). 14 amendements sur 693 387 n'ont pas de
   date dans l'index. Une **appartenance non datée** ne filtre rien non plus :
   on n'exclut personne sur une date qu'on n'a pas (§2 règle 5).
5. Ce qui est écarté se publie : `nb_signatures_hors_appartenance_ecartees`, et
   un avertissement dans `meta.warnings` — des signatures, jamais des
   « amendements » (§6).
6. La fiche de **lignée** suit : l'union des périodes du membre dans les
   maillons d'une même législature, la table que sa parole lit déjà.

## 3. L'effet, simulé sur les 31 fiches de groupe de l'Assemblée

Les deux calculs rejoués avec le code du dépôt, l'index réel et les profils du
privé `95fcbfaff`, les périodes lues dans `membres[]`. **L'ancien calcul rejoué
rend exactement les 31 chiffres publiés**, et le nouveau rend exactement une
mesure indépendante, faite sans ce code (identifiants des profils, dates de
l'index) : la simulation mesure bien la différence entre les deux règles.

| Fiche | Publié | Après | Écart | Signatures écartées | `taux_adoption` |
| --- | ---: | ---: | ---: | ---: | --- |
| `AN-EDS-15` | 25 903 | 1 332 | −95 % | 67 673 | 0,1358 → 0,0541 |
| `AN-AGIR-15` | 24 810 | 6 647 | −73 % | 50 823 | 0,1419 → 0,1691 |
| `AN-LT-15` | 40 895 | 14 554 | −64 % | 45 530 | 0,1004 → 0,0441 |
| `AN-UDI-15` | 37 992 | 15 403 | −59 % | 48 928 | 0,0919 → 0,0567 |
| `AN-DEM-15` | 37 593 | 17 655 | −53 % | 38 965 | 0,1605 → 0,2081 |
| `AN-HOR-16` | 9 748 | 5 986 | −39 % | 5 083 | 0,1981 → 0,2496 |
| `AN-GDR-17` | 11 345 | 7 354 | −35 % | 3 991 | 0,0662 → 0,1021 |
| `AN-LAREM-15` | 89 630 | 61 772 | −31 % | 109 745 | 0,2696 → 0,3679 |
| `AN-SOC-15` | 30 300 | 21 045 | −31 % | 9 671 | 0,0596 → 0,0592 |
| `AN-LIOT-17` | 10 223 | 7 564 | −26 % | 2 739 | 0,1671 → 0,179 |
| `AN-EPR-17` | 20 284 | 16 280 | −20 % | 5 181 | 0,2079 → 0,2247 |
| `AN-HOR-17` | 8 224 | 6 705 | −18 % | 2 113 | 0,2036 → 0,2107 |
| `AN-LIOT-16` | 9 326 | 8 308 | −11 % | 1 157 | 0,0925 → 0,0758 |
| `AN-SOC-17` | 16 544 | 15 342 | −7 % | 1 342 | 0,1929 → 0,1993 |
| `AN-RN-17` | 16 778 | 16 408 | −2 % | 483 | 0,0481 → 0,0491 |
| `AN-REN-16` | 21 764 | 21 303 | −2 % | 863 | 0,2944 → 0,2965 |
| `AN-RN-16` | 17 862 | 17 520 | −2 % | 342 | 0,0152 → 0,0155 |

Moins de 1 % : `AN-LR-15` (−269), `AN-FI-15` (−154), `AN-LR-16` (−72), `AN-LFI-16` (−49), `AN-ECOLO-16` (−9). Inchangées : `AN-DEM-16`, `AN-DEM-17`, `AN-DR-17`, `AN-ECOS-17`, `AN-GDR-15`, `AN-GDR-16`, `AN-LFI-17`, `AN-SOC-16`, `AN-UDR-17`.

**`taux_adoption` bouge dans les deux sens** — LaREM 26,96 % → 36,79 %, EDS
13,58 % → 5,41 % : le groupe ne garde que ce qu'il a déposé comme groupe.

**Un écart qui n'était pas cherché.** Sur quatre fiches, le chiffre publié
comptait des signatures dont l'identifiant d'amendement ne porte pas de
législature, conservées par #821 faute de pouvoir les écarter : 3 991 sur
`AN-GDR-17`, 342 sur `AN-RN-16` et `AN-RN-17`, 154 sur `AN-FI-15`. Leur date,
elle, est connue, et elle est hors de l'appartenance : la nouvelle borne les
écarte. C'est pourquoi `AN-GDR-17` baisse de 35 % sans qu'un seul de ses membres
ait changé de groupe.

**Non simulé** : les 15 fiches de lignée. Elles passent par le même code avec
l'union des périodes ; leur chiffre se mesurera au run.

## 4. Ce que cela exige du run

**Rien de particulier.** Le contrôle de perte tient
`amendements_agreges.nb_amendements` pour un scalaire surveillé : seule la
régression renseigné → `null` bloque (`audit_diff_profils`, #649). Une baisse
ne bloque pas, et aucune fiche ne tombe à zéro. Pas de run à pertes déclarées,
à la différence de #1218.

## 5. Écarté

| Option | Pourquoi |
| --- | --- |
| Borner à la période d'existence du **groupe** | corrige EDS, pas LaREM : un membre parti en 2020 verserait encore ses amendements de 2021 |
| Filtrer après le chargement, comme la cohésion | les entrées n'existent plus : il faudrait garder 6 millions de mappings en mémoire, ce que #635 a retiré |
| Écarter les signatures sans date | 14 amendements ; les écarter ferait passer une ignorance pour un fait |

## 6. Ce qui n'est pas dans ce lot

- **La page de méthodologie** écrit qu'un amendement compte « seulement s'il a
  été déposé sous la législature du groupe » : la phrase est à réécrire, côté
  interface.
- Les `recovered_slugs` de `--merge-existing` n'ont pas de dates de roster :
  leurs amendements restent bornés à la seule législature, comme leurs votes.
- Les fiches de **gouvernement** ne sont pas concernées par ce calcul.
