# `meta.warnings[]` déclare son destinataire, dans un jumeau typé et aligné (#642) (2026-08-31)

`2026-08-31`

> **En bref** — 52 des 481 profils publiés portent 115 avertissements dont **80 internes et 35 lisibles** (re-mesuré le 31/08/2026), sans rien qui les partitionne : l'interface ne publiait donc aucun des deux registres, et la page de `bruno-retailleau` restait sans explication alors qu'elle est écrite dans le fichier ; le destinataire est désormais déclaré **par avertissement, à l'endroit qui l'écrit** — vocabulaire fermé à deux valeurs, obligatoire, validé — dans `meta.avertissements[]`, jumeau typé et **aligné entrée par entrée** sur `meta.warnings[]`, ce qui rend une disparition impossible là où `audit_diff_profils` ne surveille rien ; une table indexée sur le préfixe est écartée parce que « votes introuvables » couvre à la fois un constat et une panne (#484 à l'identique), le constat ParlTrack **s'écrit deux fois** faute de destinataire « mixte », et les 19 avertissements `synchro_sources.nosdeputes` qu'aucun code n'écrit plus sont typés par une table fermée indexée sur le message entier.

`meta.warnings[]` mélangeait deux registres sous un seul champ, et rien ne
permettait de les séparer par programme. L'interface ne pouvait donc ni tout
publier — de la plomberie sur une page publique — ni rien publier — elle perdait
les explications que le lecteur attend. Elle ne publiait rien : zéro occurrence
de `warnings` dans `web/UI_finale/src`.

## La mesure, refaite sur le corpus courant

Re-mesuré le 31/08/2026 sur les 481 profils de `pivot_data/profiles/` : **52
profils portent 115 avertissements**, exactement les chiffres de l'issue, run
`33351244845` compris.

| Famille | Occurrences | Destinataire retenu |
| --- | ---: | --- |
| `chambres du profil non corroborée` | 31 | `interne` |
| `chambre de mandat électif non résolue` | 27 | `interne` |
| `votes introuvables` | 21 | `lecteur` |
| `synchro_sources.nosdeputes` | 19 | `interne` |
| `mandats introuvables` | 9 | `lecteur` |
| `aucun mandat français connu` | 3 | `lecteur` |
| `synchro_sources.assemblee_nationale` | 3 | `interne` |
| `ParlTrack` | 2 | **scindé** : 1 `lecteur` + 1 `interne` |

Soit **80 internes et 35 lisibles**. Après le lot, ces 115 avertissements-là
portent tous un destinataire — 80 / 35 exactement, **vérifié sur le corpus
publié, sans régénération** (voir « Les 49 avertissements écrits par du code qui
n'existe plus »). Le dédoublement ParlTrack ajoutera un `interne` par profil
concerné le jour où ces deux profils seront recollectés : 82 / 35 sur les mêmes
52 profils.

## La décision

**Le destinataire est déclaré par avertissement, à l'endroit qui l'écrit.**
`src/avertissements.py` porte le vocabulaire fermé `DESTINATAIRES_AVERTISSEMENT`
— `lecteur`, `interne` — et la fabrique `avertissement(message, destinataire)`,
dont le second argument n'a **pas de valeur par défaut**.

**Deux valeurs, et pas une troisième.** Un avertissement qui s'adresse aux deux
s'écrit **deux fois**, dans les termes de chacun. Une valeur « mixte » rendrait
à l'interface le tri qu'elle n'a pas su faire, avec un nom de plus.

Le champ publié est `meta.avertissements[]`, **jumeau typé et aligné** de
`meta.warnings[]` : une entrée `{"message", "destinataire"}` par avertissement,
même ordre, mêmes chaînes. `valider_avertissements()` refuse une longueur
différente, un message différent, une clé `destinataire` absente ou une valeur
hors nomenclature.

### Pourquoi un jumeau plutôt qu'un dict dans `warnings[]`

Changer le type des éléments de `meta.warnings[]` aurait touché les 61 sites
d'écriture, les cinq consommateurs qui font `startswith` (`_prune_stale_warnings`,
`unir_warnings`, `couverture_profil`, `audit_pivot_dataset`, le portail de
qualité) et **567 lignes d'assertions dans 52 fichiers de tests** — pour un
champ qu'aucun consommateur ne demandait sous cette forme, et en changeant des
textes publiés que #600 s'était engagé à ne pas toucher.

Le précédent est celui de #539 : `couverture` a été **ajoutée à côté** des cinq
listes métier qu'elle explique, sans changer leur forme. Même geste ici.
`meta.avertissements` est un champ **dérivé**, comme `chambres` (#493),
`licence_donnees` (#530) et `provenance_champs` (#603) : recomposé après toute
mutation par `deriver_avertissements()`, jamais fusionné.

Le typage voyage en mémoire sur une instance `Avertissement`, sous-classe de
`str` : les consommateurs ne voient qu'une chaîne, et rien n'a eu à changer chez
eux. `__reduce__` et `__deepcopy__` sont explicites — sans eux une copie
profonde perdrait le destinataire **en silence**, ce que ce lot existe pour
éviter.

### Pourquoi pas une table indexée sur le préfixe

C'est l'option qui ne coûtait rien, et elle est fausse.
`WARNING_PREFIX_VOTES_INTROUVABLES` couvre à la fois un **constat** (« aucune
correspondance officielle Assemblée nationale ») et une **panne** (« index des
scrutins indisponible »), qui ne s'adressent pas à la même personne. Une table
par préfixe reproduirait #484 à l'identique — c'est exactement la leçon que
`couverture_profil.MOTIFS_PANNE` a déjà dû tirer, en s'indexant par motif.

Sur le corpus du 31/08/2026 les 21 occurrences de « votes introuvables » sont
toutes du premier type — 19 sous l'ancienne formulation, 2 sous la nouvelle. Le
piège est donc **structurel**, pas visible dans les données du jour, ce qui est
la raison de ne pas s'en remettre à elles.

### Le critère de classement

`lecteur` quand la phrase explique ce que le lecteur voit — une liste vide, un
bloc `identite` absent — et nomme sa source ou sa borne (§2 règle 2).
`interne` quand elle rend compte de l'état du pipeline : compteur de migration,
panne de cache, nom de job de CI, nom de variable.

**`couverture` a la priorité.** Là où les deux disent la même chose, c'est elle
qui porte : toute panne présente dans `couverture_profil.MOTIFS_PANNE` ou dans
`MOTIFS_DEFAUT_COLLECTE` est classée `interne`, parce que le lecteur en est
déjà informé, avec sa preuve. Le typage sert les cas que `couverture` ne couvre
pas — l'échec de correspondance d'acteur, et le bloc `identite`, que les cinq
listes métier ne décrivent pas.

### Le cas qui s'écrit deux fois

`normalize_parltrack_dumps` publiait une seule phrase pour deux personnes :

> ParlTrack: aucune donnée trouvée pour le MEP ID 96742. Vérifier la
> disponibilité des dumps ou la validité du MEP ID.

« Vérifier la disponibilité des dumps » est une consigne qui nous est adressée.
Elle est désormais séparée du constat que le lecteur attend, et les deux
préfixes sont **distincts** — aucun n'est le préfixe de l'autre — pour que
l'union par famille de #600 les garde tous les deux.
`WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE` est volontairement un **préfixe du
message publié avant ce lot**, ce qui range l'ancienne forme dans la même
famille : la nouvelle la remplace au lieu de cohabiter avec elle. Même geste
qu'au #510 pour `WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES`.

## Un avertissement non typé est toléré, et la tolérance a une condition de retrait

`meta.avertissements` est **facultatif** : absent des 481 profils publiés avant
ce lot, comme `couverture` (#539) et `provenance_champs` (#603) l'étaient. Un
schéma qui n'accepte plus ce qu'il a écrit hier n'est pas une simplification,
c'est une perte — la raison déjà écrite pour `nosdeputes` dans
`KNOWN_SOURCE_TYPES`.

Présent, il est tenu à sa complétude : chaque entrée porte la clé
`destinataire`, dont la valeur peut être `null` — « personne ne l'a déclaré ».
`null` est **déclaré**, l'omission ne dit rien : c'est le même « si et seulement
si » que `couverture[].cause` sur `non_collecte`, et le même geste que
`provenance_champs`, qui publie `{"source": null}` plutôt que d'omettre
l'entrée.

**Condition de retrait de la tolérance**, écrite pour qu'elle ne devienne pas
permanente par omission, comme les replis de lecture de #431 et #432 :
`validate_profil()` cessera de tolérer l'absence du bloc le jour où aucun profil
publié n'en est dépourvu — donc après une régénération complète du corpus. Le
compte se lit avec `audit_pivot_dataset` (agrégation des warnings par type).

### Les 49 avertissements écrits par du code qui n'existe plus

**49 des 115 avertissements publiés** portent un texte qu'aucun code n'écrit
plus : ils datent d'avant #529, quand la collecte nommait encore NosDéputés.
Sans rien, ils seraient publiés sans destinataire — c'est-à-dire invisibles à
l'interface, l'état exact que ce lot corrige.

| Message publié | Occurrences | Destinataire | Sort |
| --- | ---: | --- | --- |
| `votes introuvables … (NosDéputés.fr non interrogé …)` | 19 | `lecteur` | remplacé par la forme actuelle à la prochaine collecte du profil (même famille) |
| `synchro_sources.nosdeputes …` | 19 | `interne` | **jamais réécrit** — son adaptateur est parti avec la source |
| `mandats introuvables … (NosDéputés/NosSénateurs …)` | 9 | `lecteur` | remplacé, même famille |
| `ParlTrack: aucune donnée trouvée pour le MEP ID …` | 2 | `lecteur` | remplacé par la moitié lecteur du dédoublement |

`AVERTISSEMENTS_HERITES` est une table fermée indexée sur le message **entier**,
pour la raison donnée plus haut. `PREFIXES_HERITES` en déroge pour une seule
entrée, celle qui porte un `MEP ID` variable : un préfixe n'y entre **que si
l'on peut dire à qui s'adresse tout ce qu'il recouvre**, ce qui est vrai de
celui-là et faux de `votes introuvables`. C'est un pont vers le corpus déjà
publié, du même genre que `couverture_profil.MOTIFS_JAMAIS_PANNE`, et chaque
entrée part le jour où aucun profil publié ne porte plus son message.

**Résultat mesuré sur les 481 profils publiés du 31/08/2026 : 115 avertissements
sur 115 portent un destinataire, 80 `interne` et 35 `lecteur`** — la ventilation
de l'issue, à l'unité près, et sans attendre une régénération du corpus.

## Ce que le lot ne change pas

**Aucun avertissement n'est perdu, et aucun texte publié ne change** — sauf le
ParlTrack, que l'issue demandait explicitement de réécrire.
`audit_diff_profils.py` ne surveille pas `meta.warnings`, donc rien n'aurait
bloqué une disparition : l'alignement exact vérifié par
`valider_avertissements()` est ce qui la rend impossible, et
`tests/test_destinataire_avertissements_642.py` le mesure sur l'union et sur
l'extinction de #600.

**L'affichage n'est pas dans ce lot** : il relève de #324/#594, une fois le tri
possible.

## La dette nommée

Deux avertissements classés `lecteur` portent encore des références internes
dans leur texte : `identité introuvable` cite « #529 », et `aucune intervention
syceron` cite « acteurRef » et « #510 ». Les réécrire dans ce lot aurait changé
des textes publiés sans que le tri en dépende. Le lot d'affichage tranchera ce
qui se rend à l'écran ; le typage, lui, est déjà bon.

## L'alternative écartée

Publier `meta.warnings[]` en entier et laisser l'interface filtrer sur le texte.
Écartée pour la même raison que la table par préfixe : un filtre sur la chaîne
ne se contrôle pas, ne se valide pas, et se casse au premier message reformulé —
sur une page publique, en silence.
