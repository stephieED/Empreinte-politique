"""#1020 — sur quoi les membres d'un gouvernement ont pris la parole.

Même logique que la fiche de groupe, à deux divergences près, toutes deux
mesurées le 18/09/2026 sur le corpus publié :

  - le filtre est la **fenêtre de passage du membre**, pas une législature ;
  - une intervention **sans date est écartée**, là où le groupe retient ses
    entrées sans législature.

Les cas de ce fichier sont réels. `Yaël Braun-Pivet` est celui qui a décidé du
filtre : ministre du 24 au 27 juin 2022, puis présidente de l'Assemblée, elle
porte **8 968 interventions dans la fenêtre du gouvernement Borne** et **0**
dans la sienne. Sans le filtre par membre, « la parole du gouvernement Borne »
aurait été la sienne, depuis le perchoir.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from gouvernement_profile import (  # noqa: E402
    agreger_tags_thematiques,
    fenetres_des_membres,
)


def _membre(membre_id: str, debut: str | None, fin: str | None, portefeuille=None) -> dict:
    return {"membre_id": membre_id, "nom": membre_id, "portefeuille": portefeuille,
            "debut": debut, "fin": fin, "actif": False, "source_url": None}


def _profil(id_: str, interventions: list[dict]) -> dict:
    return {"id": id_, "nom": id_, "interventions": interventions}


def _lecteur(profils: dict[str, dict]):
    """Le lecteur d'interventions que `agreger_tags_thematiques` exige.

    Il ne reçoit PLUS des profils : les profils du pipeline sont projetés sur
    cinq blocs (#635) et n'ont pas d'`interventions`. C'est ce qui a fait
    publier `[]` sur les 17 fiches pendant un run — et ce que les cas
    ci-dessous ne pouvaient pas voir, puisqu'ils fabriquaient leurs profils.
    La garde du chemin réel est dans
    `tests/test_generate_gouvernement_profiles.py`.
    """
    return lambda membre_id: (profils.get(membre_id) or {}).get("interventions") or []


def _interv(date: str | None, theme: str) -> dict:
    return {"intervention_id": f"syceron_{theme}_{date}", "date": date,
            "theme_officiel": theme, "mots_cles": []}


# ── Les fenêtres de passage ────────────────────────────────────────────────

def test_une_personne_de_deux_periodes_a_une_fenetre_par_periode():
    """`membres[]` porte une entrée par période de portefeuille (#398) :
    l'union décrit le passage, pas la première entrée trouvée."""
    membres = [
        _membre("x", "2022-05-21", "2022-07-04", "Ministère A"),
        _membre("x", "2022-09-01", "2023-01-01", "Ministère B"),
    ]

    fen = fenetres_des_membres(membres, "2022-05-17", "2024-01-09")

    assert fen == {"x": [("2022-05-21", "2022-07-04"), ("2022-09-01", "2023-01-01")]}


def test_une_borne_absente_retombe_sur_celle_du_gouvernement():
    fen = fenetres_des_membres([_membre("x", None, None)], "2022-05-17", "2024-01-09")

    assert fen == {"x": [("2022-05-17", "2024-01-09")]}


def test_un_gouvernement_en_cours_laisse_la_fenetre_ouverte():
    """`periode.fin` nulle veut dire « toujours en fonction » et n'est jamais
    remplacée par la date du jour (§2 règle 5)."""
    fen = fenetres_des_membres([_membre("x", "2025-10-13", None)], "2025-10-11", None)

    assert fen["x"] == [("2025-10-13", "9999-12-31")]


def test_sans_aucune_borne_basse_la_fenetre_n_est_pas_fabriquee():
    """Une fenêtre ouverte des deux côtés retiendrait toute la carrière."""
    assert fenetres_des_membres([_membre("x", None, None)], None, None) == {}


# ── Le filtre, et ce qu'il retire ──────────────────────────────────────────

def test_la_parole_hors_du_passage_ministeriel_est_ecartee():
    """LE cas qui a décidé du filtre. Yaël Braun-Pivet a été ministre trois
    jours, puis présidente de l'Assemblée : ses 8 968 interventions dans la
    fenêtre Borne sont celles d'une présidente de séance, pas d'un membre du
    gouvernement. Mesuré le 18/09/2026 — 8 968 → 0."""
    membres = [_membre("yael-braun-pivet", "2022-06-24", "2022-06-27")]
    profils = {"yael-braun-pivet": _profil("yael-braun-pivet", [
        _interv("2022-06-25", "outre-mer"),          # pendant son passage
        _interv("2022-11-02", "budget"),             # depuis le perchoir
        _interv("2023-06-14", "retraites"),          # idem
    ])}

    tags, porteurs, hors, sans_date = agreger_tags_thematiques(
        fenetres_des_membres(membres, "2022-05-17", "2024-01-09"), _lecteur(profils))

    assert [t["tag"] for t in tags] == ["outre-mer"]
    assert (porteurs, hors, sans_date) == (1, 2, 0)


def test_une_intervention_sans_date_est_ecartee_et_comptee():
    """Divergence assumée d'avec le groupe, qui retient ses entrées sans
    législature. Un gouvernement dure quelques mois : rien ne permet d'y
    placer une entrée non datée, et l'y mettre affirmerait sans source
    (§2 règle 5). Mesuré : 5 entrées sur 97 898 chez Borne."""
    membres = [_membre("x", "2022-05-21", "2022-07-04")]
    profils = {"x": _profil("x", [_interv(None, "budget"), _interv("2022-06-01", "sante")])}

    tags, porteurs, hors, sans_date = agreger_tags_thematiques(
        fenetres_des_membres(membres, "2022-05-17", "2024-01-09"), _lecteur(profils))

    assert [t["tag"] for t in tags] == ["sante"]
    assert (porteurs, hors, sans_date) == (1, 0, 1)


def test_un_membre_sans_profil_ne_bloque_rien():
    """205 membres n'avaient aucun profil avant #996 ; un membre non collecté
    est une absence, pas une erreur."""
    membres = [_membre("absent", "2022-05-21", "2022-07-04")]

    tags, porteurs, hors, sans_date = agreger_tags_thematiques(
        fenetres_des_membres(membres, "2022-05-17", "2024-01-09"), _lecteur({}))

    assert (tags, porteurs, hors, sans_date) == ([], 0, 0, 0)


# ── Ce que l'agrégat compte, et ce qu'il refuse de compter ─────────────────

def test_une_etiquette_compte_une_fois_par_membre():
    """L'agrégat dit combien de PERSONNES ont parlé d'un sujet, jamais combien
    de fois — un compte d'occurrences serait un indice d'activité (§2 règle 1)."""
    membres = [_membre("a", "2022-05-21", "2022-07-04"), _membre("b", "2022-05-21", "2022-07-04")]
    profils = {
        "a": _profil("a", [_interv("2022-06-01", "budget")] * 40),
        "b": _profil("b", [_interv("2022-06-02", "budget")]),
    }

    tags, porteurs, _, _ = agreger_tags_thematiques(
        fenetres_des_membres(membres, "2022-05-17", "2024-01-09"), _lecteur(profils))

    assert tags == [{"tag": "budget", "nb_membres_porteurs": 2}]
    assert porteurs == 2


def test_aucun_ratio_n_est_publie():
    """`mandats_agreges` a retiré `poids_relatif` pour que le lecteur voie
    « 5 / 76 » et non un pourcentage seul (§2.7) ; `tags_thematiques_agreges`
    du groupe ne l'a pas suivi. Le nouvel agrégat ne reproduit pas ce retard :
    son dénominateur est `comptages.membres_avec_interventions`."""
    membres = [_membre("a", "2022-05-21", "2022-07-04")]
    profils = {"a": _profil("a", [_interv("2022-06-01", "budget")])}

    tags, _, _, _ = agreger_tags_thematiques(
        fenetres_des_membres(membres, "2022-05-17", "2024-01-09"), _lecteur(profils))

    assert set(tags[0]) == {"tag", "nb_membres_porteurs"}


def test_le_tri_met_les_sujets_les_plus_partages_en_tete():
    membres = [_membre(x, "2022-05-21", "2022-07-04") for x in ("a", "b", "c")]
    profils = {
        "a": _profil("a", [_interv("2022-06-01", "budget"), _interv("2022-06-01", "sante")]),
        "b": _profil("b", [_interv("2022-06-02", "budget")]),
        "c": _profil("c", [_interv("2022-06-03", "budget")]),
    }

    tags, _, _, _ = agreger_tags_thematiques(
        fenetres_des_membres(membres, "2022-05-17", "2024-01-09"), _lecteur(profils))

    assert [(t["tag"], t["nb_membres_porteurs"]) for t in tags] == [("budget", 3), ("sante", 1)]
