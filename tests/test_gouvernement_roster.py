import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gouvernement_roster import (
    _parse_date,
    _periods_overlap,
    _expected_label,
    _est_mandat_appartenance_gouvernement,
    _mandate_matches_gouvernement,
    _derive_membre_entry,
    _dedupliquer_membres,
    _normalise_fonction,
    _normalise_libelle_organe,
    _est_libelle_chef_du_gouvernement,
    _qualite_portefeuille,
    FONCTIONS_MINISTERIELLES,
    LABELS_PORTEFEUILLE_PREMIER_MINISTRE,
    LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES,
    FONCTIONS_MINISTERIELLES_OBSERVEES,
    FONCTIONS_NON_MINISTERIELLES_OBSERVEES,
    QUALITE_INCONNUE,
    QUALITE_MINISTERIELLE,
    QUALITE_NON_MINISTERIELLE,
    build_gouvernement_roster,
    build_premier_ministre,
    BLOCS_LUS_COMPOSITION,
    load_profils_from_dir,
    load_gouvernement_config,
    main as gouvernement_roster_main,
)
from schema_gouvernement import REQUIRED_MEMBRE_KEYS, REQUIRED_PREMIER_MINISTRE_KEYS

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/gouvernements_reels.json")

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _pivot(
    id_: str = "nosdeputes:jean-dupont",
    nom: str = "Jean Dupont",
    mandats: list = None,
) -> dict:
    """Construit un profil pivot v1 minimal pour les tests."""
    return {
        "schema_version": "1",
        "id": id_,
        "nom": nom,
        "chambre": "AN",
        "parti": None,
        "groupe": None,
        "sources": [],
        "mandats": mandats if mandats is not None else [],
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
        "fonction": "membre",
        "label": label,
        "debut": debut,
        "fin": fin,
        "actif": actif,
        "source_url": "https://data.assemblee-nationale.fr/static/openData/repository/...",
        "position_dans_hemicycle": "gouvernement",
    }


def _mandat_portefeuille(
    label: str,
    debut: str,
    fin: str = None,
    actif: bool = False,
    fonction: str = "Ministre",
) -> dict:
    """Mandat `typeOrgane == "MINISTERE"` tel qu'il apparaît dans un pivot :
    même catégorie que le mandat d'appartenance, mais label de portefeuille, et
    **sans** `source_url` (aucun mandat de ce chemin n'en porte).

    `fonction` reprend `infosQualite.libQualite` du zip AMO30 — c'est le champ
    qui sépare un maroquin d'une mission parlementaire (#474). Ces fabriques
    portaient `type` et non `fonction` : la clé `type` est celle produite par
    `candidate_profile._extract_mandats_officiels`, mais
    `normalize_profil` la renomme en `fonction` avant écriture du pivot,
    et c'est un pivot que `gouvernement_roster` lit. Les fixtures figées de
    #457 portent bien `fonction` ; ces fabriques les suivent désormais.
    """
    return {
        "categorie": "fonction_gouvernementale",
        "fonction": fonction,
        "label": label,
        "debut": debut,
        "fin": fin,
        "actif": actif,
        "source_url": None,
        "position_dans_hemicycle": None,
    }


# ---------------------------------------------------------------------------
# _parse_date / _periods_overlap
# ---------------------------------------------------------------------------

def test_parse_date_valid():
    assert _parse_date("2024-01-10").isoformat() == "2024-01-10"


def test_parse_date_none_and_invalid():
    assert _parse_date(None) is None
    assert _parse_date("") is None
    assert _parse_date("not-a-date") is None


def test_periods_overlap_both_unbounded():
    assert _periods_overlap(None, None, None, None) is True


def test_periods_overlap_clearly_before():
    m_debut, m_fin = _parse_date("2020-01-01"), _parse_date("2020-06-01")
    g_debut, g_fin = _parse_date("2021-01-01"), _parse_date("2021-06-01")
    assert _periods_overlap(m_debut, m_fin, g_debut, g_fin) is False


def test_periods_overlap_clearly_after():
    m_debut, m_fin = _parse_date("2022-01-01"), None
    g_debut, g_fin = _parse_date("2021-01-01"), _parse_date("2021-06-01")
    assert _periods_overlap(m_debut, m_fin, g_debut, g_fin) is False


def test_periods_overlap_true_when_intersecting():
    m_debut, m_fin = _parse_date("2021-03-01"), _parse_date("2021-09-01")
    g_debut, g_fin = _parse_date("2021-01-01"), _parse_date("2021-06-01")
    assert _periods_overlap(m_debut, m_fin, g_debut, g_fin) is True


def test_periods_overlap_still_active_mandate():
    m_debut, m_fin = _parse_date("2025-10-13"), None
    g_debut, g_fin = _parse_date("2025-10-13"), None
    assert _periods_overlap(m_debut, m_fin, g_debut, g_fin) is True


# ---------------------------------------------------------------------------
# _expected_label / _mandate_matches_gouvernement
# ---------------------------------------------------------------------------

def test_expected_label_with_sigle():
    assert _expected_label("LECORNU II") == "Gouvernement (LECORNU II)"


def test_expected_label_without_sigle():
    assert _expected_label("") == "Gouvernement"


def test_mandate_matches_gouvernement_true():
    mandat = _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")
    g_debut, g_fin = _parse_date("2024-12-24"), _parse_date("2025-09-09")
    assert _mandate_matches_gouvernement(mandat, "BAYROU", g_debut, g_fin) is True


def test_mandate_matches_gouvernement_wrong_categorie():
    mandat = {
        "categorie": "commission",
        "label": "Gouvernement (BAYROU)",
        "debut": "2024-12-24",
        "fin": "2025-09-09",
        "actif": False,
    }
    g_debut, g_fin = _parse_date("2024-12-24"), _parse_date("2025-09-09")
    assert _mandate_matches_gouvernement(mandat, "BAYROU", g_debut, g_fin) is False


def test_mandate_matches_gouvernement_wrong_label_same_period():
    """Chevauchement de période sans correspondance de libellé : exclu (voir
    docstring du module — le libellé prime sur la seule période)."""
    mandat = _mandat_gouv("Gouvernement (ATTAL)", "2024-12-24", "2025-09-09")
    g_debut, g_fin = _parse_date("2024-12-24"), _parse_date("2025-09-09")
    assert _mandate_matches_gouvernement(mandat, "BAYROU", g_debut, g_fin) is False


def test_mandate_matches_gouvernement_matching_label_disjoint_period():
    """Libellé correspondant mais période totalement disjointe : anomalie de
    données, exclue plutôt qu'incluse à tort."""
    mandat = _mandat_gouv("Gouvernement (BAYROU)", "2010-01-01", "2010-06-01")
    g_debut, g_fin = _parse_date("2024-12-24"), _parse_date("2025-09-09")
    assert _mandate_matches_gouvernement(mandat, "BAYROU", g_debut, g_fin) is False


# ---------------------------------------------------------------------------
# build_gouvernement_roster — cas synthétiques
# ---------------------------------------------------------------------------

def test_build_roster_single_matching_member():
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert len(membres) == 1
    assert membres[0]["membre_id"] == "nosdeputes:x"
    assert membres[0]["nom"] == "X"
    assert membres[0]["portefeuille"] is None
    assert membres[0]["source_url"] is None


def test_build_roster_membre_entry_has_all_required_keys():
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert set(membres[0].keys()) == REQUIRED_MEMBRE_KEYS


