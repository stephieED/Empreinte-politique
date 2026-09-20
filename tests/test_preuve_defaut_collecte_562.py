"""Une exception n'est pas une preuve (#562).

Mesuré sur les 481 profils publiés au 28/08/2026 (`f5e20b6`, run `33165786207`) :
**99** publiaient `amendements: []` avec, pour preuve de couverture, le texte
d'un `TypeError` du dépôt —

    amendements indisponibles : '<' not supported between instances of 'dict' and 'str'

— et une `cause: "panne"`, c'est-à-dire une accusation portée contre
l'Assemblée nationale pour un défaut qui était le nôtre. Aucun contrôle n'avait
bloqué : le message est une chaîne non vide, donc le champ était « rempli ».

Ce que ces tests tiennent, dans l'ordre d'importance :

  1. **une preuve qui porte un fragment d'exception de programmation est
     refusée** — c'est le garde-fou, et il vaut pour toute exception à venir,
     pas pour celle-ci ;
  2. il refuse **sans** rejeter une preuve de panne légitime, qui cite ce que
     la source a renvoyé, nom d'erreur réseau compris. Un garde-fou qui casse
     le chemin normal serait retiré au premier incident ;
  3. un défaut de collecte interne produit une cause **distincte** de `panne`,
     et sa preuve est **construite**, jamais recopiée du warning — c'est ce qui
     rend le point 1 inatteignable en régime normal ;
  4. il passe **avant** la panne quand les deux sont signalés : de ce que nous
     savons, le fait dont nous sommes sûrs est le nôtre.

Aucune lecture de `pivot_data/` ni de `raw_data/profiles/` (#473).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import couverture_profil as cv  # noqa: E402
from candidate_profile import WARNING_PREFIX_DEFAUT_COLLECTE  # noqa: E402
from schema_pivot import (  # noqa: E402
    CAUSE_DEFAUT_COLLECTE,
    CAUSE_PANNE,
    CAUSES_NON_COLLECTE,
    ETAT_NON_COLLECTE,
    LISTES_COUVERTES,
    make_empty_profil,
    marqueur_defaut_code,
    valider_couverture,
)

LE_JOUR = "2026-08-28"

#: La preuve telle qu'elle a été publiée sur les 99 profils.
PREUVE_PUBLIEE_SUR_99_PROFILS = (
    "amendements indisponibles : '<' not supported between instances of 'dict' and 'str'"
)


def _profil(warnings=()) -> dict:
    profil = make_empty_profil("marie-martin", "Marie Martin")
    profil["meta"]["warnings"] = list(warnings)
    return profil


def _entree(liste, couverture) -> dict:
    return couverture[liste][0]


def _couverture_valide(liste, entree) -> dict:
    """Un bloc complet dont seule `liste` porte l'entrée à éprouver."""
    bloc = {
        autre: [{"etat": "couvert", "preuve": "borne d'archive", "constate_le": LE_JOUR}]
        for autre in LISTES_COUVERTES
    }
    bloc[liste] = [entree]
    return bloc


# ---------------------------------------------------------------------------
# 1. Le garde-fou : une exception n'est pas une source
# ---------------------------------------------------------------------------

def test_la_preuve_publiee_sur_les_99_profils_est_desormais_refusee():
    """Le cas exact, tel qu'il est dans le corpus publié."""
    erreurs = valider_couverture(_couverture_valide("amendements", {
        "etat": ETAT_NON_COLLECTE,
        "cause": CAUSE_PANNE,
        "preuve": PREUVE_PUBLIEE_SUR_99_PROFILS,
        "constate_le": LE_JOUR,
    }))

    assert any("fragment d'exception" in e for e in erreurs), (
        "« chaîne non vide » est le seul contrôle qui existait, et c'est lui qui "
        "a laissé passer un TypeError comme preuve sur 99 profils sur 481"
    )


def test_le_garde_fou_couvre_la_classe_pas_le_seul_incident():
    """Le tri d'aujourd'hui corrigé, la prochaine exception passerait par le même
    chemin. Le garde-fou porte sur la FORME d'une exception de programmation."""
    for preuve in (
        "Traceback (most recent call last):",
        "amendements indisponibles : 'NoneType' object has no attribute 'get'",
        "votes introuvables : KeyError: 'dateScrutin'",
        "unsupported operand type(s) for +: 'int' and 'str'",
        'File "/app/src/candidate_profile.py", line 3820, in fetch_amendements_officiels',
    ):
        assert marqueur_defaut_code(preuve) is not None, preuve


def test_le_garde_fou_ne_refuse_pas_une_preuve_de_panne_legitime():
    """**Le contre-test, et il compte autant que le test.**

    Une preuve de `panne` cite ce que la source a renvoyé — y compris le nom
    d'une erreur réseau. C'est un fait SUR LA SOURCE, et il est publiable. Un
    garde-fou qui casserait le chemin normal des pannes serait désarmé au
    premier incident, et #562 se reproduirait sous une autre forme."""
    for preuve in (
        "amendements indisponibles (législature 17) : source indisponible "
        "(ConnectionError: HTTPSConnectionPool(host='data.assemblee-nationale.fr', port=443))",
        "amendements indisponibles : échec du téléchargement (IncompleteRead(12 bytes read))",
        "amendements indisponibles : archive invalide (File is not a zip file)",
        "index des scrutins indisponible : cache absent pour la législature 16",
        "AN_AMENDEMENTS_PATH = {'17', '16', '15', '14'} — bornes d'archives",
        "collecte écartée par décision de pipeline : --skip-interventions (#357)",
    ):
        assert marqueur_defaut_code(preuve) is None, preuve
        assert valider_couverture(_couverture_valide("votes", {
            "etat": ETAT_NON_COLLECTE, "cause": CAUSE_PANNE,
            "preuve": preuve, "constate_le": LE_JOUR,
        })) == [], preuve


