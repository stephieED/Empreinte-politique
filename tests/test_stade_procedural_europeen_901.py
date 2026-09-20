"""#901 — le stade d'un dossier européen est publié, et il n'est pas traduit.

Les 383 textes portés européens publiaient `stade_procedural: null`, et le seuil
de `AGENTS.md` §6 les écartait tous. La source le publie pourtant : mesuré le
13/09/2026 sur le dump entier, **20 442 des 23 885 dossiers** portent un
`procedure.stage_reached` (85,6 %), sur **16 valeurs**.

L'indexeur le lisait puis le jetait. Ce lot le conserve, et le normaliseur le
traduit — vers une nomenclature **européenne**, jamais vers un stade français.
C'est l'arbitrage du 13/09/2026, et il tient à un contre-exemple : « Procedure
completed » n'est pas `promulgue`, puisque « Procedure rejected » est une
procédure achevée elle aussi.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from normalize_parltrack_dumps import (  # noqa: E402
    STADE_UE_PAR_LIBELLE_SOURCE,
    _make_texte_porte,
    _stade_procedural_ue,
)
from schema_pivot import (  # noqa: E402
    KNOWN_STADES_PROCEDURAUX,
    STADES_PROCEDURAUX_AN,
    STADES_PROCEDURAUX_UE,
)


# --------------------------------------------------------------------------
# La nomenclature
# --------------------------------------------------------------------------

def test_les_deux_nomenclatures_ne_se_recouvrent_pas():
    """Un stade européen ne doit jamais pouvoir passer pour un stade français.

    C'est ce que le préfixe `ue_` garantit dans la valeur elle-même : le seuil
    §6, qui est un rang dans la liste française, ne peut pas s'appliquer à l'une
    d'elles par distraction.
    """
    assert not (STADES_PROCEDURAUX_AN & STADES_PROCEDURAUX_UE)
    assert all(s.startswith("ue_") for s in STADES_PROCEDURAUX_UE)
    assert not any(s.startswith("ue_") for s in STADES_PROCEDURAUX_AN)


def test_le_frozenset_public_est_l_union_des_deux():
    assert KNOWN_STADES_PROCEDURAUX == STADES_PROCEDURAUX_AN | STADES_PROCEDURAUX_UE


def test_la_table_couvre_les_seize_valeurs_relevees():
    """Seize, relevées sur le dump entier — pas sur un échantillon.

    La première mesure, sur 20 000 dossiers, en donnait 15 et une couverture de
    91,3 %. Le dump en porte 23 885, 16 valeurs, 85,6 %.
    """
    assert len(STADE_UE_PAR_LIBELLE_SOURCE) == 16


@pytest.mark.parametrize("libelle, valeur", sorted(STADE_UE_PAR_LIBELLE_SOURCE.items()))
def test_chaque_ligne_de_la_table_vise_un_stade_declare(libelle, valeur):
    assert valeur in STADES_PROCEDURAUX_UE, (
        f"{libelle!r} → {valeur!r}, qui n'est pas dans `STADES_PROCEDURAUX_UE` : "
        "`validate_profil` refuserait le profil (AGENTS.md §4).")


def test_aucun_stade_declare_n_est_orphelin():
    """L'inverse : une valeur du frozenset que rien ne produit est du bruit."""
    assert set(STADE_UE_PAR_LIBELLE_SOURCE.values()) == STADES_PROCEDURAUX_UE


def test_une_procedure_achevee_n_est_pas_une_promulgation():
    """LE contre-exemple qui fonde l'arbitrage.

    « Procedure completed » recouvre l'adoption ET l'échec — « Procedure
    rejected » est une procédure achevée. La ranger sous `promulgue` publierait
    comme adopté un texte qui a pu être rejeté (§2 règle 2).
    """
    assert STADE_UE_PAR_LIBELLE_SOURCE["Procedure completed"] != "promulgue"
    assert STADE_UE_PAR_LIBELLE_SOURCE["Procedure completed"] not in STADES_PROCEDURAUX_AN


# --------------------------------------------------------------------------
# La résolution, et ses trois cas
# --------------------------------------------------------------------------

def test_un_libelle_connu_donne_son_stade_sans_motif():
    stade, motif = _stade_procedural_ue({"stade_source": "Procedure rejected"})

    assert stade == "ue_procedure_rejetee"
    assert motif is None


@pytest.mark.parametrize("absent", [None, "", {}])
def test_une_source_sans_stade_le_declare(absent):
    """14,4 % des dossiers du dump. Une absence de la source, pas une nôtre."""
    stade, motif = _stade_procedural_ue({"stade_source": absent})

    assert stade is None
    assert motif == {"motif": "source_sans_stade"}


def test_un_libelle_inconnu_est_declare_avec_sa_valeur_recue():
    """Ni deviné, ni fatal.

    Deviner rangerait un fait sous une étiquette choisie par ressemblance ;
    lever ferait tomber un run entier sur un libellé ajouté en amont. Le
    conserver dans le motif est ce qui permet de l'ajouter à la table ensuite.
    """
    stade, motif = _stade_procedural_ue({"stade_source": "Awaiting alien invasion"})

    assert stade is None
    assert motif == {"motif": "stade_source_inconnu",
                     "valeur_source": "Awaiting alien invasion"}


# --------------------------------------------------------------------------
# L'entrée publiée
# --------------------------------------------------------------------------

def test_le_texte_porte_publie_le_stade_et_pas_de_motif():
    entree = _make_texte_porte({"titre": "Statut de la Cour", "reference": "2011/0901(COD)",
                                "stade_source": "Awaiting Parliament 2nd reading"})

    assert entree["stade_procedural"] == "ue_attente_parlement_2e_lecture"
    assert "stade_procedural_non_resolu" not in entree


def test_le_texte_porte_sans_stade_porte_son_motif():
    entree = _make_texte_porte({"titre": "X", "reference": "2011/0901(COD)"})

    assert entree["stade_procedural"] is None
    assert entree["stade_procedural_non_resolu"] == {"motif": "source_sans_stade"}


def test_le_sort_reste_non_resolu_et_ce_n_est_pas_le_stade():
    """#743 : le stade encode l'avancement, le sort l'issue. Publier l'un ne
    renseigne pas l'autre, et le dump ne porte toujours aucune issue."""
    entree = _make_texte_porte({"titre": "X", "stade_source": "Procedure completed"})

    assert entree["stade_procedural"] == "ue_procedure_achevee"
    assert entree["sort"] is None
    assert entree["sort_non_resolu"] == {"motif": "source_sans_sort"}
