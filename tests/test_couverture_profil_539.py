"""Pourquoi une liste d'un profil est vide — le bloc `couverture` (#539).

Une liste vide ne dit rien par elle-même, et sur ce corpus le vide est la norme :
`interventions` 469/476, `textes_portes` 454/476, `amendements` 120/476,
`votes` 21/476, `mandats` 9/476. Quatre situations sans rapport entre elles s'y
confondaient — un zéro constaté, un fait sur la personne, une source qui ne
couvre pas la période, une collecte qui n'a pas eu lieu.

Ce que ces tests tiennent, dans l'ordre d'importance :

  1. **la règle de fond** — la condition porte sur la santé de la source,
     jamais sur l'absence de résultat. C'est ce qui a manqué à #484, où un
     échec réseau a produit un vide traité comme une donnée. Un référentiel
     injoignable doit rendre « non collecté — panne », jamais « jamais élu » ;
  2. la `cause` est obligatoire **si et seulement si** l'état est
     `non_collecte` — sinon « nous n'avons pas réussi » et « nous avons choisi »
     se confondent, sur 469 profils ;
  3. la couverture **n'est pas fusionnée** : elle décrit le run, pas la
     personne. C'est le piège du lot ;
  4. les bornes publiées sont **celles du code**, pas des constantes recopiées
     à côté.

Aucune lecture de `pivot_data/` ni de `raw_data/profiles/` (#473).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import couverture_profil as cv  # noqa: E402
from candidate_profile import (  # noqa: E402
    AN_AMENDEMENTS_PATH,
    AN_SCRUTINS_LEGISLATURES,
)
from couverture_dossiers import AN_DOSSIERS_ARCHIVES  # noqa: E402
from merge_profile import merge_pivot_profile  # noqa: E402
from schema_pivot import (  # noqa: E402
    CAUSE_PANNE,
    CAUSE_PAR_DECISION,
    ETAT_COUVERT,
    ETAT_FAIT_ETABLI,
    ETAT_HORS_COUVERTURE,
    ETAT_NON_COLLECTE,
    LISTES_COUVERTES,
    make_empty_profil,
    valider_couverture,
    validate_profil,
)
from syceron_debates import SYCERON_AVAILABLE_LEGISLATURES  # noqa: E402

LE_JOUR = "2026-08-28"


def _profil(provenance="candidat_declare", warnings=(), collecte_ecartee=None) -> dict:
    profil = make_empty_profil("marie-martin", "Marie Martin", provenance=provenance)
    profil["meta"]["warnings"] = list(warnings)
    if collecte_ecartee is not None:
        profil["meta"]["collecte_ecartee"] = list(collecte_ecartee)
    return profil


def _etats(couverture, liste) -> list[str]:
    return [e["etat"] for e in couverture[liste]]


# ---------------------------------------------------------------------------
# 1. La règle de fond : la santé de la source, jamais l'absence de résultat
# ---------------------------------------------------------------------------

def test_un_referentiel_non_prouve_charge_ne_produit_jamais_un_fait_etabli():
    """**Le garde-fou de #484.** Un échec réseau rend exactement le même vide
    qu'une personne jamais élue. Sans référentiel prouvé chargé, l'état retombe
    sur `non_collecte`/`panne` — jamais sur « jamais élu·e »."""
    entree = {"acteur_ref": None, "ecart": None,
              "etat_civil": {"nom": "Martin", "date_naissance": "1970-01-01"}}
    verdict = cv.etablir_fait_hors_an(entree, cv.SanteReferentiel(nb_acteurs=None))

    assert verdict.etabli is False
    assert verdict.panne

    couverture = cv.deriver(_profil(), constate_le=LE_JOUR, fait_hors_an=verdict)
    for liste in LISTES_COUVERTES:
        assert _etats(couverture, liste) == [ETAT_NON_COLLECTE]
        assert couverture[liste][0]["cause"] == CAUSE_PANNE


def test_un_referentiel_a_moitie_lu_est_traite_comme_une_panne():
    """Ce n'est pas un référentiel vide qui produit #484 — c'est un référentiel
    partiel, qui répond sans être complet."""
    sante = cv.SanteReferentiel(nb_acteurs=cv.ACTEURS_AN_PLANCHER - 1)
    assert sante.prouve_charge is False
    assert cv.SanteReferentiel(nb_acteurs=cv.ACTEURS_AN_MESURE).prouve_charge is True


def test_le_fait_est_derive_quand_le_referentiel_est_prouve_charge():
    entree = {"acteur_ref": None, "ecart": None, "etat_civil": {
        "nom": "Martin", "nom_complet": "Marie Martin", "date_naissance": "1970-01-01"}}
    verdict = cv.etablir_fait_hors_an(
        entree, cv.SanteReferentiel(nb_acteurs=cv.ACTEURS_AN_MESURE))
    assert verdict.etabli is True and verdict.humain is False
    assert str(cv.ACTEURS_AN_MESURE) in verdict.preuve


def test_sans_date_de_naissance_aucune_derivation_condition_c3():
    """Le cas Bardella : sa date est `null` dans la table. Sans état civil
    complet, c'est une déclaration humaine qui répond, pas un automatisme."""
    entree = {"acteur_ref": None, "ecart": None,
              "etat_civil": {"nom": "Bardella", "date_naissance": None}}
    verdict = cv.etablir_fait_hors_an(
        entree, cv.SanteReferentiel(nb_acteurs=cv.ACTEURS_AN_MESURE))
    assert verdict.etabli is False
    assert "date de naissance" in verdict.panne


