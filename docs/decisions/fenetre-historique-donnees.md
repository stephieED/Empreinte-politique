<a id="fenetre-historique-donnees"></a>
# Borner l'historique de données : ce que ça rend vraiment, et quand (#434) (2026-08-20)

`2026-08-20`

> **En bref** — squash déclenché par la mesure, jamais de réécriture automatique.

Décision : **option D**, borner l'historique de données plutôt que son contenu.

> **Ce que cette décision ne tranche pas.** Ses quatre options partent toutes de la même hypothèse : la donnée est versionnée dans le dépôt. **Pourquoi** elle y est n'a été écrit que le 30/08/2026 — voir [`donnees-versionnees-integrite.md`](donnees-versionnees-integrite.md). Un lot de volumétrie qui rencontre cette contrainte doit la peser contre l'intégrité de ce que le site montre, jamais contre le confort.
Variante retenue : **squash déclenché par la mesure, fenêtre de 30 commits de
données**, jamais de réécriture automatique. Rien à exécuter aujourd'hui — le
dépôt porte 23 commits de données, la fenêtre n'est pas contraignante.

Ce qui suit est mesuré sur un **clone** du dépôt (`git clone --mirror
--no-hardlinks`), `main` = `0466957`, le 20/08/2026 à 12:00. Aucune mesure n'a
été prise sur l'arbre de travail réel, et aucun historique réel n'a été
réécrit.

## Le dépôt pèse trois chiffres différents, et un seul compte

| mesure | valeur |
| --- | --- |
| `.git` sur disque | 853 Mo |
| `git rev-list --disk-usage --objects --all` | 386 Mo |
| **après `gc --prune=now`** | **284 Mo** |
| annoncé par l'API GitHub (`repos/…/.size`) | 395 Mo |

Les 853 Mo ne sont pas de l'historique : 569 Mo sont des objets **devenus
inaccessibles** par les rebases et les pushs forcés de la journée. Et
`rev-list --disk-usage` lui-même surestime — il additionne la représentation
*actuelle* de chaque objet, répartie sur 12 packs mal compactés. Le seul
chiffre comparable aux seuils GitHub est celui d'après repack : **284 Mo**,
soit 5,5 % du seuil recommandé de 5 Go.

L'écart avec les 395 Mo annoncés par GitHub est le même phénomène, côté
serveur : 111 Mo (39 %) de résidus que nous ne pouvons pas faire ramasser.
GitHub annonçait 275 Mo dans un commentaire de #434 la veille ; la hausse de
120 Mo en une journée n'est pas de la donnée, c'est le prix des pushs forcés
déjà faits.

## La contrainte annoncée n'existe pas, et c'est la principale correction

Le dimensionnement de la fenêtre devait être choisi **pour
`audit_diff_profils.py`**, au motif qu'il « compare à une ref git » et qu'une
fenêtre trop courte le priverait de point de comparaison.

**Lu dans le code, il ne dépend d'aucune profondeur d'historique.** Il fait
`git ls-tree --name-only <ref>:<répertoire>` puis `git cat-file --batch` sur
`<ref>:<répertoire>/<fichier>` : il lit **un arbre**, celui de la ref, et rien
d'autre. Aucun parcours de commits, aucun `log`, aucun `diff`. Avec
`--ref HEAD` — le choix fait en #461, et le seul juste hors `main` — il lui
faut exactement **un commit**.

C'est cohérent avec le reste : aucun `fetch-depth` n'est fixé dans
`generate-data.yml`, donc les 9 `actions/checkout` du workflow clonent déjà à
la **profondeur 1**. Le garde-fou qui aurait attrapé l'effacement des 789
interventions tourne aujourd'hui sur un clone d'un seul commit. Aucune fenêtre
≥ 1 ne peut le priver de quoi que ce soit.

Les trois mécanismes défendus dans #434 se vérifient de la même façon, et
tiennent :

