"""Le hook de diagnostic du sparse-checkout fonctionne encore (#619 puis #620).

`tests/conftest.py` porte un `pytest_runtest_makereport` qui, quand un test
échoue sur un fichier absent, ajoute au rapport que le chemin n'est peut-être
pas dans le `sparse-checkout` de `.github/workflows/tests.yml`. Il a été vérifié
par mutation à sa création, puis **plus rien ne le protégeait** : un renommage
du bloc YAML, un changement d'API pytest ou une refonte de l'analyseur le
rendrait muet en silence.

C'est le pire défaut possible pour un outil de diagnostic. Une aide qui cesse
de fonctionner sans le dire est pire que pas d'aide : on finit par faire
confiance à un silence qui ne veut plus rien dire. Ce fichier est ce qui
transforme cette panne-là en échec.

**Il ne provoque aucun échec réel.** Les fonctions internes du hook sont
appelables ; le hook lui-même est un `wrapper=True`, donc un générateur qu'on
pilote à la main (`next`, puis `send(rapport)`). Faire échouer un test bidon
pour observer le rapport coûterait un rouge permanent dans la suite.

**Aucun chemin de test n'est écrit sous la forme « ancre de racine, barre
oblique, nom entre guillemets »** — pas même en prose, ce fichier étant lui
aussi balayé : `test_ci_perimetre_sparse_checkout.py` relèverait le littéral
comme un chemin que la suite lit et en exigerait l'entrée dans la liste
blanche. Ils sont construits depuis `RACINE_DEPOT`, que son regex ne
reconnaît pas.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import conftest
import _outils_ci

RACINE_DEPOT = _outils_ci.RACINE_DEPOT

#: Un répertoire de premier niveau qui n'existe pas et n'est pas dans la liste.
HORS_LISTE = "un_repertoire_hors_liste_blanche"


@pytest.fixture(autouse=True)
def _cache_de_la_liste_blanche_neuf():
    """La liste est mémoïsée pour la durée du process : la vider des deux côtés
    évite qu'un cas pointant `WORKFLOW_TESTS` ailleurs contamine le suivant, ou
    le reste de la suite."""
    conftest._liste_blanche_sparse_checkout.cache_clear()
    yield
    conftest._liste_blanche_sparse_checkout.cache_clear()


class _FauxRapport:
    """Le strict nécessaire de ce que le hook lit et écrit d'un `TestReport`."""

    def __init__(self, failed: bool = True):
        self.failed = failed
        self.sections: list[tuple[str, str]] = []


class _FauxExcInfo:
    def __init__(self, exception: BaseException):
        self.value = exception


class _FauxCall:
    def __init__(self, exception: BaseException | None):
        self.excinfo = None if exception is None else _FauxExcInfo(exception)


def _sections_du_hook(exception: BaseException | None,
                      failed: bool = True) -> list[tuple[str, str]]:
    """Pilote le hook et rend les sections qu'il a ajoutées au rapport."""
    rapport = _FauxRapport(failed=failed)
    generateur = conftest.pytest_runtest_makereport(
        item=None, call=_FauxCall(exception))
    next(generateur)
    try:
        generateur.send(rapport)
    except StopIteration as fin:
        assert fin.value is rapport, "le hook doit rendre le rapport reçu"
    else:  # pragma: no cover - un wrapper qui ne s'arrête pas est un bug
        pytest.fail("le hook n'a pas terminé après réception du rapport")
    return rapport.sections


def _fichier_absent(chemin: Path | str) -> FileNotFoundError:
    """Un `FileNotFoundError` portant `filename`, comme `open()` le lève."""
    erreur = FileNotFoundError(2, "No such file or directory")
    erreur.filename = str(chemin)
    return erreur


# ---------------------------------------------------------------------------
# Le préalable : sans liste blanche lisible, tous les cas « se taire » seraient
# vrais par vacuité, et ce fichier ne protégerait rien.
# ---------------------------------------------------------------------------

def test_la_liste_blanche_du_workflow_est_lisible_aujourdhui():
    blanche = conftest._liste_blanche_sparse_checkout()
    assert blanche, (
        "le hook lit une liste vide : il est déjà muet. Le bloc "
        "`sparse-checkout: |` de tests.yml a changé de forme, ou "
        "`_outils_ci.lire_liste_blanche` ne le trouve plus.")
    assert {"tests", "src", "docs"} <= set(blanche), (
        f"liste blanche inattendue : {sorted(blanche)}")


