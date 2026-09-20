import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_pivot_dataset import (
    _build_arg_parser,
    BLOCS_LUS_AUDIT,
    ListeReduite,
    build_report,
    compute_agregation_warnings,
    compute_fraicheur_sources,
    compute_profils_perimes,
    compute_coherence_chambre_sources,
    compute_coherence_schema_version,
    compute_doublons_id,
    compute_plage_dates_candidats,
    compute_presence_meta,
    compute_profils_sans_activite,
    compute_repartition_chambre,
    compute_repartition_provenance,
    compute_tableau_croise_candidats,
    compute_validite_dates,
    compute_taux_remplissage,
    generate_markdown_report,
    load_pivot_directory,
    main,
)


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "audit_pivot"


@pytest.fixture(autouse=True)
def index_partages_isoles(monkeypatch, tmp_path_factory):
    """Coupe les index partagés du corpus vivant pour tout ce fichier (#473).

    `--scrutins` et `--amendements` ont pour **valeur par défaut** les chemins du
    dépôt (`pivot_data/scrutins.json`, `pivot_data/amendements/`). Quatre tests
    de `main()` surchargeaient `--input-dir` vers les fixtures mais pas ces
    deux-là : ils lisaient donc ~66 Mo du corpus vivant, sans qu'aucune de leurs
    assertions n'en dépende. C'est le pendant en lecture du piège d'écriture déjà
    rencontré ici — une option argparse dont le défaut pointe dans le dépôt.

    Le parser est construit à chaque appel de `main()` : réécrire les deux
    globales suffit, et couvre les tests à venir sans qu'ils aient à y penser.
    Un test qui veut vraiment un index le passe explicitement, la surcharge
    n'étant qu'un défaut.
    """
    absent = tmp_path_factory.mktemp("index-partages-absents")
    monkeypatch.setattr("audit_pivot_dataset.DEFAULT_SCRUTINS_PATH", absent / "scrutins.json")
    monkeypatch.setattr("audit_pivot_dataset.DEFAULT_AMENDEMENTS_DIR", absent / "amendements")


# ---------------------------------------------------------------------------
# load_pivot_directory : chargement des fixtures du dépôt
# ---------------------------------------------------------------------------

def test_load_pivot_directory_charge_les_profils_valides():
    profils_valides, erreurs_lecture = load_pivot_directory(FIXTURES_DIR)

    ids = {p["id"] for p in profils_valides}
    assert ids == {
        "nosdeputes:jean-dupont",
        "nosdeputes:marie-martin",
        "nossenateurs:paul-durand",
    }


def test_load_pivot_directory_scanne_recursivement():
    profils_valides, _ = load_pivot_directory(FIXTURES_DIR)

    # profil-3.pivot.json est dans un sous-dossier : doit être trouvé malgré tout.
    assert any(p["id"] == "nossenateurs:paul-durand" for p in profils_valides)


def test_load_pivot_directory_ne_s_interrompt_pas_sur_fichier_invalide():
    profils_valides, erreurs_lecture = load_pivot_directory(FIXTURES_DIR)

    # Le fichier invalide ne doit pas empêcher le chargement des autres profils.
    assert len(profils_valides) == 3
    assert len(erreurs_lecture) == 1


def test_load_pivot_directory_contenu_erreurs_lecture():
    _, erreurs_lecture = load_pivot_directory(FIXTURES_DIR)

    assert len(erreurs_lecture) == 1
    erreur = erreurs_lecture[0]
    assert set(erreur.keys()) == {"fichier", "erreur"}
    assert erreur["fichier"].endswith("invalide.pivot.json")
    assert isinstance(erreur["erreur"], str)
    assert erreur["erreur"]  # message non vide


# ---------------------------------------------------------------------------
# load_pivot_directory : cas limites construits en mémoire (tmp_path)
# ---------------------------------------------------------------------------

def test_load_pivot_directory_repertoire_vide(tmp_path):
    profils_valides, erreurs_lecture = load_pivot_directory(tmp_path)

    assert profils_valides == []
    assert erreurs_lecture == []


def test_load_pivot_directory_ignore_fichiers_non_pivot(tmp_path):
    (tmp_path / "notes.txt").write_text("pas un pivot", encoding="utf-8")
    (tmp_path / "autre.json").write_text('{"id": "x"}', encoding="utf-8")

    profils_valides, erreurs_lecture = load_pivot_directory(tmp_path)

    assert profils_valides == []
    assert erreurs_lecture == []


def test_load_pivot_directory_objet_racine_non_dict(tmp_path):
    (tmp_path / "liste.pivot.json").write_text("[1, 2, 3]", encoding="utf-8")

    profils_valides, erreurs_lecture = load_pivot_directory(tmp_path)

    assert profils_valides == []
    assert len(erreurs_lecture) == 1
    assert erreurs_lecture[0]["fichier"].endswith("liste.pivot.json")


def test_load_pivot_directory_est_pure(tmp_path):
    fichier = tmp_path / "profil.pivot.json"
    contenu = {"schema_version": "1", "id": "nosdeputes:test", "nom": "Test"}
    fichier.write_text(json.dumps(contenu), encoding="utf-8")

    load_pivot_directory(tmp_path)

    # Le fichier source ne doit pas être modifié par le chargement.
    assert json.loads(fichier.read_text(encoding="utf-8")) == contenu


# ---------------------------------------------------------------------------
# Fixtures minimalistes en mémoire pour les indicateurs de volumétrie.
# ---------------------------------------------------------------------------

def profil(chambre=None, nb_votes=0, nb_textes=0, nb_amendements=0,
           nb_interventions=0, nb_sources=0):
    return {
        "id": "source:x",
        "chambre": chambre,
        "sources": [{"type": "nosdeputes", "url": "u", "synchro_le": "t"}] * nb_sources,
        "votes": [{"id": i} for i in range(nb_votes)],
        "textes_portes": [{"id": i} for i in range(nb_textes)],
        "amendements": [{"id": i} for i in range(nb_amendements)],
        "interventions": [{"id": i} for i in range(nb_interventions)],
    }


# ---------------------------------------------------------------------------
# compute_repartition_chambre
# ---------------------------------------------------------------------------

def test_compute_repartition_chambre_liste_vide():
    resultat = compute_repartition_chambre([])

    assert resultat["total_profils"] == 0
    assert resultat["par_chambre"] == {
        "AN": 0, "PE": 0, "Senat": 0, "mairie": 0, "null": 0,
    }


def test_compute_repartition_chambre_repartit_par_chambre_connue():
    profils = [
        profil(chambre="AN"),
        profil(chambre="AN"),
        profil(chambre="Senat"),
        profil(chambre="PE"),
        profil(chambre="mairie"),
    ]

    resultat = compute_repartition_chambre(profils)

    assert resultat["total_profils"] == 5
    assert resultat["par_chambre"] == {
        "AN": 2, "Senat": 1, "PE": 1, "mairie": 1, "null": 0,
    }


def test_compute_repartition_chambre_valeur_null_ou_inconnue():
    profils = [
        profil(chambre=None),
        profil(chambre="valeur_inconnue"),
        profil(chambre="AN"),
    ]

    resultat = compute_repartition_chambre(profils)

    assert resultat["total_profils"] == 3
    assert resultat["par_chambre"]["null"] == 2
    assert resultat["par_chambre"]["AN"] == 1


def test_compute_repartition_chambre_chambre_absente_du_profil():
    resultat = compute_repartition_chambre([{"id": "source:x"}])

    assert resultat["total_profils"] == 1
    assert resultat["par_chambre"]["null"] == 1


# ---------------------------------------------------------------------------
# compute_repartition_provenance
# ---------------------------------------------------------------------------

def profil_provenance(provenance, id_="source:x"):
    return {"id": id_, "meta": {"provenance": provenance}}


def test_compute_repartition_provenance_liste_vide():
    resultat = compute_repartition_provenance([])

    assert resultat == {
        "total_profils": 0,
        "par_provenance": {"candidat_declare": 0, "roster_groupe": 0,
                           "roster_gouvernement": 0, "null": 0},
    }


def test_compute_repartition_provenance_profils_mixtes():
    profils = [
        profil_provenance("candidat_declare", id_="a"),
        profil_provenance("roster_groupe", id_="b"),
        profil_provenance("roster_groupe", id_="c"),
    ]

    resultat = compute_repartition_provenance(profils)

    assert resultat == {
        "total_profils": 3,
        "par_provenance": {"candidat_declare": 1, "roster_groupe": 2,
                           "roster_gouvernement": 0, "null": 0},
    }


