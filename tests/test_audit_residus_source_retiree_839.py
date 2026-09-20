"""Tests de `src/audit_residus_source_retiree.py` (#839, lot C).

Ce que les tests protègent :

1. **La distinction qui rend la clause décidable** — « une donnée publiée retient
   l'attribution » n'est pas « le marqueur la retient ». §7 fait de
   `meta.licence_donnees` un champ dérivé dont la condition de retrait court
   d'elle-même ; encore faut-il savoir, profil par profil, ce qui la retient.
2. **La licence est recomposée par la fonction de production**
   (`licences.licences_du_profil`), jamais par une règle recopiée ici.
3. **Rien n'est modifié.** Le nettoyage est simulé, sur des copies de surface —
   un `deepcopy` recopiait jusqu'à 8 Mio par profil et l'audit ne rendait pas la
   main.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_residus_source_retiree import (  # noqa: E402
    PLUS_DUE,
    RETENUE_PAR_LE_MARQUEUR,
    RETENUE_PAR_UNE_DONNEE,
    etat_de_la_clause,
    residus_du_profil,
    verifier_entrees_sans_date,
)
from licences import LICENCE_REGARDS_CITOYENS, licences_du_profil  # noqa: E402


def _heritee(identifiant, date, texte, url="https://www.nosdeputes.fr/16/seance/1247#inter_x"):
    return {"intervention_id": identifiant, "date": date, "texte": texte, "source_url": url}


def _syceron(date, texte):
    return {"intervention_id": f"syceron_X_{date}", "date": date, "texte": texte}


def _profil(**champs):
    base = {"sources": [], "mandats": [], "interventions": [], "meta": {"provenance": "candidat_declare"}}
    base.update(champs)
    return base


# ---------------------------------------------------------------------------
# L'état de la clause après nettoyage simulé
# ---------------------------------------------------------------------------

def test_une_intervention_sans_jumelle_retient_la_clause_par_la_donnee():
    """Elle survit à la purge, et son URL suffit à devoir l'attribution."""
    profil = _profil(
        sources=[{"type": "nosdeputes", "url": "https://www.nosdeputes.fr/x"}],
        interventions=[_heritee(305964, "2018-07-09", "<p>Un propos sans jumelle.</p>")],
    )
    assert etat_de_la_clause(profil) == RETENUE_PAR_UNE_DONNEE


def test_quand_la_purge_emporte_la_derniere_donnee_seul_le_marqueur_retient():
    """C'est le cas de 472 profils sur 475 : la clause ne tient plus que par
    l'entrée `sources[]`."""
    profil = _profil(
        sources=[{"type": "nosdeputes", "url": "https://www.nosdeputes.fr/x"}],
        interventions=[
            _heritee(249506, "2023-05-02", "<p>Les Mahorais ont manifesté !</p>"),
            _syceron("2023-05-02", "Les Mahorais ont manifesté !"),
        ],
    )
    assert etat_de_la_clause(profil) == RETENUE_PAR_LE_MARQUEUR


def test_l_hypothese_haute_retire_aussi_les_orphelines():
    """Mesuré le 12/09/2026 : sous cette hypothèse, **aucun** profil du corpus
    ne porte plus de donnée de la source retirée."""
    profil = _profil(
        sources=[{"type": "nosdeputes", "url": "https://www.nosdeputes.fr/x"}],
        interventions=[_heritee(305964, "2018-07-09", "<p>Un propos sans jumelle.</p>")],
    )
    assert etat_de_la_clause(profil, retirer_orphelines=True) == RETENUE_PAR_LE_MARQUEUR


def test_sans_marqueur_ni_donnee_la_clause_n_est_plus_due():
    profil = _profil(sources=[{"type": "assemblee_nationale", "url": "https://an.fr"}])
    assert etat_de_la_clause(profil) == PLUS_DUE


def test_la_licence_est_recomposee_par_la_fonction_de_production():
    """Aucune règle de licence n'est recopiée dans l'audit : c'est
    `licences_du_profil` qui tranche, et le test le vérifie des deux côtés."""
    profil = _profil(sources=[{"type": "nossenateurs", "url": "https://archive.nossenateurs.fr/x"}])
    assert LICENCE_REGARDS_CITOYENS in licences_du_profil(profil)
    assert etat_de_la_clause(profil) == RETENUE_PAR_LE_MARQUEUR


# ---------------------------------------------------------------------------
# Les entrées sans date
# ---------------------------------------------------------------------------

def test_une_entree_sans_date_est_constatee_sur_trois_proprietes():
    """Aucune date, aucun `source_url`, et publiée **active** : la troisième est
    celle qui se voit à l'écran."""
    profil = _profil(mandats=[
        {"label": "Vidéos", "categorie": "commission", "actif": True, "debut": None, "fin": None},
    ])
    constats = verifier_entrees_sans_date(profil)
    assert constats == [{"label": "Vidéos", "categorie": "commission", "sans_date": True,
                        "sans_source_url": True, "publie_comme_actif": True}]


def test_un_mandat_date_n_est_pas_constate():
    profil = _profil(mandats=[
        {"label": "Commission des lois", "categorie": "commission", "actif": True, "debut": "2022-06-29"},
    ])
    assert verifier_entrees_sans_date(profil) == []


# ---------------------------------------------------------------------------
# L'audit ne modifie rien
# ---------------------------------------------------------------------------

def test_la_simulation_ne_touche_pas_au_profil():
    interventions = [
        _heritee(249506, "2023-05-02", "<p>Les Mahorais ont manifesté !</p>"),
        _syceron("2023-05-02", "Les Mahorais ont manifesté !"),
    ]
    profil = _profil(sources=[{"type": "nosdeputes", "url": "https://www.nosdeputes.fr/x"}],
                     interventions=interventions)
    residus = residus_du_profil(profil)
    assert residus["interventions_retirees"] == 1
    assert profil["interventions"] is interventions
    assert len(profil["interventions"]) == 2
    assert len(profil["sources"]) == 1
