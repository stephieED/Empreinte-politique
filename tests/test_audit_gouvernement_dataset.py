import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_gouvernement_dataset import (
    _build_arg_parser,
    build_report,
    compute_agregation_warnings,
    compute_coherence_schema_version,
    compute_comptages_agreges,
    compute_couverture_textes,
    compute_distribution_membres_textes,
    compute_doublons_gouvernement_id,
    compute_fraicheur_sources,
    compute_gouvernements_perimes,
    compute_plage_dates_gouvernements,
    compute_presence_meta,
    compute_presence_premier_ministre,
    compute_repartition_periode_actif,
    compute_taux_portefeuille_renseigne,
    compute_validation_schema,
    generate_markdown_report,
    load_gouvernement_directory,
    main,
)
from schema_gouvernement import make_empty_comptages_statuts


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "audit_gouvernement"


# ---------------------------------------------------------------------------
# load_gouvernement_directory : chargement des fixtures du dépôt
# ---------------------------------------------------------------------------

def test_load_gouvernement_directory_charge_les_gouvernements_valides():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    ids = {g["gouvernement_id"] for g in gouvernements_valides}
    assert ids == {"gouvernement:LECORNU", "gouvernement:BARNIER"}
    assert len(gouvernements_valides) == 3  # LECORNU apparaît deux fois (doublon volontaire)


def test_load_gouvernement_directory_scanne_recursivement():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    # sous_dossier/gouvernement-LECORNU.json doit être trouvé malgré tout.
    assert sum(1 for g in gouvernements_valides if g["gouvernement_id"] == "gouvernement:LECORNU") == 2


def test_load_gouvernement_directory_ne_s_interrompt_pas_sur_fichier_invalide():
    gouvernements_valides, erreurs_lecture = load_gouvernement_directory(FIXTURES_DIR)

    assert len(gouvernements_valides) == 3
    assert len(erreurs_lecture) == 1


def test_load_gouvernement_directory_contenu_erreurs_lecture():
    _, erreurs_lecture = load_gouvernement_directory(FIXTURES_DIR)

    assert len(erreurs_lecture) == 1
    erreur = erreurs_lecture[0]
    assert set(erreur.keys()) == {"fichier", "erreur"}
    assert erreur["fichier"].endswith("gouvernement-INVALIDE.json")
    assert isinstance(erreur["erreur"], str)
    assert erreur["erreur"]  # message non vide


# ---------------------------------------------------------------------------
# load_gouvernement_directory : cas limites construits en mémoire (tmp_path)
# ---------------------------------------------------------------------------

def test_load_gouvernement_directory_repertoire_vide(tmp_path):
    gouvernements_valides, erreurs_lecture = load_gouvernement_directory(tmp_path)

    assert gouvernements_valides == []
    assert erreurs_lecture == []


def test_load_gouvernement_directory_ignore_fichiers_hors_convention(tmp_path):
    (tmp_path / "notes.txt").write_text("pas un gouvernement", encoding="utf-8")
    (tmp_path / "autre.json").write_text("{}", encoding="utf-8")

    gouvernements_valides, erreurs_lecture = load_gouvernement_directory(tmp_path)

    assert gouvernements_valides == []
    assert erreurs_lecture == []


def test_load_gouvernement_directory_objet_racine_non_dict(tmp_path):
    (tmp_path / "gouvernement-X.json").write_text("[1, 2, 3]", encoding="utf-8")

    gouvernements_valides, erreurs_lecture = load_gouvernement_directory(tmp_path)

    assert gouvernements_valides == []
    assert len(erreurs_lecture) == 1
    assert erreurs_lecture[0]["fichier"].endswith("gouvernement-X.json")


def test_load_gouvernement_directory_est_pure(tmp_path):
    fichier = tmp_path / "gouvernement-X.json"
    contenu = {"schema_version": "1", "gouvernement_id": "gouvernement:X"}
    fichier.write_text(json.dumps(contenu), encoding="utf-8")

    load_gouvernement_directory(tmp_path)

    assert json.loads(fichier.read_text(encoding="utf-8")) == contenu


# ---------------------------------------------------------------------------
# Fixtures minimalistes en mémoire.
# ---------------------------------------------------------------------------

def make_comptages(**overrides):
    # Dérivé de la nomenclature fermée plutôt qu'énuméré : un statut ajouté
    # au schéma (ex. adopte_cmp en #397) rendait sinon ces fixtures invalides
    # au schéma, faisant échouer des tests sans rapport avec le changement.
    par_statut = make_empty_comptages_statuts()
    par_statut.update(overrides)
    return {"par_statut": par_statut}


def gouvernement(gouvernement_id="gouvernement:X", actif=True, nb_membres=0, nb_textes=0,
                  premier_ministre=None, comptages=None, sources=None):
    return {
        "gouvernement_id": gouvernement_id,
        "periode": {"debut": "2025-01-01", "fin": None, "actif": actif},
        "premier_ministre": premier_ministre,
        "membres": [{"membre_id": f"m{i}", "portefeuille": None} for i in range(nb_membres)],
        "textes": [{"dossier_id": f"t{i}"} for i in range(nb_textes)],
        "comptages": comptages if comptages is not None else make_comptages(),
        "sources": sources if sources is not None else [],
    }


# ---------------------------------------------------------------------------
# compute_repartition_periode_actif
# ---------------------------------------------------------------------------

def test_compute_repartition_periode_actif_liste_vide():
    resultat = compute_repartition_periode_actif([])

    assert resultat == {"total_gouvernements": 0, "actifs": 0, "inactifs": 0, "indetermines": 0}


def test_compute_repartition_periode_actif_repartit_les_cas():
    gouvernements = [
        gouvernement(actif=True), gouvernement(actif=False), gouvernement(actif=True),
    ]

    resultat = compute_repartition_periode_actif(gouvernements)

    assert resultat == {"total_gouvernements": 3, "actifs": 2, "inactifs": 1, "indetermines": 0}


