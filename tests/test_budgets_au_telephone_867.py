"""La cascade des budgets ne dépasse pas sa carte au téléphone (#867).

Philippe II, trois exercices : 320 px de dessin dans un cadre de 30 px de marge
et de filet, la fiche débordait à 391 px pour un écran de 360 (mesuré le
15/10/2026, Playwright). Le dessin défile désormais dans son cadre.
"""

from __future__ import annotations

from pathlib import Path

COMPOSANTS = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "src" / "components"


def test_la_cascade_des_budgets_ne_depasse_pas_sa_carte():
    code = (COMPOSANTS / "BudgetsDuGouvernement.jsx").read_text(encoding="utf-8")
    assert "calc(100% - 30px)" in code
    assert "padding: 12px 14px" in (COMPOSANTS / "BudgetsDuGouvernement.css").read_text(encoding="utf-8"), (
        "les 30 px retranchés sont la marge et le filet du cadre"
    )
