"""
tests/test_parltrack_dumps.py — Tests unitaires pour parltrack_dumps.py.

Ces tests utilisent des données fictives compressées en mémoire pour éviter
tout accès réseau ou lecture de fichiers réels.

## Ce que cette suite a laissé passer pendant un an (#683)

Elle était verte, et le module n'avait **jamais lu une seule ligne** des dumps
publiés. Toutes les fixtures étaient écrites en NDJSON — un objet complet par
ligne — c'est-à-dire dans le format que le code imaginait. ParlTrack publie un
tableau JSON dont le séparateur ouvre la ligne (``[{…}`` puis ``,{…}`` puis
``]``), et sur ce format-là le module rendait zéro enregistrement.

« Une fixture qui décrit le monde tel que le code l'imagine ne peut pas révéler
que le monde a bougé » (#726). `_octets_dump` écrit donc désormais le format
**publié**, et c'est lui qui alimente tous les tests du fichier.
"""

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import zstandard as zstd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from parltrack_dumps import (
    DumpParltrackIllisible,
    TYPES_ACTIVITE,
    VERSION_SCHEMA_INDEX,
    _resolve_mepref_as_int,
    build_activities_index,
    build_amendments_index,
    build_dossiers_index,
    build_votes_index,
    definir_perimetre_meps,
    get_amendments_for_mep,
    get_dossiers_for_mep,
    iter_dump_zst,
)


