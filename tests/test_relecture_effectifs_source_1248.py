"""Effectifs des groupes confrontés à ceux de chaque scrutin (#1248, lot 5).

Les archives sont des extraits verbatim de l'open data de l'Assemblée, relevés
le 03/11/2026 : quatre fichiers de scrutin de la XVe à la XVIIe (le dernier de
la XVIIe, un scrutin dont les groupes sont publiés sous « PO0 », le scrutin du
Congrès rangé dans l'archive de la XVIe, un scrutin de la XVe dont la
ventilation omet le MoDem), et l'enveloppe du fichier unique de la XIVe réduite
à deux de ses scrutins, recopiés tels quels.
"""

import json
from pathlib import Path

import relecture_effectifs_source as re_

FIXTURES = Path(__file__).parent / "fixtures" / "relecture_effectifs"
PAR_SCRUTIN = FIXTURES / "scrutins_un_fichier_par_scrutin.zip"
XIV = FIXTURES / "scrutins_xiv_un_seul_fichier.zip"

#: Le scrutin n° 9578 de la XVIIe (02/11/2026), organe par organe.
EFFECTIFS_9578 = {
    "PO845401": 121, "PO845407": 90, "PO845413": 70, "PO845419": 68, "PO845425": 47,
    "PO845439": 38, "PO845454": 37, "PO845470": 35, "PO845485": 23, "PO845514": 17,
    "PO872880": 17, "PO840056": 11,
}


def _scrutins(chemin):
    return {s.numero: s for s in re_.scrutins_de_l_archive(chemin)}


def _unite(cle, organe, nombre, debut="2024-07-19", fin=None):
    return re_.Unite(cle, {organe}, [[{"debut": debut, "fin": fin}] for _ in range(nombre)])


def _unites_9578(**ajustements):
    return [_unite(organe, organe, ajustements.get(organe, n)) for organe, n in EFFECTIFS_9578.items()]


# ── La lecture des archives ─────────────────────────────────────────────────

def test_un_fichier_par_scrutin_se_lit():
    scrutins = _scrutins(PAR_SCRUTIN)
    assert set(scrutins) == {9578, 489, 1, 2418}
    dernier = scrutins[9578]
    assert (dernier.date, dernier.effectifs, dernier.hors_comparaison) == ("2026-11-02", EFFECTIFS_9578, None)


def test_le_fichier_unique_de_la_xive_se_lit():
    scrutins = _scrutins(XIV)
    assert set(scrutins) == {1, 905}
    assert scrutins[905].date == "2014-10-01"
    assert scrutins[905].effectifs["PO645633"] == 11  # les non-inscrits


def test_le_scrutin_du_congres_ne_se_compare_pas():
    """Il compte les groupes du Sénat : rien de l'Assemblée seule."""
    assert _scrutins(PAR_SCRUTIN)[1].hors_comparaison == "scrutin du Congrès"


def test_des_groupes_publies_sous_po0_ne_se_comparent_pas():
    assert _scrutins(PAR_SCRUTIN)[489].hors_comparaison == "groupe non identifié par la source"


# ── La comparaison ───────────────────────────────────────────────────────────

def test_le_dernier_scrutin_concorde_avec_les_memes_effectifs():
    assert re_.comparer(_scrutins(PAR_SCRUTIN)[9578], _unites_9578()) == []


def test_un_membre_de_moins_est_un_ecart():
    ecarts = re_.comparer(_scrutins(PAR_SCRUTIN)[9578], _unites_9578(PO845425=46))
    assert [(e["unite"], e["an"], e["nous"], e["jour_de_changement"]) for e in ecarts] == [
        ("PO845425", 47, 46, False)]


def test_un_organe_sans_fiche_est_un_ecart():
    unites = [u for u in _unites_9578() if u.cle != "PO872880"]
    ecarts = re_.comparer(_scrutins(PAR_SCRUTIN)[9578], unites)
    assert [(e["unite"], e["an"], e["nous"]) for e in ecarts] == [("organe PO872880", 17, None)]


def test_un_ecart_le_lendemain_d_un_changement_est_tolere():
    """Les ministres de septembre 2024 quittent leur groupe le 21/10, leurs
    suppléants y entrent le 23/10 : le 22, nous ne comptons ni les uns ni les
    autres. Un jour de part et d'autre d'un changement est toléré."""
    unites = _unites_9578()
    dr = next(u for u in unites if u.cle == "PO845425")
    dr.periodes[0] = [{"debut": "2024-07-19", "fin": "2026-11-01"}]
    dr.__post_init__()
    ecarts = re_.comparer(_scrutins(PAR_SCRUTIN)[9578], unites)
    assert [(e["unite"], e["jour_de_changement"]) for e in ecarts] == [("PO845425", True)]


