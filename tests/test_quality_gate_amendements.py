"""Tests de non-régression pour la couverture amendements dans check_quality_gate.py
(issue #185 : une régression de collecte qui vide amendements[] sur tous les
candidats AN n'était détectée par aucune section du quality gate) et pour le
signal de fraîcheur des index de législature (issue #254, sous-issue 6/6 de
#248 : distinguer un index jamais construit d'un index présent mais périmé,
en s'appuyant sur `fraicheur.json` écrit par `_write_amendements_fraicheur`,
candidate_profile.py, issue #253).

Le signal global de la §3c (« aucun profil AN n'a d'amendements ») reste un
avertissement non bloquant : il n'entre jamais dans le code de sortie, mais est
remonté à part et affiché en tête de rapport (décision #378, voir
docs/decisions/amendements-zero-pas-de-hard-fail.md). Les tests
ci-dessous verrouillent les deux moitiés de cette décision : la visibilité du
signal, et l'absence d'échec dur."""

import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from correspondance_acteurs_an import SCHEMA_VERSION as CORRESPONDANCE_SCHEMA_VERSION
from check_quality_gate import (
    _AMENDEMENTS_LEGISLATURES,
    _AMENDEMENTS_LEGISLATURES_FIGEES,
    _AMENDEMENTS_UID_MIXTE_ICONE,
    _AMENDEMENTS_ZERO_ICONE,
    _report_amendements_coverage,
    _report_amendements_figes_format,
    _report_amendements_freshness,
    main,
)


def _write_pivot(tmp_path: Path, slug: str, chambre: str, identite, amendements: list, warnings: list) -> None:
    profile = {
        "id": f"nd:{slug}",
        "nom": slug.replace("-", " ").title(),
        "chambre": chambre,
        "identite": identite,
        "mandats": [],
        "interventions": [],
        "votes": [],
        "textes_portes": [],
        "amendements": amendements,
        "tags_thematiques": [],
        "sources": [],
        "meta": {"warnings": warnings},
    }
    (tmp_path / f"{slug}.pivot.json").write_text(json.dumps(profile), encoding="utf-8")


