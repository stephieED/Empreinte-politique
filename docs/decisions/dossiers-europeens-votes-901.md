<a id="dossiers-europeens-votes-901"></a>
# L'index des dossiers européens lit aussi les dossiers que les votes citent (#901) (2026-09-17)

`2026-09-17`

> **En bref** — Les 11 013 positions de vote européennes des 6 candidats déclarés
> concernés citent 4 630 dossiers, dont **296** étaient indexés. Pour les autres,
> l'interface n'avait ni titre, ni type de procédure, ni famille : seulement
> l'intitulé du scrutin. `references_visees` lit désormais une troisième source,
> `votes[].scrutin_non_resolu.reference_dossier`. Aucune requête de plus : le dump
> `ep_dossiers` est déjà téléchargé.

## Contexte

Demandé par la session interface le 17/09/2026 : l'axe de couleur des votes doit
être celui des textes et des amendements. Mesuré sur `origin/main` `789537af5`,
chez les 32 candidats déclarés : 11 013 positions de vote européennes, 10 576 avec
une référence de dossier, **4 630** références distinctes, **296** dans l'index.

Le dump en cache (17/08) porte **4 253** des 4 334 manquantes. Les autres sont plus
récentes que le dump, comme les 12 absentes des amendements.

## Décision

1. **Troisième source** dans `references_visees`, après les amendements et les
   textes portés : un vote dont `scrutin_non_resolu.institution` vaut
   `parlement_europeen` et qui cite `reference_dossier`. Un vote de l'Assemblée
   n'a pas de bloc non résolu et n'entre pas.
2. **Rien d'autre ne change** : mêmes champs, même schéma v3. Une référence absente
   du dump ne produit toujours aucune entrée.

Estimé sur les profils des candidats déclarés et le dump du 17/08 : **4 642**
dossiers au lieu de 389, **3,4 Mo** au lieu de 290 Ko, familles sur 4 642,
commission au fond sur 4 149.

## Ce que ce lot ne fait pas

**Les domaines EuroVoc par dossier**, demandés en même temps, ne sont pas ici. Ni
le dump ParlTrack (0 dossier sur 23 885 ne mentionne EuroVoc), ni la fiche
« procédure » du portail du Parlement ne les publient. Ils ne s'obtiennent qu'en
passant par les documents du dossier, un par un : un coût et un choix à arbitrer
à part.

## Alternative rejetée

**Indexer les 23 885 dossiers du dump.** L'index suit le corpus, comme celui des
scrutins : de l'ordre de 17 Mo par simple proportion (non mesuré), pour servir 4 642 références.
