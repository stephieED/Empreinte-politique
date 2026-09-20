"""#901 — les domaines EuroVoc d'un dossier, par son document de séance.

EuroVoc est attaché à un document, jamais à une procédure. L'essai du 17/09/2026
sur les 367 dossiers amendés par les candidats déclarés a montré que le portail
classe le texte adopté (281 dossiers) et presque jamais le rapport (11).

Tout est copié de la source : le dossier `2010/0310M(NLE)` tel que le dump le
décrit (docs et événements), la réponse RÉELLE du portail pour
`TA-8-2018-0286` (8 concepts), et les domaines que le point SPARQL rend pour ces
8 concepts. Le résolveur est le vrai `ResolveurDocuments` ; seule la session
HTTP est rejouée.
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
from dossiers_europeens import documents_de_seance, domaines_des_dossiers  # noqa: E402
from europarl_documents import ResolveurDocuments  # noqa: E402
from test_documents_europeens_901 import _SessionSparql  # noqa: E402

DOSSIER_IRAQ = {
    "procedure": {"reference": "2010/0310M(NLE)"},
    "docs": [
        {"type": "Committee draft report", "docs": [{"title": "PE619.389"}]},
        {"type": "Amendments tabled in committee", "docs": [{"title": "PE621.064"}]},
        {"type": "Committee opinion", "docs": [{"title": "PE620.878"}]},
    ],
    "events": [
        {"type": "Committee report tabled for plenary", "docs": [{"title": "A8-0224/2018"}]},
        {"type": "Results of vote in Parliament", "docs": [{"title": "Results of vote in Parliament"}]},
        {"type": "Decision by Parliament", "docs": [{"title": "T8-0286/2018"}]},
    ],
}

#: Réponse réelle du portail, 17/09/2026, réduite aux champs lus.
REPONSE_TA = {"data": [{"id": "eli/dl/doc/TA-8-2018-0286", "type": "Work", "is_about": [
    "http://eurovoc.europa.eu/3074", "http://eurovoc.europa.eu/1500", "http://eurovoc.europa.eu/5404",
    "http://eurovoc.europa.eu/5403", "http://eurovoc.europa.eu/3489", "http://eurovoc.europa.eu/3077",
    "http://eurovoc.europa.eu/5897", "http://eurovoc.europa.eu/2933"],
    "title_dcterms": {"fr": "Accord de partenariat et de coopération entre l’UE et l’Iraq (résolution) "}}]}
#: Un rapport de commission : le portail répond, sans `is_about`.
REPONSE_RAPPORT = {"data": [{"id": "eli/dl/doc/A-8-2018-0224", "type": "Work",
                             "title_dcterms": {"fr": "RAPPORT"}}]}

#: Domaines rendus par SPARQL pour les 8 concepts, le 17/09/2026.
DOMAINES = {
    "3074": [("08", "08 RELATIONS INTERNATIONALES")], "3077": [("08", "08 RELATIONS INTERNATIONALES")],
    "3489": [("08", "08 RELATIONS INTERNATIONALES")], "5403": [("10", "10 UNION EUROPÉENNE")],
    "5404": [("10", "10 UNION EUROPÉENNE")], "2933": [("16", "16 ÉCONOMIE")],
    "5897": [("04", "04 VIE POLITIQUE")], "1500": [("72", "72 GÉOGRAPHIE")],
}


class _Reponse:
    def __init__(self, status_code, charge=None):
        self.status_code, self._charge, self.headers = status_code, charge, {}

    def json(self):
        return self._charge


class _Portail:
    """Rejoue le portail : `documents` → réponse, 404 sinon, compte les requêtes."""

    def __init__(self, documents):
        self.documents = documents
        self.demandes = []

    def get(self, url, params=None, timeout=None):
        doceo = url.rsplit("/", 1)[-1]
        self.demandes.append(doceo)
        if doceo in self.documents:
            return _Reponse(200, self.documents[doceo])
        return _Reponse(404)


@pytest.fixture(autouse=True)
def _sans_attente(monkeypatch):
    monkeypatch.setattr(europarl_documents, "PAUSE_ENTRE_REQUETES", 0)
    monkeypatch.setattr(documents_europeens, "ATTENTES_SPARQL", (0, 0))


def _resolveur(tmp_path, documents):
    return ResolveurDocuments(cache_path=tmp_path / "cache.json", session=_Portail(documents))


def _entree(reference="2010/0310M(NLE)"):
    return {"reference": reference, "familles": []}


def test_le_texte_adopte_passe_avant_le_rapport():
    assert documents_de_seance(DOSSIER_IRAQ) == ["TA-8-2018-0286", "A-8-2018-0224"]


def test_une_resolution_commune_devient_son_doceo():
    dossier = {"events": [{"docs": [{"title": "RC-B9-0123/2019"}, {"title": "B8-0250/2016"}]}]}
    assert documents_de_seance(dossier) == ["RC-9-2019-0123", "B-8-2016-0250"]


def test_le_dossier_porte_ses_domaines_ponderes_et_le_document_source(tmp_path):
    entrees = [_entree()]
    resolveur = _resolveur(tmp_path, {"TA-8-2018-0286": REPONSE_TA, "A-8-2018-0224": REPONSE_RAPPORT})

    compteurs = domaines_des_dossiers(
        entrees, {"2010/0310M(NLE)": documents_de_seance(DOSSIER_IRAQ)},
        resolveur, _SessionSparql({}, domaines=DOMAINES))

    assert entrees[0]["domaines"] == [
        {"code": "08", "libelle": "08 RELATIONS INTERNATIONALES", "concepts": 3},
        {"code": "10", "libelle": "10 UNION EUROPÉENNE", "concepts": 2},
        {"code": "04", "libelle": "04 VIE POLITIQUE", "concepts": 1},
        {"code": "16", "libelle": "16 ÉCONOMIE", "concepts": 1},
        {"code": "72", "libelle": "72 GÉOGRAPHIE", "concepts": 1},
    ]
    assert entrees[0]["domaines_document"] == "TA-8-2018-0286"
    assert "domaines_non_resolu" not in entrees[0]
    assert compteurs["requetes"] == 1  # le texte adopté suffit : le rapport n'est pas demandé


def test_un_dossier_dont_les_documents_ne_sont_pas_classes_le_dit(tmp_path):
    entrees = [_entree()]
    resolveur = _resolveur(tmp_path, {"A-8-2018-0224": REPONSE_RAPPORT})  # TA absent : 404

    domaines_des_dossiers(entrees, {"2010/0310M(NLE)": ["TA-8-2018-0286", "A-8-2018-0224"]},
                          resolveur, _SessionSparql({}, domaines=DOMAINES))

    assert entrees[0]["domaines"] == []
    assert entrees[0]["domaines_non_resolu"] == {"motif": "documents_non_classes"}


def test_sans_document_de_seance_aucune_requete(tmp_path):
    entrees = [_entree()]
    resolveur = _resolveur(tmp_path, {})

    domaines_des_dossiers(entrees, {"2010/0310M(NLE)": []}, resolveur, _SessionSparql({}))

    assert entrees[0]["domaines_non_resolu"] == {"motif": "aucun_document_de_seance"}
    assert resolveur.session.demandes == []


def test_le_plafond_laisse_les_votes_pour_le_run_suivant(tmp_path):
    """Les dossiers amendés passent d'abord ; au-delà du plafond, la question
    n'est pas posée, et ce n'est pas « non classé »."""
    entrees = [_entree("A-VOTE"), _entree("Z-AMENDE")]
    resolveur = _resolveur(tmp_path, {"TA-8-2018-0286": REPONSE_TA, "TA-9-2020-0001": REPONSE_TA})
    documents = {"A-VOTE": ["TA-9-2020-0001"], "Z-AMENDE": ["TA-8-2018-0286"]}

    domaines_des_dossiers(entrees, documents, resolveur, _SessionSparql({}, domaines=DOMAINES),
                          prioritaires={"Z-AMENDE"}, plafond=1)

    amende, vote = entrees[1], entrees[0]
    assert amende["domaines_document"] == "TA-8-2018-0286"
    assert vote["domaines_non_resolu"] == {"motif": "question_non_posee"}
    assert resolveur.session.demandes == ["TA-8-2018-0286"]
    assert resolveur.hors_ligne is False  # rendu tel qu'il était


def test_le_cache_repond_meme_au_dela_du_plafond(tmp_path):
    """Ce qu'un run précédent a appris ne se reperd pas."""
    resolveur = _resolveur(tmp_path, {"TA-8-2018-0286": REPONSE_TA})
    resolveur.concepts_eurovoc("TA-8-2018-0286")
    entrees = [_entree()]

    domaines_des_dossiers(entrees, {"2010/0310M(NLE)": ["TA-8-2018-0286"]}, resolveur,
                          _SessionSparql({}, domaines=DOMAINES), plafond=0)

    assert entrees[0]["domaines_document"] == "TA-8-2018-0286"
    assert resolveur.session.demandes == ["TA-8-2018-0286"]


