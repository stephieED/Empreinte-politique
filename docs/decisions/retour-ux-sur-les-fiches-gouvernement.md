<a id="retour-ux-sur-les-fiches-gouvernement"></a>

# Le retour d'ergonomie sur les fiches de gouvernement : ce qu'il dit, ce que la mesure en confirme, et ce qu'il a mal lu (2026-10-04)

`2026-10-04`

> **En bref** — Troisième retour extérieur, après ceux des fiches candidat
> ([`retour-ux-sur-les-fiches-candidat`](retour-ux-sur-les-fiches-candidat.md))
> et des fiches de groupe
> ([`retour-ux-sur-les-fiches-groupe`](retour-ux-sur-les-fiches-groupe.md)).
> Il porte sur trois fiches de gouvernement — Borne, Lecornu I, Fillon I — et
> pose sept constats et trois recommandations. **Ses mesures de hauteur se
> reproduisent** : la fiche Borne passe de 4 467 px à 10 550 px quand on ouvre
> son pôle le plus chargé et son premier sujet de parole (le retour écrit
> 10 522). **Trois de ses lectures sont fausses, et la première touche sa
> recommandation principale** : les « 21 interventions complètes » du sujet
> ouvert sont 21 membres intervenus, dont les propos sont des extraits déjà
> limités à cinq par membre, avec un bouton pour la suite — la pagination
> qu'il recommande existe. Ce fichier consigne le retour et ce que la mesure
> en dit. **Rien n'est arbitré** : le volet gouvernement de la revue n'a pas
> commencé.

## Pourquoi ce fichier existe

Le retour est la matière de départ du volet « gouvernement » de la revue
d'ergonomie, comme les deux autres l'ont été de leur volet. Sans trace, ses
points se représenteront comme des idées neuves ; transmis sans leur
vérification, ils se liront comme une liste de corrections à appliquer. Or sa
première recommandation demande ce que la fiche fait déjà, et sa troisième
compare la fiche à un état de la fiche de groupe qui n'existe plus.

## D'où viennent les mesures

Le retour dit avoir été « mesuré le 30 septembre 2026 sur les 17 gouvernements
publiés ». **Le nombre se retrouve** : le site publie 17 fiches de
gouvernement. Les trois fiches citées ont été remesurées le 04/10/2026 sur
l'application construite depuis `main` (`fe44777a2`), à 1 440 px de large.

| Fiche | Repliée | Tiroirs de pôle | Le plus grand tiroir de pôle | Sujets de parole | Pôle le plus chargé et premier sujet ouverts |
| --- | ---: | ---: | ---: | ---: | ---: |
| Borne (`BORNE`) | 4 467 px | 10 | +243 px, 9 rattachés | 10 | 10 550 px |
| Lecornu I (`LECORNU`) | 3 458 px | 1 | +77 px, 2 rattachés | 0 | 3 535 px |
| Fillon I (`FILLON_1`) | 3 616 px | 0 | — | 0 | 3 616 px |

Les valeurs du retour sont 4 467 → 10 522 px pour Borne, 3 458 → 3 535 px pour
Lecornu I, et un écart de 0 px pour Fillon I. Les deux dernières se reproduisent
à l'unité ; la première à 28 px près, écart non expliqué — quatre jours et
plusieurs runs de données séparent les deux mesures.

**Sur la fiche Borne, presque tout le gain vient du sujet de parole, pas du
pôle** : le tiroir du pôle ajoute 243 px, le sujet « motion de censure » à lui
seul 5 880 px.

| Section, fiche Borne repliée | Hauteur |
| --- | ---: |
| En bref | 393 px |
| 1 · Qui le composait | 734 px |
| 2 · Sur quoi ils ont pris la parole | 587 px |
| 3 · Ce qu'il a fait déposer | 651 px |
| 4 · Ce qu'il a fait entrer en vigueur | 1 037 px |
| 5 · Ce qu'on n'a pas pu lire | 264 px |

## Ce que le retour dit

