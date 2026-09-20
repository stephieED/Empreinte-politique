"""`identite` composée champ par champ, aux deux étages (#601, lot 2 de #598).

Le critère de sortie de l'issue est explicite : « un test compose une identité à
partir de deux sources partielles et vérifie que **les deux** contributions
survivent ». C'est ce que fait
`test_les_deux_contributions_partielles_survivent`, et il échoue sur le code
d'avant, où un seul des deux blocs sortait vivant.

Tous les tests de comportement de ce fichier sont écrits pour tomber sur la
forme d'avant — *choisir un bloc gagnant* — et pas seulement sur son critère de
choix. Le palliatif de #597 avait rendu le choix plus fin ; ce lot le remplace.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import (  # noqa: E402
    BLOCS_PROTEGES_DU_VIDE,
    fusionner_identite,
    merge_pivot_profile,
    merge_raw_profile,
    valeur_de_source,
)
from migrer_absences_publiees_556_558_560 import est_marqueur_nil  # noqa: E402

MARQUEUR = {
    "@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "@xsi:nil": "true",
}
MARQUEUR_INTERPOLE = (
    "{'@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', '@xsi:nil': 'true'}"
)

IDENTITE_AN = {
    "nom_complet": "Jean-Luc Mélenchon",
    "groupe_sigle": "FI",
    "groupe_nom": "La France insoumise",
    "profession": "Professeur",
    "date_naissance": "1951-08-19",
    "lieu_naissance": "Tanger",
    "num_circo": "4",
    "nb_mandats": 1,
    "uri_hatvp": "https://www.hatvp.fr/fiche/melenchon",
    "url_an_ou_senat": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA2150",
}

SQUELETTE = {
    "nom_complet": "Jean-Luc Mélenchon",
    "groupe_sigle": None,
    "groupe_nom": "La France Insoumise (LFI)",
    "profession": None,
    "date_naissance": None,
    "num_circo": None,
    "nb_mandats": None,
    "url_an_ou_senat": None,
}


# ---------------------------------------------------------------------------
# Le critère de sortie de #601
# ---------------------------------------------------------------------------

def test_les_deux_contributions_partielles_survivent():
    """Le job AN connaît la profession, le job UE le groupe : on garde les deux.

    Avant, un seul des deux blocs survivait — celui du dernier écrivain à « avoir
    du fond ». La contribution de l'autre était perdue sans que rien ne le dise.
    """
    an = {"profession": "Professeur", "date_naissance": "1951-08-19", "groupe_nom": None}
    ue = {"profession": None, "date_naissance": None, "groupe_nom": "La France insoumise"}
    fusionne = fusionner_identite(an, ue)
    assert fusionne["profession"] == "Professeur"
    assert fusionne["date_naissance"] == "1951-08-19"
    assert fusionne["groupe_nom"] == "La France insoumise"


def test_un_champ_que_seul_l_ancien_connait_n_est_pas_perdu():
    """Le nouvel écrivain n'a même pas la clé : elle ne disparaît pas."""
    fusionne = fusionner_identite(IDENTITE_AN, {"profession": "Professeur"})
    assert fusionne["lieu_naissance"] == "Tanger"
    assert fusionne["uri_hatvp"] == "https://www.hatvp.fr/fiche/melenchon"


def test_une_absence_n_ecrase_jamais_une_valeur_connue():
    fusionne = fusionner_identite(IDENTITE_AN, dict(IDENTITE_AN, profession=None))
    assert fusionne["profession"] == "Professeur"


def test_une_vraie_valeur_neuve_gagne_sur_son_champ():
    fusionne = fusionner_identite(IDENTITE_AN, dict(IDENTITE_AN, profession="Sénateur"))
    assert fusionne["profession"] == "Sénateur"
    assert fusionne["date_naissance"] == "1951-08-19"


# ---------------------------------------------------------------------------
# Ce qui reste de #484 : les champs remplis sans source
# ---------------------------------------------------------------------------

def test_le_groupe_editorial_du_squelette_n_ecrase_pas_le_groupe_parlementaire():
    """Le trou que la composition pure aurait rouvert.

    `groupe_nom` est l'un des deux champs que `build_minimal_profile` remplit
    depuis `raw_data/candidats.json`, sans rien demander à personne. Composer
    sans réserve laisserait « La France Insoumise (LFI) » écraser le groupe
    déclaré à l'AN, uniquement parce que le job UE passe en dernier.
    """
    fusionne = fusionner_identite(IDENTITE_AN, SQUELETTE)
    assert fusionne["groupe_nom"] == "La France insoumise"
    assert fusionne["groupe_sigle"] == "FI"
    assert fusionne["profession"] == "Professeur"


