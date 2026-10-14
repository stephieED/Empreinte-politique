"""Une baisse de `tags_thematiques_agreges` bloque sur sa cause, lue dans les profils.

Le run planifié du 13/10/2026 (`38431031465`) a échoué au contrôle de perte sur
4 fiches à −1 tag : `groupe-AN-DR-17`, `groupe-AN-EPR-17`, `lignee-AN-LR`,
`lignee-AN-REN`. Le même run retirait le même intitulé de 5 profils, sans perte
en amont, et ceux-là passaient déjà depuis #1275. La fiche de groupe ne porte
pas les interventions : la cause se lit dans la collection des profils.

L'entrée de groupe est copiée de `pivot_data/groupes/groupe-AN-EPR-17.json` au
12/10/2026 ; les interventions, de `david-magnier.pivot.json` au 09/10/2026
(voir `test_perte_tags_bloque_sur_la_cause`).
"""

import copy

from audit_diff_profils import (
    COLLECTION_GROUPES,
    COLLECTION_LIGNEES,
    COLLECTION_PARTIS,
    COLLECTION_PROFILS,
    SOURCE_DES_TAGS_AGREGES,
    comparer_tout,
    generate_markdown_report,
    relever,
)
from schema_pivot import deriver_tags_thematiques
from test_perte_tags_bloque_sur_la_cause import AU_PHENOMENE, AUX, INTERVENTIONS

PHENOMENE = AU_PHENOMENE.lower()
GLOBE = "accord multilatéral sur l’échange des informations globe"

ENTREE_PHENOMENE = {
    "tag": PHENOMENE,
    "nb_membres_porteurs": 2,
    "poids_relatif": 0.0163,
    "nb_membres_porteurs_par_fenetre": {"12_mois": 2, "6_mois": 2},
}
ENTREE_GLOBE = {
    "tag": GLOBE,
    "nb_membres_porteurs": 1,
    "poids_relatif": 0.0081,
    "nb_membres_porteurs_par_fenetre": {"12_mois": 1, "6_mois": 1},
}
ENTREE_AUX = dict(ENTREE_PHENOMENE, tag=AUX.lower())


def _profil(interventions):
    return {"interventions": interventions,
            "tags_thematiques": deriver_tags_thematiques(interventions)}


def _renommees():
    apres = copy.deepcopy(INTERVENTIONS)
    apres[1]["theme_officiel"] = AUX
    return apres


def _groupe(tags):
    return {"membres": [{"id": "david-magnier"}], "tags_thematiques_agreges": tags}


def _verdict(profil_avant, profil_apres, groupe_avant, groupe_apres,
             collection=COLLECTION_GROUPES):
    fichier = "groupe-AN-EPR-17.json"
    return comparer_tout([
        (COLLECTION_PROFILS,
         {"david-magnier.pivot.json": relever(profil_avant, COLLECTION_PROFILS)},
         {"david-magnier.pivot.json": relever(profil_apres, COLLECTION_PROFILS)}),
        (collection,
         {fichier: relever(groupe_avant, collection)},
         {fichier: relever(groupe_apres, collection)}),
    ])


def test_un_intitule_renomme_dans_les_profils_ne_bloque_pas_le_groupe():
    r = _verdict(_profil(INTERVENTIONS), _profil(_renommees()),
                 _groupe([ENTREE_AUX, ENTREE_PHENOMENE]), _groupe([ENTREE_AUX]))

    assert r["bloquant"] is False
    (perte,) = r["collections"][1]["pertes"]
    assert (perte["champ"], perte["avant"], perte["apres"]) == (
        "tags_thematiques_agreges", 2, 1)
    assert perte["renommage_dans"] == SOURCE_DES_TAGS_AGREGES


def test_les_lignees_et_les_partis_suivent_la_meme_regle():
    for collection in (COLLECTION_LIGNEES, COLLECTION_PARTIS):
        r = _verdict(_profil(INTERVENTIONS), _profil(_renommees()),
                     _groupe([ENTREE_AUX, ENTREE_PHENOMENE]), _groupe([ENTREE_AUX]),
                     collection)
        assert r["bloquant"] is False, collection.nom


def test_un_intitule_qu_aucun_profil_n_a_perdu_bloque():
    """Un membre sorti de la fenêtre, une règle d'agrégation changée : pas un renommage."""
    r = _verdict(_profil(INTERVENTIONS), _profil(INTERVENTIONS),
                 _groupe([ENTREE_AUX, ENTREE_PHENOMENE]), _groupe([ENTREE_AUX]))

    assert r["bloquant"] is True
    (perte,) = r["collections"][1]["pertes_sur_champs_stables"]
    assert "renommage_dans" not in perte


def test_un_seul_intitule_inexplique_suffit_a_bloquer():
    """EPR-17 a perdu deux intitulés le 13/10 : les deux doivent venir des profils."""
    r = _verdict(_profil(INTERVENTIONS), _profil(_renommees()),
                 _groupe([ENTREE_AUX, ENTREE_PHENOMENE, ENTREE_GLOBE]),
                 _groupe([ENTREE_AUX]))

    assert r["bloquant"] is True


def test_une_perte_en_amont_dans_les_profils_bloque_aussi_le_groupe():
    """L'intitulé a quitté le profil parce que l'intervention a disparu (#470)."""
    r = _verdict(_profil(INTERVENTIONS), _profil(INTERVENTIONS[:1]),
                 _groupe([ENTREE_AUX, ENTREE_PHENOMENE]), _groupe([ENTREE_AUX]))

    assert r["bloquant"] is True
    assert r["collections"][1]["bloquant"] is True


def test_sans_les_profils_la_cause_n_est_pas_mesurable():
    fichier = "groupe-AN-EPR-17.json"
    r = comparer_tout([
        (COLLECTION_GROUPES,
         {fichier: relever(_groupe([ENTREE_AUX, ENTREE_PHENOMENE]), COLLECTION_GROUPES)},
         {fichier: relever(_groupe([ENTREE_AUX]), COLLECTION_GROUPES)}),
    ])

    assert r["bloquant"] is True


def test_une_autre_liste_du_groupe_ne_profite_pas_de_l_exception():
    avant = dict(_groupe([ENTREE_AUX, ENTREE_PHENOMENE]),
                 membres=[{"id": "david-magnier"}, {"id": "aurore-berge"}])
    r = _verdict(_profil(INTERVENTIONS), _profil(_renommees()),
                 avant, _groupe([ENTREE_AUX]))

    assert r["bloquant"] is True
    assert [p["champ"] for p in r["collections"][1]["pertes_sur_champs_stables"]] == [
        "membres"]


def test_chaque_liste_agregee_des_tags_est_relevee_par_ses_valeurs():
    for collection in (COLLECTION_GROUPES, COLLECTION_LIGNEES, COLLECTION_PARTIS):
        assert set(collection.listes_des_tags_des_profils) <= set(collection.listes_nommees)
        assert set(collection.listes_des_tags_des_profils) <= set(collection.listes_stables)


def test_le_rapport_dit_que_les_profils_expliquent_la_baisse():
    r = _verdict(_profil(INTERVENTIONS), _profil(_renommees()),
                 _groupe([ENTREE_AUX, ENTREE_PHENOMENE]), _groupe([ENTREE_AUX]))

    markdown = generate_markdown_report(r, "HEAD")

    assert "expliquée(s) par les profils" in markdown
    assert markdown.count("Aucune perte bloquante.") == 2
