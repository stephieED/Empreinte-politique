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

from candidate_profile import normaliser_date_jo  # noqa: E402
from merge_profile import merge_raw_profile, normaliser_dates_interventions  # noqa: E402


# ── La normalisation à la collecte ────────────────────────────────────────

def test_une_date_jour_mois_an_devient_iso():
    assert normaliser_date_jo("26/03/2019") == "2019-03-26"


def test_une_date_deja_iso_ne_bouge_pas():
    assert normaliser_date_jo("2019-03-26") == "2019-03-26"


def test_une_date_absente_reste_absente():
    """Les 167 entrées sans `dateJO` sont une absence, pas un défaut à
    combler (§2 règle 5)."""
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
