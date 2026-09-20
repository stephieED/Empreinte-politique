#!/usr/bin/env python3
"""
audit_volumetrie_profils.py — Volumétrie des profils et gain de chaque levier
d'allègement (#429).

Répond à une question précise : **le passage à pleine échelle du roster (#192)
est bloqué par le volume de données versionnées, pas par le budget CI**. À 189
profils le dépôt porte 2,2 Go ; la projection à 752 dépasse les seuils GitHub
(pushs refusés au-delà de 2 Go, dépôt déconseillé au-delà de 5 Go).

Ce script mesure, sur un échantillon réel de profils, ce que rapporterait
chaque levier — afin d'arbitrer #429 sur des chiffres et non sur une
extrapolation.

**Principe : mesurer des leviers qui DÉPLACENT la donnée, pas qui la
suppriment.** L'UI actuelle n'exploite qu'une fraction des champs, mais elle
n'est pas définitive : la refonte analytics/visualisation (#324) aura besoin de
données que l'interface d'aujourd'hui ignore. Un champ « non lu » n'est pas un
champ inutile. Les leviers sont donc classés en deux familles, et le rapport
distingue explicitement celle qui ne perd rien.

Leviers mesurés :
  - `compact`      : JSON sans indentation (aucune perte, gain immédiat) ;
  - `gzip`         : fichier gzippé (aucune perte, mais blob binaire — voir la
                     réserve sur `.git` dans le rapport) ;
  - `externalise:<champ>` : poids d'un champ qu'on sortirait du profil vers un
                     index dédié, sur le modèle de l'index amendements shardé
                     par acteur (#392). La donnée reste disponible.

Fonctions pures (liste de chemins -> dict sérialisable) séparées de l'I/O,
comme `audit_pivot_dataset.py` et ses jumeaux : un fichier illisible ne doit
jamais interrompre le scan.

Aucune dépendance hors bibliothèque standard (`requirements.txt` ne porte ni
PyYAML ni pandas) : le script doit tourner sur une machine de développement
comme dans un runner.

Usage :
    python3 src/audit_volumetrie_profils.py \\
        --profils-dir pivot_data/profiles \\
        --profils-bruts-dir raw_data/profiles \\
        --cible 752 \\
        --out audit/volumetrie.md
"""

import argparse
import gzip
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from profil_brut import PartitionIllisible, charger_profil_brut
# Les deux populations de `pivot_data/profiles/` (#630). Ce script accepte
# `--profils-dir` plusieurs fois, et le brut n'a jamais porté `meta.provenance` :
# `ventiler_chemins` ne ventile donc que les `*.pivot.json` et rend les autres,
# que le rapport nomme au lieu de les fondre dans un poste.
from population_profils import Ventilation, ventiler_chemins

# Champs dont on mesure l'externalisation. `co_signataires` est imbriqué dans
# chaque amendement, d'où un chemin en deux segments.
CHAMPS_EXTERNALISABLES: tuple[tuple[str, ...], ...] = (
    ("amendements", "co_signataires"),
    ("amendements",),
    ("votes",),
    ("interventions",),
)

# Seuils GitHub (documentation GitHub, 2026-08). Ils portent sur le **dépôt** —
# ce qu'on clone, donc l'historique compressé — et non sur l'arbre de travail.
# La distinction n'est pas académique : mesuré le 19/08/2026, les profils JSON
# se déltifient d'un facteur 10 à 14 (3 017 Mo d'arbre de travail pour 670 Mo
# de `.git`). Comparer un total d'arbre de travail à ces seuils surestime donc
# le problème d'un ordre de grandeur — c'est l'erreur que faisait ce script, et
# elle a été reprise telle quelle dans le cadrage de #429.
SEUIL_PUSH_GO = 2.0
SEUIL_DEPOT_RECOMMANDE_GO = 5.0

# Fenêtre de commits de données au-delà de laquelle l'historique est borné
# (#434, option D).
#
# **La fenêtre vaut UN MOIS de données** — arbitrage du 28/08/2026 (#551). Ce
# n'est pas un objectif de taille, et ce n'est plus la latence de détection sur
# laquelle #434 l'avait dimensionnée : c'est la profondeur de retour en arrière
# qu'on veut garder sur les données publiées.
#
# 30 est la conversion, pas la décision. Mesuré le 28/08/2026 : 29 commits de
# données en 28 jours, soit 1,04/jour ; et le `schedule: cron` de
# generate-data.yml, quand il sera réactivé, vaut un run par jour. Un mois fait
# donc ~30 commits dans les deux régimes.
#
# À recalculer si la cadence change — typiquement si les runs manuels restent
# aussi fréquents qu'en août une fois le cron actif (2/jour ferait tomber la
# fenêtre à quinze jours). Le step « Fenêtre de rétention » de
# generate-data.yml affiche le compte à chaque run.
#
# Le COÛT de cette fenêtre, lui, ne se surveille pas à intervalle fixe (#551,
# question 3) : mesurer la taille du dépôt coûte 1 min 52 s de temps réel et
# 3 min 37 s de CPU, trop cher pour une alerte qui dirait « tout va bien » à
# chaque run. Il se revérifie sur ÉVÉNEMENT — une décision qui change la taille
# du corpus. Un seul est à l'horizon : la réouverture du Sénat (#528, +300
# membres). Ce jour-là, relancer ce script hors CI et vérifier qu'un mois de
# données tient toujours sous les 2 Go du critère de #429.
#
# Voir `docs/decisions/fenetre-recalibrage-551.md`.
FENETRE_COMMITS_DONNEES = 30

