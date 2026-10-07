#!/usr/bin/env python3
"""
Tests du lot #1175 (amendements) — un amendement n'entre dans l'agrégat d'un
groupe que si son signataire y siégeait le jour du dépôt.

Arbitrage de la propriétaire, 06/10/2026 : la règle de la cohésion (#1218) et de
la parole (#1073), transposée aux amendements.

Ce qu'ils verrouillent :

- **la borne est l'appartenance du membre**, bornes incluses, et non la
  législature seule ;
- **une signature sans date est gardée**, et comptée (§2 règle 5) ;
- **une appartenance non datée ne filtre rien** ;
- **les exclusions se publient**, sous le nom de signatures (§6) ;
- **un amendement cosigné reste un**, et n'entre que par un signataire qui
  siégeait ce jour-là ;
- **le chargement borne**, puisque c'est là que les entrées meurent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from group_profile import (  # noqa: E402
    CumulAmendementsDistincts,
    _aggregate_amendements,
    contribution_amendements,
    load_profil_from_file,
    periodes_d_appartenance,
    periodes_depuis_appartenance,
)

# Écologie Démocratie Solidarité : du 20/05/2020 au 16/10/2020.
EDS = [("2020-05-20", "2020-10-16")]

# Trois amendements de la XVe cosignés par Delphine Batho, copiés de
# pivot_data/amendements/15.json le 06/10/2026 (privé 95fcbfaff) : identifiant,
# date de dépôt et sort réels. Un avant EDS, un pendant, un après.
AVANT = ("AMANR5L15PO717460B1490P0D1N001431", "2018-12-19", "adopté")
PENDANT = ("AMANR5L15PO717460BTC3358P0D1N000027", "2020-09-30", "rejeté")
APRES = ("AMANR5L15PO717460BTC4858P0D1N000499", "2021-12-31", "rejeté")


def _entree(amendement, date="defaut"):
    uid, jour, sort = amendement
    return {
        "amendement_id": f"an:{uid}",
        "role_signataire": "cosignataire",
        "amendement_non_resolu": {
            "sort": sort, "type_deposant": "depute", "texte_vise": "T",
            "date": jour if date == "defaut" else date, "numero": "1",
            "base_juridique_irrecevabilite": None, "premier_signataire": None,
            "co_signataires": [], "source_url": None,
        },
    }


def test_seul_l_amendement_depose_pendant_l_appartenance_est_retenu():
    """Avant correctif, la fiche EDS publiait 25 903 amendements — ceux que ses
    17 membres ont signés de 2017 à 2022 — pour 1 332 déposés pendant qu'ils y
    siégeaient."""
    contribution = contribution_amendements(
        [_entree(AVANT), _entree(PENDANT), _entree(APRES)], legislature="15", periodes=EDS
    )
    assert contribution.total["nb_amendements"] == 1
    assert contribution.total["nb_rejetes"] == 1  # celui de septembre 2020
    assert contribution.hors_appartenance == 2
    assert contribution.hors_periode == 0


def test_les_bornes_sont_incluses():
    premier = _entree(PENDANT, date="2020-05-20")
    dernier = _entree(APRES, date="2020-10-16")
    veille = _entree(AVANT, date="2020-05-19")
    contribution = contribution_amendements([premier, dernier, veille], legislature="15", periodes=EDS)
    assert contribution.total["nb_amendements"] == 2
    assert contribution.hors_appartenance == 1


def test_une_signature_sans_date_est_gardee_et_comptee():
    contribution = contribution_amendements(
        [_entree(PENDANT, date=None), _entree(AVANT)], legislature="15", periodes=EDS
    )
    assert contribution.total["nb_amendements"] == 1
    assert contribution.sans_date == 1
    assert contribution.hors_appartenance == 1


def test_une_appartenance_non_datee_ne_filtre_rien():
    """`None` n'est pas « aucune période » : c'est « on ne sait pas », et la
    législature reste alors la seule borne — comme pour la cohésion."""
    contribution = contribution_amendements(
        [_entree(AVANT), _entree(PENDANT), _entree(APRES)], legislature="15", periodes=None
    )
    assert contribution.total["nb_amendements"] == 3
    assert contribution.hors_appartenance == 0 and contribution.sans_date == 0


def test_la_legislature_borne_toujours_et_avant_l_appartenance():
    autre = ("AMANR5L16PO420120B0001P0D1N000001", "2020-06-15", "rejeté")
    contribution = contribution_amendements(
        [_entree(autre), _entree(PENDANT)], legislature="15", periodes=EDS
    )
    assert contribution.total["nb_amendements"] == 1
    assert contribution.hors_periode == 1 and contribution.hors_appartenance == 0


def test_un_depart_suivi_d_un_retour_compte_les_deux_periodes():
    periodes = [("2018-01-01", "2018-12-31"), ("2021-06-01", "2022-06-21")]
    contribution = contribution_amendements(
        [_entree(AVANT), _entree(PENDANT), _entree(APRES)], legislature="15", periodes=periodes
    )
    assert contribution.total["nb_amendements"] == 2
    assert contribution.hors_appartenance == 1


def test_un_amendement_cosigne_entre_par_le_signataire_qui_siegeait():
    """Deux membres cosignent le même amendement de 2018 ; un seul était au
    groupe ce jour-là. L'amendement est UN, et il est retenu."""
    profils = [
        {"id": "a", "amendements": [_entree(AVANT)]},
        {"id": "b", "amendements": [_entree(AVANT)]},
    ]
    total, _ = _aggregate_amendements(
        profils, None, appartenances={"a": [("2017-06-27", "2019-12-31")], "b": EDS}
    )
    assert total["nb_amendements"] == 1
    assert total["signatures"]["nb_signatures"] == 1
    assert total["nb_signatures_hors_appartenance_ecartees"] == 1


