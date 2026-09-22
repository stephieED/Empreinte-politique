"""Une question au gouvernement, comptée une fois sur la fiche candidat (#1094).

L'acte (questions.assemblee-nationale.fr, `sous_type: "QG"`) et ses tours de
parole (compte rendu, `question_gouvernement`) sont reliés par `question_ref`
(#1096). Arbitré le 22/09/2026, option A : une entrée par question — les tours
portent le texte, l'acte leur apporte ministère et page, puis se retire.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent

UTILS = RACINE / "web" / "UI_finale" / "src" / "utils"

CROCHET = r"""
export async function resolve(specifier, context, next) {
  if (/^\.\.?\//.test(specifier) && !/\.[cm]?js$/.test(specifier)) {
    return next(specifier + '.js', context);
  }
  return next(specifier, context);
}
"""


def _executer(module: str, script: str) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = (
        "import { register } from 'node:module';\n"
        f"register('data:text/javascript,' + encodeURIComponent({json.dumps(CROCHET)}));\n"
        f"const f = await import({json.dumps((UTILS / module).as_uri())});\n"
    )
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


# ── Une question au gouvernement, comptée une fois (#1094, option A) ──────────
# Entrées copiées du corpus (philippe-brun, 28-29/04/2026), `question_ref` posé
# comme Backend le publie (#1096).
ACTE = {"intervention_id": "question_QANR5L17QG1472", "date": "2026-04-29", "type_detail": "question",
        "sujet": "Prix des carburants", "sous_type": "QG", "source_url": "https://questions.assemblee-nationale.fr/q17/QANR5L17QG1472.htm",
        "ministere": "Ministère délégué, porte-parole du Gouvernement auprès du Premier ministre, et ministère délégué, chargé de l'énergie"}
TOUR = {"intervention_id": "syceron_CRSANR5L17S2026O1N210_31", "date": "2026-04-28", "type_detail": "question_gouvernement",
        "theme_officiel": "Prix des carburants", "texte": "Monsieur le ministre…", "question_ref": "question_QANR5L17QG1472"}
SEULE = {"intervention_id": "question_QANR5L17QG9999", "date": "2026-05-06", "type_detail": "question", "sous_type": "QG", "sujet": "Autre"}
ECRITE = {"intervention_id": "question_QANR5L17QE17431", "date": "2026-07-28", "type_detail": "question", "sous_type": "QE"}


def test_une_question_au_gouvernement_ne_compte_qu_une_fois() -> None:
    script = (
        f"const r = f.rattacherQuestions({json.dumps([ACTE, TOUR, SEULE, ECRITE])});\n"
        "console.log(JSON.stringify(r.map((i) => [i.intervention_id, i.type_detail, i.question?.intervention_id ?? null])));"
    )
    assert _executer("parolesParPeriode.js", script) == [
        ["syceron_CRSANR5L17S2026O1N210_31", "question_gouvernement", "question_QANR5L17QG1472"],
        ["question_QANR5L17QG9999", "question_gouvernement", None],
        ["question_QANR5L17QE17431", "question", None],
    ]


def test_le_tour_porte_le_ministere_et_la_page_de_sa_question() -> None:
    script = (
        f"const q = f.qualifierInterventions(f.rattacherQuestions({json.dumps([ACTE, TOUR])}));\n"
        "console.log(JSON.stringify(q.map((i) => i.question)));"
    )
    [question] = _executer("parolesParPeriode.js", script)
    assert question == {"ministere": ACTE["ministere"], "lien": ACTE["source_url"]}
