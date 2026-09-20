import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from generate_all_profiles import load_candidats
from groupes_config import partitionner_groupes
from generate_roster_candidats import (
    anomalies_roster,
    build_roster_candidats,
    build_roster_candidats_detaille,
    generate_roster_candidats,
    main as generate_roster_candidats_main,
)

import pytest

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


def _deputes_payload():
    return [
        {"acteur_ref": "PA1", "slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA2", "slug": "bob", "nom": "Bob", "groupe_sigle": "SOC", "mandat_debut": "2022-06-22", "mandat_fin": None},
    ]


def _deputes_15_payload():
    """#528 : la deuxième clé de fetch était le Sénat, retiré du périmètre.
    C'est désormais une SECONDE LÉGISLATURE de l'Assemblée — ce que ces tests
    éprouvent est le partage d'un fetch par clé `(chambre, législature)`, pas la
    chambre elle-même."""
    return [
        {"acteur_ref": "PA3", "slug": "carla", "nom": "Carla", "groupe_sigle": "LR", "mandat_debut": "2017-06-21", "mandat_fin": "2022-06-21"},
    ]


_GROUPE_LR_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}
_GROUPE_SOC_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:SOC", "groupe_sigle": "SOC",
    "groupe_nom": "Socialistes", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-SOC-16.json",
}
_GROUPE_LR_AN_15 = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR-15", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "15",
    "fichier": "groupe-AN-LR-15.json",
}


# ---------------------------------------------------------------------------
# build_roster_candidats : fonction pure (pas d'accès réseau)
# ---------------------------------------------------------------------------

def test_build_roster_candidats_flattens_and_formats():
    rosters_bruts = {("deputes", "16"): _deputes_payload()}
    groupes = [_GROUPE_LR_AN, _GROUPE_SOC_AN]

    candidats = build_roster_candidats(groupes, rosters_bruts)

    par_slug = {c["slug"]: c for c in candidats}
    assert set(par_slug) == {"alice", "bob"}

    alice = par_slug["alice"]
    assert alice["nom"] == "Alice"
    assert alice["parti"] is None
    assert alice["famille_politique"] is None
    assert alice["statut"] == "roster_groupe"
    assert alice["date_declaration"] is None
    # `source` pointait vers `www.nosdeputes.fr/<slug>`, construite depuis la
    # législature par `group_roster._base_url_for`. Les deux sont partis avec
    # la plateforme (#529) : c'est la fiche AN de l'acteur qui la remplace.
    assert alice["source"] == "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA1"
    assert "LR" in alice["notes"]

    bob = par_slug["bob"]
    assert bob["source"] == "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA2"
    assert "SOC" in bob["notes"]


def test_build_roster_candidats_skips_group_with_failed_fetch():
    rosters_bruts = {("deputes", "16"): None}
    groupes = [_GROUPE_LR_AN]

    candidats = build_roster_candidats(groupes, rosters_bruts)

    assert candidats == []


def test_build_roster_candidats_dedups_by_slug_guard():
    # Garde-fou : deux entrées de config pointant vers le même (chambre, legislature)
    # avec un sigle mal configuré ne doivent pas produire de doublon par slug.
    rosters_bruts = {("deputes", "16"): _deputes_payload()}
    groupe_lr_dupe = dict(_GROUPE_LR_AN, groupe_id="AN:LR-dupe", fichier="groupe-AN-LR-16-dupe.json")
    groupes = [_GROUPE_LR_AN, groupe_lr_dupe]

    candidats = build_roster_candidats(groupes, rosters_bruts)

    assert [c["slug"] for c in candidats] == ["alice"]


