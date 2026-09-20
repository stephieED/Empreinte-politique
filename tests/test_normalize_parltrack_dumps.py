"""
tests/test_normalize_parltrack_dumps.py — Tests unitaires pour
normalize_parltrack_dumps.py.

Tests du mapping ParlTrack → schéma pivot v1 (textes_portes, amendements)
et de la fusion additive.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from normalize_parltrack_dumps import (
    WARNING_PREFIX_PARLTRACK_EXPLICATIONS_SANS_LIEN,
    WARNING_PREFIX_PARLTRACK_VOTES_ECARTES,
    _date_plausible,
    _make_intervention,
    _make_vote,
    _nature_scrutin,
    _porte_sur_ensemble,
    _make_amendement,
    _make_texte_porte,
    _role_signataire,
    enrich_pivot_with_parltrack,
)
from schema_pivot import make_empty_profil, validate_profil


@pytest.fixture(autouse=True)
def _sans_votes_ni_activites():
    """Les deux lectures ajoutées par #683 sont muettes par défaut.

    Sans ce garde, un test écrit pour les amendements sortirait sur le réseau
    pour aller chercher `ep_votes.json.zst` — et un test qui ne demande pas les
    votes européens ne doit pas en recevoir. Ceux qui les veulent doublent
    explicitement les deux fonctions.
    """
    with patch("normalize_parltrack_dumps.get_votes_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_activities_for_mep", return_value={}):
        yield


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _dossier(reference="2024/0001(COD)", titre="Titre test", comite="AFET", date="2024-03-15"):
    return {
        "reference": reference,
        "titre": titre,
        "comite": comite,
        "role": "rapporteur",
        "date": date,
        "source_url": f"https://parltrack.org/dossier/{reference}",
    }


def _amendment(amd_id="A9-0052/2023-1", reference="2020/2202(INI)", date="2023-05-10"):
    return {
        "id": amd_id,
        "reference": reference,
        "comite": None,
        "date": date,
        "source": "plenary",
        "source_url": f"https://parltrack.org/amendments/{amd_id}",
    }


def _empty_pivot():
    p = make_empty_profil("parltrack:131580", "Jordan Bardella")
    # #493 : `chambre` vaut `chambres[0]` — les deux se posent ensemble.
    p["chambres"] = ["PE"]
    p["chambre"] = "PE"
    return p


# ---------------------------------------------------------------------------
# Tests : _make_texte_porte
# ---------------------------------------------------------------------------


def test_make_texte_porte_fields():
    d = _dossier()
    tp = _make_texte_porte(d)
    assert tp["role"] == "rapporteur"
    assert tp["titre"] == "Titre test"
    assert tp["date_min"] == "2024-03-15"
    assert tp["source_url"].startswith("https://parltrack.org/dossier/")
    # #747 — l'assertion inverse jusqu'ici (« sort n'appartient pas aux
    # textes_portes ») datait d'avant #743, qui a fait du sort un champ du
    # texte porté. Le dump ParlTrack n'en porte aucun : l'entrée le DIT, au
    # lieu de publier une absence sans cause.
    assert tp["sort"] is None
    assert tp["sort_non_resolu"] == {"motif": "source_sans_sort"}
    # Champs obligatoires du schéma
    assert "stade_procedural" in tp
    assert "legislature" in tp
    assert "type_rapport" in tp


def test_make_texte_porte_missing_titre_falls_back_to_reference():
    d = _dossier(titre="", reference="2024/0042(COD)")
    tp = _make_texte_porte(d)
    assert tp["titre"] == "2024/0042(COD)"


# ---------------------------------------------------------------------------
# Tests : _make_amendement
# ---------------------------------------------------------------------------


def test_make_amendement_fields():
    """#431 : un amendement PE n'a pas d'`uid` AN, donc pas d'identifiant dans
    l'index partagé — il garde son enregistrement complet, jamais une clé
    inventée (AGENTS.md §2.5)."""
    a = _amendment()
    amd = _make_amendement(a)
    assert amd["amendement_id"] is None
    # La fixture ne porte ni `nb_signataires` ni `authors` : la source ne dit
    # rien du rôle, donc le pivot n'en dit rien non plus (#683).
    assert amd["role_signataire"] is None
    non_resolu = amd["amendement_non_resolu"]
    assert non_resolu["texte_vise"] == "2020/2202(INI)"
    assert non_resolu["sort"] is None  # ParlTrack ne fournit pas de sort fiable
    assert non_resolu["numero"] == "A9-0052/2023-1"
    assert non_resolu["source_url"].startswith("https://parltrack.org/")
    assert non_resolu["co_signataires"] == []
    assert non_resolu["base_juridique_irrecevabilite"] is None


# ---------------------------------------------------------------------------
# Tests : _role_signataire — quatre cas, dont un qui se tait (#683)
# ---------------------------------------------------------------------------


def test_un_seul_signataire_est_lauteur_principal():
    """S'il n'y en a qu'un, c'est lui — aucun nom à comparer."""
    assert _role_signataire({"nb_signataires": 1}, "Jordan BARDELLA") == "auteur_principal"


def test_le_nom_en_tete_est_celui_du_profil():
    a = {"nb_signataires": 30, "premier_auteur": "Jordan Bardella"}
    assert _role_signataire(a, "Jordan BARDELLA") == "auteur_principal"


def test_ordre_et_casse_et_accents_ne_changent_pas_le_rôle():
    """ParlTrack écrit « France Jamet », le pivot « Jean-Luc MÉLENCHON »."""
    a = {"nb_signataires": 12, "premier_auteur": "Mélenchon Jean-luc"}
    assert _role_signataire(a, "Jean-Luc MELENCHON") == "auteur_principal"


def test_un_autre_nom_en_tete_fait_un_cosignataire():
    a = {"nb_signataires": 30, "premier_auteur": "France Jamet"}
    assert _role_signataire(a, "Jordan BARDELLA") == "cosignataire"


def test_sans_nom_en_tete_le_role_reste_nul():
    """La source se tait : le pivot se tait aussi.

    91 % des amendements vérifiables mettent en tête de `meps` le premier des
    `authors` — assez pour tenter la déduction, beaucoup trop peu pour la
    publier comme un fait (§2 règle 2).
    """
    assert _role_signataire({"nb_signataires": 4, "premier_auteur": None}, "Marine LE PEN") is None
    assert _role_signataire({"nb_signataires": 4}, "Marine LE PEN") is None


# ---------------------------------------------------------------------------
# Tests : _date_plausible — 44 dates impossibles dans le corpus réel (#683)
# ---------------------------------------------------------------------------


def test_une_date_normale_passe_telle_quelle():
    assert _date_plausible("2023-06-07T00:00:00") == ("2023-06-07", None)


def test_une_annee_impossible_est_ecartee_et_conservee():
    """`PE650.371-2` porte réellement « 0302-01-01 » dans le dump publié."""
    assert _date_plausible("0302-01-01T00:00:00") == (None, "0302-01-01T00:00:00")
    assert _date_plausible("2068-01-03T00:00:00") == (None, "2068-01-03T00:00:00")


def test_une_date_absente_nest_pas_une_date_ecartee():
    """Rien à écarter quand il n'y avait rien : les deux sorties sont nulles."""
    assert _date_plausible(None) == (None, None)
    assert _date_plausible("") == (None, None)


