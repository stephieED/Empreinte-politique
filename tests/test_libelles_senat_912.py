"""#912 — le libellé d'un organe sénatorial se lit sur la colonne complète.

Trois défauts visibles à l'écran, une seule cause : `libcom` était lu sur
`evelib`, l'abrégé. La table en porte quatre, et elles ne disent pas la même
chose — `evelic` le code (`AFCL`), `evelib` l'abrégé (`Culture`, coupé à 60
caractères), `evelil` le complet en MAJUSCULES et vide sur 109 des 571 lignes,
`libcomlilmin` le complet en casse normalisée, rempli sur 568.

C'est le piège des colonnes `eve*` déjà payé sur `orgext` en instruisant #885,
et jamais appliqué à `libcom` : **les colonnes d'un même préfixe ne portent pas
la même chose d'une table à l'autre du même jeu**. Les 77 tests sénat passaient
sans rien geler de la colonne lue — c'est ce silence que ce fichier ferme.

Le mojibake est le second volet, et il a une autre cause : la source encode en
UTF-8 des octets cp1252 comme s'ils étaient du latin-1. `U+0092` est alors une
séquence UTF-8 **valide**, que `errors="replace"` ne voit pas passer.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import senat_mandats  # noqa: E402
from senat_mandats import _index_libelles, _libelle_le_plus_complet  # noqa: E402
from senat_opendata import reparer_mojibake  # noqa: E402


# --------------------------------------------------------------------------
# Le choix de colonne
# --------------------------------------------------------------------------

def test_la_colonne_complete_gagne_sur_l_abrege():
    ligne = {"libcomlilmin": "commission de la culture, de l'éducation et du sport",
             "evelib": "Culture",
             "evelil": "COMMISSION DE LA CULTURE"}

    assert _libelle_le_plus_complet(ligne, ("libcomlilmin", "evelib", "evelil")) == (
        "Commission de la culture, de l'éducation et du sport")


def test_l_ordre_est_celui_de_l_appelant_et_le_repli_joue():
    """109 lignes de `libcom` ont `evelil` vide, 3 ont `libcomlilmin` vide."""
    ligne = {"libcomlilmin": "", "evelib": "Culture", "evelil": ""}

    assert _libelle_le_plus_complet(ligne, ("libcomlilmin", "evelib", "evelil")) == "Culture"


def test_sans_aucune_colonne_remplie_le_libelle_est_absent_et_non_invente():
    """§2 règle 5 : une absence se déclare. `decouper_sur_renommages` la reprend
    en `libelle_non_resolu`, ce qui est le bon comportement."""
    ligne = {"libcomlilmin": None, "evelib": "   ", "evelil": ""}

    assert _libelle_le_plus_complet(ligne, ("libcomlilmin", "evelib", "evelil")) is None


def test_seule_l_initiale_est_relevee():
    """La source normalise en minuscules ; recapitaliser le reste abîmerait les
    sigles et les noms propres — « Union européenne », « La Poste »."""
    ligne = {"lil": "projet de loi relatif à l'entreprise publique La Poste"}

    assert _libelle_le_plus_complet(ligne, ("lil",)) == (
        "Projet de loi relatif à l'entreprise publique La Poste")


def test_les_espaces_multiples_sont_une_scorie_de_saisie():
    ligne = {"lil": "diffusion et  protection de la création"}

    assert _libelle_le_plus_complet(ligne, ("lil",)) == "Diffusion et protection de la création"


def test_l_index_borne_chaque_libellé_et_prend_le_plus_complet():
    lignes = [
        {"orgcod": "AFCL", "d": "2023-10-04", "f": "2024-01-17",
         "libcomlilmin": "commission de la culture et de la communication", "evelib": "Culture"},
        {"orgcod": "AFCL", "d": "2024-01-18", "f": None,
         "libcomlilmin": "commission de la culture, de la communication et du sport",
         "evelib": "Culture"},
    ]

    index = _index_libelles(lignes, "orgcod", "d", "f", "libcomlilmin", "evelib")

    assert [e["libelle"] for e in index["AFCL"]] == [
        "Commission de la culture et de la communication",
        "Commission de la culture, de la communication et du sport",
    ]
    assert [e["fin"] for e in index["AFCL"]] == ["2024-01-17", None]


# --------------------------------------------------------------------------
# Le mojibake
# --------------------------------------------------------------------------

@pytest.mark.parametrize("abime, repare", [
    ("l\x92Union européenne", "l’Union européenne"),
    ("mise en \x9cuvre", "mise en œuvre"),
    ("\x93citation\x94", "“citation”"),
])
def test_les_typographies_cp1252_sont_rendues(abime, repare):
    assert reparer_mojibake(abime) == repare


def test_un_texte_sain_ressort_identique():
    sain = "Commission de la culture, de l'éducation et du sport"

    assert reparer_mojibake(sain) is sain


def test_un_c1_que_cp1252_ne_definit_pas_n_est_pas_devine():
    """cp1252 laisse cinq positions indéfinies. Les remplacer par l'apostrophe
    la plus probable produirait un texte qui a l'air juste (§2 règle 5)."""
    assert reparer_mojibake("a\x81b") == "a\x81b"


# --------------------------------------------------------------------------
# Le gel : la cause, pas seulement ses symptômes
# --------------------------------------------------------------------------

def test_libcom_est_lu_sur_sa_colonne_complete_en_premier():
    """Le défaut de #912 tenait à un seul argument, et rien ne le gelait.

    Ce test lit le code : il capture les colonnes que `composer_mandats` passe
    pour `libcom`, et refuse que l'abrégé repasse devant.
    """
    captures: list[tuple[str, ...]] = []
    vrai = senat_mandats._index_libelles

    def espion(lignes, cle, debut, fin, *libelles):
        if debut == "libcomdatdeb":
            captures.append(libelles)
        return vrai(lignes, cle, debut, fin, *libelles)

    senat_mandats._index_libelles = espion
    try:
        senat_mandats.composer_mandats({}, "00000A")
    finally:
        senat_mandats._index_libelles = vrai

    assert captures, "composer_mandats n'indexe plus `libcom` — le gel ne protège plus rien"
    assert captures[0][0] == "libcomlilmin", (
        f"`libcom` est lu sur {captures[0][0]!r} en premier. `evelib` est l'abrégé : "
        "il publie « Culture » pour la commission de la culture, de l'éducation, de "
        "la communication et du sport, et coupe à 60 caractères (#912).")
