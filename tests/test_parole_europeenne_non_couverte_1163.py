"""Des années de mandat européen sans prise de parole publiée se déclarent (#1163).

Arbitré par la propriétaire le 07/10/2026 : une ligne de « Ce qu'on n'a pas pu
lire », lue dans `couverture.interventions` — une entrée `hors_couverture` de
source `parlement_europeen`, avec sa `portee`.

AUCUNE FICHE NE PORTE ENCORE CETTE ENTRÉE : la forme a été convenue avec la
session qui produit les données, qui ne l'a pas encore écrite. L'entrée de ce
test est donc construite, sur les dates mesurées pour Emmanuel Maurel, et les
autres entrées de `couverture.interventions` sont COPIÉES de sa fiche du
07/10/2026. Le jour où le corpus la porte, remplacer l'entrée construite par
la sienne (#726).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
UI = RACINE / "web" / "UI_finale" / "src"
MODULE = UI / "utils" / "paroleEuropeenneNonCouverte.js"
REGLES = UI / "utils" / "profilCandidat.js"

#: Copiées de `pivot_data/profiles/emmanuel-maurel.pivot.json`, preuves abrégées.
COUVERTURE_MAUREL = [
    {"etat": "non_collecte", "portee": None, "preuve": "collecte écartée par le run qui a produit le profil brut"},
    {"etat": "couvert", "source": "parlement_europeen",
     "portee": {"debut": "2019-07-16", "fin": "2024-04-25"},
     "preuve": "« interventions » porte aussi du matériau du Parlement européen"},
]
#: Construite : la forme convenue, les dates mesurées le 07/10/2026.
TROU_MAUREL = {"etat": "hors_couverture", "source": "parlement_europeen",
               "portee": {"debut": "2014-07-01", "fin": "2019-07-01"},
               "preuve": "aucune source ne publie ses prises de parole de la 8e législature"}


def _lignes(interventions) -> list[dict]:
    if shutil.which("node") is None:
        pytest.skip("node absent")
    profil = {"couverture": {"interventions": interventions}}
    script = (
        "const m = await import(%r);\n"
        "process.stdout.write(JSON.stringify(m.paroleEuropeenneNonCouverte(%s)));"
        % (MODULE.as_uri(), json.dumps(profil))
    )
    res = subprocess.run(["node", "--input-type=module", "-e", script],
                         capture_output=True, text=True, check=False)
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


def test_la_fiche_d_aujourd_hui_ne_dit_rien() -> None:
    """Sans l'entrée déclarée, pas de ligne : `couvert` n'est pas un manque."""
    assert _lignes(COUVERTURE_MAUREL) == []


def test_le_trou_declare_fait_une_ligne() -> None:
    lignes = _lignes(COUVERTURE_MAUREL + [TROU_MAUREL])
    assert len(lignes) == 1
    assert lignes[0]["titre"] == "Parlement européen"
    assert lignes[0]["texte"] == (
        "Son mandat de juillet 2014 à juillet 2019 n’est pas couvert : "
        "la source ne publie aucune de ses prises de parole."
    )


def test_une_entree_de_l_assemblee_n_y_entre_pas() -> None:
    """`hors_couverture` sans source est une borne de l'Assemblée, dite ailleurs."""
    assemblee = {"etat": "hors_couverture", "portee": {"debut": None, "fin": "2012-06-19"}}
    assert _lignes([assemblee]) == []


def test_une_periode_sans_fin_se_dit_depuis() -> None:
    ouverte = {**TROU_MAUREL, "portee": {"debut": "2019-07-02", "fin": None}}
    assert _lignes([ouverte])[0]["texte"].startswith("Son mandat depuis juillet 2019 n’est pas couvert")


def test_un_mois_a_voyelle_s_elide() -> None:
    avril = {**TROU_MAUREL, "portee": {"debut": "2014-04-01", "fin": "2019-07-01"}}
    assert "Son mandat d’avril 2014 à juillet 2019" in _lignes([avril])[0]["texte"]


def test_la_section_appelle_la_regle() -> None:
    code = re.sub(r"/\*.*?\*/", "", REGLES.read_text(encoding="utf-8"), flags=re.DOTALL)
    liste = code[code.index("export function manquesDeLaFiche"):]
    assert "...paroleEuropeenneNonCouverte(profil)," in liste, (
        "la section 6 n'appelle plus la règle : le trou déclaré ne s'afficherait nulle part"
    )
