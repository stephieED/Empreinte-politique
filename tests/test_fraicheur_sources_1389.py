"""#1389 — la date « à jour au » de chaque famille de données.

Arbitré le 29/10/2026 : sur le site, la dernière relecture réussie de la
source ; `synchro_le` reste dans le corpus. Une date par FAMILLE, parce qu'un
run manuel ou limité ne relit pas toute une source.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import fraicheur_sources as fs  # noqa: E402

TOUT_REUSSI = {job: "success" for f in fs.FAMILLES.values() for job in f.jobs}
CASES = {fs.CASE_INTERVENTIONS: True, fs.CASE_DOSSIERS: True}
WORKFLOW = (RACINE / ".github" / "workflows" / "generate-data.yml").read_text(encoding="utf-8")


def _poser(racine: Path, relatif: Path, jour: str, contenu: str = "x") -> None:
    chemin = racine / relatif
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if not chemin.suffix and not chemin.exists():
        chemin.mkdir()
    else:
        chemin.write_text(contenu, encoding="utf-8")
    horodatage = datetime.fromisoformat(f"{jour}T12:00:00+01:00").timestamp()
    os.utime(chemin, (horodatage, horodatage))


def _releves(**par_famille):
    return {nom: [{"date": d, "reussi": True, "job": "extract-an"} for d in dates]
            for nom, dates in par_famille.items()}


# ── Les témoins sont ceux qu'écrivent les modules ───────────────────────────

def test_les_temoins_suivent_les_constantes_des_modules():
    import candidate_profile as cp
    import gouvernement_textes as gt
    import syceron_debates as sd

    assert fs.TEMOIN_AMO30 == cp.ACTEURS_HISTORIQUE_CACHE_DIR / "acteurs_historique.zip"
    assert fs.TEMOIN_SCRUTINS == cp.SCRUTINS_CACHE_DIR / "17" / cp.SCRUTINS_CACHE_SCRUTINS_FILENAME
    assert set(fs.TEMOINS_SYCERON) == {sd.SYCERON_CACHE_DIR / "17" / cp.SYCERON_INDEX_PAR_ACTEUR_THEME_DIRNAME,
                                       sd.SYCERON_CACHE_DIR / "17" / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME}
    assert fs.TEMOIN_QUESTIONS == cp.QUESTIONS_CACHE_DIR / "17" / "index_par_acteur.json"
    assert fs.TEMOIN_DOSSIERS == gt._chemin_cache_archive(gt._LEGISLATURE_CACHE_HISTORIQUE)
    assert fs.TEMOIN_AMENDEMENTS == cp.AMENDEMENTS_CACHE_DIR / "17" / cp.AMENDEMENTS_FRAICHEUR_FILENAME


def test_chaque_job_nomme_existe_dans_le_workflow():
    jobs = set(re.findall(r"^  ([a-z0-9-]+):$", WORKFLOW, re.M))
    for nom, famille in fs.FAMILLES.items():
        assert set(famille.jobs) | set(famille.releve_par) <= jobs, nom


def test_chaque_job_qui_releve_publie_son_releve():
    """Un job nommé dans `releve_par` sans étape de relevé laisserait sa famille
    à `null` pour toujours, sans erreur."""
    for job in {j for f in fs.FAMILLES.values() for j in f.releve_par}:
        bloc = WORKFLOW.split(f"\n  {job}:\n", 1)[1].split("\n  merge-and-pivot:\n")[0]
        bloc = re.split(r"\n  [a-z0-9-]+:\n", bloc)[0]
        assert f"fraicheur_sources.py relever --job {job}" in bloc, job
        if job != "merge-and-pivot":                    # lui écrit sur place
            assert f"name: fraicheur-{job}" in bloc, job


def test_les_temoins_de_la_fiche_candidat_suivent_le_code():
    import candidate_profile_ue as ue
    import parltrack_dumps as pt

    assert fs.TEMOINS_PE_MANDATS == (ue.CACHE_DIR / "meps_FR.json", ue.CACHE_DIR / "organisations.json")
    assert fs.TEMOIN_PT_VOTES == pt.PARLTRACK_CACHE_DIR / pt._DUMP_VOTES
    assert set(fs.TEMOINS_PT_AMENDEMENTS) == {pt.PARLTRACK_CACHE_DIR / pt._DUMP_PLENARY_AMENDMENTS,
                                              pt.PARLTRACK_CACHE_DIR / pt._DUMP_COMMITTEE_AMENDMENTS}
    assert fs.TEMOIN_PT_INTERVENTIONS == pt.PARLTRACK_CACHE_DIR / pt._DUMP_ACTIVITIES
    assert fs.TEMOIN_PT_TEXTES == pt.PARLTRACK_CACHE_DIR / pt._DUMP_DOSSIERS
    # L'archive du Sénat est téléchargée par le workflow lui-même, et gardée.
    assert f"curl -sS -L --max-time 300 -o {fs.TEMOIN_SENAT}" in WORKFLOW


def test_les_documents_europeens_sont_releves_avant_la_composition():
    bloc = WORKFLOW.split("\n  merge-and-pivot:\n", 1)[1]
    assert bloc.index("src/documents_europeens.py") < bloc.index("relever --job merge-and-pivot") \
        < bloc.index("fraicheur_sources.py composer")


def test_le_job_de_fusion_compose_le_fichier():
    bloc = WORKFLOW.split("\n  merge-and-pivot:\n", 1)[1]
    assert "fraicheur_sources.py composer" in bloc
    assert "pattern: fraicheur-*" in bloc
    assert "toJSON(needs)" in bloc


# ── Relever ─────────────────────────────────────────────────────────────────

def test_la_date_d_un_temoin_est_sa_date_d_ecriture(tmp_path):
    _poser(tmp_path, fs.TEMOIN_SCRUTINS, "2026-10-20")
    _poser(tmp_path, fs.TEMOIN_AMO30, "2026-10-27")
    releve = fs.relever("extract-an", tmp_path)
    assert releve["an.votes"] == "2026-10-20"
    assert releve["an.mandats"] == "2026-10-27"
    assert releve["an.interventions"] is None          # aucun index Syceron sur le disque
    assert "an.amendements" not in releve               # relevé par un autre job


def test_l_indicateur_des_amendements_dit_s_il_a_reussi(tmp_path):
    temoin = tmp_path / fs.TEMOIN_AMENDEMENTS
    temoin.parent.mkdir(parents=True)
    temoin.write_text(json.dumps({"derniere_construction_reussie": True,
                                  "horodatage": "2026-10-28T19:05:00+0100"}), encoding="utf-8")
    assert fs.relever("extract-amendements-an", tmp_path) == {"an.amendements": "2026-10-28"}
    temoin.write_text(json.dumps({"derniere_construction_reussie": False,
                                  "horodatage": "2026-10-29T19:05:00+0100"}), encoding="utf-8")
    assert fs.relever("extract-amendements-an", tmp_path) == {"an.amendements": None}


# ── Composer ────────────────────────────────────────────────────────────────

def test_tout_reussi_les_familles_prennent_leur_date():
    doc = fs.composer(None, _releves(**{"an.votes": ["2026-10-27", "2026-10-28"]}),
                      TOUT_REUSSI, CASES, True, "2026-10-29")
    assert doc["familles"]["an.votes"]["a_jour_au"] == "2026-10-27"   # la plus ancienne des shards
    assert doc["familles"]["jo.actes"]["a_jour_au"] == "2026-10-29"   # sans cache : le run
    assert fs.valider(doc) == []


def test_un_job_en_echec_garde_la_date_precedente():
    precedent = {"familles": {"drees": {"source": "drees", "a_jour_au": "2026-10-22", "raison": None}}}
    doc = fs.composer(precedent, {}, {**TOUT_REUSSI, "extract-finances-etat": "failure"},
                      CASES, True, "2026-10-29")
    entree = doc["familles"]["drees"]
    assert entree["a_jour_au"] == "2026-10-22"
    assert entree["etat"] == fs.ETAT_EN_ECHEC and entree["en_echec_depuis"] == "2026-10-29"
    assert "extract-finances-etat" in entree["motif_dernier_run"]
    assert fs.valider(doc) == []


def test_une_famille_jamais_relue_vaut_null_avec_sa_raison():
    doc = fs.composer(None, {}, {**TOUT_REUSSI, "extract-actes-jo": "failure"}, CASES, True, "2026-10-29")
    entree = doc["familles"]["jo.actes"]
    assert entree["a_jour_au"] is None and "extract-actes-jo" in entree["raison"]


def test_une_case_decochee_n_avance_pas_sa_famille():
    precedent = {"familles": {"an.interventions": {"a_jour_au": "2026-10-26"}}}
    doc = fs.composer(precedent, _releves(**{"an.interventions": ["2026-10-28"], "an.votes": ["2026-10-28"]}),
                      TOUT_REUSSI, {fs.CASE_INTERVENTIONS: False, fs.CASE_DOSSIERS: True}, True, "2026-10-28")
    assert doc["familles"]["an.interventions"]["a_jour_au"] == "2026-10-26"
    assert doc["familles"]["an.interventions"]["etat"] == fs.ETAT_NON_RELUE
    assert "non cochée" in doc["familles"]["an.interventions"]["motif_dernier_run"]
    assert doc["familles"]["an.votes"]["a_jour_au"] == "2026-10-28"


def test_un_run_limite_n_avance_rien():
    doc = fs.composer(None, _releves(**{"an.votes": ["2026-10-28"]}), TOUT_REUSSI, CASES, False, "2026-10-28")
    assert all(e["a_jour_au"] is None for e in doc["familles"].values())
    assert "limité" in doc["familles"]["an.votes"]["raison"]


def test_un_shard_sans_temoin_ne_date_rien_et_ne_bloque_rien():
    """Un shard qui n'a pas ouvert les scrutins n'en publie rien : la date vient
    des shards qui les ont lus. Sans aucun relevé daté, la famille n'avance pas."""
    doc = fs.composer(None, _releves(**{"an.votes": ["2026-10-28", None]}), TOUT_REUSSI, CASES, True, "2026-10-28")
    assert doc["familles"]["an.votes"]["a_jour_au"] == "2026-10-28"
    doc = fs.composer(None, _releves(**{"an.votes": [None, None]}), TOUT_REUSSI, CASES, True, "2026-10-28")
    assert doc["familles"]["an.votes"]["a_jour_au"] is None
    assert "aucun fichier témoin" in doc["familles"]["an.votes"]["raison"]


