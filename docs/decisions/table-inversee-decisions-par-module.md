# Le lien code → décisions se dérive, il ne s'écrit pas à la main (2026-08-30)

`2026-08-30`

> **En bref** — `docs/decisions-par-module.md` est généré : une décision **gouverne** un module quand elle nomme un de ses symboles de tête, elle le **mentionne** quand elle n'écrit que le fichier ; `merge_profile.py` citait 0 des 39 décisions qui le gouvernent, et le seuil de 5 du test ferme la régression.

`docs/technical_decisions.md` va des **décisions vers le code** et se lit par
date. Rien n'allait du **code vers ses décisions**, sauf quand quelqu'un avait
pensé à écrire le renvoi dans le module. Un agent qui ouvre un fichier de `src/`
devait donc deviner que `docs/decisions/` existe et le fouiller, lire un index de
168 lignes rangé par date, ou lancer un `git grep` que personne ne lance
spontanément.

C'est inégalement posé, et ça se re-troue à chaque module créé.

## La mesure du 30/08/2026

Colonne « cite » : renvois `docs/decisions/<nom>.md` **distincts** présents dans
le module. Colonne « gouvernent » : décisions qui nomment un symbole de tête du
module (critère ci-dessous). Colonne « nomment le module » : décisions qui
écrivent son nom, quel qu'en soit le propos.

| Module | Cite | Gouvernent | Nomment le module |
| --- | ---: | ---: | ---: |
| `merge_profile.py` | **0** | **39** | 21 |
| `couverture_profil.py` | **0** | 3 | 4 |
| `group_profile.py` | 1 | 15 | 21 |
| `candidate_profile.py` | 8 | 60 | 37 |
| `generate_all_profiles.py` | 3 | 19 | 34 |
| `schema_pivot.py` | 4 | 18 | 14 |
| `check_quality_gate.py` | 7 | 8 | 20 |

`merge_profile.py` citait **zéro** décision alors que 39 nomment une de ses
fonctions. C'est le module de l'épic #598 — celui dont personne n'avait relu la
politique de fusion, et dont l'angle mort a duré des mois.

**Le grep par nom de module n'est pas le majorant qu'on croyait.** L'hypothèse de
départ était que compter les décisions qui écrivent `merge_profile` surestime
celles qui le gouvernent. C'est faux dans les deux sens : 39 le gouvernent contre
21 qui l'écrivent, et seules 17 sont dans les deux listes. Une décision qui pose
une règle sur `clean_stale_interventions` n'a aucune raison d'écrire le nom du
fichier ; une décision qui raconte un incident écrit le nom du fichier sans rien
poser.

## Le critère : « gouverne » nomme du code, « mentionne » nomme un fichier

Une décision **gouverne** un module quand elle nomme un **symbole de tête** de ce
module — fonction, classe ou constante définie au niveau du module — sous l'une
des deux formes :

| Forme | Exemple | Condition |
| --- | --- | --- |
| qualifiée | `merge_profile.fusionner_couverture`, `merge_profile.py::merge_raw_dirs` | aucune : le module lève l'ambiguïté |
| nue, entre dos d'accent | `` `clean_stale_interventions` `` | le symbole est défini dans **ce seul** module de `src/` |

Elle le **mentionne** quand elle n'écrit que le fichier (`merge_profile.py`) ou
le module nu : elle dit qu'il est concerné, pas quel contrat il doit tenir.

**Pourquoi ce critère et pas la position dans la page.** Le premier essai
classait par section — titre, chapeau, section « décision » contre récit
d'incident. Relu sur les 21 décisions qui écrivent `merge_profile`, il ne
séparait rien : `pivot-freshness-timestamps-stables` pose sa règle dans son
chapeau, `verification-bout-en-bout-legislatures-figees` y raconte une
observation, et les deux sont au même endroit.

**Ce qu'il gagne : il ne rouille pas.** Un symbole renommé ou supprimé retire le
lien de lui-même. Une table qui pointerait vers du code qui n'existe plus serait
pire que pas de table — c'est le défaut que ce dépôt a corrigé trois fois le
30/08/2026.

**Ce qu'il rate, nommément.** Une décision qui gouverne un module sans nommer
aucune de ses fonctions. Le cas est réel et connu :
[#collecte-vs-publie-545](collecte-vs-publie-545.md), « ce que la normalisation a
le droit de faire », est la charte de `normalize_profil` et n'écrit que
`normalize_profil.py:446` — un numéro de ligne, pas un nom. Un numéro de ligne
rouille par construction : le compter reviendrait à réintroduire exactement ce
que le critère écarte. La décision est donc citée à la main dans le module, et
la table dit « mentionne ». Le critère est mécanique et faillible dans un sens
connu, pas exact.

## Où la table vit, et pourquoi là

`docs/decisions-par-module.md`, écrit par
`scripts/generer_decisions_par_module.py`. Trois emplacements étaient ouverts :

| Emplacement | Écarté parce que |
| --- | --- |
| une section de `docs/technical_decisions.md` | AGENTS.md §8 : ce fichier est « l'index des décisions, et rien d'autre ». Une seconde table y ferait diverger deux ordres de lecture dans un fichier dont la ligne 1 est déjà un aimant à conflits |
| un bloc généré en tête de chaque module de `src/` | 62 modules réécrits à chaque décision nouvelle, donc 62 conflits potentiels par lot, pour une liste de 39 lignes que personne ne lit |
| **un fichier généré, plus un bloc court écrit à la main dans les modules troués** | **retenu** |

Le critère demandé était qu'un agent qui ouvre un module tombe dessus sans la
chercher. Un fichier seul ne le tient pas : c'est le **bloc en tête du module**
qui le tient, et il renvoie vers le fichier pour la liste complète. Le fichier
tient l'exhaustivité et la fraîcheur ; le bloc tient les deux ou trois décisions
qui comptent, choisies en les lisant. Une liste de 39 renvois ne se lit pas.

## Le garde-fou, et son seuil

`tests/test_decisions_par_module.py` échoue quand un module qu'au moins **5**
décisions gouvernent n'en cite **aucune**. Il vérifie aussi que la table
committée n'a pas dérivé du dépôt, et éprouve le critère lui-même sur un corpus
minuscule — sans quoi un analyseur cassé rendrait les deux autres tests verts par
vacuité.

Le seuil ne protège pas contre « une décision non citée » : il protège contre la
**forme #598**, un module dont la politique n'a plus aucune porte d'entrée depuis
le code. En dessous de 5, il crierait sur quatorze modules dont la gouvernance
tient en deux lignes — et *un garde-fou qui crie pour rien finit désactivé*
([#hook-diagnostic-sparse-checkout](hook-diagnostic-sparse-checkout.md)).
Au-dessus, il laisserait passer `group_profile` à 15, le second cas réellement
payé. Après la pose des blocs, le pire trou restant est à **3** : deux décisions
de marge.

## Ce qui a été posé dans les modules

Sept blocs, chacun nommant deux ou trois décisions choisies en lisant leur
contenu, jamais leur titre : `merge_profile`, `group_profile`,
`couverture_profil`, `syceron_debates`, `couverture_dossiers`,
`generate_gouvernement_profiles`, `normalize_profil`.

## L'alternative écartée : une table tenue à la main

Elle aurait permis d'écrire « gouverne » à la lecture, sans critère mécanique —
donc plus juste au jour de son écriture. Écartée pour la raison qui a fait écrire
ce lot : une table manuelle diverge du code, et une table qui ment sur ce qui
gouverne un module est plus coûteuse que l'absence de table, parce qu'on lui fait
confiance.
