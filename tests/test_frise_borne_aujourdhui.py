"""La frise du parcours s'arrête aujourd'hui, pour tous les candidats.

Elle s'arrêtait à la fin du dernier mandat quand aucun n'était en cours : la
frise de Bernard Cazeneuve finissait en 2017, celle de Jean-Luc Mélenchon en
2022, et rien ne les distinguait d'un axe qui s'arrête aujourd'hui. Le lecteur
concluait que la carrière courait jusqu'à maintenant (signalé le 16/09/2026 ;
4 axes sur les 23 candidats déclarés qui ont une frise).

La date du jour est lue à l'affichage, jamais écrite dans le code : la borne
avance d'elle-même.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
UTILS = RACINE / "web" / "UI_finale" / "src" / "utils" / "profilCandidat.js"


def _bornes(roles: list[dict], aujourdhui: str | None) -> dict | None:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    appel = (
        f"u.bornesDuParcours({json.dumps(roles)}, {json.dumps(aujourdhui)})"
        if aujourdhui
        else f"u.bornesDuParcours({json.dumps(roles)})"
    )
    script = f"""
    const u = await import({json.dumps(UTILS.as_uri())});
    console.log(JSON.stringify({{ bornes: {appel}, jour: u.aujourdhuiISO() }}));
    """
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


CARRIERE_CLOSE = [
    {"debut": "2007-06-20", "fin": "2012-06-19", "actif": False},
    {"debut": "2012-05-16", "fin": "2017-06-20", "actif": False},
]


def test_une_carriere_close_s_arrete_aujourd_hui() -> None:
    out = _bornes(CARRIERE_CLOSE, "2026-09-16")
    assert out["bornes"] == {"debut": "2007-06-20", "fin": "2026-09-16"}


def test_la_borne_est_lue_a_l_affichage() -> None:
    """Sans date passée, c'est le jour même : rien n'est figé dans le code."""
    out = _bornes(CARRIERE_CLOSE, None)
    assert out["bornes"]["fin"] == out["jour"]


def test_un_mandat_en_cours_s_arrete_aussi_aujourd_hui() -> None:
    roles = [{"debut": "2017-06-18", "fin": "9999-12-31", "actif": True}]
    assert _bornes(roles, "2026-09-16")["bornes"]["fin"] == "2026-09-16"


def test_une_fin_posterieure_a_aujourd_hui_n_est_pas_rognee() -> None:
    roles = [{"debut": "2024-07-16", "fin": "2029-07-15", "actif": False}]
    assert _bornes(roles, "2026-09-16")["bornes"]["fin"] == "2029-07-15"


def test_sans_role_pas_de_frise() -> None:
    assert _bornes([], "2026-09-16")["bornes"] is None
