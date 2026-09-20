"""Tests pour les arguments CLI de check_quality_gate.py (valeurs par défaut,
chemins personnalisés) — voir issue #212.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from check_quality_gate import _build_arg_parser


def test_gouvernements_args_defaults():
    args = _build_arg_parser().parse_args([])

    assert args.gouvernements_dir == Path("pivot_data/gouvernements")
    assert args.gouvernements_config == Path("raw_data/gouvernements_reels.json")


def test_gouvernements_args_chemins_personnalises():
    args = _build_arg_parser().parse_args([
        "--gouvernements-dir", "custom/gouvernements",
        "--gouvernements-config", "custom/gouvernements_reels.json",
    ])

    assert args.gouvernements_dir == Path("custom/gouvernements")
    assert args.gouvernements_config == Path("custom/gouvernements_reels.json")
