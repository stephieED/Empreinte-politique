# Diagnostiquer le piège du sparse-checkout plutôt que le prévenir (#619, 30/08/2026)

`2026-08-30`

> **En bref** — la liste blanche vaut 8,4 Go non téléchargés et 41 s au lieu de 4 min 30 ; le piège qu'elle crée est diagnostiqué à l'échec, pas prévenu par analyse statique, et un seul analyseur du bloc YAML sert désormais les trois lecteurs.

## Le piège

`.github/workflows/tests.yml` ne matérialise sur le disque du runner qu'une
**liste blanche** de chemins (`sparse-checkout`). Cette liste s'écrit à la main,
donc elle s'oublie. Un test qui lit un fichier hors liste **passe en local et
échoue en CI**, sur un `FileNotFoundError` qui ne dit rien de la vraie cause :
on cherche un bug dans le test pendant que le fichier n'a simplement jamais été
téléchargé.

Trois occurrences, toutes constatées après coup :

| Quand | Ce qui manquait | Comment on l'a su |
| --- | --- | --- |
| #434 | `scripts/borner_historique_donnees.sh` | Les 10 tests du bornage, rouges dès le premier run du workflow |
| #520 | `.gitignore`, lu par `test_ci_roster_unique_par_run.py` | Suite verte en local, rouge sur le push vers `main` (run `32773016491`) — **découvert après fusion sur `main`** |
| 30/08/2026 | `CLAUDE.md`, lu par `test_instructions_agents.py` | Même scénario, une troisième fois |

Les deux dernières fois, l'avertissement était **déjà écrit deux lignes au-dessus**
de la liste qu'on oubliait de compléter. Une prose qui prévient ne prévient
personne.

## Pourquoi la liste blanche existe quand même

Elle n'est pas une contrainte subie : elle achète deux choses mesurées.

