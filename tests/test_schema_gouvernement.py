import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from schema_gouvernement import (
    SCHEMA_GOUVERNEMENT_VERSION,
    KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL,
    KNOWN_CHAMBRES_DEPOT_TEXTE,
    make_empty_comptages_statuts,
    make_empty_profil_gouvernement,
    validate_profil_gouvernement,
)


# ---------------------------------------------------------------------------
# make_empty_profil_gouvernement
# ---------------------------------------------------------------------------

def test_make_empty_schema_version():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    assert g["schema_version"] == SCHEMA_GOUVERNEMENT_VERSION
    assert g["meta"]["schema_version"] == SCHEMA_GOUVERNEMENT_VERSION


def test_make_empty_type_document():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    assert g["type_document"] == "profil_gouvernement"


def test_make_empty_identifiers():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    assert g["gouvernement_id"] == "gouvernement:LECORNU"
    assert g["nom"] == "Gouvernement Lecornu"


def test_make_empty_premier_ministre_default_none():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    assert g["premier_ministre"] is None


def test_make_empty_default_lists():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    for key in ("membres", "textes", "sources"):
        assert isinstance(g[key], list)
        assert g[key] == []


def test_make_empty_periode_defaults():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    assert g["periode"]["debut"] is None
    assert g["periode"]["fin"] is None
    assert g["periode"]["actif"] is True


def test_make_empty_comptages_defaults():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    # #996 : le recensement `membres_recenses` naît à `None` — « inconnu »,
    # pas « zéro membre ». `membres_distincts`, lui, naît à `0` et c'est juste :
    # une fiche vide porte zéro membre, ce n'est pas une inconnue (#996 lot 4).
    assert g["comptages"] == {
        "membres_recenses": None,
        "membres_distincts": 0,
        # #1020 — naît à 0 comme `membres_distincts`, et pour la même raison :
        # une fiche vide porte zéro membre parlant, ce n'est pas une inconnue.
        "membres_avec_interventions": 0,
        "par_statut": make_empty_comptages_statuts(),
    }
    for statut in KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL:
        assert g["comptages"]["par_statut"][statut] == 0


def test_make_empty_meta_warnings_empty():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    assert g["meta"]["warnings"] == []


def test_make_empty_meta_genere_le_iso():
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    ts = g["meta"]["genere_le"]
    assert "T" in ts and "-" in ts


# ---------------------------------------------------------------------------
# validate_profil_gouvernement — profil valide
# ---------------------------------------------------------------------------

def _valid_gouvernement() -> dict:
    """Gouvernement minimal valide pour les tests."""
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    g["meta"]["licence_donnees"] = "Etalab"
    return g


def test_validate_valid_gouvernement_no_errors():
    assert validate_profil_gouvernement(_valid_gouvernement()) == []


def test_validate_valid_gouvernement_with_premier_ministre():
    g = _valid_gouvernement()
    g["premier_ministre"] = {
        "nom": "Sébastien Lecornu",
        "acteur_ref": "PA607469",
        "source_url": "https://www.assemblee-nationale.fr/dyn/exemple",
    }
    assert validate_profil_gouvernement(g) == []


def test_validate_valid_gouvernement_with_membre_sourced_portefeuille():
    g = _valid_gouvernement()
    g["membres"].append({
        "membre_id": "nosdeputes:bruno-le-maire",
        "nom": "Bruno Le Maire",
        "portefeuille": "Économie",
        "debut": "2025-09-09",
        "fin": None,
        "actif": True,
        "source_url": "https://www.legifrance.gouv.fr/exemple",
    })
    assert validate_profil_gouvernement(g) == []


def test_validate_valid_gouvernement_with_membre_null_portefeuille_no_source():
    g = _valid_gouvernement()
    g["membres"].append({
        "membre_id": "nosdeputes:x",
        "nom": "X",
        "portefeuille": None,
        "debut": "2025-09-09",
        "fin": None,
        "actif": True,
        "source_url": None,
    })
    assert validate_profil_gouvernement(g) == []


