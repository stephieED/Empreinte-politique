"""#922 — l'écriture du bloc `mandats_locaux` dans les profils bruts.

Miroir de `collecte_senat.py`. Ce que ces tests verrouillent avant tout, c'est
que **le bloc parle même quand il est vide** : une liste vide ne dit pas
pourquoi elle l'est, et les raisons ne se valent pas.

`aucun_mandat_trouve` est un **constat** — relu, la source n'en porte aucun.
`non_relu` est un **aveu** — personne n'a encore regardé. Publier l'un pour
l'autre ferait dire à une fiche « cette personne n'a pas de mandat local » alors
que nous ne le savons pas (§2 règle 5).

Aucun test n'ouvre le réseau : la fonction d'appel est injectée.
"""

import json
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from collecte_mandats_locaux import (  # noqa: E402
    CLE_BLOC,
    KNOWN_APPARIEMENTS,
    cle_appariement,
    collecter,
    composer_bloc,
    etat_civil,
)
from rne_opendata import COL_DEBUT_MANDAT, COL_NAISSANCE, COL_NOM, COL_PRENOM  # noqa: E402


def _appel_vide(url):
    if "/api/1/datasets/" in url:
        return {"resources": [{"title": "elus-maires-mai.csv", "id": "RID"}]}
    return {"data": []}


def _appel_avec(lignes):
    def appel(url):
        if "/api/1/datasets/" in url:
            return {"resources": [{"title": "elus-maires-mai.csv", "id": "RID"}]}
        return {"data": lignes}
    return appel


@pytest.fixture
def corpus(tmp_path):
    """Un corpus minimal : un pivot, un brut, une table relue."""
    pivot_dir = tmp_path / "pivot"
    raw_dir = tmp_path / "raw"
    pivot_dir.mkdir()
    raw_dir.mkdir()

    def poser(slug, nom, date=None, provenance="candidat_declare"):
        pivot = {"id": slug, "nom": nom,
                 "meta": {"provenance": provenance}}
        if date:
            pivot["identite"] = {"date_naissance": date}
        (pivot_dir / f"{slug}.pivot.json").write_text(
            json.dumps(pivot), encoding="utf-8")
        (raw_dir / f"{slug}.json").write_text(
            json.dumps({"nom": nom}), encoding="utf-8")

    poser("edouard-philippe", "Édouard Philippe", "1970-11-28")
    poser("david-lisnard", "David Lisnard")
    poser("selma-labib", "Selma Labib")
    poser("un-inconnu", "Jean Inconnu")
    poser("un-membre-roster", "Membre Roster", provenance="roster_groupe")

    table = tmp_path / "table.json"
    table.write_text(json.dumps({"_meta": {}, "candidats": {
        "david-lisnard": {"appariement": "confirme", "rne": {
            "nom": "LISNARD", "prenom": "David", "date_naissance": "1969-02-02"}},
        "selma-labib": {"appariement": "aucun_mandat_trouve"},
    }}), encoding="utf-8")
    return raw_dir, pivot_dir, table


# --------------------------------------------------------------------------
# L'état civil, qui n'a pas de champ prénom
# --------------------------------------------------------------------------

def test_le_prenom_se_lit_dans_le_nom_complet():
    """Le corpus n'a pas de champ `prenom` : `nom` porte « Nathalie Arthaud »."""
    assert etat_civil({"nom": "Nathalie Arthaud"}) == ("Arthaud", "Nathalie", None)


def test_un_nom_compose_garde_ses_morceaux():
    assert etat_civil({"nom": "Nicolas Dupont-Aignan"})[0] == "Dupont-Aignan"
    assert etat_civil({"nom": "Marine Le Pen"})[0] == "Le Pen"


def test_un_nom_vide_n_apparie_rien():
    assert etat_civil({"nom": ""}) == (None, None, None)


# --------------------------------------------------------------------------
# Quelle clé, et la règle qui les départage
# --------------------------------------------------------------------------

