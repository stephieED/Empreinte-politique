<a id="retrait-fiches-parti-906"></a>
# Les fiches de parti sortent : 25 sur 29 n'agrégeaient qu'un candidat, et personne ne les lisait (#906) (2026-09-13)

`2026-09-13`

> **En bref** — `pivot_data/partis/` portait **29 fiches, 192 Ko**, produites à chaque run, versionnées, contrôlées par le portail qualité, et lues par **aucune ligne** de `web/UI_finale`. L'argument du retrait n'est pas le poids : **25 des 29 fiches n'agrégeaient qu'un seul candidat déclaré**, et le seul parti qui en avait davantage était **dédoublé** en deux fiches par une majuscule et un sigle — `Parti socialiste` (3) et `Parti Socialiste (PS)` (2). Un objet qui n'agrège rien, que rien ne lit, et dont le seul cas d'agrégation est cassé. Mesuré le 13/09/2026 sur `origin/main` `78dc39968`.

## 1. L'hypothèse qu'il fallait écarter d'abord

#906 posait trois hypothèses et disait de commencer par la troisième — une **dépendance cachée**, puisque `check_quality_gate.py` et `garde_fou_blobs.py` lisent le répertoire. La question était : le lisent-ils **parce qu'ils en ont besoin**, ou **parce qu'il existe** ?

| Consommateur | Ce qu'il en faisait |
| --- | --- |
| `check_quality_gate.py` | `--partis-dir` n'alimentait que le dict de la **§1 IncompleteRead** — une détection de troncature appliquée à tout répertoire produit |
| `garde_fou_blobs.py` | une entrée de `REPERTOIRES_SURVEILLES`, surveillance de **taille** |
| `audit_integrite_referentielle.py` | déclare lui-même que `partis/` et `gouvernements/` **ne portent aucune référence** |

Aucun agrégat, aucun index, aucune fiche publiée n'en dérivait. Les deux contrôles perdent un répertoire à surveiller, rien d'autre.

L'hypothèse **délibérée** ne tient pas mieux : il n'y a aucune trace d'un onglet Partis dans `web/old/`, pas même en v7. Ces fiches n'ont jamais eu de lecteur — ni passé, ni annoncé.

## 2. Ce qu'elles contenaient

| Candidats agrégés | Fiches |
| ---: | ---: |
| 1 | **25** |
| 2 | 3 |
| 3 | 1 |

Une fiche de parti à un candidat est une fiche de candidat avec un en-tête de parti. Et le dédoublement du Parti socialiste dit d'où vient le défaut : `parti_nom` est repris du **texte libre** de `raw_data/candidats.json`, normalisé nulle part. Cinq candidats socialistes, deux fiches.

Corriger cela — normaliser le libellé de parti — aurait été le vrai travail si l'objet avait eu un lecteur. Il n'en avait pas.

## 3. Ce que le retrait n'emporte pas

`identite.parti` et le champ `parti` des profils, qui sont **publiés et lus**. Une fiche de parti et l'étiquette partisane d'une personne sont deux choses ; l'issue le disait, et c'est la seule confusion qui rendrait ce lot dangereux.

## 4. Un défaut trouvé en chemin, et laissé où il est

En mesurant, deux choses sont apparues sur `tags_thematiques_agreges`, et **elles ne sont pas propres aux partis** :

| | `partis` | `groupes` | `lignees` | `gouvernements` |
| --- | ---: | ---: | ---: | ---: |
| fiches portant `poids_relatif` | 12/29 | **29/31** | **13/14** | 0/10 |

`groupes` et `lignees` sont **publiés**.

> **Corrigé le 14/09/2026.** Ce paragraphe affirmait aussi que **184 tags distincts** des fiches de parti étaient « des intitulés de textes plutôt que des thèmes, là où `AGENTS.md` §6 annonce 8 catégories ». **C'est faux, et la citation l'était aussi.** §6 dit mot pour mot l'inverse : « `tags_thematiques[]` — the **titles of the sitting items** spoken under (`theme_officiel`), deduplicated per profile; **never a closed list of categories** ». Un intitulé de texte est donc un tag **conforme** : « projet de loi de financement de la sécurité sociale pour 2026 » est exactement ce que la règle décrit.
>
> L'erreur venait de la copie d'`AGENTS.md` chargée en contexte au début de la session — le même fichier par symlink, mais antérieure à une modification — citée sans relire le disque. Elle a été relayée dans un commentaire de #906 et dans un message à la session interface, qui l'a attrapée en remesurant. **Une règle se relit là où elle vit**, pas dans la copie qu'on croit avoir.

C'est le périmètre de **#876**, et ce lot n'y touche pas : supprimer les fiches de parti n'aurait rien réglé, puisque le défaut vit surtout dans les fiches que l'interface publie. Consigné pour que la mesure ne soit pas refaite.

## 5. Un test perd son ancrage, et l'invariant reste

`test_les_profils_de_candidats_declares_ne_dependent_pas_du_roster` s'ancrait sur deux repères : la passe pivot des candidats déclarés et `src/parti_profile.py`, ce dernier venant **après** la branche roster — c'était le cas qui obligeait le repli roster à cesser de tuer le job.

Le second repère disparaît. Le premier est le plus fort des deux, et le test s'y ancre désormais : la passe pivot des déclarés, reconnaissable à `--enrich-parltrack`, précède `generate_roster_candidats.py`. Ce qui compte est que les déclarés soient publiés **avant** que le roster puisse échouer.