def test_build_roster_candidats_independent_from_editorial_candidats_json():
    # Un membre présent aussi dans raw_data/candidats.json (ex. jean-luc-melenchon)
    # doit apparaître dans la liste roster sans aucune fusion/consultation de
    # raw_data/candidats.json — les deux listes restent distinctes à ce stade.
    rosters_bruts = {("deputes", "16"): [
        {"slug": "jean-luc-melenchon", "nom": "Jean-Luc Mélenchon", "groupe_sigle": "LFI", "mandat_debut": "2022-06-22", "mandat_fin": None},
    ]}
    groupe_lfi = dict(_GROUPE_LR_AN, groupe_sigle="LFI", groupe_nom="La France insoumise - NUPES")

    candidats = build_roster_candidats([groupe_lfi], rosters_bruts)

    assert len(candidats) == 1
    assert candidats[0]["slug"] == "jean-luc-melenchon"
    assert candidats[0]["statut"] == "roster_groupe"
    assert candidats[0]["parti"] is None  # pas de fusion avec candidats.json (parti y est renseigné)


# ---------------------------------------------------------------------------
# generate_roster_candidats : un seul fetch réseau par (chambre, législature)
# ---------------------------------------------------------------------------

def test_generate_roster_candidats_fetches_once_per_chambre_legislature(monkeypatch):
    call_count = {"n": 0}

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        call_count["n"] += 1
        assert chambre == "deputes"
        assert legislature == "16"
        return _deputes_payload()

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    candidats = generate_roster_candidats([_GROUPE_LR_AN, _GROUPE_SOC_AN])

    assert call_count["n"] == 1
    assert {c["slug"] for c in candidats} == {"alice", "bob"}


def test_generate_roster_candidats_two_chambres_two_fetches(monkeypatch):
    fetch_calls = []

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        fetch_calls.append((chambre, legislature))
        return _deputes_payload() if legislature == "16" else _deputes_15_payload()

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    candidats = generate_roster_candidats([_GROUPE_LR_AN, _GROUPE_LR_AN_15])

    assert len(fetch_calls) == 2
    assert set(fetch_calls) == {("deputes", "16"), ("deputes", "15")}
    assert {c["slug"] for c in candidats} == {"alice", "carla"}
    # La `source` ne dépend plus de la législature : elle identifie l'acteur,
    # pas le sous-domaine d'archive où on l'a trouvé (#529).
    assert next(c for c in candidats if c["slug"] == "carla")["source"] == (
        "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA3"
    )


def test_generate_roster_candidats_fetch_failure_is_ignored(monkeypatch):
    """La fonction PURE reste tolérante — c'est `main()` qui refuse d'écrire.

    Distinction voulue depuis #511 : `build_roster_candidats` est une
    transformation (elle décrit ce que la collecte a rendu), `main()` est une
    décision de publication (elle décide si ce résultat a le droit d'être écrit).
    Mélanger les deux forcerait chaque appelant à porter la politique.
    """
    import requests

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        raise requests.RequestException("boom")

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    candidats = generate_roster_candidats([_GROUPE_LR_AN])

    assert candidats == []


# ---------------------------------------------------------------------------
# Sortie JSON rechargeable par load_candidats()
# ---------------------------------------------------------------------------

def test_output_reloadable_by_load_candidats(tmp_path, monkeypatch):
    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        return _deputes_payload()

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    config_path = tmp_path / "groupes_reels.json"
    config_path.write_text(json.dumps({"groupes": [_GROUPE_LR_AN, _GROUPE_SOC_AN]}), encoding="utf-8")
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 0
    assert out_path.exists()

    candidats = load_candidats(str(out_path))
    assert {c["slug"] for c in candidats} == {"alice", "bob"}
    for c in candidats:
        # #850 : `acteur_ref` en clair, pour que la collecte ne re-devine plus
        # par le nom un acteur que le roster désigne.
        assert set(c) == {"nom", "slug", "parti", "famille_politique", "statut",
                          "date_declaration", "source", "notes", "acteur_ref"}


def test_main_missing_config_returns_error(tmp_path):
    rc = generate_roster_candidats_main(["--config", str(tmp_path / "does-not-exist.json")])
    assert rc == 1


