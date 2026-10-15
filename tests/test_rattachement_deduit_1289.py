"""Un vote que l'Assemblée ne rattache à aucun dossier reçoit le sien par la cascade (#1289).

Mesuré le 15/10/2026 : 265 des 934 votes sur l'ensemble d'un texte ne figurent
dans aucun dossier de la source, et l'interface regroupait leurs lectures par
l'intitulé — 21 textes affichés deux fois sur 11 fiches de candidats déclarés.

La cascade, arbitrée par la propriétaire le 15/10/2026 : **la source, puis la
déduction, puis — pour ce qui reste seulement — la table relue**. Ces garde-fous tiennent les conditions de l'exception à
`regrouper-nest-pas-joindre-639` : la déduction ne remplace jamais la source,
elle est marquée, et elle s'abstient dès que deux dossiers conviennent.

Les fixtures reprennent des cas réels du corpus : la loi de financement
rectificative de la sécurité sociale pour 2014 (an:14:868 rattaché par la
source, an:14:895 non), et la motion de rejet que la source pose à la place du
vote sur l'ensemble (DLR5L16N47637, 15/11/2023).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import alerte_votes_sans_dossier as alerte  # noqa: E402
import build_scrutins_dossiers as build  # noqa: E402
import rattachement_deduit as rd  # noqa: E402

LFSSR_2014 = "Sécurité sociale : loi de financement rectificative 2014"


def _scrutin(cle: str, date: str, texte: str, type_vote: str = "vote_texte") -> dict:
    return {"id": cle, "legislature": cle.split(":")[1], "date": date, "texte": texte, "type_vote": type_vote}


VOTE_895 = _scrutin(
    "an:14:895", "2014-07-21",
    "l'ensemble du projet de loi de financement de la sécurité sociale rectificative pour 2014 (nouvelle lecture).",
)
VOTE_868 = _scrutin(
    "an:14:868", "2014-07-08",
    "l'ensemble du projet de loi de financement rectificative de la sécurité sociale pour 2014 (première lecture).",
)


def _decisions(*entrees: tuple[str, str, list[str], str]) -> dict:
    """`(date, uid, votes attachés, titre)` → la forme de `indexer_decisions`."""
    par_date: dict = {}
    dossiers: dict = {}
    for date, uid, votes, titre in entrees:
        par_date.setdefault(date, []).append((uid, votes))
        dossiers[uid] = {"titre": titre, "statut": "adopte", "sort_49_3": False}
    return {"decisions": par_date, "dossiers": dossiers}


# ---------------------------------------------------------------------------
# 1. La déduction
# ---------------------------------------------------------------------------

def test_un_vote_sans_dossier_recoit_celui_qui_decide_ce_jour_la():
    decisions = _decisions(
        ("2014-07-21", "DLR5L14N33248", [], LFSSR_2014),
        ("2014-07-21", "DLR5L14N33192", [], "Budget : règlement des comptes 2013"),
    )
    assert rd.deduire([VOTE_895], set(), decisions) == {"an:14:895": "DLR5L14N33248"}


def test_la_deduction_ne_touche_jamais_un_vote_que_la_source_rattache():
    decisions = _decisions(("2014-07-21", "AUTRE", [], LFSSR_2014))
    assert rd.deduire([VOTE_895], {"an:14:895"}, decisions) == {}


def test_deux_dossiers_qui_conviennent_et_la_deduction_s_abstient():
    """Les jumelles votées le même jour sous le même titre : on ne choisit pas."""
    decisions = _decisions(
        ("2014-07-21", "D1", [], LFSSR_2014),
        ("2014-07-21", "D2", [], LFSSR_2014),
    )
    assert rd.deduire([VOTE_895], set(), decisions) == {}


def test_une_decision_qui_porte_deja_son_vote_sur_l_ensemble_n_attend_personne():
    decisions = _decisions(("2014-07-21", "D1", ["an:14:900"], LFSSR_2014))
    autre = _scrutin("an:14:900", "2014-07-21", "l'ensemble du projet de loi de financement rectificative de la sécurité sociale pour 2014.")
    assert rd.deduire([VOTE_895, autre], {"an:14:900"}, decisions) == {}


def test_une_decision_qui_ne_porte_qu_une_motion_reste_libre():
    """La source pose parfois la motion de rejet là où devrait être le vote."""
    motion = _scrutin("an:14:896", "2014-07-21", "la motion de rejet préalable du projet de loi de financement rectificative de la sécurité sociale pour 2014.")
    decisions = _decisions(("2014-07-21", "DLR5L14N33248", ["an:14:896"], LFSSR_2014))
    assert rd.deduire([VOTE_895, motion], {"an:14:896"}, decisions) == {"an:14:895": "DLR5L14N33248"}


def test_un_titre_qui_ne_correspond_pas_ne_suffit_pas_a_la_date():
    decisions = _decisions(("2014-07-21", "D1", [], "Budget : règlement des comptes 2013"))
    assert rd.deduire([VOTE_895], set(), decisions) == {}


def test_organique_et_ordinaire_ne_se_confondent_pas():
    organique = _scrutin("an:14:280", "2013-04-17", "l'ensemble du projet de loi organique relatif à l'élection des conseillers municipaux.")
    decisions = _decisions(("2013-04-17", "ORDINAIRE", [], "Élection des conseillers municipaux"))
    assert rd.deduire([organique], set(), decisions) == {}


@pytest.mark.parametrize("texte", [
    "l'amendement n° 12 de M. X à l'article 3 du projet de loi de financement rectificative de la sécurité sociale pour 2014.",
    "l'ensemble de l'article 3 du projet de loi de financement rectificative de la sécurité sociale pour 2014.",
])
def test_seuls_les_votes_sur_l_ensemble_recoivent_une_deduction(texte):
    vote = _scrutin("an:14:897", "2014-07-21", texte)
    decisions = _decisions(("2014-07-21", "DLR5L14N33248", [], LFSSR_2014))
    assert rd.deduire([vote], set(), decisions) == {}


def test_oeuvre_avec_ou_sans_ligature_est_le_meme_mot():
    assert rd.mots("mise en œuvre") == rd.mots("mise en oeuvre")


# ---------------------------------------------------------------------------
# 2. La cascade et sa trace
# ---------------------------------------------------------------------------

def _table(rattachements: dict | None = None) -> dict:
    return {"rattachements": rattachements or {}, "textes_distincts": []}


def test_la_cascade_marque_ce_qui_ne_vient_pas_de_la_source():
    composee = build.composer(
        {"scrutins": {}, "dossiers": {}, "provenance": {}},
        {"scrutins": {"an:14:868": "DLR5L14N33248"}, "dossiers": {"DLR5L14N33248": {"statut": "adopte", "sort_49_3": False}}},
        [VOTE_868, VOTE_895],
        _decisions(("2014-07-21", "DLR5L14N33248", [], LFSSR_2014)),
        _table(),
    )
    assert composee["scrutins"] == {"an:14:868": "DLR5L14N33248", "an:14:895": "DLR5L14N33248"}
    assert composee["provenance"] == {"an:14:895": rd.PROVENANCE_DEDUITE}


def test_la_table_relue_ne_remplace_ni_la_source_ni_la_deduction():
    composee = build.composer(
        {"scrutins": {}, "dossiers": {}, "provenance": {}},
        {"scrutins": {"an:14:868": "SOURCE"}, "dossiers": {}},
        [VOTE_868, VOTE_895],
        _decisions(("2014-07-21", "DEDUIT", [], LFSSR_2014)),
        _table({"an:14:868": {"dossier": "RELU"}, "an:14:895": {"dossier": "RELU"}}),
    )
    assert composee["scrutins"] == {"an:14:868": "SOURCE", "an:14:895": "DEDUIT"}
    assert composee["lignes_inutiles"] == ["an:14:868", "an:14:895"]


def test_la_table_relue_comble_ce_qui_reste_en_dernier():
    composee = build.composer(
        {"scrutins": {}, "dossiers": {}, "provenance": {}},
        {"scrutins": {"an:14:868": "SOURCE"}, "dossiers": {}},
        [VOTE_868, VOTE_895],
        _decisions(),
        _table({"an:14:895": {"dossier": "RELU"}}),
    )
    assert composee["scrutins"]["an:14:895"] == "RELU"
    assert composee["provenance"] == {"an:14:895": rd.PROVENANCE_TABLE}
    assert composee["dossiers"]["RELU"] == {"statut": None, "sort_49_3": None}


def test_sans_archives_les_deductions_d_avant_sont_gardees_telles_quelles():
    ancienne = {
        "scrutins": {"an:14:868": "DLR5L14N33248", "an:14:895": "DLR5L14N33248"},
        "dossiers": {"DLR5L14N33248": {"statut": "adopte", "sort_49_3": False}},
        "provenance": {"an:14:895": rd.PROVENANCE_DEDUITE},
    }
    composee = build.composer(ancienne, {"scrutins": {}, "dossiers": {}}, [], None, _table())
    assert composee["scrutins"] == ancienne["scrutins"]
    assert composee["provenance"] == ancienne["provenance"]


def test_une_deduction_que_la_source_rend_inutile_perd_sa_marque():
    ancienne = {
        "scrutins": {"an:14:895": "DLR5L14N33248"},
        "dossiers": {},
        "provenance": {"an:14:895": rd.PROVENANCE_DEDUITE},
    }
    composee = build.composer(
        ancienne,
        {"scrutins": {"an:14:895": "DLR5L14N33248"}, "dossiers": {}},
        [VOTE_895],
        _decisions(),
        _table(),
    )
    assert composee["provenance"] == {}


def test_le_fichier_publie_porte_la_provenance(monkeypatch, tmp_path):
    scrutins = tmp_path / "scrutins.json"
    scrutins.write_text(json.dumps({"scrutins": [VOTE_868, VOTE_895]}), encoding="utf-8")
    monkeypatch.setattr(build, "charger_table", lambda: {
        "scrutins": {"an:14:868": "DLR5L14N33248"},
        "dossiers": {"DLR5L14N33248": {"statut": "adopte", "sort_49_3": False}},
    })
    monkeypatch.setattr(build, "_decisions_des_archives", lambda: _decisions(("2014-07-21", "DLR5L14N33248", [], LFSSR_2014)))
    sortie = tmp_path / "scrutins_dossiers.json"
    assert build.main(["--out", str(sortie), "--scrutins", str(scrutins), "--table", str(tmp_path / "absente.json")]) == 0
    publie = json.loads(sortie.read_text(encoding="utf-8"))
    assert publie["provenance"] == {"an:14:895": "deduit_date_et_titre"}


# ---------------------------------------------------------------------------
# 3. La table relue et l'alerte
# ---------------------------------------------------------------------------

def test_la_table_relue_du_depot_se_lit_et_ne_nomme_que_des_votes_de_l_an():
    table = rd.charger_table_manuelle(RACINE / "config" / "rattachements_scrutins_dossiers.json")
    for cle, ligne in table["rattachements"].items():
        assert cle.startswith("an:"), cle
        assert ligne["dossier"].startswith("DLR5L"), ligne
        assert ligne.get("verifie_le") and ligne.get("preuve"), f"{cle} : ligne sans date ni preuve de relecture"


def test_l_alerte_releve_un_texte_reformule_reste_sans_dossier():
    a = _scrutin("an:17:1330", "2025-04-09", "l'ensemble de la proposition de loi visant à réformer le mode d'élection des membres du Conseil de Paris (première lecture).")
    b = _scrutin("an:17:2954", "2025-07-07", "l'ensemble de la proposition de loi visant à réformer le mode d’élection des membres du conseil de Paris (nouvelle lecture).")
    paires = alerte.relever([a, b], {"an:17:1330": "DLR5L17N50692"}, [])
    assert len(paires) == 1


def test_une_paire_jugee_distincte_n_est_plus_signalee():
    a = _scrutin("an:15:4355", "2022-01-27", "l'ensemble du projet de loi autorisant l'approbation de l'accord avec Maurice relatif au statut des forces.")
    b = _scrutin("an:15:4356", "2022-01-27", "l'ensemble du projet de loi autorisant l'approbation de l'accord avec le Qatar relatif au statut des forces.")
    assert alerte.relever([a, b], {}, [])
    assert alerte.relever([a, b], {}, [["an:15:4355", "an:15:4356"]]) == []


def test_deux_textes_qui_ont_chacun_leur_dossier_ne_sont_jamais_signales():
    a = _scrutin("an:15:246", "2017-11-14", "l'ensemble du projet de loi de finances rectificative pour 2017 (lecture définitive).")
    b = _scrutin("an:15:345", "2017-12-12", "l'ensemble du projet de loi de finances rectificative pour 2017 (première lecture).")
    assert alerte.relever([a, b], {"an:15:246": "D1", "an:15:345": "D2"}, []) == []


def test_l_alerte_a_son_issue_de_suivi_dans_le_workflow():
    workflow = (RACINE / ".github" / "workflows" / "generate-data.yml").read_text(encoding="utf-8")
    assert "python3 src/alerte_votes_sans_dossier.py" in workflow
    assert "ETIQUETTE: votes-sans-dossier" in workflow
