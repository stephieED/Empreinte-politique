<a id="cache-mode-interventions-505"></a>
# La clé de cache AN porte le MODE, et le job roster ne l'écrit plus (#505) (2026-08-20)

`2026-08-20`

> **En bref** — un job n'écrit jamais la clé d'un contenu qu'il ne produit pas.

Troisième reprise de #412 §2.3 → #424 → #498. À chaque fois la même forme : un
job écrit la clé hebdomadaire d'un contenu qu'il ne produit pas, `actions/cache`
saute la sauvegarde de ceux qui l'ont réellement téléchargé, et tout est
retéléchargé. À chaque fois aussi, un commentaire exact au moment où il a été
écrit devient faux sans être relu.

## Le diagnostic de l'issue est faux sur le mécanisme

#505 (et #498 avant elle) désigne `extract-roster-groupes` : il porterait
`--skip-interventions` en dur *et* écrirait la clé en premier. **Vérifié, c'est
l'inverse.**

Run `32149708461` (18/08/2026), logs des jobs `95753418739` et `95759753261` :

| Horodatage | Job | Événement |
| --- | --- | --- |
| 14:46:12 | `extract-an (jean-luc-melenchon)`, 1er shard | `Cache saved with key: public-data-cache-dossiers-2026-W34` |
| 14:46:15 | idem | `Cache saved with key: public-data-cache-an-2026-W34` |
| 15:05:30 | `extract-roster-groupes (shard 0)` | `Cache hit occurred on the primary key …, not saving cache` **sur les deux clés** |

`extract-roster-groupes` a `needs: [… extract-an …]` (l. 1222) : il démarre
derrière le producteur et n'a jamais écrit ces clés. Ce n'était pourtant pas une
garantie, seulement un ordonnancement — voir « ce qui reste latent » plus bas.

## Le vrai mécanisme : une dissociation entre MODES, pas entre JOBS

La clé était `public-data-cache-an-<semaine ISO>`. Son **contenu**, lui, dépend
de `collect_interventions` : sans l'input, `extract-an` ne remplit ni
`.cache/questions_an` ni `.cache/syceron_an`. Le premier run de la semaine —
presque toujours en mode par défaut — figeait donc l'entrée pour six jours.

Mesuré sur l'API des caches du dépôt, 20/08/2026 :

| Entrée | Taille | Créée le |
| --- | --- | --- |
| `public-data-cache-an-2026-W34` | **21 881 332 o** | 18/08 14:46, run `32149708461`, mode par défaut |
| `public-data-cache-an-2026-W34` (autre `path`) | 53 166 635 o | 18/08 13:50 |
| `public-data-cache-an-2026-W34` (autre `path`) | 915 710 769 o | 17/08 09:25, avant #424 |

21 Mo, c'est `acteurs_historique_an` + `scrutins_an` : ni débats ni questions.
Les deux runs en mode interventions du 20/08 (`32302557156`, `32379928098`) ont
tous deux touché cette entrée (`Cache hit for: public-data-cache-an-2026-W34`,
`Cache Size: ~21 MB`, log du job `96461052415`) sans jamais pouvoir sauver la
leur.

Trois entrées coexistent sous la même clé parce que `actions/cache` dérive la
**version** d'une entrée du hash de son `path` : deux listes de chemins
différentes sous une même clé donnent deux entrées qui ne se voient pas. C'est
la raison pour laquelle `extract-an` et `extract-roster-groupes` doivent garder
un `path` identique au caractère près, pas seulement équivalent
(`tests/test_ci_cache_paths.py`).

## Le volume, par population nommée

**Mesuré** le 20/08/2026 par 15 requêtes `HEAD` sur
`data.assemblee-nationale.fr` (Content-Length, source saine) — population : les
archives que lit UN shard `extract-an` en mode interventions, pour un candidat
député :

| Archive | Législatures | Volume |
| --- | --- | --- |
| Syceron `syseron.xml.zip` | 17 / 16 / 15 | 55,8 + 57,6 + 149,0 = **262,3 Mo** |
| Questions QE/QG/QOSD | 17 / 16 / 15 / 14 | **388,2 Mo** (12 fichiers) |
| | | **650,5 Mo par shard** |

À 8 shards, **5,2 Go par run** en mode interventions — dont 7/8 entièrement
gaspillés. C'est le coût fixe dominant du mode, et il concorde avec les 118 s
que #498 avait chronométrées sur le seul Syceron de `laurent-wauquiez`.

