import gzip
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import requests as _requests

# Les modules testés vivent dans src/, à côté du dossier tests/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import candidate_profile
from candidate_profile import (
    _collect_acteur_roles,
    _collect_initiateurs,
    _aggregate_amendements_index,
    _derive_amendement_sort,
    _derive_amendement_sort_legacy,
    _expand_aggregated_amendements_index,
    _extract_contact,
    _parse_syceron_intervention_entry,
    _format_lieu_naissance,
    _format_nom_complet,
    _parse_amendement_entry,
    _parse_amendement_entry_legacy,
    _parse_amendements_zip,
    _parse_question_entry,
    _stade_from_code_acte,
    build_profile,
    fetch_interventions_syceron,
    fetch_questions_officielles,
)
from normalize_profil import normalize_profil


class _FauxRaw:
    """Substitut minimal de `resp.raw` (urllib3) : `read(amt, decode_content=…)`."""

    def __init__(self, payload: bytes):
        self._buf = io.BytesIO(payload)

    def read(self, amt=None, decode_content=False):
        return self._buf.read(amt)


class _FluxFactice:
    """Expose `resp.raw` à partir de `iter_content` sur les réponses factices.

    Depuis #443, `_telecharger_flux` lit le flux via `resp.raw.read()` et non
    `resp.iter_content()` : mesuré, `iter_content` jette le tampon partiel
    d'urllib3 quand la connexion se coupe en cours de lecture, ce qui perdait
    jusqu'à une granularité entière d'octets pourtant reçus. Les doubles de test
    n'ont pas à connaître ce détail : ils continuent de décrire leur charge utile
    via `iter_content`, ce mixin en dérive un `raw` minimal.
    """

    headers: dict = {}

    @property
    def raw(self):
        if not hasattr(self, "_faux_raw"):
            self._faux_raw = _FauxRaw(b"".join(self.iter_content()))
        return self._faux_raw


def _budget_appels_reseau_echec_total() -> int:
    """Nombre total de requêtes d'un téléchargement d'archive qui échoue de bout
    en bout, depuis #443 : par cycle, `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`
    tentatives par plage puis **un** GET séquentiel de repli, et
    `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES` cycles avant d'abandonner en signalant
    la source indisponible. Exprimé à partir des constantes plutôt qu'en dur :
    ce qui doit rester vrai est que le budget réseau est borné, pas sa valeur du
    jour."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AMENDEMENTS_SOURCE_STALL_MAX_CYCLES,
    )

    return (AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS + 1) * AMENDEMENTS_SOURCE_STALL_MAX_CYCLES


def _budget_attentes_echec_total() -> int:
    """Attentes correspondantes : le backoff entre deux tentatives de plage d'un
    même cycle, plus l'attente entre deux cycles — aucune après la dernière,
    déjà en échec définitif."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AMENDEMENTS_SOURCE_STALL_MAX_CYCLES,
    )

    backoffs = (AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS - 1) * AMENDEMENTS_SOURCE_STALL_MAX_CYCLES
    return backoffs + AMENDEMENTS_SOURCE_STALL_MAX_CYCLES - 1


@pytest.fixture(autouse=True)
def _purge_memo_store_amendements():
    """Le mémo du store amendements (#392) est indexé par législature seule,
    pas par `AMENDEMENTS_CACHE_DIR` — sûr en production (la constante n'y est
    jamais réassignée), mais piégeux en test où chaque cas patche ce répertoire
    vers un `tmp_path` différent : sans purge, un test lirait le store mémoïsé
    du test précédent. Même piège que celui qui avait fait reverter la
    mémoïsation de #377."""
    from candidate_profile import _clear_amendements_store_memo
    _clear_amendements_store_memo()
    yield
    _clear_amendements_store_memo()


@pytest.fixture(autouse=True)
def _purge_memo_index_acteurs_historique():
    """Mémo intra-process des index dérivés du zip AMO30 (#467).

    Il est indexé par CHEMIN d'index, donc déjà insensible au patch de
    `ACTEURS_HISTORIQUE_CACHE_DIR` vers un `tmp_path` différent par test. Cette
    purge est la ceinture de la bretelle : un cas qui réutiliserait le même
    `tmp_path` en changeant le contenu de l'index lirait sinon la version
    mémoïsée. Même précaution que `_purge_memo_store_amendements`, et même
    leçon que la mémoïsation revertée de #377."""
    from candidate_profile import _clear_acteurs_historique_index_memo
    _clear_acteurs_historique_index_memo()
    yield
    _clear_acteurs_historique_index_memo()


@pytest.fixture(autouse=True)
def _reset_amendements_failed_legislatures_cache():
    """Le cache d'échec inter-candidats (`_amendements_failed_legislatures`, issue
    #239) est un état module-level : sans réinitialisation, un test qui fait
    échouer le téléchargement d'une législature pollue tous les tests suivants
    utilisant la même législature (typiquement "17")."""
    from candidate_profile import _amendements_failed_legislatures

    _amendements_failed_legislatures.clear()
    yield
    _amendements_failed_legislatures.clear()


# ---------------------------------------------------------------------------
# Ce qui a disparu d'ici avec la source (#529, lot 5)
#
# `DummyResponse` et les onze tests qui l'entouraient décrivaient la chaîne
# d'interventions scrapées de NosDéputés : `_classify_intervention` (l'orateur
# lu dans un `div.perso`), `_extract_speaker_identity_from_html`,
# `fetch_seance_context` (le sujet et les mots-clés lus dans le HTML d'une page
# de séance), `_classify_intervention_format` et son seuil de 15 mots,
# `_extract_mandats` / `_groupe_label` (les responsabilités lues dans un profil
# brut NosDéputés) et `fetch_all_intervention_results_from_domains`.
#
# Ils sont supprimés avec le code, pas conservés « au cas où » : un test qui
# fige un comportement qui n'existe plus rend son retour indolore, et c'est
# exactement ce que #510 a payé avec ses deux fixtures inventées. Ce que
# `_extract_mandats` garantissait — l'estampille de chambre sur le mandat
# électif (#492) — est repris à son nouvel emplacement dans
# `tests/test_chambre_par_mandat.py`.
#
# `test_build_profile_reports_empty_api_payloads` est en revanche conservé,
# réécrit sur la seule source restante : c'est lui qui vérifie qu'un slug
# introuvable sort avec des warnings plutôt qu'avec un profil d'apparence
# normale. Voir docs/decisions/retrait-nosdeputes-529.md.
# ---------------------------------------------------------------------------

def test_build_profile_reports_empty_api_payloads():
    """Slug absent du référentiel AN : aucune section n'est fabriquée, et le
    profil DIT pourquoi. Le repli NosDéputés qui pouvait encore rendre une
    identité ici est parti avec la source (#529) — ce chemin est donc devenu
    le seul, et son silence serait un constat faux (AGENTS.md §2.5)."""
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=(None, None)),
    ):
        profile = build_profile("deputes", "slug-inexistant")

    assert profile["identite"] is None
    assert profile["mandats"] == []
    assert profile["votes"] == []
    assert profile["source"] is None, (
        "sans acteur résolu, `source` doit rester nulle : une URL de fiche "
        "inventée serait une source qui ne mène nulle part (règle 2)"
    )
    assert any("identité" in warning for warning in profile["meta"]["warnings"])
    assert any("vote" in warning for warning in profile["meta"]["warnings"])


def test_derive_amendement_sort_maps_discute_states():
    assert _derive_amendement_sort("Discuté", "Adopté") == ("adopté", None)
    assert _derive_amendement_sort("Discuté", "Rejeté") == ("rejeté", None)
    assert _derive_amendement_sort("Discuté", "Tombé") == ("tombé", None)
    assert _derive_amendement_sort("Discuté", "Non soutenu") == ("non_soutenu", None)
    assert _derive_amendement_sort("Retiré", "Retiré avant publication") == ("retiré", None)


def test_derive_amendement_sort_maps_irrecevabilite_by_base_juridique():
    assert _derive_amendement_sort("Irrecevable 40", "Charge") == ("irrecevable", "art. 40")
    assert _derive_amendement_sort("Irrecevable", "Cavalier (45)") == ("irrecevable", "art. 45")


def test_derive_amendement_sort_unknown_or_pending_returns_none():
    assert _derive_amendement_sort("En traitement", None) == (None, None)
    assert _derive_amendement_sort("A discuter", None) == (None, None)


def test_parse_amendement_entry_keeps_primary_author_and_cosignataires():
    raw = {
        "amendement": {
            "identification": {"numeroLong": "AS1"},
            "texteLegislatifRef": "PIONANR5L17B0904",
            "signataires": {
                "auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"},
                "cosignataires": {"acteurRef": ["PA842001", "PA793182"]},
            },
            "cycleDeVie": {
                "dateDepot": "2025-02-17",
                "etatDesTraitements": {
                    "etat": {"libelle": "Discuté"},
                    "sousEtat": {"libelle": "Adopté"},
                },
            },
        }
    }

    result = _parse_amendement_entry(raw)

    assert result is not None
    by_acteur = {acteur_ref: record for acteur_ref, record in result}

    assert set(by_acteur.keys()) == {"PA1567", "PA842001", "PA793182"}

    auteur = by_acteur["PA1567"]
    assert auteur["role_signataire"] == "auteur_principal"
    assert auteur["premier_signataire"] == "an:PA1567"
    assert auteur["numero"] == "AS1"
    assert auteur["texte_vise"] == "PIONANR5L17B0904"
    assert auteur["type_deposant"] == "depute"
    assert auteur["date"] == "2025-02-17"
    assert auteur["sort"] == "adopté"
    assert auteur["co_signataires"] == ["an:PA842001", "an:PA793182"]

    cosign = by_acteur["PA842001"]
    assert cosign["role_signataire"] == "cosignataire"
    assert cosign["premier_signataire"] == "an:PA1567"


def test_parse_amendement_entry_returns_none_without_acteur_ref():
    raw = {"amendement": {"signataires": {"auteur": {}}}}
    assert _parse_amendement_entry(raw) is None


def test_parse_amendement_entry_keeps_cosignataire_from_nested_acteur_dict():
    raw = {
        "amendement": {
            "identification": {"numeroLong": "AS2"},
            "signataires": {
                "auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"},
                "cosignataires": {"acteur": {"acteurRef": "PA842001"}},
            },
            "cycleDeVie": {"dateDepot": "2025-02-18"},
        }
    }

    result = _parse_amendement_entry(raw)

    assert result is not None
    assert {acteur_ref for acteur_ref, _ in result} == {"PA1567", "PA842001"}
    by_acteur = {acteur_ref: record for acteur_ref, record in result}
    assert by_acteur["PA842001"]["role_signataire"] == "cosignataire"
    assert by_acteur["PA842001"]["co_signataires"] == ["an:PA842001"]


def test_parse_amendement_entry_extrait_luid_pour_chaque_signataire():
    """L'`uid` AN est extrait et porté par CHAQUE signataire : c'est la seule
    clé qui identifie l'amendement de façon unique (le `numeroLong` repart à
    chaque texte, voir `_aggregate_amendements_index`)."""
    raw = {
        "amendement": {
            "uid": "AMANR5L17PO59047BTC1376P0D1N000012",
            "identification": {"numeroLong": "AE12"},
            "texteLegislatifRef": "PNREANR5L17BTC1376",
            "signataires": {
                "auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"},
                "cosignataires": {"acteur": {"acteurRef": "PA842001"}},
            },
            "cycleDeVie": {"dateDepot": "2025-02-18"},
        }
    }

    result = _parse_amendement_entry(raw)

    assert result is not None
    by_acteur = {acteur_ref: record for acteur_ref, record in result}
    assert by_acteur["PA1567"]["uid"] == "AMANR5L17PO59047BTC1376P0D1N000012"
    assert by_acteur["PA842001"]["uid"] == "AMANR5L17PO59047BTC1376P0D1N000012"
    # Le numéro reste collecté : il est affichable, simplement pas identifiant.
    assert by_acteur["PA1567"]["numero"] == "AE12"


def test_parse_amendement_entry_legacy_extrait_luid():
    """Le schéma legacy de la XIVe porte lui aussi un `uid` sur chaque
    amendement (vérifié sur l'archive réelle : 167 420 amendements, 167 420
    uid distincts, mais seulement 22 159 `numeroLong` distincts)."""
    raw = {
        "textesEtAmendements": {
            "texteleg": {
                "refTexteLegislatif": "PIONANR5L14B0013",
                "amendements": {
                    "amendement": {
                        "uid": "AMANR5L14SEA644420B0013P0D1N7",
                        "identifiant": {"numero": "7"},
                        "numeroLong": "7 (Rect)",
                        "etat": "Discuté",
                        "sort": {"sortEnSeance": "Adopté"},
                        "dateDepot": "2013-01-01",
                        "signataires": {
                            "auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"},
                            "cosignataires": {"acteur": {"acteurRef": "PA842001"}},
                        },
                    }
                },
            }
        }
    }

    result = _parse_amendement_entry_legacy(raw)

    assert result is not None
    by_acteur = {acteur_ref: record for acteur_ref, record in result}
    assert by_acteur["PA1567"]["uid"] == "AMANR5L14SEA644420B0013P0D1N7"
    assert by_acteur["PA842001"]["uid"] == "AMANR5L14SEA644420B0013P0D1N7"
    assert by_acteur["PA1567"]["numero"] == "7 (Rect)"


def test_parse_amendement_entry_keeps_cosignataires_from_nested_acteur_list():
    raw = {
        "amendement": {
            "identification": {"numeroLong": "AS3"},
            "signataires": {
                "auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"},
                "cosignataires": {
                    "acteur": [
                        {"acteurRef": "PA842001"},
                        {"acteurRef": "PA793182"},
                    ]
                },
            },
            "cycleDeVie": {"dateDepot": "2025-02-19"},
        }
    }

    result = _parse_amendement_entry(raw)

    assert result is not None
    assert {acteur_ref for acteur_ref, _ in result} == {"PA1567", "PA842001", "PA793182"}
    by_acteur = {acteur_ref: record for acteur_ref, record in result}
    assert by_acteur["PA1567"]["co_signataires"] == ["an:PA842001", "an:PA793182"]
    assert by_acteur["PA793182"]["role_signataire"] == "cosignataire"


# ---------------------------------------------------------------------------
# Tests pour le schéma legacy légis 14 (`_parse_amendement_entry_legacy`,
# `_derive_amendement_sort_legacy`, détection de schéma dans
# `_parse_amendements_zip`) — issue #299.
# ---------------------------------------------------------------------------

def test_derive_amendement_sort_legacy_maps_sort_en_seance():
    assert _derive_amendement_sort_legacy("Discuté", "Tombé") == ("tombé", None)
    assert _derive_amendement_sort_legacy("Discuté", "Adopté") == ("adopté", None)
    assert _derive_amendement_sort_legacy("Discuté", "Rejeté") == ("rejeté", None)
    assert _derive_amendement_sort_legacy("Discuté", "Non soutenu") == ("non_soutenu", None)
    assert _derive_amendement_sort_legacy("Retiré", "Retiré") == ("retiré", None)


def test_derive_amendement_sort_legacy_maps_irrecevabilite_by_base_juridique():
    assert _derive_amendement_sort_legacy("Irrecevable 40", None) == ("irrecevable", "art. 40")
    assert _derive_amendement_sort_legacy("Irrecevable", None) == ("irrecevable", "art. 45")


def test_derive_amendement_sort_legacy_unknown_returns_none():
    assert _derive_amendement_sort_legacy("En traitement", None) == (None, None)


def _legacy_amendement_raw(**overrides):
    base = {
        # numeroLong ("7 (Rect)") est à la racine de l'amendement sur
        # l'archive réelle, pas imbriqué sous identifiant (qui ne porte que
        # le numéro nu "7") — vérifié le 15/08/2026, corrigé après un premier
        # essai qui lisait par erreur depuis `identifiant` et perdait
        # silencieusement le suffixe de rectification.
        "numeroLong": "7 (Rect)",
        "identifiant": {"numero": "7"},
        "dateDepot": "2014-02-14",
        "etat": "Discuté",
        "sort": {"sortEnSeance": "Tombé"},
        "signataires": {
            "auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"},
            "cosignataires": {"acteurRef": ["PA842001", "PA793182"]},
        },
    }
    base.update(overrides)
    return base


def test_parse_amendement_entry_legacy_maps_fields_and_cosignataires():
    raw = {
        "textesEtAmendements": {
            "texteleg": [
                {
                    "refTexteLegislatif": "PIONANR5L14B0013",
                    "amendements": {"amendement": [_legacy_amendement_raw()]},
                }
            ]
        }
    }

    result = _parse_amendement_entry_legacy(raw)

    assert result is not None
    by_acteur = {acteur_ref: record for acteur_ref, record in result}
    assert set(by_acteur.keys()) == {"PA1567", "PA842001", "PA793182"}

    auteur = by_acteur["PA1567"]
    assert auteur["role_signataire"] == "auteur_principal"
    assert auteur["premier_signataire"] == "an:PA1567"
    assert auteur["numero"] == "7 (Rect)"
    assert auteur["texte_vise"] == "PIONANR5L14B0013"
    assert auteur["type_deposant"] == "depute"
    assert auteur["date"] == "2014-02-14"
    assert auteur["sort"] == "tombé"
    assert auteur["base_juridique_irrecevabilite"] is None
    assert auteur["co_signataires"] == ["an:PA842001", "an:PA793182"]

    cosign = by_acteur["PA842001"]
    assert cosign["role_signataire"] == "cosignataire"
    assert cosign["premier_signataire"] == "an:PA1567"


def test_parse_amendement_entry_legacy_maps_unaccented_type_auteur():
    """L'archive réelle de la 14e législature porte `typeAuteur: "Depute"`
    (sans accent), contrairement au schéma moderne (`"Député"`) — vérifié le
    15/08/2026. `_AMENDEMENT_TYPE_AUTEUR_MAP` doit reconnaître les deux
    formes plutôt que de laisser `type_deposant` à `None` pour toute la 14e."""
    raw = {
        "textesEtAmendements": {
            "texteleg": [
                {
                    "refTexteLegislatif": "PIONANR5L14B0013",
                    "amendements": {
                        "amendement": [
                            _legacy_amendement_raw(
                                signataires={
                                    "auteur": {"typeAuteur": "Depute", "acteurRef": "PA1567"},
                                    "cosignataires": {},
                                }
                            )
                        ]
                    },
                }
            ]
        }
    }

    result = _parse_amendement_entry_legacy(raw)

    assert result is not None
    by_acteur = {acteur_ref: record for acteur_ref, record in result}
    assert by_acteur["PA1567"]["type_deposant"] == "depute"


def test_parse_amendement_entry_legacy_handles_singular_amendement_dict():
    """Un texteleg à un seul amendement expose `amendement` comme dict plutôt
    que liste (même écueil que `cosignataires.acteur` ailleurs dans le code)."""
    raw = {
        "textesEtAmendements": {
            "texteleg": {
                "refTexteLegislatif": "PIONANR5L14B0013",
                "amendements": {"amendement": _legacy_amendement_raw()},
            }
        }
    }

    result = _parse_amendement_entry_legacy(raw)

    assert result is not None
    assert {acteur_ref for acteur_ref, _ in result} == {"PA1567", "PA842001", "PA793182"}


def test_parse_amendement_entry_legacy_returns_none_without_root_key():
    assert _parse_amendement_entry_legacy({"amendement": {}}) is None


def test_parse_amendement_entry_legacy_irrecevable_sets_base_juridique():
    raw = {
        "textesEtAmendements": {
            "texteleg": [
                {
                    "refTexteLegislatif": "PIONANR5L14B0013",
                    "amendements": {
                        "amendement": [
                            _legacy_amendement_raw(etat="Irrecevable 40", sort={})
                        ]
                    },
                }
            ]
        }
    }

    result = _parse_amendement_entry_legacy(raw)

    assert result is not None
    auteur = dict(result)["PA1567"]
    assert auteur["sort"] == "irrecevable"
    assert auteur["base_juridique_irrecevabilite"] == "art. 40"


