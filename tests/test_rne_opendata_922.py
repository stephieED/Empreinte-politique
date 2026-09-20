"""#922 — les mandats locaux, lus au Répertoire national des élus.

Les fiches ne portaient aucun mandat local. Ce module en collecte deux jeux,
tous deux sous Licence Ouverte 2.0 : le RNE pour les mandats **en cours**, les
sortants 2020-2026 pour la mandature précédente.

Aucun test n'ouvre le réseau : la fonction d'appel est injectée, et les réponses
sont les formes réelles mesurées les 14 et 15/09/2026 sur
`tabular-api.data.gouv.fr`.
"""

import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from rne_opendata import (  # noqa: E402
    BORNE_COUVERTURE,
    COL_DEBUT_FONCTION,
    COL_DEBUT_MANDAT,
    COL_FONCTION,
    COL_NAISSANCE,
    COL_NOM,
    COL_PRENOM,
    FICHIERS_LOCAUX,
    FICHIERS_REFUSES,
    RneIndisponible,
    aplatir,
    cle_de_mandat,
    concerne,
    lieu_de,
    mandats_locaux,
    normaliser,
    resoudre_ressources,
)
from schema_pivot import KNOWN_CATEGORIE_SOURCES, KNOWN_CATEGORIES  # noqa: E402


def _ligne(**extra):
    base = {
        COL_NOM: "LISNARD", COL_PRENOM: "David", COL_NAISSANCE: "1969-02-02",
        "Libellé de la commune": "Cannes",
        COL_DEBUT_MANDAT: "2026-03-15", COL_FONCTION: None,
    }
    base.update(extra)
    return base


def _faux_appel(catalogue: dict, lignes: dict):
    """Rend le catalogue pour une URL de dataset, les lignes pour l'API tabulaire."""
    def appel(url: str):
        if "/api/1/datasets/" in url:
            for slug, contenu in catalogue.items():
                if slug in url:
                    return contenu
            return {}
        for rid, contenu in lignes.items():
            if f"/resources/{rid}/" in url:
                return {"data": contenu}
        return {"data": []}
    return appel


# --------------------------------------------------------------------------
# Les diacritiques — l'échec le plus silencieux de la source
# --------------------------------------------------------------------------

def test_aplatir_neutralise_les_accents_et_la_casse():
    """« Edouard » sans accent et « Jérôme » avec, dans le même fichier."""
    assert aplatir("Édouard") == aplatir("Edouard") == "EDOUARD"
    assert aplatir("Jérôme") == aplatir("Jerome")


def test_une_ligne_accentuee_autrement_est_reconnue():
    """Mesuré le 14/09/2026 : apparier sur le prénom tel qu'écrit rendait
    Édouard Philippe SANS AUCUN MANDAT, alors qu'il est maire du Havre."""
    ligne = _ligne(**{COL_NOM: "PHILIPPE", COL_PRENOM: "Edouard"})

    assert concerne(ligne, "PHILIPPE", "Édouard")


def test_un_homonyme_de_prenom_different_est_ecarte():
    """Quatre personnes nées le 28/11/1970, une seule s'appelle Philippe : le
    filtrage serveur par date ne suffit jamais seul."""
    ligne = _ligne(**{COL_NOM: "PHILIPPE", COL_PRENOM: "Patricia"})

    assert not concerne(ligne, "PHILIPPE", "Édouard")


# --------------------------------------------------------------------------
# Le lieu, et ce qu'on refuse de lire
# --------------------------------------------------------------------------

def test_le_lieu_prend_la_maille_la_plus_fine_disponible():
    """Un fichier départemental ne porte pas de commune, un régional ni l'un ni
    l'autre : supposer laquelle est renseignée rendrait `?` sur deux fichiers."""
    assert lieu_de(_ligne()) == "Cannes"
    assert lieu_de({"Libellé du département": "Alpes-Maritimes"}) == "Alpes-Maritimes"
    assert lieu_de({"Libellé de la région": "Hauts-De-France"}) == "Hauts-De-France"
    assert lieu_de({}) is None


