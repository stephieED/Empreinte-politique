<a id="correspondance-acteurs-an-525"></a>
# La correspondance slug ↔ acteur AN devient un artefact committé (#525, lot 2 de l'épic « une seule source AN ») (2026-08-26)

`2026-08-26`

> **En bref** — un artefact committé et vérifié, jamais une heuristique de noms.

## 1. Le problème

Les **slugs NosDéputés sont les identifiants de profil** du dépôt :
`pivot_data/profiles/<slug>.pivot.json`, et `id` du schéma pivot (#487). AMO30
— l'archive historique des acteurs de l'Assemblée nationale — ne publie ni ce
slug ni aucun identifiant externe : elle rend un `PA######` et de l'état civil.
Un roster dérivé d'AMO30 (lot 1) ne sait donc pas **quel profil il alimente**
tant que cette correspondance n'existe pas comme donnée.

Le slug reste l'`id`. Un `acteur_ref` est une **correspondance**, jamais un
renommage : renommer un fichier publié est une suppression, et
`audit_diff_profils` la bloque (#460/#470). Mesuré après ce lot :
`audit_diff_profils --ref HEAD` rend « Aucune perte bloquante » sur les 8
couches, aucun `id` ne change.

## 2. Ce qui existait, et ce qui manquait

`candidate_profile._resolve_acteur_ref_par_slug` rapproche déjà un slug d'un
acteur par nom normalisé, et **refuse l'homonymie** plutôt que d'attribuer au
hasard. Mesure reproduite le 26/08/2026 sur les **476 profils publiés** et les
**3 119 acteurs** d'AMO30 : **466 résolus, 10 non résolus**.

Les 10 restants ne sont pas un défaut d'algorithme — ce sont des faits d'état
civil que rien dans les données ne permet de deviner :

| Slug | Écart | `acteur_ref` | Ce que l'AN publie |
| --- | --- | --- | --- |
| `alexandra-martin` | homonymie | `PA793342` | « Alexandra Martin (Alpes-Maritimes) », née le 25/10/1968 |
| `alexandra-martin-1` | homonymie | `PA793944` | « Alexandra Martin (Gironde) », née le 28/07/1976 |
| `christelle-d-intorni` | apostrophe | `PA793322` | « Christelle D'Intorni » |
| `loic-prud-homme` | apostrophe | `PA719578` | « Loïc Prud'homme » |
| `christelle-petex-levet` | nom divergent | `PA721442` | « Christelle Petex » (courriel AN : `petex-levet`) |
| `claire-pitollat` | nom divergent | `PA718910` | « Claire Colomb-Pitollat » (courriel AN : `Claire.Pitollat`) |
| `emmanuel-tache-de-la-pagerie` | nom divergent | `PA793382` | « Emmanuel Taché », sans la particule |
| `sabrina-agresti-roubache` | nom divergent | `PA793278` | « Sabrina Roubache » (courriel AN : `agrestiroubache`) |
| `guillaume-gouffier-cha` | changement de nom | `PA721296` | « Guillaume Gouffier Valente » (site déclaré : `gouffier-cha.fr`) |
| `jordan-bardella` | **hors AN** | `null` | rien — député européen |

Deux observations tranchent le débat « algorithme ou table » :

- l'AN désambiguïse les deux Alexandra Martin **dans l'état civil lui-même**
  (`Martin (Alpes-Maritimes)` / `Martin (Gironde)`), au point de suffixer une
  adresse de courriel. Aucune règle de normalisation ne peut deviner laquelle
  des deux porte le slug non suffixé ; le `-1` de NosDéputés ne porte aucune
  information institutionnelle ;
- l'écart le plus fréquent est le **nom d'usage** ou le **changement de nom**,
  c'est-à-dire précisément ce qui bouge dans le temps. Une heuristique qui les
  rattraperait rattraperait aussi, sans le dire, des rapprochements faux.

Ce qui manquait n'était donc pas un algorithme mais un **artefact de premier
ordre** : une table committée, relue, dont chaque entrée porte sa preuve.

## 3. La décision

`raw_data/correspondance_acteurs_an.json`, schéma
`correspondance-acteurs-an-v1`, **476 entrées sur 476 profils publiés**
(475 avec acteur, 1 déclarée hors AN). Chaque entrée porte `acteur_ref`,
l'`etat_civil` retenu (celui d'AMO30), l'`ecart` (fermé :
`apostrophe`/`nom_divergent`/`homonymie`/`hors_an`, `null` pour les 466), le
`motif` — **obligatoire dès qu'il y a un écart** —, la `preuve` (URL de la
fiche AN de l'acteur, ou la source qui tranche) et la date `verifie_le`.

**Un trou est déclaré, jamais absent.** `jordan-bardella` porte
`acteur_ref: null`, `ecart: "hors_an"` et son motif : député européen, aucun
acteur AMO30 ne lui correspond. C'est un fait vérifié, pas une correspondance
manquante. Un trou muet est ce qui a produit #510 et #501 (AGENTS.md §2
règle 5). La distinction est testée : `resoudre_acteur_ref` rend `None` dans
les deux cas, `est_declare_hors_an` les sépare.