def test_build_roster_pivot_without_any_governmental_mandate_excluded():
    """Pivot sans mandat gouvernemental : absent du roster."""
    profils = [
        _pivot("nosdeputes:y", "Y", mandats=[
            {"categorie": "mandat_electif", "label": "Mandat parlementaire", "debut": "2022-06-22", "fin": None, "actif": True},
        ]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert membres == []


def test_build_roster_different_government_excluded():
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[_mandat_gouv("Gouvernement (ATTAL)", "2024-01-10", "2024-09-05")]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert membres == []


def test_build_roster_multiple_members():
    profils = [
        _pivot("nosdeputes:a", "A", mandats=[_mandat_gouv("Gouvernement (LECORNU II)", "2025-10-13", None, actif=True)]),
        _pivot("nosdeputes:b", "B", mandats=[_mandat_gouv("Gouvernement (LECORNU II)", "2025-10-13", "2026-02-26")]),
    ]
    membres = build_gouvernement_roster("LECORNU II", "2025-10-13", None, profils)
    ids = {m["membre_id"] for m in membres}
    assert ids == {"nosdeputes:a", "nosdeputes:b"}


def test_build_roster_membre_with_split_mandate_two_periods():
    """Un même membre avec deux mandats distincts pour un même gouvernement
    (changement de portefeuille en cours de gouvernement) : les deux
    entrées sont conservées, une par période (voir schema_gouvernement.py:
    'un enregistrement par ministre et par période si changement de
    portefeuille')."""
    profils = [
        _pivot("nosdeputes:z", "Z", mandats=[
            _mandat_gouv("Gouvernement (BORNE)", "2022-05-21", "2023-07-20"),
            _mandat_gouv("Gouvernement (BORNE)", "2023-07-21", "2024-01-09"),
        ]),
    ]
    membres = build_gouvernement_roster("BORNE", "2022-05-21", "2024-01-09", profils)
    assert len(membres) == 2
    assert {(m["debut"], m["fin"]) for m in membres} == {
        ("2022-05-21", "2023-07-20"),
        ("2023-07-21", "2024-01-09"),
    }


def test_build_roster_ambiguous_overlap_two_successive_governments():
    """Cas de chevauchement de période ambigu : un mandat d'un gouvernement
    voisin (période adjacente/chevauchante par erreur de saisie) n'est
    jamais confondu avec le gouvernement ciblé grâce au libellé exact."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BARNIER)", "2024-09-28", "2024-12-13"),
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
        ]),
    ]
    membres_bayrou = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert len(membres_bayrou) == 1
    assert membres_bayrou[0]["debut"] == "2024-12-24"

    membres_barnier = build_gouvernement_roster("BARNIER", "2024-09-28", "2024-12-13", profils)
    assert len(membres_barnier) == 1
    assert membres_barnier[0]["debut"] == "2024-09-28"


# ---------------------------------------------------------------------------
# build_gouvernement_roster — pivots réels, figés en fixtures (#457)
# ---------------------------------------------------------------------------

FIXTURES_PIVOTS_DIR = Path(__file__).resolve().parent / "fixtures" / "gouvernement_roster"


def _load_pivot_fixture(slug: str) -> dict:
    """Charge un pivot réel **figé** sous `tests/fixtures/gouvernement_roster/`.

    Ces tests sont les vérifications d'acceptation de #209 : ils confrontent
    `build_gouvernement_roster` à de vrais profils, pas à des cas fabriqués.
    Ils lisaient `pivot_data/profiles/` directement, et cassaient donc à chaque
    mise à jour du corpus — y compris quand la donnée **s'améliore** (#457 : un
    portefeuille jusque-là manquant a fini par être renseigné, et le test l'a
    signalé comme un échec). Un test qui rougit parce qu'une lacune a été
    comblée envoie le mauvais signal : la couverture du corpus vivant relève du
    quality gate (`check_quality_gate.py` §5), pas d'une assertion unitaire.

    Les fixtures sont donc des **extraits** des vrais pivots, réduits aux seuls
    champs que `gouvernement_roster` lit (`id`, `nom`, `identite.source_url`,
    `mandats[]`) et aux catégories de mandat `fonction_gouvernementale` et
    `mandat_electif` — quelques Ko au lieu de quelques centaines. `mandats[]`
    conserve l'ordre de la source : le roster émet ses entrées dans cet ordre.
    `mandat_electif` est gardé bien qu'inerte ici, pour que le filtrage par
    catégorie porte réellement sur quelque chose.

    Chaque fixture consigne sa provenance dans `meta.fixture` (fichier source,
    ref du dépôt, date d'extraction — AGENTS.md §2.2) : la rafraîchir, c'est
    rejouer cette même réduction sur le pivot courant.
    """
    path = FIXTURES_PIVOTS_DIR / f"{slug}.pivot.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_pivot_gabriel_attal_attal_government():
    profil = _load_pivot_fixture("gabriel-attal")
    membres = build_gouvernement_roster("ATTAL", "2024-01-10", "2024-09-05", [profil])
    assert len(membres) == 1
    assert membres[0]["membre_id"] == "nosdeputes:gabriel-attal"
    assert membres[0]["debut"] == "2024-01-10"
    assert membres[0]["fin"] == "2024-09-05"
    assert membres[0]["actif"] is False


def test_real_pivot_gabriel_attal_excluded_from_unrelated_government():
    """Gabriel Attal n'a jamais siégé dans le gouvernement Barnier."""
    profil = _load_pivot_fixture("gabriel-attal")
    membres = build_gouvernement_roster("BARNIER", "2024-09-28", "2024-12-13", [profil])
    assert membres == []


def test_real_pivot_charlotte_parmentier_lecocq_bayrou_government():
    """Vérification manuelle (acceptation #209) : Gouvernement Bayrou contre
    un profil pivot réel.

    Ce profil porte cinq portefeuilles ministériels, répartis sur trois
    gouvernements. Le test vérifie que celui rattaché est **celui de la période
    Bayrou** (2024-12-24 → 2025-09-09) : c'est l'objet de
    `_portefeuilles_du_mandat`, qui teste le chevauchement contre le mandat
    d'appartenance du membre. Il assenait auparavant `portefeuille is None`,
    ce qui figeait une lacune de données en invariant (#457) — l'intitulé est
    renseigné depuis, et le test échouait pour cette raison-là.
    """
    profil = _load_pivot_fixture("charlotte-parmentier-lecocq")
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", [profil])
    assert len(membres) == 1
    assert membres[0]["nom"] == "Charlotte Parmentier-Lecocq"
    assert membres[0]["portefeuille"] == (
        "Ministère délégué auprès de la ministre du travail, de la santé, "
        "de la solidarité et des familles, chargé de l'autonomie et du handicap"
    )
    assert membres[0]["debut"] == "2024-12-24"
    assert membres[0]["fin"] == "2025-09-09"
    # Renseigné implique traçable : le schéma refuse un intitulé sans source.
    assert membres[0]["source_url"]


def test_real_pivot_david_amiel_lecornu_ii_deux_portefeuilles_un_seul_actif():
    """Vérification manuelle (acceptation #209) : Gouvernement Lecornu II
    contre un profil pivot réel, changement de portefeuille **sans changement
    de gouvernement**.

    David Amiel est ministre délégué chargé de la fonction publique jusqu'au
    2026-02-21, puis ministre de l'action et des comptes publics à partir du
    2026-02-22 — deux fonctions distinctes, deux périodes distinctes, un seul
    mandat d'appartenance (jamais scindé, lui). Le roster rend donc **deux
    entrées pour un même `membre_id`**, une par période : les fondre en une
    seule effacerait un fait vérifiable (AGENTS.md §2.2), et en choisir une
    arbitrairement serait pire encore.

    Corollaire à connaître (#457) : `membres[]` dénombre des **entrées**, pas
    des personnes. Sur les 10 gouvernements publiés, 7 sont concernés — 113
    entrées pour 95 personnes au 20/08/2026 (#480 a retiré les 2 seules
    répétitions strictes de l'écart), Borne à lui seul 31 entrées pour 23
    personnes.
    Rien ne publie d'effectif aujourd'hui : `comptages.par_statut` dénombre des
    textes de loi, et `GovernmentProfile.jsx` liste les membres sans en donner
    le total. Aucun dénominateur faux n'est donc exposé (§2.7). Mais toute vue
    future annonçant « N ministres » devra dédupliquer par `membre_id`, sans
    quoi elle affichera 31 pour Borne au lieu de 23.
    """
    profil = _load_pivot_fixture("david-amiel")
    membres = build_gouvernement_roster("LECORNU II", "2025-10-13", None, [profil])
    assert len(membres) == 2
    assert {m["membre_id"] for m in membres} == {"nosdeputes:david-amiel"}

    # Ordre chronologique : `_portefeuilles_du_mandat` trie par date de début.
    delegue, ministre = membres
    assert delegue["portefeuille"].startswith(
        "Ministère délégué auprès de la ministre de l'action et des comptes publics"
    )
    assert delegue["debut"] == "2025-10-13"
    assert delegue["fin"] == "2026-02-21"
    assert delegue["actif"] is False

    assert ministre["portefeuille"] == "Ministère de l'action et des comptes publics"
    assert ministre["debut"] == "2026-02-22"
    assert ministre["fin"] is None
    assert ministre["actif"] is True

    # Les deux périodes se succèdent sans trou ni recouvrement : elles pavent
    # le mandat d'appartenance, elles ne le comptent pas deux fois.
    assert delegue["fin"] < ministre["debut"]


# ---------------------------------------------------------------------------
# portefeuille ministériel (#398)
# ---------------------------------------------------------------------------

def test_est_mandat_appartenance_gouvernement_distingue_les_deux_natures():
    """La catégorie `fonction_gouvernementale` mélange l'appartenance
    (typeOrgane GOUVERNEMENT) et le portefeuille (MINISTERE) : seul le label
    les distingue."""
    assert _est_mandat_appartenance_gouvernement("Gouvernement (BORNE)") is True
    assert _est_mandat_appartenance_gouvernement("Gouvernement") is True
    assert _est_mandat_appartenance_gouvernement("Premier ministre") is False
    assert _est_mandat_appartenance_gouvernement(
        "Ministère de l'éducation nationale et de la jeunesse"
    ) is False


def test_build_roster_portefeuille_renseigne_avec_sa_source():
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille("Ministère de l'intérieur", "2024-12-24", "2025-09-09"),
        ]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert len(membres) == 1
    assert membres[0]["portefeuille"] == "Ministère de l'intérieur"
    # Le schéma exige une source dès que le portefeuille est renseigné : elle
    # est reprise du mandat d'appartenance, issu du même zip AMO30.
    assert membres[0]["source_url"]


def test_build_roster_portefeuille_hors_periode_du_mandat_ignore():
    """Le portefeuille occupé dans un gouvernement antérieur ne doit pas être
    recopié sur le mandat courant."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille("Ministère de la culture", "2020-07-07", "2022-05-16"),
        ]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert len(membres) == 1
    assert membres[0]["portefeuille"] is None
    assert membres[0]["source_url"] is None


def test_build_roster_deux_portefeuilles_donnent_deux_entrees():
    """Chevauchements multiples : tous retenus, un enregistrement par période
    (§2.5 — ne jamais choisir arbitrairement l'un des deux)."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BORNE)", "2022-05-21", "2024-01-09"),
            _mandat_portefeuille("Ministère des comptes publics", "2022-05-21", "2023-07-20"),
            _mandat_portefeuille("Ministère de l'éducation nationale", "2023-07-21", "2024-01-09"),
        ]),
    ]
    membres = build_gouvernement_roster("BORNE", "2022-05-16", "2024-01-09", profils)
    assert len(membres) == 2
    assert [m["portefeuille"] for m in membres] == [
        "Ministère des comptes publics",
        "Ministère de l'éducation nationale",
    ]
    # Les dates sont celles de chaque portefeuille, pas celles du mandat
    # d'appartenance : c'est ce qui distingue les deux entrées.
    assert [(m["debut"], m["fin"]) for m in membres] == [
        ("2022-05-21", "2023-07-20"),
        ("2023-07-21", "2024-01-09"),
    ]
    assert all(set(m.keys()) == REQUIRED_MEMBRE_KEYS for m in membres)