def test_la_date_de_naissance_du_corpus_prime_sur_la_table():
    """Une relecture reste valide, mais elle devient inutile dès que le corpus
    porte la date — et deux sources qui se contrediraient en silence seraient
    pires que l'une des deux. Le cas se produit dès qu'un candidat relu est
    ensuite élu député."""
    pivot = {"nom": "David Lisnard", "identite": {"date_naissance": "1969-02-02"}}
    table = {"candidats": {"david-lisnard": {"appariement": "confirme", "rne": {
        "nom": "AUTRE", "prenom": "Autre", "date_naissance": "1900-01-01"}}}}

    appariement, cle = cle_appariement(pivot, table, "david-lisnard")

    assert appariement == "date_naissance"
    assert cle == ("Lisnard", "David", "1969-02-02")


def test_sans_date_la_table_relue_prend_le_relais():
    pivot = {"nom": "David Lisnard"}
    table = {"candidats": {"david-lisnard": {"appariement": "confirme", "rne": {
        "nom": "LISNARD", "prenom": "David", "date_naissance": "1969-02-02"}}}}

    appariement, cle = cle_appariement(pivot, table, "david-lisnard")

    assert appariement == "table_relue"
    assert cle == ("LISNARD", "David", "1969-02-02")


def test_un_appariement_ecarte_ne_collecte_rien():
    """Arthaud à Limey-Remenauville : une ligne existait, un humain l'a rejetée.
    Recollecter reproposerait l'homonyme à chaque run."""
    table = {"candidats": {"nathalie-arthaud": {"appariement": "ecarte"}}}

    assert cle_appariement({"nom": "Nathalie Arthaud"}, table,
                           "nathalie-arthaud") == ("ecarte", None)


def test_un_candidat_absent_de_la_table_est_NON_RELU_pas_sans_mandat():
    """La distinction qui porte tout le lot."""
    appariement, cle = cle_appariement({"nom": "Jean Inconnu"}, {"candidats": {}},
                                       "jean-inconnu")

    assert appariement == "non_relu"
    assert cle is None


# --------------------------------------------------------------------------
# Le bloc parle même vide
# --------------------------------------------------------------------------

def test_le_bloc_declare_toujours_son_appariement_et_sa_borne():
    bloc = composer_bloc("non_relu", [], "2026-09-15T10:00:00+0200")

    assert bloc["appariement"] == "non_relu"
    assert bloc["borne_couverture"] == "2020"
    assert bloc["mandats"] == []


def test_le_vocabulaire_des_appariements_est_ferme():
    assert KNOWN_APPARIEMENTS == {
        "date_naissance", "table_relue", "ecarte", "aucun_mandat_trouve", "non_relu"}


# --------------------------------------------------------------------------
# De bout en bout
# --------------------------------------------------------------------------

def test_chaque_candidat_declare_recoit_un_bloc(corpus):
    raw_dir, pivot_dir, table = corpus

    rapport = collecter(_appel_vide, raw_dir, pivot_dir, table, appliquer=True)

    assert rapport["nb_profils"] == 4, "les quatre candidats déclarés, pas le roster"
    for slug in ("edouard-philippe", "david-lisnard", "selma-labib", "un-inconnu"):
        brut = json.loads((raw_dir / f"{slug}.json").read_text())
        assert CLE_BLOC in brut, f"{slug} n'a pas de bloc"


def test_un_membre_de_roster_est_hors_perimetre(corpus):
    """~750 membres × 9 fichiers de requêtes pour une donnée qu'aucune page
    n'affiche : le roster n'a pas de fiche publiée."""
    raw_dir, pivot_dir, table = corpus

    collecter(_appel_vide, raw_dir, pivot_dir, table, appliquer=True)

    brut = json.loads((raw_dir / "un-membre-roster.json").read_text())
    assert CLE_BLOC not in brut


def test_les_appariements_sont_comptes_par_categorie(corpus):
    raw_dir, pivot_dir, table = corpus

    rapport = collecter(_appel_vide, raw_dir, pivot_dir, table)

    assert rapport["par_appariement"] == {
        "date_naissance": 1, "table_relue": 1,
        "aucun_mandat_trouve": 1, "non_relu": 1}


def test_les_mandats_collectes_atteignent_le_profil(corpus):
    raw_dir, pivot_dir, table = corpus
    ligne = {COL_NOM: "PHILIPPE", COL_PRENOM: "Edouard",
             COL_NAISSANCE: "1970-11-28",
             "Libellé de la commune": "Le Havre",
             COL_DEBUT_MANDAT: "2026-03-22"}

    collecter(_appel_avec([ligne]), raw_dir, pivot_dir, table, appliquer=True)

    bloc = json.loads((raw_dir / "edouard-philippe.json").read_text())[CLE_BLOC]
    assert bloc["appariement"] == "date_naissance"
    assert [m["label"] for m in bloc["mandats"]] == ["Le Havre"]