**Recoupement indépendant** : les 474 profils publiés qui portent une
`identite.source_url` AN donnent **474 accords, 0 désaccord** avec la table.
Les deux qui n'en portent pas sont `jordan-bardella` (déclaré hors AN) et
`jean-luc-melenchon`, dont l'`acteur_ref` `PA2150` est corroboré par ses
**18 721 amendements sur 18 721** signés `an:PA2150` — un slug qu'aucune
lecture de `source_url` n'aurait résolu, et que la table couvre.

## 4. Où l'échec est bruyant, et où il ne l'est pas

Question tranchée dans ce lot : la table **passe devant** la correspondance par
nom, elle ne la **remplace pas**.

- `_resolve_acteur_ref_par_slug` lit la table d'abord. Une entrée déclarée hors
  AN rend `None` **sans repli** — sinon un député européen se verrait attribuer
  un acteur AN et, avec lui, des votes ;
- un slug **absent** de la table retombe sur la correspondance par nom, qui
  garde son refus d'homonymie. Supprimer ce recours rendrait incollectable tout
  profil neuf : le roster grossit à chaque run, et un élu récent n'a par
  construction aucune entrée relue. La version stricte était plus lisible ; elle
  aurait fait de chaque élection partielle un run bloqué ;
- une table **absente ou invalide** est un repli **déclaré** — une ligne
  nommant le fichier et la cause, une fois par processus — pas un silence. Même
  ligne de conduite que le repli de `chambre` (#493) : utilisable, mais dit.

L'échec dur est ailleurs, là où il porte : **§5b du quality gate**, avant le
commit. Tout `pivot_data/profiles/<slug>.pivot.json` sans entrée bloque le
commit **en nommant le slug**, avec la commande qui répare. Seuil 0. Non
bloquant dans l'autre sens : une entrée sans profil publié est légitime — la
table a le droit de survivre à un profil retiré, comme un index partagé survit
à son référent (#485).

Le gate est le bon endroit parce qu'il est le seul contrôle d'avant-commit qui
voie **à la fois** le corpus publié et la table. Les dotfiles y sont exclus
(`Path.glob` les rend, contrairement au module `glob` — #518).

## 5. Que devient la table quand un député change de nom ?

**Rien ne bouge.** Un changement de nom ne change pas l'uid AMO30 : `PA721296`
est resté le même de « Gouffier-Cha » à « Gouffier Valente ». La correspondance
survit donc intacte à un changement de nom — c'est même l'argument principal en
faveur d'une table sur une heuristique, puisque c'est la **correspondance par
nom** qui, elle, cesse de fonctionner.

Ce qui change est le **classement** de l'entrée : elle migre de `ecart: null`
vers `ecart: "nom_divergent"`. `build_correspondance_acteurs_an.py` le signale
et ne le corrige pas seul — il compare le `nom_complet` enregistré à celui
d'AMO30 et imprime « l'état civil AN a changé depuis la vérification du
<date> », pour que le motif et la date de vérification soient repris à la main.
Il n'écrit jamais un motif qu'il aurait inventé.

Le seul cas qui exige un arbitrage humain est l'**apparition d'un homonyme** :
une deuxième « Alexandra Martin » élue rend la clé ambiguë côté nom, et c'est
exactement ce que la table tranche déjà, entrée par entrée.

## 6. Le constructeur n'invente rien

`src/build_correspondance_acteurs_an.py` reconduit **verbatim** toute entrée
existante — c'est le travail relu — puis complète avec ce que la correspondance
par nom résout seule. Ce qu'il ne résout pas, il **le nomme sur stderr et sort
en 1** : il ne comble pas depuis `identite.source_url`, alors que le champ
porte souvent le bon `PA######`. Une correspondance recopiée sans motif ni
preuve relue n'est pas un artefact vérifiable, c'est la même heuristique
déplacée d'un cran. Le résidu à trancher à la main est petit et fini : **10 sur
476**.

## 7. Condition de retrait

La table disparaît le jour où **la source publie elle-même la correspondance** :
un identifiant stable et externe dans AMO30 (le slug NosDéputés, un `uri_hatvp`
systématique, un identifiant Wikidata) qui rende le rapprochement lisible
depuis les données plutôt que depuis un fichier relu. Tant que l'AN ne publie
que `PA######` + état civil, la table reste — et sans critère écrit, ce
transitoire deviendrait permanent, comme les replis de lecture de #431 et #432.

Ce qui **ne** justifie **pas** son retrait : « les 466 se résolvent tout
seuls ». C'est vrai aujourd'hui et faux demain — quatre des dix écarts sont des
noms d'usage, c'est-à-dire des valeurs qui bougent.

## 8. Ce qui n'est pas fait ici

- le lot 1 (roster dérivé d'AMO30) reste à faire : ce lot lui donne seulement
  la table dont il dépend ;
- la table n'est **pas** lue par les tests depuis son emplacement réel — elle
  n'est pas dans le sparse-checkout de `tests.yml` (#473/#520), et l'y ajouter
  demande une modification de workflow. Les tests tournent sur
  `tests/fixtures/correspondance_acteurs_an_extrait.json`, extraite de la table
  réelle et portant les 10 cas durs **plus** deux témoins ordinaires — une
  fixture qui ne décrirait que l'exception ne dirait rien du cas courant, le
  piège de `syceron_minimal.xml` (#510). Conséquence assumée : la couverture de
  la table réelle est contrôlée par le gate à l'exécution, pas par la suite.

Gardé par `tests/test_correspondance_acteurs_an.py` (52 tests, dont les 10 cas
durs nommés un par un avec leur verdict).