def test_build_roster_portefeuille_sans_source_tracable_reste_null_avec_warning():
    """Sans source, l'intitulé n'est pas publiable (§2.3) : `portefeuille`
    retombe à null plutôt que d'être renseigné sans traçabilité."""
    mandat_sans_source = _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")
    mandat_sans_source["source_url"] = None
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            mandat_sans_source,
            _mandat_portefeuille("Ministère de l'intérieur", "2024-12-24", "2025-09-09"),
        ]),
    ]
    warnings = []
    membres = build_gouvernement_roster(
        "BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings
    )
    assert len(membres) == 1
    assert membres[0]["portefeuille"] is None
    assert len(warnings) == 1
    assert "Ministère de l'intérieur" in warnings[0]


def test_real_pivot_gabriel_attal_deux_portefeuilles_sous_borne():
    """Cas réel : Gabriel Attal a changé de portefeuille en cours de
    gouvernement Borne (comptes publics, puis éducation nationale)."""
    profil = _load_pivot_fixture("gabriel-attal")
    membres = build_gouvernement_roster("BORNE", "2022-05-16", "2024-01-09", [profil])
    assert len(membres) == 2
    portefeuilles = [m["portefeuille"] for m in membres]
    assert any("comptes publics" in p for p in portefeuilles)
    assert any("éducation nationale" in p for p in portefeuilles)
    assert all(m["source_url"] for m in membres)


# ---------------------------------------------------------------------------
# Parlementaire en mission ≠ ministre (#474)
# ---------------------------------------------------------------------------

def test_qualite_portefeuille_reconnait_les_qualites_ministerielles_observees():
    """Les 8 qualités ministérielles relevées sur les mandats `MINISTERE`.

    Sept venaient des profils publiés ; la huitième (« Haut-commissaire »)
    vient du balayage de l'archive AMO30 (#658), voir le test dédié ci-dessous.
    """
    for fonction in FONCTIONS_MINISTERIELLES_OBSERVEES:
        assert _qualite_portefeuille(fonction) == QUALITE_MINISTERIELLE, fonction


def test_qualite_portefeuille_en_mission_nest_pas_ministerielle():
    """Un parlementaire en mission (art. LO144) n'est pas ministre : c'est le
    fait qui a publié une attribution fausse (#474)."""
    for fonction in FONCTIONS_NON_MINISTERIELLES_OBSERVEES:
        assert _qualite_portefeuille(fonction) == QUALITE_NON_MINISTERIELLE, fonction
    assert "en mission" not in FONCTIONS_MINISTERIELLES


def test_qualite_portefeuille_valeur_inconnue_nest_jamais_un_portefeuille():
    """Liste blanche, pas liste noire (§2.5) : une 9e valeur qui apparaîtrait
    à pleine échelle est « inconnue », pas « ministérielle par défaut ».

    « Haut-commissaire au plan » n'est pas « Haut-commissaire » : la valeur
    ajoutée par #658 ne vaut que pour elle-même, aucun rapprochement par
    préfixe (`_normalise_fonction`).
    """
    assert _qualite_portefeuille("Haut-commissaire au plan") == QUALITE_INCONNUE
    assert _qualite_portefeuille(None) == QUALITE_INCONNUE
    assert _qualite_portefeuille("") == QUALITE_INCONNUE
    # `normalize_profil` remplace un `libQualite` absent par « membre » :
    # sur un mandat MINISTERE, c'est une lacune de source, pas une qualité.
    assert _qualite_portefeuille("membre") == QUALITE_INCONNUE


def test_qualite_haut_commissaire_est_ministerielle_par_lecture_du_referentiel():
    """« Haut-commissaire » est un maroquin **parce que la source le range
    ainsi**, pas parce que nous l'estimons équivalent à un ministre (#658).

    Relevé le 2026-08-31 sur `.cache/acteurs_historique_an/acteurs_historique.zip` :
    4 mandats, 2 personnes, tous `typeOrgane == "MINISTERE"`, tous rattachés à
    un organe de `codeType == "MINISTERE"` —

        PA1051    Jean-Paul Delevoye  PO766969  « Ministère des solidarités et
                                      de la santé – Retraites »  2019-09-04 → 2019-12-17
        PA387853  Martin Hirsch       PO383001  2007-05-18 → 2007-06-18
        PA387853  Martin Hirsch       PO388139  2007-06-19 → 2009-01-12
        PA387853  Martin Hirsch       PO418119  2009-01-12 → 2010-03-22

    L'organe de Delevoye est littéralement intitulé « Ministère ». C'est donc
    l'Assemblée nationale qui qualifie, pas nous (§2 règle 2).

    Aucun des deux acteurs n'a de profil pivot publié : ce test verrouille le
    classement avant que le cas ne se présente. Pas de fixture — inventer un
    pivot pour deux personnes qui n'en ont pas serait précisément la fixture
    fabriquée que #510 a fait supprimer.
    """
    assert "Haut-commissaire" in FONCTIONS_MINISTERIELLES_OBSERVEES
    assert _qualite_portefeuille("Haut-commissaire") == QUALITE_MINISTERIELLE

    # Effet de bout en bout : un tel mandat produit un portefeuille publié, et
    # non un `null` accompagné du warning « qualité inconnue ».
    profil = _pivot("nosdeputes:haut-commissaire", "Haut-Commissaire", mandats=[
        _mandat_gouv("Gouvernement (PHILIPPE 2)", "2017-06-22", "2020-07-06"),
        _mandat_portefeuille(
            "Ministère des solidarités et de la santé – Retraites",
            "2019-09-04", "2019-12-17", fonction="Haut-commissaire",
        ),
    ])
    warnings = []
    membres = build_gouvernement_roster(
        "PHILIPPE 2", "2017-06-22", "2020-07-06", [profil], warnings=warnings
    )
    assert len(membres) == 1
    assert membres[0]["portefeuille"] == (
        "Ministère des solidarités et de la santé – Retraites"
    )
    assert warnings == []

    # Le double verrou de #474 n'est pas entamé : cette qualité ne fait pas
    # d'un mandat de libellé « Premier ministre » un chef du gouvernement.
    profil_pm = _pivot("nosdeputes:x", "X", mandats=[
        _mandat_gouv("Gouvernement (PHILIPPE 2)", "2017-06-22", "2020-07-06"),
        _mandat_portefeuille(
            "Premier ministre", "2017-06-22", "2020-07-06",
            fonction="Haut-commissaire",
        ),
    ])
    assert build_premier_ministre(
        "PHILIPPE 2", "2017-06-22", "2020-07-06", [profil_pm]
    ) is None


def test_normalise_fonction_casse_et_espaces_seulement():
    """La source écrit « Garde des sceaux » et « Garde des Sceaux » pour la
    même qualité : normalisation typographique, jamais sémantique."""
    assert _normalise_fonction("Garde des sceaux, ministre de la justice") == (
        _normalise_fonction("Garde des Sceaux, ministre de la justice")
    )
    assert _normalise_fonction("  Ministre   délégué ") == _normalise_fonction("Ministre délégué")
    # Deux libellés distincts restent distincts : aucun rapprochement par préfixe.
    assert _normalise_fonction("Ministre") != _normalise_fonction("Ministre délégué")


