"""Quelle source a rempli quel champ, et quand (#603, lot 4 de #598).

Le critère de sortie de l'issue : « pour tout champ composé, on peut nommer la
source qui l'a renseigné et la date de cette synchronisation — **ou lire
explicitement que ce n'est pas connu** ». Les deux moitiés comptent, et la
seconde est celle qui se perd : une provenance inconnue se **déclare**
(`source: null`), elle ne s'omet pas — sans quoi l'absence d'entrée deviendrait
une seconde façon de dire « on ne sait pas », à côté de celle qui le dit déjà.

Portée du lot, et c'est une décision : **`identite` seule**. La provenance par
champ ne répond à une question que là où plusieurs sources écrivent le même
champ. `src/group_profile.py` ne lit jamais `identite` (zéro occurrence,
30/08/2026) et ne consomme que des listes, déjà fusionnées additivement — sur
une liste, l'entrée porte sa source.

Le piège que ces tests verrouillent : `sources[0]` aurait « marché » et aurait
attribué 2 597 des 2 612 champs d'identité des 481 profils publiés à
`nosdeputes`, source retirée du pipeline depuis #529, sur la seule foi de
l'ordre d'une liste. `test_une_source_ambigue_ne_sinvente_pas` tombe sur cette
version-là.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from merge_profile import (  # noqa: E402
    ORIGINE_ANCIENNE,
    ORIGINE_NOUVELLE,
    REGLES_META,
    _composer_identite,
    deriver_provenance_champs,
    fusionner_identite,
    merge_pivot_profile,
    source_ecrivain,
)
from schema_pivot import (  # noqa: E402
    BLOCS_PROVENANCE_CHAMPS,
    valider_provenance_champs,
    validate_profil,
)

SYNCHRO_AN = "2026-08-30T11:03:23+0000"
SYNCHRO_PE = "2026-08-28T09:00:00+0000"

SOURCE_AN = [{
    "type": "assemblee_nationale",
    "url": "https://data.assemblee-nationale.fr/",
    "synchro_le": SYNCHRO_AN,
}]
SOURCE_PE = [{
    "type": "europarl",
    "url": "https://data.europarl.europa.eu/",
    "synchro_le": SYNCHRO_PE,
}]


def _pivot(**extra) -> dict:
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
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-08-30T11:03:23+0000",
            "licence_donnees": "Licence Ouverte",
            "provenance": "candidat_declare",
            "warnings": [],
        },
    }
    base.update(extra)
    return base


def _provenance(profil: dict) -> dict:
    return (profil.get("meta") or {}).get("provenance_champs") or {}


# ---------------------------------------------------------------------------
# Le critère de sortie
# ---------------------------------------------------------------------------

def test_un_champ_pris_au_nouvel_ecrivain_nomme_sa_source_et_sa_date():
    ancien = _pivot(sources=list(SOURCE_PE), identite={"profession": "Sénateur"})
    neuf = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["identite"]["profession"] == "Professeur"
    assert _provenance(fusionne)["identite"]["profession"] == {
        "source": "assemblee_nationale",
        "synchro_le": SYNCHRO_AN,
    }


def test_un_champ_garde_de_lancien_profil_garde_la_provenance_de_lancien():
    """La chaîne : la valeur et son origine traversent les runs ensemble.

    Le nouvel écrivain ne dit rien de `profession` ; #601 fait survivre la
    valeur, ce lot fait survivre la source qui l'a dite — sans quoi la
    permanence d'un champ produirait une valeur publiée sans origine.
    """
    ancien = _pivot(sources=list(SOURCE_PE), identite={"profession": "Professeur"})
    ancien["meta"]["provenance_champs"] = {
        "identite": {"profession": {"source": "europarl", "synchro_le": SYNCHRO_PE}}
    }
    neuf = _pivot(sources=list(SOURCE_AN),
                  identite={"profession": None, "date_naissance": "1951-08-19"})

    fusionne = merge_pivot_profile(ancien, neuf)
    provenance = _provenance(fusionne)["identite"]

    assert fusionne["identite"]["profession"] == "Professeur"
    assert provenance["profession"] == {"source": "europarl", "synchro_le": SYNCHRO_PE}
    assert provenance["date_naissance"] == {
        "source": "assemblee_nationale", "synchro_le": SYNCHRO_AN,
    }


def test_une_provenance_inconnue_se_declare_au_lieu_de_sabsenter():
    """Un profil publié avant ce lot ne consigne rien. Le champ qu'on lui garde
    est publié avec `source: null` — lisible — et non sans entrée."""
    ancien = _pivot(
        sources=[{"type": "nosdeputes", "url": "https://www.nosdeputes.fr/x",
                  "synchro_le": "2026-08-19T00:00:00+0000"},
                 {"type": "assemblee_nationale",
                  "url": "https://data.assemblee-nationale.fr/",
                  "synchro_le": SYNCHRO_AN}],
        identite={"profession": "Professeur"},
    )
    neuf = _pivot(sources=list(SOURCE_AN), identite={"profession": None})

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["identite"]["profession"] == "Professeur"
    assert _provenance(fusionne)["identite"]["profession"] == {
        "source": None, "synchro_le": None,
    }


def test_une_source_ambigue_ne_sinvente_pas():
    """Le piège du lot. Un profil qui déclare PLUSIEURS types de source n'est pas
    un écrivain : `_merge_pivot_sources` unit par type, et 475 des 481 profils
    publiés portent encore une entrée `nosdeputes` retirée par #529.

    `sources[0]` aurait rendu `nosdeputes` — une provenance fausse, qui se lit
    comme une preuve.
    """
    ambigu = _pivot(
        sources=[{"type": "nosdeputes", "url": "https://www.nosdeputes.fr/x",
                  "synchro_le": "2026-08-19T00:00:00+0000"},
                 {"type": "assemblee_nationale",
                  "url": "https://data.assemblee-nationale.fr/",
                  "synchro_le": SYNCHRO_AN}],
        identite={"profession": "Professeur"},
    )
    assert source_ecrivain(ambigu) == (None, None)

    ancien = _pivot(sources=list(SOURCE_PE), identite={"profession": "Sénateur"})
    fusionne = merge_pivot_profile(ancien, ambigu)

    assert fusionne["identite"]["profession"] == "Professeur"
    assert _provenance(fusionne)["identite"]["profession"] == {
        "source": None, "synchro_le": None,
    }


def test_deux_entrees_du_meme_type_restent_un_ecrivain_identifiable():
    """`normalize_profil` écrit une seconde entrée pour la source des votes,
    du même type. Un écrivain reste un écrivain, et sa synchro est la plus
    récente des deux — jamais celle qu'un ordre de liste désigne."""
    ecrivain = _pivot(
        sources=[{"type": "assemblee_nationale",
                  "url": "https://data.assemblee-nationale.fr/",
                  "synchro_le": "2026-08-27T08:00:00+0000"},
                 {"type": "assemblee_nationale",
                  "url": "https://data.assemblee-nationale.fr/",
                  "synchro_le": SYNCHRO_AN}],
        identite={"profession": "Professeur"},
    )

    assert source_ecrivain(ecrivain) == ("assemblee_nationale", SYNCHRO_AN)


