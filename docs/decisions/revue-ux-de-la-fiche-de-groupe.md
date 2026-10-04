<a id="revue-ux-de-la-fiche-de-groupe"></a>

# La revue d'ergonomie de la fiche de groupe : ce qui a été décidé, section par section (2026-10-02)

`2026-10-02`

> **En bref** — Second volet de la revue d'ergonomie des fiches, après la
> fiche candidat
> ([`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md),
> [`versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat`](versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat.md)).
> La propriétaire a tout arbitré **sur maquette, avant le code**, le
> 02/10/2026. **Sept bulles** remplacent les phrases sous les titres, les
> pieds et les renvois. **« Avec qui ils votent » passe en carrés** : le
> nombre de textes communs, écrit en gros, avait été lu comme un pourcentage.
> **La liste des personnes s'ouvre un groupe à la fois** : 2 544 px au plus
> pour Ensemble pour la République, contre 7 583. **Les textes portés et les
> amendements reçoivent les figures de la fiche candidat.** **La palette des
> commissions est refaite pour les trois types de fiche** : quatre teintes se
> confondaient avec une couleur déjà prise. La fiche d'Ensemble pour la
> République passe de **6 572 à 5 889 px** repliée. **Deux choses attendent
> des données** : la figure des prises de parole, codée mais éteinte tant que
> le corpus ne porte pas le rôle de séance, et la fin de la note d'« En bref ».

## Pourquoi ce fichier existe

Le volet candidat avait posé trois règles et laissé la fiche de groupe en
l'état : rubans, couleur au rang, renvois en pied. Un retour extérieur sur
trois fiches de groupe a ouvert ce volet
([`retour-ux-sur-les-fiches-groupe`](retour-ux-sur-les-fiches-groupe.md), qui
le consigne constat par constat). Ce fichier dit ce qui a été retenu,
ce qui a été proposé puis écarté, et ce qui reste suspendu à une donnée — pour
que le volet gouvernement, qui suit, ne le rediscute pas.

**La méthode a changé d'un cran** : côté candidat, chaque section était codée
dès sa forme choisie. Ici la propriétaire a demandé de **valider toute la
fiche sur maquette avant d'écrire une ligne** — les sections se répondent
(palette, repli, bulles), et un code livré par morceaux fige des choix que la
suite défait.

## Ce qui a été retenu, section par section

| Section | Avant | Après |
| --- | --- | --- |
| En bref | Aucun texte | Une bulle au titre |
| 1 · Qui sont-ils | Phrase sous le titre, pied, renvoi ; tous les noms dépliés d'un coup, une colonne par groupe | Une bulle ; les candidats déclarés dans la carte ; **un rang par groupe, un seul ouvert** |
| 2 · Sur quoi ils ont pris la parole | Les dix débats où le plus de membres sont intervenus | **Une barre par débat, découpée par membre**, avec les pastilles de nature ; une bulle — **éteinte jusqu'au prochain run**, voir « Ce qui attend des données » |
| 3 · Ce qu'ils ont proposé | Cascade en rubans avec deux boutons de rôle ; barre pleine et « ratio par texte » | **Un carré par texte, une ligne par rôle** ; **barre découpée par texte** ; une bulle par carte |
| 4 · Ce qu'ils ont voté | Phrase, pied, renvoi | Une bulle ; la figure ne change pas |
| 5 · Avec qui ils votent | Une barre, et le nombre de textes communs en gros à droite | **Un carré par texte commun** ; la base en petit ; une bulle |
| 6 · Ce qu'on n'a pas pu lire | Phrase et deux renvois | Une bulle, et ses deux liens |

Sur toute la fiche : **ce qui s'ouvre au clic se replie au clic ailleurs**
(`useReplieAuClicDehors`, le mécanisme de la fiche candidat), et la ligne
« Période 3 sur 3 · … les flèches ← → du clavier naviguent aussi » se tait.

### Les mesures

À 1 440 px de large, sur l'application construite :

| Fiche | Repliée, avant | Repliée, après | Liste des personnes ouverte, avant | Le plus grand rang ouvert, après |
| --- | ---: | ---: | ---: | ---: |
| Ensemble pour la République (`AN-REN`) | 6 572 px | 5 889 px | 7 583 px, 448 personnes | 2 544 px (La République en Marche, 343 personnes) |
| Écologie Démocratie Solidarité (`AN-EDS`) | 5 545 px | 4 872 px | 411 px, 17 personnes | 146 px |
| LIOT (`AN-LIOT`) | 6 352 px | 5 584 px | 631 px, 35 personnes | 212 px |

À 390 px, aucune des trois ne déborde en largeur ; le rang de La République en
Marche y fait encore 7 560 px, sur une seule colonne. **Le téléphone n'a pas
été revu au-delà de cette mesure.**

## « Avec qui ils votent » : une erreur de lecture qui était un constat

Le retour parlait de « pourcentages de proximité (51 %, 50 %) ». La figure
n'affichait aucun pourcentage : « 51 », « 50 » étaient des **nombres de textes
communs**, le dénominateur. Face à La France insoumise, la barre disait 9
textes dans le même sens sur 51. Un relecteur attentif a lu le plus gros
nombre de la ligne comme un taux : c'est la règle 8 du `DESIGN_SYSTEM` §6 bis
— ce qui empêche une lecture fausse se voit dans la figure.

Quatre formes ont été rendues sur les données d'Ensemble pour la République
et d'Écologie Démocratie Solidarité.

| Forme | Principe | Sort |
| --- | --- | --- |
| A | Les trois comptes en gros, la base en étiquette au bout de la barre | Écartée |
| **B** | **Un carré par texte commun ; au survol, le même texte s'allume chez chaque groupe** | **Retenue** |
| C | Trois colonnes, une par nature | Écartée |
| D | Une grille textes × groupes, par date | Écartée |

**La base reste écrite, en petit**, au bout des trois comptes (« 51 textes
communs ») : un ratio de groupe ne se publie qu'avec son dénominateur
(`AGENTS.md` §2 règle 7), et compter 51 carrés n'est pas le lire. L'ordre des
lignes ne change pas — textes communs d'abord, l'accord pour départager.

**Écarté du retour** : dire « la part des votes consensuels qui gonflent
artificiellement » la proximité. Rien n'établit que cette part se mesure, et
« gonfler » est un jugement sur les votes.

## La liste des personnes

Cinq formes rendues : une ligne par personne avec une recherche, une fenêtre à
hauteur fixe, **un groupe à la fois (retenue)**, un chemin à la fois, la
figure elle-même comme liste.

- **Pas de champ de recherche** : proposé, montré, écarté par la propriétaire.
- **Pas de « membres clefs »**, que le retour recommandait (« présidents,
  porte-paroles, démissionnaires ») : c'est la fiche qui déciderait qui compte
  dans un groupe, et elle nommerait des personnes par un comportement
  (`AGENTS.md` §2 règle 1). Les données ne portent d'ailleurs aucune fonction
  de groupe — seulement des fonctions d'instance.
- **Le pied de la section était un fait**, pas une mention : les candidats
  déclarés passés par ces groupes restent, dans la carte. « 448 profils
  publiés sur 448 personnes » ne s'écrit plus que s'il en manque.

## « Ce qu'ils ont proposé »

**Les textes portés.** Mesuré sur les 29 groupes : de 28 textes publiés
(Écologie Démocratie Solidarité) à 390 (La République en Marche, XVe). Trois
formes en carrés : celle de la fiche candidat avec ses boutons de rôle, une
ligne par commission à l'encre seule, **une ligne par rôle (retenue)**. La
forme sans couleur avait été recommandée, parce qu'elle dispensait de la
palette ; la propriétaire a gardé la couleur, comme côté candidat. Un texte
que le groupe porte aux deux titres figure sur les deux lignes — 9 des 106
textes d'Ensemble pour la République en XVIIe.

**Les amendements.** Deux découpes par texte rendues : celle de la fiche
candidat telle quelle (**retenue**), et une variante à segments jointifs dont
chaque largeur est exacte. **Aucune des deux ne montre chaque texte** : un
groupe amende jusqu'à 126 textes sur une ligne. Mesuré à 1 440 px sur
Ensemble pour la République, 28 textes sur 237 n'ont aucun pixel dans la forme
retenue ; la variante n'en cachait aucun, mais 131 y faisaient moins d'un
pixel. Le nombre de textes reste écrit au bout de chaque ligne. La colonne
« ratio par texte » disparaît, comme côté candidat.

**La cosignature a été proposée, puis retirée.** Une barre disant combien de
membres signent chaque amendement a été maquettée, sur une question mal
comprise ; la propriétaire l'a écartée — le nombre de signataires n'a pas
d'importance ici. Aucun champ n'est à demander.

## Les bulles

Sept bulles, écrites ou choisies une à une par la propriétaire, rendues dans
leur bulle avant d'être retenues. Elles sont recopiées dans
`tests/test_revue_ergonomie_fiche_groupe.py`, pour qu'une reformulation
échoue.

| Bulle | Phrase | Note |
| --- | --- | --- |
| En bref | L'histoire du groupe à l'Assemblée : ses noms, ses effectifs, sa position face au gouvernement. | D'une législature à la suivante, l'Assemblée ne dit pas quel groupe succède à quel autre. Empreinte politique établit ce lien en comparant leurs membres. |
| Qui sont-ils | L'évolution de la composition du groupe d'une législature à la suivante et sous chacun de ses noms successifs. | Sont comptés tous les députés passés par le groupe pendant la législature, même brièvement. |
| Les textes portés (carte) | Les textes de loi portés par des membres du groupe, comme auteurs ou comme rapporteurs, à l'étape qu'ils ont atteinte. | Seuls les textes examinés en commission sont affichés. Un texte arrêté à une étape n'est pas nécessairement rejeté. |
| Les amendements (carte) | Les amendements des membres du groupe, par matière et par texte amendé. | Le nombre d'amendements seul peut tromper. Chaque segment d'une barre est un texte amendé ; sa largeur est le nombre d'amendements déposés sur ce texte. |
| Ce qu'ils ont voté | Les scrutins où le groupe a voté d'une seule voix, et ceux où ses membres se sont partagés, par législature. | « Quorum atteint » : au moins la moitié des membres du groupe a voté. « D'une seule voix » : toutes les positions exprimées vont dans le même sens. |
| Avec qui ils votent | La position du groupe comparée à celle de chaque autre groupe, texte par texte, par législature. | Voter dans le même sens n'est pas s'entendre : deux groupes peuvent rejeter un texte pour des raisons opposées. « Nuance » : l'un des deux groupes s'est abstenu. |
| Ce qu'on n'a pas pu lire | Les limites de cette fiche : ce que les sources ne disent pas sur ces groupes. | Une information absente de cette fiche n'a pas été trouvée dans les sources. Cela ne veut pas dire qu'il ne s'est rien passé. |

Chacune se termine par « Lire la méthode → ». La dernière porte d'abord
« Sources et couvertures → », le libellé de la propriétaire — repris côté
candidat le 03/10/2026, à la place de « Nos sources, et depuis quand → ».

**Ce qui a quitté la fiche sans entrer dans une bulle** : les règles de
comptage et de tri (« cosigné par vingt membres… compte une fois », « rangés
par nombre de textes communs, puis de votes dans le même sens ») et ce qui
justifiait une absence (« pourquoi aucun taux d'adoption », « pourquoi aucun
indice de cohésion », « les absences ne sont jamais comptées »). La page de
méthodologie les porte déjà.

### La règle 8 est complétée

Le 01/10/2026, la note des amendements du candidat disait « le nombre
d'amendements seul peut tromper ». Elle a été retirée quand la barre s'est
découpée par texte : l'alerte devait se lire dans la figure. En relisant cette
bulle, la propriétaire n'y a plus trouvé l'alerte. **La figure ne dispense pas
de la dire** : la phrase revient en tête de note, sur la fiche de groupe et
sur les deux versants de la fiche candidat. La règle 8 exige que l'alerte soit
dans la figure ; elle n'interdit pas que la bulle la redise.

## La palette des commissions

La palette du 01/10/2026 passait le validateur et se confondait pourtant avec
le reste du site. Mesuré contre les couleurs déjà prises (écart OKLab × 100 ;
sous 8, deux couleurs se confondent) : **quatre collisions, pas trois** — trois franches, une à la limite.

| Commission | Se confondait avec | Écart |
| --- | --- | ---: |
| Défense | le vert des votes « pour » | 2 |
| Affaires économiques | le prune de l'Assemblée | 3 |
| Finances | le sarcelle du Sénat | 4 |
| Affaires étrangères | le bleu du Parlement européen | 8,5 |

Garder les teintes saines et n'en changer que trois a été essayé : les
nouvelles se confondent avec leurs voisines (paires à 7). Trois palettes ont
été cherchées par calcul, contre les deux contraintes à la fois — toutes
paires entre elles, et chaque teinte loin de toute couleur prise.

| Palette | Principe | Couleur prise la plus proche | Deux teintes les plus proches | Sous daltonisme |
| --- | --- | ---: | ---: | ---: |
| **A — retenue** | **Le plus loin de tout : plus de vert ni de brun** | **12** | **16,1** | **8,2** |
| B | Sans violet | 10 | 15,5 | 8,4 |
| C | Garder les quatre teintes qui ne heurtaient rien | 10 | 15,5 | 7,8 |

| Commission | Avant | Palette A |
| --- | --- | --- |
| Affaires culturelles et éducation | `#f16675` | `#c57576` |
| Affaires économiques | `#882255` | `#bf165b` |
| Affaires étrangères | `#463fa0` | `#2355f1` |
| Affaires sociales | `#259ce6` | `#1096e9` |
| Défense | `#137731` | `#9c40bf` |
| Développement durable | `#ab47aa` | `#ef45c4` |
| Finances | `#09a68b` | `#15628e` |
| Lois | `#9d9201` | `#959609` |

Les deux gris ne changent pas. **La fiche de groupe et la fiche de
gouvernement, qui coloraient au rang, lisent désormais la même table**
(`utils/commissions.js`). Son coût est connu : la palette A porte deux
violets, dont la direction artistique s'était écartée pour l'identité du site.

## Ce que la page servie a corrigé (04/10/2026)

Relue sur la vraie page, une fois `role_seance` publié, la figure des prises de
parole affichait **0** sur Écologie Démocratie Solidarité. Le build ne gardait
que les interventions portant `theme_officiel` : les 969 de ses 17 membres,
toutes avec leur texte et leur nature, étaient jetées avant le compte.

- **La règle du sujet est celle de la fiche candidat**
  (`utils/sujetIntervention.js`, que le build importe) : le thème, sinon le
  sujet du chemin de l'ordre du jour. Une intervention sans aucun intitulé se
  compte dans sa nature et se range sous **« Intitulé non publié »**.
- **Cette ligne se compte et ne s'ouvre pas** : ses textes ne sont pas servis.
  Sur la XVe elle porte presque tout — 82 080 des 87 367 prises de parole de
  La République en Marche — et son paquet pesait 19,6 Mo au clic.
- **Le retrait vaut pour toute intervention, avec ou sans intitulé** : la
  présidence de séance et la parole de ministre. **La parole de rapporteur
  reste comptée** (arbitré le 04/10). La fiche candidat ne filtre rien et ne
  change pas.
- **Les extraits d'un débat ouvert passent en forme B** : le nom du député en
  tête de son bloc, la date au-dessus de chaque propos. La grille d'avant ne
  laissait que 512 px au texte dans un tiroir de 932.

L'intitulé manquant sur la XVe est un défaut de normalisation, pas un silence
de la source : `theme_officiel` n'est recopié que si l'entrée porte une
référence de séance, absente de l'archive avant mars-avril 2021 (mesure de
Backend : 489 024 des 631 579 entrées de la XVe). Le correctif est côté données.

## Ce qui attend des données

**« Sur quoi ils ont pris la parole » : codée, et éteinte jusqu'au prochain
run.** La figure arrêtée — une barre par débat, découpée par membre, rangée par
nombre de prises de parole, avec les pastilles de nature de la fiche candidat —
compte des prises de parole. La propriétaire en exclut deux choses, qui ne sont
pas la parole d'un groupe :

- **la présidence de séance** — 20 788 des 39 581 prises de parole comptées à
  Ensemble pour la République en XVIIe législature, soit 53 % ;
- **la parole prononcée comme membre du gouvernement** — 1 139. Un député
  nommé ministre reste membre de son groupe un mois ; ces prises de parole
  tombent toutes dans une période d'appartenance, et la règle des fenêtres
  (`parole-de-groupe-par-appartenance-et-fenetre-1073`) ne peut pas les
  écarter.

Elles sont **retirées par l'interface, sans pastille de rôle**
(`utils/paroleDeGroupe.js`) — du compte comme des extraits qu'on lit en ouvrant
un débat. La présidence se reconnaît à `role_seance`
([`role-de-seance-distingue-1169`](role-de-seance-distingue-1169.md)), la parole
de ministre à `fonction`, par la règle de la fiche candidat, sortie dans
`utils/fonctionGouvernementale.js` pour que le build l'importe aussi.

**Le corpus publié ne porte pas encore `role_seance`** : le champ arrive avec
un run de collecte. Le build écrit donc `rolesPublies` dans
`<groupe>.paroles.json`, vrai dès qu'une intervention du corpus porte la clé ;
tant qu'il est faux, la section garde sa figure d'avant, avec sa phrase, son
pied et son renvoi. **La figure s'allumera d'elle-même au premier build qui
suivra le run** — sur les douze fiches à la fois, y compris pour un groupe
dont aucun membre n'a présidé.

Vérifiée à l'écran le 02/10/2026 sur une **simulation locale, non committée** :
les profils des membres d'Ensemble pour la République et de LIOT (XVIIe),
complétés depuis l'index de collecte en cache par la fonction du schéma. Il
reste à Ensemble pour la République 17 654 prises de parole sur 801 débats ;
le premier, « droit à l'aide à mourir », en compte 1 446 pour 34 membres, là
où le compte brut en donnait 6 819.

Sous un mot recherché ou une période, la section garde sa liste d'avant : c'est
elle que la recherche sait réduire.

**La fin de la note d'« En bref ».** La propriétaire a validé « … Empreinte
politique établit ce lien **en comparant leurs membres** ». La note s'arrêtait à
« établit ce lien. » tant que la table des liens était écrite à la main ; elle
porte sa fin depuis le 03/10/2026, le run calculant le rattachement
([`lien-etabli-par-comparaison-1168`](lien-etabli-par-comparaison-1168.md)).

## Ce que la mesure a corrigé en route

- **« 41 pages publiées »**, que le retour annonçait et que
  [`retour-ux-sur-les-fiches-groupe`](retour-ux-sur-les-fiches-groupe.md) dit
  ne pas avoir retrouvé : 12 lignées et les 29 groupes qui les composaient ce
  jour-là font 41. **Hypothèse, pas un fait établi.**
- **Trois collisions de palette** consignées côté candidat : quatre, avec
  « Finances » et le sarcelle du Sénat.
- **« La présidence pèse 35 % »** de la parole d'Ensemble pour la République,
  mesuré d'abord sur une seule formule et une seule personne : **53 %**, une
  fois chaque prise de parole rapprochée du libellé de l'orateur dans l'index
  de collecte (20 788 sur 39 581).
- **Un contrôle qui mentait** : le premier script qui comptait les segments
  invisibles de la barre des amendements jugeait la variante à segments
  jointifs sur un critère fait pour l'autre. Corrigé avant publication de la
  maquette ; les chiffres de ce fichier sont ceux d'après.
- **L'écart « motions de censure »** — 34 membres dans l'agrégat du groupe, 26
  dans les extraits — avait été attribué à un intitulé différent. **C'était
  faux** : l'intitulé est le même. L'écart est réel et non expliqué.

## Ce que ce fichier rend caduc

| Dans | Ce qui ne vaut plus |
| --- | --- |
| [`carres-des-textes-et-couleurs-des-commissions`](carres-des-textes-et-couleurs-des-commissions.md) | Les huit teintes, et « la fiche de groupe garde la cascade » |
| [`versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat`](versant-europeen-et-ecarts-de-la-revue-ux-fiche-candidat.md) | « La fiche candidat est livrée avec la palette actuelle » : la palette commune est faite ; et la collision comptée à trois |
| [`reponse-au-retour-ux-fiche-candidat`](reponse-au-retour-ux-fiche-candidat.md) | La note de la carte des amendements, et la lecture stricte de sa règle 1 |
| [`fiche-de-lignee-ui-329`](fiche-de-lignee-ui-329.md) | La liste des noms en colonnes sous « Qui sont-ils », la cascade des textes portés, les renvois en pied |

## Ce qui reste ouvert

- **Le volet gouvernement** de la revue, à ouvrir sur le signal de la
  propriétaire.
- **Le téléphone** : mesuré sans débordement, jamais regardé figure par figure.
- **Côté données**, relevé en maquettant et non instruit ici : sur Écologie
  Démocratie Solidarité, deux lignes « Socialistes » dans « Avec qui ils
  votent », 49 textes comparés sur 59 datés hors de la période du groupe, et
  25 445 amendements pour 17 personnes en cinq mois.
