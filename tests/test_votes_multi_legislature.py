"""Votes nominatifs : agrégation multi-législature (issue #403).

Jusqu'à #403, `fetch_votes_officiels` ne couvrait qu'UNE législature par profil
— celle déduite du domaine NosDéputés où l'identité avait été trouvée, donc en
pratique toujours la 16e depuis #369. Le jeu de données s'arrêtait en juin 2024
et perdait 2,7x ses votes. Ces tests couvrent les quatre points exigés par
l'issue : couverture multi-législature, déduplication, archive au format
monolithique (14e), et législature indisponible n'empêchant pas les autres.
"""

import gzip
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile
from candidate_profile import (
    AN_SCRUTINS_LEGISLATURES,
    SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME,
    SCRUTINS_CACHE_SCRUTINS_FILENAME,
    SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME,
    SCRUTINS_FIGES_SCRUTINS_FILENAME,
    WARNING_PREFIX_VOTES_INTROUVABLES,
    _parse_scrutins_zip,
    _read_cached_votes_acteur,
    build_profile,
    fetch_votes_officiels,
)


@pytest.fixture(autouse=True)
def _purge_memo_store_scrutins():
    """Le mémo du store de scrutins est indexé par législature seule : sans
    purge, un test lirait le store mémoïsé du test précédent, dont le
    répertoire de cache a été patché ailleurs (même piège que pour les
    amendements, #377/#392)."""
    from candidate_profile import _clear_scrutins_store_memo

    _clear_scrutins_store_memo()
    yield
    _clear_scrutins_store_memo()


# ---------------------------------------------------------------------------
# Fabriques de données de test
# ---------------------------------------------------------------------------

def _scrutin_moderne(uid, numero, date, legislature, votants_par_position):
    """Scrutin au schéma 15/16/17 (clés `pours`/`contres` au pluriel)."""
    cle_par_position = {
        "pour": "pours",
        "contre": "contres",
        "abstention": "abstentions",
        "non_votant": "nonVotants",
    }
    decompte = {
        cle_par_position[position]: {"votant": [{"acteurRef": a} for a in acteurs]}
        for position, acteurs in votants_par_position.items()
    }
    return {
        "uid": uid,
        "numero": numero,
        "dateScrutin": date,
        "legislature": legislature,
        "titre": f"scrutin {numero} de la législature {legislature}",
        "sort": {"code": "adopté", "libelle": "l'Assemblée nationale a adopté"},
        "ventilationVotes": {
            "organe": {"groupes": {"groupe": [{"vote": {"decompteNominatif": decompte}}]}}
        },
    }


def _scrutin_legacy_14(uid, numero, date, votants_par_position):
    """Scrutin au schéma de la 14e législature : `pour`/`contre` au SINGULIER.

    Différence relevée le 18/08/2026 sur l'archive réelle `Scrutins_XIV.json`
    (`abstentions`/`nonVotants` restant identiques au schéma moderne)."""
    cle_par_position = {
        "pour": "pour",
        "contre": "contre",
        "abstention": "abstentions",
        "non_votant": "nonVotants",
    }
    decompte = {
        cle_par_position[position]: {"votant": [{"acteurRef": a} for a in acteurs]}
        for position, acteurs in votants_par_position.items()
    }
    return {
        "uid": uid,
        "numero": numero,
        "dateScrutin": date,
        "legislature": "14",
        "titre": f"scrutin {numero} de la 14e législature",
        "sort": {"code": "rejeté", "libelle": "l'Assemblée nationale n'a pas adopté"},
        "ventilationVotes": {
            "organe": {"groupes": {"groupe": {"vote": {"decompteNominatif": decompte}}}}
        },
    }


def _zip_scrutins_par_fichier(tmp_path, nom, scrutins):
    """Archive au conditionnement 15/16/17 : un fichier JSON par scrutin."""
    zip_path = tmp_path / nom
    with zipfile.ZipFile(zip_path, "w") as zf:
        for scrutin in scrutins:
            zf.writestr(f"json/{scrutin['uid']}.json", json.dumps({"scrutin": scrutin}))
    return zip_path


