#!/usr/bin/env python3
"""
Tests du lot #1223 — `validate_profil()` tourne dans le run, et une fiche hors
schéma ouvre une issue au lieu de rester une ligne non lue.

Ce qu'ils verrouillent :

- **le contrôle nomme les profils et leur population**, lit un fichier illisible
  comme non contrôlé, et **ne bloque jamais** (arbitrage du 06/10/2026) ;
- **le workflow l'exécute**, sans lui donner le pouvoir d'annuler le commit ;
- **l'étape d'issue fait ce qu'elle dit**, rejouée ici avec un faux `gh` : elle
  ouvre, tient à jour, ferme — et sans jeton elle avertit au lieu de se taire.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

import audit_validation_profils as audit  # noqa: E402

WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

# Mandat local copié de xavier-bertrand.pivot.json (privé 4275c239d,
# 06/10/2026), réduit aux clés que la validation regarde.
MANDAT_LOCAL = {
    "label": "Hauts-de-France", "categorie": "mandat_local", "categorie_source": "rne",
    "type_organe_source": "conseil_regional", "fonction": "Président du conseil régional",
    "debut": "2021-07-02", "fin": None, "actif": True,
}


def _ecrire(repertoire: Path, slug: str, provenance: str, type_organe: str) -> None:
    mandat = dict(MANDAT_LOCAL, type_organe_source=type_organe)
    (repertoire / f"{slug}.pivot.json").write_text(
        json.dumps({"id": slug, "meta": {"provenance": provenance}, "mandats": [mandat]}),
        encoding="utf-8",
    )


def _du_type(erreurs: list[str]) -> list[str]:
    return [e for e in erreurs if "type_organe_source" in e]


# ---------------------------------------------------------------------------
# Le contrôle
# ---------------------------------------------------------------------------

def test_le_rapport_nomme_le_profil_fautif_et_sa_population(tmp_path, monkeypatch):
    # `validate_profil` exige bien d'autres clés qu'un profil réduit n'a pas :
    # on ne garde ici que la famille d'erreurs que le lot a mesurée.
    vrai = audit.validate_profil
    monkeypatch.setattr(audit, "validate_profil", lambda p: _du_type(vrai(p)))
    _ecrire(tmp_path, "a", "candidat_declare", "conseil_regional")
    _ecrire(tmp_path, "b", "candidat_declare", "conseil_inconnu")
    _ecrire(tmp_path, "c", "roster_groupe", "conseil_municipal")
    (tmp_path / "d.pivot.json").write_text("{pas du json", encoding="utf-8")

    rapport = audit.auditer(tmp_path)

    assert [e["slug"] for e in rapport["invalides"]] == ["b"]
    assert rapport["invalides"][0]["provenance"] == "candidat_declare"
    assert rapport["illisibles"] == ["d"]
    assert rapport["erreurs_total"] == 1
    texte = audit.generate_markdown_report(rapport)
    assert "`b`" in texte and "conseil_inconnu" in texte
    assert "1 candidat" in texte  # la population, pas un total nu (#630)
    assert "`d`" in texte and "non contrôlés" in texte


def test_un_corpus_valide_le_dit(tmp_path, monkeypatch):
    monkeypatch.setattr(audit, "validate_profil", lambda p: [])
    _ecrire(tmp_path, "a", "candidat_declare", "conseil_regional")
    assert "Tous passent" in audit.generate_markdown_report(audit.auditer(tmp_path))


def test_le_controle_ne_bloque_jamais(tmp_path, monkeypatch):
    """Signalement, pas échec dur : le code de sortie est nul même en erreur."""
    monkeypatch.setattr(audit, "validate_profil", lambda p: ["erreur"])
    _ecrire(tmp_path, "a", "candidat_declare", "conseil_regional")
    sortie = tmp_path / "r.json"
    assert audit.main(["--profils-dir", str(tmp_path), "--out-json", str(sortie)]) == 0
    assert len(json.loads(sortie.read_text(encoding="utf-8"))["invalides"]) == 1


def test_un_repertoire_introuvable_n_est_pas_un_corpus_valide(tmp_path):
    assert audit.main(["--profils-dir", str(tmp_path / "absent")]) == 2


# ---------------------------------------------------------------------------
# Le workflow
# ---------------------------------------------------------------------------

def _etape(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index(f"      - name: {nom}\n")
    suite = re.search(r"\n      - name: |\n      # ─", texte[debut + 10:])
    return texte[debut: debut + 10 + suite.start()] if suite else texte[debut:]


def test_le_run_execute_le_controle_sans_pouvoir_annuler_le_commit():
    etape = _etape("Fiches hors schéma — validate_profil (signalement)")
    assert "python3 src/audit_validation_profils.py" in etape
    assert "continue-on-error: true" in etape
    assert "exit 1" not in etape


def test_l_issue_ne_decrit_que_ce_qui_a_ete_publie():
    etape = _etape("Fiches hors schéma — issue de suivi")
    assert "steps.commit.outputs.pushed == 'true'" in etape
    assert "continue-on-error: true" in etape
    # Jamais le jeton de lecture : il ne peut pas écrire d'issue, et ne doit pas.
    assert "secrets.SRC_ISSUES_TOKEN" in etape and "SRC_READ_TOKEN" not in etape


# ---------------------------------------------------------------------------
# L'étape d'issue, rejouée avec un faux `gh`
# ---------------------------------------------------------------------------

def _script() -> str:
    etape = _etape("Fiches hors schéma — issue de suivi")
    return textwrap.dedent(etape.split("        run: |\n", 1)[1])


def _jouer(tmp_path: Path, invalides: int, jeton: str, issue_ouverte: str) -> tuple[str, list[str]]:
    (tmp_path / "validation-profils.json").write_text(
        json.dumps({"invalides": [{}] * invalides, "erreurs_total": invalides * 2}), encoding="utf-8"
    )
    (tmp_path / "validation-profils.md").write_text("rapport\n", encoding="utf-8")
    journal = tmp_path / "gh.log"
    faux = tmp_path / "bin" / "gh"
    faux.parent.mkdir()
    faux.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$1 $2" >> "{journal}"\n'
        f'if [[ "$1 $2" == "issue list" ]]; then echo "{issue_ouverte}"; fi\n',
        encoding="utf-8",
    )
    faux.chmod(faux.stat().st_mode | stat.S_IEXEC)
    env = dict(
        os.environ, PATH=f"{faux.parent}:{os.environ['PATH']}", GH_TOKEN=jeton,
        DEPOT="x/y", ETIQUETTE="fiches-hors-schema", URL_RUN="https://exemple/run/1",
    )
    resultat = subprocess.run(
        ["bash", "-c", _script()], cwd=tmp_path, env=env, capture_output=True, text=True
    )
    assert resultat.returncode == 0, resultat.stderr
    appels = journal.read_text(encoding="utf-8").split("\n")[:-1] if journal.exists() else []
    return resultat.stdout, appels


def test_sans_jeton_des_fiches_fautives_avertissent_au_lieu_de_se_taire(tmp_path):
    sortie, appels = _jouer(tmp_path, invalides=3, jeton="", issue_ouverte="")
    assert "::warning::FICHES_HORS_SCHEMA" in sortie and "SRC_ISSUES_TOKEN" in sortie
    assert appels == []


def test_la_premiere_fiche_fautive_ouvre_l_issue(tmp_path):
    sortie, appels = _jouer(tmp_path, invalides=2, jeton="t", issue_ouverte="")
    assert appels == ["issue list", "label create", "issue create"]
    assert "::warning::FICHES_HORS_SCHEMA" in sortie


def test_un_defaut_qui_dure_tient_l_issue_a_jour_sans_en_ouvrir_une_autre(tmp_path):
    _, appels = _jouer(tmp_path, invalides=2, jeton="t", issue_ouverte="1300")
    assert appels == ["issue list", "issue edit", "issue comment"]


def test_le_run_qui_ne_trouve_plus_rien_ferme_l_issue(tmp_path):
    _, appels = _jouer(tmp_path, invalides=0, jeton="t", issue_ouverte="1300")
    assert appels == ["issue list", "issue close"]


def test_un_corpus_valide_sans_issue_ouverte_ne_fait_rien(tmp_path):
    sortie, appels = _jouer(tmp_path, invalides=0, jeton="t", issue_ouverte="")
    assert appels == ["issue list"] and "::warning::" not in sortie
