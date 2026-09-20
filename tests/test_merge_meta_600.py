"""`meta` composé clé par clé, aux deux étages de fusion (#600, lot 1 de #598).

Chaque test de ce fichier **échoue sur le code d'avant**, où `meta` valait
`dict(new)` — le bloc du dernier écrivain, pris entier. C'est la seule forme de
vérification qui dise quelque chose : un test qui constate qu'une fonction
existe, ou qu'un fichier contient une chaîne, ne dit rien de ce que le code fait.

Le scénario de référence est celui que #599 a mesuré sur le corpus committé :
le job AN collecte 1 016 votes et écrit ses avertissements ; le job UE écrit un
profil minimal (`build_minimal_profile`) ; le workflow le fusionne **après**
(`--dirs _artifacts/an _artifacts/ue _artifacts/roster`), et son `meta` à trois
clés gagne. `jean-luc-melenchon` publie aujourd'hui, pour tout `meta`, celui de
l'écrivain qui n'avait rien.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import generate_all_profiles  # noqa: E402
from candidate_profile import (  # noqa: E402
    WARNING_AUCUN_MANDAT_FR,
    WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE,
    WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES,
    WARNING_PREFIX_VOTES_INTROUVABLES,
)
from merge_profile import (  # noqa: E402
    REGLES_META,
    _PREFIXE_CHAMBRE_EN_ECHEC,
    _PREFIXE_DEUX_CHAMBRES,
    fusionner_meta,
    merge_pivot_profile,
    merge_raw_profile,
    unir_warnings,
)
from normalize_profil import WARNING_PREFIX_CHAMBRES_NON_CORROBOREE  # noqa: E402
from schema_pivot import REQUIRED_META_KEYS  # noqa: E402

WARNING_MINIMAL = (
    f"{WARNING_AUCUN_MANDAT_FR} (slug absent du référentiel Assemblée "
    "nationale, ou identité introuvable)"
)
WARNING_VOTES = f"{WARNING_PREFIX_VOTES_INTROUVABLES} : aucune correspondance officielle."


def _meta_an() -> dict:
    """Le `meta` de l'écrivain AN : cinq clés, dont la traçabilité de synchro."""
    return {
        "genere_le": "2026-08-29T16:22:00+0000",
        "licence_donnees": "Licence Ouverte (Assemblée nationale)",
        "synchro_sources": {
            "assemblee_nationale": "2026-08-29T16:21:00+0000",
            "assemblee_nationale_syceron": "2026-08-29T16:20:00+0000",
            "assemblee_nationale_questions": None,
        },
        "warnings": [WARNING_VOTES],
        "collecte_ecartee": ["interventions"],
    }


def _meta_chemin_minimal() -> dict:
    """Le `meta` de `build_minimal_profile` : trois clés, aucune source."""
    return {
        "genere_le": "2026-08-19T18:00:00+0000",
        "licence_donnees": "Licence Ouverte (Assemblée nationale)",
        "warnings": [WARNING_MINIMAL],
    }


# ---------------------------------------------------------------------------
# `warnings` : union par famille
# ---------------------------------------------------------------------------

def test_les_warnings_de_l_ecrivain_an_survivent_au_passage_du_chemin_minimal():
    """Le défaut de #600, dans sa forme la plus nue.

    Avant : `dict(new)` — le `warnings` publié valait `[WARNING_MINIMAL]`, et
    « votes introuvables » disparaissait sans trace.
    """
    fusionne = fusionner_meta(_meta_an(), _meta_chemin_minimal())
    assert WARNING_VOTES in fusionne["warnings"]
    assert WARNING_MINIMAL in fusionne["warnings"]


def test_l_union_ne_publie_qu_un_seul_message_par_famille_a_compteur():
    """Deux comptes contradictoires pour la même famille, c'est un de trop.

    « chambres du profil non corroborée » porte des compteurs calculés sur le
    profil qui l'émet. Une union par TEXTE publierait les deux, dont un faux ;
    l'union par famille garde celui du dernier écrivain, calculé sur le profil
    le plus complet.
    """
    ancien = f"{WARNING_PREFIX_CHAMBRES_NON_CORROBOREE} : chambres=['AN'], 2 mandat(s)."
    neuf = f"{WARNING_PREFIX_CHAMBRES_NON_CORROBOREE} : chambres=['AN', 'Senat'], 1 mandat(s)."
    assert unir_warnings([neuf], [ancien]) == [neuf]