def _zip_scrutins_monolithique(tmp_path, nom, scrutins):
    """Archive au conditionnement de la 14e : un seul JSON `scrutins.scrutin[]`."""
    zip_path = tmp_path / nom
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("Scrutins_XIV.json", json.dumps({"scrutins": {"scrutin": scrutins}}))
    return zip_path


def _meta_store(numero, date, titre, legislature, sort=None):
    """Meta d'un scrutin à la forme écrite par `_parse_scrutins_zip`.

    La qualification (`type_scrutin`/`type_vote`/`demandeur`) en fait partie
    depuis #639, et un store qui ne la porte pas est traité comme un cache
    périmé (`_scrutins_store_qualifie`) : ces fabriques doivent donc l'écrire,
    sinon les tests mesureraient un cache que la production reconstruirait."""
    return {
        "numero": numero, "date": date, "titre": titre, "sort": sort,
        "legislature": legislature,
        "type_scrutin": "public_ordinaire",
        "type_vote": "vote_texte",
        "demandeur": "Président du groupe Les Républicains",
    }


def _ecrire_cache_scrutins(racine, legislature, scrutins, index_par_acteur):
    """Écrit un cache disque à la forme dédupliquée + shardée attendue."""
    cache_dir = racine / legislature
    (cache_dir / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME).mkdir(parents=True, exist_ok=True)
    (cache_dir / SCRUTINS_CACHE_SCRUTINS_FILENAME).write_text(
        json.dumps(scrutins), encoding="utf-8"
    )
    for acteur_ref, refs in index_par_acteur.items():
        (cache_dir / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME / f"{acteur_ref}.json").write_text(
            json.dumps(refs), encoding="utf-8"
        )


# ---------------------------------------------------------------------------
# Parsing des deux conditionnements d'archive
# ---------------------------------------------------------------------------

def test_parse_scrutins_zip_conditionnement_par_fichier(tmp_path):
    """Conditionnement 15/16/17 : un fichier par scrutin, meta dédupliqué."""
    zip_path = _zip_scrutins_par_fichier(
        tmp_path,
        "Scrutins.json.zip",
        [
            _scrutin_moderne("VTANR5L17V1", "1", "2024-10-01", "17", {"pour": ["PA1", "PA2"]}),
            _scrutin_moderne("VTANR5L17V2", "2", "2024-10-02", "17", {"contre": ["PA1"]}),
        ],
    )

    scrutins, index = _parse_scrutins_zip(zip_path, "17")

    assert set(scrutins) == {"VTANR5L17V1", "VTANR5L17V2"}
    assert scrutins["VTANR5L17V1"]["numero"] == "1"
    assert scrutins["VTANR5L17V1"]["legislature"] == "17"
    assert scrutins["VTANR5L17V1"]["sort"] == "l'Assemblée nationale a adopté"
    assert index["PA1"] == [["VTANR5L17V1", "pour"], ["VTANR5L17V2", "contre"]]
    assert index["PA2"] == [["VTANR5L17V1", "pour"]]


def test_parse_scrutins_zip_conditionnement_monolithique_14e(tmp_path):
    """L'archive de la 14e est un JSON monolithique aux clés `pour`/`contre` au
    singulier : les deux différences doivent être absorbées, sinon les 1 354
    scrutins réels de cette législature restent invisibles (l'indexeur
    d'avant #403 y trouvait 0 acteur)."""
    zip_path = _zip_scrutins_monolithique(
        tmp_path,
        "Scrutins_XIV.json.zip",
        [
            _scrutin_legacy_14("VTANR5L14V1", "1", "2012-07-03", {"pour": ["PA1"], "contre": ["PA2"]}),
            _scrutin_legacy_14("VTANR5L14V2", "2", "2012-07-04", {"abstention": ["PA1"], "non_votant": ["PA2"]}),
        ],
    )

    scrutins, index = _parse_scrutins_zip(zip_path, "14")

    assert len(scrutins) == 2, "Le JSON monolithique doit livrer tous ses scrutins"
    assert scrutins["VTANR5L14V1"]["legislature"] == "14"
    assert index["PA1"] == [["VTANR5L14V1", "pour"], ["VTANR5L14V2", "abstention"]]
    assert index["PA2"] == [["VTANR5L14V1", "contre"], ["VTANR5L14V2", "non_votant"]]


