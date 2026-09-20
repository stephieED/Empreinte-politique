"""L'index des documents européens et leurs matières EuroVoc (#901).

`dossiers_europeens.json` porte la matière d'un DOSSIER. Or 628 des 694 textes
portés européens n'en citent aucun : ce sont des résolutions déposées en séance,
qui n'ouvrent pas de procédure — donc ni commission au fond, ni entrée dans
l'index des dossiers. L'axe thématique plafonnait à 66 textes sur 694.

Le portail les classe pourtant : `is_about` rend 2 à 9 concepts EuroVoc par
document. Les libellés, eux, viennent d'EuroVoc (Office des publications,
CC BY 4.0), résolus par SPARQL et par LOTS.

Ce que ces tests tiennent surtout, ce sont les trois façons de ne pas avoir de
matière — et le fait qu'elles ne se confondent pas (§2 règle 5) :
  portail_non_interroge       : la question n'a pas pu être posée
  source_sans_concept         : le portail répond, et ne classe pas ce document
  libelle_eurovoc_introuvable : le concept existe, son libellé manque
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from documents_europeens import (  # noqa: E402
    LibellesEurovocIndisponibles,
    construire,
    document,
    references_documents,
    resoudre_libelles,
    uri_eurovoc,
)


@pytest.fixture(autouse=True)
def _sans_attente(monkeypatch):
    """Les nouveaux essais SPARQL attendent 5 puis 20 s : pas dans les tests."""
    import documents_europeens
    monkeypatch.setattr(documents_europeens, "ATTENTES_SPARQL", (0, 0))


class _ReponseSparql:
    def __init__(self, bindings, status_code=200):
        self.status_code = status_code
        self._bindings = bindings

    def json(self):
        return {"results": {"bindings": self._bindings}}


class _SessionSparql:
    """Rejoue EuroVoc : un libellé pour les concepts qu'il connaît, et, à la
    requête des domaines (celle qui cite `ev:domain`), le ou les domaines de
    chacun, dans la forme que le point SPARQL rend réellement (17/09/2026)."""

    def __init__(self, libelles, status_code=200, domaines=None):
        self.libelles = libelles
        self.domaines = domaines or {}
        self.status_code = status_code
        self.requetes = []

    def get(self, url, params=None, headers=None, timeout=None):
        requete = params["query"]
        self.requetes.append(requete)
        if "ev:domain" in requete:
            return _ReponseSparql([
                {"c": {"value": uri_eurovoc(c)}, "dn": {"value": code}, "dl": {"value": libelle}}
                for c, doms in self.domaines.items() if f"<{uri_eurovoc(c)}>" in requete
                for code, libelle in doms
            ], self.status_code)
        demandes = [c for c in self.libelles if f"<{uri_eurovoc(c)}>" in requete]
        return _ReponseSparql([
            {"c": {"value": uri_eurovoc(c)}, "l": {"value": self.libelles[c]}} for c in demandes
        ], self.status_code)


class _Resolveur:
    def __init__(self, concepts):
        self.concepts = concepts

    def concepts_eurovoc(self, doceo):
        return self.concepts.get(doceo)


# --- le périmètre -----------------------------------------------------------

def _profil(tmp_path, nom, textes):
    (tmp_path / f"{nom}.pivot.json").write_text(
        json.dumps({"textes_portes": textes}), encoding="utf-8")


def test_les_references_viennent_du_source_url_publie(tmp_path):
    """Jamais reconstruites d'un titre : c'est l'adresse que #827 a vérifiée."""
    _profil(tmp_path, "a", [
        {"institution": "parlement_europeen",
         "source_url": "https://www.europarl.europa.eu/doceo/document/RC-9-2024-0227_EN.html"},
        {"institution": "parlement_europeen",
         "source_url": "https://www.europarl.europa.eu/doceo/document/B-8-2015-0293_FR.html"},
    ])
    assert references_documents(tmp_path) == {"RC-9-2024-0227", "B-8-2015-0293"}


def test_les_deux_schemas_d_url_sont_lus(tmp_path):
    """Le piège de ce lot, et il ne s'annonçait par aucune erreur.

    Mesuré le 16/09/2026 : **625** `source_url` de textes portés européens sont
    en `http://`, **56** en `https://`. Un filtre sur la seule forme moderne
    rendait 56 documents au lieu de 335 — sans erreur, sans avertissement, et
    avec un index qui aurait eu l'air de fonctionner.
    """
    _profil(tmp_path, "a", [
        {"institution": "parlement_europeen",
         "source_url": "http://www.europarl.europa.eu/doceo/document/B-8-2015-0293_EN.html"},
        {"institution": "parlement_europeen",
         "source_url": "https://www.europarl.europa.eu/doceo/document/RC-9-2024-0227_EN.html"},
    ])
    assert references_documents(tmp_path) == {"B-8-2015-0293", "RC-9-2024-0227"}


