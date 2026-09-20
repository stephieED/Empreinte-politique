"""Garde-fou #460 : le contrôle de perte doit rester branché avant le commit.

Le 19/08/2026, le run 32288588518 a effacé les 789 interventions du corpus, et
avec elles 647 `tags_thematiques` et 497 tags agrégés — des champs **publiés**.
Personne ne l'a vu.

Ni la collecte ni l'écrasement n'étaient fautifs : `extract_interventions=false`
saute la collecte (voulu), `existing_profiles=overwrite` réécrit sans ce qui n'a pas
été collecté (voulu aussi — c'est ce qui propage une correction de clé). Deux
comportements corrects dont la combinaison détruit une donnée acquise.

La quality gate ne pouvait pas l'attraper : elle mesure un **niveau**, pas une
**variation**. Sa §3 a affiché « 209 profils sous le seuil » sur 209 profils.

`audit_diff_profils.py` mesure la variation. Il existait, il était documenté
« indispensable avant tout commit de régénération » — et il n'était appelé par
aucun workflow ni aucun script. Ces tests verrouillent l'appel : sans eux, il
pourrait se débrancher exactement comme il ne s'était jamais branché.

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


def _bloc_job(nom: str) -> str:
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, flags=re.MULTILINE)
    assert debut, f"job `{nom}` absent de {WORKFLOW.name}"
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], flags=re.MULTILINE)
    return texte[debut.end(): debut.end() + suite.start()] if suite else texte[debut.end():]


def _sans_commentaires(bloc: str) -> str:
    """Les rationales de ce dépôt citent abondamment les commandes qu'elles
    expliquent : les lire comme du workflow serait un faux positif permanent."""
    return "\n".join(l for l in bloc.split("\n") if not l.lstrip().startswith("#"))


def test_le_controle_de_perte_est_appele_dans_merge_and_pivot():
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "src/audit_diff_profils.py" in code, (
        "Le contrôle de perte n'est plus appelé. C'est l'état exact qui a laissé "
        "passer l'effacement des 789 interventions (#460)."
    )


def test_le_controle_precede_le_commit():
    """Après le commit, il ne protégerait plus rien : la donnée serait publiée."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find("src/audit_diff_profils.py")
    rang_commit = code.find("git commit")
    assert rang_controle >= 0 and rang_commit >= 0
    assert rang_controle < rang_commit, (
        "Le contrôle de perte s'exécute après le commit : il constaterait une "
        "perte déjà publiée."
    )


def test_le_controle_compare_au_checkout_du_job():
    """`--ref HEAD` et non `origin/main` : HEAD est le commit checkouté, donc
    l'état d'avant CE run. C'est aussi le seul qui marche avec le
    `fetch-depth: 1` par défaut d'actions/checkout, et le seul juste sur un run
    lancé hors main (#413 §2)."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "--ref HEAD" in code
    assert "--ref origin/main" not in code


def test_une_perte_annule_le_commit():
    """Le cœur du garde-fou : sans `exit 1`, le step afficherait le rapport et
    laisserait committer — un signal de plus que personne ne lirait."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    bloc = code[code.find("src/audit_diff_profils.py"):]
    bloc = bloc[: bloc.find("- name:", 1) if bloc.find("- name:", 1) > 0 else len(bloc)]
    assert "exit 1" in bloc
    assert "PERTE_PROFILS_NON_DECLAREE" in bloc, (
        "Le message d'erreur doit être repérable dans les logs : c'est ce qui "
        "distingue un échec diagnostiquable d'un job rouge."
    )


def test_la_tolerance_existe_et_est_desactivee_par_defaut():
    """Une perte peut être légitime — la régénération de #450 en attendait une.
    Elle doit alors être DÉCLARÉE, pas subie : l'input laisse une trace dans les
    paramètres du run, là où un contrôle simplement absent n'en laisse aucune."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    bloc = texte[texte.find("allow_declared_losses:"):][:600]
    assert bloc, "input `allow_declared_losses` absent"
    assert "default: false" in bloc, "la tolérance doit être désactivée par défaut"
    assert "--tolerer-pertes" in _sans_commentaires(_bloc_job("merge-and-pivot"))


def test_le_rapport_est_joint_au_resume_de_job():
    """Un rapport qu'il faut aller télécharger n'est pas lu — et c'est en échec
    qu'on en a le plus besoin."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "GITHUB_STEP_SUMMARY" in code[code.find("src/audit_diff_profils.py"):]
