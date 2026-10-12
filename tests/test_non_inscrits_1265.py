"""#1265 — la liste des députés non inscrits, avec leurs périodes.

Tout tourne sur `tests/fixtures/amo30_gp_leg16_17.zip`, **extraite de l'archive
réelle** (voir `test_an_roster.py`) : les organes `NI` y sont à leur taille
réelle sur la XVIe (615 mandats) et la XVIIe (675 mandats), et aucune valeur
n'y est inventée. Aucun réseau, aucune lecture de `pivot_data/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC))

import an_roster  # noqa: E402
import non_inscrits_amo30  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ARCHIVE = FIXTURES / "amo30_gp_leg16_17.zip"
TABLE = FIXTURES / "correspondance_acteurs_an_extrait.json"


@pytest.fixture(scope="module")
def index():
    return an_roster.construire_index_gp(ARCHIVE)


@pytest.fixture(scope="module")
def document(index):
    return non_inscrits_amo30.construire(index, {"PA720100": "aurelien-pradie"})


def _bloc(document, legislature):
    return next(b for b in document["legislatures"] if b["legislature"] == legislature)


def test_un_organe_non_inscrit_par_legislature_depuis_la_xive(index):
    organes = non_inscrits_amo30.organes_non_inscrits(index)
    assert list(organes) == ["14", "15", "16", "17"]
    assert organes["17"] == "PO840056"
    assert organes["16"] == "PO793087"


def test_le_transit_d_ouverture_est_ecarte_et_compte(document):
    """XVIe : 576 mandats `2022-06-22 → 2022-06-28`. XVIIe : 577 mandats clos
    le 2024-07-18. Écartés de la liste, mais comptés : un trou muet se lirait
    « personne n'était non inscrit »."""
    seizieme, dix_septieme = _bloc(document, "16"), _bloc(document, "17")
    assert seizieme["date_constitution_groupes"] == "2022-06-28"
    assert seizieme["transit_d_ouverture"] == {"mandats_ecartes": 576, "personnes": 576}
    assert dix_septieme["date_constitution_groupes"] == "2024-07-18"
    assert dix_septieme["transit_d_ouverture"] == {"mandats_ecartes": 577, "personnes": 577}
    assert len(seizieme["membres"]) == 39
    assert len(dix_septieme["membres"]) == 94


def test_aucune_periode_publiee_n_est_un_transit(document):
    for bloc in document["legislatures"]:
        for membre in bloc["membres"]:
            for periode in membre["periodes"]:
                assert not an_roster.est_mandat_de_transit(
                    periode["fin"], bloc["date_constitution_groupes"]
                ), (bloc["legislature"], membre)


def test_un_membre_porte_ses_periodes_sous_la_forme_des_fiches_de_groupe(document):
    """Aurélien Pradié, non inscrit depuis le lendemain de la constitution des
    groupes de la XVIIe : une période, ouverte."""
    pradie = next(m for m in _bloc(document, "17")["membres"] if m["acteur_ref"] == "PA720100")
    assert pradie == {
        "membre_id": "aurelien-pradie",
        "acteur_ref": "PA720100",
        "nom": "Aurélien Pradié",
        "periodes": [{"debut": "2024-07-19", "fin": None}],
    }


def test_sans_entree_de_table_le_membre_reste_publie_sans_fiche(document):
    """Véronique Besse n'a pas de fiche : `membre_id` est `null`, jamais un
    slug fabriqué, et la personne reste dans la liste avec ses dates."""
    besse = next(m for m in _bloc(document, "17")["membres"] if m["acteur_ref"] == "PA309643")
    assert besse["membre_id"] is None
    assert besse["nom"] == "Véronique Besse"
    assert besse["periodes"][0]["debut"] == "2024-07-19"


def test_un_passage_court_est_publie_tel_que_la_source_le_donne(document):
    """Pas de seuil de durée : un passage d'un jour hors transit d'ouverture
    est un fait de la source."""
    courts = [
        (m["nom"], p)
        for m in _bloc(document, "17")["membres"]
        for p in m["periodes"]
        if p["fin"] is not None and p["debut"] == p["fin"]
    ]
    assert courts, "la XVIIe porte des passages d'un jour hors transit d'ouverture"


def test_ce_n_est_pas_une_fiche_de_groupe(document):
    assert document["type_document"] == "non_inscrits"
    for cle in ("cohesion_votes", "effectif", "tags_thematiques_agreges", "amendements_agreges"):
        assert cle not in document
        assert all(cle not in bloc for bloc in document["legislatures"])


def test_la_liste_n_est_pas_rangee_dans_la_couche_que_le_site_lit():
    """Arbitré le 12/10/2026 : ces données complètent des articles, elles
    n'entrent dans aucune page. `pivot_data/` est la seule couche que le site
    lit ; la liste vit dans `raw_data/`."""
    assert non_inscrits_amo30.DEFAULT_SORTIE == Path("raw_data/non_inscrits.json")


def test_le_document_construit_est_conforme(document):
    assert non_inscrits_amo30.valider(document) == []


def test_le_validateur_refuse_un_transit_publie_et_un_doublon(document):
    faux = json.loads(json.dumps(document))
    bloc = _bloc(faux, "17")
    bloc["membres"][0]["periodes"] = [{"debut": "2024-07-08", "fin": "2024-07-18"}]
    bloc["membres"].append(dict(bloc["membres"][1]))
    erreurs = non_inscrits_amo30.valider(faux)
    assert any("transit" in e for e in erreurs)
    assert any("deux fois" in e for e in erreurs)


def test_rien_n_est_ecrit_sans_table_de_correspondance(tmp_path):
    sortie = tmp_path / "non_inscrits.json"
    with pytest.raises(non_inscrits_amo30.NonInscritsIndisponibles):
        non_inscrits_amo30.main(
            ["--zip", str(ARCHIVE), "--correspondance", str(tmp_path / "absente.json"),
             "--out", str(sortie)]
        )
    assert not sortie.exists()


def test_rien_n_est_ecrit_quand_aucun_organe_non_inscrit_n_est_lu(index):
    sans_ni = dict(index)
    sans_ni["organes"] = {
        ref: organe for ref, organe in index["organes"].items()
        if organe.get("sigle") != an_roster.SIGLE_NON_INSCRIT
    }
    with pytest.raises(non_inscrits_amo30.NonInscritsIndisponibles):
        non_inscrits_amo30.construire(sans_ni, {})


def test_le_script_ecrit_le_fichier_et_le_relit(tmp_path, monkeypatch):
    # `charger_index_gp` range son index à côté du cache : on l'isole du poste.
    monkeypatch.chdir(tmp_path)
    an_roster.vider_memo()
    sortie = tmp_path / "non_inscrits.json"
    assert non_inscrits_amo30.main(
        ["--zip", str(ARCHIVE), "--correspondance", str(TABLE), "--out", str(sortie)]
    ) == 0
    ecrit = json.loads(sortie.read_text(encoding="utf-8"))
    assert [b["legislature"] for b in ecrit["legislatures"]] == ["14", "15", "16", "17"]
    assert non_inscrits_amo30.valider(ecrit) == []