def test_compute_repartition_periode_actif_periode_absente_ou_invalide_indeterminee():
    gouvernements = [
        {"gouvernement_id": "gouvernement:X"},
        {"gouvernement_id": "gouvernement:Y", "periode": "pas un dict"},
        {"gouvernement_id": "gouvernement:Z", "periode": {"actif": None}},
    ]

    resultat = compute_repartition_periode_actif(gouvernements)

    assert resultat == {"total_gouvernements": 3, "actifs": 0, "inactifs": 0, "indetermines": 3}


# ---------------------------------------------------------------------------
# compute_distribution_membres_textes
# ---------------------------------------------------------------------------

def test_compute_distribution_membres_textes_liste_vide():
    resultat = compute_distribution_membres_textes([])

    assert resultat == {
        "membres": {"min": None, "max": None, "mediane": None, "moyenne": None},
        "textes": {"min": None, "max": None, "mediane": None, "moyenne": None},
    }


def test_compute_distribution_membres_textes_distribution():
    gouvernements = [
        gouvernement(nb_membres=2, nb_textes=1),
        gouvernement(nb_membres=4, nb_textes=3),
    ]

    resultat = compute_distribution_membres_textes(gouvernements)

    assert resultat["membres"] == {"min": 2, "max": 4, "mediane": 3, "moyenne": 3.0}
    assert resultat["textes"] == {"min": 1, "max": 3, "mediane": 2, "moyenne": 2.0}


def test_compute_distribution_membres_textes_champs_absents_comptent_zero():
    resultat = compute_distribution_membres_textes([{"gouvernement_id": "gouvernement:X"}])

    assert resultat["membres"]["min"] == 0
    assert resultat["textes"]["min"] == 0


# ---------------------------------------------------------------------------
# compute_comptages_agreges
# ---------------------------------------------------------------------------

def test_compute_comptages_agreges_liste_vide():
    resultat = compute_comptages_agreges([])

    assert resultat == make_empty_comptages_statuts()


def test_compute_comptages_agreges_somme_tous_gouvernements():
    gouvernements = [
        gouvernement(comptages=make_comptages(adopte=2, adopte_49_3=1)),
        gouvernement(comptages=make_comptages(adopte=3, rejete_49_3=1)),
    ]

    resultat = compute_comptages_agreges(gouvernements)

    assert resultat["adopte"] == 5
    assert resultat["adopte_49_3"] == 1
    assert resultat["rejete_49_3"] == 1


def test_compute_comptages_agreges_bloc_absent_ou_invalide_ignore():
    gouvernements = [
        {"gouvernement_id": "gouvernement:X"},
        {"gouvernement_id": "gouvernement:Y", "comptages": None},
        gouvernement(comptages=make_comptages(adopte=5)),
    ]

    resultat = compute_comptages_agreges(gouvernements)

    assert resultat["adopte"] == 5


# ---------------------------------------------------------------------------
# compute_presence_premier_ministre
# ---------------------------------------------------------------------------

def test_compute_presence_premier_ministre_liste_vide():
    assert compute_presence_premier_ministre([]) == {"renseignes": 0, "total": 0, "taux_pct": 0.0}


def test_compute_presence_premier_ministre_distingue_present_et_absent():
    gouvernements = [
        gouvernement(premier_ministre={"nom": "A", "acteur_ref": None, "source_url": None}),
        gouvernement(premier_ministre=None),
    ]

    resultat = compute_presence_premier_ministre(gouvernements)

    assert resultat == {"renseignes": 1, "total": 2, "taux_pct": 50.0}


def test_compute_presence_premier_ministre_champ_absent():
    resultat = compute_presence_premier_ministre([{"gouvernement_id": "gouvernement:X"}])

    assert resultat == {"renseignes": 0, "total": 1, "taux_pct": 0.0}


# ---------------------------------------------------------------------------
# compute_taux_portefeuille_renseigne
# ---------------------------------------------------------------------------

def test_compute_taux_portefeuille_renseigne_liste_vide():
    assert compute_taux_portefeuille_renseigne([]) == {"renseignes": 0, "total": 0, "taux_pct": 0.0}


def test_compute_taux_portefeuille_renseigne_agrege_tous_gouvernements():
    gouvernements = [
        {
            "gouvernement_id": "gouvernement:X",
            "membres": [
                {"membre_id": "a", "portefeuille": "Économie"},
                {"membre_id": "b", "portefeuille": None},
            ],
        },
        {
            "gouvernement_id": "gouvernement:Y",
            "membres": [{"membre_id": "c", "portefeuille": "Santé"}],
        },
    ]

    resultat = compute_taux_portefeuille_renseigne(gouvernements)

    assert resultat == {"renseignes": 2, "total": 3, "taux_pct": round(200 / 3, 2)}


def test_compute_taux_portefeuille_renseigne_membres_absents_ne_contribuent_pas():
    resultat = compute_taux_portefeuille_renseigne([{"gouvernement_id": "gouvernement:X"}])

    assert resultat == {"renseignes": 0, "total": 0, "taux_pct": 0.0}


# ---------------------------------------------------------------------------
# compute_presence_meta
# ---------------------------------------------------------------------------

def test_compute_presence_meta_liste_vide():
    assert compute_presence_meta([]) == {"renseignes": 0, "total": 0, "taux_pct": 0.0}


def test_compute_presence_meta_distingue_present_et_absent():
    gouvernements = [
        {"gouvernement_id": "gouvernement:X", "meta": {"schema_version": "1", "warnings": []}},
        {"gouvernement_id": "gouvernement:Y", "meta": None},
        {"gouvernement_id": "gouvernement:Z"},
    ]

    resultat = compute_presence_meta(gouvernements)

    assert resultat == {"renseignes": 1, "total": 3, "taux_pct": round(100 / 3, 2)}


# ---------------------------------------------------------------------------
# compute_validation_schema
# ---------------------------------------------------------------------------

def test_compute_validation_schema_liste_vide():
    assert compute_validation_schema([]) == {
        "total_gouvernements": 0, "nb_gouvernements_invalides": 0, "gouvernements_invalides": [],
    }


def test_compute_validation_schema_gouvernements_valides_des_fixtures():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    resultat = compute_validation_schema(gouvernements_valides)

    assert resultat["total_gouvernements"] == 3
    assert resultat["nb_gouvernements_invalides"] == 0
    assert resultat["gouvernements_invalides"] == []


