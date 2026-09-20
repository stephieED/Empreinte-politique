"""#505 — un index d'interventions incomplet ne doit jamais être mis en cache.

Pourquoi ce fichier existe. Jusqu'à #505, `.cache/questions_an` et
`.cache/syceron_an` n'étaient jamais partagés entre les shards : la clé de
cache de la semaine était écrite par un run qui ne les remplissait pas, chaque
shard reconstruisait donc son index, et un index tronqué mourait avec son
runner.

En rendant la clé sensible au mode, #505 fait exactement l'inverse : l'index
d'un shard sert à tous les autres, pour toute la semaine ISO. Le défaut
suivant devient donc structurel — un index construit sur une archive absente
serait servi à tout le monde comme s'il était complet.

Ce n'est pas une hypothèse. Mesuré le 20/08/2026 sur la législature 17 :
l'archive des questions écrites est tombée en `IncompleteRead`, et
`_build_acteur_questions_index` a quand même écrit son `index_par_acteur.json`
— 16,8 Mo, 2 611 questions issues des seules QG/QOSD. Le commentaire de
`fetch_questions_officielles` affirmait pourtant, depuis #498, que « l'index
par acteur n'est écrit en cache qu'une fois la législature entièrement lue ».
Encore une affirmation exacte à l'écriture, devenue fausse sans être relue.

Règle imposée ici : **collecte incomplète ⇒ pas de mise en cache**. L'index
partiel est rendu à l'appelant (le profil du candidat en cours n'a pas à être
puni de la panne), mais il ne survit pas au process. C'est §2.5 — une donnée
manquante reste manquante, elle ne devient pas un « 0 » mesuré.

Aucun réseau, aucun corpus : archives ZIP et XML sont fabriquées ici.
"""

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import patch

import candidate_profile as cp

LEG = "17"


# ---------------------------------------------------------------------------
# Doublures
# ---------------------------------------------------------------------------


def _zip_questions(uid: str, acteur_ref: str) -> bytes:
    """Une archive de questions officielles minimale mais réaliste."""
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


def _telechargement(echecs: set[str]):
    """Faux `download_with_watchdog` : écrit un ZIP valide, sauf pour `echecs`."""

    def faux(url, dest, **_):
        nom = Path(dest).name  # qe.zip / qg.zip / qosd.zip
        if nom in echecs:
            raise TimeoutError(f"IncompleteRead simulé sur {nom}")
        Path(dest).write_bytes(_zip_questions(f"{nom}-uid", "PA1234"))

    return faux


def _index_questions(tmp_path: Path, echecs: set[str]):
    cp._QUESTIONS_LOCKS.clear()
    with patch("candidate_profile.QUESTIONS_CACHE_DIR", tmp_path), patch(
        "candidate_profile.download_with_watchdog", _telechargement(echecs)
    ):
        index = cp._build_acteur_questions_index(LEG)
    return index, tmp_path / LEG / "index_par_acteur.json"


# ---------------------------------------------------------------------------
# Questions officielles (QE/QG/QOSD)
# ---------------------------------------------------------------------------


def test_index_questions_complet_est_mis_en_cache(tmp_path):
    """Le cas nominal : sans lui, le test suivant passerait même si l'index
    n'était plus jamais écrit."""
    index, chemin = _index_questions(tmp_path, echecs=set())
    assert index["PA1234"], "aucune question indexée — la doublure ne représente plus rien"
    assert len(index["PA1234"]) == 3, "les trois sous-types doivent être agrégés"
    assert chemin.is_file(), "un index complet doit être mis en cache"


def test_index_questions_partiel_n_est_pas_mis_en_cache(tmp_path):
    """Le défaut mesuré. Une seule des trois archives manque et l'index perd
    une part inconnue de son contenu — le mettre en cache le figerait pour
    toute la semaine sur tous les shards."""
    index, chemin = _index_questions(tmp_path, echecs={"qe.zip"})
    assert len(index["PA1234"]) == 2, "les deux archives lisibles doivent être rendues"
    assert not chemin.exists(), (
        "un index construit sans l'archive des questions écrites a été mis en "
        "cache : tout shard qui le restaurerait croirait la collecte faite."
    )


