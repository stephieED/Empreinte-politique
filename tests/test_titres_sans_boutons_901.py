"""#901 — le titre d'une activité européenne perd les boutons de la page scrapée.

ParlTrack ne lit aucune base du Parlement : il recopie la page, et ramasse avec
le titre les boutons de téléchargement du document. Mesuré le 15/09/2026 sur le
dump `ep_mep_activities` : **27 576 des 40 146** titres d'activités portées
(68,7 %), et 7 des 13 types d'activité — dont les questions écrites, à 68,1 %.

Retirer cette queue n'ôte aucun fait : « PDF (235 KB) » est le libellé d'un
bouton, pas une information sur le texte. C'est ce qui autorise à toucher un
verbatim de source (§2 règle 2), et le `source_url` publié mène toujours à la
page d'origine.

**Deux autres traces du scraping ne sont PAS corrigées**, et ces tests le
verrouillent : l'intitulé répété deux fois, et les espaces manquants aux
jointures. Aucune règle ne les distingue d'un titre légitimement redondant ou
d'un mot composé ; les réparer serait reconstruire un intitulé que personne n'a
écrit.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

from parltrack_dumps import (  # noqa: E402
    VERSION_SCHEMA_INDEX,
    build_activities_index,
    titre_sans_boutons,
)
from test_parltrack_dumps import _write_zst_file  # noqa: E402


# --------------------------------------------------------------------------
# Ce qui part
# --------------------------------------------------------------------------

@pytest.mark.parametrize("brut,propre", [
    ("Motion for a resolution on accessibility of goods and services PDF (181 KB) DOC (45 KB)",
     "Motion for a resolution on accessibility of goods and services"),
    ("MOTION FOR A RESOLUTION on ‘Jean Monnet’ activities PDF (236 KB) DOC (47 KB)",
     "MOTION FOR A RESOLUTION on ‘Jean Monnet’ activities"),
    ("Report on X DOCX (1 024 KB)", "Report on X DOCX (1 024 KB)"),
    ("Report on X PDF (1.5 MB)", "Report on X"),
    ("Report on X pdf (235 kb)", "Report on X"),
])
def test_la_queue_de_boutons_est_retiree(brut, propre):
    assert titre_sans_boutons(brut) == propre


def test_un_titre_sans_queue_est_rendu_tel_quel():
    titre = "Report on the future budgetary requirements for external actions"

    assert titre_sans_boutons(titre) == titre


def test_un_titre_absent_devient_la_chaine_vide():
    """Le champ existait déjà à `\"\"` quand la source ne donne rien : on ne le
    fait pas basculer à `None`, ce qu'aucun consommateur n'attend."""
    assert titre_sans_boutons(None) == ""
    assert titre_sans_boutons("") == ""


# --------------------------------------------------------------------------
# Ce qui RESTE — la limite est déclarée, pas réparée
# --------------------------------------------------------------------------

def test_un_intitule_repete_nest_pas_deduplique():
    """« MOTION OF CENSURE ON THE COMMISSION » deux fois d'affilée : la source
    a concaténé deux nœuds. Aucune règle ne distingue cela d'un titre
    légitimement redondant."""
    brut = ("MOTION OF CENSURE ON THE COMMISSION MOTION OF CENSURE ON THE COMMISSION "
            "PDF (268 KB) DOC (71 KB)")

    assert titre_sans_boutons(brut) == (
        "MOTION OF CENSURE ON THE COMMISSION MOTION OF CENSURE ON THE COMMISSION")


def test_les_espaces_manquants_aux_jointures_restent():
    """« RESOLUTIONpursuant », « Procedureon » : les insérer supposerait de
    savoir où finit un mot, donc de reconstruire."""
    brut = "MOTION FOR A RESOLUTIONpursuant to Rule 133 of the Rules of Procedureon the funding"

    assert titre_sans_boutons(brut) == brut


def test_le_mot_pdf_seul_ne_declenche_rien():
    """La règle exige un type, une taille chiffrée et une unité. Un titre qui
    parle de PDF n'est pas du balisage."""
    titre = "Report on the accessibility of PDF documents for visually impaired users"

    assert titre_sans_boutons(titre) == titre


# --------------------------------------------------------------------------
# De bout en bout : c'est la PROJECTION qui nettoie, une seule fois
# --------------------------------------------------------------------------

def test_le_nettoyage_a_lieu_a_l_indexation(tmp_path):
    """Nettoyer plus loin laisserait chaque consommateur réinventer sa règle."""
    dump = tmp_path / "ep_mep_activities.json.zst"
    _write_zst_file(dump, [{
        "mep_id": 131580,
        "REPORT": [{"date": "2022-10-04T00:00:00", "term": 9,
                    "title": "Report on the situation of X PDF (268 KB) DOC (71 KB)",
                    "dossiers": ["2022/2852(RSP)"]}],
        "WQ": [{"date": "2021-03-09T00:00:00", "term": 9,
                "title": "Question on fisheries PDF (94 KB)"}],
    }])

    from unittest.mock import patch
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_activities_index(perimetre=frozenset({131580}))

    assert index[131580]["rapport"][0]["titre"] == "Report on the situation of X"
    assert index[131580]["question_ecrite"][0]["titre"] == "Question on fisheries"


def test_la_version_de_schema_a_ete_incrementee():
    """Sans elle, l'index caché resservirait les titres pollués une semaine
    entière — le même piège qu'au passage de 2 à 3."""
    assert VERSION_SCHEMA_INDEX >= 4
