#!/usr/bin/env python3
"""
generer_decisions_par_module.py — La table inversée `ce module → ces décisions`.

`docs/technical_decisions.md` va des **décisions vers le code** et se lit par
date. Rien n'allait du **code vers ses décisions**, sauf quand quelqu'un avait
pensé à écrire le renvoi dans le module. C'est donc inégalement posé, et ça se
re-troue à chaque module créé : mesuré le 30/08/2026, `src/merge_profile.py`
citait **zéro** décision alors que 39 nomment une de ses fonctions — exactement le
module de l'épic #598, dont personne n'avait relu la politique de fusion.

Le lien est **déjà dans la donnée** : chaque décision nomme les fonctions qu'elle
gouverne. Il n'était simplement pas présenté dans ce sens. Ce script le retourne
et écrit `docs/decisions-par-module.md`. Généré, jamais tenu à la main — une
table manuelle diverge, et ce dépôt a corrigé trois fois ce défaut le 30/08.

Le pourquoi complet : `docs/decisions/table-inversee-decisions-par-module.md`.

Usage :
    python3 scripts/generer_decisions_par_module.py            # écrit le fichier
    python3 scripts/generer_decisions_par_module.py --verifier # échoue s'il a dérivé

`tests/test_decisions_par_module.py` rejoue les deux.
"""

import argparse
import ast
import re
import sys
from functools import lru_cache
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "src"
DECISIONS = RACINE / "docs" / "decisions"
SORTIE = RACINE / "docs" / "decisions-par-module.md"

#: Modules dont la table ne dit rien d'utile : ce sont des passes de migration
#: datées, écrites pour un lot et conservées comme trace, pas du code qu'une
#: décision gouverne encore.
_PREFIXES_IGNORES = ("migrer_",)

#: Un symbole trop court ou sans séparateur se confond avec un mot de la prose.
#: `merge_raw_dirs` ne se confond avec rien ; `gha` ou `main`, si.
_LONGUEUR_MINIMALE_SANS_SOUS_TIRET = 10

#: Symboles écartés malgré la règle ci-dessus : ils sont le vocabulaire **métier**
#: du produit avant d'être des noms de code, et une décision qui les emploie parle
#: de la donnée, pas de la fonction.
_SYMBOLES_TROP_COMMUNS = frozenset({
    "CHAMBRE_DEPUTES", "CHAMBRE_SENAT", "LEGISLATURES_FIGEES", "LEGISLATURE_COURANTE",
})

#: La seule décision écartée du balayage, et la seule raison qui l'autorise :
#: elle porte sur **le critère lui-même**, et ses exemples sont des exemples.
#: Sans cette ligne, elle « gouvernerait » les quatre modules dont elle cite une
#: fonction pour illustrer une forme d'écriture. Ce n'est pas une porte de
#: sortie pour une décision qu'on préférerait ne pas citer.
_DECISIONS_IGNOREES = frozenset({"table-inversee-decisions-par-module"})

_RENVOI_DECISION = re.compile(r'(?:docs/)?decisions/([a-z0-9-]+)\.md')


def modules_du_depot():
    """`{nom de module: chemin}` pour `src/*.py`, hors passes de migration."""
    return {
        chemin.stem: chemin
        for chemin in sorted(SRC.glob("*.py"))
        if not chemin.stem.startswith(_PREFIXES_IGNORES)
    }


def symboles_de_tete(chemin):
    """Les noms définis **au niveau du module** : fonctions, classes, constantes.

    Rien d'imbriqué : une méthode ou une fonction interne n'est pas ce qu'une
    décision cite, et son nom se répète d'une classe à l'autre.
    """
    try:
        arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    except OSError:
        return set()
    except SyntaxError as exc:
        # Un module qu'on ne sait pas lire était IGNORÉ, et la table sortait
        # amputée de tout ce qu'il nomme — sans erreur. C'est ce qui arrivait
        # sous Python 3.11, où `src/an_roster.py` (une f-string à antislash,
        # légale depuis 3.12) ne se lit pas : la table générée différait de
        # celle de la CI, et rien ne le disait (11/09/2026).
        raise SystemExit(
            f"{chemin} ne se lit pas sous Python "
            f"{sys.version_info[0]}.{sys.version_info[1]} : {exc}. "
            "Une table qui l'ignorerait serait fausse sans le dire."
        ) from exc
    noms = set()
    for noeud in arbre.body:
        if isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            noms.add(noeud.name)
        elif isinstance(noeud, ast.Assign):
            for cible in noeud.targets:
                if isinstance(cible, ast.Name):
                    noms.add(cible.id)
        elif isinstance(noeud, ast.AnnAssign) and isinstance(noeud.target, ast.Name):
            noms.add(noeud.target.id)
    return {
        nom for nom in noms
        if nom not in _SYMBOLES_TROP_COMMUNS
        and nom != chemin.stem  # `normalize_europarl.normalize_europarl` : le nommer,
        # c'est nommer le module, pas un morceau de son code.
        and ("_" in nom.strip("_") or len(nom) >= _LONGUEUR_MINIMALE_SANS_SOUS_TIRET)
    }


