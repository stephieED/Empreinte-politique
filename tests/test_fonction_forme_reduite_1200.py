"""#1200 — la qualité de l'orateur survit à la forme réduite.

`fonction` (« ministre », « rapporteur général ») était écrite sur la forme
complète des candidats déclarés et sur aucune des 1 197 491 entrées réduites
des membres de groupe et de gouvernement : `_reduire_au_theme` ne la reprenait
pas, la branche réduite de `normalize_profil` non plus. Une fiche de groupe ne
pouvait donc pas retirer de la parole du groupe celle qu'un membre a prononcée
au banc du gouvernement.

La fixture est un compte rendu réel ; l'entrée brute est copiée de
`raw_data/profiles/elisabeth-borne.json` (privé `5b421000c`).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile as cp  # noqa: E402
from merge_profile import (  # noqa: E402
    CHAMPS_FAITS_DE_SOURCE,
    _intervention_key,
    reporter_faits_de_source,
)
from normalize_profil import _normalize_intervention  # noqa: E402
from parse_syceron import parse_syceron_xml  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "syceron_reel_leg16_creneau_questions.xml"

# Telle que publiée au brut le 04/10/2026 : séance du 21/12/2023, motion de
# censure, Élisabeth Borne au banc du gouvernement — et aucune `fonction`.
BRUT_PUBLIE = {
    "id": "syceron_CRSANR5L16S2024O1N091_000279",
    "date": "2023-12-21",
    "type_detail": "motion_censure",
    "sujet": "Motion de censure",
    "sujet_code_grammaire": "TITRE_TEXTE_DISCUSSION",
    "session_ref": "SCR5A2024O1",
    "url": (
        "https://data.assemblee-nationale.fr/static/openData/repository/16/vp/"
        "syceronbrut/syseron.xml.zip"
    ),
    "legislature": "16",
    "id_syceron": "3337400",
    "collecte": "extrait",
    "texte": "C’est précisément ce que nous faisons.",
    "texte_tronque": False,
}


def _entrees_completes():
    interventions = parse_syceron_xml(FIXTURE.read_bytes())["interventions"]
    entrees = []
    for rang, intervention in enumerate(interventions):
        resultat = cp._parse_syceron_intervention_entry(intervention, "16", rang)
        if resultat:
            entrees.append(resultat[1])
    return entrees


def test_l_extrait_garde_la_qualite_de_l_orateur():
    avec = [e for e in _entrees_completes() if e.get("fonction")]
    assert avec, "la fixture porte la parole d'un Premier ministre"
    for complete in avec:
        reduite = cp._reduire_a_l_extrait(complete)
        assert reduite["collecte"] == "extrait"
        assert reduite["fonction"] == complete["fonction"]
    assert {e["fonction"] for e in avec} == {"Premier ministre"}


def test_la_cle_n_est_pas_posee_quand_la_source_ne_dit_rien():
    """Une clé à `None` se lirait « mesuré, et sans qualité » (§2 règle 5)."""
    sans = [e for e in _entrees_completes() if not e.get("fonction")]
    assert sans
    for complete in sans:
        assert "fonction" not in cp._reduire_a_l_extrait(complete)
        assert "fonction" not in cp._reduire_au_theme(complete)


def test_la_forme_reduite_normalisee_publie_la_fonction():
    brut = {**copy.deepcopy(BRUT_PUBLIE), "fonction": "Première ministre"}
    assert _normalize_intervention(brut)["fonction"] == "Première ministre"
    assert "fonction" not in _normalize_intervention(copy.deepcopy(BRUT_PUBLIE))


def test_l_entree_deja_publiee_recoit_la_fonction():
    """La fusion est additive : c'est le report de #1169 qui la porte, parce que
    `fonction` est un fait de source nommé."""
    assert "fonction" in CHAMPS_FAITS_DE_SOURCE
    neuve = {**copy.deepcopy(BRUT_PUBLIE), "fonction": "Première ministre"}
    (apres,) = reporter_faits_de_source(
        [copy.deepcopy(BRUT_PUBLIE)], [neuve], _intervention_key)
    assert apres["fonction"] == "Première ministre"
    assert apres["texte"] == "C’est précisément ce que nous faisons."


def test_la_version_de_l_index_a_change_avec_son_contenu():
    """L'index réduit ne contient plus la même chose : sans nouvelle version, le
    run relit celui d'avant et rien n'atteint le corpus (#1169)."""
    assert cp.SYCERON_VERSION_INDEX not in ("1169", "1197")
