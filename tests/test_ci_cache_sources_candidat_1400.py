"""Garde-fou #1400 : les caches Sénat, Parlement européen et ParlTrack se renouvellent.

Le défaut, mesuré sur le run public `40970208263` (29-30/10/2026) : le premier
fichier de fraîcheur complet datait du **20/09/2026** les sept familles de ces
trois sources. Le journal disait pourquoi :

    extract-parltrack : Dump ep_votes.json.zst en cache (âge : 39 j).
    extract-senat     : Export déjà en cache, téléchargement sauté.

C'est #749 et #555 hors de l'Assemblée : la clé tourne (chaque jour pour le
Sénat, chaque semaine pour les deux autres), mais le repli par préfixe restaure
l'entrée précédente, le code saute le téléchargement dès que le fichier existe,
et l'entrée repart sous la clé neuve. Chaque période blanchit la précédente.

La correction est celle de #749 : `outputs.cache-hit` ne vaut 'true' que sur la
clé EXACTE, jamais sur un repli. Chaque job s'en sert pour renouveler sa source
quand la clé de la période n'existait pas. Le préfixe de repli reste : il garde
un cache chaud quand le téléchargement échoue.

Ce fichier vérifie, pour chaque job, que la chaîne tient de bout en bout :
le step de cache porte un `id`, et le step qui renouvelle lit la sortie
`cache-hit` de CET `id`. Un `id` renommé d'un côté seulement rendrait la sortie
vide, donc différente de 'true' : le job retéléchargerait à chaque run, sans
que rien n'échoue. Le dernier test le dit.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`test_ci_cache_fraicheur_555.py` : le workflow est lu comme du texte.
"""

import re
from pathlib import Path

import pytest

import fraicheur_sources

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

#: job → (chemin du cache, id du step de cache, step qui renouvelle)
JOBS = {
    "extract-senat": (".cache/senat", "cache_senat", "Téléchargement de l'export Sénat"),
    "extract-ue-officiel": (
        ".cache/europarl", "cache_ue", "Renouvellement de la liste des députés européens"
    ),
    "extract-parltrack": (".cache/parltrack", "cache_parltrack", "Téléchargement dumps ParlTrack"),
}


def _job(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    bloc = re.search(
        rf"^  {re.escape(nom)}:\n(.*?)(?=\n  [a-z][a-z0-9-]*:\n)", texte, flags=re.S | re.M
    )
    assert bloc, f"Job `{nom}` introuvable dans generate-data.yml."
    return bloc.group(1)


def _steps(nom: str) -> list[str]:
    """Les steps d'un job, dans l'ordre, commentaires retirés (voir #555)."""
    morceaux = re.split(r"\n(?=      - (?:uses|name):)", "\n" + _job(nom))
    return [
        "\n".join(l for l in m.split("\n") if not l.strip().startswith("#"))
        for m in morceaux
        if m.strip().startswith("- ")
    ]


def _step_de_cache(job: str) -> str:
    chemin = JOBS[job][0]
    trouves = [
        s for s in _steps(job)
        if "actions/cache@" in s and re.search(rf"path: {re.escape(chemin)}\s*$", s, re.M)
    ]
    assert len(trouves) == 1, f"{job} : {len(trouves)} step(s) de cache sur {chemin} (attendu : 1)."
    return trouves[0]


def _step(job: str, nom: str) -> str:
    trouves = [s for s in _steps(job) if f"name: {nom}" in s]
    assert len(trouves) == 1, f"{job} : {len(trouves)} step(s) « {nom} » (attendu : 1)."
    return trouves[0]


def test_le_workflow_est_lisible():
    """Sans steps trouvés, chaque test ci-dessous passerait à vide (#460)."""
    for job in JOBS:
        assert len(_steps(job)) >= 5, job


@pytest.mark.parametrize("job", sorted(JOBS))
def test_le_step_de_cache_porte_son_id(job):
    _chemin, ident, _renouvelle = JOBS[job]
    assert re.search(rf"^\s*id: {ident}\s*$", _step_de_cache(job), re.M), (
        f"{job} : le step de cache n'a plus `id: {ident}`. Sans lui, `cache-hit` est "
        "illisible et le renouvellement de #1400 ne sait plus quand se faire."
    )


@pytest.mark.parametrize("job", sorted(JOBS))
def test_le_prefixe_de_repli_reste(job):
    """Le repli garde un cache chaud : retirer la ligne n'est pas la correction."""
    step = _step_de_cache(job)
    assert "restore-keys:" in step, f"{job} : `restore-keys` a disparu."


@pytest.mark.parametrize("job", sorted(JOBS))
def test_le_renouvellement_lit_la_cle_exacte(job):
    """Le step qui renouvelle lit `cache-hit` de l'`id` du step de cache, et
    le compare à 'true' : c'est la seule valeur qui dit « clé exacte »."""
    _chemin, ident, renouvelle = JOBS[job]
    step = _step(job, renouvelle)
    assert f"steps.{ident}.outputs.cache-hit" in step, (
        f"{job} : « {renouvelle} » ne lit plus `steps.{ident}.outputs.cache-hit`. "
        "Le téléchargement se saute alors dès que le fichier existe, et le repli "
        "par préfixe fait qu'il existe toujours (#1400)."
    )
    assert "'true'" in step or '"true"' in step, f"{job} : `cache-hit` n'est plus comparé à 'true'."


@pytest.mark.parametrize("job", sorted(JOBS))
def test_le_renouvellement_precede_la_collecte(job):
    """Placé après, il jetterait ce que le job vient de lire."""
    steps = _steps(job)
    _chemin, _ident, renouvelle = JOBS[job]
    rang_cache = steps.index(_step_de_cache(job))
    rang_renouvellement = steps.index(_step(job, renouvelle))
    assert rang_cache < rang_renouvellement
    collecte = {
        "extract-senat": "Collecte des appartenances sénatoriales",
        "extract-ue-officiel": "Extraction UE",
        "extract-parltrack": "Téléchargement dumps ParlTrack",
    }[job]
    assert rang_renouvellement <= steps.index(_step(job, collecte))


def test_ue_retire_exactement_les_temoins_de_pe_mandats():
    """Les fichiers retirés sont ceux qui datent `pe.mandats` dans le fichier
    de fraîcheur. Un témoin oublié garderait sa vieille date, et la famille
    avec lui (le relevé prend la plus ancienne)."""
    step = _step("extract-ue-officiel", JOBS["extract-ue-officiel"][2])
    retires = set(re.findall(r"\.cache/europarl/[\w.]+", step))
    temoins = {str(t) for t in fraicheur_sources.TEMOINS_PE_MANDATS}
    assert retires == temoins, f"retirés {sorted(retires)} ≠ témoins {sorted(temoins)}"


def test_les_ids_ne_servent_qu_une_fois():
    """Deux steps du même `id` dans un job : GitHub refuse le workflow."""
    for job, (_chemin, ident, _r) in JOBS.items():
        assert len(re.findall(rf"^\s*id: {ident}\s*$", _job(job), re.M)) == 1, job
