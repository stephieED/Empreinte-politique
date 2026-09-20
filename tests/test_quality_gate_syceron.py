"""Tests de non-régression pour le warning Syceron dans check_quality_gate.py."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from check_quality_gate import _report_low_syceron_coverage


def _write_pivot(tmp_path: Path, slug: str, chambre: str, mandats: list, interventions: list) -> None:
    profile = {
        "id": f"nd:{slug}",
        "nom": slug.replace("-", " ").title(),
        "chambre": chambre,
        "mandats": mandats,
        "interventions": interventions,
        "votes": [],
        "textes_portes": [],
        "amendements": [],
        "tags_thematiques": [],
        "sources": [],
        "meta": {"warnings": []},
    }
    (tmp_path / f"{slug}.pivot.json").write_text(json.dumps(profile), encoding="utf-8")


def test_report_low_syceron_coverage_emits_soft_warning_when_zero_debates(tmp_path):
    """Un candidat AN avec un mandat sur législature 17 (Syceron) mais 0 débat
    Syceron doit générer un soft warning (threshold=1)."""
    _write_pivot(
        tmp_path, "jean-dupont", "AN",
        mandats=[{"label": "Député", "categorie": "mandat_electif", "legislature": "17", "debut": "2022-06-01"}],
        interventions=[],
    )
    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=1)
    assert len(soft) == 1
    assert "jean-dupont" in soft[0]
    assert "0" in soft[0]
    assert "17" in soft[0]
    assert "Jean Dupont" in console
    assert "⚠️" in md


def test_report_low_syceron_coverage_no_warning_when_above_threshold(tmp_path):
    """Un candidat avec suffisamment de débats Syceron ne doit pas générer de warning."""
    _write_pivot(
        tmp_path, "marie-martin", "AN",
        mandats=[{"label": "Député", "categorie": "mandat_electif", "legislature": "16", "debut": "2017-06-01"}],
        interventions=[
            {
                "date": "2023-01-10",
                "source_url": "https://nosdeputes.fr/seance/2023-01-10",
                "source": {"type": "syceron", "url": "...", "source_id": "s1", "legislature": "16"},
            }
        ],
    )
    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=1)
    assert len(soft) == 0
    assert "✓" in console


def test_report_low_syceron_coverage_ignores_non_an_candidates(tmp_path):
    """Les candidats non-AN (Sénat, PE...) ne doivent pas être comptés."""
    _write_pivot(
        tmp_path, "senateur-x", "Senat",
        mandats=[{"label": "Sénateur", "legislature": "17", "debut": "2020-01-01"}],
        interventions=[],
    )
    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=1)
    assert len(soft) == 0


def test_report_low_syceron_coverage_ignores_non_syceron_legislatures(tmp_path):
    """Un candidat AN avec seulement des mandats hors législatures Syceron
    (ex. législature 14) ne doit pas être inclus dans le rapport."""
    _write_pivot(
        tmp_path, "ancien-depute", "AN",
        mandats=[{"label": "Député", "legislature": "14", "debut": "2012-06-01"}],
        interventions=[],
    )
    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=1)
    assert len(soft) == 0


def test_report_low_syceron_coverage_threshold_zero_returns_empty(tmp_path):
    """threshold=0 : désactivé → aucun warning même si couverture nulle."""
    _write_pivot(
        tmp_path, "depute-z", "AN",
        mandats=[{"label": "Député", "legislature": "17", "debut": "2022-06-01"}],
        interventions=[],
    )
    # threshold=0 est géré dans main() (guard), mais la fonction elle-même
    # avec threshold=0 ne produit aucun low (0 < 0 est faux).
    soft, console, md = _report_low_syceron_coverage(tmp_path, threshold=0)
    assert len(soft) == 0
