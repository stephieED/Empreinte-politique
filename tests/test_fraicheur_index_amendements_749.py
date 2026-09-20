#!/usr/bin/env python3
"""
test_fraicheur_index_amendements_749.py — La rotation de clé hebdomadaire était
toute la politique de fraîcheur, et son propre repli la désamorçait (#749).

L'index de la 17e législature n'a pas été reconstruit pendant 18 jours. Aucun
des deux modules concernés n'avait tort :

- #249 a choisi la clé de cache hebdomadaire comme **seul** mécanisme de
  péremption, et le seuil de 7 jours de la §3d du gate est documenté comme
  « aligné sur la granularité de cache hebdomadaire » ;
- #250/#251 ne retéléchargent que si le cache est absent ou corrompu, et #253
  a **explicitement rejeté** le retéléchargement inconditionnel ;
- #424 a ajouté `restore-keys` sur la clé propre au job, pour une raison
  légitime : éviter un cache froid au changement de semaine.

Mis bout à bout, le cache n'est jamais absent, donc la reconstruction n'a plus
jamais lieu. Personne n'a rapproché les trois, et l'alarme prévue pour ça — le
warning du gate — sonnait à chaque run sans destinataire.

Ce que ces tests verrouillent :

- le prédicat de cache-hit est **nommé et partagé**, pour que le log du script
  et la décision de la fonction lourde ne puissent pas diverger — c'est un log
  faux (« Construction de l'index », 0,28 s, aucun téléchargement) qui a rendu
  la panne invisible ;
- la purge forcée ne vise **que les législatures actives** : re-matérialiser
  une figée chaque semaine coûterait la mémoire de
  `docs/decisions/oom-reconstruction-amendements-figees.md` pour une donnée qui
  ne change plus jamais ;
- le job CI passe le drapeau exactement quand la clé exacte de la semaine n'a
  pas été touchée, ce que seul `outputs.cache-hit` distingue d'un
  `restore-keys`.

Aucun test ne lit `pivot_data/`, `raw_data/profiles/`, `.cache/` ni le réseau.
"""

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import build_amendements_index  # noqa: E402
import candidate_profile  # noqa: E402
from build_amendements_index import build_all_amendements_index, purger_legislatures_actives  # noqa: E402
from candidate_profile import (  # noqa: E402
    amendements_index_en_cache_utilisable,
    purger_cache_amendements_legislature,
)

WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


def _cache_uid(tmp_path: Path, legislature: str, acteurs=("PA1", "PA2")) -> Path:
    """Un cache d'amendements au format `uid`, la forme servable."""
    cache = tmp_path / legislature
    index_dir = cache / candidate_profile.AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    index_dir.mkdir(parents=True)
    (cache / candidate_profile.AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME).write_text(
        json.dumps({"AMANR5L17PO000000B0000P0D": {"uid": "AMANR5L17PO000000B0000P0D"}}),
        encoding="utf-8",
    )
    for acteur in acteurs:
        (index_dir / f"{acteur}.json").write_text(
            json.dumps([{"uid": "AMANR5L17PO000000B0000P0D", "role_signataire": "auteur"}]),
            encoding="utf-8",
        )
    return cache


# ---------------------------------------------------------------------------
# 1. Le prédicat de cache-hit, nommé et partagé
# ---------------------------------------------------------------------------

def test_un_cache_au_format_uid_est_servable(tmp_path, monkeypatch):
    _cache_uid(tmp_path, "17")
    monkeypatch.setattr(candidate_profile, "AMENDEMENTS_CACHE_DIR", tmp_path)

    tranches = amendements_index_en_cache_utilisable("17")

    assert tranches is not None
    assert {p.stem for p in tranches} == {"PA1", "PA2"}


def test_un_cache_absent_n_est_pas_servable(tmp_path, monkeypatch):
    monkeypatch.setattr(candidate_profile, "AMENDEMENTS_CACHE_DIR", tmp_path)

    assert amendements_index_en_cache_utilisable("17") is None


def test_un_cache_au_format_herite_doit_etre_reconstruit(tmp_path, monkeypatch):
    """Références par `numero` : servi, il disparaîtrait à la lecture."""
    cache = _cache_uid(tmp_path, "17", acteurs=("PA1",))
    index_dir = cache / candidate_profile.AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    (index_dir / "PA1.json").write_text(
        json.dumps([{"numero": "42", "role_signataire": "auteur"}]), encoding="utf-8"
    )
    monkeypatch.setattr(candidate_profile, "AMENDEMENTS_CACHE_DIR", tmp_path)

    assert amendements_index_en_cache_utilisable("17") is None


# ---------------------------------------------------------------------------
# 2. Le log dit lequel des deux a eu lieu
# ---------------------------------------------------------------------------

