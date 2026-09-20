"""#823 — un compte ne voit pas un échange, et une union le paie.

Le contrôle de perte relève chaque liste par un entier. Une entrée remplacée
par une autre garde le même compte : l'échange est invisible. Il ne se voit
qu'à l'étage au-dessus, sur une union, où il apparaît comme une perte
inexplicable — c'est ce qui a coûté le run `34454305520`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_diff_profils import (  # noqa: E402
    COLLECTION_GROUPES,
    COLLECTION_PROFILS,
    LIMITE_ENTREES_NOMMEES,
    _identites,
    comparer,
    generate_markdown_report,
    comparer_tout,
    relever,
)


def _profil(tags):
    return relever({"tags_thematiques": list(tags)}, COLLECTION_PROFILS)


def _tag(t):
    return {"tag": t, "nb_membres_porteurs": 1, "poids_relatif": 0.1}


def _groupe(tags):
    return relever({"tags_thematiques_agreges": [_tag(t) for t in tags]},
                   COLLECTION_GROUPES)


# ---------------------------------------------------------------------------
# Le défaut nommé par l'issue
# ---------------------------------------------------------------------------

def test_un_echange_a_compte_egal_etait_invisible_et_ne_l_est_plus():
    """Trois étiquettes avant, trois après — et pourtant une a disparu."""
    r = comparer({"a.json": _profil(["budget", "santé", "école"])},
                 {"a.json": _profil(["budget", "santé", "climat"])},
                 COLLECTION_PROFILS)
    assert r["pertes"] == [], "aucun compte n'a baissé : c'est tout le problème"
    assert [e["disparues"] for e in r["echanges"]] == [["école"]]


def test_l_echange_ne_bloque_pas():
    """`tags_thematiques` est DÉRIVÉ, recalculé à chaque run et jamais fusionné
    (§4) : un échange y est le fonctionnement normal, pas un incident. Bloquer
    ferait échouer des runs légitimes."""
    r = comparer({"a.json": _profil(["budget", "école"])},
                 {"a.json": _profil(["budget", "climat"])},
                 COLLECTION_PROFILS)
    assert r["echanges"]
    assert r["bloquant"] is False


def test_la_perte_d_une_union_est_desormais_nommee():
    """Le cas `REN-16` : la baisse bloquait déjà, mais sans dire QUOI.

    « Le run n'ayant rien committé, sa sortie n'existe plus : seuls les comptes
    ont survécu. Je n'ai pas pu nommer l'étiquette. » — #823.
    """
    r = comparer({"g.json": _groupe(["a", "b", "c"])},
                 {"g.json": _groupe(["a", "b"])},
                 COLLECTION_GROUPES)
    assert r["bloquant"] is True, "une union qui perd reste bloquante"
    assert [e["disparues"] for e in r["echanges"]] == [["c"]]


def test_un_gain_qui_masque_une_disparition_est_vu():
    """Le cas le plus trompeur : le compte MONTE et une entrée disparaît."""
    r = comparer({"a.json": _profil(["budget", "école"])},
                 {"a.json": _profil(["budget", "climat", "santé", "europe"])},
                 COLLECTION_PROFILS)
    assert r["pertes"] == []
    assert r["gains"], "le compte monte de 2 à 4"
    assert [e["disparues"] for e in r["echanges"]] == [["école"]]


def test_aucune_disparition_ne_produit_aucun_constat():
    r = comparer({"a.json": _profil(["budget"])},
                 {"a.json": _profil(["budget", "santé"])},
                 COLLECTION_PROFILS)
    assert r["echanges"] == []


# ---------------------------------------------------------------------------
# Ce que le relevé nomme, et ce qu'il refuse de nommer
# ---------------------------------------------------------------------------

def test_seules_les_listes_declarees_sont_relevees_en_valeurs():
    """`amendements` porte des millions d'entrées : les nommer coûterait autant
    de clés. C'est pourquoi nommer n'est pas le comportement par défaut."""
    releve = relever(
        {"tags_thematiques": ["budget"], "amendements": [{"amendement_id": "x"}]},
        COLLECTION_PROFILS,
    )
    assert set(releve["valeurs"]) == {"tags_thematiques"}


def test_une_liste_qui_ne_se_nomme_pas_rend_None_et_non_un_ensemble_vide():
    """Un ensemble vide dirait « cette liste ne porte rien » — un fait faux sur
    les données là où il n'y a qu'une lecture impossible (§2 règle 5)."""
    assert _identites([{"pas_de_tag": 1}]) is None
    assert _identites("pas une liste") is None
    assert _identites([]) == set()


def test_les_deux_formes_du_corpus_se_nomment():
    assert _identites(["budget", "santé"]) == {"budget", "santé"}
    assert _identites([_tag("budget")]) == {"budget"}


def test_une_liste_non_nommable_ne_produit_aucun_constat():
    """Sans relevé des deux côtés, on ne conclut pas : ne pas savoir n'est pas
    un fait."""
    avant = relever({"tags_thematiques": [{"illisible": 1}]}, COLLECTION_PROFILS)
    apres = relever({"tags_thematiques": ["budget"]}, COLLECTION_PROFILS)
    assert comparer({"a.json": avant}, {"a.json": apres},
                    COLLECTION_PROFILS)["echanges"] == []


def test_le_nombre_d_entrees_nommees_est_plafonne():
    """Le rapport est lu par un humain qui cherche une cause, pas un inventaire."""
    avant = _profil([f"tag-{i}" for i in range(LIMITE_ENTREES_NOMMEES + 15)])
    r = comparer({"a.json": avant}, {"a.json": _profil([])}, COLLECTION_PROFILS)
    echange = r["echanges"][0]
    assert len(echange["disparues"]) == LIMITE_ENTREES_NOMMEES
    assert echange["nb_disparues"] == LIMITE_ENTREES_NOMMEES + 15


# ---------------------------------------------------------------------------
# Le rapport, sans lequel le constat serait calculé pour personne
# ---------------------------------------------------------------------------

def test_le_rapport_nomme_les_entrees_disparues():
    rapport = comparer_tout([
        (COLLECTION_PROFILS,
         {"a.json": _profil(["budget", "école"])},
         {"a.json": _profil(["budget", "climat"])}),
    ])
    md = generate_markdown_report(rapport, "abc1234")
    assert "`école`" in md
    assert "entrée(s) disparue(s)" in md


def test_le_rapport_signale_les_fichiers_qui_n_ont_perdu_aucun_compte():
    """C'est la population qu'aucun autre contrôle ne voit."""
    rapport = comparer_tout([
        (COLLECTION_PROFILS,
         {"a.json": _profil(["budget", "école"])},
         {"a.json": _profil(["budget", "climat"])}),
    ])
    md = generate_markdown_report(rapport, "abc1234")
    assert "n'ont perdu aucun compte" in md
