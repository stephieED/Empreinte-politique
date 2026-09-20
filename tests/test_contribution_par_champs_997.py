"""#997 — un artifact ne porte que les CHAMPS que le job a collectés.

`#450` a rétabli « un artifact = les SLUGS d'un job ». Il restait l'autre
moitié, et elle a coûté un run : un job publiait le profil ENTIER, donc tous
les champs qu'il n'a pas collectés, recopiés de la baseline de son checkout.

Tant que `dossiers_legislatifs[]` se fusionnait en additif pur, cette copie
périmée ne pouvait rien écraser. Depuis que la source la plus récente gagne
(#997), la DERNIÈRE de `--dirs` l'emporte : `_artifacts/mandats-locaux` a
reposé les stades du run précédent sur les 17 candidats déclarés portant des
textes portés. Mesuré sur le run 35430469408 — Édouard Philippe, 9
`examine_commission` dans les deux artifacts d'extraction, 127 committés.

Mesuré aussi, artifact contre baseline : la contribution réelle de ces jobs est
UN SEUL champ — `mandats_locaux` (33 profils), `mandat_senatorial` (2).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from merge_profile import merge_raw_dirs  # noqa: E402
from profil_brut import projeter_contribution  # noqa: E402
from projeter_contribution import projeter_staging  # noqa: E402


def _profil(slug: str, **champs) -> dict:
    base = {
        "slug": slug, "chambre": "AN", "source": "assemblee_nationale",
        "identite": {"nom_complet": slug}, "mandats": [], "votes": [],
        "interventions": [], "dossiers_legislatifs": [], "mandats_locaux": [],
        "meta": {"warnings": []},
    }
    base.update(champs)
    return base


def _dossier(stade: str) -> dict:
    return {"id": "DLR5L17N1", "titre": "Texte", "role": "auteur",
            "stade_procedural": stade, "sort": "navette_en_cours",
            "date_min": "2024-01-01", "date_max": "2024-06-01",
            "legislature": "17", "nature_texte": "projet_de_loi",
            "source_url": "https://www.assemblee-nationale.fr/dyn/17/dossiers/x"}


# ── La projection elle-même ────────────────────────────────────────────────

def test_la_contribution_garde_le_slug_et_les_champs_declares():
    projete = projeter_contribution(
        _profil("x", mandats_locaux=[{"a": 1}], votes=[{"b": 2}]), ["mandats_locaux"])

    assert projete == {"slug": "x", "mandats_locaux": [{"a": 1}],
                       "contribution_partielle": ["mandats_locaux"]}


def test_le_manifeste_de_partition_part_avec_les_amendements():
    """Un socle qui annonce une tranche absente est illisible, pas partiel :
    `charger_profil_brut` refuse bruyamment."""
    profil = _profil("x", mandats_locaux=[{"a": 1}])
    profil["amendements_partitionnes"] = {"tranches": [{"fichier": "17.json"}]}

    assert "amendements_partitionnes" not in projeter_contribution(profil, ["mandats_locaux"])


def test_les_tranches_sont_retirees_du_staging(tmp_path):
    (tmp_path / "x.json").write_text(json.dumps(
        _profil("x", mandats_locaux=[{"a": 1}])), encoding="utf-8")
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "17.json").write_text("{}", encoding="utf-8")

    projetes, tranches = projeter_staging(tmp_path, ["mandats_locaux"])

    assert (projetes, tranches) == (1, 1)
    assert not (tmp_path / "x").exists()


# ── Le chemin réel : la fusion des artifacts ───────────────────────────────

def _staging(racine: Path, nom: str, profil: dict) -> Path:
    d = racine / nom
    d.mkdir(parents=True)
    (d / f"{profil['slug']}.json").write_text(json.dumps(profil), encoding="utf-8")
    return d


def test_une_contribution_entiere_repose_le_stade_du_run_precedent(tmp_path):
    """Le défaut, reproduit : c'est ce que le run 35430469408 a publié."""
    out = tmp_path / "out"
    out.mkdir()
    an = _staging(tmp_path, "an", _profil("x", dossiers_legislatifs=[_dossier("depose")]))
    ml = _staging(tmp_path, "ml", _profil("x", dossiers_legislatifs=[_dossier("examine_commission")],
                                          mandats_locaux=[{"a": 1}]))

    merge_raw_dirs([an, ml], out)

    publie = json.loads((out / "x.json").read_text(encoding="utf-8"))
    assert publie["dossiers_legislatifs"][0]["stade_procedural"] == "examine_commission"


def test_une_contribution_reduite_laisse_le_stade_corrige_passer(tmp_path):
    """Et elle apporte quand même ce qu'elle a collecté."""
    out = tmp_path / "out"
    out.mkdir()
    an = _staging(tmp_path, "an", _profil("x", dossiers_legislatifs=[_dossier("depose")]))
    ml = _staging(tmp_path, "ml", _profil("x", dossiers_legislatifs=[_dossier("examine_commission")],
                                          mandats_locaux=[{"a": 1}]))
    projeter_staging(ml, ["mandats_locaux"])

    merge_raw_dirs([an, ml], out)

    publie = json.loads((out / "x.json").read_text(encoding="utf-8"))
    assert publie["dossiers_legislatifs"][0]["stade_procedural"] == "depose"
    assert publie["mandats_locaux"] == [{"a": 1}]