def test_eurovoc_muet_se_declare(tmp_path):
    class _Muet:
        def get(self, *a, **k):
            raise TimeoutError("silence")

    entrees = [_entree()]
    domaines_des_dossiers(entrees, {"2010/0310M(NLE)": ["TA-8-2018-0286"]},
                          _resolveur(tmp_path, {"TA-8-2018-0286": REPONSE_TA}), _Muet())

    assert entrees[0]["domaines_non_resolu"] == {"motif": "eurovoc_injoignable"}


def test_le_budget_en_temps_arrete_la_passe_quel_que_soit_le_plafond(tmp_path):
    """Le run 35231390627 : 1 500 requêtes à 3,5 s en CI, 88 minutes, job annulé.
    Le budget en temps coupe la passe même si le plafond n'est pas atteint."""
    entrees = [_entree("A-AMENDE"), _entree("B-VOTE")]
    resolveur = _resolveur(tmp_path, {"TA-8-2018-0286": REPONSE_TA, "TA-9-2020-0001": REPONSE_TA})
    documents = {"A-AMENDE": ["TA-8-2018-0286"], "B-VOTE": ["TA-9-2020-0001"]}
    temps = iter([0.0, 0.0, 1300.0, 1300.0, 1300.0])  # début, 1er dossier, 2e dossier…

    compteurs = domaines_des_dossiers(
        entrees, documents, resolveur, _SessionSparql({}, domaines=DOMAINES),
        prioritaires={"A-AMENDE"}, plafond=10_000, budget_secondes=1200,
        horloge=lambda: next(temps))

    assert entrees[0]["domaines_document"] == "TA-8-2018-0286"
    assert entrees[1]["domaines_non_resolu"] == {"motif": "question_non_posee"}
    assert resolveur.session.demandes == ["TA-8-2018-0286"]
    assert compteurs["requetes"] == 1
