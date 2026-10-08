"""#1163 point 2 — un mandat européen sans prise de parole publiée se déclare.

Les entrées sont copiées de `pivot_data/profiles/emmanuel-maurel.pivot.json`
(public `5555443e8`, 07/10/2026), réduites aux champs que la règle lit.
"""
from __future__ import annotations

import copy

from couverture_profil import (
    ETAT_HORS_COUVERTURE,
    INSTITUTION_PE,
    deriver,
    mandats_europeens_sans_parole,
)
from schema_pivot import valider_couverture

MANDAT_VIIIE = {
    "label": "Mandat de député européen", "categorie": "mandat_electif",
    "fonction": None, "debut": "2014-07-01", "fin": "2019-07-01",
    "categorie_source": "europarl",
}
MANDAT_IXE = {
    "label": "Mandat de député européen", "categorie": "mandat_electif",
    "fonction": None, "debut": "2019-07-02", "fin": "2024-07-15",
    "categorie_source": "europarl",
}
COMMISSION_VIIIE = {
    "label": "Commission du commerce international", "categorie": "commission",
    "fonction": None, "debut": "2014-07-01", "fin": "2017-01-18",
    "categorie_source": "europarl",
}
PAROLE_IXE = {
    "intervention_id": None, "date": "2019-07-17",
    "type_detail": "explication_de_vote",
    "sujet": "Numerical strength of interparliamentary delegations (B9-0005/2019)",
    "theme_officiel": None, "seance": None, "dossier": None,
    "source": {"institution": "parlement_europeen", "legislature": 9},
    "mots_cles": [],
}


def _profil(mandats, interventions):
    return {
        "id": "emmanuel-maurel", "nom": "Emmanuel Maurel",
        "mandats": copy.deepcopy(mandats),
        "interventions": copy.deepcopy(interventions),
        "votes": [], "amendements": [], "textes_portes": [],
        "meta": {"provenance": "candidat_declare", "collecte_ecartee": [], "warnings": []},
    }


def test_le_mandat_sans_parole_est_declare_et_pas_l_autre():
    profil = _profil([MANDAT_VIIIE, MANDAT_IXE, COMMISSION_VIIIE], [PAROLE_IXE])
    assert mandats_europeens_sans_parole(profil) == [("2014-07-01", "2019-07-01")]


def test_l_entree_a_la_forme_que_l_interface_lit_et_passe_le_schema():
    profil = _profil([MANDAT_VIIIE, MANDAT_IXE], [PAROLE_IXE])
    couverture = deriver(profil, constate_le="2026-10-08")
    entrees = [
        e for e in couverture["interventions"]
        if e.get("source") == INSTITUTION_PE and e["etat"] == ETAT_HORS_COUVERTURE
    ]
    assert len(entrees) == 1
    assert entrees[0]["portee"] == {"debut": "2014-07-01", "fin": "2019-07-01"}
    assert valider_couverture(couverture) == []


def test_une_parole_europeenne_sans_date_empeche_toute_declaration():
    sans_date = dict(PAROLE_IXE, date=None)
    profil = _profil([MANDAT_VIIIE, MANDAT_IXE], [PAROLE_IXE, sans_date])
    assert mandats_europeens_sans_parole(profil) == []


def test_sans_aucune_parole_europeenne_rien_n_est_declare():
    profil = _profil([MANDAT_VIIIE, MANDAT_IXE], [])
    couverture = deriver(profil, constate_le="2026-10-08")
    assert not any(
        e.get("source") == INSTITUTION_PE for e in couverture.get("interventions", [])
    )


def test_un_mandat_en_cours_se_borne_au_present():
    en_cours = dict(MANDAT_IXE, debut="2024-07-16", fin=None)
    profil = _profil([MANDAT_IXE, en_cours], [PAROLE_IXE])
    assert mandats_europeens_sans_parole(profil) == [("2024-07-16", None)]
