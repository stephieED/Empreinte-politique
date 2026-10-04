<a id="reponse-au-retour-ux-fiche-gouvernement"></a>

# La réponse au retour d'ergonomie sur la fiche de gouvernement : ce qui a été décidé, constat par constat (2026-10-04)

`2026-10-04`

> **En bref** — Le retour d'ergonomie du 04/10/2026
> ([`retour-ux-sur-les-fiches-gouvernement`](retour-ux-sur-les-fiches-gouvernement.md))
> portait sept constats et trois recommandations. La propriétaire a arbitré
> toute la fiche sur maquette, donné son accord avant le code, puis relu la
> page servie et dicté sept corrections. **Trois constats ont une réponse
> livrée, deux étaient des constats favorables et ce qu'ils saluaient est
> gardé, deux ont reçu une autre réponse que celle du retour.** Des trois
> recommandations, **une est suivie telle quelle** (le tiroir unique), **une
> demandait ce que la fiche faisait déjà**, la troisième a été traitée en
> changeant la figure plutôt que le libellé. Repliée, la fiche Borne passe de
> **4 467 à 3 788 px** ; un sujet de parole ouvert n'ajoute plus 5 880 px mais
> quelques centaines. Trois lectures fausses du retour ont compté autant que
> ses constats justes : **un nombre lu pour ce qu'il n'est pas est un défaut
> de la figure, pas du lecteur.**

## Pourquoi ce fichier existe

