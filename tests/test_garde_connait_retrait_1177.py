"""#1177 — la garde « collecté = publié » soustrait le retrait des paroles d'une
autre personne, en rejouant la fonction du retrait.

La ligne de table est copiée de `config/paroles_d_une_autre_personne.json`
(paragraphe `1010474`, attribué par la source à `PA722142`).
"""
from __future__ import annotations

import json

import audit_collecte_vs_publie as audit

TABLE = {"1010474": {"legislature": "15", "compte_rendu": "CRSANR5L15S2017E1N026",
                     "libelle": "Mme Sandra Marsaud", "acteur": "PA722142"}}


def _ecrire(tmp_path, *, acteur, retire_du_pivot):
    raw, pivot = tmp_path / "raw", tmp_path / "pivot"
    raw.mkdir()
    pivot.mkdir()
    paroles = [{"id": "a", "id_syceron": "1010474"}, {"id": "b", "id_syceron": "999"}]
    (raw / "francois-ruffin.json").write_text(json.dumps({
        "slug": "francois-ruffin", "mandats": [], "votes": [], "amendements": [],
        "dossiers_legislatifs": [], "interventions": paroles,
    }), encoding="utf-8")
    publiees = paroles[1:] if retire_du_pivot else paroles
    (pivot / "francois-ruffin.pivot.json").write_text(json.dumps({
        "id": "francois-ruffin", "identifiants": {"an": acteur},
        "mandats": [], "votes": [], "amendements": [], "textes_portes": [],
        "interventions": publiees, "meta": {"provenance": "candidat_declare"},
    }), encoding="utf-8")
    return raw, pivot


def test_le_retrait_n_est_pas_un_deficit(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "_TABLE_PAROLES", TABLE)
    raw, pivot = _ecrire(tmp_path, acteur="PA722142", retire_du_pivot=True)
    rapport = audit.auditer(raw, pivot)
    assert rapport["nb_deficits"] == 0


def test_la_reduction_ne_vaut_que_pour_l_acteur_que_la_table_nomme(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "_TABLE_PAROLES", TABLE)
    raw, pivot = _ecrire(tmp_path, acteur="PA000001", retire_du_pivot=True)
    assert audit.compter_paroles_d_une_autre_personne(raw, "francois-ruffin", pivot) == 0
    assert audit.auditer(raw, pivot)["nb_deficits"] == 1


def test_une_perte_reelle_reste_un_deficit(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "_TABLE_PAROLES", TABLE)
    raw, pivot = _ecrire(tmp_path, acteur="PA722142", retire_du_pivot=True)
    fiche = json.loads((pivot / "francois-ruffin.pivot.json").read_text(encoding="utf-8"))
    fiche["interventions"] = []
    (pivot / "francois-ruffin.pivot.json").write_text(json.dumps(fiche), encoding="utf-8")
    assert audit.auditer(raw, pivot)["nb_deficits"] == 1
