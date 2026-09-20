import io
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from schema_gouvernement import KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL
from gouvernement_textes import (
    collect_dossiers_gouvernementaux,
    collect_dossiers_gouvernementaux_multi,
    ensure_dossiers_zip_downloaded,
    fetch_dossiers_gouvernementaux,
    parse_dossier_gouvernemental,
)


# ---------------------------------------------------------------------------
# Fixtures (structures calquées sur le JSON réel observé dans
# Dossiers_Legislatifs.json.zip, voir docs/sources/an-opendata.md)
# ---------------------------------------------------------------------------

def _acte(code_acte, date_acte=None, statut_conclusion=None, enfants=None,
          texte_associe=None):
    return {
        "codeActe": code_acte,
        "dateActe": date_acte,
        "statutConclusion": statut_conclusion,
        "texteAssocie": texte_associe,
        "actesLegislatifs": {"acteLegislatif": enfants} if enfants else None,
    }


# Préfixe du document réellement déposé — signal d'origine primaire depuis
# #400 (PRJL = projet de loi, PION = proposition, PNRE = résolution).
_PREFIXE_DOC_PAR_TITRE = {
    "projet de loi": "PRJL",
    "proposition de loi": "PION",
}


def _document_par_defaut(titre: str) -> str:
    titre_normalise = (titre or "").strip().lower()
    for prefixe_titre, prefixe_doc in _PREFIXE_DOC_PAR_TITRE.items():
        if titre_normalise.startswith(prefixe_titre):
            return f"{prefixe_doc}ANR5L17B0001"
    return "PNREANR5L17B0001"


def _dossier(uid, titre, actes, *, legislature="17", titre_chemin="titre-chemin",
             procedure_code=None):
    """Dossier de test. Les actes `*-DEPOT` sans `texteAssocie` explicite en
    reçoivent un, déduit du titre : dans les données réelles un dépôt porte
    toujours le document déposé, et c'est ce document qui détermine l'origine
    depuis #400. Passer `texte_associe=` à `_acte` pour outrepasser."""
    actes_completes = []
    for acte in actes:
        if (
            str(acte.get("codeActe") or "").endswith("-DEPOT")
            and not acte.get("texteAssocie")
        ):
            acte = {**acte, "texteAssocie": _document_par_defaut(titre)}
        actes_completes.append(acte)
    dossier = {
        "uid": uid,
        "legislature": legislature,
        "titreDossier": {"titre": titre, "titreChemin": titre_chemin, "senatChemin": None},
        "initiateur": {"acteurs": {"acteur": [{"acteurRef": "PA643210", "mandatRef": "PM873637"}]}},
        "actesLegislatifs": {"acteLegislatif": actes_completes},
    }
    if procedure_code is not None:
        dossier["procedureParlementaire"] = {"code": procedure_code, "libelle": "test"}
    return dossier


def _make_zip(dossiers: dict[str, dict], *, extra_files: dict[str, str] | None = None) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for uid, dossier in dossiers.items():
            zf.writestr(f"json/dossierParlementaire/{uid}.json", json.dumps({"dossierParlementaire": dossier}))
        for name, content in (extra_files or {}).items():
            zf.writestr(name, content)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# parse_dossier_gouvernemental — origine
# ---------------------------------------------------------------------------

