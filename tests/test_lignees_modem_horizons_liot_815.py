#!/usr/bin/env python3
"""
Tests du lot #815 — les lignées MoDem, Horizons et LIOT.

Un fichier par lot (#840). Deux choses, et pourquoi chacune :

- **le tri de `fusionner_intervalles` ne compare jamais une fin ouverte à une
  date.** Un seul couple (acteur, organe) de tout l'index GP porte deux mandats
  de même début dont l'un est clos et l'autre ouvert — Stéphane Lenormand,
  LIOT-17 —, et il suffisait à faire tomber le roster du groupe. Le code de
  #809 était en place depuis la veille ; aucun des 21 groupes alors déclarés
  ne portait cette forme, et c'est pourquoi rien ne l'avait vu ;
- **la déclaration committée tient** : les trois lignées nouvelles, leurs
  sept maillons, et le MoDem de la XVe comme UNION de deux organes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from an_roster import fusionner_intervalles  # noqa: E402
from groupes_config import charger_lignees  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

CONFIG = RACINE / "raw_data" / "groupes_reels.json"


# ---------------------------------------------------------------------------
# Le tri qui plantait
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("periodes", [
    [("2024-07-19", "2025-02-28"), ("2024-07-19", None)],
    [("2024-07-19", None), ("2024-07-19", "2025-02-28")],
])
def test_deux_mandats_de_meme_debut_dont_un_ouvert_ne_font_pas_planter(periodes):
    """La forme exacte de `PA795244` sur LIOT-17, dans les deux ordres.

    À début égal, la période ouverte absorbe l'autre : rien ne se termine pour
    qui siège encore.
    """
    assert fusionner_intervalles(periodes) == [("2024-07-19", None)]


def test_une_interruption_reelle_reste_une_interruption():
    """Le correctif du tri ne recolle pas ce que #809 a appris à séparer."""
    assert fusionner_intervalles(
        [("2022-06-28", "2023-01-01"), ("2023-06-01", "2024-06-09")]
    ) == [("2022-06-28", "2023-01-01"), ("2023-06-01", "2024-06-09")]


# ---------------------------------------------------------------------------
# La déclaration committée
# ---------------------------------------------------------------------------

def _document() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


@pytest.mark.parametrize("lignee_id, maillons", [
    ("AN:LIGNEE:DEM", ["AN:DEM:15", "AN:DEM:16", "AN:DEM:17"]),
    ("AN:LIGNEE:HOR", ["AN:HOR:16", "AN:HOR:17"]),
    ("AN:LIGNEE:LIOT", ["AN:LIOT:16", "AN:LIOT:17"]),
])
def test_chaque_lignee_nouvelle_porte_ses_maillons(lignee_id, maillons):
    assert lignee_id in {l["lignee_id"] for l in charger_lignees(CONFIG)}
    declares = sorted(
        g["groupe_id"] for g in _document()["groupes"] if g.get("lignee_id") == lignee_id
    )
    assert declares == sorted(maillons)


def test_le_modem_de_la_xve_est_lunion_de_deux_organes():
    """`MODEM` jusqu'au 23/09/2020, `DEM` dès le 24 : le motif `SOC`/`SOC-A`.

    Sans l'union, la fiche perdrait trois ans sur cinq de la législature.
    """
    entree = next(
        e for e in _document()["correspondance_sigles_an"]["groupes"]
        if e["groupe_id"] == "AN:DEM:15"
    )
    assert entree["sigles_an"] == ["MODEM", "DEM"]
    assert entree["organes_an"] == ["PO730970", "PO774834"]
    assert entree["position_politique_an"]["position"] == "minoritaire"


def test_la_xviie_nest_qualifiee_par_personne():
    """L'AN ne qualifie une législature qu'une fois achevée (#686)."""
    for gid in ("AN:DEM:17", "AN:HOR:17", "AN:LIOT:17"):
        entree = next(
            e for e in _document()["correspondance_sigles_an"]["groupes"]
            if e["groupe_id"] == gid
        )
        assert entree["position_politique_an"]["position"] == "non_declaree", gid
