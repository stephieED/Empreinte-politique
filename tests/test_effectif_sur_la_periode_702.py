"""L'amplitude d'effectif d'un groupe sur la période qu'il décrit (#702).

Une fiche de groupe publiait un effectif **à une date** pour décrire deux ans :
`effectif.min_historique` et `max_historique` valaient `null` sur les 7 fiches
publiées, et le code le déclarait (« non calculé »). Ce lot les remplit, chacun
avec la date où la borne est atteinte.

Les fixtures sont des **réductions de la structure réelle**, pas des cas
inventés : la fiche `groupe-AN-REN-16` publiée au 01/09/2026 porte 193 entrées
`membres[]` pour 169 membres à la clôture, et sa courbe descend à 170 le
2023-08-21 — le jour où cinq député⋅es devenu⋅es ministres ont quitté le groupe
et où leurs suppléant⋅es n'étaient pas encore entré⋅es (arrivée le 2023-08-22).
`_fixture_remaniement` reproduit cette forme au douzième, avec les mêmes dates.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from group_profile import (  # noqa: E402
    MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE,
    MOTIF_AMPLITUDE_FENETRE_NON_BORNEE,
    _dates_de_reevaluation,
    _effectif_sur_la_periode,
    _fenetre_de_la_fiche,
    build_groupe_profile,
)
from schema_groupe import (  # noqa: E402
    valeur_borne_effectif,
    validate_profil_groupe,
)

CLOTURE_XVI = "2024-06-09"
OUVERTURE_XVI = "2022-06-29"


# ---------------------------------------------------------------------------
# Fixtures : la structure réelle, réduite
# ---------------------------------------------------------------------------

def _membre(membre_id: str, debut, fin) -> dict:
    """Une entrée `membres[]` réduite à ce que le balayage lit."""
    return {
        "membre_id": membre_id,
        "nom": membre_id,
        "debut_dans_groupe": debut,
        "fin_dans_groupe": fin,
    }


def _fixture_remaniement() -> list[dict]:
    """La forme de `groupe-AN-REN-16` au douzième, aux dates réelles.

    8 membres présents du premier au dernier jour, 2 partis le 2023-08-20
    (entrée au gouvernement), 2 entrés le 2023-08-22 (suppléant⋅es). 12 entrées
    `membres[]`, jamais plus de 10 personnes à la fois.
    """
    membres = [_membre(f"stable-{i}", OUVERTURE_XVI, CLOTURE_XVI) for i in range(8)]
    membres += [_membre(f"ministre-{i}", OUVERTURE_XVI, "2023-08-20") for i in range(2)]
    membres += [_membre(f"suppleant-{i}", "2023-08-22", CLOTURE_XVI) for i in range(2)]
    return membres


def _pivot(id_: str) -> dict:
    """Profil pivot v1 minimal — `build_groupe_profile` n'en lit ici que `id`."""
    return {
        "schema_version": "1",
        "id": id_,
        "nom": id_,
        "chambre": "AN",
        "parti": None,
        "groupe": "Renaissance",
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": [],
        "amendements": [],
        "tags_thematiques": [],
        "meta": {"schema_version": "1", "genere_le": "2026-09-01T00:00:00+0000",
                 "licence_donnees": "", "warnings": []},
    }


# ---------------------------------------------------------------------------
# La règle de calcul
# ---------------------------------------------------------------------------

def test_les_deux_bornes_portent_leur_date():
    """Un minimum sans sa date est un nombre sans fait."""
    mini, maxi, motif = _effectif_sur_la_periode(
        _fixture_remaniement(), OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI
    )
    assert motif is None
    assert mini == {"valeur": 8, "date": "2023-08-21"}
    assert maxi == {"valeur": 10, "date": OUVERTURE_XVI}


