#!/usr/bin/env python3
"""#641 — un code de nomenclature n'est pas une profession, et « sans activité
professionnelle » n'en est pas une non plus.

Huit des 457 profils qui renseignent `identite.profession` publiaient, au
31/08/2026, un code brut du référentiel AN. Deux cas distincts sous un même
motif `(nn) - ` :

| Forme publiée | Profils | Ce que c'est |
| --- | ---: | --- |
| `(33) - Cadre de la fonction publique` | 3 | un libellé bon, précédé de bruit |
| `(85) - Personne diverse sans activité professionnelle de moins de 60 ans…` | 5 | **l'énoncé d'une absence de profession**, publié comme une profession |

Ces tests portent sur les **deux** lecteurs, et le second n'est pas une
redondance du premier : `merge_profile` ne fait jamais régresser un scalaire
vers `null`, donc la collecte corrigée ne peut pas éteindre les cinq profils du
code 85 — seule la normalisation le peut. C'est l'argument de `_uri_hatvp_publiable` (#539).

Ils lisent le code **exécuté** — les deux fonctions, pas leurs commentaires —,
comme `tests/test_retrait_nosdeputes_529.py`, et ne touchent ni `pivot_data/`
ni `raw_data/profiles/` ni le réseau.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from candidate_profile import _profession_an  # noqa: E402
from normalize_profil import _profession_publiable, normalize_profil  # noqa: E402

#: Les deux lecteurs doivent rendre la même chose : un désaccord ferait publier
#: à la normalisation ce que la collecte refuse, ou l'inverse.
LECTEURS = pytest.mark.parametrize(
    "lire", [_profession_an, _profession_publiable], ids=["collecte", "publication"]
)


@LECTEURS
@pytest.mark.parametrize("brut, attendu", [
    # Les trois libellés réellement publiés sous le code 33.
    ("(33) - Cadre de la fonction publique", "Cadre de la fonction publique"),
    ("(37) - Cadre administratif et commercial d'entreprise",
     "Cadre administratif et commercial d'entreprise"),
    # Le référentiel n'espace pas toujours pareil.
    ("(12)-Agriculteur sur moyenne exploitation", "Agriculteur sur moyenne exploitation"),
    # Sans préfixe, rien ne bouge : la forme majoritaire du corpus.
    ("Avocat", "Avocat"),
])
def test_le_code_de_nomenclature_est_retire_le_libelle_reste(lire, brut, attendu):
    assert lire(brut) == attendu


@LECTEURS
@pytest.mark.parametrize("brut", [
    # Les deux variantes réellement publiées, dont celle que la source tronque.
    "(85) - Personne diverse sans activité professionnelle de moins de 60 ans (sauf r",
    "(85) - Personne diverse sans activité professionnelle de moins de 60 ans",
    "(85) - Personne diverse sans activité professionnelle de moins de 60 ans (sauf retraité)",
])
def test_l_enonce_d_une_absence_de_profession_devient_null(lire, brut):
    """Une absence n'est pas une valeur (AGENTS.md §2 règle 5). Aucune
    profession de remplacement n'est inventée : la page dira « non
    renseignée »."""
    assert lire(brut) is None


@LECTEURS
def test_une_situation_nest_pas_une_absence(lire):
    """`(84) - Elève, étudiant` est dans la même famille 8x et n'énonce aucune
    absence : la famille du code seule ne suffit pas à décider."""
    assert lire("(84) - Elève, étudiant") == "Elève, étudiant"


@LECTEURS
def test_un_ancien_metier_reste_un_libelle(lire):
    assert lire("(74) - Ancien cadre") == "Ancien cadre"


@LECTEURS
@pytest.mark.parametrize("brut", [
    None,
    "",
    "   ",
    "(85) - ",
    # Le marqueur XML d'AMO30 (#556) : un dict truthy, jamais une profession.
    {"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance", "@xsi:nil": "true"},
])
def test_rien_de_publiable_donne_null(lire, brut):
    assert lire(brut) is None


def test_le_profil_publie_ne_porte_plus_le_code(tmp_path):
    """Le bout en bout, sur le profil brut d'Éric Ciotti tel qu'il est
    aujourd'hui committé (le champ, pas le fichier : aucun test ne lit
    `raw_data/`)."""
    profil = normalize_profil({
        "slug": "eric-ciotti",
        "chambre": "deputes",
        "identite": {
            "nom_complet": "Éric Ciotti",
            "profession": "(33) - Cadre de la fonction publique",
            "url_an_ou_senat": "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA330240",
        },
    })
    assert profil["identite"]["profession"] == "Cadre de la fonction publique"


def test_un_profil_dont_la_seule_identite_etait_une_absence_na_plus_d_identite():
    """Nuller la profession peut vider le bloc `identite` — et c'est le
    comportement voulu : `identite` n'est écrit que si un champ est renseigné,
    et « pas de profession » n'en est pas un."""
    profil = normalize_profil({
        "slug": "sans-rien",
        "chambre": "deputes",
        "identite": {
            "profession": "(85) - Personne diverse sans activité professionnelle "
                          "de moins de 60 ans (sauf retraité)",
        },
    })
    assert profil["identite"] is None


def test_les_deux_lecteurs_ne_peuvent_pas_diverger():
    """Le critère est recopié dans deux modules — `normalize_profil` est
    volontairement découplé de la collecte. Le verrou n'est pas le texte, c'est
    l'accord des deux sur les formes qui comptent."""
    formes = [
        "(33) - Cadre de la fonction publique",
        "(85) - Personne diverse sans activité professionnelle de moins de 60 ans",
        "(84) - Elève, étudiant",
        "(81) - Chômeur n'ayant jamais travaillé",
        "(86) - Personne diverse sans activité professionnelle de 60 ans et plus",
        "Avocat",
        "(99)",
        "",
    ]
    assert [_profession_an(f) for f in formes] == [_profession_publiable(f) for f in formes]


