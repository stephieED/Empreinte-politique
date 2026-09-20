<a id="paroles-par-periode-328"></a>

# « Ce qu'il a dit » publie les mots, et les range par période politique (#328) (2026-09-09)

`2026-09-09`

> **En bref** — la section publiait **quatre listes de totaux de carrière** et un paragraphe de méthode : elle disait comment on sait, jamais ce qui a été dit, alors que le corpus porte **16 188 verbatims** du compte rendu pour 21 725 interventions (10 des 27 candidats déclarés) ; elle devient **période politique → nature → sujet → le fil**, avec le **même découpage que « Ce qu'il a voté » par construction** — `parolesParPeriode.js` appelle `bancALaDate` et `gouvernementALaDate` de `votesParPeriode.js`, deux sections qui découpent le temps pareil le faisant au même endroit ; **le fil reste fermé tant qu'aucun sujet n'est choisi**, non pour la longueur mais parce que la première phrase d'une liste ouverte est de fait une phrase mise en avant (§2 règle 1), et une fois ouvert il publie **toutes** les interventions du sujet, dans l'ordre ; **le sujet ne se lit pas au même niveau selon le type** — l'ordre du jour est un chemin « racine › étape › article » dont la grammaire change : une seule racine couvre **2 885 des 3 660** questions au gouvernement (« Questions au Gouvernement », un créneau de séance) quand ses 756 feuilles sont « Réforme des retraites » ou « Affaire Benalla », et c'est l'inverse sur l'examen d'un texte (105 racines qui nomment des textes, feuilles à « Suspension et reprise de la séance ») — **lire un niveau du chemin n'est pas rapprocher deux libellés** (#639) : « Motion de censure » et « Motions de censure » restent deux entrées ; **deux échelles, toutes deux nommées** — plafond de la fiche sur une période (un filtre retire de la masse, il ne redimensionne pas), plafond de l'ensemble sur « toutes les périodes », que le libellé déclare non comparable ; **`format` n'est jamais publié** bien que disponible sur 16 242 lignes, parce que c'est **notre** déduction (seuil de cinquante mots dans `parse_syceron.py`) et non un fait du compte rendu ; **la navigation devient partagée** (`NavigationPeriodes`) à la demande de la propriétaire, ce qui sort l'écouteur clavier de `window` (à deux sections, une flèche déplaçait les deux) et corrige un défaut livré — les deux flèches désactivées écrivaient « début de la période couverte », faux à droite ; **ce qui part** : le régime de qualité en pavé, `interventionsParNature`, la liste des fonctions, le bloc des questions au gouvernement ; **ce qui reste** : `regimeQualiteOrateur` et `directionQuestionsGouvernement`, que « En bref » consomme, et le raisonnement, passé en méthodologie sous l'ancre `#interventions` ; **les trous sont publiés** — 17 738/21 725 intitulés, 16 188 verbatims, 6 447 qualités, 264 sans date exploitable, et **5 483 en régime `theme_seul`** (Ruffin, Faure, Brun entiers), déclaré sous chaque entrée. 31 tests neufs, suite complète à 4 266, 0 échec.

## Le contexte

La section publiait quatre listes de totaux de carrière et un paragraphe de
méthode : combien d'interventions, de quelle nature, sous quel régime la source
publie la qualité de l'orateur, et sur quels sujets portaient les questions au
gouvernement. Elle disait **comment on sait**, et jamais **ce qui a été dit** —
alors que le corpus porte **16 188 verbatims** du compte rendu intégral pour
**21 725 interventions** collectées, sur **10 des 27 candidats déclarés**.

Le paragraphe le plus long expliquait le régime de qualité. C'était la garantie
en tête et le fait nulle part.

## La décision

La section devient, du plus large au plus fin : **période politique → nature de
l'intervention → sujet à l'ordre du jour → le fil**. Les interventions
elles-mêmes sont publiées, avec leur date, leur nature, leur qualité quand elle
existe, leur verbatim et leur source.

Le découpage est **le même que « Ce qu'il a voté »** — une nouvelle période dès
que le banc ou le gouvernement en place change — et il l'est *par construction* :
`parolesParPeriode.js` appelle `bancALaDate` et `gouvernementALaDate` de
`votesParPeriode.js`. Deux sections qui découpent le temps pareil doivent le
faire au même endroit.