def test_l_effectif_baisse_le_LENDEMAIN_d_une_sortie():
    """La borne de fin est inclusive (`_appartenance_couvre`) : un membre dont
    l'appartenance s'achève le 20 est encore compté ce jour-là."""
    membres = _fixture_remaniement()
    dates = _dates_de_reevaluation(membres, (OUVERTURE_XVI, CLOTURE_XVI))
    assert "2023-08-21" in dates
    assert "2023-08-20" not in dates
    mini, _, _ = _effectif_sur_la_periode(membres, OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI)
    assert mini["date"] == "2023-08-21"


def test_a_valeur_egale_la_premiere_date_est_retenue():
    """L'effectif remonte à 10 le 2023-08-22, mais le maximum est daté du
    premier jour où il vaut 10 : sans convention écrite, deux runs sur la même
    donnée dateraient différemment la même valeur."""
    _, maxi, _ = _effectif_sur_la_periode(
        _fixture_remaniement(), OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI
    )
    assert maxi["valeur"] == 10
    assert maxi["date"] == OUVERTURE_XVI


def test_un_groupe_sans_mouvement_publie_une_amplitude_plate():
    """`groupe-AN-SOC-16` : 31 entrées, 31 membres du premier au dernier jour.
    Une amplitude nulle est un fait, pas une absence de donnée."""
    membres = [_membre(f"m-{i}", OUVERTURE_XVI, CLOTURE_XVI) for i in range(31)]
    mini, maxi, motif = _effectif_sur_la_periode(
        membres, OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI
    )
    assert motif is None
    assert mini == maxi == {"valeur": 31, "date": OUVERTURE_XVI}


def test_aucune_date_hors_de_la_fenetre_n_est_evaluee():
    """La fiche décrit sa période, jamais au-delà : le lendemain de la clôture
    n'est pas une date d'évaluation, et une entrée postérieure n'existe pas."""
    membres = _fixture_remaniement() + [_membre("apres", "2024-07-18", None)]
    dates = _dates_de_reevaluation(membres, (OUVERTURE_XVI, CLOTURE_XVI))
    assert max(dates) <= CLOTURE_XVI
    assert "2024-06-10" not in dates
    assert "2024-07-18" not in dates


def test_le_maximum_ne_depasse_jamais_le_nombre_d_entrees():
    """193 entrées `membres[]` pour 175 personnes au plus : l'écart est la
    rotation, jamais un effectif."""
    membres = _fixture_remaniement()
    _, maxi, _ = _effectif_sur_la_periode(
        membres, OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI
    )
    assert maxi["valeur"] < len(membres)


# ---------------------------------------------------------------------------
# Ce que le calcul ne peut pas établir
# ---------------------------------------------------------------------------

def test_une_seule_entree_sans_date_de_debut_interdit_la_publication():
    """Seuil 0. Ce membre n'est comptable à aucune date (#653) : les bornes
    obtenues sans lui sont des bornes inférieures, et une borne inférieure
    publiée sous le nom « minimum » est un chiffre faux (§2 règle 5)."""
    membres = _fixture_remaniement() + [_membre("sans-date", None, None)]
    mini, maxi, motif = _effectif_sur_la_periode(
        membres, OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI
    )
    assert (mini, maxi) == (None, None)
    assert motif == MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE


def test_les_fiches_senat_gelees_restent_nulles():
    """`groupe-Senat-LR` publie 15 entrées dont 14 sans date d'appartenance, et
    une période ouverte sans `date_reference` (#516). Elle ne sera pas
    régénérée ; la règle la refuse de toute façon."""
    membres = [_membre("date", "2004-09-26", None)]
    membres += [_membre(f"sans-{i}", None, None) for i in range(14)]
    mini, maxi, motif = _effectif_sur_la_periode(membres, "2004-09-26", None, None)
    assert (mini, maxi) == (None, None)
    assert motif == MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE


def test_une_liste_de_membres_vide_ne_publie_pas_zero():
    """Sans membre daté il n'y a pas de `periode.debut`, donc pas de fenêtre :
    le motif est celui de la fenêtre, pas « 0 des 0 entrées ne sont datées »."""
    mini, maxi, motif = _effectif_sur_la_periode([], None, None, None)
    assert (mini, maxi) == (None, None)
    assert motif == MOTIF_AMPLITUDE_FENETRE_NON_BORNEE


