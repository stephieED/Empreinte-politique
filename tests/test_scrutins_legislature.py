"""Résolution de `legislature` sur les votes (#432).

`numero_scrutin` repart à 1 à chaque législature (AGENTS.md §5) : la clé de
normalisation des votes est `(legislature, numero_scrutin)`, or 22,5 % des votes
collectés ne portent aucune législature. Deux mécanismes la rétablissent, de
natures différentes et donc jamais confondus :

1. **jointure sur un jumeau étiqueté** — la donnée existe déjà, étiquetée,
   ailleurs dans le corpus : c'est une résolution, pas une inférence ;
2. **calendrier des législatures** — une dérivation, tracée comme telle.

Et un troisième comportement, qui est le vrai sujet de la moitié des tests
ci-dessous : **tout ce qu'aucun des deux ne résout échoue bruyamment**. Aucune
valeur par défaut, aucun rattachement au voisin le plus proche (AGENTS.md §2.5).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from couverture_dossiers import LEGISLATURES_DEBUT
from scrutins_legislature import (
    LEGISLATURES_AN,
    MOTIF_DATE_ABSENTE,
    MOTIF_DATE_ILLISIBLE,
    MOTIF_HORS_CALENDRIER,
    MOTIF_JUMEAU_CONTRADICTOIRE,
    MOTIF_LEGISLATURE_INCONNUE,
    PROVENANCE_CALENDRIER,
    PROVENANCE_COLLECTEE,
    PROVENANCE_JUMEAU,
    PROVENANCES_CONNUES,
    CleScrutin,
    LegislatureIrresoluble,
    Resolution,
    legislature_du_calendrier,
    provenance_par_occurrence,
    resoudre_legislatures,
)


# ── Mécanisme 1 : jointure sur un jumeau étiqueté ────────────────────────────

def test_jumeau_etiquete_resout_une_occurrence_sans_legislature():
    """Le cœur du mécanisme 1 : la donnée n'est pas devinée, elle est reprise
    d'une occurrence qui la portait — même `(numero_scrutin, date)`."""
    resolutions, echecs = resoudre_legislatures([
        ("4084", "2024-06-07", "16"),   # occurrence étiquetée (autre profil)
        ("4084", "2024-06-07", None),   # occurrence à résoudre
    ])

    assert echecs == []
    assert resolutions[CleScrutin("4084", "2024-06-07")] == Resolution("16", PROVENANCE_COLLECTEE)


def test_jumeau_ne_deborde_pas_sur_un_numero_d_une_autre_date():
    """`numero_scrutin` repart à 1 à chaque législature : la jointure porte sur
    le couple, jamais sur le numéro seul. Sans quoi le scrutin n°1 de la XVI
    étiquetterait celui de la XVII."""
    resolutions, echecs = resoudre_legislatures([
        ("1", "2022-07-11", "16"),
        ("1", "2024-10-08", None),
    ])

    assert echecs == []
    assert resolutions[CleScrutin("1", "2022-07-11")].legislature == "16"
    # Résolu par le calendrier, pas par le jumeau du même numéro.
    autre = resolutions[CleScrutin("1", "2024-10-08")]
    assert autre == Resolution("17", PROVENANCE_CALENDRIER)


def test_jumeaux_contradictoires_echouent_au_lieu_de_choisir():
    """Deux étiquettes différentes pour le même scrutin : il n'y a pas de
    bonne façon d'en préférer une. Mesuré : 0 cas aujourd'hui — le test
    verrouille le comportement pour le jour où il s'en présente un."""
    resolutions, echecs = resoudre_legislatures([
        ("4084", "2024-06-07", "16"),
        ("4084", "2024-06-07", "17"),
        ("4084", "2024-06-07", None),
    ])

    assert CleScrutin("4084", "2024-06-07") not in resolutions
    assert [e.motif for e in echecs] == [MOTIF_JUMEAU_CONTRADICTOIRE]
    assert "'16'" in str(echecs[0].detail) or "16" in echecs[0].detail


def test_legislature_collectee_inconnue_du_calendrier_echoue():
    """Soit la collecte a produit une valeur aberrante, soit une législature a
    commencé et `LEGISLATURES_AN` n'a pas suivi. Les deux demandent une décision,
    aucune ne se rattrape par un repli."""
    resolutions, echecs = resoudre_legislatures([("12", "2030-01-15", "18")])

    assert resolutions == {}
    assert echecs[0].motif == MOTIF_LEGISLATURE_INCONNUE


