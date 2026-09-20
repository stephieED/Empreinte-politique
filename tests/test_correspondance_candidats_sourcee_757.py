"""La passe sourcée : deux sources doivent s'accorder, sinon rien (#757).

Jumelle de `test_correspondance_derivee_715.py` par la forme, et son opposée par
le fond : là-bas le slug **sortait** de l'acteur, donc l'entrée n'établissait
rien ; ici le slug sort de `slugify(nom)` — un nom saisi dans un fichier
éditorial — et c'est un identifiant externe qui établit le rapprochement.

Ce que ces tests protègent tient en une phrase : **une entrée n'est écrite que
lorsque l'identifiant externe et le profil produit depuis AMO30 disent la même
chose**, et un désaccord entre deux sources n'est jamais moyenné.

Aucun réseau : la passe est hors ligne par construction (#524), et `conftest.py`
échouerait bruyamment si elle sortait.
"""

import json
from pathlib import Path

import pytest

import build_correspondance_acteurs_an as build
from correspondance_acteurs_an import charger_correspondance, vider_memo


def _profil(chemin: Path, nom: str, acteur_ref=None) -> None:
    chemin.write_text(
        json.dumps(
            {
                "nom": nom,
                "identifiants": {"an": acteur_ref},
                "identite": {"civilite": "M.", "date_naissance": "1975-10-18"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _resolution(nom, issue, acteur_ref=None, qid="Q1"):
    return {
        "nom": nom,
        "issue": issue,
        "acteur_ref": acteur_ref,
        "qid": qid,
        "preuve": f"https://www.wikidata.org/wiki/{qid}",
    }


@pytest.fixture
def profils(tmp_path: Path) -> Path:
    dossier = tmp_path / "profiles"
    dossier.mkdir()
    return dossier


# ---------------------------------------------------------------------------
# L'accord : l'entrée est écrite
# ---------------------------------------------------------------------------


def test_un_acteur_corrobore_par_le_profil_donne_une_entree_sourcee(profils):
    _profil(profils / "fabien-roussel.pivot.json", "Fabien Roussel", "PA720692")
    resolutions = {"fabien-roussel": _resolution("Fabien Roussel", "acteur", "PA720692", "Q30388733")}

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert refus == []
    entree = entrees["fabien-roussel"]
    assert entree["identifiants"]["an"] == "PA720692"
    assert entree["origine"] == "sourcee"
    assert entree["ecart"] is None
    # La preuve est l'élément Wikidata, pas la fiche AN : c'est lui qui établit.
    assert entree["preuve"] == "https://www.wikidata.org/wiki/Q30388733"


def test_le_fait_negatif_exige_que_les_deux_sources_se_taisent(profils):
    """`hors_an` n'est pas « Wikidata ne dit rien » : c'est deux silences."""
    _profil(profils / "francois-asselineau.pivot.json", "François Asselineau", None)
    resolutions = {"francois-asselineau": _resolution("François Asselineau", "hors_an", None, "Q12972")}

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert refus == []
    entree = entrees["francois-asselineau"]
    assert entree["identifiants"]["an"] is None
    assert entree["ecart"] == "hors_an"
    assert entree["origine"] == "sourcee"
    assert "P4123" in entree["motif"]
    assert "AMO30" in entree["motif"]
    # La déclaration dit sa portée, comme celles que #539 a écrites à la main.
    assert "Sénat" in entree["motif"]


def test_une_entree_ecrite_passe_le_validateur(profils, tmp_path):
    """Le schéma refuse `origine: derivee` avec un écart ; `sourcee` l'accepte."""
    _profil(profils / "francois-asselineau.pivot.json", "François Asselineau", None)
    resolutions = {"francois-asselineau": _resolution("François Asselineau", "hors_an", None, "Q12972")}
    entrees, _ = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    table = tmp_path / "table.json"
    table.write_text(
        json.dumps(
            {
                "schema_version": "correspondance-acteurs-an-v2",
                "genere_le": "2026-09-07T00:00:00+0000",
                "correspondances": entrees,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    vider_memo()
    chargee = charger_correspondance(table)

    assert chargee["francois-asselineau"]["ecart"] == "hors_an"
    assert chargee["francois-asselineau"]["origine"] == "sourcee"


# ---------------------------------------------------------------------------
# Le désaccord : rien n'est écrit, et le slug est nommé
# ---------------------------------------------------------------------------


def test_deux_acteurs_differents_ne_donnent_aucune_entree(profils):
    """Le défaut de clé collante de #540, sur le seul identifiant du dépôt."""
    _profil(profils / "homonyme.pivot.json", "Homonyme", "PA111")
    resolutions = {"homonyme": _resolution("Homonyme", "acteur", "PA999")}

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert entrees == {}
    assert len(refus) == 1
    assert "PA999" in refus[0] and "PA111" in refus[0]


def test_un_acteur_annonce_mais_absent_du_profil_ne_donne_rien(profils):
    _profil(profils / "sans-identite.pivot.json", "Sans Identité", None)
    resolutions = {"sans-identite": _resolution("Sans Identité", "acteur", "PA999")}

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert entrees == {}
    assert "aucun acteur" in refus[0]


def test_un_hors_an_dementi_par_le_profil_ne_donne_rien(profils):
    """Wikidata ne connaît aucun mandat, AMO30 en a produit un : on n'écrit pas."""
    _profil(profils / "conteste.pivot.json", "Contesté", "PA123")
    resolutions = {"conteste": _resolution("Contesté", "hors_an", None)}

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert entrees == {}
    assert "n'est pas corroboré" in refus[0]


def test_un_profil_publie_sans_resolution_est_un_refus(profils):
    _profil(profils / "selma-labib.pivot.json", "Selma Labib", None)
    resolutions = {"selma-labib": _resolution("Selma Labib", "indetermine", None, None)}
    resolutions["selma-labib"]["preuve"] = None

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert entrees == {}
    assert "à écrire à la main" in refus[0]


# ---------------------------------------------------------------------------
# Les deux filtres de forme, repris de #715
# ---------------------------------------------------------------------------


def test_la_table_passe_devant(profils):
    """Un slug déjà dans la table n'est jamais réécrit — c'est le gel (#708 §3)."""
    _profil(profils / "fabien-roussel.pivot.json", "Fabien Roussel", "PA720692")
    resolutions = {"fabien-roussel": _resolution("Fabien Roussel", "acteur", "PA720692")}
    existante = {"fabien-roussel": {"acteur_ref": "PA720692"}}

    entrees, refus = build.entrees_sourcees(profils, resolutions, existante, "2026-09-07")

    assert entrees == {} and refus == []


def test_un_candidat_non_publie_est_ignore_sans_bruit(profils):
    """La §5b ne bloque que sur les publiés : pas de tampon posé d'avance."""
    resolutions = {"jamais-collecte": _resolution("Jamais Collecté", "acteur", "PA1")}

    entrees, refus = build.entrees_sourcees(profils, resolutions, {}, "2026-09-07")

    assert entrees == {} and refus == []


# ---------------------------------------------------------------------------
# Le fichier de résolutions et la CLI
# ---------------------------------------------------------------------------


def test_les_resolutions_sont_indexees_par_slug(tmp_path):
    """La source rend des noms, la table porte des slugs : une seule conversion."""
    chemin = tmp_path / "resolutions.json"
    chemin.write_text(
        json.dumps(
            {
                "schema_version": "resolutions-candidats-v1",
                "resolutions": {"Fabien Roussel": _resolution("Fabien Roussel", "acteur", "PA720692")},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    resolutions = build.resolutions_candidats(chemin)

    assert list(resolutions) == ["fabien-roussel"]


def test_completer_candidats_exige_ses_resolutions(tmp_path):
    import argparse

    args = argparse.Namespace(
        completer_candidats=True,
        resolutions=None,
        sortie=tmp_path / "table.json",
        profiles_dir=tmp_path,
        verifie_le="2026-09-07",
    )
    assert build.completer_candidats(args) == 2


def test_un_refus_sort_en_1_pour_nommer_la_cause_ici(profils, tmp_path):
    """La §5b bloquerait de toute façon : échouer ici nomme le pourquoi."""
    import argparse

    _profil(profils / "homonyme.pivot.json", "Homonyme", "PA111")
    resolutions = tmp_path / "resolutions.json"
    resolutions.write_text(
        json.dumps({"resolutions": {"Homonyme": _resolution("Homonyme", "acteur", "PA999")}}),
        encoding="utf-8",
    )
    table = tmp_path / "table.json"
    table.write_text(
        json.dumps(
            {
                "schema_version": "correspondance-acteurs-an-v2",
                "genere_le": "2026-09-07T00:00:00+0000",
                "correspondances": {},
            }
        ),
        encoding="utf-8",
    )
    vider_memo()
    args = argparse.Namespace(
        completer_candidats=True,
        resolutions=resolutions,
        sortie=table,
        profiles_dir=profils,
        verifie_le="2026-09-07",
    )

    assert build.completer_candidats(args) == 1
    # Rien n'a été ajouté à la table.
    assert json.loads(table.read_text(encoding="utf-8"))["correspondances"] == {}
