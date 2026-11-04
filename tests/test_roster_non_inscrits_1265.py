"""#1265 — la troisième porte du roster : les députés non inscrits.

Les non-inscrits ne sont pas un groupe : la porte « groupe » ne les collectait
jamais, et 25 députés n'avaient aucun profil (mesuré le 04/11/2026). Ce lot les
verse dans `roster_candidats.json` sous la provenance `roster_non_inscrit`.

Tout tourne sur `tests/fixtures/amo30_gp_leg16_17.zip`, **extraite de l'archive
réelle** : Véronique Besse (`PA309643`, non inscrite sous la XVIe et la XVIIe),
Philippe Bonnecarrère (`PA569`) et Stéphane Chouin (`PA841347`), XVIIe, et
Emmanuelle Ménard (`PA719608`), XVIe, sont quatre des 25. Aurélien Pradié
(`PA720100`) est non inscrit et a un profil : c'est le cas de déduplication.
Aucun réseau, aucune lecture de `pivot_data/`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import an_roster  # noqa: E402
import generate_all_profiles  # noqa: E402
import generate_roster_candidats as g  # noqa: E402
from population_profils import (  # noqa: E402
    PROVENANCES_ROSTER,
    ROSTER_NON_INSCRIT,
    Ventilation,
    ventiler_provenances,
)
from schema_pivot import KNOWN_PROVENANCES  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures"
ARCHIVE = FIXTURES / "amo30_gp_leg16_17.zip"
TABLE = FIXTURES / "correspondance_acteurs_an_extrait.json"


@pytest.fixture(scope="module")
def membres():
    """`membres_non_inscrits` sur la fixture, sans écrire de cache d'index :
    le chargeur est remplacé par la construction pure."""
    import gouvernement_roster_an  # noqa: PLC0415

    patch = pytest.MonkeyPatch()
    patch.setattr(an_roster, "charger_index_gp", lambda chemin=None, **_: an_roster.construire_index_gp(Path(chemin)))
    # La fixture ne porte aucun organe de gouvernement : l'index des
    # gouvernements, qui ne sert ici qu'à l'univers de collision des slugs,
    # est vide. En production, son absence fait sauter la porte (voir `main`).
    patch.setattr(gouvernement_roster_an, "construire_index_gouvernements", lambda _chemin: {"acteurs": {}})
    try:
        yield g.membres_non_inscrits(ARCHIVE, TABLE)
    finally:
        patch.undo()


def _par_acteur(membres):
    return {m["acteur_ref"]: m for m in membres}


def test_les_non_inscrits_hors_transit_sont_lus(membres):
    """Le transit d'ouverture (576 et 577 mandats) est écarté : sans quoi les
    577 députés de chaque législature entreraient par cette porte."""
    par_acteur = _par_acteur(membres)
    assert {"PA309643", "PA569", "PA841347", "PA719608"} <= set(par_acteur)
    assert len(membres) < 200


def test_une_personne_de_deux_legislatures_n_entre_qu_une_fois(membres):
    besse = [m for m in membres if m["acteur_ref"] == "PA309643"]
    assert len(besse) == 1 and besse[0]["legislatures"] == ["16", "17"]


def test_un_slug_sans_table_est_fabrique_et_le_dit(membres):
    """La passe `--completer-derivees` en dérive l'entrée de correspondance dans
    le run : c'est `slug_origine` qui le lui dit."""
    besse = _par_acteur(membres)["PA309643"]
    assert (besse["slug"], besse["slug_origine"]) == ("veronique-besse", "fabrique")


def test_un_non_inscrit_deja_porte_par_un_groupe_n_entre_pas(membres):
    """Pradié a un profil par son groupe : il le garde, avec sa provenance. Il
    est reconnu par son `acteur_ref`, même sous un autre slug."""
    deja = [{"slug": "aurelien-pradie-autre", "acteur_ref": "PA720100"}]
    slugs = {c["slug"] for c in g.candidats_des_non_inscrits(membres, deja_pris=deja)}
    assert not any(s.startswith("aurelien-pradie") for s in slugs)


def test_un_slug_deja_pris_n_entre_pas(membres):
    deja = [{"slug": "veronique-besse", "acteur_ref": None}]
    acteurs = {c["acteur_ref"] for c in g.candidats_des_non_inscrits(membres, deja_pris=deja)}
    assert "PA309643" not in acteurs


def test_l_entree_porte_la_provenance_l_acteur_et_aucun_parti(membres):
    besse = next(c for c in g.candidats_des_non_inscrits(membres) if c["acteur_ref"] == "PA309643")
    assert besse["statut"] == ROSTER_NON_INSCRIT
    assert besse["statut"] in KNOWN_PROVENANCES and besse["statut"] in PROVENANCES_ROSTER
    assert "PA309643" in besse["source"]
    assert (besse["parti"], besse["famille_politique"]) == (None, None)
    assert "XVIe, XVIIe" in besse["notes"]


def test_la_ventilation_compte_les_non_inscrits_a_part():
    ventilation = ventiler_provenances(["roster_groupe", ROSTER_NON_INSCRIT, ROSTER_NON_INSCRIT])
    assert ventilation.non_inscrits == 2 and ventilation.total == 3
    assert "2 non-inscrits" in ventilation.detail()
    assert Ventilation.depuis_dict(ventilation.as_dict()) == ventilation
    assert "non-inscrits" not in ventiler_provenances(["roster_groupe"]).detail()


def test_un_non_inscrit_transmet_son_acteur_a_la_collecte(monkeypatch, tmp_path):
    """Le couplage que #996 a payé : sans `PROVENANCES_ROSTER`, le statut
    devenait `candidat_declare` et l'`acteur_ref` était jeté."""
    recus = []

    def fausse_collecte(chambre, slug, **kwargs):
        recus.append(kwargs)
        return {"slug": slug, "chambre": chambre, "identite": {"nom": "Véronique Besse", "slug": slug},
                "mandats": [], "votes": [], "interventions": [], "amendements": [],
                "dossiers_legislatifs": [], "votes_source": None, "source": None,
                "meta": {"warnings": [], "synchro_sources": {}}}

    monkeypatch.setattr("generate_all_profiles.build_profile", fausse_collecte)
    args = argparse.Namespace(
        source="an", pivot_only=False, skip_existing=False, skip_interventions=False,
        interventions_theme_seul=False, skip_dossiers_legislatifs=True,
        budget_interventions_secondes=0, budget_collecte_secondes=0, skip_ue=True,
        pivot=False, no_merge=False, enrich_parltrack=False, candidats_declares=frozenset(),
    )
    generate_all_profiles.process_candidat(
        {"nom": "Véronique Besse", "slug": "veronique-besse",
         "statut": ROSTER_NON_INSCRIT, "acteur_ref": "PA309643"},
        args, tmp_path / "raw", tmp_path / "pivot",
    )
    assert recus and recus[0]["acteur_ref"] == "PA309643"
