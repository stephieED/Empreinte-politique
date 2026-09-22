<a id="amendements-par-mot-sur-les-fiches-1029"></a>

# Trouver les amendements d'un sujet par leur exposé, sur les fiches (#1029) (2026-09-22)

`2026-09-22`

> **En bref** — voie 2 de #1029. L'intitulé d'un amendement est celui de son dossier (« projet de loi de finances ») : « carburant » rendait 0 amendement. Backend publie l'index des mots des exposés (#1092, 93 Mo pour quatre législatures). Arbitré le 22/09/2026 (option A, groupe et candidat) : le filtre par mot retient aussi un amendement dont **l'exposé** porte le mot. Le build tire, par fiche, le vocabulaire de ses seuls amendements ; la lecture reprend `amendements_contenu.py` à l'identique, un test compare les deux. **Sur la fiche de groupe, les amendements reviennent sous une période** : une table par maillon (type, sort, date, texte visé de chaque amendement distinct) permet de recompter la répartition par la règle du build, `repartitionParCommission`, sur les seuls types vérifiés. Cela lève le retrait décidé pour #1074, dont la cause — une projection datée par dossier — disparaît. Tables écrites sans contenu indexé : 44,9 Mo pour les maillons, chargées au premier mot ou à la première période.

## La décision

- **Candidat** : `<slug>.amendements-mots.json`, le vocabulaire des exposés de ses amendements, par législature, chargé au premier mot. Un amendement reste si l'intitulé de son dossier OU son exposé porte le mot.
- **Groupe** : `<maillon>.amendements.json`, la table des amendements distincts du maillon et le vocabulaire de leurs exposés. Sous un mot ou une période, la répartition se recompte amendement par amendement.
- **La règle de recherche** est celle de Backend : mots de 4 lettres ou plus, ramenés à leur forme indexée (`forme_indexee`), puis cherchés par inclusion dans les clés, comme le filtre cherche un intitulé.

## Les limites

- Un mot de moins de 4 lettres (« TVA ») ne cherche que dans l'intitulé.
- Un mot présent dans plus de 3 % des amendements d'une législature n'est pas indexé.
- Plusieurs mots sont cherchés dans le même exposé, sans ordre ni proximité.
- Les XIVe à XVIe arrivent une par run (#1092) : avant, leurs amendements ne se trouvent que par l'intitulé.

## Les alternatives écartées

- **Charger l'index de la législature dans la page** : 17 à 37 Mo.
- **Garder le retrait sous une période sur la fiche de groupe** : la démonstration de #1029 (« ces six derniers mois ») n'aurait montré aucun amendement côté députés.
