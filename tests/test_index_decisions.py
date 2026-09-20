"""Une décision citée résout vers un fichier qui existe, et l'index le connaît.

`docs/technical_decisions.md` portait 158 décisions en 18 404 lignes — un fichier
que personne ne lit en entier, et que personne ne lisait en entier : il était
consulté par ancre. Il a été découpé en un fichier par décision sous
`docs/decisions/`, et il est devenu leur index.

La découpe crée un risque qu'un fichier unique n'avait pas : **158 nouvelles
façons de citer un fichier qui n'existe pas.** Une faute de frappe dans un nom de
fichier ne casse rien à l'exécution, ne rougit nulle part, et se propage — l'issue
#578 a cité `test_les_inputs_du_retry_sont_tous_ecrits`, un test qui n'existe pas,
et ce nom a été repris tel quel dans des consignes avant que quiconque le vérifie.

Trois propriétés, donc :

1. tout renvoi `docs/decisions/<nom>.md` du dépôt désigne un fichier existant, et
   son ancre `#…`, si elle est là, est définie dans ce fichier ;
2. l'index et le répertoire disent la même chose — une décision sans ligne d'index,
   ou une ligne d'index sans fichier, fait échouer le test ;
3. rien ne renvoie vers `docs/archive/`, la copie figée d'avant la découpe. Elle
   n'est plus mise à jour ; un renvoi vers elle est un renvoi vers une règle
   possiblement remplacée.

Le périmètre balayé est celui du sparse-checkout de `tests.yml` : ce que ce test
lit doit être sur le disque du runner, sinon il passe en local et se tait en CI
(#518). `pivot_data/` en est **volontairement** absent, comme le veut #473 — deux
fiches de groupe publiées y citent encore l'ancien fichier, et c'est sans
conséquence : l'index porte toutes les ancres d'origine, ces liens résolvent.
"""

import os
import re
from pathlib import Path

import pytest

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")

RACINE = Path(__file__).resolve().parents[1]
DECISIONS = RACINE / "docs" / "decisions"
INDEX = RACINE / "docs" / "technical_decisions.md"

#: Ce qui est balayé. Chaque entrée est dans la liste blanche du sparse-checkout
#: de `tests.yml` — sans quoi ce test ne verrait rien en CI et ne le dirait pas.
RACINES_BALAYEES = (
    RACINE / ".github",
    RACINE / "AGENTS.md",
    RACINE / "README.md",
    RACINE / "ROADMAP.md",
    RACINE / "docs",
    RACINE / "raw_data" / "groupes_reels.json",
    RACINE / "scripts",
    RACINE / "src",
    RACINE / "tests",
    RACINE / "web",
)

_EXTENSIONS = {
    ".md", ".py", ".yml", ".yaml", ".json", ".sh", ".txt",
    ".js", ".jsx", ".mjs", ".ts", ".tsx", ".html", ".css",
}
_REPERTOIRES_IGNORES = {".git", "node_modules", "dist", "build", ".venv", "__pycache__"}

#: Élagué en plus des répertoires ci-dessus : la copie locale de `pivot_data/` que
#: le serveur Vite se fait servir. Elle est gitignorée, donc absente du runner,
#: mais présente en local — 765 Mo que ce test n'a aucune raison de lire, et que
#: #473 lui interdit de lire.
_SOUS_ARBRES_IGNORES = ("web/UI_finale/public/data",)

#: Un renvoi vers l'archive, c'est un chemin qui désigne le **fichier** figé.
#: Nommer le répertoire `docs/archive/` pour dire de ne pas y aller (AGENTS.md) n'en
#: est pas un.
_RENVOI_ARCHIVE = re.compile(r'docs/archive/\S+\.md')

#: Les deux fichiers autorisés à porter un tel chemin : l'index, qui doit dire où
#: l'archive est, et ce fichier-ci, dont le motif ci-dessus se relève lui-même.
_NOMMENT_LARCHIVE = {"docs/technical_decisions.md", "tests/test_index_decisions.py"}

