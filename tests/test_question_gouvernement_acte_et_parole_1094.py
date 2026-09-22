"""#1094 — une question au gouvernement : un acte, et ses tours de parole reliés à lui.

L'acte vient de questions.assemblee-nationale.fr (`type_detail: "question"`,
`sous_type: "QG"`, daté par le JO) ; ses tours de parole viennent du compte
rendu Syceron (`type_detail: "question_gouvernement"`, datés par la séance).
Chaque tour reçoit `question_ref` quand le thème confirme le lien.

Toutes les entrées ci-dessous sont COPIÉES du corpus publié le 22/09/2026
(profils `philippe-brun`, `fabien-roussel`, `nicolas-dupont-aignan`), réduites
aux champs utiles ; les enregistrements questions.an sont des réductions
verbatim des archives AN de la XVe (`QANR5L15QG969`, `QANR5L15QG2090`).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import candidate_profile as cp  # noqa: E402
from merge_profile import merge_pivot_profile, merge_raw_profile  # noqa: E402
from schema_pivot import rattacher_parole_aux_questions  # noqa: E402

SYCERON_17 = "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip"
SYCERON_15 = "https://data.assemblee-nationale.fr/static/openData/repository/15/vp/syceronbrut/syseron.xml.zip"

# philippe-brun — l'acte et trois tours de même thème : deux de la séance du
# 28/04/2026, la veille de la parution, et un du 05/05/2026, une autre QG.
ACTE_BRUN = {
    "intervention_id": "question_QANR5L17QG1472", "date": "2026-04-29",
    "type_detail": "question", "sujet": "Prix des carburants", "texte": None,
    "source_url": "https://questions.assemblee-nationale.fr/q17/QANR5L17QG1472.htm",
    "theme_officiel": None, "source": None, "sous_type": "QG", "date_reponse": "2026-04-29",
}


def _tour_brun(intervention_id: str, date: str) -> dict:
    return {
        "intervention_id": intervention_id, "date": date, "type_detail": "question_gouvernement",
        "theme_officiel": "Prix des carburants", "source_url": SYCERON_17,
        "source": {"type": "syceron", "url": None, "source_id": None, "legislature": "17"},
        "collecte": "theme_seul",
    }


TOURS_BRUN = [
    _tour_brun("syceron_CRSANR5L17S2026O1N220_000027", "2026-05-05"),
    _tour_brun("syceron_CRSANR5L17S2026O1N212_000076", "2026-04-28"),
    _tour_brun("syceron_CRSANR5L17S2026O1N212_000063", "2026-04-28"),
]

# fabien-roussel, XVe — le compte rendu ne publie pas de thème : il est dans `sujet`.
TOUR_ROUSSEL_XV = {
    "intervention_id": "syceron_CRSANR5L15S2018O1N256_000110", "date": "2018-06-06",
    "type_detail": "question_gouvernement", "sujet": "Pouvoir d’achat des salariés",
    "theme_officiel": None, "source_url": SYCERON_15, "source": None,
    "dossier": {"point_ordre_du_jour": "Questions au Gouvernement > Pouvoir d’achat des salariés"},
}
QG_ROUSSEL_XV = {"question": {
    "uid": "QANR5L15QG969", "type": "QG",
    "indexationAN": {"rubrique": "politique économique", "teteAnalyse": None,
                     "ANALYSE": {"ANA": "pouvoir d'achat des salariés"}},
    "auteur": {"identite": {"acteurRef": "PA720692", "mandatRef": "PM723042"},
               "groupe": {"organeRef": "PO730940", "abrege": "GDR"}},
    "minInt": {"abrege": "Économie et finances", "developpe": "Ministère de l'économie et des finances"},
    "textesReponse": {"texteReponse": {"infoJO": {"typeJO": "JO_DEBAT", "dateJO": "07/06/2018"}}},
}}

# nicolas-dupont-aignan, XVe — la source a écrit « ventre » pour « vente ».
TOUR_NDA_XV = {
    "intervention_id": "syceron_CRSANR5L15S2019O1N288_000072", "date": "2019-06-25",
    "type_detail": "question_gouvernement",
    "sujet": "Vente de la branche énergie d’Alstom à General Electric",
    "theme_officiel": None, "source_url": SYCERON_15, "source": None,
}
QG_NDA_XV = {"question": {
    "uid": "QANR5L15QG2090", "type": "QG",
    "indexationAN": {"rubrique": "industrie", "teteAnalyse": None,
                     "ANALYSE": {"ANA": "ventre de la branche énergie d'Alstom à General Electric"}},
    "auteur": {"identite": {"acteurRef": "PA1206"}},
    "textesReponse": {"texteReponse": {"infoJO": {"typeJO": "JO_DEBAT", "dateJO": "26/06/2019"}}},
}}


def _acte_depuis(brut: dict) -> dict:
    """L'acte tel que le vrai parseur le rend, à la forme d'une entrée pivot."""
    _, record = cp._parse_question_entry(copy.deepcopy(brut), "QG")
    return {
        "intervention_id": f"question_{record['uid']}", "date": record["date"],
        "type_detail": "question", "sous_type": "QG", "sujet": record["sujet"],
    }


def _refs(interventions: list[dict]) -> dict[str, str]:
    return {i["intervention_id"]: i["question_ref"] for i in interventions if "question_ref" in i}


def test_les_tours_de_la_seance_sont_relies_a_l_acte_et_pas_ceux_d_une_autre_qg():
    resultat = rattacher_parole_aux_questions([ACTE_BRUN, *copy.deepcopy(TOURS_BRUN)])

    assert _refs(resultat) == {
        "syceron_CRSANR5L17S2026O1N212_000076": "question_QANR5L17QG1472",
        "syceron_CRSANR5L17S2026O1N212_000063": "question_QANR5L17QG1472",
    }
    assert "question_ref" not in resultat[0], "l'acte ne pointe pas vers lui-même"


def test_la_xve_lit_son_sujet_sous_analyse_ana():
    assert _acte_depuis(QG_ROUSSEL_XV)["sujet"] == "pouvoir d'achat des salariés"


def test_en_xve_le_theme_du_tour_se_lit_dans_son_sujet():
    acte = _acte_depuis(QG_ROUSSEL_XV)
    assert acte["date"] == "2018-06-07"

    resultat = rattacher_parole_aux_questions([acte, copy.deepcopy(TOUR_ROUSSEL_XV)])

    assert _refs(resultat) == {"syceron_CRSANR5L15S2018O1N256_000110": "question_QANR5L15QG969"}


def test_un_intitule_qui_differe_ne_se_rapproche_pas():
    """« ventre » n'est pas « vente » : rapprocher deux intitulés serait une forme
    devinée, publiée comme un fait. Le tour reste sans lien."""
    resultat = rattacher_parole_aux_questions([_acte_depuis(QG_NDA_XV), copy.deepcopy(TOUR_NDA_XV)])

    assert _refs(resultat) == {}


def test_sans_sujet_pas_de_lien_par_la_date_seule():
    acte = {**_acte_depuis(QG_ROUSSEL_XV), "sujet": None}

    assert _refs(rattacher_parole_aux_questions([acte, copy.deepcopy(TOUR_ROUSSEL_XV)])) == {}


def test_le_lien_est_derive_un_lien_perime_disparait():
    perime = {**copy.deepcopy(TOURS_BRUN[0]), "question_ref": "question_QANR5L17QG1472"}

    assert _refs(rattacher_parole_aux_questions([ACTE_BRUN, perime])) == {}


def test_la_fusion_pivot_recalcule_le_lien_sur_les_deux_chemins():
    profil = {"interventions": [ACTE_BRUN, *copy.deepcopy(TOURS_BRUN)], "meta": {}}

    premier = merge_pivot_profile(None, copy.deepcopy(profil))
    fusionne = merge_pivot_profile(copy.deepcopy(profil), copy.deepcopy(profil))

    attendu = {
        "syceron_CRSANR5L17S2026O1N212_000076": "question_QANR5L17QG1472",
        "syceron_CRSANR5L17S2026O1N212_000063": "question_QANR5L17QG1472",
    }
    assert _refs(premier["interventions"]) == attendu
    assert _refs(fusionne["interventions"]) == attendu


def test_le_sujet_xve_atteint_la_question_deja_publiee_sans_sujet():
    """Fusion additive : l'entrée ancienne gagne. Sans report, la question
    publiée `sujet: null` le resterait à chaque régénération."""
    ancienne = {"intervention_id": "question_QANR5L15QG969", "date": "2018-06-07",
                "type_detail": "question", "sous_type": "QG", "sujet": None}
    neuve = {**ancienne, "sujet": "pouvoir d'achat des salariés"}

    pivot = merge_pivot_profile({"interventions": [ancienne], "meta": {}},
                                {"interventions": [neuve], "meta": {}})
    assert pivot["interventions"][0]["sujet"] == "pouvoir d'achat des salariés"

    brut_ancien = {"id": "question_QANR5L15QG969", "url": "https://questions.assemblee-nationale.fr/q15/QANR5L15QG969.htm",
                   "type_detail": "question", "sous_type": "QG", "sujet": None, "date": "2018-06-07"}
    brut = merge_raw_profile({"interventions": [brut_ancien]},
                             {"interventions": [{**brut_ancien, "sujet": "pouvoir d'achat des salariés"}]})
    assert brut["interventions"][0]["sujet"] == "pouvoir d'achat des salariés"


def test_un_index_de_questions_sans_marque_est_reconstruit(tmp_path, monkeypatch):
    """Les législatures closes ne sont jamais périmées (#555) : un index écrit
    avant la lecture de `ANALYSE.ANA` serait servi indéfiniment."""
    monkeypatch.setattr(cp, "QUESTIONS_CACHE_DIR", tmp_path)
    (tmp_path / "15").mkdir()
    (tmp_path / "15" / "index_par_acteur.json").write_text(
        json.dumps({"PA720692": [{"uid": "QANR5L15QG969", "sujet": None}]}), encoding="utf-8")
    monkeypatch.setattr(cp, "AN_QUESTIONS_PATH", {"15": {}})

    assert cp._build_acteur_questions_index("15") == {}, "l'index sans marque n'est pas servi"

    (tmp_path / "15" / "index_par_acteur.json").write_text(json.dumps({
        cp.CLE_FORMAT_INDEX_QUESTIONS: cp.FORMAT_INDEX_QUESTIONS,
        "PA720692": [{"uid": "QANR5L15QG969", "sujet": "pouvoir d'achat des salariés"}],
    }), encoding="utf-8")

    assert cp._build_acteur_questions_index("15") == {
        "PA720692": [{"uid": "QANR5L15QG969", "sujet": "pouvoir d'achat des salariés"}],
    }