def test_l_union_dedoublonne_un_texte_identique():
    assert unir_warnings([WARNING_VOTES], [WARNING_VOTES]) == [WARNING_VOTES]


def test_l_union_garde_l_ordre_du_nouvel_ecrivain_puis_complete():
    autre = "un message sans famille connue"
    assert unir_warnings([WARNING_MINIMAL], [WARNING_VOTES, autre]) == [
        WARNING_MINIMAL,
        WARNING_VOTES,
        autre,
    ]


def test_l_union_ignore_ce_qui_n_est_pas_une_chaine():
    assert unir_warnings([None, 42, WARNING_VOTES], [{"a": 1}]) == [WARNING_VOTES]


# ---------------------------------------------------------------------------
# `synchro_sources`, `genere_le`
# ---------------------------------------------------------------------------

def test_synchro_sources_garde_la_valeur_la_plus_recente_par_source():
    ancien = {
        "genere_le": "2026-08-29T16:00:00+0000",
        "synchro_sources": {
            "assemblee_nationale": "2026-08-29T16:21:00+0000",
            "nosdeputes": "2026-08-19T21:13:30+0000",
        },
        "warnings": [],
    }
    neuf = {
        "genere_le": "2026-08-29T17:00:00+0000",
        "synchro_sources": {"assemblee_nationale": "2026-08-19T18:43:46+0000"},
        "warnings": [],
    }
    fusionne = fusionner_meta(ancien, neuf)
    assert fusionne["synchro_sources"]["assemblee_nationale"] == "2026-08-29T16:21:00+0000"
    # La source que seul l'ancien connaissait n'est pas perdue.
    assert fusionne["synchro_sources"]["nosdeputes"] == "2026-08-19T21:13:30+0000"


def test_genere_le_est_le_plus_recent_des_deux():
    """Avant : celui du dernier écrivain — donc le 19/08 du chemin minimal sur
    un profil dont l'essentiel a été collecté le 29/08."""
    fusionne = fusionner_meta(_meta_an(), _meta_chemin_minimal())
    assert fusionne["genere_le"] == "2026-08-29T16:22:00+0000"


def test_genere_le_ne_recule_pas_quand_l_artifact_est_plus_vieux_que_le_committe():
    fusionne = fusionner_meta(
        {"genere_le": "2026-08-29T16:00:00+0000", "warnings": []},
        {"genere_le": "2026-08-01T09:00:00+0000", "warnings": []},
    )
    assert fusionne["genere_le"] == "2026-08-29T16:00:00+0000"


def test_un_horodatage_illisible_ne_fait_pas_lever_la_fusion():
    fusionne = fusionner_meta(
        {"genere_le": "pas une date", "warnings": []},
        {"genere_le": "2026-08-29T16:00:00+0000", "warnings": []},
    )
    assert fusionne["genere_le"] == "2026-08-29T16:00:00+0000"


# ---------------------------------------------------------------------------
# `collecte_ecartee` : la déclaration du run, `[]` compris
# ---------------------------------------------------------------------------

def test_collecte_ecartee_survit_a_un_ecrivain_qui_n_a_pas_la_cle():
    """Le chemin minimal n'écrit pas `collecte_ecartee`. Sans cette règle, la
    décision de collecte du job AN disparaît, et `couverture_profil` publie
    « couvert » sur une liste que personne n'a demandée (#539)."""
    fusionne = fusionner_meta(_meta_an(), _meta_chemin_minimal())
    assert fusionne["collecte_ecartee"] == ["interventions"]


def test_collecte_ecartee_vide_du_nouvel_ecrivain_gagne():
    """`[]` dit « ce run n'a rien écarté » : c'est une affirmation, pas une
    absence. `_prefer_non_empty` la prendrait pour un vide et republierait la
    décision d'un run précédent."""
    fusionne = fusionner_meta(_meta_an(), {**_meta_chemin_minimal(), "collecte_ecartee": []})
    assert fusionne["collecte_ecartee"] == []


# ---------------------------------------------------------------------------
# Les autres clés : une règle chacune, aucune au hasard
# ---------------------------------------------------------------------------