def test_la_date_ecartee_est_publiee_a_cote_de_son_motif():
    amd = _make_amendement({"id": "PE650.371-2", "date": "0302-01-01T00:00:00"})
    non_resolu = amd["amendement_non_resolu"]
    assert non_resolu["date"] is None
    assert non_resolu["date_non_resolue"] == {
        "motif": "date_hors_bornes",
        "valeur_source": "0302-01-01T00:00:00",
    }


def test_une_date_valable_ne_pose_aucun_motif():
    amd = _make_amendement({"id": "A9-1/2023", "date": "2023-05-10"})
    assert "date_non_resolue" not in amd["amendement_non_resolu"]


def test_make_amendement_missing_reference():
    a = _amendment(reference="")
    amd = _make_amendement(a)
    assert amd["amendement_non_resolu"]["texte_vise"] == ""


# ---------------------------------------------------------------------------
# Tests : enrich_pivot_with_parltrack
# ---------------------------------------------------------------------------


def test_enrich_adds_textes_portes(tmp_path):
    """Les textes portés sont ajoutés au profil pivot."""
    profil = _empty_pivot()
    dossiers = [_dossier("2024/0001(COD)", "Titre A"), _dossier("2024/0002(COD)", "Titre B")]
    amendments = []

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=dossiers), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=amendments):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    assert len(profil["textes_portes"]) == 2
    assert profil["textes_portes"][0]["role"] == "rapporteur"


