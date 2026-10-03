<a id="versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat"></a>

# Revue d'ergonomie de la fiche candidat, suite : le versant européen, et les écarts que l'implémentation avait laissés (2026-10-02)

`2026-10-02`

> **En bref** — La revue du 01/10/2026
> ([`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md))
> laissait deux choses ouvertes : le **versant européen**, dont les bulles
> écrites pour l'Assemblée étaient fausses, et **neuf écarts** que les
> sous-agents avaient pris seuls en codant. La propriétaire les a repris un par
> un le 02/10, sur maquette. **Quatre textes de bulle européens** sont arrêtés.
> Sur une fiche à deux versants, **la bulle quitte le titre et entre dans chaque
> pastille du commutateur**. Les textes portés européens passent des rubans à
> **des carrés, une ligne par thème**. **Une section vide porte sa bulle.** La
> section « Ce qu'on n'a pas pu lire » gagne **une ligne pour les mandats au
> Sénat** ; celle du Parlement européen attend des données justes (#1163). La
> palette des commissions est livrée telle quelle et sera reprise entière avec
> les fiches de groupe et de gouvernement. Deux demandes de la même séance
> s'y ajoutent : **ce qui s'ouvre au clic se replie au clic ailleurs**, et le
> bandeau « en construction » passe du cyan au gris.

## Pourquoi ce fichier existe

La décision du 01/10 dit ce qui a été répondu au retour d'ergonomie. Elle
s'arrêtait là où la propriétaire n'avait pas encore vu : le Parlement européen,
et ce que l'implémentation avait tranché sans elle. Celui-ci dit ce qu'elle a
tranché ensuite, et — parce que deux formulations ont été refusées le même jour
pour la même raison — ce qu'on a appris sur l'écriture d'une note de bulle.

## Le versant européen

Cinq fiches candidat sur 31 portent une activité au Parlement européen ; deux
n'ont que lui (Raphaël Glucksmann, Florian Philippot). Sur ces deux-là, les
bulles des sections 3 et 5 affichaient « par période de gouvernement » et
« à l'Assemblée ».

### Où se pose la bulle

| Fiche | Où est la bulle |
| --- | --- |
| Un seul versant, français ou européen | au titre, comme partout ; le texte est celui du versant |
| Un commutateur « député / député européen » | **dans chaque pastille** du commutateur ; le titre n'en porte plus |
| Un commutateur sans versant européen (« député / membre du gouvernement », prises de parole) | au titre : la règle ne vaut que si un versant européen est présent |

L'icône est **dans** la pastille, blanche sur la pastille active. Une première
forme la posait à côté ; une autre n'en gardait qu'une, au bout du commutateur,
dont le texte suivait le versant affiché. La propriétaire a retenu une icône
par pastille : le lecteur lit la règle d'un versant sans y basculer, et la
bulle ne recouvre plus le commutateur.

Dans le code, la pastille et le « i » sont deux boutons frères — HTML interdit
un bouton dans un bouton, et un clic sur le « i » basculerait de versant
(`BulleDePastille`, `InfoBulle.jsx`). Quand un commutateur de prises de parole
porte à la fois un versant européen et « membre du gouvernement », cette
dernière pastille reçoit le texte de l'Assemblée : c'est devant elle que ces
paroles sont prononcées. Aucune fiche n'est dans ce cas au 02/10/2026, et
aucun texte propre à cette qualité n'a été arrêté.

### Les quatre textes

| Emplacement | Phrase | Note |
| --- | --- | --- |
| Textes portés | Les textes dont la personne est l'auteur ou le rapporteur au Parlement européen, par thème et par étape de la procédure. | Un texte qui traite de plusieurs thèmes apparaît sur chaque ligne concernée. « Sans dossier rattaché » : la source ne dit pas où en est le texte. |
| Amendements | Les amendements dont il est l'auteur au Parlement européen, répartis par thème. | Chaque segment d'une barre est un texte amendé. Un amendement qui traite de plusieurs thèmes est compté sur chaque ligne concernée. |
| Votes | Les votes au Parlement européen, classés par thème. | Pour chaque texte, seul le vote le plus récent est retenu. Un texte qui traite de plusieurs thèmes apparaît sur chaque ligne concernée. |
| Prises de parole | Les prises de parole au Parlement européen, par type et par sujet. | La source publie les sujets le plus souvent en anglais. |

Trois mesures ont changé les brouillons de la veille :

- « Certains textes ne sont rattachés à aucun dossier » était faux par le mot
  « certains » : 251 des 252 textes européens de Florian Philippot n'ont pas
  d'étape, 53 des 58 de Marine Le Pen.
- « Le Parlement européen ne publie pas le sort des amendements » affirmait
  plus que le dépôt ne sait : c'est la source collectée qui n'en porte pas. La
  phrase redisait de surcroît l'en-tête de la carte, « sort non publié ».
- « En anglais » se mesure : sur les 5 319 prises de parole européennes de ces
  cinq fiches, environ 225 portent un sujet en français (comptage par
  mots-clés, approximatif). D'où « le plus souvent ».

### Les textes portés : des carrés, une ligne par thème

La décision du 01/10 gardait les rubans côté européen, au motif que les seize
stades de la nomenclature ne s'ordonnent pas. **Mesuré, l'argument tombe** : sur
les 382 textes européens des cinq fiches, quatre valeurs seulement paraissent —
sans dossier rattaché (326), procédure achevée (51), procédure rejetée (4),
acte délégué rejeté (1).

La vraie difficulté est le thème. À l'Assemblée, un texte a une commission, donc
une couleur. À Strasbourg, un texte touche plusieurs thèmes (232 des 252 de
Florian Philippot, 28 des 45 d'Emmanuel Maurel), et une fiche en porte vingt à
vingt-cinq. Quatre formes ont été rendues sur ces deux fiches :

| Forme | Ce qu'elle fait du thème | Pourquoi elle n'a pas été retenue |
| --- | --- | --- |
| A · la couleur du thème principal | une couleur par carré | efface les thèmes secondaires, ce que la propriétaire avait déjà refusé pour les rubans |
| B · un carré partagé en bandes | la part de chaque thème | illisible à cette taille |
| C · des carrés à l'encre, les thèmes en étiquettes | un clic éclaire les textes d'un thème | le thème ne se lit plus qu'au clic |
| **D · une ligne par thème** | **un texte est répété sur chacun de ses thèmes** | **retenue** : la couleur du thème reste |

La forme D dessine plus de carrés que de textes — 890 pour les 252 textes de
Florian Philippot, 128 pour les 45 d'Emmanuel Maurel. Trois façons de le montrer dans la figure ont été rendues
(un exemple entouré, des carrés pleins ou creux, des carrés plus petits). La
propriétaire n'en a retenu aucune : **le survol d'un carré entoure toutes les
occurrences du même texte**, et cela suffit. La note de la bulle le dit aussi.
Aucun compte n'est affiché par thème, comme arbitré le 17/09/2026.

## Les neuf écarts, et ce qu'ils sont devenus

| # | Ce que l'implémentation avait fait | Décision |
| --- | --- | --- |
| 1 | Une section vide ne portait pas de bulle | **Renversé.** « Cette décision a été prise au moment où on avait les notes en pied de section. Avec les bulles, ça n'a plus de sens. » Une section 2 entièrement vide, qui n'a plus de carte, porte une bulle unique à son titre : « Les textes de loi dont la personne est l'auteur ou le rapporteur, et les amendements dont elle est l'auteur. », sans note |
| 2 | Sans civilité, « Où cette personne a voté autrement que son groupe » | Gardé : c'est la règle des trois autres titres. 14 fiches candidat sur 31 n'ont pas de civilité — un sujet de données |
| 3 | Une phrase ajoutée à la méthodologie des écarts, après « quatre conditions » | La dernière lecture devient **la cinquième condition** du paragraphe |
| 4 | « Entrée au gouvernement » ne compte que les mandats à l'Assemblée | Gardé : le Sénat publie le motif de fin d'un mandat, la phrase y serait fausse |
| 5 | Les mandats au Sénat et au Parlement européen hors des mandats non couverts | Voir plus bas |
| 6 | La liste sous les carrés gardait la forme de l'ancienne liste | Gardé : elle affiche le rôle, et c'est la même liste sur tout le site |
| 7 | Les amendements européens perdaient aussi la colonne « ratio » | Gardé : la même figure des deux côtés |
| 8 | La bulle de la section 6 annonçait « la date où chaque source commence » | Réécrite : « Les limites de cette fiche : les mandats non couverts, et ce que les sources ne disent pas. » / « Quand un mandat n'est pas couvert, la fiche ne sait rien de cette période. Cela ne veut pas dire qu'il ne s'est rien passé. » |
| 9 | La palette : « Défense » presque au vert des votes « pour » | Voir plus bas |

### Les mandats au Sénat, et pourquoi pas ceux du Parlement européen

Lu à l'écran : la section 6 de Bruno Retailleau ne disait rien de ses quatre
mandats au Sénat, de 2004 à 2024 puis depuis novembre 2025, alors que la fiche
ne porte ni vote ni amendement. data.senat.fr n'est collecté que pour les
mandats (#885). La ligne arrêtée :

> **Sénat** — Ses mandats au Sénat, d'octobre 2004 à octobre 2024 puis depuis
> novembre 2025, ne sont pas couverts : ni vote, ni amendement, ni prise de
> parole.

Elle ne dit pas « aucune activité » : les textes déposés au Sénat sont publiés.
Deux fiches candidat la portent (`mandatsAuSenat`).

Le Parlement européen **n'a pas de ligne**, et c'est un reste déclaré. La même
mesure y a trouvé un défaut de données (#1163) : toutes les prises de parole
européennes de Jean-Luc Mélenchon, Marine Le Pen et Florian Philippot — 1 803,
956 et 1 587 — portent la même date, le 22 novembre 2016 ; Emmanuel Maurel n'en
a aucune de 2014 à mi-2019, Raphaël Glucksmann de mi-2019 à mi-2024 ; et les
profils ne déclarent aucune borne pour les sources européennes. Une période
calculée dessus publierait un fait faux.

### Deux lignes écrites par le pipeline

Sur les mêmes cinq fiches, la section 6 affiche tels quels deux avertissements
du pipeline : « votes non publiés : 19840 scrutin(s)… » et « explications de
vote : 48 des 48 explication(s)… ParlTrack transcrit l'annexe… ». Arbitré : la
première ne s'adresse plus au lecteur — elle dit un choix, pas un manque, et le
versant français ne dit nulle part que les votes sur amendement sont écartés ;
la seconde devient « Ses 48 explications de vote sont publiées sans lien vers
le document officiel. » Ces textes s'écrivent côté `src/` : l'arbitrage est
versé dans #1161, et **rien n'a changé à l'écran**.

### La palette

Remesurée contre les couleurs réservées de la fiche (écart OKLab × 100 ; sous
8, deux teintes se confondent) : il y a trois collisions, pas une.

| Commission | Se confond avec | Écart |
| --- | --- | ---: |
| Défense | le vert des votes « pour » | 2 |
| Affaires économiques | le prune de l'Assemblée, celui du bandeau de la liste sous les carrés | 3 |
| Affaires étrangères | le bleu du Parlement européen | 8 |

Un brun rouille pour « Défense » passe le validateur et tombe à 6 du bronze du
gouvernement. Toutes les familles sont prises : changer une teinte ne règle
rien. **La fiche candidat est livrée avec la palette actuelle** ; elle sera
reprise entière, sur maquette, quand les fiches de groupe et de gouvernement —
qui gardent la couleur au rang — recevront la même. D'ici là, aucune couleur ne
porte seule l'identité : la légende, le survol et la liste nomment la
commission.

## Ce qui s'ouvre au clic se replie au clic ailleurs

Demandé par la propriétaire le même jour, pour « un peu partout ». Mesuré sur
la fiche de François Ruffin : seules les bulles se repliaient. Une liste
ouverte sous une figure restait à l'écran pendant qu'on en ouvrait une autre,
et deux plis pouvaient rester ouverts ensemble.

| Règle | Retenue |
| --- | --- |
| Un seul bloc ouvert à la fois | oui |
| Tout clic hors du bloc le replie | oui |

Les deux, à sa demande — j'avais recommandé la première seule. La seconde
entraîne la première : ouvrir un bloc est un clic hors du précédent. « Hors du
bloc » se juge sur la carte entière, figure et liste comprises ; la barre de
défilement n'est pas un clic ailleurs.

Concernés, sur la fiche candidat : les listes des sections 2, 3 et 5 et les
trois plis (`useReplieAuClicDehors`, et le composant `Pli`). **Le repli attend
le clic et garde la cible en place** : replier un bloc retire de la hauteur
au-dessus de ce que le lecteur vise — 131 px pour une liste d'un texte — et la
page remonterait sous le curseur. Mesuré à l'écran après correction : la cible
ne bouge pas. Les fiches de groupe et de gouvernement ne sont pas touchées.

## Le bandeau « en construction » passe au gris

Hors de la fiche, mais demandé dans la même séance : le bandeau d'état, en tête
de toutes les pages, était cyan (`#00e5ff`) — une couleur hors palette, choisie
pour qu'il ne se lise pas comme du contenu. La propriétaire l'a ramené à un
gris de la charte (`#e7e4df`, la valeur de `--border-strong`). Le jeton
`--notice` garde son nom ; il change dans `index.css` et dans l'habillage des
pages d'instantanés (`scripts/chrome-instantane.mjs`, qui réécrit
`public/rapports/`). Contraste de l'encre sur ce gris : 14,3:1.

## Ce qui a changé de place dans le code

Pour qui reprend la fiche : `BulleDePastille` dans `InfoBulle.jsx` (la bulle
d'une pastille, et sa feuille dans `ParolesParPeriode.css`) ; les textes
européens dans `BULLES` de `CandidateProfile.jsx`, suffixés `Ue`, avec
`proposeVide` ; `CarresThemesUe.jsx` et `utils/carresThemesUe.js` (les textes
portés européens, `rangerParTheme`) ; `mandatsAuSenat` dans
`utils/profilCandidat.js`. La fiche de lignée et la fiche de gouvernement
gardent la cascade en rubans : `Cascade` et `disposerCascadeUE` n'ont plus de
lecteur côté candidat, et restent pour elles.

Une phrase est entrée avec les carrés sans avoir été vue par la propriétaire :
l'invitation de la liste, « Cliquez un carré, une étape ou un thème pour lire
les textes. » Sans elle, la liste écrivait son défaut, qui parle de rubans.

## Ce qu'on a appris sur une note de bulle

Deux notes ont été jugées « bancales » le même jour : « Un texte paraît sur la
ligne de chacun de ses thèmes : les lignes ne s'additionnent pas », puis « Un
texte voté plusieurs fois compte une fois, à son dernier vote ». La propriétaire
n'a pas énoncé de règle ; ce qui suit se déduit des textes qu'elle a écrits ou
retenus les 01 et 02/10, et lui reste à confirmer.

- **La phrase** est un groupe nominal : l'objet montré, puis l'axe qui range la
  figure (« Les votes…, classés par thème »). Elle couvre toute la partie.
- **La note** répond à la question que le lecteur se pose devant la figure, à
  partir de ce qu'il a sous les yeux : elle définit un terme affiché (« Sans
  dossier rattaché : … »), dit ce qu'est une marque (« Chaque segment d'une
  barre est un texte amendé »), dit ce qui est montré ou non, ou écarte une
  fausse conclusion.
