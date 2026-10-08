"""Un paragraphe de compte rendu republié sous un autre rang n'est publié qu'une fois.

Les deux entrées sont copiées de `pivot_data/profiles/emeric-salmon.pivot.json`
(main `3665078d3`, 08/10/2026) : le même paragraphe `4169920`, aux rangs 209 et
369 du compte rendu n° 4, la seconde avec la coquille « çà » corrigée.
"""
from __future__ import annotations

import copy

from merge_profile import dedoublonner_paragraphes_syceron, merge_pivot_profile

AVANT = {
    "intervention_id": "syceron_CRSANR5L17S2027O1N004_000209", "date": "2026-10-02",
    "type_detail": "debat",
    "theme_officiel": "Réponse intégrale aux violences sexuelles et sexistes contre les femmes et les enfants",
    "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip",
    "source": {"type": "syceron", "url": None, "source_id": None, "legislature": "17"},
    "collecte": "extrait",
    "texte": "C’est pas possible de dire çà ! (MM. Thomas Ménagé et Éric Salmon se lèvent et descendent de leurs bancs. – Exclamations sur les bancs du groupe RN.)",
    "texte_tronque": False, "id_syceron": "4169920",
}
APRES = dict(
    AVANT,
    intervention_id="syceron_CRSANR5L17S2027O1N004_000369",
    texte=AVANT["texte"].replace("çà", "ça"),
)
AUTRE = dict(AVANT, intervention_id="syceron_CRSANR5L17S2027O1N004_000210", id_syceron="4169921")


def test_le_paragraphe_republie_n_est_garde_qu_une_fois():
    merged = [copy.deepcopy(AVANT), copy.deepcopy(AUTRE), copy.deepcopy(APRES)]
    resultat = dedoublonner_paragraphes_syceron(merged, [APRES], "intervention_id")
    assert [i["id_syceron"] for i in resultat] == ["4169920", "4169921"]


def test_la_version_que_la_source_publie_aujourd_hui_l_emporte():
    merged = [copy.deepcopy(AVANT), copy.deepcopy(APRES)]
    resultat = dedoublonner_paragraphes_syceron(merged, [APRES], "intervention_id")
    assert resultat[0]["intervention_id"] == APRES["intervention_id"]
    assert "ça !" in resultat[0]["texte"]


def test_une_forme_plus_riche_n_est_jamais_remplacee_par_une_plus_pauvre():
    complete = {k: v for k, v in AVANT.items() if k != "collecte"}
    reduite = dict(APRES, collecte="theme_seul", texte=None)
    resultat = dedoublonner_paragraphes_syceron([complete, reduite], [reduite], "intervention_id")
    assert len(resultat) == 1 and "collecte" not in resultat[0]


def test_une_parole_hors_syceron_n_est_jamais_dedoublonnee():
    question = {"intervention_id": "question_QANR5L17QG42", "id_syceron": "4169920"}
    resultat = dedoublonner_paragraphes_syceron(
        [copy.deepcopy(AVANT), question], [], "intervention_id")
    assert len(resultat) == 2


def test_la_fusion_pivot_retire_les_copies_deja_publiees():
    ancien = {"id": "emeric-salmon", "interventions": [copy.deepcopy(AVANT), copy.deepcopy(APRES)]}
    neuf = {"id": "emeric-salmon", "interventions": [copy.deepcopy(APRES)]}
    fusionne = merge_pivot_profile(ancien, neuf)
    assert [i["intervention_id"] for i in fusionne["interventions"]] == [APRES["intervention_id"]]
