<a id="definition-apres-le-bloc-execution-922"></a>
# Une fonction définie après `if __name__ == "__main__"` n'existe pas pour le script (#922) (2026-09-15)

`2026-09-15`

> **En bref** — `_verser_mandats_locaux` était définie quatre lignes **après**
> le bloc d'exécution de `src/generate_all_profiles.py`. Importé, le module la
> porte ; lancé comme script, il appelle `main()` avant de l'évaluer. Le run
> `34970587091` a rendu `name '_verser_mandats_locaux' is not defined` sur
> **409 profils** avant d'être coupé, pendant que les **5 197 tests** étaient
> verts. La fonction remonte avant le bloc, et
> `tests/test_definitions_avant_execution.py` refuse désormais toute `def`,
> `class` ou `async def` de haut niveau qui le suit, dans tout `src/*.py`.

## Contexte

`_verser_mandats_locaux` avait été **nommée pour être testable** — la leçon du
run précédent, `34953770692`, où un versement inline avait écrit le bloc dans les
32 profils bruts sans qu'un seul mandat atteigne `pivot_data/`. Elle l'était :
ses deux cas sont couverts, et ils passent.

Elle a été écrite en fin de fichier, après `if __name__ == "__main__": main()`.
Python lit un module de haut en bas. Lancé comme script, il exécute le bloc —
donc tout `main()` — **avant** d'évaluer la `def` qui le suit.

Mesuré sur le run `34970587091`, lancé le 15/09/2026 à 14 h 43 (Paris) : tous
les jobs d'extraction verts, `merge-and-pivot` en erreur sur chaque profil
normalisé, 409 échecs consignés avant que le runner ne coupe l'étape à
15 h 47. Aucune donnée poussée.

## Pourquoi la suite de tests ne pouvait pas le voir

C'est le point à retenir, et il vaut au-delà de ce lot. **À l'import,
`__name__` ne vaut pas `"__main__"`** : la branche n'est pas prise, `main()`
n'est pas appelée, et la `def` qui suit est évaluée comme n'importe quelle
autre. Un test qui importe le module trouve la fonction et l'appelle sans rien
remarquer.

Le défaut n'est donc **pas dans le comportement du module, il est dans sa
structure** — l'ordre de deux nœuds de haut niveau. Aucun test de comportement
ne peut l'atteindre, quelle que soit sa couverture. Il fallait un test qui lise
le fichier plutôt que de l'exécuter : `ast.parse`, le bloc d'exécution repéré
par son motif, et toute définition de haut niveau dont la ligne le suit.

## Décision

1. La fonction remonte avant le bloc, qui redevient les deux dernières lignes du
   fichier — la disposition de tous les autres modules de `src/`.
2. `tests/test_definitions_avant_execution.py` parcourt chaque `src/*.py`,
   localise le `if __name__ == "__main__"` de haut niveau et refuse toute
   `FunctionDef`, `AsyncFunctionDef` ou `ClassDef` qui le suit. Un module sans
   bloc d'exécution est ignoré.

## Portée du test, et ce qu'il laisse passer

Volontairement étroite. Seules les **définitions** sont refusées : une
constante, un `atexit.register`, un message de fin placés après le bloc
s'exécutent à l'import et ne manquent à aucun appel. Les interdire aurait donné
une garde plus large que le défaut qu'elle répare — la forme exacte de celle qui,
sur #737, refusait « the four pre-commit guards » parce qu'elle interdisait tout
nombre dans `AGENTS.md`, et qu'il a fallu désarmer.

## Alternative écartée

**Lancer le script dans un test, sur un profil jouet, et lire son code de
sortie.** Cela aurait attrapé celui-ci — et rien d'autre, sans y mettre un vrai
corpus. Un sous-processus par module, une fixture de données par script : le
coût est celui d'une suite d'intégration, pour un défaut qui se lit dans
l'arbre syntaxique en une milliseconde.
