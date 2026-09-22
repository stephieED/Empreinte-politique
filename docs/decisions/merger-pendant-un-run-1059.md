<a id="merger-pendant-un-run-1059"></a>
# Une PR qui touche `src/` se merge pendant un run : la règle est tombée avec l'épinglage (#1059) (2026-09-21)

`2026-09-21`

> **En bref** — « Une PR touchant `src/` pendant un run = à ne pas merger » protégeait d'un run qui mêlait deux états du code. Depuis #1059, le run épingle le SHA du privé à son départ : la règle n'a plus d'objet, arbitré le 21/09/2026. Seule reste l'exception des deux fichiers que le dépôt public lit chez lui.

## Contexte

`AGENTS.md` §9 demandait d'écrire « do not merge » en tête d'une PR touchant
`src/` ou `raw_data/*.json` poussée pendant un run : le run committait des
données construites par le code de son départ, et un merge sous lui mêlait deux
états. Une garde, `GENERATION_CODE_CHANGED_DURING_RUN`, annulait le commit.

Depuis #1059, le job `epingler-le-code` résout `main` du privé **une fois**, et
chaque job superpose ce SHA : un merge pendant le run n'atteint pas ce run. La
garde a été retirée dans le même lot.

## Décision

Arbitrage de la propriétaire, 21/09/2026 : « La règle pr touche a src pendant
run = ne pas merger tombe. »

Ce qui reste, et qui se dit en tête de PR : **`generate-data.yml` et
`.github/actions/code-du-prive/` sont lus sur le dépôt public**, pas épinglés.
Une PR qui les touche se publie à la main avant le run qui doit l'utiliser
(`docs/decisions/publication-manuelle-du-workflow-1059.md`).

## Alternative rejetée

**Garder la règle par prudence** : elle bloquait des merges sans rien protéger,
et une règle sans objet apprend à ignorer les règles.
