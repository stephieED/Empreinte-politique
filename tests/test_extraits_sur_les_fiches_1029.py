"""Ce qui a été dit, sur les fiches de gouvernement et de groupe (#1029).

Backend publie l'extrait de 280 caractères (#1086) et l'ancre de la prise de
parole (#1087). L'interface les lit par UNE règle, `src/utils/extraits.js`,
partagée par le build et le navigateur. Ces gardes tiennent :

1. la même règle que Backend — le lien de séance et la coupe à 280 caractères
   rendent, sur les mêmes entrées, ce que rend `schema_pivot` ;
2. le filtre par mot : un débat reste quand ses EXTRAITS portent le mot, dans
   la période cochée, même si son intitulé ne le porte pas ;
3. le débat ouvert : sous un mot que l'intitulé ne porte pas, seuls les
   extraits qui le portent se montrent ; rien n'est compté par personne.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))
from schema_pivot import extrait_de_texte, url_seance_an  # noqa: E402

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


# Identifiant copié du corpus (Lecornu II, « prix des carburants », 13/05/2026).
ENTREES_LIEN = [
    {"intervention_id": "syceron_CRSANR5L17S2026O1N232_12", "id_syceron": "4166184"},
    {"intervention_id": "syceron_CRSANR5L17S2026O1N232_12"},
    {"intervention_id": "question_QANR5L17QG1472"},
    {},
]


def test_le_lien_de_seance_est_celui_de_backend() -> None:
    js = _executer("extraits.js", f"console.log(JSON.stringify({json.dumps(ENTREES_LIEN)}.map(f.urlSeanceAn)))")
    assert js == [url_seance_an(e) for e in ENTREES_LIEN]


TEXTES = [
    "Court.",
    "Monsieur le député, " + "le Gouvernement agit sur le prix des carburants. " * 8,
    "mot " * 120,
    "a" * 400,
    "Une phrase. " + "x" * 300,
]


def test_la_coupe_a_280_caracteres_est_celle_de_backend() -> None:
    js = _executer("extraits.js", f"console.log(JSON.stringify({json.dumps(TEXTES)}.map((t) => f.extraitDeTexte(t))))")
    assert [tuple(x) for x in js] == [extrait_de_texte(t) for t in TEXTES]


ENTREES = [
    {"sujet": "questions au gouvernement", "orateur": "Maud Bregeon", "date": "2026-05-05",
     "texte": "La hausse du prix du carburant pèse sur les ménages.", "tronque": True,
     "id": "syceron_CRSANR5L17S2026O1N230_4", "ancre": "4100001"},
    {"sujet": "questions au gouvernement", "orateur": "Roland Lescure", "date": "2025-11-02",
     "texte": "Le gazole professionnel est exonéré.", "tronque": False,
     "id": "syceron_CRSANR5L17S2025O1N050_2", "ancre": None},
    {"sujet": "narcotrafic", "orateur": "Laurent Nuñez", "date": "2026-06-01",
     "texte": None, "tronque": False, "id": "syceron_CRSANR5L17S2026O1N240_1", "ancre": None},
]
DEBUTS = {"12m": "2025-09-22", "6m": "2026-03-22"}


def _index() -> dict:
    return _executer("extraits.js", f"console.log(JSON.stringify(f.construireExtraits({json.dumps(ENTREES)}, {json.dumps(DEBUTS)})))")


def test_le_vocabulaire_suit_la_periode() -> None:
    x = _index()
    tout, douze, six, paquet = x["index"]["questions au gouvernement"]
    assert "carburant" in tout and "gazole" in tout
    assert "gazole" in douze and "gazole" not in six
    assert "carburant" in six
    assert x["paquets"][paquet]["questions au gouvernement"][0][1] == "2026-05-05", "le plus récent d'abord"


def test_un_debat_reste_par_ses_extraits_dans_la_periode() -> None:
    gouvernement = {"paroles": {"liste": [
        {"label": "questions au gouvernement", "porteurs": 2},
        {"label": "narcotrafic", "porteurs": 1},
    ]}}
    x = _index()["index"]
    script = (
        f"const g = {json.dumps(gouvernement)}; const x = {json.dumps(x)};\n"
        "const r = (s, p) => f.filtrerGouvernement(g, s, x, p).paroles.liste.map((d) => [d.label, d.parIntitule]);\n"
        "console.log(JSON.stringify([r('carburant', null), r('gazole', '6m'), r('gazole', '12m'), r('narcotrafic', null), r('carburant')]));"
    )
    carburant, gazole6, gazole12, par_intitule, sans_index = _executer("filtreGouvernement.js", script)
    assert carburant == [["questions au gouvernement", False]]
    assert gazole6 == []
    assert gazole12 == [["questions au gouvernement", False]]
    assert par_intitule == [["narcotrafic", True]]
    assert sans_index == carburant


def test_le_debat_ouvert_ne_montre_que_les_extraits_qui_portent_le_mot() -> None:
    x = _index()
    k = x["index"]["questions au gouvernement"][3]
    compacts = x["paquets"][k]["questions au gouvernement"]
    script = (
        f"const c = {json.dumps(compacts)};\n"
        "console.log(JSON.stringify([\n"
        "  f.extraitsDuDebat(c, { mots: ['carburant'] }).map((e) => e.orateur),\n"
        "  f.extraitsDuDebat(c, { mots: ['carburant'], parIntitule: true }).map((e) => e.orateur),\n"
        "  f.extraitsDuDebat(c, { debut: '2026-03-22' }).map((e) => e.orateur),\n"
        "  f.extraitsDuDebat(c, {})[0].url,\n"
        "]));"
    )
    mot, par_intitule, periode, url = _executer("extraits.js", script)
    assert mot == ["Maud Bregeon"]
    assert par_intitule == ["Maud Bregeon", "Roland Lescure"]
    assert periode == ["Maud Bregeon"]
    assert url == "https://www.assemblee-nationale.fr/dyn/17/comptes-rendus/seance/CRSANR5L17S2026O1N230#4100001"


def test_la_fiche_de_groupe_filtre_aussi_par_les_extraits() -> None:
    lignee = {"maillons": [{
        "id": "AN-SOC-17", "sujets": {"liste": [{"label": "questions au gouvernement", "porteurs": 5, "denominateur": 70}], "total": 1},
        "partageListes": {}, "amendements": {"parType": {}}, "textes": [], "quorum": {}, "convergences": None, "scrutins": {},
    }]}
    x = _index()["index"]
    script = (
        f"const l = {json.dumps(lignee)}; const x = {{'AN-SOC-17': {json.dumps(x)}}};\n"
        "const r = (s) => f.filtrerLignee(l, s, null, null, null, x).maillons[0].sujets.liste.map((d) => [d.label, d.parIntitule]);\n"
        "console.log(JSON.stringify([r('carburant'), r('retraites')]));"
    )
    carburant, retraites = _executer("filtreLignee.js", script)
    assert carburant == [["questions au gouvernement", False]]
    assert retraites == []


def test_la_tete_d_un_depute_ne_porte_que_son_nom_et_ses_dates() -> None:
    """Fiche de groupe, forme A : les propos sont RANGÉS par député (demande du
    22/09/2026), jamais COMPTÉS — la tête ne porte ni nombre ni rang."""
    source = (RACINE / "web" / "UI_finale" / "src" / "components" / "ExtraitsDuDebat.jsx").read_text(encoding="utf-8")
    debut = source.index('<div className="xd-membre-tete">')
    tete = source[debut:source.index("</div>", debut)]
    assert "nomDe(o.orateur)" in tete and "o.premiere" in tete
    assert "length" not in tete and "formatNumber" not in tete