**Mesuré** aussi, en local le 20/08, sur la seule législature 17 : Syceron pèse
**380,0 Mo sur disque** une fois l'archive extraite (55,8 Mo de ZIP + 324,2 Mo
de XML, 601 fichiers), pour un `index_par_acteur.json` de **2 octets**. Projeté
sur les trois législatures : ~1,1 Go de cache pour un index vide.

## Ce qui est retenu

1. **La clé porte le mode** :
   `public-data-cache-an-<semaine>${{ inputs.collect_interventions && '-interv' || '' }}`.
   Un run en mode interventions ne peut plus faire d'*exact key hit* sur une
   entrée sans interventions ; il repart en chaud sur `acteurs_historique_an` et
   `scrutins_an` par `restore-keys`, télécharge les archives et **sauvegarde**.
   Gain projeté : 7 shards × 650,5 Mo = **4,55 Go de moins par run**, sur la
   population des 8 shards `extract-an` en mode interventions.
2. **Le `path` ne retient que l'INDEX, jamais les archives.**
   `_build_acteur_questions_index` et `_build_acteur_interventions_syceron_index`
   court-circuitent tout le réseau dès que `index_par_acteur.json` existe :
   cacher les ZIP et l'arborescence XML n'accélérerait rien et coûterait ~1,8 Go
   d'entrée. Même principe que `.cache/amendements_an` (#251), qui n'a jamais
   caché que son index.
3. **`extract-roster-groupes` passe en `actions/cache/restore@v5`** sur ses deux
   steps. Il porte `--skip-interventions` ET `--skip-dossiers-legislatifs` en
   dur : il ne produit aucun des trois répertoires concernés. Il ne perd rien —
   `acteurs_historique_an` et `scrutins_an`, qu'il produit vraiment, sont déjà
   persistés par `extract-an` qui le précède.

## Ce qui est écarté, et pourquoi

**Un job dédié aux index d'interventions, sur le modèle de
`extract-amendements-an` + artifact** — c'est le remède que #505 proposait.
Écarté sur mesure, pour deux raisons distinctes :

- **Côté Syceron, il construirait un index vide.** Le corpus le dit :
  **0 des 789 interventions** des 209 profils bruts (`raw_data/profiles/`, ref
  `07e9147`) vient de Syceron — 446 `www.nosdeputes.fr`, 293
  `questions.assemblee-nationale.fr`, 50 `2017-2022.nosdeputes.fr`. La cause est
  identifiée : `_parse_syceron_intervention_entry` exige un `acteurRef` de la
  forme `PA\d+`, alors que les comptes rendus publient un identifiant **nu**
  (`<orateur><id>942</id>`, jamais préfixé). Vérifié : sur la législature 17,
  **115 des 207** identifiants `PA<n>` du corpus apparaissent tels quels, sans
  préfixe, parmi les 730 identifiants d'orateurs de l'archive. Reconstruit en
  local avec le préfixe, l'index de la seule législature 17 contient **105 392
  interventions pour 674 acteurs** (102,3 Mo). C'est un défaut de collecte, à
  traiter pour lui-même — pas une question de cache, et sûrement pas un job
  dédié à construire `{}`.
- **Côté questions, le gain existe mais la correction de clé le capture déjà.**
  Un job dédié coûterait un préambule complet (107-193 s mesurés sur `extract-an`)
  pour économiser ce que la sauvegarde du 1er shard économise désormais. À
  rouvrir si la mesure montre que le budget de 240 s de #498 coupe régulièrement
  le 1er shard avant la dernière législature — c'est le seul cas où l'index
  persisté resterait partiel.

**Une clé séparée pour les seules interventions** : c'est ce que #498 écartait
en invoquant un index partiel « limité aux législatures que le shard a eu besoin
de lire ». **Ce raisonnement est faux tel qu'écrit** : les deux index sont bâtis
**par législature et pour tous les acteurs**, jamais par candidat. Tout député
lit les 3 législatures Syceron et les 4 de questions. La partialité possible est
donc *entre* législatures, et seulement si le budget de #498 rend la main — pas
« celles dont il avait besoin ».

## L'affirmation corrigée, et celle qui l'accompagnait

`generate-data.yml` portait, en deux exemplaires (`extract-an` et
`extract-roster-groupes`), au-dessus du cache des **dossiers législatifs** :

> Contrairement au défaut corrigé en #424, il n'y a ici aucune dissociation entre
> producteur de contenu et écrivain de clé : les trois jobs téléchargent et
> consomment les mêmes archives.

C'était vrai à l'écriture et faux depuis #357 : `extract-roster-groupes` porte
`--skip-dossiers-legislatifs` en dur, il ne télécharge ni ne consomme aucun
dossier. Ils ne sont que **deux** producteurs (`extract-an`, `merge-and-pivot`)
sur trois jobs déclarant ce chemin.

