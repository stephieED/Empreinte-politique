"""Trouver les amendements d'un sujet par leur exposé, sur les fiches (#1029, voie 2).

Backend publie l'index des mots des exposés (`src/amendements_contenu.py`,
#1092). L'interface en tire, au build, le vocabulaire de chaque fiche
(`vocabulairesDesFiches`) et y cherche à l'écran (`amendementsQuiPortent`).
Ces gardes tiennent :

1. la même règle que Backend — un document produit par `document()` se lit en
   JS comme en Python, mot pour mot, y compris la fusion des formes ;
2. la fiche candidat retient un amendement dont l'exposé porte le mot, même si
   l'intitulé de son dossier ne le porte pas ;
3. la fiche de groupe recompte sa répartition amendement par amendement, par le
   mot et par la PÉRIODE, sur ses seuls types vérifiés.
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
from amendements_contenu import decoder, document, forme_indexee, mots_du_texte  # noqa: E402

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


# Des exposés à la forme de ceux de l'archive (HTML, accents, pluriels).
EXPOSES = {
    "AMANR5L17PO838901BTC3067P0D1N000001": "<p>Cet amendement baisse la TICPE sur le <b>carburant</b> des taxis.</p>",
    "AMANR5L17PO838901BTC3067P0D1N000002": "<p>Les carburants professionnels : exonération fiscale.</p>",
    "AMANR5L17PO838901BTC3067P0D1N000003": "<p>Soutien aux biocarburants agricoles et régimes fiscaux.</p>",
    "AMANR5L17PO838901BTC3067P0D1N000004": "<p>Hôpitaux : recrutement de médecins.</p>",
}
for i in range(5, 105):  # de quoi passer le seuil de fréquence
    EXPOSES[f"AMANR5L17PO838901BTC3067P0D1N{i:06d}"] = f"<p>Rédactionnel {i}.</p>"
DOC = document("17", {uid: (["Article 3", "A"], mots_du_texte(t)) for uid, t in EXPOSES.items()}, genere_le="2026-09-22")


def _python(saisie: str, uids: set[str]) -> list[str]:
    """La recherche selon Backend, restreinte à `uids`."""
    cles = set(DOC["mots"])
    retenus = None
    for mot in sorted(mots_du_texte(saisie)):
        forme = forme_indexee(mot, cles)
        ici = {DOC["prefixe_ids"] + DOC["ids"][p] for k in cles if forme in k for p in decoder(DOC["mots"][k])}
        retenus = ici if retenus is None else retenus & ici
    return sorted((retenus or set()) & uids)


@pytest.mark.parametrize("saisie", ["carburant", "carburants", "carbur", "fiscaux", "ticpe carburant", "médecins", "rédactionnel"])
def test_la_recherche_est_celle_de_backend(saisie: str) -> None:
    fiche = {uid for uid in EXPOSES if not uid.endswith("000002")}
    script = (
        f"const doc = {json.dumps(DOC)};\n"
        f"const v = f.vocabulairesDesFiches(doc, new Map([['X', new Set({json.dumps(sorted(fiche))})]])).get('X');\n"
        f"console.log(JSON.stringify([...f.amendementsQuiPortent([v], {json.dumps(saisie)})].sort()));"
    )
    assert _executer("amendementsMots.js", script) == _python(saisie, fiche)


def test_un_mot_trop_court_ne_cherche_rien() -> None:
    script = f"const doc = {json.dumps(DOC)};\nconsole.log(JSON.stringify(f.amendementsQuiPortent([f.vocabulairesDesFiches(doc, new Map([['X', new Set()]])).get('X')], 'tva')));"
    assert _executer("amendementsMots.js", script) is None


def test_la_fiche_candidat_retient_un_amendement_par_son_expose() -> None:
    pivot = {"amendements": [
        {"amendement_id": "an:AMANR5L17PO838901BTC3067P0D1N000001"},
        {"amendement_id": "an:AMANR5L17PO838901BTC3067P0D1N000004"},
    ], "votes": [], "textes_portes": [], "interventions": []}
    script = (
        f"const p = {json.dumps(pivot)};\n"
        "const lecteurs = { intituleDuVote: () => null, intituleDeLIntervention: () => null,\n"
        "  intituleDeLAmendement: () => 'Projet de loi de finances pour 2026',\n"
        "  amendementsParContenu: () => new Set(['AMANR5L17PO838901BTC3067P0D1N000001']) };\n"
        "console.log(JSON.stringify([f.filtrerProfil(p, 'carburant', lecteurs).amendements.map((a) => a.amendement_id),\n"
        "  f.filtrerProfil(p, 'finances', lecteurs).amendements.length]));"
    )
    par_expose, par_intitule = _executer("filtreIntitule.js", script)
    assert par_expose == ["an:AMANR5L17PO838901BTC3067P0D1N000001"]
    assert par_intitule == 2


def _lignee_et_table():
    uids = ["AMANR5L17PO838901BTC3067P0D1N000001", "AMANR5L17PO838901BTC3067P0D1N000003",
            "AMANR5L17PO838901BTC3067P0D1N000004"]
    script_vocab = (
        f"const doc = {json.dumps(DOC)};\n"
        f"console.log(JSON.stringify(f.vocabulairesDesFiches(doc, new Map([['M', new Set({json.dumps(uids)})]])).get('M')));"
    )
    vocab = _executer("amendementsMots.js", script_vocab)
    table = {
        "ids": ["an:" + u for u in uids],
        "types": ["depute", "commission_rapporteur"],
        "rows": [[0, 1, "2026-05-02", 0], [0, 0, "2025-01-10", 0], [1, 0, "2026-04-01", 1]],
        "textes": [["PRJLANR5L17B1906", "DLR5L17N51234", "Projet de loi de finances pour 2026", "CION_FIN", None],
                   ["PPLANR5L17B0100", "DLR5L17N50000", "Proposition de loi sur l'accès aux soins", "CION-SOC", None]],
        "vocabulaire": vocab,
    }
    lignee = {"maillons": [{
        "id": "AN-SOC-17", "sujets": {"liste": [], "total": 0}, "partageListes": {}, "textes": [], "quorum": {},
        "convergences": None, "scrutins": {},
        "amendements": {"distincts": 3, "parType": {"depute": {"amendements": 2}}},
    }]}
    return lignee, table


def test_la_fiche_de_groupe_recompte_par_l_expose_et_par_la_periode() -> None:
    lignee, table = _lignee_et_table()
    script = (
        f"const l = {json.dumps(lignee)}; const t = {{'AN-SOC-17': {json.dumps(table)}}};\n"
        "const r = (s, p, d) => { const m = f.filtrerLignee(l, s, null, p, d, null, t).maillons[0];\n"
        "  return [m.amendements.distincts, Object.keys(m.amendements.parType), m.amendementsHorsPeriode]; };\n"
        "console.log(JSON.stringify([r('carburant'), r('carburant', '6m', '2026-03-22'), r('', '6m', '2026-03-22'), r('soins')]));"
    )
    carburant, carburant6, periode_seule, soins = _executer("filtreLignee.js", script)
    assert carburant == [2, ["depute"], False]
    assert carburant6 == [1, ["depute"], False], "le seul amendement « carburant » daté dans les six mois"
    assert periode_seule == [1, ["depute"], False], "le type non vérifié au build ne revient pas"
    assert soins == [0, [], False]