def test_compute_validation_schema_detecte_les_erreurs():
    gouvernements = [{"gouvernement_id": "gouvernement:X"}]  # clés obligatoires manquantes

    resultat = compute_validation_schema(gouvernements)

    assert resultat["nb_gouvernements_invalides"] == 1
    entree = resultat["gouvernements_invalides"][0]
    assert entree["gouvernement_id"] == "gouvernement:X"
    assert entree["erreurs"]  # au moins une erreur remontée


def test_compute_validation_schema_detecte_le_collapse_du_49_3():
    from schema_gouvernement import make_empty_profil_gouvernement

    profil = make_empty_profil_gouvernement("gouvernement:X", "Gouvernement X")
    profil["textes"] = [{
        "dossier_id": "d1", "titre": "t", "statut": "adopte",
        "chambre_depot_initial": "AN", "date_depot": "2025-01-01",
        "date_dernier_evenement": "2025-01-02", "sort_49_3": True,
            "initiateurs": None, "source_url": None,
    }]

    resultat = compute_validation_schema([profil])

    assert resultat["nb_gouvernements_invalides"] == 1
    assert any("49_3" in e or "49.3" in e for e in resultat["gouvernements_invalides"][0]["erreurs"])


def test_compute_validation_schema_trie_par_gouvernement_id():
    gouvernements = [{"gouvernement_id": "gouvernement:Z"}, {"gouvernement_id": "gouvernement:A"}]

    resultat = compute_validation_schema(gouvernements)

    assert [e["gouvernement_id"] for e in resultat["gouvernements_invalides"]] == [
        "gouvernement:A", "gouvernement:Z",
    ]


# ---------------------------------------------------------------------------
# compute_coherence_schema_version
# ---------------------------------------------------------------------------

def test_compute_coherence_schema_version_liste_vide():
    assert compute_coherence_schema_version([]) == {"gouvernements_incoherents": []}


def test_compute_coherence_schema_version_coherente():
    gouvernements = [{"gouvernement_id": "gouvernement:X", "schema_version": "1", "meta": {"schema_version": "1"}}]

    assert compute_coherence_schema_version(gouvernements) == {"gouvernements_incoherents": []}


def test_compute_coherence_schema_version_divergente():
    gouvernements = [{"gouvernement_id": "gouvernement:X", "schema_version": "1", "meta": {"schema_version": "2"}}]

    resultat = compute_coherence_schema_version(gouvernements)

    assert resultat == {
        "gouvernements_incoherents": [
            {"gouvernement_id": "gouvernement:X", "schema_version": "1", "meta_schema_version": "2"}
        ]
    }


def test_compute_coherence_schema_version_meta_absente_ou_invalide():
    gouvernements = [
        {"gouvernement_id": "gouvernement:X", "schema_version": "1"},
        {"gouvernement_id": "gouvernement:Y", "schema_version": "1", "meta": "pas un dict"},
    ]

    resultat = compute_coherence_schema_version(gouvernements)

    assert {g["gouvernement_id"] for g in resultat["gouvernements_incoherents"]} == {
        "gouvernement:X", "gouvernement:Y",
    }
    assert all(g["meta_schema_version"] is None for g in resultat["gouvernements_incoherents"])


# ---------------------------------------------------------------------------
# compute_doublons_gouvernement_id
# ---------------------------------------------------------------------------

def test_compute_doublons_gouvernement_id_liste_vide():
    assert compute_doublons_gouvernement_id([]) == {"doublons": []}


def test_compute_doublons_gouvernement_id_sans_doublon():
    gouvernements = [{"gouvernement_id": "gouvernement:X"}, {"gouvernement_id": "gouvernement:Y"}]

    assert compute_doublons_gouvernement_id(gouvernements) == {"doublons": []}


def test_compute_doublons_gouvernement_id_detecte_les_doublons():
    gouvernements = [
        {"gouvernement_id": "gouvernement:X"}, {"gouvernement_id": "gouvernement:X"},
        {"gouvernement_id": "gouvernement:Y"}, {"gouvernement_id": "gouvernement:X"},
    ]

    resultat = compute_doublons_gouvernement_id(gouvernements)

    assert resultat == {"doublons": [{"gouvernement_id": "gouvernement:X", "occurrences": 3}]}


def test_compute_doublons_gouvernement_id_ignore_id_absent_ou_vide():
    gouvernements = [{"gouvernement_id": ""}, {"gouvernement_id": ""}, {}, {}]

    assert compute_doublons_gouvernement_id(gouvernements) == {"doublons": []}


def test_compute_doublons_gouvernement_id_sur_les_fixtures_du_depot():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    resultat = compute_doublons_gouvernement_id(gouvernements_valides)

    assert resultat == {"doublons": [{"gouvernement_id": "gouvernement:LECORNU", "occurrences": 2}]}


# ---------------------------------------------------------------------------
# Fixtures pour compute_fraicheur_sources / compute_gouvernements_perimes.
# ---------------------------------------------------------------------------

REFERENCE = datetime(2026, 8, 9, tzinfo=timezone.utc)


def source(type_source, jours_anciennete):
    synchro = REFERENCE - timedelta(days=jours_anciennete)
    return {"type": type_source, "url": "u", "synchro_le": synchro.isoformat()}


def gouvernement_sources(gouvernement_id, *sources):
    return {"gouvernement_id": gouvernement_id, "sources": list(sources)}


# ---------------------------------------------------------------------------
# compute_fraicheur_sources
# ---------------------------------------------------------------------------

def test_compute_fraicheur_sources_liste_vide():
    resultat = compute_fraicheur_sources([], reference_date=REFERENCE)

    assert resultat == {"total_sources_datees": 0, "par_type_source": {}}


def test_compute_fraicheur_sources_min_max_mediane_moyenne():
    gouvernements = [
        gouvernement_sources("a", source("assemblee_nationale", 0)),
        gouvernement_sources("b", source("assemblee_nationale", 10)),
        gouvernement_sources("c", source("assemblee_nationale", 20)),
    ]

    resultat = compute_fraicheur_sources(gouvernements, reference_date=REFERENCE)
    stats = resultat["par_type_source"]["assemblee_nationale"]

    assert resultat["total_sources_datees"] == 3
    assert stats["nombre_sources"] == 3
    assert stats["min_jours"] == 0
    assert stats["max_jours"] == 20
    assert stats["mediane_jours"] == 10
    assert stats["moyenne_jours"] == 10.0


