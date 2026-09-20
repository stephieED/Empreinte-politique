"""Garde-fou #555 : le préfixe nu RESTE, et un marqueur de fraîcheur le borne.

Le défaut, mesuré. Run `32738726729` du 24/08/2026 (lundi, première exécution
de la semaine W35), shard `jean-luc-melenchon`, job `97468417763` :

    14:28:54  Cache hit for restore-key: public-data-cache-an-2026-W34
    14:28:54  Cache restored from key: public-data-cache-an-2026-W34
    14:28:58  Extraction AN — début
    14:29:09  Elapsed (wall clock) time: 0:10.12   ← aucune archive rouverte
    14:29:12  Cache saved with key: public-data-cache-an-2026-W35

La dernière ligne des `restore-keys` est un préfixe nu, sans borne de semaine :
`actions/cache` sert l'entrée la plus récente qui commence par lui. La clé
hebdomadaire, seul mécanisme de fraîcheur des index AN, ne périme donc rien —
chaque semaine blanchit le contenu de la précédente sous son propre nom.

Ce fichier tient les DEUX moitiés de la correction, qui n'ont de sens
qu'ensemble :

1. **Le préfixe nu reste.** Le retirer réglerait la fraîcheur en rouvrant #424
   (~438 Mo re-téléchargés) et jetterait chaque semaine les index des
   législatures CLOSES, dont le réchauffement inter-semaines est légitime :
   244 s de réindexation là où 42 s suffisent (mesures #550).
2. **Un step de fraîcheur suit chaque restauration AN**, lit la semaine de la
   clé effectivement restaurée (`cache-matched-key`) et périme le seul contenu
   qui vieillit — dans le job PRODUCTEUR uniquement.

L'asymétrie du point 2 est la règle de #424/#505 appliquée à la fraîcheur :
`extract-roster-groupes` est en restauration seule, il ne sauvegarde rien, donc
y périmer ferait retélécharger par 8 shards sans rien persister en retour.

Volontairement sans PyYAML (absent de `requirements.txt`), comme
`test_ci_cache_paths.py`, `test_ci_cache_producteur_ecrivain.py` et
`test_ci_cache_completude_550.py` : le workflow est lu comme du texte.
"""

import re
from pathlib import Path

import pytest

import cache_an_fraicheur as fr

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
MODULE = RACINE / "src" / "cache_an_fraicheur.py"

#: Les deux jobs qui restaurent la clé AN partagée. Le premier la produit et la
#: sauvegarde, le second la consomme seulement (#505).
JOB_PRODUCTEUR = "extract-an"
JOB_CONSOMMATEUR = "extract-roster-groupes"

#: Le step qui ouvre réellement les archives, dans chaque job. La péremption
#: doit le PRÉCÉDER : placée après, elle jetterait ce que le job vient de
#: construire.
STEP_EXTRACTION = {
    JOB_PRODUCTEUR: "Extraction AN",
    JOB_CONSOMMATEUR: "Extraction roster-driven",
}


