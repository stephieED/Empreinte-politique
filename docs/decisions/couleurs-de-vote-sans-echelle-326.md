# Les couleurs de vote ne forment pas une échelle, et « Absent » n'est pas une catégorie (#326) — 31/08/2026

`2026-08-31`

> **En bref** — premier lot d'implémentation de #324, trois arbitrages rendus sur le **rendu d'écran soumis avant toute ligne de code** (§11) ; mesuré au commit de données `245511b4`, les **1 312 951** positions publiées des 481 profils ne prennent que **quatre** valeurs — `contre` 633 551, `pour` 584 692, `abstention` 73 479, `non_votant` 21 229 — et **`absent` n'apparaît jamais**, si bien que les cinq catégories annoncées par l'issue en auraient inventé une : la publier reviendrait à publier une absence comme un fait de vote, c'est-à-dire le taux de présence individuel qu'interdit §2 règle 3 ; `non_votant`, qui n'était PAS dans `VOTE_STYLE`, résolvait sur `undefined` et affichait une pastille sans fond et un libellé vide — une fois sur 8 860 chez les 13 candidats déclarés, donc invisible là, réel sur les fiches de groupe — et se distingue désormais par la **forme** (contour tireté, `color: null`) et jamais par une teinte, le gris neutre étant écarté parce qu'il **est** celui de l'abstention et toute autre teinte reconstruisant l'échelle chaud-froid qu'interdit §2 règle 1 ; le badge dit « Lien de source non publié » et jamais « non vérifié », parce que le premier parle de nous quand le second ferait porter le doute sur les 484 132 amendements, tous issus de l'open data (couverture des liens : scrutins 17 748/17 748, interventions des 13 candidats 16 242/16 242, textes de gouvernement 725/725, textes portés 472/472, mandats 1 915/41 723, amendements 0/484 132) ; `VOTE_STYLE` et `OUTCOME_COLOR` cessent d'être dupliqués dans `CandidateProfile.jsx` et `GroupProfile.jsx` — la « divergence silencieuse » que le `DESIGN_SYSTEM` §2 signalait lui-même — au profit de `src/utils/lecture.js`, qui porte aussi les cinq autres primitives du lot ; faute de runner JS dans le dépôt (`oxlint` seul), les trois arbitrages sont verrouillés par un test Python lisant le **code exécuté**, commentaires retirés, patron de #529 et #530 — ajouter un runner JS est nommé et laissé hors lot.

Premier lot d'implémentation de la refonte #324. Trois arbitrages rendus sur le
**rendu d'écran soumis avant toute ligne de code** — la règle de `AGENTS.md` §11 :
tout ce qu'un humain lira à l'écran se relit avant d'exister, pas après.

## Contexte

Le lot 1 pose les primitives que les lots 2, 3 et 4 appliquent au lieu de les
redéfinir. Deux d'entre elles touchent à ce que la page **affirme** sur une
personne, et pas seulement à son apparence.

`VOTE_STYLE` vivait dupliqué dans `CandidateProfile.jsx` et `GroupProfile.jsx`,
avec **trois** entrées — `pour`, `contre`, `abstention`. Le `DESIGN_SYSTEM.md` §2
signalait lui-même le risque : « à garder synchronisées […] aucun partage de
source actuellement ».

## Ce que la mesure a établi

Les positions publiées, mesurées au commit de données `245511b4` le 31/08/2026,
sur les **481 profils** — 13 `candidat_declare` et 468 `roster_groupe` :

| Position | Corpus (481 profils) | 13 candidats déclarés |
| --- | ---: | ---: |
| `contre` | 633 551 | 4 247 |
| `pour` | 584 692 | 4 089 |
| `abstention` | 73 479 | 523 |
| `non_votant` | 21 229 | **1** |
| **Total** | **1 312 951** | **8 860** |

**`absent` n'apparaît jamais.** Et `non_votant`, absent de `VOTE_STYLE`,
résolvait sur `undefined` : ses 21 229 entrées s'affichaient avec une pastille
sans fond et un libellé vide — un défaut invisible sur les pages de candidat,
où la valeur n'apparaît qu'**une fois sur 8 860**, et bien réel sur les fiches
de groupe.

