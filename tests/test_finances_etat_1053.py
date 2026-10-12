"""La collecte des finances de l'État (`raw_data/finances_etat.json`, #1053).

Onze exercices, onze formats de fichier : chaque lecteur est éprouvé sur les
**premières lignes du vrai fichier**, copiées le 12/10/2026 sous
`tests/fixtures/finances_etat/` avec leur encodage et leurs fins de ligne
d'origine. Une fixture écrite à la main aurait décrit le format tel que le code
l'imagine — c'est le défaut que ces tests doivent attraper.

Deux fixtures font exception, et le disent : les séries mensuelles et le fichier
des textes sont réduits à deux lignes et réécrits en UTF-8 (l'original pèse
100 ko en UTF-16) ; leur emballage est éprouvé à part, sur `decoder()`.

Les classeurs `.xls` de 2019 et 2020 ne se tronquent pas sans outil d'écriture :
leur lecteur est éprouvé sur les lignes que `xlrd` rend du vrai classeur.
"""
from __future__ import annotations

import gzip
import json
import sys
from datetime import date
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import finances_etat as fe  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "finances_etat"


def texte(nom: str) -> str:
    return fe.decoder((FIXTURES / nom).read_bytes())


def programme(lignes: list[dict], code: str) -> dict:
    return next(l for l in lignes if l["programme"] == code)


# ── Décodage ────────────────────────────────────────────────────────────────

def test_une_piece_jointe_en_gzip_se_lit_sans_que_rien_ne_le_dise():
    """Mesuré le 12/10/2026 : `plf25-…/exports/json` arrive compressé, sans
    en-tête HTTP, une fois sur plusieurs."""
    assert fe.decoder(gzip.compress("Ministère;é".encode("utf-8"))) == "Ministère;é"


def test_une_piece_jointe_en_utf16_se_lit():
    """Deux des quatre fichiers du jeu mensuel sont en UTF-16 avec marque d'ordre."""
    assert fe.decoder("Catégorie;Dépenses".encode("utf-16")) == "Catégorie;Dépenses"


def test_un_fichier_en_cp1252_garde_ses_accents():
    assert fe.decoder("Libellé ministère".encode("cp1252")) == "Libellé ministère"


@pytest.mark.parametrize("ecrit,attendu", [
    ("1 961 961 115", 1961961115.0), ("742542019,3", 742542019.3),
    ("1\xa0339", 1339.0), (15101806.0, 15101806.0), ("0", 0.0),
])
def test_un_montant_se_lit_dans_les_trois_ecritures_de_la_source(ecrit, attendu):
    assert fe.nombre(ecrit) == attendu


@pytest.mark.parametrize("vide", ["", "   ", None])
def test_une_cellule_vide_n_est_pas_un_zero(vide):
    """§2 règle 5 : le zéro est un montant, l'absence n'en est pas un."""
    assert fe.nombre(vide) is None


@pytest.mark.parametrize("ecrit", ["MIN01", "01", "1", 1.0, "1.0"])
def test_les_quatre_ecritures_d_un_code_de_ministere_n_en_font_qu_une(ecrit):
    assert fe.code_nu(ecrit) == "1"


# ── Le voté ─────────────────────────────────────────────────────────────────

def test_vote_2016_saute_les_quatre_lignes_de_titre():
    lignes = fe.lire_vote_2016(texte("vote2016.csv"))

    assert programme(lignes, "105") == {
        "programme": "105", "ministere_code": "1",
        "ministere": "Affaires étrangères et développement international",
        "cp": 1961961115.0}


def test_vote_2018_ne_garde_que_le_budget_general():
    lignes = fe.lire_vote_2018(texte("vote2018.csv"))

    assert programme(lignes, "105")["cp"] == 1901700695.0
    assert programme(lignes, "105")["ministere"] == "Europe et affaires étrangères"
    assert programme(lignes, "105")["ministere_code"] == "1", "« MIN01 » dans la source"


