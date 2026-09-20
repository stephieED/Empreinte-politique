"""Garde-fou #434 : le script qui borne l'historique ne doit jamais pousser.

Borner l'historique de données (option D de #434) suppose une réécriture, donc
un push forcé : irréversible pour tous les clones existants, et destructeur si
elle croise un run de données. `scripts/borner_historique_donnees.sh` mesure et
prépare — l'humaine pousse.

Ces tests verrouillent cette frontière. Trois pièges rencontrés en mesurant
produisent chacun un résultat **faux et silencieux** — un gain nul présenté
comme un succès :

  1. `git replace --graft` seul ne tronque rien : `main` porte des commits de
     merge dont le second parent plonge avant la coupure (mesuré : 677 commits
     avant la greffe, 677 après). D'où le rejeu qui remappe tous les parents.
  2. Les index bitmap sont calculés sur le graphe non greffé et priment sur la
     greffe : sans `pack.useBitmaps=false`, la vérification rend l'état
     d'AVANT sans le signaler.
  3. Les autres refs ré-épinglent l'ancien historique et annulent le gain.

Un script qui pousserait sur la foi d'une telle mesure serait plus dangereux
que l'oubli qu'il prétend corriger. Volontairement sans dépendance : on lit le
texte du script, comme les autres gardes-fous de ce dépôt.

Ce que ce fichier ne peut PAS dire, c'est si la coupure fonctionne : une
recherche de motif reste verte devant un refactor qui garderait les chaînes en
cassant la logique. C'est `tests/test_borner_historique_execution.py` (#567)
qui exécute réellement l'opération, sur un dépôt synthétique jetable portant le
merge du piège n° 1. Les deux fichiers sont complémentaires et aucun ne
remplace l'autre : celui-ci couvre ce qu'une exécution ne montre pas — que le
script ne pousse jamais, qu'il ne réécrit pas `main`, que sa fenêtre par défaut
est celle de l'audit.
"""

import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "scripts" / "borner_historique_donnees.sh"


def _code() -> str:
    """Le script sans ses commentaires **ni son heredoc d'instructions**.

    Les deux citent abondamment les commandes qu'ils décrivent — y compris les
    `git push` que l'humaine devra taper elle-même. Les lire comme du code
    serait un faux positif permanent ; ne pas les exclure ferait échouer
    `test_le_script_ne_pousse_jamais` sur le texte même qui explique pourquoi
    le script ne pousse pas.
    """
    retenues, dans_heredoc = [], False
    for ligne in SCRIPT.read_text(encoding="utf-8").split("\n"):
        if dans_heredoc:
            dans_heredoc = ligne.strip() != "FIN"
            continue
        if "<<FIN" in ligne:
            dans_heredoc = True
            continue
        if not ligne.lstrip().startswith("#"):
            retenues.append(ligne)
    return "\n".join(retenues)


def test_le_script_existe_et_est_executable():
    assert SCRIPT.is_file(), f"{SCRIPT} absent"
    assert SCRIPT.stat().st_mode & 0o111, "script non exécutable"


def test_le_script_ne_pousse_jamais():
    """LA garantie. Les commandes de push vivent dans un `cat <<FIN` destiné à
    être lu, jamais exécuté : aucune ligne de code ne doit invoquer git push."""
    for ligne in _code().split("\n"):
        nue = ligne.strip()
        assert not nue.startswith("git push"), f"push exécuté : {nue}"
        assert not nue.startswith("git -C") or "push" not in nue, f"push exécuté : {nue}"


def test_le_script_ne_reecrit_pas_main():
    """`main` doit rester intacte : la branche préparée porte un autre nom."""
    code = _code()
    assert "refs/heads/main-borne" in code
    assert "update-ref refs/heads/main " not in code
    assert "branch -f main" not in code
    assert "reset --hard" not in code


def test_le_script_desactive_les_bitmaps_ou_n_utilise_pas_de_greffe():
    """Piège n° 2. Si le script s'appuyait sur `git replace --graft`, il
    devrait impérativement désactiver les bitmaps ; le rejeu explicite qu'il
    utilise à la place n'a pas ce défaut. L'un ou l'autre, jamais la greffe
    nue."""
    code = _code()
    if "replace --graft" in code:
        assert "pack.useBitmaps=false" in code, "greffe sans désactiver les bitmaps"


def test_le_script_remappe_tous_les_parents():
    """Piège n° 1 : `rev-list --parents` puis remappage de chacun, sinon un
    merge laisse l'ancien historique atteignable par un autre chemin."""
    code = _code()
    assert "rev-list --parents -n1" in code
    assert "--reverse --topo-order" in code, "rejeu sans ordre topologique"


def test_le_script_supprime_les_autres_refs_avant_de_mesurer():
    """Piège n° 3 : une ref oubliée ré-épingle tout et le gain mesuré serait
    faux."""
    code = _code()
    assert "for-each-ref" in code
    assert "update-ref -d" in code


