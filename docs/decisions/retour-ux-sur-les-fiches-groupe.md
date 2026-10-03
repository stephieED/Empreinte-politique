<a id="retour-ux-sur-les-fiches-groupe"></a>

# Le retour d'ergonomie sur les fiches de groupe : ce qu'il dit, ce que la mesure en confirme, et ce qu'il a mal lu (2026-10-02)

`2026-10-02`

> **En bref** — Second retour extérieur, après celui des fiches candidat
> ([`retour-ux-sur-les-fiches-candidat`](retour-ux-sur-les-fiches-candidat.md)).
> Il porte sur trois fiches de groupe — Ensemble pour la République, Écologie
> Démocratie Solidarité, LIOT — et pose sept constats et trois
> recommandations. **Ses mesures de hauteur se reproduisent au pixel près** :
> la fiche d'Ensemble pour la République passe de 6 572 à 15 007 px quand on
> ouvre ses deux plis, dont 7 583 px pour la seule liste de ses 448 personnes.
> **Un de ses constats repose sur une lecture fausse, et c'est un constat en
> soi** : les « pourcentages de proximité (51 %, 50 %) » d'« Avec qui ils
> votent » sont des nombres de textes communs, pas des taux — la figure
> n'affiche aucun pourcentage. Ce fichier consigne le retour et ce que la
> mesure en dit. **Rien n'est arbitré** : la revue des fiches de groupe n'a pas
> commencé.

## Pourquoi ce fichier existe

Le retour est la matière de départ du volet « groupe » de la revue
d'ergonomie, comme l'autre l'a été du volet « candidat ». Sans trace, ses
points se représenteront comme des idées neuves ; et transmis sans leur
vérification, ils se liront comme une liste de corrections à appliquer. Or deux
d'entre eux touchent des règles déjà posées, et un troisième est une erreur de
lecture qui dit quelque chose de la figure.

## D'où viennent les mesures

Le retour dit avoir été « mesuré le 30 septembre 2026 sur les 41 pages
publiées ». **Le nombre de 41 n'a pas été retrouvé** : le site publie 12 fiches
de lignée, et rien de ce qui a été cherché ne compte 41 pages. Les trois
fiches citées, elles, ont été remesurées le 02/10/2026 sur
l'application construite, à 1 440 px de large :

| Fiche | Repliée | Les deux plis ouverts | Gain | Dont la liste des personnes |
| --- | ---: | ---: | ---: | ---: |
| Ensemble pour la République (`AN-REN`) | 6 572 px | 15 007 px | +8 435 px | 7 583 px, pour 448 personnes |
| Écologie Démocratie Solidarité (`AN-EDS`) | 5 545 px | 6 826 px | +1 281 px | 411 px, pour 17 personnes |
| LIOT (`AN-LIOT`) | 6 352 px | 7 819 px | +1 467 px | 631 px, pour 35 personnes |

Les trois gains sont ceux du retour, à l'unité. Le second pli, « Lectures
antérieures, amendements, articles et motions », ajoute de 836 à 870 px sur
les trois fiches : ce n'est pas lui qui fait la différence.

## Ce que le retour dit

