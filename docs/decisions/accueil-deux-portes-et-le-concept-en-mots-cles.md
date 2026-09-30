<a id="accueil-deux-portes-et-le-concept-en-mots-cles"></a>

# L'accueil : le concept en mots-clés, et l'entrée par deux portes permanentes (2026-09-30)

`2026-09-30`

> **En bref** — L'accueil arrêté le 16/09 (forme C, #951) ouvrait sur le Hero puis
> la grille des 31 candidats déclarés. Le 30/09, deux choses le rendent caduc : le
> [recadrage éditorial](coeur-permanent-groupes-et-gouvernements.md) — les groupes et
> les gouvernements deviennent le cœur permanent — et une refonte du bloc « Le
> concept », dont les trois cases passent en **mots-clés** au lieu d'un exemple
> fictif. Arbitré case par case sur maquette, sur les listes réelles.
> **Ce fichier ne remplace pas [`accueil-forme-c-et-tete-methodologie-951`](accueil-forme-c-et-tete-methodologie-951.md)**
> : il en reprend ce qui tient et dit ce qui change.

## Le bloc « Le concept » : trois cases, trois listes

| Case | Étiquette | Contenu |
| --- | --- | --- |
| 1 | Sources officielles | Assemblée nationale · Sénat · Parlement européen … |
| 2 | Collecte et agrégation | Automatisé · Traçable · Reproductible · Open source |
| 3 | Les parcours | Mandats · Votes · Amendements · Prises de parole |

**Trois listes de même forme, et c'est la forme qui fait la démonstration** :
d'où ça vient, ce qu'on en fait, ce que ça contient. La case 1 portait un exemple
de JSON (`{ vote: "pour", texte: "PJL exemple" }`), la case 2 une pastille jaune
« Source vérifiable », la case 3 un avatar gris et « Prénom Nom (exemple) » : trois
registres différents pour une même rangée.

