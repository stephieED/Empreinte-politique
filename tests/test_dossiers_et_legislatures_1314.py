"""Les dossiers de l'Assemblée et les législatures, un fichier par objet (#1314).

FIXTURES. Six dossiers **verbatim** des archives réelles (`dossier_*.json`), et
un extrait d'AMO30 (`amo30_extrait/`) : les fiches des sept auteurs de ces
dossiers, réduites à leur état civil, au mandat que le dossier cite et à leurs
mandats de groupe — chaque sous-objet recopié intact —, et les organes de ces
groupes. Les sièges et les groupes des tests de législature sont ceux de quatre
députés de la XVIe, relus dans l'archive figée du 28/06/2024.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import dossiers_an as da  # noqa: E402
import legislatures_an as la  # noqa: E402

FIXTURES = RACINE / "tests" / "fixtures" / "dossiers_an"

RATIFICATION_XV_XVI = "DLR5L15N42368"   # examinée en XVe, débattue en XVIe
PROGRAMMATION_49_3 = "DLR5L16N46346"    # projet de loi adopté par 49.3
SENAT_VERS_XVII = "DLR5L16N50115"       # déposé au Sénat en XVIe, à l'Assemblée en XVIIe
MISSION = "DLR5L16N46011"               # initiative d'un organe
FUCHS = "DLR5L16N46187"                 # proposition de loi d'un député DEM
SENAT_SEUL = "DLR5L16N45892"            # texte resté au Sénat


def _dossier(uid: str) -> dict:
    return json.loads((FIXTURES / f"dossier_{uid}.json").read_text(encoding="utf-8"))["dossierParlementaire"]


@pytest.fixture(scope="module")
def referentiel(tmp_path_factory) -> dict:
    """L'extrait d'AMO30, zippé comme l'archive réelle."""
    zip_path = tmp_path_factory.mktemp("amo30") / "acteurs_historique.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for fichier in sorted((FIXTURES / "amo30_extrait").rglob("*.json")):
            zf.write(fichier, fichier.relative_to(FIXTURES / "amo30_extrait").as_posix())
    return da.construire_referentiel(zip_path)


# ── L'étape à l'Assemblée, par législature ────────────────────────────────────

def test_l_etape_se_lit_par_legislature_de_l_acte():
    """Un texte examiné en commission en XVe et débattu en XVIe a deux étapes :
    la législature est celle que l'uid de chaque acte porte, jamais une date
    rapprochée de bornes."""
    etapes, sans = da.etapes_an(_dossier(RATIFICATION_XV_XVI))

    assert etapes == {"15": "examine_en_commission", "16": "debattu_en_seance"}
    assert sans == 0


def test_un_texte_du_senat_n_a_d_etape_que_la_ou_l_assemblee_a_agi():
    """Déposé au Sénat en XVIe, transmis en XVIIe : aucune étape XVIe, parce
    que les actes XVIe sont ceux du Sénat."""
    etapes, _ = da.etapes_an(_dossier(SENAT_VERS_XVII))

    assert "16" not in etapes
    assert etapes["17"] == "debattu_en_seance"


def test_un_texte_reste_au_senat_a_une_etape_vide():
    etapes, _ = da.etapes_an(_dossier(SENAT_SEUL))

    assert etapes == {}


def test_la_saisie_automatique_de_la_commission_n_est_pas_un_examen():
    """#997 : la saisine accompagne le dépôt, elle n'atteste aucun examen."""
    assert da.etape_de_l_acte("AN1-COM-FOND-SAISIE") == da.ETAPE_DEPOSE
    assert da.etape_de_l_acte("AN1-COM-FOND-REUNION") == da.ETAPE_COMMISSION
    assert da.etape_de_l_acte("AN1-DEBATS-DEC") == da.ETAPE_SEANCE


def test_la_cmp_n_est_rangee_d_aucun_cote():
    assert da.est_acte_an("CMP-DEBATS-AN-DEC")
    assert not da.est_acte_an("CMP-DEC")
    assert not da.est_acte_an("SN1-DEBATS-DEC")


# ── Scrutins et 49.3 ──────────────────────────────────────────────────────────

