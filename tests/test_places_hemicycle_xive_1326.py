#!/usr/bin/env python3
"""#1326 — les places de la XIVe, lues dans le fichier que lisait la carte de
l'hémicycle du site de l'Assemblée, à l'état du 20/06/2017.

Les fixtures sont COPIÉES, jamais écrites à la main
(`tests/fixtures/places_site_an_xive_1326/`) :

- `place_14.txt` : trois entrées verbatim de
  `https://www.assemblee-nationale.fr/14/tribun/xml/place.txt`, téléchargé le
  22/10/2026 (75 991 octets, `last-modified` 07/02/2021) ;
- `courante_xive.zip` : quatre fichiers d'acteur, octet pour octet, de
  l'archive AMO30 courante téléchargée le 22/10/2026.

  | Acteur | Fichier | Mandats XIVe dans AMO30 | Ce qu'il prouve |
  | --- | --- | --- | --- |
  | `PA606507` Florent Boudié | `s467` | 2012-06-20 → 2017-06-20 | la place |
  | `PA642724` Frédéric Barbier | `s558` | 2012-06-20 → 2014-05-02, 2015-02-08 → 2017-06-20 | le siège va au mandat ouvert le 20/06/2017, pas au précédent |
  | `PA2912` Alain Vidalies | `s`, sans numéro | 2012-06-20 → 2017-06-20 (segments) | `source_sans_place` |
  | `PA785` Bernard Cazeneuve | absent | 2012-06-20 → 2017-06-20 (segments) | `mandat_absent_de_l_archive` |

Aucun test ne lit `raw_data/` ni `pivot_data/`, aucun ne sort sur le réseau.
"""

import shutil
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cache_an_fraicheur as fr  # noqa: E402
import candidate_profile as cp  # noqa: E402
import legislatures_an  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "places_site_an_xive_1326"
URL_14 = cp.FICHIERS_PLACES_SITE_AN["14"]["source_url"]
LU = {"source_url": URL_14, "etat_au": "2017-06-20"}


def _servir(url, dest_path, **kwargs):
    assert url == URL_14, url
    shutil.copy(FIXTURES / "place_14.txt", dest_path)


@pytest.fixture
def cache(tmp_path):
    shutil.copy(FIXTURES / "courante_xive.zip", tmp_path / "acteurs_historique.zip")
    cp._clear_acteurs_historique_index_memo()
    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.download_with_watchdog", side_effect=_servir) as telechargement,
    ):
        yield tmp_path, telechargement
    cp._clear_acteurs_historique_index_memo()


def test_la_source_est_le_fichier_du_site_a_la_fin_de_la_legislature():
    assert URL_14 == "https://www.assemblee-nationale.fr/14/tribun/xml/place.txt"
    assert cp.FICHIERS_PLACES_SITE_AN["14"]["etat_au"] == "2017-06-20"
    assert {"14", "15", "16", "17"} <= cp.legislatures_avec_places_hemicycle()
    assert "13" not in cp.legislatures_avec_places_hemicycle()


def test_un_depute_en_mandat_le_20_juin_2017_recoit_son_siege(cache):
    assert cp.resoudre_place_hemicycle("PA606507", "14", "2012-06-20") == ({"numero": "467", **LU}, None)


def test_le_siege_va_au_mandat_ouvert_ce_jour_jamais_au_precedent(cache):
    """Frédéric Barbier a deux sièges XIVe : le fichier décrit le second."""
    assert cp.resoudre_place_hemicycle("PA642724", "14", "2015-02-08") == ({"numero": "558", **LU}, None)
    assert cp.resoudre_place_hemicycle("PA642724", "14", "2012-06-20") == (
        None, {"motif": "mandat_absent_de_l_archive", **LU})


def test_la_cle_sans_numero_est_un_depute_sans_siege(cache):
    assert cp.resoudre_place_hemicycle("PA2912", "14", "2012-06-20") == (
        None, {"motif": "source_sans_place", **LU})


def test_un_depute_absent_du_fichier_n_a_pas_de_siege(cache):
    """Bernard Cazeneuve est en mandat le 20/06/2017 dans AMO30, mais le
    fichier ne le porte pas : aucun siège n'est inventé."""
    assert cp.resoudre_place_hemicycle("PA785", "14", "2012-06-20") == (
        None, {"motif": "mandat_absent_de_l_archive", **LU})


def test_un_identifiant_sans_mandat_ouvert_au_jour_lu_n_emprunte_aucun_siege(cache):
    """Lu au 01/06/2014, entre ses deux mandats, Frédéric Barbier n'a aucun
    siège ouvert : le numéro du fichier ne lui est pas prêté."""
    tmp_path, _ = cache
    places = cp._places_par_mandat_site_an(
        FIXTURES / "place_14.txt", tmp_path / "acteurs_historique.zip", "14", "2014-06-01")
    assert "PA642724" not in places
    assert places["PA606507"] == {"2012-06-20": "467"}