# ---------------------------------------------------------------------------
# La transition que la première version du lot n'avait pas éprouvée (#641,
# réouverture du 31/08/2026)
# ---------------------------------------------------------------------------
#
# Les deux lecteurs ci-dessus étaient verts, et le run 33395056902 a quand même
# republié les cinq libellés. Ce que rien ne testait, c'est l'ÉTAPE SUIVANTE :
# le bloc publié n'est pas celui que la normalisation rend, c'est celui que
# `merge_pivot_profile` compose avec le pivot déjà en place, et sa première
# règle est qu'« une absence n'écrase jamais une valeur connue » (#601).
#
# D'où la différence, mesurée sur le run, entre les deux volets du lot :
# la valeur neuve des 3 profils au préfixe est renseignée et gagne ; celle des
# 5 profils du code 85 est `None`, et la composition restaure la valeur publiée.

from merge_profile import (  # noqa: E402
    FILTRES_PUBLICATION_IDENTITE,
    filtrer_identite_publiee,
    merge_pivot_profile,
)

#: Les deux formes réellement republiées par le run, verbatim.
CODE_85 = "(85) - Personne diverse sans activité professionnelle de moins de 60 ans (sauf r"
CODE_33 = "(33) - Cadre de la fonction publique"


def _pivot(profession, *, provenance=True):
    """Profil pivot minimal, à la forme que `merge_pivot_profile` reçoit."""
    profil = {
        "schema_version": "1", "id": "un-depute", "nom": "Un Député",
        "chambre": "AN", "chambres": ["AN"], "parti": None, "groupe": None,
        "sources": [{"type": "assemblee_nationale",
                     "url": "https://data.assemblee-nationale.fr/",
                     "synchro_le": "2026-08-31T13:00:00+0000"}],
        "identite": {"nom_complet": "Un Député", "profession": profession,
                     "source_url": "https://www.assemblee-nationale.fr/"},
        "mandats": [], "votes": [], "textes_portes": [], "amendements": [],
        "interventions": [], "tags_thematiques": [],
        "meta": {"schema_version": "1", "genere_le": "2026-08-31T13:00:00+0000"},
    }
    if provenance:
        profil["meta"]["provenance_champs"] = {"identite": {
            "profession": {"source": "assemblee_nationale",
                           "synchro_le": "2026-08-31T13:00:00+0000"},
            "nom_complet": {"source": "assemblee_nationale",
                            "synchro_le": "2026-08-31T13:00:00+0000"},
        }}
    return profil


def test_la_valeur_publiee_ne_survit_pas_a_la_fusion():
    """Le cas des cinq : la collecte corrigée rend `None`, et c'est la
    composition — pas la normalisation — qui décidait jusqu'ici."""
    fusionne = merge_pivot_profile(_pivot(CODE_85), _pivot(None, provenance=False))
    assert fusionne["identite"]["profession"] is None


def test_le_prefixe_est_retire_aussi_sur_une_valeur_heritee():
    """Un profil non régénéré depuis le premier volet garde son préfixe tant que
    la collecte ne repasse pas. Le filtre le rattrape à la publication."""
    fusionne = merge_pivot_profile(_pivot(CODE_33), _pivot(None, provenance=False))
    assert fusionne["identite"]["profession"] == "Cadre de la fonction publique"


def test_une_profession_legitime_heritee_est_conservee():
    """Le filtre est strictement décroissant : il ne peut rien perdre d'autre.
    Sans ce contrôle, corriger #641 rendrait `null` toute profession qu'un run
    n'aurait pas recollectée — une perte de masse sur 457 profils."""
    fusionne = merge_pivot_profile(_pivot("Avocate"), _pivot(None, provenance=False))
    assert fusionne["identite"]["profession"] == "Avocate"


def test_la_provenance_du_champ_disparait_avec_la_valeur():
    """Un champ nul n'a pas d'origine à nommer (#603) — et une provenance
    laissée seule serait la preuve d'un fait qui n'est plus publié."""
    fusionne = merge_pivot_profile(_pivot(CODE_85), _pivot(None, provenance=False))
    provenance = fusionne["meta"]["provenance_champs"]["identite"]
    assert "profession" not in provenance
    assert "nom_complet" in provenance


def test_le_premier_pivot_publie_la_meme_chose_quun_pivot_regenere():
    """`merge_pivot_profile(None, neuf)` court-circuite la composition : sans le
    filtre à cet endroit aussi, deux profils de même contenu ne publieraient pas
    la même profession selon qu'un fichier existait déjà."""
    premier = merge_pivot_profile(None, _pivot(CODE_85, provenance=False))
    assert premier["identite"]["profession"] is None
    assert "profession" not in (
        premier["meta"].get("provenance_champs", {}).get("identite", {})
    )


def test_le_filtre_est_idempotent_et_nommé_champ_par_champ():
    """Il ne s'applique qu'aux champs déclarés : généraliser inventerait la
    sémantique des autres libellés recopiés d'AMO30."""
    assert set(FILTRES_PUBLICATION_IDENTITE) == {"profession"}
    bloc = {"profession": CODE_33, "civilite": CODE_33}
    filtrer_identite_publiee(bloc)
    assert bloc == {"profession": "Cadre de la fonction publique", "civilite": CODE_33}
    fige = dict(bloc)
    filtrer_identite_publiee(bloc)
    assert bloc == fige


def test_un_bloc_absent_traverse_le_filtre_sans_bruit():
    assert filtrer_identite_publiee(None) is None
