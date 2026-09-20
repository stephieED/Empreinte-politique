"""Tests pour `couverture_dossiers.py` (#399).

Le périmètre réellement ingéré est la seule base admissible pour dire d'un
gouvernement qu'il est « hors couverture » plutôt que « à zéro » : ces tests
verrouillent la dérivation de la borne, la classification des périodes, et
l'alignement de la valeur dupliquée côté UI.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from couverture_dossiers import (
    AN_DOSSIERS_ARCHIVES,
    COUVERTURE_COUVERTE,
    COUVERTURE_HORS,
    COUVERTURE_INDETERMINEE,
    COUVERTURE_PARTIELLE,
    LEGISLATURES_DEBUT,
    borne_couverture_textes,
    legislatures_ingerees,
    libelle_couverture_textes,
    libelle_legislatures_ingerees,
    statut_couverture_textes,
    verifier_coherence_inventaire,
)

PIVOT_ADAPTER = (
    Path(__file__).resolve().parents[1]
    / "web" / "UI_finale" / "src" / "data" / "pivotAdapter.js"
)


# ---------------------------------------------------------------------------
# Inventaire et borne
# ---------------------------------------------------------------------------

def test_inventaire_coherent_toute_archive_ingeree_a_une_date_de_debut():
    # Ajouter une archive sans sa date de début fausserait silencieusement la
    # borne de couverture : c'est ce que ce garde-fou empêche.
    assert verifier_coherence_inventaire() == []


def test_legislatures_ingerees_est_triee():
    assert list(legislatures_ingerees()) == sorted(AN_DOSSIERS_ARCHIVES)


def test_borne_couverture_est_le_debut_de_la_plus_ancienne_legislature_ingeree():
    plus_ancienne = min(legislatures_ingerees())

    assert borne_couverture_textes() == LEGISLATURES_DEBUT[plus_ancienne]


def test_borne_couverture_valeur_courante():
    # XIV à XVII ingérées depuis #1019 : la borne est la première séance de la
    # XIV, relue dans l'organe `ASSEMBLEE` d'AMO30 et non de mémoire.
    assert borne_couverture_textes() == "2012-06-20"


def test_libelle_legislatures_contigues_est_un_intervalle():
    assert libelle_legislatures_ingerees() == "XIV–XVII"


def test_libelle_couverture_expose_la_borne():
    libelle = libelle_couverture_textes()

    assert "XIV" in libelle
    assert "2012-06-20" in libelle


# ---------------------------------------------------------------------------
# Classification des périodes
# ---------------------------------------------------------------------------

def test_periode_posterieure_a_la_borne_est_couverte():
    # Gouvernement Borne (XVI) : zéro texte y serait un zéro réellement constaté.
    assert statut_couverture_textes("2022-05-21", "2024-01-09") == COUVERTURE_COUVERTE


def test_periode_commencant_exactement_a_la_borne_est_couverte():
    assert statut_couverture_textes("2017-06-21", "2018-01-01") == COUVERTURE_COUVERTE


def test_periode_entierement_anterieure_est_hors_couverture():
    # Fillon II (XIIIe législature) : son archive répond 404, revérifié le
    # 18/09/2026. Hors couverture définitivement, même après #1019.
    assert statut_couverture_textes("2007-06-19", "2010-11-13") == COUVERTURE_HORS


def test_periode_a_cheval_sur_la_borne_est_partielle():
    # Ayrault II (19/06/2012 → 31/03/2014) est le cas réel depuis #1019 : il
    # commence LA VEILLE de l'ouverture de la XIV (2012-06-20), donc sa
    # couverture est partielle même si l'archive lui rend 187 textes.
    assert statut_couverture_textes("2012-06-19", "2014-03-31") == COUVERTURE_PARTIELLE


def test_gouvernement_en_cours_commence_apres_la_borne_est_couvert():
    # `fin = null` (gouvernement en fonction) n'est jamais remplacé par la
    # date du jour (AGENTS.md §2.5).
    assert statut_couverture_textes("2025-10-13", None) == COUVERTURE_COUVERTE


def test_gouvernement_en_cours_commence_avant_la_borne_est_partiel():
    assert statut_couverture_textes("2010-01-01", None) == COUVERTURE_PARTIELLE


def test_debut_absent_est_indetermine():
    assert statut_couverture_textes(None, "2020-01-01") == COUVERTURE_INDETERMINEE


def test_debut_illisible_est_indetermine():
    assert statut_couverture_textes("hier", "2020-01-01") == COUVERTURE_INDETERMINEE


def test_fin_illisible_est_indeterminee_et_jamais_devinee():
    # Une `fin` présente mais cassée n'est pas assimilée à un mandat en cours.
    assert statut_couverture_textes("2010-01-01", "31/12/2011") == COUVERTURE_INDETERMINEE


def test_debut_avec_horodatage_est_accepte():
    assert statut_couverture_textes("2022-05-21T00:00:00+02:00", None) == COUVERTURE_COUVERTE


# ---------------------------------------------------------------------------
# Alignement avec la copie côté UI
# ---------------------------------------------------------------------------

def test_borne_ui_identique_a_la_borne_python():
    """`pivotAdapter.js` duplique la borne : les deux doivent rester alignées.

    Sans ce test, l'UI pourrait continuer d'afficher « hors couverture » pour
    une période désormais ingérée (ou l'inverse) après ajout d'une archive.
    """
    source = PIVOT_ADAPTER.read_text(encoding="utf-8")
    trouve = re.search(
        r"GOVERNMENT_TEXTS_COVERAGE_START\s*=\s*'(\d{4}-\d{2}-\d{2})'", source
    )

    assert trouve is not None, "GOVERNMENT_TEXTS_COVERAGE_START introuvable dans pivotAdapter.js"
    assert trouve.group(1) == borne_couverture_textes()
