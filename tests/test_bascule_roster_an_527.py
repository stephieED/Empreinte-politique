"""Ce que la bascule du roster AN sur AMO30 change en aval (#527, lot 1b).

L'aiguillage lui-même est figé par `tests/test_group_roster.py` et le drapeau
par `tests/test_an_roster.py`. Ce fichier couvre les **conséquences** de la
bascule, celles qui ne se voient pas dans la ligne qu'on retourne :

1. une panne de la nouvelle source reste un « roster indisponible » nommé —
   donc un run qui ne publie pas de composition non mesurée (#511), et non une
   trace de pile qui coûte le commit (#518) ;
2. un membre **sans slug** — impossible avec NosDéputés, normal avec AMO30 —
   est compté et nommé au lieu d'être laissé tomber en silence (#510, #501) ;
3. le `meta.warnings` de fraîcheur **publié** nomme la source dont la
   composition vient réellement (AGENTS §2 règle 2).

Aucun réseau, aucune lecture de `pivot_data/` ni de `raw_data/profiles/`.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import generate_roster_candidats  # noqa: E402
import group_profile  # noqa: E402
from generate_roster_candidats import (  # noqa: E402
    anomalies_roster,
    build_roster_candidats_detaille,
    fetch_rosters_bruts,
    membres_sans_slug,
    resume_membres_sans_slug,
)

_GROUPE_AN = {
    "roster_chambre": "deputes",
    "groupe_id": "AN:LR",
    "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains",
    "chambre": "AN",
    "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}


def _membre(slug, nom, groupe_sigle="LR", debut="2022-06-29", fin=None):
    """Un membre brut au contrat commun aux deux sources (#526 §5)."""
    return {
        "slug": slug,
        "nom": nom,
        "groupe_sigle": groupe_sigle,
        "mandat_debut": debut,
        "mandat_fin": fin,
    }


# ---------------------------------------------------------------------------
# 1. Une panne d'AMO30 se comporte comme une panne de NosDéputés
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "exc, extrait",
    [
        (
            an_roster.RosterAnIndisponible(
                "Archive AMO30 indisponible : https://data.assemblee-nationale.fr/…"
            ),
            "RosterAnIndisponible",
        ),
        (
            an_roster.CorrespondanceSiglesInvalide(
                "Aucune correspondance de sigle AN pour ('LR', législature '16')"
            ),
            "CorrespondanceSiglesInvalide",
        ),
    ],
)
def test_une_panne_amo30_est_un_roster_indisponible_nomme(monkeypatch, exc, extrait):
    """Sans `ERREURS_ROSTER`, ces deux-là traverseraient le `except`.

    `RosterAnIndisponible` hérite de `RuntimeError`, que les consommateurs
    n'interceptaient pas : la bascule aurait transformé « source AN en panne »
    — un `exit 1` propre qui n'écrit rien — en trace de pile. Le résultat
    observable serait le même code de sortie, mais sans l'annotation qui nomme
    la clé, c'est-à-dire le défaut que #518 puis #524 ont corrigé.
    """
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda chambre, legislature=None, session=None: (_ for _ in ()).throw(exc),
    )

    rosters_bruts, echecs = fetch_rosters_bruts([_GROUPE_AN])

    assert rosters_bruts == {("deputes", "16"): None}
    assert echecs[("deputes", "16")] is exc

    candidats, par_groupe = build_roster_candidats_detaille([_GROUPE_AN], rosters_bruts)
    anomalies = anomalies_roster([_GROUPE_AN], rosters_bruts, par_groupe, candidats, echecs)

    assert any(extrait in a for a in anomalies), anomalies
    assert any("INCONNUE, pas vide" in a for a in anomalies), anomalies


def test_une_panne_amo30_n_ecrit_aucun_roster(tmp_path, monkeypatch):
    """Le garde-fou de #511 doit survivre au changement de source."""
    config = tmp_path / "groupes_reels.json"
    config.write_text(json.dumps({"groupes": [_GROUPE_AN]}), encoding="utf-8")
    sortie = tmp_path / "roster_candidats.json"

    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda chambre, legislature=None, session=None: (_ for _ in ()).throw(
            an_roster.RosterAnIndisponible("Archive AMO30 indisponible")
        ),
    )

    code = generate_roster_candidats.main(
        ["--config", str(config), "--out", str(sortie)]
    )

    assert code == 1
    assert not sortie.exists()


# ---------------------------------------------------------------------------
# 2. Un membre sans slug est compté et nommé
# ---------------------------------------------------------------------------

def test_un_membre_sans_slug_est_nomme_et_non_avale():
    """AMO30 publie un `PA######`, pas un slug : les sans-slug existent.

    `build_roster_candidats_detaille` les ignore — il n'a pas le choix, le slug
    **est** le nom du fichier de profil (#487). Ce qui n'allait pas, c'est
    qu'il les ignorait sans un mot : quatre députés de la 16e disparaissaient
    du corpus sans qu'une ligne le dise, la forme exacte du trou de #510.
    """
    rosters_bruts = {
        ("deputes", "16"): [
            _membre("alice", "Alice"),
            _membre(None, "Alexandre Vincendet", fin="2024-03-19"),
        ]
    }

    candidats, par_groupe = build_roster_candidats_detaille([_GROUPE_AN], rosters_bruts)
    sans_slug = membres_sans_slug([_GROUPE_AN], rosters_bruts)

    assert [c["slug"] for c in candidats] == ["alice"]
    assert par_groupe["AN:LR"] == 1
    assert len(sans_slug) == 1
    assert sans_slug[0]["nom"] == "Alexandre Vincendet"
    assert sans_slug[0]["mandat_fin"] == "2024-03-19"