| # | Constat | Vérifié ? |
| --- | --- | --- |
| 1 | La fiche Borne gagne 6 055 px quand on ouvre le pôle le plus chargé et le sujet « motion de censure » : « l'injection de 21 interventions complètes » recrée un défilement interminable | **Oui pour la hauteur, non pour sa cause.** Voir plus bas |
| 2 | Les fiches courtes ou anciennes ne bougent pas : +77 px sur Lecornu I, 0 px sur Fillon I | **Oui**, à l'unité. Fillon I ne porte ni tiroir de pôle ni sujet de parole |
| 3 | Les tiroirs exclusifs obligent à des allers-retours pour comparer plusieurs pôles ou plusieurs sujets | **Oui pour le mécanisme** : ouvrir un pôle referme le précédent, ouvrir un sujet referme le précédent. **Un pôle et un sujet restent en revanche ouverts ensemble** : l'exclusivité joue à l'intérieur de chaque famille, pas entre elles. Le coût des allers-retours n'est pas mesurable |
| 4 | Le diagramme de « Ce qu'il a fait déposer », « croisant les ministères et les statuts législatifs », est dense et risque d'assommer le lecteur | **Le fait cité est faux, le jugement n'est pas mesurable.** Voir plus bas |
| 5 | « Ce qu'il a fait entrer en vigueur » : la distinction entre actes nominatifs (−14 961) et actes réglementaires (17 056) est une bonne mise en contexte | **Oui pour les nombres** : 32 017 actes parus, 14 961 actes de personne, 17 056 actes qui touchent au droit. Les mots de la fiche sont « actes de personne » et « actes qui touchent au droit », pas « nominatifs » et « réglementaires » |
| 6 | Le « filtre » « le titre ne le dit pas » (16 006 actes) occupe une place prépondérante et traduit une limite technique plus qu'une information politique | **Oui pour le nombre et pour la place**, non pour ce que c'est. Voir plus bas |
| 7 | Les manques sont déclarés avec clarté, mais « Ce qu'on n'a pas pu lire » alourdit le bas de fiche de notes récurrentes | **Oui pour la citation** : Lecornu I écrit bien « un zéro mesuré, pas une absence de source ». La section fait 264 px sur Borne, 329 sur Lecornu I, 394 sur Fillon I, soit 6 à 11 % de la fiche repliée |

### Le constat 1 : 21 membres, pas 21 interventions complètes

Sur la fiche Borne, la ligne du premier sujet s'écrit « motion de censure —
**21 / 50** ». C'est le nombre de **membres du gouvernement intervenus** sur ce
sujet, sur les 50 dont la parole porte un sujet. Le retour l'a lu comme un
nombre d'interventions.

Ce que le sujet ouvert affiche réellement :

| Mesure, sujet « motion de censure » ouvert | Résultat |
| --- | ---: |
| Hauteur du bloc ouvert | 5 880 px |
| Blocs de membre affichés | 20 |
| Extraits affichés | 78 |
| Boutons « Afficher les 5 suivants » | 12 |
| Extraits restant derrière le premier de ces boutons | 634 |

Les propos ne sont pas « complets » : ce sont des extraits, coupés à 280
caractères, avec un lien vers le compte rendu. Et ils sont **déjà limités à
cinq par membre**, avec un bouton pour la suite.

Ce que cela établit, et ce que cela n'établit pas :

- **La hauteur est réelle, mais elle vient du nombre de membres, pas de la
  longueur de leurs propos.** Vingt blocs de membre, de un à cinq extraits
  chacun, font 5 880 px. Plafonner les extraits par membre ne la réduirait
  qu'à la marge ; c'est la liste des membres qui est longue.
- **Le nombre le plus visible de la ligne a été lu pour ce qu'il n'est pas**,
  comme le « 51 textes communs » de la fiche de groupe lu comme un
  pourcentage. C'est la seconde fois qu'un relecteur prend un compte de
  personnes ou de textes pour autre chose : la règle 8 du `DESIGN_SYSTEM`
  §6 bis s'applique.
- **Un écart non expliqué** : la ligne annonce 21 membres, le sujet ouvert en
  affiche 20 blocs.

### Le constat 4 : des commissions, pas des ministères

Le diagramme de « Ce qu'il a fait déposer » ne croise pas des ministères et
des statuts. À gauche, il porte la **matière** du texte — la commission
chargée de l'examiner ; à droite, l'**étape** qu'il a atteinte. Sur la fiche
Borne : onze entrées à gauche (« Affaires étrangères (27) », « Affaires
sociales (16) », « Lois (16) »… et « Matière non établie (15) »), sept à droite
(« Promulgué (19) », « Adopté (12) », « Adopté après CMP (27) », « Adopté via
49.3 (6) », « Navette en cours (4) », « Déposé (39) », « Rejeté (4) »). La
figure fait 432 px de haut.

Les ministères sont sur l'**autre** diagramme, celui des actes, une section
plus bas. Le retour a prêté à la première figure l'axe de la seconde.

Le retour ajoute « à l'instar des fiches groupes ». Ce n'est plus vrai : la
fiche de groupe a quitté ses rubans pour des carrés le 04/10/2026
([`revue-ux-de-la-fiche-de-groupe`](revue-ux-de-la-fiche-de-groupe.md)). La
fiche de gouvernement est désormais **la seule des trois à garder un diagramme
de flux** pour les textes.

### Le constat 6 : une destination du flux, pas un filtre

