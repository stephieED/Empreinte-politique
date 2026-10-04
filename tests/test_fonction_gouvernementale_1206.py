"""La parole de ministre se reconnaît dans les valeurs RÉELLES de `fonction` (#1206).

`fonction` est du texte libre du compte rendu. La règle tenait en trois mots,
écrits quand le champ n'existait que sur les candidats déclarés ; arrivé sur
tous les profils (#1200), il a montré ce qu'elle manquait. Les valeurs
ci-dessous sont COPIÉES du corpus publié (`pivot_data/profiles/`, relevé du
04/10/2026, `main` 9b7f2232c), avec leur nombre de prises de parole — pas des
exemples écrits de mémoire.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "web" / "UI_finale"

#: Fonctions gouvernementales, telles que la source les écrit.
GOUVERNEMENTALES = [
    "ministre",  # 61 245
    "secrétaire d’État",  # 14 029
    "ministre délégué",  # 11 649
    "garde des sceaux",  # 9 139 — manquée avant #1206
    "ministre d’État",  # 4 517
    "Premier ministre",  # 3 980
    "Première ministre",  # 1 947
    "garde des sceaux, ministre de la justice",  # 647
    "garde des sceaux Ministère de la justice",  # 1 — manquée avant #1206
    "secrétaire d’Etat chargé de l’enfance et des familles",  # 1 — manquée avant #1206
    "porte-parole du gouvernement, ministre déléguée chargée de l’énergie",  # 1
    "ministre déléguée chargée de la mémoire et des anciens combattants",  # 40
    "haut-commissaire",  # 60 — retenu par la propriétaire le 04/10/2026
    "haut-commissaire aux retraites",  # 19 — idem
]

#: Fonctions qui ne sont PAS gouvernementales, copiées du même relevé.
AUTRES = [
    "rapporteur",
    "rapporteur général",
    "président de la commission des finances",
    "Présidente",
    "président de l’OPECST",
    "présidente du groupe RE",
    "président de l’Ukraine",
    "suppléant Mme Isabelle Valentin",
    "Depute",
    "policier, lanceur d’alerte",
]


def _regle(valeurs: list) -> list:
    script = f"""
      import {{ estFonctionGouvernementale as f }} from './src/utils/fonctionGouvernementale.js';
      console.log(JSON.stringify({json.dumps(valeurs, ensure_ascii=False)}.map(f)));
    """
    sortie = subprocess.run(
        ["node", "--input-type=module", "-e", script], capture_output=True, text=True, cwd=UI, check=False,
    )
    assert sortie.returncode == 0, sortie.stderr
    return json.loads(sortie.stdout)


def test_les_fonctions_gouvernementales_du_corpus_sont_reconnues() -> None:
    reconnues = _regle(GOUVERNEMENTALES)
    manquees = [v for v, ok in zip(GOUVERNEMENTALES, reconnues) if not ok]
    assert not manquees, f"parole de ministre comptée comme parole de député : {manquees}"


def test_les_fonctions_parlementaires_du_corpus_ne_le_sont_pas() -> None:
    reconnues = _regle(AUTRES)
    prises = [v for v, ok in zip(AUTRES, reconnues) if ok]
    assert not prises, f"fonction non gouvernementale prise pour une parole de ministre : {prises}"


def test_une_fonction_absente_n_est_pas_gouvernementale() -> None:
    """La clé est absente quand le compte rendu ne dit rien, jamais nulle (§2 règle 5)."""
    assert _regle([None, ""]) == [False, False]
