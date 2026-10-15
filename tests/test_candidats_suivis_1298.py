"""Les candidats suivis, sur la page Sources (#1298).

La page dit qui le site compte comme candidat, et sur quelle source : un seul
tableau (forme A, 15/10/2026), candidatures retirées comprises. Ces gardes
tiennent :

1. l'ordre est celui du nom affiché, jamais un classement (§2 règle 1) ;
2. une date absente reste absente, jamais devinée (§2 règle 5), et une date au
   mois seul ne gagne pas de jour ;
3. toutes les sources relues sont affichées, et une entrée non relue retombe
   sur sa seule `source` ;
4. une candidature retirée garde son slug, mais sa fiche est masquée : pas de
   lien vers une page absente.

Les entrées sont copiées de `raw_data/candidats.json` (PR #1297 et #1301),
réduites aux champs lus.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
MODULE = RACINE / "web" / "UI_finale" / "src" / "utils" / "candidatsSuivis.js"
PAGE = RACINE / "web" / "UI_finale" / "src" / "pages" / "CoveragePage.jsx"

CANDIDATS = [
    {"nom": "Nathalie Arthaud", "slug": "nathalie-arthaud", "statut": "declare",
     "date_declaration": "2025-12",
     "source": "https://election-presidentielle-francaise-2027.fr/les-candidats-declares/",
     "sources": [
         {"url": "https://election-presidentielle-francaise-2027.fr/les-candidats-declares/",
          "media": "election-presidentielle-francaise-2027.fr", "date": None},
         {"url": "https://www.nouvelobs.com/politique/20261015.OBS119225/presidentielle-2027-quels-sont-les-31-candidats-actuellement-declares.html",
          "media": "Le Nouvel Obs", "date": "2026-10-15"},
     ]},
    {"nom": "Ségolène Royal", "slug": "segolene-royal", "statut": "decline",
     "date_declaration": "2026-07-10",
     "source": "https://www.nouvelobs.com/politique/20261015.OBS119225/presidentielle-2027-quels-sont-les-31-candidats-actuellement-declares.html"},
    {"nom": "Gilles Platret", "slug": None, "statut": "declare",
     "date_declaration": "2026-10-08",
     "source": "https://www.franceinfo.fr/elections/presidentielle/portraits-qui-sont-les-candidats-declares-a-l-election-presidentielle-de-2027_8208032.html"},
    {"nom": "François Asselineau", "slug": "francois-asselineau", "statut": "declare",
     "date_declaration": "2023-08-31", "source": "https://www.nouvelobs.com/a"},
    {"nom": "Jean-Luc Mélenchon", "slug": "jean-luc-melenchon", "statut": "declare",
     "date_declaration": None, "source": "https://lcp.fr/b"},
    {"nom": "Édouard Philippe", "slug": "edouard-philippe", "statut": "declare",
     "date_declaration": "2025-04-01", "source": "https://lcp.fr/c"},
]
# Le manifeste ne liste ni Royal (retirée, masquée) ni Platret (sans profil).
PUBLIEES = ["nathalie-arthaud", "francois-asselineau", "jean-luc-melenchon", "edouard-philippe"]


def _lignes() -> list[dict]:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        f"const f = await import({json.dumps(MODULE.as_uri())});\n"
        f"const l = f.lignesCandidats({json.dumps(CANDIDATS)}, new Set({json.dumps(PUBLIEES)}));\n"
        "console.log(JSON.stringify(l));"
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_ordre_du_nom_affiche_jamais_un_classement():
    noms = [l["nom"] for l in _lignes()]
    assert noms == ["Édouard Philippe", "François Asselineau", "Gilles Platret",
                    "Jean-Luc Mélenchon", "Nathalie Arthaud", "Ségolène Royal"]


def test_une_date_absente_reste_absente_et_un_mois_ne_gagne_pas_de_jour():
    par_nom = {l["nom"]: l for l in _lignes()}
    assert par_nom["Jean-Luc Mélenchon"]["declaration"] is None
    assert par_nom["Nathalie Arthaud"]["declaration"] == "décembre 2025"
    assert par_nom["Édouard Philippe"]["declaration"] == "1er avril 2025"
    assert par_nom["François Asselineau"]["declaration"] == "31 août 2023"


def test_toutes_les_sources_relues_et_le_repli_sur_la_seule_source():
    par_nom = {l["nom"]: l for l in _lignes()}
    assert [s["media"] for s in par_nom["Nathalie Arthaud"]["sources"]] == [
        "election-presidentielle-francaise-2027.fr", "Le Nouvel Obs"]
    assert par_nom["Nathalie Arthaud"]["sources"][1]["date"] == "2026-10-15"
    assert [s["media"] for s in par_nom["Gilles Platret"]["sources"]] == ["franceinfo.fr"]


def test_pas_de_lien_vers_une_fiche_masquee_ou_absente():
    par_nom = {l["nom"]: l for l in _lignes()}
    assert par_nom["Ségolène Royal"]["fiche"] is None
    assert par_nom["Ségolène Royal"]["statut"] == "Retirée"
    assert par_nom["Gilles Platret"]["fiche"] is None
    assert par_nom["Nathalie Arthaud"]["fiche"] == "nathalie-arthaud"


def test_la_page_affiche_la_section():
    source = PAGE.read_text(encoding="utf-8")
    assert "<CandidatsSuivis />" in source
    assert "Les candidats suivis" in source


def test_la_mention_de_l_accueil_mene_au_tableau():
    accueil = (RACINE / "web" / "UI_finale" / "src" / "components" / "landing"
               / "CommencerAExplorer.jsx").read_text(encoding="utf-8")
    assert 'to="/sources#candidats"' in accueil