def test_validate_valid_gouvernement_with_texte():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "DLR5L17N50588",
        "titre": "Projet de loi de financement de la sécurité sociale 2025",
        "statut": "adopte_49_3",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": "2024-12-04",
        "sort_49_3": True,
        "initiateurs": None,
        "source_url": "https://www.assemblee-nationale.fr/dyn/exemple",
    })
    assert validate_profil_gouvernement(g) == []


def test_validate_valid_gouvernement_texte_senat():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "PLR",
        "titre": "Projet de loi",
        "statut": "depose",
        "chambre_depot_initial": "Senat",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": None,
        "initiateurs": None,
        "source_url": None,
    })
    assert validate_profil_gouvernement(g) == []


# ---------------------------------------------------------------------------
# validate_profil_gouvernement — textes[].initiateurs (#435)
# ---------------------------------------------------------------------------

def _membre(membre_id: str = "nosdeputes:bruno-le-maire") -> dict:
    return {
        "membre_id": membre_id,
        "nom": "Bruno Le Maire",
        "portefeuille": None,
        "debut": "2025-09-09",
        "fin": None,
        "actif": True,
        "source_url": None,
    }


def _texte_avec_initiateurs(initiateurs) -> dict:
    return {
        "dossier_id": "DLR5L17N50588",
        "titre": "Projet de loi test",
        "statut": "depose",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": None,
        "initiateurs": initiateurs,
        "source_url": None,
    }


def test_validate_initiateurs_resolus_et_non_resolus_acceptes():
    """Un initiateur peut être résolu vers un membre ou rester une référence AN
    brute (couverture partielle des profils pivot)."""
    g = _valid_gouvernement()
    g["membres"].append(_membre())
    g["textes"].append(_texte_avec_initiateurs([
        {"acteur_ref": "PA643210", "membre_id": "nosdeputes:bruno-le-maire"},
        {"acteur_ref": "PA999999", "membre_id": None},
    ]))
    assert validate_profil_gouvernement(g) == []


def test_validate_initiateurs_null_accepte():
    g = _valid_gouvernement()
    g["textes"].append(_texte_avec_initiateurs(None))
    assert validate_profil_gouvernement(g) == []


def test_validate_initiateurs_liste_vide_refusee():
    """`[]` affirmerait qu'aucun ministre n'a porté le texte : l'absence se dit
    `null` (règle AGENTS.md §2.5)."""
    g = _valid_gouvernement()
    g["textes"].append(_texte_avec_initiateurs([]))
    errors = validate_profil_gouvernement(g)
    assert any("initiateurs" in e and "vide" in e for e in errors)


def test_validate_initiateurs_membre_id_inconnu_de_membres_refuse():
    g = _valid_gouvernement()
    g["membres"].append(_membre())
    g["textes"].append(_texte_avec_initiateurs([
        {"acteur_ref": "PA643210", "membre_id": "nosdeputes:jamais-membre"},
    ]))
    errors = validate_profil_gouvernement(g)
    assert any("nosdeputes:jamais-membre" in e and "membres[]" in e for e in errors)


def test_validate_initiateurs_acteur_ref_vide_refuse():
    g = _valid_gouvernement()
    g["textes"].append(_texte_avec_initiateurs([{"acteur_ref": "", "membre_id": None}]))
    errors = validate_profil_gouvernement(g)
    assert any("acteur_ref" in e for e in errors)


def test_validate_initiateurs_cles_manquantes_refusees():
    g = _valid_gouvernement()
    g["textes"].append(_texte_avec_initiateurs([{"acteur_ref": "PA643210"}]))
    errors = validate_profil_gouvernement(g)
    assert any("initiateurs[0]" in e and "membre_id" in e for e in errors)


def test_validate_initiateurs_non_liste_refusee():
    g = _valid_gouvernement()
    g["textes"].append(_texte_avec_initiateurs("PA643210"))
    errors = validate_profil_gouvernement(g)
    assert any("initiateurs" in e and "liste" in e for e in errors)