def test_la_declaration_humaine_prime_meme_sur_un_referentiel_en_panne():
    """Condition C5. Sans elle, une panne effacerait un fait vérifié à la main."""
    entree = {
        "acteur_ref": None, "ecart": "hors_an",
        "motif": "Député européen, jamais élu à l'Assemblée nationale.",
        "preuve": "https://www.europarl.europa.eu/meps/fr/131580",
        "verifie_le": "2026-08-26",
        "etat_civil": {"nom": "Bardella", "date_naissance": None},
    }
    verdict = cv.etablir_fait_hors_an(entree, cv.SanteReferentiel(nb_acteurs=None))
    assert verdict.etabli is True and verdict.humain is True and verdict.panne is None


def test_une_personne_avec_un_acteur_an_ne_pose_pas_la_question():
    """`marine-le-pen` porte `PA720614` : brancher la dérivation sur un signal
    de run lui aurait publié « jamais élue à l'Assemblée nationale »."""
    entree = {"acteur_ref": "PA720614", "ecart": None, "etat_civil": {}}
    assert cv.etablir_fait_hors_an(entree, cv.SanteReferentiel(3117)) is None


def test_un_fait_etabli_est_borne_par_ce_que_le_referentiel_etaye():
    """Condition C1 : sans la borne écrite avec la règle, la phrase publiable
    n'est pas « jamais élue » mais « jamais élue depuis la XIIe »."""
    verdict = cv.FaitHorsAn(etabli=True, humain=True, preuve="table")
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR, fait_hors_an=verdict)
    assert _etats(couverture, "mandats") == [ETAT_FAIT_ETABLI, ETAT_HORS_COUVERTURE]
    assert couverture["mandats"][0]["portee"] == {
        "debut": cv.BORNES["mandats"].debut, "fin": None}


# ---------------------------------------------------------------------------
# 2. Décision de pipeline vs panne
# ---------------------------------------------------------------------------

def test_un_profil_roster_declare_ses_deux_listes_ecartees_par_decision():
    """469 profils sur 476. `generate-data.yml:1641` porte les deux `--skip-*`
    en dur, indépendamment des inputs (#357) — la décision se lit donc sur la
    provenance seule, sans rejouer le run."""
    couverture = cv.deriver(_profil(provenance="roster_groupe"), constate_le=LE_JOUR)
    for liste in ("interventions", "textes_portes"):
        assert _etats(couverture, liste) == [ETAT_NON_COLLECTE]
        assert couverture[liste][0]["cause"] == CAUSE_PAR_DECISION
        # « La preuve d'une décision est la décision, pas une URL » : elle nomme
        # le drapeau et l'issue.
        assert "#357" in couverture[liste][0]["preuve"]
    assert _etats(couverture, "votes") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