def test_un_shard_en_echec_bloque_sa_famille_meme_si_needs_dit_succes():
    """`continue-on-error` fait lire « success » dans `needs` : le relevé porte
    l'état réel du job."""
    releves = {"an.votes": [{"date": "2026-10-28", "reussi": True, "job": "extract-an"},
                            {"date": "2026-10-28", "reussi": False, "job": "extract-roster-groupes"}]}
    doc = fs.composer(None, releves, TOUT_REUSSI, CASES, True, "2026-10-28")
    assert doc["familles"]["an.votes"]["a_jour_au"] is None
    assert "extract-roster-groupes" in doc["familles"]["an.votes"]["raison"]


# ── L'état : à jour, en échec depuis, non relue ─────────────────────────────

def test_un_echec_garde_sa_date_de_debut_jusqu_a_la_reussite():
    echec = {**TOUT_REUSSI, "extract-finances-etat": "failure"}
    doc = fs.composer(None, {}, TOUT_REUSSI, CASES, True, "2026-10-22")
    assert doc["familles"]["drees"]["etat"] == fs.ETAT_A_JOUR
    doc = fs.composer(doc, {}, echec, CASES, True, "2026-10-23")
    doc = fs.composer(doc, {}, echec, CASES, True, "2026-10-24")
    assert doc["familles"]["drees"]["en_echec_depuis"] == "2026-10-23"
    assert doc["familles"]["drees"]["a_jour_au"] == "2026-10-22"
    # Un run qui ne la relit pas ne dit rien de sa santé : l'échec reste.
    doc = fs.composer(doc, {}, TOUT_REUSSI, CASES, False, "2026-10-25")
    assert (doc["familles"]["drees"]["etat"], doc["familles"]["drees"]["en_echec_depuis"]) == \
        (fs.ETAT_EN_ECHEC, "2026-10-23")
    doc = fs.composer(doc, {}, TOUT_REUSSI, CASES, True, "2026-10-26")
    assert doc["familles"]["drees"] == {"source": "drees", "a_jour_au": "2026-10-26", "raison": None,
                                        "etat": fs.ETAT_A_JOUR, "en_echec_depuis": None,
                                        "motif_dernier_run": None}
    assert fs.valider(doc) == []


