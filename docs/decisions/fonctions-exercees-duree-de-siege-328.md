<a id="fonctions-exercees-duree-de-siege-328"></a>

# La section 1 devient « Les fonctions exercées », et son nombre est une durée de siège (#328) — 03/09/2026

`2026-09-03`

> **En bref** — la frise et le détail daté étaient montés **deux fois** sur la même page (le même composant `Frise`, pas une copie), et la section 1 les republiait à quelques centaines de pixels d'écart ; elle ne garde donc que ce que personne d'autre ne montre, et son titre le dit — « Expériences parlementaires » écarté parce qu'un bloc « Organismes extra-parlementaires » l'aurait contredit à l'écran. Le nombre affiché cesse d'être un **compte d'enregistrements** (27 entrées pour un siège continu de 5 ans 10 mois chez `jerome-guedj`, contre 4 entrées pour 2 jours à la commission des lois — le compte ne distingue pas les deux) et devient une **durée de siège en UNION d'intervalles**, jamais une somme : la fusion additive a laissé des doublons littéraux, et la somme donnerait 9,5 ans là où il y en a 5,8. Chaque catégorie montre ses **trois plus longues**, et une seule peut porter la marque — elle dépasse la **moitié du temps de mandat**, test de majorité sans constante, avec pour dénominateur l'**union des sièges électifs**, un vrai tout puisqu'on ne siège pas deux fois à la fois (§2 règle 7) ; le total des fonctions n'en serait pas un, treize groupes d'amitié simultanés faisant 33 ans sur une carrière de 19. Elle **sait se taire** : 4 fois sur les 13 blocs des deux profils de référence. La marque est **sans teinte** — aucune n'était libre, le jaune étant pris par la sélection, l'action et le badge de source, le vert et le rouge par les positions de vote, le bleu et le bronze par les institutions — donc un filet d'encre, lisible en niveaux de gris sans pictogramme de secours. Le **rôle** ne s'affiche que lorsqu'il distingue (`Membre` couvre 90,7 % des mandats de commission), ce qui fait apparaître que Guedj préside le groupe d'études « Longévité et adaptation de la société au vieillissement ». Les intitulés se coupent à **deux lignes** — une seule perdait trop sur des libellés de 200 caractères — et le « … » est un vrai bouton, posé seulement sur ce qui déborde. Le critère d'en-tête part, la règle descend en pied de section avec son lien vers la méthodologie. Deux défauts de collecte que la liste à plat noyait sont devenus visibles et ouverts à part : #729 et #730.

