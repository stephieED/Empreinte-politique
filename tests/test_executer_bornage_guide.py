"""#576 : le runner guidé du bornage — ce qu'il refuse, et dans quel ordre.

`scripts/executer_bornage_guide.sh` porte les gestes IRRÉVERSIBLES que
`scripts/borner_historique_donnees.sh` s'interdit depuis #551. On ne peut donc
pas le dérouler pour le tester : la validation de bout en bout se fait sur un
dépôt jetable, à la main, et elle est hors de portée d'une suite de tests.

Ce fichier teste ce qui reste — et c'est l'essentiel de ce qu'un runner apporte :

  - **les confirmations**. Le script est SOURÇABLE : exécuté il déroule, sourcé
    il ne fait que définir ses fonctions. `_confirmer_phrase` se teste donc pour
    de vrai, avec une saisie au bout d'un tuyau, sans approcher d'un `git push` ;
  - **l'ordre**, qui est la seule propriété dont l'erreur est irrattrapable :
    archiver après avoir coupé ne rattrape rien ;
  - **les préconditions**, et le fait qu'un contournement se DISE et se
    CONSIGNE — le second écart de la répétition du 28/08/2026 était exactement
    ça : passer outre un verdict MANQUANTS, à bon droit, sans trace ;
  - **les six corrections de procédure** que la répétition a rendues (tags,
    `refs/pull/*`, `dev` repointée, quel dépôt, coût d'entrée, durée de vie du
    tag). Ce sont des recherches de motif, et elles valent ce que valent les
    recherches de motif : elles attrapent la disparition d'un point, pas sa
    dénaturation. C'est la même limite que `test_borner_historique_donnees.py`,
    et la même raison de les garder.

Aucun test de ce fichier ne pousse, ne supprime de ref, ni ne sort sur le
réseau (AGENTS.md §3). Le seul `gh` invoqué est un faux, posé dans `PATH`, et
les dépôts distants sont des `--bare` fabriqués dans `tmp_path`.
"""

import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
RUNNER = RACINE / "scripts" / "executer_bornage_guide.sh"
BORNAGE = RACINE / "scripts" / "borner_historique_donnees.sh"

PHRASE_PUSH = "je reecris main de force"
PHRASE_REFS = "je supprime les refs qui reepinglent l ancien historique"
PHRASE_DEROGATION = "je passe outre et j en prends la responsabilite"


def _texte() -> str:
    return RUNNER.read_text(encoding="utf-8")


def _bash(extrait: str, entree: str = "", cwd=None, env=None):
    """Source le runner — donc SANS le dérouler — puis exécute `extrait`.

    `${BASH_SOURCE[0]}` vaut le chemin du script et `$0` vaut « bash » : la
    garde de fin de fichier ne déclenche pas `_principal`. C'est ce qui rend ce
    fichier possible."""
    complet = dict(os.environ)
    complet.update(env or {})
    return subprocess.run(
        ["bash", "-c", f'source "{RUNNER}"\n{extrait}'],
        input=entree, capture_output=True, text=True,
        cwd=str(cwd) if cwd else None, env=complet,
    )


# ── Le script lui-même ───────────────────────────────────────────────────────


def test_le_runner_existe_est_executable_et_sourçable_sans_rien_faire():
    """Sourcé, il ne doit RIEN dérouler. Si la garde de fin de fichier sautait,
    ce fichier de tests lancerait la procédure de bornage — c'est-à-dire
    exactement ce qu'il existe pour ne pas faire."""
    assert RUNNER.is_file()
    assert RUNNER.stat().st_mode & stat.S_IXUSR, "runner non exécutable"
    res = _bash('echo SOURCÉ')
    assert res.returncode == 0, res.stderr
    assert res.stdout.strip() == "SOURCÉ"
    assert "ÉTAPE" not in res.stderr, "le simple fait de sourcer a déroulé une étape"


