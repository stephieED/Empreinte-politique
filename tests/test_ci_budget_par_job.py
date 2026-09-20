"""Garde-fou #514 : aucun chemin de collecte ne peut plus se retrouver sans
budget en silence.

La classe de défaut, telle qu'elle s'est produite. #500 a doté `extract-an`
d'un budget de temps mur, et l'a créé ainsi :

    budget = BudgetCollecte(...) if budget_secondes and not skip_interventions else None

Le `and not skip_interventions` était juste sur son périmètre — un budget
d'interventions n'a rien à borner quand on ne collecte pas d'interventions.
Puis #502 a posé `--skip-interventions` en dur sur `extract-senat`, pour une
raison mesurée et bonne. Personne n'a écrit que le job perdait, du même coup,
le SEUL plafond interne dont il disposait : identité, votes et dossiers n'en
avaient jamais eu. Résultat mesuré, run 32421439590 du 20/08/2026 :
15 min 18 s de `timeout-minutes` consommées, **1 profil écrit sur 13
candidats**.

Aucune des deux décisions n'était fausse. Ce qui manquait, c'est qu'aucune des
deux n'avait à se prononcer sur le budget de l'autre.

Ce que ce fichier impose : **toute** invocation de `generate_all_profiles.py`
qui collecte sur le réseau déclare son régime de budget, et ce régime est
inscrit ici. Une invocation muette fait échouer `test_l_inventaire_est_a_jour` ;
une invocation qui collecte sans rien dire du budget fait échouer
`test_aucune_collecte_ne_reste_sans_regime_de_budget`. Déclarer « pas de budget »
reste permis — c'est le cas d'`extract-an` et du job roster — mais il faut
l'écrire, `--budget-collecte-secondes 0`, et non l'obtenir en ne tapant rien.

**#528 — le job qui a produit cette issue n'existe plus.** `extract-senat` a été
retiré avec le Sénat (docs/decisions/retrait-senat-528.md), et les
quatre tests qui vérifiaient la cohérence de SES deux chiffres (160 s par
candidat, 600 s pour le job, contre un `timeout-minutes` de 15) sont partis avec
lui : ils portaient sur des valeurs, pas sur une règle. Les constantes mesurées
restent en tête de fichier — ce sont des mesures, elles ne se réécrivent pas —
et l'inventaire, lui, reste armé sur les invocations qui subsistent. Plus aucune
d'elles n'est en `REGIME_BORNE` aujourd'hui : c'est un fait du moment, pas une
permission de retirer le régime.

Même forme que `tests/test_ci_interventions_par_job.py` (#501), et pour la même
raison : c'est l'inventaire qui transforme un défaut tacite en décision. Sans
PyYAML, absent de `requirements.txt`.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SOURCE_GENERATE = RACINE / "src" / "generate_all_profiles.py"

# ---------------------------------------------------------------------------
# Les valeurs, et la population de chacune
# ---------------------------------------------------------------------------

# Préambule d'un job (checkout, bootstrap-extraction, restauration du cache).
# 6-170 s sur les 15 derniers runs portant un `extract-senat` (#501), 105 s sur
# le run 32421439590. Provision identique à `extract-an`, dont le max mesuré est
# 193 s. C'est ce que `timeout-minutes` couvre EN PLUS de la collecte, et
# l'oublier est l'erreur d'origine de #498.
PREAMBULE_PROVISIONNE_SECONDES = 240

# Dépassement possible du budget par la requête en vol. Le budget est vérifié
# ENTRE deux tentatives (`_get_payload`), donc au pire une tentative complète :
# `TIMEOUT` 15 s + `_WATCHDOG_MARGIN_SECONDS` 10 s = 25 s.
DEPASSEMENT_REQUETE_EN_VOL_SECONDES = 25

# Publication (staging depuis le manifeste + upload artifact) : 6 s mesurées
# sur le job 96594132947 (22:06:11 → 22:06:17 UTC). 30 s provisionnés.
PUBLICATION_PROVISIONNEE_SECONDES = 30

# Résolution d'identité sur SOURCE DÉGRADÉE, run 32421439590 : 103 s
# (jerome-guedj), 109 s (jean-luc-melenchon), 125 s (edouard-philippe). C'est la
# seule porte vers un profil écrit — sans identité, `build_profile_any_chambre`
# rend None et rien n'est publié.
IDENTITE_SOURCE_DEGRADEE_MAX_MESUREE = 125

# La même, sur SOURCE SAINE : 2,7 s pour les 4 requêtes de `bruno-retailleau`
# le 20/08/2026 (#501). Deux populations, deux chiffres, jamais mélangés.
COLLECTE_SOURCE_SAINE_MESUREE = 2.7

# Slugs résolvables de raw_data/candidats.json : 8 sur 13 (les 5 autres n'ont
# pas de slug et ne coûtent aucune requête).
SLUGS_RESOLVABLES = 8

# ---------------------------------------------------------------------------
# Les régimes de budget possibles
# ---------------------------------------------------------------------------

REGIME_BORNE = "--budget-collecte-secondes > 0 : collecte bornée par candidat"
REGIME_SANS_BUDGET_DECLARE = "--budget-collecte-secondes 0 : absence de budget DÉCLARÉE"
REGIME_HORS_COLLECTE_FR = "--pivot-only ou --source ue : aucune collecte FR à borner"

# L'INVENTAIRE. Une entrée par invocation de `generate_all_profiles.py` dans
# generate-data.yml, clé `(job, rang dans le job)` — même clé que #501, pour que
# les deux inventaires se lisent ensemble.
INVENTAIRE = {
    # Sa collecte est bornée par le budget d'interventions de #500 dans le mode
    # où elle coûte quelque chose (59-286 s mesurées), et mesurée à 8-18 s dans
    # le mode par défaut. Un second plafond n'aurait rien à borner de plus, et
    # les 8 shards du run 32421439590 sont en succès : on n'y touche pas.
    ("extract-an", 0): REGIME_SANS_BUDGET_DECLARE,
    ("extract-ue-officiel", 0): REGIME_HORS_COLLECTE_FR,
    # `--resume` + point de sauvegarde par membre : un shard coupé reprend au
    # run suivant. Dimensionner un budget ici demanderait une mesure sur les
    # 752 membres du roster, que #514 n'a pas relevée — et poser un chiffre
    # mesuré ailleurs est précisément ce que cette issue corrige.
    ("extract-roster-groupes", 0): REGIME_SANS_BUDGET_DECLARE,
    ("merge-and-pivot", 0): REGIME_HORS_COLLECTE_FR,
    ("merge-and-pivot", 1): REGIME_HORS_COLLECTE_FR,
}


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _blocs_de_job() -> dict[str, str]:
    texte = _yaml()
    apres_jobs = texte.split("\njobs:\n", 1)
    assert len(apres_jobs) == 2, "Section `jobs:` introuvable dans generate-data.yml."
    corps = apres_jobs[1]
    debuts = [(m.start(), m.group(1)) for m in re.finditer(r"^  ([a-z][a-z0-9-]*):\n", corps, flags=re.M)]
    assert debuts, "Aucun job détecté."
    blocs = {}
    for i, (debut, nom) in enumerate(debuts):
        fin = debuts[i + 1][0] if i + 1 < len(debuts) else len(corps)
        blocs[nom] = corps[debut:fin]
    return blocs


def _invocations() -> dict[tuple[str, int], str]:
    """`{(job, rang): commande}`, continuations `\\` recollées et commentaires
    retirés — sinon un `--budget-collecte-secondes` cité dans un commentaire
    passerait pour une déclaration."""
    trouvees: dict[tuple[str, int], str] = {}
    for nom, bloc in _blocs_de_job().items():
        recollees: list[str] = []
        tampon = ""
        for ligne in bloc.split("\n"):
            nue = ligne.strip()
            if nue.startswith("#"):
                continue
            if nue.endswith("\\"):
                tampon += nue[:-1].strip() + " "
                continue
            recollees.append((tampon + nue).strip())
            tampon = ""
        if tampon:
            recollees.append(tampon.strip())
        rang = 0
        for commande in recollees:
            if "generate_all_profiles.py" not in commande:
                continue
            trouvees[(nom, rang)] = commande
            rang += 1
    return trouvees


def _regime_observe(commande: str) -> str:
    if "--pivot-only" in commande or re.search(r"--source\s+ue\b", commande):
        return REGIME_HORS_COLLECTE_FR
    motif = re.search(r"--budget-collecte-secondes\s+(\d+)", commande)
    if motif:
        return REGIME_BORNE if int(motif.group(1)) > 0 else REGIME_SANS_BUDGET_DECLARE
    return "AUCUN RÉGIME DÉCLARÉ"


# ---------------------------------------------------------------------------
# Le garde-fou contre la classe
# ---------------------------------------------------------------------------

def test_l_inventaire_est_a_jour():
    """Une septième invocation ne peut pas apparaître sans se prononcer."""
    observees = set(_invocations())
    inventoriees = set(INVENTAIRE)
    nouvelles = observees - inventoriees
    disparues = inventoriees - observees
    assert not nouvelles, (
        f"Invocation(s) de generate_all_profiles.py absente(s) de l'INVENTAIRE : "
        f"{sorted(nouvelles)}. Décidez si ce chemin porte un budget de collecte et "
        f"inscrivez-le. C'est le silence sur cette question qui a coûté 15 minutes "
        f"de runner pour un profil à extract-senat (#514)."
    )
    assert not disparues, (
        f"L'INVENTAIRE référence des invocations qui n'existent plus : {sorted(disparues)}."
    )


@pytest.mark.parametrize("cle", sorted(INVENTAIRE))
def test_chaque_invocation_declare_le_regime_inventorie(cle):
    invocations = _invocations()
    if cle not in invocations:
        pytest.skip("couvert par test_l_inventaire_est_a_jour")
    observe = _regime_observe(invocations[cle])
    assert observe == INVENTAIRE[cle], (
        f"{cle[0]} (invocation n°{cle[1]}) : régime attendu « {INVENTAIRE[cle]} », "
        f"observé « {observe} ».\n  {invocations[cle]}"
    )


def test_aucune_collecte_ne_reste_sans_regime_de_budget():
    """La formulation directe du défaut de #514 : sur un chemin qui sort sur le
    réseau, ne rien dire du budget n'est pas un régime.

    « Pas de budget » reste une réponse recevable — elle s'écrit
    `--budget-collecte-secondes 0`.
    """
    muettes = [
        cle for cle, commande in _invocations().items()
        if _regime_observe(commande) == "AUCUN RÉGIME DÉCLARÉ"
    ]
    assert not muettes, (
        f"Invocation(s) sans régime de budget déclaré : {sorted(muettes)}. "
        f"Attendu : --budget-collecte-secondes <n>, --budget-collecte-secondes 0, "
        f"--source ue ou --pivot-only."
    )


def test_aucun_budget_n_est_neutralise_par_un_autre_drapeau():
    """L'autre moitié de #514 : un budget POSÉ mais mort. `extract-senat` ne
    doit pas cumuler `--budget-interventions-secondes` et
    `--skip-interventions` — la combinaison est d'ailleurs refusée à
    l'exécution depuis #514, ce test la refuse aussi à la lecture."""
    fautives = [
        cle for cle, commande in _invocations().items()
        if "--budget-interventions-secondes" in commande and "--skip-interventions" in commande
    ]
    assert not fautives, (
        f"{sorted(fautives)} pose un budget d'interventions sous --skip-interventions : "
        f"il serait None par construction, et donnerait l'apparence d'une protection."
    )


