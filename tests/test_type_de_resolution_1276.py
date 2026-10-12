#!/usr/bin/env python3
"""
test_type_de_resolution_1276.py — Une proposition de résolution dit ce qu'elle
demande (#1276).

`nature_texte` range sous `proposition_de_resolution` un vœu adressé au
Gouvernement, une résolution européenne, une modification du Règlement et une
demande de commission d'enquête. Le titre du dossier n'en dit rien : « Les
violences commises sur les mineurs dans les temps périscolaires et
extrascolaires » est une demande de commission d'enquête. L'Assemblée le dit sur
le document déposé, `classification.sousType`.

Le dossier et la classification ci-dessous sont copiés de l'archive des dossiers
de la XVIIe (`DLR5L17N53361`, `PNREANR5L17B2246`), lue le 12/10/2026 ; l'entrée
brute d'avant le lot est copiée de `raw_data/profiles/josephine-missoffe.json`
au 09/10/2026.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau.
"""

import copy
import json
import sys
import zipfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile  # noqa: E402
from gouvernement_textes import (  # noqa: E402
    TYPE_RESOLUTION_PAR_SOUS_TYPE,
    sous_types_des_resolutions,
    type_resolution_depose,
)
from merge_profile import merge_raw_profile  # noqa: E402
from normalize_profil import _normalize_texte_porte  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_MOTIFS_TYPE_RESOLUTION_NON_RESOLU,
    KNOWN_TYPES_RESOLUTION,
    validate_profil,
)

DOSSIER = {
    "@xsi:type": "DossierResolutionAN",
    "uid": "DLR5L17N53361",
    "legislature": "17",
    "titreDossier": {
        "titre": "Les violences commises sur les mineurs dans les temps "
                 "périscolaires et extrascolaires",
        "titreChemin": "violences_commises_sur_mineurs_periscolaires_extrascolaires",
        "senatChemin": None,
    },
    "procedureParlementaire": {"code": "8", "libelle": "Résolution"},
    "initiateur": {"acteurs": {"acteur": {"acteurRef": "PA795962",
                                         "mandatRef": "PM849121"}}},
    "actesLegislatifs": {"acteLegislatif": {
        "@xsi:type": "Etape_Type",
        "uid": "L17-ANLUNI-53361",
        "codeActe": "ANLUNI",
        "libelleActe": {"nomCanonique": "Lecture unique"},
        "organeRef": "PO838901",
        "dateActe": None,
        "actesLegislatifs": {"acteLegislatif": [
            {
                "@xsi:type": "DepotInitiative_Type",
                "uid": "L17-VD229395DI",
                "codeActe": "ANLUNI-DEPOT",
                "libelleActe": {"nomCanonique": "1er dépôt d'une initiative.",
                                "libelleCourt": "1er dépôt d'une initiative."},
                "organeRef": "PO838901",
                "dateActe": "2025-12-15T00:00:00.000+01:00",
                "actesLegislatifs": None,
                "texteAssocie": "PNREANR5L17B2246",
            },
            {
                "@xsi:type": "Etape_Type",
                "uid": "L17-ANLUNI-COM-53361",
                "codeActe": "ANLUNI-COM",
                "libelleActe": {"nomCanonique": "Travaux des commissions",
                                "libelleCourt": "Travaux des commissions"},
                "organeRef": "PO838901",
                "dateActe": None,
                "actesLegislatifs": {"acteLegislatif": {
                    "@xsi:type": "Etape_Type",
                    "uid": "L17-VD229396CF",
                    "codeActe": "ANLUNI-COM-FOND",
                    "libelleActe": {
                        "nomCanonique": "Travaux de la commission saisie au fond",
                        "libelleCourt": "Travaux de la commission saisie au fond"},
                    "organeRef": "PO419604",
                    "dateActe": None,
                    "actesLegislatifs": {"acteLegislatif": {
                        "@xsi:type": "SaisieComFond_Type",
                        "uid": "L17-VD229396CFS",
                        "codeActe": "ANLUNI-COM-FOND-SAISIE",
                        "libelleActe": {
                            "nomCanonique": "Renvoi en commission au fond",
                            "libelleCourt": "Renvoi en commission au fond"},
                        "organeRef": "PO419604",
                        "dateActe": "2025-12-15T00:00:00.000+01:00",
                        "actesLegislatifs": None,
                    }},
                }},
            },
        ]},
    }},
    "fusionDossier": None,
}

