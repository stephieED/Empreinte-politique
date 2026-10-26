"""#1354 — l'ordre du jour des séances publiques, un fichier par législature.

`fixtures/ordre_du_jour_1354/Agenda_17_extrait.zip` : 35 réunions de séance
publique copiées octet pour octet de l'archive Agenda XVIIe téléchargée le
26/10/2026, plus une séance du Sénat et une réunion de commission, à écarter :

- les six séances de la proposition de loi « visant à simplifier l'ouverture
  des débits de boisson en zone rurale » : le dossier n'est porté que par la
  Discussion du 10/03/2025 à 16 h ;
- les séances où paraît le « projet de loi de financement de la sécurité
  sociale pour 2025 », dont l'intitulé mène à DEUX dossiers (le texte tombé avec
  la censure de décembre 2024, puis celui redéposé en 2025) ;
- une séance de questions au Gouvernement, et une séance supprimée.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import ordre_du_jour_an as odj

ARCHIVE = Path(__file__).parent / "fixtures" / "ordre_du_jour_1354" / "Agenda_17_extrait.zip"
DEBITS = "DLR5L17N51453"
DISCUSSION_DEBITS = "RUANR5L17S2025IDS29157"


@pytest.fixture(scope="module")
def document():
    return odj.construire("17", ARCHIVE, source_url="https://exemple/Agenda.json.zip", genere_le="2026-10-26")


def _points(document, predicat):
    return [(s, p) for s in document["seances"] for p in s["points"] if predicat(s, p)]


@pytest.mark.parametrize("objet, attendu", [
    ("Discussion de la proposition de loi visant à simplifier l’ouverture des débits de boisson en zone rurale (n° 412)",
     "proposition de loi visant à simplifier l'ouverture des débits de boisson en zone rurale"),
    ("Suite de la discussion de la proposition de loi, adoptée par le Sénat, visant à faciliter le maintien en rétention",
     "proposition de loi visant à faciliter le maintien en rétention"),
    ("Discussion, en nouvelle lecture, du projet de loi de finances pour 2025",
     "projet de loi de finances pour 2025"),
    ("Questions au Gouvernement", None),
])
def test_cle_d_intitule(objet, attendu):
    assert odj.cle_d_intitule(objet) == attendu


def test_seules_les_seances_publiques_de_l_assemblee_sont_lues(document):
    uids = [s["uid"] for s in document["seances"]]
    assert len(uids) == 35
    assert all(u.startswith("RUAN") and "IDS" in u for u in uids)
    assert uids == [s["uid"] for s in sorted(document["seances"], key=lambda s: s["debut"])]


def test_une_seance_supprimee_garde_son_etat(document):
    etats = {s["etat"] for s in document["seances"]}
    assert "Supprimé" in etats and "Confirmé" in etats


def test_le_dossier_de_la_source_reste_celui_de_la_source(document):
    (seance, point), = _points(document, lambda s, p: s["uid"] == DISCUSSION_DEBITS and "débits de boisson" in p["objet"])
    assert point["dossiers"] == [DEBITS]
    assert point["dossier_retrouve"] is None and point["dossier_non_resolu"] is None


def test_les_suites_de_la_discussion_retrouvent_le_dossier_par_l_intitule(document):
    """Le 10/03 au soir, le 31/03 et le 01/04 : aucune ne porte le dossier, toutes
    le reçoivent de la Discussion du 10/03 à 16 h, et le disent."""
    suites = _points(document, lambda s, p: "débits de boisson" in p["objet"] and s["uid"] != DISCUSSION_DEBITS
                     and s["etat"] == "Confirmé")
    assert len(suites) >= 4
    discussion = _points(document, lambda s, p: s["uid"] == DISCUSSION_DEBITS)[0][1]["uid"]
    for _, point in suites:
        assert point["dossiers"] == []
        assert point["dossier_retrouve"] == {"dossier_ref": DEBITS, "par": odj.RETROUVE_PAR_INTITULE,
                                             "point_source": discussion}


def test_un_intitule_a_deux_dossiers_ne_choisit_pas(document):
    """Le PLFSS 2025 a deux dossiers : un point sans dossier reste sans dossier,
    et nomme les deux."""
    ambigus = _points(document, lambda s, p: (p["dossier_non_resolu"] or {}).get("motif") == odj.MOTIF_INTITULE_AMBIGU)
    assert ambigus
    for _, point in ambigus:
        assert "sécurité sociale pour 2025" in point["objet"]
        assert point["dossier_retrouve"] is None
        assert len(point["dossier_non_resolu"]["dossiers"]) == 2


def test_un_point_qui_ne_nomme_aucun_texte_le_dit(document):
    questions = _points(document, lambda s, p: p["type"] == "Questions au Gouvernement")
    assert questions
    assert all(p["dossier_non_resolu"] == {"motif": odj.MOTIF_HORS_TEXTE} for _, p in questions)


def test_chaque_point_a_exactement_une_origine_de_dossier(document):
    for _, point in _points(document, lambda s, p: True):
        origines = [bool(point["dossiers"]), point["dossier_retrouve"] is not None,
                    point["dossier_non_resolu"] is not None]
        assert sum(origines) == 1, point["uid"]
        if point["dossier_non_resolu"]:
            assert point["dossier_non_resolu"]["motif"] in odj.KNOWN_MOTIFS_DOSSIER_NON_RESOLU


def test_aucune_duree_ni_presence_n_est_publiee(document):
    """§2 règle 3 : la séance publie les bornes que la source annonce, rien de calculé."""
    cles = {k for s in document["seances"] for k in s}
    assert cles == {"uid", "date", "debut", "fin", "etat", "session_ref", "compte_rendu_ref", "points"}


def test_l_ecriture_ne_change_pas_un_fichier_dont_seule_la_date_bouge(tmp_path):
    assert odj.main(["--agenda", f"17:{ARCHIVE}", "--out-dir", str(tmp_path)]) == 0
    chemin = tmp_path / "17.json"
    ecrit = json.loads(chemin.read_text(encoding="utf-8"))
    assert ecrit["schema_version"] == odj.SCHEMA_VERSION and ecrit["legislature"] == 17
    ecrit["genere_le"] = "2020-01-01"
    chemin.write_text(json.dumps(ecrit), encoding="utf-8")
    assert odj.main(["--agenda", f"17:{ARCHIVE}", "--out-dir", str(tmp_path)]) == 0
    assert json.loads(chemin.read_text(encoding="utf-8"))["genere_le"] == "2020-01-01"
