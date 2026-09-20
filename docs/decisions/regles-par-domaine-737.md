<a id="regles-par-domaine-737"></a>
# `AGENTS.md` garde ce qui gouverne tout, `docs/regles/` ce qui gouverne un domaine (#737) (2026-09-04)

`2026-09-04`

> **En bref** — le fichier faisait **983 lignes** chargées à chaque session et grossissait à chaque lot ; l'hypothèse de départ « il mélange l'instruction et sa preuve » a été appliquée à dix puces et n'a rendu que **39 lignes**, les gains tombant de 11 à 0 — **seules 30 lignes sur 983 portaient un chiffre**, le reste était de l'instruction écrite longuement ; la mesure a montré l'autre levier : **78 % du fichier (738 lignes sur 921) ne sert qu'à qui touche un module donné**, et la §3 était le seul endroit où l'on savait qu'un agent lirait une règle, d'où l'accumulation ; d'où huit fichiers `docs/regles/` (§3a→`fusion-et-index`, §3b→`ci`, §3c→`gardes-avant-commit`, §3d→`roster-et-sources`, §3e→`interventions-syceron`, §3f→`portail-qualite`, §4→`schema-pivot`, §5→`champs-sensibles`) et **983 → 343 lignes** sans qu'une instruction disparaisse ; ce qui aurait cassé en silence : le dépôt cite « AGENTS.md §X » **596 fois dans 200 fichiers**, mais **~430 visent la §2 qui ne bouge pas**, et les sections déplacées continuent de résoudre parce qu'`AGENTS.md` **garde la ligne d'index de chacune** ; 28 tests le vérifient dans les deux sens, avec un compteur-témoin contre le relevé vide (#510), un plafond de 500 lignes et l'obligation que la §2 reste sur place — seule section qu'un agent doit avoir sous les yeux **sans savoir qu'il en a besoin** ; la scission a immédiatement cassé `test_ci_signal_identite_push_685`, qui lisait une règle de §3b dans `AGENTS.md` et lit désormais **les deux fichiers** : c'est le coût réel, **un test qui vérifie une règle doit lire le fichier où elle vit** ; coût assumé et non arrondi — un agent qui n'ouvre pas le bon fichier rate une règle, et le bénéfice n'est pas la longueur mais la **stabilité** ; les dix puces réécrites sont conservées, dont celle du `texte_vise` qui annonçait « 293 582 of 484 132 » **au présent et sans date**, vrai à l'écriture et **faux depuis #696** (remesuré : **0 sur 509 744**), citée deux fois comme un état courant par une autre session — **une mesure non datée dans un fichier d'instructions se lit comme un état courant** ; déplacement contrôlé par script, chaque nombre retiré devant exister dans une décision, **comparé nombre à nombre et non chaîne à chaîne** (anglais « 477 of 481 » contre français « 477 des 481 »). 3 777 tests, 0 échec.

## 1. Le constat

`AGENTS.md` faisait **983 lignes, 83 Ko**, chargées à chaque session, pour toute
tâche. Le fichier était devenu instable : chaque lot y ajoutait sa puce.

Deux mesures, et la seconde n'est pas celle qu'on attendait :

| | |
| --- | ---: |
| Lignes portant une **mesure chiffrée** | **30** |
| dont non datées, donc lues comme un état courant | 28 |
| Règles **générales** (§1, 2, 6, 7, 8, 9, 10, 11) | **183 lignes** |
| Règles liées à **un module précis** (§3, 4, 5) | **738 lignes** |

**Le gonflement ne venait pas des chiffres.** L'hypothèse de départ — « le
fichier mélange l'instruction et sa preuve » — a été appliquée à dix puces et n'a
rendu que **39 lignes** : les gains sont tombés de 11 à 0 au fil des puces, parce
que le reste était déjà de l'instruction. Le critère est bon, il n'avait presque
rien à couper.

Ce que la mesure a montré à la place : **78 % du fichier ne sert qu'à qui touche
un module donné**, et la §3 était le seul endroit où l'on savait qu'un agent
lirait une règle. D'où l'accumulation.

## 2. La décision

`AGENTS.md` garde **ce qui gouverne tout** : le produit, les huit règles
éditoriales, les métriques publiques et internes, les licences, la tenue de la
documentation, la façon de rendre compte, le rapport d'un sous-agent, ce qu'on
demande à la propriétaire.

Huit fichiers de `docs/regles/` portent **ce qui gouverne un domaine**, chargés
quand on y touche :

| Fichier | Ex-section |
| --- | --- |
| `fusion-et-index.md` | §3a |
| `ci.md` | §3b |
| `gardes-avant-commit.md` | §3c |
| `roster-et-sources.md` | §3d |
| `interventions-syceron.md` | §3e |
| `portail-qualite.md` | §3f |
| `schema-pivot.md` | §4, §4a, §4b |
| `champs-sensibles.md` | §5 |

**983 → 343 lignes**, sans qu'une instruction disparaisse.

## 3. Ce qui aurait cassé en silence, et ce qui l'empêche

Le dépôt cite « `AGENTS.md` §X » **596 fois dans 200 fichiers**. Réécrire ces
renvois serait un lot à soi seul ; les laisser pourrir serait pire, parce qu'un
renvoi qui ne résout plus donne l'illusion d'une règle consultable.

La répartition a sauvé le lot : **~430 de ces citations visent la §2**, qui ne
bouge pas. Les sections déplacées n'en portent qu'une centaine, et elles
continuent de résoudre parce que **`AGENTS.md` garde la ligne d'index de chacune**
— « §3a » y est toujours nommée, avec le chemin du fichier qui la porte.

`tests/test_regles_par_domaine_737.py` (28 tests) le vérifie dans les deux sens :
chaque fichier de domaine existe, n'est pas réduit à son en-tête, nomme sa
section d'origine et figure dans l'index ; **toute section citée dans le dépôt
reste nommée dans `AGENTS.md`** ; et un compteur-témoin refuse que le relevé des
renvois devienne vide, ce qui ferait passer le contrôle pour de bonnes raisons
apparentes (#510).

Deux garde-fous de fond : `AGENTS.md` doit rester **sous 500 lignes**, et les
règles éditoriales de la §2 doivent y rester — c'est la seule section qu'un agent
doit avoir sous les yeux **sans savoir qu'il en a besoin**.

## 4. Ce que la scission a déjà cassé, et qui l'a rattrapé

`test_ci_signal_identite_push_685` lisait une règle de §3b **dans `AGENTS.md`**.
Elle vit désormais dans `docs/regles/ci.md`, et le test est tombé au premier
lancement. Il lit maintenant **les deux fichiers** : la garantie fausse que #685
a retirée ne doit réapparaître ni dans le fichier de règles, ni dans l'index qui
le résume.

C'est le coût réel de la scission, et il est nommé : **un test qui vérifie une
règle doit lire le fichier où elle vit.** Ici la suite l'a dit tout de suite ;
elle ne le dira pas toujours.

## 5. Ce que ça coûte, sans l'arrondir

**Un agent qui n'ouvre pas le bon fichier rate une règle.** Avant, il les avait
toutes sous les yeux — c'était le seul avantage réel des 983 lignes, et il n'est
pas nul. Ce qui le compense : l'index de la §3 nomme les huit domaines en six
lignes, et `docs/decisions-par-module.md` répond déjà à « je touche ce fichier,
qu'est-ce qui le gouverne ».

**Et le vrai bénéfice n'est pas la longueur, c'est la stabilité** : un lot sur la
fusion touche `docs/regles/fusion-et-index.md`, et `AGENTS.md` ne bouge pas.

## 6. Ce qui reste du premier critère

Les dix puces réécrites sont conservées — l'instruction reste, la preuve part
dans la décision liée. La plus utile est celle du `texte_vise` (#639) : elle
annonçait « **293 582 of 484 132 published amendments carry no key** » au présent
et sans date. C'était vrai à l'écriture, et **faux depuis #696** — remesuré le
04/09/2026 : **0 sur 509 744**. Une autre session l'a citée deux fois comme un
état courant, dont une fois pour répondre à la propriétaire qu'une donnée
n'existait pas.

**Une mesure non datée dans un fichier d'instructions se lit comme un état
courant.** Deux lignes plus bas, « 2 500 … on 01/09/2026 » portait sa date et n'a
trompé personne.

Le déplacement a été contrôlé par script, pas sur parole : chaque nombre retiré
d'une puce doit exister dans un fichier de `docs/decisions/`, **comparé nombre à
nombre et non chaîne à chaîne** — `AGENTS.md` est en anglais (« 477 of 481 ») et
les décisions en français (« 477 des 481 »).
