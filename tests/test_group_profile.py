import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import group_profile  # noqa: E402  (#821)
from group_profile import (
    BLOCS_LUS_MEMBRE,
    ContributionAmendements,
    contribution_amendements,
    load_profil_from_file,
    _parse_date,
    _member_eligible_at,
    _derive_membre_entry,
    _appartenance_couvre,
    _deriver_date_reference,
    _stamper_presences,
    appartenances_depuis_roster,
    _build_vote_index,
    _compute_cohesion_votes,
    aggregate_tags_thematiques,
    _intervals_overlap,
    MANDATS_AGREGES_CATEGORIES,
    _aggregate_mandats,
    _aggregate_amendements,
    compute_ecarts_cohesion_internes,
    build_groupe_profile,
    _is_pivot_v1,
    generate_groupe_profile_from_roster,
    main as group_profile_main,
)
from schema_groupe import ETAT_ROSTER_DANS_LE_PERIMETRE, validate_profil_groupe
from scrutins_index import ScrutinsIndex, cle_scrutin

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _pivot(
    id_: str = "nosdeputes:jean-dupont",
    nom: str = "Jean Dupont",
    groupe: str = "Socialistes et apparentés",
    mandats: list = None,
    votes: list = None,
    tags: list = None,
    interventions: list = None,
    amendements: list = None,
) -> dict:
    """Construit un profil pivot v1 minimal pour les tests."""
    return {
        "schema_version": "1",
        "id": id_,
        "nom": nom,
        "chambre": "AN",
        "parti": None,
        "groupe": groupe,
        "sources": [
            {"type": "nosdeputes", "url": f"https://www.nosdeputes.fr/{id_.split(':')[1]}", "synchro_le": "2026-07-29T10:00:00+0000"}
        ],
        "mandats": mandats if mandats is not None else [
            {
                "categorie": "mandat_electif",
                "label": "Mandat parlementaire",
                "fonction": "mandat",
                "debut": "2022-06-22",
                "fin": None,
                "actif": True,
            }
        ],
        "votes": votes if votes is not None else [],
        "textes_portes": [],
        "interventions": interventions if interventions is not None else [],
        "amendements": amendements if amendements is not None else [],
        "tags_thematiques": tags if tags is not None else [],
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-07-29T10:00:00+0000",
            "licence_donnees": "ODbL",
            "warnings": [],
        },
    }


# Depuis #432, un vote de profil n'est plus qu'un mapping `{scrutin_id, position}` :
# le méta du scrutin (date, texte, sort) vit une seule fois dans l'index partagé.
# Un profil ne se lit donc plus seul pour ses votes, et les tests de cohésion
# doivent fournir l'index — c'est le couplage assumé de cette normalisation, et
# il vaut mieux qu'il soit visible ici que contourné par une fixture magique.
#
# `_vote()` enregistre le scrutin qu'il fabrique dans `_SCRUTINS`, remis à zéro
# entre deux tests : sans cela, deux tests utilisant le même numéro à des dates
# différentes se marcheraient dessus.
_SCRUTINS: dict[str, dict] = {}


@pytest.fixture(autouse=True)
def _reset_scrutins():
    _SCRUTINS.clear()
    yield
    _SCRUTINS.clear()


def _index() -> ScrutinsIndex:
    """Index partagé cohérent avec les votes fabriqués par ce test."""
    return ScrutinsIndex(dict(_SCRUTINS))


def _vote(
    numero: str, position: str, date: str = "2024-01-15", texte: str = "PLF",
    sort: str = "adopté", legislature: str = "16",
) -> dict:
    scrutin_id = cle_scrutin(legislature, numero)
    _SCRUTINS[scrutin_id] = {
        "id": scrutin_id,
        "legislature": legislature,
        "legislature_provenance": "collectee",
        "numero_scrutin": str(numero),
        "date": date,
        "texte": texte,
        "sort": sort,
        "type_scrutin": None,
        "type_vote": "vote_texte",
        "texte_lie_id": None,
        "source_url": None,
    }
    return {"scrutin_id": scrutin_id, "position": position}


def _mandat_electif(debut: str, fin: str = None, actif: bool = None) -> dict:
    return {
        "categorie": "mandat_electif",
        "label": "Mandat",
        "fonction": "mandat",
        "debut": debut,
        "fin": fin,
        "actif": actif if actif is not None else (fin is None),
    }


def _mandat_categoriel(
    categorie: str = "commission",
    label: str = "Commission des affaires étrangères",
    fonction: str = "membre",
    debut: str = "2022-06-22",
    fin: str = None,
    actif: bool = None,
) -> dict:
    return {
        "categorie": categorie,
        "label": label,
        "fonction": fonction,
        "debut": debut,
        "fin": fin,
        "actif": actif if actif is not None else (fin is None),
    }


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

def test_parse_date_valid():
    d = _parse_date("2022-06-22")
    from datetime import date
    assert d == date(2022, 6, 22)


def test_parse_date_with_time():
    d = _parse_date("2022-06-22T14:30:00")
    from datetime import date
    assert d == date(2022, 6, 22)


def test_parse_date_none_returns_none():
    assert _parse_date(None) is None


def test_parse_date_empty_string_returns_none():
    assert _parse_date("") is None


def test_parse_date_invalid_returns_none():
    assert _parse_date("not-a-date") is None


# ---------------------------------------------------------------------------
# _member_eligible_at
# ---------------------------------------------------------------------------

def test_eligible_active_mandat_no_end():
    mandats = [_mandat_electif("2022-06-22")]
    assert _member_eligible_at(mandats, "2024-01-15") is True


def test_eligible_within_closed_mandat():
    mandats = [_mandat_electif("2017-06-21", "2022-06-21")]
    assert _member_eligible_at(mandats, "2019-06-01") is True


def test_not_eligible_before_mandat():
    mandats = [_mandat_electif("2022-06-22")]
    assert _member_eligible_at(mandats, "2020-01-01") is False


def test_not_eligible_after_closed_mandat():
    mandats = [_mandat_electif("2017-06-21", "2022-06-21")]
    assert _member_eligible_at(mandats, "2023-01-01") is False


def test_eligible_no_date_returns_true():
    mandats = [_mandat_electif("2022-06-22")]
    assert _member_eligible_at(mandats, None) is True


def test_eligible_no_mandats_returns_true():
    # Pas d'info = conservateur → éligible
    assert _member_eligible_at([], "2024-01-15") is True


def test_eligible_multiple_mandats_second_matches():
    mandats = [
        _mandat_electif("2017-06-21", "2022-06-21"),
        _mandat_electif("2022-06-22"),
    ]
    assert _member_eligible_at(mandats, "2023-01-01") is True


def test_not_eligible_between_two_mandats():
    mandats = [
        _mandat_electif("2012-06-01", "2017-06-20"),
        _mandat_electif("2022-06-22"),
    ]
    # Date dans la fenêtre entre les deux mandats
    assert _member_eligible_at(mandats, "2018-01-01") is False


def test_eligible_ignores_non_electif_mandats():
    mandats = [
        {"categorie": "commission", "debut": "2022-07-01", "fin": None, "actif": True},
    ]
    # Pas de mandat_electif → conservateur
    assert _member_eligible_at(mandats, "2023-01-01") is True


# ---------------------------------------------------------------------------
# _derive_membre_entry
# ---------------------------------------------------------------------------

def test_derive_membre_id_nom():
    p = _pivot("nosdeputes:jean-dupont", "Jean Dupont")
    m = _derive_membre_entry(p)
    assert m["membre_id"] == "nosdeputes:jean-dupont"
    assert m["nom"] == "Jean Dupont"


def test_derive_membre_dates_lues_sur_le_mandat_de_groupe():
    """Les dates viennent du mandat GP de la législature, pas du profil (#653)."""
    p = _pivot(mandats=[_mandat_electif("2022-06-22")])
    m = _derive_membre_entry(p, "AN", {"debut": "2022-06-29", "fin": "2024-06-09"})
    assert m["debut_dans_groupe"] == "2022-06-29"
    assert m["fin_dans_groupe"] == "2024-06-09"
    # La présence n'est pas posée ici : elle dépend de la date de référence,
    # qui se dérive des dates de TOUS les membres (#653).
    assert "present_a_la_date_de_reference" not in m


def _membres_stampes(profils, date_reference, appartenance=None):
    """`membres[]` comme `build_groupe_profile` les produit (#653) : dérivés puis
    stampés à la date de référence. Sans `appartenance`, tous les membres sont
    présents à cette date — le cas courant d'un test d'agrégat, qui porte sur les
    mandats et non sur l'appartenance."""
    app = appartenance or {"debut": "2022-06-29", "fin": None}
    membres = [_derive_membre_entry(p, "AN", app) for p in profils]
    _stamper_presences(membres, date_reference)
    return membres


def test_appartenance_couvre_la_date_de_reference():
    """Bornes inclusives, et une appartenance non établie ne couvre rien."""
    ferme = {"debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09"}
    assert _appartenance_couvre(ferme, "2024-06-09") is True   # borne haute incluse
    assert _appartenance_couvre(ferme, "2022-06-29") is True   # borne basse incluse
    assert _appartenance_couvre(ferme, "2024-06-10") is False
    assert _appartenance_couvre(ferme, "2022-06-28") is False
    ouvert = {"debut_dans_groupe": "2024-07-19", "fin_dans_groupe": None}
    assert _appartenance_couvre(ouvert, "2026-08-31") is True
    # Appartenance non établie : jamais « présent par défaut » (§2 règle 5).
    assert _appartenance_couvre({"debut_dans_groupe": None, "fin_dans_groupe": None},
                                "2024-06-09") is False


def test_date_reference_est_la_cloture_quand_tout_est_referme():
    membres = [
        {"debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09"},
        {"debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2023-10-18"},
    ]
    assert _deriver_date_reference(membres, "2026-08-31T10:00:00+0000") == {
        "date": "2024-06-09", "origine": "derniere_appartenance_close",
    }


def test_date_reference_est_la_generation_si_une_appartenance_reste_ouverte():
    membres = [
        {"debut_dans_groupe": "2024-07-19", "fin_dans_groupe": None},
        {"debut_dans_groupe": "2024-07-19", "fin_dans_groupe": "2025-01-01"},
    ]
    assert _deriver_date_reference(membres, "2026-08-31T10:00:00+0000") == {
        "date": "2026-08-31", "origine": "generation",
    }


def test_derive_membre_ignore_le_mandat_electif_meme_ancien():
    """Le cas Vincent Rolland : député depuis 2002, membre du groupe LR de la
    XVIe depuis le 2022-06-29. C'est la régression de #647 que ce test ferme —
    le premier mandat électif ne doit plus jamais servir de date d'entrée."""
    p = _pivot(mandats=[
        _mandat_electif("2002-06-19", "2007-06-19", actif=False),
        _mandat_electif("2017-06-18", "2022-06-21", actif=False),
        _mandat_electif("2022-06-19", "2024-06-09", actif=False),
        _mandat_electif("2024-07-07"),
    ])
    m = _derive_membre_entry(p, "AN", {"debut": "2022-06-29", "fin": "2024-06-09"})
    assert m["debut_dans_groupe"] == "2022-06-29"


def test_derive_membre_sans_appartenance_ne_date_rien():
    """Aucune appartenance identifiable → `null`, jamais un repli sur les
    mandats électifs (AGENTS.md §2 règle 5)."""
    p = _pivot(mandats=[_mandat_electif("2022-06-22")])
    m = _derive_membre_entry(p)
    assert m["debut_dans_groupe"] is None
    assert m["fin_dans_groupe"] is None


def test_derive_membre_no_mandats():
    p = _pivot(mandats=[])
    m = _derive_membre_entry(p)
    assert m["debut_dans_groupe"] is None
    assert m["fin_dans_groupe"] is None


def test_appartenances_depuis_roster_renomme_et_ecarte_les_sans_slug():
    table = appartenances_depuis_roster([
        {"slug": "alice", "mandat_debut": "2022-06-29", "mandat_fin": "2024-06-09"},
        {"slug": None, "nom": "Sans slug", "mandat_debut": "2022-06-29", "mandat_fin": None},
        {"slug": "bob", "mandat_debut": "2023-01-30", "mandat_fin": None},
    ])
    assert table == {
        "alice": {"debut": "2022-06-29", "fin": "2024-06-09", "periodes": None},
        "bob": {"debut": "2023-01-30", "fin": None, "periodes": None},
    }


# ---------------------------------------------------------------------------
# _build_vote_index
# ---------------------------------------------------------------------------

def test_build_vote_index_basic():
    """La clé est `scrutin_id` depuis #432, plus `numero_scrutin` : le numéro
    seul faisait écraser le scrutin n° 1000 de la 16e par celui de la 17e."""
    p = _pivot(votes=[_vote("100", "pour"), _vote("200", "contre")])
    idx = _build_vote_index(p)
    assert "an:16:100" in idx
    assert "an:16:200" in idx
    assert idx["an:16:100"]["position"] == "pour"


def test_build_vote_index_ignore_un_vote_sans_identifiant():
    """Un vote non résolu n'est rattachable à aucun scrutin : il ne peut pas
    entrer dans un index par scrutin."""
    p = _pivot(votes=[{"scrutin_id": None, "position": "pour",
                       "scrutin_non_resolu": {"numero_scrutin": "123"}}])
    assert _build_vote_index(p) == {}


def test_build_vote_index_empty():
    p = _pivot(votes=[])
    assert _build_vote_index(p) == {}


# ---------------------------------------------------------------------------
# _compute_cohesion_votes
# ---------------------------------------------------------------------------

def _make_groupe_profils():
    """Deux membres, un scrutin commun."""
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[_vote("42", "pour")])
    return [p1, p2]