| # | Constat | Vérifié ? |
| --- | --- | --- |
| 1 | L'« explosion verticale » : 448 noms dépliés sur plus de huit pages A4 | **Oui**, voir le tableau. La liste des personnes fait à elle seule 7 583 px — plus que la fiche entière repliée |
| 2 | Aucune recherche, aucun tri, aucune pagination dans la liste dépliée | **Oui pour la liste des personnes.** Le site porte bien une recherche par mot (#979), dans le tiroir de l'en-tête, et la fiche de groupe y répond ; mais elle filtre des intitulés — débats, textes, amendements —, pas des noms. Lu dans le code (`Recherche.jsx`, `LigneeProfile.jsx`), non rejoué à l'écran |
| 3 | La hauteur varie à l'extrême selon l'effectif : l'interface « s'adapte mal aux grands effectifs » | **Oui pour la mesure** : le pli des personnes va de 411 à 7 583 px. Le jugement n'est pas mesurable |
| 4 | Le diagramme en rubans de « Ce qu'ils ont proposé » reste difficile à lire à 1 440 px | **Non mesuré.** La section fait 1 559 à 1 622 px. C'est le même reproche que sur la fiche candidat, où les rubans ont été remplacés par des carrés |
| 5 | « Avec qui ils votent » : des barres qui « affichent des pourcentages de proximité (51 %, 50 %) » suggèrent une alliance, malgré la mention « Voter dans le même sens n'est pas s'entendre » | **Le fait cité est faux, le risque est réel.** Voir plus bas |
| 6 | Une accumulation de réserves : « Pourquoi aucun indice de cohésion », « Ce qu'on n'a pas pu lire », « Comment les groupes d'une lignée sont reliés » | **Oui pour leur présence**, non compté à l'écran. Quatre renvois relevés sur chaque fiche ; le troisième s'écrit en réalité « Comment les groupes successifs sont reliés » |
| 7 | Sur Écologie Démocratie Solidarité, la section « Sur quoi ils ont pris la parole » affiche un bloc vide | **Oui** : 297 px pour « Aucun résultat » et « Les membres du groupe sans profil publié manquent à la collecte : ils n'ont pas été écartés. » |

### Le constat 5 : une lecture fausse, qui est elle-même un constat

Sur la fiche d'Ensemble pour la République, la figure aligne dix groupes. À
droite de chaque ligne, un nombre en gros : **51**, **50**, **50**… suivi de
« textes communs ». Ce sont des **dénominateurs** — le nombre de textes sur
lesquels les deux groupes ont chacun une position —, pas des taux. La figure
n'affiche aucun pourcentage ; sous chaque barre, elle écrit des comptes
(« même sens 9 · nuance 6 · sens opposé 36 » face à La France insoumise).

Le relecteur a donc lu « 51 textes communs » comme « 51 % de proximité », et
« 50 » de même. Avec La France insoumise, la barre dit pourtant l'inverse d'une
proximité : 9 textes dans le même sens sur 51.

Ce que cela établit, et ce que cela n'établit pas :

- **Le nombre le plus visible de la ligne n'est pas celui qui répond à la
  question du titre.** Un lecteur attentif, qui écrivait un retour, y a lu un
  taux. La règle 8 du `DESIGN_SYSTEM` §6 bis s'applique : ce qui empêche une
  lecture fausse se voit dans la figure, et la mention posée sous elle ne l'a
  pas empêchée.
- **Le risque que le retour nomme — une « alliance » lue au premier coup
  d'œil — n'est pas démontré par son exemple**, puisque l'exemple est une
  erreur. Il reste plausible, et la page de méthodologie le connaît : trier
  sur l'accord seul, écrit-elle, « ferait un classement des alliés ».

## Les trois recommandations, et ce qu'elles touchent

Aucune n'est tranchée. Chacune est notée avec ce qu'il faudra vérifier avant
de la suivre.

| Recommandation | Ce qu'elle touche |
| --- | --- |
| **Paginer la liste des personnes** : 20 à 30 « membres clefs (présidents, porte-paroles, démissionnaires) », avec une recherche textuelle | La recherche et la limite d'affichage ne heurtent aucune règle. **Choisir des « membres clefs » en est une autre** : c'est la fiche qui déciderait qui compte dans un groupe, et mettre en avant les « démissionnaires » nomme des personnes par un comportement. À confronter à `AGENTS.md` §2 règle 1 avant toute maquette. Ce que les données portent comme fonctions dans un groupe n'a pas été vérifié |
| **Une hauteur maximale sur les plis**, avec défilement interne | Rien ne s'y oppose. À regarder sur téléphone, où un défilement dans un défilement se manie mal. La fiche candidat a pris une autre voie le 02/10/2026 : ce qui s'ouvre au clic se replie au clic ailleurs |
| **Dire d'emblée, dans « Avec qui ils votent », la part des votes consensuels** qui « gonflent artificiellement » la proximité entre majorité et oppositions | **Deux choses à établir d'abord.** Que cette part existe et se mesure : ce qui, dans les données, permettrait de dire un vote « consensuel » n'a pas été cherché. Et que la figure affiche bien une proximité : elle affiche des comptes, voir le constat 5. « Gonfler artificiellement » est par ailleurs un jugement sur les votes, que la fiche ne porte pas |

## Ce que le retour ne dit pas, et que la revue devra regarder

Relevé en remesurant, sans être dans le retour :

- **La fiche de groupe n'a rien reçu de la revue des fiches candidat.** Elle
  garde les rubans, la couleur au rang, la ligne « Période N sur N · … les
  flèches du clavier naviguent aussi », les renvois en pied de section, et ne
  replie pas au clic ailleurs. Ces points sont arbitrés côté candidat
  ([`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md),
  [`versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat`](versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat.md)) ;
  ils ne le sont pas ici, et la propriétaire a dit que leur tour viendrait avec
  cette revue.
- **La palette des commissions** doit être reprise entière, une seule fois pour
  les trois types de fiche : celle de la fiche candidat entre en collision avec
  trois couleurs réservées, et la fiche de groupe garde la couleur au rang.
- **Le renvoi de « Ce qu'on n'a pas pu lire »** s'écrit encore « Ce que le
  dépôt porte, et depuis quand » : « dépôt » est un mot que la propriétaire a
  refusé sur la fiche candidat.

## Ce qui reste ouvert

Tout. La revue des fiches de groupe se fera comme celle des fiches candidat :
constat par constat, sur maquette, et rien ne s'implémente sans l'accord de la
propriétaire. Les fiches de gouvernement suivront.
