"""#901 — une panne passagère d'EuroVoc ne fait plus échouer le run.

Le run 35194727922 (17/09/2026) est tombé sur un seul délai dépassé chez
l'Office des publications : `requests` a levé `ReadTimeout` sur la requête des
domaines, et toute la publication du corpus a été perdue. Rejouée une heure plus
tard, la même requête répondait en 0,1 à 0,4 s.

Le faux serveur ci-dessous lève la même exception que `requests` a levée en CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import requests

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

import documents_europeens  # noqa: E402
from documents_europeens import (  # noqa: E402
    LibellesEurovocIndisponibles,
    construire,
    resoudre_domaines,
    resoudre_libelles,
)
from test_documents_europeens_901 import _Resolveur, _SessionSparql  # noqa: E402

RELATIONS = ("08", "08 RELATIONS INTERNATIONALES")


@pytest.fixture(autouse=True)
def _sans_attente(monkeypatch):
    monkeypatch.setattr(documents_europeens, "ATTENTES_SPARQL", (0, 0), raising=False)


class _Capricieux(_SessionSparql):
    """Rejoue EuroVoc, mais lève `ReadTimeout` sur les `pannes` premières
    requêtes dont le texte contient `cible` ("ev:domain" pour les domaines)."""

    def __init__(self, libelles, domaines=None, pannes=1, cible="ev:domain", status_code=None):
        super().__init__(libelles, domaines=domaines)
        self.pannes, self.cible, self.statut_panne = pannes, cible, status_code
        self.essais_cible = 0

    def get(self, url, params=None, headers=None, timeout=None):
        if self.cible in params["query"] or (self.cible == "libelles" and "ev:domain" not in params["query"]):
            self.essais_cible += 1
            if self.essais_cible <= self.pannes:
                if self.statut_panne:
                    reponse = super().get(url, params=params, headers=headers, timeout=timeout)
                    reponse.status_code = self.statut_panne
                    return reponse
                raise requests.exceptions.ReadTimeout(
                    "HTTPSConnectionPool(host='publications.europa.eu', port=443): "
                    "Read timed out. (read timeout=60)")
        return super().get(url, params=params, headers=headers, timeout=timeout)


def test_un_delai_depasse_puis_une_reponse_rend_les_domaines():
    session = _Capricieux({}, domaines={"218": [RELATIONS]}, pannes=1)

    assert resoudre_domaines(["218"], session) == {
        "218": {"code": "08", "libelle": "08 RELATIONS INTERNATIONALES"}}
    assert session.essais_cible == 2


def test_un_503_passager_est_reessaye_aussi():
    session = _Capricieux({"2155": "opposition politique"}, pannes=2, cible="libelles", status_code=503)

    assert resoudre_libelles(["2155"], session) == {"2155": "opposition politique"}
    assert session.essais_cible == 3


def test_un_400_n_est_pas_reessaye():
    """La requête est fausse : la rejouer n'y changerait rien."""
    session = _Capricieux({"2155": "x"}, pannes=5, cible="libelles", status_code=400)

    with pytest.raises(LibellesEurovocIndisponibles):
        resoudre_libelles(["2155"], session)
    assert session.essais_cible == 1


def test_des_domaines_toujours_muets_se_declarent_sans_faire_echouer():
    """Le cas du run 35194727922, si la panne avait duré."""
    session = _Capricieux({"218": "coopération militaire"}, domaines={"218": [RELATIONS]}, pannes=99)

    entrees = construire(["A-10-2025-0084"], _Resolveur({"A-10-2025-0084": ["218"]}), session)

    assert entrees[0]["matieres"] == [
        {"code": "218", "libelle": "coopération militaire", "domaine": None}]
    assert entrees[0]["domaines_non_resolu"] == {"motif": "eurovoc_injoignable", "codes": ["218"]}
    assert session.essais_cible == 3


def test_des_libelles_toujours_muets_font_toujours_echouer():
    """Un code nu est illisible : cette absence-là bloque, comme avant."""
    session = _Capricieux({"218": "coopération militaire"}, pannes=99, cible="libelles")

    with pytest.raises(LibellesEurovocIndisponibles):
        construire(["A"], _Resolveur({"A": ["218"]}), session)
