"""Le cadre de la page : en-tête repliable et sommaire de sections (#324).

L'en-tête restait collé en entier : marque plus trois barres de sélection, soit
**357 px sur tous les supports**. Mesuré le 08/09/2026 sur la fiche de Jérôme
Guedj, build de production — 45 % de la hauteur d'un écran 1 280 × 800, 42 %
d'un mobile 390 × 844. Ce qui est collé ne rend jamais sa place, et la fiche
fait 7 968 px sur ordinateur, 12 122 px sur mobile : neuf écrans parcourus avec
un demi-écran utile.

Ce que ces garde-fous protègent :

1. **Les barres ne se recollent pas.** C'est la moitié de la réforme qui vaut
   pour TOUT LE MONDE — 357 → 56 px, soit 301 px rendus sur les cinq supports,
   mobile compris.
2. **Le sommaire ne prend jamais sur le contenu.** Il occupe 204 px de marge
   au-delà de 1 440 px de fenêtre ; en dessous il n'existe pas, et le contenu
   garde exactement la largeur qu'il avait.
3. **Le seuil de 1 440 px est une mesure, pas un goût.** Statcounter France,
   août 2026 : il couvre 39 % du parc de bureau nommé, 21 % de toutes les
   visites. Un seuil à 1 600 px aurait exclu les écrans 1 600 × 900 eux-mêmes,
   dont la fenêtre fait 1 585 px.

CE QUE #1025 A CHANGÉ, LE 18/09/2026, ET QUI RÉÉCRIT LA MOITIÉ DE CE FICHIER :
les listes ont QUITTÉ la page. Elles y vivaient en double — dépliées sous le
bandeau à l'arrivée, puis rappelées dans un bouton du bandeau une fois
franchies. Un seul endroit reste, le tiroir, et il porte aussi la recherche.
Trois garde-fous d'ici tombent donc, non pas parce qu'ils étaient faux, mais
parce que ce qu'ils protégeaient n'existe plus : `.explorer-bars`,
`.explorer-changer` et sa visibilité réglée au défilement. Ce qui les remplace
est plus simple à tenir — plus aucune lecture de la position de défilement.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Le comportement — repli au défilement, rappel des listes, suivi de la section
lue, largeur du contenu — a été vérifié hors dépôt à 1920×1080, 1536×864,
1366×768 et 390×844, sans erreur console.

UN DÉFAUT QUE LA MESURE AVAIT MANQUÉ, et qui explique un de ces tests : la
première vérification lisait `element.hidden` et déclarait les barres masquées,
alors qu'elles restaient à l'écran — `display: flex` l'emporte sur le
`[hidden] { display: none }` de la feuille de l'agent utilisateur. Seule la
capture l'a montré. Vérifier un attribut n'est pas vérifier son effet.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"

LAYOUT = SRC / "components" / "ExplorerLayout.jsx"
LAYOUT_CSS = SRC / "components" / "ExplorerLayout.css"
ENTETE_CSS = SRC / "components" / "EnTeteSite.css"
SOMMAIRE = SRC / "components" / "SommaireSections.jsx"
SOMMAIRE_CSS = SRC / "components" / "SommaireSections.css"
FICHE = SRC / "components" / "CandidateProfile.jsx"
LIGNEE = SRC / "components" / "LigneeProfile.jsx"
NAV = SRC / "components" / "NavigationSite.jsx"
NAV_CSS = SRC / "components" / "NavigationSite.css"
PAGE_CANDIDAT = SRC / "pages" / "CandidateProfilePage.jsx"
PAGE_GROUPE = SRC / "pages" / "GroupProfilePage.jsx"

SEUIL_SOMMAIRE = "1440px"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : les en-têtes CITENT les valeurs qu'ils proscrivent."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def layout() -> str:
    return sans_commentaires(LAYOUT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def layout_css() -> str:
    return sans_commentaires(LAYOUT_CSS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entete_css() -> str:
    return sans_commentaires(ENTETE_CSS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sommaire() -> str:
    return sans_commentaires(SOMMAIRE.read_text(encoding="utf-8"))


# ── L'en-tête : la rangée collée, les listes qui défilent (#951) ────────────


def _bloc(css: str, selecteur: str) -> str:
    return css.split(f"{selecteur} {{")[1].split("}")[0]


def test_les_listes_ne_sont_plus_dans_la_page(layout: str, layout_css: str, entete_css: str) -> None:
    """357 px collés sur tous les supports : c'est ce que #324 a corrigé.

    #951 n'avait gardé collée que la rangée du logo, les listes défilant avec la
    page. #1025 les en retire : elles y faisaient 425 px et la fiche ne
    commençait qu'à 577 px du haut de la page, pour un contenu que le tiroir
    redonnait de toute façon. `.explorer-bars` n'existe plus, ni dans le
    composant ni dans la feuille.
    """
    assert "explorer-bars" not in layout
    assert "explorer-bars" not in layout_css
    entete = _bloc(entete_css, ".entete-site")
    assert "position: sticky" in entete and "top: 0" in entete


def test_plus_rien_ne_lit_le_defilement(layout: str) -> None:
    """Deux mécaniques ont été payées ici, et aucune n'a plus d'objet.

    L'en-tête de #324 RETIRAIT les listes au-delà de 180 px : la page
    raccourcissait, le navigateur ramenait le défilement à 0, les listes
    revenaient — une boucle. #951 l'a remplacée par une simple visibilité, lue à
    chaque défilement plutôt que par un `IntersectionObserver`, qui manquait les
    sauts directs (une ancre, un lien partagé). Les listes ayant quitté la page,
    le tiroir est là dès l'arrivée : il n'y a plus rien à franchir, donc plus
    rien à mesurer.
    """
    assert "SEUIL_REPLI" not in layout
    assert "IntersectionObserver" not in layout
    assert "addEventListener('scroll'" not in layout
    assert "getBoundingClientRect" not in layout
    assert "explorer-repere" not in layout


def test_l_outil_remplace_l_onglet_et_ne_s_y_ajoute_pas(layout: str) -> None:
    """Sur une fiche, « Explorateur » était déjà la page courante, et son clic
    renvoyait à `/candidats` — donc à la fiche par défaut, que personne n'avait
    demandée. Le tiroir prend sa place ; la barre garde quatre entrées.

    Un seul bouton est rendu, pas un pour le bureau et un pour le mobile : deux
    boutons pour un même geste, c'est le défaut que #1025 corrige.
    """
    nav = sans_commentaires(NAV.read_text(encoding="utf-8"))
    assert "outilExplorateur" in nav
    assert "page.libelle === 'Explorateur' && courante" in nav
    # Replié dans « Menu », l'entrée disparaît : le bouton est à côté, pas dedans.
    assert "className === 'nav-site-lien'" in nav
    assert layout.count('className="explorer-outil"') == 1


def test_l_attribut_hidden_a_sa_regle_css(layout_css: str) -> None:
    """`display: flex` l'emporte sur `[hidden]` de la feuille du navigateur.

    Sans cette règle, l'attribut est posé et le tiroir reste affiché — une
    mesure qui lit `element.hidden` le déclare pourtant corrigé.
    """
    assert "display: none" in _bloc(layout_css, ".explorer-tiroir[hidden]")


def test_l_entete_et_le_tiroir_sont_opaques(layout_css: str, entete_css: str) -> None:
    """Un fond translucide laissait lire le contenu à travers les listes.

    Le flou d'arrière-plan est un raffinement qui ne survit pas partout ;
    l'opacité est un fait.
    """
    for css, selecteur in ((entete_css, ".entete-site"), (layout_css, ".explorer-tiroir")):
        bloc = _bloc(css, selecteur)
        fond = [l for l in bloc.splitlines() if l.strip().startswith("background")]
        assert fond, f"{selecteur} doit déclarer un fond"
        assert all("rgba(" not in l for l in fond), f"{selecteur} doit être opaque"
        assert "background: var(--bg);" in bloc


def test_sous_720_px_la_barre_ne_porte_que_l_outil(layout_css: str) -> None:
    """Les quatre liens passent dans « Menu », et l'outil reste à l'écran —
    après le bouton « Menu », pas avant : c'est l'ordre retenu sur maquette.

    Son libellé long ne tient pas : « Chercher ou changer de fiche » mesure
    226 px sur les 390 px d'un mobile, et la rangée débordait de 4 px.
    """
    nav_css = sans_commentaires(NAV_CSS.read_text(encoding="utf-8"))
    media = nav_css.split("@media (max-width: 720px)")[1]
    assert "display: none" in _bloc(media, ".nav-site-lien")
    assert "order: 2" in _bloc(media, ".nav-site")
    assert "order: 1" in _bloc(media, ".nav-site-menu")
    media_layout = layout_css.split("@media (max-width: 720px)")[1].split("@media")[0]
    assert "display: none" in _bloc(media_layout, ".explorer-outil-long")
    assert "display: inline" in _bloc(media_layout, ".explorer-outil-court")


def test_le_champ_n_existe_que_la_ou_il_filtre(layout: str) -> None:
    """Une barre qui ne filtre rien est du mobilier.

    Les trois fiches lisent `?mot=` depuis #979 — la fiche de gouvernement les a
    rejointes le 20/09/2026 —, et les pages éditoriales n'ont pas de filtre. Le
    tiroir se renomme alors, et ne porte pas de champ (§2 règle 5 : on ne fait
    pas semblant).
    """
    assert "const FICHES_FILTRABLES = ['/candidats', '/groupes', '/gouvernements']" in layout
    assert "{filtrable && (" in layout
    assert "filtrable ? 'Chercher ou changer de fiche' : 'Changer de fiche'" in layout


def test_la_barre_a_quitte_le_corps_des_fiches(layout: str) -> None:
    """« Rechercher sur cette page » vivait dans la fiche, sous le nom (#979).

    Elle est dans le tiroir depuis #1025. Ce qui n'a PAS bougé : le mot vit dans
    l'adresse, et c'est la page qui le lit — monter le champ ne déplace qu'un
    champ, la mécanique du filtre n'est pas touchée. Les deux pages de fiche
    n'écrivent donc plus `?mot=`, elles le lisent.
    """
    assert "BarreFiltre" in layout
    for composant in (FICHE, LIGNEE):
        assert "BarreFiltre" not in sans_commentaires(composant.read_text(encoding="utf-8"))
    for page in (PAGE_CANDIDAT, PAGE_GROUPE):
        source = sans_commentaires(page.read_text(encoding="utf-8"))
        assert "params.get('mot')" in source
        assert "setParams" not in source, "le champ du bandeau est seul à écrire le mot"


# ── L'ordre des listes ──────────────────────────────────────────────────────


def test_l_ordre_est_candidats_groupes_gouvernements(layout: str) -> None:
    """Une fiche s'atteint par un NOM ; les deux autres listes sont du contexte."""
    ordre = re.findall(r"<(CandidatesBar|GroupsBar|GovernmentsBar)\s*/>", layout)
    # Une seule fois : depuis #1025, les listes ne vivent que dans le tiroir.
    assert ordre == ["CandidatesBar", "GroupsBar", "GovernmentsBar"], ordre


# ── Le sommaire ─────────────────────────────────────────────────────────────


def test_le_sommaire_n_apparait_qu_au_dessus_du_seuil() -> None:
    """1 440 px de FENÊTRE, mesure Statcounter France d'août 2026.

    Un seuil à 1 600 px aurait exclu les écrans 1 600 × 900, dont la fenêtre
    fait 1 585 px : quinze pixels sous la barre.
    """
    css = sans_commentaires(SOMMAIRE_CSS.read_text(encoding="utf-8"))
    assert ".som {\n  display: none;\n}" in css.replace("\r\n", "\n")
    assert f"@media (min-width: {SEUIL_SOMMAIRE})" in css


def test_le_sommaire_prend_sur_la_marge_jamais_sur_le_contenu(layout_css: str) -> None:
    """Hors seuil, la grille n'a qu'UNE colonne : le contenu garde sa largeur.

    Une grille à deux colonnes en permanence ferait glisser le contenu dans la
    colonne de 204 px dès que le sommaire est absent — c'est arrivé, et seule la
    mesure de la largeur rendue l'a montré.
    """
    bloc = layout_css.split(".explorer-corps {")[1].split("}")[0]
    assert "grid-template-columns: minmax(0, 1fr)" in bloc
    media = layout_css.split(f"@media (min-width: {SEUIL_SOMMAIRE})")[1].split("}")[0]
    assert "204px" in media


def test_le_sommaire_lit_la_page_et_l_observe(sommaire: str) -> None:
    """Il est monté AVANT la fiche, dont les données arrivent en réseau.

    Une lecture unique au montage ne trouve rien et le sommaire reste vide pour
    toujours. Il sert par ailleurs les trois types de fiche sans qu'aucune ait à
    le connaître.
    """
    assert "querySelectorAll('[data-section]')" in sommaire
    assert "MutationObserver" in sommaire
    assert "disconnect()" in sommaire, "l'observateur se débranche au démontage"


def test_le_nav_est_toujours_rendu(sommaire: str) -> None:
    """Le retirer du DOM faisait glisser le contenu dans sa colonne."""
    assert "return null" not in sommaire, (
        "le nav occupe la colonne de gauche même vide ; c'est son absence qui "
        "déplaçait le contenu"
    )


def test_les_sections_portent_une_ancre_stable() -> None:
    """L'ancre est dérivée du NUMÉRO, pas du titre.

    Un titre change avec la voix du texte (« ce qu'il » / « ce qu'elle ») ; un
    lien partagé ne doit pas.
    """
    fiche = sans_commentaires(FICHE.read_text(encoding="utf-8"))
    assert "id={`section-${numero}`}" in fiche
    assert "data-section={titre}" in fiche


def test_la_section_lue_est_la_derniere_franchie(sommaire: str) -> None:
    """Pas la plus visible : le lecteur descend, et ce qui compte est où il en
    est, pas ce qui occupe le plus de place à l'écran."""
    assert "getBoundingClientRect().top <= SEUIL_LECTURE" in sommaire


def test_l_ancre_prend_une_avance_sur_la_barre_collante(sommaire: str, entete_css: str) -> None:
    """Sans elle, la rangée collée recouvre le titre qu'on vient de demander.

    L'avance se règle sur la hauteur de la rangée : elle passait sous les 80 px
    de #951 quand elle était calée sur les 56 px de l'ancienne barre compacte.
    """
    hauteur = int(re.search(r"--entete-hauteur: (\d+)px", entete_css).group(1))
    avance = int(re.search(r"AVANCE_ANCRE = (\d+)", sommaire).group(1))
    seuil = int(re.search(r"SEUIL_LECTURE = (\d+)", sommaire).group(1))
    assert avance > hauteur and seuil > avance