def test_un_champ_nul_na_pas_dentree_de_provenance():
    """Il n'y a pas de valeur dont nommer l'origine."""
    ancien = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})
    neuf = _pivot(sources=list(SOURCE_AN),
                  identite={"profession": "Professeur", "lieu_naissance": None})

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["identite"]["lieu_naissance"] is None
    assert "lieu_naissance" not in _provenance(fusionne)["identite"]


def test_le_premier_ecrit_dun_profil_porte_deja_sa_provenance():
    """Sans ce chemin, deux profils de même contenu seraient publiés dont un
    seul traçable, selon qu'un fichier existait déjà."""
    neuf = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})

    fusionne = merge_pivot_profile(None, neuf)

    assert _provenance(fusionne)["identite"]["profession"] == {
        "source": "assemblee_nationale", "synchro_le": SYNCHRO_AN,
    }


def test_pas_didentite_publiee_pas_de_bloc_de_provenance():
    """Un `{}` dirait « aucun champ n'a de provenance » là où la vérité est
    « ce profil n'a pas d'identité publiée » — le cas des 4 profils de #539."""
    ancien = _pivot(sources=list(SOURCE_AN), identite=None)
    neuf = _pivot(sources=list(SOURCE_AN), identite=None)

    fusionne = merge_pivot_profile(ancien, neuf)

    assert "provenance_champs" not in fusionne["meta"]


# ---------------------------------------------------------------------------
# Ce que la provenance n'a pas le droit d'être
# ---------------------------------------------------------------------------

def test_la_provenance_est_recalculee_et_jamais_fusionnee():
    """Patron de `chambres` (#493) et de `licence_donnees` (#530).

    Fusionner clé par clé garderait la provenance de l'ancien écrivain à côté de
    la valeur du nouveau : l'inverse exact de ce que le bloc existe pour dire.
    """
    ancien = _pivot(sources=list(SOURCE_PE), identite={"profession": "Sénateur"})
    ancien["meta"]["provenance_champs"] = {
        "identite": {"profession": {"source": "europarl", "synchro_le": SYNCHRO_PE}}
    }
    neuf = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["identite"]["profession"] == "Professeur"
    assert _provenance(fusionne)["identite"]["profession"]["source"] == "assemblee_nationale"


def test_la_provenance_ne_vit_pas_dans_identite():
    """`identite` est un dictionnaire champ → VALEUR, et l'interface l'itère
    comme tel. Une clé de provenance dedans obligerait chaque lecteur à
    connaître la liste des clés à sauter."""
    ancien = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})
    neuf = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})

    fusionne = merge_pivot_profile(ancien, neuf)

    assert set(fusionne["identite"]) == {"profession"}


