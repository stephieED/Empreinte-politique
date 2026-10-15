"""Les sources d'une candidature : une liste lue telle quelle par /sources (#1298).

`/sources` publie, pour chaque candidat, chaque article qui atteste sa
candidature. L'interface ne trie ni ne compte : elle lit `sources` s'il existe,
sinon `source`. Ces tests tiennent la forme dont elle dépend, sur le fichier réel.

Une entrée **sans** `sources` reste valide : `fetch_candidats_declares.py`
ajoute un candidat avec sa seule `source`, et c'est la relecture à la main qui
écrit la liste.
"""

import json
import re
from pathlib import Path

import pytest

#: Voir `test_perimetre_candidats_760.py` : le garde-fou de `conftest.py` exige
#: que le fichier de référence lu soit déclaré (#791).
pytestmark = pytest.mark.lit_reference_committee("raw_data/candidats.json")

DATE_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _candidats():
    source = Path("raw_data/candidats.json")
    if not source.exists():  # checkout partiel
        pytest.skip("raw_data/candidats.json absent de ce checkout")
    return json.loads(source.read_text(encoding="utf-8"))["candidats"]


def test_chaque_source_porte_url_media_et_date():
    fautes = []
    for c in _candidats():
        for s in c.get("sources", []):
            if set(s) != {"url", "media", "date"}:
                fautes.append(f"{c['nom']} : clés {sorted(s)}")
                continue
            if not str(s["url"]).startswith(("https://", "http://")):
                fautes.append(f"{c['nom']} : url {s['url']!r}")
            if not isinstance(s["media"], str) or not s["media"].strip():
                fautes.append(f"{c['nom']} : media vide")
            # Une date inconnue est `null`, jamais devinée (§2 règle 5).
            if s["date"] is not None and not DATE_ISO.match(s["date"]):
                fautes.append(f"{c['nom']} : date {s['date']!r}")
    assert not fautes, "\n".join(fautes)


def test_la_liste_commence_par_source_et_ne_repete_aucun_article():
    """`source` reste lu seul ailleurs (profils minimaux, identifiants) : la
    liste le reprend en tête, pour que les deux ne divergent jamais."""
    fautes = []
    for c in _candidats():
        if "sources" not in c:
            continue
        urls = [s["url"] for s in c["sources"]]
        if not urls or urls[0] != c.get("source"):
            fautes.append(f"{c['nom']} : `sources` ne commence pas par `source`")
        if len(urls) != len(set(urls)):
            fautes.append(f"{c['nom']} : un article répété")
    assert not fautes, "\n".join(fautes)
