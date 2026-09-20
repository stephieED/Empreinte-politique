import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from schema_groupe import (
    SCHEMA_GROUPE_VERSION,
    AMENDEMENTS_TYPES_DEPOSANT,
    make_empty_profil_groupe,
    validate_profil_groupe,
)
from schema_pivot import KNOWN_CHAMBRES


# ---------------------------------------------------------------------------
# make_empty_profil_groupe
# ---------------------------------------------------------------------------

def test_make_empty_schema_version():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["schema_version"] == SCHEMA_GROUPE_VERSION
    assert g["meta"]["schema_version"] == SCHEMA_GROUPE_VERSION


def test_make_empty_type_document():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["type_document"] == "profil_groupe"


def test_make_empty_identifiers():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes et apparentés", "AN", "16")
    assert g["groupe_id"] == "AN:SOC"
    assert g["groupe_sigle"] == "SOC"
    assert g["groupe_nom"] == "Socialistes et apparentés"
    assert g["chambre"] == "AN"
    assert g["legislature"] == "16"


def test_make_empty_default_lists():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    for key in ("historique_noms", "membres", "cohesion_votes", "tags_thematiques_agreges", "sources"):
        assert isinstance(g[key], list)
        assert g[key] == []


def test_make_empty_amendements_agreges_defaults():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    empty_stats = {
        "nb_amendements": 0,
        "nb_adoptes": 0,
        "nb_rejetes": 0,
        "nb_irrecevables": 0,
        "nb_retires_ou_tombes": 0,
        "taux_adoption": None,
    }
    assert g["amendements_agreges"] == {
        **empty_stats,
        "par_type_deposant": {t: dict(empty_stats) for t in AMENDEMENTS_TYPES_DEPOSANT},
    }


def test_make_empty_periode_defaults():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["periode"]["debut"] is None
    assert g["periode"]["fin"] is None
    assert g["periode"]["actif"] is True


def test_make_empty_effectif_defaults():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["effectif"]["a_la_date_de_reference"] == 0
    assert g["date_reference"] is None
    assert g["effectif"]["min_historique"] is None
    assert g["effectif"]["max_historique"] is None


def test_make_empty_meta_warnings_empty():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["meta"]["warnings"] == []


def test_make_empty_meta_profils_sources_empty():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["meta"]["profils_sources"] == []


def test_make_empty_meta_seuil_quorum_default():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    assert g["meta"]["seuil_quorum"] == 0.5


def test_make_empty_meta_genere_le_iso():
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes", "AN", "16")
    ts = g["meta"]["genere_le"]
    assert "T" in ts and "-" in ts


def test_make_empty_chambre_none():
    g = make_empty_profil_groupe("PE:S&D", "S&D", "Socialistes", None, None)
    assert g["chambre"] is None
    assert g["legislature"] is None


# ---------------------------------------------------------------------------
# validate_profil_groupe — profil valide
# ---------------------------------------------------------------------------

def _valid_groupe() -> dict:
    """Groupe minimal valide pour les tests."""
    g = make_empty_profil_groupe("AN:SOC", "SOC", "Socialistes et apparentés", "AN", "16")
    g["meta"]["licence_donnees"] = "ODbL"
    return g


def test_validate_valid_groupe_no_errors():
    assert validate_profil_groupe(_valid_groupe()) == []


def test_validate_valid_groupe_chambre_senat():
    g = _valid_groupe()
    g["chambre"] = "Senat"
    g["groupe_id"] = "Senat:SER"
    assert validate_profil_groupe(g) == []


def test_validate_valid_groupe_chambre_pe():
    g = _valid_groupe()
    g["chambre"] = "PE"
    g["groupe_id"] = "PE:S&D"
    assert validate_profil_groupe(g) == []


def test_validate_valid_groupe_chambre_none():
    g = _valid_groupe()
    g["chambre"] = None
    assert validate_profil_groupe(g) == []


# ---------------------------------------------------------------------------
# validate_profil_groupe — erreurs détectées
# ---------------------------------------------------------------------------

def test_validate_non_dict_input():
    errors = validate_profil_groupe("not a dict")  # type: ignore[arg-type]
    assert errors
    assert any("dict" in e for e in errors)


def test_validate_missing_top_level_key():
    g = _valid_groupe()
    del g["groupe_nom"]
    errors = validate_profil_groupe(g)
    assert any("groupe_nom" in e for e in errors)


