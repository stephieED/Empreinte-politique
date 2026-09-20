"""#885 — le nom d'un organe **à la date**, et ce qu'un renommage coupe en deux.

C'est le défaut qui a fait échouer #878 : le référentiel de l'Assemblée ne porte
qu'un libellé par organe sénatorial — l'actuel — et un code interne resté à
l'ancien nom. Publier « Les Républicains » pour une appartenance de 2012 est
faux, et le Sénat, lui, publie la table qui permet de ne pas l'être.

Les cas nommés ici sont **réels**, relevés le 13/09/2026 sur l'export :

  - `jean-luc-melenchon`, 28/11/2008 → 07/01/2010 : « Groupe CRC-SPG », que
    l'Assemblée rendrait « Groupe CRCE - Kanaky ». Le libellé commence le jour
    même de son arrivée, le groupe ayant été renommé pour l'accueillir ;
  - `bruno-retailleau`, 07/11/2012 → 21/10/2024 : **deux** entrées, « Groupe
    UMP » jusqu'au 01/06/2015 puis « Groupe Les Républicains », et ses fonctions
    suivent le découpage ;
  - 17 organes de groupe d'études n'ont **aucun** libellé borné, et leur nom ne
    se jette pas pour autant : `grpsenami` le porte, non daté, et l'entrée le
    déclare.

Toutes les doublures sont construites ici : aucun test ne lit l'export réel, le
corpus publié, ni le réseau (AGENTS.md §3, #457/#473/#488).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from senat_mandats import (  # noqa: E402
    FAMILLES,
    composer_mandats,
    decouper_sur_renommages,
)


def _libelle(nom, debut, fin):
    return {"libelle": nom, "debut": debut, "fin": fin}


# ---------------------------------------------------------------------------
# Le découpage sur renommage
# ---------------------------------------------------------------------------

def test_un_renommage_coupe_l_appartenance_en_deux():
    """Le cas `bruno-retailleau`. Une entrée unique sous le nom le plus récent
    perdrait ce que la source sait (§2 règle 2)."""
    entrees = decouper_sur_renommages(
        "2012-11-07", "2024-10-21",
        [_libelle("Groupe UMP", "2002-12-11", "2015-06-01"),
         _libelle("Groupe Les Républicains", "2015-06-02", None)],
    )

    assert [(e["libelle"], e["debut"], e["fin"]) for e in entrees] == [
        ("Groupe UMP", "2012-11-07", "2015-06-01"),
        ("Groupe Les Républicains", "2015-06-02", "2024-10-21"),
    ]


def test_chaque_entree_est_bornee_a_l_intersection():
    """Ni la période d'appartenance, ni celle du libellé : leur recouvrement.
    Publier les bornes du libellé ferait commencer le mandat avant l'arrivée."""
    entrees = decouper_sur_renommages(
        "2008-11-28", "2010-01-07",
        [_libelle("Groupe CRC-SPG", "2008-11-28", "2011-09-30")],
    )

    assert entrees == [{"libelle": "Groupe CRC-SPG",
                        "debut": "2008-11-28", "fin": "2010-01-07"}]


def test_un_libelle_qui_ne_recouvre_pas_est_ignore():
    """Le nom d'avant l'arrivée n'est pas le nom du mandat."""
    entrees = decouper_sur_renommages(
        "2008-11-28", "2010-01-07",
        [_libelle("Groupe socialiste", "1900-01-01", "2008-11-27"),
         _libelle("Groupe CRC-SPG", "2008-11-28", "2011-09-30")],
    )

    assert [e["libelle"] for e in entrees] == ["Groupe CRC-SPG"]


def test_aucune_date_n_est_fabriquee_par_la_jointure():
    """Quand les deux côtés sont muets, la borne reste absente. On ne comble
    jamais une date avec celle de l'autre côté (§2 règle 5)."""
    entrees = decouper_sur_renommages(None, None, [_libelle("Groupe socialiste", None, None)])

    assert entrees == [{"libelle": "Groupe socialiste", "debut": None, "fin": None}]


