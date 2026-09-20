#!/usr/bin/env python3
"""
Tests du lot #860 — les mandats antérieurs à la couverture de l'Assemblée.

Un fichier par lot (#840). Ce qu'ils verrouillent :

- **la table committée tient ses invariants** : une source primaire par ligne,
  aucune ligne qui se termine dans la couverture (19/06/2002), une fin nulle
  toujours accompagnée de son motif, les lignes triées ;
- **relu n'est pas non relu** : un candidat de la table reçoit sa liste, un
  candidat absent reçoit `null` et `non_relu` — absent n'est pas « aucun »
  (§2 règle 5) ; un membre de roster ne reçoit rien ;
- **le champ est dérivé** : reposé à chaque écriture, jamais fusionné, et
  validé par `validate_profil`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from mandats_anterieurs import (  # noqa: E402
    BORNE_COUVERTURE_AN,
    TableMandatsAnterieursInvalide,
    appliquer_mandats_anterieurs,
    charger_table,
)
from schema_pivot import valider_mandats_anterieurs  # noqa: E402

pytestmark = pytest.mark.lit_reference_committee("raw_data/mandats_anterieurs.json")

TABLE = RACINE / "raw_data" / "mandats_anterieurs.json"


# ---------------------------------------------------------------------------
# La table committée
# ---------------------------------------------------------------------------

def test_la_table_committee_est_valide():
    table = charger_table(TABLE)
    # Relevé du 11/09/2026 : 5 candidats, 6 mandats de député et 5 fonctions
    # gouvernementales. Les 2 mandats de sénateur de Mélenchon ne sont pas
    # portés, en attente de la reprise de #528.
    #
    # La table porte aussi, depuis le 15/09/2026, des entrées SANS mandat —
    # une absence constatée sur sa source (#860). Ce test-ci ne parle que des
    # entrées qui portent des mandats ; les autres ont le leur.
    avec_mandats = {s for s, e in table.items() if e["mandats"]}
    assert avec_mandats == {
        "segolene-royal", "jean-luc-melenchon", "bruno-retailleau",
        "bernard-cazeneuve", "nicolas-dupont-aignan",
    }
    lignes = [l for e in table.values() for l in e["mandats"]]
    assert len(lignes) == 11
    assert sum(l["institution"] == "assemblee_nationale" for l in lignes) == 6
    assert sum(l["institution"] == "gouvernement" for l in lignes) == 5
    assert not any("senat" in l["institution"] for l in lignes)


def test_chaque_ligne_porte_sa_source_primaire():
    for slug, entree in charger_table(TABLE).items():
        for l in entree["mandats"]:
            assert l["source_url"].startswith((
                "https://www2.assemblee-nationale.fr/sycomore/",
                "https://www.legifrance.gouv.fr/jorf/id/",
            )), (slug, l["source_url"])


def test_la_seule_fin_inconnue_dit_pourquoi():
    """La fin de 1993 n'a pas de décret trouvé : `null`, et le motif (§2 règle 5)."""
    nulles = [(s, l) for s, e in charger_table(TABLE).items()
              for l in e["mandats"] if l["fin"] is None]
    assert [s for s, _ in nulles] == ["segolene-royal"]
    assert nulles[0][1]["fin_non_resolue"]["motif"] == "source_primaire_non_trouvee"


# ---------------------------------------------------------------------------
# Les refus de la table
# ---------------------------------------------------------------------------

def _table(tmp_path: Path, lignes: list) -> Path:
    chemin = tmp_path / "t.json"
    chemin.write_text(json.dumps({"candidats": {"x": lignes}}), encoding="utf-8")
    return chemin


def _ligne(**surcharges):
    base = {"institution": "assemblee_nationale", "libelle": "Député", "debut": "1997-06-01",
            "fin": "2002-06-18", "source_url": "https://exemple.fr/a", "verifie_le": "2026-09-11"}
    base.update(surcharges)
    return base


def test_une_ligne_dans_la_couverture_est_refusee(tmp_path):
    """Un trou après la borne est un autre défaut (#859), jamais cette table."""
    with pytest.raises(TableMandatsAnterieursInvalide, match="couverture"):
        charger_table(_table(tmp_path, [_ligne(fin=BORNE_COUVERTURE_AN)]))


