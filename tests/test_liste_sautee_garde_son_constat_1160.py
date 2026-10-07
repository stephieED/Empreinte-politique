#!/usr/bin/env python3
"""
Tests du lot #1160 — une liste qu'un run n'a pas lue garde ce que le dernier
run qui l'a lue a établi.

Arbitrage de la propriétaire, 07/10/2026 (option A) : la fiche dit ce que le
dernier run qui a LU la liste a constaté, avec sa date ; « non collecté »
seulement si aucun run ne l'a jamais lue.

Deux défauts, deux verrous :

- **la fusion de la couverture** donnait raison au constat le plus récent même
  quand il disait seulement « ce run a sauté la liste » ;
- **le roster parlait pour l'AN** : un candidat déclaré relu par un job roster,
  qui saute ses interventions exprès, déclarait « interventions écartées » —
  et cette déclaration, fusionnée après celle de l'AN, devenait celle du
  profil. Mesuré sur le run `37526734878` (06/10, `collect_interventions=true`).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import generate_all_profiles  # noqa: E402
from merge_profile import fusionner_couverture, merge_raw_profile  # noqa: E402

# Entrées copiées de pivot_data/profiles/jean-luc-melenchon.pivot.json
# (privé 58ca17625, 07/10/2026), preuves raccourcies.
SAUTEE = {
    "etat": "non_collecte", "cause": "par_decision",
    "preuve": "collecte écartée par le run qui a produit le profil brut (meta.collecte_ecartee, #357) : interventions",
    "constate_le": "2026-10-07",
}
LUE = [
    {"etat": "couvert", "portee": {"debut": "2017-06-21", "fin": None},
     "preuve": "l'Assemblée nationale ne publie pas de comptes rendus de séance (Syceron) avant la XVe législature",
     "constate_le": "2026-09-12"},
    {"etat": "hors_couverture", "portee": {"debut": None, "fin": "2017-06-20"},
     "preuve": "l'Assemblée nationale ne publie pas de comptes rendus de séance (Syceron) avant la XVe législature",
     "constate_le": "2026-09-12"},
]
PANNE = {
    "etat": "non_collecte", "cause": "panne",
    "preuve": "archive Syceron de la XVe indisponible : transfert coupé", "constate_le": "2026-10-07",
}


# ---------------------------------------------------------------------------
# La fusion de la couverture
# ---------------------------------------------------------------------------

def test_un_run_qui_a_saute_la_liste_garde_le_dernier_constat_et_sa_date():
    bloc, non_tranchees = fusionner_couverture({"interventions": LUE}, {"interventions": [SAUTEE]})
    assert bloc["interventions"] == LUE
    assert bloc["interventions"][0]["constate_le"] == "2026-09-12"  # la fraîcheur, telle quelle
    assert non_tranchees == []


def test_non_collecte_seulement_si_aucun_run_ne_l_a_jamais_lue():
    bloc, _ = fusionner_couverture({"interventions": [dict(SAUTEE, constate_le="2026-10-01")]},
                                   {"interventions": [SAUTEE]})
    assert bloc["interventions"] == [SAUTEE]
    bloc, _ = fusionner_couverture({}, {"interventions": [SAUTEE]})
    assert bloc["interventions"] == [SAUTEE]


def test_une_panne_d_aujourd_hui_l_emporte_toujours_sur_un_couvert_d_hier():
    """La règle 2 de #602 tient pour tout ce qui a interrogé la source."""
    bloc, _ = fusionner_couverture({"interventions": LUE}, {"interventions": [PANNE]})
    assert bloc["interventions"] == [PANNE]


def test_une_lecture_neuve_remplace_une_lecture_ancienne():
    neuve = [dict(e, constate_le="2026-10-07") for e in LUE]
    bloc, _ = fusionner_couverture({"interventions": LUE}, {"interventions": neuve})
    assert bloc["interventions"] == neuve


