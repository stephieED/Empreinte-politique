"""Garde-fou #685 : un commit de données sans suite de tests ne passe plus en silence.

`AGENTS.md` §3b affirmait, au titre de #508 : « A deploy-key push emits a `push`
event, so `tests.yml` really runs on data commits. » Mesuré le 01/09/2026 :
**0 des 15** commits de données arrivés sur `main` depuis que `tests.yml` existe
ne porte de run de la suite, dont les **11** postérieurs à #508. Le dépôt n'a
aucune clé de déploiement et le secret `DATA_PUSH_SSH_KEY` n'existe pas : le
push repart sous le GITHUB_TOKEN, qui n'émet aucun événement.

Ce qui a rendu la panne invisible n'est pas le repli — il est voulu — c'est
qu'il est **muet** : le « rejet bruyant » de #508 ne parle que sur un `GH013`,
lequel suppose le check requis, jamais rétabli. Les deux omissions se couvrent
l'une l'autre.

**Ce fichier verrouille que le signal parle**, et il le fait en *exécutant* le
fragment de shell extrait du workflow plutôt qu'en le relisant : un garde-fou
qui devient muet sans le dire est pire que pas de garde-fou (`AGENTS.md` §3b),
et un test qui se contente de reconnaître un motif reste vert le jour où le
motif est là mais ne s'imprime plus.

Volontairement sans PyYAML (absent de `requirements.txt` comme de
`requirements-dev.txt`), comme les autres gardes-fous de workflow du dépôt.

Voir docs/decisions/identite-du-push-et-declenchement-des-tests-685.md.
"""

import re
import subprocess
import textwrap
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
WORKFLOW_TESTS = RACINE / ".github" / "workflows" / "tests.yml"
AGENTS = RACINE / "AGENTS.md"

#: Le nom du step, tel qu'il apparaît dans le journal du run.
NOM_DU_STEP = "Le commit de données déclenchera-t-il `tests.yml` ? (#685)"


