"""Garde-fou #505 : un job ne peut plus écrire une clé de cache pour un
répertoire qu'il ne remplit pas.

Contexte — la même faute, trois fois.

#412 §2.3 soupçonne que `extract-amendements-an`, écrivant le premier la clé
hebdomadaire partagée, empêche les autres jobs de sauvegarder la leur. La
réserve est laissée ouverte faute de log. #424 la confirme (run 32136438841,
~438 Mo re-téléchargés par run) et la corrige en donnant aux amendements leur
propre clé. Un commentaire est alors écrit dans `generate-data.yml` pour
expliquer que le même défaut ne peut pas se reproduire sur la clé des dossiers
législatifs : « il n'y a ici aucune dissociation entre producteur de contenu et
écrivain de clé : les trois jobs téléchargent et consomment les mêmes
archives ».

Ce commentaire était vrai le jour où il a été écrit. #357 avait déjà mis
`extract-roster-groupes` en mode léger (`--skip-interventions
--skip-dossiers-legislatifs` en dur) : ce job ne télécharge donc ni les débats,
ni les questions, ni les dossiers — trois des chemins qu'il déclare cacher.
Personne n'a relu l'affirmation, et #498 a retrouvé le défaut sur les
interventions.

Ce que ce fichier impose n'est pas la correction de #505 mais **sa classe** :

1. tout step `actions/cache` du workflow est inventorié ici, avec son job et
   son sens (sauvegarde ou restauration seule) ;
2. un step qui SAUVEGARDE ne peut lister que des répertoires que son job
   remplit réellement — déduit des drapeaux `--skip-*` lus dans le job lui-même,
   pas d'une liste recopiée ;
3. un répertoire qu'un job ne remplit que dans un MODE doit voir ce mode
   figurer dans la clé, sans quoi le premier run de la semaine fige l'entrée
   pour tous les autres. C'est le défaut mesuré de #505 : l'entrée
   `public-data-cache-an-2026-W34` (21 881 332 o) a été écrite en mode par
   défaut, sans débats ni questions, et les deux runs en mode interventions du
   20/08/2026 l'ont touchée sans jamais pouvoir sauver la leur.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`test_ci_cache_paths.py`, `test_ci_budget_interventions.py` et
`test_ci_interventions_par_job.py`. Aucune lecture du corpus, aucun réseau : le
workflow est lu comme du texte.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# ---------------------------------------------------------------------------
# Ce qui produit quoi
# ---------------------------------------------------------------------------

# `.cache/<répertoire>` -> drapeau CLI qui en supprime le remplissage.
# Un job qui porte ce drapeau ne peut pas produire ce répertoire, et n'a donc
# rien à sauvegarder sous une clé qui le couvre.
SUPPRIME_PAR = {
    "questions_an": "--skip-interventions",
    "syceron_an": "--skip-interventions",
    "dossiers_an": "--skip-dossiers-legislatifs",
}

# Trois états possibles d'un répertoire vis-à-vis d'un job.
PRODUIT_TOUJOURS = "produit à chaque run"
PRODUIT_SELON_MODE = "produit seulement dans un mode"
JAMAIS_PRODUIT = "jamais produit (drapeau --skip-* en dur)"

# L'INVENTAIRE des steps de cache. Une entrée par step, clé `(job, rang du step
# de cache dans le job)`, valeur : True s'il sauvegarde, False s'il est en
# restauration seule (`actions/cache/restore`).
#
# Ajouter un step de cache sans l'inscrire ici fait échouer
# `test_l_inventaire_des_steps_de_cache_est_a_jour` : le sens de lecture ou
# d'écriture devient une décision écrite, pas un défaut hérité.
INVENTAIRE_STEPS = {
    # #550 : le cache AN est passé en restore + save explicites. La clé
    # RESTAURÉE porte la complétude ATTENDUE, la clé SAUVEGARDÉE la complétude
    # ATTEINTE : deux clés différentes, qu'un `actions/cache` combiné ne sait
    # pas exprimer. C'est ce qui empêche une entrée partielle d'occuper la clé
    # d'une entrée complète — et, une entrée de cache GitHub étant immuable, la
    # seule façon de reprendre la main sur une clé déjà écrite dans la semaine.
    ("extract-an", 0): False,  # cache AN : restauration
    ("extract-an", 1): True,   # cache dossiers : produit aussi
    ("extract-ue-officiel", 0): True,
    ("extract-parltrack", 0): True,
    # #885 : l'export du Sénat est régénéré chaque nuit, d'où une clé au JOUR
    # là où ParlTrack se contente de la semaine. Producteur-écrivain : le job
    # télécharge et remplit son cache.
    ("extract-senat", 0): True,
    ("extract-amendements-an", 0): True,
    # #505 : le job roster ne produit ni questions/débats (--skip-interventions)
    # ni dossiers (--skip-dossiers-legislatifs). Restauration seule sur les deux.
    ("extract-roster-groupes", 0): False,
    ("extract-roster-groupes", 1): False,
    # Repli #424 : lecture seule explicite, ce job ne produit pas d'amendements.
    ("extract-roster-groupes", 2): False,
    # Repli #424, même step côté extract-an.
    ("extract-an", 2): False,
    # #550 : la sauvegarde du cache AN, placée APRÈS la publication du profil
    # pour qu'un archivage coupé par `timeout-minutes` ne coûte jamais qu'une
    # entrée de cache. Ce job reste le seul écrivain de la clé AN.
    ("extract-an", 3): True,
    ("merge-and-pivot", 0): True,   # dossiers : produits par ce job (#427)
    # #827 : les documents européens. Ce job est bien leur écrivain — c'est
    # `enregistrer_resolveur_europarl()`, en fin de `generate_all_profiles`,
    # qui pose `.cache/europarl/documents_doceo.json`. Il sauvegarde donc ce
    # qu'il remplit, ce qu'exige la règle de #505.
    ("merge-and-pivot", 1): True,
    # #901 : la même clé européenne, sauvegardée TÔT (`actions/cache/save`, en
    # `if: always()`) juste après la passe des domaines EuroVoc des dossiers.
    # Le run 35231390627 a été annulé au-delà des 120 minutes, et le post-job,
    # qui n'enregistre qu'en cas de succès, a perdu 1 501 réponses. Toujours le
    # même écrivain, sous une clé suffixée `-dossiers`.
    ("merge-and-pivot", 2): True,
}

# Jobs autorisés à cacher `.cache` EN BLOC. Le seul l'était `extract-senat`,
# sous une clé qui n'appartenait qu'à lui (`public-data-cache-senat-*`) : il ne
# pouvait affamer aucun autre job. Il a été retiré avec le Sénat (#528), et
# l'ensemble redevient **vide** — pas conservé « au cas où ». Une tolérance qui
# survit à son bénéficiaire est une porte ouverte que personne ne relit ; la
# règle, elle, porte toujours sur les clés PARTAGÉES.
# Voir docs/decisions/retrait-senat-528.md.
JOBS_CACHE_LARGE_TOLERES: set[str] = set()

# Clés partagées par plus d'un job. Pour chacune, un seul job doit sauvegarder.
CLES_PARTAGEES = ("public-data-cache-an-", "public-data-cache-dossiers-")


# ---------------------------------------------------------------------------
# Lecture du workflow
# ---------------------------------------------------------------------------


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _jobs() -> dict[str, list[str]]:
    """`{job: [lignes du job]}`, découpé sur les en-têtes de deux espaces."""
    par_job: dict[str, list[str]] = {}
    job = None
    for ligne in _yaml().split("\n"):
        entete = re.match(r"^  ([a-z][a-z0-9-]*):\s*$", ligne)
        if entete:
            job = entete.group(1)
            par_job[job] = []
            continue
        if job is not None:
            par_job[job].append(ligne)
    return par_job


def _steps_de_cache(lignes: list[str]) -> list[dict]:
    """Steps `actions/cache*` d'un job, dans l'ordre, avec sens/chemins/clé."""
    steps: list[dict] = []
    courant: dict | None = None
    for ligne in lignes:
        debut_step = re.match(r"^      - (uses|name):", ligne)
        if debut_step:
            courant = None
        if "actions/cache" in ligne and "uses:" in ligne:
            courant = {
                "sauvegarde": "actions/cache/restore@" not in ligne,
                "repertoires": set(),
                "cle": "",
                "large": False,
            }
            steps.append(courant)
            continue
        if courant is None:
            continue
        if ligne.lstrip().startswith("#"):
            # Un commentaire posé entre deux steps cite souvent le `path` du
            # step voisin : le lire attribuerait au step courant des chemins
            # qu'il ne déclare pas.
            courant = None
            continue
        trouve = re.search(r"\.cache/([a-z_]+)", ligne)
        if trouve:
            courant["repertoires"].add(trouve.group(1))
        if ligne.strip() == "path: .cache":
            courant["large"] = True
        cle = re.match(r"\s*key:\s*(.+)$", ligne)
        if cle:
            courant["cle"] = cle.group(1).strip()
    return steps


def _etat_de_production(lignes: list[str], repertoire: str) -> str:
    """Ce job produit-il `.cache/<repertoire>` — toujours, selon le mode, jamais ?

    Déduit du texte du job et non d'une liste recopiée : c'est ce qui permet à
    ce garde-fou de suivre le pipeline quand il bouge, au lieu de vieillir comme
    le commentaire que #505 a dû corriger.
    """
    drapeau = SUPPRIME_PAR.get(repertoire)
    if drapeau is None:
        return PRODUIT_TOUJOURS
    lignes_drapeau = [l for l in lignes if drapeau in l and not l.lstrip().startswith("#")]
    if not lignes_drapeau:
        return PRODUIT_TOUJOURS
    if any("inputs.collect_interventions" in l for l in lignes_drapeau):
        return PRODUIT_SELON_MODE
    return JAMAIS_PRODUIT


# ---------------------------------------------------------------------------
# Garde-fou du garde-fou
# ---------------------------------------------------------------------------


def test_le_workflow_est_lisible():
    """Si le découpage ne trouve plus ni jobs ni steps de cache, tous les tests
    ci-dessous passeraient pour une mauvaise raison (leçon de #460)."""
    jobs = _jobs()
    # 8 depuis le retrait d'`extract-senat` (#528), 9 avant.
    assert len(jobs) >= 8, f"jobs trouvés : {sorted(jobs)}"
    total = sum(len(_steps_de_cache(l)) for l in jobs.values())
    assert total >= 9, f"{total} step(s) actions/cache trouvés"


def test_l_inventaire_des_steps_de_cache_est_a_jour():
    """Ajouter un step de cache oblige à déclarer s'il sauvegarde ou non."""
    reel = {}
    for job, lignes in _jobs().items():
        for rang, step in enumerate(_steps_de_cache(lignes)):
            reel[(job, rang)] = step["sauvegarde"]
    assert reel == INVENTAIRE_STEPS, (
        "L'inventaire des steps de cache ne correspond plus au workflow.\n"
        f"  workflow  : {sorted(reel.items())}\n"
        f"  inventaire: {sorted(INVENTAIRE_STEPS.items())}\n"
        "Un step ajouté doit être inscrit ici avec son sens (#505)."
    )


# ---------------------------------------------------------------------------
# La règle de #505
# ---------------------------------------------------------------------------


def test_aucun_job_ne_sauvegarde_un_repertoire_qu_il_ne_remplit_pas():
    """LA règle. C'est #424 (amendements), puis #498/#505 (interventions), puis
    les dossiers du job roster : à chaque fois un job écrivait la clé d'un
    contenu produit par quelqu'un d'autre, et `actions/cache` sautait la
    sauvegarde de ceux qui, eux, l'avaient téléchargé."""
    fautes = []
    for job, lignes in _jobs().items():
        for step in _steps_de_cache(lignes):
            if not step["sauvegarde"] or job in JOBS_CACHE_LARGE_TOLERES:
                continue
            for repertoire in sorted(step["repertoires"]):
                if _etat_de_production(lignes, repertoire) == JAMAIS_PRODUIT:
                    fautes.append(
                        f"{job} sauvegarde `{step['cle']}` en couvrant "
                        f".cache/{repertoire}, qu'il ne remplit jamais "
                        f"({SUPPRIME_PAR[repertoire]} en dur)"
                    )
    assert not fautes, (
        "Dissociation producteur/écrivain de clé :\n  - " + "\n  - ".join(fautes)
        + "\nPasser ce step en `actions/cache/restore@v5` (#505)."
    )


def test_un_repertoire_produit_selon_le_mode_impose_le_mode_dans_la_cle():
    """Le défaut mesuré de #505. `.cache/questions_an` et `.cache/syceron_an` ne
    sont remplis que si `collect_interventions` est coché ; tant que la clé ne
    portait que la semaine ISO, le premier run de la semaine figeait l'entrée
    pour les six jours suivants — et le mode par défaut étant celui qui tourne
    le plus souvent, l'entrée figée était celle SANS interventions."""
    fautes = []
    for job, lignes in _jobs().items():
        for step in _steps_de_cache(lignes):
            if not step["sauvegarde"] or job in JOBS_CACHE_LARGE_TOLERES:
                continue
            selon_mode = sorted(
                r for r in step["repertoires"]
                if _etat_de_production(lignes, r) == PRODUIT_SELON_MODE
            )
            if selon_mode and "inputs.collect_interventions" not in step["cle"]:
                fautes.append(
                    f"{job} sauvegarde `{step['cle']}` en couvrant "
                    f"{selon_mode} sans que le mode figure dans la clé"
                )
    assert not fautes, (
        "Clé de cache muette sur le mode qui détermine son contenu :\n  - "
        + "\n  - ".join(fautes)
        + "\nUn run en mode interventions ferait alors un *exact key hit* sur "
        "une entrée sans interventions et ne sauvegarderait jamais la sienne "
        "(#424, reparu en #505)."
    )


@pytest.mark.parametrize("prefixe", CLES_PARTAGEES)
def test_tout_ecrivain_d_une_cle_partagee_en_produit_le_contenu(prefixe):
    """Plusieurs écrivains sur une même clé ne sont PAS un défaut en soi : sur
    `public-data-cache-dossiers-*`, extract-an et merge-and-pivot téléchargent
    tous deux les dossiers, donc le premier qui sauvegarde suffit et l'exact key
    hit du second ne perd rien. C'est exactement ce que le commentaire corrigé
    par #505 voulait dire — il se trompait seulement sur la liste des
    producteurs. Ce qui est un défaut, c'est un écrivain qui NE produit pas."""
    fautes = []
    for job, lignes in _jobs().items():
        for step in _steps_de_cache(lignes):
            if not step["sauvegarde"] or prefixe not in step["cle"]:
                continue
            non_produits = sorted(
                r for r in step["repertoires"]
                if _etat_de_production(lignes, r) == JAMAIS_PRODUIT
            )
            if non_produits:
                fautes.append(f"{job} écrit `{prefixe}*` sans produire {non_produits}")
    assert not fautes, (
        f"Écrivain non producteur sur la clé partagée `{prefixe}*` :\n  - "
        + "\n  - ".join(fautes)
    )


def test_le_job_roster_ne_sauvegarde_aucun_cache():
    """La régression exacte de #505, nommée. Ce job porte `--skip-interventions`
    ET `--skip-dossiers-legislatifs` en dur : il ne produit rien qui ne soit
    déjà produit par extract-an, qui le précède par `needs:`. Le remettre en
    `actions/cache@v5` rétablirait la dissociation — aujourd'hui masquée par
    l'ordonnancement, mais un `prepare-an-matrix` rendant une liste vide skippe
    extract-an et laisse le roster écrire la clé de la semaine sur du vide."""
    lignes = _jobs()["extract-roster-groupes"]
    steps = _steps_de_cache(lignes)
    assert steps, "aucun step de cache trouvé — le test ne vérifie plus rien"
    sauvegardes = [s["cle"] for s in steps if s["sauvegarde"]]
    assert not sauvegardes, (
        f"extract-roster-groupes sauvegarde à nouveau : {sauvegardes}."
    )


def test_le_commentaire_des_trois_jobs_ne_revient_pas():
    """L'affirmation qui a rendu #505 possible, mot pour mot. Elle a survécu à
    #357 (qui l'a rendue fausse) et à #424 (qui l'a citée), parce que rien ne la
    relisait. Ce test la relit."""
    yaml = _yaml()
    assert "les trois\n      # jobs téléchargent et consomment les mêmes archives" not in yaml, (
        "Le commentaire « les trois jobs téléchargent et consomment les mêmes "
        "archives » est de retour. Il est faux depuis #357 : "
        "extract-roster-groupes porte --skip-dossiers-legislatifs en dur."
    )