def test_validate_wrong_schema_version():
    g = _valid_groupe()
    g["schema_version"] = "99"
    errors = validate_profil_groupe(g)
    assert any("schema_version" in e for e in errors)


def test_validate_wrong_type_document():
    g = _valid_groupe()
    g["type_document"] = "profil_individuel"
    errors = validate_profil_groupe(g)
    assert any("type_document" in e for e in errors)


def test_validate_empty_groupe_id():
    g = _valid_groupe()
    g["groupe_id"] = ""
    errors = validate_profil_groupe(g)
    assert any("groupe_id" in e for e in errors)


def test_validate_unknown_chambre():
    g = _valid_groupe()
    g["chambre"] = "SENAT_INCONNU"
    errors = validate_profil_groupe(g)
    assert any("chambre" in e for e in errors)


def test_validate_membres_not_a_list():
    g = _valid_groupe()
    g["membres"] = {"not": "a list"}
    errors = validate_profil_groupe(g)
    assert any("membres" in e for e in errors)


def test_validate_cohesion_votes_not_a_list():
    g = _valid_groupe()
    g["cohesion_votes"] = "string"
    errors = validate_profil_groupe(g)
    assert any("cohesion_votes" in e for e in errors)


def test_validate_tags_not_a_list():
    g = _valid_groupe()
    g["tags_thematiques_agreges"] = 42
    errors = validate_profil_groupe(g)
    assert any("tags_thematiques_agreges" in e for e in errors)


def test_validate_amendements_agreges_not_a_dict():
    g = _valid_groupe()
    g["amendements_agreges"] = "string"
    errors = validate_profil_groupe(g)
    assert any("amendements_agreges" in e for e in errors)


def test_validate_amendements_agreges_none_is_valid():
    g = _valid_groupe()
    g["amendements_agreges"] = None
    assert validate_profil_groupe(g) == []


def test_validate_amendements_agreges_par_type_deposant_not_a_dict():
    g = _valid_groupe()
    g["amendements_agreges"]["par_type_deposant"] = "string"
    errors = validate_profil_groupe(g)
    assert any("par_type_deposant" in e for e in errors)


def test_known_amendements_types_deposant_contains_inconnu():
    assert "depute" in AMENDEMENTS_TYPES_DEPOSANT
    assert "gouvernement" in AMENDEMENTS_TYPES_DEPOSANT
    assert "commission_rapporteur" in AMENDEMENTS_TYPES_DEPOSANT
    assert "inconnu" in AMENDEMENTS_TYPES_DEPOSANT


def test_validate_couverture_roster_absent_is_valid():
    g = _valid_groupe()
    assert "couverture_roster" not in g["meta"]
    assert validate_profil_groupe(g) == []


def test_validate_couverture_roster_dict_is_valid():
    g = _valid_groupe()
    g["meta"]["couverture_roster"] = {"roster_total": 62, "profils_disponibles": 12}
    assert validate_profil_groupe(g) == []


def test_validate_couverture_roster_not_a_dict():
    g = _valid_groupe()
    g["meta"]["couverture_roster"] = "12/62"
    errors = validate_profil_groupe(g)
    assert any("couverture_roster" in e for e in errors)


def test_validate_periode_not_a_dict():
    g = _valid_groupe()
    g["periode"] = "2022-01-01"
    errors = validate_profil_groupe(g)
    assert any("periode" in e for e in errors)


def test_validate_meta_not_a_dict():
    g = _valid_groupe()
    g["meta"] = "not a dict"
    errors = validate_profil_groupe(g)
    assert any("meta" in e for e in errors)


def test_validate_meta_missing_key():
    g = _valid_groupe()
    del g["meta"]["genere_le"]
    errors = validate_profil_groupe(g)
    assert any("genere_le" in e for e in errors)


def test_validate_meta_schema_version_mismatch():
    g = _valid_groupe()
    g["meta"]["schema_version"] = "99"
    errors = validate_profil_groupe(g)
    assert any("meta.schema_version" in e for e in errors)


def test_validate_meta_warnings_not_a_list():
    g = _valid_groupe()
    g["meta"]["warnings"] = "not a list"
    errors = validate_profil_groupe(g)
    assert any("warnings" in e for e in errors)


def test_validate_meta_profils_sources_not_a_list():
    g = _valid_groupe()
    g["meta"]["profils_sources"] = "not a list"
    errors = validate_profil_groupe(g)
    assert any("profils_sources" in e for e in errors)
