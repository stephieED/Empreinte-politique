"""Tests du doublon d'appartenance européenne (#729) — collecte et retrait.

Le portail du Parlement européen publie **deux fois** la même appartenance :
`role: MEMBER_PARLIAMENT` sans classification, et `role: MEMBER` classée
`EU_INSTITUTION`. Mesuré le 12/09/2026 : **42 mandats sur 29 profils** publiés
en double, une fois en `autre`, une fois en `mandat_electif`.

Deux corrections, donc deux jeux de tests :

1. `normalize_europarl.dedupliquer_appartenances` — pour que la collecte cesse
   d'en produire ;
2. `purge_mandats_doublons_europarl.purge_profil` — pour retirer ce qui est déjà
   publié, la fusion étant additive.

Ce que les deux protègent avant tout : **deux fonctions distinctes sur le même
organe et la même période ne sont pas un doublon.** Membre et vice-président
d'une commission, c'est deux faits.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from normalize_europarl import dedupliquer_appartenances  # noqa: E402
from purge_mandats_doublons_europarl import purge_profil  # noqa: E402


def _appartenance(type_, role, nom="Mandat de député européen", debut="2014-07-01", fin="2017-06-18"):
    return {"type": type_, "role": role, "organisation_nom": nom, "debut": debut, "fin": fin}


def _mandat(categorie, fonction, source="europarl", label="Mandat de député européen",
            debut="2014-07-01", fin="2017-06-18"):
    return {"label": label, "categorie": categorie, "fonction": fonction,
            "categorie_source": source, "debut": debut, "fin": fin}


# ---------------------------------------------------------------------------
# La collecte : ne plus produire le doublon
# ---------------------------------------------------------------------------

def test_la_paire_publiee_par_la_source_est_reduite_a_l_entree_classee():
    conserves, ecartes = dedupliquer_appartenances([
        _appartenance("AUTRE", "MEMBER_PARLIAMENT"),
        _appartenance("EU_INSTITUTION", "MEMBER"),
    ])
    assert [m["type"] for m in conserves] == ["EU_INSTITUTION"]
    assert [m["role"] for m in ecartes] == ["MEMBER_PARLIAMENT"]


def test_le_libelle_de_role_explicite_survit_a_la_reduction():
    """La classification et le rôle explicite ne sont pas portés par la même
    entrée : `EU_INSTITUTION` dit le type sous un rôle générique, l'entrée non
    classée porte « Membre du Parlement européen ». Garder l'une sans l'autre
    appauvrirait la fiche."""
    conserves, _ = dedupliquer_appartenances([
        _appartenance("AUTRE", "MEMBER_PARLIAMENT") | {"role_label": "Membre du Parlement européen"},
        _appartenance("EU_INSTITUTION", "MEMBER") | {"role_label": "Membre"},
    ])
    assert conserves[0]["type"] == "EU_INSTITUTION"
    assert conserves[0]["role_label"] == "Membre du Parlement européen"


def test_deux_fonctions_classees_sur_le_meme_organe_ne_sont_pas_un_doublon():
    """Membre et vice-président d'une commission : deux faits, pas deux
    écritures du même."""
    entrees = [
        _appartenance("COMMITTEE_PARLIAMENTARY_STANDING", "MEMBER", nom="AFET"),
        _appartenance("COMMITTEE_PARLIAMENTARY_STANDING", "CHAIR_VICE", nom="AFET"),
    ]
    conserves, ecartes = dedupliquer_appartenances(entrees)
    assert len(conserves) == 2 and ecartes == []


def test_une_periode_differente_n_est_jamais_un_doublon():
    conserves, ecartes = dedupliquer_appartenances([
        _appartenance("AUTRE", "MEMBER_PARLIAMENT", debut="2009-07-14", fin="2014-06-30"),
        _appartenance("EU_INSTITUTION", "MEMBER"),
    ])
    assert len(conserves) == 2 and ecartes == []


def test_une_entree_non_classee_seule_est_conservee():
    """Sans contrepartie classée, la source n'a rien publié deux fois : écarter
    l'entrée perdrait le seul témoignage de l'appartenance."""
    conserves, ecartes = dedupliquer_appartenances([_appartenance("AUTRE", "MEMBER_PARLIAMENT")])
    assert len(conserves) == 1 and ecartes == []


def test_l_ordre_du_portail_est_preserve():
    """`_extract_groupe` lit la liste dans l'ordre du portail — du plus récent au
    plus ancien — pour choisir le groupe politique courant."""
    entrees = [
        _appartenance("EU_POLITICAL_GROUP", "MEMBER", nom="GUE/NGL", debut="2014-07-01"),
        _appartenance("AUTRE", "MEMBER_PARLIAMENT"),
        _appartenance("EU_INSTITUTION", "MEMBER"),
        _appartenance("COMMITTEE_PARLIAMENTARY_STANDING", "MEMBER", nom="AFET"),
    ]
    conserves, _ = dedupliquer_appartenances(entrees)
    assert [m.get("organisation_nom") for m in conserves] == [
        "GUE/NGL", "Mandat de député européen", "AFET"]


# ---------------------------------------------------------------------------
# Le retrait de ce qui est déjà publié
# ---------------------------------------------------------------------------

def test_le_doublon_publie_est_retire_et_le_mandat_reste():
    profil = {"mandats": [
        _mandat("autre", "Membre du Parlement européen"),
        _mandat("mandat_electif", "Membre"),
    ]}
    profil, retires = purge_profil(profil)
    assert [m["categorie"] for m in retires] == ["autre"]
    assert [m["categorie"] for m in profil["mandats"]] == ["mandat_electif"]


def test_le_retrait_ne_perd_pas_le_libelle_de_fonction():
    """Le libellé explicite est porté par l'entrée retirée, la classification
    par celle qui reste : le retrait doit garder les deux, comme la collecte."""
    profil = {"mandats": [
        _mandat("autre", "Membre du Parlement européen"),
        _mandat("mandat_electif", "Membre"),
    ]}
    profil, _ = purge_profil(profil)
    assert profil["mandats"][0]["fonction"] == "Membre du Parlement européen"


def test_sans_contrepartie_electif_rien_n_est_retire():
    profil = {"mandats": [_mandat("autre", "Membre du Parlement européen")]}
    profil, retires = purge_profil(profil)
    assert retires == [] and len(profil["mandats"]) == 1


def test_une_entree_sans_estampille_n_est_pas_touchee():
    """Le seul cas du corpus que le critère laisse : `yannick-vaugrenard`, dont
    les mandats européens n'ont pas d'estampille. Ils relèvent de #718, qui a
    tranché « marquer, jamais supprimer »."""
    profil = {"mandats": [
        _mandat("autre", "Membre du Parlement européen", source=None),
        _mandat("mandat_electif", "Membre", source=None),
    ]}
    profil, retires = purge_profil(profil)
    assert retires == [] and len(profil["mandats"]) == 2


def test_une_delegation_classee_autre_sans_contrepartie_survit():
    """`autre` couvre aussi les délégations : le critère exige la contrepartie
    `mandat_electif` au même libellé et à la même période."""
    profil = {"mandats": [
        _mandat("autre", "Membre", label="Délégation pour les relations avec l'Inde"),
        _mandat("mandat_electif", "Membre"),
    ]}
    profil, retires = purge_profil(profil)
    assert retires == [] and len(profil["mandats"]) == 2


def test_idempotent():
    profil = {"mandats": [
        _mandat("autre", "Membre du Parlement européen"),
        _mandat("mandat_electif", "Membre"),
    ]}
    profil, premiers = purge_profil(profil)
    profil, seconds = purge_profil(profil)
    assert len(premiers) == 1 and seconds == []
