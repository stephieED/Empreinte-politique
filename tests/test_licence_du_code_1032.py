"""La licence du code, et les trois régimes qui ne se confondent pas (#1032).

Le dépôt était **public sans licence** : lisible, et tous droits réservés par
défaut. `/a-propos` allait pourtant écrire « le code est public », ce qu'un
lecteur lit comme une autorisation de réutilisation, pendant que les mentions
légales disaient « à préciser » — deux pages, deux réponses à la même question.
C'est la propriétaire qui l'a relevé.

Arbitré le 18/09/2026 : **code sous AGPL-3.0, textes et charte tous droits
réservés, données sous les licences de leurs sources.**

Ce que ces garde-fous protègent :

1. **Le dépôt porte le texte officiel de la licence.** Sans le fichier, « open
   source » est faux ; la clause « ce qui entre est sous la même licence que ce
   qui sort » de GitHub ne joue pas non plus, et une PR extérieure arrive sans
   cadre.
2. **Les trois pages disent la même chose.** `/a-propos`, `/mentions-legales` et
   le README. Une contradiction entre deux d'entre elles est ce que ce lot
   corrige.
3. **Les trois régimes restent distincts.** Une licence de logiciel ne couvre ni
   la prose ni la marque, et ne touche pas les licences des données (§7) — dont
   la clause de partage à l'identique de l'ODbL vit sur certains champs.
4. **L'offre de source de l'AGPL (section 13).** Un service en réseau doit
   permettre à qui l'utilise d'atteindre le code : `/a-propos` porte le lien
   vers le dépôt.

CE QU'ILS NE COUVRENT PAS : que le site déployé corresponde au code publié.
C'est une obligation de l'AGPL qu'aucun test ne peut vérifier d'ici — elle se
tient en ne déployant que ce qui est poussé.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
LICENCE = RACINE / "LICENSE"
README = RACINE / "README.md"
AGENTS = RACINE / "AGENTS.md"
WEB = RACINE / "web" / "UI_finale"
APROPOS = WEB / "src" / "pages" / "AboutPage.jsx"
LEGAL = WEB / "src" / "pages" / "LegalNoticePage.jsx"
PACKAGE = WEB / "package.json"

SPDX = "AGPL-3.0"
DEPOT = "github.com/stephieED/Empreinte-politique-src"


@pytest.fixture(scope="module")
def licence() -> str:
    assert LICENCE.exists(), "sans ce fichier, « open source » est faux"
    return LICENCE.read_text(encoding="utf-8")


def test_le_depot_porte_le_texte_officiel_de_l_agpl(licence: str) -> None:
    """Le texte de la FSF, pas un résumé : une licence se cite en entier."""
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in licence
    assert "Version 3, 19 November 2007" in licence
    # La section 13 est celle qui distingue l'AGPL de la GPL.
    assert "13. Remote Network Interaction" in licence
    assert len(licence.splitlines()) > 600, "le texte complet fait ~660 lignes"


def test_les_trois_pages_annoncent_la_meme_licence() -> None:
    """Une contradiction entre deux d'entre elles est ce que ce lot corrige."""
    for fichier in (APROPOS, LEGAL, README):
        assert SPDX in fichier.read_text(encoding="utf-8"), fichier.name


def test_les_mentions_legales_separent_le_code_de_la_prose() -> None:
    """« Le code source, la charte graphique et les textes sont à préciser »
    mettait les trois dans le même panier. Ils ont trois régimes."""
    legal = LEGAL.read_text(encoding="utf-8")
    assert "tous droits réservés" in legal
    assert "à préciser, sauf" not in legal, "l'ancien paragraphe est parti"
    assert "restent sous leurs licences propres" in legal


def test_la_page_a_propos_porte_l_offre_de_source() -> None:
    """Section 13 de l'AGPL : qui utilise le service doit pouvoir atteindre le
    code de la version qu'il utilise."""
    apropos = APROPOS.read_text(encoding="utf-8")
    assert DEPOT in apropos
    assert "open source" in apropos


def test_le_paquet_declare_son_identifiant_spdx() -> None:
    """`npm` et les outils d'analyse lisent ce champ, pas le README."""
    paquet = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert paquet.get("license") == "AGPL-3.0-only"


def test_la_licence_du_code_ne_touche_pas_celle_des_donnees() -> None:
    """La clause de partage à l'identique de l'ODbL vit sur certains champs quelle
    que soit la licence du code : les deux ne se répondent pas (§7)."""
    for fichier in (README, AGENTS):
        texte = fichier.read_text(encoding="utf-8")
        assert "ODbL" in texte
    assert "changes nothing here" in AGENTS.read_text(encoding="utf-8")
