#!/usr/bin/env python3
"""
Tests du lot #1168 (lot 4) — le résumé de run dit ce que la composition de la
table des groupes a fait.

Le résumé d'un run du dépôt public est lisible par tous. Il nomme les groupes
ajoutés, les lignées ouvertes, les renommages, les liens à relire — et **jamais
le décompte d'un lien** : la propriétaire a arbitré le 03/10/2026 que seule la
règle se publie. C'est ce que le premier test tient, sur un journal réel.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import groupes_amo30  # noqa: E402
from test_mise_a_jour_table_groupes_1168 import XVII, _depart, _index  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"
JOUR = "2027-07-01"

LEGISLATIVES = {
    **XVII,
    "PO10": ("EPR", "18", "2027-07-01", None, 10, 80),
    "PO12": ("AUTRE", "18", "2027-07-01", None, 500, 540),
    "PO13": ("TARDIF", "18", "2027-07-01", None, 0, 0),
}


@pytest.fixture
def journal_de_legislatives() -> dict:
    _, journal = groupes_amo30.composer_table(_depart(_index(XVII)), None, _index(LEGISLATIVES), jour=JOUR)
    return journal


def test_le_resume_nomme_les_groupes_sans_jamais_publier_un_decompte(journal_de_legislatives):
    resume = groupes_amo30.resume_de_run(journal_de_legislatives, ecrite=True)
    assert "`AN:EPR:18`" in resume and "prend la suite de `AN:EPR:17`" in resume
    assert "`AN:AUTRE:18`" in resume and "aucun prédécesseur" in resume
    assert "`AN:LIGNEE:AUTRE`" in resume
    assert "TARDIF" in resume, "un groupe en attente est nommé"
    assert not re.search(r"\d+ sur \d+", resume), "un décompte de lien ne se publie pas"
    assert " communs" not in resume


def test_un_lien_sous_le_seuil_est_nomme_sans_son_decompte():
    journal = groupes_amo30._journal_vide()
    journal["liens_non_soutenus"] = [
        {"groupe_id": "AN:EPR:17", "predecesseur": "AN:REN:16", "communs": 9, "base": 20},
    ]
    resume = groupes_amo30.resume_de_run(journal, ecrite=True)
    assert "`AN:REN:16` → `AN:EPR:17`" in resume
    assert "9" not in resume and "20" not in resume


def test_un_run_ordinaire_tient_en_une_ligne():
    journal = groupes_amo30._journal_vide()
    journal["champs_rafraichis"] = [{"groupe_id": "AN:LIOT:17", "champ": "effectif_amo30"}]
    resume = groupes_amo30.resume_de_run(journal, ecrite=True)
    assert resume.count("\n") == 3
    assert "Aucun groupe nouveau" in resume and "1 groupe(s)" in resume


def test_une_table_non_ecrite_le_dit_d_abord():
    journal = groupes_amo30._journal_vide()
    journal["conflits"] = [{"groupe_id": "AN:NEUF:17", "motif": "l'adresse d'une page ne se déplace pas (#836)"}]
    resume = groupes_amo30.resume_de_run(journal, ecrite=False)
    assert resume.splitlines()[2].startswith("**Table non écrite**")
    assert "`AN:NEUF:17`" in resume


def test_la_commande_ecrit_le_resume_quand_le_runner_le_demande(tmp_path, monkeypatch, capsys):
    resume = tmp_path / "resume.md"
    resume.write_text("avant\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(resume))
    assert groupes_amo30.main([
        "--archive", str(ARCHIVE), "--config", str(CONFIG), "--mettre-a-jour",
    ]) == 0
    texte = resume.read_text(encoding="utf-8")
    assert texte.startswith("avant\n"), "le résumé s'ajoute, il n'écrase pas les étapes précédentes"
    assert "### Table des groupes du run (#1168)" in texte


def test_hors_d_un_runner_rien_n_est_ecrit(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.chdir(tmp_path)
    assert groupes_amo30.main(["--archive", str(ARCHIVE), "--config", str(CONFIG), "--mettre-a-jour"]) == 0
    assert list(tmp_path.iterdir()) == []


def test_un_groupe_ajoute_est_annonce_dans_le_runner(monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    journal = groupes_amo30._journal_vide()
    journal["groupes_ajoutes"] = [{
        "groupe_id": "AN:AUTRE:18", "lignee_id": "AN:LIGNEE:AUTRE", "sigles_an": ["AUTRE"],
        "effectif_amo30": 40, "succede_a": [],
    }]
    groupes_amo30._publier_le_resume(journal, ecrite=True)
    assert "::notice::GROUPE_AJOUTE — AN:AUTRE:18" in capsys.readouterr().out
