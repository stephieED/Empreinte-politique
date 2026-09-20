"""#901 — l'index des scrutins européens, et ce qu'il refuse de déduire.

Les 11 013 votes européens portaient déjà de quoi s'afficher : titre, nature,
référence de dossier, date, numéro, URL du procès-verbal — dans
`scrutin_non_resolu`, renseignés à 100 % sauf la référence (96 %).

Ce qu'aucun profil ne peut porter, c'est le scrutin vu d'ensemble : les
effectifs pour / contre / abstention, ventilés par groupe politique. La source
les publie sur 44 556 des 44 648 scrutins. C'est ce que cet index ajoute, et
rien d'autre.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from scrutins_europeens import (  # noqa: E402
    POSITIONS,
    SCHEMA_VERSION,
    DumpVotesIndisponible,
    _repartition,
    construire,
    document,
    identifiant,
    numeros_cites,
)


def _scrutin(voteid, votes=None, **extra):
    base = {"voteid": voteid, "ts": "2018-04-18T13:08:47", "title": "Un texte",
            "url": "https://www.europarl.europa.eu/pv", "epref": ["2017/2184(DEC)"],
            "doc": "A8-0075/2018"}
    base.update(extra)
    if votes is not None:
        base["votes"] = votes
    return base


def _profil(*numeros):
    return {"votes": [
        {"scrutin_id": None, "position": "pour",
         "scrutin_non_resolu": {"institution": "parlement_europeen", "numero_scrutin": n}}
        for n in numeros
    ]}


# --------------------------------------------------------------------------
# L'identifiant
# --------------------------------------------------------------------------

def test_l_identifiant_porte_l_institution_et_le_numero_de_la_source():
    assert identifiant(7649) == "pe:7649"


def test_les_deux_formes_de_voteid_sont_reprises_telles_quelles():
    """4 855 entiers et 716 chaînes composites sur les 5 571 cités.

    Normaliser la seconde produirait une clé que la source ne connaît pas ; la
    jointure depuis un profil se fait sur `numero_scrutin`, repris à l'identique.
    """
    assert identifiant("2017-06-01 00:00:00-1.") == "pe:2017-06-01 00:00:00-1."


def test_deux_scrutins_ne_partagent_jamais_un_identifiant(tmp_path):
    """Une collision en écraserait un en silence."""
    entrees = construire([7649, "2017-06-01 00:00:00-1."],
                         dump_path=_dump(tmp_path, [_scrutin(7649),
                                                    _scrutin("2017-06-01 00:00:00-1.")]))

    ids = [e["id"] for e in entrees]
    assert len(set(ids)) == len(ids) == 2


# --------------------------------------------------------------------------
# La répartition
# --------------------------------------------------------------------------

def test_les_trois_positions_de_la_source_sont_nommees():
    assert POSITIONS == {"+": "pour", "-": "contre", "0": "abstention"}


def test_les_effectifs_par_groupe_sont_recomptes_sur_la_liste_nominative():
    """La source publie un total ET une liste ; seule la liste garantit que le
    chiffre correspond aux personnes rangées sous ce groupe."""
    votes = {"+": {"total": 3, "groups": {"PPE": [{"mepid": 1}, {"mepid": 2}]}},
             "-": {"total": 1, "groups": {"ECR": [{"mepid": 3}]}}}

    totaux, par_groupe = _repartition(votes)

    assert totaux == {"pour": 3, "contre": 1}
    assert par_groupe == {"PPE": {"pour": 2}, "ECR": {"contre": 1}}


def test_une_position_absente_de_la_source_ne_vaut_pas_zero():
    """« La source n'a pas publié ce décompte » et « personne n'a voté ainsi »
    ne sont pas la même chose (§2 règle 5)."""
    totaux, _ = _repartition({"+": {"total": 12, "groups": {}}})

    assert totaux == {"pour": 12}
    assert "contre" not in totaux and "abstention" not in totaux


def test_un_code_de_position_inconnu_n_est_pas_range_dans_les_trois():
    totaux, par_groupe = _repartition({"?": {"total": 5, "groups": {"PPE": [{"mepid": 1}]}}})

    assert totaux == {} and par_groupe == {}


def test_le_sort_n_est_jamais_deduit_des_totaux(tmp_path):
    """Conclure « adopté » de pour > contre serait une inférence : le Parlement
    vote aussi à la majorité qualifiée, et le dump ne dit pas quelle règle
    s'appliquait. Un sort déduit aurait l'air d'un fait sourcé sans en être un.
    """
    votes = {"+": {"total": 400, "groups": {}}, "-": {"total": 10, "groups": {}}}
    entrees = construire([7649], dump_path=_dump(tmp_path, [_scrutin(7649, votes)]))

    assert "sort" not in entrees[0]
    assert entrees[0]["totaux"] == {"pour": 400, "contre": 10}


# --------------------------------------------------------------------------
# Le périmètre et la forme
# --------------------------------------------------------------------------

def _dump(tmp_path, scrutins):
    """Un dump `.zst` au format ParlTrack : un tableau JSON, séparateur en tête."""
    import zstandard as zstd
    chemin = tmp_path / "ep_votes.json.zst"
    lignes = []
    for rang, scrutin in enumerate(scrutins):
        lignes.append(("[" if rang == 0 else ",") + json.dumps(scrutin, ensure_ascii=False))
    lignes.append("]")
    brut = "\n".join(lignes).encode("utf-8")
    chemin.write_bytes(zstd.ZstdCompressor().compress(brut))
    return chemin


def test_seuls_les_scrutins_cites_entrent_dans_l_index(tmp_path):
    """Indexer les 44 648 du dump pour en servir 5 571 ferait porter au dépôt
    huit fois le poids utile. Même choix que `scrutins.json` côté Assemblée."""
    chemin = _dump(tmp_path, [_scrutin(1), _scrutin(2), _scrutin(3)])

    entrees = construire([2], dump_path=chemin)

    assert [e["numero_scrutin"] for e in entrees] == [2]


def test_un_cite_absent_du_dump_ne_produit_aucune_entree(tmp_path):
    """Ni fabriqué, ni comblé : l'appelant le compte et le dit (§2 règle 5)."""
    entrees = construire([999], dump_path=_dump(tmp_path, [_scrutin(1)]))

    assert entrees == []


