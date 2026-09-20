import sys
from pathlib import Path
from unittest.mock import patch

# Les modules testés vivent dans src/, à côté du dossier tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from candidate_profile_ue import (
    _extract_mandats_europeens,
    _normalize_name,
    _prettify_uri,
    build_profile_ue,
    find_mep_by_name,
    resolve_organization,
)


def test_normalize_name_ignores_accents_casse_et_ordre():
    assert _normalize_name("Jordan Bardella") == _normalize_name("BARDELLA Jordan")
    assert _normalize_name("Jean-Luc Mélenchon") == _normalize_name("MÉLENCHON Jean-Luc")
    assert _normalize_name("Jordan Bardella") != _normalize_name("Marine Le Pen")


def test_prettify_uri_fallback_pour_role_inconnu():
    assert _prettify_uri("def/ep-roles/SOME_NEW_ROLE") == "Some new role"
    assert _prettify_uri(None) is None


def test_find_mep_by_name_matches_exact_normalized_name():
    roster = [
        {"identifier": "131580", "label": "Jordan BARDELLA"},
        {"identifier": "28210", "label": "Marine LE PEN"},
    ]
    with patch("candidate_profile_ue.fetch_all_meps_by_country", return_value=roster):
        found = find_mep_by_name("Jordan Bardella")
        assert found["identifier"] == "131580"

        assert find_mep_by_name("Bruno Retailleau") is None


def test_extract_mandats_europeens_resout_organisation_et_trie_par_date():
    mep_detail = {
        "hasMembership": [
            {
                "memberDuring": {"startDate": "2019-07-02", "endDate": "2024-07-15"},
                "organization": "org/5588",
                "role": "def/ep-roles/MEMBER",
                "membershipClassification": "def/ep-entities/EU_POLITICAL_GROUP",
            },
            {
                "memberDuring": {"startDate": "2024-07-16"},
                "organization": "org/7150",
                "role": "def/ep-roles/CHAIR",
                "membershipClassification": "def/ep-entities/EU_POLITICAL_GROUP",
            },
            {
                "memberDuring": {"startDate": "2024-07-16"},
                "organization": "org/ep-10",
                "role": "def/ep-roles/MEMBER",
                "membershipClassification": "def/ep-entities/EU_INSTITUTION",
            },
        ]
    }

    org_cache = {
        "org/5588": {"sigle": "ID", "nom_complet": "Identité et démocratie"},
        "org/7150": {"sigle": "PfE", "nom_complet": "Groupe Patriotes pour l'Europe"},
    }

    mandats = _extract_mandats_europeens(mep_detail, org_cache)

    assert len(mandats) == 3
    # Trié du plus récent au plus ancien.
    assert mandats[0]["debut"] == "2024-07-16"
    assert mandats[-1]["debut"] == "2019-07-02"
    assert mandats[-1]["fin"] == "2024-07-15"
    assert mandats[-1]["actif"] is False

    chair_entry = next(m for m in mandats if m["role"] == "CHAIR")
    assert chair_entry["organisation_sigle"] == "PfE"
    assert chair_entry["role_label"] == "Président(e)"
    assert chair_entry["actif"] is True

    legislature_entry = next(m for m in mandats if m["type"] == "EU_INSTITUTION")
    assert legislature_entry["organisation_sigle"] == "10e législature"


def test_resolve_organization_utilise_le_cache():
    cache = {"org/123": {"sigle": "ABC", "nom_complet": "A Big Committee"}}
    with patch("candidate_profile_ue._get_json") as mock_get_json:
        result = resolve_organization("org/123", cache)
        mock_get_json.assert_not_called()
        assert result == {"sigle": "ABC", "nom_complet": "A Big Committee"}


def test_build_profile_ue_renvoie_none_si_candidat_non_trouve():
    with patch("candidate_profile_ue.find_mep_by_name", return_value=None):
        assert build_profile_ue("Personne Inconnue") is None
