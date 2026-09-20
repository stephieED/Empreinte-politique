"""Garde-fou #workers-fige-a-1 : `workers` ne doit pas revenir dans le
formulaire `workflow_dispatch`, et aucun site ne doit le lire.

Contexte. L'input existait avec `default: 1` et une description qui disait
elle-même, depuis #467, qu'augmenter la valeur RALENTIT l'extraction — mesuré
9,8 s à 1 contre 13,8 s à 4 (+41 %), la charge étant du parsing JSON sous GIL
sérialisé par les verrous par législature. Un paramètre documenté comme
nuisible reste un piège : dans un formulaire de lancement, « workers » se lit
comme un levier d'optimisation, et la valeur par défaut ne protège que celui
qui n'y touche pas.

Le découpage par job a été envisagé puis écarté : l'input était partagé par
trois charges de natures différentes, et le Sénat — la seule bornée par le
réseau — l'est par la source elle-même, donc y ajouter des workers le rendrait
moins courtois sans le rendre plus rapide.

Ce test porte sur le YAML et non sur l'exécution : ce qui est en jeu n'est pas
qu'un garde-fou se déclenche, c'est qu'un bouton n'existe plus. Une assertion
textuelle est exactement la bonne forme ici.

Le flag `--workers` de `generate_all_profiles.py` reste, lui, disponible en
local : la CLI n'a pas à être amputée parce que la CI n'en veut plus.

Volontairement sans PyYAML (absent de requirements.txt), comme
`test_ci_publication_profils.py` et `test_ci_cache_paths.py`.
"""

import pathlib
import re

WORKFLOW = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows" / "generate-data.yml"


def _contenu() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_aucun_site_ne_lit_l_input_workers():
    """`${{ inputs.workers }}` ne doit apparaître nulle part.

    Les cinq sites qui le lisaient — extract-senat (retiré depuis, #528),
    extract-ue-officiel, le shard roster et les deux invocations de
    merge-and-pivot — sont figés.
    """
    contenu = _contenu()
    assert "inputs.workers" not in contenu, (
        "generate-data.yml relit `inputs.workers` : l'input a été réintroduit ou "
        "un site a été rebranché dessus. Voir "
        "docs/decisions/workers-fige-a-1.md — augmenter cette valeur "
        "ralentit l'extraction (+41 % mesuré)."
    )


def test_l_input_workers_n_est_pas_de_retour_dans_le_formulaire():
    """La clé `workers:` ne doit pas reparaître dans `workflow_dispatch.inputs`.

    Le test délimite le bloc `inputs:` plutôt que de chercher « workers »
    partout : le mot subsiste légitimement dans les commentaires et dans les
    `--workers 1` en dur.
    """
    contenu = _contenu()
    debut = contenu.index("  workflow_dispatch:")
    fin = contenu.index("\njobs:")
    formulaire = contenu[debut:fin]
    assert not re.search(r"^      workers:", formulaire, re.MULTILINE), (
        "l'input `workers` est de retour dans workflow_dispatch. Il a été retiré "
        "délibérément : un paramètre dont la description dit qu'il nuit est un "
        "piège dans un formulaire de lancement. "
        "Voir docs/decisions/workers-fige-a-1.md."
    )


def test_les_quatre_invocations_passent_workers_1_en_dur():
    """Le figeage doit être explicite, pas obtenu en retirant le flag.

    Retirer `--workers` marcherait (le défaut de l'argparse vaut 1), mais
    rendrait le choix invisible à la relecture du workflow — c'est précisément
    ce qui a rendu #467 nécessaire.
    """
    lignes = [
        ligne for ligne in _contenu().splitlines()
        if "--workers 1" in ligne and not ligne.lstrip().startswith("#")
    ]
    assert len(lignes) == 4, (
        f"attendu 4 invocations `--workers 1` en dur, trouvé {len(lignes)} :\n"
        + "\n".join(f"  {l.strip()}" for l in lignes)
        + "\nSites attendus : extract-ue-officiel, le shard roster, et les deux "
        "invocations de merge-and-pivot. Le cinquième site était extract-senat, "
        "retiré par #528 avec le Sénat. Les lignes de commentaire sont exclues "
        "du décompte — deux en mentionnent, dont une antérieure à ce garde-fou."
    )