def test_parse_scrutins_zip_accepte_les_cles_singulieres_du_congres(tmp_path):
    """Le scrutin du Congrès `VTCGR5L16V1` (04/03/2024) mélange les deux
    schémas : `pour`/`contre` ET `abstention`/`nonVotant` au singulier. Les
    quatre positions doivent être reconnues — c'est ce relevé qui a révélé que
    l'indexeur d'avant #403 ne lisait que le pluriel."""
    scrutin = _scrutin_moderne("VTANR5L16V7", "7", "2024-03-04", "16", {})
    scrutin["ventilationVotes"]["organe"]["groupes"]["groupe"][0]["vote"]["decompteNominatif"] = {
        "pour": {"votant": [{"acteurRef": "PA1"}]},
        "contre": {"votant": [{"acteurRef": "PA2"}]},
        "abstention": {"votant": [{"acteurRef": "PA3"}]},
        "nonVotant": {"votant": [{"acteurRef": "PA4"}]},
    }
    zip_path = _zip_scrutins_par_fichier(tmp_path, "Scrutins.json.zip", [scrutin])

    _, index = _parse_scrutins_zip(zip_path, "16")

    assert index["PA1"] == [["VTANR5L16V7", "pour"]]
    assert index["PA2"] == [["VTANR5L16V7", "contre"]]
    assert index["PA3"] == [["VTANR5L16V7", "abstention"]]
    assert index["PA4"] == [["VTANR5L16V7", "non_votant"]]


def test_parse_scrutins_zip_ecarte_les_scrutins_du_congres(tmp_path):
    """Les archives AN contiennent aussi le scrutin du Congrès du 04/03/2024
    (uid `VTCGR…`). Il est écarté : sa numérotation repart de 1 et entre en
    collision avec la motion de censure n° 1 de la 16e — le publier donnerait
    une source primaire fausse (/dyn/16/scrutins/1 renvoie la motion) et
    confondrait les deux scrutins dans la cohésion de groupe."""
    zip_path = _zip_scrutins_par_fichier(
        tmp_path,
        "Scrutins.json.zip",
        [
            _scrutin_moderne("VTANR5L16V1", "1", "2022-07-11", "16", {"pour": ["PA1"]}),
            _scrutin_moderne("VTCGR5L16V1", "1", "2024-03-04", "16", {"pour": ["PA1"]}),
        ],
    )

    scrutins, index = _parse_scrutins_zip(zip_path, "16")

    assert set(scrutins) == {"VTANR5L16V1"}
    assert index["PA1"] == [["VTANR5L16V1", "pour"]]


def test_parse_scrutins_zip_ignore_scrutin_sans_ventilation(tmp_path):
    """Un scrutin sans ventilation nominative n'est pas indexé (aucune position
    ne peut en être tirée) et n'interrompt pas le parsing des autres."""
    zip_path = _zip_scrutins_par_fichier(
        tmp_path,
        "Scrutins.json.zip",
        [_scrutin_moderne("VTANR5L17V2", "2", "2024-10-02", "17", {"pour": ["PA1"]})],
    )
    with zipfile.ZipFile(zip_path, "a") as zf:
        zf.writestr("json/VTANR5L17V9.json", json.dumps({"scrutin": {"uid": "VTANR5L17V9", "numero": "9"}}))

    scrutins, index = _parse_scrutins_zip(zip_path, "17")

    assert set(scrutins) == {"VTANR5L17V2"}
    assert index["PA1"] == [["VTANR5L17V2", "pour"]]


# ---------------------------------------------------------------------------
# Lecture shardée du cache
# ---------------------------------------------------------------------------

