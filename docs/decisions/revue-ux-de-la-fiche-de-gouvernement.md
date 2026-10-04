<a id="revue-ux-de-la-fiche-de-gouvernement"></a>

# La revue d'ergonomie de la fiche de gouvernement : ce qui a été décidé, section par section (2026-10-04)

`2026-10-04`

> **En bref** — Troisième et dernier volet de la revue d'ergonomie des fiches,
> après la fiche candidat et la fiche de groupe
> ([`revue-ux-de-la-fiche-de-groupe`](revue-ux-de-la-fiche-de-groupe.md)). Il
> part d'un retour extérieur
> ([`retour-ux-sur-les-fiches-gouvernement`](retour-ux-sur-les-fiches-gouvernement.md)).
> La propriétaire a tout arbitré **sur maquette, puis donné son accord avant le
> code**. **Six bulles** remplacent les quatre renvois en pied de section.
> **La parole** prend la figure de la fiche de groupe : débats rangés par prises
> de parole, un segment par membre, un membre lu à la fois — un sujet ouvert
> passe de **5 880 à 638 px** sur Borne. **Les projets de loi passent en
> carrés**, cinq colonnes : la fiche de gouvernement était la seule à garder un
> diagramme de flux. **Les actes au Journal officiel passent en barres par
> ministère, à l'encre.** Deux règles de forme en sortent, ajoutées au
> `DESIGN_SYSTEM` §6 bis : **une couleur porte une information ou se retire**,
> et **même logique, même forme**. Une mention temporaire signale l'interruption
> du Journal officiel (#1199).

## Pourquoi ce fichier existe

Le retour dit ce qu'un relecteur a vu, et ce qu'il a mal lu. Ce fichier dit ce
qui a été retenu, ce qui a été proposé puis écarté, et ce qui attend une
donnée — pour que la suite ne le rediscute pas.

**La méthode** est celle du volet groupe, précisée par deux mises au point de
la propriétaire. Un choix validé sur maquette n'est pas un feu vert : rien ne
se code sans son accord explicite — la mention temporaire avait été codée trop
tôt, et elle l'a relevé. Et sa relecture ne porte que sur l'interface : un
document du dépôt part en PR sans attendre.

## Ce qui a été retenu, section par section

| Section | Avant | Après |
| --- | --- | --- |
| Toute la fiche | Quatre renvois en pied de section | **Six bulles** au titre ; ce qui s'ouvre au clic se replie au clic ailleurs |
| En bref | — | La bulle seule |
| Qui le composait | Liseré, flèche et lien « rattachés » en marron ; deux cartes pour Élisabeth Borne | **Au neutre** ; **une seule carte** pour une Première ministre ; un tiroir ouvert à la fois |
| Sur quoi ils ont pris la parole | Dix débats rangés par nombre de membres, « 21 / 50 » ; un sujet ouvert dépliait tous ses membres | **Rangés par prises de parole**, une barre découpée par membre, deux colonnes nommées ; **un membre lu à la fois**, son nombre au clic ; prises de parole sans intitulé **comptées** |
| Ce qu'il a fait déposer | Diagramme de flux matière → étape | **Un carré par projet de loi**, cinq colonnes ; pastille 49.3 qui allume ses carrés au survol |
| Ce qu'il a fait entrer en vigueur | Diagramme de flux, cinq ministères en couleur, deux rangées de filtres, un paragraphe d'explication | **Une barre par ministère, à l'encre** ; la part sombre est celle des actes dont le titre cite une loi |
| Ce qu'on n'a pas pu lire | — | La bulle seule |

### Les mesures

Sur l'application construite, à 1 440 px de large, le 04/10/2026.

| Fiche | Repliée, avant | Repliée, après | Premier sujet ouvert, avant | Après |
| --- | ---: | ---: | ---: | ---: |
| Borne (`BORNE`) | 4 467 px | 3 879 px | 10 550 px (avec le pôle le plus chargé) | 4 517 px |
| Lecornu II (`LECORNU_II`) | non relevé | 4 007 px | — | — |
| Fillon I (`FILLON_1`) | 3 616 px | 3 187 px | sans sujet | sans sujet |

## La parole d'un gouvernement

**La figure est celle de la fiche de groupe.** La propriétaire l'a choisie
contre la forme que l'agent recommandait (une ligne par membre), puis posé la
règle : *même logique, même forme*. Trois formes avaient été rendues pour un
sujet ouvert, « motion de censure » sur Borne :

| Forme | Principe | Hauteur |
| --- | --- | ---: |
| Avant | Vingt blocs de membre dépliés, cinq propos chacun | 5 880 px |
| A | Une ligne par membre, un seul ouvert | 1 416 px |
| B | Tous les membres, deux propos chacun | 4 752 px |
| **C — retenue** | **La barre du sujet découpée par membre, un membre lu à la fois** | **519 px** sur maquette, 638 sur la page |

- **« 21 / 50 » avait été lu comme 21 interventions.** Les deux colonnes
  s'écrivent désormais : « prises de parole », « membres ».
- **Le nombre d'un membre ne s'affiche que pour celui qu'on désigne** — « Éric
  Dupond-Moretti · 87 prises de parole sur 857 dans "motion de censure" ». Il
  était écrit à côté de vingt noms à la fois. La comparaison se lit encore dans
  la largeur des segments : c'est la conséquence, connue, de la barre découpée.
- **Une personne passée par deux portefeuilles n'a qu'un segment** ; le détail
  dit sous quel titre elle parlait.
- **Les prises de parole sans intitulé sont comptées**, sous « Intitulé non
  publié », ligne non ouvrable. La fiche les jetait : 2 144 sur 26 034 pour
  Borne, 1 923 sur 15 269 pour Lecornu II. La règle du sujet est celle de la
  fiche candidat (`utils/sujetIntervention.js`).
- **Aucun filtre de rôle.** `role_seance` ne connaît que la présidence, et
  `fonction` était vide hors candidats déclarés (#1200). Une prise de parole
  est retenue par les dates des fonctions de la personne.

Sous un mot recherché ou une période, la section garde sa liste d'avant.

## Les projets de loi en carrés

| Forme | Colonnes | Sort |
| --- | --- | --- |
| A | Les sept étapes du diagramme | Écartée |
| **B** | **Cinq : déposés, en navette, adoptés, promulgués, rejetés** | **Retenue** |

« Adoptés » réunit les trois adoptions, comme la colonne unique de la fiche
candidat. **Le 49.3 est dit par sa pastille** ; au survol, ses carrés
s'allument et les autres s'estompent — demandé par la propriétaire en
commentaire sur la maquette.

**Pas de pastille pour la commission mixte paritaire**, qu'elle a envisagée :
« adopté » y est exact, il n'y a pas de lecture fausse à prévenir, et une
seconde pastille ôterait son sens d'alerte à la première. L'étape exacte se lit
en toutes lettres dans la liste ; le sigle « CMP », qu'elle a dû se faire
expliquer, ne s'écrit plus seul.

La première colonne, « déposés », est propre au gouvernement : candidat et
groupe ne montrent un texte qu'à partir de l'examen en commission.

## Les actes au Journal officiel

Le retour lisait « le titre ne le dit pas » comme une catégorie par défaut qui
écrasait la répartition par ministère. C'était une des deux destinations du
flux, mais elle recevait 16 006 des 17 056 actes de Borne.

| Forme | Principe | Sort |
| --- | --- | --- |
| **A** | **Une barre par ministère ; la part sombre est celle des actes dont le titre cite une loi** | **Retenue, à l'encre** |
| B | Les lois citées en carrés, puis les barres | Écartée |

**La couleur.** La propriétaire a d'abord voulu la garder, puis un code commun
avec les projets de loi. Trois voies ont été examinées et écartées :

| Voie | Pourquoi elle ne tient pas |
| --- | --- |
| Les cinq teintes d'avant | Elles suivent le rang, pas le ministère : la première barre est toujours bleue |
| Une table ministère → commission | Écrite à la main, sans source ; l'Économie relève de deux commissions. Refusée |
| Colorer les projets de loi par ministère | La fiche ne porte pas le ministère d'un projet : `initiateurs` nomme des personnes, sans portefeuille. **Corrigé le 04/10/2026** — cette ligne écrivait « la fiche ne connaît que le Premier ministre comme auteur : 110 des 111 projets de Borne », et c'était faux. Élisabeth Borne figure parmi les auteurs de 110 des 111 projets de sa fiche ; elle n'y est seule que sur 46 (40 portent deux noms, 25 trois ou plus). Mesure et suite : [`ministres-presentant-un-projet-de-loi-1204`](ministres-presentant-un-projet-de-loi-1204.md) |

D'où l'encre, et la règle : **une couleur porte une information ou se retire**.
La voie reste ouverte : la source publie le ministre qui présente un projet de
loi (`coSignataires` du document de dépôt), et la collecte le lit depuis #1204
(PR #1208) : le portefeuille arrive sur les fiches au run qui suit.

**Ce qui ne devait pas se perdre** avec le paragraphe retiré sous la figure,
et qu'un test existant a rattrapé : « le titre ne le dit pas » ne veut pas dire
« sans loi » — écrit dans la légende —, et le délai d'une loi est celui de son
premier acte de cette période — écrit là où le délai s'affiche.

## Les bulles

Écrites ou recomposées par la propriétaire, rendues dans leur bulle, recopiées
dans `tests/test_revue_ergonomie_fiche_gouvernement.py`.

| Section | Phrase | Note |
| --- | --- | --- |
| En bref | Le gouvernement en quelques faits. | Le nombre de membres varie au fil des remaniements. |
| Qui le composait | Les ministres, ministres délégués et secrétaires d'État de ce gouvernement, par ministère. | Sont comptés tous les membres passés par ce gouvernement, même brièvement. |
| Sur quoi ils ont pris la parole | Les prises de parole des membres du gouvernement à l'Assemblée, par débat. | Une prise de parole peut tenir en quelques mots. |
| Ce qu'il a fait déposer | Les projets de loi que ce gouvernement a présentés au Parlement, et jusqu'où chacun est allé. | Un texte arrêté à une étape n'est pas nécessairement rejeté. Le 49.3 est un fait de procédure, jamais un vote. |
| Ce qu'il a fait entrer en vigueur | Les décrets, arrêtés et ordonnances parus au Journal officiel pendant ce gouvernement, par ministère. | Seuls les actes qui touchent au droit sont pris en compte et non ceux qui relèvent du fonctionnement interne de l'État (nominations, promotions…). Un acte peut appliquer une loi adoptée avant ce gouvernement. |
| Ce qu'on n'a pas pu lire | Les limites de cette fiche : ce que les sources ne disent pas sur ce gouvernement. | Une information absente de cette fiche n'a pas été trouvée dans les sources. Cela ne veut pas dire qu'il ne s'est rien passé. |

Pour la note des actes, elle a écarté « qui concernent une personne »,
« d'ordre administratif » et « politique », et retenu **« fonctionnement
interne »**, son mot. La note laisse de côté les naturalisations et les
médailles, écartées elles aussi.

## La page de méthodologie

Elle écrivait : « Aucune section de méthode ne décrit encore cette fiche. »
Quatre sections sont écrites, une par bulle qui y mène : `gouv-composition`,
`gouv-paroles`, `gouv-textes`, `gouv-actes`.

## La mention temporaire

Le service qui diffuse le Journal officiel refuse toute requête depuis le
02/10/2026. La propriétaire a arbitré une **mention de circonstance**, et non
une borne permanente : texte « Données incomplètes depuis le 2 octobre 2026… »,
sur la fiche du gouvernement en place seulement, à l'encre pleine, **posée et
retirée à la main**. L'issue #1199 ne se ferme pas tant qu'elle s'affiche.

## Ce qui attend des données

| Sujet | Où il en est |
| --- | --- |
| Le ministre qui présente un projet de loi | La source le publie ; changement de schéma côté données, en attente d'arbitrage |
| `fonction` sur les prises de parole | #1200, PR #1201 : arrivera après un run |
| « Motion de censure » : la ligne d'avant disait 21 membres, la figure en compte 19 | Écart non expliqué entre l'agrégat et le détail servi |

## Corrigé à la relecture de la page

La propriétaire a relu la page servie le 04/10/2026, après les maquettes. Sept
corrections, toutes de sa main :

| Section | Avant la relecture | Après |
| --- | --- | --- |
| Sur quoi ils ont pris la parole | Le membre se nommait au survol d'un segment | **Au clic seulement.** Sur « Intitulé non publié », qui ne s'ouvre pas, le clic nomme le membre et son nombre |
| Ce qu'il a fait déposer | Le texte survolé s'écrivait sur une ligne sous la grille, qui décalait la suite | **L'infobulle des carrés** des fiches candidat et groupe (`.cp-car-bulle`), hors du flux |
| Ce qu'il a fait entrer en vigueur | La ligne d'un ministère s'ouvrait d'un bloc | **Le nom ouvre tout le ministère, chaque part de la barre la sienne** — le geste de la parole : le sujet entier, ou un membre |
| — légende | « Le titre ne le dit pas » ne veut pas dire « sans loi » sur sa propre ligne | À la suite de l'étiquette qu'elle précise |
| — cartes de tête | « actes parus au Journal officiel pendant ce gouvernement » ; « actes de personne, rangés là par le Journal officiel lui‑même », suivi de « dont N d'après leur titre… » ; le gris sur la carte des actes qui touchent au droit | « actes parus au Journal officiel » ; « actes relevant du fonctionnement interne de l'État » ; **le gris sur la carte de ce qui est écarté**, le blanc sur ce que la section montre |
| En bref (gouvernement et groupe) | Rien ne disait pourquoi aucun groupe n'est déclaré majoritaire | La note de la bulle reçoit « L'Assemblée nationale ne dit quel groupe est majoritaire qu'une fois la législature achevée. », seulement quand la fiche l'écrit — mesure dans [`position-politique-groupes-686`](position-politique-groupes-686.md) |

Le nombre d'actes écartés d'après leur titre ne se lit plus sur la fiche : la
règle est en méthodologie (« c'est le titre de l'acte qui le dit »), et
`tests/test_actes_gouvernement_1029.py` l'y exige désormais.

## Ce que ce fichier rend caduc

| Dans | Ce qui ne vaut plus |
| --- | --- |
| [`fiche-de-gouvernement-330`](fiche-de-gouvernement-330.md) | Le flux matière → étape, les renvois en pied, le compte de membres seul sous la parole |
| [`actes-sur-la-fiche-de-gouvernement-1029`](actes-sur-la-fiche-de-gouvernement-1029.md) | Le flux à deux colonnes, les cinq teintes de ministère, les deux rangées de filtres |

## Ce qui reste ouvert

- **Une phrase de « Ce qu'on n'a pas pu lire » contredit la bulle** : « Depuis
  2024, l'Assemblée nationale ne déclare plus la position de ses groupes »
  laisse croire à un arrêt, quand c'est la législature en cours qui n'est pas
  encore qualifiée. Question posée à la propriétaire, sans réponse.
- **Le téléphone** : aucune de ces figures n'y a été regardée (#867).
- **Quatorze des dix-sept fiches de gouvernement** n'ont pas été regardées à
  l'écran : seules Borne, Lecornu II et Fillon I l'ont été.
- **Trois textes écrits en codant**, à faire relire : la ligne « Prises de
  parole » de « Ce qu'on n'a pas pu lire », le message d'une section de parole
  vide, et les quatre sections de méthodologie.
