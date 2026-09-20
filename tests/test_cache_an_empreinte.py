"""#550 — la clé de cache AN doit porter la COMPLÉTUDE de son contenu.

Pourquoi ce fichier existe. Trois fois de suite, la même faute : une clé de
cache qui ne décrit pas ce qu'elle protège.

| Forme | Issue | Ce que la clé ignorait |
| --- | --- | --- |
| 1re | #424 | les répertoires réellement couverts |
| 2e | #505 | le mode d'extraction (`-interv`) |
| 3e | #550 | la complétude du contenu indexé |

Le 27/08/2026, run `33100214165`, les archives Syceron des 15e et 16e
législatures et les archives de questions des 14e et 15e sont tombées en
`IncompleteRead`. Les gardes de #505/#510 ont refusé de mettre ces index en
cache — c'est juste, un index vide figé serait pire. Mais le shard a quand même
sauvegardé son entrée sous `public-data-cache-an-2026-W35-interv`, avec pour
tout contenu d'interventions la 17e législature de débats et les 16e/17e de
questions. Deux heures plus tard, le run `33110395663` a fait un *exact key
hit* dessus ; `actions/cache` a sauté sa sauvegarde (« not saving cache »,
20:02:40, job 98652271090) ; les 7 shards porteurs ont réindexé les 15e et 16e
pour rien, 113 à 219 s chacun.

Ce que ce fichier impose n'est pas la correction mais **sa règle** : une
législature compte dans l'empreinte si et seulement si son index est
réellement sur le disque, tel que le `path:` du step de cache le capturera.
Les deux derniers tests le vérifient contre les VRAIS constructeurs d'index,
pas contre une doublure de l'empreinte : c'est le seul moyen que la garde de
#505 (« ne jamais mettre en cache un index incomplet ») et l'empreinte de #550
ne puissent pas diverger.

Aucun réseau, aucun corpus : archives ZIP et XML sont fabriquées ici, comme
dans `test_index_interventions_cache_partiel.py`.
"""

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import cache_an_empreinte as emp
import candidate_profile as cp

FIXTURE_SYCERON = Path(__file__).resolve().parent / "fixtures" / "syceron_reel_leg17.xml"
ACTEUR_FIXTURE = "PA847629"


# ---------------------------------------------------------------------------
# L'empreinte attendue est DÉRIVÉE du code, jamais recopiée
# ---------------------------------------------------------------------------


def test_l_empreinte_attendue_suit_les_constantes_du_code():
    """Recopiée ici, la liste des législatures deviendrait fausse à l'ouverture
    de la 18e : l'empreinte attendue ne serait plus jamais atteinte, donc plus
    aucun *exact key hit*, donc une sauvegarde de cache par shard."""
    assert emp.empreinte_attendue() == emp.empreinte(
        cp.SYCERON_AVAILABLE_LEGISLATURES, cp.AN_QUESTIONS_PATH
    )


def test_l_empreinte_attendue_couvre_les_deux_sources_du_mode_interventions():
    """Garde-fou du garde-fou : une empreinte vide passerait tous les tests
    ci-dessous sans rien décrire."""
    attendue = emp.empreinte_attendue()
    assert attendue.startswith("syc") and "-q" in attendue
    syceron, questions = attendue.split("-q")
    assert syceron[3:].split("."), "aucune législature Syceron dans l'empreinte"
    assert questions.split("."), "aucune législature de questions dans l'empreinte"


def test_une_legislature_de_plus_change_l_empreinte():
    """Le contrat même de la clé : deux contenus différents, deux clés
    différentes. Sans cela une entrée partielle percute une entrée complète —
    le défaut de #550."""
    with patch.object(cp, "SYCERON_AVAILABLE_LEGISLATURES", {"15", "16", "17", "18"}):
        assert emp.empreinte_attendue() != emp.empreinte(
            {"15", "16", "17"}, cp.AN_QUESTIONS_PATH
        )


