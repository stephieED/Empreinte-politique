"""Tests de `src/audit_mandats_reproductibles.py` (#839, lot B).

Ce que les tests protègent, dans l'ordre d'importance :

1. **Aucun verdict favorable sur une absence de mesure.** Une entrée sans date,
   un acteur non résolu, un référentiel vide : ce sont des déclarations, pas des
   jugements, et un lot de retrait ne doit pouvoir s'appuyer sur aucun des trois
   (§2 règle 5, résilience #241).
2. **Deux référentiels, jamais un seul.** AMO30 ne porte pas les organes du
   Parlement européen ; les juger sur lui seul les déclarerait introuvables,
   donc retirables.
3. **L'appariement approché reste borné.** Il rapproche « … de la francophonie
   a.p.f » de « … de la francophonie », pas « les transports » de « les
   transports et le tourisme ».

Les libellés des fixtures sont repris de profils réels, mais **aucun test ne lit
le corpus** : le détail vit dans la décision.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_mandats_reproductibles import (  # noqa: E402
    ACTEUR_NON_RESOLU,
    INTROUVABLE,
    PERIODE_COUVERTE_AUTREMENT,
    REFERENTIEL_INDISPONIBLE,
    REPRODUIT_AUTRE_PERIODE,
    REPRODUIT_EUROPEEN,
    REPRODUIT_LIBELLE_APPROCHE,
    REPRODUIT_MEME_PERIODE,
    SANS_DATE,
    auditer_profil,
    classer_mandat,
    organes_europeens,
)


def _mandat(label, debut=None, fin=None, categorie="commission", **extra):
    return {"label": label, "categorie": categorie, "debut": debut, "fin": fin, **extra}


def _classer(mandat, reference=(), organes_ue=frozenset(), sources=()):
    return classer_mandat(mandat, list(reference), set(organes_ue), list(sources))


# ---------------------------------------------------------------------------
# Les verdicts favorables
# ---------------------------------------------------------------------------

def test_meme_organe_periode_recouvrante():
    reference = [_mandat("Commission des affaires étrangères", "2017-06-29", "2019-01-29")]
    assert _classer(_mandat("Commission des affaires étrangères", "2017-06-29", "2019-01-29"), reference) \
        == REPRODUIT_MEME_PERIODE


def test_meme_organe_periode_disjointe_dit_que_le_fait_existe_et_pas_ce_decoupage():
    reference = [_mandat("Commission des affaires économiques", "2020-02-12", "2020-02-13")]
    assert _classer(_mandat("Commission des affaires économiques", "2012-01-01", "2012-06-30"), reference) \
        == REPRODUIT_AUTRE_PERIODE


def test_l_apostrophe_typographique_ne_doit_pas_faire_manquer_l_organe():
    """Calibrage du 12/09/2026 : `_normalize_label` garde les apostrophes, donc
    son retrait de préfixe ne reconnaissait pas « Mission d’information sur … »
    et les deux libellés gardaient chacun des mots que l'autre n'avait pas."""
    reference = [_mandat("Mission d’information sur l’impact de l’épidémie de coronavirus-covid 19",
                         "2020-03-30", "2020-11-30", categorie="mission_information")]
    publie = _mandat("Mission d'information sur l'impact de l'épidémie de coronavirus-covid 19 en france",
                     "2020-03-31", "2020-12-02")
    assert _classer(publie, reference) == REPRODUIT_LIBELLE_APPROCHE


def test_un_suffixe_du_referentiel_ne_casse_pas_l_appariement():
    reference = [_mandat("Section française de l'Assemblée parlementaire de la francophonie",
                         "2017-10-27", "2022-06-21", categorie="delegation")]
    publie = _mandat("Section française de l'assemblée parlementaire de la francophonie a.p.f",
                     "2017-10-28", None, categorie="extra_parlementaire")
    assert _classer(publie, reference) == REPRODUIT_LIBELLE_APPROCHE


def test_l_appariement_approche_refuse_les_libelles_trop_courts():
    """Deux mots significatifs rapprocheraient deux commissions distinctes."""
    reference = [_mandat("Commission des transports et du tourisme", "2007-01-31", "2009-07-13")]
    assert _classer(_mandat("Commission des transports", "2007-01-31", "2009-07-13"), reference) == INTROUVABLE


def test_un_organe_europeen_est_juge_sur_le_referentiel_europeen():
    """AMO30 ne les porte pas : sur lui seul, ils seraient déclarés
    introuvables, donc retirables. 21 entrées sont dans ce cas (#839, lot A)."""
    organes = organes_europeens({"mandat_europeen": {"mandats_europeens": [
        {"organisation_nom": "Commission de l'emploi et des affaires sociales"},
    ]}})
    mandat = _mandat("Commission de l'emploi et des affaires sociales", "2004-07-21", "2007-01-14")
    assert _classer(mandat, [], organes) == REPRODUIT_EUROPEEN
    assert _classer(mandat, []) == INTROUVABLE


def test_le_mandat_de_depute_europeen_fait_partie_du_referentiel_europeen():
    organes = organes_europeens({"mandat_europeen": {"mandats_europeens": []}})
    assert _classer(_mandat("Mandat de député européen", "2004-07-20", "2009-07-13"), [], organes) \
        == REPRODUIT_EUROPEEN


# ---------------------------------------------------------------------------
# Ce qui demande une relecture, et ce qui n'est pas un verdict
# ---------------------------------------------------------------------------

def test_une_periode_couverte_par_un_mandat_source_est_signalee_pas_tranchee():
    """Un nom de groupe publié comme commission : le fait est porté ailleurs,
    sous un autre nom. 113 entrées sont dans ce cas — elles se relisent."""
    sources = [_mandat("Groupe politique (FI)", "2017-06-27", "2022-06-21",
                       categorie="groupe_politique", categorie_source="an")]
    assert _classer(_mandat("La France Insoumise", "2017-06-28", "2021-10-12"), [], frozenset(), sources) \
        == PERIODE_COUVERTE_AUTREMENT


def test_une_entree_sans_aucune_date_n_est_pas_introuvable_mais_insituable():
    """La ranger parmi les introuvables autoriserait un retrait sur une absence
    de mesure. Les 13 intitulés de navigation sont dans ce cas."""
    assert _classer(_mandat("Vidéos", None, None, actif=True)) == SANS_DATE


def test_un_acteur_non_resolu_ne_rend_aucun_verdict():
    profil = {"mandats": [_mandat("Commission des lois", "2022-06-29")]}
    verdicts = auditer_profil(profil, [], frozenset(), acteur_resolu=False)
    assert [v for _, v in verdicts] == [ACTEUR_NON_RESOLU]


def test_un_referentiel_vide_ne_rend_aucun_verdict():
    """Résilience #241 : une extraction en échec ne doit rien conclure — sinon
    tout le profil serait déclaré introuvable, donc retirable."""
    profil = {"mandats": [_mandat("Commission des lois", "2022-06-29")]}
    verdicts = auditer_profil(profil, [], frozenset(), acteur_resolu=True)
    assert [v for _, v in verdicts] == [REFERENTIEL_INDISPONIBLE]


def test_seules_les_entrees_sans_estampille_sont_jugees():
    """Les entrées sourcées ne sont pas en cause : #718 les a établies."""
    profil = {"mandats": [
        _mandat("Commission des lois", "2022-06-29", categorie_source="an"),
        _mandat("Renaissance", "2022-06-29"),
    ]}
    verdicts = auditer_profil(profil, [_mandat("Commission des lois", "2022-06-29")], frozenset(), True)
    assert len(verdicts) == 1
    assert verdicts[0][0]["label"] == "Renaissance"


def test_un_profil_sans_entree_sans_estampille_ne_rend_rien():
    profil = {"mandats": [_mandat("Commission des lois", "2022-06-29", categorie_source="an")]}
    assert auditer_profil(profil, [], frozenset(), True) == []


def test_le_referentiel_europeen_d_un_profil_sans_volet_europeen_est_vide():
    assert organes_europeens(None) == set()
    assert organes_europeens({}) == set()