def test_compute_repartition_provenance_meta_absente_compte_candidat_declare():
    # Pivot généré avant #189 (rétro-compatibilité, voir validate_profil()).
    resultat = compute_repartition_provenance([{"id": "a"}])

    assert resultat["par_provenance"]["candidat_declare"] == 1
    assert resultat["par_provenance"]["roster_groupe"] == 0
    assert resultat["par_provenance"]["null"] == 0


def test_compute_repartition_provenance_meta_provenance_absente_compte_candidat_declare():
    resultat = compute_repartition_provenance([{"id": "a", "meta": {}}])

    assert resultat["par_provenance"]["candidat_declare"] == 1


def test_compute_repartition_provenance_valeur_inconnue_compte_null():
    resultat = compute_repartition_provenance([profil_provenance("valeur_inconnue")])

    assert resultat["par_provenance"]["null"] == 1
    assert resultat["par_provenance"]["candidat_declare"] == 0


def test_compute_repartition_provenance_meta_invalide_compte_candidat_declare():
    resultat = compute_repartition_provenance([{"id": "a", "meta": "pas un dict"}])

    assert resultat["par_provenance"]["candidat_declare"] == 1


# ---------------------------------------------------------------------------
# Fixtures pour compute_fraicheur_sources / compute_profils_perimes.
# ---------------------------------------------------------------------------

REFERENCE = datetime(2026, 8, 9, tzinfo=timezone.utc)


def source(type_source, jours_anciennete):
    synchro = REFERENCE - timedelta(days=jours_anciennete)
    return {"type": type_source, "url": "u", "synchro_le": synchro.isoformat()}


def profil_sources(id_, *sources):
    return {"id": id_, "sources": list(sources)}


# ---------------------------------------------------------------------------
# compute_fraicheur_sources
# ---------------------------------------------------------------------------

def test_compute_fraicheur_sources_liste_vide():
    resultat = compute_fraicheur_sources([], reference_date=REFERENCE)

    assert resultat == {"total_sources_datees": 0, "par_type_source": {}}


def test_compute_fraicheur_sources_min_max_mediane_moyenne():
    profils = [
        profil_sources("a", source("nosdeputes", 0)),
        profil_sources("b", source("nosdeputes", 10)),
        profil_sources("c", source("nosdeputes", 20)),
    ]

    resultat = compute_fraicheur_sources(profils, reference_date=REFERENCE)
    stats = resultat["par_type_source"]["nosdeputes"]

    assert resultat["total_sources_datees"] == 3
    assert stats["nombre_sources"] == 3
    assert stats["min_jours"] == 0
    assert stats["max_jours"] == 20
    assert stats["mediane_jours"] == 10
    assert stats["moyenne_jours"] == 10.0


def test_compute_fraicheur_sources_regroupe_par_type():
    profils = [profil_sources("a", source("nosdeputes", 5), source("parltrack", 50))]

    resultat = compute_fraicheur_sources(profils, reference_date=REFERENCE)

    assert set(resultat["par_type_source"]) == {"nosdeputes", "parltrack"}
    assert resultat["par_type_source"]["nosdeputes"]["min_jours"] == 5
    assert resultat["par_type_source"]["parltrack"]["min_jours"] == 50


def test_compute_fraicheur_sources_type_absent_regroupe_sous_null():
    profils = [profil_sources("a", {"url": "u", "synchro_le": REFERENCE.isoformat()})]

    resultat = compute_fraicheur_sources(profils, reference_date=REFERENCE)

    assert resultat["par_type_source"]["null"]["nombre_sources"] == 1


def test_compute_fraicheur_sources_ignore_synchro_le_invalide_ou_absente():
    profils = [
        profil_sources("a", {"type": "nosdeputes", "url": "u", "synchro_le": "pas-une-date"}),
        profil_sources("b", {"type": "nosdeputes", "url": "u"}),
        profil_sources("c", source("nosdeputes", 1)),
    ]

    resultat = compute_fraicheur_sources(profils, reference_date=REFERENCE)

    assert resultat["total_sources_datees"] == 1
    assert resultat["par_type_source"]["nosdeputes"]["nombre_sources"] == 1


def test_compute_fraicheur_sources_ignore_profils_sans_sources():
    resultat = compute_fraicheur_sources(
        [profil_sources("a"), {"id": "b"}], reference_date=REFERENCE
    )

    assert resultat == {"total_sources_datees": 0, "par_type_source": {}}


def test_compute_fraicheur_sources_sans_reference_date_utilise_maintenant():
    hier = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    profils = [profil_sources("a", {"type": "nosdeputes", "url": "u", "synchro_le": hier})]

    resultat = compute_fraicheur_sources(profils)

    assert resultat["par_type_source"]["nosdeputes"]["min_jours"] == 1


# ---------------------------------------------------------------------------
# compute_profils_perimes
# ---------------------------------------------------------------------------

def test_compute_profils_perimes_toutes_sources_perimees():
    profils = [profil_sources("a", source("nosdeputes", 100))]

    resultat = compute_profils_perimes(profils, staleness_days=30, reference_date=REFERENCE)

    assert resultat == ["a"]


def test_compute_profils_perimes_une_source_fraiche_suffit_a_exclure():
    profils = [profil_sources("a", source("nosdeputes", 100), source("parltrack", 5))]

    resultat = compute_profils_perimes(profils, staleness_days=30, reference_date=REFERENCE)

    assert resultat == []


def test_compute_profils_perimes_seuil_variable():
    profils = [profil_sources("a", source("nosdeputes", 15))]

    assert compute_profils_perimes(profils, staleness_days=10, reference_date=REFERENCE) == ["a"]
    assert compute_profils_perimes(profils, staleness_days=20, reference_date=REFERENCE) == []


def test_compute_profils_perimes_exactement_au_seuil_n_est_pas_perime():
    profils = [profil_sources("a", source("nosdeputes", 30))]

    resultat = compute_profils_perimes(profils, staleness_days=30, reference_date=REFERENCE)

    assert resultat == []


def test_compute_profils_perimes_aucune_source_n_est_jamais_perime():
    profils = [profil_sources("a"), {"id": "b"}]

    resultat = compute_profils_perimes(profils, staleness_days=0, reference_date=REFERENCE)

    assert resultat == []


def test_compute_profils_perimes_resultat_trie_par_id():
    profils = [
        profil_sources("z", source("nosdeputes", 100)),
        profil_sources("a", source("nosdeputes", 100)),
    ]

    resultat = compute_profils_perimes(profils, staleness_days=10, reference_date=REFERENCE)

    assert resultat == ["a", "z"]


# ---------------------------------------------------------------------------
# compute_agregation_warnings
# ---------------------------------------------------------------------------

def profil_warnings(id_, *warnings):
    return {"id": id_, "meta": {"warnings": list(warnings)}}


def test_compute_agregation_warnings_aucun_profil():
    assert compute_agregation_warnings([]) == {"total_warnings": 0, "par_type": {}}


def test_compute_agregation_warnings_profils_sans_warnings():
    profils = [profil_warnings("a"), {"id": "b"}, {"id": "c", "meta": {}}]

    resultat = compute_agregation_warnings(profils)

    assert resultat == {"total_warnings": 0, "par_type": {}}


def test_compute_agregation_warnings_type_par_prefixe_avant_les_deux_points():
    profils = [
        profil_warnings("a", "identité introuvable : l'API ne renvoie pas de profil exploitable."),
        profil_warnings("b", "identité introuvable : réponse API vide."),
    ]

    resultat = compute_agregation_warnings(profils)

    assert resultat["total_warnings"] == 2
    assert resultat["par_type"]["identité introuvable"] == {"frequence": 2, "ids": ["a", "b"]}


def test_compute_agregation_warnings_message_sans_deux_points_utilise_le_message_entier():
    profils = [profil_warnings("a", "MEP marqué inactif dans le dump Parltrack.")]

    resultat = compute_agregation_warnings(profils)

    assert resultat["par_type"] == {
        "MEP marqué inactif dans le dump Parltrack.": {"frequence": 1, "ids": ["a"]},
    }


def test_compute_agregation_warnings_plusieurs_types_et_frequences():
    profils = [
        profil_warnings("a", "votes introuvables : x", "amendements indisponibles : y"),
        profil_warnings("b", "votes introuvables : z"),
    ]

    resultat = compute_agregation_warnings(profils)

    assert resultat["total_warnings"] == 3
    assert resultat["par_type"]["votes introuvables"] == {"frequence": 2, "ids": ["a", "b"]}
    assert resultat["par_type"]["amendements indisponibles"] == {"frequence": 1, "ids": ["a"]}


def test_compute_agregation_warnings_meme_type_deux_fois_meme_profil_ids_dedupliques():
    profils = [profil_warnings("a", "votes introuvables : x", "votes introuvables : y")]

    resultat = compute_agregation_warnings(profils)

    assert resultat["par_type"]["votes introuvables"] == {"frequence": 2, "ids": ["a"]}
