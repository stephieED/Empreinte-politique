import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_pipeline import (
    _build_arg_parser,
    build_report,
    compute_vue_ensemble,
    generate_markdown_report,
    main,
)
from audit_gouvernement_dataset import build_report as build_report_gouvernements
from audit_gouvernement_dataset import load_gouvernement_directory
from audit_groupe_dataset import build_report as build_report_groupes
from audit_groupe_dataset import load_groupe_directory
from audit_pivot_dataset import build_report as build_report_profils
from audit_pivot_dataset import load_pivot_directory


FIXTURES_PROFILS_DIR = Path(__file__).resolve().parent / "fixtures" / "audit_pivot"
FIXTURES_GROUPES_DIR = Path(__file__).resolve().parent / "fixtures" / "audit_groupe"
FIXTURES_GOUVERNEMENTS_DIR = Path(__file__).resolve().parent / "fixtures" / "audit_gouvernement"

REFERENCE_DATE = datetime(2026, 8, 10, tzinfo=timezone.utc)


def _rapport_profils(warnings_par_type=None, erreurs_lecture=None, total_profils=2):
    return {
        "meta": {
            "genere_le": REFERENCE_DATE.isoformat(),
            "total_profils": total_profils,
            "total_erreurs_lecture": len(erreurs_lecture or []),
            "staleness_days": 30,
        },
        "warnings": {
            "total_warnings": sum(e["frequence"] for e in (warnings_par_type or {}).values()),
            "par_type": warnings_par_type or {},
        },
        "erreurs_lecture": erreurs_lecture or [],
    }


def _rapport_groupes(warnings_par_type=None, erreurs_lecture=None, total_groupes=1):
    return {
        "meta": {
            "genere_le": REFERENCE_DATE.isoformat(),
            "total_groupes": total_groupes,
            "total_erreurs_lecture": len(erreurs_lecture or []),
            "staleness_days": 30,
        },
        "warnings": {
            "total_warnings": sum(e["frequence"] for e in (warnings_par_type or {}).values()),
            "par_type": warnings_par_type or {},
        },
        "erreurs_lecture": erreurs_lecture or [],
    }


def _rapport_gouvernements(warnings_par_type=None, erreurs_lecture=None, total_gouvernements=1):
    return {
        "meta": {
            "genere_le": REFERENCE_DATE.isoformat(),
            "total_gouvernements": total_gouvernements,
            "total_erreurs_lecture": len(erreurs_lecture or []),
            "staleness_days": 30,
        },
        "warnings": {
            "total_warnings": sum(e["frequence"] for e in (warnings_par_type or {}).values()),
            "par_type": warnings_par_type or {},
        },
        "erreurs_lecture": erreurs_lecture or [],
    }


# ---------------------------------------------------------------------------
# compute_vue_ensemble : composition à partir de rapports simulés
# ---------------------------------------------------------------------------

def test_compute_vue_ensemble_agrege_les_totaux():
    rapport_profils = _rapport_profils(
        erreurs_lecture=[{"fichier": "a.pivot.json", "erreur": "JSON invalide"}],
        total_profils=3,
    )
    rapport_groupes = _rapport_groupes(
        erreurs_lecture=[{"fichier": "b.json", "erreur": "JSON invalide"}],
        total_groupes=2,
    )
    rapport_gouvernements = _rapport_gouvernements(
        erreurs_lecture=[{"fichier": "c.json", "erreur": "JSON invalide"}],
        total_gouvernements=4,
    )

    vue = compute_vue_ensemble(rapport_profils, rapport_groupes, rapport_gouvernements)

    assert vue["total_profils_audites"] == 3
    assert vue["total_groupes_audites"] == 2
    assert vue["total_gouvernements_audites"] == 4
    assert vue["total_erreurs_lecture"] == 3
    assert vue["erreurs_lecture"] == {
        "profils": [{"fichier": "a.pivot.json", "erreur": "JSON invalide"}],
        "groupes": [{"fichier": "b.json", "erreur": "JSON invalide"}],
        "gouvernements": [{"fichier": "c.json", "erreur": "JSON invalide"}],
    }