def test_un_changement_trois_jours_avant_n_est_pas_tolere():
    unites = _unites_9578()
    dr = next(u for u in unites if u.cle == "PO845425")
    dr.periodes[0] = [{"debut": "2024-07-19", "fin": "2026-10-30"}]
    dr.__post_init__()
    ecarts = re_.comparer(_scrutins(PAR_SCRUTIN)[9578], unites)
    assert [(e["unite"], e["jour_de_changement"]) for e in ecarts] == [("PO845425", False)]


def test_un_groupe_absent_de_la_ventilation_n_est_pas_un_ecart():
    """Le scrutin n° 2418 de la XVe (07/01/2020) ne ventile pas le MoDem."""
    scrutin = _scrutins(PAR_SCRUTIN)[2418]
    unites = [_unite(o, o, n, debut="2017-06-27") for o, n in scrutin.effectifs.items()]
    unites.append(_unite("AN:DEM:15", "PO774834", 46, debut="2017-06-27"))
    bilan = re_.controler("15", [scrutin], unites, "2017-06-27", set())
    assert (bilan.groupe_absent_de_la_source, bilan.en_ecart) == (1, 0)


# ── Le bilan ─────────────────────────────────────────────────────────────────

def test_un_ecart_valide_ne_revient_pas_tant_que_les_comptes_ne_bougent_pas():
    scrutin = _scrutins(PAR_SCRUTIN)[9578]
    unites = _unites_9578(PO845425=46)
    valide = {("17", "2026-11-02", "PO845425", 47, 46)}
    assert re_.controler("17", [scrutin], unites, None, valide).seulement_valides == 1
    autre = re_.controler("17", [scrutin], _unites_9578(PO845425=45), None, valide)
    assert (autre.en_ecart, list(autre.ecarts)) == (1, [("2026-11-02", "PO845425", 47, 45)])


def test_avant_la_constitution_des_groupes_rien_ne_se_compare():
    bilan = re_.controler("14", [_scrutins(XIV)[1]], [], "2012-07-10", set())
    assert (bilan.avant_constitution, bilan.en_ecart) == (1, 0)


def test_bout_en_bout(tmp_path):
    """Des fiches de groupe et des non-inscrits sur le disque, l'archive
    fournie en local, le fichier des écarts validés : le rapport et le JSON que
    le workflow lit (`scrutins_en_ecart`)."""
    groupes = tmp_path / "groupes"
    groupes.mkdir()
    for organe, n in EFFECTIFS_9578.items():
        if organe == "PO840056":
            continue
        n = {"PO845425": 46, "PO845485": 24}.get(organe, n)
        fiche = {"groupe_id": f"AN:{organe}:17", "historique_noms": [{"organe_an": organe}],
                 "membres": [{"periodes": [{"debut": "2024-07-19", "fin": None}]}] * n}
        (groupes / f"groupe-AN-{organe}-17.json").write_text(json.dumps(fiche), encoding="utf-8")
    non_inscrits = tmp_path / "non_inscrits.json"
    non_inscrits.write_text(json.dumps({"legislatures": [{
        "legislature": "17", "organe_ref": "PO840056", "date_constitution_groupes": "2024-07-18",
        "membres": [{"periodes": [{"debut": "2024-07-19", "fin": None}]}] * 11}]}), encoding="utf-8")
    valides = tmp_path / "valides.json"
    valides.write_text(json.dumps({"ecarts": [
        {"legislature": "17", "date": "2026-11-02", "unite": "AN:PO845485:17", "an": 23, "nous": 24}]}),
        encoding="utf-8")
    out, out_json = tmp_path / "r.md", tmp_path / "r.json"
    args = ["--groupes-dir", str(groupes), "--non-inscrits", str(non_inscrits), "--valides", str(valides),
            "--out", str(out), "--out-json", str(out_json)]
    args += [f"--archive=17={PAR_SCRUTIN}", "--legislature=17"]
    assert re_.main(args) == 0
    resume = json.loads(out_json.read_text(encoding="utf-8"))
    # Les scrutins d'autres législatures rangés dans la même archive de test
    # sont écartés par leur champ `legislature`.
    assert (resume["scrutins"], resume["scrutins_en_ecart"]) == (2, 1)
    assert [(e["unite"], e["an"], e["nous"]) for e in resume["ecarts"]] == [("AN:PO845425:17", 47, 46)]
    assert "AN:PO845425:17" in out.read_text(encoding="utf-8")