def test_un_job_saute_n_est_pas_une_panne():
    doc = fs.composer(None, {}, {**TOUT_REUSSI, "extract-actes-jo": "skipped"}, CASES, True, "2026-10-28")
    assert doc["familles"]["jo.actes"]["etat"] == fs.ETAT_NON_RELUE
    assert doc["familles"]["jo.actes"]["en_echec_depuis"] is None


def test_un_job_reussi_sans_aucun_temoin_est_un_echec():
    doc = fs.composer(None, _releves(**{"an.votes": [None]}), TOUT_REUSSI, CASES, True, "2026-10-28")
    assert doc["familles"]["an.votes"]["etat"] == fs.ETAT_EN_ECHEC


def test_le_validateur_refuse_un_etat_incoherent():
    doc = fs.composer(None, {}, TOUT_REUSSI, CASES, True, "2026-10-28")
    doc["familles"]["jo.actes"]["etat"] = "cassee"
    doc["familles"]["drees"]["en_echec_depuis"] = "2026-10-01"
    erreurs = fs.valider(doc)
    assert any("état inconnu" in e for e in erreurs)
    assert any("si et seulement si l'état est en échec" in e for e in erreurs)


def test_une_famille_sans_temoin_est_datee_par_son_releve():
    releves = {"rne.mandats_locaux": [{"date": None, "reussi": True, "job": "extract-mandats-locaux"}]}
    doc = fs.composer(None, releves, TOUT_REUSSI, CASES, True, "2026-10-29")
    assert doc["familles"]["rne.mandats_locaux"]["a_jour_au"] == "2026-10-29"
    # Sans relevé, le job n'a rien dit de lui-même : ce n'est pas une réussite.
    assert doc["familles"]["pe.documents"]["etat"] == fs.ETAT_EN_ECHEC
    assert "aucun relevé publié" in doc["familles"]["pe.documents"]["motif_dernier_run"]
    # Un relevé en échec (le job des mandats locaux, le 28/10/2026) ne date rien.
    releves = {"rne.mandats_locaux": [{"date": None, "reussi": False, "job": "extract-mandats-locaux"}]}
    doc = fs.composer(None, releves, TOUT_REUSSI, CASES, True, "2026-10-29")
    assert doc["familles"]["rne.mandats_locaux"]["etat"] == fs.ETAT_EN_ECHEC