def test_compute_vue_ensemble_fusionne_les_warnings_communs_aux_trois_audits():
    rapport_profils = _rapport_profils(
        warnings_par_type={
            "identite introuvable": {"frequence": 2, "ids": ["nosdeputes:a", "nosdeputes:b"]},
        },
    )
    rapport_groupes = _rapport_groupes(
        warnings_par_type={
            "identite introuvable": {"frequence": 1, "groupe_ids": ["AN:LFI"]},
        },
    )
    rapport_gouvernements = _rapport_gouvernements(
        warnings_par_type={
            "identite introuvable": {
                "frequence": 1, "gouvernement_ids": ["gouvernement:BARNIER"],
            },
        },
    )

    vue = compute_vue_ensemble(rapport_profils, rapport_groupes, rapport_gouvernements)

    assert vue["warnings"]["total_warnings"] == 4
    assert vue["warnings"]["par_type"] == {
        "identite introuvable": {
            "frequence": 4,
            "profils_ids": ["nosdeputes:a", "nosdeputes:b"],
            "groupe_ids": ["AN:LFI"],
            "gouvernement_ids": ["gouvernement:BARNIER"],
        },
    }


def test_compute_vue_ensemble_type_de_warning_present_dans_un_seul_audit():
    rapport_profils = _rapport_profils(
        warnings_par_type={
            "seulement_profils": {"frequence": 1, "ids": ["nosdeputes:a"]},
        },
    )
    rapport_groupes = _rapport_groupes(
        warnings_par_type={
            "seulement_groupes": {"frequence": 1, "groupe_ids": ["AN:LFI"]},
        },
    )
    rapport_gouvernements = _rapport_gouvernements(
        warnings_par_type={
            "seulement_gouvernements": {
                "frequence": 1, "gouvernement_ids": ["gouvernement:BARNIER"],
            },
        },
    )

    vue = compute_vue_ensemble(rapport_profils, rapport_groupes, rapport_gouvernements)

    assert vue["warnings"]["par_type"]["seulement_profils"] == {
        "frequence": 1,
        "profils_ids": ["nosdeputes:a"],
        "groupe_ids": [],
        "gouvernement_ids": [],
    }
    assert vue["warnings"]["par_type"]["seulement_groupes"] == {
        "frequence": 1,
        "profils_ids": [],
        "groupe_ids": ["AN:LFI"],
        "gouvernement_ids": [],
    }
    assert vue["warnings"]["par_type"]["seulement_gouvernements"] == {
        "frequence": 1,
        "profils_ids": [],
        "groupe_ids": [],
        "gouvernement_ids": ["gouvernement:BARNIER"],
    }


def test_compute_vue_ensemble_sans_warning_ni_erreur():
    vue = compute_vue_ensemble(
        _rapport_profils(), _rapport_groupes(), _rapport_gouvernements(),
    )

    assert vue["warnings"] == {"total_warnings": 0, "par_type": {}}
    assert vue["erreurs_lecture"] == {"profils": [], "groupes": [], "gouvernements": []}
    assert vue["total_erreurs_lecture"] == 0


# ---------------------------------------------------------------------------
# build_report : assemblage meta + vue_ensemble + sous-rapports
# ---------------------------------------------------------------------------

def test_build_report_assemble_meta_et_sous_rapports():
    rapport_profils = _rapport_profils(total_profils=3)
    rapport_groupes = _rapport_groupes(total_groupes=2)
    rapport_gouvernements = _rapport_gouvernements(total_gouvernements=4)

    rapport = build_report(rapport_profils, rapport_groupes, rapport_gouvernements)

    assert rapport["meta"] == {
        "genere_le": REFERENCE_DATE.isoformat(),
        "staleness_days": 30,
    }
    assert rapport["audit_profils"] is rapport_profils
    assert rapport["audit_groupes"] is rapport_groupes
    assert rapport["audit_gouvernements"] is rapport_gouvernements
    assert rapport["vue_ensemble"]["total_profils_audites"] == 3
    assert rapport["vue_ensemble"]["total_groupes_audites"] == 2
    assert rapport["vue_ensemble"]["total_gouvernements_audites"] == 4


