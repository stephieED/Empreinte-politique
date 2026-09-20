"""`couverture` fusionnée par liste métier (#602, lot 3 de #598).

Le critère de sortie de l'issue est explicite : « un test fusionne deux profils
portant chacun la couverture d'une liste différente et vérifie que **les deux**
survivent ». C'est
`test_les_couvertures_de_deux_listes_differentes_survivent_toutes_les_deux`.

Chaque test de comportement de ce fichier est écrit pour **échouer sur le code
d'avant**, où le bloc entier était pris au dernier écrivain qui en avait un
(`_prefer_non_empty(new, old)`), à une maille — le bloc — que #539 n'a jamais
publiée : son modèle est par liste métier.

Ce que ces tests NE remettent pas en cause : `couverture` reste **remplacée**,
jamais unie additivement (#539, décision 4). Le remplacement descend du bloc à
la liste, il ne devient pas une union — `test_une_liste_est_remplacee_et_jamais_unie`
le verrouille.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import (  # noqa: E402
    FAMILLES_WARNINGS,
    WARNING_PREFIX_COUVERTURE_DIVERGENTE,
    fusionner_couverture,
    merge_pivot_profile,
)
from schema_pivot import (  # noqa: E402
    CAUSE_DEFAUT_COLLECTE,
    CAUSE_PANNE,
    CAUSE_PAR_DECISION,
    ETAT_COUVERT,
    ETAT_HORS_COUVERTURE,
    ETAT_NON_COLLECTE,
    LISTES_COUVERTES,
    valider_couverture,
)

HIER = "2026-08-29"
AUJOURD_HUI = "2026-08-30"


def _couvert(constate_le: str = AUJOURD_HUI, debut: str = "2012-06-20") -> list[dict]:
    """La forme générale de #539 : deux entrées, la fenêtre couverte et l'avant."""
    return [
        {
            "etat": ETAT_COUVERT,
            "preuve": "AN open data, scrutins des législatures XIV-XVII.",
            "constate_le": constate_le,
            "portee": {"debut": debut, "fin": None},
        },
        {
            "etat": ETAT_HORS_COUVERTURE,
            "preuve": "AN open data, scrutins des législatures XIV-XVII.",
            "constate_le": constate_le,
            "portee": {"debut": None, "fin": "2012-06-19"},
        },
    ]


def _non_collecte(cause: str, constate_le: str = AUJOURD_HUI, preuve: str = "") -> list[dict]:
    return [
        {
            "etat": ETAT_NON_COLLECTE,
            "cause": cause,
            "preuve": preuve or f"cause déclarée : {cause}.",
            "constate_le": constate_le,
        }
    ]


def _bloc_complet(constate_le: str = AUJOURD_HUI, **surcharges) -> dict:
    """Les cinq listes de #539, la complétude étant obligatoire."""
    bloc = {liste: _couvert(constate_le) for liste in LISTES_COUVERTES}
    bloc.update(surcharges)
    return bloc


def _pivot(**extra) -> dict:
    base = {
        "schema_version": "1",
        "id": "jean-luc-melenchon",
        "nom": "Jean-Luc Mélenchon",
        "chambre": "AN",
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": [],
        "amendements": [],
        "tags_thematiques": [],
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-08-30T09:00:00+0000",
            "licence_donnees": "Licence Ouverte",
            "provenance": "candidat_declare",
            "warnings": [],
        },
    }
    base.update(extra)
    return base


# ---------------------------------------------------------------------------
# Le critère de sortie de #602
# ---------------------------------------------------------------------------

def test_les_couvertures_de_deux_listes_differentes_survivent_toutes_les_deux():
    """Le critère de sortie, littéralement.

    Un écrivain sait dire quelque chose de `votes`, l'autre d'`interventions`.
    Avant, le second remplaçait le premier : `votes` disparaissait du bloc
    publié. C'est le défaut de #484 sur le bloc qui existe pour ne pas publier
    un silence comme un fait.
    """
    ancien = {"votes": _couvert()}
    neuf = {"interventions": _non_collecte(CAUSE_PAR_DECISION)}

    fusionne, non_tranchees = fusionner_couverture(ancien, neuf)

    assert fusionne["votes"] == ancien["votes"]
    assert fusionne["interventions"] == neuf["interventions"]
    assert non_tranchees == []


