"""#885 — le branchement : ce qui entre dans `raw_data/`, et ce qui n'y entre pas.

`collecte_senat` est le pendant sénatorial de `candidate_profile` : il écrit du
brut, source-near, et ne publie rien. Le bloc qu'il pose est calqué sur
`mandat_europeen` — deux sources étrangères au référentiel de l'Assemblée, deux
blocs de même forme, un seul chemin de normalisation à comprendre.

Trois refus sont gelés ici, et chacun empêche une donnée d'entrer là où la
fusion additive la garderait pour toujours (#729) :

1. **Hors périmètre.** 34 des 36 profils appariés sont des membres de roster.
   Le filtre est à la collecte, pas à l'affichage : une donnée qu'on ne
   publiera pas ne se collecte pas.
2. **Sans matricule apparié.** `identifiants.senat` vaut `null` sur 1 160 des
   1 196 entrées, et sur deux c'est une **décision** — les homonymes de
   `beatrice-descamps` et `jean-louis-masson`. Écrire sur un profil non apparié
   publierait la carrière de quelqu'un d'autre.
3. **Sans profil brut.** Un profil apparié dont le socle manque n'est pas un
   profil vide : c'est une collecte qui n'a pas eu lieu, et fabriquer le socle
   ici écrirait une identité que personne n'a collectée (§2 règle 5).

Doublures construites ici (AGENTS.md §3, #457/#473/#488).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from collecte_senat import CLE_BLOC, collecter, composer_bloc, profils_a_collecter  # noqa: E402


def _corpus(tmp_path, profils, correspondances):
    """`profils` : {slug: (provenance | None, brut | None)}."""
    raw = tmp_path / "raw"
    pivot = tmp_path / "pivot"
    raw.mkdir(exist_ok=True)
    pivot.mkdir(exist_ok=True)
    for slug, (provenance, brut) in profils.items():
        if provenance is not None:
            (pivot / f"{slug}.pivot.json").write_text(
                json.dumps({"slug": slug, "meta": {"provenance": provenance}}),
                encoding="utf-8")
        if brut is not None:
            (raw / f"{slug}.json").write_text(json.dumps(brut), encoding="utf-8")
    corr = tmp_path / "correspondance.json"
    corr.write_text(json.dumps({"correspondances": correspondances}), encoding="utf-8")
    return raw, pivot, corr


def _dump(tmp_path):
    """Un export minimal : un sénateur, un mandat."""
    chemin = tmp_path / "export.sql"
    chemin.write_text(
        "COPY sen (senmat, sennomuse) FROM stdin;\n04033B\tRetailleau\n\\.\n"
        "COPY elusen (senmat, eludatdeb, eludatfin, etadebmancod, etafinmancod, dptnum)"
        " FROM stdin;\n04033B\t2020-10-01 00:00:00\t2024-10-21 00:00:00\tREN2\tFINMEMGVT\t850\n\\.\n",
        encoding="utf-8")
    return chemin


# ---------------------------------------------------------------------------
# Le périmètre
# ---------------------------------------------------------------------------

def test_seuls_les_candidats_declares_sont_collectes(tmp_path):
    """34 des 36 appariés sont des membres de roster. Le filtre est à la
    collecte : une donnée qu'on ne publiera pas ne se collecte pas."""
    raw, pivot, corr = _corpus(tmp_path, {
        "bruno-retailleau": ("candidat_declare", {"slug": "bruno-retailleau"}),
        "gerard-larcher": ("roster_groupe", {"slug": "gerard-larcher"}),
    }, {
        "bruno-retailleau": {"identifiants": {"senat": "04033B"}},
        "gerard-larcher": {"identifiants": {"senat": "88999X"}},
    })

    a_collecter, hors = profils_a_collecter(
        json.loads(corr.read_text()), pivot)

    assert a_collecter == {"bruno-retailleau": "04033B"}
    assert hors == ["gerard-larcher"]


def test_un_profil_sans_matricule_n_est_jamais_collecte(tmp_path):
    """Sur deux entrées, le `null` est une décision : les homonymes de
    `beatrice-descamps` et `jean-louis-masson`."""
    raw, pivot, corr = _corpus(tmp_path, {
        "jean-louis-masson": ("candidat_declare", {"slug": "jean-louis-masson"}),
    }, {"jean-louis-masson": {"identifiants": {"senat": None}}})

    a_collecter, hors = profils_a_collecter(json.loads(corr.read_text()), pivot)

    assert a_collecter == {}
    assert hors == []


def test_un_pivot_illisible_est_hors_perimetre(tmp_path):
    """Une provenance qu'on ne peut pas lire n'est pas une provenance
    publiable (§2 règle 5)."""
    raw, pivot, corr = _corpus(tmp_path, {
        "casse": (None, {"slug": "casse"}),
    }, {"casse": {"identifiants": {"senat": "04033B"}}})
    (pivot / "casse.pivot.json").write_text("{ pas du json", encoding="utf-8")

    a_collecter, hors = profils_a_collecter(json.loads(corr.read_text()), pivot)

    assert a_collecter == {}
    assert hors == ["casse"]


