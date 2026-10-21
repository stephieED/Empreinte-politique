#!/usr/bin/env python3
"""#1317 — la place de chaque député dans l'hémicycle, lue dans l'archive de SA
législature.

Les fixtures sont COPIÉES, jamais écrites à la main :

- `tests/fixtures/amo30_place_hemicycle_1317/` : trois extraits octet pour
  octet des archives AMO30 téléchargées par la session du 19-21/10/2026 —
  `courante_17.zip` (`repository/17`, 19/10/2026 : acteurs `PA606507` et
  `PA721912`, et les organes de leurs mandats `ASSEMBLEE`/`GP`),
  `figee_16.zip` (`repository/16`, `last-modified` 28/06/2024 : `PA606507`),
  `figee_15.zip` (`repository/15`, 09/06/2022 : `PA606507` ; `PA721912` n'y
  est pas).

  | Acteur | Mandat | Courante | Archive de la législature | Ce qu'il prouve |
  | --- | --- | --- | --- | --- |
  | `PA606507` Florent Boudié | XVIIe 2024-07-07 | sans place | — | `source_sans_place` |
  | | XVIe 2022-06-19 | `251` | `354` | **le piège** : jamais 251 |
  | | XVe 2017-06-18 | `251` | `448` | idem |
  | | XIVe 2012-06-20 | `251` | aucune archive (404) | `legislature_sans_archive_figee` |
  | `PA721912` Damien Derelle | XVe 2017-06-18 | sans place | absent | `mandat_absent_de_l_archive` |

- `tests/fixtures/florent_boudie_mandats_1317.json` : le bloc `mandats` du
  profil brut et du profil pivot (`roster_groupe`) de `public/main`
  (`a9c3e10b9d`), verbatim — ses quatre mandats de député ont été publiés
  **sans** le champ, et c'est la transition vers un run qui le collecte que ce
  fichier teste.

Aucun test ne lit `raw_data/` ni `pivot_data/`, aucun ne sort sur le réseau.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cache_an_fraicheur as fr  # noqa: E402
import candidate_profile as cp  # noqa: E402
import merge_profile  # noqa: E402
from merge_profile import (  # noqa: E402
    backfill_mandat_place_hemicycle,
    merge_pivot_profile,
    merge_raw_profile,
)
from normalize_profil import _normalize_mandat  # noqa: E402
from schema_pivot import (  # noqa: E402
    KNOWN_MOTIFS_PLACE_HEMICYCLE_NON_RESOLU,
    _erreur_place_hemicycle,
    validate_profil,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ARCHIVES = FIXTURES / "amo30_place_hemicycle_1317"
CORPUS = FIXTURES / "florent_boudie_mandats_1317.json"

URL_16 = cp.ARCHIVES_AMO30_FIGEES["16"]["source_url"]
URL_15 = cp.ARCHIVES_AMO30_FIGEES["15"]["source_url"]
#: La date que porte le fichier de l'archive courante dans le cache : celle de
#: son téléchargement, qu'`etat_au` doit rendre (heure de Paris).
TELECHARGEE_LE = "2026-10-19"


def _servir_figees(url, dest_path, **kwargs):
    """Doublure de `download_with_watchdog` : rend l'extrait de l'archive que
    l'URL désigne, et rien d'autre."""
    source = {URL_16: ARCHIVES / "figee_16.zip", URL_15: ARCHIVES / "figee_15.zip"}[url]
    shutil.copy(source, dest_path)


@pytest.fixture
def cache(tmp_path):
    """L'archive courante en cache (téléchargée le 19/10/2026), les archives
    figées servies par la doublure — jamais par le réseau."""
    courante = tmp_path / "acteurs_historique.zip"
    shutil.copy(ARCHIVES / "courante_17.zip", courante)
    midi = datetime(2026, 10, 19, 12, tzinfo=ZoneInfo("Europe/Paris")).timestamp()
    os.utime(courante, (midi, midi))
    cp._clear_acteurs_historique_index_memo()
    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.download_with_watchdog", side_effect=_servir_figees) as telechargement,
    ):
        yield tmp_path, telechargement
    cp._clear_acteurs_historique_index_memo()


def _electifs(mandats):
    return [m for m in mandats if m.get("categorie") == "mandat_electif"]


# ---------------------------------------------------------------------------
# 1. La lecture : chaque législature dans SON archive
# ---------------------------------------------------------------------------

def test_un_mandat_xvie_porte_la_place_de_l_archive_xvie_jamais_la_courante(cache):
    """LE défaut central : l'archive courante donne 251 au mandat XVIe de
    Florent Boudié — son siège en XVIIe, recopié. L'archive XVIe, figée le
    28/06/2024, dit 354. La place publiée est 354."""
    import zipfile

    with zipfile.ZipFile(ARCHIVES / "courante_17.zip") as zf:
        acteur = json.loads(zf.read("json/acteur/PA606507.json"))["acteur"]
    xvie_courante = [m for m in acteur["mandats"]["mandat"]
                     if m.get("typeOrgane") == "ASSEMBLEE" and m["legislature"] == "16"]
    assert xvie_courante[0]["mandature"]["placeHemicycle"] == "251", "le piège doit être dans la fixture"

    place, non_resolu = cp.resoudre_place_hemicycle("PA606507", "16", "2022-06-19")
    assert place == {"numero": "354", "source_url": URL_16, "etat_au": "2024-06-28"}
    assert non_resolu is None


def test_un_mandat_xve_porte_la_place_de_l_archive_xve(cache):
    place, non_resolu = cp.resoudre_place_hemicycle("PA606507", "15", "2017-06-18")
    assert place == {"numero": "448", "source_url": URL_15, "etat_au": "2022-06-09"}
    assert non_resolu is None


def test_la_xive_n_emprunte_la_place_d_aucune_autre_archive(cache):
    """La courante donne 251 au mandat XIVe ; aucune archive XIVe n'existe."""
    place, non_resolu = cp.resoudre_place_hemicycle("PA606507", "14", "2012-06-20")
    assert place is None
    assert non_resolu == {"motif": "legislature_sans_archive_figee", "legislature": "14"}


