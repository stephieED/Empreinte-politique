"""Une passe cesse d'interroger un portail qui ne répond plus (#901).

Le 16/09/2026, `data.europarl.europa.eu` a cessé de répondre sur `/documents`.
Pas un `429` avec son `Retry-After`, que ce module sait attendre : un SILENCE
de 30 s par requête. Le diagnostic, fait le jour même, tient en trois mesures —
les autres ressources du portail répondaient encore (`/meps` en 12 s), la même
URL servie depuis un autre réseau rendait 200, et seule cette ressource était
muette depuis notre adresse. La limitation nous visait.

Le défaut que cela révèle n'est pas la limitation, c'est ce que le code en
faisait : `except Exception: return None`, sans rien compter. Une passe sur 279
documents aurait payé le `TIMEOUT` pour chacun — **2 h 20** — pour finir sans un
seul titre, et sans que rien ne dise pourquoi.

Ce que le disjoncteur NE change PAS, et c'est essentiel : la donnée manquante
reste « question non posée » (`None`), jamais « ce document n'existe pas »
(`False`). §2 règle 5 vaut autant après cinq silences qu'après un seul.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from europarl_documents import MAX_ECHECS_CONSECUTIFS, ResolveurDocuments  # noqa: E402


class _Reponse:
    def __init__(self, status_code, charge=None, headers=None):
        self.status_code = status_code
        self._charge = charge
        self.headers = headers or {}

    def json(self):
        if self._charge is None:
            raise ValueError("pas de corps")
        return self._charge


class _SessionMuette:
    """Le portail ne répond plus : chaque appel lève, comme un timeout."""

    def __init__(self):
        self.appels = 0

    def get(self, url, params=None, timeout=None):
        self.appels += 1
        raise TimeoutError("le portail ne répond pas")


class _SessionIntermittente:
    """Échoue, puis répond — le compteur doit repartir de zéro."""

    def __init__(self, echecs_avant_succes):
        self.restants = echecs_avant_succes
        self.appels = 0

    def get(self, url, params=None, timeout=None):
        self.appels += 1
        if self.restants > 0:
            self.restants -= 1
            raise TimeoutError("silence")
        return _Reponse(200, {"data": {"title_dcterms": {"fr": "Titre"}}})


def _doceos(n):
    return [f"B-9-2024-{i:04d}" for i in range(n)]


def test_la_passe_s_arrete_apres_le_seuil(tmp_path):
    session = _SessionMuette()
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    for doceo in _doceos(MAX_ECHECS_CONSECUTIFS + 20):
        r.existe(doceo)
    assert r.disjoncte is True
    assert session.appels == MAX_ECHECS_CONSECUTIFS, (
        "après le seuil, plus aucune requête ne doit partir — c'est tout l'objet"
    )


def test_une_absence_reste_une_question_non_posee(tmp_path):
    """Jamais `False` : un silence ne prouve pas qu'un document n'existe pas."""
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_SessionMuette())
    for doceo in _doceos(MAX_ECHECS_CONSECUTIFS + 3):
        assert r.existe(doceo) is None
        assert r.titre_francais(doceo) is None


def test_un_succes_remet_le_compteur_a_zero(tmp_path):
    """Un aléa isolé ne doit pas rapprocher la passe du disjoncteur."""
    session = _SessionIntermittente(echecs_avant_succes=MAX_ECHECS_CONSECUTIFS - 1)
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    for doceo in _doceos(MAX_ECHECS_CONSECUTIFS - 1):
        r.existe(doceo)
    assert r.disjoncte is False
    assert r.existe("B-9-2024-9999") is True
    assert r.statistiques["echecs_consecutifs"] == 0
    assert r.disjoncte is False


def test_le_cache_repond_encore_apres_le_disjoncteur(tmp_path):
    """Ce qui a été obtenu reste acquis : seule l'interrogation s'arrête."""
    session = _SessionIntermittente(echecs_avant_succes=0)
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=session)
    assert r.existe("B-9-2024-0001") is True
    r._disjoncte = True
    assert r.existe("B-9-2024-0001") is True
    assert r.titre_francais("B-9-2024-0001") == "Titre"
    assert r.existe("B-9-2024-0002") is None


def test_un_echec_n_entre_pas_au_cache(tmp_path):
    """Sinon la panne d'un jour se figerait en fait pour tous les runs suivants."""
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_SessionMuette())
    r.existe("B-9-2024-0001")
    assert r.statistiques["documents_connus"] == 0


def test_les_statistiques_disent_que_la_passe_s_est_arretee(tmp_path):
    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_SessionMuette())
    assert r.statistiques["disjoncte"] is False
    for doceo in _doceos(MAX_ECHECS_CONSECUTIFS):
        r.existe(doceo)
    stats = r.statistiques
    assert stats["disjoncte"] is True
    assert stats["echecs_consecutifs"] >= MAX_ECHECS_CONSECUTIFS


def test_un_404_n_est_pas_un_echec(tmp_path):
    """Le portail qui répond « inconnu » répond : ce n'est pas une panne."""
    class _Session404:
        def get(self, url, params=None, timeout=None):
            return _Reponse(404)

    r = ResolveurDocuments(cache_path=tmp_path / "c.json", session=_Session404())
    for doceo in _doceos(MAX_ECHECS_CONSECUTIFS + 5):
        assert r.existe(doceo) is False
    assert r.disjoncte is False
