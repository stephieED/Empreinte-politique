"""Le rattachement d'un scrutin à son dossier se lit dans la source, ou n'existe pas (#758).

Un scrutin de l'Assemblée ne nomme pas le texte qu'il tranche :
`objet.referenceLegislative` et `demandeur.referenceLegislative` sont nuls sur
0/18 311 scrutins bruts des législatures 14 à 17. Le lien n'existe qu'en sens
inverse, dans `actesLegislatifs[].voteRefs` du dossier.

Ce que ces garde-fous protègent tient en une phrase : **on lit ce lien, on ne
le devine jamais**. La tentation est réelle — un scrutin porte le titre du
texte, et un dossier aussi ; les rapprocher par ressemblance de libellé est
exactement la classification que `regrouper-nest-pas-joindre-639` interdit, et
elle donnerait un rattachement plausible et faux.

Mesuré au 07/09/2026 sur les trois archives : **715 scrutins rattachés à 561
dossiers**, soit 423 des 697 textes en dernière lecture (61 %), dont 412 avec
une commission saisie au fond. Les 39 % restants sont une absence déclarée.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import scrutins_dossiers_an as sd  # noqa: E402
from scrutins_index import cle_scrutin  # noqa: E402


def _dossier(uid: str, actes: object) -> dict:
    return {"uid": uid, "actesLegislatifs": actes}


@pytest.fixture(autouse=True)
def _memo_propre():
    sd.vider_memo()
    yield
    sd.vider_memo()


# ---------------------------------------------------------------------------
# 1. La clé produite est celle des scrutins publiés, ou rien
# ---------------------------------------------------------------------------

def test_la_cle_est_exactement_celle_de_l_index_des_scrutins():
    """Une clé qui diverge d'un caractère ne joint rien, en silence."""
    assert sd.cle_depuis_uid("VTANR5L17V960") == cle_scrutin("17", "960")
    assert sd.cle_depuis_uid("VTANR5L14V1") == cle_scrutin("14", "1")


@pytest.mark.parametrize(
    "uid",
    [
        "VTCGR5L16V12",   # Congrès : partage l'espace de numérotation, exclu de la collecte
        "VTANR5L17",      # tronqué
        "DLR5L17N51481",  # un dossier n'est pas un scrutin
        "",
        None,
        1760,
    ],
)
def test_un_uid_qui_n_est_pas_un_scrutin_an_ne_produit_aucune_cle(uid):
    """Fabriquer une clé sur un uid étranger rattacherait un vote qui n'existe pas."""
    assert sd.cle_depuis_uid(uid) is None


# ---------------------------------------------------------------------------
# 2. L'arbre est irrégulier : la lecture doit l'être aussi
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "actes",
    [
        {"acte": {"voteRefs": "VTANR5L17V960"}},
        {"acte": {"voteRefs": ["VTANR5L17V960"]}},
        {"acte": {"voteRefs": {"voteRef": "VTANR5L17V960"}}},
        {"acte": {"voteRefs": {"voteRef": ["VTANR5L17V960"]}}},
        [{"voteRefs": "VTANR5L17V960"}],
        {"a": {"b": {"c": {"voteRefs": "VTANR5L17V960"}}}},
    ],
)
def test_le_vote_ref_est_trouve_quelle_que_soit_la_forme(monkeypatch, actes):
    """`actesLegislatifs` est irrégulier — objet ou liste, à toute profondeur.

    Suivre un chemin fixe ferait perdre des rattachements sans rien signaler.
    """
    monkeypatch.setattr(sd, "iter_dossiers_bruts", lambda a: [(17, _dossier("D1", actes))])
    monkeypatch.setattr(sd, "_determine_statut", lambda uid, actes: ("adopte", False, None))
    table = sd.construire_table([])
    assert table["scrutins"] == {"an:17:960": "D1"}


# ---------------------------------------------------------------------------
# 3. Rien n'est deviné
# ---------------------------------------------------------------------------

def test_un_dossier_sans_vote_ref_n_a_aucune_entree(monkeypatch):
    """Le titre du dossier ressemble à celui du scrutin — et ne suffit pas.

    Rapprocher par le libellé serait la jointure par ressemblance que #639
    interdit : elle donnerait un rattachement plausible et faux.
    """
    dossier = _dossier("D1", {"acte": {"libelle": "Projet de loi de finances pour 2023"}})
    monkeypatch.setattr(sd, "iter_dossiers_bruts", lambda a: [(17, dossier)])
    table = sd.construire_table([])
    assert table["scrutins"] == {}
    assert table["dossiers"] == {}


def test_un_dossier_sans_uid_est_ignore(monkeypatch):
    monkeypatch.setattr(
        sd, "iter_dossiers_bruts",
        lambda a: [(17, {"actesLegislatifs": {"acte": {"voteRefs": "VTANR5L17V960"}}})],
    )
    assert sd.construire_table([])["scrutins"] == {}


# ---------------------------------------------------------------------------
# 4. Une issue non résolue reste une absence, jamais un défaut
# ---------------------------------------------------------------------------