def test_le_fichier_se_telecharge_une_fois_et_reste_dans_le_cache_des_figees(cache):
    tmp_path, telechargement = cache
    cp.resoudre_place_hemicycle("PA606507", "14", "2012-06-20")
    cp.resoudre_place_hemicycle("PA642724", "14", "2015-02-08")
    assert [appel.args[0] for appel in telechargement.call_args_list] == [URL_14]
    assert telechargement.call_args.kwargs["hard_timeout_seconds"] == cp.BUDGET_FICHIER_PLACES_SITE_AN_SECONDES
    dossier = tmp_path / cp.SOUS_REPERTOIRE_AMO30_FIGEES / "14"
    assert (dossier / cp.NOM_FICHIER_PLACES_SITE_AN).is_file()
    assert (dossier / cp.NOM_INDEX_PLACES_HEMICYCLE).is_file()


def test_un_fichier_indisponible_n_est_jamais_un_constat_d_absence(tmp_path):
    import requests

    shutil.copy(FIXTURES / "courante_xive.zip", tmp_path / "acteurs_historique.zip")
    cp._clear_acteurs_historique_index_memo()
    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.download_with_watchdog",
              side_effect=requests.ConnectionError("coupé")) as telechargement,
    ):
        for _ in range(3):
            assert cp.resoudre_place_hemicycle("PA606507", "14", "2012-06-20") == (
                None, {"motif": "archive_indisponible", "source_url": URL_14})
        assert telechargement.call_count == 1
    assert not list(tmp_path.rglob(cp.NOM_INDEX_PLACES_HEMICYCLE))
    cp._clear_acteurs_historique_index_memo()


def test_un_fichier_illisible_n_ecrit_aucun_index(tmp_path):
    shutil.copy(FIXTURES / "courante_xive.zip", tmp_path / "acteurs_historique.zip")
    cp._clear_acteurs_historique_index_memo()
    """Une page d'erreur servie en 200 : rien n'est publié comme lu, le fichier
    ne reste pas en cache, et il n'est pas retéléchargé dans le même process."""
    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.download_with_watchdog",
              side_effect=lambda url, dest, **kw: Path(dest).write_text("<html>", encoding="utf-8"))
        as telechargement,
    ):
        for _ in range(3):
            assert cp.resoudre_place_hemicycle("PA606507", "14", "2012-06-20") == (
                None, {"motif": "archive_indisponible", "source_url": URL_14})
        assert telechargement.call_count == 1
    assert not list(tmp_path.rglob(cp.NOM_INDEX_PLACES_HEMICYCLE))
    assert not list(tmp_path.rglob(cp.NOM_FICHIER_PLACES_SITE_AN))
    cp._clear_acteurs_historique_index_memo()


def test_la_peremption_hebdomadaire_epargne_le_fichier_des_places(tmp_path):
    acteurs = tmp_path / "acteurs_historique_an"
    dossier = acteurs / cp.SOUS_REPERTOIRE_AMO30_FIGEES / "14"
    dossier.mkdir(parents=True)
    (dossier / cp.NOM_FICHIER_PLACES_SITE_AN).write_text("{}", encoding="utf-8")
    fr.perimer(fr.chemins_perissables(
        cache_acteurs=acteurs, cache_scrutins=tmp_path / "s", cache_questions=tmp_path / "q",
        cache_syceron=tmp_path / "y",
    ))
    assert (dossier / cp.NOM_FICHIER_PLACES_SITE_AN).is_file()


def test_les_groupes_de_la_xive_se_rangent_par_leur_siege(cache):
    """`legislatures.json` lit le même index : un groupe XIVe reçoit la
    médiane des sièges de ses membres au 20/06/2017. L'organe et les deux
    adhésions sont ceux de l'index `an_roster.charger_index_gp` lu sur
    l'archive du 22/10/2026, réduits à ces deux membres."""
    index = cp._build_index_places_hemicycle("14")
    index_gp = {
        "organes": {"PO713077": {"sigle": "SER", "sigle_abrege": "SER", "legislature": "14",
                                 "libelle": "Socialiste, écologiste et républicain"}},
        "mandats": {"PO713077": [["PA642724", "2016-05-25", "2017-06-20"],
                                 ["PA606507", "2016-05-25", "2017-06-20"]]},
    }
    groupes = legislatures_an.groupes_par_siege(index_gp, "14", "2017-06-20", index["places"])
    assert [(g["sigle"], g["membres_avec_place"], g["place_mediane"]) for g in groupes] == [("SER", 2, 512.5)]
