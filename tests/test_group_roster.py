"""Le roster d'un groupe, et le fait qu'il n'ait plus qu'une source (#529).

Jusqu'au lot 5, ce fichier testait DEUX choses : la lecture HTTP de NosDéputés
(`fetch_full_roster_nosdeputes`, ses domaines par législature, son
déballage de l'enveloppe `{"depute": {...}}`) et l'aiguillage de #527 qui
choisissait entre elle et AMO30. La première n'existe plus, et il n'y a donc
plus rien à aiguiller.

Ce qui reste à verrouiller est le **contrat** que la bascule avait pour but de
ne pas changer, et qui doit survivre au retrait de la seconde source :

- `fetch_full_roster` délègue à AMO30 et **n'émet aucune requête** propre ;
- `filter_roster_by_sigle` filtre sur le sigle et **rien d'autre** — aucun
  filtrage temporel résiduel (`_member_matches_legislature`, propre au Sénat,
  est parti avec #528) ;
- toute chambre hors `deputes` **refuse en nommant la décision**, et ce refus
  est un « roster indisponible » interceptable, pas une trace de pile ;
- `ERREURS_ROSTER` couvre ce qu'AMO30 peut lever.

Les tests qui figeaient la reprise réseau (`test_roster_reprise_reseau.py`) et
le plafond de lecture (`test_roster_timeout_lecture.py`) sont supprimés avec le
code qu'ils décrivaient : ils portaient sur un endpoint de 814 Ko généré à la
volée, et garder sous test un comportement qui n'existe plus, c'est garder sa
cause armée (même arbitrage que les deux fixtures inventées de #510).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import an_roster
import group_roster
from group_roster import (
    fetch_full_roster,
    fetch_group_roster,
    filter_roster_by_sigle,
)


def _membres_amo30():
    """Ce qu'`an_roster.fetch_full_roster_an` rend : le contrat de sortie.

    Les clés sont celles de `#526` — `acteur_ref` compris, que
    `filter_roster_by_sigle` fait traverser depuis #529 pour que la `source`
    d'une entrée de roster puisse pointer sur la fiche AN du membre.
    """
    return [
        {"acteur_ref": "PA1", "slug": "alice", "nom": "Alice", "groupe_sigle": "LR",
         "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA2", "slug": "bob", "nom": "Bob", "groupe_sigle": "SOC",
         "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA3", "slug": "carla", "nom": "Carla", "groupe_sigle": "LR",
         "mandat_debut": "2017-06-21", "mandat_fin": "2022-06-21"},
    ]


@pytest.fixture
def amo30(monkeypatch):
    """`an_roster` rend un roster connu, sans lire d'archive."""
    appels: list = []

    def faux_roster_an(legislature, **kwargs):
        appels.append(legislature)
        return _membres_amo30()

    monkeypatch.setattr(an_roster, "fetch_full_roster_an", faux_roster_an)
    return appels


# ---------------------------------------------------------------------------
# Une seule source, et aucun réseau propre
# ---------------------------------------------------------------------------

def test_l_assemblee_est_derivee_d_amo30(amo30):
    membres = fetch_full_roster("deputes", legislature="16")

    assert amo30 == ["16"]
    assert {m["slug"] for m in membres} == {"alice", "bob", "carla"}


def test_le_module_n_a_plus_aucune_lecture_nosdeputes():
    """Le verrou du lot 5. Ces cinq noms formaient la chaîne complète : le
    fetch, le choix de domaine, la politique de reprise et son plafond. Tant
    que l'un d'eux existe, une source retirée par décision peut être rebranchée
    sans que personne ne la décide."""
    for nom in (
        "fetch_full_roster_nosdeputes",
        "_base_url_for",
        "_BASE_URL_BY_LEGISLATURE_AN",
        "_erreur_retentable",
        "_ROSTER_MAX_ATTEMPTS",
        "_ROSTER_TIMEOUT",
        "_LIST_ENDPOINT",
    ):
        assert not hasattr(group_roster, nom), (
            f"`group_roster.{nom}` est de retour : c'est un morceau du chemin "
            "NosDéputés, retiré par #529. Voir "
            "docs/decisions/retrait-nosdeputes-529.md."
        )