def test_un_statut_non_resolu_garde_son_entree_et_reste_nul(monkeypatch):
    """Le rattachement est un fait même quand l'issue ne l'est pas.

    `statut: null` se lit comme une absence — jamais comme « en navette », qui
    est un état réel et sourcé (§2 règle 5).
    """
    monkeypatch.setattr(
        sd, "iter_dossiers_bruts",
        lambda a: [(17, _dossier("D1", {"acte": {"voteRefs": "VTANR5L17V960"}}))],
    )
    monkeypatch.setattr(sd, "_determine_statut", lambda uid, actes: (None, None, "code inconnu"))
    table = sd.construire_table([])
    assert table["scrutins"] == {"an:17:960": "D1"}
    assert table["dossiers"]["D1"] == {"statut": None, "sort_49_3": None}


# ---------------------------------------------------------------------------
# 5. Une absence de source ne supprime jamais ce qui est publié
# ---------------------------------------------------------------------------

def test_sans_archives_la_table_est_vide_et_non_une_exception(monkeypatch, tmp_path):
    """L'appelant en fait une absence comptée, pas une suppression (§3a, #465)."""
    monkeypatch.setattr(sd, "ensure_dossiers_zips_downloaded", lambda: [])
    table = sd.charger_table(cache_dir=tmp_path)
    assert table == {"scrutins": {}, "dossiers": {}}


def test_la_construction_est_additive_et_ne_vide_jamais_le_publie(monkeypatch, tmp_path):
    """Un run sans archives conserve le fichier déjà publié."""
    import build_scrutins_dossiers as build

    sortie = tmp_path / "scrutins_dossiers.json"
    sortie.write_text(
        json.dumps({"scrutins": {"an:16:1": "D0"}, "dossiers": {"D0": {"statut": "adopte"}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(build, "charger_table", lambda: {"scrutins": {}, "dossiers": {}})
    assert build.main(["--out", str(sortie)]) == 0
    publie = json.loads(sortie.read_text(encoding="utf-8"))
    assert publie["scrutins"] == {"an:16:1": "D0"}, (
        "une collecte vide a écrasé un rattachement déjà publié"
    )


# ---------------------------------------------------------------------------
# 6. Aucun cache disque : la leçon de #749
# ---------------------------------------------------------------------------

def test_la_collecte_n_ecrit_rien_a_cote_des_archives(monkeypatch, tmp_path):
    """`.cache/dossiers_an` est RESTAURÉ ENTRE RUNS en CI.

    Y poser l'index dérivé le ferait servir depuis le cache de la semaine
    précédente et il ne se reconstruirait jamais — exactement le défaut de
    #749, où un repli de cache désamorçait la rotation qu'il devait servir. Le
    parcours complet coûte 1,7 s : le cache disque achèterait ces 1,7 s au prix
    d'une donnée qui vieillit en silence.
    """
    dossier = _dossier("D1", {"acte": {"voteRefs": "VTANR5L17V960"}})
    monkeypatch.setattr(sd, "ensure_dossiers_zips_downloaded", lambda: [(17, tmp_path)])
    monkeypatch.setattr(sd, "iter_dossiers_bruts", lambda a: [(17, dossier)])
    monkeypatch.setattr(sd, "_determine_statut", lambda uid, actes: ("adopte", False, None))

    avant = set(tmp_path.rglob("*"))
    table = sd.charger_table(cache_dir=tmp_path)
    assert table["scrutins"] == {"an:17:960": "D1"}
    assert set(tmp_path.rglob("*")) == avant, (
        "la collecte a écrit un fichier à côté des archives : ce cache serait "
        "restauré entre runs et la table ne se reconstruirait plus (#749)"
    )


def test_le_memo_evite_le_double_parcours_dans_un_meme_process(monkeypatch, tmp_path):
    """Le mémo est en process — il ne survit pas au run, donc ne périme rien."""
    appels = []
    monkeypatch.setattr(sd, "ensure_dossiers_zips_downloaded", lambda: [(17, tmp_path)])
    monkeypatch.setattr(
        sd, "iter_dossiers_bruts",
        lambda a: appels.append(1) or [(17, _dossier("D1", {"acte": {"voteRefs": "VTANR5L17V960"}}))],
    )
    monkeypatch.setattr(sd, "_determine_statut", lambda uid, actes: ("adopte", False, None))
    sd.charger_table(cache_dir=tmp_path)
    sd.charger_table(cache_dir=tmp_path)
    assert len(appels) == 1, "le parcours a été refait dans le même process"
    sd.vider_memo()
    sd.charger_table(cache_dir=tmp_path)
    assert len(appels) == 2, "`vider_memo` ne relance pas le parcours"


# ---------------------------------------------------------------------------
# 7. `texte_lie_id` garde son sens
# ---------------------------------------------------------------------------

def test_la_cle_neuve_ne_touche_pas_au_texte_lie_des_motions():
    """`texte_lie_id` répond à une autre question (AGENTS.md §5).

    Il dit quel texte une MOTION DE CENSURE vise, et il est nul partout
    ailleurs. Le confondre avec le rattachement d'un scrutin à son dossier
    ferait porter à un champ deux faits différents.
    """
    source = (RACINE / "src" / "scrutins_dossiers_an.py").read_text(encoding="utf-8")
    code = source.split('"""', 2)[-1]
    assert "texte_lie_id" not in code, (
        "le module écrit dans `texte_lie_id`, réservé aux motions de censure"
    )
