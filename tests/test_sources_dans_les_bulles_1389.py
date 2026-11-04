"""Le pied de source des bulles de section, sur les quatre fiches (#1389).

Chaque bulle se termine par une ligne par source qui alimente la section : le
nom de la source tel que le schéma de la page Sources l'écrit, en lien, et
« à jour au JJ/MM/AAAA » (forme B du 29/10/2026 ; « à jour au », la dernière
relecture RÉUSSIE, arbitré le même jour). La date est lue dans
`fraicheur_sources.json`, famille par famille, et non plus dans
`sources[].synchro_le` du profil, qui dit quand la donnée a changé. Ces gardes
tiennent :

1. le nom est celui du schéma, à la lettre, et l'ordre est celui du schéma ;
2. la date `a_jour_au` (« 2026-11-03 ») se lit telle quelle, sans glisser d'un
   jour ;
3. plusieurs familles d'une même source dans une bulle : une ligne, à la date
   de la plus ancienne ; une source entière vaut toutes ses familles ;
4. une famille en échec garde sa dernière date réussie ; une famille sans date
   n'a pas de ligne — aucune date inventée (§2 règle 5) ;
   une source absente de la fiche de la personne n'a pas de ligne ;
5. chaque bulle des quatre fiches déclare ses sources (sauf celle des budgets,
   dont la source n'a pas d'entrée sur la page Sources), chaque fiche pose
   ses dates, et chaque famille nommée est une famille qu'écrit
   `src/fraicheur_sources.py` ;
6. le libellé est « à jour au », jamais « mis à jour le » ni « consulté » ;
7. `sync-data` copie le fichier pour le site.

`FRAICHEUR` est un extrait de `pivot_data/fraicheur_sources.json` (run du
03/11/2026), dont trois dates ont été vieillies pour que les cas se
distinguent.
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
BULLE = UI / "components" / "InfoBulle.jsx"
SYNC = RACINE / "web" / "UI_finale" / "scripts" / "sync-data.mjs"


def _famille(a_jour_au, etat="a_jour", en_echec_depuis=None):
    return {"a_jour_au": a_jour_au, "etat": etat, "en_echec_depuis": en_echec_depuis}


FRAICHEUR = {
    "schema_version": "fraicheur-sources-v1",
    "genere_le": "2026-11-03",
    "familles": {
        "an.mandats": _famille("2026-11-03"),
        "an.gouvernements": _famille("2026-11-03"),
        "an.votes": _famille("2026-11-03"),
        "an.interventions": _famille("2026-11-03"),
        "an.questions": _famille("2026-11-01"),
        "an.dossiers": _famille("2026-11-02"),
        "an.amendements": _famille("2026-11-02"),
        "sen.mandats": _famille("2026-10-28", "en_echec", "2026-10-29"),
        "pe.mandats": _famille("2026-11-02"),
        "pe.documents": _famille("2026-11-03"),
        "pt.votes": _famille("2026-11-02"),
        "pt.textes": _famille("2026-11-02"),
        "rne.mandats_locaux": _famille(None, "non_relue"),
    },
}


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


def _lignes(demandees, fraicheur=FRAICHEUR):
    return _node(
        f"const d = f.datesDesFamilles({json.dumps(fraicheur)});\n"
        f"console.log(JSON.stringify(f.lignesDeSources({json.dumps(demandees)}, d)));"
    )


def test_le_nom_est_celui_du_schema_et_l_ordre_aussi():
    lignes = _lignes(["pt.votes", "an.votes", "pe.mandats"])
    assert [l["nom"] for l in lignes] == ["Assemblée nationale (données)", "Parlement européen", "ParlTrack"]
    assert [l["url"] for l in lignes] == [
        "https://data.assemblee-nationale.fr/", "https://data.europarl.europa.eu/", "https://parltrack.org/"]


def test_chaque_source_des_familles_a_sa_place_dans_le_schema():
    manquants = _node(
        "const ids = new Set(s.SOURCES_SCHEMA.map((x) => x.id));\n"
        "console.log(JSON.stringify(Object.keys(f.FAMILLES_PAR_SOURCE).filter((i) => !ids.has(i))));"
    )
    assert manquants == []


def test_une_page_plus_precise_remplace_l_accueil_de_la_source():
    lignes = _lignes([{"id": "an.interventions", "url": "https://exemple.fr/debats"}, "an.questions"])
    assert lignes[0]["url"] == "https://exemple.fr/debats"


def test_la_date_se_lit_telle_quelle():
    assert [l["date"] for l in _lignes(["an.votes", "pt.votes"])] == ["03/11/2026", "02/11/2026"]


def test_plusieurs_familles_d_une_source_la_plus_ancienne_l_emporte():
    assert [l["date"] for l in _lignes(["an.interventions", "an.questions"])] == ["01/11/2026"]
    # Une source entière vaut toutes ses familles : la plus ancienne de l'AN.
    assert [l["date"] for l in _lignes(["an"])] == ["01/11/2026"]


def test_une_famille_en_echec_garde_sa_derniere_date_reussie():
    assert [(l["id"], l["date"]) for l in _lignes(["sen.mandats"])] == [("sen", "28/10/2026")]


def test_sans_date_pas_de_ligne():
    assert [l["id"] for l in _lignes(["an.mandats", "rne.mandats_locaux"])] == ["an"]
    assert _lignes(["pt.interventions"]) == []  # famille absente du fichier
    assert _lignes(["an.votes"], fraicheur=None) == []
    assert _lignes([]) == []


def test_une_source_absente_de_la_fiche_n_a_pas_de_ligne():
    """Attal n'a siégé ni au Sénat ni au Parlement européen (profil du 28/10/2026)."""
    attal = [{"type": "assemblee_nationale"}, {"type": "rne"}]
    lignes = _node(
        f"const d = f.datesDesFamilles({json.dumps(FRAICHEUR)});\n"
        f"const p = f.sourcesDuProfil({json.dumps(attal)});\n"
        "console.log(JSON.stringify(f.lignesDeSources("
        "['an.mandats', 'sen.mandats', 'pe.mandats', 'rne.mandats_locaux'], d, p)));"
    )
    assert [l["id"] for l in lignes] == ["an"]  # rne sans date dans l'extrait


