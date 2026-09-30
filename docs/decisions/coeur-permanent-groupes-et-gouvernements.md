<a id="coeur-permanent-groupes-et-gouvernements"></a>

# Le cœur du site est parlementaire et gouvernemental ; les candidats sont un volet borné (2026-09-30)

`2026-09-30`

> **En bref** — Le site s'est construit autour des candidats déclarés à 2027 : c'est
> ce que disent son premier écran, son onglet d'entrée, son README et la première
> phrase d'`AGENTS.md`. **Arbitré par la propriétaire le 30/09/2026 : les groupes
> parlementaires et les gouvernements deviennent le cœur permanent, et les
> candidats un volet borné par l'élection.** Ce fichier consigne la direction et
> ce qu'elle oblige à revoir ; les formes restent à trancher.

## Ce qui a décidé

Le volet candidats a une **date de péremption** : passé avril 2027, une liste de
candidats déclarés ne décrit plus rien. Les groupes parlementaires et les
gouvernements, eux, continuent — ils sont ce que le corpus couvre depuis 2012,
et ce qu'il couvrira après.

Le site disait l'inverse. Il présentait le durable comme un complément du
ponctuel.

## Ce que ça change, et ce qui est déjà fait

| Endroit | Ce qu'il disait | État |
| --- | --- | --- |
| Titre de l'accueil | « … pour la présidentielle 2027 » | **retiré le 30/09** — la phrase est devenue « L'explorateur neutre et sourcé des parcours politiques. » |
| `AGENTS.md` §1 | « political CVs … for 2027 presidential candidates » | **corrigé ici** |
| `README.md` | « pour les candidats … ainsi que pour les groupes et les gouvernements » | **corrigé ici** — l'ordre disait la hiérarchie |
| Bloc d'entrée de l'accueil | Trois portes de même rang, candidats en premier | **à trancher** — trois formes maquettées le 30/09 |
| Onglet « Explorateur » | mène à `/candidats` (`NavigationSite.jsx`) | **à trancher** — c'est la porte d'entrée de tout le site |
| Le mot « parcours » | mot de personne, employé pour l'ensemble | **ouvert** — voir plus bas |

## Ce que ce fichier ne tranche PAS

**La forme du bloc d'entrée.** Trois maquettes rendues sur données réelles :
l'ordre inversé ; deux portes plus un encart daté ; deux portes et les candidats
en renvoi. La deuxième est recommandée — elle dit *ponctuel* sans dire
*secondaire* — mais rien n'est posé.

**Le vocabulaire.** Le titre annonce « des parcours politiques ». Un parcours est
le mot d'une personne : il convient aux candidats, mal aux gouvernements, et pas
du tout à une lignée de groupe. Si le cœur devient parlementaire et
gouvernemental, le mot du titre doit être réexaminé — c'est une question de fond,
pas une reformulation, et elle mérite son propre arbitrage.

## Ce qui ne change pas

**Les candidats restent collectés en entier et publiés comme aujourd'hui.** Le
recadrage porte sur la HIÉRARCHIE de présentation, pas sur le périmètre : aucune
fiche ne disparaît, aucune collecte ne s'arrête, et `raw_data/candidats.json`
continue de faire foi sur qui est déclaré.

Aucune règle de §2 n'est touchée.

## Pourquoi il n'y a pas de test

Les gardes de ce dépôt tiennent des faits vérifiables — une ancre qui existe, un
plafond de lignes, un champ présent. **Une hiérarchie éditoriale ne se teste
pas** : elle s'écrit ici, et c'est ce fichier qu'une session relit avant de
remettre les candidats en tête parce que « c'est un site sur 2027 ».