def test_report_amendements_coverage_flags_global_regression_when_all_empty(tmp_path):
    """Plusieurs candidats AN avec identité mais amendements[] vide partout :
    doit déclencher un soft warning global (régression de collecte)."""
    _write_pivot(tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"}, amendements=[], warnings=[])
    _write_pivot(tmp_path, "marie-martin", "AN", {"nom_complet": "Marie Martin"}, amendements=[], warnings=[])

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert len(soft) == 1
    assert "2" in soft[0]
    # Retourné à part pour l'affichage en tête de rapport (#378), tout en
    # restant présent dans soft_warnings (même nature : non bloquant).
    assert regression == soft[0]
    assert _AMENDEMENTS_ZERO_ICONE in console
    assert "RÉGRESSION PROBABLE DE COLLECTE" in console
    assert "NON bloquant" in console
    assert _AMENDEMENTS_ZERO_ICONE in md
    assert "non bloquant" in md


def test_report_amendements_coverage_no_warning_when_some_have_amendements(tmp_path):
    """Si au moins un candidat AN a des amendements collectés, pas de warning global."""
    _write_pivot(
        tmp_path,
        "jean-dupont",
        "AN",
        {"nom_complet": "Jean Dupont"},
        amendements=[{"sort": "adopté", "type_deposant": "depute"}],
        warnings=[],
    )
    _write_pivot(tmp_path, "marie-martin", "AN", {"nom_complet": "Marie Martin"}, amendements=[], warnings=[])

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert len(soft) == 0
    assert regression is None
    assert "✓" in console
    assert _AMENDEMENTS_ZERO_ICONE not in console


def test_report_amendements_coverage_flags_per_candidate_fetch_failure(tmp_path):
    """Un warning 'amendements indisponibles' dans meta.warnings doit être
    remonté individuellement, même si d'autres candidats ont bien des amendements."""
    _write_pivot(
        tmp_path,
        "jean-dupont",
        "AN",
        {"nom_complet": "Jean Dupont"},
        amendements=[],
        warnings=["amendements indisponibles : échec du téléchargement (boom)"],
    )
    _write_pivot(
        tmp_path,
        "marie-martin",
        "AN",
        {"nom_complet": "Marie Martin"},
        amendements=[{"sort": "adopté", "type_deposant": "depute"}],
        warnings=[],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert any("jean-dupont" in w for w in soft)
    # Pas de régression globale puisque marie-martin a bien des amendements.
    assert not any("aucun profil AN" in w for w in soft)


def test_report_amendements_coverage_ignores_candidates_without_identite(tmp_path):
    """Un candidat AN sans identité (non éligible à la collecte d'amendements
    officiels côté candidate_profile.py) ne doit pas être compté."""
    _write_pivot(tmp_path, "sans-identite", "AN", None, amendements=[], warnings=[])

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert len(soft) == 0
    assert "0" in console


def test_report_amendements_coverage_ignores_non_an_candidates(tmp_path):
    """Les candidats non-AN (Sénat...) ne doivent pas être comptés dans la couverture."""
    _write_pivot(tmp_path, "senateur-x", "Senat", {"nom_complet": "Senateur X"}, amendements=[], warnings=[])

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert len(soft) == 0


def test_report_amendements_coverage_empty_dir_returns_no_warning(tmp_path):
    """Aucun profil AN analysé : pas de faux positif sur régression globale."""
    soft, regression, console, md = _report_amendements_coverage(tmp_path)
    assert len(soft) == 0


def test_report_amendements_coverage_signal_global_non_duplique(tmp_path):
    """Le signal global est affiché en bandeau, pas répété dans la liste des
    avertissements par candidat — sinon il apparaîtrait deux fois pour un même
    fait, en tête et en queue de section (#378)."""
    _write_pivot(
        tmp_path,
        "jean-dupont",
        "AN",
        {"nom_complet": "Jean Dupont"},
        amendements=[],
        warnings=["amendements indisponibles : échec du téléchargement (boom)"],
    )
    _write_pivot(tmp_path, "marie-martin", "AN", {"nom_complet": "Marie Martin"}, amendements=[], warnings=[])

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert regression is not None
    # Deux avertissements (un par candidat en échec + le global), mais le
    # global n'est listé qu'une fois, dans le bandeau.
    assert len(soft) == 2
    assert console.count("aucun profil AN") == 1
    assert md.count("aucun profil AN") == 1
    # L'avertissement par candidat reste listé normalement.
    assert "jean-dupont" in console


def test_report_amendements_coverage_mesure_suit_le_champ_apres_431(tmp_path):
    """#431 : l'identifiant a migré d'`uid` vers `amendement_id`, la mesure suit.

    Sans cette bascule, un profil normalisé serait lu à 0 % de couverture et
    signalé comme cassé alors qu'il vient d'être corrigé — la §3c annoncerait
    une régression là où il y a une correction.
    """
    _write_pivot(
        tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"},
        amendements=[
            {"amendement_id": "an:AMANR5L17PO0B0000P0D1N000001",
             "role_signataire": "auteur_principal"},
            {"amendement_id": "an:AMANR5L17PO0B0000P0D1N000002",
             "role_signataire": "cosignataire"},
        ],
        warnings=[],
    )
    soft, regression, console, md = _report_amendements_coverage(tmp_path)
    assert regression is None
    assert soft == []
    assert "dont uid : 2 (100.0 %)" in console


def test_report_amendements_coverage_profil_ancien_et_normalise_cohabitent(tmp_path):
    """La fusion additive fait cohabiter les deux formes le temps d'une
    régénération : les deux doivent compter."""
    _write_pivot(
        tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"},
        amendements=[
            {"amendement_id": "an:AMANR5L17PO0B0000P0D1N000001",
             "role_signataire": "auteur_principal"},
            {"uid": "AMANR5L17PO0B0000P0D1N000002", "sort": "rejeté"},
            {"numero": "CL9", "sort": "rejeté"},  # ni l'un ni l'autre
        ],
        warnings=[],
    )
    soft, regression, console, md = _report_amendements_coverage(tmp_path)
    assert "dont uid : 2 (66.7 %)" in console
    assert any("1/3 amendements sans uid" in w for w in soft)


def _write_config_vide(path: Path, cle: str) -> None:
    path.write_text(json.dumps({cle: []}), encoding="utf-8")


def _write_correspondance(path: Path, slugs) -> None:
    """Table slug ↔ acteur AN couvrant les profils factices de `_run_main`.

    Même raison que `--amendements-figes-dir` ci-dessous : sans elle, la §5b
    lirait la table réelle du dépôt, n'y trouverait pas `jean-dupont`, et ces
    tests-ci — qui portent sur les sections 3c/3d — échoueraient sur un autre
    sujet que le leur (#525).
    """
    correspondances = {
        slug: {
            "acteur_ref": f"PA90000{index}",
            "etat_civil": {"nom_complet": slug.replace("-", " ").title()},
            "ecart": None,
            "motif": None,
            "preuve": f"https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA90000{index}",
            "verifie_le": "2026-08-26",
        }
        for index, slug in enumerate(sorted(slugs))
    }
    path.write_text(
        json.dumps({
            "schema_version": CORRESPONDANCE_SCHEMA_VERSION,
            "genere_le": "2026-08-26T00:00:00+0000",
            "source_referentiel": "https://data.assemblee-nationale.fr/",
            "correspondances": correspondances,
        }),
        encoding="utf-8",
    )


def _run_main(monkeypatch, tmp_path: Path, cache_dir: Path | None, pivots: dict | None = None) -> int:
    """Exécute le quality gate complet sur une arborescence minimale, avec les
    seules sections amendements susceptibles de signaler quelque chose.

    `pivots` : `{slug: amendements}` à écrire au lieu des deux profils vides
    par défaut, pour les tests qui ont besoin d'un contenu d'amendements
    particulier (couverture `uid`, #447)."""
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    profils = pivots or {"jean-dupont": [], "marie-martin": []}
    for slug, amendements in profils.items():
        _write_pivot(
            profiles_dir, slug, "AN", {"nom_complet": slug.replace("-", " ").title()},
            amendements=amendements, warnings=[],
        )
    _write_correspondance(tmp_path / "correspondance_acteurs_an.json", profils)

    for sous_dossier in ("groupes", "gouvernements", "raw"):
        (tmp_path / sous_dossier).mkdir()
    _write_config_vide(tmp_path / "groupes_reels.json", "groupes")
    _write_config_vide(tmp_path / "gouvernements_reels.json", "gouvernements")
    _write_config_vide(tmp_path / "candidats.json", "candidats")

    argv = [
        "check_quality_gate.py",
        "--profiles-dir", str(profiles_dir),
        "--groupes-dir", str(tmp_path / "groupes"),
        "--gouvernements-dir", str(tmp_path / "gouvernements"),
        "--raw-dir", str(tmp_path / "raw"),
        "--candidats", str(tmp_path / "candidats.json"),
        "--groupes-config", str(tmp_path / "groupes_reels.json"),
        "--gouvernements-config", str(tmp_path / "gouvernements_reels.json"),
        "--amendements-cache-dir", str(cache_dir if cache_dir is not None else tmp_path / "cache_absent"),
        # Répertoire d'index figés vide : la §3e ne se prononce que sur le
        # format de ce qui existe, et ces tests-ci portent sur les sections
        # 3c/3d. Sans cet argument, ils liraient les index réels du dépôt et
        # dépendraient de leur état.
        "--amendements-figes-dir", str(tmp_path / "figes_absent"),
        "--correspondance-acteurs", str(tmp_path / "correspondance_acteurs_an.json"),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    return main()


def test_main_zero_amendement_ne_bloque_pas_le_commit(tmp_path, monkeypatch, capsys):
    """Décision #378 : « 0 amendement collecté partout » est un signal fort,
    affiché en tête de rapport, mais **jamais** un échec dur — le commit reste
    autorisé (exit 0)."""
    code = _run_main(monkeypatch, tmp_path, cache_dir=None)
    sortie = capsys.readouterr().out

    assert code == 0
    assert "COMMIT AUTORISÉ" in sortie
    # Affiché en tête (bandeau), avant même la section 3c.
    entete, _, corps = sortie.partition("┌─ 1/4")
    assert _AMENDEMENTS_ZERO_ICONE in entete
    assert "aucun profil AN sur 2" in entete
    assert "non bloquant" in entete.lower()


def test_main_index_jamais_construit_ne_bloque_pas_le_commit(tmp_path, monkeypatch, capsys):
    """Aucune régression sur le fil #239→#254 : une législature dont l'index
    n'a jamais pu être construit (échec chronique de téléchargement de la 17)
    ne doit jamais bloquer un run — c'est un aléa réseau, pas une régression."""
    code = _run_main(monkeypatch, tmp_path, cache_dir=tmp_path / "amendements_an_absent")
    sortie = capsys.readouterr().out

    assert code == 0
    assert "jamais construit" in sortie


# ---------------------------------------------------------------------------
# _report_amendements_freshness (issue #254)
# ---------------------------------------------------------------------------

REFERENCE = datetime(2026, 8, 13, 12, 0, 0, tzinfo=timezone.utc)


def _horodatage(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


def _write_index(cache_dir: Path, legislature: str) -> None:
    """Écrit un cache d'amendements au format dédupliqué (#377) : les deux
    fichiers `amendements.json` + `index_par_acteur.json` vont toujours de
    pair, et le rapport de fraîcheur exige désormais les deux (un cache
    n'ayant que l'un des deux est un cache hérité d'avant #377, traité comme
    absent aussi bien ici que par le lecteur réel)."""
    leg_dir = cache_dir / legislature
    leg_dir.mkdir(parents=True, exist_ok=True)
    (leg_dir / "amendements.json").write_text(json.dumps({}), encoding="utf-8")
    shards = leg_dir / "index_par_acteur"
    shards.mkdir(exist_ok=True)
    (shards / "PA123.json").write_text(json.dumps([]), encoding="utf-8")


def _write_fraicheur(cache_dir: Path, legislature: str, reussi: bool, horodatage: str, figee: bool = False) -> None:
    leg_dir = cache_dir / legislature
    leg_dir.mkdir(parents=True, exist_ok=True)
    payload = {"derniere_construction_reussie": reussi, "horodatage": horodatage}
    if figee:
        payload["figee"] = True
    (leg_dir / "fraicheur.json").write_text(json.dumps(payload), encoding="utf-8")


def _write_all_fresh(cache_dir: Path) -> None:
    """Prépare les 3 législatures comme fraîches, pour isoler une seule
    législature sous test dans les cas ci-dessous (une législature non
    créée du tout serait autrement comptée « jamais construite »)."""
    for legislature in _AMENDEMENTS_LEGISLATURES:
        _write_index(cache_dir, legislature)
        _write_fraicheur(cache_dir, legislature, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=1)))


def test_report_amendements_freshness_all_never_built_on_empty_cache_dir(tmp_path):
    """Répertoire de cache absent/vide : chaque législature est signalée
    « jamais construite », pas de faux « périmé »."""
    soft, console, md = _report_amendements_freshness(tmp_path / "amendements_an", staleness_days=7)

    assert len(soft) == len(_AMENDEMENTS_LEGISLATURES)
    assert all("jamais construit" in w for w in soft)
    assert "⚠" in console


def test_report_amendements_freshness_fresh_index_no_warning(tmp_path):
    """Index présent, dernière reconstruction réussie et récente : pas de warning."""
    cache_dir = tmp_path / "amendements_an"
    for legislature in _AMENDEMENTS_LEGISLATURES:
        _write_index(cache_dir, legislature)
        _write_fraicheur(cache_dir, legislature, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=1)))

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert len(soft) == 0
    assert "✓" in console