def test_enrich_adds_amendements(tmp_path):
    """Les amendements sont ajoutés au profil pivot."""
    profil = _empty_pivot()
    dossiers = []
    amds = [_amendment("AMD-1"), _amendment("AMD-2"), _amendment("AMD-3")]

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=dossiers), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=amds):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    assert len(profil["amendements"]) == 3


def test_enrich_additive_no_duplicate(tmp_path):
    """La fusion additive ne duplique pas les entrées existantes."""
    profil = _empty_pivot()
    # Pré-charger un amendement existant
    profil["amendements"] = [{
        "texte_vise": "2020/2202(INI)",
        "sort": None,
        "base_juridique_irrecevabilite": None,
        "role_signataire": "auteur_principal",
        "premier_signataire": None,
        "co_signataires": [],
        "type_deposant": None,
        "date": "2023-05-10",
        "numero": "A9-0052/2023-1",
        "source_url": "https://parltrack.org/amendments/A9-0052/2023-1",
    }]

    amds = [_amendment("A9-0052/2023-1"), _amendment("A9-0053/2023-1")]  # 1er déjà présent

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=amds):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    # Seul le nouvel amendement est ajouté. L'entrée pré-chargée est à l'ancienne
    # forme (champs à la racine), la nouvelle à la forme #431 : la clé de fusion
    # doit les rapprocher malgré tout, sinon une régénération dupliquerait tout
    # l'existant le jour de la bascule.
    assert len(profil["amendements"]) == 2

    def _numero(a):
        return (a.get("amendement_non_resolu") or a).get("numero")

    numeros = {_numero(a) for a in profil["amendements"]}
    assert "A9-0052/2023-1" in numeros
    assert "A9-0053/2023-1" in numeros


def test_enrich_schema_valid_after_enrichment():
    """Le profil pivot reste valide après enrichissement."""
    profil = _empty_pivot()
    profil["sources"] = [{"type": "parltrack", "url": "https://parltrack.org/mep/131580",
                           "synchro_le": "2026-07-24T00:00:00"}]
    dossiers = [_dossier()]
    amds = [_amendment()]

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=dossiers), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=amds):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    errors = validate_profil(profil)
    assert errors == [], f"Erreurs de validation schéma : {errors}"


def test_enrich_adds_warning_when_no_data():
    """Un warning est ajouté si aucun dossier ni amendement n'est trouvé."""
    profil = _empty_pivot()

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=[]):
        enrich_pivot_with_parltrack(profil, mep_id=99999)

    warnings = profil["meta"]["warnings"]
    assert any("ParlTrack" in w for w in warnings)


def test_enrich_parltrack_source_added_once():
    """La source ParlTrack dumps n'est pas dupliquée si appelé deux fois."""
    profil = _empty_pivot()
    profil["sources"] = []
    dossiers = [_dossier()]
    amds = [_amendment()]

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=dossiers), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=amds):
        enrich_pivot_with_parltrack(profil, mep_id=131580)
        # Deuxième appel — les données sont déjà là (deduplication)
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    dumps_sources = [s for s in profil["sources"] if "dumps" in (s.get("url") or "")]
    assert len(dumps_sources) == 1