def test_la_trace_ecrite_par_la_collecte_prime_sur_l_inference():
    """La passe pivot de la CI est un `--pivot-only` sans drapeau
    (`generate-data.yml:1903`) : sans `meta.collecte_ecartee`, elle publierait
    « couvert » sur une liste que personne n'a demandée."""
    couverture = cv.deriver(
        _profil(collecte_ecartee=["interventions"]), constate_le=LE_JOUR)
    assert couverture["interventions"][0]["cause"] == CAUSE_PAR_DECISION
    assert _etats(couverture, "textes_portes") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


def test_une_absence_de_resultat_n_est_pas_une_panne():
    """**Le cœur de la règle.** Le même préfixe `votes introuvables` couvre deux
    faits opposés dans `candidate_profile` : « aucune correspondance officielle
    AN n'a été trouvée » (l. 4766, un constat) et « index des scrutins
    indisponible » (l. 1208, une panne). Indexer sur le préfixe reproduirait
    #484 ; la table est donc indexée sur le motif."""
    constat = _profil(warnings=[
        "votes introuvables : aucune correspondance officielle Assemblée "
        "nationale n'a été trouvée pour ce parlementaire/cette législature.",
        "mandats introuvables : aucun mandat/responsabilité trouvé dans le "
        "référentiel officiel Assemblée nationale.",
    ])
    couverture = cv.deriver(constat, constate_le=LE_JOUR)
    assert _etats(couverture, "votes") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]
    assert _etats(couverture, "mandats") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


def test_une_panne_de_source_est_bien_relevee():
    """La contrepartie : le garde-fou doit attraper ce qu'il prétend attraper."""
    panne = _profil(warnings=[
        "votes introuvables (législature 17) : index des scrutins indisponible "
        "(archive open data non téléchargée ou invalide)."
    ])
    couverture = cv.deriver(panne, constate_le=LE_JOUR)
    assert _etats(couverture, "votes") == [ETAT_NON_COLLECTE]
    assert couverture["votes"][0]["cause"] == CAUSE_PANNE
    # …et elle ne déborde pas sur les listes qu'elle ne concerne pas.
    assert _etats(couverture, "amendements") == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]


def test_une_troncature_de_budget_est_une_panne_sur_la_liste_tronquee():
    """Un profil tronqué est écrit et publié (#498) : sans cet état, son compte
    partiel se lirait comme un compte complet."""
    couverture = cv.deriver(
        _profil(warnings=["collecte d'interventions tronquée (budget de temps) : "
                          "budget épuisé après 247 s (plafond 240 s)"]),
        constate_le=LE_JOUR,
    )
    assert couverture["interventions"][0]["cause"] == CAUSE_PANNE


def test_une_decision_passe_avant_une_panne_sur_la_meme_liste():
    """Rien n'a été demandé à la source : ni son périmètre ni sa santé ne disent
    quoi que ce soit sur cette liste."""
    profil = _profil(provenance="roster_groupe",
                     warnings=["interventions syceron indisponibles : archive absente"])
    assert cv.deriver(profil, constate_le=LE_JOUR)["interventions"][0]["cause"] \
        == CAUSE_PAR_DECISION


# ---------------------------------------------------------------------------
# 3. La forme : complétude, cause, preuve, constat, portée
# ---------------------------------------------------------------------------

def test_les_cinq_listes_metier_et_pas_tags_thematiques():
    """`tags_thematiques` est une aide à la lecture dérivée des autres listes
    (AGENTS.md §2.8) : sans source propre, elle n'a pas de borne propre."""
    assert set(LISTES_COUVERTES) == {
        "mandats", "votes", "textes_portes", "interventions", "amendements"}
    assert "tags_thematiques" not in LISTES_COUVERTES


def test_la_completude_est_obligatoire():
    """Aucun défaut implicite : « pas d'entrée = couvert » ferait porter à l'UI
    une hypothèse qu'aucune mesure n'étaye."""
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    assert set(couverture) == set(LISTES_COUVERTES)
    assert all(couverture[liste] for liste in LISTES_COUVERTES)

    del couverture["votes"]
    assert any("incomplète" in e and "votes" in e for e in valider_couverture(couverture))


def test_une_liste_a_zero_entree_est_refusee():
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    couverture["mandats"] = []
    assert any("au moins une entrée" in e for e in valider_couverture(couverture))


