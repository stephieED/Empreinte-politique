"""Un article se publie avec sa mise en page de téléphone (#1372, 29/10/2026).

Les quatre premiers articles de `/rapports` ont été publiés vérifiés à
l'ordinateur seulement : à 390 px, ils débordaient de l'écran, onze figures
défilaient de côté et des textes descendaient à 5 px. Ils ont été repris après
coup (`docs/decisions/articles-au-telephone-1372.md`), et la propriétaire a
demandé que l'affichage au téléphone soit vérifié pour chaque article à venir
(règle dans `docs/regles/textes-publies.md`).

Ce test ne voit pas l'écran : il tient seulement le minimum vérifiable sans
navigateur — chaque article porte, HORS du style commun du chrome, son propre
bloc `@media (max-width: 720px)`. Un article sans bloc téléphone n'a pas été
pensé pour le téléphone. Le reste — débordement, figures qui défilent,
textes sous 13 px — se contrôle à l'écran, à 390 et à 360 px.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "public" / "rapports"
BLOC_TELEPHONE = re.compile(r"@media\s*\(\s*max-width\s*:\s*720px\s*\)")


def articles() -> list[Path]:
    return sorted(p for p in DOSSIER.glob("*.html") if not p.name.startswith("_"))


def hors_chrome(source: str) -> str:
    """Le style commun (entre `/*chrome:style*/` et `/*/chrome:style*/`) porte
    déjà son propre bloc téléphone : il ne compte pas pour l'article."""
    debut, fin = source.find("/*chrome:style*/"), source.find("/*/chrome:style*/")
    if debut < 0 or fin < 0:
        return source
    return source[:debut] + source[fin:]


def test_il_y_a_des_articles() -> None:
    assert articles(), "aucun article publié : le dossier a-t-il bougé ?"


@pytest.mark.parametrize("article", articles(), ids=lambda p: p.name)
def test_chaque_article_porte_sa_mise_en_page_de_telephone(article: Path) -> None:
    source = hors_chrome(article.read_text(encoding="utf-8"))
    assert BLOC_TELEPHONE.search(source), (
        f"{article.name} n'a pas de bloc @media (max-width: 720px) à lui : "
        "vérifier l'article à 390 et à 360 px avant de le publier "
        "(docs/regles/textes-publies.md)."
    )
