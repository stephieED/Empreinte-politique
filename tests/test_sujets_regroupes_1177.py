"""Un même sujet sous deux graphies se lit en une ligne sur la fiche de groupe (#1177).

L'Assemblée intitule la même séance « Motion de censure » et « Motions de
censure ». L'agrégat des fiches de groupe range les deux sous une clé
(`cle_tag_thematique`, #1042) ; la fiche lisait l'intitulé exact. Mesuré le
08/10/2026 sur `groupe-AN-EPR-17` (`main` 1739b9c12) : deux lignes, 226 prises
de parole de 21 membres et 183 de 24, là où l'agrégat publie 34 membres sous
« motions de censure ». Arbitré par la propriétaire : la fiche regroupe avec la
même clé. Après : une ligne, 409 prises de parole de 33 membres — l'écart d'un
membre avec l'agrégat est celui de la population (la fiche écarte la présidence
de séance et la parole tenue comme membre du gouvernement).

LA FICHE CANDIDAT N'EST PAS CONCERNÉE : deux intitulés voisins y restent deux
entrées (#639, `tests/test_paroles_par_periode_328.py`), et la règle vit pour
cela dans un module à part.

CE QUE CES TESTS NE COUVRENT PAS : ils ne construisent aucune fiche. Les
intitulés sont copiés du corpus ; le compte sur EPR a été mesuré hors dépôt.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from src.schema_pivot import cle_tag_thematique

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "src" / "utils" / "sujetsRegroupes.js"

#: Intitulés copiés du corpus (thèmes de séance, étiquettes de fiches de groupe).
INTITULES = [
    "Motion de censure", "Motions de censure", "dépôt d’une motion de censure",
    "dépôt de deux motions de censure", "Fermetures de classes", "fermeture de classes",
    "Pénurie de médicaments", "États généraux de la justice", "Prix du gaz",
    "Statut des AESH", "Parcoursup", "  Carte   scolaire ", "Jeux Olympiques et Paralympiques de 2030",
]


def _node(expression: str):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = "const m = await import(%r);\nprocess.stdout.write(JSON.stringify(%s));" % (MODULE.as_uri(), expression)
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_la_cle_de_l_interface_est_celle_de_l_agregat() -> None:
    """Deux copies d'une règle divergent : celle-ci est exécutée des deux côtés."""
    cote_interface = _node("%s.map(m.cleTagThematique)" % json.dumps(INTITULES))
    assert cote_interface == [cle_tag_thematique(t.strip().lower()) for t in INTITULES]


def test_singulier_et_pluriel_prennent_la_forme_de_l_agregat() -> None:
    lus = ["motion de censure"] * 3 + ["motions de censure"] * 2
    formes = dict(_node("[...m.formesDesSujets(%s, ['motions de censure'])]" % json.dumps(lus)))
    assert formes == {"motion de censure": "motions de censure", "motions de censure": "motions de censure"}


def test_sans_agregat_la_forme_la_plus_frequente_l_emporte() -> None:
    """Toujours une forme de la source, jamais la clé (§2 règle 2)."""
    lus = ["fermetures de classes", "fermeture de classes", "fermetures de classes"]
    formes = dict(_node("[...m.formesDesSujets(%s, [])]" % json.dumps(lus)))
    assert set(formes.values()) == {"fermetures de classes"}
    egalite = dict(_node("[...m.formesDesSujets(['b classes', 'b classe'], [])]"))
    assert set(egalite.values()) == {"b classe"}, "l'ordre alphabétique départage"


def test_intitule_non_publie_ne_se_regroupe_avec_rien() -> None:
    formes = dict(_node("[...m.formesDesSujets(['Intitulé non publié', 'x'], [])]"))
    assert "Intitulé non publié" not in formes


def test_la_figure_et_les_extraits_passent_par_le_regroupement() -> None:
    vue = (UI / "scripts" / "vue-lignee.mjs").read_text(encoding="utf-8")
    assert "formesDesSujets(m.paroles.map((p) => p.sujet), m.formesPubliees)" in vue
    assert "construireExtraits(m.entrees.map(sous), debuts)" in vue
    assert "agregerParoles(m.paroles.map(sous))" in vue
