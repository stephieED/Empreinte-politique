"""#908 — le dernier reste de Regards Citoyens part quand il ne couvre plus rien.

#890 a retiré le marqueur des profils de député et s'est arrêté aux deux qui
touchent le Sénat : leur marqueur couvrait une carrière que rien d'autre ne
portait. #885 a branché `data.senat.fr`, la carrière est publiée, et ce lot en
tire la conséquence.

Le test central de ce fichier n'est pas le retrait : c'est ce qui l'**empêche**.
Un appariement par libellé est une heuristique déguisée en table, et sa première
version proposait 17 mandats de député au retrait.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from retrait_heritage_senat import (  # noqa: E402
    APPARIEMENTS_HERITES,
    _labels_publies,
    mandats_apparies_remplaces,
    mandats_bruts_apparies_remplaces,
    mandats_senatoriaux_orphelins,
)
from retrait_residus_senat_908 import traiter  # noqa: E402


def _herite(label, categorie="commission"):
    return {"label": label, "categorie": categorie, "debut": None, "fin": None}


def _senatorial(label, categorie="commission", debut="2020-01-01", fin=None):
    return {"label": label, "categorie": categorie, "debut": debut, "fin": fin,
            "categorie_source": "senat", "chambre": "Senat"}


# --------------------------------------------------------------------------
# Ce qui empêche le retrait
# --------------------------------------------------------------------------

def test_un_libelle_absent_de_la_table_n_est_jamais_propose():
    """LE défaut de la première version, et il aurait effacé des faits.

    `table.get(label)` rend `None` pour un libellé absent de la table ; comme
    cinq appartenances sénatoriales sont publiées **sans nom**, `None` était
    dans l'ensemble des libellés publiés, et `None in publies` était vrai.
    Mesuré sur le corpus : 17 mandats de député de `jean-luc-melenchon`,
    « Commission des affaires étrangères » 2017-2022 comprise, étaient proposés
    au retrait.
    """
    profil = {"mandats": [
        _herite("Commission des affaires étrangères"),
        _senatorial(None),               # l'appartenance sans nom, celle qui piégeait
        _senatorial("Chrétiens d'Orient"),
    ]}

    assert mandats_apparies_remplaces(profil) == []


def test_les_libelles_publies_excluent_l_absence_de_nom():
    assert _labels_publies([None, "", "  Culture  ", "Économie"]) == {"  Culture  ", "Économie"}


def test_sans_remplacant_publie_rien_n_est_propose():
    """La table dit ce qui *devrait* remplacer ; elle ne prouve pas que la
    collecte l'a publié. Sans ce contrôle, un renommage côté source retirerait
    le fait hérité sans que rien ne prenne sa place."""
    profil = {"mandats": [
        _herite("Groupe Chrétiens d'Orient", "groupe_amitie"),
        _senatorial("Groupe d'études Élevage", "groupe_etudes"),
    ]}

    assert mandats_apparies_remplaces(profil) == []


def test_un_mandat_electif_reste_hors_de_ce_perimetre():
    """Ils ont leur propre fonction, et leur critère est le recouvrement de
    période — pas le nom (#885 point 5)."""
    profil = {"mandats": [
        {"label": "Chrétiens d'Orient", "categorie": "mandat_electif"},
        _senatorial("Chrétiens d'Orient"),
    ]}

    assert mandats_apparies_remplaces(profil) == []


def test_une_entree_deja_estampillee_n_est_pas_touchee():
    profil = {"mandats": [
        dict(_herite("Groupe Chrétiens d'Orient", "groupe_amitie"), categorie_source="an"),
        _senatorial("Chrétiens d'Orient"),
    ]}

    assert mandats_apparies_remplaces(profil) == []


# --------------------------------------------------------------------------
# Ce qui l'autorise
# --------------------------------------------------------------------------

def test_une_entree_appariee_dont_le_remplacant_est_publie_est_proposee():
    herite = _herite("Groupe Chrétiens d'Orient", "groupe_amitie")
    profil = {"mandats": [herite, _senatorial("Chrétiens d'Orient", "autre")]}

    assert mandats_apparies_remplaces(profil) == [herite]


def test_le_brut_lit_ses_remplacants_dans_son_propre_bloc_senatorial():
    """Les deux couches se contrôlent l'une l'autre (#729) : faire dépendre le
    brut du pivot inverserait le sens de la chaîne."""
    herite = _herite("Groupe Chrétiens d'Orient", "groupe_amitie")
    brut = {"mandats": [herite],
            "mandat_senatorial": {"mandats_senatoriaux": [{"label": "Chrétiens d'Orient"}]}}

    assert mandats_bruts_apparies_remplaces(brut) == [herite]


def test_sans_bloc_senatorial_le_brut_ne_propose_rien():
    brut = {"mandats": [_herite("Groupe Chrétiens d'Orient", "groupe_amitie")]}

    assert mandats_bruts_apparies_remplaces(brut) == []


# --------------------------------------------------------------------------
# La garde du marqueur
# --------------------------------------------------------------------------

def _profil_complet(mandats, sources=None):
    return {"mandats": mandats,
            "sources": sources if sources is not None else [
                {"type": "nossenateurs", "url": "https://archive.nossenateurs.fr/x"},
                {"type": "assemblee_nationale", "url": "https://data.assemblee-nationale.fr/"},
            ],
            "meta": {"licence_donnees": "à recomposer"}}


def test_le_marqueur_reste_tant_qu_une_donnee_en_derive():
    """§2 règle 2 : l'attribution est due tant que la donnée est publiée.

    La garde porte sur un parcours **récursif** de ce que le document contient,
    clés de dict comprises — pas sur l'absence de `categorie_source`. La
    première version faisait l'inverse, et le test ci-dessous dit pourquoi.
    """
    profil = _profil_complet([
        _herite("Groupe Chrétiens d'Orient", "groupe_amitie"),
        _senatorial("Chrétiens d'Orient", "autre"),
    ])
    profil["interventions"] = [{"source_url": "https://www.nosdeputes.fr/x/2020"}]

    rendu = traiter("x", profil, None)

    assert rendu["mandats_pivot"] == 1
    assert rendu["marqueur_retire"] is False
    assert rendu["marqueur_retenu_par"] == [".interventions[].source_url"]
    assert any(s["type"] == "nossenateurs" for s in profil["sources"])


def test_des_mandats_non_estampilles_ne_retiennent_pas_le_marqueur():
    """Le défaut de la première garde, et il bloquait un retrait légitime.

    Elle listait les appartenances **non estampillées** et refusait le retrait
    tant qu'il en restait. `jean-luc-melenchon` en porte 18 — « Commission des
    affaires étrangères », 2017-2022 — qui sont des mandats de **député**, sans
    aucun rapport avec Regards Citoyens. Une estampille absente veut dire
    « personne n'a établi cette catégorie » (#718), jamais « cela en vient ».
    """
    profil = _profil_complet([
        _herite("Commission des affaires étrangères"),
        _senatorial("Chrétiens d'Orient", "autre"),
    ])

    rendu = traiter("x", profil, None)

    assert rendu["marqueur_retire"] is True
    assert rendu["marqueur_retenu_par"] == []


def test_une_phrase_de_couverture_ne_retient_pas_le_marqueur():
    """La donnée d'un côté, la phrase qui la décrit de l'autre.

    `couverture[].preuve` est un champ **dérivé**, recomposé à chaque run, et
    celle de `bruno-retailleau` raconte un certificat TLS expiré sur
    `archive.nossenateurs.fr`. Elle cite un domaine ; elle ne publie aucune
    donnée qui en vienne, et l'attribution n'est due que pour la donnée.
    """
    profil = _profil_complet([_senatorial("Chrétiens d'Orient", "autre")])
    profil["couverture"] = {"interventions": [
        {"etat": "non_collecte", "preuve": "certificat TLS expiré sur archive.nossenateurs.fr"}]}

    rendu = traiter("x", profil, None)

    assert rendu["marqueur_retire"] is True


def test_le_marqueur_part_quand_plus_rien_ne_le_retient():
    profil = _profil_complet([
        _herite("Groupe Chrétiens d'Orient", "groupe_amitie"),
        _senatorial("Chrétiens d'Orient", "autre"),
    ])
    brut = {"mandats": [_herite("Groupe Chrétiens d'Orient", "groupe_amitie")],
            "mandat_senatorial": {"mandats_senatoriaux": [{"label": "Chrétiens d'Orient"}]},
            "meta": {"synchro_sources": {"nosdeputes": "2026-08-20", "assemblee_nationale": "x"}}}

    rendu = traiter("x", profil, brut)

    assert rendu["marqueur_retire"] is True
    assert [s["type"] for s in profil["sources"]] == ["assemblee_nationale"]
    assert "nosdeputes" not in brut["meta"]["synchro_sources"]
    assert brut["meta"]["synchro_sources"]["assemblee_nationale"] == "x"


def test_la_licence_est_recomposee_et_non_reecrite():
    """Champ dérivé : `licences.py` en est la seule fabrique (§7, #909)."""
    profil = _profil_complet([
        _herite("Groupe Chrétiens d'Orient", "groupe_amitie"),
        _senatorial("Chrétiens d'Orient", "autre"),
    ])

    rendu = traiter("x", profil, None)

    assert "ODbL" not in profil["meta"]["licence_donnees"]
    assert rendu["licence_apres"] == profil["meta"]["licence_donnees"]


# --------------------------------------------------------------------------
# La table elle-même
# --------------------------------------------------------------------------

def test_la_table_couvre_les_huit_entrees_heritees_mesurees():
    assert len(APPARIEMENTS_HERITES) == 8


@pytest.mark.parametrize("hérité, sénatorial", sorted(APPARIEMENTS_HERITES.items()))
def test_chaque_ligne_nomme_un_remplacant_non_vide(hérité, sénatorial):
    assert hérité and sénatorial


# --------------------------------------------------------------------------
# Les entrées périmées, que la fusion additive a laissées à côté des neuves
# --------------------------------------------------------------------------

def _brut_senatorial(entrees):
    return {"mandats": [], "mandat_senatorial": {"mandats_senatoriaux": entrees}}


def test_une_entree_que_la_collecte_ne_produit_plus_est_orpheline():
    """Le défaut que #912 a créé dans la donnée, sans en créer dans le code.

    La fusion des profils est additive : un libellé corrigé n'en remplace pas
    un, il s'ajoute. Le run du 13/09/2026 a publié « Culture » ET « Commission
    de la culture… » pour la même période — 126 entrées sénatoriales sur
    `bruno-retailleau` pour 101 collectées.
    """
    perimee = _senatorial("Culture", "commission", "2023-10-04", "2024-01-17")
    courante = _senatorial("Commission de la culture, de l'éducation et de la communication",
                           "commission", "2023-10-04", "2024-01-17")
    profil = {"mandats": [perimee, courante]}
    brut = _brut_senatorial([
        {"famille": "commission", "label": "Commission de la culture, de l'éducation et de la communication",
         "debut": "2023-10-04", "fin": "2024-01-17"},
    ])

    assert mandats_senatoriaux_orphelins(profil, brut) == [perimee]


def test_le_brut_est_compare_APRES_normalisation():
    """Sans cela, le critère désignait une entrée légitime comme orpheline.

    `normalize_senat` transforme le libellé : « Groupe UMP » y devient « Groupe
    UMP (rattaché) ». Comparer le brut au pivot tel quel proposait donc au
    retrait l'appartenance de `bruno-retailleau` au groupe UMP, 2011-2012 — un
    fait que la source publie.
    """
    publiee = _senatorial("Groupe UMP (rattaché)", "groupe_politique", "2011-10-01", "2012-11-06")
    brut = _brut_senatorial([
        {"famille": "groupe_politique", "label": "Groupe UMP", "organe_code": "UMP",
         "debut": "2011-10-01", "fin": "2012-11-06",
         "type_appartenance": "Rattaché", "type_appartenance_code": "R"},
    ])

    assert mandats_senatoriaux_orphelins({"mandats": [publiee]}, brut) == []


def test_sans_collecte_senatoriale_rien_n_est_propose():
    """« Plus produit » et « pas encore collecté » ne se distinguent pas quand
    le bloc est vide, et seul le premier justifie un retrait (§2 règle 5)."""
    publiee = _senatorial("Culture", "commission")

    assert mandats_senatoriaux_orphelins({"mandats": [publiee]}, _brut_senatorial([])) == []
    assert mandats_senatoriaux_orphelins({"mandats": [publiee]}, {"mandats": []}) == []


def test_une_entree_non_senatoriale_n_est_jamais_orpheline():
    """La comparaison ne vaut que pour ce que la collecte sénatoriale produit."""
    an = {"label": "Commission des affaires étrangères", "categorie": "commission",
          "categorie_source": "an", "debut": "2017-06-29", "fin": "2019-01-29"}
    brut = _brut_senatorial([{"famille": "commission", "label": "Culture",
                              "debut": "2023-10-04", "fin": None}])

    assert mandats_senatoriaux_orphelins({"mandats": [an]}, brut) == []
