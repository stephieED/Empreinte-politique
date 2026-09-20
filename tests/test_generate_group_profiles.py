import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from amendements_index import charger as charger_amendements_reel
from generate_group_profiles import generate_all, main as generate_group_profiles_main
from schema_groupe import validate_profil_groupe
from scrutins_index import charger as charger_scrutins_reel

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


@pytest.fixture(autouse=True)
def index_partages_isoles(monkeypatch, tmp_path_factory):
    """Coupe les index partagés du corpus vivant pour tout ce fichier (#473).

    `generate_all()` reçoit `scrutins_path` / `amendements_path` en **valeur par
    défaut de paramètre** — liée à la définition, donc insensible à un
    monkeypatch de la globale du module. Cinq tests d'ici lisaient ainsi
    `pivot_data/scrutins.json` et `pivot_data/amendements/` (~66 Mo) sans qu'une
    seule assertion n'en dépende : leurs pivots portent `votes: []` et
    `amendements: []`. C'est le pendant en lecture du piège d'écriture déjà
    rencontré ici — un défaut qui pointe dans le dépôt.

    Les vrais chargeurs sont conservés, appliqués à un chemin absent : ils
    rendent un index vide du bon type (contrat documenté « index vide si le
    fichier est absent »), plutôt qu'un doublon de test qui dériverait.
    """
    absent = tmp_path_factory.mktemp("index-partages-absents")
    monkeypatch.setattr(
        "generate_group_profiles.charger_scrutins",
        lambda _chemin: charger_scrutins_reel(absent / "scrutins.json"),
    )
    monkeypatch.setattr(
        "generate_group_profiles.charger_amendements",
        lambda _dossier, **kwargs: charger_amendements_reel(absent / "amendements", **kwargs),
    )


#: Bloc `correspondance_sigles_an` minimal, mais **verbatim** : `LR`-16 est
#: bien l'organe `PO800508` et l'Assemblée le déclare `Opposition` dans AMO30
#: (mesuré le 01/09/2026 sur l'archive réelle, cf. tests/test_an_roster.py).
#: Rien n'est inventé ici — ni le sigle AN, ni l'uid d'organe, ni la chaîne
#: source (#510 : une fixture se réduit, elle ne se rédige pas).
SOURCE_AMO30 = (
    "https://data.assemblee-nationale.fr/static/openData/repository/17/amo/"
    "tous_acteurs_mandats_organes_xi_legislature/"
    "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip"
)


def _correspondance_sigles_an(groupe_sigle: str = "LR") -> dict:
    """Table sigle publié → sigle AN, avec la qualification déclarée (#686)."""
    return {
        "source": SOURCE_AMO30,
        "groupes": [
            {
                "groupe_sigle": groupe_sigle,
                "groupe_id": f"AN:{groupe_sigle}",
                "legislature": "16",
                "fichier": f"groupe-AN-{groupe_sigle}-16.json",
                "sigles_an": ["LR"],
                "organes_an": ["PO800508"],
                "position_politique_an": {
                    "position": "opposition",
                    "verifie_le": "2026-09-01",
                    "organes": [
                        {"organe_an": "PO800508", "sigle_an": "LR",
                         "valeur_source": "Opposition", "position": "opposition"},
                    ],
                },
                "effectif_amo30": 63,
                "verifie_le": "2026-09-01",
            },
        ],
    }


def _pivot(id_: str, nom: str) -> dict:
    return {
        "schema_version": "1",
        "id": id_,
        "nom": nom,
        "chambre": "AN",
        "parti": None,
        "groupe": None,
        "sources": [],
        "mandats": [
            {
                "categorie": "mandat_electif",
                "label": "Mandat parlementaire",
                "fonction": "mandat",
                "debut": "2022-06-22",
                "fin": None,
                "actif": True,
            }
        ],
        "votes": [],
        "textes_portes": [],
        "interventions": [],
        "amendements": [],
        "tags_thematiques": [],
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-07-29T10:00:00+0000",
            "licence_donnees": "ODbL",
            "warnings": [],
        },
    }


