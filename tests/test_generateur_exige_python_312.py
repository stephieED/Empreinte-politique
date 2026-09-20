#!/usr/bin/env python3
"""
`generer_decisions_par_module.py` refuse de produire une table fausse en silence.

Constaté le 11/09/2026 : sous Python 3.11, `src/an_roster.py` ne se lit pas (une
f-string à antislash, légale depuis 3.12). Le script avalait la `SyntaxError`,
ignorait le module, et écrivait une table différente de celle de la CI — que
`tests/test_decisions_par_module.py` refusait ensuite, sans que l'on sache
pourquoi. Deux verrous : le refus sous 3.12, et un module illisible qui fait
échouer au lieu de disparaître.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "generer_decisions_par_module", RACINE / "scripts" / "generer_decisions_par_module.py"
)
generateur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generateur)


def test_un_module_illisible_fait_echouer(tmp_path):
    casse = tmp_path / "casse.py"
    casse.write_text("def f(:\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="ne se lit pas"):
        generateur.symboles_de_tete(casse)


def test_sous_python_311_le_script_refuse(monkeypatch, capsys):
    monkeypatch.setattr(generateur.sys, "version_info", (3, 11, 9, "final", 0))
    assert generateur.main([]) == 2
    assert "exige 3.12" in capsys.readouterr().err