def test_toute_valeur_publiee_a_son_entree_et_reciproquement():
    """Le critère de sortie, vérifié sur le profil publié plutôt que sur une
    fonction : c'est ce que `validate_profil` fera respecter en CI."""
    ancien = _pivot(sources=list(SOURCE_PE), identite={
        "profession": "Sénateur", "date_naissance": None, "num_circo": "4",
    })
    neuf = _pivot(sources=list(SOURCE_AN), identite={
        "profession": "Professeur", "date_naissance": "1951-08-19", "num_circo": None,
    })

    fusionne = merge_pivot_profile(ancien, neuf)
    publies = {c for c, v in fusionne["identite"].items() if v not in (None, "", [], {})}

    assert set(_provenance(fusionne)["identite"]) == publies
    assert validate_profil(fusionne) == []


def test_la_composition_didentite_rend_le_meme_bloc_quavant():
    """`_composer_identite` est la MÊME décision que `fusionner_identite`, dite
    en plus. Deux lectures d'une même décision divergent — c'est le piège que
    `_accorder_hatvp` a dû rattraper au #601, et ici rien ne le rattraperait."""
    ancien = {"profession": "Sénateur", "num_circo": "4"}
    neuf = {"profession": "Professeur", "num_circo": None}

    bloc, origines = _composer_identite(ancien, neuf)

    assert bloc == fusionner_identite(ancien, neuf)
    assert origines == {"profession": ORIGINE_NOUVELLE, "num_circo": ORIGINE_ANCIENNE}


def test_provenance_champs_a_sa_regle_nommee_dans_regles_meta():
    """#600 refuse qu'une clé de `meta` soit prise « au hasard »."""
    assert "provenance_champs" in REGLES_META


# ---------------------------------------------------------------------------
# La contrainte de schéma
# ---------------------------------------------------------------------------

def _profil_valide() -> dict:
    return {
        "identite": {"profession": "Professeur"},
        "meta": {"provenance_champs": {
            "identite": {"profession": {"source": "assemblee_nationale",
                                        "synchro_le": SYNCHRO_AN}}
        }},
    }


def test_un_bloc_conforme_ne_leve_aucune_erreur():
    profil = _profil_valide()
    assert valider_provenance_champs(
        profil["meta"]["provenance_champs"], profil) == []


def test_un_champ_publie_sans_provenance_est_refuse():
    profil = _profil_valide()
    profil["identite"]["date_naissance"] = "1951-08-19"

    erreurs = valider_provenance_champs(profil["meta"]["provenance_champs"], profil)

    assert any("incomplète" in e and "date_naissance" in e for e in erreurs)


def test_une_provenance_sans_champ_publie_est_refusee():
    profil = _profil_valide()
    profil["meta"]["provenance_champs"]["identite"]["lieu_naissance"] = {
        "source": "assemblee_nationale", "synchro_le": SYNCHRO_AN,
    }

    erreurs = valider_provenance_champs(profil["meta"]["provenance_champs"], profil)

    assert any("ne publie pas" in e and "lieu_naissance" in e for e in erreurs)


def test_une_date_sans_source_est_refusee():
    """Un horodatage que rien ne rattache à une source n'est pas une
    traçabilité : c'est la forme d'une preuve qui n'en est pas une (§2.2)."""
    profil = _profil_valide()
    profil["meta"]["provenance_champs"]["identite"]["profession"] = {
        "source": None, "synchro_le": SYNCHRO_AN,
    }

    erreurs = valider_provenance_champs(profil["meta"]["provenance_champs"], profil)

    assert any("date une provenance qu'elle ne nomme pas" in e for e in erreurs)


def test_une_source_hors_nomenclature_est_refusee():
    profil = _profil_valide()
    profil["meta"]["provenance_champs"]["identite"]["profession"]["source"] = "wikipedia"

    erreurs = valider_provenance_champs(profil["meta"]["provenance_champs"], profil)

    assert any("source non reconnue" in e for e in erreurs)


def test_un_bloc_hors_nomenclature_est_refuse():
    profil = _profil_valide()
    profil["meta"]["provenance_champs"]["mandats"] = {}

    erreurs = valider_provenance_champs(profil["meta"]["provenance_champs"], profil)

    assert any("hors nomenclature" in e for e in erreurs)
    assert "mandats" not in BLOCS_PROVENANCE_CHAMPS


def test_une_entree_aux_mauvaises_cles_est_refusee():
    profil = _profil_valide()
    profil["meta"]["provenance_champs"]["identite"]["profession"] = {
        "source": "assemblee_nationale", "url": "https://..."
    }

    erreurs = valider_provenance_champs(profil["meta"]["provenance_champs"], profil)

    assert any("attendu exactement" in e for e in erreurs)


def test_un_profil_sans_le_bloc_reste_valide():
    """Les 481 profils publiés avant ce lot ne le portent pas : les déclarer
    invalides ne dirait rien de vrai sur eux (précédent de #539)."""
    profil = _pivot(sources=list(SOURCE_AN), identite={"profession": "Professeur"})

    assert "provenance_champs" not in profil["meta"]
    assert validate_profil(profil) == []


def test_deriver_ne_rend_rien_sur_un_bloc_absent():
    assert deriver_provenance_champs(None, {}, None, _pivot()) == {}
