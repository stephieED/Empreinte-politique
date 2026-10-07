"""Les mandats absents de la source se disent dans « Ce qu'on n'a pas pu lire » (#859).

Trois mandats de Xavier Bertrand, exercés entre 2002 et 2007, manquent au
fichier de l'Assemblée et sont cités à la main dans
`mandats_absents_de_la_source`. Arbitré par la propriétaire le 07/10/2026 : une
ligne de la section 6, sur le modèle des mandats antérieurs (#860), avec une
phrase à elle — « exercés avant le 19 juin 2002 » serait fausse ici.

Le test exécute le module sur les lignes COPIÉES de la table committée, et non
sur une entrée inventée : une fixture qui décrit les données comme le code les
imagine ne révèle pas qu'elles ont bougé (#726).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
MODULE = UI / "utils" / "mandatsAbsents.js"
REGLES = UI / "utils" / "profilCandidat.js"
TABLE = RACINE / "config" / "mandats_anterieurs.json"


def _limite(absents) -> dict | None:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(JSON.stringify(m.limiteMandatsAbsents(%s)));"
        % (MODULE.as_uri(), json.dumps(absents))
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def _lignes_de_la_table(slug: str) -> list[dict]:
    return json.loads(TABLE.read_text(encoding="utf-8"))["absents_de_la_source"][slug]


def test_la_ligne_dit_les_trois_mandats_de_la_table() -> None:
    lignes = _lignes_de_la_table("xavier-bertrand")
    assert len(lignes) == 3, "la table a changé : relire ce que ce test affirme"
    limite = _limite(lignes)
    assert limite["cle"] == "mandats-absents-de-la-source"
    assert limite["titre"] == "Mandats absents de la source"
    assert limite["texte"] == (
        "3 mandats exercés entre le 19 juin 2002 et le 26 mars 2007 "
        "— 1 à l’Assemblée, 2 au gouvernement — sont cités depuis leur source primaire. "
        "Aucune activité n’y est collectée."
    )


def test_la_phrase_des_mandats_anterieurs_n_y_est_pas() -> None:
    """« avant le 19 juin 2002 » serait faux : ces mandats suivent cette date."""
    assert "avant le" not in _limite(_lignes_de_la_table("xavier-bertrand"))["texte"]


@pytest.mark.parametrize("absents", [None, []])
def test_une_fiche_non_relue_ne_dit_rien(absents) -> None:
    """`null` + `non_relu` parle de notre travail, pas de la personne (#860)."""
    assert _limite(absents) is None


def test_un_seul_mandat_s_accorde_au_singulier() -> None:
    limite = _limite(_lignes_de_la_table("xavier-bertrand")[:1])
    assert limite["texte"].startswith("1 mandat exercé entre le 19 juin 2002 et le 30 avril 2004 est cité depuis sa source")


def test_sans_toutes_les_dates_la_phrase_n_en_donne_aucune() -> None:
    lignes = [dict(l) for l in _lignes_de_la_table("xavier-bertrand")]
    lignes[1]["fin"] = None
    assert "entre le" not in _limite(lignes)["texte"]


def test_la_fiche_lit_le_champ_et_range_la_ligne() -> None:
    code = re.sub(r"/\*.*?\*/", "", REGLES.read_text(encoding="utf-8"), flags=re.DOTALL)
    assert "limiteMandatsAbsents(profil?.mandats_absents_de_la_source)" in code, (
        "la section 6 ne lit plus le champ : les mandats cités n'apparaîtraient nulle part"
    )
    rangs = re.search(r"RANG_DES_AUTRES_LIMITES\s*=\s*\[(.*?)\]", code, re.DOTALL)
    assert rangs and "CLE_MANDATS_ABSENTS" in rangs.group(1), (
        "la ligne a perdu son rang : elle se mêlerait aux signalements de collecte"
    )
