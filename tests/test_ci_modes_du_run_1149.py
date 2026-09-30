"""#1149 — les deux modes du run se lisent en un seul endroit.

Un déclenchement `schedule` ne reçoit **aucun** input (#1054) : les cases
`collect_interventions` et `collect_dossiers_legislatifs` y valent `false`, et le
run nocturne ne collectait donc ni les prises de parole ni les textes portés du
roster. La couverture des interventions n'avançait jamais seule — c'est ce qui a
laissé la fiche d'Olivier Becht en régime « extrait » jusqu'au 26/09/2026.

`epingler-le-code`, qui précède tous les jobs concernés, calcule les deux modes
une fois et les publie ; le reste du workflow lit ses sorties.

## Pourquoi une sortie de job, et pas l'expression répétée seize fois

Parce que **des clés de cache en dépendent**. Une occurrence oubliée ferait
restaurer l'entrée d'un autre mode, et `actions/cache` sauterait la sauvegarde de
ce que le run vient de construire : c'est #424, #505 et #657, trois fois le même
défaut, à chaque fois des centaines de Mo retéléchargés sans que rien ne le dise.
Une définition unique ne peut pas diverger d'elle-même ; seize occurrences, si.

Ce fichier refuse donc toute lecture directe de `inputs.collect_*` ailleurs que
dans cette définition.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"

#: Les deux sorties, et l'expression exacte que chacune doit porter.
MODES = {
    "interventions": "inputs.collect_interventions || github.event_name == 'schedule'",
    "dossiers_legislatifs": "inputs.collect_dossiers_legislatifs || github.event_name == 'schedule'",
}

#: Les jobs qui lisent ces sorties doivent en dépendre, sinon l'expression
#: s'évalue à vide et le mode retombe silencieusement sur « non ».
JOBS_LECTEURS = ("prepare-an-matrix", "extract-an", "extract-roster-groupes")


def _yaml() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def _lignes_hors_commentaire():
    """Le YAML sans ses commentaires — qui **citent** les inputs qu'ils
    expliquent, et feraient échouer ce garde sur sa propre justification."""
    for numero, ligne in enumerate(_yaml().split("\n"), 1):
        if not ligne.lstrip().startswith("#"):
            yield numero, ligne


def _bloc_job(nom: str) -> str:
    texte = _yaml()
    debut = re.search(rf"^  {re.escape(nom)}:\s*$", texte, re.MULTILINE)
    assert debut, f"Job `{nom}` introuvable."
    suite = re.search(r"^  [a-z][a-z0-9-]*:\s*$", texte[debut.end():], re.MULTILINE)
    return texte[debut.end():] if not suite else texte[debut.end(): debut.end() + suite.start()]


def test_les_deux_modes_sont_publies_par_le_job_de_tete():
    bloc = _bloc_job("epingler-le-code")
    for sortie, expression in MODES.items():
        attendu = f"{sortie}: ${{{{ {expression} }}}}"
        assert attendu in bloc, (
            f"`epingler-le-code` ne publie plus `{sortie}` sous la forme "
            f"attendue :\n  {attendu}\n"
            "Sans `github.event_name == 'schedule'`, un run programmé retombe "
            "sur le mode par défaut et ne collecte rien de plus (#1054)."
        )


def test_aucun_job_ne_lit_les_inputs_directement():
    """La règle du lot. Une seule définition, et elle est ailleurs."""
    definition = _bloc_job("epingler-le-code")
    fautes = [
        (numero, ligne.strip()[:90])
        for numero, ligne in _lignes_hors_commentaire()
        if re.search(r"inputs\.collect_(interventions|dossiers_legislatifs)", ligne)
        and ligne not in definition
    ]
    assert not fautes, (
        "Ces lignes lisent un input de collecte directement, au lieu des sorties "
        "d'`epingler-le-code` :\n"
        + "\n".join(f"  ligne {n} : {t}" for n, t in fautes)
        + "\n\nSur un déclenchement `schedule` elles vaudront `false` quoi qu'il "
        "arrive. Si la ligne est une CLÉ DE CACHE, le run restaurera en plus "
        "l'entrée d'un autre mode et ne sauvegardera pas la sienne (#424, #505, "
        "#657)."
    )


def test_les_jobs_lecteurs_dependent_du_job_de_tete():
    """Une sortie lue sans `needs:` s'évalue à la chaîne vide — donc à « non »,
    sans erreur ni log. Le mode se perdrait exactement comme il se perdait avant
    ce lot."""
    for job in JOBS_LECTEURS:
        bloc = _bloc_job(job)
        if "needs.epingler-le-code.outputs." not in bloc:
            continue
        needs = re.search(r"\n    needs: (.+)\n", bloc)
        assert needs and "epingler-le-code" in needs.group(1), (
            f"`{job}` lit une sortie d'`epingler-le-code` sans en dépendre : "
            "elle s'évaluerait à vide."
        )


def test_les_seize_lectures_passent_toutes_par_les_sorties():
    """Garde-fou du garde-fou : si plus rien ne lisait ces sorties, le test
    ci-dessus passerait pour une mauvaise raison."""
    texte = _yaml()
    for sortie in MODES:
        n = texte.count(f"needs.epingler-le-code.outputs.{sortie}")
        assert n >= 2, (
            f"`{sortie}` n'est lue que {n} fois dans le workflow : le mode ne "
            "commande plus grand-chose, ou les lectures sont reparties dans les "
            "inputs."
        )


def test_le_motif_attrape_ce_qui_a_casse_et_epargne_les_commentaires():
    """Sans ce test, un garde qui saute les commentaires peut se mettre à tout
    sauter — et ne plus rien voir."""
    lignes = dict(_lignes_hors_commentaire())
    assert lignes, "plus aucune ligne de code n'est examinée"
    # Les commentaires du workflow CITENT les inputs qu'ils expliquent : ils
    # doivent rester hors du champ, sinon le garde échoue sur sa propre prose.
    tous = _yaml().split("\n")
    assert len(lignes) < len(tous), "aucun commentaire n'a été écarté"
    cites = [l for l in tous
             if l.lstrip().startswith("#")
             and "inputs.collect_" in l]
    assert cites, (
        "aucun commentaire ne cite plus `inputs.collect_*` : soit le fichier a "
        "changé, soit l'exception ne sert plus à rien et peut tomber."
    )
