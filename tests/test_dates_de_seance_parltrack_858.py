"""#858 — une activité republiée par ParlTrack ne porte pas sa date.

ParlTrack date du 22/11/2016 toute activité dont `date-type` vaut
`datePublished` (548 598 dans le dump du 12/09/2026) : c'est la date de sa
republication, pas celle de la séance. Trois fiches de candidats déclarés
publiaient 4 346 prises de parole et 314 textes européens à cette date.

Les entrées ci-dessous sont copiées des profils publiés (privé `2140244c4`) :
`jean-luc-melenchon` pour le compte rendu et la question, `florian-philippot`
pour l'explication de vote et pour la prise de parole réellement tenue le
22/11/2016.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


import parltrack_dumps  # noqa: E402
from merge_profile import (  # noqa: E402
    _pivot_intervention_key,
    corriger_dates_de_republication,
    merge_lists_by_key,
)
from normalize_parltrack_dumps import (  # noqa: E402
    MOTIF_DATE_DE_REPUBLICATION,
    _make_intervention,
    _make_texte_porte_activite,
)
from parltrack_dumps import date_de_seance  # noqa: E402

PE = {"institution": "parlement_europeen", "legislature": 8}
REPUBLICATION = "2016-11-22"

COMPTE_RENDU = {
    "intervention_id": "europarl_P8_CRE-REV(2017)03-16(4-233-0000)",
    "date": REPUBLICATION,
    "type_detail": "debat",
    "sujet": ("Constitutional, legal and institutional implications of a Common Security "
              "and Defence Policy: possibilities offered by the Lisbon Treaty (A8-0042/2017 "
              "- Esteban González Pons, Michael Gahler) FR"),
    "source": PE,
    "source_url": "http://www.europarl.europa.eu/doceo/document/CRE-8-2017-03-16-INT-4-233-0000_FR.html",
    "texte": None,
    "collecte": "sans_verbatim_source",
}
QUESTION = {
    "intervention_id": "europarl_E-001015/2017 - Commission",
    "date": REPUBLICATION,
    "type_detail": "question",
    "sujet": "Report on corruption in Romania",
    "source": PE,
    "source_url": "http://www.europarl.europa.eu/doceo/document/E-8-2017-001015_EN.html",
    "texte": None,
    "collecte": "sans_verbatim_source",
    "sous_type": "QE",
}
EXPLICATION = {
    "intervention_id": None,
    "date": REPUBLICATION,
    "type_detail": "explication_de_vote",
    "sujet": "Calendar of Parliament's part-sessions - 2020 FR",
    "source": PE,
    "source_url": None,
    "texte": ("Cette proposition de calendrier pour 2020 respecte le statut de Strasbourg "
              "comme siège du Parlement européen. Je la soutiens donc."),
}
TENUE_LE_22_11 = {
    "intervention_id": "europarl_P8_CRE-REV(2016)11-22(2-156-0876)",
    "date": REPUBLICATION,
    "type_detail": "debat",
    "sujet": ("Agreement on Operational and Strategic Cooperation between Ukraine and "
              "Europol (A8-0342/2016 - Mariya Gabriel) FR"),
    "source": PE,
    "source_url": "http://www.europarl.europa.eu/doceo/document/CRE-8-2016-11-22-INT-2-156-0876_FR.html",
    "texte": None,
    "collecte": "sans_verbatim_source",
}


def _entree_d_index(publiee, *, date, republication=None):
    """L'entrée que `build_activities_index` rend pour cette activité."""
    reference = (publiee["intervention_id"] or "").removeprefix("europarl_") or None
    return {
        "titre": publiee["sujet"], "date": date, "reference": reference,
        "source_url": publiee["source_url"], "legislature": 8, "texte": publiee["texte"],
        **({"date_republication": republication} if republication else {}),
    }


# --- la date de séance, là où la source l'écrit ---------------------------------

def test_la_reference_d_un_compte_rendu_porte_la_date_de_seance():
    assert date_de_seance("P8_CRE-REV(2017)03-16(4-233-0000)", None) == "2017-03-16"
    assert date_de_seance("P6_CRE(2008)07-09(12)", None) == "2008-07-09"


def test_a_defaut_l_adresse_du_compte_rendu_la_porte():
    """7 225 comptes rendus republiés ont pour référence « -REV()- »."""
    adresse = "http://www.europarl.europa.eu/doceo/document/CRE-8-2017-02-14-INT-2-1686-0000_EN.html"
    assert date_de_seance("-REV()-", adresse) == "2017-02-14"


