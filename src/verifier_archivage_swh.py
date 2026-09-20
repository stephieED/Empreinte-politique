#!/usr/bin/env python3
"""
verifier_archivage_swh.py — les SHA cités résolvent-ils dans Software Heritage ?
(#568, sous-issue de #566)

**Ce que ce script remplace.** L'étape 2b de
`scripts/borner_historique_donnees.sh --preparer` décrivait cette vérification
en prose, sous la forme d'une boucle `curl` à recopier. Elle est faite sous
pression, juste avant une opération irréversible — le moment exact où l'on
saute une étape. Or c'est elle qui distingue un archivage d'un rituel
(#551, question 4 : « une vérification après archivage, sinon c'est un
rituel »).

**Pourquoi ce n'est pas une boucle de trois lignes.** La boucle en prose
itérait sur `git log --format=%H`, c'est-à-dire sur **tout** l'historique :
677 commits pour un quota anonyme de 120 requêtes/heure, soit six heures de
temporisation pour vérifier une population qui n'est pas celle qui compte. Ce
qui compte, ce sont les SHA **effectivement cités** — ceux qui cesseraient de
résoudre pour un lecteur d'issue ou de journal de décision. Ils sont noyés dans
la prose des fichiers `.md` suivis et des corps d'issues, et le tri manuel est
le meilleur moyen d'en oublier : au 28/08/2026, **135 chaînes hexadécimales
extraites de 42 fichiers `.md` et 260 corps d'issues, dont 47 résolvent en
commit**. Le reste est fait d'horodatages, d'identifiants de run et de sommes
de contrôle. (#551 relevait 124 pour 42 quelques heures plus tôt le même jour,
sur `dc3ba83` et 253 issues. La population bouge d'un commit et d'une issue à
l'autre : c'est précisément pourquoi on l'outille au lieu de la recopier.)

**Trois états, pas deux.** Un SHA absent de l'archive et une visite qui n'a pas
conclu ne se traitent pas pareil, et les confondre coûte dans les deux sens :
renoncer à une coupure légitime parce que l'ingestion est en cours, ou
l'autoriser alors que l'archive est incomplète. D'où :

  VÉRIFIÉ (0)      la visite est `full` et tous les SHA cités résolvent.
  MANQUANTS (1)    la visite est `full` et des SHA cités n'y sont pas. C'est un
                   vrai manque : ne pas couper.
  INDÉTERMINÉ (2)  la visite n'a pas conclu, le quota est épuisé, ou l'API est
                   injoignable. On n'a rien établi : réessayer, ne pas couper.

Le code de sortie porte le verdict ; la sortie nomme les SHA manquants et **où
ils sont cités**. « 3 manquants » n'aide personne ; « `deb28a7`, cité dans
#429, ne résout pas » se traite.

**Une quatrième situation, découverte au premier lancement réel** (28/08/2026)
et qu'il aurait été facile de confondre avec un manque d'archive : un SHA cité
qui résout dans le clone local mais n'est **atteignable depuis aucune ref**. Il
vient d'une branche de PR récrite par un rebase ou un `--force`, il survit ici
en objet pendant, et GitHub ne l'a jamais servi depuis une branche ou un tag.
Software Heritage archive ce qui est atteignable depuis les refs de l'origine :
un tel commit ne pouvait pas y entrer, et **relancer « Save Code Now » n'y
changera rien**.

C'est une citation déjà cassée pour un tiers, aujourd'hui, indépendamment de
toute coupure — donc un défaut de documentation, pas un défaut d'archive. Le
script la nomme sous l'étiquette CITATIONS ORPHELINES et **ne bloque pas**
dessus : couper n'aggrave rien, et un verdict rouge permanent finirait par ne
plus être lu. Ce qui bloque, c'est un SHA atteignable et pourtant absent de
l'archive — celui-là, la coupure le perdrait vraiment.

**Le périmètre suit la coupure, quand on la donne** (#575, quatrième cas de la nomenclature).
Vérifier TOUS les SHA cités alors que seuls les ancêtres du point de coupure
sont à risque produit un blocage presque systématique : Software Heritage
repasse tous les ~11 jours, donc tout commit fusionné depuis sa dernière visite
paraît « manquant » sans rien risquer. Mesuré le 28/08/2026 sur le banc de
répétition de #569, fenêtre 5 : **38 SHA cités, 28 perdus par la coupure et 10
conservés** — et le script a bloqué sur un des 10 conservés, c'est-à-dire pour
une raison qui n'existait pas. C'est le raisonnement des orphelines appliqué à
un autre axe, et personne ne l'avait vu parce que le script n'avait jamais
tourné contre une coupure réelle.

  CONSERVÉ PAR LA COUPURE   cité, non ancêtre du point de coupure. Il n'est pas
                            interrogé et il ne bloque JAMAIS : après la coupure,
                            le dépôt en reste la copie de référence.

La nuance à ne pas perdre : ces SHA **tomberont sous une coupure future**, et
l'archive les couvrira d'ici là — SWH repasse bien avant la prochaine coupure.
Ce n'est donc pas « ils n'ont pas besoin d'archive », c'est « **pas pour cette
coupure-ci** ». La sortie le dit ainsi, sinon on croira l'archive facultative.

**Sans point de coupure, le périmètre reste TOUT — et la sortie le dit.** Une
vérification sans coupure connue est un **audit d'archive**, pas un feu vert de
coupure : les deux usages sont légitimes, ils ne rendent pas le même verdict.

**L'origine est celle du dépôt, plus celle du code** (#575, second défaut).
Lancé le 28/08/2026 sur un banc dont le remote est autre, le script interrogeait
l'archive du dépôt RÉEL sans le signaler, et rendait un verdict confiant sur la
mauvaise origine. Il n'échouait pas — c'est pire : un fork, un miroir, un dépôt
renommé ou un clone de travail obtenaient un « VÉRIFIÉ » qui ne parlait pas
d'eux, et c'est précisément dans ces situations qu'on lance une vérification.
L'origine est maintenant dérivée de `git remote get-url origin`,
`ORIGINE_PAR_DEFAUT` n'en est plus que le repli — **annoncé quand il
s'applique** — et la provenance figure dans la sortie à côté du snapshot.

Les formes sont **normalisées** avant interrogation : `git@github.com:o/r.git`,
`ssh://git@github.com/o/r` et `https://github.com/o/r/` désignent la même
origine pour Software Heritage, pas pour une comparaison de chaînes. Sans ça,
la correction déplacerait le défaut au lieu de le corriger.

**Quota.** L'API anonyme de Software Heritage limite la route
`/api/1/revision/` à **120 requêtes/heure** (relevé le 28/08/2026 dans
l'en-tête `X-RateLimit-Limit`). Le script lit `X-RateLimit-Remaining` et
`X-RateLimit-Reset` à chaque réponse, temporise **en le disant** plutôt que
d'échouer en silence sur un `429`, et borne l'attente cumulée
(`--attente-max`) pour qu'un lancement ne puisse pas se transformer en veille
d'une heure sans l'annoncer.

**Ce script ne coupe rien, ne pousse rien, n'écrit rien dans le dépôt.** Il
lit, il interroge, il rend un verdict.

Usage :
    python3 src/verifier_archivage_swh.py                      # AUDIT d'archive
    python3 src/verifier_archivage_swh.py --fenetre 30         # feu vert de coupure
    python3 src/verifier_archivage_swh.py --coupure de23b62    # idem, point explicite
    python3 src/verifier_archivage_swh.py --sans-issues        # .md seulement
    python3 src/verifier_archivage_swh.py --json audit/swh.json

Voir `docs/decisions/fenetre-recalibrage-551.md`, question 4, et
`docs/decisions/perimetre-coupure-575.md`.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from audit_volumetrie_profils import MOTIF_COMMIT_DONNEES

# REPLI, et rien de plus (#575). L'origine interrogée est dérivée de
# `git remote get-url origin` ; cette valeur ne sert que lorsqu'il n'y a aucun
# remote, et la sortie l'annonce alors explicitement. Elle était le défaut
# silencieux jusqu'au 28/08/2026, et faisait rendre un verdict confiant sur
# l'archive d'un autre dépôt que celui qu'on tenait sous la main.
ORIGINE_PAR_DEFAUT = "https://github.com/stephieED/Empreinte-politique-src"
BASE_SWH = "https://archive.softwareheritage.org/api/1"

# 7 caractères est la longueur de SHA abrégé que git rend par défaut, et celle
# dans laquelle les citations de ce dépôt sont écrites. Les gardes
# lookbehind/lookahead écartent les fragments d'un mot plus long : sans elles,
# une chaîne de 41 caractères rendrait ses 40 premiers, et `deadbeefcafe` serait
# extrait de `xdeadbeefcafe`.
MOTIF_SHA = re.compile(r"(?<![0-9A-Za-z])([0-9a-f]{7,40})(?![0-9A-Za-z])")

# Au-delà, la sortie cesse d'être lisible : on nomme les premiers et on compte
# le reste. Ne s'applique qu'aux LIEUX de citation d'un même SHA, jamais aux
# SHA manquants eux-mêmes — ceux-là sont tous nommés, c'est l'objet du script.
MAX_LIEUX_AFFICHES = 4

# Même raison, pour les SHA conservés par la coupure. Ceux-là ne sont
# ACTIONNABLES par personne — ils ne demandent rien — et une fenêtre non
# contraignante les met tous dans ce cas : au 28/08/2026, ce serait les 47 SHA
# cités du dépôt. Les compter et en nommer quelques-uns suffit ; le rapport
# `--json` porte la liste entière pour qui la veut.
MAX_CONSERVES_AFFICHES = 10


# ── Extraction ───────────────────────────────────────────────────────────────


@dataclass
class Citation:
    """Une chaîne hexadécimale trouvée dans un texte, et l'endroit où elle
    l'a été. Le lieu est ce qui rend un manque traitable."""

    chaine: str
    lieu: str


