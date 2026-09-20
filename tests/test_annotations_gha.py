"""Les échecs bloquants se lisent dans les ANNOTATIONS, pas seulement en log (#518).

## Ce que ces tests protègent

Le 24/08/2026, le run `32738726729` s'est arrêté avant commit sur
`audit_collecte_non_publiee.py`. Tout ce qu'un lecteur pouvait en tirer sans
télécharger le log du job : `Process completed with exit code 1`, puis un
`::error::COLLECTE_NON_PUBLIEE` qui **ne nommait personne**. Le rapport qui
nomme les slugs existait — dans l'onglet « Summary » et dans un artifact — mais
ni l'un ni l'autre n'apparaît dans la liste des annotations, et l'artifact
expire.

Même constat pour `generate_roster_candidats.py` : trois runs (21, 22, 24/08)
sont morts sur ses anomalies sans qu'aucune annotation ne dise laquelle
(ROADMAP.md, #516).

Une annotation n'est pas un `print` plus joli : c'est le seul canal qui survit
à la fermeture d'un run. Ces tests verrouillent donc les deux moitiés — elle est
émise **quand il faut**, et **silencieuse hors CI**, un script lancé à la main
n'ayant aucune raison d'imprimer des commandes de workflow.
"""

import json
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import gha
from audit_collecte_non_publiee import main as audit_main
from generate_roster_candidats import main as roster_main


def _annotations(capsys, niveau=None):
    """Les annotations émises, lues sur STDOUT — le seul flux que GitHub lit.

    Vérifier le flux fait partie du contrat : ce dépôt imprime ses anomalies sur
    stderr, et un `::error::` posté là s'affiche dans le log sans jamais créer
    d'annotation.

    `capsys.readouterr()` VIDE le tampon : un test qui appelle cette fonction
    deux fois (une par niveau) lirait la seconde fois sur du vide. D'où le
    filtrage en mémoire par l'appelant plutôt qu'un second appel — voir
    `_par_niveau`.
    """
    prefixe = f"::{niveau}::" if niveau else "::"
    return [l for l in capsys.readouterr().out.splitlines() if l.startswith(prefixe)]


def _par_niveau(capsys):
    """Toutes les annotations d'un coup, groupées par niveau (une seule lecture)."""
    groupes: dict[str, list[str]] = {niveau: [] for niveau in gha.NIVEAUX}
    for ligne in _annotations(capsys):
        niveau = ligne.split("::")[1]
        groupes.setdefault(niveau, []).append(ligne)
    return groupes


# ---------------------------------------------------------------------------
# gha.annoter
# ---------------------------------------------------------------------------

def test_annoter_est_silencieux_hors_ci(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    gha.annoter("error", "rien ne doit sortir")
    assert _annotations(capsys) == []


def test_annoter_aplatit_le_message(monkeypatch, capsys):
    """Une commande de workflow s'arrête au premier saut de ligne : non aplati,
    un message multi-lignes publie sa première ligne et déverse le reste."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    gha.annoter("warning", "deux\nlignes\r\net demie")
    assert _annotations(capsys) == ["::warning::deux lignes et demie"]


def test_annoter_refuse_un_niveau_inconnu(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    with pytest.raises(ValueError):
        gha.annoter("critical", "niveau inexistant côté GitHub")


# ---------------------------------------------------------------------------
# generate_roster_candidats : chaque anomalie est nommée
# ---------------------------------------------------------------------------

_GROUPE_LR_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}


def _config(tmp_path, groupes):
    chemin = tmp_path / "groupes.json"
    chemin.write_text(json.dumps({"groupes": groupes}), encoding="utf-8")
    return chemin


def test_un_fetch_en_echec_est_annote_et_nomme_la_cle(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: (_ for _ in ()).throw(requests.Timeout("Read timed out")),
    )

    rc = roster_main(["--config", str(_config(tmp_path, [_GROUPE_LR_AN])),
                      "--out", str(tmp_path / "roster.json")])

    assert rc == 1
    erreurs = _annotations(capsys, "error")
    assert any("deputes" in e for e in erreurs), erreurs
    assert any("ROSTER_INCOMPLET" in e for e in erreurs), erreurs


def test_un_groupe_a_zero_membre_est_annote_et_nomme_le_groupe(tmp_path, monkeypatch, capsys):
    """Le sigle renommé en amont — l'anomalie qu'un test de vacuité ne voit pas."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: [{"slug": "bob", "nom": "Bob", "groupe_sigle": "AUTRE"}],
    )

    rc = roster_main(["--config", str(_config(tmp_path, [_GROUPE_LR_AN])),
                      "--out", str(tmp_path / "roster.json")])

    assert rc == 1
    assert any("AN:LR" in e for e in _annotations(capsys, "error"))


