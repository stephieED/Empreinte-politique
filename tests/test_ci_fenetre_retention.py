"""Garde-fou #551 : la détection de la fenêtre de rétention est ARMÉE, et elle
ne fait que compter.

#434 affirmait que « ce qui est automatisé, c'est la détection ». Le code
existait — `src/audit_volumetrie_profils.py` sait dire si la fenêtre est
contraignante — mais aucun workflow ne l'invoquait : la détection était
outillée, pas armée. Ces tests verrouillent les trois propriétés de la
correction, et chacune répond à une faute précise.

  1. **Le step existe**, dans le job qui écrit les commits de données.
  2. **La valeur de la fenêtre est lue, jamais recopiée.** Elle vit déjà à deux
     endroits dont `tests/test_borner_historique_donnees.py` verrouille
     l'égalité ; un troisième domicile ferait répondre deux valeurs différentes
     à « la fenêtre est-elle contraignante ? ».
  3. **Aucun workflow ne borne ni ne mesure.** La réécriture d'historique est
     irréversible pour tous les clones existants : c'est une décision, pas une
     étape de CI. Et `--mesurer` clone puis repacke deux fois le dépôt entier —
     1 min 52 s de temps réel, 3 min 37 s de CPU au 28/08/2026.

#579 en a ajouté une quatrième, et elle est d'une autre nature : **le step
s'EXÉCUTE ici**, contre des dépôts fabriqués, au lieu d'être seulement relu.
Les deux pannes du 28/08/2026 ont toutes deux survécu à une relecture et à des
tests de motif — la seconde a même survécu à un test qui verrouillait
explicitement la ligne fautive (`test_l_approfondissement_depasse_la_fenetre`,
retiré ici : il exigeait une profondeur devinée, c'est-à-dire le défaut).

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.

Aucun test de ce fichier ne sort sur le réseau (AGENTS.md §3) : les dépôts sont
fabriqués dans `tmp_path` et servis en `file://`.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((RACINE / ".github" / "workflows").glob("*.yml"))
GENERATE = RACINE / ".github" / "workflows" / "generate-data.yml"
AUDIT = RACINE / "src" / "audit_volumetrie_profils.py"
NOM_STEP = "Fenêtre de rétention de l'historique de données (#551)"

MOTIF_REEL = re.search(
    r'^MOTIF_COMMIT_DONNEES = "(.+)"$', AUDIT.read_text(encoding="utf-8"),
    flags=re.MULTILINE,
).group(1)


def _sans_commentaires(bloc: str) -> str:
    """Les rationales de ce dépôt citent abondamment les commandes qu'elles
    expliquent : les lire comme du workflow serait un faux positif permanent."""
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def _step_detection() -> str:
    texte = GENERATE.read_text(encoding="utf-8")
    debut = texte.find(f"- name: {NOM_STEP}")
    assert debut != -1, f"step « {NOM_STEP} » absent de {GENERATE.name}"
    suite = re.search(r"^      - name: ", texte[debut + 1:], flags=re.MULTILINE)
    return texte[debut: debut + 1 + suite.start()] if suite else texte[debut:]


def test_la_detection_est_armee():
    """La faute de #551 : le code de détection existait sans que rien ne le
    lance. Un step qui n'existe pas ne détecte rien."""
    assert f"- name: {NOM_STEP}" in GENERATE.read_text(encoding="utf-8")


def test_la_detection_vit_dans_le_job_qui_ecrit_les_commits_de_donnees():
    """Compter ailleurs que là où l'on committe, c'est compter un état qui n'est
    pas encore celui du dépôt."""
    texte = GENERATE.read_text(encoding="utf-8")
    debut = re.search(r"^  merge-and-pivot:\s*$", texte, flags=re.MULTILINE)
    assert debut, "job `merge-and-pivot` absent"
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], flags=re.MULTILINE)
    bloc = texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]
    assert NOM_STEP in bloc, "la détection doit vivre dans `merge-and-pivot`"