def test_un_depart_suivi_d_un_retour_est_invisible_et_c_est_dit():
    """`membres[]` ne porte qu'un intervalle par membre : `an_roster` recolle
    les périodes successives (#526), `None` l'emportant sur une fin. Un membre
    parti puis revenu est donc publié présent en continu, et l'amplitude ne
    voit pas son absence. Le test épingle la limite plutôt que de la masquer."""
    recolle = [_membre("aller-retour", OUVERTURE_XVI, CLOTURE_XVI)]
    recolle += [_membre(f"stable-{i}", OUVERTURE_XVI, CLOTURE_XVI) for i in range(9)]
    mini, _, _ = _effectif_sur_la_periode(recolle, OUVERTURE_XVI, CLOTURE_XVI, CLOTURE_XVI)
    assert mini["valeur"] == 10  # et non 9 : l'absence n'est pas dans la donnée


# ---------------------------------------------------------------------------
# La fenêtre
# ---------------------------------------------------------------------------

def test_la_fenetre_est_celle_de_la_fiche():
    assert _fenetre_de_la_fiche(OUVERTURE_XVI, CLOTURE_XVI, "2026-09-01") == (
        OUVERTURE_XVI, CLOTURE_XVI,
    )


def test_une_periode_ouverte_est_bornee_par_la_date_de_reference():
    """Tant qu'une appartenance reste ouverte, `periode.fin` est `null` et la
    seule borne haute qui ait un sens est la date de génération (#653)."""
    assert _fenetre_de_la_fiche(OUVERTURE_XVI, None, "2026-09-01") == (
        OUVERTURE_XVI, "2026-09-01",
    )


def test_sans_borne_haute_la_fenetre_n_existe_pas():
    """Une fenêtre non bornée couvrirait toutes les dates — l'inverse exact de
    la règle appliquée à une borne d'appartenance absente."""
    assert _fenetre_de_la_fiche(OUVERTURE_XVI, None, None) is None
    assert _fenetre_de_la_fiche(None, CLOTURE_XVI, CLOTURE_XVI) is None


def test_une_fenetre_a_l_envers_est_refusee():
    assert _fenetre_de_la_fiche(CLOTURE_XVI, OUVERTURE_XVI, None) is None


def test_quand_les_deux_motifs_sont_vrais_c_est_le_plus_instruit_qui_sort():
    """`groupe-Senat-LR` cumule les deux : période ouverte sans `date_reference`
    ET 14 entrées non datées. Le motif rendu est celui qui apprend un nombre au
    lecteur, pas la borne manquante qui en découle."""
    membres = [_membre("date", "2004-09-26", None), _membre("sans", None, None)]
    _, _, motif = _effectif_sur_la_periode(membres, "2004-09-26", None, None)
    assert motif == MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE


def test_le_motif_de_fenetre_non_bornee_est_distinct():
    membres = [_membre(f"m-{i}", OUVERTURE_XVI, None) for i in range(3)]
    mini, maxi, motif = _effectif_sur_la_periode(membres, OUVERTURE_XVI, None, None)
    assert (mini, maxi) == (None, None)
    assert motif == MOTIF_AMPLITUDE_FENETRE_NON_BORNEE


# ---------------------------------------------------------------------------
# Bout en bout : la fiche publiée
# ---------------------------------------------------------------------------

def _fiche_remaniement() -> dict:
    membres = _fixture_remaniement()
    return build_groupe_profile(
        "AN:REN", "REN", "Renaissance", "AN", "16",
        [_pivot(m["membre_id"]) for m in membres],
        appartenances={
            m["membre_id"]: {"debut": m["debut_dans_groupe"], "fin": m["fin_dans_groupe"]}
            for m in membres
        },
    )


def test_la_fiche_publie_l_amplitude_et_reste_valide():
    fiche = _fiche_remaniement()
    assert fiche["effectif"]["min_historique"] == {"valeur": 8, "date": "2023-08-21"}
    assert fiche["effectif"]["max_historique"] == {"valeur": 10, "date": OUVERTURE_XVI}
    assert validate_profil_groupe(fiche) == []


