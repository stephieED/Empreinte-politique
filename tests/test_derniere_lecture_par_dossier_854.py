"""Un texte renommé entre deux lectures reste UN texte (#854).

La dernière lecture d'un texte était reconnue à son intitulé (#711). Mesuré le
08/10/2026 sur `main` 98327b0c0, sur les 931 votes portant sur un texte entier :
38 textes ont changé de titre entre deux lectures ou ont été repris sous la
législature suivante, et 3 ne diffèrent que par une graphie. Chacun gardait
deux « dernières lectures » : 701 textes au lieu de 661, et 110 positions de
trop sur 15 des 35 fiches de candidats (12 sur celle d'Olivier Faure).

Arbitré par la propriétaire (piste C) : deux lectures sont celles d'un même
texte si elles partagent l'intitulé, le dossier de l'Assemblée quand il est
connu (669 des 931 votes), ou l'intitulé assoupli dans une même législature.

Les scrutins de `tests/fixtures/derniere_lecture_854/` sont COPIÉS du corpus.

CE QUE CES TESTS NE COUVRENT PAS : aucune fiche n'est rendue ; le compte sur le
corpus entier a été mesuré hors dépôt. Pour un vote sans dossier connu, un
texte renommé reste compté deux fois, et rien ici ne le détecte.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
MODULE = RACINE / "web" / "UI_finale" / "src" / "utils" / "lecture.js"
FIXTURE = json.loads((RACINE / "tests" / "fixtures" / "derniere_lecture_854" / "scrutins.json").read_text(encoding="utf-8"))


def _retenus(avec_dossiers: bool) -> list[str]:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(JSON.stringify(m.selectDerniereLectureVotes(%s, %s).map((s) => s.id)));"
        % (MODULE.as_uri(), json.dumps(FIXTURE["scrutins"]), json.dumps(FIXTURE["dossiers"] if avec_dossiers else None))
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_un_texte_renomme_n_a_qu_une_derniere_lecture() -> None:
    """« relative à la sécurité globale » devient « pour une sécurité globale
    préservant les libertés » ; « haine sur internet », « contenus haineux »."""
    retenus = _retenus(avec_dossiers=True)
    assert "an:15:3658" in retenus and "an:15:3254" not in retenus
    assert "an:15:2742" in retenus and "an:15:2039" not in retenus


def test_un_texte_repris_sous_la_legislature_suivante_reste_un_texte() -> None:
    """Formation de sage-femme : première lecture en 2021 (XVe), deuxième en
    2023 (XVIe). Le dossier de l'Assemblée est le même."""
    retenus = _retenus(avec_dossiers=True)
    assert "an:16:839" in retenus and "an:15:4182" not in retenus


def test_une_graphie_ne_dedouble_plus_meme_sans_dossier() -> None:
    """« relatif » / « relative » (jeux Olympiques de 2030), et « spoliation » /
    « spoliations » (biens culturels), dont le second vote n'a pas de dossier."""
    assert "an:16:2282" not in FIXTURE["dossiers"]["scrutins"]
    for avec in (True, False):
        retenus = _retenus(avec_dossiers=avec)
        assert "an:17:5296" in retenus and "an:17:4963" not in retenus
        assert "an:16:2282" in retenus and "an:16:2118" not in retenus


def test_sans_la_table_des_dossiers_l_intitule_decide() -> None:
    """La table peut manquer : un texte renommé reste alors compté deux fois —
    un manque, pas une position attribuée à tort."""
    retenus = _retenus(avec_dossiers=False)
    assert {"an:15:3254", "an:15:3658", "an:15:4182", "an:16:839"} <= set(retenus)
    assert len(retenus) == 8
    assert len(_retenus(avec_dossiers=True)) == 5


def test_les_deux_appelants_passent_les_dossiers() -> None:
    ui = RACINE / "web" / "UI_finale"
    assert "selectDerniereLectureVotes(scrutinsCorpus, scrutinsDossiers)" in (ui / "src" / "utils" / "profilCandidat.js").read_text(encoding="utf-8")
    assert "selectDerniereLectureVotes(scrutinsListe, dossiersDesScrutins)" in (ui / "scripts" / "sync-data.mjs").read_text(encoding="utf-8")


def test_la_methodologie_dit_le_dossier() -> None:
    regles = MODULE.read_text(encoding="utf-8")
    assert "par son dossier à l’Assemblée quand il est connu, sinon par son intitulé" in regles