def test_la_regle_ne_vaut_que_pour_la_liste_sautee():
    ancien = {"interventions": LUE, "votes": LUE}
    neuf = {"interventions": [SAUTEE], "votes": [dict(e, constate_le="2026-10-07") for e in LUE]}
    bloc, _ = fusionner_couverture(ancien, neuf)
    assert bloc["interventions"] == LUE
    assert bloc["votes"][0]["constate_le"] == "2026-10-07"


# ---------------------------------------------------------------------------
# Le roster ne déclare plus la collecte d'un candidat déclaré
# ---------------------------------------------------------------------------

def _args_roster_theme_seul(slug: str) -> argparse.Namespace:
    return argparse.Namespace(
        source="an", pivot_only=False, skip_existing=False,
        skip_interventions=False, interventions_theme_seul=True,
        skip_dossiers_legislatifs=True, budget_interventions_secondes=0,
        budget_collecte_secondes=0, skip_ue=True, pivot=False, no_merge=False,
        enrich_parltrack=False, candidats_declares=frozenset({slug}),
    )


def _fausse_collecte(monkeypatch) -> list[dict]:
    recus: list[dict] = []

    def collecte(chambre, slug, **kwargs):
        recus.append(kwargs)
        ecartees = sorted(
            liste for liste, ecarte in (
                ("interventions", kwargs.get("skip_interventions")),
                ("textes_portes", kwargs.get("skip_dossiers_legislatifs")),
            ) if ecarte
        )
        return {
            "slug": slug, "chambre": chambre, "identite": {"nom": slug},
            "mandats": [], "votes": [], "interventions": [], "amendements": [],
            "dossiers_legislatifs": [], "votes_source": None, "source": None,
            "meta": {"warnings": [], "synchro_sources": {}, "collecte_ecartee": ecartees},
        }

    monkeypatch.setattr("generate_all_profiles.build_profile", collecte)
    return recus


def test_le_roster_n_ecrit_pas_la_declaration_d_un_candidat_declare(monkeypatch, tmp_path):
    recus = _fausse_collecte(monkeypatch)
    generate_all_profiles.process_candidat(
        {"nom": "Jean-Luc Mélenchon", "slug": "jean-luc-melenchon",
         "statut": "roster_groupe", "acteur_ref": "PA2150"},
        _args_roster_theme_seul("jean-luc-melenchon"), tmp_path / "raw", tmp_path / "pivot",
    )
    assert recus and recus[0]["skip_interventions"] is True  # le refus de #657 tient
    brut = json.loads((tmp_path / "raw" / "jean-luc-melenchon.json").read_text(encoding="utf-8"))
    assert "collecte_ecartee" not in brut["meta"]


def test_un_membre_de_roster_ordinaire_declare_toujours_ce_qu_il_saute(monkeypatch, tmp_path):
    _fausse_collecte(monkeypatch)
    generate_all_profiles.process_candidat(
        {"nom": "Claire O'Petit", "slug": "claire-o-petit",
         "statut": "roster_groupe", "acteur_ref": "PA719364"},
        _args_roster_theme_seul("un-autre-slug"), tmp_path / "raw", tmp_path / "pivot",
    )
    brut = json.loads((tmp_path / "raw" / "claire-o-petit.json").read_text(encoding="utf-8"))
    assert brut["meta"]["collecte_ecartee"] == ["textes_portes"]


def test_sans_la_cle_la_fusion_garde_la_declaration_de_l_an():
    """L'ordre `--dirs an ue roster senat` : l'AN d'abord, le roster ensuite."""
    an = {"slug": "x", "meta": {"collecte_ecartee": [], "warnings": []}, "interventions": []}
    roster = {"slug": "x", "meta": {"warnings": []}, "interventions": []}
    fusionne = merge_raw_profile(an, roster)
    assert fusionne["meta"]["collecte_ecartee"] == []