def test_les_mandats_deja_collectes_ailleurs_sont_refuses_a_l_entree():
    """Députés, sénateurs et représentants au PE ont leur propre collecte, avec
    leur propre datation. Les lire publierait le même mandat deux fois, sans
    que rien ne dise laquelle des deux dates fait foi."""
    assert set(FICHIERS_REFUSES) == {
        "elus-deputes-dep", "elus-senateurs-sen",
        "elus-representants-Parlement-européen-rpe"}
    assert not (set(FICHIERS_REFUSES) & set(FICHIERS_LOCAUX))


def test_les_neuf_fichiers_locaux_sont_lus():
    """S'arrêter aux conseillers municipaux et aux maires aurait conclu « aucun
    mandat » pour Marine Tondelier, que seul le fichier RÉGIONAL porte."""
    assert len(FICHIERS_LOCAUX) == 9
    assert "elus-conseillers-regionaux-cr" in FICHIERS_LOCAUX


# --------------------------------------------------------------------------
# La date de fin, qui n'existe dans aucun des deux jeux
# --------------------------------------------------------------------------

def test_la_fin_est_nulle_et_porte_toujours_sa_cause():
    """Aucun jeu ne publie de date de fin : ils portent des DÉBUTS datés et des
    états constatés à une date. « Maire du Havre depuis le 28/06/2020, constaté
    le 27/02/2026 » est sourçable ; « jusqu'en mars 2026 » serait une inférence
    (§2 règle 5). Patron de `sort_non_resolu` (#747)."""
    mandat = normaliser(_ligne(), "mairie", False, "2026-02-27", "https://x")

    assert mandat["fin"] is None
    assert mandat["fin_non_resolue"] == {
        "motif": "source_sans_date_de_fin", "constate_le": "2026-02-27"}


def test_actif_dit_quel_jeu_a_rendu_la_ligne_jamais_une_deduction():
    """Le RNE ne publie que des mandats en cours, les sortants que des mandats
    clos : `actif` recopie ce fait, il ne le calcule pas."""
    assert normaliser(_ligne(), "mairie", True, None, "https://x")["actif"] is True
    assert normaliser(_ligne(), "mairie", False, None, "https://x")["actif"] is False


def test_la_date_de_fonction_est_distincte_de_celle_du_mandat():
    """Un maire est d'abord élu conseiller, puis désigné maire quelques jours
    plus tard — Lisnard : mandat au 2020-05-18, fonction au 2020-05-23."""
    mandat = normaliser(
        _ligne(**{COL_FONCTION: "Maire", COL_DEBUT_MANDAT: "2020-05-18",
                  COL_DEBUT_FONCTION: "2020-05-23"}),
        "conseil_municipal", False, "2026-02-27", "https://x")

    assert mandat["debut"] == "2020-05-18"
    assert mandat["debut_fonction"] == "2020-05-23"


def test_une_fonction_a_la_meme_date_ne_dedouble_pas_le_champ():
    mandat = normaliser(
        _ligne(**{COL_FONCTION: "Maire", COL_DEBUT_MANDAT: "2026-03-15",
                  COL_DEBUT_FONCTION: "2026-03-15"}),
        "conseil_municipal", True, None, "https://x")

    assert "debut_fonction" not in mandat


# --------------------------------------------------------------------------
# Le schéma
# --------------------------------------------------------------------------

def test_le_mandat_local_ne_se_confond_pas_avec_un_mandat_electif():
    """`appliquer_chambres` dérive `chambres[]` des `mandat_electif` et compte
    ceux SANS chambre comme un défaut de collecte (#492). Y verser un
    conseiller régional ferait sonner cette garde à tort."""
    mandat = normaliser(_ligne(), "conseil_regional", True, None, "https://x")

    assert mandat["categorie"] == "mandat_local"
    assert mandat["categorie"] in KNOWN_CATEGORIES
    assert mandat["categorie"] != "mandat_electif"
    assert "chambre" not in mandat


def test_la_source_est_estampillee():
    mandat = normaliser(_ligne(), "mairie", True, None, "https://x")

    assert mandat["categorie_source"] == "rne"
    assert mandat["categorie_source"] in KNOWN_CATEGORIE_SOURCES