# ---------------------------------------------------------------------------
# Les six cas vérifiés par mutation à la création du hook.
# ---------------------------------------------------------------------------

def test_il_parle_sur_un_chemin_absent_hors_liste_blanche():
    manquant = RACINE_DEPOT / HORS_LISTE / "fichier.json"
    sections = _sections_du_hook(_fichier_absent(manquant))
    assert len(sections) == 1, sections
    titre, corps = sections[0]
    assert titre == conftest.TITRE_SECTION
    assert f"{HORS_LISTE}/fichier.json" in corps
    assert conftest.MESSAGE_HORS_LISTE_BLANCHE in corps


@pytest.mark.parametrize("relatif", [
    "pivot_data/profiles/jean-dupont.pivot.json",
    "raw_data/profiles/jean-dupont.json",
])
def test_il_dit_de_ne_pas_inscrire_le_corpus_exclu_expres(relatif):
    """Les deux exclusions volontaires (#473) : parler, mais surtout ne pas
    conseiller la liste blanche — le garde-fou du workflow refuse leur retour."""
    sections = _sections_du_hook(_fichier_absent(RACINE_DEPOT / relatif))
    assert len(sections) == 1, sections
    corps = sections[0][1]
    assert relatif in corps
    assert conftest.RAPPEL_CORPUS in corps


def test_un_chemin_hors_liste_ordinaire_ne_recoit_pas_le_rappel_corpus():
    """Contre-épreuve du cas ci-dessus : le rappel #473 n'est pas collé partout."""
    manquant = RACINE_DEPOT / HORS_LISTE / "fichier.json"
    corps = _sections_du_hook(_fichier_absent(manquant))[0][1]
    assert conftest.RAPPEL_CORPUS not in corps


def test_il_se_tait_sur_une_assertion_ordinaire():
    assert _sections_du_hook(AssertionError("2 != 3")) == []


def test_il_se_tait_sur_un_chemin_absent_mais_couvert_par_la_liste():
    """`docs` est dans la liste blanche : le fichier manque pour une autre
    raison, et le hook n'a rien à dire."""
    manquant = RACINE_DEPOT / "docs" / "decisions" / "fiche-qui-nexiste-pas.md"
    assert _sections_du_hook(_fichier_absent(manquant)) == []


def test_il_se_tait_quand_l_exception_ne_nomme_aucun_fichier():
    """`raise FileNotFoundError("gh")` : on ne devine pas ce qu'elle visait."""
    assert _sections_du_hook(FileNotFoundError("gh introuvable")) == []


def test_il_se_tait_sur_un_chemin_hors_du_depot(tmp_path):
    """Un `tmp_path` : la CI ne l'aurait pas téléchargé davantage en local."""
    assert _sections_du_hook(_fichier_absent(tmp_path / "absent.json")) == []


# ---------------------------------------------------------------------------
# Deux cas de plus, sur le hook lui-même.
# ---------------------------------------------------------------------------

def test_il_se_tait_et_ne_casse_rien_si_tests_yml_est_illisible(monkeypatch):
    """`tests.yml` absent → `None`, silence, **aucune erreur de collecte**.

    Le hook s'exécute pour chaque test de la suite : une exception ici
    transformerait chaque échec en erreur, et masquerait sa cause.
    """
    monkeypatch.setattr(
        conftest, "WORKFLOW_TESTS",
        RACINE_DEPOT / ".github" / "workflows" / "tests-inexistant.yml")
    conftest._liste_blanche_sparse_checkout.cache_clear()

    assert conftest._liste_blanche_sparse_checkout() is None
    manquant = RACINE_DEPOT / HORS_LISTE / "fichier.json"
    assert _sections_du_hook(_fichier_absent(manquant)) == []


def test_il_ne_masque_jamais_l_echec_qu_il_commente(monkeypatch):
    """Même si l'analyse explose, le hook rend le rapport intact."""
    def _exploser(*_args, **_kwargs):
        raise RuntimeError("analyseur cassé")

    monkeypatch.setattr(conftest, "_chemin_du_fichier_absent", _exploser)
    manquant = RACINE_DEPOT / HORS_LISTE / "fichier.json"
    assert _sections_du_hook(_fichier_absent(manquant)) == []