def test_compute_fraicheur_sources_regroupe_par_type():
    gouvernements = [gouvernement_sources("a", source("assemblee_nationale", 5), source("senat", 50))]

    resultat = compute_fraicheur_sources(gouvernements, reference_date=REFERENCE)

    assert set(resultat["par_type_source"]) == {"assemblee_nationale", "senat"}
    assert resultat["par_type_source"]["assemblee_nationale"]["min_jours"] == 5
    assert resultat["par_type_source"]["senat"]["min_jours"] == 50


def test_compute_fraicheur_sources_type_absent_regroupe_sous_null():
    gouvernements = [gouvernement_sources("a", {"url": "u", "synchro_le": REFERENCE.isoformat()})]

    resultat = compute_fraicheur_sources(gouvernements, reference_date=REFERENCE)

    assert resultat["par_type_source"]["null"]["nombre_sources"] == 1


def test_compute_fraicheur_sources_ignore_synchro_le_invalide_ou_absente():
    gouvernements = [
        gouvernement_sources("a", {"type": "assemblee_nationale", "url": "u", "synchro_le": "pas-une-date"}),
        gouvernement_sources("b", {"type": "assemblee_nationale", "url": "u"}),
        gouvernement_sources("c", source("assemblee_nationale", 1)),
    ]

    resultat = compute_fraicheur_sources(gouvernements, reference_date=REFERENCE)

    assert resultat["total_sources_datees"] == 1
    assert resultat["par_type_source"]["assemblee_nationale"]["nombre_sources"] == 1


def test_compute_fraicheur_sources_ignore_gouvernements_sans_sources():
    resultat = compute_fraicheur_sources(
        [gouvernement_sources("a"), {"gouvernement_id": "b"}], reference_date=REFERENCE
    )

    assert resultat == {"total_sources_datees": 0, "par_type_source": {}}


def test_compute_fraicheur_sources_sans_reference_date_utilise_maintenant():
    hier = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    gouvernements = [gouvernement_sources("a", {"type": "assemblee_nationale", "url": "u", "synchro_le": hier})]

    resultat = compute_fraicheur_sources(gouvernements)

    assert resultat["par_type_source"]["assemblee_nationale"]["min_jours"] == 1


# ---------------------------------------------------------------------------
# compute_gouvernements_perimes
# ---------------------------------------------------------------------------

def test_compute_gouvernements_perimes_toutes_sources_perimees():
    gouvernements = [gouvernement_sources("a", source("assemblee_nationale", 100))]

    resultat = compute_gouvernements_perimes(gouvernements, staleness_days=30, reference_date=REFERENCE)

    assert resultat == ["a"]


def test_compute_gouvernements_perimes_une_source_fraiche_suffit_a_exclure():
    gouvernements = [gouvernement_sources("a", source("assemblee_nationale", 100), source("senat", 5))]

    resultat = compute_gouvernements_perimes(gouvernements, staleness_days=30, reference_date=REFERENCE)

    assert resultat == []


def test_compute_gouvernements_perimes_seuil_variable():
    gouvernements = [gouvernement_sources("a", source("assemblee_nationale", 15))]

    assert compute_gouvernements_perimes(gouvernements, staleness_days=10, reference_date=REFERENCE) == ["a"]
    assert compute_gouvernements_perimes(gouvernements, staleness_days=20, reference_date=REFERENCE) == []


def test_compute_gouvernements_perimes_exactement_au_seuil_n_est_pas_perime():
    gouvernements = [gouvernement_sources("a", source("assemblee_nationale", 30))]

    resultat = compute_gouvernements_perimes(gouvernements, staleness_days=30, reference_date=REFERENCE)

    assert resultat == []


def test_compute_gouvernements_perimes_aucune_source_n_est_jamais_perime():
    gouvernements = [gouvernement_sources("a"), {"gouvernement_id": "b"}]

    resultat = compute_gouvernements_perimes(gouvernements, staleness_days=0, reference_date=REFERENCE)

    assert resultat == []


def test_compute_gouvernements_perimes_trie_les_resultats():
    gouvernements = [
        gouvernement_sources("z", source("assemblee_nationale", 100)),
        gouvernement_sources("a", source("assemblee_nationale", 100)),
    ]

    resultat = compute_gouvernements_perimes(gouvernements, staleness_days=30, reference_date=REFERENCE)

    assert resultat == ["a", "z"]


# ---------------------------------------------------------------------------
# compute_agregation_warnings
# ---------------------------------------------------------------------------

def gouvernement_warnings(gouvernement_id, *warnings):
    return {"gouvernement_id": gouvernement_id, "meta": {"warnings": list(warnings)}}


def test_compute_agregation_warnings_aucun_gouvernement():
    assert compute_agregation_warnings([]) == {"total_warnings": 0, "par_type": {}}


def test_compute_agregation_warnings_gouvernements_sans_warnings():
    gouvernements = [
        gouvernement_warnings("a"), {"gouvernement_id": "b"}, {"gouvernement_id": "c", "meta": {}},
    ]

    resultat = compute_agregation_warnings(gouvernements)

    assert resultat == {"total_warnings": 0, "par_type": {}}


def test_compute_agregation_warnings_type_par_prefixe_avant_les_deux_points():
    gouvernements = [
        gouvernement_warnings("a", "couverture_ministerielle : portefeuille non confirme."),
        gouvernement_warnings("b", "couverture_ministerielle : portefeuille non confirme."),
    ]

    resultat = compute_agregation_warnings(gouvernements)

    assert resultat["total_warnings"] == 2
    assert resultat["par_type"]["couverture_ministerielle"] == {
        "frequence": 2, "gouvernement_ids": ["a", "b"],
    }


def test_compute_agregation_warnings_message_sans_deux_points_utilise_le_message_entier():
    gouvernements = [gouvernement_warnings("a", "dossier exclu de textes[].")]

    resultat = compute_agregation_warnings(gouvernements)

    assert resultat["par_type"] == {
        "dossier exclu de textes[].": {"frequence": 1, "gouvernement_ids": ["a"]},
    }


