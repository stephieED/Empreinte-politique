"""#498 — la collecte d'interventions se borne elle-même, et le dit.

Ce que ces tests protègent, et qui n'est pas le simple fait de « s'arrêter à
temps » : **ce qui a été collecté avant l'arrêt doit être conservé, et l'arrêt
doit laisser une trace exploitable**. C'est exactement ce que le
`timeout-minutes` du job ne sait pas faire — sur les 12 shards `extract-an` tués
des runs 32302557156 et 32379928098, le log ne dit que
`##[error]The operation was canceled` et le step de publication rapporte
« 0 profil(s) écrits par ce job ».

Aucun réseau, aucune lecture du corpus : les index Syceron/questions et les
détails d'intervention sont des doublures, et le temps est piloté par une
horloge factice — un test qui dormirait réellement 240 s serait un test qu'on
finit par désactiver.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import budget_collecte
from budget_collecte import BudgetCollecte
from candidate_profile import (
    WARNING_PREFIX_BUDGET_INTERVENTIONS,
    build_profile,
    fetch_interventions_syceron,
    fetch_questions_officielles,
)


class HorlogeFactice:
    """`time.monotonic` pilotée à la main : le budget est une question de temps
    mur, et un test ne doit pas payer ce temps-là pour l'éprouver."""

    def __init__(self) -> None:
        self.maintenant = 1000.0

    def __call__(self) -> float:
        return self.maintenant

    def avancer(self, secondes: float) -> None:
        self.maintenant += secondes


@pytest.fixture(autouse=True)
def cache_syceron_isole(tmp_path, monkeypatch):
    """Le cache Syceron de CE test, jamais celui du poste (#721).

    `fetch_interventions_syceron` passe par `_interventions_syceron_acteur`, qui
    LIT LE CACHE avant d'appeler le constructeur. Patcher le constructeur — ce
    que ces tests font — ne suffit donc pas : sur une machine ayant déjà
    collecté, la lecture réussissait et servait 688 interventions réelles là où
    la fixture en attend une. Le répertoire courant porte le cache parce que les
    constantes sont relatives ; le déplacer suffit à les emmener toutes.
    """
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def horloge(monkeypatch):
    faux = HorlogeFactice()
    monkeypatch.setattr(budget_collecte.time, "monotonic", faux)
    return faux


# ---------------------------------------------------------------------------
# La classe elle-même
# ---------------------------------------------------------------------------

def test_un_budget_nul_ou_negatif_est_refuse():
    """Pas de désactivation silencieuse : 0 s n'est pas « pas de budget »."""
    for valeur in (0, -1, -0.5):
        with pytest.raises(ValueError, match="budget"):
            BudgetCollecte(valeur, libelle="collecte d'interventions")


def test_le_temps_ne_court_que_dans_une_section(horloge):
    budget = BudgetCollecte(10, libelle="collecte d'interventions")

    horloge.avancer(30)  # travail hors collecte (votes, amendements, textes)
    assert budget.consomme() == 0
    assert not budget.epuise()

    with budget.section("recherche"):
        horloge.avancer(4)
    assert budget.consomme() == pytest.approx(4)
    assert budget.restant() == pytest.approx(6)
    assert not budget.epuise()


def test_le_budget_s_epuise_pendant_la_section_pas_seulement_a_sa_sortie(horloge):
    """Sinon une seule section très longue ne serait jamais vue comme épuisée
    depuis l'intérieur — or c'est précisément là que les gardes sont posées."""
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    with budget.section("détails"):
        horloge.avancer(11)
        assert budget.epuise()
        assert budget.restant() == 0


def test_les_sections_imbriquees_ne_facturent_pas_deux_fois(horloge):
    budget = BudgetCollecte(100, libelle="collecte d'interventions")
    with budget.section("externe"):
        with budget.section("interne"):
            horloge.avancer(5)
        horloge.avancer(5)
    assert budget.consomme() == pytest.approx(10)


