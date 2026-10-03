#!/usr/bin/env python3
"""
Tests du lot #1168 (lot 2a) — la table des groupes mise à jour depuis AMO30.

Ce que `mettre_a_jour_table` promet, et que chaque test tient :

- **ce qui est nommé ne se réécrit jamais** — sigle publié, identifiants,
  `succede_a` : un lien se calcule une fois, à l'entrée du groupe ;
- **ce que la source dit se rafraîchit** — noms successifs, position, effectif ;
- **un organe que la table ignore y entre**, dans son groupe ou comme groupe neuf ;
- **ce qui ne se tranche pas reste dehors**, nommé (`AGENTS.md` §2 règle 5).

Le dernier bloc repart de la table committée amputée de sa XVIIe et vérifie, sur
l'archive réelle réduite, que la mise à jour la **reconstruit** : mêmes groupes,
mêmes liens, mêmes lignées. C'est la situation d'une législature neuve.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import groupes_amo30  # noqa: E402
from groupes_config import charger_correspondance_sigles, charger_lignees  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"
JOUR = "2027-07-01"


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


def _table(index: dict, groupes: list[tuple]) -> dict:
    """`[(sigle publié, législature, [organes], lignée, [succede_a])]` → document de table."""
    document = {"groupes": [], "correspondance_sigles_an": {"groupes": []}, "lignees": []}
    for sigle, leg, organes, lignee, succede_a in groupes:
        groupe_id = f"AN:{sigle}:{leg}"
        fichier = f"groupe-AN-{sigle}-{leg}.json"
        derive = groupes_amo30._groupe_des_organes(index, organes)
        entree = {
            "groupe_sigle": sigle, "groupe_id": groupe_id, "legislature": leg,
            "fichier": fichier,
            "sigles_an": [index["organes"][r]["sigle"] for r in organes],
            "organes_an": organes,
            "historique_organes_an": derive["historique_organes_an"],
            "position_politique_an": {**derive["position_politique_an"], "verifie_le": "2026-01-01"},
            "effectif_amo30": derive["effectif_amo30"], "effectif_publie": None,
            "verifie_le": "2026-01-01", "ecart_membres": [], "ecart_motif": "écrit à la main",
        }
        if succede_a:
            entree["succede_a"] = succede_a
        document["correspondance_sigles_an"]["groupes"].append(entree)
        document["groupes"].append({
            "roster_chambre": "deputes", "groupe_id": groupe_id, "lignee_id": lignee,
            "groupe_sigle": sigle, "groupe_nom": f"Nom relu {sigle}", "chambre": "AN",
            "legislature": leg, "fichier": fichier,
        })
        if lignee not in {l["lignee_id"] for l in document["lignees"]}:
            document["lignees"].append({
                "lignee_id": lignee, "lignee_nom": "Nom de lignée relu", "chambre": "AN",
                "fichier": f"lignee-{lignee.replace(':', '-')}.json", "verifie_le": "2026-01-01",
            })
    return document


XVII = {
    "PO1": ("REN", "17", "2024-07-18", "2027-06-20", 0, 100),
    "PO2": ("LR", "17", "2024-07-18", "2027-06-20", 100, 150),
}


def _depart(index: dict) -> dict:
    return _table(index, [
        ("EPR", "17", ["PO1"], "AN:LIGNEE:REN", None),
        ("LR", "17", ["PO2"], "AN:LIGNEE:LR", None),
    ])


# ---------------------------------------------------------------------------
# Rien de neuf : rien ne bouge
# ---------------------------------------------------------------------------

def test_sans_organe_nouveau_la_table_ne_change_pas():
    index = _index(XVII)
    document = _depart(index)
    nouveau, journal = groupes_amo30.mettre_a_jour_table(document, index, jour=JOUR)
    assert nouveau == document
    assert not groupes_amo30.table_modifiee(journal)


def test_le_document_recu_n_est_jamais_modifie():
    index = _index({**XVII, "PO3": ("NEUF", "17", "2025-01-10", None, 200, 220)})
    document = _depart(_index(XVII))
    avant = copy.deepcopy(document)
    groupes_amo30.mettre_a_jour_table(document, index, jour=JOUR)
    assert document == avant


# ---------------------------------------------------------------------------
# Un organe nouveau
# ---------------------------------------------------------------------------

def test_un_renommage_rejoint_son_groupe_sans_toucher_a_ses_noms():
    index = _index({
        **XVII,
        "PO1": ("REN", "17", "2024-07-18", "2025-03-01", 0, 100),
        "PO3": ("EPR", "17", "2025-03-02", None, 0, 98),
    })
    document = _depart(_index(XVII))
    nouveau, journal = groupes_amo30.mettre_a_jour_table(document, index, jour=JOUR)
    entree = nouveau["correspondance_sigles_an"]["groupes"][0]
    assert entree["organes_an"] == ["PO1", "PO3"]
    assert entree["sigles_an"] == ["REN", "EPR"]
    assert [h["sigle_an"] for h in entree["historique_organes_an"]] == ["REN", "EPR"]
    assert (entree["groupe_sigle"], entree["groupe_id"], entree["fichier"]) == (
        "EPR", "AN:EPR:17", "groupe-AN-EPR-17.json",
    )
    assert nouveau["groupes"] == document["groupes"], "les noms relus ne bougent pas"
    assert [r["organe_an"] for r in journal["organes_rattaches"]] == ["PO3"]
    assert journal["groupes_ajoutes"] == []


def test_un_groupe_neuf_sans_predecesseur_ouvre_sa_lignee():
    index = _index({**XVII, "PO3": ("NEUF", "17", "2025-01-10", None, 200, 220)})
    nouveau, journal = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    ajout, = journal["groupes_ajoutes"]
    assert (ajout["groupe_id"], ajout["lignee_id"], ajout["succede_a"]) == (
        "AN:NEUF:17", "AN:LIGNEE:NEUF", [],
    )
    entree = nouveau["correspondance_sigles_an"]["groupes"][-1]
    assert "succede_a" not in entree, "une clé absente dit « pas de prédécesseur »"
    assert entree["effectif_publie"] is None and entree["verifie_le"] == JOUR
    assert nouveau["lignees"][-1]["lignee_nom"] == "Groupe NEUF"


def test_une_legislature_neuve_relie_chaque_groupe_a_sa_lignee():
    """Les législatives : deux groupes se reconstituent, un troisième est nouveau."""
    index = _index({
        **XVII,
        "PO10": ("EPR", "18", "2027-07-01", None, 10, 80),      # 70 des 100 de REN-17
        "PO11": ("DR", "18", "2027-07-01", None, 100, 130),     # 30 des 50 de LR-17
        "PO12": ("AUTRE", "18", "2027-07-01", None, 500, 540),
    })
    nouveau, journal = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    ajouts = {a["groupe_id"]: a for a in journal["groupes_ajoutes"]}
    assert ajouts["AN:EPR:18"]["lignee_id"] == "AN:LIGNEE:REN"
    assert ajouts["AN:EPR:18"]["succede_a"] == [{"groupe_id": "AN:EPR:17", "communs": 70, "base": 70}]
    assert ajouts["AN:DR:18"]["lignee_id"] == "AN:LIGNEE:LR"
    assert ajouts["AN:AUTRE:18"]["lignee_id"] == "AN:LIGNEE:AUTRE"
    assert [l["lignee_id"] for l in journal["lignees_ajoutees"]] == ["AN:LIGNEE:AUTRE"]
    assert len(nouveau["lignees"]) == 3, "aucune lignée existante n'est dupliquée ni renommée"


def test_un_lien_ecrit_n_est_jamais_recalcule():
    """Un groupe déjà dans la table sans `succede_a` : la règle le relierait, on n'y touche pas."""
    index = _index({**XVII, "PO10": ("EPR", "18", "2027-07-01", None, 10, 80)})
    document = _table(index, [
        ("EPR", "17", ["PO1"], "AN:LIGNEE:REN", None),
        ("LR", "17", ["PO2"], "AN:LIGNEE:LR", None),
        ("EPR", "18", ["PO10"], "AN:LIGNEE:AUTRE-CHOSE", None),
    ])
    nouveau, journal = groupes_amo30.mettre_a_jour_table(document, index, jour=JOUR)
    assert nouveau == document
    assert journal["groupes_ajoutes"] == []