Deux autres commentaires du même fichier étaient périmés depuis #424 et sont
corrigés au passage : « les trois jobs qui écrivent la clé de cache partagée
`public-data-cache-an-*` » (il n'y en a plus qu'un, `extract-an`) et « Clé de
cache réutilisée : la même clé hebdomadaire partagée `public-data-cache-an-*` »
côté amendements (ils ont leur propre clé depuis #424).

Enfin, `fetch_questions_officielles` affirmait depuis #498 que « l'index par
acteur n'est écrit en cache qu'une fois la législature entièrement lue ».
**Faux, et mesuré comme tel** : le 20/08, l'archive QE de la législature 17 est
tombée en `IncompleteRead` et `_build_acteur_questions_index` a quand même écrit
son index — 16,8 Mo, 2 611 questions issues des seules QG/QOSD.

## Le corollaire obligé : ne jamais mettre en cache un index incomplet

Tant que chaque shard reconstruisait son index, un index tronqué mourait avec
son runner. En rendant la clé sensible au mode, #505 fait l'inverse : l'index
d'un shard sert à tous les autres, pour toute la semaine. Une seule coupure
réseau figerait donc une collecte tronquée présentée comme faite — un « 0 » qui
n'est pas une absence mesurée (§2.5).

`_build_acteur_questions_index` et `_build_acteur_interventions_syceron_index`
rendent désormais l'index partiel à l'appelant (le candidat en cours n'a pas à
être puni de la panne) mais **refusent de le mettre en cache**. Couvert par
`tests/test_index_interventions_cache_partiel.py`, sur doublures.

> **Ce corollaire est juste, et il ne suffisait pas** (#550, 2026-08-28). Refuser
> de mettre en cache une législature illisible évite bien de figer un index vide
> — mais le shard sauvegarde quand même son entrée, avec les autres législatures,
> **sous une clé qui ne dit rien de ce qui manque**. Mesuré le 27/08 : une entrée
> de 114 481 867 o écrite sous `public-data-cache-an-2026-W35-interv` avec une
> seule des trois législatures de débats, sur laquelle le run suivant a fait un
> *exact key hit*. La règle qui manquait n'est pas dans le constructeur d'index,
> elle est dans la clé. Voir
> [#cache-completude-interventions-550](cache-completude-interventions-550.md).

## Ce qui reste latent, et le garde-fou

La dissociation côté dossiers n'a jamais mordu parce que `extract-an` précède le
roster. Mais rien ne l'imposait : un `prepare-an-matrix` rendant une liste vide
skippe `extract-an`, et `extract-roster-groupes` (`if: !cancelled()`) aurait
alors écrit la clé de la semaine sur un répertoire vide — et
`merge-and-pivot`, qui en a réellement besoin pour les profils de gouvernement,
aurait retéléchargé les trois archives à chaque run des six jours suivants, avec
le risque d'écrasement que #427 décrit. La restauration seule ferme ce cas.

`tests/test_ci_cache_producteur_ecrivain.py` tient la **classe** de défaut, pas
sa dernière instance :

1. tout step `actions/cache` du workflow est inventorié avec son sens
   (sauvegarde / restauration seule) — en ajouter un sans se prononcer échoue ;
2. un step qui sauvegarde ne peut lister que des répertoires que son job
   remplit, **déduit des drapeaux `--skip-*` lus dans le job** et non d'une
   liste recopiée : c'est ce qui permet au garde-fou de suivre le pipeline
   quand il bouge, au lieu de vieillir comme le commentaire qu'il remplace ;
3. un répertoire produit seulement dans un mode impose ce mode dans la clé ;
4. la phrase « les trois jobs téléchargent et consomment les mêmes archives » ne
   peut plus revenir.

Vérifié **par mutation** (leçon de #460 : un garde-fou débranché est pire
qu'aucun) — 10 régressions introduites une à une, 10 détectées : les 4 remises
en `actions/cache@v5` / perte du mode dans la clé / retour du commentaire /
12ᵉ step non déclaré / divergence de `path` entre les deux jobs AN, et les 4 du
volet Python (index incomplet remis en cache, échec de téléchargement non
marqué, index Syceron vide remis en cache, retour de l'affirmation de #498).

## Conséquence sur la première exécution

Le `path` change, donc sa version aussi : la prochaine exécution ne verra plus
l'entrée de 21 Mo du 18/08 et retéléchargera une fois `acteurs_historique_an` +
`scrutins_an` (~40 Mo, relevé #467). Coût unique, dans le budget de 5 min du
mode par défaut, dont l'extraction consomme 8-18 s.
