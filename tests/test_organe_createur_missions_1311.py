#!/usr/bin/env python3
"""#1311 — chaque mission d'information publie l'organe qui l'a créée.

Les deux fixtures sont COPIÉES, jamais écrites à la main :

- `tests/fixtures/amo30_organe_createur_1311.zip` : extrait octet pour octet de
  l'archive AMO30 téléchargée le 19/10/2026 — l'acteur `PA2150` (Jean-Luc
  Mélenchon) et les organes qu'il faut pour couvrir les trois cas :

  | Organe | Ce qu'il prouve |
  | --- | --- |
  | `PO744155` (MISINFO) → `PO59047` | une mission d'une commission permanente, résolue (affaires étrangères) |
  | `PO781969` (MISINFO) → `PO59046` | idem, commission de la défense |
  | `PO734384`, `PO771231` (MISINFOPRE) | Conférence des présidents : la source ne nomme aucun parent |
  | `PO825329` (MISINFOPRE), `PO821566` (MISINFOCOM) | idem, XVIe législature, dont une mission commune |

- `tests/fixtures/jean_luc_melenchon_mandats_1311.json` : le bloc `mandats` du
  profil brut et du profil pivot de `public/main` (`a9c3e10b9d`), verbatim — les
  cinq missions qu'il y porte ont été publiées **sans** le champ, et c'est la
  transition vers un run qui le collecte que ce fichier teste.

Aucun test ne lit `raw_data/` ni `pivot_data/`, aucun ne sort sur le réseau.
"""

import io
import json
import shutil
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import candidate_profile as cp  # noqa: E402
from merge_profile import (  # noqa: E402
    backfill_mandat_organe_createur,
    merge_pivot_profile,
    merge_raw_profile,
)
from normalize_profil import _normalize_mandat  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_MOTIFS_ORGANE_CREATEUR_NON_RESOLU,
    _erreur_organe_createur,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ARCHIVE = FIXTURES / "amo30_organe_createur_1311.zip"
CORPUS = FIXTURES / "jean_luc_melenchon_mandats_1311.json"

AFFAIRES_ETRANGERES = {
    "organe_ref": "PO59047",
    "nom": "Commission des affaires étrangères",
    "sigle": "Affaires étrangères",
    "type": "COMPER",
}


@pytest.fixture
def cache_amo30(tmp_path):
    """Le cache disque garni de l'extrait verbatim : aucun téléchargement."""
    shutil.copy(ARCHIVE, tmp_path / "acteurs_historique.zip")
    cp._clear_acteurs_historique_index_memo()
    with patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path):
        yield tmp_path
    cp._clear_acteurs_historique_index_memo()


def _archive_sans(tmp_path: Path, *exclus: str) -> None:
    """Réécrit l'extrait sans certains organes — chaque entrée gardée reste
    verbatim. Sert au cas « parent nommé, introuvable dans le référentiel »."""
    buf = io.BytesIO()
    with zipfile.ZipFile(ARCHIVE) as zi, zipfile.ZipFile(buf, "w") as zo:
        for nom in zi.namelist():
            if not any(nom.endswith(f"/{e}.json") for e in exclus):
                zo.writestr(nom, zi.read(nom))
    (tmp_path / "acteurs_historique.zip").write_bytes(buf.getvalue())


def _missions(mandats):
    return [m for m in mandats if m.get("categorie") == "mission_information"]


# ---------------------------------------------------------------------------
# 1. L'index des organes garde `organeParent`, et son cache est versionné
# ---------------------------------------------------------------------------

def test_l_index_des_organes_garde_le_parent(cache_amo30):
    index = cp._build_organe_index()
    assert index["PO781969"]["parent"] == "PO59046"
    assert index["PO744155"]["parent"] == "PO59047"
    assert index["PO59046"]["parent"] is None  # une commission permanente n'a pas de parent
    assert index["PO821566"]["parent"] is None  # MISINFOCOM
    assert index["PO825329"]["parent"] is None  # MISINFOPRE


def test_un_index_ecrit_avant_1311_n_est_pas_relu(cache_amo30):
    """Un cache porte le code qui l'a écrit : un index `v2`, sans `parent`, lu
    comme s'il en avait un ferait de chaque mission une mission « sans organe
    créateur » — un faux constat. Le nom change, l'ancien fichier est ignoré."""
    assert cp.NOM_INDEX_ORGANES != "index_organes_v2.json"
    (cache_amo30 / "index_organes_v2.json").write_text(
        json.dumps({"PO781969": {"sigle": "x", "nom": "x", "type": "MISINFO"}}), encoding="utf-8"
    )
    assert cp._build_organe_index()["PO781969"]["parent"] == "PO59046"


