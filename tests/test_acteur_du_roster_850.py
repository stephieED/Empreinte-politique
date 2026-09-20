#!/usr/bin/env python3
"""
Tests du lot #850 — un membre de roster n'est plus re-deviné par son nom.

Un fichier par lot (#840). Ce qu'ils verrouillent :

- **l'acteur du roster voyage jusqu'à la collecte**, de l'entrée de
  `roster_candidats.json` à `build_profile`, et seulement pour un membre de
  roster — un candidat déclaré passe par la table (#757) ;
- **fourni, il passe devant toute résolution** : la correspondance par nom n'est
  plus appelée. C'est elle qui rendait six membres « introuvables » au run
  `34575181245` — une apostrophe (`claire-o-petit`), une barre
  (`emeline-k-bidi`), deux homonymes (`beatrice-descamps`) ;
- **sauf s'il contredit la table**, et alors rien n'est collecté. Mesuré le
  11/09/2026 : 0 contradiction sur les 1 134 entrées de roster qui ont une
  entrée de table — les 6 qui n'en ont pas sont exactement les six
  introuvables.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import candidate_profile  # noqa: E402
import generate_all_profiles  # noqa: E402
from candidate_profile import (  # noqa: E402
    ActeurContreditParLaTable,
    fetch_identite_officielle_par_slug,
)
from generate_roster_candidats import build_roster_candidats_detaille  # noqa: E402


# ---------------------------------------------------------------------------
# La résolution d'identité
# ---------------------------------------------------------------------------

@pytest.fixture
def referentiel(monkeypatch):
    """Un index d'identité et une table en mémoire ; la résolution par nom interdite.

    Rien du dépôt n'est lu : ni le cache AMO30 du poste, ni la table committée
    (#721, #791).
    """
    index = {
        "PA720696": {"nom_complet": "Béatrice Descamps"},
        "PA392736": {"nom_complet": "Béatrice Descamps"},
        "PA841729": {"nom_complet": "Abdelkader Lahmar"},
    }
    table = {"abdelkader-lahmar": {"acteur_ref": "PA841729"}}
    appels_par_nom: list[str] = []

    def resolution_par_nom(slug, **_):
        appels_par_nom.append(slug)
        return None

    monkeypatch.setattr(candidate_profile, "_build_acteur_identite_index", lambda: index)
    monkeypatch.setattr(candidate_profile, "_correspondance_committee", lambda: table)
    monkeypatch.setattr(candidate_profile, "_resolve_acteur_ref_par_slug", resolution_par_nom)
    return appels_par_nom


def test_l_acteur_du_roster_passe_devant_le_nom(referentiel):
    """Deux homonymes dans l'index : le nom renonce, le roster tranche."""
    fiche, acteur = fetch_identite_officielle_par_slug(
        "beatrice-descamps", acteur_ref="PA720696"
    )
    assert acteur == "PA720696"
    assert fiche == {"nom_complet": "Béatrice Descamps"}
    assert referentiel == [], "la correspondance par nom ne doit plus être appelée"


def test_la_table_qui_s_accorde_ne_change_rien(referentiel):
    _, acteur = fetch_identite_officielle_par_slug(
        "abdelkader-lahmar", acteur_ref="PA841729"
    )
    assert acteur == "PA841729"


def test_la_table_qui_contredit_le_roster_empeche_la_collecte(referentiel):
    """Un désaccord ne se tranche pas en silence (#757) : les deux acteurs sont nommés."""
    with pytest.raises(ActeurContreditParLaTable) as exc:
        fetch_identite_officielle_par_slug("abdelkader-lahmar", acteur_ref="PA999999")
    assert "PA999999" in str(exc.value) and "PA841729" in str(exc.value)


def test_sans_acteur_fourni_rien_ne_change(referentiel):
    """Un candidat déclaré, ou une entrée d'avant ce lot : la résolution d'origine."""
    assert fetch_identite_officielle_par_slug("inconnu") == (None, None)
    assert referentiel == ["inconnu"]


# ---------------------------------------------------------------------------
# Le trajet : roster → liste → collecte
# ---------------------------------------------------------------------------

def test_l_entree_de_roster_porte_l_acteur_en_clair():
    """`source` en portait l'identifiant, encodé dans une URL que rien ne relisait."""
    groupes = [{
        "groupe_id": "AN:LIOT:16", "groupe_sigle": "LIOT", "groupe_nom": "LIOT",
        "chambre": "AN", "legislature": "16", "roster_chambre": "deputes",
        "fichier": "groupe-AN-LIOT-16.json",
    }]
    rosters = {("deputes", "16"): [{
        "slug": "pierre-morel-a-l-huissier", "slug_origine": "fabrique",
        "nom": "Pierre Morel-À-L'Huissier", "groupe_sigle": "LIOT",
        "mandat_debut": "2022-06-29", "mandat_fin": "2024-06-09",
        "acteur_ref": "PA266788",
    }]}
    candidats, _ = build_roster_candidats_detaille(groupes, rosters)
    assert [c["acteur_ref"] for c in candidats] == ["PA266788"]


def _args_roster() -> argparse.Namespace:
    return argparse.Namespace(
        source="an", pivot_only=False, skip_existing=False,
        skip_interventions=False, interventions_theme_seul=False,
        skip_dossiers_legislatifs=True, budget_interventions_secondes=0,
        budget_collecte_secondes=0, skip_ue=True, pivot=False, no_merge=False,
        enrich_parltrack=False, candidats_declares=frozenset(),
    )


def _collecte_espionne(monkeypatch) -> list[dict]:
    recus: list[dict] = []

    def fausse_collecte(chambre, slug, **kwargs):
        recus.append(kwargs)
        return {
            "slug": slug, "chambre": chambre, "identite": None, "mandats": [],
            "votes": [], "interventions": [], "amendements": [],
            "dossiers_legislatifs": [], "votes_source": None, "source": None,
            "meta": {"warnings": [], "synchro_sources": {}},
        }

    monkeypatch.setattr("generate_all_profiles.build_profile", fausse_collecte)
    return recus


def test_un_membre_de_roster_transmet_son_acteur_a_la_collecte(monkeypatch, tmp_path):
    recus = _collecte_espionne(monkeypatch)
    generate_all_profiles.process_candidat(
        {"nom": "Claire O'Petit", "slug": "claire-o-petit",
         "statut": "roster_groupe", "acteur_ref": "PA719364"},
        _args_roster(), tmp_path / "raw", tmp_path / "pivot",
    )
    assert recus and recus[0]["acteur_ref"] == "PA719364"


def test_un_candidat_declare_passe_par_la_table(monkeypatch, tmp_path):
    """Même si son entrée portait un `acteur_ref` : c'est la table qui le résout (#757)."""
    recus = _collecte_espionne(monkeypatch)
    generate_all_profiles.process_candidat(
        {"nom": "Un Candidat", "slug": "un-candidat",
         "statut": "declare", "acteur_ref": "PA000001"},
        _args_roster(), tmp_path / "raw", tmp_path / "pivot",
    )
    assert recus and recus[0]["acteur_ref"] is None