def test_sans_citation_l_index_est_vide_sans_lire_le_dump():
    assert construire([]) == []


def test_un_dump_indisponible_leve_au_lieu_de_rendre_un_index_vide(monkeypatch):
    """Un index vide se lirait comme « aucun scrutin européen » — la confusion
    que #510 a payée, et que `DumpParltrackIllisible` a déjà réglée en amont."""
    import scrutins_europeens

    monkeypatch.setattr(scrutins_europeens, "ensure_dump", lambda *a, **k: None)

    with pytest.raises(DumpVotesIndisponible):
        scrutins_europeens.construire([7649])


def test_les_profils_non_europeens_ne_sont_pas_comptes(tmp_path):
    (tmp_path / "x.pivot.json").write_text(json.dumps({"votes": [
        {"scrutin_id": "an:17:1"},
        {"scrutin_non_resolu": {"institution": "assemblee_nationale", "numero_scrutin": 5}},
    ]}), encoding="utf-8")

    assert numeros_cites(tmp_path) == set()


def test_les_numeros_cites_sont_lus_dans_scrutin_non_resolu(tmp_path):
    (tmp_path / "a.pivot.json").write_text(json.dumps(_profil(7649, 7650)), encoding="utf-8")
    (tmp_path / "b.pivot.json").write_text(json.dumps(_profil(7649)), encoding="utf-8")

    assert numeros_cites(tmp_path) == {7649, 7650}


def test_l_entete_nomme_le_schema_et_la_licence_de_parltrack():
    """`licence_donnees` vient de `licences.py`, jamais écrit en dur (#909)."""
    entete = document([])

    assert entete["schema_version"] == SCHEMA_VERSION
    assert "ODbL" in entete["licence_donnees"]
    assert "ParlTrack" in entete["licence_donnees"]
    assert entete["scrutins"] == []


def test_l_ordre_est_stable_malgre_les_deux_formes_de_voteid(tmp_path):
    """Comparer un entier et une chaîne lève ; et un ordre instable ferait
    bouger l'index sans que rien n'ait bougé."""
    chemin = _dump(tmp_path, [
        _scrutin("2018-04-18 00:00:00-2.", ts="2018-04-18T13:00:00"),
        _scrutin(7649, ts="2016-01-01T10:00:00"),
        _scrutin("2018-04-18 00:00:00-1.", ts="2018-04-18T13:00:00"),
    ])

    entrees = construire([7649, "2018-04-18 00:00:00-1.", "2018-04-18 00:00:00-2."],
                         dump_path=chemin)

    assert [e["date"] for e in entrees] == ["2016-01-01", "2018-04-18", "2018-04-18"]
    assert entrees[1]["numero_scrutin"] == "2018-04-18 00:00:00-1."
