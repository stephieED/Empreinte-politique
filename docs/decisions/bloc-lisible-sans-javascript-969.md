<a id="bloc-lisible-sans-javascript-969"></a>

# Les faits d'une fiche sont écrits dans le HTML, lisibles sans JavaScript (#969) (2026-09-17)

`2026-09-17`

> **En bref** — mesuré en production le 17/09/2026, après #1002 : le corps d'une fiche servie contenait **0 caractère** — tout est construit par React, que Google exécute mais que les robots des modèles de langage (GPTBot, ClaudeBot, PerplexityBot) n'exécutent en général pas ; ils ne lisaient donc que le titre et la description, ~180 caractères. `scripts/bloc-sans-js.mjs` écrit au build, **dans le conteneur de l'application**, les faits déjà publiés — mandats et fonctions avec leurs dates et leur source, composition d'un gouvernement, groupes d'une lignée — et React les remplace au démarrage : **52 fiches** (30 candidats, 12 lignées, 10 gouvernements), **705 caractères** sur la fiche Mélenchon contre 20 831 avec JavaScript, **390 Ko** de HTML au total, 10 Ko au maximum. Arbitré sur maquette, cinq fiches réelles, et instruit avec la session backend. **Rien n'est écrit à la main** : le bloc est refait à chaque build depuis les mêmes fichiers que les pages — un candidat qui se déclare a le sien, une candidature déclinée n'a plus de page (#761). **Ce qu'il ne porte pas** : aucun compte d'activité (règle 1), aucun `meta.avertissements` (ils portent un destinataire, parfois l'agent de collecte), aucun `notableCount` (§6), aucun statut de texte tant que #997 n'a pas tranché. **Deux pièges de données, tenus par des tests** : la période se lit sur `actif` et jamais sur la présence de `fin` — un mandat local clos peut n'avoir pas de fin (#922/#966) —, et une fiche sans mandat déclare que **la collecte des mandats locaux commence en 2020**, sans jamais écrire « aucun mandat local ». 10 tests, deux mutations vérifiées échouantes, rendu vérifié dans Firefox JavaScript activé puis coupé.

Ancres : `bloc-sans-js.mjs`, `pages-par-adresse.mjs`.

## Contexte

#999 a donné un statut 200 à chaque adresse, #1002 un titre et une description.
Restait ce que la page **dit** : rien, tant que le JavaScript n'a pas tourné.
La propriétaire veut les fiches lisibles par les moteurs **et** par les modèles
de langage ; ces derniers lisent le fichier servi, pas la page rendue.

Trois options lui ont été présentées : ne rien faire ; écrire un résumé factuel
au build ; pré-rendre la page entière (rendu React au build), qui demanderait de
revoir le chargement des données, fait dans le navigateur. La deuxième a été
retenue le 17/09/2026.

## Décision

| Fiche | Ce que le bloc porte |
| --- | --- |
| Candidat | nom, candidature déclarée 2027 · étiquette, mandats et fonctions (`mandat_electif`, `fonction_gouvernementale`, `mandat_local`) avec période et source |
| Lignée | nom, chambre, période, nombre de personnes ayant siégé, groupes de la lignée |
| Gouvernement | nom, période, nombre de membres, composition avec portefeuille et période |

Chaque bloc finit par la date du build, la phrase qui nomme ce que JavaScript
ajoute, et les liens vers `/sources` et `/methodologie`.

**Le bloc vit dans `<div id="root">`.** Hors du conteneur, React ne le
remplacerait pas et la page l'afficherait deux fois.

## Ce que le lot ne fait pas

Les quatre pages fixes (méthode, sources, FAQ, mentions légales) restent vides
sans JavaScript : leur contenu est écrit dans des composants React, pas dans les
données. Les publier en clair demanderait de les sortir du code, ou de
pré-rendre — c'est la troisième option, non retenue.

## Alternative écartée

**Un bloc masqué aux lecteurs et servi aux robots** : c'est du contenu caché,
sanctionné par les moteurs, et surtout deux versions d'une même page — celle que
le lecteur voit et celle que la machine lit.
