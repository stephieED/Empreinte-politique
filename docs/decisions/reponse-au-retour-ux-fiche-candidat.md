<a id="reponse-au-retour-ux-fiche-candidat"></a>

# La réponse au retour d'ergonomie sur la fiche candidat : ce qui a été décidé, point par point (2026-10-01)

`2026-10-01`

> **En bref** — Le retour d'ergonomie du 01/10/2026
> ([`retour-ux-sur-les-fiches-candidat`](retour-ux-sur-les-fiches-candidat.md))
> portait six constats et trois « arbitrages prioritaires ». La propriétaire les a
> repris un par un, sur maquette, le même jour. **Quatre constats ont une réponse
> implémentée, deux restent ouverts.** La fiche de François Ruffin passe de
> **7 650 à 6 338 px** repliée, celle d'Anasse Kazib de **2 017 à 1 612 px**. Le gain
> vient des figures redessinées, pas des textes retirés. Trois règles sont sorties
> du travail et valent au-delà de la fiche candidat : **ce qui empêche une lecture
> fausse se voit dans la figure, sans clic** ; **une note aide à lire, elle ne
> justifie pas ce qu'on n'a pas fait** ; **la légende appartient à la figure**.
> La section des écarts avec le groupe **ne compare plus que la dernière
> lecture**, ce qui défait un point de
> [`derniere-lecture-retenue-711`](derniere-lecture-retenue-711.md).

## Pourquoi ce fichier existe

Le fichier du retour dit ce que le retour demandait et ce qui s'y opposait. Il
s'arrêtait à la fiche vide. Celui-ci dit **ce qui a été répondu au reste**, avec
les mesures et les mots validés, pour que la revue des fiches de groupe et de
gouvernement — qui suit — parte des règles posées ici et ne les rediscute pas.

Le second lot a sa propre décision, parce qu'il porte une palette et un modèle
de sélection :
[`carres-des-textes-et-couleurs-des-commissions`](carres-des-textes-et-couleurs-des-commissions.md).

## La réponse, constat par constat