def test_read_cached_votes_acteur_resout_les_references(tmp_path):
    """Les références compactes `[uid, position]` de l'acteur sont résolues via
    le store dédupliqué, sans jamais charger l'index complet."""
    _ecrire_cache_scrutins(
        tmp_path,
        "17",
        scrutins={
            "VTANR5L17V1": {"numero": "1", "date": "2024-10-01", "titre": "T1", "sort": None, "legislature": "17"},
            "VTANR5L17V2": {"numero": "2", "date": "2024-10-02", "titre": "T2", "sort": None, "legislature": "17"},
        },
        index_par_acteur={
            "PA1": [["VTANR5L17V1", "pour"]],
            "PA2": [["VTANR5L17V2", "contre"]],
        },
    )

    with (
        patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        votes = _read_cached_votes_acteur("17", "PA1")

    assert votes == [
        {
            "numero": "1", "date": "2024-10-01", "titre": "T1", "sort": None,
            "legislature": "17", "uid": "VTANR5L17V1", "position": "pour",
        }
    ]
    mock_get.assert_not_called()


def test_read_cached_votes_acteur_distingue_absence_et_cache_manquant(tmp_path):
    """Acteur absent de l'index → liste vide ; cache absent → None. Confondre
    les deux publierait « 0 vote » pour une donnée simplement manquante
    (AGENTS.md règle 5)."""
    _ecrire_cache_scrutins(tmp_path, "17", scrutins={}, index_par_acteur={"PA1": []})

    with patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path):
        assert _read_cached_votes_acteur("17", "PA9") == []
        assert _read_cached_votes_acteur("16", "PA1") is None


# ---------------------------------------------------------------------------
# Agrégation multi-législature
# ---------------------------------------------------------------------------

def test_fetch_votes_officiels_agrege_toutes_les_legislatures(tmp_path):
    """Le cœur de #403 : un député ayant siégé sous plusieurs législatures doit
    porter les votes de toutes, pas seulement ceux de la 16e."""
    for legislature, uid in (("15", "VTANR5L15V1"), ("16", "VTANR5L16V1"), ("17", "VTANR5L17V1")):
        _ecrire_cache_scrutins(
            tmp_path,
            legislature,
            scrutins={
                uid: _meta_store("1", f"20{legislature}-01-01", f"T{legislature}", legislature)
            },
            index_par_acteur={"PA1": [[uid, "pour"]]},
        )

    with (
        patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path),
        # Restreint aux trois législatures peuplées ci-dessus : la 14e, sans
        # cache, prendrait le chemin réseau et brouillerait l'assertion
        # « aucun téléchargement » (elle a son propre test).
        patch("candidate_profile.AN_SCRUTINS_LEGISLATURES", ("17", "16", "15")),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        votes, legislatures = fetch_votes_officiels("https://www.assemblee-nationale.fr/dyn/deputes/PA1")

    assert legislatures == ["15", "16", "17"]
    assert [v["legislature"] for v in votes] == ["17", "16", "15"], "Tri du plus récent au plus ancien"
    mock_get.assert_not_called()


def test_fetch_votes_officiels_dedoublonne_par_uid_de_scrutin(tmp_path):
    """Un même scrutin présent dans deux législatures (uid identique) n'est
    compté qu'une fois — un vote ne doit jamais être compté deux fois (#400).

    La déduplication porte sur l'`uid`, jamais sur le `numero` : celui-ci
    repart de 1 à chaque législature, donc dédoublonner par numéro effacerait
    des scrutins distincts (ici, le n° 1 de la 16e ET celui de la 17e)."""
    meta_partage = {"VTANR5L17V1": _meta_store("1", "2024-10-01", "T", "17")}
    _ecrire_cache_scrutins(tmp_path, "17", meta_partage, {"PA1": [["VTANR5L17V1", "pour"]]})
    _ecrire_cache_scrutins(
        tmp_path,
        "16",
        {
            **meta_partage,
            "VTANR5L16V1": _meta_store("1", "2023-01-01", "T16", "16"),
        },
        {"PA1": [["VTANR5L17V1", "pour"], ["VTANR5L16V1", "contre"]]},
    )

    with (
        patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path),
        patch("candidate_profile.AN_SCRUTINS_LEGISLATURES", ("17", "16")),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        votes, _ = fetch_votes_officiels("https://www.assemblee-nationale.fr/dyn/deputes/PA1")

    mock_get.assert_not_called()
    uids = [v["uid"] for v in votes]
    assert uids == ["VTANR5L17V1", "VTANR5L16V1"]
    assert len(uids) == len(set(uids)), "Aucun scrutin ne doit être compté deux fois"


