import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from generate_gouvernement_profiles import (
    COLLECTE_INCOMPLETE,
    EXIT_COLLECTE_INCOMPLETE,
    generate_all,
    main as generate_gouvernement_profiles_main,
)
from schema_gouvernement import validate_profil_gouvernement

import pytest

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/gouvernements_reels.json")

REPO_ROOT = Path(__file__).resolve().parents[1]


def _pivot(id_: str, nom: str, mandats: list) -> dict:
    return {
        "schema_version": "1",
        "id": id_,
        "nom": nom,
        "chambre": "AN",
        "parti": None,
        "groupe": None,
        "sources": [],
        "mandats": mandats,
        "votes": [],
        "textes_portes": [],
        "amendements": [],
        "interventions": [],
        "tags_thematiques": [],
        "meta": {"schema_version": "1", "genere_le": "2026-07-29T10:00:00+0000", "licence_donnees": "", "warnings": []},
    }


def _mandat_gouv(label: str, debut: str, fin: str = None, actif: bool = False) -> dict:
    return {
        "categorie": "fonction_gouvernementale",
        "type": "membre",
        "label": label,
        "debut": debut,
        "fin": fin,
        "actif": actif,
        "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/...",
        "position_dans_hemicycle": "gouvernement",
    }


# `legislatures_ingerees` fait partie du contrat de
# `fetch_dossiers_gouvernementaux` depuis #427 : sans elle, l'appelant ne peut
# pas distinguer « zéro dossier constaté » de « collecte incomplète ». Les
# doubles doivent donc la renvoyer, sous peine de déclencher le garde-fou pour
# une raison sans rapport avec ce qu'ils testent.
def _toutes_legislatures() -> list[int]:
    from gouvernement_textes import AN_DOSSIERS_ARCHIVES

    return sorted(AN_DOSSIERS_ARCHIVES)