## Décision

### 1. « Absent » ne devient pas une catégorie de vote

L'issue #326 en annonçait cinq. Il y en a quatre. Deux motifs, et le second
suffirait seul :

- **Aucune source ne la produit** : l'inventer publierait un fait que rien ne
  soutient (§2 règle 2).
- **Publier une absence comme un fait de vote est un taux de présence
  individuel**, que §2 règle 3 interdit sans exception. La catégorie ferait
  exactement ce que le dénominateur interdit fait : transformer une absence en
  information négative sur la personne.

La catégorie n'est donc **pas affichée**, et toute valeur inconnue — `absent`
comprise, si la source en produisait une un jour — tombe sur la forme sans
teinte, jamais sur une couleur.

### 2. `non_votant` se distingue par la forme, jamais par une teinte

Pour, Contre et Abstention sont des positions **exprimées** : elles gardent les
couleurs du `DESIGN_SYSTEM` (`#007A45`, `#E53420`, `#8B8794`). `non_votant` n'en
est pas une : contour tireté, `color: null`.

C'est ce qui empêche les quatre valeurs de se lire comme un dégradé du meilleur
au pire. Une échelle chaud-froid fabriquerait un jugement (§2 règle 1) — et elle
le fabriquerait d'autant plus sûrement que le reste de la page est sobre.

### 3. Le badge dit « Lien de source non publié », jamais « non vérifié »

La couverture des liens de source est réelle et très inégale :

| Objet | Avec lien de source |
| --- | ---: |
| Scrutins | 17 748 / 17 748 |
| Interventions des 13 candidats déclarés | 16 242 / 16 242 |
| Textes des gouvernements | 725 / 725 |
| Textes portés | 472 / 472 |
| Mandats | 1 915 / 41 723 |
| Amendements | 0 / 484 132 |

« Lien de source non publié » parle de **nous** : nous ne publions pas encore
l'adresse. « Non vérifié » ferait porter le doute sur les 484 132 amendements
eux-mêmes, qui viennent tous de l'open data de l'Assemblée nationale — un
jugement sur la donnée là où il n'y a qu'un constat sur la page.

## Alternative écartée

**Donner à `non_votant` une couleur neutre** — le gris `#8B8794`, par exemple.
Écartée parce que ce gris **est** celui de l'abstention : les deux se
confondraient, alors que l'abstention est une position exprimée et que le
non-vote ne l'est pas. Toute autre teinte, elle, place la valeur sur l'échelle
qu'il s'agit précisément de ne pas construire.

**Laisser les constantes dupliquées et n'ajouter `non_votant` que dans les deux
fichiers.** Écartée : c'est la divergence que le `DESIGN_SYSTEM` signalait déjà,
et les lots 2 à 4 en auraient produit une troisième et une quatrième copie.

## Portée

- `web/UI_finale/src/utils/lecture.js` — les six règles et les couleurs, une
  seule fois. `VOTE_STYLE`, `styleForPosition`, `OUTCOME_COLOR`, `ratio`,
  `truncation`, `EMPTY_LIST_CAUSES`, `emptyListMessage`, `sourceBadge`,
  `READING_LEVELS`, `STATED_REFUSALS`.
- `web/UI_finale/src/components/Lecture.jsx` et `Lecture.css` — leur forme.
- `CandidateProfile.jsx` et `GroupProfile.jsx` importent au lieu de redéclarer.
- `tests/test_fondations_lecture_326.py` — verrouille les trois arbitrages en
  lisant le **code exécuté**, commentaires retirés : un commentaire qui parle
  d'« absent » ne doit ni faire passer ni faire échouer le test qui vérifie que
  la catégorie n'existe pas.

## Ce que ce lot ne fait pas

Il ne touche à aucune donnée, ne demande aucune collecte, n'ouvre aucun agrégat.
Le dépôt n'a pas de runner JS (`oxlint` seul) : les invariants sont donc tenus
par un test Python lisant la source, le patron de `tests/test_retrait_nosdeputes_529.py`
et de `tests/test_licences_530.py`. Ajouter un runner JS est un chantier à part,
et il n'est pas ouvert.