DOCUMENT = {
    "uid": "PNREANR5L17B2246",
    "legislature": "17",
    "denominationStructurelle": "Proposition de résolution",
    "titres": {
        "titrePrincipal": "proposition de résolution tendant à la création d'une "
                          "commission d'enquête relative aux violences commises "
                          "sur les mineurs dans les temps périscolaires et "
                          "extrascolaires",
        "titrePrincipalCourt": "Les violences commises sur les mineurs dans les "
                               "temps périscolaires et extrascolaires",
    },
    "classification": {
        "famille": {
            "depot": {"code": "INITDEP", "libelle": "Initiative en 1er Dépôt"},
            "classe": {"code": "PIONRES", "libelle": "Proposition de résolution"},
            "espece": {"code": "COMENQ",
                       "libelle": "tendant à la création d'une commission d'enquête"},
        },
        "type": {"code": "PNRE", "libelle": "Proposition de résolution"},
        "sousType": {"code": "COMENQ",
                     "libelle": "tendant à la création d'une commission d'enquête"},
        "statutAdoption": None,
    },
    "provenance": "Texte Déposé",
}

#: `raw_data/profiles/josephine-missoffe.json`, 09/10/2026 — avant le lot.
ENTREE_BRUTE_AVANT = {
    "id": "DLR5L17N53361",
    "titre": "Les violences commises sur les mineurs dans les temps "
             "périscolaires et extrascolaires",
    "role": "auteur",
    "nature_texte": "proposition_de_resolution",
    "type_rapport": None,
    "stade_procedural": "depose",
    "sort": "depose",
    "sort_non_resolu": None,
    "date_min": "2025-12-15",
    "date_max": "2025-12-15",
    "legislature": "17",
    "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/"
                  "violences_commises_sur_mineurs_periscolaires_extrascolaires",
}

SOUS_TYPES = {"PNREANR5L17B2246": "COMENQ"}


def _archive(tmp_path, dossiers, documents):
    chemin = tmp_path / "dossiers.zip"
    with zipfile.ZipFile(chemin, "w") as z:
        for d in dossiers:
            z.writestr(f"json/dossierParlementaire/{d['uid']}.json",
                       json.dumps({"dossierParlementaire": d}))
        for d in documents:
            z.writestr(f"json/document/{d['uid']}.json", json.dumps({"document": d}))
    return [(17, chemin)]


# --- La lecture à la source ------------------------------------------------

def test_le_titre_du_dossier_ne_dit_pas_ce_que_la_resolution_demande():
    assert "enquête" not in DOSSIER["titreDossier"]["titre"]
    assert DOSSIER["procedureParlementaire"] == {"code": "8", "libelle": "Résolution"}


def test_le_type_est_lu_dans_la_classification_du_document_depose(tmp_path):
    archives = _archive(tmp_path, [DOSSIER], [DOCUMENT])
    sous_types = sous_types_des_resolutions(archives)
    assert sous_types == SOUS_TYPES
    assert type_resolution_depose(DOSSIER, sous_types) == (
        "creation_commission_d_enquete", None)


def test_un_document_qui_n_est_pas_une_resolution_n_entre_pas_dans_la_table(tmp_path):
    loi = dict(DOCUMENT, uid="PIONANR5L17B0001")
    assert sous_types_des_resolutions(_archive(tmp_path, [], [loi])) == {}


