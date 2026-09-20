"""Garde-fou #569 : une référence git absente ne se diagnostique pas comme un
chemin absent.

`audit_diff_profils` compare l'état publié à une référence git. Après un
bornage d'historique (#551), la référence citée dans une doc ou une issue peut
avoir **disparu** — et c'est précisément le moment où l'on vérifie que ce
contrôle fonctionne encore.

Il refusait déjà correctement — exit 1, jamais « aucune perte » — mais son
message conseillait `--ref-dir`, c'est-à-dire une erreur d'invocation. On
aurait cherché un problème de chemin là où le commit entier était absent.

Vérifié le 29/08/2026 en déroulant la dernière case de #569.
"""

import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "src" / "audit_diff_profils.py"
SHA_ABSENT = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"


def _lancer(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=RACINE,
    )


def test_reference_absente_le_dit_et_ne_conseille_pas_ref_dir():
    """Le cas d'après-bornage. Conseiller `--ref-dir` ici envoie chercher un
    problème de chemin alors que le commit n'existe pas."""
    r = _lancer("--ref", SHA_ABSENT)
    sortie = r.stdout + r.stderr
    assert r.returncode != 0, "une référence absente doit faire échouer le contrôle"
    assert "Référence git introuvable" in sortie
    assert "le commit lui-même est absent" in sortie
    assert "--ref-dir" not in sortie, (
        "conseiller `--ref-dir` sur une référence absente envoie chercher un "
        "problème de chemin là où le commit entier a disparu"
    )
    assert "bornage" in sortie.lower(), (
        "la cause la plus probable après un bornage doit être nommée, sans "
        "être présentée comme le seul diagnostic"
    )


def test_chemin_absent_conseille_toujours_ref_dir():
    """L'autre cause, inchangée : la référence existe, le chemin n'y est pas.
    C'est bien une erreur d'invocation, et le conseil reste juste."""
    r = _lancer("--ref", "HEAD", "--ref-dir", "chemin/qui/n/existe/pas")
    sortie = r.stdout + r.stderr
    assert r.returncode != 0
    assert "Chemin introuvable" in sortie
    assert "--ref-dir" in sortie
    assert "Référence git introuvable" not in sortie, (
        "les deux causes ne doivent pas rendre le même message"
    )


def test_une_reference_absente_ne_conclut_jamais_aucune_perte():
    """Le scénario redouté de #569 : une coupure d'historique rendrait ce
    garde-fou silencieusement inutile s'il concluait à l'absence de perte."""
    sortie = (lambda r: r.stdout + r.stderr)(_lancer("--ref", SHA_ABSENT))
    for mensonge in ("aucune perte", "Aucune perte", "0 perte"):
        assert mensonge not in sortie