def index_des_symboles(modules):
    """`{symbole: {modules qui le définissent}}` — l'unicité décide plus bas."""
    index = {}
    for nom, chemin in modules.items():
        for symbole in symboles_de_tete(chemin):
            index.setdefault(symbole, set()).add(nom)
    return index


#: Une décision qui parle de code l'écrit en code. Exiger le dos d'accent pour la
#: forme nue écarte la coïncidence de prose, et coûte zéro faux négatif mesuré :
#: les 168 décisions écrivent toutes leurs symboles entre accents.
_SPAN_CODE = re.compile(r'`([^`\n]+)`')
_IDENTIFIANT = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
#: `merge_profile.fusionner_couverture`, `merge_profile.py::merge_raw_dirs`. Le
#: symbole est capturé sans être consommé, pour que `a.b.c` rende `(a, b)` **et**
#: `(b, c)`.
_QUALIFIE = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)(?:\.py)?(?:\.|::)(?=([A-Za-z_][A-Za-z0-9_]*))')


@lru_cache(maxsize=None)
def _jetons(texte):
    """`(identifiants du texte, identifiants entre dos d'accent, couples qualifiés)`.

    Une seule passe par décision : le balayage naïf — un `re.search` par couple
    (module, symbole) — coûtait 90 s sur les 168 décisions et les 62 modules.
    """
    code = "\n".join(_SPAN_CODE.findall(texte))
    return (frozenset(_IDENTIFIANT.findall(texte)),
            frozenset(_IDENTIFIANT.findall(code)),
            frozenset(_QUALIFIE.findall(texte)))


def nomme_le_module(texte, module):
    """`texte` écrit le nom du module — le critère « mentionne »."""
    return module in _jetons(texte)[0]


def symboles_nommes(texte, module, symboles, index):
    """Les symboles de `module` que `texte` nomme — le critère « gouverne ».

    Deux formes acceptées, et une seule raison de les accepter : dans les deux,
    la décision parle d'un **morceau de code nommé**, pas du fichier.

    - **qualifiée** — `merge_profile.fusionner_couverture`,
      `merge_profile.py::merge_raw_dirs` : le module lève toute ambiguïté ;
    - **nue, entre dos d'accent** — `` `clean_stale_interventions` ``, à condition
      que le symbole soit défini dans **ce seul** module de `src/`. Un symbole
      partagé ne désigne personne.
    """
    _, dans_le_code, qualifies = _jetons(texte)
    trouves = {symbole for symbole in symboles if (module, symbole) in qualifies}
    trouves |= {
        symbole for symbole in symboles & dans_le_code
        if index.get(symbole) == {module}
    }
    return trouves


def analyser():
    """`{module: {"gouvernent": {décision: [symboles]}, "mentionnent": [décisions],
    "cite": [décisions citées par le module]}}`."""
    modules = modules_du_depot()
    index = index_des_symboles(modules)
    symboles_par_module = {nom: symboles_de_tete(chemin) for nom, chemin in modules.items()}

    resultat = {
        nom: {
            "gouvernent": {},
            "mentionnent": [],
            "cite": sorted(set(_RENVOI_DECISION.findall(chemin.read_text(encoding="utf-8")))),
        }
        for nom, chemin in modules.items()
    }

    for fiche in sorted(DECISIONS.glob("*.md")):
        if fiche.stem in _DECISIONS_IGNOREES:
            continue
        texte = fiche.read_text(encoding="utf-8")
        for nom in modules:
            gouvernes = symboles_nommes(texte, nom, symboles_par_module[nom], index)
            if gouvernes:
                resultat[nom]["gouvernent"][fiche.stem] = sorted(gouvernes)
            elif nomme_le_module(texte, nom):
                resultat[nom]["mentionnent"].append(fiche.stem)
    return resultat


@lru_cache(maxsize=None)
def _titre(fiche):
    for ligne in (DECISIONS / f"{fiche}.md").read_text(encoding="utf-8").split("\n"):
        if ligne.startswith("# "):
            return ligne[2:].strip()
    return fiche