def test_la_fenetre_est_lue_jamais_recopiee():
    """Troisième domicile interdit. `FENETRE` (script de bornage) et
    `FENETRE_COMMITS_DONNEES` (audit) sont déjà tenus égaux par un test ; un
    nombre en dur ici les contredirait sans que rien ne le dise."""
    step = _sans_commentaires(_step_detection())
    assert "FENETRE_COMMITS_DONNEES" in step, (
        "le step doit LIRE la fenêtre depuis `audit_volumetrie_profils`"
    )
    assert "MOTIF_COMMIT_DONNEES" in step, (
        "le motif du commit de données doit être lu, pas recopié"
    )
    valeur = re.search(r"^FENETRE_COMMITS_DONNEES = (\d+)$",
                       (RACINE / "src" / "audit_volumetrie_profils.py").read_text(encoding="utf-8"),
                       flags=re.MULTILINE)
    assert valeur, "FENETRE_COMMITS_DONNEES introuvable"
    assert re.search(rf"\b{valeur.group(1)}\b", step) is None, (
        f"le step écrit {valeur.group(1)} en dur : ce serait un troisième "
        "domicile pour la valeur de la fenêtre"
    )


def test_la_detection_approfondit_avant_de_compter():
    """Le défaut qui a rendu la détection inopérante à son premier run (#551).

    `actions/checkout` cloue l'historique à un commit ; `merge-and-pivot` ne
    demande pas d'autre profondeur. Sans approfondissement, `git log --grep` ne
    voit que le commit de données que le job vient d'écrire : le compteur rendait
    **1** et le step annonçait « non contraignante » alors que la fenêtre était
    pleine à 30 sur 30. Constaté sur le run 33185097538 du 28/08/2026.

    Un step qui tourne et ne voit rien est pire qu'un step absent : il a l'air
    de marcher.
    """
    step = _sans_commentaires(_step_detection())
    assert "git fetch" in step and "--unshallow" in step, (
        "le step compte sur un historique superficiel : le compteur ne pourra "
        "jamais atteindre la fenêtre"
    )
    assert step.index("--unshallow") < step.index("git log --grep"), (
        "l'approfondissement doit précéder le comptage"
    )


def test_aucune_profondeur_n_est_devinee():
    """LE défaut de #574, et la raison pour laquelle il a survécu à un test.

    La fenêtre se compte en COMMITS DE DONNÉES ; `--deepen` se compte en
    PROFONDEUR D'HISTOIRE. Les deux n'ont aucun rapport fixe : mesuré le
    29/08/2026 sur l'historique réel, depuis le commit de données du run
    33200210924, il y a 32 commits de données pour 867 commits atteignables, et
    le 32e commit de données est à la profondeur 203. Une profondeur de
    `FENETRE + 10` = 41 en montrait **8 sur 32** — assez peu pour prendre la
    branche « non contraignante », assez plausible pour ne pas se voir.

    Le test qui gardait cette ligne (`test_l_approfondissement_depasse_la_fenetre`)
    exigeait que la profondeur soit dérivée de `FENETRE` : il verrouillait la
    confusion d'unités au lieu de l'interdire.
    """
    step = _sans_commentaires(_step_detection())
    assert "--deepen" not in step, (
        "une profondeur devinée confond deux unités : le rapport entre commits "
        "de données et profondeur d'histoire dépend du rythme des PR, il n'est "
        "pas une constante du dépôt"
    )


def test_l_approfondissement_ne_tire_ni_arbre_ni_blob():
    """`git log --grep` ne lit que des objets COMMIT. `--filter=blob:none`
    laissait encore venir tous les ARBRES, c'est-à-dire l'essentiel du poids.
    `--filter=tree:0` rend enfin ce que le commentaire de #574 promettait : le
    graphe, pas le contenu.

    Mesuré le 29/08/2026 contre github.com sur ce dépôt : 3,16 s, 877 commits,
    `.git` de 972 Ko au total."""
    step = _sans_commentaires(_step_detection())
    assert "--filter=tree:0" in step, (
        "l'approfondissement doit être sans arbres NI blobs : `blob:none` "
        "ramène encore tout l'arborescent d'un corpus de profils"
    )


def test_la_detection_publie_dans_le_resume_de_run():
    """« Rendre le franchissement visible là où on regarde » : une annotation de
    plus se noie, le résumé de run non."""
    assert "GITHUB_STEP_SUMMARY" in _step_detection()


