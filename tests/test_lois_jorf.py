"""La table `numéro de loi → identifiant JORFTEXT` (`raw_data/lois_jorf.json`).

Les actes publient les lois qu'ils appliquent par leur identifiant `JORFTEXT` ;
les textes promulgués viennent des archives de l'Assemblée, qui publient le
numéro de loi et — sur 603 des 1 015 seulement — le NOR. Cette table fait le pont
par le numéro, que les deux sources publient.

Les deux enregistrements de `2007-1544` sont RÉELS : la loi du 29/10/2007 paraît
deux fois dans le fonds, le 30/10 puis le 10/11 (rectificatif), sous deux
identifiants. Mesuré le 23/09/2026 : 106 des 1 754 numéros depuis 2007 sont dans
ce cas.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import lois_jorf  # noqa: E402

ORIGINE = ("JORFTEXT000000279082", "2007-10-30")
RECTIFICATIF = ("JORFTEXT000000465327", "2007-11-10")


def test_un_numero_garde_ses_deux_enregistrements_la_plus_ancienne_en_tete():
    table: dict = {}

    assert lois_jorf.noter(table, "2007-1544", *RECTIFICATIF) is True
    assert lois_jorf.noter(table, "2007-1544", *ORIGINE) is True

    assert lois_jorf.resoudre(table, "2007-1544") == [ORIGINE[0], RECTIFICATIF[0]], (
        "un acte peut citer l'une ou l'autre : n'en garder qu'une ferait échouer "
        "la jointure sans le dire")


def test_une_loi_relue_ne_se_dedouble_pas():
    """La même loi revient à chaque redélivrance : la table est idempotente."""
    table: dict = {}
    lois_jorf.noter(table, "2007-1544", *ORIGINE)

    assert lois_jorf.noter(table, "2007-1544", *ORIGINE) is False
    assert len(table["2007-1544"]) == 1


def test_un_numero_inconnu_ne_resout_rien():
    assert lois_jorf.resoudre({}, "2026-1") == []
    assert lois_jorf.resoudre({}, None) == []


def test_seules_les_lois_entrent_dans_la_table():
    """Une ordonnance est un acte, pas une loi : elle vit dans
    `pivot_data/actes_reglementaires/`."""
    table: dict = {}

    assert lois_jorf.depuis_meta(table, "ORDONNANCE", "2021-1", "JORFTEXT000000000001", "2021-01-01") is False
    assert lois_jorf.depuis_meta(table, "LOI_ORGANIQUE", "2021-2", "JORFTEXT000000000002", "2021-01-02") is True
    assert list(table) == ["2021-2"]


def test_la_table_se_relit_et_une_table_illisible_ne_fait_pas_echouer(tmp_path):
    chemin = tmp_path / "lois_jorf.json"
    table = {"2007-1544": [list(ORIGINE)]}
    lois_jorf.ecrire(table, chemin, genere_le="2026-09-23T14:00:00+0200")

    assert lois_jorf.charger(chemin) == table
    assert json.loads(chemin.read_text(encoding="utf-8"))["schema_version"] == lois_jorf.SCHEMA_VERSION
    assert lois_jorf.charger(tmp_path / "absente.json") == {}
    (tmp_path / "cassee.json").write_text("{", encoding="utf-8")
    assert lois_jorf.charger(tmp_path / "cassee.json") == {}
