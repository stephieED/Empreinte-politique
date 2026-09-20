"""Garde-fou #424 : les répertoires de `.cache/` doivent tous être couverts par
un `actions/cache` de `generate-data.yml`.

Contexte. Jusqu'à #424, les trois jobs AN cachaient `.cache` en bloc sous une
clé partagée. `extract-amendements-an` écrivant la clé exacte de la semaine en
premier, `extract-an` et `extract-roster-groupes` faisaient un *exact key hit*
et `actions/cache` sautait leur sauvegarde post-job : ce qu'ils téléchargeaient
n'était jamais persisté (~438 Mo re-téléchargés par run, confirmé par le run
32136438841).

Le correctif donne aux amendements leur propre clé et **énumère explicitement**
les répertoires cachés par les autres jobs — sans quoi ils ré-embarqueraient
`amendements_an` et déplaceraient le problème au lieu de le résoudre.

Le revers de l'énumération est qu'un nouveau `.cache/<quelque_chose>` ajouté
côté Python ne serait pas caché, **sans que rien ne le signale** : le pipeline
continuerait de fonctionner en re-téléchargeant à chaque run. D'où ce test.

Volontairement sans PyYAML (absent de requirements.txt) : une recherche
textuelle suffit et évite d'ajouter une dépendance pour un seul garde-fou.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# Jobs autorisés à cacher `.cache` en bloc, avec la raison. Le seul l'était
# `extract-senat`, qui n'écrivait rien sous `.cache` (aucune constante côté
# Sénat) : son entrée ne recopiait que ce que la restauration y avait mis. #424
# l'avait laissée en l'état plutôt que de la supprimer en effet de bord ; #528
# a retiré le job, donc l'entrée, donc la tolérance. L'ensemble redevient
# **vide** : une tolérance qui survit à son bénéficiaire est une porte ouverte
# que personne ne relit. Voir docs/decisions/retrait-senat-528.md.
JOBS_CACHE_LARGE_TOLERES: set[str] = set()


def _repertoires_cache_utilises_par_le_code() -> set[str]:
    motif = re.compile(r'Path\("\.cache"\)\s*/\s*"([a-z_]+)"')
    trouves: set[str] = set()
    for fichier in (RACINE / "src").glob("*.py"):
        trouves.update(motif.findall(fichier.read_text(encoding="utf-8")))
    return trouves


def test_le_code_declare_bien_des_repertoires_de_cache():
    """Garde-fou du garde-fou : si l'extraction ne trouve plus rien, le test
    ci-dessous passerait pour une mauvaise raison."""
    assert len(_repertoires_cache_utilises_par_le_code()) >= 5


def _chemins_caches_par_job() -> dict[str, set[str]]:
    """`{job: {sous-répertoires de .cache listés dans ses actions/cache}}`.

    Analyse par job et non sur le fichier entier : un répertoire retiré de
    l'énumération d'UN job resterait présent ailleurs, et une simple recherche
    textuelle ne verrait rien — c'est le trou qu'avait la première version de
    ce test.
    """
    par_job: dict[str, set[str]] = {}
    job = None
    dans_cache = False
    for ligne in WORKFLOW.read_text(encoding="utf-8").split("\n"):
        entete = re.match(r"^  ([a-z][a-z0-9-]*):\s*$", ligne)
        if entete:
            job = entete.group(1)
            par_job.setdefault(job, set())
        if re.match(r"^      - (uses|name):", ligne):
            dans_cache = "actions/cache" in ligne
        elif ligne.strip().startswith("uses:"):
            dans_cache = "actions/cache" in ligne
        if dans_cache and job:
            trouve = re.search(r"\.cache/([a-z_]+)", ligne)
            if trouve:
                par_job[job].add(trouve.group(1))
    return par_job


# Jobs consommant le même jeu de données source AN : leurs `path:` doivent
# rester identiques, sinon l'un d'eux re-télécharge ce que l'autre a persisté.
JOBS_AN = ("extract-an", "extract-roster-groupes")

# Jobs qui lisent les dossiers législatifs. merge-and-pivot en fait partie
# depuis #427 : `generate_gouvernement_profiles.py` appelle directement
# `fetch_dossiers_gouvernementaux()`, et sans cache ce job re-téléchargeait les
# 3 archives à chaque run — avec, à la clé, l'écrasement des textes de
# gouvernement en cas d'échec réseau.
JOBS_DOSSIERS = ("extract-an", "extract-roster-groupes", "merge-and-pivot")


def test_les_deux_jobs_an_cachent_exactement_les_memes_repertoires():
    par_job = _chemins_caches_par_job()
    ensembles = {job: par_job.get(job, set()) for job in JOBS_AN}
    reference, *autres = ensembles.values()
    assert all(e == reference for e in autres), (
        f"Les jobs AN divergent sur les répertoires cachés : {ensembles}. "
        "extract-roster-groupes consomme le même jeu de données que extract-an "
        "(#424) : une divergence signifie qu'un des deux re-télécharge."
    )


def test_tous_les_repertoires_de_cache_sont_couverts_par_le_workflow():
    """Chaque `.cache/<dir>` du code doit être caché par au moins un job.

    Sans cela il serait re-téléchargé à chaque run **sans aucun signal** — le
    pipeline continuerait de fonctionner, simplement plus lentement et plus
    exposé aux coupures réseau de data.assemblee-nationale.fr.
    """
    par_job = _chemins_caches_par_job()
    couverts: set[str] = set().union(*par_job.values()) if par_job else set()
    manquants = sorted(_repertoires_cache_utilises_par_le_code() - couverts)
    assert not manquants, (
        f"Répertoires de cache absents de {WORKFLOW.name} : {manquants}. "
        "Les ajouter au `path:` du job qui les produit (#424)."
    )


def test_amendements_ont_leur_propre_cle_de_cache():
    """Le cœur de #424 : si les amendements repassaient sous la clé AN, les
    jobs qui la partagent recommenceraient à ne jamais sauvegarder."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "public-data-cache-amendements-" in workflow

    # Aucun bloc `path:` contenant amendements_an ne doit porter la clé AN.
    for bloc in re.split(r"\n      - (?:uses|name):", workflow):
        if ".cache/amendements_an" not in bloc:
            continue
        if "public-data-cache-an-" in bloc and "cache@" in bloc:
            raise AssertionError(
                "Un actions/cache couvre à la fois .cache/amendements_an et la "
                "clé public-data-cache-an-* : c'est exactement la configuration "
                "qui empêchait extract-an de sauvegarder son cache (#424)."
            )