def test_build_roster_mandat_en_mission_nest_pas_un_portefeuille():
    """Cas synthétique minimal du défaut : le label d'un mandat de
    parlementaire en mission est l'intitulé du ministère **auprès duquel** la
    personne est missionnée — indiscernable d'un maroquin sur ce seul critère.
    """
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille(
                "Ministère de l'économie", "2024-12-24", "2025-09-09",
                fonction="en mission",
            ),
        ]),
    ]
    warnings = []
    membres = build_gouvernement_roster(
        "BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings
    )
    assert len(membres) == 1
    assert membres[0]["portefeuille"] is None
    assert membres[0]["source_url"] is None
    # Exclusion attendue, pas anomalie : 92 des 209 profils du dépôt portent au
    # moins un tel mandat. Un warning par occurrence noierait les vraies alertes.
    assert warnings == []


def test_build_roster_qualite_inconnue_warning_explicite_et_portefeuille_null():
    """Une qualité hors liste blanche ne devient jamais un portefeuille, et ne
    passe jamais en silence : warning nommant la personne, l'intitulé et la
    qualité rencontrée, pour que l'ajout à la liste soit une décision humaine."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille(
                "Ministère de l'intérieur", "2024-12-24", "2025-09-09",
                fonction="Haut-commissaire au plan",
            ),
        ]),
    ]
    warnings = []
    membres = build_gouvernement_roster(
        "BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings
    )
    assert len(membres) == 1
    assert membres[0]["portefeuille"] is None
    assert len(warnings) == 1
    assert "Haut-commissaire au plan" in warnings[0]
    assert "Ministère de l'intérieur" in warnings[0]
    assert "X" in warnings[0]


def test_build_roster_warning_de_qualite_inconnue_dedupe():
    """Deux mandats d'appartenance au même gouvernement réexaminent le même
    mandat ministériel : le fait est consigné une fois, pas deux."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", None, actif=True),
            _mandat_portefeuille(
                "Ministère de l'intérieur", "2024-12-24", "2025-09-09",
                fonction="Haut-commissaire au plan",
            ),
        ]),
    ]
    warnings = []
    build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings)
    assert len(warnings) == 1


def test_build_roster_portefeuille_posterieur_a_la_fin_du_gouvernement_exclu():
    """Second défaut de #474, indépendant de la qualité : un mandat
    d'appartenance jamais clos (`fin: null`) sur un gouvernement pourtant
    achevé accroche n'importe quel mandat ministériel postérieur.

    Sans borne sur la période du gouvernement, le portefeuille de 2026
    ci-dessous entrerait dans un gouvernement clos en 2025 — avec `actif:
    true` dans un gouvernement `actif: false`.
    """
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            # Le mandat d'appartenance sans fin, l'anomalie de source.
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", None, actif=True),
            _mandat_portefeuille(
                "Ministère de l'économie", "2026-02-04", None, actif=True,
                fonction="Ministre",
            ),
        ]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert len(membres) == 1
    assert membres[0]["portefeuille"] is None
    assert membres[0]["debut"] == "2024-12-24"


def test_build_roster_borne_gouvernement_ne_casse_pas_le_ministre_entre_en_cours():
    """Non-régression du garde-fou de #398 : la borne ajoutée par #474 ne fait
    que restreindre, elle ne peut rien rattraper.

    Un ministre entré en cours de mandature ne doit pas se voir attribuer le
    portefeuille qu'il occupait avant — même quand ce portefeuille antérieur
    chevauche, lui, la période du gouvernement.
    """
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            # Entré en cours de gouvernement.
            _mandat_gouv("Gouvernement (BORNE)", "2023-07-21", "2024-01-09"),
            # Portefeuille antérieur : dans la période du gouvernement, hors
            # de celle du mandat.
            _mandat_portefeuille(
                "Ministère de la culture", "2022-05-21", "2023-07-20",
                fonction="Ministre",
            ),
        ]),
    ]
    membres = build_gouvernement_roster("BORNE", "2022-05-21", "2024-01-09", profils)
    assert len(membres) == 1
    assert membres[0]["portefeuille"] is None


def test_real_pivot_astrid_panosyan_bouvet_pas_de_maroquin_fantome_sous_bayrou():
    """L'attribution fausse publiée sur `main` à `ea6f0d5` (#474).

    Le profil porte un mandat de parlementaire en mission auprès du ministère
    de l'économie (`fonction: "en mission"`, 2026-02-04, jamais clos) et
    **deux** mandats d'appartenance au gouvernement Bayrou, dont un jamais clos
    lui non plus. Le second accrochait le premier, et
    `gouvernement-BAYROU.json` publiait un portefeuille de l'économie daté du
    2026-02-04 dans un gouvernement achevé le 2025-09-09, `actif: true` dans un
    gouvernement `actif: false`.

    Les assertions portent sur des propriétés, pas sur un compte d'entrées :
    ce profil déclenchait par ailleurs une duplication d'entrées (deux mandats
    d'appartenance identiques en tout sauf leur `fin`), défaut distinct, hors
    périmètre de #474 et corrigé depuis par #480 — figer le compte ici le
    graverait en invariant, ce que #457 a précisément appris à ne pas faire.
    Le compte, lui, est vérifié par
    `test_real_pivot_bayrou_deux_mandats_dappartenance_une_entree_par_personne`.
    """
    profil = _load_pivot_fixture("astrid-panosyan-bouvet")
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", [profil])

    assert membres, "le mandat ministériel légitime sous Bayrou doit rester"
    assert not any(
        "économie" in (m["portefeuille"] or "") for m in membres
    ), "le ministère de la mission LO144 ne doit plus être attribué"
    # Aucun début postérieur à la fin du gouvernement, aucun actif dans un
    # gouvernement clos (critères d'acceptation de #474).
    assert all(m["debut"] <= "2025-09-09" for m in membres)
    assert all(m["actif"] is False for m in membres)
    # Le portefeuille réellement occupé, lui, est conservé.
    assert all(
        m["portefeuille"].startswith("Ministère auprès de la ministre du travail")
        for m in membres
    )
    assert all(m["source_url"] for m in membres)


def test_real_pivot_astrid_panosyan_bouvet_portefeuille_reel_conserve_sous_barnier():
    """Contrôle positif : le filtre ne rogne pas les vrais maroquins.

    Sous Barnier, la même personne détient « Ministère du travail et de
    l'emploi » (`fonction: "Ministre"`) — attribution qui doit rester intacte.
    """
    profil = _load_pivot_fixture("astrid-panosyan-bouvet")
    membres = build_gouvernement_roster("BARNIER", "2024-09-28", "2024-12-13", [profil])
    assert len(membres) == 1
    assert membres[0]["portefeuille"] == "Ministère du travail et de l’emploi"
    assert membres[0]["debut"] == "2024-09-22"
    assert membres[0]["source_url"]


def test_le_mandat_en_mission_reste_dans_le_profil():
    """#474 retire une attribution fausse, il ne supprime aucune donnée
    collectée : le mandat de parlementaire en mission est un fait public et
    traçable, il reste dans `mandats[]` du profil (critère d'acceptation).
    """
    for slug in ("astrid-panosyan-bouvet", "david-amiel"):
        profil = _load_pivot_fixture(slug)
        missions = [
            m for m in profil["mandats"]
            if m.get("categorie") == "fonction_gouvernementale"
            and m.get("fonction") == "en mission"
        ]
        assert missions, slug


# ---------------------------------------------------------------------------
# Déduplication des entrées `membres[]` (#480)
# ---------------------------------------------------------------------------

def test_build_roster_mandat_dappartenance_scinde_ne_publie_pas_deux_fois_le_meme_fait():
    """Deux mandats d'appartenance au même gouvernement, un seul portefeuille :
    une seule entrée (#480).

    C'est la forme fabriquée du cas Bayrou : la source AN porte deux mandats
    `GOUVERNEMENT` de même `dateDebut` pour le même organe, dont un jamais clos.
    Le portefeuille chevauche les deux, et l'entrée dérivée — dates du
    portefeuille, jamais du mandat d'appartenance — sort donc deux fois à
    l'identique. Le même fait, sourcé une fois, ne se publie pas deux fois
    (AGENTS.md §2.2).
    """
    profils = [
        _pivot("nosdeputes:y", "Y", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", None, actif=True),
            _mandat_portefeuille("Ministère du travail", "2024-12-24", "2025-09-09"),
        ]),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert len(membres) == 1
    assert membres[0]["portefeuille"] == "Ministère du travail"
    assert membres[0]["debut"] == "2024-12-24"
    assert membres[0]["fin"] == "2025-09-09"
    assert membres[0]["actif"] is False