def test_compute_agregation_warnings_plusieurs_types_et_frequences():
    gouvernements = [
        gouvernement_warnings("a", "statut inconnu : x", "chambre inconnue : y"),
        gouvernement_warnings("b", "statut inconnu : z"),
    ]

    resultat = compute_agregation_warnings(gouvernements)

    assert resultat["total_warnings"] == 3
    assert resultat["par_type"]["statut inconnu"] == {"frequence": 2, "gouvernement_ids": ["a", "b"]}
    assert resultat["par_type"]["chambre inconnue"] == {"frequence": 1, "gouvernement_ids": ["a"]}


def test_compute_agregation_warnings_meme_type_deux_fois_meme_gouvernement_ids_dedupliques():
    gouvernements = [gouvernement_warnings("a", "statut inconnu : x", "statut inconnu : y")]

    resultat = compute_agregation_warnings(gouvernements)

    assert resultat["par_type"]["statut inconnu"] == {"frequence": 2, "gouvernement_ids": ["a"]}


def test_compute_agregation_warnings_sur_les_fixtures_du_depot():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    resultat = compute_agregation_warnings(gouvernements_valides)

    assert resultat["total_warnings"] == 1
    assert resultat["par_type"]["couverture_ministerielle"]["gouvernement_ids"] == [
        "gouvernement:BARNIER",
    ]


# ---------------------------------------------------------------------------
# Toutes les fonctions compute_* restent pures et sérialisables en JSON
# sur le corpus de fixtures du dépôt.
# ---------------------------------------------------------------------------

def test_toutes_les_fonctions_compute_sur_les_fixtures_du_depot_sont_serialisables():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    rapport = {
        "repartition_periode_actif": compute_repartition_periode_actif(gouvernements_valides),
        "distribution_membres_textes": compute_distribution_membres_textes(gouvernements_valides),
        "comptages_agreges": compute_comptages_agreges(gouvernements_valides),
        "presence_premier_ministre": compute_presence_premier_ministre(gouvernements_valides),
        "taux_portefeuille_renseigne": compute_taux_portefeuille_renseigne(gouvernements_valides),
        "presence_meta": compute_presence_meta(gouvernements_valides),
        "validation_schema": compute_validation_schema(gouvernements_valides),
        "coherence_schema_version": compute_coherence_schema_version(gouvernements_valides),
        "doublons_gouvernement_id": compute_doublons_gouvernement_id(gouvernements_valides),
        "fraicheur_sources": compute_fraicheur_sources(gouvernements_valides, reference_date=REFERENCE),
        "gouvernements_perimes": compute_gouvernements_perimes(
            gouvernements_valides, staleness_days=30, reference_date=REFERENCE
        ),
        "plage_dates_gouvernements": compute_plage_dates_gouvernements(gouvernements_valides),
        "warnings": compute_agregation_warnings(gouvernements_valides),
    }

    json.dumps(rapport, ensure_ascii=False)


# ---------------------------------------------------------------------------
# build_report
# ---------------------------------------------------------------------------

def test_build_report_structure_top_level_keys():
    rapport = build_report([], [], staleness_days=30, reference_date=REFERENCE)

    assert set(rapport.keys()) == {
        "meta", "volumetrie", "completude", "coherence", "fraicheur",
        "couverture_textes", "plage_dates_gouvernements", "warnings", "erreurs_lecture",
    }
    assert set(rapport["volumetrie"].keys()) == {
        "repartition_periode_actif", "distribution_membres_textes", "comptages_agreges",
    }
    assert set(rapport["completude"].keys()) == {
        "presence_premier_ministre", "taux_portefeuille_renseigne", "presence_meta",
    }
    assert set(rapport["coherence"].keys()) == {
        "validation_schema", "coherence_schema_version", "doublons_gouvernement_id",
    }
    assert set(rapport["fraicheur"].keys()) == {"fraicheur_sources", "gouvernements_perimes"}


def test_build_report_meta_section():
    erreurs = [{"fichier": "x.json", "erreur": "boom"}]
    gouvernements = [gouvernement_sources("a", source("assemblee_nationale", 5))]

    rapport = build_report(gouvernements, erreurs, staleness_days=15, reference_date=REFERENCE)

    assert rapport["meta"] == {
        "genere_le": REFERENCE.isoformat(),
        "total_gouvernements": 1,
        "total_erreurs_lecture": 1,
        "staleness_days": 15,
    }


def test_build_report_erreurs_lecture_passthrough():
    erreurs = [{"fichier": "a.json", "erreur": "JSON invalide"}]

    rapport = build_report([], erreurs, reference_date=REFERENCE)

    assert rapport["erreurs_lecture"] == erreurs


def test_build_report_delegue_aux_fonctions_compute():
    gouvernements = [
        gouvernement(gouvernement_id="a", actif=True, nb_membres=2),
        gouvernement(gouvernement_id="b", actif=False, nb_textes=1),
    ]
    erreurs = []

    rapport = build_report(gouvernements, erreurs, staleness_days=30, reference_date=REFERENCE)

    assert (
        rapport["volumetrie"]["repartition_periode_actif"]
        == compute_repartition_periode_actif(gouvernements)
    )
    assert (
        rapport["volumetrie"]["distribution_membres_textes"]
        == compute_distribution_membres_textes(gouvernements)
    )
    assert rapport["volumetrie"]["comptages_agreges"] == compute_comptages_agreges(gouvernements)
    assert (
        rapport["completude"]["presence_premier_ministre"]
        == compute_presence_premier_ministre(gouvernements)
    )
    assert (
        rapport["completude"]["taux_portefeuille_renseigne"]
        == compute_taux_portefeuille_renseigne(gouvernements)
    )
    assert rapport["completude"]["presence_meta"] == compute_presence_meta(gouvernements)
    assert rapport["coherence"]["validation_schema"] == compute_validation_schema(gouvernements)
    assert (
        rapport["coherence"]["coherence_schema_version"]
        == compute_coherence_schema_version(gouvernements)
    )
    assert (
        rapport["coherence"]["doublons_gouvernement_id"]
        == compute_doublons_gouvernement_id(gouvernements)
    )
    assert (
        rapport["fraicheur"]["fraicheur_sources"]
        == compute_fraicheur_sources(gouvernements, reference_date=REFERENCE)
    )
    assert (
        rapport["fraicheur"]["gouvernements_perimes"]
        == compute_gouvernements_perimes(gouvernements, staleness_days=30, reference_date=REFERENCE)
    )
    assert (
        rapport["plage_dates_gouvernements"]
        == compute_plage_dates_gouvernements(gouvernements)
    )
    assert rapport["warnings"] == compute_agregation_warnings(gouvernements)


