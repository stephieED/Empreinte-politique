"""#996 lot 4 — la fiche rattache ses membres par `organe_ref`, plus par un
libellé comparé entre deux sources.

Les cas de ce fichier ne sont pas inventés : chacun est un couple
(personne, gouvernement) relu le 18/09/2026 dans l'archive AMO30 du jour et
dans `pivot_data/profiles/` sur `origin/main`. Trois d'entre eux ont été
trouvés **en mesurant l'écart entre les deux voies**, pas en lisant le code —
c'est pour ça qu'ils sont ici.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from gouvernement_roster import (  # noqa: E402
    build_gouvernement_roster,
    slugs_du_gouvernement,
)


def _pivot(id_: str, nom: str, mandats: list) -> dict:
    return {
        "schema_version": "1", "id": id_, "nom": nom, "chambre": "AN",
        "parti": None, "groupe": None, "sources": [], "mandats": mandats,
    }


def _appartenance(label: str, debut: str, fin: str | None = None) -> dict:
    return {
        "categorie": "fonction_gouvernementale", "fonction": "membre",
        "label": label, "debut": debut, "fin": fin, "actif": False,
        "source_url": "https://data.assemblee-nationale.fr/...",
        "position_dans_hemicycle": "gouvernement",
    }


def _membre_roster(slug: str, periodes: list[tuple[str, str, str | None]]) -> dict:
    """Une entrée du roster, au format de `gouvernement_roster_an.deriver_membres`."""
    return {
        "slug": slug, "slug_origine": "fabrique", "acteur_ref": "PA000",
        "nom": slug, "mandat_periodes": [
            {"organe_ref": ref, "libelle_an": ref, "debut": d, "fin": f}
            for ref, d, f in periodes
        ],
    }


# ── L'index d'appartenance ─────────────────────────────────────────────────

def test_sans_roster_l_index_vaut_none_et_non_un_ensemble_vide():
    """La distinction porte tout le repli : `None` dit « pas de roster, prends
    le libellé », un ensemble vide dirait « ce gouvernement n'a aucun membre »
    et viderait la fiche (§2 règle 5)."""
    assert slugs_du_gouvernement(None, "PO873418") is None
    assert slugs_du_gouvernement([], "PO873418") is None
    assert slugs_du_gouvernement([_membre_roster("x", [])], None) is None


def test_l_index_ne_retient_que_l_organe_demande():
    roster = [
        _membre_roster("a", [("PO873418", "2025-09-10", "2025-10-10")]),
        _membre_roster("b", [("PO873634", "2025-10-11", None)]),
    ]
    assert slugs_du_gouvernement(roster, "PO873418") == {"a"}


# ── Ce que la voie roster rattrape ─────────────────────────────────────────

def test_un_mandat_sans_sigle_est_rattache_par_le_roster():
    """Damien Abad et Yaël Braun-Pivet portent, sous Borne, un mandat
    d'appartenance libellé `"Gouvernement"` **sans parenthèses** : la source n'a
    pas donné de sigle. L'égalité stricte du repli le jetait — mesuré le
    18/09/2026, 2 entrées perdues sur la fiche Borne. Le roster déclare la
    personne membre, la période le confirme."""
    profils = [_pivot("damien-abad", "Damien Abad", [
        _appartenance("Gouvernement", "2022-06-24", "2022-07-05"),
    ])]
    roster = [_membre_roster("damien-abad", [("PO791579", "2022-05-21", "2022-07-04")])]

    par_libelle = build_gouvernement_roster("BORNE", "2022-05-17", "2024-01-09", profils, [])
    par_roster = build_gouvernement_roster(
        "BORNE", "2022-05-17", "2024-01-09", profils, [],
        slugs_roster=slugs_du_gouvernement(roster, "PO791579"))

    assert par_libelle == []
    assert [m["membre_id"] for m in par_roster] == ["damien-abad"]


def test_un_profil_que_le_roster_ne_nomme_pas_n_est_pas_examine():
    """C'est le roster qui tranche l'appartenance : un profil portant le bon
    libellé mais absent du roster de cet organe n'entre pas."""
    profils = [_pivot("x", "X", [_appartenance("Gouvernement (BORNE)", "2022-06-01")])]
    roster = [_membre_roster("autre", [("PO791579", "2022-05-21", None)])]

    assert build_gouvernement_roster(
        "BORNE", "2022-05-17", "2024-01-09", profils, [],
        slugs_roster=slugs_du_gouvernement(roster, "PO791579")) == []


