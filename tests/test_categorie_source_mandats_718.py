#!/usr/bin/env python3
"""
test_categorie_source_mandats_718.py — Le référentiel qui a établi la catégorie
d'un mandat est estampillé, et son absence n'accuse personne (#718).

Le constat : **12 % des mandats `categorie: "commission"` des 13 candidats
déclarés n'en sont pas** — 2,1 % sur les 641 profils, et nommer la population
change le chiffre d'un ordre de grandeur. Trois natures s'y mêlent : des onglets
de page hérités du parcours NosDéputés retiré par #529, des groupes politiques,
et surtout des **mandats réels** (commissions d'enquête, groupes d'études,
délégations) que NosDéputés aplatissait sous `commission` et que l'AN nomme
autrement, si bien que la purge de #387 ne peut pas les apparier.

La catégorie était déjà sourcée — `_TYPE_ORGANE_TO_CATEGORIE` la tire du
`codeType` de l'organe AMO30. Ce qui manquait n'était pas un critère, c'était de
pouvoir dire, dans un corpus où la fusion est additive, **quelles entrées un
référentiel a qualifiées**.

Ce que ces tests verrouillent, et c'est le cœur de l'arbitrage : il n'existe
**aucune** valeur « héritée ». Une entrée que la collecte neuve ne rend pas reste
**sans clé** — « personne ne l'a établie », jamais « sa catégorie est fausse ».
La nuance est celle que #486 a payée : 29 des 511 `mandat_electif` publiés sont
des entrées que la source ne sert plus, et les accuser aurait été un fait faux
de plus.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import (  # noqa: E402
    _mandat_key,
    backfill_mandat_categorie_source,
    merge_pivot_profile,
    merge_raw_profile,
)
from normalize_profil import _normalize_mandat  # noqa: E402
from schema_pivot import KNOWN_CATEGORIE_SOURCES, validate_profil  # noqa: E402


def _mandat(**kw):
    base = {
        "categorie": "commission",
        "type": "Président",
        "label": "Commission des finances",
        "debut": "2022-06-22",
        "fin": None,
        "actif": True,
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------
# 1. Le vocabulaire, fermé, et l'absence qui est un sens
# --------------------------------------------------------------------------

def test_le_vocabulaire_nomme_les_referentiels_et_rien_d_autre():
    """Il n'y a pas de valeur « héritée » : ce serait une accusation, et le
    corpus ne permet pas de la porter (#486)."""
    # #885 ajoute « senat » : data.senat.fr classe ses propres organes par ses
    # tables de types, et c'est donc un référentiel au même titre que les deux
    # premiers. Le gel se **retourne**, il ne se supprime pas — c'est lui qui
    # empêche une valeur inventée d'entrer sans que personne ne l'ait voulue.
    #
    # #922 ajoute « rne » : le Répertoire national des élus classe lui aussi ses
    # propres entrées — un fichier par type de mandat, et le type est le fichier.
    # Ce test a fait exactement son travail le 15/09/2026 : la valeur a été
    # ajoutée au schéma, et il a refusé de passer tant que personne ne l'avait
    # inscrite ICI. C'est ce refus qui distingue un vocabulaire fermé d'une
    # liste qui s'allonge toute seule.
    assert KNOWN_CATEGORIE_SOURCES == frozenset({"an", "europarl", "senat", "rne"})


def test_la_cle_absente_est_licite():
    profil = {
        "id": "x", "nom": "X", "chambres": ["AN"], "chambre": "AN",
        "mandats": [_mandat()],
    }
    assert not [e for e in validate_profil(profil) if "categorie_source" in e]


@pytest.mark.parametrize("valeur", ["an", "europarl"])
def test_les_valeurs_du_vocabulaire_sont_licites(valeur):
    profil = {
        "id": "x", "nom": "X", "chambres": ["AN"], "chambre": "AN",
        "mandats": [_mandat(categorie_source=valeur)],
    }
    assert not [e for e in validate_profil(profil) if "categorie_source" in e]


def test_un_referentiel_invente_est_refuse():
    profil = {
        "id": "x", "nom": "X", "chambres": ["AN"], "chambre": "AN",
        "mandats": [_mandat(categorie_source="nosdeputes")],
    }
    erreurs = [e for e in validate_profil(profil) if "categorie_source" in e]
    assert erreurs and "nosdeputes" in erreurs[0]


def test_la_cle_presente_a_none_est_refusee():
    """`None` dirait la même chose que l'absence, sous la forme d'un constat —
    et un constat, ici, n'a pas été fait (§2 règle 5)."""
    profil = {
        "id": "x", "nom": "X", "chambres": ["AN"], "chambre": "AN",
        "mandats": [_mandat(categorie_source=None)],
    }
    assert [e for e in validate_profil(profil) if "categorie_source" in e]


# --------------------------------------------------------------------------
# 2. Le report nommé — sixième occurrence de la même famille
# --------------------------------------------------------------------------

def test_le_report_estampille_une_entree_deja_collectee():
    """`_mandat_key` ne contient pas le champ : sans report, l'entrée ancienne
    gagne à chaque régénération et n'acquiert jamais l'estampille."""
    ancienne = [_mandat()]
    neuve = [_mandat(categorie_source="an")]

    resultat = backfill_mandat_categorie_source(ancienne, neuve, _mandat_key)

    assert resultat[0]["categorie_source"] == "an"


def test_le_report_n_ecrase_jamais_une_estampille_posee():
    ancienne = [_mandat(categorie_source="europarl")]
    neuve = [_mandat(categorie_source="an")]

    resultat = backfill_mandat_categorie_source(ancienne, neuve, _mandat_key)

    assert resultat[0]["categorie_source"] == "europarl"


def test_une_entree_que_la_collecte_ne_rend_plus_reste_SANS_cle():
    """Le point d'arbitrage du lot. Une entrée absente de la collecte neuve
    n'est pas « héritée » : elle est non établie. #486 — 29 des 511
    `mandat_electif` publiés sont des entrées que la source ne sert plus."""
    ancienne = [_mandat(label="Groupe d'études polices municipales", debut="2017-01-01")]
    neuve = [_mandat(categorie_source="an")]

    resultat = backfill_mandat_categorie_source(ancienne, neuve, _mandat_key)

    orpheline = [m for m in resultat if m["label"] == "Groupe d'études polices municipales"][0]
    assert "categorie_source" not in orpheline


def test_le_report_ne_touche_aucun_autre_champ_et_ne_reordonne_rien():
    ancienne = [_mandat(label="A"), _mandat(label="B")]
    neuve = [_mandat(label="B", categorie_source="an")]

    resultat = backfill_mandat_categorie_source(ancienne, neuve, _mandat_key)

    assert [m["label"] for m in resultat] == ["A", "B"]
    assert resultat[0] == _mandat(label="A")


def test_une_collecte_vide_ne_reporte_rien():
    ancienne = [_mandat()]
    assert backfill_mandat_categorie_source(ancienne, None, _mandat_key) == ancienne
    assert backfill_mandat_categorie_source(ancienne, [], _mandat_key) == ancienne


def test_le_report_est_cable_dans_la_fusion_brute():
    """Le report le mieux écrit ne sert à rien s'il n'est pas appelé — c'est le
    défaut que #668 a payé pendant toute une remédiation."""
    ancien = {"id": "x", "mandats": [_mandat()]}
    neuf = {"id": "x", "mandats": [_mandat(categorie_source="an")]}

    fusionne = merge_raw_profile(ancien, neuf)

    assert fusionne["mandats"][0]["categorie_source"] == "an"


# --------------------------------------------------------------------------
# 3. La traversée vers le pivot, en clé facultative
# --------------------------------------------------------------------------

def test_le_pivot_publie_l_estampille_quand_elle_existe():
    assert _normalize_mandat(_mandat(categorie_source="an"))["categorie_source"] == "an"


def test_le_pivot_omet_la_cle_plutot_que_de_la_publier_a_null():
    """Même arbitrage que `interventions[].collecte` (#657) : l'absence est la
    forme pleine, et un `null` se lirait comme un fait sur le mandat."""
    assert "categorie_source" not in _normalize_mandat(_mandat())


def test_la_fusion_pivot_ne_perd_pas_l_estampille():
    ancien = {"id": "x", "mandats": [_normalize_mandat(_mandat())]}
    neuf = {"id": "x", "mandats": [_normalize_mandat(_mandat(categorie_source="an"))]}

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["mandats"][0].get("categorie_source") == "an"
