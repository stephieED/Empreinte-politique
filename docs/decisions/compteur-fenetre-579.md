<a id="compteur-fenetre-579"></a>
<a id="etape-ci-runner-576"></a>
# Trois contrôles qui écrivaient leur conclusion sans la mesurer (#576, #579) (2026-08-29)

`2026-08-29`

> **En bref** — trois compteurs recâblés sur la mesure réelle.

Trois défauts constatés **en exécution réelle** les 28 et 29/08/2026, et une
même forme : un contrôle qui produit une phrase juste-vraisemblable au lieu d'un
constat. C'est la prémisse de l'épic #566 — *ce qui n'a jamais été exécuté n'est
pas connu* — appliquée cette fois à des correctifs déjà livrés.

## #579 — le compteur de fenêtre comptait la mauvaise population

**L'hypothèse de l'issue est infirmée, et c'est mesuré.** #579 soupçonnait
`git fetch --filter=blob:none` d'être refusé par GitHub sur un clone superficiel
mais non partiel — l'extension `partialclone` n'étant pas configurée. Rejoué le
29/08/2026 contre `github.com` (git 2.43.0), depuis un clone `--depth=1` **non
partiel** : le fetch filtré rend **0**, sans avertissement, et enregistre
`remote.origin.promisor=true` de lui-même. Les **3,8 s** du step au run
`33200210924` ne sont pas la trace d'un fetch en échec : c'est la durée d'un
fetch **qui a réussi**.

**La cause est une confusion d'unités**, la même famille que les chiffres faux
du budget de temps mur de `generate-data.yml` avant #467 :

| grandeur | unité |
| --- | --- |
| la fenêtre de rétention | **commits de données** (30) |
| `git fetch --deepen=N` | **profondeur d'histoire** (générations) |