def test_cohesion_unanimite():
    profils = _make_groupe_profils()
    cohesion = _compute_cohesion_votes(profils, scrutins_index=_index())
    assert len(cohesion) == 1
    r = cohesion[0]
    assert r["scrutin_id"] == "an:16:42"
    assert r["position_majoritaire"] == "pour"
    assert r["pour"] == 2
    assert r["contre"] == 0
    assert r["absents"] == 0
    assert r["taux_coherence"] == 1.0
    assert r["taux_participation"] == 1.0


def test_cohesion_partielle():
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[_vote("42", "contre")])
    p3 = _pivot("nosdeputes:charlie", votes=[_vote("42", "pour")])
    cohesion = _compute_cohesion_votes([p1, p2, p3], scrutins_index=_index())
    r = cohesion[0]
    assert r["position_majoritaire"] == "pour"
    assert r["pour"] == 2
    assert r["contre"] == 1
    # 2 alignés sur 3 éligibles
    assert abs(r["taux_coherence"] - 2 / 3) < 1e-4


def test_cohesion_absent_implicite():
    """Un membre n'a aucun vote pour le scrutin → absent."""
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[])  # n'a pas voté
    cohesion = _compute_cohesion_votes([p1, p2], scrutins_index=_index())
    r = cohesion[0]
    assert r["absents"] == 1
    assert r["membres_eligibles"] == 2
    assert abs(r["taux_participation"] - 0.5) < 1e-4


def test_cohesion_quorum_atteint():
    profils = _make_groupe_profils()
    cohesion = _compute_cohesion_votes(profils, seuil_quorum=0.5, scrutins_index=_index())
    assert cohesion[0]["quorum_atteint"] is True


def test_cohesion_quorum_non_atteint():
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[])
    # 50 % de participation, seuil à 0.6 → quorum non atteint
    cohesion = _compute_cohesion_votes([p1, p2], seuil_quorum=0.6, scrutins_index=_index())
    assert cohesion[0]["quorum_atteint"] is False


def test_cohesion_trie_par_date_desc():
    p1 = _pivot("nosdeputes:alice", votes=[
        _vote("10", "pour", date="2023-01-10"),
        _vote("20", "contre", date="2024-06-01"),
    ])
    index = _index()
    cohesion = _compute_cohesion_votes([p1], scrutins_index=index)
    # La date n'est plus dans l'entrée de cohésion (#432) : elle se relit dans
    # l'index. L'ORDRE publié, lui, reste chronologique décroissant.
    dates = [index.get(r["scrutin_id"])["date"] for r in cohesion]
    assert dates == sorted(dates, reverse=True)


def test_cohesion_membre_non_eligible_exclu():
    """Un membre dont le mandat est terminé avant le vote ne compte pas."""
    p1 = _pivot(
        "nosdeputes:alice",
        mandats=[_mandat_electif("2022-06-22")],
        votes=[_vote("42", "pour", date="2024-01-15")],
    )
    p2 = _pivot(
        "nosdeputes:ancien",
        mandats=[_mandat_electif("2017-06-21", "2022-06-21", actif=False)],
        votes=[_vote("42", "contre", date="2024-01-15")],
    )
    cohesion = _compute_cohesion_votes([p1, p2], scrutins_index=_index())
    r = cohesion[0]
    # bob (mandat terminé en 2022) ne devrait pas être éligible au scrutin de 2024
    assert r["membres_eligibles"] == 1
    assert r["pour"] == 1
    assert r["contre"] == 0


def test_cohesion_vide_si_aucun_scrutin():
    p1 = _pivot(votes=[])
    p2 = _pivot(votes=[])
    assert _compute_cohesion_votes([p1, p2], scrutins_index=_index()) == []


def test_cohesion_plusieurs_scrutins():
    p1 = _pivot("nosdeputes:alice", votes=[
        _vote("10", "pour"),
        _vote("11", "contre"),
    ])
    cohesion = _compute_cohesion_votes([p1], scrutins_index=_index())
    nums = {r["scrutin_id"] for r in cohesion}
    assert nums == {"an:16:10", "an:16:11"}


def test_cohesion_position_majoritaire_none_si_aucun_vote_exprime():
    """Scrutin où tous les membres ont non_votant → pas de position majoritaire."""
    p1 = _pivot(votes=[_vote("99", "non_votant", date="2024-01-01")])
    cohesion = _compute_cohesion_votes([p1], scrutins_index=_index())
    assert cohesion[0]["position_majoritaire"] is None


def test_cohesion_taux_coherence_hors_absents():
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[_vote("42", "pour")])
    p3 = _pivot("nosdeputes:charlie", votes=[])  # absent
    cohesion = _compute_cohesion_votes([p1, p2, p3], scrutins_index=_index())
    r = cohesion[0]
    assert r["taux_coherence_hors_absents"] == 1.0  # 2/2 parmi ceux qui ont voté
    assert abs(r["taux_coherence"] - 2 / 3) < 1e-4  # 2/3 globalement


# ---------------------------------------------------------------------------
# aggregate_tags_thematiques
# ---------------------------------------------------------------------------

def test_tags_agrege_compte_membres():
    p1 = _pivot(tags=["budget", "fiscalité"])
    p2 = _pivot(tags=["budget", "santé"])
    tags = aggregate_tags_thematiques([p1, p2]).tags
    budget_entry = next(t for t in tags if t["tag"] == "budget")
    assert budget_entry["nb_membres_porteurs"] == 2
    assert budget_entry["poids_relatif"] == 1.0


def test_tags_agrege_deduplication_par_membre():
    """Un tag répété dans le profil d'un membre ne compte qu'une fois."""
    p1 = _pivot(tags=["budget", "budget", "budget"])
    tags = aggregate_tags_thematiques([p1]).tags
    budget_entry = next(t for t in tags if t["tag"] == "budget")
    assert budget_entry["nb_membres_porteurs"] == 1


def test_tags_trie_par_nombre_membres_desc():
    p1 = _pivot(tags=["budget", "santé", "défense"])
    p2 = _pivot(tags=["budget", "santé"])
    p3 = _pivot(tags=["budget"])
    tags = aggregate_tags_thematiques([p1, p2, p3]).tags
    counts = [t["nb_membres_porteurs"] for t in tags]
    assert counts == sorted(counts, reverse=True)


def test_tags_fallback_sur_mots_cles_interventions():
    """Si tags_thematiques est vide, on utilise les mots-clés des interventions."""
    interventions = [{"mots_cles": ["immigration", "social"], "date": "2024-01-01"}]
    p1 = _pivot(tags=[], interventions=interventions)
    _agregat = aggregate_tags_thematiques([p1])
    tags, source = _agregat.tags, _agregat.source
    tag_names = {t["tag"] for t in tags}
    assert "immigration" in tag_names
    assert source == "mots_cles_interventions"


def test_tags_source_tags_thematiques():
    p1 = _pivot(tags=["budget"])
    source = aggregate_tags_thematiques([p1]).source
    assert source == "tags_thematiques"


def test_tags_source_mixed():
    p1 = _pivot(tags=["budget"])
    p2 = _pivot(tags=[], interventions=[{"mots_cles": ["santé"], "date": "2024-01-01"}])
    source = aggregate_tags_thematiques([p1, p2]).source
    assert source == "mixed"


def test_tags_vide_si_aucun_tag():
    p1 = _pivot(tags=[], interventions=[])
    _agregat = aggregate_tags_thematiques([p1])
    tags, source = _agregat.tags, _agregat.source
    assert tags == []
    assert source is None


def test_tags_poids_relatif():
    p1 = _pivot(tags=["budget"])
    p2 = _pivot(tags=[])
    tags = aggregate_tags_thematiques([p1, p2]).tags
    budget_entry = next(t for t in tags if t["tag"] == "budget")
    assert budget_entry["poids_relatif"] == 0.5  # 1 membre sur 2


# ---------------------------------------------------------------------------
# _is_pivot_v1
# ---------------------------------------------------------------------------

def test_is_pivot_v1_true():
    p = _pivot()
    assert _is_pivot_v1(p) is True


def test_is_pivot_v1_false_raw_format():
    raw = {"slug": "jean-dupont", "chambre": "deputes"}
    assert _is_pivot_v1(raw) is False


def test_is_pivot_v1_false_missing_id():
    p = {"schema_version": "1", "nom": "X"}
    assert _is_pivot_v1(p) is False


# ---------------------------------------------------------------------------
# build_groupe_profile
# ---------------------------------------------------------------------------

def test_build_groupe_profile_valide():
    profils = [
        _pivot("nosdeputes:alice", votes=[_vote("42", "pour")]),
        _pivot("nosdeputes:bob", votes=[_vote("42", "pour")]),
    ]
    g = build_groupe_profile(
        groupe_id="AN:SOC",
        groupe_sigle="SOC",
        groupe_nom="Socialistes et apparentés",
        chambre="AN",
        legislature="16",
        profils=profils,
        licence_donnees="ODbL",
    )
    errors = validate_profil_groupe(g)
    assert errors == [], f"Erreurs de schéma inattendues : {errors}"