« Le titre ne le dit pas » n'est ni un filtre ni une catégorie de ministère.
Le diagramme des actes va des ministères, à gauche, vers **ce que le titre de
l'acte déclare d'une loi**, à droite. Cette colonne de droite n'a que deux
valeurs :

| Ce que le titre déclare d'une loi, fiche Borne | Actes |
| --- | ---: |
| lié à une loi | 1 050 |
| le titre ne le dit pas | 16 006 |
| **Actes qui touchent au droit** | **17 056** |

Le retour a donc raison sur un point et tort sur un autre. **Raison** : 16 006
actes sur 17 056 arrivent dans une seule case, et la figure se lit d'abord
comme « presque tout est muet ». La proportion est du même ordre sur Lecornu I
(641 sur 681) et sur Fillon I (583 sur 594). **Tort** : cette case n'écrase
pas « la répartition par ministère », qui est sur l'autre bord du diagramme et
garde ses proportions.

Ce que la valeur veut dire relève de la décision qui a construit la figure
([`actes-sur-la-fiche-de-gouvernement-1029`](actes-sur-la-fiche-de-gouvernement-1029.md)),
pas de ce retour. Qu'elle soit « une limite technique d'indexation » est
l'interprétation du relecteur : elle n'a pas été vérifiée ici.

## Les trois recommandations, et ce qu'elles touchent

Aucune n'est tranchée. Chacune est notée avec ce qu'il faudra vérifier avant
de la suivre.

| Recommandation | Ce qu'elle touche |
| --- | --- |
| **Paginer les propos** : plafonner à 3 ou 5 citations par sujet, avec un bouton « Charger la suite » | **Elle existe déjà, par membre** : cinq extraits, puis « Afficher les 5 suivants ». Ce qui n'est pas plafonné, c'est le **nombre de membres** affichés sous un sujet : 20 blocs sur « motion de censure ». La question à poser est donc autre que celle du retour — et la fiche de groupe vient de changer l'agencement des mêmes extraits (nom en tête, date au-dessus de chaque propos), alors que la fiche de gouvernement garde la grille à deux colonnes de gauche |
| **Clarifier « le titre ne le dit pas »**, pour qu'une catégorie par défaut n'écrase pas la répartition par ministère | Le constat de proportion tient (94 % des actes de Borne). **À établir d'abord** : ce que la figure cherche à montrer quand une de ses deux destinations porte presque tout. Renommer la case ne change pas sa largeur. La palette de ce diagramme n'a pas été revue non plus : elle attribue cinq teintes au rang, dont un vert, et n'a jamais été confrontée aux couleurs déjà prises |
| **Garder le tiroir unique**, « nettement plus adapté » que « le système de balises `<details>` cumulatives des fiches groupes » | **La comparaison est périmée.** Depuis le 04/10/2026, la fiche de groupe n'ouvre qu'un rang de personnes à la fois et replie au clic ailleurs. Les trois fiches ne plient toujours pas pareil, mais plus pour la raison que le retour donne. La recommandation elle-même — ne pas revenir à un état « tout déplié » — ne heurte rien |

## Ce que le retour ne dit pas, et que la revue devra regarder

Relevé en remesurant, sans être dans le retour :

- **La fiche de gouvernement n'a rien reçu des deux premiers volets, sauf la
  palette des commissions.** Elle ne porte aucune bulle : ses quatre renvois
  sont encore en pied de section (« Majorité, minorité et opposition, selon
  l'Assemblée → », « D'où viennent ces intitulés → », « Ce que la figure
  compte, et ce qu'elle refuse de compter → », « Pourquoi ces limites se
  déclarent au lieu de se combler → »).
- **« Sur quoi ils ont pris la parole » compte des membres, pas des prises de
  parole**, là où la fiche de groupe compte désormais les deux. Et la règle du
  sujet de la fiche candidat, que la fiche de groupe a reprise le 04/10, n'a
  pas été vérifiée ici.
- **Les ministères de Fillon I s'écrivent en capitales** (« MINISTERE DE LA
  JUSTICE », sans accent), tels que la source les donne, là où ceux de Borne
  sont en minuscules.
- **Une section de parole vide fait 157 px** sur Lecornu I et sur Fillon I ;
  ce qu'elle écrit pour dire son vide n'a pas été relu.
- **Le téléphone** n'a pas été mesuré sur ces fiches.

## Ce qui reste ouvert

Tout. La revue des fiches de gouvernement se fera sur le signal de la
propriétaire, et sa méthode reste à confirmer avec elle : toute la fiche
arbitrée sur maquette avant le code, comme pour le groupe, ou section par
section. Les règles déjà posées par les deux premiers volets ne sont pas à
rediscuter
([`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md),
[`revue-ux-de-la-fiche-de-groupe`](revue-ux-de-la-fiche-de-groupe.md)).
