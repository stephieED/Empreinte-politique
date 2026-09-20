#!/usr/bin/env python3
"""
test_reprise_mandats_gouvernementaux_730.py — Huit mandats ministériels sortent
de `commission`, et aucune période ne se perd (#730).

Le critère de détection est **le typage du référentiel** : l'index d'organes AN
type `Gouvernement` en `GOUVERNEMENT`, seul libellé du référentiel dans ce cas,
et `_TYPE_ORGANE_TO_CATEGORIE` ne le mappe volontairement pas. On lit ce que la
source déclare de l'organe — on ne classe rien par ressemblance de libellé.

Deux critères ont été écartés **par la mesure**, et ces tests les gardent
écartés en gardant le bon :

- le croisement (profil × période) **seul** capture **1 036** mandats, pas 8 —
  un ministre garde ses commissions et ses groupes d'amitié ;
- le vocabulaire ministériel de #474 en capture **0** : il est fait pour les
  `libQualite` courts d'AMO30, quand ces entrées portent l'intitulé complet du
  portefeuille.

Le croisement garde un rôle, mais c'est celui de décider du **sort** de chaque
entrée reconnue : période déjà couverte par le profil → on retire ; non couverte
→ on requalifie, parce que retirer effacerait une période ministérielle réelle.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau.
"""

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from reprise_mandats_gouvernementaux import (  # noqa: E402
    CATEGORIE_CIBLE,
    _couvre,
    libelles_gouvernementaux,
    periodes_ministerielles,
    reprendre_profil,
)

GOUV = {"Gouvernement"}
PERIODES = [("2022-05-21", "2022-07-04")]