# --------------------------------------------------------------------------
# La déduplication entre deux fichiers
# --------------------------------------------------------------------------

def test_un_maire_publie_dans_deux_fichiers_ne_compte_qu_une_fois():
    """Un maire figure chez les conseillers municipaux avec la fonction
    « Maire », ET chez les maires. C'est le même mandat."""
    cm = _ligne(**{COL_FONCTION: "Maire"})
    mai = _ligne()

    assert cle_de_mandat(cm) == cle_de_mandat(mai)


def test_deux_mandats_de_dates_differentes_restent_deux():
    """Lisnard est maire de Cannes depuis 2014, réélu en 2020 puis 2026 : trois
    mandats, pas un."""
    assert cle_de_mandat(_ligne()) != cle_de_mandat(
        _ligne(**{COL_DEBUT_MANDAT: "2020-05-18"}))


# --------------------------------------------------------------------------
# De bout en bout, sans réseau
# --------------------------------------------------------------------------

def test_la_collecte_dedoublonne_et_trie(monkeypatch):
    catalogue = {
        "repertoire-national-des-elus-1": {"resources": [
            {"title": "elus-conseillers-municipaux-cm.csv", "id": "RID_CM"},
            {"title": "elus-maires-mai.csv", "id": "RID_MAI"},
            {"title": "elus-deputes-dep.csv", "id": "RID_DEP"},
        ]},
        "elections-municipales-2026-maires": {"resources": [
            {"title": "mun2026-cm-sortants-20260227.csv", "id": "RID_SORT"},
        ]},
    }
    lignes = {
        "RID_CM": [_ligne(**{COL_FONCTION: "Maire"})],
        "RID_MAI": [_ligne()],
        "RID_DEP": [_ligne(**{COL_DEBUT_MANDAT: "1900-01-01"})],
        "RID_SORT": [_ligne(**{COL_DEBUT_MANDAT: "2020-05-18"})],
    }

    mandats = mandats_locaux(
        _faux_appel(catalogue, lignes), "LISNARD", "David", "1969-02-02",
        constate_le="2026-02-27")

    assert [m["debut"] for m in mandats] == ["2020-05-18", "2026-03-15"]
    assert all(m["debut"] != "1900-01-01" for m in mandats), (
        "le fichier des députés est refusé à l'entrée")


def test_le_mandat_en_cours_n_est_jamais_retrograde(monkeypatch):
    """Le RNE est interrogé avant les sortants : si les deux portent la même
    clé, c'est celui en cours qui gagne."""
    catalogue = {
        "repertoire-national-des-elus-1": {"resources": [
            {"title": "elus-maires-mai.csv", "id": "RID_MAI"}]},
        "elections-municipales-2026-maires": {"resources": [
            {"title": "mun2026-maires-sortants.csv", "id": "RID_SORT"}]},
    }
    lignes = {"RID_MAI": [_ligne()], "RID_SORT": [_ligne()]}

    mandats = mandats_locaux(
        _faux_appel(catalogue, lignes), "LISNARD", "David", "1969-02-02")

    assert len(mandats) == 1
    assert mandats[0]["actif"] is True


def test_un_catalogue_muet_leve_au_lieu_de_rendre_une_liste_vide():
    """Une liste vide se publierait comme « cette personne n'a aucun mandat
    local » — un constat sur la personne, pas sur la panne (§2 règle 5)."""
    with pytest.raises(RneIndisponible):
        resoudre_ressources(lambda url: {"resources": []}, "un-slug")


def test_le_rid_est_resolu_jamais_code_en_dur():
    """Il change à chaque publication trimestrielle : l'URL porte sa date."""
    resolues = resoudre_ressources(
        lambda url: {"resources": [{"title": "elus-maires-mai.csv", "id": "ABC"}]},
        "repertoire-national-des-elus-1")

    assert resolues == {"elus-maires-mai": "ABC"}


def test_la_borne_de_couverture_est_declaree():
    assert BORNE_COUVERTURE == "2020"