def test_fetch_full_roster_n_emet_aucune_requete(amo30):
    """La `session` reste dans la signature — trois appelants en passent une —
    mais elle est ignorée. Un appelant qui croirait piloter le réseau par là se
    tromperait en silence : le test dit que non."""
    session = MagicMock()

    fetch_full_roster("deputes", legislature="16", session=session)

    session.get.assert_not_called()


def test_le_drapeau_baisse_coupe_au_lieu_de_basculer(monkeypatch):
    """`AN_ROSTER_ACTIF` n'est plus un aiguillage (#529) : il n'y a plus de
    seconde source. Baissé, il doit **lever** — jamais rendre une liste vide,
    qu'on ne distinguerait pas d'un groupe dissous une fois écrite sur disque
    (#511, #524)."""
    monkeypatch.setattr(an_roster, "AN_ROSTER_ACTIF", False)

    with pytest.raises(an_roster.RosterAnInactif):
        fetch_full_roster("deputes", legislature="16")


# ---------------------------------------------------------------------------
# Le refus des chambres hors périmètre (#528), remonté dans fetch_full_roster
# ---------------------------------------------------------------------------

def test_le_senat_refuse_en_nommant_la_decision():
    """Ce chemin n'est atteint que si quelqu'un lève la suspension des 2 entrées
    Sénat de `groupes_reels.json` — il doit alors échouer bruyamment, et dire
    POURQUOI. Un « chambre inconnue » générique laisserait croire à une faute
    de frappe."""
    with pytest.raises(ValueError) as echec:
        fetch_full_roster("senateurs")
    message = str(echec.value)
    assert "#528" in message, message
    assert "retrait-senat-528" in message, (
        "le refus doit renvoyer à la décision écrite, pas seulement la citer"
    )


def test_une_chambre_inconnue_refuse_aussi():
    with pytest.raises(ValueError) as echec:
        fetch_full_roster("maires")
    assert "maires" in str(echec.value)


def test_le_senat_ne_bascule_pas_sur_amo30_en_perdant_sa_source(monkeypatch):
    """AMO30 est un référentiel de l'Assemblée : le Sénat n'y est pas (#526 §10).
    Son retrait (#528) ne doit donc pas se traduire par un aiguillage silencieux
    vers AMO30 — qui rendrait un roster vide au lieu d'un refus."""
    def interdit(*_a, **_k):  # pragma: no cover - doit ne jamais être appelé
        raise AssertionError("Le Sénat ne se dérive pas d'AMO30.")

    monkeypatch.setattr(an_roster, "fetch_full_roster_an", interdit)

    with pytest.raises(ValueError):
        fetch_full_roster("senateurs")


def test_le_refus_du_senat_est_un_roster_indisponible_pas_un_crash():
    """`ValueError` appartient à `ERREURS_ROSTER` : les trois appelants le
    traitent en « roster indisponible » (exit 2, fiches publiées intactes)
    plutôt qu'en trace de pile qui coûte le commit du run (#518/#524)."""
    assert any(issubclass(ValueError, e) for e in group_roster.ERREURS_ROSTER)


def test_les_erreurs_de_la_source_sont_interceptables_ensemble():
    """`ERREURS_ROSTER` doit couvrir ce qu'AMO30 lève, sinon un job meurt en 1.

    `RosterAnIndisponible` hérite de `RuntimeError` : sans cette liste, une
    archive AMO30 absente traverserait le `except` des consommateurs et ferait
    sortir le run en 1 — c'est-à-dire annuler son commit — là où #518 a payé
    pour obtenir un 2 qui laisse les fiches publiées en place.

    `requests.Timeout` y reste après #529 : plus aucune requête ne part d'ici,
    mais `an_roster` fait télécharger l'archive AMO30 par `candidate_profile`,
    et ce téléchargement-là lève encore des exceptions `requests`.
    """
    for erreur in (
        an_roster.RosterAnIndisponible("archive absente"),
        an_roster.RosterAnInactif("drapeau baissé"),
        an_roster.CorrespondanceSiglesInvalide("sigle inconnu"),
        requests.Timeout("Read timed out"),
        ValueError("législature inconnue"),
    ):
        assert isinstance(erreur, group_roster.ERREURS_ROSTER), type(erreur).__name__