@pytest.fixture(autouse=True)
def _perimetre_neutre():
    """Le périmètre est un état de module : un test qui le pose le rendrait aux suivants."""
    definir_perimetre_meps(None)
    yield
    definir_perimetre_meps(None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _octets_dump(records: list[dict]) -> bytes:
    """Compresse des enregistrements **au format publié par ParlTrack**.

    Un seul tableau JSON, un objet par ligne, le séparateur en tête :

        [{"…": 1}
        ,{"…": 2}
        ]

    C'est cette fonction, et elle seule, qui empêche la suite de repasser verte
    sur un format que la source n'utilise pas.
    """
    if not records:
        corps = "[]"
    else:
        lignes = [json.dumps(r, ensure_ascii=False) for r in records]
        corps = "[" + lignes[0] + "\n" + "".join(f",{l}\n" for l in lignes[1:]) + "]"
    cctx = zstd.ZstdCompressor()
    return cctx.compress((corps + "\n").encode("utf-8"))


# Alias historique : les tests écrits avant #683 l'appellent encore.
_make_zst_bytes = _octets_dump


def _write_zst_file(path: Path, records: list[dict]) -> None:
    """Écrit un dump .zst fictif sur disque, au format publié."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_octets_dump(records))


# ---------------------------------------------------------------------------
# Tests : iter_dump_zst
# ---------------------------------------------------------------------------


def test_iter_dump_zst_basic(tmp_path):
    """Lecture streaming d'un fichier .zst minimal."""
    records = [{"a": 1}, {"b": 2}]
    p = tmp_path / "test.json.zst"
    _write_zst_file(p, records)
    result = list(iter_dump_zst(p))
    assert result == records


def _compresser(texte: str) -> bytes:
    return zstd.ZstdCompressor().compress(texte.encode("utf-8"))


def test_iter_dump_zst_lignes_vides(tmp_path):
    """Une ligne vide ne porte pas de séparateur : elle est sautée, pas terminale."""
    p = tmp_path / "test.json.zst"
    p.write_bytes(_compresser('[{"x": 1}\n\n,{"y": 2}\n]\n'))
    assert list(iter_dump_zst(p)) == [{"x": 1}, {"y": 2}]


def test_iter_dump_zst_ligne_illisible_sautee(tmp_path):
    """Une ligne tronquée ne doit pas perdre le reste du dump."""
    p = tmp_path / "test.json.zst"
    p.write_bytes(_compresser('[{"ok": true}\n,PAS_DU_JSON\n,{"ok2": true}\n]\n'))
    assert list(iter_dump_zst(p)) == [{"ok": True}, {"ok2": True}]


def test_iter_dump_zst_dump_vide(tmp_path):
    """« [] » est un dump légitimement vide, pas une panne."""
    p = tmp_path / "test.json.zst"
    p.write_bytes(_compresser("[]\n"))
    lignes = [0]
    assert list(iter_dump_zst(p, lignes)) == []
    assert lignes[0] == 0, "un dump vide ne porte aucune ligne d'enregistrement"


def test_iter_dump_zst_refuse_le_ndjson(tmp_path):
    """LE test qui manquait (#683).

    Le NDJSON — un objet complet par ligne, sans séparateur de tête — est le
    format que le module a supposé pendant un an. Sur ce format, le lecteur
    perd le premier caractère de chaque ligne et ne rend donc rien. Ce test
    fige le sens de la lecture : c'est le tableau JSON qui est lu, pas le
    NDJSON, et l'inverse n'est pas silencieusement toléré.
    """
    p = tmp_path / "test.json.zst"
    p.write_bytes(_compresser('{"a": 1}\n{"b": 2}\n'))
    assert list(iter_dump_zst(p)) == []


def test_un_dump_illisible_leve_au_lieu_de_rendre_vide(tmp_path):
    """La garde de #683 : un dump plein qu'on ne sait plus lire est une PANNE.

    C'est ce qui manquait le plus. Sans elle, un changement de format côté
    ParlTrack rend un index vide, l'index vide rend des listes vides, et les
    listes vides se publient comme des constats sur les personnes (#484, #510).
    """
    dump = tmp_path / "ep_dossiers.json.zst"
    dump.write_bytes(_compresser('{"procedure": {"reference": "x"}}\n'))

    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        with pytest.raises(DumpParltrackIllisible):
            build_dossiers_index(force_download=False)


# ---------------------------------------------------------------------------
# Tests : _resolve_mepref_as_int
# ---------------------------------------------------------------------------


def test_resolve_mepref_int():
    assert _resolve_mepref_as_int(131580) == 131580


def test_resolve_mepref_str_int():
    assert _resolve_mepref_as_int("131580") == 131580


def test_resolve_mepref_hash_returns_none():
    """Un hash hexadécimal historique de 24 caractères retourne None."""
    assert _resolve_mepref_as_int("5479da7eb01f9fc4c71bb6a1") is None


def test_resolve_mepref_none():
    assert _resolve_mepref_as_int(None) is None


def test_resolve_mepref_garbage():
    assert _resolve_mepref_as_int("not_a_number") is None


# ---------------------------------------------------------------------------
# Tests : build_dossiers_index
# ---------------------------------------------------------------------------


def _dossier_record(reference: str, mepref: int, titre: str = "Titre test") -> dict:
    return {
        "procedure": {"reference": reference, "title": titre},
        "committees": [
            {
                "committee": "AFET",
                "rapporteur": [{"mepref": mepref, "date": "2024-03-15"}],
            }
        ],
        "meta": {"source": f"https://parltrack.org/dossier/{reference}"},
    }


def test_build_dossiers_index_known_meps(tmp_path):
    """L'index rapporteur contient les 3 MEP IDs tests."""
    records = [
        _dossier_record("2024/0001(COD)", 131580, "Dossier Bardella"),
        _dossier_record("2020/0001(INI)", 28210, "Dossier Le Pen"),
        _dossier_record("2020/0002(INI)", 96742, "Dossier Mélenchon"),
    ]
    zst_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(zst_path, records)

    with patch("parltrack_dumps.ensure_dump", return_value=zst_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_dossiers_index(force_download=False)

    assert 131580 in index
    assert 28210 in index
    assert 96742 in index
    assert index[131580][0]["role"] == "rapporteur"
    assert index[131580][0]["reference"] == "2024/0001(COD)"


def test_build_dossiers_index_hash_mepref_ignored(tmp_path):
    """Un mepref hash est ignoré sans lever d'exception, pas ajouté à l'index."""
    records = [
        {
            "procedure": {"reference": "2014/0802(NLE)", "title": "Ancien dossier"},
            "committees": [
                {
                    "committee": "AFET",
                    "rapporteur": [{"mepref": "5479da7eb01f9fc4c71bb6a1", "date": "2014-01-01"}],
                }
            ],
            "meta": {"source": "https://parltrack.org/dossier/2014/0802(NLE)"},
        }
    ]
    zst_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(zst_path, records)

    with patch("parltrack_dumps.ensure_dump", return_value=zst_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_dossiers_index(force_download=False)

    assert len(index) == 0


def test_build_dossiers_index_cache_used(tmp_path):
    """L'index JSON sur disque est utilisé si plus récent que le dump."""
    import time as _time

    cached = {
        "131580": [{"reference": "from_cache", "titre": "Cached", "role": "rapporteur",
                    "comite": "AFET", "date": "2024-01-01",
                    "source_url": "https://parltrack.org/dossier/from_cache"}]
    }
    # Le nom porte la VERSION du schéma d'entrée : un cache écrit par la
    # version précédente doit être ignoré, pas relu avec un champ en moins
    # (#901). Le composer ici plutôt que de l'écrire en dur fait échouer ce
    # test si l'empreinte cesse de porter la version.
    index_path = tmp_path / f"index_dossiers_rapporteur-v{VERSION_SCHEMA_INDEX}-tous.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(cached), encoding="utf-8")

    # Créer un dump fictif plus ancien
    dump_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(dump_path, [])
    # S'assurer que le dump est plus ancien que le cache
    import os
    old_time = _time.time() - 100
    os.utime(dump_path, (old_time, old_time))

    with patch("parltrack_dumps.ensure_dump", return_value=dump_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_dossiers_index(force_download=False)

    assert 131580 in index
    assert index[131580][0]["reference"] == "from_cache"


def test_un_cache_de_schema_anterieur_est_ignore(tmp_path):
    """Le cas que l'empreinte de périmètre ne couvrait pas (#901).

    Quand une entrée d'index gagne un champ, un cache écrit avant reste
    lisible : il se relit sans erreur et rend le nouveau champ absent partout.
    Un `stade_source` manquant se lirait alors comme « la source ne publie pas
    de stade » — le contraire de ce que la source publie sur 85,6 % des
    dossiers. Le cache doit RATER, pas mentir (#510).
    """
    import os
    import time as _time

    ancien = tmp_path / "index_dossiers_rapporteur-tous.json"
    ancien.write_text(json.dumps({"131580": [{"reference": "schema_v1"}]}), encoding="utf-8")

    dump_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(dump_path, [])
    vieux = _time.time() - 100
    os.utime(dump_path, (vieux, vieux))

    with patch("parltrack_dumps.ensure_dump", return_value=dump_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_dossiers_index(force_download=False)

    assert 131580 not in index, (
        "un cache d'un schéma antérieur a été relu : le nom de fichier ne porte "
        "plus la version, et un champ ajouté ressortirait absent partout.")


# ---------------------------------------------------------------------------
# Tests : build_amendments_index
# ---------------------------------------------------------------------------


def _plenary_amd_record(amd_id: str, reference: str, mep_id: int) -> dict:
    return {
        "id": amd_id,
        "reference": reference,
        "date": "2023-05-10",
        "meps": [mep_id],
        "meta": {"source": f"https://parltrack.org/amendments/{amd_id}"},
    }


def _committee_amd_record(amd_id: str, reference: str, mep_id: int) -> dict:
    return {
        "id": amd_id,
        "reference": reference,
        "committee": ["AFET"],
        "date": "2023-06-01",
        "meps": [mep_id],
        "meta": {"source": f"https://parltrack.org/amendments/{amd_id}"},
    }


def test_build_amendments_index_bardella(tmp_path):
    """Jordan Bardella (131580) : amendements plénière + comité."""
    plenary = [
        _plenary_amd_record(f"A9-0052/2023-{i}", "2020/2202(INI)", 131580)
        for i in range(15)
    ]
    committee = [
        _committee_amd_record(f"PE529.899-{i}", "2014/2021(INI)", 131580)
        for i in range(510)
    ]

    plenary_path = tmp_path / "ep_plenary_amendments.json.zst"
    committee_path = tmp_path / "ep_amendments.json.zst"
    _write_zst_file(plenary_path, plenary)
    _write_zst_file(committee_path, committee)

    with patch("parltrack_dumps.ensure_dump") as mock_ensure, \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        def _side(name, force_download=False):
            if "plenary" in name:
                return plenary_path
            return committee_path
        mock_ensure.side_effect = _side
        index = build_amendments_index(force_download=True)

    assert 131580 in index
    assert len(index[131580]) == 15 + 510


def test_build_amendments_index_multiple_meps(tmp_path):
    """Marine Le Pen (28210) et Mélenchon (96742) ont aussi des amendements."""
    plenary = [_plenary_amd_record("AMD-1", "2020/2202(INI)", 28210)]
    committee = [
        _committee_amd_record(f"PE001-{i}", "2014/2021(INI)", 96742)
        for i in range(154)
    ]

    plenary_path = tmp_path / "ep_plenary_amendments.json.zst"
    committee_path = tmp_path / "ep_amendments.json.zst"
    _write_zst_file(plenary_path, plenary)
    _write_zst_file(committee_path, committee)

    with patch("parltrack_dumps.ensure_dump") as mock_ensure, \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        def _side(name, force_download=False):
            if "plenary" in name:
                return plenary_path
            return committee_path
        mock_ensure.side_effect = _side
        index = build_amendments_index(force_download=True)

    assert 28210 in index
    assert len(index[28210]) == 1
    assert 96742 in index
    assert len(index[96742]) == 154


def test_build_amendments_index_missing_dump_returns_empty(tmp_path):
    """Si un dump est indisponible (None), retourne dict vide sans exception."""
    with patch("parltrack_dumps.ensure_dump", return_value=None), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_amendments_index(force_download=False)
    assert index == {}


# ---------------------------------------------------------------------------
# Tests : get_dossiers_for_mep / get_amendments_for_mep (API publique)
# ---------------------------------------------------------------------------


def test_get_dossiers_for_mep_unknown_returns_empty(tmp_path):
    """Un MEP ID inconnu retourne une liste vide."""
    records = [_dossier_record("2024/0001(COD)", 131580, "Dossier")]
    zst_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(zst_path, records)

    with patch("parltrack_dumps.ensure_dump", return_value=zst_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        result = get_dossiers_for_mep(99999, force_download=False)

    assert result == []


def test_get_amendments_for_mep_known(tmp_path):
    """get_amendments_for_mep retourne les amendements du MEP."""
    plenary = [_plenary_amd_record("A9-0001", "2020/0001(INI)", 28210)]
    committee = []

    plenary_path = tmp_path / "ep_plenary_amendments.json.zst"
    committee_path = tmp_path / "ep_amendments.json.zst"
    _write_zst_file(plenary_path, plenary)
    _write_zst_file(committee_path, committee)

    with patch("parltrack_dumps.ensure_dump") as mock_ensure, \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        def _side(name, force_download=False):
            if "plenary" in name:
                return plenary_path
            return committee_path
        mock_ensure.side_effect = _side
        result = get_amendments_for_mep(28210, force_download=True)

    assert len(result) == 1
    assert result[0]["id"] == "A9-0001"


# ---------------------------------------------------------------------------
# Tests : le périmètre d'indexation (#683)
# ---------------------------------------------------------------------------


def test_lindex_ne_retient_que_le_perimetre(tmp_path):
    """Indexer tout le Parlement européen coûte 2 675 293 entrées, ~0,5 Go.

    Le défaut d'origine ne s'en apercevait pas : l'index sortait vide, donc
    gratuit. Réparer la lecture sans borner le périmètre aurait écrit ce
    demi-giga dans `.cache/parltrack/`, mis en cache et téléversé à chaque run.
    """
    records = [
        _dossier_record("2024/0001(COD)", 131580),
        _dossier_record("2020/0001(INI)", 28210),
    ]
    zst_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(zst_path, records)

    with patch("parltrack_dumps.ensure_dump", return_value=zst_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_dossiers_index(perimetre=frozenset({131580}))

    assert set(index) == {131580}


def test_le_nom_de_lindex_porte_lempreinte_du_perimetre(tmp_path):
    """Un index construit pour 1 personne et relu pour 7 rendrait 6 listes vides.

    Et six listes vides se lisent comme six constats (#510). L'empreinte fait
    donc rater le cache au lieu de le laisser mentir — même geste qu'au #505.
    """
    zst_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(zst_path, [_dossier_record("2024/0001(COD)", 131580)])

    with patch("parltrack_dumps.ensure_dump", return_value=zst_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        build_dossiers_index(perimetre=frozenset({131580}))
        build_dossiers_index(perimetre=frozenset({131580, 28210}))

    ecrits = sorted(p.name for p in tmp_path.glob("index_dossiers_rapporteur-*.json"))
    assert len(ecrits) == 2, f"deux périmètres, deux fichiers d'index : {ecrits}"


def test_le_perimetre_de_module_sert_de_defaut(tmp_path):
    """`definir_perimetre_meps` évite une relecture du dump par personne."""
    zst_path = tmp_path / "ep_dossiers.json.zst"
    _write_zst_file(zst_path, [
        _dossier_record("2024/0001(COD)", 131580),
        _dossier_record("2020/0001(INI)", 28210),
    ])
    definir_perimetre_meps([131580, 28210])

    with patch("parltrack_dumps.ensure_dump", return_value=zst_path), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        assert set(get_dossiers_for_mep(131580)[0]) >= {"reference", "role"}
        index = build_dossiers_index()

    assert set(index) == {131580, 28210}


# ---------------------------------------------------------------------------
# Tests : les scrutins nominatifs (#683)
# ---------------------------------------------------------------------------


def _scrutin(voteid: int, pour: list[int], contre: list[int] = (), abstention: list[int] = ()):
    def bloc(ids):
        return {"total": len(ids), "groups": {"ID": [{"mepid": i} for i in ids]}}
    positions = {}
    if pour:
        positions["+"] = bloc(pour)
    if contre:
        positions["-"] = bloc(contre)
    if abstention:
        positions["0"] = bloc(abstention)
    return {
        "voteid": voteid,
        "ts": "2023-06-07T11:40:25",
        "title": "Résolution sur le sujet",
        "url": "https://www.europarl.europa.eu/…/RCV.xml",
        "epref": "A9-0183/2023",
        "votes": positions,
    }


def test_les_positions_sont_celles_du_schema(tmp_path):
    """`+`/`-`/`0` sont traduits dans le vocabulaire déjà fermé du pivot."""
    dump = tmp_path / "ep_votes.json.zst"
    _write_zst_file(dump, [
        _scrutin(1, pour=[131580]),
        _scrutin(2, pour=[], contre=[131580]),
        _scrutin(3, pour=[], abstention=[131580]),
    ])
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_votes_index(perimetre=frozenset({131580}))

    assert [v["position"] for v in index[131580]] == ["pour", "contre", "abstention"]
    assert index[131580][0]["date"] == "2023-06-07"
    assert index[131580][0]["source_url"].startswith("https://www.europarl.europa.eu/")


def test_un_scrutin_sans_detail_nominatif_nest_pas_une_absence(tmp_path):
    """92 scrutins sur 44 648 n'ont pas de détail publié.

    Ils sont comptés et sautés. Les publier comme « n'a pas voté » inventerait
    un fait que la source ne porte pas (§2 règle 5), et l'assiduité
    individuelle ne se publie jamais (§2 règle 3).
    """
    dump = tmp_path / "ep_votes.json.zst"
    _write_zst_file(dump, [
        {"voteid": 9, "ts": "2020-01-01T00:00:00", "title": "Sans détail", "url": "u"},
        _scrutin(10, pour=[131580]),
    ])
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_votes_index(perimetre=frozenset({131580}))

    assert len(index[131580]) == 1
    assert index[131580][0]["scrutin_id"] == 10


# ---------------------------------------------------------------------------
# Tests : les activités (#683)
# ---------------------------------------------------------------------------


def test_les_activites_sont_groupees_par_type(tmp_path):
    dump = tmp_path / "ep_mep_activities.json.zst"
    _write_zst_file(dump, [{
        "mep_id": 131580,
        "CRE": [{
            "date": "2024-07-17T00:00:00",
            "title": "The need for the EU's continuous support for Ukraine (debate)",
            "reference": "P10_CRE-REV(2024)07-17(2-020-0000)",
            "url": "https://www.europarl.europa.eu/doceo/document/CRE-10-2024-07-17-INT-2-020-0000_FR.html",
            "term": 10,
        }],
        "WEXP": [{"date": "2024-07-17T00:00:00", "title": "…", "text": "Derrière l'objectif louable…"}],
    }])
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_activities_index(perimetre=frozenset({131580}))

    assert set(index[131580]) == {"intervention_seance", "explication_de_vote_ecrite"}
    intervention = index[131580]["intervention_seance"][0]
    assert intervention["date"] == "2024-07-17"
    assert intervention["legislature"] == 10
    assert intervention["source_url"].startswith("https://www.europarl.europa.eu/doceo/")
    # Seule l'explication de vote porte les mots de la personne.
    assert intervention["texte"] is None
    assert index[131580]["explication_de_vote_ecrite"][0]["texte"].startswith("Derrière")


def test_un_code_dactivite_inconnu_est_ignore_pas_range_ailleurs(tmp_path):
    """`TYPES_ACTIVITE` est fermé, comme les `KNOWN_*` du schéma (§4).

    Ranger un code inconnu sous une étiquette approchante publierait une
    qualification que personne n'a établie.
    """
    dump = tmp_path / "ep_mep_activities.json.zst"
    _write_zst_file(dump, [{
        "mep_id": 131580,
        "CRE": [{"date": "2024-07-17T00:00:00", "title": "Débat"}],
        "CODE_QUI_NEXISTE_PAS": [{"date": "2024-07-17T00:00:00", "title": "?"}],
    }])
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_activities_index(perimetre=frozenset({131580}))

    assert set(index[131580]) == {"intervention_seance"}
    assert "CODE_QUI_NEXISTE_PAS" not in TYPES_ACTIVITE


# ---------------------------------------------------------------------------
# Le job et le module disent la même chose (#683)
# ---------------------------------------------------------------------------


def test_le_workflow_telecharge_exactement_les_dumps_que_le_module_lit():
    """Une seule définition de la liste, et le YAML la lit au lieu de la recopier.

    Recopiée, elle aurait divergé du jour où le module lit un dump de plus : le
    fichier manquant ne fait pas échouer la lecture, il rend un index vide, et
    un index vide se publie comme un constat sur les personnes (#510).
    """
    from parltrack_dumps import DUMPS_LUS

    workflow = (
        Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"
    ).read_text(encoding="utf-8")
    assert "from parltrack_dumps import ensure_dump, DUMPS_LUS" in workflow
    assert "for dump in DUMPS_LUS:" in workflow
    assert len(DUMPS_LUS) == len(set(DUMPS_LUS)) == 5
    assert "ep_votes.json.zst" in DUMPS_LUS
    assert "ep_mep_activities.json.zst" in DUMPS_LUS