def test_un_ecrivain_partiel_nefface_pas_les_quatre_autres_listes():
    """Le cas du corpus : un bloc complet face à un écrivain qui n'en décrit
    qu'une. Avant, quatre listes sur cinq étaient perdues d'un coup."""
    ancien = _bloc_complet(amendements=_non_collecte(CAUSE_PAR_DECISION))
    neuf = {"amendements": _non_collecte(CAUSE_DEFAUT_COLLECTE)}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert set(fusionne) == set(LISTES_COUVERTES)
    # `amendements` : l'écrivain qui a interrogé la source et a échoué (#562)
    # l'emporte sur celui qui n'a rien demandé.
    assert fusionne["amendements"] == neuf["amendements"]
    for liste in ("mandats", "votes", "textes_portes", "interventions"):
        assert fusionne[liste] == ancien[liste]
    # Et le bloc reste conforme au schéma de #539 : la complétude est le point.
    assert valider_couverture(fusionne) == []


# ---------------------------------------------------------------------------
# Les règles, dans leur ordre
# ---------------------------------------------------------------------------

def test_un_constat_dhier_ne_masque_pas_un_constat_daujourdhui():
    """La garde de #539 décision 4, dans le sens où l'ordre des jobs la violait.

    L'écrivain qui passe en dernier a recopié un profil committé hier, où la
    collecte avait réussi ; l'écrivain d'aujourd'hui déclare la panne. Avant,
    le `couvert` d'hier était publié et la panne du jour disparaissait.
    """
    ancien = {"votes": _non_collecte(CAUSE_PANNE, AUJOURD_HUI)}
    neuf = {"votes": _couvert(HIER)}

    fusionne, non_tranchees = fusionner_couverture(ancien, neuf)

    assert fusionne["votes"] == ancien["votes"]
    assert non_tranchees == []


def test_un_constat_daujourdhui_lemporte_sur_un_constat_dhier():
    """Le sens inverse, pour que la règle soit une règle et pas une préférence
    pour l'ancien : la panne d'hier ne survit pas à la collecte du jour."""
    ancien = {"votes": _non_collecte(CAUSE_PANNE, HIER)}
    neuf = {"votes": _couvert(AUJOURD_HUI)}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert fusionne["votes"] == neuf["votes"]


def test_celui_qui_na_rien_demande_a_la_source_necrase_pas_celui_qui_la_interrogee():
    """Le cas réel du même run : le job roster porte `--skip-interventions` en
    dur (#357) et publie `non_collecte`/`par_decision` ; le job AN a collecté.
    Les deux constatent le même jour. Avant, `--dirs an ue roster` décidait."""
    ancien = {"interventions": _couvert()}
    neuf = {"interventions": _non_collecte(CAUSE_PAR_DECISION)}

    fusionne, non_tranchees = fusionner_couverture(ancien, neuf)

    assert fusionne["interventions"] == ancien["interventions"]
    assert non_tranchees == []


def test_une_panne_declaree_lemporte_sur_une_decision_de_ne_rien_demander():
    """Deux `non_collecte` du même jour ne se valent pas : l'un a interrogé la
    source, l'autre non. Le rang d'interrogation, pas l'ordre des jobs."""
    ancien = {"amendements": _non_collecte(CAUSE_PANNE)}
    neuf = {"amendements": _non_collecte(CAUSE_PAR_DECISION)}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert fusionne["amendements"] == ancien["amendements"]


def test_un_cas_non_tranchable_se_declare_au_lieu_de_se_choisir():
    """Même jour, même rang, contenus différents : aucune règle ne départage.

    La couverture déjà publiée est conservée — ne rien changer est le seul
    geste qui ne prétende pas avoir tranché — et la liste est **nommée**.
    """
    ancien = {"votes": _non_collecte(CAUSE_PANNE, preuve="AMO30 n'a pas répondu.")}
    neuf = {"votes": _non_collecte(CAUSE_DEFAUT_COLLECTE, preuve="tri sur une date nulle.")}

    fusionne, non_tranchees = fusionner_couverture(ancien, neuf)

    assert fusionne["votes"] == ancien["votes"]
    assert non_tranchees == ["votes"]


def test_deux_couvertures_identiques_ne_sont_pas_une_divergence():
    ancien = _bloc_complet()
    neuf = _bloc_complet()

    fusionne, non_tranchees = fusionner_couverture(ancien, neuf)

    assert fusionne == ancien
    assert non_tranchees == []


# ---------------------------------------------------------------------------
# Ce que la fusion n'a pas le droit de faire
# ---------------------------------------------------------------------------

