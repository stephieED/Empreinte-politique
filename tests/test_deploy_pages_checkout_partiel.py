"""Le déploiement du site ne récupère que ce que le build lit.

`deploy-pages.yml` récupère trois chemins du dépôt (`sparse-checkout`,
`filter: blob:none`) au lieu des 9,5 Go entiers : mesuré le 28/10/2026, le
build (`npm run build`, tracé par strace) n'ouvre rien d'autre hors de
`web/UI_finale/`. → `docs/decisions/deploy-pages-checkout-partiel.md`

Le jour où un script de build lit un autre chemin du dépôt, le build échoue
en CI sur un fichier absent, et seulement là : ce test le dit avant.

CE QU'IL NE VOIT PAS : un chemin construit autrement que par
`path.join(repoRoot, '<littéral>', …)` dans `web/UI_finale/scripts/`. Le
second test refuse les autres façons connues de remonter à la racine.
"""
from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
WORKFLOW = RACINE / ".github" / "workflows" / "deploy-pages.yml"
SCRIPTS = RACINE / "web" / "UI_finale" / "scripts"
SOURCES_UI = RACINE / "web" / "UI_finale" / "src"


def _motifs() -> list[str]:
    texte = WORKFLOW.read_text(encoding="utf-8")
    bloc = re.search(r"sparse-checkout: \|\n((?:[ ]{12}\S.*\n)+)", texte)
    assert bloc, "deploy-pages.yml ne déclare plus de sparse-checkout"
    return [ligne.strip() for ligne in bloc.group(1).splitlines()]


def _couvert(chemin: str, motifs: list[str]) -> bool:
    """`chemin` est relatif à la racine, sans barre initiale."""
    absolu = "/" + chemin
    for motif in motifs:
        if motif.startswith("!"):
            continue
        if motif.endswith("/") and (absolu + "/").startswith(motif):
            return True
        if absolu == motif:
            return True
    return False


def test_le_checkout_est_partiel_et_filtre():
    texte = WORKFLOW.read_text(encoding="utf-8")
    assert "filter: blob:none" in texte
    assert "sparse-checkout-cone-mode: false" in texte
    motifs = _motifs()
    for attendu in ("/pivot_data/", "/raw_data/candidats.json", "/web/UI_finale/"):
        assert attendu in motifs


def test_chaque_chemin_lu_par_le_build_est_recupere():
    motifs = _motifs()
    lus = set()
    for script in SCRIPTS.glob("*.mjs"):
        for m in re.finditer(r"join\(\s*repoRoot((?:\s*,\s*'[^']+')+)", script.read_text(encoding="utf-8")):
            parties = re.findall(r"'([^']+)'", m.group(1))
            lus.add(("/".join(parties), script.name))
    assert any(c.startswith("pivot_data") for c, _ in lus), "plus aucun chemin relevé : le motif du test est périmé"
    manquants = sorted(f"{c} ({s})" for c, s in lus if not _couvert(c, motifs))
    assert not manquants, (
        "lu par le build mais non récupéré par deploy-pages.yml — ajouter le chemin au "
        f"sparse-checkout : {manquants}"
    )


def test_aucune_autre_remontee_vers_la_racine():
    """`repoRoot` n'est défini qu'une fois ; une autre remontée (`'..', '..'`
    ou un import `../../../`) échapperait au test précédent."""
    remontees = []
    for fichier in [*SCRIPTS.glob("*.mjs"), *SOURCES_UI.rglob("*.js"), *SOURCES_UI.rglob("*.jsx")]:
        texte = fichier.read_text(encoding="utf-8")
        for m in re.finditer(r"'\.\.',\s*'\.\.'|['\"`]\.\./\.\./\.\./", texte):
            ligne = texte[: m.start()].count("\n") + 1
            remontees.append(f"{fichier.relative_to(RACINE)}:{ligne}")
    assert remontees == ["web/UI_finale/scripts/sync-data.mjs:22"], remontees