def test_une_ligne_sans_source_est_refusee(tmp_path):
    with pytest.raises(TableMandatsAnterieursInvalide, match="source_url"):
        charger_table(_table(tmp_path, [_ligne(source_url="")]))


def test_une_fin_nulle_sans_motif_est_refusee(tmp_path):
    with pytest.raises(TableMandatsAnterieursInvalide, match="fin_non_resolue"):
        charger_table(_table(tmp_path, [_ligne(fin=None)]))


def test_le_senat_n_entre_pas_sans_la_reprise_de_528(tmp_path):
    with pytest.raises(TableMandatsAnterieursInvalide, match="528"):
        charger_table(_table(tmp_path, [_ligne(institution="senat")]))


# ---------------------------------------------------------------------------
# Le champ dérivé sur la fiche
# ---------------------------------------------------------------------------

#: Constat d'absence minimal, pour les tests du champ dérivé (#860).
_CONSTAT = {
    "source_url": "https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept=17264",
    "constate_le": "2026-09-15",
    "methode": "lecture_fiche_sycomore",
}


def _profil(slug, provenance="candidat_declare"):
    return {"id": slug, "meta": {"provenance": provenance}}


def test_un_candidat_relu_recoit_sa_liste():
    table = {"c": {"mandats": [_ligne()], "constat": None}}
    p = _profil("c"); appliquer_mandats_anterieurs(p, table)
    assert p["mandats_anterieurs"] == [_ligne()]
    assert "mandats_anterieurs_non_resolu" not in p
    assert valider_mandats_anterieurs(p) == []


def test_un_candidat_non_relu_le_dit():
    p = _profil("inconnu")
    appliquer_mandats_anterieurs(p, {"c": {"mandats": [], "constat": _CONSTAT}})
    assert p["mandats_anterieurs"] is None
    assert p["mandats_anterieurs_non_resolu"] == {"motif": "non_relu"}
    assert valider_mandats_anterieurs(p) == []


def test_un_candidat_relu_sans_mandat_recoit_une_liste_vide():
    """Relu et vide : « aucun », ce qui n'est pas « non relu » — et le constat
    dit sur quelle source cet « aucun » repose (#860)."""
    p = _profil("c")
    appliquer_mandats_anterieurs(p, {"c": {"mandats": [], "constat": _CONSTAT}})
    assert p["mandats_anterieurs"] == []
    assert p["mandats_anterieurs_constat"] == _CONSTAT


def test_un_membre_de_roster_ne_recoit_rien():
    p = _profil("m", provenance="roster_groupe")
    p["mandats_anterieurs"] = [_ligne()]
    appliquer_mandats_anterieurs(p, {"m": {"mandats": [_ligne()], "constat": None}})
    assert "mandats_anterieurs" not in p and "mandats_anterieurs_non_resolu" not in p


def test_le_champ_est_repose_jamais_fusionne():
    """Une ligne retirée de la table disparaît de la fiche au passage suivant."""
    p = _profil("c")
    appliquer_mandats_anterieurs(p, {"c": {"mandats": [_ligne()], "constat": None}})
    appliquer_mandats_anterieurs(p, {"c": {"mandats": [], "constat": _CONSTAT}})
    assert p["mandats_anterieurs"] == []


def test_validate_profil_refuse_un_null_sans_motif():
    assert valider_mandats_anterieurs({"mandats_anterieurs": None})


# ---------------------------------------------------------------------------
# Le rappel là où passe qui relit un candidat neuf
# ---------------------------------------------------------------------------

def test_une_entree_neuve_rappelle_la_releve_des_mandats_anterieurs():
    """La table ne se met pas à jour seule : l'entrée neuve le dit, avec ou sans slug."""
    import fetch_candidats_declares as fcd

    candidat = fcd.CandidatDeclare(nom="Un Nouveau", parti="Un parti", url=None)
    for slug in ("un-nouveau", None):
        notes = fcd.nouvelle_entree(candidat, "2026-09-11", slug)["notes"]
        assert "raw_data/mandats_anterieurs.json" in notes, slug
        assert "#860" in notes, slug