def _deputes_payload():
    return {
        "deputes": [
            {"depute": {"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None}},
            {"depute": {"slug": "bob", "nom": "Bob", "groupe_sigle": "SOC", "mandat_debut": "2022-06-22", "mandat_fin": None}},
        ]
    }


# ---------------------------------------------------------------------------
# generate_all : un seul fetch réseau par (chambre, législature) partagée
# ---------------------------------------------------------------------------

def test_generate_all_fetches_once_per_chambre_legislature(tmp_path, monkeypatch):
    (tmp_path / "profiles").mkdir()
    (tmp_path / "profiles" / "alice.pivot.json").write_text(json.dumps(_pivot("nosdeputes:alice", "Alice")), encoding="utf-8")
    (tmp_path / "profiles" / "bob.pivot.json").write_text(json.dumps(_pivot("nosdeputes:bob", "Bob")), encoding="utf-8")
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    call_count = {"n": 0}

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        call_count["n"] += 1
        assert chambre == "deputes"
        assert legislature == "16"
        return [m["depute"] for m in _deputes_payload()["deputes"]]

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", fake_fetch_full_roster)

    groupes = [
        {"roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR", "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16", "fichier": "groupe-AN-LR-16.json"},
        {"roster_chambre": "deputes", "groupe_id": "AN:SOC", "groupe_sigle": "SOC", "groupe_nom": "Socialistes", "chambre": "AN", "legislature": "16", "fichier": "groupe-AN-SOC-16.json"},
    ]

    resultat = generate_all(groupes, profiles_dir=tmp_path / "profiles", out_dir=out_dir, validate=True)

    assert resultat.echecs == 0
    assert call_count["n"] == 1  # un seul fetch réseau partagé entre les 2 groupes

    lr = json.loads((out_dir / "groupe-AN-LR-16.json").read_text(encoding="utf-8"))
    soc = json.loads((out_dir / "groupe-AN-SOC-16.json").read_text(encoding="utf-8"))
    assert {m["membre_id"] for m in lr["membres"]} == {"nosdeputes:alice"}
    assert {m["membre_id"] for m in soc["membres"]} == {"nosdeputes:bob"}
    assert validate_profil_groupe(lr) == []
    assert validate_profil_groupe(soc) == []


def test_generate_all_two_chambres_two_fetches(tmp_path, monkeypatch):
    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    fetch_calls = []

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        fetch_calls.append((chambre, legislature))
        if chambre == "deputes":
            return [m["depute"] for m in _deputes_payload()["deputes"]]
        return [{"slug": "carla", "nom": "Carla", "groupe_sigle": "LR", "mandat_debut": "2020-01-01", "mandat_fin": None}]

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", fake_fetch_full_roster)

    groupes = [
        {"roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR", "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16", "fichier": "groupe-AN-LR-16.json"},
        {"roster_chambre": "senateurs", "groupe_id": "Senat:LR", "groupe_sigle": "LR", "groupe_nom": "Les Républicains", "chambre": "Senat", "legislature": None, "fichier": "groupe-Senat-LR.json"},
    ]

    resultat = generate_all(groupes, profiles_dir=tmp_path / "profiles", out_dir=out_dir)

    assert resultat.echecs == 0
    assert len(fetch_calls) == 2
    assert set(fetch_calls) == {("deputes", "16"), ("senateurs", None)}


def test_generate_all_roster_fetch_failure_reported_as_echec(tmp_path, monkeypatch):
    import requests

    (tmp_path / "profiles").mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        raise requests.RequestException("boom")

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", fake_fetch_full_roster)

    groupes = [
        {"roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR", "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16", "fichier": "groupe-AN-LR-16.json"},
    ]

    resultat = generate_all(groupes, profiles_dir=tmp_path / "profiles", out_dir=out_dir)

    assert resultat.echecs == 1
    assert not (out_dir / "groupe-AN-LR-16.json").exists()
    # Un roster indisponible n'est PAS un échec de génération (#518) : rien n'a
    # été écrit, donc rien n'a été perdu — voir test_generate_group_profiles_codes_sortie.py.
    assert resultat.echecs_generation == []
    assert resultat.groupes_sautes == {("deputes", "16"): ["AN:LR"]}


# ---------------------------------------------------------------------------
# main() : lecture de la config JSON
# ---------------------------------------------------------------------------

def test_main_reads_config_and_generates(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "alice.pivot.json").write_text(json.dumps(_pivot("nosdeputes:alice", "Alice")), encoding="utf-8")
    out_dir = tmp_path / "groupes"

    config_path = tmp_path / "groupes_reels.json"
    config_path.write_text(json.dumps({
        "groupes": [
            {"roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR", "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16", "fichier": "groupe-AN-LR-16.json"},
        ],
        # Depuis #686, une fiche AN se génère avec la position politique que
        # l'Assemblée déclare, lue dans cette table committée. Sans l'entrée,
        # la génération refuse — c'est le comportement voulu, vérifié juste
        # en dessous.
        "correspondance_sigles_an": _correspondance_sigles_an(),
    }), encoding="utf-8")

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        return [m["depute"] for m in _deputes_payload()["deputes"]]

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", fake_fetch_full_roster)

    rc = generate_group_profiles_main([
        "--config", str(config_path),
        "--profiles-dir", str(profiles_dir),
        "--out-dir", str(out_dir),
    ])

    assert rc == 0
    fiche = json.loads((out_dir / "groupe-AN-LR-16.json").read_text(encoding="utf-8"))
    # La posture atterrit dans la fiche AVEC sa preuve — l'organe AN, la chaîne
    # du référentiel verbatim — et non comme un simple mot (#686).
    assert fiche["position_politique"]["position"] == "opposition"
    assert fiche["position_politique"]["organes"] == [
        {"organe_an": "PO800508", "sigle_an": "LR",
         "valeur_source": "Opposition", "position": "opposition"}
    ]
    assert fiche["position_politique"]["source_url"].startswith("https://data.assemblee-nationale.fr/")


def test_main_refuse_une_fiche_an_sans_entree_dans_la_table(tmp_path, monkeypatch, capsys):
    """Le sigle publié ne se rapproche PAS du sigle AN (#686).

    Nos fiches disent `REN` et `LFI`, le référentiel dit `RE` et `LFI-NUPES` :
    un appariement par ressemblance rendrait `None` sur deux fiches sur cinq,
    dont la seule majoritaire. Une entrée manquante doit donc coûter la
    génération de CE groupe, bruyamment et en nommant le couple — jamais une
    fiche publiée avec une posture devinée ou absente.
    """
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "alice.pivot.json").write_text(
        json.dumps(_pivot("nosdeputes:alice", "Alice")), encoding="utf-8"
    )
    out_dir = tmp_path / "groupes"

    config_path = tmp_path / "groupes_reels.json"
    config_path.write_text(json.dumps({
        "groupes": [
            {"roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
             "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
             "fichier": "groupe-AN-LR-16.json"},
        ],
        "correspondance_sigles_an": _correspondance_sigles_an(groupe_sigle="REN"),
    }), encoding="utf-8")

    monkeypatch.setattr(
        "generate_group_profiles.fetch_full_roster",
        lambda chambre, legislature=None, session=None: [
            m["depute"] for m in _deputes_payload()["deputes"]
        ],
    )

    rc = generate_group_profiles_main([
        "--config", str(config_path),
        "--profiles-dir", str(profiles_dir),
        "--out-dir", str(out_dir),
    ])

    assert rc == 1
    assert not (out_dir / "groupe-AN-LR-16.json").exists()
    erreur = capsys.readouterr().err
    assert "'LR'" in erreur and "16" in erreur


def test_main_missing_config_returns_error(tmp_path):
    rc = generate_group_profiles_main(["--config", str(tmp_path / "does-not-exist.json")])
    assert rc == 1


def test_main_empty_groupes_returns_error(tmp_path):
    config_path = tmp_path / "empty.json"
    config_path.write_text(json.dumps({"groupes": []}), encoding="utf-8")
    rc = generate_group_profiles_main(["--config", str(config_path)])
    assert rc == 1


def test_repository_groupes_reels_json_is_valid():
    config_path = Path(__file__).resolve().parents[1] / "raw_data" / "groupes_reels.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(payload.get("groupes"), list)
    assert payload["groupes"]


# ---------------------------------------------------------------------------
# #191 — roster largement couvert (post #190), à l'échelle d'un batch complet
# generate_all(), au-delà des scénarios de faible couverture ci-dessus.
# ---------------------------------------------------------------------------

def test_generate_all_couverture_roster_grande_echelle_quasi_complete(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    n = 50
    n_manquants = 3
    roster_members = []
    for i in range(n):
        slug = f"membre-{i}"
        roster_members.append({"slug": slug, "nom": f"Membre {i}", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None})
        if i < n - n_manquants:
            (profiles_dir / f"{slug}.pivot.json").write_text(json.dumps(_pivot(f"nosdeputes:{slug}", f"Membre {i}")), encoding="utf-8")

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        return roster_members

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", fake_fetch_full_roster)

    groupes = [
        {"roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR", "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16", "fichier": "groupe-AN-LR-16.json"},
    ]

    resultat = generate_all(groupes, profiles_dir=profiles_dir, out_dir=out_dir, validate=True)
    assert resultat.echecs == 0

    lr = json.loads((out_dir / "groupe-AN-LR-16.json").read_text(encoding="utf-8"))
    couverture = lr["meta"]["couverture_roster"]
    assert couverture["roster_total"] == n
    assert couverture["profils_disponibles"] == n - n_manquants
    assert couverture["profils_disponibles"] / couverture["roster_total"] > 0.9
    assert len(lr["membres"]) == n - n_manquants
    assert validate_profil_groupe(lr) == []