def test_les_exclusions_se_publient_sous_le_nom_de_signatures():
    profils = [{"id": "a", "amendements": [_entree(AVANT), _entree(PENDANT, date=None)]}]
    total, _ = _aggregate_amendements(profils, None, appartenances={"a": EDS})
    assert total["nb_signatures_hors_appartenance_ecartees"] == 1
    assert total["nb_signatures_sans_date_retenues"] == 1
    assert not [cle for cle in total if "amendements_hors" in cle]


def test_le_chargement_borne_car_les_entrees_n_y_survivent_pas(tmp_path):
    chemin = tmp_path / "delphine-batho.pivot.json"
    chemin.write_text(
        json.dumps({
            "schema_version": "1", "id": "delphine-batho", "nom": "Delphine Batho",
            "mandats": [], "votes": [], "interventions": [], "tags_thematiques": [],
            "sources": [], "amendements": [_entree(AVANT), _entree(PENDANT), _entree(APRES)],
        }),
        encoding="utf-8",
    )
    cumul = CumulAmendementsDistincts()
    profil = load_profil_from_file(chemin, None, distincts=cumul, legislature="15", periodes=EDS)
    assert profil["amendements"].total["nb_amendements"] == 1
    assert profil["amendements"].hors_appartenance == 2
    total, _ = _aggregate_amendements([profil], None)
    assert total["nb_amendements"] == 1


def test_les_deux_lectures_des_periodes_rendent_la_meme_chose():
    """Les amendements lisent l'entrée du roster, la cohésion lit `membres[]` :
    un même membre ne doit pas avoir deux appartenances."""
    du_roster = {"debut": "2020-05-20", "fin": "2020-10-16",
                 "periodes": [{"debut": "2020-05-20", "fin": "2020-10-16"}]}
    de_la_fiche = {"debut_dans_groupe": "2020-05-20", "fin_dans_groupe": "2020-10-16",
                   "periodes": [{"debut": "2020-05-20", "fin": "2020-10-16"}]}
    assert periodes_depuis_appartenance(du_roster) == periodes_d_appartenance(de_la_fiche) == EDS
    # Sans le détail (#809) : les deux bornes de l'enveloppe.
    assert periodes_depuis_appartenance({"debut": "2020-05-20", "fin": None, "periodes": None}) == [
        ("2020-05-20", None)
    ]
    assert periodes_depuis_appartenance({"debut": None, "fin": None, "periodes": None}) is None
    assert periodes_depuis_appartenance(None) is None
