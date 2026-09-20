"""Une anomalie de roster nomme sa cause, et la suspension totale n'en est pas une (#524).

## A — porter l'exception jusqu'à l'annotation

`fetch_rosters_bruts` affichait l'exception sur `stderr` puis la **jetait**
(`rosters_bruts[key] = None`). `anomalies_roster` reconstruisait ensuite son
message à partir de la **seule clé**, si bien que l'annotation `::error::`
ajoutée par #518 — dont c'était pourtant tout l'objet — disait « en échec » et
rien d'autre : jamais `HTTP 500`, jamais `SSLError`, jamais `Read timed out`.

Le run `32876863499` (24/08/2026) en a fait la démonstration : 3 jobs rouges,
la même annotation muette dans les trois, et il a fallu sonder l'endpoint à la
main pour découvrir que `www.nosdeputes.fr/deputes/json` répondait 500 en
0,4 s. Quatre runs sont morts sur cette ligne en une semaine.

## C — « tous les groupes suspendus » est une décision, pas une anomalie

`main()` sortait en **1** quand toutes les entrées de `groupes_reels.json`
portaient `extraction_suspendue`. Or suspendre les entrées AN — comme les 2
entrées Sénat le sont depuis #516 — est le remède documenté d'une source en
panne : tant que ce cas sortait en 1, **le remède reproduisait l'échec qu'il
devait éteindre**, et il n'existait aucun moyen de conclure un run vert pendant
que NosDéputés répondait 500.

Ce que ce code ne dit jamais : « écris un roster vide ». Chaque test ci-dessous
vérifie aussi que **rien n'est écrit** — c'est l'interdit de #511, et il n'est
pas assoupli.

Aucun test de ce fichier ne touche le réseau (`fetch_full_roster` est doublé)
ni ne lit `pivot_data/` (AGENTS.md §3).
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from generate_roster_candidats import (  # noqa: E402
    EXIT_ROSTER_INDISPONIBLE,
    anomalies_roster,
    build_roster_candidats_detaille,
    fetch_rosters_bruts,
    main as generate_roster_candidats_main,
    resume_exception,
)

_GROUPE_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}
_GROUPE_SENAT_SUSPENDU = {
    "roster_chambre": "senateurs", "groupe_id": "Senat:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "Senat", "legislature": None,
    "fichier": "groupe-Senat-LR.json",
    "extraction_suspendue": {
        "depuis": "2026-08-24",
        "motif": "certificat TLS expiré sur archive.nossenateurs.fr",
        "references": ["#516"],
        "condition_reprise": "GET https://archive.nossenateurs.fr/senateurs/json en 200",
    },
}


def _config(tmp_path, groupes) -> Path:
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps({"groupes": groupes}), encoding="utf-8")
    return chemin


def _http_error(statut: int) -> requests.HTTPError:
    """Le `HTTPError` que `raise_for_status()` produit, réponse attachée."""
    reponse = MagicMock()
    reponse.status_code = statut
    erreur = requests.HTTPError(
        f"{statut} Server Error: Internal Server Error for url: "
        "https://www.nosdeputes.fr/deputes/json"
    )
    erreur.response = reponse
    return erreur


#: Les trois familles réellement observées sur cette source, et leur signature
#: attendue dans l'anomalie. La cause n'est pas décorative : c'est elle qui
#: distingue « relancer » (Timeout) de « suspendre » (SSLError, 500).
_PANNES = [
    pytest.param(_http_error(500), "HTTPError", "500 Server Error", id="http-500"),
    pytest.param(
        requests.exceptions.SSLError(
            "HTTPSConnectionPool(host='archive.nossenateurs.fr', port=443): "
            "certificate verify failed: certificate has expired"
        ),
        "SSLError", "certificate has expired", id="ssl",
    ),
    pytest.param(
        requests.Timeout(
            "HTTPSConnectionPool(host='www.nosdeputes.fr', port=443): "
            "Read timed out. (read timeout=90)"
        ),
        "Timeout", "Read timed out", id="timeout",
    ),
]


# ---------------------------------------------------------------------------
# A — la cause remonte de `fetch_rosters_bruts` jusqu'au message
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("exc, type_attendu, extrait_attendu", _PANNES)
def test_le_fetch_conserve_l_exception_de_chaque_cle_tombee(
    monkeypatch, exc, type_attendu, extrait_attendu
):
    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        raise exc

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    rosters_bruts, echecs = fetch_rosters_bruts([_GROUPE_AN])

    assert rosters_bruts == {("deputes", "16"): None}
    assert echecs[("deputes", "16")] is exc


@pytest.mark.parametrize("exc, type_attendu, extrait_attendu", _PANNES)
def test_l_anomalie_nomme_le_type_et_le_message_de_l_exception(
    monkeypatch, exc, type_attendu, extrait_attendu
):
    """LE test de ce fichier : le verdict doit se lire sans télécharger un log."""
    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        raise exc

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    rosters_bruts, echecs = fetch_rosters_bruts([_GROUPE_AN])
    candidats, par_groupe = build_roster_candidats_detaille([_GROUPE_AN], rosters_bruts)
    anomalies = anomalies_roster([_GROUPE_AN], rosters_bruts, par_groupe, candidats, echecs)

    assert type_attendu in anomalies[0], anomalies[0]
    assert extrait_attendu in anomalies[0], anomalies[0]
    # Le verdict de #511 reste porté par la même phrase : la cause s'ajoute,
    # elle ne remplace rien.
    assert "INCONNUE, pas vide" in anomalies[0]


@pytest.mark.parametrize("exc, type_attendu, extrait_attendu", _PANNES)
def test_l_annotation_gha_porte_la_cause(
    tmp_path, monkeypatch, capsys, exc, type_attendu, extrait_attendu
):
    """Sur stdout, en une ligne : c'est là et seulement là que GitHub lit."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        raise exc

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main(
        ["--config", str(_config(tmp_path, [_GROUPE_AN])), "--out", str(out_path)])

    assert rc == 1
    assert not out_path.exists()
    annotations = [
        ligne for ligne in capsys.readouterr().out.splitlines()
        if ligne.startswith("::error::")
    ]
    roster = [a for a in annotations if a.startswith("::error::ROSTER —")]
    assert roster, annotations
    assert type_attendu in roster[0], roster[0]
    assert extrait_attendu in roster[0], roster[0]
    assert len(roster[0].splitlines()) == 1