| mécanisme | ce dont il dépend réellement |
| --- | --- |
| fusion additive (`merge_raw_profile`) | `json_path.exists()` puis lecture du fichier |
| `--skip-existing` | `json_path.exists()` |
| `--refresh-existing` (`_select_existants`) | `(out_dir / f"{slug}.json").exists()` |
| `build_scrutins_index.py` | `--profils-dir raw_data/profiles` au HEAD |
| `build_amendements_index_pivot.py` | `--profils-dir raw_data/profiles` au HEAD |

**Présence du fichier au HEAD, jamais profondeur d'historique.** C'est ce qui
rend l'option D viable, et ce n'est pas une supposition.

## Ce qui dimensionne vraiment la fenêtre : la latence de détection

Reste un consommateur réel de profondeur : la **restauration après incident**.
#463 et #464 ont utilisé `git show a125e9e^:…` et `git show e4d71cf^:…` —
respectivement le 2e et le 1er commit de données depuis le sommet. C'est peu,
mais c'est le mauvais chiffre à retenir : ce qu'il faut couvrir n'est pas la
profondeur des incidents passés, c'est le **délai avant qu'on les remarque**.

Deux mesures :

- **cadence de pointe : 4 commits de données par jour** (18/08 et 19/08/2026) ;
- **latence de réparation de l'incident le plus grave** : `a125e9e` committé le
  19/08 à 19:32Z, interventions restaurées le 20/08 à 08:32Z — 13 h. Et la
  réparation n'était pas finie : le 20/08 à midi, `#468` puis `#469`
  restauraient encore des mandats, des textes portés, puis un parti effacé par
  les restaurations elles-mêmes. Le sillage forensique d'un incident se compte
  en jours, pas en heures, et il est itératif.

D'où la règle : **fenêtre = cadence de pointe × période sans surveillance**.
4 × 7 jours = 28, arrondi à **30**. Une semaine d'absence, à la cadence la plus
forte jamais observée, reste réparable.

À pleine échelle (752 profils), cette fenêtre plafonne le dépôt à environ
**2,9 Go** — socle projeté 457 Mo + 30 × 81 Mo de coût moyen par run. Sous le
seuil recommandé, avec de la marge. C'est ça, l'objet de l'option D : un
plafond, pas un gain.

## Le coût par run : c'est la distribution, jamais la moyenne

Sur les 8 runs les plus récents :

| | Mo |
| --- | --- |
| médian | 12,6 |
| moyen | 20,2 |
| minimum | 0,2 |
| maximum | 53,5 |

**Un facteur 4 entre la médiane et le maximum.** Les deux runs chers
(`a125e9e`, `25f7bc7`) sont des propagations en `--no-merge`, structurellement
exceptionnelles. Une moyenne seule dimensionnerait la fenêtre sur un run qui
n'existe pas.

Et la distribution ne porte **que** sur les runs récents. Étendue aux 23
commits de données, la médiane tombe à 2,6 Mo et l'écart min/max grimpe à
× 1 790 — parce que les plus anciens décrivent un corpus de 14 à 30 profils.
Un chiffre qui ne décrit aucun run existant.

## Le gain réel, mesuré variante par variante

Taille du dépôt après réécriture *et* `gc --prune=now`, sur le clone :

| fenêtre | 0 | 1 | 2 | 3 | 4 | 6 | 8 | 10 | 15 | 20 | 23 (tout) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dépôt | 127 | 169 | 175 | 218 | 246 | 258 | 259 | 280 | 280 | 283 | **284** Mo |

**La courbe sature à partir de ~10.** Tout ce qui précède le 10e commit de
données vaut moins de 2 % du dépôt : ces commits ont été écrits quand le corpus
faisait 14 à 30 profils. À 23 commits de données pour une fenêtre de 30,
**l'opération ne retirerait rien aujourd'hui**.

D'où l'écartement des variantes, sur mesure et non sur principe :

- **Fenêtre glissante appliquée à chaque run** — écartée : gain mesuré nul
  aujourd'hui, pour un push forcé par run. Le rapport risque/bénéfice est le
  pire des quatre.
