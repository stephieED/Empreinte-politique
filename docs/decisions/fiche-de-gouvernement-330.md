# La fiche de gouvernement dit d'abord où elle se situe (#330)

`2026-09-18`

> **En bref** — la fiche de gouvernement n'avait jamais été arbitrée : trois blocs hérités d'août 2025, aucun validé. Elle passe à **trois sections** construites en maquette sur données réelles les 17 et 18/09/2026 — « En bref », « Qui le composait », « Ce qu'il a fait déposer » —, et ce qui a été **écarté** compte autant que ce qui reste. « En bref » ne porte **aucune activité** : comme sur les fiches sœurs, il dit ce que l'objet EST — la frise des dix-sept gouvernements publiés depuis 2007, celui de la fiche en teinte, puis quatre faits (Premier ministre et durée sur une ligne, fourchette d'effectif et remaniements, groupe **déclaré** majoritaire, les trois nombres des projets de loi). Trois formes y ont été essayées et retirées : les grandes tuiles de chiffres (« une rangée de chiffres ne dit pas quand »), la frise des dépôts mois par mois (elle avançait ce que la section 03 dit déjà) et la liste des remaniements ligne à ligne (douze lignes pour Philippe II contre « remanié 10 fois »). L'organigramme est **replié**, une carte ouverte à la fois, et ses colonnes sont construites en JS : une grille CSS aligne chaque rangée sur son bloc le plus haut, si bien qu'ouvrir une carte les ouvrait visuellement toutes. Le **rattachement d'un ministre délégué se lit dans le libellé officiel** (« Secrétariat d'État **auprès du** ministre de l'Europe »), jamais deviné — trois pièges payés en maquette : la source écrit des espaces **insécables**, elle écrit parfois « **après** de la ministre » (faute de la source, qui se lit et ne se corrige pas), et le libellé d'un ministère ne commence pas comme celui de son rattachement, d'où un rapprochement qui retire les têtes de phrase **tant qu'il y en a**. La **majorité n'est pas notre lecture** : l'Assemblée déclare la position de chaque groupe et ne déclare plus rien depuis 2024 — cette absence est publiée telle quelle plutôt que comblée par « le plus nombreux », qui serait un jugement. Deux pistes **fermées** : la cohabitation (le président n'est dans aucun corpus, et le mot est contesté sur le seul cas récent) et le groupe d'appartenance du Premier ministre (le champ `groupe` d'un profil est celui d'**aujourd'hui** — Manuel Valls y est « La République en Marche » sous son gouvernement de 2014) ; le nom mène désormais à sa fiche, où le parcours est daté.

## Le point de départ : une fiche que personne n'avait arbitrée

`GovernmentProfile.jsx` datait du 14/08/2025 et n'avait jamais été revue : un
bandeau sombre, des pastilles de comptage par statut, un mur de cartes de textes
— 64 sur Lecornu II, 282 sur Philippe II — puis une grille de vignettes de
membres. La propriétaire l'a dit le 17/09/2026 : « ces fiches sont un résidu
d'un travail d'il y a très longtemps qui n'a jamais été creusé/validé. L'idée
serait de rester dans une lignée cohérente avec ce qui est fait sur les fiches
de candidats et les fiches de groupes. »

Rien de l'existant n'était donc acquis. La référence est ce qui a été arbitré
sur la fiche candidat ([`six-emplacements-fiche-candidat-328`](six-emplacements-fiche-candidat-328.md),
[`les-grands-chiffres-fiche-candidat-328`](les-grands-chiffres-fiche-candidat-328.md))
et sur la fiche de lignée ([`fiche-de-lignee-ui-329`](fiche-de-lignee-ui-329.md)).

## Ce que la fiche pouvait affirmer, mesuré avant de dessiner

Mesuré le 17/09 sur `origin/main 760f1bffe`, puis re-mesuré le 18/09 sur
`7e8f58bab` — **la collecte des membres est passée entre les deux**, et elle a
changé la réponse :

| Bloc | Le 17/09 | Le 18/09 |
| --- | --- | --- |
| Membres | 192 personnes publiées sur 414 appartenances recensées par l'AN | **0 manquant, 0 en trop** sur les 17 fiches |
| Premier ministre | publié sur 5 fiches | publié sur **17** |
| Dates du gouvernement | 4 décalées, dérivées des mandats de nos profils | bornes officielles de l'organe `GOUVERNEMENT` |
| Initiateurs reliés à un membre | 185 des 282 textes de Philippe II | **280 des 282** |

