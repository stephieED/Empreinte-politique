#!/usr/bin/env python3
"""
Tests du lot #1011 — un scrutin européen que ParlTrack publie deux fois n'est
compté qu'une fois.

Sur certains jours, `ep_votes` publie chaque scrutin sous l'identifiant entier du
Parlement ET sous un identifiant composite (`"2018-12-12 00:00:00-1."`), l'heure
réelle recopiée au bout de l'intitulé. Mesuré le 07/10/2026 : 1 042 des 1 043
composites de ces jours ont un jumeau unique à la même seconde, et les fiches
de Maurel, Philippot et Glucksmann comptaient 269 votes deux fois.

Ce que ces tests verrouillent :

- **le jumeau se reconnaît à la source** : même jour, même seconde, mêmes totaux,
  un seul candidat — sinon le composite est gardé ;
- **l'index des votes n'écrit plus la copie**, et le retrait nommé la retire des
  fiches déjà publiées, en gardant le jumeau ;
- **l'ordre dans la séance est un entier publié**, pour que l'interface ne relise
  plus la chaîne.
"""

from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import parltrack_dumps  # noqa: E402
from normalize_parltrack_dumps import (  # noqa: E402
    porte_un_vote_europeen_composite,
    retirer_votes_publies_deux_fois,
)
from parltrack_dumps import doublons_de_seance, get_votes_doublons  # noqa: E402
from scrutins_europeens import ordre_dans_la_seance  # noqa: E402

# Une paire réelle, copiée du dump `ep_votes` en cache (12/09/2026), réduite aux
# clés que la règle lit : le même vote, sous ses deux identifiants.
TOTAUX = {"+": {"total": 612}, "-": {"total": 25}, "0": {"total": 27}}
ENTIER = {"voteid": 97747, "ts": "2018-12-12T12:51:11",
          "title": "A8-0399/2018 - Siegfried Mureşan - Vote unique", "votes": TOTAUX}
COMPOSITE = {"voteid": "2018-12-12 00:00:00-1.", "ts": "2018-12-12T00:00:00",
             "title": "A8-0399/2018 - Siegfried Mureşan - Vote unique 12/12/2018 12:51:11.000",
             "votes": TOTAUX}


def _vote(numero, position="pour", date="2018-12-12"):
    return {"scrutin_id": None, "position": position, "scrutin_non_resolu": {
        "institution": "parlement_europeen", "numero_scrutin": numero, "date": date}}


# ---------------------------------------------------------------------------
# La règle
# ---------------------------------------------------------------------------

def test_la_copie_composite_d_un_scrutin_publie_deux_fois_est_reconnue():
    assert doublons_de_seance([ENTIER, COMPOSITE]) == {"2018-12-12 00:00:00-1."}


def test_un_composite_sans_jumeau_est_le_seul_exemplaire_et_reste():
    """563 scrutins de l'index publié, sur 62 jours, n'existent qu'ainsi."""
    seul = dict(COMPOSITE, voteid="2017-06-01 00:00:00-1.", ts="2017-06-01T00:00:00",
                title="A8-0189/2017 - Tom Vandenkendelaere - Vote unique 01/06/2017 11:46:29.000")
    assert doublons_de_seance([ENTIER, seul]) == set()


def test_des_totaux_differents_ne_font_pas_un_jumeau():
    autre = dict(COMPOSITE, votes={"+": {"total": 611}, "-": {"total": 25}, "0": {"total": 27}})
    assert doublons_de_seance([ENTIER, autre]) == set()


def test_deux_candidats_a_la_meme_seconde_ne_font_pas_un_jumeau():
    second = dict(ENTIER, voteid=97748)
    assert doublons_de_seance([ENTIER, second, COMPOSITE]) == set()


def test_un_intitule_sans_heure_ne_permet_pas_d_apparier():
    sans_heure = dict(COMPOSITE, title="A8-0399/2018 - Siegfried Mureşan - Vote unique")
    assert doublons_de_seance([ENTIER, sans_heure]) == set()


def test_sans_dump_local_rien_n_est_ecarte(tmp_path, monkeypatch):
    monkeypatch.setattr(parltrack_dumps, "PARLTRACK_CACHE_DIR", tmp_path)
    assert get_votes_doublons(telecharger=False) == set()


# ---------------------------------------------------------------------------
# Sur la fiche
# ---------------------------------------------------------------------------

def test_le_retrait_garde_le_jumeau_et_ne_touche_que_la_copie():
    profil = {"votes": [_vote(97747), _vote("2018-12-12 00:00:00-1."),
                        _vote("2017-06-01 00:00:00-1.", date="2017-06-01")]}
    assert retirer_votes_publies_deux_fois(profil, {"2018-12-12 00:00:00-1."}) == 1
    assert [v["scrutin_non_resolu"]["numero_scrutin"] for v in profil["votes"]] == [
        97747, "2017-06-01 00:00:00-1."]


def test_un_vote_de_l_assemblee_n_est_jamais_touche():
    an = {"scrutin_id": "an:16:1", "position": "pour"}
    profil = {"votes": [an]}
    assert retirer_votes_publies_deux_fois(profil, {"2018-12-12 00:00:00-1."}) == 0
    assert profil["votes"] == [an]


def test_le_dump_n_est_lu_que_si_la_fiche_porte_un_composite():
    assert porte_un_vote_europeen_composite({"votes": [_vote("2018-12-12 00:00:00-1.")]})
    assert not porte_un_vote_europeen_composite({"votes": [_vote(97747), _vote("97747")]})
    assert not porte_un_vote_europeen_composite({"votes": [{"scrutin_id": "an:16:1"}]})


# ---------------------------------------------------------------------------
# L'ordre dans la séance
# ---------------------------------------------------------------------------

def test_l_ordre_dans_la_seance_est_un_entier_publie():
    assert ordre_dans_la_seance(97747) == 97747
    assert ordre_dans_la_seance("97747") == 97747
    assert ordre_dans_la_seance("2018-12-12 00:00:00-13.") == 13
    assert ordre_dans_la_seance("2018-12-12 00:00:00-13") == 13
    assert ordre_dans_la_seance(None) is None