def test_l_echec_de_l_approfondissement_n_est_pas_avale():
    """« Un garde-fou qui avale ce qu'il devrait signaler » (#579), même famille
    que le `except Exception` de #562. Le `|| true` transformait une panne en
    silence, et le compteur rendait un nombre plausible au lieu d'une erreur."""
    step = _sans_commentaires(_step_detection())
    ligne_fetch = [l for l in step.split("\n") if "git fetch" in l]
    assert ligne_fetch, "plus de fetch dans le step"
    for ligne in ligne_fetch:
        assert "|| true" not in ligne, (
            "l'échec de l'approfondissement est avalé : le compteur rendra un "
            "nombre plausible au lieu de dire qu'il n'a rien pu établir"
        )
    assert "2>/dev/null" not in step, (
        "la sortie d'erreur du fetch est jetée : c'est elle qui dirait POURQUOI "
        "le compte n'a pas pu être établi"
    )


def test_le_compte_part_sur_stdout_et_pas_seulement_dans_le_resume():
    """`$GITHUB_STEP_SUMMARY` n'est récupérable NI par `gh run view --log` NI
    par l'API (`output.summary` et `output.text` reviennent vides). Diagnostiquer
    #579 a demandé de télécharger le journal brut du job et de MESURER LA DURÉE
    du step pour en déduire ce qu'il avait fait."""
    step = _sans_commentaires(_step_detection())
    sur_stdout = [
        l for l in step.split("\n")
        if l.strip().startswith("echo ") and "GITHUB_STEP_SUMMARY" not in l
        and "::" not in l and "${NB}" in l
    ]
    assert sur_stdout, (
        "aucune ligne de compte n'atteint stdout : le step reste indébogable "
        "par le journal comme par l'API"
    )


# ── Le step EXÉCUTÉ, contre des dépôts fabriqués ────────────────────────────
#
# Les deux pannes du 28/08/2026 ont survécu à la relecture ET aux tests de
# motif. Ce qui suit lance le script du step pour de vrai : c'est le seul
# niveau où « le compteur compte-t-il ce qu'il annonce ? » se pose.


def _script_du_step() -> str:
    """Extrait le corps du `run: |` du step, désindenté, prêt pour bash."""
    lignes = _step_detection().split("\n")
    depart = next(i for i, l in enumerate(lignes) if l.strip() == "run: |")
    corps = []
    for ligne in lignes[depart + 1:]:
        if ligne.strip() and not ligne.startswith(" " * 10):
            break
        corps.append(ligne[10:])
    return "\n".join(corps)


def _git(depot, *args):
    return subprocess.run(["git", "-C", str(depot), *args],
                          check=True, capture_output=True, text=True).stdout


def _fabriquer(chemin, donnees, bruit_par_donnee, fenetre):
    """Un dépôt jetable : `donnees` commits de données, chacun suivi de
    `bruit_par_donnee` commits ordinaires — parce que sur le vrai dépôt les
    commits de données NE SONT PAS contigus, et que c'est exactement ce que la
    profondeur devinée de #574 ne voyait pas."""
    chemin.mkdir(parents=True)
    _git(chemin, "init", "-q", "-b", "main")
    _git(chemin, "config", "user.email", "banc@test")
    _git(chemin, "config", "user.name", "banc")
    for i in range(donnees):
        _git(chemin, "commit", "-q", "--allow-empty",
             "-m", f"chore: {MOTIF_REEL} (2026-08-{i + 1:02d})")
        for j in range(bruit_par_donnee):
            _git(chemin, "commit", "-q", "--allow-empty", "-m", f"fix: bruit {i}-{j}")
    _poser_le_module(chemin, fenetre)
    return chemin


def _poser_le_module(chemin, fenetre):
    """Le step LIT la fenêtre et le motif dans `src/audit_volumetrie_profils`.

    Le motif posé ici est le VRAI, lu dans la source — un motif inventé ne
    prouverait rien du comptage réel. La fenêtre, elle, est réduite : le banc
    teste les trois branches, pas la valeur de production, que
    `test_la_fenetre_est_lue_jamais_recopiee` verrouille déjà statiquement.
    """
    (chemin / "src").mkdir(exist_ok=True)
    (chemin / "src" / "audit_volumetrie_profils.py").write_text(
        f"FENETRE_COMMITS_DONNEES = {fenetre}\n"
        f'MOTIF_COMMIT_DONNEES = "{MOTIF_REEL}"\n',
        encoding="utf-8",
    )