# ── Les deux pièges que la mesure a révélés ────────────────────────────────

def test_une_periode_de_roster_non_bornee_n_avale_pas_le_gouvernement_suivant():
    """AMO30 publie des appartenances non bornées : Amélie de Montchalin porte
    DEUX périodes `BAYROU`, dont une `2024-12-24 → None` (relevé le
    18/09/2026). Utiliser les dates du roster comme garde temporel lui
    attribuait ses 4 entrées Lecornu sur la fiche Bayrou. C'est la période de
    l'ORGANE qui fait foi — elle, est bornée.

    Le second mandat est libellé **sans sigle** à dessein : avec un
    `Gouvernement (LECORNU)`, c'est le départage par libellé qui l'écarterait,
    et ce test passerait sans rien dire du garde temporel. Vérifié par mutation
    le 18/09/2026 — retirer le garde ne le faisait pas échouer.
    """
    profils = [_pivot("amelie-de-montchalin", "Amélie de Montchalin", [
        _appartenance("Gouvernement (BAYROU)", "2024-12-24", "2025-09-09"),
        _appartenance("Gouvernement", "2025-10-05", "2025-10-10"),
    ])]
    roster = [_membre_roster("amelie-de-montchalin", [
        ("PO855052", "2024-12-24", "2025-09-09"),
        ("PO855052", "2024-12-24", None),          # la borne ouverte de la source
        ("PO873418", "2025-10-05", "2025-10-10"),
    ])]

    membres = build_gouvernement_roster(
        "BAYROU", "2024-12-14", "2025-09-09", profils, [],
        slugs_roster=slugs_du_gouvernement(roster, "PO855052"))

    assert [m["debut"] for m in membres] == ["2024-12-24"]


def test_deux_gouvernements_qui_se_touchent_ne_se_volent_pas_leurs_mandats():
    """`FILLON 1` finit le 2007-06-18, `FILLON 2` commence le 2007-06-18 : les
    périodes se chevauchent d'un jour, donc le chevauchement ne peut pas les
    séparer. Sans le libellé pour départager les mandats D'UNE MÊME PERSONNE,
    Fillon II récupérait 19 entrées de Fillon I, et Valls II 27 de Valls
    (mesuré le 18/09/2026)."""
    profils = [_pivot("rachida-dati", "Rachida Dati", [
        _appartenance("Gouvernement (FILLON 1)", "2007-05-18", "2007-06-18"),
        _appartenance("Gouvernement (FILLON 2)", "2007-06-19", "2010-11-13"),
    ])]
    roster = [_membre_roster("rachida-dati", [
        ("PO382939", "2007-05-18", "2007-06-18"),
        ("PO384206", "2007-06-19", "2010-11-13"),
    ])]

    membres = build_gouvernement_roster(
        "FILLON 2", "2007-06-18", "2010-11-13", profils, [],
        slugs_roster=slugs_du_gouvernement(roster, "PO384206"))

    assert [m["debut"] for m in membres] == ["2007-06-19"]


# ── Le repli ───────────────────────────────────────────────────────────────

def test_sans_roster_le_comportement_historique_est_inchange():
    """Un run sans artifact de roster doit continuer à produire les fiches : la
    voie fragile vaut mieux que pas de fiche (§2 règle 5)."""
    profils = [_pivot("x", "X", [_appartenance("Gouvernement (BAYROU)", "2024-12-24")])]

    membres = build_gouvernement_roster("BAYROU", "2024-12-14", "2025-09-09", profils, [])

    assert [m["membre_id"] for m in membres] == ["x"]
