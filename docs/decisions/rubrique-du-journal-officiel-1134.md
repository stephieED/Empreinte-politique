<a id="rubrique-du-journal-officiel-1134"></a>
# La rubrique du Journal officiel se lit dans le conteneur, et ne se devine pas dans les titres (#1134) (2026-09-25)

`2026-09-25`

> **En bref** — La source distingue « Textes généraux » de « Mesures nominatives », mais elle le dit dans le **conteneur** de la livraison — la table des matières du JO — que notre collecte jetait. Branchée, elle range l'arrêté « personnes autorisées à exercer la profession de médecin » en mesure nominative, là où aucun filtre par titre ne l'attrapait. Publiée **à côté** des lignes d'actes, jamais devinée, `null` quand la source ne l'a pas dite.

## Constat

La section « mise en application des lois » d'une fiche de gouvernement compte
les actes qui citent une loi. Mesuré sur la fenêtre de Lecornu II : **308 des
395 actes qui citent une loi par son numéro citent la même**, la LFSS 2007, et
ce sont des arrêtés *« fixant la liste des personnes autorisées à exercer en
France la profession de médecin »*.

78 % de ce que la fiche appellerait « mise en application des lois » serait donc
une chaîne d'**autorisations individuelles de praticiens**. Le filtre par titres
qui écarte les actes de personne — « portant nomination », « portant
cessation », « portant admission »… — ne les voit pas : leur intitulé n'emploie
aucune de ces formules.

## Ce que la source publie, et que nous jetions

Vérifié en téléchargeant deux livraisons brutes, pas déduit. Chaque livraison
porte, à côté des fichiers d'actes, un **conteneur** : le sommaire du Journal
officiel du jour. `<STRUCTURE_TXT>` y imbrique des `<TM>` — chacun avec son
`<TITRE_TM>` — et pour feuilles des `<LIEN_TXT idtxt="JORFTEXT…">`.

Trois rubriques sous « Décrets, arrêtés, circulaires » : **Textes généraux**,
**Mesures nominatives**, **Conventions collectives**, puis le ministère. Relevé
sur `JORF_20260909-003012` : 29, 52 et 6 sur 105 textes rangés.

**L'arrêté `JORFTEXT000054812249` y est classé en « Mesures nominatives »** —
par le Journal officiel lui-même. Le fait est de la source, pas notre lecture
(§2 règle 2).

`actes_reglementaires.py` filtrait les membres du tar sur `/texte/version/` et
`/article/` : les conteneurs n'étaient jamais ouverts.

## Décision

Le filtre laisse passer `/conteneur/`, et `rubriques_du_conteneur` rend
`(identifiant, rubrique)` pour chaque texte du sommaire.

**La chaîne est rendue telle que la source la compose**, racine retirée :
`Décrets, arrêtés, circulaires > Mesures nominatives > Ministère de la santé…`.
On n'en extrait aucun niveau « utile » et on n'invente aucune nomenclature — un
lecteur qui cherche les actes de personne demande si « Mesures nominatives » est
dans la chaîne. La racine, « Journal officiel "Lois et Décrets" », ne distingue
rien : tous les textes en dépendent, et la publier alourdirait chaque chaîne.

**Publiée à côté des lignes, pas dedans.** `rubriques` est la table,
`rubrique_des_actes` est **aligné sur `ids`** — comme `articles` l'est dans
`amendements_contenu`. Ajouter une 7e colonne à `actes` aurait cassé tout
lecteur dépaquetant six valeurs : le test du dépôt l'a fait immédiatement, et
une section d'interface en cours de relecture les lit aussi. Un lecteur qui
ignore les deux nouvelles clés ne voit aucun changement.

**`null` veut dire que la source ne l'a pas dite ici**, jamais « acte général »
(§2 règle 5).

## Alternatives écartées, mesurées

| Piste | Pourquoi non |
| --- | --- |
| Le **NOR** | Sa dernière lettre est la NATURE, pas la portée : sur les 97 423 NOR de 60 mois du fonds, 76 622 en `A` (arrêté) et 19 992 en `D` (décret). Rien d'exploitable |
| Le **titre** | C'est le point de départ du problème : les 308 arrêtés n'emploient aucune formule d'acte de personne |
| Extraire un niveau « portée » de la chaîne | Il faudrait décider où finit la rubrique et où commence le ministère. La source ne le marque pas ; le deviner serait inventer une nomenclature |

## La limite, et elle est structurelle

Un run ne relit que `MOIS_RELUS` mois. **La rubrique n'apparaîtra donc que sur
les actes des mois relus** ; les 389 000 actes déjà publiés restent sans, sauf
relecture complète du fonds — qui est un autre chantier, du même ordre que la
reprise du dump global.

Toute vue qui compte des actes « généraux » doit donc déclarer cette borne, et
ne jamais lire une rubrique absente comme une rubrique connue.