def test_enrich_licence_enriched():
    """La licence ParlTrack s'ajoute à celle que le profil portait déjà.

    Depuis #530 (lot 6), `meta.licence_donnees` est DÉRIVÉ de `sources[]` et
    non plus concaténé à la valeur en place : le profil doit donc porter sa
    source européenne, comme le fait `normalize_europarl` dans le pipeline
    réel. Ce que le test vérifie est inchangé — l'ODbL de ParlTrack **s'ajoute**
    à l'attribution existante au lieu de la remplacer, faute de quoi le partage
    à l'identique du versant européen serait annoncé seul.
    """
    profil = _empty_pivot()
    profil["sources"] = [
        {"type": "europarl", "url": "https://www.europarl.europa.eu/meps/fr/131580",
         "synchro_le": "2026-08-27T10:00:00+0000"},
    ]
    dossiers = [_dossier()]

    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=dossiers), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=[]):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    assert "ODbL" in profil["meta"]["licence_donnees"]
    assert "CC BY 4.0" in profil["meta"]["licence_donnees"]


# ---------------------------------------------------------------------------
# Les votes : ce qui se publie, et ce qui se compte (#683)
# ---------------------------------------------------------------------------


def _scrutin(titre, position="pour", voteid=1, date="2023-06-07", reference="2022/2060(INI)"):
    return {
        "scrutin_id": voteid, "titre": titre, "date": date, "position": position,
        "reference": reference, "groupe": "ID",
        "source_url": "https://www.europarl.europa.eu/…/RCV.xml",
    }


def test_les_natures_densemble_sont_reconnues():
    """Relevées sur les 44 648 scrutins du dump, pas devinées."""
    for titre in [
        "A9-0183/2023 - Marie Dupont - Résolution 07/06/2023 12:03:45.000",
        "A9-0005/2019 - John Howarth - Vote unique 18/09/2019 12:03:45.000",
        "B9-0014/2019 - Proposition de résolution",
        "A9-0052/2023 - Résolution législative",
        "A9-0052/2023 - Proposition de la Commission",
    ]:
        assert _porte_sur_ensemble(titre), titre


def test_un_vote_damendement_ou_de_paragraphe_nest_pas_un_vote_sur_le_texte():
    """93 % des intitulés sont de cette forme — c'est la raison d'être du tri."""
    for titre in [
        "RC-B9-0012/2019 - Am 1",
        "RC-B9-0014/2019 - § 13",
        "Mardi - demande du groupe GUE/NGL 15/07/2019 17:09:37.000",
        "A9-0183/2023 - Article 4",
    ]:
        assert not _porte_sur_ensemble(titre), titre


def test_un_vote_europeen_na_jamais_de_scrutin_id():
    """`scrutins_index.decomposer_id` refuse tout ce qui n'est pas `an:` (#431)."""
    v = _make_vote(_scrutin("A9-0183/2023 - Résolution", position="contre", voteid=108425))
    assert v["scrutin_id"] is None
    assert v["position"] == "contre"
    non_resolu = v["scrutin_non_resolu"]
    assert non_resolu["institution"] == "parlement_europeen"
    assert non_resolu["numero_scrutin"] == 108425
    assert non_resolu["reference_dossier"] == "2022/2060(INI)"
    assert non_resolu["source_url"].startswith("https://www.europarl.europa.eu/")


def test_seuls_les_votes_sur_lensemble_dun_texte_entrent_et_le_reste_est_compte():
    """Une position d'amendement n'est pas une position absente (#511, §2 règle 5)."""
    profil = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    scrutins = (
        [_scrutin("A9-1/2023 - Résolution", voteid=i) for i in range(3)]
        + [_scrutin(f"A9-1/2023 - Am {i}", voteid=100 + i) for i in range(7)]
    )
    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_votes_for_mep", return_value=scrutins), \
         patch("normalize_parltrack_dumps.get_activities_for_mep", return_value={}):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    assert len(profil["votes"]) == 3
    ecartes = [w for w in profil["meta"]["warnings"]
               if w.startswith(WARNING_PREFIX_PARLTRACK_VOTES_ECARTES)]
    assert len(ecartes) == 1
    assert "7 scrutin(s)" in ecartes[0]
    assert validate_profil(profil) == []