def test_toute_cle_obligatoire_du_schema_a_une_regle_nommee():
    """#600 exige une règle explicite pour chaque clé de `meta`.

    Le test porte sur les clés du schéma publié **et** sur celles que la
    collecte écrit à l'étage brut : une clé qui apparaîtrait sans règle
    retomberait sur le défaut, ce qui est acceptable, mais elle doit être un
    choix et non un oubli.
    """
    cles_du_brut = {"genere_le", "licence_donnees", "synchro_sources", "warnings", "collecte_ecartee"}
    cles_du_pivot = set(REQUIRED_META_KEYS) | {"provenance", "collecte_ecartee"}
    for cle in sorted(cles_du_brut | cles_du_pivot):
        assert cle in REGLES_META, f"`meta.{cle}` n'a pas de règle nommée"


def test_une_cle_inconnue_ne_regresse_jamais_vers_null():
    """La règle par défaut est celle des scalaires, pas « prendre le nouveau » —
    c'est précisément ce défaut-là que le lot corrige."""
    fusionne = fusionner_meta(
        {"warnings": [], "cle_future": "une valeur"},
        {"warnings": [], "cle_future": None},
    )
    assert fusionne["cle_future"] == "une valeur"


def test_une_cle_inconnue_du_nouvel_ecrivain_est_conservee():
    fusionne = fusionner_meta({"warnings": []}, {"warnings": [], "cle_future": "neuve"})
    assert fusionne["cle_future"] == "neuve"


def test_schema_version_est_celle_du_producteur_courant():
    fusionne = fusionner_meta(
        {"schema_version": "0", "warnings": []},
        {"schema_version": "1", "warnings": []},
    )
    assert fusionne["schema_version"] == "1"


def test_les_prefixes_recopies_n_ont_pas_diverge_de_leur_constante():
    """`merge_profile` recopie deux préfixes de `generate_all_profiles`, qui
    l'importe : les importer serait circulaire. Ce test est le prix de la
    recopie — sans lui, un renommage de libellé désaccorderait silencieusement
    l'union par famille."""
    assert _PREFIXE_CHAMBRE_EN_ECHEC == generate_all_profiles.WARNING_PREFIX_CHAMBRE_EN_ECHEC
    assert _PREFIXE_DEUX_CHAMBRES == generate_all_profiles.WARNING_PREFIX_DEUX_CHAMBRES


# ---------------------------------------------------------------------------
# Étage brut : le scénario complet de #484 / #599
# ---------------------------------------------------------------------------

def _profil_an() -> dict:
    return {
        "slug": "jean-luc-melenchon",
        "identite": {"nom_complet": "Jean-Luc Mélenchon", "profession": "Professeur"},
        "votes": [{"numero_scrutin": 1, "date": "2024-01-01"}],
        "mandats": [{"categorie": "electif", "label": "Député", "debut": "2022-06-22"}],
        "meta": _meta_an(),
    }


def _profil_minimal() -> dict:
    return {
        "slug": "jean-luc-melenchon",
        "identite": {
            "nom_complet": "Jean-Luc Mélenchon",
            "groupe_sigle": None,
            "groupe_nom": "La France Insoumise (LFI)",
            "profession": None,
            "date_naissance": None,
            "num_circo": None,
            "nb_mandats": None,
            "url_an_ou_senat": None,
        },
        "mandats": [],
        "votes": [],
        "meta": _meta_chemin_minimal(),
    }


def test_etage_brut_le_meta_de_l_ecrivain_an_survit_au_profil_minimal():
    fusionne = merge_raw_profile(_profil_an(), _profil_minimal())
    meta = fusionne["meta"]
    assert meta["collecte_ecartee"] == ["interventions"]
    assert meta["genere_le"] == "2026-08-29T16:22:00+0000"
    assert meta["synchro_sources"]["assemblee_nationale"] == "2026-08-29T16:21:00+0000"
    # « votes introuvables » est éteint parce que les votes sont là : c'est le
    # mécanisme d'extinction qui parle, pas une perte.
    assert WARNING_VOTES not in meta["warnings"]
    # ... et le warning du chemin minimal l'est aussi, démenti par l'identité.
    assert meta["warnings"] == []