def test_fetch_votes_officiels_legislature_indisponible_nempeche_pas_les_autres(tmp_path):
    """Une législature dont l'index est absent ne doit pas faire perdre les
    autres (même précaution qu'en #241 sur les amendements), et son absence
    doit être tracée nommément."""
    _ecrire_cache_scrutins(
        tmp_path,
        "17",
        {"VTANR5L17V1": _meta_store("1", "2024-10-01", "T", "17")},
        {"PA1": [["VTANR5L17V1", "pour"]]},
    )

    warnings: list[str] = []
    with (
        patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path),
        # Aucun repli committé et aucun réseau : les autres législatures
        # restent indisponibles pour de bon.
        patch("candidate_profile.AN_SCRUTINS_FIGES_DIR", tmp_path / "figes-absent"),
        patch("candidate_profile.requests.get", side_effect=candidate_profile.requests.RequestException("réseau coupé")),
    ):
        votes, legislatures = fetch_votes_officiels(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1", warnings
        )

    assert len(votes) == 1, "Les votes de la législature disponible doivent être conservés"
    assert legislatures == ["17"]
    manquantes = [leg for leg in AN_SCRUTINS_LEGISLATURES if leg != "17"]
    for leg in manquantes:
        assert any(
            w.startswith(WARNING_PREFIX_VOTES_INTROUVABLES) and f"législature {leg}" in w
            for w in warnings
        ), f"L'indisponibilité de la législature {leg} doit être tracée"


def test_fetch_votes_officiels_sans_acteur_ref_ne_touche_pas_au_reseau():
    """Sans acteurRef exploitable, aucun index n'est construit ni téléchargé."""
    with patch("candidate_profile.requests.get") as mock_get:
        votes, legislatures = fetch_votes_officiels(None)

    assert (votes, legislatures) == ([], [])
    mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# Législatures figées (budget CI)
# ---------------------------------------------------------------------------

def test_legislature_figee_est_materialisee_sans_reseau(tmp_path):
    """Une législature figée (14/15/16) doit être servie depuis l'index committé,
    sans aucun téléchargement : c'est ce qui retire 3 archives sur 4 du budget
    réseau de chaque shard CI."""
    figes = tmp_path / "figes"
    (figes / "16").mkdir(parents=True)
    with gzip.open(figes / "16" / SCRUTINS_FIGES_SCRUTINS_FILENAME, "wt", encoding="utf-8") as f:
        json.dump({"VTANR5L16V1": _meta_store("1", "2023-01-01", "T", "16")}, f)
    with gzip.open(figes / "16" / SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME, "wt", encoding="utf-8") as f:
        json.dump({"PA1": [["VTANR5L16V1", "pour"]]}, f)

    with (
        patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path / "cache"),
        patch("candidate_profile.AN_SCRUTINS_FIGES_DIR", figes),
        patch("candidate_profile.AN_SCRUTINS_LEGISLATURES", ("16",)),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        votes, legislatures = fetch_votes_officiels("https://www.assemblee-nationale.fr/dyn/deputes/PA1")

    assert legislatures == ["16"]
    assert votes[0]["position"] == "pour"
    mock_get.assert_not_called()


