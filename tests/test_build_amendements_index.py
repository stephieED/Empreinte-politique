"""Tests du point d'entrée dédié `src/build_amendements_index.py` (issue #251,
sous-issue 3/6 de #248) : construit sans condition les index amendements des
3 législatures de `AN_AMENDEMENTS_PATH`, sans dépendre d'une liste de
candidats, avec isolation par législature (un échec n'empêche pas les
autres, aucune exception non gérée ne doit remonter à l'appelant CI).

#749 — ces tests patchent AUSSI `amendements_index_en_cache_utilisable`, pour
la même raison qu'ils patchaient déjà `amendements_index_deja_figee` : sans
cela ils dépendraient silencieusement de l'état réel du cache disque de la
machine qui les exécute, et passeraient ou non selon qu'elle a déjà collecté.
`return_value=None` signifie « aucun cache servable », donc « construis »."""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from build_amendements_index import build_all_amendements_index, main
from candidate_profile import AN_AMENDEMENTS_PATH, AmendementsIndexError


def test_build_all_amendements_index_calls_all_three_legislatures():
    calls = []

    def fake_index(legislature):
        calls.append(legislature)
        return {}

    with (
        patch("build_amendements_index._download_and_build_amendement_index", side_effect=fake_index),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", return_value=False),
    ):
        ok = build_all_amendements_index()

    assert calls == list(AN_AMENDEMENTS_PATH), "Les 3 législatures doivent être tentées, dans l'ordre déclaré"
    assert ok is True


def test_build_all_amendements_index_partial_failure_does_not_stop_others():
    """Une législature en échec définitif ne doit ni interrompre la boucle, ni
    lever d'exception non gérée : les législatures suivantes sont tout de
    même tentées (même isolation que `fetch_amendements_officiels`)."""
    calls = []

    def fake_index(legislature):
        calls.append(legislature)
        if legislature == "16":
            raise AmendementsIndexError("échec du téléchargement (simulé)")
        return {"PA1": []}

    with (
        patch("build_amendements_index._download_and_build_amendement_index", side_effect=fake_index),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", return_value=False),
    ):
        ok = build_all_amendements_index()

    assert calls == list(AN_AMENDEMENTS_PATH), "Les 3 législatures doivent être tentées malgré l'échec de la 16e"
    assert ok is False, "Un échec partiel doit être reflété dans la valeur de retour"


def test_build_all_amendements_index_all_succeed_returns_true():
    with (
        patch("build_amendements_index._download_and_build_amendement_index", return_value={"PA1": []}),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", return_value=False),
    ):
        assert build_all_amendements_index() is True


def test_build_all_amendements_index_all_fail_returns_false_without_raising():
    with (
        patch(
            "build_amendements_index._download_and_build_amendement_index",
            side_effect=AmendementsIndexError("échec (simulé)"),
        ),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", return_value=False),
    ):
        assert build_all_amendements_index() is False


def test_build_all_amendements_index_skips_already_frozen_legislature():
    """Une législature figée déjà matérialisée en cache est sautée sans
    recharger l'index existant en mémoire (évite l'OOM constaté en pratique
    sur un index volumineux, voir la docstring du module)."""
    calls = []

    def fake_index(legislature):
        calls.append(legislature)
        return {}

    def fake_deja_figee(legislature):
        return legislature == "16"

    with (
        patch("build_amendements_index._download_and_build_amendement_index", side_effect=fake_index),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", side_effect=fake_deja_figee),
    ):
        ok = build_all_amendements_index()

    assert "16" not in calls, "Une législature déjà figée ne doit jamais être rechargée"
    assert calls == [leg for leg in AN_AMENDEMENTS_PATH if leg != "16"]
    assert ok is True


def test_main_returns_exit_code_1_on_partial_failure():
    def fake_index(legislature):
        if legislature == "15":
            raise AmendementsIndexError("échec du téléchargement (simulé)")
        return {}

    with (
        patch("build_amendements_index._download_and_build_amendement_index", side_effect=fake_index),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", return_value=False),
    ):
        assert main([]) == 1


def test_main_returns_exit_code_0_when_all_succeed():
    with (
        patch("build_amendements_index._download_and_build_amendement_index", return_value={}),
        patch("build_amendements_index.amendements_index_en_cache_utilisable", return_value=None),
        patch("build_amendements_index.amendements_index_deja_figee", return_value=False),
    ):
        assert main([]) == 0