def test_build_roster_changement_de_portefeuille_survit_a_la_deduplication():
    """Le garde-fou contre la sur-déduplication (#480).

    Même mandat d'appartenance scindé que le test précédent, mais **deux**
    portefeuilles successifs. Les entrées diffèrent alors par leur intitulé et
    leurs dates : ce sont deux faits, pas une répétition, et
    `schema_gouvernement.py` les prévoit explicitement (« un enregistrement par
    ministre et par période si changement de portefeuille »). Une déduplication
    par `membre_id` seul les fondrait — c'est précisément ce que ce test
    interdit. Sur le corpus au 20/08/2026, 18 des 20 entrées surnuméraires sont
    de cette nature ; les fondre effacerait 18 faits réels.
    """
    profils = [
        _pivot("nosdeputes:y", "Y", mandats=[
            _mandat_gouv("Gouvernement (BORNE)", "2022-05-21", "2024-01-09"),
            _mandat_gouv("Gouvernement (BORNE)", "2022-05-21", None, actif=True),
            _mandat_portefeuille("Ministère de la transition", "2022-05-21", "2023-07-20"),
            _mandat_portefeuille("Ministère de l'éducation", "2023-07-21", "2024-01-09"),
        ]),
    ]
    membres = build_gouvernement_roster("BORNE", "2022-05-21", "2024-01-09", profils)
    assert len(membres) == 2
    assert {m["membre_id"] for m in membres} == {"nosdeputes:y"}
    assert [m["portefeuille"] for m in membres] == [
        "Ministère de la transition",
        "Ministère de l'éducation",
    ]
    assert [(m["debut"], m["fin"]) for m in membres] == [
        ("2022-05-21", "2023-07-20"),
        ("2023-07-21", "2024-01-09"),
    ]


def test_dedupliquer_membres_garde_les_deux_entrees_divergentes_hors_identite():
    """Deux entrées de même identité mais de `source_url` différentes ne sont
    **pas** fusionnées : aucune n'est plus traçable que l'autre, en choisir une
    serait arbitraire et les fondre perdrait une source (AGENTS.md §2.5).

    Le cas ne se présente pas sur le corpus au 20/08/2026 — les deux mandats
    d'appartenance scindés portent la même URL AMO30. Le warning existe pour
    qu'il ne passe pas inaperçu s'il apparaissait.
    """
    entree = {
        "membre_id": "nosdeputes:y",
        "nom": "Y",
        "portefeuille": "Ministère du travail",
        "debut": "2024-12-24",
        "fin": "2025-09-09",
        "actif": False,
        "source_url": "https://data.assemblee-nationale.fr/a.zip",
    }
    autre_source = dict(entree, source_url="https://data.assemblee-nationale.fr/b.zip")

    warnings: list[str] = []
    uniques = _dedupliquer_membres([entree, autre_source], warnings)
    assert len(uniques) == 2
    assert len(warnings) == 1
    assert "divergent hors identité" in warnings[0]

    # Strictement identiques : plus de warning, une seule entrée.
    warnings_stricts: list[str] = []
    assert _dedupliquer_membres([entree, dict(entree)], warnings_stricts) == [entree]
    assert warnings_stricts == []


def test_real_pivot_bayrou_deux_mandats_dappartenance_une_entree_par_personne():
    """Le cas réel de #480, sur fixtures figées.

    `astrid-panosyan-bouvet` et `marc-ferracci` portent chacun deux mandats
    d'appartenance au gouvernement Bayrou (même `debut`, l'un clos au
    2025-09-09, l'autre jamais clos et `actif: true`) et un seul portefeuille
    chevauchant les deux. `membres[]` publiait deux entrées strictement
    identiques par personne. Le roster en rend désormais une chacune.

    Assertions de propriété, pas de compte figé sur le corpus (#457) : les
    fixtures sont figées, le compte porte sur elles seules.
    """
    profils = [
        _load_pivot_fixture("astrid-panosyan-bouvet"),
        _load_pivot_fixture("marc-ferracci"),
    ]
    membres = build_gouvernement_roster("BAYROU", "2024-12-24", "2025-09-09", profils)

    assert len(membres) == 2
    assert {m["membre_id"] for m in membres} == {
        "nosdeputes:astrid-panosyan-bouvet",
        "nosdeputes:marc-ferracci",
    }
    # Aucune entrée n'est la répétition d'une autre, sur l'identité du fait
    # publié comme sur l'entrée entière.
    identites = [
        (m["membre_id"], m["portefeuille"], m["debut"], m["fin"], m["actif"])
        for m in membres
    ]
    assert len(set(identites)) == len(membres)
    assert all(m["source_url"] for m in membres)


def test_real_pivot_marc_ferracci_portefeuille_reel_conserve_sous_barnier():
    """Contrôle positif sur la fixture ajoutée par #480 : la déduplication ne
    rogne pas le portefeuille que la même personne détenait sous Barnier — un
    autre gouvernement, un autre fait."""
    profil = _load_pivot_fixture("marc-ferracci")
    membres = build_gouvernement_roster("BARNIER", "2024-09-28", "2024-12-13", [profil])
    assert len(membres) == 1
    assert membres[0]["portefeuille"].startswith("Ministère délégué auprès du ministre")
    assert membres[0]["debut"] == "2024-09-22"
    assert membres[0]["fin"] == "2024-12-13"


# ---------------------------------------------------------------------------
# build_premier_ministre (#398)
# ---------------------------------------------------------------------------

def test_build_premier_ministre_nominal():
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille(
                "Premier ministre", "2024-12-24", "2025-09-09",
                fonction="Premier ministre",
            ),
        ]),
    ]
    pm = build_premier_ministre("BAYROU", "2024-12-24", "2025-09-09", profils)
    assert pm is not None
    assert pm["nom"] == "X"
    assert set(pm.keys()) == REQUIRED_PREMIER_MINISTRE_KEYS


def test_build_premier_ministre_aucun_candidat_reste_none():
    """Cas attendu et majoritaire : le Premier ministre n'a pas de profil
    pivot local. Aucune valeur déduite du nom du gouvernement (§2.5)."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille("Ministère de l'intérieur", "2024-12-24", "2025-09-09"),
        ]),
    ]
    warnings = []
    assert build_premier_ministre(
        "BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings
    ) is None
    assert warnings == []


def test_build_premier_ministre_ambigu_reste_none_avec_warning():
    """Deux candidats : trancher serait arbitraire — None + warning."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille(
                "Premier ministre", "2024-12-24", "2025-09-09",
                fonction="Premier ministre",
            ),
        ]),
        _pivot("nosdeputes:y", "Y", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille(
                "Premier ministre", "2024-12-24", "2025-09-09",
                fonction="Premier ministre",
            ),
        ]),
    ]
    warnings = []
    assert build_premier_ministre(
        "BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings
    ) is None
    assert len(warnings) == 1
    assert "Premiers ministres possibles" in warnings[0]


def test_build_premier_ministre_dun_autre_gouvernement_non_retenu():
    """Le mandat d'appartenance désambiguïse : un Premier ministre d'un autre
    gouvernement n'est jamais capté par simple proximité de période."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (ATTAL)", "2024-01-10", "2024-09-05"),
            _mandat_portefeuille(
                "Premier ministre", "2024-01-10", "2024-09-05",
                fonction="Premier ministre",
            ),
        ]),
    ]
    assert build_premier_ministre("BARNIER", "2024-09-21", "2024-12-13", profils) is None


def test_real_pivot_premier_ministre_attal_et_philippe():
    """Cas réels : les seuls Premiers ministres ayant un profil pivot local."""
    attal = _load_pivot_fixture("gabriel-attal")
    pm_attal = build_premier_ministre("ATTAL", "2024-01-10", "2024-09-05", [attal])
    assert pm_attal["nom"] == "Gabriel Attal"
    assert pm_attal["acteur_ref"] == "PA722190"
    assert pm_attal["source_url"]

    philippe = _load_pivot_fixture("edouard-philippe")
    pm_philippe = build_premier_ministre("PHILIPPE 2", "2017-06-20", "2020-07-06", [philippe])
    assert pm_philippe["nom"] == "Édouard Philippe"

    # Le même profil ne doit pas devenir Premier ministre d'un gouvernement
    # auquel il n'a pas appartenu.
    assert build_premier_ministre("BAYROU", "2024-12-24", "2025-09-09", [attal]) is None


def test_build_premier_ministre_missionne_ninvente_pas_un_premier_ministre():
    """Cas latent de #474 : le label « Premier ministre » est aussi celui d'une
    mission parlementaire **auprès de** Matignon.

    Seul en lice, un missionné ne doit pas devenir Premier ministre.
    """
    profils = [
        _pivot("nosdeputes:missionne", "Missionné", mandats=[
            _mandat_gouv("Gouvernement (ATTAL)", "2024-01-10", "2024-09-05"),
            _mandat_portefeuille(
                "Premier ministre", "2024-01-12", "2024-05-05",
                fonction="en mission",
            ),
        ]),
    ]
    warnings = []
    assert build_premier_ministre(
        "ATTAL", "2024-01-10", "2024-09-05", profils, warnings=warnings
    ) is None
    assert warnings == []


def test_build_premier_ministre_missionne_nefface_pas_le_vrai_premier_ministre():
    """Le dégât ne serait pas seulement d'inventer un Premier ministre : deux
    candidats font retourner `None` **avec un warning d'ambiguïté** (§2.5), donc
    un missionné pourrait *effacer* le vrai (#474).

    Cas synthétique et non fixture : les deux mandats existent bien dans le
    corpus — `nosdeputes:david-amiel` porte « Premier ministre » /
    `en mission` du 2024-01-12 au 2024-05-05, période du gouvernement Attal —
    mais son seul mandat d'appartenance est postérieur (Lecornu II,
    2025-10-13), si bien qu'aucun chevauchement ne se produit *aujourd'hui*.
    Le fait « en mission » lui-même est vérifié sur la fixture figée, ci-dessous
    et dans `test_le_mandat_en_mission_reste_dans_le_profil`.
    """
    profils = [
        _pivot("nosdeputes:vrai-pm", "Vrai PM", mandats=[
            _mandat_gouv("Gouvernement (ATTAL)", "2024-01-10", "2024-09-05"),
            _mandat_portefeuille(
                "Premier ministre", "2024-01-10", "2024-09-05",
                fonction="Premier ministre",
            ),
        ]),
        _pivot("nosdeputes:missionne", "Missionné", mandats=[
            _mandat_gouv("Gouvernement (ATTAL)", "2024-01-10", "2024-09-05"),
            _mandat_portefeuille(
                "Premier ministre", "2024-01-12", "2024-05-05",
                fonction="en mission",
            ),
        ]),
    ]
    warnings = []
    pm = build_premier_ministre(
        "ATTAL", "2024-01-10", "2024-09-05", profils, warnings=warnings
    )
    assert pm is not None, "le vrai Premier ministre ne doit pas être effacé"
    assert pm["nom"] == "Vrai PM"
    assert not any("Premiers ministres possibles" in w for w in warnings)


def test_build_premier_ministre_label_pm_mais_autre_qualite_warning():
    """Second verrou, propre à `build_premier_ministre` : une qualité
    ministérielle connue mais différente de « Premier ministre » sur un mandat
    de label « Premier ministre » est une incohérence de source — écartée avec
    un warning, jamais retenue en silence."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
            _mandat_portefeuille(
                "Premier ministre", "2024-12-24", "2025-09-09",
                fonction="Ministre délégué",
            ),
        ]),
    ]
    warnings = []
    assert build_premier_ministre(
        "BAYROU", "2024-12-24", "2025-09-09", profils, warnings=warnings
    ) is None
    assert len(warnings) == 1
    assert "Ministre délégué" in warnings[0]
    assert "#474" in warnings[0]


