"""Les actions d'artifact du workflow parlent toutes la même version.

Le run `34160985529` a émis un avertissement de dépréciation Node 20 sur
`actions/download-artifact@v4` : deux blocs neufs — le seul `upload` et le seul
`download` ajoutés par #757 — étaient restés en `v4` quand les vingt autres
étaient en `v6`/`v7`. Rien ne l'a vu, ni la suite ni la relecture, parce qu'une
version d'action est le genre de détail qu'on recopie du bloc d'à côté sans le
regarder — et le bloc d'à côté, ici, était la documentation d'`upload-artifact`.

**Ce test ne fige aucun numéro.** Il vérifie l'**homogénéité** : le jour où le
dépôt monte de version, il monte partout, et un bloc oublié rougit. Figer `v6`
et `v7` obligerait à modifier ce test à chaque montée, c'est-à-dire à faire du
garde-fou une formalité — et une formalité, on la met à jour sans la lire.
"""

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOWS = RACINE / ".github" / "workflows"

_ACTION = re.compile(r"actions/(upload|download)-artifact@(v\d+)")


def _versions(chemin: Path) -> dict[str, set[str]]:
    trouvees: dict[str, set[str]] = {"upload": set(), "download": set()}
    for sens, version in _ACTION.findall(chemin.read_text(encoding="utf-8")):
        trouvees[sens].add(version)
    return trouvees


@pytest.mark.parametrize("nom", sorted(p.name for p in WORKFLOWS.glob("*.yml")))
def test_un_workflow_nutilise_quune_version_par_sens(nom):
    versions = _versions(WORKFLOWS / nom)
    for sens, vues in versions.items():
        assert len(vues) <= 1, (
            f"{nom} mélange {sorted(vues)} pour `actions/{sens}-artifact` — "
            "un bloc a été recopié sans sa version, et GitHub le signalera en "
            "dépréciation avant que quiconque ne le remarque."
        )


def test_le_workflow_de_generation_les_utilise_bien():
    """Garde-fou du garde-fou : le test ci-dessus passerait sur un fichier qui
    n'en contient aucune."""
    versions = _versions(WORKFLOWS / "generate-data.yml")
    assert versions["upload"] and versions["download"]