def test_l_identifiant_est_le_sigle_de_naissance():
    """Entré tard, après un renommage : même identifiant que s'il était entré le premier jour."""
    index = _index({
        **XVII,
        "PO3": ("AD", "17", "2024-07-18", "2024-09-11", 300, 316),
        "PO4": ("UDR", "17", "2024-09-12", None, 300, 316),
    })
    _, journal = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    ajout, = journal["groupes_ajoutes"]
    assert (ajout["groupe_id"], ajout["lignee_id"]) == ("AN:AD:17", "AN:LIGNEE:AD")


# ---------------------------------------------------------------------------
# Ce que la source dit se rafraîchit
# ---------------------------------------------------------------------------

def test_l_effectif_et_la_date_de_fin_suivent_la_source():
    depart = _depart(_index(XVII))
    index = _index({**XVII, "PO2": ("LR", "17", "2024-07-18", "2027-06-21", 100, 152)})
    index["organes"]["PO2"]["position_politique"] = "Opposition"
    nouveau, journal = groupes_amo30.mettre_a_jour_table(depart, index, jour=JOUR)
    entree = nouveau["correspondance_sigles_an"]["groupes"][1]
    assert entree["effectif_amo30"] == 52
    assert entree["historique_organes_an"][0]["fin"] == "2027-06-21"
    assert entree["position_politique_an"]["position"] == "opposition"
    assert entree["verifie_le"] == JOUR
    assert entree["ecart_motif"] == "écrit à la main", "les notes relues ne sont pas touchées"
    assert {c["champ"] for c in journal["champs_rafraichis"]} == set(groupes_amo30.CHAMPS_RAFRAICHIS)
    assert nouveau["correspondance_sigles_an"]["groupes"][0] == depart["correspondance_sigles_an"]["groupes"][0]


