"""#682 — le lieu d'élection se porte sur le mandat, complet.

`identite.num_circo` valait « 6 » pour Jérôme Guedj, et rien d'autre ne situait
son mandat : un numéro sans département ne désigne aucune circonscription, et un
champ rangé sur la personne ne peut pas dire qu'elle en a changé. AMO30 porte le
lieu sur chacun des 3 954 mandats de député, en cinq champs.

Les mandats ci-dessous sont copiés de l'archive AMO30 : Jérôme Guedj (`PA1567`),
et Bernard Cazeneuve (`PA785`), élu dans la 5e puis la 4e circonscription de la
Manche — l'un des 54 acteurs à avoir changé de circonscription.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile as cp  # noqa: E402
from merge_profile import _pivot_mandat_key, backfill_mandat_lieu_election  # noqa: E402
from normalize_profil import _normalize_mandat  # noqa: E402
from schema_pivot import CLES_LIEU_ELECTION, make_empty_profil, validate_profil  # noqa: E402

ESSONNE_6 = {"region": "Ile-de-France", "regionType": "Métropolitain",
             "departement": "Essonne", "numDepartement": "91", "numCirco": "6"}


def _mandat_an(legislature, debut, fin, lieu):
    return {"typeOrgane": "ASSEMBLEE", "legislature": legislature, "dateDebut": debut,
            "dateFin": fin, "election": {"lieu": lieu, "causeMandat": "élections générales"}}


GUEDJ = [_mandat_an("16", "2022-06-19", "2024-06-09", ESSONNE_6)]
MANCHE = {"region": "Normandie", "regionType": "Métropolitain", "departement": "Manche",
          "numDepartement": "50"}
CAZENEUVE = [
    _mandat_an("14", "2012-06-20", "2012-07-21", {**MANCHE, "numCirco": "4"}),
    _mandat_an("13", "2007-06-20", "2012-06-16", {**MANCHE, "numCirco": "5"}),
    _mandat_an("14", "2012-06-20", "2017-06-20", {**MANCHE, "numCirco": "4"}),
]


def test_les_cinq_champs_de_la_source_survivent():
    (periode,) = cp._periodes_mandats_assemblee(GUEDJ, {})
    assert periode["lieu_election"] == {
        "region": "Ile-de-France", "type_region": "Métropolitain",
        "departement": "Essonne", "num_departement": "91", "num_circo": "6"}
    assert set(periode["lieu_election"]) == CLES_LIEU_ELECTION


def test_un_changement_de_circonscription_se_lit_mandat_par_mandat():
    periodes = cp._periodes_mandats_assemblee(CAZENEUVE, {})
    par_debut = {p["debut"]: p["lieu_election"]["num_circo"] for p in periodes}
    # Deux segments de la XIVe recollés en un siège, et la XIIIe ailleurs.
    assert par_debut == {"2012-06-20": "4", "2007-06-20": "5"}


def test_un_mandat_sans_lieu_rend_null_et_pas_un_dict_vide():
    sans = [{"typeOrgane": "ASSEMBLEE", "legislature": "16", "dateDebut": "2022-06-19",
             "dateFin": None}]
    (periode,) = cp._periodes_mandats_assemblee(sans, {})
    assert periode["lieu_election"] is None


def test_le_nom_de_l_index_d_identite_a_change_avec_son_contenu():
    """Un index en cache écrit avant ce lot ne porte pas le lieu (#1169)."""
    assert cp.NOM_INDEX_IDENTITE != "index_identite_v4.json"


def _mandat_brut(lieu=...):
    brut = {"categorie": "mandat_electif", "type": "mandat",
            "label": "Mandat parlementaire (Socialistes et apparentés)",
            "debut": "2022-06-19", "fin": "2024-06-09", "actif": False, "chambre": "deputes"}
    if lieu is not ...:
        brut["lieu_election"] = lieu
    return brut


LIEU = {"region": "Ile-de-France", "type_region": "Métropolitain", "departement": "Essonne",
        "num_departement": "91", "num_circo": "6"}


def test_la_normalisation_publie_le_lieu_quand_le_brut_le_porte():
    assert _normalize_mandat(_mandat_brut(LIEU))["lieu_election"] == LIEU
    assert _normalize_mandat(_mandat_brut(None))["lieu_election"] is None
    # Un mandat collecté avant ce lot : la clé reste absente, elle ne dit rien.
    assert "lieu_election" not in _normalize_mandat(_mandat_brut())


def test_un_mandat_deja_publie_recoit_le_lieu():
    publie = _normalize_mandat(_mandat_brut())
    neuf = _normalize_mandat(_mandat_brut(LIEU))
    (apres,) = backfill_mandat_lieu_election([copy.deepcopy(publie)], [neuf], _pivot_mandat_key)
    assert apres["lieu_election"] == LIEU


def test_le_report_n_ecrit_jamais_sur_un_lieu_deja_pose():
    publie = {**_normalize_mandat(_mandat_brut(None))}
    neuf = _normalize_mandat(_mandat_brut(LIEU))
    (apres,) = backfill_mandat_lieu_election([publie], [neuf], _pivot_mandat_key)
    assert apres["lieu_election"] is None


def _profil_avec(mandat):
    profil = make_empty_profil(id_="jerome-guedj", nom="Jérôme Guedj")
    profil["mandats"] = [mandat]
    return profil


def test_la_validation_accepte_le_lieu_complet_null_ou_absent():
    for brut in (_mandat_brut(LIEU), _mandat_brut(None), _mandat_brut()):
        erreurs = validate_profil(_profil_avec(_normalize_mandat(brut)))
        assert not [e for e in erreurs if "lieu_election" in e]


def test_la_validation_refuse_un_lieu_incomplet_ou_hors_mandat_electif():
    incomplet = {**_normalize_mandat(_mandat_brut()), "lieu_election": {"num_circo": "6"}}
    assert any("lieu_election" in e for e in validate_profil(_profil_avec(incomplet)))
    commission = {**_normalize_mandat(_mandat_brut(LIEU)), "categorie": "commission"}
    assert any("seul un mandat électif" in e for e in validate_profil(_profil_avec(commission)))
