"""Tests du sigle et du type d'organe européens (#863).

Besoin remonté par la session interface : la frise du parcours ne garde, sur
chaque segment parlementaire, que **le sigle du groupe** et la place dans
l'hémicycle. À l'Assemblée les deux sont publiés ; au Parlement européen, aucun
des deux ne l'était — le groupe vivait sous `categorie: "autre"`, au milieu des
délégations, reconnaissable seulement à la lecture de son intitulé.

Ce que ces tests protègent :

1. **La source classe, nous ne devinons pas.** `type_organe_source` traduit la
   classification publiée par le portail ; quand le portail ne classe pas
   (`AUTRE`), la clé est **absente** — et son absence dit cela, pas « autre ».
2. **Un identifiant n'est pas un sigle.** `stephane-le-foll` porte
   `organisation_sigle: "2953"` avec `organisation_nom: null` : le publier comme
   sigle inventerait une donnée (§2 règle 5). Il devient `null` + un motif.
3. **Un champ neuf n'atteint pas une entrée déjà publiée tout seul** : le report
   nommé est la septième occurrence de la famille #492/#639/#641/#696/#710/#718.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import backfill_mandat_organe_source  # noqa: E402
from normalize_europarl import normalize_europarl  # noqa: E402
from schema_pivot import KNOWN_TYPES_ORGANE_SOURCE  # noqa: E402


def _profil_ue(mandats):
    return {
        "identifiant_pe": "96742",
        "nom_complet": "Jean-Luc MÉLENCHON",
        "url_source": "https://www.europarl.europa.eu/meps/fr/96742",
        "mandats_europeens": mandats,
    }


def _appartenance(type_, nom, sigle, role="MEMBER", debut="2014-07-01", fin="2017-06-18"):
    return {"type": type_, "type_label": type_, "role": role, "role_label": "Membre",
            "organisation_nom": nom, "organisation_sigle": sigle, "debut": debut, "fin": fin}


def _mandats(profil, label):
    return [m for m in profil["mandats"] if m.get("label") == label]


def _cle(m):
    return (m.get("categorie"), m.get("type"), m.get("label"), m.get("debut"))


# ---------------------------------------------------------------------------
# Ce que la normalisation publie
# ---------------------------------------------------------------------------

def test_le_groupe_politique_europeen_porte_son_sigle_et_son_type():
    profil = normalize_europarl(_profil_ue([
        _appartenance("EU_POLITICAL_GROUP",
                      "Groupe confédéral de la Gauche unitaire européenne/Gauche verte nordique",
                      "GUE/NGL"),
    ]))
    (mandat,) = _mandats(profil, "Groupe confédéral de la Gauche unitaire européenne/Gauche verte nordique")
    assert mandat["sigle_organe"] == "GUE/NGL"
    assert mandat["type_organe_source"] == "groupe_politique_europeen"
    assert mandat["type_organe_source"] in KNOWN_TYPES_ORGANE_SOURCE


def test_une_commission_et_un_parti_national_ne_sont_pas_un_groupe_politique():
    """L'interface doit pouvoir distinguer le groupe du reste sans lire
    l'intitulé : c'est tout l'objet du champ."""
    profil = normalize_europarl(_profil_ue([
        _appartenance("COMMITTEE_PARLIAMENTARY_STANDING", "Commission des budgets", "BUDG"),
        _appartenance("NATIONAL_POLITICAL_GROUP", "Parti de Gauche", "PG"),
    ]))
    types = {m["label"]: m.get("type_organe_source") for m in profil["mandats"]}
    assert types["Commission des budgets"] == "commission_parlementaire_europeenne"
    assert types["Parti de Gauche"] == "parti_national_au_parlement_europeen"


