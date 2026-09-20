"""Garde-fou partagé par toute la suite : **aucun test ne sort sur le réseau**.

AGENTS.md §3 l'exige depuis #473 — un test qui appelait réellement
`archive.nossenateurs.fr` coûtait 16 des 35 s d'un fichier. C'était jusqu'ici
une règle **auditée une fois**, pas une règle tenue : rien n'empêchait un test
neuf de rouvrir une socket. #488 l'a vérifié à ses dépens — une seule requête
ajoutée dans le chemin de `process_candidat` a fait passer
`test_generate_all_profiles.py` de 0,50 s à 13,4 s, sans qu'aucun test échoue.

La fixture ci-dessous coupe `requests` à sa couche la plus basse
(`Session.send`, par où passent `requests.get`, `requests.post` et toute
session construite ailleurs) et **échoue bruyamment** en nommant l'URL.

**La boucle locale reste ouverte** : 11 tests de `test_amendements_download_modes`
montent un `http.server` sur `127.0.0.1` pour éprouver la reprise par `Range`
sur un vrai socket. C'est une doublure, pas une source tierce — le critère est
« sortir de la machine », pas « parler HTTP ». Un test qui a besoin d'une
réponse d'un hôte distant fournit sa propre doublure, comme le reste de la
suite le fait déjà.

Le sparse-checkout du workflow de tests couvre l'autre moitié de la règle
(le corpus vivant est absent du disque en CI) ; celle-ci couvre le réseau.

Ce fichier en porte deux autres, sans rapport avec le premier :

- **les fichiers du dépôt qui bougent sous la suite** — le `.cache/` du poste
  (#721) et les `.json` de `raw_data/` qu'un run réécrit (#791). Le filtre est
  posé sur les **trois** portes d'ouverture (`builtins.open`, `io.open`,
  `Path.open`), parce qu'aucune n'attrape les deux autres ;
- le hook `pytest_runtest_makereport` de la fin du fichier, qui nomme la cause
  probable quand un test échoue sur un fichier que le sparse-checkout ne
  télécharge pas.

Chacun porte son pourquoi à l'endroit où il est écrit.
"""

import builtins
import io
import os
import sys
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
# `tests/` sur le chemin d'import **avant** `_outils_ci` : le seul analyseur du
# bloc `sparse-checkout:` du dépôt y vit, et un conftest ne peut pas importer un
# module de test. Poser le chemin ici plutôt que compter sur l'`--import-mode`
# de pytest fait que les tests qui importent le même module voient le même objet.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _outils_ci  # noqa: E402  (l'import dépend du sys.path ci-dessus)

HOTES_AUTORISES = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


class ReseauInterditDansLesTests(AssertionError):
    """Levée quand un test tente une requête HTTP vers un hôte distant
    (AGENTS.md §3, #473)."""


def _est_boucle_locale(url: str) -> bool:
    return (urlsplit(url).hostname or "").lower() in HOTES_AUTORISES


@pytest.fixture(autouse=True)
def _reseau_coupe(monkeypatch):
    envoyer_reel = requests.sessions.Session.send

    def _filtrer(self, request, **kwargs):
        url = getattr(request, "url", "") or ""
        if _est_boucle_locale(url):
            return envoyer_reel(self, request, **kwargs)
        raise ReseauInterditDansLesTests(
            f"Requête HTTP réelle vers {url or '?'} depuis un test. Aucun test ne "
            "doit sortir sur le réseau (AGENTS.md §3, #473) : remplace l'appel par "
            "une doublure, ou sers la réponse depuis 127.0.0.1."
        )

    monkeypatch.setattr(requests.sessions.Session, "send", _filtrer)


