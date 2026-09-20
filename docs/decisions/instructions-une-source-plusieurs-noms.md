<a id="instructions-une-source-plusieurs-noms"></a>
# Une seule source d'instructions, plusieurs noms de fichiers (#612) (2026-08-30)

`2026-08-30`

> **En bref** — `AGENTS.md` reste le fichier ; `CLAUDE.md` et `.github/copilot-instructions.md` sont des liens symboliques vers lui. Claude Code suit le lien, vérifié ; Copilot non vérifié.

## Contexte

Les outils n'attendent pas le même nom. Claude Code charge `CLAUDE.md` ; GitHub
Copilot lit `.github/copilot-instructions.md`. `AGENTS.md` — la convention
inter-outils, citée **488 fois dans 172 fichiers** de ce dépôt, plus 30 issues
et 52 messages de commit — portait les instructions sans qu'aucun outil ne le
charge automatiquement.

Mesuré le 30/08/2026 : le bloc d'instructions injecté au démarrage d'une session
Claude Code ne contenait que `MEMORY.md`. `AGENTS.md` n'y était pas — un agent
ne le lisait que s'il pensait à l'ouvrir. Il porte pourtant la ligne éditoriale
non négociable (§2), la règle de vérification des sous-agents (§10) et celle sur
ce qu'il faut demander à la propriétaire (§11).

## Décision

`AGENTS.md` reste **le fichier réel**. Les autres noms sont des **liens
symboliques** vers lui.

```
AGENTS.md                          ← la source
CLAUDE.md                       → AGENTS.md
.github/copilot-instructions.md → ../AGENTS.md
```

Verrouillé par `tests/test_instructions_agents.py` (6 cas, vérifié par
mutation) : chaque alias est un lien, il pointe la source, il en rend le
contenu, et il figure dans la liste blanche du sparse-checkout de `tests.yml`.

## Vérifié, et ce qui ne l'est pas

**Claude Code suit le lien.** Constaté le 30/08/2026 sur une session neuve après
la fusion de #613 : `CLAUDE.md` est chargé, et le contexte porte les onze
sections d'`AGENTS.md`. Ce n'est pas une déduction — deux tentatives
antérieures avaient mesuré un arbre de travail périmé et n'avaient rien établi.

**Copilot n'est pas vérifié.** Le lien `.github/copilot-instructions.md` est
posé, son comportement n'a pas été constaté. Il est possible que Copilot lise
`AGENTS.md` nativement, auquel cas le lien est une redondance sans effet.

## Alternative rejetée : une copie synchronisée

Une copie **peut** diverger ; on ne fait que le détecter après coup. Un lien ne
le peut pas — c'est le même objet. La dérive n'est pas surveillée, elle est
impossible.

## Alternative rejetée : renommer `AGENTS.md`

Non à cause des 488 renvois, qui se réécriraient. Garder `AGENTS.md` comme
fichier réel est le choix **robuste à l'incertitude sur Copilot** : s'il lit ce
nom nativement, le lien ne coûte rien ; sinon, il le couvre. Migrer vers un nom
dont on n'est pas sûr, c'est parier le contraire.

## Réserve connue

Sur Windows, `git clone` sans `core.symlinks=true` rend un **fichier texte
d'une ligne** contenant le chemin, pas le lien. Un agent lirait alors
« AGENTS.md » au lieu des instructions, sans que rien ne le signale. Sans
conséquence ici — une mainteneuse et des agents sous Linux — et
`test_chaque_alias_est_un_lien_vers_la_source` le ferait échouer.

## Ce que le test ne garantit pas

Qu'un outil **suive** le lien est une propriété de l'outil, constatable
seulement en l'exécutant. Le test garantit la source unique, pas la lecture.
