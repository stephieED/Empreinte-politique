"""Migration de `raw_data/profiles` vers la forme partitionnée (#580).

Ce que ces tests exigent du script de migration :

  - il **refuse de perdre** — nombre d'amendements et multi-ensemble des `uid`
    comparés avant/après, sur chaque profil ;
  - il est **idempotent** — relancé sur un corpus déjà migré, il ne réécrit
    rien et rend la même empreinte de corpus ;
  - il **ne touche à rien sans `--apply`** ;
  - une découpe qui perdrait quoi que ce soit **restaure l'original** et
    interrompt la migration, plutôt que de propager le défaut aux 480 autres.
"""

import json
from collections import Counter

import pytest

import migrer_profils_partitionnes_580 as migration
from profil_brut import CLE_MANIFESTE, CLE_PARTITIONNEE, charger_profil_brut, est_partitionne

from test_profil_brut_partition_580 import GROUPE, INTERFOLIE, profil_doublure


def _ecrire_monolithique(dossier, slug, profil):
    profil = dict(profil, slug=slug)
    (dossier / f"{slug}.json").write_text(
        json.dumps(profil, ensure_ascii=False), encoding="utf-8"
    )
    return profil


@pytest.fixture
def corpus(tmp_path):
    dossier = tmp_path / "profiles"
    dossier.mkdir()
    attendus = {
        "aline": _ecrire_monolithique(dossier, "aline", profil_doublure(GROUPE)),
        "boris": _ecrire_monolithique(dossier, "boris", profil_doublure(INTERFOLIE)),
        "chloe": _ecrire_monolithique(dossier, "chloe", profil_doublure([])),
    }
    # Un fichier de service : il ne doit jamais être pris pour un profil.
    (dossier / ".generation_checkpoint.json").write_text("{}", encoding="utf-8")
    return dossier, attendus


def test_simulation_n_ecrit_rien(corpus):
    dossier, attendus = corpus
    avant = {p.name: p.read_bytes() for p in dossier.glob("*.json")}

    rapport = migration.migrer(dossier, ecrire=False)

    assert rapport["nb_profils"] == 3
    assert rapport["par_etat"] == {"a_migrer": 2, "sans_amendement": 1}
    assert {p.name: p.read_bytes() for p in dossier.glob("*.json")} == avant
    assert not any(p.is_dir() for p in dossier.iterdir())


def test_migration_preserve_amendements_et_uid(corpus):
    dossier, attendus = corpus
    a_blanc = migration.migrer(dossier, ecrire=False)

    rapport = migration.migrer(dossier, ecrire=True)

    assert rapport["par_etat"] == {"migre": 2, "sans_amendement": 1}
    # L'empreinte du corpus ne bouge pas entre le run à blanc et le run réel :
    # c'est la preuve, en un chiffre, qu'aucun contenu n'a changé.
    assert rapport["empreinte_corpus"] == a_blanc["empreinte_corpus"]
    assert rapport["total_amendements"] == a_blanc["total_amendements"]

    for slug, profil in attendus.items():
        relu = charger_profil_brut(dossier / f"{slug}.json")
        assert relu == profil
        assert Counter(a["uid"] for a in relu.get(CLE_PARTITIONNEE) or []) == Counter(
            a["uid"] for a in profil.get(CLE_PARTITIONNEE) or []
        )


def test_migration_est_idempotente(corpus):
    dossier, _ = corpus
    premier = migration.migrer(dossier, ecrire=True)
    empreintes = {p.name: p.read_bytes() for p in dossier.rglob("*.json")}

    second = migration.migrer(dossier, ecrire=True)

    assert second["par_etat"] == {"deja_partitionne": 2, "sans_amendement": 1}
    assert second["empreinte_corpus"] == premier["empreinte_corpus"]
    assert {p.name: p.read_bytes() for p in dossier.rglob("*.json")} == empreintes


def test_profil_sans_amendement_reste_monolithique(corpus):
    """Un profil qui n'a rien à ranger ne gagne ni manifeste ni répertoire :
    la partition est un remède au volume, pas une cérémonie."""
    dossier, _ = corpus
    migration.migrer(dossier, ecrire=True)

    socle = json.loads((dossier / "chloe.json").read_text(encoding="utf-8"))
    assert CLE_MANIFESTE not in socle
    assert not est_partitionne(socle)
    assert not (dossier / "chloe").exists()


def test_une_perte_restaure_l_original_et_interrompt(corpus, monkeypatch):
    """Le comportement qui compte : si la vérification après écriture échoue,
    l'octet d'origine revient et la migration s'arrête. On sabote `recomposer`
    seulement après l'écriture, pour éprouver précisément ce chemin-là."""
    dossier, attendus = corpus
    original = (dossier / "aline.json").read_bytes()

    vrai_charger = migration.charger_profil_brut

    def charger_ampute(chemin):
        profil = vrai_charger(chemin)
        if profil.get(CLE_PARTITIONNEE):
            profil[CLE_PARTITIONNEE] = profil[CLE_PARTITIONNEE][:-1]
        return profil

    monkeypatch.setattr(migration, "charger_profil_brut", charger_ampute)

    with pytest.raises(migration.MigrationRefusee) as exc:
        migration.migrer(dossier, ecrire=True)

    assert "aline" in str(exc.value)
    assert (dossier / "aline.json").read_bytes() == original
    assert not (dossier / "aline").exists()


def test_cli_simulation_puis_apply(corpus, capsys):
    dossier, attendus = corpus

    assert migration.main(["--profils-dir", str(dossier)]) == 0
    assert "SIMULATION" in capsys.readouterr().out

    assert migration.main(["--profils-dir", str(dossier), "--apply"]) == 0
    assert "APPLIQUÉ" in capsys.readouterr().out

    assert migration.main(
        ["--profils-dir", str(dossier), "--verifier-seulement"]
    ) == 0
    assert "VÉRIFICATION" in capsys.readouterr().out

    for slug, profil in attendus.items():
        assert charger_profil_brut(dossier / f"{slug}.json") == profil
