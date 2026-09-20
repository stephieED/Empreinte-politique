"""#514 — la collecte d'un candidat est bornée, et une troncature est déclarée.

## Ce que #529 a retiré de ce fichier, et pourquoi

Ce fichier rejouait l'archive dégradée du run 32421439590 (20/08/2026) contre
`candidate_profile._get_with_watchdog` : une doublure de transport qui servait
des timeouts et des 404 sur `www.nosdeputes.fr`, sous un `BASE_URLS` réduit à
un domaine. Toute cette machinerie visait UN chemin réseau, celui de
NosDéputés/NosSénateurs, et ce chemin est retiré (lot 5, #529). Sont partis
avec lui :

- **`WARNING_PREFIX_SOURCE_INJOIGNABLE` et les deux compteurs** qui
  l'alimentaient. Ils distinguaient « la source dit que ce slug n'existe pas »
  de « la source n'a rien dit ». L'identité ne part plus sur le réseau du tout
  — elle se résout dans l'archive AMO30 déjà en cache — donc il n'y a plus de
  silence à qualifier : une archive absente ou illisible **lève**, et
  l'exception est nommée dans `meta.warnings` par
  `WARNING_PREFIX_CHAMBRE_EN_ECHEC` (#488) ;
- **le statut `source_indisponible` distinct d'`introuvable`** sur ce chemin :
  il reste dans `process_candidat`, mais il se décide désormais sur un échec
  déclaré, pas sur un compteur ;
- **le pire cas structurel de la résolution d'identité** (2 formats ×
  3 tentatives × 26,5 s = 159 s), qui donnait au budget de 160 s sa valeur.
  Cette valeur reste celle du workflow, mais ce qu'elle borne a changé : elle
  ne couvre plus une cascade de requêtes par candidat.

Ce qui reste ici est ce que #514 a apporté et qui ne dépendait d'aucune
source : **la chaîne de budgets** (un budget enfant est épuisé par son parent,
et le message nomme le plafond réellement atteint), **la fabrique qui n'a pas
d'opinion sur les modes** — c'est un `and not skip_interventions` posé dans
`creer` qui a produit #514 —, **le budget de job qui rend la main en le
déclarant** plutôt que de se faire tuer par un `timeout-minutes`, et **le
garde-fou de ligne de commande** qui refuse un budget mort au lieu de le
neutraliser en silence.

Voir docs/decisions/retrait-nosdeputes-529.md.
"""

import argparse
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import budget_collecte
import candidate_profile
from budget_collecte import BudgetCollecte, creer
from generate_all_profiles import (
    process_candidat,
    valider_budgets,
)

#: La valeur retenue par le workflow pour `--budget-collecte-secondes`.
BUDGET_PAR_CANDIDAT = 160


class HorlogeFactice:
    """`time.monotonic` pilotée à la main : le budget est une question de temps
    mur, et un test qui dormirait réellement est un test qu'on désactive."""

    def __init__(self) -> None:
        self.maintenant = 1000.0

    def __call__(self) -> float:
        return self.maintenant

    def avancer(self, secondes: float) -> None:
        self.maintenant += secondes


@pytest.fixture
def horloge(monkeypatch):
    faux = HorlogeFactice()
    monkeypatch.setattr(budget_collecte.time, "monotonic", faux)
    monkeypatch.setattr(candidate_profile.time, "sleep", faux.avancer)
    return faux


# ---------------------------------------------------------------------------
# La chaîne de budgets
# ---------------------------------------------------------------------------

def test_un_budget_enfant_est_epuise_par_son_parent(horloge):
    """C'est ce qui permet au budget par candidat de borner la collecte
    d'interventions sans qu'une ligne de #500 ne change."""
    parent = BudgetCollecte(10, libelle="collecte")
    enfant = BudgetCollecte(1000, libelle="collecte d'interventions", parent=parent)

    with enfant.section("travail"):
        horloge.avancer(11)

    assert enfant.epuise(), "l'enfant doit voir l'épuisement du parent"
    assert parent.consomme() == pytest.approx(11), (
        "le parent doit être facturé du temps passé dans les sections de l'enfant"
    )