def test_vote_2019_lit_l_export_json():
    lignes = fe.lire_vote_2019(texte("vote2019.json"))

    assert programme(lignes, "150") == {
        "programme": "150", "ministere_code": "38",
        "ministere": "Enseignement supérieur, recherche et innovation",
        "cp": 13593136803.0}


def test_vote_2020_prend_le_libelle_dans_la_nomenclature():
    """Le fichier de crédits 2020 ne porte que le code du ministère."""
    libelles = fe.lire_nomenclature_2020(texte("nomenclature_vote2020.csv"))
    lignes = fe.lire_vote_2020(texte("vote2020.csv"), libelles)

    assert len(libelles) == 17
    assert programme(lignes, "101")["ministere"] == "Justice"
    assert programme(lignes, "101")["cp"] == 521759215.0, "huit lignes d'action additionnées"


def test_vote_2022_lit_la_loi_votee_pas_le_projet():
    """Le fichier porte projet, amendements et loi votée côte à côte."""
    lignes = fe.lire_vote_2021(texte("vote2022.csv"))

    assert programme(lignes, "101")["cp"] == 667743516.0
    assert programme(lignes, "101")["ministere_code"] == "10"


# ── Le consommé ─────────────────────────────────────────────────────────────

def test_realise_2015_additionne_les_actions_d_un_programme():
    lignes = fe.lire_realise_2015(texte("exec2015.csv"))

    assert programme(lignes, "151")["cp"] == 202564985.0
    assert programme(lignes, "151")["ministere"] == (
        "Affaires étrangères et développement international")


def test_realise_2017_additionne_les_sept_titres():
    """2017 n'a pas de colonne de total : T1 à T7 se somment, les vides valent rien."""
    lignes = fe.lire_realise_2017(texte("exec2017.csv"))

    assert programme(lignes, "105")["cp"] == 1788947207.0
    assert programme(lignes, "105")["ministere_code"] == "1"


def test_realise_2018_ecarte_les_comptes_speciaux():
    lignes = fe.lire_realise_2018(texte("exec2018.json"))

    assert "753" not in {l["programme"] for l in lignes}, (
        "le 753 est un compte d'affectation spéciale, pas le budget général")
    assert programme(lignes, "422")["ministere"] == "Services du Premier ministre"


def test_realise_xls_lit_les_lignes_du_classeur(monkeypatch):
    """Lignes rendues par `xlrd` sur `PLR2019-Credits_Destination_Nature.xls`."""
    credits = [
        ["exercice", "loi", "typeBudget", "ministere", "mission", "programme", "action",
         "sous_action", "categorie", "titre", "AE EXEC", "CP EXEC"],
        ["2019", "PLR", "BG", "01", "AA", "105", "105-01", "", 22.0, "2", 15101806.0, 15101806.0],
        ["2019", "PLR", "BG", "01", "AA", "105", "105-01", "", "23", "2", 490979.0, 490979.0],
        ["2019", "PLR", "CCF", "21", "ZC", "832", "832-01", "", "71", "7", 1.0, 1.0],
    ]
    nomenclature = [
        ["Type ligne ", "Type Budget", "code", "Mission", "Ministere", "Libelle"],
        ["MIN", "", 1.0, "", "", "Europe et affaires étrangères"],
        ["PGM", "CCF", "832.0", "ZC", "21", "Avances aux collectivités"],
    ]
    monkeypatch.setattr(fe, "_feuille", lambda contenu: credits if contenu == b"c" else nomenclature)

    lignes = fe.lire_realise_xls(b"c", fe.lire_nomenclature_xls(b"n"))

    assert lignes == [{"programme": "105", "ministere_code": "1",
                       "ministere": "Europe et affaires étrangères", "cp": 15592785.0}]


# ── 2023-2025 : le ministère par le programme ───────────────────────────────

@pytest.mark.parametrize("fichier,code", [
    ("nomen2023.json", "1"), ("nomen2024.json", None), ("nomen2025.json", "1")])