def test_l_empreinte_est_stable_et_triee():
    """La clé doit être la même quel que soit l'ordre de parcours du disque :
    `iterdir()` ne garantit aucun ordre, et deux clés pour un même contenu
    doubleraient les entrées au lieu de les partager."""
    assert emp.empreinte(["17", "15", "16"], ["16", "14"]) == "syc15.16.17-q14.16"
    assert emp.empreinte([], []) == "syc-q"


# ---------------------------------------------------------------------------
# L'empreinte du disque décrit ce que le `path:` capturera
# ---------------------------------------------------------------------------


def _poser_index_syceron(racine: Path, legislature: str, vide: bool = False) -> None:
    index_dir = racine / "syceron_an" / legislature / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME
    index_dir.mkdir(parents=True)
    if not vide:
        (index_dir / "PA1234.json").write_text("[]", encoding="utf-8")


def _poser_index_questions(racine: Path, legislature: str) -> None:
    dossier = racine / "questions_an" / legislature
    dossier.mkdir(parents=True)
    (dossier / emp.QUESTIONS_INDEX_FILENAME).write_text("{}", encoding="utf-8")


def _empreinte_de(racine: Path) -> str:
    return emp.empreinte(
        emp.legislatures_syceron_indexees(racine / "syceron_an"),
        emp.legislatures_questions_indexees(racine / "questions_an"),
    )


def test_l_entree_fautive_du_27_08_ne_se_declare_plus_complete(tmp_path):
    """LE cas de #550, reconstruit à l'identique depuis le contenu réel de
    l'entrée `public-data-cache-an-2026-W35-interv` (114 481 867 o, écrite le
    27/08 à 17:55:27) : Syceron 17 seule, questions 16 et 17 seules."""
    _poser_index_syceron(tmp_path, "17")
    _poser_index_questions(tmp_path, "16")
    _poser_index_questions(tmp_path, "17")

    obtenue = _empreinte_de(tmp_path)
    assert obtenue == "syc17-q16.17"
    assert obtenue != emp.empreinte_attendue(), (
        "L'entrée partielle du 27/08 porte la même empreinte qu'une entrée "
        "complète : elle referait un exact key hit, et les 7 shards "
        "réindexeraient les 15e et 16e législatures pour rien (#550)."
    )


def test_un_cache_complet_porte_bien_l_empreinte_attendue(tmp_path):
    """Le témoin. Sans lui, le test ci-dessus passerait même si l'empreinte du
    disque ne coïncidait JAMAIS avec l'attendue — auquel cas plus aucune
    restauration ne ferait d'exact key hit et chaque shard sauvegarderait."""
    for legislature in cp.SYCERON_AVAILABLE_LEGISLATURES:
        _poser_index_syceron(tmp_path, legislature)
    for legislature in cp.AN_QUESTIONS_PATH:
        _poser_index_questions(tmp_path, legislature)
    assert _empreinte_de(tmp_path) == emp.empreinte_attendue()


def test_un_repertoire_d_index_vide_ne_compte_pas(tmp_path):
    """`_write_syceron_index_par_acteur` publie d'un seul `os.replace` et ne
    publie jamais d'index vide — mais l'empreinte décrit le DISQUE, pas le
    chemin qui l'a produit. Un répertoire vide laissé par un runner tué en
    plein archivage compterait sinon pour un index complet."""
    _poser_index_syceron(tmp_path, "17", vide=True)
    assert emp.legislatures_syceron_indexees(tmp_path / "syceron_an") == []


def test_un_cache_absent_donne_une_empreinte_vide(tmp_path):
    """Le cas du runner neuf : rien sur le disque, aucune erreur, une empreinte
    qui le dit."""
    assert _empreinte_de(tmp_path) == "syc-q"


def test_les_repertoires_hors_forme_sont_ignores(tmp_path):
    """`.cache/syceron_an/<législature>` ne contient que des numéros. Un
    répertoire de travail qui s'y glisserait ne doit pas entrer dans une clé de
    cache — c'est la même règle que `_syceron_shard_path_acteur`, qui refuse
    tout `acteurRef` hors forme plutôt que de l'assainir approximativement."""
    (tmp_path / "syceron_an" / "index_par_acteur.partiel").mkdir(parents=True)
    _poser_index_syceron(tmp_path, "17")
    assert emp.legislatures_syceron_indexees(tmp_path / "syceron_an") == ["17"]


