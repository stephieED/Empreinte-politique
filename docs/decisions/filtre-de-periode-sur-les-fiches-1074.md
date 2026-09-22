<a id="filtre-de-periode-sur-les-fiches-1074"></a>

# Deux cases de période sur les fiches : 6 derniers mois, 12 derniers mois (#1074) (2026-09-22)

`2026-09-22`

> **En bref** — la propriétaire voulait un exemple de ce que l'outil permet : **que s'est-il passé à l'Assemblée, côté députés et côté gouvernement, sur la hausse des prix des carburants, ces six derniers mois ?** (#1029). Un calcul fait directement dans les données trouvait **10 interventions** de ministres sur le débat « prix des carburants », là où la fiche Lecornu II en affiche **49** : un rapport calculé à côté des fiches aurait publié des nombres invérifiables sur le site. D'où un **filtre de période sur les fiches elles-mêmes**, par les mêmes adaptateurs que le mot (#979) — la période réduit ce que la fiche lit avant qu'elle se construise, figures et listes suivent. **Deux durées fixes, jamais une fenêtre libre** : deux dates libres sont l'outil idéal pour découper la période qui fait dire ce qu'on veut aux chiffres. **De vraies cases à cocher**, retenues sur maquette entre trois formes, mais **exclusives**. Les fenêtres se comptent **depuis la date des données**, lue par `sync-data` sur la `date_reference` des fiches de groupe — là où Backend compte les siennes (#1077) —, pour qu'une seule date vaille partout. Trois défauts de données sont apparus en chemin et sont réglés : la fiche de groupe ne datait pas sa parole (#1073, livré par Backend en #1077) ; la fiche de gouvernement n'en gardait que la première et la dernière date — **26 couples membre × débat sur 1 427** chez Lecornu II ne disaient pas combien de tours tombaient dans six mois, et le script qui les écrivait est le nôtre ; et six mois avant le 31 août tombaient le 3 mars au lieu du 28 février. **Les amendements des groupes se retirent sous une période** : comptés par dossier sur toute la législature, les recompter dans une fenêtre serait inventer.

## Le contexte

Le rapport « carburant » de #1029 devait répondre à une question d'actualité
avec des chiffres que le lecteur retrouve à l'écran. Sans borne de date, il
était faisable ; sur « ces six derniers mois », non : aucune fiche ne savait
filtrer par date, et la fiche de groupe ne datait même pas sa parole.

Mesuré le 22/09/2026 :

| | Ce qui existait |
| --- | --- |
| Fiche candidat | Toutes ses listes datées — les votes et amendements via les index partagés |
| Fiche de gouvernement | `paroles.json` : `premiere`, `derniere`, `tours` par membre et par débat |
| Fiche de groupe | `[intitulé, nombre de membres]` par législature, **aucune date** |
| Calcul à côté | 10 interventions de ministres « prix des carburants » ; la fiche en affiche 49 |

## La décision

### 1. Des durées fixes, et le même geste que le mot

« 6 derniers mois » et « 12 derniers mois ». Sans case cochée, la fiche montre
tout. La période vit dans l'adresse (`?periode=6m`), comme le mot, et agit au
même endroit : **avant** que la fiche se construise. Chaque figure porte son
étiquette — « Contenant « prix carburant » · depuis le 22/03/2026 » —, chaque
vide dit sur quoi il a filtré, et un élément sans date ne passe pas une
fenêtre active (§2 règle 5). Les sections des mandats se retirent sous une
période comme sous un mot.

Un texte porté est dans la fenêtre s'il y a été **actif** — sa dernière date y
tombe —, pas seulement s'il y a été déposé.

### 2. De vraies cases, exclusives

Trois formes jouées dans l'application et capturées : des pilules sous le
champ, des cases à cocher, des pilules sur la ligne du champ. **Retenues : les
cases à cocher.** Elles sont exclusives — cocher l'une décoche l'autre,
décocher la case active revient à tout —, ce qu'une case ne promet pas
d'elle-même ; c'est le coût accepté de la forme.

### 3. Une seule date de référence

Les fenêtres se comptent depuis la date des données, pas depuis le jour.
`sync-data` écrit `donnees.json` à partir de la `date_reference` la plus récente
des fiches de groupe — la date depuis laquelle Backend compte `fenetres_parole`
(#1077). Deux fiches ne peuvent donc pas afficher « depuis le » à deux dates
différentes. Sans date lisible, le fichier n'est pas écrit et les cases ne
filtrent rien.

### 4. Ce que chaque fiche a dû recevoir

| Fiche | Comment la période s'y applique |
| --- | --- |
| **Candidat** | Sur le profil pivot : interventions par leur date, textes par leur dernière date, votes et amendements par la date que porte leur index |
| **Gouvernement** | `vue-parole-gouvernement.mjs` garde désormais `seances` — la date de chaque séance, avec ses tours. Un membre compte sur un débat s'il y a au moins une séance dans la fenêtre, et ses tours sont recomptés dedans. **Exact** |
| **Groupe** | Backend publie, par débat, les membres distincts intervenus pendant chaque fenêtre et pendant leur appartenance au groupe (#1077), et la fenêtre porte son dénominateur. Aucune date par membre n'est publiée : les profils de roster ne sont pas des fiches publiées. Les scrutins et les textes du groupe se datent eux-mêmes. **Les amendements se retirent**, et la fiche le dit |

### 5. Des cases seulement là où elles filtrent

`FICHES_DATEES` nomme les fiches qui datent ce qu'elles montrent. Des cases
qui ne filtrent rien seraient du mobilier. Les pages éditoriales n'en ont pas.

## Les alternatives écartées

| Option | Pourquoi écartée |
| --- | --- |
| Calculer le rapport à côté, dans les données | Des chiffres invérifiables à l'écran : 10 là où la fiche dit 49 |
| Deux dates libres | L'outil idéal pour choisir la fenêtre qui arrange un propos |
| Des comptes par mois côté Backend | Des membres distincts ne s'additionnent pas d'un mois à l'autre |
| Des dates par membre dans la parole des groupes | Un relevé d'activité individuel des profils de roster dans un fichier public (§2 règles 3 et 7) |
| Des pilules | Plus proches du reste du site ; écartées par la propriétaire au profit des cases |

## Les garde-fous

`tests/test_filtre_periode_1074.py` : la fenêtre et le piège du calendrier, le
filtrage sur des entrées copiées du corpus, la date commune, les séances datées
du gouvernement, les fenêtres de groupe avec leur dénominateur, le retrait des
amendements, les cases exclusives et leur présence là seulement où elles
filtrent, l'étiquette et les vides qui disent la période. Les gardes de #979
sont mises à jour : elles verrouillaient des phrases vides écrites d'un seul
tenant et des conditions sur le mot seul.