def _step(nom: str) -> str:
    """Le bloc YAML d'un step, du `- name:` au step suivant, ou `\"\"` s'il a disparu.

    **Jamais de levée à l'import.** Le step retiré ferait sinon une *erreur de
    collecte*, qui emporte tout le fichier — y compris le cas sur `AGENTS.md`,
    lequel n'a rien à voir avec ce step — et se lit comme une suite cassée
    plutôt que comme un garde-fou qui parle. Chaque cas échoue à son tour, en
    disant lequel des deux morceaux manque.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.find(f"- name: {nom}")
    if debut == -1:
        return ""
    suite = re.search(r"^      - (?:name|uses|run):", texte[debut:][1:], flags=re.MULTILINE)
    return texte[debut: debut + 1 + suite.start()] if suite else texte[debut:]


def _script(bloc_step: str) -> str:
    """Le contenu du `run: |` du step, dédenté, prêt à être exécuté."""
    marqueur = "run: |\n"
    if marqueur not in bloc_step:
        return ""
    debut = bloc_step.index(marqueur) + len(marqueur)
    return textwrap.dedent(bloc_step[debut:])


BLOC = _step(NOM_DU_STEP)
SCRIPT = _script(BLOC)

#: Message unique du step disparu — les six cas qui en dépendent le citent.
ABSENT = (
    f"step « {NOM_DU_STEP} » introuvable dans {WORKFLOW.name} : le signal de "
    "#685 a été retiré ou renommé, et un commit de données sans suite de tests "
    "redeviendrait invisible (docs/decisions/"
    "identite-du-push-et-declenchement-des-tests-685.md)."
)


def test_le_step_du_signal_existe_toujours():
    """Le premier cas à lire quand ce fichier rougit en bloc."""
    assert BLOC, ABSENT
    assert SCRIPT, f"{ABSENT} (le `run: |` du step est vide ou absent)"


def _rejouer(url_distante: str, tmp_path: Path) -> tuple[int, str, str]:
    """Exécute le script du step dans un dépôt local dont `origin` vaut `url`.

    Aucun accès réseau (`AGENTS.md` §3b) : `git remote get-url` lit la
    configuration locale, et le dépôt est créé sous `tmp_path`, jamais sous
    `pivot_data/` ni `raw_data/`.
    """
    assert SCRIPT, ABSENT
    depot = tmp_path / "depot"
    depot.mkdir()
    for commande in (["git", "init", "-q"], ["git", "remote", "add", "origin", url_distante]):
        subprocess.run(commande, cwd=depot, check=True, capture_output=True)

    resume = tmp_path / "resume.md"
    resume.touch()
    acheve = subprocess.run(
        ["bash", "-c", SCRIPT],
        cwd=depot,
        env={"PATH": "/usr/bin:/bin", "GITHUB_STEP_SUMMARY": str(resume)},
        capture_output=True,
        text=True,
    )
    return acheve.returncode, acheve.stdout + acheve.stderr, resume.read_text(encoding="utf-8")


# ── 1. Le step existe, et au bon moment ──────────────────────────────────────

def test_le_signal_ne_parle_que_sur_un_push_reellement_abouti():
    """Sans commit poussé, il n'y a pas de commit de données à couvrir : le
    signal parlerait dans le vide et deviendrait du bruit qu'on apprend à
    ignorer."""
    assert BLOC, ABSENT
    assert re.search(r"if:\s*steps\.commit\.outputs\.pushed == 'true'", BLOC), (
        "le signal de #685 doit être gardé par `pushed == 'true'`, comme le "
        "déclenchement de deploy-pages.yml."
    )


def test_le_signal_mesure_le_distant_employe_et_ne_devine_pas_lintention():
    """`secrets.DATA_PUSH_SSH_KEY != ''` dirait ce qu'on a voulu faire ;
    `git remote get-url origin` dit ce qui s'est passé. `actions/checkout` pose
    `git@github.com:` quand `ssh-key` est renseignée, `https://github.com/`
    sinon — c'est cette bascule, lue sur le dépôt du runner, qui a prouvé la
    cause de #685 dans le journal du job 99566091830."""
    assert SCRIPT, ABSENT
    assert "git remote get-url origin" in SCRIPT, (
        "le signal doit mesurer l'URL du distant réellement utilisée par le push."
    )
    assert "secrets." not in SCRIPT, (
        "lire le secret ici rendrait le signal dépendant d'une intention et non "
        "d'un fait : un secret renseigné mais refusé par le checkout passerait."
    )


# ── 2. Le signal parle, et on le vérifie en l'exécutant ──────────────────────

def test_sur_un_push_sous_le_token_le_signal_nomme_la_consequence(tmp_path):
    """Le cas de #685 lui-même. Trois choses doivent sortir : une annotation
    que GitHub remonte, le nom du workflow qui ne tournera pas, et de quoi
    réparer. Nommer seulement « pas de clé de déploiement » laisserait le
    lecteur reconstruire la conséquence — c'est la reconstruction qui n'a pas
    eu lieu pendant quinze commits."""
    code, sortie, resume = _rejouer("https://github.com/stephieED/Empreinte-politique-src", tmp_path)

    assert "::warning::" in sortie, (
        "un push sous le GITHUB_TOKEN doit produire une annotation : sans elle, "
        "le repli redevient muet et #685 se reproduit sans trace."
    )
    assert "tests.yml" in sortie, "l'annotation doit nommer le workflow qui ne tournera pas"
    assert "GITHUB_TOKEN" in sortie, "l'annotation doit nommer l'identité qui a poussé"
    assert "DATA_PUSH_SSH_KEY" in sortie, "l'annotation doit nommer la piste de réparation"
    assert "685" in sortie, "l'annotation doit être rattachable à sa décision"

    assert "tests.yml" in resume and "NE tournera PAS" in resume, (
        "le résumé du job est le second canal, et le seul qui se relise après "
        "coup : les annotations d'un run ancien ne se retrouvent pas."
    )


