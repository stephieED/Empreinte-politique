"""Tests pour `_report_gouvernements` (check_quality_gate.py, §5 gouvernements).

Miroir de `tests/test_quality_gate_groupes.py`, adapté au schéma
`schema_gouvernement.py` : pas de notion de roster réseau (couverture
ministérielle = attribution de `portefeuille`, pas profils/roster), voir
issue #212 (plan d'implémentation #184).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from check_quality_gate import _report_gouvernements
from schema_gouvernement import make_empty_comptages_statuts


def _write_gouvernement(
    gouvernements_dir: Path,
    fichier: str,
    gouvernement_id: str,
    nb_membres: int = 1,
    nb_portefeuille_connu: int = 0,
    nb_textes: int = 0,
    periode_debut: str | None = "2024-07-18",
    periode_fin: str | None = None,
    warnings: list | None = None,
) -> None:
    data = {
        "schema_version": "1",
        "type_document": "profil_gouvernement",
        "gouvernement_id": gouvernement_id,
        "nom": f"Gouvernement {gouvernement_id}",
        "premier_ministre": None,
        "periode": {"debut": periode_debut, "fin": periode_fin, "actif": periode_fin is None},
        "membres": [
            {
                "membre_id": f"nosdeputes:membre-{i}",
                "nom": f"Membre {i}",
                "portefeuille": "Ministre" if i < nb_portefeuille_connu else None,
                "debut": "2024-07-18",
                "fin": None,
                "actif": True,
                "source_url": "https://example.org/source" if i < nb_portefeuille_connu else None,
            }
            for i in range(nb_membres)
        ],
        "textes": [
            {
                "dossier_id": f"DLR{i}",
                "titre": f"Texte {i}",
                "statut": "depose",
                "chambre_depot_initial": "AN",
                "date_depot": "2024-08-01",
                "date_dernier_evenement": "2024-08-01",
                "sort_49_3": None,
                "initiateurs": None,
                "source_url": None,
            }
            for i in range(nb_textes)
        ],
        # Dérivé de la nomenclature fermée plutôt qu'énuméré : un statut
        # ajouté au schéma (ex. adopte_cmp en #397) ne doit pas faire échouer
        # ces tests pour une raison sans rapport avec ce qu'ils vérifient.
        "comptages": {
            "par_statut": {**make_empty_comptages_statuts(), "depose": nb_textes}
        },
        "sources": [],
        "meta": {
            "schema_version": "1",
            "genere_le": "2026-08-01T10:00:00+00:00",
            "licence_donnees": "",
            "warnings": warnings or [],
        },
    }
    (gouvernements_dir / fichier).write_text(json.dumps(data), encoding="utf-8")


def _write_config(config_path: Path, gouvernements: list[dict]) -> None:
    config_path.write_text(json.dumps({"gouvernements": gouvernements}), encoding="utf-8")


# ---------------------------------------------------------------------------
# Structure cassée (hard errors)
# ---------------------------------------------------------------------------

def test_report_gouvernements_fichier_manquant_est_une_erreur_dure(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "manquant.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert len(hard) == 1
    assert "fichier manquant" in hard[0]
    assert "✗" in console


def test_report_gouvernements_config_illisible_est_une_erreur_dure(tmp_path):
    config_path = tmp_path / "n-existe-pas.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert len(hard) == 1
    assert "Impossible de lire" in hard[0]


def test_report_gouvernements_json_invalide_est_une_erreur_dure(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    (gouvernements_dir / "x.json").write_text("{ invalide", encoding="utf-8")
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert len(hard) == 1
    assert "JSON invalide" in hard[0]


def test_report_gouvernements_schema_invalide_est_une_erreur_dure(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    # Il manque toutes les clés obligatoires du schéma.
    (gouvernements_dir / "x.json").write_text(json.dumps({"nom": "X"}), encoding="utf-8")
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert len(hard) == 1
    assert "schéma invalide" in hard[0]


# ---------------------------------------------------------------------------
# Données valides — non-régression sur le cas nominal
# ---------------------------------------------------------------------------

def test_report_gouvernements_passe_sur_donnees_valides_completes(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=2, nb_portefeuille_connu=2, nb_textes=1,
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert soft == []
    assert "✓" in console


# ---------------------------------------------------------------------------
# Soft fail — couverture ministérielle incomplète
# ---------------------------------------------------------------------------

def test_report_gouvernements_couverture_ministerielle_incomplete_est_un_soft_fail(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=3, nb_portefeuille_connu=1, nb_textes=1,
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert any("couverture ministérielle incomplète" in w for w in soft)
    assert any("1/3" in w for w in soft)
    assert "⚠" in console


# ---------------------------------------------------------------------------
# Soft fail — textes[] vide sur une période couverte par la source (#399)
# ---------------------------------------------------------------------------

def test_report_gouvernements_textes_vides_avec_periode_renseignee_est_un_soft_fail(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=1, nb_portefeuille_connu=1, nb_textes=0,
        periode_debut="2024-07-18",
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert any("aucun texte porté" in w for w in soft)


def test_report_gouvernements_textes_vides_hors_couverture_nest_pas_un_soft_fail(tmp_path):
    """Fillon II : période antérieure aux archives ingérées.

    L'absence de texte y vient de la source, pas des données — la signaler
    comme un défaut afficherait une absence de couverture comme un fait
    mesuré (#399, AGENTS.md §2.5).
    """
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:FILLON_2",
        nb_membres=1, nb_portefeuille_connu=1, nb_textes=0,
        periode_debut="2007-06-19", periode_fin="2010-11-13",
    )
    _write_config(
        config_path,
        [{"gouvernement_id": "gouvernement:FILLON_2", "nom": "Fillon II", "fichier": "x.json"}],
    )

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert not any("aucun texte porté" in w for w in soft)
    # Le constat reste lisible, en information et non en avertissement.
    assert "hors de la couverture de la source" in console
    assert "Hors couverture de la source" in md


def test_report_gouvernements_textes_vides_couverture_partielle_nest_pas_un_soft_fail(tmp_path):
    # Période à cheval sur la borne : un textes[] vide y reste ininterprétable.
    # #1019 — la borne ayant reculé au 2012-06-20, l'ancienne fixture
    # (2016 → 2018) est devenue entièrement couverte. La période retenue est
    # celle d'Ayrault II, le cas à cheval RÉEL : il commence la veille de
    # l'ouverture de la XIV.
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=1, nb_portefeuille_connu=1, nb_textes=0,
        periode_debut="2012-06-19", periode_fin="2014-03-31",
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert not any("aucun texte porté" in w for w in soft)
    assert "partiellement couverte par la source" in console


def test_report_gouvernements_borne_de_couverture_est_affichee(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=1, nb_portefeuille_connu=1, nb_textes=1,
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    _, _, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert "2012-06-20" in console
    assert "2012-06-20" in md


def test_report_gouvernements_textes_vides_sans_periode_ne_declenche_rien(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=1, nb_portefeuille_connu=1, nb_textes=0,
        periode_debut=None,
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert not any("aucun texte porté" in w for w in soft)


# ---------------------------------------------------------------------------
# Soft fail — signaux réseau IncompleteRead
# ---------------------------------------------------------------------------

def test_report_gouvernements_incomplete_read_est_un_soft_fail(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=1, nb_portefeuille_connu=1, nb_textes=1,
        warnings=["dossiers_legislatifs: IncompleteRead(12 bytes read, 3 more expected)"],
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert hard == []
    assert any("IncompleteRead" in w for w in soft)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------

def test_report_gouvernements_markdown_affiche_le_detail(tmp_path):
    config_path = tmp_path / "gouvernements_reels.json"
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir()
    _write_gouvernement(
        gouvernements_dir, "x.json", "gouvernement:X",
        nb_membres=2, nb_portefeuille_connu=0, nb_textes=0,
    )
    _write_config(config_path, [{"gouvernement_id": "gouvernement:X", "nom": "X", "fichier": "x.json"}])

    hard, soft, console, md = _report_gouvernements(config_path, gouvernements_dir)

    assert "Portefeuilles confirmés" in md
    assert "0/2" in md


# ---------------------------------------------------------------------------
# Filet #427 : signature d'un écrasement massif de textes[]
# ---------------------------------------------------------------------------

def _config(*ids: str) -> list[dict]:
    return [{"gouvernement_id": i, "fichier": f"{i.replace(':', '-')}.json"} for i in ids]


def _ecrire_couverts(tmp_path: Path, nb_textes_par_gouv: list[int]) -> tuple[Path, Path]:
    """N gouvernements dont la période est couverte par les archives ingérées."""
    gouvernements_dir = tmp_path / "gouvernements"
    gouvernements_dir.mkdir(exist_ok=True)
    ids = []
    for rang, nb_textes in enumerate(nb_textes_par_gouv):
        gid = f"gouvernement:G{rang}"
        ids.append(gid)
        _write_gouvernement(
            gouvernements_dir,
            f"{gid.replace(':', '-')}.json",
            gid,
            nb_membres=3,
            nb_textes=nb_textes,
            # Période postérieure à la borne de couverture (2017-06-21).
            periode_debut="2024-01-10",
            periode_fin="2024-09-05",
        )
    config_path = tmp_path / "gouvernements.json"
    _write_config(config_path, _config(*ids))
    return gouvernements_dir, config_path


def test_tous_les_gouvernements_couverts_a_zero_est_un_echec_dur(tmp_path):
    """L'écrasement des 725 textes par une collecte échouée passait en simple
    avertissement, donc était committé et publié (#427)."""
    gouvernements_dir, config_path = _ecrire_couverts(tmp_path, [0, 0, 0])
    hard, _soft, _console, _md = _report_gouvernements(config_path, gouvernements_dir)
    assert any("simultanément" in e for e in hard)


def test_un_seul_gouvernement_couvert_a_zero_reste_un_avertissement(tmp_path):
    """Un gouvernement couvert peut légitimement n'avoir porté aucun texte —
    Philippe I n'en a qu'un. Seule la simultanéité est anormale."""
    gouvernements_dir, config_path = _ecrire_couverts(tmp_path, [0, 12, 30])
    hard, soft, _console, _md = _report_gouvernements(config_path, gouvernements_dir)
    assert not any("simultanément" in e for e in hard)
    assert any("aucun texte porté" in w for w in soft)


def test_un_seul_gouvernement_couvert_au_total_ne_declenche_pas_le_filet(tmp_path):
    """Avec un seul gouvernement couvert, « tous à zéro » ne distingue plus un
    écrasement d'un zéro légitime : ne pas bloquer sur cette base."""
    gouvernements_dir, config_path = _ecrire_couverts(tmp_path, [0])
    hard, _soft, _console, _md = _report_gouvernements(config_path, gouvernements_dir)
    assert not any("simultanément" in e for e in hard)
