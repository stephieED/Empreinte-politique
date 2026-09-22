"""#1075 — un index partagé ne se réécrit pas pour son seul `genere_le`.

Mesuré sur le commit du run `35648745220` (21/09/2026) : sur les 18 fichiers
de `pivot_data/` modifiés hors profils, 13 ne changeaient que par
`genere_le` — dont `amendements/15.json`, 70 Mo, législature close.

Un index ne contient que ce que les profils collectés citent : un nouveau
profil qui a siégé sous la 15e doit, lui, faire changer `15.json`. La règle
est donc « le contenu a changé », jamais « la législature est close ».

Le scrutin est une entrée RÉELLE de `pivot_data/scrutins.json`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE / "src"))

from json_io import dumps_indente, ecrire_index_json  # noqa: E402
from scrutins_index import ScrutinsIndex, ecrire  # noqa: E402

SCRUTIN = json.loads('''{"id": "an:14:1", "legislature": "14", "legislature_provenance": "collectee", "numero_scrutin": "1", "date": "2012-07-03", "texte": "la déclaration de politique générale du gouvernement de Jean-Marc Ayrault (application de l'article 49, alinéa premier de la Constitution).", "sort": "l'Assemblée nationale a adopté", "type_scrutin": "tribune", "type_vote": "vote_texte", "texte_lie_id": null, "source_url": "https://www.assemblee-nationale.fr/dyn/14/scrutins/1", "demandeur": "Conférence des présidents"}''')


def _index(genere_le, scrutins=None):
    return {"schema_version": "x", "genere_le": genere_le, "licence_donnees": "y",
            "scrutins": scrutins if scrutins is not None else [SCRUTIN]}


def test_un_index_inchange_n_est_pas_reecrit(tmp_path):
    chemin = tmp_path / "index.json"
    assert ecrire_index_json(chemin, _index("2026-09-21T06:01:06+0000"))
    avant = chemin.read_bytes()

    assert not ecrire_index_json(chemin, _index("2026-09-21T16:59:45+0000"))

    assert chemin.read_bytes() == avant
    assert json.loads(avant)["genere_le"] == "2026-09-21T06:01:06+0000"


def test_un_contenu_change_reecrit_avec_la_nouvelle_date(tmp_path):
    """Le cas du nouveau profil : un amendement de plus, et le fichier bouge."""
    chemin = tmp_path / "index.json"
    ecrire_index_json(chemin, _index("2026-09-21T06:01:06+0000"))

    autre = {**SCRUTIN, "id": SCRUTIN["id"] + "-bis"}
    assert ecrire_index_json(chemin, _index("2026-09-22T06:00:00+0000", [SCRUTIN, autre]))

    publie = json.loads(chemin.read_text(encoding="utf-8"))
    assert publie["genere_le"] == "2026-09-22T06:00:00+0000"
    assert len(publie["scrutins"]) == 2


def test_un_changement_de_format_compte_comme_un_changement(tmp_path):
    chemin = tmp_path / "index.json"
    ecrire_index_json(chemin, _index("2026-09-21T06:01:06+0000"))

    assert ecrire_index_json(chemin, _index("2026-09-22T06:00:00+0000"), dumps_indente)


def test_un_genere_le_null_se_compare_aussi(tmp_path):
    chemin = tmp_path / "index.json"
    ecrire_index_json(chemin, _index(None), dumps_indente)

    assert not ecrire_index_json(chemin, _index("2026-09-22T06:00:00+0000"), dumps_indente)


def test_l_ecrivain_reel_de_scrutins_json_garde_sa_date(tmp_path):
    chemin = tmp_path / "scrutins.json"
    index = ScrutinsIndex({SCRUTIN["id"]: SCRUTIN})
    ecrire(chemin, index, genere_le="2026-09-21T06:01:06+0000")

    ecrire(chemin, index, genere_le="2026-09-22T06:00:00+0000")

    assert json.loads(chemin.read_text(encoding="utf-8"))["genere_le"] == "2026-09-21T06:01:06+0000"