def test_la_nomenclature_rend_le_ministere_de_chaque_programme(fichier, code):
    """Trois jeux, trois nommages de colonnes — et pas de code en 2024."""
    ministeres = fe.lire_nomenclature_json(texte(fichier))

    assert ministeres["105"] == (code, "Europe et affaires étrangères")


def test_l_etat_des_credits_rend_le_vote_et_le_consomme_de_la_meme_ligne():
    ministeres = fe.lire_nomenclature_json(texte("nomen2025.json"))
    vote, realise = fe.lire_etat_cp(texte("exec2025.csv"), ministeres)

    assert programme(vote, "105")["cp"] == 1339439190 + 1310499412
    assert programme(realise, "105")["cp"] == 2613879162.74, "virgule décimale dans la source"
    assert programme(realise, "105")["ministere"] == "Europe et affaires étrangères"


def test_un_programme_absent_de_la_nomenclature_garde_un_ministere_nul():
    """La fixture de nomenclature ne porte que les programmes 105 et 185.

    Dans le vrai fichier, c'est le cas du 367 en 2023 et 2024 : il n'est rangé
    sous aucun ministère d'emprunt.
    """
    ministeres = fe.lire_nomenclature_json(texte("nomen2025.json"))
    _vote, realise = fe.lire_etat_cp(texte("exec2025.csv"), ministeres)

    assert programme(realise, "354")["ministere"] is None
    assert programme(realise, "354")["ministere_code"] is None
    assert programme(realise, "354")["cp"] == 2642744725.6, "le montant, lui, est gardé"


def test_un_programme_sous_deux_ministeres_fait_echouer():
    """La jointure de 2023-2025 repose sur le fait que cela n'arrive pas."""
    deux = json.dumps([
        {"typebudget": "BG", "programme": "105", "ministere": "1", "libelle_ministere": "A"},
        {"typebudget": "BG", "programme": "105", "ministere": "9", "libelle_ministere": "B"}])

    with pytest.raises(fe.FinancesIndisponibles, match="deux ministères"):
        fe.lire_nomenclature_json(deux)


# ── Les grandes lignes ──────────────────────────────────────────────────────

def test_les_series_mensuelles_sont_cle_par_mois():
    lignes = fe.lire_series_mensuelles([texte("series_mensuelles_2024.csv")])
    impot = lignes[("Recettes", "Budget général", "Impôt sur le revenu")]

    assert impot["niveau"] == "3"
    assert impot["mensuel"]["2024-12"] == 87987247678.47
    assert list(impot["mensuel"])[0] == "2024-01"


def test_les_textes_gardent_la_colonne_execution_telle_que_la_source_la_donne():
    """Elle est décalée d'un an de 2019 à 2021 : 2019 y répète 2018. Le module
    ne la corrige pas — il la garde, et le réalisé se lit ailleurs."""
    textes = fe.lire_textes([texte("textes_2013_2023.csv")])
    depenses = textes[("Dépenses", "Budget général", "Total dépenses nettes du budget général")]

    assert depenses["LFI"]["2022"] == 391906772665.0
    assert depenses["Exécution"]["2019"] == depenses["Exécution"]["2018"]


# ── La collecte ─────────────────────────────────────────────────────────────

URL_VOTE = "https://exemple.invalid/vote2016.csv"
URL_REALISE = "https://exemple.invalid/exec2015.csv"


@pytest.fixture
def plan(monkeypatch):
    """Un plan à un exercice, servi par les fixtures ; le plancher est levé
    parce qu'une fixture porte dix lignes, pas un budget."""
    monkeypatch.setattr(fe, "PLANCHER_PROGRAMMES", 1)
    monkeypatch.setattr(fe, "LECTEURS", {
        2016: {"vote": {"fichier": URL_VOTE, "lire": "vote_2016"},
               "realise": {"fichier": URL_REALISE, "lire": "realise_2015"}},
        2021: {"vote": {"fichier": URL_VOTE, "lire": "vote_2016"},
               "realise": {"raison": "PDF seulement"}},
    })
    monkeypatch.setattr(fe, "lire_grandes_lignes", lambda appel: {"lignes": []})
    return {URL_VOTE: (FIXTURES / "vote2016.csv").read_bytes(),
            URL_REALISE: (FIXTURES / "exec2015.csv").read_bytes()}


