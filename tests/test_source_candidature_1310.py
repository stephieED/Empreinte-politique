"""#1310 — l'attestation d'une candidature n'est pas une source de l'Assemblée.

Mesuré le 19/10/2026 sur les 43 profils `candidat_declare` : 20 portaient sous
le type `assemblee_nationale` l'article de presse — ou la page Wikipédia — qui
atteste leur candidature, et publiaient donc la licence de l'Assemblée sans en
porter une donnée. En corrigeant, un second trou : les mandats locaux (#922)
n'avaient pas d'entrée `sources[]`, et leur licence n'était dite nulle part.

FIXTURES. Recopiées du corpus du 21/10/2026 (`raw_data/profiles/` et
`pivot_data/profiles/` au commit de données `85f898a614`) : le profil brut de
`juan-branco` (sans mandat), le bloc `mandats_locaux` de `david-lisnard` réduit
à un mandat, et les entrées `sources[]` publiées de ces deux fiches.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import generate_all_profiles as gap  # noqa: E402
from licences import LICENCE_AN, LICENCE_RNE, est_url_assemblee  # noqa: E402
from merge_profile import _merge_pivot_sources, est_source_mal_typee, merge_pivot_profile  # noqa: E402
from normalize_profil import normalize_profil  # noqa: E402
from schema_pivot import KNOWN_SOURCE_TYPES  # noqa: E402

ARTICLE_BRANCO = ("https://www.nouvelobs.com/politique/20261015.OBS119225/"
                  "presidentielle-2027-quels-sont-les-31-candidats-actuellement-declares.html")
ARTICLE_LISNARD = ("https://www.france24.com/fr/france/20260524-france-presidentielle-2027-"
                   "qui-sont-les-candidats-officiellement-declares")
RNE = "https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1"


def _brut_branco() -> dict:
    return {
        "slug": "juan-branco",
        "chambre": None,
        "source": ARTICLE_BRANCO,
        "identite": {
            "nom_complet": "Juan Branco", "groupe_sigle": None, "groupe_nom": "Les Ruches",
            "profession": None, "date_naissance": None, "num_circo": None, "nb_mandats": None,
            "url_an_ou_senat": None,
        },
        "mandats": [], "votes": [], "votes_source": None, "dossiers_legislatifs": [],
        "interventions": [], "amendements": [],
        "meta": {"genere_le": "2026-10-21T20:09:19+0000", "warnings": []},
        "mandats_locaux": {
            "source": RNE, "synchro_le": "2026-10-18T16:30:26+0000", "borne_couverture": "2020",
            "appariement": "aucun_mandat_trouve", "mandats": [],
        },
    }


def _bloc_local_lisnard() -> dict:
    return {
        "source": RNE, "synchro_le": "2026-10-18T16:30:26+0000", "borne_couverture": "2020",
        "appariement": "table_relue",
        "mandats": [{
            "label": "Ca Cannes Pays De Lerins", "categorie": "mandat_local", "categorie_source": "rne",
            "type_organe_source": "conseil_communautaire", "fonction": "Président du conseil communautaire",
            "debut": "2026-03-15", "fin": None, "actif": True, "source_url": RNE,
            "fin_non_resolue": {"motif": "source_sans_date_de_fin", "constate_le": "2026-02-27"},
            "debut_fonction": "2026-04-03",
        }],
    }


def _publie(slug: str, url: str) -> dict:
    """L'entrée `sources[]` que la fiche publiait le 21/10/2026."""
    return {"type": "assemblee_nationale", "url": url, "synchro_le": "2026-10-21T16:38:18+0000"}


# ── Le normaliseur ────────────────────────────────────────────────────────────

def test_un_article_de_presse_n_est_pas_type_assemblee_nationale():
    pivot = normalize_profil(_brut_branco(), provenance="candidat_declare")

    assert pivot["sources"] == []
    assert pivot["meta"]["licence_donnees"] == ""


