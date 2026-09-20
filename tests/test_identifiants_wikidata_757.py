"""`identifiants_wikidata.py` — l'acteur AN par un identifiant, jamais par un nom (#757).

Les deux fixtures sont des **réponses réelles**, capturées le 07/09/2026, et
chacune porte une forme qui casse une lecture naïve :

- `pageprops.json` — une page normale, une **redirection** (« Jean-Luc
  Melenchon » sans accent renvoie vers l'article accentué) et une page
  **absente** (`pageid: -1`, clé `missing`). Sans le suivi de redirection, un
  candidat dont l'article a été renommé sort de la correspondance sans un mot ;
- `sparql_p4123.json` — deux éléments qui portent `P4123` et **un qui ne le
  porte pas** : la ligne revient quand même, sans la liaison `an`. C'est
  exactement ce qui sépare `HORS_AN` d'`INDETERMINE`.

Aucun test ne sort sur le réseau : `conftest.py` coupe `Session.send` et
échouerait bruyamment.
"""

import json
from pathlib import Path

import pytest
import requests

import identifiants_wikidata as iw

FIXTURES = Path(__file__).parent / "fixtures" / "wikidata"


class _Reponse:
    """Doublure minimale de `requests.Response`."""

    def __init__(self, charge, exc=None):
        self._charge = charge
        self._exc = exc

    def raise_for_status(self):
        if self._exc is not None:
            raise self._exc

    def json(self):
        if isinstance(self._charge, Exception):
            raise self._charge
        return self._charge


def _session(*charges):
    """Une session qui rend les charges dans l'ordre des appels."""
    restantes = list(charges)

    class _Session:
        appels: list[dict] = []

        def get(self, url, params=None, headers=None, timeout=None):
            self.appels.append({"url": url, "params": params})
            return _Reponse(restantes.pop(0))

    return _Session()


@pytest.fixture
def pageprops():
    return json.loads((FIXTURES / "pageprops.json").read_text(encoding="utf-8"))