@dataclass
class CommitCite:
    """Un SHA qui résout en commit du dépôt, et tous ses lieux de citation."""

    sha: str
    lieux: list[str] = field(default_factory=list)
    date: Optional[str] = None
    # presente | absente | indetermine | conserve | non_verifie
    etat: str = "non_verifie"
    detail: str = ""
    # Atteignable depuis une ref du clone local ? Calculé PARESSEUSEMENT, et
    # seulement pour les SHA absents de l'archive : c'est la seule question à
    # laquelle il sert de répondre, et la calculer pour les 47 coûterait 47
    # parcours de graphe pour rien.
    atteignable: Optional[bool] = None
    ref: Optional[str] = None

    @property
    def court(self) -> str:
        return self.sha[:7]

    @property
    def orpheline(self) -> bool:
        """Citation déjà cassée avant toute coupure : le commit n'est
        atteignable depuis aucune ref, donc jamais servi par l'origine, donc
        jamais archivable."""
        return self.etat == "absente" and self.atteignable is False

    @property
    def conserve(self) -> bool:
        """Hors du périmètre de CETTE coupure-ci (#575) : le commit n'est pas
        ancêtre du point de coupure, donc le dépôt en reste la copie de
        référence après l'opération. Il n'est pas interrogé, et il ne bloque
        jamais.

        À ne pas lire comme « pas besoin d'archive » : il tombera sous une
        coupure FUTURE, et Software Heritage repasse bien avant."""
        return self.etat == "conserve"


def extraire_chaines(texte: str) -> list[str]:
    """Les chaînes hexadécimales de 7 caractères ou plus d'un texte.

    Aucun filtrage sémantique ici : une somme de contrôle, un identifiant
    d'artefact ou un nombre en base 10 fait de chiffres hexadécimaux passent.
    C'est `resoudre_commits()` qui tranche, et git est le seul arbitre légitime.
    """
    return [m.group(1).lower() for m in MOTIF_SHA.finditer(texte)]


def citations_des_fichiers_md(
    racine: str, lire: Callable[[str], str], fichiers: Iterable[str]
) -> list[Citation]:
    """Balaie les fichiers `.md` **suivis par git**, ligne à ligne.

    Ligne à ligne parce que le lieu doit être actionnable : « cité dans
    `docs/technical_decisions.md` » envoie chercher dans 2 000 lignes ;
    « `docs/technical_decisions.md:412` » s'ouvre.
    """
    citations: list[Citation] = []
    for chemin in fichiers:
        try:
            texte = lire(f"{racine}/{chemin}")
        except OSError as err:  # un fichier suivi mais absent du disque
            print(f"[!] {chemin} illisible : {err}", file=sys.stderr)
            continue
        for numero, ligne in enumerate(texte.split("\n"), start=1):
            for chaine in extraire_chaines(ligne):
                citations.append(Citation(chaine, f"{chemin}:{numero}"))
    return citations


def citations_des_issues(issues: Iterable[dict[str, Any]]) -> list[Citation]:
    """Balaie les corps d'issues. Le lieu est `#<numéro>`, la seule adresse
    stable — un titre se récrit, un numéro non.

    Les commentaires ne sont pas couverts : `gh issue list` ne les rend pas, et
    les tirer coûterait une requête API par issue. La population vérifiée est
    donc un peu plus étroite que la population citée, et c'est dit dans le
    rapport plutôt que passé sous silence.
    """
    citations: list[Citation] = []
    for issue in issues:
        numero = issue.get("number")
        corps = issue.get("body") or ""
        for chaine in extraire_chaines(corps):
            citations.append(Citation(chaine, f"#{numero}"))
    return citations


# ── Résolution par git ───────────────────────────────────────────────────────


def resoudre_commits(
    citations: Iterable[Citation],
    batch_check: Callable[[list[str]], dict[str, Optional[str]]],
    dater: Callable[[list[str]], dict[str, str]] = lambda shas: {},
) -> tuple[list[CommitCite], int]:
    """Ne garde que les chaînes qui résolvent en **commit** du dépôt.

    Rend `(commits, nb_chaines_distinctes)`. L'écart entre les deux est le
    chiffre à citer : « 42 SHA cités sur 124 chaînes extraites » — nommer la
    population, jamais le seul total.

    Deux chaînes différentes peuvent désigner le même commit (une abrégée, une
    complète) : elles fusionnent sur le SHA plein, et leurs lieux s'additionnent.
    """
    par_chaine: dict[str, list[str]] = {}
    for citation in citations:
        par_chaine.setdefault(citation.chaine, []).append(citation.lieu)

    resolus = batch_check(sorted(par_chaine))

    commits: dict[str, CommitCite] = {}
    for chaine, sha in resolus.items():
        if sha is None:
            continue
        commit = commits.setdefault(sha, CommitCite(sha=sha))
        for lieu in par_chaine.get(chaine, []):
            if lieu not in commit.lieux:
                commit.lieux.append(lieu)

    dates = dater(sorted(commits)) if commits else {}
    for sha, commit in commits.items():
        commit.date = dates.get(sha)

    ordonnes = sorted(commits.values(), key=lambda c: (c.date or "", c.sha))
    return ordonnes, len(par_chaine)


