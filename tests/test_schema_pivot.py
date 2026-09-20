import sys
from pathlib import Path

# Les modules testés vivent dans src/, à côté du dossier tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import time
from schema_pivot import (
    SCHEMA_VERSION,
    KNOWN_CHAMBRES,
    KNOWN_POSITIONS,
    KNOWN_CATEGORIES,
    KNOWN_POSITIONS_HEMICYCLE,
    KNOWN_MODES_DECLENCHEMENT,
    KNOWN_TYPES_RAPPORT,
    KNOWN_STADES_PROCEDURAUX,
    KNOWN_TYPES_SCRUTIN,
    KNOWN_TYPES_VOTE,
    KNOWN_TYPES_DEPOSANT,
    KNOWN_ROLES_SIGNATAIRE_AMENDEMENT,
    KNOWN_BASES_IRRECEVABILITE,
    KNOWN_PROVENANCES,
    make_empty_profil,
    validate_profil,
    validate_amendements_index,
    validate_amendements_cosignatures,
)


# ---------------------------------------------------------------------------
# make_empty_profil
# ---------------------------------------------------------------------------

def test_make_empty_profil_schema_version():
    p = make_empty_profil("nosdeputes:jean-dupont", "Jean Dupont")
    assert p["schema_version"] == SCHEMA_VERSION
    assert p["meta"]["schema_version"] == SCHEMA_VERSION


def test_make_empty_profil_id_and_nom():
    p = make_empty_profil("parltrack:123", "Marie Martin")
    assert p["id"] == "parltrack:123"
    assert p["nom"] == "Marie Martin"


def test_make_empty_profil_default_lists():
    p = make_empty_profil("test:x", "X")
    for key in (
        "sources", "mandats", "votes", "textes_portes", "interventions",
        "amendements", "tags_thematiques",
    ):
        assert isinstance(p[key], list), f"'{key}' doit être une liste vide par défaut"
        assert p[key] == []


def test_make_empty_profil_default_nulls():
    p = make_empty_profil("test:x", "X")
    assert p["chambre"] is None
    assert p["parti"] is None
    assert p["groupe"] is None


def test_make_empty_profil_genere_le_looks_like_iso():
    p = make_empty_profil("test:x", "X")
    ts = p["meta"]["genere_le"]
    # time.strftime('%Y-%m-%dT%H:%M:%S') always produces both 'T' and '-'
    assert "T" in ts and "-" in ts, f"genere_le ne ressemble pas à un ISO-8601 : {ts!r}"


def test_make_empty_profil_warnings_empty():
    p = make_empty_profil("test:x", "X")
    assert p["meta"]["warnings"] == []


def test_make_empty_profil_provenance_defaut_candidat_declare():
    p = make_empty_profil("test:x", "X")
    assert p["meta"]["provenance"] == "candidat_declare"


def test_make_empty_profil_provenance_explicite_roster_groupe():
    p = make_empty_profil("test:x", "X", provenance="roster_groupe")
    assert p["meta"]["provenance"] == "roster_groupe"


# ---------------------------------------------------------------------------
# validate_profil — profil valide
# ---------------------------------------------------------------------------

def _valid_profil() -> dict:
    """Construit un profil pivot minimal valide pour les tests."""
    p = make_empty_profil("nosdeputes:test", "Test Personne")
    # #493 : `chambre` vaut `chambres[0]`, et `validate_profil` le vérifie. Les
    # deux se posent donc ensemble — normalement via `deriver_chambres()`, seule
    # fabrique du couple ; ici à la main, pour garder la fixture minimale.
    p["chambres"] = ["AN"]
    p["chambre"] = "AN"
    p["meta"]["licence_donnees"] = "ODbL"
    return p


def test_validate_valid_profil_returns_no_errors():
    assert validate_profil(_valid_profil()) == []