def test_build_groupe_profile_membres():
    profils = [
        _pivot("nosdeputes:alice", "Alice"),
        _pivot("nosdeputes:bob", "Bob"),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert len(g["membres"]) == 2
    ids = {m["membre_id"] for m in g["membres"]}
    assert ids == {"nosdeputes:alice", "nosdeputes:bob"}


def test_build_groupe_profile_effectif_a_la_date_de_reference_legislature_ouverte():
    """Une appartenance encore ouverte → la date de référence est celle de la
    génération, et l'effectif compte qui appartient au groupe ce jour-là."""
    profils = [
        _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22")]),
        _pivot("nosdeputes:ancien", mandats=[_mandat_electif("2017-06-21", "2022-06-21", actif=False)]),
    ]
    g = build_groupe_profile(
        "AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index(),
        appartenances={
            "nosdeputes:alice": {"debut": "2022-06-29", "fin": None},
            "nosdeputes:ancien": {"debut": "2022-06-29", "fin": "2023-10-18"},
        },
    )
    assert g["date_reference"]["origine"] == "generation"
    assert g["effectif"]["a_la_date_de_reference"] == 1  # seule alice appartient encore
    assert g["membres"][0]["present_a_la_date_de_reference"] is True
    assert g["membres"][1]["present_a_la_date_de_reference"] is False


def test_build_groupe_profile_legislature_close_compte_a_la_cloture():
    """Le cœur de #653 : sur une législature close, la date de référence est la
    clôture, et l'effectif y compte les membres du groupe CE JOUR-LÀ — pas ceux
    qui sont encore député⋅es aujourd'hui, pas zéro."""
    profils = [
        _pivot("nosdeputes:alice", mandats=[_mandat_electif("2024-07-07")]),
        _pivot("nosdeputes:parti", mandats=[_mandat_electif("2022-06-19", "2023-10-18", actif=False)]),
    ]
    g = build_groupe_profile(
        "AN:LR", "LR", "Les Républicains", "AN", "16", profils, scrutins_index=_index(),
        appartenances={
            "nosdeputes:alice": {"debut": "2022-06-29", "fin": "2024-06-09"},
            "nosdeputes:parti": {"debut": "2022-06-29", "fin": "2023-10-18"},
        },
    )
    assert g["date_reference"] == {"date": "2024-06-09", "origine": "derniere_appartenance_close"}
    assert g["effectif"]["a_la_date_de_reference"] == 1
    assert len(g["membres"]) == 2
    assert validate_profil_groupe(g) == []
    assert any(w.startswith("date_reference : tous les comptes") for w in g["meta"]["warnings"])


def test_build_groupe_profile_sans_appartenances_publie_null_et_le_dit():
    profils = [_pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22")])]
    g = build_groupe_profile(
        "AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index()
    )
    assert g["membres"][0]["debut_dans_groupe"] is None
    assert g["periode"]["debut"] is None
    assert any(
        w.startswith("appartenance_au_groupe : aucun roster fourni")
        for w in g["meta"]["warnings"]
    )


def test_build_groupe_profile_membre_hors_roster_est_compte_et_nomme():
    profils = [
        _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22")]),
        _pivot("nosdeputes:bob", mandats=[_mandat_electif("2022-06-22")]),
    ]
    g = build_groupe_profile(
        "AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index(),
        appartenances={"nosdeputes:alice": {"debut": "2022-06-29", "fin": None}},
    )
    assert len(g["membres"]) == 2  # aucune entrée retirée
    warning = next(
        w for w in g["meta"]["warnings"] if w.startswith("appartenance_au_groupe : 1 membre")
    )
    assert "nosdeputes:bob" in warning


def test_build_groupe_profile_periode():
    profils = [_pivot(mandats=[_mandat_electif("2022-06-22")])]
    g = build_groupe_profile(
        "AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index(),
        appartenances={"nosdeputes:jean-dupont": {"debut": "2022-06-29", "fin": None}},
    )
    assert g["periode"]["debut"] == "2022-06-29"
    assert g["periode"]["fin"] is None
    # `periode.actif` décrit la PÉRIODE, pas un compte : il n'est pas rapporté
    # à la date de référence (#653).
    assert g["periode"]["actif"] is True


def test_build_groupe_profile_cohesion_votes():
    profils = [
        _pivot("nosdeputes:alice", votes=[_vote("42", "pour")]),
        _pivot("nosdeputes:bob", votes=[_vote("42", "contre")]),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert len(g["cohesion_votes"]) == 1
    assert g["cohesion_votes"][0]["scrutin_id"] == "an:16:42"


def test_build_groupe_profile_profils_sources_dans_meta():
    profils = [
        _pivot("nosdeputes:alice"),
        _pivot("nosdeputes:bob"),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert "nosdeputes:alice" in g["meta"]["profils_sources"]
    assert "nosdeputes:bob" in g["meta"]["profils_sources"]


def test_build_groupe_profile_seuil_quorum_dans_meta():
    profils = [_pivot()]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, seuil_quorum=0.7, scrutins_index=_index())
    assert g["meta"]["seuil_quorum"] == 0.7


def _interv(theme: str, legislature: str = "16", n: int = 1) -> dict:
    """Une intervention telle que le corpus en porte : l'id dit la législature."""
    return {
        "intervention_id": f"syceron_CRSANR5L{legislature}S2023O1N245_{n:06d}",
        "theme_officiel": theme,
        "date": "2024-01-01",
    }


def test_build_groupe_profile_tags():
    """#825 — une fiche lit les interventions de SA législature, pas `tags_thematiques`.

    La fixture d'origine posait `tags_thematiques` à la main et n'avait aucune
    intervention : elle décrivait le monde tel que le code l'imaginait, et ne
    pouvait donc pas voir que la fiche comptait la carrière entière.
    """
    profils = [
        _pivot(interventions=[_interv("budget")]),
        _pivot(interventions=[_interv("budget"), _interv("santé", n=2)]),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    tag_names = {t["tag"] for t in g["tags_thematiques_agreges"]}
    assert "budget" in tag_names
    assert "santé" in tag_names


def test_tags_agreges_ecartent_les_autres_legislatures():
    """L'empreinte d'une fiche de la XVIe ignore ce qui a été dit sous la XVe."""
    profils = [
        _pivot(interventions=[
            _interv("budget", legislature="16"),
            _interv("retraites", legislature="15", n=2),
            _interv("écologie", legislature="17", n=3),
        ]),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert {t["tag"] for t in g["tags_thematiques_agreges"]} == {"budget"}
    assert any(
        "tags_thematiques_agreges : 2 intervention(s) tenue(s) sous une autre" in w
        for w in g["meta"]["warnings"]
    )


def test_tags_agreges_conservent_une_intervention_sans_legislature():
    """Une ignorance n'est pas un fait : l'entrée est retenue, et le compte déclaré."""
    profils = [
        _pivot(interventions=[
            _interv("budget", legislature="16"),
            {"intervention_id": None, "theme_officiel": "santé", "date": "2024-01-01"},
        ]),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert {t["tag"] for t in g["tags_thematiques_agreges"]} == {"budget", "santé"}
    assert any(
        "1 intervention(s) dont l'identifiant ne porte pas de législature sont CONSERVÉES" in w
        for w in g["meta"]["warnings"]
    )


def test_tags_agreges_sans_legislature_gardent_la_carriere():
    """Une fiche de parti ne nomme aucune législature : rien n'est filtré (#825)."""
    profils = [
        _pivot(interventions=[
            _interv("budget", legislature="16"),
            _interv("retraites", legislature="15", n=2),
        ]),
    ]
    agregat = aggregate_tags_thematiques(profils)
    assert {t["tag"] for t in agregat.tags} == {"budget", "retraites"}
    assert agregat.hors_periode == 0


def test_build_groupe_profile_sources_deduplication():
    """Les sources identiques entre profils ne doivent apparaître qu'une fois."""
    same_source = {
        "type": "nosdeputes",
        "url": "https://www.nosdeputes.fr/groupe/SOC",
        "synchro_le": "2026-07-29T10:00:00+0000",
    }
    profils = [
        {**_pivot("nosdeputes:alice"), "sources": [same_source]},
        {**_pivot("nosdeputes:bob"), "sources": [same_source]},
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    # La même source ne doit apparaître qu'une fois
    urls = [s["url"] for s in g["sources"]]
    assert urls.count(same_source["url"]) == 1


def test_build_groupe_profile_repli_mots_cles_survit_au_filtre():
    """#825 — le repli sur `mots_cles` n'est pas rouvert : il est DANS la fabrique.

    L'issue craignait que recalculer l'empreinte depuis les interventions
    « rouvre la question du repli documenté ». Elle ne se rouvre pas :
    `deriver_tags_thematiques` porte déjà `theme_officiel` puis `mots_cles`,
    et une fiche de groupe en hérite. Ce qui change est le nom de la source,
    plus le chemin.
    """
    profils = [
        _pivot(tags=[], interventions=[{
            "intervention_id": "syceron_CRSANR5L16S2023O1N245_000001",
            "mots_cles": ["santé"],
            "date": "2024-01-01",
        }]),
    ]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert {t["tag"] for t in g["tags_thematiques_agreges"]} == {"santé"}


def test_parti_profile_garde_le_warning_de_repli_mots_cles():
    """Sans législature, le repli d'origine et son avertissement tiennent."""
    profils = [
        _pivot(tags=[], interventions=[{"mots_cles": ["santé"], "date": "2024-01-01"}]),
    ]
    assert aggregate_tags_thematiques(profils).source == "mots_cles_interventions"


def test_build_groupe_profile_profils_vide():
    """Appel avec liste vide ne doit pas lever d'exception."""
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", [], scrutins_index=_index())
    assert g["membres"] == []
    assert g["cohesion_votes"] == []
    assert g["effectif"]["a_la_date_de_reference"] == 0


# ---------------------------------------------------------------------------
# _intervals_overlap
# ---------------------------------------------------------------------------

def test_intervals_overlap_true_when_overlapping():
    from datetime import date
    assert _intervals_overlap(date(2022, 1, 1), date(2022, 12, 31), date(2022, 6, 1), date(2023, 1, 1))


def test_intervals_overlap_false_when_disjoint():
    from datetime import date
    assert not _intervals_overlap(date(2022, 1, 1), date(2022, 6, 1), date(2023, 1, 1), date(2023, 12, 31))


def test_intervals_overlap_none_bounds_treated_as_unbounded():
    from datetime import date
    assert _intervals_overlap(None, None, date(2023, 1, 1), date(2023, 12, 31))
    assert _intervals_overlap(date(2022, 1, 1), None, date(2023, 1, 1), None)


def test_intervals_overlap_adjacent_boundaries_overlap():
    from datetime import date
    assert _intervals_overlap(date(2022, 1, 1), date(2022, 6, 1), date(2022, 6, 1), date(2022, 12, 31))


# ---------------------------------------------------------------------------
# _aggregate_mandats
# ---------------------------------------------------------------------------

def test_mandats_agreges_categories_perimetre():
    """Périmètre élargi par #382/#385 : les instances de travail collectives
    sont agrégées, les catégories structurelles ou individuelles ne le sont
    pas (voir le commentaire de MANDATS_AGREGES_CATEGORIES)."""
    assert set(MANDATS_AGREGES_CATEGORIES) == {
        "commission", "commission_enquete", "mission_information",
        "groupe_etudes", "delegation", "groupe_amitie", "extra_parlementaire",
    }


def test_mandats_agreges_categories_exclut_structurel_et_individuel():
    """Non-régression du périmètre : agréger `mandat_electif`/`groupe_politique`
    (identiques pour tous les membres) ou `fonction_gouvernementale`
    (individuelle) n'apprendrait rien au niveau groupe ; `autre` est un
    fourre-tout sans unité éditoriale (AGENTS.md §2.8)."""
    for categorie in ("mandat_electif", "groupe_politique", "fonction_gouvernementale", "autre"):
        assert categorie not in MANDATS_AGREGES_CATEGORIES


def test_mandats_agreges_compte_membres_par_categorie_label():
    p1 = _pivot(mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel()])
    p2 = _pivot(mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel()])
    membres = [_derive_membre_entry(p1), _derive_membre_entry(p2)]
    result = _aggregate_mandats([p1, p2], membres)
    assert len(result) == 1
    entry = result[0]
    assert entry["categorie"] == "commission"
    assert entry["label"] == "Commission des affaires étrangères"
    assert entry["nb_membres_cumul_historique"] == 2
    assert "nb_membres" not in entry  # #656 : plus de nombre unique ambigu


def test_mandats_agreges_exclut_categories_hors_perimetre():
    """mandat_electif, groupe_politique, fonction_gouvernementale, autre exclus (v1)."""
    p1 = _pivot(mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(categorie="groupe_politique", label="SOC"),
        _mandat_categoriel(categorie="fonction_gouvernementale", label="Ministre"),
        _mandat_categoriel(categorie="autre", label="Divers"),
    ])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    assert result == []


def test_mandats_agreges_inclut_groupe_amitie_et_extra_parlementaire():
    p1 = _pivot(mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(categorie="groupe_amitie", label="France-Japon"),
        _mandat_categoriel(categorie="extra_parlementaire", label="Conseil d'orientation"),
    ])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    categories = {r["categorie"] for r in result}
    assert categories == {"groupe_amitie", "extra_parlementaire"}


def test_mandats_agreges_exclut_mandat_hors_chevauchement_mandat_electif():
    """Mandat catégoriel dont la période ne chevauche aucun mandat électif : exclu."""
    p1 = _pivot(mandats=[
        _mandat_electif("2012-06-20", fin="2017-06-20", actif=False),
        _mandat_categoriel(debut="2022-06-22", fin=None, actif=True),
    ])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    assert result == []


def test_mandats_agreges_inclut_mandat_chevauchant_mandat_electif():
    p1 = _pivot(mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(debut="2023-01-01", fin=None, actif=True),
    ])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    assert len(result) == 1
    assert result[0]["nb_membres_cumul_historique"] == 1


def test_mandats_agreges_membre_sans_mandat_electif_est_eligible_par_defaut():
    """Approche conservatrice : pas de mandat électif renseigné → non exclu."""
    p1 = _pivot(mandats=[_mandat_categoriel(debut="2023-01-01", fin=None, actif=True)])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    assert len(result) == 1
    assert result[0]["nb_membres_cumul_historique"] == 1


def test_mandats_agreges_tie_break_doublon_priorite_actif():
    """Doublon (categorie, label) pour un même membre : priorité à actif=true."""
    p1 = _pivot(mandats=[
        _mandat_electif("2012-06-20"),
        _mandat_categoriel(debut="2012-06-20", fin="2017-06-19", actif=False, fonction="membre"),
        _mandat_categoriel(debut="2017-06-20", fin=None, actif=True, fonction="président"),
    ])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    assert len(result) == 1
    assert result[0]["nb_membres_cumul_historique"] == 1
    assert result[0]["membres"][0]["fonction"] == "président"


def test_mandats_agreges_tie_break_doublon_sans_actif_prend_fin_la_plus_recente():
    p1 = _pivot(mandats=[
        _mandat_electif("2007-06-20"),
        _mandat_categoriel(debut="2007-06-20", fin="2012-06-19", actif=False, fonction="membre"),
        _mandat_categoriel(debut="2012-06-20", fin="2017-06-19", actif=False, fonction="président"),
    ])
    membres = [_derive_membre_entry(p1)]
    result = _aggregate_mandats([p1], membres)
    assert result[0]["membres"][0]["fonction"] == "président"


def test_mandats_agreges_par_fonction_distribution():
    p1 = _pivot(mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="membre")])
    p2 = _pivot(mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="président")])
    membres = [_derive_membre_entry(p1), _derive_membre_entry(p2)]
    result = _aggregate_mandats([p1, p2], membres)
    assert result[0]["par_fonction"] == {"membre": 1, "président": 1}


def test_mandats_agreges_par_fonction_normalise_la_casse():
    """#379 : depuis #369 les mandats viennent de deux référentiels aux
    conventions typographiques différentes — NosDéputés écrit `"membre"`,
    l'Assemblée nationale `"Membre"`. Sans normalisation, le comptage éclatait
    le même rôle en deux entrées (mesuré en production : `'membre': 521` et
    `'Membre': 312`), donnant à lire deux rôles distincts."""
    p1 = _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="membre")])
    p2 = _pivot("nosdeputes:bob", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="Membre")])
    p3 = _pivot("nosdeputes:carol", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="  MEMBRE  ")])
    membres = [_derive_membre_entry(p) for p in (p1, p2, p3)]

    result = _aggregate_mandats([p1, p2, p3], membres)

    assert result[0]["par_fonction"] == {"membre": 3}


def test_mandats_agreges_par_fonction_preserve_les_variantes_genrees():
    """Le genre n'est PAS normalisé : `président`/`présidente` sont des
    libellés institutionnels réellement distincts, les fusionner effacerait
    une information portée par la source."""
    p1 = _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="président")])
    p2 = _pivot("nosdeputes:bob", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="présidente")])
    membres = [_derive_membre_entry(p) for p in (p1, p2)]

    result = _aggregate_mandats([p1, p2], membres)

    assert result[0]["par_fonction"] == {"président": 1, "présidente": 1}


def test_mandats_agreges_par_fonction_absente_reste_non_precise():
    """Une fonction non renseignée reste distincte de « simple membre » :
    donnée manquante ≠ valeur par défaut (AGENTS.md §2.5)."""
    p1 = _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction=None)])
    p2 = _pivot("nosdeputes:bob", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(fonction="   ")])
    membres = [_derive_membre_entry(p) for p in (p1, p2)]

    result = _aggregate_mandats([p1, p2], membres)

    assert result[0]["par_fonction"] == {"non_precise": 2}


def test_mandats_agreges_membres_siegeant_requiert_mandat_ouvert_et_appartenance():
    p1 = _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel(actif=True)])
    p2 = _pivot("nosdeputes:bob", mandats=[
        _mandat_electif("2012-06-20", fin="2017-06-19", actif=False),
        _mandat_categoriel(debut="2012-06-20", fin="2017-06-19", actif=False),
    ])
    # Depuis #653, « siéger » se juge À LA DATE DE RÉFÉRENCE, sur les deux
    # facteurs : alice appartient au groupe et son mandat couvre 2023-01-01,
    # bob a quitté le groupe en 2017 et son mandat était clos depuis.
    membres = [
        _derive_membre_entry(p1, "AN", {"debut": "2022-06-29", "fin": None}),
        _derive_membre_entry(p2, "AN", {"debut": "2012-06-26", "fin": "2017-06-19"}),
    ]
    _stamper_presences(membres, "2023-01-01")
    result = _aggregate_mandats([p1, p2], membres, "AN", "2023-01-01")
    assert result[0]["nb_membres_cumul_historique"] == 2
    assert result[0]["nb_membres_a_la_date_de_reference"] == 1


