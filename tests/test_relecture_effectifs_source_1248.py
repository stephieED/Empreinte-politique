"""Effectifs des groupes confrontés à ceux de chaque scrutin (#1248, lot 5).

Les archives sont des extraits verbatim de l'open data de l'Assemblée, relevés
le 03/11/2026 : quatre fichiers de scrutin de la XVe à la XVIIe (le dernier de
la XVIIe, un scrutin dont les groupes sont publiés sous « PO0 », le scrutin du
Congrès rangé dans l'archive de la XVIe, un scrutin de la XVe dont la
ventilation omet le MoDem), et l'enveloppe du fichier unique de la XIVe réduite
à deux de ses scrutins, recopiés tels quels.
"""

import datetime as dt
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


def test_un_changement_trois_jours_avant_est_tolere():
    """Alix Fruchon quitte DR le 30/10/2026 dans AMO30 ; le scrutin du 02/11
    la compte encore à DR. Le compte d'un scrutin suit avec 2 ou 3 jours."""
    unites = _unites_9578()
    dr = next(u for u in unites if u.cle == "PO845425")
    dr.periodes[0] = [{"debut": "2024-07-19", "fin": "2026-10-30"}]
    dr.__post_init__()
    ecarts = re_.comparer(_scrutins(PAR_SCRUTIN)[9578], unites)
    assert [(e["unite"], e["jour_de_changement"]) for e in ecarts] == [("PO845425", True)]


def test_un_changement_quatre_jours_avant_n_est_pas_tolere():
    unites = _unites_9578()
    dr = next(u for u in unites if u.cle == "PO845425")
    dr.periodes[0] = [{"debut": "2024-07-19", "fin": "2026-10-29"}]
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
    index = tmp_path / "scrutins.json"
    index.write_text(json.dumps({"scrutins": [{"legislature": "17", "numero_scrutin": "9578"}]}), encoding="utf-8")
    args = ["--groupes-dir", str(groupes), "--non-inscrits", str(non_inscrits), "--valides", str(valides),
            "--index-scrutins", str(index), "--sans-amo30", "--out", str(out), "--out-json", str(out_json)]
    args += [f"--archive=17={PAR_SCRUTIN}", "--legislature=17"]
    assert re_.main(args) == 0
    resume = json.loads(out_json.read_text(encoding="utf-8"))
    # Les scrutins d'autres législatures rangés dans la même archive de test
    # sont écartés par leur champ `legislature`.
    assert (resume["scrutins"], resume["scrutins_en_ecart"]) == (2, 1)
    assert [(e["unite"], e["an"], e["nous"]) for e in resume["ecarts"]] == [("AN:PO845425:17", 47, 46)]
    # Le scrutin n° 489 de l'archive manque à l'index : un jour d'effectif en
    # écart plus un scrutin absent, deux signalements pour l'issue.
    assert (resume["scrutins_absents"], resume["a_signaler"]) == (1, 2)
    assert "AN:PO845425:17" in out.read_text(encoding="utf-8")


# ── Les scrutins de l'archive contre ceux de l'index (#1248, lot 5 bis) ──────

def test_un_scrutin_de_l_archive_absent_de_l_index_est_releve():
    bilan = re_.Bilan("17")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), {9578})
    assert (bilan.scrutins_de_l_archive, bilan.absents_de_l_index, bilan.absents_de_l_archive) == (2, [489], [])


def test_un_scrutin_publie_que_l_archive_ne_porte_pas_est_releve():
    bilan = re_.Bilan("17")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), {489, 9578, 9579})
    assert (bilan.absents_de_l_index, bilan.absents_de_l_archive) == ([], [9579])


def test_le_congres_n_entre_pas_dans_la_numerotation():
    """Son n° 1 double le n° 1 de la XVIe : il ne doit ni manquer à l'index ni
    masquer l'absence du vrai n° 1."""
    bilan = re_.Bilan("16")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), set())
    assert (bilan.scrutins_de_l_archive, bilan.absents_de_l_index) == (0, [])


def test_les_numeros_que_l_archive_saute_sont_ceux_de_la_source():
    bilan = re_.Bilan("17")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), {489, 9578})
    assert len(bilan.trous_de_l_archive) == 9578 - 2
    assert (bilan.absents_de_l_index, bilan.absents_de_l_archive) == ([], [])


def test_un_scrutin_plus_recent_que_l_index_n_est_pas_encore_collecte():
    """Le run 41932814357 (05/11/2026) : la collecte a lu l'archive arrêtée au
    02/11, le contrôle celle publiée sept minutes après son départ."""
    bilan = re_.Bilan("17")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), set(), "2026-11-01", dt.date(2026, 11, 3))
    assert (bilan.pas_encore_collectes, bilan.absents_de_l_index) == ([9578], [489])
    _, resume = re_.rapport([bilan])
    assert (resume["scrutins_pas_encore_collectes"], resume["scrutins_absents"]) == (1, 1)


