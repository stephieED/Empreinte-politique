"""Garde-fou #545 : le contrôle « collecté vs publié, liste par liste » reste
branché, au bon endroit, et n'est désarmé par aucune des trois autres tolérances.

Un contrôle correct placé trop tôt est un contrôle faux — même raison qu'en
#511 : entre la passe pivot des candidats déclarés et la passe pivot
roster-driven, un membre de roster n'a pas encore de pivot. Ces tests
verrouillent l'emplacement autant que la présence de l'appel.

Ils verrouillent aussi le **cloisonnement des quatre tolérances** :
`allow_declared_losses` (#460/#470), `allow_broken_references` (#485) et
`allow_unpublished_profiles` (#511) ne doivent pas désarmer celle-ci. #470 a
documenté le piège inverse — rendre bloquant un contrôle grossier force
l'opérateur à relancer avec une tolérance, qui désarme du même coup les
contrôles précis.

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SCRIPT = "src/audit_collecte_vs_publie.py"


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


#: Ancré sur le NOM du step et pas sur l'appel : `--tolerer-ecarts` est posé
#: quelques lignes AVANT, dans le tableau `TOLERANCE`.
NOM_STEP = "- name: Collecté vs publié, liste par liste"


def _step_du_controle(code: str) -> str:
    debut = code.find(NOM_STEP)
    assert debut >= 0, f"step `{NOM_STEP}` absent du job"
    bloc = code[debut:]
    suivant = bloc.find("- name:", 1)
    step = bloc[:suivant] if suivant > 0 else bloc
    assert SCRIPT in step, "le step ne lance plus le contrôle"
    return step


def test_le_controle_est_appele_dans_merge_and_pivot():
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert SCRIPT in code, (
        "Le contrôle « collecté vs publié » n'est plus appelé : une liste "
        "publiée qui porte moins que ce que la collecte a rendu redeviendrait "
        "invisible, et le run se conclurait en succès — c'est le run "
        "33100214165, 7 767 interventions collectées et 891 publiées (#545)."
    )


def test_le_controle_precede_le_commit():
    """Après le commit, il ne protégerait plus rien."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find(SCRIPT)
    rang_commit = code.find("git commit")
    assert rang_controle >= 0 and rang_commit >= 0
    assert rang_controle < rang_commit


def test_le_controle_suit_les_deux_passes_de_normalisation_pivot():
    """LE test d'emplacement, même raison qu'en #511.

    Entre les deux passes `--pivot-only`, un membre de roster est légitimement
    sans pivot : y brancher le contrôle rapporterait des écarts qui n'existent
    pas encore.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find(SCRIPT)
    assert rang_controle > 0

    rang_fusion = code.find("src/merge_profile.py")
    assert 0 <= rang_fusion < rang_controle, (
        "la fusion des profils bruts doit précéder le rapprochement : sinon "
        "`raw_data/profiles` n'a pas encore reçu les profils du run.")

    passes_pivot = [m.start() for m in re.finditer(r"--pivot-only", code)]
    assert len(passes_pivot) >= 2, (
        "les deux passes pivot attendues (candidats déclarés, puis roster) ne "
        "sont plus toutes les deux dans le job.")
    assert max(passes_pivot) < rang_controle, (
        "le contrôle s'exécute avant la dernière passe pivot : il compterait "
        "comme non publié ce que cette passe est justement en train de publier.")


def test_un_ecart_annule_le_commit():
    """Sans `exit 1`, le step afficherait le rapport et laisserait committer —
    c'est-à-dire exactement le run 33100214165, conclu en succès."""
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "exit 1" in step
    assert "ECART_COLLECTE_PUBLICATION" in step, (
        "Le message d'erreur doit être repérable dans les logs : c'est ce qui "
        "distingue un échec diagnostiquable d'un job rouge."
    )


def test_le_controle_porte_sur_les_deux_repertoires_de_profils():
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "--raw-dir raw_data/profiles" in step
    assert "--pivot-dir pivot_data/profiles" in step


def test_la_tolerance_est_distincte_des_trois_autres():
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "--tolerer-ecarts" in step
    assert "--tolerer-pertes" not in step
    assert "--tolerer-orphelins" not in step
    assert "--tolerer-non-publies" not in step
    assert "allow_declared_losses" not in step
    assert "allow_broken_references" not in step
    assert "allow_unpublished_profiles" not in step
    assert "inputs.allow_publication_gaps" in step


def test_la_tolerance_existe_et_est_desactivee_par_defaut():
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.find("allow_publication_gaps:")
    assert debut > 0, "input `allow_publication_gaps` absent"
    bloc = texte[debut:][:1200]
    assert "default: false" in bloc
    # Même exigence qu'en #485 et #511 : GitHub affiche la description comme
    # libellé du champ et masque le nom de l'input. La gravité doit se lire dans
    # le texte lui-même, pas dans un renvoi vers un nom invisible à l'écran.
    assert "BREAK GLASS" in bloc, (
        "Le libellé doit porter sa propre marque de gravité, distincte de "
        "« INTENDED REMOVAL » (#470), « EMERGENCY ONLY » (#485) et "
        "« LAST RESORT » (#511)."
    )


def test_les_quatre_marques_de_gravite_restent_distinctes():
    """Quatre tolérances, quatre libellés : deux inputs qui portent la même
    marque ne se distinguent plus à l'écran, où seul le libellé s'affiche."""
    texte = WORKFLOW.read_text(encoding="utf-8")
    for marque in ("INTENDED REMOVAL", "EMERGENCY ONLY", "LAST RESORT",
                   "BREAK GLASS"):
        assert texte.count(f'"{marque}:') == 1, marque


def test_le_rapport_est_joint_au_resume_de_job():
    """Un rapport qu'il faut aller télécharger n'est pas lu — et c'est en échec
    qu'on en a le plus besoin."""
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "GITHUB_STEP_SUMMARY" in step


def test_les_trois_autres_controles_restent_branches():
    """Les quatre sont complémentaires, pas alternatifs. Aucun des trois autres
    n'était en défaut sur #540 : c'est l'espace ENTRE eux qui n'était pas
    couvert."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "src/audit_diff_profils.py" in code
    assert "src/audit_integrite_referentielle.py" in code
    assert "src/audit_collecte_non_publiee.py" in code