def test_etage_brut_un_avertissement_an_sans_rapport_avec_les_listes_survit():
    """Le cœur du défaut : un avertissement que rien ne dément ne doit pas
    disparaître parce qu'un autre écrivain est passé après."""
    an = _profil_an()
    an["meta"]["warnings"] = [f"{_PREFIXE_DEUX_CHAMBRES} : identité aussi trouvée au Sénat."]
    fusionne = merge_raw_profile(an, _profil_minimal())
    assert fusionne["meta"]["warnings"] == [
        f"{_PREFIXE_DEUX_CHAMBRES} : identité aussi trouvée au Sénat."
    ]


def test_etage_brut_la_synchro_survit_a_un_ecrivain_sans_bloc_meta():
    """Avant, le rattrapage exigeait que les DEUX profils portent un `meta`
    dict : un écrivain sans `meta` du tout emportait la traçabilité entière."""
    sans_meta = {k: v for k, v in _profil_minimal().items() if k != "meta"}
    fusionne = merge_raw_profile(_profil_an(), sans_meta)
    assert fusionne["meta"]["synchro_sources"]["assemblee_nationale"] == "2026-08-29T16:21:00+0000"
    assert fusionne["meta"]["collecte_ecartee"] == ["interventions"]


def test_etage_brut_la_fusion_ne_mute_pas_le_meta_du_profil_neuf():
    """`merged = dict(new)` faisait partager le MÊME objet `meta` : toute
    retouche d'après-fusion écrivait dans le profil du nouvel écrivain, que
    l'appelant peut réutiliser."""
    neuf = _profil_minimal()
    avant = list(neuf["meta"]["warnings"])
    merge_raw_profile(_profil_an(), neuf)
    assert neuf["meta"]["warnings"] == avant


# ---------------------------------------------------------------------------
# Étage pivot
# ---------------------------------------------------------------------------

def _pivot(meta: dict, **extra) -> dict:
    base = {
        "schema_version": "1",
        "id": "jean-luc-melenchon",
        "nom": "Jean-Luc Mélenchon",
        "chambre": "AN",
        "sources": [],
        "mandats": [],
        "votes": [],
        "textes_portes": [],
        "interventions": [],
        "amendements": [],
        "tags_thematiques": [],
        "meta": meta,
    }
    base.update(extra)
    return base


def test_etage_pivot_les_warnings_des_deux_ecrivains_survivent():
    ancien = _pivot({
        "schema_version": "1",
        "genere_le": "2026-08-29T16:00:00+0000",
        "licence_donnees": "Licence Ouverte",
        "provenance": "candidat_declare",
        "warnings": [f"{_PREFIXE_DEUX_CHAMBRES} : identité aussi trouvée au Sénat."],
    })
    neuf = _pivot({
        "schema_version": "1",
        "genere_le": "2026-08-19T18:00:00+0000",
        "licence_donnees": "Licence Ouverte",
        "provenance": "candidat_declare",
        "warnings": [WARNING_MINIMAL],
    })
    fusionne = merge_pivot_profile(ancien, neuf)
    assert f"{_PREFIXE_DEUX_CHAMBRES} : identité aussi trouvée au Sénat." in fusionne["meta"]["warnings"]
    assert fusionne["meta"]["genere_le"] == "2026-08-29T16:00:00+0000"


def test_etage_pivot_provenance_ne_regresse_pas_vers_l_absence():
    """`meta.provenance` est un scalaire SURVEILLÉ par `audit_diff_profils` : un
    passage renseigné -> `null` abandonne le commit en CI. Avant, un écrivain
    dont le `meta` n'a pas la clé l'emportait avec lui."""
    ancien = _pivot({
        "schema_version": "1",
        "genere_le": "2026-08-29T16:00:00+0000",
        "licence_donnees": "Licence Ouverte",
        "provenance": "roster_groupe",
        "warnings": [],
    })
    neuf = _pivot({
        "schema_version": "1",
        "genere_le": "2026-08-29T17:00:00+0000",
        "licence_donnees": "Licence Ouverte",
        "warnings": [],
    })
    fusionne = merge_pivot_profile(ancien, neuf)
    assert fusionne["meta"]["provenance"] == "roster_groupe"


