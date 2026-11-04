"""Retrait nommé des signatures de cosignataire retirées à la source (#1429).

Le cas : l'amendement n° I-3250 du PLF 2027, déposé par Jean-Pierre Bataille,
collecté le 12/10/2026 avec 22 cosignataires dont 14 se sont retirés. Réduit ici
à un cosignataire resté (Joël Bruneau) et un parti (Charles de Courson). Les
profils sont écrits par `profil_brut.ecrire_profil_brut`, sous leur vraie forme
partitionnée ; la XVIIe, législature vivante, n'a pas de tranche dérivée.
"""

import inspect
import json
from pathlib import Path

import amendements_index
import cosignatures_retirees as cr
import generate_all_profiles
from profil_brut import charger_profil_brut, chemin_socle, ecrire_profil_brut

X = "AMANR5L17PO838901B3210P1D1N003250"   # le premier signataire est resté, Courson est parti
Y = "AMANR5L17PO838901B3210P1D1N003634"   # aucune copie du premier signataire dans le corpus
Z = "AMANR5L17PO838901B3210P1D1N000585"   # Courson en est le premier signataire
ACTEURS = {"jean-pierre-bataille": "PA267763", "joel-bruneau": "PA719286", "charles-de-courson": "PA1592"}


def _amd(uid, role, cosignataires):
    return {"uid": uid, "legislature": "17", "role_signataire": role,
            "premier_signataire": "an:PA267763", "co_signataires": cosignataires}


def _corpus(tmp_path):
    brut, pivot = tmp_path / "raw", tmp_path / "pivot"
    brut.mkdir()
    pivot.mkdir()
    profils = {
        "jean-pierre-bataille": [_amd(X, "auteur_principal", ["an:PA719286"])],
        "joel-bruneau": [_amd(X, "cosignataire", ["an:PA719286"])],
        "charles-de-courson": [
            _amd(X, "cosignataire", ["an:PA719286", "an:PA1592"]),   # la copie périmée du 12/10
            _amd(Y, "cosignataire", ["an:PA1592"]),
            _amd(Z, "auteur_principal", []),
        ],
    }
    for slug, amendements in profils.items():
        ecrire_profil_brut(brut, slug, {"id": slug, "nom": slug, "amendements": amendements})
        (pivot / f"{slug}.pivot.json").write_text(json.dumps({"id": slug, "amendements": [
            {"amendement_id": f"an:{a['uid']}", "role_signataire": a["role_signataire"]} for a in amendements
        ]}), encoding="utf-8")
    return brut, pivot


def _index(brut):
    return amendements_index.construire_index(amendements_index.iter_amendements_du_repertoire(brut))


def _uids_brut(brut, slug):
    return sorted(a["uid"] for a in charger_profil_brut(chemin_socle(brut, slug))["amendements"])


def _ids_pivot(pivot, slug):
    return sorted(a["amendement_id"] for a in json.loads((pivot / f"{slug}.pivot.json").read_text())["amendements"])


def test_la_signature_retiree_sort_du_brut_et_du_pivot(tmp_path):
    brut, pivot = _corpus(tmp_path)
    releve = cr.retirer(brut, pivot, _index(brut), ACTEURS.get)
    assert (releve.signatures, releve.retraits, releve.pivots_corriges) == (1, {"charles-de-courson": 1}, 1)
    assert _uids_brut(brut, "charles-de-courson") == sorted([Y, Z])
    assert _ids_pivot(pivot, "charles-de-courson") == sorted([f"an:{Y}", f"an:{Z}"])


def test_le_cosignataire_reste_et_l_auteur_ne_sont_pas_touches(tmp_path):
    brut, pivot = _corpus(tmp_path)
    cr.retirer(brut, pivot, _index(brut), ACTEURS.get)
    assert _uids_brut(brut, "joel-bruneau") == [X]
    assert _uids_brut(brut, "jean-pierre-bataille") == [X]


def test_sans_copie_du_premier_signataire_rien_n_est_retire(tmp_path):
    """L'absence d'une preuve n'est pas une preuve : Y reste à Courson."""
    brut, pivot = _corpus(tmp_path)
    cr.retirer(brut, pivot, _index(brut), ACTEURS.get)
    assert Y in _uids_brut(brut, "charles-de-courson")


def test_un_profil_sans_acteur_an_est_compte_et_laisse(tmp_path):
    brut, pivot = _corpus(tmp_path)
    releve = cr.retirer(brut, pivot, _index(brut), {"jean-pierre-bataille": "PA267763"}.get)
    assert (releve.signatures, releve.profils_sans_acteur) == (0, 2)
    assert X in _uids_brut(brut, "charles-de-courson")


def test_le_retrait_est_idempotent(tmp_path):
    brut, pivot = _corpus(tmp_path)
    cr.retirer(brut, pivot, _index(brut), ACTEURS.get)
    assert cr.retirer(brut, pivot, _index(brut), ACTEURS.get).signatures == 0


def test_le_repere_du_premier_signataire_survit_a_la_fusion_des_index(tmp_path):
    """En CI, le retrait lit l'index FUSIONNÉ que rend `rafraichir`."""
    brut, pivot = _corpus(tmp_path)
    dossier = tmp_path / "index"
    amendements_index.rafraichir(brut, dossier)              # un index déjà publié
    index = amendements_index.rafraichir(brut, dossier)      # fusionné avec lui
    assert f"an:{X}" in index.listes_du_premier_signataire
    assert cr.retirer(brut, pivot, index, ACTEURS.get).signatures == 1


def test_le_retrait_est_branche_apres_l_index_dans_la_passe_pivot():
    """La CI ne passe que par `generate_all_profiles` (#1101) : c'est là qu'il doit vivre."""
    source = inspect.getsource(generate_all_profiles._rafraichir_index_amendements)
    assert source.index("rafraichir_amendements(") < source.index("retirer_cosignatures(")


def test_le_resume_nomme_les_profils():
    releve = cr.Releve(profils_lus=3, retraits={"charles-de-courson": 291, "estelle-youssouffa": 394})
    texte = cr.resume(releve)
    assert "685 retirée(s) sur 2 profil(s)" in texte and texte.index("estelle-youssouffa") < texte.index("charles")