### Le fil est fermé tant qu'aucun sujet n'est choisi

Ouvrir 3 963 interventions d'emblée, c'est publier un mur où le lecteur ne
cherche rien. Ce n'est pas le motif principal : **la première phrase d'une liste
ouverte est, de fait, une phrase mise en avant**, et rien ne nous autorise à
choisir laquelle (§2 règle 1). Fermée, la section ne choisit plus à la place du
lecteur ; ouverte sur un sujet, elle publie **toutes** les interventions de ce
sujet, dans l'ordre, sans en distinguer aucune.

### Le sujet ne se lit pas au même niveau selon le type

L'Assemblée écrit son ordre du jour en **chemin** — « racine › étape › article »
— et la grammaire de ce chemin change avec le type d'intervention.

| Type | Intitulés | Racines | Feuilles |
| --- | ---: | ---: | ---: |
| Question au gouvernement | 3 660 | 74 | 756 |
| Débat en séance | 8 321 | 384 | 410 |
| Examen d'un texte | 4 453 | 105 | 328 |
| Motion de censure | 401 | 2 | 6 |

Les nombres ne tranchent pas, leur **contenu** si. Sur les questions, une seule
racine — « Questions au Gouvernement » — couvre **2 885 des 3 660** intitulés :
c'est un créneau de séance, pas un sujet, et les feuilles sont « Réforme des
retraites » (240) ou « Affaire Benalla » (100). Sur l'examen d'un texte, c'est
l'inverse : les racines nomment des textes, les feuilles sont « Suspension et
reprise de la séance » (444) ou « Après l'article 2 (suite) » (293).

Le niveau se choisit donc **par type**. C'est **lire** la structure que la
source pose, et non rapprocher deux libellés voisins, qui reste proscrit
([`regrouper-nest-pas-joindre-639`](regrouper-nest-pas-joindre-639.md)) : deux
racines différentes ne se rejoignent jamais, et « Motion de censure » (390) et
« Motions de censure » (11) restent **deux** entrées.

C'est aussi ce qui explique pourquoi l'ancienne section paraissait plus
parlante sur un point : elle ne publiait de sujets **que** sur les questions au
gouvernement (`directionQuestionsGouvernement`), c'est-à-dire précisément là où
la feuille en porte un. Elle ne faisait rien des 17 800 autres interventions.

### Deux échelles, toutes deux nommées

Sur **une** période, le plafond des barres est celui du plus gros couple
(période, sujet) de la fiche : une barre se compare alors d'une période à
l'autre, et un filtre retire de la masse sans redimensionner — la règle déjà
posée sur les votes. Sur **toutes** les périodes, ce plafond serait dépassé par
le premier sujet cumulé ; l'échelle devient celle de l'ensemble, et le libellé
l'écrit : « échelle propre à l'ensemble, non comparable à celle d'une période ».
Une échelle qui changerait sans le dire serait le seul vrai défaut.

Les **compteurs**, eux, suivent la sélection : chaque facette est comptée sous
l'autre. C'est ce qui en fait le dénominateur de ce qu'on lit, et non un
palmarès (§2 règle 7).

## Ce que la vue refuse de faire

- **Publier `format`.** « Réaction courte » / « prise de parole développée » est
  disponible sur 16 242 lignes, et c'est **notre** déduction : un seuil de
  cinquante mots dans `src/parse_syceron.py::_infer_format`, jamais un fait du
  compte rendu. Le publier ferait passer un choix d'implémentation pour une
  donnée. `test_le_seuil_de_format_est_bien_une_deduction_du_depot` tombera le
  jour où la source publierait elle-même ce champ, ce qui changerait la règle.
- **Dessiner une densité par jour de séance.** Un creux s'y lirait comme une
  absence individuelle, que la source ne publie pas et nous jamais (§2 règle 3).
- **Totaliser une carrière.** Comme pour les votes : une intervention portée
  depuis le banc du gouvernement et une intervention portée depuis les bancs ne
  se comptent pas dans la même unité.