# compute_doublons_id
# ---------------------------------------------------------------------------

def test_compute_doublons_id_liste_vide():
    assert compute_doublons_id([]) == {"doublons": []}


def test_compute_doublons_id_sans_doublon():
    profils = [{"id": "nosdeputes:a"}, {"id": "nosdeputes:b"}]

    assert compute_doublons_id(profils) == {"doublons": []}


def test_compute_doublons_id_detecte_les_doublons():
    profils = [
        {"id": "nosdeputes:a"},
        {"id": "nosdeputes:a"},
        {"id": "nosdeputes:b"},
        {"id": "nosdeputes:a"},
        {"id": "nosdeputes:c"},
        {"id": "nosdeputes:c"},
    ]

    resultat = compute_doublons_id(profils)

    assert resultat == {
        "doublons": [
            {"id": "nosdeputes:a", "occurrences": 3},
            {"id": "nosdeputes:c", "occurrences": 2},
        ]
    }


def test_compute_doublons_id_ignore_id_absent_ou_vide():
    profils = [{"id": ""}, {"id": ""}, {}, {}]

    assert compute_doublons_id(profils) == {"doublons": []}


# ---------------------------------------------------------------------------
# compute_coherence_schema_version
# ---------------------------------------------------------------------------

def test_compute_coherence_schema_version_liste_vide():
    assert compute_coherence_schema_version([]) == {"profils_incoherents": []}


def test_compute_coherence_schema_version_coherente():
    profils = [{"id": "a", "schema_version": "1", "meta": {"schema_version": "1"}}]

    assert compute_coherence_schema_version(profils) == {"profils_incoherents": []}


def test_compute_coherence_schema_version_divergente():
    profils = [{"id": "a", "schema_version": "1", "meta": {"schema_version": "2"}}]

    resultat = compute_coherence_schema_version(profils)

    assert resultat == {
        "profils_incoherents": [
            {"id": "a", "schema_version": "1", "meta_schema_version": "2"}
        ]
    }


def test_compute_coherence_schema_version_meta_absente_ou_invalide():
    profils = [
        {"id": "a", "schema_version": "1"},                # meta absente
        {"id": "b", "schema_version": "1", "meta": "pas un dict"},
    ]

    resultat = compute_coherence_schema_version(profils)

    assert {p["id"] for p in resultat["profils_incoherents"]} == {"a", "b"}
    assert all(p["meta_schema_version"] is None for p in resultat["profils_incoherents"])


# ---------------------------------------------------------------------------
# compute_validite_dates
# ---------------------------------------------------------------------------

def profil_dates(genere_le="2024-01-01T00:00:00+00:00", sources=None, id_="a"):
    return {
        "id": id_,
        "meta": {"genere_le": genere_le},
        "sources": sources if sources is not None else [],
    }


def test_compute_validite_dates_liste_vide():
    assert compute_validite_dates([]) == {"dates_invalides": []}


def test_compute_validite_dates_dates_valides():
    profils = [
        profil_dates(
            genere_le="2024-01-01T00:00:00+00:00",
            sources=[{"type": "nosdeputes", "synchro_le": "2024-06-01T12:00:00Z"}],
        )
    ]

    assert compute_validite_dates(profils) == {"dates_invalides": []}


def test_compute_validite_dates_format_invalide():
    profils = [profil_dates(genere_le="pas une date")]

    resultat = compute_validite_dates(profils)

    assert resultat == {
        "dates_invalides": [
            {"id": "a", "champ": "meta.genere_le", "valeur": "pas une date", "erreur": "format_invalide"}
        ]
    }


def test_compute_validite_dates_genere_le_absent():
    """#726 — une valeur ABSENTE n'est pas une valeur FAUTIVE. La distinction
    existe parce que 464 des 1 115 entrées `sources[]` publiées n'ont plus de
    date depuis #529 et n'en auront jamais : les ranger sous « format invalide »
    confondait une donnée manquante avec une donnée erronée (§2 règle 5)."""
    profils = [{"id": "a", "meta": {}, "sources": []}]

    resultat = compute_validite_dates(profils)

    assert resultat["dates_invalides"] == [
        {"id": "a", "champ": "meta.genere_le", "valeur": None, "erreur": "non_renseigne"}
    ]


def test_compute_validite_dates_source_retiree_est_non_renseignee_pas_invalide():
    """Le cas réel : une entrée `nosdeputes` conservée pour la clause ODbL
    (`AGENTS.md` §7), que plus aucune collecte ne date."""
    profils = [{
        "id": "a",
        "meta": {"genere_le": "2026-09-01T00:00:00+00:00"},
        "sources": [
            {"type": "nosdeputes", "url": "https://www.nosdeputes.fr/a", "synchro_le": None},
            {"type": "assemblee_nationale", "url": "https://x", "synchro_le": "2026-09-01"},
        ],
    }]

    resultat = compute_validite_dates(profils)

    assert resultat["dates_invalides"] == [
        {"id": "a", "champ": "sources[0].synchro_le", "valeur": None, "erreur": "non_renseigne"}
    ]


def test_compute_validite_dates_une_valeur_non_chaine_reste_invalide():
    """Une absence est un trou ; un entier dans un champ de date est une faute."""
    profils = [{"id": "a", "meta": {"genere_le": 20260901}, "sources": []}]

    resultat = compute_validite_dates(profils)

    assert resultat["dates_invalides"][0]["erreur"] == "format_invalide"


def test_compute_validite_dates_date_future():
    profils = [profil_dates(genere_le="2999-01-01T00:00:00+00:00")]

    resultat = compute_validite_dates(profils)

    assert resultat == {
        "dates_invalides": [
            {
                "id": "a", "champ": "meta.genere_le",
                "valeur": "2999-01-01T00:00:00+00:00", "erreur": "date_future",
            }
        ]
    }


def test_compute_validite_dates_source_invalide_indexee():
    profils = [
        profil_dates(sources=[
            {"type": "nosdeputes", "synchro_le": "2024-01-01T00:00:00+00:00"},
            {"type": "wikidata", "synchro_le": "2999-01-01T00:00:00+00:00"},
        ])
    ]

    resultat = compute_validite_dates(profils)

    assert resultat == {
        "dates_invalides": [
            {
                "id": "a", "champ": "sources[1].synchro_le",
                "valeur": "2999-01-01T00:00:00+00:00", "erreur": "date_future",
            }
        ]
    }


# ---------------------------------------------------------------------------
# compute_coherence_chambre_sources
# ---------------------------------------------------------------------------

def profil_chambre(chambre, types_sources, id_="a"):
    return {
        "id": id_,
        "chambre": chambre,
        "sources": [{"type": t} for t in types_sources],
    }


def test_compute_coherence_chambre_sources_liste_vide():
    assert compute_coherence_chambre_sources([]) == {"profils_incoherents": []}


def test_compute_coherence_chambre_sources_an_coherente():
    profils = [
        profil_chambre("AN", ["nosdeputes"]),
        profil_chambre("AN", ["assemblee_nationale"]),
    ]

    assert compute_coherence_chambre_sources(profils) == {"profils_incoherents": []}


def test_compute_coherence_chambre_sources_an_incoherente():
    profils = [profil_chambre("AN", ["wikidata"])]

    resultat = compute_coherence_chambre_sources(profils)

    assert resultat == {
        "profils_incoherents": [
            {
                "id": "a",
                "chambres": ["AN"],
                "chambres_sans_source": ["AN"],
                "types_sources": ["wikidata"],
            }
        ]
    }


def test_compute_coherence_chambre_sources_senat():
    profils = [
        profil_chambre("Senat", ["nossenateurs"], id_="ok"),
        profil_chambre("Senat", ["nosdeputes"], id_="ko"),
    ]

    resultat = compute_coherence_chambre_sources(profils)

    assert [p["id"] for p in resultat["profils_incoherents"]] == ["ko"]


def test_compute_coherence_chambre_sources_pe():
    profils = [
        profil_chambre("PE", ["parltrack"], id_="ok1"),
        profil_chambre("PE", ["europarl"], id_="ok2"),
        profil_chambre("PE", ["nosdeputes"], id_="ko"),
    ]

    resultat = compute_coherence_chambre_sources(profils)

    assert [p["id"] for p in resultat["profils_incoherents"]] == ["ko"]


def test_compute_coherence_chambre_sources_mairie_jamais_signalee():
    profils = [profil_chambre("mairie", [])]

    assert compute_coherence_chambre_sources(profils) == {"profils_incoherents": []}


