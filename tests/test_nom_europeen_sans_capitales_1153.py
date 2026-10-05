"""#1153 — le nom d'un député européen se publie dans la casse de la source.

« Florian PHILIPPOT » et « Raphaël GLUCKSMANN » s'affichaient en capitales sur
l'accueil, la fiche et les métadonnées de page. L'issue l'attribuait à la
saisie de `raw_data/candidats.json` : c'est faux, la liste porte « Florian
Philippot ». Les capitales viennent du `label` de l'API du Parlement européen,
repris tel quel comme nom du profil.

Les trois triplets ci-dessous sont copiés des réponses de
`data.europarl.europa.eu/api/v2/meps/<id>` relevées le 05/10/2026.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from candidate_profile_ue import _nom_complet  # noqa: E402

PHILIPPOT = {"label": "Florian PHILIPPOT", "givenName": "Florian", "familyName": "Philippot"}
GLUCKSMANN = {"label": "Raphaël GLUCKSMANN", "givenName": "Raphaël", "familyName": "Glucksmann"}
LE_PEN = {"label": "Marine LE PEN", "givenName": "Marine", "familyName": "Le Pen"}


def test_le_nom_est_assemble_des_deux_champs_en_casse_courante():
    assert _nom_complet(PHILIPPOT) == "Florian Philippot"
    assert _nom_complet(GLUCKSMANN) == "Raphaël Glucksmann"


def test_une_particule_garde_la_casse_que_la_source_lui_donne():
    """Aucune règle de casse : c'est la source qui écrit « Le Pen »."""
    assert _nom_complet(LE_PEN) == "Marine Le Pen"


def test_sans_les_deux_champs_le_label_reste_publie_tel_quel():
    assert _nom_complet({"label": "Florian PHILIPPOT"}) == "Florian PHILIPPOT"
    assert _nom_complet({"label": "Florian PHILIPPOT", "givenName": "Florian"}) == "Florian PHILIPPOT"
    assert _nom_complet({"label": "X Y", "givenName": " ", "familyName": "Y"}) == "X Y"
    assert _nom_complet({}) is None