# ---------------------------------------------------------------------------
# L'empreinte et la garde de #505 doivent dire la MÊME chose
# ---------------------------------------------------------------------------


def _zip_questions(uid: str, acteur_ref: str) -> bytes:
    """Une archive de questions officielles minimale mais réaliste (reprise de
    `test_index_interventions_cache_partiel.py`)."""
    question = {
        "question": {
            "uid": uid,
            "auteur": {"identite": {"acteurRef": acteur_ref}, "groupe": {"abrege": "GRP"}},
            "indexationAN": {"analyses": {"analyse": "Santé"}},
            "textesQuestion": {
                "texteQuestion": {
                    "texte": "Question de doublure.",
                    "infoJO": {"dateJO": "2024-05-01"},
                }
            },
            "minInt": {"developpe": "Ministère de doublure"},
        }
    }
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as zf:
        zf.writestr(f"{uid}.json", json.dumps(question))
    return tampon.getvalue()


def test_une_legislature_de_questions_refusee_au_cache_est_absente_de_l_empreinte(
    tmp_path, monkeypatch
):
    """LE point de jonction entre #505 et #550, éprouvé sur le vrai
    constructeur. Une des trois archives tombe : `_build_acteur_questions_index`
    refuse la mise en cache (#505) — et l'empreinte doit refuser de compter
    cette législature, sans quoi la clé annoncerait un contenu que l'entrée
    n'a pas."""
    monkeypatch.chdir(tmp_path)

    def faux_telechargement(url, dest, **_):
        nom = Path(dest).name
        if "/15/" in url and nom == "qe.zip":
            raise TimeoutError("IncompleteRead simulé")
        Path(dest).write_bytes(_zip_questions(f"{nom}-uid", "PA1234"))

    cp._QUESTIONS_LOCKS.clear()
    with patch("candidate_profile.download_with_watchdog", faux_telechargement):
        cp._build_acteur_questions_index("16")
        cp._build_acteur_questions_index("15")

    indexees = emp.legislatures_questions_indexees()
    assert "16" in indexees, "la législature complète n'a pas été mise en cache"
    assert "15" not in indexees, (
        "une législature de questions dont une archive a échoué compte dans "
        "l'empreinte : la clé déclarerait complète une entrée qui ne l'est pas "
        "(#505 + #550)."
    )


def test_une_legislature_syceron_refusee_au_cache_est_absente_de_l_empreinte(
    tmp_path, monkeypatch
):
    """Même jonction côté débats. `iter_syceron_xml_files` rend un itérateur
    VIDE quand l'archive est injoignable — c'est très exactement ce qui s'est
    produit le 27/08 sur les 15e et 16e législatures."""
    monkeypatch.chdir(tmp_path)
    xml_dir = tmp_path / ".cache" / "syceron_an" / "17" / "xml" / "compteRendu"
    xml_dir.mkdir(parents=True)
    (xml_dir / "CRSANR5L17S2025O1N053.xml").write_bytes(FIXTURE_SYCERON.read_bytes())

    def faux_iter(legislature, **_):
        return iter(sorted(xml_dir.glob("*.xml"))) if legislature == "17" else iter(())

    cp._SYCERON_LOCKS.clear()
    cp._SYCERON_INDEX_NON_PUBLIE.clear()
    with patch("candidate_profile.iter_syceron_xml_files", faux_iter):
        index_17 = cp._build_acteur_interventions_syceron_index("17")
        cp._build_acteur_interventions_syceron_index("16")

    assert index_17[ACTEUR_FIXTURE], "la fixture réelle ne produit plus d'intervention"
    indexees = emp.legislatures_syceron_indexees()
    assert indexees == ["17"], (
        f"empreinte Syceron = {indexees} : une législature dont l'archive était "
        "injoignable est comptée comme indexée (#550)."
    )
