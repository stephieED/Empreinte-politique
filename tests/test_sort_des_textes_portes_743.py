#!/usr/bin/env python3
"""
test_sort_des_textes_portes_743.py — Un texte porté dit ce qu'il est devenu, et
son sort ne se déduit jamais de son stade (#743).

`textes_portes[]` publiait dix champs dont **aucun** ne disait si le texte avait
été rejeté, retiré, ou s'il était encore en navette. `stade_procedural` encode
une PROGRESSION — un dossier n'en porte que le cran le plus avancé atteint — et
l'absence du cran suivant est un fait de la source à sa date, jamais une issue.
« Discuté en séance et pas adopté » ne permet pas d'écrire « rejeté »
(§2 règles 2 et 5).

Ce n'était pas un manque de source : les fiches de gouvernement publient ce sort
depuis #184, sur `statutConclusion.fam_code`, et `_determine_statut` ne dépend
pas de l'origine du dossier. Mesuré sur les 464 `dossier_id` distincts de
`textes_portes[]` : **464 / 464 résolus, 0 `fam_code` inconnu**.

Ce que ces tests verrouillent :

- le sort et le stade sont deux champs, et rien ne dérive l'un de l'autre ;
- une absence de sort porte TOUJOURS son motif, et les trois motifs ne se
  confondent pas — un dossier sans décision de séance est un état légitime, un
  `fam_code` inconnu est un trou à combler, une archive absente est une panne ;
- le report traverse les DEUX étages de fusion, la leçon de #729/#730.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/` ni le réseau.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import (  # noqa: E402
    _dossier_key,
    _pivot_texte_key,
    backfill_sort_texte_porte,
    merge_pivot_profile,
    merge_raw_profile,
)
from normalize_profil import _normalize_texte_porte  # noqa: E402
from schema_gouvernement import KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_MOTIFS_SORT_NON_RESOLU,
    KNOWN_SORTS_TEXTE_PORTE,
    validate_profil,
)


def _dossier(**kw):
    base = {
        "id": "DLR5L17N50939", "titre": "Un texte", "role": "auteur",
        "nature_texte": "projet_de_loi", "type_rapport": None,
        "stade_procedural": "discute_seance", "date_min": "2024-01-01",
        "date_max": "2024-06-01", "legislature": "17", "source_url": "https://x",
    }
    base.update(kw)
    return base


def _profil_avec(texte):
    return {
        "id": "x", "nom": "X", "chambres": ["AN"], "chambre": "AN",
        "textes_portes": [texte],
    }


# --------------------------------------------------------------------------
# 1. Le vocabulaire, et son accord avec celui des gouvernements
# --------------------------------------------------------------------------

def test_le_sort_reprend_le_vocabulaire_des_fiches_de_gouvernement():
    """MÊME source, MÊME fonction (`_determine_statut` sur `statutConclusion`),
    donc mêmes valeurs. Ce test est le verrou de la duplication : les deux
    schémas restent indépendants, mais ils ne peuvent pas diverger ici sans
    qu'on le voie."""
    assert KNOWN_SORTS_TEXTE_PORTE == KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL


def test_les_motifs_ne_se_reparent_pas_au_meme_endroit():
    """#747 ajoute le quatrième : les trois premiers sont ceux de l'archive AN
    — un trou à combler, un état légitime, une panne — et #743 n'avait instruit
    que ce chemin. Le dump ParlTrack ne porte AUCUNE issue de dossier : c'est
    un fait de la source, qui ne se répare nulle part."""
    assert KNOWN_MOTIFS_SORT_NON_RESOLU == {
        "fam_code_inconnu", "sans_decision", "archives_indisponibles",
        "source_sans_sort",
    }


# --------------------------------------------------------------------------
# 2. Le schéma refuse la contradiction et l'absence sans cause
# --------------------------------------------------------------------------

@pytest.mark.parametrize("sort", sorted(KNOWN_SORTS_TEXTE_PORTE))
def test_un_sort_du_vocabulaire_est_licite(sort):
    erreurs = validate_profil(_profil_avec(_normalize_texte_porte(_dossier(sort=sort))))
    assert not [e for e in erreurs if "sort" in e]


def test_un_sort_invente_est_refuse():
    texte = _normalize_texte_porte(_dossier(sort="peut_etre"))
    erreurs = validate_profil(_profil_avec(texte))
    assert [e for e in erreurs if ".sort non reconnu" in e]


def test_un_motif_invente_est_refuse():
    texte = _normalize_texte_porte(_dossier(sort_non_resolu={"motif": "sait_pas"}))
    erreurs = validate_profil(_profil_avec(texte))
    assert [e for e in erreurs if "sort_non_resolu.motif inconnu" in e]