def test_origine_proposition_de_loi_exclue():
    dossier = _dossier("TEST-PPL", "Proposition de loi test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    assert parse_dossier_gouvernemental(dossier) is None


def test_origine_sans_prefixe_reconnu_exclue():
    dossier = _dossier("TEST-RES", "Résolution portant sur un sujet quelconque", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    assert parse_dossier_gouvernemental(dossier) is None


def test_origine_projet_de_loi_organique_incluse():
    dossier = _dossier("TEST-ORGA", "Projet de loi organique test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record is not None
    assert record["statut"] == "depose"


# ---------------------------------------------------------------------------
# parse_dossier_gouvernemental — statut : cas nominaux
# ---------------------------------------------------------------------------

def test_statut_adopte():
    dossier = _dossier("TEST-ADOPTE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF01", "libelle": "adoptée"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "adopte"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


def test_statut_rejete():
    dossier = _dossier("TEST-REJETE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF07", "libelle": "rejetée"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "rejete"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


# --- fam_code ajoutés en #397 -----------------------------------------------
# Leur absence excluait 45 dossiers sur 106 (42 %) du jeu de données. Le
# libellé de chaque cas est celui porté par le dataset AN lui-même.

def test_statut_adopte_sans_modification():
    """TSORTF03 : adoption définitive par la seconde chambre sans modifier le
    texte — une adoption au même titre que TSORTF01."""
    dossier = _dossier("TEST-SANS-MODIF", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("SN1-DEBATS-DEC", "2024-03-01",
              {"fam_code": "TSORTF03", "libelle": "adopté sans modification"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "adopte"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


def test_statut_adopte_cmp_est_distinct_dadopte():
    """TSORTF18 : approbation du texte de CMP (art. 45 al. 3). L'issue est une
    adoption, mais la voie procédurale reste distincte et n'est pas fondue
    dans `adopte` — arbitrage #397, symétrique de celui de #208 sur le 49.3.
    Cas réel : PLF 2025 (DLR5L17N50198)."""
    dossier = _dossier("TEST-CMP", "Projet de loi de finances test", [
        _acte("AN1-DEPOT", "2024-10-10"),
        _acte("AN1-DEBATS-DEC", "2025-02-06", {
            "fam_code": "TSORTF18",
            "libelle": "adopté, dans les conditions prévues à l'article 45, "
                       "alinéa 3, de la Constitution",
        }),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "adopte_cmp"
    assert record["statut"] != "adopte", "ne pas collapser vers adopte (§2.4)"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


def test_statut_modifie_est_une_navette_en_cours():
    """TSORTF05 : « modifié » n'est pas une issue mais la poursuite de la
    navette."""
    dossier = _dossier("TEST-MODIFIE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("SN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF05", "libelle": "modifié"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "navette_en_cours"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


# --- fam_code ajoutés en #402 -----------------------------------------------
# Apparus avec l'ingestion des archives XV/XVI (#400). Le libellé de chaque cas
# est celui porté par le dataset AN lui-même.

def test_statut_adopte_avec_modifications_est_une_navette_en_cours():
    """TSORTF02 : « adopté avec modifications » décrit le même fait que
    TSORTF05 — une chambre adopte un texte qu'elle a modifié, donc la navette
    continue. Vérifié sur données réelles : sur 53 occurrences, les 29 non
    terminales sont toutes suivies d'une lecture dans l'autre chambre, et
    7 des 24 terminales ne sont jamais promulguées (#402)."""
    dossier = _dossier("TEST-AVEC-MODIF", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF05", "libelle": "modifié"}),
        _acte("SN2-DEBATS-DEC", "2024-05-15",
              {"fam_code": "TSORTF02", "libelle": "adopté avec modifications"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "navette_en_cours"
    assert record["statut"] != "adopte", "sans promulgation, rien n'établit l'adoption (§2.5)"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


def test_statut_adopte_avec_modifications_puis_promulgation():
    """Cas réel `DLR5L16N48973` : TSORTF02 en 2e lecture au Sénat, puis
    publication au JO 8 jours plus tard. La promulgation prime (#400) — c'est
    elle, et non le libellé de la décision de séance, qui établit l'issue."""
    dossier = _dossier("TEST-AVEC-MODIF-PROM", "Projet de loi ordinaire test", [
        _acte("SN1-DEPOT", "2023-11-22"),
        _acte("AN1-DEBATS-DEC", "2024-04-08", {"fam_code": "TSORTF05", "libelle": "modifié"}),
        _acte("SN2-DEBATS-DEC", "2024-05-15",
              {"fam_code": "TSORTF02", "libelle": "adopté avec modifications"}),
        _acte("PROM-PUB", "2024-05-23"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "promulgue"
    assert record["warnings"] == []


def test_statut_vote_en_termes_identiques_est_une_adoption():
    """TSORTF14 : le vote conforme des deux assemblées est une adoption
    parlementaire achevée. Cas réel `DLR5L16N49373` (projet de loi
    constitutionnelle sur le corps électoral calédonien) : jamais promulgué
    faute de Congrès, d'où `adopte` et non `promulgue`."""
    dossier = _dossier("TEST-TERMES-IDENTIQUES", "Projet de loi constitutionnelle test", [
        _acte("SN1-DEPOT", "2024-01-29"),
        _acte("SN1-DEBATS-DEC", "2024-04-02", {"fam_code": "TSORTF01", "libelle": "adopté"}),
        _acte("AN1-DEBATS-DEC", "2024-05-14", {
            "fam_code": "TSORTF14",
            "libelle": "voté par les deux assemblées du Parlement en termes identiques",
        }),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "adopte"
    assert record["statut"] != "promulgue", "adoption parlementaire n'est pas promulgation"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


def test_statut_rejete_definitivement():
    """TSORTF13 : rejet prononcé par un vote en lecture définitive, distinct
    du rejet consécutif à un 49.3 (`TSORTF24`), d'où `sort_49_3 = False`. Cas
    réel `DLR5L16N45929` (règlement du budget 2021, 03/08/2022)."""
    dossier = _dossier("TEST-REJETE-DEF", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2022-07-04"),
        _acte("SNNLEC-DEBATS-DEC", "2022-08-02", {"fam_code": "TSORTF07", "libelle": "rejeté"}),
        _acte("ANLDEF-DEBATS-DEC", "2022-08-03",
              {"fam_code": "TSORTF13", "libelle": "rejeté définitivement"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "rejete"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


def test_elargissement_du_mapping_ne_desactive_pas_la_protection_25():
    """L'ajout de trois codes ne doit pas transformer la nomenclature fermée
    en fourre-tout : un fam_code réellement inconnu produit toujours
    statut = None et un warning, jamais un statut par défaut (§2.5)."""
    dossier = _dossier("TEST-INCONNU-2", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01",
              {"fam_code": "TSORTF42", "libelle": "issue inédite"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] is None
    assert len(record["warnings"]) == 1
    assert "TSORTF42" in record["warnings"][0]


def test_statut_retire():
    dossier = _dossier("TEST-RETIRE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-RTRINI", "2024-02-15"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "retire"
    assert record["sort_49_3"] is None
    assert record["warnings"] == []


def test_statut_navette_en_cours_quand_deja_examine_sans_decision():
    """L'intention de ce test est juste, sa fixture ne l'était pas (#997).

    Elle portait `AN1-COM` **daté du 2024-02-01**. Or, sur les archives XV à
    XVII, `AN1-COM` est un conteneur d'étape : 6 418 occurrences, **aucune
    datée**. La fixture décrivait donc un monde que la source ne produit pas,
    et c'est elle qui faisait croire que `navette_en_cours` était atteint par
    un renvoi en commission.

    `AN1-COM-FOND-REUNION` est le code réel d'un examen — 3 672 occurrences
    sur les mêmes archives.
    """
    dossier = _dossier("TEST-NAVETTE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-COM-FOND-REUNION", "2024-02-01"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "navette_en_cours"
    assert record["warnings"] == []


def test_statut_depose_quand_seul_le_depot_existe():
    dossier = _dossier("TEST-DEPOSE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "depose"
    assert record["warnings"] == []


def test_statut_depose_malgre_la_saisine_automatique_de_commission():
    """LE défaut de #997, dans la forme exacte où il se produit.

    Copié de `DLR5L16N49329` (proposition de loi de Marine Le Pen), relu dans
    l'archive XVI le 18/09/2026 : le dépôt et la saisine portent **la même
    date**, et rien d'autre ne suit. La saisine est automatique au dépôt ; la
    traiter comme un acte franchi rendait `"depose"` inatteignable — 279 des
    728 dossiers d'origine gouvernementale étaient publiés `navette_en_cours`.
    """
    dossier = _dossier("TEST-SAISIE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-25"),
        _acte("AN1-COM-FOND-SAISIE", "2024-01-25"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "depose"
    assert record["warnings"] == []


def test_statut_depose_malgre_la_nomination_d_un_rapporteur():
    """L'option A, écartée le 18/09/2026 : une nomination dit que la commission
    s'organise, pas qu'elle a examiné."""
    dossier = _dossier("TEST-NOMIN", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-COM-FOND-NOMIN", "2024-01-20"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "depose"


def test_le_rapport_de_commission_vaut_examen_comme_la_reunion():
    """B retient les deux signaux, et `-AVIS` à côté de `-FOND` : une
    commission saisie pour avis qui se réunit a examiné le texte."""
    for code in ("AN1-COM-FOND-RAPPORT", "AN1-COM-AVIS-REUNION",
                 "CMP-COM-RAPPORT-AN", "SN1-COM-FOND-REUNION"):
        dossier = _dossier(f"TEST-{code}", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
            _acte(code, "2024-02-01"),
        ])
        assert parse_dossier_gouvernemental(dossier)["statut"] == "navette_en_cours", code


def test_une_motion_est_un_acte_et_non_un_conteneur():
    """`MOTION` est le seul `codeActe` sans tiret qui porte une date — 8
    occurrences, 8 datées, mesuré sur les archives XV à XVII. Les 16 autres
    codes nus n'en portent jamais : ce sont des conteneurs d'étape, présents
    dès le dépôt. Sans cette exception, une motion ne compterait pas."""
    dossier = _dossier("TEST-MOTION", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("MOTION", "2024-02-01"),
    ])
    assert parse_dossier_gouvernemental(dossier)["statut"] == "navette_en_cours"


def test_un_conteneur_d_etape_n_atteste_rien():
    """`AN1`, `PROM`, `CMP`… sans tiret et sans date : ils portent les actes de
    leur étape, ils n'en sont pas un."""
    for code in ("AN1", "SN1", "ANLUNI", "CMP", "AN20"):
        dossier = _dossier(f"TEST-{code}", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
            _acte(code, None),
        ])
        assert parse_dossier_gouvernemental(dossier)["statut"] == "depose", code


# ---------------------------------------------------------------------------
# parse_dossier_gouvernemental — cas limites de statut
# ---------------------------------------------------------------------------

def test_fam_code_inconnu_produit_un_warning_jamais_un_statut_par_defaut():
    dossier = _dossier("TEST-INCONNU", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF99", "libelle": "inconnu"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] is None
    assert len(record["warnings"]) == 1
    assert "TEST-INCONNU" in record["warnings"][0]
    assert "TSORTF99" in record["warnings"][0]


def test_fam_code_sentinelle_tsortfnull_ignore_sans_warning():
    dossier = _dossier("TEST-SENTINELLE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("SNNLEC-DEBATS-DEC", "2024-02-01", {"fam_code": "TSORTFnull"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "navette_en_cours"
    assert record["warnings"] == []


def test_rejete_via_49_3_censure_mappe_vers_rejete_49_3_sans_warning():
    dossier = _dossier("TEST-CENSURE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("CMP-DEBATS-AN-DEC", "2024-03-01", {
            "fam_code": "TSORTF24",
            "libelle": "considéré comme rejeté [...] article 49, alinéa 3, motion de censure adoptée",
        }),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "rejete_49_3"
    assert record["sort_49_3"] is True
    assert record["warnings"] == []


def test_conclusion_conseil_constitutionnel_nest_pas_une_decision_de_seance():
    """CC-CONCLUSION porte un statutConclusion mais n'est pas un `-DEBATS-DEC` :
    la dernière vraie décision de séance (adoption) doit rester déterminante,
    même si la conclusion du Conseil constitutionnel est chronologiquement
    postérieure (cas réel DLR5L17N50588, voir docs/sources/an-opendata.md)."""
    dossier = _dossier("TEST-CC", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF01", "libelle": "adoptée"}),
        _acte("CC-CONCLUSION", "2024-04-01", {"fam_code": "TCD02", "libelle": "Partiellement conforme"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "adopte"
    assert record["warnings"] == []


def test_derniere_decision_de_seance_chronologique_prevaut_sur_une_decision_anterieure():
    """Une première lecture adoptée, puis modifiée en seconde chambre : le
    dossier est toujours en navette, pas 'adopté' (cas réel DLR5L17N54196,
    voir docs/sources/an-opendata.md)."""
    dossier = _dossier("TEST-NAVETTE-2", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF07", "libelle": "rejetée"}),
        _acte("SN1-DEBATS-DEC", "2024-04-01", {"fam_code": "TSORTF05", "libelle": "modifié"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    # Avant #397, TSORTF05 n'était pas mappé : ce test assertait statut = None
    # + warning, alors que sa propre docstring décrivait une navette en cours.
    # Le mapping du code réaligne le résultat sur l'intention.
    assert record["statut"] == "navette_en_cours"
    assert record["sort_49_3"] is False
    assert record["warnings"] == []


# ---------------------------------------------------------------------------
# parse_dossier_gouvernemental — dates / chambre / source_url
# ---------------------------------------------------------------------------

def test_date_depot_est_le_premier_depot_chronologique_toutes_chambres():
    dossier = _dossier("TEST-DATES", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("SN1-DEPOT", "2024-02-05"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF01", "libelle": "adoptée"}),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["date_depot"] == "2024-01-10"
    assert record["date_dernier_evenement"] == "2024-03-01"
    assert record["chambre_depot_initial"] == "AN"


def test_chambre_depot_initial_senat_quand_premier_depot_au_senat():
    dossier = _dossier("TEST-SENAT-DEPOT", "Projet de loi ordinaire test", [
        _acte("SN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEPOT", "2024-02-05"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["chambre_depot_initial"] == "Senat"
    assert record["date_depot"] == "2024-01-10"


def test_source_url_construite_depuis_legislature_et_titre_chemin():
    dossier = _dossier(
        "TEST-URL", "Projet de loi ordinaire test", [_acte("AN1-DEPOT", "2024-01-10")],
        legislature="17", titre_chemin="mon_titre_chemin",
    )
    record = parse_dossier_gouvernemental(dossier)
    assert record["source_url"] == "https://www.assemblee-nationale.fr/dyn/17/dossiers/mon_titre_chemin"


# ---------------------------------------------------------------------------
# parse_dossier_gouvernemental — initiateurs (#435) : le lien membre -> texte,
# porté par `initiateur.acteurs.acteur[].acteurRef` dans le dump AN.
# ---------------------------------------------------------------------------

def test_initiateur_unique_en_objet_extrait():
    """Forme majoritaire du dump : `acteur` est un objet, pas une liste."""
    dossier = _dossier("TEST-INIT-1", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    dossier["initiateur"] = {"acteurs": {"acteur": {"acteurRef": "PA796090", "mandatRef": "PM840372"}}}
    record = parse_dossier_gouvernemental(dossier)
    assert record["initiateurs_acteur_refs"] == ["PA796090"]


def test_initiateurs_multiples_tous_conserves_dans_lordre_de_la_source():
    """365 des 725 textes rattachés à un gouvernement portent plusieurs
    initiateurs : aucun n'est arbitrairement élu « le » déposant."""
    dossier = _dossier("TEST-INIT-N", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    dossier["initiateur"] = {"acteurs": {"acteur": [
        {"acteurRef": "PA643210", "mandatRef": "PM873637"},
        {"acteurRef": "PA721836", "mandatRef": "PM873664"},
    ]}}
    record = parse_dossier_gouvernemental(dossier)
    assert record["initiateurs_acteur_refs"] == ["PA643210", "PA721836"]


def test_initiateur_absent_donne_none_jamais_une_liste_vide():
    """Constaté sur 2 des 725 textes : la source ne déclare aucun initiateur.
    `[]` se lirait comme « aucun ministre n'a porté ce texte » (AGENTS.md §2.5)."""
    dossier = _dossier("TEST-INIT-0", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    dossier["initiateur"] = None
    record = parse_dossier_gouvernemental(dossier)
    assert record["initiateurs_acteur_refs"] is None

    del dossier["initiateur"]
    assert parse_dossier_gouvernemental(dossier)["initiateurs_acteur_refs"] is None


def test_initiateur_organe_seul_sans_acteur_nomme_donne_none():
    """25 dossiers de l'archive XVII ne portent qu'un `organes` : une initiative
    d'organe n'est pas un lien vers un membre, et ne s'invente pas."""
    dossier = _dossier("TEST-INIT-ORGANE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    dossier["initiateur"] = {"organes": {"organe": {"organeRef": {"uid": "PO866403"}}}, "acteurs": None}
    record = parse_dossier_gouvernemental(dossier)
    assert record["initiateurs_acteur_refs"] is None


def test_initiateurs_dedoublonnes_et_entrees_illisibles_ignorees():
    dossier = _dossier("TEST-INIT-DEDUP", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    dossier["initiateur"] = {"acteurs": {"acteur": [
        {"acteurRef": "PA643210"},
        {"acteurRef": "PA643210"},   # doublon de la source
        {"mandatRef": "PM873664"},   # pas d'acteurRef : aucun lien à en tirer
        {"acteurRef": ""},           # référence vide : idem
        "PA000000",                  # entrée non structurée
    ]}}
    record = parse_dossier_gouvernemental(dossier)
    assert record["initiateurs_acteur_refs"] == ["PA643210"]


# ---------------------------------------------------------------------------
# Texte réel vérifié manuellement (PLFSS 2025, DLR5L17N50588 — structure et
# dates constatées en direct sur data.assemblee-nationale.fr le 2026-08-14,
# voir docs/sources/an-opendata.md) : engagement de responsabilité rejeté en 1ère
# lecture (49.3 + motion de censure adoptée, chute du gouvernement Barnier),
# puis nouvel engagement en nouvelle lecture, considéré comme adopté.
# ---------------------------------------------------------------------------

def test_texte_reel_plfss_2025_49_3_puis_adoption_49_3():
    dossier = _dossier(
        "DLR5L17N50588",
        "Projet de loi de financement de la sécurité sociale pour 2025",
        [
            _acte("AN1-DEPOT", "2024-10-10"),
            _acte("SN1-DEPOT", "2024-11-08"),
            _acte("SN1-DEBATS-DEC", "2024-11-26", {"fam_code": "TSORTF05", "libelle": "modifié"}),
            _acte("CMP-DEBATS-AN-DEC", "2024-12-04", {
                "fam_code": "TSORTF24",
                "libelle": "considéré comme rejeté [...] article 49, alinéa 3, motion de censure adoptée",
            }),
            _acte("CMP-DEBATS-SN-DEC", "2025-01-23", {
                "fam_code": "TSORTF18",
                "libelle": "adopté, dans les conditions prévues à l'article 45, alinéa 3",
            }),
            _acte("CMP-DEC", "2024-11-28", {"fam_code": "TCCMP01", "libelle": "Accord"}),
            _acte("ANNLEC-DEPOT", "2024-11-26"),
            _acte("ANNLEC-DEBATS-DEC", "2025-02-12", {
                "fam_code": "TSORTF06",
                "libelle": "considéré comme adopté [...] article 49, alinéa 3",
            }),
            _acte("SNNLEC-DEPOT", "2025-02-12"),
            _acte("SNNLEC-DEBATS-DEC", "2025-02-17", {"fam_code": "TSORTFnull"}),
            _acte("CC-CONCLUSION", "2025-02-28", {"fam_code": "TCD02", "libelle": "Partiellement conforme"}),
        ],
        legislature="17",
        titre_chemin="plfss_pour_2025",
    )
    record = parse_dossier_gouvernemental(dossier)
    assert record["dossier_id"] == "DLR5L17N50588"
    assert record["titre"] == "Projet de loi de financement de la sécurité sociale pour 2025"
    assert record["statut"] == "adopte_49_3"
    assert record["sort_49_3"] is True
    assert record["date_depot"] == "2024-10-10"
    assert record["date_dernier_evenement"] == "2025-02-28"
    assert record["chambre_depot_initial"] == "AN"
    assert record["source_url"] == "https://www.assemblee-nationale.fr/dyn/17/dossiers/plfss_pour_2025"
    assert record["warnings"] == []


# ---------------------------------------------------------------------------
# collect_dossiers_gouvernementaux
# ---------------------------------------------------------------------------

def test_collect_ignore_les_entrees_non_dossier_et_les_json_illisibles():
    dossiers = {
        "TEST-OK": _dossier("TEST-OK", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
        ]),
    }
    zip_bytes = _make_zip(dossiers, extra_files={
        "json/document/sans-rapport.json": "{}",
        "json/dossierParlementaire/TEST-CASSE.json": "{not valid json",
    })
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        result = collect_dossiers_gouvernementaux(zf)

    assert [d["dossier_id"] for d in result["dossiers"]] == ["TEST-OK"]
    assert result["warnings"] == []


def test_collect_exclut_les_dossiers_non_gouvernementaux():
    dossiers = {
        "TEST-GOUV": _dossier("TEST-GOUV", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
        ]),
        "TEST-PARL": _dossier("TEST-PARL", "Proposition de loi test", [
            _acte("AN1-DEPOT", "2024-01-10"),
        ]),
    }
    zip_bytes = _make_zip(dossiers)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        result = collect_dossiers_gouvernementaux(zf)

    assert [d["dossier_id"] for d in result["dossiers"]] == ["TEST-GOUV"]


def test_collect_agrege_les_warnings_de_chaque_dossier():
    dossiers = {
        "TEST-A": _dossier("TEST-A", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
            _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF99"}),
        ]),
        "TEST-B": _dossier("TEST-B", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
            _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF01", "libelle": "adoptée"}),
        ]),
    }
    zip_bytes = _make_zip(dossiers)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        result = collect_dossiers_gouvernementaux(zf)

    assert len(result["warnings"]) == 1
    assert "TEST-A" in result["warnings"][0]


def test_tous_les_statuts_connus_appartiennent_a_la_nomenclature_fermee():
    dossiers = {
        "TEST-A": _dossier("TEST-A", "Projet de loi ordinaire test", [
            _acte("AN1-DEPOT", "2024-01-10"),
            _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF01", "libelle": "adoptée"}),
        ]),
    }
    zip_bytes = _make_zip(dossiers)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        result = collect_dossiers_gouvernementaux(zf)

    for record in result["dossiers"]:
        if record["statut"] is not None:
            assert record["statut"] in KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL


# ---------------------------------------------------------------------------
# ensure_dossiers_zip_downloaded / fetch_dossiers_gouvernementaux
# ---------------------------------------------------------------------------

class DummyStreamResponse:
    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size: int = 1024 * 1024):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start:start + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_ensure_dossiers_zip_downloaded_downloads_once_then_reuses_cache(tmp_path):
    zip_bytes = _make_zip({"TEST": _dossier("TEST", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])})
    cache_dir = tmp_path / "cache"

    with patch("gouvernement_textes.DOSSIERS_CACHE_DIR", cache_dir), \
         patch("gouvernement_textes.requests.get", return_value=DummyStreamResponse(zip_bytes)) as mock_get:
        first = ensure_dossiers_zip_downloaded()
        second = ensure_dossiers_zip_downloaded()

    assert first == second == cache_dir / "dossiers.zip"
    assert first.is_file()
    assert mock_get.call_count == 1


def test_ensure_dossiers_zip_downloaded_returns_none_on_http_error_and_leaves_no_partial_file(tmp_path):
    cache_dir = tmp_path / "cache"

    with patch("gouvernement_textes.DOSSIERS_CACHE_DIR", cache_dir), \
         patch("gouvernement_textes.requests.get", return_value=DummyStreamResponse(b"", status_code=404)):
        result = ensure_dossiers_zip_downloaded()

    assert result is None
    assert not (cache_dir / "dossiers.zip").exists()
    assert not (cache_dir / "dossiers.zip.part").exists()


def test_fetch_dossiers_gouvernementaux_returns_warning_when_download_fails():
    with patch("gouvernement_textes.ensure_dossiers_zip_downloaded", return_value=None):
        result = fetch_dossiers_gouvernementaux()

    assert result["dossiers"] == []
    assert len(result["warnings"]) == 1


def test_fetch_dossiers_gouvernementaux_delegates_to_collect(tmp_path):
    zip_bytes = _make_zip({"TEST": _dossier("TEST", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])})
    zip_path = tmp_path / "dossiers.zip"
    zip_path.write_bytes(zip_bytes)

    with patch("gouvernement_textes.ensure_dossiers_zip_downloaded", return_value=zip_path):
        result = fetch_dossiers_gouvernementaux()

    assert [d["dossier_id"] for d in result["dossiers"]] == ["TEST"]


# ---------------------------------------------------------------------------
# Origine : signal document (#400)
# ---------------------------------------------------------------------------

def test_origine_titre_descriptif_reconnue_par_le_document():
    """Cas central de #400 : sur la XV les titres sont descriptifs. Le filtre
    par préfixe de titre y retenait ZÉRO projet de loi déposé entre 2017 et
    2019. C'est le document déposé (PRJL) qui porte l'origine.

    Cas réel : « Taxe sur les services numériques […] (taxe GAFA) ».
    """
    dossier = _dossier(
        "DLR5L15N38010",
        "Taxe sur les services numériques et impôt sur les sociétés (taxe GAFA)",
        [_acte("AN1-DEPOT", "2019-03-06", texte_associe="PRJLANR5L15B1737")],
        legislature="15",
    )
    record = parse_dossier_gouvernemental(dossier)
    assert record is not None, "un titre descriptif ne doit plus exclure le dossier"
    assert record["statut"] == "depose"


def test_origine_document_pion_exclue_malgre_titre_ambigu():
    dossier = _dossier(
        "TEST-PION", "Démocratie plus représentative",
        [_acte("AN1-DEPOT", "2018-05-09", texte_associe="PIONANR5L15B0911")],
        legislature="15",
    )
    assert parse_dossier_gouvernemental(dossier) is None


def test_origine_document_pnre_resolution_exclue():
    """PNRE = proposition de résolution : ni gouvernemental, ni parlementaire
    au sens des textes de loi."""
    dossier = _dossier(
        "TEST-PNRE", "Résolution sur un sujet quelconque",
        [_acte("AN1-DEPOT", "2024-01-10", texte_associe="PNREANR5L17B0123")],
    )
    assert parse_dossier_gouvernemental(dossier) is None


def test_origine_document_prime_sur_la_procedure_contradictoire():
    """8 dossiers de règlement du budget sont typés « Proposition de loi
    ordinaire » (code 2) à la source alors que le document déposé est un PRJL.
    Le document réellement déposé fait foi.

    Cas réel : « Règlement du budget 2016 » (DLR5L15N35837).
    """
    dossier = _dossier(
        "DLR5L15N35837", "Règlement du budget 2016",
        [_acte("AN1-DEPOT", "2017-06-28", texte_associe="PRJLANR5L15B0005")],
        legislature="15", procedure_code="2",
    )
    record = parse_dossier_gouvernemental(dossier)
    assert record is not None
    assert record["dossier_id"] == "DLR5L15N35837"


def test_origine_repli_sur_procedure_quand_aucun_document():
    """Sans document de dépôt résolvable, la procédure sert de repli — mais
    seulement pour les codes dont l'origine est univoque."""
    gouvernemental = _dossier(
        "TEST-REPLI-G", "Un intitulé descriptif", [_acte("AN1-DEBATS-DEC", "2024-03-01")],
        procedure_code="1",  # Projet de loi ordinaire
    )
    assert parse_dossier_gouvernemental(gouvernemental) is not None

    parlementaire = _dossier(
        "TEST-REPLI-P", "Un intitulé descriptif", [_acte("AN1-DEBATS-DEC", "2024-03-01")],
        procedure_code="2",  # Proposition de loi ordinaire
    )
    assert parse_dossier_gouvernemental(parlementaire) is None


def test_origine_procedure_ambigue_jamais_devinee():
    """Codes 5 et 7 (« Projet OU proposition de loi organique/constitutionnelle ») :
    le libellé ne tranche pas. Sans document, le dossier est exclu plutôt que
    classé par défaut (AGENTS.md §2.5)."""
    for code in ("5", "7"):
        dossier = _dossier(
            f"TEST-AMBIGU-{code}", "Un intitulé descriptif",
            [_acte("AN1-DEBATS-DEC", "2024-03-01")], procedure_code=code,
        )
        assert parse_dossier_gouvernemental(dossier) is None, f"code {code} deviné"


# ---------------------------------------------------------------------------
# Multi-archives : déduplication par uid (#400)
# ---------------------------------------------------------------------------

def _ecrire_zip(tmp_path, nom, dossiers):
    chemin = tmp_path / nom
    chemin.write_bytes(_make_zip(dossiers))
    return chemin


def test_multi_archives_dedupliqué_par_uid(tmp_path):
    """Un dossier présent dans deux archives ne doit apparaître qu'une fois :
    sans déduplication il serait compté deux fois dans textes[] et dans les
    textes portés de chaque acteur."""
    commun = _dossier("DLR-COMMUN", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
    ])
    a16 = _ecrire_zip(tmp_path, "d16.zip", {"DLR-COMMUN": commun, "DLR-16": _dossier(
        "DLR-16", "Projet de loi ordinaire seize", [_acte("AN1-DEPOT", "2023-01-10")])})
    a17 = _ecrire_zip(tmp_path, "d17.zip", {"DLR-COMMUN": commun, "DLR-17": _dossier(
        "DLR-17", "Projet de loi ordinaire dix-sept", [_acte("AN1-DEPOT", "2025-01-10")])})

    resultat = collect_dossiers_gouvernementaux_multi([(16, a16), (17, a17)])
    ids = [d["dossier_id"] for d in resultat["dossiers"]]

    assert sorted(ids) == ["DLR-16", "DLR-17", "DLR-COMMUN"]
    assert len(ids) == len(set(ids)), "aucun doublon inter-archives"


def test_multi_archives_la_legislature_la_plus_elevee_fait_foi(tmp_path):
    """L'archive la plus récente porte l'état le plus à jour des actes, donc du
    statut. Lire d'abord la plus ancienne figerait un statut périmé : un texte
    « en navette » dans la XVI peut être « adopté » dans la XVII."""
    en_navette = _dossier("DLR-X", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("SN1-DEBATS-DEC", "2024-04-01", {"fam_code": "TSORTF05", "libelle": "modifié"}),
    ])
    adopte = _dossier("DLR-X", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("SN1-DEBATS-DEC", "2024-04-01", {"fam_code": "TSORTF05", "libelle": "modifié"}),
        _acte("AN1-DEBATS-DEC", "2025-06-01", {"fam_code": "TSORTF01", "libelle": "adoptée"}),
    ])
    a16 = _ecrire_zip(tmp_path, "d16.zip", {"DLR-X": en_navette})
    a17 = _ecrire_zip(tmp_path, "d17.zip", {"DLR-X": adopte})

    resultat = collect_dossiers_gouvernementaux_multi([(16, a16), (17, a17)])
    assert [d["statut"] for d in resultat["dossiers"]] == ["adopte"]

    # Ordre d'appel inversé : le résultat ne doit pas en dépendre.
    resultat_inverse = collect_dossiers_gouvernementaux_multi([(17, a17), (16, a16)])
    assert [d["statut"] for d in resultat_inverse["dossiers"]] == ["adopte"]


def test_multi_archives_archive_illisible_nempeche_pas_les_autres(tmp_path):
    valide = _ecrire_zip(tmp_path, "ok.zip", {"DLR-OK": _dossier(
        "DLR-OK", "Projet de loi ordinaire test", [_acte("AN1-DEPOT", "2024-01-10")])})
    corrompue = tmp_path / "ko.zip"
    corrompue.write_bytes(b"ceci n'est pas un zip")

    resultat = collect_dossiers_gouvernementaux_multi([(16, corrompue), (17, valide)])
    assert [d["dossier_id"] for d in resultat["dossiers"]] == ["DLR-OK"]


def test_fetch_signale_une_archive_manquante(tmp_path):
    """Une archive absente réduit la couverture : cela doit être signalé, pas
    se lire comme « ce gouvernement n'a porté aucun texte » (§2.8)."""
    valide = _ecrire_zip(tmp_path, "ok.zip", {"DLR-OK": _dossier(
        "DLR-OK", "Projet de loi ordinaire test", [_acte("AN1-DEPOT", "2024-01-10")])})

    with patch("gouvernement_textes.ensure_dossiers_zips_downloaded",
               return_value=[(17, valide)]):
        resultat = fetch_dossiers_gouvernementaux()

    assert [d["dossier_id"] for d in resultat["dossiers"]] == ["DLR-OK"]
    assert any("indisponible" in w for w in resultat["warnings"])
    assert any("15" in w and "16" in w for w in resultat["warnings"])


# ---------------------------------------------------------------------------
# Promulgation (#400)
# ---------------------------------------------------------------------------

def test_promulgation_corrige_une_navette_factuellement_fausse():
    """Cas réel DLR5L15N38367 : dernière décision de séance « modifié » au
    Sénat le 2021-01-28, donc `navette_en_cours` — mais le texte a été
    promulgué le 2021-02-03. Publier « en navette » en 2026 serait faux."""
    dossier = _dossier("DLR5L15N38367", "Convention relative aux infractions à bord des aéronefs", [
        # Titre descriptif + document PRJL : le cas typique de la XV.
        _acte("AN1-DEPOT", "2019-11-27", texte_associe="PRJLANR5L15B2451"),
        _acte("AN1-DEBATS-DEC", "2020-12-10", {"fam_code": "TSORTF01", "libelle": "adopté"}),
        _acte("SN1-DEBATS-DEC", "2021-01-28", {"fam_code": "TSORTF05", "libelle": "modifié"}),
        _acte("PROM-PUB", "2021-02-03"),
    ], legislature="15")
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "promulgue"
    assert record["sort_49_3"] is False


def test_promulgation_corrige_un_rejet_infirme_ensuite():
    dossier = _dossier("TEST-PROM-REJET", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2019-01-10"),
        _acte("AN1-DEBATS-DEC", "2019-03-01", {"fam_code": "TSORTF07", "libelle": "rejetée"}),
        _acte("PROM", "2019-08-01"),
    ])
    assert parse_dossier_gouvernemental(dossier)["statut"] == "promulgue"


def test_promulgation_necrase_jamais_adopte_cmp_ni_49_3():
    """Point sensible §2.4 : `promulgue` ne dit pas PAR QUELLE VOIE le texte a
    été adopté. L'écrasement ferait disparaître le fait CMP ou 49.3."""
    cmp_ = _dossier("TEST-PROM-CMP", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-10-10"),
        _acte("AN1-DEBATS-DEC", "2025-02-06", {"fam_code": "TSORTF18", "libelle": "art. 45 al. 3"}),
        _acte("PROM-PUB", "2025-02-15"),
    ])
    assert parse_dossier_gouvernemental(cmp_)["statut"] == "adopte_cmp"

    art49 = _dossier("TEST-PROM-493", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-10-10"),
        _acte("AN1-DEBATS-DEC", "2024-12-04", {"fam_code": "TSORTF06", "libelle": "49 al. 3"}),
        _acte("PROM-PUB", "2024-12-20"),
    ])
    record = parse_dossier_gouvernemental(art49)
    assert record["statut"] == "adopte_49_3"
    assert record["sort_49_3"] is True


def test_promulgation_necrase_pas_un_retrait():
    """Retrait + promulgation serait contradictoire : ne pas trancher."""
    dossier = _dossier("TEST-PROM-RETIRE", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-RTRINI", "2024-05-01"),
        _acte("PROM-PUB", "2024-06-01"),
    ])
    assert parse_dossier_gouvernemental(dossier)["statut"] == "retire"


def test_promulgation_conserve_le_warning_fam_code_inconnu():
    """Le statut devient connu, mais le fam_code reste non mappé : le signal
    doit rester visible pour un mapping futur."""
    dossier = _dossier("TEST-PROM-INCONNU", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-DEBATS-DEC", "2024-03-01", {"fam_code": "TSORTF99", "libelle": "?"}),
        _acte("PROM-PUB", "2024-06-01"),
    ])
    record = parse_dossier_gouvernemental(dossier)
    assert record["statut"] == "promulgue"
    assert len(record["warnings"]) == 1
    assert "TSORTF99" in record["warnings"][0]


def test_promulgation_sans_decision_de_seance():
    dossier = _dossier("TEST-PROM-SEUL", "Projet de loi ordinaire test", [
        _acte("AN1-DEPOT", "2024-01-10"),
        _acte("AN1-COM-FOND-RAPPORT", "2024-02-01"),
        _acte("PROM-PUB", "2024-06-01"),
    ])
    assert parse_dossier_gouvernemental(dossier)["statut"] == "promulgue"
