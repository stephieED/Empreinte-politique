"""Suspension temporaire de l'extraction d'un groupe configuré (#516).

Le garde-fou couvre les quatre propriétés qui font qu'une suspension est une
décision et non un renoncement :

1. **elle coupe le réseau** — la clé de fetch d'un groupe suspendu n'est jamais
   interrogée, c'est le point de départ : c'est `('senateurs', None)`, sur un
   certificat TLS expiré, qui faisait échouer les runs `32463926808` et
   `32548486495`, collecte AN comprise ;
2. **elle n'est pas une panne** — un groupe suspendu ne déclenche ni l'anomalie
   « 0 membre retenu » de #511 ni un échec de génération ;
3. **elle ne supprime rien** — la fiche de groupe publiée reste sur le disque,
   et le quality gate continue d'en contrôler la structure ;
4. **elle se documente, ou elle échoue** — un bloc sans motif, sans date, sans
   référence ni condition de reprise est une erreur dure.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from check_quality_gate import _report_groupes
from generate_group_profiles import generate_all
from generate_roster_candidats import (
    EXIT_ROSTER_INDISPONIBLE,
    anomalies_roster,
    build_roster_candidats_detaille,
    fetch_rosters_bruts,
    main as generate_roster_candidats_main,
)
from groupes_config import (
    CHAMPS_SUSPENSION_REQUIS,
    anomalies_suspension,
    est_suspendu,
    partitionner_groupes,
    resume_suspension,
)

from test_generate_group_profiles import index_partages_isoles  # noqa: F401  (fixture autouse)
from test_quality_gate_groupes import _write_config, _write_groupe

import pytest

#: Ce fichier de tests lit la configuration committée nommée ci-dessous.
#: Le garde-fou de `conftest.py` refuse tout `.json` de `raw_data/` qu'un
#: test n'a pas déclaré (#791), et n'accepte la déclaration que si le chemin
#: est dans le `sparse-checkout` de `tests.yml` — sinon le test ne tournerait
#: qu'en local, sur ce qu'un run y a laissé.
pytestmark = pytest.mark.lit_reference_committee("raw_data/groupes_reels.json")


_SUSPENSION = {
    "depuis": "2026-08-24",
    "motif": "Certificat TLS expiré sur archive.nossenateurs.fr.",
    "references": ["#516", "run 32548486495"],
    "condition_reprise": "Un certificat valide, ou une source de remplacement.",
}

_GROUPE_AN = {
    "roster_chambre": "deputes", "groupe_id": "AN:LR", "groupe_sigle": "LR",
    "groupe_nom": "Les Républicains", "chambre": "AN", "legislature": "16",
    "fichier": "groupe-AN-LR-16.json",
}
_GROUPE_SENAT = {
    "roster_chambre": "senateurs", "groupe_id": "Senat:SER", "groupe_sigle": "SER",
    "groupe_nom": "Socialiste, Écologiste et Républicain", "chambre": "Senat",
    "legislature": None, "fichier": "groupe-Senat-SER.json",
    "extraction_suspendue": _SUSPENSION,
}

_MEMBRES_AN = [
    {"slug": "alice", "nom": "Alice", "groupe_sigle": "LR", "mandat_debut": "2022-06-22", "mandat_fin": None},
]


# ---------------------------------------------------------------------------
# groupes_config : la lecture partagée
# ---------------------------------------------------------------------------

def test_est_suspendu_ne_lit_qu_une_valeur_vraie():
    assert est_suspendu(_GROUPE_SENAT)
    assert not est_suspendu(_GROUPE_AN)
    assert not est_suspendu(dict(_GROUPE_AN, extraction_suspendue=None))
    assert not est_suspendu(dict(_GROUPE_AN, extraction_suspendue=False))


def test_partitionner_groupes_conserve_l_ordre_de_la_config():
    actifs, suspendus = partitionner_groupes([_GROUPE_SENAT, _GROUPE_AN, _GROUPE_SENAT])

    assert [g["groupe_id"] for g in actifs] == ["AN:LR"]
    assert [g["groupe_id"] for g in suspendus] == ["Senat:SER", "Senat:SER"]


def test_anomalies_suspension_exige_les_quatre_champs():
    for champ in CHAMPS_SUSPENSION_REQUIS:
        incomplet = {k: v for k, v in _SUSPENSION.items() if k != champ}
        anomalies = anomalies_suspension(dict(_GROUPE_SENAT, extraction_suspendue=incomplet))
        assert len(anomalies) == 1, (champ, anomalies)
        assert champ in anomalies[0]


def test_anomalies_suspension_refuse_un_bloc_non_documentable():
    # `"extraction_suspendue": true` suspend sans rien dire — la forme même que
    # cette issue interdit.
    anomalies = anomalies_suspension(dict(_GROUPE_SENAT, extraction_suspendue=True))

    assert len(anomalies) == 1
    assert "objet documenté" in anomalies[0]


def test_anomalies_suspension_silencieuse_sur_un_groupe_actif_ou_en_regle():
    assert anomalies_suspension(_GROUPE_AN) == []
    assert anomalies_suspension(_GROUPE_SENAT) == []


def test_resume_suspension_nomme_le_groupe_la_date_et_les_references():
    resume = resume_suspension(_GROUPE_SENAT)

    assert "Senat:SER" in resume
    assert "2026-08-24" in resume
    assert "#516" in resume


# ---------------------------------------------------------------------------
# 1 & 2 — le roster : pas de fetch, pas d'anomalie
# ---------------------------------------------------------------------------

def test_roster_n_interroge_jamais_la_cle_d_un_groupe_suspendu(monkeypatch):
    """La propriété centrale : c'est ce fetch-là qui faisait rougir les runs."""
    interrogees = []

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        interrogees.append((chambre, legislature))
        return _MEMBRES_AN

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", fake_fetch_full_roster)

    rosters_bruts, echecs = fetch_rosters_bruts([_GROUPE_AN, _GROUPE_SENAT])

    assert interrogees == [("deputes", "16")]
    assert ("senateurs", None) not in rosters_bruts
    assert echecs == {}