def test_deux_blocs_pauvres_face_a_face_le_neuf_parle():
    """`jordan-bardella` : aucune identité AN d'aucun côté. Il n'y a rien de
    mieux à protéger, donc la réserve ne s'applique pas."""
    fusionne = fusionner_identite(
        SQUELETTE, dict(SQUELETTE, nom_complet="Jordan Bardella", groupe_nom="RN")
    )
    assert fusionne["nom_complet"] == "Jordan Bardella"
    assert fusionne["groupe_nom"] == "RN"


def test_un_bloc_qui_apporte_du_fond_peut_corriger_un_champ_sans_source():
    """La réserve porte sur les blocs SANS fond, pas sur les champs.

    Un écrivain qui a réellement collecté quelque chose corrige `groupe_nom`
    comme n'importe quel autre champ — sinon un changement de groupe ne pourrait
    plus jamais être publié.
    """
    neuf = dict(SQUELETTE, groupe_nom="Groupe neuf", profession="Professeur certifié")
    fusionne = fusionner_identite(IDENTITE_AN, neuf)
    assert fusionne["groupe_nom"] == "Groupe neuf"


def test_la_table_des_champs_sans_source_suit_le_profil_minimal():
    """Garde-fou de #597, conservé : si `build_minimal_profile` apprend à
    remplir un champ de plus sans source, la table doit le savoir."""
    from generate_all_profiles import build_minimal_profile

    minimal = build_minimal_profile(
        "Jean-Luc Mélenchon", "jean-luc-melenchon", {"parti": "La France Insoumise (LFI)"}
    )
    renseignes = {
        champ for champ, valeur in minimal["identite"].items()
        if valeur_de_source(valeur) is not None
    }
    assert renseignes <= set(BLOCS_PROTEGES_DU_VIDE["identite"]), (
        "le profil minimal remplit un champ que BLOCS_PROTEGES_DU_VIDE ne "
        "déclare pas comme rempli sans source"
    )


# ---------------------------------------------------------------------------
# Le marqueur `xsi:nil` ne vaut pas une valeur
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("marqueur", [MARQUEUR, MARQUEUR_INTERPOLE])
def test_un_marqueur_nil_n_ecrase_pas_une_valeur_connue(marqueur):
    """#556 a fermé l'amont ; la fusion ne doit pas le laisser gagner s'il
    ressurgit. Un dict truthy se repère ; une chaîne interpolée non vide se lit
    comme une donnée, et c'est la pire des deux formes."""
    fusionne = fusionner_identite(IDENTITE_AN, dict(IDENTITE_AN, profession=marqueur))
    assert fusionne["profession"] == "Professeur"


@pytest.mark.parametrize("marqueur", [MARQUEUR, MARQUEUR_INTERPOLE])
def test_un_champ_dont_le_seul_candidat_est_un_marqueur_est_publie_null(marqueur):
    """Une absence déclarée par la source est une absence, pas une valeur (§2.5).
    Republier la plomberie XML ferait croire à un consommateur qui teste
    `if identite['profession']` qu'il tient une profession."""
    fusionne = fusionner_identite(
        dict(IDENTITE_AN, profession=marqueur), dict(IDENTITE_AN, profession=None)
    )
    assert fusionne["profession"] is None


@pytest.mark.parametrize("marqueur", [MARQUEUR, MARQUEUR_INTERPOLE])
def test_la_lecture_du_marqueur_n_a_pas_diverge_de_sa_definition_canonique(marqueur):
    """`merge_profile` recopie le prédicat plutôt que d'importer un script de
    migration dans le chemin chaud du pipeline. Ce test est le prix de la
    recopie."""
    assert valeur_de_source(marqueur) is None
    if isinstance(marqueur, dict):
        assert est_marqueur_nil(marqueur)


def test_valeur_de_source_garde_un_zero():
    """`nb_mandats: 0` est une valeur mesurée, pas une absence."""
    assert valeur_de_source(0) == 0


# ---------------------------------------------------------------------------
# Les deux étages
# ---------------------------------------------------------------------------

def test_etage_brut_le_squelette_ne_vide_plus_rien():
    """Non-régression de #484/#597 : ce cas-là passait déjà avant ce lot, et il
    doit continuer de passer une fois le palliatif absorbé."""
    merged = merge_raw_profile(
        {"slug": "x", "identite": dict(IDENTITE_AN)},
        {"slug": "x", "identite": dict(SQUELETTE)},
    )
    assert merged["identite"]["profession"] == "Professeur"
    assert merged["identite"]["lieu_naissance"] == "Tanger"
    assert merged["identite"]["groupe_nom"] == "La France insoumise"


def test_etage_brut_une_identite_absente_ne_regresse_pas_vers_null():
    """`identite` est un scalaire SURVEILLÉ par `audit_diff_profils` : un
    passage renseigné -> `null` abandonne le commit."""
    merged = merge_raw_profile({"identite": dict(IDENTITE_AN)}, {"identite": None})
    assert merged["identite"] == IDENTITE_AN