def test_lister_les_etapes_ne_fait_rien_et_les_donne_dans_l_ordre():
    res = subprocess.run([str(RUNNER), "--lister"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    positions = [res.stdout.index(f"\n   {n} ") for n in range(1, 8)]
    assert positions == sorted(positions), "les sept étapes ne sont pas dans l'ordre"
    assert "PUSH FORCÉ" in res.stdout and "SUPPRIMER LES AUTRES REFS" in res.stdout


# ── Les confirmations : une phrase, jamais un « y » ─────────────────────────


@pytest.mark.parametrize(
    "saisie",
    [
        "y", "Y", "o", "O", "oui", "yes", "",
        "Je Reecris Main De Force",          # casse
        " je reecris main de force",         # espace en tête
        "je reecris main de force ",         # espace en queue
        "je reecris main",                   # préfixe
        "je reecris main de force!",         # un caractère de trop
    ],
)
def test_une_confirmation_refuse_tout_sauf_la_phrase_exacte(saisie):
    """« Un `y` se tape par réflexe, et c'est précisément le réflexe qu'on veut
    interrompre » (#576). Rogner les espaces ou ignorer la casse rendrait la
    saisie plus facile, donc plus réflexe : la comparaison est stricte, et ces
    onze saisies doivent toutes échouer."""
    res = _bash(
        f'if _confirmer_phrase "{PHRASE_PUSH}" "raison"; then echo PASSE; '
        'else echo REFUSE; fi',
        entree=saisie + "\n",
    )
    assert res.stdout.strip() == "REFUSE", f"« {saisie} » a été accepté"
    assert "Rien n'a été fait" in res.stderr


def test_une_confirmation_accepte_la_phrase_exacte():
    """Le pendant obligatoire : sans lui, « tout refuser » passerait le test
    précédent et le runner ne pourrait plus rien faire."""
    res = _bash(
        f'if _confirmer_phrase "{PHRASE_PUSH}" "raison"; then echo PASSE; '
        'else echo REFUSE; fi',
        entree=PHRASE_PUSH + "\n",
    )
    assert res.stdout.strip() == "PASSE", res.stderr
    assert "CONFIRMÉ" in res.stderr


def test_la_phrase_demandee_nomme_le_geste_et_ne_s_abrege_pas():
    """Une phrase courte redevient un réflexe. Celles-ci nomment ce qu'elles
    autorisent — « reecris main de force », « supprime les refs » — et c'est ce
    qui oblige à les lire avant de les taper."""
    for phrase in (PHRASE_PUSH, PHRASE_REFS):
        assert f'"{phrase}"' in _texte(), f"phrase absente du runner : {phrase}"
        assert len(phrase.split()) >= 5, f"phrase trop courte : {phrase}"
    texte = _texte()
    for etape in ("_etape_4_pousser", "_etape_5_supprimer_les_refs"):
        corps = _corps_de_fonction(texte, etape)
        assert "[o/N]" not in corps and "[y/N]" not in corps, (
            f"{etape} se contente d'un caractère là où #576 exige une phrase"
        )


# ── Les préconditions, et le contournement qui se dit ───────────────────────


def test_une_precondition_remplie_passe_sans_rien_demander():
    res = _bash('if _precondition "toujours vrai" true; then echo PASSE; fi')
    assert res.stdout.strip() == "PASSE"
    assert "PRÉCONDITION OK" in res.stderr


def test_une_precondition_en_echec_arrete_si_la_derogation_est_refusee():
    res = _bash(
        'if _precondition "jamais vrai" false; then echo PASSE; else echo ARRÊT; fi',
        entree="y\n",
    )
    assert res.stdout.strip() == "ARRÊT"
    assert "PRÉCONDITION EN ÉCHEC" in res.stderr
    assert "ARRÊT — précondition" in res.stderr


def test_une_derogation_se_tape_en_toutes_lettres_et_se_consigne(tmp_path):
    """« Si l'opératrice passe outre, il le lui fait dire explicitement et le
    consigne » (#576). C'est le second écart de la répétition du 28/08/2026 :
    passer outre un verdict MANQUANTS, à bon droit, et n'en garder trace que
    dans une conversation."""
    journal = tmp_path / "session.journal"
    res = _bash(
        f'JOURNAL="{journal}"\n'
        'if _precondition "le verdict n\'est pas MANQUANTS" false; '
        'then echo PASSE; else echo ARRÊT; fi',
        entree=PHRASE_DEROGATION + "\n",
    )
    assert res.stdout.strip() == "PASSE"
    consigne = journal.read_text(encoding="utf-8")
    assert "PRÉCONDITION EN ÉCHEC" in consigne
    assert "DÉROGATION" in consigne and "assumé et consigné" in consigne
    assert "MANQUANTS" in consigne, "le journal ne dit pas CE qui a été contourné"


def test_le_journal_horodate_chaque_ligne(tmp_path):
    """« quoi, quand, avec quel résultat » : sans l'horodatage, une trace ne
    permet pas de reconstituer l'ordre — et l'ordre est tout ce qui compte."""
    journal = tmp_path / "j.journal"
    _bash(f'JOURNAL="{journal}"\n_journaliser "un fait"')
    ligne = journal.read_text(encoding="utf-8").strip()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4}\] un fait$", ligne)


# ── L'ordre : la seule erreur irrattrapable ─────────────────────────────────


def test_l_ordre_est_impose_et_l_etape_manquante_est_nommee(tmp_path):
    """« Archiver APRÈS avoir coupé ne rattrape rien. » Demander l'étape 4 sans
    avoir consigné les trois premières doit échouer, et dire lesquelles."""
    journal = tmp_path / "j.journal"
    journal.write_text(
        "[2026-08-29T10:00:00+0000] ÉTAPE 1 — TERMINÉE\n", encoding="utf-8"
    )
    res = _bash(
        f'JOURNAL="{journal}"\n'
        'if _exiger_etapes_precedentes 4; then echo PASSE; else echo ARRÊT; fi'
    )
    assert res.stdout.strip() == "ARRÊT"
    assert "2 3 non terminée" in res.stderr
    assert "archiver APRÈS avoir coupé ne rattrape rien" in res.stderr


def test_l_ordre_laisse_passer_quand_tout_le_precedent_est_termine(tmp_path):
    journal = tmp_path / "j.journal"
    journal.write_text(
        "".join(f"[2026-08-29T10:0{n}:00+0000] ÉTAPE {n} — TERMINÉE\n"
                for n in (1, 2, 3)),
        encoding="utf-8",
    )
    res = _bash(
        f'JOURNAL="{journal}"\n'
        'if _exiger_etapes_precedentes 4; then echo PASSE; else echo ARRÊT; fi'
    )
    assert res.stdout.strip() == "PASSE"


