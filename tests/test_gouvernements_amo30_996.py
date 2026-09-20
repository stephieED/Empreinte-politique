"""#996 lot 1 — la liste des gouvernements lue dans AMO30, plus écrite à la main.

Les organes ci-dessous sont COPIÉS de l'archive AMO30 du 17/08/2026
(`json/organe/PO*.json`), réduits aux champs lus ; un organe `GP` sert de témoin.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from gouvernements_amo30 import (  # noqa: E402
    GouvernementsIndisponibles,
    construire,
    lire_organes_gouvernement,
    main,
    nom_gouvernement,
)


def _organe(uid, abrege, debut, fin, code_type="GOUVERNEMENT"):
    return {"organe": {"uid": uid, "codeType": code_type, "libelle": "Gouvernement",
                       "libelleEdition": "du Gouvernement", "libelleAbrege": abrege,
                       "libelleAbrev": "GVT",
                       "viMoDe": {"dateDebut": debut, "dateAgrement": None, "dateFin": fin},
                       "legislature": None, "regime": None, "organeParent": None}}


ORGANES = [
    _organe("PO382939", "FILLON 1", "2007-05-17", "2007-06-18"),
    _organe("PO384206", "FILLON 2", "2007-06-18", "2010-11-13"),
    _organe("PO717173", "PHILIPPE", "2017-05-18", "2017-06-19"),
    _organe("PO725688", "PHILIPPE 2", "2017-06-20", "2020-07-06"),
    _organe("PO715793", "CAZENEUVE", "2016-12-07", "2017-05-17"),
    _organe("PO873418", "LECORNU", "2025-09-10", "2025-10-10"),
    _organe("PO873634", "LECORNU II", "2025-10-11", None),
]


def _zip(tmp_path, organes, avec_gp=True):
    chemin = tmp_path / "acteurs_historique.zip"
    with zipfile.ZipFile(chemin, "w") as zf:
        for o in organes:
            zf.writestr(f"json/organe/{o['organe']['uid']}.json", json.dumps(o))
        if avec_gp:
            gp = _organe("PO800520", "RE", "2022-06-28", None, code_type="GP")
            zf.writestr("json/organe/PO800520.json", json.dumps(gp))
        zf.writestr("json/acteur/PA1.json", json.dumps({"acteur": {"uid": "PA1"}}))
    return chemin


def test_seuls_les_organes_gouvernement_sont_lus_et_tries(tmp_path):
    organes = lire_organes_gouvernement(_zip(tmp_path, ORGANES))

    assert [o["libelle_an"] for o in organes] == [
        "FILLON 1", "FILLON 2", "CAZENEUVE", "PHILIPPE", "PHILIPPE 2", "LECORNU", "LECORNU II"]
    assert organes[-1] == {"organe_ref": "PO873634", "libelle_an": "LECORNU II",
                           "debut": "2025-10-11", "fin": None}


@pytest.mark.parametrize("libelle, attendu", [
    ("FILLON 2", "Gouvernement Fillon II"),
    ("PHILIPPE", "Gouvernement Philippe I"),   # un successeur numéroté existe
    ("LECORNU", "Gouvernement Lecornu I"),     # successeur en chiffres romains
    ("LECORNU II", "Gouvernement Lecornu II"),
    ("CAZENEUVE", "Gouvernement Cazeneuve"),   # pas de successeur : pas de « I »
])
def test_le_nom_met_en_forme_le_libelle_de_la_source(libelle, attendu):
    libelles = [o["organe"]["libelleAbrege"] for o in ORGANES]
    assert nom_gouvernement(libelle, libelles) == attendu


def test_les_identifiants_de_la_liste_manuelle_sont_conserves(tmp_path):
    """Les 10 fiches existantes gardent leur identifiant et leur fichier."""
    doc = construire(lire_organes_gouvernement(_zip(tmp_path, ORGANES)))
    par_id = {g["gouvernement_id"]: g for g in doc["gouvernements"]}

    assert par_id["gouvernement:FILLON_2"]["fichier"] == "gouvernement-FILLON_2.json"
    assert par_id["gouvernement:PHILIPPE"]["nom"] == "Gouvernement Philippe I"
    assert par_id["gouvernement:LECORNU_II"]["fichier"] == "gouvernement-LECORNU_II.json"
    assert par_id["gouvernement:LECORNU_II"]["periode"] == {"debut": "2025-10-11", "fin": None}
    assert par_id["gouvernement:FILLON_1"]["organe_ref"] == "PO382939"


def test_l_entete_declare_la_borne_de_disponibilite(tmp_path):
    doc = construire(lire_organes_gouvernement(_zip(tmp_path, ORGANES)))
    assert "FILLON 1 (2007-05-17)" in doc["_meta"]["avertissement"]


def test_une_archive_sans_gouvernement_leve_sans_ecrire(tmp_path):
    sortie = tmp_path / "gouvernements_reels.json"
    sortie.write_text('{"gouvernements": ["liste committée"]}', encoding="utf-8")

    with pytest.raises(GouvernementsIndisponibles):
        main(["--zip", str(_zip(tmp_path, [])), "--out", str(sortie)])

    assert json.loads(sortie.read_text())["gouvernements"] == ["liste committée"]


@pytest.mark.lit_reference_committee("raw_data/gouvernements_reels.json")
def test_la_liste_du_depot_couvre_fillon_i_a_lecornu_ii():
    """La liste committée est celle qu'AMO30 produit : 17 gouvernements au
    17/08/2026, dont les 7 absents de la liste manuelle."""
    payload = json.loads((RACINE / "raw_data" / "gouvernements_reels.json").read_text(encoding="utf-8"))
    libelles = {g["libelle_an"] for g in payload["gouvernements"]}
    assert {"FILLON 1", "AYRAULT 1", "AYRAULT 2", "VALLS", "VALLS 2", "CAZENEUVE", "LECORNU"} <= libelles
    assert all(g.get("organe_ref", "").startswith("PO") for g in payload["gouvernements"])


def test_le_comptage_des_membres_recenses_accompagne_chaque_gouvernement(tmp_path):
    """Le dénominateur de `membres[]` : « 2 des 21 membres recensés »."""
    import zipfile

    chemin = _zip(tmp_path, ORGANES[:2])
    with zipfile.ZipFile(chemin, "a") as zf:
        for uid, organe, debut, fin in [
            ("PA1", "PO382939", "2007-05-18", "2007-06-18"),
            ("PA2", "PO382939", "2007-05-18", "2007-06-18"),
            ("PA2", "PO384206", "2007-06-19", "2010-11-13"),  # même personne, deux gouvernements
        ]:
            zf.writestr(f"json/acteur/{uid}-{organe}.json", json.dumps({"acteur": {
                "uid": uid, "etatCivil": {"ident": {"prenom": "A", "nom": uid}},
                "mandats": {"mandat": [{"typeOrgane": "GOUVERNEMENT",
                                        "organes": {"organeRef": organe},
                                        "dateDebut": debut, "dateFin": fin}]}}}))

    from gouvernements_amo30 import compter_membres

    comptes = compter_membres(chemin)
    doc = construire(lire_organes_gouvernement(chemin), comptes)
    par_id = {g["gouvernement_id"]: g for g in doc["gouvernements"]}

    assert par_id["gouvernement:FILLON_1"]["membres_recenses"] == 2
    assert par_id["gouvernement:FILLON_2"]["membres_recenses"] == 1


def test_un_gouvernement_sans_comptage_porte_none(tmp_path):
    """Un dénominateur inventé ferait lire « 2 des 2 membres »."""
    doc = construire(lire_organes_gouvernement(_zip(tmp_path, ORGANES)), {})
    assert all(g["membres_recenses"] is None for g in doc["gouvernements"])