# ── Mécanisme 2 : calendrier ─────────────────────────────────────────────────

@pytest.mark.parametrize("date,attendu", [
    ("2012-06-20", "14"),   # borne basse incluse
    ("2017-06-20", "14"),   # borne haute incluse
    ("2017-06-21", "15"),
    ("2022-06-21", "15"),
    ("2022-06-22", "16"),
    ("2024-06-09", "16"),   # jour de la dissolution, encore dans la XVI
    ("2024-07-18", "17"),
    ("2026-07-21", "17"),   # législature en cours : pas de borne haute
])
def test_calendrier_bornes_incluses(date, attendu):
    assert legislature_du_calendrier(date) == attendu


@pytest.mark.parametrize("date", ["2024-06-10", "2024-07-01", "2024-07-17"])
def test_entre_deux_dissolution_ouverture_n_appartient_a_aucune_legislature(date):
    """Les cinq semaines entre la dissolution du 09/06/2024 et l'ouverture du
    18/07/2024 ne sont couvertes par aucune législature. Rattacher au voisin le
    plus proche inventerait une donnée."""
    assert legislature_du_calendrier(date) is None

    resolutions, echecs = resoudre_legislatures([("999", date, None)])
    assert resolutions == {}
    assert echecs[0].motif == MOTIF_HORS_CALENDRIER


def test_date_anterieure_au_calendrier_echoue():
    assert legislature_du_calendrier("2011-01-01") is None
    _, echecs = resoudre_legislatures([("5", "2011-01-01", None)])
    assert echecs[0].motif == MOTIF_HORS_CALENDRIER


@pytest.mark.parametrize("date", [None, "", "07/11/2022", "2022-13-45", "hier"])
def test_date_absente_ou_illisible_ne_recoit_jamais_de_valeur(date):
    """Une date malformée comparée en ISO donnerait un résultat au petit
    bonheur : elle est rejetée avant toute comparaison."""
    assert legislature_du_calendrier(date) is None

    resolutions, echecs = resoudre_legislatures([("5", date, None)])
    assert resolutions == {}
    assert echecs[0].motif in (MOTIF_DATE_ABSENTE, MOTIF_DATE_ILLISIBLE)


def test_derivation_calendaire_est_tracee_comme_telle():
    """« À tracer explicitement comme dérivé, pas comme collecté. »"""
    resolutions, echecs = resoudre_legislatures([("632", "2022-11-25", None)])

    assert echecs == []
    assert resolutions[CleScrutin("632", "2022-11-25")] == Resolution("16", PROVENANCE_CALENDRIER)


# ── Les deux mécanismes ensemble, dans l'ordre ───────────────────────────────

def test_le_jumeau_prime_sur_le_calendrier():
    """Ordre voulu : une donnée étiquetée existante l'emporte toujours sur une
    dérivation. Les deux tomberaient ici sur « 16 » ; c'est la PROVENANCE qui
    doit refléter laquelle a servi."""
    resolutions, _ = resoudre_legislatures([
        ("744", "2022-12-11", "16"),
        ("744", "2022-12-11", None),
    ])

    assert resolutions[CleScrutin("744", "2022-12-11")].provenance == PROVENANCE_COLLECTEE


def test_resolution_est_globale_au_corpus_pas_par_profil():
    """Un profil est soit entièrement sur l'ancien chemin de collecte, soit
    entièrement sur le nouveau : le jumeau étiqueté vit toujours dans un AUTRE
    fichier. Une résolution profil par profil ne trouverait donc jamais rien."""
    profil_ancien = [("4084", "2024-06-07", None), ("4085", "2024-06-07", None)]
    profil_recent = [("4084", "2024-06-07", "16"), ("4085", "2024-06-07", "16")]

    seuls, _ = resoudre_legislatures(profil_ancien)
    assert all(r.provenance == PROVENANCE_CALENDRIER for r in seuls.values())

    ensemble, _ = resoudre_legislatures(profil_ancien + profil_recent)
    assert all(r.provenance == PROVENANCE_COLLECTEE for r in ensemble.values())