def _make_amendements_zip(tmp_path, entries: dict):
    import zipfile as zipfile_module

    zip_path = tmp_path / "amendements.zip"
    with zipfile_module.ZipFile(zip_path, "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, json.dumps(content))
    return zip_path


def test_parse_amendements_zip_dispatches_current_schema(tmp_path):
    raw = {
        "amendement": {
            "identification": {"numeroLong": "AS1"},
            "texteLegislatifRef": "PIONANR5L17B0904",
            "signataires": {"auteur": {"typeAuteur": "Député", "acteurRef": "PA1567"}},
            "cycleDeVie": {"dateDepot": "2025-02-17"},
        }
    }
    zip_path = _make_amendements_zip(tmp_path, {"AMANR5L17PO001.json": raw})

    index = _parse_amendements_zip(zip_path)

    assert set(index.keys()) == {"PA1567"}
    assert index["PA1567"][0]["numero"] == "AS1"


def test_parse_amendements_zip_dispatches_legacy_schema(tmp_path):
    raw = {
        "textesEtAmendements": {
            "texteleg": [
                {
                    "refTexteLegislatif": "PIONANR5L14B0013",
                    "amendements": {"amendement": [_legacy_amendement_raw()]},
                }
            ]
        }
    }
    zip_path = _make_amendements_zip(tmp_path, {"Amendements_XIV.json": raw})

    index = _parse_amendements_zip(zip_path)

    assert set(index.keys()) == {"PA1567", "PA842001", "PA793182"}
    assert index["PA1567"][0]["sort"] == "tombé"


def test_parse_amendements_zip_warns_explicitly_on_unknown_schema(tmp_path, capsys):
    zip_path = _make_amendements_zip(tmp_path, {"unknown.json": {"somethingElse": {}}})

    index = _parse_amendements_zip(zip_path)

    assert index == {}
    captured = capsys.readouterr()
    assert "format inconnu" in captured.err
    assert "unknown.json" in captured.err


# ---------------------------------------------------------------------------
# Tests pour `_aggregate_amendements_index` / `_expand_aggregated_amendements_index`
# (issue #268) : le format brut d'`_parse_amendements_zip` duplique
# l'intégralité de chaque amendement (dont `co_signataires`) une fois par
# signataire — mesuré à 3,86 Go décompressés pour la législature 16,
# impossible à committer. `_aggregate_amendements_index` compacte ce résultat
# (chaque amendement une seule fois, référencé par son `uid` AN) avant écriture
# par `build_amendements_index_figees.py` ; `_expand_aggregated_amendements_index`
# est l'inverse, utilisé par `_load_frozen_amendement_index` pour reconstruire
# la forme plate attendue par le reste du pipeline.
#
# La clé est l'`uid`, jamais le `numero` (corrigé le 18/08/2026, voir
# docs/decisions/amendements-cle-uid.md) : le `numeroLong` repart à
# chaque texte, et keyer par lui écrasait 74,9 % des amendements de la
# législature 17.
# ---------------------------------------------------------------------------

def test_aggregate_amendements_index_deduplicates_shared_amendment():
    """Un amendement à 2 cosignataires (3 entrées dupliquées en entrée) ne doit
    apparaître qu'une seule fois dans `amendements`, sous sa clé `uid` ; les
    3 signataires ne conservent chacun qu'une référence légère."""
    shared_record = {
        "uid": "AMANR5L17PO59047B0904P0D1N000001",
        "texte_vise": "PIONANR5L17B0904",
        "sort": None,
        "base_juridique_irrecevabilite": None,
        "premier_signataire": "an:PA1567",
        "co_signataires": ["an:PA842001", "an:PA793182"],
        "type_deposant": "depute",
        "date": "2025-02-17",
        "numero": "AS1",
        "source_url": None,
    }
    index = {
        "PA1567": [{**shared_record, "role_signataire": "auteur_principal"}],
        "PA842001": [{**shared_record, "role_signataire": "cosignataire"}],
        "PA793182": [{**shared_record, "role_signataire": "cosignataire"}],
    }

    amendements, index_par_acteur = _aggregate_amendements_index(index)

    uid = shared_record["uid"]
    assert list(amendements.keys()) == [uid]
    assert amendements[uid] == shared_record
    assert "role_signataire" not in amendements[uid]
    assert index_par_acteur == {
        "PA1567": [{"uid": uid, "role_signataire": "auteur_principal"}],
        "PA842001": [{"uid": uid, "role_signataire": "cosignataire"}],
        "PA793182": [{"uid": uid, "role_signataire": "cosignataire"}],
    }


def test_aggregate_amendements_index_ne_confond_pas_deux_amendements_de_meme_numero():
    """Régression du 18/08/2026 : deux amendements DIFFÉRENTS portant le même
    `numero` sur des textes différents doivent rester deux amendements.

    Le `numeroLong` de l'AN repart à chaque texte : mesuré sur l'archive de la
    législature 17, 121 805 amendements pour 30 616 `numeroLong` distincts
    (« AE12 » est porté par 7 textes sans rapport). Le store keyé par `numero`
    n'en gardait qu'un et faisait résoudre les références de l'autre vers lui —
    40,5 % des paires (acteur, amendement) pointaient vers un amendement qui
    n'était pas le leur. Un fait faux, pas seulement une perte de volume.
    """
    premier = {
        "uid": "AMANR5L17PO59047BTC1376P0D1N000012",
        "texte_vise": "PNREANR5L17BTC1376",
        "numero": "AE12",
        "date": "2025-01-10",
        "premier_signataire": "an:PA1567",
        "co_signataires": [],
    }
    second = {
        "uid": "AMANR5L17PO59047B0118P0D1N000012",
        "texte_vise": "PIONANR5L17B0118",
        "numero": "AE12",  # même numéro, autre texte, autre amendement
        "date": "2025-03-04",
        "premier_signataire": "an:PA842001",
        "co_signataires": [],
    }
    index = {
        "PA1567": [{**premier, "role_signataire": "auteur_principal"}],
        "PA842001": [{**second, "role_signataire": "auteur_principal"}],
    }

    amendements, index_par_acteur = _aggregate_amendements_index(index)

    assert len(amendements) == 2, "deux amendements distincts ne doivent pas fusionner"
    assert amendements[premier["uid"]]["texte_vise"] == "PNREANR5L17BTC1376"
    assert amendements[second["uid"]]["texte_vise"] == "PIONANR5L17B0118"

    # Et chaque signataire retrouve le SIEN, pas celui de l'autre.
    reconstruit = _expand_aggregated_amendements_index(amendements, index_par_acteur)
    assert reconstruit["PA1567"][0]["texte_vise"] == "PNREANR5L17BTC1376"
    assert reconstruit["PA1567"][0]["date"] == "2025-01-10"
    assert reconstruit["PA842001"][0]["texte_vise"] == "PIONANR5L17B0118"
    assert reconstruit["PA842001"][0]["date"] == "2025-03-04"


def test_aggregate_amendements_index_assigns_synthetic_key_without_dropping_records_missing_uid():
    """Un enregistrement sans `uid` (non observé : les archives XIV à XVII en
    portent un sur chaque amendement) ne doit jamais être perdu ni fusionné à
    tort avec un autre : il reçoit une clé synthétique qui lui est propre."""
    index = {
        "PA1": [{"uid": None, "texte_vise": "A"}],
        "PA2": [{"uid": None, "texte_vise": "B"}],
    }

    amendements, index_par_acteur = _aggregate_amendements_index(index)

    assert len(amendements) == 2
    assert {v["texte_vise"] for v in amendements.values()} == {"A", "B"}
    assert len(index_par_acteur["PA1"]) == 1
    assert len(index_par_acteur["PA2"]) == 1


def test_expand_aggregated_amendements_index_reconstructs_flat_form():
    uid = "AMANR5L17PO59047B0904P0D1N000001"
    amendements = {
        uid: {
            "uid": uid,
            "texte_vise": "PIONANR5L17B0904",
            "premier_signataire": "an:PA1567",
            "co_signataires": ["an:PA842001"],
            "numero": "AS1",
        }
    }
    index_par_acteur = {
        "PA1567": [{"uid": uid, "role_signataire": "auteur_principal"}],
        "PA842001": [{"uid": uid, "role_signataire": "cosignataire"}],
    }

    expanded = _expand_aggregated_amendements_index(amendements, index_par_acteur)

    assert expanded == {
        "PA1567": [{**amendements[uid], "role_signataire": "auteur_principal"}],
        "PA842001": [{**amendements[uid], "role_signataire": "cosignataire"}],
    }


def test_expand_aggregated_amendements_index_ignores_dangling_reference():
    """Une référence dont l'`uid` est absent de `amendements` (ne devrait
    pas arriver, les deux fichiers étant committés ensemble) est ignorée sans
    lever."""
    expanded = _expand_aggregated_amendements_index(
        {}, {"PA1": [{"uid": "INTROUVABLE", "role_signataire": "auteur_principal"}]}
    )
    assert expanded == {"PA1": []}


def test_aggregate_then_expand_amendements_index_round_trips():
    """L'aller-retour agrégation -> expansion doit reproduire exactement
    l'index plat d'origine — invariant central de la compaction committée."""
    shared_record = {
        "uid": "AMANR5L17PO59047B0904P0D1N000001",
        "texte_vise": "PIONANR5L17B0904",
        "premier_signataire": "an:PA1567",
        "co_signataires": ["an:PA842001"],
        "numero": "AS1",
    }
    original = {
        "PA1567": [{**shared_record, "role_signataire": "auteur_principal"}],
        "PA842001": [{**shared_record, "role_signataire": "cosignataire"}],
    }

    amendements, index_par_acteur = _aggregate_amendements_index(original)
    roundtripped = _expand_aggregated_amendements_index(amendements, index_par_acteur)

    assert roundtripped == original


# `_collect_texte_codes` et ses deux tests ont été retirés avec
# `_build_texte_titre_index` (#639, rang 3) : le collecteur n'existait que pour
# elle, et elle n'existait que pour écraser le `texte_vise` sourcé d'un
# amendement par le titre de son dossier. Le rattachement au dossier se fait
# désormais d'uid à uid (`textes_dossiers_an.py`).


def test_format_lieu_naissance_france_avec_departement():
    assert _format_lieu_naissance("Nantes", "Loire-Atlantique", "France") == "Nantes (Loire-Atlantique)"


def test_format_lieu_naissance_etranger_prefere_le_pays():
    assert _format_lieu_naissance("Alger", None, "Algérie") == "Alger (Algérie)"


def test_format_lieu_naissance_ville_seule():
    assert _format_lieu_naissance("Nantes", None, None) == "Nantes"


def test_format_lieu_naissance_tout_absent():
    assert _format_lieu_naissance(None, None, None) is None


def test_format_nom_complet_prenom_et_nom():
    assert _format_nom_complet("Antoine", "Golliot") == "Antoine Golliot"


def test_format_nom_complet_nom_seul():
    assert _format_nom_complet(None, "Golliot") == "Golliot"


def test_format_nom_complet_tout_absent():
    assert _format_nom_complet(None, None) is None


def test_extract_contact_types_connus():
    adresses = [
        {"typeLibelle": "Adresse officielle", "intitule": "Assemblée nationale,"},
        {"typeLibelle": "Mèl", "valElec": "antoine.golliot@assemblee-nationale.fr"},
        {"typeLibelle": "Twitter", "valElec": "@AGolliot"},
        {"typeLibelle": "Facebook", "valElec": "Antoine Golliot"},
        {"typeLibelle": "Site internet", "valElec": "www.antoine-golliot.fr"},
        {"typeLibelle": "Instagram", "valElec": "antoine.golliot"},
    ]
    assert _extract_contact(adresses) == {
        "email": "antoine.golliot@assemblee-nationale.fr",
        "twitter": "@AGolliot",
        "facebook": "Antoine Golliot",
        "site_web": "www.antoine-golliot.fr",
    }


def test_extract_contact_aucune_adresse():
    assert _extract_contact([]) == {
        "email": None,
        "twitter": None,
        "facebook": None,
        "site_web": None,
    }


def test_stade_from_code_acte_depot():
    assert _stade_from_code_acte("AN1-DEPOT", None) == "depose"


def test_stade_from_code_acte_commission():
    assert _stade_from_code_acte("AN1-COM-FOND-RAPPORT", None) == "examine_commission"


def test_stade_from_code_acte_debats_seance():
    assert _stade_from_code_acte("AN1-DEBATS-SEANCE", None) == "discute_seance"


def test_stade_from_code_acte_decision_adoptee():
    assert _stade_from_code_acte("AN1-DEBATS-DEC", "adopté") == "adopte"


def test_stade_from_code_acte_decision_rejetee_reste_discute_seance():
    assert _stade_from_code_acte("AN1-DEBATS-DEC", "rejetée") == "discute_seance"


def test_stade_from_code_acte_promulgation():
    assert _stade_from_code_acte("PROM-PUB", None) == "promulgue"


def test_stade_from_code_acte_code_inconnu():
    assert _stade_from_code_acte("CODE-INCONNU", None) is None


def test_collect_initiateurs_acteur_unique():
    acteur_roles: dict = {}
    dossier = {"initiateur": {"acteurs": {"acteur": {"acteurRef": "PA1"}}}}
    _collect_initiateurs(dossier, acteur_roles)
    assert acteur_roles == {"PA1": ("auteur", None)}


def test_collect_initiateurs_liste_acteurs():
    acteur_roles: dict = {}
    dossier = {"initiateur": {"acteurs": {"acteur": [{"acteurRef": "PA1"}, {"acteurRef": "PA2"}]}}}
    _collect_initiateurs(dossier, acteur_roles)
    assert acteur_roles == {"PA1": ("auteur", None), "PA2": ("auteur", None)}


def test_collect_acteur_roles_rapporteur_unique_et_dates():
    dossier = {
        "legislature": "17",
        "initiateur": None,
        "actesLegislatifs": {
            "acteLegislatif": {
                "codeActe": "AN1-COM-FOND-NOMIN",
                "dateActe": "2024-01-10T00:00:00.000+01:00",
                "rapporteurs": {"rapporteur": {"acteurRef": "PA1", "typeRapporteur": "rapporteur"}},
            }
        },
    }
    acteur_roles, stade, date_min, date_max = _collect_acteur_roles(dossier)
    assert acteur_roles == {"PA1": ("rapporteur", "rapporteur_fond")}
    # #997, option B — la NOMINATION d'un rapporteur dit que la commission
    # s'organise, pas qu'elle a examiné : elle ne donne donc plus de stade.
    # C'était l'option A, écartée. Le sujet de ce test est le rôle collecté,
    # que la nomination établit bien, et qui est inchangé.
    assert stade is None
    assert date_min == date_max == "2024-01-10"


def test_collect_acteur_roles_co_rapporteurs():
    dossier = {
        "legislature": "17",
        "initiateur": None,
        "actesLegislatifs": {
            "acteLegislatif": {
                "codeActe": "AN1-COM-FOND-NOMIN",
                "dateActe": "2024-01-10T00:00:00.000+01:00",
                "rapporteurs": {"rapporteur": [
                    {"acteurRef": "PA1", "typeRapporteur": "rapporteur pour avis"},
                    {"acteurRef": "PA2", "typeRapporteur": "rapporteur pour avis"},
                ]},
            }
        },
    }
    acteur_roles, stade, date_min, date_max = _collect_acteur_roles(dossier)
    assert acteur_roles == {
        "PA1": ("co-rapporteur", "rapporteur_avis"),
        "PA2": ("co-rapporteur", "rapporteur_avis"),
    }


def test_collect_acteur_roles_stade_le_plus_avance_retenu():
    dossier = {
        "legislature": "17",
        "initiateur": {"acteurs": {"acteur": {"acteurRef": "PA1"}}},
        "actesLegislatifs": {
            "acteLegislatif": [
                {"codeActe": "AN1-DEPOT", "dateActe": "2024-01-01T00:00:00.000+01:00"},
                {"codeActe": "PROM-PUB", "dateActe": "2024-06-01T00:00:00.000+02:00"},
            ]
        },
    }
    acteur_roles, stade, date_min, date_max = _collect_acteur_roles(dossier)
    assert acteur_roles == {"PA1": ("auteur", None)}
    assert stade == "promulgue"
    assert date_min == "2024-01-01"
    assert date_max == "2024-06-01"


# ---------------------------------------------------------------------------
# _parse_question_entry
# ---------------------------------------------------------------------------

def _make_question_data(
    xsi_type="QuestionEcrite_Type",
    acteur_ref="PA1567",
    uid="QANR5L17QE12345",
    analyse="Budget 2025",
    texte="Monsieur le ministre, ...",
    date_jo="2025-01-15",
    reponse_texte=None,
    date_reponse=None,
    ministere="Ministère de l'Économie",
    groupe_sigle="LFI-NUPES",
):
    data: dict = {
        "question": {
            "@xsi:type": xsi_type,
            "uid": uid,
            "auteur": {
                "identite": {"acteurRef": acteur_ref},
                "groupe": {"abrege": groupe_sigle, "developpe": "La France Insoumise"},
            },
            "minInt": {"developpe": ministere},
            "indexationAN": {"analyses": {"analyse": analyse}},
            "textesQuestion": {
                "texteQuestion": {"texte": texte, "infoJO": {"dateJO": date_jo}}
            },
        }
    }
    if reponse_texte is not None:
        data["question"]["textesReponse"] = {
            "texteReponse": {"texte": reponse_texte, "infoJO": {"dateJO": date_reponse}}
        }
    return data


def test_parse_question_entry_basic_qe():
    data = _make_question_data()
    result = _parse_question_entry(data, "QE")
    assert result is not None
    acteur_ref, record = result
    assert acteur_ref == "PA1567"
    assert record["uid"] == "QANR5L17QE12345"
    assert record["sous_type"] == "QE"
    assert record["sujet"] == "Budget 2025"
    assert record["texte"] == "Monsieur le ministre, ..."
    assert record["date"] == "2025-01-15"
    assert record["reponse"] is None
    assert record["date_reponse"] is None
    assert record["ministere"] == "Ministère de l'Économie"
    assert record["groupe_sigle"] == "LFI-NUPES"


def test_parse_question_entry_with_response():
    data = _make_question_data(
        reponse_texte="La réponse est ...",
        date_reponse="2025-03-10",
    )
    result = _parse_question_entry(data, "QG")
    assert result is not None
    _, record = result
    assert record["sous_type"] == "QG"
    assert record["reponse"] == "La réponse est ..."
    assert record["date_reponse"] == "2025-03-10"


def test_parse_question_entry_returns_none_without_acteur_ref():
    data = {"question": {"uid": "QANR5L17QE99999", "auteur": {"identite": {}}}}
    assert _parse_question_entry(data, "QE") is None


def test_parse_question_entry_returns_none_without_question_key():
    assert _parse_question_entry({}, "QE") is None
    assert _parse_question_entry({"autre": {}}, "QE") is None


def test_parse_question_entry_analyse_as_list():
    data = _make_question_data(analyse=["Thème A", "Thème B"])
    result = _parse_question_entry(data, "QOSD")
    assert result is not None
    _, record = result
    assert record["sujet"] == "Thème A ; Thème B"


def test_parse_question_entry_texte_question_as_list_takes_last():
    data = {
        "question": {
            "uid": "QANR5L17QE1",
            "auteur": {"identite": {"acteurRef": "PA1"}, "groupe": {}},
            "minInt": {},
            "indexationAN": {"analyses": {"analyse": "Sujet"}},
            "textesQuestion": {
                "texteQuestion": [
                    {"texte": "Version initiale", "infoJO": {"dateJO": "2025-01-01"}},
                    {"texte": "Version révisée", "infoJO": {"dateJO": "2025-02-01"}},
                ]
            },
        }
    }
    result = _parse_question_entry(data, "QE")
    assert result is not None
    _, record = result
    assert record["texte"] == "Version révisée"
    assert record["date"] == "2025-02-01"


# ---------------------------------------------------------------------------
# fetch_questions_officielles
# ---------------------------------------------------------------------------

def test_fetch_questions_officielles_returns_empty_without_acteur_ref():
    # Sans url_an_ou_senat, l'acteur_ref ne peut pas être extrait → liste vide.
    result = fetch_questions_officielles(None)
    assert result == []

    result = fetch_questions_officielles("https://www.nosdeputes.fr/jean-dupont")
    assert result == []


def test_fetch_questions_officielles_maps_index_to_interventions():
    # Simule un index déjà construit (sans réseau) avec 2 questions pour PA1567.
    index = {
        "PA1567": [
            {
                "uid": "QANR5L17QE1",
                "sous_type": "QE",
                "sujet": "Budget 2025",
                "texte": "Question sur le budget.",
                "reponse": None,
                "ministere": "Min. des Finances",
                "date": "2025-01-15",
                "date_reponse": None,
                "groupe_sigle": "LFI",
            },
            {
                "uid": "QANR5L17QG2",
                "sous_type": "QG",
                "sujet": "Santé",
                "texte": "Question au gouvernement sur la santé.",
                "reponse": "Réponse du gouvernement.",
                "ministere": "Min. de la Santé",
                "date": "2025-02-20",
                "date_reponse": "2025-03-10",
                "groupe_sigle": "LFI",
            },
        ]
    }

    def fake_build_index(legislature, **_):
        return index if legislature == "17" else {}

    with patch("candidate_profile._build_acteur_questions_index", side_effect=fake_build_index):
        result = fetch_questions_officielles(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1567"
        )

    assert len(result) == 2
    # Tri décroissant par date
    assert result[0]["date"] == "2025-02-20"
    assert result[1]["date"] == "2025-01-15"

    q0 = result[0]
    assert q0["type_detail"] == "question"
    assert q0["sous_type"] == "QG"
    assert q0["sujet"] == "Santé"
    assert q0["reponse"] == "Réponse du gouvernement."
    assert q0["ministere"] == "Min. de la Santé"
    assert q0["date_reponse"] == "2025-03-10"
    assert q0["format"] == "prise_de_parole_developpee"
    assert q0["id"] == "question_QANR5L17QG2"
    assert "q17/QANR5L17QG2.htm" in (q0["url"] or "")
    assert q0["legislature"] == "17"

    q1 = result[1]
    assert q1["reponse"] is None
    assert q1["date_reponse"] is None


def test_fetch_questions_officielles_aggregates_multiple_legislatures():
    index_16 = {"PA1567": [{"uid": "QANR5L16QE1", "sous_type": "QE", "sujet": "S16",
                             "texte": "T", "reponse": None, "ministere": None,
                             "date": "2023-05-01", "date_reponse": None, "groupe_sigle": None}]}
    index_17 = {"PA1567": [{"uid": "QANR5L17QE1", "sous_type": "QE", "sujet": "S17",
                             "texte": "T", "reponse": None, "ministere": None,
                             "date": "2025-01-01", "date_reponse": None, "groupe_sigle": None}]}

    def fake_build_index(legislature, **_):
        return index_17 if legislature == "17" else index_16 if legislature == "16" else {}

    with patch("candidate_profile._build_acteur_questions_index", side_effect=fake_build_index):
        result = fetch_questions_officielles(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1567"
        )

    assert len(result) == 2
    subjects = {r["sujet"] for r in result}
    assert subjects == {"S16", "S17"}


# ---------------------------------------------------------------------------
# Syceron (débats officiels)
# ---------------------------------------------------------------------------

def test_parse_syceron_intervention_entry_keeps_official_actor_match():
    parsed = _parse_syceron_intervention_entry(
        {
            "date": "2025-02-11",
            "type_detail": "question_gouvernement",
            "sujet": "Questions au Gouvernement",
            "texte": "Monsieur le Premier ministre...",
            "fonction": "député",
            "format": "prise_de_parole_developpee",
            "mots_cles": [],
            "source_id": "CRSANR5L17S2025O1N037",
            "seance_ref": "RUANR5L17S2025IDS28624",
            "session_ref": "SCR5A2025O1",
            "orateur_id_source": "PA1567",
            "orateur_nom": "Jean Dupont",
            "point_ordre_du_jour": "Questions au Gouvernement",
            "etat_compte_rendu": "complet",
            "version_compte_rendu": "JO",
        },
        "17",
        3,
    )

    assert parsed is not None
    acteur_ref, record = parsed
    assert acteur_ref == "PA1567"
    assert record["id"] == "syceron_CRSANR5L17S2025O1N037_000003"
    assert record["legislature"] == "17"
    assert record["source_url"].endswith("/17/vp/syceronbrut/syseron.xml.zip")


def test_parse_syceron_intervention_entry_returns_none_without_official_actor_ref():
    assert _parse_syceron_intervention_entry({"orateur_id_source": None}, "17", 0) is None
    assert _parse_syceron_intervention_entry({"orateur_id_source": "GVT1"}, "17", 0) is None


def test_fetch_interventions_syceron_returns_empty_without_acteur_ref():
    assert fetch_interventions_syceron(None) == []
    assert fetch_interventions_syceron("https://www.nosdeputes.fr/jean-dupont") == []


def test_fetch_interventions_syceron_maps_actor_to_candidate_interventions(tmp_path, monkeypatch):
    # Le cache Syceron de CE test, jamais celui du poste (#721) :
    # `fetch_interventions_syceron` LIT LE CACHE avant d'appeler le
    # constructeur patché ci-dessous, et sur une machine ayant déjà
    # collecté, la lecture réussissait et rendait 688 interventions
    # réelles pour la seule qu'attend la fixture. Les constantes de cache
    # étant relatives, déplacer le répertoire courant les emmène toutes.
    monkeypatch.chdir(tmp_path)

    index = {
        "PA1567": [
            {
                "id": "syceron_CRS17_000001",
                "date": "2025-02-11",
                "type_detail": "question_gouvernement",
                "sujet": "Questions au Gouvernement",
                "texte": "Texte 17",
                "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip",
                "legislature": "17",
            }
        ]
    }

    with patch("candidate_profile.SYCERON_AVAILABLE_LEGISLATURES", {"17"}), \
         patch("candidate_profile._build_acteur_interventions_syceron_index", return_value=index):
        result = fetch_interventions_syceron(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1567"
        )

    assert len(result) == 1
    assert result[0]["id"] == "syceron_CRS17_000001"
    assert result[0]["sujet"] == "Questions au Gouvernement"


def test_fetch_interventions_syceron_aggregates_multiple_legislatures(tmp_path, monkeypatch):
    # Le cache Syceron de CE test, jamais celui du poste (#721) :
    # `fetch_interventions_syceron` LIT LE CACHE avant d'appeler le
    # constructeur patché ci-dessous, et sur une machine ayant déjà
    # collecté, la lecture réussissait et rendait 688 interventions
    # réelles pour la seule qu'attend la fixture. Les constantes de cache
    # étant relatives, déplacer le répertoire courant les emmène toutes.
    monkeypatch.chdir(tmp_path)

    index_16 = {
        "PA1567": [{"id": "syceron_CRS16_000001", "date": "2024-06-01", "sujet": "L16"}]
    }
    index_17 = {
        "PA1567": [{"id": "syceron_CRS17_000001", "date": "2025-02-11", "sujet": "L17"}]
    }

    def fake_build_index(legislature, **_):
        return index_17 if legislature == "17" else index_16 if legislature == "16" else {}

    with patch("candidate_profile.SYCERON_AVAILABLE_LEGISLATURES", {"16", "17"}), \
         patch("candidate_profile._build_acteur_interventions_syceron_index", side_effect=fake_build_index):
        result = fetch_interventions_syceron(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1567"
        )

    assert [r["sujet"] for r in result] == ["L17", "L16"]


# ---------------------------------------------------------------------------
# build_profile integrates official questions into interventions
# ---------------------------------------------------------------------------

def test_build_profile_includes_official_questions_in_interventions():
    fake_questions = [
        {
            "id": "question_QANR5L17QE1",
            "date": "2025-01-15",
            "type_detail": "question",
            "sous_type": "QE",
            "sujet": "Budget",
            "texte": "Texte Q",
            "reponse": None,
            "date_reponse": None,
            "ministere": "Min. Finances",
            "groupe_sigle": "LFI",
            "fonction": None,
            "format": "prise_de_parole_developpee",
            "mots_cles": [],
            "url": "https://questions.assemblee-nationale.fr/q17/QANR5L17QE1.htm",
            "url_detail": "https://questions.assemblee-nationale.fr/q17/QANR5L17QE1.htm",
            "legislature": "17",
        }
    ]

    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_questions_officielles", return_value=fake_questions),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=(None, None)),
    ):
        profile = build_profile("deputes", "slug-test")

    # Sans identité, les questions ne sont pas collectées : elles ne doivent PAS
    # être dans interventions.
    assert not any(i.get("type_detail") == "question" for i in profile["interventions"])