Sur ce dépôt les deux sont sans rapport, et le rapport n'est pas une constante :
il dépend du rythme des PR. Mesuré le 29/08/2026 sur l'historique réel, depuis
`68c07e0` (le commit de données qu'a écrit le run `33200210924`) — **32 commits
de données pour 867 commits atteignables**, et les commits de données ne sont
pas contigus. En modélisant la sémantique exacte de `--deepen` (profondeur =
plus court chemin depuis la pointe) :

| profondeur demandée | commits vus | dont commits de données |
| ---: | ---: | ---: |
| 11 | 26 | 3 |
| **41** (`FENETRE + 10`, #574) | **119** | **8** |
| 101 | 284 | 17 |
| 199 | — | 30 |
| 203 | — | 32 |

`--deepen=40` faisait voir **8 commits de données sur 32**. Assez peu pour
prendre la branche « non contraignante », assez plausible pour ne pas se voir.
**Le compteur comptait juste ; il comptait sur la mauvaise population.**

**La correction ne devine plus de profondeur** : le step dé-superficialise
l'historique, avec `--filter=tree:0` et non `blob:none`. `git log --grep` ne lit
que des objets *commit* ; `blob:none` laissait encore venir **tous les arbres**,
c'est-à-dire l'essentiel du poids d'un dépôt de profils. `tree:0` rend enfin ce
que le commentaire de #574 promettait déjà — *le graphe, pas le contenu*.

Mesuré contre `github.com`, sur ce dépôt : **3,16 s, 877 commits, `.git` de
972 Ko au total**, et `git log --grep` y rend **32** — le chiffre de #579. Et
depuis un clone superficiel **non partiel** (`github/gitignore`, 4 221
commits) : **1,58 s**, code 0, filtre bien enregistré, arbres anciens absents.
La dé-superficialisation filtrée n'est donc pas réservée aux clones déjà
partiels.

**Deux garde-fous, parce qu'un seul ne couvre pas les deux pannes :**

- `|| true` et `2>/dev/null` retirés du fetch. Un approfondissement en échec
  n'autorise **aucun** compte, et le step le dit par `::warning::` en nommant le
  code de retour. « Je n'ai pas pu compter » n'est pas « la fenêtre n'est pas
  atteinte » — même famille que le `except Exception` de #562 ;
- un fetch qui rend **0 sans lever la troncature** ne donne pas non plus le
  droit de compter. C'est le garde-fou qui aurait attrapé #574 *en exécution* :
  un compte sur un historique tronqué est un **minorant**, et un minorant
  plausible ne se voit pas.

**Le compte part sur stdout.** `$GITHUB_STEP_SUMMARY` n'est récupérable ni par
`gh run view --log` ni par l'API (`output.summary` et `output.text` reviennent
vides) : diagnostiquer les deux pannes a demandé de télécharger le journal brut
du job et de **mesurer la durée du step**. Une ligne suffit, et elle nomme la
population de chaque chiffre.

Le step ne fait toujours pas tomber le job : il vient de committer des données,
et un compteur n'est pas une porte de qualité.

**Ce qui reste à établir sur un run réel.** La version de git du runner
`ubuntu-latest`, et l'absence de configuration posée par `actions/checkout` qui
gênerait la dé-superficialisation filtrée. **Condition de vérification, écrite
d'avance** : au prochain run de `generate-data`, le journal du step doit porter
la ligne `Fenêtre de rétention : N commit(s) de données pour une fenêtre de 30,
sur M commit(s) d'historique complet parcourus`, avec **M de l'ordre de 900** et
**N ≥ 30**, suivie d'un `::warning::`. Toute autre sortie est un échec du
correctif — et elle est maintenant lisible sans télécharger quoi que ce soit.

**Ce que ça dit du test.** `test_l_approfondissement_depasse_la_fenetre` est
retiré : il exigeait que la profondeur soit dérivée de `FENETRE`, c'est-à-dire
qu'il **verrouillait la confusion d'unités** au lieu de l'interdire. Un test
peut figer un défaut ; celui-là l'a fait pendant une journée. Le step est
désormais **exécuté** contre des dépôts fabriqués, pas seulement relu.

## #576 — l'étape 6 du runner déclarait le succès avant de regarder

Réserve 1 du déroulé de bout en bout du 29/08/2026 sur le banc. L'étape écrivait
`« … et elle est passée : Tests (pytest) vert sur f307be7 »` **avant** toute
interrogation ; le SHA était en dur et datait de la répétition de la veille, pas
du commit qu'on venait de pousser (`f47213e`) ; et la sortie de `gh run list`
était affichée mais **jamais lue**, son échec avalé par `|| true`.

La CI *était* verte ce jour-là. Un jour où elle casse, l'étape aurait écrit la
même chose. C'était **la case centrale de #569**, et la seule étape du runner
qui n'observait pas ce qu'elle annonçait.

Le commit à vérifier **se lit sur `refs/heads/main` du dépôt distant** — le seul
endroit où « ce qui est poussé » existe. La branche locale `main-borne` reste un
repli, et le repli **se dit** : *« C'est une supposition, pas une lecture. »*
L'étape attend ensuite une conclusion, avec un plafond, pour que « toujours en
cours » finisse par se dire au lieu de bloquer une session déjà passée par le
point de non-retour.

La conclusion est une **précondition au sens du runner** : elle refuse
d'avancer, elle se contourne en toutes lettres, le contournement se consigne.
Quatre constats, quatre messages — verte, rouge, et trois façons d'être
indéterminée (rien de conclu, aucun run déclenché, question impossible à poser).
**Une CI rouge n'est pas un échec du bornage** : la coupure a tenu. C'est un
constat sur ce qui tourne dessus, il s'affiche, il se journalise, et il nomme
les runs fautifs.

## #576 — `--depuis` n'existait qu'à moitié : arbitrage rendu, on le retire

Réserve 2. `DEPUIS` était initialisée à 1 et fixée par rien d'autre que
`--etape`. Une plage « 6 à 7 » n'était pas exprimable, et `--jusqu-a 7`
repartait de l'étape 1 — c'est-à-dire **rejouait le push forcé**.

**On retire la variable plutôt que de finir l'option**, pour trois raisons :

1. `--depuis 6` serait une **déclaration** — « les cinq premières sont faites » —
   que le runner devrait de toute façon confronter au journal, seul endroit où
   cette information existe. Deux sources de vérité pour une même question, dont
   une invérifiable ;
2. `--reprendre <journal>` **dérive** le point de reprise de la trace, et il
   fonctionne : vérifié le 29/08/2026, relancé après l'étape 5, il a sauté 4 et
   5 sans qu'aucune phrase ne soit redonnée ;
3. sans journal, `--depuis 6` n'aiderait pas davantage — il faudrait déroger
   cinq fois pour franchir l'ordre.

Ce qui manquait n'était donc pas l'option : c'était de **dire** que `--reprendre`
est le chemin. `--lister` le dit, et nomme le piège — sans journal, `--jusqu-a 7`
repart de l'étape 1. La variable devient `PREMIERE_ETAPE`, interne, et un test
verrouille qu'elle n'est fixée qu'à l'initialisation et par `--etape`.

## Ce que ces trois défauts ont en commun

Aucun n'était atteignable par relecture, et deux ont **survécu à des tests** —
un test de motif qui verrouillait la ligne fautive, une étape dont le message ne
dépendait d'aucune observation. La correction n'est donc pas seulement dans le
code : les deux contrôles sont désormais **exécutés** dans la suite, contre des
dépôts fabriqués, et chaque garde-fou a été validé **par mutation** — quatorze
mutations, chacune fait tomber au moins un test.