def test_un_index_servi_par_le_cache_le_dit_et_n_appelle_pas_la_fonction_lourde(capsys):
    """Le défaut qui a caché la panne 18 jours : « Construction de l'index
    amendements, législature 17 » puis un compte d'acteurs, pour 0,28 s sans un
    octet téléchargé."""
    appels = []

    with (
        patch.object(build_amendements_index, "amendements_index_deja_figee", return_value=False),
        patch.object(build_amendements_index, "amendements_index_en_cache_utilisable",
                     return_value=[Path("PA1.json"), Path("PA2.json")]),
        patch.object(build_amendements_index, "_download_and_build_amendement_index",
                     side_effect=lambda leg: appels.append(leg) or {}),
    ):
        assert build_all_amendements_index() is True

    sortie = capsys.readouterr().out
    assert appels == [], "un cache servable ne doit déclencher aucune construction"
    assert "déjà en cache, non reconstruit" in sortie
    assert "Construction de l'index" not in sortie


def test_un_index_absent_du_cache_est_construit_et_le_dit(capsys):
    with (
        patch.object(build_amendements_index, "amendements_index_deja_figee", return_value=False),
        patch.object(build_amendements_index, "amendements_index_en_cache_utilisable",
                     return_value=None),
        patch.object(build_amendements_index, "_download_and_build_amendement_index",
                     return_value={"PA1": []}),
    ):
        assert build_all_amendements_index() is True

    sortie = capsys.readouterr().out
    assert "Construction de l'index" in sortie
    assert "déjà en cache" not in sortie


# ---------------------------------------------------------------------------
# 3. La purge ne vise que les législatures actives
# ---------------------------------------------------------------------------

def test_purger_supprime_le_cache_et_dit_s_il_y_avait_quelque_chose(tmp_path, monkeypatch):
    _cache_uid(tmp_path, "17")
    monkeypatch.setattr(candidate_profile, "AMENDEMENTS_CACHE_DIR", tmp_path)

    assert purger_cache_amendements_legislature("17") is True
    assert not (tmp_path / "17").exists()
    assert purger_cache_amendements_legislature("17") is False


def test_la_purge_forcee_epargne_les_legislatures_figees(tmp_path, monkeypatch, capsys):
    """Une figée n'a aucune fraîcheur à rafraîchir, et la re-matérialiser chaque
    semaine coûterait la mémoire de #oom-reconstruction-amendements-figees pour
    une archive dont le `Last-Modified` ne bouge plus (#249)."""
    for legislature in candidate_profile.AN_AMENDEMENTS_PATH:
        _cache_uid(tmp_path, legislature)
    monkeypatch.setattr(candidate_profile, "AMENDEMENTS_CACHE_DIR", tmp_path)

    purger_legislatures_actives()

    figees = candidate_profile.AN_AMENDEMENTS_LEGISLATURES_FIGEES
    actives = [leg for leg in candidate_profile.AN_AMENDEMENTS_PATH if leg not in figees]
    assert actives, "le test perdrait son objet si toutes les législatures étaient figées"
    for legislature in actives:
        assert not (tmp_path / legislature).exists(), legislature
    for legislature in figees:
        assert (tmp_path / legislature).is_dir(), legislature


# ---------------------------------------------------------------------------
# 4. Le job CI arme la purge sur le bon signal
# ---------------------------------------------------------------------------

def _job_amendements() -> str:
    """Le bloc textuel du job — sans PyYAML, absent de requirements.txt
    (même choix que `tests/test_ci_cache_paths.py`)."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index("\n  extract-amendements-an:")
    fin = texte.index("\n  ", texte.index("Upload artifact amendements AN"))
    return texte[debut:fin]


def test_le_cache_du_job_porte_un_id_et_garde_son_repli():
    """`restore-keys` RESTE : le retirer viderait le cache entier chaque
    semaine, figées comprises. C'est `cache-hit` qui apporte le signal manquant."""
    job = _job_amendements()

    assert "id: cache_amendements" in job
    assert "restore-keys:" in job
    assert "public-data-cache-amendements-${{ steps.week.outputs.week }}" in job


def test_la_reconstruction_est_armee_quand_la_cle_exacte_n_a_pas_ete_touchee():
    """`outputs.cache-hit` vaut 'true' sur la SEULE correspondance exacte de la
    clé primaire — pas sur un `restore-keys`. C'est le signal « nouvelle semaine
    ISO », et c'est lui qui manquait."""
    job = _job_amendements()

    assert "steps.cache_amendements.outputs.cache-hit" in job
    assert "--reconstruire-actives" in job
    assert re.search(r'if \[\[ "\$CLE_SEMAINE_TOUCHEE" != "true" \]\]', job), (
        "la purge doit être armée sur l'ABSENCE de correspondance exacte"
    )


def test_le_drapeau_existe_vraiment_dans_le_script():
    """Un workflow qui passerait un drapeau inconnu ferait échouer le job."""
    from build_amendements_index import main

    with (
        patch.object(build_amendements_index, "purger_legislatures_actives") as purge,
        patch.object(build_amendements_index, "build_all_amendements_index", return_value=True),
    ):
        assert main(["--reconstruire-actives"]) == 0
        assert purge.called
        purge.reset_mock()
        assert main([]) == 0
        assert not purge.called
