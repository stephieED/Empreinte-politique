#!/usr/bin/env python3
"""
Tests du lot #1168 (lot 3) — un lien se publie « établi par comparaison des
membres » quand, et seulement quand, sa mesure est écrite et passe la règle.

Arbitré le 03/10/2026 (option A) : tous les liens portent la même valeur, et la
méthodologie dit en une phrase comment ils sont établis. Ce qui rend la valeur
vraie à la lettre, c'est que la fiche ne la porte que pour un lien **mesuré** :

- la table du run porte, pour chaque lien, `{groupe_id, communs, reelus,
  anciens}` depuis #1328 (`{groupe_id, communs, base}` avant) ;
- un lien sans mesure (table écrite seule, groupe sans membre connu) ou sous le
  seuil se publie `relecture_humaine`, la valeur qui reste vraie.

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import groupes_amo30  # noqa: E402
import groupes_config  # noqa: E402
from schema_groupe import (  # noqa: E402
    ETABLI_PAR_COMPARAISON_DES_MEMBRES,
    ETABLI_PAR_RELECTURE_HUMAINE,
    ETABLISSEMENTS_SUCCESSION,
)
from test_mise_a_jour_table_groupes_1168 import _index, _table  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"
ARCHIVE = RACINE / "tests" / "fixtures" / "amo30_gp_leg16_17.zip"
JOUR = "2027-07-01"


def _deux_legislatures(communs_avec_le_premier: int, partis_ailleurs: int = 0) -> tuple[dict, dict]:
    """REN-16 (20 membres) → EPR-17 (20 membres), dont `communs` en commun.

    `partis_ailleurs` : des membres de REN-16 réélus dans un AUTRE groupe de la
    XVIIe. Ce sont eux qui font descendre la part des réélus (#1328) : sans eux,
    tout réélu de REN-16 serait à EPR-17 et la règle serait toujours atteinte.
    """
    organes = {
        "PO1": ("RE", "16", "2022-06-28", "2024-06-09", 0, 20),
        "PO2": ("EPR", "17", "2024-07-18", None, 20 - communs_avec_le_premier, 40 - communs_avec_le_premier),
    }
    if partis_ailleurs:
        organes["PO3"] = ("AUTRE", "17", "2024-07-18", None, 0, partis_ailleurs)
    index = _index(organes)
    table = _table(index, [
        ("REN", "16", ["PO1"], "AN:LIGNEE:REN", None),
        ("EPR", "17", ["PO2"], "AN:LIGNEE:REN", ["AN:REN:16"]),
    ])
    return index, table


def _ecrire(tmp_path: Path, document: dict) -> Path:
    chemin = tmp_path / "groupes.json"
    chemin.write_text(json.dumps(document), encoding="utf-8")
    return chemin


def _etabli_par(chemin: Path) -> str:
    bloc, = groupes_config.succession_publiee("EPR", "17", chemin=chemin)
    return bloc["etabli_par"]


def test_le_vocabulaire_porte_les_deux_valeurs():
    """La valeur ancienne reste admise : une fiche non régénérée la porte encore."""
    assert set(ETABLISSEMENTS_SUCCESSION) == {
        ETABLI_PAR_RELECTURE_HUMAINE, ETABLI_PAR_COMPARAISON_DES_MEMBRES,
    }


def test_un_lien_mesure_au_dessus_du_seuil_se_publie_par_comparaison(tmp_path):
    # 15 communs, 20 réélus (15 + 5 partis ailleurs), 15 anciens : 2×15/35 = 86 %.
    index, table = _deux_legislatures(15, partis_ailleurs=5)
    composee, journal = groupes_amo30.mettre_a_jour_table(table, index, jour=JOUR)
    epr = composee["correspondance_sigles_an"]["groupes"][1]
    assert epr["succede_a_mesures"] == [
        {"groupe_id": "AN:REN:16", "communs": 15, "reelus": 20, "anciens": 15},
    ]
    assert journal["liens_non_soutenus"] == []
    assert _etabli_par(_ecrire(tmp_path, composee)) == ETABLI_PAR_COMPARAISON_DES_MEMBRES


def test_les_soixante_pour_cent_exacts_suffisent(tmp_path):
    """#1328 : 6 communs, 14 réélus, 6 anciens — 2×6/20 = 60 % tout juste."""
    index, table = _deux_legislatures(6, partis_ailleurs=8)
    composee, _ = groupes_amo30.mettre_a_jour_table(table, index, jour=JOUR)
    assert _etabli_par(_ecrire(tmp_path, composee)) == ETABLI_PAR_COMPARAISON_DES_MEMBRES


def test_un_lien_sous_le_seuil_reste_publie_mais_comme_relecture_humaine(tmp_path):
    """La règle ne retire pas un lien écrit à la main : elle refuse de dire qu'elle l'a établi.

    6 communs, 15 réélus, 6 anciens : 2×6/21 = 57 %.
    """
    index, table = _deux_legislatures(6, partis_ailleurs=9)
    composee, journal = groupes_amo30.mettre_a_jour_table(table, index, jour=JOUR)
    assert journal["liens_non_soutenus"] == [
        {"groupe_id": "AN:EPR:17", "predecesseur": "AN:REN:16", "communs": 6, "reelus": 15, "anciens": 6},
    ]
    assert _etabli_par(_ecrire(tmp_path, composee)) == ETABLI_PAR_RELECTURE_HUMAINE


def test_un_lien_sous_le_plancher_reste_relecture_humaine(tmp_path):
    """#1328 : 4 communs font 100 % des deux côtés, mais quatre personnes ne
    disent pas la suite d'un groupe."""
    index, table = _deux_legislatures(4)
    composee, journal = groupes_amo30.mettre_a_jour_table(table, index, jour=JOUR)
    assert journal["liens_non_soutenus"] == [
        {"groupe_id": "AN:EPR:17", "predecesseur": "AN:REN:16", "communs": 4, "reelus": 4, "anciens": 4},
    ]
    assert _etabli_par(_ecrire(tmp_path, composee)) == ETABLI_PAR_RELECTURE_HUMAINE


def test_la_table_ecrite_seule_publie_relecture_humaine(tmp_path):
    """Pas de mesure, donc rien qui permette de dire « par comparaison »."""
    _, table = _deux_legislatures(15)
    assert "succede_a_mesures" not in table["correspondance_sigles_an"]["groupes"][1]
    assert _etabli_par(_ecrire(tmp_path, table)) == ETABLI_PAR_RELECTURE_HUMAINE


def test_un_groupe_sans_membre_connu_n_est_pas_mesure():
    index, table = _deux_legislatures(15)
    index["mandats"]["PO1"] = []
    composee, journal = groupes_amo30.mettre_a_jour_table(table, index, jour=JOUR)
    assert "succede_a_mesures" not in composee["correspondance_sigles_an"]["groupes"][1]
    assert journal["liens_non_soutenus"] == []


@pytest.mark.parametrize("mesure", [
    {"groupe_id": "AN:AILLEURS:16", "communs": 15, "reelus": 20, "anciens": 15},  # un lien que l'entrée ne porte pas
    {"groupe_id": "AN:REN:16", "communs": 15.0, "reelus": 20, "anciens": 15},     # pas un entier
    {"groupe_id": "AN:REN:16", "communs": 16, "reelus": 20, "anciens": 15},       # plus de communs que d'anciens
    {"groupe_id": "AN:REN:16", "communs": 15, "reelus": 20},                      # la moitié d'une mesure
    {"groupe_id": "AN:REN:16", "communs": 21, "base": 20},                        # ancienne forme, impossible
])
def test_une_mesure_mal_formee_est_refusee(tmp_path, mesure):
    _, table = _deux_legislatures(15)
    table["correspondance_sigles_an"]["groupes"][1]["succede_a_mesures"] = [mesure]
    with pytest.raises(groupes_config.CorrespondanceSiglesInvalide, match="succede_a_mesures"):
        groupes_config.charger_correspondance_sigles(_ecrire(tmp_path, table))


def test_l_ancienne_forme_de_mesure_reste_lisible(tmp_path):
    """La table du run publiée avant #1328 porte `{communs, base}` jusqu'au run
    suivant : elle se charge, et se lit sous la règle qui l'a écrite."""
    _, table = _deux_legislatures(15)
    table["correspondance_sigles_an"]["groupes"][1]["succede_a_mesures"] = [
        {"groupe_id": "AN:REN:16", "communs": 15, "base": 20},
    ]
    assert _etabli_par(_ecrire(tmp_path, table)) == ETABLI_PAR_COMPARAISON_DES_MEMBRES


@pytest.mark.parametrize("mesure, attendu", [
    (None, False),
    ({"communs": 0, "base": 0}, False),
    ({"communs": 10, "base": 20}, True),          # ancienne forme : la moitié
    ({"communs": 9, "base": 19}, False),
    ({"communs": 56, "reelus": 65, "anciens": 56}, True),   # LES-REP-14 → LR-15, 93 %
    ({"communs": 26, "reelus": 55, "anciens": 36}, False),  # SER-14 → LAREM-15, 57 %
    ({"communs": 3, "reelus": 4, "anciens": 3}, False),     # EDS-15 → ECOLO-16 : sous le plancher
    ({"communs": 6, "reelus": 14, "anciens": 6}, True),     # 60 % exacts
    ({"communs": 5, "reelus": 0, "anciens": 5}, False),     # personne ne pouvait passer
])
def test_mesure_soutient_le_lien(mesure, attendu):
    assert groupes_config.mesure_soutient_le_lien(mesure) is attendu


# ---------------------------------------------------------------------------
# La table committée, sur l'archive réelle réduite
# ---------------------------------------------------------------------------

def test_sur_l_archive_reelle_chaque_lien_mesurable_passe_et_se_publie_par_comparaison(tmp_path):
    """XVIe → XVIIe mesurables, XVe → XVIe non (l'archive réduite n'a pas leurs mandats)."""
    index = an_roster.construire_index_gp(ARCHIVE)
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    composee, journal = groupes_amo30.mettre_a_jour_table(document, index, jour=JOUR)
    assert journal["liens_non_soutenus"] == []
    chemin = _ecrire(tmp_path, composee)
    vus = set()
    for entree in groupes_config.charger_correspondance_sigles(chemin):
        if not entree.get("succede_a"):
            continue
        for bloc in groupes_config.succession_publiee(entree["groupe_sigle"], entree["legislature"], chemin=chemin):
            attendu = (
                ETABLI_PAR_COMPARAISON_DES_MEMBRES if entree["legislature"] == "17"
                else ETABLI_PAR_RELECTURE_HUMAINE
            )
            assert bloc["etabli_par"] == attendu, (entree["groupe_id"], bloc["groupe_id"])
            vus.add(bloc["etabli_par"])
    assert vus == set(ETABLISSEMENTS_SUCCESSION)
