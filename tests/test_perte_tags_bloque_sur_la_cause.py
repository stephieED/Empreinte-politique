"""Une baisse de `tags_thematiques` ne bloque que si sa cause est une perte.

Les runs des 10 et 11/10/2026 ont échoué sur 7 profils à −1 tag. L'Assemblée
avait unifié deux intitulés du même texte ; un profil qui portait les deux n'en
portait plus qu'un, sans qu'aucune intervention ait perdu le sien.

Les deux interventions ci-dessous sont copiées de
`pivot_data/profiles/david-magnier.pivot.json` au 09/10/2026 (un des 7 profils),
`texte` raccourci. Le renommage est rejoué à la main sur la seconde : la sortie
du run en échec n'est pas publiée.
"""

import copy

from audit_diff_profils import (
    COLLECTION_PROFILS,
    comparer,
    generate_markdown_report,
    relever,
)
from schema_pivot import deriver_tags_thematiques, porte_un_tag_thematique

AUX = ("Réponse intégrale aux violences sexuelles et sexistes contre les "
       "femmes et les enfants")
AU_PHENOMENE = ("Réponse intégrale au phénomène des violences sexuelles et "
                "sexistes contre les femmes et les enfants")

INTERVENTIONS = [
    {
        "intervention_id": "syceron_CRSANR5L17S2027O1N006_000088",
        "date": "2026-10-02",
        "type_detail": "debat",
        "theme_officiel": AUX,
        "source_url": "https://data.assemblee-nationale.fr/static/openData/"
                      "repository/17/vp/syceronbrut/syseron.xml.zip",
        "source": {"type": "syceron", "url": None, "source_id": None,
                   "legislature": "17"},
        "collecte": "extrait",
        "texte": "Le Rassemblement national soutient l’esprit de l’article 12",
        "texte_tronque": True,
        "id_syceron": "4171560",
    },
    {
        "intervention_id": "syceron_CRSANR5L17S2027O1N011_000242",
        "date": "2026-10-07",
        "type_detail": "debat",
        "theme_officiel": AU_PHENOMENE,
        "source_url": "https://data.assemblee-nationale.fr/static/openData/"
                      "repository/17/vp/syceronbrut/syseron.xml.zip",
        "source": {"type": "syceron", "url": None, "source_id": None,
                   "legislature": "17"},
        "collecte": "extrait",
        "texte": "Avec cet article 24, nous mettons des mots et, surtout, une "
                 "sanction pénale",
        "texte_tronque": True,
        "id_syceron": "4175686",
    },
]


def _profil(interventions):
    return {
        "interventions": interventions,
        "tags_thematiques": deriver_tags_thematiques(interventions),
    }


def _comparer(avant, apres):
    return comparer(
        {"david-magnier.pivot.json": relever(avant, COLLECTION_PROFILS)},
        {"david-magnier.pivot.json": relever(apres, COLLECTION_PROFILS)},
        COLLECTION_PROFILS,
    )


def _renommees():
    apres = copy.deepcopy(INTERVENTIONS)
    apres[1]["theme_officiel"] = AUX
    return apres


def test_deux_intitules_reunis_par_la_source_ne_bloquent_pas():
    avant, apres = _profil(INTERVENTIONS), _profil(_renommees())
    assert (len(avant["tags_thematiques"]), len(apres["tags_thematiques"])) == (2, 1)

    r = _comparer(avant, apres)

    assert r["bloquant"] is False
    assert r["pertes_sur_champs_stables"] == []
    (perte,) = r["pertes"]
    assert (perte["champ"], perte["avant"], perte["apres"]) == ("tags_thematiques", 2, 1)
    assert perte["renommage_dans"] == "interventions"


def test_l_intitule_disparu_reste_nomme():
    r = _comparer(_profil(INTERVENTIONS), _profil(_renommees()))
    (echange,) = r["echanges"]
    assert echange["disparues"] == [AU_PHENOMENE.lower()]


def test_une_intervention_qui_perd_son_intitule_bloque():
    apres = copy.deepcopy(INTERVENTIONS)
    apres[1]["theme_officiel"] = None

    r = _comparer(_profil(INTERVENTIONS), _profil(apres))

    assert r["bloquant"] is True
    (perte,) = r["pertes_sur_champs_stables"]
    assert perte["champ"] == "tags_thematiques"
    assert "renommage_dans" not in perte


def test_une_intervention_disparue_bloque_sur_les_deux_listes():
    r = _comparer(_profil(INTERVENTIONS), _profil(INTERVENTIONS[:1]))

    assert r["bloquant"] is True
    assert {p["champ"] for p in r["pertes_sur_champs_stables"]} == {
        "interventions", "tags_thematiques"}


def test_le_cas_de_470_bloque_toujours():
    """647 → 0 : les tags tombent parce que les intitulés ont tous disparu."""
    apres = copy.deepcopy(INTERVENTIONS)
    for intervention in apres:
        intervention["theme_officiel"] = None

    r = _comparer(_profil(INTERVENTIONS), _profil(apres))

    assert r["bloquant"] is True


def test_un_renommage_a_cote_d_un_intitule_perdu_bloque():
    """Autant d'interventions, mais une de moins alimente les tags."""
    troisieme = copy.deepcopy(INTERVENTIONS[0])
    troisieme.update(intervention_id="syceron_fictif_000001", id_syceron="1",
                     theme_officiel="Projet de loi de finances pour 2027")
    avant = INTERVENTIONS + [troisieme]
    apres = _renommees() + [dict(troisieme, theme_officiel=None)]

    r = _comparer(_profil(avant), _profil(apres))

    assert r["bloquant"] is True


def test_un_compte_qu_on_n_a_pas_pu_prendre_ne_leve_pas_le_blocage():
    """Un profil sans liste `interventions` : la cause n'est pas mesurable."""
    r = _comparer({"tags_thematiques": ["a", "b"]}, {"tags_thematiques": ["a"]})

    assert r["bloquant"] is True


def test_une_autre_liste_stable_ne_profite_pas_de_l_exception():
    avant = dict(_profil(INTERVENTIONS), votes=[{"scrutin_id": "1"}, {"scrutin_id": "2"}])
    apres = dict(_profil(INTERVENTIONS), votes=[{"scrutin_id": "1"}])

    r = _comparer(avant, apres)

    assert r["bloquant"] is True
    assert [p["champ"] for p in r["pertes_sur_champs_stables"]] == ["votes"]


def test_le_predicat_lit_comme_la_fabrique():
    """`porte_un_tag_thematique` et `deriver_tags_thematiques` : une seule règle."""
    cas = INTERVENTIONS + [
        {"theme_officiel": None},
        {"theme_officiel": "   "},
        {"theme_officiel": ""},
        {"theme_officiel": None, "mots_cles": ["budget"]},
        {"theme_officiel": None, "mots_cles": ["  ", None]},
        {"mots_cles": []},
        "pas un objet",
    ]
    for entree in cas:
        assert porte_un_tag_thematique(entree) is bool(
            deriver_tags_thematiques([entree])), entree


def test_le_rapport_dit_pourquoi_la_baisse_ne_bloque_pas():
    r = _comparer(_profil(INTERVENTIONS), _profil(_renommees()))
    r.update(absente_avant=False, absente_apres=False)
    rapport = {"collections": [r], "collections_ignorees": [], "bloquant": False,
               "nb_pertes_bloquantes": 0}

    markdown = generate_markdown_report(rapport, "HEAD")

    assert "sans perte en amont" in markdown
    assert "Aucune perte bloquante." in markdown
