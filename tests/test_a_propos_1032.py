"""La page /a-propos (#1032).

Le manifeste du site vivait dans l'**introduction de `/methodologie`** ; la
propriétaire en a redemandé un, à trois mots près le même, pour une page « À
propos ». Deux pages portant le même texte est le défaut que #1026 venait de
mesurer : la `meta description` et cette introduction ne disaient déjà pas la
même chose. Arbitré le 18/09/2026 — **structure A** : `/a-propos` porte le
manifeste et l'éditrice, `/methodologie` garde ses quinze sections et perd son
introduction, remplacée par un renvoi.

Ce que ces garde-fous protègent :

1. **Le manifeste n'existe qu'à un seul endroit.** Il est dans `AboutPage.jsx`,
   et `/methodologie` ne le reprend pas.
2. **Les dix ancres profondes ne bougent pas.** Les fiches appellent
   `/methodologie#fonctions`, `#propose`, `#couverture`, `#ecarts` : la page de
   méthode n'est pas renommée, c'est son introduction qui change.
3. **La page est atteignable et référencée.** Une adresse absente de
   `PAGES_FIXES` n'a ni page servie sans JavaScript, ni ligne de sitemap
   (#969, #1008) — `tests/test_pages_par_adresse_969.py` le tient déjà, celui-ci
   vérifie qu'elle y est bien entrée et que le pied de page y mène.
4. **« Qui édite ce site », jamais « Qui sommes-nous ».** La page parle à la
   première personne : un « nous » pour une personne seule est la première chose
   qu'un lecteur relève.

CE QU'ILS NE COUVRENT PAS (§2 règle 5) : aucun composant React n'est rendu ici.
Les trois formes ont été jouées dans l'application et capturées le 18/09/2026, à
1 280 px et 390 px, sans erreur console.

5. **Le patronyme n'est pas publié.** La propriétaire signe « Stéphie E. », et
   c'est ce qui laisse les mentions légales dire « une personne physique »
   (LCEN, article 6-III) sans se contredire.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SRC = RACINE / "web" / "UI_finale" / "src"

APROPOS = SRC / "pages" / "AboutPage.jsx"
APROPOS_CSS = SRC / "pages" / "AboutPage.css"
METHODO = SRC / "pages" / "MethodologyPage.jsx"
APP = SRC / "App.jsx"
PIED = SRC / "components" / "PiedDeSite.jsx"
ADRESSES = RACINE / "web" / "UI_finale" / "scripts" / "pages-par-adresse.mjs"

PREMIERE_PHRASE = "rassemble ce que les institutions publient"


def sans_commentaires(source: str) -> str:
    """Le code exécuté seul : les en-têtes CITENT ce qu'ils proscrivent."""
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", source)


@pytest.fixture(scope="module")
def apropos() -> str:
    return sans_commentaires(APROPOS.read_text(encoding="utf-8"))


def test_le_manifeste_n_existe_qu_a_un_seul_endroit(apropos: str) -> None:
    """Il est sur /a-propos, et /methodologie ne le reprend pas."""
    assert PREMIERE_PHRASE in apropos
    methodo = sans_commentaires(METHODO.read_text(encoding="utf-8"))
    assert PREMIERE_PHRASE not in methodo
    assert "aucun fait n" not in methodo, "la promesse ne se réécrit pas ici"


def test_methodologie_dit_desormais_ce_que_sa_page_fait() -> None:
    """Son introduction n'est plus le manifeste : c'est une phrase sur elle-même."""
    methodo = sans_commentaires(METHODO.read_text(encoding="utf-8"))
    intro = methodo.split("const INTRODUCTION = [")[1].split("];")[0]
    assert "Cette page dit comment chaque fiche est faite" in intro
    assert intro.count("',") + intro.count('",') <= 1, "une seule phrase"