# ---------------------------------------------------------------------------
# Deuxième garde-fou : aucun test ne lit les FICHIERS DU DÉPÔT qui bougent
# sous lui — le cache du poste (#721) et les `.json` de `raw_data/` (#791).
# ---------------------------------------------------------------------------
#
# LE CACHE DU POSTE (#721). Les onze constantes de cache du dépôt valent
# `Path(".cache") / ...` — un chemin RELATIF au répertoire courant, donc la
# racine du dépôt quand pytest tourne en local. En CI, `tests.yml` fait un
# checkout partiel, `.cache/` n'existe pas, la lecture échoue et le repli
# s'applique. Sur un poste qui a déjà lancé une collecte, la même lecture
# RÉUSSIT et sert des données réelles à la place de la fixture.
#
# Mesuré le 02/09/2026 : six tests — les quatre de `test_budget_interventions`
# et deux de `test_candidate_profile` — rendaient **688** interventions là où
# leur fixture en attendait **1**. Ils patchaient le CONSTRUCTEUR
# (`_build_acteur_interventions_syceron_index`) mais pas la lecture du cache,
# qui passe avant lui. Verts en CI parce que la machine est vide, verts en local
# depuis #719 parce que le cache du poste est périmé donc rejeté : deux raisons
# accidentelles, aucune bonne.
#
# LES `.json` DE `raw_data/` (#791). Même piège, sur une troisième population.
# `raw_data/candidats.json`, `raw_data/correspondance_acteurs_an.json`,
# `raw_data/resolutions_candidats.json` sont RÉÉCRITS par chaque run de
# `generate-data.yml` et committés par le bot. Le run `34278343461` a ajouté
# dans la nuit l'entrée sourcée d'Asselineau : trois tests écrits le 08/09 sont
# passés au rouge le lendemain, en local seulement — le sparse-checkout de
# `tests.yml` ne matérialise pas ces fichiers, donc la CI ne les voit jamais.
#
# CE QUI RESTE LISIBLE, ET SEULEMENT AINSI. Deux `.json` de `raw_data/` sont des
# CONFIGURATIONS éditoriales committées à la main — `groupes_reels.json`,
# `gouvernements_reels.json` — et la suite porte des tests dont le SUJET est
# leur validité (`test_repository_groupes_reels_json_is_valid`). Les figer
# reviendrait à valider une copie, c'est-à-dire à désarmer le test. Ils restent
# donc lisibles, mais **jamais par accident** : le fichier de test le déclare
# par `pytest.mark.lit_reference_committee("raw_data/<fichier>.json")`, et le
# garde-fou n'accepte cette déclaration que si le chemin est couvert par le
# `sparse-checkout` de `tests.yml`. C'est la condition qui manquait : un fichier
# absent du checkout n'est pas lu par la CI, donc un test qui le lit ne tourne
# qu'ici, sur ce qu'un run a laissé.
#
# POURQUOI TROIS POINTS D'INTERCEPTION ET PAS UN. `monkeypatch.setattr(builtins,
# "open", ...)` n'attrape PAS `pathlib` : `Path.open()` appelle `io.open`, et
# `builtins.open` en est une AUTRE référence — patcher l'une laisse l'autre
# intacte (vérifié sur CPython 3.12). Mesuré le 10/09/2026 sur la suite
# complète : des 144 tests qui ouvrent un fichier du dépôt sous surveillance,
# **41** passent par `builtins.open` et **103** par `pathlib`. Le garde-fou de
# #721 avait donc le même trou depuis son écriture, et un test le traversait :
# `test_candidate_profile.py::test_download_and_build_amendement_index_disk_
# marker_from_different_run_is_ignored` lisait `.cache/amendements_an/17/
# failed_run_id` sans être arrêté.
#
# CE GARDE-FOU DIAGNOSTIQUE, IL NE REDIRIGE PAS. Réécrire les constantes vers un
# répertoire jetable a été essayé et cassait dix tests qui isolent déjà leur
# cache par `monkeypatch.chdir(tmp_path)` : leur `.cache` relatif suit le
# répertoire courant, et une constante rendue absolue le leur retire. L'idiome
# existant est bon ; ce qui manquait était de voir ceux qui ne l'appliquent pas.

#: Le cache réel du poste — celui qu'aucun test ne doit lire.
CACHE_DU_DEPOT = (Path(__file__).resolve().parents[1] / ".cache").resolve()

#: `raw_data/` du dépôt, et la seule branche que ce garde-fou laisse à un autre :
#: `raw_data/profiles/`, déjà couverte par le hook de diagnostic du bas de ce
#: fichier (elle est exclue du checkout EXPRÈS, #473, et le message à donner
#: n'est pas le même).
RAW_DATA_DU_DEPOT = (Path(__file__).resolve().parents[1] / "raw_data").resolve()
PROFILS_DU_DEPOT = RAW_DATA_DU_DEPOT / "profiles"