# ---------------------------------------------------------------------------
# `_get_payload` / `_try_urls` / le watchdog : RETIRÉS (#529, lot 5)
#
# Six tests figeaient ici la logique de court-circuit sur échec déterministe
# (`_TERMINAL_FAILURE` sur 4xx et sur format inconnu, `None` sur 5xx après trois
# tentatives, l'abandon du watchdog sur requête pendue, le saut du suffixe
# `/xml` après un `/json` terminal). Tout cela décrivait UN chemin réseau, celui
# de NosDéputés/NosSénateurs : l'open data AN passe par `requests.get`,
# `download_with_watchdog` et `_telecharger_flux` en direct, jamais par là.
#
# Les tests partent avec le code. Ce qui protège les téléchargements restants
# est ailleurs et n'a pas bougé : les reprises segmentées des archives
# d'amendements (plus bas dans ce fichier) et `download_watchdog.py` avec son
# propre fichier de tests.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# #78 — Syceron comme source primaire dans build_profile()
# ---------------------------------------------------------------------------

def _identite_an_resolue():
    """Ce que `fetch_identite_officielle_par_slug` rend pour un slug résolu.

    Remplace `_fake_identity_with_acteur_ref`, qui fabriquait une réponse
    NosDéputés (`{"depute": {...}}`) : cette forme n'entre plus nulle part
    depuis #529. L'`acteur_ref` est ce dont dépend tout le reste de la
    collecte — c'est lui que `_extract_acteur_ref` relit dans l'URL de fiche.
    """
    return (
        {
            "nom_complet": "Jean Dupont",
            "groupe_sigle": "RE",
            "groupe_nom": "Renaissance",
            "mandat_debut": "2024-07-18",
            "mandat_fin": None,
        },
        "PA123456",
    )


def test_build_profile_uses_syceron_as_primary_for_deputes():
    """Quand Syceron retourne des interventions, elles doivent être utilisées
    comme source primaire — et, depuis #529, comme seule source."""
    fake_syceron = [
        {
            "id": "syceron_CRS17_000001",
            "date": "2025-02-11",
            "type_detail": "loi",
            "sujet": "Débat officiel",
            "texte": "Texte officiel.",
            "seance_ref": "RUANR5L17S2025O1N037",
        }
    ]
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=fake_syceron),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        profile = build_profile("deputes", "jean-dupont")

    assert profile["interventions"] == fake_syceron
    assert profile["meta"]["synchro_sources"]["assemblee_nationale_syceron"] is not None
    assert not any("syceron indisponibles" in w for w in profile["meta"]["warnings"])


def test_build_profile_ne_retombe_plus_sur_nosdeputes_quand_syceron_est_vide():
    """#510 : le repli NosDéputés a été RETIRÉ du chemin interventions.

    Une collecte Syceron vide reste vide, et le dit. C'est ce repli qui a rendu
    #510 invisible pendant toute sa durée de vie : le chemin rendait 789
    interventions, dont 0 de la source primaire, donc rien ne signalait que
    celle-ci était muette.
    """
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        profile = build_profile("deputes", "jean-dupont")

    assert profile["interventions"] == []
    assert profile["meta"]["synchro_sources"]["assemblee_nationale_syceron"] is None
    # #560 — le silence est déclaré, mais sous le préfixe du CONSTAT et non
    # celui de la panne : la collecte est allée au bout sans lever, donc les
    # archives ont répondu. Un préfixe ne recouvre plus deux états.
    warnings_syceron = [
        w for w in profile["meta"]["warnings"]
        if w.startswith(candidate_profile.WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE)
    ]
    assert warnings_syceron, "le silence de la source primaire doit être déclaré (§2.5)"
    assert not any(
        w.startswith(candidate_profile.WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES)
        for w in profile["meta"]["warnings"]
    ), "une collecte qui aboutit à vide n'est pas une panne (#560)"
    assert not any("fallback" in w.lower() for w in profile["meta"]["warnings"])


def test_build_profile_syceron_en_echec_est_declare_sans_repli():
    """Une exception Syceron laisse la section vide, déclarée — et ne convoque personne (#510).

    L'échec simulé est un `requests.ConnectionError` depuis #562, et non plus un
    `RuntimeError` : le test dit « la source n'a pas répondu », et depuis #562
    c'est le TYPE de l'exception qui porte cette affirmation. Un `RuntimeError`
    ne vient jamais du réseau — il est désormais lu comme un défaut de ce dépôt,
    ce que vérifie `test_build_profile_defaut_de_code_nest_pas_une_panne_de_source`.
    """
    import requests

    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron",
              side_effect=requests.ConnectionError("connexion échouée")),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        profile = build_profile("deputes", "jean-dupont")

    assert profile["meta"]["synchro_sources"]["assemblee_nationale_syceron"] is None
    assert any("connexion échouée" in w for w in profile["meta"]["warnings"]), (
        "la cause de l'échec doit voyager jusqu'au warning publié (#524)"
    )


def test_les_fetchs_nosdeputes_nont_plus_de_definition():
    """Le verrou du lot 5, côté collecte de profil. Ces noms formaient la
    chaîne complète, du transport au résultat : tant que l'un d'eux existe,
    une source retirée par décision peut être rebranchée sans décision."""
    for nom in (
        "BASE_URLS",
        "_get_payload",
        "_get_with_watchdog",
        "_try_urls",
        "fetch_identity",
        "fetch_recherche",
        "fetch_all_intervention_results",
        "fetch_all_intervention_results_from_domains",
        "fetch_intervention_details",
        "fetch_seance_context",
        "_extract_search_results",
        "_process_search_result",
        "_classify_intervention",
        "_extract_speaker_identity_from_html",
        "_extract_mandats",
        "_extract_parlementaire",
        "compteur_appels_nosdeputes",
        "compteur_requetes_sans_reponse",
        "WARNING_PREFIX_SOURCE_INJOIGNABLE",
    ):
        assert not hasattr(candidate_profile, nom), (
            f"`candidate_profile.{nom}` est de retour : c'est un morceau du "
            "chemin NosDéputés, retiré par #529. Voir "
            "docs/decisions/retrait-nosdeputes-529.md."
        )


# ---------------------------------------------------------------------------
# #357 — mode d'extraction léger (extract-roster-groupes) : skip_dossiers_legislatifs
# ---------------------------------------------------------------------------

def test_build_profile_skip_dossiers_legislatifs_deputes_never_calls_textes_portes():
    """skip_dossiers_legislatifs=True doit empêcher tout appel à
    fetch_textes_portes_officiels (étape 8bis, députés) et laisser
    dossiers_legislatifs vide."""
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels") as mock_textes_portes,
    ):
        profile = build_profile(
            "deputes", "jean-dupont", skip_interventions=True, skip_dossiers_legislatifs=True
        )

    mock_textes_portes.assert_not_called()
    assert profile["dossiers_legislatifs"] == []


# ---------------------------------------------------------------------------
# #83 — Tests d'intégration bout-en-bout : build_profile() → normalize_profil()
# ---------------------------------------------------------------------------

def _fake_syceron_interventions():
    """3 interventions Syceron avec seance_ref, session_ref et point_ordre_du_jour."""
    syceron_zip = "https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronXML/syceron.zip"
    return [
        {
            "id": "syceron_CRS17_000001_000000",
            "date": "2025-02-11",
            "type_detail": "loi",
            "sujet": "Débat sur le budget rectificatif",
            "texte": "Texte de l'intervention 1.",
            "fonction": None,
            "format": "long",
            "mots_cles": ["budget", "fiscalité"],
            "source": syceron_zip,
            "source_url": syceron_zip,
            "url": syceron_zip,
            "url_detail": None,
            "source_id": "CRS17_000001",
            "seance_ref": "RUANR5L17S2025O1N037",
            "session_ref": "S2024-2025",
            "orateur_id_source": "PA123456",
            "orateur_nom": "Jean Dupont",
            "point_ordre_du_jour": "Examen du PLFR 2025",
            "etat_compte_rendu": "definitif",
            "version_compte_rendu": "1",
            "legislature": "17",
        },
        {
            "id": "syceron_CRS17_000002_000000",
            "date": "2025-03-05",
            "type_detail": "commission",
            "sujet": "Audition du ministre de l'économie",
            "texte": "Texte de l'intervention 2.",
            "fonction": "president",
            "format": "court",
            "mots_cles": ["économie"],
            "source": syceron_zip,
            "source_url": syceron_zip,
            "url": syceron_zip,
            "url_detail": None,
            "source_id": "CRS17_000002",
            "seance_ref": "RUANR5L17S2025O1N041",
            "session_ref": "S2024-2025",
            "orateur_id_source": "PA123456",
            "orateur_nom": "Jean Dupont",
            "point_ordre_du_jour": None,
            "etat_compte_rendu": "definitif",
            "version_compte_rendu": "1",
            "legislature": "17",
        },
        {
            "id": "syceron_CRS17_000003_000000",
            "date": "2025-04-22",
            "type_detail": "loi",
            "sujet": "Discussion générale sur la réforme des retraites",
            "texte": "Texte de l'intervention 3.",
            "fonction": None,
            "format": "long",
            "mots_cles": ["social", "retraites"],
            "source": syceron_zip,
            "source_url": syceron_zip,
            "url": syceron_zip,
            "url_detail": None,
            "source_id": "CRS17_000003",
            "seance_ref": "RUANR5L17S2025O1N055",
            "session_ref": "S2024-2025",
            "orateur_id_source": "PA123456",
            "orateur_nom": "Jean Dupont",
            "point_ordre_du_jour": "Réforme des retraites — PL n° 2025-17",
            "etat_compte_rendu": "provisoire",
            "version_compte_rendu": "1",
            "legislature": "17",
        },
    ]


def test_integration_build_profile_syceron_enrichit_champs_pivot():
    """Intégration bout-en-bout : build_profile() avec Syceron → normalize_profil()
    doit produire des interventions avec theme_officiel, seance, dossier et
    source renseignés.

    Le test vérifiait aussi qu'aucun scraping HTML NosDéputés
    (`fetch_seance_context`) n'était déclenché ; cette assertion est devenue
    structurelle avec #529 — la fonction n'existe plus, et
    `test_les_fetchs_nosdeputes_nont_plus_de_definition` le vérifie une fois
    pour toutes plutôt qu'à chaque scénario.
    """
    fake_syceron = _fake_syceron_interventions()

    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=fake_syceron),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        raw_profile = build_profile("deputes", "jean-dupont")

    # L'étape de normalisation transforme les enregistrements bruts Syceron en format pivot.
    pivot = normalize_profil(raw_profile)

    assert len(pivot["interventions"]) == 3, "Les 3 interventions Syceron doivent être présentes dans le pivot"

    # Intervention 1 — avec seance_ref, session_ref et point_ordre_du_jour
    i1 = pivot["interventions"][0]
    assert i1["theme_officiel"] == "Débat sur le budget rectificatif"
    assert i1["seance"] == {"ref": "RUANR5L17S2025O1N037", "session_ref": "S2024-2025"}
    assert i1["dossier"] == {"point_ordre_du_jour": "Examen du PLFR 2025"}
    assert i1["source"]["type"] == "syceron"
    assert i1["source"]["source_id"] == "CRS17_000001"
    assert i1["source"]["legislature"] == "17"

    # Intervention 2 — avec seance_ref mais sans point_ordre_du_jour
    i2 = pivot["interventions"][1]
    assert i2["theme_officiel"] == "Audition du ministre de l'économie"
    assert i2["seance"]["ref"] == "RUANR5L17S2025O1N041"
    assert i2["dossier"] is None
    assert i2["source"]["type"] == "syceron"

    # Intervention 3 — avec seance_ref et point_ordre_du_jour
    i3 = pivot["interventions"][2]
    assert i3["theme_officiel"] == "Discussion générale sur la réforme des retraites"
    assert i3["seance"]["ref"] == "RUANR5L17S2025O1N055"
    assert i3["dossier"] == {"point_ordre_du_jour": "Réforme des retraites — PL n° 2025-17"}
    assert i3["source"]["type"] == "syceron"


def test_integration_les_interventions_nosdeputes_deja_collectees_restent_normalisables():
    """#510 : le repli est retiré de la COLLECTE, pas de la normalisation.

    La fusion additive ne retire rien : les interventions NosDéputés déjà
    acquises restent dans `raw_data/profiles/` et doivent continuer à se
    normaliser — sans champs Syceron, qu'elles n'ont jamais portés. Retirer leur
    lecture ferait disparaître du corpus publié des faits déjà collectés, ce que
    le contrôle de perte de #460/#470 bloque.
    """
    raw_profile = {
        "interventions": [
            {
                "type": "Intervention",
                "date": "2024-11-15",
                "sujet": "Discussion générale",
                "texte": "Intervention NosDéputés déjà collectée.",
                "url": "https://www.nosdeputes.fr/jean-dupont/intervention/123",
                "url_detail": "https://www.nosdeputes.fr/jean-dupont/intervention/123",
                "mots_cles": [],
                "source_id": None,
                "seance_ref": None,
                "session_ref": None,
                "point_ordre_du_jour": None,
            }
        ],
    }

    pivot = normalize_profil(raw_profile)

    assert len(pivot["interventions"]) == 1
    i = pivot["interventions"][0]
    assert i["texte"] == "Intervention NosDéputés déjà collectée."
    assert i["theme_officiel"] is None, "theme_officiel doit être null pour une intervention NosDéputés"
    assert i["seance"] is None, "seance doit être null pour une intervention NosDéputés"
    assert i["source"] is None, "source syceron doit être null pour une intervention NosDéputés"