def test_les_ancres_profondes_de_la_methodologie_ne_bougent_pas() -> None:
    """Les fiches y déposent le lecteur section par section : renommer la page
    aurait cassé dix liens, et c'est ce qui a fait écarter la fusion."""
    citees = set()
    for fichier in SRC.rglob("*.jsx"):
        citees |= set(re.findall(r"/methodologie#([a-z0-9-]+)", fichier.read_text(encoding="utf-8")))
    assert citees, "aucune ancre trouvée : la mesure est fausse, pas le code"
    methodo = METHODO.read_text(encoding="utf-8")
    for ancre in citees:
        assert f"id: '{ancre}'" in methodo, f"/methodologie#{ancre} ne mène nulle part"


def test_la_page_est_servie_et_referencee() -> None:
    """Hors de `PAGES_FIXES`, l'adresse n'a ni page sans JavaScript ni sitemap."""
    assert "'a-propos'" in ADRESSES.read_text(encoding="utf-8")
    assert 'path="/a-propos"' in APP.read_text(encoding="utf-8")
    assert 'to="/a-propos"' in PIED.read_text(encoding="utf-8"), "le pied de page y mène"


def test_la_section_dit_qui_edite_et_ne_dit_pas_nous(apropos: str) -> None:
    """La page parle à la première personne du singulier."""
    assert "Qui édite ce site" in apropos
    assert "Qui sommes-nous" not in apropos
    assert "mon temps libre" in apropos


def test_le_nom_complet_n_est_pas_publie(apropos: str) -> None:
    """La propriétaire signe « Stéphie E. », choisi le 18/09/2026.

    C'est ce qui permet aux mentions légales de garder leur formulation — « une
    personne physique », l'identité tenue à la disposition de l'hébergeur au
    titre de l'article 6-III de la LCEN. Ajouter le patronyme ici sans le
    demander mettrait les deux pages en contradiction.
    """
    assert "Stéphie E." in apropos
    assert "Edwige" not in apropos


def test_le_bandeau_reprend_la_baseline_et_ses_puces_en_accent(apropos: str) -> None:
    """Le manifeste est sur fond d'encre — le seul fond où le jaune signal passe
    le contraste (16,01:1 ; 1,05:1 sur fond clair, DESIGN_SYSTEM §2)."""
    assert "baseline--bandeau" in apropos
    css = APROPOS_CSS.read_text(encoding="utf-8")
    bandeau = css.split(".apropos-bandeau {")[1].split("}")[0]
    assert "background: var(--ink)" in bandeau


def test_le_bandeau_a_la_meme_largeur_que_les_cartes() -> None:
    """Deux largeurs sur une même page, et c'est la propriétaire qui l'a vu.

    `.static-main` porte déjà la gouttière — 40 px de chaque côté, 20 px sous
    680 px. Le bandeau en ajoutait 40 : il rendait 740 px de large quand les
    cartes en dessous en faisaient 820, mesuré à 1 440 px le 18/09/2026. Il ne
    porte donc aucune marge horizontale, ni au repos ni sous le seuil.
    """
    css = APROPOS_CSS.read_text(encoding="utf-8")
    for bloc in css.split(".apropos-bandeau {")[1:]:
        marge = [l for l in bloc.split("}")[0].splitlines() if "margin" in l]
        assert marge, "le bandeau déclare sa marge, pour qu'elle se relise"
        for ligne in marge:
            valeurs = ligne.split(":", 1)[1].strip().rstrip(";").split()
            horizontale = valeurs[1] if len(valeurs) > 1 else valeurs[0]
            assert horizontale == "0", f"marge horizontale {horizontale} : la gouttière est celle de .static-main"


def test_le_surtitre_ne_garde_pas_le_gris_des_pages_claires() -> None:
    """`--muted` est calibré sur le fond clair : sur l'encre il tombe sous AA."""
    css = APROPOS_CSS.read_text(encoding="utf-8")
    eyebrow = css.split(".apropos-eyebrow {")[1].split("}")[0]
    assert "var(--muted)" not in eyebrow