#: `docs/decisions/<nom>.md` ou `docs/decisions/<nom>.md#<ancre>`, et la même
#: chose vue depuis `docs/` (les fichiers de `docs/decisions/` se citent entre eux
#: par `<nom>.md`, résolu plus bas relativement au fichier citant).
_RENVOI = re.compile(r'(?:docs/)?decisions/([a-z0-9-]+)\.md(?:#([a-z0-9-]+))?')
_RENVOI_LOCAL = re.compile(r'\]\(([a-z0-9-]+)\.md(?:#([a-z0-9-]+))?\)')
_ANCRE = re.compile(r'<a id="([^"]+)"></a>')
_LIGNE_INDEX = re.compile(r'^- `[^`]+` ((?:<a id="[^"]+"></a>)+)\[.+\]\(decisions/([a-z0-9-]+)\.md\) — \S')


def _fichiers_balayes():
    for racine in RACINES_BALAYEES:
        if racine.is_file():
            yield racine
            continue
        if not racine.is_dir():
            continue
        for dossier, sous, noms in os.walk(racine):
            ici = Path(dossier).relative_to(RACINE).as_posix()
            sous[:] = sorted(
                d for d in sous
                if d not in _REPERTOIRES_IGNORES
                and f"{ici}/{d}" not in _SOUS_ARBRES_IGNORES)
            for nom in sorted(noms):
                chemin = Path(dossier) / nom
                if chemin.suffix in _EXTENSIONS:
                    yield chemin


def _lire(chemin):
    try:
        return chemin.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


def _decisions():
    """`{nom: ancres définies dans le fichier}` — le nom compte comme ancre."""
    fiches = {}
    for chemin in sorted(DECISIONS.glob("*.md")):
        nom = chemin.stem
        fiches[nom] = {nom} | set(_ANCRE.findall(_lire(chemin)))
    return fiches


def test_le_repertoire_des_decisions_nest_pas_vide():
    """Garde-fou du garde-fou : un `docs/` absent du sparse-checkout rendrait
    tous les autres tests de ce fichier vrais par vacuité, en CI seulement."""
    fiches = _decisions()
    assert len(fiches) > 100, (
        f"{len(fiches)} décision(s) trouvée(s) sous {DECISIONS} — le répertoire est "
        "absent ou vide. En CI, cela veut dire que `docs` a quitté le "
        "sparse-checkout de tests.yml.")


def test_toute_decision_citee_dans_le_depot_existe():
    fiches = _decisions()
    manquants = []
    for chemin in _fichiers_balayes():
        texte = _lire(chemin)
        relatif = chemin.relative_to(RACINE)
        couples = [(n, a) for n, a in _RENVOI.findall(texte)]
        if chemin.parent == DECISIONS:
            couples += [(n, a) for n, a in _RENVOI_LOCAL.findall(texte)]
        for nom, ancre in couples:
            if nom not in fiches:
                manquants.append(f"{relatif} → docs/decisions/{nom}.md (fichier absent)")
            elif ancre and ancre not in fiches[nom]:
                manquants.append(
                    f"{relatif} → docs/decisions/{nom}.md#{ancre} (ancre absente du fichier)")
    assert not manquants, (
        "ces renvois ne résolvent vers rien — une décision se cite par le nom de son "
        "fichier, jamais de mémoire :\n  " + "\n  ".join(sorted(set(manquants))))


def test_lindex_et_le_repertoire_disent_la_meme_chose():
    lignes = [m for m in (_LIGNE_INDEX.match(l) for l in INDEX.read_text(
        encoding="utf-8").split("\n")) if m]
    indexes = [m.group(2) for m in lignes]
    fiches = set(_decisions())

    doublons = sorted({n for n in indexes if indexes.count(n) > 1})
    assert not doublons, f"décisions citées deux fois dans l'index : {doublons}"

    sans_ligne = sorted(fiches - set(indexes))
    assert not sans_ligne, (
        "ces décisions existent sous docs/decisions/ mais n'ont pas de ligne dans "
        f"docs/technical_decisions.md — ajoutez-la en tête de la liste : {sans_ligne}")

    sans_fichier = sorted(set(indexes) - fiches)
    assert not sans_fichier, (
        "ces lignes d'index ne désignent aucun fichier de docs/decisions/ : "
        f"{sans_fichier}")


