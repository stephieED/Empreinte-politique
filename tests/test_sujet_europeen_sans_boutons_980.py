"""#980 — le sujet nettoyé d'une question européenne atteint l'entrée déjà publiée.

#938 retire la queue de boutons « PDF (… KB) DOC (… KB) » à l'indexation du
dump : l'entrée NEUVE est propre. Mais `merge_pivot_profile` fusionne les
interventions par `merge_lists_by_key`, où l'ancienne entrée gagne à
identifiant égal. Mesuré le 16/09/2026 sur `origin/main` `966dd18a3`, après un
run complet : **313** interventions des candidats déclarés gardaient leur sujet
sale (Le Pen 147, Philippot 128, Mélenchon 38), toutes des questions QE/QO.

L'ancienne entrée ci-dessous est **copiée du corpus** (florian-philippot), pas
inventée. La neuve sort du vrai chemin : un dump, `build_activities_index`, puis
`_make_intervention`.
"""

import copy
import sys
from pathlib import Path
from unittest.mock import patch

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "tests"))

from merge_profile import backfill_sujet_europeen, merge_pivot_profile  # noqa: E402
from normalize_parltrack_dumps import _make_intervention  # noqa: E402
from parltrack_dumps import build_activities_index  # noqa: E402
from test_parltrack_dumps import _write_zst_file  # noqa: E402

MEP = 124738

#: Copiée verbatim de `pivot_data/profiles/florian-philippot.pivot.json`,
#: `origin/main` `966dd18a3`.
PUBLIEE = {
    "intervention_id": "europarl_E-005582/2017 - Commission",
    "date": "2016-11-22",
    "type_detail": "question",
    "sujet": "Overhaul of the Posted Workers Directive PDF (5 KB) DOC (18 KB)",
    "theme_officiel": None,
    "seance": None,
    "dossier": None,
    "source": {"institution": "parlement_europeen", "legislature": 8},
    "fonction": None,
    "format": None,
    "mots_cles": [],
    "source_url": "http://www.europarl.europa.eu/doceo/document/E-8-2017-005582_EN.html",
    "texte": None,
    "collecte": "sans_verbatim_source",
    "sous_type": "QE",
}


def _recollectee(tmp_path: Path, titre: str = PUBLIEE["sujet"]) -> dict:
    """La même question, telle qu'un run la produit aujourd'hui."""
    dump = tmp_path / "ep_mep_activities.json.zst"
    _write_zst_file(dump, [{
        "mep_id": MEP,
        "WQ": [{
            "date": "2017-07-12T00:00:00",
            "term": 8,
            "reference": "E-005582/2017 - Commission",
            "url": PUBLIEE["source_url"],
            "title": titre,
        }],
    }])
    with patch("parltrack_dumps.ensure_dump", return_value=dump), \
         patch("parltrack_dumps.PARLTRACK_CACHE_DIR", tmp_path):
        index = build_activities_index(perimetre=frozenset({MEP}))
    return _make_intervention("question_ecrite", index[MEP]["question_ecrite"][0])


def test_l_entree_recollectee_a_la_meme_identite_et_un_sujet_propre(tmp_path):
    """Le prérequis du défaut : même clé, sujet différent."""
    neuve = _recollectee(tmp_path)

    assert neuve["intervention_id"] == PUBLIEE["intervention_id"]
    assert neuve["sujet"] == "Overhaul of the Posted Workers Directive"


def test_la_fusion_pivot_publie_le_sujet_propre(tmp_path):
    """Le défaut mesuré : sans report, l'ancienne entrée gagnait."""
    ancien = {"interventions": [copy.deepcopy(PUBLIEE)]}
    neuf = {"interventions": [_recollectee(tmp_path)]}

    fusionne = merge_pivot_profile(ancien, neuf)

    assert len(fusionne["interventions"]) == 1
    entree = fusionne["interventions"][0]
    assert entree["sujet"] == "Overhaul of the Posted Workers Directive"
    # Seul le sujet change : l'entrée publiée garde tout le reste.
    assert {k: v for k, v in entree.items() if k != "sujet"} == {
        k: v for k, v in PUBLIEE.items() if k != "sujet"}


def test_un_sujet_qui_differe_autrement_n_est_pas_remplace(tmp_path):
    """Le critère est la queue de boutons, pas « le neuf gagne » : un intitulé
    que la source aurait réécrit n'est pas une correction de #938."""
    neuve = _recollectee(tmp_path, titre="Revision of the Posted Workers Directive")

    fusionne = backfill_sujet_europeen(
        [copy.deepcopy(PUBLIEE)], [neuve])

    assert fusionne[0]["sujet"] == PUBLIEE["sujet"]


def test_une_entree_de_l_assemblee_n_est_pas_touchee():
    """Même identifiant, même forme de sujet : sans institution européenne, rien."""
    ancienne = {**PUBLIEE, "source": {"type": "syceron"}}
    neuve = {**ancienne, "sujet": "Overhaul of the Posted Workers Directive"}

    fusionne = backfill_sujet_europeen([ancienne], [neuve])

    assert fusionne[0]["sujet"] == PUBLIEE["sujet"]


def test_le_report_est_idempotent(tmp_path):
    """Un second run sur le corpus corrigé ne change plus rien."""
    neuf = {"interventions": [_recollectee(tmp_path)]}
    une_fois = merge_pivot_profile({"interventions": [copy.deepcopy(PUBLIEE)]}, neuf)

    deux_fois = merge_pivot_profile(copy.deepcopy(une_fois), neuf)

    assert deux_fois["interventions"] == une_fois["interventions"]