def test_report_amendements_freshness_legacy_flat_cache_reported_as_never_built(tmp_path):
    """Cache hérité d'un format précédent (ici #377 : `index_par_acteur.json`
    en fichier unique, sans le répertoire de tranches de #392) : doit être
    rapporté « jamais construit », le
    même verdict que celui du lecteur réel
    (`candidate_profile._read_cached_amendements_agreges`, qui exige les deux
    fichiers et ne relit jamais l'ancien format en mémoire). Sans ça, le
    rapport annoncerait « construit » un index que la collecte ignore."""
    cache_dir = tmp_path / "amendements_an"
    legislature = _AMENDEMENTS_LEGISLATURES[0]
    leg_dir = cache_dir / legislature
    leg_dir.mkdir(parents=True, exist_ok=True)
    (leg_dir / "index_par_acteur.json").write_text(json.dumps({"PA123": []}), encoding="utf-8")
    (leg_dir / "amendements.json").write_text(json.dumps({}), encoding="utf-8")
    _write_fraicheur(cache_dir, legislature, reussi=True, horodatage=_horodatage(REFERENCE))

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert any(legislature in w and "jamais construit" in w for w in soft)


def test_report_amendements_freshness_stale_successful_build_flagged(tmp_path):
    """Index présent, dernière reconstruction réussie mais au-delà du seuil : périmé."""
    cache_dir = tmp_path / "amendements_an"
    _write_all_fresh(cache_dir)
    legislature = _AMENDEMENTS_LEGISLATURES[0]
    _write_fraicheur(cache_dir, legislature, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=10)))

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert len(soft) == 1
    assert "périmé" in soft[0]
    assert "10 jour" in soft[0]