def test_main_empty_groupes_returns_error(tmp_path):
    config_path = tmp_path / "empty.json"
    config_path.write_text(json.dumps({"groupes": []}), encoding="utf-8")
    rc = generate_roster_candidats_main(["--config", str(config_path)])
    assert rc == 1


# ---------------------------------------------------------------------------
# #511 — le roster n'est jamais écrit sur une collecte incomplète
#
# Le run 32405297873 (20/08/2026) s'est conclu en `success` avec un roster de 0
# candidat écrit après deux `Read timed out`, et la passe pivot suivante a itéré
# sur le vide : 229 profils bruts pour 209 pivots au commit 68bc094.
#
# Toutes les doublures ci-dessous sont locales (monkeypatch de
# `fetch_full_roster`) : aucune ne touche le réseau ni le corpus vivant.
# ---------------------------------------------------------------------------

def _config(tmp_path, groupes):
    chemin = tmp_path / "groupes_reels.json"
    chemin.write_text(json.dumps({"groupes": groupes}), encoding="utf-8")
    return chemin


def _timeout_sur(cles):
    """Doublure du `Read timed out` de l'incident, pour les clés nommées.

    #528 : la clé est `(chambre, législature)` et non plus la seule chambre —
    les deux clés de ces tests sont maintenant deux législatures de la même
    chambre, le Sénat étant sorti du périmètre.
    """
    import requests

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        if (chambre, legislature) in cles:
            raise requests.RequestException(
                "HTTPSConnectionPool(host='www.nosdeputes.fr', port=443): "
                "Read timed out. (read timeout=15)"
            )
        return _deputes_payload() if legislature == "16" else _deputes_15_payload()

    return fake_fetch_full_roster


def test_les_deux_fetchs_en_timeout_n_ecrivent_pas_le_roster(tmp_path, monkeypatch, capsys):
    """L'incident rejoué à l'identique : 0 candidat, et un code de sortie 0."""
    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster",
                        _timeout_sur({("deputes", "16"), ("deputes", "15")}))
    config_path = _config(tmp_path, [_GROUPE_LR_AN, _GROUPE_LR_AN_15])
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 1, "un roster vide écrit avec un code 0 est exactement l'incident"
    assert not out_path.exists(), "le roster ne doit pas être écrit du tout"
    err = capsys.readouterr().err
    assert "ROSTER_INCOMPLET" in err


def test_un_roster_existant_n_est_pas_ecrase_par_une_collecte_en_echec(tmp_path, monkeypatch):
    """Le fichier précédent survit intact — il n'est ni vidé ni réécrit."""
    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster",
                        _timeout_sur({("deputes", "16")}))
    config_path = _config(tmp_path, [_GROUPE_LR_AN])
    out_path = tmp_path / "roster_candidats.json"
    precedent = json.dumps({"candidats": [{"slug": "alice", "nom": "Alice"}]})
    out_path.write_text(precedent, encoding="utf-8")

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 1
    assert out_path.read_text(encoding="utf-8") == precedent


def test_un_seul_fetch_en_echec_bloque_aussi(tmp_path, monkeypatch, capsys):
    """LE cas qu'un test de vacuité ne verrait pas.

    Sur `raw_data/groupes_reels.json` au 19/08/2026, les deux clés de fetch
    valent 452 (AN) et 300 (Sénat) membres sur 752 : un échec partiel n'enlève
    pas « quelques » membres, il en enlève 40 % ou 60 % d'un coup, et le roster
    reste NON VIDE. C'est la réponse à « faut-il refuser un roster qui
    rétrécit ? » — oui, et par la cause, pas par un seuil chiffré.
    """
    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster",
                        _timeout_sur({("deputes", "15")}))
    config_path = _config(tmp_path, [_GROUPE_LR_AN, _GROUPE_SOC_AN, _GROUPE_LR_AN_15])
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 1
    assert not out_path.exists()
    err = capsys.readouterr().err
    assert "deputes" in err
    assert "INCONNUE, pas vide" in err


