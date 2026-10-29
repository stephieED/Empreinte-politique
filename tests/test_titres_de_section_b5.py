"""Les titres de section et la rangée collée, à l'ordinateur (B5, 29/10/2026).

Arbitré sur maquette par la propriétaire : la rangée de pastilles du téléphone
vient à l'ordinateur, collée sous la barre du site, et remplace le sommaire de
gauche sur les quatre fiches ; le titre de section perd la bande J3 et prend un
trait encre court et épais au-dessus. Les pastilles comme titre ont été
écartées : elles ressemblent à un bouton ou à un filtre. Ces gardes tiennent :

1. la rangée lit la page et l'observe, et ne s'affiche pas au téléphone, qui a
   la sienne ;
2. ses entrées sont des liens vers les ancres des sections, « En bref » en tête ;
3. la bande J3 a disparu des feuilles et de ses jetons ;
4. les trois feuilles de titres (candidat, groupe, gouvernement — la
   législature reprend celle du gouvernement) portent le trait B5, et le numéro
   de section n'est plus affiché ;
5. le jaune reste à l'onglet courant : aucun titre de section n'en porte.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "src"
RANGEE = SRC / "components" / "RangeeSections.jsx"
RANGEE_CSS = SRC / "components" / "RangeeSections.css"
FEUILLES = {
    "components/CandidateProfile.css": (".cp-section-tete", ".cp-section-bande"),
    "components/LigneeProfile.css": (".lp-section-tete", ".lp-section-bande"),
    "components/GovernmentProfile.css": (".gvp-section-titre-rang", ".gvp-section-tete"),
}


def sans_commentaires(texte: str) -> str:
    return re.sub(r"/\*.*?\*/", "", texte, flags=re.S)


def bloc(css: str, selecteur: str) -> str:
    debut = css.index(selecteur + " {")
    return css[debut : css.index("}", debut)]


@pytest.fixture(scope="module")
def rangee() -> str:
    return RANGEE.read_text(encoding="utf-8")


def test_la_rangee_lit_la_page_et_l_observe(rangee: str) -> None:
    assert "querySelectorAll('[data-section]')" in rangee
    assert "MutationObserver" in rangee
    assert "disconnect()" in rangee


def test_la_rangee_laisse_le_telephone_a_sa_propre_rangee(rangee: str) -> None:
    assert "const REQUETE = '(min-width: 721px)';" in rangee
    assert "if (!actif || sections.length < 2) return null;" in rangee
    css = sans_commentaires(RANGEE_CSS.read_text(encoding="utf-8"))
    assert "@media (max-width: 720px)" in css


def test_les_entrees_sont_des_liens_vers_les_ancres_en_bref_en_tete(rangee: str) -> None:
    assert "href={s.id === HAUT ? pathname : `#${s.id}`}" in rangee
    assert "[{ id: HAUT, titre: EN_BREF }, ...lues]" in rangee
    assert "aria-current={s.id === courant ? 'true' : undefined}" in rangee


def test_la_rangee_est_collee_sous_la_barre_du_site() -> None:
    css = sans_commentaires(RANGEE_CSS.read_text(encoding="utf-8"))
    regle = bloc(css, ".rangee-sections")
    assert "position: sticky;" in regle
    assert "top: 80px;" in regle


def test_la_bande_j3_a_disparu() -> None:
    for fichier in SRC.rglob("*.css"):
        texte = fichier.read_text(encoding="utf-8")
        assert "j3-bande" not in texte and "j3-filigrane" not in texte, fichier.name


@pytest.mark.parametrize("feuille", sorted(FEUILLES))
def test_le_titre_porte_le_trait_b5_et_plus_le_numero(feuille: str) -> None:
    tete, numero = FEUILLES[feuille]
    css = sans_commentaires((SRC / feuille).read_text(encoding="utf-8"))
    trait = bloc(css, tete + "::before")
    for propriete in ("width: 64px;", "height: 6px;", "background: var(--ink);", "position: absolute;"):
        assert propriete in trait, f"{feuille} : {propriete}"
    regle_numero = bloc(css, numero)
    assert regle_numero.count("display:") == 1 and "display: none;" in regle_numero, feuille


@pytest.mark.parametrize("feuille", sorted(FEUILLES))
def test_le_jaune_reste_a_l_onglet_courant(feuille: str) -> None:
    tete, _ = FEUILLES[feuille]
    css = sans_commentaires((SRC / feuille).read_text(encoding="utf-8"))
    assert "--accent" not in bloc(css, tete)
    assert "--accent" not in bloc(css, tete + "::before")
