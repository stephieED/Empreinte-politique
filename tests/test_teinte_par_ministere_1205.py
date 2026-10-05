"""Une teinte par ministère, la même dans trois sections de la fiche de gouvernement.

Forme A, retenue par la propriétaire le 04/10/2026. Les entrées ci-dessous sont
COPIÉES de `pivot_data/gouvernements/gouvernement-BORNE.json` (`main` 07d094cbf) :
six mandats de `membres[]` et les `initiateurs` de deux dossiers, tels que la
source les écrit — apostrophes typographiques comprises.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "web" / "UI_finale"
REGLE = UI / "src" / "utils" / "ministere.js"

ECO = "Ministère de l’économie, des finances et de la souveraineté industrielle et numérique"
COMPTES = (
    "Ministère auprès du ministre de l’économie, des finances et de la souveraineté "
    "industrielle et numérique, chargé des comptes publics"
)
AGRI = "Ministère de l’agriculture et de la souveraineté alimentaire"

MEMBRES = [
    {"membre_id": "bruno-le-maire", "nom": "Bruno Le Maire", "portefeuille": ECO, "debut": "2022-05-21", "fin": "2024-01-09"},
    {"membre_id": "elisabeth-borne", "nom": "Élisabeth Borne", "portefeuille": "Première ministre", "debut": "2022-05-17", "fin": "2024-01-09"},
    {"membre_id": "eric-dupond-moretti", "nom": "Éric Dupond-Moretti", "portefeuille": "Ministère de la justice", "debut": "2022-05-21", "fin": "2024-01-09"},
    {"membre_id": "gabriel-attal", "nom": "Gabriel Attal", "portefeuille": COMPTES, "debut": "2022-05-21", "fin": "2023-07-20"},
    {"membre_id": "gabriel-attal", "nom": "Gabriel Attal", "portefeuille": "Ministère de l’éducation nationale et de la jeunesse", "debut": "2023-07-21", "fin": "2024-01-09"},
    {"membre_id": "marc-fesneau", "nom": "Marc Fesneau", "portefeuille": AGRI, "debut": "2022-05-21", "fin": "2024-01-09"},
]
PM = {"membre_id": "elisabeth-borne", "portefeuille": "Première ministre"}
#: DLR5L16N47569 : la Première ministre, le ministre de l'économie et son ministre délégué.
BUDGET = {"initiateurs": [PM, {"membre_id": "bruno-le-maire", "portefeuille": ECO}, {"membre_id": "gabriel-attal", "portefeuille": COMPTES}]}
#: DLR5L16N46008 : la Première ministre et le ministre de l'agriculture.
AGRICOLE = {"initiateurs": [PM, {"membre_id": "marc-fesneau", "portefeuille": AGRI}]}
SEULE = {"initiateurs": [PM]}
DEUX = {"initiateurs": [PM, {"portefeuille": ECO}, {"portefeuille": AGRI}]}


def _regle(corps: str):
    script = f"""
      import * as M from './src/utils/ministere.js';
      const gouvernement = {{ membres: {json.dumps(MEMBRES, ensure_ascii=False)}, premierMinistre: 'Élisabeth Borne',
        periode: {{ debut: '2022-05-17', fin: '2024-01-09' }} }};
      const poles = M.polesDuGouvernement(gouvernement);
      const textes = {json.dumps([BUDGET, AGRICOLE, SEULE, DEUX], ensure_ascii=False)};
      const teintes = M.teintesDesMinisteres(poles, textes);
      const [budget, agricole, seule, deux] = textes;
      console.log(JSON.stringify({corps}));
    """
    sortie = subprocess.run(
        ["node", "--input-type=module", "-e", script], capture_output=True, text=True, cwd=UI, check=False,
    )
    assert sortie.returncode == 0, sortie.stderr
    return json.loads(sortie.stdout)


def test_un_ministre_delegue_rejoint_le_ministere_que_son_titre_nomme() -> None:
    """Aucune table écrite à la main : « auprès du ministre de l'économie… » suit la règle des cartes."""
    r = _regle("{ budget: M.clesDuTexte(poles, budget), agricole: M.clesDuTexte(poles, agricole), "
               "seule: M.clesDuTexte(poles, seule), acte: M.poleDuLibelle(poles, \"Ministère de l'agriculture et de la souveraineté alimentaire\")?.cle }")
    assert len(r["budget"]) == 1 and r["budget"][0].startswith("economie"), "le délégué et son ministre : un seul ministère"
    assert len(r["agricole"]) == 1 and r["agricole"][0].startswith("agriculture")
    assert r["seule"] == [], "le Premier ministre signe tous les projets : il ne compte pas"
    assert r["acte"] == r["agricole"][0], "le libellé d'un acte (apostrophe droite) rejoint la même carte"


