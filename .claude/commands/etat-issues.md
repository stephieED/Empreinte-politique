---
description: Synthèse des issues ouvertes par milestone et par priorité, en tableaux — version Empreinte politique
allowed-tools: Bash(git fetch:*), Bash(git log:*), Bash(git status:*), Bash(git rev-parse:*), Bash(git branch:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh pr list:*), Bash(gh pr view:*), Bash(gh api:*), Read, Grep, Glob
---

Produis une synthèse des issues ouvertes, groupée par milestone et ordonnée par priorité.

## 1. Rafraîchis l'état avant toute affirmation

N'affirme rien depuis le contexte de la conversation ni depuis un fichier de suivi : les deux sont périmés plus souvent qu'on ne le croit. Commence toujours par :

- `git fetch --prune --quiet` — sans `--prune`, les références de branches distantes supprimées ailleurs restent affichées et produisent un rapport faux ;
- `git log --oneline -1 origin/main` et `git status -sb` ;
- `gh issue list --state open --limit 60 --json number,title,milestone,labels` ;
- `gh pr list --state open` — une PR ouverte change l'état d'une issue.

## 2. Rends le résultat en tableaux, jamais en prose sectionnée

**Un tableau par milestone**, dans cet ordre de colonnes :

| Rang | Issue | Sujet | État | Ce qui bloque |

- **Rang** : l'ordre dans lequel tu lancerais les chantiers, pas une urgence absolue. Deux issues parallélisables partagent le même rang.
- **Issue** : le numéro seul, `#553`.
- **Sujet** : un titre **court**, 3 à 6 mots, qui dit de quoi il s'agit sans que l'utilisatrice ait à ouvrir l'issue. **Ce n'est pas le titre GitHub tronqué** — les titres de ce dépôt sont longs et portent souvent leur constat chiffré. Réécris-le : « fraîcheur du cache AN », « refonte CandidateProfile », « rétention de l'historique ». Jamais de coupure à mi-mot ni d'ellipse.
- **État** : où en est concrètement le travail — « prêt », « agent en cours », « PR #N fusionnée, reste X », « needs-human ». Pas un statut GitHub, qui est déjà connu.
- **Ce qui bloque** : « rien » si rien ne bloque. Une dépendance se nomme par son numéro.

Termine par un tableau **« Ce qui est actionnable tout de suite »** : les issues dont la colonne « ce qui bloque » vaut « rien », ordonnées, **avec la même colonne Sujet** et une raison courte pour chacune.

## 3. Signale les anomalies de rangement

Après les tableaux, en quelques lignes seulement :

- les issues ouvertes **sans milestone**, et celui que tu proposerais ;
- les milestones **sans issue ouverte dont l'objectif n'est pas atteint** — un axe que plus rien ne suit est un angle mort, pas un axe terminé ;
- les épics dont toutes les sous-issues sont closes et qui pourraient se fermer ;
- tout document de cadrage du dépôt — feuille de route, corps d'épic, index de décisions — dont tu constates qu'il **contredit l'état mesuré** : dis lequel et sur quel point.

## 4. Confronte les constats de cadrage du dépôt

> **Cette version est celle d'Empreinte politique.** Elle prend le pas sur la
> version générale de `~/.claude/commands/etat-issues.md` pour ce dépôt
> uniquement. Ce §4 est la seule section qui diffère : elle nomme les fichiers
> au lieu de dire où les chercher. Toute autre correction se fait **dans les
> deux**.

**Ne mets plus à jour de tableau d'issues dans `ROADMAP.md`.** Il n'y en a plus, et
c'est délibéré : un tableau qui recopie l'état de GitHub se périme à chaque lot
livré, et un tableau faux est pire qu'un tableau absent — on le croit. La liste
vit dans GitHub ; ta synthèse la rend à la demande.

Ce que `ROADMAP.md` garde, c'est le **pourquoi** : sa section « Constats de cadrage,
à ne pas re-trancher », ses défauts connus, ses renvois vers `docs/decisions/`.
GitHub ne sait pas le tenir, et c'est ce qu'une session qui démarre à froid doit lire.

Depuis le 30/08/2026, **une décision technique = un fichier** sous
`docs/decisions/<ancre>.md` ; `docs/technical_decisions.md` n'en est plus que
l'index, une ligne par décision, de la plus récente à la plus ancienne — c'est là
qu'on lit ce qui s'est décidé récemment sans connaître l'ancre. Une décision
nouvelle s'écrit dans un fichier neuf, jamais insérée dans un fichier existant
(convention : `AGENTS.md` §8). `docs/archive/` porte la version d'avant la
découpe : **ne la citez jamais** — ses ancres sont préfixées `archive-` exprès, et
`tests/test_index_decisions.py` refuse tout chemin qui y pointe.

`docs/decisions-par-module.md` est **généré** : ne le corrigez pas à la main,
relancez `scripts/generer_decisions_par_module.py`.

**Ton travail sur ces fichiers est de les contredire, pas de les recopier.** Après
avoir mesuré l'état, relis ces constats et signale ceux que la mesure infirme :

- un chiffre qui a bougé — ils en portent souvent (comptes, volumétries, SHA) ;
- une dépendance levée, ou une sérialisation qui ne tient plus ;
- un constat rendu faux par un lot livré depuis.

**Un constat périmé est plus dangereux qu'une liste périmée** : il se lit comme du
raisonnement, donc on le croit, et il oriente une décision au lieu d'un tri.

Si tu en trouves un, **dis-le dans ta synthèse** — n'édite pas le fichier de ta
propre initiative. Corriger un constat de cadrage est une décision : il a été écrit
parce qu'il avait coûté quelque chose, et le remplacer suppose de savoir ce qui l'a
rendu faux. Propose la correction, laisse l'arbitrage.

## 5. Discipline

- **Nomme la population de chaque chiffre.** `pivot_data/profiles/` porte **deux** populations qu'un `glob` confond : **13** `candidat_declare`, qui ont une page publiée, et **468** `roster_groupe`, qui alimentent les agrégats et n'en auront jamais. « 5 des 468 membres de roster », jamais « 5 profils ». Un chiffre juste sur la mauvaise population est une erreur, pas une approximation.
- **Ne recopie pas un chiffre depuis une issue ou une doc sans le vérifier** s'il porte ta conclusion. Les issues vieillissent, et une affirmation exacte au moment où elle a été écrite peut ne plus l'être.
- **N'invente aucun classement de priorité** que tu ne saurais justifier en une phrase. Si deux issues sont indépendantes, dis-le plutôt que d'en inventer une.
- Recommande, ne survole pas : si l'utilisatrice ne devait lancer qu'une chose, dis laquelle et pourquoi.
