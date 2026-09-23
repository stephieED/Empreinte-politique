"""#1101 — l'artifact des amendements arrive AVANT les étapes qui le lisent.

`merge-and-pivot` lit `.cache/amendements_an` à deux titres : le quality gate
(§3d, fraîcheur des index) et, depuis #1092, `publier_contenus`, qui publie
`pivot_data/amendements/<lég>.contenu.json` et pose `article` sur chaque
amendement. L'étape de téléchargement était écrite pour le premier lecteur et
placée juste avant lui — donc APRÈS le second.

Mesuré sur le run 35767700159 (22/09/2026) : index pivot construit à 19h54 et
20h03, artifact téléchargé à 20h14, zéro contenu publié, zéro `article` posé sur
les 14 520 amendements de `philippe-brun`, et aucune ligne de journal pour le
dire. Ce test verrouille l'ordre, parce qu'une instruction sans test se périme.
"""
from __future__ import annotations

from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

#: Le nom exact de l'étape de téléchargement, tel que le YAML l'écrit.
TELECHARGEMENT = "- name: Download artifact amendements AN (optionnel)"

#: Les étapes de `merge-and-pivot` qui lisent ce cache, dans l'ordre du job.
LECTEURS = (
    "- name: Normalisation pivot + enrichissement ParlTrack",
    "- name: Normalisation pivot roster-driven",
    "- name: Quality gate — résumé et contrôle qualité",
)


def _lignes() -> list[str]:
    return WORKFLOW.read_text(encoding="utf-8").splitlines()


def _rang_dans_merge_and_pivot(fragment: str) -> int:
    """Le numéro de ligne du fragment DANS le job `merge-and-pivot`.

    Le nom de l'étape de téléchargement est le même dans `extract-an` et
    `extract-roster-groupes` : chercher dans tout le fichier prendrait le
    premier, qui n'est pas dans le bon job.
    """
    lignes = _lignes()
    debut = next(i for i, ligne in enumerate(lignes) if ligne.startswith("  merge-and-pivot:"))
    for i in range(debut, len(lignes)):
        if fragment in lignes[i]:
            return i
    raise AssertionError(f"« {fragment} » n'est plus une étape de merge-and-pivot")


@pytest.mark.parametrize("lecteur", LECTEURS)
def test_le_telechargement_precede_chaque_lecteur_du_cache(lecteur: str):
    assert _rang_dans_merge_and_pivot(TELECHARGEMENT) < _rang_dans_merge_and_pivot(lecteur), (
        f"« {lecteur} » lit .cache/amendements_an avant que l'artifact n'arrive : "
        "le contenu des amendements (#1092) ne serait pas publié, et le quality gate "
        "lirait des index « jamais construits ».")


def test_le_telechargement_reste_une_degradation_gracieuse():
    """Son absence ne doit pas coûter le commit d'un run dont la donnée est bonne."""
    lignes = _lignes()
    rang = _rang_dans_merge_and_pivot(TELECHARGEMENT)

    assert any("continue-on-error: true" in ligne for ligne in lignes[rang:rang + 6])


# ---------------------------------------------------------------------------
# Les deux chemins d'appel — la CI ne passe pas par le script
# ---------------------------------------------------------------------------

SRC = RACINE / "src"


def test_les_deux_chemins_dappel_publient_le_contenu():
    """`build_amendements_index_pivot.py` est le script en ligne de commande ;
    `generate_all_profiles._rafraichir_index_amendements` est ce que la CI
    appelle — sa propre docstring le dit déjà pour le report de #696.

    `publier_contenus` n'était branchée que sur le premier : deux runs ont donc
    publié zéro `<lég>.contenu.json` et posé zéro `article`, alors que
    `extract-amendements-an` construisait bien le contenu (125 057 amendements
    pour la XVIIe, 167 420 pour la XIVe, run 35792678909 du 23/09/2026)."""
    for module in ("build_amendements_index_pivot.py", "generate_all_profiles.py"):
        source = (SRC / module).read_text(encoding="utf-8")
        assert "publier_contenus(" in source, (
            f"{module} ne publie pas le contenu des amendements (#1029 voie 2)")
        assert "articles=articles" in source, (
            f"{module} ne pose pas l'article visé sur l'index")


def test_la_ci_publie_le_contenu_avant_de_rafraichir_l_index():
    """L'ordre dans la fonction compte : `articles` est un argument de
    `rafraichir`, donc la publication le précède."""
    source = (SRC / "generate_all_profiles.py").read_text(encoding="utf-8")

    assert source.index("articles = publier_contenus(") < source.index("articles=articles")
