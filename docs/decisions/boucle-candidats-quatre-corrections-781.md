# La boucle du périmètre a cassé quatre fois au même endroit (#771, #775, #781)

`2026-09-08`

> **En bref** — une seule décision pour trois lots parce qu'ils n'ont qu'une histoire : #757 a fermé la boucle et elle a rouvert **trois fois**, sur le même geste — **borner une population à ce qu'on avait sous les yeux en l'écrivant** ; #771 résolvait ce qui est **neuf** quand la passe hors ligne a besoin de ce que **la table ne couvre pas** (1 h 18 de collecte, commit refusé), #775 réservait l'entrée à ceux qui ont un **profil publié** quand cinq candidats n'en auraient jamais eu sans entrée (verrou circulaire, troisième apparition de #715), #781 posait la seconde déclaration à l'écriture du **brut** et pas à la publication du **pivot** (cinq bruts sans pivot, commit refusé) ; le précurseur est #766, dont les trois entrées écrites **à la main** sont ce qui a fait diverger les deux populations de #771 ; corollaire de #771 : un fichier de résolutions s'écrit **même vide**, conditionner une étape sur la **présence** d'un fichier transformant « rien à ajouter » en « ne fais rien » ; garde-fous de #775 : `en_echec` (#484), `indetermine` qui ne vaut pas déclaration, un fichier absent qui ne déclare rien ; **ce que la série apprend** : deux fois sur quatre la prose du dépôt décrivait le piège — la décision de #757 prévenait que #715 était « borné à sa population », et le commentaire de `_normaliser_en_pivot` nommait le défaut mot pour mot —, et **un avertissement écrit ne protège pas celui qui l'écrit** ; ce qui a attrapé les défauts, ce sont les garde-fous **exécutables** (§5b, « collecté mais non publié » #511, la liste blanche du sparse-checkout, un banc refusant un `args` sans attribut) ; d'où la règle : **quand une règle décide d'une population, chercher sa jumelle avant de committer**, les tests vérifiant désormais la paire et non la place ; **non réparé** : les cinq de #775 restent non publiés pour une cause hors série — les artifacts d'extraction n'atteignent pas `merge-and-pivot` —, et le run vert l'est **parce que** la collecte n'arrive pas.

Une seule décision pour trois lots, parce qu'ils n'ont qu'une histoire : #757 a
fermé la boucle du périmètre des candidats, et elle a rouvert **trois fois**, sur
le même geste. Les séparer en trois fichiers rendrait chacun lisible et la série
invisible — or c'est la série qui est instructive.

## Le motif, énoncé une fois

**Borner une population à ce qu'on avait sous les yeux en l'écrivant.**

À chaque fois : une règle est posée pour la population qu'on regardait, elle est
juste pour elle, et elle devient fausse pour la population voisine — que rien ne
distingue à la lecture du code.

| Lot | La population regardée | Celle qui manquait | Ce que ça a coûté |
| --- | --- | --- | --- |
| #771 | ce qui est **neuf** | ce que la **table ne couvre pas** | 1 h 18 de collecte, commit refusé |
| #775 | ceux qui ont un **profil publié** | ceux qui n'en ont pas **et n'en auront jamais** sans entrée | 5 candidats bloqués, aucun run futur ne les débloquait |
| #781 | l'écriture du **brut** | la publication du **pivot** | 5 profils bruts sans pivot, commit refusé |

Et le précurseur, #766 : trois entrées `hors_an` écrites **à la main** parce que
la chaîne d'identifiants ne les corroborait pas. Ce geste manuel est précisément
ce qui a fait diverger les deux populations de #771 — la main a écrit des slugs
entre deux runs, et « ce qui est neuf » a cessé de coïncider avec « ce que la
table ne couvre pas ».

## Ce que chaque lot a réparé

**#771 — la population à résoudre.** Le job de tête ne résolvait que les entrées
neuves ou sans slug. La passe hors ligne, elle, a besoin des résolutions de
**tout slug sans entrée de table**. Les deux ensembles ont coïncidé exactement
une fois : au premier run. Corollaire posé au passage : le fichier de résolutions
s'écrit **même vide**, parce que conditionner une étape sur la *présence* d'un
fichier transforme « rien à ajouter » en « ne fais rien ».

**#775 — le verrou.** Pour recevoir une entrée de table il faut un profil publié
(filtre 2 de #715, il n'y a rien à corroborer sans lui) ; pour recevoir un profil
il fallait une entrée déclarant `hors_an` (#539). Aucun des deux ne pouvait
passer en premier. D'où une **seconde déclaration** d'absence : un identifiant
externe qui ne connaît aucun mandat AN à cette personne. Ce qu'elle ne relâche
pas : `en_echec` garde la branche (#484), `indetermine` ne vaut pas déclaration,
un fichier absent ne déclare rien.

**#781 — la symétrie.** #775 a posé la seconde déclaration à l'endroit qui écrit
le brut, pas à celui qui décide s'il devient un pivot. Le commentaire de
`_normaliser_en_pivot` annonçait le défaut **mot pour mot**, trois lignes plus
haut : « un candidat vérifié comme n'ayant jamais siégé aurait un profil brut et
aucun pivot : un “collecté mais non publié” créé par le lot censé le retirer ».
C'est arrivé, par le lot censé le retirer.

## Ce que la série apprend, et qui n'est pas « faire attention »

**Un avertissement écrit ne protège pas celui qui l'écrit.** Deux fois sur
quatre, la prose du dépôt décrivait exactement le piège — la décision de #757
prévenait que le correctif de #715 était « borné à sa population », et le
commentaire de `_normaliser_en_pivot` nommait le défaut avant qu'il n'arrive.
Les deux ont été lus, et les deux ont été rejoués.

Ce qui a réellement attrapé les défauts, ce sont les **garde-fous exécutables** :
la §5b sur les entrées manquantes, « collecté mais non publié » de #511, la liste
blanche du sparse-checkout, le banc qui refuse un `args` sans attribut. Chacun a
coûté un run, et chacun a nommé sa cause.

D'où la seule règle qu'on peut en tirer : **quand une règle décide d'une
population, chercher sa jumelle avant de committer.** Une déclaration qui
autorise la collecte doit autoriser la publication ; une résolution qui sert au
job de tête doit servir à la passe hors ligne. Les tests de ces trois lots
vérifient désormais la *paire*, pas la place.

## Ce que la série n'a pas réparé

Au 08/09/2026, les cinq candidats de #775 ne sont toujours pas publiés — pour une
cause qui n'est plus dans cette série : les artifacts d'extraction n'atteignent
pas `merge-and-pivot` (« Répertoire source absent, ignoré : `_artifacts/an` »),
alors qu'ils existent. Le run `34241352524` conclut vert **parce que** la
collecte n'arrive pas : sans profil brut, le garde-fou de #511 n'a rien à
signaler. Un vert qui vient d'une absence.

Suivi dans #775, qui reste ouverte pour cette raison.