def test_une_url_de_l_assemblee_reste_une_source_de_l_assemblee():
    brut = _brut_branco()
    brut["source"] = "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA722190"
    pivot = normalize_profil(brut, provenance="candidat_declare")

    assert [s["type"] for s in pivot["sources"]] == ["assemblee_nationale"]
    assert pivot["meta"]["licence_donnees"] == LICENCE_AN


def test_wikipedia_n_atteint_aucune_source():
    """AGENTS.md §7 : Wikipédia (CC BY-SA) ne va dans aucun `sources[]`."""
    brut = _brut_branco()
    brut["source"] = "https://fr.wikipedia.org/wiki/Candidatures_à_l'élection_présidentielle_française_de_2027"

    assert normalize_profil(brut, provenance="candidat_declare")["sources"] == []


def test_les_trois_hotes_de_l_assemblee_sont_reconnus():
    for url in ("https://data.assemblee-nationale.fr/", "https://www.assemblee-nationale.fr/dyn/17",
                "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA1"):
        assert est_url_assemblee(url)
    for url in (ARTICLE_BRANCO, "https://www.nosdeputes.fr/x", "https://assemblee-nationale.fr.example.com/",
                None, ""):
        assert not est_url_assemblee(url)


# ── Les mandats locaux déclarent leur source ──────────────────────────────────

def test_les_mandats_locaux_portent_leur_source_et_leur_licence():
    pivot = normalize_profil(_brut_branco(), provenance="candidat_declare")
    brut = {"mandats_locaux": _bloc_local_lisnard()}
    gap._verser_mandats_locaux(brut, pivot)

    assert pivot["sources"] == [{"type": "rne", "url": RNE, "synchro_le": "2026-10-18T16:30:26+0000"}]
    assert pivot["meta"]["licence_donnees"] == LICENCE_RNE
    assert "rne" in KNOWN_SOURCE_TYPES


def test_un_bloc_sans_mandat_n_ajoute_aucune_source():
    """« Relu, aucun mandat » publie sa couverture, pas une source sans donnée."""
    pivot = normalize_profil(_brut_branco(), provenance="candidat_declare")
    gap._verser_mandats_locaux(_brut_branco(), pivot)

    assert pivot["sources"] == []
    assert pivot["mandats_locaux_couverture"]["appariement"] == "aucun_mandat_trouve"


def test_un_profil_minimal_n_annonce_plus_la_licence_de_l_assemblee():
    profil = gap.build_minimal_profile("Juan Branco", "juan-branco", {"source": ARTICLE_BRANCO})

    assert profil["meta"]["licence_donnees"] == ""


# ── Le retrait, à la fusion ───────────────────────────────────────────────────

def test_la_fusion_retire_l_entree_publiee_mal_typee():
    """L'union par type garderait l'entrée publiée indéfiniment : le retrait
    s'écrit (AGENTS.md §7)."""
    ancien = [_publie("david-lisnard", ARTICLE_LISNARD)]
    neuf = [{"type": "rne", "url": RNE, "synchro_le": "2026-10-22T10:00:00+0000"}]

    assert _merge_pivot_sources(ancien, neuf) == neuf


def test_le_retrait_ne_touche_ni_une_source_de_l_assemblee_ni_une_entree_sans_url():
    vraie = _publie("gabriel-attal", "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA722190")
    sans_url = {"type": "assemblee_nationale", "url": None, "synchro_le": None}

    assert not est_source_mal_typee(vraie)
    assert not est_source_mal_typee(sans_url)
    assert est_source_mal_typee(_publie("juan-branco", ARTICLE_BRANCO))


def test_une_fiche_publiee_sans_donnee_perd_sa_licence_au_run_suivant():
    neuf = normalize_profil(_brut_branco(), provenance="candidat_declare")
    ancien = copy.deepcopy(neuf)
    ancien["sources"] = [_publie("juan-branco", ARTICLE_BRANCO)]
    ancien["meta"]["licence_donnees"] = LICENCE_AN

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["sources"] == []
    assert fusionne["meta"]["licence_donnees"] == ""