# ---------------------------------------------------------------------------
# L'écriture
# ---------------------------------------------------------------------------

def test_le_bloc_est_calque_sur_le_bloc_europeen(tmp_path):
    """Même forme, donc même chemin de normalisation dans
    `generate_all_profiles`."""
    from senat_opendata import lire_tables

    bloc = composer_bloc(lire_tables(_dump(tmp_path), tables={"sen", "elusen"}),
                         "04033B", "2026-09-13T12:42:00+0000")

    assert set(bloc) == {"matricule", "source", "source_portail",
                         "synchro_le", "mandats_senatoriaux"}
    assert bloc["matricule"] == "04033B"
    assert len(bloc["mandats_senatoriaux"]) == 1


def test_la_simulation_n_ecrit_rien(tmp_path):
    raw, pivot, corr = _corpus(tmp_path, {
        "bruno-retailleau": ("candidat_declare", {"slug": "bruno-retailleau"}),
    }, {"bruno-retailleau": {"identifiants": {"senat": "04033B"}}})
    avant = (raw / "bruno-retailleau.json").read_text()

    rapport = collecter(_dump(tmp_path), raw, pivot, corr)

    assert rapport["applique"] is False
    assert rapport["nb_profils"] == 1
    assert (raw / "bruno-retailleau.json").read_text() == avant


def test_l_ecriture_pose_le_bloc_sans_toucher_au_reste(tmp_path):
    """Le socle brut porte l'identité et les listes collectées ailleurs : ce
    module n'ajoute qu'une clé."""
    raw, pivot, corr = _corpus(tmp_path, {
        "bruno-retailleau": ("candidat_declare",
                             {"slug": "bruno-retailleau", "votes": [1, 2, 3],
                              "identite": {"nom_complet": "Bruno Retailleau"}}),
    }, {"bruno-retailleau": {"identifiants": {"senat": "04033B"}}})

    collecter(_dump(tmp_path), raw, pivot, corr, appliquer=True)

    brut = json.loads((raw / "bruno-retailleau.json").read_text())
    assert brut["votes"] == [1, 2, 3]
    assert brut["identite"]["nom_complet"] == "Bruno Retailleau"
    assert brut[CLE_BLOC]["matricule"] == "04033B"


def test_un_apparie_sans_brut_est_declare_jamais_fabrique(tmp_path):
    """Fabriquer le socle écrirait une identité que personne n'a collectée."""
    raw, pivot, corr = _corpus(tmp_path, {
        "bruno-retailleau": ("candidat_declare", None),
    }, {"bruno-retailleau": {"identifiants": {"senat": "04033B"}}})

    rapport = collecter(_dump(tmp_path), raw, pivot, corr, appliquer=True)

    assert rapport["nb_sans_brut"] == 1
    assert rapport["sans_brut"] == ["bruno-retailleau"]
    assert not (raw / "bruno-retailleau.json").exists()


def test_une_correspondance_illisible_leve(tmp_path):
    """Elle est le seul lien entre un slug et un matricule. L'inventer
    publierait la carrière de quelqu'un d'autre."""
    import pytest

    raw, pivot, corr = _corpus(tmp_path, {}, {})
    corr.write_text("{ pas du json", encoding="utf-8")

    with pytest.raises(ValueError) as echec:
        collecter(_dump(tmp_path), raw, pivot, corr)

    assert "carrière de quelqu'un d'autre" in str(echec.value)


def test_un_export_vide_arrete_avant_toute_ecriture(tmp_path):
    """L'archive du 13/09/2026 à 03 h 33 : 444 octets, 0 table, HTTP 200. Un
    collecteur qui aurait tourné entre 03 h 33 et 12 h 42 aurait vidé les fiches
    en silence."""
    import pytest
    from senat_opendata import ExportSenatVide

    raw, pivot, corr = _corpus(tmp_path, {
        "bruno-retailleau": ("candidat_declare", {"slug": "bruno-retailleau"}),
    }, {"bruno-retailleau": {"identifiants": {"senat": "04033B"}}})
    vide = tmp_path / "vide.sql"
    vide.write_text("-- PostgreSQL database dump\n", encoding="utf-8")
    avant = (raw / "bruno-retailleau.json").read_text()

    with pytest.raises(ExportSenatVide):
        collecter(vide, raw, pivot, corr, appliquer=True)

    assert (raw / "bruno-retailleau.json").read_text() == avant


# ---------------------------------------------------------------------------
# La garde d'avant-commit
# ---------------------------------------------------------------------------

def test_le_bloc_senatorial_est_declare_dans_la_relation_des_mandats():
    """Sans cette déclaration, `audit_collecte_vs_publie` lirait un déficit de
    la taille du bloc et **bloquerait le commit** — ce qu'il a fait au run
    `34712936188` pour la raison inverse (#888)."""
    from audit_collecte_vs_publie import RELATIONS

    relation = next(r for r in RELATIONS if r.champ_pivot == "mandats")

    assert ("mandat_senatorial", "mandats_senatoriaux") in relation.sources
    assert "mandat_senatorial.mandats_senatoriaux" in relation.libelle_sources