def test_un_texte_qui_n_est_pas_une_resolution_n_a_ni_type_ni_motif():
    loi = copy.deepcopy(DOSSIER)
    depot = loi["actesLegislatifs"]["acteLegislatif"]["actesLegislatifs"]["acteLegislatif"][0]
    depot["texteAssocie"] = "PIONANR5L17B0001"
    assert type_resolution_depose(loi, SOUS_TYPES) == (None, None)


@pytest.mark.parametrize("sous_types, motif", [
    ({}, {"motif": "document_absent"}),
    ({"PNREANR5L17B2246": None}, {"motif": "sous_type_absent"}),
    ({"PNREANR5L17B2246": "NOUVEAU"}, {"motif": "sous_type_inconnu", "code": "NOUVEAU"}),
])
def test_chaque_absence_nomme_sa_cause(sous_types, motif):
    assert type_resolution_depose(DOSSIER, sous_types) == (None, motif)


def test_une_resolution_sans_document_de_depot_le_dit():
    sans_depot = dict(DOSSIER, actesLegislatifs=None)
    assert type_resolution_depose(sans_depot, SOUS_TYPES) == (
        None, {"motif": "sans_document"})


def test_un_document_sans_classification_est_dans_la_table_a_none(tmp_path):
    nu = {"uid": "PNREANR5L17B9999", "classification": None}
    assert sous_types_des_resolutions(_archive(tmp_path, [], [nu])) == {
        "PNREANR5L17B9999": None}


def test_la_table_et_le_vocabulaire_ferme_disent_la_meme_chose():
    assert set(TYPE_RESOLUTION_PAR_SOUS_TYPE.values()) == KNOWN_TYPES_RESOLUTION
    assert len(set(TYPE_RESOLUTION_PAR_SOUS_TYPE.values())) == len(
        TYPE_RESOLUTION_PAR_SOUS_TYPE)


# --- L'index, puis le pivot -------------------------------------------------

@pytest.fixture
def index(tmp_path, monkeypatch):
    archives = _archive(tmp_path, [DOSSIER], [DOCUMENT])
    monkeypatch.setattr(candidate_profile, "ensure_dossiers_zips_downloaded",
                        lambda *a, **k: archives)
    monkeypatch.setattr(candidate_profile, "DOSSIERS_CACHE_DIR", tmp_path / "cache")
    return candidate_profile._build_acteur_textes_portes_index()


def test_l_index_des_textes_portes_ecrit_le_type(index):
    (entree,) = index["PA795962"]
    assert entree["id"] == "DLR5L17N53361"
    assert entree["nature_texte"] == "proposition_de_resolution"
    assert entree["type_resolution"] == "creation_commission_d_enquete"
    assert entree["type_resolution_non_resolu"] is None


def test_l_index_change_de_nom_avec_son_contenu(index, tmp_path):
    """Un cache porte le code qui l'a écrit : `_v5` ne portait pas le type."""
    assert [p.name for p in (tmp_path / "cache").iterdir()] == [
        "index_acteur_textes_v6.json"]


def test_le_pivot_publie_le_type_a_cote_de_la_nature(index):
    texte = _normalize_texte_porte(index["PA795962"][0])
    assert texte["nature_texte"] == "proposition_de_resolution"
    assert texte["role"] == "auteur_proposition_de_resolution"
    assert texte["type_resolution"] == "creation_commission_d_enquete"
    assert texte["type_resolution_non_resolu"] is None


def test_une_entree_collectee_avant_le_lot_sort_non_relue():
    texte = _normalize_texte_porte(ENTREE_BRUTE_AVANT)
    assert texte["type_resolution"] is None
    assert texte["type_resolution_non_resolu"] == {"motif": "non_relu"}


