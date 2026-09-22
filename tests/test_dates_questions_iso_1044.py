"""#1044 — une date de question doit être lisible par un filtre de période.

`_parse_question_entry` recopiait `infoJO.dateJO` telle que la source la
présente. Mesuré le 20/09/2026 sur les 1 217 384 interventions publiées :
**715 dates en `JJ/MM/AAAA`** et 167 vides, sur 12 profils `candidat_declare`,
toutes des questions. Les filtres par période comparent des chaînes ISO : ces
entrées ne tombaient dans aucune fenêtre et disparaissaient **sans être
comptées comme écartées**.

Le lot a deux moitiés, et la seconde est celle qui atteint le corpus : les
interventions se fusionnent en additif pur aux deux étages, donc une date déjà
publiée ne se serait jamais corrigée seule. C'est le défaut de #997, au même
endroit.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from candidate_profile import _parse_question_entry, normaliser_date_jo  # noqa: E402
from merge_profile import merge_pivot_profile, merge_raw_profile, normaliser_dates_interventions  # noqa: E402


# ── La normalisation à la collecte ────────────────────────────────────────

def test_une_date_jour_mois_an_devient_iso():
    assert normaliser_date_jo("26/03/2019") == "2019-03-26"


def test_une_date_deja_iso_ne_bouge_pas():
    assert normaliser_date_jo("2019-03-26") == "2019-03-26"


def test_une_date_absente_reste_absente():
    """Une `dateJO` absente n'est pas devinée par la normalisation (§2
    règle 5). Les 167 QG sans date se datent ailleurs — voir plus bas."""
    assert normaliser_date_jo(None) is None
    assert normaliser_date_jo("") is None
    assert normaliser_date_jo("   ") is None


def test_une_forme_inconnue_n_est_pas_devinee():
    """Reformater n'est pas deviner : ce qui n'est pas reconnu passe tel quel,
    et sera visible, plutôt que d'être transformé en une date inventée."""
    assert normaliser_date_jo("mars 2019") == "mars 2019"


# ── La reprise des entrées déjà publiées ──────────────────────────────────

def test_la_passe_reformate_une_entree_ancienne():
    entrees = [{"intervention_id": "q1", "date": "26/03/2019",
                "date_reponse": "02/04/2019"}]

    normaliser_dates_interventions(entrees)

    assert entrees[0]["date"] == "2019-03-26"
    assert entrees[0]["date_reponse"] == "2019-04-02"


def test_la_passe_n_invente_aucune_date():
    entrees = [{"intervention_id": "q2", "date": None, "date_reponse": ""}]

    normaliser_dates_interventions(entrees)

    assert entrees[0]["date"] is None
    assert entrees[0]["date_reponse"] == ""


def test_le_corpus_deja_publie_est_repris_par_la_fusion():
    """La moitié qui compte : sans elle, la date publiée gagne et ne bouge
    jamais — les interventions se fusionnent en additif pur."""
    old = {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [],
           "interventions": [{"intervention_id": "q1", "date": "26/03/2019",
                              "type_detail": "question"}]}
    new = {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [],
           "interventions": []}

    merged = merge_raw_profile(old, new)

    assert merged["interventions"][0]["date"] == "2019-03-26"


# ── Les 167 dates vides : des questions au gouvernement (22/09/2026) ──────
#
# Toutes `sous_type: "QG"`. La source ne publie jamais le texte d'une QG,
# posée à l'oral (8 574 sur 8 574, législatures 15 à 17), et la date se lisait
# là. La question paraît au JO dans le même compte rendu que la réponse : sa
# date de parution est celle-là (arbitré le 22/09/2026).

#: `QANR5L17QG689` telle que l'archive AN la publie, réduite aux champs lus.
QG_689 = {"question": {
    "uid": "QANR5L17QG689", "type": "QG",
    "auteur": {"identite": {"acteurRef": "PA335999", "mandatRef": "PM843494"},
               "groupe": {"organeRef": "PO845439", "abrege": "ECOS", "developpe": "Écologiste et Social"}},
    "minInt": {"organeRef": "PO855098", "abrege": "Agriculture, souveraineté alimentaire",
               "developpe": "Ministère de l’agriculture et de la souveraineté alimentaire"},
    "textesQuestion": None,
    "textesReponse": {"texteReponse": {
        "infoJO": {"typeJO": "JO_DEBAT", "dateJO": "2025-05-21", "pageJO": "5032", "numJO": None,
                   "urlLegifrance": None, "referenceNOR": None},
        "texte": "</p><p align=\"CENTER\"> UTILISATION DE L'ACÉTAMIPRIDE"}},
}}


def test_une_qg_collectee_porte_la_date_de_son_compte_rendu():
    _, record = _parse_question_entry(QG_689, "QG")

    assert record["date"] == "2025-05-21"
    assert record["date_reponse"] == "2025-05-21"


def test_une_question_ecrite_sans_texte_reste_sans_date():
    """La règle vaut pour la QG, posée à l'oral — pas pour une question écrite,
    dont la date de dépôt n'est pas celle de la réponse."""
    qe = {"question": {**QG_689["question"], "type": "QE"}}

    _, record = _parse_question_entry(qe, "QE")

    assert record["date"] is None


def test_une_qg_deja_publiee_sans_date_est_reprise_aux_deux_etages():
    ancienne = {"intervention_id": "question_QANR5L16QG674", "id": "question_QANR5L16QG674",
                "type_detail": "question", "sous_type": "QG", "date": None,
                "date_reponse": "2023-03-22"}
    for fusion in (merge_raw_profile, merge_pivot_profile):
        old = {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [],
               "interventions": [dict(ancienne)]}
        new = {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [],
               "interventions": []}

        merged = fusion(old, new)

        assert merged["interventions"][0]["date"] == "2023-03-22", fusion.__name__
