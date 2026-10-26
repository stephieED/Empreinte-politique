"""Les instantanés publiés : un dossier, et un index qui se construit depuis lui.

Un instantané est une page STATIQUE de `web/UI_finale/public/rapports/`,
servie telle quelle par GitHub Pages — l'application React ne la route pas.
Son adresse répond donc 200 et ne bouge plus une fois partagée.

L'index `/rapports` était écrit à la main ; il est désormais produit par
`scripts/index-rapports.mjs` en lisant le dossier. Ces gardes tiennent ce
qu'aucune revue ne rattrape : la version committée ne dérive pas du dossier,
et chaque instantané porte de quoi être listé — une date dans son nom, un
titre, une description.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
INDEX = UI / "public" / "rapports.html"
DOSSIER = UI / "public" / "rapports"
GENERATEUR = UI / "scripts" / "index-rapports.mjs"

NOM = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.html$")


def instantanes() -> list[Path]:
    return sorted(DOSSIER.glob("*.html"))


def test_le_dossier_son_index_et_son_generateur_existent() -> None:
    assert GENERATEUR.is_file(), "le générateur de l'index manque"
    assert INDEX.is_file(), "l'index /rapports manque"
    assert DOSSIER.is_dir() and instantanes(), "aucun instantané publié"


@pytest.mark.parametrize("instantane", instantanes(), ids=lambda p: p.name)
def test_un_instantane_porte_sa_date_et_se_presente(instantane: Path) -> None:
    assert NOM.match(instantane.name), "le nom porte la date des DONNÉES, puis le sujet"
    source = instantane.read_text(encoding="utf-8")
    assert re.search(r"<title>.+</title>", source), "titre absent"
    assert 'name="description"' in source, "description absente : l'index la reprend"
    assert 'name="article:type"' in source, "type absent : l'index ne le devine pas"
    assert 'href="https://empreinte-politique.fr/rapports"' in source, "retour à l'index absent"
    for bloc, ouvre in (("style", "/*chrome:style*/"), ("bandeau", "<!--chrome:bandeau-->"), ("pied", "<!--chrome:pied-->")):
        assert ouvre in source, f"le bloc de chrome « {bloc} » manque : la page n'est pas une page du site"
    assert '<footer class="pds">' in source, "pied du site absent"
    assert 'class="entete-site"' in source, "bandeau du site absent"
    assert 'rel="canonical"' in source, "canonical absente : l'adresse de la page ne se déclare pas"


def test_l_index_committe_ne_derive_pas_du_dossier() -> None:
    """Un instantané ajouté sans régénérer l'index ne serait trouvable par personne."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(m.page(m.instantanes()));" % GENERATEUR.as_uri()
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert res.stdout == INDEX.read_text(encoding="utf-8"), (
        "public/rapports.html a dérivé : relancer `node scripts/index-rapports.mjs`"
    )


def test_le_chrome_committe_ne_derive_pas_du_module() -> None:
    """Le bandeau et le pied suivent le site ; seul le CONTENU d'un instantané est gelé."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(JSON.stringify(m.rafraichirLeChrome(undefined, { ecrire: false })));"
        % GENERATEUR.as_uri()
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    derives = json.loads(res.stdout)
    assert derives == [], (
        f"le chrome a dérivé sur {derives} : relancer `node scripts/index-rapports.mjs`"
    )


def test_les_instantanes_entrent_dans_le_sitemap() -> None:
    """Une page servie 200 vers laquelle rien d'indexé ne pointe n'est trouvée par personne."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(JSON.stringify(m.entreesDeSitemap()));" % GENERATEUR.as_uri()
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    entrees = json.loads(res.stdout)
    chemins = [e["chemin"] for e in entrees]
    assert chemins[0] == "rapports", "l'index des instantanés manque au sitemap"
    for instantane in instantanes():
        assert f"rapports/{instantane.name}" in chemins, f"{instantane.name} manque au sitemap"
    for entree in entrees:
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", entree["lastmod"]), (
            "`lastmod` porte la date des DONNÉES, celle du nom du fichier"
        )
    source = (UI / "scripts" / "pages-par-adresse.mjs").read_text(encoding="utf-8")
    assert "entreesDeSitemap()" in source, "le sitemap du build ne reprend pas les instantanés"


def test_le_serveur_de_developpement_resout_les_adresses_sans_extension() -> None:
    """`/rapports` rendait un écran blanc en local : Vite ne fait pas ce que Pages fait."""
    config = (UI / "vite.config.js").read_text(encoding="utf-8")
    assert "apply: 'serve'" in config, "le repli ne doit valoir qu'en développement"
    assert "public" in config and ".html" in config, (
        "le serveur de développement ne résout plus `/x` en `public/x.html`"
    )


