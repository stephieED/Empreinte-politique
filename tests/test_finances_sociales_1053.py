"""La collecte des comptes des caisses sociales (`raw_data/finances_sociales.json`, #1053).

Chaque lecteur est éprouvé sur **le vrai fichier**, copié le 12/10/2026 sous
`tests/fixtures/finances_sociales/` :

- `classeur_2024.xlsx` — le classeur de la Drees, réduit aux deux feuilles lues
  (les XML d'origine, non réécrits : seules les dix autres feuilles manquent) ;
- `fiche_drees.json` — la liste des pièces jointes du jeu, telle que l'API la rend ;
- `regimes_1975_1989_2023.json` — trois années de l'export des prestations par
  régime, une par régime de la source : sans détail, détail incomplet, complet ;
- `unedic.json` — l'export entier de l'Unédic, quinze années.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import finances_sociales as fs  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "finances_sociales"
URL_CLASSEUR = json.loads((FIXTURES / "fiche_drees.json").read_text(encoding="utf-8"))["attachments"][1]["url"]

REPONSES = {
    fs.URL_JEU_DREES: "fiche_drees.json",
    URL_CLASSEUR: "classeur_2024.xlsx",
    fs.URL_REGIMES: "regimes_1975_1989_2023.json",
    fs.URL_UNEDIC: "unedic.json",
}


def appel(url: str) -> bytes:
    return (FIXTURES / REPONSES[url]).read_bytes()


@pytest.fixture(autouse=True)
def _plancher_des_trois_annees(monkeypatch):
    # La fixture porte trois années sur soixante-six.
    monkeypatch.setattr(fs, "PLANCHER_REGIMES", 50)


def ligne(bloc: dict, libelle: str) -> dict:
    return next(l for l in bloc["lignes"] if l["libelle"] == libelle)["valeurs"]


# ── Le classeur ─────────────────────────────────────────────────────────────

def test_le_classeur_est_retrouve_par_son_type_pas_par_son_nom():
    bloc = fs.lire_protection_sociale(appel)
    assert bloc["source_urls"] == [URL_CLASSEUR]
    assert bloc["classeur"] == "La protection sociale en France de 1959 à 2024.xlsx"
    assert set(bloc["champs"]) == {"ensemble_des_regimes", "administrations_de_securite_sociale"}


def test_les_ressources_de_2023_sont_celles_du_fichier():
    champs = fs.lire_protection_sociale(appel)["champs"]
    ensemble = champs["ensemble_des_regimes"]
    assert ensemble["feuille"] == "opérations_1959_2024"
    assert ligne(ensemble, "TOTAL DES RESSOURCES HORS TRANSFERTS")["2023"] == 960232.88
    assert ligne(ensemble, "Cotisations sociales d'employeurs")["2023"] == 281881.31
    assert ligne(ensemble, "Impôts et taxes affectés")["2023"] == 289348.15
    asso = champs["administrations_de_securite_sociale"]
    assert ligne(asso, "TOTAL DES RESSOURCES HORS TRANSFERTS")["2023"] == 722838.32
    assert sorted(asso["statuts"]) == ["2020", "2021", "2022", "2023", "2024"]


def test_le_statut_de_chaque_annee_est_garde():
    statuts = fs.lire_protection_sociale(appel)["champs"]["ensemble_des_regimes"]["statuts"]
    assert (statuts["2022"], statuts["2023"], statuts["2024"]) == ("DEF", "SD", "PROV")
    assert min(statuts) == "1959"


def test_une_cellule_vide_reste_absente_jamais_zero():
    """En 2024, provisoire, les trois cotisations tiennent sur une seule ligne."""
    ensemble = fs.lire_protection_sociale(appel)["champs"]["ensemble_des_regimes"]
    assert ligne(ensemble, "Cotisations sociales de salariés")["2024"] is None
    assert ligne(ensemble, "Autres cotisations sociales")["2024"] is None
    assert ligne(ensemble, "Cotisations sociales d'employeurs")["2024"] == 482239.04
    assert ligne(ensemble, "Impôts et taxes affectés")["1959"] is None


def test_les_lignes_de_note_ne_sont_pas_des_donnees():
    for bloc in fs.lire_protection_sociale(appel)["champs"].values():
        assert not [l for l in bloc["lignes"] if l["libelle"].startswith(("*", "Source"))]


def test_un_total_qui_ne_vaut_plus_ses_lignes_fait_echouer():
    feuilles = fs.lire_classeur(appel(URL_CLASSEUR))
    lignes = [dict(l) for l in feuilles["opérations_ASSO"]]
    del lignes[next(i for i, l in enumerate(lignes) if l.get("A") == "Impôts et taxes affectés")]
    with pytest.raises(fs.FinancesIndisponibles, match="total des ressources"):
        fs.lire_operations(lignes, "essai")


def test_un_classeur_rendu_en_gzip_se_lit():
    assert fs.lire_classeur(gzip.compress(appel(URL_CLASSEUR))).keys() == fs.lire_classeur(appel(URL_CLASSEUR)).keys()


def test_deux_classeurs_joints_font_echouer_plutot_que_choisir():
    fiche = json.loads(appel(fs.URL_JEU_DREES))
    fiche["attachments"].append(dict(fiche["attachments"][1], id="autre"))
    with pytest.raises(fs.FinancesIndisponibles, match="un seul attendu"):
        fs.lire_protection_sociale(lambda u: json.dumps(fiche).encode() if u == fs.URL_JEU_DREES else appel(u))


# ── Les prestations par régime ──────────────────────────────────────────────

def test_les_regimes_de_2023_et_leurs_trois_niveaux():
    annee = fs.lire_prestations_par_regime(appel)["annees"]["2023"]
    assert [r["montant"] for r in annee if r["niveau"] == 0] == [889478.93]
    cnav = next(r for r in annee if r["regime"] == "Caisse nationale d’assurance vieillesse")
    assert (cnav["niveau"], cnav["secteur_code"], cnav["montant"]) == (2, "S13141", 151825.8)
    assert sum(r["niveau"] == 1 for r in annee) == 9


def test_une_annee_sans_detail_ne_fait_pas_echouer():
    """Avant 1981 la source ne donne que l'ensemble ; de 1981 à 1989 ses
    régimes ne font pas son total. Les deux sont gardés tels quels."""
    annees = fs.lire_prestations_par_regime(appel)["annees"]
    assert [r["niveau"] for r in annees["1975"]] == [0]
    regimes = sum(r["montant"] for r in annees["1989"] if r["niveau"] == 2)
    ensemble = next(r["montant"] for r in annees["1989"] if r["niveau"] == 0)
    assert round(ensemble - regimes) == 1282


def test_une_reponse_courte_n_est_pas_le_jeu(monkeypatch):
    monkeypatch.setattr(fs, "PLANCHER_REGIMES", 1000)
    with pytest.raises(fs.FinancesIndisponibles, match="lignes lues"):
        fs.lire_prestations_par_regime(appel)


# ── L'assurance chômage ─────────────────────────────────────────────────────

def test_les_recettes_de_l_assurance_chomage():
    annees = fs.lire_assurance_chomage(appel)["annees"]
    assert (min(annees), max(annees)) == ("2011", "2025")
    assert annees["2023"]["recettes_total"] == 43997
    assert annees["2023"]["recettes_csg"] == 16757
    assert annees["2011"]["recettes_csg"] is None, "pas de CSG avant 2019 : absente, jamais zéro"


def test_un_total_de_recettes_incoherent_fait_echouer():
    rangs = json.loads(appel(fs.URL_UNEDIC))
    rangs[0]["recettes_total"] += 50
    with pytest.raises(fs.FinancesIndisponibles, match="recettes"):
        fs.lire_assurance_chomage(lambda u: json.dumps(rangs).encode())


# ── La collecte ─────────────────────────────────────────────────────────────

def test_la_collecte_porte_ses_trois_parties_et_sa_licence():
    document = fs.collecter({}, appel)
    assert document["echecs"] == []
    assert document["schema_version"] == "finances-sociales-v1"
    assert document["unite"] == "millions d'euros"
    assert "Licence Ouverte" in document["licence_donnees"]
    assert all(document[p] for p in fs.PARTIES)


def test_une_partie_en_echec_garde_celle_deja_publiee():
    publie = fs.collecter({}, appel)

    def panne(url: str) -> bytes:
        if url == fs.URL_UNEDIC:
            raise OSError("portail injoignable")
        return appel(url)

    document = fs.collecter(publie, panne)
    assert document["assurance_chomage"] == publie["assurance_chomage"]
    assert "assurance_chomage_non_resolu" not in document
    assert document["echecs"] == ["assurance_chomage : portail injoignable"]


def test_une_partie_jamais_lue_est_nulle_et_dit_pourquoi():
    def panne(url: str) -> bytes:
        if url == fs.URL_REGIMES:
            return b"<html>erreur</html>"
        return appel(url)

    document = fs.collecter({}, panne)
    assert document["prestations_par_regime"] is None
    assert document["prestations_par_regime_non_resolu"]["a_retenter"] is True
    assert document["protection_sociale"] and document["assurance_chomage"]


def test_main_ecrit_le_fichier_et_rend_zero(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(fs, "_appel_reseau", appel)
    sortie = tmp_path / "finances_sociales.json"
    assert fs.main(["--sortie", str(sortie)]) == 0
    ecrit = json.loads(sortie.read_text(encoding="utf-8"))
    assert "echecs" not in ecrit and set(fs.PARTIES) <= set(ecrit)
    assert "assurance_chomage : de 2011 à 2025" in capsys.readouterr().out
