"""Les budgets que chaque gouvernement a fait voter (`pivot_data/budgets_gouvernements.json`, #1053).

Les quatre fixtures de `tests/fixtures/budgets_gouvernements/` sont des coupes
des fichiers produits le 13/10/2026 par les deux collectes et par le dépôt :
mêmes clés, mêmes libellés, mêmes montants, réduits aux années et aux
gouvernements dont les tests ont besoin. Le fichier de 2024 y est laissé SANS
mission, comme l'était le fichier publié avant que la collecte ne la garde.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import budgets_gouvernements as bg  # noqa: E402
import finances_etat as fe  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "budgets_gouvernements"


def charge(nom: str) -> dict:
    return json.loads((FIXTURES / nom).read_text(encoding="utf-8"))


def texte_fixture(nom: str) -> str:
    """Un fichier de la source, copié dans les fixtures de la collecte."""
    return fe.decoder((RACINE / "tests" / "fixtures" / "finances_etat" / nom).read_bytes())


@pytest.fixture(scope="module")
def document() -> dict:
    return bg.composer(charge("gouvernements_reels.json"), charge("textes_promulgues.json"),
                       charge("finances_etat.json"), charge("finances_sociales.json"))


def exercices(document: dict, ident: str) -> dict:
    return {e["exercice"]: e for e in document["gouvernements"]["gouvernement:" + ident]["exercices"]}


def test_une_annee_revient_au_gouvernement_qui_a_fait_promulguer_sa_loi(document):
    assert list(exercices(document, "BORNE")) == ["2023", "2024"]
    assert exercices(document, "BORNE")["2024"]["loi_de_finances_promulguee_le"] == "2023-12-30"
    assert list(exercices(document, "LECORNU_II")) == ["2026"]


def test_un_gouvernement_sans_loi_de_finances_n_a_aucun_budget(document):
    """Attal a exécuté le budget 2024, voté sous Borne : rien n'est réparti."""
    assert document["gouvernements"]["gouvernement:ATTAL"] == {"exercices": []}


def test_une_loi_rectificative_ne_rattache_aucune_annee():
    dates = bg.exercices_votes(charge("textes_promulgues.json"))
    assert dates["2023"] == "2022-12-31" and dates["2025"] == "2025-02-16"
    assert all(len(an) == 4 for an in dates)


def test_le_budget_de_2023_reprend_les_montants_de_la_source(document):
    etat = exercices(document, "BORNE")["2023"]["budget_de_l_etat"]
    assert etat["dernier_mois"] == "2023-12" and etat["exercice_complet"] is True
    assert etat["solde"] == -172972201009.24
    assert etat["depenses_nettes"] == 454565410321.53
    assert {r["ligne"]: r["montant"] for r in etat["recettes"]}["Impôt sur le revenu"] == 88589440367.92


def test_les_missions_et_les_degrevements_locaux_font_les_depenses_nettes(document):
    """C'est ce qui explique l'écart de 5 Md€ entre les deux fichiers du budget."""
    etat = exercices(document, "BORNE")["2023"]["budget_de_l_etat"]
    missions = {m["mission"]: m["montant"] for m in etat["missions"]}
    assert "Remboursements et dégrèvements" not in missions
    assert len(missions) == 32 and round(missions["Enseignement scolaire"] / 1e9, 1) == 82.0
    ecart = etat["depenses_nettes"] - sum(missions.values()) - etat["degrevements_d_impots_locaux"]
    assert abs(ecart) < 1e6


def test_sans_mission_dans_la_collecte_la_partie_est_declaree_absente(document):
    etat = exercices(document, "BORNE")["2024"]["budget_de_l_etat"]
    assert etat["missions"] is None and "raison" in etat["missions_non_resolu"]
    assert etat["solde"] == -155929972365.41, "le reste de l'exercice est publié"


def test_l_exercice_en_cours_s_arrete_au_dernier_mois_publie(document):
    etat = exercices(document, "LECORNU_II")["2026"]["budget_de_l_etat"]
    assert etat["dernier_mois"] == "2026-08" and etat["exercice_complet"] is False
    assert etat["missions"] is None


def test_les_caisses_de_2023(document):
    caisses = exercices(document, "BORNE")["2023"]["securite_sociale"]
    assert caisses["statut"] == "SD" and caisses["ressources_total"] == 722838.32
    origines = {r["origine"]: r["montant"] for r in caisses["ressources"]}
    assert origines["Cotisations sociales d'employeurs"] == 280242.62
    assert abs(sum(origines.values()) - caisses["ressources_total"]) < 2
    regimes = {p["regime"]: p["montant"] for p in caisses["prestations"]}
    assert regimes["Caisse nationale d’assurance vieillesse"] == 151825.8
    assert len(regimes) == 19
    assert round(sum(regimes.values()) + caisses["autres_emplois"], 2) == caisses["emplois_total"]


def test_une_annee_sans_prestations_par_regime_est_declaree_absente(document):
    entree = exercices(document, "BORNE")["2024"]
    assert entree["securite_sociale"] is None
    assert "raison" in entree["securite_sociale_non_resolu"]