- **Combler le silence de la qualité.** Le compte rendu ne publie `fonction` que
  pour une fonction particulière — ministre, rapporteur —, sur 6 447 des 21 725
  interventions. Lire ce silence comme « cette personne parlait comme député »
  serait notre inférence ; la fiche écrit la qualité quand elle existe, et rien
  quand elle n'existe pas.

## Ce que la section publie de ses propres trous

Sous la figure, avec leurs dénominateurs : **17 738 / 21 725** portent un
intitulé officiel, **16 188** le verbatim, **6 447** la qualité de l'orateur, et
**264** ne portent pas de date exploitable — celles-là restent hors du
découpage, parce que sans date ni le banc ni le gouvernement ne se lisent.

**5 483 relèvent du régime de collecte `theme_seul`** (#657) : la date, la
nature et le thème, et rien d'autre. Trois candidats entiers — Ruffin (3 279),
Faure (1 328), Brun (876) —, sans un verbatim, et **3 760** de ces lignes sans
intitulé. Ce n'est pas une donnée manquante à combler : c'est un régime nommé
par le pipeline, et chaque entrée concernée le dit à l'écran, sous les mots
« ce n'est pas un silence de la personne ».

## La navigation par période devient partagée

La propriétaire a demandé le 09/09/2026 que les deux sections « se manœuvrent à
l'identique ». Deux copies du même mécanisme, ce sont deux mécanismes qui
divergeront : `NavigationPeriodes.jsx` / `.css` sort de `VotesParPeriode`, qui
l'importe désormais. Trois conséquences, toutes voulues :

1. **L'écouteur clavier n'est plus posé sur `window`.** Tant qu'une seule
   section naviguait, un écouteur global marchait ; à deux, une flèche déplaçait
   les deux sections à la fois. Il est porté par le conteneur et n'agit que si
   le focus est dans la navigation — l'état où l'on vient de cliquer une flèche
   ou un segment.
2. **Les deux flèches désactivées ne disent plus la même chose.**
   `VotesParPeriode.jsx` écrivait « début de la période couverte » des deux
   côtés ; à droite, on est au bout le plus **récent**. Défaut corrigé pour les
   deux sections.
3. **« Toutes les périodes » est optionnel** (`avecTout`), et « Ce qu'il a voté »
   ne le prend pas : y cumuler deux périodes reformerait le total de carrière
   que cette vue refuse. Sur les paroles, la propriétaire l'a demandé, et
   l'échelle le déclare.

La fiche s'ouvre sur la **période la plus récente**, et non sur la première.

## Ce qui part, et ce qui reste

**Part** : le bloc du régime de qualité, la liste des natures toutes périodes
confondues (`interventionsParNature`, dont le seul lecteur disparaissait), la
liste des fonctions, le bloc des questions au gouvernement.

**Reste** : `regimeQualiteOrateur` et `directionQuestionsGouvernement`, que
« En bref » consomme — le fait qu'une question au gouvernement puisse être
**reçue** plutôt que posée est intact —, `TYPES_INTERVENTION`, qui reste la
table de libellés de ce champ et n'a plus qu'un lecteur.

Le raisonnement, lui, ne disparaît pas : il passe dans la page de méthodologie,
sous l'ancre `#interventions` où mène le renvoi. `DESIGN_SYSTEM.md` §7 règle 2 —
« une limite tient en deux mots, une explication en paragraphe » — s'applique à
la figure, pas à la méthodologie.

## L'alternative écartée

**Garder les compteurs et ajouter le fil dessous.** C'était la forme la moins
risquée, et elle a été dessinée : elle laisse en tête de section quatre nombres
dont le lecteur ne peut rien conclure (DESIGN_SYSTEM §7 règle 1), et elle repose
la question à laquelle la vue par période répond — 3 963 interventions
« de Gabriel Attal » ne sont pas une quantité, ce sont neuf situations
politiques différentes.

**Regrouper les sujets en rubriques.** Il n'existe **aucune taxinomie thématique
dans le corpus** : ce sont des intitulés d'ordre du jour, pas huit catégories.
L'Assemblée en publie une, `indexationAN.rubrique`, sur les seules questions
écrites — et la collecte n'en garde aujourd'hui que `analyse`. Elle couvrirait
906 des 21 725 interventions. Sujet ouvert, hors de ce lot.