def test_cache_plat_herite_est_reconstruit_et_supprime(tmp_path):
    """Un cache écrit avant #403 (fichier unique, meta recopié par votant) doit
    être reconstruit, jamais relu : c'est cette forme plate — jusqu'à 357 Mo
    par législature — qui a provoqué deux OOM sur les amendements (#377, #392)."""
    from candidate_profile import _scrutins_cache_present, _write_cached_scrutins

    cache = tmp_path / "16"
    cache.mkdir(parents=True)
    legacy = cache / "index_par_acteur.json"
    legacy.write_text(json.dumps({"PA1": [{"numero": "1", "titre": "T", "position": "pour"}]}), encoding="utf-8")
    (cache / "json").mkdir()
    (cache / "json" / "VTANR5L16V1.json").write_text("{}", encoding="utf-8")

    with patch("candidate_profile.SCRUTINS_CACHE_DIR", tmp_path):
        assert _scrutins_cache_present("16") is False, "L'ancien format ne doit pas passer pour un cache valide"
        _write_cached_scrutins(
            "16",
            {"VTANR5L16V1": _meta_store("1", "2023-01-01", "T", "16")},
            {"PA1": [["VTANR5L16V1", "pour"]]},
        )
        assert _scrutins_cache_present("16") is True

    assert not legacy.exists(), "L'index plat hérité doit être supprimé, pas laissé à occuper des centaines de Mo"
    assert not (cache / "json").exists(), "L'arborescence décompressée n'a plus lieu d'être conservée"


# ---------------------------------------------------------------------------
# votes_source : refléter l'ensemble des législatures couvertes
# ---------------------------------------------------------------------------

def _build_profile_avec_votes(votes, legislatures):
    """Construit un profil de député avec des votes officiels simulés.

    L'identité venait d'une réponse NosDéputés (`{"depute": {...}}`) doublée
    sur `fetch_identity` ; elle vient du référentiel AN depuis #529, doublée
    sur `fetch_identite_officielle_par_slug`. C'est le seul changement : ce que
    le test éprouve — `votes_source` — n'a pas bougé.
    """
    identite_an = {
        "nom_complet": "Jean Dupont",
        "mandat_debut": "2022-06-22",
        "mandat_fin": None,
        "groupe_sigle": "RE",
        "groupe_nom": "Renaissance",
    }
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=(identite_an, "PA123456")),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=(votes, legislatures)),
    ):
        return build_profile("deputes", "jean-dupont", skip_interventions=True)


def test_votes_source_enumere_toutes_les_legislatures_couvertes():
    """`votes_source` doit refléter l'ensemble des législatures agrégées :
    afficher « législature 16 » au singulier alors que trois sont couvertes
    rendrait la limite du jeu de données illisible (AGENTS.md §2.8)."""
    votes = [
        {"numero": "1", "date": "2024-10-01", "titre": "T17", "sort": None, "legislature": "17", "position": "pour"},
        {"numero": "1", "date": "2023-01-01", "titre": "T16", "sort": None, "legislature": "16", "position": "contre"},
    ]
    profile = _build_profile_avec_votes(votes, ["16", "17"])

    assert "législatures 16, 17" in profile["votes_source"]
    assert len(profile["votes"]) == 2


def test_votes_source_reste_au_singulier_pour_une_seule_legislature():
    votes = [
        {"numero": "1", "date": "2023-01-01", "titre": "T16", "sort": None, "legislature": "16", "position": "pour"}
    ]
    profile = _build_profile_avec_votes(votes, ["16"])

    assert "législature 16)" in profile["votes_source"]
    assert "législatures" not in profile["votes_source"]


def test_chaque_vote_porte_sa_source_primaire():
    """Règle 2 (traçabilité) : la page du scrutin dépendant de la législature,
    elle est portée par le vote lui-même et non déduite de `votes_source`, qui
    en couvre désormais plusieurs."""
    votes = [
        {"numero": "1000", "date": "2025-03-13", "titre": "T", "sort": None, "legislature": "17", "position": "pour"}
    ]
    profile = _build_profile_avec_votes(votes, ["17"])

    assert profile["votes"][0]["url_source"] == "https://www.assemblee-nationale.fr/dyn/17/scrutins/1000"
    assert profile["votes"][0]["legislature"] == "17"
