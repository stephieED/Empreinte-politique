"""Un rôle se rattache à la législature ou au gouvernement qu'il recouvre le plus
longtemps (#1329, `web/UI_finale/src/utils/rattachement.js`).

FIXTURES copiées du corpus le 26/10/2026 : les trois sièges de Gabriel Attal
(`pivot_data/profiles/gabriel-attal.pivot.json`) et les bornes des législatures
du manifeste. Le premier siège commence le 18/06/2017, jour de l'élection, deux
jours avant la clôture de la XIVe : c'est le cas qui a fait écarter la règle de
la date de début.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
MODULE = RACINE / "web" / "UI_finale" / "src" / "utils" / "rattachement.js"

LEGISLATURES = [
    {"id": "17", "debut": "2024-07-01", "fin": None},
    {"id": "16", "debut": "2022-06-22", "fin": "2024-06-09"},
    {"id": "15", "debut": "2017-06-21", "fin": "2022-06-21"},
    {"id": "14", "debut": "2012-06-20", "fin": "2017-06-20"},
]
SIEGES = [("2017-06-18", "2018-11-16", "15"), ("2022-06-19", "2022-07-22", "16"), ("2024-07-07", None, "17")]


def _rattacher(debut, fin, periodes):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        f"import {{ periodeDuRole }} from {json.dumps(MODULE.as_uri())};\n"
        f"const p = periodeDuRole({json.dumps(debut)}, {json.dumps(fin)}, {json.dumps(periodes)}, '2026-10-26');\n"
        "console.log(JSON.stringify(p ? p.id : null));"
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


@pytest.mark.parametrize("debut, fin, attendue", SIEGES)
def test_un_siege_va_a_la_legislature_qu_il_recouvre_le_plus(debut, fin, attendue):
    assert _rattacher(debut, fin, LEGISLATURES) == attendue


def test_un_siege_avant_la_xive_n_a_pas_de_legislature():
    assert _rattacher("2007-06-20", "2012-06-19", LEGISLATURES) is None


def test_le_jour_de_bascule_va_au_plus_recent():
    """Deux gouvernements se touchent : un rôle d'un jour, ce jour-là, va au second."""
    govs = [{"id": "A", "debut": "2017-05-17", "fin": "2017-06-20"}, {"id": "B", "debut": "2017-06-20", "fin": "2020-07-06"}]
    assert _rattacher("2017-06-20", "2017-06-20", govs) == "B"