def test_un_mandat_xviie_sans_place_le_dit_et_nomme_l_archive_lue(cache):
    place, non_resolu = cp.resoudre_place_hemicycle("PA606507", "17", "2024-07-07")
    assert place is None
    assert non_resolu == {
        "motif": "source_sans_place",
        "source_url": cp.AN_ACTEURS_HISTORIQUE_ZIP_URL,
        "etat_au": TELECHARGEE_LE,
    }


def test_un_mandat_que_l_archive_de_sa_legislature_ne_porte_pas(cache):
    """Damien Derelle, remplaçant entré en XVe après le 09/06/2022 : la
    courante a son mandat, l'archive XVe figée ne l'a pas."""
    place, non_resolu = cp.resoudre_place_hemicycle("PA721912", "15", "2017-06-18")
    assert place is None
    assert non_resolu == {"motif": "mandat_absent_de_l_archive", "source_url": URL_15, "etat_au": "2022-06-09"}


def test_les_archives_figees_se_telechargent_une_fois_et_restent_en_cache(cache):
    tmp_path, telechargement = cache
    cp.resoudre_place_hemicycle("PA606507", "16", "2022-06-19")
    cp.resoudre_place_hemicycle("PA606507", "16", "2022-06-19")
    assert [appel.args[0] for appel in telechargement.call_args_list] == [URL_16]
    kwargs = telechargement.call_args.kwargs
    assert kwargs["hard_timeout_seconds"] == cp.BUDGET_ARCHIVE_AMO30_FIGEE_SECONDES
    assert kwargs["reprises"] == cp.REPRISES_ARCHIVE_AMO30_FIGEE
    dossier = tmp_path / cp.SOUS_REPERTOIRE_AMO30_FIGEES / "16"
    assert (dossier / cp.NOM_ARCHIVE_AMO30_FIGEE).is_file()
    assert (dossier / cp.NOM_INDEX_PLACES_HEMICYCLE).is_file()


def test_une_archive_indisponible_n_est_jamais_un_constat_d_absence(tmp_path):
    """§2 règle 5 : un téléchargement en échec publie `archive_indisponible`,
    n'écrit aucun index, et n'est tenté qu'une fois par process."""
    import requests

    cp._clear_acteurs_historique_index_memo()
    with (
        patch("candidate_profile.ACTEURS_HISTORIQUE_CACHE_DIR", tmp_path),
        patch("candidate_profile.download_with_watchdog",
              side_effect=requests.ConnectionError("coupé")) as telechargement,
    ):
        for _ in range(3):
            place, non_resolu = cp.resoudre_place_hemicycle("PA606507", "16", "2022-06-19")
            assert place is None
            assert non_resolu == {"motif": "archive_indisponible", "source_url": URL_16}
        assert telechargement.call_count == 1
    assert not list(tmp_path.rglob(cp.NOM_INDEX_PLACES_HEMICYCLE))
    cp._clear_acteurs_historique_index_memo()