# Nombre de runs récents sur lesquels la distribution du coût est calculée.
# Prendre TOUS les commits de données la fausserait : les plus anciens ont été
# écrits quand le corpus faisait 14 à 30 profils, et coûtaient 0,03 à 2,8 Mo.
# Les mélanger aux runs à 209 profils ramène la médiane de 12,6 à 2,6 Mo et
# gonfle l'écart min/max à × 1 790 — un chiffre qui ne décrit aucun run réel.
RUNS_RECENTS = 8

# Motif du sujet des commits de données. Le workflow les écrit tous ainsi
# (`.github/workflows/generate-data.yml`, étape de commit).
MOTIF_COMMIT_DONNEES = "mise à jour automatique des données"

_OCTETS_PAR_GO = 1024 ** 3
_OCTETS_PAR_MO = 1024 ** 2


def _dumps(valeur: Any) -> bytes:
    """JSON compact, encodage UTF-8 réel — pas d'échappement \\uXXXX, qui
    gonflerait artificiellement le poids des accents."""
    return json.dumps(valeur, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _poids_champ(profil: dict[str, Any], chemin: tuple[str, ...]) -> int:
    """Octets occupés par un champ, éventuellement imbriqué dans une liste.

    `("amendements", "co_signataires")` additionne le champ `co_signataires` de
    chaque entrée de `amendements`.
    """
    if not chemin:
        return 0
    tete, *reste = chemin
    valeur = profil.get(tete)
    if valeur is None:
        return 0
    if not reste:
        return len(_dumps(valeur))
    if not isinstance(valeur, list):
        return 0
    return sum(
        len(_dumps(entree[reste[0]]))
        for entree in valeur
        if isinstance(entree, dict) and reste[0] in entree
    )


def fichiers_du_profil(chemin: Path) -> list[Path]:
    """Tous les fichiers d'un profil : le socle, plus ses tranches (#580).

    Un profil brut n'est plus un fichier depuis la partition par législature.
    Toute mesure de volume qui continuerait de le croire rapporterait le seul
    socle — 1,85 Mo pour un profil qui en pèse 56. Un profil monolithique, ou un
    pivot, n'a pas de répertoire frère : la liste rend alors le seul fichier.
    """
    chemins = [chemin]
    dossier = chemin.parent / chemin.name[: -len(".json")] if chemin.name.endswith(".json") else None
    if dossier is not None and dossier.is_dir():
        chemins.extend(sorted(dossier.glob("*.json")))
    return chemins


def octets_du_profil(chemin: Path) -> int:
    """Poids disque d'un profil, tranches comprises."""
    total = 0
    for f in fichiers_du_profil(chemin):
        try:
            total += f.stat().st_size
        except OSError:
            continue
    return total


def analyser_profil(chemin: Path) -> Optional[dict[str, Any]]:
    """Mesures d'un profil. `None` si le fichier est illisible — un JSON
    malformé ne doit pas interrompre le scan.

    Partition (#580) : `octets` et `octets_gzip` portent sur le socle **et** ses
    tranches, et le poids des champs est mesuré sur le profil RECOMPOSÉ. Sans
    cela, `externalise:amendements` rendrait 0 sur un profil partitionné — soit
    exactement la conclusion inverse de la mesure qui a motivé la découpe.
    """
    try:
        fichiers = fichiers_du_profil(chemin)
        brut = b"".join(f.read_bytes() for f in fichiers)
        profil = charger_profil_brut(chemin)
    except (OSError, ValueError, PartitionIllisible):
        return None
    if not isinstance(profil, dict):
        return None

    compact = _dumps(profil)
    return {
        "fichier": chemin.name,
        "octets": len(brut),
        "octets_compact": len(compact),
        "octets_gzip": len(gzip.compress(brut, 6)),
        "champs": {
            ":".join(c): _poids_champ(profil, c) for c in CHAMPS_EXTERNALISABLES
        },
    }


def compute_volumetrie(
    mesures: list[dict[str, Any]], exact: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Agrège les mesures. Fonction pure.

    `exact` porte les chiffres relevés sur TOUS les fichiers (passe 1). Les
    ratios de l'échantillon y sont appliqués pour extrapoler compact/gzip/champs
    au total réel — plutôt que de rapporter le poids de l'échantillon, qui ne
    représenterait rien.
    """
    if not mesures:
        return {"nb_profils": (exact or {}).get("nb_profils", 0)}

    octets_ech = sum(m["octets"] for m in mesures)
    champs: dict[str, int] = {}
    for mesure in mesures:
        for nom, poids in mesure["champs"].items():
            champs[nom] = champs.get(nom, 0) + poids

    if exact and exact.get("octets_total"):
        total = exact["octets_total"]
        facteur = total / octets_ech if octets_ech else 0
        nb = exact["nb_profils"]
        median, maximum, f_max = exact["octets_median"], exact["octets_max"], exact["fichier_max"]
    else:
        total = octets_ech
        facteur = 1.0
        nb = len(mesures)
        tries = sorted(m["octets"] for m in mesures)
        median, maximum = tries[len(tries) // 2], tries[-1]
        f_max = max(mesures, key=lambda m: m["octets"])["fichier"]

    return {
        "nb_profils": nb,
        # #630 — la ventilation vient de la passe 1 (tous les fichiers), donc du
        # même comptage que `nb_profils` ; elle est absente si `exact` l'est.
        "ventilation_provenance": (exact or {}).get("ventilation_provenance"),
        "nb_profils_sans_provenance": (exact or {}).get("nb_profils_sans_provenance", 0),
        "nb_echantillon": len(mesures),
        "extrapole": facteur != 1.0,
        "octets_total": total,
        "octets_median": median,
        "octets_moyen": total // nb if nb else 0,
        "octets_max": maximum,
        "fichier_max": f_max,
        "octets_compact_total": int(sum(m["octets_compact"] for m in mesures) * facteur),
        "octets_gzip_total": int(sum(m["octets_gzip"] for m in mesures) * facteur),
        "poids_par_champ": {k: int(v * facteur) for k, v in champs.items()},
    }


def compute_leviers(volumetrie: dict[str, Any]) -> list[dict[str, Any]]:
    """Gain de chaque levier, en octets et en pourcentage. Fonction pure.

    `perte` distingue ce qui déplace la donnée de ce qui la supprimerait — la
    distinction qui structure l'arbitrage de #429.
    """
    total = volumetrie.get("octets_total") or 0
    if not total:
        return []

    leviers = [
        {
            "nom": "JSON compact (sans indentation)",
            "gain_octets": total - volumetrie["octets_compact_total"],
            "perte": False,
            "note": "aucune décision éditoriale, aucun champ touché",
        },
        {
            "nom": "Fichiers gzippés (.json.gz)",
            "gain_octets": total - volumetrie["octets_gzip_total"],
            "perte": False,
            "note": "blob binaire : git ne peut plus déltifier, mesurer l'effet sur .git",
        },
    ]
    for nom, poids in sorted(
        volumetrie["poids_par_champ"].items(), key=lambda kv: -kv[1]
    ):
        leviers.append({
            "nom": f"Externaliser `{nom}` hors du profil",
            "gain_octets": poids,
            "perte": False,
            "note": "la donnée reste disponible dans un index dédié (modèle #392)",
        })
    return sorted(leviers, key=lambda l: -l["gain_octets"])


def compute_historique_git(repertoires: list[Path]) -> dict[str, Any]:
    """Coût de chaque répertoire dans l'historique git, et coût du dernier
    commit de données.

    C'est **cette** mesure qu'il faut comparer aux seuils GitHub, pas celle de
    l'arbre de travail : les seuils portent sur le dépôt. Et c'est surtout le
    coût **par run** qui décide, parce qu'un commit de données ajoute de
    l'historique définitivement — la photo, elle, ne grandit qu'avec le nombre
    de profils.

    MAIS `octets_total` est un **majorant**, jamais la taille du dépôt.
    `rev-list --disk-usage` additionne la représentation *actuelle* de chaque
    objet, donc sur des packs mal compactés il compte des deltas que le repack
    fera disparaître. Mesuré le 20/08/2026 sur `3a8455a` : 409 Mo ici, **295 Mo**
    sur un `git clone --mirror --no-hardlinks` après `gc --prune=now`, soit
    39 % d'écart — l'API GitHub en annonçait 397 le même jour, et ce troisième
    chiffre porte en plus le coût des push forcés non ramassés. Le rapport le
    dit à l'endroit où le chiffre se lit : c'est la même confusion arbre de
    travail / dépôt qui a fait recadrer #429 quatre fois. Pour obtenir la
    mesure d'après repack sans toucher au dépôt de travail :
    `scripts/borner_historique_donnees.sh --mesurer` (#434).

    Renvoie un dict vide hors dépôt git ou si `git` est indisponible : la
    volumétrie de l'arbre de travail reste utile seule, elle ne doit pas
    dépendre de ça.
    """
    def _disk_usage(*args: str) -> Optional[int]:
        try:
            sortie = subprocess.run(
                ["git", "rev-list", "--disk-usage", "--objects", *args],
                capture_output=True, text=True, check=True, timeout=120,
            ).stdout.strip()
            return int(sortie) if sortie else None
        except (subprocess.SubprocessError, OSError, ValueError):
            return None

    total = _disk_usage("--all")
    if total is None:
        return {}

    par_repertoire = {}
    for repertoire in repertoires:
        octets = _disk_usage("--all", "--", str(repertoire))
        if octets is not None:
            par_repertoire[str(repertoire)] = octets

    # Coût du dernier commit de données : le meilleur estimateur du coût par
    # run, seul chiffre qui dise à quelle vitesse le dépôt grossit.
    dernier_run = None
    try:
        sha = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--grep=mise à jour automatique des données"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()
        if sha:
            dernier_run = {
                "sha": sha[:7],
                "octets": _disk_usage(sha, "--not", f"{sha}^"),
                "par_repertoire": {
                    str(r): _disk_usage(sha, "--not", f"{sha}^", "--", str(r))
                    for r in repertoires
                },
            }
    except (subprocess.SubprocessError, OSError):
        pass

    return {
        "octets_total": total,
        "par_repertoire": par_repertoire,
        "dernier_run": dernier_run,
    }


def collecte_commits_donnees(limite: int = 200) -> list[dict[str, Any]]:
    """Relève les commits de données et ce que chacun a coûté en historique.

    I/O pure git, du plus récent au plus ancien. Renvoie une liste vide hors
    dépôt git ou si `git` est indisponible : la mesure de fenêtre est un
    complément, elle ne doit jamais faire échouer le reste du rapport.

    Le coût d'un commit est celui des objets qu'il **introduit** — donc
    `--not` chacun de ses parents, et non le seul premier : sur un merge, ne
    retrancher que le premier parent recompterait toute la branche fusionnée.
    """
    def _git(*args: str) -> Optional[str]:
        try:
            return subprocess.run(
                ["git", *args], capture_output=True, text=True, check=True, timeout=120,
            ).stdout.strip()
        except (subprocess.SubprocessError, OSError):
            return None

    listing = _git(
        "log", f"--max-count={limite}", "--format=%H %aI",
        f"--grep={MOTIF_COMMIT_DONNEES}",
    )
    if not listing:
        return []

    commits: list[dict[str, Any]] = []
    for ligne in listing.splitlines():
        sha, _, date = ligne.partition(" ")
        if not sha:
            continue
        parents = (_git("rev-list", "--parents", "-n1", sha) or "").split()[1:]
        exclusions: list[str] = []
        for parent in parents:
            exclusions += ["--not", parent]
        brut = _git("rev-list", "--disk-usage", "--objects", sha, *exclusions)
        try:
            octets = int(brut) if brut else 0
        except ValueError:
            octets = 0
        commits.append({"sha": sha[:7], "date": date, "octets": octets})
    return commits


def compute_fenetre_donnees(
    commits: list[dict[str, Any]],
    fenetre: int = FENETRE_COMMITS_DONNEES,
    socle_octets: Optional[int] = None,
    recents: int = RUNS_RECENTS,
) -> dict[str, Any]:
    """État de la fenêtre glissante de #434. Fonction pure.

    Dit trois choses, et une seule décide :

    1. **La fenêtre est-elle contraignante ?** Tant que le dépôt porte moins de
       `fenetre` commits de données, borner l'historique ne retirerait rien —
       il n'y a pas d'opération à mener, seulement à mesurer.
    2. **La distribution du coût par run**, jamais la moyenne seule : mesuré le
       20/08/2026, les huit derniers runs vont de 0,2 à 53,5 Mo pour une
       médiane de 12,6 — un facteur 4 entre médiane et maximum. Une moyenne
       dimensionnerait la fenêtre sur un run qui n'existe pas.

       Elle porte sur les `recents` derniers runs, pas sur tous : le coût d'un
       run suit la taille du corpus, et y mêler les runs à 14 profils
       décrirait un dépôt qui n'existe plus.
    3. **Le majorant du gain** — et c'est le chiffre à ne PAS lire comme un
       gain.

    ⚠️ `majorant_gain_octets` est la somme de ce qu'ont coûté les commits hors
    fenêtre. Ce **n'est pas** ce qu'un squash libérerait, et l'écart est
    énorme : mesuré sur un clone au 20/08/2026, à `fenetre=10` la somme vaut
    93 Mo pour un gain réel de **6 Mo** (× 15), et à `fenetre=3` elle vaut
    254 Mo pour **115 Mo** (× 2,2). La raison est structurelle : le squash
    conserve l'arbre complet à la coupure, et les objets des commits retirés
    sont majoritairement des deltas dont la base doit de toute façon être
    gardée. Le seul gain fiable se mesure en repackant un clone, jamais en
    additionnant des coûts par run.
    """
    nb = len(commits)
    resultat: dict[str, Any] = {
        "fenetre": fenetre,
        "nb_commits_donnees": nb,
        "contraignante": nb > fenetre,
        "sha_coupure": None,
        "majorant_gain_octets": 0,
        "couts": {},
    }
    if not nb:
        return resultat

    echantillon = commits[:recents] if recents > 0 else commits
    couts = sorted(c.get("octets") or 0 for c in echantillon)
    milieu = len(couts) // 2
    resultat["nb_runs_mesures"] = len(couts)
    resultat["couts"] = {
        "median": couts[milieu] if len(couts) % 2 else (couts[milieu - 1] + couts[milieu]) // 2,
        "moyen": sum(couts) // len(couts),
        "max": couts[-1],
        "min": couts[0],
    }

    if nb > fenetre:
        resultat["sha_coupure"] = commits[fenetre]["sha"]
        resultat["majorant_gain_octets"] = sum(
            c.get("octets") or 0 for c in commits[fenetre:]
        )

    if socle_octets:
        resultat["plafond_octets"] = socle_octets + fenetre * resultat["couts"]["moyen"]
    return resultat


def compute_projection(
    volumetrie: dict[str, Any], cible: int, facteur_duplication: float
) -> dict[str, Any]:
    """Projection à `cible` profils. Fonction pure.

    ⚠️ Elle projette la taille de l'**arbre de travail**, c'est-à-dire le coût
    d'un checkout — pas la taille du dépôt. Les seuils GitHub, eux, portent sur
    le dépôt : voir `compute_historique_git`.

    `cible` est un nombre de **fichiers**, pas de profils : `octets_total` est
    divisé par `nb_profils`, qui compte les fichiers scannés. Passer deux
    répertoires avec `facteur_duplication=1.0` projette donc 752 *fichiers*,
    soit ~376 profils — ni l'état actuel, ni le scénario d'un seul répertoire.
    Le bon usage est **un seul répertoire**, avec le facteur en paramètre.

    `facteur_duplication` vaut 2,0 quand `raw_data/profiles` et
    `pivot_data/profiles` sont tous deux versionnés — ils portent des volumes
    comparables, et c'est un levier à part entière.
    """
    nb = volumetrie.get("nb_profils") or 0
    if not nb:
        return {}
    par_profil = volumetrie["octets_total"] / nb
    projete = par_profil * cible * facteur_duplication
    return {
        "cible": cible,
        "facteur_duplication": facteur_duplication,
        "octets_projetes": int(projete),
        "go_projetes": round(projete / _OCTETS_PAR_GO, 2),
        "depasse_seuil_push": projete / _OCTETS_PAR_GO > SEUIL_PUSH_GO,
        "depasse_seuil_depot": projete / _OCTETS_PAR_GO > SEUIL_DEPOT_RECOMMANDE_GO,
        "profils_avant_seuil_depot": (
            int(SEUIL_DEPOT_RECOMMANDE_GO * _OCTETS_PAR_GO / (par_profil * facteur_duplication))
            if par_profil else None
        ),
    }


def _mo(octets: int) -> str:
    return f"{octets / _OCTETS_PAR_MO:,.1f} Mo".replace(",", " ")


def _avertissement_representativite(vol: dict[str, Any], proj: dict[str, Any]) -> str:
    """Mise en garde sur la représentativité — mais **seulement quand elle
    s'applique**.

    Quand la population mesurée atteint déjà la cible, il n'y a plus de
    projection : le total est un fait. Laisser l'avertissement dans ce cas
    inviterait à douter d'un chiffre certain, ce qui est aussi trompeur que
    d'omettre la réserve dans le cas inverse.
    """
    if vol["nb_profils"] >= proj["cible"]:
        return (
            f"> Population **complète** ({vol['nb_profils']} profils "
            f"{_libelle_ventilation(vol)} pour une "
            f"cible de {proj['cible']}) : le total est mesuré, pas extrapolé."
        )
    return (
        "> La projection suppose la population représentative. Si elle ne porte "
        "que des profils déjà générés, elle peut être biaisée — les profils "
        "générés en premier ne sont pas forcément de poids médian."
    )


def _libelle_ventilation(vol: dict[str, Any]) -> str:
    """Ventilation par provenance d'une volumétrie, brut compris (#630).

    Les profils bruts n'ont pas de `meta.provenance` : ils sont comptés à part
    et **nommés**, jamais rangés d'office parmi les candidats déclarés. Sans
    cette distinction, `--profils-dir raw_data/profiles` afficherait « 476
    candidats déclarés » — un chiffre juste sur la mauvaise population.
    """
    ventilation = Ventilation.depuis_dict(vol.get("ventilation_provenance"))
    sans_provenance = vol.get("nb_profils_sans_provenance") or 0
    if not ventilation.total and not sans_provenance:
        return ""
    postes = [f"{effectif} {libelle}" for effectif, libelle in ventilation.postes()
              ] if ventilation.total else []
    if sans_provenance:
        postes.append(f"{sans_provenance} profils bruts, sans meta.provenance")
    return "(" + " · ".join(postes) + ")"


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    """Rapport prêt à coller dans #429."""
    vol = rapport["volumetrie"]
    if not vol.get("nb_profils"):
        return "# Volumétrie des profils\n\nAucun profil analysé.\n"

    total = vol["octets_total"]
    lignes = [
        "# Volumétrie des profils et leviers d'allègement",
        "",
        f"Population : **{vol['nb_profils']} profils** "
        f"{_libelle_ventilation(vol)}, **{_mo(total)}** au "
        f"total — mesuré sur tous les fichiers.",
        "",
        f"Ratios (compact, gzip, poids par champ) calculés sur "
        f"**{vol.get('nb_echantillon', vol['nb_profils'])} profils** "
        f"échantillonnés à intervalle régulier sur la distribution des tailles.",
        "",
        "| Indicateur | Valeur |",
        "| --- | --- |",
        f"| Profil médian | {_mo(vol['octets_median'])} |",
        f"| Profil moyen | {_mo(vol['octets_moyen'])} |",
        f"| Profil le plus lourd | {_mo(vol['octets_max'])} (`{vol['fichier_max']}`) |",
        "",
    ]

    proj = rapport.get("projection") or {}
    if proj:
        lignes += [
            "## Projection",
            "",
            f"À **{proj['cible']} profils**, facteur de duplication "
            f"`raw`/`pivot` = {proj['facteur_duplication']} :",
            "",
            f"- **{proj['go_projetes']} Go** dans l'arbre de travail — c'est le coût "
            "d'un *checkout*, pas la taille du dépôt ;",
            f"- à titre indicatif, les seuils GitHub ({SEUIL_PUSH_GO} Go par push, "
            f"{SEUIL_DEPOT_RECOMMANDE_GO} Go recommandés) portent sur le **dépôt** : "
            "voir la section « Historique git » ci-dessous, qui est la mesure à leur "
            "comparer.",
            "",
            "> ⚠️ `cible` compte des **fichiers**, pas des profils. Deux répertoires "
            "passés avec `--facteur-duplication 1.0` projettent 752 *fichiers*, soit "
            "~376 profils. Le bon usage est un seul répertoire, avec le facteur en "
            "paramètre.",
            "",
            _avertissement_representativite(vol, proj),
            "",
        ]

    hist = rapport.get("historique_git") or {}
    if hist:
        lignes += [
            "## Historique git — la mesure à comparer aux seuils GitHub",
            "",
            f"Dépôt entier (objets atteignables) : **{_mo(hist['octets_total'])}**.",
            "",
            "> ⚠️ Ce total est un **majorant**, pas la taille du dépôt. "
            "`rev-list --disk-usage` additionne la représentation *actuelle* de "
            "chaque objet sur des packs mal compactés ; le seul chiffre "
            "comparable aux seuils GitHub est celui d'après `gc --prune=now`, "
            "mesuré 39 % plus bas le 20/08/2026 (409 Mo annoncés ici, 295 Mo "
            "après repack). Le mesurer sans toucher au dépôt de travail : "
            "`scripts/borner_historique_donnees.sh --mesurer` "
            "(#434, `docs/decisions/fenetre-historique-donnees.md`).",
            "",
        ]
        if hist.get("par_repertoire"):
            lignes += [
                "| Répertoire | Arbre de travail | Historique | Facteur |",
                "| --- | --- | --- | --- |",
            ]
            for rep, octets in hist["par_repertoire"].items():
                # `rglob` : les tranches de #580 sont un niveau plus bas.
                arbre = sum(
                    f.stat().st_size for f in Path(rep).rglob("*.json")
                    if not f.name.startswith(".")
                ) if Path(rep).is_dir() else 0
                facteur = f"× {arbre / octets:.1f}" if octets else "—"
                lignes.append(f"| `{rep}` | {_mo(arbre)} | {_mo(octets)} | {facteur} |")
            lignes.append("")
        run = hist.get("dernier_run") or {}
        if run.get("octets"):
            lignes += [
                f"**Coût du dernier commit de données** (`{run['sha']}`) : "
                f"**{_mo(run['octets'])}** ajoutés à l'historique, définitivement.",
                "",
                "C'est le chiffre qui décide : la photo ne grandit qu'avec le nombre de "
                "profils, l'historique grandit à **chaque run**. Un dépôt qui reste sous "
                "les seuils aujourd'hui peut les franchir en quelques semaines de runs "
                "quotidiens, sans qu'un seul profil ne s'alourdisse.",
                "",
            ]
            details = {k: v for k, v in (run.get("par_repertoire") or {}).items() if v}
            if details:
                lignes += ["| Répertoire | Coût du dernier run |", "| --- | --- |"]
                lignes += [f"| `{k}` | {_mo(v)} |" for k, v in details.items()]
                lignes.append("")

    fen = rapport.get("fenetre_donnees") or {}
    if fen.get("nb_commits_donnees"):
        couts = fen["couts"]
        lignes += [
            "## Fenêtre d'historique de données (#434)",
            "",
            f"**{fen['nb_commits_donnees']} commits de données** dans l'historique, "
            f"pour une fenêtre retenue de **{fen['fenetre']}**.",
            "",
            f"Distribution mesurée sur les **{fen.get('nb_runs_mesures', 0)} runs les "
            "plus récents** : le coût d'un run suit la taille du corpus, et y mêler "
            "les runs à 14 profils décrirait un dépôt qui n'existe plus.",
            "",
            "| Coût par run | Valeur |",
            "| --- | --- |",
            f"| Médian | {_mo(couts['median'])} |",
            f"| Moyen | {_mo(couts['moyen'])} |",
            f"| Minimum | {_mo(couts['min'])} |",
            f"| Maximum | {_mo(couts['max'])} |",
            "",
            "> C'est la **distribution** qui dimensionne, pas la moyenne : "
            "l'écart entre le run le moins cher et le plus cher est d'un facteur "
            f"{(couts['max'] / couts['min']) if couts['min'] else 0:.1f}.",
            "",
        ]
        if fen.get("plafond_octets"):
            lignes += [
                f"Plafond impliqué par la fenêtre : **{_mo(fen['plafond_octets'])}** "
                "(socle + fenêtre × coût moyen).",
                "",
            ]
        if fen["contraignante"]:
            lignes += [
                f"⚠️ **La fenêtre est contraignante** : la coupure serait "
                f"`{fen['sha_coupure']}`. Majorant du gain : "
                f"{_mo(fen['majorant_gain_octets'])}.",
                "",
                "> Ce majorant n'est **pas** le gain. Il additionne des coûts par "
                "run, alors qu'un squash conserve l'arbre complet à la coupure et "
                "que les objets retirés sont surtout des deltas dont la base est "
                "gardée. Mesuré sur un clone le 20/08/2026 : × 15 d'écart à une "
                "fenêtre de 10, × 2,2 à une fenêtre de 3. **Le gain réel se mesure "
                "en repackant un clone**, jamais en additionnant cette colonne — "
                "`scripts/borner_historique_donnees.sh --mesurer`.",
                "",
            ]
        else:
            lignes += [
                "✓ **La fenêtre n'est pas contraignante** : moins de commits de "
                "données que la fenêtre ne l'autorise. Il n'y a rien à borner, et "
                "donc aucune réécriture d'historique à mener.",
                "",
            ]

    lignes += [
        "## Leviers, tous sans perte d'information",
        "",
        "| Levier | Gain | Part | Remarque |",
        "| --- | --- | --- | --- |",
    ]
    for levier in rapport["leviers"]:
        part = 100 * levier["gain_octets"] / total if total else 0
        lignes.append(
            f"| {levier['nom']} | {_mo(levier['gain_octets'])} | "
            f"**{part:.1f} %** | {levier['note']} |"
        )

    lignes += [
        "",
        "> Aucun levier listé ici ne supprime de donnée : ils la compressent ou "
        "la déplacent hors du fichier de profil. C'est délibéré — l'UI n'est pas "
        "définitive, et la refonte analytics (#324) aura besoin de champs que "
        "l'interface actuelle n'exploite pas encore (#429).",
        "",
    ]
    if rapport.get("erreurs_lecture"):
        lignes += [
            "## Fichiers illisibles",
            "",
            *(f"- `{f}`" for f in rapport["erreurs_lecture"]),
            "",
        ]
    return "\n".join(lignes)


def analyser_repertoires(
    repertoires: list[Path], echantillon: int
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    """I/O en deux passes, pour rester utilisable à pleine échelle.

    Passe 1 — `stat` sur TOUS les fichiers : total, médiane et maximum sont donc
    exacts, jamais extrapolés.

    Passe 2 — analyse profonde (parsing, ré-encodage compact, gzip, poids par
    champ) sur un échantillon seulement. Gzipper 1,1 Go prend plusieurs minutes,
    et ce serait quatre fois pire sur le roster complet : un script de mesure
    qui ne finit pas ne sert à rien.

    L'échantillon est pris à intervalle régulier sur les fichiers **triés par
    taille**, et non au hasard : il couvre ainsi toute la distribution, des
    profils légers aux gros déposants d'amendements. Un tirage aléatoire
    donnerait des ratios instables d'une exécution à l'autre.
    """
    tous: list[Path] = []
    for repertoire in repertoires:
        if not repertoire.is_dir():
            print(f"  [!] Répertoire absent, ignoré : {repertoire}", file=sys.stderr)
            continue
        # Un fichier de service n'est pas un profil, et le compter fausserait la
        # volumétrie : `raw_data/profiles/.generation_checkpoint.json` est un
        # point de progression, pas une donnée collectée (#518). `Path.glob`
        # remonte les fichiers cachés, contrairement au module `glob` — même
        # filtre que `merge_profile`, `scrutins_index`, `amendements_index`.
        tous.extend(sorted(
            c for c in repertoire.glob("*.json") if not c.name.startswith(".")))

    # `octets_du_profil` et non `stat()` : depuis #580 un profil brut est un
    # socle plus ses tranches. Le `glob` reste non récursif — il énumère les
    # slugs, comme avant — et c'est la mesure qui descend dans le répertoire.
    ventilation, hors_pivot = ventiler_chemins(tous)

    tailles = [(c, octets_du_profil(c)) for c in tous]
    tailles.sort(key=lambda ct: ct[1])
    exact = {
        "nb_profils": len(tailles),
        "ventilation_provenance": ventilation.as_dict(),
        "nb_profils_sans_provenance": len(hors_pivot),
        "octets_total": sum(t for _c, t in tailles),
        "octets_median": tailles[len(tailles) // 2][1] if tailles else 0,
        "octets_max": tailles[-1][1] if tailles else 0,
        "fichier_max": tailles[-1][0].name if tailles else None,
    }

    if echantillon > 1 and len(tailles) > echantillon:
        # Indices répartis de 0 à len-1 INCLUS. Un simple `int(i * len/n)`
        # s'arrête avant le dernier élément et manque donc systématiquement le
        # profil le plus lourd — précisément celui où les amendements pèsent le
        # plus. Les ratios en sortaient sous-estimés.
        dernier = len(tailles) - 1
        choisis = [
            tailles[round(i * dernier / (echantillon - 1))][0]
            for i in range(echantillon)
        ]
    elif echantillon == 1 and tailles:
        choisis = [tailles[-1][0]]
    else:
        choisis = [c for c, _t in tailles]

    mesures: list[dict[str, Any]] = []
    erreurs: list[str] = []
    for chemin in choisis:
        mesure = analyser_profil(chemin)
        if mesure is None:
            erreurs.append(str(chemin))
        else:
            mesures.append(mesure)
    exact["nb_echantillon"] = len(mesures)
    return mesures, erreurs, exact


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--profils-dir", action="append", default=None, metavar="REP",
        help="Répertoire de profils à analyser (répétable). "
             "Défaut : pivot_data/profiles.",
    )
    parser.add_argument(
        "--cible", type=int, default=752, metavar="N",
        help="Effectif projeté (défaut : 752, le roster complet).",
    )
    parser.add_argument(
        "--facteur-duplication", type=float, default=2.0, metavar="F",
        help="2.0 si raw_data ET pivot_data sont versionnés (défaut), "
             "1.0 si un seul l'est.",
    )
    parser.add_argument(
        "--echantillon", type=int, default=40, metavar="N",
        help="Nombre de profils analysés en profondeur (défaut : 40, 0 = tous). "
             "Le total, la médiane et le maximum restent mesurés sur TOUS les "
             "fichiers ; seuls les ratios compact/gzip/champs sont échantillonnés.",
    )
    parser.add_argument(
        "--sans-historique-git", action="store_true",
        help="Ne pas mesurer l'historique git (`git rev-list --disk-usage`). Utile hors "
             "dépôt, ou sur un très gros dépôt où la mesure traîne ; le rapport perd "
             "alors la seule mesure comparable aux seuils GitHub.",
    )
    parser.add_argument(
        "--fenetre", type=int, default=FENETRE_COMMITS_DONNEES, metavar="N",
        help=f"Nombre de commits de données conservés par la fenêtre glissante de "
             f"#434 (défaut : {FENETRE_COMMITS_DONNEES}). Sert à dire si la fenêtre "
             "est contraignante, jamais à réécrire quoi que ce soit.",
    )
    parser.add_argument("--out", metavar="FICHIER", help="Rapport Markdown.")
    parser.add_argument("--out-json", metavar="FICHIER", help="Rapport JSON.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    repertoires = [Path(d) for d in (args.profils_dir or ["pivot_data/profiles"])]

    mesures, erreurs, exact = analyser_repertoires(repertoires, args.echantillon)
    if not mesures:
        print("[!] Aucun profil analysable.", file=sys.stderr)
        return 1

    volumetrie = compute_volumetrie(mesures, exact)
    rapport = {
        "volumetrie": volumetrie,
        "leviers": compute_leviers(volumetrie),
        "projection": compute_projection(volumetrie, args.cible, args.facteur_duplication),
        "historique_git": (
            {} if args.sans_historique_git else compute_historique_git(repertoires)
        ),
        "fenetre_donnees": (
            {} if args.sans_historique_git
            else compute_fenetre_donnees(collecte_commits_donnees(), args.fenetre)
        ),
        "erreurs_lecture": erreurs,
    }

    markdown = generate_markdown_report(rapport)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"→ Rapport écrit : {args.out}", file=sys.stderr)
    else:
        print(markdown)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"→ Rapport JSON écrit : {args.out_json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
