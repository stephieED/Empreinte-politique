"""#1177 — un paragraphe sans identifiant d'orateur, que la source attribue.

Sur la XVe, 71 520 paragraphes — tous de 2021, la moitié de la parole de
l'année — nomment leur orateur et portent `id_acteur`, sans `<orateur><id>`.
Ils étaient rangés sous « absent », comme des didascalies : Jean-Michel Blanquer
publiait 1 999 prises de parole pour 2 160 dans l'archive.

La fixture est réduite du compte rendu réel `CRSANR5L15S2021E1N009` (questions
au Gouvernement du 13/07/2021). Les libellés d'orateurs collectifs sont ceux
relevés sur l'archive.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile as cp  # noqa: E402
from parse_syceron import parse_syceron_xml  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "syceron_reel_leg15_orateur_sans_id.xml"
BLANQUER, PRESIDENT = "PA717157", "PA606171"


def _interventions():
    return parse_syceron_xml(FIXTURE.read_bytes())["interventions"]


def test_la_fixture_montre_bien_le_cas():
    """Aucun `<orateur><id>`, et pourtant un acteur et un nom sur chaque paragraphe."""
    interventions = _interventions()
    assert len(interventions) == 18
    for i in interventions:
        assert i["orateur_id_source"] is None
        assert i["orateur_id_acteur"].startswith("PA")
        assert i["orateur_nom"].startswith("M.")


def test_un_orateur_nomme_est_attribue_par_l_acteur_de_la_source():
    assert cp._normaliser_orateur_id_syceron(None, BLANQUER, "M. Jean-Michel Blanquer") == (
        BLANQUER, "attribue_par_id_acteur")
    assert cp._normaliser_orateur_id_syceron(None, PRESIDENT, "M. le président") == (
        PRESIDENT, "attribue_par_id_acteur")


def test_un_orateur_collectif_n_est_pas_attribue():
    """La source rattache « Un député du groupe LR » au président de séance :
    14 paragraphes sur la XVe. Le libellé n'est pas celui d'une personne."""
    for libelle in ("Un député du groupe LR", "Plusieurs députés du groupe LaREM",
                    "Un député du groupe GDR"):
        assert cp._normaliser_orateur_id_syceron(None, PRESIDENT, libelle) == (None, "absent")


def test_sans_libelle_ou_sans_acteur_valide_rien_n_est_attribue():
    assert cp._normaliser_orateur_id_syceron(None, BLANQUER, None) == (None, "absent")
    assert cp._normaliser_orateur_id_syceron(None, BLANQUER) == (None, "absent")
    assert cp._normaliser_orateur_id_syceron(None, "PA0", "M. Un Tel") == (None, "absent")
    assert cp._normaliser_orateur_id_syceron(None, "PA-125799", "M. Un Tel") == (None, "absent")
    assert cp._normaliser_orateur_id_syceron(None, None, "M. Un Tel") == (None, "absent")


def test_un_identifiant_d_orateur_present_garde_ses_regles():
    """Le chemin nominal n'est pas touché, refus de la source compris."""
    assert cp._normaliser_orateur_id_syceron("717157", BLANQUER, "M. Jean-Michel Blanquer") == (
        BLANQUER, "identifiant_nu_prefixe")
    assert cp._normaliser_orateur_id_syceron("717157", "PA0", "M. Jean-Michel Blanquer") == (
        None, "attribution_refusee_par_la_source")


def test_les_prises_de_parole_du_ministre_entrent_dans_l_index():
    entrees = [cp._parse_syceron_intervention_entry(i, "15", rang)
               for rang, i in enumerate(_interventions())]
    assert all(e is not None for e in entrees)
    du_ministre = [r for a, r in entrees if a == BLANQUER]
    assert len(du_ministre) == 5
    assert du_ministre[0]["date"] == "2021-07-13"
    assert du_ministre[0]["id"].startswith("syceron_CRSANR5L15S2021E1N009_")


def test_la_presidence_de_seance_est_reconnue_sur_ces_entrees_aussi():
    de_la_presidence = [
        r for rang, i in enumerate(_interventions())
        for a, r in [cp._parse_syceron_intervention_entry(i, "15", rang)] if a == PRESIDENT]
    assert len(de_la_presidence) == 3
    assert {r.get("role_seance") for r in de_la_presidence} == {"presidence"}


def test_la_version_de_l_index_a_change_avec_son_contenu():
    assert cp.SYCERON_VERSION_INDEX not in ("1169", "1197", "1200")