def test_mandats_agreges_effectif_reference_est_la_couverture_disponible():
    """#656 : le dénominateur est publié, pas pré-divisé.

    `effectif_reference` vaut `len(profils)` — la couverture disponible du
    groupe, jamais `meta.couverture_roster.roster_total`. Il remplace
    `poids_relatif`, qui valait `nb_membres / len(membres)` et ne disait pas
    de laquelle des deux grandeurs il était le poids. Publier le dénominateur
    permet de lire « 1 / 2 » plutôt qu'un pourcentage seul (AGENTS.md §2.7).
    """
    p1 = _pivot(mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel()])
    p2 = _pivot(mandats=[_mandat_electif("2022-06-22")])
    membres = [_derive_membre_entry(p1), _derive_membre_entry(p2)]
    result = _aggregate_mandats([p1, p2], membres)
    assert result[0]["effectif_reference"] == 2
    assert "poids_relatif" not in result[0]


def test_mandats_agreges_vide_si_profils_vide():
    assert _aggregate_mandats([], []) == []


def test_mandats_agreges_le_cumul_departage_a_egalite_de_membres_siegeant():
    """À nombre égal de membres siégeant (ici 0), le cumul départage, puis
    (categorie, label) — l'ordre historique de #361 est préservé."""
    p1 = _pivot(mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(categorie="commission", label="Commission A"),
    ])
    p2 = _pivot(mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(categorie="commission", label="Commission A"),
    ])
    p3 = _pivot(mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(categorie="commission", label="Commission B"),
    ])
    membres = [_derive_membre_entry(p) for p in (p1, p2, p3)]
    result = _aggregate_mandats([p1, p2, p3], membres)
    assert [(r["label"], r["nb_membres_cumul_historique"]) for r in result] == [
        ("Commission A", 2),
        ("Commission B", 1),
    ]


def test_mandats_agreges_trie_par_membres_siegeant_avant_le_cumul():
    """#656 : trier sur le cumul faisait remonter la commission traversée par
    beaucoup de monde au-dessus de celle où l'on siège vraiment.

    Mesuré sur `groupe-AN-LFI-16` : la commission des finances cumule
    67 passages dont 44 d'une journée ou moins, et 5 membres siégeant ; la
    commission des affaires sociales 66 passages et 9 siégeant — le tri sur le
    cumul mettait donc les finances en tête. Ici, en réduction : « Traversée »
    cumule 2 passages clos, « Siège » 1 seul mandat mais encore ouvert — c'est
    « Siège » qui doit être en tête.
    """
    traversee = dict(categorie="commission", label="Traversée")
    siege = dict(categorie="commission", label="Siège")
    p1 = _pivot("nosdeputes:alice", mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(**traversee, debut="2023-10-27", fin="2023-10-27", actif=False),
    ])
    p2 = _pivot("nosdeputes:bob", mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(**traversee, debut="2024-01-24", fin="2024-01-24", actif=False),
    ])
    p3 = _pivot("nosdeputes:carol", mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(**siege, debut="2022-06-30", fin=None, actif=True),
    ])
    membres = _membres_stampes((p1, p2, p3), "2024-01-25")

    result = _aggregate_mandats([p1, p2, p3], membres, "AN", "2024-01-25")

    assert [
        (r["label"], r["nb_membres_a_la_date_de_reference"], r["nb_membres_cumul_historique"])
        for r in result
    ] == [
        ("Siège", 1, 1),
        ("Traversée", 0, 2),
    ]


def test_mandats_agreges_adhesion_dun_jour_comptee_dans_le_cumul_jamais_filtree():
    """#656 : distinguer, pas nettoyer.

    Une adhésion d'un jour est un fait — 43 % des 2 708 adhésions de commission
    publiées par les 7 fiches durent une journée ou moins, parce qu'un⋅e
    député⋅e n'appartient qu'à une commission permanente à la fois et que tout
    passage temporaire y est écrit comme un mandat à part entière. Elle reste comptée dans le cumul, absente
    du décompte de celles et ceux qui y siègent, et sa durée reste lisible
    dans `membres[]`.
    """
    p1 = _pivot("nosdeputes:alice", mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(debut="2022-06-30", fin=None, actif=True),
    ])
    p2 = _pivot("nosdeputes:bob", mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(debut="2023-10-27", fin="2023-10-27", actif=False),
    ])
    membres = _membres_stampes((p1, p2), "2024-01-25")

    result = _aggregate_mandats([p1, p2], membres, "AN", "2024-01-25")

    assert result[0]["nb_membres_cumul_historique"] == 2
    assert result[0]["nb_membres_a_la_date_de_reference"] == 1
    passage = [m for m in result[0]["membres"] if m["membre_id"] == "nosdeputes:bob"]
    assert len(passage) == 1
    assert (passage[0]["debut"], passage[0]["fin"]) == ("2023-10-27", "2023-10-27")


def test_mandats_agreges_ne_publie_aucun_taux_de_rotation():
    """Aucun indice dérivé des adhésions courtes (AGENTS.md §2.1) : un « taux
    de rotation » serait comparable entre groupes, donc un classement."""
    p1 = _pivot("nosdeputes:alice", mandats=[
        _mandat_electif("2022-06-22"),
        _mandat_categoriel(debut="2023-10-27", fin="2023-10-27", actif=False),
    ])
    membres = _membres_stampes((p1,), "2024-01-25")

    result = _aggregate_mandats([p1], membres, "AN", "2024-01-25")

    assert set(result[0]) == {
        "categorie", "label", "nb_membres_a_la_date_de_reference",
        "nb_membres_cumul_historique",
        "effectif_reference", "par_fonction", "membres",
    }


def test_build_groupe_profile_inclut_mandats_agreges():
    p1 = _pivot(mandats=[_mandat_electif("2022-06-22"), _mandat_categoriel()])
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", [p1], scrutins_index=_index())
    assert len(g["mandats_agreges"]) == 1
    assert g["mandats_agreges"][0]["categorie"] == "commission"
    assert validate_profil_groupe(g) == []


def test_build_groupe_profile_mandats_agreges_vide_si_profils_vide():
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", [], scrutins_index=_index())
    assert g["mandats_agreges"] == []


# ---------------------------------------------------------------------------
# _aggregate_amendements
# ---------------------------------------------------------------------------

def _amendement(sort: str, deposant: str = "depute") -> dict:
    return {
        "texte_vise": "PLF 2025",
        "sort": sort,
        "base_juridique_irrecevabilite": "art. 40" if sort == "irrecevable" else None,
        "premier_signataire": "nosdeputes:jean-dupont",
        "co_signataires": [],
        "type_deposant": deposant,
        "date": "2024-10-15",
        "numero": "CL42",
        "source_url": None,
    }


def test_aggregate_amendements_compte_par_statut():
    p1 = _pivot("nosdeputes:alice", amendements=[
        _amendement("adopté"), _amendement("rejeté"), _amendement("irrecevable"),
    ])
    p2 = _pivot("nosdeputes:bob", amendements=[_amendement("retiré")])
    agg, _ = _aggregate_amendements([p1, p2])
    assert agg["nb_amendements"] == 4
    assert agg["nb_adoptes"] == 1
    assert agg["nb_rejetes"] == 1
    assert agg["nb_irrecevables"] == 1
    assert agg["nb_retires_ou_tombes"] == 1


def test_aggregate_amendements_taux_adoption():
    p1 = _pivot(amendements=[_amendement("adopté"), _amendement("rejeté")])
    agg, _ = _aggregate_amendements([p1])
    assert agg["taux_adoption"] == 0.5


def test_aggregate_amendements_sans_accent_est_reconnu():
    """'adopte' (sans accent) doit être reconnu comme 'adopté'."""
    p1 = _pivot(amendements=[_amendement("adopte")])
    agg, _ = _aggregate_amendements([p1])
    assert agg["nb_adoptes"] == 1


def test_aggregate_amendements_taux_none_si_aucun():
    agg, _ = _aggregate_amendements([_pivot(amendements=[])])
    assert agg["nb_amendements"] == 0
    assert agg["taux_adoption"] is None


def test_build_groupe_profile_inclut_amendements_agreges():
    profils = [_pivot(amendements=[_amendement("adopté"), _amendement("rejeté")])]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert g["amendements_agreges"]["nb_amendements"] == 2
    assert g["amendements_agreges"]["taux_adoption"] == 0.5
    assert validate_profil_groupe(g) == []


def test_aggregate_amendements_par_type_deposant_depute():
    p1 = _pivot(amendements=[
        _amendement("adopté", deposant="depute"), _amendement("rejeté", deposant="depute"),
    ])
    agg, _ = _aggregate_amendements([p1])
    assert agg["par_type_deposant"]["depute"]["nb_amendements"] == 2
    assert agg["par_type_deposant"]["depute"]["taux_adoption"] == 0.5


def test_aggregate_amendements_par_type_deposant_ne_pollue_pas_depute():
    """Les amendements gouvernement/rapporteur (quasi tous adoptés) ne doivent pas
    gonfler le sous-total 'depute', utilisé comme comparateur d'un⋅e élu⋅e."""
    p1 = _pivot(amendements=[
        _amendement("rejeté", deposant="depute"),
        _amendement("adopté", deposant="gouvernement"),
        _amendement("adopté", deposant="commission_rapporteur"),
    ])
    agg, _ = _aggregate_amendements([p1])
    assert agg["par_type_deposant"]["depute"]["nb_amendements"] == 1
    assert agg["par_type_deposant"]["depute"]["taux_adoption"] == 0.0
    assert agg["par_type_deposant"]["gouvernement"]["nb_amendements"] == 1
    assert agg["par_type_deposant"]["commission_rapporteur"]["nb_amendements"] == 1
    # Le total, lui, mélange bien tout (c'est pour ça qu'il ne doit pas servir
    # de comparateur direct).
    assert agg["nb_amendements"] == 3
    assert agg["taux_adoption"] == round(2 / 3, 4)


def test_aggregate_amendements_signatures_identiques_avant_apres_normalisation():
    """Critère d'acceptation #431, restreint aux **signatures** par #643.

    Même population, deux formes : l'ancienne (chaque signataire porte
    l'enregistrement complet) et la nouvelle (mapping + index partagé). Le
    décompte des signatures doit coïncider — c'est ce qui prouve qu'aucune
    information utile n'a été perdue en route. Vérifié aussi sur les données
    réelles au moment de la bascule : 810 552 paires, 7 groupes committés,
    **0 écart**.

    Les **amendements distincts**, eux, ne peuvent pas coïncider, et ce n'est
    pas un défaut : la forme plate ne porte aucun `amendement_id`, donc rien ne
    permet de rapprocher deux copies d'un même amendement. Le test le dit au
    lieu de le masquer — c'est exactement ce que `nb_sans_identifiant` publie.
    """
    from amendements_index import cle_amendement, construire_index

    sorts = ["adopté", "rejeté", "irrecevable", "retiré", "tombé", "non_soutenu", "adopte"]
    deposants = ["depute", "gouvernement", "commission_rapporteur"]
    plats = []
    for i, sort in enumerate(sorts):
        for j, deposant in enumerate(deposants):
            a = _amendement(sort, deposant=deposant)
            a["uid"] = f"AMANR5L17PO0B0000P0D1N{i * 10 + j:06d}"
            a["role_signataire"] = "auteur_principal" if j == 0 else "cosignataire"
            plats.append(a)
    # Un même amendement recopié chez trois signataires : la duplication que
    # #431 supprime. C'est une paire (membre, amendement), donc trois
    # signatures — et **un** amendement.
    plats += [dict(plats[0]), dict(plats[0])]

    avant, non_resolus_avant = _aggregate_amendements([_pivot(amendements=plats)])
    assert non_resolus_avant == 0

    index = construire_index(plats)
    mapping = [
        {"amendement_id": cle_amendement(a["uid"]), "role_signataire": a["role_signataire"]}
        for a in plats
    ]
    apres, non_resolus_apres = _aggregate_amendements([_pivot(amendements=mapping)], index)

    assert non_resolus_apres == 0
    assert apres["signatures"] == avant["signatures"]
    assert apres["signatures"]["nb_signatures"] == 23

    # 21 amendements distincts, la copie triple ramenée à une.
    assert apres["nb_amendements"] == 21
    assert apres["nb_sans_identifiant"] == 0
    # La forme plate n'a pas de clé : chaque entrée compte pour un amendement,
    # et le champ qui le dit n'est pas nul.
    assert avant["nb_amendements"] == 23
    assert avant["nb_sans_identifiant"] == 23


def test_aggregate_amendements_entree_non_resolue_est_comptee_pas_ignoree():
    """Une exclusion muette transformerait un dénominateur en donnée fausse
    (AGENTS.md §2.7)."""
    from amendements_index import construire_index

    connu = _amendement("adopté")
    connu["uid"] = "AMANR5L17PO0B0000P0D1N000001"
    index = construire_index([connu])
    mapping = [
        {"amendement_id": "an:AMANR5L17PO0B0000P0D1N000001", "role_signataire": "auteur_principal"},
        # Référence un amendement qu'un index partiel ne connaît pas.
        {"amendement_id": "an:AMANR5L17PO0B0000P0D1N999999", "role_signataire": "cosignataire"},
    ]
    agg, non_resolus = _aggregate_amendements([_pivot(amendements=mapping)], index)
    assert agg["nb_amendements"] == 1
    assert non_resolus == 1


