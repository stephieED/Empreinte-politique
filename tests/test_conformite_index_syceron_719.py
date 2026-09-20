#!/usr/bin/env python3
"""
test_conformite_index_syceron_719.py — Un index Syceron en cache qui ne porte
pas `sujet_code_grammaire` est refusé, pas relu au mieux (#719).

Ce que ces tests protègent tient en une phrase : **l'index par acteur n'est pas
une archive mise de côté, c'est un parsage mis en cache.** Sa clé dit quand, dans
quel mode et sur quelles archives il a été écrit (#550) ; elle ne dit rien du
parseur. Un champ ajouté au parseur n'atteint donc jamais un index déjà restauré,
et c'est exactement ce qui a fait échouer #710 en silence sur le run
`33652389393` : 0 entrée qualifiée sur les 3 963 de `gabriel-attal`, 2 041 sujets
de créneau intacts, et aucun garde-fou pour le dire.

Le mémo est vérifié dans les deux sens, parce que ses deux défauts sont
symétriques et coûteux : sans mémo, chaque acteur relit une tranche ; sans oubli
à la publication, chaque acteur reparcourt l'archive entière.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau : tout est
monté en `tmp_path`.
"""

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile as cp  # noqa: E402


@pytest.fixture(autouse=True)
def _memo_propre():
    cp.vider_memo_qualification_syceron()
    yield
    cp.vider_memo_qualification_syceron()


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Branche `SYCERON_CACHE_DIR` sur un cache jetable."""
    racine = tmp_path / "syceron_an"
    monkeypatch.setattr(cp, "SYCERON_CACHE_DIR", racine)
    return racine


def _entree(avec_qualification: bool, sujet="Motions de censure"):
    e = {
        "id": "syceron_CR123_000001",
        "date": "2024-10-08",
        "type_detail": "debat",
        "sujet": sujet,
        "legislature": "17",
    }
    if avec_qualification:
        e["sujet_code_grammaire"] = "TITRE_TEXTE_DISCUSSION"
    return e


def _ecrire_index(racine, legislature, tranches, *, theme=False):
    dirname = "index_par_acteur_theme" if theme else "index_par_acteur"
    d = racine / legislature / dirname
    d.mkdir(parents=True, exist_ok=True)
    for acteur_ref, entrees in tranches.items():
        (d / f"{acteur_ref}.json").write_text(
            json.dumps(entrees, ensure_ascii=False), encoding="utf-8"
        )
    return d


# --------------------------------------------------------------------------
# 1. Le verdict de conformité
# --------------------------------------------------------------------------

def test_un_index_du_parseur_corrige_est_qualifie(cache):
    d = _ecrire_index(cache, "17", {"PA1": [_entree(True)]})
    assert cp._syceron_index_qualifie(d) is True


def test_un_index_anterieur_a_710_ne_lest_pas(cache):
    d = _ecrire_index(cache, "17", {"PA1": [_entree(False)]})
    assert cp._syceron_index_qualifie(d) is False


def test_la_cle_suffit_meme_a_none(cache):
    """`sujet_code_grammaire` vaut légitimement `None` sur un point dont la
    grammaire ne porte pas de sujet : exiger une valeur refuserait un index
    correct. Même règle que `_scrutins_store_qualifie` (#639)."""
    entree = dict(_entree(True), sujet=None, sujet_code_grammaire=None)
    d = _ecrire_index(cache, "17", {"PA1": [entree]})
    assert cp._syceron_index_qualifie(d) is True


def test_un_repertoire_vide_nest_pas_qualifie(cache):
    d = cache / "17" / "index_par_acteur"
    d.mkdir(parents=True)
    assert cp._syceron_index_qualifie(d) is False


def test_une_tranche_illisible_nest_pas_qualifiee(cache):
    d = _ecrire_index(cache, "17", {"PA1": [_entree(True)]})
    (d / "PA1.json").write_text("{ pas du json", encoding="utf-8")
    cp.vider_memo_qualification_syceron()
    assert cp._syceron_index_qualifie(d) is False


def test_le_temoin_lu_est_la_plus_petite_tranche(cache, monkeypatch):
    """#628 : une tranche d'acteur bavard pèse plusieurs Mio, et une seule entrée
    tranche le verdict. Le témoin le moins cher est donc le bon."""
    import builtins

    d = _ecrire_index(
        cache,
        "17",
        {"PA1": [_entree(True) for _ in range(200)], "PA2": [_entree(True)]},
    )
    lues: list[str] = []
    ouvrir = builtins.open

    def _tracer(fichier, *a, **kw):
        lues.append(str(fichier))
        return ouvrir(fichier, *a, **kw)

    monkeypatch.setattr(builtins, "open", _tracer)
    assert cp._syceron_index_qualifie(d) is True
    assert [f for f in lues if f.endswith("PA2.json")]
    assert not [f for f in lues if f.endswith("PA1.json")]


# --------------------------------------------------------------------------
# 2. Le refus à la lecture — un index périmé se lit comme un index ABSENT
# --------------------------------------------------------------------------

def test_un_index_qualifie_est_servi(cache):
    _ecrire_index(cache, "17", {"PA1": [_entree(True)]})
    entrees = cp._read_cached_interventions_syceron_acteur("17", "PA1")
    assert entrees is not None and len(entrees) == 1


def test_un_index_perime_est_lu_comme_absent(cache, capsys):
    """`None` — pas `[]` : l'appelant reconstruit. Rendre une liste vide dirait
    « cette personne n'a pas parlé », ce qui est le défaut de #510 (§2 règle 5)."""
    _ecrire_index(cache, "17", {"PA1": [_entree(False)]})
    assert cp._read_cached_interventions_syceron_acteur("17", "PA1") is None
    assert "antérieur à #710" in capsys.readouterr().out


def test_un_run_reduit_se_rabat_sur_lautre_forme(cache):
    """Le refus est un `continue`, pas un `return None` : un index complet
    périmé ne doit pas masquer un index réduit conforme (#657)."""
    _ecrire_index(cache, "17", {"PA1": [_entree(False)]})
    _ecrire_index(cache, "17", {"PA1": [_entree(True)]}, theme=True)
    entrees = cp._read_cached_interventions_syceron_acteur("17", "PA1", theme_seul=True)
    assert entrees is not None and len(entrees) == 1


def test_un_run_complet_ne_regarde_jamais_lindex_reduit(cache):
    """Règle de #510/#657, inchangée par ce lot."""
    _ecrire_index(cache, "17", {"PA1": [_entree(True)]}, theme=True)
    assert cp._read_cached_interventions_syceron_acteur("17", "PA1") is None


# --------------------------------------------------------------------------
# 3. Le mémo, dans les deux sens
# --------------------------------------------------------------------------

def test_le_verdict_est_memoise_par_chemin(cache):
    d1 = _ecrire_index(cache, "16", {"PA1": [_entree(True)]})
    d2 = _ecrire_index(cache, "17", {"PA1": [_entree(False)]})
    assert cp._syceron_index_qualifie(d1) is True
    assert cp._syceron_index_qualifie(d2) is False
    # Le mémo d'une législature ne décide pas de l'autre — le piège de #377.
    assert cp._syceron_index_qualifie(d1) is True


def test_la_publication_oublie_le_verdict(cache):
    """Sans cet oubli, l'index qu'on vient d'écrire serait refusé et CHAQUE
    acteur reparcourrait l'archive — 12,5 s et 3,8 Gio de pic (#510)."""
    _ecrire_index(cache, "17", {"PA1": [_entree(False)]})
    assert cp._read_cached_interventions_syceron_acteur("17", "PA1") is None

    cp._write_syceron_index_par_acteur("17", {"PA1": [_entree(True)]})

    entrees = cp._read_cached_interventions_syceron_acteur("17", "PA1")
    assert entrees is not None and len(entrees) == 1


def test_la_publication_reduite_noublie_que_sa_forme(cache):
    _ecrire_index(cache, "17", {"PA1": [_entree(False)]})
    complet = cache / "17" / "index_par_acteur"
    assert cp._syceron_index_qualifie(complet) is False

    cp._write_syceron_index_par_acteur("17", {"PA1": [_entree(True)]}, theme_seul=True)

    # La forme COMPLÈTE reste jugée périmée : sa réécriture n'a pas eu lieu.
    assert cp._syceron_index_qualifie(complet) is False
    assert cp._syceron_index_qualifie(cache / "17" / "index_par_acteur_theme") is True
