"""#836 — une lignée n'est pas la somme de ses maillons.

Trois régimes, et c'est toute la difficulté : ce qui s'unit sur une clé, ce qui
se recalcule depuis les profils, et ce qui ne s'agrège pas du tout.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lignee_profile import composer_lignee, ordonner_maillons  # noqa: E402
from schema_lignee import validate_profil_lignee  # noqa: E402


def _fiche(gid, leg, membres, succede_a=(), **extra):
    f = {
        "groupe_id": gid, "groupe_sigle": gid.split(":")[1], "groupe_nom": gid,
        "legislature": leg,
        "periode": {"debut": f"20{leg}-06-01", "fin": None},
        "membres": [
            {"membre_id": m, "nom": m.title(),
             "debut_dans_groupe": f"20{leg}-06-29", "fin_dans_groupe": None}
            for m in membres
        ],
        "succede_a": [{"groupe_id": g} for g in succede_a],
        "cohesion_votes": [], "mandats_agreges": [], "sources": [],
        "position_politique": {"valeur": f"position-{leg}"},
    }
    f.update(extra)
    return f


# ---------------------------------------------------------------------------
# L'ordre vient de `succede_a`, pas des dates
# ---------------------------------------------------------------------------

def test_l_ordre_des_maillons_se_lit_sur_succede_a():
    fiches = {
        "AN:SOC:17": _fiche("AN:SOC:17", "17", [], ["AN:SOC:16"]),
        "AN:NG:15": _fiche("AN:NG:15", "15", []),
        "AN:SOC:16": _fiche("AN:SOC:16", "16", [], ["AN:SOC:15"]),
        "AN:SOC:15": _fiche("AN:SOC:15", "15", [], ["AN:NG:15"]),
    }
    assert ordonner_maillons(fiches, fiches) == [
        "AN:NG:15", "AN:SOC:15", "AN:SOC:16", "AN:SOC:17"
    ]


def test_un_cycle_est_refuse_plutot_que_parcouru():
    """Mieux vaut une lignée manquante qu'une lignée qui boucle en silence."""
    fiches = {
        "AN:A:16": _fiche("AN:A:16", "16", [], ["AN:B:17"]),
        "AN:B:17": _fiche("AN:B:17", "17", [], ["AN:A:16"]),
    }
    with pytest.raises(ValueError, match="cycle"):
        ordonner_maillons(fiches, fiches)


# ---------------------------------------------------------------------------
# Ce qui s'unit
# ---------------------------------------------------------------------------

def test_un_membre_present_sous_trois_maillons_ne_compte_qu_une_fois():
    """170 entrées pour 96 personnes, sur la lignée socialiste réelle."""
    a = _fiche("AN:NG:15", "15", ["alice", "bob"])
    b = _fiche("AN:SOC:16", "16", ["alice", "carole"], ["AN:NG:15"])
    p = composer_lignee("AN:LIGNEE:SOC", "Socialistes", "AN", [a, b])
    assert [m["membre_id"] for m in p["membres"]] == ["alice", "bob", "carole"]
    assert p["effectif"]["cumul_historique"] == 3
    alice = next(m for m in p["membres"] if m["membre_id"] == "alice")
    assert alice["maillons"] == ["AN:NG:15", "AN:SOC:16"]


def test_les_scrutins_de_cohesion_s_unissent_sur_leur_identifiant():
    """Les maillons ne sont PAS disjoints : 4 104 doublons mesurés sur la
    lignée socialiste, 20 524 entrées pour 16 420 scrutins."""
    a = _fiche("AN:NG:15", "15", [], cohesion_votes=[{"scrutin_id": "an:15:1"},
                                                     {"scrutin_id": "an:15:2"}])
    b = _fiche("AN:SOC:16", "16", [], ["AN:NG:15"],
               cohesion_votes=[{"scrutin_id": "an:15:2"}, {"scrutin_id": "an:16:9"}])
    p = composer_lignee("AN:LIGNEE:SOC", "Socialistes", "AN", [a, b])
    assert len(p["cohesion_votes"]) == 3


def test_un_scrutin_sans_identifiant_est_garde_sans_etre_dedoublonne():
    """On ne sait pas si c'est le même : le taire serait pire que le garder."""
    a = _fiche("AN:NG:15", "15", [], cohesion_votes=[{"scrutin_id": None}])
    b = _fiche("AN:SOC:16", "16", [], ["AN:NG:15"], cohesion_votes=[{"scrutin_id": None}])
    assert len(composer_lignee("X", "X", "AN", [a, b])["cohesion_votes"]) == 2


def test_une_appartenance_ouverte_l_emporte_sur_une_fin_anterieure():
    a = _fiche("AN:NG:15", "15", ["alice"])
    a["membres"][0]["fin_dans_groupe"] = "2018-09-11"
    b = _fiche("AN:SOC:16", "16", ["alice"], ["AN:NG:15"])
    p = composer_lignee("X", "X", "AN", [a, b])
    assert p["membres"][0]["fin_dans_lignee"] is None


def test_la_periode_de_la_lignee_va_de_la_premiere_borne_a_la_derniere():
    a = _fiche("AN:NG:15", "15", [])
    a["periode"] = {"debut": "2017-06-27", "fin": "2018-09-11"}
    b = _fiche("AN:SOC:16", "16", [], ["AN:NG:15"])
    b["periode"] = {"debut": "2022-06-29", "fin": "2024-06-09"}
    p = composer_lignee("X", "X", "AN", [a, b])
    assert p["periode"] == {"debut": "2017-06-27", "fin": "2024-06-09"}


# ---------------------------------------------------------------------------
# Ce qui ne s'agrège PAS
# ---------------------------------------------------------------------------

def test_la_position_politique_est_recopiee_par_maillon_jamais_reunie():
    """L'Assemblée qualifie ses groupes PAR LÉGISLATURE (#686). Les réunir en
    une seule valeur produirait un jugement que personne n'a porté (§2 règle 1).
    """
    a = _fiche("AN:NG:15", "15", [])
    b = _fiche("AN:SOC:16", "16", [], ["AN:NG:15"])
    p = composer_lignee("X", "X", "AN", [a, b])
    assert [m["position_politique"]["valeur"] for m in p["maillons"]] == [
        "position-15", "position-16"
    ]
    assert "position_politique" not in p


def test_les_deux_agregats_qui_ne_se_somment_pas_restent_vides_sans_recalcul():
    """Vides plutôt que faux : une somme de maillons compterait un amendement
    cosigné autant de fois qu'il a de signataires répartis sur la lignée."""
    a = _fiche("AN:NG:15", "15", [], amendements_agreges={"nb_amendements": 500})
    b = _fiche("AN:SOC:16", "16", [], ["AN:NG:15"],
               amendements_agreges={"nb_amendements": 700})
    p = composer_lignee("X", "X", "AN", [a, b])
    assert p["amendements_agreges"] == {}
    assert p["tags_thematiques_agreges"] == []


# ---------------------------------------------------------------------------
# Le schéma
# ---------------------------------------------------------------------------

def test_une_lignee_sans_maillon_est_refusee():
    p = composer_lignee("X", "X", "AN", [])
    assert any("ne décrit rien" in e for e in validate_profil_lignee(p))


def test_une_lignee_d_un_seul_maillon_est_valide():
    """Un groupe sans prédécesseur ni successeur en est une à un maillon."""
    p = composer_lignee("AN:LIGNEE:EDS", "EDS", "AN", [_fiche("AN:EDS:15", "15", ["a"])])
    assert validate_profil_lignee(p) == []
