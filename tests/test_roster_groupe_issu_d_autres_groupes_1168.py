#!/usr/bin/env python3
"""
Un groupe né d'une scission n'est pas une configuration fausse (#1168).

Le run du 02/10/2026 à 20:23 s'est arrêté sur « groupe AN:AGIR:15 (AGIR) :
0 membre retenu ». Les 23 membres d'Agir ensemble (XVe) étaient tous passés
avant par un groupe que la table range plus haut — 11 par LAREM, 10 par le
groupe UDI —, et la garde comptait les membres **retenus après
déduplication**. Elle compte désormais ceux que le filtre par sigle **trouve** :
c'est un sigle qui ne trouve personne qu'elle doit voir.

Les deux membres ci-dessous reprennent la forme d'une entrée du roster complet
(`an_roster.fetch_full_roster_an`) : un acteur passé par deux groupes dans la
même législature y apparaît une fois par groupe.
"""

from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from generate_roster_candidats import (  # noqa: E402
    anomalies_roster,
    build_roster_candidats_detaille,
)


def _groupe(sigle: str) -> dict:
    return {
        "roster_chambre": "deputes", "groupe_id": f"AN:{sigle}:15", "groupe_sigle": sigle,
        "groupe_nom": sigle, "chambre": "AN", "legislature": "15",
        "fichier": f"groupe-AN-{sigle}-15.json",
    }


def _membre(slug: str, sigle: str, debut: str, fin: str) -> dict:
    return {"acteur_ref": f"PA-{slug}", "slug": slug, "nom": slug, "groupe_sigle": sigle,
            "mandat_debut": debut, "mandat_fin": fin}


ROSTER_XVE = [
    _membre("alice", "LAREM", "2017-06-27", "2020-05-26"),
    _membre("bob", "UDI", "2017-06-27", "2020-05-25"),
    _membre("alice", "AGIR", "2020-05-27", "2022-06-21"),
    _membre("bob", "AGIR", "2020-05-27", "2022-06-21"),
]
GROUPES = [_groupe("LAREM"), _groupe("UDI"), _groupe("AGIR")]


def test_un_groupe_dont_tous_les_membres_viennent_d_autres_groupes_n_est_pas_une_anomalie():
    rosters = {("deputes", "15"): ROSTER_XVE}
    candidats, par_groupe = build_roster_candidats_detaille(GROUPES, rosters)
    assert par_groupe["AN:AGIR:15"] == 2
    assert anomalies_roster(GROUPES, rosters, par_groupe, candidats) == []


def test_chaque_personne_reste_un_seul_candidat():
    """La déduplication ne change pas : on compte autrement, on ne collecte pas deux fois."""
    candidats, _ = build_roster_candidats_detaille(GROUPES, {("deputes", "15"): ROSTER_XVE})
    assert sorted(c["slug"] for c in candidats) == ["alice", "bob"]


def test_un_sigle_qui_ne_trouve_personne_reste_une_anomalie():
    groupes = [*GROUPES, _groupe("RENOMME")]
    rosters = {("deputes", "15"): ROSTER_XVE}
    candidats, par_groupe = build_roster_candidats_detaille(groupes, rosters)
    anomalie, = anomalies_roster(groupes, rosters, par_groupe, candidats)
    assert "RENOMME" in anomalie and "0 membre trouvé" in anomalie


def test_un_membre_sans_slug_ne_compte_pas():
    """Il n'entre pas au roster : le compter masquerait un groupe dont personne n'entre."""
    roster = [{**_membre("x", "AGIR", "2020-05-27", "2022-06-21"), "slug": None}]
    rosters = {("deputes", "15"): roster}
    candidats, par_groupe = build_roster_candidats_detaille([_groupe("AGIR")], rosters)
    assert par_groupe["AN:AGIR:15"] == 0
    assert anomalies_roster([_groupe("AGIR")], rosters, par_groupe, candidats)
