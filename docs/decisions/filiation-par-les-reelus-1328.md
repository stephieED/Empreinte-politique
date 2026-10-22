<a id="filiation-par-les-reelus-1328"></a>
# Deux groupes se suivent quand les réélus de l'un font l'autre : la filiation se mesure sur ceux qui pouvaient passer (#1328, 2026-10-22)

`2026-10-22`

> **En bref** — La règle qui relie un groupe à celui de la législature suivante n'est plus « la moitié du plus petit des deux » (#1168). Elle rapportait les personnes communes à tout l'effectif, départs compris, et ne voyait plus aucune continuité en 2017, quand 76 % des élus étaient nouveaux. La règle retenue (option F, arbitrée le 22/10/2026) : la moyenne harmonique de la part des réélus du premier groupe passés au second et de la part des anciens du second venus du premier, **au moins 60 %**, et **au moins 5 personnes communes**. Elle retrouve les 16 liens publiés, en ajoute 4 de la XIVe à la XVe, et n'en fabrique aucun. Le renommage dans une législature garde la règle de la moitié.

## Contexte mesuré

Ouvrir les fiches de groupe à la XIVe (#1328) a obligé à passer la règle de #1168 sur
le passage de 2012 à 2017. Mesuré le 22/10/2026 sur l'archive AMO30 courante du
19/10/2026, `groupes_amo30.deriver` sur XIV-XVII, non-inscrits exclus :

| Groupe XIVe | Groupe XVe le plus proche | Communs | Règle de la moitié (plus petit des deux) |
| --- | --- | ---: | ---: |
| `SRC`/`SER` | `NG`/`SOC` | 28 | 28/39 = 72 % — lien |
| `UMP`/`LES-REP` | `LR` | 56 | 56/120 = 47 % — **pas de lien** |
| `UDI` | `LC`/`UDI-AGIR`/… | 14 | 14/35 = 40 % — **pas de lien** |
| `GDR` | `GDR` | 6 | 6/15 = 40 % — **pas de lien** |

La cause est le renouvellement. Part des députés élus en juin qui n'étaient pas
députés sous la législature précédente, dans la même archive (mandats `ASSEMBLEE`
ouverts en juin de l'année d'élection — plus de 577, quelques segments et suppléants
y entrent ; l'ordre de grandeur tient) : 36 % en 2007, 43 % en 2012, **76 % en
2017**, 52 % en 2022, 33 % en 2024. Une règle qui compte les partants contre les
groupes qui se continuent ne voit plus la continuité quand les partants sont trois sur
quatre.

## Décision

Pour un groupe A de la législature L et un groupe B de L+1 :

- **communs** : les personnes membres des deux (organes renommés réunis) ;
- **réélus** de A : ses membres qui siègent dans un groupe de L+1 ;
- **anciens** de B : ses membres qui siégeaient dans un groupe de L ;
- le lien existe si `2 × communs / (réélus + anciens) ≥ 60 %` — la moyenne harmonique
  de communs/réélus et communs/anciens, comparée en entiers (`10 c ≥ 3 (r + a)`) —
  **et** si `communs ≥ 5`.

Plusieurs couples peuvent passer pour un même groupe : une fusion ou une scission à
parts comparables reste représentable.

Code : `groupes_config.filiation_atteinte` et `mesure_de_filiation`, appelés par
`groupes_amo30.deriver_filiations` (la dérivation), `groupes_amo30.mesurer_liens` (la
mesure écrite dans la table du run, `succede_a_mesures` = `{groupe_id, communs,
reelus, anciens}`) et `audit_filiation_lignees.mesurer_couple` (l'audit).

**Le résultat**, même archive :

| Passage | Liens | Écart avec la règle de la moitié |
| --- | --- | --- |
| XIVe → XVe | `SRC` → `SOC` (67 %), `UMP` → `LR` (93 %), `UDI` → `UDI` (74 %), `GDR` → `GDR` (100 %) | + 3 |
| XVe → XVIe | les 6 publiés, de 89 à 96 % | aucun |
| XVIe → XVIIe | les 10 publiés, de 86 à 100 % | aucun |

Couples écartés, du plus haut au plus bas : `EDS` → `ECOLO` (3 communs, 86 %, sous le
plancher), `SER` → `LAREM` (26 communs, 57 % : une scission, pas une continuation),
`LT` → `LIOT` (54 %), `R-UMP` → `LR` (47 %), `UDI-I` → `LIOT` (44 %), `AGIR-E` →
`HOR` (43 %). **Aucune lignée publiée ne bouge.**

**Le seuil et le plancher.** Les liens validés sont tous à 86 % ou plus, le plus haut
écarté à 57 %. Pour que les quatre liens de la XIVe passent sans faux lien, le seuil
devait tomber entre 58 et 67 %. La propriétaire : « non 60%. 62% dans la méthodo aura
l'air trop arbitraire ». Le plancher sépare `GDR` → `GDR` (6 communs, à garder) de
`EDS` → `ECOLO` (3) ; 4, 5 et 6 donnaient le même résultat — « oui, 5 ».

**Ce qui ne change pas.** Le renommage dans une législature (deux organes contigus)
garde la moitié du plus petit des deux (`audit_filiation_lignees.atteint_le_seuil`) :
il n'a pas de renouvellement à neutraliser. Un lien déclaré dans une même législature
(un renommage écrit comme une succession) est mesuré de même, `{groupe_id, communs,
base}`. Une table du run publiée avant ce lot porte encore `{communs, base}` ; elle se
charge, et se lit sous la règle qui l'a écrite, jusqu'au run suivant qui la réécrit.

## Alternatives écartées

Toutes mesurées le 22/10/2026 sur la même archive (détail dans #1328).

| Option | Ce qu'elle donnait | Pourquoi écartée |
| --- | --- | --- |
| A. La règle de la moitié | 1 lien XIVe → XVe | `LES-REP` 2012-2017 hors de la lignée LR |
| B. La part des seuls réélus | 6 liens | relie à tort `ECOLO` et `RRDP` de la XIVe à `LAREM` (5 réélus sur 5, sur 10) |
| C. Des fiches XIVe sans lignée | 0 lien | sept fiches sans suite pour quatre groupes qui se continuent |
| D. Les liens de 2017 écrits à la main | 4 liens | une exception pour un seul passage, contre « aucun lien écrit à la main » |
| E. Le premier choix mutuel (matrice de transition) | 4 liens + 2 en XVe → XVIe | un seul successeur par groupe, et `UDI-I` → `LIOT` aurait réuni deux lignées publiées (#836) |
| G. Le parti de rattachement financier (`PARPOL`) | — | `DEM`, `HOR` et `RE` (XVIe) tous rattachés à `ENSEM` ; l'UDI change de code (`URCID`, `UDRL`) |
| Toute une lignée plutôt que le groupe suivant | 57 communs `LES-REP` → lignée LR, contre 56 → `LR`-15 | en 2017 les sortants ont quitté l'Assemblée, ils n'ont pas changé de groupe |

Wikidata : la propriété « remplace » (`P1365`) manque pour les groupes (#1168).

## Ce qui n'a pas été vérifié

- La règle n'a été mesurée que de la XIVe à la XVIIe. Les législatives de 2027 en
  seront le premier passage nouveau.
- La phrase de la méthodologie publiée sur le site dit encore la règle de la moitié :
  elle est à réécrire côté interface.
