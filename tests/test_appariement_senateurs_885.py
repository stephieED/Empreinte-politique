"""#885 — relier un profil publié à son matricule sénatorial, ou refuser.

`raw_data/correspondance_acteurs_an.json` porte déjà un champ
`identifiants.senat` sur ses 1 196 entrées, **nul sur les 1 196**. Il attendait
une source ; il n'en fallait pas une seconde.

Trois comportements sont gelés ici, et le dernier compte plus que les deux
autres :

1. **Les particules.** La source range « Dominique de Legge » en
   `senprenomuse = "Dominique"`, `sennomuse = "de Legge"`. Un découpage du nom
   publié sur son dernier mot cherche « Legge » précédé de « Dominique de », et
   ne trouve rien.
2. **Le refus d'inventer.** Deux sénateurs de même nom **et** même date de
   naissance ne se tranchent pas automatiquement (#525).
3. **L'homonyme que le nom seul ne voit pas.** `jean-louis-masson` publié est
   né le 05/02/1954 ; le sénateur mosellan homonyme, `PA2116` chez AMO30, est né
   le 25/03/1947. Aucun des deux n'est ambigu côté Sénat — le nom y est unique.
   C'est le **corpus publié** qui porte l'homonyme, et seule la date de
   naissance le montre. Le nom seul produisait **2 faux positifs sur 38**.

Mesuré le 13/09/2026 : **36 appariements, 2 homonymes écartés, 0 ambigu** sur
les 1 196 profils publiés. Zéro ambiguïté est une mesure sur ce corpus, pas une
garantie : le refus reste armé, et ces tests le vérifient.

Toutes les doublures sont construites ici (AGENTS.md §3, #457/#473/#488).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from appariement_senateurs import (  # noqa: E402
    ORIGINE_APPARIEMENT,
    AppariementAmbigu,
    apparier,
    indexer_senateurs,
    normaliser,
    proposer_appariements,
)


def _sen(matricule, prenom, nom, naissance="1950-01-01"):
    return {"senmat": matricule, "senprenomuse": prenom, "sennomuse": nom,
            "sendatnai": f"{naissance} 00:00:00" if naissance else None}


def _entree(nom_complet, senat=None, naissance="1950-01-01"):
    return {"identifiants": {"an": "PA1", "senat": senat},
            "etat_civil": {"nom_complet": nom_complet, "date_naissance": naissance}}


# ---------------------------------------------------------------------------
# La normalisation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("brut,attendu", [
    ("Jean-Luc", "jeanluc"),
    ("Jean Luc", "jeanluc"),
    ("Mélenchon", "melenchon"),
    ("de Legge", "delegge"),
    ("O'Brien", "obrien"),
    (None, ""),
])
def test_la_normalisation_compare_ce_qui_est_comparable(brut, attendu):
    """La source n'est pas régulière sur les traits d'union ni les accents ;
    l'appariement ne peut pas l'être non plus."""
    assert normaliser(brut) == attendu


# ---------------------------------------------------------------------------
# Les particules — le seul échec mesuré
# ---------------------------------------------------------------------------

def test_un_nom_a_particule_est_apparie():
    """`sennomuse` vaut « de Legge », pas « Legge ». Un découpage sur le dernier
    mot du nom publié manquerait tous les noms à particule."""
    index = indexer_senateurs([_sen("08034U", "Dominique", "de Legge")])

    assert apparier("Dominique de Legge", "1950-01-01", index) == "08034U"


def test_tous_les_decoupages_sont_essayes():
    """Un prénom composé range la coupure ailleurs — et le module ne sait pas
    d'avance de quel côté elle tombe."""
    index = indexer_senateurs([_sen("1", "Marie Claire", "du Pont")])

    assert apparier("Marie Claire du Pont", "1950-01-01", index) == "1"


def test_un_nom_simple_est_apparie():
    index = indexer_senateurs([_sen("86039K", "Jean-Luc", "Mélenchon")])

    assert apparier("Jean-Luc Mélenchon", "1950-01-01", index) == "86039K"


# ---------------------------------------------------------------------------
# Le refus
# ---------------------------------------------------------------------------

def test_deux_senateurs_pour_un_nom_ne_se_tranchent_pas():
    """Un identifiant faux rattacherait la carrière de quelqu'un d'autre à une
    fiche publiée. Personne ne le verrait ensuite."""
    index = indexer_senateurs([_sen("1", "Jean", "Dupont"), _sen("2", "Jean", "Dupont")])

    with pytest.raises(AppariementAmbigu) as echec:
        apparier("Jean Dupont", "1950-01-01", index)

    assert "1" in str(echec.value) and "2" in str(echec.value)


def test_le_refus_dit_ou_trancher():
    """Un refus qui ne dit pas quoi faire se contourne."""
    index = indexer_senateurs([_sen("1", "Jean", "Dupont"), _sen("2", "Jean", "Dupont")])

    with pytest.raises(AppariementAmbigu) as echec:
        apparier("Jean Dupont", "1950-01-01", index)

    assert "correspondance_acteurs_an.json" in str(echec.value)


def test_aucun_senateur_n_est_le_cas_normal():
    """1 158 des 1 196 profils publiés n'ont aucun passé sénatorial. Lever
    ferait de la normalité une erreur."""
    index = indexer_senateurs([_sen("1", "Jean", "Dupont")])

    assert apparier("Gabriel Attal", "1950-01-01", index) is None
    assert apparier("", "1950-01-01", index) is None


