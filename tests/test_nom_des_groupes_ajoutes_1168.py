#!/usr/bin/env python3
"""
Le nom affiché d'un groupe que seul un run a ajouté suit le dernier nom de
l'Assemblée (#1168, arbitré le 03/10/2026).

Ce qui suit : `groupe_nom`, et `lignee_nom` d'une lignée que seul un run a
ouverte. Ce qui ne bouge jamais : un nom écrit à la main, les identifiants —
donc l'adresse de la page —, le sigle publié.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import groupes_amo30  # noqa: E402
from test_mise_a_jour_table_groupes_1168 import XVII, _depart, _index  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

JOUR = "2027-07-01"

AVANT = {**XVII, "PO3": ("AD", "17", "2024-07-18", None, 300, 316)}
APRES = {
    **XVII,
    "PO3": ("AD", "17", "2024-07-18", "2024-09-11", 300, 316),
    "PO4": ("UDR", "17", "2024-09-12", None, 300, 316),
}


def _renomme(index: dict, ref: str, libelle: str) -> dict:
    index["organes"][ref]["libelle"] = libelle
    return index


def _deux_runs() -> tuple[dict, dict, dict]:
    ecrite = _depart(_index(XVII))
    premier, _ = groupes_amo30.composer_table(
        ecrite, None, _renomme(_index(AVANT), "PO3", "À droite"), jour=JOUR,
    )
    index = _renomme(_renomme(_index(APRES), "PO3", "À droite"), "PO4", "Union des droites")
    second, journal = groupes_amo30.composer_table(ecrite, premier, index, jour="2027-07-02")
    return premier, second, journal


def _groupe(document: dict, groupe_id: str) -> dict:
    return next(g for g in document["groupes"] if g["groupe_id"] == groupe_id)


def _lignee(document: dict, lignee_id: str) -> dict:
    return next(l for l in document["lignees"] if l["lignee_id"] == lignee_id)


def test_un_groupe_ajoute_puis_renomme_prend_le_dernier_nom():
    premier, second, journal = _deux_runs()
    assert _groupe(premier, "AN:AD:17")["groupe_nom"] == "À droite"
    assert _groupe(second, "AN:AD:17")["groupe_nom"] == "Union des droites"
    assert {"objet": "AN:AD:17", "avant": "À droite", "apres": "Union des droites"} in journal["noms_rafraichis"]


def test_sa_lignee_ouverte_par_un_run_suit_aussi():
    premier, second, _ = _deux_runs()
    assert _lignee(premier, "AN:LIGNEE:AD")["lignee_nom"] == "À droite"
    assert _lignee(second, "AN:LIGNEE:AD")["lignee_nom"] == "Union des droites"
    assert _lignee(second, "AN:LIGNEE:AD")["verifie_le"] == "2027-07-02"


def test_les_identifiants_et_le_sigle_ne_bougent_pas():
    """L'adresse de la page reste celle de la naissance du groupe (#836)."""
    _, second, _ = _deux_runs()
    groupe = _groupe(second, "AN:AD:17")
    assert (groupe["groupe_id"], groupe["lignee_id"], groupe["groupe_sigle"]) == (
        "AN:AD:17", "AN:LIGNEE:AD", "AD",
    )


def test_un_nom_ecrit_a_la_main_ne_suit_jamais():
    _, second, _ = _deux_runs()
    assert _groupe(second, "AN:EPR:17")["groupe_nom"] == "Nom relu EPR"
    assert _lignee(second, "AN:LIGNEE:REN")["lignee_nom"] == "Nom de lignée relu"


def test_une_lignee_ecrite_a_la_main_garde_son_nom_meme_si_un_run_y_ajoute_un_groupe():
    """Les législatives : EPR-18 entre dans la lignée REN, dont le nom est relu."""
    ecrite = _depart(_index(XVII))
    index = _renomme(_index({**XVII, "PO10": ("EPR", "18", "2027-07-01", None, 10, 80)}),
                     "PO10", "Ensemble, autrement")
    composee, journal = groupes_amo30.composer_table(ecrite, None, index, jour=JOUR)
    assert _lignee(composee, "AN:LIGNEE:REN")["lignee_nom"] == "Nom de lignée relu"
    assert _groupe(composee, "AN:EPR:18")["groupe_nom"] == "Ensemble, autrement"
    assert journal["noms_rafraichis"] == []


def test_rien_ne_bouge_au_run_suivant():
    _, second, _ = _deux_runs()
    ecrite = _depart(_index(XVII))
    index = _renomme(_renomme(_index(APRES), "PO3", "À droite"), "PO4", "Union des droites")
    troisieme, journal = groupes_amo30.composer_table(ecrite, second, index, jour="2027-07-03")
    assert troisieme == second
    assert journal["noms_rafraichis"] == []
