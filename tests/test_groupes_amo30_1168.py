#!/usr/bin/env python3
"""
Tests du lot #1168 (lot 1) — les groupes et leurs lignées, dérivés d'AMO30.

Deux étages, comme pour l'audit de filiation :

- **la règle, sur des organes écrits à la main** : ce qui fait un renommage
  (contigu, au-dessus de la moitié, seul de son espèce), ce qui n'en fait pas un
  (une scission, un trou d'un jour de trop, deux successeurs), et ce que les
  filiations relient en lignées ;
- **la table committée, sur l'archive réelle réduite**
  (`tests/fixtures/amo30_gp_leg16_17.zip`) : sur les XVIe et XVIIe, la dérivation
  doit **reproduire** `config/groupes_reels.json` — mêmes groupes, mêmes liens,
  mêmes lignées, et champ par champ ce que la table écrit à la main. La XVe n'y
  est pas mesurable : l'archive réduite porte ses organes sans leurs mandats.

Aucun décompte n'est figé (#777) : c'est l'égalité qui est tenue, pas son
cardinal. Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import groupes_amo30  # noqa: E402
from groupes_config import charger_correspondance_sigles  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"


def _index(organes: dict[str, tuple]) -> dict:
    """`{ref: (sigle, législature, début, fin, premier acteur, dernier exclu)}` → index GP."""
    return {
        "organes": {
            ref: {"sigle": sigle, "libelle": f"Groupe {sigle}", "legislature": leg,
                  "debut": debut, "fin": fin, "position_politique": None}
            for ref, (sigle, leg, debut, fin, _, _) in organes.items()
        },
        "mandats": {
            ref: [[f"PA{n}", debut, fin] for n in range(premier, dernier)]
            for ref, (_, _, debut, fin, premier, dernier) in organes.items()
        },
        "acteurs": {},
    }


def _sigles(derivation: dict) -> list[list[str]]:
    return [groupe["sigles_an"] for groupe in derivation["groupes"]]


# ---------------------------------------------------------------------------
# Le renommage
# ---------------------------------------------------------------------------

def test_un_organe_rouvert_le_lendemain_avec_les_memes_membres_est_le_meme_groupe():
    index = _index({
        "PO1": ("SOC", "16", "2022-06-28", "2023-10-18", 0, 31),
        "PO2": ("SOC-A", "16", "2023-10-19", None, 0, 31),
    })
    derivation = groupes_amo30.deriver_groupes(index)
    groupe, = derivation["groupes"]
    assert groupe["organes_an"] == ["PO1", "PO2"]
    assert [h["nom"] for h in groupe["historique_organes_an"]] == ["Groupe SOC", "Groupe SOC-A"]
    assert groupe["effectif_amo30"] == 31


def test_une_chaine_de_renommages_fait_un_seul_groupe():
    index = _index({
        "PO1": ("AD", "17", "2024-07-18", "2024-09-11", 0, 16),
        "PO2": ("UDR", "17", "2024-09-12", "2025-09-04", 0, 16),
        "PO3": ("UDDPLR", "17", "2025-09-05", None, 1, 17),
    })
    assert _sigles(groupes_amo30.deriver_groupes(index)) == [["AD", "UDR", "UDDPLR"]]


def test_une_scission_n_est_pas_un_renommage():
    """`UDI-A-I → AGIR-E` : contigu, mais moins de la moitié du plus petit."""
    index = _index({
        "PO1": ("UDI-A-I", "15", "2019-09-28", "2020-05-25", 0, 28),
        "PO2": ("AGIR-E", "15", "2020-05-26", None, 18, 41),
    })
    derivation = groupes_amo30.deriver_groupes(index)
    assert _sigles(derivation) == [["UDI-A-I"], ["AGIR-E"]]
    couple, = derivation["renommages"]
    assert (couple["communs"], couple["base"], couple["renommage"]) == (10, 23, False)


def test_un_trou_de_deux_jours_n_est_pas_un_renommage():
    """Le lendemain, pas le surlendemain : au-delà d'un jour, c'est une absence."""
    index = _index({
        "PO1": ("A", "16", "2022-06-28", "2023-01-10", 0, 20),
        "PO2": ("B", "16", "2023-01-12", None, 0, 20),
    })
    derivation = groupes_amo30.deriver_groupes(index)
    assert _sigles(derivation) == [["A"], ["B"]]
    assert derivation["renommages"] == []


def test_deux_legislatures_ne_se_renomment_pas_l_une_dans_l_autre():
    index = _index({
        "PO1": ("A", "15", "2017-06-27", "2022-06-21", 0, 20),
        "PO2": ("A", "16", "2022-06-22", None, 0, 20),
    })
    assert _sigles(groupes_amo30.deriver_groupes(index)) == [["A"], ["A"]]


def test_deux_successeurs_au_dessus_du_seuil_ne_sont_pas_tranches():
    """Une scission en deux moitiés : aucune n'est « le même groupe », et c'est dit."""
    index = _index({
        "PO1": ("A", "16", "2022-06-28", "2023-01-10", 0, 30),
        "PO2": ("B", "16", "2023-01-11", None, 0, 20),
        "PO3": ("C", "16", "2023-01-11", None, 20, 30),
    })
    derivation = groupes_amo30.deriver_groupes(index)
    assert _sigles(derivation) == [["A"], ["B"], ["C"]]
    assert {c["sigle_arrivee"] for c in derivation["renommages_ambigus"]} == {"B", "C"}


def test_les_non_inscrits_et_les_legislatures_anciennes_ne_sont_pas_derives():
    index = _index({
        "PO1": ("A", "16", "2022-06-28", None, 0, 20),
        "PO8": (an_roster.SIGLE_NON_INSCRIT, "16", "2022-06-22", None, 0, 500),
        "PO9": ("VIEUX", str(groupes_amo30.PREMIERE_LEGISLATURE - 1), "2012-06-26", "2017-06-20", 0, 20),
    })
    assert _sigles(groupes_amo30.deriver_groupes(index)) == [["A"]]


def test_la_position_est_resumee_jamais_choisie():
    """Deux organes qui se contredisent : `divergente`, pas l'un des deux."""
    index = _index({
        "PO1": ("A", "15", "2017-06-27", "2019-01-10", 0, 20),
        "PO2": ("B", "15", "2019-01-11", "2022-06-21", 0, 20),
    })
    index["organes"]["PO1"]["position_politique"] = "Opposition"
    index["organes"]["PO2"]["position_politique"] = "Minoritaire"
    groupe, = groupes_amo30.deriver_groupes(index)["groupes"]
    assert groupe["position_politique_an"]["position"] == "divergente"
    assert [o["valeur_source"] for o in groupe["position_politique_an"]["organes"]] == [
        "Opposition", "Minoritaire",
    ]


