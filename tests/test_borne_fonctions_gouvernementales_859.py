"""#859 — la borne des fonctions gouvernementales est posée sur chaque profil,
sous sa propre clé, à la forme que lit `couverture-corpus.mjs`."""
from __future__ import annotations

import couverture_profil as cv
from schema_pivot import LISTES_COUVERTES, valider_couverture


def _profil(provenance="roster_groupe"):
    return {
        "id": "x", "mandats": [], "votes": [], "interventions": [],
        "amendements": [], "textes_portes": [],
        "meta": {"provenance": provenance, "collecte_ecartee": [], "warnings": []},
    }


def test_la_borne_est_posee_et_valide():
    couverture = cv.deriver(_profil(), constate_le="2026-10-08")
    entrees = couverture["fonctions_gouvernementales"]
    assert {(e["etat"], e["portee"]["debut"], e["portee"]["fin"]) for e in entrees} == {
        ("couvert", "2007-05-17", None),
        ("hors_couverture", None, "2007-05-16"),
    }
    assert valider_couverture(couverture) == []


def test_ce_n_est_pas_une_liste_metier():
    """Rangée dans `mandats`, la page des sources retiendrait 2002 et perdrait 2007."""
    assert "fonctions_gouvernementales" not in LISTES_COUVERTES


def test_un_profil_ecrit_avant_le_lot_reste_valide():
    couverture = cv.deriver(_profil(), constate_le="2026-10-08")
    del couverture["fonctions_gouvernementales"]
    assert valider_couverture(couverture) == []


def test_une_cle_inconnue_reste_refusee():
    couverture = cv.deriver(_profil(), constate_le="2026-10-08")
    couverture["fonctions_ministerielles"] = couverture["fonctions_gouvernementales"]
    assert any("hors nomenclature" in e for e in valider_couverture(couverture))
