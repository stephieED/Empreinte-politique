"""#1019 — l'archive de la XIVe législature est monolithique, pas incompatible.

`couverture_dossiers.py` écrivait qu'elle n'a « aucun `dossierParlementaire` ».
Mesuré le 18/09/2026 sur l'archive réelle : elle en porte **3 432**, chacun sous
cette clé exactement comme dans le format par fichier. Seul l'emballage change —
un seul JSON de 36 Mo décompressés au lieu d'un fichier par objet.

Les fixtures de ce fichier reproduisent les DEUX formes réelles, relevées sur
les archives téléchargées le même jour :

  - par fichier (XV-XVII) : `json/dossierParlementaire/<uid>.json`, l'uid dans
    le NOM DE FICHIER, l'objet sous la clé `dossierParlementaire` ;
  - monolithique (XIV) : un `.json` unique, `export.dossiersLegislatifs.dossier[]`
    dont chaque entrée est `{"dossierParlementaire": {...}}`, et
    `export.textesLegislatifs.document[]` dont chaque entrée est l'objet NU.

Cette asymétrie d'emballage entre les deux collections est la seule subtilité du
format, et c'est elle que `_COLLECTIONS_MONOLITHE` encode.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from gouvernement_textes import (  # noqa: E402
    _entrees_monolithiques,
    iter_documents_bruts,
    iter_dossiers_bruts,
)


def _dossier(uid: str, titre: str = "Projet de loi test") -> dict:
    return {"uid": uid, "legislature": "14", "titreDossier": {"titre": titre}}


def _zip_par_fichier(chemin: Path, dossiers: list[dict]) -> Path:
    """La forme des archives XV à XVII : un fichier par objet."""
    with zipfile.ZipFile(chemin, "w") as zf:
        for d in dossiers:
            zf.writestr(
                f"json/dossierParlementaire/{d['uid']}.json",
                json.dumps({"dossierParlementaire": d}),
            )
    return chemin


def _zip_monolithe(chemin: Path, dossiers: list[dict], documents: list[dict] = ()) -> Path:
    """La forme de l'archive XIV : un seul JSON, deux tableaux."""
    with zipfile.ZipFile(chemin, "w") as zf:
        zf.writestr("Dossiers_Legislatifs_XIV.json", json.dumps({"export": {
            "dossiersLegislatifs": {"dossier": [{"dossierParlementaire": d} for d in dossiers]},
            "textesLegislatifs": {"document": list(documents)},
        }}))
    return chemin


# ── La lecture du format monolithique ──────────────────────────────────────

def test_les_dossiers_se_lisent_sous_leur_enveloppe(tmp_path):
    chemin = _zip_monolithe(tmp_path / "xiv.zip", [_dossier("DLR5L14N28814")])

    entrees = _entrees_monolithiques(chemin, "dossierParlementaire")

    assert list(entrees) == ["DLR5L14N28814"]
    assert entrees["DLR5L14N28814"]["titreDossier"]["titre"] == "Projet de loi test"


def test_les_documents_se_lisent_SANS_enveloppe(tmp_path):
    """L'asymétrie réelle du format : un dossier est emballé, un document non.
    Traiter les deux pareil rendrait `{}` sur l'une des deux collections."""
    chemin = _zip_monolithe(
        tmp_path / "xiv.zip", [], documents=[{"uid": "PRJLANR5L14B0001", "legislature": "14"}])

    entrees = _entrees_monolithiques(chemin, "document")

    assert list(entrees) == ["PRJLANR5L14B0001"]


def test_une_archive_par_fichier_n_est_pas_lue_comme_un_monolithe(tmp_path):
    """La détection porte sur la FORME, et doit rendre `{}` — sans quoi une
    archive normale serait chargée entière en mémoire pour rien."""
    chemin = _zip_par_fichier(tmp_path / "xv.zip", [_dossier("DLR5L15N37770")])

    assert _entrees_monolithiques(chemin, "dossierParlementaire") == {}


def test_un_objet_sans_uid_n_entre_pas(tmp_path):
    """Sans nom de fichier, l'uid ne se lit que dans l'objet : un objet qui n'en
    porte pas est inclassable, et un uid inventé serait pire (§2 règle 5)."""
    chemin = _zip_monolithe(tmp_path / "xiv.zip", [{"legislature": "14"}])

    assert _entrees_monolithiques(chemin, "dossierParlementaire") == {}


def test_une_archive_illisible_ne_leve_pas(tmp_path):
    chemin = tmp_path / "casse.zip"
    chemin.write_bytes(b"ceci n'est pas un zip")

    assert _entrees_monolithiques(chemin, "dossierParlementaire") == {}


# ── Les deux formes cohabitent, et la déduplication tient ──────────────────

def test_les_deux_formes_se_lisent_dans_la_meme_iteration(tmp_path):
    monolithe = _zip_monolithe(tmp_path / "xiv.zip", [_dossier("DLR5L14N28814")])
    par_fichier = _zip_par_fichier(tmp_path / "xv.zip", [_dossier("DLR5L15N37770")])

    vus = {d["uid"] for _leg, d in iter_dossiers_bruts([(14, monolithe), (15, par_fichier)])}

    assert vus == {"DLR5L14N28814", "DLR5L15N37770"}


def test_la_legislature_la_plus_haute_gagne_meme_entre_deux_formes(tmp_path):
    """La règle existante de `_iter_entrees_brutes` — l'archive la plus récente
    porte l'état le plus à jour — doit valoir quand le doublon est à cheval sur
    les deux formats. Ce n'est pas théorique : **30 uids de la XIV figurent
    aussi dans les XV-XVII**, mesuré le 18/09/2026.
    """
    uid = "DLR5L14N30000"
    monolithe = _zip_monolithe(tmp_path / "xiv.zip", [_dossier(uid, "version PÉRIMÉE")])
    par_fichier = _zip_par_fichier(tmp_path / "xv.zip", [_dossier(uid, "version À JOUR")])

    lus = list(iter_dossiers_bruts([(14, monolithe), (15, par_fichier)]))

    assert len(lus) == 1, "le doublon doit être tranché, pas rendu deux fois"
    legislature, dossier = lus[0]
    assert legislature == 15
    assert dossier["titreDossier"]["titre"] == "version À JOUR"


def test_le_monolithe_gagne_quand_c_est_lui_le_plus_recent(tmp_path):
    """Le contre-témoin : l'arbitrage porte sur la législature, jamais sur le
    format. Sans lui, le test précédent passerait avec un code qui préfère
    bêtement la forme par fichier."""
    uid = "DLR5L16N40000"
    par_fichier = _zip_par_fichier(tmp_path / "xv.zip", [_dossier(uid, "version PÉRIMÉE")])
    monolithe = _zip_monolithe(tmp_path / "xvi.zip", [_dossier(uid, "version À JOUR")])

    lus = list(iter_dossiers_bruts([(15, par_fichier), (16, monolithe)]))

    assert len(lus) == 1
    legislature, dossier = lus[0]
    assert legislature == 16
    assert dossier["titreDossier"]["titre"] == "version À JOUR"


def test_les_documents_monolithiques_traversent_aussi_l_iterateur(tmp_path):
    monolithe = _zip_monolithe(
        tmp_path / "xiv.zip", [], documents=[{"uid": "PRJLANR5L14B0001"}])

    vus = {d["uid"] for _leg, d in iter_documents_bruts([(14, monolithe)])}

    assert vus == {"PRJLANR5L14B0001"}
