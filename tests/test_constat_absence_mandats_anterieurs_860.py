"""Garde-fou : une absence relue dit sur quoi elle se fonde (#860).

Une liste `mandats_anterieurs` vide n'est pas un silence — elle AFFIRME que la
personne n'a exercé aucun mandat national avant le 19/06/2002. C'est un fait
publié, et §2 règle 2 veut qu'un fait publié renvoie à sa source primaire.
Quand la liste porte des mandats, chaque ligne porte la sienne ; vide, elle
n'avait rien à quoi l'accrocher, et la fiche affirmait sans montrer.

D'où `constat` dans la table et `mandats_anterieurs_constat` sur le pivot :
l'URL consultée, la date, et la MÉTHODE. Les deux méthodes ne se valent pas et
c'est tout l'intérêt de les nommer — `lecture_fiche_sycomore` est une lecture de
la source primaire par le pipeline, reproductible ; `relecture_humaine` est une
signature, que rien d'automatique ne pose à la place de quelqu'un.

Les trois états restent distincts, et aucun ne se lit comme un autre :
  liste pleine  → relu, des mandats trouvés (source sur chaque ligne)
  liste vide    → relu, aucun mandat — avec son constat
  null          → personne n'a regardé (`non_relu`)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mandats_anterieurs import (
    TableMandatsAnterieursInvalide,
    appliquer_mandats_anterieurs,
    charger_table,
)
from schema_pivot import KNOWN_METHODES_CONSTAT_ANTERIEUR, valider_mandats_anterieurs

RACINE = Path(__file__).resolve().parent.parent
TABLE = RACINE / "raw_data" / "mandats_anterieurs.json"

CONSTAT = {
    "source_url": "https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept=17264",
    "constate_le": "2026-09-15",
    "methode": "lecture_fiche_sycomore",
}


def _ecrire(tmp_path: Path, candidats: dict) -> Path:
    p = tmp_path / "table.json"
    p.write_text(json.dumps({"_meta": {}, "candidats": candidats}), encoding="utf-8")
    return p


def _profil(slug: str) -> dict:
    return {"id": slug, "meta": {"provenance": "candidat_declare"}}


# --- la table ---------------------------------------------------------------

def test_liste_vide_nue_est_refusee(tmp_path: Path) -> None:
    """La forme qui affirmait sans sourcer ne passe plus."""
    with pytest.raises(TableMandatsAnterieursInvalide, match="constat"):
        charger_table(_ecrire(tmp_path, {"delphine-batho": []}))


def test_absence_avec_constat_est_acceptee(tmp_path: Path) -> None:
    table = charger_table(_ecrire(tmp_path, {"delphine-batho": {"mandats": [], "constat": CONSTAT}}))
    assert table["delphine-batho"]["constat"] == CONSTAT


@pytest.mark.parametrize(
    "champ, valeur",
    [
        ("source_url", None),
        ("source_url", "http://www2.assemblee-nationale.fr/x"),  # pas https
        ("constate_le", None),
        ("constate_le", "15/09/2026"),                            # pas ISO
        ("methode", None),
        ("methode", "on_a_regarde_vite_fait"),                    # hors frozenset
    ],
)
def test_constat_incomplet_est_refuse(tmp_path: Path, champ: str, valeur) -> None:
    constat = dict(CONSTAT)
    if valeur is None:
        constat.pop(champ)
    else:
        constat[champ] = valeur
    with pytest.raises(TableMandatsAnterieursInvalide):
        charger_table(_ecrire(tmp_path, {"delphine-batho": {"mandats": [], "constat": constat}}))


def test_constat_sur_liste_pleine_est_refuse(tmp_path: Path) -> None:
    """Deux endroits pour un même fait finissent par diverger."""
    ligne = {
        "institution": "assemblee_nationale",
        "libelle": "Députée des Deux-Sèvres",
        "debut": "1988-06-13",
        "fin": "1992-05-02",
        "source_url": "https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept=6174",
        "verifie_le": "2026-09-11",
    }
    with pytest.raises(TableMandatsAnterieursInvalide, match="non vide"):
        charger_table(_ecrire(tmp_path, {"segolene-royal": {"mandats": [ligne], "constat": CONSTAT}}))


# --- le versement sur la fiche ---------------------------------------------

def test_les_trois_etats_ne_se_confondent_pas(tmp_path: Path) -> None:
    ligne = {
        "institution": "gouvernement",
        "libelle": "Ministre délégué",
        "debut": "2000-03-27",
        "fin": "2002-05-06",
        "source_url": "https://www.legifrance.gouv.fr/jorf/id/X",
        "verifie_le": "2026-09-11",
    }
    table = charger_table(_ecrire(tmp_path, {
        "avec-mandats": {"mandats": [ligne], "constat": None},
        "sans-mandat": {"mandats": [], "constat": CONSTAT},
    }))

    plein = _profil("avec-mandats")
    appliquer_mandats_anterieurs(plein, table)
    assert len(plein["mandats_anterieurs"]) == 1
    assert "mandats_anterieurs_constat" not in plein

    vide = _profil("sans-mandat")
    appliquer_mandats_anterieurs(vide, table)
    assert vide["mandats_anterieurs"] == []
    assert vide["mandats_anterieurs_constat"] == CONSTAT

    jamais = _profil("inconnu")
    appliquer_mandats_anterieurs(jamais, table)
    assert jamais["mandats_anterieurs"] is None
    assert jamais["mandats_anterieurs_non_resolu"] == {"motif": "non_relu"}
    assert "mandats_anterieurs_constat" not in jamais


def test_le_constat_est_repose_et_jamais_fusionne(tmp_path: Path) -> None:
    """Champ dérivé : un constat retiré de la table disparaît de la fiche."""
    table = charger_table(_ecrire(tmp_path, {"x": {"mandats": [], "constat": CONSTAT}}))
    profil = _profil("x")
    appliquer_mandats_anterieurs(profil, table)
    assert profil["mandats_anterieurs_constat"]
    appliquer_mandats_anterieurs(profil, charger_table(_ecrire(tmp_path / "b", {}) if False else _ecrire(tmp_path, {})))
    assert "mandats_anterieurs_constat" not in profil


def test_un_membre_de_roster_ne_porte_aucune_des_trois_cles(tmp_path: Path) -> None:
    table = charger_table(_ecrire(tmp_path, {"x": {"mandats": [], "constat": CONSTAT}}))
    profil = {"id": "x", "meta": {"provenance": "roster_groupe"},
              "mandats_anterieurs_constat": dict(CONSTAT)}
    appliquer_mandats_anterieurs(profil, table)
    assert "mandats_anterieurs" not in profil
    assert "mandats_anterieurs_constat" not in profil


# --- la validation du pivot -------------------------------------------------

def test_le_schema_refuse_une_absence_sans_constat() -> None:
    erreurs = valider_mandats_anterieurs({"mandats_anterieurs": []})
    assert any("constat" in e for e in erreurs)


def test_le_schema_accepte_une_absence_constatee() -> None:
    assert valider_mandats_anterieurs(
        {"mandats_anterieurs": [], "mandats_anterieurs_constat": CONSTAT}
    ) == []


# --- la table du dépôt ------------------------------------------------------
#
# Le SUJET de ce test est le fichier committé lui-même, pas une fixture : il
# vérifie que la table du dépôt porte bien des constats. Le marqueur le déclare,
# et `tests.yml` a déjà ce chemin dans son sparse-checkout (#791).


@pytest.mark.lit_reference_committee("raw_data/mandats_anterieurs.json")
def test_la_table_commitee_se_charge() -> None:
    table = charger_table(TABLE)
    vides = {s: e for s, e in table.items() if not e["mandats"]}
    assert vides, "aucune absence constatée : le champ ne sert à rien"
    for slug, entree in vides.items():
        assert entree["constat"]["methode"] in KNOWN_METHODES_CONSTAT_ANTERIEUR, slug
