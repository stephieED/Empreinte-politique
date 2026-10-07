#!/usr/bin/env python3
"""
Tests du lot #859 — les mandats postérieurs au 19/06/2002 que la source ne
porte pas, cités à la main.

Ce qu'ils verrouillent :

- **les trois lignes de Xavier Bertrand**, telles que relues le 06/10/2026 sur
  Sycomore et sur quatre décrets, et le motif de chacune ;
- **un motif se vérifie sur la ligne** : une fonction gouvernementale d'avant le
  17/05/2007 manque à la source pour tout le monde, un mandat de député non ;
- **le champ ne se confond pas avec `mandats_anterieurs`**, dont l'interface
  publie « exercés avant le 19 juin 2002 » ;
- **une ligne que le corpus finit par porter n'est plus publiée**, et elle est
  rendue à l'appelant pour être signalée ;
- **non relu n'est pas « aucun »** (§2 règle 5).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from mandats_anterieurs import (  # noqa: E402
    BORNE_COUVERTURE_AN,
    BORNE_COUVERTURE_GOUVERNEMENT,
    TableMandatsAnterieursInvalide,
    appliquer_mandats_absents_de_la_source,
    charger_absents,
    charger_table,
)
from schema_pivot import (  # noqa: E402
    valider_mandats_absents_de_la_source,
    validate_profil,
)

pytestmark = pytest.mark.lit_reference_committee("config/mandats_anterieurs.json")

TABLE = RACINE / "config" / "mandats_anterieurs.json"

# Les mandats nationaux que la fiche de Xavier Bertrand LIT à la source, copiés
# de pivot_data/profiles/xavier-bertrand.pivot.json le 06/10/2026 (privé
# 106ceb16e) et réduits aux clés que le lot regarde.
MANDATS_DU_CORPUS = [
    {"categorie": "fonction_gouvernementale", "fonction": "Ministre", "debut": "2007-05-18", "fin": "2007-06-18"},
    {"categorie": "fonction_gouvernementale", "fonction": "Ministre", "debut": "2007-06-19", "fin": "2008-03-17"},
    {"categorie": "mandat_electif", "chambre": "AN", "debut": "2007-06-20", "fin": "2012-06-19"},
    {"categorie": "mandat_electif", "chambre": "AN", "debut": "2012-06-20", "fin": "2016-01-12"},
]


def _fiche(slug: str = "xavier-bertrand", provenance: str = "candidat_declare") -> dict:
    return {"id": slug, "meta": {"provenance": provenance}, "mandats": copy.deepcopy(MANDATS_DU_CORPUS)}


def _table(tmp_path: Path, lignes: list[dict]) -> Path:
    chemin = tmp_path / "table.json"
    chemin.write_text(
        json.dumps({"candidats": {}, "absents_de_la_source": {"x": lignes}}), encoding="utf-8"
    )
    return chemin


def _ligne(**surcharge) -> dict:
    ligne = {
        "institution": "gouvernement",
        "libelle": "Ministre de la santé et des solidarités",
        "debut": "2005-06-02",
        "fin": "2007-03-26",
        "source_url": "https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000000629661",
        "verifie_le": "2026-10-06",
        "absence": {"motif": "gouvernement_anterieur_a_la_source", "constate_le": "2026-10-06"},
    }
    ligne.update(surcharge)
    return ligne


# ---------------------------------------------------------------------------
# La table committée
# ---------------------------------------------------------------------------

def test_les_trois_lignes_de_xavier_bertrand():
    absents = charger_absents(TABLE)
    assert set(absents) == {"xavier-bertrand"}
    assert [(l["institution"], l["debut"], l["fin"], l["absence"]["motif"]) for l in absents["xavier-bertrand"]] == [
        ("assemblee_nationale", "2002-06-19", "2004-04-30", "mandat_non_porte_par_la_source"),
        ("gouvernement", "2004-03-31", "2005-05-31", "gouvernement_anterieur_a_la_source"),
        ("gouvernement", "2005-06-02", "2007-03-26", "gouvernement_anterieur_a_la_source"),
    ]


def test_le_bloc_des_anterieurs_n_a_pas_bouge():
    """Xavier Bertrand reste « aucun mandat avant le 19/06/2002 », et c'est vrai."""
    entree = charger_table(TABLE)["xavier-bertrand"]
    assert entree["mandats"] == [] and entree["constat"]["methode"] == "lecture_fiche_sycomore"


def test_la_borne_gouvernementale_n_est_pas_celle_de_l_assemblee():
    assert BORNE_COUVERTURE_AN == "2002-06-19"
    assert BORNE_COUVERTURE_GOUVERNEMENT == "2007-05-17"
    meta = json.loads(TABLE.read_text(encoding="utf-8"))["_meta"]
    assert meta["borne_couverture_gouvernement"] == BORNE_COUVERTURE_GOUVERNEMENT


