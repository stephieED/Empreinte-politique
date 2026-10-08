"""La 17e se réindexe chaque jour, le référentiel des acteurs chaque semaine.

Cas du 08/10/2026 : l'index restauré sous la clé de la semaine avait été écrit le
07/10 au soir, et la séance du 07/10 manquait au run du 08/10.
"""
from __future__ import annotations

import cache_an_fraicheur as cf

CLE_MERCREDI = "public-data-cache-an-2026-W41-j3-interv-syc15.16.17-q14.15.16.17-p1177-libelle"
CLE_SANS_JOUR = "public-data-cache-an-2026-W41-interv-syc15.16.17-q14.15.16.17-p1177-libelle"


def test_meme_jour_frais():
    assert cf.evaluer("2026-W41-j3", CLE_MERCREDI).etat == cf.FRAIS


def test_autre_jour_de_la_semaine_perime_les_legislatures_vivantes():
    verdict = cf.evaluer("2026-W41-j4", CLE_MERCREDI)
    assert verdict.etat == cf.PERIME_DU_JOUR and verdict.perimee


def test_une_entree_ecrite_avant_le_jour_dans_la_cle_est_perimee():
    assert cf.evaluer("2026-W41-j4", CLE_SANS_JOUR).etat == cf.PERIME_DU_JOUR


def test_autre_semaine_perime_tout():
    assert cf.evaluer("2026-W42-j1", CLE_MERCREDI).etat == cf.PERIME


def test_appel_a_l_ancienne_forme_inchange():
    assert cf.evaluer("2026-W41", CLE_SANS_JOUR).etat == cf.FRAIS


def test_le_perime_du_jour_garde_le_referentiel_des_acteurs(tmp_path, monkeypatch):
    acteurs = tmp_path / "acteurs"
    syceron = tmp_path / "syceron"
    for chemin in (acteurs / "x", syceron / "17" / "index_par_acteur", syceron / "16" / "index_par_acteur"):
        chemin.mkdir(parents=True)
    monkeypatch.setattr(cf._cp, "ACTEURS_HISTORIQUE_CACHE_DIR", acteurs)
    monkeypatch.setattr(cf._cp, "SYCERON_CACHE_DIR", syceron)
    monkeypatch.setattr(cf._cp, "SCRUTINS_CACHE_DIR", tmp_path / "absent1")
    monkeypatch.setattr(cf._cp, "QUESTIONS_CACHE_DIR", tmp_path / "absent2")
    monkeypatch.setattr(cf, "legislatures_figees", lambda: frozenset({"15", "16"}))
    cf.main(["--semaine", "2026-W41-j4", "--cle-restauree", CLE_MERCREDI, "--perimer"])
    assert acteurs.is_dir()
    assert not (syceron / "17").exists()
    assert (syceron / "16").is_dir()