def test_build_report_sur_fixtures_reelles():
    profils, erreurs_profils = load_pivot_directory(FIXTURES_PROFILS_DIR)
    rapport_profils = build_report_profils(
        profils, erreurs_profils, staleness_days=30, reference_date=REFERENCE_DATE,
    )
    groupes, erreurs_groupes = load_groupe_directory(FIXTURES_GROUPES_DIR)
    rapport_groupes = build_report_groupes(
        groupes, erreurs_groupes, staleness_days=30, reference_date=REFERENCE_DATE,
    )
    gouvernements, erreurs_gouvernements = load_gouvernement_directory(FIXTURES_GOUVERNEMENTS_DIR)
    rapport_gouvernements = build_report_gouvernements(
        gouvernements, erreurs_gouvernements, staleness_days=30, reference_date=REFERENCE_DATE,
    )

    rapport = build_report(rapport_profils, rapport_groupes, rapport_gouvernements)

    assert rapport["vue_ensemble"]["total_profils_audites"] == 3
    assert rapport["vue_ensemble"]["total_groupes_audites"] == 3
    assert rapport["vue_ensemble"]["total_gouvernements_audites"] == 3
    assert rapport["vue_ensemble"]["total_erreurs_lecture"] == 3
    assert rapport["vue_ensemble"]["warnings"]["total_warnings"] == 2
    assert rapport["vue_ensemble"]["warnings"]["par_type"]["couverture_roster"] == {
        "frequence": 1,
        "profils_ids": [],
        "groupe_ids": ["AN:LFI"],
        "gouvernement_ids": [],
    }
    assert rapport["vue_ensemble"]["warnings"]["par_type"]["couverture_ministerielle"] == {
        "frequence": 1,
        "profils_ids": [],
        "groupe_ids": [],
        "gouvernement_ids": ["gouvernement:BARNIER"],
    }


# ---------------------------------------------------------------------------
# generate_markdown_report
# ---------------------------------------------------------------------------

def test_generate_markdown_report_contient_toutes_les_sections():
    # generate_markdown_report délègue les sous-rapports détaillés aux
    # générateurs Markdown de chaque module ; on construit ici des
    # sous-rapports complets via les fixtures pour un test réaliste.
    profils, erreurs_profils = load_pivot_directory(FIXTURES_PROFILS_DIR)
    rapport_profils = build_report_profils(
        profils, erreurs_profils, staleness_days=30, reference_date=REFERENCE_DATE,
    )
    groupes, erreurs_groupes = load_groupe_directory(FIXTURES_GROUPES_DIR)
    rapport_groupes = build_report_groupes(
        groupes, erreurs_groupes, staleness_days=30, reference_date=REFERENCE_DATE,
    )
    gouvernements, erreurs_gouvernements = load_gouvernement_directory(FIXTURES_GOUVERNEMENTS_DIR)
    rapport_gouvernements = build_report_gouvernements(
        gouvernements, erreurs_gouvernements, staleness_days=30, reference_date=REFERENCE_DATE,
    )
    rapport = build_report(rapport_profils, rapport_groupes, rapport_gouvernements)

    markdown = generate_markdown_report(rapport)

    assert "# Rapport d'audit pipeline (profils + groupes + gouvernements)" in markdown
    assert "## Vue d'ensemble" in markdown
    assert "# Rapport d'audit du jeu de données pivot" in markdown
    assert "# Rapport d'audit du jeu de données groupes" in markdown
    assert "# Rapport d'audit du jeu de données gouvernements" in markdown
    assert "couverture_roster" in markdown
    assert "couverture_ministerielle" in markdown