def test_les_votes_ne_se_republient_pas_a_chaque_run():
    """La clé doit être CELLE de `merge_profile._pivot_vote_key`, branche non résolue."""
    profil = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    scrutins = [_scrutin("A9-1/2023 - Résolution", voteid=42)]
    doublure = {
        "normalize_parltrack_dumps.get_dossiers_for_mep": [],
        "normalize_parltrack_dumps.get_amendments_for_mep": [],
        "normalize_parltrack_dumps.get_votes_for_mep": scrutins,
        "normalize_parltrack_dumps.get_activities_for_mep": {},
    }
    for _ in range(2):
        with patch(list(doublure)[0], return_value=doublure[list(doublure)[0]]), \
             patch(list(doublure)[1], return_value=doublure[list(doublure)[1]]), \
             patch(list(doublure)[2], return_value=doublure[list(doublure)[2]]), \
             patch(list(doublure)[3], return_value=doublure[list(doublure)[3]]):
            enrich_pivot_with_parltrack(profil, mep_id=131580)
    assert len(profil["votes"]) == 1


# ---------------------------------------------------------------------------
# Les interventions : trois natures, une seule liste (#683)
# ---------------------------------------------------------------------------


def test_une_intervention_de_seance_declare_que_la_SOURCE_na_pas_de_verbatim():
    """`theme_seul` dirait que NOTRE run ne l'a pas demandé — deux absences
    différentes (§2 règle 5, la distinction de #657)."""
    i = _make_intervention("intervention_seance", {
        "titre": "The need for the EU's continuous support for Ukraine (debate)",
        "date": "2024-07-17", "reference": "P10_CRE-REV(2024)07-17(2-020-0000)",
        "source_url": "https://www.europarl.europa.eu/doceo/document/CRE-10-…_FR.html",
        "legislature": 10, "texte": None,
    })
    assert i["type_detail"] == "debat"
    assert i["collecte"] == "sans_verbatim_source"
    assert i["texte"] is None
    assert i["intervention_id"] == "europarl_P10_CRE-REV(2024)07-17(2-020-0000)"


def test_une_explication_de_vote_porte_les_mots_et_aucune_marque_de_collecte():
    """C'est la seule matière européenne de forme complète : elle a son texte."""
    i = _make_intervention("explication_de_vote_ecrite", {
        "titre": "The need for the EU's continuous support for Ukraine (B10-0007/2024)",
        "date": "2024-07-17", "reference": None, "source_url": None,
        "legislature": 10, "texte": "Derrière l'objectif louable d'un soutien appuyé…",
    })
    assert i["type_detail"] == "explication_de_vote"
    assert "collecte" not in i
    assert i["texte"].startswith("Derrière")
    assert i["source_url"] is None


def test_une_question_ecrite_se_range_ou_lassemblee_range_les_siennes():
    i = _make_intervention("question_ecrite", {
        "titre": "Attacks on Bangladesh's Hindu minority", "date": "2024-09-10",
        "reference": "E-001670/2024", "legislature": 10,
        "source_url": "https://www.europarl.europa.eu/doceo/document/E-10-2024-001670_EN.html",
    })
    assert i["type_detail"] == "question"
    assert i["sous_type"] == "QE"


def test_labsence_de_lien_des_explications_de_vote_est_declaree():
    """0 sur 190 en portent un : la limite se publie, elle ne se comble pas
    par une URL devinée (§2 règle 2)."""
    profil = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    activites = {"explication_de_vote_ecrite": [
        {"titre": f"Texte {i}", "date": "2024-07-17", "reference": None,
         "source_url": None, "legislature": 10, "texte": f"Mon explication {i}"}
        for i in range(4)
    ]}
    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_votes_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_activities_for_mep", return_value=activites):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    assert len(profil["interventions"]) == 4
    declares = [w for w in profil["meta"]["warnings"]
                if w.startswith(WARNING_PREFIX_PARLTRACK_EXPLICATIONS_SANS_LIEN)]
    assert len(declares) == 1 and "4 explication(s)" in declares[0]
    assert validate_profil(profil) == []


