"""#1175 — un membre compte pour un scrutin s'il appartenait au groupe ce jour-là.

`_compute_cohesion_votes` tenait pour éligible tout profil passé par le groupe
dans la législature et EN MANDAT DE DÉPUTÉ le jour du scrutin. Quiconque avait
quitté le groupe, ou n'y était pas encore entré, comptait au dénominateur — et
avec sa voix.

Les deux profils ci-dessous sont réduits de profils réels (privé `2140244c4`),
mandats, votes et périodes copiés tels quels :

- Éric Woerth, membre d'Ensemble pour la République du 19/07/2024 au 01/03/2026 ;
- Stella Dupont, membre du 19/07/2024 au 03/10/2024, députée non inscrite
  ensuite, mandat toujours ouvert.

Le 30/10/2024 (`an:17:200`), Stella Dupont vote « pour », 27 jours après avoir
quitté le groupe : la fiche publiée d'EPR comptait ce « pour ».
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from group_profile import _compute_cohesion_votes  # noqa: E402
from scrutins_index import ScrutinsIndex  # noqa: E402

SCRUTINS = ScrutinsIndex({
    "an:17:200": {"id": "an:17:200", "legislature": "17", "numero_scrutin": "200",
                  "date": "2024-10-30"},
    "an:17:4241": {"id": "an:17:4241", "legislature": "17", "numero_scrutin": "4241",
                   "date": "2025-11-21"},
})

WOERTH = {
    "id": "eric-woerth",
    "mandats": [{"label": "Mandat parlementaire (Ensemble pour la République)",
                 "categorie": "mandat_electif", "fonction": "mandat",
                 "debut": "2024-07-07", "fin": "2026-03-01", "chambre": "AN"}],
    "votes": [{"scrutin_id": "an:17:4241", "position": "contre"}],
}
DUPONT = {
    "id": "stella-dupont",
    "mandats": [{"label": "Mandat parlementaire (Non inscrit)",
                 "categorie": "mandat_electif", "fonction": "mandat",
                 "debut": "2024-07-07", "fin": None, "chambre": "AN"}],
    "votes": [{"scrutin_id": "an:17:200", "position": "pour"}],
}
APPARTENANCES = {
    "eric-woerth": [("2024-07-19", "2026-03-01")],
    "stella-dupont": [("2024-07-19", "2024-10-03")],
}


def _cohesion(appartenances):
    lignes = _compute_cohesion_votes(
        [WOERTH, DUPONT], legislature="17", scrutins_index=SCRUTINS, chambre="AN",
        appartenances=appartenances)
    return {l["scrutin_id"]: l for l in lignes}


def test_avant_la_voix_d_une_deputee_partie_comptait_pour_le_groupe():
    """Le constat, tel que le code le rendait : c'est ce qui était publié."""
    ancien = _cohesion(None)
    assert ancien["an:17:200"]["membres_eligibles"] == 2
    assert ancien["an:17:200"]["pour"] == 1
    assert ancien["an:17:4241"]["membres_eligibles"] == 2
    assert ancien["an:17:4241"]["absents"] == 1


def test_un_membre_parti_ne_compte_ni_au_denominateur_ni_par_sa_voix():
    nouveau = _cohesion(APPARTENANCES)
    # Le 30/10/2024, seul Éric Woerth est membre, et il n'a pas voté.
    assert nouveau["an:17:200"]["membres_eligibles"] == 1
    assert nouveau["an:17:200"]["pour"] == 0
    assert nouveau["an:17:200"]["absents"] == 1
    assert nouveau["an:17:200"]["position_majoritaire"] is None
    # Le 21/11/2025, il vote « contre », et il est le seul membre.
    assert nouveau["an:17:4241"]["membres_eligibles"] == 1
    assert nouveau["an:17:4241"]["contre"] == 1
    assert nouveau["an:17:4241"]["absents"] == 0


def test_un_scrutin_sans_aucun_membre_ce_jour_la_n_est_pas_attribue_au_groupe():
    seule = _compute_cohesion_votes(
        [DUPONT], legislature="17", scrutins_index=SCRUTINS, chambre="AN",
        appartenances=APPARTENANCES)
    assert seule == []


def test_les_bornes_de_l_appartenance_sont_incluses():
    index = ScrutinsIndex({"an:17:1": {"id": "an:17:1", "legislature": "17",
                                       "numero_scrutin": "1", "date": "2024-10-03"}})
    dupont = {**DUPONT, "votes": [{"scrutin_id": "an:17:1", "position": "pour"}]}
    (ligne,) = _compute_cohesion_votes(
        [dupont], legislature="17", scrutins_index=index, chambre="AN",
        appartenances=APPARTENANCES)
    assert ligne["pour"] == 1


def test_une_appartenance_non_datee_garde_le_critere_du_mandat():
    """On n'exclut pas quelqu'un sur une date qu'on n'a pas (§2 règle 5)."""
    non_datee = _cohesion({"eric-woerth": APPARTENANCES["eric-woerth"], "stella-dupont": None})
    assert non_datee["an:17:200"]["membres_eligibles"] == 2
    assert non_datee["an:17:200"]["pour"] == 1