# ---------------------------------------------------------------------------
# filter_roster_by_sigle : le contrat que la bascule ne devait pas changer
# ---------------------------------------------------------------------------

def test_fetch_group_roster_filters_by_sigle(amo30):
    roster = fetch_group_roster("deputes", "LR", legislature="16")

    assert {m["slug"] for m in roster} == {"alice", "carla"}


def test_fetch_group_roster_marks_actif_from_mandat_fin(amo30):
    roster = fetch_group_roster("deputes", "LR", legislature="16")
    by_slug = {m["slug"]: m for m in roster}

    assert by_slug["alice"]["actif"] is True
    assert by_slug["carla"]["actif"] is False


def test_fetch_group_roster_empty_when_no_match(amo30):
    assert fetch_group_roster("deputes", "GDR", legislature="16") == []


def test_filter_roster_by_sigle_matches_fetch_group_roster(amo30):
    """`fetch_full_roster` + `filter_roster_by_sigle` doit produire exactement
    le même résultat qu'un `fetch_group_roster` direct — la garantie qui permet
    à `generate_group_profiles.py` de partager un seul roster entre plusieurs
    sigles."""
    direct = fetch_group_roster("deputes", "LR", legislature="16")

    raw_members = fetch_full_roster("deputes", legislature="16")
    via_filter = filter_roster_by_sigle(raw_members, "deputes", "LR")

    assert via_filter == direct


def test_un_seul_roster_partage_entre_plusieurs_sigles(amo30):
    raw_members = fetch_full_roster("deputes", legislature="16")
    lr = filter_roster_by_sigle(raw_members, "deputes", "LR")
    soc = filter_roster_by_sigle(raw_members, "deputes", "SOC")

    assert amo30 == ["16"], "le roster doit être dérivé une seule fois"
    assert {m["slug"] for m in lr} == {"alice", "carla"}
    assert {m["slug"] for m in soc} == {"bob"}


def test_filter_roster_by_sigle_empty_when_no_match():
    assert filter_roster_by_sigle(_membres_amo30(), "deputes", "GDR") == []


# ---------------------------------------------------------------------------
# `senat_periode_debut` / `_member_matches_legislature` (#191) : RETIRÉS (#528)
#
# Ce filtre côté client n'existait que pour `archive.nossenateurs.fr`, servi sur
# un domaine d'archive unique sans sous-domaine par période : il fallait donc
# trier les membres sur `mandat_fin`. L'Assemblée n'en a jamais eu besoin — sa
# législature était un sous-domaine du temps de NosDéputés, elle est une donnée
# du référentiel avec AMO30 (#526). Voir
# docs/decisions/retrait-senat-528.md.
# ---------------------------------------------------------------------------

def test_filter_roster_by_sigle_ne_filtre_que_sur_le_sigle():
    """Aucun filtrage temporel résiduel : un mandat clos reste dans le roster,
    et c'est `_member_eligibility_intervals` (group_profile) qui décide qui vote
    quand — jamais ce filtre-ci."""
    roster = filter_roster_by_sigle(_membres_amo30(), "deputes", "LR")

    # carla a un mandat terminé en 2022-06-21 : elle reste incluse.
    assert {m["slug"] for m in roster} == {"alice", "carla"}
    assert {m["actif"] for m in roster} == {True, False}


def test_l_acteur_ref_traverse_le_filtre():
    """C'est ce qui permet à `generate_roster_candidats` de donner à chaque
    entrée une `source` qui pointe vers la fiche AN du membre, là où elle
    pointait vers `www.nosdeputes.fr/<slug>` (#529). Absent de la source →
    `None`, jamais inventé (AGENTS.md §2 règle 5)."""
    roster = filter_roster_by_sigle(_membres_amo30(), "deputes", "LR")
    assert {m["acteur_ref"] for m in roster} == {"PA1", "PA3"}

    sans_ref = filter_roster_by_sigle(
        [{"slug": "zoe", "nom": "Zoé", "groupe_sigle": "LR"}], "deputes", "LR"
    )
    assert sans_ref[0]["acteur_ref"] is None