def test_un_echec_ne_contamine_pas_les_autres_scrutins():
    """Rien n'est résolu partiellement : la clé en échec est absente du
    dictionnaire, les autres restent résolues."""
    resolutions, echecs = resoudre_legislatures([
        ("4084", "2024-06-07", "16"),
        ("999", "2024-07-01", None),      # entre-deux : irrésoluble
    ])

    assert CleScrutin("4084", "2024-06-07") in resolutions
    assert CleScrutin("999", "2024-07-01") not in resolutions
    assert len(echecs) == 1


def test_corpus_entierement_resoluble_ne_produit_aucun_echec():
    resolutions, echecs = resoudre_legislatures([
        ("1", "2022-07-11", "16"), ("1", "2022-07-11", None),
        ("2", "2026-01-05", "17"),
        ("3", "2023-03-02", None),
    ])
    assert echecs == []
    assert len(resolutions) == 3


# ── Provenance vue de l'occurrence ───────────────────────────────────────────

def test_provenance_par_occurrence_distingue_collectee_et_jumeau():
    """Le même scrutin est « collecté » pour le vote qui portait la valeur et
    « résolu par jumeau » pour celui qui ne la portait pas. C'est cette
    distinction qui rend le mécanisme 1 lisible dans un rapport."""
    resolution = Resolution("16", PROVENANCE_COLLECTEE)

    assert provenance_par_occurrence("16", resolution) == PROVENANCE_COLLECTEE
    assert provenance_par_occurrence(None, resolution) == PROVENANCE_JUMEAU


def test_provenance_par_occurrence_ne_requalifie_pas_une_derivation():
    """Une dérivation calendaire reste une dérivation pour toutes ses
    occurrences : aucune ne portait la valeur."""
    resolution = Resolution("16", PROVENANCE_CALENDRIER)

    assert provenance_par_occurrence(None, resolution) == PROVENANCE_CALENDRIER


def test_provenances_connues_est_close():
    assert PROVENANCES_CONNUES == {PROVENANCE_COLLECTEE, PROVENANCE_JUMEAU, PROVENANCE_CALENDRIER}


# ── L'exception ──────────────────────────────────────────────────────────────

def test_exception_porte_tous_les_echecs_pas_seulement_le_premier():
    """Un appelant qui corrigerait au coup par coup relancerait le corpus
    entier à chaque fois."""
    _, echecs = resoudre_legislatures([
        ("1", "2024-07-01", None), ("2", "2024-07-02", None),
        ("3", "2024-07-03", None), ("4", "2024-07-04", None),
    ])
    exc = LegislatureIrresoluble(echecs)

    assert exc.echecs == echecs
    assert "4 scrutin(s)" in str(exc)
    assert "et 1 autre(s)" in str(exc)
    assert "§2.5" in str(exc)
    assert "LEGISLATURES_AN" in str(exc)


# ── Le calendrier lui-même ───────────────────────────────────────────────────

def test_calendrier_coherent_avec_couverture_dossiers():
    """`couverture_dossiers.LEGISLATURES_DEBUT` porte déjà les dates d'ouverture
    des législatures dont l'archive de dossiers est ingérée. Deux calendriers qui
    divergeraient rattacheraient les votes et les textes à des périodes
    différentes, sans que rien ne le signale."""
    for legislature, debut in LEGISLATURES_DEBUT.items():
        cle = str(legislature)
        if cle in LEGISLATURES_AN:
            assert LEGISLATURES_AN[cle][0] == debut, (
                f"Législature {cle} : ouverture {LEGISLATURES_AN[cle][0]} ici, "
                f"{debut} dans couverture_dossiers."
            )


def test_calendrier_est_ordonne_et_sans_recouvrement():
    """Un recouvrement rendrait `legislature_du_calendrier` dépendante de
    l'ordre d'itération du dict — une dérivation qui change avec une
    réorganisation du code."""
    entrees = sorted(LEGISLATURES_AN.items(), key=lambda kv: kv[1][0])
    for (_, (_, fin_precedente)), (cle, (debut, _)) in zip(entrees, entrees[1:]):
        assert fin_precedente is not None, "seule la dernière législature peut être ouverte"
        assert fin_precedente < debut, f"recouvrement avant la législature {cle}"


def test_une_seule_legislature_est_ouverte():
    ouvertes = [cle for cle, (_, fin) in LEGISLATURES_AN.items() if fin is None]
    assert len(ouvertes) == 1, f"législatures sans borne haute : {ouvertes}"
