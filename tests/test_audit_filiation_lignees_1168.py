#!/usr/bin/env python3
"""
Tests du lot #1168 — l'audit de filiation des lignées.

Deux étages, et pourquoi chacun :

- **la règle, sur des groupes écrits à la main.** Le seuil se joue à une
  personne près (9 sur 18 passe, 8 sur 18 non), la base est le plus petit des
  deux, les non-inscrits sont exclus, un groupe sans membre n'est pas mesuré :
  ce sont des propriétés arithmétiques, et une archive réelle ne porte pas les
  cas limites ;
- **la table committée, sur l'archive réelle réduite**
  (`tests/fixtures/amo30_gp_leg16_17.zip`, extraite d'AMO30, voir
  `test_an_roster.py`). Elle porte les mandats des XVIe et XVIIe et **aucun**
  de la XVe : les liens XVIe → XVIIe s'y mesurent, les liens qui partent de la
  XVe y sont non mesurables — la forme exacte que l'audit doit savoir dire.

Aucun décompte de la table n'est figé ici (#777) : ce qui est vérifié est une
règle — tout lien mesurable de la table est retrouvé, aucun couple non déclaré
n'atteint le seuil —, pas l'état du jour.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import audit_filiation_lignees as audit  # noqa: E402
from groupes_config import charger_correspondance_sigles  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"


# ---------------------------------------------------------------------------
# La règle
# ---------------------------------------------------------------------------

def _index(organes: dict[str, tuple[str, str, int, int]]) -> dict:
    """`{ref: (sigle, législature, premier acteur, dernier acteur exclu)}` → index GP."""
    return {
        "organes": {
            ref: {"sigle": sigle, "libelle": sigle, "legislature": leg,
                  "debut": f"20{leg}-01-01", "fin": None}
            for ref, (sigle, leg, _, _) in organes.items()
        },
        "mandats": {
            ref: [[f"PA{n}", f"20{leg}-01-01", None] for n in range(debut, fin)]
            for ref, (_, leg, debut, fin) in organes.items()
        },
        "acteurs": {},
    }


def _entree(sigle: str, leg: str, sigles_an: list[str], succede_a=None) -> dict:
    entree = {
        "groupe_sigle": sigle,
        "groupe_id": f"AN:{sigle}:{leg}",
        "legislature": leg,
        "sigles_an": sigles_an,
    }
    if succede_a:
        entree["succede_a"] = succede_a
    return entree


@pytest.mark.parametrize("communs, base, attendu", [
    (9, 18, True),    # la moitié exacte passe : « à partir de 50 % »
    (8, 18, False),
    (10, 19, True),
    (9, 19, False),   # 47 % : un arrondi ne le sauve pas
    (0, 12, False),
    (0, 0, None),     # aucun membre connu : la question ne se pose pas
])
def test_le_seuil_se_joue_en_entiers(communs, base, attendu):
    assert audit.atteint_le_seuil(communs, base) is attendu


def test_la_base_est_le_plus_petit_des_deux():
    """Un groupe qui s'effondre : 40 de ses 100 membres font tout le groupe d'arrivée."""
    index = _index({"PO1": ("A", "15", 0, 100), "PO2": ("B", "16", 0, 40)})
    entrees = [_entree("A", "15", ["A"]), _entree("B", "16", ["B"], ["AN:A:15"])]
    lien, = audit.auditer_filiation(index, entrees)["liens_declares"]
    assert (lien["communs"], lien["base"], lien["base_prise_sur"]) == (40, 40, "arrivee")
    assert lien["atteint_le_seuil"] is True


def test_un_lien_declare_que_la_composition_ne_soutient_pas_est_un_ecart():
    index = _index({"PO1": ("A", "15", 0, 20), "PO2": ("A", "16", 15, 35)})
    entrees = [_entree("A", "15", ["A"]), _entree("A", "16", ["A"], ["AN:A:15"])]
    rapport = audit.auditer_filiation(index, entrees)
    lien, = rapport["liens_non_retrouves"]
    assert (lien["communs"], lien["base"]) == (5, 20)
    assert lien["sigle_publie_identique"] is True
    assert rapport["ecarts"] == 1


def test_le_sigle_identique_passe_devant_sans_exempter():
    """Deux liens ratés : celui que personne ne rouvrirait est listé le premier."""
    index = _index({
        "PO1": ("A", "15", 0, 20), "PO2": ("B", "16", 15, 35),
        "PO3": ("C", "15", 100, 120), "PO4": ("C", "16", 119, 139),
    })
    entrees = [
        _entree("A", "15", ["A"]), _entree("B", "16", ["B"], ["AN:A:15"]),
        _entree("C", "15", ["C"]), _entree("C", "16", ["C"], ["AN:C:15"]),
    ]
    rates = audit.auditer_filiation(index, entrees)["liens_non_retrouves"]
    assert [lien["arrivee"] for lien in rates] == ["AN:C:16", "AN:B:16"]


def test_un_couple_au_dessus_du_seuil_et_non_declare_est_un_ecart():
    index = _index({"PO1": ("A", "15", 0, 20), "PO2": ("B", "16", 0, 30)})
    entrees = [_entree("A", "15", ["A"]), _entree("B", "16", ["B"])]
    rapport = audit.auditer_filiation(index, entrees)
    candidat, = rapport["candidats_non_declares"]
    assert (candidat["depart"], candidat["arrivee"]) == ("AN:A:15", "AN:B:16")
    assert rapport["ecarts"] == 1


def test_tous_les_couples_qui_passent_sont_retenus_pas_seulement_le_meilleur():
    """Une fusion : deux groupes de départ se retrouvent dans le même groupe d'arrivée."""
    index = _index({
        "PO1": ("A", "15", 0, 20), "PO2": ("B", "15", 20, 30), "PO3": ("C", "16", 0, 30),
    })
    entrees = [
        _entree("A", "15", ["A"]), _entree("B", "15", ["B"]), _entree("C", "16", ["C"]),
    ]
    candidats = audit.auditer_filiation(index, entrees)["candidats_non_declares"]
    assert {c["depart"] for c in candidats} == {"AN:A:15", "AN:B:15"}