def test_demander_l_etape_4_directement_ne_pousse_rien(tmp_path):
    """Le runner LANCÉ, pas sourcé — et il doit s'arrêter avant tout geste.
    C'est le seul déroulé réel de ce fichier, et il est sans danger : l'ordre
    l'arrête avant la première commande distante."""
    depot = tmp_path / "depot"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(depot)],
                   check=True, capture_output=True)
    journal = tmp_path / "j.journal"
    journal.write_text("", encoding="utf-8")
    res = subprocess.run(
        [str(RUNNER), "--etape", "4", "--journal", str(journal)],
        cwd=str(depot), capture_output=True, text=True, input="",
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    assert res.returncode == 1
    consigne = journal.read_text(encoding="utf-8")
    assert "ARRÊT — étape 4 demandée" in consigne
    assert "push" not in consigne.lower(), "un push a été tenté malgré l'ordre"


# ── Le dépôt qu'on borne (point d de la répétition) ─────────────────────────


@pytest.mark.parametrize(
    "remote",
    [
        "https://github.com/stephieED/test_procedure_bornage_issue_569.git",
        "git@github.com:stephieED/test_procedure_bornage_issue_569.git",
        "https://github.com/stephieED/test_procedure_bornage_issue_569",
    ],
)
def test_le_depot_cible_est_derive_du_remote_pas_supposé(tmp_path, remote):
    """« L'étape 4 doit dire SUR QUEL DÉPÔT vérifier qu'aucun run ne tourne.
    Ambigu dès qu'on répète ailleurs » (#569). Une répétition est exactement le
    moment où « le dépôt » désigne deux choses."""
    depot = tmp_path / "depot"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(depot)],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(depot), "remote", "add", "origin", remote],
                   check=True, capture_output=True)
    res = _bash("_depot_cible", cwd=depot)
    assert res.stdout.strip() == "stephieED/test_procedure_bornage_issue_569"


def _faux_gh(tmp_path, sortie, code=0):
    binaire = tmp_path / "bin"
    binaire.mkdir(exist_ok=True)
    faux = binaire / "gh"
    faux.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "{sortie}"\nexit {code}\n',
                    encoding="utf-8")
    faux.chmod(0o755)
    return {"PATH": f"{binaire}:{os.environ['PATH']}"}


def test_un_run_en_cours_bloque_l_etape_4(tmp_path):
    """Un push forcé qui croise un run fait committer ce run sur un historique
    qui n'existe plus."""
    assert _bash('if _aucun_run_en_cours "o/r"; then echo LIBRE; else echo OCCUPÉ; fi',
                 env=_faux_gh(tmp_path, "2")).stdout.strip() == "OCCUPÉ"
    assert _bash('if _aucun_run_en_cours "o/r"; then echo LIBRE; else echo OCCUPÉ; fi',
                 env=_faux_gh(tmp_path, "0")).stdout.strip() == "LIBRE"


def test_un_gh_muet_ne_vaut_pas_un_feu_vert(tmp_path):
    """Ne pas pouvoir établir qu'aucun run ne tourne n'est pas la même chose
    qu'établir qu'aucun ne tourne — la confusion que #568 corrigeait déjà côté
    archive, sur un axe différent."""
    res = _bash('if _aucun_run_en_cours "o/r"; then echo LIBRE; else echo OCCUPÉ; fi',
                env=_faux_gh(tmp_path, "", code=1))
    assert res.stdout.strip() == "OCCUPÉ"
    assert "impossible d'établir" in res.stderr


# ── Deux scripts, deux contrats ─────────────────────────────────────────────


def _corps_de_fonction(texte: str, nom: str) -> str:
    debut = re.search(rf"^{re.escape(nom)}\(\) \{{$", texte, flags=re.MULTILINE)
    assert debut, f"fonction {nom} introuvable"
    reste = texte[debut.end():]
    fin = re.search(r"^\}$", reste, flags=re.MULTILINE)
    assert fin, f"fin de {nom} introuvable"
    return reste[: fin.start()]


def _fonctions(texte: str) -> dict:
    return {
        nom: _corps_de_fonction(texte, nom)
        for nom in re.findall(r"^([_a-zA-Z0-9]+)\(\) \{$", texte, flags=re.MULTILINE)
    }


def _hors_heredoc(corps: str) -> str:
    """Le corps SANS ses heredocs ni ses commentaires.

    Les deux citent abondamment les commandes qu'ils décrivent — l'étape 7
    imprime la commande de retour en arrière, `git push --force origin
    <tag>^{commit}:main`, précisément pour qu'on ne l'invente pas le jour du
    regret. La lire comme du code ferait un faux positif permanent, et c'est le
    même piège que `_code()` évite dans `test_borner_historique_donnees.py`.
    """
    retenues, dans_heredoc = [], False
    for ligne in corps.split("\n"):
        if dans_heredoc:
            dans_heredoc = ligne.strip() != "FIN"
            continue
        if "<<'FIN'" in ligne or "<<FIN" in ligne:
            dans_heredoc = True
            continue
        if not ligne.lstrip().startswith("#"):
            retenues.append(ligne)
    return "\n".join(retenues)