def test_un_texte_francais_ou_sans_url_n_entre_pas(tmp_path):
    _profil(tmp_path, "b", [
        {"institution": None, "source_url": "https://www.assemblee-nationale.fr/x"},
        {"institution": "parlement_europeen", "source_url": None},
        {"institution": "parlement_europeen", "source_url": "https://exemple.org/autre"},
    ])
    assert references_documents(tmp_path) == set()


def test_un_document_cite_par_deux_profils_n_entre_qu_une_fois(tmp_path):
    """628 occurrences pour 279 documents : c'est la raison d'être de l'index."""
    url = "https://www.europarl.europa.eu/doceo/document/RC-9-2024-0227_EN.html"
    _profil(tmp_path, "a", [{"institution": "parlement_europeen", "source_url": url}])
    _profil(tmp_path, "b", [{"institution": "parlement_europeen", "source_url": url}])
    assert references_documents(tmp_path) == {"RC-9-2024-0227"}


# --- la résolution des libellés ---------------------------------------------

def test_les_libelles_sont_demandes_par_lots():
    session = _SessionSparql({str(i): f"c{i}" for i in range(250)})
    libelles = resoudre_libelles([str(i) for i in range(250)], session, lot=100)
    assert len(libelles) == 250
    assert len(session.requetes) == 3, "250 concepts en 3 requêtes, pas 250"


def test_un_concept_sans_libelle_n_est_pas_invente():
    session = _SessionSparql({"2155": "opposition politique"})
    assert resoudre_libelles(["2155", "9999"], session) == {"2155": "opposition politique"}


def test_eurovoc_injoignable_leve_plutot_que_de_publier_des_codes_nus():
    class _Muet:
        def get(self, *a, **k):
            raise TimeoutError("silence")

    with pytest.raises(LibellesEurovocIndisponibles):
        resoudre_libelles(["2155"], _Muet())


def test_un_statut_inattendu_leve_aussi():
    with pytest.raises(LibellesEurovocIndisponibles):
        resoudre_libelles(["2155"], _SessionSparql({"2155": "x"}, status_code=503))


# --- les entrées d'index ----------------------------------------------------

def test_un_document_classe_porte_ses_matieres():
    entrees = construire(
        ["RC-9-2024-0227"],
        _Resolveur({"RC-9-2024-0227": ["2155", "5454"]}),
        _SessionSparql({"2155": "opposition politique", "5454": "Azerbaïdjan"}),
    )
    assert [(m["code"], m["libelle"]) for m in entrees[0]["matieres"]] == [
        ("2155", "opposition politique"),
        ("5454", "Azerbaïdjan"),
    ]
    assert "matieres_non_resolu" not in entrees[0]


@pytest.mark.parametrize("concepts, motif", [
    (None, "portail_non_interroge"),
    ([], "source_sans_concept"),
])
def test_les_deux_absences_ne_se_confondent_pas(concepts, motif):
    """Ne pas avoir pu demander n'est pas savoir qu'il n'y a rien."""
    entrees = construire(["X-9-2024-0001"], _Resolveur({"X-9-2024-0001": concepts}),
                         _SessionSparql({}))
    assert entrees[0]["matieres"] == []
    assert entrees[0]["matieres_non_resolu"]["motif"] == motif


def test_un_libelle_manquant_est_declare_sans_perdre_les_autres():
    entrees = construire(
        ["X-9-2024-0001"],
        _Resolveur({"X-9-2024-0001": ["2155", "9999"]}),
        _SessionSparql({"2155": "opposition politique"}),
    )
    assert [(m["code"], m["libelle"]) for m in entrees[0]["matieres"]] == [
        ("2155", "opposition politique")]
    assert entrees[0]["matieres_non_resolu"] == {
        "motif": "libelle_eurovoc_introuvable", "codes": ["9999"]}


def test_aucune_entree_sans_matiere_ni_motif():
    entrees = construire(
        ["A", "B", "C"],
        _Resolveur({"A": ["2155"], "B": [], "C": None}),
        _SessionSparql({"2155": "opposition politique"}),
    )
    for e in entrees:
        assert e["matieres"] or e.get("matieres_non_resolu"), e


def test_l_entete_nomme_les_deux_licences():
    doc = document([])
    assert doc["schema_version"] == "documents-europeens-v2"
    assert "CC BY 4.0" in doc["licence_donnees"]
    assert "data.europarl.europa.eu" in doc["licence_donnees"]