def test_sans_apply_rien_n_est_ecrit(corpus):
    raw_dir, pivot_dir, table = corpus

    rapport = collecter(_appel_vide, raw_dir, pivot_dir, table)

    assert rapport["applique"] is False
    assert CLE_BLOC not in json.loads((raw_dir / "david-lisnard.json").read_text())


def test_le_manifeste_ne_consigne_que_les_profils_ecrits(corpus, tmp_path):
    """Uploader `raw_data/profiles/` entier réinjecterait la baseline
    committée du checkout (#450)."""
    raw_dir, pivot_dir, table = corpus
    manifeste = tmp_path / "m" / "locaux.txt"

    collecter(_appel_vide, raw_dir, pivot_dir, table,
              appliquer=True, manifest_out=manifeste)

    lignes = manifeste.read_text(encoding="utf-8").strip().split("\n")
    assert sorted(lignes) == sorted([
        "david-lisnard.json", "edouard-philippe.json",
        "selma-labib.json", "un-inconnu.json"])


def test_un_profil_sans_brut_est_compte_jamais_fabrique(corpus):
    """Fabriquer un socle ici écrirait une fiche sans identité (§2 règle 5)."""
    raw_dir, pivot_dir, table = corpus
    (raw_dir / "un-inconnu.json").unlink()

    rapport = collecter(_appel_vide, raw_dir, pivot_dir, table, appliquer=True)

    assert rapport["sans_brut"] == ["un-inconnu"]
    assert not (raw_dir / "un-inconnu.json").exists()


# --------------------------------------------------------------------------
# Le versement au pivot — collecter n'est pas publier
# --------------------------------------------------------------------------

def test_le_bloc_brut_doit_atteindre_le_pivot():
    """Le run 34953770692 a écrit le bloc dans les 32 profils bruts, et ZÉRO
    mandat n'a atteint le pivot.

    Quatrième fois de la semaine que le motif se répète : la donnée arrive, une
    étape de projection la laisse tomber sans rien dire. Ce test-ci tient le
    contrat côté données ; `generate_all_profiles` tient le versement.
    """
    from generate_all_profiles import _verser_mandats_locaux

    pivot = {"mandats": [], "id": "x"}
    brut = {"mandats_locaux": {
        "appariement": "date_naissance", "borne_couverture": "2020",
        "synchro_le": "2026-09-15T12:00:00+0200",
        "mandats": [{"label": "Cannes", "categorie": "mandat_local"}]}}

    _verser_mandats_locaux(brut, pivot)

    assert [m["label"] for m in pivot["mandats"]] == ["Cannes"]
    assert pivot["mandats_locaux_couverture"]["appariement"] == "date_naissance"
    assert pivot["mandats_locaux_couverture"]["borne_couverture"] == "2020"


def test_un_appariement_sans_mandat_publie_quand_meme_sa_couverture():
    """« Relu, aucun mandat » et « personne n'a regardé » sont deux faits, et
    aucun des deux ne se lit dans une liste vide."""
    from generate_all_profiles import _verser_mandats_locaux

    pivot = {"mandats": [], "id": "x"}
    _verser_mandats_locaux(
        {"mandats_locaux": {"appariement": "non_relu",
                            "borne_couverture": "2020", "mandats": []}}, pivot)

    assert pivot["mandats"] == []
    assert pivot["mandats_locaux_couverture"]["appariement"] == "non_relu"


def test_les_mandats_locaux_ne_touchent_pas_les_chambres():
    """Un conseil régional n'est pas une chambre parlementaire — c'est toute la
    raison d'être de la catégorie `mandat_local` (#492)."""
    from generate_all_profiles import _verser_mandats_locaux
    from schema_pivot import appliquer_chambres

    pivot = {"mandats": [], "id": "x", "chambres": [], "chambre": None}
    _verser_mandats_locaux(
        {"mandats_locaux": {"appariement": "date_naissance", "mandats": [
            {"label": "Hauts-De-France", "categorie": "mandat_local"}]}}, pivot)
    appliquer_chambres(pivot)

    assert pivot["chambres"] == []
