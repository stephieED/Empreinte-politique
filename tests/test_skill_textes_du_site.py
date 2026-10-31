"""La skill `textes-du-site` reste légère à chaque usage.

Ses exemples grossissent à chaque correction de la propriétaire (SKILL.md §6).
Deux règles les bornent : trois fois la même correction devient une règle, et
un fichier d'exemples ne dépasse pas 6 000 octets. La seconde se vérifie ici,
sinon elle s'oublie. La skill doit aussi nommer chacun de ses fichiers
d'exemples, faute de quoi un agent ne le lirait jamais.
"""

from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "textes-du-site"
PLAFOND = 6000
EXEMPLES = sorted((SKILL / "exemples").glob("*.md"))


def test_la_skill_a_des_exemples() -> None:
    assert EXEMPLES, "aucun fichier d'exemples dans .claude/skills/textes-du-site/exemples/"


@pytest.mark.parametrize("fichier", EXEMPLES, ids=lambda f: f.name)
def test_un_fichier_d_exemples_reste_sous_le_plafond(fichier: Path) -> None:
    taille = len(fichier.read_bytes())
    assert taille <= PLAFOND, (
        f"{fichier.name} : {taille} octets pour un plafond de {PLAFOND}. "
        "Avant d'ajouter une paire, fusionner celles qui disent la même chose "
        "en une règle de SKILL.md (§2 ou §3) et ne garder qu'un exemple (SKILL.md §6)."
    )


@pytest.mark.parametrize("fichier", EXEMPLES, ids=lambda f: f.name)
def test_la_skill_nomme_chaque_fichier_d_exemples(fichier: Path) -> None:
    texte = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert f"exemples/{fichier.name}" in texte, (
        f"SKILL.md ne nomme pas exemples/{fichier.name} : aucun agent ne le lira."
    )