Révision de la section 1 de la fiche candidat, arbitrée en maquette avec la
propriétaire le 03/09/2026 sur une réplique du rendu réel
([artifact `c5168437`](https://claude.ai/code/artifact/c5168437-1f95-4853-afa7-ce350288670a)),
puis transposée ici. Les mesures portent sur les **641 profils pivot publiés**
de `aef8b791` — 13 `candidat_declare` et 628 `roster_groupe` — et sur les **12
fiches de groupe** ; jamais sur les 481 d'avant #708, qui mélangeraient deux
états du corpus.

## 1. La frise et la liste datée quittent la section

Le composant `Frise` était monté **deux fois** sur la même page : une fois par
`GrandsChiffres`, où il est l'ossature des colonnes, et une fois par la
section 1. Même bande, même légende de sept motifs, même pli « Détails du
parcours », à quelques centaines de pixels d'écart, sur 9 ou 10 des 13 fiches.
Ce n'était pas une copie — c'était le même composant, ce qui rendait la
redondance invisible à la relecture du code.

La frise reste en tête, la liste datée reste dans son pli, et la section 1 ne
garde que ce que personne d'autre ne montre. **Le titre suit** : « Le parcours »
ne décrivait plus rien, puisque le parcours est au-dessus.

**« Expériences parlementaires » a été proposé et écarté** : la section porte un
bloc « Organismes extra-parlementaires » — 5 intitulés chez Jérôme Guedj, dont
le Conseil d'administration du Centre Pompidou — et le titre se serait contredit
à l'écran. « Les fonctions exercées » est le vocabulaire que le code employait
déjà (`fonctionsExercees`, `CATEGORIES_FONCTIONS`).

Le bloc de tête est renommé **« En bref »** au passage, au format d'un titre de
section. Sans numéro : le numéroter en ferait la section 1 et décalerait les
sept suivantes, ce qui n'a pas été décidé.

## 2. Le nombre affiché est une durée, pas un compte

C'est la décision qui porte tout le reste.

La carte affichait un **compte d'enregistrements** : « Commission des affaires
sociales · 27 ». Or la source réécrit un même siège à chaque changement de
composition. Mesuré sur `jerome-guedj` :

| Intitulé | Enregistrements | Dont d'un jour | Durée réelle |
| --- | ---: | ---: | ---: |
| Commission des affaires sociales | 27 | **0** | **5 ans 10 mois** |
| Commission des lois | 4 | **4** | **2 jours** |

Le compte ne distingue pas un siège continu de quatre passages d'un jour ; la
durée si. C'est la confusion que #656 a séparée sur les fiches de groupe — « y
siège » n'est pas « y est passé » — vue depuis la fiche candidat.

**La durée est une UNION d'intervalles, jamais une somme.** La fusion additive a
laissé des doublons littéraux (même début, fin décalée d'un jour) : la somme
donne 9,5 ans là où il y en a 5,8. Un mandat sans `debut` n'est comptable à
aucune date : il sort du calcul, il n'y entre pas comme un zéro (§2 règle 5). Un
mandat ouvert court jusqu'à aujourd'hui, jamais jusqu'à la borne `9999-12-31` du
schéma.

## 3. Ce qui ressort dépasse la moitié du temps de mandat

Chaque catégorie montre ses **trois plus longues** — toujours trois, jamais une
seule : un bloc à une grande ligne et un autre à trois petites déséquilibraient
la carte sans que la donnée le justifie. Une seule ligne peut porter la
**marque**, et c'est un fait, pas un seuil choisi : la personne y a passé plus de
la moitié de son temps de mandat. C'est le test de majorité que #328 avait déjà
retenu pour les amendements (« ce dossier porte plus que tous les autres
réunis »).

**Le dénominateur est l'union des sièges électifs, et ce choix est le cœur de la
règle.** On ne siège pas deux fois à la fois : c'est un vrai tout, donc un
num/dénom publiable (§2 règle 7). Le total des fonctions n'en serait pas un —
on appartient à treize groupes d'amitié simultanément, et leur somme fait
**33 ans sur une carrière de 19**.

**Elle sait se taire**, et c'est ce qui la rend utile. Mesurée sur les 13 blocs
des deux profils de référence, elle parle **4 fois** :

| | Bloc | Part du mandat | Verdict |
| --- | --- | ---: | --- |
| Guedj | Commissions | 53 % | marquée |
| Guedj | Groupes d'amitié | 42 % | se tait |
| Guedj | Groupes d'études | 27 % | se tait |
| Guedj | Commissions d'enquête | 4 % | se tait |
| Attal | Commissions | 78 % | marquée |
| Attal | Groupes d'amitié | 73 % | marquée |
| Attal | Délégations | 51 % | marquée |
| Attal | Groupes d'études | 21 % | se tait |

Une règle qui ne peut pas se taire ne dit rien quand elle parle (#326, règle 5).

La marque va **nécessairement** à la plus longue : dépasser la moitié du tout
interdit qu'une autre le fasse aussi. Elle n'est donc pas choisie, elle est
structurellement unique.

## 4. La marque est sans teinte, et aucune couleur n'était libre

Le jaune signal est pris par la sélection, l'action et le badge « source
vérifiée » ; le vert et le rouge par les positions de vote (`DESIGN_SYSTEM` §2) ;
le bleu `#2E4A7D` et le bronze `#8A6512` par les institutions dans la frise. En
introduire une quatrième aurait dilué les trois autres — et la charte pose que le
jaune n'indique **jamais** un jugement.

La marque est donc un **filet d'encre et le lavis `#fbfaf8`**, celui des puces.
C'est aussi ce qui la rend lisible en niveaux de gris et sous daltonisme sans la
doubler d'un pictogramme : elle ne repose sur aucune perception chromatique.

**Deux états, jamais une graduation** : une ligne porte la marque ou non, et rien
ne hiérarchise les deux autres entre elles.

## 5. Le rôle ne s'affiche que lorsqu'il distingue

`Membre` couvre **90,7 %** des 14 128 mandats de commission du corpus, et 203 des
225 des 13 candidats déclarés. L'écrire sur neuf lignes sur dix serait un mot
dont le lecteur ne tire rien (#326, règle 1). Ce qui s'affiche est ce qui
distingue — et c'est ce qui rend la section lisible : Jérôme Guedj est
**président du groupe d'études « Longévité et adaptation de la société au
vieillissement »**, vice-président de trois autres. C'est son sujet, et rien ne
le disait.

Le rôle prend l'encre et le gras du libellé : en teinte sourde, il passait
inaperçu. Et il vit **hors du texte coupable** — sur une ligne tronquée, il
serait perdu précisément là où l'intitulé est long.

⚠️ **La casse n'est pas normalisée à la source** : `Membre`/`membre`,
`Vice-Président`/`vice-président`, `vice-présidente`. 48 des 225 mandats de
commission des 13 candidats sont en bas de casse. On uniformise **à l'affichage
seulement** : la donnée n'est pas touchée, et le défaut reste lisible pour qui
l'ouvre. Le dépôt a déjà tranché ce point côté fiches de groupe
(`normalisation-fonction-mandats-agreges`) ; le pipeline reste à aligner.

## 6. Les intitulés se coupent à deux lignes, et les points sont un vrai bouton

Une seule ligne perdait trop : les commissions d'enquête portent des intitulés de
plus de 200 caractères. À deux lignes, **plus aucun ne déborde en pleine
largeur** — c'est en écran étroit que la coupe sert, et elle y sert vraiment.

Pas de `-webkit-line-clamp` ni de `text-overflow` : ils peignent leurs propres
points de suspension, et on en aurait deux avec le bouton. La coupe est franche,
le « … » vient dessous.

Le « … » est un **vrai bouton** — atteignable au clavier, portant
`aria-expanded` — et il n'apparaît **que sur ce qui déborde vraiment** : poser
l'affordance partout apprendrait au lecteur à ne plus cliquer. La mesure se
refait au redimensionnement, la place disponible décidant, pas le texte.

## 7. La règle est documentée en pied de section, et le critère d'en-tête part

Le critère annonçait la section avant qu'on ait rien lu — et il décrivait la
frise, qui n'y est plus. Ce qui devait y survivre descend en petites lignes,
après le contenu, avec un lien vers la méthodologie :

> Chaque catégorie montre ses trois fonctions les plus longues. Un filet marque
> celle qui dépasse la moitié du temps de mandat, quand il y en a une. Le rôle
> n'est précisé que lorsqu'il n'est pas celui de membre. **Méthodologie →**

Le pied n'a pas de `max-width` : il s'aligne sur la carte qui le précède, sinon
les deux bords gauches se répondent et le bord droit part tout seul. C'est un
compromis assumé — 82 caractères était la longueur de ligne confortable, on monte
à ~140 — tenable sur trois phrases courtes, à rediscuter si le pied s'allonge.

## 8. La forme rendue a deux lecteurs, et le second n'est pas une vue

`fonctionsExercees` rendait un **tableau** de blocs `{cle, titre, total, items[]}` ;
elle rend un objet `{mandat, blocs[]}`. La vue a suivi. Le second lecteur n'a pas
suivi, et rien ne l'a signalé : `vivierDesPoints` lit la même forme pour un point
**dormant** — « L'essentiel » a emporté le rendu du vivier, pas son calcul, et
`buildCandidateView` appelle `essentiel()` sans condition. `(fonctions || []).find(…)`
sur un objet lève `find is not a function` : **toute la fiche disparaît, pour les
treize candidats**. Mesuré en rejouant `buildCandidateView` sous Node sur les
profils publiés — la suite, elle, était au vert, parce qu'aucun de ses 3 720 tests
n'exécute une ligne de JS.

Le point est réparé **en durée**, pas en compte : le remettre debout sur
`items[0].n` aurait laissé dans le code la mesure que §2 vient d'écarter de la
page. Il lit `blocs[].montrees`, déjà triées par durée, et l'adaptateur lui passe
la forme **entière** — le dénominateur du point est le temps de mandat, qui vit
sur `mandat`, et le défaire obligerait l'adaptateur à refaire une mesure.

Trois tests le verrouillent, mutations vérifiées. Ils ne remplacent pas ce qui
manque : **un consommateur qui n'est pas une vue ne se voit pas en relisant la
page**, et le dépôt n'a aucun moyen de l'exécuter.

## Ce que ce lot a révélé, et qui n'est pas de son ressort

Afficher le rôle et ne montrer que trois lignes a rendu lisibles deux défauts de
collecte que la liste à plat noyait. **Deux issues ouvertes, aucune corrigée
ici** — le défaut est à la collecte, où la catégorie est écrite :

- **#729** — le même organe rangé sous deux catégories selon le profil : 25
  libellés, 542 mandats, et **11 des 12 fiches de groupe** publient des groupes
  d'études en commissions ou en amitiés. Chez Guedj, les rangs 2 et 3 des
  « Groupes d'amitié » sont deux groupes d'études.
- **#730** — huit mandats ministériels publiés comme des commissions, tous sous
  le libellé `Gouvernement`, **aucun n'ayant de jumeau correct** dans
  `fonction_gouvernementale`.

Filtrer ces entrées côté vue serait la classification par libellé que
`regrouper-nest-pas-joindre-639` interdit et que #718 écarte déjà.

## Alternatives écartées

| Écartée | Pourquoi |
| --- | --- |
| Garder le compte d'enregistrements et corriger seulement l'affichage | Le compte est faux dans son principe, pas dans sa présentation : 27 et 4 ne mesurent pas la même chose selon le profil. |
| « Plus que toutes les autres réunies » comme test de saillance | Écarté après mesure : les fonctions sont **simultanées**, leur somme n'est le tout de rien. Sur les groupes d'amitié de Guedj elle vaut 33 ans pour 19 ans de carrière. |
| Un percentile, ou un multiple du suivant | Toute constante serait un arbitrage éditorial déguisé en mesure — le défaut du P90 déjà écarté par `les-grands-chiffres-fiche-candidat-328`. |
| Une teinte pour la marque | Aucune n'était libre sans en diluer une autre. Le jaune en filet seul reste possible et n'a pas été retenu de ma propre initiative. |
| Un pictogramme doublant la marque | La marque n'est que de l'encre et du blanc cassé : elle passe déjà en niveaux de gris. Le doubler serait le texte explicatif que #326 règle 2 fait retirer. |
| Couper les intitulés à une ligne | Essayé, puis écarté à l'écran : trop de sens perdu sur des intitulés de 200 caractères. |

## Ce qui n'est pas vérifié

- **Aucun harnais JS dans le dépôt.** Les 23 tests de
  `tests/test_fonctions_exercees_328.py` lisent le **code exécuté**, commentaires
  retirés ; **huit mutations** ont été vérifiées échouantes. Ils ne couvrent ni
  la mise en page rendue, ni le contraste, ni le parcours clavier.
- Le rendu a été relu **sur une réplique publiée**, aux trois largeurs, sur les
  deux profils de référence — pas sur l'application elle-même. C'est cette
  omission qui a laissé passer le défaut du §8 : la réplique rendait la section,
  jamais la fiche, et le point mort vivait ailleurs sur la fiche. L'application
  a depuis été construite et servie, et les huit profils de référence rendus par
  ses propres composants.
- Les règles ont été **rejouées en Node sur les deux profils pivot publiés** et
  reproduisent la maquette à l'unité : 1 bloc marqué sur 6 chez Guedj, 3 sur 7
  chez Attal, mêmes durées, mêmes rôles.
