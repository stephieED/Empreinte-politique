#!/usr/bin/env python3
"""
Tests du lot #1223 — le type d'organe d'un mandat local est dans le vocabulaire.

Le lot #922 écrivait `type_organe_source` sur chaque mandat local sans étendre
`KNOWN_TYPES_ORGANE_SOURCE` : 38 erreurs sur 16 des 34 fiches de candidats
déclarés, mesurées le 05/10/2026, que personne ne voyait parce que
`validate_profil()` ne tourne dans aucun job.

Ce que ces tests verrouillent : **ce que la collecte peut écrire, le schéma
l'accepte** — lu dans le code de la collecte, pas dans le corpus du jour, qui
n'en portait que quatre sur neuf.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from rne_opendata import FICHIERS_LOCAUX, normaliser  # noqa: E402
from schema_pivot import KNOWN_TYPES_ORGANE_SOURCE, validate_profil  # noqa: E402


def test_tout_type_que_la_collecte_locale_ecrit_est_dans_le_vocabulaire():
    hors = sorted(set(FICHIERS_LOCAUX.values()) - KNOWN_TYPES_ORGANE_SOURCE)
    assert not hors, (
        f"rne_opendata.FICHIERS_LOCAUX écrit {hors} que KNOWN_TYPES_ORGANE_SOURCE "
        "ne connaît pas — étendre le frozenset, jamais le contourner."
    )


@pytest.mark.parametrize("type_organe", sorted(set(FICHIERS_LOCAUX.values())))
def test_validate_profil_accepte_un_mandat_local_de_chaque_type(type_organe):
    # Forme copiée d'un mandat local de xavier-bertrand.pivot.json (privé
    # 4275c239d, 06/10/2026), réduite aux clés que la validation regarde.
    mandat = {
        "label": "Hauts-de-France",
        "categorie": "mandat_local",
        "categorie_source": "rne",
        "type_organe_source": type_organe,
        "fonction": "Président du conseil régional",
        "debut": "2021-07-02",
        "fin": None,
        "actif": True,
    }
    erreurs = validate_profil({"mandats": [mandat]})
    assert not [e for e in erreurs if "type_organe_source" in e]


def test_un_type_inconnu_est_toujours_refuse():
    erreurs = validate_profil({"mandats": [{"categorie": "mandat_local", "type_organe_source": "conseil_inconnu"}]})
    assert any("type_organe_source non reconnu" in e for e in erreurs)