# ---------------------------------------------------------------------------
# La filiation et les lignées
# ---------------------------------------------------------------------------

def test_une_lignee_est_ce_que_les_filiations_relient():
    index = _index({
        "PO1": ("A", "15", "2017-06-27", "2022-06-21", 0, 20),
        "PO2": ("A", "16", "2022-06-28", "2024-06-09", 0, 20),
        "PO3": ("B", "17", "2024-07-18", None, 5, 25),
        "PO4": ("SEUL", "16", "2022-06-28", "2024-06-09", 100, 120),
    })
    derivation = groupes_amo30.deriver(index)
    assert derivation["lignees"] == [["PO1", "PO2", "PO3"], ["PO4"]]
    assert [(l["depart"], l["arrivee"], l["communs"], l["base"]) for l in derivation["filiations"]] == [
        ("PO1", "PO2", 20, 20), ("PO2", "PO3", 15, 20),
    ]


def test_la_filiation_se_mesure_sur_le_groupe_renomme_entier():
    """`NG` puis `SOC` : pris séparément, `NG` raterait le lien vers la législature suivante."""
    index = _index({
        "PO1": ("NG", "15", "2017-06-27", "2018-09-11", 0, 30),
        "PO2": ("SOC", "15", "2018-09-12", "2022-06-21", 2, 36),
        "PO3": ("SOC", "16", "2022-06-28", None, 20, 50),
    })
    derivation = groupes_amo30.deriver(index)
    assert derivation["lignees"] == [["PO1", "PO3"]]
    lien, = derivation["filiations"]
    assert (lien["communs"], lien["base"]) == (16, 30)


def test_une_fusion_relie_deux_groupes_a_la_meme_lignee():
    index = _index({
        "PO1": ("A", "15", "2017-06-27", "2022-06-21", 0, 20),
        "PO2": ("B", "15", "2017-06-27", "2022-06-21", 20, 30),
        "PO3": ("C", "16", "2022-06-28", None, 0, 30),
    })
    assert groupes_amo30.deriver(index)["lignees"] == [["PO1", "PO2", "PO3"]]


