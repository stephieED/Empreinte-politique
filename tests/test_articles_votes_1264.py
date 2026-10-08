"""#1264 — sur quoi porte un article soumis au vote.

Le texte est un extrait réel de `PIONANR5L17BTC3190` (texte de commission de la
PPL « réponse intégrale… », lu le 08/10/2026) ; les actes de dossier reprennent
la forme de `DLR5L17N54776` dans l'archive XVIIe du 08/10/2026.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import articles_votes as av

FIXTURE = Path(__file__).parent / "fixtures" / "articles_votes" / "PIONANR5L17BTC3190_extrait.html"
SEANCE = "RUANR5L17S2027IDS30920"
DOSSIER = "DLR5L17N54776"
DOSSIER_ORGANIQUE = "DLR5L17N54777"


@pytest.mark.parametrize("brut, attendu", [
    ("Article 1 er", "1er"), ("premier", "1er"), ("Article 4 bis", "4 bis"),
    ("4 (nouveau)", "4"), ("Article 12 bis A (nouveau)", "12 bis a"), ("unique", "unique"),
])
def test_normaliser_article(brut, attendu):
    assert av.normaliser_article(brut) == attendu


def test_article_du_libelle():
    libelle = ("l'article 5 (examen prioritaire) de la proposition de loi apportant une réponse "
               "intégrale au phénomène des violences sexuelles et sexistes contre les femmes et les "
               "enfants (première lecture).")
    assert av.article_du_libelle(libelle) == "5"
    assert av.article_du_libelle("l'article premier du projet de loi de finances pour 2025") == "1er"
    assert av.article_du_libelle("l'ensemble de la proposition de loi") is None


def test_une_plage_regroupee_se_deplie():
    assert av._deplier("1er à 3") == ["1er", "2", "3"]
    assert av._deplier("4 bis à 4 quater") == ["4 bis à 4 quater"]


def test_structure_du_texte_reel():
    structure = av.structure_du_texte(FIXTURE.read_text(encoding="utf-8"))
    fiche = structure["5"]
    assert fiche["titre"]["numero"] == "Titre II"
    assert fiche["titre"]["intitule"].startswith("Dispositions relatives À la police judiciaire")
    assert fiche["chapitre"] == {"numero": "Chapitre II",
                                 "intitule": "Dispositions relatives à l’organisation judiciaire"}
    assert fiche["texte"].startswith("I. – Le code de l’organisation judiciaire est ainsi modifié")
    # Un nouveau chapitre remplace le précédent, le titre reste.
    assert structure["3"]["chapitre"]["intitule"] == "Dispositions relatives à la police judiciaire"
    assert structure["3"]["titre"]["numero"] == "Titre II"


class FauxTextes:
    def __init__(self, structures):
        self.structures = structures

    def structure(self, uid):
        return self.structures.get(uid)


def _dossier(uid, texte_commission, seance=SEANCE):
    return {"uid": uid, "actesLegislatifs": {"acteLegislatif": [{
        "codeActe": "AN1", "actesLegislatifs": {"acteLegislatif": [
            {"codeActe": "AN1-DEPOT", "dateActe": "2026-08-11T00:00:00.000+02:00",
             "texteAssocie": texte_commission.replace("BTC", "B")},
            {"codeActe": "AN1-COM", "actesLegislatifs": {"acteLegislatif": [
                {"codeActe": "AN1-COM-FOND", "actesLegislatifs": {"acteLegislatif": [
                    {"codeActe": "AN1-COM-FOND-RAPPORT", "dateActe": "2026-09-23T00:00:00.000+02:00",
                     "texteAdopte": texte_commission}]}}]}},
            {"codeActe": "AN1-DEBATS", "actesLegislatifs": {"acteLegislatif": [
                {"codeActe": "AN1-DEBATS-SEANCE", "dateActe": "2026-10-05T00:00:00.000+02:00",
                 "reunionRef": seance}]}},
        ]}}]}}


SCRUTIN = {"scrutin_id": "an:17:8441", "date": "2026-10-05", "seance_ref": SEANCE, "dossier_ref": None,
           "libelle": "l'article 5 (examen prioritaire) de la proposition de loi apportant une réponse "
                      "intégrale au phénomène des violences sexuelles et sexistes (première lecture)."}


def _structures():
    return {"PIONANR5L17BTC3190": av.structure_du_texte(FIXTURE.read_text(encoding="utf-8")),
            "PIONANR5L17B3106": {"1er": {"texte": "x"}},
            "PIONANR5L17BTC3191": {"1er": {"texte": "x"}, "2": {"texte": "x"}},
            "PIONANR5L17B3191": {"1er": {"texte": "x"}}}


def test_seance_a_un_dossier_rattache_le_texte_de_commission():
    index = av.IndexDossiers([_dossier(DOSSIER, "PIONANR5L17BTC3190")])
    entree = av.rattacher(SCRUTIN, index, {SEANCE: [DOSSIER]}, FauxTextes(_structures()))
    assert entree["texte_id"] == "PIONANR5L17BTC3190"
    assert entree["rattachement"] == av.RATTACHEMENT_SEANCE
    assert entree["chapitre"]["numero"] == "Chapitre II"
    assert entree["extrait"] and entree["source_url"].endswith("PIONANR5L17BTC3190.html")


def test_un_dossier_de_l_ordre_du_jour_sans_acte_empeche_le_rattachement():
    """L'acte de séance du second dossier manque : il reste candidat par l'ordre du jour."""
    index = av.IndexDossiers([_dossier(DOSSIER, "PIONANR5L17BTC3190")])
    entree = av.rattacher(SCRUTIN, index, {SEANCE: [DOSSIER, DOSSIER_ORGANIQUE]}, FauxTextes(_structures()))
    assert entree["motif"] == av.MOTIF_PLUSIEURS_DOSSIERS


def test_le_seul_texte_portant_l_article_l_emporte():
    """La loi et sa loi organique dans la même séance : seule la loi a un article 5."""
    index = av.IndexDossiers([_dossier(DOSSIER, "PIONANR5L17BTC3190"),
                              _dossier(DOSSIER_ORGANIQUE, "PIONANR5L17BTC3191")])
    entree = av.rattacher(SCRUTIN, index, {SEANCE: [DOSSIER, DOSSIER_ORGANIQUE]}, FauxTextes(_structures()))
    assert entree["dossier_id"] == DOSSIER
    assert entree["rattachement"] == av.RATTACHEMENT_ARTICLE


def test_l_elimination_exige_que_toutes_les_versions_du_concurrent_aient_ete_lues():
    structures = _structures()
    structures["PIONANR5L17B3191"] = None  # texte déposé du concurrent jamais lu
    index = av.IndexDossiers([_dossier(DOSSIER, "PIONANR5L17BTC3190"),
                              _dossier(DOSSIER_ORGANIQUE, "PIONANR5L17BTC3191")])
    entree = av.rattacher(SCRUTIN, index, {SEANCE: [DOSSIER, DOSSIER_ORGANIQUE]}, FauxTextes(structures))
    assert entree["motif"] == av.MOTIF_PLUSIEURS_DOSSIERS


def test_le_dossier_porte_par_le_scrutin_departage():
    index = av.IndexDossiers([_dossier(DOSSIER, "PIONANR5L17BTC3190"),
                              _dossier(DOSSIER_ORGANIQUE, "PIONANR5L17BTC3191")])
    scrutin = dict(SCRUTIN, dossier_ref=DOSSIER)
    entree = av.rattacher(scrutin, index, {SEANCE: [DOSSIER, DOSSIER_ORGANIQUE]}, FauxTextes(_structures()))
    assert entree["rattachement"] == av.RATTACHEMENT_DOSSIER


def test_un_gabarit_non_lu_et_un_article_absent_se_declarent():
    index = av.IndexDossiers([_dossier(DOSSIER, "PIONANR5L17BTC3190")])
    structures = _structures()
    structures["PIONANR5L17BTC3190"] = {}
    assert av.rattacher(SCRUTIN, index, {SEANCE: [DOSSIER]}, FauxTextes(structures))["motif"] \
        == av.MOTIF_GABARIT_NON_LU
    absent = dict(SCRUTIN, libelle="l'article 99 de la proposition de loi apportant…")
    assert av.rattacher(absent, index, {SEANCE: [DOSSIER]}, FauxTextes(_structures()))["motif"] \
        == av.MOTIF_ARTICLE_ABSENT


def test_chaque_motif_publie_est_au_vocabulaire():
    resultat = av.construire([SCRUTIN, dict(SCRUTIN, scrutin_id="an:17:1", seance_ref="inconnue")],
                             [_dossier(DOSSIER, "PIONANR5L17BTC3190")], FauxTextes(_structures()),
                             agenda={SEANCE: [DOSSIER]}, genere_le="2026-10-08")
    assert set(resultat["scrutins"]) == {"an:17:8441"}
    assert {e["motif"] for e in resultat["non_rattaches"].values()} <= av.MOTIFS