def test_une_appartenance_sans_debut_garde_son_absence():
    """1 064 appartenances sur 3 213 n'ont pas de date de début — un tiers. Ce
    n'est pas un cas rare à traiter en passant."""
    entrees = decouper_sur_renommages(
        None, "2000-04-27", [_libelle("Groupe socialiste", "1900-01-01", "2011-09-30")])

    assert entrees[0]["debut"] is None
    assert entrees[0]["fin"] == "2000-04-27"


# ---------------------------------------------------------------------------
# Quand la source ne borne aucun libellé
# ---------------------------------------------------------------------------

def test_un_libelle_courant_sert_de_repli_et_se_declare_non_date():
    """17 organes de groupe d'études n'ont aucune ligne dans `libgrpsen`.
    Publier `null` jetterait un nom que la source porte ; le publier sans rien
    dire laisserait croire qu'il est daté."""
    entrees = decouper_sur_renommages(
        "2004-10-01", "2011-09-30", [],
        libelle_courant="Groupe d'études Monde combattant et mémoire")

    assert entrees[0]["libelle"] == "Groupe d'études Monde combattant et mémoire"
    assert entrees[0]["libelle_date"] is False
    assert "libelle_non_resolu" not in entrees[0]


def test_sans_aucun_libelle_l_appartenance_reste_publiee_et_se_declare():
    """L'appartenance est un fait même quand son nom est introuvable. Une entrée
    nommée `None` se voit ; une entrée absente ne se voit pas."""
    entrees = decouper_sur_renommages("2004-11-01", "2007-12-31", [], libelle_courant=None)

    assert entrees == [{"libelle": None, "debut": "2004-11-01",
                        "fin": "2007-12-31", "libelle_non_resolu": True}]


# ---------------------------------------------------------------------------
# La composition complète
# ---------------------------------------------------------------------------

def _tables_retailleau():
    """Le cas réel, réduit à ce que le test vérifie."""
    return {
        "elusen": [
            {"senmat": "04033B", "eludatdeb": "2020-10-01 00:00:00",
             "eludatfin": "2024-10-21 00:00:00", "etadebmancod": "REN2",
             "etafinmancod": "FINMEMGVT", "dptnum": "850"},
        ],
        "memgrppol": [
            {"senmat": "04033B", "memgrppolid": "1", "grppolcod": "LR",
             "typapppolcod": "N", "memgrppoldatdeb": "2012-11-07 00:00:00",
             "memgrppoldatfin": "2024-10-21 00:00:00"},
            {"senmat": "04033B", "memgrppolid": "2", "grppolcod": "LR",
             "typapppolcod": "R", "memgrppoldatdeb": "2011-10-01 00:00:00",
             "memgrppoldatfin": "2012-11-06 00:00:00"},
        ],
        "libgrppol": [
            {"grppolcod": "LR", "evelib": "Groupe UMP",
             "libgrppoldatdeb": "2002-12-11 00:00:00", "libgrppoldatfin": "2015-06-01 00:00:00"},
            {"grppolcod": "LR", "evelib": "Groupe Les Républicains",
             "libgrppoldatdeb": "2015-06-02 00:00:00", "libgrppoldatfin": None},
        ],
        "grppol": [{"grppolcod": "LR", "grppollibcou": "Groupe Les Républicains"}],
        "typapppol": [
            {"typapppolcod": "N", "typapppollib": "Membre"},
            {"typapppolcod": "R", "typapppollib": "Rattaché"},
        ],
        "fonmemgrppol": [
            {"memgrppolid": "1", "fongrppolcod": "PRESPOL",
             "fonmemgrppoldatdeb": "2014-10-07 00:00:00", "fonmemgrppoldatfin": None},
        ],
        "fongrppol": [{"fongrppolcod": "PRESPOL", "fongrppollib": "Président"}],
    }


