"""Garde-fou : rien ne se définit APRÈS le bloc d'exécution d'un module.

Le défaut, mesuré le 15/09/2026 sur le run 34970587091. `_verser_mandats_locaux`
était définie ligne 2169 de `src/generate_all_profiles.py`, quatre lignes après
`if __name__ == "__main__": main()`. Python lit le module de haut en bas :
lancé comme script, il exécute `main()` AVANT d'évaluer la `def` qui suit, et
chaque profil est tombé sur `name '_verser_mandats_locaux' is not defined` —
409 profils en erreur, le job coupé, zéro mandat local versé au pivot.

CE QUE LA SUITE DE TESTS NE POUVAIT PAS VOIR, et c'est le cœur du problème :
importé, le module ne prend pas cette branche. `__name__` vaut
`generate_all_profiles`, `main()` n'est pas appelée, la `def` est évaluée
normalement — la fonction existe, le test qui l'appelle passe. Les 5 197 tests
étaient verts pendant que le corpus ne recevait rien. Seule la STRUCTURE du
fichier porte le défaut, jamais son comportement à l'import : il fallait donc un
test qui lise la structure.

Portée volontairement étroite (#737 : une garde trop large finit désarmée) :
seules les définitions de haut niveau — `def`, `class`, `async def` — sont
refusées après le bloc. Une constante, un `atexit.register`, un log de fin
restent permis : ils s'exécutent, ils ne manquent pas à un appel plus haut.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
MODULES = sorted((RACINE / "src").glob("*.py"))

DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _ligne_du_bloc_execution(arbre: ast.Module) -> int | None:
    """Ligne du `if __name__ == "__main__":` de haut niveau, s'il existe."""
    for noeud in arbre.body:
        if not isinstance(noeud, ast.If):
            continue
        test = noeud.test
        if (
            isinstance(test, ast.Compare)
            and isinstance(test.left, ast.Name)
            and test.left.id == "__name__"
            and len(test.comparators) == 1
            and isinstance(test.comparators[0], ast.Constant)
            and test.comparators[0].value == "__main__"
        ):
            return noeud.lineno
    return None


@pytest.mark.parametrize("module", MODULES, ids=lambda p: p.name)
def test_aucune_definition_apres_le_bloc_execution(module: Path) -> None:
    arbre = ast.parse(module.read_text(encoding="utf-8"))
    ligne_bloc = _ligne_du_bloc_execution(arbre)
    if ligne_bloc is None:
        pytest.skip(f"{module.name} n'a pas de bloc d'exécution")

    tardives = [
        f"{type(n).__name__} {n.name} (ligne {n.lineno})"
        for n in arbre.body
        if isinstance(n, DEFINITIONS) and n.lineno > ligne_bloc
    ]
    assert not tardives, (
        f"{module.name} définit après `if __name__ == \"__main__\"` (ligne "
        f"{ligne_bloc}) : {', '.join(tardives)}. Lancé comme script, le module "
        "exécute son bloc avant d'évaluer ces définitions — elles n'existent "
        "pas pour le code appelé depuis. Les remonter avant le bloc."
    )