def test_integration_sans_syceron_le_pivot_ne_fabrique_aucune_intervention():
    """Le pendant du test ci-dessus, après #529 : Syceron vide ne produit plus
    d'interventions du tout.

    Ce test remplaçait `test_integration_build_profile_fallback_sans_acteur_ref`,
    qui vérifiait qu'une intervention de repli NosDéputés traversait la
    normalisation avec `theme_officiel`, `seance` et `source` à `null`. Ce
    repli n'existe plus ; ce qui doit rester vrai est que le vide est
    **déclaré** et que la normalisation n'invente rien pour le combler.
    """
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        raw_profile = build_profile("deputes", "jean-dupont")

    assert raw_profile["meta"]["synchro_sources"].get("assemblee_nationale_syceron") is None
    # #560 : préfixe du constat, pas celui de la panne.
    assert any(
        w.startswith(candidate_profile.WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE)
        for w in raw_profile["meta"]["warnings"]
    )

    pivot = normalize_profil(raw_profile)

    assert pivot["interventions"] == []
    assert pivot["tags_thematiques"] == [], (
        "aucun tag ne doit être dérivé de rien — les tags publiés viennent des "
        "interventions déjà collectées, conservées par la fusion additive"
    )
    # Le warning brut voyage jusqu'au pivot : c'est lui qui rend le vide lisible
    # dans le corpus publié.
    assert any(
        w.startswith(candidate_profile.WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE)
        for w in pivot["meta"]["warnings"]
    )


# ---------------------------------------------------------------------------
# Tests pour la non-avalage des échecs de collecte des amendements officiels
# (issue #185 : un échec réseau/zip était indiscernable d'un simple "aucun
# amendement" — aucun warning n'était jamais tracé dans meta.warnings).
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tests pour la séparation téléchargement/construction vs lecture cache-only
# (issue #250, sous-issue 2/6 de #248) : la lecture du cache ne doit jamais
# déclencher d'appel réseau ; `_download_and_build_amendement_index` reprend
# telle quelle la logique réseau (téléchargement/retry/cache d'échec),
# désormais appelée uniquement par le job dédié `extract-amendements-an`
# (`src/build_amendements_index.py`, #251) — plus par `fetch_amendements_officiels`,
# qui lit exclusivement le cache depuis #252 (sous-issue 4/6 de #248).
#
# Depuis #377, le cache est stocké sous forme dédupliquée (`amendements.json`
# + `index_par_acteur.json` compact) et la lecture se fait par acteur
# (`_read_cached_amendements_acteur`) au lieu d'expanser tout l'index.
# ---------------------------------------------------------------------------

def _write_cache_amendements(cache_dir: Path, legislature: str, amendements: dict, index_par_acteur: dict) -> None:
    """Écrit un cache d'amendements au format attendu : store dédupliqué (#377)
    + index shardé par acteur (#392, un fichier par acteurRef)."""
    leg_dir = cache_dir / legislature
    leg_dir.mkdir(parents=True, exist_ok=True)
    (leg_dir / "amendements.json").write_text(json.dumps(amendements, ensure_ascii=False), encoding="utf-8")
    shards = leg_dir / "index_par_acteur"
    shards.mkdir(exist_ok=True)
    for acteur_ref, refs in index_par_acteur.items():
        (shards / f"{acteur_ref}.json").write_text(json.dumps(refs, ensure_ascii=False), encoding="utf-8")


def test_read_cached_amendements_acteur_returns_none_when_absent(tmp_path):
    """Aucun cache pour cette législature : `None` (pas `[]`, pour rester
    distinguable d'un acteur sans amendement dans un index bien présent), et
    aucun appel réseau ne doit être déclenché."""
    from candidate_profile import _read_cached_amendements_acteur

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        result = _read_cached_amendements_acteur("17", "PA1")

    assert result is None
    mock_get.assert_not_called()


