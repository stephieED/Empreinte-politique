"""Les commandes de `docs/commandes.md` ne mentionnent rien qui n'existe pas.

Une doc de commandes se périme en silence : une option renommée dans un
`argparse` ne fait rougir personne, et la ligne qui la cite continue d'être lue
et recopiée. Le dépôt l'a vécu deux fois le 30/08/2026 — cinq inputs de
workflow disparus, encore cités 17 fois, et une doc renvoyant vers un fichier
jamais créé.

Ce test transforme cette dérive en échec de suite. Pour chaque commande citée
dans un bloc ```bash de `docs/commandes.md` :

1. **le script existe** — le chemin est résolu depuis la racine du dépôt ;
2. **chaque option longue citée est déclarée** — pour un module Python, en
   relevant les littéraux `add_argument("--…")` de son AST ; pour un script
   shell, en cherchant l'option dans son texte. Aucun script n'est exécuté :
   ni `--help`, ni import, donc aucun effet de bord et aucun appel réseau
   (#473).

Les tableaux d'options sont contrôlés aussi : les `` `--option` `` d'une ligne
de tableau sont rapportés au **dernier script cité avant elle**, qui est la
structure du fichier (le tableau commente la commande qui le précède). Une prose
citant une option en passant échappe au contrôle — c'est assumé : l'attribuer à
un script demanderait de deviner.

Périmètre : `docs/`, `src/` et `scripts/` sont tous les trois dans la liste
blanche du sparse-checkout de `tests.yml`, donc ce test lit en CI ce qu'il lit
en local (#434, #518, #520).
"""

import ast
import re
import shlex
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
COMMANDES = RACINE / "docs" / "commandes.md"

#: Ce que l'on accepte de voir en tête d'une ligne sans qu'il s'agisse d'un
#: exécutable du dépôt : outils tiers et primitives shell. Tout le reste doit
#: résoudre vers un fichier versionné.
_HORS_DEPOT = {"npm", "pytest", "cd", "tail", "kill", "git", "source", "pip"}

#: `python3 -m pytest`, `python3 -m http.server` : le module n'est pas un
#: fichier du dépôt.
#: `node web/UI_finale/scripts/…` : l'interpréteur n'est pas du dépôt, le
#: script qui suit l'est (#969).
_INTERPRETEURS = {"python", "python3", "node"}

_OPTION_LONGUE = re.compile(r"^--[a-z0-9][a-z0-9-]*$")
_OPTION_EN_TABLEAU = re.compile(r"`(--[a-z0-9][a-z0-9-]*)")
_AFFECTATION = re.compile(r"^[A-Z_][A-Z0-9_]*=")


def _decoupe(ligne: str) -> tuple[str | None, list[str]]:
    """(chemin du script relatif à la racine, options longues citées).

    Rend `(None, [])` pour une commande qui ne désigne pas un exécutable du
    dépôt (`npm run dev`, `pytest -q`, `python3 -m http.server`).
    """
    jetons = shlex.split(ligne, comments=True)
    while jetons and _AFFECTATION.match(jetons[0]):
        jetons.pop(0)
    if not jetons:
        return None, []

    tete = jetons.pop(0)
    if tete in _INTERPRETEURS:
        if not jetons or jetons[0] == "-m":
            return None, []
        script = jetons.pop(0)
    elif tete in _HORS_DEPOT:
        return None, []
    else:
        script = tete

    script = script[2:] if script.startswith("./") else script
    options = [j.split("=", 1)[0] for j in jetons]
    return script, [o for o in options if _OPTION_LONGUE.match(o)]


def _options_declarees(script: Path) -> set[str]:
    """Les options longues qu'un exécutable déclare, sans l'exécuter."""
    texte = script.read_text(encoding="utf-8")
    if script.suffix != ".py":
        # Un script shell déclare ses options dans un `case`/`if` : le
        # littéral doit au moins figurer dans le fichier.
        return {opt for opt in re.findall(r"--[a-z0-9][a-z0-9-]*", texte)}
    declarees = set()
    for noeud in ast.walk(ast.parse(texte)):
        if (isinstance(noeud, ast.Call)
                and isinstance(noeud.func, ast.Attribute)
                and noeud.func.attr == "add_argument"):
            for arg in noeud.args:
                if (isinstance(arg, ast.Constant)
                        and isinstance(arg.value, str)
                        and arg.value.startswith("--")):
                    declarees.add(arg.value)
    return declarees


def _commandes_documentees() -> list[tuple[str, list[str]]]:
    """(script, options) pour chaque commande du fichier, tableaux compris.

    Une seule passe linéaire, pour que « le dernier script cité » soit celui
    qui précède réellement le tableau dans le fichier.
    """
    releve: list[tuple[str, list[str]]] = []
    dernier: str | None = None
    dans_bash = False
    courante = ""

    for ligne in COMMANDES.read_text(encoding="utf-8").split("\n"):
        nue = ligne.strip()
        if nue.startswith("```"):
            dans_bash = nue == "```bash"
            assert not courante, f"continuation `\\` non terminée : {courante!r}"
            continue
        if dans_bash:
            if not nue or nue.startswith("#"):
                continue
            if nue.endswith("\\"):
                courante += nue[:-1] + " "
                continue
            script, options = _decoupe((courante + nue).strip())
            courante = ""
            if script is not None:
                releve.append((script, options))
                dernier = script
            continue
        if nue.startswith("|") and dernier is not None:
            options = _OPTION_EN_TABLEAU.findall(nue)
            if options:
                releve.append((dernier, options))

    assert releve, "aucune commande relevée dans docs/commandes.md"
    return releve


COMMANDES_DOCUMENTEES = _commandes_documentees()


def test_le_fichier_des_commandes_existe():
    assert COMMANDES.is_file(), (
        "docs/commandes.md est le foyer des commandes du dépôt (AGENTS.md §8)")


@pytest.mark.parametrize(
    "script", sorted({s for s, _ in COMMANDES_DOCUMENTEES}))
def test_le_script_documente_existe(script):
    assert (RACINE / script).is_file(), (
        f"docs/commandes.md cite `{script}`, qui n'existe pas dans le dépôt")


@pytest.mark.parametrize(
    "script,options",
    [(s, tuple(o)) for s, o in COMMANDES_DOCUMENTEES if o],
    ids=lambda v: v if isinstance(v, str) else "+".join(v))
def test_les_options_documentees_sont_declarees(script, options):
    chemin = RACINE / script
    assert chemin.is_file(), f"docs/commandes.md cite `{script}`, absent du dépôt"
    declarees = _options_declarees(chemin)
    inconnues = sorted(set(options) - declarees)
    assert not inconnues, (
        f"docs/commandes.md cite {inconnues} pour `{script}`, qui ne "
        f"la/les déclare pas — option renommée ou retirée du code, doc restée "
        f"en place")


def test_toute_commande_relevee_porte_un_chemin_du_depot():
    """Le relevé ne doit pas se vider en silence : si le format du fichier
    change (blocs non ```bash, par exemple), les deux tests ci-dessus
    passeraient sur une liste vide."""
    scripts = {s for s, _ in COMMANDES_DOCUMENTEES}
    assert len(scripts) >= 25, (
        f"seulement {len(scripts)} scripts relevés dans docs/commandes.md — "
        "le format des blocs de commande a probablement changé")
    hors_arbo = sorted(
        s for s in scripts
        if not (s.startswith("src/") or s.startswith("scripts/")
                or s.startswith("web/UI_finale/scripts/")))
    assert not hors_arbo, (
        f"chemins inattendus dans docs/commandes.md : {hors_arbo}")
