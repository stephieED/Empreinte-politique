# Un agrégat de fiche ne compte que la période de la fiche (#821)

`2026-09-10`

> **En bref** — `_aggregate_amendements` parcourait l'`amendements[]` des membres **sans aucun filtre** : `LR-16` publiait 159 274 amendements dont **32 277 seulement** déposés sous la XVIe, et **20 501 venaient de la XVIIe**, c'est-à-dire d'après la dissolution du 9 juin 2024, sous un groupe qui n'existait plus — 20 % dans la période pour `LR-16`, 26 % pour `SOC-16`, 46 % pour `RN-16`, si bien que **les chiffres publiés n'étaient même pas comparables entre eux** ; c'est le filtre de #403 pour les votes (« un scrutin serait attribué à un groupe qui n'existait pas au moment du vote »), jamais transposé, **quatrième occurrence de la semaine** après #657, #817 et #683 ; la législature se lit sur l'identifiant (`AMANR5L16…`), donnée **structurelle** jamais déduite d'une date, un identifiant qui ne la porte pas est **retenu** et compté à part (§2 règle 5), et le filtre ne s'arme que si l'appelant nomme une législature ; **une signature n'est pas un amendement, et le compteur a dû l'apprendre** — la première version nommait « amendements » ce qui s'incrémente une fois par signataire : **657 996 signatures écartées pour 126 997 amendements distincts** sur `LR-16`, la confusion même que #643 a corrigée et que §6 verrouille, défaut vu en lisant la sortie réelle et non en relisant le code. Effet vérifié en rejouant la génération : 159 274 → **32 277**, exactement le chiffre mesuré indépendamment avant d'écrire une ligne, et `taux_adoption` bouge de 0,0424 à 0,0354 — il était lui aussi calculé hors période. **Non corrigé ici** : `tags_thematiques_agreges` a le même défaut (26 % des interventions de `REN-16` dans la période) mais `tags_thematiques` est une liste de chaînes **sans provenance** — un lot à part. **Écarté** : filtrer sur l'appartenance réelle, parce que #809 a établi que ces bornes sont une enveloppe. Suite complète à 4 376, 0 échec.

## Contexte

Trouvé en instruisant une question de la session UI sur l'agrégation par
lignée. Le défaut est **sur les fiches déjà publiées**, et il n'a rien à voir
avec la lignée.

`_aggregate_amendements` parcourt l'`amendements[]` de chaque membre **sans
aucun filtre de législature ni de période**. Un membre présent sous plusieurs
législatures apporte donc à la fiche tout ce qu'il a déposé ailleurs.

Mesuré le 10/09/2026 sur `origin/main`, la législature lue dans l'uid
(`AMANR5L<leg>…`) :

| Fiche | Publié | XIVe | XVe | **XVIe** | XVIIe | Dans la période |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `LR-16` | 159 274 | 30 353 | 76 143 | **32 277** | 20 501 | **20 %** |
| `SOC-16` | 56 895 | 9 789 | 19 570 | **14 998** | 12 538 | **26 %** |
| `RN-16` | 37 812 | — | 5 783 | **17 520** | 14 509 | **46 %** |

`LR-16` publiait **20 501 amendements de la XVIIe** — déposés après la
dissolution du 9 juin 2024, sous un groupe qui n'existait plus.

## C'est le défaut que #403 a corrigé pour les votes

`_votes_de_legislature` filtre, et sa docstring dit pourquoi :

> Sans ce filtre, la cohésion d'un groupe de la 16e agrégerait les scrutins de
> la 17e dès qu'un membre y siège encore — **un scrutin serait attribué à un
> groupe qui n'existait pas au moment du vote**.

Le raisonnement n'avait jamais été appliqué aux amendements. Quatrième
occurrence du motif « ce motif est devenu faux » cette semaine, après #657
(interventions), #817 (textes portés) et #683 (lecture des dumps).

## Décision