def _job(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    bloc = re.search(
        rf"^  {re.escape(nom)}:\n(.*?)(?=\n  [a-z][a-z0-9-]*:\n)", texte, flags=re.S | re.M
    )
    assert bloc, f"Job `{nom}` introuvable dans generate-data.yml."
    return bloc.group(1)


def _steps(nom: str) -> list[str]:
    """Les steps d'un job, dans l'ordre, **commentaires retirés**.

    Le découpage se fait sur `- uses:` / `- name:` : les commentaires qui
    PRÉCÈDENT un step tombent donc à la fin du chunk du step précédent. Les
    garder ferait repérer un step par le commentaire qui l'annonce — c'est
    exactement ce qui a fait échouer la première version de ce fichier, et
    c'est le genre de faux positif qui rend un garde-fou muet.
    """
    morceaux = re.split(r"\n(?=      - (?:uses|name):)", "\n" + _job(nom))
    return [
        "\n".join(l for l in m.split("\n") if not l.strip().startswith("#"))
        for m in morceaux
        if m.strip().startswith("- ")
    ]


def _rang(steps: list[str], motif: str) -> int:
    trouves = [i for i, step in enumerate(steps) if motif in step]
    assert len(trouves) == 1, f"{len(trouves)} step(s) contiennent « {motif} » (attendu : 1)."
    return trouves[0]


def _rang_restauration_an(steps: list[str]) -> int:
    """Le step `actions/cache/restore` qui porte la clé AN partagée."""
    trouves = [
        i
        for i, step in enumerate(steps)
        if "actions/cache/restore" in step and "key: public-data-cache-an-" in step
    ]
    assert len(trouves) == 1, f"{len(trouves)} restauration(s) du cache AN (attendu : 1)."
    return trouves[0]


# ---------------------------------------------------------------------------
# Garde-fou du garde-fou
# ---------------------------------------------------------------------------


def test_le_workflow_est_lisible():
    """Si le découpage ne trouve plus les jobs ni leurs steps, tous les tests
    ci-dessous passeraient pour une mauvaise raison (leçon de #460)."""
    for job in (JOB_PRODUCTEUR, JOB_CONSOMMATEUR):
        steps = _steps(job)
        assert len(steps) >= 8, f"{job} : {len(steps)} step(s) trouvés"
        assert _rang(steps, STEP_EXTRACTION[job]) >= 0


# ---------------------------------------------------------------------------
# 1. Le préfixe nu reste — ne pas rouvrir #424
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("job", [JOB_PRODUCTEUR, JOB_CONSOMMATEUR])
def test_le_prefixe_nu_reste_la_derniere_cle_de_repli(job):
    """La correction de #555 ne doit PAS être « retirer la dernière ligne ».

    Sans elle, le premier run de chaque semaine repart d'un cache AN vide et
    retélécharge les archives — c'est #424, et c'est ce que ce préfixe a été
    mis là pour éviter. Il porte aussi les index des législatures closes, dont
    le réchauffement inter-semaines est légitime et gratuit.
    """
    steps = _steps(job)
    restauration = steps[_rang_restauration_an(steps)]
    lignes = [l.strip() for l in restauration.split("\n") if l.strip()]
    assert f"{fr.PREFIXE_CLE_AN}" in lignes, (
        f"{job} : le préfixe nu `{fr.PREFIXE_CLE_AN}` a disparu des `restore-keys`. "
        "Retirer la ligne règle la fraîcheur en rouvrant #424 (~438 Mo par run) et "
        "en jetant chaque semaine 202 s d'index de législatures closes. "
        "Voir docs/decisions/cache-fraicheur-interventions-555.md."
    )


def test_le_prefixe_du_module_est_celui_du_workflow():
    """La semaine se lit dans la clé restaurée : si le workflow renommait ses
    clés sans que le module suive, plus aucune semaine ne serait lisible, donc
    toute restauration serait déclarée périmée — une réindexation à chaque run,
    et silencieuse."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    assert f"key: {fr.PREFIXE_CLE_AN}" in texte


# ---------------------------------------------------------------------------
# 2. Un marqueur de fraîcheur borne le préfixe nu
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("job", [JOB_PRODUCTEUR, JOB_CONSOMMATEUR])
def test_un_step_de_fraicheur_suit_immediatement_la_restauration_an(job):
    """Immédiatement : tout step glissé entre les deux lirait un cache dont
    personne n'a encore dit l'âge."""
    steps = _steps(job)
    restauration = _rang_restauration_an(steps)
    fraicheur = _rang(steps, "cache_an_fraicheur.py")
    assert fraicheur == restauration + 1, (
        f"{job} : le step de fraîcheur est au rang {fraicheur}, la restauration AN "
        f"au rang {restauration}. Il doit la suivre immédiatement (#555)."
    )


@pytest.mark.parametrize("job", [JOB_PRODUCTEUR, JOB_CONSOMMATEUR])
def test_la_fraicheur_precede_l_extraction(job):
    """Placée après l'extraction, la péremption jetterait ce que le job vient
    de construire — et le job sauvegarderait un cache vide."""
    steps = _steps(job)
    assert _rang(steps, "cache_an_fraicheur.py") < _rang(steps, STEP_EXTRACTION[job])


@pytest.mark.parametrize("job", [JOB_PRODUCTEUR, JOB_CONSOMMATEUR])
def test_la_fraicheur_lit_la_cle_reellement_restauree(job):
    """`cache-matched-key` est LE marqueur, et il ne coûte rien au `path:`.

    Un fichier sentinelle aurait dû y être ajouté ; le `path:` entrant dans le
    hachage de *version* d'une entrée, la correction aurait fait perdre une
    semaine de cache rien qu'à se déployer.
    """
    steps = _steps(job)
    restauration = steps[_rang_restauration_an(steps)]
    identifiant = re.search(r"^\s*id:\s*(\S+)\s*$", restauration, flags=re.M)
    assert identifiant, f"{job} : la restauration AN n'a pas d'`id:`, sa clé est illisible."
    step = steps[_rang(steps, "cache_an_fraicheur.py")]
    assert f"steps.{identifiant.group(1)}.outputs.cache-matched-key" in step
    assert "steps.week.outputs.week" in step


def test_le_producteur_perime():
    """`extract-an` est le seul écrivain de la clé AN (#505/#550) : il paie la
    réindexation de la législature en cours et la persiste pour les autres."""
    steps = _steps(JOB_PRODUCTEUR)
    assert "--perimer" in steps[_rang(steps, "cache_an_fraicheur.py")]


def test_le_consommateur_ne_perime_pas():
    """L'asymétrie, et c'est la règle de #424/#505 appliquée à la fraîcheur :
    `extract-roster-groupes` est en restauration seule et ne sauvegarde rien.
    Y périmer ferait retélécharger ~40 Mo d'archives AN par chacun de ses 8
    shards sans que rien ne soit persisté en retour — #424 recréé, pas
    corrigé. Il déclare, il ne périme pas."""
    steps = _steps(JOB_CONSOMMATEUR)
    assert "--perimer" not in steps[_rang(steps, "cache_an_fraicheur.py")]


@pytest.mark.parametrize("job", [JOB_PRODUCTEUR, JOB_CONSOMMATEUR])
def test_la_fraicheur_ne_peut_pas_faire_echouer_un_shard(job):
    """La péremption est un rafraîchissement, pas une garde : un shard qui a
    des profils à publier ne doit jamais mourir sur elle. Même arbitrage que la
    sauvegarde explicite de #550."""
    steps = _steps(job)
    step = steps[_rang(steps, "cache_an_fraicheur.py")]
    assert "continue-on-error: true" in step


@pytest.mark.parametrize("job", [JOB_PRODUCTEUR, JOB_CONSOMMATEUR])
def test_la_fraicheur_est_sautee_en_cold_start(job):
    """`cold_start` purge déjà `.cache` en entier : il n'y a ni restauration à
    dater ni contenu à périmer."""
    steps = _steps(job)
    step = steps[_rang(steps, "cache_an_fraicheur.py")]
    assert "!inputs.cold_start" in step


# ---------------------------------------------------------------------------
# La frontière n'est pas recopiée dans le workflow
# ---------------------------------------------------------------------------


def test_aucune_liste_de_legislatures_n_est_recopiee_dans_le_workflow():
    """Même règle que l'empreinte de #550 : la frontière figé/vivant se dérive
    des constantes du code (`AN_SCRUTINS_LEGISLATURES_FIGEES`,
    `AN_AMENDEMENTS_LEGISLATURES_FIGEES`). Recopiée dans le workflow, elle
    deviendrait fausse à la clôture de la 17e sans que rien ne le dise."""
    steps = _steps(JOB_PRODUCTEUR)
    step = steps[_rang(steps, "cache_an_fraicheur.py")]
    assert not re.search(r"\b1[4-9]\b", step), (
        "Un numéro de législature est recopié dans le step de fraîcheur : "
        "la frontière doit rester dérivée du code (#555, même règle que #550)."
    )


def test_le_module_derive_la_frontiere_des_deux_referentiels():
    """Lu dans le source : le module ne doit contenir aucune liste de
    législatures en dur."""
    source = MODULE.read_text(encoding="utf-8")
    corps = source.split('"""', 2)[-1]
    assert "AN_SCRUTINS_LEGISLATURES_FIGEES" in corps
    assert "AN_AMENDEMENTS_LEGISLATURES_FIGEES" in corps
    assert not re.search(r'frozenset\(\{["\']1\d', corps), (
        "Une liste de législatures est figée dans src/cache_an_fraicheur.py."
    )