| Sans liste blanche | Avec |
| --- | --- |
| 8,4 Go de corpus (`raw_data/profiles/`, `pivot_data/`) téléchargés à chaque run | Non téléchargés |
| Suite en 4 min 30 | Suite en 41 s |
| « Aucun test ne lit le corpus vivant » (#473) : règle **auditée une fois** | Règle **structurelle** — le corpus n'est pas sur le disque |

Le troisième point est le vrai. `tests.yml` porte en plus un garde-fou (#473) qui
échoue si `pivot_data/` ou `raw_data/profiles/` réapparaissent dans le checkout :
la liste blanche ne peut pas être élargie vers le corpus sans que le job le dise.

Le piège est donc le **prix** d'un gain réel, pas un défaut à supprimer. Ce qu'on
peut supprimer, c'est son coût.

## La décision : diagnostiquer, pas prévenir

Le hook `pytest_runtest_makereport` de `tests/conftest.py` ajoute au rapport
d'échec, et seulement dans ce cas, la cause probable : *ce chemin n'est pas dans
le `sparse-checkout` de `tests.yml`*. Il lit la liste depuis `tests.yml`, ne la
recopie jamais, et se tait sur toute autre situation — assertion ordinaire,
chemin couvert, chemin hors du dépôt, liste illisible.

Sur les deux exclusions volontaires (`pivot_data/`, `raw_data/profiles/`) il
parle **et corrige le conseil** : ne pas les inscrire dans la liste, lire une
fixture figée sous `tests/fixtures/`.

### L'alternative écartée : prévenir par analyse statique

Prévenir demande de savoir ce que la suite lira, donc de lire tout le code de
test. Deux tests le font déjà pour la part facile, et cette part-là **échoue en
local** — elle reste la première ligne de défense :

- `tests/test_ci_perimetre_sparse_checkout.py` relève les **littéraux** de chemin
  ancrés à la racine et vérifie que chacun est couvert (et l'inverse : le corpus
  reste hors liste) ;
- `tests/test_instructions_agents.py` fait de même pour ses propres alias.

Pousser l'analyse plus loin — chemins construits en morceaux, `os.path.join`,
chemin passé en variable, indirection par fixture — produirait des **faux
positifs**, et *un garde-fou qui crie pour rien finit désactivé*. On aurait
échangé une panne rare et lisible contre un bruit permanent.

Surtout : le coût réel du piège n'est pas d'y tomber. C'est le temps passé à
chercher au mauvais endroit une fois tombé — les trois fois, la CI disait
« fichier absent » et personne ne lisait « jamais téléchargé ». Le hook supprime
ce coût-là, et rien d'autre. Son public est la personne qui lit un journal de CI
rouge.

### Ce qu'il coûte

Rien sur un test qui passe : la première chose lue est `rapport.failed`.
`tests.yml` n'est ouvert qu'à la première défaillance qui ressemble au piège, et
une seule fois (`lru_cache`). Rien n'est écrit en sortie standard. Une exception
dans le diagnostic est avalée : il ne masque jamais l'échec qu'il commente.

Mesuré sur la suite complète en local, avant et après la mise en commun de
l'analyseur : **31,5 / 35,1 / 35,5 s** pour 2 837 tests avant, **32,1 / 32,3 /
32,5 / 35,9 s** pour 2 857 tests après. Les deux séries se recouvrent : l'écart
entre deux exécutions du même code dépasse l'effet cherché. Pas d'impact
mesurable — ce qui est attendu, le hook ne lisant `tests.yml` qu'à un échec.

## Ce qui verrouille le hook (#620)

Un outil de diagnostic qui cesse de fonctionner **sans le dire** est pire que pas
d'outil : on finit par faire confiance à un silence qui ne veut plus rien dire.
Le hook a été vérifié par mutation à sa création, puis plus rien ne le protégeait.

`tests/test_hook_diagnostic_sparse_checkout.py` le verrouille **sans provoquer
d'échec réel** : il appelle les fonctions internes et pilote le hook — un
`hookimpl(wrapper=True)`, donc un générateur — à la main. Il couvre les six cas
d'origine (parler hors liste ; parler et corriger le conseil sur les deux
exclusions ; se taire sur une assertion, sur un chemin couvert, sur une exception
sans nom de fichier, sur un chemin hors du dépôt), plus le cas « `tests.yml`
illisible → silence, aucune erreur de collecte » et les cas de changement de
forme du bloc YAML.

Son premier test est le préalable : la liste blanche est **effectivement lue
aujourd'hui**. Sans lui, tous les cas « se taire » seraient vrais par vacuité.

## Un seul analyseur du bloc YAML (#620)

Le bloc `sparse-checkout:` était analysé à trois endroits — `tests/conftest.py`,
`tests/test_ci_perimetre_sparse_checkout.py`, `tests/test_instructions_agents.py`
— avec trois analyseurs différents. Aucun ne codait la liste en dur : pas de
divergence possible sur le *contenu*. Le problème était la **forme** : trois
choses à corriger le jour où le bloc change, dont deux échouent en silence (le
hook redevient muet, `test_instructions_agents` compare des alias à une liste
vide).

La contrainte qui avait produit la duplication : `conftest.py` ne peut pas
importer un module de test.

| Option | Coût |
| --- | --- |
| Une fonction dans `src/` | Du code de production qui ne sert qu'aux tests |
| **`tests/_outils_ci.py`**, préfixé donc non collecté par pytest | Un import de voisin depuis `conftest.py` |
| Garder trois analyseurs, documentés | Trois corrections, dont deux muettes |

Retenu : `tests/_outils_ci.py`. `conftest.py` met `tests/` sur `sys.path` avant
de l'importer, ce qui rend l'import indépendant de l'`--import-mode` de pytest et
garantit que les tests importent le **même** objet module. Vérifié en mode
`prepend` (défaut), en mode `importlib`, et depuis `tests/` comme répertoire
courant.

L'analyseur commun a corrigé au passage un défaut que les trois versions
partageaient à des degrés divers : un bloc `sparse-checkout: |` **vidé** faisait
avaler la clé YAML suivante comme si c'était un chemin. Une liste blanche
inventée fait taire le hook sur un vrai chemin hors liste — exactement la panne
silencieuse qu'on cherche à empêcher. Les entrées retenues sont désormais
strictement plus indentées que la clé elle-même, et un bloc qui ne se lit pas
proprement rend `None`, jamais une liste devinée.
