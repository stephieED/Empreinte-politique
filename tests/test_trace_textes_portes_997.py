"""#997 — le chemin des textes portés cesse d'échouer en silence.

`_build_acteur_textes_portes_index` est **non fatal par construction**, et doit
le rester : une panne d'archive ne doit pas faire échouer un run dont tout le
reste est bon (#524). Mais « non fatal » avait dérivé en « silencieux ».

Quatre sorties rendaient `[]` sans un mot. La conséquence est la même pour les
quatre : la fusion conserve intégralement les entrées du run précédent, le
profil ne bouge pas d'un octet, et **aucune étape n'échoue**. Le correctif de
stade de #997 a traversé **trois runs** sans atteindre le corpus, et aucun log
ne permettait de dire lequel des quatre chemins avait été pris.

Ces tests verrouillent la trace, pas la valeur : ils vérifient qu'un run futur
pourra être diagnostiqué.
"""
from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import candidate_profile  # noqa: E402

FICHE_AN = "https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA345619"


def _isole(monkeypatch, tmp_path):
    """Cache neuf : aucun index du poste ne doit être relu (#791)."""
    monkeypatch.setattr(candidate_profile, "DOSSIERS_CACHE_DIR", tmp_path)


def test_aucune_archive_le_dit(monkeypatch, tmp_path, capsys):
    """LA sortie muette qui a coûté trois runs. Sans archive, l'index est vide,
    la collecte rend `[]`, et la fusion garde tout l'ancien."""
    _isole(monkeypatch, tmp_path)
    monkeypatch.setattr(candidate_profile, "ensure_dossiers_zips_downloaded", lambda: [])

    assert candidate_profile.fetch_textes_portes_officiels(FICHE_AN) == []

    err = capsys.readouterr().err
    assert "AUCUNE archive de dossiers disponible" in err
    assert "restent ceux du run précédent" in err


def test_une_url_sans_acteur_le_dit(monkeypatch, tmp_path, capsys):
    """Le profil déclare pourtant `textes_portes` COLLECTÉE, puisque le drapeau
    ne l'avait pas écartée : sans trace, les deux cas sont indistinguables."""
    _isole(monkeypatch, tmp_path)

    assert candidate_profile.fetch_textes_portes_officiels("https://exemple.invalide/x") == []

    assert "aucun acteur AN résolu" in capsys.readouterr().err


def test_un_acteur_absent_de_l_index_le_dit(monkeypatch, tmp_path, capsys):
    """Un acteur réel qu'aucun dossier ne cite : c'est un fait, mais il doit
    être lisible — sinon il ressemble à une panne."""
    _isole(monkeypatch, tmp_path)
    monkeypatch.setattr(candidate_profile, "ensure_dossiers_zips_downloaded", lambda: [])

    candidate_profile.fetch_textes_portes_officiels(FICHE_AN)

    err = capsys.readouterr().err
    assert "PA345619 absent de l'index" in err


def test_la_reconstruction_dit_ce_qu_elle_a_lu(monkeypatch, tmp_path, capsys):
    """Le cas nominal doit parler aussi : sans lui, l'absence de trace ne
    distingue pas « rien reconstruit » de « reconstruit sans rien trouver »."""
    _isole(monkeypatch, tmp_path)
    monkeypatch.setattr(candidate_profile, "ensure_dossiers_zips_downloaded",
                        lambda: [(17, tmp_path / "absente.zip")])
    monkeypatch.setattr(candidate_profile, "iter_dossiers_bruts", lambda archives: iter(()))

    candidate_profile._build_acteur_textes_portes_index()

    err = capsys.readouterr().err
    assert "index reconstruit depuis 1 archive(s) : 0 acteurs" in err
    assert "l'index est VIDE alors que les archives ont été lues" in err


def test_un_index_relu_du_cache_le_dit(monkeypatch, tmp_path, capsys):
    """La trace qui aurait montré #997 du premier coup : un index relu n'est
    PAS reconstruit, donc il porte le code qui l'a écrit, pas celui qui
    tourne."""
    _isole(monkeypatch, tmp_path)
    (tmp_path / "index_acteur_textes_v5.json").write_text('{"PA1": []}', encoding="utf-8")

    candidate_profile._build_acteur_textes_portes_index()

    err = capsys.readouterr().err
    assert "index relu depuis index_acteur_textes_v5.json" in err
    assert "AUCUNE reconstruction" in err


def test_un_cache_illisible_le_dit_et_reconstruit(monkeypatch, tmp_path, capsys):
    _isole(monkeypatch, tmp_path)
    (tmp_path / "index_acteur_textes_v5.json").write_text("{ pas du json", encoding="utf-8")
    monkeypatch.setattr(candidate_profile, "ensure_dossiers_zips_downloaded", lambda: [])

    candidate_profile._build_acteur_textes_portes_index()

    err = capsys.readouterr().err
    assert "illisible" in err
    assert "reconstruction" in err


def test_la_trace_ne_change_pas_le_contrat(monkeypatch, tmp_path):
    """La trace ne doit RIEN changer au contrat : sans archive, la collecte rend
    une LISTE VIDE, jamais une exception (#524) — un run dont tout le reste est
    bon ne doit pas mourir ici.

    Ce test a d'abord été écrit avec un `try/except` dont les deux branches
    passaient : il n'affirmait rien. Il porte maintenant sur la valeur rendue.
    """
    _isole(monkeypatch, tmp_path)
    monkeypatch.setattr(candidate_profile, "ensure_dossiers_zips_downloaded", lambda: [])

    resultat = candidate_profile.fetch_textes_portes_officiels(FICHE_AN)

    assert resultat == []