def test_read_cached_amendements_acteur_resolves_references(tmp_path):
    """Les références compactes `{uid, role_signataire}` de l'acteur sont
    résolues en enregistrements complets via `amendements.json`, sans appel
    réseau — et seules celles de cet acteur le sont."""
    from candidate_profile import _read_cached_amendements_acteur

    _write_cache_amendements(
        tmp_path,
        "17",
        amendements={
            "U1": {"uid": "U1", "numero": "A1", "date": "2024-01-01", "texte_vise": "T1"},
            "U2": {"uid": "U2", "numero": "A2", "date": "2024-02-01", "texte_vise": "T2"},
        },
        index_par_acteur={
            "PA1": [{"uid": "U1", "role_signataire": "auteur_principal"}],
            "PA2": [{"uid": "U2", "role_signataire": "co_signataire"}],
        },
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        result = _read_cached_amendements_acteur("17", "PA1")

    assert result == [
        {"uid": "U1", "numero": "A1", "date": "2024-01-01", "texte_vise": "T1",
         "role_signataire": "auteur_principal"}
    ]
    mock_get.assert_not_called()


def test_read_cached_amendements_acteur_refuse_une_tranche_au_format_herite(tmp_path):
    """Une tranche héritée (`{numero, role_signataire}`, avant la correction de
    clé du 18/08/2026) doit être traitée comme un cache absent — donc
    reconstruite — jamais relue.

    La relire résoudrait vers le mauvais amendement dans 40,5 % des cas, et
    rien à l'usage ne distinguerait ces enregistrements de références
    correctes : mieux vaut un warning « index indisponible » qu'un amendement
    attribué au mauvais texte (AGENTS.md §2.5).
    """
    from candidate_profile import _read_cached_amendements_acteur

    _write_cache_amendements(
        tmp_path,
        "17",
        amendements={"A1": {"numero": "A1", "texte_vise": "T1"}},
        index_par_acteur={"PA1": [{"numero": "A1", "role_signataire": "auteur_principal"}]},
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        assert _read_cached_amendements_acteur("17", "PA1") is None


def test_read_cached_amendements_acteur_returns_empty_list_for_unknown_acteur(tmp_path):
    """Cache présent mais acteur absent de l'index : liste vide (pas `None`) —
    distinguer « pas d'amendement pour cet élu » de « index indisponible »
    est ce qui pilote le warning côté `fetch_amendements_officiels`."""
    from candidate_profile import _read_cached_amendements_acteur

    _write_cache_amendements(tmp_path, "17", amendements={}, index_par_acteur={"PA1": []})

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        result = _read_cached_amendements_acteur("17", "PA_INCONNU")

    assert result == []


def test_read_cached_amendements_acteur_ignores_dangling_reference(tmp_path):
    """Une référence dont l'`uid` est absent de `amendements.json` est
    ignorée plutôt que de lever (cohérent avec
    `_expand_aggregated_amendements_index`)."""
    from candidate_profile import _read_cached_amendements_acteur

    _write_cache_amendements(
        tmp_path,
        "17",
        amendements={"U1": {"uid": "U1", "numero": "A1"}},
        index_par_acteur={"PA1": [{"uid": "U1"}, {"uid": "INCONNU"}]},
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        result = _read_cached_amendements_acteur("17", "PA1")

    assert result == [{"uid": "U1", "numero": "A1", "role_signataire": None}]


def test_read_cached_amendements_acteur_ne_lit_que_la_tranche_demandee(tmp_path):
    """#392 : la lecture ne doit toucher QUE la tranche de l'acteur demandé.

    Vérifié en rendant illisible la tranche d'un AUTRE acteur : si la lecture
    parcourait encore l'index complet, elle échouerait. C'est tout l'objet du
    shardage — relire les 673 Mo d'index à chaque candidat représentait 93 %
    du coût d'extraction du roster (#376)."""
    from candidate_profile import _read_cached_amendements_acteur

    _write_cache_amendements(
        tmp_path, "17",
        amendements={"U1": {"uid": "U1", "numero": "A1", "date": "2024-01-01"}},
        index_par_acteur={"PA1": [{"uid": "U1", "role_signataire": "auteur_principal"}]},
    )
    # Tranche d'un autre acteur, volontairement corrompue.
    (tmp_path / "17" / "index_par_acteur" / "PA999.json").write_text("{pas du JSON", encoding="utf-8")

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        result = _read_cached_amendements_acteur("17", "PA1")

    assert result == [
        {"uid": "U1", "numero": "A1", "date": "2024-01-01", "role_signataire": "auteur_principal"}
    ]


def test_download_and_build_amendement_index_reconstruit_un_cache_au_format_herite(tmp_path):
    """Un cache disque hérité (références par `numero`) ne doit PAS être
    considéré comme un cache-hit : sans ce contrôle, il ne serait jamais
    reconstruit ici, pendant que `_read_cached_amendements_acteur` le
    refuserait à la lecture — les amendements de la législature
    disparaîtraient silencieusement jusqu'à expiration du cache CI."""
    from candidate_profile import _download_and_build_amendement_index

    cache_dir = tmp_path / "cache"
    _write_cache_amendements(
        cache_dir,
        "17",
        amendements={"A1": {"numero": "A1", "texte_vise": "T1"}},
        index_par_acteur={"PA1": [{"numero": "A1", "role_signataire": "auteur_principal"}]},
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir),
        patch("candidate_profile._amendements_zip_url", return_value=None),
    ):
        resultat = _download_and_build_amendement_index("17")

    # `_amendements_zip_url` à None court-circuite le téléchargement : ce qui
    # compte ici est que le cache hérité n'ait PAS été rendu tel quel.
    assert resultat == {}


def test_download_and_build_amendement_index_sert_un_cache_au_format_uid(tmp_path):
    """Symétrique : un cache au format `uid` reste un cache-hit, sans réseau."""
    from candidate_profile import _download_and_build_amendement_index

    cache_dir = tmp_path / "cache"
    _write_cache_amendements(
        cache_dir,
        "17",
        amendements={"U1": {"uid": "U1", "numero": "A1"}},
        index_par_acteur={"PA1": [{"uid": "U1", "role_signataire": "auteur_principal"}]},
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        resultat = _download_and_build_amendement_index("17")

    assert set(resultat) == {"PA1"}
    mock_get.assert_not_called()


def test_read_cached_amendements_acteur_refuse_un_acteur_ref_hors_forme(tmp_path):
    """Le nom de tranche dérive de l'acteurRef : tout ce qui n'a pas la forme
    `PA<chiffres>` est refusé plutôt qu'assaini approximativement, pour qu'un
    identifiant malformé ne puisse jamais désigner un chemin hors du cache."""
    from candidate_profile import _read_cached_amendements_acteur

    _write_cache_amendements(tmp_path, "17", amendements={}, index_par_acteur={"PA1": []})

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        for mauvais in ("../../etc/passwd", "PA1/../PA2", "", "NOTAREF"):
            assert _read_cached_amendements_acteur("17", mauvais) == []


def test_write_cached_amendements_supprime_l_index_plat_herite(tmp_path):
    """Migration : l'écriture au format shardé supprime le fichier unique
    hérité de #377, pour libérer les centaines de Mo qu'il occupait."""
    from candidate_profile import _write_cached_amendements_agreges

    leg_dir = tmp_path / "17"
    leg_dir.mkdir(parents=True)
    (leg_dir / "index_par_acteur.json").write_text('{"PA1": []}', encoding="utf-8")

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        _write_cached_amendements_agreges("17", {"A1": {"numero": "A1"}}, {"PA1": [{"numero": "A1"}]})

    assert not (leg_dir / "index_par_acteur.json").exists(), "L'index plat hérité doit être supprimé"
    assert (leg_dir / "index_par_acteur" / "PA1.json").is_file()


def test_write_cached_amendements_reconstruit_le_repertoire_de_tranches(tmp_path):
    """Une tranche d'un acteur disparu d'une reconstruction ne doit pas
    survivre : le répertoire est reconstruit de zéro, pas complété."""
    from candidate_profile import _write_cached_amendements_agreges

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        _write_cached_amendements_agreges("17", {}, {"PA1": [], "PA2": []})
        assert (tmp_path / "17" / "index_par_acteur" / "PA2.json").is_file()
        _write_cached_amendements_agreges("17", {}, {"PA1": []})

    assert (tmp_path / "17" / "index_par_acteur" / "PA1.json").is_file()
    assert not (tmp_path / "17" / "index_par_acteur" / "PA2.json").exists()


def test_read_cached_amendements_acteur_returns_none_on_legacy_flat_cache(tmp_path):
    """Cache hérité d'avant #377 (`index_par_acteur.json` plat, sans
    `amendements.json`) : traité comme absent, JAMAIS relu en mémoire — c'est
    tout l'objet du correctif, cette forme pesant jusqu'à 4,67 Go pour la
    législature 16. Le cache sera reconstruit au format compact."""
    from candidate_profile import _read_cached_amendements_acteur

    leg_dir = tmp_path / "17"
    leg_dir.mkdir(parents=True)
    (leg_dir / "index_par_acteur.json").write_text(
        json.dumps({"PA1": [{"numero": "A1", "date": "2024-01-01"}]}), encoding="utf-8"
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        result = _read_cached_amendements_acteur("17", "PA1")

    assert result is None


def test_read_cached_amendements_acteur_returns_none_on_corrupted_cache(tmp_path):
    """Cache présent mais illisible (JSON corrompu) : traité comme absent
    (`None`), pas d'exception propagée, aucun appel réseau."""
    from candidate_profile import _read_cached_amendements_acteur

    leg_dir = tmp_path / "17"
    leg_dir.mkdir(parents=True)
    (leg_dir / "amendements.json").write_text("{not valid json", encoding="utf-8")
    (leg_dir / "index_par_acteur.json").write_text("{not valid json", encoding="utf-8")

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        result = _read_cached_amendements_acteur("17", "PA1")

    assert result is None
    mock_get.assert_not_called()


def test_download_and_build_amendement_index_ignores_existing_cache_write(tmp_path):
    """`_download_and_build_amendement_index` reprend telle quelle la logique
    réseau : sur un échec de téléchargement, elle lève `AmendementsIndexError`
    et marque la législature en échec (#239/#246), exactement comme
    `_build_acteur_amendement_index` avant le découpage de #250."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AmendementsIndexError,
        _download_and_build_amendement_index,
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")) as mock_get,
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    assert mock_get.call_count == _budget_appels_reseau_echec_total()


# ---------------------------------------------------------------------------
# Tests pour l'indicateur de fraîcheur et la non-régression d'un index déjà en
# cache sur échec définitif de reconstruction (issue #253, sous-issue 5/6 de
# #248) : `_download_and_build_amendement_index` n'ouvre `index_path` en
# écriture qu'après succès complet — un échec, quel qu'il soit, laisse donc
# tel quel un index déjà présent sur disque. `fraicheur.json`, écrit à côté,
# permet de distinguer un index frais d'un index conservé faute de mieux.
# ---------------------------------------------------------------------------

def test_download_and_build_amendement_index_success_writes_fraicheur(tmp_path):
    """Reconstruction réussie : l'index est remplacé et `fraicheur.json` reflète
    le succès avec un horodatage."""
    import io
    import zipfile as zipfile_module

    from candidate_profile import _download_and_build_amendement_index

    buf = io.BytesIO()
    with zipfile_module.ZipFile(buf, "w") as zf:
        pass  # zip valide mais vide : suffisant, ce test porte sur la fraîcheur
    valid_zip_bytes = buf.getvalue()

    class FakeStreamResponse(_FluxFactice):
        status_code = 200  # fichier entier en un seul segment (voir tests ci-dessus)

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield valid_zip_bytes

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=FakeStreamResponse()),
        patch("candidate_profile.time.strftime", return_value="2026-08-13T12:00:00+0000"),
    ):
        index = _download_and_build_amendement_index("17")

    assert index == {}
    fraicheur = json.loads((tmp_path / "17" / "fraicheur.json").read_text(encoding="utf-8"))
    assert fraicheur == {
        "derniere_construction_reussie": True,
        "horodatage": "2026-08-13T12:00:00+0000",
    }


# ---------------------------------------------------------------------------
# Nettoyage de l'archive brute `amendements.zip` (issue #264) : 283-618 Mo par
# législature, jamais relus une fois l'index construit — ni par la lecture
# cache-only, ni pour reprendre un téléchargement (toujours réécrit depuis
# zéro). Doivent disparaître dans TOUS les cas, sinon ils gonflent l'artifact
# `amendements-index-an` et le cache partagé `public-data-cache-an-*`.
# ---------------------------------------------------------------------------

def _fake_amendements_zip_response(zip_bytes: bytes):
    """Réponse de streaming factice servant `zip_bytes` en un seul segment."""

    class FakeStreamResponse(_FluxFactice):
        status_code = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield zip_bytes

    return FakeStreamResponse()


def test_download_and_build_amendement_index_success_removes_raw_zip(tmp_path):
    """Succès : l'archive brute est supprimée, l'index utile reste."""
    import io
    import zipfile as zipfile_module

    from candidate_profile import _download_and_build_amendement_index

    buf = io.BytesIO()
    with zipfile_module.ZipFile(buf, "w") as zf:
        pass  # zip valide mais vide : ce test porte sur le nettoyage, pas le contenu

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_fake_amendements_zip_response(buf.getvalue())),
    ):
        _download_and_build_amendement_index("17")

    assert not (tmp_path / "17" / "amendements.zip").exists(), "L'archive brute doit être supprimée après succès"
    assert (tmp_path / "17" / "index_par_acteur").is_dir(), "Index shardé par acteur (#392)"
    assert (tmp_path / "17" / "amendements.json").is_file()


def test_download_and_build_amendement_index_download_failure_removes_partial_zip(tmp_path):
    """Échec de téléchargement (tentatives épuisées) : aucun fichier partiel
    résiduel ne doit rester sur disque."""
    from candidate_profile import AmendementsIndexError, _download_and_build_amendement_index

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    assert not (tmp_path / "17" / "amendements.zip").exists()


def test_download_and_build_amendement_index_bad_zip_removes_raw_zip(tmp_path):
    """Archive invalide (`BadZipFile`) : l'archive téléchargée est supprimée
    malgré l'échec — un fichier invalide n'a pas plus d'utilité qu'un valide."""
    from candidate_profile import AmendementsIndexError, _download_and_build_amendement_index

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch(
            "candidate_profile.requests.get",
            return_value=_fake_amendements_zip_response(b"ceci n'est pas une archive zip"),
        ),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    assert not (tmp_path / "17" / "amendements.zip").exists()


def test_download_and_build_amendement_index_failure_preserves_existing_index(tmp_path):
    """Échec définitif sur une législature dont un index existait déjà (ici
    corrompu — seul cas où une reconstruction est réellement retentée malgré
    un fichier déjà présent : un index valide est utilisé tel quel sans
    nouvelle tentative, voir
    `test_download_and_build_amendement_index_uses_existing_cache_without_download`) : le
    fichier existant ne doit être ni supprimé ni remplacé par un résultat
    vide/partiel, et `fraicheur.json` doit refléter l'échec."""
    from candidate_profile import (
        AmendementsIndexError,
        _download_and_build_amendement_index,
    )

    index_dir = tmp_path / "17"
    index_dir.mkdir(parents=True)
    existing_content = "{not valid json"
    (index_dir / "index_par_acteur.json").write_text(existing_content, encoding="utf-8")

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")),
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.time.strftime", return_value="2026-08-13T12:05:00+0000"),
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    assert (index_dir / "index_par_acteur.json").read_text(encoding="utf-8") == existing_content, (
        "Le fichier existant ne doit jamais être supprimé ni remplacé par un résultat vide/partiel sur échec"
    )
    fraicheur = json.loads((index_dir / "fraicheur.json").read_text(encoding="utf-8"))
    assert fraicheur == {
        "derniere_construction_reussie": False,
        "horodatage": "2026-08-13T12:05:00+0000",
    }


def test_download_and_build_amendement_index_failure_without_existing_index_writes_nothing(tmp_path):
    """Échec définitif sur une législature sans index préexistant : comportement
    actuel inchangé — ni `index_par_acteur.json` ni `fraicheur.json` ne sont
    créés (rien à préserver, pas d'indicateur de fraîcheur à qualifier)."""
    from candidate_profile import AmendementsIndexError, _download_and_build_amendement_index

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    index_dir = tmp_path / "17"
    assert not (index_dir / "index_par_acteur.json").exists()
    assert not (index_dir / "fraicheur.json").exists()


def test_download_and_build_amendement_index_already_failed_this_run_preserves_existing_index(tmp_path):
    """Même garantie sur le raccourci `_amendements_legislature_failed_this_run`
    (appel suivant du même run pour une législature déjà en échec définitif) :
    un index corrompu déjà présent est préservé et `fraicheur.json` est
    rafraîchi, sans nouvelle tentative réseau."""
    from candidate_profile import (
        AmendementsIndexError,
        _amendements_failed_legislatures,
        _download_and_build_amendement_index,
    )

    index_dir = tmp_path / "17"
    index_dir.mkdir(parents=True)
    existing_content = "{not valid json"
    (index_dir / "index_par_acteur.json").write_text(existing_content, encoding="utf-8")
    _amendements_failed_legislatures.add("17")

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    mock_get.assert_not_called()
    assert (index_dir / "index_par_acteur.json").read_text(encoding="utf-8") == existing_content
    fraicheur = json.loads((index_dir / "fraicheur.json").read_text(encoding="utf-8"))
    assert fraicheur["derniere_construction_reussie"] is False


def test_download_and_build_amendement_index_uses_existing_cache_without_download(tmp_path):
    """`_download_and_build_amendement_index` : quand le cache disque existe déjà
    (double-check en tête, sous le même verrou), il est utilisé tel quel — pas de
    téléchargement."""
    from candidate_profile import _download_and_build_amendement_index

    cached_index = {"PA1": [{"uid": "U1", "role_signataire": "auteur_principal"}]}
    _write_cache_amendements(
        tmp_path, "17", amendements={"U1": {"uid": "U1", "numero": "A1"}},
        index_par_acteur=cached_index,
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        result = _download_and_build_amendement_index("17")

    # Depuis #392 le cache-hit ne renvoie que les acteurs indexés (déduits des
    # noms de tranches), pas leur contenu : le seul consommateur en fait
    # `len()`, et matérialiser les références coûterait des centaines de Mo
    # pour une information dont personne ne se sert.
    assert set(result) == set(cached_index)
    assert result == {"PA1": []}
    mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# Législatures figées (15/16) : fallback committé, aucun accès réseau
# (docs/decisions/amendements-legislatures-figees.md).
# ---------------------------------------------------------------------------

def test_download_and_build_amendement_index_uses_frozen_fallback_without_download(tmp_path):
    """Pour une législature dans `AN_AMENDEMENTS_LEGISLATURES_FIGEES`, l'index
    committé (`AN_AMENDEMENTS_FIGEES_DIR`, sous forme dédupliquée et compressée
    gzip — `amendements.json.gz` + `index_par_acteur.json.gz` allégé, voir
    `_aggregate_amendements_index`) est utilisé sans jamais toucher le réseau,
    même en l'absence de tout cache disque préexistant, et matérialisé dans le
    cache sous la MEME forme dédupliquée (en clair) — depuis #377, plus aucune
    expansion vers la forme plate n'a lieu ici."""
    from candidate_profile import _download_and_build_amendement_index

    frozen_amendements = {
        "AMANR5L15PO123456B0001P0D1N001": {
            "uid": "AMANR5L15PO123456B0001P0D1N001",
            "texte_vise": "PRJLANR5L15B0001",
            "sort": None,
            "base_juridique_irrecevabilite": None,
            "premier_signataire": "an:PA1",
            "co_signataires": [],
            "type_deposant": None,
            "date": "2018-01-01",
            "numero": "AMANR5L15PO123456B0001P0D1N001",
            "source_url": None,
        }
    }
    frozen_index_par_acteur = {
        "PA1": [{"uid": "AMANR5L15PO123456B0001P0D1N001", "role_signataire": "auteur_principal"}]
    }
    frozen_dir = tmp_path / "figees" / "15"
    frozen_dir.mkdir(parents=True)
    with gzip.open(frozen_dir / "amendements.json.gz", "wt", encoding="utf-8") as f:
        json.dump(frozen_amendements, f, ensure_ascii=False)
    with gzip.open(frozen_dir / "index_par_acteur.json.gz", "wt", encoding="utf-8") as f:
        json.dump(frozen_index_par_acteur, f, ensure_ascii=False)
    (frozen_dir / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-13T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    cache_dir = tmp_path / "cache"
    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir),
        patch("candidate_profile.AN_AMENDEMENTS_FIGEES_DIR", tmp_path / "figees"),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        result = _download_and_build_amendement_index("15")

    assert result == frozen_index_par_acteur
    mock_get.assert_not_called()
    # Matérialisé dans le cache disque sous la forme dédupliquée (#377), en
    # clair : même contenu que le fallback committé, seule la compression
    # change — plus aucune expansion vers la forme plate.
    assert json.loads((cache_dir / "15" / "amendements.json").read_text(encoding="utf-8")) == frozen_amendements
    # Index matérialisé en tranches par acteur (#392), pas en fichier unique.
    shard = cache_dir / "15" / "index_par_acteur" / "PA1.json"
    assert shard.is_file()
    assert json.loads(shard.read_text(encoding="utf-8")) == frozen_index_par_acteur["PA1"]
    assert json.loads((cache_dir / "15" / "fraicheur.json").read_text(encoding="utf-8"))["figee"] is True

    # Et la lecture par acteur reconstitue bien l'enregistrement complet.
    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        from candidate_profile import _read_cached_amendements_acteur

        assert _read_cached_amendements_acteur("15", "PA1") == [
            {
                **frozen_amendements["AMANR5L15PO123456B0001P0D1N001"],
                "role_signataire": "auteur_principal",
            }
        ]


def test_amendements_index_deja_figee_true_when_materialized_and_figee(tmp_path):
    from candidate_profile import amendements_index_deja_figee

    cache_dir = tmp_path / "cache"
    _write_cache_amendements(cache_dir, "15", amendements={}, index_par_acteur={})
    (cache_dir / "15" / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-13T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        assert amendements_index_deja_figee("15") is True


def test_amendements_index_deja_figee_false_on_legacy_flat_cache(tmp_path):
    """Cache hérité d'avant #377 (`index_par_acteur.json` seul, forme plate) :
    ne doit PAS être considéré comme déjà figé, sinon il resterait en place
    indéfiniment sans jamais être migré vers le format compact — et resterait
    illisible pour `_read_cached_amendements_acteur`, qui exige les deux
    fichiers."""
    from candidate_profile import amendements_index_deja_figee

    cache_dir = tmp_path / "cache"
    leg_dir = cache_dir / "15"
    leg_dir.mkdir(parents=True)
    (leg_dir / "index_par_acteur.json").write_text("{}", encoding="utf-8")
    (leg_dir / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-13T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        assert amendements_index_deja_figee("15") is False


def test_amendements_index_deja_figee_false_for_non_frozen_legislature(tmp_path):
    """La législature 17 (active) n'est jamais figée, même avec un index et
    un fraicheur.json présents en cache — le code n'écrit jamais figee: true
    pour elle en pratique, mais la fonction ne doit pas en dépendre : elle
    exclut la 17 par sa seule appartenance à AN_AMENDEMENTS_LEGISLATURES_FIGEES."""
    from candidate_profile import amendements_index_deja_figee

    cache_dir = tmp_path / "cache"
    leg_dir = cache_dir / "17"
    leg_dir.mkdir(parents=True)
    (leg_dir / "index_par_acteur.json").write_text("{}", encoding="utf-8")
    (leg_dir / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-13T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        assert amendements_index_deja_figee("17") is False


def test_amendements_index_deja_figee_false_when_not_yet_materialized(tmp_path):
    from candidate_profile import amendements_index_deja_figee

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path / "cache"):
        assert amendements_index_deja_figee("15") is False


def test_amendements_index_deja_figee_does_not_read_index_par_acteur(tmp_path):
    """Ne doit jamais charger index_par_acteur.json en mémoire (c'est tout le
    point : éviter l'OOM constaté en pratique sur un gros index déjà figé) —
    un fichier JSON invalide à cet emplacement ne doit donc jamais faire
    échouer la fonction, tant que fraicheur.json est valide."""
    from candidate_profile import amendements_index_deja_figee

    cache_dir = tmp_path / "cache"
    _write_cache_amendements(cache_dir, "16", amendements={}, index_par_acteur={})
    (cache_dir / "16" / "index_par_acteur.json").write_text(
        "{ceci n'est pas du JSON valide", encoding="utf-8"
    )
    (cache_dir / "16" / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-13T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        assert amendements_index_deja_figee("16") is True


def test_download_and_build_amendement_index_frozen_legislature_falls_back_to_network_if_no_committed_index(tmp_path):
    """Une législature figée sans fallback committé (ne devrait pas arriver en
    pratique) ne doit pas lever : elle retombe simplement sur le chemin réseau
    standard, qui échoue ici normalement (aucune archive servie)."""
    from candidate_profile import AmendementsIndexError, _download_and_build_amendement_index

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path / "cache"),
        patch("candidate_profile.AN_AMENDEMENTS_FIGEES_DIR", tmp_path / "figees_absent"),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")) as mock_get,
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        try:
            _download_and_build_amendement_index("15")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    mock_get.assert_called()


def test_download_and_build_amendement_index_raises_on_download_failure(tmp_path):
    """Échec persistant (toutes les tentatives échouent) : AmendementsIndexError
    doit toujours être levée après épuisement des tentatives (non-régression #199),
    et toutes les tentatives prévues doivent avoir été consommées."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AmendementsIndexError,
        _download_and_build_amendement_index,
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")) as mock_get,
        patch("candidate_profile.time.sleep", return_value=None) as mock_sleep,
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass

    assert mock_get.call_count == _budget_appels_reseau_echec_total(), (
        "Le téléchargement doit être retenté jusqu'à épuisement du nombre de tentatives borné"
    )
    # Backoff entre chaque tentative, mais pas après la dernière (déjà en échec définitif).
    assert mock_sleep.call_count == _budget_attentes_echec_total()


def test_download_and_build_amendement_index_failed_legislature_is_not_retried_for_next_candidate(tmp_path):
    """Une législature dont le téléchargement échoue définitivement (toutes les
    tentatives épuisées) ne doit être retentée qu'une seule fois par run — pas
    une fois par appelant suivant en ayant besoin (issue #239 : régression de
    #225, où l'absence de mémoire inter-appels d'un échec transformait un
    échec instantané pré-#225 en plusieurs minutes de blocage répétées)."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AmendementsIndexError,
        _download_and_build_amendement_index,
    )

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")) as mock_get,
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        # Premier appel ayant besoin de cette législature : cycle complet de
        # tentatives (comportement de #225 préservé), puis échec définitif.
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass
        assert mock_get.call_count == _budget_appels_reseau_echec_total()

        # Second appel, même législature : échec immédiat depuis le cache
        # d'échec, sans aucun nouvel appel réseau.
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass
        assert mock_get.call_count == _budget_appels_reseau_echec_total(), (
            "Le second appel ne doit déclencher aucun nouvel appel réseau pour "
            "une législature déjà en échec définitif durant ce run"
        )


def test_download_and_build_amendement_index_failed_legislature_shared_across_jobs_via_disk_marker(tmp_path, monkeypatch):
    """Deux process Python distincts du même run (ex. deux invocations
    successives de `src/build_amendements_index.py` dans le job
    `extract-amendements-an`, ou une reprise du même run) ne doivent pas payer
    chacune le cycle complet de retry pour la même législature en échec : la
    seconde doit lever immédiatement grâce au marqueur disque partagé
    (`GITHUB_RUN_ID`), même sans mémoire process partagée (issue #246,
    extension de #239 au-delà du process courant)."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AmendementsIndexError,
        _amendements_failed_legislatures,
        _download_and_build_amendement_index,
    )

    monkeypatch.setenv("GITHUB_RUN_ID", "31685914622")

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")) as mock_get,
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        # Premier process : cycle complet de tentatives, échec définitif.
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass
        assert mock_get.call_count == _budget_appels_reseau_echec_total()

        # Simule le passage à un second process (ex. reprise du même run) : le
        # cache mémoire intra-process est réinitialisé, mais le cache disque
        # (`.cache/amendements_an/`) est le même.
        _amendements_failed_legislatures.clear()

        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass
        assert mock_get.call_count == _budget_appels_reseau_echec_total(), (
            "Le second process ne doit déclencher aucun nouvel appel réseau : le marqueur "
            "disque du run courant doit suffire à lever immédiatement"
        )


def test_download_and_build_amendement_index_disk_marker_from_different_run_is_ignored(tmp_path, monkeypatch):
    """Un marqueur disque référençant un `GITHUB_RUN_ID` différent du run courant
    (résidu d'une semaine ISO précédente restauré via `restore-keys`) doit être
    ignoré : la législature est retentée normalement, sans dépendre d'un TTL
    explicite (comportement de #239 volontairement préservé, critère
    d'acceptation de #246)."""
    from candidate_profile import (
        AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS,
        AmendementsIndexError,
        _amendements_failed_marker_path,
        _download_and_build_amendement_index,
    )

    monkeypatch.setenv("GITHUB_RUN_ID", "31694500982")

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path):
        # Le chemin du marqueur se calcule DANS le `patch`, pas avant (#791) :
        # `_amendements_failed_marker_path` dérive de `AMENDEMENTS_CACHE_DIR`,
        # donc l'appeler d'abord rendait `.cache/amendements_an/17/failed_run_id`
        # — le cache RÉEL du dépôt, que ce test créait puis écrivait. Le
        # garde-fou de #721 ne le voyait pas : il ne coupait que `builtins.open`,
        # et `Path.write_text` passe par `io.open`.
        marker_path = _amendements_failed_marker_path("17")
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text("99999999999", encoding="utf-8")  # run_id d'un run précédent

        with (
            patch("candidate_profile.requests.get", side_effect=_requests.RequestException("boom")) as mock_get,
            patch("candidate_profile.time.sleep", return_value=None),
        ):
            try:
                _download_and_build_amendement_index("17")
                assert False, "AmendementsIndexError attendue (échec réseau simulé, pas le marqueur périmé)"
            except AmendementsIndexError:
                pass

    assert mock_get.call_count == _budget_appels_reseau_echec_total(), (
        "Un marqueur d'un GITHUB_RUN_ID différent doit être ignoré : cycle complet de "
        "tentatives réseau attendu, pas un échec immédiat depuis le marqueur périmé"
    )


def test_download_and_build_amendement_index_retries_transient_failure_then_succeeds(tmp_path):
    """Un échec réseau transitoire isolé (ex. un seul IncompleteRead/RequestException)
    ne doit plus faire échouer la construction de l'index si une tentative suivante
    aboutit — c'est le comportement central demandé par #220."""
    import io
    import zipfile as zipfile_module

    from candidate_profile import _download_and_build_amendement_index

    buf = io.BytesIO()
    with zipfile_module.ZipFile(buf, "w") as zf:
        pass  # zip valide mais vide : suffisant pour vérifier l'absence d'erreur
    valid_zip_bytes = buf.getvalue()

    class FakeStreamResponse(_FluxFactice):
        # status_code=200 (au lieu de 206) simule un serveur qui ignore l'en-tête
        # Range et renvoie le fichier entier en un seul segment — suffisant ici
        # puisque ce test porte sur le retry transitoire, pas sur le découpage
        # par plages (voir test_download_amendements_zip_retries_only_failed_segment
        # pour le retry ciblé d'un seul segment médian).
        status_code = 200

        def __init__(self, payload: bytes):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield self._payload

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch(
            "candidate_profile.requests.get",
            side_effect=[
                _requests.RequestException("IncompleteRead(16779130 bytes read, 346527232 more expected)"),
                FakeStreamResponse(valid_zip_bytes),
            ],
        ) as mock_get,
        patch("candidate_profile.time.sleep", return_value=None) as mock_sleep,
    ):
        index = _download_and_build_amendement_index("17")

    assert index == {}
    assert mock_get.call_count == 2, "Un seul échec transitoire suivi d'un succès : exactement 2 tentatives"
    assert mock_sleep.call_count == 1, "Backoff attendu une seule fois, entre l'échec et la tentative réussie"


def test_download_and_build_amendement_index_raises_on_bad_zip(tmp_path):
    import zipfile

    from candidate_profile import AmendementsIndexError, _download_and_build_amendement_index

    class FakeStreamResponse(_FluxFactice):
        status_code = 200  # fichier entier en un seul segment, voir commentaire ci-dessus

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield b"not a valid zip archive"

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=FakeStreamResponse()),
    ):
        try:
            _download_and_build_amendement_index("17")
            assert False, "AmendementsIndexError attendue"
        except AmendementsIndexError:
            pass
        except zipfile.BadZipFile:
            assert False, "BadZipFile ne doit pas être avalée : elle doit être reconvertie en AmendementsIndexError"


def test_download_amendements_zip_retries_only_failed_segment(tmp_path):
    """Une coupure mi-flux sur un segment ne doit retenter que ce segment — pas
    tout le fichier (critère d'acceptation de l'issue #241)."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"  # 12 octets, découpés en segments de 4 -> 3 segments
    calls: list[str] = []

    class FakeRangeResponse(_FluxFactice):
        def __init__(self, data: bytes, total: int):
            self._data = data
            self.status_code = 206
            self.headers = {"Content-Range": f"bytes 0-0/{total}"}

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield self._data

    def fake_get(url, headers=None, timeout=None, stream=None):
        range_value = headers["Range"]
        calls.append(range_value)
        start, end = (int(x) for x in range_value.removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        # Échec transitoire simulé une seule fois, sur le segment médian (offset 4).
        if start == 4 and calls.count("bytes=4-7") == 1:
            raise _requests.RequestException("IncompleteRead simulée mi-segment")
        return FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.get", side_effect=fake_get),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        zip_path = tmp_path / "amendements.zip"
        _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")

    assert zip_path.read_bytes() == payload, "Le fichier reconstitué doit être identique octet pour octet"
    assert calls.count("bytes=0-3") == 1, "Le premier segment (déjà réussi) ne doit pas être re-demandé"
    assert calls.count("bytes=4-7") == 2, "Seul le segment en échec doit être retenté"
    assert calls.count("bytes=8-11") == 1, "Le dernier segment ne doit être demandé qu'une fois"


# ---------------------------------------------------------------------------
# Reprise entre deux invocations (fichier partiel déjà sur disque avant même
# le premier appel à `_download_amendements_zip` — pas seulement entre deux
# segments d'une même invocation, cf. test ci-dessus).
# ---------------------------------------------------------------------------

class _FakeHeadResponse:
    def __init__(self, content_length):
        self.headers = {} if content_length is None else {"Content-Length": str(content_length)}

    def raise_for_status(self):
        pass


class _FakeRangeResponse(_FluxFactice):
    def __init__(self, data: bytes, total: int):
        self._data = data
        self.status_code = 206
        self.headers = {"Content-Range": f"bytes 0-0/{total}"}

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=1024 * 1024):
        yield self._data


def test_download_amendements_zip_resumes_from_existing_partial_file(tmp_path):
    """Un fichier partiel déjà présent sur disque (interruption d'une invocation
    précédente du script) doit être repris à partir de l'octet déjà écrit, pas
    retéléchargé depuis le début."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"  # 12 octets, segments de 4
    zip_path = tmp_path / "amendements.zip"
    zip_path.write_bytes(payload[:4])  # premier segment déjà présent sur disque

    calls: list[str] = []

    def fake_get(url, headers=None, timeout=None, stream=None):
        range_value = headers["Range"]
        calls.append(range_value)
        start, end = (int(x) for x in range_value.removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        return _FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.head", return_value=_FakeHeadResponse(len(payload))),
        patch("candidate_profile.requests.get", side_effect=fake_get),
    ):
        _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")

    assert zip_path.read_bytes() == payload, "Le fichier final doit être identique octet pour octet"
    assert "bytes=0-3" not in calls, "Le segment déjà présent sur disque ne doit jamais être redemandé"
    assert calls.count("bytes=4-7") == 1
    assert calls.count("bytes=8-11") == 1


def test_download_amendements_zip_chunk_bytes_param_overrides_module_default(tmp_path):
    """Le paramètre explicite `chunk_bytes` doit primer sur
    `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES` — utilisé par `--chunk-size-mb` pour
    réduire la taille de segment sans toucher au défaut partagé avec le
    chemin réseau de la législature 17 (voir docstring de la fonction, ajout
    du 14/08/2026)."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"  # 12 octets
    zip_path = tmp_path / "amendements.zip"
    calls: list[str] = []

    def fake_get(url, headers=None, timeout=None, stream=None):
        range_value = headers["Range"]
        calls.append(range_value)
        start, end = (int(x) for x in range_value.removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        return _FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.get", side_effect=fake_get),
    ):
        _download_amendements_zip(
            "https://example.test/amendements.zip", zip_path, "17", chunk_bytes=2,
        )

    assert zip_path.read_bytes() == payload
    assert calls == ["bytes=0-1", "bytes=2-3", "bytes=4-5", "bytes=6-7", "bytes=8-9", "bytes=10-11"], (
        "Les segments doivent suivre chunk_bytes=2, pas AMENDEMENTS_DOWNLOAD_CHUNK_BYTES=4"
    )


def test_download_amendements_zip_max_attempts_param_overrides_module_default(tmp_path):
    """Le paramètre explicite `max_attempts` doit primer sur
    `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS` — utilisé par `--max-attempts` pour
    augmenter le nombre de tentatives par segment sans toucher au défaut
    partagé avec le chemin réseau de la législature 17."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"  # 12 octets, segments de 4 -> 3 segments
    zip_path = tmp_path / "amendements.zip"
    attempts_for_middle_segment = 0

    def fake_get(url, headers=None, timeout=None, stream=None):
        nonlocal attempts_for_middle_segment
        start, end = (int(x) for x in headers["Range"].removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        if start == 4:
            attempts_for_middle_segment += 1
            if attempts_for_middle_segment < 4:
                raise _requests.RequestException("IncompleteRead simulée")
        return _FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS", 2),
        patch("candidate_profile.requests.get", side_effect=fake_get),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        _download_amendements_zip(
            "https://example.test/amendements.zip", zip_path, "17", max_attempts=5,
        )

    assert zip_path.read_bytes() == payload, (
        "Avec max_attempts=5 (> AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS=2 patché), le segment "
        "qui échoue 3 fois avant de réussir à la 4e doit tout de même aboutir"
    )
    assert attempts_for_middle_segment == 4


def test_download_amendements_zip_skips_entirely_when_already_complete(tmp_path):
    """Un fichier partiel dont la taille locale correspond déjà à la taille
    distante (téléchargement complet mais échec précédent avant l'écriture de
    `fraicheur.json`, par exemple) ne doit déclencher aucune requête de
    téléchargement — seulement la sonde de taille."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"
    zip_path = tmp_path / "amendements.zip"
    zip_path.write_bytes(payload)

    with (
        patch("candidate_profile.requests.head", return_value=_FakeHeadResponse(len(payload))) as mock_head,
        patch("candidate_profile.requests.get") as mock_get,
    ):
        _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")

    mock_head.assert_called_once()
    mock_get.assert_not_called()
    assert zip_path.read_bytes() == payload, "Le fichier local complet ne doit pas être altéré"


def test_download_amendements_zip_restarts_from_scratch_when_probe_fails(tmp_path):
    """Si la sonde de taille distante échoue (réseau indisponible, etc.), reprendre
    un fichier partiel serait une supposition risquée : redémarrer proprement
    depuis le début plutôt que de deviner un offset."""
    from candidate_profile import _download_amendements_zip

    zip_path = tmp_path / "amendements.zip"
    zip_path.write_bytes(b"donnees-partielles-potentiellement-perimees")

    payload = b"0123456789AB"
    calls: list[str] = []

    def fake_get(url, headers=None, timeout=None, stream=None):
        range_value = headers["Range"]
        calls.append(range_value)
        start, end = (int(x) for x in range_value.removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        return _FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.head", side_effect=_requests.RequestException("HEAD indisponible")),
        patch("candidate_profile.requests.get", side_effect=fake_get),
    ):
        _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")

    assert zip_path.read_bytes() == payload, "Le fichier doit être entièrement reconstruit depuis le début"
    assert calls[0] == "bytes=0-3", "Le tout premier segment doit être redemandé (aucune reprise sans sonde fiable)"


def test_download_amendements_zip_restarts_from_scratch_when_local_size_exceeds_remote(tmp_path):
    """Un fichier local plus gros que la taille distante annoncée est incohérent
    (archive locale corrompue/périmée) : redémarrer depuis le début plutôt que
    de traiter ça comme "déjà complet" ou de reprendre à un offset invalide."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"
    zip_path = tmp_path / "amendements.zip"
    zip_path.write_bytes(payload + b"EXTRA-INCOHERENT")  # plus gros que `payload`

    calls: list[str] = []

    def fake_get(url, headers=None, timeout=None, stream=None):
        range_value = headers["Range"]
        calls.append(range_value)
        start, end = (int(x) for x in range_value.removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        return _FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.head", return_value=_FakeHeadResponse(len(payload))),
        patch("candidate_profile.requests.get", side_effect=fake_get),
    ):
        _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")

    assert zip_path.read_bytes() == payload, "Le fichier incohérent doit être écrasé, pas conservé ni complété"
    assert calls[0] == "bytes=0-3"


def test_download_amendements_zip_raises_instead_of_corrupting_on_unexpected_200_mid_resume(tmp_path):
    """Si le serveur répond 200 (Range ignoré) alors qu'un offset non nul était
    demandé (reprise ou segment ultérieur), écrire cette réponse corromprait
    l'archive (contenu dupliqué à partir de l'octet 0, décalé par rapport à ce
    qui est déjà sur disque) — doit lever plutôt qu'écrire silencieusement."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"
    zip_path = tmp_path / "amendements.zip"
    zip_path.write_bytes(payload[:4])

    class FakeFullResponse(_FluxFactice):
        status_code = 200
        headers: dict = {}

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size=1024 * 1024):
            yield payload  # renvoie tout le fichier depuis l'octet 0, en ignorant Range

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.head", return_value=_FakeHeadResponse(len(payload))),
        patch("candidate_profile.requests.get", return_value=FakeFullResponse()),
        patch("candidate_profile.time.sleep", return_value=None),
    ):
        try:
            _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")
            assert False, "OSError attendue au lieu d'une écriture silencieuse corrompue"
        except OSError:
            pass

    assert zip_path.read_bytes() == payload[:4], "Le fichier partiel existant ne doit pas être corrompu"


def test_download_amendements_zip_prints_progress_on_success(tmp_path, capsys):
    """Chaque segment écrit avec succès doit produire une ligne de progression
    (octets/total, pourcentage), pas seulement les échecs/retries — sinon une
    invocation avec de petits `chunk_bytes` reste silencieuse pendant des
    minutes et ressemble à un blocage (voir docstring, ajout du 15/08/2026)."""
    from candidate_profile import _download_amendements_zip

    payload = b"0123456789AB"  # 12 octets, segments de 4 -> 3 segments
    zip_path = tmp_path / "amendements.zip"

    def fake_get(url, headers=None, timeout=None, stream=None):
        start, end = (int(x) for x in headers["Range"].removeprefix("bytes=").split("-"))
        end = min(end, len(payload) - 1)
        return _FakeRangeResponse(payload[start : end + 1], len(payload))

    with (
        patch("candidate_profile.AMENDEMENTS_DOWNLOAD_CHUNK_BYTES", 4),
        patch("candidate_profile.requests.get", side_effect=fake_get),
    ):
        _download_amendements_zip("https://example.test/amendements.zip", zip_path, "17")

    out = capsys.readouterr().out
    assert out.count("écrit") == 3, "Une ligne de progression par segment réussi (3 segments)"
    assert "4/12" in out and "8/12" in out and "12/12" in out
    assert "100.0%" in out


def test_fetch_amendements_officiels_legislature_failure_does_not_erase_others():
    """Légis 17 en cache + les autres législatures absentes du cache : les
    amendements de la légis 17 doivent être conservés (plus de vidage global
    sur l'absence d'une seule législature), et chaque absence doit être
    tracée avec la législature concernée dans les warnings (critères
    d'acceptation de l'issue #241, adaptés à la lecture cache-only de #252 :
    plus d'`AmendementsIndexError`, une législature absente du cache retourne
    simplement `None`)."""
    from candidate_profile import (
        AN_AMENDEMENTS_PATH,
        WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
        fetch_amendements_officiels,
    )

    def fake_records(legislature, acteur_ref):
        if legislature == "17":
            return [{"numero": "1", "date": "2024-01-01", "texte_vise": "T1", "sort": None}]
        return None

    warnings: list[str] = []
    with (
        patch("candidate_profile._read_cached_amendements_acteur", side_effect=fake_records),
        patch("candidate_profile._extract_acteur_ref", return_value="PA1"),
    ):
        amendements = fetch_amendements_officiels("https://www.assemblee-nationale.fr/dyn/deputes/PA1", warnings)

    assert len(amendements) == 1, "Les amendements de la législature en cache (17) doivent être conservés"
    assert amendements[0]["legislature"] == "17"

    autres_legislatures = [leg for leg in AN_AMENDEMENTS_PATH if leg != "17"]
    failure_warnings = [w for w in warnings if w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES)]
    assert len(failure_warnings) == len(autres_legislatures), (
        "Un warning distinct par législature absente, pas un échec global"
    )
    for leg in autres_legislatures:
        assert any(leg in w for w in failure_warnings), f"Le warning doit mentionner spécifiquement la législature {leg}"


def test_fetch_amendements_officiels_never_triggers_network_when_cache_absent(tmp_path):
    """Critère d'acceptation central de l'issue #252 : quand l'index en cache est
    absent pour toutes les législatures, `fetch_amendements_officiels` ne doit
    déclencher aucun appel réseau (mocké) — seulement le warning existant."""
    from candidate_profile import (
        AN_AMENDEMENTS_PATH,
        WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
        fetch_amendements_officiels,
    )

    warnings: list[str] = []
    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
        patch("candidate_profile._extract_acteur_ref", return_value="PA1"),
    ):
        amendements = fetch_amendements_officiels("https://www.assemblee-nationale.fr/dyn/deputes/PA1", warnings)

    assert amendements == []
    mock_get.assert_not_called()
    failure_warnings = [w for w in warnings if w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES)]
    assert len(failure_warnings) == len(AN_AMENDEMENTS_PATH), (
        "Un warning par législature absente du cache, aucune tentative réseau"
    )


def test_fetch_amendements_officiels_warns_when_acteur_ref_missing():
    """#265 (fix 5) : un `url_an_ou_senat` absent ou non parsable ne doit plus
    produire un zéro parfaitement silencieux, indiscernable d'une absence
    légitime d'amendements. Cet appel n'ayant lieu que pour `chambre ==
    "deputes"` (voir `build_profile`), l'impossibilité d'extraire un acteurRef
    est toujours une anomalie — constatée en pratique sur des profils dont
    l'identité avait été écrite partiellement par un run interrompu."""
    from candidate_profile import (
        WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
        fetch_amendements_officiels,
    )

    for url in (None, "https://example.org/pas-de-acteur-ref"):
        warnings: list[str] = []
        amendements = fetch_amendements_officiels(url, warnings)

        assert amendements == []
        assert any(w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES) for w in warnings), (
            f"Un zéro dû à un acteurRef introuvable doit être tracé (url={url!r})"
        )


def test_fetch_amendements_officiels_missing_acteur_ref_without_warnings_list_does_not_raise():
    """`warnings` est optionnel : l'absence d'acteurRef ne doit pas lever quand
    l'appelant ne fournit pas de liste (non-régression de la signature)."""
    from candidate_profile import fetch_amendements_officiels

    assert fetch_amendements_officiels(None) == []


def test_fetch_amendements_officiels_returns_cached_amendements_when_index_present(tmp_path):
    """Quand l'index est présent en cache pour une législature, les amendements
    de l'acteur doivent être retournés — identique au comportement actuel,
    sans passer par un téléchargement (critère d'acceptation de l'issue #252)."""
    from candidate_profile import AN_AMENDEMENTS_PATH as _LEGISLATURES
    from candidate_profile import fetch_amendements_officiels

    legislature = next(iter(_LEGISLATURES))
    _write_cache_amendements(
        tmp_path,
        legislature,
        amendements={"U1": {"uid": "U1", "numero": "1", "date": "2024-01-01",
                            "texte_vise": "T1", "sort": None}},
        index_par_acteur={"PA1": [{"uid": "U1", "role_signataire": "auteur_principal"}]},
    )

    warnings: list[str] = []
    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
        patch("candidate_profile._extract_acteur_ref", return_value="PA1"),
    ):
        amendements = fetch_amendements_officiels("https://www.assemblee-nationale.fr/dyn/deputes/PA1", warnings)

    mock_get.assert_not_called()
    matching = [a for a in amendements if a["legislature"] == legislature]
    assert len(matching) == 1
    assert matching[0]["numero"] == "1"


# ---------------------------------------------------------------------------
# #562 — la date `xsi:nil` des amendements, et le TypeError qu'elle levait
# ---------------------------------------------------------------------------

#: Le marqueur XML tel qu'il arrive dans l'open data AN converti en JSON : un
#: élément vide n'y devient pas `null`, il devient un OBJET.
NIL_AN = {"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "@xsi:nil": "true"}


def test_texte_an_lit_le_marqueur_xsi_nil_comme_une_donnee_manquante():
    """Une valeur `xsi:nil` n'est pas une donnée : c'est une donnée manquante,
    et le pivot l'écrit `null` (AGENTS.md §2.5). Troisième occurrence de
    l'idiome dans ce dépôt après `identite.uri_hatvp` (#539)."""
    from candidate_profile import _texte_an

    assert _texte_an(NIL_AN) is None
    assert _texte_an("2024-01-01") == "2024-01-01"
    assert _texte_an("") is None
    assert _texte_an(None) is None


def test_parse_amendement_entry_normalise_une_date_de_depot_nil():
    """Schéma moderne (légis 15/16/17) : `cycleDeVie.dateDepot` nil ne doit pas
    entrer tel quel dans l'enregistrement pivot."""
    from candidate_profile import _parse_amendement_entry

    entrees = _parse_amendement_entry({"amendement": {
        "uid": "U1",
        "texteLegislatifRef": "PRJLANR5L16B0274",
        "signataires": {"auteur": {"acteurRef": "PA1", "typeAuteur": "Député"}},
        "cycleDeVie": {"dateDepot": NIL_AN},
        "identification": {"numeroLong": "12"},
    }})

    assert entrees is not None
    assert entrees[0][1]["date"] is None


def test_parse_amendement_legacy_normalise_une_date_de_depot_nil():
    """Même règle sur le schéma legacy de la XIVe (#299) : la source change de
    forme, pas la règle."""
    from candidate_profile import _parse_amendement_legacy_single

    entrees = _parse_amendement_legacy_single(
        {
            "uid": "U1",
            "signataires": {"auteur": {"acteurRef": "PA1", "typeAuteur": "Député"}},
            "dateDepot": NIL_AN,
            "numeroLong": "7 (Rect)",
        },
        "PRJLANR5L14B0001",
    )

    assert entrees[0][1]["date"] is None


def test_fetch_amendements_officiels_tolere_une_date_xsi_nil_en_cache(tmp_path):
    """**Le défaut de #562**, et le seul test qui le tienne vraiment.

    `'<' not supported between instances of 'dict' and 'str'` : le tri par date
    de `fetch_amendements_officiels` recevait le marqueur `xsi:nil` d'un
    `dateDepot` absent. 8 amendements sur les 624 180 des trois législatures
    figées le portent — mais ils sont cosignés, et **99 profils publiés sur
    481** perdaient de ce fait la totalité de leurs amendements.

    La normalisation est vérifiée **à la lecture du cache**, et c'est le point :
    les index des trois législatures figées sont COMMITTÉS et ne sont pas
    reconstruits par la CI. Un correctif limité au parsing laisserait le corpus
    cassé jusqu'à un rejeu manuel de `build_amendements_index_figees.py` sur
    350-650 Mo d'archives.
    """
    from candidate_profile import AN_AMENDEMENTS_PATH as _LEGISLATURES
    from candidate_profile import fetch_amendements_officiels

    legislature = next(iter(_LEGISLATURES))
    _write_cache_amendements(
        tmp_path,
        legislature,
        amendements={
            "U1": {"uid": "U1", "numero": "1", "date": NIL_AN, "texte_vise": "T1", "sort": None},
            "U2": {"uid": "U2", "numero": "2", "date": "2024-01-01", "texte_vise": "T2", "sort": None},
        },
        index_par_acteur={"PA1": [
            {"uid": "U1", "role_signataire": "cosignataire"},
            {"uid": "U2", "role_signataire": "auteur_principal"},
        ]},
    )

    warnings: list[str] = []
    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
        patch("candidate_profile._extract_acteur_ref", return_value="PA1"),
    ):
        amendements = fetch_amendements_officiels(
            "https://www.assemblee-nationale.fr/dyn/deputes/PA1", warnings
        )

    mock_get.assert_not_called()
    assert len(amendements) == 2, "aucun amendement ne doit être perdu par une date absente"
    par_uid = {a["uid"]: a for a in amendements}
    assert par_uid["U1"]["date"] is None, "une date `xsi:nil` se publie `null`, pas en objet"
    assert par_uid["U2"]["date"] == "2024-01-01"
    assert amendements[0]["uid"] == "U2", "l'amendement daté reste en tête du tri décroissant"
    # Les autres législatures n'ont pas de cache dans ce tmp_path et le disent :
    # ce sont des absences d'index, pas des exceptions. Aucune ne doit porter la
    # trace d'un défaut de code.
    assert not any("not supported between instances" in w for w in warnings)
    assert not any(f"(législature {legislature})" in w for w in warnings), (
        "la législature effectivement en cache n'a rien à signaler"
    )


def test_build_profile_defaut_de_code_nest_pas_une_panne_de_source():
    """#562 — un `TypeError` du dépôt ne doit plus être publié comme une
    indisponibilité de l'Assemblée nationale.

    C'est le défaut éditorial, indépendant du précédent : même le TypeError
    corrigé, la prochaine exception repasserait par le même chemin. Le préfixe
    de panne est réservé aux exceptions qui disent quelque chose de la source
    (`ERREURS_SOURCE`) ; tout le reste parle de nous, et le dit."""
    from candidate_profile import (
        WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
        WARNING_PREFIX_DEFAUT_COLLECTE,
    )

    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch(
            "candidate_profile.fetch_amendements_officiels",
            side_effect=TypeError("'<' not supported between instances of 'dict' and 'str'"),
        ),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        raw_profile = build_profile("deputes", "jean-dupont")

    warnings = raw_profile["meta"]["warnings"]
    assert any(w.startswith(WARNING_PREFIX_DEFAUT_COLLECTE) for w in warnings), (
        "un défaut de code doit être nommé comme tel dans meta.warnings"
    )
    assert not any(w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES) for w in warnings), (
        "aucune source n'était en défaut : rien n'autorise à déclarer les "
        "amendements indisponibles côté Assemblée nationale"
    )
    assert "amendements" in " ".join(
        w for w in warnings if w.startswith(WARNING_PREFIX_DEFAUT_COLLECTE)
    ), "le warning doit nommer la liste condamnée, sinon la couverture ne peut pas le router"


def test_build_profile_amendements_fetch_failure_is_tracked_in_warnings():
    """Quand fetch_amendements_officiels échoue de façon inattendue (ex. exception
    propagée), le try/except de build_profile doit ajouter un warning
    WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES — au lieu de silencieusement laisser
    profile['amendements'] absent/vide sans trace."""
    from candidate_profile import AmendementsIndexError, WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES

    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug",
              return_value=_identite_an_resolue()),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch(
            "candidate_profile.fetch_amendements_officiels",
            side_effect=AmendementsIndexError("échec du téléchargement (boom)"),
        ),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        raw_profile = build_profile("deputes", "jean-dupont")

    amendements_warnings = [
        w for w in raw_profile["meta"]["warnings"] if w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES)
    ]
    assert amendements_warnings, (
        "Un échec de collecte des amendements officiels doit être tracé dans meta.warnings, "
        "pas avalé silencieusement"
    )
    # #562 : le tri des deux branches se vérifie dans les DEUX sens. Une
    # `AmendementsIndexError` dit bien que la source AN n'a pas délivré son
    # archive — elle reste une panne, et ne doit pas basculer côté « défaut du
    # dépôt » sous prétexte qu'on y a ajouté une branche.
    from candidate_profile import WARNING_PREFIX_DEFAUT_COLLECTE

    assert not any(
        w.startswith(WARNING_PREFIX_DEFAUT_COLLECTE) for w in raw_profile["meta"]["warnings"]
    ), "un échec de la source n'est pas un défaut de notre code"


# ---------------------------------------------------------------------------
# Tests pour _build_organe_index / fetch_organe (issue #353) : index
# organeRef -> {sigle, nom, type} construit depuis json/organe/*.json du zip
# bulk historique des acteurs/mandats/organes, sans filtrage par codeType
# (contrairement à _build_organe_positions_index, limité à GP/GOUVERNEMENT).
# ---------------------------------------------------------------------------

def _make_fake_acteurs_historique_zip_bytes(organe_entries, acteur_entries=None):
    """Construit en mémoire un zip minimal imitant AN_ACTEURS_HISTORIQUE_ZIP_URL :
    `organe_entries` est un mapping organeRef -> dict organe (ex. {"uid": ...,
    "codeType": ..., "libelle": ..., "libelleAbrege": ...}), `acteur_entries`
    un mapping acteurRef -> dict acteur, tous deux écrits sous
    json/organe/{ref}.json et json/acteur/{ref}.json respectivement."""
    import io
    import zipfile as zipfile_module

    buf = io.BytesIO()
    with zipfile_module.ZipFile(buf, "w") as zf:
        for organe_ref, organe in organe_entries.items():
            zf.writestr(f"json/organe/{organe_ref}.json", json.dumps({"organe": organe}, ensure_ascii=False))
        for acteur_ref, acteur in (acteur_entries or {}).items():
            zf.writestr(f"json/acteur/{acteur_ref}.json", json.dumps({"acteur": acteur}, ensure_ascii=False))
    return buf.getvalue()


class _FakeActeursHistoriqueStreamResponse(_FluxFactice):
    status_code = 200

    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size=1024 * 1024):
        yield self._payload