#: Le marqueur par lequel un fichier de test déclare lire une configuration
#: committée. Enregistré dans `pytest_configure` — le dépôt n'a pas de
#: `pytest.ini`, et un marqueur non déclaré ne serait qu'un avertissement.
MARQUEUR_REFERENCE = "lit_reference_committee"


class CacheDuPosteLuDansUnTest(AssertionError):
    """Levée quand un test ouvre un fichier du cache réel du dépôt (#721)."""


class RawDataDuDepotLuDansUnTest(AssertionError):
    """Levée quand un test ouvre un `.json` de `raw_data/` sans le déclarer (#791)."""


class ReferenceCommitteeHorsChecKout(AssertionError):
    """Levée quand un marqueur autorise un chemin que la CI ne télécharge pas (#791)."""


def _texte_du_chemin(fichier):
    """Le chemin sous forme de `str`, ou `None` si l'argument n'en porte pas.

    `open(3)` réouvre un descripteur : il n'y a rien à examiner.
    """
    if isinstance(fichier, int):
        return None
    texte = os.fspath(fichier) if hasattr(fichier, "__fspath__") else fichier
    if isinstance(texte, bytes):
        texte = texte.decode("utf-8", "replace")
    return texte if isinstance(texte, str) else None


def _resolu(texte):
    try:
        return Path(texte).resolve()
    except (OSError, ValueError):
        return None


def _sous_le_cache_du_depot(fichier) -> bool:
    """Vrai si `fichier` désigne quelque chose sous le `.cache/` du dépôt.

    Le test grossier sur la chaîne vient d'abord : `resolve()` sur chaque
    ouverture de fichier coûterait cher pour un cas qui ne se produit presque
    jamais.
    """
    texte = _texte_du_chemin(fichier)
    if texte is None or ".cache" not in texte:
        return False
    resolu = _resolu(texte)
    return resolu is not None and CACHE_DU_DEPOT in (resolu, *resolu.parents)


def _json_de_raw_data_du_depot(fichier):
    """Le chemin résolu si `fichier` est un `.json` de `raw_data/`, sinon `None`.

    `raw_data/profiles/` est rendu `None` : il a son propre diagnostic.
    """
    texte = _texte_du_chemin(fichier)
    if texte is None or "raw_data" not in texte or not texte.endswith(".json"):
        return None
    resolu = _resolu(texte)
    if resolu is None or RAW_DATA_DU_DEPOT not in resolu.parents:
        return None
    if PROFILS_DU_DEPOT in (resolu, *resolu.parents):
        return None
    return resolu


def _chemins_declares(item) -> frozenset:
    """Les chemins que les marqueurs du test autorisent, résolus.

    Chaque chemin doit être couvert par le `sparse-checkout` de `tests.yml` :
    sinon la CI ne le télécharge pas, le test ne tourne qu'en local, et la
    déclaration servirait à masquer #791 au lieu de le nommer. La liste blanche
    illisible (`None`) ne fait pas échouer — c'est le cas des tests qui la
    détournent eux-mêmes.
    """
    declares = []
    blanche = _liste_blanche_sparse_checkout()
    for marqueur in item.iter_markers(MARQUEUR_REFERENCE):
        for brut in marqueur.args:
            relatif = str(brut).strip("/")
            if blanche is not None and relatif not in blanche:
                raise ReferenceCommitteeHorsChecKout(
                    f"`{MARQUEUR_REFERENCE}(\"{relatif}\")` autorise un fichier "
                    "que le `sparse-checkout` de `.github/workflows/tests.yml` ne "
                    "télécharge pas : en CI ce test ne lirait rien, il ne tournerait "
                    "qu'en local, sur ce qu'un run y a laissé (#791). Inscrire le "
                    "chemin dans la liste blanche, ou figer une fixture."
                )
            declares.append((RACINE_DEPOT / relatif).resolve())
    return frozenset(declares)


