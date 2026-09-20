# Quelle source a rempli quel champ, et quand — un bloc à côté d'`identite` (#603) (2026-08-30)

`2026-08-30`

> **En bref** — `meta.provenance_champs` décrit `identite` seule, champ par champ ; dérivé après la fusion et jamais fusionné, l'inconnu se publie `source: null`, et `sources[0]` aurait attribué 2 597 des 2 612 champs à une source retirée depuis #529.

Lot 4 de l'épic #598, et le seul qui **ouvre le schéma publié**. AGENTS.md §2.2
demande qu'un fait publié remonte à sa source primaire ; sur les listes c'est
acquis — une entrée porte son `source_url`, et la fusion est additive. Sur
`identite`, non : depuis [#permanence-champs-identite-601](permanence-champs-identite-601.md)
le bloc est composé **champ par champ** à partir de deux écrivains, et rien dans
le fichier publié ne dit lequel a rempli quoi.

## Ce que la mesure a fermé avant l'écriture

Deux des quatre questions du lot n'en étaient pas.

| Question | Réponse, mesurée le 30/08/2026 |
| --- | --- |
| Le volume | 2 862 clés d'`identite` sur les 481 profils pivot publiés, dont **2 612 renseignées**. Le bloc coûte **147,0 Kio** en rejouant la fusion sur le corpus committé, **239,1 Kio** si chaque champ est attribué (rejeu avec un écrivain frais) — soit **0,023 %** et **0,038 %** des 621,28 Mio de `pivot_data/profiles`. Le garde-fou de blob bloque à 80 Mio (#580) : la question se répondait par une multiplication |
| La portée | `src/group_profile.py` ne lit **jamais** `identite` — zéro occurrence ; il consomme `nom`, `mandats`, `votes`, `interventions`, `amendements`, **que des listes**, déjà fusionnées additivement. La provenance par champ ne répond à une question que là où plusieurs sources écrivent le même champ : **`identite`, et elle seule** |

Population : **13 profils `candidat_declare`** sur les 481 publiés, dont 9
portent un bloc `identite` (48 champs renseignés) ; les 468 `roster_groupe`
alimentent les agrégats de groupe **sans** `identite`, mais leur `identite` est
publiée — 2 564 champs renseignés — et c'est là que vivaient les 191 marqueurs
HATVP et les lieux de naissance en plomberie XML de #556.

## Décision 1 — le bloc vit **à côté** d'`identite`, dans `meta`

`meta.provenance_champs = {"identite": {"<champ>": {"source", "synchro_le"}}}`.

Trois raisons, dans l'ordre où elles pèsent :

1. `identite` est un dictionnaire champ → **valeur**, et l'interface l'itère
   comme tel. Y ajouter des clés qui ne sont pas des valeurs publiables
   obligerait chaque lecteur à connaître la liste des clés à sauter.
2. `fusionner_identite` compose le bloc champ par champ. Une clé de provenance
   rangée dedans passerait par la règle des valeurs — « une absence n'écrase
   jamais » (#601) —, et une provenance obsolète survivrait à la valeur qu'elle
   décrit. Une métadonnée doit au contraire **suivre**.
3. `meta` est déjà l'endroit de la traçabilité du run (`synchro_sources`,
   `collecte_ecartee`, `warnings`), et depuis
   [#union-warnings-extinction-600](union-warnings-extinction-600.md) c'est le
   seul bloc dont chaque clé est **obligée** de nommer sa règle de fusion. Une
   clé posée ailleurs n'aurait rien à déclarer.

**Deux voisins à ne pas confondre**, et le nom seul ne suffit pas à les séparer :

| Bloc | Question | Maille |
| --- | --- | --- |
| `meta.provenance` (#189) | *pourquoi ce profil existe-t-il ?* | le profil |
| `couverture` (#539) | *pourquoi cette liste est-elle vide ?* | la liste métier |
| `meta.provenance_champs` (ce lot) | *d'où vient cette valeur, et de quand ?* | le champ |

Les trois coexistent. Aucun ne remplace un autre — arbitrage de la propriétaire
du 30/08/2026, non rouvert ici.

## Décision 2 — la provenance est **dérivée**, jamais fusionnée

Même patron que `chambres` (#493) et `licence_donnees` (#530) : un champ dérivé
se recalcule après la fusion de ce dont il dérive. Fusionner `provenance_champs`
clé par clé publierait la provenance d'un écrivain à côté de la valeur d'un
autre — l'inverse exact de ce que le bloc existe pour dire.

Et le verdict vient de la composition elle-même : `_composer_identite` rend le
bloc **et** l'origine de chaque champ, en une seule implémentation.
`fusionner_identite` n'est plus qu'une porte d'entrée. Un second calcul qui
rejouerait les mêmes règles à côté divergerait — c'est le piège que
`_accorder_hatvp` a dû rattraper au #601, et il ne s'y rattrapait que parce
qu'un invariant le rendait détectable. Ici rien ne le rendrait détectable : une
provenance fausse est une provenance, et elle se lit comme une preuve.

## Décision 3 — l'inconnu se **déclare**, il ne s'omet pas

Un champ gardé d'un profil publié avant ce lot n'a pas de provenance
consignée. Il est publié `{"source": null, "synchro_le": null}`, et
`valider_provenance_champs` **exige la complétude dans les deux sens** : tout
champ publié et renseigné a son entrée, aucune entrée ne décrit un champ absent.

Sans le premier sens, l'absence d'entrée deviendrait une seconde façon de dire
« on ne sait pas », à côté de celle qui le dit déjà — et de deux façons de dire
la même chose, c'est celle qu'on oublie de lire qui gagne. Le schéma refuse
aussi une **date sans source** : un horodatage que rien ne rattache n'est pas
une traçabilité, c'est la forme d'une preuve qui n'en est pas une (§2.2).

## Le piège mesuré : `sources[0]` aurait « marché »

La source d'un champ pris au nouvel écrivain est celle que ce profil déclare.
La lecture naïve — `sources[0]` — passe tous les tests d'un profil frais.

Rejouée sur le corpus committé, elle attribue **2 597 des 2 612 champs
d'identité des 481 profils publiés à `nosdeputes`**, source retirée du pipeline
depuis #529, sur la seule foi de l'ordre d'une liste. `_merge_pivot_sources`
unit `sources[]` par type, et 475 des 481 profils publiés portent encore une
entrée `nosdeputes`.

D'où la règle retenue : **`sources[]` doit ne nommer qu'un seul `type`**, sinon
la provenance est inconnue. Un profil frais en nomme un seul —
`assemblee_nationale` chez `normalize_profil`, y compris quand il ajoute une
seconde entrée du même type pour la source des votes ; `europarl` chez
`normalize_europarl`. Un profil déjà fusionné en nomme plusieurs, et n'est donc
pas un écrivain.

Rien n'est deviné depuis l'ancien profil non plus : son `sources[]` est un
surensemble des deux côtés, et lui attribuer un champ serait inventer une
preuve. §2.5, appliqué à la traçabilité elle-même.

## L'alternative écartée : attendre l'épic UI #594

Une recommandation de décaler ce lot après le temps 2 de l'épic UI a été écrite
sur ce lot, puis **retirée**. Son argument — « un bloc publié que rien ne lit
reproduit les 3 800 entrées de `couverture` invisibles à l'écran » — se trompe
de cause.

Le problème de `couverture` n'est pas d'avoir été construit trop tôt : c'est que
**l'interface n'a jamais été mise à jour pour le lire**. La défaillance est en
aval. Et l'exemple va contre l'argument : la revue #593 a pu mesurer ce qui
manquait à l'interface **parce que la donnée existait**.

Ce qu'il faut en garder tient en une phrase : **quand on publie un bloc,
quelqu'un doit avoir le mandat de le lire.** Ça se règle en le nommant dans
#594 — ce qui a été fait — pas en retardant sa création.

## Ce qui reste ouvert

- **Le rendu.** Ce lot publie la donnée et ne touche aucun composant React. Ce
  que l'interface en montre est nommé dans #594.
- **Les autres blocs composés.** `BLOCS_PROVENANCE_CHAMPS` n'en contient qu'un,
  et c'est une décision, pas un début d'inventaire. `identifiants` est composé
  clé par clé lui aussi (#539) mais n'y entre pas : chacune de ses clés **est**
  le nom de sa source (`an`, `europarl`, `hatvp`).
- **Les champs déjà publiés.** Aucune migration : la provenance d'un champ
  apparaît au run qui le réécrit, et jusque-là elle se lit `null`. Une migration
  devrait deviner qui a écrit quoi, ce que la mesure ci-dessus interdit.
