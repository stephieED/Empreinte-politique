"""#901 — le seuil de publication d'un texte porté européen.

`AGENTS.md` §6 publie un texte porté « parvenu au moins en commission ». C'est
un **rang** dans la nomenclature française, et aucun stade européen n'en a :
appliqué tel quel, le seuil écartait les **383** textes portés européens, et
`raphael-glucksmann` affichait « 0 publiés » en en portant 23.

Arbitré le 14/09/2026 : la nomenclature européenne étant **plate** — ses seize
valeurs décrivent des états, pas des degrés —, la règle se dit par exclusion et
n'écarte que le stade qui correspond au `depose` français.
"""

import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from schema_pivot import (  # noqa: E402
    STADES_PROCEDURAUX_AN,
    STADES_PROCEDURAUX_UE,
    STADES_UE_NON_PUBLIES,
    STADES_UE_PUBLIES,
)


def test_un_seul_stade_europeen_est_ecarte():
    """58 dossiers sur les 20 442 qui portent un stade. Écarter davantage
    demanderait de classer des états qui ne s'ordonnent pas."""
    assert STADES_UE_NON_PUBLIES == {"ue_phase_preparatoire_parlement"}


def test_les_publies_sont_exactement_les_quinze_autres():
    assert STADES_UE_PUBLIES == STADES_PROCEDURAUX_UE - STADES_UE_NON_PUBLIES
    assert len(STADES_UE_PUBLIES) == 15


def test_le_stade_ecarte_existe_bien_dans_la_nomenclature():
    """Une exclusion qui ne vise rien n'exclut rien : si la valeur était
    renommée en amont, la règle deviendrait muette sans qu'une assertion tombe.
    """
    assert STADES_UE_NON_PUBLIES <= STADES_PROCEDURAUX_UE


def test_aucun_stade_francais_n_est_concerne():
    """Le seuil français reste un rang dans sa propre liste : cette règle ne le
    remplace pas, elle traite le cas qu'il ne savait pas traiter."""
    assert not (STADES_UE_PUBLIES & STADES_PROCEDURAUX_AN)
    assert not (STADES_UE_NON_PUBLIES & STADES_PROCEDURAUX_AN)


def test_agents_md_nomme_la_meme_exclusion_que_le_code():
    """La règle vit dans `AGENTS.md` §6 ; le code en est l'expression machine.
    Les deux qui divergent, c'est une règle appliquée que personne ne lit."""
    agents = (RACINE / "AGENTS.md").read_text(encoding="utf-8")
    ligne = next((l for l in agents.splitlines()
                  if "`textes_portes[]` **European**" in l), None)

    assert ligne is not None, (
        "AGENTS.md §6 ne porte plus la ligne des textes européens — la règle "
        "n'existe alors que dans le code, où personne ne la cherche.")
    for stade in STADES_UE_NON_PUBLIES:
        assert stade in ligne, (
            f"{stade!r} est écarté par le code mais absent de la ligne d'AGENTS.md.")
