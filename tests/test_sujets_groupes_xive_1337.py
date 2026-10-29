"""#1337 — un groupe de la XIVe n'a pas « aucun sujet » : sa parole n'est pas collectée.

Les 7 fiches de groupe XIVe publiaient `tags_thematiques_agreges: []`, sans
motif, et les 3 lignées faites des seuls groupes de la XIVe (`ECOLO-14`,
`R-UMP`, `RRDP`) aussi. Une liste vide se lit « aucun sujet de parole » ; or
l'Assemblée ne publie pas de comptes rendus de séance avant la XVe
(`couverture_profil.BORNES["interventions"]`). §2 règle 5.

`fixtures/sujets_groupes_xive_1337/fiches.json` : l'en-tête et les deux
premiers membres de quatre fiches réelles (`SRC-14`, `SOC-15`, `GDR-14`,
`GDR-15`), copiés de `pivot_data/groupes/` le 29/10/2026, avec le nombre de
sujets que chacune publiait ce jour-là (0, 1 936, 0, 1 816).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import group_profile as gp  # noqa: E402
from couverture_profil import BORNES, parole_hors_couverture  # noqa: E402
from lignee_profile import composer_lignee  # noqa: E402
from schema_groupe import (  # noqa: E402
    CLE_TAGS_NON_RESOLU,
    MOTIF_TAGS_HORS_COUVERTURE,
    valider_tags_non_resolu,
    validate_profil_groupe,
)
from schema_lignee import validate_profil_lignee  # noqa: E402

FICHES = json.loads((RACINE / "tests" / "fixtures" / "sujets_groupes_xive_1337" / "fiches.json")
                    .read_text(encoding="utf-8"))


def _fiche(nom: str) -> dict:
    """La fiche reconstruite par `build_groupe_profile`, sur les membres réels."""
    reel = FICHES[nom]
    profils = [{"id": m["membre_id"], "nom": m["nom"], "mandats": [], "votes": [],
                "amendements": [], "sources": [], "interventions": []} for m in reel["membres"]]
    return gp.build_groupe_profile(
        reel["groupe_id"], reel["groupe_sigle"], reel["groupe_nom"], reel["chambre"],
        str(reel["legislature"]), profils,
        appartenances={m["membre_id"]: {"debut": m["debut_dans_groupe"], "fin": m["fin_dans_groupe"],
                                        "periodes": m["periodes"]} for m in reel["membres"]})


def test_la_fixture_est_bien_le_constat():
    assert FICHES["groupe-AN-SRC-14.json"]["nb_tags_publies_le_29_10"] == 0
    assert FICHES["groupe-AN-SOC-15.json"]["nb_tags_publies_le_29_10"] > 0


def test_la_borne_est_celle_des_interventions():
    bloc = parole_hors_couverture("AN", "14")
    assert bloc == {"motif": MOTIF_TAGS_HORS_COUVERTURE,
                    "legislatures_couvertes": list(BORNES["interventions"].legislatures),
                    "preuve": BORNES["interventions"].limite_source}
    assert 14 not in bloc["legislatures_couvertes"]


@pytest.mark.parametrize("chambre, legislature", [("AN", "15"), ("AN", "17"), ("Senat", "14"), ("AN", None)])
def test_hors_de_ce_cas_rien_n_est_declare(chambre, legislature):
    assert parole_hors_couverture(chambre, legislature) is None


def test_un_groupe_de_la_xive_publie_null_et_son_motif():
    fiche = _fiche("groupe-AN-SRC-14.json")
    assert fiche["tags_thematiques_agreges"] is None
    assert fiche[CLE_TAGS_NON_RESOLU]["motif"] == MOTIF_TAGS_HORS_COUVERTURE
    assert validate_profil_groupe(fiche) == []


def test_contre_epreuve_un_groupe_de_la_xve_garde_sa_liste():
    """Sans parole chez ces deux membres, la liste est vide ET publiée : c'est
    un zéro mesuré, que la source couvre."""
    fiche = _fiche("groupe-AN-SOC-15.json")
    assert fiche["tags_thematiques_agreges"] == []
    assert CLE_TAGS_NON_RESOLU not in fiche
    assert validate_profil_groupe(fiche) == []


@pytest.mark.parametrize("tags, bloc, attendu", [
    (None, None, "sans 'tags_thematiques_non_resolu'"),
    ([], {"motif": "hors_couverture", "legislatures_couvertes": [15], "preuve": "x"}, "n'a pas de sens"),
    (None, {"motif": "inconnu", "legislatures_couvertes": [15], "preuve": "x"}, "non reconnu"),
    (None, {"motif": "hors_couverture", "legislatures_couvertes": [15], "preuve": ""}, "preuve"),
])
def test_le_validateur_refuse_un_couple_incoherent(tags, bloc, attendu):
    profil = {"tags_thematiques_agreges": tags}
    if bloc is not None:
        profil[CLE_TAGS_NON_RESOLU] = bloc
    erreurs = valider_tags_non_resolu(profil)
    assert erreurs and attendu in erreurs[0]


def test_une_lignee_de_la_seule_xive_publie_null():
    fiche = _fiche("groupe-AN-GDR-14.json")
    lignee = composer_lignee("AN:GDR-14", "Gauche démocrate et républicaine", "AN", [fiche],
                             agregats_recalcules={"tags_thematiques_agreges": []})
    assert lignee["tags_thematiques_agreges"] is None
    assert lignee[CLE_TAGS_NON_RESOLU] == fiche[CLE_TAGS_NON_RESOLU]
    assert not [e for e in validate_profil_lignee(lignee) if "tags" in e]


def test_contre_epreuve_une_lignee_avec_un_maillon_couvert_garde_sa_liste():
    fiches = [_fiche("groupe-AN-GDR-14.json"), _fiche("groupe-AN-GDR-15.json")]
    tags = [{"tag": "Projet de loi de finances pour 2018", "nb_membres_porteurs": 1, "poids_relatif": 0.5}]
    lignee = composer_lignee("AN:GDR", "Gauche démocrate et républicaine", "AN", fiches,
                             agregats_recalcules={"tags_thematiques_agreges": tags})
    assert lignee["tags_thematiques_agreges"] == tags
    assert CLE_TAGS_NON_RESOLU not in lignee