def test_build_organe_index_parses_all_organe_types(tmp_path):
    """L'index doit couvrir tous les codeType sans filtrage (commissions,
    groupes politiques, groupes d'amitié...), contrairement à
    _build_organe_positions_index limité à GP/GOUVERNEMENT — c'est tout
    l'objet de l'issue #353. Les entrées json/acteur/*.json du même zip
    doivent être ignorées (préfixe de chemin différent)."""
    from candidate_profile import _build_organe_index

    organe_entries = {
        "PO59048": {
            "uid": "PO59048",
            "codeType": "COMPER",
            "libelle": "Commission des finances, de l'économie générale et du contrôle budgétaire",
            "libelleAbrege": "Finances",
        },
        "PO845401": {
            "uid": "PO845401",
            "codeType": "GP",
            "libelle": "Rassemblement National",
            "libelleAbrege": "RN",
        },
        "PO393167": {
            "uid": "PO393167",
            "codeType": "GA",
            "libelle": "France-Malaisie",
            "libelleAbrege": "Malaisie",
        },
    }
    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries, acteur_entries={"PA1": {"uid": "PA1"}}
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        index = _build_organe_index()

    assert index == {
        "PO59048": {
            "sigle": "Finances",
            "nom": "Commission des finances, de l'économie générale et du contrôle budgétaire",
            "type": "COMPER",
        },
        "PO845401": {"sigle": "RN", "nom": "Rassemblement National", "type": "GP"},
        "PO393167": {"sigle": "Malaisie", "nom": "France-Malaisie", "type": "GA"},
    }


