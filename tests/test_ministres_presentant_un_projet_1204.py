"""#1204 — le ministre qui présente un projet de loi complète `initiateurs`.

Un projet de loi est déposé au nom du Premier ministre et présenté par un
ministre. Le dossier législatif de l'Assemblée ne nomme ce ministre qu'une fois
sur deux ; le DOCUMENT de dépôt le porte, comme cosignataire. Mesuré le
04/10/2026 sur les 1 298 projets des fiches de gouvernement : 646 ne portaient
qu'un nom ou aucun, 26 après lecture du document de dépôt.

Les deux fixtures sont copiées de l'archive des dossiers de la XVIe : le dossier
`DLR5L16N46008` (déposé au Sénat le 20/07/2022, initiateur Élisabeth Borne) et
son document de dépôt `PRJLSNR5S379B0807`, cosigné par Marc Fesneau. Les lignes
de `membres[]` sont celles de `gouvernement-BORNE.json`.
"""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import gouvernement_profile as gp  # noqa: E402
import gouvernement_textes as gt  # noqa: E402
from schema_gouvernement import KNOWN_RELEVES_INITIATEUR, _erreurs_initiateurs  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "dossier_gouvernemental_1204"
DOSSIER = json.loads((FIXTURES / "DLR5L16N46008.json").read_text(encoding="utf-8"))[
    "dossierParlementaire"]
DOCUMENT = json.loads((FIXTURES / "PRJLSNR5S379B0807.json").read_text(encoding="utf-8"))[
    "document"]

BORNE, FESNEAU = "PA717161", "PA719938"
INDEX = {BORNE: "elisabeth-borne", FESNEAU: "marc-fesneau"}
MEMBRES = [
    {"membre_id": "elisabeth-borne", "portefeuille": "Première ministre",
     "debut": "2022-05-17", "fin": "2024-01-09"},
    {"membre_id": "marc-fesneau",
     "portefeuille": "Ministère de l’agriculture et de la souveraineté alimentaire",
     "debut": "2022-05-21", "fin": "2024-01-09"},
]


def test_le_dossier_ne_nomme_que_la_premiere_ministre():
    """Le constat de départ, sur la source elle-même."""
    assert gt._initiateurs_acteur_refs(DOSSIER) == [BORNE]


def test_le_document_de_depot_porte_le_ministre_qui_presente():
    assert gt._document_depot_initial(DOSSIER["actesLegislatifs"]) == DOCUMENT["uid"]
    assert gt._cosignataires_acteur_refs(DOCUMENT) == [FESNEAU]


def test_un_document_sans_cosignataire_rend_none_jamais_une_liste_vide():
    assert gt._cosignataires_acteur_refs({**DOCUMENT, "coSignataires": None}) is None
    assert gt._cosignataires_acteur_refs({**DOCUMENT, "coSignataires": {"coSignataire": []}}) is None


def test_l_enregistrement_porte_les_presentateurs_quand_la_table_est_fournie():
    table = {DOCUMENT["uid"]: [FESNEAU]}
    record = gt.parse_dossier_gouvernemental(DOSSIER, table)
    assert record["document_depot"] == DOCUMENT["uid"]
    assert record["presentateurs_acteur_refs"] == [FESNEAU]
    assert record["initiateurs_acteur_refs"] == [BORNE]
    # Sans table — ou sans le document dans la table —, la source ne dit rien.
    assert gt.parse_dossier_gouvernemental(DOSSIER)["presentateurs_acteur_refs"] is None
    assert gt.parse_dossier_gouvernemental(DOSSIER, {})["presentateurs_acteur_refs"] is None


def test_la_collecte_sur_archive_lit_le_document_de_depot(tmp_path):
    archive = tmp_path / "dossiers_16.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.write(FIXTURES / "DLR5L16N46008.json", "json/dossierParlementaire/DLR5L16N46008.json")
        zf.write(FIXTURES / "PRJLSNR5S379B0807.json", "json/document/PRJLSNR5S379B0807.json")
    (record,) = gt.collect_dossiers_gouvernementaux_multi([(16, archive)])["dossiers"]
    assert record["presentateurs_acteur_refs"] == [FESNEAU]


def test_la_fiche_publie_le_ministre_son_portefeuille_et_ou_il_a_ete_lu():
    initiateurs = gp._initiateurs_texte([BORNE], INDEX, [FESNEAU], "2022-07-20", MEMBRES)
    assert initiateurs == [
        {"acteur_ref": BORNE, "membre_id": "elisabeth-borne",
         "portefeuille": "Première ministre", "releve_dans": "dossier"},
        {"acteur_ref": FESNEAU, "membre_id": "marc-fesneau",
         "portefeuille": "Ministère de l’agriculture et de la souveraineté alimentaire",
         "releve_dans": "document_depot"},
    ]
    assert _erreurs_initiateurs(0, initiateurs, {"elisabeth-borne", "marc-fesneau"}) == []


def test_un_ministre_deja_nomme_par_le_dossier_n_est_pas_repete():
    initiateurs = gp._initiateurs_texte([BORNE, FESNEAU], INDEX, [FESNEAU], "2022-07-20", MEMBRES)
    assert [i["acteur_ref"] for i in initiateurs] == [BORNE, FESNEAU]
    assert {i["releve_dans"] for i in initiateurs} == {"dossier"}


def test_le_portefeuille_est_celui_du_jour_du_depot():
    """Une ligne de `membres[]` par période : après un remaniement, la même
    personne en a plusieurs, et deux périodes peuvent se toucher le même jour."""
    membres = [
        {"membre_id": "x", "portefeuille": "Ministère A", "debut": "2022-05-20", "fin": "2023-07-20"},
        {"membre_id": "x", "portefeuille": "Ministère B", "debut": "2023-07-20", "fin": "2024-01-09"},
    ]
    assert gp._portefeuille_a_la_date("x", "2022-12-01", membres) == "Ministère A"
    assert gp._portefeuille_a_la_date("x", "2023-07-20", membres) == "Ministère B"
    assert gp._portefeuille_a_la_date("x", "2023-12-01", membres) == "Ministère B"
    # Hors de toute période, hors de membres[], sans date : rien n'est déduit.
    assert gp._portefeuille_a_la_date("x", "2021-01-01", membres) is None
    assert gp._portefeuille_a_la_date("y", "2022-12-01", membres) is None
    assert gp._portefeuille_a_la_date(None, "2022-12-01", membres) is None
    assert gp._portefeuille_a_la_date("x", None, membres) is None


def test_sans_initiateur_ni_presentateur_la_liste_reste_null():
    assert gp._initiateurs_texte(None, INDEX, None, "2022-07-20", MEMBRES) is None


def test_la_validation_refuse_une_origine_inconnue_et_un_portefeuille_sans_membre():
    assert KNOWN_RELEVES_INITIATEUR == {"dossier", "document_depot"}
    mauvais = [{"acteur_ref": BORNE, "membre_id": None,
                "portefeuille": "Première ministre", "releve_dans": "ailleurs"}]
    erreurs = _erreurs_initiateurs(0, mauvais, set())
    assert any("releve_dans" in e for e in erreurs)
    assert any("portefeuille" in e for e in erreurs)


def test_une_fiche_d_avant_ce_lot_reste_valide():
    """Les deux clés ne sont pas obligatoires : une fiche qu'un run n'a pas pu
    réécrire (#427) ne les porte pas, et leur absence n'est pas une faute."""
    ancien = [{"acteur_ref": BORNE, "membre_id": "elisabeth-borne"}]
    assert _erreurs_initiateurs(0, ancien, {"elisabeth-borne"}) == []
