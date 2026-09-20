<a id="libelles-formulaire"></a>
# Les descriptions d'input sont des LIBELLES, pas des descriptions (2026-08-20)

`2026-08-20`

> **En bref** — GitHub affiche la description d'un input comme libellé du champ : ce sont des libellés, pas des descriptions.

Constat de l'utilisatrice en utilisant reellement le formulaire : **GitHub
affiche la description comme libelle du champ et masque le nom de l'input.**

La refonte du meme jour ([[refonte-inputs-workflow]]) avait raccourci les
descriptions mais gardait des renvois croises — « Implies overwrite_profiles »,
« Already implied by cold_start », « DISTINCT from allow_declared_losses ». Ces
renvois designent des noms **que personne ne voit a l'ecran**. Ils etaient donc
inutilisables par construction, et personne ne l'avait remarque parce que
personne n'avait relu le formulaire rendu.

## Ce qui change

Les libelles sont courts, autonomes, et ne referencent aucun autre champ par
son nom. La relation entre les deux premiers se lit **dans le texte** :

| Champ | Libelle |
| --- | --- |
| `cold_start` | *Overwrite profiles from scratch (purge cache & output - no merge)* |
| `overwrite_profiles` | *Overwrite profiles from cache (no merge)* |
| `refresh_existing_only` | *Limit roster to pre-existing members (no new ones)* |
| `roster_limit` | *Roster members to process. 0 = all* |
| `collect_interventions` | *Collect floor speeches (skipped for roster AN and senate)* |
| `incomplete_read_threshold` | *IncompleteRead errors tolerated before the quality gate fails* |
| `allow_declared_losses` | *INTENDED REMOVAL: allow commit despite lost entries* |
| `allow_broken_references` | *EMERGENCY ONLY: allow keys that don't resolve in their shared index* |

Les deux libelles sont **paralleles** : « Overwrite profiles **from
scratch** » contre « Overwrite profiles **from cache** ». Un seul mot les
separe, et c'est le bon. La lectrice voit la difference sans connaitre aucun
nom.

**« overwrite » et non « rebuild »** : `--no-merge` remplace au lieu de
fusionner. « rebuild » etait plus vague pour le meme nombre de caracteres.

## Deux mentions retirees, et pourquoi

**« Applies PER SHARD » sur `roster_limit`.** Elle expliquait *pourquoi* une
valeur non nulle force un seul shard — c'est-a-dire du rationale, exactement ce
que la refonte devait sortir du formulaire. Le defaut corrige y avait ete
reintroduit. Et comme toute valeur non nulle force un seul shard, la valeur
**est** le total : « 0 = all » suffit, sans ambiguite.

**Le renvoi « DISTINCT from allow_declared_losses ».** Le garde-fou de
`test_ci_integrite_referentielle.py` l'exigeait. Il exige desormais que le
libelle porte sa propre marque de gravite (`EMERGENCY ONLY`), qui le separe de
`INTENDED REMOVAL` sur l'autre tolerance — une distinction **visible a l'ecran**
plutot qu'un renvoi a un nom cache.

## `DANGEROUS` remplace par `INTENDED REMOVAL` (meme jour)

`DANGEROUS` disait l'humeur, pas l'enjeu : il prevenait qu'il faut faire
attention sans dire **de quoi on prend la responsabilite**. C'est exactement ce
qui a manque le 19/08/2026, quand la case a ete cochee sans que les pertes
soient elucidees — 789 interventions effacees.

`INTENDED REMOVAL` est une **affirmation que l'operatrice doit pouvoir faire
honnetement**. Si elle coche parce qu'un run a perdu des donnees sans qu'on
sache pourquoi, le libelle sonne faux au moment de cliquer. C'est la qu'il doit
resister.

*Ecarte* : `CLEANING`. Il decrit une activite benigne et y installe la lectrice
— « oui, je fais du menage », donc je coche. Un libelle qui rassure au moment
ou il faudrait faire hesiter est pire qu'un libelle absent.

*Ecarte aussi* : un `(careful!)` en fin de ligne. La lectrice a deja lu
l'action et decide ; un avertissement final se lit comme une politesse. Un
marqueur en tete change la lecture, un marqueur en queue la commente.

Le miroir avec le champ voisin tient : **INTENDED REMOVAL** contre **EMERGENCY
ONLY** — ce qu'on affirme d'un cote, ce qu'on subit de l'autre. Le rendement du
rétrécissement de portee est assume : le drapeau couvre « j'ai compris cette
perte et je l'assume », ce qui n'est pas toujours une suppression voulue. Ce
rétrécissement joue dans le bon sens — il rend le drapeau inconfortable
precisement dans le cas ou il a ete mal employe.

## `nosdeputes_max_pages` retire

Jamais employe autrement que par son defaut. Fige a `--max-pages 5` a l'unique
site qui le lisait, et retire de la reconstruction de `retry-generate-data.yml`
— y compris son extraction depuis les logs, devenue sans consommateur.

Le flag `--max-pages` de `generate_all_profiles.py` reste : la CLI n'a pas a
etre amputee parce que la CI n'en veut plus. Meme raisonnement que
[[workers-fige-a-1]].

## Ce que cet episode apprend

Deux refontes du meme formulaire dans la meme journee, la seconde corrigeant ce
que la premiere n'avait pas vu — parce que la premiere avait ete faite en
lisant le YAML, pas en regardant l'ecran que l'operatrice utilise. Un artefact
d'interface se relit dans son rendu.

