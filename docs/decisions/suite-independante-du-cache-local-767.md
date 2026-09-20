# La suite dit son monde au lieu d'en hériter (#767)

`2026-09-10`

> **En bref** — treize tests passaient ou échouaient selon qu'un répertoire de cache **local** existait, `.cache/acteurs_historique_an/` : **verts en CI** dont le checkout est vide, **rouges chez la propriétaire** au moment précis où elle vérifie qu'elle n'a rien cassé ; **ma première re-mesure était fausse** — j'avais lié `.cache` par un **lien symbolique**, or le garde-fou de #721 compare des chemins **résolus**, si bien que ma reproduction avait désarmé le contrôle qu'elle prétendait exercer, et j'ai annoncé « 1 échec, pas 13 » avant de retrouver les treize avec une vraie copie ; **le garde-fou n'était pas en cause** — il diagnostique en nommant le fichier lu et l'idiome à appliquer, et son commentaire dit qu'il ne redirige pas **exprès**, une redirection globale ayant été essayée puis écartée parce qu'elle casse les dix tests qui isolent par `chdir` ; d'où une fixture `autouse` **par fichier**, qui pointe `ACTEURS_HISTORIQUE_CACHE_DIR` vers un répertoire jetable **et vide le mémo de module aux deux bouts** — `_ACTEURS_HISTORIQUE_INDEX_MEMO` est un `dict` partagé qui, rempli par un test voisin, rend le vrai référentiel **sans rouvrir un fichier**, donc sans que le garde-fou puisse le voir. Vérifié **dans les deux mondes** : 4 372 passés cache présent, 4 372 passés cache absent — un correctif vert d'un côté et rouge de l'autre n'aurait fait que déplacer la dépendance. Ne traite pas #791, même famille sur `raw_data/*.json`, rencontrée trois fois aujourd'hui.

## Contexte

La suite passait ou échouait selon qu'un répertoire de cache **local** existait.
Treize tests, un seul répertoire : `.cache/acteurs_historique_an/`.

**Verts en CI, rouges chez la propriétaire.** Le job de tests fait un
sparse-checkout sans `.cache/`, et rien ne l'y crée : le défaut ne mord que la
personne qui vient de lancer une collecte — c'est-à-dire au moment précis où
elle vérifie qu'elle n'a rien cassé.

## Ce que la re-mesure a corrigé, et ce qu'elle a confirmé

**Le premier relevé était faux, et pour une raison instructive.** Reproduisant
le défaut dans un worktree, j'y avais lié `.cache` par un **lien symbolique**
vers le cache du dépôt. Un seul test échouait alors, et j'ai annoncé « 1 échec,
pas 13 — la mesure de l'issue a vieilli ».

C'était l'inverse : le garde-fou de #721 compare des chemins **résolus**, et un
lien symbolique sortait le fichier de son périmètre. Ma reproduction avait
désarmé le contrôle qu'elle prétendait exercer. Avec une vraie copie du cache,
les treize échecs sont là, exactement comme l'issue les décrivait — douze dans
`test_generate_all_profiles.py`, un dans `test_pivot_nom_resolutions_788.py`.

## Le garde-fou n'était pas en cause

`conftest` diagnostique correctement : il lève `CacheDuPosteLuDansUnTest` en
nommant le fichier lu et l'idiome à appliquer. Son commentaire le dit
lui-même — « ce garde-fou DIAGNOSTIQUE, il ne redirige pas », et rediriger
globalement avait été essayé puis écarté, parce que dix tests isolent déjà leur
cache par `monkeypatch.chdir(tmp_path)` et qu'une constante rendue absolue le
leur retire.

Ce qui manquait n'était pas le contrôle : c'était l'idiome, dans deux fichiers.

## Décision

Une fixture `autouse` par fichier concerné, qui pointe
`candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR` vers un répertoire jetable.

**Par fichier et non globalement**, pour la raison déjà mesurée par #721 : une
redirection globale casse les dix tests qui isolent par `chdir`.

**Le mémo de module est vidé aux deux bouts.**
`_ACTEURS_HISTORIQUE_INDEX_MEMO` est un `dict` partagé : rempli par un test
voisin, il rend le vrai référentiel **sans jamais rouvrir un fichier**, donc
sans que le garde-fou puisse le voir. Isoler le chemin sans vider le mémo aurait
laissé passer le cas le plus difficile à diagnostiquer.

## Effet vérifié, dans les deux mondes

| Condition | Avant | Après |
| --- | --- | --- |
| `.cache/acteurs_historique_an/` présent | **13 échecs** | **4 372 passés** |
| Répertoire absent (condition CI) | 4 372 passés | **4 372 passés** |

C'est la seule vérification qui compte ici : un correctif qui rendrait la suite
verte avec le cache et rouge sans lui n'aurait fait que déplacer la dépendance.

## Ce que ce lot ne fait pas

Il ne traite pas #791 — `conftest` refuse `.cache/` et le réseau, mais pas les
lectures de `raw_data/*.json`, que 23 fichiers de tests citent. C'est la même
famille (un test qui hérite de l'état du poste au lieu de le dire) sur une autre
couche, et je l'ai rencontrée trois fois aujourd'hui : déclarer un groupe dans
`groupes_reels.json` a fait échouer des tests qui lisent la configuration
réelle.
