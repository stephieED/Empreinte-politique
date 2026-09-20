"""#996 lot 2 — le roster d'un gouvernement vient d'AMO30, et ses membres
reçoivent un identifiant de profil.

Aucun module ne pouvait donner de slug à une personne jamais députée : l'index
GP ne connaît que les acteurs porteurs d'un mandat de groupe. Mesuré le
17/09/2026 sur l'archive du 17/08 : 311 membres, 106 slugs repris de la table de
correspondance, **205 fabriqués**, aucun acteur sans slug.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from gouvernement_roster_an import (  # noqa: E402
    RosterGouvernementIndisponible,
    construire_index_gouvernements,
    deriver_membres,
    resoudre_slugs_des_membres,
)


def _archive(tmp_path, acteurs, organes=(("PO873418", "LECORNU", "2025-09-10", "2025-10-10"),)):
    chemin = tmp_path / "acteurs_historique.zip"
    with zipfile.ZipFile(chemin, "w") as zf:
        for uid, sigle, debut, fin in organes:
            zf.writestr(f"json/organe/{uid}.json", json.dumps({"organe": {
                "uid": uid, "codeType": "GOUVERNEMENT", "libelleAbrege": sigle,
                "viMoDe": {"dateDebut": debut, "dateFin": fin}}}))
        zf.writestr("json/organe/PO800520.json", json.dumps({"organe": {
            "uid": "PO800520", "codeType": "GP", "libelleAbrev": "RE",
            "viMoDe": {"dateDebut": "2022-06-28", "dateFin": None}}}))
        for uid, prenom, nom, mandats in acteurs:
            zf.writestr(f"json/acteur/{uid}.json", json.dumps({"acteur": {
                "uid": {"#text": uid}, "etatCivil": {"ident": {"prenom": prenom, "nom": nom}},
                "mandats": {"mandat": mandats}}}))
    return chemin


def _mandat(organe_ref, debut, fin=None, type_organe="GOUVERNEMENT"):
    return {"typeOrgane": type_organe, "organes": {"organeRef": organe_ref},
            "dateDebut": debut, "dateFin": fin}


def test_l_index_ne_retient_que_les_organes_gouvernement(tmp_path):
    chemin = _archive(tmp_path, [
        ("PA387829", "Rachida", "Dati", [_mandat("PO873418", "2025-09-10", "2025-10-10")]),
        ("PA2", "Jean", "Dupont", [_mandat("PO800520", "2022-06-28", None, "GP")]),
    ])

    index = construire_index_gouvernements(chemin)

    assert list(index["organes"]) == ["PO873418"]
    assert index["acteurs"] == {"PA387829": "Rachida Dati"}
    assert index["mandats"]["PO873418"] == [["PA387829", "2025-09-10", "2025-10-10"]]


def test_une_archive_sans_gouvernement_leve(tmp_path):
    with pytest.raises(RosterGouvernementIndisponible):
        construire_index_gouvernements(_archive(tmp_path, [], organes=()))


def test_un_ministre_jamais_depute_recoit_un_slug_fabrique(tmp_path):
    """Le cas des 124 membres jamais députés : l'index GP les ignore."""
    index = construire_index_gouvernements(_archive(tmp_path, [
        ("PA387829", "Rachida", "Dati", [_mandat("PO873418", "2025-09-10", "2025-10-10")]),
    ]))

    slugs, origines, non_attribues = resoudre_slugs_des_membres(index, {"acteurs": {}})

    assert slugs == {"PA387829": "rachida-dati"}
    assert origines == {"PA387829": "fabrique"}
    assert non_attribues == []


def test_l_univers_de_collision_inclut_les_deputes(tmp_path):
    """Un ministre et un député homonymes ne peuvent pas recevoir le même slug."""
    index = construire_index_gouvernements(_archive(tmp_path, [
        ("PA100", "Jean", "Martin", [_mandat("PO873418", "2025-09-10")]),
    ]))

    slugs, _origines, non_attribues = resoudre_slugs_des_membres(
        index, {"acteurs": {"PA200": "Jean Martin"}})

    assert slugs == {}
    assert [x["motif"] for x in non_attribues] == ["homonymie_amo30"]


def test_une_personne_de_deux_gouvernements_n_entre_qu_une_fois(tmp_path):
    index = construire_index_gouvernements(_archive(tmp_path, [
        ("PA1", "Élisabeth", "Borne", [_mandat("PO873418", "2025-09-10", "2025-10-10"),
                                       _mandat("PO855052", "2024-12-14", "2025-09-09")]),
    ], organes=(("PO873418", "LECORNU", "2025-09-10", "2025-10-10"),
                ("PO855052", "BAYROU", "2024-12-14", "2025-09-09"))))
    slugs, origines, _ = resoudre_slugs_des_membres(index, {"acteurs": {}})

    membres = deriver_membres(index, slugs, origines)

    assert len(membres) == 1
    assert membres[0]["slug"] == "elisabeth-borne"
    assert membres[0]["slug_origine"] == "fabrique"
    assert [p["libelle_an"] for p in membres[0]["mandat_periodes"]] == ["BAYROU", "LECORNU"]


def test_un_acteur_sans_slug_n_entre_pas_dans_le_roster(tmp_path):
    index = construire_index_gouvernements(_archive(tmp_path, [
        ("PA1", "Jean", "Martin", [_mandat("PO873418", "2025-09-10")]),
    ]))

    membres = deriver_membres(index, {}, {})

    assert membres == []
