"""`scripts/sync_depots.sh` pousse le commit courant, jamais la branche `main` locale.

Le script tourne depuis un worktree détaché : la branche `main` locale y est
celle du checkout partagé, loin derrière `origin/main`. Le 08/10/2026, `--tout`
a poussé cette branche au lieu du commit de récupération des données.
"""

from pathlib import Path

SYNC = Path(__file__).resolve().parent.parent / "scripts" / "sync_depots.sh"


def _lignes_de_code() -> list[str]:
    return [
        ligne
        for ligne in SYNC.read_text(encoding="utf-8").splitlines()
        if not ligne.lstrip().startswith("#")
    ]


def test_aucun_push_de_la_branche_main_locale():
    fautives = [ligne for ligne in _lignes_de_code() if "git push origin main" in ligne]
    assert not fautives, fautives


def test_tout_pousse_le_commit_courant_avant_de_publier():
    (tout,) = [ligne for ligne in _lignes_de_code() if ligne.lstrip().startswith("--tout)")]
    etapes = [etape.strip() for etape in tout.split(")", 1)[1].split(";") if etape.strip()]
    assert etapes[:3] == ["verifier_remotes", "recuperer_donnees", "pousser_vers_le_prive"], etapes
    assert etapes[3].startswith("publier_code"), etapes
