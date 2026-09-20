<a id="selection-vote-sur-ensemble-672"></a>

# Un vote « sur l'ensemble d'un texte » se reconnaît à un motif ancré, jamais à une sous-chaîne (#672) (2026-08-31)

`2026-08-31`

> **En bref** — deuxième lot de #324, et l'étape 1 de l'issue est levée : `type_scrutin` est publié sur **17 748 / 17 748** scrutins sans un seul `null` (`public_ordinaire` 17 312, `solennel` 361, `motion_censure` 66, `tribune` 9, commit de données `c6edee05`) ; la sélection existante cherchait `l'ensemble` **en sous-chaîne** et était fausse dans les deux sens — 938 retenus, dont 5 vrais faux positifs (1 motion de rejet préalable, 1 article unique, 2 amendements, 1 article premier), et 22 scrutins manqués parce que l'apostrophe **typographique** n'apparaît que dans les législatures 16 (343) et 17 (541), les deux plus **récentes** ; deux corrections à l'énoncé : l'ancrage strict qu'il prescrit écarte `an:14:32`, seul scrutin des 17 748 dont l'intitulé commence par « **sur** l'ensemble » et vrai vote **solennel** sur l'ensemble — d'où `^(sur )?l'ensemble\b`, 933 —, et l'ancrage ne suffit pas puisque **8** des 933 portent sur une **sous-partie** (5 articles, 3 parties de budget dont un solennel), que l'issue n'avait pas relevés et qui reproduiraient exactement le contresens qu'elle ferme (§2 règle 2) : **925 retenus** ; la règle est écrite **une seule fois**, dans `web/UI_finale/src/utils/lecture.js`, en deux moitiés de nature différente — `type_vote` **sourcé** (#639), qui écarte les 66 motions de censure et ne rouille pas (§2 règle 4), et le motif sur le libellé, **approché**, qui rouille et se déclare ; 925 est donc un **plancher** que `MethodologyPage.jsx` publie à la place de l'affirmation d'exhaustivité que `AGENTS.md` §5 signalait lui-même comme non soutenue (17 312 scrutins portent `SPO`, qui ne sépare pas l'ensemble de l'article, et **70 des 361 solennels** ne sont pas retenus faute de la locution) ; faute de runner JS, le verrou est un test Python qui lit le code exécuté **et** exécute les littéraux d'expression régulière extraits du JS sur des libellés recopiés verbatim — le rejeu est **dérivé** de la source et non réécrit à côté d'elle, deux pièges ayant été trouvés par mutation (`re.match` ancre implicitement là où `RegExp.test` non, ce qui laissait passer un motif redevenu sous-chaîne ; une normalisation recopiée survivait à sa suppression dans le module) ; cinq mutations sont vérifiées échouantes ; `normalizeLabel` n'est appliquée qu'à cette sélection, l'étape 3 de l'issue — « partout où un libellé est comparé » — restant à moitié honorée, et les cinq vues consommatrices restent à écrire.

