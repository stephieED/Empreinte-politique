"""Un texte publié sur le site ne porte pas le vocabulaire du dépôt.

La règle vit dans `docs/regles/textes-publies.md` (AGENTS.md §3g) et ne vaut
que pour ce que le lecteur du site voit : la documentation, le code et les
issues gardent leurs termes exacts. Cette garde n'en tient qu'une partie — six
mots sans ambiguïté, dans les fichiers qui portent le plus de texte publié.
« champ », « fusion » ou « collecte » sont aussi des mots courants : aucun test
ne peut les juger, et le fichier de règles le dit.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"

#: Les mots du dépôt qu'aucune phrase adressée au lecteur n'a de raison de porter.
MOTS_DU_DEPOT = ("pivot", "roster", "run", "pipeline", "workflow", "backfill")
_MOT = re.compile(r"\b(" + "|".join(MOTS_DU_DEPOT) + r")s?\b", re.IGNORECASE)

#: Une liste de classes CSS (« hero-pipeline-step hero-pipeline-step--lien »)
#: n'est pas une phrase : ni majuscule, ni accent, ni ponctuation.
_LISTE_DE_CLASSES = re.compile(r"^[a-z0-9_ -]+$")


def fichiers_publies() -> list[Path]:
    return sorted(
        list((UI / "src" / "pages").glob("*.jsx"))
        + list((UI / "src" / "components" / "landing").glob("*.jsx"))
        + [UI / "src" / "data" / "sources.config.js", UI / "src" / "data" / "schemaSources.js"]
        + list((UI / "public" / "rapports").glob("*.html"))
        + [UI / "public" / "rapports.html"]
    )


def texte_visible(chemin: Path) -> str:
    source = chemin.read_text(encoding="utf-8")
    if chemin.suffix == ".html":
        return re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", "", source, flags=re.S))
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    source = re.sub(r"(?m)^\s*//.*$", "", source)
    entre_balises = re.findall(r">([^<>{}]+)<", source)
    chaines = [
        m[1]
        for m in re.findall(r"""(['"`])((?:(?!\1)[^\\\n]|\\.){12,})\1""", source)
        if " " in m[1] and not _LISTE_DE_CLASSES.match(m[1])
    ]
    return " ".join(entre_balises + chaines)


def test_le_releve_couvre_les_pages_et_les_articles() -> None:
    """Témoin : un glob vide ferait passer la garde pour de bonnes raisons apparentes."""
    noms = {f.name for f in fichiers_publies()}
    assert {"MethodologyPage.jsx", "FaqPage.jsx", "rapports.html", "sources.config.js"} <= noms
    assert all(f.is_file() for f in fichiers_publies())
    assert len(texte_visible(UI / "src" / "pages" / "MethodologyPage.jsx").split()) > 1000


@pytest.mark.parametrize("chemin", fichiers_publies(), ids=lambda p: p.name)
def test_aucun_mot_du_depot_dans_un_texte_publie(chemin: Path) -> None:
    trouve = _MOT.search(texte_visible(chemin))
    assert trouve is None, (
        f"{chemin.name} publie « {trouve.group(0)} » : un mot du dépôt, que le lecteur "
        "du site ne connaît pas. Voir docs/regles/textes-publies.md."
    )


def test_la_garde_reconnait_un_mot_du_depot(tmp_path: Path) -> None:
    """Sans ce contrôle, une garde qui ne lit plus rien resterait verte."""
    page = tmp_path / "Page.jsx"
    page.write_text("export default () => <p>Chaque run régénère le pivot.</p>;\n", encoding="utf-8")
    assert _MOT.search(texte_visible(page))
    classes = tmp_path / "Hero.jsx"
    classes.write_text('const c = "hero-pipeline-step hero-pipeline-step--lien";\n', encoding="utf-8")
    assert _MOT.search(texte_visible(classes)) is None


# ── Le cliquet des tics d'écriture (30/10/2026) ─────────────────────────────
#
# Deux relectures extérieures (GPT, Gemini) ont relevé les tournures de modèle
# de langage du site, après qu'un lecteur les a remarquées (règle « Les tics
# d'un modèle de langage… » de docs/regles/textes-publies.md). Deux de ces
# tics se comptent sans lire : le tiret long d'incise et la négation d'abord.
# Leur total sur les textes publiés ne peut que BAISSER. Quand une réécriture
# en retire, abaisser le plafond au nouveau compte, dans le même lot : sinon
# le terrain gagné se reperd sans que rien ne le voie.
#
# Plafonds mesurés le 30/10/2026 sur main, sur les fichiers que lit
# `fichiers_publies()` (les bulles des fiches n'y sont pas).

_TICS = {
    "tiret long d'incise « — »": (re.compile(r"—"), 76),
    "négation d'abord (« n'est pas », « ne veut pas dire »)": (
        re.compile(r"n[’']est pas|ne veut pas dire"),
        31,
    ),
}


@pytest.mark.parametrize("tic", sorted(_TICS))
def test_les_tics_d_ecriture_ne_peuvent_que_baisser(tic: str) -> None:
    motif, plafond = _TICS[tic]
    par_fichier = {f.name: len(motif.findall(texte_visible(f))) for f in fichiers_publies()}
    total = sum(par_fichier.values())
    pires = ", ".join(f"{n} ({c})" for n, c in sorted(par_fichier.items(), key=lambda x: -x[1])[:3] if c)
    assert total <= plafond, (
        f"{tic} : {total} dans les textes publiés, pour un plafond de {plafond}. "
        f"Les plus chargés : {pires}. Réécrire plutôt qu'ajouter "
        "(docs/regles/textes-publies.md, « Les tics d'un modèle de langage »)."
    )
