"""#1029 — la parole des membres de roster publie un EXTRAIT de 280 caractères.

Arbitré le 22/09/2026 : « un extrait de 280 » pour tous les profils de groupes
et de gouvernement, le texte entier restant chez l'Assemblée (#1087). Trois
formes désormais, et un ordre : réduite au thème (#657) < extrait < complète.

L'entrée est RÉELLE : une intervention de Gabriel Attal du 20/07/2026, lue
dans son profil brut publié ; ses formes réduites sont celles que produisent
les vraies fonctions de `candidate_profile`.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from candidate_profile import _reduire_a_l_extrait, _reduire_au_theme  # noqa: E402
from merge_profile import aligner_collecte_reduite, merge_pivot_profile, merge_raw_profile  # noqa: E402
from normalize_profil import _normalize_intervention  # noqa: E402
from schema_pivot import EXTRAIT_TEXTE_CARACTERES, extrait_de_texte  # noqa: E402

#: Les 504 premiers caractères RÉELS du verbatim (1 877 au total), coupés
#: après une phrase entière.
TEXTE = ('Je voudrais d’abord rebondir sur certains propos d’une collègue de LFI qui a parlé d’hum'
         'iliation à propos des députés de mon groupe qui avaient déposé un amendement. Je tiens à'
         ' lui dire qu’on ne grandit pas le Parlement quand on cherche par ses propos à humilier d'
         'es collègues qui ont déposé un amendement, surtout quand on prétend défendre la même cau'
         'se. (Applaudissements sur plusieurs bancs du groupe EPR. – M. Éric Martineau applaudit é'
         'galement. – Exclamations sur plusieurs bancs du groupe LFI-NFP.)')
COMPLETE = {
    "id": "syceron_CRSANR5L17S2026E1N022_000399", "date": "2026-07-20", "type_detail": "debat",
    "sujet": "Protection et souveraineté agricoles", "texte": TEXTE,
    "fonction": None, "format": "prise_de_parole_developpee", "mots_cles": [],
    "source": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut",
    "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut",
    "url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut",
    "url_detail": None, "source_id": "CRSANR5L17S2026E1N022", "seance_ref": "RUANR5L17S2026IDS30879",
    "session_ref": "SCR5A2026E1", "orateur_id_source": "PA722190", "orateur_nom": "M. Gabriel Attal",
    "point_ordre_du_jour": "Protection et souveraineté agricoles", "point_code_grammaire": "DISC_ARTICLES_1_1",
    "etat_compte_rendu": "complet", "version_compte_rendu": "avant_JO", "legislature": "17",
    "sujet_code_grammaire": "TITRE_TEXTE_DISCUSSION",
}
THEME = _reduire_au_theme(COMPLETE)
EXTRAIT = _reduire_a_l_extrait(COMPLETE)


def _brut(interventions, forme=None):
    meta = {"collecte_reduite": {"interventions": forme}} if forme else {}
    return {"slug": "x", "votes": [], "mandats": [], "dossiers_legislatifs": [],
            "interventions": interventions, "meta": meta}


# ── L'extrait ─────────────────────────────────────────────────────────────

def test_l_extrait_s_arrete_en_fin_de_phrase_sans_rien_ajouter():
    extrait, tronque = extrait_de_texte(TEXTE)

    assert tronque
    assert len(extrait) <= EXTRAIT_TEXTE_CARACTERES
    assert extrait.endswith("qui avaient déposé un amendement.")
    assert TEXTE.startswith(extrait)


def test_un_texte_court_est_publie_entier_et_non_tronque():
    assert extrait_de_texte("Très bien.") == ("Très bien.", False)


def test_sans_fin_de_phrase_la_coupe_tombe_entre_deux_mots():
    extrait, tronque = extrait_de_texte("mot " * 100)

    assert tronque and not extrait.endswith(" ") and extrait.endswith("mot")


def test_la_forme_extrait_garde_le_theme_et_ajoute_l_extrait():
    assert EXTRAIT["collecte"] == "extrait"
    assert EXTRAIT["texte_tronque"] is True
    assert {k: v for k, v in EXTRAIT.items() if k not in ("texte", "texte_tronque", "collecte")} == {
        k: v for k, v in THEME.items() if k != "collecte"}


def test_une_entree_deja_reduite_n_est_pas_recoupee():
    assert _reduire_a_l_extrait(EXTRAIT) == EXTRAIT
    assert _reduire_a_l_extrait(THEME) == THEME


def test_l_etage_pivot_publie_l_extrait_et_son_drapeau():
    pivot = _normalize_intervention(dict(EXTRAIT))

    assert pivot["texte"] == EXTRAIT["texte"]
    assert pivot["texte_tronque"] is True
    assert pivot["collecte"] == "extrait"
    assert "fonction" not in pivot


# ── La fusion : une forme plus riche remplace une plus pauvre, jamais l'inverse ──

def test_une_entree_reduite_au_theme_recoit_l_extrait():
    merged = merge_raw_profile(_brut([dict(THEME)], "theme_seul"), _brut([dict(EXTRAIT)], "extrait"))

    (entree,) = merged["interventions"]
    assert entree["collecte"] == "extrait"
    assert merged["meta"]["collecte_reduite"] == {"interventions": "extrait"}


def test_une_forme_complete_n_est_jamais_remplacee_par_un_extrait():
    merged = merge_raw_profile(_brut([dict(COMPLETE)]), _brut([dict(EXTRAIT)], "extrait"))

    (entree,) = merged["interventions"]
    assert entree["texte"] == TEXTE
    assert "collecte_reduite" not in merged["meta"]


def test_la_declaration_dit_la_forme_la_plus_pauvre_encore_publiee():
    autre = {**THEME, "id": "syceron_CRSANR5L17S2026E1N022_000400"}
    profil = aligner_collecte_reduite(_brut([dict(EXTRAIT), autre], "extrait"))

    assert profil["meta"]["collecte_reduite"] == {"interventions": "theme_seul"}


def test_l_etage_pivot_recoit_aussi_l_extrait():
    ancien = _normalize_intervention(dict(THEME))
    neuf = _normalize_intervention(dict(EXTRAIT))
    old = {"id": "x", "interventions": [ancien], "votes": [], "mandats": [],
           "meta": {"collecte_reduite": {"interventions": "theme_seul"}}, "sources": []}
    new = {"id": "x", "interventions": [neuf], "votes": [], "mandats": [],
           "meta": {"collecte_reduite": {"interventions": "extrait"}}, "sources": []}

    merged = merge_pivot_profile(old, new)

    (entree,) = merged["interventions"]
    assert entree["texte"] == EXTRAIT["texte"]