def test_validate_valid_profil_with_chambre_senat():
    p = _valid_profil()
    p["chambres"] = ["Senat"]
    p["chambre"] = "Senat"
    assert validate_profil(p) == []


def test_validate_valid_profil_with_chambre_pe():
    p = _valid_profil()
    p["chambres"] = ["PE"]
    p["chambre"] = "PE"
    assert validate_profil(p) == []


def test_validate_valid_profil_chambre_none():
    p = _valid_profil()
    p["chambres"] = []
    p["chambre"] = None
    assert validate_profil(p) == []


# ---------------------------------------------------------------------------
# validate_profil — erreurs détectées
# ---------------------------------------------------------------------------

def test_validate_missing_top_level_key():
    p = _valid_profil()
    del p["nom"]
    errors = validate_profil(p)
    assert any("nom" in e for e in errors), f"Erreur attendue pour 'nom' manquant : {errors}"


def test_validate_wrong_schema_version():
    p = _valid_profil()
    p["schema_version"] = "0"
    errors = validate_profil(p)
    assert any("schema_version" in e for e in errors)


def test_validate_empty_id():
    p = _valid_profil()
    p["id"] = ""
    errors = validate_profil(p)
    assert any("'id'" in e for e in errors)


def test_validate_empty_nom():
    p = _valid_profil()
    p["nom"] = ""
    errors = validate_profil(p)
    assert any("'nom'" in e for e in errors)


def test_validate_unknown_chambre():
    p = _valid_profil()
    p["chambre"] = "ASSEMBLEE_GENERALE"
    errors = validate_profil(p)
    assert any("chambre" in e for e in errors)


def test_validate_votes_not_a_list():
    p = _valid_profil()
    p["votes"] = {"not": "a list"}
    errors = validate_profil(p)
    assert any("votes" in e for e in errors)


def test_validate_mandats_not_a_list():
    p = _valid_profil()
    p["mandats"] = "should be a list"
    errors = validate_profil(p)
    assert any("mandats" in e for e in errors)


def test_validate_missing_meta_key():
    p = _valid_profil()
    del p["meta"]["genere_le"]
    errors = validate_profil(p)
    assert any("genere_le" in e for e in errors)


def test_validate_meta_not_a_dict():
    p = _valid_profil()
    p["meta"] = "not a dict"
    errors = validate_profil(p)
    assert any("meta" in e for e in errors)