def _lancer(cwd, resume):
    return subprocess.run(
        ["bash", "-c", _script_du_step()], cwd=str(cwd),
        capture_output=True, text=True,
        env={**os.environ, "GITHUB_STEP_SUMMARY": str(resume),
             "GIT_TERMINAL_PROMPT": "0"},
    )


@pytest.mark.parametrize(
    "donnees, fenetre, attendu",
    [
        (3, 10, "rien"),          # non contraignante : aucune annotation
        (8, 10, "::notice::"),    # 2 commits avant qu'elle morde
        (10, 10, "::warning::"),  # contraignante, à la borne exacte
        (12, 10, "::warning::"),  # franchie
    ],
)
def test_le_compte_choisit_la_bonne_branche_et_le_dit_sur_stdout(
        tmp_path, donnees, fenetre, attendu):
    """Le franchissement observé de #579 : 32 commits pour une fenêtre de 30,
    et aucune annotation. Ici la fenêtre est franchie pour de vrai, et
    l'annotation doit sortir — sur stdout, là où le journal et l'API la voient."""
    depot = _fabriquer(tmp_path / "depot", donnees, 3, fenetre)
    resume = tmp_path / "resume.md"
    res = _lancer(depot, resume)
    assert res.returncode == 0, res.stderr
    assert f"Fenêtre de rétention : {donnees} commit(s) de données pour une " \
           f"fenêtre de {fenetre}" in res.stdout, res.stdout
    if attendu == "rien":
        assert "::warning::" not in res.stdout and "::notice::" not in res.stdout
        assert "non contraignante" in resume.read_text(encoding="utf-8")
    else:
        assert attendu in res.stdout, res.stdout


def test_un_historique_tronque_ne_rend_aucun_compte(tmp_path):
    """LE défaut de #574 rendu bruyant.

    Un clone superficiel dont l'origine est injoignable : l'approfondissement
    échoue. L'ancien step avalait l'échec (`|| true`) et publiait le compte du
    seul commit visible — 1 sur 32, plausible, silencieux. Le nouveau doit
    refuser de publier un chiffre, et dire qu'il n'a RIEN pu établir."""
    source = _fabriquer(tmp_path / "source", 12, 5, 10)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--depth=1",
                    f"file://{source}", str(clone)], check=True, capture_output=True)
    _poser_le_module(clone, 10)
    (source / ".git").rename(tmp_path / "origine-partie")  # origine injoignable

    resume = tmp_path / "resume.md"
    res = _lancer(clone, resume)
    assert res.returncode == 0, "le compteur ne doit pas faire tomber le job"
    assert "AUCUN compte établi" in res.stdout, res.stdout
    assert "::warning::" in res.stdout and "RIEN n'a pu être compté" in res.stdout
    assert "commit(s) de données pour une fenêtre" not in res.stdout, (
        "un chiffre a été publié alors que rien n'a pu être établi"
    )
    assert "non contraignante" not in resume.read_text(encoding="utf-8")
    # Le code de retour du fetch DOIT être celui qui est rapporté : c'est ce
    # qu'un `|| true` effacerait, et le diagnostic retomberait sur le symptôme
    # (« resté superficiel ») au lieu de la cause.
    assert re.search(r"approfondissement a échoué \(git fetch, code [1-9]", res.stdout), (
        "l'échec du fetch n'est pas rapporté avec son code : il a été avalé"
    )


