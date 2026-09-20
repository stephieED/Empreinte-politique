"""Chaque adresse publiée répond 200, parce qu'elle est un fichier réel (#969).

MESURÉ EN PRODUCTION LE 17/09/2026 : `/` répondait 200 ; `/sources`, `/faq`,
`/candidats/jean-luc-melenchon`, `/groupes`… 404, servies par le repli
`404.html` de #756. Le lecteur voyait la page, un moteur de recherche une
erreur.

`web/UI_finale/scripts/pages-par-adresse.mjs` écrit au build une copie de
`index.html` par adresse publiée, lue dans le manifeste. Ces tests tiennent ce
que le script ne peut pas vérifier seul : que sa liste de pages fixes suit les
routes de `App.jsx`, et qu'il reste branché au build.

CE QU'ILS NE COUVRENT PAS : la CI des tests n'installe pas Node, rien n'est
construit ici. Le build complet a été lancé le 17/09/2026 et `dist/` servi par
un serveur imitant Pages : 57 pages et 33 redirections en 200, une fiche
masquée et un identifiant inconnu en 404.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
SCRIPT = UI / "scripts" / "pages-par-adresse.mjs"
APP = UI / "src" / "App.jsx"


@pytest.fixture(scope="module")
def script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _liste_js(source: str, nom: str) -> set[str]:
    bloc = re.search(rf"export const {nom} = \[(.*?)\];", source, re.S)
    assert bloc, f"`{nom}` introuvable dans pages-par-adresse.mjs"
    return set(re.findall(r"'([^']+)'", bloc.group(1)))


def _cles_js(source: str, nom: str) -> dict[str, str]:
    bloc = re.search(rf"export const {nom} = \{{(.*?)\}};", source, re.S)
    assert bloc, f"`{nom}` introuvable dans pages-par-adresse.mjs"
    return dict(re.findall(r"^\s*([\w-]+):\s*[`']([^`']+)[`'],", bloc.group(1), re.M))


def _routes_app() -> tuple[set[str], set[str]]:
    """Routes sans paramètre de `App.jsx` : (pages, redirections)."""
    pages, redirections = set(), set()
    for ligne in APP.read_text(encoding="utf-8").splitlines():
        m = re.search(r'<Route path="/?([^"]+)" element=\{<(\w+)', ligne)
        if not m or ":" in m.group(1):
            continue
        chemin, composant = m.groups()
        (redirections if composant in {"Navigate", "RedirectionCouverture"} else pages).add(chemin)
    return pages, redirections


def test_le_build_ecrit_les_pages_apres_le_repli():
    build = json.loads((UI / "package.json").read_text(encoding="utf-8"))["scripts"]["build"]
    assert "pages-par-adresse" in build, f"le build n'écrit plus les pages par adresse : « {build} »"
    assert build.index("vite build") < build.index("pages-par-adresse"), (
        "les pages copient `dist/index.html` : elles doivent venir après `vite build`"
    )


def test_chaque_page_fixe_de_l_application_a_son_fichier(script):
    pages, _ = _routes_app()
    assert pages, "aucune route lue dans App.jsx — l'analyse du fichier ne tient plus"
    assert pages - {"/"} == _liste_js(script, "PAGES_FIXES"), (
        "les pages fixes de pages-par-adresse.mjs ne suivent plus les routes de App.jsx : "
        "une page ajoutée sans fichier répond 404 aux moteurs de recherche"
    )


def test_chaque_redirection_de_l_application_a_son_fichier(script):
    _, redirections = _routes_app()
    fixes = _cles_js(script, "REDIRECTIONS_FIXES")
    assert redirections == set(fixes), (
        "les redirections de pages-par-adresse.mjs ne suivent plus celles de App.jsx"
    )
    app = APP.read_text(encoding="utf-8")
    assert "pathname: '/sources'" in app and fixes["couverture"] == "sources"


def test_les_redirections_partagent_les_identifiants_par_defaut_de_l_application(script):
    """Une seule source : l'application et la balise canonical ne divergent pas."""
    assert "../src/data/adressesParDefaut.js" in script
    index = (UI / "src" / "data" / "index.js").read_text(encoding="utf-8")
    assert "from './adressesParDefaut.js'" in index
    assert not re.search(r"export const DEFAULT_\w+_ID\s*=", index), (
        "un identifiant par défaut est redéfini dans data/index.js, hors de adressesParDefaut.js"
    )


def test_les_fiches_viennent_du_manifeste_jamais_d_une_liste_en_dur(script):
    assert "manifest.json" in script
    for population in ("manifeste.candidates", "manifeste.lignees", "manifeste.gouvernements"):
        assert population in script, f"`{population}` n'est plus lu : ses fiches répondraient 404"


def test_un_fichier_x_html_jamais_un_dossier_x_index_html(script):
    """Pages répond 301 vers `/x/` pour un dossier : une redirection par fiche."""
    assert "`${chemin}.html`" in script
    assert not re.search(r"`\$\{\w+\}/index\.html`", script)


def test_le_script_echoue_plutot_que_d_omettre(script):
    assert "process.exit(1)" in script
    assert "n'est pas une page publiée" in script


def test_la_page_est_declaree_en_francais():
    assert '<html lang="fr">' in (UI / "index.html").read_text(encoding="utf-8")
