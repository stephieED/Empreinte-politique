<a id="liste-sautee-garde-son-constat-1160"></a>
# Une liste qu'un run n'a pas lue garde ce que le dernier run qui l'a lue a établi (#1160) (2026-10-07)

`2026-10-07`

> **En bref** — quand un run sautait une liste, la fiche la déclarait « non collectée », même pleine de ce que les runs précédents avaient lu : 15 des 34 fiches de candidats déclarés pour les prises de parole, 17 pour les textes portés, mesuré le 06/10/2026 — 5 736 prises de parole chez Jean-Luc Mélenchon. Arbitrage de la propriétaire, 07/10/2026 (option A) : la fiche dit ce que le **dernier run qui a lu** la liste a établi, avec sa date ; « non collecté » seulement si aucun run ne l'a jamais lue. En mesurant, un second défaut : **le job roster parlait pour l'AN**, et déclarait « écartées » des prises de parole que l'AN venait de collecter.

## 1. Le constat

Mesuré le 06/10/2026 sur le privé `92f52ab7b` :

| Population | Liste | Déclarées « non collecté » | Dont listes pleines |
| --- | --- | ---: | ---: |
| 34 candidats déclarés | prises de parole | 18 | 15 |
| 34 candidats déclarés | textes portés | 17 | 17 |
| 1 368 membres de groupe et de gouvernement | prises de parole | 1 367 | 1 232 |
| 1 368 membres de groupe et de gouvernement | textes portés | 1 367 | 1 161 |

L'issue comptait 3 fiches pour les textes portés le 01/10 : l'état suivait les
cases cochées du dernier run, pas la donnée.

## 2. Deux causes

**La fusion de la couverture.** `fusionner_couverture` (#602) donnait raison au
constat le plus récent (règle 2, « une couverture décrit le run »), y compris
quand ce constat disait seulement « ce run a sauté la liste ». La règle 3, qui
classe les écrivains selon qu'ils ont interrogé la source, ne jouait qu'à date
égale.

**Le roster parlait pour l'AN.** Un candidat déclaré qui siège dans un groupe est
collecté deux fois : en entier par `extract-an`, et par un shard du roster qui
saute exprès ses interventions (`theme_seul_refuse`, #657) et ses dossiers. Ce
shard écrivait `collecte_ecartee: ["interventions", "textes_portes"]`. Les
artifacts sont fusionnés dans l'ordre `an ue roster senat`, et
`_declaration_du_run` retient le dernier écrivain qui pose la clé : la
déclaration du roster devenait celle du profil. Mesuré sur le run
`37526734878` (06/10, `collect_interventions=true`) : le brut de Jean-Luc
Mélenchon portait 3 933 interventions collectées le soir même **et** la
déclaration qu'elles avaient été écartées ; 17 des 34 fiches de candidats
déclarés restaient « non collecté » sur leurs prises de parole après ce run.
Ségolène Royal, membre d'un roster de gouvernement, est dans le même cas.

## 3. La décision

1. **Règle 1bis de `fusionner_couverture`** : une entrée `non_collecte` /
   `par_decision` ne remplace jamais une entrée d'un run qui a interrogé la
   source, quelles que soient les dates. La fiche garde le dernier constat réel
   et sa date (`constate_le`), qui dit la fraîcheur. « Non collecté » ne reste
   que si aucun run n'a jamais lu la liste.
2. **Une panne l'emporte toujours** : la règle 2 de #602 tient pour tout ce qui
   a interrogé la source — une source muette aujourd'hui ne se cache pas
   derrière un `couvert` d'hier.
3. **Le job roster n'écrit plus `collecte_ecartee` pour un candidat déclaré.**
   Sans la clé, `_declaration_du_run` garde celle de l'AN, fusionnée avant. Un
   membre de roster ordinaire déclare toujours ce qu'il saute.

## 4. Ce qui change, et quand

Aucune donnée ne change d'elle-même : la fiche se répare au premier run qui
**lit** la liste, puis garde ce constat aux runs qui la sautent.

| Liste | Se répare au run qui… |
| --- | --- |
| prises de parole des candidats déclarés | collecte les interventions (`collect_interventions=true`, ou le run planifié) |
| textes portés des candidats déclarés | collecte les dossiers — à mesurer, la case par défaut est décochée |
| listes des membres de roster | les collecte, sous la même condition |

Ségolène Royal, dont la vérité est `hors_couverture` (son mandat précède la
source), la retrouvera au premier run qui interroge ses interventions.

## 5. Écarté

| Option | Pourquoi |
| --- | --- |
| B. Un cinquième état, « non rafraîchie » | écarté par l'arbitrage : un vocabulaire fermé à étendre et une interface à instruire, pour une fraîcheur que la date dit déjà |
| C. Rien | l'interface ignore ce champ depuis le 01/10, mais `pivot_data/` est la donnée publiée et réutilisée |
| Dériver `couvert` dès qu'une liste sautée est pleine | publierait la date du jour comme date de constat : une fraîcheur inventée |
| Fusionner `collecte_ecartee` par intersection entre écrivains | la fusion ne distingue pas les écrivains d'un même run de ceux des runs précédents ; une liste sautée ce soir et lue hier sortirait « couvert » à la date du jour |

## 6. Limites déclarées

- **Un gel de groupe** (#558) publie aussi `par_decision`. Sur un profil dont le
  groupe serait gelé après avoir été lu, la règle garderait le dernier constat
  plutôt que la preuve du gel. Non mesuré : combien des 20 membres des deux fiches
  gelées portaient un constat de lecture avant le gel.
- La seconde question de #1160 — une preuve publiée peut-elle citer un nom de
  champ et un numéro d'issue ? — n'est pas traitée ici.