def test_index_questions_totalement_indisponible_n_est_pas_mis_en_cache(tmp_path):
    """Le cas le plus dangereux : un index VIDE mis en cache est indiscernable
    d'une législature réellement sans questions (§2.5)."""
    index, chemin = _index_questions(tmp_path, echecs={"qe.zip", "qg.zip", "qosd.zip"})
    assert index == {}
    assert not chemin.exists(), "un index vide par panne réseau a été mis en cache"


def test_archive_illisible_compte_aussi_comme_incomplete(tmp_path):
    """Le téléchargement peut réussir et l'archive être corrompue — même
    conséquence, donc même règle."""
    def faux(url, dest, **_):
        nom = Path(dest).name
        if nom == "qg.zip":
            Path(dest).write_bytes(b"ceci n'est pas un zip")
        else:
            Path(dest).write_bytes(_zip_questions(f"{nom}-uid", "PA1234"))

    cp._QUESTIONS_LOCKS.clear()
    with patch("candidate_profile.QUESTIONS_CACHE_DIR", tmp_path), patch(
        "candidate_profile.download_with_watchdog", faux
    ):
        index = cp._build_acteur_questions_index(LEG)
    assert len(index["PA1234"]) == 2
    assert not (tmp_path / LEG / "index_par_acteur.json").exists()


# ---------------------------------------------------------------------------
# Débats Syceron
# ---------------------------------------------------------------------------

# La réduction VERBATIM d'un compte rendu réel de la 17e législature — jamais un
# XML écrit à la main. #510 a été rendu invisible pendant des mois par deux
# fixtures inventées (`<id>PA…</id>`, `<titreStruct>` sous `<point>`, deux
# formes que l'Assemblée nationale ne publie pas) ; celle qui vivait ici en
# portait exactement les mêmes traits.
FIXTURE_SYCERON = Path(__file__).resolve().parent / "fixtures" / "syceron_reel_leg17.xml"
ACTEUR_FIXTURE = "PA847629"


def _servir_fixture_syceron(cache: Path) -> Path:
    xml_dir = cache / "xml" / "compteRendu"
    xml_dir.mkdir(parents=True)
    (xml_dir / "CRSANR5L17S2025O1N053.xml").write_bytes(FIXTURE_SYCERON.read_bytes())
    return xml_dir


def test_index_syceron_vide_par_archive_absente_n_est_pas_mis_en_cache(tmp_path, monkeypatch):
    """`iter_syceron_xml_files` rend un itérateur VIDE quand le téléchargement
    échoue : une fois l'index écrit, cette panne devient indiscernable d'une
    législature sans débats."""
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".cache" / "syceron_an" / LEG
    cache.mkdir(parents=True)
    cp._SYCERON_LOCKS.clear()
    cp._SYCERON_INDEX_NON_PUBLIE.clear()
    with patch("candidate_profile.iter_syceron_xml_files", lambda leg, **_: iter(())):
        index = cp._build_acteur_interventions_syceron_index(LEG)
    assert index == {}
    assert not (cache / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME).exists(), (
        "un index Syceron vide par archive absente a été mis en cache"
    )