def test_real_pivot_david_amiel_mission_aupres_de_matignon_jamais_premier_ministre():
    """Fixture figée : David Amiel porte bien un mandat de label « Premier
    ministre » de qualité « en mission ». Il ne devient Premier ministre
    d'aucun des gouvernements auxquels il a appartenu, et son roster Lecornu II
    ne fait apparaître aucun portefeuille « Premier ministre »."""
    profil = _load_pivot_fixture("david-amiel")
    mission = [
        m for m in profil["mandats"]
        if m.get("label") == "Premier ministre" and m.get("fonction") == "en mission"
    ]
    assert len(mission) == 1

    warnings = []
    assert build_premier_ministre(
        "LECORNU II", "2025-10-13", None, [profil], warnings=warnings
    ) is None
    assert build_premier_ministre(
        "ATTAL", "2024-01-10", "2024-09-05", [profil], warnings=warnings
    ) is None
    assert warnings == []

    membres = build_gouvernement_roster("LECORNU II", "2025-10-13", None, [profil])
    assert all(m["portefeuille"] != "Premier ministre" for m in membres)


# ---------------------------------------------------------------------------
# Le libellé d'organe du chef du gouvernement s'accorde en genre (#658)
# ---------------------------------------------------------------------------

def test_real_pivot_elisabeth_borne_premiere_ministre_de_son_gouvernement():
    """Cas de #658 : le mandat porte `label = "Première ministre"` (libellé
    d'organe, accordé) et `fonction = "Premier ministre"` (qualité, jamais
    accordée). L'égalité stricte sur le label rendait `null` alors que la
    personne figurait dans les `membres[]` de sa propre fiche."""
    borne = _load_pivot_fixture("elisabeth-borne")

    mandat_pm = [
        m for m in borne["mandats"]
        if m.get("label") == "Première ministre"
    ]
    assert len(mandat_pm) == 1, "la fixture doit porter le libellé au féminin"
    assert mandat_pm[0]["fonction"] == "Premier ministre", (
        "la qualité, elle, reste au masculin dans la source"
    )

    warnings = []
    pm = build_premier_ministre(
        "BORNE", "2022-05-17", "2024-01-09", [borne], warnings=warnings
    )
    assert pm is not None
    assert pm["nom"] == "Élisabeth Borne"
    assert pm["acteur_ref"] == "PA717161"
    assert pm["source_url"]
    assert warnings == []


def test_real_pivot_elisabeth_borne_pas_pm_des_gouvernements_ou_elle_fut_ministre():
    """Le même profil appartient à cinq autres gouvernements comme ministre :
    aucun ne doit hériter d'un chef du gouvernement (#398, garde-fou du
    rattachement par mandat d'appartenance)."""
    borne = _load_pivot_fixture("elisabeth-borne")
    for libelle, debut, fin in [
        ("PHILIPPE", "2017-05-18", "2017-06-19"),
        ("PHILIPPE 2", "2017-06-22", "2020-07-06"),
        ("CASTEX", "2020-07-07", "2022-05-16"),
        ("BAYROU", "2024-12-24", "2025-09-09"),
        ("LECORNU", "2025-10-05", "2025-10-10"),
    ]:
        assert build_premier_ministre(libelle, debut, fin, [borne]) is None, libelle


def test_liste_des_libelles_de_chef_du_gouvernement_est_fermee():
    """Liste fermée relue et datée, jamais une règle de genre (#658).

    Les deux formes relevées le 2026-08-31 sur l'archive AMO30 (1 162 mandats
    `MINISTERE`) sont acceptées ; tout le reste est refusé, y compris les
    libellés réels qui **contiennent** « Première ministre » sans être celui
    du chef du gouvernement.
    """
    assert LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES == (
        "Premier ministre",
        "Première ministre",
    )
    assert LABELS_PORTEFEUILLE_PREMIER_MINISTRE == {
        "premier ministre",
        "première ministre",
    }

    for accepte in ("Premier ministre", "Première ministre", "  PREMIÈRE   MINISTRE "):
        assert _est_libelle_chef_du_gouvernement(accepte), accepte

    # Libellés réels de l'archive AMO30 : un maroquin « auprès de la Première
    # ministre » n'est pas le chef du gouvernement.
    for refuse in (
        "Ministère auprès de la Première ministre, chargé des relations avec le Parlement",
        "Secrétariat d’État auprès de la Première ministre, chargé de la mer",
        "Ministère de la justice",
        "Premier ministère",
        None,
        "",
    ):
        assert not _est_libelle_chef_du_gouvernement(refuse), refuse


def test_normalise_libelle_organe_reste_purement_typographique():
    """Casse et espaces — insécable compris, que la source AN pose dans
    certains libellés d'organe. Aucun rapprochement de genre : c'est la liste
    fermée qui accueille le féminin, pas la normalisation (#658)."""
    assert _normalise_libelle_organe("Première\u00a0ministre") == "première ministre"
    assert _normalise_libelle_organe("  Premier   Ministre ") == "premier ministre"
    assert _normalise_libelle_organe(None) == ""
    # Deux libellés distincts restent distincts.
    assert _normalise_libelle_organe("Première ministre") != _normalise_libelle_organe(
        "Premier ministre"
    )


def test_normalise_fonction_nintroduit_aucune_regle_de_genre():
    """Garde-fou de #658 : la correction porte sur le libellé d'organe, jamais
    sur la qualité. Le balayage de l'archive AMO30 a montré que `libQualite`
    ne porte aucune forme féminine — une ministre déléguée y porte « Ministre
    délégué » — donc rien ne justifie d'y rapprocher les genres, et le faire
    serait sémantique."""
    assert _normalise_fonction("Ministre déléguée") != _normalise_fonction(
        "Ministre délégué"
    )
    assert _qualite_portefeuille("Ministre déléguée") == QUALITE_INCONNUE
    assert _qualite_portefeuille("Ministre délégué") == QUALITE_MINISTERIELLE


def test_libelle_feminin_ne_desarme_pas_le_double_verrou_474():
    """Le second verrou de #474 s'applique identiquement au féminin.

    L'organe `PO791580` (« Première ministre ») porte, dans l'archive AMO30,
    un mandat de qualité « Premier ministre » (Élisabeth Borne) **et** un
    mandat de qualité « en mission » — une mission parlementaire auprès de
    Matignon. Le missionné ne doit ni devenir chef du gouvernement, ni
    *effacer* le vrai en créant une ambiguïté.
    """
    missionne = _pivot("nosdeputes:missionne", "Missionné", mandats=[
        _mandat_gouv("Gouvernement (BORNE)", "2022-05-17", "2024-01-09"),
        _mandat_portefeuille(
            "Première ministre", "2022-06-01", "2023-06-01", fonction="en mission",
        ),
    ])

    warnings = []
    assert build_premier_ministre(
        "BORNE", "2022-05-17", "2024-01-09", [missionne], warnings=warnings
    ) is None
    assert warnings == []

    borne = _load_pivot_fixture("elisabeth-borne")
    warnings = []
    pm = build_premier_ministre(
        "BORNE", "2022-05-17", "2024-01-09", [borne, missionne], warnings=warnings
    )
    assert pm is not None, "le vrai chef du gouvernement ne doit pas être effacé"
    assert pm["nom"] == "Élisabeth Borne"
    assert not any("Premiers ministres possibles" in w for w in warnings)