Deuxième lot d'implémentation de la refonte #324, après
[`couleurs-de-vote-sans-echelle-326`](couleurs-de-vote-sans-echelle-326.md). Cinq
vues du temps 2 (#594) sélectionnent les scrutins « portant sur l'ensemble d'un
texte ». La règle n'était **écrite nulle part** — c'est déjà la cause des deux
tableaux du temps 2 que le temps 3 n'a pas su reproduire
(`audit/faisabilite-visualisations-20260831.md` §6).

## Le contexte

L'étape 1 de l'issue — « attendre #639 rang 1 » — est levée : `type_scrutin` est
publié sur **17 748 / 17 748** scrutins, sans un seul `null`
(`public_ordinaire` 17 312, `solennel` 361, `motion_censure` 66, `tribune` 9).
Mesuré au commit de données `c6edee05` le 31/08/2026, sur
`pivot_data/scrutins.json`.

La sélection existante cherchait la locution `l'ensemble` en sous-chaîne. Elle
était fausse **dans les deux sens**, et les deux erreurs ne se compensent pas.

| Motif sur `scrutins.json[].texte` | Retenus |
| --- | ---: |
| sous-chaîne `l'ensemble`, apostrophe normalisée (l'existant) | 938 |
| ancré en tête sur `l'ensemble` strict, comme #672 le prescrivait | 932 |
| **ancré `^(sur )?l'ensemble\b`** | **933** |
| **moins les votes sur une sous-partie** | **925** ← la règle |

## Trois constats, dont deux corrigent l'énoncé de l'issue

### 1. L'apostrophe fait décrocher les deux législatures les plus récentes

`pivot_data/scrutins.json` porte deux apostrophes : l'ASCII `'` et la
typographique `’`. La seconde n'apparaît **que** dans les législatures 16
(343 scrutins) et 17 (541) — les deux plus récentes. Un motif écrit sur l'ASCII
manque donc 22 scrutins aujourd'hui, et en manquera davantage demain.

La normalisation est donc une règle à part entière, valable **partout où un
libellé est comparé** : NFC, puis les apostrophes sur l'ASCII, puis les espaces,
puis la casse. Le résultat est une **forme de comparaison** ; ce qui s'affiche
reste le libellé de la source (§2 règle 2).

### 2. L'ancrage strict prescrit par l'issue écarte un vrai vote

L'étape 4 de l'issue — « ancrer en tête » — est insuffisante telle qu'écrite.
Ancrer sur `l'ensemble` écarte `an:14:32`, un scrutin **solennel** dont
l'intitulé est « sur l'ensemble du projet de loi organique relatif à la
programmation et à la gouvernance des finances publiques » : un authentique vote
sur l'ensemble. C'est le **seul** des 17 748 dans ce cas, et c'est exactement
pour cela qu'il faut un test — personne ne le reverra à l'œil.

Le motif retenu rend donc le `sur ` initial optionnel. Les **5** vrais faux
positifs restent écartés dans les deux cas : 1 motion de rejet préalable
(`an:14:1353`), 1 article unique (`an:17:7003`), 2 amendements (`an:17:915`,
`an:17:916`), 1 article premier (`an:17:917`).

L'issue en annonçait 6 ; il y en a 5, la sixième étant `an:14:32` ci-dessus,
que son tableau classait à tort en faux positif.

### 3. L'ancrage ne suffit pas : 8 votes sur une sous-partie, non relevés par l'issue

Sur les 933 scrutins ancrés, **8** commencent bien par « l'ensemble » mais
portent sur une **sous-partie** du texte :

| Objet | Scrutins |
| --- | --- |
| un **article** | `an:14:1224`, `an:14:1236` (article premier du PLC de protection de la Nation), `an:14:875` (article 5 bis du PLFR 2014), `an:14:886`, `an:14:891` (articles premier et 3 du texte sur la délimitation des régions) |
| une **partie de budget** | `an:14:663` (première partie du PLF 2014, scrutin **solennel**), `an:17:445` (première partie du PLFG 2024), `an:17:242` (deuxième partie du PLFSS 2025) |

Les publier comme des votes sur un texte entier serait **exactement** le
contresens que l'ancrage vient de fermer — celui que l'issue qualifie
d'éditorialement plus grave que les 22 manqués : affirmer une position que la
personne n'a pas prise (§2 règle 2). Ils sont donc écartés eux aussi.

## La décision

**La règle est écrite une seule fois, dans `web/UI_finale/src/utils/lecture.js`,
et elle a deux moitiés de nature différente.**

| Moitié | Nature | Ce qu'elle fait |
| --- | --- | --- |
| `type_vote === 'vote_texte'` | **sourcée**, ne rouille pas | vient de `typeVote.codeTypeVote` (#639) ; écarte les 66 motions de censure, faits de procédure et jamais des positions sur un texte (§2 règle 4) |
| le motif ancré sur le libellé | **approchée**, rouille | le code de scrutin ne distingue pas l'ensemble de l'article : il reste l'intitulé, qui nomme l'objet du vote en clair |

La seconde moitié rouille, et c'est admis **parce qu'elle est déclarée**. C'est
la différence avec ce que [`regrouper-nest-pas-joindre-639`](regrouper-nest-pas-joindre-639.md)
interdit : cette décision-là ferme la **jointure** d'objets de sources
différentes par ressemblance de libellés. Ici, aucune jointure — un seul objet,
une seule source, et le libellé n'est pas une clé mais la description que
l'Assemblée donne de l'objet du vote. Ce qui reste vrai des deux côtés, c'est
que le libellé dérive : d'où la borne publiée, et d'où le test.

## La borne, publiée

925 est un **plancher**, jamais un décompte exhaustif, et
`MethodologyPage.jsx` le dit (§2 règle 5). L'affirmation qu'elle remplace —
« l'univers retenu comprend **tous** les scrutins publics disponibles […]
portant sur l'ensemble d'un texte » — est celle que `AGENTS.md` §5 signale
lui-même comme non soutenue par la donnée : `SPO` « ne constitue PAS l'univers
des votes sur le texte entier que la méthodologie publiée revendique ».

Deux mesures fondent la borne :

- **la source ne distingue pas** : 17 312 des 17 748 scrutins portent le code
  `SPO`, qui couvre l'ensemble, l'article et l'amendement sans les séparer ;
- **le libellé ne dit pas toujours « l'ensemble »** : 70 des 361 scrutins
  **solennels** ne sont pas retenus, et certains sont d'authentiques votes sur un
  texte entier formulés autrement — « le projet de loi de modernisation, de
  développement et de protection des territoires de montagne (première
  lecture) ».

Ces votes-là manquent. Un vide se préfère à un décompte gonflé : un vote absent
ne dit rien, un vote attribué à tort affirme une position que la personne n'a
pas prise.

## Le verrou : un test qui dérive du code, pas qui le paraphrase

Le dépôt n'a pas de runner JS (`oxlint` seul), donc
`tests/test_selection_vote_ensemble_672.py` fait deux choses, patron de
`tests/test_fondations_lecture_326.py` : il lit le **code exécuté**,
commentaires retirés — indispensable ici, où les commentaires du module citent
les faux positifs un par un —, **et** il extrait les littéraux d'expression
régulière du fichier JS pour les exécuter en Python sur un tableau gelé de
libellés recopiés verbatim (aucun test ne lit `pivot_data/`, #473).

**Le rejeu est dérivé de la source, jamais réécrit à côté d'elle** : chaque étape
n'est appliquée en Python que si le corps JS l'applique vraiment. Deux pièges de
traduction, tous deux trouvés par mutation le 31/08/2026 et corrigés :

- `re.match` ancre implicitement en tête, `RegExp.prototype.test` non. Avec
  `re.match`, un motif redevenu **sous-chaîne** passait les 5 faux positifs au
  vert : c'était le défaut même que le test devait attraper. Le rejeu emploie
  `re.search`, et c'est le `^` du littéral JS qui ancre, comme dans le navigateur.
- une normalisation **recopiée** dans le test survit à sa suppression dans le
  module. Retirer la normalisation d'apostrophe du JS ne faisait alors échouer
  aucun test.

Cinq mutations sont vérifiées échouantes : motif redevenu sous-chaîne (6 tests),
apostrophe non normalisée (2), exclusion des sous-parties retirée (8), filtre
`type_vote` retiré (2), NFC retiré (1).

## L'alternative écartée

**Ajouter des variantes au motif** pour rattraper les cas manquants — ce que
l'issue interdit explicitement. Chaque variante ajoutée est une rouille de plus
et aucune n'est sourcée. La borne publiée est la contrepartie assumée : on
préfère déclarer ce que la sélection ne voit pas plutôt que d'élargir un motif
que rien ne garantit.

**Se limiter aux scrutins `solennel`.** Écartée : 633 des 925 retenus sont des
`public_ordinaire`, et 291 seulement des `solennel`. Se limiter au solennel
écarterait plus des deux tiers des votes sur des textes entiers — c'est le choix
que la méthodologie publiée refusait déjà, et elle avait raison.

**Attendre un identifiant sourcé du type d'objet voté.** L'Assemblée n'en publie
pas : `SPO` couvre les trois cas. Attendre reviendrait à ne rien afficher, alors
que la sélection ancrée est correcte sur ce qu'elle retient et déclare ce
qu'elle manque.

## Portée

- `web/UI_finale/src/utils/lecture.js` — `normalizeLabel`,
  `WHOLE_TEXT_VOTE_PATTERN`, `SUBPART_VOTE_PATTERN`, `isWholeTextVote`,
  `selectWholeTextVotes`, `WHOLE_TEXT_VOTE_BOUND`.
- `web/UI_finale/src/pages/MethodologyPage.jsx` — la borne, en texte publié, à
  la place de l'affirmation d'exhaustivité.
- `tests/test_selection_vote_ensemble_672.py` — 26 cas.

## Ce que ce lot ne fait pas

Il ne touche à aucune donnée et ne demande aucune collecte. `normalizeLabel`
n'est appliquée pour l'instant qu'à cette sélection : les autres comparaisons de
libellés du site ne sont pas reprises, et l'étape 3 de l'issue — « partout où un
libellé est comparé » — n'est donc honorée qu'à moitié. Les cinq vues du temps 2
qui consommeront `selectWholeTextVotes` restent à écrire.
