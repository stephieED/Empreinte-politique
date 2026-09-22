"""#853 — les mandats agrégés d'un groupe sont ceux exercés PENDANT l'appartenance.

Le filtre ne regardait que le mandat électif : un député l'était déjà en 2012,
donc son groupe d'amitié de 2012 comptait pour son groupe de 2024. Mesuré le
11/09/2026 sur les 28 fiches AN : 38 835 des 82 233 entrées membre × mandat
hors appartenance.

Le cas réel, copié de `groupe-AN-EPR-17.json` et du profil publié : Gérald
Darmanin, membre d'EPR du 19/07/2024 au 23/01/2025, député de 2012 à 2016
(Les Républicains), membre du groupe d'amitié France-Ukraine de 2012 à 2016 —
compté pour EPR avant ce lot.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import group_profile as gp  # noqa: E402


def _mandat(categorie, label, debut, fin, chambre=None, fonction="Membre"):
    return {"categorie": categorie, "label": label, "chambre": chambre, "debut": debut,
            "fin": fin, "actif": False, "fonction": fonction}


DARMANIN = {"id": "gerald-darmanin", "nom": "Gérald Darmanin", "mandats": [
    _mandat("mandat_electif", "Mandat parlementaire (Les Républicains)", "2012-06-20", "2016-01-27",
            chambre="AN", fonction="mandat"),
    _mandat("mandat_electif", "Mandat parlementaire (Ensemble pour la République)", "2024-07-07",
            "2025-01-23", chambre="AN", fonction="mandat"),
    _mandat("groupe_amitie", "France-Ukraine", "2012-10-12", "2016-01-27"),
    _mandat("commission", "Commission des affaires étrangères", "2024-09-21", "2025-01-23"),
]}
MEMBRE = {"membre_id": "gerald-darmanin", "nom": "Gérald Darmanin",
          "debut_dans_groupe": "2024-07-19", "fin_dans_groupe": "2025-01-23",
          "periodes": [{"debut": "2024-07-19", "fin": "2025-01-23"}],
          "present_a_la_date_de_reference": False}


def _labels(agregat):
    return {e["label"] for e in agregat}


def test_un_mandat_d_avant_le_groupe_ne_compte_pas():
    agregat = gp._aggregate_mandats([DARMANIN], [MEMBRE], "AN", "2026-09-22")

    assert _labels(agregat) == {"Commission des affaires étrangères"}


def test_une_appartenance_non_datee_garde_le_seul_filtre_electif():
    """Rien ne prouve qu'il n'était pas membre : le filtre d'avant s'applique."""
    sans_date = {**MEMBRE, "debut_dans_groupe": None, "fin_dans_groupe": None}
    del sans_date["periodes"]

    agregat = gp._aggregate_mandats([DARMANIN], [sans_date], "AN", "2026-09-22")

    assert _labels(agregat) == {"France-Ukraine", "Commission des affaires étrangères"}


def test_un_mandat_qui_deborde_l_appartenance_compte_avec_ses_dates():
    """Un chevauchement suffit, et les dates publiées restent celles du mandat.
    Cas réel : Patricia Lemoine entre dans EPR le 18/04/2026, et siège en
    commission de la défense du 17 au 20/04/2026."""
    lemoine = {"id": "patricia-lemoine", "nom": "Patricia Lemoine", "mandats": [
        _mandat("commission", "Commission de la défense nationale et des forces armées",
                "2026-04-17", "2026-04-20")]}
    membre = {"membre_id": "patricia-lemoine", "nom": "Patricia Lemoine",
              "debut_dans_groupe": "2026-04-18", "fin_dans_groupe": None,
              "periodes": [{"debut": "2026-04-18", "fin": None}],
              "present_a_la_date_de_reference": True}

    agregat = gp._aggregate_mandats([lemoine], [membre], "AN", "2026-09-22")

    assert agregat[0]["membres"][0]["debut"] == "2026-04-17"