# ---------------------------------------------------------------------------
# Ce que la table refuse
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "surcharge, mot",
    [
        ({"source_url": "http://exemple.fr"}, "https"),
        ({"fin": None}, "'fin' absent"),
        ({"absence": None}, "absence.motif"),
        ({"absence": {"motif": "gouvernement_anterieur_a_la_source"}}, "constate_le"),
        # Terminée avant 2002 : c'est un mandat ANTÉRIEUR, l'autre bloc.
        ({"debut": "2000-03-27", "fin": "2001-03-27"}, "'candidats'"),
        # Terminée après le 17/05/2007 : la source couvre, le motif est faux.
        ({"fin": "2008-01-01"}, "17"),
        # Un mandat de député n'est jamais « gouvernement antérieur ».
        ({"institution": "assemblee_nationale"}, "fonction gouvernementale"),
        # Une fonction d'avant 2007 manque pour tout le monde : motif imposé.
        ({"absence": {"motif": "mandat_non_porte_par_la_source", "constate_le": "2026-10-06"}}, "pour tout le"),
    ],
)
def test_une_ligne_fautive_est_refusee(tmp_path, surcharge, mot):
    with pytest.raises(TableMandatsAnterieursInvalide) as exc:
        charger_absents(_table(tmp_path, [_ligne(**surcharge)]))
    assert mot in str(exc.value)


def test_une_entree_vide_est_refusee(tmp_path):
    with pytest.raises(TableMandatsAnterieursInvalide):
        charger_absents(_table(tmp_path, []))


def test_un_fichier_sans_le_bloc_rend_une_table_vide(tmp_path):
    chemin = tmp_path / "t.json"
    chemin.write_text(json.dumps({"candidats": {}}), encoding="utf-8")
    assert charger_absents(chemin) == {}


# ---------------------------------------------------------------------------
# Sur la fiche
# ---------------------------------------------------------------------------

def test_la_fiche_recoit_ses_trois_lignes_dans_un_champ_a_part():
    fiche = _fiche()
    fiche["mandats_anterieurs"] = []
    ecartees = appliquer_mandats_absents_de_la_source(fiche, charger_absents(TABLE))
    assert ecartees == []
    assert len(fiche["mandats_absents_de_la_source"]) == 3
    # L'interface publie de `mandats_anterieurs` « exercés avant le 19 juin
    # 2002 » : aucune de ces lignes ne doit y entrer.
    assert fiche["mandats_anterieurs"] == []
    assert valider_mandats_absents_de_la_source(fiche) == []


def test_un_candidat_hors_du_bloc_est_non_relu_jamais_vide():
    fiche = _fiche("segolene-royal")
    appliquer_mandats_absents_de_la_source(fiche, charger_absents(TABLE))
    assert fiche["mandats_absents_de_la_source"] is None
    assert fiche["mandats_absents_de_la_source_non_resolu"] == {"motif": "non_relu"}
    assert valider_mandats_absents_de_la_source(fiche) == []


def test_un_membre_de_groupe_ne_recoit_rien():
    fiche = _fiche(provenance="roster_groupe")
    fiche["mandats_absents_de_la_source"] = [_ligne()]
    appliquer_mandats_absents_de_la_source(fiche, charger_absents(TABLE))
    assert "mandats_absents_de_la_source" not in fiche
    assert "mandats_absents_de_la_source_non_resolu" not in fiche


def test_une_ligne_que_le_corpus_porte_desormais_n_est_plus_publiee():
    """Le jour où l'Assemblée publie son mandat de la XIIe, la citation part."""
    fiche = _fiche()
    fiche["mandats"].append(
        {"categorie": "mandat_electif", "chambre": "AN", "debut": "2002-06-19", "fin": "2004-04-30"}
    )
    ecartees = appliquer_mandats_absents_de_la_source(fiche, charger_absents(TABLE))
    assert [l["libelle"] for l in ecartees] == ["Député de l'Aisne"]
    assert [l["institution"] for l in fiche["mandats_absents_de_la_source"]] == ["gouvernement", "gouvernement"]


def test_un_mandat_europeen_de_la_meme_periode_ne_remplace_pas_un_mandat_de_depute():
    fiche = _fiche()
    fiche["mandats"].append(
        {"categorie": "mandat_electif", "chambre": "PE", "debut": "2002-01-01", "fin": "2004-12-31"}
    )
    assert appliquer_mandats_absents_de_la_source(fiche, charger_absents(TABLE)) == []


def test_le_champ_est_repose_jamais_fusionne():
    absents = charger_absents(TABLE)
    fiche = _fiche()
    fiche["mandats_absents_de_la_source"] = [_ligne(libelle="ligne périmée")]
    appliquer_mandats_absents_de_la_source(fiche, absents)
    assert "ligne périmée" not in json.dumps(fiche, ensure_ascii=False)


# ---------------------------------------------------------------------------
# validate_profil
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valeur, non_resolu",
    [
        (None, None),                       # null sans motif
        ([], None),                         # liste vide : affirmerait « tout y est »
        ([_ligne(absence=None)], None),     # ligne sans motif d'absence
        ([_ligne(source_url=None)], None),  # ligne sans source
        ([_ligne()], {"motif": "non_relu"}),
    ],
)
def test_validate_profil_tient_le_champ(valeur, non_resolu):
    fiche = {"mandats_absents_de_la_source": valeur}
    if non_resolu is not None:
        fiche["mandats_absents_de_la_source_non_resolu"] = non_resolu
    assert valider_mandats_absents_de_la_source(fiche)
    assert any("mandats_absents_de_la_source" in e for e in validate_profil(fiche))
