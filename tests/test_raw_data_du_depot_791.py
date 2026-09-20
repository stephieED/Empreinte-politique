#!/usr/bin/env python3
"""Les garde-fous de lecture mordent encore, `pathlib` compris (#791).

`tests/conftest.py` refuse deux populations de fichiers du dépôt : le cache du
poste (#721) et les `.json` de `raw_data/` (#791). Ce fichier est leur témoin.

## Le défaut qu'il verrouille

Le garde-fou de #721 ne coupait que `builtins.open`. **`pathlib` ne passe pas
par là** : `Path.open()` appelle `io.open`, et `builtins.open` en est une AUTRE
référence — patcher l'une laisse l'autre intacte. Mesuré le 10/09/2026 sur la
suite complète : des 144 tests qui ouvraient un fichier du dépôt sous
surveillance, **41** passaient par `builtins.open` et **103** par `pathlib`.
Le trou n'était pas théorique : `test_candidate_profile.py::test_download_and_
build_amendement_index_disk_marker_from_different_run_is_ignored` calculait le
chemin de son marqueur AVANT de régler `AMENDEMENTS_CACHE_DIR`, créait
`.cache/amendements_an/17/` dans le dépôt et y écrivait — pendant deux mois,
sans que le garde-fou censé l'attraper dise quoi que ce soit.

## Ce que le témoin vérifie

1. les trois portes sont coupées (`builtins.open`, `io.open`, `Path.open`) ;
2. la restauration a bien lieu entre deux tests — sinon les filtres
   s'empileraient, et un garde-fou empilé 4 380 fois n'est pas un garde-fou ;
3. le refus nomme le fichier et dit quoi faire, des deux côtés ;
4. une déclaration `lit_reference_committee` ne peut pas autoriser un chemin
   que le `sparse-checkout` de `tests.yml` ne télécharge pas — sans quoi elle
   servirait à masquer #791 au lieu de le nommer ;
5. les référentiels servis à la suite sont bien les fixtures figées, et les
   mémos de module sont vides à l'entrée du test (le piège de #767).

Les filtres sont appelés **directement**, sans faire échouer la suite, comme
`test_hook_diagnostic_sparse_checkout.py` le fait pour son propre hook.
"""

import builtins
import io
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import _outils_ci  # noqa: E402
import conftest as conftest_suite  # noqa: E402

# Importés ICI, au chargement du module, et non dans le corps des tests : la
# fixture de `conftest.py` ne règle les défauts que sur les modules DÉJÀ
# importés, et elle s'exécute après la collecte. Un import tardif verrait le
# chemin réel — et se ferait refuser par le garde-fou, bruyamment.
import correspondance_acteurs_an  # noqa: E402
import generate_all_profiles  # noqa: E402
import perimetre_candidats  # noqa: E402

RACINE = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------
# 1. Les trois portes sont coupées, et rien ne s'empile
# --------------------------------------------------------------------------

def test_les_trois_portes_sont_coupees():
    """`builtins.open`, `io.open` et `Path.open` : trois références, et aucune
    n'attrape les deux autres."""
    for porte in (builtins.open, io.open, Path.open):
        assert porte.__module__ == "conftest", (
            f"{porte!r} n'est pas le filtre de conftest : la porte est ouverte")


def _originaux_captures(filtre):
    """Ce que le filtre a capturé comme fonction d'ouverture « réelle »."""
    return [cellule.cell_contents for cellule in (filtre.__closure__ or ())]


def test_le_garde_fou_ne_sempile_pas():
    """La preuve que `monkeypatch` restaure : le filtre du test COURANT a
    capturé la vraie fonction d'ouverture, pas le filtre du test précédent.

    Sans restauration, les filtres se chaîneraient d'un test à l'autre — 4 380
    couches à la fin de la suite, et un `RecursionError` avant.
    """
    captures = _originaux_captures(builtins.open)
    assert any(type(c).__name__ == "builtin_function_or_method" for c in captures), (
        "le filtre de `builtins.open` a capturé autre chose que la fonction "
        "native : un filtre d'un test précédent n'a pas été retiré")

    captures_path = _originaux_captures(Path.open)
    assert any(getattr(c, "__qualname__", "") == "Path.open"
               and getattr(c, "__module__", "") == "pathlib" for c in captures_path), (
        "le filtre de `Path.open` n'a pas capturé `pathlib.Path.open` : "
        "la restauration n'a pas eu lieu")