def test_tout_geste_irreversible_est_precede_d_une_phrase_tapee():
    """LA garantie de ce runner, structurelle plutôt que déclarative : toute
    fonction qui pousse ou supprime une ref distante doit demander une phrase
    dans la même fonction.

    Un `git push` ajouté ailleurs — dans une étape réversible, dans une
    fonction utilitaire — passerait sous le radar d'une relecture, et c'est
    précisément ce qu'un runner existe pour empêcher."""
    coupables = []
    for nom, corps in _fonctions(_texte()).items():
        code = _hors_heredoc(corps)
        pousse = any(
            l.strip().startswith("git push") for l in code.split("\n")
        )
        if pousse and "_confirmer_phrase" not in code:
            coupables.append(nom)
    assert not coupables, f"gestes irréversibles sans phrase de confirmation : {coupables}"


def test_le_script_de_bornage_ne_pousse_toujours_jamais():
    """#551 en a fait une décision, et le runner ne doit pas l'éroder en
    déplaçant un `git push` dans le script préparatoire. Les deux contrats
    tiennent ensemble ou pas du tout."""
    retenues, dans_heredoc = [], False
    for ligne in BORNAGE.read_text(encoding="utf-8").split("\n"):
        if dans_heredoc:
            dans_heredoc = ligne.strip() != "FIN"
            continue
        if "<<FIN" in ligne:
            dans_heredoc = True
            continue
        if not ligne.lstrip().startswith("#"):
            retenues.append(ligne.strip())
    assert not [l for l in retenues if l.startswith("git push")]
    assert "borner_historique_donnees.sh" in _texte(), (
        "le runner n'appelle plus le script de préparation : il aurait absorbé "
        "son contrat au lieu de s'y adosser"
    )


def test_la_procedure_en_prose_pointe_vers_le_runner_qui_la_deroule():
    """« Le texte se saute — et le moment où on le lit est précisément celui où
    l'on est sous pression » (#576). Un runner que la procédure ne nomme pas ne
    sera pas trouvé le jour J : c'est le heredoc de `--preparer` qu'on lit, et
    lui seul."""
    texte = BORNAGE.read_text(encoding="utf-8")
    heredoc = texte.split("<<FIN", 1)[1].split("\nFIN\n", 1)[0]
    assert "executer_bornage_guide.sh" in heredoc, (
        "la procédure ne dit pas qu'un runner existe pour la dérouler"
    )
    assert "386" in heredoc, "le fait qui justifie le runner n'est pas dit"


def test_le_runner_ne_se_declenche_jamais_tout_seul():
    """« La détection est armée, la réécriture reste manuelle » (#551,
    question 2). Un runner interactif ne franchit pas cette ligne — sauf s'il
    finit dans un workflow."""
    for workflow in (RACINE / ".github" / "workflows").glob("*.yml"):
        assert "executer_bornage_guide" not in workflow.read_text(encoding="utf-8"), (
            f"{workflow.name} invoque le runner de bornage"
        )
    assert "cron" not in _texte()


# ── Les six corrections que la répétition a rendues ─────────────────────────


def test_l_etape_5_traite_les_tags_et_pas_seulement_les_branches():
    """LE défaut de la répétition : « la procédure dit "toute autre BRANCHE
    distante" : elle ne mentionne pas les tags ». `amendements-figes-v1`,
    oublié, ré-épinglait 386 commits."""
    corps = _corps_de_fonction(_texte(), "_etape_5_supprimer_les_refs")
    assert "ls-remote --tags" in corps, "l'étape 5 n'énumère pas les tags"
    assert "refs/tags/" in corps and "--delete" in corps
    assert "386" in corps, "le fait mesuré qui justifie le point a disparu"


def test_dev_est_repointee_et_jamais_supprimee():
    """0 commit propre, mais 21 commits de données gardés atteignables — soit
    l'essentiel des 272 Mo de gain, non parce qu'elle est grosse mais parce
    qu'elle est ANCIENNE. Il n'y a donc pas de contradiction avec la politique
    « ne jamais supprimer `dev` » : elle se repointe."""
    corps = _corps_de_fonction(_texte(), "_etape_5_supprimer_les_refs")
    assert 'nom" == "dev"' in corps, "dev n'est plus traitée à part"
    assert "refs/heads/dev" in corps and "REPOINTÉE" in corps
    dev = corps.split('"dev"', 1)[1].split("continue", 1)[0]
    assert "--delete" not in dev, "dev est supprimée au lieu d'être repointée"


def test_les_refs_pull_sont_nommees_comme_non_supprimables():
    """« Les nommer pour qu'on ne les cherche pas » (#576). Sans ça, on cherche
    pendant l'étape la plus stressante de la procédure une suppression qui
    n'existe pas."""
    corps = _corps_de_fonction(_texte(), "_etape_5_supprimer_les_refs")
    assert re.search(r"refs/pull/\*.*?(?:NE SONT PAS SUPPRIMABLES|non supprimables)",
                     corps, flags=re.IGNORECASE | re.DOTALL), (
        "l'étape 5 elle-même ne dit pas que les refs/pull ne se suppriment "
        "pas ; l'en-tête ne suffit pas, c'est l'étape qu'on lit en la faisant"
    )
    assert "NON supprimables" in corps or "non supprimables" in corps
    assert "GitHub les gère" in corps, (
        "l'étape dit qu'elles résistent sans dire POURQUOI : sans la raison, on "
        "cherche un problème de droits au moment le plus tendu de la procédure"
    )
    assert "Ne pas les" in corps and "chercher" in corps


