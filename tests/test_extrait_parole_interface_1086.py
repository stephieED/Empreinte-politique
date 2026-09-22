"""L'interface lit la collecte en extrait comme un régime à part (#1086).

Backend publie désormais, pour la parole des membres de roster et de
gouvernement, `collecte: "extrait"` : les 280 premiers caractères du verbatim
dans `texte`, et `texte_tronque` quand il continue. Deux lecteurs testaient la
valeur exacte `theme_seul` et auraient pris un extrait pour le compte rendu
entier : l'adaptateur de « Ce qu'il a dit » et la page /couverture. Ces gardes
vérifient qu'un extrait n'est jamais compté parmi les verbatims.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "src" / "utils" / "parolesParPeriode.js"
COUVERTURE = UI / "scripts" / "couverture-corpus.mjs"


CROCHET = """
export async function resolve(specifier, context, next) {
  if (/^\\.\\.?\\//.test(specifier) && !/\\.[cm]?js$/.test(specifier)) {
    return next(specifier + '.js', context);
  }
  return next(specifier, context);
}
"""


def _executer(script: str) -> object:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    # Les modules de l'interface importent sans extension, à la manière de
    # Vite ; node ne les résout pas seul. Le crochet ajoute « .js » à un import
    # relatif qui n'en porte pas, et rien d'autre.
    entete = (
        "import { register } from 'node:module';\n"
        f"register('data:text/javascript,' + encodeURIComponent({json.dumps(CROCHET)}));\n"
        f"const f = await import({json.dumps(MODULE.as_uri())});\n"
    )
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout.strip().splitlines()[-1])


ENTREES = [
    # Forme copiée d'une entrée `extrait` telle que #1086 la publie.
    {"intervention_id": "syceron_CRSANR5L17S2026O1N180_3", "date": "2026-03-24",
     "type_detail": "question_gouvernement", "collecte": "extrait",
     "texte": "Monsieur le député, le Gouvernement est mobilisé.", "texte_tronque": True},
    {"intervention_id": "syceron_CRSANR5L17S2026O1N180_4", "date": "2026-03-24",
     "type_detail": "question_gouvernement", "collecte": "theme_seul"},
    {"intervention_id": "syceron_CRSANR5L17S2026O1N180_5", "date": "2026-03-24",
     "type_detail": "question_gouvernement", "texte": "Compte rendu entier."},
]


def test_un_extrait_est_qualifie_comme_tel() -> None:
    q = _executer(f"console.log(JSON.stringify(f.qualifierInterventions({json.dumps(ENTREES)})))")
    assert [(i["extrait"], i["themeSeul"], i["texteTronque"]) for i in q] == [
        (True, False, True), (False, True, False), (False, False, False),
    ]


def test_un_extrait_ne_compte_pas_parmi_les_verbatims() -> None:
    c = _executer(
        f"console.log(JSON.stringify(f.couvertureDesParoles(f.qualifierInterventions({json.dumps(ENTREES)}))))"
    )
    assert (c["total"], c["verbatim"], c["extrait"], c["themeSeul"]) == (3, 1, 1, 1)


def test_la_couverture_n_ecrit_pas_un_extrait_comme_un_verbatim() -> None:
    source = COUVERTURE.read_text(encoding="utf-8")
    ligne = re.search(r"champ\('avec le verbatim du compte rendu', \[\s*apport\([^\n]*", source)
    assert ligne and "collecte !== 'extrait'" in ligne.group(0)
