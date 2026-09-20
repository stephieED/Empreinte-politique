"""#909 — une étiquette de licence ne s'écrit jamais en dur.

`AGENTS.md` §7 le dit depuis #530 : `meta.licence_donnees` est un champ
**dérivé**, recomposé depuis `sources[]` par `licences.appliquer_licence_donnees`
après chaque étape qui touche ces sources. Les 24 tests de
`test_licences_530.py` vérifient cette dérivation — aucun ne vérifiait qu'un
module ne la **contourne** pas.

C'est ce trou qui a laissé `mep_profile.normalize_parltrack` inscrire pendant
quatre lots « Open Data — Parltrack (CC0 / Open Database License) », une
étiquette que `docs/decisions/licences.md` avait pourtant relevée comme fausse
en instruisant #530 : les dumps ParlTrack sont sous ODbL v1.0, et le CC0
annoncé effaçait le partage à l'identique.

Les deux tests d'ici ne sont donc pas redondants. Le premier ferme le cas
mesuré ; le second ferme la **famille**, pour que le prochain constructeur de
profil n'ait pas à connaître le premier.
"""

import ast
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "src"
sys.path.insert(0, str(SRC))

from licences import LICENCE_PARLTRACK  # noqa: E402
from mep_profile import normalize_parltrack  # noqa: E402

#: Le seul module autorisé à contenir des littéraux de licence : c'est lui, le
#: référentiel. Le sortir de cette liste ferait de n'importe quel module un
#: référentiel concurrent — exactement ce que #530 a démonté.
MODULE_REFERENTIEL = "licences.py"

#: Le champ dérivé, sous ses deux écritures possibles en Python.
CHAMP = "licence_donnees"


def _mep_brut_minimal() -> dict:
    """Un enregistrement ParlTrack réduit à ce que la licence exige.

    `normalize_parltrack` ne lit le réseau nulle part : `get_cache_date` retombe
    sur `None` quand le dump n'est pas en cache, et c'est le seul accès disque.
    """
    return {
        "UserID": 197451,
        "Name": {"full": "DUPONT Marie"},
        "active": True,
        "Groups": [],
        "Committees": [],
        "Constituencies": [],
    }


def test_un_profil_mep_derive_sa_licence_au_lieu_de_l_annoncer():
    profil = normalize_parltrack(_mep_brut_minimal(), votes=[])

    assert profil["meta"][CHAMP] == LICENCE_PARLTRACK


def test_un_profil_mep_n_annonce_jamais_du_cc0():
    """Le fond de #909 : ParlTrack est du partage à l'identique, pas du CC0.

    Une régression ici ne casserait pas le pipeline — elle publierait une
    licence qui autorise ce que la vraie interdit.
    """
    profil = normalize_parltrack(_mep_brut_minimal(), votes=[])

    assert "CC0" not in profil["meta"][CHAMP]
    assert "ODbL" in profil["meta"][CHAMP]


def _cible_est_le_champ_licence(cible: ast.expr) -> bool:
    """True si `cible` écrit `…["licence_donnees"]` ou `….licence_donnees`."""
    if isinstance(cible, ast.Subscript):
        indice = cible.slice
        return isinstance(indice, ast.Constant) and indice.value == CHAMP
    if isinstance(cible, ast.Attribute):
        return cible.attr == CHAMP
    return False


def _affectations_litterales(source: str) -> list[int]:
    """Les lignes où `licence_donnees` reçoit une chaîne littérale.

    Une f-string compte : elle compose une étiquette sur place, ce qui est la
    même faute par un autre chemin. Un appel — `appliquer_licence_donnees(…)`,
    `composer_licence_donnees(…)` — n'en est pas une, et une constante importée
    de `licences` non plus : c'est le référentiel qui parle.
    """
    lignes: list[int] = []
    for noeud in ast.walk(ast.parse(source)):
        if isinstance(noeud, ast.Assign):
            cibles, valeur = noeud.targets, noeud.value
        elif isinstance(noeud, ast.AnnAssign) and noeud.value is not None:
            cibles, valeur = [noeud.target], noeud.value
        else:
            continue
        if not any(_cible_est_le_champ_licence(c) for c in cibles):
            continue
        if isinstance(valeur, ast.Constant) and isinstance(valeur.value, str):
            lignes.append(noeud.lineno)
        elif isinstance(valeur, ast.JoinedStr):
            lignes.append(noeud.lineno)
    return lignes


@pytest.mark.parametrize(
    "module",
    sorted(p for p in SRC.glob("*.py") if p.name != MODULE_REFERENTIEL),
    ids=lambda p: p.name,
)
def test_aucun_module_n_ecrit_une_etiquette_de_licence_en_dur(module: Path):
    lignes = _affectations_litterales(module.read_text(encoding="utf-8"))

    assert not lignes, (
        f"{module.name} écrit `{CHAMP}` en dur ligne(s) {lignes}. "
        f"C'est un champ dérivé depuis #530 : importer "
        f"`appliquer_licence_donnees` de `licences` (AGENTS.md §7). "
        f"Une étiquette recopiée à la main survit à la source qu'elle décrit — "
        f"celle de `mep_profile` annonçait du CC0 pour de l'ODbL (#909)."
    )
