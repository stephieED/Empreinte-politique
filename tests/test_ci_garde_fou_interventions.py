"""Garde-fou #460 : signaler, avant de lancer le run, qu'un écrasement sans
collecte d'interventions va détruire des données déjà acquises.

Contexte. `existing_profiles=overwrite` lève `--no-merge` ;
`extract_interventions=false` lève `--skip-interventions`. Chacun est correct
isolément — l'un est le mode de correction de schéma, l'autre le mode
d'extraction rapide. Ensemble, ils réécrivent le profil **sans** ce que le run
n'a pas collecté. Le run 32288588518 (commit `a125e9e`, 19/08/2026) a ainsi
effacé 789 interventions, les 647 `tags_thematiques` qui en dérivent et les
497 `tags_thematiques_agreges` de deux profils de groupe — ces deux derniers
étant des champs **publiés** (AGENTS.md §6).

Pourquoi un avertissement et non un refus. Le refus dur existe déjà en aval :
`audit_diff_profils.py`, branché avant l'étape de commit, bloque sur toute
perte d'un champ stable. Refuser ici la combinaison ferait double emploi et
casserait un usage légitime — propager une correction de clé sans repayer la
collecte des interventions est un choix valide dès lors qu'il est conscient.
Ce qui manquait n'était pas un veto, c'était de rendre le choix conscient
**avant** d'engager une heure de runner.

Depuis #578, `cold_start` ne lève plus `--no-merge` : il purge le cache de
téléchargement, ce qui ne détruit aucune donnée acquise. Le garde-fou suit —
un signal qui crie sur un mode inoffensif est un signal qu'on apprend à
ignorer.

Ces tests exécutent réellement le script du step, extrait du workflow : une
assertion purement textuelle sur le YAML dirait que l'avertissement est écrit,
pas qu'il se déclenche. Or c'est bien un garde-fou débranché qui est à
l'origine de #460.

Volontairement sans PyYAML (absent de requirements.txt), comme
`test_ci_publication_profils.py` et `test_ci_cache_paths.py`.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

INDENTATION_RUN = 10  # `run: |` est à 8 espaces, son contenu à 10.


def _script_du_garde_fou() -> str:
    """Le shell du step, tel que GitHub Actions l'exécutera.

    Reproduit le dépliage du bloc scalaire YAML (`run: |`) : retirer les 10
    espaces d'indentation de base. C'est ce dépliage qui rend le heredoc
    Python exécutable — l'oublier donnerait un script au corps sur-indenté,
    et un test qui échouerait pour une raison sans rapport avec #460.
    """
    texte = WORKFLOW.read_text(encoding="utf-8")
    motif = re.search(
        r"^      - name: Garde-fou.*?\n        run: \|\n(.*?)(?=\n      - name:|\n  # ─|\Z)",
        texte,
        flags=re.S | re.M,
    )
    assert motif, (
        "Aucun step nommé « Garde-fou » avec un `run: |` dans "
        f"{WORKFLOW.name} : le garde-fou de #460 a été renommé ou retiré."
    )
    lignes = [
        ligne[INDENTATION_RUN:] if ligne.startswith(" " * INDENTATION_RUN) else ligne
        for ligne in motif.group(1).split("\n")
    ]
    return "\n".join(lignes)


def _corpus(repertoire: Path, interventions_par_profil: dict[str, int]) -> None:
    """Écrit un corpus pivot minimal : seul `interventions` est lu."""
    profils = repertoire / "pivot_data" / "profiles"
    profils.mkdir(parents=True, exist_ok=True)
    for slug, nombre in interventions_par_profil.items():
        (profils / f"{slug}.pivot.json").write_text(
            json.dumps(
                {"id": f"nosdeputes:{slug}", "interventions": [{"sujet": str(i)} for i in range(nombre)]},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )


def _executer(tmp_path: Path, *, overwrite: str, interventions: str,
              corpus: dict[str, int]) -> tuple[int, str, str]:
    """Lance le step dans un corpus jetable. Retourne (code, sortie, résumé)."""
    _corpus(tmp_path, corpus)
    resume = tmp_path / "step_summary.md"
    resume.write_text("", encoding="utf-8")
    acheve = subprocess.run(
        ["bash", "-c", _script_du_garde_fou()],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env={
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "OVERWRITE": overwrite,
            "INTERVENTIONS": interventions,
            "GITHUB_STEP_SUMMARY": str(resume),
        },
    )
    return acheve.returncode, acheve.stdout + acheve.stderr, resume.read_text(encoding="utf-8")


CORPUS_TEMOIN = {"jerome-guedj": 395, "marine-le-pen": 302, "gabriel-attal": 5, "sans-interventions": 0}
TOTAL_TEMOIN = 702
PROFILS_TEMOIN = 3


def test_le_step_existe_dans_prepare_an_matrix():
    """Garde-fou du garde-fou. Le step doit vivre dans `prepare-an-matrix` :
    ce job n'a aucun `needs`, il démarre donc immédiatement et l'avertissement
    est lisible avant que la moindre extraction ait consommé du runner. Le
    déplacer en aval le rendrait exact mais inutile."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.index("\n  prepare-an-matrix:")
    fin = texte.index("\n  extract-an:")
    bloc = texte[debut:fin]
    assert "- name: Garde-fou" in bloc, (
        "Le garde-fou de #460 n'est plus dans `prepare-an-matrix`. Un job avec "
        "`needs:` avertirait après coup, une fois le runner déjà engagé."
    )


