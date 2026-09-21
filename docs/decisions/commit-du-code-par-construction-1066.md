<a id="commit-du-code-par-construction-1066"></a>
# Le commit de fin de run publie le code par liste, jamais par exclusion (#1066) (2026-09-21)

`2026-09-21`

> **En bref** — « tout sauf les données » a publié 5,3 Go de sous-produits du run sur le dépôt public ; le code se stage désormais depuis la liste de ce que le dépôt privé porte, avec un second filet qui retire tout le reste.

**Contexte** : le premier run qui publiait code et données ensemble
([[code-du-prive-dans-le-run-1059]]), le 21/09/2026 (`35621418895`), a réussi —
et son commit `7dc120699` portait en plus :

| Publié par erreur | Volume |
| --- | --- |
| `_artifacts/` — les profils bruts téléchargés des shards | **2 100 fichiers, 5,3 Go** |
| huit rapports de contrôle à la racine (`integrite-referentielle`, `diff-profils`, `collecte-vs-publie`, `collecte-non-publiee`, en `.json` et `.md`) | 8 fichiers |

La ligne de commit stageait `git add -A -- . ':(exclude)pivot_data'
':(exclude)raw_data'`, et son commentaire affirmait que « le `.gitignore` écarte
caches et artifacts ». **L'affirmation n'avait pas été vérifiée, et elle était
fausse** : aucune règle ne couvrait ni `_artifacts/` ni les rapports.

Aucune donnée sensible n'est sortie : les rapports ne mentionnent que des comptes
du champ `cohesion_votes`, public au niveau du groupe, et `_artifacts/` duplique
`raw_data/profiles/`. Le risque réel était pour le run suivant, dont le checkout
aurait ramené 5,3 Go de profils périmés là où les artifacts frais sont ensuite
téléchargés.

**Réparation** : la pointe du dépôt public a été remplacée par un commit
identique moins les sous-produits — même parent, mêmes métadonnées, **mêmes
2 732 fichiers de données octet pour octet**, vérifié. L'arbre et le commit ont
d'abord été calculés localement, puis recréés par l'API ; leurs SHA
coïncidaient avant que la référence ne bouge.

**Décision : le code se stage depuis la liste de ce que le privé porte.**

1. L'action de superposition écrit les entrées de tête de l'arbre **source** —
   jamais de l'arbre de travail —, données exclues.
2. Le commit ne stage que ces entrées, `git add -A` couvrant ajouts,
   modifications et suppressions à l'intérieur de chacune.
3. Une seconde passe retire de l'index toute entrée de tête qui n'est ni listée
   ni une donnée. Elle sert d'abord à propager une suppression faite sur le
   privé ; elle **rattrape aussi** tout sous-produit qui aurait été stagé par
   ailleurs.

**Deux filets, chacun suffisant seul**, vérifiés par mutation : en remettant
l'ancienne ligne, seul le garde statique échoue — la seconde passe retire
`_artifacts/` et le rapport ; en retirant la seconde passe, c'est le test de la
suppression qui échoue. Le fragment de shell est **exécuté** par la suite dans un
dépôt jetable où le run dépose exactement ce qu'il dépose en vrai.

**Une liste absente ne se lit jamais comme « tout »** : le code n'est alors pas
committé, et le log le dit.

**Alternative écartée : compléter le `.gitignore` et garder l'exclusion.** Les
règles sont ajoutées quand même, pour un arbre local propre ; mais une liste
d'ignorés se périme au premier sous-produit que personne n'a pensé à nommer, et
c'est exactement ce qui s'est produit. La liste du code, elle, vient de la
source et ne peut contenir que ce que le dépôt privé porte.
