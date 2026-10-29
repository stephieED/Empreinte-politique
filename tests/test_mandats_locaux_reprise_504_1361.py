"""#1361 — une page en 504 de l'API tabulaire ne doit plus arrêter la collecte.

Du 23 au 26/10/2026, `extract-mandats-locaux` a échoué sur trois runs sur
quatre, chaque fois sur la même erreur levée par `_appel_reseau` :

    urllib.error.HTTPError: HTTP Error 504: Gateway Timeout

et le job s'arrêtait sans écrire aucun profil. Le dernier échec relevé avant
ce lot est celui du 28/10 (run public `40734395125`).
"""
from __future__ import annotations

import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import collecte_mandats_locaux as cml  # noqa: E402
from rne_opendata import RneIndisponible  # noqa: E402

URL = "https://tabular-api.data.gouv.fr/api/resources/RID/data/?page=2"


def _http(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(URL, code, "Gateway Timeout", {}, io.BytesIO(b""))


class _Serveur:
    """Rend, dans l'ordre, les erreurs puis les réponses qu'on lui donne."""

    def __init__(self, *suite):
        self.suite = list(suite)
        self.appels = 0

    def __call__(self, url):
        self.appels += 1
        element = self.suite.pop(0) if len(self.suite) > 1 else self.suite[0]
        if isinstance(element, BaseException):
            raise element
        return element


def _repris(serveur, **kw):
    attentes: list[float] = []
    return cml.avec_reprises(serveur, dormir=attentes.append, horloge=lambda: 0.0, **kw), attentes


def test_un_504_puis_une_reponse_rend_la_reponse():
    serveur = _Serveur(_http(504), {"data": [{"ok": 1}]})
    appel, attentes = _repris(serveur)
    assert appel(URL) == {"data": [{"ok": 1}]}
    assert serveur.appels == 2 and attentes == [cml.ATTENTES_REPRISE_S[0]]


@pytest.mark.parametrize("code", sorted(cml.STATUTS_A_REESSAYER))
def test_les_erreurs_passageres_se_reessaient(code):
    appel, attentes = _repris(_Serveur(_http(code), {"data": []}))
    assert appel(URL) == {"data": []}
    assert len(attentes) == 1


def test_une_coupure_reseau_se_reessaie():
    appel, _ = _repris(_Serveur(urllib.error.URLError("connexion refusée"), {"data": []}))
    assert appel(URL) == {"data": []}


@pytest.mark.parametrize("code", [400, 404])
def test_une_requete_fausse_ne_se_reessaie_pas(code):
    serveur = _Serveur(_http(code))
    appel, attentes = _repris(serveur)
    with pytest.raises(urllib.error.HTTPError):
        appel(URL)
    assert serveur.appels == 1 and attentes == []


def test_une_panne_qui_dure_est_nommee_apres_le_dernier_essai():
    serveur = _Serveur(_http(504))
    appel, attentes = _repris(serveur)
    with pytest.raises(RneIndisponible, match="HTTP 504 après 4 essai"):
        appel(URL)
    assert serveur.appels == 4 and attentes == list(cml.ATTENTES_REPRISE_S)


def test_le_budget_est_commun_a_tout_le_run():
    """La 2e requête en 504 n'attend pas : 10 s déjà dépensées + 10 > 15."""
    serveur = _Serveur(_http(504), {"data": []}, _http(504), {"data": []})
    appel, attentes = _repris(serveur, budget_s=15)
    assert appel(URL) == {"data": []}
    with pytest.raises(RneIndisponible):
        appel(URL)
    assert attentes == [10]


def test_le_temps_des_essais_rates_compte_dans_le_budget():
    """Un 504 de passerelle met souvent une minute à venir : il se décompte."""
    temps = iter([0.0, 60.0, 70.0, 130.0])
    serveur = _Serveur(_http(504), _http(504), {"data": []})
    attentes: list[float] = []
    appel = cml.avec_reprises(serveur, dormir=attentes.append, horloge=lambda: next(temps),
                              budget_s=100)
    with pytest.raises(RneIndisponible, match="130 s de reprises"):
        appel(URL)
    assert attentes == [10]


def test_main_nomme_la_panne_au_lieu_d_une_trace_de_pile(tmp_path, monkeypatch, capsys):
    pivot_dir, raw_dir = tmp_path / "pivot", tmp_path / "raw"
    pivot_dir.mkdir()
    raw_dir.mkdir()
    (pivot_dir / "edouard-philippe.pivot.json").write_text(json.dumps({
        "id": "edouard-philippe", "nom": "Édouard Philippe",
        "meta": {"provenance": "candidat_declare"},
        "identite": {"date_naissance": "1970-11-28"}}), encoding="utf-8")
    (raw_dir / "edouard-philippe.json").write_text('{"nom": "Édouard Philippe"}', encoding="utf-8")
    table = tmp_path / "table.json"
    table.write_text('{"candidats": {}}', encoding="utf-8")

    def toujours_504(url):
        raise _http(504)

    monkeypatch.setattr(cml, "_appel_reseau", toujours_504)
    monkeypatch.setattr(cml.time, "sleep", lambda s: None)
    code = cml.main(["--raw-dir", str(raw_dir), "--pivot-dir", str(pivot_dir),
                     "--table", str(table), "--apply",
                     "--manifest-out", str(tmp_path / "manifeste.txt")])
    sortie = capsys.readouterr().err
    assert code == 1
    assert "::error::RNE_INDISPONIBLE — HTTP 504" in sortie
    assert sortie.count("::warning::RNE_REPRISE") == len(cml.ATTENTES_REPRISE_S)
    assert not (tmp_path / "manifeste.txt").exists()