**Le filtre est celui de #403, transposé.** La législature se lit sur
l'identifiant (`AMANR5L16…`) : c'est une donnée **structurelle**, écrite par
l'Assemblée, jamais déduite d'une date.

Trois propriétés qui ne vont pas de soi.

**Un identifiant qui ne porte pas de législature n'est PAS écarté.** Rien ne
prouve qu'il soit hors période, et l'écarter ferait passer une ignorance pour un
fait (§2 règle 5). Il est retenu, et compté à part.

**Le filtre ne s'arme que si l'appelant nomme une législature.** Un profil lu
isolément — le chemin des tests, et celui d'un consommateur hors fiche — garde
tout. La fiche seule sait de quelle période elle parle.

**Ce qui est écarté se publie**, sans quoi la fiche afficherait un chiffre plus
petit qu'avant sans dire pourquoi : une exclusion muette transforme un
dénominateur en donnée fausse (§2 règle 7).

## Une signature n'est pas un amendement, et le compteur a dû l'apprendre

La première version nommait ces exclusions « amendements ». C'est faux : le
compteur s'incrémente une fois par **entrée** d'`amendements[]`, donc une fois
par signataire. Sur `LR-16`, **657 996 signatures** écartées pour **126 997
amendements distincts**.

Les publier sous le mot « amendements » aurait reproduit exactement la confusion
que #643 a corrigée, et que §6 verrouille — « les signatures se publient sous
`amendements_agreges.signatures`, jamais sous le mot amendements ». D'où
`nb_signatures_hors_periode_ecartees` et
`nb_signatures_sans_legislature_retenues`.

Le défaut a été vu en lisant la sortie réelle, pas en relisant le code : c'est
l'écart entre 657 996 et 126 997 qui l'a trahi.

## Effet vérifié

`generate_group_profiles.py` rejoué sur `LR-16` :

| | Avant | Après |
| --- | ---: | ---: |
| `nb_amendements` | 159 274 | **32 277** |
| `nb_adoptes` | 6 752 | 1 142 |
| `taux_adoption` | 0,0424 | **0,0354** |
| signatures écartées | — | 657 996 |

Le chiffre obtenu est **exactement** celui mesuré indépendamment sur les uid
avant d'écrire une ligne. Et `taux_adoption` bouge : le taux publié était
lui aussi calculé sur une population hors période.

## Ce que ce lot ne fait pas

**`tags_thematiques_agreges` a le même défaut, et il n'est pas corrigé ici.**
Vérifié : `aggregate_tags_thematiques(profils)` ne reçoit ni législature ni
période. Mesuré sur 40 membres de `REN-16` : leurs interventions se répartissent
en 36 264 (XVe), 14 172 (XVIe), 5 477 (XVIIe) — **26 %** seulement relèvent de
la fiche.

Il n'est pas corrigé parce qu'il est **plus difficile**, et pour une raison de
fond : `tags_thematiques` est une liste de **chaînes**, sans provenance. Filtrer
demanderait soit d'y porter l'origine de chaque étiquette, soit de recalculer
l'agrégat depuis les interventions. Les deux sont des lots à part entière.

Le run en cours multiplie ces étiquettes par vingt sur certaines fiches
(`ECOLO-16` 64 → 1 306) : le défaut y gagne en visibilité, pas en gravité.

## Alternative écartée

**Filtrer sur l'appartenance réelle au groupe** (`membres[].debut_dans_groupe` /
`fin_dans_groupe`) plutôt que sur la législature. Plus juste en théorie, et
écarté pour une raison mesurée : #809 a établi que ces bornes sont une
**enveloppe**, pas les périodes réelles — 33 membres publiés sur 8 fiches ont
une interruption masquée, jusqu'à 571 jours, dont 23 correspondent à des
fonctions gouvernementales. Filtrer sur une enveloppe ferait entrer dans
l'agrégat ce qu'un ministre a déposé pendant qu'il n'était pas au groupe.

La législature, elle, est portée par l'identifiant et ne dépend d'aucune de nos
lectures.
