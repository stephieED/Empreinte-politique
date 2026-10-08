"""Une fin de mandat publiée par la source après la première collecte est reportée.

Entrée copiée de `raw_data/profiles/anne-stambach-terrenoir.json` (main
`3665078d3`, 08/10/2026) ; la fin vient d'AMO30 du 08/10 (22/09/2026).
"""
from __future__ import annotations

import copy

from merge_profile import (
    _mandat_key,
    _pivot_mandat_key,
    backfill_mandat_fin,
    merge_raw_profile,
)

LIBELLE = (
    "Commission spéciale chargée d'examiner la proposition de loi apportant une réponse "
    "intégrale au phénomène des violences sexuelles et sexistes contre les femmes et les "
    "enfants et la proposition de loi organique visant à adapter l'autorité judiciaire à la "
    "lutte contre les violences sexuelles et intrafamiliales"
)
OUVERT = {"categorie": "commission_enquete", "type": "Membre", "label": LIBELLE,
          "debut": "2026-07-24", "fin": None, "actif": True, "categorie_source": "an"}
FERME = dict(OUVERT, fin="2026-09-22", actif=False)


def test_la_fin_publiee_depuis_est_reportee_au_brut():
    fusionne = merge_raw_profile({"slug": "x", "mandats": [copy.deepcopy(OUVERT)]},
                                 {"slug": "x", "mandats": [copy.deepcopy(FERME)]})
    assert [(m["fin"], m["actif"]) for m in fusionne["mandats"]] == [("2026-09-22", False)]


def test_une_fin_n_est_jamais_effacee_par_une_collecte_qui_n_en_porte_pas():
    resultat = backfill_mandat_fin([copy.deepcopy(FERME)], [copy.deepcopy(OUVERT)], _mandat_key)
    assert resultat[0]["fin"] == "2026-09-22"


def test_la_source_corrige_une_fin_deja_publiee():
    corrige = dict(FERME, fin="2026-09-23")
    resultat = backfill_mandat_fin([copy.deepcopy(FERME)], [corrige], _pivot_mandat_key)
    assert resultat[0]["fin"] == "2026-09-23"


def test_un_autre_mandat_n_est_pas_touche():
    rapporteur = dict(OUVERT, type="Rapporteur thématique", fonction="Rapporteur thématique")
    membre_ferme = dict(FERME, fonction="Membre")
    resultat = backfill_mandat_fin([copy.deepcopy(rapporteur)], [membre_ferme], _pivot_mandat_key)
    assert resultat[0]["fin"] is None