def test_build_organe_index_uses_disk_cache_without_download(tmp_path):
    """Un index déjà présent sur disque (cache) est utilisé tel quel, sans
    nouvel appel réseau."""
    from candidate_profile import _build_organe_index

    cached_index = {"PO59048": {"sigle": "Finances", "nom": "Commission des finances", "type": "COMPER"}}
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / candidate_profile.NOM_INDEX_ORGANES).write_text(json.dumps(cached_index, ensure_ascii=False), encoding="utf-8")

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        index = _build_organe_index()

    mock_get.assert_not_called()
    assert index == cached_index


# ── Mémo intra-process des index dérivés du zip AMO30 (#467) ────────────────
# Le cache disque évitait le re-TÉLÉCHARGEMENT, jamais le re-PARSING : chaque
# appel relisait son `index_*.json`. Mesuré sur les 24 membres du shard 0 du
# run 32288588518 rejoués en local : 2 255 appels à `fetch_organe`, 59,8 s de
# relecture sur 88,8 s de temps mur. Ces tests verrouillent le remède ET son
# effet de bord dangereux (un mémo global qui ferait fuiter l'index d'un test
# dans le suivant — le piège qui avait fait reverter la mémoïsation de #377).


def test_index_historique_lu_une_seule_fois_par_process(tmp_path):
    """Le deuxième appel ne relit pas le fichier : c'est tout l'objet du mémo.

    Vérifié en RENDANT LE DISQUE MENTEUR entre les deux appels — si le second
    relisait, il verrait le nouveau contenu."""
    from candidate_profile import _build_organe_index

    chemin = tmp_path / candidate_profile.NOM_INDEX_ORGANES
    premier = {"PO59048": {"sigle": "Finances", "nom": "Commission des finances", "type": "COMPER"}}
    chemin.write_text(json.dumps(premier, ensure_ascii=False), encoding="utf-8")

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        assert _build_organe_index() == premier
        chemin.write_text(json.dumps({"PO1": {"sigle": "X", "nom": "X", "type": "GA"}}), encoding="utf-8")
        assert _build_organe_index() == premier
        chemin.unlink()
        assert _build_organe_index() == premier

    mock_get.assert_not_called()


def test_index_historique_memoise_par_chemin_pas_globalement(tmp_path):
    """Deux répertoires de cache distincts ne partagent pas leur mémo.

    C'est la propriété qui rend la mémoïsation sûre en test : chaque cas patche
    `ACTEURS_HISTORIQUE_CACHE_DIR` vers son propre `tmp_path`. Un mémo indexé
    par nom logique ferait lire au second l'index du premier."""
    from candidate_profile import _build_organe_index

    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    index_a = {"PO59048": {"sigle": "Finances", "nom": "Commission des finances", "type": "COMPER"}}
    index_b = {"PO393167": {"sigle": "Malaisie", "nom": "France-Malaisie", "type": "GA"}}
    (a / candidate_profile.NOM_INDEX_ORGANES).write_text(json.dumps(index_a, ensure_ascii=False), encoding="utf-8")
    (b / candidate_profile.NOM_INDEX_ORGANES).write_text(json.dumps(index_b, ensure_ascii=False), encoding="utf-8")

    with patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", a):
        assert _build_organe_index() == index_a
    with patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", b):
        assert _build_organe_index() == index_b


def test_purge_du_memo_index_historique_rend_la_relecture(tmp_path):
    """La purge explicite (fixture autouse) restaure bien la relecture disque —
    sans quoi le garde-fou ci-dessus protégerait un mécanisme inerte."""
    from candidate_profile import _build_organe_index, _clear_acteurs_historique_index_memo

    chemin = tmp_path / candidate_profile.NOM_INDEX_ORGANES
    premier = {"PO59048": {"sigle": "Finances", "nom": "Commission des finances", "type": "COMPER"}}
    second = {"PO1": {"sigle": "X", "nom": "X", "type": "GA"}}
    chemin.write_text(json.dumps(premier, ensure_ascii=False), encoding="utf-8")

    with patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path):
        assert _build_organe_index() == premier
        chemin.write_text(json.dumps(second, ensure_ascii=False), encoding="utf-8")
        _clear_acteurs_historique_index_memo()
        assert _build_organe_index() == second


def test_index_historique_memoise_apres_construction_depuis_le_zip(tmp_path):
    """Le mémo est alimenté aussi par le chemin « construction depuis le zip »,
    pas seulement par la relecture du cache disque : sinon le tout premier
    candidat d'un run paierait un parsing de plus que les suivants."""
    from candidate_profile import _build_organe_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes({
        "PO59048": {"uid": "PO59048", "codeType": "COMPER",
                    "libelle": "Commission des finances", "libelleAbrege": "Finances"},
    })

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get",
              return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        premier = _build_organe_index()
        (tmp_path / candidate_profile.NOM_INDEX_ORGANES).unlink()
        assert _build_organe_index() is premier


def test_build_organe_index_download_failure_returns_empty(tmp_path):
    """Un échec réseau lors du téléchargement du zip bulk est non-fatal :
    l'index retourné est {}, sans exception propagée."""
    from candidate_profile import _build_organe_index
    import requests as _requests_module

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests_module.RequestException("boom")),
    ):
        index = _build_organe_index()

    assert index == {}


def test_fetch_organe_resolves_known_ref_and_returns_none_otherwise(tmp_path):
    """fetch_organe résout un organeRef connu vers {sigle, nom, type}, et
    retourne None pour un organeRef vide/absent ou inconnu du référentiel."""
    from candidate_profile import fetch_organe

    zip_bytes = _make_fake_acteurs_historique_zip_bytes({
        "PO59048": {
            "uid": "PO59048",
            "codeType": "COMPER",
            "libelle": "Commission des finances",
            "libelleAbrege": "Finances",
        },
    })

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        assert fetch_organe("PO59048") == {"sigle": "Finances", "nom": "Commission des finances", "type": "COMPER"}
        assert fetch_organe("PO_INCONNU") is None
        assert fetch_organe(None) is None
        assert fetch_organe("") is None


def test_acteurs_historique_zip_downloaded_once_and_shared_across_indexes(tmp_path):
    """_build_organe_index et _build_acteur_positions_hemicycle_index partagent
    le même zip bulk (AN_ACTEURS_HISTORIQUE_ZIP_URL) via
    _ensure_acteurs_historique_zip_downloaded : un seul téléchargement, même
    si les deux index sont construits dans la même exécution (issue #353 —
    "aucune dépendance amont — travail indépendant sur la même archive déjà
    en cache")."""
    from candidate_profile import _build_acteur_positions_hemicycle_index, _build_organe_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={
            "PO845401": {
                "uid": "PO845401",
                "codeType": "GP",
                "libelle": "Rassemblement National",
                "libelleAbrege": "RN",
                "positionPolitique": "Opposition",
            },
        },
        acteur_entries={
            "PA1": {
                "uid": {"#text": "PA1"},
                "mandats": {
                    "mandat": [
                        {
                            "typeOrgane": "GP",
                            "organes": {"organeRef": "PO845401"},
                            "legislature": "16",
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        }
                    ]
                },
            }
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)) as mock_get,
    ):
        organe_index = _build_organe_index()
        hemicycle_index = _build_acteur_positions_hemicycle_index()

    assert mock_get.call_count == 1, "Le zip bulk ne doit être téléchargé qu'une seule fois, partagé entre les deux index"
    assert organe_index["PO845401"]["sigle"] == "RN"
    assert hemicycle_index["PA1"][0]["groupe_sigle"] == "RN"


# ---------------------------------------------------------------------------
# Tests pour _build_acteur_identite_index / fetch_identite_officielle (issue
# #354, sous-issue 3/6 de #351) : bascule de AMO10 (actifs uniquement) vers le
# même zip bulk historique AMO30 que _build_organe_index /
# _build_acteur_positions_hemicycle_index, pour couvrir les élu⋅e⋅s dont le
# mandat est terminé.
# ---------------------------------------------------------------------------

def test_select_mandat_assemblee_courant_prefers_mandat_en_cours():
    """Parmi plusieurs mandats ASSEMBLEE (réélections successives), celui sans
    dateFin (en cours) doit toujours être préféré, quel que soit l'ordre."""
    from candidate_profile import _select_mandat_assemblee_courant

    mandats = [
        {"typeOrgane": "ASSEMBLEE", "dateDebut": "2017-06-21", "dateFin": "2022-06-21", "legislature": "15"},
        {"typeOrgane": "ASSEMBLEE", "dateDebut": "2024-07-08", "dateFin": None, "legislature": "17"},
        {"typeOrgane": "ASSEMBLEE", "dateDebut": "2022-06-22", "dateFin": "2024-06-09", "legislature": "16"},
    ]
    best = _select_mandat_assemblee_courant(mandats)
    assert best["legislature"] == "17"


def test_select_mandat_assemblee_courant_falls_back_to_most_recent_dateDebut():
    """Sans mandat en cours (élu dont le mandat est terminé), le mandat retenu
    est celui dont dateDebut est le plus récent."""
    from candidate_profile import _select_mandat_assemblee_courant

    mandats = [
        {"typeOrgane": "ASSEMBLEE", "dateDebut": "2012-06-20", "dateFin": "2017-06-20", "legislature": "14"},
        {"typeOrgane": "ASSEMBLEE", "dateDebut": "2017-06-21", "dateFin": "2022-06-21", "legislature": "15"},
        {"typeOrgane": "GP", "dateDebut": "2017-06-21", "dateFin": None, "legislature": "15"},
    ]
    best = _select_mandat_assemblee_courant(mandats)
    assert best["legislature"] == "15"


def test_select_mandat_assemblee_courant_returns_none_without_assemblee_mandat():
    from candidate_profile import _select_mandat_assemblee_courant

    assert _select_mandat_assemblee_courant([{"typeOrgane": "GP", "dateFin": None}]) is None
    assert _select_mandat_assemblee_courant([]) is None


def test_build_acteur_identite_index_covers_former_deputy(tmp_path):
    """Contrairement à l'ancien jeu de données AMO10 (actifs uniquement), un
    acteur dont le mandat est terminé (dateFin renseignée, absent de la
    législature en cours) doit apparaître dans l'index — c'est l'objet même
    de l'issue #354."""
    from candidate_profile import _build_acteur_identite_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA295": {
                "uid": {"#text": "PA295"},
                "etatCivil": {
                    "ident": {"civ": "M.", "prenom": "François", "nom": "Asensi"},
                    "infoNaissance": {"dateNais": "1945-06-01", "villeNais": "Douai", "depNais": "59", "paysNais": "France"},
                },
                "profession": {"libelleCourant": "Dessinateur industriel"},
                "uri_hatvp": None,
                "adresses": {"adresse": []},
                "mandats": {
                    "mandat": [
                        {
                            "typeOrgane": "ASSEMBLEE",
                            "legislature": "14",
                            "dateDebut": "2012-06-20",
                            "dateFin": "2017-06-20",
                            "election": {"lieu": {"numDepartement": "93", "numCirco": "4"}},
                            "mandature": {"placeHemicycle": "123"},
                        }
                    ]
                },
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        index = _build_acteur_identite_index()

    assert index["PA295"]["nom_complet"] == "François Asensi"
    assert index["PA295"]["numero_departement"] == "93"
    assert index["PA295"]["numero_circo"] == "4"
    assert index["PA295"]["place_hemicycle"] == "123"


def test_build_acteur_identite_index_resolves_groupe_politique_and_mandat_dates(tmp_path):
    """groupe_sigle/groupe_nom (mandat GP le plus actuel, organeRef résolu),
    mandat_debut/mandat_fin (mandat ASSEMBLEE sélectionné) et nb_mandats
    (compte des mandats ASSEMBLEE) doivent être renseignés (#369, étape 4 :
    nécessaires pour rendre fetch_identity conditionnel sans perdre ces
    champs, jusque-là NosDéputés uniquement)."""
    from candidate_profile import _build_acteur_identite_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={
            "PO845401": {
                "uid": "PO845401",
                "codeType": "GP",
                "libelle": "Rassemblement National",
                "libelleAbrege": "RN",
            },
        },
        acteur_entries={
            "PA1": {
                "uid": {"#text": "PA1"},
                "etatCivil": {"ident": {"prenom": "Jane", "nom": "Doe"}},
                "mandats": {
                    "mandat": [
                        {
                            "typeOrgane": "ASSEMBLEE",
                            "legislature": "16",
                            "dateDebut": "2022-06-22",
                            "dateFin": "2024-06-09",
                        },
                        {
                            "typeOrgane": "ASSEMBLEE",
                            "legislature": "17",
                            "dateDebut": "2024-07-08",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "GP",
                            "organes": {"organeRef": "PO845401"},
                            "dateDebut": "2024-07-08",
                            "dateFin": None,
                        },
                    ]
                },
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        index = _build_acteur_identite_index()

    assert index["PA1"]["groupe_sigle"] == "RN"
    assert index["PA1"]["groupe_nom"] == "Rassemblement National"
    assert index["PA1"]["mandat_debut"] == "2024-07-08"
    assert index["PA1"]["mandat_fin"] is None
    assert index["PA1"]["nb_mandats"] == 2


def test_build_acteur_identite_index_keeps_current_mandate_over_past_ones(tmp_path):
    """Pour un acteur réélu sur plusieurs législatures, la circonscription/place
    hémicycle retenue doit être celle du mandat en cours, pas un mandat
    antérieur rencontré en premier dans la liste (voir
    _select_mandat_assemblee_courant)."""
    from candidate_profile import _build_acteur_identite_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA1": {
                "uid": {"#text": "PA1"},
                "etatCivil": {"ident": {"prenom": "Jane", "nom": "Doe"}},
                "mandats": {
                    "mandat": [
                        {
                            "typeOrgane": "ASSEMBLEE",
                            "legislature": "16",
                            "dateDebut": "2022-06-22",
                            "dateFin": "2024-06-09",
                            "election": {"lieu": {"numDepartement": "75", "numCirco": "1"}},
                            "mandature": {"placeHemicycle": "old"},
                        },
                        {
                            "typeOrgane": "ASSEMBLEE",
                            "legislature": "17",
                            "dateDebut": "2024-07-08",
                            "dateFin": None,
                            "election": {"lieu": {"numDepartement": "75", "numCirco": "2"}},
                            "mandature": {"placeHemicycle": "new"},
                        },
                    ]
                },
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        index = _build_acteur_identite_index()

    assert index["PA1"]["numero_circo"] == "2"
    assert index["PA1"]["place_hemicycle"] == "new"


def test_build_acteur_identite_index_uses_disk_cache_without_download(tmp_path):
    from candidate_profile import _build_acteur_identite_index

    cached_index = {"PA1": {"nom_complet": "Jane Doe"}}
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / candidate_profile.NOM_INDEX_IDENTITE).write_text(json.dumps(cached_index, ensure_ascii=False), encoding="utf-8")

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get") as mock_get,
    ):
        index = _build_acteur_identite_index()

    mock_get.assert_not_called()
    assert index == cached_index


def test_build_acteur_identite_index_download_failure_returns_empty(tmp_path):
    from candidate_profile import _build_acteur_identite_index
    import requests as _requests_module

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", side_effect=_requests_module.RequestException("boom")),
    ):
        index = _build_acteur_identite_index()

    assert index == {}


def test_fetch_identite_officielle_resolves_former_deputy(tmp_path):
    from candidate_profile import fetch_identite_officielle

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA295": {
                "uid": {"#text": "PA295"},
                "etatCivil": {"ident": {"prenom": "François", "nom": "Asensi"}},
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        assert fetch_identite_officielle("https://www.assemblee-nationale.fr/dyn/deputes/PA295")["nom_complet"] == "François Asensi"
        assert fetch_identite_officielle(None) is None


# ---------------------------------------------------------------------------
# Tests pour _build_acteur_mandats_index / _extract_mandats_officiels (#369) :
# commissions/groupes d'amitié/engagements extra-parlementaires sourcés
# depuis le référentiel officiel AN plutôt que NosDéputés, avec organeRef
# résolu via fetch_organe (#353).
# ---------------------------------------------------------------------------