def test_une_collecte_arretee_ne_se_cache_pas_derriere_le_delai():
    bilan = re_.Bilan("17")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), set(), "2026-11-01", dt.date(2026, 11, 6))
    assert (bilan.pas_encore_collectes, bilan.absents_de_l_index) == ([], [489, 9578])


def test_un_scrutin_anterieur_au_dernier_de_l_index_reste_absent():
    bilan = re_.Bilan("17")
    re_.couvrir(bilan, _scrutins(PAR_SCRUTIN).values(), set(), "2026-11-02", dt.date(2026, 11, 3))
    assert (bilan.pas_encore_collectes, bilan.absents_de_l_index) == ([], [489, 9578])


def test_la_date_de_l_index_se_lit_par_legislature(tmp_path):
    index = tmp_path / "scrutins.json"
    index.write_text(json.dumps({"scrutins": [
        {"legislature": "17", "date": "2026-11-02"}, {"legislature": "17", "date": "2024-07-19"},
        {"legislature": "16", "date": None}]}), encoding="utf-8")
    assert re_.dates_publiees(index) == {"17": "2026-11-02"}


def test_l_index_publie_se_lit_par_legislature(tmp_path):
    index = tmp_path / "scrutins.json"
    index.write_text(json.dumps({"scrutins": [
        {"legislature": "17", "numero_scrutin": "9578"}, {"legislature": "16", "numero_scrutin": "1"},
        {"legislature": "17", "numero_scrutin": None}]}), encoding="utf-8")
    assert re_.numeros_publies(index) == {"17": {9578}, "16": {1}}



# ── Le référentiel AMO30 juge notre collecte (#1248, critères du 03/11/2026) ──

def _reference(**effectifs):
    """Un index GP à la forme d'`an_roster.construire_index_gp` : `n` acteurs
    distincts par organe, tous membres depuis 2024."""
    return re_.ReferenceAmo30({
        organe: [[f"PA{organe}{k}", "2024-07-19", None] for k in range(n)]
        for organe, n in effectifs.items()
    })


def test_le_referentiel_compte_des_acteurs_distincts_a_la_date():
    """Les dates d'AMO30 portent parfois une heure ; un acteur à deux mandats
    dans le même organe ne compte qu'une fois ; la fin est incluse."""
    ref = re_.ReferenceAmo30({"PO1": [
        ["PA1", "2026-10-31+01:00", None],
        ["PA2", "2025-11-14", "2026-10-30"],
        ["PA3", "2024-07-19", "2026-11-02"],
        ["PA3", "2024-07-19", None],
    ]})
    assert ref.effectif({"PO1"}, "2026-11-02") == 2
    assert ref.effectif({"PO1"}, "2026-10-30") == 2


def test_nous_comptons_comme_amo30_et_le_scrutin_autrement_est_interne():
    """Alix Fruchon : AMO30 la sort de DR le 30/10/2026, le scrutin du 02/11
    la compte encore à DR. Nous comptons comme AMO30 : rien à signaler."""
    scrutin = _scrutins(PAR_SCRUTIN)[9578]
    effectifs = {**EFFECTIFS_9578, "PO845425": 46}
    bilan = re_.controler("17", [scrutin], _unites_9578(PO845425=46), None, set(), _reference(**effectifs))
    assert (bilan.desaccords_internes, bilan.en_ecart) == (1, 0)


def test_un_ecart_avec_amo30_est_signale_meme_pres_d_un_changement():
    """Sans référentiel, un changement la veille serait toléré. Avec lui, nous
    divergeons de notre propre source : c'est notre lecture, signalée."""
    unites = _unites_9578()
    dr = next(u for u in unites if u.cle == "PO845425")
    dr.periodes[0] = [{"debut": "2024-07-19", "fin": "2026-11-01"}]
    dr.__post_init__()
    scrutin = _scrutins(PAR_SCRUTIN)[9578]
    assert re_.controler("17", [scrutin], unites, None, set()).en_ecart == 0
    bilan = re_.controler("17", [scrutin], unites, None, set(), _reference(**EFFECTIFS_9578))
    assert (bilan.en_ecart, list(bilan.ecarts)) == (1, [("2026-11-02", "PO845425", 47, 46)])


def test_le_rapport_dit_quel_critere_a_juge():
    texte, resume = re_.rapport([re_.Bilan("17")], reference_lue=None)
    assert resume["reference_amo30"] is True and "désaccord interne" in texte
    texte, resume = re_.rapport([re_.Bilan("17")], reference_lue="RosterAnIndisponible: archive absente")
    assert resume["reference_amo30"] is False and "Référentiel AMO30 non lu" in texte