def test_une_proposition_de_resolution_est_un_texte_porte():
    """Le rôle existe déjà dans `KNOWN_ROLES_TEXTE` — rien à inventer."""
    profil = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    activites = {"proposition_de_resolution": [{
        "titre": "MOTION FOR A RESOLUTION on the situation of women in Afghanistan",
        "date": "2024-09-16", "reference": "B10-0040/2024", "legislature": 10,
        "source_url": "https://www.europarl.europa.eu/doceo/document/B-10-2024-0040_EN.html",
    }]}
    # `build_stades_dossiers_index` lirait le cache RÉEL du poste (#721) : une
    # activité portée déclenche désormais sa construction, pour résoudre le
    # stade du dossier visé (#901). L'index vide suffit ici — cette activité ne
    # vise aucun dossier, et l'entrée doit le déclarer.
    with patch("normalize_parltrack_dumps.get_dossiers_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_amendments_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.get_votes_for_mep", return_value=[]), \
         patch("normalize_parltrack_dumps.build_stades_dossiers_index", return_value={}), \
         patch("normalize_parltrack_dumps.get_activities_for_mep", return_value=activites):
        enrich_pivot_with_parltrack(profil, mep_id=131580)

    assert len(profil["textes_portes"]) == 1
    assert profil["textes_portes"][0]["role"] == "auteur_proposition_de_resolution"
    assert profil["textes_portes"][0]["reference_dossier"] is None
    assert profil["textes_portes"][0]["stade_procedural_non_resolu"] == {
        "motif": "activite_sans_dossier"}
    assert profil["interventions"] == []
    assert validate_profil(profil) == []


# ---------------------------------------------------------------------------
# Le défaut que la suite n'attrapait pas (#683)
# ---------------------------------------------------------------------------


def test_la_legislature_en_cours_est_lue_malgre_le_changement_de_langue():
    """LE test qui manquait.

    Au passage à la XIe législature (juillet 2024), la source change deux
    choses à la fois : elle écrit en **anglais** et sépare par un **tiret
    demi-cadratin** au lieu du trait d'union. La première version de la
    sélection ne connaissait ni l'un ni l'autre : elle rendait `0` scrutin
    retenu sur 2024, 2025 et 2026 — **5 012 pour le seul Jordan Bardella** —
    et la fiche se serait arrêtée au 19/10/2023 sans que rien ne le dise.

    Aucun test unitaire n'aurait pu le voir : toutes les fixtures étaient
    écrites dans le format d'avant. Il a fallu regarder l'effet sur le corpus
    réel — la borne de couverture qui s'arrêtait trois ans trop tôt.
    """
    for titre in [
        "RC-B10-0055/2025 – Motion for a resolution (as a whole)",
        "A10-0027/2024 – Karlo Ressler – Draft Council decision",
        "A10-0167/2026 – Single vote",
        "B10-0040/2024 – Commission proposal",
    ]:
        assert _porte_sur_ensemble(titre), titre


def test_les_points_de_procedure_de_la_legislature_en_cours_restent_ecartes():
    """Le tiret long ne doit pas faire entrer ce que le trait d'union écartait."""
    for titre in [
        "Wednesday's agenda – Request by the PfE Group",
        "RC-B10-0055/2025 – § 19 – Am 4= 7=",
        "A10-0027/2024 – Proposal to vote on amendments",
        "B10-0040/2024 – Request for referral back (Rule 60(4))",
    ]:
        assert not _porte_sur_ensemble(titre), titre


def test_la_nature_garde_lordre_de_ses_mots():
    """`_normaliser_nom` trie les mots — un nom s'écrit dans les deux ordres.
    Une nature de scrutin, non : « proposition de décision » et « décision de
    proposition » ne sont pas la même chose."""
    assert _nature_scrutin("A9-1/2023 - Proposition de décision") == "proposition de decision"
    assert not _porte_sur_ensemble("A9-1/2023 - Décision de proposition")


# ---------------------------------------------------------------------------
# Un constat périmé ne survit pas à l'arrivée de données (#683)
# ---------------------------------------------------------------------------


