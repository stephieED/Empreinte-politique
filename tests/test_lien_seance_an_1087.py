"""#1087 — chaque prise de parole Syceron porte l'ancre de sa page de séance AN.

`source_url` mène à l'archive de la législature : le lecteur ne peut rien y
vérifier. La page de compte rendu de l'AN porte une ancre par prise de parole,
au numéro EXACT de l'attribut `id_syceron` du `<paragraphe>`. Mesuré le
22/09/2026 : 100 % des interventions de 120 comptes rendus de la XVIIe et de 40
de chacune des XVe et XVIe portent l'attribut, 90 séances tirées au hasard
répondent 200, et l'ancre existe sur la page (vérifié pour chaque législature).

La fixture est une RÉDUCTION VERBATIM d'un compte rendu réel
(`CRSANR5L17S2026O1N187`) ; l'ancre `#4049546` de M. Steevy Gustave a été
vérifiée sur la page de l'AN le même jour.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from candidate_profile import _reduire_a_l_extrait, _reduire_au_theme  # noqa: E402
from merge_profile import merge_pivot_profile, merge_raw_profile  # noqa: E402
from normalize_profil import _normalize_intervention  # noqa: E402
from parse_syceron import parse_syceron_xml  # noqa: E402
from schema_pivot import url_seance_an  # noqa: E402

FIXTURE = RACINE / "tests" / "fixtures" / "syceron_reel_leg17_structure.xml"


def _interventions():
    r = parse_syceron_xml(FIXTURE.read_bytes())
    return r if isinstance(r, list) else r["interventions"]


def test_le_parseur_lit_l_ancre_de_chaque_paragraphe():
    gustave = next(i for i in _interventions() if i["orateur_nom"] == "M. Steevy Gustave")

    assert gustave["id_syceron"] == "4049546"
    assert all(i.get("id_syceron") for i in _interventions())


def test_le_lien_mene_a_la_prise_de_parole():
    assert url_seance_an({"intervention_id": "syceron_CRSANR5L17S2026O1N187_000003",
                          "id_syceron": "4049546"}) == (
        "https://www.assemblee-nationale.fr/dyn/17/comptes-rendus/seance/"
        "CRSANR5L17S2026O1N187#4049546")


def test_sans_ancre_le_lien_mene_a_la_seance():
    assert url_seance_an({"intervention_id": "syceron_CRSANR5L15S2018O1N001_000012"}) == (
        "https://www.assemblee-nationale.fr/dyn/15/comptes-rendus/seance/CRSANR5L15S2018O1N001")


def test_une_entree_hors_syceron_n_a_pas_de_lien():
    assert url_seance_an({"intervention_id": "question_QANR5L17QG689"}) is None


# ── Toutes les formes gardent l'ancre ────────────────────────────────────

def _brute():
    """L'entrée brute que la collecte écrit, produite par le VRAI constructeur
    à partir de la fixture — rien n'est écrit à la main."""
    from candidate_profile import _parse_syceron_intervention_entry  # noqa: PLC0415

    interventions = _interventions()
    index = next(k for k, i in enumerate(interventions) if i["orateur_nom"] == "M. Steevy Gustave")
    _acteur, entree = _parse_syceron_intervention_entry(interventions[index], "17", index)
    return entree


BRUTE = _brute()


def test_les_formes_reduites_gardent_l_ancre():
    assert BRUTE["id"].startswith("syceron_CRSANR5L17S2026O1N187_")
    assert _reduire_au_theme(BRUTE)["id_syceron"] == "4049546"
    assert _reduire_a_l_extrait(BRUTE)["id_syceron"] == "4049546"


def test_une_entree_d_avant_1087_ne_recoit_pas_d_ancre_a_null():
    """Posée à `None`, la clé ferait passer un vieil index pour conforme."""
    ancienne = {k: v for k, v in BRUTE.items() if k != "id_syceron"}
    assert "id_syceron" not in _reduire_au_theme(ancienne)
    assert "id_syceron" not in _normalize_intervention(dict(ancienne))


def test_l_etage_pivot_publie_l_ancre():
    assert _normalize_intervention(dict(BRUTE))["id_syceron"] == "4049546"
    assert _normalize_intervention(_reduire_a_l_extrait(BRUTE))["id_syceron"] == "4049546"


# ── Le report sur les entrées déjà publiées ──────────────────────────────

def test_une_entree_publiee_sans_ancre_la_recoit_aux_deux_etages():
    ancienne = {k: v for k, v in BRUTE.items() if k != "id_syceron"}
    brut = merge_raw_profile(
        {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [], "interventions": [ancienne]},
        {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [], "interventions": [dict(BRUTE)]})
    assert brut["interventions"][0]["id_syceron"] == "4049546"

    pivot = merge_pivot_profile(
        {"id": "x", "votes": [], "mandats": [], "sources": [], "meta": {},
         "interventions": [_normalize_intervention(dict(ancienne))]},
        {"id": "x", "votes": [], "mandats": [], "sources": [], "meta": {},
         "interventions": [_normalize_intervention(dict(BRUTE))]})
    assert pivot["interventions"][0]["id_syceron"] == "4049546"