def _mandat(**kw):
    base = {
        "categorie": "commission",
        "type": "Ministre des outre-mer",
        "label": "Gouvernement",
        "debut": "2022-06-24",
        "fin": "2022-06-27",
        "actif": False,
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------
# 1. Le critère de détection vient du référentiel
# --------------------------------------------------------------------------

def test_le_referentiel_donne_les_libelles_gouvernementaux(tmp_path):
    index = tmp_path / "organes.json"
    index.write_text(json.dumps({
        "PO1": {"nom": "Gouvernement", "sigle": "BORNE", "type": "GOUVERNEMENT"},
        "PO2": {"nom": "Commission des lois", "sigle": "Lois", "type": "COMPER"},
        "PO3": {"nom": "Gouvernement", "sigle": "ATTAL", "type": "GOUVERNEMENT"},
    }), encoding="utf-8")

    assert libelles_gouvernementaux(index) == {"Gouvernement"}


def test_un_index_absent_ne_reconnait_rien(tmp_path):
    """Un critère qui ne peut pas s'établir ne se devine pas (§2 règle 5) : sans
    index, la reprise ne modifie rien plutôt que de retomber sur le libellé."""
    assert libelles_gouvernementaux(tmp_path / "absent.json") == set()


def test_un_index_illisible_ne_reconnait_rien(tmp_path):
    index = tmp_path / "organes.json"
    index.write_text("{ pas du json", encoding="utf-8")

    assert libelles_gouvernementaux(index) == set()


def test_une_entree_dun_organe_non_gouvernemental_nest_jamais_touchee():
    """C'est ce qui sépare ce lot du croisement seul, qui prenait 1 036 mandats."""
    profil = {"mandats": [_mandat(label="Commission des lois", categorie="commission")]}

    _, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert not retires and not requalifies


def test_une_entree_deja_gouvernementale_nest_pas_retouchee():
    profil = {"mandats": [_mandat(categorie=CATEGORIE_CIBLE)]}

    _, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert not retires and not requalifies


def test_une_entree_hors_de_toute_periode_publiee_nest_pas_touchee():
    """Le croisement verrouille la détection : sans appartenance publiée qui la
    recoupe, l'entrée n'est pas reconnue comme ministérielle."""
    profil = {"mandats": [_mandat(debut="2019-01-01", fin="2019-02-01")]}

    _, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert not retires and not requalifies


# --------------------------------------------------------------------------
# 2. Le sort de l'entrée, décidé par ce que le profil porte déjà
# --------------------------------------------------------------------------

def test_une_periode_deja_couverte_fait_retirer_l_entree():
    profil = {"mandats": [
        _mandat(),
        {"categorie": CATEGORIE_CIBLE, "label": "Gouvernement (BORNE)",
         "debut": "2022-05-21", "fin": "2024-01-09"},
    ]}

    profil, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert len(retires) == 1 and not requalifies
    assert [m["categorie"] for m in profil["mandats"]] == [CATEGORIE_CIBLE]


def test_une_periode_non_couverte_fait_requalifier_plutot_que_retirer():
    """Retirer effacerait du profil une période ministérielle réelle — 2 des 8."""
    profil = {"mandats": [_mandat()]}

    profil, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert not retires and len(requalifies) == 1
    (seul,) = profil["mandats"]
    assert seul["categorie"] == CATEGORIE_CIBLE
    # Rien d'autre ne bouge : la période, le libellé et la fonction sont ceux
    # que l'entrée portait déjà — on ne fabrique aucun fait.
    assert seul["debut"] == "2022-06-24" and seul["fin"] == "2022-06-27"
    assert seul["type"] == "Ministre des outre-mer"


def test_un_simple_chevauchement_ne_vaut_pas_couverture():
    """Deux intervalles qui se touchent d'un jour décrivent des faits
    différents : retirer sur cette base perdrait la partie non couverte."""
    profil = {"mandats": [
        _mandat(debut="2022-06-24", fin="2022-08-30"),
        {"categorie": CATEGORIE_CIBLE, "label": "Gouvernement (BORNE)",
         "debut": "2022-05-21", "fin": "2022-07-04"},
    ]}

    _, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert not retires and len(requalifies) == 1


@pytest.mark.parametrize("d2,f2,attendu", [
    ("2022-06-01", "2022-06-30", True),    # strictement contenu
    ("2022-05-21", "2022-07-04", True),    # bornes identiques
    ("2022-05-20", "2022-06-30", False),   # déborde à gauche
    ("2022-06-01", "2022-07-05", False),   # déborde à droite
])
def test_la_couverture_exige_le_recouvrement_complet(d2, f2, attendu):
    assert _couvre("2022-05-21", "2022-07-04", d2, f2) is attendu


def test_une_entree_sans_date_nest_jamais_declaree_couverte():
    assert _couvre("2022-05-21", "2022-07-04", None, None) is False


# --------------------------------------------------------------------------
# 3. La lecture des appartenances publiées
# --------------------------------------------------------------------------

def test_les_periodes_sont_indexees_par_slug_jamais_par_nom(tmp_path):
    """Un profil brut ne porte pas de `nom`, et apparier deux corpus sur un nom
    d'affichage est ce que #487 et #668 ont fait payer : un nom d'usage change,
    un identifiant non."""
    (tmp_path / "gouvernement-X.json").write_text(json.dumps({"membres": [
        {"membre_id": "jean-dupont", "nom": "Jean Dupont",
         "debut": "2022-05-21", "fin": "2022-07-04"},
        {"membre_id": None, "nom": "Sans slug", "debut": "2022-05-21", "fin": None},
    ]}), encoding="utf-8")

    periodes = periodes_ministerielles(tmp_path)

    assert periodes == {"jean-dupont": [("2022-05-21", "2022-07-04")]}


def test_une_fin_absente_est_une_periode_ouverte(tmp_path):
    (tmp_path / "g.json").write_text(json.dumps({"membres": [
        {"membre_id": "x", "debut": "2024-01-01", "fin": None}]}), encoding="utf-8")

    assert periodes_ministerielles(tmp_path)["x"] == [("2024-01-01", "9999-12-31")]


def test_une_fiche_illisible_est_ignoree_sans_faire_echouer(tmp_path):
    (tmp_path / "cassee.json").write_text("{", encoding="utf-8")
    (tmp_path / "bonne.json").write_text(json.dumps({"membres": [
        {"membre_id": "x", "debut": "2024-01-01"}]}), encoding="utf-8")

    assert set(periodes_ministerielles(tmp_path)) == {"x"}


# --------------------------------------------------------------------------
# 4. Idempotence
# --------------------------------------------------------------------------

def test_une_seconde_passe_ne_trouve_plus_rien():
    profil = {"mandats": [_mandat()]}

    profil, _, _ = reprendre_profil(profil, GOUV, PERIODES)
    profil, retires, requalifies = reprendre_profil(profil, GOUV, PERIODES)

    assert not retires and not requalifies