def test_avertit_quand_overwrite_ecrase_des_interventions(tmp_path):
    """Le cas de #460 lui-même : c'est ce run-là qui a effacé 789 interventions."""
    code, sortie, resume = _executer(
        tmp_path, overwrite="true", interventions="false", corpus=CORPUS_TEMOIN
    )
    assert "::warning::" in sortie, (
        "Aucun avertissement alors que existing_profiles=overwrite et "
        f"extract_interventions=false détruiraient {TOTAL_TEMOIN} interventions."
    )
    assert str(TOTAL_TEMOIN) in sortie, (
        "L'avertissement ne chiffre pas la perte. Un signal non chiffré est "
        "exactement ce que la §3 de la quality gate produisait déjà, et que "
        "personne n'a lu (#460)."
    )
    assert str(TOTAL_TEMOIN) in resume, "Le résumé de run ne chiffre pas la perte."
    assert "jerome-guedj (395)" in resume, (
        "Le résumé ne nomme pas les profils concernés : impossible de savoir "
        "si la perte est celle qu'on croit."
    )
    assert code == 0, (
        "Le garde-fou fait échouer le job. Le choix documenté est un "
        "avertissement : le refus dur est en aval, sur la perte mesurée "
        "(audit_diff_profils.py), pas sur une prédiction."
    )


@pytest.mark.parametrize(
    "overwrite, interventions, raison",
    [
        ("false", "false", "fusion additive : rien n'est écrasé, "
                           "y compris en cold_start, qui ne purge que le cache (#578)"),
        ("true", "true", "l'écrasement est accompagné de la collecte"),
        ("false", "true", "ni écrasement ni saut de collecte"),
    ],
)
def test_silencieux_quand_rien_n_est_menace(tmp_path, overwrite, interventions, raison):
    """Un garde-fou qui crie à tort se fait ignorer — c'est le mécanisme même
    par lequel la §3 de la quality gate est devenue inaudible (#460)."""
    _, sortie, resume = _executer(
        tmp_path, overwrite=overwrite, interventions=interventions, corpus=CORPUS_TEMOIN
    )
    assert "::warning::" not in sortie, f"Avertissement injustifié alors que {raison}."
    assert resume.strip() == "", f"Résumé de run pollué alors que {raison}."


def test_silencieux_si_le_corpus_ne_porte_aucune_intervention(tmp_path):
    """La propriété qui manquait à la quality gate : un signal de **variation**,
    pas de **niveau**. Sur un corpus sans interventions committées, l'écrasement
    ne détruit rien et le garde-fou se tait — c'est l'exact symétrique du
    « 209 profils sous le seuil » qui ne disait rien de ce qui avait changé."""
    _, sortie, resume = _executer(
        tmp_path, overwrite="true", interventions="false",
        corpus={"a": 0, "b": 0},
    )
    assert "::warning::" not in sortie, (
        "Avertissement alors qu'aucune intervention n'est committée : le "
        "garde-fou mesure un niveau, pas une variation."
    )
    assert resume.strip() == ""


def test_la_condition_suit_le_calcul_de_merge_flag():
    """Le garde-fou ne vaut que s'il se déclenche exactement quand `--no-merge`
    est levé. Si la condition des jobs d'extraction change sans que celle-ci
    suive, l'avertissement devient muet ou bavard — sans que rien ne casse."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    condition_merge = '[[ "$OVERWRITE" == "true" ]] && MERGE_FLAG=(--no-merge)'
    assert condition_merge in texte, (
        "Le calcul de MERGE_FLAG a changé de forme : revoir la condition du "
        "garde-fou de #460, qui la reproduit en négatif."
    )
    assert '[[ "$OVERWRITE" != "true" ]]' in _script_du_garde_fou(), (
        "La condition du garde-fou n'est plus le négatif de celle de MERGE_FLAG."
    )
    # Et `OVERWRITE` vaut exactement l'axe 1 du formulaire (#578) : si les deux
    # divergeaient, le garde-fou avertirait sur un autre mode que celui qui
    # écrase.
    assert "OVERWRITE: ${{ inputs.existing_profiles == 'overwrite' }}" in texte
