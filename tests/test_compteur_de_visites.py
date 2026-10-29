"""Le compteur de visites (GoatCounter, 29/10/2026).

Choisi par la propriétaire : sans cookie, sans donnée personnelle. Ces gardes
tiennent :

1. l'application et les articles comptent vers la MÊME adresse ;
2. l'application compte chaque changement de page (elle ne recharge pas), une
   fois, et ne plante pas si le script est absent (bloqueur) ;
3. chaque article et l'index des articles portent le script.
"""

from __future__ import annotations

import re
from pathlib import Path

UI = Path(__file__).resolve().parent.parent / "web" / "UI_finale"
ADRESSE = "https://empreinte-politique.goatcounter.com/count"
SCRIPT = f'<script data-goatcounter="{ADRESSE}" async src="https://gc.zgo.at/count.js"></script>'


def test_l_application_et_les_articles_comptent_vers_la_meme_adresse() -> None:
    assert SCRIPT in (UI / "index.html").read_text(encoding="utf-8")
    chrome = (UI / "scripts" / "chrome-instantane.mjs").read_text(encoding="utf-8")
    assert f"export const COMPTEUR = '{ADRESSE}';" in chrome


def test_l_application_compte_chaque_changement_de_page_une_fois() -> None:
    app = (UI / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "<CompteurDeVisites />" in app
    compteur = (UI / "src" / "components" / "CompteurDeVisites.jsx").read_text(encoding="utf-8")
    assert "window.goatcounter?.count?.({ path: chemin })" in compteur
    assert "if (chemin === derniere.current) return;" in compteur


def test_chaque_article_et_l_index_portent_le_compteur() -> None:
    pages = sorted(p for p in (UI / "public" / "rapports").glob("*.html") if not p.name.startswith("_"))
    pages.append(UI / "public" / "rapports.html")
    assert len(pages) > 1
    for page in pages:
        assert re.search(re.escape(f'data-goatcounter="{ADRESSE}"'), page.read_text(encoding="utf-8")), page.name
