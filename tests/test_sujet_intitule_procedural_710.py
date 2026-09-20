"""Un créneau de séance n'est pas un sujet — critère STRUCTUREL (#710).

`AGENTS.md` §3e : « ce qui sépare un sujet d'un intitulé procédural est
structurel, pas lexical (le `code_grammaire` du point) ». La règle tenait pour
les points d'article et de procédure (#510) mais pas pour le point d'ORDRE DU
JOUR : `TITRE_TEXTE_DISCUSSION` désigne tantôt un texte — « Droit à l'aide à
mourir » — tantôt un créneau — « Questions au Premier ministre ».

Mesuré le 02/09/2026 sur les 481 profils publiés à `c13c99f2` : 69 d'entre eux
portaient le tag « questions au premier ministre », et la fiche `AN:LR` le
publiait au 32e rang de son empreinte thématique.

Toute mesure se prend sur des RÉDUCTIONS VERBATIM de l'archive réelle. Aucune
fixture inventée : #510 a supprimé les deux qui existaient plutôt que de les
déprécier, parce que les garder sous test gardait la cause armée.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import parse_syceron
from merge_profile import (
    CHAMPS_SUJET_INTERVENTION,
    CLE_PREUVE_SUJET,
    _entree_syceron_publiee,
    backfill_sujet_seance,
    merge_pivot_profile,
    merge_raw_profile,
)
from parse_syceron import parse_syceron_xml
from schema_pivot import deriver_tags_thematiques

FIXTURES = Path(__file__).resolve().parent / "fixtures"

#: Réduction verbatim de CRSANR5L16S2024O1N228 : un créneau « Questions au
#: Premier ministre », un QPM_1_1 « Parcoursup », et en contrôle un texte en
#: discussion sous lequel aucun point de question n'est rangé.
CRENEAU = "syceron_reel_leg16_creneau_questions.xml"
#: Réduction verbatim de CRSANR5L17S2026O1N187 : un créneau « Questions au
#: gouvernement » avec ses QG_1_1.
STRUCTURE = "syceron_reel_leg17_structure.xml"


def _parse(nom: str) -> dict:
    return parse_syceron_xml((FIXTURES / nom).read_bytes())


@pytest.fixture(scope="module")
def creneau():
    return _parse(CRENEAU)


@pytest.fixture(scope="module")
def structure():
    return _parse(STRUCTURE)


# ---------------------------------------------------------------------------
# 1. Le critère : un créneau de questions ne fournit jamais de sujet
# ---------------------------------------------------------------------------

def test_le_titre_du_creneau_de_questions_nest_jamais_un_sujet(creneau):
    """`sujet: None`, et rien d'autre — surtout pas une valeur de repli.

    Le paragraphe visé est l'appel de l'ordre du jour par la présidence, porté
    par le point d'ordre du jour lui-même. Son titre reste lisible dans
    `point_ordre_du_jour`, qui est du contexte, pas un thème (§2 règles 5 et 8).
    """
    portes_par_le_creneau = [
        i for i in creneau["interventions"]
        if i["point_code_grammaire"] == "TITRE_TEXTE_DISCUSSION"
    ]
    assert portes_par_le_creneau, "la réduction porte l'appel de l'ordre du jour"
    for i in portes_par_le_creneau:
        assert i["sujet"] is None
        assert i["sujet_code_grammaire"] is None
        assert i["point_ordre_du_jour"] == "Questions au Premier ministre"


def test_le_creneau_qg_de_la_dix_septieme_est_traite_pareil(structure):
    """Même verdict sur une autre législature et une autre grammaire (`QG_1_1`).

    Cette entrée sortait avec `sujet: "Questions au gouvernement"` avant #710 :
    la fixture de #510 portait déjà le défaut, personne ne le regardait.
    """
    appel = structure["interventions"][0]
    assert appel["point_ordre_du_jour"] == "Questions au gouvernement"
    assert appel["sujet"] is None
    assert appel["sujet_code_grammaire"] is None


def test_le_sujet_dune_question_est_celui_de_la_question(creneau):
    """`QPM_1_1` porte « Parcoursup », pas « Questions au Premier ministre ».

    Le code manquait au vocabulaire du parseur : 629 paragraphes des
    législatures 16 et 17 héritaient donc du titre du créneau, dont 179 déjà
    publiés.
    """
    parcoursup = [i for i in creneau["interventions"] if i["sujet"] == "Parcoursup"]
    assert parcoursup
    for i in parcoursup:
        assert i["sujet_code_grammaire"] == "QPM_1_1"
        assert i["type_detail"] == "question_gouvernement"


def test_le_critere_est_positif_un_texte_garde_son_titre(creneau):
    """Un point d'ordre du jour sous lequel AUCUNE question n'est rangée garde
    son titre pour sujet — sinon la correction viderait le corpus.

    C'est la moitié qu'un filtre trop large casserait, et c'est aussi ce qui
    montre que le critère ne rend pas un code inconnu procédural par défaut :
    il faut, POSITIVEMENT, que la source range des points de question dessous.
    """
    texte = [
        i for i in creneau["interventions"]
        if i["sujet"] == "Accroître le financement des entreprises et l’attractivité de la France"
    ]
    assert texte
    for i in texte:
        assert i["sujet_code_grammaire"] == "TITRE_TEXTE_DISCUSSION"


# ---------------------------------------------------------------------------
# 2. Le critère ne lit AUCUN libellé
# ---------------------------------------------------------------------------

def test_le_verdict_ne_depend_pas_du_libelle_du_creneau():
    """Le piège de #672 et #639, sous test.

    La source publie « Questions au gouvernement », « Questions au
    Gouvernement », « Questions au premier ministre » et « Questions au
    Gouvernement (suite) » — quatre variantes du même créneau sur les seules
    législatures 16 et 17. On remplace ici le libellé par une chaîne qui ne
    ressemble à rien : le verdict doit être le même, parce qu'il ne vient pas de
    là. Une liste de libellés, même exhaustive, ferait échouer ce test.
    """
    brut = (FIXTURES / CRENEAU).read_text(encoding="utf-8")
    renomme = brut.replace(
        "<texte>Questions au Premier ministre</texte>",
        "<texte>ZZZ libellé sans rapport</texte>",
    )
    assert renomme != brut, "le libellé est bien dans la réduction"

    parsed = parse_syceron_xml(renomme.encode("utf-8"))
    appel = [
        i for i in parsed["interventions"]
        if i["point_code_grammaire"] == "TITRE_TEXTE_DISCUSSION"
    ]
    assert appel
    for i in appel:
        assert i["sujet"] is None
    assert any(i["sujet"] == "Parcoursup" for i in parsed["interventions"])


def test_un_point_dordre_du_jour_sans_question_dessous_nest_pas_un_creneau(creneau):
    """`_creneaux_de_questions` ne retient QUE ce que la source range.

    Un `code_grammaire` absent ou inconnu ne devient pas procédural par défaut :
    il ne rend le point ni porteur de sujet ni créneau.
    """
    import xml.etree.ElementTree as ET

    racine = ET.fromstring((FIXTURES / CRENEAU).read_bytes())
    contenu = racine.find(parse_syceron._tag("contenu"))
    creneaux = parse_syceron._creneaux_de_questions(contenu)
    assert len(creneaux) == 1, "un seul des deux points d'ordre du jour est un créneau"


# ---------------------------------------------------------------------------
# 3. Le report nommé : cinquième occurrence de #492 / #639 / #641 / #696
# ---------------------------------------------------------------------------

def _brut(sujet, code, marque_le_code=True):
    entree = {
        "id": "syceron_CR_000001",
        "url": "https://data.assemblee-nationale.fr/x.zip",
        "sujet": sujet,
        "session_ref": "SCR5A2024O1",
    }
    if marque_le_code:
        entree[CLE_PREUVE_SUJET] = code
    return entree


def test_sans_report_la_fusion_additive_garde_le_creneau():
    """L'entrée ancienne gagne : c'est la mécanique, pas un accident.

    Ce test mesure le trou lui-même, pour que le report ait quelque chose à
    corriger. `merge_lists_by_key` est additif pur et la clé repose sur `id`,
    que la correction ne touche pas.
    """
    from merge_profile import _intervention_key, merge_lists_by_key

    fusionne = merge_lists_by_key(
        [_brut("Questions au Premier ministre", None, marque_le_code=False)],
        [_brut("Parcoursup", "QPM_1_1")],
        _intervention_key,
    )
    assert fusionne[0]["sujet"] == "Questions au Premier ministre"


def test_le_report_corrige_lentree_deja_collectee():
    ancien = {
        "interventions": [_brut("Questions au Premier ministre", None, marque_le_code=False)]
    }
    neuf = {"interventions": [_brut("Parcoursup", "QPM_1_1")]}

    fusionne = merge_raw_profile(ancien, neuf)

    assert len(fusionne["interventions"]) == 1
    assert fusionne["interventions"][0]["sujet"] == "Parcoursup"
    assert fusionne["interventions"][0][CLE_PREUVE_SUJET] == "QPM_1_1"


def test_le_report_sait_retirer_un_sujet_et_pas_seulement_en_poser():
    """La différence avec les quatre reports précédents, et elle est déclarée.

    #492, #639, #641 et #696 ne remplissaient qu'un champ absent. Celui-ci
    RETIRE une valeur — 282 des 765 interventions publiées qu'il corrige sur les
    législatures 16 et 17. C'est une perte sur `tags_thematiques`, liste
    surveillée bloquante : elle se déclare par `allow_declared_losses`.
    """
    ancien = {
        "interventions": [_brut("Questions au gouvernement", None, marque_le_code=False)]
    }
    neuf = {"interventions": [_brut(None, None)]}

    fusionne = merge_raw_profile(ancien, neuf)

    assert fusionne["interventions"][0]["sujet"] is None


def test_le_report_ne_touche_pas_une_entree_sans_preuve():
    """Le critère est sourcé : sans la clé du parseur corrigé, rien ne bouge.

    Une entrée neuve venue d'un autre chemin de collecte — questions de l'open
    data AN, entrées héritées de NosDéputés — ne la porte pas.
    """
    ancien = {
        "interventions": [_brut("Questions au gouvernement", None, marque_le_code=False)]
    }
    neuf = {"interventions": [_brut(None, None, marque_le_code=False)]}

    fusionne = merge_raw_profile(ancien, neuf)

    assert fusionne["interventions"][0]["sujet"] == "Questions au gouvernement"


def test_le_report_ne_touche_pas_une_entree_que_le_run_ne_recollecte_pas():
    """Ce que le report ne peut pas faire, et qu'il ne prétend pas faire :
    une législature non rejouée garde son sujet de créneau (§2 règle 5)."""
    ancien = {
        "interventions": [_brut("Questions au gouvernement", None, marque_le_code=False)]
    }
    fusionne = merge_raw_profile(ancien, {"interventions": []})
    assert fusionne["interventions"][0]["sujet"] == "Questions au gouvernement"


def test_le_report_ne_touche_pas_la_cle_de_fusion():
    """Ce qui le distingue du défaut de #668 : la clé ne change pas de branche."""
    from merge_profile import _intervention_key

    ancienne = _brut("Questions au Premier ministre", None, marque_le_code=False)
    reporte = backfill_sujet_seance(
        [dict(ancienne)],
        [_brut("Parcoursup", "QPM_1_1")],
        _intervention_key,
        preuve=lambda i: CLE_PREUVE_SUJET in i,
    )[0]
    assert _intervention_key(reporte) == _intervention_key(ancienne)