def test_un_49_3_est_un_fait_de_procedure_sans_scrutin():
    """§2 règle 4 : l'engagement de responsabilité n'est jamais un vote."""
    _scrutins, _non_reconnus, engagements = da.scrutins_et_49_3(_dossier(PROGRAMMATION_49_3))

    assert engagements, "le projet de loi de programmation 2023-2027 a été adopté par 49.3"
    assert {e["issue"] for e in engagements} <= da.KNOWN_ISSUES_49_3
    assert all(set(e) == {"date", "issue", "acte_uid", "code_acte"} for e in engagements)


def test_un_scrutin_cite_mais_absent_du_corpus_est_declare(referentiel):
    """Sans le corpus des scrutins, aucun ne peut être dit solennel : ils sont
    tous déclarés absents du corpus, jamais rangés « non solennels »."""
    ligne = da.entree(_dossier(SENAT_VERS_XVII), referentiel, {})

    assert ligne["scrutins_an"] == ["an:17:3057"]
    assert ligne["scrutins_solennels"] == []
    assert ligne["scrutins_absents_du_corpus"] == ["an:17:3057"]


def test_un_vote_solennel_se_lit_dans_le_type_du_scrutin(referentiel):
    ligne = da.entree(_dossier(SENAT_VERS_XVII), referentiel, {"an:17:3057": da.TYPE_SCRUTIN_SOLENNEL})

    assert ligne["scrutins_solennels"] == ["an:17:3057"]
    assert ligne["scrutins_absents_du_corpus"] is None


# ── Les auteurs ───────────────────────────────────────────────────────────────

def test_la_qualite_vient_du_mandat_cite_et_le_groupe_du_jour_du_depot(referentiel):
    """Bruno Fuchs dépose le 23/08/2022 au titre de son mandat de député : son
    groupe ce jour-là est le groupe Démocrate de la XVIe (PO800484)."""
    ligne = da.entree(_dossier(FUCHS), referentiel, {})
    auteur = ligne["initiateurs"][0]

    assert auteur["acteur_ref"] == "PA722284"
    assert auteur["qualite"] == "depute"
    assert auteur["groupe_ref"] == "PO800484"
    assert auteur["non_resolu"] is None


def test_un_membre_du_gouvernement_n_a_pas_de_groupe_et_c_est_dit(referentiel):
    ligne = da.entree(_dossier(PROGRAMMATION_49_3), referentiel, {})

    assert {a["qualite"] for a in ligne["initiateurs"]} == {"membre_du_gouvernement"}
    assert all(a["groupe_ref"] is None for a in ligne["initiateurs"])
    assert all(a["non_resolu"] == {"groupe": "qualite_sans_groupe"} for a in ligne["initiateurs"])


def test_un_senateur_prend_son_groupe_du_senat(referentiel):
    ligne = da.entree(_dossier(SENAT_SEUL), referentiel, {})
    auteur = ligne["initiateurs"][0]

    assert auteur["qualite"] == "senateur"
    assert auteur["groupe_ref"], "le mandat GROUPESENAT ouvert le jour du dépôt"


def test_un_mandat_absent_d_amo30_est_declare(referentiel):
    reduit = json.loads(json.dumps(referentiel))
    reduit["acteurs"]["PA722284"]["mandats"] = {}
    auteur = da.entree(_dossier(FUCHS), reduit, {})["initiateurs"][0]

    assert auteur["qualite"] is None
    assert auteur["non_resolu"] == {"qualite": "mandat_introuvable", "groupe": "qualite_non_resolue"}


def test_sans_referentiel_les_auteurs_restent_nommes_par_leur_reference():
    auteur = da.entree(_dossier(FUCHS), None, {})["initiateurs"][0]

    assert auteur["acteur_ref"] == "PA722284"
    assert auteur["non_resolu"]["qualite"] == "referentiel_indisponible"


def test_une_initiative_d_organe_n_est_pas_un_dossier_sans_auteur(referentiel):
    ligne = da.entree(_dossier(MISSION), referentiel, {})

    assert ligne["initiateurs"] is None
    assert ligne["initiateurs_non_resolus"] == {"motif": "initiative_d_organe"}
    assert ligne["organes_initiateurs"]