def test_les_quatre_motifs_sont_fermes():
    assert set(KNOWN_MOTIFS_PLACE_HEMICYCLE_NON_RESOLU) == {
        "legislature_sans_archive_figee", "archive_indisponible",
        "mandat_absent_de_l_archive", "source_sans_place",
    }


def test_les_archives_figees_sont_celles_des_legislatures_closes():
    assert set(cp.ARCHIVES_AMO30_FIGEES) <= fr.legislatures_figees()
    assert cp.LEGISLATURE_ARCHIVE_AMO30_COURANTE not in fr.legislatures_figees()
    for legislature, archive in cp.ARCHIVES_AMO30_FIGEES.items():
        assert archive["source_url"] == cp.AN_ACTEURS_HISTORIQUE_ZIP_URL.replace(
            "/repository/17/", f"/repository/{legislature}/")


# ---------------------------------------------------------------------------
# 2. Le profil : le même chemin pour les candidats et pour les rosters
# ---------------------------------------------------------------------------

def _build_profile(acteur_ref):
    """`build_profile` tel que `generate_all_profiles` l'appelle pour un
    candidat déclaré comme pour un membre de roster (`acteur_ref` fourni) :
    rien ne dépend de la provenance avant l'écriture."""
    identite_an = cp._build_acteur_identite_index()[acteur_ref]
    with (
        patch("candidate_profile.time.sleep", return_value=None),
        patch("candidate_profile.fetch_identite_officielle_par_slug", return_value=(identite_an, acteur_ref)),
        patch("candidate_profile._extract_mandats_officiels", return_value=[]),
        patch("candidate_profile.fetch_positions_hemicycle_officielles", return_value=[]),
        patch("candidate_profile.fetch_votes_officiels", return_value=([], [])),
        patch("candidate_profile.fetch_amendements_officiels", return_value=[]),
        patch("candidate_profile.fetch_textes_portes_officiels", return_value=[]),
        patch("candidate_profile.fetch_interventions_syceron", return_value=[]),
        patch("candidate_profile.fetch_questions_officielles", return_value=[]),
    ):
        return cp.build_profile("deputes", "florent-boudie", acteur_ref=acteur_ref)


def test_chaque_mandat_de_depute_du_profil_porte_sa_place(cache):
    profil = _build_profile("PA606507")
    par_debut = {m["debut"]: m for m in _electifs(profil["mandats"])}
    assert set(par_debut) == {"2024-07-07", "2022-06-19", "2017-06-18", "2012-06-20"}
    assert par_debut["2022-06-19"]["place_hemicycle"]["numero"] == "354"
    assert par_debut["2017-06-18"]["place_hemicycle"]["numero"] == "448"
    assert par_debut["2024-07-07"]["place_hemicycle_non_resolu"]["motif"] == "source_sans_place"
    assert par_debut["2012-06-20"]["place_hemicycle_non_resolu"]["motif"] == "legislature_sans_archive_figee"
    assert not any(m.get("place_hemicycle") and m["place_hemicycle"]["numero"] == "251"
                   for m in par_debut.values())
    pivot = [_normalize_mandat(m) for m in profil["mandats"]]
    assert all(_erreur_place_hemicycle(m) is None for m in pivot)


# ---------------------------------------------------------------------------
# 3. Le schéma et la normalisation
# ---------------------------------------------------------------------------

PLACE = {"numero": "354", "source_url": URL_16, "etat_au": "2024-06-28"}
DEPUTE = {"categorie": "mandat_electif", "chambre": "AN"}


def test_le_validateur_accepte_les_formes_justes():
    assert _erreur_place_hemicycle(DEPUTE) is None  # collecté avant le lot
    assert _erreur_place_hemicycle({**DEPUTE, "place_hemicycle": PLACE}) is None
    assert _erreur_place_hemicycle({**DEPUTE, "place_hemicycle": None, "place_hemicycle_non_resolu": {
        "motif": "legislature_sans_archive_figee", "legislature": "14"}}) is None
    assert _erreur_place_hemicycle({**DEPUTE, "place_hemicycle": None, "place_hemicycle_non_resolu": {
        "motif": "source_sans_place", "source_url": URL_16, "etat_au": "2024-06-28"}}) is None


