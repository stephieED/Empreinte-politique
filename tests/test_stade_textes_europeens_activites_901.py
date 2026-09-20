"""#901 — la SECONDE fabrique de textes portés européens publie elle aussi son stade.

Le lot du stade avait corrigé `_make_texte_porte`, qui construit une entrée à
partir d'un dossier dont la personne est rapporteure. Le run du 14/09/2026 a
montré ce qu'il avait manqué : **12 des 383** textes portés européens portaient
un stade, soit 3 %. Les 371 autres viennent de `_make_texte_porte_activite`,
qui écrivait `stade_procedural: None` en dur.

Deux fabriques, une seule corrigée — la même erreur que sur les motifs de
suspension le même jour, où `GroupeSuspendu.preuve` avait été traitée et
`groupes_config.resume_suspension` oubliée. **Chercher où un champ est jeté ne
suffit pas : il faut chercher tous les endroits où l'objet est fabriqué.**

## Ce que ce fichier ne pouvait pas voir, et qui a coûté un second run

Corriger la seconde fabrique n'a rien changé au corpus : le run suivant a publié
**12 stades sur 383**, le même chiffre. Ces tests-ci passaient pourtant — parce
qu'ils appellent les fabriques sur des entrées **que le test construit**, avec
`dossiers` dedans. Or la chaîne réelle ne leur remet jamais ce champ :
`build_activities_index` le jetait à la projection, une étape plus haut.

Ils vérifient donc que les fabriques savent lire un champ qu'elles ne reçoivent
pas. C'est utile, et ce n'est pas suffisant : la chaîne de bout en bout est
tenue par `tests/test_projection_activites_conserve_dossiers_901.py`, qui part
d'un dump et ne fabrique aucune entrée intermédiaire.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from normalize_parltrack_dumps import (  # noqa: E402
    _make_texte_porte,
    _make_texte_porte_activite,
    _reference_dossier_activite,
)


def _activite(**extra):
    base = {"titre": "Report on X", "date": "2016-11-22T19:07:00",
            "dossiers": ["1995/2236(COS)"]}
    base.update(extra)
    return base


# --------------------------------------------------------------------------
# La référence que l'activité vise
# --------------------------------------------------------------------------

def test_la_reference_se_lit_dans_dossiers_au_pluriel():
    """Mesuré le 14/09/2026 sur les 4 585 fiches du dump : 9 593 `REPORT` sur 9 935.

    L'entrée est fabriquée ici : ce test dit que la fonction sait lire le champ,
    pas qu'elle le reçoit. Ce second point est ailleurs (voir l'en-tête).
    """
    assert _reference_dossier_activite(_activite()) == "1995/2236(COS)"


def test_une_activite_visant_plusieurs_dossiers_retient_le_premier():
    entree = _activite(dossiers=["2011/0901(COD)", "2017/2070(INI)"])

    assert _reference_dossier_activite(entree) == "2011/0901(COD)"


@pytest.mark.parametrize("valeur", [None, [], "", {}])
def test_une_activite_sans_dossier_ne_rend_aucune_reference(valeur):
    assert _reference_dossier_activite(_activite(dossiers=valeur)) is None


# --------------------------------------------------------------------------
# Le stade, et ses trois absences déclarées
# --------------------------------------------------------------------------

def test_un_dossier_connu_donne_son_stade():
    entree = _make_texte_porte_activite(
        "rapport", _activite(), {"1995/2236(COS)": "Procedure completed"})

    assert entree["stade_procedural"] == "ue_procedure_achevee"
    assert "stade_procedural_non_resolu" not in entree


def test_un_dossier_absent_de_l_index_declare_l_absence_de_la_source():
    entree = _make_texte_porte_activite("rapport", _activite(), {})

    assert entree["stade_procedural"] is None
    assert entree["stade_procedural_non_resolu"] == {"motif": "source_sans_stade"}


def test_une_activite_sans_dossier_a_son_propre_motif():
    """Distinct de `source_sans_stade` : il n'y a rien à interroger, ce n'est
    pas la source qui se tait sur un dossier connu."""
    entree = _make_texte_porte_activite("rapport", _activite(dossiers=None), {})

    assert entree["stade_procedural"] is None
    assert entree["stade_procedural_non_resolu"] == {"motif": "activite_sans_dossier"}


def test_un_stade_inconnu_conserve_le_libelle_recu():
    entree = _make_texte_porte_activite(
        "rapport", _activite(), {"1995/2236(COS)": "Awaiting alien invasion"})

    assert entree["stade_procedural_non_resolu"] == {
        "motif": "stade_source_inconnu", "valeur_source": "Awaiting alien invasion"}


def test_sans_index_du_tout_l_absence_reste_declaree():
    """L'appelant ne construit l'index que si une activité portée existe ;
    l'appel sans index ne doit pas lever."""
    entree = _make_texte_porte_activite("rapport", _activite())

    assert entree["stade_procedural"] is None
    assert "stade_procedural_non_resolu" in entree


# --------------------------------------------------------------------------
# Les deux fabriques publient la même forme
# --------------------------------------------------------------------------

def test_les_deux_fabriques_publient_reference_dossier():
    """Sans elle, les 383 textes portés européens ne rejoignaient aucun index —
    besoin remonté par l'interface. Le champ porte le même nom que sur un vote
    (`scrutin_non_resolu.reference_dossier`) : lui en donner deux obligerait
    chaque consommateur à connaître le chemin qui a produit l'entrée.
    """
    depuis_activite = _make_texte_porte_activite("rapport", _activite(), {})
    depuis_dossier = _make_texte_porte({"titre": "Y", "reference": "2017/2070(INI)"})

    assert depuis_activite["reference_dossier"] == "1995/2236(COS)"
    assert depuis_dossier["reference_dossier"] == "2017/2070(INI)"


def test_les_deux_fabriques_portent_les_memes_cles():
    """Une fiche ne doit pas distinguer deux textes selon le chemin qui les a
    produits. `nature_texte` est la seule clé propre aux activités : elle dit
    la nature d'une résolution, qu'un dossier rapporteur n'a pas.
    """
    activite = set(_make_texte_porte_activite("rapport", _activite(), {}))
    dossier = set(_make_texte_porte({"titre": "Y", "reference": "R"}))

    assert dossier - activite == set()
    assert activite - dossier == {"nature_texte"}