def test_validate_meta_schema_version_mismatch():
    p = _valid_profil()
    p["meta"]["schema_version"] = "99"
    errors = validate_profil(p)
    assert any("meta.schema_version" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_profil — meta.provenance
# ---------------------------------------------------------------------------

def test_validate_provenance_candidat_declare_valide():
    p = _valid_profil()
    p["meta"]["provenance"] = "candidat_declare"
    assert validate_profil(p) == []


def test_validate_provenance_roster_groupe_valide():
    p = _valid_profil()
    p["meta"]["provenance"] = "roster_groupe"
    assert validate_profil(p) == []


def test_validate_provenance_absente_reste_valide():
    """Rétro-compatibilité : un pivot existant sans meta.provenance (pré-#189)
    reste valide, traité comme "candidat_declare" par défaut par les consommateurs."""
    p = _valid_profil()
    del p["meta"]["provenance"]
    assert validate_profil(p) == []


def test_validate_provenance_valeur_hors_enum_rejetee():
    p = _valid_profil()
    p["meta"]["provenance"] = "extraterrestre"
    errors = validate_profil(p)
    assert any("meta.provenance" in e for e in errors)


def test_known_provenances_contient_les_trois_populations():
    """Une par population de `pivot_data/profiles/` (#996 lot 3).

    L'égalité et non l'inclusion : `KNOWN_*` est un vocabulaire FERMÉ, et une
    valeur ajoutée sans être documentée quelque part est ce que
    `tests/test_sources_documentees.py` refuse (AGENTS.md §8).
    """
    assert KNOWN_PROVENANCES == frozenset({
        "candidat_declare", "roster_groupe", "roster_gouvernement",
    })


def test_validate_meta_warnings_not_a_list():
    p = _valid_profil()
    p["meta"]["warnings"] = "not a list"
    errors = validate_profil(p)
    assert any("warnings" in e for e in errors)


def test_validate_non_dict_input():
    errors = validate_profil("not a dict")  # type: ignore[arg-type]
    assert errors
    assert any("dict" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_profil — amendements[]
# ---------------------------------------------------------------------------

def test_validate_amendements_not_a_list():
    p = _valid_profil()
    p["amendements"] = "should be a list"
    errors = validate_profil(p)
    assert any("amendements" in e for e in errors)


def test_validate_amendements_mapping_valide():
    """#431 : le profil ne porte plus que `{amendement_id, role_signataire}`."""
    p = _valid_profil()
    p["amendements"] = [
        {
            "amendement_id": "an:AMANR5L17PO59047BTC1376P0D1N000012",
            "role_signataire": "auteur_principal",
        }
    ]
    assert validate_profil(p) == []


def test_validate_amendement_role_signataire_inconnu():
    p = _valid_profil()
    p["amendements"] = [
        {
            "amendement_id": "an:AMANR5L17PO59047BTC1376P0D1N000012",
            "role_signataire": "inconnu",
        }
    ]
    errors = validate_profil(p)
    assert any("role_signataire" in e for e in errors)


def test_validate_amendement_id_mal_forme_est_une_erreur():
    p = _valid_profil()
    p["amendements"] = [
        {"amendement_id": "AMANR5L17PO59047BTC1376P0D1N000012",
         "role_signataire": "auteur_principal"}
    ]
    errors = validate_profil(p)
    assert any("mal formé" in e for e in errors)


def test_validate_amendement_sans_id_exige_enregistrement_non_resolu():
    """Un amendement qu'on ne sait pas rattacher n'est ni supprimé ni deviné."""
    p = _valid_profil()
    p["amendements"] = [{"amendement_id": None, "role_signataire": "cosignataire"}]
    errors = validate_profil(p)
    assert any("amendement_non_resolu" in e for e in errors)

    p["amendements"] = [{
        "amendement_id": None,
        "role_signataire": "cosignataire",
        "amendement_non_resolu": {"texte_vise": "PLF 2025", "sort": "rejeté"},
    }]
    assert validate_profil(p) == []


def test_validate_amendement_id_absent_de_lindex_est_une_erreur():
    """Invariant devenu jointure : vérifié SI l'index est fourni."""
    from amendements_index import AmendementsIndex

    p = _valid_profil()
    p["amendements"] = [
        {"amendement_id": "an:AMANR5L17PO0P0D1N000001", "role_signataire": "auteur_principal"}
    ]
    # Sans index : sauté, jamais déclaré valide par défaut par une autre voie.
    assert validate_profil(p) == []
    index = AmendementsIndex({"an:AMANR5L17PO0P0D1N000002": {"sort": "adopté"}})
    errors = validate_profil(p, amendements_index=index)
    assert any("introuvable dans l'index des amendements" in e for e in errors)

    index = AmendementsIndex({"an:AMANR5L17PO0P0D1N000001": {"sort": "adopté"}})
    assert validate_profil(p, amendements_index=index) == []


# ---------------------------------------------------------------------------
# validate_profil — mandats[].position_dans_hemicycle (champ éditorial sensible)
# ---------------------------------------------------------------------------

def test_validate_position_hemicycle_sans_source_url_est_une_erreur():
    p = _valid_profil()
    p["mandats"] = [{
        "label": "Mandat parlementaire",
        "categorie": "mandat_electif",
        "fonction": "membre",
        "debut": "2022-01-01",
        "fin": None,
        "actif": True,
        "source_url": None,
        "position_dans_hemicycle": "majorite",
    }]
    errors = validate_profil(p)
    assert any("position_dans_hemicycle" in e for e in errors)


def test_validate_position_hemicycle_avec_source_url_est_valide():
    p = _valid_profil()
    p["mandats"] = [{
        "label": "Mandat parlementaire",
        "categorie": "mandat_electif",
        "fonction": "membre",
        "debut": "2022-01-01",
        "fin": None,
        "actif": True,
        "source_url": "https://www.assemblee-nationale.fr/...",
        "position_dans_hemicycle": "opposition",
    }]
    assert validate_profil(p) == []


def test_validate_position_hemicycle_none_ne_requiert_pas_de_source():
    p = _valid_profil()
    p["mandats"] = [{
        "label": "Mandat parlementaire",
        "categorie": "mandat_electif",
        "fonction": "membre",
        "debut": "2022-01-01",
        "fin": None,
        "actif": True,
        "source_url": None,
        "position_dans_hemicycle": None,
    }]
    assert validate_profil(p) == []


# ---------------------------------------------------------------------------
# validate_profil — mandats[].mode_declenchement
# ---------------------------------------------------------------------------

def test_validate_mode_declenchement_inconnu_est_une_erreur():
    p = _valid_profil()
    p["mandats"] = [{"categorie": "commission_enquete", "mode_declenchement": "vote_a_main_levee"}]
    errors = validate_profil(p)
    assert any("mode_declenchement" in e for e in errors)


def test_validate_mode_declenchement_connu_est_valide():
    p = _valid_profil()
    for mode in KNOWN_MODES_DECLENCHEMENT:
        p["mandats"] = [{"categorie": "commission_enquete", "mode_declenchement": mode}]
        assert validate_profil(p) == []


# ---------------------------------------------------------------------------
# validate_profil / validate_scrutins_index — votes[] après normalisation (#432)
#
# `type_scrutin`, `type_vote`, `texte_lie_id` et `sort` ont migré du profil vers
# `pivot_data/scrutins.json` : ce sont des champs du SCRUTIN, identiques pour
# tous ses votants. Leur validation les a suivis — elle s'exécute désormais une
# fois par scrutin au lieu d'une fois par votant.
#
# Deux invariants sont devenus des JOINTURES et ne sont vérifiables qu'avec
# l'index : qu'un `scrutin_id` référencé existe, et la règle 4 (un 49.3 ne porte
# jamais de position). Sans index ils sont sautés — jamais validés par défaut.
# ---------------------------------------------------------------------------

def _index(scrutins):
    """Index minimal, du type de ce que `ScrutinsIndex` expose à la validation."""
    class _Faux:
        par_id = {s["id"]: s for s in scrutins}
    return _Faux()


def _scrutin(**champs):
    base = {
        "id": "an:17:1", "legislature": "17", "numero_scrutin": "1",
        "legislature_provenance": "collectee", "date": "2026-01-05",
        "texte": "Projet de loi", "sort": "adopté", "type_scrutin": None,
        "type_vote": "vote_texte", "texte_lie_id": None, "source_url": None,
    }
    base.update(champs)
    return base


def test_validate_vote_mapping_minimal_est_valide():
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": "an:17:1", "position": "pour"}]
    assert validate_profil(p) == []


def test_validate_scrutin_id_mal_forme_est_une_erreur():
    """Un identifiant partiel se confondrait avec celui d'une autre législature :
    le numéro de scrutin repart à 1 à chaque fois (AGENTS.md §5)."""
    for mauvais in ("17:1", "an:17", "an::1", "an:17:", "1", "eu:17:1"):
        p = _valid_profil()
        p["votes"] = [{"scrutin_id": mauvais, "position": "pour"}]
        errors = validate_profil(p)
        assert any("scrutin_id" in e for e in errors), mauvais


def test_validate_vote_sans_scrutin_id_exige_l_enregistrement_complet():
    """Une donnée qu'on ne sait pas normaliser reste une donnée (§2.5) : sans
    identifiant, le vote doit conserver son enregistrement — sinon il n'est pas
    seulement non normalisé, il est perdu."""
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": None, "position": "pour"}]
    errors = validate_profil(p)
    assert any("scrutin_non_resolu" in e for e in errors)


def test_validate_vote_non_resolu_avec_enregistrement_est_valide():
    p = _valid_profil()
    p["votes"] = [{
        "scrutin_id": None, "position": "pour",
        "scrutin_non_resolu": {"numero_scrutin": "1", "date": None, "texte": "x"},
    }]
    assert validate_profil(p) == []


def test_validate_scrutin_id_absent_de_l_index_est_une_erreur():
    """Le mapping pointerait dans le vide — exactement ce que la fusion additive
    de l'index existe pour empêcher."""
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": "an:17:999", "position": "pour"}]
    errors = validate_profil(p, scrutins_index=_index([_scrutin()]))
    assert any("introuvable dans l'index" in e for e in errors)


def test_validate_sans_index_ne_verifie_pas_l_existence_du_scrutin():
    """Sauté, pas validé par défaut : `validate_profil` ne peut pas affirmer
    qu'un identifiant existe quand rien ne le lui dit."""
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": "an:17:999", "position": "pour"}]
    assert validate_profil(p) == []


def test_validate_regle_4_49_3_avec_position_est_une_erreur():
    """Règle 4 : un 49.3 n'est jamais une position. Le `sort` vivant sur le
    scrutin et la `position` sur le profil, c'est devenu une jointure."""
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": "an:17:1", "position": "pour"}]
    index = _index([_scrutin(sort="adopte_sans_vote_49_3")])
    errors = validate_profil(p, scrutins_index=index)
    assert any("règle 4" in e for e in errors)


def test_validate_regle_4_49_3_sans_position_est_valide():
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": "an:17:1", "position": None}]
    index = _index([_scrutin(sort="adopte_sans_vote_49_3")])
    assert validate_profil(p, scrutins_index=index) == []


def test_validate_position_inconnue_reste_une_erreur():
    p = _valid_profil()
    p["votes"] = [{"scrutin_id": "an:17:1", "position": "peut-etre"}]
    assert any("position" in e for e in validate_profil(p))


# --- validate_scrutins_index : les champs migrés y sont validés ---------------

def test_validate_index_minimal_est_valide():
    from schema_pivot import validate_scrutins_index
    assert validate_scrutins_index({
        "schema_version": "scrutins-v1", "scrutins": [_scrutin()],
    }) == []


def test_validate_index_type_scrutin_inconnu_est_une_erreur():
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({
        "schema_version": "scrutins-v1", "scrutins": [_scrutin(type_scrutin="secret")],
    })
    assert any("type_scrutin" in e for e in errors)


def test_validate_index_types_scrutin_connus_sont_valides():
    from schema_pivot import validate_scrutins_index
    for type_scrutin in KNOWN_TYPES_SCRUTIN:
        assert validate_scrutins_index({
            "schema_version": "scrutins-v1", "scrutins": [_scrutin(type_scrutin=type_scrutin)],
        }) == []


def test_validate_index_type_vote_inconnu_est_une_erreur():
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({
        "schema_version": "scrutins-v1", "scrutins": [_scrutin(type_vote="vote_secret")],
    })
    assert any("type_vote" in e for e in errors)


def test_validate_index_motion_censure_sans_texte_lie_id_est_une_erreur():
    """Invariant inchangé, seulement déplacé : une motion de censure n'est
    jamais fusionnée avec le vote sur le texte 49.3 concerné."""
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({
        "schema_version": "scrutins-v1", "scrutins": [_scrutin(type_vote="motion_censure")],
    })
    assert any("texte_lie_id" in e for e in errors)


def test_validate_index_motion_censure_avec_texte_lie_id_est_valide():
    from schema_pivot import validate_scrutins_index
    assert validate_scrutins_index({
        "schema_version": "scrutins-v1",
        "scrutins": [_scrutin(type_vote="motion_censure", texte_lie_id="49-3-texte-42")],
    }) == []


def test_validate_index_provenance_inconnue_est_une_erreur():
    """Une législature dérivée d'un calendrier ne doit jamais passer pour une
    donnée collectée."""
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({
        "schema_version": "scrutins-v1",
        "scrutins": [_scrutin(legislature_provenance="devinee")],
    })
    assert any("legislature_provenance" in e for e in errors)


def test_validate_index_id_incoherent_avec_ses_champs_est_une_erreur():
    """L'identifiant est dérivé de `legislature` et `numero_scrutin` : une
    divergence rendrait la liste incohérente avec elle-même."""
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({
        "schema_version": "scrutins-v1", "scrutins": [_scrutin(legislature="16")],
    })
    assert any("divergent" in e for e in errors)


def test_validate_index_doublon_d_identifiant_est_une_erreur():
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({
        "schema_version": "scrutins-v1", "scrutins": [_scrutin(), _scrutin()],
    })
    assert any("double" in e for e in errors)


def test_validate_index_version_de_schema_erronee_est_une_erreur():
    from schema_pivot import validate_scrutins_index
    errors = validate_scrutins_index({"schema_version": "1", "scrutins": []})
    assert any("schema_version" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_profil — textes_portes[].type_rapport / stade_procedural
# ---------------------------------------------------------------------------

def test_validate_type_rapport_inconnu_est_une_erreur():
    p = _valid_profil()
    p["textes_portes"] = [{"titre": "PPL x", "type_rapport": "rapporteur_vip"}]
    errors = validate_profil(p)
    assert any("type_rapport" in e for e in errors)


def test_validate_type_rapport_connu_est_valide():
    p = _valid_profil()
    for type_rapport in KNOWN_TYPES_RAPPORT:
        p["textes_portes"] = [{"titre": "PPL x", "type_rapport": type_rapport,
                               "sort": "adopte"}]
        assert validate_profil(p) == []


def test_validate_stade_procedural_inconnu_est_une_erreur():
    p = _valid_profil()
    p["textes_portes"] = [{"titre": "PPL x", "stade_procedural": "vote_final"}]
    errors = validate_profil(p)
    assert any("stade_procedural" in e for e in errors)


def test_validate_stade_procedural_connu_est_valide():
    p = _valid_profil()
    for stade in KNOWN_STADES_PROCEDURAUX:
        p["textes_portes"] = [{"titre": "PPL x", "stade_procedural": stade,
                               "sort": "adopte"}]
        assert validate_profil(p) == []


def test_validate_role_texte_inconnu_est_une_erreur():
    p = _valid_profil()
    p["textes_portes"] = [{"titre": "PPL x", "role": "porteur"}]
    errors = validate_profil(p)
    assert any("role non reconnu" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_amendements_index — type_deposant / sort / base_juridique_irrecevabilite
#
# Ces invariants portaient sur `amendements[]` des profils. Depuis #431 les
# champs vivent dans l'index partagé, et **la validation a suivi les champs** :
# elle s'exécute une fois par amendement au lieu d'une fois par signataire.
# ---------------------------------------------------------------------------

_UID = "an:AMANR5L17PO59047BTC1376P0D1N000012"


def _index_fichier(amendement: dict) -> dict:
    return {
        "schema_version": "amendements-v1",
        "legislature": "17",
        "amendements": {_UID: amendement},
    }


def test_index_amendements_valide():
    assert validate_amendements_index(_index_fichier({
        "texte_vise": "PLF 2025", "sort": "rejeté", "type_deposant": "depute",
    })) == []


def test_index_validate_type_deposant_inconnu_est_une_erreur():
    errors = validate_amendements_index(_index_fichier({
        "texte_vise": "PLF 2025", "sort": "rejeté", "type_deposant": "senateur",
    }))
    assert any("type_deposant" in e for e in errors)


def test_index_validate_type_deposant_connu_est_valide():
    for type_deposant in KNOWN_TYPES_DEPOSANT:
        assert validate_amendements_index(_index_fichier({
            "texte_vise": "PLF 2025", "sort": "rejeté", "type_deposant": type_deposant,
        })) == []


def test_index_validate_irrecevable_sans_base_juridique_est_une_erreur():
    errors = validate_amendements_index(_index_fichier({
        "texte_vise": "PLF 2025", "sort": "irrecevable",
    }))
    assert any("base_juridique_irrecevabilite" in e for e in errors)


def test_index_validate_irrecevable_avec_base_juridique_inconnue_est_une_erreur():
    errors = validate_amendements_index(_index_fichier({
        "texte_vise": "PLF 2025", "sort": "irrecevable",
        "base_juridique_irrecevabilite": "art. 41",
    }))
    assert any("base_juridique_irrecevabilite" in e for e in errors)


def test_index_validate_irrecevable_avec_base_juridique_connue_est_valide():
    for base in KNOWN_BASES_IRRECEVABILITE:
        assert validate_amendements_index(_index_fichier({
            "texte_vise": "PLF 2025", "sort": "irrecevable",
            "base_juridique_irrecevabilite": base,
        })) == []


def test_index_validate_sort_non_irrecevable_ne_requiert_pas_de_base_juridique():
    assert validate_amendements_index(_index_fichier({
        "texte_vise": "PLF 2025", "sort": "rejeté",
    })) == []


def test_index_validate_legislature_incoherente_est_une_erreur():
    """Un fichier porte UNE législature : une entrée d'une autre y serait
    invisible pour un consommateur qui ne charge que la sienne."""
    index = _index_fichier({"texte_vise": "PLF 2025", "sort": "rejeté"})
    index["legislature"] = "16"
    errors = validate_amendements_index(index)
    assert any("mais le fichier déclare" in e for e in errors)


def test_index_validate_cosignataires_dans_le_meta_est_une_erreur():
    """Les cosignatures vivent dans le fichier compagnon : 59 % du poids."""
    errors = validate_amendements_index(_index_fichier({
        "texte_vise": "PLF 2025", "sort": "rejeté", "co_signataires": ["an:PA1"],
    }))
    assert any("co_signataires" in e for e in errors)


def test_index_cosignatures_valide():
    assert validate_amendements_cosignatures({
        "schema_version": "amendements-cosignatures-v1",
        "legislature": "17",
        "co_signataires": {_UID: ["an:PA1", "an:PA2"]},
    }) == []


def test_index_cosignatures_liste_vide_est_une_erreur():
    """Un amendement sans cosignataire est ABSENT du fichier, il n'y figure pas
    avec une liste vide — sans quoi « aucun cosignataire » et « non renseigné »
    deviendraient indiscernables."""
    errors = validate_amendements_cosignatures({
        "schema_version": "amendements-cosignatures-v1",
        "legislature": "17",
        "co_signataires": {_UID: []},
    })
    assert any("liste vide" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_profil — interventions[].* (champs débats officiels optionnels)
# ---------------------------------------------------------------------------

def test_validate_intervention_champs_debat_officiel_valides():
    p = _valid_profil()
    p["interventions"] = [{
        "date": "2026-01-01",
        "type_detail": "loi",
        "theme_officiel": "Pouvoir d'achat",
        "seance": {"uid": "CRS-17-001", "intitule": "Séance du soir"},
        "dossier": {"id": "AN-2026-001", "titre": "Projet de loi X"},
        "source": {"type": "assemblee_nationale", "url": "https://data.assemblee-nationale.fr/..."},
        "source_url": "https://www.assemblee-nationale.fr/...",
    }]
    assert validate_profil(p) == []


def test_validate_intervention_theme_officiel_type_invalide():
    p = _valid_profil()
    p["interventions"] = [{"date": "2026-01-01", "type_detail": "loi", "theme_officiel": 42}]
    errors = validate_profil(p)
    assert any("interventions[0].theme_officiel" in e for e in errors)


def test_validate_intervention_seance_type_invalide():
    p = _valid_profil()
    p["interventions"] = [{"date": "2026-01-01", "type_detail": "loi", "seance": "S1"}]
    errors = validate_profil(p)
    assert any("interventions[0].seance" in e for e in errors)


def test_validate_intervention_dossier_type_invalide():
    p = _valid_profil()
    p["interventions"] = [{"date": "2026-01-01", "type_detail": "loi", "dossier": ["D1"]}]
    errors = validate_profil(p)
    assert any("interventions[0].dossier" in e for e in errors)


def test_validate_intervention_source_type_invalide():
    p = _valid_profil()
    p["interventions"] = [{"date": "2026-01-01", "type_detail": "loi", "source": 123}]
    errors = validate_profil(p)
    assert any("interventions[0].source" in e for e in errors)


# ---------------------------------------------------------------------------
# Constantes exposées
# ---------------------------------------------------------------------------

def test_known_chambres_contains_expected_values():
    assert "AN" in KNOWN_CHAMBRES
    assert "Senat" in KNOWN_CHAMBRES
    assert "PE" in KNOWN_CHAMBRES
    assert "mairie" in KNOWN_CHAMBRES


def test_known_positions_contains_expected_values():
    assert "pour" in KNOWN_POSITIONS
    assert "contre" in KNOWN_POSITIONS
    assert "abstention" in KNOWN_POSITIONS
    assert "non_votant" in KNOWN_POSITIONS


def test_known_categories_contains_expected_values():
    assert "mandat_electif" in KNOWN_CATEGORIES
    assert "commission" in KNOWN_CATEGORIES
    assert "groupe_amitie" in KNOWN_CATEGORIES
    assert "groupe_politique" in KNOWN_CATEGORIES
    assert "fonction_gouvernementale" in KNOWN_CATEGORIES


def test_known_positions_hemicycle_contains_expected_values():
    assert KNOWN_POSITIONS_HEMICYCLE == {"majorite", "opposition", "minoritaire", "gouvernement"}


def test_known_modes_declenchement_contains_expected_values():
    assert KNOWN_MODES_DECLENCHEMENT == {"droit_tirage", "demande_votee"}


def test_known_types_rapport_contains_expected_values():
    assert "rapporteur_fond" in KNOWN_TYPES_RAPPORT
    assert "rapporteur_avis" in KNOWN_TYPES_RAPPORT
    assert "rapporteur_special_budget" in KNOWN_TYPES_RAPPORT
    assert "mission_information" in KNOWN_TYPES_RAPPORT


def test_known_stades_proceduraux_contains_expected_values():
    assert "depose" in KNOWN_STADES_PROCEDURAUX
    assert "adopte" in KNOWN_STADES_PROCEDURAUX
    assert "promulgue" in KNOWN_STADES_PROCEDURAUX


def test_known_types_scrutin_contains_expected_values():
    assert KNOWN_TYPES_SCRUTIN == {"public_ordinaire", "solennel", "tribune", "motion_censure"}


def test_known_types_vote_contains_expected_values():
    assert KNOWN_TYPES_VOTE == {"vote_texte", "motion_censure"}


def test_known_types_deposant_contains_expected_values():
    assert KNOWN_TYPES_DEPOSANT == {"gouvernement", "commission_rapporteur", "depute"}


def test_known_bases_irrecevabilite_contains_expected_values():
    assert KNOWN_BASES_IRRECEVABILITE == {"art. 40", "art. 45"}