def test_sur_un_push_sous_cle_de_deploiement_le_signal_confirme(tmp_path):
    """L'autre moitié du garde-fou. Un signal qui crie dans les deux cas
    n'apprend rien ; un signal qui se tait dans les deux cas non plus. Le jour
    où les trois gestes de #508 §7 seront posés, ce cas est celui qui doit
    basculer — et il dit ce que le run doit alors afficher."""
    code, sortie, resume = _rejouer("git@github.com:stephieED/Empreinte-politique-src.git", tmp_path)

    assert "::warning::" not in sortie, (
        "sous clé de déploiement l'événement `push` est bien émis : avertir "
        "ici userait le signal jusqu'à ce qu'on cesse de le lire."
    )
    assert "tests.yml" in sortie and "clé de déploiement" in sortie
    assert "NE tournera PAS" not in resume


@pytest.mark.parametrize(
    "url",
    ["https://github.com/stephieED/Empreinte-politique-src", "git@github.com:stephieED/x.git"],
)
def test_le_signal_ne_fait_jamais_echouer_le_job(url, tmp_path):
    """Les trois gestes qui répareraient le mécanisme (clé de déploiement,
    secret, check requis) vivent hors du dépôt : faire échouer le job priverait
    le site de ses données fraîches pour une configuration que seule une
    humaine peut poser. Rendre ce signal bloquant est un arbitrage, pas une
    correction — ce cas échoue si quelqu'un le prend en passant."""
    code, sortie, _ = _rejouer(url, tmp_path)
    assert code == 0, f"le signal de #685 doit rester non bloquant ; sortie :\n{sortie}"


# ── 3. L'identité du push est bien la seule cause possible ───────────────────

def test_tests_yml_ne_filtre_aucun_chemin_sur_main():
    """Si `tests.yml` gagnait un `paths:`/`paths-ignore:`, un commit de données
    pourrait le manquer pour une deuxième raison, et l'annotation ci-dessus
    deviendrait un diagnostic faux — elle affirmerait que l'identité du push
    est en cause alors que le filtre suffirait à l'expliquer."""
    texte = WORKFLOW_TESTS.read_text(encoding="utf-8")
    declencheurs = texte[texte.index("\non:"): texte.index("\npermissions:")]
    sans_commentaires = "\n".join(
        l for l in declencheurs.split("\n") if not l.lstrip().startswith("#")
    )
    assert "paths" not in sans_commentaires, (
        "aucun filtre de chemin sur les déclencheurs de tests.yml : c'est ce qui "
        "fait de l'identité du push la seule explication d'un commit de données "
        "non couvert (#685)."
    )
    assert re.search(r"push:\s*\n\s*branches:\s*\[main\]", sans_commentaires)


# ── 4. AGENTS.md ne promet plus ce que le dépôt ne tient pas ─────────────────

def test_agents_md_ne_promet_plus_la_suite_sur_les_commits_de_donnees():
    """La phrase d'origine — « A deploy-key push emits a `push` event, so
    `tests.yml` really runs on data commits » — décrivait un mécanisme réel
    sous une condition jamais remplie. Laisser une garantie fausse en place est
    plus coûteux que de n'en donner aucune : on s'y fie."""
    # #737 — la §3b vit désormais dans `docs/regles/ci.md`, `AGENTS.md` n'en
    # gardant que la ligne d'index. On lit LES DEUX : la garantie fausse ne doit
    # réapparaître ni dans le fichier de règles, ni dans l'index qui le résume.
    regles_ci = AGENTS.parent / "docs" / "regles" / "ci.md"
    assert regles_ci.is_file(), (
        "`docs/regles/ci.md` a disparu : la §3b n'est plus nulle part (#737)."
    )
    texte = AGENTS.read_text(encoding="utf-8") + regles_ci.read_text(encoding="utf-8")
    assert "so `tests.yml` really runs on data commits" not in texte, (
        "§3b affirmait cette garantie comme acquise alors qu'aucun commit de "
        "données depuis l'existence de tests.yml ne la vérifie (#685). Elle ne "
        "peut se rétablir qu'avec les trois gestes de #508 §7."
    )
    assert "#685" in texte, (
        "§3b doit renvoyer à #685 : sans lui, la ligne corrigée ne dit pas où "
        "lire la mesure ni ce qu'il faudrait poser pour la rendre vraie."
    )
