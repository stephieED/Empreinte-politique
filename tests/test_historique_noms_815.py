#!/usr/bin/env python3
"""
Tests du lot #815 — `historique_noms` se remplit depuis les organes de l'Assemblée.

Un fichier par lot (#840). Ce qu'ils verrouillent :

- **la table committée dit ce que l'archive dit.** `historique_organes_an` est
  mesuré sur AMO30 puis committé — l'étape groupe du run ne lit aucune archive,
  comme pour la position politique (#686). Le premier test le confronte, entrée
  par entrée, à la fixture d'archive des XVIe et XVIIe : une valeur recopiée de
  travers ou vieillie fait échouer la suite au lieu de se publier ;
- **deux écritures du même fait ne divergent pas en silence** : l'historique
  doit nommer exactement `organes_an`, dans le même ordre ;
- **le champ atteint la fiche** par les deux générateurs, et une absence de
  mesure reste une liste vide, jamais un historique inventé.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import groupes_config  # noqa: E402
from group_profile import build_groupe_profile  # noqa: E402
from groupes_config import (  # noqa: E402
    CorrespondanceSiglesInvalide,
    charger_correspondance_sigles,
    historique_noms_publie,
)

pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

CONFIG = RACINE / "raw_data" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"


@pytest.fixture
def index(tmp_path, monkeypatch):
    """L'index de la fixture, construit dans un `tmp_path` — jamais dans le dépôt."""
    monkeypatch.chdir(tmp_path)
    an_roster.vider_memo()
    yield an_roster.charger_index_gp(ARCHIVE, repertoire_cache=tmp_path)
    an_roster.vider_memo()


def test_la_table_committee_dit_ce_que_l_archive_dit(index):
    """Fil-piège : chaque historique des XVIe et XVIIe, contre la fixture AMO30."""
    compares = 0
    for entree in charger_correspondance_sigles(CONFIG):
        if entree["legislature"] not in ("16", "17"):
            continue  # la fixture ne couvre que ces deux législatures
        mesure = an_roster.historique_organes(index, entree["legislature"], entree["sigles_an"])
        assert entree["historique_organes_an"] == mesure, entree["groupe_id"]
        compares += 1
    assert compares >= 20, "le fil-piège ne compare presque rien : la fixture a-t-elle bougé ?"


def test_les_trois_renommages_du_corpus_sont_publies():
    """Mesuré le 11/09/2026 : trois fiches AN sur 29 ont plus d'un organe."""
    attendus = {
        ("SOC", "16"): ["SOC", "SOC-A"],
        ("DEM", "15"): ["MODEM", "DEM"],
        ("UDR", "17"): ["AD", "UDR", "UDDPLR"],
    }
    for (sigle, legislature), sigles in attendus.items():
        historique = historique_noms_publie(sigle, legislature, CONFIG)
        assert [b["sigle"] for b in historique] == sigles
        assert all(b["organe_an"].startswith("PO") for b in historique)
    # Un organe ouvert n'a pas de fin, et ce n'est pas un trou.
    assert historique_noms_publie("UDR", "17", CONFIG)[-1]["fin"] is None


def test_un_historique_qui_contredit_organes_an_est_refuse(tmp_path):
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    entree = next(
        e for e in document["correspondance_sigles_an"]["groupes"] if e["groupe_id"] == "AN:SOC:16"
    )
    entree["historique_organes_an"] = list(reversed(entree["historique_organes_an"]))
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(CorrespondanceSiglesInvalide, match="l'une a bougé sans l'autre"):
        charger_correspondance_sigles(chemin)


def test_une_entree_non_mesuree_ne_publie_rien(tmp_path):
    """Pas de clé : `None`, et la fiche garde une liste vide — pas un historique inventé."""
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    for e in document["correspondance_sigles_an"]["groupes"]:
        e.pop("historique_organes_an", None)
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    assert historique_noms_publie("SOC", "16", chemin) is None


def test_le_champ_atteint_la_fiche():
    historique = historique_noms_publie("SOC", "16", CONFIG)
    fiche = build_groupe_profile(
        groupe_id="AN:SOC:16", groupe_sigle="SOC", groupe_nom="Socialistes",
        chambre="AN", legislature="16", profils=[], historique_noms=historique,
    )
    assert fiche["historique_noms"] == historique
    sans = build_groupe_profile(
        groupe_id="AN:SOC:16", groupe_sigle="SOC", groupe_nom="Socialistes",
        chambre="AN", legislature="16", profils=[],
    )
    assert sans["historique_noms"] == []


def test_generate_group_profiles_transmet_l_historique(monkeypatch, tmp_path):
    """Le générateur du run passe l'historique de la table, comme `succede_a`."""
    import generate_group_profiles as ggp

    recus: dict[str, object] = {}

    def fausse_generation(**kwargs):
        recus[kwargs["groupe_id"]] = kwargs.get("historique_noms")
        return {}

    monkeypatch.setattr(ggp, "generate_groupe_profile_from_roster", fausse_generation)
    monkeypatch.setattr(ggp, "charger_scrutins", lambda *_a, **_k: {})
    monkeypatch.setattr(ggp, "charger_amendements", lambda *_a, **_k: {})
    monkeypatch.setattr(ggp, "filter_roster_by_sigle", lambda *_a, **_k: [])
    groupe = next(
        g for g in json.loads(CONFIG.read_text(encoding="utf-8"))["groupes"]
        if g["groupe_id"] == "AN:SOC:16"
    )
    # Aucun fetch ne part : le roster rendu est vide, et c'est l'historique qui
    # est observé, pas la composition.
    monkeypatch.setattr(ggp, "fetch_full_roster", lambda *_a, **_k: [])
    ggp.generate_all(
        [copy.deepcopy(groupe)], profiles_dir=tmp_path, out_dir=tmp_path,
        chemin_config=CONFIG,
    )
    assert [b["sigle"] for b in recus["AN:SOC:16"]] == ["SOC", "SOC-A"]