@pytest.mark.parametrize("mandat", [
    {"categorie": "mandat_electif", "chambre": "PE", "place_hemicycle": PLACE},
    {"categorie": "commission", "chambre": "AN", "place_hemicycle": PLACE},
    {**DEPUTE, "place_hemicycle": None},
    {**DEPUTE, "place_hemicycle": None, "place_hemicycle_non_resolu": {"motif": "inconnu"}},
    {**DEPUTE, "place_hemicycle": None, "place_hemicycle_non_resolu": {"motif": "source_sans_place"}},
    {**DEPUTE, "place_hemicycle": PLACE, "place_hemicycle_non_resolu": {"motif": "archive_indisponible"}},
    {**DEPUTE, "place_hemicycle": {"numero": "354"}},
    {**DEPUTE, "place_hemicycle": {**PLACE, "numero": ""}},
    {**DEPUTE, "place_hemicycle": {**PLACE, "etat_au": "28/06/2024"}},
    {**DEPUTE, "place_hemicycle_non_resolu": {"motif": "archive_indisponible"}},
])
def test_le_validateur_refuse_les_formes_fausses(mandat):
    assert _erreur_place_hemicycle(mandat)


def test_validate_profil_rapporte_l_erreur():
    profil = {"mandats": [{"categorie": "mandat_electif", "chambre": "AN", "label": "x", "place_hemicycle": None}]}
    assert any("place_hemicycle" in e for e in validate_profil(profil))


def test_la_normalisation_ne_recopie_le_champ_que_sur_un_mandat_de_depute():
    brut = {"categorie": "mandat_electif", "chambre": "deputes", "type": "mandat", "label": "x",
            "debut": "2022-06-19", "place_hemicycle": PLACE}
    assert _normalize_mandat(brut)["place_hemicycle"] == PLACE
    nul = {**brut, "place_hemicycle": None,
           "place_hemicycle_non_resolu": {"motif": "archive_indisponible", "source_url": URL_16}}
    assert _normalize_mandat(nul)["place_hemicycle_non_resolu"]["motif"] == "archive_indisponible"
    assert "place_hemicycle" not in _normalize_mandat({**brut, "chambre": "europarl"})
    assert "place_hemicycle" not in _normalize_mandat({k: v for k, v in brut.items() if k != "place_hemicycle"})


# ---------------------------------------------------------------------------
# 4. La transition : un profil publié SANS le champ, puis un run qui le collecte
# ---------------------------------------------------------------------------

def _transition(cache):
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    ancien_brut, ancien_pivot = corpus["brut"], corpus["pivot"]
    assert all("place_hemicycle" not in m for m in ancien_brut["mandats"] + ancien_pivot["mandats"])
    neuf_brut = {"mandats": _build_profile("PA606507")["mandats"]}
    brut = merge_raw_profile(ancien_brut, neuf_brut)
    neuf_pivot = {"mandats": [_normalize_mandat(m) for m in brut["mandats"]]}
    pivot = merge_pivot_profile(ancien_pivot, neuf_pivot)
    return ancien_brut, ancien_pivot, brut, pivot


def test_le_champ_atteint_les_mandats_deja_publies_aux_deux_etages(cache):
    """Les quatre mandats de député de `florent-boudie` (profil de roster),
    publiés sans le champ sur `public/main`, le reçoivent au run suivant — au
    brut ET au pivot, la seule couche que `web/` lit."""
    ancien_brut, ancien_pivot, brut, pivot = _transition(cache)
    assert len(brut["mandats"]) == len(ancien_brut["mandats"]), "aucun mandat publié deux fois"
    assert len(pivot["mandats"]) == len(ancien_pivot["mandats"])
    for couche in (brut, pivot):
        par_debut = {m["debut"]: m for m in _electifs(couche["mandats"])}
        assert len(par_debut) == 4
        assert par_debut["2022-06-19"]["place_hemicycle"] == PLACE
        assert par_debut["2017-06-18"]["place_hemicycle"]["numero"] == "448"
        assert par_debut["2024-07-07"]["place_hemicycle_non_resolu"]["motif"] == "source_sans_place"
        assert par_debut["2012-06-20"]["place_hemicycle_non_resolu"]["motif"] == "legislature_sans_archive_figee"
    assert all(_erreur_place_hemicycle(m) is None for m in pivot["mandats"])
    assert not any("place_hemicycle" in m for m in pivot["mandats"] if m.get("categorie") != "mandat_electif")