def test_les_motifs_sont_ceux_des_vocabulaires_fermes(referentiel):
    for uid in (RATIFICATION_XV_XVI, PROGRAMMATION_49_3, SENAT_VERS_XVII, MISSION, FUCHS, SENAT_SEUL):
        ligne = da.entree(_dossier(uid), referentiel, {})
        assert set(ligne["etape_an"].values()) <= da.KNOWN_ETAPES_AN
        if ligne["initiateurs_non_resolus"]:
            assert ligne["initiateurs_non_resolus"]["motif"] in da.KNOWN_MOTIFS_INITIATEURS_NON_RESOLUS
        for auteur in ligne["initiateurs"] or []:
            assert auteur["qualite"] in da.KNOWN_QUALITES_INITIATEUR | {None}
            for champ, motif in (auteur["non_resolu"] or {}).items():
                vocabulaire = (da.KNOWN_MOTIFS_QUALITE_NON_RESOLUE if champ == "qualite"
                               else da.KNOWN_MOTIFS_GROUPE_NON_RESOLU)
                assert motif in vocabulaire


# ── Le découpage et la fusion ─────────────────────────────────────────────────

def test_un_dossier_parait_dans_chaque_legislature_ou_l_assemblee_a_agi(referentiel):
    ligne = da.entree(_dossier(RATIFICATION_XV_XVI), referentiel, {})

    assert da.legislatures_du_dossier(ligne) == ["15", "16"]


def test_la_fusion_conserve_ce_qu_un_run_n_a_pas_revu(tmp_path, referentiel):
    """AGENTS.md §3a : un run partiel remplace ses lignes, garde les autres, et
    garde les noms qu'il ne relit pas."""
    premier = {FUCHS: da.entree(_dossier(FUCHS), referentiel, {})}
    da.ecrire(tmp_path, premier, referentiel)
    second = {SENAT_SEUL: da.entree(_dossier(SENAT_SEUL), referentiel, {})}
    da.ecrire(tmp_path, second, None)

    publie = json.loads((tmp_path / "16.json").read_text(encoding="utf-8"))
    assert set(publie["dossiers"]) == {FUCHS, SENAT_SEUL}
    assert publie["acteurs"]["PA722284"] == "Bruno Fuchs"
    assert publie["organes"]["PO800484"]["sigle"] == "DEM"


def test_sans_fusion_la_reconstruction_repart_de_rien(tmp_path, referentiel):
    da.ecrire(tmp_path, {FUCHS: da.entree(_dossier(FUCHS), referentiel, {})}, referentiel)
    da.ecrire(tmp_path, {SENAT_SEUL: da.entree(_dossier(SENAT_SEUL), referentiel, {})},
              referentiel, fusion=False)

    publie = json.loads((tmp_path / "16.json").read_text(encoding="utf-8"))
    assert set(publie["dossiers"]) == {SENAT_SEUL}


# ── Les législatures ──────────────────────────────────────────────────────────

def test_le_terme_redonne_les_deux_fins_au_terme_publiees_par_l_assemblee():
    """Art. LO 121 : XIVe élue en 2012, finie le 20/06/2017 ; XVe élue en 2017,
    finie le 21/06/2022 — les deux `dateFin` de l'organe ASSEMBLEE."""
    assert la.terme_prevu("2012-06-20")["date"] == "2017-06-20"
    assert la.terme_prevu("2017-06-21")["date"] == "2022-06-21"
    assert la.terme_prevu("2022-06-22")["date"] == "2027-06-15"
    assert la.terme_prevu(None) is None


def _actes_juin_2024(repertoire: Path) -> Path:
    """La ligne du décret, telle que `pivot_data/actes_reglementaires/2024-06.json`
    la publie, et sa voisine dans le fichier."""
    repertoire.mkdir(parents=True, exist_ok=True)
    (repertoire / "2024-06.json").write_text(json.dumps({
        "prefixe_ids": "JORFTEXT",
        "ids": ["000049689651", "000049629721"],
        "actes": [
            [1, "Décret du 9 juin 2024 portant dissolution de l'Assemblée nationale",
             "2024-06-10", 14, "PREX2415533D", None],
            [1, "Décret du 31 mai 2024 portant nomination dans l'ordre national du Mérite",
             "2024-06-01", 14, "IOMK2404697D", None],
        ],
    }, ensure_ascii=False), encoding="utf-8")
    return repertoire


def test_la_dissolution_se_lit_au_journal_officiel(tmp_path):
    decret = la.decret_de_dissolution("2024-06-09", _actes_juin_2024(tmp_path / "actes"))

    assert decret["jorftext"] == "JORFTEXT000049689651"
    assert decret["date_publication"] == "2024-06-10"
    assert la.mode_de_fin("2024-06-09", la.terme_prevu("2022-06-22"), decret) == ("dissolution", None)