# --------------------------------------------------------------------------
# 2. Le cache du poste, par les trois portes (#721)
# --------------------------------------------------------------------------

CIBLE_CACHE = RACINE / ".cache" / "syceron_an" / "17" / "index_par_acteur" / "PA1567.json"


def test_le_cache_du_poste_est_refuse_par_builtins():
    with pytest.raises(conftest_suite.CacheDuPosteLuDansUnTest) as exc:
        builtins.open(str(CIBLE_CACHE))
    assert "#721" in str(exc.value)


def test_le_cache_du_poste_est_refuse_par_io():
    with pytest.raises(conftest_suite.CacheDuPosteLuDansUnTest):
        io.open(str(CIBLE_CACHE))


def test_le_cache_du_poste_est_refuse_par_pathlib():
    """LE cas de #791 : `Path.read_text` passe par `io.open`, jamais par
    `builtins.open`. C'est par là que le marqueur d'amendements passait."""
    with pytest.raises(conftest_suite.CacheDuPosteLuDansUnTest):
        CIBLE_CACHE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# 3. Les `.json` de raw_data/, par les trois portes (#791)
# --------------------------------------------------------------------------

CIBLE_RAW = RACINE / "raw_data" / "correspondance_acteurs_an.json"


def test_un_json_de_raw_data_est_refuse_par_builtins():
    with pytest.raises(conftest_suite.RawDataDuDepotLuDansUnTest) as exc:
        builtins.open(str(CIBLE_RAW))
    message = str(exc.value)
    assert "raw_data/correspondance_acteurs_an.json" in message, "le message doit NOMMER le fichier"
    assert "#791" in message
    assert "tests/fixtures/" in message, "le message doit donner l'idiome à appliquer"


def test_un_json_de_raw_data_est_refuse_par_io():
    with pytest.raises(conftest_suite.RawDataDuDepotLuDansUnTest):
        io.open(str(CIBLE_RAW))


def test_un_json_de_raw_data_est_refuse_par_pathlib():
    with pytest.raises(conftest_suite.RawDataDuDepotLuDansUnTest):
        CIBLE_RAW.read_text(encoding="utf-8")


def test_une_ecriture_dans_raw_data_est_refusee_aussi():
    """Un test qui ÉCRIT dans `raw_data/` est pire qu'un test qui le lit : il
    salit l'arbre de travail de la personne qui lance la suite."""
    with pytest.raises(conftest_suite.RawDataDuDepotLuDansUnTest):
        (RACINE / "raw_data" / "candidats.json").write_text("{}", encoding="utf-8")


def test_le_corpus_publie_reste_au_hook_de_diagnostic():
    """`raw_data/profiles/` est exclu du checkout EXPRÈS (#473) et a déjà son
    message. Deux garde-fous sur le même chemin en donneraient deux."""
    assert conftest_suite._json_de_raw_data_du_depot(
        str(RACINE / "raw_data" / "profiles" / "jordan-bardella.json")) is None


def test_un_json_hors_du_depot_nest_pas_refuse(tmp_path):
    """Le cas nominal : les tests écrivent leurs configurations sous `tmp_path`."""
    fichier = tmp_path / "raw_data" / "groupes_reels.json"
    fichier.parent.mkdir(parents=True)
    fichier.write_text("{}", encoding="utf-8")
    assert fichier.read_text(encoding="utf-8") == "{}"


def test_un_fichier_du_depot_qui_nest_pas_un_json_nest_pas_refuse():
    """Le garde-fou porte sur les `.json` réécrits par un run, pas sur
    `raw_data/` entier : les archives figées ont leur propre régime."""
    assert conftest_suite._json_de_raw_data_du_depot(
        str(RACINE / "raw_data" / "amendements_an_figes" / "17" / "amendements.json.gz")) is None


# --------------------------------------------------------------------------
# 4. La déclaration `lit_reference_committee` ne peut pas mentir
# --------------------------------------------------------------------------

_DECLARATION = re.compile(r'lit_reference_committee\(\s*"([^"]+)"\s*\)')