def test_un_groupe_configure_sans_membre_bloque(tmp_path, monkeypatch, capsys):
    """Dernier mécanisme de rétrécissement : le sigle ne matche plus.

    Le fetch réussit, le filtre ne retient personne. Aucun échec réseau à
    signaler, un roster non vide — et pourtant un groupe entier disparaît.
    """
    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        return _deputes_payload()

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)
    groupe_inconnu = dict(_GROUPE_LR_AN, groupe_id="AN:XYZ", groupe_sigle="XYZ")
    config_path = _config(tmp_path, [_GROUPE_LR_AN, groupe_inconnu])
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 1
    assert not out_path.exists()
    assert "AN:XYZ" in capsys.readouterr().err


def test_collecte_complete_ecrit_et_rend_zero(tmp_path, monkeypatch):
    """Le cas nominal reste inchangé : rien de ce qui marchait ne se met à bloquer."""
    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        return _deputes_payload() if legislature == "16" else _deputes_15_payload()

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)
    config_path = _config(tmp_path, [_GROUPE_LR_AN, _GROUPE_SOC_AN, _GROUPE_LR_AN_15])
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 0
    assert {c["slug"] for c in load_candidats(str(out_path))} == {"alice", "bob", "carla"}


def test_autoriser_roster_incomplet_ecrit_quand_meme(tmp_path, monkeypatch, capsys):
    """L'échappatoire existe, elle n'est câblée sur aucun input du workflow."""
    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster",
                        _timeout_sur({("deputes", "15")}))
    config_path = _config(tmp_path, [_GROUPE_LR_AN, _GROUPE_LR_AN_15])
    out_path = tmp_path / "roster_candidats.json"

    rc = generate_roster_candidats_main([
        "--config", str(config_path), "--out", str(out_path),
        "--autoriser-roster-incomplet",
    ])

    assert rc == 0
    assert {c["slug"] for c in load_candidats(str(out_path))} == {"alice"}
    err = capsys.readouterr().err
    assert "deputes" in err, "les anomalies restent affichées, la tolérance ne les tait pas"


def test_le_workflow_ne_cable_aucune_tolerance_de_roster():
    """Un input qui autoriserait un roster incomplet rouvrirait #511."""
    workflow = (Path(__file__).resolve().parents[1]
                / ".github" / "workflows" / "generate-data.yml").read_text(encoding="utf-8")
    assert "--autoriser-roster-incomplet" not in workflow


# --- décompte par groupe et anomalies : fonctions pures ---------------------

def test_build_detaille_compte_les_membres_par_groupe():
    rosters_bruts = {("deputes", "16"): _deputes_payload()}
    candidats, par_groupe = build_roster_candidats_detaille(
        [_GROUPE_LR_AN, _GROUPE_SOC_AN], rosters_bruts)

    assert len(candidats) == 2
    assert par_groupe == {"AN:LR": 1, "AN:SOC": 1}


def test_build_detaille_compte_zero_pour_un_groupe_dont_le_fetch_a_echoue():
    """Le groupe doit apparaître au décompte avec 0, pas manquer du décompte :
    une clé absente et une clé à 0 se lisent pareil chez l'appelant."""
    _, par_groupe = build_roster_candidats_detaille(
        [_GROUPE_LR_AN], {("deputes", "16"): None})

    assert par_groupe == {"AN:LR": 0}


def test_anomalies_roster_est_vide_sur_une_collecte_complete():
    rosters_bruts = {("deputes", "16"): _deputes_payload()}
    groupes = [_GROUPE_LR_AN, _GROUPE_SOC_AN]
    candidats, par_groupe = build_roster_candidats_detaille(groupes, rosters_bruts)

    assert anomalies_roster(groupes, rosters_bruts, par_groupe, candidats) == []