def test_report_amendements_freshness_failed_last_attempt_flagged_regardless_of_age(tmp_path):
    """Dernière tentative de reconstruction en échec (index préservé, #253) :
    périmé même si l'horodatage de l'échec est récent."""
    cache_dir = tmp_path / "amendements_an"
    _write_all_fresh(cache_dir)
    legislature = _AMENDEMENTS_LEGISLATURES[0]
    _write_fraicheur(cache_dir, legislature, reussi=False, horodatage=_horodatage(REFERENCE))

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert len(soft) == 1
    assert "échec" in soft[0]


def test_report_amendements_freshness_index_without_fraicheur_file_flagged(tmp_path):
    """Index présent mais sans fraicheur.json (ex. cache antérieur à #253) :
    fraîcheur non garantie, traité comme périmé plutôt que comme faux frais."""
    cache_dir = tmp_path / "amendements_an"
    _write_all_fresh(cache_dir)
    legislature = _AMENDEMENTS_LEGISLATURES[0]
    (cache_dir / legislature / "fraicheur.json").unlink()

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert len(soft) == 1
    assert "absent" in soft[0]


def test_report_amendements_freshness_mixed_states_across_legislatures(tmp_path):
    """Des législatures différentes peuvent être dans des états différents
    simultanément : chacune est rapportée indépendamment."""
    cache_dir = tmp_path / "amendements_an"
    leg_fresh, leg_stale, leg_never = _AMENDEMENTS_LEGISLATURES[:3]
    _write_index(cache_dir, leg_fresh)
    _write_fraicheur(cache_dir, leg_fresh, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=1)))
    _write_index(cache_dir, leg_stale)
    _write_fraicheur(cache_dir, leg_stale, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=30)))
    # leg_never : aucun fichier créé.
    # Toute autre législature au-delà des 3 ci-dessus (ex. l'ajout futur d'une
    # 4e) est mise fraîche pour ne pas fausser l'assertion `len(soft) == 2`
    # ci-dessous, qui ne porte que sur leg_stale/leg_never.
    for leg_autre in _AMENDEMENTS_LEGISLATURES[3:]:
        _write_index(cache_dir, leg_autre)
        _write_fraicheur(cache_dir, leg_autre, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=1)))

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert len(soft) == 2
    assert any(leg_stale in w and "périmé" in w for w in soft)
    assert any(leg_never in w and "jamais construit" in w for w in soft)
    assert not any(leg_fresh in w for w in soft)