def test_un_fetch_qui_reussit_sans_lever_la_troncature_ne_compte_pas(tmp_path):
    """La panne que le seul contrôle du code de retour NE VOIT PAS, et qui est
    exactement celle de #574 : le fetch rend 0, et l'historique reste tronqué.
    Le compte serait alors un MINORANT — et un minorant plausible ne se voit
    pas, c'est tout le problème de #579.

    Le banc pose un faux `git` dans `PATH` qui répond 0 à `fetch` sans rien
    faire : aucun réseau, et la seule façon honnête de produire cette
    combinaison."""
    source = _fabriquer(tmp_path / "source", 12, 5, 10)
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--depth=1",
                    f"file://{source}", str(clone)], check=True, capture_output=True)
    _poser_le_module(clone, 10)

    vrai_git = subprocess.run(["bash", "-c", "command -v git"],
                              capture_output=True, text=True, check=True).stdout.strip()
    binaire = tmp_path / "bin"
    binaire.mkdir()
    (binaire / "git").write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$1" == "fetch" ]]; then exit 0; fi\n'
        f'exec {vrai_git} "$@"\n',
        encoding="utf-8",
    )
    (binaire / "git").chmod(0o755)

    res = subprocess.run(
        ["bash", "-c", _script_du_step()], cwd=str(clone),
        capture_output=True, text=True,
        env={**os.environ, "PATH": f"{binaire}:{os.environ['PATH']}",
             "GITHUB_STEP_SUMMARY": str(tmp_path / "resume.md")},
    )
    assert res.returncode == 0, res.stderr
    assert "resté superficiel" in res.stdout, res.stdout
    assert "::warning::" in res.stdout
    assert "commit(s) de données pour une fenêtre" not in res.stdout, (
        "un compte a été publié sur un historique tronqué : c'est le 1 de "
        "#551 et le 8 de #574, avec la même apparence de succès"
    )


def test_l_approfondissement_restitue_la_population_entiere(tmp_path):
    """Le test qui MORD sur #574 : 12 commits de données noyés dans 72 commits,
    donc hors de portée d'une profondeur de `fenêtre + 10` = 20. Le compteur
    doit rendre 12, pas les 3 ou 4 que la profondeur devinée montrait.

    ⚠ L'origine est servie en `file://`, et un serveur local est PLUS PERMISSIF
    que GitHub : il rend « filtering not recognized by server, ignoring » là où
    GitHub applique le filtre. C'est la faute de validation de #574, et elle
    n'est pas refaite ici : ce banc établit LE COMPTE, pas le filtre. Le filtre,
    lui, a été mesuré contre github.com le 29/08/2026 (3,16 s, 877 commits,
    `.git` de 972 Ko), et c'est écrit dans le commentaire du step."""
    source = _fabriquer(tmp_path / "source", 12, 5, 10)
    assert int(_git(source, "rev-list", "--count", "HEAD")) == 72
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--depth=1",
                    f"file://{source}", str(clone)], check=True, capture_output=True)
    _poser_le_module(clone, 10)
    assert _git(clone, "rev-parse", "--is-shallow-repository").strip() == "true"

    res = _lancer(clone, tmp_path / "resume.md")
    assert res.returncode == 0, res.stderr
    assert "Fenêtre de rétention : 12 commit(s) de données pour une fenêtre de 10" \
        in res.stdout, res.stdout
    assert "sur 72 commit(s) d'historique complet" in res.stdout, res.stdout
    assert "::warning::" in res.stdout, "la fenêtre est franchie et le step se tait"


def test_aucun_workflow_ne_borne_l_historique():
    """La réécriture d'historique est irréversible pour tous les clones
    existants. `borner_historique_donnees.sh` garantit par test qu'il ne pousse
    jamais ; l'appeler depuis la CI contournerait cette garantie."""
    for wf in WORKFLOWS:
        corps = _sans_commentaires(wf.read_text(encoding="utf-8"))
        assert "borner_historique_donnees" not in corps, (
            f"{wf.name} invoque le script de bornage : le bornage est une "
            "décision humaine, jamais une étape de CI"
        )


def test_aucun_workflow_n_appelle_la_mesure_lourde():
    """`--mesurer` clone le dépôt entier et le repacke deux fois : 1 min 52 s de
    temps réel et 3 min 37 s de CPU pour ~434 Mo au 28/08/2026. Compter des
    commits coûte une commande."""
    for wf in WORKFLOWS:
        corps = _sans_commentaires(wf.read_text(encoding="utf-8"))
        assert "audit_volumetrie_profils.py --mesurer" not in corps
        assert "--mesurer" not in corps, (
            f"{wf.name} appelle `--mesurer` : mesure lourde interdite en CI (#551)"
        )