def test_la_preuve_du_pivot_est_la_source_publiee():
    """Au pivot, la preuve est `source.type == "syceron"` — déjà publiée sur les
    deux formes d'entrée, y compris celle réduite au thème (#657). Republier le
    code de point coûterait le budget que #657 est allé chercher."""
    assert _entree_syceron_publiee({"source": {"type": "syceron"}})
    assert not _entree_syceron_publiee({"source": {"type": "assemblee_nationale"}})
    assert not _entree_syceron_publiee({"source": None})


def test_le_report_pivot_corrige_sujet_et_theme_officiel():
    ancien = {
        "interventions": [{
            "intervention_id": "syceron_CR_000001",
            "sujet": "Questions au Premier ministre",
            "theme_officiel": "Questions au Premier ministre",
            "source": {"type": "syceron"},
        }],
        "tags_thematiques": ["questions au premier ministre"],
    }
    neuf = {
        "interventions": [{
            "intervention_id": "syceron_CR_000001",
            "sujet": "Parcoursup",
            "theme_officiel": "Parcoursup",
            "source": {"type": "syceron"},
        }],
        "tags_thematiques": ["parcoursup"],
    }

    fusionne = merge_pivot_profile(ancien, neuf)

    assert len(fusionne["interventions"]) == 1
    assert fusionne["interventions"][0]["sujet"] == "Parcoursup"
    assert fusionne["interventions"][0]["theme_officiel"] == "Parcoursup"


