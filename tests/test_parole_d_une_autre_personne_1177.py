#!/usr/bin/env python3
"""
Tests du constat 3 de #1177 — une prise de parole dont le libellé nomme une autre
personne que l'acteur attribué n'est pas attribuée.

Le 08/01/2026, l'Assemblée rattache à Audrey Abadie-Amiel (`PA793214`), aux deux
endroits où elle écrit l'orateur, les paroles de deux invités du débat : « M.
Jean-Marc Cantais, policier, lanceur d'alerte » et « Mme Assa Traoré ». Seul le
nom trahit l'erreur. Arbitrage de la propriétaire, 07/10/2026.

Ce que ces tests verrouillent :

- **la règle est étroite** : un libellé de fonction, un nom d'une lettre, un nom
  d'usage changé ne sont pas « une autre personne » ;
- **la collecte refuse**, et le dit par un motif ;
- **le retrait nommé** enlève les paroles déjà publiées, et seulement de la fiche
  à laquelle la source les rattachait.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import candidate_profile  # noqa: E402
from candidate_profile import (  # noqa: E402
    _normaliser_orateur_id_syceron,
    libelle_designe_une_autre_personne,
)
from paroles_d_une_autre_personne import (  # noqa: E402
    charger_table,
    retirer_paroles_d_une_autre_personne,
)

pytestmark = pytest.mark.lit_reference_committee("config/paroles_d_une_autre_personne.json")

# Identités copiées de l'index d'identité AMO30 en cache (07/10/2026).
ABADIE_AMIEL = {"prenom": "Audrey", "nom": "Abadie-Amiel"}
CEDRIC_O = {"prenom": "Cédric", "nom": "O"}
LE_NABOUR = {"prenom": "Christine", "nom": "Le Nabour"}
LUCAS_LUNDY = {"prenom": "Benjamin", "nom": "Lucas-Lundy"}


@pytest.mark.parametrize("libelle, identite, autre", [
    # Les deux invités du 08/01/2026, libellés copiés du compte rendu.
    ("M. Jean-Marc Cantais, policier, lanceur d’alerte", ABADIE_AMIEL, True),
    ("Mme Assa Traoré, militante antiraciste française, fondatrice du comité Vérité et justice pour Adama", ABADIE_AMIEL, True),
    # Ce qui n'est PAS une autre personne.
    ("Mme Audrey Abadie-Amiel (LIOT)", ABADIE_AMIEL, False),
    ("M. Cédric O", CEDRIC_O, False),                 # un nom d'une lettre
    ("Mme Christine Cloarec", LE_NABOUR, False),       # un nom d'usage changé
    ("M. Benjamin Lucas", LUCAS_LUNDY, False),         # un nom complété
    ("Mme la présidente", ABADIE_AMIEL, False),        # une fonction
    ("M. le ministre", CEDRIC_O, False),
    ("Plusieurs députés du groupe LIOT", ABADIE_AMIEL, False),  # un collectif
])
def test_la_regle(libelle, identite, autre):
    assert libelle_designe_une_autre_personne(libelle, identite) is autre


def test_sans_identite_rien_n_est_conclu():
    assert libelle_designe_une_autre_personne("M. Jean-Marc Cantais", None) is False


def test_la_collecte_refuse_et_nomme_le_motif():
    identites = {"PA793214": ABADIE_AMIEL}
    assert _normaliser_orateur_id_syceron(
        "793214", "PA793214", "M. Jean-Marc Cantais, policier, lanceur d’alerte",
        identites=identites,
    ) == (None, "libelle_d_une_autre_personne")
    assert _normaliser_orateur_id_syceron(
        "793214", "PA793214", "Mme Audrey Abadie-Amiel (LIOT)", identites=identites,
    ) == ("PA793214", "identifiant_nu_prefixe")


def test_sans_referentiel_la_collecte_garde_l_attribution_de_la_source():
    assert _normaliser_orateur_id_syceron(
        "793214", "PA793214", "M. Jean-Marc Cantais") == ("PA793214", "identifiant_nu_prefixe")


def test_la_version_d_index_a_change():
    """Un cache porte le code qui l'a écrit : sans cela, l'index restauré
    garderait les paroles refusées."""
    assert candidate_profile.SYCERON_VERSION_INDEX == "1177-libelle"


def test_la_table_committee_porte_les_deux_invites_du_08_01_2026():
    table = charger_table()
    for id_syceron in ("3984123", "3984138"):
        assert table[id_syceron]["acteur"] == "PA793214"
        assert table[id_syceron]["compte_rendu"] == "CRSANR5L17S2026O1N106"


def test_le_retrait_ne_touche_que_la_fiche_a_laquelle_la_source_l_attribuait():
    table = {"3984123": {"acteur": "PA793214"}}
    garde = {"id_syceron": "3984120"}
    fiche = {"identifiants": {"an": "PA793214"},
             "interventions": [{"id_syceron": "3984123"}, garde]}
    assert retirer_paroles_d_une_autre_personne(fiche, table) == 1
    assert fiche["interventions"] == [garde]
    autre = {"identifiants": {"an": "PA000001"}, "interventions": [{"id_syceron": "3984123"}]}
    assert retirer_paroles_d_une_autre_personne(autre, table) == 0


def test_une_table_absente_ne_retire_rien(tmp_path):
    assert charger_table(tmp_path / "absente.json") == {}