def test_une_fin_sans_decret_ni_terme_n_est_pas_expliquee(tmp_path):
    actes = _actes_juin_2024(tmp_path / "actes")

    assert la.decret_de_dissolution("2017-06-20", actes) is None
    assert la.mode_de_fin("2017-06-20", la.terme_prevu("2012-06-20"), None) == ("terme", None)
    assert la.mode_de_fin("2016-01-01", la.terme_prevu("2012-06-20"), None) == (None, "fin_non_expliquee")
    assert la.mode_de_fin(None, la.terme_prevu("2024-07-01"), None) == (None, "en_cours")


#: Quatre députés de la XVIe, leurs mandats de groupe (index GP d'AMO30) et
#: leur siège dans l'archive figée du 28/06/2024.
INDEX_GP_XVI = {
    "organes": {
        "PO793087": {"sigle": "NI", "sigle_abrege": "NI", "libelle": "Non inscrit", "legislature": "16"},
        "PO800484": {"sigle": "DEM", "sigle_abrege": "Dem", "libelle": "Démocrate (MoDem et Indépendants)",
                     "legislature": "16"},
        "PO800520": {"sigle": "RN", "sigle_abrege": "RN", "libelle": "Rassemblement National", "legislature": "16"},
        "PO800490": {"sigle": "LFI-NUPES", "sigle_abrege": "LFI - NUPES",
                     "libelle": "La France insoumise - Nouvelle Union Populaire écologique et sociale",
                     "legislature": "16"},
        "PO800502": {"sigle": "GDR-NUPES", "sigle_abrege": "GDR - NUPES",
                     "libelle": "Gauche démocrate et républicaine - NUPES", "legislature": "16"},
    },
    "mandats": {
        "PO793087": [["PA722284", "2022-06-22", "2022-06-28"], ["PA720614", "2022-06-22", "2022-06-28"],
                     ["PA720892", "2022-06-22", "2022-06-28"], ["PA722202", "2022-06-22", "2022-06-28"]],
        "PO800484": [["PA722284", "2022-06-29", "2024-06-09"]],
        "PO800520": [["PA720614", "2022-06-29", "2024-06-09"], ["PA720614", "2022-06-29", "2024-06-09"]],
        "PO800490": [["PA720892", "2022-06-29", "2024-06-09"]],
        "PO800502": [["PA722202", "2022-06-29", "2024-06-09"]],
    },
}
PLACES_XVI = {
    "PA722284": {"2022-06-19": "276"}, "PA720614": {"2022-06-19": "035"},
    "PA720892": {"2022-06-19": "623"}, "PA722202": {"2022-06-19": "583"},
}


def test_les_groupes_se_rangent_par_leur_siege_median_au_jour_de_reference():
    groupes = la.groupes_par_siege(INDEX_GP_XVI, "16", "2024-06-09", PLACES_XVI)

    assert [g["sigle"] for g in groupes] == ["RN", "DEM", "GDR-NUPES", "LFI-NUPES"]
    assert groupes[0]["place_mediane"] == 35
    assert all(g["membres_au_jour"] == g["membres_avec_place"] == 1 for g in groupes)


def test_un_groupe_de_transit_ne_siege_plus_au_jour_de_reference():
    """Les non-inscrits du 22 au 28 juin 2022 sont la constitution des groupes,
    pas un groupe de fin de législature."""
    groupes = la.groupes_par_siege(INDEX_GP_XVI, "16", "2024-06-09", PLACES_XVI)

    assert "NI" not in {g["sigle"] for g in groupes}


def test_sans_archive_les_groupes_restent_publies_sans_siege():
    groupes = la.groupes_par_siege(INDEX_GP_XVI, "16", "2024-06-09", {})

    assert len(groupes) == 4
    assert all(g["place_mediane"] is None and g["membres_avec_place"] == 0 for g in groupes)


def test_une_legislature_sans_archive_le_dit(tmp_path):
    ligne = la.entree(
        "14", {"organe_ref": "PO644420", "debut": "2012-06-20", "fin": "2017-06-20"},
        source_url="https://exemple", repertoire_actes=tmp_path, index_gp=INDEX_GP_XVI,
        index_places=None, motif_places="legislature_sans_archive_figee",
    )

    assert ligne["mode_fin"] == "terme"
    assert ligne["places_non_resolues"] == {"motif": "legislature_sans_archive_figee"}
    assert ligne["groupes_jour_reference"] == "2017-06-20"
