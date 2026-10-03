#!/usr/bin/env python3
"""
Tests du lot #1168 (lot 2b) — `NG` et `SOC` de la XVe sont un seul groupe, et
une fiche de groupe se retire par son nom.

Trois choses, et pourquoi chacune :

- **la déclaration** (`fiches_retirees`) ne peut désigner qu'une fiche de groupe
  que la table ne régénère plus, et qu'un groupe déclaré remplace ;
- **la garde** refuse le retrait tant que la fiche remplaçante ne porte pas les
  organes ET tous les membres de la fiche retirée. Le contrôle de perte du run
  ne peut pas tenir ce rôle : la disparition du fichier est voulue, il la verra
  comme telle quel que soit le fichier retiré ;
- **la table committée** applique la règle à tout le monde : plus aucun
  renommage n'y est écrit comme une succession.

Les deux fiches du dernier bloc sont **réduites des fiches publiées** de
`NG-15` et `SOC-15` (organes et identifiants de membres réels, rien d'inventé).

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import generate_group_profiles as generation  # noqa: E402
from groupes_config import (  # noqa: E402
    FichesRetireesInvalides,
    charger_correspondance_sigles,
    charger_fiches_retirees,
)

pytestmark = pytest.mark.lit_reference_committee("config/groupes_reels.json")

CONFIG = RACINE / "config" / "groupes_reels.json"


def _config(tmp_path: Path, retraits, groupes=None) -> Path:
    document = {
        "groupes": groupes if groupes is not None else [
            {"groupe_id": "AN:SOC:15", "fichier": "groupe-AN-SOC-15.json"},
        ],
    }
    if retraits is not None:
        document["fiches_retirees"] = retraits
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps(document), encoding="utf-8")
    return chemin


def _retrait(**remplace) -> dict:
    return {
        "fichier": "groupe-AN-NG-15.json", "groupe_id": "AN:NG:15",
        "remplacee_par": "AN:SOC:15", "depuis": "2026-10-02", "motif": "renommage",
        **remplace,
    }


# ---------------------------------------------------------------------------
# La déclaration
# ---------------------------------------------------------------------------

def test_sans_la_cle_il_n_y_a_rien_a_retirer(tmp_path):
    assert charger_fiches_retirees(_config(tmp_path, None)) == []


def test_un_retrait_bien_forme_est_rendu_tel_quel(tmp_path):
    assert charger_fiches_retirees(_config(tmp_path, [_retrait()])) == [_retrait()]


@pytest.mark.parametrize("cle", ["fichier", "groupe_id", "remplacee_par", "depuis", "motif"])
def test_un_retrait_sans_l_une_de_ses_cles_est_refuse(tmp_path, cle):
    retrait = _retrait()
    del retrait[cle]
    with pytest.raises(FichesRetireesInvalides, match=cle):
        charger_fiches_retirees(_config(tmp_path, [retrait]))


@pytest.mark.parametrize("fichier", [
    "../profiles/jerome-guedj.pivot.json",   # remontée de répertoire
    "groupes/groupe-AN-NG-15.json",          # un chemin, pas un nom
    "lignee-AN-SOC.json",                    # une fiche de lignée
    "groupe-AN-NG-15.txt",
])
def test_un_retrait_ne_designe_qu_une_fiche_de_groupe(tmp_path, fichier):
    with pytest.raises(FichesRetireesInvalides, match="n'est pas un nom de fiche de groupe"):
        charger_fiches_retirees(_config(tmp_path, [_retrait(fichier=fichier)]))


def test_on_ne_retire_pas_une_fiche_que_le_meme_run_regenere(tmp_path):
    groupes = [
        {"groupe_id": "AN:SOC:15", "fichier": "groupe-AN-SOC-15.json"},
        {"groupe_id": "AN:NG:15", "fichier": "groupe-AN-NG-15.json"},
    ]
    with pytest.raises(FichesRetireesInvalides, match="à la fois"):
        charger_fiches_retirees(_config(tmp_path, [_retrait()], groupes))


def test_un_retrait_sans_remplacant_declare_est_refuse(tmp_path):
    with pytest.raises(FichesRetireesInvalides, match="AN:AILLEURS:15"):
        charger_fiches_retirees(_config(tmp_path, [_retrait(remplacee_par="AN:AILLEURS:15")]))


def test_le_meme_fichier_ne_se_retire_pas_deux_fois(tmp_path):
    with pytest.raises(FichesRetireesInvalides, match="deux fois"):
        charger_fiches_retirees(_config(tmp_path, [_retrait(), _retrait()]))


# ---------------------------------------------------------------------------
# La garde — sur des fiches réduites des fiches publiées
# ---------------------------------------------------------------------------

def _fiche(organes: list[tuple[str, str]], membres: list[str]) -> dict:
    return {
        "historique_noms": [{"sigle": sigle, "organe_an": ref} for sigle, ref in organes],
        "membres": [{"membre_id": membre} for membre in membres],
    }


NG = _fiche([("NG", "PO730946")], ["alain-david", "olivier-faure", "delphine-batho"])
SOC_SEUL = _fiche([("SOC", "PO758835")], ["alain-david", "olivier-faure", "boris-vallaud"])
SOC_REUNI = _fiche(
    [("NG", "PO730946"), ("SOC", "PO758835")],
    ["alain-david", "olivier-faure", "delphine-batho", "boris-vallaud"],
)


def test_la_fiche_reunie_autorise_le_retrait():
    assert generation.motif_de_refus_du_retrait(NG, SOC_REUNI) is None


def test_la_fiche_pas_encore_reunie_le_refuse():
    """L'état d'avant le run : `SOC-15` ne porte pas l'organe de `NG`."""
    refus = generation.motif_de_refus_du_retrait(NG, SOC_SEUL)
    assert refus and "PO730946" in refus