def test_le_cout_d_entree_est_annonce_avant_la_preparation():
    """« 4,9 Go et 45 s sur ce corpus. À annoncer avant, pas à découvrir »
    (#576). Le chiffre doit être dans l'étape 3 elle-même, pas seulement dans
    l'en-tête : c'est l'étape qu'on lit au moment de la lancer."""
    corps = _corps_de_fonction(_texte(), "_etape_3_preparer")
    assert "4,9 Go" in corps and "45 s" in corps
    assert "arbre" in corps and "propre" in corps


def test_la_duree_de_vie_du_tag_de_sauvegarde_est_ecrite():
    """« Seule sauvegarde immédiate en cas de regret, et rien ne dit combien de
    temps la garder » (#576). La règle est désormais écrite dans l'étape 7 :
    visite `full` couvrant l'avant-coupure ET CI verte, plancher de 30 jours."""
    corps = _corps_de_fonction(_texte(), "_etape_7_remesurer")
    assert "archive/pre-borne-" in corps
    assert "30 JOURS" in corps or "30 jours" in corps
    assert "full" in corps, "la condition d'archive n'est pas nommée"
    assert "JAMAIS pousser ce tag" in corps, (
        "le tag poussé sur le dépôt borné garderait tout l'historique "
        "atteignable et le gain serait nul"
    )


def test_le_verdict_d_archivage_n_est_pas_masque_par_le_tuyau():
    """`| tee` remplace le code de sortie du script par celui de `tee`, qui
    réussit toujours. Sans `PIPESTATUS`, la précondition « le verdict n'est pas
    MANQUANTS » serait verte en toutes circonstances — un garde-fou qui ne
    garde rien, exactement ce que #575 vient de corriger sur l'autre versant."""
    code = _hors_heredoc(_corps_de_fonction(_texte(), "_etape_2_verifier_archivage"))
    assert "code=${PIPESTATUS[0]}" in code, (
        "le code de sortie lu n'est plus celui de la vérification : le "
        "commentaire qui l'explique ne suffit pas, c'est l'affectation qui "
        "garde quelque chose"
    )
    assert "--fenetre" in code, "l'étape 2b ignore où passe la coupure (#575)"


def test_l_etape_2_precede_les_gestes_irreversibles_dans_le_dispatch():
    """L'ordre du `case` de dispatch EST l'ordre d'exécution. Une inversion y
    passerait une relecture — et c'est la seule erreur que rien ne rattrape."""
    texte = _texte()
    attendu = [
        "_etape_1_mesurer", "_etape_2_verifier_archivage", "_etape_3_preparer",
        "_etape_4_pousser", "_etape_5_supprimer_les_refs",
        "_etape_6_verifier_la_ci", "_etape_7_remesurer",
    ]
    dispatch = re.findall(r"^      \d\) (_etape_\w+) ;;$", texte, flags=re.MULTILINE)
    assert dispatch == attendu, f"dispatch dans le désordre : {dispatch}"


def test_la_fenetre_par_defaut_est_la_meme_que_celle_du_bornage():
    """Le runner passe sa fenêtre au script de bornage ET à la vérification
    d'archivage. Trois valeurs pour une même question, c'est trois coupures
    différentes vérifiées et faites."""
    ici = re.search(r"^FENETRE=(\d+)$", _texte(), flags=re.MULTILINE)
    la_bas = re.search(r"^FENETRE=(\d+)$", BORNAGE.read_text(encoding="utf-8"),
                       flags=re.MULTILINE)
    assert ici and la_bas and ici.group(1) == la_bas.group(1)


# ── Réserve 1 du déroulé du 29/08/2026 : l'étape 6 n'observait rien ─────────


def _g(depot, *args):
    return subprocess.run(["git", "-C", str(depot), *args],
                          check=True, capture_output=True, text=True).stdout


def _origine_locale(tmp_path):
    """Un `--bare` dans `tmp_path` qui tient lieu d'origin, et une `main-borne`
    LOCALE volontairement DIFFÉRENTE de ce que porte cette origine.

    C'est la discrimination que l'étape 6 doit passer : lire le commit poussé
    sur la ref distante, et non le supposer depuis ce qu'on a sous la main."""
    travail = tmp_path / "travail"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(travail)],
                   check=True, capture_output=True)
    _g(travail, "config", "user.email", "banc@test")
    _g(travail, "config", "user.name", "banc")
    _g(travail, "commit", "-q", "--allow-empty", "-m", "ce qui est poussé")
    distant = _g(travail, "rev-parse", "HEAD").strip()
    origine = tmp_path / "origine.git"
    subprocess.run(["git", "clone", "--quiet", "--bare", str(travail), str(origine)],
                   check=True, capture_output=True)
    _g(travail, "commit", "-q", "--allow-empty", "-m", "ce qui est resté local")
    _g(travail, "branch", "main-borne", "HEAD")
    local = _g(travail, "rev-parse", "main-borne").strip()
    _g(travail, "remote", "add", "origin", str(origine))
    assert distant != local
    return travail, distant, local