- **Branche orpheline périodiquement écrasée** — écartée malgré le meilleur
  gain (127 Mo, −55 %). Elle détruit l'historique du **code**, donc `git log`
  et `git blame` sur `src/`, et les 27 SHA cités dans ce journal cessent de
  résoudre. Le journal de décision est la mémoire du projet ; l'échanger contre
  157 Mo est un mauvais troc.
- **Élagage des seuls répertoires de données dans les vieux commits** (garder
  tous les commits, retirer les blobs) — séduisante parce qu'elle préserve
  toute l'archéologie du code. Écartée pour deux raisons : elle exige
  `git-filter-repo`, absent de l'environnement, et la saturation ci-dessus
  borne son gain aux mêmes < 2 %. Elle change d'ailleurs tous les SHA elle
  aussi.
- **Squash déclenché par la mesure** — retenue. C'est la seule dont la
  fréquence s'ajuste au problème : elle ne s'exécute que quand la fenêtre
  devient contraignante *et* que le gain mesuré le justifie.

## Le piège du majorant : × 15 d'écart

La tentation est d'estimer le gain en additionnant ce qu'ont coûté les commits
hors fenêtre. C'est faux, et largement :

| fenêtre | somme des coûts par run | **gain réel mesuré** | écart |
| --- | --- | --- | --- |
| 10 | 93 Mo | **6 Mo** | × 15 |
| 3 | 254 Mo | **115 Mo** | × 2,2 |

La raison est structurelle : le squash conserve l'**arbre complet** à la
coupure, et les objets des commits retirés sont majoritairement des deltas dont
la base doit de toute façon être gardée. `audit_volumetrie_profils.py` publie
donc ce total sous le nom de *majorant*, avec l'avertissement à l'endroit exact
où on lit le chiffre — même correction qu'en
[[volumetrie-arbre-de-travail-nest-pas-depot]]. **Le seul gain fiable se mesure
en repackant un clone.**

## Trois pièges rencontrés en mesurant, tous silencieux

1. **`git replace --graft` ne suffit pas.** `main` porte des commits de merge
   dont le second parent plonge avant la coupure : greffer le seul commit de
   coupure laisse tout l'ancien historique atteignable par un autre chemin.
   Mesuré : 677 commits avant la greffe, 677 après. D'où le rejeu explicite qui
   remappe **tous** les parents (677 → 20 commits à la fenêtre 3).
2. **Les index bitmap sont calculés sur le graphe non greffé**, et `rev-list`
   les utilise en priorité. Sans `-c pack.useBitmaps=false`, la vérification
   rend le résultat d'**avant** la coupure sans rien signaler.
3. **Les autres refs ré-épinglent l'ancien historique.** Le dépôt local porte
   18 refs, GitHub 3 branches et 1 tag. Une branche oubliée annule tout le
   gain, en silence.

Un quatrième, pour qui vérifie : `git clone` sur un **chemin** local recopie le
répertoire d'objets tel quel, résidus compris. Il faut `--no-local` ou une URL
`file://` pour mesurer ce qu'un serveur sert réellement.

## Ce que l'opération coûte, et ce qu'elle ne rend pas tout de suite

Un push forcé ne libère rien tant qu'un `gc` n'a pas tourné, et **côté GitHub
on ne peut pas en déclencher un**. Mesuré sur un dépôt nu local :

| | |
| --- | --- |
| serveur, historique complet, `gc` fait | 284 Mo |
| après push forcé d'une fenêtre à 3 (169 Mo atteignables) | **284 Mo — inchangé** |
| après `gc --prune=now` | 169 Mo |

Mais il faut séparer deux choses, et la mesure les sépare nettement. Depuis le
**même serveur non ramassé**, un clone passé par le protocole git :

| | |
| --- | --- |
| serveur sur disque, sans `gc` | 284 Mo |
| **clone frais depuis ce serveur** | **218 Mo — déjà borné** |

`upload-pack` reconstruit le pack à partir des seuls objets **atteignables**.
Donc : le coût pour les consommateurs — clone, checkout CI, temps de fetch —
tombe **immédiatement** après le push forcé, sans attendre aucun `gc`. Ce qui
reste haut, c'est l'empreinte disque de GitHub et le `size` de son API, dont la
date de ramassage n'est ni annoncée ni déclenchable. Le « plafond » de l'option
D est donc réel pour le quota affiché, et **inexistant pour l'usage**.