@pytest.fixture
def sparql():
    return json.loads((FIXTURES / "sparql_p4123.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Article → élément
# ---------------------------------------------------------------------------


def test_resout_les_elements_et_suit_les_redirections(pageprops):
    titres = [
        "Bernard Cazeneuve",
        "François Asselineau",
        "Jean-Luc Melenchon",
        "Personne Qui N Existe Pas 2027",
    ]
    elements = iw.resoudre_elements(titres, session=_session(pageprops))

    assert elements["Bernard Cazeneuve"] == "Q560890"
    assert elements["François Asselineau"] == "Q12972"
    # Le titre DEMANDÉ porte le résultat, pas celui vers lequel on a été redirigé.
    assert elements["Jean-Luc Melenchon"] == "Q5829"
    assert elements["Personne Qui N Existe Pas 2027"] is None


def test_une_panne_de_wikipedia_leve_au_lieu_de_rendre_vide():
    class _Session:
        def get(self, *a, **k):
            raise requests.RequestException("Read timed out")

    with pytest.raises(iw.ResolutionIndisponible) as leve:
        iw.resoudre_elements(["Bernard Cazeneuve"], session=_Session())
    assert "Read timed out" in str(leve.value)


# ---------------------------------------------------------------------------
# Élément → acteur AN
# ---------------------------------------------------------------------------


def test_resout_lacteur_an_et_laisse_none_sur_un_element_sans_p4123(sparql):
    acteurs = iw.resoudre_acteurs_an(["Q560890", "Q12972", "Q5829"], session=_session(sparql))

    assert acteurs["Q560890"] == "PA785"
    assert acteurs["Q5829"] == "PA2150"
    # L'élément existe, la ligne revient, et il ne porte pas la propriété.
    assert acteurs["Q12972"] is None


def test_une_panne_de_wikidata_leve_au_lieu_de_rendre_hors_an():
    """Un timeout qui se lirait « n'a jamais siégé » écrirait un fait faux."""

    class _Session:
        def get(self, *a, **k):
            raise requests.RequestException("HTTP 500")

    with pytest.raises(iw.ResolutionIndisponible):
        iw.resoudre_acteurs_an(["Q560890"], session=_Session())


def test_les_lots_sont_bornes(monkeypatch, sparql):
    """50 par requête : la limite anonyme de l'API MediaWiki."""
    vus = []

    class _Session:
        def get(self, url, params=None, headers=None, timeout=None):
            vus.append(params)
            return _Reponse({"results": {"bindings": []}})

    iw.resoudre_acteurs_an([f"Q{n}" for n in range(120)], session=_Session())
    assert len(vus) == 3, "120 identifiants doivent partir en 3 lots de 50 au plus"


# ---------------------------------------------------------------------------
# La chaîne complète, et ses trois issues
# ---------------------------------------------------------------------------


def test_les_trois_issues_sont_distinguees(pageprops, sparql):
    candidats = [
        {"nom": "Bernard Cazeneuve", "source": "https://fr.wikipedia.org/wiki/Bernard_Cazeneuve"},
        {"nom": "François Asselineau", "source": "https://fr.wikipedia.org/wiki/Fran%C3%A7ois_Asselineau"},
        {
            "nom": "Selma Labib",
            # Le repli écrit par fetch_candidats_declares quand la personne n'a
            # pas d'article : une URL de SECTION, qui n'est pas un titre.
            "source": "https://fr.wikipedia.org/wiki/Candidatures#Candidats_d%C3%A9clar%C3%A9s",
        },
    ]
    resolutions = iw.resoudre(candidats, session=_session(pageprops, sparql))

    assert resolutions["Bernard Cazeneuve"].issue is iw.Issue.ACTEUR
    assert resolutions["Bernard Cazeneuve"].acteur_ref == "PA785"
    assert resolutions["Bernard Cazeneuve"].preuve == "https://www.wikidata.org/wiki/Q560890"

    # L'élément existe et ne connaît aucun mandat AN : un fait négatif, à corroborer.
    assert resolutions["François Asselineau"].issue is iw.Issue.HORS_AN
    assert resolutions["François Asselineau"].qid == "Q12972"

    # Wikidata ne dit rien de cette personne : ce n'est pas la même affirmation.
    assert resolutions["Selma Labib"].issue is iw.Issue.INDETERMINE
    assert resolutions["Selma Labib"].qid is None


def test_une_url_de_section_ninterroge_aucun_article(pageprops, sparql):
    """Sinon l'article des candidatures serait demandé une fois par sans-article."""
    session = _session({"query": {"pages": {}}}, sparql)
    candidats = [
        {"nom": "Selma Labib", "source": "https://fr.wikipedia.org/wiki/Candidatures#Candidats"},
        {"nom": "Benoît Mathieu", "source": "https://fr.wikipedia.org/wiki/Candidatures#Candidats"},
    ]
    iw.resoudre(candidats, session=session)

    titres = [a["params"].get("titles") for a in session.appels if a["params"]]
    assert all(not t for t in titres), f"aucun titre ne devait partir, vu : {titres}"


def test_une_entree_sans_source_est_indeterminee(pageprops, sparql):
    resolutions = iw.resoudre([{"nom": "Sans Source", "source": None}], session=_session({"query": {"pages": {}}}))
    assert resolutions["Sans Source"].issue is iw.Issue.INDETERMINE


# ---------------------------------------------------------------------------
# Le fichier que la passe hors ligne relira
# ---------------------------------------------------------------------------


def test_ecrire_resolutions_rend_un_document_relisible(tmp_path):
    chemin = tmp_path / "resolutions.json"
    iw.ecrire_resolutions(
        chemin,
        {
            "Bernard Cazeneuve": iw.Resolution(
                nom="Bernard Cazeneuve",
                issue=iw.Issue.ACTEUR,
                acteur_ref="PA785",
                qid="Q560890",
                preuve="https://www.wikidata.org/wiki/Q560890",
            )
        },
        "2026-09-07",
    )
    document = json.loads(chemin.read_text(encoding="utf-8"))

    assert document["schema_version"] == "resolutions-candidats-v1"
    assert document["propriete"] == "P4123"
    assert document["resolutions"]["Bernard Cazeneuve"]["acteur_ref"] == "PA785"
    assert document["resolutions"]["Bernard Cazeneuve"]["issue"] == "acteur"