Deux constats de cette mesure ont été transmis à la session Backend et traités
par elle : les **sept gouvernements absents** de `raw_data/gouvernements_reels.json`
(#996) et le statut **`depose` inatteignable** dans `_determine_statut` — sur
les trois archives, 9 278 dossiers portent un acte `-DEPOT` et **aucun** n'a que
des actes `-DEPOT`, si bien que 336 textes s'affichent « Navette en cours » dont
315 n'ont aucun acte daté après leur dépôt. **La fiche affiche le statut tel que
la donnée le publie** : la correction est chez Backend, l'interface ne
réinterprète pas.

## « En bref » : ce que l'objet est, jamais ce qu'il a fait

C'est l'arbitrage structurant, et il a demandé trois tentatives.

Les deux fiches sœurs ont la même intention, qu'il a fallu aller relire à
l'écran plutôt que dans le code : la lignée montre l'effectif de ses maillons
dans le temps, le candidat la frise de sa carrière. Aucune ne met son activité
dans « En bref ». Une frise des **dépôts mois par mois** — essayée, publiée en
maquette, rejetée — faisait exactement l'inverse.

La forme retenue : **la suite des dix-sept gouvernements**, celui de la fiche en
teinte et nommé, les autres en gris avec leurs dates au survol. Un lecteur
arrivé par une recherche situe immédiatement l'époque, et la comparaison des
largeurs dit ce qu'aucun chiffre ne dit — Attal huit mois, Philippe II trois
ans.

Dessous, quatre faits, dans cette forme :

- **Premier ministre** — son nom, lien ordinaire vers sa fiche, suivi de la
  période et de la durée sur la même ligne ;
- **Composition** — « entre 30 et 37 membres · remanié 10 fois ». La fourchette
  compte des **personnes simultanément en fonction**, pas des portefeuilles :
  quelqu'un qui en tient deux le même jour ne compte qu'une fois, faute de quoi
  Fillon I affiche « entre 21 et 22 membres » pour 21 personnes. Elle se lit
  **après la formation** — au premier jour, le Premier ministre est seul nommé ;
- **Majorité à l'Assemblée** — voir plus bas ;
- **Projets de loi** — « 282 déposés · 151 adoptés · 15 promulgués à ce jour »,
  et dessous « dont 1 adopté sans vote (article 49.3), fait de procédure ». Les
  151 adoptés réunissent les quatre statuts d'adoption, promulgation comprise :
  un texte promulgué a d'abord été adopté.

**Le gras ne porte que ce qui se retient.** Tout en gras ne met rien en valeur :
le texte de liaison reste en gris, les noms et les nombres passent en appui, les
nombres en chiffres tabulaires, et une absence s'écrit en italique — jamais en
gras.

## « Un remaniement », et pourquoi ce n'est pas une date

Compter les dates de prise de fonction postérieures à la formation donne des
nombres faux : chez Attal, dix-sept nominations tombent à quinze jours du début
et zéro à trente jours, parce que le gouvernement s'est constitué en deux
vagues. Un seuil arbitraire déciderait donc du chiffre.

Une **vague** regroupe les prises de fonction à moins de huit jours d'écart — un
décret de nomination et son complément. Le seuil est déclaré dans
`JOURS_MEME_VAGUE`, pas caché dans une comparaison. Philippe II compte alors 10
remaniements, Attal 1, Fillon I 1.

## La majorité se lit, elle ne se décide pas

L'Assemblée publie la position de chaque groupe — « Majoritaire », « Opposition »,
« Minoritaire » —, portée par `position_politique.position` sur les fiches de
groupe. La fiche de gouvernement la lit et la nomme ; elle ne désigne jamais le
groupe le plus nombreux, qui serait notre jugement (§2 règle 1).

**Depuis 2024, l'Assemblée ne déclare plus rien** : les dix groupes de la XVIIe
législature portent `non_declaree`. La fiche écrit alors « aucun groupe déclaré
majoritaire », et pour les gouvernements d'avant 2017 « non collectée pour cette
période » — deux absences, deux causes, aucune comblée (§2 règle 5).

Le manifeste porte désormais `position`, `debut` et `fin` pour chaque fiche de
groupe : la fiche de gouvernement n'a pas à télécharger un fichier de groupe, qui
atteint 500 Ko.

## Deux pistes fermées

**La cohabitation.** Le nom du président n'est dans aucun corpus — l'Assemblée
publie les députés et les gouvernements, pas l'Élysée —, il faudrait une table
écrite à la main. Et sur les dix-sept gouvernements, tous postérieurs à 2007, le
seul cas où le mot se poserait (Barnier) est contesté : trancher serait un
jugement.

**Le groupe du Premier ministre.** Le champ `groupe` d'un profil est celui
d'aujourd'hui : Manuel Valls y est « La République en Marche » sous son
gouvernement de 2014, Élisabeth Borne « Ensemble pour la République », un groupe
né en 2024. Le groupe **daté** n'existe que sur 7 des 17 Premiers ministres. S'y
ajoute un fait institutionnel : un Premier ministre n'a pas de groupe pendant
qu'il gouverne. Le nom mène donc à sa fiche, où le parcours est daté.

## L'organigramme : replié, et une carte à la fois

Un bloc par ministère, son titulaire — ou ses titulaires successifs, reliés par
une flèche et la date du changement (« François de Rugy → Élisabeth Borne depuis
07/2019 ») —, et au clic les ministres délégués et secrétaires d'État rattachés.

Trois mesures ont conduit à cette forme, à 1 200 px de large sur Philippe II :
tout déplié, 1 573 px de haut ; replié, **697 px** ; une carte ouverte, 788 px.

**Les colonnes sont construites en JS.** Une grille CSS étire toutes les cartes
d'une rangée à la hauteur de la plus haute : ouvrir une carte les ouvrait
visuellement toutes. Des colonnes indépendantes ne font descendre que ce qui est
sous la carte ouverte. `column-count` a été essayé avant : le navigateur
rééquilibre les colonnes et les cartes sautent de l'une à l'autre au dépliage.

**Le rattachement est lu, jamais déduit** — et trois défauts de la source ont été
payés en maquette :

1. des **espaces insécables** dans les libellés (« Ministère␣auprès␣du Premier
   ministre ») : ni retour à la ligne, ni rattachement lisible ;
2. « Secrétariat d'État **après** de la ministre des solidarités » : la faute est
   dans la donnée. Elle est **lue** — sinon un ministère fantôme apparaît — et
   non corrigée ;
3. le libellé d'un ministère et celui de son rattachement ne commencent pas
   pareil (« Ministère de l'agriculture » contre « du ministre de
   l'agriculture ») : les têtes de phrase se retirent **tant qu'il y en a**,
   sinon le même ministère fait deux blocs.

Une personne qui a changé de charge dans le même ministère n'y figure qu'une
fois, avec la dernière : sans ce dédoublonnage, Castaner apparaît trois fois
dans le bloc du Premier ministre de Philippe II.

Un cas reste visible sans être résolu, et la propriétaire a tranché « on laisse
comme ça » : Élisabeth Borne figure dans le même bloc comme titulaire du
ministère de la transition écologique **et** comme ministre des transports qui
lui était rattachée. C'est ce qui s'est passé ; rien ne le dit.

## « Ce qu'il a fait déposer » : le flux matière → étape

À gauche la **commission saisie au fond**, sourcée, jamais une lecture du titre ;
à droite l'étape où le texte s'est arrêté. L'épaisseur d'un ruban est un nombre
de textes, jamais une part, et **aucun seuil** ne fait disparaître un texte seul.

Le **49.3 ne prend aucune teinte** : un texte adopté sans vote porte un contour
et est nommé à côté de la figure (§2 règle 4). Les **commissions spéciales**,
créées pour un seul texte, sont regroupées dans la figure — une dizaine de
rubans d'un texte y superposaient leurs étiquettes — et la liste nomme chacune.

La liste s'ouvre sur les 30 derniers dépôts et se déplie ; chaque ligne porte sa
date, son étape, sa chambre de dépôt, sa matière et son lien vers la source.

## Alternative écartée : garder les pastilles de comptage par statut

L'ancienne fiche affichait neuf pastilles (« 19 promulgués », « 43 en navette »…)
au-dessus du mur de cartes. Elles disent la même chose que le flux, sans dire
d'où viennent les textes ni à quelle matière ils se rattachent, et elles
plaçaient le 49.3 au milieu des autres statuts, comme une issue parmi d'autres.
Elles partent avec le mur de cartes.

## Une quatrième section : ce qu'on n'a pas pu lire

Ajoutée le 18/09 après relecture : la limite de couverture vivait en
avertissement au-dessus des textes, où elle se lisait comme un défaut de la
figure. Elle rejoint une section dédiée, comme sur la fiche de lignée, avec
**trois causes qui ne se confondent pas** (DESIGN_SYSTEM §7 règle 7) : une
archive que la source ne publie pas, une position que la source ne déclare
plus, une activité qui n'existe pas au niveau d'un gouvernement — un
gouvernement ne vote pas.

**Deux entrées sans portefeuille** apparaissent avec la collecte complète de
#996 : Damien Abad et Yaël Braun-Pivet portent chacun, sous Borne, un second
mandat d'appartenance libellé « Gouvernement » sans sigle, aux dates
chevauchantes. C'est fidèle à la source ; en faire un bloc « Portefeuille non
renseigné » afficherait la personne deux fois. L'entrée muette est donc écartée
**uniquement quand la personne est déjà placée ailleurs** — jamais quand elle
est sa seule trace.

## Une cinquième section : sur quoi ils ont pris la parole (19-20/09)

Ajoutée quand `tags_thematiques_agreges` a été publié sur les fiches (#1020,
corrigé par #1030), au **gabarit de la fiche de groupe** : les débats où le
plus de MEMBRES sont intervenus, un compte de membres et jamais d'occurrences,
le dénominateur `comptages.membres_avec_interventions` publié à côté du
numérateur plutôt que pré-divisé (§2 règle 7), et un renvoi vers
`/methodologie#paroles`. Un intitulé de débat est un **sujet**, jamais une
position (§2 règle 8).

**L'étiquetage n'est pas uniforme, et la fiche le dit.** Mesuré le 19/09 :
les membres de Philippe II portent 48 370 interventions dans leur fenêtre,
dont **329 seulement** avec un `theme_officiel` — d'où 61 sujets, contre
1 738 pour Borne et ses 23 890 interventions étiquetées sur 26 034. Sans une
ligne dans « Ce qu'on n'a pas pu lire », cet écart se lit comme un
gouvernement silencieux, ce qu'il n'est pas.

Neuf fiches n'ont aucun sujet : les interventions collectées commencent le
28/06/2017, et Lecornu I n'a aucune séance dans sa fenêtre d'un mois. Ce sont
des faits, pas des trous, et chacun est déclaré.

### Le détail d'un sujet, au clic (20/09)

Un sujet s'ouvre sur **les membres qui y sont intervenus** — nom, dates, nombre
de tours de parole, type —, chargés d'une projection de build
(`scripts/vue-parole-gouvernement.mjs`), au premier clic et jamais avec la
fiche : 1,2 Mo pour les dix-sept gouvernements, quand la fiche de Borne en pèse
1. Même geste que les débats d'une lignée (#979).

**Le verbatim n'existe pas pour ces personnes.** Mesuré le 20/09 : `texte`
n'est porté que par les profils de candidats déclarés ; les 205 profils de
membres de gouvernement sont collectés en mode réduit au thème. La fiche dit
donc qui a parlé et quand, jamais ce qui a été dit.

**Une ligne par membre, pas par tour de parole.** La première version rendait
857 lignes pour la motion de censure de décembre 2023, dont trente-quatre fois
« 21 décembre 2023 · Élisabeth Borne » : une intervention de la source est un
tour de parole. L'ordre a été arbitré deux fois le 20/09 : alphabétique d'abord — « classer par
volume fabriquerait un indice d'activité » —, puis **par date de dernière prise
de parole décroissante, et à date égale par nombre de tours décroissant**, à la
demande de la propriétaire. Ce qui reste interdit ne change pas : aucun total,
aucun rang affiché, et aucun rapport de ce nombre à un possible, qui en ferait
un taux (§2 règle 3).

**Deux défauts payés en écrivant la projection**, tous deux invisibles sans
mesure : la clé d'un sujet est `theme.strip().lower()` dans
`deriver_tags_thematiques`, si bien que keyer sur le libellé brut donnait
**zéro correspondance** sur les 1 738 sujets de Borne ; et le `source_url`
d'une intervention pointe l'archive Syceron — 100 Mo de zip —, pas le
paragraphe, si bien qu'un badge « Source » y menant n'atteste rien. Le lien
n'apparaît donc que lorsqu'il mène à un document lisible.

### En qualité de quoi ils ont parlé (20/09)

Chaque ligne du détail porte le **portefeuille exercé à la date** de ses prises
de parole. La source ne le dit pas sur l'intervention — `fonction` est vide sur
les 4 213 entrées d'Élisabeth Borne — mais l'Assemblée publie les fenêtres
d'exercice : la qualité se **lit** dans la fenêtre qui contient la date, elle ne
se devine pas.

Conséquence voulue : **onze membres du gouvernement Borne portent deux lignes**,
une par portefeuille. Gabriel Attal y parle « chargé des comptes publics » en
décembre 2022, puis « ministre de l'éducation nationale et de la jeunesse » en
novembre 2023 — deux qualités, deux périodes, un seul nom.

La ligne passe en **quatre colonnes** — qui · en qualité de quoi · quand ·
combien : en flex, un intitulé long rejetait le compte à la ligne suivante.

## Ce que ce lot ne fait pas

- **Il ne touche pas au pipeline** : ni au statut `depose`, ni aux populations de
  profils. Le seul champ ajouté l'est au **manifeste de l'interface**.
- Il ne publie pas de section « Ce qu'on n'a pas pu lire » sur la fiche de
  gouvernement : les absences sont dites à l'endroit où elles se constatent —
  la majorité non collectée, les archives qui commencent au 21 juin 2017.
- Il n'ajoute pas de sommaire ni de barre de recherche : les deux existent sur
  les fiches sœurs et n'ont pas été arbitrées ici.