def test_une_archive_sans_mandats_ne_vide_pas_une_entree():
    """L'archive réduite porte des organes sans leurs mandats : ce n'est pas « effectif 0 »."""
    depart = _depart(_index(XVII))
    index = _index(XVII)
    index["mandats"]["PO2"] = []
    nouveau, journal = groupes_amo30.mettre_a_jour_table(depart, index, jour=JOUR)
    assert nouveau == depart and journal["champs_rafraichis"] == []


# ---------------------------------------------------------------------------
# Ce qui ne se tranche pas reste dehors
# ---------------------------------------------------------------------------

def test_un_groupe_sans_mandat_commence_attend():
    index = _index({**XVII, "PO3": ("NEUF", "17", "2027-06-30", None, 0, 0)})
    nouveau, journal = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    assert nouveau == _depart(_index(XVII))
    assert [a["sigles_an"] for a in journal["en_attente"]] == [["NEUF"]]


def test_une_fusion_de_deux_lignees_n_est_pas_tranchee():
    index = _index({**XVII, "PO10": ("UNION", "18", "2027-07-01", None, 40, 145)})
    nouveau, journal = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    assert len(nouveau["groupes"]) == 2, "le groupe n'entre pas : on ne choisit pas sa page"
    cas, = journal["non_tranches"]
    assert "plusieurs lignées" in cas["motif"]
    assert "AN:LIGNEE:LR" in cas["motif"] and "AN:LIGNEE:REN" in cas["motif"]


def test_un_identifiant_deja_pris_n_est_pas_reattribue():
    """Le sigle de l'Assemblée d'un groupe neuf est le sigle publié d'un autre."""
    index = _index({**XVII, "PO3": ("EPR", "17", "2025-01-10", None, 300, 320)})
    nouveau, journal = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    assert len(nouveau["groupes"]) == 2
    cas, = journal["non_tranches"]
    assert "AN:EPR:17 est déjà pris" in cas["motif"]


def test_deux_entrees_pour_un_groupe_renomme_sont_signalees_pas_fusionnees():
    """`NG` et `SOC` de la XVe : la règle en fait un groupe, la table deux."""
    organes = {
        "PO1": ("NG", "15", "2017-06-27", "2018-09-11", 0, 33),
        "PO2": ("SOC", "15", "2018-09-12", "2022-06-21", 3, 39),
    }
    index = _index(organes)
    document = _table(index, [
        ("NG", "15", ["PO1"], "AN:LIGNEE:SOC", None),
        ("SOC", "15", ["PO2"], "AN:LIGNEE:SOC", ["AN:NG:15"]),
    ])
    nouveau, journal = groupes_amo30.mettre_a_jour_table(document, index, jour=JOUR)
    assert nouveau == document
    cas, = journal["a_fusionner"]
    assert cas["groupes"] == ["AN:NG:15", "AN:SOC:15"]