def _declarations_de_la_suite() -> set[str]:
    trouvees = set()
    for fichier in sorted(Path(__file__).parent.glob("test_*.py")):
        trouvees.update(_DECLARATION.findall(fichier.read_text(encoding="utf-8")))
    return trouvees


def test_toute_declaration_est_couverte_par_le_sparse_checkout():
    """La condition qui rend la déclaration honnête : ce que la CI ne
    télécharge pas, aucun test ne le lit — sinon il ne tourne qu'en local, sur
    ce qu'un run y a laissé, et c'est #791 tel quel."""
    blanche = _outils_ci.lire_liste_blanche(conftest_suite.WORKFLOW_TESTS)
    assert blanche, "liste blanche illisible — voir `_outils_ci.lire_liste_blanche`"
    declarees = _declarations_de_la_suite()
    assert declarees, (
        "aucune déclaration relevée : le relevé s'est cassé, ou le marqueur a "
        "été retiré des fichiers de tests sans que ce témoin le sache")
    hors_liste = sorted(chemin for chemin in declarees if chemin not in blanche)
    assert not hors_liste, (
        "ces chemins sont déclarés lisibles mais absents du sparse-checkout de "
        f"tests.yml : {hors_liste}")


class _MarqueurFactice:
    def __init__(self, *args):
        self.args = args


class _ItemFactice:
    def __init__(self, *marqueurs):
        self._marqueurs = marqueurs

    def iter_markers(self, nom):
        return iter(self._marqueurs)


def test_une_declaration_hors_liste_blanche_leve():
    with pytest.raises(conftest_suite.ReferenceCommitteeHorsChecKout) as exc:
        conftest_suite._chemins_declares(
            _ItemFactice(_MarqueurFactice("raw_data/rosters_bruts.json")))
    assert "sparse-checkout" in str(exc.value)


def test_une_declaration_couverte_est_acceptee():
    autorises = conftest_suite._chemins_declares(
        _ItemFactice(_MarqueurFactice("raw_data/groupes_reels.json")))
    assert (RACINE / "raw_data" / "groupes_reels.json").resolve() in autorises


# --------------------------------------------------------------------------
# 5. Ce que la suite lit à la place, et les mémos vidés aux deux bouts (#767)
# --------------------------------------------------------------------------

def test_le_referentiel_servi_est_la_fixture_figee():
    assert correspondance_acteurs_an.CHEMIN_PAR_DEFAUT == conftest_suite.FIXTURE_CORRESPONDANCE
    assert conftest_suite.FIXTURE_CORRESPONDANCE.exists()
    table = correspondance_acteurs_an.charger_correspondance()
    assert table, "la fixture figée doit porter des entrées, sinon elle ne prouve rien"


def test_les_resolutions_servies_sont_la_fixture_neutre():
    """La constante est réglée sur la fixture neutre, et la fixture répond.

    Le paramètre par défaut de `declare_hors_an_par_identifiant` est lié à la
    DÉFINITION de la fonction : le régler ici ne le déplace pas, et c'est
    pourquoi le test passe le chemin. Ce qui compte est que les appelants de
    production lisent `perimetre.RESOLUTIONS_PAR_DEFAUT` à l'appel — sinon le
    garde-fou les arrêterait, bruyamment, ce qui reste le bon échec.
    """
    assert perimetre_candidats.RESOLUTIONS_PAR_DEFAUT == str(conftest_suite.FIXTURE_RESOLUTIONS)
    assert conftest_suite.FIXTURE_RESOLUTIONS.exists()
    assert not perimetre_candidats.declare_hors_an_par_identifiant(
        "Jordan Bardella", perimetre_candidats.RESOLUTIONS_PAR_DEFAUT)


def test_les_memos_sont_vides_a_lentree_du_test():
    """Un mémo non vidé sert la table d'un test voisin SANS rouvrir de fichier —
    donc sans que le garde-fou puisse le voir. C'est le piège de #767, et il se
    referme aux deux bouts : à l'entrée comme à la sortie."""

    assert correspondance_acteurs_an._MEMO == {}
    assert perimetre_candidats._MEMO_RESOLUTIONS == {}
    assert generate_all_profiles._MEMBRES_GROUPES_SUSPENDUS is None
