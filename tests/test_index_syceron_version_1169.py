#!/usr/bin/env python3
"""
L'index des interventions en cache porte la version du parseur qui l'a écrit
(#1169).

Le run du 03/10/2026 (`37123323269`), lancé avec les interventions, a relu un
index écrit avant `role_seance` et publié **0** rôle de séance sur les 30 244
interventions de `yael-braun-pivet`. La qualification de #710/#1087 lit la
présence d'une clé ; `role_seance`, posée seulement sur les paragraphes de
présidence, ne peut pas qualifier un index de cette façon. La version, si.

Aucun réseau : un cache jetable sous `tmp_path`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import candidate_profile as cp  # noqa: E402


@pytest.fixture(autouse=True)
def _memo_propre():
    cp.vider_memo_qualification_syceron()
    yield
    cp.vider_memo_qualification_syceron()


@pytest.fixture
def cache(tmp_path, monkeypatch):
    racine = tmp_path / "syceron_an"
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", racine)
    return racine


ENTREE = {
    "id": "syceron_CR1_000001", "date": "2024-10-08", "type_detail": "debat",
    "sujet": "Questions au Gouvernement", "legislature": "17",
    "sujet_code_grammaire": "QUESTIONS", "id_syceron": "4166184",
    "role_seance": "presidence",
}


def test_l_index_publie_porte_la_version_du_parseur(cache):
    cp._write_syceron_index_par_acteur("17", {"PA1": [ENTREE]})
    index_dir = cache / "17" / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME
    assert (index_dir / cp.SYCERON_FICHIER_VERSION).read_text(encoding="utf-8") == cp.SYCERON_VERSION_INDEX
    assert cp._syceron_index_qualifie(index_dir) is True
    assert cp._read_cached_interventions_syceron_acteur("17", "PA1") == [ENTREE]


def test_un_index_sans_version_est_reconstruit(cache, capsys):
    """La forme exacte du cache du 03/10 : la clé de #1087 y est, la version non."""
    index_dir = cache / "17" / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME
    index_dir.mkdir(parents=True)
    ancienne = {k: v for k, v in ENTREE.items() if k != "role_seance"}
    (index_dir / "PA1.json").write_text(json.dumps([ancienne]), encoding="utf-8")
    assert cp._syceron_index_qualifie(index_dir) is False
    assert cp._read_cached_interventions_syceron_acteur("17", "PA1") is None
    assert "autre parseur" in capsys.readouterr().out


def test_un_index_d_une_autre_version_est_reconstruit(cache):
    cp._write_syceron_index_par_acteur("17", {"PA1": [ENTREE]})
    index_dir = cache / "17" / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME
    (index_dir / cp.SYCERON_FICHIER_VERSION).write_text("ancienne", encoding="utf-8")
    cp.vider_memo_qualification_syceron()
    assert cp._syceron_index_qualifie(index_dir) is False


def test_le_fichier_de_version_n_est_pas_lu_comme_une_tranche(cache):
    """Les tranches s'appellent `PA*.json` ; la version, non — rien ne la prend pour un acteur."""
    cp._write_syceron_index_par_acteur("17", {"PA1": [ENTREE]})
    index_dir = cache / "17" / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME
    assert sorted(p.name for p in index_dir.glob("*.json")) == ["PA1.json"]
