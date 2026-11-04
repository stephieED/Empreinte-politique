"""Nos textes promulgués confrontés aux lois du Journal officiel (#1248).

Les entrées reprennent des enregistrements réels, réduits à ce que le contrôle
lit : la loi 2018-287 (droit des contrats, absente de l'open data de l'AN,
#1424), la loi 2026-962 (présente des deux côtés), la loi 2026-1015 (publiée
au JO le 03/11/2026, après nos dossiers à jour au 02/11).
"""

import json

import relecture_lois_promulguees as rl

JO = {
    "2018-287": [["JORFTEXT000036825602", "2018-04-21"]],
    "2026-962": [["JORFTEXT000054999122", "2026-10-20"]],
    "2026-1015": [["JORFTEXT000055047268", "2026-11-03"]],
    "2010-1": [["JORFTEXT000021601325", "2010-01-05"]],   # avant la XIVe : hors du contrôle
}
TEXTES = {"DLR5L17N53095": {"numero_loi": "2026-962"}}


def test_tout_est_explique():
    bilan = rl.controler(JO, TEXTES, {"2018-287"}, "2026-11-02")
    assert (bilan.lois_du_jo, bilan.declarees_absentes, bilan.pas_encore_relues, bilan.a_signaler) == (
        3, ["2018-287"], ["2026-1015"], 0)


def test_une_loi_du_jo_ni_declaree_ni_recente_est_perdue():
    bilan = rl.controler(JO, TEXTES, set(), "2026-11-02")
    assert [e["numero_loi"] for e in bilan.perdues] == ["2018-287"] and bilan.a_signaler == 1


def test_sans_date_de_fraicheur_aucune_loi_n_est_excusee():
    bilan = rl.controler(JO, TEXTES, {"2018-287"}, None)
    assert [e["numero_loi"] for e in bilan.perdues] == ["2026-1015"]


def test_un_texte_publie_absent_de_la_table_est_signale():
    """Cas fictif, et voulu : aucun de nos 1 019 numéros ne manque à la table."""
    textes = {**TEXTES, "DLR5L17N52999": {"numero_loi": "2026-999"}}
    bilan = rl.controler(JO, textes, {"2018-287"}, "2026-11-02")
    assert bilan.absentes_du_jo == [{"numero_loi": "2026-999", "dossiers": ["DLR5L17N52999"]}]


def test_une_loi_declaree_que_nous_publions_est_signalee():
    textes = {**TEXTES, "DLR5L14N35818": {"numero_loi": "2018-287"}}
    bilan = rl.controler(JO, textes, {"2018-287"}, "2026-11-02")
    assert (bilan.declarees_a_tort, bilan.a_signaler) == (["2018-287"], 1)


def test_bout_en_bout_et_entree_illisible(tmp_path):
    table, textes, absentes, fraicheur = (tmp_path / n for n in ("t.json", "p.json", "a.json", "f.json"))
    table.write_text(json.dumps({"lois": JO}), encoding="utf-8")
    textes.write_text(json.dumps({"textes": TEXTES}), encoding="utf-8")
    absentes.write_text(json.dumps({"lois": [{"numero_loi": "2018-287"}]}), encoding="utf-8")
    fraicheur.write_text(json.dumps({"familles": {"an.dossiers": {"a_jour_au": "2026-11-02"}}}), encoding="utf-8")
    out, out_json = tmp_path / "r.md", tmp_path / "r.json"
    base = ["--textes-promulgues", str(textes), "--absentes", str(absentes), "--fraicheur", str(fraicheur),
            "--out", str(out), "--out-json", str(out_json)]
    assert rl.main(["--lois-jorf", str(table)] + base) == 0
    assert json.loads(out_json.read_text())["a_signaler"] == 0
    rl.main(["--lois-jorf", str(tmp_path / "absente.json")] + base)
    resume = json.loads(out_json.read_text())
    assert resume["a_signaler"] == 0 and "illisible" in resume["non_verifie"]
