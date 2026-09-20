"""Les mandats locaux sur la frise du parcours (#922).

CE QUE CES GARDES TIENNENT. Un rôle ouvert se dit `FIN_OUVERTE`, la valeur que
`positionSurAxe` rabat sur la fin de l'axe. Le premier branchement des mandats
locaux laissait `fin: null` : `positionSurAxe(null)` vaut 0, et chaque mandat en
cours se dessinait à la largeur minimale — la présidence de région de Bruno
Retailleau, commencée en 2021, tenait sur la frise comme trois mois. Aucun test
ne l'a vu ; c'est la propriétaire, en regardant la page.

Et un mandat clos du fichier des sortants n'a pas de date de fin publiée : il ne
doit pas être rouvert en déduisant `actif` de l'absence de fin, comme le fait une
fonction gouvernementale.
"""

from __future__ import annotations

import re
from pathlib import Path

REGLES = Path(__file__).resolve().parent.parent / "web" / "UI_finale" / "src" / "utils" / "profilCandidat.js"


def _bloc_local() -> str:
    source = REGLES.read_text(encoding="utf-8")
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    source = re.sub(r"^\s*//.*$", "", source, flags=re.MULTILINE)
    debut = source.index("m.categorie !== CATEGORIE_MANDAT_LOCAL")
    return source[debut:source.index("roles.sort(", debut)]


def test_un_mandat_local_en_cours_court_jusqu_a_la_fin_de_l_axe() -> None:
    bloc = _bloc_local()
    assert "FIN_OUVERTE" in bloc, (
        "un mandat local en cours doit finir sur `FIN_OUVERTE` : `null` le "
        "dessine à la largeur minimale"
    )


def test_un_mandat_local_clos_n_est_pas_rouvert() -> None:
    bloc = _bloc_local()
    assert re.search(r"const actif = Boolean\(m\.actif\);", bloc), (
        "`actif` se lit sur la source"
    )
    assert "!m.fin" not in bloc.split("const actif")[1].split(";")[0], (
        "déduire `actif` de l'absence de fin rouvrirait un mandat que la source dit achevé"
    )
