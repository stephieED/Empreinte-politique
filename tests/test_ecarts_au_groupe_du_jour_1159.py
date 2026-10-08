"""Un vote ne se compare qu'au groupe dont la personne était membre ce jour-là (#1159).

Une fiche de groupe couvre une législature ; la section « écarts avec son
groupe » de la fiche candidat lui comparait tous les votes de la personne, y
compris après son départ. Mesuré le 08/10/2026 sur `main` 98327b0c0, en
exécutant `ecartsAvecLeGroupe` sur les 35 fiches de candidats :

| Fiche | Scrutins comparés | Écarts affichés |
| --- | --- | --- |
| Delphine Batho | 132, dont 121 distincts → 101 | 16 → 7 |
| Olivier Becht | 172, dont 132 distincts → 132 | 24 → 10 |

Les 33 autres fiches ne changent pas. Olivier Faure, cité par l'issue, ne
l'était déjà plus : ses deux fiches de groupe de la XVe n'en font plus qu'une.

Les périodes ci-dessous sont COPIÉES de `pivot_data/groupes/` (`membres[]`).

CE QUE CES TESTS NE COUVRENT PAS : `ecartsAvecLeGroupe` n'est pas exécutée ici
(son module n'est pas importable hors de l'application) ; le compte ci-dessus
l'a été hors dépôt. La fiche n'est pas rendue.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

UI = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "src"
MODULE = UI / "utils" / "appartenanceAuGroupe.js"

#: `groupe-AN-SOC-15.json`, `groupe-AN-EDS-15.json`, `groupe-AN-REN-16.json`.
SOC_15 = {"membres": [{"membre_id": "delphine-batho", "periodes": [{"debut": "2017-06-27", "fin": "2018-05-02"}]}]}
EDS_15 = {"membres": [{"membre_id": "delphine-batho", "periodes": [{"debut": "2020-05-20", "fin": "2020-10-16"}]}]}
REN_16 = {"membres": [{"membre_id": "olivier-becht", "periodes": [
    {"debut": "2022-06-29", "fin": "2022-08-04"}, {"debut": "2024-02-13", "fin": "2024-06-09"}]}]}
ECOS_17 = {"membres": [{"membre_id": "delphine-batho", "periodes": [{"debut": "2024-07-19", "fin": None}]}]}


def _membre(fiche: dict, membre_id, date) -> bool:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(JSON.stringify(m.etaitMembreLe(m.periodesDansLeGroupe(%s, %s), %s)));"
        % (MODULE.as_uri(), json.dumps(fiche), json.dumps(membre_id), json.dumps(date))
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_un_vote_d_apres_le_depart_n_est_plus_compare() -> None:
    assert _membre(SOC_15, "delphine-batho", "2018-05-02") is True
    assert _membre(SOC_15, "delphine-batho", "2018-05-03") is False
    assert _membre(SOC_15, "delphine-batho", "2021-11-16") is False


def test_entre_deux_groupes_rien_ne_se_compare() -> None:
    """De mai 2018 à mai 2020, ni le groupe quitté ni le groupe à venir."""
    for fiche in (SOC_15, EDS_15):
        assert _membre(fiche, "delphine-batho", "2019-06-01") is False


def test_deux_periodes_dans_un_meme_groupe() -> None:
    assert _membre(REN_16, "olivier-becht", "2022-07-15") is True
    assert _membre(REN_16, "olivier-becht", "2023-03-01") is False
    assert _membre(REN_16, "olivier-becht", "2024-03-01") is True


def test_une_periode_ouverte_court_jusqu_a_aujourd_hui() -> None:
    assert _membre(ECOS_17, "delphine-batho", "2026-07-01") is True


def test_ce_qu_on_ne_sait_pas_dater_n_est_pas_retire() -> None:
    """Membre absent de la fiche, ou appelant qui ne nomme personne : pas de filtre."""
    assert _membre(SOC_15, None, "2021-11-16") is True
    assert _membre(SOC_15, "inconnu", "2021-11-16") is True
    assert _membre({"membres": [{"membre_id": "x"}]}, "x", "2021-11-16") is True


def test_un_vote_sans_date_ne_se_compare_pas_a_une_periode() -> None:
    assert _membre(SOC_15, "delphine-batho", None) is False


def test_la_comparaison_passe_par_la_regle() -> None:
    module = (UI / "utils" / "ecartsGroupe.js").read_text(encoding="utf-8")
    assert "const periodes = periodesDansLeGroupe(fiche, membreId);" in module
    assert "if (!etaitMembreLe(periodes, mien.date)) continue;" in module
    adaptateur = (UI / "data" / "pivotAdapter.js").read_text(encoding="utf-8")
    appel = adaptateur.split("const ecarts = ecartsAvecLeGroupe(")[1].split(");")[0]
    assert "manifestEntry.slug" in appel, "sans le membre, aucune période n'est lue"
