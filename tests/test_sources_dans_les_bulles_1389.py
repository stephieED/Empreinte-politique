"""Le pied de source des bulles de section, sur la fiche candidat (#1389).

Chaque bulle se termine par une ligne par source qui alimente la section : le
nom de la source tel que le schéma de la page Sources l'écrit, en lien, et
« mis à jour le JJ/MM/AAAA » (forme B et mots arrêtés par la propriétaire le
29/10/2026). Ces gardes tiennent :

1. le nom est celui du schéma, à la lettre, et l'ordre est celui du schéma ;
2. la date est lue en heure de Paris : une relecture à 23 h 58 UTC tombe le
   lendemain ; une date sans fuseau (ParlTrack) se lit en UTC ;
3. deux entrées du même type : la plus ancienne l'emporte ;
4. une source sans date lisible, ou d'un type absent du schéma, n'a pas de
   ligne — aucune date inventée (§2 règle 5) ;
5. chaque bulle de la fiche candidat déclare ses sources ;
6. le libellé est « mis à jour le », jamais « consulté ».

Les entrées `sources[]` sont copiées de `pivot_data/profiles/` (Emmanuel
Maurel et Gabriel Attal, run du 28/10/2026).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
MODULE = UI / "utils" / "sourcesDesBulles.js"
SCHEMA = UI / "data" / "schemaSources.js"
FICHE = UI / "components" / "CandidateProfile.jsx"
BULLE = UI / "components" / "InfoBulle.jsx"

MAUREL = [
    {"type": "assemblee_nationale", "url": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA842271",
     "synchro_le": "2026-10-28T18:07:48+0000"},
    {"type": "europarl", "url": "https://www.europarl.europa.eu/meps/fr/24505",
     "synchro_le": "2026-10-28T18:08:00+0000"},
    {"type": "parltrack", "url": "https://parltrack.org/dumps", "synchro_le": "2026-10-15T06:42:09"},
]
ATTAL = [
    {"type": "assemblee_nationale", "url": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA722190",
     "synchro_le": "2026-10-28T18:05:28+0000"},
    {"type": "rne", "url": "https://www.data.gouv.fr/datasets/repertoire-national-des-elus-1",
     "synchro_le": "2026-10-25T17:26:13+0000"},
]


def _node(script: str):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    entete = (
        f"const f = await import({json.dumps(MODULE.as_uri())});\n"
        f"const s = await import({json.dumps(SCHEMA.as_uri())});\n"
    )
    res = subprocess.run(["node", "--input-type=module", "-e", entete + script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def _lignes(sources, demandees):
    return _node(
        f"const d = f.datesDesSources({json.dumps(sources)});\n"
        f"console.log(JSON.stringify(f.lignesDeSources({json.dumps(demandees)}, d)));"
    )


def test_le_nom_est_celui_du_schema_et_l_ordre_aussi():
    lignes = _lignes(MAUREL, ["pt", "an", "pe"])
    assert [l["nom"] for l in lignes] == ["Assemblée nationale (données)", "Parlement européen", "ParlTrack"]
    assert [l["url"] for l in lignes] == [
        "https://data.assemblee-nationale.fr/", "https://data.europarl.europa.eu/", "https://parltrack.org/"]


def test_chaque_type_connu_a_sa_place_dans_le_schema():
    manquants = _node(
        "const ids = new Set(s.SOURCES_SCHEMA.map((x) => x.id));\n"
        "console.log(JSON.stringify(Object.values(f.TYPE_VERS_SCHEMA).filter((i) => !ids.has(i))));"
    )
    assert manquants == []


def test_une_page_plus_precise_remplace_l_accueil_de_la_source():
    lignes = _lignes(MAUREL, [{"id": "an", "url": "https://exemple.fr/debats"}])
    assert lignes[0]["url"] == "https://exemple.fr/debats"


def test_la_date_se_lit_a_paris_et_sans_fuseau_en_utc():
    assert [l["date"] for l in _lignes(MAUREL, ["an", "pt"])] == ["28/10/2026", "15/10/2026"]
    tard = [{"type": "assemblee_nationale", "synchro_le": "2026-10-26T23:58:14+0000"},
            {"type": "parltrack", "synchro_le": "2026-10-26T23:58:14"}]
    assert [l["date"] for l in _lignes(tard, ["an", "pt"])] == ["27/10/2026", "27/10/2026"]


def test_deux_entrees_du_meme_type_la_plus_ancienne_l_emporte():
    deux = [{"type": "assemblee_nationale", "synchro_le": "2026-10-28T18:07:48+0000"},
            {"type": "assemblee_nationale", "synchro_le": "2026-10-26T18:43:34+0000"}]
    assert _lignes(deux, ["an"])[0]["date"] == "26/10/2026"


def test_sans_date_ou_hors_schema_pas_de_ligne():
    sources = ATTAL + [{"type": "senat", "synchro_le": None},
                       {"type": "senat", "synchro_le": "pas une date"},
                       {"type": "wikipedia", "synchro_le": "2026-10-28T18:00:00+0000"}]
    assert [l["id"] for l in _lignes(sources, ["an", "sen", "pe", "rne"])] == ["an", "rne"]
    assert _lignes([], ["an"]) == []
    assert _lignes(MAUREL, []) == []


def _bloc_des_bulles() -> str:
    texte = FICHE.read_text(encoding="utf-8")
    debut = texte.index("const BULLES = {")
    return texte[debut:texte.index("\n};", debut)]


def test_chaque_bulle_de_la_fiche_candidat_declare_ses_sources():
    bloc = _bloc_des_bulles()
    assert len(re.findall(r"^\s+phrase:", bloc, re.M)) == len(re.findall(r"^\s+sources:", bloc, re.M))


def test_le_lien_de_source_des_paroles_est_passe_dans_le_pied():
    assert "La source : les comptes rendus" not in _bloc_des_bulles()


def test_le_libelle_est_mis_a_jour_jamais_consulte():
    texte = BULLE.read_text(encoding="utf-8")
    assert "mis à jour le {l.date}" in texte
    assert "consulté" not in texte.lower()