# ---------------------------------------------------------------------------
# État « figé » (légis 15/16 : dossier clos, fallback committé, jamais
# reconstruit — docs/decisions/amendements-legislatures-figees.md).
# ---------------------------------------------------------------------------

def test_report_amendements_freshness_frozen_legislature_no_warning_even_when_very_old(tmp_path):
    """Une législature figée (fraicheur.json avec figee: true) ne doit jamais
    être signalée périmée, même très au-delà du seuil de péremption."""
    cache_dir = tmp_path / "amendements_an"
    _write_all_fresh(cache_dir)
    legislature = next(iter(_AMENDEMENTS_LEGISLATURES_FIGEES))
    _write_fraicheur(
        cache_dir, legislature, reussi=True,
        horodatage=_horodatage(REFERENCE - timedelta(days=365)), figee=True,
    )

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert not any(legislature in w for w in soft)
    assert "❄️" in md


def test_report_amendements_freshness_legislature_marked_figee_but_not_in_frozen_set_still_checked(tmp_path):
    """Défense en profondeur : un `figee: true` errant sur une législature hors
    `_AMENDEMENTS_LEGISLATURES_FIGEES` (ex. la 17e, active) ne doit pas la
    dispenser du contrôle de péremption normal."""
    cache_dir = tmp_path / "amendements_an"
    _write_all_fresh(cache_dir)
    active_legislature = next(leg for leg in _AMENDEMENTS_LEGISLATURES if leg not in _AMENDEMENTS_LEGISLATURES_FIGEES)
    _write_fraicheur(
        cache_dir, active_legislature, reussi=True,
        horodatage=_horodatage(REFERENCE - timedelta(days=30)), figee=True,
    )

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=7, reference_date=REFERENCE)

    assert any(active_legislature in w and "périmé" in w for w in soft)


