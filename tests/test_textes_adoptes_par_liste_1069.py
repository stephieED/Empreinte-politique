"""#1069 — les textes adoptés se lisent par liste annuelle, plus un par un.

La passe document par document obtenait ~650 réponses par run, et commençait
par les dossiers de 1992, que le portail ne classe pas. La liste annuelle
`/adopted-texts?year=…` rend `is_about` pour 200 textes par page : 5 196 textes
en 35 requêtes, mesuré le 21/09/2026, identiques à la requête unitaire sur 10
textes tirés au hasard.

Les deux textes viennent de la liste RÉELLE de 2021, réduits aux champs lus :
`TA-9-2021-0460` (8 concepts) et `TA-9-2021-0358` (non classé). Le résolveur est
le vrai `ResolveurDocuments` ; seule la session HTTP est rejouée.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

import documents_europeens  # noqa: E402
import europarl_documents  # noqa: E402
from dossiers_europeens import domaines_des_dossiers  # noqa: E402
from europarl_documents import ResolveurDocuments  # noqa: E402
from test_documents_europeens_901 import _SessionSparql  # noqa: E402

TA_CLASSE = {
    "identifier": "TA-9-2021-0460",
    "is_about": ["http://eurovoc.europa.eu/6030", "http://eurovoc.europa.eu/4258",
                 "http://eurovoc.europa.eu/937", "http://eurovoc.europa.eu/1005",
                 "http://eurovoc.europa.eu/1895", "http://eurovoc.europa.eu/4298",
                 "http://eurovoc.europa.eu/5787", "http://eurovoc.europa.eu/4257"],
    "title_dcterms": {"fr": "Statistiques intégrées sur les exploitations agricoles: contribution "
                            "de l’Union au titre du cadre financier 2021-2027 ***I"},
}
TA_NON_CLASSE = {
    "identifier": "TA-9-2021-0358",
    "title_dcterms": {"fr": "Examen du cadre législatif macroéconomique "},
}
#: Domaines que le thésaurus rendrait — ici, un seul suffit à la preuve.
DOMAINES = {c.rsplit("/", 1)[-1]: [("56", "56 AGRICULTURE, SYLVICULTURE ET PÊCHE")]
            for c in TA_CLASSE["is_about"]}
RAPPORT = {"data": [{"id": "eli/dl/doc/A-9-2021-0150", "is_about": ["http://eurovoc.europa.eu/6030"]}]}


class _Reponse:
    def __init__(self, status_code, charge=None):
        self.status_code, self._charge, self.headers = status_code, charge, {}

    def json(self):
        return self._charge


class _Portail:
    """La liste annuelle par `year`/`offset`, et les documents un par un."""

    def __init__(self, listes=None, documents=None, pannes=0):
        self.listes = listes or {}
        self.documents = documents or {}
        self.pannes = pannes
        self.pages = []
        self.demandes = []

    def get(self, url, params=None, timeout=None):
        if url.endswith("/adopted-texts"):
            self.pages.append((params["year"], params["offset"]))
            if self.pannes:
                self.pannes -= 1
                return _Reponse(404)
            textes = self.listes.get(params["year"])
            if not textes:
                return _Reponse(204)
            debut = params["offset"]
            return _Reponse(200, {"data": textes[debut:debut + params["limit"]]})
        doceo = url.rsplit("/", 1)[-1]
        self.demandes.append(doceo)
        if doceo in self.documents:
            return _Reponse(200, self.documents[doceo])
        return _Reponse(404)


@pytest.fixture(autouse=True)
def _sans_attente(monkeypatch):
    monkeypatch.setattr(europarl_documents, "PAUSE_ENTRE_REQUETES", 0)
    monkeypatch.setattr(europarl_documents, "PAUSE_REESSAI_LISTE", 0)
    monkeypatch.setattr(documents_europeens, "ATTENTES_SPARQL", (0, 0))


def _passe(tmp_path, portail, documents, **options):
    entrees = [{"reference": r, "familles": []} for r in documents]
    resolveur = ResolveurDocuments(cache_path=tmp_path / "cache.json", session=portail)
    compteurs = domaines_des_dossiers(entrees, documents, resolveur,
                                      _SessionSparql({}, domaines=DOMAINES), **options)
    return {e["reference"]: e for e in entrees}, resolveur, compteurs


def test_un_texte_liste_classe_son_dossier_sans_requete_unitaire(tmp_path):
    portail = _Portail(listes={2021: [TA_CLASSE]})
    entrees, _, compteurs = _passe(tmp_path, portail, {"2021/0270(COD)": ["TA-9-2021-0460"]})

    assert entrees["2021/0270(COD)"]["domaines_document"] == "TA-9-2021-0460"
    assert portail.demandes == []
    assert compteurs["textes_adoptes_par_liste"] == 1


def test_un_texte_liste_non_classe_laisse_essayer_le_document_suivant(tmp_path):
    """Non classé est une réponse : le texte adopté n'est pas redemandé, le
    rapport l'est — comme si la réponse unitaire avait été `is_about` absent."""
    portail = _Portail(listes={2021: [TA_NON_CLASSE]}, documents={"A-9-2021-0150": RAPPORT})
    entrees, _, _ = _passe(tmp_path, portail, {"2020/2075(INI)": ["TA-9-2021-0358", "A-9-2021-0150"]})

    assert portail.demandes == ["A-9-2021-0150"]
    assert entrees["2020/2075(INI)"]["domaines_document"] == "A-9-2021-0150"