# ---------------------------------------------------------------------------
# CLI : bout-en-bout sur fixtures combinées
# ---------------------------------------------------------------------------

def test_build_arg_parser_valeurs_par_defaut():
    parser = _build_arg_parser()
    args = parser.parse_args([])

    assert args.profiles_dir == "pivot_data/profiles"
    assert args.groupes_dir == "pivot_data/groupes"
    assert args.gouvernements_dir == "pivot_data/gouvernements"
    assert args.staleness_days == 30
    assert args.output_json is None
    assert args.output_md is None


def test_main_ecrit_json_et_markdown(tmp_path):
    output_json = tmp_path / "rapport.json"
    output_md = tmp_path / "rapport.md"

    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
        "--output-json", str(output_json),
        "--output-md", str(output_md),
        "--staleness-days", "30",
    ])

    assert code == 0
    assert output_json.exists()
    assert output_md.exists()

    rapport = json.loads(output_json.read_text(encoding="utf-8"))
    assert rapport["meta"]["staleness_days"] == 30
    assert rapport["vue_ensemble"]["total_profils_audites"] == 3
    assert rapport["vue_ensemble"]["total_groupes_audites"] == 3
    assert rapport["vue_ensemble"]["total_gouvernements_audites"] == 3
    assert rapport["vue_ensemble"]["total_erreurs_lecture"] == 3
    assert rapport["audit_profils"]["meta"]["total_profils"] == 3
    assert rapport["audit_groupes"]["meta"]["total_groupes"] == 3
    assert rapport["audit_gouvernements"]["meta"]["total_gouvernements"] == 3

    markdown = output_md.read_text(encoding="utf-8")
    assert "# Rapport d'audit pipeline (profils + groupes + gouvernements)" in markdown


def test_main_sans_output_json_ecrit_sur_stdout(capsys):
    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
    ])

    assert code == 0
    captured = capsys.readouterr()
    rapport = json.loads(captured.out)
    assert rapport["vue_ensemble"]["total_profils_audites"] == 3
    assert rapport["vue_ensemble"]["total_groupes_audites"] == 3
    assert rapport["vue_ensemble"]["total_gouvernements_audites"] == 3


def test_main_dossier_profils_introuvable_retourne_1(tmp_path):
    code = main([
        "--profiles-dir", str(tmp_path / "n-existe-pas"),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
    ])

    assert code == 1


def test_main_dossier_groupes_introuvable_retourne_1(tmp_path):
    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(tmp_path / "n-existe-pas"),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
    ])

    assert code == 1


def test_main_dossier_gouvernements_introuvable_retourne_1(tmp_path):
    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(tmp_path / "n-existe-pas"),
    ])

    assert code == 1


def test_main_out_dir_est_cree_si_absent(tmp_path):
    output_json = tmp_path / "sous" / "dossier" / "rapport.json"

    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
        "--output-json", str(output_json),
    ])

    assert code == 0
    assert output_json.exists()


def test_main_output_dir_ecrit_json_et_markdown_horodates(tmp_path):
    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
        "--output-dir", str(tmp_path),
    ])

    assert code == 0
    json_files = list(tmp_path.glob("audit_pipeline_*.json"))
    md_files = list(tmp_path.glob("audit_pipeline_*.md"))
    assert len(json_files) == 1
    assert len(md_files) == 1


def test_main_output_dir_incompatible_avec_output_json(tmp_path):
    code = main([
        "--profiles-dir", str(FIXTURES_PROFILS_DIR),
        "--groupes-dir", str(FIXTURES_GROUPES_DIR),
        "--gouvernements-dir", str(FIXTURES_GOUVERNEMENTS_DIR),
        "--output-dir", str(tmp_path),
        "--output-json", str(tmp_path / "rapport.json"),
    ])

    assert code == 1
    assert list(tmp_path.glob("*.json")) == []
