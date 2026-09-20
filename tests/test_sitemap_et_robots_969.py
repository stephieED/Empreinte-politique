"""`sitemap.xml`, `robots.txt` et le contrôle de référencement (#969).

Mesuré en production le 17/09/2026 : les deux fichiers étaient absents, et
`/sitemap.xml` répondait 404 — un moteur n'avait aucune liste à explorer.

Le sitemap liste les **57 pages publiées**, jamais les **33 redirections**
(arbitré le 17/09/2026) : une redirection n'a rien à indexer, et sa `canonical`
dit déjà où aller. `lastmod` porte la date de la DONNÉE (`meta.genere_le`), pas
celle du build : un build qui ne change rien n'annonce pas 57 pages modifiées.

CE QU'ILS NE COUVRENT PAS : la CI n'installe pas Node et ne construit rien. Le
build complet a été lancé le 17/09/2026, puis `dist/` servi par un serveur
imitant Pages : `node web/UI_finale/scripts/verifier-referencement.mjs
http://127.0.0.1:8969` rend « 57 adresses du sitemap, dont 52 fiches ; 57 en
200, 57 titres distincts. Aucun défaut. »
"""

from __future__ import annotations

import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale"
MODULE = UI / "scripts" / "sitemap-et-robots.mjs"
CONTROLE = UI / "scripts" / "verifier-referencement.mjs"
PAGES = UI / "scripts" / "pages-par-adresse.mjs"
COMMANDES = RACINE / "docs" / "commandes.md"

ENTREES = [
    {"chemin": "", "lastmod": "2026-09-17"},
    {"chemin": "candidats/jean-luc-melenchon", "lastmod": "2026-09-17T10:29:51+0000"},
    {"chemin": "gouvernements/ATTAL", "lastmod": "2026-09-13T03:23:37+0000"},
    {"chemin": "faq", "lastmod": None},
]


def _node(corps: str) -> str:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    script = f"import * as S from {json.dumps(MODULE.as_uri())};\n{corps}"
    res = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return res.stdout


@pytest.fixture(scope="module")
def plan() -> str:
    return _node(f"console.log(S.sitemap('empreinte-politique.fr', {json.dumps(ENTREES)}));")


def test_le_sitemap_est_un_xml_valide_et_liste_chaque_adresse(plan):
    racine = ET.fromstring(plan)
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    locs = [u.findtext(f"{ns}loc") for u in racine.findall(f"{ns}url")]
    assert locs == [
        "https://empreinte-politique.fr/",
        "https://empreinte-politique.fr/candidats/jean-luc-melenchon",
        "https://empreinte-politique.fr/faq",
        "https://empreinte-politique.fr/gouvernements/ATTAL",
    ]


def test_lastmod_porte_la_date_de_la_donnee(plan):
    assert "<lastmod>2026-09-13</lastmod>" in plan, "la date d'un gouvernement est celle de sa génération"
    assert "T10:29:51" not in plan, "`lastmod` est un jour, pas un horodatage"


def test_une_date_absente_ne_devient_pas_une_date_inventee(plan):
    assert plan.count("<lastmod>") == 3


def test_ni_changefreq_ni_priority(plan):
    """Deux affirmations de plus à tenir, que Google ignore."""
    assert "changefreq" not in plan and "priority" not in plan


def test_le_sitemap_ne_liste_pas_les_redirections():
    script = PAGES.read_text(encoding="utf-8")
    bloc = script.split("const entrees =")[1].split("writeFileSync")[0]
    assert "publiees" in bloc and "redirections" not in bloc, (
        "le sitemap listerait des adresses qui n'ont rien à indexer"
    )


def test_robots_autorise_tout_le_monde_et_designe_le_sitemap():
    sortie = _node("console.log(S.robots('empreinte-politique.fr'));")
    assert "User-agent: *" in sortie and "Allow: /" in sortie
    assert "Disallow" not in sortie, "aucun robot n'est exclu, ceux des modèles de langage compris"
    assert "Sitemap: https://empreinte-politique.fr/sitemap.xml" in sortie


def test_le_build_ecrit_les_deux_fichiers():
    script = PAGES.read_text(encoding="utf-8")
    assert "'sitemap.xml'" in script and "'robots.txt'" in script


def test_le_controle_echoue_sur_ce_que_le_lot_promet():
    """Le critère de fin de #969 : la régression doit se voir."""
    source = CONTROLE.read_text(encoding="utf-8")
    for promesse in ("HTTP ${l.statut}", "aucun titre", "aucune canonical", "portent le titre", "sans JavaScript"):
        assert promesse in source, f"le contrôle ne relève plus : {promesse}"
    assert "process.exit(1)" in source


def test_le_controle_mesure_la_base_donnee_et_pas_la_production():
    source = CONTROLE.read_text(encoding="utf-8")
    assert "base + new URL(m[1]).pathname" in source, (
        "les `loc` portent le domaine de production : sans réécriture, un contrôle "
        "local mesure le site en ligne"
    )


def test_la_commande_est_documentee():
    assert "verifier-referencement.mjs" in COMMANDES.read_text(encoding="utf-8")