def test_le_report_pivot_ne_pose_pas_un_sujet_absent_sur_une_entree_complete():
    """Une entrée pivot réduite au thème (#657) n'a pas de clé `sujet` : le
    report ne doit reporter que les champs que l'entrée neuve PORTE, sinon il
    effacerait le sujet de l'entrée complète qu'elle remplace."""
    ancien = {
        "interventions": [{
            "intervention_id": "i1",
            "sujet": "Parcoursup",
            "theme_officiel": "Parcoursup",
            "source": {"type": "syceron"},
        }],
    }
    neuf = {
        "interventions": [{
            "intervention_id": "i1",
            "theme_officiel": "Parcoursup",
            "collecte": "theme_seul",
            "source": {"type": "syceron"},
        }],
    }

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["interventions"][0]["sujet"] == "Parcoursup"


def test_les_champs_reportes_sont_nommes():
    """Reporter tout ce qui manque ferait de la fusion additive une fusion champ
    par champ, ce qu'elle n'est pas (#492)."""
    assert CHAMPS_SUJET_INTERVENTION == ("sujet", "theme_officiel", "sujet_code_grammaire")


# ---------------------------------------------------------------------------
# 4. `tags_thematiques` est DÉRIVÉ, plus uni
# ---------------------------------------------------------------------------