def test_un_membre_sans_slug_ne_bloque_pas_l_ecriture(tmp_path, monkeypatch):
    """Non bloquant, et c'est un choix — les 4 sont une catégorie déclarée.

    Même arbitrage que les 5 389 identifiants non résolus de #510 : ce qui
    doit être bruyant, c'est leur **nombre s'il bouge**, pas chaque entrée d'une
    liste écrite d'avance dans `raw_data/groupes_reels.json`. Les faire bloquer
    reviendrait à empêcher tout run tant que la clause 2 de la condition de
    retrait de #526 §9 n'est pas soldée.
    """
    config = tmp_path / "groupes_reels.json"
    config.write_text(json.dumps({"groupes": [_GROUPE_AN]}), encoding="utf-8")
    sortie = tmp_path / "roster_candidats.json"

    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda chambre, legislature=None, session=None: [
            _membre("alice", "Alice"),
            _membre(None, "Xavier Batut", fin="2023-08-29"),
        ],
    )

    code = generate_roster_candidats.main(
        ["--config", str(config), "--out", str(sortie)]
    )

    assert code == 0
    ecrit = json.loads(sortie.read_text(encoding="utf-8"))
    assert [c["slug"] for c in ecrit["candidats"]] == ["alice"]


def test_l_annotation_des_sans_slug_est_une_ligne_qui_les_nomme(capsys):
    """Destination : une annotation GitHub Actions, donc une seule ligne.

    Le décompte n'est jamais tronqué, les noms le sont au-delà de la borne —
    l'inverse ferait d'une annotation illisible le seul état visible d'un run.
    """
    sans_slug = [
        {
            "groupe": "AN:LR",
            "nom": f"Député {i}",
            "mandat_debut": "2022-06-29",
            "mandat_fin": "2024-03-19",
        }
        for i in range(generate_roster_candidats._MAX_MEMBRES_NOMMES + 3)
    ]

    resume = resume_membres_sans_slug(sans_slug)

    assert "\n" not in resume
    assert f"{len(sans_slug)} membre(s)" in resume
    assert "Député 0" in resume
    assert "+3 autre(s)" in resume
    assert "--divergence" in resume


def test_le_resume_nomme_chaque_membre_quand_ils_tiennent():
    sans_slug = [
        {
            "groupe": "AN:REN",
            "nom": "Pierre Henriet",
            "mandat_debut": "2022-06-29",
            "mandat_fin": "2024-02-15",
        }
    ]

    resume = resume_membres_sans_slug(sans_slug)

    assert "Pierre Henriet" in resume
    assert "2024-02-15" in resume
    assert "autre(s)" not in resume


def test_un_roster_entierement_slugue_ne_declare_rien():
    """Le cas Sénat, et le cas nominal : pas d'annotation sans membre écarté."""
    rosters_bruts = {("deputes", "16"): [_membre("alice", "Alice")]}
    assert membres_sans_slug([_GROUPE_AN], rosters_bruts) == []


# ---------------------------------------------------------------------------
# 3. Le `meta.warnings` publié nomme la source dont vient la composition
# ---------------------------------------------------------------------------

def test_l_avertissement_de_fraicheur_nomme_amo30(monkeypatch):
    """C'est un champ PUBLIÉ : le laisser dire `www.nosdeputes.fr` alors que la
    composition vient d'AMO30 est une atteinte à la traçabilité (AGENTS §2
    règle 2), pas une imprécision de rédaction."""
    monkeypatch.setattr(an_roster, "AN_ROSTER_ACTIF", True)

    avertissement = group_profile._avertissement_fraicheur_an()

    assert avertissement.startswith("fraicheur_donnees :")
    assert "dérivée du référentiel AMO30" in avertissement
    # Le miroir est nommé — au passé, et c'est délibéré : deux versions
    # successives d'une même fiche publiée doivent se relire l'une contre
    # l'autre. Ce qui est interdit, c'est de le présenter comme la source.
    assert "composition dérivée de www.nosdeputes.fr" not in avertissement


def test_l_avertissement_ne_suit_plus_aucun_repli(monkeypatch):
    """Le texte avait DEUX rédactions, choisies sur le drapeau : celle d'AMO30
    et celle de NosDéputés, la source du repli.

    #529 a retiré le repli. Un avertissement publié qui changerait de source
    selon un drapeau dont l'autre branche ne lit plus rien serait pire qu'inutile
    — il nommerait une source dont aucune composition ne peut venir. Il n'y a
    donc plus qu'une rédaction, et elle ne dépend plus du drapeau.
    """
    for actif in (True, False):
        monkeypatch.setattr(an_roster, "AN_ROSTER_ACTIF", actif)
        avertissement = group_profile._avertissement_fraicheur_an()
        assert "dérivée du référentiel AMO30" in avertissement
        assert "composition dérivée de www.nosdeputes.fr" not in avertissement