def test_pas_de_cache_large_non_declare():
    """`path: .cache` en bloc ré-embarque les amendements. Toute nouvelle
    occurrence doit être un choix explicite, pas une régression."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    jobs_larges: set[str] = set()
    job_courant = None
    for ligne in workflow.split("\n"):
        entete = re.match(r"^  ([a-z][a-z0-9-]*):\s*$", ligne)
        if entete:
            job_courant = entete.group(1)
        if ligne.strip() == "path: .cache" and job_courant:
            jobs_larges.add(job_courant)

    assert jobs_larges <= JOBS_CACHE_LARGE_TOLERES, (
        f"Jobs cachant `.cache` en bloc sans justification : "
        f"{sorted(jobs_larges - JOBS_CACHE_LARGE_TOLERES)}."
    )


def test_les_jobs_lisant_les_dossiers_les_cachent_tous():
    """#427 : merge-and-pivot était le seul job sans aucun actions/cache."""
    par_job = _chemins_caches_par_job()
    sans_cache = sorted(j for j in JOBS_DOSSIERS if "dossiers_an" not in par_job.get(j, set()))
    assert not sans_cache, (
        f"Jobs lisant les dossiers législatifs sans les cacher : {sans_cache}. "
        "Ils re-téléchargent ~33 Mo par run et s'exposent à un échec réseau "
        "dont la conséquence, côté merge-and-pivot, est l'écrasement des "
        "textes de gouvernement (#427)."
    )


def test_les_dossiers_ont_leur_propre_cle():
    """Restaurer `public-data-cache-an-*` pour obtenir les dossiers
    embarquerait aussi `scrutins_an` : plusieurs centaines de Mo pour en
    utiliser 46."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "public-data-cache-dossiers-" in workflow

    for bloc in re.split(r"\n      - (?:uses|name):", workflow):
        if ".cache/dossiers_an" not in bloc or "cache@" not in bloc:
            continue
        assert "public-data-cache-an-" not in bloc, (
            "Un actions/cache couvre .cache/dossiers_an sous la clé AN : les "
            "dossiers doivent garder leur clé dédiée (#427)."
        )


# ---------------------------------------------------------------------------
# Découplage écrasement / purge du cache (#440, redécoupé par #578)
#
# `existing_profiles=overwrite` écrit par-dessus l'existant ; `cold_start`
# purge les caches de téléchargement. Ce sont deux axes, et les quatre
# combinaisons ont un sens — « écraser sans purger le cache » étant la plus
# courante : on réécrit à partir d'archives déjà téléchargées.
# ---------------------------------------------------------------------------

RETRY = RACINE / ".github" / "workflows" / "retry-generate-data.yml"


def test_l_ecrasement_se_demande_sans_purger_le_cache():
    """Écraser les profils et purger le cache sont deux besoins distincts : la
    correction de clé de #440 impose le premier, alors que purger obligerait à
    re-télécharger ~300 Mo auprès d'une source dont l'indisponibilité a déjà
    bloqué trois chantiers."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "      existing_profiles:" in workflow
    assert "          - overwrite\n" in workflow, (
        "l'écrasement n'est plus une valeur de l'axe 1 : la correction de clé "
        "de #440 n'est plus demandable."
    )