def test_report_amendements_freshness_disabled_via_zero_threshold_is_caller_responsibility(tmp_path):
    """staleness_days=0 : tout âge positif dépasse le seuil (aucun raccourci
    interne de désactivation — c'est main() qui saute l'appel sur 0, voir CLI)."""
    cache_dir = tmp_path / "amendements_an"
    legislature = _AMENDEMENTS_LEGISLATURES[0]
    _write_index(cache_dir, legislature)
    _write_fraicheur(cache_dir, legislature, reussi=True, horodatage=_horodatage(REFERENCE - timedelta(days=1)))

    soft, console, md = _report_amendements_freshness(cache_dir, staleness_days=0, reference_date=REFERENCE)

    assert any(legislature in w and "périmé" in w and "seuil 0" in w for w in soft)


# ---------------------------------------------------------------------------
# §3e — format de clé des index figés committés (correction du 18/08/2026,
# docs/decisions/amendements-cle-uid.md). Échec DUR, contrairement au
# reste de la section : un index keyé par `numero` ne porte pas des données
# périmées mais des amendements attribués au mauvais texte.
# ---------------------------------------------------------------------------

def _ecrire_index_fige(dossier: Path, legislature: str, refs: list) -> None:
    leg_dir = dossier / legislature
    leg_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(leg_dir / "index_par_acteur.json.gz", "wt", encoding="utf-8") as f:
        json.dump({"PA1": refs}, f)


def test_report_amendements_figes_format_accepte_un_index_keye_par_uid(tmp_path):
    for legislature in _AMENDEMENTS_LEGISLATURES_FIGEES:
        _ecrire_index_fige(
            tmp_path, legislature,
            [{"uid": "AMANR5L16PO1B0001P0D1N1", "role_signataire": "auteur_principal"}],
        )

    hard, console, md = _report_amendements_figes_format(tmp_path)

    assert hard == []
    assert "uid" in console


