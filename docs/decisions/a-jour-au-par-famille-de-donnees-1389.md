# « À jour au » : la dernière relecture réussie de chaque famille de données, et son état (#1389) (2026-10-29)

`2026-10-29`

> **En bref** — les fiches agrégées (lignée, gouvernement, législature) terminent chaque bulle de section par « <source> · à jour au JJ/MM/AAAA » (forme B, validée par la propriétaire). Cette date est **la dernière relecture réussie** de la donnée à sa source, pas la date de son dernier changement : `sources[].synchro_le` garde ce second sens dans le corpus, pour le débogage et l'audit. Arbitré le 29/10/2026, avec une date par **famille de données** et non par source, parce qu'un run manuel ou limité ne relit pas une source en entier. `pivot_data/fraicheur_sources.json`, composé par `merge-and-pivot` à partir de relevés publiés par les jobs d'extraction ; une famille lue à travers un cache est datée par la date d'écriture de son fichier témoin, que le cache restaure telle quelle.

## Contexte

La session interface a demandé une date par source pour les pieds de section
(#1389). Ce que porte le corpus, relevé le 29/10/2026 :

- `sources[].synchro_le` d'un profil date le dernier **changement** :
  `merge_profile.preserve_stable_freshness_timestamps` (#343) restaure
  l'ancienne date quand le contenu régénéré est identique. Le profil roster
  `abdelkader-lahmar` disait le 26/10 alors qu'un run avait tourné le 28/10.
- Une fiche agrégée porte une entrée de `sources[]` par membre : agréger ces
  dates (la plus ancienne, comme le proposait l'interface) afficherait 2017 sur
  une lignée dont les membres d'une législature close ne changent plus.
- Les sources de l'Assemblée passent par des caches quotidiens ou hebdomadaires
  dont les `restore-keys` restaurent une entrée plus ancienne (#555 : le
  24/08/2026, une entrée du 20/08 restaurée et resauvegardée sans qu'une
  archive soit retéléchargée).
- Le run planifié coche toujours « interventions » et « dossiers
  législatifs » (`generate-data.yml`, `github.event_name == 'schedule'`), un run
  manuel les laisse décochées par défaut, et `test_slugs` / `roster_limit`
  réduisent le périmètre.

## Décision

1. **Deux dates, deux usages** (arbitré par la propriétaire) : « à jour au »
   sur le site ; « mis à jour le » (`synchro_le`) gardé tel quel dans le corpus.
2. **Une date par famille de données**, `<source>.<famille>` : 13 familles,
   celles qui alimentent les trois fiches agrégées (`an.mandats`,
   `an.gouvernements`, `an.votes`, `an.interventions`, `an.questions`,
   `an.dossiers`, `an.amendements`, `an.ordre_du_jour`, `an.articles_votes`,
   `jo.actes`, `budget_etat`, `drees`, `unedic`). La fiche candidat garde ses
   dates par profil.
3. **Une famille n'avance que si** ses jobs ont réussi, sur tout le périmètre,
   avec sa case cochée quand elle en dépend, et si sa date a pu être relevée.
   Sinon elle garde sa date précédente ; jamais relue, elle vaut `null` avec sa
   `raison` (§2 règle 5).
4. **La date d'une famille lue à travers un cache** est la date d'écriture de
   son **fichier témoin** (l'archive, ou l'index construit à partir d'elle),
   heure de Paris, la plus ancienne entre les shards qui l'ont lue. Les caches
   d'Actions la restaurent (`tar -xf` sans `-m`, vérifié dans le journal du
   run `40734395125`). Même raisonnement que `_etat_au_archive_courante` (#1317).
   Un shard sans le témoin n'a pas lu la source : il ne date rien et ne bloque
   rien.
5. **L'état du job voyage avec son relevé** (`job.status`) :
   `extract-an` et `extract-roster-groupes` sont `continue-on-error`, et
   `needs.<job>.result` n'y suffit pas.
6. **Les familles sans cache** (actes du JO, ordre du jour, articles votés,
   budgets, gouvernements) prennent la date du run quand leur job a réussi :
   leurs archives sont retéléchargées à chaque run.

7. **L'état de la collecte, par famille** (arbitré le 29/10/2026, « pas par
   source mais par famille ») : `etat` vaut `a_jour`, `en_echec` (avec
   `en_echec_depuis`, le premier run en échec depuis la dernière réussite) ou
   `non_relue` (case décochée, run limité, job sauté). Un run qui ne tente pas
   la famille laisse un échec en place : il ne prouve pas la réparation. Un job
   réussi dont aucun shard n'a le fichier témoin est un échec : il n'a rien lu
   de ce qu'il devait lire. Le mot est « en échec », pas « cassée » : l'état
   d'un job ne dit pas si la source est tombée ou si notre code est en faute
   (#562). `motif_dernier_run` dit pourquoi une famille n'est pas à jour.

## Alternatives écartées

- **Une date par source** : fausse dès qu'un run ne relit pas toutes les
  familles d'une source.
- **Un champ « dernière visite » par profil**, à côté de `synchro_le` : la
  relecture est la même pour tous les profils d'une famille ; la répéter dans
  chaque profil coûte sans rien dire de plus.
- **La date du run** pour les familles derrière un cache : elle annoncerait
  plus frais que la donnée.
- **Un fichier sentinelle écrit au téléchargement** : la date d'écriture du
  fichier le donne déjà, sans toucher au `path:` des caches (donc sans en
  changer la version).

## Ce qui reste approché

- Les trois budgets avancent ensemble sur la réussite de
  `extract-finances-etat` : un échec de la seule Drees retient aussi la date du
  budget de l'État. Jamais plus frais que la donnée, parfois plus ancien.
- La date des familles sans cache est celle de la composition, en fin de run :
  un run lancé à 23 h peut finir le lendemain.

## Non vérifié

- Le premier run : les relevés, leur téléchargement en `merge-multiple`, et
  les dates obtenues.
- Que tous les shards d'`extract-an` aient le témoin AMO30 et `scrutins.json` :
  un shard sans eux ne bloque rien, mais il ne doit pas être le seul.