def test_une_reference_qui_ne_donne_qu_une_annee_ne_donne_pas_de_date():
    assert date_de_seance("A8-0042/2017", None) is None
    assert date_de_seance("E-001015/2017 - Commission", QUESTION["source_url"]) is None
    assert date_de_seance(None, None) is None


def test_la_version_de_l_index_a_change_avec_son_contenu():
    assert parltrack_dumps.VERSION_SCHEMA_INDEX >= 5


# --- ce que la normalisation publie ----------------------------------------------

def test_un_compte_rendu_republie_est_publie_a_sa_date_de_seance():
    i = _make_intervention("intervention_seance", _entree_d_index(COMPTE_RENDU, date="2017-03-16"))
    assert i["date"] == "2017-03-16"
    assert "date_non_resolue" not in i


def test_sans_date_de_seance_la_date_est_nulle_et_son_motif_est_dit():
    i = _make_intervention(
        "explication_de_vote_ecrite",
        _entree_d_index(EXPLICATION, date=None, republication=REPUBLICATION))
    assert i["date"] is None
    assert i["date_non_resolue"] == {
        "motif": MOTIF_DATE_DE_REPUBLICATION, "valeur_source": REPUBLICATION}


def test_un_texte_porte_republie_declare_lui_aussi_sa_date_absente():
    t = _make_texte_porte_activite("proposition_de_resolution", {
        "titre": "MOTION FOR A RESOLUTION on the situation in Yemen", "date": None,
        "date_republication": REPUBLICATION, "reference": "B8-0144/2017",
        "source_url": "http://www.europarl.europa.eu/doceo/document/B-8-2017-0144_EN.html",
        "legislature": 8, "texte": None, "dossiers": None,
    })
    assert t["date_min"] is None and t["date_max"] is None
    assert t["date_non_resolue"]["motif"] == MOTIF_DATE_DE_REPUBLICATION


# --- les entrées déjà publiées ---------------------------------------------------

def _neuves():
    return [
        _make_intervention("intervention_seance", _entree_d_index(COMPTE_RENDU, date="2017-03-16")),
        _make_intervention("question_ecrite",
                           _entree_d_index(QUESTION, date=None, republication=REPUBLICATION)),
        _make_intervention("explication_de_vote_ecrite",
                           _entree_d_index(EXPLICATION, date=None, republication=REPUBLICATION)),
        _make_intervention("intervention_seance", _entree_d_index(TENUE_LE_22_11, date=REPUBLICATION)),
    ]


def _publiees():
    return [copy.deepcopy(e) for e in (COMPTE_RENDU, QUESTION, EXPLICATION, TENUE_LE_22_11)]


def test_les_entrees_publiees_recoivent_la_date_ou_son_absence():
    cr, question, explication, tenue = corriger_dates_de_republication(_publiees(), _neuves())
    assert cr["date"] == "2017-03-16" and "date_non_resolue" not in cr
    assert question["date"] is None
    assert question["date_non_resolue"]["valeur_source"] == REPUBLICATION
    assert explication["date"] is None
    assert explication["date_non_resolue"]["motif"] == MOTIF_DATE_DE_REPUBLICATION
    # Une prise de parole réellement tenue le 22/11/2016 garde sa date.
    assert tenue["date"] == REPUBLICATION and "date_non_resolue" not in tenue


def test_aucune_explication_de_vote_n_est_publiee_deux_fois():
    """Sa clé de fusion est son contenu, DATE COMPRISE : corrigée après la
    fusion, elle serait ajoutée au lieu d'être reconnue (le défaut de #827)."""
    neuves = _neuves()
    sans_report = merge_lists_by_key(_publiees(), neuves, _pivot_intervention_key)
    assert len(sans_report) == 5
    avec_report = merge_lists_by_key(
        corriger_dates_de_republication(_publiees(), neuves), neuves, _pivot_intervention_key)
    assert len(avec_report) == 4


def test_une_entree_non_europeenne_n_est_jamais_touchee():
    francaise = {**copy.deepcopy(EXPLICATION), "source": {"type": "syceron"}}
    (apres,) = corriger_dates_de_republication([francaise], _neuves())
    assert apres == francaise


def test_une_date_neuve_que_la_reference_n_ecrit_pas_n_est_pas_reportee():
    """Le critère est sourcé : pas « la nouvelle date gagne »."""
    neuve = {**copy.deepcopy(QUESTION), "date": "2017-02-01"}
    (apres,) = corriger_dates_de_republication([copy.deepcopy(QUESTION)], [neuve])
    assert apres["date"] == REPUBLICATION
