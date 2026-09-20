"""Un lien profond doit démarrer l'application, pas la page d'erreur de GitHub.

MESURÉ EN PRODUCTION LE 07/09/2026, sur `https://empreinte-politique.fr` :

    /                          200
    /candidats                 404
    /candidats/gabriel-attal   404
    /404.html                  404

L'application route côté client (`BrowserRouter`) ; GitHub Pages sert des
FICHIERS et répond 404 à tout chemin qui n'en est pas un. Le site n'était donc
navigable qu'en partant de la racine : un favori, un lien partagé, une entrée
d'historique, ou simplement **F5 sur une fiche candidat** tombaient sur la page
d'erreur de GitHub.

Pages sert `404.html` pour tout chemin inconnu. Lui donner le contenu de
`index.html` fait démarrer l'application, qui lit l'URL et affiche la bonne
page. C'est le seul mécanisme disponible — Pages n'a aucune règle de
réécriture.

CE QUI RESTAIT ASSUMÉ : le statut HTTP demeurait 404 sur un lien profond. Le
lecteur voyait la bonne page, un robot une erreur. Depuis #969, chaque adresse
publiée a son propre fichier et répond 200 (`test_pages_par_adresse_969.py`) ;
le repli ne sert plus qu'aux adresses non publiées.

CE QUE CES GARDE-FOUS NE COUVRENT PAS : ils ne construisent rien et
n'exécutent aucun script (la CI des tests n'installe pas Node). Le repli a été
éprouvé hors dépôt, contre un serveur reproduisant Pages — fichier s'il
existe, sinon `404.html` avec le statut 404 : le lien profond y rend bien la
fiche de Gabriel Attal.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
REPLI = UI / "scripts" / "spa-fallback.mjs"
WORKFLOW = RACINE / ".github" / "workflows" / "deploy-pages.yml"


@pytest.fixture(scope="module")
def paquet() -> dict:
    return json.loads((UI / "package.json").read_text(encoding="utf-8"))


def test_le_repli_est_produit_par_le_build_pas_par_le_workflow(paquet):
    """Un `dist/` construit à la main et publié autrement doit le porter aussi.

    Mettre la copie dans `deploy-pages.yml` la lierait à un seul chemin de
    publication ; le workflow ne fait que téléverser `dist/`, c'est au build de
    le rendre complet.
    """
    assert REPLI.exists(), "`web/UI_finale/scripts/spa-fallback.mjs` a disparu"
    build = paquet["scripts"]["build"]
    assert "spa-fallback" in build, (
        f"le script `build` ne produit plus le repli de routage — il vaut « {build} »"
    )


def test_le_repli_copie_index_html_vers_404_html():
    """Le nom du fichier n'est pas indifférent : Pages ne sert que `404.html`."""
    source = REPLI.read_text(encoding="utf-8")
    assert "'404.html'" in source or '"404.html"' in source, (
        "le repli n'écrit plus `404.html`, le seul nom que GitHub Pages sert "
        "pour un chemin inconnu"
    )
    assert "index.html" in source, "le repli ne copie plus le point d'entrée de l'application"


def test_le_repli_echoue_bruyamment_si_le_build_n_a_pas_tourne():
    """Un repli silencieusement absent redonne le défaut sans rien dire."""
    source = REPLI.read_text(encoding="utf-8")
    assert re.search(r"process\.exit\(1\)", source), (
        "le repli doit échouer quand `dist/index.html` manque, jamais passer en silence"
    )


def test_le_workflow_televerse_bien_le_dossier_qui_porte_le_repli():
    """Le repli est écrit dans `dist/` : c'est `dist/` qui doit partir."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "upload-pages-artifact" in workflow
    assert re.search(r"path:\s*web/UI_finale/dist", workflow), (
        "l'artifact publié n'est plus `web/UI_finale/dist` : le repli n'y serait pas"
    )


def test_le_routage_est_bien_celui_qui_exige_un_repli():
    """`BrowserRouter` est la raison d'être du repli.

    Ce test n'impose pas le routeur — il rend visible le lien : si quelqu'un
    passe un jour à `HashRouter`, le repli devient inutile et ce test le dit,
    au lieu de laisser un fichier orphelin dans le build.
    """
    main = (UI / "src" / "main.jsx").read_text(encoding="utf-8")
    assert "BrowserRouter" in main, (
        "le routeur a changé : si les URL passent au fragment (`/#/…`), le repli "
        "`404.html` n'a plus d'objet et doit être retiré avec cette explication"
    )
