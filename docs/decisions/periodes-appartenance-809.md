# L'appartenance publiée cesse d'être une enveloppe (#809)

`2026-09-10`

> **En bref** — `membres[].debut_dans_groupe`/`fin_dans_groupe` n'étaient pas les dates d'appartenance mais leur **enveloppe**, `_fusionner_periodes` recollant tous les mandats `GP` en une période : **33 membres de 8 fiches** étaient dits dans leur groupe pendant qu'ils étaient **au gouvernement**, 23 des trous coïncidant exactement avec une `fonction_gouvernementale` — Dussopt ministre du 21/05/2022 au 09/01/2024, sa fiche `REN-16` le disant présent sans interruption ; **re-mesuré ici** sur un corpus qui a gagné `LR-15` et `LAREM-15` : **48 des 1 604 couples** (acteur, groupe) ont plusieurs périodes et le plus long trou fait **1 110 jours**, pas 571. **Aucun compteur publié n'était faux** — 0 membre mal compté sur les 18 groupes — mais par **coïncidence de dates**, aucune date de référence ne tombant dans un trou : le défaut de #653 un cran plus haut, qui ne se corrige pas en espérant que ça dure. D'où `membres[].periodes[]`, et `_appartenance_couvre` exact par construction. **Le seuil de recollement ne se choisit pas, il se lit** : 67 trous d'exactement 1 jour, **0** entre 2 et 30, 48 au-delà de 31 — distribution bimodale, aucune zone grise, donc deux mandats séparés d'un jour sont un changement d'organe et au-delà une absence. L'enveloppe **reste publiée et reste le repli** pour les fiches d'avant ce lot, et la clé **n'apparaît que si la source l'a donnée** — l'écrire à `null` dirait « aucune période connue » sur un membre dont on connaît les bornes (§2 règle 5). `validate_profil_groupe` gagne sa **seule** validation de contenu d'entrée : les périodes détaillent l'enveloppe, elles ne la contredisent pas — une contradiction entre deux champs du même membre ne se rattrape nulle part en aval. **Écarté** : déclarer l'existence des trous sans les dater — 1 110 jours ne sont pas une approximation. Suite complète à 4 427, 0 échec.

## Contexte

`membres[].debut_dans_groupe` / `fin_dans_groupe` sont publiés sur chaque fiche
de groupe depuis #653. Ce ne sont pas les dates d'appartenance : c'est leur
**enveloppe**. `an_roster._fusionner_periodes` recolle tous les mandats `GP`
d'un acteur en une seule période — `min(débuts)`, `max(fins)`, `None`
l'emportant.

Ce que l'enveloppe recouvre, mesuré le 09/09/2026 : **33 membres de 8 fiches**
étaient dits dans leur groupe pendant qu'ils étaient **au gouvernement**,
jusqu'à **571 jours** masqués. 23 des 33 trous coïncidaient exactement avec une
`fonction_gouvernementale` du profil de la personne. Dussopt est ministre du
travail du 21/05/2022 au 09/01/2024 ; sa fiche `REN-16` le disait dans le groupe
du 29/06/2022 au 09/06/2024, sans interruption.

**Re-mesuré le 10/09/2026**, le corpus ayant gagné `LR-15` et `LAREM-15` depuis :
**48 des 1 604 couples (acteur, groupe)** ont plusieurs périodes, et le plus
long trou est de **1 110 jours** (`LAREM-15`, acteur `PA721872`) — pas 571.

| Fiche | Membres à périodes multiples |
| --- | ---: |
| `EPR-17` | 13 |
| `LAREM-15` | 13 |
| `REN-16` | 8 |
| `DR-17` | 7 |
| `LR-15` · `SOC-16` · `LFI-16` · `LR-16` | 2 · 1 · 1 · 1 |

## Ce qui n'était pas faux, et qu'il faut dire

**Aucun compteur publié n'était faux.** Vérifié sur les 18 groupes : 0 membre
compté dans `effectif.a_la_date_de_reference` alors qu'il n'était pas dans le
groupe à cette date.

Mais ce n'est pas une propriété du calcul : c'est une **coïncidence de dates**,
les dates de référence ne tombant dans aucun trou. Un défaut qui ne se voit pas
parce que les dates s'y prêtent est exactement ce que #653 corrigeait un cran
plus haut — et il ne se corrige pas en espérant que ça continue.

## La décision

**Publier plusieurs intervalles par membre** (piste 1 de l'issue),
`membres[].periodes[]`. La donnée exacte existe dans l'index AMO30 ;
`_appartenance_couvre` devient exact par construction.

**Écarté** : garder l'enveloppe et déclarer qu'elle comporte des trous sans les
dater (piste 2). Moins coûteux, mais un lecteur ne pourrait toujours pas dater
ce qu'il lit — et 1 110 jours ne sont pas une approximation.

**Écarté aussi** : ne rien changer et l'écrire dans la méthodologie.

## Le seuil de recollement ne se choisit pas : il se lit dans les données

Deux mandats séparés d'**un jour** sont recollés — un mandat qui finit le 15/03
et reprend le 16/03 est un changement d'organe, pas une interruption. Au-delà,
c'est une absence.

Ce seuil n'est pas un arbitrage. Mesuré sur les 1 604 couples :

| Écart entre deux mandats | Occurrences |
| --- | ---: |
| exactement 1 jour | **67** |
| 2 à 30 jours | **0** |
| 31 jours et plus | 48 |

La seule valeur sous 30 jours est `1`. La distribution est **bimodale**, sans
zone grise à trancher.

## L'enveloppe reste publiée, et reste le repli

Les deux bornes ne disparaissent pas : elles sont exactes **en tant que
bornes**, et les fiches publiées avant ce lot ne portent pas `periodes[]`.
`_appartenance_couvre` lit les périodes quand elles existent et retombe sur
l'enveloppe sinon — exiger la clé ferait sortir des compteurs à zéro sur des
données qui n'ont pas changé.

**La clé n'apparaît que si la source l'a donnée.** L'écrire à `null` dirait
« aucune période connue » sur un membre dont on connaît les bornes ; l'omettre
dit « ce roster ne les portait pas », ce qui est le fait (§2 règle 5).

## La seule entrée que le schéma valide

`validate_profil_groupe` ne valide pas le contenu de chaque membre — à une
exception près, introduite ici : les `periodes[]` **détaillent** l'enveloppe,
elles ne la contredisent pas. Sont refusées une liste vide (elle dirait « aucune
appartenance connue » sur un membre qui en a une), une période sans début, un
ordre non croissant, et un désaccord de bornes entre les deux champs.

Une contradiction publiée entre deux champs du même membre ne se rattrape nulle
part en aval.

Suite complète à 4 427, 0 échec.