Le reste du prix, lui, est immédiat et entier :

- **tous les SHA changent** à partir de la coupure, y compris ceux des commits
  conservés — leur ascendance change, donc leur hachage. Les 27 SHA cités dans
  ce fichier et ceux cités dans les issues cessent de résoudre. Archiver
  l'ancien `main` **ailleurs** est la seule parade : le garder en tag dans le
  même dépôt le rendrait atteignable, et le gain serait nul.
- **tout clone existant est invalidé.** Un `git pull` dessus recrée l'ancien
  historique et peut le repousser.
- **un push forcé ne doit jamais croiser un run de données** : le run
  committerait sur un historique qui n'existe plus.

## Pourquoi ce n'est pas automatisé

#434 demandait de peser l'automatisation, au motif qu'un squash manuel qu'on
oublie ne vaut rien. La mesure tranche dans l'autre sens.

Ce qui est automatisé, c'est la **détection** : `audit_volumetrie_profils.py`
dit désormais si la fenêtre est contraignante, avec la distribution du coût par
run et le majorant assorti de son avertissement. Ce qui ne l'est pas, c'est la
**réécriture**. Trois raisons, toutes constatées :

1. Les trois pièges ci-dessus produisent chacun un résultat **faux et
   silencieux** — un gain nul présenté comme un succès. Un script qui pousse en
   force sur la foi d'une telle mesure est plus dangereux que l'oubli qu'il
   corrige.
2. Le dépôt a de l'**activité concurrente** : pendant cette mesure, une autre
   session committait les restaurations de #468 et #469, et `origin/main` a
   avancé trois fois en une heure. Un `schedule:` qui pousse en force ne peut
   pas savoir qu'il écrase du travail en cours.
3. Le gain est **nul aujourd'hui**. Automatiser une opération irréversible pour
   qu'elle ne rende rien, ce n'est pas de la prévoyance.

`scripts/borner_historique_donnees.sh` est donc à deux modes, et **ne pousse
jamais** : `--mesurer` clone dans un répertoire temporaire et rend le gain réel
sans rien toucher ; `--preparer` écrit une branche locale et un tag de
sauvegarde, vérifie, puis affiche les commandes de push à exécuter à la main,
dans l'ordre, avec leurs points de non-retour.

La vérification qui compte tient en une ligne, et le script la fait :
**l'arbre du sommet doit être identique avant et après**. Un arbre git est un
hachage récursif de tout le contenu ; s'il coïncide, chaque fichier coïncide.
C'est une preuve, pas un sondage.

## Traçabilité (AGENTS.md §2.2) : aucun obstacle, et il faut le dire

La règle exige que **tout fait publié soit rattaché à une source primaire**.
Elle porte sur le chaînage fait → source, matérialisé dans `sources[]`,
`source_url` et les identifiants AN — tous **dans les fichiers**, au HEAD.

L'historique git de `raw_data/profiles` et `pivot_data/profiles` n'est pas une
source : ce sont des fichiers **dérivés**, reconstructibles depuis les APIs
publiques, et aucun champ publié ne référence un commit. Squasher les vieux
commits ne retire donc **aucun lien de traçabilité** : après l'opération, tout
profil au HEAD porte exactement les mêmes `sources[]` qu'avant — c'est ce que
prouve l'identité de l'arbre du sommet.

Ce qui est perdu est d'une autre nature : la capacité de **rejouer l'historique
d'un fichier dérivé** — de l'archéologie de pipeline, utile (c'est ce que #463
et #464 ont fait) mais qui ne relève pas de §2.2. C'est précisément ce que la
fenêtre de 30 protège, et c'est pour ça qu'elle est dimensionnée sur la latence
de détection.

**§2.2 ne fait pas obstacle à l'option D.** Je n'ai pas trouvé de lecture qui
conduise à l'inverse.

