"""Tests de `audit_diff_profils.py`.

Ce script est le garde-fou d'une régénération `--no-merge` : il détecte ce que
l'abandon de la fusion additive a fait perdre. Ses tests doivent donc surtout
prouver qu'il **détecte** — un comparateur qui ne signale rien est pire
qu'aucun comparateur, puisqu'il donne une fausse assurance.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from audit_diff_profils import (
    lire_profils_git,
    CHAMPS_HAUSSE_ATTENDUE,
    CHAMPS_STABLES,
    comparer,
    generate_markdown_report,
    lire_profils_disque,
)


def _profil(**compte) -> dict:
    return {c: [{"x": i} for i in range(n)] for c, n in compte.items()}


def _releve(**compte) -> dict:
    """Relevé d'un profil : longueurs de listes, aucun scalaire surveillé.

    Depuis #470 un relevé porte deux espaces de noms — les listes et les
    scalaires — pour qu'un champ nommé `votes` ne puisse pas entrer en
    collision avec un scalaire du même nom."""
    from audit_diff_profils import TOUS_CHAMPS
    return {"listes": {c: compte.get(c, 0) for c in TOUS_CHAMPS},
            "scalaires": {}, "lu": True}


# ---------------------------------------------------------------------------
# Détection des pertes
# ---------------------------------------------------------------------------

def test_perte_sur_champ_stable_est_signalee():
    r = comparer({"a.json": _releve(votes=100)}, {"a.json": _releve(votes=90)})
    assert len(r["pertes_sur_champs_stables"]) == 1
    p = r["pertes_sur_champs_stables"][0]
    assert (p["champ"], p["avant"], p["apres"]) == ("votes", 100, 90)


def test_profil_entierement_disparu_est_une_perte():
    """Le pire cas : un profil que la régénération n'a pas produit."""
    r = comparer({"a.json": _releve(votes=100)}, {})
    assert len(r["pertes_sur_champs_stables"]) == 1
    assert r["pertes_sur_champs_stables"][0]["champ"] == "(fichier entier)"


def test_baisse_amendements_signalee_mais_pas_bloquante():
    """La correction de clé de #440 fait croître les amendements ; une baisse
    reste anormale, mais elle n'a pas le même statut qu'une perte de votes."""
    r = comparer({"a.json": _releve(amendements=100)}, {"a.json": _releve(amendements=40)})
    assert r["pertes"], "la baisse doit être relevée"
    assert not r["pertes_sur_champs_stables"], "mais pas comme perte bloquante"


def test_hausse_amendements_nest_pas_une_perte():
    r = comparer({"a.json": _releve(amendements=100)}, {"a.json": _releve(amendements=700)})
    assert not r["pertes"]
    assert len(r["gains"]) == 1


# ---------------------------------------------------------------------------
# Le piège que ce script existe pour éviter
# ---------------------------------------------------------------------------

def test_gain_global_ne_masque_pas_une_perte_individuelle():
    """LE cas d'usage. Après #440 les amendements explosent ; si la comparaison
    se faisait en agrégat, une perte de votes sur un profil passerait
    inaperçue derrière ce gain."""
    avant = {
        "a.json": _releve(votes=1000, amendements=100),
        "b.json": _releve(votes=1000, amendements=100),
    }
    apres = {
        "a.json": _releve(votes=1000, amendements=5000),   # gros gain
        "b.json": _releve(votes=200, amendements=5000),    # perte cachée
    }
    r = comparer(avant, apres)

    total_avant = sum(r["totaux_avant"].values())
    total_apres = sum(r["totaux_apres"].values())
    assert total_apres > total_avant, "en agrégat, tout semble en hausse"

    assert len(r["pertes_sur_champs_stables"]) == 1
    assert r["pertes_sur_champs_stables"][0]["fichier"] == "b.json"


def test_champ_absent_equivaut_a_liste_vide():
    """Un champ absent et une liste vide décrivent le même fait : le profil ne
    porte aucune entrée. Les distinguer produirait de fausses alertes."""
    r = comparer({"a.json": _releve()}, {"a.json": _releve()})
    assert not r["pertes"] and not r["gains"]


def test_amendements_hors_des_champs_stables():
    """Garde-fou de la classification elle-même : si `amendements` rejoignait
    les champs stables, toute régénération après #440 serait bloquée."""
    assert "amendements" in CHAMPS_HAUSSE_ATTENDUE
    assert "amendements" not in CHAMPS_STABLES
    assert "votes" in CHAMPS_STABLES


# ---------------------------------------------------------------------------
# Lecture disque et rapport
# ---------------------------------------------------------------------------

def test_lecture_disque_compte_les_entrees(tmp_path):
    (tmp_path / "a.json").write_text(
        json.dumps(_profil(votes=3, amendements=5)), encoding="utf-8")
    releve = lire_profils_disque(tmp_path)
    assert releve["a.json"]["listes"]["votes"] == 3
    assert releve["a.json"]["listes"]["amendements"] == 5


def test_lecture_disque_ignore_un_json_illisible(tmp_path):
    (tmp_path / "ok.json").write_text(json.dumps(_profil(votes=1)), encoding="utf-8")
    (tmp_path / "casse.json").write_text("{ pas du json", encoding="utf-8")
    releve = lire_profils_disque(tmp_path)
    assert set(releve) == {"ok.json"}


def test_rapport_dit_explicitement_quand_rien_nest_perdu():
    md = generate_markdown_report(
        comparer({"a.json": _releve(votes=5)}, {"a.json": _releve(votes=5)}), "origin/main")
    assert "Aucune" in md


