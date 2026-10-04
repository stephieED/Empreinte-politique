"""#1197 — le titre d'une loi de finances est un intitulé de séance.

Dans l'archive Syceron, le point d'ordre du jour d'un projet de loi de finances
porte `APPEL_PLF_1_20`, et non `TITRE_TEXTE_DISCUSSION`. Le parseur ne le lisait
pas : 111 839 + 20 588 + 35 877 paragraphes des trois législatures sortaient
sans sujet, dont presque toute la parole d'un rapporteur général du budget.

La fixture est RÉDUITE d'un compte rendu réel (`CRSANR5L17S2025O1N044`, séance
du 08/11/2024) : ses trois premiers points et un paragraphe publié, rien
d'inventé. L'entrée brute est copiée de `raw_data/profiles/paul-andre-colombani.json`.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile as cp  # noqa: E402
from merge_profile import (  # noqa: E402
    CLE_PREUVE_SUJET,
    _intervention_key,
    backfill_sujet_seance,
)
from normalize_profil import _normalize_intervention  # noqa: E402
from parse_syceron import _CODE_GRAMMAIRE_SUJET, parse_syceron_xml  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "syceron_reel_leg17_loi_de_finances.xml"
TITRE = "Projet de loi de finances pour 2025"

# Telle que publiée au brut le 04/10/2026, avant le correctif.
BRUT_PUBLIE = {
    "id": "syceron_CRSANR5L17S2025O1N044_000131",
    "date": "2024-11-08",
    "type_detail": "loi",
    "sujet": None,
    "sujet_code_grammaire": None,
    "session_ref": "SCR5A2025O1",
    "url": (
        "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/"
        "syceronbrut/syseron.xml.zip"
    ),
    "legislature": "17",
    "id_syceron": "3565087",
    "collecte": "extrait",
    "texte": "Je le retire, madame la présidente.",
    "texte_tronque": False,
}


def _interventions():
    return parse_syceron_xml(FIXTURE.read_bytes())["interventions"]


def test_toute_prise_de_parole_du_debat_porte_le_titre_du_texte():
    interventions = _interventions()
    assert len(interventions) == 5
    for i in interventions:
        assert i["sujet"] == TITRE
        assert i["sujet_code_grammaire"] == "APPEL_PLF_1_20"
        assert i["type_detail"] == "loi"


def test_la_partie_et_l_article_ne_deviennent_pas_le_sujet():
    """« Première partie (suite) » et « Article 32 » nomment un moment du débat."""
    for i in _interventions():
        assert "Première partie" in i["point_ordre_du_jour"]
        assert "partie" not in i["sujet"].lower()
        assert "article" not in i["sujet"].lower()
    assert "APPEL_PLF_1_30" not in _CODE_GRAMMAIRE_SUJET


def test_l_entree_deja_publiee_recoit_le_titre():
    """La fusion est additive : c'est le report de #710 qui porte le titre sur
    l'entrée brute déjà écrite, parce qu'elle porte la clé de preuve."""
    (lue,) = [i for i in _interventions() if i["id_syceron"] == "3565087"]
    neuve = {**copy.deepcopy(BRUT_PUBLIE),
             "sujet": lue["sujet"], "sujet_code_grammaire": lue["sujet_code_grammaire"]}
    (apres,) = backfill_sujet_seance(
        [copy.deepcopy(BRUT_PUBLIE)], [neuve], _intervention_key,
        preuve=lambda i: CLE_PREUVE_SUJET in i)
    assert apres["sujet"] == TITRE
    assert apres["texte"] == "Je le retire, madame la présidente."
    assert _normalize_intervention(apres)["theme_officiel"] == TITRE


def test_la_version_de_l_index_a_change_avec_le_parseur():
    """Sans cela, un index en cache écrit par l'ancien parseur est relu tel quel
    et le correctif n'atteint pas le corpus (#1169)."""
    assert cp.SYCERON_VERSION_INDEX != "1169"
