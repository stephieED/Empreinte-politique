"""Les pages de texte : un sommaire à gauche, le titre de chaque carte en marge.

Forme E, arbitrée sur maquette le 21/10/2026, après la colonne commune de
1 600 px (#1318) : dans une colonne aussi large, une carte de texte bornée à
80 caractères par ligne laissait sa moitié droite vide — À propos,
Méthodologie, Mentions légales, FAQ. Le sommaire des fiches est repris à
gauche, et chaque carte met son titre dans une colonne de marge.

Ce que ces garde-fous protègent, pour les pages d'aujourd'hui et celles qui
viendront :

1. **Toute page de texte porte le sommaire** : `StaticPage` le rend, et une
   page qui compose son propre `static-main` (À propos, Sources, Nous soutenir)
   doit le rendre aussi.
2. **Chaque carte se déclare au sommaire** (`data-section`), sans quoi elle
   n'y figure pas — et une carte sans ancre n'y mène nulle part.
3. **Le titre en marge vit dans le cadre commun** (`StaticPage.css`), pas dans
   une page : une page à venir en hérite.

CE QU'ILS NE COUVRENT PAS : le rendu. Il a été joué le 21/10/2026 sur les six
pages de texte à 2 560, 1 440, 1 280 et 390 px.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"


def test_toute_page_de_texte_porte_le_sommaire() -> None:
    static = (SRC / "components" / "StaticPage.jsx").read_text(encoding="utf-8")
    assert "<SommaireSections" in static, "StaticPage ne rend plus le sommaire"
    for page in sorted((SRC / "pages").glob("*.jsx")):
        source = page.read_text(encoding="utf-8")
        if 'className="static-main' in source:
            assert "<SommaireSections" in source, f"{page.name} compose son cadre sans le sommaire"


def test_chaque_carte_se_declare_au_sommaire() -> None:
    static = (SRC / "components" / "StaticPage.jsx").read_text(encoding="utf-8")
    assert "data-section={section.heading}" in static
    assert "data-section={section.famille}" in static and "data-section-groupe" in static
    assert "data-section={section.titre}" in static
    fautes = []
    for page in sorted((SRC / "pages").glob("*.jsx")):
        for balise in re.findall(r"<section\s+className=\"static-card[^>]*>", page.read_text(encoding="utf-8")):
            if "data-section=" not in balise or " id=" not in balise:
                fautes.append(f"{page.name} : {balise}")
    assert not fautes, "carte absente du sommaire :\n" + "\n".join(fautes)


def test_un_bloc_compose_de_methodologie_porte_son_titre() -> None:
    """Un bloc `element` n'a pas de `heading` : sans `titre`, il n'aurait pas
    de nom dans le sommaire."""
    source = (SRC / "pages" / "MethodologyPage.jsx").read_text(encoding="utf-8")
    for ligne in re.findall(r"\{[^{}]*element:[^\n]*", source):
        assert "titre:" in ligne, ligne


def test_le_titre_en_marge_vit_dans_le_cadre_commun() -> None:
    css = (SRC / "components" / "StaticPage.css").read_text(encoding="utf-8")
    assert ".static-card:not(.static-card--figure)" in css
    assert "grid-template-columns: 240px minmax(0, 1fr);" in css
    assert "grid-template-columns: 204px minmax(0, 1fr);" in css, "sommaire : même largeur que sur les fiches"


def test_les_tuiles_du_bandeau_lisent_la_devise_unique() -> None:
    """Forme C du bandeau (21/10/2026) : les tuiles d'À propos sont la devise de
    `Baseline.jsx`, présentée autrement, jamais une seconde copie du texte."""
    baseline = (SRC / "components" / "Baseline.jsx").read_text(encoding="utf-8")
    assert "BASELINE.map" in baseline.split("if (tuiles)")[1].split("return (")[1]
    apropos = (SRC / "pages" / "AboutPage.jsx").read_text(encoding="utf-8")
    assert "<Baseline tuiles" in apropos
    assert "automatisé" not in apropos.split("MANIFESTE")[0], "la devise ne se recopie pas dans la page"