**Pourquoi « agrégation » et pas « traitement ».** « Traitement » ne dit pas sur
quoi il porte, et se lit comme une retouche du fond. La contrainte posée par la
propriétaire est explicite : aucun mot à connotation de transformation.
« Mise en forme » a été proposé et écarté au profit d'« agrégation », bien qu'il
soit le mot de la baseline elle-même (`Baseline.jsx` : « *"automatisé" porte sur
la COLLECTE et la mise en forme — aucun fait n'est écrit ni altéré à la main* »).

**Pourquoi « Les parcours » et pas « Profil ».** Le site écrit « fiche » 39 fois
contre 2 « profil ». Et « parcours » est le mot du titre, six lignes plus haut —
la page se répond à elle-même. L'article se justifie : *parcours* est invariable,
sans « les » on ne sait pas s'il y en a un ou trente.

**La pastille jaune est retirée de la case 2**, et avec elle la dépendance à
`SOURCE_BADGE_VERIFIED`. Ce libellé est partagé par toutes les fiches et vient de
#328 — « *"Vérifié" disait que nous contrôlons la donnée ; nous ne la contrôlons
pas, nous la publions avec le lien vers la source* ». Le Hero ne parlant plus d'un
fait particulier mais du procédé, il cesse d'en dépendre.

**Les cases 1 et 2 sont des liens** — `/sources` et `/methodologie#comment-ca-marche`.
La destination s'annonce au survol **et au `:focus-visible`**, par un élément de la
page et non un `title` natif : l'infobulle native est lente, ne se style pas et
n'existe pas au clavier. La mention est posée en **absolu** — dans le flux, elle
pousserait le contenu et ferait sauter la rangée au survol.

**Le battement des cases est retiré.** Il est passé aux portes, où il désigne un
geste à faire ; sur les cases il n'appelait aucune action, et deux animations sur
un écran se disputent l'attention.

## L'entrée : deux portes permanentes, les candidats dans un encart daté

Forme **B**, retenue le 30/09 entre trois. Les groupes parlementaires et les
gouvernements occupent la rangée ; les candidats passent sous un filet, avec leur
borne écrite — « Jusqu'à l'élection d'avril 2027 ».

**C'est la seule des trois qui dise *ponctuel* sans dire *secondaire*.** L'ordre
inversé seul était trop discret pour se lire comme un recadrage ; les candidats
réduits à une ligne de renvoi dégradaient plus que ce que le recadrage demande.

**Une porte est un OBJET, pas un filtre.** Les onglets ont été écartés pour cette
raison : ils font lire trois familles comme trois vues d'une même liste, alors
qu'un gouvernement et un candidat ne sont pas deux façons de regarder la même
chose. Chaque porte annonce son volume.

**Les listes sont masquées à l'arrivée et n'apparaissent qu'au clic**, un second
clic refermant la porte ouverte — sans quoi on ne revient pas à l'état d'arrivée
sans recharger. Le coût est assumé et il est réel : le premier écran ne montre
plus aucun nom. Les volumes annoncés sur chaque porte le compensent en partie, et
c'est ce qui rend cette forme viable là où des onglets ne l'auraient pas été.

**Une surbrillance tourne entre les portes tant que rien n'est choisi** : chaque
porte reste allumée 2 s sur 6, avec les décalages du Hero. Le réglage du Hero —
un éclat d'un quart de seconde — ne se voyait pas sur trois boutons à désigner.
L'éclat montre **l'état ouvert** (filet d'encre, trait jaune sous la carte) :
le jaune signal est illisible en bordure sur fond clair (1,05:1), il ne porte que
sur le noir du Hero. Le cycle **s'arrête au premier clic** — il ne doit pas
concurrencer la sélection du lecteur — et se tait sous `prefers-reduced-motion`.

## Le titre de l'entrée, et l'amorce

« **Commencer à explorer** », à 25 px et non plus à 16 : c'était un titre de
section comme les autres, alors que c'est l'entrée du site.

Une amorce le suit : « *Un groupe, un gouvernement ou une personne : chaque fiche
rassemble ce que les institutions publient — mandats, votes, textes, prises de
parole. **Chaque fait porte le lien vers sa source.*** »

**C'est le seul endroit de l'accueil où un texte explicatif est à sa place** : il
n'accompagne pas une figure (règle de forme 2), il dit ce qu'est le site à qui ne
le connaît pas. Son ordre — groupe, gouvernement, personne — dit le recadrage. Elle
dit ce qu'on **trouve**, pas ce qu'on doit **faire** : les trois portes juste
dessous disent déjà où cliquer.

## Ce qui disparaît

- **Le titre « Les candidats déclarés »** : une porte ne vit pas sous le titre
  d'une seule des trois familles.
- **La ligne « Aussi : les groupes parlementaires · les gouvernements »**, que les
  portes remplacent.
- **L'onglet « Explorateur »** de la barre de navigation. Il menait à `/candidats`,
  donc il portait l'ancienne hiérarchie.
- **« pour la présidentielle 2027 »** du titre, qui tenait sur deux lignes et n'en
  tient plus qu'une.

## Trois pièges mesurés, pour l'implémentation

**Les pastilles de groupe et de gouvernement sont des `<button>` dans le site** —
ce sont des filtres (`GroupsBar.jsx`, `GovernmentsBar.jsx`). Sur l'accueil ce sont
des **liens**, et un lien hérite du soulignement global d'`index.css`. Sans une
règle `text-decoration: none` sur les trois classes de pastille, les listes
repartent avec deux rendus pour une même forme.

**« Les principes » n'est pas une ancre.** Dans `MethodologyPage.jsx` c'est une
**famille** de sections (`{ famille: 'Les principes' }`) ; seules les sections
portent un `id`. La première de la famille est `comment-ca-marche`, et c'est la
cible du lien. Une ancre inexistante dépose le lecteur en haut de la page sans
que rien ne le lui dise.

**`NavigationSite` est un composant unique**, partagé par toutes les pages.
Retirer « Explorateur » *seulement sur l'accueil* n'est pas une ligne supprimée
mais une règle conditionnelle à la route. Le retirer partout est plus cohérent
avec le recadrage, mais supprime un raccourci depuis les pages de contenu :
**non tranché**.

## La forme B est retenue, son exécution ne l'est pas

**Mise à jour du 30/09/2026, en fin de session.** Le principe — deux portes
permanentes, les candidats sous leur borne — est arbitré et ne se rediscute pas.
**Le rendu, lui, n'a pas convaincu la propriétaire** et sera repris.

C'est écrit ici parce qu'une décision qui dit « retenue » sans dire « à
retravailler » ferait lire la maquette du 30/09 comme un acquis. Le bloc « Le
concept » et les textes, eux, sont arrêtés.

## Ce qui reste ouvert

- **« Par gouvernement » est au singulier** quand les deux autres portes sont au
  pluriel.
- **« groupes parlementaires » mène aux 12 LIGNÉES**, pas aux 29 groupes. C'est le
  mot du site, mais il ne désigne pas la même chose.
- **Le mot « parcours »** du titre, question de fond ouverte par le recadrage.
- **La troisième case du concept n'est pas cliquable** quand les deux autres le
  sont : l'écart se voit au survol.