def test_un_roster_complet_n_annote_rien(tmp_path, monkeypatch, capsys):
    """Une annotation par run sain ferait de l'onglet un bruit de fond."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: [{"slug": "alice", "nom": "Alice", "groupe_sigle": "LR"}],
    )

    rc = roster_main(["--config", str(_config(tmp_path, [_GROUPE_LR_AN])),
                      "--out", str(tmp_path / "roster.json")])

    assert rc == 0
    assert _annotations(capsys) == []


def test_l_ecriture_forcee_reste_annotee_en_warning(tmp_path, monkeypatch, capsys):
    """`--autoriser-roster-incomplet` publie une composition non mesurée : le run
    continue, donc plus rien d'autre ne le dira."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda *a, **k: [{"slug": "bob", "nom": "Bob", "groupe_sigle": "AUTRE"}],
    )

    rc = roster_main(["--config", str(_config(tmp_path, [_GROUPE_LR_AN])),
                      "--out", str(tmp_path / "roster.json"),
                      "--autoriser-roster-incomplet"])

    assert rc == 0
    assert any("ROSTER_INCOMPLET" in a for a in _annotations(capsys, "warning"))


# ---------------------------------------------------------------------------
# audit_collecte_non_publiee : l'annotation NOMME les slugs
# ---------------------------------------------------------------------------

def _corpus(tmp_path, bruts, pivots):
    raw = tmp_path / "raw"
    piv = tmp_path / "pivot"
    raw.mkdir()
    piv.mkdir()
    for slug in bruts:
        (raw / f"{slug}.json").write_text("{}", encoding="utf-8")
    for slug in pivots:
        (piv / f"{slug}.pivot.json").write_text("{}", encoding="utf-8")
    return raw, piv


def test_les_slugs_non_publies_partent_en_annotation(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw, piv = _corpus(tmp_path, ["alice", "bob"], ["alice"])

    rc = audit_main(["--raw-dir", str(raw), "--pivot-dir", str(piv)])

    assert rc == 1
    erreurs = _annotations(capsys, "error")
    assert len(erreurs) == 1, erreurs
    assert "bob" in erreurs[0]
    assert "COLLECTE_NON_PUBLIEE" in erreurs[0]


def test_l_annotation_est_plafonnee_et_annonce_le_reste(tmp_path, monkeypatch, capsys):
    """543 annotations identiques noieraient l'onglet au lieu de le renseigner."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    bruts = [f"membre-{i:03d}" for i in range(30)]
    raw, piv = _corpus(tmp_path, bruts, [])

    rc = audit_main(["--raw-dir", str(raw), "--pivot-dir", str(piv)])

    assert rc == 1
    erreur = _annotations(capsys, "error")[0]
    assert "+10" in erreur, erreur
    assert "membre-000" in erreur


def test_un_corpus_publie_n_annote_rien(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw, piv = _corpus(tmp_path, ["alice"], ["alice"])

    rc = audit_main(["--raw-dir", str(raw), "--pivot-dir", str(piv)])

    assert rc == 0
    assert _annotations(capsys) == []


def test_la_tolerance_degrade_l_annotation_sans_la_supprimer(tmp_path, monkeypatch, capsys):
    """Toléré n'est pas résolu : le run commite, donc l'écart doit rester lisible."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw, piv = _corpus(tmp_path, ["alice", "bob"], ["alice"])

    rc = audit_main(["--raw-dir", str(raw), "--pivot-dir", str(piv),
                     "--tolerer-non-publies"])

    assert rc == 0
    par_niveau = _par_niveau(capsys)
    assert par_niveau["error"] == []
    assert any("bob" in a for a in par_niveau["warning"])


def test_un_repertoire_absent_est_annote(tmp_path, monkeypatch, capsys):
    """« Rien n'a été rapproché » n'est pas « aucun écart » — le contrôle
    doit le dire là où on le lit."""
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    raw, piv = _corpus(tmp_path, ["alice"], ["alice"])

    rc = audit_main(["--raw-dir", str(tmp_path / "absent"), "--pivot-dir", str(piv)])

    assert rc == 1
    assert any("absent" in e for e in _annotations(capsys, "error"))