def rendre(analyse):
    """Le fichier Markdown, à partir de l'analyse. Aucune lecture de disque ici."""
    troues = sorted(
        (nom for nom, d in analyse.items() if d["gouvernent"] and not d["cite"]),
        key=lambda n: (-len(analyse[n]["gouvernent"]), n))

    lignes = [
        "# Les décisions qui gouvernent chaque module",
        "",
        "**Fichier généré — ne pas le modifier à la main.**",
        "`python3 scripts/generer_decisions_par_module.py` le réécrit ;",
        "`tests/test_decisions_par_module.py` échoue s'il a dérivé.",
        "",
        "[`docs/technical_decisions.md`](technical_decisions.md) va des décisions vers le",
        "code et se lit par date. Cette table va dans l'autre sens : **ce module → ces",
        "décisions**, pour qu'un agent qui ouvre un fichier de `src/` sache ce qui le",
        f"gouverne sans avoir à fouiller les {len(list(DECISIONS.glob('*.md')))} décisions",
        "du répertoire. Le critère, ce qu'il rate et pourquoi la table est générée :",
        "[`docs/decisions/table-inversee-decisions-par-module.md`]"
        "(decisions/table-inversee-decisions-par-module.md).",
        "",
        "## Ce que « gouverne » veut dire ici",
        "",
        "Une décision **gouverne** un module quand elle nomme **un symbole de tête de ce",
        "module** — une fonction, une classe ou une constante définie au niveau du module —",
        "soit qualifié (`merge_profile.fusionner_couverture`), soit nu à condition que ce",
        "symbole soit défini dans ce seul module de `src/`. La colonne « nomme » dit",
        "lesquels.",
        "",
        "Une décision qui ne nomme que le **fichier** (`merge_profile.py`) ou le module nu",
        "le **mentionne** sans le gouverner : elle dit qu'il est concerné, pas quel contrat",
        "il doit tenir. Ces décisions-là sont listées à part, en fin de section.",
        "",
        "Le critère est mécanique et volontairement faillible dans un sens précis : il rate",
        "une décision qui gouverne un module sans nommer aucune de ses fonctions. En",
        "échange il ne rouille pas — un symbole renommé ou supprimé retire le lien au lieu",
        "de le laisser pointer vers du code qui n'existe plus.",
        "",
        "---",
        "",
    ]

    if troues:
        lignes += [
            "## Les modules qui ne citent aucune de leurs décisions",
            "",
            "Ce que ce fichier existe pour rendre visible. `tests/test_decisions_par_module.py`",
            "échoue au-delà du seuil qu'il fixe.",
            "",
            "| Module | Décisions qui le gouvernent |",
            "| --- | ---: |",
        ]
        lignes += [f"| `src/{nom}.py` | {len(analyse[nom]['gouvernent'])} |" for nom in troues]
        lignes += ["", "---", ""]

    for nom in sorted(analyse):
        fiche = analyse[nom]
        if not fiche["gouvernent"] and not fiche["mentionnent"]:
            continue
        lignes += [f"## `src/{nom}.py`", ""]
        if fiche["gouvernent"]:
            lignes += [
                f"{len(fiche['gouvernent'])} décision(s) le gouvernent ; le module en cite "
                f"{len(fiche['cite'])}.",
                "",
                "| Décision | Nomme |",
                "| --- | --- |",
            ]
            for decision in sorted(fiche["gouvernent"]):
                symboles = ", ".join(f"`{s}`" for s in fiche["gouvernent"][decision])
                lignes.append(
                    f"| [{_titre(decision)}](decisions/{decision}.md) | {symboles} |")
            lignes.append("")
        if fiche["mentionnent"]:
            noms = ", ".join(
                f"[`{d}`](decisions/{d}.md)" for d in sorted(fiche["mentionnent"]))
            lignes += [f"Le mentionnent sans le gouverner : {noms}.", ""]
    return "\n".join(lignes).rstrip("\n") + "\n"


#: La version du dépôt : celle de la CI (`setup-python`, `tests.yml` et
#: `generate-data.yml`). `src/` en emploie la syntaxe.
VERSION_MINIMALE = (3, 12)


def main(argv=None):
    if tuple(sys.version_info[:2]) < VERSION_MINIMALE:
        print(
            f"Python {sys.version_info[0]}.{sys.version_info[1]} : ce script "
            f"exige {VERSION_MINIMALE[0]}.{VERSION_MINIMALE[1]}, la version du dépôt. "
            "Sous une version plus ancienne, des modules de src/ ne se lisent pas "
            "et la table sortirait différente de celle de la CI. Lancer "
            "`python3.12 scripts/generer_decisions_par_module.py`, ou le Python du venv.",
            file=sys.stderr,
        )
        return 2
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parseur.add_argument(
        "--verifier", action="store_true",
        help="ne rien écrire ; sortir 1 si le fichier committé a dérivé du dépôt")
    arguments = parseur.parse_args(argv)

    attendu = rendre(analyser())
    if arguments.verifier:
        actuel = SORTIE.read_text(encoding="utf-8") if SORTIE.exists() else ""
        if actuel != attendu:
            print(f"{SORTIE.relative_to(RACINE)} a dérivé — relancer "
                  "`python3 scripts/generer_decisions_par_module.py`.", file=sys.stderr)
            return 1
        print(f"{SORTIE.relative_to(RACINE)} est à jour.")
        return 0
    SORTIE.write_text(attendu, encoding="utf-8")
    print(f"{SORTIE.relative_to(RACINE)} écrit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
