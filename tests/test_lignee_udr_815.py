#!/usr/bin/env python3
"""
Tests du lot #815 — UDR, lignée à elle seule (11/09/2026).

Un fichier par lot (#840). Deux choses :

- **UDR est l'union de trois organes renommés** — `AD` (18/07 → 11/09/2024),
  `UDR` (12/09/2024 → 04/09/2025), `UDDPLR` (depuis le 05/09/2025) —, le motif
  `SOC`/`SOC-A` : sans l'union, la fiche perdrait deux des trois périodes ;
- **elle n'a pas de prédécesseur, et c'est mesuré.** #815 et #836 décrivaient
  une scission, « AD quitte DR le 11/09/2024 ». L'archive dit autre chose :
  0 des 16 acteurs d'AD n'a siégé dans DR, et 2 seulement viennent de LR-16.
  Un `succede_a` affirmerait une succession que la source ne porte pas.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from groupes_config import charger_lignees  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

CONFIG = RACINE / "raw_data" / "groupes_reels.json"


def _entree() -> dict:
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    return next(
        e for e in document["correspondance_sigles_an"]["groupes"]
        if e["groupe_id"] == "AN:UDR:17"
    )


def test_udr_est_l_union_de_trois_organes_renommes():
    entree = _entree()
    assert entree["sigles_an"] == ["AD", "UDR", "UDDPLR"]
    assert entree["organes_an"] == ["PO845520", "PO847173", "PO872880"]


def test_udr_n_a_pas_de_predecesseur():
    """Ni DR, dont aucun membre ne vient d'AD, ni LR-16, qui en a donné 2 sur 16."""
    assert "succede_a" not in _entree()


def test_udr_est_une_lignee_a_un_seul_maillon():
    assert "AN:LIGNEE:UDR" in {l["lignee_id"] for l in charger_lignees(CONFIG)}
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    maillons = [g["groupe_id"] for g in document["groupes"] if g.get("lignee_id") == "AN:LIGNEE:UDR"]
    assert maillons == ["AN:UDR:17"]


def test_la_xviie_n_est_qualifiee_par_personne():
    assert _entree()["position_politique_an"]["position"] == "non_declaree"
