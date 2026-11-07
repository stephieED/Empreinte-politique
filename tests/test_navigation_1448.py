"""La navigation de l'interface (#1448).

Cinq défauts relevés sur le site en ligne le 06/11/2026 : une page qui s'ouvre
à la position de la précédente, une ancre non suivie ou suivie trop tôt,
l'ancienne adresse d'un groupe qui perd son mot et son ancre, les débats d'une
période dans l'ordre de la législature, une lettre perdue en tapant vite. Le
comptage des visites a sa garde dans `test_compteur_de_visites.py`.

Ces gardes lisent le code : le comportement ne se voit qu'au navigateur.
"""

from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "web" / "UI_finale" / "src"


def lire(chemin: str) -> str:
    return (SRC / chemin).read_text(encoding="utf-8")


def test_un_seul_composant_suit_le_defilement_de_toutes_les_pages() -> None:
    assert "<SuiviDeNavigation />" in lire("App.jsx")
    suivi = lire("components/SuiviDeNavigation.jsx")
    # « Précédent » garde la position que rend le navigateur.
    assert "type === 'POP' && !auChargement" in suivi
    assert "window.scrollTo({ top: 0 })" in suivi
    # L'ancre se recale tant que la page se charge, et lâche au premier geste.
    assert "MutationObserver" in suivi and "ResizeObserver" in suivi
    assert "'wheel', 'touchstart', 'keydown', 'mousedown'" in suivi


def test_la_page_des_sources_ne_saute_plus_d_elle_meme() -> None:
    # Deux sauts propres à la page partaient avant la fin du chargement : la
    # frise arrivait 2 191 px trop haut.
    assert "scrollIntoView" not in lire("pages/CoveragePage.jsx")


def test_l_ancienne_adresse_d_un_groupe_garde_mot_periode_et_ancre() -> None:
    page = lire("pages/GroupProfilePage.jsx")
    assert "pathname: `/groupes/${data.redirection}`, search, hash" in page


def test_les_debats_d_une_periode_sont_retries_sur_ses_membres() -> None:
    assert ".sort((a, b) => b.porteurs - a.porteurs)" in lire("utils/filtreLignee.js")
    gouvernement = lire("pages/GovernmentProfilePage.jsx")
    assert ".sort((a, b) => b.porteurs - a.porteurs)" in gouvernement
    # Sous une période, rien ne s'affiche avant le détail par membre.
    assert "(debut && government && !detail)" in gouvernement


def test_le_champ_de_recherche_suit_la_frappe_et_non_le_rendu() -> None:
    explorateur = lire("components/ExplorerLayout.jsx")
    assert "useState(motAdresse)" in explorateur
    assert "new URLSearchParams(window.location.search).get('mot')" in explorateur
