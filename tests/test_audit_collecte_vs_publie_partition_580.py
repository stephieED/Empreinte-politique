"""Le contrôle collecté/publié compte les tranches de #580.

Pourquoi ce fichier existe séparément de `test_audit_collecte_vs_publie.py` :
c'est **le filet** du lot #580. Le socle n'ayant plus de clé `amendements`, un
lecteur non adapté lirait « 0 amendement collecté » — et un contrôle qui
compare 0 collecté à 6 millions publiés ne signale aucun déficit. Il
deviendrait vert et aveugle sur 96,7 % du volume.

Tant que ce contrôle-ci compte juste, tout lecteur oublié en aval se déclare de
lui-même avant le commit, avec le slug et les deux comptes (#545).
"""

import json

import pytest

from audit_collecte_vs_publie import (
    auditer,
    compter_listes,
    compter_listes_profil_brut,
)
from profil_brut import ecrire_profil_brut


def _profil_brut(slug, nb_par_legislature):
    return {
        "slug": slug,
        "chambre": "deputes",
        "identite": {"nom": slug},
        "mandats": [{"label": "Députée"}],
        "votes": [{"numero_scrutin": 1}],
        "interventions": [],
        "dossiers_legislatifs": [],
        "amendements": [
            {"uid": f"{legis}-{i}", "legislature": legis}
            for legis, n in nb_par_legislature.items()
            for i in range(n)
        ],
        "meta": {"warnings": []},
    }


def _ecrire_pivot(dossier, slug, nb_amendements):
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / f"{slug}.pivot.json").write_text(
        json.dumps({
            "id": f"an:{slug}",
            "mandats": [{"label": "Députée"}],
            "votes": [{"scrutin_id": "an:16:1"}],
            "interventions": [],
            "textes_portes": [],
            "amendements": [
                {"amendement_id": f"an:{i}"} for i in range(nb_amendements)
            ],
        }, ensure_ascii=False),
        encoding="utf-8",
    )


def test_compte_les_amendements_a_travers_les_tranches(tmp_path):
    ecrire_profil_brut(tmp_path, "aline", _profil_brut("aline", {"15": 3, "16": 7, "17": 2}))

    # Le socle seul dirait 0 : c'est exactement le piège.
    assert "amendements" not in compter_listes(tmp_path / "aline.json")

    releve = compter_listes_profil_brut(tmp_path, "aline")
    assert releve["amendements"] == 12
    assert releve["mandats"] == 1
    assert releve["votes"] == 1


def test_le_compte_est_mesure_et_non_lu_au_manifeste(tmp_path):
    """Un contrôle qui recopierait le `total` annoncé écrirait sa conclusion
    sans la vérifier (#576, #579). On fausse le manifeste : le compte mesuré ne
    doit pas bouger."""
    ecrire_profil_brut(tmp_path, "aline", _profil_brut("aline", {"16": 5}))
    socle_path = tmp_path / "aline.json"
    socle = json.loads(socle_path.read_text(encoding="utf-8"))
    socle["amendements_partitionnes"]["total"] = 99999
    socle_path.write_text(json.dumps(socle, ensure_ascii=False), encoding="utf-8")

    assert compter_listes_profil_brut(tmp_path, "aline")["amendements"] == 5


def test_forme_monolithique_toujours_comptee(tmp_path):
    profil = _profil_brut("boris", {"16": 4})
    (tmp_path / "boris.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8"
    )
    assert compter_listes_profil_brut(tmp_path, "boris")["amendements"] == 4


def test_socle_qui_porte_encore_la_cle_a_cote_des_tranches_refuse(tmp_path):
    """La donnée serait comptée deux fois : c'est un défaut, pas un doublon
    inoffensif."""
    ecrire_profil_brut(tmp_path, "aline", _profil_brut("aline", {"16": 3}))
    socle_path = tmp_path / "aline.json"
    socle = json.loads(socle_path.read_text(encoding="utf-8"))
    socle["amendements"] = [{"uid": "x"}]
    socle_path.write_text(json.dumps(socle, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="comptée deux fois"):
        compter_listes_profil_brut(tmp_path, "aline")


def test_repertoire_de_tranches_vide_refuse(tmp_path):
    ecrire_profil_brut(tmp_path, "aline", _profil_brut("aline", {"16": 3}))
    for f in (tmp_path / "aline").glob("*.json"):
        f.unlink()

    with pytest.raises(ValueError, match="vide"):
        compter_listes_profil_brut(tmp_path, "aline")


def test_deficit_detecte_sur_un_profil_partitionne(tmp_path):
    """Le bout du bout : un pivot qui publie moins que ce que la partition
    porte doit ressortir en déficit, et donc annuler le commit."""
    raw = tmp_path / "raw"
    pivot = tmp_path / "pivot"
    ecrire_profil_brut(raw, "aline", _profil_brut("aline", {"16": 10, "17": 5}))
    _ecrire_pivot(pivot, "aline", nb_amendements=9)

    rapport = auditer(raw, pivot, seuil=0)

    deficits = [e for e in rapport["deficits"] if e["champ_pivot"] == "amendements"]
    assert deficits, "le déficit d'amendements doit être vu à travers les tranches"
    assert deficits[0]["collecte"] == 15
    assert deficits[0]["publie"] == 9


def test_aucun_deficit_quand_tout_est_publie(tmp_path):
    raw = tmp_path / "raw"
    pivot = tmp_path / "pivot"
    ecrire_profil_brut(raw, "aline", _profil_brut("aline", {"16": 10, "17": 5}))
    _ecrire_pivot(pivot, "aline", nb_amendements=15)

    rapport = auditer(raw, pivot, seuil=0)
    assert not [e for e in rapport["deficits"] if e["champ_pivot"] == "amendements"]