def test_le_script_verifie_l_identite_de_l_arbre_du_sommet():
    """La seule preuve qu'aucun octet n'est perdu : un arbre git est un
    hachage récursif de tout le contenu. S'il coïncide, chaque fichier
    coïncide.

    La vérification doit être appelée dans **les deux** modes — c'est dans
    `--preparer` qu'elle protège quelque chose, puisque c'est de là que sort
    la branche destinée à être poussée."""
    code = _code()
    assert "^{tree}" in code
    assert code.count("_verifier ") >= 2, "vérification absente d'un des deux modes"
    for mode in ("mesurer", "preparer"):
        # L'étiquette du `case` de dispatch est en début de ligne ; `--mesurer)`
        # est celle de l'analyse d'arguments, et la prendre découperait le
        # mauvais bloc.
        debut = re.search(rf"^{mode}\)$", code, flags=re.MULTILINE)
        assert debut, f"branche `{mode})` introuvable"
        bloc = code[debut.end():].split(";;", 1)[0]
        assert "_verifier " in bloc, f"aucune vérification d'arbre dans le mode {mode}"


def test_le_mode_par_defaut_est_la_mesure_pas_la_preparation():
    """Un lancement sans argument ne doit rien écrire dans le dépôt.

    On cherche la ligne d'affectation par défaut, pas la sous-chaîne : la
    branche `--mesurer)` du `case` contient elle aussi « MODE=mesurer », et
    une recherche naïve resterait verte après un basculement du défaut."""
    lignes = [l.strip() for l in _code().split("\n")]
    assert "MODE=mesurer" in lignes, "le défaut n'est pas le mode mesure"
    assert "MODE=preparer" not in lignes, "préparer est devenu le défaut"


def test_la_preparation_refuse_un_arbre_sale_ou_une_divergence():
    """Préparer sur un arbre sale, hors `main`, ou désynchronisé d'origin
    produirait une réécriture qui ne correspond à rien de poussable."""
    code = _code()
    assert "git status --porcelain" in code
    assert "origin/main" in code
    for refus in ("Refus.", "exit 1"):
        assert refus in code


def test_la_preparation_archive_l_ancien_main():
    """Tous les SHA changent à partir de la coupure : sans archive, les 27 SHA
    cités dans le journal de décision cessent de résoudre."""
    code = _code()
    assert "archive/pre-borne-" in code
    assert "git tag" in code


def _en_tete() -> list[str]:
    """Le bloc de commentaires qui suit le shebang, jusqu'à la première ligne
    de code."""
    lignes = SCRIPT.read_text(encoding="utf-8").split("\n")[1:]
    entete = []
    for ligne in lignes:
        if not ligne.startswith("#"):
            break
        entete.append(ligne)
    return entete


def test_l_aide_ne_tronque_pas_l_en_tete():
    """L'en-tête EST la documentation : il porte la table des mesures, les
    trois pièges et ce que l'opération ne rend pas. `--help` doit le rendre en
    entier.

    Une plage de lignes en dur se périme au premier ajout et tronque l'aide
    sans rien signaler. C'est arrivé : `sed -n '2,80p'` a cessé de couvrir
    l'en-tête bien avant que #551 l'allonge encore."""
    entete = _en_tete()
    assert len(entete) > 80, "en-tête étrangement court : le repère a bougé"
    aide = [l for l in _code().split("\n") if "--help" in l]
    assert aide, "option --help absente"
    assert not re.search(r"\d+\s*,\s*\d+\s*p", aide[0]), (
        f"plage de lignes en dur dans --help : {aide[0].strip()}"
    )


def test_la_fenetre_par_defaut_est_la_meme_ici_et_dans_l_audit():
    """La valeur de la fenêtre vit à DEUX endroits (#551) : `FENETRE` dans ce
    script, `FENETRE_COMMITS_DONNEES` dans `src/audit_volumetrie_profils.py`.

    L'audit est ce qui dit « la fenêtre est-elle contraignante ? » et le script
    est ce qui coupe. Un arbitrage qui n'en changerait qu'un ferait répondre
    deux valeurs différentes à la même question, sans que rien ne le signale.
    """
    ici = re.search(r"^FENETRE=(\d+)$", _code(), flags=re.MULTILINE)
    assert ici, "valeur par défaut de FENETRE introuvable"
    audit = (RACINE / "src" / "audit_volumetrie_profils.py").read_text(
        encoding="utf-8"
    )
    la_bas = re.search(r"^FENETRE_COMMITS_DONNEES = (\d+)$", audit, flags=re.MULTILINE)
    assert la_bas, "FENETRE_COMMITS_DONNEES introuvable dans l'audit"
    assert ici.group(1) == la_bas.group(1), (
        f"fenêtre incohérente : script={ici.group(1)}, audit={la_bas.group(1)}"
    )