def test_un_test_qui_passe_ne_fait_rien_lire():
    assert _sections_du_hook(None, failed=False) == []


# ---------------------------------------------------------------------------
# L'analyseur partagé : jamais une liste fausse.
# ---------------------------------------------------------------------------

def _workflow(tmp_path: Path, contenu: str) -> Path:
    chemin = tmp_path / "tests.yml"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def test_un_bloc_renomme_rend_none_et_pas_une_liste_devinee(tmp_path):
    """Le cas du renommage : ne rien trouver, plutôt que trouver n'importe quoi."""
    contenu = (
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          chemins-a-materialiser: |\n"
        "            docs\n"
        "            src\n"
        "      - name: Etape suivante\n"
        "        run: echo ok\n"
    )
    assert _outils_ci.lire_liste_blanche(_workflow(tmp_path, contenu)) is None


def test_un_bloc_en_notation_de_flot_rend_none(tmp_path):
    contenu = (
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          sparse-checkout: [docs, src]\n"
    )
    assert _outils_ci.lire_liste_blanche(_workflow(tmp_path, contenu)) is None


def test_un_bloc_vide_rend_none_et_n_avale_pas_la_cle_suivante(tmp_path):
    """LE piège de l'analyse par indentation. Si le bloc se vide, les lignes
    suivantes ne doivent pas devenir des entrées : une liste blanche inventée
    ferait taire le hook sur un vrai chemin hors liste, sans rien dire."""
    contenu = (
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          sparse-checkout: |\n"
        "          fetch-depth: 0\n"
        "\n"
        "      - name: Le corpus vivant reste hors du checkout (#473)\n"
        "        run: echo ok\n"
    )
    assert _outils_ci.lire_liste_blanche(_workflow(tmp_path, contenu)) is None


def test_un_bloc_reduit_a_des_commentaires_rend_none(tmp_path):
    contenu = (
        "        with:\n"
        "          sparse-checkout: |\n"
        "            # docs\n"
        "            # src\n"
        "      - name: Etape suivante\n"
    )
    assert _outils_ci.lire_liste_blanche(_workflow(tmp_path, contenu)) is None


def test_un_fichier_absent_rend_none_sans_lever(tmp_path):
    assert _outils_ci.lire_liste_blanche(tmp_path / "nulle-part.yml") is None


def test_un_bloc_normal_est_lu_et_s_arrete_a_la_cle_suivante(tmp_path):
    contenu = (
        "      - uses: actions/checkout@v5\n"
        "        with:\n"
        "          sparse-checkout: |\n"
        "            .github\n"
        "            # un commentaire\n"
        "            docs\n"
        "            raw_data/groupes_reels.json\n"
        "\n"
        "      - name: Etape suivante\n"
        "        run: echo ok\n"
    )
    lue = _outils_ci.lire_liste_blanche(_workflow(tmp_path, contenu))
    assert lue == frozenset({".github", "docs", "raw_data/groupes_reels.json"})


# ---------------------------------------------------------------------------
# Les deux autres fonctions internes, appelées directement.
# ---------------------------------------------------------------------------

def test_le_chemin_absent_est_relu_a_travers_la_chaine_des_causes():
    """Un `FileNotFoundError` enveloppé garde son chemin lisible."""
    manquant = RACINE_DEPOT / HORS_LISTE / "fichier.json"
    try:
        raise _fichier_absent(manquant)
    except FileNotFoundError as cause:
        enveloppe = RuntimeError("échec de chargement")
        enveloppe.__cause__ = cause

    assert conftest._chemin_du_fichier_absent(enveloppe) == str(manquant)
    assert conftest._chemin_du_fichier_absent(None) is None


def test_un_chemin_relatif_est_resolu_depuis_le_repertoire_courant(monkeypatch):
    """Le hook reçoit ce que l'exception porte, parfois un chemin relatif."""
    monkeypatch.chdir(RACINE_DEPOT)
    assert conftest._relatif_hors_liste_blanche(
        f"{HORS_LISTE}/fichier.json") == f"{HORS_LISTE}/fichier.json"
    assert conftest._relatif_hors_liste_blanche("docs/absent.md") is None