def _dossier(dossier_id: str, statut: str, date_depot: str, chambre: str = "AN") -> dict:
    return {
        "dossier_id": dossier_id,
        "titre": "Projet de loi test",
        "statut": statut,
        "sort_49_3": False,
        "chambre_depot_initial": chambre,
        "date_depot": date_depot,
        "date_dernier_evenement": date_depot,
        "legislature": "17",
        "source_url": f"https://www.assemblee-nationale.fr/dyn/17/dossiers/{dossier_id}",
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# generate_all : un seul fetch réseau / chargement disque partagé entre tous
# les gouvernements du batch
# ---------------------------------------------------------------------------

def test_generate_all_fetches_dossiers_once_for_all_gouvernements(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "a.pivot.json").write_text(json.dumps(
        _pivot("nosdeputes:a", "A", [_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")])
    ), encoding="utf-8")
    (profiles_dir / "b.pivot.json").write_text(json.dumps(
        _pivot("nosdeputes:b", "B", [_mandat_gouv("Gouvernement (ATTAL)", "2024-01-10", "2024-09-05", actif=False)])
    ), encoding="utf-8")
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()

    call_count = {"n": 0}

    def fake_fetch_dossiers_gouvernementaux():
        call_count["n"] += 1
        return {
            "dossiers": [
                _dossier("D-BAYROU", "adopte", "2025-01-10"),
                _dossier("D-ATTAL", "rejete", "2024-03-01"),
            ],
            "warnings": [],
            "legislatures_ingerees": _toutes_legislatures(),
        }

    monkeypatch.setattr("generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", fake_fetch_dossiers_gouvernementaux)

    gouvernements = [
        {"gouvernement_id": "gouvernement:BAYROU", "nom": "Gouvernement Bayrou", "libelle_an": "BAYROU",
         "periode": {"debut": "2024-12-24", "fin": "2025-09-09"}, "fichier": "gouvernement-BAYROU.json"},
        {"gouvernement_id": "gouvernement:ATTAL", "nom": "Gouvernement Attal", "libelle_an": "ATTAL",
         "periode": {"debut": "2024-01-10", "fin": "2024-09-05"}, "fichier": "gouvernement-ATTAL.json"},
    ]

    echecs = generate_all(gouvernements, profiles_dir=profiles_dir, out_dir=out_dir, validate=True)

    assert echecs == 0
    assert call_count["n"] == 1  # un seul fetch réseau partagé entre les 2 gouvernements

    bayrou = json.loads((out_dir / "gouvernement-BAYROU.json").read_text(encoding="utf-8"))
    attal = json.loads((out_dir / "gouvernement-ATTAL.json").read_text(encoding="utf-8"))

    assert {m["membre_id"] for m in bayrou["membres"]} == {"nosdeputes:a"}
    assert {t["dossier_id"] for t in bayrou["textes"]} == {"D-BAYROU"}
    assert {m["membre_id"] for m in attal["membres"]} == {"nosdeputes:b"}
    assert {t["dossier_id"] for t in attal["textes"]} == {"D-ATTAL"}

    # Aucun double-comptage : chaque dossier n'apparaît que dans le
    # gouvernement dont la période couvre sa date de dépôt.
    assert "D-ATTAL" not in {t["dossier_id"] for t in bayrou["textes"]}
    assert "D-BAYROU" not in {t["dossier_id"] for t in attal["textes"]}

    assert validate_profil_gouvernement(bayrou) == []
    assert validate_profil_gouvernement(attal) == []


def _gouvernement_bayrou() -> dict:
    return {
        "gouvernement_id": "gouvernement:BAYROU", "nom": "Gouvernement Bayrou",
        "libelle_an": "BAYROU", "periode": {"debut": "2024-12-24", "fin": "2025-09-09"},
        "fichier": "gouvernement-BAYROU.json",
    }


def test_collecte_totalement_echouee_nreecrit_aucun_profil(tmp_path, monkeypatch):
    """#427 : ce script ÉCRASE les profils. Une coupure réseau rendait
    `dossiers = []`, ce qui réécrivait les 10 gouvernements avec `textes: []`
    — 725 textes perdus, committés et publiés, sans que le quality gate ne
    bloque. Un zéro non mesuré n'est pas une donnée (AGENTS.md §2.5).

    Avant ce correctif, ce test assertait l'inverse : que le profil ÉTAIT
    écrit avec `textes == []`.
    """
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()

    # Profil déjà committé, avec des textes : il ne doit pas être touché.
    existant = out_dir / "gouvernement-BAYROU.json"
    existant.write_text(json.dumps({"textes": [{"dossier_id": "DEJA-LA"}]}), encoding="utf-8")

    def fake_fetch():
        return {
            "dossiers": [],
            "warnings": ["gouvernement_textes: téléchargement impossible."],
            "legislatures_ingerees": [],
        }

    monkeypatch.setattr("generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", fake_fetch)

    resultat = generate_all([_gouvernement_bayrou()], profiles_dir=profiles_dir, out_dir=out_dir)

    assert resultat is COLLECTE_INCOMPLETE
    conserve = json.loads(existant.read_text(encoding="utf-8"))
    assert conserve["textes"] == [{"dossier_id": "DEJA-LA"}], "le profil existant a été écrasé"


def test_collecte_partielle_nreecrit_aucun_profil(tmp_path, monkeypatch):
    """Une seule archive manquante suffit : perdre la XV, c'est perdre les 282
    textes de Philippe II. Le garde-fou ne se limite donc pas à l'échec total.
    """
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()

    partielles = _toutes_legislatures()[1:]  # une archive en moins
    assert partielles, "le test suppose au moins deux archives connues"

    def fake_fetch():
        return {"dossiers": [], "warnings": [], "legislatures_ingerees": partielles}

    monkeypatch.setattr("generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", fake_fetch)

    resultat = generate_all([_gouvernement_bayrou()], profiles_dir=profiles_dir, out_dir=out_dir)

    assert resultat is COLLECTE_INCOMPLETE
    assert not (out_dir / "gouvernement-BAYROU.json").exists()


def test_main_retourne_un_code_distinct_sur_collecte_incomplete(tmp_path, monkeypatch):
    """Le code 2 distingue « collecte incomplète, rien touché » d'un échec de
    génération ordinaire (1) — le workflow peut ainsi traiter le premier comme
    dégradé-mais-sûr sans masquer le second."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()
    config_path = tmp_path / "gouvernements.json"
    config_path.write_text(json.dumps({"gouvernements": [_gouvernement_bayrou()]}), encoding="utf-8")

    monkeypatch.setattr(
        "generate_gouvernement_profiles.fetch_dossiers_gouvernementaux",
        lambda: {"dossiers": [], "warnings": [], "legislatures_ingerees": []},
    )

    rc = generate_gouvernement_profiles_main([
        "--config", str(config_path),
        "--profiles-dir", str(profiles_dir),
        "--out-dir", str(out_dir),
    ])
    assert rc == EXIT_COLLECTE_INCOMPLETE
    assert rc != 1, "ne doit pas être confondu avec un échec de génération"


def test_generate_all_echec_sur_un_gouvernement_n_arrete_pas_les_autres(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()

    def fake_fetch_dossiers_gouvernementaux():
        return {"dossiers": [], "warnings": [], "legislatures_ingerees": _toutes_legislatures()}

    monkeypatch.setattr("generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", fake_fetch_dossiers_gouvernementaux)

    gouvernements = [
        {"gouvernement_id": "gouvernement:CASSE", "nom": "Gouvernement Casse", "libelle_an": "CASSE",
         "periode": "not-a-dict", "fichier": "gouvernement-CASSE.json"},  # provoque une exception dans build_gouvernement_profile
        {"gouvernement_id": "gouvernement:OK", "nom": "Gouvernement OK", "libelle_an": "OK",
         "periode": {"debut": "2020-01-01", "fin": "2020-06-01"}, "fichier": "gouvernement-OK.json"},
    ]

    echecs = generate_all(gouvernements, profiles_dir=profiles_dir, out_dir=out_dir, validate=True)

    assert echecs == 1
    assert not (out_dir / "gouvernement-CASSE.json").exists()
    assert (out_dir / "gouvernement-OK.json").exists()


# ---------------------------------------------------------------------------
# main() : lecture de la config JSON
# ---------------------------------------------------------------------------

def test_main_reads_config_and_generates(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "a.pivot.json").write_text(json.dumps(
        _pivot("nosdeputes:a", "A", [_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")])
    ), encoding="utf-8")
    out_dir = tmp_path / "gouvernements"

    config_path = tmp_path / "gouvernements_reels.json"
    config_path.write_text(json.dumps({
        "gouvernements": [
            {"gouvernement_id": "gouvernement:BAYROU", "nom": "Gouvernement Bayrou", "libelle_an": "BAYROU",
             "periode": {"debut": "2024-12-24", "fin": "2025-09-09"}, "fichier": "gouvernement-BAYROU.json"},
        ]
    }), encoding="utf-8")

    def fake_fetch_dossiers_gouvernementaux():
        return {"dossiers": [], "warnings": [], "legislatures_ingerees": _toutes_legislatures()}

    monkeypatch.setattr("generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", fake_fetch_dossiers_gouvernementaux)

    rc = generate_gouvernement_profiles_main([
        "--config", str(config_path),
        "--profiles-dir", str(profiles_dir),
        "--out-dir", str(out_dir),
    ])

    assert rc == 0
    assert (out_dir / "gouvernement-BAYROU.json").exists()


def test_main_missing_config_returns_error(tmp_path):
    rc = generate_gouvernement_profiles_main(["--config", str(tmp_path / "does-not-exist.json")])
    assert rc == 1


def test_main_empty_gouvernements_returns_error(tmp_path):
    config_path = tmp_path / "empty.json"
    config_path.write_text(json.dumps({"gouvernements": []}), encoding="utf-8")
    rc = generate_gouvernement_profiles_main(["--config", str(config_path)])
    assert rc == 1


def test_repository_gouvernements_reels_json_is_valid():
    config_path = REPO_ROOT / "raw_data" / "gouvernements_reels.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(payload.get("gouvernements"), list)
    assert payload["gouvernements"]


# ---------------------------------------------------------------------------
# #1020 — la parole agrégée, par le CHEMIN RÉEL
# ---------------------------------------------------------------------------
#
# Ces deux cas existent parce que les leurs n'ont pas suffi. `tags_thematiques_agreges`
# a été publié `[]` sur les 17 fiches, et `comptages.membres_avec_interventions`
# à `0`, pendant un run entier : `load_profils_from_dir` projette les profils
# sur cinq blocs (#635) et `interventions` n'en fait pas partie, donc
# l'agrégation lisait un bloc absent.
#
# `tests/test_agregat_parole_gouvernement_1020.py` ne pouvait pas le voir : il
# fabrique ses profils, avec leurs interventions dedans, et les passe
# directement à `agreger_tags_thematiques`. Un test qui contourne le chemin
# réel ne prouve rien de ce chemin. Ici les profils sont ÉCRITS SUR DISQUE et
# c'est `generate_all` qui les lit.


def _pivot_avec_interventions(id_: str, nom: str, mandats: list, interventions: list) -> dict:
    profil = _pivot(id_, nom, mandats)
    profil["interventions"] = interventions
    return profil


def _interv(date: str, theme: str) -> dict:
    return {"intervention_id": f"syceron_{theme}_{date}", "date": date,
            "theme_officiel": theme, "mots_cles": []}


def _fetch_sans_dossier():
    return {"dossiers": [], "warnings": [], "legislatures_ingerees": _toutes_legislatures()}


def test_les_tags_agreges_traversent_la_lecture_des_profils(tmp_path, monkeypatch):
    """La fiche produite par `generate_all` porte les étiquettes de ses membres.

    Le profil écrit ici porte ses `interventions` ; la projection les retire de
    la liste chargée, et seule une lecture à la demande peut les retrouver.
    """
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "a.pivot.json").write_text(json.dumps(_pivot_avec_interventions(
        "a", "A",
        [_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")],
        [_interv("2025-02-01", "budget"), _interv("2025-03-01", "outre-mer")],
    )), encoding="utf-8")
    (profiles_dir / "b.pivot.json").write_text(json.dumps(_pivot_avec_interventions(
        "b", "B",
        [_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")],
        [_interv("2025-02-02", "budget")],
    )), encoding="utf-8")
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()

    monkeypatch.setattr(
        "generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", _fetch_sans_dossier)

    echecs = generate_all([_gouvernement_bayrou()], profiles_dir=profiles_dir,
                          out_dir=out_dir, validate=True)

    assert echecs == 0
    fiche = json.loads((out_dir / "gouvernement-BAYROU.json").read_text(encoding="utf-8"))
    assert [(t["tag"], t["nb_membres_porteurs"]) for t in fiche["tags_thematiques_agreges"]] == [
        ("budget", 2), ("outre-mer", 1),
    ]
    assert fiche["comptages"]["membres_avec_interventions"] == 2


def test_une_intervention_hors_fenetre_du_membre_ne_traverse_pas_non_plus(tmp_path, monkeypatch):
    """Le filtre de #1020 s'applique bien sur le chemin réel, pas seulement
    dans la fonction : le cas Braun-Pivet, en miniature."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "a.pivot.json").write_text(json.dumps(_pivot_avec_interventions(
        "a", "A",
        [_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-01-05")],
        [_interv("2025-01-02", "outre-mer"), _interv("2025-06-01", "budget")],
    )), encoding="utf-8")
    out_dir = tmp_path / "gouvernements"
    out_dir.mkdir()

    monkeypatch.setattr(
        "generate_gouvernement_profiles.fetch_dossiers_gouvernementaux", _fetch_sans_dossier)

    generate_all([_gouvernement_bayrou()], profiles_dir=profiles_dir, out_dir=out_dir)

    fiche = json.loads((out_dir / "gouvernement-BAYROU.json").read_text(encoding="utf-8"))
    assert [t["tag"] for t in fiche["tags_thematiques_agreges"]] == ["outre-mer"]
    assert any("hors de la fenêtre" in w for w in fiche["meta"]["warnings"])