def test_build_report_staleness_days_par_defaut():
    rapport = build_report([], [], reference_date=REFERENCE)

    assert rapport["meta"]["staleness_days"] == 30


def test_build_report_sans_reference_date_utilise_maintenant():
    rapport = build_report([], [])

    genere_le = datetime.fromisoformat(rapport["meta"]["genere_le"])
    assert (datetime.now(timezone.utc) - genere_le).total_seconds() < 5


def test_build_report_sur_les_fixtures_du_depot():
    gouvernements_valides, erreurs_lecture = load_gouvernement_directory(FIXTURES_DIR)

    rapport = build_report(gouvernements_valides, erreurs_lecture, staleness_days=30, reference_date=REFERENCE)

    assert rapport["meta"]["total_gouvernements"] == 3
    assert rapport["meta"]["total_erreurs_lecture"] == 1
    # Le rapport doit rester intégralement sérialisable en JSON.
    json.dumps(rapport, ensure_ascii=False)


# ---------------------------------------------------------------------------
# compute_couverture_textes (#399)
# ---------------------------------------------------------------------------

def gouvernement_periode(gouvernement_id, debut, fin, textes=None, nom=None):
    """Profil minimal : seuls `periode` et `textes` comptent pour la couverture."""
    profil = {
        "gouvernement_id": gouvernement_id,
        "nom": nom or gouvernement_id,
        "periode": {"debut": debut, "fin": fin, "actif": fin is None},
    }
    if textes is not None:
        profil["textes"] = textes
    return profil


def test_compute_couverture_textes_liste_vide():
    resultat = compute_couverture_textes([])

    assert resultat["lignes"] == []
    assert resultat["sans_texte_hors_couverture"] == []
    assert resultat["sans_texte_dans_couverture"] == []
    assert resultat["borne_couverture"] == "2012-06-20"


def test_compute_couverture_textes_gouvernement_hors_couverture_sans_texte():
    # Fillon II : période antérieure aux archives ingérées — l'absence de
    # texte vient de la source, ce n'est pas un zéro constaté.
    gouvernements = [gouvernement_periode("gouvernement:FILLON_2", "2007-06-19", "2010-11-13", [])]

    resultat = compute_couverture_textes(gouvernements)

    assert resultat["lignes"][0]["statut_couverture"] == "hors_couverture"
    assert resultat["sans_texte_hors_couverture"] == ["gouvernement:FILLON_2"]
    assert resultat["sans_texte_dans_couverture"] == []


def test_compute_couverture_textes_gouvernement_couvert_sans_texte():
    # Période couverte et pourtant vide : anomalie réelle, à signaler.
    gouvernements = [gouvernement_periode("gouvernement:X", "2024-07-18", None, [])]

    resultat = compute_couverture_textes(gouvernements)

    assert resultat["lignes"][0]["statut_couverture"] == "couverte"
    assert resultat["sans_texte_dans_couverture"] == ["gouvernement:X"]
    assert resultat["sans_texte_hors_couverture"] == []


def test_compute_couverture_textes_gouvernement_couvert_avec_textes_nest_pas_signale():
    gouvernements = [
        gouvernement_periode("gouvernement:X", "2024-07-18", None, [texte(date_depot="2024-09-01")])
    ]

    resultat = compute_couverture_textes(gouvernements)

    assert resultat["sans_texte_dans_couverture"] == []
    assert resultat["sans_texte_hors_couverture"] == []
    assert resultat["lignes"][0]["nb_textes"] == 1


def test_compute_couverture_textes_champ_textes_absent_reste_none_jamais_zero():
    # AGENTS.md §2.5 : un champ absent est une donnée manquante, pas un 0.
    gouvernements = [gouvernement_periode("gouvernement:X", "2024-07-18", None, textes=None)]

    resultat = compute_couverture_textes(gouvernements)

    assert resultat["lignes"][0]["nb_textes"] is None


def test_compute_couverture_textes_liste_vide_est_bien_un_zero_observe():
    gouvernements = [gouvernement_periode("gouvernement:X", "2024-07-18", None, [])]

    assert compute_couverture_textes(gouvernements)["lignes"][0]["nb_textes"] == 0


def test_compute_couverture_textes_repartition_par_statut():
    gouvernements = [
        gouvernement_periode("gouvernement:HORS", "2007-06-19", "2010-11-13", []),
        # #1019 — la borne ayant reculé au 2012-06-20, l'ancienne fixture
        # (2017-06-20) est devenue entièrement couverte. Ayrault II est le cas
        # partiel RÉEL : il commence la veille de l'ouverture de la XIV.
        gouvernement_periode("gouvernement:PARTIEL", "2012-06-19", "2014-03-31", []),
        gouvernement_periode("gouvernement:COUVERT", "2024-07-18", None, []),
        gouvernement_periode("gouvernement:INDETERMINE", None, None, []),
    ]

    par_statut = compute_couverture_textes(gouvernements)["par_statut"]

    assert par_statut == {
        "couverte": 1, "partielle": 1, "hors_couverture": 1, "indeterminee": 1,
    }


def test_compute_couverture_textes_periode_absente_est_indeterminee():
    resultat = compute_couverture_textes([{"gouvernement_id": "gouvernement:X", "nom": "X"}])

    assert resultat["lignes"][0]["statut_couverture"] == "indeterminee"
    # Ni « à zéro » ni « hors couverture » : on n'affirme rien.
    assert resultat["sans_texte_dans_couverture"] == []
    assert resultat["sans_texte_hors_couverture"] == []