def test_les_bornes_encadrent_l_effectif_a_la_date_de_reference():
    """Les trois compteurs sortent du même balayage : les voir se contredire
    signifierait que l'un d'eux ne lit pas `membres[]`."""
    fiche = _fiche_remaniement()
    effectif = fiche["effectif"]
    mini = effectif["min_historique"]["valeur"]
    maxi = effectif["max_historique"]["valeur"]
    assert mini <= effectif["a_la_date_de_reference"] <= maxi


def test_la_fiche_nomme_sa_fenetre_et_sa_limite():
    warnings = _fiche_remaniement()["meta"]["warnings"]
    avis = next(w for w in warnings if w.startswith("effectif_sur_la_periode :"))
    assert OUVERTURE_XVI in avis and CLOTURE_XVI in avis
    assert "un départ suivi d'un retour" in avis


def test_sans_roster_la_fiche_publie_null_et_dit_pourquoi():
    """Aucune appartenance datée : `null` sur les deux bornes, et le motif en
    clair — un `null` muet dirait « on n'a pas calculé »."""
    fiche = build_groupe_profile(
        "AN:REN", "REN", "Renaissance", "AN", "16", [_pivot("solo")],
    )
    assert fiche["effectif"]["min_historique"] is None
    assert fiche["effectif"]["max_historique"] is None
    avis = next(
        w for w in fiche["meta"]["warnings"] if w.startswith("effectif_sur_la_periode :")
    )
    assert "1 des 1 entrées" in avis
    assert validate_profil_groupe(fiche) == []


# ---------------------------------------------------------------------------
# Le schéma : deux formes lues, une seule produite
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("borne", "attendu"), [
    (None, None),
    (167, 167),                                   # forme héritée
    ({"valeur": 167, "date": "2024-03-09"}, 167),  # forme du lot
    ({"valeur": None, "date": None}, None),
    (True, None),
    ("167", None),
])
def test_les_deux_formes_de_borne_sont_lues(borne, attendu):
    """Exiger la forme objet ferait cesser de lire les 2 fiches gelées."""
    assert valeur_borne_effectif(borne) == attendu


def _fiche_avec_effectif(effectif: dict) -> dict:
    fiche = _fiche_remaniement()
    fiche["effectif"] = effectif
    return fiche


def test_une_borne_sans_date_est_une_erreur_de_schema():
    erreurs = validate_profil_groupe(_fiche_avec_effectif({
        "a_la_date_de_reference": 10,
        "min_historique": {"valeur": 8},
        "max_historique": {"valeur": 10, "date": OUVERTURE_XVI},
    }))
    assert any("min_historique.date" in e for e in erreurs)


def test_une_borne_sans_valeur_est_une_erreur_de_schema():
    erreurs = validate_profil_groupe(_fiche_avec_effectif({
        "a_la_date_de_reference": 10,
        "min_historique": {"date": "2023-08-21"},
        "max_historique": None,
    }))
    assert any("min_historique.valeur" in e for e in erreurs)


def test_un_maximum_inferieur_a_son_minimum_est_refuse():
    erreurs = validate_profil_groupe(_fiche_avec_effectif({
        "a_la_date_de_reference": 10,
        "min_historique": {"valeur": 10, "date": OUVERTURE_XVI},
        "max_historique": {"valeur": 8, "date": "2023-08-21"},
    }))
    assert any("supérieur" in e for e in erreurs)


def test_la_forme_publiee_avant_le_lot_reste_valide():
    """`null` (les 7 fiches) et l'entier nu (aucune, mais le schéma l'annonçait)
    passent la validation : une migration ne se paie pas en cassant du publié."""
    for borne in (None, 61):
        assert validate_profil_groupe(_fiche_avec_effectif({
            "a_la_date_de_reference": 61,
            "min_historique": borne,
            "max_historique": borne,
        })) == []