def test_aggregate_amendements_entree_sans_index_lit_lenregistrement_conserve():
    """`amendement_non_resolu` porte l'enregistrement complet : il est lu, pas
    écarté."""
    mapping = [{
        "amendement_id": None,
        "role_signataire": "auteur_principal",
        "amendement_non_resolu": _amendement("adopté"),
    }]
    agg, non_resolus = _aggregate_amendements([_pivot(amendements=mapping)], None)
    assert agg["nb_amendements"] == 1
    assert agg["nb_adoptes"] == 1
    assert non_resolus == 0


def test_aggregate_amendements_type_deposant_absent_est_inconnu():
    a = _amendement("adopté")
    del a["type_deposant"]
    agg, _ = _aggregate_amendements([_pivot(amendements=[a])])
    assert agg["par_type_deposant"]["inconnu"]["nb_amendements"] == 1
    assert agg["par_type_deposant"]["depute"]["nb_amendements"] == 0


def test_build_groupe_profile_amendements_agreges_par_type_deposant_valide():
    profils = [_pivot(amendements=[
        _amendement("adopté", deposant="depute"), _amendement("adopté", deposant="gouvernement"),
    ])]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert g["amendements_agreges"]["par_type_deposant"]["depute"]["nb_amendements"] == 1
    assert g["amendements_agreges"]["par_type_deposant"]["gouvernement"]["nb_amendements"] == 1
    assert validate_profil_groupe(g) == []


# ---------------------------------------------------------------------------
# #643 — un amendement cosigné n'est pas N amendements
#
# `_aggregate_amendements` faisait `nb_amendements += 1` par entrée de profil,
# donc une fois par signataire, et publiait le résultat sous le mot
# « amendements ». 92,2 % des entrées du corpus étant des cosignatures,
# `AN:LFI` annonçait 2 600 765 amendements déposés pour 76 députés.
#
# Les fixtures qui suivent sont minuscules mais leurs formes viennent des
# données : un amendement cosigné (le cas dominant), un `sort` absent (33,3 %
# des 132 960 amendements distincts d'`AN:LFI`), une entrée sans identifiant
# (la forme normale d'un amendement du Parlement européen).
# ---------------------------------------------------------------------------

def _mapping(uid: str, role: str = "cosignataire") -> dict:
    return {"amendement_id": f"an:{uid}", "role_signataire": role}


def _index_amendements(*specs) -> "object":
    """Index partagé bâti depuis `(uid, sort, type_deposant)`."""
    from amendements_index import construire_index

    plats = []
    for uid, sort, deposant in specs:
        a = _amendement(sort, deposant=deposant)
        a["uid"] = uid
        plats.append(a)
    return construire_index(plats)


