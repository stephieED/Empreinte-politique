<a id="sources-dans-les-bulles-1389"></a>

# Les sources dans les bulles de section de la fiche candidat (#1389, 2026-10-29)

`2026-10-29`

> **En bref** — Chaque bulle de section de la fiche candidat se termine par un pied : une ligne par source qui alimente la section, le nom du schéma de la page Sources en lien, et « mis à jour le JJ/MM/AAAA », la date à laquelle la collecte a relu cette source pour cette fiche (`sources[].synchro_le`, en heure de Paris). Forme B et mots arrêtés par la propriétaire sur maquette. Les fiches de groupe, de gouvernement et de législature attendent une date par source, demandée à la collecte le même jour.

## Le problème

Un lecteur du fil r/developpeurs (#1389) : « une donnée politique correcte mais périmée peut vite être prise pour une donnée actuelle ». Le site publiait `meta.genere_le` et `sources[].synchro_le` dans ses fichiers, et rien à l'écran : ni la date des données, ni la source d'une section, sauf pour les prises de parole (un lien « La source : les comptes rendus de l'Assemblée → »).

## La décision

La propriétaire a choisi le grain de la **bulle de section**, pas celui des bulles de survol d'une figure (une ligne répétée sur des centaines de points), et a demandé des noms « suffisamment parlants, dans la même idée que le nom des sources dans le diagramme de la page Sources ».

| Arbitré | Retenu | Écarté |
| --- | --- | --- |
| Forme (maquette https://claude.ai/artifact/1eeUpq1nF8LzkfoyFpJZCp) | **B** : un pied sous un filet, une ligne par source, nom à gauche, date à droite | A (une phrase « Source : …, consultée le … » dans la note) ; C (les cases colorées du schéma ; contraste faible du blanc sur le turquoise du Sénat) |
| Mot | « mis à jour le » | « consultée le » (« je n'aime pas le mot "consulté" ») ; la date seule, qui ne dit pas ce qu'elle date |
| Nom | celui de `SOURCES_SCHEMA`, à la lettre (« Assemblée Nationale - Data », « Parlement européen », « ParlTrack »…) | un nom propre à la bulle : un objet garde un seul nom sur le site |

Ce qui en découle :

- **Le lien de source des paroles est absorbé par le pied.** Il garde sa cible, la page du jeu de données des débats, plus précise que l'accueil du portail.
- **Une source sans date n'a pas de ligne.** Ni une source citée sans être interrogée (Sycomore, décrets de nomination du Journal officiel), ni un type absent du schéma (`TYPE_VERS_SCHEMA`).
- **Deux entrées du même type : la plus ancienne l'emporte**, pour ne jamais annoncer plus frais que la partie la moins fraîche.
- **Au téléphone**, la date passe sous le nom pour toutes les lignes : à 360 px, « Assemblée Nationale - Data » coupé sur deux lignes, seul parmi les autres, se lisait comme une anomalie (vu sur la maquette).

| Bulle | Sources déclarées |
| --- | --- |
| En bref | Assemblée, Sénat, Parlement européen, Répertoire national des élus |
| Les fonctions exercées | Assemblée, Sénat, Parlement européen |
| Versant Assemblée (textes, amendements, votes, écarts, paroles) | Assemblée |
| Versant européen | ParlTrack et Parlement européen (« Activité européenne, titres français » sur le schéma) |
| Ce qu'on n'a pas pu lire | les cinq |

`tests/test_sources_dans_les_bulles_1389.py` tient le nom, l'ordre, l'heure de Paris, la plus ancienne date, l'absence de ligne sans date, la déclaration de chaque bulle et le mot.

## Ce qui n'est pas fait

- **Les fiches de groupe, de gouvernement et de législature.** Leurs fichiers portent `sources[]` à raison d'une entrée par profil membre, et rien pour les sources qui ne passent pas par les profils (actes du Journal officiel, budgets, scrutins). Une date par source au niveau de la fiche a été demandée à la session Backend le 29/10/2026, avec la règle « la plus ancienne des profils lus » en proposition.
- **L'état du dernier passage de collecte**, source par source (#1389, point 4) : une panne ne se cache pas dans une bulle, elle irait dans « Ce qu'on n'a pas pu lire ».

## Ce qui n'est pas vérifié

- Le sens exact de `synchro_le` pour un profil que le dernier run n'a pas touché (le profil roster d'Abdelkader Lahmar dit 26/10 après le run du 28/10) : question posée à Backend. Le libellé « mis à jour le » en dépend.
- Au doigt, sur un vrai téléphone.
