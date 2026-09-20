<a id="bornage-execute-567"></a>
# La coupure d'historique a tourné pour la première fois — et `--preparer` n'avait jamais imprimé sa procédure (#567) (2026-08-28)

`2026-08-28`

> **En bref** — douze tests de motifs textuels ne valaient pas une exécution.

Sous-issue 1 de #566. `tests/test_borner_historique_donnees.py` comptait douze
tests, **tous des recherches de motifs dans le texte du script**. Ils restent
entiers : eux seuls disent que le script ne pousse jamais, qu'il ne réécrit pas
`main`, que sa fenêtre par défaut est celle de l'audit. Mais un refactor qui
garderait les chaînes en cassant la logique les passerait tous, et la coupure
elle-même n'avait jamais été exécutée — ni en test, ni en réel.

`tests/test_borner_historique_execution.py` l'exécute : onze tests, 7 s, sur un
dépôt synthétique monté dans `tmp_path`.

## Le défaut trouvé : `--preparer` sortait en erreur sans rien imprimer

**C'est le résultat principal de ce lot**, et il n'aurait pas pu sortir d'une
recherche de motif. Le bloc d'instructions de `--preparer` vit dans un
`cat <<FIN` **non quoté** : le shell y applique donc substitution de commandes
et de paramètres. Trois expansions involontaires s'y étaient glissées —
`` `full` `` et `` `git remote update` ``, cités comme exemples, étaient
*exécutés* ; `$sha`, variable d'exemple, était sans liaison, et `set -u` tuait
le script **avant la première ligne du bloc**. Mesuré : le mode prépare bien la
branche et le tag, vérifie l'arbre, puis sort en **erreur 1** sans avoir rien
imprimé.

La procédure *est* le livrable de ce mode : c'est là que vivent l'ordre non
négociable (archiver avant de couper) et le retour en arrière. Corrigé par
échappement des trois séquences et des deux `\` de continuation, qui recollaient
trois lignes de la boucle `curl` en une seule ; `$TAG` et `$NEW`, qui doivent
bien être substitués, ne bougent pas. Le test garde désormais la sortie
complète.

## Le mécanisme lui-même est bon

La fixture porte le **piège n° 1** de l'en-tête du script : un merge dont le
second parent plonge avant la coupure. Un test le déclenche pour montrer qu'elle
le porte vraiment — `git replace --graft` du seul commit de coupure laisse le
socle, les deux premiers commits de données et le point de branchement
atteignables, reproduction en miniature des « 677 commits avant, 677 après »
relevés sur le vrai dépôt. Le rejeu explicite, lui, les détache.

Populations, sur le dépôt synthétique (14 commits, dont **10 commits de
données** — sujet portant `MOTIF_COMMIT_DONNEES` —, fenêtre du banc à 3) :

| Vérifié | Résultat |
| --- | --- |
| arbre du sommet, avant vs après | identique, `docs/veine.md` compris — entré par le seul merge |
| commits de données conservés | **3**, exactement la fenêtre, et les trois plus récents |
| SHA d'origine antérieurs à la coupure | tous inatteignables, y compris par le chemin du merge |
| taille du dépôt entier après `gc --prune=now` | **11 Mo → 6 Mo**, et le gain annoncé est celui que deux témoins mesurés à part constatent |

Le « après » est mesuré par un clone `--no-local` de la seule branche bornée :
c'est ce qu'un consommateur reçoit vraiment. Un clone sur *chemin* recopierait
le répertoire d'objets tel quel et rendrait la taille d'avant.

## Le test mord : trois régressions introduites, trois échecs

| Régression introduite | Tests rouges sur 11 |
| --- | --- |
| greffe simple au lieu du rejeu (piège n° 1) | **5** — fenêtre, inatteignabilité, forme du graphe, gain nul |
| greffe + index bitmap sur le graphe non greffé (piège n° 2) | **5**, mêmes |
| autres refs non supprimées avant de mesurer (piège n° 3) | **1** — 11 Mo annoncés « après » là où la branche bornée en pèse 6 |

**Le piège n° 2 ne se reproduit plus tel quel sur git 2.43.** Il ne pouvait pas
être introduit à la lettre : `pack.useBitmaps=false` **n'apparaît nulle part
dans le script**, qui évite le piège par construction en n'utilisant pas de
greffe. Reconstruit dans sa vraie configuration — `repack -adb` puis greffe —,
git rend le même résultat bitmaps actifs ou désactivés (**48 objets
atteignables après greffe contre 68 avant**), parce qu'il refuse d'utiliser les
bitmaps dès qu'une ref de remplacement existe. Le mutant échoue donc par sa
greffe, pas par ses bitmaps. La consigne reste juste pour toute mesure faite
autrement ; elle n'est plus un piège de ce script.

Effet de bord relevé au passage, et devenu une assertion : une `refs/replace/*`
oubliée **change ce que `main` affiche dans tout le dépôt**, sans toucher un
seul SHA — sous le mutant à greffe, `main` ne montrait plus que 6 de ses 10
commits de données.

## Ce que ce lot ne couvre pas

Le push forcé, les refs distantes et la CI après coupure : c'est la répétition
en grandeur réelle (#569), et aucun test unitaire ne l'atteint. Le test ne
touche que son dépôt temporaire — `cwd` est la seule chose qui dise au script
où travailler, `TMPDIR` est replié dans `tmp_path` pour que même le clone de
mesure y reste, et une assertion vérifie que le dépôt réel n'a reçu ni
`main-borne` ni tag d'archive.