def test_roster_suspendu_n_est_pas_une_anomalie_de_retrecissement():
    """#511 signale un groupe à 0 membre ; un groupe suspendu n'en est pas un.

    Sans cette exclusion, la suspension déplacerait simplement l'échec : le
    roster ne serait toujours pas écrit, pour une autre raison.
    """
    groupes = [_GROUPE_AN, _GROUPE_SENAT]
    rosters_bruts = {("deputes", "16"): _MEMBRES_AN}

    candidats, membres_par_groupe = build_roster_candidats_detaille(groupes, rosters_bruts)
    anomalies = anomalies_roster(groupes, rosters_bruts, membres_par_groupe, candidats)

    assert [c["slug"] for c in candidats] == ["alice"]
    assert membres_par_groupe == {"AN:LR": 1}  # le groupe suspendu n'est pas compté à 0
    assert anomalies == []


def test_roster_ecrit_bien_le_fichier_malgre_un_groupe_suspendu(tmp_path, monkeypatch):
    config_path = tmp_path / "groupes_reels.json"
    config_path.write_text(json.dumps({"groupes": [_GROUPE_AN, _GROUPE_SENAT]}), encoding="utf-8")
    out_path = tmp_path / "roster_candidats.json"

    monkeypatch.setattr(
        "generate_roster_candidats.fetch_full_roster",
        lambda chambre, legislature=None, session=None: _MEMBRES_AN,
    )

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == 0
    ecrit = json.loads(out_path.read_text(encoding="utf-8"))
    assert [c["slug"] for c in ecrit["candidats"]] == ["alice"]


def test_roster_refuse_une_config_entierement_suspendue(tmp_path, monkeypatch):
    """Zéro groupe actif n'est pas « un roster vide » : c'est une décision écrite.

    Le distinguer importe — un roster vide écrit sans bruit est exactement
    l'incident de #511, et rien n'est écrit ici.

    Le code de sortie est **2** depuis #524 (`EXIT_ROSTER_INDISPONIBLE`) et non
    plus 1 : suspendre les entrées AN comme les 2 entrées Sénat le sont depuis
    #516 est le remède documenté d'une source en panne. Tant que ce cas sortait
    en 1, ce remède reproduisait l'échec qu'il devait éteindre.
    """
    config_path = tmp_path / "groupes_reels.json"
    config_path.write_text(json.dumps({"groupes": [_GROUPE_SENAT]}), encoding="utf-8")
    out_path = tmp_path / "roster_candidats.json"

    def interdit(*args, **kwargs):
        raise AssertionError("aucun fetch ne doit partir sur une config entièrement suspendue")

    monkeypatch.setattr("generate_roster_candidats.fetch_full_roster", interdit)

    rc = generate_roster_candidats_main(["--config", str(config_path), "--out", str(out_path)])

    assert rc == EXIT_ROSTER_INDISPONIBLE
    assert not out_path.exists(), "aucun roster à 0 candidat n'est jamais écrit (#511)"


# ---------------------------------------------------------------------------
# 2 & 3 — la génération : ni fetch, ni échec, ni suppression
# ---------------------------------------------------------------------------

def test_generation_ignore_un_groupe_suspendu_sans_le_compter_en_echec(tmp_path, monkeypatch):
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()

    interrogees = []

    def fake_fetch_full_roster(chambre, legislature=None, session=None):
        interrogees.append(chambre)
        return _MEMBRES_AN

    monkeypatch.setattr("generate_group_profiles.fetch_full_roster", fake_fetch_full_roster)

    resultat = generate_all(
        [_GROUPE_AN, _GROUPE_SENAT],
        profiles_dir=profiles_dir,
        out_dir=out_dir,
        validate=True,
    )

    # 0 et non 1 : compter la suspension en échec ferait sortir le script en 1
    # à chaque run, donc échouer le job pour une décision écrite.
    assert resultat.echecs == 0
    # Et pas davantage un « roster indisponible » (code 2, #518) : une clé de
    # fetch qu'on n'a délibérément pas construite n'est pas une clé en panne.
    assert resultat.code_sortie() == 0
    assert interrogees == ["deputes"]
    assert (out_dir / "groupe-AN-LR-16.json").exists()
    assert not (out_dir / "groupe-Senat-SER.json").exists()


