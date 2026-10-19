"""La page /nous-soutenir (#1033).

Arbitré le 19/10/2026 sur maquette : la forme A, le bandeau d'encre de
`/a-propos` avec le don dedans, puis le code et le partage en deux cartes.

Ce que ces garde-fous protègent :

1. **Le don est un lien, jamais un widget.** Rien de Ko-fi ne s'exécute chez le
   lecteur : ni script, ni cadre. Un widget poserait des cookies, et les mentions
   légales n'ont pas de section « cookies et tiers ».
2. **L'adresse Ko-fi est renseignée.** La page a été écrite avant que le compte
   n'existe ; tant que l'adresse est provisoire, ce test échoue, et la page ne
   se publie pas avec un bouton qui ne mène nulle part.
3. **Les textes sont ceux de la propriétaire**, validés le 19/10/2026 — la
   mention de transparence sans sa parenthèse fiscale, et la phrase de
   `/a-propos` qui ne dit plus « aucun financement extérieur ».
4. **La page est atteignable et référencée** : route, pied de page, pages fixes.

CE QU'ILS NE COUVRENT PAS : aucun composant React n'est rendu ici. La page a été
jouée dans l'application et capturée le 19/10/2026, à 1 280 px et 390 px, sans
erreur console ni défilement horizontal.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"

PAGE = SRC / "pages" / "SoutenirPage.jsx"
APROPOS = SRC / "pages" / "AboutPage.jsx"
APP = SRC / "App.jsx"
PIED = SRC / "components" / "PiedDeSite.jsx"
ADRESSES = UI / "scripts" / "pages-par-adresse.mjs"
META = UI / "scripts" / "metadonnees-pages.mjs"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : les en-têtes CITENT ce qu'ils proscrivent."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"\{/\*.*?\*/\}", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def page() -> str:
    return sans_commentaires(PAGE.read_text(encoding="utf-8"))


def test_le_don_est_un_lien_et_rien_de_ko_fi_ne_s_execute(page: str) -> None:
    assert "<script" not in page and "<iframe" not in page
    assert "useEffect" not in page, "la page n'a rien à charger après coup"
    sources = "\n".join(p.read_text(encoding="utf-8") for p in SRC.rglob("*.js*"))
    sources += (UI / "index.html").read_text(encoding="utf-8")
    assert "ko-fi.com/widgets" not in sources and "storage.ko-fi.com" not in sources, (
        "un widget Ko-fi est chargé : il pose des cookies que les mentions légales ne déclarent pas"
    )


def test_l_adresse_ko_fi_est_renseignee(page: str) -> None:
    adresse = re.search(r"export const KOFI = '([^']+)'", page)
    assert adresse, "l'adresse Ko-fi ne se lit plus dans SoutenirPage.jsx"
    assert re.fullmatch(r"https://ko-fi\.com/[A-Za-z0-9_]+", adresse.group(1))
    assert "A_RENSEIGNER" not in adresse.group(1), (
        "l'adresse Ko-fi est encore provisoire : le bouton de don ne mènerait nulle part"
    )


def test_les_textes_sont_ceux_valides(page: str) -> None:
    assert (
        "Vos contributions permettent de couvrir les coûts d'hébergement et de serveurs.\"" in page
    ), "la mention de transparence a changé"
    assert "BNC" not in page, "la parenthèse fiscale a été retirée le 19/10/2026"
    assert "Paiement en ligne via Ko-fi, sans création de compte." in page


def test_a_propos_ne_dit_plus_aucun_financement_exterieur() -> None:
    apropos = re.sub(r"\s+", " ", sans_commentaires(APROPOS.read_text(encoding="utf-8")))
    assert "aucun financement extérieur" not in apropos, "la phrase contredirait l'appel aux dons"
    assert "aucun financement hors{' '} <Link to=\"/nous-soutenir\">dons sur le site</Link>" in apropos, (
        "la phrase validée le 19/10/2026 mène à la page des dons"
    )


def test_le_partage_ne_porte_que_l_adresse(page: str) -> None:
    """§2 règle 1 : un lien de partage ne fabrique pas de message."""
    for motif in (r"share-offsite/\?url=", r"intent/post\?url="):
        assert re.search(motif, page)
    assert "&text=" not in page and "?text=" not in page


def test_la_page_est_servie_et_referencee() -> None:
    assert "'nous-soutenir'" in ADRESSES.read_text(encoding="utf-8")
    assert "'nous-soutenir'" in META.read_text(encoding="utf-8")
    assert 'path="/nous-soutenir"' in APP.read_text(encoding="utf-8")
    assert 'to="/nous-soutenir"' in PIED.read_text(encoding="utf-8"), "le pied de page y mène"
