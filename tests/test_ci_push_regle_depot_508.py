"""Garde-fou #508 : le push de données survit à un check requis, et nomme sa cause.

Un ruleset de dépôt applique ses `required_status_checks` **aux pushs directs**,
pas seulement aux PR. `merge-and-pivot` pousse sur `main` sans PR : aucun check
ne peut être attaché au commit qu'il fabrique, donc la règle lui est
*insatisfiable*. Le 20/08/2026, elle a fait rejeter trois fois de suite un run
qui avait produit toutes ses données, et le check a dû être retiré du dépôt.

Deux choses sont verrouillées ici, et elles ne se remplacent pas :

1. **l'identité du push** — le checkout de ce job porte une clé de déploiement,
   seul type d'acteur qui puisse figurer dans les `bypass_actors` d'un ruleset
   sur un dépôt personnel ;
2. **le diagnostic** — un rejet par une règle ne doit plus être rapporté comme
   de la « concurrence soutenue ». C'est ce que le run 32398799010 a imprimé,
   trois lignes sous un `remote:` qui nommait la règle.

Volontairement sans PyYAML (absent de requirements.txt), comme les autres
gardes-fous de workflow de ce dépôt.

Voir docs/decisions/push-donnees-cle-de-deploiement-508.md.
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


BLOC = _sans_commentaires(_bloc_job("merge-and-pivot"))


# ── 1. L'identité du push ────────────────────────────────────────────────────

def test_le_checkout_de_merge_and_pivot_porte_la_cle_de_deploiement():
    """Sans `ssh-key`, le push repart sous le GITHUB_TOKEN — l'identité que le
    ruleset ne peut pas exempter sur un dépôt personnel."""
    assert re.search(
        r"uses:\s*actions/checkout@v\d+\s*\n\s*with:\s*\n\s*ssh-key:\s*\$\{\{\s*secrets\.DATA_PUSH_SSH_KEY\s*\}\}",
        BLOC,
    ), (
        "le checkout de merge-and-pivot doit porter "
        "`ssh-key: ${{ secrets.DATA_PUSH_SSH_KEY }}` : c'est cette identité, et "
        "pas le GITHUB_TOKEN, qui figure dans les bypass_actors du ruleset (#508)."
    )


def test_le_nom_du_secret_est_le_seul_du_job():
    """Un second secret de push signifierait deux identités possibles, donc une
    seule inscrite dans le ruleset et une qui se ferait rejeter.

    Ce que le test compte, ce sont les `secrets.` : un step qui a besoin du
    jeton du run pour LIRE (l'inventaire des artifacts, #786) le prend par
    `github.token`, qui n'est pas une identité de push et n'entre donc pas dans
    ce décompte. `test_le_jeton_du_run_ne_sert_jamais_a_pousser`, dans
    `test_transport_artifacts_786.py`, verrouille cette moitié-là.
    """
    secrets = set(re.findall(r"secrets\.([A-Z0-9_]+)", BLOC))
    assert secrets == {"DATA_PUSH_SSH_KEY"}, (
        f"secrets attendus dans merge-and-pivot : DATA_PUSH_SSH_KEY seul ; trouvés : {sorted(secrets)}"
    )


# ── 2. Le diagnostic ─────────────────────────────────────────────────────────

def test_un_rejet_par_regle_sort_de_la_boucle_de_retry():
    """Un ruleset ne cède pas au rebase : reboucler répète l'erreur à
    l'identique (trois fois, le 20/08). La détection doit précéder le rebase."""
    detection = re.search(r"grep\s+-qi\s+'GH013", BLOC)
    assert detection, "la sortie du push doit être relue pour y reconnaître un rejet GH013 (#508)"

    rupture = BLOC.index("push_status=\"regle\"", detection.end())
    rebase = BLOC.index("git rebase --autostash")
    assert rupture < rebase, (
        "le rejet par une règle doit sortir de la boucle AVANT la tentative de rebase : "
        "rebaser puis repousser ne fait que se faire rejeter à nouveau."
    )


def test_le_statut_du_push_est_lu_sur_le_code_de_retour_pas_a_travers_un_pipe():
    """`if git push | tee log` teste le statut de `tee`, toujours nul : le rejet
    passerait pour un succès et le job committerait dans le vide."""
    assert "git push >" in BLOC, "la sortie du push doit être redirigée vers un fichier, pas pipée"
    assert re.search(r"push_code=\$\?", BLOC), "le code de retour du push doit être capturé sur $?"
    assert not re.search(r"git push[^\n]*\|\s*tee", BLOC), (
        "pipe vers tee interdit ici : il masque le code de retour de git push"
    )


def test_le_message_de_rejet_par_regle_ne_conclut_pas_a_la_concurrence():
    """Le défaut d'origine n'était pas l'absence de message, c'était le mauvais
    message : « concurrence soutenue » imprimé sur un rejet de ruleset. Le mot
    « concurrence » reste autorisé — le message l'emploie pour écarter cette
    piste ; ce qui est interdit, c'est la conclusion."""
    branche = re.search(
        r'if \[ "\$push_status" = "regle" \]; then\n(.*?)\n\s*elif ', BLOC, flags=re.DOTALL
    )
    assert branche, "la boucle de push doit traiter le cas `regle` à part (#508)"
    message = branche.group(1)
    assert "::error::" in message
    assert "concurrence soutenue" not in message.lower(), (
        "un rejet par une règle de dépôt n'est pas de la concurrence soutenue — "
        "c'est la confusion exacte que le run 32398799010 a publiée."
    )
    assert "GH013" in message and "DATA_PUSH_SSH_KEY" in message, (
        "le message doit nommer la piste utile : le code de rejet et le secret à vérifier."
    )


# ── 3. La publication reste indépendante de l'identité qui pousse ────────────

def test_le_declenchement_explicite_de_deploy_pages_est_conserve():
    """Sous clé de déploiement, le push émet un événement et les `paths:` de
    deploy-pages.yml suffiraient — mais seulement tant que la clé est là. Le
    `gh workflow run` de #416 est le seul chemin qui ne dépende pas de
    l'identité du push ; le retirer rendrait la panne #416 silencieuse."""
    assert "gh workflow run deploy-pages.yml" in BLOC, (
        "le déclenchement explicite de deploy-pages.yml doit rester (#416/#508)"
    )
    condition = re.search(
        r"if:\s*steps\.commit\.outputs\.pushed == 'true' && github\.ref == 'refs/heads/main'", BLOC
    )
    assert condition, (
        "la garde du déploiement reste `pushed == true` sur main, et rien de plus : "
        "la conditionner à l'identité du push réintroduirait la panne #416."
    )
