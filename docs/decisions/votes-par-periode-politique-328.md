<a id="votes-par-periode-politique-328"></a>

# « Ce qu'il a voté » range les positions par période politique, et ne totalise plus une carrière (#328) (2026-09-08)

`2026-09-08`

> **En bref** — la section publiait trois nombres justes et muets (« 123 pour, 34 contre, 11 abstentions »), alors qu'**un même vote n'a pas le même sens selon d'où il est émis** : 35 pour / 1 contre depuis la majorité en 2012-2014 chez Guedj, 16 pour / 6 contre depuis l'opposition en 2022-2023 — additionner détruit exactement ce que la répartition portait ; les positions de dernière lecture se découpent donc en **périodes politiques**, une nouvelle dès que le **banc** ou le **gouvernement en place** change, avec une barre divergente par matière et jamais un total par-dessus ; **deux repères parce qu'aucun ne couvre seul**, et leurs trous ne sont pas aux mêmes endroits — de 2012 à 2017 l'Assemblée publie le banc et le corpus n'a aucune fiche de gouvernement, depuis 2024 c'est l'inverse : banc **719 / 1 160**, gouvernement **916 / 1 160**, **banc ou gouvernement 1 160 / 1 160**, quand le banc seul en laissait **441 dehors** (dont les 132 positions de Marine Le Pen sur la XVIIe) ; cinq faits qualifient chaque vote, chacun de sa source — matière **711 / 1 160** (commission saisie au fond du dossier), origine **1 160 / 1 160** (mot ancré en tête de l'intitulé officiel, **pas** un rapprochement de libellés — #639), sort du texte **722 / 1 160** (`scrutins_dossiers.json`, #758, désormais servi au site) ; **quatre refus** : combler un repère manquant par celui de la période voisine (le titre écrit « banc non publié »), recalculer l'échelle sous un filtre — `porteeCommune` se calcule sur toutes les périodes **sans garde**, sinon 2 textes paraissent aussi larges que 37 et cocher un filtre n'apprend plus rien —, déduire la matière d'un intitulé, et totaliser par-dessus les périodes ; **l'encodage de l'origine a été arbitré sur maquette**, quatre variantes dessinées sur les mêmes données — rayure écartée (elle éclaircit la teinte d'un tiers et **disparaît sur un segment d'un ou deux textes**, donc sur les cas rares), creux seul (pèse trop peu), deux rangées (barres deux fois plus fines), voile seul (se lit « estimé ») —, retenu **voile 26 % + filet pleine saturation**, dont les défauts s'annulent ; `votesDuProfil` rend désormais `retenus` pour que le repli sur la dernière lecture n'ait **qu'une** implémentation (#711, AGENTS.md §6) ; le « pourquoi » des deux règles publiées passe dans la méthodologie — **leurs phrases restent sur la fiche**, parce que #711 est né d'une méthodologie qui annonçait la règle quand rien ne l'appliquait ; **reste ouvert** : le groupe majoritaire en face n'est pas nommé (#770), l'explication de vote ne se joint pas (214 entrées, 0 clé de dossier), et 449 positions restent en « matière non établie » — absence de source, jamais absence de commission, et la section l'écrit. 25 tests neufs, suite complète à 4 099, 0 échec.

## Le contexte

La section publiait trois nombres : « 123 pour, 34 contre, 11 abstentions ».
Les trois sont justes, sourcés, repliés sur la dernière lecture depuis #711 —
et ils ne disent rien.

Le motif tient en une phrase : **un même vote n'a pas le même sens selon d'où
il est émis.** Depuis la majorité, voter contre n'arrive presque jamais ; depuis
l'opposition, c'est le vote *pour* qui se remarque. Mesuré sur les 168 positions
de dernière lecture de Jérôme Guedj : 35 pour et 1 contre sur ses 37 votes de
2012-2014, depuis la majorité ; 16 pour et 6 contre sur ses 36 votes de
2022-2023, depuis l'opposition. Additionner les deux périodes détruit
exactement l'information que la répartition portait.

La demande de la propriétaire, le 06/09/2026 : voir **ce qui ressort** des
textes pour lesquels la personne a voté pour, contre, ou s'est abstenue ; voir
**si ces textes sont finalement passés** ; et pouvoir le parcourir.

