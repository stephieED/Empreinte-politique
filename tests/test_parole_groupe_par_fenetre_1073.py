"""#1073 — la parole d'un groupe est celle que ses membres y ont tenue, et elle
se compte sur deux fenêtres fixes.

Arbitré le 22/09/2026 : 6 mois, 12 mois, toute la période, comptées depuis la
date de référence de la fiche ; et, sur les trois, seule compte la parole tenue
PENDANT l'appartenance au groupe. Mesuré avant correctif sur EPR-17 : 7 308
interventions de membres partis ou pas encore arrivés nourrissaient l'empreinte
du groupe.

Les cas réels, copiés de `groupe-AN-RN-17.json` et des profils publiés :
Christine Engrand quitte le groupe RN le 19/11/2024 et prend la parole le
01/04/2025 et le 17/02/2026 — comptée pour le RN avant ce lot ; José Gonzalez
préside, en doyen, l'élection du 18/07/2024, la veille de la constitution des
groupes.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

import group_profile as gp  # noqa: E402
from lignee_profile import recalculer_agregats  # noqa: E402

ENGRAND = {"id": "christine-engrand", "interventions": [
    {"intervention_id": "syceron_CRSANR5L17S2025O1N154_000209", "date": "2025-04-01",
     "theme_officiel": "Allocation de solidarité aux personnes âgées"},
    {"intervention_id": "syceron_CRSANR5L17S2026O1N153_000108", "date": "2026-02-17",
     "theme_officiel": "Accueil des enfants souffrants d’autisme"},
]}
MEMBRE_ENGRAND = {"membre_id": "christine-engrand", "nom": "Christine Engrand",
                  "debut_dans_groupe": "2024-07-19", "fin_dans_groupe": "2024-11-19",
                  "periodes": [{"debut": "2024-07-19", "fin": "2024-11-19"}]}
GONZALEZ = {"id": "jose-gonzalez", "interventions": [
    {"intervention_id": "syceron_CRSANR5L17S2024D1N001_000014", "date": "2024-07-18",
     "theme_officiel": "Élection du président de l’Assemblée nationale"},
    {"intervention_id": "syceron_CRSANR5L17S2025O1N029_000887", "date": "2024-10-31",
     "theme_officiel": "Restaurer un système de retraite plus juste"},
]}
MEMBRE_GONZALEZ = {"membre_id": "jose-gonzalez", "nom": "José Gonzalez",
                   "debut_dans_groupe": "2024-07-19", "fin_dans_groupe": None,
                   "periodes": [{"debut": "2024-07-19", "fin": None}]}
APPARTENANCES = {m["membre_id"]: gp.periodes_d_appartenance(m) for m in (MEMBRE_ENGRAND, MEMBRE_GONZALEZ)}


def _intervention(jour, theme, n=1):
    return {"intervention_id": f"syceron_CRSANR5L17S2026O1N{n:03d}_000001", "date": jour,
            "theme_officiel": theme}


def _tags(agregat):
    return {t["tag"]: t for t in agregat.tags}


def test_la_parole_d_un_membre_parti_n_est_plus_celle_du_groupe():
    agregat = gp.aggregate_tags_thematiques([ENGRAND, GONZALEZ], legislature="17",
                                            appartenances=APPARTENANCES)

    assert set(_tags(agregat)) == {"restaurer un système de retraite plus juste"}
    assert agregat.hors_appartenance == 3  # Engrand deux fois, le doyen une


def test_une_appartenance_non_datee_garde_toute_la_legislature():
    """Rien ne prouve qu'il n'était pas membre : sa parole reste, et il est compté."""
    agregat = gp.aggregate_tags_thematiques(
        [ENGRAND], legislature="17", appartenances={"christine-engrand": None})

    assert len(agregat.tags) == 2
    assert agregat.appartenance_non_datee == 1


def test_une_fenetre_compte_des_membres_distincts():
    """Deux interventions du même membre sur le même débat : UN porteur."""
    a = {"id": "a", "interventions": [_intervention("2026-04-01", "Prix des carburants", 1),
                                      _intervention("2026-05-01", "Prix des carburants", 2)]}
    b = {"id": "b", "interventions": [_intervention("2025-11-01", "Prix des carburants", 3)]}
    ouvert = [("2024-07-19", None)]
    fenetres = gp.bornes_des_fenetres("2026-09-21", "2024-07-19")

    agregat = gp.aggregate_tags_thematiques(
        [a, b], legislature="17", appartenances={"a": ouvert, "b": ouvert}, fenetres=fenetres)

    tag = _tags(agregat)["prix des carburants"]
    assert tag["nb_membres_porteurs"] == 2
    assert tag["nb_membres_porteurs_par_fenetre"] == {"12_mois": 2, "6_mois": 1}
    assert agregat.fenetres["6_mois"]["nb_membres"] == 2


def test_le_denominateur_d_une_fenetre_ne_compte_que_les_membres_presents():
    """Parti le 19/11/2024, Christine Engrand n'est pas du dénominateur des
    fenêtres de 2026 — ni de leur numérateur."""
    fenetres = gp.bornes_des_fenetres("2026-09-21", "2024-07-19")
    agregat = gp.aggregate_tags_thematiques(
        [ENGRAND, GONZALEZ], legislature="17", appartenances=APPARTENANCES, fenetres=fenetres)

    assert agregat.fenetres["6_mois"]["nb_membres"] == 1
    assert agregat.fenetres["12_mois"]["nb_membres"] == 1
    assert "accueil des enfants souffrants d’autisme" not in _tags(agregat)


def test_une_intervention_sans_date_compte_sur_la_periode_pas_dans_une_fenetre():
    sans_date = {"id": "a", "interventions": [_intervention(None, "Budget")]}
    agregat = gp.aggregate_tags_thematiques(
        [sans_date], legislature="17", appartenances={"a": [("2024-07-19", None)]},
        fenetres=gp.bornes_des_fenetres("2026-09-21", "2024-07-19"))

    assert _tags(agregat)["budget"]["nb_membres_porteurs"] == 1
    assert _tags(agregat)["budget"]["nb_membres_porteurs_par_fenetre"] == {"12_mois": 0, "6_mois": 0}
    assert agregat.sans_date == 1


def test_les_bornes_partent_de_la_date_de_reference_et_jamais_avant_la_periode():
    assert gp.bornes_des_fenetres("2026-08-31", "2024-07-19") == {
        "12_mois": {"debut": "2025-08-31", "fin": "2026-08-31"},
        "6_mois": {"debut": "2026-02-28", "fin": "2026-08-31"},
    }
    assert gp.bornes_des_fenetres("2024-12-01", "2024-07-19")["12_mois"]["debut"] == "2024-07-19"
    assert gp.bornes_des_fenetres(None, "2024-07-19") is None


def test_la_projection_d_un_membre_garde_la_date():
    assert "date" in gp.CLES_LUES_PAR_ENTREE["interventions"]


def test_la_lignee_applique_aussi_l_appartenance():
    agregats = recalculer_agregats(
        [("17", ENGRAND), ("17", GONZALEZ)],
        appartenances={(m, "17"): p for m, p in APPARTENANCES.items()})

    assert [t["tag"] for t in agregats["tags_thematiques_agreges"]] == [
        "restaurer un système de retraite plus juste"]


def test_la_fiche_publie_les_fenetres_et_leurs_comptes():
    """Bout en bout : `build_groupe_profile` date les fenêtres sur la date de
    référence de la fiche, publie leurs bornes et leur dénominateur, et ne
    publie aucune date par membre."""
    profils = [{**p, "nom": m["nom"], "mandats": [], "votes": [], "amendements": [], "sources": []}
               for p, m in ((ENGRAND, MEMBRE_ENGRAND), (GONZALEZ, MEMBRE_GONZALEZ))]
    fiche = gp.build_groupe_profile(
        "AN:RN", "RN", "Rassemblement national", "AN", "17", profils,
        appartenances={m["membre_id"]: {"debut": m["debut_dans_groupe"], "fin": m["fin_dans_groupe"],
                                        "periodes": m["periodes"]}
                       for m in (MEMBRE_ENGRAND, MEMBRE_GONZALEZ)})

    reference = fiche["date_reference"]["date"]
    assert fiche["fenetres_parole"]["6_mois"]["fin"] == reference
    assert fiche["fenetres_parole"]["6_mois"]["nb_membres"] == 1
    assert set(fiche["fenetres_parole"]["6_mois"]) == {"debut", "fin", "nb_membres"}
    assert [t["tag"] for t in fiche["tags_thematiques_agreges"]] == [
        "restaurer un système de retraite plus juste"]
    assert set(fiche["tags_thematiques_agreges"][0]["nb_membres_porteurs_par_fenetre"]) == {
        "12_mois", "6_mois"}