# ---------------------------------------------------------------------------
# 2. La cause : « la source n'a pas répondu » ≠ « notre code a échoué »
# ---------------------------------------------------------------------------

def test_defaut_collecte_est_une_cause_a_part_entiere():
    """Trois causes, pas deux : ranger un défaut du dépôt sous `panne` impute à
    l'Assemblée nationale une faute qui n'est pas la sienne."""
    assert CAUSE_DEFAUT_COLLECTE in CAUSES_NON_COLLECTE
    assert CAUSE_DEFAUT_COLLECTE != CAUSE_PANNE


def test_un_defaut_interne_ne_produit_jamais_une_panne():
    warning = (
        f"{WARNING_PREFIX_DEFAUT_COLLECTE} (amendements) : fetch_amendements_officiels "
        "a échoué sur une anomalie de ce dépôt (TypeError) — aucune source de "
        "l'Assemblée nationale n'est en cause. Trace complète au journal de run."
    )
    couverture = cv.deriver(_profil(warnings=[warning]), constate_le=LE_JOUR)

    entree = _entree("amendements", couverture)
    assert entree["etat"] == ETAT_NON_COLLECTE
    assert entree["cause"] == CAUSE_DEFAUT_COLLECTE
    assert len(couverture["amendements"]) == 1


def test_la_preuve_dun_defaut_interne_est_construite_pas_recopiee():
    """La règle qui répare #562 à la racine : le texte de l'exception reste dans
    `meta.warnings`, et n'atteint jamais le champ publié."""
    warning = (
        f"{WARNING_PREFIX_DEFAUT_COLLECTE} (amendements) : fetch_amendements_officiels "
        "a échoué sur une anomalie de ce dépôt (TypeError) — voir le journal."
    )
    couverture = cv.deriver(_profil(warnings=[warning]), constate_le=LE_JOUR)
    preuve = _entree("amendements", couverture)["preuve"]

    assert "TypeError" not in preuve
    assert marqueur_defaut_code(preuve) is None
    assert "amendements" in preuve
    assert valider_couverture(couverture) == []


def test_un_defaut_interne_passe_avant_une_panne_sur_la_meme_liste():
    """Quand les deux sont signalés, celui dont nous sommes sûrs est le nôtre."""
    couverture = cv.deriver(_profil(warnings=[
        "amendements indisponibles (législature 17) : index en cache absent",
        f"{WARNING_PREFIX_DEFAUT_COLLECTE} (amendements) : fetch_amendements_officiels "
        "a échoué sur une anomalie de ce dépôt (TypeError).",
    ]), constate_le=LE_JOUR)

    assert _entree("amendements", couverture)["cause"] == CAUSE_DEFAUT_COLLECTE


def test_un_defaut_interne_ne_condamne_que_sa_liste():
    """Le warning nomme la liste ; rien d'autre ne bascule."""
    couverture = cv.deriver(_profil(warnings=[
        f"{WARNING_PREFIX_DEFAUT_COLLECTE} (amendements) : fetch_amendements_officiels "
        "a échoué sur une anomalie de ce dépôt (TypeError).",
    ]), constate_le=LE_JOUR)

    assert _entree("amendements", couverture)["cause"] == CAUSE_DEFAUT_COLLECTE
    for liste in LISTES_COUVERTES:
        if liste == "amendements":
            continue
        assert all(e.get("cause") != CAUSE_DEFAUT_COLLECTE for e in couverture[liste]), liste


def test_les_motifs_de_defaut_suivent_les_listes_couvertes():
    """Dérivés, pas recopiés : deux expressions du même invariant divergent en
    silence — c'est l'argument qui vaut déjà pour le calendrier des
    législatures."""
    listes_couvertes_par_les_motifs = {
        liste for _, listes in cv.MOTIFS_DEFAUT_COLLECTE for liste in listes
    }
    assert listes_couvertes_par_les_motifs == set(LISTES_COUVERTES)


def test_un_defaut_de_collecte_dementi_par_la_fusion_ne_survit_pas():
    """La fusion additive peut restaurer la liste depuis le fichier déjà publié.
    Continuer à la déclarer non collectée publierait un `non_collecte` sur une
    liste pleine — même règle que pour le préfixe de panne."""
    from merge_profile import merge_pivot_profile

    warning = (
        f"{WARNING_PREFIX_DEFAUT_COLLECTE} (amendements) : fetch_amendements_officiels "
        "a échoué sur une anomalie de ce dépôt (TypeError)."
    )
    ancien = make_empty_profil("marie-martin", "Marie Martin")
    ancien["amendements"] = [{"uid": "U1", "numero": "1", "date": "2024-01-01"}]
    neuf = _profil(warnings=[warning])

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["amendements"], "la fusion additive restaure la liste"
    assert warning not in fusionne["meta"]["warnings"]
    couverture = cv.deriver(fusionne, constate_le=LE_JOUR)
    assert all(
        e.get("cause") != CAUSE_DEFAUT_COLLECTE for e in couverture["amendements"]
    )


def test_aucun_motif_de_defaut_nest_aussi_un_motif_de_panne():
    """Les deux tables se lisent l'une contre l'autre : un même warning ne peut
    pas être à la fois « la source n'a pas répondu » et « notre code a échoué »."""
    for motif_defaut, _ in cv.MOTIFS_DEFAUT_COLLECTE:
        for motif_panne, _ in cv.MOTIFS_PANNE:
            assert motif_panne.lower() not in motif_defaut.lower(), (
                f"{motif_defaut!r} serait aussi lu comme la panne {motif_panne!r}"
            )
