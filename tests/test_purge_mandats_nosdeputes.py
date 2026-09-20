"""#718 — les mandats écrits par la collecte NosDéputés quittent les profils,
ceux d'une source vivante restent.

Toutes les entrées sont **copiées** du corpus (`origin/main` `186375320`) :
`damien-abad` et `gabriel-attal` au pivot, `jean-luc-melenchon` au brut.
"""

import copy
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from purge_mandats_nosdeputes import porte_la_forme_heritee, main, purge_profil  # noqa: E402

_VIDES = {"source_url": None, "position_dans_hemicycle": None, "mode_declenchement": None,
          "suspendu_pour_fonction_gouvernementale": None}

#: NosDéputés, pivot — un groupe politique rangé en `commission`.
PIVOT_GROUPE_EN_COMMISSION = {"label": "Députés Non Inscrits", "categorie": "commission", "fonction": "membre", "debut": "2022-06-24", "fin": "2022-06-29", "actif": False, **_VIDES}
#: NosDéputés, pivot — le mandat de député, sans estampille.
PIVOT_MANDAT_NOSDEPUTES = {"label": "Mandat parlementaire", "categorie": "mandat_electif", "fonction": "mandat", "debut": "2017-06-21", "fin": "2018-11-16", "actif": False, **_VIDES}
#: AN, pivot — le même mandat, estampillé : `type` aussi en minuscule, mais établi.
PIVOT_MANDAT_AN = {"label": "Mandat parlementaire (La République en Marche)", "categorie": "mandat_electif", "fonction": "mandat", "debut": "2017-06-18", "fin": "2018-11-16", "actif": False, "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/tous_acteurs_mandats_organes_xi_legislature/AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip", "position_dans_hemicycle": None, "mode_declenchement": None, "suspendu_pour_fonction_gouvernementale": None, "chambre": "AN", "categorie_source": "an"}
#: Non estampillée, fonction capitalisée : pas NosDéputés, conservée.
PIVOT_GOUVERNEMENT_SANS_ESTAMPILLE = {"label": "Gouvernement", "categorie": "fonction_gouvernementale", "fonction": "Ministre des solidarités, de l'autonomie et des personnes handicapées", "debut": "2022-06-24", "fin": "2022-07-05", "actif": False, **_VIDES}

#: Brut, `jean-luc-melenchon`.
BRUT_AN = {"categorie": "commission", "type": "Membre", "label": "Commission des affaires étrangères", "debut": "2022-01-14", "fin": "2022-06-21", "actif": False, "categorie_source": "an"}
BRUT_NOSDEPUTES = {"categorie": "commission", "type": "membre", "label": "Commission des affaires étrangères", "debut": "2022-01-14", "fin": None, "actif": True}


def test_la_signature_exige_les_deux_conditions():
    assert porte_la_forme_heritee(PIVOT_GROUPE_EN_COMMISSION)
    assert porte_la_forme_heritee(PIVOT_MANDAT_NOSDEPUTES)
    assert porte_la_forme_heritee(BRUT_NOSDEPUTES)
    # Estampillée : une source vivante l'a établie, même en minuscule.
    assert not porte_la_forme_heritee(PIVOT_MANDAT_AN)
    assert not porte_la_forme_heritee(BRUT_AN)
    # Sans estampille, mais capitalisée : pas la forme NosDéputés.
    assert not porte_la_forme_heritee(PIVOT_GOUVERNEMENT_SANS_ESTAMPILLE)


def test_une_fonction_absente_ne_prouve_rien():
    sans_fonction = {k: v for k, v in PIVOT_GROUPE_EN_COMMISSION.items() if k != "fonction"}

    assert not porte_la_forme_heritee(sans_fonction)


def test_le_profil_garde_ce_qu_une_source_vivante_etablit():
    profil, retires = purge_profil({"mandats": copy.deepcopy([
        PIVOT_MANDAT_AN, PIVOT_MANDAT_NOSDEPUTES,
        PIVOT_GROUPE_EN_COMMISSION, PIVOT_GOUVERNEMENT_SANS_ESTAMPILLE,
    ])})

    assert retires == [PIVOT_MANDAT_NOSDEPUTES, PIVOT_GROUPE_EN_COMMISSION]
    assert profil["mandats"] == [PIVOT_MANDAT_AN, PIVOT_GOUVERNEMENT_SANS_ESTAMPILLE]


def test_le_brut_est_purge_sur_type(tmp_path):
    chemin = tmp_path / "jean-luc-melenchon.json"
    chemin.write_text(json.dumps({"mandats": [BRUT_AN, BRUT_NOSDEPUTES]}), encoding="utf-8")

    assert main(["--profiles-dir", str(tmp_path), "--apply"]) == 0

    assert json.loads(chemin.read_text(encoding="utf-8"))["mandats"] == [BRUT_AN]


def test_le_pivot_recompose_ses_chambres(tmp_path):
    chemin = tmp_path / "gabriel-attal.pivot.json"
    chemin.write_text(json.dumps({
        "id": "gabriel-attal", "chambre": "AN", "chambres": ["AN"],
        "mandats": [PIVOT_MANDAT_AN, PIVOT_MANDAT_NOSDEPUTES],
    }), encoding="utf-8")

    main(["--profiles-dir", str(tmp_path), "--apply"])

    ecrit = json.loads(chemin.read_text(encoding="utf-8"))
    assert ecrit["mandats"] == [PIVOT_MANDAT_AN]
    assert ecrit["chambres"] == ["AN"]


def test_sans_apply_rien_n_est_ecrit(tmp_path):
    chemin = tmp_path / "damien-abad.pivot.json"
    contenu = json.dumps({"mandats": [PIVOT_GROUPE_EN_COMMISSION]})
    chemin.write_text(contenu, encoding="utf-8")

    main(["--profiles-dir", str(tmp_path)])

    assert chemin.read_text(encoding="utf-8") == contenu


def test_idempotent():
    une_fois, _ = purge_profil({"mandats": copy.deepcopy([PIVOT_MANDAT_AN, PIVOT_GROUPE_EN_COMMISSION])})
    _, retires = purge_profil(copy.deepcopy(une_fois))

    assert retires == []