def test_index_syceron_construit_est_publie_en_tranches(tmp_path, monkeypatch):
    """Le témoin. S'il tombait, le test ci-dessus ne prouverait plus rien.

    Il fixe aussi la FORME du cache (#510) : une tranche par acteur, publiée
    d'un seul `os.replace`. L'index plat n'est plus écrit — il était relu en
    entier à chaque candidat (1 664,8 Mio, 12,5 s sur les trois archives).
    """
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".cache" / "syceron_an" / LEG
    xml_dir = _servir_fixture_syceron(cache)

    cp._SYCERON_LOCKS.clear()
    cp._SYCERON_INDEX_NON_PUBLIE.clear()
    with patch(
        "candidate_profile.iter_syceron_xml_files",
        lambda leg, **_: iter(sorted(xml_dir.glob("*.xml"))),
    ):
        index = cp._build_acteur_interventions_syceron_index(LEG)
    assert index[ACTEUR_FIXTURE], "la fixture réelle ne produit plus d'intervention indexée"

    tranche = cache / cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME / f"{ACTEUR_FIXTURE}.json"
    assert tranche.is_file()
    assert json.loads(tranche.read_text(encoding="utf-8")) == index[ACTEUR_FIXTURE]
    assert not (cache / "index_par_acteur.json").exists(), (
        "l'index plat n'est plus écrit : il était relu entier à chaque candidat"
    )
    # Le répertoire temporaire de publication ne survit jamais au basculement.
    assert not (cache / f"{cp.SYCERON_INDEX_PAR_ACTEUR_DIRNAME}.partiel").exists()


def test_un_index_plat_herite_est_supprime_a_la_publication(tmp_path, monkeypatch):
    """Un index plat de 2 octets (`{}`) — l'état de #510 — traînant dans le cache
    de la semaine (#505) ne doit jamais rester lisible derrière les tranches."""
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".cache" / "syceron_an" / LEG
    xml_dir = _servir_fixture_syceron(cache)
    for nom in cp.SYCERON_INDEX_FILENAMES_HERITES:
        (cache / nom).write_text("{}", encoding="utf-8")

    cp._SYCERON_LOCKS.clear()
    cp._SYCERON_INDEX_NON_PUBLIE.clear()
    with patch(
        "candidate_profile.iter_syceron_xml_files",
        lambda leg, **_: iter(sorted(xml_dir.glob("*.xml"))),
    ):
        cp._build_acteur_interventions_syceron_index(LEG)

    for nom in cp.SYCERON_INDEX_FILENAMES_HERITES:
        assert not (cache / nom).exists(), f"{nom} hérité doit être supprimé"


def test_la_tranche_dun_acteur_absent_nest_pas_un_index_indisponible(tmp_path, monkeypatch):
    """Règle 5 : « cet acteur n'a pas parlé » et « index absent » ne sont pas le
    même fait, et ne se lisent pas pareil en aval."""
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".cache" / "syceron_an" / LEG
    xml_dir = _servir_fixture_syceron(cache)

    cp._SYCERON_LOCKS.clear()
    cp._SYCERON_INDEX_NON_PUBLIE.clear()
    # Index absent : None, l'appelant reconstruit.
    assert cp._read_cached_interventions_syceron_acteur(LEG, "PA999999") is None

    with patch(
        "candidate_profile.iter_syceron_xml_files",
        lambda leg, **_: iter(sorted(xml_dir.glob("*.xml"))),
    ):
        cp._build_acteur_interventions_syceron_index(LEG)

    # Index publié, acteur absent : liste vide, sans reconstruction.
    assert cp._read_cached_interventions_syceron_acteur(LEG, "PA999999") == []
    assert cp._read_cached_interventions_syceron_acteur(LEG, ACTEUR_FIXTURE)


# ---------------------------------------------------------------------------
# L'affirmation corrigée
# ---------------------------------------------------------------------------


def test_le_commentaire_de_fetch_questions_ne_ment_plus():
    """#498 avait écrit que l'index n'était mis en cache qu'une législature
    entièrement lue. Ce n'était vrai ni alors ni après. La phrase est corrigée
    dans le code ; ce test empêche qu'elle revienne telle quelle."""
    source = Path(cp.__file__).read_text(encoding="utf-8")
    assert (
        "l'index par acteur n'est écrit en cache qu'une fois la\n"
        "        # législature entièrement lue" not in source
    ), (
        "L'affirmation de #498 est de retour dans fetch_questions_officielles. "
        "Elle ne décrit le code que depuis #505, et seulement parce que "
        "_build_acteur_questions_index refuse désormais de mettre en cache un "
        "index incomplet."
    )