def test_rapport_avertit_que_les_totaux_ne_suffisent_pas():
    """L'avertissement est le cœur du rapport : sans lui, un lecteur pressé
    conclurait du tableau des totaux."""
    md = generate_markdown_report(
        comparer({"a.json": _releve(votes=5)}, {"a.json": _releve(votes=5)}), "origin/main")
    assert "Les totaux ne suffisent pas" in md


# ---------------------------------------------------------------------------
# lire_profils_git — lecture EN FLUX (#460)
#
# `git cat-file --batch` était lu avec `capture_output=True`, donc la totalité
# des profils était bufferisée avant qu'une seule entrée ne soit comptée :
# 3,2 Gio de RSS sur les 209 profils du 19/08/2026, et un process tué par
# l'OOM killer. À 752 profils ce serait ~11 Go — un échec certain en CI, pour
# un script dont tout l'intérêt est de tourner AVANT le commit.
#
# En flux : 236 Mio, soit −93 %. La mémoire ne dépend plus que du plus gros
# blob, pas du corpus.
# ---------------------------------------------------------------------------

def _depot_avec_profils(tmp_path: Path, profils: dict) -> Path:
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    rep = tmp_path / "pivot_data" / "profiles"
    rep.mkdir(parents=True)
    for nom, contenu in profils.items():
        (rep / nom).write_text(json.dumps(contenu, ensure_ascii=False), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "profils"], cwd=tmp_path, check=True)
    return tmp_path


def test_lecture_git_compte_chaque_profil(tmp_path, monkeypatch):
    depot = _depot_avec_profils(tmp_path, {
        "alice.pivot.json": {"votes": [1, 2, 3], "amendements": [1]},
        "bob.pivot.json": {"votes": [1], "mandats": [1, 2]},
    })
    monkeypatch.chdir(depot)

    releve = lire_profils_git("HEAD", "pivot_data/profiles")

    assert releve["alice.pivot.json"]["listes"]["votes"] == 3
    assert releve["alice.pivot.json"]["listes"]["amendements"] == 1
    assert releve["bob.pivot.json"]["listes"]["mandats"] == 2
    assert releve["bob.pivot.json"]["listes"]["interventions"] == 0


def test_lecture_git_reste_correcte_sur_un_grand_nombre_de_profils(tmp_path, monkeypatch):
    """La lecture en flux entrelace écriture des requêtes et lecture des blobs :
    un décalage d'un octet dans le protocole `--batch` décalerait TOUS les
    profils suivants, et le contrôle rendrait des comptes faux sans rien
    signaler. C'est le risque propre à cette réécriture."""
    profils = {
        f"membre-{i:03d}.pivot.json": {"votes": list(range(i)), "mandats": [1]}
        for i in range(60)
    }
    depot = _depot_avec_profils(tmp_path, profils)
    monkeypatch.chdir(depot)

    releve = lire_profils_git("HEAD", "pivot_data/profiles")

    assert len(releve) == 60
    for i in range(60):
        assert releve[f"membre-{i:03d}.pivot.json"]["listes"]["votes"] == i, i


def test_lecture_git_supporte_des_profils_de_tailles_tres_inegales(tmp_path, monkeypatch):
    """Le corpus réel va de quelques Ko à 26 Mo. Un blob volumineux ne doit ni
    tronquer la lecture, ni désynchroniser les suivants."""
    depot = _depot_avec_profils(tmp_path, {
        "petit.pivot.json": {"votes": [1]},
        "gros.pivot.json": {"votes": [{"x": "y" * 200} for _ in range(2000)]},
        "apres.pivot.json": {"votes": [1, 2]},
    })
    monkeypatch.chdir(depot)

    releve = lire_profils_git("HEAD", "pivot_data/profiles")

    assert releve["petit.pivot.json"]["listes"]["votes"] == 1
    assert releve["gros.pivot.json"]["listes"]["votes"] == 2000
    assert releve["apres.pivot.json"]["listes"]["votes"] == 2


def test_lecture_git_ignore_un_json_illisible_sans_desynchroniser(tmp_path, monkeypatch):
    """Un profil corrompu doit être sauté, et les suivants rester justes."""
    depot = _depot_avec_profils(tmp_path, {"alice.pivot.json": {"votes": [1]}})
    (depot / "pivot_data" / "profiles" / "casse.pivot.json").write_text("{ pas du json", encoding="utf-8")
    (depot / "pivot_data" / "profiles" / "zoe.pivot.json").write_text(
        json.dumps({"votes": [1, 2, 3]}), encoding="utf-8"
    )
    import subprocess
    subprocess.run(["git", "add", "-A"], cwd=depot, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "ajout"], cwd=depot, check=True)
    monkeypatch.chdir(depot)

    releve = lire_profils_git("HEAD", "pivot_data/profiles")

    assert "casse.pivot.json" not in releve
    assert releve["zoe.pivot.json"]["listes"]["votes"] == 3


def test_lecture_git_chemin_absent_de_la_reference_echoue_clairement(tmp_path, monkeypatch):
    import pytest
    depot = _depot_avec_profils(tmp_path, {"alice.pivot.json": {"votes": [1]}})
    monkeypatch.chdir(depot)

    with pytest.raises(SystemExit) as exc:
        lire_profils_git("HEAD", "pivot_data/inexistant")

    assert "--ref-dir" in str(exc.value)
