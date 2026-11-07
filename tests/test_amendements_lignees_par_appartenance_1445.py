"""La carte des amendements d'une fiche de groupe recompte par appartenance (#1445).

Depuis #1175, la fiche de groupe ne compte une signature que si l'amendement a
été déposé un jour où son signataire siégeait au groupe. Le recompte du build
(`web/UI_finale/scripts/amendements-lignees.mjs`) prenait tous les amendements
des membres sur la législature : il dépassait la fiche sur 26 maillons AN sur
38 (mesuré le 06/11/2026, données de `origin/main` `3131b99da4`), et la
répartition par commission de ces maillons n'était plus servie — SOC · XVIIe
annonçait 17 966 amendements et n'en répartissait aucun. Avec la règle de la
fiche, les 38 retombent au chiffre près.

Ces gardes tiennent :

1. les deux jumelles JS rendent ce que rendent `periodes_d_appartenance` et
   `_dans_periodes` de `src/group_profile.py` ;
2. un amendement déposé avant l'arrivée du membre dans le groupe n'est pas
   recompté, et le maillon retombe sur sa fiche ;
3. sans date de dépôt, la signature est gardée (§2 règle 5).

Les entrées sont copiées du corpus (06/11/2026) : Belkhir Belhaddad, membre de
SOC · XVIIe à partir du 30/09/2025, deux amendements de la XVIIe, l'un déposé le
25/06/2025, avant, l'autre le 20/07/2026, après.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
SCRIPT = RACINE / "web" / "UI_finale" / "scripts" / "amendements-lignees.mjs"
sys.path.insert(0, str(RACINE / "src"))

from group_profile import _dans_periodes, periodes_d_appartenance  # noqa: E402

AVANT = "an:AMANR5L17PO838901BTC1591P0D1N000570"
APRES = "an:AMANR5L17PO838901BTC3067P0D1N000040"
INDEX = {
    "amendements": {
        AVANT: {"texte_vise": "PIONANR5L17BTC1591", "sort": "irrecevable", "premier_signataire": "an:PA720362",
                "type_deposant": "depute", "date": "2025-06-25", "numero": "570"},
        APRES: {"texte_vise": "PRJLANR5L17BTC3067", "sort": "irrecevable", "premier_signataire": "an:PA793816",
                "type_deposant": "depute", "date": "2026-07-20", "numero": "40"},
    },
    "textes": {
        "PIONANR5L17BTC1591": {"dossier_id": "DLR5L16N47697",
                               "titre": "Réforme de l’audiovisuel public et souveraineté audiovisuelle"},
        "PRJLANR5L17BTC3067": {"dossier_id": "DLR5L17N54085",
                               "titre": "Projet de loi d’urgence pour la protection et la souveraineté agricoles"},
    },
}
COMMISSIONS = {"commissions": {
    "DLR5L16N47697": {"organe_ref": "PO419604", "sigle": "Affaires culturelles et éducation",
                      "nom": "Commission des affaires culturelles et de l'éducation", "type": "COMPER"},
    "DLR5L17N54085": {"organe_ref": "PO419610", "sigle": "Affaires économiques",
                      "nom": "Commission des affaires économiques", "type": "COMPER"},
}}
MEMBRE = {"membre_id": "belkhir-belhaddad", "nom": "Belkhir Belhaddad", "debut_dans_groupe": "2025-09-30",
          "fin_dans_groupe": None, "periodes": [{"debut": "2025-09-30", "fin": None}]}


def _node(script: str):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = f"const f = await import({json.dumps(SCRIPT.as_uri())});\n"
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


MEMBRES = [
    MEMBRE,
    {"membre_id": "x", "debut_dans_groupe": "2024-07-19", "fin_dans_groupe": "2025-01-01", "periodes": []},
    {"membre_id": "y", "periodes": [{"debut": "2024-07-19", "fin": "2024-12-31"}, {"debut": "2025-03-01", "fin": None}]},
    {"membre_id": "z"},
]
JOURS = ["2024-07-19", "2024-12-31", "2025-01-02", "2025-03-01", "2026-07-20"]


def test_les_jumelles_js_rendent_la_regle_python():
    js = _node(
        f"const ms = {json.dumps(MEMBRES)}; const js = {json.dumps(JOURS)};\n"
        "console.log(JSON.stringify(ms.map((m) => { const p = f.periodesDAppartenance(m);"
        " return [p, p ? js.map((j) => f.dansPeriodes(j, p)) : null]; })));"
    )
    for membre, (periodes_js, dedans_js) in zip(MEMBRES, js):
        periodes_py = periodes_d_appartenance(membre)
        assert (periodes_js is None) == (periodes_py is None), membre["membre_id"]
        if periodes_py is None:
            continue
        assert [tuple(p) for p in periodes_js] == periodes_py, membre["membre_id"]
        assert dedans_js == [_dans_periodes(j, periodes_py) for j in JOURS], membre["membre_id"]


def _maillon(tmp_path: Path, index: dict, attendu: int):
    (tmp_path / "profiles").mkdir()
    (tmp_path / "amendements").mkdir()
    (tmp_path / "profiles" / "belkhir-belhaddad.pivot.json").write_text(
        json.dumps({"amendements": [{"amendement_id": AVANT}, {"amendement_id": APRES}]}), encoding="utf-8")
    (tmp_path / "amendements" / "17.json").write_text(json.dumps(index), encoding="utf-8")
    (tmp_path / "commissions.json").write_text(json.dumps(COMMISSIONS), encoding="utf-8")
    groupe = {"chambre": "AN", "legislature": 17, "membres": [MEMBRE],
              "amendements_agreges": {"par_type_deposant": {"depute": {"nb_amendements": attendu}}}}
    return _node(
        f"const fiches = new Map([['groupe-AN-SOC-17.json', {json.dumps(groupe)}]]);\n"
        f"const r = f.repartitionsDesMaillons({{ fiches, profilesDir: {json.dumps(str(tmp_path / 'profiles'))},"
        f" amendementsDir: {json.dumps(str(tmp_path / 'amendements'))},"
        f" commissionsPath: {json.dumps(str(tmp_path / 'commissions.json'))}, scrutinsDossiersPath: null }});\n"
        "const m = r.get('groupe-AN-SOC-17.json');\n"
        "console.log(JSON.stringify({ types: Object.fromEntries(Object.entries(m.types).map(([k, v]) => [k, v.amendements])),"
        " ecarts: m.ecarts, lignes: m.parAmendement.rows.length }));"
    )


def test_un_amendement_depose_avant_l_arrivee_n_est_pas_recompte(tmp_path: Path):
    """La fiche de groupe compte 1 (l'amendement d'après le 30/09/2025) : le
    recompte retombe sur 1, la répartition est servie, sans écart."""
    m = _maillon(tmp_path, INDEX, attendu=1)
    assert m == {"types": {"depute": 1}, "ecarts": [], "lignes": 1}


def test_sans_date_la_signature_est_gardee(tmp_path: Path):
    index = json.loads(json.dumps(INDEX))
    del index["amendements"][AVANT]["date"]
    m = _maillon(tmp_path, index, attendu=2)
    assert m == {"types": {"depute": 2}, "ecarts": [], "lignes": 2}