def test_libelle_feminin_avec_autre_qualite_ministerielle_declenche_le_warning():
    """Second verrou, au féminin : un libellé de chef du gouvernement porté
    par une qualité ministérielle connue mais autre est une incohérence de
    source — écartée avec un warning, jamais retenue en silence."""
    profils = [
        _pivot("nosdeputes:x", "X", mandats=[
            _mandat_gouv("Gouvernement (BORNE)", "2022-05-17", "2024-01-09"),
            _mandat_portefeuille(
                "Première ministre", "2022-05-17", "2024-01-09",
                fonction="Ministre délégué",
            ),
        ]),
    ]
    warnings = []
    assert build_premier_ministre(
        "BORNE", "2022-05-17", "2024-01-09", profils, warnings=warnings
    ) is None
    assert len(warnings) == 1
    assert "Première ministre" in warnings[0]
    assert "Ministre délégué" in warnings[0]
    assert "#474" in warnings[0]


def test_acteur_ref_absent_si_url_non_reconnue():
    """Fiche Sénat ou identité absente : `acteur_ref` reste None plutôt que
    d'être reconstruit."""
    profil = _pivot("nosdeputes:x", "X", mandats=[
        _mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
        _mandat_portefeuille(
                "Premier ministre", "2024-12-24", "2025-09-09",
                fonction="Premier ministre",
            ),
    ])
    profil["identite"] = {"source_url": "https://archive.nossenateurs.fr/stephane-mazars"}
    pm = build_premier_ministre("BAYROU", "2024-12-24", "2025-09-09", [profil])
    assert pm["acteur_ref"] is None


# ---------------------------------------------------------------------------
# load_profils_from_dir
# ---------------------------------------------------------------------------

def test_load_profils_from_dir(tmp_path):
    (tmp_path / "a.pivot.json").write_text(json.dumps(_pivot("nosdeputes:a", "A")), encoding="utf-8")
    (tmp_path / "b.pivot.json").write_text(json.dumps(_pivot("nosdeputes:b", "B")), encoding="utf-8")
    (tmp_path / "not-a-pivot.json").write_text(json.dumps({"foo": "bar"}), encoding="utf-8")

    profils = load_profils_from_dir(tmp_path)
    assert len(profils) == 2
    ids = {p["id"] for p in profils}
    assert ids == {"nosdeputes:a", "nosdeputes:b"}


def test_load_profils_from_dir_ignores_invalid_json(tmp_path):
    (tmp_path / "broken.pivot.json").write_text("{not valid json", encoding="utf-8")
    (tmp_path / "ok.pivot.json").write_text(json.dumps(_pivot("nosdeputes:ok", "OK")), encoding="utf-8")

    profils = load_profils_from_dir(tmp_path)
    assert len(profils) == 1
    assert profils[0]["id"] == "nosdeputes:ok"


# ---------------------------------------------------------------------------
# load_gouvernement_config
# ---------------------------------------------------------------------------