def test_report_amendements_figes_format_bloque_un_index_keye_par_numero(tmp_path):
    """Régression : un index hérité doit faire échouer le gate, pas passer avec
    un avertissement — c'est ce qui empêche de re-committer la donnée fausse."""
    _ecrire_index_fige(tmp_path, "16", [{"numero": "1", "role_signataire": "auteur_principal"}])

    hard, console, md = _report_amendements_figes_format(tmp_path)

    assert len(hard) == 1
    assert "16" in hard[0] and "hérité" in hard[0]
    # Le message doit porter la commande de reconstruction : sans elle, le
    # blocage ne dit pas quoi faire.
    assert "build_amendements_index_figees.py" in hard[0]


def test_report_amendements_figes_format_ignore_un_index_absent(tmp_path):
    """L'absence d'index est traitée par la §3d (« jamais construit ») : cette
    section-ci ne se prononce que sur le format de ce qui existe."""
    hard, _console, _md = _report_amendements_figes_format(tmp_path)

    assert hard == []


def test_report_amendements_figes_format_signale_un_index_illisible(tmp_path):
    leg_dir = tmp_path / "16"
    leg_dir.mkdir(parents=True)
    (leg_dir / "index_par_acteur.json.gz").write_bytes(b"pas du gzip")

    hard, _console, _md = _report_amendements_figes_format(tmp_path)

    assert len(hard) == 1
    assert "illisible" in hard[0]


# ---------------------------------------------------------------------------
# Couverture `uid` partielle dans un même profil (#447)
#
# Ce défaut est resté deux jours sans être identifié parce que RIEN ne le
# signalait : ni les logs d'extraction, ni cette gate. Il a été pris pour de
# l'instabilité de collecte, alors qu'il matérialise deux versions du même
# amendement dans un même profil — celle résolue sur la clé écrasée d'avant
# #440, et celle résolue sur `uid`. Un amendement compté deux fois n'est pas
# une donnée incomplète, c'est un fait faux, et les dénominateurs publiés en
# dépendent (AGENTS.md §2.7). Cause : #450.
# ---------------------------------------------------------------------------

def _amendement(uid=None):
    return {"uid": uid, "sort": "adopté", "type_deposant": "depute"}


