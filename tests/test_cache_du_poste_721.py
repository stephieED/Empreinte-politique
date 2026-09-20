#!/usr/bin/env python3
"""
test_cache_du_poste_721.py — Aucun test ne lit le cache du poste, et le
garde-fou qui le dit ne devient pas muet (#721).

Le défaut, mesuré le 02/09/2026 : six tests rendaient **688** interventions là
où leur fixture en attendait **1**. Ils patchaient le constructeur
(`_build_acteur_interventions_syceron_index`) mais pas la lecture du cache, qui
passe avant lui — et les onze constantes de cache du dépôt valent
`Path(".cache") / ...`, un chemin **relatif au répertoire courant**. En CI, le
checkout partiel ne pose pas `.cache/`, la lecture échoue, le test passe ; sur
un poste ayant déjà collecté, elle réussit et sert des données réelles.

Deux propriétés se tiennent ici, et la seconde protège la première :

1. le garde-fou de `conftest.py` refuse une ouverture sous le `.cache` du dépôt ;
2. les constantes de cache restent **relatives**, ce qui est ce qui rend
   `monkeypatch.chdir(tmp_path)` suffisant pour isoler un test. Une constante
   rendue absolue laisserait `chdir` sans effet, et le garde-fou serait alors le
   seul filet — il tient, mais le test qui l'a déclenché serait à réécrire.

Le garde-fou est piloté **sans faire échouer la suite** : on appelle le filtre
directement, comme `test_hook_diagnostic_sparse_checkout.py` le fait pour son
propre hook. Un diagnostic qui cesse de parler sans le dire est pire que pas de
diagnostic.
"""

from pathlib import Path
import importlib
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import conftest as conftest_suite  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# 1. Ce que le garde-fou reconnaît
# --------------------------------------------------------------------------

def test_un_chemin_du_cache_du_depot_est_reconnu():
    assert conftest_suite._sous_le_cache_du_depot(
        str(RACINE / ".cache" / "syceron_an" / "17" / "index_par_acteur" / "PA1.json")
    )


def test_le_cache_lui_meme_est_reconnu():
    assert conftest_suite._sous_le_cache_du_depot(str(RACINE / ".cache"))


def test_un_objet_pathlike_est_reconnu():
    assert conftest_suite._sous_le_cache_du_depot(RACINE / ".cache" / "questions_an")


def test_un_chemin_en_octets_est_reconnu():
    """`open()` accepte des `bytes` ; les ignorer laisserait un trou silencieux."""
    assert conftest_suite._sous_le_cache_du_depot(bytes(RACINE / ".cache" / "x"))


def test_un_cache_ailleurs_nest_pas_reconnu(tmp_path):
    """C'est le cas nominal des tests qui s'isolent par `chdir` : leur `.cache`
    est sous un `tmp_path`, il ne doit rien déclencher."""
    assert not conftest_suite._sous_le_cache_du_depot(str(tmp_path / ".cache" / "syceron_an"))


def test_un_fichier_du_depot_hors_cache_nest_pas_reconnu():
    assert not conftest_suite._sous_le_cache_du_depot(str(RACINE / "AGENTS.md"))


def test_un_descripteur_deja_ouvert_nest_pas_reconnu():
    """`open(3)` réouvre un descripteur : il n'y a pas de chemin à examiner."""
    assert not conftest_suite._sous_le_cache_du_depot(3)


# --------------------------------------------------------------------------
# 2. Le garde-fou parle, et il nomme le fichier
# --------------------------------------------------------------------------

def test_ouvrir_le_cache_du_poste_leve_en_nommant_le_fichier(monkeypatch):
    """Piloté sans faire échouer la suite : la fixture `autouse` de `conftest`
    a déjà remplacé `builtins.open`, on l'appelle donc directement."""
    import builtins

    cible = str(RACINE / ".cache" / "syceron_an" / "17" / "index_par_acteur" / "PA1567.json")
    with pytest.raises(conftest_suite.CacheDuPosteLuDansUnTest) as exc:
        builtins.open(cible)

    message = str(exc.value)
    assert cible in message
    assert "#721" in message
    # Le message doit dire QUOI FAIRE, pas seulement ce qui est interdit.
    assert "monkeypatch.chdir" in message


def test_le_garde_fou_laisse_passer_le_reste(tmp_path):
    """Sans ça, il ne serait pas un garde-fou mais une panne."""
    fichier = tmp_path / "temoin.txt"
    fichier.write_text("ok", encoding="utf-8")
    assert fichier.read_text(encoding="utf-8") == "ok"


# --------------------------------------------------------------------------
# 3. Les constantes de cache restent relatives
# --------------------------------------------------------------------------

#: Modules de `src/` portant une constante de cache. Le balayage se fait sur les
#: modules IMPORTÉS : les nommer ici garantit qu'ils le sont, quel que soit
#: l'ordre des tests.
_MODULES_A_CACHE = (
    "an_roster", "candidate_profile", "candidate_profile_ue", "gouvernement_textes",
    "mep_profile", "parltrack_dumps", "syceron_debates",
)


def _constantes_de_cache():
    for nom in _MODULES_A_CACHE:
        module = importlib.import_module(nom)
        for attribut in dir(module):
            if attribut.startswith("__"):
                continue
            valeur = getattr(module, attribut, None)
            if isinstance(valeur, Path) and ".cache" in str(valeur):
                yield f"{nom}.{attribut}", valeur


def test_les_constantes_de_cache_sont_toutes_relatives():
    """C'est cette propriété qui rend `monkeypatch.chdir(tmp_path)` suffisant.

    Une constante absolue isolerait mal : `chdir` n'aurait plus d'effet sur elle,
    et un test qui croirait s'être isolé lirait le cache du poste — avec pour
    seul filet le garde-fou de `conftest.py`, qui échouerait au lieu de servir la
    fixture attendue.
    """
    absolues = sorted(nom for nom, valeur in _constantes_de_cache() if valeur.is_absolute())
    assert not absolues, (
        "ces constantes de cache sont absolues, donc insensibles à "
        f"`monkeypatch.chdir` : {absolues}. Les rendre relatives, ou isoler les "
        "tests concernés en réglant la constante elle-même.")


def test_il_y_a_bien_des_constantes_a_surveiller():
    """Compteur-témoin : si le balayage cessait de rien trouver, le test
    ci-dessus passerait pour de bonnes raisons apparentes et de mauvaises
    vraies — le trou muet de #510."""
    assert len(list(_constantes_de_cache())) >= 10