def test_les_tags_se_recalculent_apres_la_fusion_pivot():
    """L'autre moitié du défaut, et sans elle la correction n'arrive nulle part.

    `merge_pivot_profile` unissait l'ancienne liste et la neuve : un tag publié
    une fois y restait pour toujours, quelle que soit la correction apportée aux
    interventions dont il dérive.
    """
    ancien = {
        "interventions": [{
            "intervention_id": "syceron_CR_000001",
            "theme_officiel": "Questions au Premier ministre",
            "source": {"type": "syceron"},
        }],
        "tags_thematiques": ["questions au premier ministre"],
    }
    neuf = {
        "interventions": [{
            "intervention_id": "syceron_CR_000001",
            "theme_officiel": "Parcoursup",
            "source": {"type": "syceron"},
        }],
        "tags_thematiques": ["parcoursup"],
    }

    fusionne = merge_pivot_profile(ancien, neuf)

    assert fusionne["tags_thematiques"] == ["parcoursup"]


def test_un_run_sans_interventions_ne_perd_aucun_tag():
    """La fusion des interventions est additive : un run qui n'en collecte
    aucune (`--skip-interventions`) laisse la liste fusionnée égale à l'ancienne,
    donc les tags aussi. Le recalcul ne peut pas vider un profil tout seul."""
    ancien = {
        "interventions": [{"intervention_id": "i1", "theme_officiel": "Parcoursup"}],
        "tags_thematiques": ["parcoursup"],
    }
    fusionne = merge_pivot_profile(ancien, {"interventions": [], "tags_thematiques": []})
    assert fusionne["tags_thematiques"] == ["parcoursup"]


def test_le_repli_sur_mots_cles_survit_a_la_derivation():
    """#529 : plus rien ne collecte `mots_cles`, mais 647 tags publiés en
    dérivent, et `tags_thematiques` est une liste surveillée bloquante."""
    assert deriver_tags_thematiques(
        [{"theme_officiel": None, "mots_cles": ["Budget", "  fiscalité  "]}]
    ) == ["budget", "fiscalité"]