def test_la_cause_et_la_portee_ne_se_separent_jamais_de_leur_etat():
    """L'unité échangée est le jeu d'entrées entier d'une liste.

    Une entrée recomposée — l'état d'un écrivain, la portée de l'autre —
    publierait une frontière que personne n'a constatée. Chaque entrée publiée
    doit donc être, à l'identique, une entrée de l'un des deux écrivains.
    """
    ancien = {"votes": _couvert(AUJOURD_HUI, debut="2012-06-20")}
    neuf = {"votes": _couvert(AUJOURD_HUI, debut="2017-06-21")}

    fusionne, non_tranchees = fusionner_couverture(ancien, neuf)

    assert non_tranchees == ["votes"]
    for entree in fusionne["votes"]:
        assert entree in ancien["votes"] or entree in neuf["votes"]
    # Et le jeu retenu est celui d'UN seul écrivain, pas un panachage.
    assert fusionne["votes"] in (ancien["votes"], neuf["votes"])


def test_une_liste_est_remplacee_et_jamais_unie():
    """#539 décision 4 tient : la couverture décrit le run, elle ne s'accumule
    pas. Deux entrées d'hier plus une d'aujourd'hui feraient trois."""
    ancien = {"votes": _non_collecte(CAUSE_PANNE, HIER)}
    neuf = {"votes": _couvert(AUJOURD_HUI)}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert fusionne["votes"] == neuf["votes"]
    assert len(fusionne["votes"]) == 2


def test_une_liste_vide_ne_vaut_pas_un_constat():
    """`[]` est refusé par `schema_pivot` : le laisser gagner publierait une
    liste que le schéma rejette, et effacerait un état établi."""
    ancien = {"votes": _couvert()}
    neuf = {"votes": []}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert fusionne["votes"] == ancien["votes"]


def test_un_bloc_absent_ne_remplace_rien():
    """Un outil autonome qui ne dérive pas de couverture n'efface pas celle du
    corpus — la nuance de #539, conservée telle quelle."""
    ancien = _bloc_complet()

    assert fusionner_couverture(ancien, None) == (ancien, [])
    assert fusionner_couverture(ancien, {}) == (ancien, [])
    assert fusionner_couverture(None, None) == (None, [])


def test_une_liste_hors_nomenclature_nest_pas_effacee_par_la_fusion():
    """Faire disparaître une clé inconnue rendrait `valider_couverture` muet sur
    elle : le bloc passerait pour conforme parce que la fusion l'a nettoyé."""
    ancien = {"senat": _couvert()}
    neuf = {"votes": _couvert()}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert "senat" in fusionne
    assert valider_couverture(fusionne) != []


def test_lordre_des_listes_suit_la_nomenclature_de_539():
    """Un ordre stable d'un run à l'autre : sans lui, git voit une différence là
    où le contenu n'a pas bougé."""
    ancien = {liste: _couvert() for liste in reversed(LISTES_COUVERTES)}
    neuf = {"votes": _non_collecte(CAUSE_PAR_DECISION)}

    fusionne, _ = fusionner_couverture(ancien, neuf)

    assert list(fusionne) == list(LISTES_COUVERTES)


# ---------------------------------------------------------------------------
# Étage pivot : la déclaration du cas non tranchable
# ---------------------------------------------------------------------------

def test_le_pivot_declare_la_divergence_dans_meta_warnings():
    ancien = _pivot(couverture=_bloc_complet(
        votes=_non_collecte(CAUSE_PANNE, preuve="AMO30 n'a pas répondu.")))
    neuf = _pivot(couverture=_bloc_complet(
        votes=_non_collecte(CAUSE_DEFAUT_COLLECTE, preuve="tri sur une date nulle.")))

    fusionne = merge_pivot_profile(ancien, neuf)

    declarations = [
        w for w in fusionne["meta"]["warnings"]
        if w.startswith(WARNING_PREFIX_COUVERTURE_DIVERGENTE)
    ]
    assert len(declarations) == 1
    assert "votes" in declarations[0]
    assert fusionne["couverture"]["votes"] == ancien["couverture"]["votes"]


def test_la_declaration_seteint_quand_la_divergence_disparait():
    """Le warning décrit CETTE fusion. Ramené de l'ancien profil par l'union de
    #600, il décrirait un constat que la fusion courante ne retrouve pas."""
    perime = (
        f"{WARNING_PREFIX_COUVERTURE_DIVERGENTE} : deux écrivains constatent le "
        "même jour des couvertures différentes pour votes."
    )
    ancien = _pivot(couverture=_bloc_complet())
    ancien["meta"]["warnings"] = [perime]
    neuf = _pivot(couverture=_bloc_complet())

    fusionne = merge_pivot_profile(ancien, neuf)

    assert not any(
        w.startswith(WARNING_PREFIX_COUVERTURE_DIVERGENTE)
        for w in fusionne["meta"]["warnings"]
    )