def test_le_type_d_appartenance_est_publie():
    """Rattaché n'est pas membre, et la source le dit. Confondre les deux
    publierait une appartenance que l'intéressé n'avait pas."""
    mandats = composer_mandats(_tables_retailleau(), "04033B")

    rattache = [m for m in mandats if m.get("type_appartenance_code") == "R"]
    assert len(rattache) == 1
    assert rattache[0]["type_appartenance"] == "Rattaché"
    assert rattache[0]["label"] == "Groupe UMP"


def test_les_fonctions_suivent_le_decoupage():
    """Une présidence commencée en 2014 ne ressort pas sur l'entrée « Groupe Les
    Républicains » seulement : elle recouvre les deux, et chaque entrée porte ce
    qui la recouvre."""
    mandats = composer_mandats(_tables_retailleau(), "04033B")
    groupes = {(m["label"], m["debut"]): m for m in mandats
               if m["famille"] == "groupe_politique"}

    umpc = groupes[("Groupe UMP", "2012-11-07")]
    lr = groupes[("Groupe Les Républicains", "2015-06-02")]
    assert [f["libelle"] for f in umpc["fonctions"]] == ["Président"]
    assert [f["libelle"] for f in lr["fonctions"]] == ["Président"]
    # …mais pas sur l'appartenance de 2011, antérieure à la présidence.
    assert groupes[("Groupe UMP", "2011-10-01")]["fonctions"] == []


def test_le_mandat_parlementaire_publie_ses_motifs():
    """« FINMEMGVT » dit pourquoi un mandat s'arrête. C'est un fait que rien
    d'autre dans le corpus ne porte."""
    mandats = composer_mandats(_tables_retailleau(), "04033B")

    mandat = next(m for m in mandats if m["famille"] == "mandat_parlementaire")
    assert mandat["motif_debut"] == "REN2"
    assert mandat["motif_fin"] == "FINMEMGVT"
    assert mandat["debut"] == "2020-10-01"


def test_un_matricule_inconnu_rend_une_liste_vide():
    """Pas une exception : c'est à l'appelant de décider si c'est un fait ou un
    défaut d'appariement."""
    assert composer_mandats(_tables_retailleau(), "00000X") == []


def test_les_entrees_sans_date_trient_en_dernier():
    """Une date absente n'est pas « avant tout » : elle est inconnue, et la
    mettre en tête ferait lire un ordre qui n'existe pas."""
    tables = _tables_retailleau()
    tables["memgrppol"].append(
        {"senmat": "04033B", "memgrppolid": "3", "grppolcod": "LR",
         "typapppolcod": "N", "memgrppoldatdeb": None, "memgrppoldatfin": None})

    mandats = composer_mandats(tables, "04033B")

    assert mandats[-1]["debut"] is None


def test_une_sentinelle_ne_devient_pas_une_borne_de_mandat():
    """`1900-01-01` dit « depuis toujours ». Publiée, elle ferait commencer une
    appartenance au XIXe siècle."""
    tables = _tables_retailleau()
    tables["memgrppol"] = [
        {"senmat": "04033B", "memgrppolid": "9", "grppolcod": "LR",
         "typapppolcod": "N", "memgrppoldatdeb": "1900-01-01 00:50:39",
         "memgrppoldatfin": "2014-09-30 00:00:00"}]

    mandats = composer_mandats(tables, "04033B")

    groupe = next(m for m in mandats if m["famille"] == "groupe_politique")
    assert groupe["debut"] is None


def test_les_familles_composees_sont_nommees():
    """Un ajout de famille sans nom la rendrait invisible aux consommateurs.

    `extra_parlementaire` est la cinquième, arrivée après coup : l'Assemblée en
    publie 3 pour `bruno-retailleau` **sans date**, le Sénat en date 13 avec leur
    désignateur."""
    assert FAMILLES == ("mandat_parlementaire", "groupe_politique", "commission",
                        "groupe_senatorial", "extra_parlementaire")