def test_message_est_none_tant_que_rien_n_a_ete_ignore(horloge):
    """Un budget serré mais suffisant n'a rien à signaler : ce qui doit se voir,
    c'est une collecte incomplète, pas un plafond frôlé."""
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    with budget.section("recherche"):
        horloge.avancer(9.9)
    assert budget.message() is None


def test_message_nomme_les_unites_non_collectees(horloge):
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    with budget.section("détails"):
        horloge.avancer(12)
        budget.ignorer("document(s) d'intervention NosDéputés", 143)
        budget.ignorer("législature(s) de questions officielles", 4)

    message = budget.message()
    assert "143 document(s) d'intervention NosDéputés" in message  # libellé conservé : le corpus en porte
    assert "4 législature(s) de questions officielles" in message
    assert "12 s" in message and "10 s" in message


def test_annoncer_troncature_emet_une_annotation_en_ci(horloge, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    with budget.section("détails"):
        horloge.avancer(11)
        budget.ignorer("document(s) d'intervention NosDéputés", 7)

    message = budget_collecte.annoncer_troncature(budget, "deputes/jean-dupont")
    sortie = capsys.readouterr()
    assert message is not None
    assert "::warning::deputes/jean-dupont" in sortie.out
    assert "7 document(s)" in sortie.err


def test_annoncer_troncature_reste_muette_sans_troncature(horloge, capsys):
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    assert budget_collecte.annoncer_troncature(budget, "deputes/jean-dupont") is None
    assert budget_collecte.annoncer_troncature(None, "deputes/jean-dupont") is None
    assert capsys.readouterr().out == ""


# ---------------------------------------------------------------------------
# Les points de collecte, un par un
# ---------------------------------------------------------------------------

def test_syceron_s_arrete_entre_deux_legislatures_et_garde_les_premieres(horloge):
    """La législature en cours n'est jamais coupée en son milieu : son index
    n'est mis en cache qu'une fois lue entièrement, et un index partiel ferait
    passer une collecte incomplète pour une collecte faite."""
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    lues: list[str] = []

    def faux_index(legislature, **_):
        lues.append(legislature)
        horloge.avancer(6)  # chaque archive coûte 6 s : la 2e épuise les 10 s
        return {"PA1567": [{"id": f"syceron_{legislature}", "date": "2025-01-01"}]}

    with patch("candidate_profile.SYCERON_AVAILABLE_LEGISLATURES", {"15", "16", "17"}), \
         patch("candidate_profile._build_acteur_interventions_syceron_index", side_effect=faux_index), \
         budget.section("débats Syceron"):
        interventions = fetch_interventions_syceron(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1567", budget
        )

    # Parcours du plus récent au plus ancien : 17 puis 16, et 15 abandonnée.
    assert lues == ["17", "16"]
    assert len(interventions) == 2
    assert budget.unites_ignorees() == {"législature(s) de débats Syceron": 1}


def test_questions_officielles_s_arretent_et_comptent_les_legislatures_perdues(horloge):
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    lues: list[str] = []

    def faux_index(legislature, **_):
        lues.append(legislature)
        horloge.avancer(11)  # une seule archive suffit à épuiser le budget
        return {"PA1567": [{"uid": f"Q{legislature}", "sous_type": "QE", "date": "2025-01-01"}]}

    with patch("candidate_profile.AN_QUESTIONS_PATH", {"17": {}, "16": {}, "15": {}}), \
         patch("candidate_profile._build_acteur_questions_index", side_effect=faux_index), \
         budget.section("questions officielles"):
        questions = fetch_questions_officielles(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1567", budget
        )

    assert lues == ["17"]
    assert len(questions) == 1
    assert budget.unites_ignorees() == {"législature(s) de questions officielles": 2}


# `test_les_details_nosdeputes_s_arretent_document_par_document` est RETIRÉ
# (#529, lot 5). Il verrouillait la granularité la plus fine du budget : un
# document d'intervention à la fois, parce que sur une source dégradée un
# document coûtait jusqu'à 45 s (read timeout 15 s × 3 tentatives) et qu'il y
# en avait jusqu'à ~250 par candidat. Cette collecte-là — `_extract_search_results`
# et les requêtes de détail qu'elle enchaînait — n'existe plus.
#
# Les deux granularités qui restent sont testées juste au-dessus et en dessous :
# la législature de débats Syceron et la législature de questions officielles.
# Ce sont désormais les seules unités que la phase d'interventions consomme,
# et ce sont aussi les seules qui coûtaient des dizaines de secondes.


def test_sans_budget_la_collecte_reste_complete(horloge):
    """Le budget est optionnel : `None` doit rendre exactement le comportement
    d'avant #498, sinon le mode par défaut et les appels locaux changeraient de
    sémantique sans que personne l'ait demandé."""
    lues: list[str] = []

    def faux_index(legislature, **_):
        lues.append(legislature)
        horloge.avancer(10_000)
        return {}

    with patch("candidate_profile.SYCERON_AVAILABLE_LEGISLATURES", {"15", "16", "17"}), \
         patch("candidate_profile._build_acteur_interventions_syceron_index", side_effect=faux_index):
        fetch_interventions_syceron("https://www.assemblee-nationale.fr/dyn/deputes/PA1567", None)

    assert lues == ["17", "16", "15"]


# ---------------------------------------------------------------------------
# Bout en bout : le profil est rendu, tronqué et déclaré
# ---------------------------------------------------------------------------

def _profil(horloge, budget, cout_syceron, **kwargs):
    """Profil de député dont la seule source coûteuse est Syceron."""

    def faux_index(legislature, **_):
        horloge.avancer(cout_syceron)
        return {"PA1567": [{"id": f"syceron_{legislature}", "date": "2025-01-01", "sujet": "S"}]}

    identite_an = {
        "nom_complet": "Jean Dupont",
        "mandat_debut": "2022-06-22",
        "groupe_sigle": "GRP",
    }

    with (
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=(identite_an, "PA1567")),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.SYCERON_AVAILABLE_LEGISLATURES", {"15", "16", "17"}),
        patch("candidate_profile._build_acteur_interventions_syceron_index", side_effect=faux_index),
        patch("candidate_profile.AN_QUESTIONS_PATH", {"17": {}}),
        patch("candidate_profile._build_acteur_questions_index", return_value={}),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        return build_profile("deputes", "jean-dupont", budget_interventions=budget, **kwargs)


def test_un_profil_tronque_est_rendu_avec_ce_qui_a_ete_collecte(horloge):
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    profil = _profil(horloge, budget, cout_syceron=6)

    # Deux législatures lues avant épuisement, la troisième abandonnée — et un
    # profil rendu, donc écrit puis publié, là où le timeout de job n'en rendait
    # aucun.
    assert len(profil["interventions"]) == 2
    tronque = [
        w for w in profil["meta"]["warnings"]
        if w.startswith(WARNING_PREFIX_BUDGET_INTERVENTIONS)
    ]
    assert len(tronque) == 1
    assert "1 législature(s) de débats Syceron" in tronque[0]


def test_un_profil_complet_ne_porte_aucun_avertissement_de_budget(horloge):
    budget = BudgetCollecte(100, libelle="collecte d'interventions")
    profil = _profil(horloge, budget, cout_syceron=1)

    assert len(profil["interventions"]) == 3
    assert not any(
        w.startswith(WARNING_PREFIX_BUDGET_INTERVENTIONS) for w in profil["meta"]["warnings"]
    )


def test_skip_interventions_n_est_jamais_facture_au_budget(horloge):
    """`--skip-interventions` ne collecte rien : il ne doit rien consommer non
    plus, sinon le budget d'un mode se ferait manger par l'autre."""
    budget = BudgetCollecte(10, libelle="collecte d'interventions")
    profil = _profil(horloge, budget, cout_syceron=10_000, skip_interventions=True)

    assert profil["interventions"] == []
    assert budget.unites_ignorees() == {}
    assert not any(
        w.startswith(WARNING_PREFIX_BUDGET_INTERVENTIONS) for w in profil["meta"]["warnings"]
    )