def test_la_fabrique_de_budget_ne_reprend_pas_de_condition_de_mode():
    """La régression exacte, au niveau du code cette fois.

    Le budget de collecte par candidat ne doit dépendre que de sa VALEUR. Le
    jour où un `and not skip_interventions` — ou tout autre drapeau — revient
    conditionner sa création, ce test tombe. C'est la ligne qui a produit #514 :
    elle rendait `None` sans que rien en aval ne distingue ce `None` d'un
    « aucun budget demandé ».
    """
    source = SOURCE_GENERATE.read_text(encoding="utf-8")
    motif = re.search(
        r"budget_collecte_candidat = creer_budget\((?P<args>[^)]*)\)", source, flags=re.S
    )
    assert motif, "création de `budget_collecte_candidat` introuvable ou réécrite."
    arguments = motif.group("args")
    assert "skip_interventions" not in arguments, (
        "La création du budget de collecte redevient conditionnelle à "
        "`skip_interventions` :\n  "
        f"{arguments.strip()}\n"
        "Une condition de mode se pose sur la valeur passée, à l'endroit qui décide "
        "du mode — pas sur la fabrique (#514)."
    )


# ---------------------------------------------------------------------------
# Les valeurs d'extract-senat : bloc RETIRÉ par #528
#
# Quatre tests vérifiaient que les deux budgets de ce job tenaient ensemble et
# tenaient dans son `timeout-minutes` : budget de job + préambule + requête en
# vol + publication <= timeout ; budget par candidat >= la résolution d'identité
# la plus chère mesurée sur source dégradée (125 s) et >= 20 × la collecte
# mesurée sur source saine ; 8 slugs × budget par candidat > budget de job (la
# raison d'en avoir deux). Le job a été retiré avec le Sénat (#528) : ces tests
# portaient sur SES chiffres, pas sur une règle transposable telle quelle.
#
# Ce qu'il faut refaire le jour où une invocation repasse en `REGIME_BORNE` :
# les quatre interlocks ci-dessus, avec les mesures de CE job-là. Les recopier
# avec les constantes du Sénat serait exactement l'erreur que #514 corrige —
# un chiffre mesuré sur une population, appliqué à une autre.
# ---------------------------------------------------------------------------