# ---------------------------------------------------------------------------
# La proposition, qui n'écrit rien
# ---------------------------------------------------------------------------

def test_la_proposition_ne_modifie_pas_les_correspondances():
    """Une proposition se lit avant de s'écrire."""
    correspondances = {"jean-luc-melenchon": _entree("Jean-Luc Mélenchon")}
    avant = dict(correspondances["jean-luc-melenchon"]["identifiants"])

    proposer_appariements(correspondances, [_sen("86039K", "Jean-Luc", "Mélenchon")])

    assert correspondances["jean-luc-melenchon"]["identifiants"] == avant


def test_un_identifiant_deja_renseigne_n_est_jamais_recalcule():
    """Il a pu être **relu** par un humain. Un appariement automatique qui
    l'écrase défait précisément le travail qu'il faut protéger (#715)."""
    correspondances = {"bruno-retailleau": _entree("Bruno Retailleau", senat="RELU42")}

    appariements, ambigus, deja = proposer_appariements(
        correspondances, [_sen("04033B", "Bruno", "Retailleau")])

    assert appariements == {}
    assert deja == ["bruno-retailleau"]
    assert ambigus == []


def test_les_ambigus_sont_nommes_et_non_apparies():
    """Ils sortent de la proposition par une liste, pas par une exception : un
    corpus qui en porte un ne doit pas empêcher les 37 autres d'être écrits."""
    correspondances = {
        "jean-dupont": _entree("Jean Dupont"),
        "jean-luc-melenchon": _entree("Jean-Luc Mélenchon"),
    }

    appariements, ambigus, _ = proposer_appariements(correspondances, [
        _sen("1", "Jean", "Dupont"), _sen("2", "Jean", "Dupont"),
        _sen("86039K", "Jean-Luc", "Mélenchon"),
    ])

    assert appariements == {"jean-luc-melenchon": "86039K"}
    assert ambigus == ["jean-dupont"]


def test_un_appariement_automatique_gele_sans_prouver():
    """Le même régime que les 699 entrées dérivées de #715 : il fixe
    l'identifiant, il ne l'établit pas. La relecture reste due."""
    assert ORIGINE_APPARIEMENT == "derivee"


# ---------------------------------------------------------------------------
# L'homonyme — ce que le nom seul ne voit pas
# ---------------------------------------------------------------------------

def test_un_homonyme_de_date_differente_ne_s_apparie_pas():
    """Le cas réel `jean-louis-masson` : deux acteurs AMO30 portent ce nom,
    `PA2116` né le 25/03/1947 — Mosellan, député **puis** sénateur — et
    `PA346218` né le 05/02/1954, qui est le profil publié. Le nom seul donnait
    au second les trois mandats sénatoriaux du premier.

    Aucun des deux n'est « ambigu » côté Sénat : le nom y est unique. C'est le
    **corpus publié** qui porte l'homonyme."""
    index = indexer_senateurs([_sen("01060R", "Jean Louis", "Masson", "1947-03-25")])

    assert apparier("Jean-Louis Masson", "1954-02-05", index) is None
    assert apparier("Jean-Louis Masson", "1947-03-25", index) == "01060R"


def test_le_refus_ne_dit_pas_que_le_nom_n_a_pas_de_senateur():
    """`PA2116` n'est pas publié aujourd'hui. Le jour où il le sera, `01060R`
    sera son appariement légitime — le `null` porte sur **ce profil-ci**, pas
    sur le nom."""
    index = indexer_senateurs([_sen("01060R", "Jean Louis", "Masson", "1947-03-25")])
    correspondances = {
        "jean-louis-masson": _entree("Jean-Louis Masson", naissance="1954-02-05"),
        "jean-louis-masson-1947": _entree("Jean-Louis Masson", naissance="1947-03-25"),
    }

    appariements, ambigus, _ = proposer_appariements(
        correspondances, [_sen("01060R", "Jean Louis", "Masson", "1947-03-25")])

    assert appariements == {"jean-louis-masson-1947": "01060R"}
    assert ambigus == []


def test_sans_date_de_naissance_publiee_rien_ne_s_apparie():
    """Il ne resterait que le nom, et le nom a produit 2 faux positifs sur 38.
    Un appariement qu'on ne peut pas prouver ne se fait pas (§2 règle 5)."""
    index = indexer_senateurs([_sen("86039K", "Jean-Luc", "Mélenchon", "1951-08-19")])

    assert apparier("Jean-Luc Mélenchon", None, index) is None


def test_un_senateur_sans_date_de_naissance_n_entre_pas_dans_l_index():
    """Il ne serait appariable que par son nom."""
    index = indexer_senateurs([_sen("X", "Jean", "Dupont", None)])

    assert index == {}
    assert apparier("Jean Dupont", "1950-01-01", index) is None


def test_l_ambiguite_reste_armee_malgre_la_date():
    """Deux sénateurs de même nom **et** même date restent un refus : zéro
    ambiguïté est une mesure sur ce corpus, pas une garantie."""
    index = indexer_senateurs([_sen("1", "Jean", "Dupont", "1950-01-01"),
                               _sen("2", "Jean", "Dupont", "1950-01-01")])

    with pytest.raises(AppariementAmbigu):
        apparier("Jean Dupont", "1950-01-01", index)