def test_anomalies_roster_ne_repete_pas_les_groupes_d_un_fetch_en_echec():
    """La cause d'abord, une fois — pas une ligne par conséquence.

    Cinq groupes AN derrière une seule clé en échec doivent produire UNE
    anomalie, celle du fetch, pas six.
    """
    groupes = [_GROUPE_LR_AN, _GROUPE_SOC_AN]
    rosters_bruts = {("deputes", "16"): None}
    candidats, par_groupe = build_roster_candidats_detaille(groupes, rosters_bruts)

    anomalies = anomalies_roster(groupes, rosters_bruts, par_groupe, candidats)

    assert len(anomalies) == 2, anomalies
    assert "deputes" in anomalies[0]
    assert "roster total vide" in anomalies[1]


# ---------------------------------------------------------------------------
# Cohérence miroir de test_repository_groupes_reels_json_is_valid
# (tests/test_generate_group_profiles.py), appliquée au fichier généré à
# partir des données réelles du dépôt (fetch réseau mocké).
# ---------------------------------------------------------------------------

_PAYLOADS_REELS = {
    "deputes": [
        {"acteur_ref": "PA10", "slug": "alice", "nom": "Alice", "groupe_sigle": "REN", "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA11", "slug": "bob", "nom": "Bob", "groupe_sigle": "SOC", "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA12", "slug": "carla", "nom": "Carla", "groupe_sigle": "RN", "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA13", "slug": "dan", "nom": "Dan", "groupe_sigle": "LFI", "mandat_debut": "2022-06-22", "mandat_fin": None},
        {"acteur_ref": "PA14", "slug": "eve", "nom": "Eve", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None},
    ],
    "senateurs": [
        {"acteur_ref": None, "slug": "farid", "nom": "Farid", "groupe_sigle": "LR", "mandat_debut": "2020-01-01", "mandat_fin": None},
        {"acteur_ref": None, "slug": "gina", "nom": "Gina", "groupe_sigle": "SER", "mandat_debut": "2020-01-01", "mandat_fin": None},
    ],
}


def _groupes_reels() -> list[dict]:
    config_path = Path(__file__).resolve().parents[1] / "raw_data" / "groupes_reels.json"
    return json.loads(config_path.read_text(encoding="utf-8"))["groupes"]


def test_repository_groupes_reels_json_produces_valid_roster_candidats(monkeypatch):
    groupes = _groupes_reels()

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        return _PAYLOADS_REELS[chambre]

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    candidats = generate_roster_candidats(groupes)

    # Attendu dérivé de la config, pas figé : ce test doit rester vrai qu'une
    # entrée soit suspendue (#516) ou réactivée, sans être réécrit à chaque
    # bascule — sinon il finit par décrire l'état d'hier.
    actifs, _ = partitionner_groupes(groupes)
    attendus = {
        membre["slug"]
        for groupe in actifs
        for membre in _PAYLOADS_REELS[groupe["roster_chambre"]]
        if membre["groupe_sigle"] == groupe["groupe_sigle"]
    }

    assert isinstance(candidats, list)
    assert candidats
    assert {c["slug"] for c in candidats} == attendus
    for c in candidats:
        assert c["statut"] == "roster_groupe"
        assert c["slug"]
        assert c["nom"]
        # `source` reste `None` quand la source ne rend pas d'`acteur_ref` : on
        # n'invente pas d'URL de fiche (règle 5). Les entrées AN en portent un,
        # et les 2 entrées Sénat sont suspendues depuis #516 — donc jamais
        # collectées ici.
        assert c["source"], f"{c['slug']} : source manquante"

    # Rechargeable sans erreur par generate_all_profiles.load_candidats().
    payload_path_content = json.dumps({"candidats": candidats}, ensure_ascii=False)
    reloaded = json.loads(payload_path_content).get("candidats")
    assert reloaded == candidats