def test_les_non_inscrits_ne_sont_ni_compares_ni_listes():
    """`NI` recouvre tout le monde : le garder ferait passer le seuil à chaque groupe."""
    index = _index({
        "PO1": ("A", "15", 0, 20), "PO2": ("A", "16", 0, 20),
        "PO8": (an_roster.SIGLE_NON_INSCRIT, "15", 0, 500),
        "PO9": (an_roster.SIGLE_NON_INSCRIT, "16", 0, 500),
    })
    entrees = [_entree("A", "15", ["A"]), _entree("A", "16", ["A"], ["AN:A:15"])]
    rapport = audit.auditer_filiation(index, entrees)
    assert rapport["candidats_non_declares"] == []
    assert rapport["organes_sans_entree"] == []
    assert rapport["ecarts"] == 0


def test_un_groupe_renomme_se_compare_par_l_union_de_ses_organes():
    """`MODEM` puis `DEM` : un seul groupe, deux organes — pris séparément, chacun raterait."""
    index = _index({
        "PO1": ("MODEM", "15", 0, 12), "PO2": ("DEM", "15", 8, 20),
        "PO3": ("DEM", "16", 0, 20),
    })
    entrees = [
        _entree("DEM", "15", ["MODEM", "DEM"]),
        _entree("DEM", "16", ["DEM"], ["AN:DEM:15"]),
    ]
    rapport = audit.auditer_filiation(index, entrees)
    lien, = rapport["liens_declares"]
    assert (lien["communs"], lien["base"]) == (20, 20)
    assert rapport["organes_sans_entree"] == []


def test_un_organe_que_la_table_ignore_est_nomme_et_compare_seul():
    index = _index({
        "PO1": ("A", "15", 0, 20), "PO2": ("A", "16", 0, 20),
        "PO3": ("X", "16", 100, 110),      # ouvert par l'Assemblée, absent de la table
        "PO4": ("Y", "14", 0, 20),         # législature que la table ne couvre pas
    })
    entrees = [_entree("A", "15", ["A"]), _entree("A", "16", ["A"], ["AN:A:15"])]
    rapport = audit.auditer_filiation(index, entrees)
    organe, = rapport["organes_sans_entree"]
    assert (organe["organe_an"], organe["sigle_an"], organe["effectif"]) == ("PO3", "X", 10)
    assert rapport["ecarts"] == 0, "nommé, pas compté : l'absence peut être voulue"


def test_un_lien_dans_une_meme_legislature_est_mesure_et_marque():
    index = _index({"PO1": ("NG", "15", 0, 30), "PO2": ("SOC", "15", 3, 36)})
    entrees = [_entree("NG", "15", ["NG"]), _entree("SOC", "15", ["SOC"], ["AN:NG:15"])]
    lien, = audit.auditer_filiation(index, entrees)["liens_declares"]
    assert lien["meme_legislature"] is True
    assert lien["atteint_le_seuil"] is True


