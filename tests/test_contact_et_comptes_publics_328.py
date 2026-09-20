"""Le contact et les comptes publics : les mentions légales, et un rappel discret (#328).

Trois demandes de la propriétaire, le 09/09/2026 : l'adresse de contact devient
`contact@empreinte-politique.fr`, et les deux comptes publics — LinkedIn et X —
sont ajoutés.

**Où.** Les mentions légales font foi : c'est la page que la LCEN désigne, et
c'est là que l'adresse de l'éditeur doit se trouver. Le pied de page les
RAPPELLE en discret, parce qu'une adresse qu'il faut aller chercher dans une
page légale est une adresse qu'on n'écrit pas.

**Une seule adresse dans le dépôt.** `docs/decisions/licences.md` cite le texte
des mentions légales dans son état du 14/08/2026 : cette citation datée n'est
pas réécrite — c'est un enregistrement —, mais elle porte désormais la note qui
dit où se trouve le texte qui fait foi. Une adresse périmée qu'on peut recopier
est pire qu'une adresse absente.
"""

from __future__ import annotations

from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"
LEGAL = SRC / "pages" / "LegalNoticePage.jsx"
# Le pied vit dans son PROPRE composant depuis #328 : il y en avait trois — un
# par carcasse — et celui des pages statiques n'existait pas, ce qui laissait le
# contact absent de la méthodologie, des mentions légales et de la couverture.
PIED = SRC / "components" / "PiedDeSite.jsx"

CONTACT = "contact@empreinte-politique.fr"
LINKEDIN = "https://www.linkedin.com/company/empreinte-politique"
X = "https://x.com/EmpreintePol"


def test_les_mentions_legales_portent_les_trois() -> None:
    source = LEGAL.read_text(encoding="utf-8")
    assert f"mailto:{CONTACT}" in source
    assert LINKEDIN in source
    assert X in source


def test_le_pied_de_page_les_rappelle() -> None:
    source = PIED.read_text(encoding="utf-8")
    # Les trois valeurs sont des CONSTANTES du composant, pas des chaînes semées
    # dans le JSX : c'est ce qui permet de les relire ici et de les vérifier une
    # fois pour les quatre carcasses qui rendent ce pied.
    assert f"export const CONTACT = '{CONTACT}';" in source
    assert f"export const LINKEDIN = '{LINKEDIN}';" in source
    assert f"export const X_COMPTE = '{X}';" in source
    assert "href={`mailto:${CONTACT}`}" in source
    # L'adresse s'écrit EN ENTIER, pas derrière un libellé « Contact » : c'est
    # ce qui la rend copiable et mémorisable, et c'est ce qui a fait retenir ce
    # rendu plutôt qu'une ligne de six liens de même poids.
    assert "{CONTACT}</a>" in source or ">{CONTACT}<" in source.replace("\n", "")


def test_les_trois_carcasses_rendent_LE_MEME_pied() -> None:
    """Trois pieds pour un site sont trois pieds qui divergeront.

    Vérifié aussi au navigateur : accueil, méthodologie, couverture et fiche
    candidat rendent le même `.pds`, 148 px de haut, deux icônes.
    """
    for chemin in (
        SRC / "pages" / "LandingPage.jsx",
        SRC / "components" / "ExplorerLayout.jsx",
        SRC / "components" / "StaticPage.jsx",
        SRC / "pages" / "CoveragePage.jsx",
    ):
        source = chemin.read_text(encoding="utf-8")
        assert "<PiedDeSite />" in source, f"{chemin.name} ne rend pas le pied du site"
    for mort in ("landing-footer", "explorer-footer"):
        for chemin in SRC.rglob("*.css"):
            assert mort not in chemin.read_text(encoding="utf-8"), (
                f"{mort} survit dans {chemin.name} — un pied mort qui reprend du service"
            )


def test_les_deux_comptes_sont_des_icones_nommees() -> None:
    """L'icône remplace le libellé À L'ÉCRAN, jamais pour un lecteur d'écran."""
    source = PIED.read_text(encoding="utf-8")
    assert source.count('aria-label="Empreinte politique sur ') == 2
    assert 'aria-hidden="true"' in source, "les glyphes doivent être masqués à la synthèse vocale"
    feuille = (SRC / "components" / "PiedDeSite.css").read_text(encoding="utf-8")
    assert "width: 30px" in feuille and "height: 30px" in feuille, (
        "la cible tactile ne fait pas 30 px"
    )


def test_les_liens_sortants_ne_gardent_pas_la_main() -> None:
    """`target="_blank"` sans `rel="noopener"` laisse la page ouverte piloter
    celle qu'elle a quittée."""
    for chemin in (LEGAL, PIED):
        source = chemin.read_text(encoding="utf-8")
        for ligne in source.splitlines():
            if 'target="_blank"' in ligne:
                bloc = source[max(0, source.index(ligne) - 400) : source.index(ligne) + 400]
                assert "noopener" in bloc, f"{chemin.name} : un lien sortant sans noopener"


def test_l_ancienne_adresse_ne_subsiste_que_datee() -> None:
    """Elle reste dans une citation datée, jamais dans du texte publiable.

    `web/old/` est hors périmètre : ce sont des générations archivées de
    l'interface (AGENTS.md §1), qui ne sont plus servies.
    """
    ancienne = "empreinte.politique@gmail.com"
    for chemin in SRC.rglob("*"):
        if chemin.is_file() and chemin.suffix in {".js", ".jsx"}:
            assert ancienne not in chemin.read_text(encoding="utf-8"), (
                f"{chemin.name} publie encore l'ancienne adresse"
            )
    licences = (RACINE / "docs" / "decisions" / "licences.md").read_text(encoding="utf-8")
    assert ancienne in licences, "la citation datée a été réécrite au lieu d'être annotée"
    assert CONTACT in licences, "la citation ne dit pas où trouver le texte qui fait foi"