def test_chaque_ministere_a_sa_teinte_et_le_premier_ministre_aucune() -> None:
    r = _regle("{ teintes: [...teintes], pm: poles.find((p) => p.pm)?.cle, palette: M.PALETTE_MINISTERES }")
    cles = [c for c, _ in r["teintes"]]
    couleurs = [t for _, t in r["teintes"]]
    assert r["pm"] not in cles
    assert len(couleurs) == len(set(couleurs)) == 4, "économie, justice, éducation, agriculture : quatre teintes distinctes"
    assert len(r["palette"]) == len(set(r["palette"])) == 24
    assert set(couleurs) <= set(r["palette"])


def test_la_teinte_suit_le_nom_et_non_le_rang() -> None:
    """Retirer un ministère de la fiche ne déplace pas la teinte des autres."""
    script_sans = "(() => { const g2 = { ...gouvernement, membres: gouvernement.membres.filter((m) => m.membre_id !== 'marc-fesneau') }; " \
                  "const p2 = M.polesDuGouvernement(g2); return Object.fromEntries(M.teintesDesMinisteres(p2, [budget])); })()"
    r = _regle("{ avec: Object.fromEntries(teintes), sans: %s }" % script_sans)
    for cle, teinte in r["sans"].items():
        assert r["avec"][cle] == teinte, cle


def test_un_projet_a_plusieurs_ministeres_est_un_carre_en_bandes_et_sans_ministere_un_carre_gris() -> None:
    r = _regle("{ un: M.fondDuTexte(poles, teintes, agricole), deux: M.fondDuTexte(poles, teintes, deux), "
               "seule: M.fondDuTexte(poles, teintes, seule), gris: M.GRIS_SANS_MINISTERE, t: Object.fromEntries(teintes) }")
    assert r["un"] in r["t"].values()
    assert r["deux"].startswith("linear-gradient(135deg, ") and "50.0%" in r["deux"]
    assert sum(t in r["deux"] for t in r["t"].values()) == 2, "une bande par ministère, aucun choisi à la place de l'autre"
    assert r["seule"] == r["gris"]


def test_au_dela_de_vingt_quatre_ministeres_les_projets_de_loi_passent_d_abord() -> None:
    script = """
      import * as M from './src/utils/ministere.js';
      const mot = (k) => `q${String.fromCharCode(97 + Math.floor(k / 26))}${String.fromCharCode(97 + (k % 26))}`;
      const poles = Array.from({ length: 30 }, (_, k) => ({ cle: `${mot(k)} domaine`, titre: `Ministère ${mot(k)} domaine` }));
      const dernier = { initiateurs: [{ portefeuille: `Ministère ${mot(29)} domaine` }] };
      const t = M.teintesDesMinisteres(poles, [dernier]);
      console.log(JSON.stringify({ n: t.size, dernier: t.has(`${mot(29)} domaine`), distinctes: new Set(t.values()).size }));
    """
    sortie = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, cwd=UI, check=False)
    assert sortie.returncode == 0, sortie.stderr
    r = json.loads(sortie.stdout)
    assert r == {"n": 24, "dernier": True, "distinctes": 24}


def test_les_trois_sections_lisent_la_meme_table() -> None:
    fiche = (UI / "src" / "components" / "GovernmentProfile.jsx").read_text(encoding="utf-8")
    actes = (UI / "src" / "components" / "ActesDuGouvernement.jsx").read_text(encoding="utf-8")
    assert fiche.count("= useMinisteres(government);") == 3, "composition, projets de loi, actes"
    assert "teinte={teintes.get(pole.cle) || null}" in fiche
    assert "fondDuTexte(poles, teintes, t)" in fiche
    assert "teintes.get(poleDuLibelle(poles, l.nom)?.cle)" in actes
    assert "initiateurs: t.initiateurs || []" in (UI / "src" / "data" / "pivotAdapter.js").read_text(encoding="utf-8")
