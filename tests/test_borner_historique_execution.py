"""#567 : la coupure d'historique, EXÉCUTÉE, sur un dépôt synthétique jetable.

`tests/test_borner_historique_donnees.py` lit le texte de
`scripts/borner_historique_donnees.sh` : douze gardes-fous qui attrapent les
régressions de code — que le script ne pousse jamais, qu'il ne réécrit pas
`main`, que sa fenêtre par défaut est celle de l'audit. Ils restent, et ils
couvrent ce qu'une exécution ne montre pas.

Ce qu'ils ne peuvent pas dire, c'est si l'opération FONCTIONNE. Un refactor qui
garderait les chaînes cherchées en cassant la logique les passerait tous. Or
#551 vient de faire du bornage l'unique frein à la croissance du dépôt, et
l'épic #566 part d'un constat simple : **la coupure n'avait jamais été
exécutée**, ni en test ni en réel.

Ce fichier l'exécute. Il monte un dépôt de ~11 Mo dans `tmp_path`, lance le
script dessus, et vérifie le résultat sur le graphe obtenu.

**La fixture porte un commit de merge dont le second parent plonge avant la
coupure.** C'est le piège n° 1 de l'en-tête du script, et le seul point de ce
fichier qu'une fixture linéaire raterait entièrement : `git replace --graft`
laisse alors l'ancien historique atteignable par l'autre chemin — mesuré à
l'époque sur le vrai dépôt, 677 commits avant la greffe, 677 après.

Ce que le test ne couvre pas, délibérément : le push forcé, les refs distantes
et la CI après coupure. C'est la répétition en grandeur réelle (#569), et
aucun test unitaire ne l'atteint.
"""

import os
import random
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from audit_volumetrie_profils import FENETRE_COMMITS_DONNEES, MOTIF_COMMIT_DONNEES

RACINE = Path(__file__).resolve().parents[1]
SCRIPT = RACINE / "scripts" / "borner_historique_donnees.sh"

# Fenêtre du banc d'essai. Volontairement PAS la fenêtre de production : celle-ci
# vaut 30 (`FENETRE_COMMITS_DONNEES`, un mois de données), et il faudrait donc
# plus de 30 commits de données pour qu'elle morde — 30 Mo de fixture et autant
# de `gc` pour ne rien prouver de plus. La fenêtre de production est éprouvée
# ailleurs dans ce fichier, sur son propre chemin : celui du refus de couper.
FENETRE_BANC = 3

# 10 commits de données, dont 7 tombent. Chacun réécrit intégralement un bloc
# d'un mébioctet d'octets aléatoires : incompressible et non déltifiable, donc
# le gain se lit en mébioctets entiers sur `du -sm`, la grandeur exacte que le
# script rapporte. Un corpus en texte se serait déltifié et le gain se serait
# perdu dans l'arrondi.
NB_COMMITS_DONNEES = 10
TAILLE_BLOC = 1024 * 1024

# Tolérance des comparaisons de taille, en Mo : `du -sm` arrondit au mébioctet
# supérieur et deux chemins de repack différents ne rendent pas l'octet près.
TOLERANCE_MO = 1


# ── Le banc ──────────────────────────────────────────────────────────────────


@dataclass
class Banc:
    """Tout ce que l'exécution a produit, monté une seule fois."""

    base: Path
    depot: Path
    env: dict
    sha: dict = field(default_factory=dict)  # repère → SHA d'origine
    main_avant: str = ""
    mesure: subprocess.CompletedProcess = None
    mesure_defaut: subprocess.CompletedProcess = None
    preparation: subprocess.CompletedProcess = None
    mo_avant_mesure: int = 0  # mesuré indépendamment, dépôt complet
    mo_apres_mesure: int = 0  # mesuré indépendamment, branche bornée seule


