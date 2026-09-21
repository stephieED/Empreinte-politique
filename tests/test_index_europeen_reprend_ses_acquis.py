"""L'index des dossiers européens reprend ce que l'index PUBLIÉ sait déjà.

Ce que la passe des domaines apprend vit dans le cache du portail européen,
qui est un cache de CI : il disparaît. Mesuré le 21/09/2026, premier run sur le
dépôt public, cache reparti vide — **996 dossiers sont repassés de
`documents_non_classes` à `question_non_posee`**, c'est-à-dire de « le portail
a répondu, il ne classe rien » à « nous n'avons jamais demandé ». La fiche
européenne devenait plus pauvre d'un run à l'autre, et aucune garde ne pouvait
le voir : les deux états sont des absences licites (§2 règle 5), et le contrôle
de perte compte des cardinalités, pas des motifs.

Les entrées d'essai sont **copiées du corpus** (`pivot_data/dossiers_europeens.json`,
état du 21/09/2026) : références, motifs et forme des domaines sont ceux que la
source produit, pas ceux qu'un test imagine.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dossiers_europeens import reprendre_acquis  # noqa: E402

#: Copiée du corpus : un dossier dont les domaines sont connus.
AVEC_DOMAINES = {
    "id": "pe-dossier:1998/0031R(NLE)",
    "reference": "1998/0031R(NLE)",
    "titre": "Partnership and Cooperation Agreement with Turkmenistan",
    "domaines": [{"code": "6", "libelle": "Relations extérieures", "concepts": 4}],
    "domaines_document": "A-8-2016-0072",
}

#: Copiée du corpus : un dossier dont le portail a répondu sans classer.
SANS_CLASSEMENT = {
    "id": "pe-dossier:1992/0449B(COD)",
    "reference": "1992/0449B(COD)",
    "titre": "Safety and health at work: exposure of workers to optical radiations",
    "domaines": [],
    "domaines_non_resolu": {"motif": "documents_non_classes"},
}


def _publier(tmp_path: Path, entrees: list[dict]) -> Path:
    chemin = tmp_path / "dossiers_europeens.json"
    chemin.write_text(json.dumps({"dossiers": entrees}, ensure_ascii=False), encoding="utf-8")
    return chemin


def _ignorant(entree: dict) -> dict:
    """La même entrée telle qu'un run au cache froid la produit."""
    return {"id": entree["id"], "reference": entree["reference"], "titre": entree["titre"],
            "domaines": [], "domaines_non_resolu": {"motif": "question_non_posee"}}


def test_un_verdict_publie_est_repris_quand_ce_run_na_pas_demande(tmp_path):
    """Le discriminant du lot : sans reprise, l'entrée reste « jamais demandé »."""
    publie = _publier(tmp_path, [SANS_CLASSEMENT])
    entrees = [_ignorant(SANS_CLASSEMENT)]

    compteurs = reprendre_acquis(entrees, {SANS_CLASSEMENT["reference"]: []}, publie)

    assert entrees[0]["domaines_non_resolu"] == {"motif": "documents_non_classes"}
    assert compteurs == {"documents_non_classes": 1}


def test_des_domaines_publies_reviennent_avec_leur_document(tmp_path):
    publie = _publier(tmp_path, [AVEC_DOMAINES])
    entrees = [_ignorant(AVEC_DOMAINES)]

    compteurs = reprendre_acquis(
        entrees, {AVEC_DOMAINES["reference"]: ["A-8-2016-0072", "B-8-2016-0001"]}, publie)

    assert entrees[0]["domaines"] == AVEC_DOMAINES["domaines"]
    assert entrees[0]["domaines_document"] == "A-8-2016-0072"
    assert "domaines_non_resolu" not in entrees[0], (
        "une entrée qui retrouve ses domaines ne doit plus porter de motif d'absence"
    )
    assert compteurs == {"avec_domaines": 1}


def test_un_verdict_obtenu_maintenant_lemporte_sur_lancien(tmp_path):
    """Rien n'est figé : ce run a demandé, sa réponse est la plus fraîche.

    C'est ce qui permet au budget du run suivant de réinterroger ce qui a été
    repris, au lieu de le geler définitivement.
    """
    publie = _publier(tmp_path, [SANS_CLASSEMENT])
    entrees = [dict(SANS_CLASSEMENT, domaines=[{"code": "6", "libelle": "Relations extérieures",
                                                "concepts": 2}],
                    domaines_document="B-8-2016-0001")]
    entrees[0].pop("domaines_non_resolu")

    compteurs = reprendre_acquis(entrees, {SANS_CLASSEMENT["reference"]: []}, publie)

    assert entrees[0]["domaines_document"] == "B-8-2016-0001"
    assert compteurs == {}


def test_une_panne_eurovoc_nest_pas_un_acquis(tmp_path):
    """`eurovoc_injoignable` est une panne, pas une réponse du portail.

    La reprendre publierait une absence dont la cause a disparu, et
    empêcherait de redemander ce qui n'a jamais reçu de réponse (§2 règle 5).
    """
    publie = _publier(tmp_path, [dict(SANS_CLASSEMENT,
                                      domaines_non_resolu={"motif": "eurovoc_injoignable"})])
    entrees = [_ignorant(SANS_CLASSEMENT)]

    compteurs = reprendre_acquis(entrees, {SANS_CLASSEMENT["reference"]: []}, publie)

    assert entrees[0]["domaines_non_resolu"] == {"motif": "question_non_posee"}
    assert compteurs == {}


def test_des_domaines_tires_dun_document_qui_nest_plus_cite_ne_reviennent_pas(tmp_path):
    """Le dump bouge. Republier un domaine tiré d'un document que le dossier ne
    cite plus serait une affirmation que la source ne porte pas (§2 règle 2)."""
    publie = _publier(tmp_path, [AVEC_DOMAINES])
    entrees = [_ignorant(AVEC_DOMAINES)]

    compteurs = reprendre_acquis(
        entrees, {AVEC_DOMAINES["reference"]: ["TA-9-2024-0001"]}, publie)

    assert entrees[0]["domaines"] == []
    assert entrees[0]["domaines_non_resolu"] == {"motif": "question_non_posee"}
    assert compteurs == {}


def test_un_index_publie_absent_ou_illisible_ne_fait_rien_echouer(tmp_path):
    """Premier run d'un dépôt neuf : il n'y a rien à reprendre, et c'est normal."""
    entrees = [_ignorant(SANS_CLASSEMENT)]
    assert reprendre_acquis(entrees, {}, tmp_path / "absent.json") == {}

    illisible = tmp_path / "casse.json"
    illisible.write_text("{ceci n'est pas du JSON", encoding="utf-8")
    assert reprendre_acquis(entrees, {}, illisible) == {}
    assert entrees[0]["domaines_non_resolu"] == {"motif": "question_non_posee"}