def test_compute_coherence_chambre_sources_chambre_absente_ou_inconnue():
    profils = [
        {"id": "a", "chambre": None, "sources": []},
        {"id": "b", "chambre": "inconnue", "sources": []},
    ]

    assert compute_coherence_chambre_sources(profils) == {"profils_incoherents": []}


def test_compute_coherence_chambre_sources_sources_absentes():
    profils = [{"id": "a", "chambre": "AN"}]

    resultat = compute_coherence_chambre_sources(profils)

    assert resultat == {
        "profils_incoherents": [
            {
                "id": "a",
                "chambres": ["AN"],
                "chambres_sans_source": ["AN"],
                "types_sources": [],
            }
        ]
    }


def test_compute_coherence_chambre_sources_bicameral_controle_chaque_chambre():
    """#494 — un profil AN + PE est contrôlé sur **les deux**, pas sur une seule.

    Le scalaire n'en portait qu'une : ce profil-ci, publié `chambre: "AN"` et
    déclarant une source `nosdeputes`, passait le contrôle alors que rien
    n'étaye son mandat européen. C'est un contrôle élargi, pas déplacé.
    """
    profils = [{
        "id": "bicameral",
        "chambres": ["AN", "PE"],
        "chambre": "AN",
        "sources": [{"type": "nosdeputes"}],
    }]

    resultat = compute_coherence_chambre_sources(profils)

    assert resultat == {
        "profils_incoherents": [
            {
                "id": "bicameral",
                "chambres": ["AN", "PE"],
                "chambres_sans_source": ["PE"],
                "types_sources": ["nosdeputes"],
            }
        ]
    }


def test_compute_coherence_chambre_sources_bicameral_les_deux_etayees():
    profils = [{
        "id": "bicameral",
        "chambres": ["AN", "PE"],
        "chambre": "AN",
        "sources": [{"type": "nosdeputes"}, {"type": "europarl"}],
    }]

    assert compute_coherence_chambre_sources(profils) == {"profils_incoherents": []}


# compute_taux_remplissage
# ---------------------------------------------------------------------------

def test_compute_taux_remplissage_liste_vide():
    resultat = compute_taux_remplissage([])

    for champ in ("parti", "groupe", "tags_thematiques", "mandats"):
        assert resultat[champ] == {"renseignes": 0, "total": 0, "taux_pct": 0.0}


def test_compute_taux_remplissage_champ_absent_du_profil():
    resultat = compute_taux_remplissage([{"id": "a"}])

    assert resultat["parti"] == {"renseignes": 0, "total": 1, "taux_pct": 0.0}
    assert resultat["mandats"] == {"renseignes": 0, "total": 1, "taux_pct": 0.0}


def test_compute_taux_remplissage_distingue_null_vide_et_renseigne():
    profils = [
        {"id": "a", "parti": None, "groupe": "", "tags_thematiques": [], "mandats": []},
        {"id": "b", "parti": "PS", "groupe": "LFI", "tags_thematiques": ["budget"],
         "mandats": [{"type": "depute"}]},
    ]

    resultat = compute_taux_remplissage(profils)

    # null (a.parti) et chaîne/liste vide (a.groupe, a.tags, a.mandats) comptent
    # tous les deux comme "non renseigné" : seul le profil "b" est renseigné.
    assert resultat["parti"] == {"renseignes": 1, "total": 2, "taux_pct": 50.0}
    assert resultat["groupe"] == {"renseignes": 1, "total": 2, "taux_pct": 50.0}
    assert resultat["tags_thematiques"] == {"renseignes": 1, "total": 2, "taux_pct": 50.0}
    assert resultat["mandats"] == {"renseignes": 1, "total": 2, "taux_pct": 50.0}


def test_compute_taux_remplissage_tous_champs_renseignes():
    profils = [
        {"id": "a", "parti": "PS", "groupe": "LFI", "tags_thematiques": ["budget"],
         "mandats": [{"type": "depute"}]},
    ]

    resultat = compute_taux_remplissage(profils)

    for champ in ("parti", "groupe", "tags_thematiques", "mandats"):
        assert resultat[champ]["taux_pct"] == 100.0


# ---------------------------------------------------------------------------
# compute_profils_sans_activite
# ---------------------------------------------------------------------------

def test_compute_profils_sans_activite_liste_vide():
    resultat = compute_profils_sans_activite([])

    # #630 — le relevé porte désormais la ventilation par provenance : « 24 sur
    # 481 » ne dit pas si le trou est sur les 13 fiches publiées ou sur les 468
    # membres de roster. Sur une population vide, tous les postes sont à 0 — un
    # compte absent n'est jamais omis, il vaut 0 parce qu'il a été mesuré.
    vide = {
        "total": 0, "candidat_declare": 0, "roster_groupe": 0,
        "roster_gouvernement": 0, "provenance_autre": 0, "illisibles": 0,
    }
    assert resultat == {
        "total_profils": 0, "nb_profils_sans_activite": 0, "profils_sans_activite": [],
        "ventilation_provenance": vide, "ventilation_provenance_total": vide,
    }


def test_compute_profils_sans_activite_detecte_les_profils_totalement_vides():
    profils = [
        {"id": "sans-activite-1"},
        {"id": "sans-activite-2", "votes": None, "amendements": [], "interventions": None},
        {"id": "avec-votes", "votes": [{"id": 1}], "amendements": [], "interventions": []},
    ]

    resultat = compute_profils_sans_activite(profils)

    assert resultat["total_profils"] == 3
    assert resultat["nb_profils_sans_activite"] == 2
    assert set(resultat["profils_sans_activite"]) == {"sans-activite-1", "sans-activite-2"}


def test_compute_profils_sans_activite_un_seul_champ_actif_suffit():
    profils = [
        {"id": "a", "votes": [], "amendements": [{"id": 1}], "interventions": []},
    ]

    resultat = compute_profils_sans_activite(profils)

    assert resultat["nb_profils_sans_activite"] == 0
    assert resultat["profils_sans_activite"] == []


# ---------------------------------------------------------------------------
# compute_tableau_croise_candidats
# ---------------------------------------------------------------------------

def test_compute_tableau_croise_candidats_liste_vide():
    resultat = compute_tableau_croise_candidats([])

    assert resultat == {
        "lignes": [],
        "non_candidats": {
            "total_profils": 0,
            "par_groupe": [],
            "ensemble": {
                champ: {"min": None, "max": None, "mediane": None, "moyenne": None}
                for champ in ("votes", "textes_portes", "amendements", "interventions")
            },
        },
    }


