"""Une fiche de candidat ne lit que ses amendements (#1273).

Mesuré le 09/10/2026 sur le site en ligne : la fiche de François Ruffin restait
blanche de 10 à 14 secondes, parce qu'elle téléchargeait l'index entier des
amendements des XVe, XVIe et XVIIe législatures — 587 667 entrées, 162 Mo de
JSON — pour en joindre 48 786. `sync-data` écrit désormais un extrait par
candidat, de même forme que l'index.

CE QUE CES TESTS NE COUVRENT PAS : ils ne construisent aucune fiche et ne
mesurent aucun temps de chargement. Les entrées sont copiées de
`pivot_data/amendements/17.json` (`main` f831b89c7).
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "src" / "utils" / "extraitAmendements.js"

#: Deux amendements que le profil de François Ruffin référence, un qu'il ne
#: référence pas, et les textes visés (celui de l'autre député est écrit ici, pas copié).
SIEN_1 = "an:AMANR5L17PO838901BTC3018P0D1N001222"
SIEN_2 = "an:AMANR5L17PO838901BTC3018P0D1N001202"
AUTRE = "an:AMANR5L17PO419604B0118P0D1N000001"
INDEX = {
    "amendements": {
        SIEN_1: {"texte_vise": "PRJLANR5L17BTC3018", "sort": "irrecevable", "base_juridique_irrecevabilite": "art. 45",
                 "premier_signataire": "an:PA841885", "type_deposant": "depute", "date": "2026-07-16",
                 "numero": "1222", "source_url": None, "article": ["Article 10", "A"]},
        SIEN_2: {"texte_vise": "PRJLANR5L17BTC3018", "sort": "adopté", "base_juridique_irrecevabilite": None,
                 "premier_signataire": "an:PA841885", "type_deposant": "depute", "date": "2026-07-15",
                 "numero": "1202", "source_url": None, "article": ["Article 5", "A"]},
        AUTRE: {"texte_vise": "PIONANR5L17B0118", "sort": "non_soutenu", "base_juridique_irrecevabilite": None,
                "premier_signataire": "an:PA722284", "type_deposant": "commission_rapporteur", "date": "2024-12-04",
                "numero": "AC1", "source_url": None, "article": ["Article PREMIER", "A"]},
    },
    "textes": {
        "PRJLANR5L17BTC3018": {"dossier_id": "DLR5L17N54372", "titre": "Projet de loi relatif à la protection des enfants"},
        "PIONANR5L17B0118": {"dossier_id": "DLR5L17N50338", "titre": "Texte visé par l'amendement d'un autre député"},
    },
}


def _extrait(index, ids):
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = "const m = await import(%r);\nprocess.stdout.write(JSON.stringify(m.extraitDesAmendements(%s, %s)));" % (
        MODULE.as_uri(), json.dumps(index), json.dumps(ids))
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_l_extrait_ne_porte_que_les_amendements_du_profil_et_leurs_textes() -> None:
    extrait = _extrait(INDEX, [SIEN_1, SIEN_2])
    assert set(extrait["amendements"]) == {SIEN_1, SIEN_2}
    assert set(extrait["textes"]) == {"PRJLANR5L17BTC3018"}


def test_chaque_entree_est_celle_de_l_index_sans_rien_perdre() -> None:
    """La fiche joint l'extrait comme elle joignait l'index : mêmes champs, mêmes valeurs."""
    extrait = _extrait(INDEX, [SIEN_1])
    assert extrait["amendements"][SIEN_1] == INDEX["amendements"][SIEN_1]
    assert extrait["textes"]["PRJLANR5L17BTC3018"] == INDEX["textes"]["PRJLANR5L17BTC3018"]


def test_un_amendement_absent_de_l_index_reste_absent() -> None:
    """Jamais une entrée inventée : la vue en fait une donnée manquante (§2 règle 5)."""
    extrait = _extrait(INDEX, [SIEN_1, "an:AMANR5L17PO000000B0000P0D1N000000"])
    assert set(extrait["amendements"]) == {SIEN_1}


def test_un_texte_vise_hors_de_la_table_ne_casse_pas_l_extrait() -> None:
    """Mesuré sur François Ruffin : 9 de ses 12 604 amendements de la XVIIe visent un texte que la table ne porte pas."""
    index = {"amendements": {SIEN_1: INDEX["amendements"][SIEN_1]}, "textes": {}}
    extrait = _extrait(index, [SIEN_1])
    assert set(extrait["amendements"]) == {SIEN_1}
    assert extrait["textes"] == {}


def test_la_construction_ecrit_l_extrait_et_la_fiche_le_lit() -> None:
    """Les deux bouts tiennent ensemble : un nom de fichier changé d'un seul côté rendrait des fiches sans amendements."""
    sync = (UI / "scripts" / "sync-data.mjs").read_text(encoding="utf-8")
    lecture = (UI / "src" / "data" / "index.js").read_text(encoding="utf-8")
    assert "extraitDesAmendements" in sync
    assert ".amendements.json`" in sync
    assert "/data/profiles/${slug}.amendements.json" in lecture
