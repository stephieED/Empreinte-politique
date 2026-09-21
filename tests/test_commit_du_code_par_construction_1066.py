"""Le commit de fin de run publie le code superposé, et rien d'autre (#1066).

Le 21/09/2026, le premier run à publier code et données ensemble (#1059) a
aussi publié **5,3 Go de `_artifacts/` et huit rapports de contrôle** : la ligne
de commit stageait « tout sauf les données » et comptait sur un `.gitignore`
qui ne couvrait ni l'un ni l'autre. La pointe du dépôt public a dû être purgée.

Le correctif stage **par construction**, et avec deux filets indépendants :

1. l'action de superposition écrit la liste des entrées de tête de l'arbre du
   dépôt privé, et le commit ne stage que celles-là ;
2. une seconde passe retire de l'index toute entrée de tête qui n'est ni dans
   cette liste ni une donnée — ce qui sert d'abord à propager une suppression
   faite sur le privé, et **retire aussi tout sous-produit qui aurait été stagé
   par ailleurs**.

Vérifié par mutation le 21/09/2026 : en remettant l'ancienne ligne de commit,
seul le garde statique échoue — la seconde passe rattrape `_artifacts/` et le
rapport ; en retirant la seconde passe, c'est le test de la suppression qui
échoue. Chacun des deux filets suffit seul à ne rien publier de parasite.

Ce test **exécute** le fragment de shell extrait du workflow dans un
dépôt jetable, où un run a déposé exactement ce qu'il dépose en vrai — c'est la
seule façon de savoir ce qu'il stage, et c'est ce qu'une relecture du YAML
n'avait pas vu.
"""

import os
import pathlib
import re
import subprocess

import pytest

RACINE = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
ACTION = RACINE / ".github" / "actions" / "code-du-prive" / "action.yml"


def _fragment_de_commit() -> str:
    """Le bloc qui stage le code, extrait tel quel du workflow."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index('          LISTE="$RUNNER_TEMP/code-du-prive-racine.lst"\n')
    fin = texte.index("\n          fi\n", debut) + len("\n          fi\n")
    bloc = texte[debut:fin]
    assert "${{" not in bloc, "le fragment doit rester exécutable hors de GitHub"
    return "\n".join(l[10:] if l.startswith(" " * 10) else l for l in bloc.splitlines())


def _git(depot: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=depot, check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def run_simule(tmp_path):
    """Un checkout du dépôt public, puis ce qu'un run y laisse.

    - `src/a.py` modifié et `src/b.py` ajouté sur le privé, superposés ;
    - `obsolete.txt` supprimé sur le privé, donc retiré par `rsync --delete` ;
    - `_artifacts/` et un rapport de contrôle déposés à la racine par le run ;
    - une donnée modifiée — elle a son propre `git add`, hors de ce fragment.
    """
    depot = tmp_path / "public"
    depot.mkdir()
    _git(depot, "init", "-q")
    _git(depot, "config", "user.email", "t@example.org")
    _git(depot, "config", "user.name", "t")
    for chemin, contenu in {"src/a.py": "v1\n", "README.md": "r\n", "obsolete.txt": "o\n",
                            "pivot_data/x.json": "{}\n", "raw_data/y.json": "{}\n"}.items():
        (depot / chemin).parent.mkdir(parents=True, exist_ok=True)
        (depot / chemin).write_text(contenu, encoding="utf-8")
    _git(depot, "add", "-A")
    _git(depot, "commit", "-q", "-m", "v1.0.3")

    (depot / "src" / "a.py").write_text("v2\n", encoding="utf-8")
    (depot / "src" / "b.py").write_text("nouveau\n", encoding="utf-8")
    (depot / "obsolete.txt").unlink()
    (depot / "_artifacts" / "roster").mkdir(parents=True)
    (depot / "_artifacts" / "roster" / "p.json").write_text("{}\n", encoding="utf-8")
    (depot / "diff-profils.json").write_text("{}\n", encoding="utf-8")
    (depot / "pivot_data" / "x.json").write_text('{"v": 2}\n', encoding="utf-8")

    temp = tmp_path / "runner-temp"
    temp.mkdir()
    return depot, temp


def _stager(depot, temp, liste):
    if liste is not None:
        (temp / "code-du-prive-racine.lst").write_text("".join(f"{e}\n" for e in liste),
                                                        encoding="utf-8")
    resultat = subprocess.run(["bash", "-c", _fragment_de_commit()], cwd=depot,
                              capture_output=True, text=True,
                              env={**os.environ, "RUNNER_TEMP": str(temp)})
    assert resultat.returncode == 0, resultat.stderr
    stage = dict(
        reversed(ligne.split("\t", 1))
        for ligne in _git(depot, "diff", "--cached", "--name-status").splitlines()
    )
    return {chemin: statut for chemin, statut in stage.items()}, resultat.stdout


def test_seul_le_code_superpose_est_stage(run_simule):
    """Le discriminant du lot : `_artifacts/` et les rapports n'entrent PAS."""
    depot, temp = run_simule
    stage, _ = _stager(depot, temp, ["src", "README.md"])

    assert stage.get("src/a.py") == "M"
    assert stage.get("src/b.py") == "A"
    assert not any(c.startswith("_artifacts/") for c in stage), (
        f"des sous-produits du run seraient publiés : {sorted(stage)}"
    )
    assert "diff-profils.json" not in stage


def test_une_entree_de_tete_supprimee_sur_le_prive_disparait_du_public(run_simule):
    """`rsync --delete` l'a retirée de l'arbre ; sans la passe dédiée, le dépôt
    public la garderait indéfiniment."""
    depot, temp = run_simule
    stage, _ = _stager(depot, temp, ["src", "README.md"])
    assert stage.get("obsolete.txt") == "D"


def test_les_donnees_restent_hors_de_ce_fragment(run_simule):
    """Elles ont leur `git add` explicite, juste au-dessus dans le workflow."""
    depot, temp = run_simule
    stage, _ = _stager(depot, temp, ["src", "README.md"])
    assert not any(c.startswith(("pivot_data/", "raw_data/")) for c in stage)


def test_sans_liste_rien_du_code_nest_publie_et_le_log_le_dit(run_simule):
    """Une liste absente ne doit jamais se lire comme « tout » : on ne publie
    rien au hasard, et on le dit."""
    depot, temp = run_simule
    stage, sortie = _stager(depot, temp, None)
    assert stage == {}
    assert "Liste du code superposé absente" in sortie


def test_l_action_ecrit_la_liste_depuis_l_arbre_du_prive_sans_les_donnees():
    """La liste vient de la SOURCE superposée, jamais de l'arbre de travail —
    c'est ce qui l'empêche de contenir un sous-produit du run."""
    action = ACTION.read_text(encoding="utf-8")
    assert "git ls-tree --name-only HEAD" in action
    assert 'code-du-prive-racine.lst' in action
    assert re.search(r'grep -vxF -e "\$\{DONNEES\[0\]\}" -e "\$\{DONNEES\[1\]\}"', action)


def test_aucun_git_add_ne_stage_la_racine_entiere():
    """La forme qui a publié les 5,3 Go ne doit pas revenir, sous aucune
    variante : `git add -A` sur `.`, `-A` seul, ou `git add .`."""
    for ligne in WORKFLOW.read_text(encoding="utf-8").splitlines():
        code = ligne.split("#", 1)[0]
        assert not re.search(r"git add (-A )?(-- )?\.(\s|$)", code), ligne.strip()
        assert not re.search(r"git add -A\s*$", code), ligne.strip()