def test_compute_couverture_textes_trie_par_nom_puis_id():
    gouvernements = [
        gouvernement_periode("gouvernement:B", "2024-07-18", None, [], nom="Gouvernement B"),
        gouvernement_periode("gouvernement:A", "2024-07-18", None, [], nom="Gouvernement A"),
    ]

    lignes = compute_couverture_textes(gouvernements)["lignes"]

    assert [ligne["gouvernement_id"] for ligne in lignes] == ["gouvernement:A", "gouvernement:B"]


def test_compute_couverture_textes_est_serialisable_json():
    gouvernements = [gouvernement_periode("gouvernement:X", "2024-07-18", None, [])]

    json.dumps(compute_couverture_textes(gouvernements), ensure_ascii=False)


# ---------------------------------------------------------------------------
# compute_plage_dates_gouvernements
# ---------------------------------------------------------------------------

def membre(debut=None, fin=None, membre_id="m"):
    return {"membre_id": membre_id, "portefeuille": None, "debut": debut, "fin": fin}


def texte(date_depot=None, date_dernier_evenement=None, dossier_id="d"):
    return {
        "dossier_id": dossier_id, "date_depot": date_depot,
        "date_dernier_evenement": date_dernier_evenement,
    }


def test_compute_plage_dates_gouvernements_liste_vide():
    assert compute_plage_dates_gouvernements([]) == {"lignes": [], "dates_invalides": []}


def test_compute_plage_dates_gouvernements_mandat_en_cours_fin_null():
    gouvernements = [{
        "gouvernement_id": "gouvernement:X", "nom": "X",
        "membres": [membre(debut="2025-09-09", fin=None)],
        "textes": [],
    }]

    resultat = compute_plage_dates_gouvernements(gouvernements)

    ligne = resultat["lignes"][0]
    assert ligne["mandats_membres"] == {"min": "2025-09-09", "max": "2025-09-09"}
    # fin=null n'est jamais substitué par la date du jour, et n'est pas une date invalide.
    assert resultat["dates_invalides"] == []


def test_compute_plage_dates_gouvernements_mandat_termine_fin_incluse_dans_le_max():
    gouvernements = [{
        "gouvernement_id": "gouvernement:X", "nom": "X",
        "membres": [membre(debut="2024-01-01", fin="2024-06-01")],
        "textes": [],
    }]

    resultat = compute_plage_dates_gouvernements(gouvernements)

    assert resultat["lignes"][0]["mandats_membres"] == {"min": "2024-01-01", "max": "2024-06-01"}


def test_compute_plage_dates_gouvernements_gouvernement_sans_texte():
    gouvernements = [{
        "gouvernement_id": "gouvernement:X", "nom": "X",
        "membres": [membre(debut="2025-01-01", fin=None)],
        "textes": [],
    }]

    resultat = compute_plage_dates_gouvernements(gouvernements)

    assert resultat["lignes"][0]["textes"] is None


def test_compute_plage_dates_gouvernements_gouvernement_avec_plusieurs_textes():
    gouvernements = [{
        "gouvernement_id": "gouvernement:X", "nom": "X",
        "membres": [],
        "textes": [
            texte(date_depot="2024-10-10", date_dernier_evenement="2024-12-04", dossier_id="t1"),
            texte(date_depot="2024-11-01", date_dernier_evenement="2025-01-15", dossier_id="t2"),
        ],
    }]

    resultat = compute_plage_dates_gouvernements(gouvernements)

    assert resultat["lignes"][0]["textes"] == {"min": "2024-10-10", "max": "2025-01-15"}


def test_compute_plage_dates_gouvernements_membres_et_textes_absents():
    resultat = compute_plage_dates_gouvernements([{"gouvernement_id": "gouvernement:X", "nom": "X"}])

    ligne = resultat["lignes"][0]
    assert ligne["mandats_membres"] is None
    assert ligne["textes"] is None
    assert resultat["dates_invalides"] == []


def test_compute_plage_dates_gouvernements_dates_invalides_recensees():
    gouvernements = [{
        "gouvernement_id": "gouvernement:X", "nom": "X",
        "membres": [membre(debut="pas-une-date", fin="aussi-invalide")],
        "textes": [texte(date_depot=None, date_dernier_evenement="pas-une-date")],
    }]

    resultat = compute_plage_dates_gouvernements(gouvernements)

    assert resultat["lignes"][0]["mandats_membres"] is None
    assert resultat["lignes"][0]["textes"] is None
    champs = {e["champ"] for e in resultat["dates_invalides"]}
    assert champs == {
        "membres[0].debut", "membres[0].fin",
        "textes[0].date_depot", "textes[0].date_dernier_evenement",
    }


def test_compute_plage_dates_gouvernements_trie_par_nom_puis_id():
    gouvernements = [
        {"gouvernement_id": "gouvernement:Z", "nom": "B"},
        {"gouvernement_id": "gouvernement:A", "nom": "A"},
    ]

    resultat = compute_plage_dates_gouvernements(gouvernements)

    assert [ligne["gouvernement_id"] for ligne in resultat["lignes"]] == [
        "gouvernement:A", "gouvernement:Z",
    ]


def test_compute_plage_dates_gouvernements_est_serialisable_json():
    gouvernements_valides, _ = load_gouvernement_directory(FIXTURES_DIR)

    resultat = compute_plage_dates_gouvernements(gouvernements_valides)

    json.dumps(resultat, ensure_ascii=False)


# ---------------------------------------------------------------------------
# generate_markdown_report
# ---------------------------------------------------------------------------

def test_generate_markdown_report_contient_toutes_les_sections():
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "# Rapport d'audit du jeu de données gouvernements" in markdown
    assert "## Volumétrie" in markdown
    assert "## Couverture des textes portés" in markdown
    assert "## Tableau croisé des plages temporelles par gouvernement" in markdown
    assert "## Complétude" in markdown
    assert "## Cohérence" in markdown
    assert "## Fraîcheur" in markdown
    assert "## Warnings" in markdown
    assert "## Erreurs de lecture" in markdown