def _git(banc_ou_env, depot: Path, *args: str) -> str:
    env = banc_ou_env.env if isinstance(banc_ou_env, Banc) else banc_ou_env
    return subprocess.run(
        ["git", "-C", str(depot), *args],
        env=env, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _mo(chemin: Path) -> int:
    """La MÊME grandeur que celle que le script rapporte : `du -sm`."""
    return int(subprocess.run(
        ["du", "-sm", str(chemin)], check=True, capture_output=True, text=True
    ).stdout.split()[0])


def _environnement(base: Path) -> dict:
    """Un git hermétique : ni config globale de la machine, ni `$TMPDIR` hors
    du bac à sable.

    `--mesurer` clone dans `$(mktemp -d)` ; pointer `TMPDIR` dans `tmp_path`
    garde même ce clone-là sous le répertoire que pytest nettoiera. Et la
    config globale doit porter une identité : le clone de mesure n'hérite pas
    de la config LOCALE du dépôt, et `commit-tree` sans identité échoue.
    """
    home = base / "home"
    home.mkdir()
    temporaire = base / "tmp"
    temporaire.mkdir()
    config = base / "gitconfig"
    config.write_text(
        "[user]\n\tname = Banc 567\n\temail = banc-567@example.invalid\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    for fuite in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                  "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(fuite, None)
    env.update({
        "HOME": str(home),
        "GIT_CONFIG_GLOBAL": str(config),
        "GIT_CONFIG_SYSTEM": str(config),
        "TMPDIR": str(temporaire),
        "GIT_TERMINAL_PROMPT": "0",
    })
    return env


def _construire_depot(base: Path) -> Banc:
    """Le dépôt synthétique. Sa forme est le sujet du test, pas un décor.

    Chronologie de `main` — la coupure tombera sur d7, quatrième commit de
    données en partant du sommet :

        socle · d1 · d2 · point ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ v1 · v2
                                 └ d3 … d7 · d8 · M ┘ · d9 · d10

    `point` est ANTÉRIEUR à la coupure et `M` lui est postérieur : le second
    parent de `M` plonge donc avant la coupure. C'est très exactement la forme
    qui rend `git replace --graft` inopérant — greffer d7 ne coupe rien, parce
    que d1, d2 et `point` restent atteignables par M → v2 → v1 → point.
    """
    banc = Banc(base=base, depot=base / "depot", env=_environnement(base))
    depot, env = banc.depot, banc.env
    subprocess.run(["git", "init", "--quiet", "-b", "main", str(depot)],
                   env=env, check=True, capture_output=True)
    (depot / "data").mkdir()
    (depot / "docs").mkdir()
    alea = random.Random(567)
    compteur = {"n": 0}

    def _commit(sujet: str) -> str:
        _git(banc, depot, "add", "-A")
        _git(banc, depot, "commit", "--quiet", "-m", sujet)
        return _git(banc, depot, "rev-parse", "HEAD")

    def _commit_donnees() -> str:
        compteur["n"] += 1
        # Bloc réécrit en entier : c'est ce que fait un run du pipeline sur
        # `pivot_data/`, et c'est ce qui rend l'ancien contenu jetable.
        (depot / "data" / "corpus.bin").write_bytes(alea.randbytes(TAILLE_BLOC))
        with (depot / "data" / "journal.txt").open("a", encoding="utf-8") as f:
            f.write(f"run {compteur['n']}\n")
        # Le sujet doit porter MOTIF_COMMIT_DONNEES : c'est à lui, et à lui
        # seul, que le script reconnaît un commit de données.
        return _commit(f"chore(données): {MOTIF_COMMIT_DONNEES} ({compteur['n']})")

    def _commit_code(sujet: str, ligne: str) -> str:
        with (depot / "docs" / "notes.md").open("a", encoding="utf-8") as f:
            f.write(ligne + "\n")
        return _commit(sujet)

    banc.sha["socle"] = _commit_code("chore: socle du dépôt", "socle")
    banc.sha["d1"] = _commit_donnees()
    banc.sha["d2"] = _commit_donnees()
    banc.sha["point"] = _commit_code("feat: point de branchement", "avant la coupure")
    for i in range(3, 9):  # d3 … d8
        banc.sha[f"d{i}"] = _commit_donnees()

    # La veine qui plonge sous la coupure : branchée sur `point`, fusionnée
    # APRÈS d8, donc après la coupure.
    _git(banc, depot, "checkout", "--quiet", "-b", "veine", banc.sha["point"])
    (depot / "docs" / "veine.md").write_text("veine 1\n", encoding="utf-8")
    banc.sha["v1"] = _commit("feat(veine): premier commit")
    (depot / "docs" / "veine.md").write_text("veine 1\nveine 2\n", encoding="utf-8")
    banc.sha["v2"] = _commit("feat(veine): second commit")
    _git(banc, depot, "checkout", "--quiet", "main")
    _git(banc, depot, "merge", "--quiet", "--no-ff", "veine",
         "-m", "Merge pull request: veine")
    banc.sha["M"] = _git(banc, depot, "rev-parse", "HEAD")

    banc.sha["d9"] = _commit_donnees()
    banc.sha["d10"] = _commit_donnees()

    # `--preparer` refuse si `main` et `origin/main` divergent : il lui faut
    # un `origin`. Un dépôt nu local en tient lieu — aucun réseau (AGENTS.md §3).
    origine = base / "origin.git"
    subprocess.run(["git", "init", "--quiet", "--bare", str(origine)],
                   env=env, check=True, capture_output=True)
    _git(banc, depot, "remote", "add", "origin", str(origine))
    _git(banc, depot, "push", "--quiet", "origin", "main")
    _git(banc, depot, "fetch", "--quiet", "origin")
    banc.main_avant = _git(banc, depot, "rev-parse", "main")
    return banc


def _lancer(banc: Banc, *args: str) -> subprocess.CompletedProcess:
    """Le script, depuis le dépôt synthétique. `cwd` est la SEULE chose qui
    dise au script où travailler : il fait `git rev-parse --show-toplevel`."""
    return subprocess.run(
        [str(SCRIPT), *args], cwd=str(banc.depot), env=banc.env,
        capture_output=True, text=True,
    )


@pytest.fixture(scope="module")
def banc(tmp_path_factory) -> Banc:
    """Monte le dépôt, l'exécute, et mesure — une seule fois pour le fichier.

    Deux `gc --prune=now` par appel à `--mesurer` : le refaire par test
    coûterait une dizaine de secondes pour rien.
    """
    if shutil.which("git") is None:  # pragma: no cover
        pytest.skip("git absent")
    base = tmp_path_factory.mktemp("borner")
    banc = _construire_depot(base)

    # Mesure indépendante du dépôt COMPLET, par le même chemin que le script :
    # miroir, puis `gc --prune=now`. À faire avant `--preparer`, qui ajoute des
    # refs au dépôt et fausserait la comparaison.
    miroir = base / "temoin-complet.git"
    subprocess.run(["git", "clone", "--quiet", "--mirror", "--no-hardlinks",
                    str(banc.depot), str(miroir)],
                   env=banc.env, check=True, capture_output=True)
    _git(banc, miroir, "gc", "--prune=now", "--quiet")
    banc.mo_avant_mesure = _mo(miroir)

    banc.mesure = _lancer(banc, "--mesurer", "--fenetre", str(FENETRE_BANC))
    banc.mesure_defaut = _lancer(banc, "--mesurer")
    banc.preparation = _lancer(banc, "--preparer", "--fenetre", str(FENETRE_BANC))

    # Mesure indépendante de l'APRÈS : ce qu'un consommateur clonerait de la
    # branche bornée. `--no-local` force le protocole git — un clone sur CHEMIN
    # recopie le répertoire d'objets tel quel, résidus compris, et rendrait la
    # taille d'avant (piège documenté dans l'en-tête du script).
    if "refs/heads/main-borne" in _git(banc, banc.depot, "for-each-ref",
                                       "--format=%(refname)"):
        borne = base / "temoin-borne.git"
        subprocess.run(["git", "clone", "--quiet", "--bare", "--no-local",
                        "--single-branch", "--branch", "main-borne",
                        str(banc.depot), str(borne)],
                       env=banc.env, check=True, capture_output=True)
        _git(banc, borne, "gc", "--prune=now", "--quiet")
        banc.mo_apres_mesure = _mo(borne)
    return banc


def _nombre(motif: str, sortie: str) -> int:
    trouve = re.search(motif, sortie)
    assert trouve, f"introuvable dans la sortie du script : {motif}\n---\n{sortie}"
    return int(trouve.group(1))


def _atteignables(banc: Banc, ref: str) -> set:
    """Les commits atteignables depuis `ref`, bitmaps DÉSACTIVÉS.

    Piège n° 2 de l'en-tête : les index bitmap sont calculés sur le graphe non
    greffé et priment sur la greffe. Une vérification qui les laisserait faire
    rendrait le résultat d'AVANT la coupure sans le signaler — c'est-à-dire
    que le test mentirait dans le sens qui l'arrange le moins : il verrait
    l'ancien historique là où il n'est plus, ou l'inverse.
    """
    sortie = subprocess.run(
        ["git", "-C", str(banc.depot), "-c", "pack.useBitmaps=false",
         "rev-list", ref],
        env=banc.env, check=True, capture_output=True, text=True,
    ).stdout
    return set(sortie.split())


# ── Ce que l'exécution établit ───────────────────────────────────────────────


def test_la_mesure_aboutit_et_ne_travaille_que_dans_le_depot_jetable(banc):
    """Le script résout sa racine par `git rev-parse --show-toplevel` : c'est
    `cwd` qui décide, et rien d'autre. Le vérifier avant tout le reste — un
    test qui mesurerait le VRAI dépôt passerait ses assertions de taille et
    n'aurait rien prouvé."""
    assert banc.mesure.returncode == 0, banc.mesure.stderr
    assert str(banc.depot) in banc.mesure.stdout, (
        "le script n'a pas nommé le dépôt jetable comme sa racine :\n"
        + banc.mesure.stdout
    )


def test_la_coupure_conserve_exactement_la_fenetre_de_commits_de_donnees(banc):
    """Population : les commits de données — ceux dont le sujet porte
    `MOTIF_COMMIT_DONNEES` — atteignables depuis la branche produite. Pas les
    commits du dépôt, dont la plupart sont du code.

    `main` en porte 10 ; la branche bornée doit en porter exactement 3, ni un
    de plus (le commit de coupure lui-même est remplacé par le socle, dont le
    sujet ne porte pas le motif) ni un de moins.
    """
    def _compter(ref: str) -> int:
        sortie = _git(banc, banc.depot, "log", "--format=%H",
                      f"--grep={MOTIF_COMMIT_DONNEES}", ref)
        return len(sortie.split())

    assert _compter("main") == NB_COMMITS_DONNEES, (
        "main ne montre plus ses 10 commits de données : soit la fixture a "
        "dérivé, soit la coupure a laissé derrière elle une réécriture qui "
        "vaut pour TOUT le dépôt — c'est ce que fait `git replace --graft`, "
        "dont la ref survit à l'opération et change ce que main affiche"
    )
    assert _compter("main-borne") == FENETRE_BANC, (
        "la fenêtre demandée n'est pas celle qui a été conservée"
    )
    # Et ce sont bien les plus RÉCENTS, pas trois commits quelconques.
    conserves = _git(banc, banc.depot, "log", "--format=%s",
                     f"--grep={MOTIF_COMMIT_DONNEES}", "main-borne").split("\n")
    assert [s.rsplit("(", 1)[1] for s in conserves] == ["10)", "9)", "8)"]


def test_l_arbre_du_sommet_est_identique_avant_et_apres_la_coupure(banc):
    """La coupure change l'histoire, jamais le contenu. Un arbre git est un
    hachage récursif de tout le contenu : s'il coïncide, chaque fichier
    coïncide — y compris `docs/veine.md`, qui n'est arrivé que par le merge."""
    avant = _git(banc, banc.depot, "rev-parse", f"{banc.main_avant}^{{tree}}")
    apres = _git(banc, banc.depot, "rev-parse", "main-borne^{tree}")
    assert avant == apres, "le contenu du sommet a changé — rien ne serait poussable"
    assert avant in banc.mesure.stdout, (
        "le script annonce un autre arbre que celui qu'il a produit"
    )
    # Ce que l'égalité des arbres recouvre, dit une fois en clair : le fichier
    # que SEUL le merge a fait entrer dans `main` est toujours là, à sa valeur.
    assert "veine 2" in _git(banc, banc.depot, "show", "main-borne:docs/veine.md")


def test_les_commits_anterieurs_a_la_coupure_sont_inatteignables(banc):
    """Piège n° 1, et la raison d'être de ce fichier.

    `point` n'est atteignable depuis le sommet QUE par le second parent du
    merge. Une greffe sur le seul commit de coupure le laisserait en place, et
    avec lui tout ce qui le précède : mesuré sur le vrai dépôt, 677 commits
    avant la greffe, 677 après. Seul un rejeu qui remappe TOUS les parents le
    détache.
    """
    vivants = _atteignables(banc, "main-borne")
    for repere in ("socle", "d1", "d2", "point", "d3", "d4", "d5", "d6", "d7"):
        assert banc.sha[repere] not in vivants, (
            f"« {repere} » précède la coupure et reste atteignable depuis "
            "main-borne : l'ancien historique n'a pas été détaché"
        )
    # Les originaux du merge et de la veine tombent aussi : ils sont REJOUÉS,
    # donc leurs SHA changent. Ce qui compte est que leur contenu survive.
    for repere in ("v1", "v2", "M", "d8", "d9", "d10"):
        assert banc.sha[repere] not in vivants, (
            f"« {repere} » n'a pas été rejoué : ses parents pointent encore "
            "vers l'ancien graphe"
        )
    # Le merge lui-même survit sous forme rejouée, à deux parents : le rejeu
    # remappe le chemin, il ne l'aplatit pas.
    merges = [l for l in _git(banc, banc.depot, "log", "--format=%H %P",
                              "main-borne").split("\n") if len(l.split()) == 3]
    assert len(merges) == 1, "le merge a été perdu ou dupliqué par le rejeu"
    # Et la coupure ne doit RIEN laisser derrière elle qui réécrive le dépôt :
    # une `refs/replace/*` oubliée changerait ce que toute commande y voit,
    # `main` comprise, sans toucher un seul SHA.
    assert not _git(banc, banc.depot, "for-each-ref", "--format=%(refname)",
                    "refs/replace"), "une ref de remplacement survit à la coupure"


def test_la_fixture_reproduit_bien_le_piege_de_la_greffe(banc):
    """Le test précédent ne vaut que si la fixture porte VRAIMENT le piège.

    On le montre en le déclenchant : sur un miroir jetable, `git replace
    --graft` du seul commit de coupure, puis on regarde ce qui reste
    atteignable. Si l'ancien historique tombait tout seul, la forme du dépôt
    synthétique serait trop simple et le test d'à côté ne prouverait rien.

    C'est la reproduction en miniature des « 677 commits avant, 677 après »
    relevés sur le vrai dépôt.
    """
    greffe = banc.base / "greffe.git"
    subprocess.run(["git", "clone", "--quiet", "--mirror",
                    str(banc.depot), str(greffe)],
                   env=banc.env, check=True, capture_output=True)
    _git(banc, greffe, "replace", "--graft", banc.sha["d7"])
    apres_greffe = set(subprocess.run(
        ["git", "-C", str(greffe), "-c", "pack.useBitmaps=false",
         "rev-list", "main"],
        env=banc.env, check=True, capture_output=True, text=True,
    ).stdout.split())

    assert banc.sha["d7"] in apres_greffe, "la greffe n'a pas pris"
    for repere in ("point", "d2", "d1", "socle"):
        assert banc.sha[repere] in apres_greffe, (
            f"« {repere} » est tombé sans rejeu : la fixture ne porte plus le "
            "piège n° 1, et le test de la coupure ne prouve plus rien"
        )
    # …alors que la vraie coupure, elle, les détache : c'est l'écart entre les
    # deux qui mesure ce que le rejeu apporte.
    assert not {banc.sha[r] for r in ("point", "d2", "d1", "socle")} & \
        _atteignables(banc, "main-borne")


def test_l_historique_borne_est_une_ligne_droite_jusqu_a_un_seul_socle(banc):
    """Deux racines voudraient dire qu'un morceau de l'ancien historique a
    survécu à côté du socle."""
    racines = _git(banc, banc.depot, "rev-list", "--max-parents=0",
                   "main-borne").split()
    assert len(racines) == 1, f"{len(racines)} racines au lieu d'une"
    assert "socle historique" in _git(banc, banc.depot, "log", "-1",
                                      "--format=%s", racines[0])


def test_le_gain_annonce_correspond_a_la_mesure_reelle(banc):
    """Population des trois chiffres : le dépôt entier sur disque après
    `gc --prune=now`, en mébioctets — PAS la somme des coûts par run, qui
    surestime d'un facteur 2 (en-tête du script).

    Le témoin d'avant est un miroir repacké du dépôt complet ; celui d'après
    est ce qu'un clone `--no-local` de la seule branche bornée sert vraiment.
    """
    avant = _nombre(r"historique complet, après repack : (\d+) Mo",
                    banc.mesure.stdout)
    apres = _nombre(rf"historique borné à {FENETRE_BANC}, après repack : (\d+) Mo",
                    banc.mesure.stdout)
    gain = _nombre(r"GAIN RÉEL : (\d+) Mo", banc.mesure.stdout)

    assert gain == avant - apres, "l'arithmétique du gain annoncé ne tient pas"
    assert abs(avant - banc.mo_avant_mesure) <= TOLERANCE_MO, (
        f"avant annoncé {avant} Mo, mesuré {banc.mo_avant_mesure} Mo"
    )
    assert abs(apres - banc.mo_apres_mesure) <= TOLERANCE_MO, (
        f"après annoncé {apres} Mo, mesuré {banc.mo_apres_mesure} Mo — "
        "un gain annoncé que personne ne constate"
    )
    # Et le gain est réel, pas un arrondi : 7 des 10 blocs d'un Mo tombent.
    assert gain >= 4, f"gain de {gain} Mo là où 7 blocs d'un Mo devaient tomber"


def test_la_fenetre_de_production_refuse_de_couper_ce_qu_elle_ne_borne_pas(banc):
    """La fenêtre par défaut ne vit pas ici : elle vient de
    `FENETRE_COMMITS_DONNEES`, et `test_la_fenetre_par_defaut_est_la_meme_ici_et_dans_l_audit`
    la tient égale à celle du script. On ne la recopie pas, on l'importe.

    Sur 10 commits de données, elle n'est pas contraignante : le script doit le
    dire et ne rien réécrire. C'est le chemin le plus fréquent en pratique —
    aujourd'hui encore, le vrai dépôt est de ce côté-là.
    """
    assert NB_COMMITS_DONNEES < FENETRE_COMMITS_DONNEES, "banc mal calibré"
    assert banc.mesure_defaut.returncode == 0, banc.mesure_defaut.stderr
    assert "Fenêtre NON contraignante" in banc.mesure_defaut.stdout
    assert f"({NB_COMMITS_DONNEES} ≤ {FENETRE_COMMITS_DONNEES})" in \
        banc.mesure_defaut.stdout
    assert "GAIN RÉEL" not in banc.mesure_defaut.stdout


def test_la_preparation_laisse_main_intacte_et_archive_l_ancien_sommet(banc):
    """`main` doit sortir de `--preparer` au même SHA qu'elle y est entrée, et
    le tag d'archive doit résoudre : sans lui, les SHA cités dans
    `docs/technical_decisions.md` et dans les issues cessent de résoudre."""
    assert banc.preparation.returncode == 0, banc.preparation.stderr
    assert _git(banc, banc.depot, "rev-parse", "main") == banc.main_avant, (
        "main a été réécrite — la garantie centrale du script"
    )
    tags = [t for t in _git(banc, banc.depot, "for-each-ref",
                            "--format=%(refname)", "refs/tags").split("\n") if t]
    archives = [t for t in tags if t.startswith("refs/tags/archive/pre-borne-")]
    assert len(archives) == 1, f"tags d'archive : {tags}"
    assert _git(banc, banc.depot, "rev-parse", archives[0] + "^{commit}") == \
        banc.main_avant


def test_la_preparation_rend_la_procedure_en_entier(banc):
    """Le mode `--preparer` ne sert à rien s'il n'imprime pas la procédure :
    c'est là que vivent l'ordre non négociable (archiver AVANT de couper) et le
    retour en arrière.

    Ce test a trouvé un défaut réel (#567) : les instructions vivaient dans un
    heredoc NON quoté, donc soumis aux substitutions du shell. `\\`full\\``
    lançait une commande `full`, `$sha` était une variable sans liaison, et
    `set -u` tuait le script AVANT la première ligne du bloc. Le mode
    `--preparer` sortait en erreur 1 et n'avait jamais rien imprimé.

    Les fragments cités ont changé avec #568, qui a remplacé le bloc `curl` en
    prose par l'appel à `src/verifier_archivage_swh.py`. Ce qui est vérifié n'a
    pas changé : ce qui est cité sort littéralement, ce qui est une variable est
    substitué. C'est la sélectivité de l'échappement qui est le sujet, pas les
    chaînes elles-mêmes.
    """
    sortie = banc.preparation.stdout
    for repere in ("RIEN n'a été poussé", "sauvegarde locale", "branche réécrite",
                   "Save Code Now", "force-with-lease", "Retour en arrière"):
        assert repere in sortie, f"procédure tronquée : « {repere} » manquant"
    assert "commande introuvable" not in banc.preparation.stderr
    assert "unbound variable" not in banc.preparation.stderr
    assert "sans liaison" not in banc.preparation.stderr
    # Les fragments de shell CITÉS doivent sortir littéralement, non exécutés.
    # Ce sont les backticks qui avaient le plus mordu : `full` était lancé comme
    # une commande, d'où le « commande introuvable » vérifié plus haut.
    assert "visite `full`, tout résout" in sortie
    assert "`--sans-issues` si `gh` n'est pas authentifié" in sortie
    assert "JAMAIS `git remote update` ni `--prune` dessus" in sortie
    # La procédure doit nommer l'outil de vérification (#568), pas le décrire.
    assert "python3 src/verifier_archivage_swh.py" in sortie
    # …et la preuve INVERSE : l'échappement est sélectif, pas global. Les vraies
    # variables doivent encore être substituées, sinon la procédure imprimerait
    # « $TAG » là où l'opératrice attend le nom du tag qu'elle vient de créer.
    assert "archive/pre-borne-" in sortie
    assert "$TAG" not in sortie and "$NEW" not in sortie
    # Les deux valeurs qui, elles, DOIVENT être substituées.
    assert _git(banc, banc.depot, "rev-parse", "main-borne") in sortie


def test_l_execution_n_a_rien_ecrit_dans_le_depot_reel(banc):
    """Le test ne doit toucher que son dépôt temporaire. `--preparer` écrit une
    branche et un tag : si `cwd` avait été mal placé, ils seraient ici."""
    reelles = subprocess.run(
        ["git", "-C", str(RACINE), "for-each-ref", "--format=%(refname)"],
        check=True, capture_output=True, text=True,
    ).stdout.split()
    assert "refs/heads/main-borne" not in reelles
    assert not [r for r in reelles if r.startswith("refs/tags/archive/pre-borne-")]
    # Ni les fichiers de la fixture. On interroge git plutôt que le disque :
    # un littéral de chemin ancré à la racine serait relevé par
    # `test_ci_perimetre_sparse_checkout` comme un chemin que la suite LIT, et
    # réclamerait son entrée dans le sparse-checkout — pour un fichier qui
    # n'existe justement nulle part.
    salissures = subprocess.run(
        ["git", "-C", str(RACINE), "status", "--porcelain"],
        check=True, capture_output=True, text=True,
    ).stdout
    assert "corpus.bin" not in salissures, "la fixture a débordé dans le dépôt réel"