def test_lindex_conserve_toutes_les_ancres_dorigine():
    """Des centaines de liens `docs/technical_decisions.md#<ancre>` vivent dans les
    commentaires d'issues GitHub, hors du dépôt et non réécrivables. Toute ancre
    définie dans une décision doit donc rester déclarée sur sa ligne d'index, sans
    quoi le vieux lien atterrit en haut de page au lieu de la bonne décision."""
    texte = INDEX.read_text(encoding="utf-8")
    dans_index = set(_ANCRE.findall(texte))
    absentes = {}
    for nom, ancres in _decisions().items():
        manquantes = sorted(a for a in ancres if a not in dans_index)
        if manquantes:
            absentes[nom] = manquantes
    assert not absentes, (
        "ces ancres sont définies dans une décision mais absentes de l'index : "
        f"{absentes}")


def test_rien_ne_renvoie_vers_larchive():
    """`docs/archive/` est la copie figée d'avant la découpe (30/08/2026). Elle
    n'est plus mise à jour et ses ancres sont préfixées `archive-` exprès. Un
    renvoi vers elle est un renvoi vers une règle possiblement remplacée."""
    coupables = []
    for chemin in _fichiers_balayes():
        relatif = chemin.relative_to(RACINE).as_posix()
        if relatif.startswith("docs/archive/") or relatif in _NOMMENT_LARCHIVE:
            continue
        if _RENVOI_ARCHIVE.search(_lire(chemin)):
            coupables.append(relatif)
    assert not coupables, (
        "ces fichiers renvoient vers l'archive figée au lieu de la décision vivante "
        f"de docs/decisions/ : {sorted(coupables)}")


# ---------------------------------------------------------------------------
# #840 — l'index est GÉNÉRÉ, il ne s'édite plus
# ---------------------------------------------------------------------------
#
# Il était maintenu à la main, et tous les lots y écrivaient au même endroit :
# une ligne insérée en tête, à chaque décision. Deux branches parallèles
# conflictaient donc systématiquement — quatre rebases en une heure le
# 10/09/2026, sur des lots qui ne se recouvraient pas.

def test_lindex_committe_est_celui_que_le_script_produit():
    """La dérive se voit ici, pas au prochain conflit de fusion.

    Même contrat que `tests/test_decisions_par_module.py` : un fichier généré
    qui a été édité à la main ne se rattrape nulle part ailleurs.
    """
    import subprocess
    import sys

    resultat = subprocess.run(
        [sys.executable, "scripts/generer_index_decisions.py", "--verifier"],
        cwd=RACINE, capture_output=True, text=True,
    )
    assert resultat.returncode == 0, (
        "`docs/technical_decisions.md` ne correspond plus aux fichiers de "
        "`docs/decisions/`. Il ne s'édite pas à la main : lancer "
        "`python3 scripts/generer_index_decisions.py`.\n"
        f"{resultat.stderr}"
    )


def test_chaque_decision_porte_de_quoi_produire_sa_ligne():
    """Un titre, une date, un résumé. Le script refuse d'inventer ce qui manque.

    Une décision sans `> **En bref** — …` sortirait de l'index en silence, ce
    qui est exactement ce que l'index maintenu à la main risquait à chaque
    oubli d'insertion.
    """
    import sys

    sys.path.insert(0, str(RACINE / "scripts"))
    from generer_index_decisions import DecisionIncomplete, lire_decision

    manquantes = []
    for chemin in sorted((RACINE / "docs" / "decisions").glob("*.md")):
        try:
            lire_decision(chemin)
        except DecisionIncomplete as exc:
            manquantes.append(str(exc))
    assert not manquantes, "\n".join(manquantes)
