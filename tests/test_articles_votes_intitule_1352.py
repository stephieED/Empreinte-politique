"""#1352 — l'intitulé d'un article voté, et le gabarit des lois de finances.

Les deux textes sont des extraits réels, copiés octet pour octet des pages
`dyn/opendata/<uid>.html` téléchargées le 26/10/2026 :

- `PRJLANR5L17B3210_extrait.html` (projet de loi de finances pour 2027) : de la
  première partie jusqu'à l'article 2, puis le titre « États législatifs
  annexés » et son premier état ;
- `PRJLANR5L17B3211_extrait.html` (projet de loi de financement de la sécurité
  sociale pour 2027) : de la deuxième partie jusqu'à l'article 4, puis les
  articles 10 et 11.

Avant ce lot, les 6 scrutins d'article du PLF 2027 étaient déclarés
`texte_a_gabarit_non_lu`, et les 6 du PLFSS 2027 `article_absent_du_texte`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import articles_votes as av

FIXTURES = Path(__file__).parent / "fixtures" / "articles_votes"
PLF = FIXTURES / "PRJLANR5L17B3210_extrait.html"
PLFSS = FIXTURES / "PRJLANR5L17B3211_extrait.html"
ORDINAIRE = FIXTURES / "PIONANR5L17BTC3190_extrait.html"


def _structure(chemin: Path) -> dict:
    return av.structure_du_texte(chemin.read_text(encoding="utf-8"))


@pytest.mark.parametrize("en_tete, attendu", [
    ("Article 4 Aide aux cotisants affectés", ("4", "Aide aux cotisants affectés")),
    ("Article 1 er Rectification des tableaux d’équilibre", ("1er", "Rectification des tableaux d’équilibre")),
    ("ARTICLE 2 : Soutenir le travail", ("2", "Soutenir le travail")),
    ("ARTICLE liminaire : : Prévisions de solde", ("liminaire", "Prévisions de solde")),
    # Un mot court d'intitulé n'est pas la lettre d'un article inséré.
    ("Article 6 Le régime social", ("6", "Le régime social")),
    ("Article 12 quater A Taxe", ("12 quater a", "Taxe")),
    # Ce que la lecture d'avant rendait déjà, inchangé.
    ("Article 4 bis A (nouveau)", ("4 bis a", None)),
    ("Article 3 (Supprimé)", ("3", None)),
    ("Articles 1er à 3", ("1er à 3", None)),
    ("Article premier", ("1er", None)),
    ("Article unique", ("unique", None)),
])
def test_en_tete_d_article(en_tete, attendu):
    assert av.en_tete_d_article(en_tete) == attendu


# ---------------------------------------------------------------------------
# Le PLFSS : l'intitulé dans le paragraphe du numéro
# ---------------------------------------------------------------------------

def test_plfss_l_article_se_retrouve_par_son_numero_avec_son_intitule():
    structure = _structure(PLFSS)
    fiche = structure["4"]
    assert fiche["intitule"].startswith("Aide aux cotisants affectés par les incendies et le cyclone Chido")
    assert fiche["partie"]["numero"] == "DEUXIÈME PARTIE :"
    assert fiche["partie"]["intitule"].startswith("Dispositions relatives aux recettes")
    assert fiche["titre"]["numero"] == "TITRE I er"
    assert fiche["texte"].startswith("I. – A. – Bénéficient")


def test_plfss_contre_epreuve_sans_separer_l_intitule(monkeypatch):
    """La lecture d'avant : l'en-tête entier devient la désignation, et
    l'article voté « 4 » n'est plus retrouvé."""
    monkeypatch.setattr(av, "en_tete_d_article", lambda texte: (av.normaliser_article(texte), None))
    assert "4" not in _structure(PLFSS)


def test_un_chapitre_cite_dans_un_article_n_est_pas_une_division():
    """L'article 10 insère dans le code un « « Chapitre V ter ». Lu comme une
    division, il était donné à l'article 11 ; il appartient au texte de l'article 10."""
    structure = _structure(PLFSS)
    assert structure["11"]["chapitre"] is None
    assert "Chapitre V ter" in structure["10"]["texte"]


# ---------------------------------------------------------------------------
# Le PLF : le gabarit des lois de finances
# ---------------------------------------------------------------------------

def test_plf_le_gabarit_des_lois_de_finances_se_lit():
    structure = _structure(PLF)
    assert set(structure) == {"1", "2"}, "un état annexé n'est pas un article"
    fiche = structure["2"]
    assert fiche["intitule"].startswith("Soutenir le travail en revalorisant le barème de l’impôt sur le revenu")
    assert fiche["partie"] == {"numero": "PREMIÈRE PARTIE",
                               "intitule": "CONDITIONS GÉNÉRALES DE L’ÉQUILIBRE FINANCIER"}
    assert fiche["titre"] == {"numero": "TITRE PREMIER", "intitule": "DISPOSITIONS RELATIVES AUX RESSOURCES"}
    assert fiche["chapitre"] == {"numero": "I", "intitule": "Impôts et ressources autorisées"}
    assert fiche["section"] == {"numero": "B", "intitule": "Mesures fiscales"}
    assert fiche["texte"].startswith("I. – Le code général des impôts est ainsi modifié")
    assert "Exposé des motifs" not in fiche["texte"]
    assert structure["1"]["section"]["intitule"] == "Autorisation de perception des impôts et produits"


def test_un_texte_sans_article_reste_un_gabarit_non_lu():
    assert av.structure_du_texte("<html><body><p class=\"assnatBodyText\">x</p></body></html>") == {}


def test_un_texte_ordinaire_ne_change_pas():
    fiche = _structure(ORDINAIRE)["5"]
    assert fiche["intitule"] is None and fiche["partie"] is None
    assert fiche["chapitre"] == {"numero": "Chapitre II",
                                 "intitule": "Dispositions relatives à l’organisation judiciaire"}


# ---------------------------------------------------------------------------
# La publication
# ---------------------------------------------------------------------------

class FauxTextes:
    def __init__(self, structures):
        self.structures = structures

    def structure(self, uid):
        return self.structures.get(uid)


def test_le_scrutin_publie_l_intitule_et_la_partie():
    seance, dossier, texte = "RUANR5L17S2027IDS99999", "DLR5L17N54629", "PRJLANR5L17B3210"
    index = av.IndexDossiers([{"uid": dossier, "actesLegislatifs": {"acteLegislatif": [{
        "codeActe": "AN1", "actesLegislatifs": {"acteLegislatif": [
            {"codeActe": "AN1-DEPOT", "dateActe": "2026-10-01T00:00:00.000+02:00", "texteAssocie": texte},
            {"codeActe": "AN1-DEBATS-SEANCE", "dateActe": "2026-10-20T00:00:00.000+02:00",
             "reunionRef": seance}]}}]}}])
    scrutin = {"scrutin_id": "an:17:8737", "date": "2026-10-20", "seance_ref": seance, "dossier_ref": dossier,
               "libelle": "l'article 2 du projet de loi de finances pour 2027 (première lecture)."}
    entree = av.rattacher(scrutin, index, {seance: [dossier]}, FauxTextes({texte: _structure(PLF)}))
    assert entree["article"] == "2"
    assert entree["intitule"].startswith("Soutenir le travail")
    assert entree["partie"]["numero"] == "PREMIÈRE PARTIE"
    assert entree["section"]["intitule"] == "Mesures fiscales"


# ---------------------------------------------------------------------------
# Les articles des textes lus (option A, arbitrée le 26/10/2026)
# ---------------------------------------------------------------------------

def test_tous_les_articles_d_un_texte_a_intitules_sont_publies():
    lus = {"PRJLANR5L17B3210": _structure(PLF), "PIONANR5L17BTC3190": _structure(ORDINAIRE)}
    publies = av.articles_des_textes(lus)
    assert set(publies) == {"PRJLANR5L17B3210"}, "un texte sans intitulé n'est pas repris"
    plf = publies["PRJLANR5L17B3210"]
    assert plf["source_url"] == av.URL_TEXTE_HTML.format(uid="PRJLANR5L17B3210")
    assert list(plf["articles"]) == ["1", "2"], "l'ordre du texte, la désignation normalisée"
    assert plf["articles"]["2"]["intitule"].startswith("Soutenir le travail")
    assert plf["articles"]["2"]["section"] == {"numero": "B", "intitule": "Mesures fiscales"}
    assert "texte" not in plf["articles"]["2"], "le texte de l'article reste propre aux scrutins"


def test_la_designation_d_un_amendement_se_joint_apres_normalisation():
    articles = av.articles_des_textes({"PRJLANR5L17B3210": _structure(PLF)})["PRJLANR5L17B3210"]["articles"]
    for designation in ("Article 2", "ARTICLE 2", "article 2"):
        assert av.normaliser_article(designation) in articles


def test_construire_publie_les_textes_lus():
    seance, dossier, texte = "RUANR5L17S2027IDS99999", "DLR5L17N54629", "PRJLANR5L17B3210"
    index = [{"uid": dossier, "actesLegislatifs": {"acteLegislatif": [{
        "codeActe": "AN1", "actesLegislatifs": {"acteLegislatif": [
            {"codeActe": "AN1-DEPOT", "dateActe": "2026-10-01T00:00:00.000+02:00", "texteAssocie": texte},
            {"codeActe": "AN1-DEBATS-SEANCE", "dateActe": "2026-10-20T00:00:00.000+02:00",
             "reunionRef": seance}]}}]}}]
    scrutin = {"scrutin_id": "an:17:8737", "date": "2026-10-20", "seance_ref": seance, "dossier_ref": dossier,
               "libelle": "l'article 2 du projet de loi de finances pour 2027 (première lecture)."}
    lecteur = av.LecteurDeTextes(reseau=False)
    lecteur._memo[texte] = _structure(PLF)
    resultat = av.construire([scrutin], index, lecteur, agenda={seance: [dossier]}, genere_le="2026-10-26")
    assert resultat["schema_version"] == "articles-votes-v3"
    assert set(resultat["textes"]) == {texte}
    assert resultat["scrutins"]["an:17:8737"]["intitule"].startswith("Soutenir le travail")
