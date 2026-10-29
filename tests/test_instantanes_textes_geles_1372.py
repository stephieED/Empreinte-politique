"""Les textes d'un instantané sont gelés (#1372, 29/10/2026).

Un instantané « n'est jamais mis à jour » pour ses faits
(`docs/decisions/chrome-du-site-sur-les-instantanes-1029.md`) : seul le chrome
— bandeau et pied du site — suit le site. Le 29/10/2026, la propriétaire a
autorisé PONCTUELLEMENT à redessiner les quatre articles pour le téléphone, à
une condition : aucun texte, aucun nombre ne change. Une exception, accordée le
même jour : les 34 intitulés des articles du projet de loi de finances pour 2026
ajoutés aux lignes de « Votes par article, député par député » (budget).

Ce test tient la condition : l'ensemble des chaînes de texte de chaque page,
bandeau, pied, `<head>`, styles et scripts exclus, est figé par son empreinte.
Une mise en page peut changer ; un mot ou un nombre qui bouge fait rougir la
suite. Changer un texte d'un instantané demande l'accord de la propriétaire,
puis une nouvelle empreinte ici, avec la raison.
→ `docs/decisions/articles-au-telephone-1372.md`
"""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

DOSSIER = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "public" / "rapports"

EMPREINTES = {
    "2026-09-23-prix-des-carburants.html": "dcdbb4baeb22ca51",
    # + 34 intitulés d'articles du PLF 2026, accord du 29/10/2026.
    "2026-10-04-budget-2026.html": "8a4737383d5cc765",
    "2026-10-09-education-a-l-assemblee.html": "8272090c0be5802f",
    "2026-10-13-violences-sexuelles-et-sexistes.html": "390c6b9d76979cc0",
}


class _Textes(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.textes: list[str] = []
        self._ignore = 0

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: ANN001
        if tag in ("style", "script"):
            self._ignore += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script") and self._ignore:
            self._ignore -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            t = re.sub(r"\s+", " ", data).strip()
            if t:
                self.textes.append(t)


def textes(source: str) -> set[str]:
    source = re.sub(r"<!--chrome:(bandeau|pied)-->.*?<!--/chrome:\1-->", "", source, flags=re.S)
    source = re.sub(r"<head>.*?</head>", "", source, flags=re.S)
    lecteur = _Textes()
    lecteur.feed(source)
    return set(lecteur.textes)


def empreinte(source: str) -> str:
    return hashlib.sha256("\n".join(sorted(textes(source))).encode()).hexdigest()[:16]


@pytest.mark.parametrize("nom", sorted(EMPREINTES))
def test_les_textes_d_un_instantane_ne_bougent_pas(nom: str) -> None:
    page = DOSSIER / nom
    assert page.is_file(), f"{nom} a disparu"
    assert empreinte(page.read_text(encoding="utf-8")) == EMPREINTES[nom], (
        f"un texte de {nom} a changé : un instantané garde ses faits. "
        "Si la propriétaire l'a accordé, recalculer l'empreinte et dire pourquoi."
    )