def test_le_message_nomme_le_budget_reellement_epuise(horloge):
    """Dire « plafond 1 000 s » alors que c'est un plafond de 10 s qui a rendu
    la main serait un chiffre juste attribué à la mauvaise population."""
    parent = BudgetCollecte(10, libelle="collecte du job")
    enfant = BudgetCollecte(1000, libelle="collecte d'interventions", parent=parent)

    with enfant.section("travail"):
        horloge.avancer(11)
    enfant.ignorer("document(s)", 3)

    message = enfant.message()
    assert "collecte du job" in message
    assert "plafond 10 s" in message
    assert "plafond 1000 s" not in message


def test_creer_ne_depend_que_de_la_valeur():
    """La fabrique refuse d'avoir une opinion sur les modes : c'est un
    `and not skip_interventions` posé là qui a produit #514."""
    assert creer(0, "collecte") is None
    assert creer(None, "collecte") is None
    budget = creer(120, "collecte")
    assert isinstance(budget, BudgetCollecte)
    assert budget.secondes == 120


# ---------------------------------------------------------------------------
# process_candidat : le budget de job rend la main au lieu d'être tué
# ---------------------------------------------------------------------------

def _args(**overrides) -> argparse.Namespace:
    base = dict(
        source="an",
        pivot_only=False,
        skip_existing=False,
        max_pages=None,
        skip_interventions=True,
        skip_dossiers_legislatifs=False,
        budget_interventions_secondes=0,
        budget_collecte_secondes=BUDGET_PAR_CANDIDAT,
        budget_job_secondes=0,
        skip_ue=True,
        pivot=False,
        no_merge=False,
        enrich_parltrack=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_le_budget_de_job_rend_la_main_sans_collecter(monkeypatch, tmp_path, horloge):
    """Un candidat que le budget de job n'atteint pas doit sortir DÉCLARÉ et
    sans qu'aucune collecte ne démarre — la différence avec un
    `timeout-minutes` atteint, où les candidats restants ne figurent nulle
    part.

    La doublure porte sur `build_profile` et non plus sur le transport HTTP
    (#529) : c'est le premier étage que `process_candidat` franchit, et le seul
    qu'il faut compter pour savoir si le candidat a été collecté.
    """
    collectes: list[str] = []

    def fausse_collecte(chambre, slug, budget_collecte=None, **kwargs):
        """Une collecte qui coûte 120 s et ne trouve aucune identité.

        Le temps est facturé DANS une section du budget de collecte du
        candidat, qui a le budget de job pour parent : c'est cette chaîne que
        le test éprouve, et la court-circuiter en faisant seulement avancer
        l'horloge ne prouverait rien.
        """
        collectes.append(slug)
        with budget_collecte.section("collecte factice"):
            horloge.avancer(120)
        return {
            "slug": slug,
            "chambre": chambre,
            "identite": None,
            "mandats": [],
            "votes": [],
            "interventions": [],
            "amendements": [],
            "dossiers_legislatifs": [],
            "votes_source": None,
            "source": None,
            "meta": {"warnings": [], "synchro_sources": {}},
        }

    monkeypatch.setattr("generate_all_profiles.build_profile", fausse_collecte)
    budget_job = BudgetCollecte(90, libelle="collecte du job")

    premier = process_candidat(
        {"nom": "Édouard Philippe", "slug": "edouard-philippe"},
        _args(),
        tmp_path / "raw",
        tmp_path / "pivot",
        budget_job=budget_job,
    )
    second = process_candidat(
        {"nom": "Jérôme Guedj", "slug": "jerome-guedj"},
        _args(),
        tmp_path / "raw",
        tmp_path / "pivot",
        budget_job=budget_job,
    )

    assert premier["statut"] == "introuvable", (
        "sans identité, le candidat est introuvable — un constat du référentiel AN"
    )
    assert second["statut"] == "budget_job_epuise"
    assert collectes == ["edouard-philippe"], (
        "un candidat non collecté ne doit déclencher aucune collecte"
    )
    assert budget_job.unites_ignorees().get("candidat(s) non collecté(s)") == 1


def test_process_candidat_signale_une_chambre_en_echec(monkeypatch, tmp_path, horloge):
    """L'héritier de « source injoignable » (#529). Une vraie panne — archive
    AMO30 absente ou illisible — lève, et cette exception doit ressortir
    NOMMÉE : c'est elle qui sépare « le référentiel ne connaît pas ce slug »
    de « le référentiel n'a pas pu être lu »."""
    def collecte_en_panne(chambre, slug, **kwargs):
        raise OSError("archive AMO30 illisible")

    monkeypatch.setattr("generate_all_profiles.build_profile", collecte_en_panne)

    resultat = process_candidat(
        {"nom": "Édouard Philippe", "slug": "edouard-philippe"},
        _args(),
        tmp_path / "raw",
        tmp_path / "pivot",
    )

    assert resultat["statut"] == "source_indisponible", (
        "« introuvable » affirmerait que le référentiel ne connaît pas ce slug, "
        "alors qu'il n'a pas pu être lu"
    )


# ---------------------------------------------------------------------------
# Le garde-fou de ligne de commande
# ---------------------------------------------------------------------------

def test_un_budget_mort_est_refuse_et_non_neutralise():
    """La moitié visible de #514. `--budget-interventions-secondes` sous
    `--skip-interventions` était accepté puis rendu `None` en silence, ce qui
    donnait à `extract-senat` l'apparence d'une protection qu'il n'avait pas.

    Le refuser plutôt que le neutraliser oblige à choisir : soit on collecte
    des interventions et le budget vit, soit on ne collecte pas et il n'a rien
    à faire là.
    """
    args = _args(budget_interventions_secondes=240, skip_interventions=True)

    with pytest.raises(SystemExit) as echec:
        valider_budgets(args)

    assert "--budget-collecte-secondes" in str(echec.value), (
        "le refus doit indiquer le budget qui, lui, borne quelque chose"
    )


def test_une_collecte_sans_budget_declare_est_signalee(capsys):
    """L'autre moitié : ne rien dire. Un avertissement et non une erreur —
    rendre l'option obligatoire casserait les commandes locales de README.md, et
    un garde-fou qu'on désactive pour travailler ne garde rien (#460). Le garde
    dur est dans tests/test_ci_budget_par_job.py."""
    valider_budgets(_args(budget_collecte_secondes=None))

    sortie = capsys.readouterr().out
    assert "sans --budget-collecte-secondes" in sortie
    assert "--budget-collecte-secondes 0" in sortie, (
        "l'avertissement doit dire comment déclarer l'absence de budget"
    )


def test_un_zero_explicite_ne_declenche_aucun_avertissement(capsys):
    """`--budget-collecte-secondes 0` est une décision, pas un oubli : la
    distinction entre les deux est tout l'objet du garde-fou."""
    valider_budgets(_args(budget_collecte_secondes=0))

    assert "budget-collecte-secondes" not in capsys.readouterr().out


def test_le_warning_de_source_injoignable_a_disparu():
    """Le verrou du retrait. Un warning qui ne peut plus se déclencher est un
    garde-fou désarmé qu'on croit armé : le retirer était le point, le voir
    revenir doit échouer bruyamment."""
    for nom in (
        "WARNING_PREFIX_SOURCE_INJOIGNABLE",
        "compteur_requetes_sans_reponse",
        "compteur_appels_nosdeputes",
    ):
        assert not hasattr(candidate_profile, nom), (
            f"`candidate_profile.{nom}` est de retour alors qu'aucune requête "
            "ne peut plus l'alimenter (#529). Voir "
            "docs/decisions/retrait-nosdeputes-529.md."
        )
