"""La corroboration de `chambres` porte sur la liste publiée, pas sur la
complétude de `mandats[]` (épic **#486**, après #492 et #493).

Pourquoi ce lot existe, mesuré sur les **481 profils pivot publiés** du
30/08/2026 : le warning `chambres du profil non corroborée` y est publié **31
fois**, et **30 de ces 31 occurrences énoncent un problème que leur propre
phrase dénie** —

- **27** disent « chambres=['AN'], dont *aucune* sans mandat électif estampillé
  pour l'étayer, et 1 mandat(s) électif(s) encore sans chambre » : la liste
  publiée est intégralement étayée, et le titre dit le contraire ;
- **3** (`david-lisnard`, `marine-tondelier`, `nathalie-arthaud`) disent
  « chambres=[], dont aucune […] et 0 mandat(s) » : un avertissement qui ne
  nomme aucun problème ;
- **1** seule décrit un fait — `bruno-retailleau`, dont la liste publie `AN`
  qu'aucun mandat n'étaye, alors que son unique `mandat_electif` est estampillé
  `Senat` et toujours ouvert. C'est le défaut fondateur de l'épic.

Conséquence pratique, et raison pour laquelle ce n'est pas un détail de
formulation : la **condition 2 du retrait de `chambre`**
(docs/decisions/chambres-profil-derivees.md) est « ce warning est absent de tout
le corpus ». Tant qu'il redéclare la complétude des mandats, elle gage le
retrait d'un champ de **niveau profil** sur une complétude de **niveau mandat**
que la fusion additive ne peut pas atteindre : les 29 `mandat_electif` à
`chambre: null` des 511 publiés sont exactement ceux que la source ne rend plus,
donc ceux qu'aucune recollecte ne réestampillera et que
`backfill_mandat_chambre` ne peut pas apparier.

Le fait n'est pas perdu pour autant : il est déclaré par le warning de #492,
`chambre de mandat électif non résolue`, qui le nomme et le compte — et qui
devient ici le seul à le faire, donc doit survivre à la fusion dans les deux
sens.

Aucune lecture du corpus vivant (`pivot_data/`, `raw_data/profiles/`) : fixtures
figées, comme #473 l'exige pour la CI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import (  # noqa: E402
    FAMILLES_WARNINGS,
    merge_pivot_profile,
    unir_warnings,
)
from normalize_profil import (  # noqa: E402
    WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE,
    WARNING_PREFIX_CHAMBRES_NON_CORROBOREE,
    normalize_profil,
)
from schema_pivot import deriver_chambres  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures figées
# ---------------------------------------------------------------------------

def _mandat_brut(chambre=None, label="Mandat parlementaire", debut="2022-06-22"):
    mandat = {
        "categorie": "mandat_electif",
        "type": "mandat",
        "label": label,
        "debut": debut,
        "fin": None,
        "actif": True,
    }
    if chambre is not None:
        mandat["chambre"] = chambre
    return mandat


def _brut(chambre="deputes", mandats=None):
    return {
        "slug": "marie-martin",
        "chambre": chambre,
        "source": "https://www.nosdeputes.fr/marie-martin",
        "identite": {"nom_complet": "Marie Martin", "groupe_nom": "Socialistes"},
        "mandats": mandats if mandats is not None else [],
        "votes": [],
        "interventions": [],
        "amendements": [],
        "dossiers_legislatifs": [],
        "meta": {
            "genere_le": "2026-08-30T12:00:00+0000",
            "synchro_sources": {"nosdeputes": "2026-08-30T12:00:00+0000"},
        },
    }


def _mandat_pivot(chambre=None, label="Mandat parlementaire", debut="2022-06-22"):
    return {
        "label": label,
        "categorie": "mandat_electif",
        "fonction": "membre",
        "debut": debut,
        "fin": None,
        "actif": True,
        "chambre": chambre,
    }


def _w493(pivot):
    return [w for w in pivot["meta"]["warnings"]
            if w.startswith(WARNING_PREFIX_CHAMBRES_NON_CORROBOREE)]


def _w492(pivot):
    return [w for w in pivot["meta"]["warnings"]
            if w.startswith(WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE)]


def _sans_w492(pivot):
    """Un pivot antérieur à #492 : le mandat est là, l'avertissement jamais écrit.

    C'est l'état réel de `yannick-vaugrenard` — 1 des 481 profils publiés porte
    un `mandat_electif` à `chambre: null` sans aucun warning pour le dire.
    """
    pivot["meta"]["warnings"] = [w for w in pivot["meta"]["warnings"]
                                if not w.startswith(WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE)]
    return pivot


# ---------------------------------------------------------------------------
# 1. Le prédicat : ce que `corroboree` dit, et ce qu'il ne dit plus
# ---------------------------------------------------------------------------

def test_une_liste_vide_na_rien_a_corroborer():
    """3 des 481 profils publiés sont dans ce cas : aucun mandat parlementaire,
    aucune chambre de collecte, donc aucune chambre publiée — et un warning qui
    ne nommait rien."""
    d = deriver_chambres([], repli=None)
    assert d.chambres == []
    assert d.corroboree is True


def test_une_liste_entierement_etayee_est_corroboree_meme_avec_un_mandat_a_null():
    """Les 27 autres. `AN` est dite par un mandat estampillé ; le mandat resté à
    `null` ne retire rien à cet étai."""
    d = deriver_chambres(
        [_mandat_pivot("AN", debut="2024-07-07"), _mandat_pivot(None, debut="2022-06-22")],
        repli="AN",
    )
    assert d.corroboree is True
    assert d.chambres_non_corroborees == []
    assert d.mandats_non_estampilles == 1


def test_une_chambre_de_collecte_sans_mandat_reste_non_corroboree():
    """Le cas `bruno-retailleau`, seul des 31 à décrire un fait : le jeu de
    données AN a répondu pour un profil dont l'unique mandat est sénatorial.
    Ce lot ne doit pas éteindre celui-là — c'est le défaut fondateur de #486."""
    d = deriver_chambres([_mandat_pivot("Senat", debut="2004-09-26")], repli="AN")
    assert d.chambres == ["AN", "Senat"]
    assert d.corroboree is False
    assert d.chambres_non_corroborees == ["AN"]


