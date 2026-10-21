"""Les SVG publiés ne contiennent pas de texte en police (21/10/2026).

Un SVG servi par `<img>` ne voit pas les polices de la page : un `<text>`
Manrope y est rendu dans la police installée chez le visiteur. Le logo
s'affichait ainsi en Arial presque partout, et coupait son « e » final chez
qui avait installé Manrope (constaté sous Windows). Les lettres du lockup sont
des tracés ; un SVG redérivé du pack sans cette conversion fait rougir ce test.
→ web/UI_finale/brand-source/README.md
"""

from __future__ import annotations

import re
from pathlib import Path

PUBLIC = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "public"


def test_aucun_svg_publie_ne_contient_de_texte() -> None:
    fautes = [
        str(svg.relative_to(PUBLIC))
        for svg in sorted(PUBLIC.rglob("*.svg"))
        if re.search(r"<text[\s>]", svg.read_text(encoding="utf-8"))
    ]
    assert not fautes, "SVG publié avec du texte en police (le convertir en tracés) : " + ", ".join(fautes)


def test_le_lockup_garde_son_nom_accessible() -> None:
    """Les lettres devenues des tracés, le nom ne se lit plus dans le dessin :
    il est porté par `aria-label`, et par le lien qui entoure l'image."""
    svg = (PUBLIC / "brand" / "empreinte-lockup-light.svg").read_text(encoding="utf-8")
    assert 'aria-label="Empreinte politique"' in svg