def _message_raw_data(resolu) -> str:
    try:
        relatif = resolu.relative_to(RACINE_DEPOT).as_posix()
    except ValueError:  # pragma: no cover - `resolu` est sous la racine par construction
        relatif = str(resolu)
    return (
        f"Ce test lit {relatif} — le fichier RÉEL du dépôt, pas une fixture "
        "(#791). Chaque run de `generate-data.yml` réécrit les `.json` de "
        "`raw_data/`, et le `sparse-checkout` de `tests.yml` n'en matérialise "
        "qu'une partie : ce test passera ou échouera selon ce qu'un run a "
        "laissé, et la CI ne le verra pas. Lire une fixture figée sous "
        "`tests/fixtures/` (pour la table de correspondance, pointer "
        "`correspondance_acteurs_an.CHEMIN_PAR_DEFAUT` vers "
        "`tests/fixtures/correspondance_acteurs_an_extrait.json` et vider le "
        f"mémo aux deux bouts) ; si le SUJET du test est ce fichier committé, "
        f"le déclarer par `pytest.mark.{MARQUEUR_REFERENCE}(\"{relatif}\")` — "
        "ce qui exige qu'il soit dans le `sparse-checkout`."
    )


@pytest.fixture(autouse=True)
def _fichiers_du_depot_hors_de_portee(request, monkeypatch):
    """Coupe les trois portes d'ouverture de fichier, pour toute la suite.

    `builtins.open`, `io.open` et `pathlib.Path.open` : trois références, deux
    chemins d'appel réels, et aucun n'attrape les autres. La restauration est
    celle de `monkeypatch`, donc garantie même si le test lève.
    """
    autorises = _chemins_declares(request.node)

    def _verifier(fichier):
        if _sous_le_cache_du_depot(fichier):
            raise CacheDuPosteLuDansUnTest(
                f"Ce test lit {fichier} — le cache RÉEL du poste, pas sa fixture "
                "(#721). Il passera ou échouera selon ce qu'une collecte locale y "
                "a laissé, et la CI ne le verra jamais : son checkout est vide. "
                "Isole le cache, comme le fait `tests/test_syceron_acteur_ref.py` "
                "avec `monkeypatch.chdir(tmp_path)`, ou règle la constante de "
                "cache du module vers un `tmp_path`."
            )
        resolu = _json_de_raw_data_du_depot(fichier)
        if resolu is not None and resolu not in autorises:
            raise RawDataDuDepotLuDansUnTest(_message_raw_data(resolu))

    ouvrir_builtins = builtins.open
    ouvrir_io = io.open
    ouvrir_path = Path.open

    def _filtrer_builtins(fichier, *args, **kwargs):
        _verifier(fichier)
        return ouvrir_builtins(fichier, *args, **kwargs)

    def _filtrer_io(fichier, *args, **kwargs):
        _verifier(fichier)
        return ouvrir_io(fichier, *args, **kwargs)

    def _filtrer_path(self, *args, **kwargs):
        _verifier(self)
        return ouvrir_path(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", _filtrer_builtins)
    monkeypatch.setattr(io, "open", _filtrer_io)
    monkeypatch.setattr(Path, "open", _filtrer_path)


# ---------------------------------------------------------------------------
# Le corollaire du garde-fou : ce que les tests lisent à la place (#791).
# ---------------------------------------------------------------------------
#
# Refuser sans donner de remplaçant ferait échouer 46 tests qui ne demandaient
# rien au contenu réel : ils traversaient `charger_correspondance()` ou
# `declare_hors_an_par_identifiant()` sur leur chemin par DÉFAUT, sans jamais
# regarder ce qui en sortait. Les défauts sont donc réglés ici, pour toute la
# suite, sur des fixtures figées — un test qui veut une autre table continue de
# poser la sienne, comme `test_correspondance_acteurs_an.py` le fait déjà.
#
# LE PIÈGE DE #767, ET IL SE REFERME AUX DEUX BOUTS. `correspondance_acteurs_an`
# et `perimetre_candidats` mémoïsent par chemin dans un `dict` de module — pas
# un `lru_cache`, rien qui s'annule tout seul. Un mémo non vidé À L'ENTRÉE sert
# au test la table qu'un voisin a chargée ; non vidé À LA SORTIE, il la sert au
# suivant. Dans les deux cas, aucun fichier n'est rouvert, donc le garde-fou
# ci-dessus ne voit rien : c'est exactement le trou qu'il est censé fermer.

#: Table de correspondance figée — 13 entrées, déjà utilisée par quatre fichiers
#: de tests qui la nomment explicitement.
FIXTURE_CORRESPONDANCE = (
    Path(__file__).resolve().parent / "fixtures" / "correspondance_acteurs_an_extrait.json")

#: `raw_data/resolutions_candidats.json` n'existe sur AUCUN disque du dépôt : il
#: est écrit par le job de tête d'un run (#757) et n'est pas committé. Le défaut
#: de CLI pointe pourtant dessus, `declare_hors_an_par_identifiant` rattrape
#: l'`OSError` de l'absence — mais pas l'`AssertionError` du garde-fou. La
#: fixture rend le même verdict (« aucune résolution ») en le déclarant.
FIXTURE_RESOLUTIONS = (
    Path(__file__).resolve().parent / "fixtures" / "resolutions_candidats_neutre.json")

#: `raw_data/mandats_anterieurs.json` (#860) : une table relue que chaque
#: écriture de pivot de candidat relit. Servie figée, pour qu'aucun test qui
#: écrit un pivot ne dépende de ce que la table committée contient ce jour-là.
FIXTURE_MANDATS_ANTERIEURS = (
    Path(__file__).resolve().parent / "fixtures" / "mandats_anterieurs_extrait.json")

#: `(module, attribut, valeur)`. Réglés sur les modules **déjà importés** : le
#: conftest n'importe rien de `src/` pour lui-même, sans quoi il paierait
#: l'import de toute la chaîne à chaque session, y compris pour les tests qui
#: n'en touchent aucun.
_DEFAUTS_FIGES = (
    ("correspondance_acteurs_an", "CHEMIN_PAR_DEFAUT", FIXTURE_CORRESPONDANCE),
    ("build_correspondance_acteurs_an", "CHEMIN_PAR_DEFAUT", FIXTURE_CORRESPONDANCE),
    ("check_quality_gate", "CORRESPONDANCE_PAR_DEFAUT", FIXTURE_CORRESPONDANCE),
    ("perimetre_candidats", "RESOLUTIONS_PAR_DEFAUT", str(FIXTURE_RESOLUTIONS)),
    ("generate_all_profiles", "CHEMIN_TABLE_MANDATS_ANTERIEURS", FIXTURE_MANDATS_ANTERIEURS),
)

#: `(module, fonction)` — les mémos de module à vider aux DEUX bouts.
_MEMOS_A_VIDER = (
    ("correspondance_acteurs_an", "vider_memo"),
    ("perimetre_candidats", "vider_memo_resolutions"),
    ("generate_all_profiles", "vider_index_groupes_suspendus"),
    ("generate_all_profiles", "vider_table_mandats_anterieurs"),
)


def _vider_les_memos() -> None:
    for nom_module, nom_fonction in _MEMOS_A_VIDER:
        module = sys.modules.get(nom_module)
        vider = getattr(module, nom_fonction, None) if module else None
        if callable(vider):
            vider()


@pytest.fixture(autouse=True)
def _referentiels_figes(monkeypatch):
    """Les chemins par défaut des référentiels pointent vers des fixtures.

    Placée après le garde-fou dans l'ordre de définition, donc appliquée dans
    le même ordre : si un jour elle cessait de mordre, c'est le garde-fou qui
    le dirait, pas un test qui verdirait en silence.
    """
    _vider_les_memos()
    for nom_module, attribut, valeur in _DEFAUTS_FIGES:
        module = sys.modules.get(nom_module)
        if module is not None and hasattr(module, attribut):
            monkeypatch.setattr(module, attribut, valeur)
    yield
    _vider_les_memos()


def pytest_configure(config):
    """Déclare le marqueur — sans `pytest.ini`, il ne serait qu'un avertissement."""
    config.addinivalue_line(
        "markers",
        f"{MARQUEUR_REFERENCE}(chemin): ce fichier de test lit une configuration "
        "committée de `raw_data/`, et le chemin est dans le `sparse-checkout` de "
        "`tests.yml` (#791).",
    )


# ---------------------------------------------------------------------------
# Troisième garde-fou du fichier : diagnostiquer le piège du sparse-checkout.
# ---------------------------------------------------------------------------

#: Racine du dépôt et fichier de workflow : repris de `_outils_ci`, le seul
#: analyseur du bloc `sparse-checkout:`. Les réexporter ici garde le hook
#: lisible et laisse un test pointer `WORKFLOW_TESTS` ailleurs.
RACINE_DEPOT = _outils_ci.RACINE_DEPOT
WORKFLOW_TESTS = _outils_ci.WORKFLOW_TESTS

MESSAGE_HORS_LISTE_BLANCHE = (
    "Ce chemin n'est pas dans le `sparse-checkout` de "
    "`.github/workflows/tests.yml`. En CI, il n'est pas téléchargé — c'est "
    "probablement la cause, pas ton test. Ajouter son répertoire de premier "
    "niveau à la liste blanche."
)

#: Les deux exclusions volontaires (#473) : leur conseiller la liste blanche
#: serait un mauvais conseil, le garde-fou du workflow refuse leur présence.
CORPUS_HORS_CHECKOUT = ("pivot_data", "raw_data/profiles")

RAPPEL_CORPUS = (
    "Sauf que ce chemin-là est exclu **exprès** (#473, AGENTS.md §3b) et que le "
    "garde-fou du workflow refuse de le voir apparaître : ne pas l'inscrire dans "
    "la liste blanche — le test doit lire une fixture figée sous tests/fixtures/."
)


@lru_cache(maxsize=1)
def _liste_blanche_sparse_checkout() -> frozenset[str] | None:
    """Entrées du bloc `sparse-checkout: |` de `tests.yml`, ou `None`.

    Lue à la **première défaillance** qui la demande, jamais au chargement :
    une suite verte ne touche pas le fichier. `None` dès que quoi que ce soit
    cloche (fichier absent, bloc introuvable, bloc vide) — le hook se tait
    alors, plutôt que de transformer un échec de test en erreur de collecte.

    Piège récursif assumé : ce fichier est lui-même hors du disque du runner si
    `.github` quitte la liste blanche. Il y est (et `tests/test_ci_perimetre_
    sparse_checkout.py` le vérifie) ; s'il en sortait, ce hook deviendrait muet
    sans rien casser d'autre.

    L'analyse vit dans `tests/_outils_ci.py`, partagée avec les deux tests qui
    lisent le même bloc : ici, seule la mise en cache est locale.
    """
    return _outils_ci.lire_liste_blanche(WORKFLOW_TESTS)


def _chemin_du_fichier_absent(exception: BaseException | None) -> str | None:
    """Le chemin nommé par le premier `FileNotFoundError` de la chaîne.

    `None` si l'échec est autre chose, ou si l'erreur ne nomme aucun fichier
    (`raise FileNotFoundError("gh")` : on ne devine pas ce qu'elle voulait dire).
    """
    vues: set[int] = set()
    tete = exception
    while tete is not None and id(tete) not in vues:
        vues.add(id(tete))
        if isinstance(tete, FileNotFoundError) and tete.filename is not None:
            try:
                return os.fsdecode(tete.filename)
            except (TypeError, ValueError):
                return None
        tete = tete.__cause__ or tete.__context__
    return None


def _relatif_hors_liste_blanche(chemin: str) -> str | None:
    """Le chemin relatif à la racine s'il échappe à la liste blanche, sinon `None`.

    Trois raisons de se taire, toutes du côté « dans le doute, rien » :
    la liste est illisible ; le chemin sort du dépôt (un `tmp_path`, un fichier
    système — la CI ne l'aurait pas téléchargé davantage en local) ; une entrée
    de la liste le couvre, en préfixe de composants (`raw_data/groupes_reels.json`
    couvre ce seul fichier, `docs` couvre tout ce qui est dessous).
    """
    blanche = _liste_blanche_sparse_checkout()
    if not blanche:
        return None
    try:
        absolu = Path(chemin)
        if not absolu.is_absolute():
            absolu = Path.cwd() / absolu
        relatif = absolu.resolve().relative_to(RACINE_DEPOT)
    except (OSError, ValueError, RuntimeError):
        return None
    composants = relatif.parts
    if not composants:
        return None
    for entree in blanche:
        attendus = tuple(entree.split("/"))
        if composants[:len(attendus)] == attendus:
            return None
    return relatif.as_posix()


#: Titre de la section ajoutée au rapport d'échec.
TITRE_SECTION = "Chemin hors du sparse-checkout de la CI"


def _corps_du_diagnostic(relatif: str) -> str:
    """Le texte ajouté au rapport, pour un chemin relatif hors liste blanche.

    Séparé du hook pour être éprouvable sans provoquer d'échec réel
    (`tests/test_hook_diagnostic_sparse_checkout.py`).
    """
    corps = f"{relatif}\n\n{MESSAGE_HORS_LISTE_BLANCHE}"
    if any(relatif == exclu or relatif.startswith(exclu + "/")
           for exclu in CORPUS_HORS_CHECKOUT):
        corps = f"{corps}\n\n{RAPPEL_CORPUS}"
    return corps


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """Ajoute au rapport d'échec la cause probable : le fichier n'a jamais été téléchargé.

    LE PIÈGE. `.github/workflows/tests.yml` ne matérialise qu'une **liste
    blanche** de chemins (`sparse-checkout`), pour ne pas poser sur le runner
    les 8,4 Go de corpus (`raw_data/profiles/`, `pivot_data/`) — la suite passe
    de 4 min 30 à 41 s, et le critère « aucun test ne lit le corpus vivant »
    (#473) devient structurel au lieu d'audité une fois. Le prix : la liste
    s'écrit à la main, donc elle s'oublie. Un test qui lit un fichier hors liste
    **passe en local et échoue en CI**, sur un `FileNotFoundError` qui ne dit
    rien de la vraie cause. On cherche alors un bug dans le test, pendant que le
    fichier n'a simplement jamais été téléchargé.

    TROIS OCCURRENCES. #434, les 10 tests de `scripts/borner_historique_donnees.sh`,
    dès le premier run du workflow. #520, `.gitignore` lu par
    `test_ci_roster_unique_par_run.py` : suite verte en local, rouge sur le push
    vers `main` (run `32773016491`), découverte après fusion. Puis le 30/08/2026,
    `CLAUDE.md` lu par `test_instructions_agents.py`. Les deux dernières fois,
    l'avertissement était **déjà écrit deux lignes au-dessus** de la liste qu'on
    oubliait de compléter : une prose qui prévient ne prévient personne.

    POURQUOI DIAGNOSTIQUER PLUTÔT QUE PRÉVENIR. Prévenir demande de savoir ce que
    la suite lira, donc de lire tout le code de test. `test_ci_perimetre_sparse_
    checkout.py` le fait déjà pour les **littéraux** ancrés à la racine, et
    `test_instructions_agents.py` pour ses propres alias : c'est la moitié qui
    échoue en local, et elle reste la première ligne de défense. Pousser
    l'analyse plus loin — chemins construits, `os.path.join`, indirections —
    coûterait cher et produirait des faux positifs, *et un garde-fou qui crie
    pour rien finit désactivé*. Ce hook prend l'autre moitié : il ne cherche pas
    à empêcher la chute, il supprime les vingt minutes passées à chercher au
    mauvais endroit après coup. Son public est la personne qui lit un journal de
    CI rouge.

    CE QU'IL COÛTE. Rien sur un test qui passe : la première chose lue est
    `rapport.failed`. `tests.yml` n'est ouvert qu'à la première défaillance qui
    ressemble au piège, et une seule fois (`lru_cache`). Rien n'est jamais écrit
    en sortie standard ; le texte s'ajoute au rapport de l'échec, là où on le lit.

    CE QU'IL NE FAIT PAS. Il ne parle que si l'échec est bien un fichier absent
    **et** que le chemin manquant n'est effectivement couvert par aucune entrée
    de la liste blanche, lue depuis `tests.yml` et jamais recopiée ici. Toute
    autre situation — assertion ordinaire, chemin couvert, chemin hors dépôt,
    liste illisible — le laisse muet. En local le fichier existe : il ne se
    déclenche pas, et c'est le comportement attendu.

    CE QUI LE VERROUILLE. `tests/test_hook_diagnostic_sparse_checkout.py`, qui
    appelle les fonctions ci-dessus et pilote ce hook directement, sans faire
    échouer de test. Une aide au diagnostic qui cesse de fonctionner sans le
    dire est pire que pas d'aide : on finit par faire confiance à un silence
    qui ne veut plus rien dire.
    """
    rapport = yield
    try:
        if rapport.failed and call.excinfo is not None:
            chemin = _chemin_du_fichier_absent(call.excinfo.value)
            if chemin is not None:
                relatif = _relatif_hors_liste_blanche(chemin)
                if relatif is not None:
                    rapport.sections.append(
                        (TITRE_SECTION, _corps_du_diagnostic(relatif)))
    except Exception:
        pass  # un diagnostic ne masque jamais l'échec qu'il commente
    return rapport