- **Elle n'est ni une règle de comptage, ni une conséquence dite en négatif.**
  Les deux phrases refusées étaient cela.
- **Avant d'écrire une mise en garde, se demander si la figure peut la
  porter** — règle 8 du `DESIGN_SYSTEM` §6 bis.

Un brouillon de la veille ne se soumet pas tel quel : il se réécrit d'abord, et
se montre rendu dans sa bulle, sur la fiche.

## Ce que cette suite rend caduc dans les décisions de la veille

Une décision ne se réécrit pas en place : elle dit ce qui était vrai le jour où
elle a été prise. Deux décisions du 01/10/2026 décrivent un état que celle-ci a
changé, et se lisent désormais avec elle.

| Décision | Ce qui n'est plus vrai |
| --- | --- |
| [`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md) | Le texte de la bulle de la section 6, dans le tableau des huit textes : il est réécrit |
| | « Fait, versant français » pour le diagramme en rubans, et « Le versant européen garde `Cascade` » : les textes portés européens sont en carrés |
| | Dans « Ce qui reste ouvert » : le versant européen (ses quatre textes sont arrêtés), les mandats au Sénat (ils ont leur ligne), la phrase de méthodologie sur la dernière lecture |
| | Les bulles « au titre », sans exception : sur une fiche à deux versants, elles sont dans les pastilles du commutateur |
| [`carres-des-textes-et-couleurs-des-commissions`](carres-des-textes-et-couleurs-des-commissions.md) | « Le versant européen des textes portés garde la cascade : ses seize stades ne s'ordonnent pas » — quatre valeurs seulement paraissent sur les fiches, et la figure est en carrés |
| | « Défense » comme seule collision de la palette : il y en a trois |

La règle « une section vide ne porte pas de bulle » n'était écrite dans aucune
décision : elle vivait dans le code et dans un test, tous deux retournés.

## Ce qui reste ouvert

| Sujet | Où il en est |
| --- | --- |
| Les mandats au Parlement européen en section 6 | Attend #1163 |
| Les deux lignes européennes de la section 6 | Arbitrées, à écrire côté `src/` (#1161) |
| L'encadré européen de la section 3 | Non revu : les encadrés français sont devenus des lignes de la section 6, celui-ci est resté sous sa figure |
| La palette des commissions | Reprise entière avec les fiches de groupe et de gouvernement |
| Quatre textes déjà codés, jamais confirmés | Les lignes « Votes » et « Prises de parole » de la section 6, « Cliquez un carré, une étape ou une commission pour lire les textes. » et sa jumelle européenne, « Sur 168 scrutins de textes en dernière lecture » |
| Le motif de fin d'un mandat au Sénat | Dans les données, affiché nulle part |
| La civilité | Absente de 14 fiches candidat sur 31 |
| La largeur téléphone | Ni l'icône dans la pastille ni les carrés européens n'ont été regardés à 390 px |
| L'ancrage au clic (constat 3 du retour) | Traité en partie : ce qui s'ouvre se replie, et l'élément cliqué reste en place. L'effet sur le repérage n'a pas été mesuré |
| Le scroll (constat 2) | La fiche de Delphine Batho fait encore 10 451 px, dont 4 665 pour sa section 4 — mesure du 01/10, non refaite |
| La fiche comme « super-CV » (constat 6) | À la propriétaire : c'est du positionnement |
| Le repli au clic sur les fiches de groupe et de gouvernement | Reporté à leur revue, à sa demande |
| La double comparaison de la section 4 | #1159 |