def test_un_run_qui_relit_le_dossier_remplace_l_entree_non_relue(index):
    """`merge_dossier_records` fait gagner la neuve : aucun report à écrire."""
    avant = {"dossiers_legislatifs": [ENTREE_BRUTE_AVANT]}
    apres = {"dossiers_legislatifs": [index["PA795962"][0]]}
    (fusionnee,) = merge_raw_profile(avant, apres)["dossiers_legislatifs"]
    assert _normalize_texte_porte(fusionnee)["type_resolution"] == (
        "creation_commission_d_enquete")


def test_un_run_qui_ne_rend_pas_le_dossier_garde_l_entree_telle_quelle():
    avant = {"dossiers_legislatifs": [ENTREE_BRUTE_AVANT]}
    (gardee,) = merge_raw_profile(avant, {"dossiers_legislatifs": []})[
        "dossiers_legislatifs"]
    assert _normalize_texte_porte(gardee)["type_resolution_non_resolu"] == {
        "motif": "non_relu"}


def test_une_loi_ne_porte_ni_type_ni_motif():
    loi = dict(ENTREE_BRUTE_AVANT, nature_texte="proposition_de_loi",
               type_resolution="creation_commission_d_enquete")
    texte = _normalize_texte_porte(loi)
    assert (texte["type_resolution"], texte["type_resolution_non_resolu"]) == (None, None)


# --- La validation ----------------------------------------------------------

def _erreurs(texte):
    erreurs, _ = _valider({"textes_portes": [texte]})
    return [e for e in erreurs if "type_resolution" in e or "résolution sans" in e]


def _valider(profil):
    resultat = validate_profil(profil)
    if isinstance(resultat, tuple):
        return resultat[0], resultat[1:]
    return resultat, ()


def test_le_texte_normalise_passe_la_validation(index):
    assert _erreurs(_normalize_texte_porte(index["PA795962"][0])) == []
    assert _erreurs(_normalize_texte_porte(ENTREE_BRUTE_AVANT)) == []


def test_une_resolution_sans_type_ni_motif_est_refusee():
    texte = _normalize_texte_porte(ENTREE_BRUTE_AVANT)
    texte["type_resolution_non_resolu"] = None
    assert len(_erreurs(texte)) == 1


def test_un_type_et_son_motif_d_absence_ne_cohabitent_pas(index):
    texte = _normalize_texte_porte(index["PA795962"][0])
    texte["type_resolution_non_resolu"] = {"motif": "non_relu"}
    assert len(_erreurs(texte)) == 1


def test_un_type_hors_vocabulaire_est_refuse(index):
    texte = _normalize_texte_porte(index["PA795962"][0])
    texte["type_resolution"] = "commission_enquete"
    assert len(_erreurs(texte)) == 1


def test_un_type_sur_une_loi_est_refuse(index):
    texte = _normalize_texte_porte(index["PA795962"][0])
    texte.update(nature_texte="proposition_de_loi", role="auteur_proposition_de_loi")
    assert len(_erreurs(texte)) == 1


def test_un_motif_hors_vocabulaire_est_refuse():
    texte = _normalize_texte_porte(ENTREE_BRUTE_AVANT)
    texte["type_resolution_non_resolu"] = {"motif": "inconnu"}
    assert len(_erreurs(texte)) == 1
    assert "non_relu" in KNOWN_MOTIFS_TYPE_RESOLUTION_NON_RESOLU


def test_une_resolution_europeenne_n_est_pas_tenue_de_nommer_un_type():
    """Forme écrite par `normalize_parltrack_dumps` : pas de clé `type_resolution`."""
    europeenne = {
        "titre": "Résolution sur la situation au Venezuela",
        "institution": "parlement_europeen",
        "nature_texte": "proposition_de_resolution",
        "role": "auteur_proposition_de_resolution",
        "type_rapport": None,
        "stade_procedural": None,
        "sort": None,
        "sort_non_resolu": {"motif": "source_sans_sort"},
    }
    assert _erreurs(europeenne) == []