def _faux_gh_lignes(tmp_path, lignes, code=0, nom="bin"):
    """Un faux `gh` qui rend les lignes `statut<TAB>conclusion<TAB>workflow`
    que `_etat_ci` demande à `--jq`."""
    binaire = tmp_path / nom
    binaire.mkdir(exist_ok=True)
    # `%b` et non `%s` : ce sont de vraies TABULATIONS que `--jq` rendrait.
    corps = "\n".join(f'printf "%b\\n" "{l}"' for l in lignes)
    (binaire / "gh").write_text(f"#!/usr/bin/env bash\n{corps}\nexit {code}\n",
                                encoding="utf-8")
    (binaire / "gh").chmod(0o755)
    return {"PATH": f"{binaire}:{os.environ['PATH']}"}


@pytest.mark.parametrize(
    "lignes, attendu",
    [
        ([r"completed\tsuccess\tTests (pytest)"], "vert"),
        ([r"completed\tsuccess\tTests", r"completed\tskipped\tPages",
          r"completed\tneutral\tLint"], "vert"),
        ([r"completed\tfailure\tTests (pytest)"], "rouge"),
        ([r"completed\tsuccess\tTests", r"completed\ttimed_out\tPages"], "rouge"),
        ([r"completed\tcancelled\tTests"], "rouge"),
        ([r"in_progress\t\tTests"], "encours"),
        ([r"queued\t\tTests", r"completed\tsuccess\tPages"], "encours"),
        # Un échec déjà constaté ne devient pas moins vrai parce qu'un autre
        # run tourne encore.
        ([r"in_progress\t\tPages", r"completed\tfailure\tTests"], "rouge"),
        ([], "aucun"),
    ],
)
def test_l_etat_de_la_ci_est_lu_dans_ce_que_gh_rend(tmp_path, lignes, attendu):
    """« La phrase déclare le succès avant de regarder » (#576, réserve 1). Ces
    neuf cas sont ce que « regarder » veut dire."""
    res = _bash('_etat_ci "o/r" "abc123"', env=_faux_gh_lignes(tmp_path, lignes))
    assert res.stdout.strip() == attendu, res.stderr


def test_un_gh_muet_rend_la_ci_indeterminee_pas_verte(tmp_path):
    """Même confusion que `_aucun_run_en_cours` refuse déjà à l'étape 4, et que
    #568 a corrigée côté archive : « pas pu regarder » n'est pas « c'est vert »."""
    res = _bash('if _etat_ci "o/r" "abc123"; then echo LU; else echo MUET; fi',
                env=_faux_gh_lignes(tmp_path, ["erreur"], code=1))
    assert res.stdout.strip() == "MUET"
    assert "gh n'a pas répondu" in res.stderr


def test_l_attente_rend_la_main_quand_le_plafond_est_atteint(tmp_path):
    """Un run en cours n'est pas une conclusion, et attendre indéfiniment
    bloquerait une session au point de non-retour déjà franchi."""
    res = _bash('_attendre_ci "o/r" "abc123"',
                env={**_faux_gh_lignes(tmp_path, [r"in_progress\t\tTests"]),
                     "ATTENTE_CI": "0", "PAS_CI": "0"})
    assert res.stdout.strip() == "encours"
    assert "toujours en cours après 0 s" in res.stderr


def test_l_attente_attend_vraiment_une_conclusion(tmp_path):
    """Le pendant obligatoire : sans lui, « rendre encours tout de suite »
    passerait le test précédent et l'étape 6 ne verrait jamais une CI verte qui
    met dix secondes à conclure."""
    binaire = tmp_path / "bin"
    binaire.mkdir()
    compteur = tmp_path / "appels"
    (binaire / "gh").write_text(
        "#!/usr/bin/env bash\n"
        f'echo x >> "{compteur}"\n'
        f'if [[ $(wc -l < "{compteur}") -lt 3 ]]; then\n'
        '  printf "%s\\n" "in_progress\t\tTests"\n'
        'else\n'
        '  printf "%s\\n" "completed\tsuccess\tTests"\n'
        'fi\n',
        encoding="utf-8",
    )
    (binaire / "gh").chmod(0o755)
    res = _bash('_attendre_ci "o/r" "abc123"',
                env={"PATH": f"{binaire}:{os.environ['PATH']}",
                     "ATTENTE_CI": "60", "PAS_CI": "0"})
    assert res.stdout.strip() == "vert", res.stderr
    assert compteur.read_text().count("x") == 3, "l'attente n'a pas réinterrogé"


def test_le_commit_verifie_est_celui_de_la_ref_distante(tmp_path):
    """Le SHA `f307be7` était CODÉ EN DUR et datait de la répétition de la
    veille : l'étape citait un commit en regardant un autre historique. Le
    commit à vérifier se lit sur la ref distante, seul endroit où « ce qui est
    poussé » existe."""
    travail, distant, local = _origine_locale(tmp_path)
    res = _bash("_sha_pousse", cwd=travail)
    assert res.stdout.strip() == distant, (
        f"SHA lu {res.stdout.strip()!r} ; la branche locale main-borne vaut "
        f"{local!r} — le runner suppose au lieu de lire"
    )