def test_un_membre_manquant_le_refuse_et_le_nomme():
    """Les organes y sont, pas tout le monde : c'est exactement ce qu'un compte ne voit pas."""
    amputee = _fiche(
        [("NG", "PO730946"), ("SOC", "PO758835")],
        ["alain-david", "olivier-faure", "boris-vallaud"],
    )
    refus = generation.motif_de_refus_du_retrait(NG, amputee)
    assert refus and "delphine-batho" in refus


def test_sans_remplacante_ou_sans_organe_rien_ne_part():
    assert generation.motif_de_refus_du_retrait(NG, None)
    assert generation.motif_de_refus_du_retrait(None, SOC_REUNI)
    assert generation.motif_de_refus_du_retrait(_fiche([], ["alain-david"]), SOC_REUNI)


# ---------------------------------------------------------------------------
# L'application
# ---------------------------------------------------------------------------

GROUPES = [{"groupe_id": "AN:SOC:15", "fichier": "groupe-AN-SOC-15.json"}]


def _ecrire(dossier: Path, nom: str, fiche: dict) -> Path:
    chemin = dossier / nom
    chemin.write_text(json.dumps(fiche), encoding="utf-8")
    return chemin


def test_le_retrait_supprime_la_fiche_nommee_et_elle_seule(tmp_path):
    ng = _ecrire(tmp_path, "groupe-AN-NG-15.json", NG)
    soc = _ecrire(tmp_path, "groupe-AN-SOC-15.json", SOC_REUNI)
    autre = _ecrire(tmp_path, "groupe-AN-EDS-15.json", _fiche([("EDS", "PO771789")], ["x"]))
    retires, refuses = generation.retirer_fiches([_retrait()], GROUPES, tmp_path)
    assert (retires, refuses) == (["groupe-AN-NG-15.json"], [])
    assert not ng.exists() and soc.exists() and autre.exists()


def test_un_retrait_refuse_laisse_la_fiche_et_dit_pourquoi(tmp_path):
    ng = _ecrire(tmp_path, "groupe-AN-NG-15.json", NG)
    _ecrire(tmp_path, "groupe-AN-SOC-15.json", SOC_SEUL)
    retires, refuses = generation.retirer_fiches([_retrait()], GROUPES, tmp_path)
    assert retires == [] and ng.exists()
    (fichier, motif), = refuses
    assert fichier == "groupe-AN-NG-15.json" and "PO730946" in motif


def test_une_fiche_deja_retiree_n_est_ni_retiree_ni_refusee(tmp_path):
    """Le run d'après : la déclaration reste dans la table, comme la trace du retrait."""
    _ecrire(tmp_path, "groupe-AN-SOC-15.json", SOC_REUNI)
    assert generation.retirer_fiches([_retrait()], GROUPES, tmp_path) == ([], [])


# ---------------------------------------------------------------------------
# La table committée
# ---------------------------------------------------------------------------

def test_les_retraits_de_la_table_committee_sont_valides():
    for retrait in charger_fiches_retirees(CONFIG):
        assert retrait["motif"] and retrait["depuis"]


def test_aucun_renommage_n_est_ecrit_comme_une_succession():
    """La même règle pour tout le monde : `succede_a` relie deux législatures, jamais une."""
    entrees = charger_correspondance_sigles(CONFIG)
    legislature_de = {e["groupe_id"]: e["legislature"] for e in entrees}
    dans_la_meme = [
        (cible, e["groupe_id"])
        for e in entrees for cible in e.get("succede_a") or []
        if legislature_de[cible] == e["legislature"]
    ]
    assert dans_la_meme == []


def test_un_organe_n_appartient_qu_a_un_groupe():
    vus: dict[str, str] = {}
    for entree in charger_correspondance_sigles(CONFIG):
        for organe in entree["organes_an"]:
            assert organe not in vus, f"{organe} : {vus[organe]} et {entree['groupe_id']}"
            vus[organe] = entree["groupe_id"]