def test_couverture_uid_partielle_est_signalee(tmp_path):
    _write_pivot(
        tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"},
        amendements=[_amendement("AMANR5L17-1"), _amendement(), _amendement()],
        warnings=[],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert regression is None, "signal distinct de celui de #378, ne doit pas le déclencher"
    assert len(soft) == 1
    assert "jean-dupont" in soft[0]
    assert "2/3 amendements sans uid" in soft[0]
    assert _AMENDEMENTS_UID_MIXTE_ICONE in console
    assert _AMENDEMENTS_UID_MIXTE_ICONE in md


def test_couverture_uid_complete_ne_signale_rien(tmp_path):
    _write_pivot(
        tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"},
        amendements=[_amendement("AMANR5L17-1"), _amendement("AMANR5L17-2")],
        warnings=[],
    )

    soft, _, console, _ = _report_amendements_coverage(tmp_path)

    assert soft == []
    assert _AMENDEMENTS_UID_MIXTE_ICONE not in console


def test_couverture_uid_nulle_n_est_pas_signalee_comme_mixte(tmp_path):
    """Un profil entièrement sur l'ancienne clé est en retard de correction
    (#440), pas dupliqué : c'est une frontière de conquête, pas un fait faux.
    Le confondre avec un profil mixte noierait le signal utile sous les 119
    profils qui attendent leur régénération."""
    _write_pivot(
        tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"},
        amendements=[_amendement(), _amendement()],
        warnings=[],
    )

    soft, _, console, _ = _report_amendements_coverage(tmp_path)

    assert soft == []
    assert _AMENDEMENTS_UID_MIXTE_ICONE not in console


def test_couverture_uid_globale_est_chiffree(tmp_path):
    """Le taux global sert à décider si une re-mesure de #429 est exploitable :
    un comptage d'amendements distincts repose sur l'`uid`."""
    _write_pivot(
        tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"},
        amendements=[_amendement("AMANR5L17-1"), _amendement()],
        warnings=[],
    )
    _write_pivot(
        tmp_path, "marie-martin", "AN", {"nom_complet": "Marie Martin"},
        amendements=[_amendement("AMANR5L17-2"), _amendement("AMANR5L17-3")],
        warnings=[],
    )

    _, _, console, md = _report_amendements_coverage(tmp_path)

    assert "Amendements : 4" in console
    assert "dont uid : 3 (75.0 %)" in console
    assert "| dont portant un `uid` | 3 (75.0 %) |" in md


def test_couverture_uid_partielle_ne_bloque_jamais_le_commit(tmp_path, monkeypatch, capsys):
    """Soft, comme tout le reste de la §3c (#378). Pendant la fenêtre de remise
    en état de #450, les profils mixtes SONT attendus : faire échouer la gate
    bloquerait précisément les runs censés les corriger. Ce qui manquait
    n'était pas un verrou, c'était un signal."""
    code = _run_main(monkeypatch, tmp_path, cache_dir=None, pivots={
        "jean-dupont": [_amendement("AMANR5L17-1"), _amendement()],
        "marie-martin": [_amendement("AMANR5L17-2")],
    })
    sortie = capsys.readouterr().out

    assert code == 0
    assert "COMMIT AUTORISÉ" in sortie
    assert _AMENDEMENTS_UID_MIXTE_ICONE in sortie


def test_report_amendements_coverage_couvre_les_amendements_hors_population_an(tmp_path):
    """Angle mort mesuré le 19/08/2026 (#447) : un profil peut PUBLIER des
    amendements AN sans appartenir à la population « candidat AN avec identité »
    de la §3c. `jean-luc-melenchon` — 18 721 amendements AN — est sorti du champ
    de la section en passant à `chambre: "Senat"` avec `identite` vide, soit
    2,3 % du corpus rendus invisibles au signal même qui doit les surveiller.

    La mesure de couverture `uid` doit donc suivre les amendements publiés, pas
    la fiche : un tel profil, s'il est mixte, doit être signalé."""
    _write_pivot(
        tmp_path,
        "jean-luc-melenchon",
        "Senat",
        None,
        amendements=[{"uid": "AMANR5L17PO1B1P0D1N1"}, {"numero": "12"}],
        warnings=[],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert any("jean-luc-melenchon" in w and "sans uid" in w for w in soft), soft
    assert _AMENDEMENTS_UID_MIXTE_ICONE in console
    # Ses amendements entrent bien dans le dénominateur global.
    assert "| Amendements | 2 |" in md


def test_report_amendements_coverage_hors_population_an_ne_fausse_pas_les_compteurs(tmp_path):
    """Contrepartie du test précédent : les lignes ajoutées pour leurs seuls
    amendements ne doivent ni gonfler « Profils AN avec identité » — le compteur
    s'appelait « Candidats AN avec identité » jusqu'à #630, alors qu'il compte
    477 profils dont 468 membres de roster —, ni
    éteindre le signal de régression globale « amendements[] vide partout »,
    qui porte sur la population dont on ATTEND des amendements."""
    _write_pivot(tmp_path, "jean-dupont", "AN", {"nom_complet": "Jean Dupont"}, amendements=[], warnings=[])
    _write_pivot(
        tmp_path,
        "senateur-x",
        "Senat",
        None,
        amendements=[{"uid": "AMANR5L17PO1B1P0D1N1"}],
        warnings=[],
    )

    soft, regression, console, md = _report_amendements_coverage(tmp_path)

    assert regression is not None and "aucun profil AN sur 1" in regression
    assert "| ⚠️ Profils AN avec identité | 1 (1 candidats · 0 membres de roster) |" in md
    # Chaque compteur garde un sens unique : l'apport hors population AN est
    # rendu explicite au lieu d'être fondu dans les compteurs « candidats AN ».
    assert "| Avec ≥ 1 amendement | 0 |" in md
    assert "| Dont hors population AN | 1 profil(s), 1 amendement(s) |" in md
    assert "Dont hors population AN : 1 profil(s), 1 amendement(s)" in console