Le fichier du retour dit ce que le retour demandait et ce que la mesure en
confirmait. Il se terminait par « Tout reste ouvert ».
[`revue-ux-de-la-fiche-de-gouvernement`](revue-ux-de-la-fiche-de-gouvernement.md)
dit ce qui a été retenu **section par section**, avec les formes écartées.
Celui-ci fait le chemin inverse : il reprend le retour **constat par constat**
et dit ce que chacun est devenu, comme
[`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md)
et [`reponse-au-retour-ux-fiche-groupe`](reponse-au-retour-ux-fiche-groupe.md)
l'ont fait pour les deux premiers volets. Il ne redit pas les formes : il y
renvoie.

## La réponse, constat par constat

| # | Constat du retour | Réponse | État |
| --- | --- | --- | --- |
| 1 | La fiche Borne gagne 6 055 px quand on ouvre le pôle le plus chargé et le sujet « motion de censure » : « l'injection de 21 interventions complètes » | La hauteur venait du **nombre de membres** dépliés d'un coup, pas de la longueur des propos. Un sujet ouvert montre désormais **un membre à la fois**, désigné au clic sur sa part de la barre | Fait |
| 2 | Les fiches courtes ou anciennes ne bougent pas : +77 px sur Lecornu I, 0 px sur Fillon I | Constat favorable. Rien à corriger ; la phrase qu'écrit une section de parole vide a été réécrite, et « Ce qu'on n'a pas pu lire » en donne la raison | Gardé |
| 3 | Les tiroirs exclusifs obligent à des allers-retours pour comparer plusieurs pôles ou plusieurs sujets | **Le tiroir unique reste**, et le retour le recommandait lui-même. Ce qui s'ouvre au clic se replie désormais au clic ailleurs, comme sur les deux autres fiches | Répondu autrement |
| 4 | Le diagramme de « Ce qu'il a fait déposer » est dense | Le fait cité était faux — la figure croisait des commissions et des étapes, pas des ministères. Elle est remplacée par **un carré par projet de loi, cinq colonnes** : la fiche de gouvernement était la dernière à garder un diagramme de flux | Fait |
| 5 | La distinction entre actes de personne et actes qui touchent au droit est une bonne mise en contexte | Constat favorable. Les trois cartes restent ; la deuxième se lit « actes relevant du fonctionnement interne de l'État », et **le gris passe sur ce qui est écarté** | Gardé |
| 6 | « Le titre ne le dit pas » (16 006 actes) occupe une place prépondérante | La proportion était réelle : 94 % des actes de Borne dans une seule case. **Une barre par ministère** ; la part sombre est celle des actes dont le titre cite une loi, le reste de la barre est « le titre ne le dit pas ». La proportion se lit ministère par ministère, elle ne tient plus la moitié de la figure | Fait |
| 7 | « Ce qu'on n'a pas pu lire » alourdit le bas de fiche de notes récurrentes | **La section reste, et gagne une ligne** sur les prises de parole. Une absence se déclare (`AGENTS.md` §2 règle 5) : la retirer pour gagner 239 px ferait d'un manque un silence. Sa bulle dit en une phrase comment la lire | Répondu autrement |

### Ce que la mesure dit, avant et après

Mesuré le 04/10/2026 au soir sur la page servie depuis la branche de la PR
#1209, à 1 440 px de large, après les corrections de la relecture. Les valeurs
« avant » sont celles du fichier du retour, mesurées le même jour sur `main`.

| Fiche | Repliée, avant | Repliée, après |
| --- | ---: | ---: |
| Borne (`BORNE`) | 4 467 px | 3 788 px |
| Fillon I (`FILLON_1`) | 3 616 px | 3 127 px |

Lecornu I, la troisième fiche du retour, n'a pas été remesurée.

| Section, fiche Borne repliée | Avant | Après |
| --- | ---: | ---: |
| En bref | 393 px | 368 px |
| 1 · Qui le composait | 734 px | 758 px |
| 2 · Sur quoi ils ont pris la parole | 587 px | 489 px |
| 3 · Ce qu'il a fait déposer | 651 px | 406 px |
| 4 · Ce qu'il a fait entrer en vigueur | 1 037 px | 727 px |
| 5 · Ce qu'on n'a pas pu lire | 264 px | 239 px |
| **Fiche entière** | **4 467 px** | **3 788 px** |

« Qui le composait » est la seule section qui grandit, de 24 px : la cause n'a
pas été cherchée.

**Le sujet ouvert.** Avant, « motion de censure » ouvert ajoutait 5 880 px à
la fiche Borne. Après, la liste est rangée par prises de parole et son premier
sujet ouvrable est « programmation militaire 2024-2030 » : ouvert, il fait
716 px, et la fiche 4 473 px. La comparaison n'est donc pas terme à terme ;
sur « motion de censure », la session précédente avait relevé 638 px, valeur
non remesurée ici.

## Les trois recommandations, et ce qu'elles sont devenues

| Recommandation du retour | Ce qui a été fait |
| --- | --- |
| Paginer les propos : 3 ou 5 citations par sujet, avec « Charger la suite » | **Elle existait déjà, par membre** — cinq extraits, puis « Afficher les 5 suivants ». Ce qui n'était pas borné, c'était le nombre de membres affichés. La réponse est ailleurs : un membre à la fois |
| Clarifier « le titre ne le dit pas » | **La figure a changé, pas le libellé.** Renommer la case ne changeait pas sa largeur. La limite reste écrite — « Le titre ne le dit pas » ne veut pas dire « sans loi » —, à la suite de l'étiquette de légende qu'elle précise |
| Garder le tiroir unique | **Suivie.** La comparaison qui la justifiait était périmée — la fiche de groupe n'empile plus ses plis —, mais la recommandation ne heurtait rien |

## Trois lectures fausses, et ce qu'elles ont changé

Le retour se trompait trois fois sur ce qu'il voyait. Aucune de ces erreurs
n'a été écartée comme une erreur du relecteur : chacune disait quelque chose
de la figure.

| Ce que le retour a lu | Ce que c'était | Ce que la fiche fait maintenant |
| --- | --- | --- |
| « 21 interventions complètes » | « 21 / 50 » : 21 membres intervenus, sur 50 | Deux colonnes **nommées** : « prises de parole », « membres » |
| Un diagramme « croisant les ministères et les statuts » | Des commissions et des étapes | Des carrés rangés par étape ; la commission est une couleur, nommée dans la légende et dans l'infobulle |
| Un « filtre » qui « écrase la répartition par ministère » | Une des deux destinations du flux | Plus de flux : une barre par ministère, deux parts |

C'est la deuxième fois qu'un relecteur prend un compte pour autre chose — le
« 51 textes communs » de la fiche de groupe avait été lu « 51 % ». La règle 8
du `DESIGN_SYSTEM` §6 bis s'applique aux trois fiches.

## Ce que la relecture de la page a corrigé

La maquette avait arbitré les formes. Relisant la page servie, la propriétaire
a dicté sept corrections, dont trois sur des gestes qu'aucune maquette ne
montre.

| Section | Correction |
| --- | --- |
| Sur quoi ils ont pris la parole | Le membre se nomme **au clic**, plus au survol |
| Ce qu'il a fait déposer | Le texte survolé se nomme dans **l'infobulle des carrés** des deux autres fiches ; la ligne écrite sous la grille décalait tout ce qui la suit |
| Ce qu'il a fait entrer en vigueur | **Le nom ouvre tout le ministère, chaque part de la barre la sienne** |
| — légende | La limite suit son étiquette, sur la même ligne |
| — cartes de tête | « actes parus au Journal officiel » ; « actes relevant du fonctionnement interne de l'État » ; le gris sur ce qui est écarté ; la ligne « dont N d'après leur titre » retirée, la règle restant en méthodologie |
| En bref, fiches de gouvernement et de groupe | La note dit, quand aucun groupe n'est déclaré majoritaire, que l'Assemblée ne le dit qu'une fois la législature achevée |

## Les six bulles

Écrites ou recomposées par la propriétaire, rendues dans leur bulle avant
d'être retenues, et recopiées dans
`tests/test_revue_ergonomie_fiche_gouvernement.py`. Elles sont dans
[`revue-ux-de-la-fiche-de-gouvernement`](revue-ux-de-la-fiche-de-gouvernement.md).
Elles remplacent les quatre renvois en pied de section que le fichier du
retour relevait.

## La page de méthodologie a suivi

Elle écrivait : « Aucune section de méthode ne décrit encore cette fiche. »
Quatre sections ont été écrites avec la revue, une par bulle qui y mène, puis
réécrites le 04/10/2026 pour un lecteur qui n'a pas travaillé sur le projet,
comme l'avaient été celles des fiches candidat et de groupe.

| Ce qui est parti | Ce qui le remplace |
| --- | --- |
| « un segment par membre » | « la barre d'un débat est découpée en autant de parts qu'il y a de membres intervenus » |
| « jamais par déduction » | « et seulement d'après ce titre » |
| « rien ne rapporte ces nombres à un possible : ce serait un taux de présence » | « ne compare ces nombres à aucun nombre de séances : ce serait mesurer la présence de chacun » |
| « un décret et son complément tombent souvent à deux ou trois jours d'écart » | « un gouvernement est souvent complété deux ou trois jours après sa nomination » |
| « en navette entre les deux chambres », « projet de loi », sans explication | Les deux mots restent, chacun avec ce qu'il désigne |
| « Les actes qui concernent une personne » | Les mots de la fiche : « actes relevant du fonctionnement interne de l'État » |

Trois choses y sont entrées, qui n'y étaient pas : pourquoi « En bref » peut
écrire « aucun groupe déclaré majoritaire » ; ce qu'ouvre un clic sur le nom
d'un ministère ou sur une part de sa barre ; et le clic, non le survol, pour
lire la parole d'un membre.

## Ce qui a été décidé contre l'avis de l'agent, et ce qu'il a mal compris

Consigné parce que la suite repartira des mêmes réflexes.

| Sujet | Ce qui était proposé ou compris | Ce qui a été tranché |
| --- | --- | --- |
| Sujet de parole ouvert | Une ligne par membre, un seul ouvert | La barre découpée de la fiche de groupe : **même logique, même forme** |
| Mention du Journal officiel interrompu | Une disparition automatique au retour de la source | Posée et retirée **à la main** |
| La même mention | Codée dès le texte validé sur maquette | **Un choix validé n'est pas un feu vert** : rien ne se code sans accord explicite |
| Rôles de parole | « Rapporteur » et « membre du gouvernement » attribués à `role_seance` | Ils viennent de `fonction`, texte libre du compte rendu ; `role_seance` ne connaît que la présidence |
| Philippe I | « Ce gouvernement a siégé de 2017 à 2020 », pour expliquer 0 prise de parole | `PHILIPPE` est Philippe I, un mois sans séance ; le zéro est attendu |

## Ce qui reste ouvert

| Sujet | Où il en est |
| --- | --- |
| « Depuis 2024, l'Assemblée nationale ne déclare plus la position de ses groupes » | Phrase de « Ce qu'on n'a pas pu lire » qui contredit la nouvelle note d'« En bref » ; question posée, sans réponse |
| Quatorze des dix-sept fiches de gouvernement | Jamais regardées à l'écran : seules Borne, Lecornu II et Fillon I l'ont été (#1205) |
| « Motion de censure » : 21 membres annoncés avant, 19 comptés par la figure | Écart non expliqué entre l'agrégat et le détail servi |
| La couleur par ministère | Rouvrir si les projets de loi portent un jour le ministre qui les présente (#1204) |
| La parole de ministre reconnue dans un texte libre | #1206 |
| La palette des thèmes européens | #1207 |
| La ligne « Intitulé non publié » | Redeviendra ouvrable quand elle sera petite (#1178) |
| Le téléphone | Écarté de ce volet par la propriétaire ; #867 |
| La mention temporaire | À retirer à la main au retour du Journal officiel (#1199) |
| Sous un mot recherché ou une période | La section de parole garde sa liste d'avant |

## Ce qui a servi, et ce que cela a coûté

La méthode du volet groupe a tenu : toute la fiche arbitrée sur maquette, le
code en une fois, puis la relecture de la page servie. Ce volet y ajoute un
cran : **l'accord pour coder est un mot de la propriétaire, pas une
conséquence de la maquette.**

Quatre pièges payés :

- **Un geste ne se juge pas sur maquette.** Survol ou clic, ligne qui s'insère
  ou infobulle : les trois corrections de geste ont été vues sur la page, pas
  avant.
- **Un paragraphe retiré emporte ses limites.** En ôtant la notice sous les
  actes, deux mentions obligatoires sont parties avec ; ce sont les tests
  existants qui les ont rattrapées.
- **Une cause devinée ne se transmet pas comme un fait.** Le zéro de Philippe I
  avait reçu une explication fausse ; l'écart 19 / 21 reste écrit « non
  expliqué ».
- **Une question sur un rendu se pose capture en main.** Un « texte marron » a
  été discuté dans une section où il n'était pas.
