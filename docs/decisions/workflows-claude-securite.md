<a id="workflows-claude-securite"></a>
# Workflows Claude : garde d'auteur, asymétrie de sandbox levée, marketplace non épinglé (#415) (2026-08-18)

`2026-08-18`

> **En bref** — garde d'auteur sur `issue_comment`, asymétrie de sandbox levée, marketplace non épinglé.

**Contexte** : le dépôt est public et `claude.yml` / `claude-code-review.yml`
se déclenchent tous deux sur `issue_comment`, event qui s'exécute toujours dans
le contexte du dépôt de base, avec accès aux secrets. Ni l'un ni l'autre ne
filtrait l'auteur du commentaire, et les deux fichiers avaient divergé sans
qu'aucune ligne n'écrive pourquoi (cf. [[revue-workflows-ci-342]], qui laissait
la question ouverte).

**Premier constat, qui corrige la prémisse de l'issue** : l'absence de garde
d'auteur n'ouvre **pas** l'usage du `CLAUDE_CODE_OAUTH_TOKEN` à n'importe qui.
`anthropics/claude-code-action` vérifie elle-même que l'acteur déclencheur a le
droit d'**écriture** sur le dépôt — pour les events issue, pull request,
comment et review — et s'arrête avant d'appeler Claude sinon
(`docs/security.md` de l'action). Le seul contournement documenté est
`allowed_non_write_users`, resté à sa valeur par défaut (vide) ici. Le risque
réel n'était donc pas l'exécution d'un prompt hostile, mais la **consommation
de minutes Actions** : un commentaire d'un inconnu démarrait un runner,
installait bubblewrap et les dépendances de l'action avant de se faire refuser.

**Décisions** :

- **Garde d'auteur ajoutée dans les deux `if:`**
  (`contains(fromJson('["OWNER","MEMBER","COLLABORATOR"]'), …author_association)`),
  assumée comme **pré-filtre** et non comme mécanisme de sécurité : elle évite
  le démarrage du runner, la vérification qui fait foi reste celle de l'action.
  Elle est répétée sur chacune des quatre branches de `claude.yml` plutôt que
  factorisée en fin d'expression, parce que `author_association` vit dans
  `.comment`, `.review` ou `.issue` selon l'event : une forme factorisée
  (`a || b || c`) reposerait sur le déréférencement d'objets absents.
  `COLLABORATOR` inclut un invité en lecture seule — accepté, puisque ce n'est
  pas cette garde qui décide.
- **L'asymétrie de `github_token` / `permissions` / `--allowed-tools` est
  confirmée volontaire**, et désormais écrite en en-tête des deux fichiers :
  `claude.yml` reçoit un prompt arbitraire *et* un `WORKFLOW_PAT` en écriture,
  donc défense en profondeur proportionnée ; `claude-code-review.yml` tourne un
  prompt fixe avec un token en lecture seule, donc surface d'écriture nulle et
  aucune raison de brider les outils du plugin de review.
- **L'asymétrie de sandbox, elle, est supprimée.** `claude-code-review.yml`
  reçoit les mêmes deux étapes de préparation (bubblewrap/socat, contournement
  AppArmor d'Ubuntu 24.04+) et le **même** bloc `settings.sandbox` que
  `claude.yml`, allowlist réseau comprise. Raison : le token OAuth Claude est
  présent dans les deux workflows, et celui de review lit du contenu de PR
  potentiellement hostile (diff, titre, description d'une PR de fork) — la
  garde d'auteur n'y change rien, un mainteneur peut légitimement lancer
  `/claude-review` sur une PR externe. Sans isolation réseau, une injection
  réussie exfiltrait ce secret vers un domaine arbitraire. Coût accepté :
  ~20-30 s d'`apt-get` par run de review, et un échec dur si bubblewrap ne
  démarre pas (`failIfUnavailable: true`, même choix que `claude.yml`).
  L'installation du marketplace et du plugin a lieu dans les étapes de l'action,
  avant Claude, donc hors sandbox : elle n'est pas affectée.

*Réserve non levée, refus argumenté* : **`plugin_marketplaces` reste non
épinglé**. Aucune syntaxe de révision n'existe — l'input de l'action valide
l'entrée contre `^https://…\.git$` et se contente de lancer
`claude plugin marketplace add <url>`, qui clone la branche par défaut ; il n'y
a ni argument `--ref` ni forme `url#sha`. Les deux seuls contournements
seraient de vendorer une copie du marketplace dans ce dépôt ou d'en maintenir
un fork, c'est-à-dire déplacer la confiance de « la branche `main`
d'Anthropic » vers « une copie locale à resynchroniser à la main », avec le
risque de la laisser pourrir. Or ce marketplace est le dépôt de l'éditeur de
l'action elle-même, référencée ici par le tag flottant
`anthropics/claude-code-action@v1` : épingler le marketplace en laissant
l'action flotter ne réduirait aucune surface réelle. **Condition de
réouverture** : si `claude-code-action` est un jour épinglée sur un SHA, épingler
le marketplace dans la foulée — sinon la décision devient incohérente.

*Divergences mineures corrigées dans la foulée* :

- `claude-code-review.yml` reçoit `timeout-minutes: 45` (il tournait avec le
  défaut de 360) et un `concurrency` par PR — N commentaires `/claude-review`
  produisaient N runs parallèles sur le même diff. `cancel-in-progress: true`,
  contrairement à `claude.yml` qui sérialise : une review n'écrit rien qu'une
  annulation perdrait, et un second `/claude-review` veut l'état le plus récent
  de la PR, pas deux fois la même review.
- `actions/checkout@v4` → `@v5` dans les deux, alignement sur les quatre autres
  workflows.
- `--allowed-tools` de `claude.yml` nettoyé : une entrée était précédée d'une
  espace parasite (`Bash(python3 -m unittest), Bash(python3:*)`) qui pouvait
  faire échouer son matching, `Bash(pytest:*)` apparaissait deux fois, et les
  quatre variantes `Bash(python3 -m pytest…)` / `Bash(python3 -m unittest)`
  étaient toutes couvertes par `Bash(python3:*)`. Liste ramenée à six entrées
  Bash, couverture inchangée.
- `--model` : le pin est **reconfirmé** (sans lui, le modèle dépend du défaut
  du CLI et de l'abonnement au moment du run, qui peut basculer sur un modèle
  plus petit sans que rien ne le signale dans ce fichier) et **mis à jour** —
  il était resté sur `claude-opus-4-8`, une génération en retard, ce qui est
  précisément la contrepartie du pin. Rendez-vous de revalidation : chaque
  revue de ce fichier.

*Point vérifié, acté tel quel* : le `--append-system-prompt` interdit à Claude
de modifier `claude.yml` et `claude-code-review.yml` — les deux fichiers qui
définissent ses propres privilèges, dont la modification depuis un run Claude
serait une auto-élévation. `generate-data.yml`, `retry-generate-data.yml`,
`deploy-pages.yml` et `debug-network-shutdown-signal.yml` ne sont
volontairement **pas** couverts : workflows de données/déploiement, sans secret
d'élévation, dont toute modification passe de toute façon par une PR relue. La
justification est maintenant écrite à côté du garde-fou pour que la question ne
se repose pas.