def test_build_acteur_mandats_index_maps_type_organe_to_categorie(tmp_path):
    """Chaque typeOrgane du périmètre doit produire sa catégorie (voir
    `_TYPE_ORGANE_TO_CATEGORIE`, élargi par #382/#383) ; un typeOrgane
    volontairement exclu (`_TYPE_ORGANE_NON_MAPPES`) doit être ignoré — et
    surtout PAS retomber dans une catégorie fourre-tout par défaut."""
    from candidate_profile import _build_acteur_mandats_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA1": {
                "uid": {"#text": "PA1"},
                "mandats": {
                    "mandat": [
                        {
                            "typeOrgane": "COMPER",
                            "organes": {"organeRef": "PO59048"},
                            "infosQualite": {"libQualite": "Président"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "GA",
                            "organes": {"organeRef": "PO393167"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": "2024-06-09",
                        },
                        {
                            "typeOrgane": "ORGEXTPARL",
                            "organes": {"organeRef": "PO111111"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "MISINFO",
                            "organes": {"organeRef": "PO222222"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "CNPE",
                            "organes": {"organeRef": "PO444444"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "GE",
                            "organes": {"organeRef": "PO555555"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "API",
                            "organes": {"organeRef": "PO666666"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "MINISTERE",
                            "organes": {"organeRef": "PO777777"},
                            "infosQualite": {"libQualite": "Ministre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "BUREAU",
                            "organes": {"organeRef": "PO888888"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "ASSEMBLEE",
                            "organes": {"organeRef": "PO333333"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "CMP",
                            "organes": {"organeRef": "PO999999"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                        {
                            "typeOrgane": "PARPOL",
                            "organes": {"organeRef": "PO101010"},
                            "infosQualite": {"libQualite": "Membre"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                    ]
                },
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        index = _build_acteur_mandats_index()

    categories = {e["organe_ref"]: e["categorie"] for e in index["PA1"]}
    assert categories == {
        "PO59048": "commission",
        "PO393167": "groupe_amitie",
        "PO111111": "extra_parlementaire",
        "PO222222": "mission_information",
        "PO444444": "commission_enquete",
        "PO555555": "groupe_etudes",
        "PO666666": "delegation",
        "PO777777": "fonction_gouvernementale",
        "PO888888": "autre",
    }
    # Exclusions volontaires (`_TYPE_ORGANE_NON_MAPPES`) : aucune catégorie,
    # pas même un fourre-tout — chacune a sa raison documentée.
    assert categories.get("PO333333") is None  # ASSEMBLEE : c'est le mandat électif
    assert categories.get("PO999999") is None  # CMP : organe temporaire par texte
    assert categories.get("PO101010") is None  # PARPOL : recoupe `parti`/groupe_politique


def test_type_organe_mapping_et_exclusions_sont_coherents():
    """Garde-fou #382 : un `typeOrgane` ne peut pas être à la fois mappé et
    déclaré exclu, et toute catégorie produite doit appartenir au vocabulaire
    du schéma pivot — sinon `validate_profil` rejetterait les profils générés."""
    from candidate_profile import _TYPE_ORGANE_NON_MAPPES, _TYPE_ORGANE_TO_CATEGORIE
    from schema_pivot import KNOWN_CATEGORIES

    chevauchement = set(_TYPE_ORGANE_TO_CATEGORIE) & set(_TYPE_ORGANE_NON_MAPPES)
    assert not chevauchement, f"typeOrgane à la fois mappé et exclu : {chevauchement}"

    inconnues = set(_TYPE_ORGANE_TO_CATEGORIE.values()) - KNOWN_CATEGORIES
    assert not inconnues, f"catégories hors schema_pivot.KNOWN_CATEGORIES : {inconnues}"


def test_extract_mandats_officiels_resolves_organe_labels(tmp_path):
    """Le label doit venir de fetch_organe (nom, ou sigle en repli) — pas
    juste l'organeRef brut."""
    from candidate_profile import _extract_mandats_officiels

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={
            "PO59048": {
                "uid": "PO59048",
                "codeType": "COMPER",
                "libelle": "Commission des finances, de l'économie générale et du contrôle budgétaire",
                "libelleAbrege": "Finances",
            },
        },
        acteur_entries={
            "PA1": {
                "uid": {"#text": "PA1"},
                "mandats": {
                    "mandat": [
                        {
                            "typeOrgane": "COMPER",
                            "organes": {"organeRef": "PO59048"},
                            "infosQualite": {"libQualite": "Président"},
                            "dateDebut": "2022-06-22",
                            "dateFin": None,
                        },
                    ]
                },
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        mandats = _extract_mandats_officiels("PA1")

    assert mandats == [
        {
            "categorie": "commission",
            "type": "Président",
            "label": "Commission des finances, de l'économie générale et du contrôle budgétaire",
            "debut": "2022-06-22",
            "fin": None,
            "actif": True,
            # #718 — la catégorie vient du `codeType` de l'organe (`COMPER`
            # ci-dessus), et l'estampille le dit. C'est ce qui distingue ce
            # mandat d'une entrée héritée que plus aucun référentiel ne
            # qualifie, et donc ce qui rend le dénominateur de la fiche exact.
            "categorie_source": "an",
        }
    ]


def test_extract_mandats_officiels_unknown_acteur_returns_empty():
    from candidate_profile import _extract_mandats_officiels

    with patch("candidate_profile._build_acteur_mandats_index", return_value={}):
        assert _extract_mandats_officiels("PA_INCONNU") == []


def test_build_profile_mandats_viennent_tous_du_referentiel_an():
    """Les mandats commission/groupe_amitie/extra_parlementaire viennent
    d'`_extract_mandats_officiels`, et le mandat électif est reconstruit depuis
    `identite_an`.

    C'était déjà le cas depuis #369 (étape 4) quand l'acteur était résolu côté
    AN ; le complément NosDéputés qui subsistait pour les catégories non
    couvertes est parti avec la source (#529). Ce test s'appelait
    `..._prefer_an_over_nosdeputes_for_shared_categories` : il n'y a plus de
    préférence à exprimer, il n'y a plus qu'une source."""
    identite_an = {
        "nom_complet": "Jean Dupont",
        "mandat_debut": "2022-06-22",
        "mandat_fin": None,
        "groupe_sigle": "RE",
        "groupe_nom": "Renaissance",
    }
    mandats_officiels = [
        {
            "categorie": "commission",
            "type": "Président",
            "label": "Commission des finances, de l'économie générale et du contrôle budgétaire",
            "debut": "2022-06-22",
            "fin": None,
            "actif": True,
            # #718 — la doublure rend ce que l'extracteur réel produit,
            # estampille comprise : `build_profile` la laisse passer sans y
            # toucher, et l'assertion plus bas le vérifie.
            "categorie_source": "an",
        }
    ]

    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=(identite_an, "PA123456")),
        patch("candidate_profile.fetch_identite_officielle", return_value=None),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile._extract_mandats_officiels", return_value=mandats_officiels),
    ):
        profile = build_profile("deputes", "jean-dupont")

    commission_entries = [m for m in profile["mandats"] if m["categorie"] == "commission"]
    assert commission_entries == [
        {
            "categorie": "commission",
            "type": "Président",
            "label": "Commission des finances, de l'économie générale et du contrôle budgétaire",
            "debut": "2022-06-22",
            "fin": None,
            "actif": True,
            "categorie_source": "an",  # #718
        }
    ]
    # Mandat électif reconstruit depuis identite_an : `_extract_mandats_officiels`
    # ne parcourt que les organes. `chambre` est estampillée à la collecte
    # depuis #492, et ce chemin n'est atteignable que pour la chambre "deputes".
    mandat_electif_entries = [m for m in profile["mandats"] if m["categorie"] == "mandat_electif"]
    assert mandat_electif_entries == [
        {
            "categorie": "mandat_electif",
            "categorie_source": "an",  # #718
            "type": "mandat",
            "label": "Mandat parlementaire (Renaissance)",
            "debut": "2022-06-22",
            "fin": None,
            "actif": True,
            # #640 : la période reconstruite dit d'où elle vient (§2 règle 2).
            "source_url": candidate_profile.AN_ACTEURS_HISTORIQUE_ZIP_URL,
            "chambre": "deputes",
        }
    ]
    assert profile["identite"]["groupe_sigle"] == "RE"
    assert profile["identite"]["groupe_nom"] == "Renaissance"


# ---------------------------------------------------------------------------
# Tests pour la résolution acteur_ref par slug NosDéputés (bascule
# fetch_identity vers l'AN comme source primaire pour les députés, #355) :
# fetch_identite_officielle_par_slug ne dépend plus d'une URL AN obtenue via
# un appel NosDéputés préalable.
# ---------------------------------------------------------------------------


def test_fetch_identite_officielle_par_slug_resolves_by_normalized_name(tmp_path):
    from candidate_profile import fetch_identite_officielle_par_slug

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA295": {
                "uid": {"#text": "PA295"},
                "etatCivil": {"ident": {"prenom": "François", "nom": "Asensi"}},
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        fiche, acteur_ref = fetch_identite_officielle_par_slug("francois-asensi")

    assert acteur_ref == "PA295"
    assert fiche["nom_complet"] == "François Asensi"


def test_fetch_identite_officielle_par_slug_returns_none_when_absent(tmp_path):
    from candidate_profile import fetch_identite_officielle_par_slug

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA295": {
                "uid": {"#text": "PA295"},
                "etatCivil": {"ident": {"prenom": "François", "nom": "Asensi"}},
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        fiche, acteur_ref = fetch_identite_officielle_par_slug("candidat-inconnu")

    assert fiche is None
    assert acteur_ref is None


def test_fetch_identite_officielle_par_slug_resolves_hyphenated_prenom(tmp_path):
    """Un prénom composé (ex. "Jean-Luc") conserve son tiret dans nom_complet,
    alors que le slug NosDéputés.fr ("jean-luc-melenchon") remplace TOUS ses
    tirets par des espaces : sans normalisation symétrique côté nom_complet,
    la clé ne matche jamais ("jean-luc melenchon" vs "jean luc melenchon") et
    la résolution échoue en silence pour tout prénom/nom composé (bug réel
    observé en production sur jean-luc-melenchon, cf. run #47)."""
    from candidate_profile import fetch_identite_officielle_par_slug

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA2150": {
                "uid": {"#text": "PA2150"},
                "etatCivil": {"ident": {"prenom": "Jean-Luc", "nom": "Mélenchon"}},
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        fiche, acteur_ref = fetch_identite_officielle_par_slug("jean-luc-melenchon")

    assert acteur_ref == "PA2150"
    assert fiche["nom_complet"] == "Jean-Luc Mélenchon"


def test_fetch_identite_officielle_par_slug_refuses_homonym_ambiguity(tmp_path):
    """Deux acteurs distincts partageant le même nom normalisé (homonymie) ne
    doivent jamais être résolus au hasard vers l'un des deux : la fonction
    renonce plutôt que de risquer une mauvaise attribution d'identité."""
    from candidate_profile import fetch_identite_officielle_par_slug

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA1": {"uid": {"#text": "PA1"}, "etatCivil": {"ident": {"prenom": "Jean", "nom": "Dupont"}}},
            "PA2": {"uid": {"#text": "PA2"}, "etatCivil": {"ident": {"prenom": "Jean", "nom": "Dupont"}}},
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
    ):
        fiche, acteur_ref = fetch_identite_officielle_par_slug("jean-dupont")

    assert fiche is None
    assert acteur_ref is None


def test_build_profile_resout_l_identite_depuis_le_referentiel_an(tmp_path):
    """Bascule #355 : l'identité (infos biographiques) est renseignée depuis le
    référentiel historique officiel AN, résolu par nom depuis le slug — sans
    dépendre d'une URL AN qu'une plateforme tierce aurait fournie.

    Le test s'appelait `..._when_nosdeputes_has_no_profile` : ce n'est plus un
    cas particulier depuis #529, c'est le seul chemin."""
    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={},
        acteur_entries={
            "PA295": {
                "uid": {"#text": "PA295"},
                "etatCivil": {
                    "ident": {"civ": "M.", "prenom": "François", "nom": "Asensi"},
                    "infoNaissance": {"dateNais": "1945-06-01", "villeNais": "Douai", "depNais": "59", "paysNais": "France"},
                },
                "profession": {"libelleCourant": "Dessinateur industriel"},
                "adresses": {"adresse": []},
                "mandats": {"mandat": []},
            },
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)),
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        profile = build_profile("deputes", "francois-asensi")

    assert profile["identite"]["nom_complet"] == "François Asensi"
    assert profile["identite"]["profession"] == "Dessinateur industriel"
    assert profile["identite"]["lieu_naissance"] is not None
    assert "PA295" in profile["identite"]["url_an_ou_senat"]
    # Cet acteur factice n'a aucun mandat AN (mandats.mandat vide) : le warning
    # mandats introuvables doit être émis, mais pas celui d'identité
    # introuvable (l'AN a bien trouvé l'acteur).
    assert not any(w.startswith("identité introuvable") for w in profile["meta"]["warnings"])
    assert any(w.startswith("mandats introuvables") for w in profile["meta"]["warnings"])
    assert profile["mandats"] == []


def test_build_profile_sans_acteur_an_ne_fabrique_aucune_identite():
    """Le repli complet vers NosDéputés (#369, étape 4) a été RETIRÉ (#529).

    Un slug absent du référentiel AN combiné ne produit plus d'identité du
    tout. Ce n'est pas un silence : le profil sort avec
    `WARNING_PREFIX_IDENTITE_INTROUVABLE`, qui nomme la seule source
    consultée, et `process_candidat` le compte en « introuvable ». C'est un
    CONSTAT de l'AN — la table `raw_data/correspondance_acteurs_an.json` (#525)
    est ce qui résout le couple slug ↔ acteur, et §5b du garde-fou qualité
    échoue déjà sur tout slug publié qui n'y a pas d'entrée.
    """
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=(None, None)),
        patch("candidate_profile.fetch_interventions_syceron") as mock_syceron,
        patch("candidate_profile.fetch_questions_officielles") as mock_questions,
        patch("candidate_profile.fetch_votes_officiels") as mock_votes,
        patch("candidate_profile.fetch_amendements_officiels") as mock_amendements,
        patch("candidate_profile.fetch_textes_portes_officiels") as mock_textes,
    ):
        profile = build_profile("deputes", "jean-dupont")

    assert profile["identite"] is None
    assert profile["mandats"] == []
    introuvable = [
        w for w in profile["meta"]["warnings"]
        if w.startswith(candidate_profile.WARNING_PREFIX_IDENTITE_INTROUVABLE)
    ]
    assert introuvable, "l'absence d'identité doit être déclarée"
    assert "#529" in introuvable[0], (
        "le warning doit nommer la seule source consultée et la décision qui "
        "l'a rendue seule"
    )

    # Sans identité, aucune collecte en aval n'est tentée : une section vide
    # produite par une collecte qui n'a pas eu lieu se lit comme un constat.
    for mock in (mock_syceron, mock_questions, mock_votes, mock_amendements, mock_textes):
        mock.assert_not_called()


def test_identite_index_shares_historique_zip_download_with_organe_index(tmp_path):
    """_build_acteur_identite_index doit réutiliser le même zip bulk que
    _build_organe_index (_ensure_acteurs_historique_zip_downloaded) : un seul
    téléchargement, pas un par index (issue #354, même refactor que #353)."""
    from candidate_profile import _build_acteur_identite_index, _build_organe_index

    zip_bytes = _make_fake_acteurs_historique_zip_bytes(
        organe_entries={
            "PO1": {"uid": "PO1", "codeType": "COMPER", "libelle": "Commission", "libelleAbrege": "Com"},
        },
        acteur_entries={
            "PA1": {"uid": {"#text": "PA1"}, "etatCivil": {"ident": {"prenom": "Jane", "nom": "Doe"}}},
        },
    )

    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.requests.get", return_value=_FakeActeursHistoriqueStreamResponse(zip_bytes)) as mock_get,
    ):
        organe_index = _build_organe_index()
        identite_index = _build_acteur_identite_index()

    assert mock_get.call_count == 1, "Le zip bulk ne doit être téléchargé qu'une seule fois, partagé entre les deux index"
    assert organe_index["PO1"]["sigle"] == "Com"
    assert identite_index["PA1"]["nom_complet"] == "Jane Doe"


def test_amendements_index_deja_figee_false_on_legacy_uid_shards(tmp_path):
    """Impasse mesurée sur le cache local du 19/08/2026 (#447) : un cache figé
    matérialisé AVANT la correction de clé du 18/08 (références par `numero`)
    était déclaré « déjà figé » — donc jamais reconstruit par
    `build_amendements_index.py` — pendant que `_read_cached_amendements_acteur`
    le REFUSAIT à la lecture. Ni reconstruit, ni lu : la législature perd la
    totalité de ses amendements, avec pour seul signe un warning soft « index en
    cache absent ».

    Les deux moitiés de l'impasse sont vérifiées ici, pour que le test dise
    pourquoi le format compte et pas seulement qu'il est contrôlé."""
    from candidate_profile import _read_cached_amendements_acteur, amendements_index_deja_figee

    cache_dir = tmp_path / "cache"
    _write_cache_amendements(
        cache_dir,
        "15",
        amendements={"12": {"numero": "12", "texte_vise": "PIONANR5L15B4852"}},
        index_par_acteur={"PA1": [{"numero": "12", "role_signataire": "auteur_principal"}]},
    )
    (cache_dir / "15" / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-15T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        # Moitié lecture : l'index hérité est refusé (comportement déjà acquis).
        assert _read_cached_amendements_acteur("15", "PA1") is None
        # Moitié reconstruction : il ne doit donc PAS être considéré comme figé.
        assert amendements_index_deja_figee("15") is False


def test_amendements_index_deja_figee_true_on_uid_shards(tmp_path):
    """Contrepartie : le même cache, au format `uid`, reste bien « déjà figé »
    — le contrôle de format ne doit pas faire retélécharger une législature
    figée correctement matérialisée."""
    from candidate_profile import amendements_index_deja_figee

    cache_dir = tmp_path / "cache"
    uid = "AMANR5L15PO123456B0001P0D1N001"
    _write_cache_amendements(
        cache_dir,
        "15",
        amendements={uid: {"uid": uid, "numero": "12"}},
        index_par_acteur={"PA1": [{"uid": uid, "role_signataire": "auteur_principal"}]},
    )
    (cache_dir / "15" / "fraicheur.json").write_text(
        json.dumps({"derniere_construction_reussie": True, "horodatage": "2026-08-15T00:00:00+0000", "figee": True}),
        encoding="utf-8",
    )

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        assert amendements_index_deja_figee("15") is True


def test_write_cached_amendements_agreges_publie_le_repertoire_dun_seul_coup(tmp_path):
    """Une écriture interrompue ne doit JAMAIS laisser un répertoire de tranches
    qui existe et qui est incomplet (#447).

    C'est ce que la docstring de `_write_cached_amendements_agreges` promettait
    déjà, mais que le code ne tenait pas : il faisait `mkdir` puis remplissait en
    place, donc pendant toute la boucle le répertoire existait à moitié rempli.
    Un tel répertoire est accepté comme cache-hit par
    `_download_and_build_amendement_index` (`index_dir.is_dir()`), donc jamais
    reconstruit, et chaque acteur dont la tranche manque est lu comme « aucun
    amendement » au lieu de « index indisponible » — un zéro silencieux.
    Atteignable en CI : le step d'upload de l'artifact amendements est en
    `if: always()`, donc un job interrompu publie l'état partiel du disque."""
    from candidate_profile import _write_cached_amendements_agreges

    cache_dir = tmp_path / "cache"
    uid = "AMANR5L17PO1B1P0D1N1"
    index = {f"PA{i}": [{"uid": uid, "role_signataire": "auteur_principal"}] for i in range(1, 6)}

    vrai_dump = json.dump
    appels = {"n": 0}

    def dump_qui_echoue(obj, fp, **kwargs):
        # Laisse passer amendements.json puis les 2 premières tranches, et
        # interrompt : le répertoire est alors à moitié écrit.
        appels["n"] += 1
        if appels["n"] > 3:
            raise OSError("interruption simulée en cours d'écriture des tranches")
        return vrai_dump(obj, fp, **kwargs)

    with (
        patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir),
        patch("candidate_profile.json.dump", side_effect=dump_qui_echoue),
        pytest.raises(OSError),
    ):
        _write_cached_amendements_agreges("17", {uid: {"uid": uid}}, index)

    # Le répertoire officiel ne doit pas exister : un cache traité comme absent,
    # jamais un cache incohérent.
    assert not (cache_dir / "17" / "index_par_acteur").exists()


def test_write_cached_amendements_agreges_ecrit_bien_toutes_les_tranches(tmp_path):
    """Contrepartie : une écriture qui va au bout publie le répertoire complet,
    et ne laisse derrière elle aucun répertoire temporaire."""
    from candidate_profile import _read_cached_amendements_acteur, _write_cached_amendements_agreges

    cache_dir = tmp_path / "cache"
    uid = "AMANR5L17PO1B1P0D1N1"
    index = {f"PA{i}": [{"uid": uid, "role_signataire": "auteur_principal"}] for i in range(1, 6)}

    with patch("candidate_profile.AMENDEMENTS_CACHE_DIR", cache_dir):
        _write_cached_amendements_agreges("17", {uid: {"uid": uid, "numero": "12"}}, index)

        index_dir = cache_dir / "17" / "index_par_acteur"
        assert sorted(p.name for p in index_dir.glob("*.json")) == [f"PA{i}.json" for i in range(1, 6)]
        assert not (cache_dir / "17" / "index_par_acteur.partiel").exists()
        assert _read_cached_amendements_acteur("17", "PA3") == [
            {"uid": uid, "numero": "12", "role_signataire": "auteur_principal"}
        ]