def test_un_groupe_sans_membre_connu_n_est_ni_retrouve_ni_manque():
    index = _index({"PO1": ("A", "15", 0, 0), "PO2": ("A", "16", 0, 20)})
    entrees = [_entree("A", "15", ["A"]), _entree("A", "16", ["A"], ["AN:A:15"])]
    rapport = audit.auditer_filiation(index, entrees)
    assert len(rapport["non_mesurables"]) == 1
    assert rapport["liens_non_retrouves"] == []
    assert rapport["ecarts"] == 0


# ---------------------------------------------------------------------------
# La table committée, sur l'archive réelle réduite
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rapport_reel() -> dict:
    index = an_roster.construire_index_gp(ARCHIVE)
    return audit.auditer_filiation(index, charger_correspondance_sigles(CONFIG))


def test_chaque_lien_de_la_table_est_dans_le_rapport(rapport_reel):
    declares = {
        (cible, entree["groupe_id"])
        for entree in charger_correspondance_sigles(CONFIG)
        for cible in entree.get("succede_a") or []
    }
    assert declares
    assert {(l["depart"], l["arrivee"]) for l in rapport_reel["liens_declares"]} == declares


def test_la_table_committee_et_la_composition_disent_la_meme_chose(rapport_reel):
    """Le jour où ce test tombe, c'est la table qu'on relit — pas le seuil."""
    mesures = [l for l in rapport_reel["liens_declares"] if l["atteint_le_seuil"] is not None]
    assert mesures, "l'archive réduite doit porter au moins un lien mesurable"
    assert rapport_reel["liens_non_retrouves"] == []
    assert rapport_reel["candidats_non_declares"] == []


def test_les_liens_partant_de_la_xve_sont_non_mesurables_sur_l_archive_reduite(rapport_reel):
    """L'archive réduite ne porte aucun mandat de la XVe : dit, jamais lu comme 0 %."""
    non_mesurables = rapport_reel["non_mesurables"]
    assert non_mesurables
    assert all(l["depart"].endswith(":15") for l in non_mesurables)


def test_aucun_taux_sans_son_decompte(rapport_reel):
    """§2 règle 7 : chaque mesure porte son numérateur et son dénominateur."""
    for cle in ("liens_declares", "candidats_non_declares", "ecartes_les_plus_proches"):
        for mesure in rapport_reel[cle]:
            assert isinstance(mesure["communs"], int) and isinstance(mesure["base"], int)
            assert mesure["base"] == min(mesure["effectif_depart"], mesure["effectif_arrivee"])


# ---------------------------------------------------------------------------
# La ligne de commande
# ---------------------------------------------------------------------------

def test_la_commande_rend_0_quand_rien_ne_diverge(capsys):
    assert audit.main(["--archive", str(ARCHIVE), "--config", str(CONFIG)]) == 0
    assert "Aucun écart" in capsys.readouterr().out


def test_la_commande_rend_un_json_relisible(capsys):
    assert audit.main(["--archive", str(ARCHIVE), "--config", str(CONFIG), "--json"]) == 0
    rapport = json.loads(capsys.readouterr().out)
    assert rapport["seuil"] == "1/2"


def test_une_archive_nommee_n_ecrit_pas_dans_le_cache(tmp_path, monkeypatch):
    """Le cache d'index est partagé entre les sessions : une archive d'essai n'y écrit rien."""
    monkeypatch.chdir(tmp_path)
    assert audit.main(["--archive", str(ARCHIVE), "--config", str(CONFIG)]) == 0
    assert not (tmp_path / ".cache").exists()


def test_un_ecart_rend_1(tmp_path, capsys):
    """Un lien retiré de la table : la composition le propose, et la commande le dit."""
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    retire = None
    for entree in document["correspondance_sigles_an"]["groupes"]:
        if entree["legislature"] == "17" and entree.get("succede_a"):
            retire = (entree.pop("succede_a")[0], entree["groupe_id"])
            break
    assert retire
    config = tmp_path / "groupes_reels.json"
    config.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    assert audit.main(["--archive", str(ARCHIVE), "--config", str(config), "--json"]) == 1
    candidats = json.loads(capsys.readouterr().out)["candidats_non_declares"]
    assert [(c["depart"], c["arrivee"]) for c in candidats] == [retire]


def test_une_archive_illisible_rend_2(tmp_path, capsys):
    faux = tmp_path / "pas_une_archive.zip"
    faux.write_text("rien", encoding="utf-8")
    assert audit.main(["--archive", str(faux), "--config", str(CONFIG)]) == 2
    assert "illisible" in capsys.readouterr().err