def test_la_mise_a_jour_est_idempotente():
    index = _index({
        **XVII,
        "PO10": ("EPR", "18", "2027-07-01", None, 10, 80),
        "PO12": ("AUTRE", "18", "2027-07-01", None, 500, 540),
    })
    premier, _ = groupes_amo30.mettre_a_jour_table(_depart(_index(XVII)), index, jour=JOUR)
    second, journal = groupes_amo30.mettre_a_jour_table(premier, index, jour="2027-07-02")
    assert second == premier
    assert not groupes_amo30.table_modifiee(journal)


# ---------------------------------------------------------------------------
# La table committée, amputée de sa XVIIe, sur l'archive réelle réduite
# ---------------------------------------------------------------------------

def _structure(document: dict) -> tuple[set, set, set]:
    entrees = document["correspondance_sigles_an"]["groupes"]
    lignee_de = {g["groupe_id"]: g["lignee_id"] for g in document["groupes"]}
    organes = {e["groupe_id"]: frozenset(e["organes_an"]) for e in entrees}
    liens = {
        (organes[cible], organes[e["groupe_id"]])
        for e in entrees for cible in e.get("succede_a") or []
    }
    lignees: dict[str, set] = {}
    for e in entrees:
        lignees.setdefault(lignee_de[e["groupe_id"]], set()).update(e["organes_an"])
    return set(organes.values()), liens, {frozenset(v) for v in lignees.values()}


@pytest.fixture(scope="module")
def reconstruction(tmp_path_factory) -> tuple[dict, dict, dict]:
    original = json.loads(CONFIG.read_text(encoding="utf-8"))
    ampute = copy.deepcopy(original)
    garde = lambda e: e["legislature"] != "17"  # noqa: E731
    ampute["correspondance_sigles_an"]["groupes"] = [
        e for e in ampute["correspondance_sigles_an"]["groupes"] if garde(e)
    ]
    ampute["groupes"] = [g for g in ampute["groupes"] if garde(g)]
    restantes = {g["lignee_id"] for g in ampute["groupes"]}
    ampute["lignees"] = [l for l in ampute["lignees"] if l["lignee_id"] in restantes]
    index = an_roster.construire_index_gp(ARCHIVE)
    reconstruit, journal = groupes_amo30.mettre_a_jour_table(ampute, index, jour=JOUR)
    return original, reconstruit, journal


def test_une_legislature_retiree_de_la_table_est_reconstruite(reconstruction):
    """Mêmes groupes, mêmes liens, mêmes lignées — seuls les noms attribués diffèrent."""
    original, reconstruit, journal = reconstruction
    assert journal["groupes_ajoutes"], "la XVIIe devait être à reconstruire"
    assert _structure(reconstruit) == _structure(original)
    assert journal["non_tranches"] == [] and journal["en_attente"] == []


def test_la_table_reconstruite_passe_la_validation_du_depot(reconstruction, tmp_path):
    _, reconstruit, _ = reconstruction
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(reconstruit, ensure_ascii=False), encoding="utf-8")
    assert len(charger_correspondance_sigles(chemin)) == len(
        reconstruit["correspondance_sigles_an"]["groupes"]
    )
    assert charger_lignees(chemin)


def test_les_entrees_gardees_ne_sont_pas_renommees(reconstruction):
    original, reconstruit, _ = reconstruction
    noms = lambda doc: {  # noqa: E731
        g["groupe_id"]: (g["groupe_sigle"], g["groupe_nom"], g["lignee_id"], g["fichier"])
        for g in doc["groupes"] if g["legislature"] != "17"
    }
    assert noms(reconstruit) == noms(original)


# ---------------------------------------------------------------------------
# La ligne de commande
# ---------------------------------------------------------------------------

def test_sans_out_rien_n_est_ecrit(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code = groupes_amo30.main(["--archive", str(ARCHIVE), "--config", str(CONFIG), "--mettre-a-jour"])
    assert code == 0
    assert list(tmp_path.iterdir()) == []


def test_out_ecrit_une_table_que_le_depot_sait_relire(tmp_path, capsys):
    sortie = tmp_path / "raw_data" / "groupes_reels.json"
    code = groupes_amo30.main([
        "--archive", str(ARCHIVE), "--config", str(CONFIG), "--mettre-a-jour", "--out", str(sortie),
    ])
    assert code == 0
    assert charger_correspondance_sigles(sortie) and charger_lignees(sortie)


def test_out_sans_mettre_a_jour_est_refuse(capsys):
    with pytest.raises(SystemExit):
        groupes_amo30.main(["--out", "quelque/part.json"])
