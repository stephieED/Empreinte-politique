"""Le bandeau et le pied du site sur les pages statiques (#1029).

Un instantané est servi tel quel par GitHub Pages : l'application React ne le
route pas, donc `EnTeteSite.jsx`, `NavigationSite.jsx` et `PiedDeSite.jsx` n'y
sont pas rendus. `web/UI_finale/scripts/chrome-instantane.mjs` en RECOPIE le
markup, et une copie dérive — une page ajoutée à la barre du site, un compte
qui change, une adresse de contact qui bouge.

Ces gardes tiennent la copie sur ce qui se voit : les entrées de la barre, les
liens du pied, l'adresse, les deux comptes et la baseline. Le style n'est pas
tenu ici : une couleur qui dérive se voit à l'écran, une entrée de menu absente
ne se voit jamais — on est sur la page, pas sur le site.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
CHROME = UI / "scripts" / "chrome-instantane.mjs"
COMPOSANTS = UI / "src" / "components"


def source(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def paires(texte: str) -> list[tuple[str, str]]:
    """Les couples (libellé, adresse) déclarés en objets `{ libelle, vers }`."""
    return re.findall(r"libelle: '([^']+)', vers: '([^']+)'", texte)


def test_le_module_de_chrome_existe() -> None:
    assert CHROME.is_file(), "le module qui porte le bandeau des pages statiques manque"


def test_la_barre_des_pages_dit_la_meme_chose_que_l_application() -> None:
    """Une page ajoutée à la barre du site doit atteindre les instantanés."""
    application = paires(source(COMPOSANTS / "NavigationSite.jsx"))
    statique = paires(source(CHROME))
    assert application, "les pages de NavigationSite.jsx ne se lisent plus"
    assert statique[: len(application)] == application, (
        "la barre des pages statiques a dérivé de NavigationSite.jsx : "
        f"{application} contre {statique[: len(application)]}"
    )


def test_le_pied_porte_les_memes_liens_que_le_composant() -> None:
    pied = source(COMPOSANTS / "PiedDeSite.jsx")
    bloc = pied[pied.index('aria-label="Pages du site"') : pied.index("Nous joindre")]
    attendus = re.findall(r'<Link to="([^"]+)">([^<]+)</Link>', bloc)
    assert attendus, "la colonne « Le site » ne se lit plus dans PiedDeSite.jsx"
    barre = paires(source(COMPOSANTS / "NavigationSite.jsx"))
    statique = paires(source(CHROME))[len(barre) :]
    assert [(vers, libelle) for libelle, vers in statique] == attendus, (
        f"la colonne « Le site » a dérivé de PiedDeSite.jsx : {attendus} contre {statique}"
    )


def test_l_adresse_et_les_deux_comptes_sont_ceux_du_site() -> None:
    pied = source(COMPOSANTS / "PiedDeSite.jsx")
    chrome = source(CHROME)
    for nom in ("CONTACT", "LINKEDIN", "X_COMPTE"):
        motif = rf"export const {nom} = '([^']+)';"
        attendu = re.search(motif, pied)
        assert attendu, f"{nom} ne se lit plus dans PiedDeSite.jsx"
        trouve = re.search(motif, chrome)
        assert trouve and trouve.group(1) == attendu.group(1), (
            f"{nom} a dérivé : le site dit {attendu.group(1)}"
        )


def test_la_baseline_est_ecrite_une_seule_fois() -> None:
    """Quatre mentions, une promesse : deux copies divergentes seraient pires que pas de pied."""
    motif = r"export const BASELINE = \[([^\]]+)\];"
    attendu = re.search(motif, source(COMPOSANTS / "Baseline.jsx"))
    trouve = re.search(motif, source(CHROME))
    assert attendu and trouve, "la baseline ne se lit plus"
    assert trouve.group(1) == attendu.group(1), "la baseline du pied statique a dérivé"


def test_l_avis_en_construction_est_repris_mot_pour_mot() -> None:
    """Le bandeau d'état est sur TOUTES les pages du site : un instantané en est une."""
    phrase = "Ce site est publié pendant son développement."
    banniere = re.sub(r"\s+", " ", source(COMPOSANTS / "ConstructionBanner.jsx"))
    assert phrase in banniere, "la phrase du bandeau d'état a changé"
    assert phrase in re.sub(r"\s+", " ", source(CHROME)), "le bandeau d'état manque aux pages statiques"