def test_les_deux_ensemble_sont_refuses():
    """« Voici son issue » et « voici pourquoi elle manque » ne peuvent pas être
    vrais ensemble."""
    texte = _normalize_texte_porte(
        _dossier(sort="rejete", sort_non_resolu={"motif": "sans_decision"})
    )
    erreurs = validate_profil(_profil_avec(texte))
    assert [e for e in erreurs if "à la fois" in e]


# --------------------------------------------------------------------------
# 3. Le sort ne se déduit pas du stade
# --------------------------------------------------------------------------

@pytest.mark.parametrize("stade", ["depose", "discute_seance", "adopte", "promulgue"])
def test_aucun_stade_ne_fabrique_un_sort(stade):
    """Le piège que le lot existe pour fermer : un stade avancé ne dit rien de
    l'issue, et un stade non atteint encore moins."""
    normalise = _normalize_texte_porte(_dossier(stade_procedural=stade))

    assert normalise["stade_procedural"] == stade
    assert normalise["sort"] is None


def test_le_sort_et_le_stade_cohabitent_sans_se_contredire():
    normalise = _normalize_texte_porte(_dossier(stade_procedural="adopte", sort="rejete"))

    assert (normalise["stade_procedural"], normalise["sort"]) == ("adopte", "rejete")


# --------------------------------------------------------------------------
# 4. Le report nommé, aux deux étages
# --------------------------------------------------------------------------

def test_le_report_pose_le_sort_sur_une_entree_deja_collectee():
    ancienne = [_dossier()]
    neuve = [_dossier(sort="rejete")]

    resultat = backfill_sort_texte_porte(ancienne, neuve, _dossier_key)

    assert resultat[0]["sort"] == "rejete"


def test_le_report_transporte_aussi_le_motif():
    """Sans lui, une entrée ancienne resterait sans sort ET sans explication."""
    ancienne = [_dossier()]
    neuve = [_dossier(sort=None, sort_non_resolu={"motif": "sans_decision"})]

    resultat = backfill_sort_texte_porte(ancienne, neuve, _dossier_key)

    assert resultat[0]["sort_non_resolu"] == {"motif": "sans_decision"}


def test_le_report_n_ecrase_jamais_un_sort_pose():
    ancienne = [_dossier(sort="promulgue")]
    neuve = [_dossier(sort="rejete")]

    resultat = backfill_sort_texte_porte(ancienne, neuve, _dossier_key)

    assert resultat[0]["sort"] == "promulgue"


def test_le_report_ne_touche_aucun_autre_champ():
    ancienne = [_dossier(titre="Ancien titre")]
    neuve = [_dossier(titre="Nouveau titre", sort="adopte")]

    resultat = backfill_sort_texte_porte(ancienne, neuve, _dossier_key)

    assert resultat[0]["titre"] == "Ancien titre"


def test_une_collecte_vide_ne_reporte_rien():
    ancienne = [_dossier()]
    assert backfill_sort_texte_porte(ancienne, None, _dossier_key) == ancienne


def test_le_report_est_cable_dans_la_fusion_BRUTE():
    ancien = {"id": "x", "dossiers_legislatifs": [_dossier()]}
    neuf = {"id": "x", "dossiers_legislatifs": [_dossier(sort="retire")]}

    fusionne = merge_raw_profile(ancien, neuf)

    assert fusionne["dossiers_legislatifs"][0]["sort"] == "retire"


def test_le_sort_atteint_le_pivot_SANS_report():
    """La leçon de #729/#730 ne s'applique PAS ici, et c'est mesuré.

    `textes_portes` ne se fusionne pas comme les autres listes :
    `merge_dossier_records` fait gagner l'entrée **neuve** en cas de collision de
    clé, là où `merge_lists_by_key` fait gagner l'ancienne. Un report posé à cet
    étage serait du code mort justifié par un raisonnement faux — il a été écrit,
    puis retiré quand la mutation a montré que le décâbler ne faisait échouer
    aucun test.
    """
    ancien = {"id": "x", "textes_portes": [_normalize_texte_porte(_dossier())]}
    neuf = {"id": "x", "textes_portes": [_normalize_texte_porte(_dossier(sort="rejete"))]}

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["textes_portes"][0]["sort"] == "rejete"


def test_la_cle_de_fusion_ne_change_pas():
    """Élargir la clé pour y mettre le sort ferait deux entrées d'une seule —
    le défaut de #668, 468 doublons sur 940 entrées."""
    assert _dossier_key(_dossier(sort="rejete")) == _dossier_key(_dossier())
    a = _normalize_texte_porte(_dossier(sort="rejete"))
    b = _normalize_texte_porte(_dossier())
    assert _pivot_texte_key(a) == _pivot_texte_key(b)
