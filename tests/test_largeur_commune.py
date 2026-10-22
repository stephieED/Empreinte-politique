"""Une seule largeur pour toutes les pages du site (arbitré le 21/10/2026).

Avant ce lot, chaque page avait reçu sa largeur le jour où elle avait été
faite : l'accueil 1 600 px collé à gauche, les pages du site 900 ou 1 180 px,
les fiches 1 100 px, à gauche ou centrées selon la fiche. Sur un grand écran,
le lecteur voyait six mises en page.

La largeur vit désormais dans un jeton de `src/index.css` : `--colonne`
(la page) ; `--mesure` (80 caractères de texte courant) est retiré le
22/10/2026 : le texte des pages de texte occupe toute sa carte. Ce que ces garde-fous
protègent, pour les pages d'aujourd'hui et celles qui viendront :

1. **Aucune feuille de style ne fixe une largeur de page à elle** — ni
   `max-width`, ni `width` d'au moins 1 000 px. Une nouvelle page qui en
   écrirait une fait rougir la suite : elle doit lire `--colonne`.
2. **Les trois cadres lisent `--colonne`** — l'accueil, les pages du site
   (`static-main`) et les fiches (`explorer-corps`), avec la barre du haut et
   le pied.
3. **Toute page routée passe par l'un de ces cadres** : une page ajoutée à
   `App.jsx` sans eux n'hériterait pas de la largeur.
4. **Les articles** (`public/rapports/`, hors de l'application) portent la
   même valeur dans leur barre et leur pied, recopiée par
   `scripts/chrome-instantane.mjs`.

CE QU'ILS NE COUVRENT PAS : le rendu. La colonne a été jouée le 21/10/2026 à
1 280, 1 600 et 2 560 px et à 390 px sur l'accueil, les pages du site et les
trois fiches.
"""

from __future__ import annotations

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SRC = UI / "src"

SEUIL_PAGE = 1000  # px : en deçà, c'est un bloc ; au-delà, une largeur de page


def sans_commentaires(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def jeton(nom: str, css: str) -> str:
    trouve = re.findall(rf"{re.escape(nom)}:\s*([^;]+);", css)
    assert len(trouve) == 1, f"{nom} doit être défini une seule fois, trouvé {trouve}"
    return trouve[0].strip()


def regle(css: str, selecteur: str) -> str:
    m = re.search(rf"(?m)^{re.escape(selecteur)}\s*\{{([^}}]*)\}}", sans_commentaires(css))
    assert m, f"règle {selecteur} introuvable"
    return m.group(1)


def test_la_largeur_vit_dans_un_jeton() -> None:
    css = (SRC / "index.css").read_text(encoding="utf-8")
    assert jeton("--colonne", css) == "1600px"


def test_aucune_page_ne_fixe_sa_largeur() -> None:
    fautes = []
    motif = re.compile(r"(?<![-\w])(max-width|width)\s*:\s*(?:min\(\s*)?(\d+)px")
    for fichier in sorted(SRC.rglob("*.css")):
        for n, ligne in enumerate(sans_commentaires(fichier.read_text(encoding="utf-8")).splitlines(), 1):
            if ligne.lstrip().startswith("@media") or "@container" in ligne:
                continue
            for _, valeur in motif.findall(ligne):
                if int(valeur) >= SEUIL_PAGE:
                    fautes.append(f"{fichier.relative_to(SRC)}:{n} {ligne.strip()}")
    assert not fautes, "largeur de page en dur — lire var(--colonne) :\n" + "\n".join(fautes)


def test_les_trois_cadres_lisent_la_colonne() -> None:
    attendus = {
        "components/landing/landing.css": ".landing-main",
        "components/StaticPage.css": ".static-main",
        "components/ExplorerLayout.css": ".explorer-corps",
        "components/PiedDeSite.css": ".pds",
        "components/EnTeteSite.css": ".entete-site",
    }
    for fichier, selecteur in attendus.items():
        corps = regle((SRC / fichier).read_text(encoding="utf-8"), selecteur)
        assert "var(--colonne)" in corps, f"{selecteur} ({fichier}) ne lit plus --colonne"


def test_le_texte_des_pages_de_texte_occupe_sa_carte() -> None:
    """Arbitré le 22/10/2026 : le texte des pages de texte n'est plus borné à 80
    caractères, il prend la largeur de sa carte comme sur l'accueil et les
    fiches. Une borne en `ch` revenue dans ces feuilles ferait réapparaître la
    marge droite que la propriétaire a relevée sur /methodologie."""
    for fichier in ("components/StaticPage.css", "pages/CoveragePage.css"):
        css = sans_commentaires((SRC / fichier).read_text(encoding="utf-8"))
        assert not re.search(r"max-width\s*:\s*[\d.]+ch", css), f"{fichier} borne encore le texte en caractères"
    assert "--mesure" not in sans_commentaires((SRC / "index.css").read_text(encoding="utf-8"))


def test_toute_page_routee_passe_par_un_cadre() -> None:
    app = (SRC / "App.jsx").read_text(encoding="utf-8")
    debut = app.index("<Route element={<ExplorerLayout />}>")
    fin = app.index("</Route>", debut)
    sous_fiches = set(re.findall(r"element=\{<(\w+Page) />\}", app[debut:fin]))
    hors = set(re.findall(r"element=\{<(\w+Page) />\}", app[:debut] + app[fin:]))
    assert sous_fiches, "les fiches ne passent plus par ExplorerLayout"
    for page in sorted(hors):
        source = (SRC / "pages" / f"{page}.jsx").read_text(encoding="utf-8")
        assert re.search(r"<StaticPage\b|className=\"(static|landing)-main\b", source), (
            f"{page} n'utilise aucun cadre commun (StaticPage, static-main, landing-main) : "
            "elle n'hériterait pas de la largeur des autres pages"
        )


def test_les_articles_portent_la_meme_colonne() -> None:
    css = (SRC / "index.css").read_text(encoding="utf-8")
    chrome = (UI / "scripts" / "chrome-instantane.mjs").read_text(encoding="utf-8")
    assert jeton("--colonne", chrome) == jeton("--colonne", css)
    assert chrome.count("var(--colonne)") >= 3, "barre et pied des articles : lire --colonne"