def test_les_lecteurs_de_l_index_suivent_sa_version():
    import commissions_dossiers_an
    import reprise_mandats_gouvernementaux

    assert reprise_mandats_gouvernementaux.DEFAUT_INDEX_ORGANES.name == cp.NOM_INDEX_ORGANES
    assert cp.NOM_INDEX_ORGANES in (commissions_dossiers_an.__doc__ or "")


# ---------------------------------------------------------------------------
# 2. La résolution, sur les trois cas de la source
# ---------------------------------------------------------------------------

def test_une_mission_de_commission_est_resolue(cache_amo30):
    createur, non_resolu = cp.resoudre_organe_createur(cp.fetch_organe("PO781969"))
    assert createur == {
        "organe_ref": "PO59046",
        "nom": "Commission de la défense nationale et des forces armées",
        "sigle": "Défense",
        "type": "COMPER",
    }
    assert non_resolu is None


@pytest.mark.parametrize("mission", ["PO821566", "PO825329", "PO734384"])
def test_une_mission_sans_parent_le_dit(cache_amo30, mission):
    createur, non_resolu = cp.resoudre_organe_createur(cp.fetch_organe(mission))
    assert createur is None
    assert non_resolu == {"motif": "source_sans_organe_createur"}


def test_un_parent_nomme_mais_introuvable_n_est_pas_confondu(cache_amo30):
    _archive_sans(cache_amo30, "PO59046")
    createur, non_resolu = cp.resoudre_organe_createur(cp.fetch_organe("PO781969"))
    assert createur is None
    assert non_resolu == {"motif": "organe_createur_introuvable", "organe_ref": "PO59046"}
    assert set(KNOWN_MOTIFS_ORGANE_CREATEUR_NON_RESOLU) == {
        "source_sans_organe_createur", "organe_createur_introuvable",
    }


def test_les_mandats_an_portent_l_organe_createur_et_seules_les_missions(cache_amo30):
    mandats = cp._extract_mandats_officiels("PA2150")
    missions = _missions(mandats)
    assert len(missions) == 5
    par_debut = {(m["type"], m["debut"]): m for m in missions}
    assert par_debut[("Co-rapporteur", "2017-10-24")]["organe_createur"] == AFFAIRES_ETRANGERES
    assert "organe_createur_non_resolu" not in par_debut[("Co-rapporteur", "2017-10-24")]
    for cle in [("Membre", "2017-09-21"), ("Président de groupe", "2020-03-30")]:
        assert par_debut[cle]["organe_createur"] is None
        assert par_debut[cle]["organe_createur_non_resolu"] == {"motif": "source_sans_organe_createur"}
    autres = [m for m in mandats if m.get("categorie") != "mission_information"]
    assert autres, "l'extrait doit porter d'autres catégories pour que le test dise quelque chose"
    assert not any("organe_createur" in m for m in autres)


# ---------------------------------------------------------------------------
# 3. Le schéma
# ---------------------------------------------------------------------------

def test_le_validateur_accepte_les_trois_formes():
    base = {"categorie": "mission_information"}
    assert _erreur_organe_createur(base) is None  # collecté avant le lot
    assert _erreur_organe_createur({**base, "organe_createur": AFFAIRES_ETRANGERES}) is None
    assert _erreur_organe_createur({
        **base, "organe_createur": None,
        "organe_createur_non_resolu": {"motif": "source_sans_organe_createur"},
    }) is None


@pytest.mark.parametrize("mandat", [
    {"categorie": "commission", "organe_createur": AFFAIRES_ETRANGERES},
    {"categorie": "mission_information", "organe_createur": None},
    {"categorie": "mission_information", "organe_createur": None,
     "organe_createur_non_resolu": {"motif": "inconnu"}},
    {"categorie": "mission_information", "organe_createur": None,
     "organe_createur_non_resolu": {"motif": "organe_createur_introuvable"}},
    {"categorie": "mission_information", "organe_createur": AFFAIRES_ETRANGERES,
     "organe_createur_non_resolu": {"motif": "source_sans_organe_createur"}},
    {"categorie": "mission_information", "organe_createur": {"nom": "Commission des affaires étrangères"}},
    {"categorie": "mission_information", "organe_createur": {**AFFAIRES_ETRANGERES, "organe_ref": ""}},
    {"categorie": "mission_information",
     "organe_createur_non_resolu": {"motif": "source_sans_organe_createur"}},
])
def test_le_validateur_refuse_les_formes_fausses(mandat):
    assert _erreur_organe_createur(mandat)


