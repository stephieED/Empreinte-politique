"""Tests de `src/purge_mandats_non_faits.py` (#839, lot D).

L'enjeu tient en une phrase : **treize entrées partagent la même signature de
forme, et cinq seulement ne sont pas des faits.** Les huit autres sont des
organes réels du Sénat, protégés par la réserve de la propriétaire du
12/09/2026 et par #528. Un critère de forme seul les emporterait — d'où la
liste **close** de libellés, établie par mesure, et les quatre conditions
cumulatives que ces tests verrouillent.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from purge_mandats_non_faits import (  # noqa: E402
    LIBELLES_DE_NAVIGATION,
    est_un_non_fait,
    purge_profil,
)


def _onglet(label):
    return {"label": label, "categorie": "commission", "fonction": "membre",
            "debut": None, "fin": None, "actif": True, "source_url": None}


def test_les_cinq_onglets_de_page_sont_des_non_faits():
    for label in ("Amendements", "Interventions", "Questions", "Vidéos", "Loi ou de résolution"):
        assert est_un_non_fait(_onglet(label)), label
    assert LIBELLES_DE_NAVIGATION == frozenset(
        {"Amendements", "Interventions", "Questions", "Vidéos", "Loi ou de résolution"})


def test_un_organe_reel_de_meme_forme_est_conserve():
    """Les 8 entrées de `bruno-retailleau` : sans date, sans `source_url`,
    publiées actives — et pourtant des organes réels du Sénat."""
    for label in ("Commission de la culture, de l'éducation et de la communication",
                  "Groupe Chrétiens d'Orient",
                  "Commission départementale de la coopération intercommunale"):
        assert not est_un_non_fait(_onglet(label)), label


def test_une_entree_datee_est_conservee_meme_si_le_libelle_figure_dans_la_liste():
    """Une date situe l'entrée : elle cesse d'être un onglet de page."""
    mandat = _onglet("Questions")
    mandat["debut"] = "2022-06-29"
    assert not est_un_non_fait(mandat)


def test_une_entree_portant_une_source_url_est_conservee():
    mandat = _onglet("Vidéos")
    mandat["source_url"] = "https://data.assemblee-nationale.fr/..."
    assert not est_un_non_fait(mandat)


def test_une_entree_etablie_par_un_referentiel_est_intouchable():
    """#718 : `categorie_source` dit qui a établi la catégorie. Le script ne
    peut pas retirer une entrée estampillée, même au libellé listé."""
    mandat = _onglet("Amendements")
    mandat["categorie_source"] = "an"
    assert not est_un_non_fait(mandat)


def test_purge_profil_retire_les_cinq_et_garde_le_reste():
    profil = {"mandats": [
        _onglet("Amendements"),
        _onglet("Vidéos"),
        _onglet("Groupe Chrétiens d'Orient"),
        {"label": "Commission des lois", "categorie": "commission", "debut": "2022-06-29",
         "categorie_source": "an"},
    ]}
    profil, retires = purge_profil(profil)
    assert sorted(m["label"] for m in retires) == ["Amendements", "Vidéos"]
    assert [m["label"] for m in profil["mandats"]] == ["Groupe Chrétiens d'Orient", "Commission des lois"]


def test_un_profil_sans_mandats_ne_leve_pas():
    profil, retires = purge_profil({"slug": "x"})
    assert retires == [] and "mandats" not in profil


def test_idempotent():
    profil = {"mandats": [_onglet("Questions")]}
    profil, premiers = purge_profil(profil)
    profil, seconds = purge_profil(profil)
    assert len(premiers) == 1 and seconds == []
