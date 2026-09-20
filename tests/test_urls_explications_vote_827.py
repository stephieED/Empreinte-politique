"""#827 — l'adresse est dérivée, l'existence est prouvée.

Aucun test ici ne touche le réseau (`tests/conftest.py` le refuse depuis #473) :
la session du portail est simulée, et c'est justement ce que le résolveur rend
possible en la recevant par injection.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from europarl_documents import (  # noqa: E402
    DOCEO_BASE,
    ResolveurDocuments,
    reference_doceo,
    url_doceo,
)


class _Reponse:
    def __init__(self, status_code, headers=None):
        self.status_code = status_code
        self.headers = headers or {}


class _SessionSimulee:
    """Rejoue le portail : 200 pour les documents connus, 404 sinon."""

    def __init__(self, existants, sequence=None):
        self.existants = set(existants)
        self.sequence = list(sequence or [])
        self.appels = []

    def get(self, url, params=None, timeout=None):
        self.appels.append(url)
        if self.sequence:
            return self.sequence.pop(0)
        doceo = url.rsplit("/", 1)[-1]
        return _Reponse(200 if doceo in self.existants else 404)


# ---------------------------------------------------------------------------
# La conversion : deux formes, et la seconde perd sa lettre
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("intitule, attendu", [
    ("Mobilisation of the EGF (A8-0196/2017 - Petri Sarvamaa) FR", "A-8-2017-0196"),
    ("Situation in Gaza (RC-B8-0292/2018)", "RC-8-2018-0292"),
    ("Objection (B9-0123/2021 - Someone)", "B-9-2021-0123"),
    ("Position du Conseil (C9-0212/2020)", "C-9-2020-0212"),
    ("Rapport (A10-0007/2024)", "A-10-2024-0007"),
])
def test_reference_extraite_de_l_intitule(intitule, attendu):
    assert reference_doceo(intitule) == attendu


def test_la_resolution_commune_perd_sa_lettre():
    """`RC-B8-0292/2018` → `RC-8-2018-0292` : garder le `B` ferait une URL fausse.

    C'est la conversion la plus risquée du lot, et la seule dont une erreur
    serait silencieuse — le pare-feu du site public répondant à l'identique pour
    une URL vraie et pour une URL inventée.
    """
    assert reference_doceo("(RC-B8-0292/2018)") == "RC-8-2018-0292"
    assert "B8" not in reference_doceo("(RC-B8-0292/2018)")


@pytest.mark.parametrize("intitule", [
    "Allocation of slots at Community airports: common rules",
    "Draft amending budget No 1/2020: Assistance to Greece",
    None,
    "",
    42,
])
def test_un_intitule_sans_document_ne_rend_rien(intitule):
    """271 des 1 801 explications sont dans ce cas : un fait sur la source."""
    assert reference_doceo(intitule) is None


def test_url_doceo_est_pure():
    assert url_doceo("A-8-2017-0196") == f"{DOCEO_BASE}/A-8-2017-0196_FR.html"


# ---------------------------------------------------------------------------
# L'existence : prouvée, jamais supposée
# ---------------------------------------------------------------------------

def test_une_url_n_est_publiee_que_si_le_document_existe(tmp_path):
    session = _SessionSimulee({"A-8-2017-0196"})
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    assert r.url_verifiee("(A8-0196/2017 - X)") == f"{DOCEO_BASE}/A-8-2017-0196_FR.html"


def test_un_document_introuvable_ne_donne_aucune_url(tmp_path):
    """Les 17 documents de type `C` sont dans ce cas : transmis par une autre
    institution, ils n'ont pas d'entrée au Parlement."""
    session = _SessionSimulee(set())
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    assert r.url_verifiee("(C9-0212/2020)") is None


def test_sans_resolveur_de_reseau_la_question_reste_sans_reponse(tmp_path):
    """`None`, jamais `False` : une ignorance publiée comme un fait négatif est
    ce que §2 règle 5 interdit."""
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", hors_ligne=True)
    assert r.existe("A-8-2017-0196") is None
    assert r.url_verifiee("(A8-0196/2017 - X)") is None


def test_un_portail_injoignable_ne_publie_rien(tmp_path):
    class _SessionQuiCasse:
        def get(self, *a, **k):
            raise OSError("réseau coupé")

    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_SessionQuiCasse())
    assert r.existe("A-8-2017-0196") is None


# ---------------------------------------------------------------------------
# Le débit et le cache
# ---------------------------------------------------------------------------

def test_le_429_est_respecte_puis_reessaye(tmp_path, monkeypatch):
    """Le portail ne déclare sa limite qu'en la refusant : une première passe
    sans pause a rendu 1 320 réponses 429 sur 1 424, mesure entièrement perdue."""
    dormi = []
    monkeypatch.setattr("europarl_documents.time.sleep", lambda s: dormi.append(s))
    session = _SessionSimulee(set(), sequence=[
        _Reponse(429, {"Retry-After": "60"}),
        _Reponse(200),
    ])
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    assert r.existe("A-8-2017-0196") is True
    assert 61 in dormi, "le Retry-After du portail doit être respecté"
    assert len(session.appels) == 2


def test_le_cache_evite_de_reinterroger(tmp_path, monkeypatch):
    monkeypatch.setattr("europarl_documents.time.sleep", lambda s: None)
    session = _SessionSimulee({"A-8-2017-0196"})
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    for _ in range(5):
        r.existe("A-8-2017-0196")
    assert len(session.appels) == 1


def test_un_document_absent_est_mis_en_cache_comme_les_autres(tmp_path, monkeypatch):
    """Un 404 est un fait établi sur le document, pas un échec de collecte :
    le redemander à chaque run coûterait sans rien apprendre."""
    monkeypatch.setattr("europarl_documents.time.sleep", lambda s: None)
    session = _SessionSimulee(set())
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    r.existe("C-9-2020-0212")
    r.existe("C-9-2020-0212")
    assert len(session.appels) == 1


def test_le_cache_survit_a_un_second_resolveur(tmp_path, monkeypatch):
    monkeypatch.setattr("europarl_documents.time.sleep", lambda s: None)
    chemin = tmp_path / "c.json"
    session = _SessionSimulee({"A-8-2017-0196"})
    premier = ResolveurDocuments(cache_path=chemin, session=session)
    premier.existe("A-8-2017-0196")
    premier.enregistrer()

    second = ResolveurDocuments(cache_path=chemin, hors_ligne=True)
    assert second.existe("A-8-2017-0196") is True
    # v3 depuis #901 : le cache porte `{existe, titre_fr, concepts}` là où il ne
    # portait qu'un booléen. Les caches v1 et v2 se relisent sans être invalidés
    # (tests dédiés dans `test_titre_francais_textes_europeens_901.py`).
    assert json.loads(chemin.read_text())["schema_version"] == "documents-doceo-v3"


def test_un_cache_illisible_ne_fait_pas_tomber_le_run(tmp_path):
    chemin = tmp_path / "c.json"
    chemin.write_text("{ ceci n'est pas du json")
    r = ResolveurDocuments(cache_path=chemin, hors_ligne=True)
    assert r.existe("A-8-2017-0196") is None


# ---------------------------------------------------------------------------
# Le câblage dans la normalisation
# ---------------------------------------------------------------------------

def test_l_explication_de_vote_recoit_son_lien(tmp_path, monkeypatch):
    monkeypatch.setattr("europarl_documents.time.sleep", lambda s: None)
    from normalize_parltrack_dumps import _make_intervention

    session = _SessionSimulee({"A-8-2017-0196"})
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    entree = {"titre": "EGF (A8-0196/2017 - X) FR", "texte": "J'ai voté pour.",
              "date": "2017-05-01T00:00:00", "legislature": "8"}
    interv = _make_intervention("WEXP", entree, r)
    assert interv["source_url"] == f"{DOCEO_BASE}/A-8-2017-0196_FR.html"


def test_sans_resolveur_aucune_url_n_est_inventee():
    """L'état d'avant #827, et le comportement des tests : rien n'est publié."""
    from normalize_parltrack_dumps import _make_intervention

    entree = {"titre": "EGF (A8-0196/2017 - X) FR", "texte": "J'ai voté pour.",
              "date": "2017-05-01T00:00:00", "legislature": "8"}
    assert _make_intervention("WEXP", entree)["source_url"] is None


def test_une_url_deja_donnee_par_la_source_est_gardee(tmp_path):
    """Les neuf autres types d'activité en portent une : on ne la remplace pas."""
    from normalize_parltrack_dumps import _make_intervention

    session = _SessionSimulee({"A-8-2017-0196"})
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    entree = {"titre": "Débat (A8-0196/2017 - X)", "source_url": "https://exemple/officiel",
              "date": "2017-05-01T00:00:00", "legislature": "8"}
    assert _make_intervention("CRE", entree, r)["source_url"] == "https://exemple/officiel"
    assert session.appels == [], "la source faisait autorité : ne pas interroger le portail"
