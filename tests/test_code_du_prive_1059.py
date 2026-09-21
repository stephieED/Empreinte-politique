"""Le run prend son code sur le dépôt privé, ses données sur le public (#1059).

Ces gardes tiennent trois promesses que rien d'autre ne tient :

1. **un seul code pour tout le run** — le SHA est épinglé par un job de tête et
   tous les autres en dépendent. Résolu par job, un merge pendant le run
   donnerait des extractions faites avec un code et une fusion faite avec un
   autre : l'état mixte que #390 a écarté ;
2. **les données ne sont jamais superposées** — elles viennent du dépôt public,
   seule copie à jour ; les écraser par la copie du privé ferait repartir la
   fusion additive d'un état périmé ;
3. **le code entre dans le commit final** — sans quoi le public porterait des
   données produites par un code qu'il ne contient pas, ce qui est le défaut
   que ce lot corrige.

Écrit **sans PyYAML**, comme les autres `test_ci_*` : la bibliothèque n'est pas
dans `requirements.txt`, et un test qui en dépend ne tourne que sur les postes
qui l'ont.
"""

import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
ACTION = RACINE / ".github" / "actions" / "code-du-prive" / "action.yml"

JOB_DE_TETE = "epingler-le-code"
#: Les deux répertoires que la superposition ne doit jamais toucher. Même
#: constante que `DONNEES` dans `scripts/sync_depots.sh` et dans l'action.
DONNEES = ("pivot_data", "raw_data")


def _texte_workflow() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _jobs() -> dict[str, list[str]]:
    """`{nom du job: ses needs}`, relevé à l'indentation plutôt qu'avec PyYAML.

    Les deux formes du champ sont lues : `needs: un-job` et
    `needs: [a, b]`. Un job sans `needs:` rend une liste vide.
    """
    jobs: dict[str, list[str]] = {}
    courant = None
    dans_les_jobs = False
    for ligne in _texte_workflow().splitlines():
        if ligne.rstrip() == "jobs:":
            dans_les_jobs = True
            continue
        if not dans_les_jobs:
            continue
        entete = re.match(r"^  ([a-z][a-z0-9_-]*):\s*$", ligne)
        if entete:
            courant = entete.group(1)
            jobs[courant] = []
            continue
        besoins = re.match(r"^    needs: (.+)$", ligne)
        if besoins and courant:
            valeur = besoins.group(1).strip().strip("[]")
            jobs[courant] = [v.strip() for v in valeur.split(",") if v.strip()]
    return jobs


def test_tous_les_jobs_dependent_du_job_de_tete():
    """Un job qui n'en dépend pas superposerait un SHA vide, donc aucun code.

    Le symptôme serait muet : le job tournerait sur le code PUBLIÉ, plus
    ancien, et le commit final publierait un code qui n'a pas produit ces
    données.
    """
    jobs = _jobs()
    assert JOB_DE_TETE in jobs, "le job qui épingle le code doit exister"
    assert len(jobs) > 5, f"relevé incomplet : {sorted(jobs)}"
    orphelins = [nom for nom, besoins in jobs.items()
                 if nom != JOB_DE_TETE and JOB_DE_TETE not in besoins]
    assert not orphelins, (
        f"ces jobs ne dépendent pas de `{JOB_DE_TETE}` : {sorted(orphelins)} — ils "
        "tourneraient sur le code publié, sans que rien ne le dise"
    )


def test_chaque_checkout_est_suivi_de_la_superposition():
    """Un checkout sans superposition, c'est un job qui tourne sur l'ancien code.

    Le compte des deux doit coïncider : c'est la seule vérification qui survit
    à l'ajout d'un job, là où une liste de jobs se périmerait.
    """
    texte = _texte_workflow()
    checkouts = len(re.findall(r"^      - uses: actions/checkout@", texte, re.MULTILINE))
    superpositions = len(re.findall(r"^      - uses: \./\.github/actions/code-du-prive$",
                                    texte, re.MULTILINE))
    assert checkouts, "aucun checkout relevé : le relevé s'est cassé"
    assert superpositions == checkouts, (
        f"{checkouts} checkout(s) pour {superpositions} superposition(s) : un job "
        "tournerait sur le code publié au lieu du code du run"
    )


def test_la_superposition_recoit_le_sha_epingle_et_jamais_une_branche():
    """`main` passé ici rouvrirait la fenêtre que le job de tête ferme."""
    texte = _texte_workflow()
    # Seuls les passages À L'ACTION comptent : la sortie du job de tête
    # (`steps.resolu.outputs.sha`) porte le même nom de clé.
    passages = re.findall(
        r"- uses: \./\.github/actions/code-du-prive\n\s+with:\n\s+sha: \$\{\{ ([^}]+) \}\}",
        texte)
    assert passages, "aucun passage de SHA relevé"
    for passage in passages:
        assert passage.strip() == f"needs.{JOB_DE_TETE}.outputs.sha", (
            f"la superposition reçoit `{passage.strip()}` : seul le SHA épinglé "
            "garantit que tous les jobs partagent le même code"
        )


def test_la_superposition_exclut_les_deux_repertoires_de_donnees():
    """Les données viennent du public. Les superposer ferait repartir la fusion
    additive d'une copie périmée — et `rsync --delete` en supprimerait la part
    que le privé n'a pas."""
    action = ACTION.read_text(encoding="utf-8")
    declaration = re.search(r"^\s*DONNEES=\(([^)]*)\)", action, re.MULTILINE)
    assert declaration, "la constante DONNEES doit rester lisible par une garde"
    assert tuple(declaration.group(1).split()) == DONNEES, (
        f"DONNEES vaut ({declaration.group(1)}) dans l'action — les deux répertoires "
        "de données doivent en être, et eux seuls"
    )
    assert "--delete" in action, (
        "sans `--delete`, un fichier supprimé sur le privé survivrait indéfiniment "
        "dans le code publié"
    )


def test_le_code_entre_dans_le_commit_final():
    """Le commit doit porter le code ET les données, par exclusion des données.

    Une liste de répertoires de code se périmerait au premier répertoire ajouté
    à la racine ; l'exclusion, non.
    """
    texte = _texte_workflow()
    ligne = next((l for l in texte.splitlines() if "git add -A" in l), None)
    assert ligne, (
        "le commit final ne stage plus le code : le dépôt public porterait des "
        "données produites par un code qu'il ne contient pas"
    )
    for donnee in DONNEES:
        assert f"':(exclude){donnee}'" in ligne, (
            f"`{donnee}` doit être exclu de ce `git add` — il a sa propre ligne, "
            "explicite, juste au-dessus"
        )


def test_le_jeton_est_en_lecture_seule_et_nomme():
    """Le secret est nommé une seule fois dans le workflow et dans l'action.

    `WORKFLOW_PAT` ne doit pas servir ici : c'est un jeton en écriture, fait
    pour l'action Claude interactive. Le montage n'a besoin que de lire.
    """
    texte = _texte_workflow()
    assert "secrets.SRC_READ_TOKEN" in texte
    superposition = re.findall(r"token: \$\{\{ secrets\.([A-Z_]+) \}\}", texte)
    assert superposition, "la superposition doit recevoir un jeton"
    assert set(superposition) == {"SRC_READ_TOKEN"}, (
        f"jetons passés à la superposition : {sorted(set(superposition))} — seul un "
        "jeton de LECTURE doit atteindre ce chemin"
    )