def test_generation_laisse_intacte_la_fiche_deja_publiee(tmp_path, monkeypatch):
    """Une suspension gèle un fichier publié ; elle ne le réécrit ni ne l'efface.

    C'est ce qui la distingue d'un retrait de la config, lequel ferait
    disparaître un fichier — perte bloquante pour `audit_diff_profils`
    (#460/#470).
    """
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    out_dir = tmp_path / "groupes"
    out_dir.mkdir()
    publie = out_dir / "groupe-Senat-SER.json"
    publie.write_text('{"groupe_id": "Senat:SER", "gele": true}', encoding="utf-8")

    monkeypatch.setattr(
        "generate_group_profiles.fetch_full_roster",
        lambda chambre, legislature=None, session=None: _MEMBRES_AN,
    )

    generate_all([_GROUPE_SENAT], profiles_dir=profiles_dir, out_dir=out_dir)

    assert json.loads(publie.read_text(encoding="utf-8")) == {"groupe_id": "Senat:SER", "gele": True}


# ---------------------------------------------------------------------------
# 3 & 4 — le quality gate : structure toujours gardée, suspension documentée
# ---------------------------------------------------------------------------

def _config_suspendue(tmp_path, suspension=_SUSPENSION):
    config_path = tmp_path / "groupes_reels.json"
    _write_config(config_path, [{
        "groupe_id": "Senat:SER", "groupe_nom": "SER", "fichier": "ser.json",
        "extraction_suspendue": suspension,
    }])
    return config_path


def test_gate_ne_mesure_plus_la_couverture_d_un_groupe_suspendu(tmp_path):
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    # Couverture nulle et 0 vote de cohésion : deux soft warnings sur un groupe
    # actif — aucun ici, ils mesureraient une collecte qui n'a pas eu lieu.
    _write_groupe(groupes_dir, "ser.json", "Senat:SER", roster_total=76,
                  profils_disponibles=0, nb_membres=5, nb_cohesion=0)

    hard, soft, console, md = _report_groupes(_config_suspendue(tmp_path), groupes_dir, min_members=1)

    assert hard == []
    assert soft == []
    assert "⏸" in console
    assert "#516" in console
    assert "Extraction suspendue" in md


def test_gate_garde_les_controles_durs_sur_un_groupe_suspendu(tmp_path):
    """Le fichier reste publié : sa disparition reste une erreur dure."""
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()

    hard, soft, console, md = _report_groupes(_config_suspendue(tmp_path), groupes_dir, min_members=1)

    assert len(hard) == 1
    assert "fichier manquant" in hard[0]


def test_gate_refuse_une_suspension_non_documentee(tmp_path):
    groupes_dir = tmp_path / "groupes"
    groupes_dir.mkdir()
    _write_groupe(groupes_dir, "ser.json", "Senat:SER", roster_total=76,
                  profils_disponibles=5, nb_membres=5, nb_cohesion=1)
    config_path = _config_suspendue(tmp_path, suspension={"motif": "parce que"})

    hard, soft, console, md = _report_groupes(config_path, groupes_dir, min_members=1)

    assert len(hard) == 1
    assert "non documentée" in hard[0]
    assert "condition_reprise" in hard[0]


# ---------------------------------------------------------------------------
# La config du dépôt
# ---------------------------------------------------------------------------

def test_toute_suspension_du_depot_est_documentee():
    """Vrai avec 0 suspension comme avec 2 : ce test survit à la réactivation.

    Il ne fige pas *quels* groupes sont suspendus — c'est une décision
    éditoriale datée, pas un invariant — mais il exige que chacune reste
    relisable : pourquoi, depuis quand, sous quelle référence, et à quelle
    condition on la lève.
    """
    config_path = Path(__file__).resolve().parents[1] / "raw_data" / "groupes_reels.json"
    groupes = json.loads(config_path.read_text(encoding="utf-8"))["groupes"]

    anomalies = [a for groupe in groupes for a in anomalies_suspension(groupe)]

    assert anomalies == []


def test_la_config_du_depot_garde_au_moins_un_groupe_actif():
    config_path = Path(__file__).resolve().parents[1] / "raw_data" / "groupes_reels.json"
    groupes = json.loads(config_path.read_text(encoding="utf-8"))["groupes"]

    actifs, _ = partitionner_groupes(groupes)

    assert actifs, "tous les groupes suspendus : `generate_roster_candidats.py` sortirait en 1"