def test_contre_epreuve_sans_le_report_rien_n_arrive(cache, monkeypatch):
    """Le report neutralisé, l'entrée ancienne gagne et aucun mandat publié ne
    reçoit le champ : c'est bien `backfill_mandat_place_hemicycle` qui le porte."""
    monkeypatch.setattr(merge_profile, "backfill_mandat_place_hemicycle", lambda merged, new, key: merged)
    _, _, brut, pivot = _transition(cache)
    for couche in (brut, pivot):
        assert not any("place_hemicycle" in m for m in _electifs(couche["mandats"]))


CLE = lambda m: (m.get("categorie"), m.get("debut"))  # noqa: E731


def _mandat(**champs):
    return {"categorie": "mandat_electif", "debut": "2022-06-19", **champs}


def test_une_place_resolue_n_est_jamais_remise_a_null():
    publie = [_mandat(place_hemicycle=PLACE)]
    neuf = [_mandat(place_hemicycle=None,
                    place_hemicycle_non_resolu={"motif": "archive_indisponible", "source_url": URL_16})]
    assert backfill_mandat_place_hemicycle(publie, neuf, CLE) == publie


def test_une_lecture_plus_recente_remplace_la_place_publiee():
    ancienne = {"numero": "380", "source_url": cp.AN_ACTEURS_HISTORIQUE_ZIP_URL, "etat_au": "2026-10-12"}
    recente = {**ancienne, "numero": "381", "etat_au": "2026-10-19"}
    assert backfill_mandat_place_hemicycle(
        [_mandat(place_hemicycle=ancienne)], [_mandat(place_hemicycle=recente)], CLE
    ) == [_mandat(place_hemicycle=recente)]
    assert backfill_mandat_place_hemicycle(
        [_mandat(place_hemicycle=recente)], [_mandat(place_hemicycle=ancienne)], CLE
    ) == [_mandat(place_hemicycle=recente)]


def test_une_place_resolue_remplace_un_null_et_son_motif():
    publie = [_mandat(place_hemicycle=None,
                      place_hemicycle_non_resolu={"motif": "archive_indisponible", "source_url": URL_16})]
    assert backfill_mandat_place_hemicycle(publie, [_mandat(place_hemicycle=PLACE)], CLE) == [
        _mandat(place_hemicycle=PLACE)
    ]


def test_un_run_sans_archive_n_efface_pas_un_motif_lu():
    lu = {"motif": "source_sans_place", "source_url": URL_16, "etat_au": "2024-06-28"}
    publie = [_mandat(place_hemicycle=None, place_hemicycle_non_resolu=lu)]
    neuf = [_mandat(place_hemicycle=None,
                    place_hemicycle_non_resolu={"motif": "archive_indisponible", "source_url": URL_16})]
    assert backfill_mandat_place_hemicycle(publie, neuf, CLE) == publie
    # …et l'inverse : une archive enfin lue remplace « indisponible ».
    assert backfill_mandat_place_hemicycle(neuf, publie, CLE) == publie


def test_un_mandat_qu_aucune_collecte_ne_couvre_reste_sans_cle():
    publie = [_mandat(debut="2012-06-20")]
    assert backfill_mandat_place_hemicycle(publie, [_mandat(place_hemicycle=PLACE)], CLE) == publie


# ---------------------------------------------------------------------------
# 5. Le cache : les archives figées ne périment pas chaque semaine
# ---------------------------------------------------------------------------

def test_la_peremption_hebdomadaire_epargne_les_archives_figees(tmp_path):
    acteurs = tmp_path / "acteurs_historique_an"
    figee = acteurs / cp.SOUS_REPERTOIRE_AMO30_FIGEES / "16"
    figee.mkdir(parents=True)
    (figee / cp.NOM_ARCHIVE_AMO30_FIGEE).write_bytes(b"PK")
    (acteurs / "acteurs_historique.zip").write_bytes(b"PK")
    (acteurs / cp.NOM_INDEX_PLACES_HEMICYCLE).write_text("{}", encoding="utf-8")
    fr.perimer(fr.chemins_perissables(
        cache_acteurs=acteurs, cache_scrutins=tmp_path / "s", cache_questions=tmp_path / "q",
        cache_syceron=tmp_path / "y",
    ))
    assert (figee / cp.NOM_ARCHIVE_AMO30_FIGEE).is_file()
    assert not (acteurs / "acteurs_historique.zip").exists()
    assert not (acteurs / cp.NOM_INDEX_PLACES_HEMICYCLE).exists()
