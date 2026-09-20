"""#996 lot 3 — `roster_gouvernement`, la troisième population de
`pivot_data/profiles/`.

Le lot 2 a donné un slug aux 311 membres des 17 gouvernements. Il ne les
collectait pas : ils n'entraient pas dans `roster_candidats.json`, le seul
fichier que les shards lisent. Ce lot les y verse, sous une provenance à eux.

**Les identifiants de ces tests viennent du corpus, pas d'une invention** —
c'est la précaution que trois défauts publiés le 16/09/2026 avec des tests
verts ont rendue non négociable :

  - `PA721670` / `amelie-de-montchalin`, `PA605991` / `annie-genevard` :
    membres publiés de `pivot_data/gouvernements/gouvernement-LECORNU.json`,
    tous deux porteurs d'un profil — ce sont des cas de DÉDUPLICATION ;
  - `PA387829` / `rachida-dati` : membre de gouvernement **sans profil et sans
    entrée de table**, vérifié sur `origin/main` le 18/09/2026. C'est un des
    205, le cas que ce lot existe pour ouvrir ;
  - `PO873418`, l'organe `GOUVERNEMENT` de Lecornu I, déjà utilisé par
    `tests/test_roster_gouvernements_996.py`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import generate_all_profiles  # noqa: E402
from generate_roster_candidats import candidats_des_gouvernements  # noqa: E402
from population_profils import (  # noqa: E402
    PROVENANCES_ROSTER,
    ROSTER_GOUVERNEMENT,
    ROSTER_GROUPE,
    Ventilation,
    ventiler_provenances,
)
from schema_pivot import KNOWN_PROVENANCES, validate_profil  # noqa: E402


def _membre(slug, acteur_ref, nom, libelles=("Gouvernement Sébastien LECORNU",)):
    """Un membre au format que `gouvernement_roster_an.deriver_membres` rend."""
    return {
        "slug": slug,
        "slug_origine": "fabrique",
        "acteur_ref": acteur_ref,
        "nom": nom,
        "mandat_periodes": [
            {"organe_ref": "PO873418", "libelle_an": libelle,
             "debut": "2025-10-05", "fin": "2025-10-10"}
            for libelle in libelles
        ],
    }


# ── Le versement dans roster_candidats.json ────────────────────────────────

def test_un_membre_sans_profil_entre_dans_le_roster_de_candidats():
    """Le cas des 205. Sans cette entrée, sa collecte ne part jamais : les
    shards itèrent sur `roster_candidats.json`, et lui seul."""
    candidats = candidats_des_gouvernements([
        _membre("rachida-dati", "PA387829", "Rachida Dati"),
    ])

    assert len(candidats) == 1
    entree = candidats[0]
    assert entree["slug"] == "rachida-dati"
    assert entree["statut"] == ROSTER_GOUVERNEMENT
    assert entree["acteur_ref"] == "PA387829"


def test_le_statut_ecrit_est_une_provenance_du_schema():
    """`generate_all_profiles` reprend ce `statut` TEL QUEL comme
    `meta.provenance` : s'il n'est pas dans `KNOWN_PROVENANCES`,
    `validate_profil()` refuse tous les profils que ce roster fait collecter.
    Le couplage est réel et muet, donc il est tenu ici."""
    entree = candidats_des_gouvernements([
        _membre("rachida-dati", "PA387829", "Rachida Dati"),
    ])[0]

    assert entree["statut"] in KNOWN_PROVENANCES


def test_l_acteur_ref_est_transmis_car_le_nom_ne_suffit_pas():
    """124 des 311 membres n'ont jamais été députés : aucune recherche par nom
    ne les retrouve dans AMO30 (#850, aggravé). `acteur_ref` est donc la seule
    façon dont leur collecte peut partir, et `source` le rend vérifiable
    (§2 règle 2)."""
    entree = candidats_des_gouvernements([
        _membre("rachida-dati", "PA387829", "Rachida Dati"),
    ])[0]

    assert entree["acteur_ref"] == "PA387829"
    assert "PA387829" in entree["source"]


def test_un_membre_sans_acteur_ref_ne_recoit_pas_de_source_inventee():
    """§2 règle 5 : `null` dit « la source ne l'a pas rendu », jamais une URL
    fabriquée depuis le slug."""
    membre = _membre("sans-acteur", None, "Sans Acteur")
    membre["acteur_ref"] = None

    entree = candidats_des_gouvernements([membre])[0]

    assert entree["acteur_ref"] is None
    assert entree["source"] is None


def test_aucune_etiquette_politique_n_est_inventee():
    """AMO30 ne publie pas de parti sur un mandat de gouvernement. `null` dit
    « non porté », pas « sans parti » (§2 règle 5)."""
    entree = candidats_des_gouvernements([
        _membre("rachida-dati", "PA387829", "Rachida Dati"),
    ])[0]

    assert entree["parti"] is None
    assert entree["famille_politique"] is None


def test_les_notes_nomment_les_gouvernements_traverses():
    entree = candidats_des_gouvernements([
        _membre("rachida-dati", "PA387829", "Rachida Dati",
                libelles=("Gouvernement Sébastien LECORNU", "Gouvernement Michel BARNIER")),
    ])[0]

    assert "Sébastien LECORNU" in entree["notes"]
    assert "Michel BARNIER" in entree["notes"]


def test_un_membre_sans_slug_n_entre_pas():
    """`<slug>.pivot.json` EST le nom du fichier (#487) : sans slug, il n'y a
    pas de profil à collecter."""
    membre = _membre("", "PA1", "Sans Slug")

    assert candidats_des_gouvernements([membre]) == []


# ── La déduplication, et qui gagne ─────────────────────────────────────────

def test_un_ministre_deja_porte_par_un_groupe_reste_membre_de_groupe():
    """LE point qui compte. Amélie de Montchalin est à la fois membre publié du
    gouvernement Lecornu I et porteuse d'un profil venu du roster de son
    groupe. La rétrograder en `roster_gouvernement` la retirerait de la
    cohésion de son groupe, que `group_profile.py` agrège sur la provenance.
    Son rattachement au gouvernement passe par `acteur_ref` (lot 4), pas par
    la provenance : rien n'est perdu."""
    candidats = candidats_des_gouvernements(
        [_membre("amelie-de-montchalin", "PA721670", "Amélie de Montchalin")],
        deja_pris=["amelie-de-montchalin"],
    )

    assert candidats == []


def test_une_personne_de_deux_gouvernements_n_entre_qu_une_fois():
    """Même règle que le lot 2 : c'est une personne à collecter, pas une par
    gouvernement."""
    membre = _membre("rachida-dati", "PA387829", "Rachida Dati")

    candidats = candidats_des_gouvernements([membre, membre])

    assert len(candidats) == 1


def test_les_membres_de_groupe_ne_sont_pas_reecrits():
    """`deja_pris` est consommé une seule fois : passer un générateur ne doit
    pas vider la garde au premier membre."""
    candidats = candidats_des_gouvernements(
        [
            _membre("annie-genevard", "PA605991", "Annie Genevard"),
            _membre("amelie-de-montchalin", "PA721670", "Amélie de Montchalin"),
            _membre("rachida-dati", "PA387829", "Rachida Dati"),
        ],
        deja_pris=(s for s in ["annie-genevard", "amelie-de-montchalin"]),
    )

    assert [c["slug"] for c in candidats] == ["rachida-dati"]


# ── La population, et sa ventilation ───────────────────────────────────────

def test_la_provenance_est_une_provenance_de_roster():
    """Six modules testaient l'égalité à `roster_groupe` pour dire « membre de
    roster ». C'est cette égalité qui aurait laissé les membres de gouvernement
    collectés en bicaméral et sans `acteur_ref`."""
    assert ROSTER_GOUVERNEMENT in PROVENANCES_ROSTER
    assert ROSTER_GROUPE in PROVENANCES_ROSTER


def test_la_ventilation_compte_les_membres_de_gouvernement_a_part():
    ventilation = ventiler_provenances([
        "candidat_declare", ROSTER_GROUPE, ROSTER_GOUVERNEMENT, ROSTER_GOUVERNEMENT,
    ])

    assert ventilation.membres_gouvernement == 2
    assert ventilation.membres_roster == 1
    assert ventilation.total == 4
    assert "2 membres de gouvernement" in ventilation.detail()


def test_le_poste_gouvernement_est_muet_tant_qu_il_ne_pese_pas():
    """Avant le premier run de collecte, le poste vaudrait `0` sur chaque ligne
    de chaque rapport : c'est du bruit, pas une ventilation. Un `0` masqué ne
    cache aucune population — il dit qu'il n'y en a pas."""
    ventilation = ventiler_provenances(["candidat_declare", ROSTER_GROUPE])

    assert ventilation.membres_gouvernement == 0
    assert "gouvernement" not in ventilation.detail()


def test_le_total_reste_la_somme_des_postes():
    """La propriété que #630 a posée : le total et la somme de ses parts ne
    peuvent pas diverger en silence."""
    ventilation = Ventilation(
        candidats_declares=32, membres_roster=1145, membres_gouvernement=205,
        provenance_autre=1, illisibles=2,
    )

    assert ventilation.total == 32 + 1145 + 205 + 1 + 2
    assert sum(effectif for effectif, _ in ventilation.postes()) == ventilation.total


def test_la_ventilation_serialisee_porte_le_nouveau_poste():
    """Un rapport JSON porte la ventilation, son rendu Markdown la relit."""
    ventilation = Ventilation(membres_gouvernement=205)

    assert ventilation.as_dict()[ROSTER_GOUVERNEMENT] == 205
    assert Ventilation.depuis_dict(ventilation.as_dict()) == ventilation


def test_un_rapport_d_avant_ce_lot_se_relit_sans_inventer_de_membres():
    """Rétro-compatibilité : la clé est absente des rapports d'avant #996
    lot 3, et `0` y est la valeur juste — ces corpus n'en portaient aucun."""
    ancien = {"total": 481, "candidat_declare": 13, "roster_groupe": 468,
              "provenance_autre": 0, "illisibles": 0}

    ventilation = Ventilation.depuis_dict(ancien)

    assert ventilation.membres_gouvernement == 0
    assert ventilation.total == 481


# ── La collecte : le couplage que l'ancien code cassait en silence ─────────

def _args_roster() -> argparse.Namespace:
    """Même harnais que `tests/test_acteur_du_roster_850.py` : aucun réseau,
    aucune lecture du dépôt."""
    return argparse.Namespace(
        source="an", pivot_only=False, skip_existing=False,
        skip_interventions=False, interventions_theme_seul=False,
        skip_dossiers_legislatifs=True, budget_interventions_secondes=0,
        budget_collecte_secondes=0, skip_ue=True, pivot=False, no_merge=False,
        enrich_parltrack=False, candidats_declares=frozenset(),
    )


def _collecte_espionne(monkeypatch) -> list[dict]:
    recus: list[dict] = []

    def fausse_collecte(chambre, slug, **kwargs):
        recus.append({"chambre": chambre, **kwargs})
        return {
            "slug": slug, "chambre": chambre,
            # Une identité, sinon `process_candidat` n'écrit aucun pivot et le
            # test du bout de chaîne ne mesurerait rien.
            "identite": {"nom": "Rachida Dati", "slug": slug}, "mandats": [],
            "votes": [], "interventions": [], "amendements": [],
            "dossiers_legislatifs": [], "votes_source": None, "source": None,
            "meta": {"warnings": [], "synchro_sources": {}},
        }

    monkeypatch.setattr("generate_all_profiles.build_profile", fausse_collecte)
    return recus


def test_un_membre_de_gouvernement_transmet_son_acteur_a_la_collecte(monkeypatch, tmp_path):
    """Mesuré sur `origin/main` le 18/09/2026 : le mapping testait l'égalité à
    `roster_groupe`, donc un membre de gouvernement devenait
    `candidat_declare` et son `acteur_ref` était remplacé par `None`. 124 des
    311 membres n'ont jamais été députés : leur collecte ne serait jamais
    partie, et rien n'aurait échoué."""
    recus = _collecte_espionne(monkeypatch)

    generate_all_profiles.process_candidat(
        {"nom": "Rachida Dati", "slug": "rachida-dati",
         "statut": ROSTER_GOUVERNEMENT, "acteur_ref": "PA387829"},
        _args_roster(), tmp_path / "raw", tmp_path / "pivot",
    )

    assert recus and recus[0]["acteur_ref"] == "PA387829"


# `groupes_reels.json` est une config tenue à la main, pas un fichier qu'un run
# réécrit : le déclarer est le chemin documenté par le garde de #791, et non un
# affaiblissement. Même déclaration que `tests/test_generate_all_profiles.py`,
# et sur le SEUL test qui va jusqu'à l'écriture du pivot.
@pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")
def test_le_pivot_ecrit_declare_la_provenance_de_gouvernement(monkeypatch, tmp_path):
    """Le bout de la chaîne, et l'observable durable : c'est
    `meta.provenance` du fichier publié qui décide de tout l'aval — la
    ventilation des outils, la couverture, et la population qu'un agrégat
    consomme. Sur `origin/main`, ce même profil était publié
    `candidat_declare`, donc compté comme une fiche à publier.

    `collecte_bicamerale`, l'autre effet du mapping, n'est PAS testé ici : sur
    une seule chambre il n'a aucun effet observable, et `build_profile_any_chambre`
    le dit lui-même (`generate_all_profiles.py`, § « Deux régimes »). Un test
    qui l'affirmerait quand même décrirait l'endroit où l'on a regardé.
    """
    _collecte_espionne(monkeypatch)
    args = _args_roster()
    args.pivot, args.no_merge = True, True

    generate_all_profiles.process_candidat(
        {"nom": "Rachida Dati", "slug": "rachida-dati",
         "statut": ROSTER_GOUVERNEMENT, "acteur_ref": "PA387829"},
        args, tmp_path / "raw", tmp_path / "pivot",
    )

    publie = json.loads(
        (tmp_path / "pivot" / "rachida-dati.pivot.json").read_text(encoding="utf-8"))
    assert publie["meta"]["provenance"] == ROSTER_GOUVERNEMENT


# ── Le profil publié passe la validation ───────────────────────────────────

def test_un_profil_de_membre_de_gouvernement_est_valide():
    """Le bout de la chaîne : si le schéma refusait la provenance, aucun des
    205 profils ne pourrait être publié."""
    from schema_pivot import make_empty_profil  # noqa: PLC0415

    profil = make_empty_profil(
        "an:PA387829", "Rachida Dati", provenance=ROSTER_GOUVERNEMENT)
    # Le couple `chambres`/`chambre` se pose ensemble (#493) ; ici à la main,
    # pour garder la fixture minimale — même patron que `test_schema_pivot`.
    profil["chambres"] = ["AN"]
    profil["chambre"] = "AN"
    profil["meta"]["licence_donnees"] = "Licence Ouverte / Open Licence (Etalab)"

    assert profil["meta"]["provenance"] == ROSTER_GOUVERNEMENT
    assert validate_profil(profil) == []
