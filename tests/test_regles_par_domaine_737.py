#!/usr/bin/env python3
"""
test_regles_par_domaine_737.py — Une règle sortie d'`AGENTS.md` reste
atteignable, et le renvoi qui la désigne continue de résoudre (#737).

`AGENTS.md` faisait 983 lignes, dont **738 ne servaient qu'à qui touche un
module donné** — et il est chargé à chaque session, pour toute tâche. C'est ce
qui le rendait instable : chaque lot ajoutait sa puce, parce que la §3 était le
seul endroit où l'on savait qu'un agent la lirait.

La scission ne vaut que si deux choses tiennent, et ce sont elles qu'on teste :

1. **les renvois continuent de résoudre.** Le dépôt cite « AGENTS.md §X » près de
   600 fois, dans 200 fichiers. Réécrire ces renvois serait un lot à soi seul, et
   les laisser pourrir serait pire : chaque section citée doit donc rester
   nommée dans `AGENTS.md`, fût-ce par une ligne d'index ;
2. **rien n'a disparu.** Un fichier de règles vide, ou absent de l'index, rendrait
   la scission indétectable — c'est le trou muet de #510, appliqué à la doc.
"""

from pathlib import Path
import re

import pytest

RACINE = Path(__file__).resolve().parents[1]
AGENTS = RACINE / "AGENTS.md"
REGLES = RACINE / "docs" / "regles"

#: Les fichiers de domaine, et la section dont ils sont issus.
DOMAINES: dict[str, str] = {
    "fusion-et-index.md": "§3a",
    "ci.md": "§3b",
    "gardes-avant-commit.md": "§3c",
    "roster-et-sources.md": "§3d",
    "interventions-syceron.md": "§3e",
    "portail-qualite.md": "§3f",
    "schema-pivot.md": "§4",
    "champs-sensibles.md": "§5",
}

#: Extensions parcourues pour relever les renvois. `.json` est exclu : les
#: données ne citent pas les instructions.
SOURCES = ("*.py", "*.md", "*.yml", "*.yaml", "*.js", "*.jsx")

_RENVOI = re.compile(r"AGENTS\.md\s+§(\d+[a-f]?)")


def _texte_agents() -> str:
    return AGENTS.read_text(encoding="utf-8")


def _sections_citees() -> set[str]:
    citees: set[str] = set()
    for motif in SOURCES:
        for chemin in RACINE.rglob(motif):
            if any(p in chemin.parts for p in (".git", "node_modules", ".venv", "dist")):
                continue
            try:
                citees.update(_RENVOI.findall(chemin.read_text(encoding="utf-8")))
            except (OSError, UnicodeDecodeError):
                continue
    return citees


# --------------------------------------------------------------------------
# 1. Les fichiers de domaine existent et disent d'où ils viennent
# --------------------------------------------------------------------------

@pytest.mark.parametrize("nom", sorted(DOMAINES))
def test_chaque_fichier_de_domaine_existe_et_nest_pas_vide(nom: str):
    chemin = REGLES / nom
    assert chemin.is_file(), (
        f"`docs/regles/{nom}` a disparu. Les règles qu'il portait sont sorties "
        "d'AGENTS.md : sans lui, elles ne sont plus nulle part.")
    # Un fichier réduit à son en-tête serait une scission qui a perdu son contenu.
    assert len(chemin.read_text(encoding="utf-8").splitlines()) > 20, (
        f"`docs/regles/{nom}` est quasi vide — une scission silencieuse.")


@pytest.mark.parametrize("nom,section", sorted(DOMAINES.items()))
def test_chaque_fichier_de_domaine_nomme_sa_section_dorigine(nom: str, section: str):
    """Un renvoi « AGENTS.md §3a » doit tomber sur quelque chose qui se
    reconnaît comme §3a, sinon le lecteur doit deviner."""
    assert section in (REGLES / nom).read_text(encoding="utf-8"), (
        f"`docs/regles/{nom}` ne dit pas qu'il porte {section}.")


@pytest.mark.parametrize("nom", sorted(DOMAINES))
def test_agents_indexe_chaque_fichier_de_domaine(nom: str):
    """Un fichier de règles que l'index ne nomme pas n'est lu par personne."""
    assert f"docs/regles/{nom}" in _texte_agents(), (
        f"`docs/regles/{nom}` n'est cité nulle part dans AGENTS.md : aucun agent "
        "ne saura qu'il faut l'ouvrir.")


# --------------------------------------------------------------------------
# 2. Les renvois du dépôt continuent de résoudre
# --------------------------------------------------------------------------

def test_toute_section_citee_dans_le_depot_est_nommee_dans_agents():
    """Près de 600 renvois « AGENTS.md §X » vivent dans le dépôt. Déplacer une
    section sans laisser sa ligne d'index les invaliderait tous en silence."""
    texte = _texte_agents()
    manquantes = sorted(
        s for s in _sections_citees()
        if f"§{s}" not in texte and not re.search(rf"^#+ {re.escape(s[0])}\.", texte, re.M)
    )
    assert not manquantes, (
        f"ces sections sont citées dans le dépôt mais ne sont plus nommées dans "
        f"AGENTS.md : {manquantes}. Un renvoi qui ne résout plus est pire qu'un "
        "renvoi absent — il donne l'illusion d'une règle consultable.")


def test_le_releve_des_renvois_nest_pas_vide():
    """Compteur-témoin : si le relevé cessait de rien trouver, le test
    ci-dessus passerait pour de bonnes raisons apparentes (#510)."""
    assert len(_sections_citees()) >= 8


# --------------------------------------------------------------------------
# 3. Ce qu'AGENTS.md doit garder
# --------------------------------------------------------------------------

def test_agents_reste_court():
    """La scission n'a de valeur que si le fichier reste court. Le seuil est
    haut exprès : il refuse le retour à 983 lignes, pas la prochaine règle."""
    n = len(_texte_agents().splitlines())
    assert n <= 500, (
        f"AGENTS.md fait {n} lignes. Une règle qui ne gouverne qu'un module va "
        "dans `docs/regles/`, jamais ici — c'est ce que #737 a démêlé.")


def test_les_regles_editoriales_restent_dans_agents():
    """La §2 est citée ~430 fois et ne se délègue pas : c'est la seule section
    qu'un agent doit avoir sous les yeux sans savoir qu'il en a besoin."""
    texte = _texte_agents()
    assert "## 2. Non-negotiable editorial rules" in texte
    for regle in ("No value judgments", "Full traceability", "Missing data means missing data"):
        assert regle in texte, f"la règle éditoriale « {regle} » a quitté AGENTS.md."
