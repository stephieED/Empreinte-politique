"""La mention temporaire d'une source interrompue (#1199).

Le service qui diffuse le Journal officiel ne répond plus depuis le 02/10/2026.
La propriétaire a arbitré le 04/10/2026 une mention de circonstance, posée et
retirée À LA MAIN, sur la fiche du gouvernement en place seulement. Son texte
est validé au mot près ; l'issue #1199 ne se ferme pas tant qu'elle s'affiche.

Quand le service répond de nouveau : passer `SOURCE_INTERROMPUE` à `null`,
puis retirer ce fichier dans le même lot.
"""
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
FICHE = RACINE / "web" / "UI_finale" / "src" / "components" / "GovernmentProfile.jsx"
STYLE = RACINE / "web" / "UI_finale" / "src" / "components" / "GovernmentProfile.css"
SOURCES = RACINE / "web" / "UI_finale" / "src" / "pages" / "CoveragePage.jsx"


def test_le_texte_de_la_mention_est_celui_qu_elle_a_valide() -> None:
    fiche = FICHE.read_text(encoding="utf-8")
    assert "titre: 'Données incomplètes depuis le 2 octobre 2026.'," in fiche
    assert (
        "texte: 'Le service qui diffuse le Journal officiel ne répond plus : "
        "les actes parus depuis cette date n’apparaissent pas encore ici.',"
    ) in fiche


def test_la_mention_ne_s_affiche_que_sur_le_gouvernement_en_place() -> None:
    fiche = FICHE.read_text(encoding="utf-8")
    assert "const interrompue = SOURCE_INTERROMPUE && !government.periode.fin;" in fiche
    assert "{interrompue && (" in fiche


def test_la_mention_renvoie_a_l_issue_qui_la_fera_retirer() -> None:
    """Posée à la main, elle ne s'efface pas seule : le code dit où regarder."""
    fiche = FICHE.read_text(encoding="utf-8")
    bloc = fiche[: fiche.index("export const SOURCE_INTERROMPUE")]
    assert "#1199" in bloc[-900:]


def test_la_mention_n_est_pas_sur_la_page_sources() -> None:
    assert "SOURCE_INTERROMPUE" not in SOURCES.read_text(encoding="utf-8")


def test_la_mention_est_a_l_encre_pleine() -> None:
    style = STYLE.read_text(encoding="utf-8")
    bloc = style[style.index(".gvp-mention {") :]
    bloc = bloc[: bloc.index("}")]
    assert "background: var(--ink);" in bloc and "color: var(--card);" in bloc