def test_une_appartenance_que_la_source_ne_classe_pas_reste_sans_type():
    """`AUTRE` n'est pas une classification : la clé est absente, et son absence
    dit que la source ne s'est pas prononcée."""
    profil = normalize_europarl(_profil_ue([
        _appartenance("AUTRE", "Mandat de député européen", "8e législature", role="MEMBER_PARLIAMENT"),
    ]))
    (mandat,) = _mandats(profil, "Mandat de député européen")
    assert "type_organe_source" not in mandat


def test_un_identifiant_non_resolu_n_est_jamais_publie_comme_sigle():
    """Mesuré sur `stephane-le-foll` : `organisation_sigle: "2953"` avec
    `organisation_nom: null`. Le sigle est `null`, et le motif l'accompagne."""
    profil = normalize_europarl(_profil_ue([
        {"type": "EU_POLITICAL_GROUP", "role": "MEMBER", "role_label": "Membre",
         "organisation_nom": None, "organisation_sigle": "2953",
         "debut": "2009-07-14", "fin": "2012-01-18"},
    ]))
    (mandat,) = [m for m in profil["mandats"] if m.get("type_organe_source") == "groupe_politique_europeen"]
    assert mandat["sigle_organe"] is None
    assert mandat["sigle_organe_non_resolu"]["valeur_source"] == "2953"
    assert "identifiant" in mandat["sigle_organe_non_resolu"]["raison"]


# ---------------------------------------------------------------------------
# Le report sur les entrées déjà publiées
# ---------------------------------------------------------------------------

def test_le_report_pose_les_deux_champs_sur_une_entree_ancienne():
    ancien = [{"label": "Groupe Europe des Nations et des Libertés", "categorie": "autre",
               "debut": "2015-06-15", "fin": "2017-06-18", "categorie_source": "europarl"}]
    neuf = [{**ancien[0], "sigle_organe": "ENF", "type_organe_source": "groupe_politique_europeen"}]
    (resultat,) = backfill_mandat_organe_source(ancien, neuf, _cle)
    assert resultat["sigle_organe"] == "ENF"
    assert resultat["type_organe_source"] == "groupe_politique_europeen"


def test_le_report_n_ecrase_jamais_une_valeur_deja_posee():
    ancien = [{"label": "G", "categorie": "autre", "debut": "2015-06-15", "sigle_organe": "ENF"}]
    neuf = [{"label": "G", "categorie": "autre", "debut": "2015-06-15", "sigle_organe": "ID"}]
    (resultat,) = backfill_mandat_organe_source(ancien, neuf, _cle)
    assert resultat["sigle_organe"] == "ENF"


def test_une_entree_que_la_collecte_neuve_ne_couvre_pas_reste_muette():
    """Elle reste sans sigle et sans type : « la source ne l'a pas classée »,
    jamais « elle n'a pas de sigle »."""
    ancien = [{"label": "Organe disparu", "categorie": "autre", "debut": "2004-07-20"}]
    neuf = [{"label": "Autre organe", "categorie": "autre", "debut": "2014-07-01",
             "sigle_organe": "S&D", "type_organe_source": "groupe_politique_europeen"}]
    (resultat,) = backfill_mandat_organe_source(ancien, neuf, _cle)
    assert "sigle_organe" not in resultat and "type_organe_source" not in resultat


def test_le_motif_de_non_resolution_est_reporte_lui_aussi():
    ancien = [{"label": "G", "categorie": "autre", "debut": "2009-07-14"}]
    neuf = [{"label": "G", "categorie": "autre", "debut": "2009-07-14", "sigle_organe": None,
             "sigle_organe_non_resolu": {"raison": "organisation non résolue", "valeur_source": "2953"}}]
    (resultat,) = backfill_mandat_organe_source(ancien, neuf, _cle)
    assert resultat["sigle_organe_non_resolu"]["valeur_source"] == "2953"


def test_sans_collecte_neuve_le_report_ne_fait_rien():
    ancien = [{"label": "G", "categorie": "autre", "debut": "2015-06-15"}]
    assert backfill_mandat_organe_source(ancien, None, _cle) == ancien
    assert backfill_mandat_organe_source(ancien, [], _cle) == ancien
