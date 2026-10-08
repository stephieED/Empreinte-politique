<a id="borne-fonctions-gouvernementales-859"></a>
# La borne des fonctions gouvernementales est posée sur chaque profil, sous sa propre clé (#859) (2026-10-08)

`2026-10-08`

> **En bref** — la source (AMO30) ne publie aucun gouvernement avant le **17/05/2007** (Fillon I) : mesuré les 05 et 06/10/2026, 659 mandats `GOUVERNEMENT`, le plus ancien de cette date. La page `/couverture` affichait « aucune borne déclarée » pour les fonctions gouvernementales. Arbitrage de la propriétaire, 08/10/2026 : **l'option la plus cohérente avec l'existant** (option A). La borne est écrite sur chaque profil, comme celle des mandats de l'Assemblée (19/06/2002), dans `couverture.fonctions_gouvernementales`, la clé que `couverture-corpus.mjs` lit déjà (#1238).

## 1. Pourquoi sur chaque profil

Toutes les bornes existantes vivent dans la `couverture` de chaque fiche, et la page `/couverture` les recalcule depuis les fiches (`bornesPubliees()`). Un fichier commun aurait été la seule borne rangée autrement, avec sa lecture à part.

## 2. Pourquoi une clé à part

Les fonctions gouvernementales sont une partie de `mandats`. Écrite dans `couverture.mandats`, la borne serait perdue : `bornesPubliees()` retient la plus ancienne date d'une liste, donc 2002. D'où `schema_pivot.BORNES_COUVERTURE_CORPUS`, à côté de `LISTES_COUVERTES` et non dedans :

- **facultative** : un profil écrit avant ce lot reste valide, et la dérivation la pose à la prochaine écriture ;
- **hors de la machinerie des listes métier** : ni décision de collecte, ni panne, ni fait « jamais élu » ne s'y appliquent, parce qu'elle ne dépend ni de la personne ni de sa collecte ;
- validée par `valider_couverture` comme les autres entrées, et toute autre clé hors nomenclature reste refusée.

## 3. Alternative écartée

**Un seul endroit pour le corpus** (option B) : une date répétée 1 402 fois de moins, mais une forme que rien d'autre n'emploie, et une ligne de lecture de plus côté interface.
