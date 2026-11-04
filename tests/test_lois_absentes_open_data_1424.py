"""La liste des lois que l'open data de l'Assemblée ne porte pas (#1424).

Un trou de la source, déclaré à la main : la garde vérifie sa forme et ce
qu'elle affirme d'elle-même, pas le corpus (aucun test ne lit les données).
"""

import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
LISTE = RACINE / "config" / "lois_absentes_open_data_an.json"


def _doc():
    return json.loads(LISTE.read_text(encoding="utf-8"))


def test_chaque_loi_porte_son_numero_son_identifiant_et_sa_date():
    for loi in _doc()["lois"]:
        assert re.fullmatch(r"20\d\d-\d+", loi["numero_loi"]), loi
        assert re.fullmatch(r"JORFTEXT\d{12}", loi["jorftext"]), loi
        assert "2012-06-20" <= loi["publiee_au_jo_le"] <= _doc()["_meta"]["constate_le"], loi


def test_aucune_loi_n_est_listee_deux_fois():
    numeros = [loi["numero_loi"] for loi in _doc()["lois"]]
    assert len(numeros) == len(set(numeros)) == 71


def test_la_cause_verifiee_nomme_son_dossier():
    verifiees = [loi for loi in _doc()["lois"] if "verifie" in loi]
    assert [(l["numero_loi"], l["dossier_an"]) for l in verifiees] == [("2018-287", "DLR5L14N35818")]


def test_la_liste_est_documentee_avec_la_source():
    assert "lois_absentes_open_data_an.json" in (RACINE / "docs" / "sources" / "an-opendata.md").read_text(encoding="utf-8")