def test_validate_texte_sans_cle_initiateurs_refuse():
    """`initiateurs` est une clé obligatoire de textes[] depuis #435 : un texte
    généré par une version antérieure du pipeline doit être signalé, pas
    silencieusement accepté sans lien membre → texte."""
    g = _valid_gouvernement()
    texte = _texte_avec_initiateurs(None)
    del texte["initiateurs"]
    g["textes"].append(texte)
    errors = validate_profil_gouvernement(g)
    assert any("initiateurs" in e and "manquantes" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_profil_gouvernement — erreurs détectées
# ---------------------------------------------------------------------------

def test_validate_non_dict_input():
    errors = validate_profil_gouvernement("not a dict")  # type: ignore[arg-type]
    assert errors
    assert any("dict" in e for e in errors)


def test_validate_missing_top_level_key():
    g = _valid_gouvernement()
    del g["nom"]
    errors = validate_profil_gouvernement(g)
    assert any("nom" in e for e in errors)


def test_validate_wrong_schema_version():
    g = _valid_gouvernement()
    g["schema_version"] = "99"
    errors = validate_profil_gouvernement(g)
    assert any("schema_version" in e for e in errors)


def test_validate_wrong_type_document():
    g = _valid_gouvernement()
    g["type_document"] = "profil_groupe"
    errors = validate_profil_gouvernement(g)
    assert any("type_document" in e for e in errors)


def test_validate_empty_gouvernement_id():
    g = _valid_gouvernement()
    g["gouvernement_id"] = ""
    errors = validate_profil_gouvernement(g)
    assert any("gouvernement_id" in e for e in errors)


def test_validate_gouvernement_id_wrong_prefix():
    g = _valid_gouvernement()
    g["gouvernement_id"] = "LECORNU"
    errors = validate_profil_gouvernement(g)
    assert any("gouvernement_id" in e for e in errors)


def test_validate_missing_nom():
    g = _valid_gouvernement()
    g["nom"] = ""
    errors = validate_profil_gouvernement(g)
    assert any("nom" in e for e in errors)


def test_validate_membres_not_a_list():
    g = _valid_gouvernement()
    g["membres"] = {"not": "a list"}
    errors = validate_profil_gouvernement(g)
    assert any("membres" in e for e in errors)


def test_validate_textes_not_a_list():
    g = _valid_gouvernement()
    g["textes"] = "string"
    errors = validate_profil_gouvernement(g)
    assert any("textes" in e for e in errors)


def test_validate_periode_not_a_dict():
    g = _valid_gouvernement()
    g["periode"] = "2025-09-09"
    errors = validate_profil_gouvernement(g)
    assert any("periode" in e for e in errors)


def test_validate_premier_ministre_not_a_dict():
    g = _valid_gouvernement()
    g["premier_ministre"] = "Sébastien Lecornu"
    errors = validate_profil_gouvernement(g)
    assert any("premier_ministre" in e for e in errors)


def test_validate_premier_ministre_missing_keys():
    g = _valid_gouvernement()
    g["premier_ministre"] = {"nom": "Sébastien Lecornu"}
    errors = validate_profil_gouvernement(g)
    assert any("premier_ministre" in e for e in errors)


def test_validate_meta_not_a_dict():
    g = _valid_gouvernement()
    g["meta"] = "not a dict"
    errors = validate_profil_gouvernement(g)
    assert any("meta" in e for e in errors)


def test_validate_meta_missing_key():
    g = _valid_gouvernement()
    del g["meta"]["genere_le"]
    errors = validate_profil_gouvernement(g)
    assert any("genere_le" in e for e in errors)


def test_validate_meta_schema_version_mismatch():
    g = _valid_gouvernement()
    g["meta"]["schema_version"] = "99"
    errors = validate_profil_gouvernement(g)
    assert any("meta.schema_version" in e for e in errors)


def test_validate_meta_warnings_not_a_list():
    g = _valid_gouvernement()
    g["meta"]["warnings"] = "not a list"
    errors = validate_profil_gouvernement(g)
    assert any("warnings" in e for e in errors)


# --- membres[] ---

def test_validate_membre_not_a_dict():
    g = _valid_gouvernement()
    g["membres"] = ["not a dict"]
    errors = validate_profil_gouvernement(g)
    assert any("membres[0]" in e for e in errors)


def test_validate_membre_missing_keys():
    g = _valid_gouvernement()
    g["membres"] = [{"membre_id": "x", "nom": "X"}]
    errors = validate_profil_gouvernement(g)
    assert any("membres[0]" in e and "manquantes" in e for e in errors)


def test_validate_membre_portefeuille_non_null_without_source():
    g = _valid_gouvernement()
    g["membres"].append({
        "membre_id": "nosdeputes:x",
        "nom": "X",
        "portefeuille": "Intérieur",
        "debut": "2025-09-09",
        "fin": None,
        "actif": True,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("portefeuille" in e for e in errors)


def test_validate_membre_actif_not_a_bool():
    g = _valid_gouvernement()
    g["membres"].append({
        "membre_id": "nosdeputes:x",
        "nom": "X",
        "portefeuille": None,
        "debut": "2025-09-09",
        "fin": None,
        "actif": "oui",
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("actif" in e for e in errors)


# --- textes[] ---

def test_validate_texte_not_a_dict():
    g = _valid_gouvernement()
    g["textes"] = ["not a dict"]
    errors = validate_profil_gouvernement(g)
    assert any("textes[0]" in e for e in errors)


def test_validate_texte_missing_keys():
    g = _valid_gouvernement()
    g["textes"] = [{"dossier_id": "X"}]
    errors = validate_profil_gouvernement(g)
    assert any("textes[0]" in e and "manquantes" in e for e in errors)


def test_validate_texte_unknown_statut():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "vote_favorable",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": None,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("statut inconnu" in e for e in errors)


def test_validate_texte_unknown_chambre_depot():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "depose",
        "chambre_depot_initial": "PE",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": None,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("chambre_depot_initial" in e for e in errors)


def test_validate_texte_sort_49_3_not_a_bool():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "depose",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": "oui",
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("sort_49_3" in e for e in errors)


def test_validate_texte_adopte_49_3_requires_sort_49_3_true():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "adopte_49_3",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": None,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("sort_49_3" in e and "adopte_49_3" in e for e in errors)


def test_validate_texte_sort_49_3_true_collapsed_into_adopte_rejected():
    """Point sensible AGENTS.md §2.4 : le 49.3 ne doit jamais être collapsé
    silencieusement vers 'adopte'."""
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "adopte",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": True,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("collapsé" in e for e in errors)


def test_validate_texte_rejete_49_3_requires_sort_49_3_true():
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "rejete_49_3",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": None,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("sort_49_3" in e and "rejete_49_3" in e for e in errors)


def test_validate_texte_rejete_49_3_with_sort_49_3_true_is_valid():
    """Cas réel TSORTF24 (#210) : motion de censure adoptée après 49.3 —
    doit être représentable sans erreur une fois la nomenclature étendue."""
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "rejete_49_3",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": True,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert not any("sort_49_3" in e or "rejete_49_3" in e for e in errors)


def test_validate_texte_sort_49_3_true_collapsed_into_rejete_rejected():
    """Symétrique du cas 'adopte' : le 49.3 ne doit pas non plus être
    collapsé silencieusement vers 'rejete' simple."""
    g = _valid_gouvernement()
    g["textes"].append({
        "dossier_id": "X",
        "titre": "Texte",
        "statut": "rejete",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": True,
        "initiateurs": None,
        "source_url": None,
    })
    errors = validate_profil_gouvernement(g)
    assert any("collapsé" in e for e in errors)


# --- comptages ---

def test_validate_comptages_not_a_dict():
    g = _valid_gouvernement()
    g["comptages"] = "string"
    errors = validate_profil_gouvernement(g)
    assert any("comptages" in e for e in errors)


def test_validate_comptages_par_statut_not_a_dict():
    g = _valid_gouvernement()
    g["comptages"]["par_statut"] = "string"
    errors = validate_profil_gouvernement(g)
    assert any("par_statut" in e for e in errors)


def test_validate_comptages_par_statut_missing_key():
    g = _valid_gouvernement()
    del g["comptages"]["par_statut"]["retire"]
    errors = validate_profil_gouvernement(g)
    assert any("par_statut" in e and "manquantes" in e for e in errors)


def test_validate_comptages_par_statut_unknown_key():
    g = _valid_gouvernement()
    g["comptages"]["par_statut"]["vote_favorable"] = 0
    errors = validate_profil_gouvernement(g)
    assert any("inconnues" in e for e in errors)


def test_validate_comptages_par_statut_not_an_int():
    g = _valid_gouvernement()
    g["comptages"]["par_statut"]["adopte"] = 0.15
    errors = validate_profil_gouvernement(g)
    assert any("entier brut" in e for e in errors)


def test_validate_comptages_par_statut_bool_rejected():
    """bool est une sous-classe d'int en Python : doit être explicitement rejeté."""
    g = _valid_gouvernement()
    g["comptages"]["par_statut"]["adopte"] = True
    errors = validate_profil_gouvernement(g)
    assert any("entier brut" in e for e in errors)


def test_validate_comptages_par_statut_negative():
    g = _valid_gouvernement()
    g["comptages"]["par_statut"]["adopte"] = -1
    errors = validate_profil_gouvernement(g)
    assert any("négatif" in e for e in errors)


# ---------------------------------------------------------------------------
# Nomenclature
# ---------------------------------------------------------------------------

def test_known_statuts_texte_gouvernemental():
    assert KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL == frozenset({
        "depose", "navette_en_cours", "adopte", "adopte_49_3", "adopte_cmp",
        "promulgue", "rejete", "rejete_49_3", "retire",
    })


def _texte_adopte_cmp(sort_49_3) -> dict:
    return {
        "dossier_id": "X",
        "titre": "Texte de CMP",
        "statut": "adopte_cmp",
        "chambre_depot_initial": "AN",
        "date_depot": "2024-10-10",
        "date_dernier_evenement": None,
        "sort_49_3": sort_49_3,
        "initiateurs": None,
        "source_url": None,
    }


def test_adopte_cmp_nest_pas_un_statut_49_3():
    """`adopte_cmp` (art. 45 al. 3, texte de CMP) est une voie procédurale
    distincte du 49.3 : sort_49_3 = True doit être refusé, sous peine de
    confondre deux faits procéduraux différents (AGENTS.md §2.4)."""
    g = _valid_gouvernement()
    g["textes"].append(_texte_adopte_cmp(sort_49_3=True))
    assert any("sort_49_3" in e for e in validate_profil_gouvernement(g))


def test_adopte_cmp_accepte_sans_49_3():
    g = _valid_gouvernement()
    g["textes"].append(_texte_adopte_cmp(sort_49_3=False))
    g["comptages"]["par_statut"]["adopte_cmp"] += 1
    assert validate_profil_gouvernement(g) == []


def test_comptages_vides_derivent_de_la_nomenclature():
    """`adopte_cmp` doit apparaître dans les comptages sans énumération
    codée en dur : make_empty_comptages_statuts() dérive de la nomenclature,
    donc tout futur statut se propage sans modification supplémentaire."""
    assert set(make_empty_comptages_statuts()) == KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL
    assert make_empty_comptages_statuts()["adopte_cmp"] == 0


def test_known_chambres_depot_texte():
    assert KNOWN_CHAMBRES_DEPOT_TEXTE == frozenset({"AN", "Senat"})


def test_no_rate_or_score_field_in_empty_profil():
    """Revue manuelle explicite (AGENTS.md §2.1) : aucun champ de taux, pourcentage
    ou classement dans le schéma — comptages n'expose que des entiers bruts."""
    g = make_empty_profil_gouvernement("gouvernement:LECORNU", "Gouvernement Lecornu")
    suspect_substrings = ("taux", "ratio", "pourcentage", "score", "classement", "rang")

    def _walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                assert not any(s in key.lower() for s in suspect_substrings), key
                _walk(value)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(g)