def test_aggregate_amendements_un_amendement_cosigne_ne_compte_quune_fois():
    """Le défaut de #643, dans sa plus petite forme."""
    index = _index_amendements(("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"))
    profils = [_pivot(f"nosdeputes:m{i}", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")])
               for i in range(3)]
    agg, _ = _aggregate_amendements(profils, index)
    assert agg["nb_amendements"] == 1
    assert agg["par_type_deposant"]["depute"]["nb_amendements"] == 1


def test_aggregate_amendements_signatures_comptent_chaque_signataire():
    """L'autre grandeur n'est pas perdue : elle est nommée."""
    index = _index_amendements(("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"))
    profils = [_pivot(f"nosdeputes:m{i}", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")])
               for i in range(3)]
    agg, _ = _aggregate_amendements(profils, index)
    assert agg["signatures"]["nb_signatures"] == 3
    assert agg["signatures"]["par_type_deposant"]["depute"]["nb_signatures"] == 3


def test_aggregate_amendements_taux_dadoption_baisse_quand_ladopte_est_le_plus_cosigne():
    """Le cas `AN:LFI` : 5,01 % publié → 2,99 % sur les distincts (seau `depute`)."""
    index = _index_amendements(
        ("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"),
        ("AMANR5L17PO0B0000P0D1N000002", "rejeté", "depute"),
    )
    profils = [
        _pivot("nosdeputes:a", amendements=[
            _mapping("AMANR5L17PO0B0000P0D1N000001"), _mapping("AMANR5L17PO0B0000P0D1N000002"),
        ]),
        _pivot("nosdeputes:b", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")]),
        _pivot("nosdeputes:c", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")]),
    ]
    agg, _ = _aggregate_amendements(profils, index)
    assert agg["signatures"]["nb_signatures"] == 4  # dont 3 sur l'adopté
    assert agg["nb_amendements"] == 2
    assert agg["taux_adoption"] == 0.5


def test_aggregate_amendements_taux_dadoption_monte_quand_le_rejete_est_le_plus_cosigne():
    """Le cas `AN:SOC`, en sens inverse : 7,24 % publié → 14,54 % sur les distincts.

    C'est cette bidirectionnalité qui rend le défaut publiable-mais-faux : le
    taux n'était pas biaisé dans une direction connue (AGENTS.md §2 règle 7).
    """
    index = _index_amendements(
        ("AMANR5L17PO0B0000P0D1N000001", "rejeté", "depute"),
        ("AMANR5L17PO0B0000P0D1N000002", "adopté", "depute"),
    )
    profils = [
        _pivot("nosdeputes:a", amendements=[
            _mapping("AMANR5L17PO0B0000P0D1N000001"), _mapping("AMANR5L17PO0B0000P0D1N000002"),
        ]),
        _pivot("nosdeputes:b", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")]),
        _pivot("nosdeputes:c", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")]),
    ]
    agg, _ = _aggregate_amendements(profils, index)
    assert agg["signatures"]["nb_signatures"] == 4  # dont 1 seule sur l'adopté
    assert agg["nb_amendements"] == 2
    assert agg["taux_adoption"] == 0.5


def test_aggregate_amendements_sort_absent_a_sa_bande():
    """33,3 % des amendements distincts d'`AN:LFI` n'ont pas de `sort`.

    Sans bande, une barre empilée publierait un tiers d'absences comme des
    zéros (AGENTS.md §2 règle 5).
    """
    index = _index_amendements(
        ("AMANR5L17PO0B0000P0D1N000001", None, "depute"),
        ("AMANR5L17PO0B0000P0D1N000002", "adopté", "depute"),
    )
    profils = [_pivot(amendements=[
        _mapping("AMANR5L17PO0B0000P0D1N000001"), _mapping("AMANR5L17PO0B0000P0D1N000002"),
    ])]
    agg, _ = _aggregate_amendements(profils, index)
    assert agg["nb_sort_non_renseigne"] == 1
    assert agg["nb_sort_non_reconnu"] == 0
    assert agg["par_type_deposant"]["depute"]["nb_sort_non_renseigne"] == 1


def test_aggregate_amendements_sort_hors_nomenclature_nest_pas_une_absence():
    """Compteur sous surveillance (AGENTS.md §3d) : 0 sur les 484 132
    amendements de l'index au 31/08/2026, sept libellés seulement.

    Le ranger sous « non renseigné » publierait une valeur présente comme une
    absence — l'erreur exactement symétrique de celle que la bande corrige.
    """
    index = _index_amendements(("AMANR5L17PO0B0000P0D1N000001", "satisfait", "depute"))
    agg, _ = _aggregate_amendements(
        [_pivot(amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")])], index
    )
    assert agg["nb_sort_non_reconnu"] == 1
    assert agg["nb_sort_non_renseigne"] == 0


@pytest.mark.parametrize("bloc", ["total", "depute"])
def test_aggregate_amendements_les_six_bandes_somment_au_total(bloc):
    """L'invariant qui rend une barre empilée honnête."""
    from group_profile import BANDES_DE_SORT

    index = _index_amendements(
        ("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"),
        ("AMANR5L17PO0B0000P0D1N000002", "rejeté", "depute"),
        ("AMANR5L17PO0B0000P0D1N000003", "irrecevable", "depute"),
        ("AMANR5L17PO0B0000P0D1N000004", "tombé", "depute"),
        ("AMANR5L17PO0B0000P0D1N000005", None, "depute"),
        ("AMANR5L17PO0B0000P0D1N000006", "satisfait", "depute"),
    )
    profils = [_pivot(amendements=[
        _mapping(f"AMANR5L17PO0B0000P0D1N00000{i}") for i in range(1, 7)
    ])]
    agg, _ = _aggregate_amendements(profils, index)
    stats = agg if bloc == "total" else agg["par_type_deposant"]["depute"]
    assert sum(stats[b] for b in BANDES_DE_SORT) == stats["nb_amendements"] == 6


def test_aggregate_amendements_entree_sans_identifiant_est_comptee_par_signataire():
    """Aucune clé ne s'invente (AGENTS.md §2 règle 5).

    Un amendement sans `amendement_id` — la forme normale côté Parlement
    européen — n'est rapprochable d'aucun autre : il est compté tel quel, et le
    champ qui le dit est publié pour que `nb_amendements` ne mélange pas en
    silence deux natures de compte.
    """
    entree = {
        "amendement_id": None,
        "role_signataire": "cosignataire",
        "amendement_non_resolu": _amendement("adopté"),
    }
    profils = [_pivot(f"nosdeputes:m{i}", amendements=[dict(entree)]) for i in range(3)]
    agg, non_resolus = _aggregate_amendements(profils)
    assert non_resolus == 0
    assert agg["nb_amendements"] == 3
    assert agg["nb_sans_identifiant"] == 3


def test_build_groupe_profile_avertit_sur_les_amendements_non_dedoublonnables():
    entree = {
        "amendement_id": None,
        "role_signataire": "cosignataire",
        "amendement_non_resolu": _amendement("adopté"),
    }
    profils = [_pivot(f"nosdeputes:m{i}", amendements=[dict(entree)]) for i in range(2)]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils,
                             scrutins_index=_index())
    assert any("non dédoublonnables" in w for w in g["meta"]["warnings"])


def test_build_groupe_profile_ne_previent_pas_quand_tout_est_dedoublonnable():
    index = _index_amendements(("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"))
    profils = [_pivot(amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")])]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils,
                             scrutins_index=_index(), amendements_index=index)
    assert not any("non dédoublonnables" in w for w in g["meta"]["warnings"])
    assert g["amendements_agreges"]["nb_sans_identifiant"] == 0
    assert validate_profil_groupe(g) == []


def test_build_groupe_profile_publie_les_deux_grandeurs_sous_deux_noms():
    index = _index_amendements(("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"))
    profils = [_pivot(f"nosdeputes:m{i}", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")])
               for i in range(4)]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils,
                             scrutins_index=_index(), amendements_index=index)
    agg = g["amendements_agreges"]
    assert agg["nb_amendements"] == 1
    assert agg["signatures"]["nb_signatures"] == 4
    assert validate_profil_groupe(g) == []


def test_aggregate_amendements_cumul_partage_donne_le_meme_resultat_que_par_membre():
    """Le partage du cumul est une économie de mémoire, jamais un changement de
    résultat : un cumul absorbé une fois ou trois donne le même compte."""
    from group_profile import CumulAmendementsDistincts, contribution_amendements

    index = _index_amendements(
        ("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"),
        ("AMANR5L17PO0B0000P0D1N000002", "rejeté", "depute"),
    )
    entiers = [
        _pivot("nosdeputes:a", amendements=[
            _mapping("AMANR5L17PO0B0000P0D1N000001"), _mapping("AMANR5L17PO0B0000P0D1N000002"),
        ]),
        _pivot("nosdeputes:b", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")]),
    ]
    partage = CumulAmendementsDistincts()
    reduits = [
        dict(p, amendements=contribution_amendements(p["amendements"], index, partage))
        for p in entiers
    ]
    assert len(partage.par_id) == 2
    assert _aggregate_amendements(reduits) == _aggregate_amendements(entiers, index)


def test_load_profil_from_file_alimente_le_cumul_partage_de_la_fiche(tmp_path):
    """Ce qui rend la déduplication possible une fois les entrées relâchées.

    Sans cumul partagé, dédoublonner demanderait de garder un ensemble
    d'identifiants **par membre** — les 2 647 601 signatures d'`AN:LFI` au lieu
    de ses 132 960 amendements distincts, soit la mémoire que #635 vient de
    rendre.
    """
    from group_profile import CumulAmendementsDistincts

    index = _index_amendements(("AMANR5L17PO0B0000P0D1N000001", "adopté", "depute"))
    cumul = CumulAmendementsDistincts()
    for i in range(3):
        chemin = tmp_path / f"m{i}.pivot.json"
        chemin.write_text(json.dumps(
            _pivot(f"nosdeputes:m{i}", amendements=[_mapping("AMANR5L17PO0B0000P0D1N000001")]),
            ensure_ascii=False,
        ), encoding="utf-8")
        charge = load_profil_from_file(chemin, index, distincts=cumul)
        assert charge["amendements"].distincts is cumul
    assert len(cumul.par_id) == 1
    assert len(cumul) == 1


# ---------------------------------------------------------------------------
# compute_ecarts_cohesion_internes (contrôle interne, hors schéma public)
# ---------------------------------------------------------------------------

def test_ecarts_cohesion_internes_membre_aligne_ecart_nul():
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[_vote("42", "pour")])
    cohesion = _compute_cohesion_votes([p1, p2], scrutins_index=_index())
    ecarts = compute_ecarts_cohesion_internes([p1, p2], cohesion, scrutins_index=_index())
    for e in ecarts:
        assert e["taux_participation_individuel"] == 1.0
        assert e["taux_coherence_individuel"] == 1.0
        assert e["ecart_participation_vs_groupe"] == 0.0
        assert e["ecart_coherence_vs_groupe"] == 0.0


def test_ecarts_cohesion_internes_membre_moins_coherent():
    p1 = _pivot("nosdeputes:alice", votes=[_vote("42", "pour")])
    p2 = _pivot("nosdeputes:bob", votes=[_vote("42", "contre")])
    p3 = _pivot("nosdeputes:charlie", votes=[_vote("42", "pour")])
    cohesion = _compute_cohesion_votes([p1, p2, p3], scrutins_index=_index())
    ecarts = compute_ecarts_cohesion_internes([p1, p2, p3], cohesion, scrutins_index=_index())
    bob = next(e for e in ecarts if e["membre_id"] == "nosdeputes:bob")
    assert bob["taux_coherence_individuel"] == 0.0
    assert bob["ecart_coherence_vs_groupe"] < 0


def test_ecarts_cohesion_internes_vide_si_pas_de_cohesion():
    assert compute_ecarts_cohesion_internes([_pivot()], []) == []


def test_ecarts_cohesion_internes_absent_du_profil_groupe_public():
    """Champ de contrôle interne : ne doit jamais apparaître dans le profil public."""
    profils = [_pivot("nosdeputes:alice", votes=[_vote("42", "pour")])]
    g = build_groupe_profile("AN:SOC", "SOC", "Socialistes", "AN", "16", profils, scrutins_index=_index())
    assert "ecarts_cohesion_internes" not in g
    assert "compute_ecarts_cohesion_internes" not in str(g)


# ---------------------------------------------------------------------------
# CLI --from-roster (composition réelle du groupe via group_roster.py)
# ---------------------------------------------------------------------------

def test_main_from_roster_builds_group_and_reports_couverture(tmp_path, monkeypatch):
    (tmp_path / "alice.pivot.json").write_text(json.dumps(_pivot("nosdeputes:alice")), encoding="utf-8")
    # "bob" fait partie du roster mais n'a aucun pivot local dans tmp_path.

    def fake_fetch_group_roster(chambre, groupe_sigle, legislature=None, senat_periode_debut=None):
        assert chambre == "deputes"
        assert groupe_sigle == "LR"
        assert legislature == "16"
        return [
            {"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
            {"slug": "bob", "nom": "Bob", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
        ]

    monkeypatch.setattr("group_roster.fetch_group_roster", fake_fetch_group_roster)

    out_path = tmp_path / "out.json"
    rc = group_profile_main([
        "--from-roster", "--roster-chambre", "deputes",
        "--groupe-id", "AN:LR", "--groupe-sigle", "LR", "--groupe-nom", "Les Républicains",
        "--chambre", "AN", "--legislature", "16",
        "--profiles-dir", str(tmp_path),
        "--out", str(out_path),
    ])

    assert rc == 0
    profil_groupe = json.loads(out_path.read_text(encoding="utf-8"))
    # `etat` (#558) : un groupe généré par ce chemin est un groupe activement
    # collecté — `generate_group_profiles` écarte les entrées suspendues.
    assert profil_groupe["meta"]["couverture_roster"] == {
        "roster_total": 2, "profils_disponibles": 1,
        "etat": ETAT_ROSTER_DANS_LE_PERIMETRE,
    }
    assert len(profil_groupe["membres"]) == 1
    assert validate_profil_groupe(profil_groupe) == []


def test_main_from_roster_missing_roster_chambre_returns_error(capsys):
    rc = group_profile_main([
        "--from-roster",
        "--groupe-id", "AN:LR", "--groupe-sigle", "LR", "--groupe-nom", "Les Républicains",
    ])
    assert rc == 1
    assert "--roster-chambre" in capsys.readouterr().err


def test_main_from_roster_merge_existing_recupere_membre_absent_du_roster(tmp_path, monkeypatch):
    """--merge-existing : un membre présent dans --out lors d'une exécution précédente
    mais absent du roster récupéré cette fois-ci (échec partiel de récupération) doit
    être réintégré, avec un avertissement explicite dans meta.warnings."""
    (tmp_path / "alice.pivot.json").write_text(json.dumps(_pivot("nosdeputes:alice")), encoding="utf-8")
    (tmp_path / "bob.pivot.json").write_text(json.dumps(_pivot("nosdeputes:bob")), encoding="utf-8")

    def fake_fetch_group_roster_complet(chambre, groupe_sigle, legislature=None, senat_periode_debut=None):
        return [
            {"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
            {"slug": "bob", "nom": "Bob", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
        ]

    out_path = tmp_path / "out.json"
    monkeypatch.setattr("group_roster.fetch_group_roster", fake_fetch_group_roster_complet)
    rc = group_profile_main([
        "--from-roster", "--roster-chambre", "deputes",
        "--groupe-id", "AN:LR", "--groupe-sigle", "LR", "--groupe-nom", "Les Républicains",
        "--chambre", "AN", "--legislature", "16",
        "--profiles-dir", str(tmp_path),
        "--out", str(out_path),
    ])
    assert rc == 0
    assert len(json.loads(out_path.read_text(encoding="utf-8"))["membres"]) == 2

    # Exécution suivante : le roster live ne renvoie plus que "bob" (échec partiel simulé).
    def fake_fetch_group_roster_partiel(chambre, groupe_sigle, legislature=None, senat_periode_debut=None):
        return [
            {"slug": "bob", "nom": "Bob", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
        ]

    monkeypatch.setattr("group_roster.fetch_group_roster", fake_fetch_group_roster_partiel)
    rc = group_profile_main([
        "--from-roster", "--roster-chambre", "deputes",
        "--groupe-id", "AN:LR", "--groupe-sigle", "LR", "--groupe-nom", "Les Républicains",
        "--chambre", "AN", "--legislature", "16",
        "--profiles-dir", str(tmp_path),
        "--out", str(out_path),
        "--merge-existing",
    ])
    assert rc == 0
    profil_groupe = json.loads(out_path.read_text(encoding="utf-8"))
    membres_ids = {m["membre_id"] for m in profil_groupe["membres"]}
    assert "nosdeputes:alice" in membres_ids
    assert "nosdeputes:bob" in membres_ids
    assert any("fusion_avec_existant" in w and "alice" in w for w in profil_groupe["meta"]["warnings"])


def test_main_from_roster_sans_merge_existing_perd_membre_absent_du_roster(tmp_path, monkeypatch):
    """Sans --merge-existing (comportement par défaut), --out écrase entièrement :
    un membre absent du roster récupéré cette fois-ci disparaît du fichier de sortie."""
    (tmp_path / "alice.pivot.json").write_text(json.dumps(_pivot("nosdeputes:alice")), encoding="utf-8")
    (tmp_path / "bob.pivot.json").write_text(json.dumps(_pivot("nosdeputes:bob")), encoding="utf-8")

    def fake_fetch_group_roster_complet(chambre, groupe_sigle, legislature=None, senat_periode_debut=None):
        return [
            {"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
            {"slug": "bob", "nom": "Bob", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
        ]

    out_path = tmp_path / "out.json"
    monkeypatch.setattr("group_roster.fetch_group_roster", fake_fetch_group_roster_complet)
    group_profile_main([
        "--from-roster", "--roster-chambre", "deputes",
        "--groupe-id", "AN:LR", "--groupe-sigle", "LR", "--groupe-nom", "Les Républicains",
        "--chambre", "AN", "--legislature", "16",
        "--profiles-dir", str(tmp_path),
        "--out", str(out_path),
    ])

    def fake_fetch_group_roster_partiel(chambre, groupe_sigle, legislature=None, senat_periode_debut=None):
        return [
            {"slug": "bob", "nom": "Bob", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True},
        ]

    monkeypatch.setattr("group_roster.fetch_group_roster", fake_fetch_group_roster_partiel)
    group_profile_main([
        "--from-roster", "--roster-chambre", "deputes",
        "--groupe-id", "AN:LR", "--groupe-sigle", "LR", "--groupe-nom", "Les Républicains",
        "--chambre", "AN", "--legislature", "16",
        "--profiles-dir", str(tmp_path),
        "--out", str(out_path),
    ])
    profil_groupe = json.loads(out_path.read_text(encoding="utf-8"))
    membres_ids = {m["membre_id"] for m in profil_groupe["membres"]}
    assert membres_ids == {"nosdeputes:bob"}




# ---------------------------------------------------------------------------
# #80 — aggregate_tags_thematiques avec theme_officiel Syceron
# ---------------------------------------------------------------------------

def test_tags_fallback_sur_theme_officiel_avant_mots_cles():
    """Si tags_thematiques est vide, theme_officiel est préféré aux mots_cles."""
    interventions = [
        {
            "theme_officiel": "réforme des retraites",
            "mots_cles": ["social", "emploi"],
            "date": "2025-01-01",
        }
    ]
    p1 = _pivot(tags=[], interventions=interventions)
    _agregat = aggregate_tags_thematiques([p1])
    tags, source = _agregat.tags, _agregat.source
    tag_names = {t["tag"] for t in tags}
    assert "réforme des retraites" in tag_names
    # mots_cles ne doivent pas apparaître quand theme_officiel est disponible
    assert "social" not in tag_names
    assert source == "theme_officiel"


def test_tags_fallback_mots_cles_si_pas_theme_officiel():
    """Si theme_officiel est absent (None), les mots_cles sont utilisés en fallback."""
    interventions = [
        {
            "theme_officiel": None,
            "mots_cles": ["immigration", "social"],
            "date": "2024-01-01",
        }
    ]
    p1 = _pivot(tags=[], interventions=interventions)
    _agregat = aggregate_tags_thematiques([p1])
    tags, source = _agregat.tags, _agregat.source
    tag_names = {t["tag"] for t in tags}
    assert "immigration" in tag_names
    assert source == "mots_cles_interventions"


# ---------------------------------------------------------------------------
# #191 — roster largement couvert (post #190), à l'opposé des scénarios de
# faible couverture ci-dessus (candidats.json, échantillon éditorial réduit).
# ---------------------------------------------------------------------------

def _synthetic_pivot(i: int, nb_votes: int = 5) -> dict:
    """Profil pivot synthétique pour un membre numéroté (scénario grande échelle)."""
    slug = f"membre-{i}"
    votes = [
        _vote(str(v), "pour" if (i + v) % 2 == 0 else "contre", date=f"2023-{(v % 12) + 1:02d}-01")
        for v in range(nb_votes)
    ]
    return _pivot(f"nosdeputes:{slug}", f"Membre {i}", mandats=[_mandat_electif("2022-06-22")], votes=votes)


def test_from_roster_couverture_roster_grande_echelle_quasi_complete(tmp_path):
    """Roster de 60 membres avec 58 profils pivot locaux (~97 %) — scénario
    'roster largement couvert', complémentaire des tests de faible couverture
    ci-dessus (test_main_from_roster_builds_group_and_reports_couverture)."""
    n = 60
    n_manquants = 2
    roster = []
    for i in range(n):
        slug = f"membre-{i}"
        roster.append({
            "slug": slug, "nom": f"Membre {i}", "groupe_sigle": "LR",
            "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True,
        })
        if i < n - n_manquants:
            (tmp_path / f"{slug}.pivot.json").write_text(
                json.dumps(_synthetic_pivot(i)), encoding="utf-8",
            )

    profil_groupe = generate_groupe_profile_from_roster(
        roster=roster,
        groupe_id="AN:LR", groupe_sigle="LR", groupe_nom="Les Républicains",
        chambre="AN", legislature="16", roster_chambre="deputes",
        profiles_dir=tmp_path,
    )

    couverture = profil_groupe["meta"]["couverture_roster"]
    assert couverture["roster_total"] == n
    assert couverture["profils_disponibles"] == n - n_manquants
    assert couverture["profils_disponibles"] / couverture["roster_total"] > 0.95
    assert len(profil_groupe["membres"]) == n - n_manquants
    # Roster ouvert (aucun `mandat_fin`) → date de référence = la génération, et
    # les 58 membres couverts y appartiennent tous au groupe (#653).
    assert profil_groupe["date_reference"]["origine"] == "generation"
    assert profil_groupe["effectif"]["a_la_date_de_reference"] == n - n_manquants
    assert validate_profil_groupe(profil_groupe) == []


def test_build_groupe_profile_scale_200_membres_sans_lenteur_perceptible():
    """Pas de dégradation de performance perceptible à ~200 membres/groupe
    (mesure informelle, cf. critère d'acceptation #191 — pas de benchmark
    formel requis). Sert aussi de garde-fou anti-régression quadratique :
    _compute_cohesion_votes est O(scrutins x membres), jamais O(membres^2)."""
    import time

    n_membres = 200
    n_votes = 150
    profils = [_synthetic_pivot(i, nb_votes=n_votes) for i in range(n_membres)]

    debut = time.monotonic()
    g = build_groupe_profile("AN:LR", "LR", "Les Républicains", "AN", "16", profils, scrutins_index=_index())
    duree = time.monotonic() - debut

    assert len(g["membres"]) == n_membres
    assert len(g["cohesion_votes"]) == n_votes
    assert validate_profil_groupe(g) == []
    assert duree < 5.0, f"build_groupe_profile trop lent à l'échelle ({duree:.2f}s) : régression possible"


# `test_from_roster_senat_warning_couverture_roster_senat_present` a été retiré
# par #528 : la branche `roster_chambre == "senateurs"` de
# `generate_groupe_profile_from_roster` est partie avec le Sénat. Les deux
# fiches `groupe-Senat-*.json` restent PUBLIÉES et FIGÉES, avec leurs deux
# avertissements — elles ne sont plus régénérées (suspension #516), et les
# retirer supprimerait un fichier publié, ce que `audit_diff_profils` bloque
# (#460/#470). Le test ci-dessous garde l'autre moitié : le warning ne doit pas
# apparaître là où il n'a rien à faire.

def test_from_roster_deputes_pas_de_warning_couverture_roster_senat(tmp_path):
    """Le warning spécifique Sénat ne doit pas apparaître pour un roster AN —
    et depuis #528 il ne doit plus apparaître nulle part sur une génération."""
    roster = [{"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None, "actif": True}]
    (tmp_path / "alice.pivot.json").write_text(json.dumps(_pivot("nosdeputes:alice")), encoding="utf-8")

    profil_groupe = generate_groupe_profile_from_roster(
        roster=roster,
        groupe_id="AN:LR", groupe_sigle="LR", groupe_nom="Les Républicains",
        chambre="AN", legislature="16", roster_chambre="deputes",
        profiles_dir=tmp_path,
    )

    assert not any("couverture_roster_senat" in w for w in profil_groupe["meta"]["warnings"])


# ---------------------------------------------------------------------------
# #403 — cohésion et multi-législature : le numéro de scrutin n'identifie un
# scrutin qu'à législature donnée (il repart de 1 à chaque législature).
# ---------------------------------------------------------------------------

def _vote_legis(numero: str, position: str, legislature: str, date: str, texte: str = "PLF") -> dict:
    return _vote(numero, position, date=date, texte=texte, legislature=legislature)


def test_cohesion_ne_melange_pas_deux_legislatures_sous_un_meme_numero():
    """Deux scrutins n° 1000 (16e et 17e) sont deux textes sans rapport : la
    cohésion d'un groupe de la 16e ne doit retenir que le sien, jamais fusionner
    les deux décomptes sous un numéro unique."""
    membre = _pivot(
        "nosdeputes:alice",
        mandats=[_mandat_electif("2022-06-22")],
        votes=[
            _vote_legis("1000", "pour", "16", "2023-01-15"),
            _vote_legis("1000", "contre", "17", "2025-03-13"),
        ],
    )

    index = _index()
    cohesion = _compute_cohesion_votes([membre], legislature="16", scrutins_index=index)

    assert len(cohesion) == 1, "Un seul scrutin retenu : celui de la législature du groupe"
    assert cohesion[0]["scrutin_id"] == "an:16:1000"
    assert index.get(cohesion[0]["scrutin_id"])["date"] == "2023-01-15"
    assert cohesion[0]["pour"] == 1
    assert cohesion[0]["contre"] == 0


def test_cohesion_ecarte_les_scrutins_d_une_autre_legislature():
    """Un membre encore en mandat sous la 17e ne doit pas apporter ses scrutins
    de la 17e à un profil de groupe de la 16e : le groupe n'existait pas au
    moment de ces votes."""
    membre = _pivot(
        "nosdeputes:alice",
        mandats=[_mandat_electif("2022-06-22")],
        votes=[
            _vote_legis("10", "pour", "16", "2023-01-15"),
            _vote_legis("20", "pour", "17", "2025-03-13"),
        ],
    )

    cohesion = _compute_cohesion_votes([membre], legislature="16", scrutins_index=_index())

    assert {r["scrutin_id"] for r in cohesion} == {"an:16:10"}


def test_cohesion_conserve_les_votes_sans_legislature():
    """Les votes collectés avant #403 n'ont pas de législature : ils sont
    conservés (règle 5 — une donnée absente n'est pas une donnée contradictoire),
    sans quoi une regénération partielle viderait la cohésion existante."""
    membre = _pivot("nosdeputes:alice", mandats=[_mandat_electif("2022-06-22")], votes=[_vote("42", "pour")])

    cohesion = _compute_cohesion_votes([membre], legislature="16", scrutins_index=_index())

    assert [r["scrutin_id"] for r in cohesion] == ["an:16:42"]


def test_cohesion_sans_legislature_de_groupe_ne_filtre_rien():
    """Un groupe sans législature (Sénat) agrège tous ses votes."""
    membre = _pivot(
        "nosdeputes:alice",
        mandats=[_mandat_electif("2022-06-22")],
        votes=[_vote_legis("10", "pour", "16", "2023-01-15"), _vote_legis("20", "pour", "17", "2025-03-13")],
    )

    cohesion = _compute_cohesion_votes([membre], legislature=None, scrutins_index=_index())

    assert {r["scrutin_id"] for r in cohesion} == {"an:16:10", "an:17:20"}


def test_build_vote_index_restreint_a_la_legislature():
    membre = _pivot(
        "nosdeputes:alice",
        votes=[_vote_legis("1000", "pour", "16", "2023-01-15"), _vote_legis("1000", "contre", "17", "2025-03-13")],
    )

    index = _build_vote_index(membre, "17")

    assert index["an:17:1000"]["position"] == "contre", (
        "La tranche de la 17e ne doit pas être écrasée par celle de la 16e"
    )
    assert "an:16:1000" not in index


def test_ecarts_internes_utilisent_la_meme_legislature_que_la_cohesion():
    """Le rapport interne compare membre et groupe scrutin par scrutin : s'il
    indexait les votes toutes législatures confondues, le n° 1000 de la 17e
    d'un membre serait comparé à la position majoritaire du n° 1000 de la 16e."""
    membres = [
        _pivot(
            f"nosdeputes:m{i}",
            mandats=[_mandat_electif("2022-06-22")],
            votes=[
                _vote_legis("1000", "pour", "16", "2023-01-15"),
                _vote_legis("1000", "contre", "17", "2025-03-13"),
            ],
        )
        for i in range(2)
    ]
    cohesion = _compute_cohesion_votes(membres, legislature="16", scrutins_index=_index())

    rapport = compute_ecarts_cohesion_internes(membres, cohesion, "16", scrutins_index=_index())

    assert all(r["nb_scrutins_eligibles"] == 1 for r in rapport)
    assert all(r["taux_coherence_individuel"] == 1.0 for r in rapport), (
        "Chaque membre est aligné sur la position majoritaire du scrutin de la 16e"
    )


def test_build_groupe_profile_transmet_sa_legislature_a_la_cohesion():
    """Bout en bout : un profil de groupe de la 16e ne publie que des scrutins
    de la 16e, quand bien même ses membres portent désormais ceux de la 17e."""
    membres = [
        _pivot(
            "nosdeputes:alice",
            mandats=[_mandat_electif("2022-06-22")],
            votes=[
                _vote_legis("10", "pour", "16", "2023-01-15"),
                _vote_legis("11", "pour", "17", "2025-03-13"),
            ],
        )
    ]

    profil = build_groupe_profile(
        groupe_id="AN:SOC", groupe_sigle="SOC", groupe_nom="Socialistes",
        chambre="AN", legislature="16", profils=membres, scrutins_index=_index(),
    )

    assert [c["scrutin_id"] for c in profil["cohesion_votes"]] == ["an:16:10"]


# ---------------------------------------------------------------------------
# Mémoire : le plafond est dans le test (#635)
# ---------------------------------------------------------------------------
#
# `generate_groupe_profile_from_roster` gardait le profil **entier** de chaque
# membre du roster. Mesuré sur les 5 fiches AN publiées, index partagés déjà
# chargés, chaque groupe dans son propre processus :
#
#   LFI  76 membres  253,5 Mo sur disque   985,8 Mio -> 82,3 Mio
#                                          (932,6 -> 66,7 au rejeu du 31/08)
#   REN 193 membres   97,2 Mo              372,4 Mio -> 128,1 Mio
#   RN   90 membres  128,1 Mo              471,7 Mio -> 59,7 Mio
#
# `amendements[]` fait l'essentiel de ce poids (577,3 des 651,5 Mo du corpus
# committé du 30/08/2026) et la fiche n'en tire que des **compteurs additifs**.
# Ils sont donc calculés au chargement, membre par membre, et les entrées
# meurent — `votes` et `mandats`, eux, sont réellement parcourus et restent.

NB_PROFILS_FIXTURE_MEMOIRE = 24

#: Poids visé, par membre, de l'`amendements[]` que le chargement doit relâcher.
POIDS_AMENDEMENTS_RELACHES = 2 * 1024 * 1024

#: Plancher de vraisemblance du corpus-fixture : sous ce poids, le plafond
#: qu'il déduit ne prouve plus rien. Regonfler les fixtures, jamais desserrer
#: le plancher.
PLANCHER_POIDS_RELACHE = 40 * 1024 * 1024

_PILOTE_MEMOIRE = """\
import json, resource, sys
from pathlib import Path

depot, dossier = sys.argv[1], sys.argv[2]
sys.path.insert(0, str(Path(depot) / "src"))
import group_profile

depart = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
profils = [group_profile.load_profil_from_file(p)
           for p in sorted(Path(dossier).glob("*.pivot.json"))]
fiche = group_profile.build_groupe_profile(
    groupe_id="AN:TEST", groupe_sigle="TEST", groupe_nom="Test",
    chambre="AN", legislature="16", profils=profils,
)
pic = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
print(json.dumps({
    "depart": depart, "pic": pic, "nb": len(profils),
    "nb_amendements": fiche["amendements_agreges"]["nb_amendements"],
    "nb_membres": len(fiche["membres"]),
}))
"""


def _liste_lourde_memoire(octets_vises: int, gabarit: dict) -> list:
    """Une liste métier pesant environ `octets_vises` une fois sérialisée.

    Entrées **petites** à dessein : depuis #431 un `amendements[]` publié est un
    mapping à deux clés, et c'est cette forme-là qui gonfle d'un facteur 3 à 10
    en objets Python (× 4,47 mesuré sur les 76 profils du groupe LFI). Une
    fixture bâtie sur de longues chaînes ne gonflerait que d'environ × 1,5 et
    le garde-fou ne séparerait plus rien.
    """
    (cle_id, _), = [(k, v) for k, v in gabarit.items() if k.endswith("_id")]
    unite = len(json.dumps(gabarit, ensure_ascii=False)) + 1
    return [
        dict(gabarit, **{cle_id: f"{gabarit[cle_id]}{i:07d}"})
        for i in range(max(1, octets_vises // unite))
    ]


def _corpus_de_mesure_memoire(tmp_path: Path) -> tuple[Path, int]:
    """Écrit un corpus-fixture de membres et rend le **poids sur disque des
    `amendements[]` que le chargement doit relâcher** — c'est de ce poids, et
    non d'une observation, que le plafond est déduit.

    Les listes réellement parcourues (`votes`, `mandats`) y sont volontairement
    minuscules : elles sont **gardées**, et les compter dans le plafond
    reviendrait à tolérer qu'on garde autre chose.
    """
    dossier = tmp_path / "profiles"
    dossier.mkdir()

    amendements = _liste_lourde_memoire(
        POIDS_AMENDEMENTS_RELACHES,
        {"amendement_id": "an:AMANR5L16PO0000B0000P0D0N", "role_signataire": "cosignataire"},
    )
    poids_relache = NB_PROFILS_FIXTURE_MEMOIRE * len(
        json.dumps(amendements, ensure_ascii=False))

    for i in range(NB_PROFILS_FIXTURE_MEMOIRE):
        profil = _pivot(
            f"an:depute-{i:03d}", f"Députée {i:03d}",
            mandats=[_mandat_electif("2022-06-22")],
            votes=[{"scrutin_id": f"an:16:{n}", "position": "pour"} for n in range(20)],
            tags=["sante"],
            interventions=[{"theme_officiel": "Santé"}],
            amendements=amendements,
        )
        (dossier / f"depute-{i:03d}.pivot.json").write_text(
            json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    return dossier, poids_relache


def test_load_profil_from_file_ne_retient_que_ce_que_la_fiche_lit(tmp_path):
    """Le fond du défaut : un document lu n'est jamais un document gardé.

    Le pic mémoire dépend de la machine ; **ce que la projection retient** n'en
    dépend pas. C'est donc ici que l'invariant est verrouillé, et le test de
    plafond qui suit ne fait que confirmer qu'il a l'effet annoncé.
    """
    profil = _pivot(
        "an:depute", "Députée",
        mandats=[dict(_mandat_electif("2022-06-22"), source_url="https://x",
                      position_dans_hemicycle="12")],
        votes=[{"scrutin_id": "an:16:1", "position": "pour", "numero_scrutin": 1}],
        tags=["sante"],
        interventions=[{"theme_officiel": "Santé", "texte": "x" * 500,
                        "mots_cles": ["climat"]}],
        amendements=[{"amendement_id": "an:X", "role_signataire": "auteur"}],
    )
    profil["identite"] = {"nom_complet": "Députée"}
    profil["identifiants"] = {"hatvp": "https://www.hatvp.fr/fiche/x"}
    profil["couverture"] = {"amendements": {"motif": None}}
    (tmp_path / "depute.pivot.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8")

    charge = load_profil_from_file(tmp_path / "depute.pivot.json")

    for bloc in ("identite", "identifiants", "couverture", "meta",
                 "textes_portes", "chambre", "parti", "groupe", "schema_version"):
        assert bloc not in charge, f"{bloc} n'est lu par aucune ligne de la fiche"
    assert sorted(charge) == sorted(BLOCS_LUS_MEMBRE)

    # Les listes parcourues restent des listes, de même longueur…
    assert len(charge["votes"]) == 1
    assert len(charge["mandats"]) == 1
    assert len(charge["interventions"]) == 1
    # … mais leurs entrées ne portent que les clés lues.
    assert charge["votes"][0] == {"scrutin_id": "an:16:1", "position": "pour"}
    assert "source_url" not in charge["mandats"][0]
    assert "texte" not in charge["interventions"][0]
    assert charge["interventions"][0]["theme_officiel"] == "Santé"
    # `sources` est recopié tel quel dans la fiche publiée : jamais projeté.
    assert charge["sources"] == profil["sources"]
    # `amendements` est réduit à sa contribution, pas à un cardinal muet.
    assert isinstance(charge["amendements"], ContributionAmendements)
    assert len(charge["amendements"]) == 1


def test_l_agregat_amendements_est_le_meme_sur_la_liste_et_sur_sa_contribution():
    """Une contribution est une somme partielle : agréger membre par membre puis
    sommer rend les mêmes compteurs que parcourir les listes entières."""
    amendements_a = [
        {"amendement_id": None, "amendement_non_resolu": {"sort": "adopte", "type_deposant": "depute"}},
        {"amendement_id": None, "amendement_non_resolu": {"sort": "rejete", "type_deposant": "depute"}},
    ]
    amendements_b = [
        {"amendement_id": None, "amendement_non_resolu": {"sort": "irrecevable", "type_deposant": "gouvernement"}},
        {"amendement_id": None},
    ]
    entiers = [_pivot("an:a", "A", amendements=amendements_a),
               _pivot("an:b", "B", amendements=amendements_b)]
    reduits = [
        dict(p, amendements=contribution_amendements(p["amendements"]))
        for p in entiers
    ]

    assert _aggregate_amendements(reduits) == _aggregate_amendements(entiers)
    total, non_resolus = _aggregate_amendements(reduits)
    assert total["nb_amendements"] == 3
    assert non_resolus == 1
    assert total["taux_adoption"] == round(1 / 3, 4)


@pytest.mark.skipif(sys.platform.startswith("win"), reason="`resource` est POSIX")
def test_le_pic_memoire_d_une_fiche_de_groupe_reste_sous_le_plafond_declare(tmp_path):
    """La construction d'une fiche ne doit pas croître de plus que le poids
    **sur disque** des `amendements[]` qu'elle est censée relâcher.

    D'où vient le plafond
    ---------------------
    Il n'est pas relevé sur une exécution puis arrondi — ce serait un plafond
    qui suit la dérive qu'il doit signaler. C'est une **règle** : la croissance
    mémoire doit rester sous le poids en octets, sur disque, des entrées lues et
    non gardées. La désérialisation JSON ne **réduit** jamais : si la fiche
    croît de moins que le texte qu'elle a lu, elle ne peut pas le détenir.

    Ce que le test ne prouve pas
    ----------------------------
    Ni la vitesse, ni le pic absolu d'un vrai groupe — mesuré à 82,3 Mio pour
    les 76 profils de la fiche LFI, contre 0,9 à 1,1 Gio avant, et nulle part en CI :
    `pivot_data` est hors du sparse-checkout de `tests.yml` (#473).
    """
    dossier, poids_relache = _corpus_de_mesure_memoire(tmp_path)
    assert poids_relache >= PLANCHER_POIDS_RELACHE, (
        f"corpus-fixture trop léger ({poids_relache / 1024**2:.0f} Mio "
        f"d'amendements à relâcher) : sous ce plancher le plafond qu'il déduit "
        f"ne prouve plus rien. Regonfler les fixtures, jamais desserrer le "
        f"plancher.")

    pilote = tmp_path / "pilote_memoire.py"
    pilote.write_text(_PILOTE_MEMOIRE, encoding="utf-8")
    acheve = subprocess.run(
        [sys.executable, str(pilote),
         str(Path(__file__).resolve().parents[1]), str(dossier)],
        capture_output=True, text=True, timeout=300,
    )
    assert acheve.returncode == 0, (
        f"la fiche n'a pas été construite (code {acheve.returncode}) — un 137 "
        f"est un OOM, le défaut même de #635 :\n{acheve.stderr[-2000:]}")
    mesure = json.loads(acheve.stdout.strip().splitlines()[-1])

    assert mesure["nb"] == NB_PROFILS_FIXTURE_MEMOIRE
    assert mesure["nb_membres"] == NB_PROFILS_FIXTURE_MEMOIRE
    assert mesure["nb_amendements"] == 0, (
        "sans index partagé et sans enregistrement autoporté, aucune entrée "
        "n'est résolue — ce que la fiche compte, ce sont les non-résolues")

    # `ru_maxrss` est en Kio sous Linux, en octets sous macOS.
    facteur = 1 if sys.platform == "darwin" else 1024
    croissance = (mesure["pic"] - mesure["depart"]) * facteur
    assert croissance < poids_relache, (
        f"la fiche a grossi de {croissance / 1024**2:.1f} Mio en lisant "
        f"{NB_PROFILS_FIXTURE_MEMOIRE} profils dont {poids_relache / 1024**2:.0f} Mio "
        f"d'amendements qu'elle ne doit pas garder. Au-dessus de ce plafond elle "
        f"en retient une partie : c'est le défaut de #635, qui coûtait près "
        f"d'un Gio sur la seule fiche LFI.")


# ---------------------------------------------------------------------------
# #821 — un agrégat d'amendements ne compte que la période de la fiche
# ---------------------------------------------------------------------------


def _entree_amendement(uid, sort="rejeté", type_deposant="depute"):
    return {
        "amendement_id": f"an:{uid}",
        "role_signataire": "auteur_principal",
        "amendement_non_resolu": {
            "sort": sort, "type_deposant": type_deposant,
            "texte_vise": "T", "date": "2023-01-01", "numero": "1",
            "base_juridique_irrecevabilite": None, "premier_signataire": None,
            "co_signataires": [], "source_url": None,
        },
    }


def test_un_amendement_dune_autre_legislature_nentre_pas_dans_lagregat():
    """Le filtre de #403, transposé aux amendements.

    Mesuré avant correctif : `LR-16` publiait 159 274 amendements dont
    **32 277 seulement** déposés sous la XVIe. 20 501 venaient de la XVIIe,
    c'est-à-dire d'après la dissolution du 9 juin 2024, sous un groupe qui
    n'existait plus.
    """
    amendements = [
        _entree_amendement("AMANR5L16PO420120B0001P0D1N000001"),
        _entree_amendement("AMANR5L16PO420120B0001P0D1N000002"),
        _entree_amendement("AMANR5L17PO838901BTC3051P0D1N000003"),
        _entree_amendement("AMANR5L15PO717460B0002P0D1N000004"),
    ]
    contribution = group_profile.contribution_amendements(
        amendements, None, None, legislature="16"
    )
    assert contribution.total["nb_amendements"] == 2
    assert contribution.hors_periode == 2
    assert contribution.sans_legislature == 0


def test_sans_legislature_demandee_rien_nest_ecarte():
    """Le filtre ne s'arme que si l'appelant nomme une législature : un profil
    lu isolément garde tout."""
    amendements = [
        _entree_amendement("AMANR5L16PO420120B0001P0D1N000001"),
        _entree_amendement("AMANR5L17PO838901BTC3051P0D1N000003"),
    ]
    contribution = group_profile.contribution_amendements(amendements)
    assert contribution.total["nb_amendements"] == 2
    assert contribution.hors_periode == 0


def test_un_identifiant_sans_legislature_est_conserve_et_compte():
    """Rien ne prouve qu'il soit hors période. L'écarter ferait passer une
    ignorance pour un fait (§2 règle 5) ; il est retenu, et déclaré."""
    amendements = [
        _entree_amendement("AMANR5L16PO420120B0001P0D1N000001"),
        _entree_amendement("FORME-INCONNUE-0001"),
    ]
    contribution = group_profile.contribution_amendements(
        amendements, None, None, legislature="16"
    )
    assert contribution.total["nb_amendements"] == 2, "l'entrée douteuse est retenue"
    assert contribution.sans_legislature == 1
    assert contribution.hors_periode == 0


def test_les_exclusions_se_publient_sous_le_nom_de_signatures():
    """Une entrée d'`amendements[]` est une SIGNATURE, pas un amendement.

    657 996 signatures écartées sur `LR-16` pour 126 997 amendements distincts :
    les nommer « amendements » reproduirait la confusion que #643 a corrigée
    (§6 — les signatures se publient sous leur nom).
    """
    agreges, _ = group_profile._aggregate_amendements([
        {"amendements": group_profile.contribution_amendements(
            [_entree_amendement("AMANR5L17PO838901BTC3051P0D1N000003")],
            None, None, legislature="16",
        )},
    ])
    assert agreges["nb_signatures_hors_periode_ecartees"] == 1
    assert "nb_hors_periode_ecartes" not in agreges


# ---------------------------------------------------------------------------
# #808 — l'étiquette nomme le critère, plus un événement
# ---------------------------------------------------------------------------

def test_l_origine_nomme_la_derniere_appartenance_et_non_la_cloture():
    """`NG-15` s'arrête au 11/09/2018 ; la XVe se clôt le 21/06/2022.

    L'ancienne valeur annonçait un événement que deux fiches sur douze n'ont
    jamais connu — 3 ans 9 mois d'écart pour celle-ci. Le chiffre était juste,
    la phrase qui l'accompagnait ne l'était pas (§2 règle 2).
    """
    from group_profile import _deriver_date_reference

    membres = [
        {"debut_dans_groupe": "2017-06-27", "fin_dans_groupe": "2018-09-11"},
        {"debut_dans_groupe": "2017-06-27", "fin_dans_groupe": "2018-06-30"},
    ]
    bloc = _deriver_date_reference(membres, "2026-09-10T00:00:00+0000")
    assert bloc == {"date": "2018-09-11", "origine": "derniere_appartenance_close"}


def test_une_appartenance_ouverte_garde_la_date_de_generation():
    from group_profile import _deriver_date_reference

    membres = [
        {"debut_dans_groupe": "2024-07-19", "fin_dans_groupe": None},
        {"debut_dans_groupe": "2024-07-19", "fin_dans_groupe": "2025-01-10"},
    ]
    bloc = _deriver_date_reference(membres, "2026-09-10T00:00:00+0000")
    assert bloc["origine"] == "generation"


def test_l_ancienne_valeur_reste_valide_a_la_lecture():
    """Les 14 fiches qui la portent doivent valider jusqu'à leur régénération :
    sans ce repli, le portail échouerait sur des fichiers que personne n'a
    touchés."""
    from schema_groupe import ORIGINES_DATE_REFERENCE

    assert "cloture_legislature" in ORIGINES_DATE_REFERENCE
    assert "derniere_appartenance_close" in ORIGINES_DATE_REFERENCE


# ---------------------------------------------------------------------------
# #809 — l'appartenance n'est plus une enveloppe
# ---------------------------------------------------------------------------

def test_les_periodes_du_roster_atteignent_la_fiche():
    """Le cas Dussopt : 571 jours au gouvernement, masqués par l'enveloppe."""
    table = appartenances_depuis_roster([{
        "slug": "olivier-dussopt",
        "mandat_debut": "2022-06-29", "mandat_fin": "2024-06-09",
        "mandat_periodes": [
            {"debut": "2022-06-29", "fin": "2022-07-20"},
            {"debut": "2024-02-11", "fin": "2024-06-09"},
        ],
    }])
    assert len(table["olivier-dussopt"]["periodes"]) == 2


def test_un_membre_absent_a_la_date_de_reference_n_est_plus_compte_present():
    """L'enveloppe le disait présent ; les périodes disent qu'il ne l'était pas.

    Aucun compteur publié n'était faux au 09/09/2026 — vérifié sur les 18
    groupes — mais par coïncidence de dates, les dates de référence ne tombant
    dans aucun trou. Un défaut qui ne se voit pas parce que les dates s'y
    prêtent reste un défaut.
    """
    from group_profile import _appartenance_couvre

    membre = {
        "debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09",
        "periodes": [
            {"debut": "2022-06-29", "fin": "2022-07-20"},
            {"debut": "2024-02-11", "fin": "2024-06-09"},
        ],
    }
    assert _appartenance_couvre(membre, "2023-06-01") is False, "il était ministre"
    assert _appartenance_couvre(membre, "2022-07-01") is True
    assert _appartenance_couvre(membre, "2024-06-09") is True


def test_sans_periodes_l_enveloppe_reste_le_repli():
    """Les fiches publiées avant #809 ne portent pas la clé : exiger celle-ci
    ferait sortir des compteurs à zéro sur des données qui n'ont pas changé."""
    from group_profile import _appartenance_couvre

    membre = {"debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09"}
    assert _appartenance_couvre(membre, "2023-06-01") is True


def test_une_periode_ouverte_couvre_jusqu_a_aujourd_hui():
    from group_profile import _appartenance_couvre

    membre = {
        "debut_dans_groupe": "2024-07-19", "fin_dans_groupe": None,
        "periodes": [{"debut": "2024-07-19", "fin": None}],
    }
    assert _appartenance_couvre(membre, "2026-09-10") is True


def test_les_periodes_ne_peuvent_pas_contredire_l_enveloppe():
    """Une contradiction entre deux champs du même membre ne se rattrape nulle
    part en aval : c'est le seul contenu d'entrée que le schéma valide."""
    from schema_groupe import make_empty_profil_groupe, validate_profil_groupe

    profil = make_empty_profil_groupe("AN:SOC:16", "SOC", "Socialistes", "AN", "16")
    profil["membres"] = [{
        "membre_id": "alice",
        "debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09",
        "periodes": [{"debut": "2023-01-01", "fin": "2024-06-09"}],
    }]
    erreurs = validate_profil_groupe(profil)
    assert any("l'enveloppe le 2022-06-29" in e for e in erreurs)


def test_une_liste_de_periodes_vide_est_refusee():
    """Elle dirait « aucune appartenance connue » sur un membre qui en a une ;
    c'est l'ABSENCE de clé qui dit « non collectées » (§2 règle 5)."""
    from schema_groupe import make_empty_profil_groupe, validate_profil_groupe

    profil = make_empty_profil_groupe("AN:SOC:16", "SOC", "Socialistes", "AN", "16")
    profil["membres"] = [{
        "membre_id": "alice",
        "debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09",
        "periodes": [],
    }]
    assert any("liste non vide" in e for e in validate_profil_groupe(profil))


def test_deux_periodes_coherentes_passent():
    from schema_groupe import make_empty_profil_groupe, validate_profil_groupe

    profil = make_empty_profil_groupe("AN:REN:16", "REN", "Renaissance", "AN", "16")
    profil["membres"] = [{
        "membre_id": "olivier-dussopt",
        "debut_dans_groupe": "2022-06-29", "fin_dans_groupe": "2024-06-09",
        "periodes": [
            {"debut": "2022-06-29", "fin": "2022-07-20"},
            {"debut": "2024-02-11", "fin": "2024-06-09"},
        ],
    }]
    assert validate_profil_groupe(profil) == []