def _batch_check_git(racine: str) -> Callable[[list[str]], dict[str, Optional[str]]]:
    """`git cat-file --batch-check` : une seule invocation pour toute la
    population, là où un `cat-file -t` par chaîne en ferait 124.

    Rend la chaîne d'entrée -> SHA plein si elle résout en commit, `None`
    sinon. Un `tree`, un `blob`, un `tag`, un `missing` ou un `ambiguous` sont
    tous des non-commits : seuls les commits cessent de résoudre après une
    coupure d'historique.
    """

    def executer(chaines: list[str]) -> dict[str, Optional[str]]:
        if not chaines:
            return {}
        sortie = subprocess.run(
            ["git", "-C", racine, "cat-file", "--batch-check"],
            input="\n".join(chaines) + "\n",
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        resultats: dict[str, Optional[str]] = {}
        for chaine, ligne in zip(chaines, sortie.strip().split("\n")):
            champs = ligne.split()
            resultats[chaine] = (
                champs[0] if len(champs) >= 2 and champs[1] == "commit" else None
            )
        return resultats

    return executer


def _dater_git(racine: str) -> Callable[[list[str]], dict[str, str]]:
    """Date d'auteur ISO de chaque commit, pour ordonner le rapport du plus
    ancien au plus récent — l'ordre dans lequel une coupure les emporte."""

    def executer(shas: list[str]) -> dict[str, str]:
        dates: dict[str, str] = {}
        for sha in shas:
            try:
                dates[sha] = subprocess.run(
                    ["git", "-C", racine, "log", "-1", "--format=%aI", sha],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            except subprocess.CalledProcessError:
                continue
        return dates

    return executer


# Les seules familles de refs qu'un archiveur peut voir depuis l'origine. Le
# balayage est délibérément restreint :
#   - `refs/pull/<n>/head` : GitHub la sert, mais Software Heritage n'archive
#     pas les refs de pull request. La question posée est « l'origine a-t-elle
#     jamais offert ce commit à un archiveur ? », pas « GitHub le sert-il ? » ;
#   - `refs/claude/*`, `refs/stash`, `refs/notes/*` : elles n'existent que dans
#     ce clone. Les compter ferait passer pour un trou d'archive un commit que
#     l'origine n'a jamais porté — donc bloquer à tort une coupure légitime.
# Ça reste une APPROXIMATION, et il faut savoir dans quel sens elle penche : une
# branche locale déjà supprimée sur l'origine compte encore. L'erreur possible
# est donc « MANQUANT » au lieu d'« orpheline », c'est-à-dire un blocage de
# trop — jamais une autorisation de trop. C'est le bon sens pour un garde-fou
# posé devant une opération irréversible.
FAMILLES_DE_REFS_DE_L_ORIGINE = ("refs/heads", "refs/tags", "refs/remotes/origin")


def _refs_contenant_git(racine: str) -> Callable[[str], Optional[str]]:
    """La première ref de l'origine d'où un commit est atteignable, ou `None`
    s'il n'y en a aucune — auquel cas Software Heritage n'a jamais pu le voir.
    """

    def executer(sha: str) -> Optional[str]:
        try:
            sortie = subprocess.run(
                ["git", "-C", racine, "for-each-ref",
                 f"--contains={sha}", "--count=1", "--format=%(refname)",
                 *FAMILLES_DE_REFS_DE_L_ORIGINE],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            return None
        return sortie or None

    return executer


# ── Origine : celle du dépôt, pas celle du code (#575) ───────────────────────

# Les schémas qui désignent le même dépôt qu'un `https://`. Software Heritage
# indexe une origine PAR SON URL : deux écritures de la même origine sont deux
# origines pour une comparaison de chaînes, et une seule pour l'archive.
SCHEMAS_EQUIVALENTS_A_HTTPS = ("ssh", "git", "git+ssh", "git+https")

# La forme « scp » de git — `git@github.com:stephieED/x.git` — n'a ni schéma ni
# `//`. Le `(?!//)` écarte `hote://…`, qui est un schéma mal écrit, pas un
# chemin scp.
MOTIF_ORIGINE_SCP = re.compile(r"^(?:[^@/]+@)?([^:/]+):(?!//)(.+)$")


def normaliser_origine(url: Optional[str]) -> Optional[str]:
    """Ramène les écritures d'une même origine à une seule.

    `git@github.com:o/r.git`, `ssh://git@github.com/o/r`, `https://github.com/o/r/`
    et `https://github.com/o/r.git` désignent le même dépôt pour Software
    Heritage. Sans cette normalisation, dériver l'origine du remote
    DÉPLACERAIT le défaut de #575 au lieu de le corriger : un clone en SSH
    interrogerait une origine que l'archive ne connaît pas, et rendrait
    « origine inconnue » sur un dépôt parfaitement archivé.
    """
    if not url:
        return None
    brut = url.strip()
    if not brut:
        return None
    if "://" in brut:
        schema, _, reste = brut.partition("://")
        schema = schema.lower()
        if schema in SCHEMAS_EQUIVALENTS_A_HTTPS:
            schema = "https"
    else:
        scp = MOTIF_ORIGINE_SCP.match(brut)
        if not scp:
            # Un chemin local (`/srv/miroir.git`) : rien à normaliser au-delà
            # du suffixe. Ce n'est pas une origine que SWH connaîtra, et c'est
            # justement ce qu'il faut donner à voir dans la sortie.
            return brut.rstrip("/").removesuffix(".git").rstrip("/") or None
        schema, reste = "https", f"{scp.group(1)}/{scp.group(2)}"
    hote, _, chemin = reste.partition("/")
    hote = hote.rpartition("@")[2].lower()  # retire un `utilisateur[:mdp]@`
    if schema == "https" and hote.endswith(":443"):
        hote = hote.removesuffix(":443")
    if schema == "http" and hote.endswith(":80"):
        hote = hote.removesuffix(":80")
    chemin = chemin.rstrip("/").removesuffix(".git").rstrip("/")
    return f"{schema}://{hote}/{chemin}" if chemin else f"{schema}://{hote}"


def _remote_git(racine: str) -> Callable[[], Optional[str]]:
    """L'URL du remote `origin`, ou `None` — un dépôt tout neuf, un clone sans
    remote, un banc monté par `git init` n'en ont pas."""

    def executer() -> Optional[str]:
        try:
            sortie = subprocess.run(
                ["git", "-C", racine, "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        except (subprocess.CalledProcessError, OSError):
            return None
        return sortie or None

    return executer


def resoudre_origine(
    explicite: Optional[str], remote: Callable[[], Optional[str]]
) -> tuple[str, str]:
    """Rend `(origine interrogée, provenance)`.

    La provenance est faite pour être IMPRIMÉE, et c'est elle qui manquait le
    28/08/2026 : le script interrogeait l'archive du dépôt réel depuis un banc
    de répétition, et rien dans sa sortie ne permettait de s'en apercevoir.
    """
    if explicite:
        return (normaliser_origine(explicite) or explicite), "donnée par `--origine`"
    brut = remote()
    derivee = normaliser_origine(brut)
    if derivee:
        provenance = "dérivée de `git remote get-url origin`"
        if brut and brut.strip() != derivee:
            provenance += f" — {brut.strip()}, normalisée"
        return derivee, provenance
    return (
        normaliser_origine(ORIGINE_PAR_DEFAUT) or ORIGINE_PAR_DEFAUT,
        "REPLI sur ORIGINE_PAR_DEFAUT — aucun remote `origin` dans ce dépôt : "
        "vérifier que c'est bien l'origine qu'on veut interroger",
    )


# ── Point de coupure (#575) ──────────────────────────────────────────────────


@dataclass
class Coupure:
    """Le point de coupure que `borner_historique_donnees.sh` s'apprête à faire.

    `sha is None` veut dire « fenêtre demandée mais NON CONTRAIGNANTE » : il n'y
    a pas de coupure, donc rien à perdre. C'est autre chose qu'aucune coupure
    demandée (`coupure is None`), qui laisse le script à son mode d'audit et
    vérifie tout.
    """

    sha: Optional[str]
    demande: str
    fenetre: Optional[int] = None

    @property
    def contraignante(self) -> bool:
        return self.sha is not None

    @property
    def court(self) -> str:
        return self.sha[:7] if self.sha else "aucune"


def _coupure_par_fenetre_git(racine: str) -> Callable[[int], Optional[str]]:
    """Le MÊME calcul que la fonction `_coupure()` de
    `scripts/borner_historique_donnees.sh` : les commits de données de `main`,
    du plus récent au plus ancien, et le (N+1)-ième est le point de coupure.

    Le motif vient d'`audit_volumetrie_profils.MOTIF_COMMIT_DONNEES`, pas d'une
    copie locale : vérifier une coupure différente de celle qui sera faite
    serait exactement le défaut que #575 corrige, avec un pas de côté de plus.
    """

    def executer(fenetre: int) -> Optional[str]:
        try:
            sortie = subprocess.run(
                ["git", "-C", racine, "log", "--format=%H",
                 f"--grep={MOTIF_COMMIT_DONNEES}", "main"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.split()
        except (subprocess.CalledProcessError, OSError):
            return None
        return sortie[fenetre] if len(sortie) > fenetre else None

    return executer


def _est_ancetre_git(racine: str) -> Callable[[str, str], bool]:
    """`git merge-base --is-ancestor` : 0 si oui, 1 si non. C'est la question
    exacte — « la coupure emporterait-elle ce commit ? »"""

    def executer(sha: str, coupure: str) -> bool:
        return subprocess.run(
            ["git", "-C", racine, "merge-base", "--is-ancestor", sha, coupure],
            capture_output=True,
            text=True,
        ).returncode == 0

    return executer


def _resoudre_ref_git(racine: str) -> Callable[[str], Optional[str]]:
    def executer(reference: str) -> Optional[str]:
        try:
            return subprocess.run(
                ["git", "-C", racine, "rev-parse", "--verify",
                 f"{reference}^{{commit}}"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip() or None
        except (subprocess.CalledProcessError, OSError):
            return None

    return executer


def resoudre_coupure(
    fenetre: Optional[int],
    commit: Optional[str],
    par_fenetre: Callable[[int], Optional[str]],
    resoudre_ref: Callable[[str], Optional[str]],
) -> Optional[Coupure]:
    """La coupure demandée, ou `None` si aucune ne l'a été (mode audit).

    Lève `ValueError` si la coupure demandée ne résout pas. Refuser de conclure
    vaut mieux que vérifier un autre périmètre que celui qu'on croit — c'est la
    forme même du défaut corrigé ici.
    """
    if commit:
        sha = resoudre_ref(commit)
        if not sha:
            raise ValueError(
                f"--coupure {commit} ne résout en aucun commit de ce dépôt : "
                "rien n'a été vérifié."
            )
        return Coupure(sha=sha, demande=f"--coupure {commit}")
    if fenetre is None:
        return None
    return Coupure(
        sha=par_fenetre(fenetre), demande=f"--fenetre {fenetre}", fenetre=fenetre
    )


def marquer_conserves(
    commits: Iterable[CommitCite],
    coupure: Optional[Coupure],
    est_ancetre: Callable[[str, str], bool],
) -> None:
    """Sort du périmètre les SHA que la coupure NE perdrait pas.

    Sans coupure connue, ne marque rien : le périmètre reste tout, et c'est le
    rapport qui dit que c'est un audit et non un feu vert.
    """
    if coupure is None:
        return
    for commit in commits:
        if not coupure.contraignante or not est_ancetre(commit.sha, coupure.sha):
            commit.etat = "conserve"


def fichiers_md_suivis(racine: str) -> list[str]:
    sortie = subprocess.run(
        ["git", "-C", racine, "ls-files", "*.md"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [ligne for ligne in sortie.split("\n") if ligne]


def corps_des_issues(racine: str, limite: int = 1000) -> list[dict[str, Any]]:
    """Les corps d'issues via `gh`. Tous états : une issue fermée cite autant
    qu'une ouverte, et son lecteur a le même besoin de vérifier."""
    sortie = subprocess.run(
        [
            "gh", "issue", "list", "--state", "all",
            "--limit", str(limite), "--json", "number,body",
        ],
        cwd=racine,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(sortie or "[]")


# ── Interrogation de Software Heritage ───────────────────────────────────────


@dataclass
class Reponse:
    """Le strict nécessaire d'une réponse HTTP, pour qu'un test puisse en
    fabriquer une sans réseau ni bibliothèque."""

    code: int
    corps: Any = None
    entetes: dict[str, str] = field(default_factory=dict)


def _fetch_reel(timeout: float = 30.0) -> Callable[[str], Reponse]:
    """Le seul point du script qui sorte sur le réseau. Isolé pour que tout le
    reste soit vérifiable hors ligne — la suite de tests ne joint jamais SWH
    (AGENTS.md §3 : aucun test ne sort sur le réseau)."""
    import requests

    session = requests.Session()

    def executer(url: str) -> Reponse:
        rep = session.get(url, timeout=timeout)
        try:
            corps = rep.json()
        except ValueError:
            corps = None
        return Reponse(rep.status_code, corps, dict(rep.headers))

    return executer


@dataclass
class Quota:
    """L'état du quota anonyme, tel que les en-têtes le rendent.

    Ce n'est pas un compteur tenu par le script : il est **lu** à chaque
    réponse. Un compteur local se désynchronise dès qu'un autre outil consomme
    le même quota depuis la même adresse IP — ce qui arrive exactement le jour
    où l'on vérifie à la main en parallèle.
    """

    limite: Optional[int] = None
    restant: Optional[int] = None
    reset: Optional[int] = None
    requetes: int = 0
    attente_totale: float = 0.0

    def lire(self, entetes: dict[str, str]) -> None:
        normalises = {k.lower(): v for k, v in entetes.items()}
        for cle, attribut in (
            ("x-ratelimit-limit", "limite"),
            ("x-ratelimit-remaining", "restant"),
            ("x-ratelimit-reset", "reset"),
        ):
            valeur = normalises.get(cle)
            if valeur is not None:
                try:
                    setattr(self, attribut, int(valeur))
                except ValueError:
                    pass


def _attente_avant_reset(quota: Quota, maintenant: float) -> float:
    """Secondes à patienter jusqu'à la remise à zéro du seau, plus une seconde
    de marge — un réveil pile à la borne retombe sur un `429`."""
    if quota.reset is None:
        return 60.0
    return max(0.0, quota.reset - maintenant) + 1.0


def _seau_vide(quota: Quota, maintenant: float) -> bool:
    """Le seau est-il vide **et l'attente sert-elle encore à quelque chose** ?

    `restant` est une photographie de la réponse précédente. Passé l'horodatage
    `reset`, elle est PÉRIMÉE : le seau a roulé, et la seule façon de connaître
    le nouveau compte est d'émettre une requête et de relire l'en-tête.

    Ne pas faire cette distinction produit un bavardage inutile, observé en
    conditions réelles le 28/08/2026 : vingt « quota épuisé — attente de 1 s »
    d'affilée après un reset, chacun suivi d'une requête qui passait très bien.
    Un garde-fou qui crie sans raison finit par n'être plus lu, et il masquait
    ici les deux VRAIES temporisations de la même exécution (702 s et 1 504 s).
    """
    if quota.restant is None or quota.restant > 0:
        return False
    return quota.reset is None or quota.reset > maintenant


def interroger_revision(
    sha: str,
    fetch: Callable[[str], Reponse],
    quota: Quota,
    dormir: Callable[[float], None] = time.sleep,
    horloge: Callable[[], float] = time.time,
    attente_max: float = 3900.0,
    journal: Callable[[str], None] = lambda m: print(m, file=sys.stderr),
    essais: int = 3,
) -> tuple[str, str]:
    """Un SHA résout-il dans l'archive ? Rend `(etat, detail)`.

    `presente` (200) · `absente` (404) · `indetermine` (tout le reste, quota
    épuisé compris). L'état `indetermine` n'est jamais confondu avec `absente` :
    ne pas trouver et ne pas avoir regardé sont deux choses différentes, et
    c'est la seconde qui doit faire réessayer plutôt que renoncer.
    """
    url = f"{BASE_SWH}/revision/{sha}/"
    for essai in range(1, essais + 1):
        # Temporisation PRÉVENTIVE : si la réponse précédente annonçait un seau
        # vide, on attend le reset au lieu d'aller chercher un 429.
        if _seau_vide(quota, horloge()):
            attente = _attente_avant_reset(quota, horloge())
            if quota.attente_totale + attente > attente_max:
                return (
                    "indetermine",
                    f"quota épuisé, reset dans {attente:.0f} s — au-delà de "
                    f"--attente-max ({attente_max:.0f} s)",
                )
            journal(
                f"    quota épuisé ({quota.limite or '?'} requêtes/heure) — "
                f"attente de {attente:.0f} s avant de reprendre"
            )
            dormir(attente)
            quota.attente_totale += attente
            quota.restant = None

        try:
            rep = fetch(url)
        except Exception as err:  # réseau, DNS, TLS, timeout
            return "indetermine", f"appel impossible : {type(err).__name__}: {err}"

        quota.requetes += 1
        quota.lire(rep.entetes)

        if rep.code == 200:
            return "presente", ""
        if rep.code == 404:
            return "absente", "404 : révision inconnue de l'archive"
        if rep.code == 429:
            attente = _attente_avant_reset(quota, horloge())
            if essai == essais or quota.attente_totale + attente > attente_max:
                return (
                    "indetermine",
                    f"429 (quota de {quota.limite or 120} requêtes/heure) après "
                    f"{essai} essai(s) — vérification non conclue",
                )
            journal(
                f"    429 sur {sha[:7]} : quota atteint, attente de "
                f"{attente:.0f} s puis nouvel essai"
            )
            dormir(attente)
            quota.attente_totale += attente
            continue
        return "indetermine", f"HTTP {rep.code} inattendu"
    return "indetermine", "essais épuisés"


def interroger_visite(
    origine: str, fetch: Callable[[str], Reponse], quota: Quota
) -> dict[str, Any]:
    """L'état de la dernière visite de l'origine.

    Rend `{"connue": bool, "statut": str|None, "snapshot": str|None,
    "date": str|None, "erreur": str|None}`. `statut == "full"` est la seule
    valeur qui autorise à lire un 404 comme un vrai manque.

    Ses en-têtes de quota sont comptés mais **pas lus** : cette route a son
    propre seau, mesuré à 700 requêtes/heure le 28/08/2026 contre 120 pour
    `/revision/`. Y recopier `restant` et `reset` ferait croire au reste du
    script qu'il dispose de 700 requêtes, et la temporisation ne se
    déclencherait qu'une fois le seau des révisions déjà vidé.
    """
    url = f"{BASE_SWH}/origin/{origine}/visit/latest/"
    try:
        rep = fetch(url)
    except Exception as err:
        return {"connue": False, "erreur": f"{type(err).__name__}: {err}"}
    quota.requetes += 1
    if rep.code == 404:
        return {"connue": False, "erreur": "origine inconnue de Software Heritage"}
    if rep.code != 200 or not isinstance(rep.corps, dict):
        return {"connue": False, "erreur": f"HTTP {rep.code}"}
    return {
        "connue": True,
        "statut": rep.corps.get("status"),
        "snapshot": rep.corps.get("snapshot"),
        "date": rep.corps.get("date"),
        "visite": rep.corps.get("visit"),
        "erreur": None,
    }


# ── Verdict et rapport ───────────────────────────────────────────────────────

VERIFIE, MANQUANTS, INDETERMINE = 0, 1, 2


def _population_chiffree(n: int, coupure: Optional["Coupure"]) -> str:
    """Nommer la population de chaque chiffre : « 3 sur 28 » ne dit rien tant
    qu'on ne sait pas de quels 28 il s'agit — et depuis #575, ces 28 ne sont
    plus les SHA cités mais les SHA cités que la coupure emporterait."""
    if coupure is not None and coupure.contraignante:
        return (
            f"{_accord(n, 'SHA cité', 'SHA cités')} ancêtre"
            f"{'s' if abs(n) > 1 else ''} de la coupure {coupure.court}"
        )
    return _accord(n, "SHA cité", "SHA cités")


def _reserve_orphelines(orphelines: list[CommitCite]) -> str:
    if not orphelines:
        return ""
    return (
        f" ({_accord(len(orphelines), 'citation orpheline signalée à part', 'citations orphelines signalées à part')} : "
        "ce qui n'est atteignable depuis aucune ref de l'origine n'a jamais pu "
        "être archivé, et est déjà irrésolvable pour un tiers.)"
    )


def _reserve_conserves(
    conserves: list[CommitCite], coupure: Optional["Coupure"]
) -> str:
    """La nuance de #575, à ne pas perdre : « pas pour cette coupure-ci » n'est
    pas « pas besoin d'archive ». Sans cette phrase, on croira l'archive
    facultative pour ces SHA — alors qu'ils tomberont sous une coupure future.
    """
    if not conserves or coupure is None:
        return ""
    if not coupure.contraignante:
        return (
            f" ({_accord(len(conserves), 'SHA cité', 'SHA cités')} hors périmètre : "
            f"la fenêtre demandée ({coupure.demande}) n'est PAS contraignante, "
            "il n'y a donc pas de coupure et rien à perdre. Ces SHA tomberont "
            "sous une coupure FUTURE : ce n'est pas « pas besoin d'archive », "
            "c'est « pas pour cette coupure-ci ».)"
        )
    pluriel = abs(len(conserves)) > 1
    return (
        f" ({_accord(len(conserves), 'SHA cité conservé', 'SHA cités conservés')} "
        f"par la coupure {coupure.court}, non interrogé{'s' if pluriel else ''} : "
        "après l'opération, le dépôt en reste la copie de référence. "
        + ("Ils tomberont" if pluriel else "Il tombera")
        + " sous une coupure FUTURE, et l'archive "
        + ("les" if pluriel else "le")
        + " couvrira d'ici là — ce n'est pas « pas besoin d'archive », c'est "
        "« pas pour cette coupure-ci ».)"
    )


def _reserve_perimetre(coupure: Optional["Coupure"]) -> str:
    """Sans point de coupure, le comportement reste celui d'avant #575 — mais
    la sortie dit désormais que le périmètre est plus large que le risque."""
    if coupure is not None:
        return ""
    return (
        " (AUDIT D'ARCHIVE, pas un feu vert de coupure : aucun point de coupure "
        "n'a été donné, le périmètre vérifié est donc TOUS les SHA cités — plus "
        "large que la population à risque, qui est celle des ancêtres de la "
        "coupure. Relancer avec `--fenetre N` ou `--coupure <commit>` pour "
        "obtenir un feu vert.)"
    )


def rendre_verdict(
    visite: dict[str, Any],
    commits: list[CommitCite],
    coupure: Optional["Coupure"] = None,
) -> tuple[int, str]:
    """Le cœur de la distinction demandée par #568, sur le périmètre demandé
    par #575.

    Une visite en cours n'est pas un échec d'archivage. Un SHA absent d'une
    visite `full` en est un — À CONDITION que la coupure le perde. Un SHA
    conservé par la coupure ne bloque jamais : c'est le blocage constaté le
    28/08/2026, sur un des 10 SHA que la coupure gardait.
    """
    if not commits:
        return INDETERMINE, (
            "Aucun SHA cité n'a été trouvé : population vide, il n'y a rien à "
            "conclure. Vérifier l'extraction avant de couper quoi que ce soit."
        )

    # Un absent atteignable depuis une ref est un vrai trou d'archive : la
    # coupure le perdrait. Un absent orphelin est déjà perdu aujourd'hui, et
    # couper n'y change rien — il ne bloque donc pas, il se signale. Un
    # conservé n'est même pas interrogé : la coupure ne le perd pas.
    conserves = [c for c in commits if c.conserve]
    a_risque = [c for c in commits if not c.conserve]
    absents = [c for c in a_risque if c.etat == "absente" and not c.orpheline]
    orphelines = [c for c in a_risque if c.orpheline]
    indetermines = [c for c in a_risque if c.etat in ("indetermine", "non_verifie")]
    visite_conclue = visite.get("connue") and visite.get("statut") == "full"
    reserve = (
        _reserve_orphelines(orphelines)
        + _reserve_conserves(conserves, coupure)
        + _reserve_perimetre(coupure)
    )
    archivables = len(a_risque) - len(orphelines)

    if not a_risque:
        return VERIFIE, (
            f"Aucun des {_accord(len(commits), 'SHA cité')} ne tombe sous la "
            "coupure : elle ne perdrait aucune citation, et il n'y avait rien "
            "à interroger." + reserve
        )
    if indetermines:
        un_seul = len(indetermines) == 1
        return INDETERMINE, (
            f"{len(indetermines)} des {_population_chiffree(len(a_risque), coupure)} "
            + ("n'a pas pu être interrogé" if un_seul else "n'ont pas pu être interrogés")
            + " (quota, réseau, ou réponse inattendue). On n'a rien établi : "
            "réessayer plus tard. NE PAS COUPER."
        )
    if not visite_conclue:
        statut = visite.get("statut") or visite.get("erreur") or "inconnu"
        if absents:
            un_seul = len(absents) == 1
            return INDETERMINE, (
                f"La visite n'est pas `full` (statut : {statut}) et "
                f"{len(absents)} des "
                f"{_population_chiffree(len(a_risque), coupure)} "
                + ("n'y résout pas encore" if un_seul else "n'y résolvent pas encore")
                + ". Ce n'est PAS un échec d'archivage : l'ingestion peut être "
                "en cours. Relancer cette vérification plus tard. NE PAS COUPER."
            )
        return VERIFIE, (
            f"Les {_accord(archivables, 'SHA cité archivable', 'SHA cités archivables')} "
            f"résolvent tous, bien que la visite ne soit pas encore `full` "
            f"(statut : {statut}). La condition de l'étape 2b est remplie ; "
            "attendre `full` reste plus prudent." + reserve
        )
    if absents:
        un_seul = len(absents) == 1
        return MANQUANTS, (
            f"{len(absents)} des "
            f"{_population_chiffree(len(a_risque), coupure)} "
            + ("ne résout pas alors qu'il est atteignable"
               if un_seul else "ne résolvent pas alors qu'ils sont atteignables")
            + " depuis une ref de l'origine, et la visite est `full` : "
            + ("c'est un vrai manque" if un_seul else "ce sont de vrais manques")
            + ", pas une ingestion en cours. NE PAS COUPER — relancer "
            "« Save Code Now », puis revérifier." + reserve
        )
    return VERIFIE, (
        f"Les {_accord(archivables, 'SHA cité archivable', 'SHA cités archivables')} "
        "résolvent tous dans une visite `full`. L'archivage n'est pas un "
        "rituel : la coupure peut suivre." + reserve
    )


def _accord(n: int, singulier: str, pluriel: Optional[str] = None) -> str:
    """« 1 SHA cité ne résout pas » / « 3 SHA cités ne résolvent pas ».

    Cette sortie est lue sous pression, juste avant une opération
    irréversible : une faute d'accord fait relire la phrase au lieu d'agir.
    """
    return f"{n} {singulier if abs(n) <= 1 else (pluriel or singulier + 's')}"


def _lieux(commit: CommitCite) -> str:
    lieux = commit.lieux[:MAX_LIEUX_AFFICHES]
    reste = len(commit.lieux) - len(lieux)
    texte = ", ".join(lieux)
    return f"{texte} (+{reste} autre{'s' if reste > 1 else ''})" if reste else texte


def formater_rapport(
    origine: str,
    visite: dict[str, Any],
    commits: list[CommitCite],
    nb_chaines: int,
    nb_md: int,
    nb_issues: int,
    quota: Quota,
    verdict: tuple[int, str],
    provenance: str = "",
    coupure: Optional["Coupure"] = None,
) -> str:
    code, message = verdict
    etiquette = {VERIFIE: "VÉRIFIÉ", MANQUANTS: "MANQUANTS", INDETERMINE: "INDÉTERMINÉ"}[code]
    lignes = [
        "Vérification d'archivage Software Heritage (#568, #575)",
        f"  origine : {origine}" + (f"\n            ({provenance})" if provenance else ""),
    ]

    if visite.get("connue"):
        lignes.append(
            f"  visite n°{visite.get('visite', '?')} : statut "
            f"{visite.get('statut')}, snapshot {visite.get('snapshot') or 'null'}"
            + (f", {visite['date']}" if visite.get("date") else "")
        )
    else:
        lignes.append(f"  visite : NON ÉTABLIE — {visite.get('erreur')}")

    conserves = [c for c in commits if c.conserve]
    a_risque = [c for c in commits if not c.conserve]
    presents = sum(1 for c in a_risque if c.etat == "presente")
    orphelines = [c for c in a_risque if c.orpheline]
    absents = [c for c in a_risque if c.etat == "absente" and not c.orpheline]
    indetermines = [c for c in a_risque if c.etat in ("indetermine", "non_verifie")]

    # Le périmètre, avant les chiffres : c'est lui qui dit ce que le verdict
    # engage. Le lire après les totaux, c'est le lire trop tard.
    if coupure is None:
        lignes += [
            "  périmètre : TOUS les SHA cités — AUDIT D'ARCHIVE, pas un feu vert",
            "              de coupure. La population à RISQUE est celle des ancêtres",
            "              du point de coupure : `--fenetre N` ou `--coupure <commit>`.",
        ]
    elif coupure.contraignante:
        lignes.append(
            f"  périmètre : coupure {coupure.court} ({coupure.demande}) — "
            f"{_accord(len(a_risque), 'SHA cité', 'SHA cités')} sous la coupure, "
            f"{_accord(len(conserves), 'conservé', 'conservés')}."
        )
    else:
        lignes.append(
            f"  périmètre : fenêtre NON contraignante ({coupure.demande}) — aucune "
            f"coupure, les {len(commits)} SHA cités sont tous conservés."
        )

    lignes += [
        "",
        f"  population : {_accord(nb_chaines, 'chaîne hexadécimale extraite', 'chaînes hexadécimales extraites')} de "
        f"{_accord(nb_md, 'fichier .md suivi', 'fichiers .md suivis')} et "
        + _accord(nb_issues, "corps d'issue", "corps d'issues"),
        "               (commentaires d'issues EXCLUS : la population citée est "
        "un peu plus large),",
        f"               dont {len(commits)} "
        + ("résout" if len(commits) <= 1 else "résolvent")
        + " en commit du dépôt (`git cat-file -t` == commit).",
        f"  résultat   : sur les {len(a_risque)} SHA du périmètre, {presents} dans "
        f"l'archive · {len(absents)} manquant(s) · {len(orphelines)} orpheline(s) "
        f"· {len(indetermines)} indéterminé(s)"
        + (
            f" ; {_accord(len(conserves), 'conservé', 'conservés')} hors "
            "périmètre."
            if conserves
            else "."
        ),
        f"  quota      : {_accord(quota.requetes, 'requête émise', 'requêtes émises')}"
        + (
            f", {quota.restant} restantes sur {quota.limite} par heure"
            if quota.restant is not None
            else ""
        )
        + (
            f", {quota.attente_totale:.0f} s d'attente cumulée"
            if quota.attente_totale
            else ""
        ),
    ]

    # Nommer, pas compter : c'est la demande explicite de #568.
    groupes = (
        ("MANQUANTS — archivables et pourtant absents ; la coupure les perdrait",
         absents),
        ("CITATIONS ORPHELINES — atteignables depuis aucune ref de l'origine, "
         "donc jamais\n  archivables ; déjà irrésolvables pour un tiers, et la "
         "coupure n'y change rien.\n  Corriger la citation, pas l'archive",
         orphelines),
        ("INDÉTERMINÉS — non conclus, ni présents ni absents", indetermines),
    )
    for titre, groupe in groupes:
        if not groupe:
            continue
        lignes += ["", f"  {titre} :"]
        for commit in groupe:
            date = f" ({commit.date[:10]})" if commit.date else ""
            lignes.append(f"    {commit.court}{date} — cité dans {_lieux(commit)}")
            if commit.detail:
                lignes.append(f"        {commit.detail}")

    if conserves:
        lignes += [
            "",
            "  CONSERVÉS PAR LA COUPURE — cités, non ancêtres du point de coupure,",
            "  donc NON interrogés : après l'opération, le dépôt en reste la copie de",
            "  référence. Ils tomberont sous une coupure FUTURE et l'archive les",
            "  couvrira d'ici là : ce n'est pas « pas besoin d'archive », c'est",
            "  « pas pour cette coupure-ci ». Ne jamais bloquer dessus :",
        ]
        for commit in conserves[:MAX_CONSERVES_AFFICHES]:
            date = f" ({commit.date[:10]})" if commit.date else ""
            lignes.append(f"    {commit.court}{date} — cité dans {_lieux(commit)}")
        reste = len(conserves) - MAX_CONSERVES_AFFICHES
        if reste > 0:
            lignes.append(
                f"    (+{reste} autre{'s' if reste > 1 else ''} — la liste "
                "entière est dans le rapport `--json`)"
            )

    lignes += ["", f"  VERDICT : {etiquette}", f"  {message}"]
    return "\n".join(lignes)


def rapport_json(
    origine: str,
    visite: dict[str, Any],
    commits: list[CommitCite],
    nb_chaines: int,
    nb_md: int,
    nb_issues: int,
    quota: Quota,
    verdict: tuple[int, str],
    provenance: str = "",
    coupure: Optional["Coupure"] = None,
) -> dict[str, Any]:
    conserves = [c for c in commits if c.conserve]
    return {
        "origine": origine,
        "origine_provenance": provenance,
        "coupure": (
            None
            if coupure is None
            else {
                "sha": coupure.sha,
                "fenetre": coupure.fenetre,
                "demande": coupure.demande,
                "contraignante": coupure.contraignante,
            }
        ),
        "visite": visite,
        "population": {
            "chaines_extraites": nb_chaines,
            "fichiers_md": nb_md,
            "issues": nb_issues,
            "sha_resolus_en_commit": len(commits),
            "sha_sous_la_coupure": len(commits) - len(conserves),
            "sha_conserves_par_la_coupure": len(conserves),
        },
        "verdict": {"code": verdict[0], "message": verdict[1]},
        "quota": {
            "limite": quota.limite,
            "restant": quota.restant,
            "requetes": quota.requetes,
            "attente_totale_s": quota.attente_totale,
        },
        "commits": [
            {
                "sha": c.sha,
                "date": c.date,
                "etat": c.etat,
                "detail": c.detail,
                "atteignable": c.atteignable,
                "ref": c.ref,
                "orpheline": c.orpheline,
                "conserve": c.conserve,
                "lieux": c.lieux,
            }
            for c in commits
        ],
    }


# ── Assemblage ───────────────────────────────────────────────────────────────


def verifier(
    racine: str,
    origine: Optional[str] = None,
    avec_issues: bool = True,
    fenetre: Optional[int] = None,
    commit_coupure: Optional[str] = None,
    fetch: Optional[Callable[[str], Reponse]] = None,
    lire: Optional[Callable[[str], str]] = None,
    lister_md: Optional[Callable[[], list[str]]] = None,
    lister_issues: Optional[Callable[[], list[dict[str, Any]]]] = None,
    batch_check: Optional[Callable[[list[str]], dict[str, Optional[str]]]] = None,
    dater: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ref_contenant: Optional[Callable[[str], Optional[str]]] = None,
    remote: Optional[Callable[[], Optional[str]]] = None,
    coupure_par_fenetre: Optional[Callable[[int], Optional[str]]] = None,
    resoudre_ref: Optional[Callable[[str], Optional[str]]] = None,
    est_ancetre: Optional[Callable[[str, str], bool]] = None,
    attente_max: float = 3900.0,
    dormir: Callable[[float], None] = time.sleep,
    horloge: Callable[[], float] = time.time,
    journal: Callable[[str], None] = lambda m: print(m, file=sys.stderr),
) -> tuple[int, dict[str, Any], str]:
    """Le déroulé complet. Toutes les dépendances externes — git, `gh`, le
    disque, le réseau — sont injectables : c'est ce qui rend le script
    vérifiable sans jamais joindre l'API depuis la CI (#551 : aucune mesure
    lourde en CI, et la vérification d'archivage est un geste de pré-coupure).

    `origine=None` fait DÉRIVER l'origine du remote `origin` (#575) ; la passer
    explicitement reste possible et l'emporte. `fenetre` ou `commit_coupure`
    donnent le point de coupure ; sans eux, le périmètre reste tout et le
    rapport dit que c'est un audit, pas un feu vert."""
    fetch = fetch or _fetch_reel()
    # `errors="replace"` : un .md mal encodé ne doit pas faire renoncer à toute
    # la vérification juste avant une opération irréversible.
    lire = lire or (
        lambda p: Path(p).read_text(encoding="utf-8", errors="replace")
    )
    lister_md = lister_md or (lambda: fichiers_md_suivis(racine))
    batch_check = batch_check or _batch_check_git(racine)
    dater = dater or _dater_git(racine)
    ref_contenant = ref_contenant or _refs_contenant_git(racine)
    remote = remote or _remote_git(racine)
    coupure_par_fenetre = coupure_par_fenetre or _coupure_par_fenetre_git(racine)
    resoudre_ref = resoudre_ref or _resoudre_ref_git(racine)
    est_ancetre = est_ancetre or _est_ancetre_git(racine)

    origine, provenance = resoudre_origine(origine, remote)
    coupure = resoudre_coupure(
        fenetre, commit_coupure, coupure_par_fenetre, resoudre_ref
    )

    fichiers = lister_md()
    citations = citations_des_fichiers_md(racine, lire, fichiers)
    issues: list[dict[str, Any]] = []
    if avec_issues:
        lister_issues = lister_issues or (lambda: corps_des_issues(racine))
        try:
            issues = lister_issues()
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as err:
            # `gh` absent ou non authentifié : on continue sur les .md seuls,
            # en le disant. Un demi-périmètre annoncé vaut mieux qu'un échec
            # qui pousse à sauter l'étape.
            journal(f"[!] Corps d'issues indisponibles ({err}) — .md seuls.")
        citations += citations_des_issues(issues)

    commits, nb_chaines = resoudre_commits(citations, batch_check, dater)
    journal(
        f"→ {len(commits)} SHA cités résolvent en commit, sur {nb_chaines} "
        f"chaînes hexadécimales extraites de {len(fichiers)} fichiers .md "
        f"et {len(issues)} corps d'issues."
    )

    # Le périmètre AVANT les requêtes : c'est ce qui évite d'en émettre pour
    # des SHA que la coupure ne perd pas — 28 au lieu de 38 sur le banc du
    # 28/08/2026, et l'écart grandit avec la fenêtre.
    marquer_conserves(commits, coupure, est_ancetre)
    a_interroger = [c for c in commits if not c.conserve]
    journal(
        f"→ origine interrogée : {origine} ({provenance})."
    )
    if coupure is None:
        journal(
            "→ aucun point de coupure : AUDIT d'archive sur les "
            f"{len(commits)} SHA cités, pas un feu vert de coupure."
        )
    else:
        journal(
            f"→ périmètre : {len(a_interroger)} SHA sous la coupure "
            f"{coupure.court} ({coupure.demande}), "
            f"{len(commits) - len(a_interroger)} conservés et non interrogés."
        )

    quota = Quota()
    visite = interroger_visite(origine, fetch, quota)

    for index, commit in enumerate(a_interroger, start=1):
        commit.etat, commit.detail = interroger_revision(
            commit.sha,
            fetch,
            quota,
            dormir=dormir,
            horloge=horloge,
            attente_max=attente_max,
            journal=journal,
        )
        if commit.etat == "absente":
            # Seulement ici : distinguer un trou d'archive d'une citation déjà
            # orpheline ne se pose que pour un SHA effectivement absent.
            commit.ref = ref_contenant(commit.sha)
            commit.atteignable = commit.ref is not None
            commit.detail += (
                f" ; atteignable depuis {commit.ref} — l'archive a un trou"
                if commit.atteignable
                else " ; atteignable depuis AUCUNE ref de l'origine (branche de "
                "PR récrite ?) : elle ne l'a jamais servi, donc Software "
                "Heritage n'a jamais pu le voir. Relancer « Save Code Now » n'y "
                "changera rien — c'est la citation qu'il faut corriger"
            )
        if commit.etat != "presente":
            journal(f"  [{index}/{len(a_interroger)}] {commit.court} : {commit.etat}")

    verdict = rendre_verdict(visite, commits, coupure)
    texte = formater_rapport(
        origine, visite, commits, nb_chaines, len(fichiers), len(issues), quota,
        verdict, provenance, coupure,
    )
    donnees = rapport_json(
        origine, visite, commits, nb_chaines, len(fichiers), len(issues), quota,
        verdict, provenance, coupure,
    )
    return verdict[0], donnees, texte


def construire_parseur() -> argparse.ArgumentParser:
    """Séparé de `main()` pour être inspectable sans exécuter quoi que ce soit :
    une option citée dans la procédure de bornage et absente d'ici ferait perdre
    le seul lancement disponible avant la coupure."""
    parseur = argparse.ArgumentParser(
        description=(
            "Vérifie que les SHA cités dans les .md suivis et les corps "
            "d'issues résolvent dans Software Heritage (#568, #575)."
        )
    )
    parseur.add_argument("--racine", default=".", help="racine du dépôt git")
    parseur.add_argument(
        "--origine",
        default=None,
        help=(
            "origine à interroger. Par défaut, DÉRIVÉE de `git remote get-url "
            f"origin` et normalisée ; à défaut de remote, repli sur "
            f"{ORIGINE_PAR_DEFAUT}, annoncé dans la sortie (#575)."
        ),
    )
    parseur.add_argument(
        "--fenetre",
        type=int,
        default=None,
        metavar="N",
        help=(
            "nombre de commits de données conservés, comme "
            "`borner_historique_donnees.sh --fenetre N`. Restreint la "
            "vérification aux SHA cités ANCÊTRES du point de coupure — les "
            "seuls que la coupure perdrait. Sans cette option ni `--coupure`, "
            "le périmètre reste tout : c'est un audit d'archive, pas un feu "
            "vert de coupure."
        ),
    )
    parseur.add_argument(
        "--coupure",
        default=None,
        metavar="COMMIT",
        help=(
            "point de coupure explicite, au lieu de le dériver d'une fenêtre. "
            "S'emploie quand `--preparer` a déjà annoncé le sien."
        ),
    )
    parseur.add_argument(
        "--sans-issues",
        action="store_true",
        help="n'extraire que des .md suivis (pas d'appel à `gh`)",
    )
    parseur.add_argument(
        "--attente-max",
        type=float,
        default=3900.0,
        help=(
            "secondes d'attente cumulée tolérées pour respecter le quota "
            "anonyme (120 requêtes/heure). Au-delà, le verdict est INDÉTERMINÉ "
            "plutôt qu'une veille silencieuse."
        ),
    )
    parseur.add_argument("--json", dest="json_out", help="écrit aussi le rapport JSON")
    return parseur


def main(argv: Optional[list[str]] = None) -> int:
    args = construire_parseur().parse_args(argv)

    racine = subprocess.run(
        ["git", "-C", args.racine, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    try:
        code, donnees, texte = verifier(
            racine,
            origine=args.origine,
            avec_issues=not args.sans_issues,
            fenetre=args.fenetre,
            commit_coupure=args.coupure,
            attente_max=args.attente_max,
        )
    except ValueError as err:
        # Une coupure qui ne résout pas : refuser de conclure vaut mieux que
        # vérifier un autre périmètre que celui qu'on croit.
        print(f"[!] {err}", file=sys.stderr)
        return INDETERMINE
    print(texte)
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(
            json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"→ Rapport JSON écrit : {args.json_out}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