def test_la_cause_est_obligatoire_sur_non_collecte():
    couverture = cv.deriver(_profil(provenance="roster_groupe"), constate_le=LE_JOUR)
    del couverture["interventions"][0]["cause"]
    assert any("obligatoire" in e for e in valider_couverture(couverture))


def test_la_cause_est_interdite_ailleurs():
    """Le « si et seulement si », dans l'autre sens : sans lui, une cause posée
    sur un `couvert` laisserait croire à un état intermédiaire."""
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    couverture["votes"][0]["cause"] = CAUSE_PANNE
    assert any("n'a de sens que sur" in e for e in valider_couverture(couverture))


@pytest.mark.parametrize("champ", ["preuve", "constate_le"])
def test_preuve_et_constat_sont_obligatoires_sur_chaque_entree(champ):
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    del couverture["votes"][0][champ]
    assert any(champ in e for e in valider_couverture(couverture))


def test_toute_entree_porte_sa_preuve_et_sa_date():
    couverture = cv.deriver(_profil(provenance="roster_groupe"), constate_le=LE_JOUR)
    for entrees in couverture.values():
        for entree in entrees:
            assert entree["preuve"].strip()
            assert entree["constate_le"] == LE_JOUR


@pytest.mark.parametrize("portee", [
    {"legislature": 17},
    {"debut": "2012-06-20", "fin": None},
    {"debut": None, "fin": "2012-06-19"},
    None,
])
def test_les_formes_de_portee_admises(portee):
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    couverture["votes"] = [{"etat": ETAT_COUVERT, "portee": portee,
                            "preuve": "p", "constate_le": LE_JOUR}]
    assert valider_couverture(couverture) == []


@pytest.mark.parametrize("portee, motif", [
    ({}, "ne borne rien"),
    ({"legislature": "17"}, "entier positif"),
    ({"legislature": 17, "debut": "2024-07-18"}, "mêle"),
    ({"annee": 2024}, "non reconnues"),
    ({"debut": "18/07/2024"}, "date ISO"),
])
def test_les_formes_de_portee_refusees(portee, motif):
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    couverture["votes"] = [{"etat": ETAT_COUVERT, "portee": portee,
                            "preuve": "p", "constate_le": LE_JOUR}]
    assert any(motif in e for e in valider_couverture(couverture))


def test_une_couverture_a_cheval_s_exprime_en_deux_entrees_pas_en_cinquieme_etat():
    """Le cas Ségolène Royal : mandat de XIIe législature, archives de scrutins
    à partir de la XIVe. `partielle` (le cinquième état de #399) aurait dit
    « à cheval » sans dire OÙ passe la frontière."""
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    votes = couverture["votes"]
    assert [e["etat"] for e in votes] == [ETAT_COUVERT, ETAT_HORS_COUVERTURE]
    assert votes[0]["portee"]["debut"] == "2012-06-20"   # ouverture de la XIVe
    assert votes[1]["portee"]["fin"] == "2012-06-19"     # la veille, sans trou
    assert "partielle" not in {e["etat"] for e in votes}


def test_un_hors_couverture_sans_portee_est_refuse():
    """Dire qu'une source ne couvre pas, sans dire quoi, n'informe personne."""
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    couverture["votes"][1]["portee"] = None
    assert any("sans portée" in e for e in valider_couverture(couverture))


def test_la_fabrique_refuse_de_publier_un_bloc_non_conforme(monkeypatch):
    """`appliquer` se contrôle avec la règle du schéma, écrite une fois."""
    monkeypatch.setattr(cv, "deriver", lambda *a, **k: {"votes": []})
    with pytest.raises(ValueError, match="non conforme"):
        cv.appliquer(_profil())


# ---------------------------------------------------------------------------
# 4. Le piège du lot : la couverture n'est pas fusionnée additivement
# ---------------------------------------------------------------------------

def test_la_couverture_du_run_remplace_celle_du_precedent():
    """Elle décrit le run, pas la personne. Fusionner ferait survivre un
    `couvert` établi le jour où la collecte tournait, à côté d'un
    `non_collecte` d'aujourd'hui : la panne masquée par son historique."""
    ancien = _profil()
    cv.appliquer(ancien, constate_le="2026-08-01")
    nouveau = _profil(warnings=["amendements indisponibles : archive absente"])
    cv.appliquer(nouveau, constate_le=LE_JOUR)

    fusionne = merge_pivot_profile(ancien, nouveau)
    assert _etats(fusionne["couverture"], "amendements") == [ETAT_NON_COLLECTE]
    assert fusionne["couverture"]["amendements"][0]["constate_le"] == LE_JOUR