def test_un_groupe_sans_membre_connu_n_entre_dans_aucun_lien():
    index = _index({
        "PO1": ("A", "15", "2017-06-27", "2022-06-21", 0, 0),
        "PO2": ("A", "16", "2022-06-28", None, 0, 20),
    })
    derivation = groupes_amo30.deriver(index)
    assert derivation["filiations"] == []
    assert derivation["lignees"] == [["PO1"], ["PO2"]]


# ---------------------------------------------------------------------------
# La table committée, sur l'archive réelle réduite
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def comparaison() -> dict:
    index = an_roster.construire_index_gp(ARCHIVE)
    derivation = groupes_amo30.deriver(index, ("16", "17"))
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    return groupes_amo30.comparer_a_la_table(
        derivation, index, document, charger_correspondance_sigles(CONFIG)
    )


@pytest.mark.parametrize("etage", ["lignees", "groupes", "filiations"])
def test_la_derivation_reproduit_la_table_sur_les_xvie_et_xviie(comparaison, etage):
    """Le jour où ce test tombe : l'Assemblée a bougé, ou la table a été écrite de travers."""
    bloc = comparaison[etage]
    assert bloc["table"] > 0
    assert bloc["identiques"] == bloc["table"], bloc


def test_les_champs_ecrits_a_la_main_sont_ceux_que_la_source_donne(comparaison):
    """Organes, noms successifs et leurs dates, position, effectif : rien à écrire à la main."""
    assert comparaison["champs_differents"] == []
    assert comparaison["renommages_ambigus"] == []


def test_les_entrees_de_la_xve_sont_laissees_de_cote_et_comptees(comparaison):
    xve = sum(1 for e in charger_correspondance_sigles(CONFIG) if e["legislature"] == "15")
    assert xve and comparaison["entrees_hors_legislatures"] == xve


# ---------------------------------------------------------------------------
# La ligne de commande
# ---------------------------------------------------------------------------

def test_la_commande_derive_sans_rien_ecrire(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert groupes_amo30.main(["--archive", str(ARCHIVE), "--config", str(CONFIG)]) == 0
    assert "lignée(s)" in capsys.readouterr().out
    assert not (tmp_path / ".cache").exists()


def test_la_commande_rend_un_json_sans_les_ensembles_de_membres(capsys):
    assert groupes_amo30.main(["--archive", str(ARCHIVE), "--json"]) == 0
    sortie = json.loads(capsys.readouterr().out)
    assert sortie["groupes"] and all("membres" not in g for g in sortie["groupes"])


def test_une_table_qui_s_ecarte_rend_1(tmp_path, capsys):
    """Un organe retiré d'une entrée de la table : la comparaison le nomme."""
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    retouchee = None
    for entree in document["correspondance_sigles_an"]["groupes"]:
        if entree["legislature"] in ("16", "17") and len(entree["sigles_an"]) > 1:
            entree["sigles_an"] = entree["sigles_an"][:1]
            entree["organes_an"] = entree["organes_an"][:1]
            entree["historique_organes_an"] = entree["historique_organes_an"][:1]
            entree["position_politique_an"]["organes"] = entree["position_politique_an"]["organes"][:1]
            retouchee = entree["groupe_id"]
            break
    assert retouchee
    config = tmp_path / "groupes_reels.json"
    config.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    # L'archive réduite ne mesure pas la XVe : la comparaison complète y trouverait
    # des écarts qui ne disent rien. On compare donc par la fonction, sur 16-17.
    index = an_roster.construire_index_gp(ARCHIVE)
    rapport = groupes_amo30.comparer_a_la_table(
        groupes_amo30.deriver(index, ("16", "17")), index,
        document, charger_correspondance_sigles(config),
    )
    assert rapport["differences"] > 0
    assert rapport["groupes"]["table_seulement"] and rapport["groupes"]["derives_seulement"]


def test_une_archive_illisible_rend_2(tmp_path, capsys):
    faux = tmp_path / "pas_une_archive.zip"
    faux.write_text("rien", encoding="utf-8")
    assert groupes_amo30.main(["--archive", str(faux)]) == 2
    assert "illisible" in capsys.readouterr().err