def test_un_texte_absent_de_la_liste_reste_demande_a_l_unite(tmp_path):
    """L'absence d'une liste n'est pas une inexistence : elle n'est rien écrite."""
    portail = _Portail(listes={2021: [TA_CLASSE]})
    entrees, _, _ = _passe(tmp_path, portail, {"X": ["TA-9-2021-0999"]})

    assert portail.demandes == ["TA-9-2021-0999"]
    assert entrees["X"]["domaines_non_resolu"] == {"motif": "documents_non_classes"}


def test_seules_les_annees_encore_inconnues_sont_listees(tmp_path):
    portail = _Portail(listes={2021: [TA_CLASSE]})
    documents = {"2021/0270(COD)": ["TA-9-2021-0460"]}
    _, resolveur, _ = _passe(tmp_path, portail, documents)
    resolveur.enregistrer()

    second = _Portail(listes={2021: [TA_CLASSE]})
    _passe(tmp_path, second, documents)

    assert portail.pages == [(2021, 0)]
    assert second.pages == []


def test_sans_budget_rien_n_est_liste(tmp_path):
    """`merge-and-pivot` passe budget et plafond à zéro : il lit le cache chaud."""
    portail = _Portail(listes={2021: [TA_CLASSE]})
    _passe(tmp_path, portail, {"2021/0270(COD)": ["TA-9-2021-0460"]},
           budget_secondes=0, plafond=0)

    assert portail.pages == []


def test_la_liste_se_parcourt_par_pages_et_se_reessaie(tmp_path, monkeypatch):
    """Un 404 passager a été vu en pleine liste de 2015 : il se réessaie."""
    monkeypatch.setattr(europarl_documents, "TAILLE_PAGE_LISTE", 1)
    portail = _Portail(listes={2021: [TA_CLASSE, TA_NON_CLASSE]}, pannes=1)
    _, resolveur, _ = _passe(tmp_path, portail, {"A": ["TA-9-2021-0460"], "B": ["TA-9-2021-0358"]})

    assert portail.pages == [(2021, 0), (2021, 0), (2021, 1), (2021, 2)]
    assert resolveur.concepts_eurovoc("TA-9-2021-0358") == []


def test_les_dossiers_recents_passent_d_abord(tmp_path):
    """Par ordre croissant, la passe du 21/09/2026 commençait en 1992."""
    portail = _Portail(documents={"TA-5-1999-0012": RAPPORT, "TA-9-2021-0001": RAPPORT})
    entrees, _, _ = _passe(tmp_path, portail,
                           {"1992/0449B(COD)": ["TA-5-1999-0012"], "2021/0001(COD)": ["TA-9-2021-0001"]},
                           plafond=1)

    assert portail.demandes == ["TA-9-2021-0001"]
    assert entrees["1992/0449B(COD)"]["domaines_non_resolu"] == {"motif": "question_non_posee"}