def test_le_validateur_refuse_une_entree_sans_date_ni_raison():
    doc = fs.composer(None, {}, TOUT_REUSSI, CASES, True, "2026-10-28")
    doc["familles"]["an.votes"] = {"source": "an", "a_jour_au": None, "raison": None}
    assert any("exactement une" in e for e in fs.valider(doc))


def test_de_bout_en_bout(tmp_path):
    _poser(tmp_path, fs.TEMOIN_SCRUTINS, "2026-10-27")
    assert fs.main(["relever", "--job", "extract-an", "--racine", str(tmp_path),
                    "--sortie", str(tmp_path / "_fraicheur" / "extract-an-a.json"), "--reussi", "true"]) == 0
    fichier = tmp_path / "fraicheur_sources.json"
    needs = json.dumps({job: {"result": "success"} for job in TOUT_REUSSI})
    assert fs.main(["composer", "--releves", str(tmp_path / "_fraicheur"), "--needs", needs,
                    "--interventions", "true", "--dossiers", "true", "--perimetre-complet", "true",
                    "--date-du-run", "2026-10-28", "--fichier", str(fichier)]) == 0
    doc = json.loads(fichier.read_text(encoding="utf-8"))
    assert doc["familles"]["an.votes"]["a_jour_au"] == "2026-10-27"
    assert doc["familles"]["an.mandats"]["a_jour_au"] is None     # témoin absent du relevé