def test_le_constat_aucune_donnee_est_retire_quand_la_donnee_arrive():
    """Sans cette reprise, la fiche de Bardella publierait « ParlTrack : aucune
    donnée trouvée pour le député européen 131580 » à côté de 1 926 votes.

    `unir_warnings` garde un message de l'ancien écrivain dont la famille n'est
    pas représentée par le nouveau — et un run qui TROUVE des données n'émet
    rien dans la famille « aucune donnée ».
    """
    from merge_profile import merge_pivot_profile

    ancien = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    ancien["meta"]["warnings"] = [
        "ParlTrack: aucune donnée trouvée pour le député européen "
        "(identifiant ParlTrack 131580) dans les dumps publiés sur parltrack.org/dumps.",
        "ParlTrack (diagnostic) : aucune donnée pour le MEP ID 131580.",
    ]
    nouveau = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    nouveau["votes"] = [_make_vote(_scrutin("A9-1/2023 - Résolution", voteid=7))]

    fusionne = merge_pivot_profile(ancien, nouveau)
    restants = [w for w in fusionne["meta"]["warnings"] if "ParlTrack" in w]
    assert restants == [], restants


def test_le_constat_survit_tant_quaucune_donnee_narrive():
    """La reprise se fait sur PREUVE — une entrée européenne —, pas sur le
    succès d'un appel. Sans donnée, le constat reste vrai et reste publié."""
    from merge_profile import merge_pivot_profile

    ancien = make_empty_profil("jordan-bardella", "Jordan BARDELLA")
    ancien["meta"]["warnings"] = [
        "ParlTrack: aucune donnée trouvée pour le député européen "
        "(identifiant ParlTrack 131580) dans les dumps publiés sur parltrack.org/dumps.",
    ]
    fusionne = merge_pivot_profile(ancien, make_empty_profil("jordan-bardella", "Jordan BARDELLA"))
    assert any("ParlTrack" in w for w in fusionne["meta"]["warnings"])


def test_les_deux_constats_de_couverture_sont_des_familles():
    """Ils portent des COMPTEURS : sans famille, deux fusions successives
    publient deux comptes côte à côte, dont un faux (vérifié : 12 000 et 18 709)."""
    from merge_profile import unir_warnings

    premier = unir_warnings(
        [f"{WARNING_PREFIX_PARLTRACK_VOTES_ECARTES} 18709 scrutin(s) …"], [])
    second = unir_warnings(
        [f"{WARNING_PREFIX_PARLTRACK_VOTES_ECARTES} 12000 scrutin(s) …"], premier)
    assert len(second) == 1 and "12000" in second[0]

    premier = unir_warnings(
        [f"{WARNING_PREFIX_PARLTRACK_EXPLICATIONS_SANS_LIEN} 179 explication(s) …"], [])
    second = unir_warnings(
        [f"{WARNING_PREFIX_PARLTRACK_EXPLICATIONS_SANS_LIEN} 4 explication(s) …"], premier)
    assert len(second) == 1 and " 4 " in second[0]


def test_le_repli_perime_est_retire_lui_aussi():
    """Le troisième constat ParlTrack, manqué par la première reprise (#683).

    Le run `34377413730` a publié « ParlTrack (fallback) : dumps absents ce
    run » sur **les 6 profils enrichis**, hérité d'un run où c'était vrai, à
    côté des votes qui viennent précisément de ces dumps. Même mécanisme que
    les deux autres familles : c'est l'énumération qui était incomplète.
    """
    from merge_profile import merge_pivot_profile

    ancien = make_empty_profil("raphael-glucksmann", "Raphaël GLUCKSMANN")
    ancien["meta"]["warnings"] = [
        "ParlTrack (fallback) : dumps absents ce run — données ParlTrack issues "
        "du cache/dépôt précédent.",
    ]
    nouveau = make_empty_profil("raphael-glucksmann", "Raphaël GLUCKSMANN")
    nouveau["votes"] = [_make_vote(_scrutin("A9-1/2023 - Résolution", voteid=7))]

    fusionne = merge_pivot_profile(ancien, nouveau)
    assert [w for w in fusionne["meta"]["warnings"] if "ParlTrack" in w] == []