def test_la_couverture_ancienne_survit_a_un_pivot_qui_n_en_derive_pas():
    """Un outil autonome qui ne dérive pas de couverture ne doit pas effacer
    celle du corpus — il ne peut pas non plus en inventer une."""
    ancien = _profil()
    cv.appliquer(ancien, constate_le="2026-08-01")
    nouveau = _profil()
    assert merge_pivot_profile(ancien, nouveau)["couverture"] \
        == ancien["couverture"]


def test_aucun_bloc_n_est_fabrique_sur_deux_profils_qui_n_en_ont_pas():
    assert "couverture" not in merge_pivot_profile(_profil(), _profil())


# ---------------------------------------------------------------------------
# 5. Les bornes publiées sont celles du code
# ---------------------------------------------------------------------------

def test_chaque_liste_metier_porte_sa_borne():
    assert set(cv.BORNES) == set(LISTES_COUVERTES)


@pytest.mark.parametrize("liste, attendues", [
    ("votes", tuple(sorted(int(x) for x in AN_SCRUTINS_LEGISLATURES))),
    ("amendements", tuple(sorted(int(x) for x in AN_AMENDEMENTS_PATH))),
    ("textes_portes", tuple(sorted(AN_DOSSIERS_ARCHIVES))),
    ("interventions", tuple(sorted(int(x) for x in SYCERON_AVAILABLE_LEGISLATURES))),
])
def test_la_borne_publiee_suit_la_constante_qui_la_porte(liste, attendues):
    """Le jour où une archive est ajoutée sans que la couverture publiée le
    dise, c'est ici que ça tombe — pas six mois plus tard, dans l'interface."""
    assert cv.BORNES[liste].legislatures == attendues


def test_la_borne_d_amo30_est_ecrite_avec_sa_mesure():
    """Condition C1 : « la borne basse d'AMO30 doit être mesurée et écrite avec
    la règle »."""
    borne = cv.BORNES["mandats"]
    assert borne.legislatures[0] == 12
    assert borne.debut == "2002-06-19"
    assert "3 117" in borne.preuve and "2002-06-19" in borne.preuve


def test_le_calendrier_ne_peut_pas_diverger_de_celui_des_scrutins():
    """Deux copies d'une même borne divergent en silence — l'argument qui a fait
    écarter le patron de #399 côté UI."""
    cv._verifier_calendrier()  # ne lève pas
    with pytest.raises(ValueError, match="deux valeurs"):
        original = cv.CALENDRIER_LEGISLATURES[17]
        cv.CALENDRIER_LEGISLATURES[17] = ("2024-07-19", None)
        try:
            cv._verifier_calendrier()
        finally:
            cv.CALENDRIER_LEGISLATURES[17] = original


def test_la_veille_est_contigue_a_la_borne_sans_trou_ni_recouvrement():
    for borne in cv.BORNES.values():
        from datetime import date, timedelta
        assert date.fromisoformat(borne.veille) + timedelta(days=1) \
            == date.fromisoformat(borne.debut)


# ---------------------------------------------------------------------------
# 6. Le bloc dans le schéma
# ---------------------------------------------------------------------------

def test_un_profil_couvert_est_valide_au_sens_du_schema():
    profil = _profil()
    cv.appliquer(profil, constate_le=LE_JOUR)
    assert validate_profil(profil) == []


def test_un_profil_sans_bloc_couverture_reste_valide():
    """Les 476 profils publiés avant #539 n'en portent pas."""
    assert validate_profil(_profil()) == []


def test_une_liste_hors_nomenclature_est_refusee():
    couverture = cv.deriver(_profil(), constate_le=LE_JOUR)
    couverture["tags_thematiques"] = [
        {"etat": ETAT_COUVERT, "preuve": "p", "constate_le": LE_JOUR}]
    assert any("hors nomenclature" in e for e in valider_couverture(couverture))