def test_compute_tableau_croise_candidats_candidat_toutes_categories_renseignees():
    profils = [
        {
            "id": "nosdeputes:a",
            "nom": "Alice",
            "chambre": "AN",
            "votes": [{"id": 1}, {"id": 2}],
            "textes_portes": [{"id": 1}],
            "amendements": [{"id": 1}, {"id": 2}, {"id": 3}],
            "interventions": [{"id": 1}],
        },
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert resultat["lignes"] == [
        {
            "id": "nosdeputes:a", "nom": "Alice", "chambres": ["AN"],
            "votes": 2, "textes_portes": 1, "amendements": 3, "interventions": 1,
        },
    ]


def test_compute_tableau_croise_candidats_ligne_porte_les_deux_chambres():
    """#494 — la ligne montre la carrière entière, pas la chambre qui l'emporte."""
    profils = [
        {
            "id": "bicameral",
            "nom": "Alice",
            "chambres": ["AN", "Senat"],
            "chambre": "AN",
        },
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert resultat["lignes"][0]["chambres"] == ["AN", "Senat"]


def test_compute_tableau_croise_candidats_categories_vides_ou_absentes():
    profils = [
        {"id": "nosdeputes:b", "nom": "Bob", "chambre": "AN", "votes": [], "textes_portes": None},
        {"id": "nosdeputes:c", "nom": "Chloé", "chambre": "Senat"},
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert resultat["lignes"] == [
        {
            "id": "nosdeputes:b", "nom": "Bob", "chambres": ["AN"],
            "votes": 0, "textes_portes": 0, "amendements": 0, "interventions": 0,
        },
        {
            "id": "nosdeputes:c", "nom": "Chloé", "chambres": ["Senat"],
            "votes": 0, "textes_portes": 0, "amendements": 0, "interventions": 0,
        },
    ]


def test_compute_tableau_croise_candidats_trie_par_nom():
    profils = [
        {"id": "x:z", "nom": "Zoé", "chambre": "AN"},
        {"id": "x:a", "nom": "Alban", "chambre": "AN"},
        {"id": "x:m", "nom": "Marc", "chambre": "AN"},
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert [ligne["nom"] for ligne in resultat["lignes"]] == ["Alban", "Marc", "Zoé"]


def test_compute_tableau_croise_candidats_nom_absent_tri_deterministe_par_id():
    profils = [
        {"id": "x:b", "nom": None, "chambre": "AN"},
        {"id": "x:a", "nom": None, "chambre": "AN"},
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert [ligne["id"] for ligne in resultat["lignes"]] == ["x:a", "x:b"]


def roster(id_, nom, groupe, **listes):
    """Profil issu du roster d'un groupe (donc non candidat)."""
    return {
        "id": id_, "nom": nom, "chambre": "AN", "groupe": groupe,
        "meta": {"provenance": "roster_groupe"},
        **listes,
    }


def test_compute_tableau_croise_candidats_exclut_les_profils_roster_du_detail():
    profils = [
        {"id": "x:a", "nom": "Alice", "chambre": "AN", "votes": [{"id": 1}]},
        roster("x:r", "Robert", "GDR", votes=[{"id": 1}, {"id": 2}]),
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert [ligne["id"] for ligne in resultat["lignes"]] == ["x:a"]
    assert resultat["non_candidats"]["total_profils"] == 1
    # Aucun identifiant ni nom de membre non candidat n'apparaît dans l'agrégat.
    assert "x:r" not in json.dumps(resultat["non_candidats"], ensure_ascii=False)
    assert "Robert" not in json.dumps(resultat["non_candidats"], ensure_ascii=False)


def test_compute_tableau_croise_candidats_provenance_absente_reste_un_candidat():
    profils = [
        {"id": "x:a", "nom": "Alice", "chambre": "AN"},
        {"id": "x:b", "nom": "Bob", "chambre": "AN", "meta": {"provenance": "candidat_declare"}},
        {"id": "x:c", "nom": "Chloé", "chambre": "AN", "meta": "pas un dict"},
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert [ligne["id"] for ligne in resultat["lignes"]] == ["x:a", "x:b", "x:c"]
    assert resultat["non_candidats"]["total_profils"] == 0


def test_compute_tableau_croise_candidats_agregat_non_candidats_par_groupe():
    profils = [
        roster("x:r1", "R1", "GDR", votes=[{"id": 1}]),
        roster("x:r2", "R2", "GDR", votes=[{"id": 1}, {"id": 2}, {"id": 3}]),
        roster("x:r3", "R3", "LFI", votes=[{"id": 1}, {"id": 2}]),
    ]

    resultat = compute_tableau_croise_candidats(profils)
    par_groupe = {ligne["groupe"]: ligne for ligne in resultat["non_candidats"]["par_groupe"]}

    assert [ligne["groupe"] for ligne in resultat["non_candidats"]["par_groupe"]] == ["GDR", "LFI"]
    assert par_groupe["GDR"]["nb_profils"] == 2
    assert par_groupe["GDR"]["votes"] == {"min": 1, "max": 3, "mediane": 2, "moyenne": 2.0}
    assert par_groupe["GDR"]["amendements"] == {
        "min": 0, "max": 0, "mediane": 0, "moyenne": 0.0,
    }
    assert par_groupe["LFI"]["votes"] == {"min": 2, "max": 2, "mediane": 2, "moyenne": 2.0}
    assert resultat["non_candidats"]["ensemble"]["votes"] == {
        "min": 1, "max": 3, "mediane": 2, "moyenne": 2.0,
    }


def test_compute_tableau_croise_candidats_non_candidat_sans_groupe_regroupe_sous_null():
    profils = [
        roster("x:r1", "R1", None, votes=[{"id": 1}]),
        roster("x:r2", "R2", "  ", votes=[{"id": 1}]),
    ]

    resultat = compute_tableau_croise_candidats(profils)

    assert [ligne["groupe"] for ligne in resultat["non_candidats"]["par_groupe"]] == ["null"]
    assert resultat["non_candidats"]["par_groupe"][0]["nb_profils"] == 2


# ---------------------------------------------------------------------------
# compute_plage_dates_candidats
# ---------------------------------------------------------------------------

def test_compute_plage_dates_candidats_liste_vide():
    resultat = compute_plage_dates_candidats([])

    assert resultat == {
        "lignes": [],
        "non_candidats": {
            "total_profils": 0,
            "par_groupe": [],
            "ensemble": {
                champ: {"min": None, "max": None}
                for champ in ("votes", "textes_portes", "amendements", "interventions")
            },
        },
        "dates_ignorees": {
            "votes": 0, "textes_portes": 0, "amendements": 0, "interventions": 0,
        },
    }


def test_compute_plage_dates_candidats_listes_vides_ou_absentes_donnent_null():
    profils = [
        {"id": "x:a", "nom": "Alice", "chambre": "AN", "votes": [], "textes_portes": None},
        {"id": "x:b", "nom": "Bob", "chambre": "AN"},
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    for ligne in resultat["lignes"]:
        for champ in ("votes", "textes_portes", "amendements", "interventions"):
            assert ligne[champ] == {"min": None, "max": None}
    assert resultat["dates_ignorees"] == {
        "votes": 0, "textes_portes": 0, "amendements": 0, "interventions": 0,
    }


# Depuis #432, un vote ne porte plus sa date : c'est un champ du scrutin, qui
# vit dans l'index partagé. La plage de dates des votes doit donc être calculée
# EN JOIGNANT l'index — sans quoi elle tomberait à null partout, silencieusement,
# alors que c'est elle qui avait montré que le corpus s'arrêtait en juin 2024.
_SCRUTINS_PLAGE: dict = {}


def _vote_date(date_valeur):
    """Vote au format mapping, dont la date est enregistrée dans l'index."""
    scrutin_id = f"an:16:{len(_SCRUTINS_PLAGE) + 1}"
    _SCRUTINS_PLAGE[scrutin_id] = {"id": scrutin_id, "date": date_valeur}
    return {"scrutin_id": scrutin_id, "position": "pour"}


def _index_plage():
    from scrutins_index import ScrutinsIndex
    index = ScrutinsIndex(dict(_SCRUTINS_PLAGE))
    _SCRUTINS_PLAGE.clear()
    return index


def test_compute_plage_dates_candidats_min_max_direct_sur_champ_date():
    profils = [
        {
            "id": "x:a", "nom": "Alice", "chambre": "AN",
            "votes": [_vote_date("2024-06-12"), _vote_date("2022-01-01"), _vote_date("2023-05-05")],
            "amendements": [{"date": "2021-11-30"}],
            "interventions": [{"date": "2020-03-14"}, {"date": "2020-09-01"}],
        },
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    ligne = resultat["lignes"][0]
    assert ligne["votes"] == {"min": "2022-01-01", "max": "2024-06-12"}
    assert ligne["amendements"] == {"min": "2021-11-30", "max": "2021-11-30"}
    assert ligne["interventions"] == {"min": "2020-03-14", "max": "2020-09-01"}


def test_compute_plage_dates_candidats_textes_portes_agrege_date_min_date_max():
    profils = [
        {
            "id": "x:a", "nom": "Alice", "chambre": "AN",
            "textes_portes": [
                {"date_min": "2022-01-01", "date_max": "2022-06-30"},
                {"date_min": "2023-02-01", "date_max": "2023-12-15"},
            ],
        },
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert resultat["lignes"][0]["textes_portes"] == {"min": "2022-01-01", "max": "2023-12-15"}


def test_compute_plage_dates_candidats_dates_invalides_ignorees_et_comptees():
    profils = [
        {
            "id": "x:a", "nom": "Alice", "chambre": "AN",
            "votes": [
                _vote_date("2024-06-12"),
                _vote_date("pas-une-date"),
                _vote_date(""),
            ],
        },
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert resultat["lignes"][0]["votes"] == {"min": "2024-06-12", "max": "2024-06-12"}
    assert resultat["dates_ignorees"]["votes"] == 2


def test_compute_plage_dates_candidats_date_absente_pas_comptee_comme_ignoree():
    profils = [{"id": "x:a", "nom": "Alice", "chambre": "AN", "votes": [{"id": 1}]}]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert resultat["lignes"][0]["votes"] == {"min": None, "max": None}
    assert resultat["dates_ignorees"]["votes"] == 0


def test_compute_plage_dates_candidats_textes_portes_dates_invalides_comptees():
    profils = [
        {
            "id": "x:a", "nom": "Alice", "chambre": "AN",
            "textes_portes": [
                {"date_min": "invalide", "date_max": "2022-06-30"},
                {"date_min": "2023-02-01", "date_max": "invalide"},
            ],
        },
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert resultat["lignes"][0]["textes_portes"] == {"min": "2023-02-01", "max": "2022-06-30"}
    assert resultat["dates_ignorees"]["textes_portes"] == 2


def test_compute_plage_dates_candidats_trie_par_nom():
    profils = [
        {"id": "x:z", "nom": "Zoé", "chambre": "AN"},
        {"id": "x:a", "nom": "Alban", "chambre": "AN"},
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert [ligne["nom"] for ligne in resultat["lignes"]] == ["Alban", "Zoé"]


def test_compute_plage_dates_candidats_exclut_les_profils_roster_du_detail():
    profils = [
        {"id": "x:a", "nom": "Alice", "chambre": "AN", "votes": [_vote_date("2024-01-01")]},
        roster("x:r", "Robert", "GDR", votes=[{"date": "2020-01-01"}]),
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert [ligne["id"] for ligne in resultat["lignes"]] == ["x:a"]
    assert resultat["non_candidats"]["total_profils"] == 1
    assert "Robert" not in json.dumps(resultat["non_candidats"], ensure_ascii=False)


def test_compute_plage_dates_candidats_agregat_non_candidats_par_groupe():
    profils = [
        roster("x:r1", "R1", "GDR", votes=[_vote_date("2021-06-01"), _vote_date("2022-01-01")]),
        roster("x:r2", "R2", "GDR", votes=[_vote_date("2019-03-15")]),
        roster("x:r3", "R3", "LFI", interventions=[{"date": "2023-09-09"}]),
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())
    par_groupe = {ligne["groupe"]: ligne for ligne in resultat["non_candidats"]["par_groupe"]}

    assert par_groupe["GDR"]["nb_profils"] == 2
    assert par_groupe["GDR"]["votes"] == {"min": "2019-03-15", "max": "2022-01-01"}
    assert par_groupe["GDR"]["interventions"] == {"min": None, "max": None}
    assert par_groupe["LFI"]["interventions"] == {"min": "2023-09-09", "max": "2023-09-09"}
    assert resultat["non_candidats"]["ensemble"]["votes"] == {
        "min": "2019-03-15", "max": "2022-01-01",
    }


def test_compute_plage_dates_candidats_dates_ignorees_couvrent_aussi_les_non_candidats():
    profils = [
        roster("x:r1", "R1", "GDR", votes=[_vote_date("pas-une-date")]),
    ]

    resultat = compute_plage_dates_candidats(profils, _index_plage())

    assert resultat["dates_ignorees"]["votes"] == 1


# ---------------------------------------------------------------------------
# compute_presence_meta
# ---------------------------------------------------------------------------

def test_compute_presence_meta_liste_vide():
    resultat = compute_presence_meta([])

    assert resultat == {
        "total_profils": 0,
        "meta_absente": [],
        "licence_donnees_manquante": [],
        "genere_le_manquant": [],
    }


def test_compute_presence_meta_meta_absent_du_profil():
    resultat = compute_presence_meta([{"id": "sans-meta"}])

    assert resultat["meta_absente"] == ["sans-meta"]
    assert resultat["licence_donnees_manquante"] == ["sans-meta"]
    assert resultat["genere_le_manquant"] == ["sans-meta"]


def test_compute_presence_meta_meta_incomplet():
    profils = [
        {"id": "licence-vide", "meta": {"licence_donnees": "", "genere_le": "2026-01-01T00:00:00"}},
        {"id": "genere_le-null", "meta": {"licence_donnees": "ODbL", "genere_le": None}},
        {"id": "complet", "meta": {"licence_donnees": "ODbL", "genere_le": "2026-01-01T00:00:00"}},
    ]

    resultat = compute_presence_meta(profils)

    assert resultat["meta_absente"] == []
    assert resultat["licence_donnees_manquante"] == ["licence-vide"]
    assert resultat["genere_le_manquant"] == ["genere_le-null"]


def test_compute_presence_meta_total_profils():
    resultat = compute_presence_meta([{"id": "a"}, {"id": "b", "meta": {}}])

    assert resultat["total_profils"] == 2
    assert resultat["meta_absente"] == ["a"]
    assert set(resultat["licence_donnees_manquante"]) == {"a", "b"}
    assert set(resultat["genere_le_manquant"]) == {"a", "b"}


# ---------------------------------------------------------------------------
# build_report
# ---------------------------------------------------------------------------

def test_build_report_structure_top_level_keys():
    rapport = build_report([], [], staleness_days=30, reference_date=REFERENCE)

    assert set(rapport.keys()) == {
        "meta", "volumetrie", "completude", "coherence", "fraicheur",
        "warnings", "tableau_croise_candidats", "plage_dates_candidats", "erreurs_lecture",
    }
    assert set(rapport["volumetrie"].keys()) == {
        "repartition_chambre", "repartition_provenance",
    }
    assert set(rapport["completude"].keys()) == {
        "taux_remplissage", "profils_sans_activite", "presence_meta",
    }
    assert set(rapport["coherence"].keys()) == {
        "doublons_id", "coherence_schema_version", "validite_dates",
        "coherence_chambre_sources",
    }
    assert set(rapport["fraicheur"].keys()) == {"fraicheur_sources", "profils_perimes"}


def test_build_report_meta_section():
    erreurs = [{"fichier": "x.pivot.json", "erreur": "boom"}]
    profils = [profil_sources("a", source("nosdeputes", 5))]

    rapport = build_report(profils, erreurs, staleness_days=15, reference_date=REFERENCE)

    assert rapport["meta"] == {
        "genere_le": REFERENCE.isoformat(),
        "total_profils": 1,
        # #630 — `total_profils` ne voyage plus seul : l'en-tête du rapport
        # Markdown affiche le compte AVEC sa ventilation, et il la lit ici.
        # Un pivot sans `meta.provenance` vaut `candidat_declare`
        # (rétro-compatibilité, docs/decisions/provenance-pivot.md).
        "ventilation_provenance": {
            "total": 1, "candidat_declare": 1, "roster_groupe": 0,
            "roster_gouvernement": 0, "provenance_autre": 0, "illisibles": 0,
        },
        "total_erreurs_lecture": 1,
        "staleness_days": 15,
    }


def test_build_report_erreurs_lecture_passthrough():
    erreurs = [{"fichier": "a.pivot.json", "erreur": "JSON invalide"}]

    rapport = build_report([], erreurs, reference_date=REFERENCE)

    assert rapport["erreurs_lecture"] == erreurs


def test_build_report_delegue_aux_fonctions_compute():
    profils = [
        profil_warnings("a", "votes introuvables : x"),
        profil_chambre("AN", ["wikidata"], id_="b"),
    ]
    erreurs = []

    rapport = build_report(profils, erreurs, staleness_days=30, reference_date=REFERENCE)

    assert rapport["volumetrie"]["repartition_chambre"] == compute_repartition_chambre(profils)
    assert rapport["volumetrie"]["repartition_provenance"] == compute_repartition_provenance(profils)
    assert rapport["completude"]["taux_remplissage"] == compute_taux_remplissage(profils)
    assert rapport["completude"]["profils_sans_activite"] == compute_profils_sans_activite(profils)
    assert rapport["completude"]["presence_meta"] == compute_presence_meta(profils)
    assert rapport["coherence"]["doublons_id"] == compute_doublons_id(profils)
    assert rapport["coherence"]["coherence_schema_version"] == compute_coherence_schema_version(profils)
    assert rapport["coherence"]["validite_dates"] == compute_validite_dates(profils)
    assert (
        rapport["coherence"]["coherence_chambre_sources"]
        == compute_coherence_chambre_sources(profils)
    )
    assert (
        rapport["fraicheur"]["fraicheur_sources"]
        == compute_fraicheur_sources(profils, reference_date=REFERENCE)
    )
    assert (
        rapport["fraicheur"]["profils_perimes"]
        == compute_profils_perimes(profils, staleness_days=30, reference_date=REFERENCE)
    )
    assert rapport["warnings"] == compute_agregation_warnings(profils)
    assert (
        rapport["tableau_croise_candidats"]
        == compute_tableau_croise_candidats(profils)
    )
    assert (
        rapport["plage_dates_candidats"]
        == compute_plage_dates_candidats(profils, _index_plage())
    )


def test_build_report_staleness_days_par_defaut():
    rapport = build_report([], [], reference_date=REFERENCE)

    assert rapport["meta"]["staleness_days"] == 30


def test_build_report_sans_reference_date_utilise_maintenant():
    rapport = build_report([], [])

    genere_le = datetime.fromisoformat(rapport["meta"]["genere_le"])
    assert (datetime.now(timezone.utc) - genere_le).total_seconds() < 5


def test_build_report_sur_les_fixtures_du_depot():
    profils, erreurs_lecture = load_pivot_directory(FIXTURES_DIR)

    rapport = build_report(profils, erreurs_lecture, staleness_days=30, reference_date=REFERENCE)

    assert rapport["meta"]["total_profils"] == 3
    assert rapport["meta"]["total_erreurs_lecture"] == 1
    # Le rapport doit rester intégralement sérialisable en JSON.
    json.dumps(rapport, ensure_ascii=False)


# ---------------------------------------------------------------------------
# generate_markdown_report
# ---------------------------------------------------------------------------

def test_generate_markdown_report_contient_toutes_les_sections():
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "# Rapport d'audit du jeu de données pivot" in markdown
    assert "## Volumétrie" in markdown
    assert "### Répartition par provenance" in markdown
    assert "## Tableau croisé des volumes par candidat" in markdown
    assert "## Plages temporelles par candidat" in markdown
    assert "## Complétude" in markdown
    assert "## Cohérence" in markdown
    assert "## Fraîcheur" in markdown
    assert "## Warnings" in markdown
    assert "## Erreurs de lecture" in markdown


def test_generate_markdown_report_sections_vides_affichent_un_message_explicite():
    rapport = build_report([], [], reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert "Aucun doublon détecté." in markdown
    assert "Aucune divergence détectée." in markdown
    assert "Aucune date invalide détectée." in markdown
    assert "Aucune incohérence détectée." in markdown
    assert "Aucune source datée." in markdown
    assert "Aucun profil périmé." in markdown
    assert "Aucune date ignorée." in markdown
    assert "Aucun warning." in markdown
    assert "Aucune erreur de lecture." in markdown


def test_generate_markdown_report_reflete_les_donnees_du_rapport():
    profils = [
        profil_chambre("AN", ["nosdeputes"], id_="a"),
        profil_chambre("AN", ["nosdeputes"], id_="a"),  # doublon volontaire
    ]
    erreurs = [{"fichier": "casse.pivot.json", "erreur": "JSON invalide"}]

    rapport = build_report(profils, erreurs, reference_date=REFERENCE)
    markdown = generate_markdown_report(rapport)

    assert "casse.pivot.json" in markdown
    assert "JSON invalide" in markdown
    assert "| a | 2 |" in markdown  # doublons_id : id "a" en double


def test_generate_markdown_report_retourne_une_chaine_non_vide():
    profils, erreurs_lecture = load_pivot_directory(FIXTURES_DIR)
    rapport = build_report(profils, erreurs_lecture, reference_date=REFERENCE)

    markdown = generate_markdown_report(rapport)

    assert isinstance(markdown, str)
    assert len(markdown) > 0


# ---------------------------------------------------------------------------
# CLI : _build_arg_parser / main
# ---------------------------------------------------------------------------

def test_build_arg_parser_defaut_staleness_days():
    parser = _build_arg_parser()
    args = parser.parse_args(["--input-dir", str(FIXTURES_DIR)])

    assert args.staleness_days == 30
    assert args.output_json is None
    assert args.output_md is None


def test_build_arg_parser_input_dir_obligatoire():
    parser = _build_arg_parser()
    try:
        parser.parse_args([])
        assert False, "SystemExit attendu (--input-dir manquant)"
    except SystemExit:
        pass


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
    assert rapport["meta"]["total_profils"] == 3
    assert rapport["meta"]["total_erreurs_lecture"] == 1
    assert rapport["meta"]["staleness_days"] == 30

    markdown = output_md.read_text(encoding="utf-8")
    assert "# Rapport d'audit du jeu de données pivot" in markdown


def test_main_sans_output_json_ecrit_sur_stdout(capsys):
    code = main(["--input-dir", str(FIXTURES_DIR)])

    assert code == 0
    captured = capsys.readouterr()
    rapport = json.loads(captured.out)
    assert rapport["meta"]["total_profils"] == 3


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
    json_files = list(tmp_path.glob("audit_pivot_*.json"))
    md_files = list(tmp_path.glob("audit_pivot_*.md"))
    assert len(json_files) == 1
    assert len(md_files) == 1

    rapport = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert rapport["meta"]["total_profils"] == 3


def test_main_output_dir_incompatible_avec_output_json(tmp_path):
    code = main([
        "--input-dir", str(FIXTURES_DIR),
        "--output-dir", str(tmp_path),
        "--output-json", str(tmp_path / "rapport.json"),
    ])

    assert code == 1
    assert list(tmp_path.glob("*.json")) == []


# ---------------------------------------------------------------------------
# Mémoire : le plafond est dans le test (#635)
# ---------------------------------------------------------------------------
#
# `load_pivot_directory` rangeait chaque profil pivot **entier** dans une liste.
# Mesuré sur les 481 profils committés du 30/08/2026 (651,5 Mo), sous un
# plafond `RLIMIT_AS` de 2,0 Gio, index partagés chargés : `MemoryError` autour
# du **300e** profil (293e et 304e sur deux exécutions), ~1 500 Mio de
# croissance pour 397 à 418 Mo de JSON lus — facteur × 3,6 à × 4,0, donc 2,3 à
# 2,5 Gio pour le corpus seul, en plus des ~517 Mio de
# l'index des amendements. L'audit ne rendait pas son rapport.
#
# Ce que l'audit lit de ces listes est pourtant deux choses seulement : leur
# cardinal, et la plage de dates de leurs entrées. Ce sont ces deux résultats
# qui sont désormais retenus (`ListeReduite`), pas les 6,09 millions d'entrées
# qui les portent. Une projection par clés ne suffisait pas : réduite à
# `{amendement_id}`, une entrée pèse encore 184 octets de `dict` — 1,6 Gio pour
# le seul corpus.

#: Profils du corpus-fixture de mesure.
NB_PROFILS_FIXTURE_MEMOIRE = 24

#: Poids visé, par profil, de chacune des trois listes métier dont les entrées
#: doivent être relâchées (`amendements`, `votes`, `interventions`).
POIDS_LISTE_RELACHEE = 800 * 1024

#: Plancher de vraisemblance du corpus-fixture : sous ce poids, le plafond
#: qu'il déduit ne prouve plus rien. Regonfler les fixtures, jamais desserrer
#: le plancher.
PLANCHER_POIDS_RELACHE = 40 * 1024 * 1024

_PILOTE_MEMOIRE = """\
import json, resource, sys
from pathlib import Path

depot, dossier = sys.argv[1], sys.argv[2]
sys.path.insert(0, str(Path(depot) / "src"))
import audit_pivot_dataset as audit

depart = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
profils, erreurs = audit.load_pivot_directory(Path(dossier))
rapport = audit.build_report(profils, erreurs)
pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({
    "depart": depart, "pic": pic,
    "nb": rapport["meta"]["total_profils"],
    "amendements": rapport["tableau_croise_candidats"]["lignes"][0]["amendements"],
}))
"""


def _liste_lourde_memoire(octets_vises: int, gabarit: dict) -> list:
    """Une liste métier pesant environ `octets_vises` une fois sérialisée.

    Entrées **petites** à dessein : depuis #431 et #432 un `amendements[]` ou un
    `votes[]` publié est un mapping à deux clés, et c'est cette forme-là qui
    gonfle d'un facteur 3 à 10 en objets Python (× 3,95 mesuré ici sur le
    corpus committé). Une fixture bâtie sur de longues chaînes ne gonflerait
    que d'environ × 1,5 et le garde-fou ne séparerait plus rien.
    """
    (cle_id, _), = [(k, v) for k, v in gabarit.items() if k.endswith("_id")]
    unite = len(json.dumps(gabarit, ensure_ascii=False)) + 1
    return [
        dict(gabarit, **{cle_id: f"{gabarit[cle_id]}{i:07d}"})
        for i in range(max(1, octets_vises // unite))
    ]


def _corpus_de_mesure_memoire(tmp_path: Path) -> tuple[Path, int]:
    """Écrit un corpus-fixture et rend le **poids sur disque des entrées que
    l'audit doit relâcher** — c'est de ce poids, et non d'une observation, que
    le plafond est déduit."""
    dossier = tmp_path / "pivot_profiles"
    dossier.mkdir()

    amendements = _liste_lourde_memoire(
        POIDS_LISTE_RELACHEE,
        {"amendement_id": "an:AMANR5L16PO0000B0000P0D0N", "role_signataire": "cosignataire"},
    )
    votes = _liste_lourde_memoire(
        POIDS_LISTE_RELACHEE, {"scrutin_id": "an:16:", "position": "pour"},
    )
    interventions = _liste_lourde_memoire(
        POIDS_LISTE_RELACHEE, {"intervention_id": "an:seance:", "date": "2024-03-12"},
    )
    poids_relache = NB_PROFILS_FIXTURE_MEMOIRE * sum(
        len(json.dumps(bloc, ensure_ascii=False))
        for bloc in (amendements, votes, interventions)
    )

    for i in range(NB_PROFILS_FIXTURE_MEMOIRE):
        profil = {
            "schema_version": "1",
            "id": f"depute-{i:03d}",
            "nom": f"Députée {i:03d}",
            "chambres": ["AN"],
            "parti": "Parti",
            "groupe": "Groupe",
            "tags_thematiques": ["sante"],
            "sources": [{"type": "assemblee_nationale",
                         "url": "https://data.assemblee-nationale.fr",
                         "synchro_le": "2026-08-30T10:00:00+0000"}],
            "mandats": [{"categorie": "mandat_electif", "debut": "2022-06-22"}],
            "votes": votes,
            "amendements": amendements,
            "interventions": interventions,
            "textes_portes": [],
            "couverture": {"amendements": {"motif": None}},
            "identite": {"nom_complet": f"Députée {i:03d}"},
            "meta": {"schema_version": "1", "genere_le": "2026-08-30T11:00:00+0000",
                     "licence_donnees": "Licence Ouverte", "warnings": [],
                     "provenance": "candidat_declare"},
        }
        (dossier / f"depute-{i:03d}.pivot.json").write_text(
            json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    return dossier, poids_relache


def test_load_pivot_directory_ne_retient_que_ce_que_les_mesures_lisent(tmp_path):
    """Le fond du défaut : un document lu n'est jamais un document gardé.

    Le pic mémoire dépend de la machine ; **ce que la projection retient** n'en
    dépend pas. C'est donc ici que l'invariant est verrouillé, et le test de
    plafond qui suit ne fait que confirmer qu'il a l'effet annoncé.
    """
    profil = {
        "schema_version": "1", "id": "depute", "nom": "Députée",
        "chambres": ["AN"], "parti": "P", "groupe": "G",
        "tags_thematiques": ["sante", "climat"],
        "sources": [{"type": "assemblee_nationale", "url": "u", "synchro_le": "2026-08-30T10:00:00+0000"}],
        "mandats": [{"categorie": "mandat_electif"}, {"categorie": "commission"}],
        "votes": [{"scrutin_id": "an:16:1", "position": "pour"}],
        "amendements": [{"amendement_id": "an:X", "role_signataire": "auteur"}],
        "interventions": [{"date": "2024-03-12"}, {"date": "2024-05-02"}],
        "textes_portes": [{"date_min": "2023-01-01", "date_max": "2023-06-01"}],
        "couverture": {"amendements": {"motif": None}},
        "identite": {"nom_complet": "Députée"},
        "identifiants": {"hatvp": "https://www.hatvp.fr/fiche/x"},
        "meta": {"schema_version": "1", "genere_le": "2026-08-30T11:00:00+0000",
                 "licence_donnees": "Licence Ouverte", "warnings": []},
    }
    (tmp_path / "depute.pivot.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    profils, erreurs = load_pivot_directory(tmp_path)
    assert erreurs == []
    projete = profils[0]

    for bloc in ("identite", "identifiants", "couverture"):
        assert bloc not in projete, f"{bloc} n'est ouvert par aucune mesure"
    for bloc in BLOCS_LUS_AUDIT:
        if bloc in profil:
            assert bloc in projete

    # Les listes métier ne survivent que par ce que les mesures en lisent.
    for champ in ("mandats", "tags_thematiques", "votes", "amendements",
                  "interventions", "textes_portes"):
        assert isinstance(projete[champ], ListeReduite)
    assert len(projete["mandats"]) == 2
    assert projete["amendements"].nb == 1
    assert projete["interventions"].date_min == "2024-03-12"
    assert projete["interventions"].date_max == "2024-05-02"
    assert projete["textes_portes"].date_min == "2023-01-01"
    assert projete["textes_portes"].date_max == "2023-06-01"


def test_les_mesures_lisent_le_meme_chiffre_sur_la_liste_et_sur_sa_reduction(tmp_path):
    """La projection ne peut pas changer un chiffre : le rapport tiré des
    profils projetés est celui qu'on tire des profils entiers."""
    profil = {
        "schema_version": "1", "id": "depute", "nom": "Députée", "chambres": ["AN"],
        "parti": "P", "groupe": None, "tags_thematiques": [],
        "sources": [{"type": "assemblee_nationale", "url": "u",
                     "synchro_le": "2026-08-20T10:00:00+0000"}],
        "mandats": [{"categorie": "mandat_electif"}],
        "votes": [{"scrutin_id": "an:16:1", "position": "pour",
                   "scrutin_non_resolu": {"date": "2024-02-01"}}],
        "amendements": [{"amendement_id": None,
                         "amendement_non_resolu": {"date": "2024-04-01"}},
                        {"amendement_id": None,
                         "amendement_non_resolu": {"date": "pas-une-date"}}],
        "interventions": [{"date": "2024-03-12"}],
        "textes_portes": [],
        "meta": {"schema_version": "1", "genere_le": "2026-08-30T11:00:00+0000",
                 "licence_donnees": "Licence Ouverte", "warnings": ["a : b"]},
    }
    (tmp_path / "depute.pivot.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    reference = datetime(2026, 8, 30, 12, 0, tzinfo=timezone.utc)
    projetes, _ = load_pivot_directory(tmp_path)
    depuis_projection = build_report(projetes, [], reference_date=reference)
    depuis_entiers = build_report([profil], [], reference_date=reference)

    assert depuis_projection == depuis_entiers
    # Le cas qui compte : une date illisible reste **comptée**, jamais masquée.
    assert depuis_projection["plage_dates_candidats"]["dates_ignorees"]["amendements"] == 1


@pytest.mark.skipif(sys.platform.startswith("win"), reason="`resource` est POSIX")
def test_le_pic_memoire_de_l_audit_reste_sous_le_plafond_declare(tmp_path):
    """L'audit ne doit pas croître de plus que le poids **sur disque** des
    entrées qu'il est censé relâcher.

    D'où vient le plafond
    ---------------------
    Il n'est pas relevé sur une exécution puis arrondi — ce serait un plafond
    qui suit la dérive qu'il doit signaler. C'est une **règle** : la croissance
    mémoire de l'audit doit rester sous le poids en octets, sur disque, des
    entrées qu'il lit et ne doit pas garder. Le raisonnement tient en une
    ligne : la désérialisation JSON ne **réduit** jamais — donc si l'audit
    croît de moins que le texte qu'il a lu, il ne peut pas le détenir.

    Ce que le test ne prouve pas
    ----------------------------
    Ni la vitesse, ni le pic absolu sur le corpus réel — mesuré à 539 Mio pour
    les 481 profils committés, dont **517 Mio d'index des amendements partagé**,
    que #635 ne touche pas. Et rien de tout cela n'est mesuré en CI :
    `pivot_data` est hors du sparse-checkout de `tests.yml` (#473).
    """
    dossier, poids_relache = _corpus_de_mesure_memoire(tmp_path)
    assert poids_relache >= PLANCHER_POIDS_RELACHE, (
        f"corpus-fixture trop léger ({poids_relache / 1024**2:.0f} Mio d'entrées "
        f"à relâcher) : sous ce plancher le plafond qu'il déduit ne prouve plus "
        f"rien. Regonfler les fixtures, jamais desserrer le plancher.")

    pilote = tmp_path / "pilote_memoire.py"
    pilote.write_text(_PILOTE_MEMOIRE, encoding="utf-8")
    acheve = subprocess.run(
        [sys.executable, str(pilote), str(Path(__file__).resolve().parents[1]), str(dossier)],
        capture_output=True, text=True, timeout=300,
    )
    assert acheve.returncode == 0, (
        f"l'audit n'a pas rendu son rapport (code {acheve.returncode}) — un 137 "
        f"est un OOM, le défaut même de #635 :\n{acheve.stderr[-2000:]}")
    mesure = json.loads(acheve.stdout.strip().splitlines()[-1])

    assert mesure["nb"] == NB_PROFILS_FIXTURE_MEMOIRE
    assert mesure["amendements"] > 0, (
        "le cardinal doit survivre à la réduction : c'est une mesure publiée")

    # `ru_maxrss` est en Kio sous Linux, en octets sous macOS.
    facteur = 1 if sys.platform == "darwin" else 1024
    croissance = (mesure["pic"] - mesure["depart"]) * facteur
    assert croissance < poids_relache, (
        f"l'audit a grossi de {croissance / 1024**2:.1f} Mio en lisant "
        f"{NB_PROFILS_FIXTURE_MEMOIRE} profils dont {poids_relache / 1024**2:.0f} Mio "
        f"d'entrées qu'il ne doit pas garder. Au-dessus de ce plafond il en "
        f"retient une partie : c'est le défaut de #635, qui faisait atteindre le "
        f"plafond de 2,0 Gio autour du 300e des 481 profils committés.")
