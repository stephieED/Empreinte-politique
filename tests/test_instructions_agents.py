"""Garde-fou : une seule source d'instructions, plusieurs noms de fichiers.

`AGENTS.md` est la source. Les outils qui attendent un autre nom — Claude Code
lit `CLAUDE.md`, GitHub Copilot lit `.github/copilot-instructions.md` — y
accèdent par un **lien symbolique**, pas par une copie.

Pourquoi un lien et pas une copie synchronisée : une copie **peut** diverger,
on ne fait que le détecter. Un lien ne le peut pas, c'est le même objet. La
dérive n'est pas surveillée, elle est impossible.

Ce que ce test attrape, et qu'un lien seul ne dit pas :

1. un checkout Windows sans `core.symlinks=true`, qui remplace le lien par un
   fichier texte d'une ligne contenant le chemin — silencieusement, et un agent
   lirait alors « AGENTS.md » au lieu des instructions ;
2. quelqu'un qui remplace le lien par une copie, croyant simplifier ;
3. un nouvel outil ajouté avec son fichier, sans lien.

Il ne dit RIEN de ce que chaque outil fait du lien : qu'un chargeur le suive
est une propriété de l'outil, constatable seulement en l'exécutant. Ce test
garantit la source unique, pas la lecture.

Constaté le 30/08/2026, hors de ce test : **Claude Code suit le lien** — une
session neuve charge `CLAUDE.md` et porte les onze sections d'`AGENTS.md`.
**Copilot n'a pas été vérifié.** Voir
`docs/decisions/instructions-une-source-plusieurs-noms.md`.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

import _outils_ci

RACINE = Path(__file__).resolve().parent.parent
SOURCE = "AGENTS.md"

# nom du fichier attendu par l'outil -> cible relative, depuis son répertoire
ALIAS: dict[str, str] = {
    "CLAUDE.md": SOURCE,
    ".github/copilot-instructions.md": f"../{SOURCE}",
}


def test_la_source_existe_et_nest_pas_un_lien():
    """`AGENTS.md` est le fichier réel — pas un alias d'autre chose."""
    source = RACINE / SOURCE
    assert source.is_file(), f"{SOURCE} manquant"
    assert not source.is_symlink(), (
        f"{SOURCE} est devenu un lien : la source doit rester le fichier réel, "
        "sinon la chaîne d'alias n'a plus d'origine."
    )


@pytest.mark.parametrize("alias", sorted(ALIAS))
def test_chaque_alias_est_un_lien_vers_la_source(alias: str):
    chemin = RACINE / alias
    assert chemin.exists(), (
        f"`{alias}` manquant. Les outils qui attendent ce nom ne liront aucune "
        f"instruction. Le poser : `ln -s {ALIAS[alias]} {alias}`."
    )
    assert chemin.is_symlink(), (
        f"`{alias}` n'est pas un lien symbolique mais un fichier ordinaire. "
        "Deux causes : un checkout Windows sans `core.symlinks=true` (le fichier "
        f"contient alors la chaîne « {ALIAS[alias]} »), ou une copie posée à la "
        "main. Une copie diverge ; le lien est la seule forme qui ne le peut pas."
    )
    cible = os.readlink(chemin)
    assert cible == ALIAS[alias], (
        f"`{alias}` pointe vers « {cible} », attendu « {ALIAS[alias]} »."
    )


@pytest.mark.parametrize("alias", sorted(ALIAS))
def test_chaque_alias_rend_le_contenu_de_la_source(alias: str):
    """Le lien résout, et il résout au bon endroit.

    `is_symlink` ne dit pas que la cible existe : un lien cassé le passerait.
    """
    lu = (RACINE / alias).read_text(encoding="utf-8")
    attendu = (RACINE / SOURCE).read_text(encoding="utf-8")
    assert lu == attendu, (
        f"`{alias}` ne rend pas le contenu de {SOURCE} — lien cassé, ou cible "
        "déplacée."
    )


def test_chaque_alias_est_dans_la_liste_blanche_du_sparse_checkout():
    """Un test qui lit un fichier hors du checkout CI échoue là, et nulle part ailleurs.

    `tests.yml` ne matérialise qu'une liste blanche : tout ce qui n'y figure pas
    est absent du disque du runner. Un test portant sur un fichier hors liste
    passe en local et échoue en CI — sur un `FileNotFoundError` qui ne dit rien
    de la vraie cause.

    Le piège s'est produit **trois fois** : #434 (les tests du bornage), #520
    (`.gitignore`, run 32773016491), puis ce lot-ci avec `CLAUDE.md`. Le
    commentaire du workflow l'annonçait déjà les deux dernières fois. Un
    avertissement en prose ne suffit pas ; celui-ci échoue.

    Il ne couvre que les alias de ce fichier. Le cas général — tout chemin lu
    par un test doit être dans la liste — demanderait une analyse statique.

    Le bloc est analysé par `tests/_outils_ci.py`, partagé avec `conftest.py`
    et `test_ci_perimetre_sparse_checkout.py`.
    """
    liste = _outils_ci.lire_liste_blanche(
        RACINE / ".github" / "workflows" / "tests.yml")
    assert liste, (
        "bloc `sparse-checkout: |` absent, vide ou de forme inattendue dans "
        "tests.yml — sans lui ce test serait vrai par vacuité. Voir "
        "`tests/_outils_ci.lire_liste_blanche`.")

    for alias in sorted(ALIAS):
        racine_du_chemin = alias.split("/")[0]
        assert racine_du_chemin in liste, (
            f"`{alias}` n'est couvert par aucune entrée de la liste blanche de "
            f"`tests.yml` (cherché « {racine_du_chemin} »). Le runner ne le "
            "matérialisera pas, et les tests ci-dessus échoueront en CI en "
            "passant en local. Ajouter l'entrée dans le `sparse-checkout:` du "
            "workflow."
        )