def test_chaque_type_du_profil_a_sa_place_dans_le_schema():
    manquants = _node(
        "const ids = new Set(s.SOURCES_SCHEMA.map((x) => x.id));\n"
        "console.log(JSON.stringify(Object.values(f.TYPE_VERS_SCHEMA).filter((i) => !ids.has(i))));"
    )
    assert manquants == []


COMPOSANTS = UI / "components"
PAGES = UI / "pages"
#: Les quatre fiches et la page qui pose leurs dates (#1389, 04/11/2026).
FICHES = {
    "CandidateProfile.jsx": "CandidateProfile.jsx",
    "LigneeProfile.jsx": "GroupProfilePage.jsx",
    "GovernmentProfile.jsx": "GovernmentProfilePage.jsx",
    "LegislatureProfile.jsx": "LegislatureProfilePage.jsx",
}
#: Les bulles sans pied, et pourquoi : leur source n'a pas d'entrée sur la
#: page Sources, donc pas de nom à afficher.
SANS_PIED: dict[str, int] = {}


def _bloc_des_bulles(fiche: str = "CandidateProfile.jsx") -> str:
    texte = (COMPOSANTS / fiche).read_text(encoding="utf-8")
    debut = texte.index("const BULLES = {")
    return texte[debut:texte.index("\n};", debut)]


@pytest.mark.parametrize("fiche", sorted(FICHES))
def test_chaque_bulle_de_chaque_fiche_declare_ses_sources(fiche):
    bloc = _bloc_des_bulles(fiche)
    phrases = len(re.findall(r"^\s+phrase:", bloc, re.M))
    assert phrases - len(re.findall(r"^\s+sources:", bloc, re.M)) == SANS_PIED.get(fiche, 0)


@pytest.mark.parametrize("fiche", sorted(FICHES))
def test_chaque_fiche_pose_les_dates_de_ses_bulles(fiche):
    page = FICHES[fiche]
    texte = ((COMPOSANTS if page == fiche else PAGES) / page).read_text(encoding="utf-8")
    assert "<PiedDesBulles" in texte


def test_chaque_famille_nommee_existe_dans_le_fichier_publie():
    """Une faute de frappe (« an.vote ») ôterait la ligne sans bruit. Les
    familles sont celles qu'écrit `src/fraicheur_sources.py` : aucun test ne
    lit `pivot_data/` (tests.yml)."""
    import sys

    sys.path.insert(0, str(RACINE / "src"))
    from fraicheur_sources import FAMILLES

    connues = set(FAMILLES)
    nommees = set()
    for fiche in FICHES:
        nommees |= set(re.findall(r"'([a-z]+\.[a-z_]+)'", _bloc_des_bulles(fiche)))
    nommees |= set(_node("console.log(JSON.stringify(Object.values(f.FAMILLES_PAR_SOURCE).flat()))"))
    assert nommees and nommees <= connues, sorted(nommees - connues)


def test_le_lien_de_source_des_paroles_est_passe_dans_le_pied():
    assert "La source : les comptes rendus" not in _bloc_des_bulles()


def test_le_libelle_est_a_jour_au():
    texte = BULLE.read_text(encoding="utf-8")
    assert "à jour au {l.date}" in texte
    assert "mis à jour le" not in texte
    assert "consulté" not in texte.lower()


def test_sync_data_copie_le_fichier_pour_le_site():
    texte = SYNC.read_text(encoding="utf-8")
    assert "'fraicheur_sources.json'" in texte


# ── L'état de chaque source sur la page Sources (forme A, 04/11/2026) ────────


def test_l_etat_d_une_source_reunit_ses_familles():
    etats = _node(f"console.log(JSON.stringify(f.etatDesSources({json.dumps(FRAICHEUR)})))")
    # La plus ancienne relecture réussie de l'AN (an.questions, au 01/11).
    assert etats["an"] == {"aJourAu": "2026-11-01", "enEchecDepuis": None}
    # Une famille en échec garde sa dernière date réussie, et dit depuis quand.
    assert etats["sen"] == {"aJourAu": "2026-10-28", "enEchecDepuis": "2026-10-29"}
    # Sans aucune date, pas d'état : on n'invente rien.
    assert "rne" not in etats


def test_les_budgets_se_rangent_sous_leurs_sources():
    fr = {"familles": {"budget_etat": _famille("2026-11-03"), "drees": _famille("2026-11-02"),
                       "unedic": _famille("2026-11-01")}}
    etats = _node(f"console.log(JSON.stringify(f.etatDesSources({json.dumps(fr)})))")
    assert {k: v["aJourAu"] for k, v in etats.items()} == {
        "mef": "2026-11-03", "drees": "2026-11-02", "unedic": "2026-11-01"}


def test_la_fiche_de_la_source_porte_a_jour_au():
    texte = (COMPOSANTS / "SchemaSources.jsx").read_text(encoding="utf-8")
    assert "<dt>À jour au</dt>" in texte
    assert "Les mises à jour échouent depuis le " in texte
    assert texte.count("etat={etats[") == 2  # la bulle à la souris et la bande au doigt