| # | Constat du retour | Réponse | État |
| --- | --- | --- | --- |
| 1 | La page vide à 2 700 px | La fiche vide tient en une ligne par section (#1158), et « Ce qu'on n'a pas pu lire » y devient **une phrase** : la fiche d'Anasse Kazib fait 1 612 px | Fait |
| 2 | La surcharge de la fiche Ruffin | 7 650 → 6 338 px (−17 %). Voir le tableau par section | Fait, en partie |
| 3 | Les poignées de dépliage sans ancrage | Non traité | Ouvert |
| 4 | Le diagramme en rubans, illisible, et sa barre courte lue comme un échec | Remplacé par **un carré par texte**, rangé à l'étape atteinte | Fait, versant français |
| 5 | La profusion de textes explicatifs | 23 textes relevés **à l'écran**, jugés un par un ; les renvois deviennent des bulles | Fait |
| 6 | La fiche candidat comme « super-CV » | Non traité : c'est du positionnement | Ouvert |

### Ce que la mesure a montré d'abord

Le retour parlait d'une « profusion de disclaimers ». Le fichier du retour en
comptait 33 emplacements **dans le code**. Compté **à l'écran**, sur la fiche de
François Ruffin repliée : **23 textes**, pour environ 4 % de la hauteur de la
fiche. La surcharge ne venait donc pas d'eux. Ce sont les deux figures de
« Ce qu'il a proposé » et le tableau de « Ce qu'on n'a pas pu lire » qui
portaient le volume.

| Section, fiche de François Ruffin | Avant | Après |
| --- | ---: | ---: |
| En bref | 375 px | 342 px |
| 1 · Les fonctions exercées | 1 049 px | 1 050 px |
| 2 · Ce qu'il a proposé | 1 195 px | 825 px |
| 3 · Ce qu'il a voté | 1 299 px | 1 123 px |
| 4 · Où il a voté autrement que son groupe | 1 051 px | 863 px |
| 5 · Ce qu'il a dit | 1 055 px | 897 px |
| 6 · Ce qu'on n'a pas pu lire | 712 px | 324 px |
| **Fiche entière** | **7 650 px** | **6 338 px** |

Mesuré le 01/10/2026 sur l'application construite, à 1 280 px de large, plis
fermés.

## Les trois « arbitrages prioritaires », et ce qu'ils sont devenus

| Proposition du retour | Ce qui a été fait |
| --- | --- |
| Masquer les blocs vides | **Déclarer une fois, là où ça s'explique** : #1158 pour les sections vides, puis « Ce qu'on n'a pas pu lire » réduite à ce qui manque |
| Simplifier les dataviz | Fait sur les deux figures de la section 2, et une couleur fixe par commission |
| Regrouper les avertissements dans une modale | **La modale reste écartée.** Une **bulle ancrée au titre** a été retenue : elle reste à côté du fait qu'elle qualifie, ce qu'une modale ne fait pas |

## Les trois règles posées en chemin

Elles s'ajoutent aux sept règles de forme du `DESIGN_SYSTEM` §6 bis.

**1. Ce qui empêche une lecture fausse se voit dans la figure, sans clic.**
La plupart des lecteurs n'ouvrent pas une bulle. La première note écrite pour
les amendements prévenait que « le nombre d'amendements seul peut tromper » ;
la figure, elle, classait et dimensionnait ses barres par ce nombre. La
correction est allée dans la figure : la barre se découpe par texte, et le
biais se voit. D'où la répartition :

| Type de texte | Où il vit |
| --- | --- |
| Ce qui empêche une lecture fausse | dans la figure |
| Comment c'est construit | dans la bulle, en une ou deux phrases |
| Le raisonnement complet | dans la page de méthodologie |

**2. Une note aide à lire, elle ne justifie pas ce qu'on n'a pas fait.**
« Aucun taux d'adoption n'est calculé » a été refusé deux fois — les mots de la
propriétaire : « juste une justification de quelque chose qu'on n'a pas fait ».
C'est le même critère qui a fait retirer « Jamais totalisée » sous le titre de
la section 4 : la phrase n'empêchait personne de compter les lignes.

**3. La légende appartient à la figure.** Le pied de la section 1 portait la
légende de la ligne surlignée. Retiré, puis remis — **dans la carte**, en tête,
avec un échantillon de la marque. Une légende derrière un clic laisse la ligne
surlignée se lire comme une fonction plus importante que les autres.

Une quatrième règle porte sur les mots : **un texte d'aide s'écrit pour qui n'a
pas travaillé sur le projet.** Les premières bulles reprenaient mot pour mot la
page de méthodologie ; elles ont été jugées « illisibles ». Reprendre un texte
déjà publié ne le rend pas lisible.

## Les bulles

Une icône « i » à droite du titre ; au **clic** — un téléphone n'a pas de
survol —, une bulle : une phrase qui dit ce que la partie présente, une note,
un lien vers la méthodologie. Composant `InfoBulle.jsx` ; les textes sont dans
la constante `BULLES` de `CandidateProfile.jsx`, **validés au mot près**.

| Emplacement | Phrase | Note |
| --- | --- | --- |
| En bref | Le parcours d'élu, et l'activité en quelques chiffres bruts. | « Majorité » et « opposition » sont les qualifications déclarées par l'Assemblée nationale. Quand elle n'en déclare aucune, la fiche l'indique. |
| 1 · Fonctions | Les responsabilités tenues pendant les mandats, classées par durée dans chaque catégorie. | Une ligne sans rôle indiqué signifie simple membre. Une fonction longue n'est pas une fonction plus importante. |
| 2 · Textes portés (carte) | Les textes de loi dont la personne est l'auteur ou le rapporteur, rangés à l'étape qu'ils ont atteinte. | Seuls les textes examinés en commission sont affichés. Un texte arrêté à une étape n'est pas nécessairement rejeté. |
| 2 · Amendements (carte) | Les amendements dont il est l'auteur, répartis par thème de la commission. | Chaque segment d'une barre est un texte amendé. Sa largeur est le nombre d'amendements déposés sur ce texte. |
| 3 · Votes | Les votes sur les textes de loi en dernière lecture, par période de gouvernement. | Dernière lecture : le vote le plus récent sur le texte entier. Les votes sont regroupés par gouvernement pour distinguer ceux émis dans la majorité, la minorité ou l'opposition. |
| 4 · Écarts | Les votes où sa position diffère de celle de la majorité de son groupe parlementaire. | Seuls les votes en dernière lecture sont comparés, et uniquement sur les scrutins où une majorité se dégage dans le groupe. |
| 5 · Prises de parole | Les prises de parole à l'Assemblée, par période de gouvernement, par type et par sujet. | Les sujets sont les titres de l'ordre du jour de l'Assemblée. |
| 6 · Manques | Les limites de cette fiche : la date où chaque source commence, et ce qu'elle ne dit pas. | Avant cette date, la fiche ne sait rien. Cela ne veut pas dire qu'il ne s'est rien passé. |

« Période politique » a été refusé — « ça ne parle à personne » — au profit de
« période de gouvernement ». Le titre de période, lui, garde « Banc non
publié · gouvernement … » : décision explicite, à ne pas rouvrir.

## Ce qui a été décidé, section par section

**Section 1.** Le pied part. La légende de la ligne surlignée entre en tête de
carte.

**Section 2.** Les textes portés : un carré par texte, en quatre colonnes
(examinés en commission, discutés en séance, adoptés, promulgués). Survol d'un
carré : son titre ; clic : ce texte seul ; clic sur une colonne ou sur une
commission de la légende : les textes de l'étape ou de la commission. Les
amendements : la barre de chaque commission se découpe en un segment par
texte ; la colonne « ratio par texte » disparaît. **La couleur d'une commission
ne suit plus son rang sur la fiche** : les huit commissions permanentes ont
chacune la leur, la même partout ; les commissions spéciales partagent un gris.

La propriétaire a tenu à la couleur — « elle permet d'indiquer ce sur quoi le
candidat a proposé des choses […] pas juste le sort ». Passer les carrés à
l'encre avait été proposé, et refusé.

Six formes ont été maquettées pour les textes, sur la fiche la plus mince
(François Ruffin, 6 textes) et la plus fournie (Édouard Philippe, 170). La
barre éclatée qu'elle avait en tête tient, mais n'ouvre qu'un thème à la fois.

**Section 3.** « 168 textes — dernière lecture retenue pour chaque texte »
devient « Sur 168 scrutins de textes en dernière lecture ». La ligne « Période
7 sur 7 · 31 textes · les flèches ← → du clavier naviguent aussi » part : la
case noire de la barre des périodes dit la position, le nombre est répété deux
fois plus bas, et le raccourci clavier est un mode d'emploi.

**Section 4.** Le titre « Où il s'est écarté des siens » évoquait une
déloyauté ; « Où il se distingue de son groupe » aurait évoqué un mérite. Retenu :
**« Où il a voté autrement que son groupe »**. Les deux sous-étiquettes de
« Ce qui est comparable » et la phrase sous le titre de la liste partent.

**Section 5.** La phrase sous le titre part. La phrase sur l'archive des
comptes rendus devient le premier lien de la bulle.

**Section 6.** Voir plus bas.

## La section 4 ne compare plus que la dernière lecture

`derniere-lecture-retenue-711` excluait les écarts de la règle : « une
divergence en première lecture est un fait sur ce scrutin, pas une affirmation
sur la loi ». L'argument tient pour une liste. Il n'explique pas pourquoi la
section 3 fait l'inverse, et il laissait deux défauts : la section 4 montrait
des écarts sur des votes que la section 3 ne montre pas, et une même loi
paraissait deux fois dans la liste.

La propriétaire a tranché pour **une règle unique sur toute la fiche** — celle
que le site annonce : un texte, une position.

| Mesuré le 01/10/2026, 31 fiches candidat publiées | Toutes lectures | Dernière lecture |
| --- | ---: | ---: |
| Scrutins comparés, sur les 11 fiches qui ont une base | 1 940 | 1 304 |
| Écarts affichés, sur les 8 fiches qui en portent | 95 | 57 |
| Fiches qui gardent au moins un écart | 8 | 8 |

**Le prix, connu** : 19 lois sur lesquelles la personne ne s'est écartée qu'à
une lecture intermédiaire ne sont plus publiées, dont 16 sur la fiche de
Delphine Batho. `ecartsAvecLeGroupe` reçoit la sélection de `votesDuProfil` ;
aucune seconde sélection n'est écrite.

Un défaut ancien a été trouvé en vérifiant ces nombres, et **n'est pas
corrigé** : une personne passée par deux groupes dans une législature voit
chaque scrutin comparé aux deux (#1159).

## « Ce qu'on n'a pas pu lire » : une seule liste de manques

La section publiait un tableau — « couvert depuis », « hors couverture
jusqu'au », « N entrées ». Trois défauts mesurés : il disait deux fois la même
borne ; ses dates étaient les mêmes sur toutes les fiches, donc il ne disait
rien **de la personne** ; et ses « 48 448 entrées » d'amendements contredisaient
les 5 396 de la section 2, parce qu'elles comptaient les cosignatures.

La fonction première de la section est de dire **ce qui manque**. Ce que les
sources portent, et depuis quand, a déjà sa page : `/couverture`.

La section devient une carte, « Ce qui manque sur cette fiche », une ligne par
manque (`manquesDeLaFiche`) :

1. les mandats que la source ne couvre pas — « Son mandat de juin 2007 à juin
   2012 n'est pas couvert : la source commence le 20 juin 2012 » ;
2. la qualification de groupe que l'Assemblée n'a pas déclarée ;
3. l'entrée au gouvernement que la source ne date pas ;
4. les votes sans commission ou sans sort connus, et les prises de parole sans
   texte ou sans qualité — les deux encadrés « Ce que cette figure ne sait
   pas », qui quittent les sections 3 et 5 ;
5. les autres limites, inchangées ;
6. « Avant juin 2002 — Nos sources ne connaissent aucun mandat avant le 19 juin
   2002 », sauf si la fiche porte déjà des mandats antérieurs.

Une fiche sans mandat parlementaire porte une phrase : « Nos sources ne
connaissent aucun mandat parlementaire de cette personne. » Elle dit ce que les
sources savent, pas un fait sur la personne.

**La liste se calcule sans relecture.** La propriétaire l'a posé : « on n'est
que sur du processus automatique ». Une première forme écrivait « Rien : nos
sources couvrent tous ses mandats » ; cette phrase supposait une vérification
humaine, elle est partie. Les fichiers écrits à la main et committés dans le
dépôt — `config/mandats_anterieurs.json` et les tables de correspondance — ne
sont pas concernés : la propriétaire les a validés. Sa ligne rouge est une
donnée allée chercher hors du dépôt sans son accord.

L'état `non_collecte` du pipeline ne s'affiche plus. Il publiait « collecte
écartée par le run qui a produit le profil brut (meta.collecte_ecartee, #357) »
en face d'une liste de plusieurs milliers d'entrées, sur 16 des 31 fiches.

## Ce que cette revue rend caduc dans les décisions antérieures

Une décision ne se réécrit pas en place : elle dit ce qui était vrai le jour où
elle a été prise. Quatre d'entre elles décrivent un état que cette revue a
changé, et se lisent désormais avec celle-ci.

| Décision | Ce qui n'est plus vrai |
| --- | --- |
| [`derniere-lecture-retenue-711`](derniere-lecture-retenue-711.md) | « Il ne touche pas `ecartsAvecLeGroupe` » : la section des écarts suit maintenant la dernière lecture |
| [`preuve-de-borne-dite-une-fois-328`](preuve-de-borne-dite-une-fois-328.md) | Le mécanisme qui disait une borne une seule fois par ligne du tableau est retiré avec le tableau |
| [`pourquoi-en-methodologie-328`](pourquoi-en-methodologie-328.md) | Le renvoi en pied de section et le critère sous le titre : le renvoi vit dans la bulle, les critères des sections 4 et 5 sont partis |
| [`divergences-avec-le-groupe-328`](divergences-avec-le-groupe-328.md) | Le titre de la section, ses deux sous-étiquettes, et la base comparable mesurée sur toutes les lectures |

Le fichier du retour, lui, comptait « 33 emplacements de texte explicatif » :
c'était un compte d'occurrences dans le code. Le compte à l'écran est 23.

## Ce qui a changé de place dans le code

Pour qui reprend la fiche : `InfoBulle.jsx` (la bulle), `CarresTextes.jsx` et
`utils/carresTextes.js` (les textes portés), `utils/commissions.js` (les
couleurs fixes), `manquesDeLaFiche` dans `utils/profilCandidat.js` (la liste de
la section 6), et `candidate.manques` dans la vue (les nombres des deux
encadrés retirés des sections 3 et 5). Le versant européen garde `Cascade`.

## Ce qui reste ouvert

| Sujet | Où il en est |
| --- | --- |
| Le versant européen | Cinq fiches sur 31 ont une activité au Parlement européen. Quatre textes de bulle sont proposés et maquettés, **non validés** ; la figure des textes portés y garde ses rubans |
| Les mandats au Sénat et au Parlement européen en section 6 | Exclus du calcul des mandats non couverts ; aucune règle n'est posée pour eux |
| La double comparaison de la section 4 | #1159 |
| L'ancrage au clic (constat 3) | Non mesuré |
| La fiche candidat comme « super-CV » (constat 6) | À la propriétaire |
| Les modes d'emploi restants | « Choisissez un sujet… » en section 5 |
| La page de méthodologie | Elle écrit encore « un ruban, une barre ou une étiquette ouvre la liste » |
| La palette | Défense est à peine distincte du vert des votes « pour » ; la paire Affaires sociales / Finances est faible en tritanopie |
| Les fiches de groupe et de gouvernement | La revue suit ; elles gardent la couleur au rang |

## Ce qui a servi, et où le retrouver

Chaque décision a été prise sur une maquette rendue sur l'application
construite, par injection dans la page servie, puis la fiche entière a été
rendue avant et après. Une forme cachée derrière un bouton a été lue comme
« je ne vois rien » : **les formes à comparer se montrent empilées, visibles
d'emblée**.

Trois pièges payés, pour la suite :

- **Compter à l'écran, pas dans le code.** Les 33 « emplacements » étaient des
  occurrences d'un mot, commentaires compris ; un sélecteur CSS en trouvait
  dix ; la lecture des captures en a rendu 23.
- **Agrandir avant de dire qu'une légende manque.** La légende des votes
  existait ; elle avait été lue sur une capture réduite et coupée.
- **Une capture pleine page par session de navigateur.** La machine manque de
  mémoire, et le noyau tue le navigateur de capture au second.
