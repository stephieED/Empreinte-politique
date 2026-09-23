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