def test_sans_origine_joignable_le_repli_local_se_dit(tmp_path):
    """Un repli silencieux serait la même faute d'un cran plus bas : rendre un
    SHA plausible sans dire d'où il vient."""
    travail, _distant, local = _origine_locale(tmp_path)
    _g(travail, "remote", "set-url", "origin", str(tmp_path / "nulle-part.git"))
    res = _bash("_sha_pousse", cwd=travail)
    assert res.stdout.strip() == local
    assert "C'est une supposition, pas une lecture" in res.stderr


def test_l_etape_6_ne_declare_aucune_conclusion_en_dur():
    """« La phrase déclare le succès avant de regarder, et le SHA est celui de
    la veille » (#576, réserve 1). Ni l'un ni l'autre ne doit pouvoir revenir :
    ce sont deux constantes là où il faut deux observations."""
    corps = _corps_de_fonction(_texte(), "_etape_6_verifier_la_ci")
    code = _hors_heredoc(corps)
    assert "f307be7" not in corps, "le SHA de la répétition du 28/08 est encore cité"
    assert not re.search(r"\b[0-9a-f]{7,40}\b", code), (
        f"un SHA en dur subsiste dans le code de l'étape 6 : "
        f"{re.findall(r'[0-9a-f]{7,40}', code)}"
    )
    assert "elle est passée" not in code, (
        "l'étape écrit encore sa conclusion au lieu de la mesurer"
    )
    assert "|| true" not in code, (
        "la sortie de l'interrogation est encore avalée"
    )


def test_l_etape_6_fait_de_la_conclusion_une_precondition():
    """« Verte, rouge, ou indéterminée, avec un message différent pour
    chacune » (#576). Une précondition au sens du runner : elle refuse
    d'avancer, elle se contourne en toutes lettres, et le contournement se
    consigne."""
    code = _hors_heredoc(_corps_de_fonction(_texte(), "_etape_6_verifier_la_ci"))
    assert "_precondition" in code, "la conclusion n'arrête rien"
    assert "_sha_pousse" in code and "_attendre_ci" in code
    for mot in ("vert)", "rouge)", "encours)", "aucun)"):
        assert mot in code, f"la conclusion « {mot[:-1]} » n'a pas de message propre"
    assert "--commit" in _texte(), (
        "la CI est interrogée sans filtrer sur le commit poussé : les 5 derniers "
        "runs du dépôt ne disent rien de CE commit"
    )


def _journal_jusqu_a_5(tmp_path):
    journal = tmp_path / "j.journal"
    journal.write_text(
        "".join(f"[2026-08-29T10:0{n}:00+0000] ÉTAPE {n} — TERMINÉE\n"
                for n in range(1, 6)),
        encoding="utf-8",
    )
    return journal


def _lancer_etape_6(tmp_path, lignes, entree, code_gh=0):
    travail, distant, _local = _origine_locale(tmp_path)
    journal = _journal_jusqu_a_5(tmp_path)
    env = {**os.environ, **_faux_gh_lignes(tmp_path, lignes, code=code_gh),
           "ATTENTE_CI": "0", "PAS_CI": "0", "GIT_TERMINAL_PROMPT": "0"}
    res = subprocess.run(
        [str(RUNNER), "--etape", "6", "--journal", str(journal)],
        cwd=str(travail), capture_output=True, text=True, input=entree, env=env,
    )
    return res, journal.read_text(encoding="utf-8"), distant


def test_une_ci_rouge_arrete_l_etape_6_et_se_consigne(tmp_path):
    """« Une CI rouge n'est pas un échec du bornage : c'est un constat qui doit
    s'afficher et se journaliser, pas se taire » (#576). L'ancienne étape
    écrivait « elle est passée » et terminait."""
    res, consigne, distant = _lancer_etape_6(
        tmp_path, [r"completed\tfailure\tTests (pytest)"], entree="\n")
    assert res.returncode == 1
    assert "CI ROUGE" in consigne
    assert distant in consigne, "le journal ne dit pas SUR QUEL commit"
    assert "Tests (pytest) » : failure" in consigne, "le run fautif n'est pas nommé"
    assert "PRÉCONDITION EN ÉCHEC" in consigne
    assert "ÉTAPE 6 — TERMINÉE" not in consigne, (
        "l'étape s'est déclarée terminée sur une CI rouge"
    )


def test_une_ci_rouge_se_contourne_en_toutes_lettres(tmp_path):
    """Le pendant : le bornage n'est pas annulé par une CI rouge, mais passer
    outre se tape et se consigne."""
    res, consigne, _ = _lancer_etape_6(
        tmp_path, [r"completed\tfailure\tTests"], entree=PHRASE_DEROGATION + "\n")
    assert res.returncode == 0, res.stderr
    assert "DÉROGATION" in consigne and "ÉTAPE 6 — TERMINÉE" in consigne


def test_une_ci_verte_passe_sans_rien_demander(tmp_path):
    """Sans ce test, « tout refuser » passerait les deux précédents et l'étape 6
    ne pourrait plus jamais conclure."""
    res, consigne, distant = _lancer_etape_6(
        tmp_path, [r"completed\tsuccess\tTests (pytest)"], entree="")
    assert res.returncode == 0, res.stderr
    assert f"CI VERTE sur {distant}" in consigne
    assert "ÉTAPE 6 — TERMINÉE" in consigne
    assert "DÉROGATION" not in consigne


