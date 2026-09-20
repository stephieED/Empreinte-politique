"""Garde-fou #485 : le contrôle d'intégrité référentielle reste branché avant le commit.

Depuis #432 (votes) et #431 (amendements), un profil ne garde qu'une **clé** et
le détail vit dans un index partagé : la donnée est passée d'un état
auto-suffisant à un état **référentiel**, et une clé qui ne résout pas produit
un vote publié **sans objet**.

`audit_diff_profils` ne peut pas le voir : il compare un avant et un après, donc
une variation dans le temps. Ce contrôle-ci vérifie une **invariance dans un
état donné** — deux couches d'un même état régénérées de façon
cohérente-mais-fausse ne bougent aucun compteur.

Ces tests verrouillent l'appel et, surtout, le **cloisonnement des deux
tolérances** : `allow_declared_losses` ne doit jamais désarmer ce contrôle-ci.
#470 a documenté le piège inverse — un contrôle grossier rendu bloquant force
l'opérateur à relancer avec la tolérance, ce qui désarme du même coup les
contrôles précis.

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"
SCRIPT = "src/audit_integrite_referentielle.py"


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


#: Ancré sur le NOM du step, pas sur l'appel au script : `--tolerer-orphelins`
#: est posé quelques lignes AVANT l'appel, dans le tableau `TOLERANCE`, et une
#: tranche démarrée à l'appel le raterait — en concluant à tort qu'il n'y est pas.
NOM_STEP = "- name: Intégrité référentielle de pivot_data"


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
        "Le contrôle d'intégrité référentielle n'est plus appelé : une clé qui "
        "ne résout pas publierait un vote sans objet, sans qu'aucun compteur ne "
        "bouge (#485)."
    )


def test_le_controle_precede_le_commit():
    """Après le commit, il ne protégerait plus rien : la donnée serait publiée."""
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find(SCRIPT)
    rang_commit = code.find("git commit")
    assert rang_controle >= 0 and rang_commit >= 0
    assert rang_controle < rang_commit


def test_le_controle_suit_l_ecriture_des_index():
    """L'index doit être écrit avant d'être vérifié.

    Les deux index sont produits par les passes `generate_all_profiles.py
    --pivot-only`, et `cohesion_votes` par la génération des profils de groupe.
    Vérifier avant, c'est contrôler un état que le run n'a pas fini d'écrire.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    rang_controle = code.find(SCRIPT)
    for producteur in ("generate_all_profiles.py", "generate_group_profiles.py"):
        rang = code.find(producteur)
        assert 0 <= rang < rang_controle, (
            f"`{producteur}` ne s'exécute plus avant le contrôle d'intégrité : "
            "celui-ci vérifierait un index pas encore écrit.")


def test_une_reference_orpheline_annule_le_commit():
    """Sans `exit 1`, le step afficherait le rapport et laisserait committer."""
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "exit 1" in step
    assert "REFERENCES_ORPHELINES" in step, (
        "Le message d'erreur doit être repérable dans les logs : c'est ce qui "
        "distingue un échec diagnostiquable d'un job rouge."
    )


def test_le_controle_porte_sur_tout_pivot_data():
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "--pivot-dir pivot_data" in step
    assert "--sans-amendements" not in step, (
        "L'index des amendements est shardé, donc le plus exposé à une "
        "publication partielle : c'est la couche qu'il faut le moins sauter."
    )


def test_la_tolerance_est_distincte_de_celle_du_controle_de_perte():
    """LE point de ces tests.

    `allow_declared_losses` désarme le contrôle de perte. S'il désarmait aussi
    celui-ci, déclarer une perte légitime publierait au passage des références
    cassées — exactement l'échange que #470 refuse.
    """
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "--tolerer-orphelins" in step
    assert "--tolerer-pertes" not in step
    assert "allow_declared_losses" not in step, (
        "Le contrôle d'intégrité lit la tolérance du contrôle de perte : une "
        "perte déclarée désarmerait aussi la détection des références "
        "orphelines (#470, #485)."
    )
    assert "inputs.allow_broken_references" in step


def test_la_tolerance_existe_et_est_desactivee_par_defaut():
    texte = WORKFLOW.read_text(encoding="utf-8")
    debut = texte.find("allow_broken_references:")
    assert debut > 0, "input `allow_broken_references` absent"
    bloc = texte[debut:][:1200]
    assert "default: false" in bloc
    # La version précédente exigeait la mention « DISTINCT from
    # allow_declared_losses ». Elle renvoyait au NOM d'un autre input — or
    # GitHub affiche la description comme libellé du champ et masque le nom :
    # le renvoi désignait quelque chose d'invisible à l'écran. La distinction
    # doit donc se lire dans le texte lui-même, par sa marque de gravité.
    assert "EMERGENCY ONLY" in bloc, (
        "Le libellé doit porter sa propre marque de gravité : c'est ce qui le "
        "sépare de la tolérance du contrôle de perte, qui dit « DANGEROUS ». "
        "Sans elle, les deux seront confondus à la première relecture."
    )


def test_le_rapport_est_joint_au_resume_de_job():
    """Un rapport qu'il faut aller télécharger n'est pas lu — et c'est en échec
    qu'on en a le plus besoin."""
    step = _step_du_controle(_sans_commentaires(_bloc_job("merge-and-pivot")))
    assert "GITHUB_STEP_SUMMARY" in step


def test_le_controle_de_perte_reste_branche_lui_aussi():
    """Les deux contrôles sont complémentaires, pas alternatifs.

    Celui-ci ne voit pas une perte d'entrées ; celui de #460/#470 ne voit pas une
    rupture de correspondance. Remplacer l'un par l'autre rouvrirait un trou.
    """
    code = _sans_commentaires(_bloc_job("merge-and-pivot"))
    assert "src/audit_diff_profils.py" in code
    assert code.find("src/audit_diff_profils.py") < code.find(SCRIPT)