def test_un_cote_sans_fichier_est_declare_jamais_tu(plan):
    document = fe.collecter({}, plan.__getitem__)
    bloc = document["exercices"]["2021"]

    assert bloc["realise"] is None
    assert bloc["realise_non_resolu"] == {"raison": "PDF seulement", "a_retenter": False}
    assert bloc["vote"]["programmes"], "l'autre côté n'est pas emporté"


def test_une_lecture_en_echec_n_ecrase_pas_ce_qui_etait_resolu(plan):
    premier = fe.collecter({}, plan.__getitem__)

    def panne(url: str) -> bytes:
        raise OSError("portail injoignable")

    second = fe.collecter(premier, panne, tout=True)

    assert second["exercices"]["2016"]["vote"] == premier["exercices"]["2016"]["vote"]
    assert "vote_non_resolu" not in second["exercices"]["2016"]
    assert any("2016 vote" in e for e in second["echecs"]), "l'échec est rendu, pas avalé"


def test_une_premiere_lecture_en_echec_se_declare_a_retenter(plan):
    def panne(url: str) -> bytes:
        raise OSError("portail injoignable")

    document = fe.collecter({}, panne)

    assert document["exercices"]["2016"]["vote"] is None
    assert document["exercices"]["2016"]["vote_non_resolu"]["a_retenter"] is True


def test_un_fichier_trop_court_n_est_pas_publie_comme_un_budget(plan, monkeypatch):
    """Une colonne renommée par la source rendrait trois lignes sans erreur."""
    monkeypatch.setattr(fe, "PLANCHER_PROGRAMMES", 100)

    document = fe.collecter({}, plan.__getitem__)

    assert document["exercices"]["2016"]["vote"] is None
    assert "moins que les 100" in document["exercices"]["2016"]["vote_non_resolu"]["raison"]


def test_un_exercice_clos_et_resolu_ne_se_relit_pas(plan):
    premier = fe.collecter({}, plan.__getitem__)
    appels: list[str] = []

    def compte(url: str) -> bytes:
        appels.append(url)
        return plan[url]

    fe.collecter(premier, compte, aujourd_hui=date(2026, 10, 12))

    assert appels == [], "2016 et 2021 sont figés : aucun fichier à relire"


@pytest.mark.parametrize("an,fige", [(2024, True), (2025, False), (2026, False)])
def test_l_exercice_de_l_an_dernier_se_relit_encore(an, fige):
    """La loi de règlement de N paraît au printemps N+1, et peut être republiée."""
    resolu = {"vote": {"programmes": []}, "realise": {"programmes": []}}

    assert fe.est_fige(resolu, an, date(2026, 10, 12)) is fige


def test_un_cote_a_retenter_empeche_de_figer():
    bloc = {"vote": {"programmes": []}, "realise": None,
            "realise_non_resolu": {"raison": "lecture en échec", "a_retenter": True}}

    assert fe.est_fige(bloc, 2019, date(2026, 10, 12)) is False


def test_chaque_exercice_du_plan_declare_ses_deux_cotes():
    """Garde-fou du plan : un exercice ajouté sans son côté consommé se lirait
    à moitié sans que rien ne le dise."""
    for an, cotes in fe.LECTEURS.items():
        assert an >= fe.BORNE_MINISTERE
        assert set(cotes) in ({"vote", "realise"}, {"etat"}), f"exercice {an}"
        for source in cotes.values():
            assert "raison" in source or source["fichier"].startswith("https://"), f"exercice {an}"