def test_load_gouvernement_config_found(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    config_path.write_text(json.dumps({
        "gouvernements": [
            {"gouvernement_id": "gouvernement:BAYROU", "nom": "Gouvernement Bayrou", "libelle_an": "BAYROU",
             "periode": {"debut": "2024-12-24", "fin": "2025-09-09"}, "fichier": "gouvernement-BAYROU.json"},
        ]
    }), encoding="utf-8")

    entry = load_gouvernement_config(config_path, "gouvernement:BAYROU")
    assert entry["libelle_an"] == "BAYROU"


def test_load_gouvernement_config_not_found(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    config_path.write_text(json.dumps({"gouvernements": []}), encoding="utf-8")

    try:
        load_gouvernement_config(config_path, "gouvernement:INCONNU")
        assert False, "ValueError attendue"
    except ValueError as exc:
        assert "gouvernement:INCONNU" in str(exc)


# ---------------------------------------------------------------------------
# Test de cohérence du fichier raw_data/gouvernements_reels.json
# (miroir de test_repository_groupes_reels_json_is_valid)
# ---------------------------------------------------------------------------

def test_repository_gouvernements_reels_json_is_valid():
    config_path = REPO_ROOT / "raw_data" / "gouvernements_reels.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    assert isinstance(payload.get("gouvernements"), list)
    assert payload["gouvernements"]

    seen_ids = set()
    for entry in payload["gouvernements"]:
        for key in ("gouvernement_id", "nom", "periode", "fichier", "libelle_an"):
            assert key in entry, f"clé manquante {key!r} dans {entry}"
        assert entry["gouvernement_id"].startswith("gouvernement:")
        assert entry["gouvernement_id"] not in seen_ids, f"doublon : {entry['gouvernement_id']}"
        seen_ids.add(entry["gouvernement_id"])
        assert "debut" in entry["periode"] and "fin" in entry["periode"]
        assert entry["periode"]["debut"] is not None


def test_repository_gouvernements_reels_json_covers_bayrou_and_lecornu():
    """Critère d'acceptation #209 : Bayrou et Lecornu doivent figurer dans
    l'échantillon disponible."""
    config_path = REPO_ROOT / "raw_data" / "gouvernements_reels.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    libelles = {entry["libelle_an"] for entry in payload["gouvernements"]}
    assert "BAYROU" in libelles
    assert any(libelle.startswith("LECORNU") for libelle in libelles)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_main_writes_roster(tmp_path):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "x.pivot.json").write_text(json.dumps(
        _pivot("nosdeputes:x", "X", mandats=[_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")])
    ), encoding="utf-8")

    config_path = tmp_path / "gouvernements_reels.json"
    config_path.write_text(json.dumps({
        "gouvernements": [
            {"gouvernement_id": "gouvernement:BAYROU", "nom": "Gouvernement Bayrou", "libelle_an": "BAYROU",
             "periode": {"debut": "2024-12-24", "fin": "2025-09-09"}, "fichier": "gouvernement-BAYROU.json"},
        ]
    }), encoding="utf-8")

    out_path = tmp_path / "out.json"
    rc = gouvernement_roster_main([
        "--config", str(config_path),
        "--gouvernement-id", "gouvernement:BAYROU",
        "--profiles-dir", str(profiles_dir),
        "--out", str(out_path),
    ])
    assert rc == 0
    roster = json.loads(out_path.read_text(encoding="utf-8"))
    assert roster["gouvernement_id"] == "gouvernement:BAYROU"
    assert len(roster["membres"]) == 1
    assert roster["membres"][0]["membre_id"] == "nosdeputes:x"


def test_cli_main_unknown_gouvernement_id_returns_error(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    config_path.write_text(json.dumps({"gouvernements": []}), encoding="utf-8")
    rc = gouvernement_roster_main([
        "--config", str(config_path),
        "--gouvernement-id", "gouvernement:INCONNU",
    ])
    assert rc == 1


# ---------------------------------------------------------------------------
# Mémoire : le plafond est dans le test (#635)
# ---------------------------------------------------------------------------
#
# `load_profils_from_dir` rangeait chaque profil pivot **entier** dans une
# liste, pour n'en lire que `id`, `nom`, `identite`, `mandats` et `sources`.
# Mesuré sur les 481 profils committés du 30/08/2026 (651,5 Mo), sous un
# plafond `RLIMIT_AS` de 2,0 Gio : `MemoryError` autour du **370e** profil
# (362e, 381e et 383e sur trois exécutions — le rang dépend de l'empreinte de
# départ du processus, pas de la lecture), ~2 004 Mio de croissance pour 500 à
# 525 Mo de JSON lus, facteur × 3,8 à × 4,2, donc 2,4 à 2,7 Gio pour le corpus
# entier. Les trois appelants
# (`generate_gouvernement_profiles.py`, `gouvernement_profile.py`, la CLI de ce
# module) ne pouvaient donc pas aller au bout sur une machine à 4 Gio libres.
#
# Le défaut est un défaut de **rétention**, pas de volume : un chargeur qui
# range les documents entiers les range à toutes les tailles. C'est pourquoi la
# propriété se vérifie sur des fixtures, la CI ne téléchargeant jamais le
# corpus (#473).

#: Profils du corpus-fixture de mesure. Assez nombreux pour que le coût
#: **transitoire** d'un seul document soit un ordre de grandeur sous le plafond.
NB_PROFILS_FIXTURE_MEMOIRE = 24

#: Poids visé, par profil, de chacun des trois blocs que le chargeur doit
#: relâcher (`amendements`, `votes`, `interventions`).
POIDS_BLOC_RELACHE = 800 * 1024

#: Plancher de vraisemblance du corpus-fixture. Rétrécir les fixtures
#: rétrécirait le plafond avec elles, et le test finirait par passer sur un
#: corpus si petit qu'il ne prouverait plus rien.
PLANCHER_POIDS_RELACHE = 40 * 1024 * 1024

#: Ce que le processus enfant exécute : il mesure **son propre** pic mémoire
#: (`ru_maxrss`, sans dépendance externe) de part et d'autre du chargement.
#: Un sous-processus est nécessaire : dans le processus pytest, `ru_maxrss`
#: porterait aussi le pic de tous les tests précédents.
_PILOTE_MEMOIRE = """\
import json, resource, sys
from pathlib import Path

depot, dossier = sys.argv[1], sys.argv[2]
sys.path.insert(0, str(Path(depot) / "src"))
import gouvernement_roster

depart = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
profils = gouvernement_roster.load_profils_from_dir(Path(dossier))
pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({
    "depart": depart, "pic": pic, "nb": len(profils),
    "mandats": sum(len(p.get("mandats") or []) for p in profils),
}))
"""


def _liste_lourde_memoire(octets_vises: int, gabarit: dict) -> list:
    """Une liste métier pesant environ `octets_vises` une fois sérialisée.

    Les entrées sont **petites**, et c'est le point : depuis #431 et #432 un
    `amendements[]` ou un `votes[]` publié est un mapping à deux clés, et c'est
    cette forme-là qui gonfle d'un facteur 3 à 10 en objets Python (× 4,2
    mesuré sur le corpus committé). Une fixture bâtie sur de longues chaînes ne
    gonflerait que d'environ × 1,5 et le garde-fou ne séparerait plus rien.
    """
    (cle_id, _), = [(k, v) for k, v in gabarit.items() if k.endswith("_id")]
    unite = len(json.dumps(gabarit, ensure_ascii=False)) + 1
    return [
        dict(gabarit, **{cle_id: f"{gabarit[cle_id]}{i:07d}"})
        for i in range(max(1, octets_vises // unite))
    ]


def _corpus_de_mesure_memoire(tmp_path: Path) -> tuple[Path, int]:
    """Écrit un corpus-fixture dont les blocs relâchés font l'essentiel du poids.

    Rend le dossier et le **poids sur disque des blocs que le chargeur doit
    relâcher** — c'est de ce poids, et non d'une observation, que le plafond
    est déduit.
    """
    dossier = tmp_path / "pivot_profiles"
    dossier.mkdir()

    amendements = _liste_lourde_memoire(
        POIDS_BLOC_RELACHE,
        {"amendement_id": "an:AMANR5L16PO0000B0000P0D0N", "role_signataire": "cosignataire"},
    )
    votes = _liste_lourde_memoire(
        POIDS_BLOC_RELACHE, {"scrutin_id": "an:16:", "position": "pour"},
    )
    interventions = _liste_lourde_memoire(
        POIDS_BLOC_RELACHE, {"intervention_id": "an:seance:", "type_detail": "question"},
    )
    poids_relache = NB_PROFILS_FIXTURE_MEMOIRE * sum(
        len(json.dumps(bloc, ensure_ascii=False))
        for bloc in (amendements, votes, interventions)
    )

    for i in range(NB_PROFILS_FIXTURE_MEMOIRE):
        profil = _pivot(
            f"depute-{i:03d}", f"Députée {i:03d}",
            mandats=[_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")],
        )
        profil["identite"] = {"source_url": "https://www.assemblee-nationale.fr/dyn/deputes/PA722190"}
        profil["sources"] = [{"type": "assemblee_nationale", "url": "https://data.assemblee-nationale.fr"}]
        profil["amendements"] = amendements
        profil["votes"] = votes
        profil["interventions"] = interventions
        profil["couverture"] = {"amendements": {"motif": None}}
        (dossier / f"depute-{i:03d}.pivot.json").write_text(
            json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    return dossier, poids_relache


def test_load_profils_from_dir_ne_retient_que_les_blocs_lus(tmp_path):
    """Le fond du défaut : un document lu n'est jamais un document gardé.

    Le pic mémoire dépend de la machine ; **ce que la projection retient** n'en
    dépend pas. C'est donc ici que l'invariant est verrouillé, et le test de
    plafond qui suit ne fait que confirmer qu'il a l'effet annoncé.
    """
    profil = _pivot("depute", "Députée", mandats=[_mandat_gouv("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09")])
    profil["identite"] = {"source_url": "https://www.assemblee-nationale.fr/dyn/deputes/PA722190"}
    profil["sources"] = [{"type": "assemblee_nationale", "url": "https://data.assemblee-nationale.fr"}]
    profil["amendements"] = [{"amendement_id": "an:X", "role_signataire": "auteur"}]
    profil["votes"] = [{"scrutin_id": "an:16:1", "position": "pour"}]
    profil["interventions"] = [{"intervention_id": "an:1"}]
    profil["couverture"] = {"amendements": {"motif": None}}
    (tmp_path / "depute.pivot.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    charges = load_profils_from_dir(tmp_path)
    assert len(charges) == 1
    assert sorted(charges[0]) == sorted(BLOCS_LUS_COMPOSITION)
    for bloc in ("amendements", "votes", "interventions", "couverture", "meta",
                 "textes_portes", "tags_thematiques", "chambre"):
        assert bloc not in charges[0], f"{bloc} n'est lu par aucun consommateur"
    # `mandats` est **parcouru** : jamais réduit à son cardinal.
    assert charges[0]["mandats"] == profil["mandats"]


def test_load_profils_from_dir_ignore_une_racine_non_objet(tmp_path):
    """Une racine JSON qui n'est pas un objet n'a aucun bloc à projeter — et la
    laisser passer faisait lever un `AttributeError` au premier `profil.get()`."""
    (tmp_path / "liste.pivot.json").write_text("[1, 2, 3]", encoding="utf-8")
    (tmp_path / "ok.pivot.json").write_text(
        json.dumps(_pivot("nosdeputes:ok", "OK")), encoding="utf-8")

    profils = load_profils_from_dir(tmp_path)
    assert [p["id"] for p in profils] == ["nosdeputes:ok"]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="`resource` est POSIX")
def test_le_pic_memoire_du_chargement_reste_sous_le_plafond_declare(tmp_path):
    """Le chargement ne doit pas croître de plus que le poids **sur disque** des
    blocs qu'il est censé relâcher.

    D'où vient le plafond
    ---------------------
    Il n'est pas relevé sur une exécution puis arrondi — ce serait un plafond
    qui suit la dérive qu'il doit signaler. C'est une **règle** : la croissance
    mémoire du chargement doit rester sous le poids en octets, sur disque, des
    blocs qu'il lit et ne doit pas garder (`amendements`, `votes`,
    `interventions`). Le raisonnement tient en une ligne : la désérialisation
    JSON ne **réduit** jamais — une liste de petits dictionnaires occupe 3 à 10
    fois le texte qui la décrit. Donc si le chargement croît de moins que ce
    texte, il ne peut pas le détenir.

    Ce que le test ne prouve pas
    ----------------------------
    Ni la vitesse, ni le pic absolu sur le corpus réel (mesuré à 133 et 141 Mio
    sur deux exécutions, pour les 481 profils committés, et nulle part en CI : `pivot_data` est hors du
    sparse-checkout de `tests.yml`, #473).
    """
    dossier, poids_relache = _corpus_de_mesure_memoire(tmp_path)
    assert poids_relache >= PLANCHER_POIDS_RELACHE, (
        f"corpus-fixture trop léger ({poids_relache / 1024**2:.0f} Mio de blocs "
        f"à relâcher) : sous ce plancher le plafond qu'il déduit ne prouve plus "
        f"rien. Regonfler les fixtures, jamais desserrer le plancher.")

    pilote = tmp_path / "pilote_memoire.py"
    pilote.write_text(_PILOTE_MEMOIRE, encoding="utf-8")
    acheve = subprocess.run(
        [sys.executable, str(pilote), str(REPO_ROOT), str(dossier)],
        capture_output=True, text=True, timeout=300,
    )
    assert acheve.returncode == 0, (
        f"le chargement n'a pas abouti (code {acheve.returncode}) — un 137 est "
        f"un OOM, le défaut même de #635 :\n{acheve.stderr[-2000:]}")
    mesure = json.loads(acheve.stdout.strip().splitlines()[-1])

    assert mesure["nb"] == NB_PROFILS_FIXTURE_MEMOIRE
    assert mesure["mandats"] == NB_PROFILS_FIXTURE_MEMOIRE, (
        "les mandats doivent survivre à la projection : ils sont parcourus")

    # `ru_maxrss` est en Kio sous Linux, en octets sous macOS.
    facteur = 1 if sys.platform == "darwin" else 1024
    croissance = (mesure["pic"] - mesure["depart"]) * facteur
    assert croissance < poids_relache, (
        f"le chargement a grossi de {croissance / 1024**2:.1f} Mio en lisant "
        f"{NB_PROFILS_FIXTURE_MEMOIRE} profils dont {poids_relache / 1024**2:.0f} Mio "
        f"de blocs qu'il ne doit pas garder. Au-dessus de ce plafond il en "
        f"retient une partie : c'est le défaut de #635, qui faisait atteindre "
        f"le plafond de 2,0 Gio autour du 370e des 481 profils committés.")
