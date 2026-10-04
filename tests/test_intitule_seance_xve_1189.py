"""#1189 — l'intitulé de séance de la XVe d'avant avril 2021.

`normalize_profil` ne publiait `theme_officiel` — et, sur la forme complète,
`source` — que si l'entrée brute portait `seance_ref` ou `session_ref`.
L'archive Syceron de la XVe ne publie ces métadonnées qu'à partir de mars-avril
2021 : 488 919 intitulés lus au brut étaient jetés.

Les entrées ci-dessous sont COPIÉES du corpus (privé `40892200f7`), pas
imaginées : c'est l'absence de référence de séance, propre à ces années, qui
faisait le défaut, et une fixture écrite d'après la XVIIe ne le montrait pas.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from merge_profile import (  # noqa: E402
    CHAMPS_FAITS_DE_SOURCE,
    merge_pivot_profile,
    reporter_source_syceron,
    _pivot_intervention_key,
)
from normalize_profil import _normalize_intervention, _vient_de_syceron  # noqa: E402

ARCHIVE_15 = (
    "https://data.assemblee-nationale.fr/static/openData/repository/15/vp/"
    "syceronbrut/syseron.xml.zip"
)

# raw_data/profiles/jean-luc-melenchon.json — forme complète, candidat déclaré.
BRUT_COMPLET = {
    "id": "syceron_CRSANR5L15S2019E2N011_000398",
    "date": "2019-09-25",
    "type_detail": "debat",
    "sujet": "Bioéthique",
    "texte": "Oh !",
    "fonction": None,
    "format": "reaction_courte",
    "mots_cles": [],
    "source": ARCHIVE_15,
    "source_url": ARCHIVE_15,
    "url": ARCHIVE_15,
    "url_detail": None,
    "source_id": "CRSANR5L15S2019E2N011",
    "seance_ref": None,
    "session_ref": None,
    "orateur_id_source": "PA2150",
    "orateur_nom": "M. Jean-Luc Mélenchon",
    "point_ordre_du_jour": "Bioéthique > Discussion des articles > Article 1er",
    "point_code_grammaire": "DISC_ARTICLES_2_4",
    "etat_compte_rendu": "complet",
    "version_compte_rendu": "avant_JO",
    "legislature": "15",
    "sujet_code_grammaire": "TITRE_TEXTE_DISCUSSION",
    "id_syceron": "1830801",
}

# pivot_data/profiles/jean-luc-melenchon.pivot.json — la même, telle que publiée.
PIVOT_PUBLIE = {
    "intervention_id": "syceron_CRSANR5L15S2019E2N011_000398",
    "date": "2019-09-25",
    "type_detail": "debat",
    "sujet": "Bioéthique",
    "texte": "Oh !",
    "fonction": None,
    "format": "reaction_courte",
    "mots_cles": [],
    "source_url": ARCHIVE_15,
    "theme_officiel": None,
    "seance": None,
    "dossier": {"point_ordre_du_jour": "Bioéthique > Discussion des articles > Article 1er"},
    "source": None,
    "id_syceron": "1830801",
}

# raw_data/profiles/emilie-cariou.json — forme réduite, membre de groupe.
BRUT_EXTRAIT = {
    "id": "syceron_CRSANR5L15S2020O1N111_000084",
    "date": "2019-12-19",
    "type_detail": "loi",
    "sujet": "Projet de loi de finances pour 2020",
    "sujet_code_grammaire": "TITRE_TEXTE_DISCUSSION",
    "session_ref": None,
    "url": ARCHIVE_15,
    "legislature": "15",
    "id_syceron": "1974500",
    "collecte": "extrait",
    "texte": (
        "Et cela se confirme avec le projet de loi de finances pour 2020, auquel le "
        "groupe La République en marche apportera tout son soutien. (Applaudissements "
        "sur les bancs du groupe LaREM et sur quelques bancs du groupe MODEM.)"
    ),
    "texte_tronque": False,
}


def test_l_extrait_sans_reference_de_seance_publie_son_intitule():
    i = _normalize_intervention(copy.deepcopy(BRUT_EXTRAIT))
    assert i["theme_officiel"] == "Projet de loi de finances pour 2020"
    assert i["collecte"] == "extrait"


def test_la_forme_complete_sans_reference_publie_intitule_et_source():
    i = _normalize_intervention(copy.deepcopy(BRUT_COMPLET))
    assert i["theme_officiel"] == "Bioéthique"
    assert i["source"] == {
        "type": "syceron",
        "url": ARCHIVE_15,
        "source_id": "CRSANR5L15S2019E2N011",
        "legislature": "15",
    }
    # La référence de séance, elle, reste absente : la source ne la publie pas.
    assert i["seance"] is None


def test_une_question_de_l_open_data_ne_devient_pas_un_theme():
    question = {
        "id": "question_QANR5L15QE1234",
        "date": "2019-03-05",
        "type_detail": "question",
        "sujet": "Fiscalité des carburants",
        "url": "https://questions.assemblee-nationale.fr/q15/15-1234QE.htm",
    }
    assert not _vient_de_syceron(question)
    i = _normalize_intervention(question)
    assert i["theme_officiel"] is None
    assert i["source"] is None


def test_l_entree_deja_publiee_recoit_intitule_et_source():
    """La fusion est additive : sans report, le correctif n'atteint pas le corpus."""
    ancien = {"meta": {}, "interventions": [copy.deepcopy(PIVOT_PUBLIE)]}
    neuf = {"meta": {}, "interventions": [_normalize_intervention(copy.deepcopy(BRUT_COMPLET))]}
    fusion = merge_pivot_profile(ancien, neuf)
    (i,) = fusion["interventions"]
    assert i["theme_officiel"] == "Bioéthique"
    assert i["source"]["type"] == "syceron"
    assert i["texte"] == "Oh !"


def test_le_report_de_source_n_ecrit_que_la_ou_rien_n_est_ecrit():
    publie = {**copy.deepcopy(PIVOT_PUBLIE), "source": {"type": "syceron", "url": "x",
                                                        "source_id": None, "legislature": "15"}}
    neuf = _normalize_intervention(copy.deepcopy(BRUT_COMPLET))
    (i,) = reporter_source_syceron([publie], [neuf], _pivot_intervention_key)
    assert i["source"]["url"] == "x"


def test_le_report_de_source_ignore_une_entree_neuve_non_syceron():
    neuf = {**copy.deepcopy(PIVOT_PUBLIE), "source": {"type": "autre"}}
    (i,) = reporter_source_syceron([copy.deepcopy(PIVOT_PUBLIE)], [neuf], _pivot_intervention_key)
    assert i["source"] is None


def test_source_reste_hors_des_faits_de_source():
    """`source` est composé par la normalisation, et le brut porte autre chose sous ce nom."""
    assert "source" not in CHAMPS_FAITS_DE_SOURCE
