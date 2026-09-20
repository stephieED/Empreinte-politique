"""Tests de `json_io.py` — écriture compacte des profils individuels (#433).

Deux garanties à tenir :
  1. le fichier écrit est bien compact (c'est tout le gain de #433) ;
  2. le format n'emporte aucun sens — relecture sémantiquement identique, et
     détection « contenu identique » de #343 insensible à l'indentation.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from json_io import SEPARATEURS_COMPACTS, dumps_profil_json, ecrire_profil_json
from merge_profile import load_existing_document, preserve_stable_freshness_timestamps


PROFIL_EXEMPLE = {
    "id": "an:alice-durand",
    "nom": "Alice Durand",
    "chambre": "AN",
    "parti": None,
    "identite": {"date_naissance": "1975-04-02", "profession": "Médecin généraliste"},
    "sources": [
        {"type": "assemblee_nationale", "url": "https://example.org/a", "synchro_le": "2026-08-18T09:00:00+0200"},
        {"type": "nosdeputes", "url": "https://example.org/b", "synchro_le": "2026-08-18T09:00:00+0200"},
    ],
    "mandats": [{"categorie": "commission", "label": "Commission des finances", "notableCount": 3}],
    "votes": [{"legislature": 17, "numero_scrutin": 42, "position": "pour", "sort": "adopte"}],
    "amendements": [{"numero": "CF12", "sort": "irrecevable", "base_juridique_irrecevabilite": "art. 40"}],
    "interventions": [],
    "tags_thematiques": ["economie"],
    "meta": {"schema_version": 1, "genere_le": "2026-08-18T09:00:00+0200", "warnings": []},
}


# ---------------------------------------------------------------------------
# Compacité
# ---------------------------------------------------------------------------

def test_dumps_profil_json_ne_contient_aucun_saut_de_ligne():
    assert "\n" not in dumps_profil_json(PROFIL_EXEMPLE)


def test_dumps_profil_json_supprime_les_espaces_de_separation():
    rendu = dumps_profil_json(PROFIL_EXEMPLE)
    assert '": ' not in rendu
    assert ", " not in rendu


def test_dumps_profil_json_garde_les_accents_en_utf8_reel():
    # Un échappement \\uXXXX coûterait 6 octets par caractère accentué et
    # annulerait une part du gain sur des profils en français.
    rendu = dumps_profil_json({"profession": "Médecin généraliste"})
    assert "Médecin généraliste" in rendu
    assert "\\u" not in rendu


def test_dumps_profil_json_est_plus_court_que_la_version_indentee():
    compact = dumps_profil_json(PROFIL_EXEMPLE)
    indente = json.dumps(PROFIL_EXEMPLE, ensure_ascii=False, indent=2)
    assert len(compact) < len(indente)


def test_separateurs_compacts_sont_sans_espace():
    assert SEPARATEURS_COMPACTS == (",", ":")


# ---------------------------------------------------------------------------
# Écriture / relecture : égalité sémantique
# ---------------------------------------------------------------------------

def test_ecrire_puis_relire_donne_un_document_semantiquement_identique(tmp_path):
    chemin = tmp_path / "alice.pivot.json"
    ecrire_profil_json(chemin, PROFIL_EXEMPLE)
    assert json.loads(chemin.read_text(encoding="utf-8")) == PROFIL_EXEMPLE


def test_ecrire_produit_un_fichier_sur_une_seule_ligne(tmp_path):
    chemin = tmp_path / "alice.pivot.json"
    ecrire_profil_json(chemin, PROFIL_EXEMPLE)
    assert len(chemin.read_text(encoding="utf-8").splitlines()) == 1


def test_ecrire_est_plus_leger_que_l_ecriture_indentee(tmp_path):
    compact = tmp_path / "compact.json"
    indente = tmp_path / "indente.json"
    ecrire_profil_json(compact, PROFIL_EXEMPLE)
    indente.write_text(json.dumps(PROFIL_EXEMPLE, ensure_ascii=False, indent=2), encoding="utf-8")
    assert compact.stat().st_size < indente.stat().st_size


def test_ecrire_cree_le_repertoire_parent_absent(tmp_path):
    chemin = tmp_path / "profiles" / "sous" / "alice.json"
    ecrire_profil_json(chemin, PROFIL_EXEMPLE)
    assert json.loads(chemin.read_text(encoding="utf-8")) == PROFIL_EXEMPLE


def test_ecrire_ecrase_le_fichier_existant_sans_residu(tmp_path):
    # Passage indenté -> compact : le contenu précédent, plus long, ne doit
    # laisser aucune queue de fichier derrière lui.
    chemin = tmp_path / "alice.json"
    chemin.write_text(json.dumps(PROFIL_EXEMPLE, ensure_ascii=False, indent=2), encoding="utf-8")
    ecrire_profil_json(chemin, {"nom": "Alice Durand"})
    assert json.loads(chemin.read_text(encoding="utf-8")) == {"nom": "Alice Durand"}


def test_ecrire_accepte_un_chemin_en_chaine(tmp_path):
    chemin = tmp_path / "alice.json"
    ecrire_profil_json(str(chemin), PROFIL_EXEMPLE)
    assert json.loads(chemin.read_text(encoding="utf-8")) == PROFIL_EXEMPLE


def test_ecrire_relire_est_idempotent_octet_pour_octet(tmp_path):
    chemin = tmp_path / "alice.json"
    ecrire_profil_json(chemin, PROFIL_EXEMPLE)
    premier = chemin.read_bytes()
    ecrire_profil_json(chemin, json.loads(chemin.read_text(encoding="utf-8")))
    assert chemin.read_bytes() == premier


# ---------------------------------------------------------------------------
# #343 : la détection « contenu identique » ignore le formatage
# ---------------------------------------------------------------------------

def test_freshness_preservee_quand_l_ancien_fichier_etait_indente(tmp_path):
    # Le cas réel du basculement : les profils déjà commités sont indentés, la
    # régénération les réécrit compacts. Le contenu n'a pas bougé, donc
    # genere_le/synchro_le ne doivent pas ré-avancer (#343).
    chemin = tmp_path / "alice.pivot.json"
    chemin.write_text(json.dumps(PROFIL_EXEMPLE, ensure_ascii=False, indent=2), encoding="utf-8")

    regenere = json.loads(dumps_profil_json(PROFIL_EXEMPLE))
    regenere["meta"]["genere_le"] = "2026-09-01T10:00:00+0200"
    for source in regenere["sources"]:
        source["synchro_le"] = "2026-09-01T10:00:00+0200"

    resultat = preserve_stable_freshness_timestamps(load_existing_document(chemin), regenere)

    assert resultat["meta"]["genere_le"] == "2026-08-18T09:00:00+0200"
    assert [s["synchro_le"] for s in resultat["sources"]] == ["2026-08-18T09:00:00+0200"] * 2

    ecrire_profil_json(chemin, resultat)
    assert json.loads(chemin.read_text(encoding="utf-8")) == PROFIL_EXEMPLE


def test_freshness_avance_toujours_quand_le_contenu_change_malgre_le_format(tmp_path):
    chemin = tmp_path / "alice.pivot.json"
    chemin.write_text(json.dumps(PROFIL_EXEMPLE, ensure_ascii=False, indent=2), encoding="utf-8")

    regenere = json.loads(dumps_profil_json(PROFIL_EXEMPLE))
    regenere["votes"].append({"legislature": 17, "numero_scrutin": 43, "position": "contre", "sort": "rejete"})
    regenere["meta"]["genere_le"] = "2026-09-01T10:00:00+0200"

    resultat = preserve_stable_freshness_timestamps(load_existing_document(chemin), regenere)

    assert resultat["meta"]["genere_le"] == "2026-09-01T10:00:00+0200"


def test_load_existing_document_relit_indifferemment_compact_et_indente(tmp_path):
    compact = tmp_path / "compact.json"
    indente = tmp_path / "indente.json"
    ecrire_profil_json(compact, PROFIL_EXEMPLE)
    indente.write_text(json.dumps(PROFIL_EXEMPLE, ensure_ascii=False, indent=2), encoding="utf-8")
    assert load_existing_document(compact) == load_existing_document(indente)