def test_le_pivot_ne_perd_plus_les_listes_de_lecrivain_precedent():
    """Le même défaut, vu depuis `merge_pivot_profile` et pas depuis la fonction
    isolée : c'est le chemin que la CI emprunte."""
    ancien = _pivot(couverture=_bloc_complet())
    neuf = _pivot(couverture={"votes": _non_collecte(CAUSE_PAR_DECISION)})

    fusionne = merge_pivot_profile(ancien, neuf)

    assert set(fusionne["couverture"]) == set(LISTES_COUVERTES)
    assert valider_couverture(fusionne["couverture"]) == []


def test_la_declaration_a_sa_famille_davertissement():
    """Elle porte l'énumération des listes divergentes, donc un compteur : sans
    famille, deux fusions publieraient deux énumérations, dont une périmée."""
    assert WARNING_PREFIX_COUVERTURE_DIVERGENTE in FAMILLES_WARNINGS


# ---------------------------------------------------------------------------
# Cinquième règle : un sur-ensemble strict de sources l'emporte (#683)
# ---------------------------------------------------------------------------


def _entree_an(constate_le="2026-09-09"):
    return {
        "etat": "couvert",
        "portee": {"debut": "2012-06-20", "fin": None},
        "preuve": "l'Assemblée nationale publie ses scrutins depuis la XIVe législature.",
        "constate_le": constate_le,
    }


def _entree_pe(constate_le="2026-09-09"):
    return {
        "etat": "couvert",
        "source": "parlement_europeen",
        "portee": {"debut": "2019-07-18", "fin": "2026-03-11"},
        "preuve": "« votes » porte aussi du matériau du Parlement européen, collecté "
                  "via les dumps ParlTrack.",
        "constate_le": constate_le,
    }


def test_lecrivain_qui_couvre_une_source_de_plus_lemporte():
    """Le cas réel du run `34377413730`.

    `extract-ue-officiel` écrit une couverture sans volet européen,
    `merge-and-pivot` en écrit une avec. Même jour, même rang, contenus
    différents : la règle 4 gardait la couverture déjà publiée, et **3 profils
    sur 6** — Glucksmann, Philippot, Massard — publiaient leurs votes du
    Parlement européen sans la borne qui les date.

    Un sur-ensemble strict n'est pas une contradiction : il dit tout ce que
    l'autre dit, plus une source de plus.
    """
    ancien = {"votes": [_entree_an()]}
    neuf = {"votes": [_entree_an(), _entree_pe()]}
    bloc, non_tranchees = fusionner_couverture(ancien, neuf)
    assert non_tranchees == []
    assert any(e.get("source") == "parlement_europeen" for e in bloc["votes"])


def test_le_sur_ensemble_lemporte_aussi_quand_il_est_deja_publie():
    """Symétrique : un écrivain qui en dit moins n'efface pas celui qui en dit plus."""
    ancien = {"votes": [_entree_an(), _entree_pe()]}
    neuf = {"votes": [_entree_an()]}
    bloc, non_tranchees = fusionner_couverture(ancien, neuf)
    assert non_tranchees == []
    assert any(e.get("source") == "parlement_europeen" for e in bloc["votes"])


def test_deux_jeux_de_sources_simplement_differents_restent_non_tranchables():
    """La règle préfère le plus complet ; elle ne départage pas deux vérités.

    Sans cette borne, elle deviendrait un « le dernier qui parle a raison »
    déguisé — exactement ce que #602 a retiré.
    """
    ancien = {"votes": [_entree_an(), dict(_entree_pe(), source="senat")]}
    neuf = {"votes": [_entree_an(), _entree_pe()]}
    bloc, non_tranchees = fusionner_couverture(ancien, neuf)
    assert non_tranchees == ["votes"]
    assert bloc["votes"] == ancien["votes"], "la couverture déjà publiée est conservée"


def test_une_entree_sans_source_vaut_assemblee_nationale():
    """100 % des entrées écrites avant #683 n'ont pas la clé : l'absence le dit,
    et aucun backfill n'a été fait."""
    ancien = {"votes": [_entree_an()]}
    neuf = {"votes": [dict(_entree_an(), source="assemblee_nationale")]}
    bloc, non_tranchees = fusionner_couverture(ancien, neuf)
    assert non_tranchees == ["votes"], (
        "mêmes sources des deux côtés : le cas reste non tranchable, "
        "la clé explicite ne crée pas une source de plus"
    )
