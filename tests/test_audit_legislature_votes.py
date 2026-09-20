"""Passe de corpus : la `legislature` des votes est-elle résoluble ? (#432)

Cette passe est un préalable à la normalisation des votes, pas une étape de
celle-ci : elle ne modifie aucun fichier et se contente de dire si la clé
`(legislature, numero_scrutin)` est utilisable sur l'ensemble du corpus, et par
quel mécanisme chaque scrutin y arrive.

Le code de sortie porte la moitié du contrat : un scrutin irrésoluble bloque,
parce qu'il ne recevra jamais de valeur par défaut (AGENTS.md §2.5).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import audit_legislature_votes
from audit_legislature_votes import analyser, main
from scrutins_legislature import PROVENANCE_CALENDRIER, PROVENANCE_COLLECTEE, PROVENANCE_JUMEAU


def _ecrire_profil(dossier: Path, slug: str, votes: list[dict], suffixe: str = ".json") -> None:
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{slug}{suffixe}").write_text(
        json.dumps({"slug": slug, "votes": votes}, ensure_ascii=False), encoding="utf-8"
    )


def _vote(numero, date, legislature=None):
    return {"numero_scrutin": numero, "date": date, "legislature": legislature, "position": "pour"}


def test_analyse_compte_paires_et_scrutins_distincts(tmp_path):
    _ecrire_profil(tmp_path, "alice", [_vote("1", "2026-01-05", "17"), _vote("2", "2026-01-06", "17")])
    _ecrire_profil(tmp_path, "bob", [_vote("1", "2026-01-05", "17")])

    rapport = analyser(tmp_path)

    assert rapport["n_paires"] == 3
    assert rapport["n_scrutins"] == 2
    assert rapport["echecs"] == []


def test_analyse_resout_entre_profils_pas_dans_un_seul(tmp_path):
    """Le jumeau étiqueté vit dans un autre fichier : c'est ce que la passe de
    corpus apporte et qu'une normalisation profil par profil ne peut pas voir."""
    _ecrire_profil(tmp_path, "ancien", [_vote("4084", "2024-06-07", None)])
    _ecrire_profil(tmp_path, "recent", [_vote("4084", "2024-06-07", "16")])

    rapport = analyser(tmp_path)

    assert rapport["par_occurrence"][PROVENANCE_JUMEAU] == 1
    assert rapport["par_occurrence"][PROVENANCE_COLLECTEE] == 1
    assert rapport["par_scrutin"][PROVENANCE_COLLECTEE] == 1
    assert rapport["profils_touches"][PROVENANCE_JUMEAU] == 1


def test_analyse_trace_la_derivation_calendaire_a_part(tmp_path):
    _ecrire_profil(tmp_path, "alice", [_vote("632", "2022-11-25", None)])

    rapport = analyser(tmp_path)

    assert rapport["par_scrutin"][PROVENANCE_CALENDRIER] == 1
    assert rapport["par_occurrence"][PROVENANCE_CALENDRIER] == 1
    assert rapport["par_occurrence"][PROVENANCE_JUMEAU] == 0
    assert rapport["legislatures"]["16"] == 1


def test_analyse_lit_aussi_les_pivots(tmp_path):
    """Le triplet lu porte le même nom dans les deux schémas : la passe doit
    accepter `raw_data/profiles` comme `pivot_data/profiles`."""
    _ecrire_profil(tmp_path, "alice", [_vote("1", "2026-01-05", "17")], suffixe=".pivot.json")

    assert analyser(tmp_path)["n_paires"] == 1


def test_analyse_ignore_un_profil_illisible_sans_planter(tmp_path, capsys):
    _ecrire_profil(tmp_path, "alice", [_vote("1", "2026-01-05", "17")])
    (tmp_path / "casse.json").write_text("{ pas du json", encoding="utf-8")

    rapport = analyser(tmp_path)

    assert rapport["n_paires"] == 1
    assert "Lecture impossible" in capsys.readouterr().out


def test_analyse_repertoire_absent_ne_plante_pas(tmp_path):
    rapport = analyser(tmp_path / "inexistant")
    assert rapport["n_paires"] == 0
    assert rapport["echecs"] == []


def test_cli_sort_en_zero_quand_tout_est_resolu(tmp_path, monkeypatch, capsys):
    _ecrire_profil(tmp_path, "ancien", [_vote("4084", "2024-06-07", None)])
    _ecrire_profil(tmp_path, "recent", [_vote("4084", "2024-06-07", "16")])
    monkeypatch.setattr(sys, "argv", ["audit_legislature_votes.py", "--profils-dir", str(tmp_path)])

    code = main()

    assert code == 0
    assert "Tous les scrutins sont résolus" in capsys.readouterr().out


def test_cli_bloque_sur_un_scrutin_irresoluble(tmp_path, monkeypatch, capsys):
    """Un vote daté dans l'entre-deux dissolution/ouverture (10/06 → 17/07/2024)
    n'appartient à aucune législature. Il bloque, il ne se voit pas attribuer la
    plus proche."""
    _ecrire_profil(tmp_path, "alice", [_vote("999", "2024-07-01", None)])
    monkeypatch.setattr(sys, "argv", ["audit_legislature_votes.py", "--profils-dir", str(tmp_path)])

    code = main()
    sortie = capsys.readouterr().out

    assert code == 1
    assert "irrésoluble" in sortie.lower()
    assert "§2.5" in sortie
    assert "2024-07-01" in sortie


def test_cli_ecrit_le_rapport_dans_out(tmp_path, monkeypatch, capsys):
    _ecrire_profil(tmp_path, "alice", [_vote("1", "2026-01-05", "17")])
    rapport = tmp_path / "rapports" / "legislature.md"
    monkeypatch.setattr(sys, "argv", [
        "audit_legislature_votes.py", "--profils-dir", str(tmp_path), "--out", str(rapport),
    ])

    assert main() == 0
    capsys.readouterr()
    assert "Résolution de `legislature`" in rapport.read_text(encoding="utf-8")


def test_le_repertoire_par_defaut_est_celui_des_profils_bruts():
    """Les profils bruts portent `votes_source` et sont la source de la
    normalisation ; les pivots en dérivent."""
    assert audit_legislature_votes.DEFAUT_PROFILS_DIR == Path("raw_data") / "profiles"