def test_la_collecte_garde_la_mission_la_ou_la_source_la_donne():
    texte = ("Mission;Programme;Titre;LFI;Depenses_constatees\n"
             "Justice;Justice judiciaire - 166;Titre 2 - Dépenses de personnel;10;11\n"
             "Justice;Justice judiciaire - 166;Autres titres - Autres dépenses;5;4\n")
    vote, realise = fe.lire_etat_cp(texte, {"166": ("10", "Justice")})
    assert realise == [{"programme": "166", "ministere_code": "10", "ministere": "Justice",
                        "cp": 15.0, "mission": "Justice",
                        "libelle_programme": "Justice judiciaire"}]
    assert vote[0]["mission"] == "Justice"


def test_un_programme_sous_deux_missions_fait_echouer():
    texte = ("Mission;Programme;Titre;LFI;Depenses_constatees\n"
             "Justice;Justice judiciaire - 166;T;1;1\nSanté;Justice judiciaire - 166;T;1;1\n")
    with pytest.raises(fe.FinancesIndisponibles, match="deux missions"):
        fe.lire_etat_cp(texte, {})


def test_un_exercice_publie_sans_mission_se_relit_une_fois():
    from datetime import date
    bloc = {"vote": {"programmes": [{"programme": "101", "cp": 1.0}]},
            "realise": {"programmes": [{"programme": "101", "cp": 1.0}]}}
    assert fe.est_fige(bloc, 2023, date(2026, 10, 13)) is False
    bloc["realise"]["programmes"][0]["mission"] = "Justice"
    assert fe.est_fige(bloc, 2023, date(2026, 10, 13)) is False, "sans le nom du programme"
    bloc["realise"]["programmes"][0]["libelle_programme"] = "Justice judiciaire"
    assert fe.est_fige(bloc, 2023, date(2026, 10, 13)) is True


def test_la_collecte_garde_le_nom_du_programme_tel_que_la_source_l_ecrit():
    """La ligne de `Annexe1-Etat_CP-2025.csv`, copiée : le nom est avant « - 105 »."""
    _vote, realise = fe.lire_etat_cp(texte_fixture("exec2025.csv"), {})
    noms = {p["programme"]: p["libelle_programme"] for p in realise}
    assert noms["105"] == "Action de la France en Europe et dans le monde"
    assert noms["185"] == "Diplomatie culturelle et d'influence"


def test_un_programme_nomme_de_deux_facons_n_a_pas_de_nom():
    texte = ("Mission;Programme;Titre;LFI;Depenses_constatees\n"
             "Justice;Justice judiciaire - 166;T;1;1\nJustice;Justice - 166;T;1;1\n")
    _vote, realise = fe.lire_etat_cp(texte, {})
    assert realise[0]["libelle_programme"] is None


def test_une_mission_publie_ses_programmes_et_retombe_sur_leur_somme(document):
    for gouv in document["gouvernements"].values():
        for entree in gouv["exercices"]:
            for mission in ((entree["budget_de_l_etat"] or {}).get("missions") or []):
                assert mission["programmes"], mission["mission"]
                assert round(sum(p["montant"] for p in mission["programmes"]), 2) == mission["montant"]
                assert {"programme", "libelle", "montant"} == set(mission["programmes"][0])


def test_un_nom_de_programme_absent_de_la_collecte_est_null(document):
    """La coupe de 2023 a été écrite avant que la collecte ne garde le nom."""
    etat = exercices(document, "BORNE")["2023"]["budget_de_l_etat"]
    assert all(p["libelle"] is None for m in etat["missions"] for p in m["programmes"])


def test_le_nom_du_programme_va_de_la_collecte_a_la_mission():
    _vote, realise = fe.lire_etat_cp(texte_fixture("exec2025.csv"), {})
    finances = {"grandes_lignes": {"lignes": [
        {"ligne": nom, "mensuel": {"2025-12": 1.0}}
        for nom in (*bg.RECETTES, bg.TOTAL_RECETTES, bg.TOTAL_DEPENSES, *bg.REVERSE,
                    *bg.COMPTES_A_PART, bg.SOLDE, bg.DEGREVEMENTS_LOCAUX)]},
        "exercices": {"2025": {"realise": {"programmes": realise}}}}
    etat = bg.budget_de_l_etat(finances, "2025")
    (action_exterieure,) = [m for m in etat["missions"] if m["mission"] == "Action extérieure de l'État"]
    assert {p["programme"]: p["libelle"] for p in action_exterieure["programmes"]}["105"] == (
        "Action de la France en Europe et dans le monde")


def test_un_programme_a_zero_sans_mission_n_empeche_pas_la_repartition():
    """#1302 : en 2015, dix-neuf programmes à 0 € manquent au fichier par
    mission. Ils n'ajoutent rien ; un programme qui dépense, lui, bloque."""
    finances = charge("finances_etat.json")
    programmes = finances["exercices"]["2024"]["realise"]["programmes"]
    for p in programmes:
        p["mission"] = "Mission"
    programmes.append({"programme": "401", "cp": 0.0})

    assert bg.budget_de_l_etat(finances, "2024")["missions"] is not None

    programmes[-1]["cp"] = 1.0
    etat = bg.budget_de_l_etat(finances, "2024")
    assert etat["missions"] is None
    assert etat["missions_non_resolu"]["raison"] == (
        "un programme qui dépense n'a pas de mission dans la source")
