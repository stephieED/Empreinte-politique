#!/usr/bin/env python3
"""
test_commission_au_fond_gouvernement_689.py — Un texte de gouvernement porte sa
commission saisie au fond, ou dit pourquoi il ne la porte pas (#689).

Lire les lois d'un gouvernement par matière suppose une matière, et le dépôt n'a
pas à en inventer une : l'Assemblée renvoie elle-même chaque dossier à une
commission, et `pivot_data/commissions_dossiers.json` la publie depuis le commit
de données `5de11422`.

Ce que ces tests verrouillent tient dans la distinction des trois motifs
d'absence. Mesuré le 04/09/2026 sur les 725 textes publiés : **381 des 381**
dossiers déposés à l'AN résolvent, et **les 174 non résolus sont à 100 % des
dépôts au Sénat** — l'index est celui de l'AN, et le Sénat est hors périmètre
(#528). Confondre cette limite avec un trou de collecte, ou avec une panne du
run, ferait lire une décision éditoriale comme un défaut : c'est la leçon de
#726, où un audit rendait 62 705 lignes en lisant un champ déplacé.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gouvernement_profile import _commission_du_texte  # noqa: E402
from schema_gouvernement import (  # noqa: E402
    KNOWN_MOTIFS_COMMISSION_NON_RESOLUE,
    validate_profil_gouvernement,
)

INDEX = {
    "DLR5L17N50172": {
        "organe_ref": "PO420120",
        "sigle": "Affaires sociales",
        "nom": "Commission des affaires sociales",
        "type": "COMPER",
    }
}


# --------------------------------------------------------------------------
# 1. La résolution, et les trois motifs qui ne se confondent pas
# --------------------------------------------------------------------------

def test_un_dossier_indexe_rend_sa_commission():
    commission, non_resolue = _commission_du_texte("DLR5L17N50172", "AN", INDEX)

    assert non_resolue is None
    assert commission == {
        "organe_ref": "PO420120",
        "sigle": "Affaires sociales",
        "nom": "Commission des affaires sociales",
        "type": "COMPER",
    }


def test_le_type_d_organe_est_republie_verbatim():
    """Ce test disait d'abord l'inverse, et il avait tort.

    `type` n'est pas une propriété du seul référentiel : une `CNPS` est une
    commission **spéciale créée pour ce texte-là**, une `COMPER` est permanente
    et couvre une matière. Sans lui, séparer les matières principales de la
    traîne n'a d'autre règle qu'un seuil — l'arbitrage éditorial déguisé en
    mesure que §2 règle 1 refuse. Mesuré sur les 725 textes publiés :
    COMPER 532, CNPS 19.
    """
    commission, _ = _commission_du_texte("DLR5L17N50172", "AN", INDEX)

    assert commission["type"] == "COMPER"


def test_un_type_absent_de_l_index_est_publie_null_pas_omis():
    """Une clé qui disparaît selon l'entrée oblige chaque lecteur à se défendre ;
    `null` dit « l'index ne le porte pas » et se lit d'une seule façon."""
    index = {"DLR5L17N50172": {"organe_ref": "PO1", "sigle": "S", "nom": "N"}}
    commission, _ = _commission_du_texte("DLR5L17N50172", "AN", index)

    assert commission["type"] is None


def test_un_depot_senat_absent_de_l_index_est_une_limite_de_perimetre():
    """Les 174 textes concernés ne sont pas un trou de collecte : l'index est
    celui de l'AN, et le Sénat est hors périmètre depuis #528."""
    commission, non_resolue = _commission_du_texte("DLR5L16N49943", "Senat", INDEX)

    assert commission is None
    assert non_resolue == {"motif": "depot_senat"}


def test_un_depot_AN_absent_de_l_index_est_un_vrai_trou():
    """Compteur-témoin : ce motif vaut 0 sur le corpus publié. Non nul, il dit
    que l'index a cessé de couvrir ce qu'il couvrait."""
    commission, non_resolue = _commission_du_texte("DLR5L17N99999", "AN", INDEX)

    assert commission is None
    assert non_resolue == {"motif": "absente_de_l_index"}


def test_un_index_absent_est_declare_et_non_tu():
    """`None` n'est pas une erreur, c'est un motif publié : sans lui, une panne
    du run se lirait comme « aucun texte n'a de commission » (#510, #726)."""
    commission, non_resolue = _commission_du_texte("DLR5L17N50172", "AN", None)

    assert commission is None
    assert non_resolue == {"motif": "index_indisponible"}


def test_un_texte_sans_dossier_id_ne_resout_pas():
    commission, non_resolue = _commission_du_texte(None, "AN", INDEX)

    assert commission is None
    assert non_resolue == {"motif": "absente_de_l_index"}


def test_les_motifs_produits_appartiennent_tous_au_vocabulaire():
    produits = {
        _commission_du_texte("X", "Senat", INDEX)[1]["motif"],
        _commission_du_texte("X", "AN", INDEX)[1]["motif"],
        _commission_du_texte("X", "AN", None)[1]["motif"],
    }
    assert produits == set(KNOWN_MOTIFS_COMMISSION_NON_RESOLUE)


@pytest.mark.parametrize("chambre", ["AN", "Senat", None])
def test_exactement_un_des_deux_est_rendu(chambre):
    """L'invariant que le schéma refuse de voir violé : une commission résolue
    n'a pas de motif d'absence, et réciproquement."""
    commission, non_resolue = _commission_du_texte("DLR5L17N50172", chambre, INDEX)
    assert (commission is None) != (non_resolue is None)


# --------------------------------------------------------------------------
# 2. Le schéma refuse la contradiction
# --------------------------------------------------------------------------

def _profil(texte_extra):
    texte = {
        "dossier_id": "DLR5L17N50172",
        "titre": "Un texte",
        "statut": "adopte",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": False,
        "initiateurs": None,
        "source_url": None,
    }
    texte.update(texte_extra)
    return {
        "schema_version": "gouvernement-v1",
        "type_document": "gouvernement",
        "gouvernement_id": "gouvernement:X",
        "nom": "Gouvernement X",
        "periode": {"debut": "2024-01-01", "fin": None, "actif": True},
        "premier_ministre": None,
        "membres": [],
        "textes": [texte],
        "comptages": {"par_statut": {}},
        "sources": [],
        "meta": {},
    }


def test_le_schema_accepte_une_commission_resolue():
    erreurs = validate_profil_gouvernement(
        _profil({"commission_saisie_au_fond": INDEX["DLR5L17N50172"], "commission_non_resolue": None})
    )
    assert not [e for e in erreurs if "commission" in e]


def test_le_schema_accepte_un_motif_connu():
    erreurs = validate_profil_gouvernement(
        _profil({"commission_saisie_au_fond": None, "commission_non_resolue": {"motif": "depot_senat"}})
    )
    assert not [e for e in erreurs if "commission" in e]


def test_le_schema_refuse_un_motif_invente():
    erreurs = validate_profil_gouvernement(
        _profil({"commission_saisie_au_fond": None, "commission_non_resolue": {"motif": "sait_pas"}})
    )
    assert [e for e in erreurs if "commission_non_resolue.motif" in e]


def test_le_schema_refuse_les_deux_a_la_fois():
    """« Voici sa commission » et « voici pourquoi elle manque » ne peuvent pas
    être vrais ensemble."""
    erreurs = validate_profil_gouvernement(
        _profil({
            "commission_saisie_au_fond": INDEX["DLR5L17N50172"],
            "commission_non_resolue": {"motif": "depot_senat"},
        })
    )
    assert [e for e in erreurs if "à la fois" in e]