def test_l_axe_d_ecriture_ne_purge_jamais_le_cache():
    """L'invariant central de ce découplage. Un step de nettoyage conditionné à
    `existing_profiles` annulerait tout l'intérêt du mode."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    for bloc in re.split(r"\n      - name: ", workflow):
        if not bloc.startswith("Nettoyage"):
            continue
        entete = bloc.split("\n", 1)[0]
        condition = re.search(r"if:\s*\$\{\{([^}]+)\}\}", bloc)
        assert condition, f"step de nettoyage sans condition : {entete}"
        assert "existing_profiles" not in condition.group(1), (
            f"le step « {entete} » purge sur l'axe 1 — or l'écrasement existe "
            "précisément pour réécrire SANS re-télécharger (#440)."
        )


def test_tous_les_no_merge_suivent_le_meme_axe():
    """`--no-merge` est posé par l'axe 1, et par lui seul (#578).

    Un job qui regarderait un autre signal — `cold_start`, hier — fusionnerait
    alors que les autres écrasent, ou l'inverse : les doublons que #440 corrige,
    sur ce job-là seulement, ce qui est d'autant plus difficile à voir.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")
    lignes = [l for l in workflow.split("\n") if "MERGE_FLAG=(--no-merge)" in l]
    assert lignes, "aucun MERGE_FLAG trouvé — le test ne vérifie plus rien"
    for ligne in lignes:
        assert ligne.strip() == '[[ "$OVERWRITE" == "true" ]] && MERGE_FLAG=(--no-merge)', (
            f"condition divergente : {ligne.strip()}"
        )


def test_le_retry_reconstruit_l_axe_1():
    """Sans cette reconstruction, un run `overwrite` préempté serait relancé en
    fusion additive — exactement le scénario de doublons que ce mode existe
    pour éviter."""
    retry = RETRY.read_text(encoding="utf-8")
    assert "existing_profiles=$(echo \"$roster_log\"" in retry
    assert "-f existing_profiles=" in retry, "l'input n'est pas transmis à la relance"


def test_le_retry_lit_les_logs_avant_d_en_deduire_l_axe_1():
    """La reconstruction s'appuie sur `roster_log` et sur `an_log` : les placer
    avant leur définition la rendrait toujours fausse, silencieusement."""
    retry = RETRY.read_text(encoding="utf-8")
    deduction = retry.index("existing_profiles=$(echo \"$roster_log\"")
    assert retry.index("an_log=$(job_log") < deduction
    assert retry.index("roster_log=$(job_log") < deduction


def test_le_job_roster_ne_pose_jamais_skip_existing_en_dur():
    """`--skip-existing` s'applique AVANT `--no-merge` : posé en dur, il saute
    les profils déjà committés — exactement ceux qu'une correction de fond doit
    atteindre (#445). Le remettre en dur rendrait la clé corrigée de #440 non
    propageable, sans qu'aucun log ne le signale."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "--skip-existing --resume" not in workflow, (
        "--skip-existing est de nouveau posé en dur sur le job roster : "
        "aucune combinaison d'inputs ne peut plus régénérer l'existant."
    )
    assert '"${POP_FLAG[@]}" --resume' in workflow, (
        "la population n'est plus transmise à generate_all_profiles.py"
    )


def test_les_deux_drapeaux_de_population_ne_cohabitent_jamais():
    """`--refresh-existing` et `--skip-existing` s'annulent, et le script
    refuse la combinaison : les laisser cohabiter ferait échouer le job roster
    au démarrage (#445). Depuis #578 c'est structurel — une seule affectation
    de `POP_FLAG` est atteinte par run."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    lignes = [l.strip() for l in workflow.split("\n") if l.strip().startswith("POP_FLAG=")]
    assert lignes == ["POP_FLAG=()", "POP_FLAG=(--skip-existing)", "POP_FLAG=(--refresh-existing)"], (
        f"les affectations de POP_FLAG ont changé de forme : {lignes}"
    )