def test_un_instantane_ne_se_nomme_pas_autrement_dans_son_texte() -> None:
    """Un article de type instantané ne se désigne pas lui-même comme « ce rapport » ou « ce panorama ».

    Le 23/09/2026 la même page se nommait de trois façons — « instantané » dans
    la barre, « ce rapport » dans un titre, « ce panorama » dans le chapeau.
    L'adresse `/rapports` reste, elle : c'est un identifiant, pas un mot lu.

    **Ce que la garde vise, c'est le nom que la page se donne, pas le mot.**
    Jusqu'au 12/10/2026 elle refusait toute occurrence de « rapport » ou de
    « panorama » : elle a alors bloqué le titre d'une figure (« Panorama des
    textes déposés par les groupes parlementaires ») et le titre d'un texte de
    l'Assemblée (« … l'équilibre dans les rapports locatifs »), qui ne nomment
    ni l'un ni l'autre l'article. La propriétaire, le 12/10 : « il ne
    s'agissait pas d'appliquer une règle aussi stricte ».
    → `docs/decisions/rapport-et-panorama-mots-permis-1217.md`
    """
    se_nomme = re.compile(
        r"\b(?:ce|cet|le présent|la présente|notre)\s+(?:nouveau\s+|nouvelle\s+)?(rapport|panorama)\b",
        re.IGNORECASE,
    )
    for page in instantanes():
        visible = re.sub(r"<[^>]*>", " ", page.read_text(encoding="utf-8"))
        visible = re.sub(r"\s+", " ", visible)
        trouve = se_nomme.search(visible)
        assert trouve is None, (
            f"{page.name} se désigne par « {trouve.group(0) if trouve else ''} » : "
            "le mot publié pour l'objet est « article », de type « instantané »"
        )


def test_la_garde_du_nom_laisse_passer_un_titre_de_figure_et_refuse_ce_rapport() -> None:
    """La garde ci-dessus, sur les deux phrases qui l'ont fait resserrer et sur celle qu'elle doit encore refuser."""
    se_nomme = re.compile(
        r"\b(?:ce|cet|le présent|la présente|notre)\s+(?:nouveau\s+|nouvelle\s+)?(rapport|panorama)\b",
        re.IGNORECASE,
    )
    assert se_nomme.search("Panorama des textes déposés par les groupes parlementaires") is None
    assert se_nomme.search("Retrouver la confiance et l’équilibre dans les rapports locatifs") is None
    assert se_nomme.search("Ce que ce rapport ne dit pas") is not None
    assert se_nomme.search("ce panorama liste les interventions") is not None


# ── Le carrousel de l'accueil (15/10/2026) ──────────────────────────────────


@pytest.mark.parametrize("instantane", instantanes(), ids=lambda p: p.name)
def test_un_article_est_livre_avec_sa_vignette(instantane: Path) -> None:
    """La vignette est choisie à la publication — la figure la plus parlante
    de l'article — et livrée à côté de lui : le carrousel ne la fabrique pas."""
    vignette = instantane.with_name(instantane.name.replace(".html", ".vignette.jpg"))
    assert vignette.is_file(), (
        f"{vignette.name} manque : un article se publie avec sa vignette, que montre l'accueil"
    )


def test_la_liste_de_l_accueil_ne_derive_pas_du_dossier() -> None:
    """`public/rapports.json` est ce que lit le carrousel : un article ajouté
    sans régénérer serait absent de l'accueil."""
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(m.listeAccueil(m.instantanes()));" % GENERATEUR.as_uri()
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    assert res.stdout == (UI / "public" / "rapports.json").read_text(encoding="utf-8"), (
        "public/rapports.json a dérivé : relancer `node scripts/index-rapports.mjs`"
    )
    liste = json.loads(res.stdout)
    assert [a["date"] for a in liste] == sorted((a["date"] for a in liste), reverse=True), (
        "le plus récent d'abord, jamais un autre ordre (§2 règle 1)"
    )


def test_l_accueil_montre_les_analyses_au_dessus_du_pied_de_page() -> None:
    # Depuis #1329 (22/10/2026), le carrousel est dans la carte héro, en tête de
    # l'accueil, et non plus au-dessus du pied de page.
    page = (UI / "src" / "pages" / "LandingPage.jsx").read_text(encoding="utf-8")
    assert page.index("<Hero />") < page.index("<PiedDeSite />")
    hero = (UI / "src" / "components" / "landing" / "Hero.jsx").read_text(encoding="utf-8")
    assert "<AnalysesThematiques dansHero />" in hero
    carrousel = (UI / "src" / "components" / "landing" / "AnalysesThematiques.jsx").read_text(encoding="utf-8")
    # Depuis #1329, la liste est lue à un seul endroit pour ses trois lecteurs —
    # le carrousel, le bandeau « Articles », les fiches.
    lecteur = (UI / "src" / "data" / "articles.js").read_text(encoding="utf-8")
    assert "fetch('/rapports.json')" in lecteur, "la liste vient du dossier, jamais recopiée"
    assert "getArticles" in carrousel
    assert "prefers-reduced-motion" in carrousel, "aucune rotation pour qui a demandé moins d'animations"