def test_generate_markdown_report_sections_vides_affichent_un_message_explicite():
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "Aucun gouvernement invalide détecté." in markdown
    assert "Aucune divergence détectée." in markdown
    assert "Aucun doublon détecté." in markdown
    assert "Aucune source datée." in markdown
    assert "Aucun gouvernement périmé." in markdown
    assert "Aucun warning." in markdown
    assert "Aucune erreur de lecture." in markdown
    assert "Aucune date invalide détectée." in markdown


def test_generate_markdown_report_en_tete_expose_la_borne_de_couverture():
    # Objectif de #399 : la borne doit être lisible sans lire le code.
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "2012-06-20" in markdown.split("## Volumétrie")[0]


def test_generate_markdown_report_distingue_hors_couverture_et_zero_constate():
    gouvernements = [
        gouvernement_periode(
            "gouvernement:FILLON_2", "2007-06-19", "2010-11-13", [], nom="Gouvernement Fillon II",
        ),
        gouvernement_periode(
            "gouvernement:X", "2024-07-18", None, [], nom="Gouvernement X",
        ),
    ]

    markdown = generate_markdown_report(build_report(gouvernements, [], reference_date=REFERENCE))
    section_couverture = markdown.split("## Couverture des textes portés")[1]
    sans_texte_couverts, sans_texte_hors = section_couverture.split(
        "### Sans texte, hors couverture"
    )

    # Le gouvernement couvert est le seul rangé parmi les zéros constatés…
    assert "gouvernement:X" in sans_texte_couverts.split("### Sans texte, dans la couverture")[1]
    # …et le gouvernement hors couverture parmi les absences de source.
    assert "gouvernement:FILLON_2" in sans_texte_hors
    assert "gouvernement:FILLON_2" not in sans_texte_couverts.split(
        "### Sans texte, dans la couverture"
    )[1]


def test_generate_markdown_report_plage_dates_qualifie_le_nd_hors_couverture():
    gouvernements = [
        gouvernement_periode(
            "gouvernement:FILLON_2", "2007-06-19", "2010-11-13", [], nom="Gouvernement Fillon II",
        ),
    ]

    markdown = generate_markdown_report(build_report(gouvernements, [], reference_date=REFERENCE))

    assert "N/D (hors couverture)" in markdown


def test_generate_markdown_report_reflete_les_donnees_du_rapport():
    gouvernements = [{"gouvernement_id": "a"}, {"gouvernement_id": "a"}]  # doublon volontaire
    erreurs = [{"fichier": "casse.json", "erreur": "JSON invalide"}]

    rapport = build_report(gouvernements, erreurs, reference_date=REFERENCE)
    markdown = generate_markdown_report(rapport)

    assert "casse.json" in markdown
    assert "JSON invalide" in markdown
    assert "| a | 2 |" in markdown  # doublons_gouvernement_id : "a" en double


def test_generate_markdown_report_plage_dates_mandat_en_cours():
    gouvernements = [{
        "gouvernement_id": "gouvernement:X", "nom": "Gouvernement X",
        "membres": [membre(debut="2025-09-09", fin=None)],
        "textes": [],
    }]

    rapport = build_report(gouvernements, [], reference_date=REFERENCE)
    markdown = generate_markdown_report(rapport)

    assert "2025-09-09 → 2025-09-09" in markdown
    assert "N/D" in markdown  # cellule "textes" du gouvernement sans texte


def test_generate_markdown_report_retourne_une_chaine_non_vide():
    gouvernements_valides, erreurs_lecture = load_gouvernement_directory(FIXTURES_DIR)
    rapport = build_report(gouvernements_valides, erreurs_lecture, reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert isinstance(markdown, str)
    assert len(markdown) > 0


# ---------------------------------------------------------------------------
# CLI : _build_arg_parser / main
# ---------------------------------------------------------------------------

def test_build_arg_parser_defauts():
    parser = _build_arg_parser()
    args = parser.parse_args([])

    assert args.input_dir == "pivot_data/gouvernements"
    assert args.staleness_days == 30
    assert args.output_json is None
    assert args.output_md is None


def test_main_ecrit_json_et_markdown(tmp_path):
    output_json = tmp_path / "rapport.json"
    output_md = tmp_path / "rapport.md"

    code = main([
        "--input-dir", str(FIXTURES_DIR),
        "--output-json", str(output_json),
        "--output-md", str(output_md),
        "--staleness-days", "30",
    ])

    assert code == 0
    assert output_json.exists()
    assert output_md.exists()

    rapport = json.loads(output_json.read_text(encoding="utf-8"))
    assert rapport["meta"]["total_gouvernements"] == 3
    assert rapport["meta"]["total_erreurs_lecture"] == 1
    assert rapport["meta"]["staleness_days"] == 30

    markdown = output_md.read_text(encoding="utf-8")
    assert "# Rapport d'audit du jeu de données gouvernements" in markdown


def test_main_sans_output_json_ecrit_sur_stdout(capsys):
    code = main(["--input-dir", str(FIXTURES_DIR)])

    assert code == 0
    captured = capsys.readouterr()
    rapport = json.loads(captured.out)
    assert rapport["meta"]["total_gouvernements"] == 3


def test_main_dossier_introuvable_retourne_1(tmp_path):
    code = main(["--input-dir", str(tmp_path / "n-existe-pas")])

    assert code == 1


def test_main_out_dir_est_cree_si_absent(tmp_path):
    output_json = tmp_path / "sous" / "dossier" / "rapport.json"

    code = main(["--input-dir", str(FIXTURES_DIR), "--output-json", str(output_json)])

    assert code == 0
    assert output_json.exists()


def test_main_output_dir_ecrit_json_et_markdown_horodates(tmp_path):
    code = main(["--input-dir", str(FIXTURES_DIR), "--output-dir", str(tmp_path)])

    assert code == 0
    json_files = list(tmp_path.glob("audit_gouvernement_*.json"))
    md_files = list(tmp_path.glob("audit_gouvernement_*.md"))
    assert len(json_files) == 1
    assert len(md_files) == 1


def test_main_output_dir_incompatible_avec_output_json(tmp_path):
    code = main([
        "--input-dir", str(FIXTURES_DIR),
        "--output-dir", str(tmp_path),
        "--output-json", str(tmp_path / "rapport.json"),
    ])

    assert code == 1
    assert list(tmp_path.glob("*.json")) == []
