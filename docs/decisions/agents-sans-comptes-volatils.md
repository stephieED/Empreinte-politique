# `AGENTS.md` ne porte plus de compte qu'un run déplace

`2026-09-11`

> **En bref** — trois comptes d'`AGENTS.md` étaient faux le jour où on les a relus, et aucun par négligence : **481 profils, dont 13 candidats déclarés et 468 membres de roster** (#630) quand `main` en porte **1 035, dont 32 et 1 003** ; **158 fichiers de décision** quand il y en a **285** ; un portail à **quatorze blocs** quand #845 venait de lui ajouter la §4c. Chacun était juste à sa date. Le défaut n'est pas la mesure, c'est son **emplacement** : `AGENTS.md` est chargé à chaque session et lu comme l'état présent, alors qu'un run déplace les deux premiers et qu'un lot déplace le troisième. Question posée par la propriétaire, 11/09/2026 : ces chiffres ont-ils leur place dans un fichier censé être stable ? Non. Ils sont retirés, la règle qu'ils illustraient reste — deux populations, un champ qui les distingue, des outils qui impriment la ventilation —, et le §8 interdit désormais d'en rajouter. **Rien n'est perdu** : les chiffres de #630 vivent dans `populations-profils-portees-par-les-outils-630.md`, et le compte à jour se lit en une commande.

## Ce qui a changé

| Ligne | Avant | Après |
| --- | --- | --- |
| §3, les deux populations | 481 fichiers, 13 déclarés, 468 membres | la règle, le champ `meta.provenance`, et `src/population_profils.py` qui ventile |
| Références, portail | « fourteen blocks (1, 2, 3, …) » | un bloc numéroté par sujet ; la liste est `main()` et le résumé du run |
| Références, `docs/commandes.md` | « 33 of the repo's 45 executables » | les exécutables internes sont laissés de côté, et le fichier le dit |
| Références, index | « the 158 decision files » | l'index généré de toutes les décisions |
| §8, ligne `AGENTS.md` | — | jamais un compte qu'un run ou un lot déplace |

## Le critère

Un chiffre reste dans `AGENTS.md` s'il **ne bouge qu'avec une décision** — le
nombre de sorties de `pivot_data/`, qui change quand un lot en ajoute une et que
ce lot met à jour. Il en sort s'il **bouge avec la donnée** : un run, une
collecte, un lot sans rapport. Le premier est une structure, le second une
mesure.

## Écarté

**Garder les chiffres en les datant.** « 481 au 30/08/2026 » est honnête, mais un
fichier chargé à chaque session transforme une date en décor : on lit le nombre,
pas le jour. C'est exactement ce qui s'est passé.

## Deux passages qui servaient d'argument, arbitrés à part

Deux passages portaient des mesures qui bougent avec la donnée, mais chacun
servait d'**argument** plutôt que d'inventaire. Arbitré par la propriétaire le
11/09/2026, sur recommandation :

| Passage | Rôle du chiffre | Sort |
| --- | --- | --- |
| §7 — « 475 of 476 profiles », « 511 interventions » | la preuve que la clause ODbL survit (#530) | **gardé et daté** (27/08/2026, `74c77c2`) : c'est la preuve d'une obligation légale, et elle doit se lire au moment où l'on décide — mais comme une mesure datée, à refaire avant de s'y fier |
| Références — `commissions_dossiers.json` (6 024 dossiers, 381/381, 0 sur 174) | inventaire | **retiré** : `docs/data-architecture.md` porte déjà ces chiffres ; reste le constat structurel, le référentiel est celui de l'AN |

Le même paragraphe portait un compte ajouté la veille par #845 lui-même — « 23
fiches de groupe publiées pour 10 lignées » —, déjà faux au moment de cette
relecture : 30 fiches et 13 lignées étaient déclarées depuis #846. Il sort avec
le reste. C'est l'argument de cette décision en une ligne : le compte avait un
jour.