def test_validate_profil_rapporte_l_erreur():
    from schema_pivot import validate_profil

    profil = {"mandats": [{"categorie": "commission", "label": "x", "organe_createur": None}]}
    assert any("organe_createur" in e for e in validate_profil(profil))


def test_la_normalisation_recopie_le_champ_sur_les_seules_missions():
    neuf = {"categorie": "mission_information", "type": "Membre", "label": "x", "debut": "2023-01-01",
            "organe_createur": None, "organe_createur_non_resolu": {"motif": "source_sans_organe_createur"}}
    pivot = _normalize_mandat(neuf)
    assert pivot["organe_createur"] is None
    assert pivot["organe_createur_non_resolu"] == {"motif": "source_sans_organe_createur"}
    assert "organe_createur" not in _normalize_mandat({"categorie": "mission_information", "label": "x"})
    assert "organe_createur" not in _normalize_mandat({**neuf, "categorie": "commission"})


# ---------------------------------------------------------------------------
# 4. La transition : un profil publié SANS le champ, puis un run qui le collecte
# ---------------------------------------------------------------------------

def test_le_champ_atteint_les_missions_deja_publiees_aux_deux_etages(cache_amo30):
    """Les cinq missions de `jean-luc-melenchon`, publiées sans le champ sur
    `public/main`, le reçoivent au run suivant — au brut ET au pivot, la seule
    couche que `web/` lit. Sans `backfill_mandat_organe_createur`, l'entrée
    ancienne gagne (la clé ne contient pas le champ) et rien n'arrive."""
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    ancien_brut, ancien_pivot = corpus["brut"], corpus["pivot"]
    assert all("organe_createur" not in m for m in ancien_brut["mandats"] + ancien_pivot["mandats"])

    neuf_brut = {"mandats": cp._extract_mandats_officiels("PA2150")}
    brut = merge_raw_profile(ancien_brut, neuf_brut)
    assert len(brut["mandats"]) == len(ancien_brut["mandats"]), "aucune mission publiée deux fois"

    neuf_pivot = {"mandats": [_normalize_mandat(m) for m in brut["mandats"]]}
    pivot = merge_pivot_profile(ancien_pivot, neuf_pivot)
    assert len(pivot["mandats"]) == len(ancien_pivot["mandats"])

    for couche in (brut, pivot):
        missions = _missions(couche["mandats"])
        assert len(missions) == 5
        assert all("organe_createur" in m for m in missions)
        resolues = [m for m in missions if m["organe_createur"] is not None]
        assert [m["organe_createur"] for m in resolues] == [AFFAIRES_ETRANGERES] * 2
        assert all(
            m["organe_createur_non_resolu"] == {"motif": "source_sans_organe_createur"}
            for m in missions if m["organe_createur"] is None
        )
        assert all(_erreur_organe_createur(m) is None for m in couche["mandats"])
        assert not any("organe_createur" in m for m in couche["mandats"]
                       if m.get("categorie") != "mission_information")


def test_le_report_ne_retire_jamais_un_organe_resolu():
    cle = lambda m: (m.get("categorie"), m.get("label"))  # noqa: E731
    publie = [{"categorie": "mission_information", "label": "x", "organe_createur": AFFAIRES_ETRANGERES}]
    neuf = [{"categorie": "mission_information", "label": "x", "organe_createur": None,
             "organe_createur_non_resolu": {"motif": "organe_createur_introuvable", "organe_ref": "PO59047"}}]
    assert backfill_mandat_organe_createur(publie, neuf, cle) == publie


def test_le_report_resout_une_mission_publiee_non_resolue():
    cle = lambda m: (m.get("categorie"), m.get("label"))  # noqa: E731
    publie = [{"categorie": "mission_information", "label": "x", "organe_createur": None,
               "organe_createur_non_resolu": {"motif": "organe_createur_introuvable", "organe_ref": "PO59047"}}]
    neuf = [{"categorie": "mission_information", "label": "x", "organe_createur": AFFAIRES_ETRANGERES}]
    assert backfill_mandat_organe_createur(publie, neuf, cle) == [
        {"categorie": "mission_information", "label": "x", "organe_createur": AFFAIRES_ETRANGERES}
    ]


def test_une_mission_qu_aucune_collecte_ne_couvre_reste_sans_cle():
    cle = lambda m: (m.get("categorie"), m.get("label"))  # noqa: E731
    publie = [{"categorie": "mission_information", "label": "ancienne"}]
    neuf = [{"categorie": "mission_information", "label": "autre", "organe_createur": AFFAIRES_ETRANGERES}]
    assert backfill_mandat_organe_createur(publie, neuf, cle) == publie
