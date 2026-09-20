"""Tests pour `_report_groupes` (check_quality_gate.py, §4 groupes).

Comble un trou de couverture identifié par #193 : `_report_groupes` n'avait
jusqu'ici aucun test dédié (seul `tests/test_quality_gate_syceron.py` couvre
une autre section du même module). Couvre le seuil absolu historique
(`min_members`) et le nouveau seuil relatif optionnel (`min_coverage_pct`,
voir docs/decisions/seuil-couverture-groupe.md).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from check_quality_gate import _report_groupes


def _write_groupe(
    groupes_dir: Path,
    fichier: str,
    groupe_id: str,
    roster_total: int,
    profils_disponibles: int,
    nb_membres: int = 1,
    nb_cohesion: int = 0,
    warnings: list | None = None,
) -> None:
    data = {
        "schema_version": "1",
        "type_document": "profil_groupe",
        "groupe_id": groupe_id,
        "groupe_sigle": groupe_id.split(":")[-1],
        "groupe_nom": f"Groupe {groupe_id}",
        "chambre": "AN",
        "legislature": "17",
        "periode": {"debut": "2024-07-18", "fin": None, "actif": True},
        "historique_noms": [],
        "membres": [
            {
                "membre_id": f"nosdeputes:membre-{i}",
                "nom": f"Membre {i}",
                "debut_dans_groupe": "2024-07-18",
                "fin_dans_groupe": None,
                "actif": True,
            }
            for i in range(nb_membres)
        ],
        "effectif": {"actuel": nb_membres, "min_historique": None, "max_historique": None},
        "cohesion_votes": [{"numero_scrutin": str(i)} for i in range(nb_cohesion)],
        "tags_thematiques_agreges": [],
        "mandats_agreges": [],
        "amendements_agreges": {
            "nb_amendements": 0, "nb_adoptes": 0, "nb_rejetes": 0,
            "nb_irrecevables": 0, "nb_retires_ou_tombes": 0, "taux_adoption": None,
            "par_type_deposant": {},
        },
        "sources": [],
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-08-01T10:00:00+00:00",
            "licence_donnees": "ODbL",
            "profils_sources": [],
            "warnings": warnings or [],
            "couverture_roster": {
                "roster_total": roster_total,
                "profils_disponibles": profils_disponibles,
            },
        },
    }
    (groupes_dir / fichier).write_text(json.dumps(data), encoding="utf-8")


def _write_config(config_path: Path, groupes: list[dict]) -> None:
    config_path.write_text(json.dumps({"groupes": groupes}), encoding="utf-8")


# ---------------------------------------------------------------------------
# Structure cassée (hard errors) — non-régression
# ---------------------------------------------------------------------------

def test_report_groupes_fichier_manquant_est_une_erreur_dure(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "manquant.json"}])

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert len(hard) == 1
    assert "fichier manquant" in hard[0]
    assert "✗" in console


def test_report_groupes_config_illisible_est_une_erreur_dure(tmp_path):
    config_path = tmp_path / "n-existe-pas.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert len(hard) == 1
    assert "Impossible de lire" in hard[0]


# ---------------------------------------------------------------------------
# Seuil absolu (min_members) — comportement historique
# ---------------------------------------------------------------------------

def test_report_groupes_min_members_soft_fail_sous_le_seuil(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=76, profils_disponibles=0, nb_membres=0)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert hard == []
    assert len(soft) == 1
    assert "couverture insuffisante" in soft[0]
    assert "0/76" in soft[0]


def test_report_groupes_min_members_ok_au_dessus_du_seuil(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=76, profils_disponibles=1, nb_cohesion=1)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert hard == []
    assert soft == []


def test_report_groupes_min_members_desactive_avec_zero(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=76, profils_disponibles=0, nb_membres=0)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=0)

    # min_members=0 : 0 < 0 est faux, le soft fail "couverture insuffisante" ne se déclenche pas.
    assert not any("couverture insuffisante" in w for w in soft)


# ---------------------------------------------------------------------------
# Seuil relatif (min_coverage_pct) — nouveau, désactivé par défaut
# ---------------------------------------------------------------------------

def test_report_groupes_min_coverage_pct_desactive_par_defaut(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    # Couverture très faible (0.5 %), mais min_coverage_pct par défaut = 0 (désactivé).
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=193, profils_disponibles=1, nb_cohesion=1)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert not any("taux de couverture insuffisant" in w for w in soft)


def test_report_groupes_min_coverage_pct_soft_fail_sous_le_seuil(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=100, profils_disponibles=50, nb_cohesion=1)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(
        config_path, groupes_dir, min_members=1, min_coverage_pct=80.0
    )

    assert hard == []
    assert any("taux de couverture insuffisant" in w for w in soft)
    assert any("50.0%" in w for w in soft)
    assert "⚠" in console


def test_report_groupes_min_coverage_pct_ok_au_dessus_du_seuil(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=100, profils_disponibles=99, nb_cohesion=1)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(
        config_path, groupes_dir, min_members=1, min_coverage_pct=80.0
    )

    assert hard == []
    assert not any("taux de couverture insuffisant" in w for w in soft)


def test_report_groupes_min_coverage_pct_hard_errors_toujours_prioritaires(tmp_path):
    """Un seuil relatif ne doit jamais transformer une structure cassée en soft warning."""
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "absent.json"}])

    hard, soft, console, md = _report_groupes(
        config_path, groupes_dir, min_members=1, min_coverage_pct=80.0
    )

    assert len(hard) == 1
    assert soft == []


def test_report_groupes_markdown_affiche_le_taux_de_couverture(tmp_path):
    config_path = tmp_path / "groupes_reels.json"
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "x.json", "AN:X", roster_total=100, profils_disponibles=25, nb_cohesion=1)
    _write_config(config_path, [{"groupe_id": "AN:X", "groupe_nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert "Taux de couverture (%)" in md
    assert "25.0%" in md
