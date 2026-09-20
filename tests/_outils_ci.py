"""Le bloc `sparse-checkout:` de `tests.yml`, lu à un seul endroit.

**Pourquoi un module et pas un test.** Trois lecteurs analysaient le même bloc
avec trois analyseurs différents : `tests/conftest.py` (le hook de diagnostic),
`tests/test_ci_perimetre_sparse_checkout.py` et `tests/test_instructions_agents.py`.
Aucun ne codait la liste en dur — pas de divergence possible sur le *contenu* —
mais le jour où le bloc change de forme, il y avait trois choses à corriger, et
deux d'entre elles échouent en silence : le hook redevient muet, et
`test_instructions_agents` compare des alias à une liste vide.

**Pourquoi ici et pas dans `src/`.** `conftest.py` ne peut pas importer un
module de test (pytest le collecterait, et l'import circulerait), ce qui est
exactement ce qui avait fait dupliquer le code. Une fonction dans `src/` n'a
rien à faire dans le code de production : elle ne sert qu'à la suite. Le
préfixe `_` sort ce fichier de la collecte pytest (`python_files = test_*.py`)
tout en le laissant importable ; `conftest.py` met `tests/` sur `sys.path`
avant de l'importer, donc l'import ne dépend pas de l'`--import-mode` de pytest.

**Ce que la fonction ne fait jamais** : lever. Son premier appelant est un hook
de rapport d'échec, où une exception transformerait un échec de test en erreur
de collecte. `None` veut dire « je n'ai rien pu lire de sûr », et chaque
appelant décide quoi en faire : le hook se tait, les tests échouent.
"""

from __future__ import annotations

from pathlib import Path

#: Racine du dépôt, telle que la voit la suite.
RACINE_DEPOT = Path(__file__).resolve().parents[1]

#: Le seul endroit où la liste blanche existe. Jamais recopiée ailleurs.
WORKFLOW_TESTS = RACINE_DEPOT / ".github" / "workflows" / "tests.yml"

#: Le bloc cherché. Une entrée en notation de flot (`sparse-checkout: [a, b]`)
#: ou un renommage ne correspond pas : la lecture rend `None` plutôt qu'une
#: liste devinée.
MARQUEUR_BLOC = "sparse-checkout: |"


def lire_liste_blanche(workflow: Path | None = None) -> frozenset[str] | None:
    """Les entrées du bloc `sparse-checkout: |`, ou `None`.

    `None` dès que quoi que ce soit cloche — fichier absent ou illisible, bloc
    introuvable, bloc vide. **Jamais une liste fausse** : les lignes retenues
    sont strictement plus indentées que la clé `sparse-checkout:` elle-même, si
    bien qu'un bloc vidé ne peut pas avaler la clé YAML suivante et la faire
    passer pour un chemin (une entrée inventée ferait taire le hook de
    `conftest.py` sur un vrai chemin hors liste).

    Les entrées sont rendues sans `/` de tête ni de queue, telles qu'on les
    compare à un chemin relatif à la racine.
    """
    try:
        chemin = WORKFLOW_TESTS if workflow is None else Path(workflow)
        texte = chemin.read_text(encoding="utf-8")
        debut_marqueur = texte.index(MARQUEUR_BLOC)
        debut_ligne = texte.rfind("\n", 0, debut_marqueur) + 1
        indentation_cle = debut_marqueur - debut_ligne

        entrees: list[str] = []
        for ligne in texte[debut_marqueur:].split("\n")[1:]:
            nu = ligne.strip()
            if not nu:
                continue
            if len(ligne) - len(ligne.lstrip()) <= indentation_cle:
                break  # ligne au niveau de la clé ou au-dessus : bloc terminé
            if nu.startswith("#"):
                continue
            if nu.startswith("- "):
                break  # un élément de liste n'est pas une ligne de scalaire
            entrees.append(nu.strip("/"))
        return frozenset(entrees) or None
    except Exception:
        return None