def test_etage_pivot_candidat_declare_n_est_toujours_pas_retrograde():
    """La règle #189 reste plus forte que la composition : elle s'applique
    APRÈS, et le lot ne doit pas l'avoir désarmée."""
    ancien = _pivot({
        "schema_version": "1",
        "genere_le": "2026-08-29T16:00:00+0000",
        "licence_donnees": "Licence Ouverte",
        "provenance": "candidat_declare",
        "warnings": [],
    })
    neuf = _pivot({
        "schema_version": "1",
        "genere_le": "2026-08-29T17:00:00+0000",
        "licence_donnees": "Licence Ouverte",
        "provenance": "roster_groupe",
        "warnings": [],
    })
    assert merge_pivot_profile(ancien, neuf)["meta"]["provenance"] == "candidat_declare"


# ---------------------------------------------------------------------------
# L'extinction, étendue aux deux familles que l'union peut ressusciter
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "prefixe",
    [
        WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES,
        WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE,
    ],
)
def test_un_avertissement_syceron_s_eteint_si_les_interventions_sont_la(prefixe):
    """L'avertissement est porté par le NOUVEL écrivain — celui dont le `meta`
    gagnait avant ce lot : le test dit donc quelque chose de l'extinction, et
    pas seulement de l'union. Sans l'extension, il est publié sur un profil qui
    porte des interventions Syceron, et le dément."""
    ancien = _profil_an()
    ancien["interventions"] = [{"id": "i1", "type_detail": "prise_de_parole"}]
    neuf = _profil_minimal()
    neuf["meta"]["warnings"] = [f"{prefixe} : archive muette."]
    fusionne = merge_raw_profile(ancien, neuf)
    assert fusionne["meta"]["warnings"] == []


@pytest.mark.parametrize(
    "prefixe",
    [
        WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES,
        WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE,
    ],
)
def test_des_questions_seules_n_eteignent_pas_un_avertissement_syceron(prefixe):
    """Les questions viennent de l'open data AN, pas de Syceron (#510). Les
    compter éteindrait un constat Syceron avec la preuve d'une autre source."""
    ancien = _profil_an()
    ancien["interventions"] = [{"id": "q1", "type_detail": "question"}]
    neuf = _profil_minimal()
    neuf["meta"]["warnings"] = [f"{prefixe} : archive muette."]
    fusionne = merge_raw_profile(ancien, neuf)
    assert fusionne["meta"]["warnings"] == [f"{prefixe} : archive muette."]


def test_un_avertissement_de_budget_ressuscite_n_est_jamais_eteint():
    """Une liste tronquée par budget reste une liste dont on ne sait pas si elle
    est complète, même quand la fusion l'a remplie (#498/#514)."""
    from candidate_profile import WARNING_PREFIX_BUDGET_INTERVENTIONS

    ancien = _profil_an()
    ancien["interventions"] = [{"id": "i1", "type_detail": "prise_de_parole"}]
    neuf = _profil_minimal()
    neuf["meta"]["warnings"] = [f"{WARNING_PREFIX_BUDGET_INTERVENTIONS} : 3 législatures sur 4."]
    fusionne = merge_raw_profile(ancien, neuf)
    assert fusionne["meta"]["warnings"] == [
        f"{WARNING_PREFIX_BUDGET_INTERVENTIONS} : 3 législatures sur 4."
    ]


# ---------------------------------------------------------------------------
# La mesure de #599, rejouée sur le résultat de la fusion
# ---------------------------------------------------------------------------

def test_les_mesures_2_et_3_de_599_rendent_zero_apres_la_fusion(tmp_path):
    """Le critère de sortie de #600, vérifié avec l'outil du lot 0 lui-même.

    Le corpus de test reproduit le cas mesuré : un écrivain AN complet, un
    écrivain minimal qui passe après. Sur le code d'avant, l'audit compte le
    profil dans les deux mesures.
    """
    import json

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from audit_fusion_blocs_599 import mesurer_synchro, mesurer_warnings

    fusionne = merge_raw_profile(_profil_an(), _profil_minimal())
    json.dumps(fusionne, ensure_ascii=False)  # le résultat reste sérialisable

    bruts = {"un-depute": fusionne}
    mesure2 = mesurer_warnings(bruts, {}, "2026-08-29")
    mesure3 = mesurer_synchro(bruts)

    assert mesure2["nb_profils_touches"] == 0
    assert mesure3["nb_dont_source_encore_ecrite"] == 0
    assert mesure3["nb_meta_sans_synchro_sources"] == 0