def test_une_cle_sans_exception_connue_garde_le_message_d_origine():
    """`anomalies_roster` reste appelable sans `echecs` — et n'invente alors
    aucune cause plutôt que d'en supposer une (AGENTS.md §2 règle 5)."""
    rosters_bruts = {("deputes", "16"): None}
    candidats, par_groupe = build_roster_candidats_detaille([_GROUPE_AN], rosters_bruts)

    anomalies = anomalies_roster([_GROUPE_AN], rosters_bruts, par_groupe, candidats)

    assert anomalies[0] == (
        "récupération du roster (deputes, législature=16) en échec : "
        "la composition de ses groupes est INCONNUE, pas vide."
    )


def test_resume_exception_aplatit_et_borne():
    """Destination : une annotation, donc UNE ligne, et pas l'URL complète d'un
    dump de 814 Ko en travers d'une liste."""
    court = resume_exception(ValueError("boum\nsur deux lignes"))
    assert court == "ValueError: boum sur deux lignes"

    long = resume_exception(ValueError("x" * 500))
    assert long.startswith("ValueError: ")
    assert len(long) < 250
    assert long.endswith("…")

    assert resume_exception(ValueError()) == "ValueError: aucun message"


# ---------------------------------------------------------------------------
# C — « tous les groupes suspendus » rend 2, et n'écrit rien
# ---------------------------------------------------------------------------

def test_tous_les_groupes_suspendus_rendent_le_code_2(tmp_path, monkeypatch):
    """Le cas de sortie du lot : c'est ce code que les trois appelants tolèrent.

    Rendre 1 ici, c'était rendre la suspension — le seul remède documenté —
    strictement équivalente à la panne qu'elle traite.
    """
    def interdit(*args, **kwargs):
        raise AssertionError("aucun fetch ne doit partir sur une config entièrement suspendue")

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", interdit)
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main([
        "--config", str(_config(tmp_path, [_GROUPE_SENAT_SUSPENDU])),
        "--out", str(out_path),
    ])

    assert rc == EXIT_ROSTER_INDISPONIBLE
    assert not out_path.exists(), "jamais de roster à 0 candidat (#511)"


def test_le_code_2_ne_se_confond_pas_avec_un_roster_incomplet(tmp_path, monkeypatch):
    """Les deux refusent d'écrire ; un seul est une décision.

    Un fetch tombé laisse une composition NON MESURÉE : le run doit le dire
    fort (code 1). Une suspension totale ne laisse rien du tout à mesurer.
    """
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        MagicMock(side_effect=_http_error(500)),
    )
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main([
        "--config", str(_config(tmp_path, [_GROUPE_AN, _GROUPE_SENAT_SUSPENDU])),
        "--out", str(out_path),
    ])

    assert rc == 1
    assert not out_path.exists()


def test_le_code_2_est_annonce_en_annotation(tmp_path, monkeypatch, capsys):
    """`warning` et non `error` : un run qui saute une branche délibérément
    suspendue n'a pas de défaut à signaler — mais l'onglet de résumé doit dire
    pourquoi il ne publie aucun profil de roster, sans quoi la suspension
    devient invisible au bout de deux runs (#516)."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        MagicMock(side_effect=AssertionError("aucun fetch attendu")),
    )

    rc = generate_roster_candidats_main([
        "--config", str(_config(tmp_path, [_GROUPE_SENAT_SUSPENDU])),
        "--out", str(tmp_path / "roster_candidats.json"),
    ])

    assert rc == EXIT_ROSTER_INDISPONIBLE
    sortie = capsys.readouterr().out.splitlines()
    warnings = [l for l in sortie if l.startswith("::warning::ROSTER_SUSPENDU")]
    assert warnings, sortie
    assert not [l for l in sortie if l.startswith("::error::")], (
        "une décision écrite n'est pas une erreur")


def test_le_code_2_reste_distinct_d_une_config_illisible(tmp_path):
    """Une config absente ou vide est un vrai défaut : elle garde le code 1.

    Sans cette séparation, le `if:` des appelants sauterait la branche roster
    sur une erreur de dépôt — un silence, exactement ce que #511 refuse.
    """
    assert generate_roster_candidats_main(
        ["--config", str(tmp_path / "absent.json")]) == 1
    assert generate_roster_candidats_main(
        ["--config", str(_config(tmp_path, []))]) == 1