# ---------------------------------------------------------------------------
# 2. Ce que `normalize_profil` publie
# ---------------------------------------------------------------------------

def test_le_pivot_ne_declare_plus_non_corroboree_une_liste_etayee():
    pivot = normalize_profil(_brut(
        chambre="deputes",
        mandats=[_mandat_brut("deputes", label="Neuf", debut="2024-07-07"),
                 _mandat_brut(None, label="Ancien", debut="2022-06-22")],
    ))
    assert pivot["chambres"] == ["AN"]
    assert _w493(pivot) == []


def test_le_fait_reste_declare_par_lavertissement_de_492():
    """Rien ne devient muet : le mandat sans chambre garde son avertissement,
    celui qui le nomme et le compte (§2.5)."""
    pivot = normalize_profil(_brut(
        chambre="deputes",
        mandats=[_mandat_brut("deputes", label="Neuf", debut="2024-07-07"),
                 _mandat_brut(None, label="Ancien", debut="2022-06-22")],
    ))
    assert len(_w492(pivot)) == 1
    assert "1 mandat(s)" in _w492(pivot)[0]


def test_lavertissement_de_493_ne_compte_plus_les_mandats():
    """Un message dit une chose. Mêler le compte des mandats à la déclaration
    d'une chambre non étayée est ce qui a rendu les 30 occurrences illisibles."""
    pivot = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("senateurs")]))
    assert len(_w493(pivot)) == 1
    assert "mandat(s) électif(s) encore sans chambre" not in _w493(pivot)[0]


# ---------------------------------------------------------------------------
# 3. La fusion : l'avertissement de #492 survit dans les deux sens
# ---------------------------------------------------------------------------

def test_la_fusion_reconstruit_lavertissement_quun_ancien_pivot_na_jamais_porte():
    """Le trou mesuré : `normalize_profil` compte sur les mandats du profil
    NEUF, la fusion additive en publie un surensemble. Sans reconstruction,
    un mandat sans chambre venu de l'ancien profil ne se déclare nulle part."""
    ancien = _sans_w492(normalize_profil(
        _brut(chambre="deputes", mandats=[_mandat_brut(None, label="Ancien", debut="2022-06-22")])
    ))
    assert _w492(ancien) == []

    neuf = normalize_profil(
        _brut(chambre="deputes", mandats=[_mandat_brut("deputes", label="Neuf", debut="2024-07-07")])
    )
    assert _w492(neuf) == []

    fusionne = merge_pivot_profile(ancien, neuf)
    assert len(_w492(fusionne)) == 1
    assert "1 mandat(s)" in _w492(fusionne)[0]


def test_la_fusion_eteint_lavertissement_quand_le_backfill_a_tout_estampille():
    """L'autre sens : `backfill_mandat_chambre` remplit le champ de l'entrée
    ancienne de même clé, et le dire encore serait faux."""
    ancien = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut(None)]))
    assert len(_w492(ancien)) == 1

    neuf = normalize_profil(_brut(chambre="deputes", mandats=[_mandat_brut("deputes")]))
    fusionne = merge_pivot_profile(ancien, neuf)
    assert _w492(fusionne) == []
    assert _w493(fusionne) == []


def test_la_fusion_remplace_un_compte_devenu_faux():
    """Un compte faux est aussi trompeur qu'un compte absent : il fait croire la
    migration plus avancée qu'elle n'est."""
    ancien = normalize_profil(_brut(
        chambre="deputes",
        mandats=[_mandat_brut(None, label="A", debut="2012-06-20"),
                 _mandat_brut(None, label="B", debut="2017-06-21"),
                 _mandat_brut(None, label="C", debut="2022-06-22")],
    ))
    assert "3 mandat(s)" in _w492(ancien)[0]

    # Le run neuf réestampille B et C ; A reste fossile.
    neuf = normalize_profil(_brut(
        chambre="deputes",
        mandats=[_mandat_brut("deputes", label="B", debut="2017-06-21"),
                 _mandat_brut("deputes", label="C", debut="2022-06-22")],
    ))
    fusionne = merge_pivot_profile(ancien, neuf)
    assert len(_w492(fusionne)) == 1
    assert "1 mandat(s)" in _w492(fusionne)[0]


def test_lavertissement_de_492_a_une_famille():
    """Sans famille, `unir_warnings` compare les textes : deux comptes
    contradictoires sont publiés côte à côte, dont un faux. C'est la règle que
    #600 a posée pour les messages à compteur, et qui manquait à celui-ci."""
    assert WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE in FAMILLES_WARNINGS
    ancien = f"{WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE} : 3 mandat(s) sans chambre."
    neuf = f"{WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE} : 1 mandat(s) sans chambre."
    assert unir_warnings([neuf], [ancien]) == [neuf]