def test_une_contribution_reduite_seule_ne_reecrit_rien(tmp_path):
    """Sinon elle publierait un profil AMPUTÉ.

    `merge_raw_dirs` écrit l'union des SOURCES et `ecrire_profil_brut` écrase :
    un slug dont seul un job d'enrichissement parle — son extraction complète
    ayant échoué, `continue-on-error` étant la règle — n'aurait plus que son
    champ. On laisse le profil committé en place, comme pour un slug qu'aucun
    job n'a touché (#450).

    Remettre la baseline en première source de la fusion ne marche pas : elle
    réinjecte ce que #450 a supprimé, et
    `test_publication_scopee_laisse_aboutir_la_correction_de_cle` le fait
    tomber — mesuré, pas supposé.
    """
    out = tmp_path / "out"
    out.mkdir()
    committe = _profil("x", votes=[{"scrutin_id": "s1"}],
                       dossiers_legislatifs=[_dossier("depose")])
    (out / "x.json").write_text(json.dumps(committe), encoding="utf-8")
    ml = _staging(tmp_path, "ml", _profil("x", mandats_locaux=[{"a": 1}]))
    projeter_staging(ml, ["mandats_locaux"])

    merge_raw_dirs([ml], out)

    publie = json.loads((out / "x.json").read_text(encoding="utf-8"))
    assert publie == committe


def test_une_contribution_reduite_ecrit_des_qu_une_collecte_complete_parle(tmp_path):
    """L'autre moitié : le garde-fou ne doit pas bloquer le cas nominal."""
    out = tmp_path / "out"
    out.mkdir()
    an = _staging(tmp_path, "an", _profil("x", votes=[{"scrutin_id": "s1"}]))
    ml = _staging(tmp_path, "ml", _profil("x", mandats_locaux=[{"a": 1}]))
    projeter_staging(ml, ["mandats_locaux"])

    merge_raw_dirs([an, ml], out)

    publie = json.loads((out / "x.json").read_text(encoding="utf-8"))
    assert publie["mandats_locaux"] == [{"a": 1}]
    assert publie["votes"] == [{"scrutin_id": "s1"}]
    assert "contribution_partielle" not in publie


# ---------------------------------------------------------------------------
# #997 — un champ qu'AUCUNE source ne reprend ne disparaît pas
# ---------------------------------------------------------------------------
#
# `merge_raw_profile` construisait son résultat par `dict(new)` : tout champ que
# la contribution ne portait pas était EFFACÉ. Invisible tant que chaque
# artifact publiait le profil entier ; depuis les contributions réduites, une
# source qui parle en dernier efface ce qu'une source précédente a apporté.
#
# Mesuré sur le run 35442990475, corpus entier : `mandat_senatorial` perdu sur
# 2 profils — Bruno Retailleau et Jean-Luc Mélenchon. Reproduit en rejouant la
# fusion sur les trois artifacts réels, dans l'ordre réel des `--dirs`.
#
# `mandats_locaux` n'a survécu que parce que sa source passe en DERNIER. De la
# chance, pas un contrat : ces deux champs sont les seuls que le traitement
# explicite de `merge_raw_profile` ne rattrape pas.


def test_un_champ_absent_de_la_contribution_survit(tmp_path):
    """Le cas Retailleau : le Sénat apporte, les mandats locaux parlent après."""
    out = tmp_path / "out"
    out.mkdir()
    an = _staging(tmp_path, "an", _profil("x"))
    sn = _staging(tmp_path, "sn", {"slug": "x", "mandat_senatorial": {"actif": True}})
    ml = _staging(tmp_path, "ml", {"slug": "x", "mandats_locaux": [{"a": 1}]})
    projeter_staging(sn, ["mandat_senatorial"])
    projeter_staging(ml, ["mandats_locaux"])

    merge_raw_dirs([an, sn, ml], out)

    publie = json.loads((out / "x.json").read_text(encoding="utf-8"))
    assert publie["mandat_senatorial"] == {"actif": True}
    assert publie["mandats_locaux"] == [{"a": 1}]


def test_une_contribution_peut_toujours_vider_un_champ_qu_elle_porte(tmp_path):
    """L'autre moitié : conserver l'absent ne doit pas empêcher d'écraser."""
    out = tmp_path / "out"
    out.mkdir()
    an = _staging(tmp_path, "an", _profil("x", mandats_locaux=[{"a": 1}]))
    ml = _staging(tmp_path, "ml", {"slug": "x", "mandats_locaux": []})
    projeter_staging(ml, ["mandats_locaux"])

    merge_raw_dirs([an, ml], out)

    publie = json.loads((out / "x.json").read_text(encoding="utf-8"))
    assert publie["mandats_locaux"] == []