## La décision

Les positions de dernière lecture sont découpées en **périodes politiques** —
une nouvelle dès que le **banc** ou le **gouvernement en place** change — et
jamais totalisées par-dessus. Chaque période porte une barre divergente par
matière : contre à gauche de l'axe, abstention puis pour à droite.

Cinq faits qualifient chaque vote, **chacun de sa source, aucun deviné** :

| Fait | Source | Couverture mesurée |
| --- | --- | ---: |
| Banc | `mandats[].position_dans_hemicycle`, refusé sans `source_url` | 719 / 1 160 |
| Gouvernement en place | dates des fiches de gouvernement, via le manifeste | 916 / 1 160 |
| **Banc OU gouvernement** | — | **1 160 / 1 160** |
| Matière | commission saisie au fond du dossier (`commissions_dossiers.json`) | 711 / 1 160 |
| Origine du texte | intitulé officiel du scrutin | 1 160 / 1 160 |
| Sort final du texte | statut du dossier (`scrutins_dossiers.json`, #758) | 722 / 1 160 |

Mesuré au commit de données `fef9de43` sur les positions de dernière lecture des
13 candidats déclarés — dont 9 ont au moins un vote publié.

### Pourquoi deux repères, et pas un

Parce qu'aucun des deux ne couvre le corpus, et que **leurs trous ne sont pas
aux mêmes endroits** : de 2012 à 2017, l'Assemblée publie le banc et le corpus
ne porte aucune fiche de gouvernement ; depuis 2024, elle ne déclare plus le
banc alors que les gouvernements se succèdent. Édouard Philippe et Xavier
Bertrand n'ont **que** le banc (74 et 59 positions) ; Marine Le Pen n'a le banc
que sur 24 de ses 132 positions, et le gouvernement sur les 132.

Ensemble, ils couvrent **tout**. C'est le seul découpage mesuré qui ne laisse
aucune position sans repère — et c'est la raison de le préférer au banc seul,
qui en laissait 441 dehors.

### Ce que la vue refuse de faire

- **Combler un repère manquant par celui de la période voisine.** Le titre écrit
  « Banc non publié · gouvernement Philippe II ». Un banc non déclaré par la
  source et une absence de banc sont deux faits différents (§2 règle 5).
- **Recalculer l'échelle sous un filtre.** `porteeCommune` se calcule sur toutes
  les périodes, sans garde. Une échelle qui suit le filtre ferait paraître
  2 textes parlementaires aussi larges que 37 gouvernementaux : cocher un filtre
  n'apprendrait plus rien, et deux périodes cesseraient de se comparer. Un
  filtre **retire de la masse**, il ne redimensionne pas.
- **Déduire la matière d'un intitulé.** Elle vient du dossier ou elle est « non
  établie ». Un rapprochement de libellés est proscrit
  ([`regrouper-nest-pas-joindre-639`](regrouper-nest-pas-joindre-639.md)).
- **Compter quoi que ce soit par-dessus les périodes.** Aucun total de carrière,
  aucun taux : ce serait le score que §2 règle 1 interdit.

### L'origine du texte se lit dans l'intitulé, et c'est une lecture, pas une jointure

L'Assemblée écrit elle-même la catégorie juridique en tête de l'intitulé du
scrutin : « projet de loi » désigne un texte du gouvernement, « proposition de
loi » ou « proposition de résolution » un texte du Parlement. Le motif est
**ancré en tête**, après les seuls articles initiaux, jamais cherché en
sous-chaîne — « … modifiant la proposition de loi … » ne dit rien de l'origine
du texte voté.

Mesuré : **925 / 925** votes sur l'ensemble d'un texte classés, **697 / 697**
dernières lectures. Le troisième état — origine non établie — reste dans le code
malgré cette couverture de 100 % : une couverture à une date n'est pas une
garantie de schéma, et ranger un texte au Parlement par défaut inventerait une
initiative parlementaire.

## L'encodage : l'origine se dit par la forme, la position par la couleur

La barre porte deux informations. La couleur est prise par la **position** ; il
restait à dire l'**origine** sans la brouiller. Quatre encodages ont été dessinés
sur les mêmes données réelles, à la même échelle, et comparés à l'œil :

| Encodage | Variable visuelle | Pourquoi écarté |
| --- | --- | --- |
| Rayure sur la couleur | texture | Éclaircit la teinte d'environ un tiers — le vert s'approche du gris de l'abstention — et **disparaît sur un segment d'un ou deux textes**, c'est-à-dire sur les cas rares |
| Creux (fond de page + filet) | forme | Un creux pèse visuellement moins lourd qu'un aplat de même largeur, alors qu'il vaut autant de textes |
| Deux rangées par matière | position | Chaque barre est deux fois plus fine ; les petites matières deviennent des filets et la ligne perd sa silhouette |
| Voile seul (teinte à 34 %) | valeur | Une teinte pâlie se lit comme « estimé » ; et sur l'abstention, déjà grise, elle disparaît |

**Retenu : le voile ET le filet.** Voile de la teinte à 26 % à l'intérieur
(32 % en thème sombre), filet à pleine saturation autour. Les deux derniers
défauts s'annulent : le voile rend au segment le poids que le creux lui
retirait, le filet garde l'arête là où le voile seul s'effaçait. Et la teinte de
position n'est **jamais** altérée — c'était l'objection de fond contre la rayure.

## Ce qui a bougé ailleurs

- **`votesDuProfil` rend `retenus`**, la liste et non plus son seul décompte. Le
  repli sur la dernière lecture n'a ainsi **qu'une** implémentation, celle de
  `utils/lecture.js` (#711, AGENTS.md §6). La vue par période consomme des votes
  déjà retenus ; elle ne trie aucune lecture.
- **`pivot_data/scrutins_dossiers.json` est servi au site** — 72 Ko, copié par
  `scripts/sync-data.mjs`, chargé par `data/index.js`. C'est ce qui apporte la
  matière et le sort. Son absence est **déclarée** (`rattachementDisponible`) :
  un index illisible n'est pas la même chose qu'un texte sans commission saisie
  au fond (même distinction que #510 pour l'index des scrutins).
- **Les deux règles publiées sous la figure perdent leur « pourquoi », pas leur
  phrase.** Le raisonnement long — quatre lectures d'un même texte, un code de
  scrutin qui ne sépare pas l'ensemble de l'article — passe dans
  `MethodologyPage`, où mène le renvoi posé sous la figure. Les deux phrases
  restent à côté du chiffre : #711 les y veut, parce que la méthodologie
  annonçait déjà la règle de la dernière lecture à l'époque où **rien ne
  l'appliquait**. La déplacer entièrement rejouerait l'incident.
- **`StaticPage` accepte un `id` de section**, pour que `/methodologie#votes`
  dépose le lecteur devant la règle et non en haut d'une page de dix sections.

## L'alternative écartée

**Découper par banc seul.** C'était la première forme dessinée, et elle est plus
simple à expliquer : majorité / opposition / non déclaré. Elle laissait 441 des
1 160 positions hors de toute période, dont la totalité de celles de Marine Le
Pen entre 2017 et 2022 et les 132 de sa XVIIe législature. Une vue qui perd un
tiers de son corpus au premier repère manquant n'est pas une vue, c'est un
échantillon — et rien à l'écran ne l'aurait dit.

**Découper par législature.** Le repère est complet, mais il n'est pas
politique : la XVIe législature de Jérôme Guedj couvre Borne *et* Attal, deux
majorités et deux contextes de vote. On aurait gagné une couverture et perdu la
raison même du découpage.

## Ce que cette vue ne couvre pas, et qui reste ouvert

- **Le groupe majoritaire en face n'est pas nommé** — la table de référence ne
  couvre ni la XIVe ni la XVe, et la XVIIe n'est pas déclarée par la source
  (#770).
- **L'explication de vote n'est pas jointe.** Les 214 entrées du corpus ne
  portent aucune clé de dossier, et une jointure par date ne couvrirait que 22
  des 769 positions mesurées à l'époque du sondage : ce serait un rapprochement,
  pas une jointure.
- **449 positions restent en « matière non établie ».** C'est une absence de
  source, pas une absence de commission, et la section l'écrit sous la figure.