def test_une_ci_qu_on_n_a_pas_pu_lire_ne_passe_pas(tmp_path):
    """Le troisième message. `gh` muet, aucun run, run non conclu : trois
    situations distinctes, toutes « indéterminées », et aucune n'est verte."""
    res, consigne, _ = _lancer_etape_6(tmp_path, ["boum"], entree="\n", code_gh=1)
    assert res.returncode == 1
    assert "CI INDÉTERMINÉE" in consigne
    assert "n'est pas « c'est vert »" in consigne


def test_aucun_run_declenche_n_est_pas_une_ci_verte(tmp_path):
    res, consigne, _ = _lancer_etape_6(tmp_path, [], entree="\n")
    assert res.returncode == 1
    assert "AUCUN run n'a été déclenché" in consigne


# ── Réserve 2 : `--depuis` n'existait qu'à moitié ───────────────────────────


def test_il_n_y_a_pas_d_option_depuis(tmp_path):
    """L'arbitrage rendu (#576, réserve 2) : la variable morte est retirée, pas
    finie. Le journal est la seule preuve de ce qui a été fait ; une option qui
    l'affirmerait sans lui serait une seconde source de vérité, et le runner
    devrait de toute façon la confronter au journal.

    Lancé dans un dépôt jetable : si l'option était acceptée, le runner
    déroulerait — et il n'a rien à dérouler dans le dépôt du projet."""
    depot = tmp_path / "depot"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(depot)],
                   check=True, capture_output=True)
    res = subprocess.run(
        [str(RUNNER), "--depuis", "6", "--journal", str(tmp_path / "j.journal")],
        cwd=str(depot), capture_output=True, text=True, input="",
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    assert res.returncode == 2 and "Option inconnue" in res.stderr
    parsage = _corps_de_fonction(_texte(), "_principal").split("esac", 1)[0]
    assert "--depuis" not in parsage, "l'option fantôme est revenue"


def test_lister_designe_reprendre_comme_le_chemin_de_reprise():
    """« `--reprendre` couvre le besoin et fonctionne, mais rien ne le désigne
    comme le chemin pour reprendre à mi-parcours — `--lister` ne le mentionne
    pas » (#576). C'est `--lister` qu'on lit le jour J."""
    res = subprocess.run([str(RUNNER), "--lister"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert "--reprendre" in res.stdout, (
        "la liste des étapes ne dit pas comment reprendre à mi-parcours"
    )
    assert "--depuis" in res.stdout and "pas de" in res.stdout.lower(), (
        "l'absence de --depuis n'est pas dite : on la cherchera"
    )
    assert "REJOUE le push forcé" in res.stdout, (
        "rien ne dit que `--jusqu-a 7` sans journal repart de l'étape 1"
    )


def test_le_point_de_depart_ne_se_fixe_que_par_etape():
    """Une variable de départ qu'une autre option pourrait fixer redeviendrait
    la demi-option de la réserve 2, sans que rien ne le dise."""
    affectations = re.findall(r"PREMIERE_ETAPE=(\S+)", _texte())
    assert affectations == ["1", "$2;"], (
        f"PREMIERE_ETAPE est fixée ailleurs qu'à l'initialisation et par "
        f"`--etape` : {affectations}"
    )
    assert "DEPUIS=" not in _texte(), "la variable morte est encore là"


def test_reprendre_saute_ce_qui_est_deja_consigne(tmp_path):
    """Vérifié en réel le 29/08/2026 — il a sauté les étapes 4 et 5 déjà faites.
    Ce test le fige : sans le saut, l'étape 1 relancerait `--mesurer`, et sur
    une session déjà passée par l'étape 4 ce serait le push forcé qu'on
    rejouerait."""
    depot = tmp_path / "depot"
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(depot)],
                   check=True, capture_output=True)
    journal = tmp_path / "j.journal"
    journal.write_text(
        "".join(f"[2026-08-29T10:0{n}:00+0000] ÉTAPE {n} — TERMINÉE\n"
                for n in (1, 2, 3)),
        encoding="utf-8",
    )
    res = subprocess.run(
        [str(RUNNER), "--reprendre", str(journal), "--jusqu-a", "3"],
        cwd=str(depot), capture_output=True, text=True, input="",
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    assert res.returncode == 0, res.stderr
    consigne = journal.read_text(encoding="utf-8")
    assert consigne.count("déjà consignée comme terminée, passée") == 3
    assert "SESSION TERMINÉE" in consigne
    assert "mesure du gain" not in consigne, "l'étape 1 a été rejouée"


def test_l_aide_ne_tronque_pas_l_en_tete():
    """L'en-tête EST la documentation du runner : il porte les six corrections
    de la répétition et les deux contrats. Une plage de lignes en dur se périme
    au premier ajout et tronque l'aide sans rien signaler — c'est arrivé sur le
    script de bornage."""
    entete = []
    for ligne in _texte().split("\n")[1:]:
        if not ligne.startswith("#"):
            break
        entete.append(ligne)
    assert len(entete) > 80, "en-tête étrangement court : le repère a bougé"
    aide = [l for l in _texte().split("\n") if "--help" in l and "awk" in l]
    assert aide, "option --help absente"
    assert not re.search(r"\d+\s*,\s*\d+\s*p", aide[0]), (
        f"plage de lignes en dur dans --help : {aide[0].strip()}"
    )
