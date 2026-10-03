#!/usr/bin/env python3
"""
Tests du lot #1168 (lot 2c) — la table des groupes tenue par le run.

Trois choses, et pourquoi chacune :

- **le choix de la table à lire** (`chemin_table_groupes`) : celle du run quand
  elle a été composée de la table écrite telle qu'elle est aujourd'hui, sinon la
  table écrite. Sans l'empreinte, une correction faite à la main entre deux runs
  serait ignorée de tous les outils, sans un mot ;
- **la composition** (`composer_table`) : la table écrite a toujours raison sur
  ce qu'elle porte, ce qu'un run a ajouté est repris tel quel — c'est ce qui
  fige un lien et une adresse —, et une contradiction avec ce qui est publié
  arrête tout au lieu d'être tranchée ;
- **le workflow** : la table est composée avant le roster, voyage avec lui,
  entre dans le commit, et plus aucune étape ne nomme en dur la table écrite.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import groupes_amo30  # noqa: E402
import groupes_config  # noqa: E402
from test_mise_a_jour_table_groupes_1168 import XVII, _depart, _index, _table  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
JOUR = "2027-07-01"

AVEC_NEUF = {**XVII, "PO3": ("NEUF", "17", "2025-01-10", None, 200, 220)}


# ---------------------------------------------------------------------------
# Quelle table lire
# ---------------------------------------------------------------------------

def _poser(racine: Path, ecrite: dict, du_run: dict | None) -> None:
    (racine / "config").mkdir()
    (racine / "config" / "groupes_reels.json").write_text(json.dumps(ecrite), encoding="utf-8")
    if du_run is not None:
        (racine / "raw_data").mkdir()
        (racine / "raw_data" / "groupes_du_run.json").write_text(
            json.dumps(du_run), encoding="utf-8"
        )


def _empreinte(racine: Path) -> str:
    return groupes_config.empreinte_table(racine / "config" / "groupes_reels.json")


def test_sans_table_du_run_on_lit_la_table_ecrite(tmp_path):
    _poser(tmp_path, {"groupes": []}, None)
    assert groupes_config.chemin_table_groupes(tmp_path) == tmp_path / "config" / "groupes_reels.json"


def test_la_table_du_run_est_lue_quand_elle_vient_de_la_table_ecrite_d_aujourd_hui(tmp_path):
    _poser(tmp_path, {"groupes": []}, {})
    du_run = tmp_path / "raw_data" / "groupes_du_run.json"
    du_run.write_text(json.dumps({"_meta": {
        groupes_config.CLE_EMPREINTE_TABLE_ECRITE: {"sha256": _empreinte(tmp_path)},
    }}), encoding="utf-8")
    assert groupes_config.chemin_table_groupes(tmp_path) == du_run


def test_une_table_ecrite_corrigee_depuis_reprend_la_main(tmp_path):
    """Une PR a touché la table écrite après le dernier run : c'est elle qu'on lit."""
    _poser(tmp_path, {"groupes": []}, {})
    du_run = tmp_path / "raw_data" / "groupes_du_run.json"
    du_run.write_text(json.dumps({"_meta": {
        groupes_config.CLE_EMPREINTE_TABLE_ECRITE: {"sha256": _empreinte(tmp_path)},
    }}), encoding="utf-8")
    (tmp_path / "config" / "groupes_reels.json").write_text(
        json.dumps({"groupes": ["corrigée"]}), encoding="utf-8"
    )
    assert groupes_config.chemin_table_groupes(tmp_path) == tmp_path / "config" / "groupes_reels.json"


@pytest.mark.parametrize("contenu", ["pas du json", "[]", "{}", '{"_meta": {}}'])
def test_une_table_du_run_illisible_ou_sans_empreinte_n_est_pas_lue(tmp_path, contenu):
    _poser(tmp_path, {"groupes": []}, {})
    (tmp_path / "raw_data" / "groupes_du_run.json").write_text(contenu, encoding="utf-8")
    assert groupes_config.chemin_table_groupes(tmp_path) == tmp_path / "config" / "groupes_reels.json"


def _poser_une_table_du_run_a_jour(racine: Path) -> Path:
    _poser(racine, {"groupes": []}, {})
    du_run = racine / "raw_data" / "groupes_du_run.json"
    du_run.write_text(json.dumps({"_meta": {
        groupes_config.CLE_EMPREINTE_TABLE_ECRITE: {"sha256": _empreinte(racine)},
    }}), encoding="utf-8")
    return du_run


def test_la_suite_de_tests_ne_lit_jamais_la_table_du_run(tmp_path, monkeypatch):
    """`conftest.py` pose la variable : même à jour et sur le disque, elle n'est pas lue."""
    _poser_une_table_du_run_a_jour(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert os.environ.get(groupes_config.VARIABLE_TABLE_ECRITE_SEULE) == "1"
    assert groupes_config.chemin_table_groupes() == groupes_config.CHEMIN_TABLE_ECRITE


def test_hors_de_la_suite_la_resolution_par_defaut_lit_la_table_du_run(tmp_path, monkeypatch):
    """Ce que fait une étape du run : pas de variable, le répertoire courant, la table à jour."""
    _poser_une_table_du_run_a_jour(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(groupes_config.VARIABLE_TABLE_ECRITE_SEULE)
    assert groupes_config.chemin_table_groupes() == groupes_config.CHEMIN_TABLE_DU_RUN


def test_les_deux_tables_ne_portent_pas_le_meme_nom():
    """#1057 : deux fichiers de même nom de part et d'autre se liraient comme deux copies."""
    assert groupes_config.CHEMIN_TABLE_ECRITE.parts[0] == "config"
    assert groupes_config.CHEMIN_TABLE_DU_RUN.parts[0] == "raw_data"
    assert groupes_config.CHEMIN_TABLE_ECRITE.name != groupes_config.CHEMIN_TABLE_DU_RUN.name


# ---------------------------------------------------------------------------
# La composition
# ---------------------------------------------------------------------------

def test_sans_table_precedente_la_composition_est_la_mise_a_jour(tmp_path):
    index = _index(AVEC_NEUF)
    ecrite = _depart(_index(XVII))
    composee, journal = groupes_amo30.composer_table(ecrite, None, index, jour=JOUR)
    attendue, _ = groupes_amo30.mettre_a_jour_table(ecrite, index, jour=JOUR)
    assert composee == attendue
    assert journal["conflits"] == [] and journal["groupes_repris"] == []


def test_un_groupe_ajoute_par_un_run_est_repris_tel_quel_au_run_suivant():
    """Le lien et l'adresse sont figés : le second run ne les recalcule pas."""
    ecrite = _depart(_index(XVII))
    premier, _ = groupes_amo30.composer_table(ecrite, None, _index(AVEC_NEUF), jour=JOUR)
    # Entre les deux runs, la composition du groupe a tellement changé que la
    # règle le relierait désormais à REN-17. Il est déjà dans la table : rien ne bouge.
    bouge = {**XVII, "PO3": ("NEUF", "17", "2025-01-10", None, 0, 90)}
    second, journal = groupes_amo30.composer_table(ecrite, premier, _index(bouge), jour="2027-07-02")
    assert journal["groupes_repris"] == ["AN:NEUF:17"] and journal["groupes_ajoutes"] == []
    neuf = lambda doc: next(g for g in doc["groupes"] if g["groupe_id"] == "AN:NEUF:17")  # noqa: E731
    assert neuf(second) == neuf(premier)
    entree = next(e for e in second["correspondance_sigles_an"]["groupes"] if e["groupe_id"] == "AN:NEUF:17")
    assert "succede_a" not in entree
    assert [l["lignee_id"] for l in second["lignees"]] == [l["lignee_id"] for l in premier["lignees"]]


def test_la_table_ecrite_a_raison_sur_ce_qu_elle_porte():
    """Un humain adopte le groupe sous un autre sigle, dans la même lignée : sa version vaut."""
    index = _index(AVEC_NEUF)
    premier, _ = groupes_amo30.composer_table(_depart(_index(XVII)), None, index, jour=JOUR)
    adoptee = _table(index, [
        ("EPR", "17", ["PO1"], "AN:LIGNEE:REN", None),
        ("LR", "17", ["PO2"], "AN:LIGNEE:LR", None),
        ("NOUV", "17", ["PO3"], "AN:LIGNEE:NEUF", None),
    ])
    second, journal = groupes_amo30.composer_table(adoptee, premier, index, jour=JOUR)
    assert journal["conflits"] == [] and journal["groupes_repris"] == []
    assert [g["groupe_id"] for g in second["groupes"]] == ["AN:EPR:17", "AN:LR:17", "AN:NOUV:17"]


def test_une_adresse_deja_publiee_ne_se_deplace_pas():
    """La table écrite range le groupe dans une AUTRE lignée : la composition s'arrête."""
    index = _index(AVEC_NEUF)
    premier, _ = groupes_amo30.composer_table(_depart(_index(XVII)), None, index, jour=JOUR)
    deplacee = _table(index, [
        ("EPR", "17", ["PO1"], "AN:LIGNEE:REN", None),
        ("LR", "17", ["PO2"], "AN:LIGNEE:LR", None),
        ("NOUV", "17", ["PO3"], "AN:LIGNEE:AILLEURS", None),
    ])
    composee, journal = groupes_amo30.composer_table(deplacee, premier, index, jour=JOUR)
    assert composee is None
    conflit, = journal["conflits"]
    assert conflit["groupe_id"] == "AN:NEUF:17" and "AN:LIGNEE:NEUF" in conflit["motif"]


def test_un_identifiant_repris_pour_un_autre_groupe_arrete_la_composition():
    index = _index({**AVEC_NEUF, "PO4": ("AUTRE", "17", "2025-02-01", None, 400, 420)})
    premier, _ = groupes_amo30.composer_table(_depart(_index(XVII)), None, _index(AVEC_NEUF), jour=JOUR)
    reprise = _table(index, [
        ("EPR", "17", ["PO1"], "AN:LIGNEE:REN", None),
        ("LR", "17", ["PO2"], "AN:LIGNEE:LR", None),
        ("NEUF", "17", ["PO4"], "AN:LIGNEE:X", None),   # même identifiant, autres organes
    ])
    composee, journal = groupes_amo30.composer_table(reprise, premier, index, jour=JOUR)
    assert composee is None
    assert "reprend cet identifiant" in journal["conflits"][0]["motif"]


LEGISLATIVES = {**XVII, "PO10": ("EPR", "18", "2027-07-01", None, 10, 80)}


def _succede_a(document: dict, groupe_id: str) -> list:
    return next(
        e for e in document["correspondance_sigles_an"]["groupes"] if e["groupe_id"] == groupe_id
    ).get("succede_a")


def test_un_predecesseur_renomme_par_la_table_ecrite_est_retrouve_par_ses_organes():
    """Le cas de `NG` rejoint par `SOC` : mêmes organes, autre identifiant — le lien suit."""
    index = _index(LEGISLATIVES)
    premier, _ = groupes_amo30.composer_table(_depart(_index(XVII)), None, index, jour=JOUR)
    assert _succede_a(premier, "AN:EPR:18") == ["AN:EPR:17"]
    renommee = _table(index, [
        ("ENS", "17", ["PO1"], "AN:LIGNEE:REN", None),     # EPR-17 devient ENS-17, même lignée
        ("LR", "17", ["PO2"], "AN:LIGNEE:LR", None),
    ])
    second, journal = groupes_amo30.composer_table(renommee, premier, index, jour=JOUR)
    assert journal["conflits"] == []
    assert _succede_a(second, "AN:EPR:18") == ["AN:ENS:17"]
    assert groupes_config._valider_successions(second["correspondance_sigles_an"]["groupes"], Path("x")) is None


def test_un_groupe_retire_de_la_table_ecrite_revient_tel_qu_il_etait_publie():
    """L'Assemblée le porte toujours : la table ne peut pas l'oublier, et il garde ses noms."""
    index = _index(LEGISLATIVES)
    premier, _ = groupes_amo30.composer_table(_depart(_index(XVII)), None, index, jour=JOUR)
    sans_epr = _table(index, [("LR", "17", ["PO2"], "AN:LIGNEE:LR", None)])
    second, journal = groupes_amo30.composer_table(sans_epr, premier, index, jour=JOUR)
    assert journal["conflits"] == []
    assert set(journal["groupes_repris"]) == {"AN:EPR:17", "AN:EPR:18"}
    assert _succede_a(second, "AN:EPR:18") == ["AN:EPR:17"]
    assert next(g for g in second["groupes"] if g["groupe_id"] == "AN:EPR:17")["groupe_nom"] == "Nom relu EPR"


def test_un_lien_repris_dont_le_predecesseur_a_vraiment_disparu_arrete_la_composition():
    """Une table précédente abîmée : le lien nomme un groupe que rien ne porte plus."""
    index = _index(LEGISLATIVES)
    premier, _ = groupes_amo30.composer_table(_depart(_index(XVII)), None, index, jour=JOUR)
    abimee = copy.deepcopy(premier)
    next(
        e for e in abimee["correspondance_sigles_an"]["groupes"] if e["groupe_id"] == "AN:EPR:18"
    )["succede_a"] = ["AN:FANTOME:17"]
    composee, journal = groupes_amo30.composer_table(_depart(_index(XVII)), abimee, index, jour=JOUR)
    assert composee is None
    assert any("AN:FANTOME:17" in c["motif"] for c in journal["conflits"])


def test_une_date_de_relecture_ne_bouge_que_si_le_contenu_bouge():
    """La table est refaite de la table écrite chaque jour : la date ne doit pas suivre."""
    ecrite = _depart(_index(XVII))
    index = _index({**XVII, "PO2": ("LR", "17", "2024-07-18", "2027-06-20", 100, 152)})
    premier, _ = groupes_amo30.composer_table(ecrite, None, index, jour="2027-07-01")
    second, _ = groupes_amo30.composer_table(ecrite, premier, index, jour="2027-07-02")
    assert second == premier
    lr = next(e for e in second["correspondance_sigles_an"]["groupes"] if e["groupe_id"] == "AN:LR:17")
    assert lr["effectif_amo30"] == 52 and lr["verifie_le"] == "2027-07-01"


def test_la_composition_consigne_l_empreinte_de_la_table_ecrite():
    composee, _ = groupes_amo30.composer_table(
        _depart(_index(XVII)), None, _index(XVII), jour=JOUR, empreinte="abc123",
    )
    assert composee["_meta"][groupes_config.CLE_EMPREINTE_TABLE_ECRITE]["sha256"] == "abc123"


def test_les_tables_recues_ne_sont_jamais_modifiees():
    ecrite = _depart(_index(XVII))
    premier, _ = groupes_amo30.composer_table(ecrite, None, _index(AVEC_NEUF), jour=JOUR)
    copies = copy.deepcopy(ecrite), copy.deepcopy(premier)
    groupes_amo30.composer_table(ecrite, premier, _index(AVEC_NEUF), jour=JOUR)
    assert (ecrite, premier) == copies


# ---------------------------------------------------------------------------
# La ligne de commande, comme le run l'appelle
# ---------------------------------------------------------------------------

def test_le_premier_run_ecrit_la_table_et_le_second_ne_la_reecrit_pas(tmp_path, capsys):
    sortie = tmp_path / "raw_data" / "groupes_du_run.json"
    arguments = [
        "--archive", str(ARCHIVE), "--config", str(CONFIG), "--mettre-a-jour",
        "--precedent", str(sortie), "--out", str(sortie),
    ]
    assert groupes_amo30.main(arguments) == 0
    assert "Table écrite" in capsys.readouterr().err
    premier = sortie.read_text(encoding="utf-8")
    assert json.loads(premier)["_meta"][groupes_config.CLE_EMPREINTE_TABLE_ECRITE]["sha256"] == (
        groupes_config.empreinte_table(CONFIG)
    )
    assert groupes_amo30.main(arguments) == 0
    assert "déjà à jour" in capsys.readouterr().err
    assert sortie.read_text(encoding="utf-8") == premier


def test_la_table_composee_passe_la_validation_du_depot(tmp_path):
    sortie = tmp_path / "groupes_du_run.json"
    groupes_amo30.main([
        "--archive", str(ARCHIVE), "--config", str(CONFIG), "--mettre-a-jour", "--out", str(sortie),
    ])
    assert groupes_config.charger_correspondance_sigles(sortie)
    assert groupes_config.charger_lignees(sortie)


def test_precedent_sans_mettre_a_jour_est_refuse():
    with pytest.raises(SystemExit):
        groupes_amo30.main(["--precedent", "quelque/part.json"])


# ---------------------------------------------------------------------------
# Le workflow
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_la_table_est_composee_avant_le_roster_qui_la_lit(workflow):
    composition = workflow.index("src/groupes_amo30.py --mettre-a-jour")
    roster = workflow.index("src/generate_roster_candidats.py \\\n            --rosters-bruts-out")
    assert composition < roster
    assert "--precedent raw_data/groupes_du_run.json" in workflow
    assert "--out raw_data/groupes_du_run.json" in workflow


def test_la_table_voyage_dans_l_artifact_du_roster(workflow):
    """Les shards et la fusion téléchargent `roster-candidats` dans `raw_data` : elle y revient à sa place."""
    bloc = re.search(r"name: roster-candidats\n(?:\s*#.*\n)*\s*path: \|\n((?:\s+raw_data/\S+\n)+)", workflow)
    assert bloc, "l'artifact du roster doit rester lisible par cette garde"
    assert "raw_data/groupes_du_run.json" in bloc.group(1)
    assert "raw_data/roster_candidats.json" in bloc.group(1)


def test_le_commit_garde_la_table_du_run_sans_pouvoir_echouer_sur_son_absence(workflow):
    """`git add` d'un chemin absent est fatal : l'ajout est conditionnel, et à part."""
    assert "if [ -f raw_data/groupes_du_run.json ]; then git add raw_data/groupes_du_run.json; fi" in workflow
    for ligne in workflow.splitlines():
        if "git add " in ligne and "groupes_du_run" in ligne:
            assert ligne.strip().startswith("if [ -f "), ligne


def test_plus_aucune_etape_ne_nomme_en_dur_la_table_ecrite(workflow):
    """Une étape qui passerait `--config config/groupes_reels.json` ne verrait jamais un groupe ajouté par le run."""
    assert not re.search(r"--(?:groupes-)?config\s+config/groupes_reels\.json", workflow)