def _pivot(**extra) -> dict:
    base = {
        "schema_version": "1",
        "id": "x",
        "nom": "X",
        "chambre": "AN",
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": [],
        "amendements": [],
        "tags_thematiques": [],
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-08-29T16:00:00+0000",
            "licence_donnees": "Licence Ouverte",
            "warnings": [],
        },
    }
    base.update(extra)
    return base


def test_etage_pivot_compose_aussi_champ_par_champ():
    ancien = _pivot(identite={
        "profession": "Professeur",
        "date_naissance": "1951-08-19",
        "lieu_naissance": "Tanger",
        "num_circo": "4",
        "uri_hatvp": "https://www.hatvp.fr/fiche/melenchon",
        "source_url": "https://www2.assemblee-nationale.fr/",
    })
    neuf = _pivot(identite={
        "profession": None,
        "date_naissance": None,
        "lieu_naissance": None,
        "num_circo": "5",
        "uri_hatvp": None,
        "source_url": None,
    })
    fusionne = merge_pivot_profile(ancien, neuf)
    assert fusionne["identite"]["profession"] == "Professeur"
    assert fusionne["identite"]["num_circo"] == "5"
    assert fusionne["identite"]["source_url"] == "https://www2.assemblee-nationale.fr/"


# ---------------------------------------------------------------------------
# L'invariant `uri_hatvp` / `identifiants.hatvp`
# ---------------------------------------------------------------------------

URI = "https://www.hatvp.fr/fiche/melenchon"


def test_les_deux_noms_de_l_uri_hatvp_ne_divergent_pas_apres_composition():
    """`identifiants.hatvp` est la recopie d'`identite.uri_hatvp`, jamais une
    seconde collecte : `validate_profil` refuse qu'ils diffèrent. Ce sont
    désormais deux compositions distinctes, et rien ne garantissait qu'elles
    retiennent la même valeur."""
    ancien = _pivot(
        identite={"uri_hatvp": URI, "source_url": "https://x"},
        identifiants={"an": "PA2150", "hatvp": None},
    )
    neuf = _pivot(
        identite={"uri_hatvp": None, "source_url": "https://x"},
        identifiants={"an": "PA2150", "hatvp": None},
    )
    fusionne = merge_pivot_profile(ancien, neuf)
    assert fusionne["identite"]["uri_hatvp"] == URI
    assert fusionne["identifiants"]["hatvp"] == URI


def test_l_uri_connue_du_seul_bloc_identifiants_revient_dans_identite():
    ancien = _pivot(
        identite={"uri_hatvp": None, "source_url": "https://x"},
        identifiants={"an": "PA2150", "hatvp": URI},
    )
    neuf = _pivot(
        identite={"uri_hatvp": None, "source_url": "https://x"},
        identifiants={"an": "PA2150", "hatvp": None},
    )
    fusionne = merge_pivot_profile(ancien, neuf)
    assert fusionne["identite"]["uri_hatvp"] == URI
    assert fusionne["identifiants"]["hatvp"] == URI


def test_le_profil_fusionne_passe_la_validation_du_schema():
    """Le contrôle qui compte : c'est `validate_profil` qui refuse la
    divergence, pas ce fichier de tests."""
    from schema_pivot import validate_profil

    ancien = _pivot(
        identite={
            "profession": "Professeur",
            "date_naissance": "1951-08-19",
            "lieu_naissance": "Tanger",
            "num_circo": "4",
            "uri_hatvp": URI,
            "source_url": "https://www2.assemblee-nationale.fr/",
        },
        identifiants={"an": "PA2150", "senat": None, "europarl": None, "hatvp": None},
    )
    neuf = _pivot(
        identite={
            "profession": None,
            "date_naissance": None,
            "lieu_naissance": None,
            "num_circo": None,
            "uri_hatvp": None,
            "source_url": "https://www2.assemblee-nationale.fr/",
        },
        identifiants={"an": "PA2150", "senat": None, "europarl": None, "hatvp": None},
    )
    fusionne = merge_pivot_profile(ancien, neuf)
    assert validate_profil(fusionne) == []


# ---------------------------------------------------------------------------
# La mesure 1 de #599, rejouée
# ---------------------------------------------------------------------------

def test_la_mesure_1_de_599_rend_zero_apres_la_fusion():
    """Le critère de sortie de #601, vérifié avec l'outil du lot 0."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from audit_fusion_blocs_599 import mesurer_identite

    brut = merge_raw_profile(
        {
            "slug": "x",
            "identite": dict(IDENTITE_AN),
            "votes": [{"numero_scrutin": 1, "date": "2024-01-01"}],
            "meta": {"genere_le": "2026-08-29T16:00:00+0000", "warnings": []},
        },
        {
            "slug": "x",
            "identite": dict(SQUELETTE),
            "votes": [],
            "meta": {"genere_le": "2026-08-19T18:00:00+0000", "warnings": []},
        },
    )
    mesure = mesurer_identite({"x": brut}, {})
    assert mesure["nb_profils_touches"] == 0
