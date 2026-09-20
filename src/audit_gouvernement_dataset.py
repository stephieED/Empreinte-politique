#!/usr/bin/env python3
"""
audit_gouvernement_dataset.py — Audit du jeu de données gouvernements
(pivot_data/gouvernements).

Structure jumelle de `audit_groupe_dataset.py` (lui-même jumeau de
`audit_pivot_dataset.py`), pour les profils de gouvernement agrégés
(`schema_gouvernement.py`), voir issue #319 (sous-issue 3/6 de #316). Couche
de chargement (`load_gouvernement_directory`) volontairement séparée de la
logique de calcul des indicateurs, pour rester testable indépendamment : un
fichier JSON malformé ne doit jamais interrompre le scan du répertoire.

Indicateurs sous forme de fonctions pures (liste de profils de gouvernement
-> dict sérialisable JSON), sans aucune I/O :
  - volumétrie : nombre de gouvernements, répartition par `periode.actif`,
    distribution de `len(membres)` / `len(textes)`, `comptages.par_statut`
    agrégé tous gouvernements confondus ;
  - complétude : présence de `premier_ministre`, taux de
    `membres[].portefeuille` renseigné, présence des métadonnées `meta` ;
  - cohérence : validation `schema_gouvernement.validate_profil_gouvernement`
    (couvre déjà l'invariant du 49.3, non redupliqué ici), divergence
    `schema_version`/`meta.schema_version`, doublons de `gouvernement_id` ;
  - fraîcheur : ancienneté de `sources[].synchro_le`, gouvernements périmés
    (`compute_gouvernements_perimes`, seuil `staleness_days` injectable), même
    logique que les deux scripts existants.
  - warnings : agrégation de `meta.warnings[]` par type
    (`compute_agregation_warnings`), même contrat que
    `audit_groupe_dataset.compute_agregation_warnings` (issue #321, nécessaire
    à `audit_pipeline.py::compute_vue_ensemble` pour agréger les warnings des
    trois types de profil).

  - couverture des textes portés (`compute_couverture_textes`, issue #399) :
    classe chaque gouvernement selon que sa période tombe ou non dans le
    périmètre des archives de dossiers réellement ingérées
    (`couverture_dossiers.py`). Sépare « hors couverture de la source » de
    « réellement à zéro » : un `textes[]` vide hors couverture est une
    absence de source, jamais un fait mesuré (AGENTS.md §2.5) ; `nb_textes`
    reste `null` quand le champ `textes` est absent, jamais rendu par `0`.

  - tableau croisé des plages temporelles par gouvernement
    (`compute_plage_dates_gouvernements`, issue #320, sous-issue 4/6 de
    #316) : une ligne par gouvernement, min/max de `membres[].debut`/`.fin`
    (`mandats_membres`) et de `textes[].date_depot`/`.date_dernier_evenement`
    (`textes`). `membres[].fin` peut être `null` (mandat en cours) : exclu
    du calcul sans jamais être remplacé par la date du jour (AGENTS.md
    §2.5), et sans être compté comme une date invalide (c'est une absence
    légitime, pas une erreur de donnée).

`build_report()` assemble tous ces indicateurs en un rapport structuré
unique, et `generate_markdown_report()` en dérive un rendu Markdown lisible
par un humain, sur le même modèle que `audit_groupe_dataset.py`. La CLI
(`main()` / `_build_arg_parser()`) partage le même contrat d'options que
`audit_groupe_dataset.py`.

Aucune dépendance lourde : stdlib uniquement.
"""

import argparse
import json
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from couverture_dossiers import (
    COUVERTURE_COUVERTE,
    COUVERTURE_HORS,
    COUVERTURE_INDETERMINEE,
    COUVERTURE_PARTIELLE,
    LIBELLES_COUVERTURE,
    borne_couverture_textes,
    legislatures_ingerees,
    libelle_couverture_textes,
    statut_couverture_textes,
)
from schema_gouvernement import make_empty_comptages_statuts, validate_profil_gouvernement


def load_gouvernement_directory(input_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scanne récursivement `input_dir` à la recherche de fichiers `gouvernement-*.json`.

    Args:
        input_dir: répertoire racine à scanner (récursif), convention de
            nommage `gouvernement-<LIBELLE>.json` déjà en place (voir
            `pivot_data/gouvernements/`).

    Returns:
        Tuple (gouvernements_valides, erreurs_lecture) :
          - gouvernements_valides : liste des profils de gouvernement chargés
            avec succès, triés par chemin de fichier pour un résultat
            déterministe.
          - erreurs_lecture : liste de {"fichier": str, "erreur": str} pour
            chaque fichier n'ayant pas pu être chargé (JSON invalide, objet
            racine non-dict, erreur de lecture...). Un fichier problématique
            n'interrompt jamais le scan des suivants.
    """
    gouvernements_valides: list[dict[str, Any]] = []
    erreurs_lecture: list[dict[str, Any]] = []

    for path in sorted(input_dir.rglob("gouvernement-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            erreurs_lecture.append({"fichier": str(path), "erreur": str(exc)})
            continue

        if not isinstance(data, dict):
            erreurs_lecture.append({
                "fichier": str(path),
                "erreur": f"Attendu un objet JSON, reçu {type(data).__name__}.",
            })
            continue

        gouvernements_valides.append(data)

    return gouvernements_valides, erreurs_lecture


def _taille_liste(gouvernement: dict[str, Any], champ: str) -> int:
    """Longueur de `gouvernement[champ]`, `0` si absent ou `null` (donnée manquante)."""
    valeur = gouvernement.get(champ)
    return len(valeur) if valeur else 0


def _est_renseigne(valeur: Any) -> bool:
    """True si `valeur` est une donnée renseignée.

    `None`, chaîne vide et liste vide comptent comme non renseignés — une
    chaîne/liste vide est une absence de donnée déguisée, jamais un
    remplissage valide (AGENTS.md §2.5).
    """
    if valeur is None:
        return False
    if isinstance(valeur, (str, list)):
        return len(valeur) > 0
    return True


def _stats_entiers(valeurs: list[int]) -> dict[str, Any]:
    """Min/max/médiane/moyenne d'une liste d'entiers, `None` partout si vide."""
    if not valeurs:
        return {"min": None, "max": None, "mediane": None, "moyenne": None}

    return {
        "min": min(valeurs),
        "max": max(valeurs),
        "mediane": statistics.median(valeurs),
        "moyenne": round(statistics.mean(valeurs), 2),
    }


# ---------------------------------------------------------------------------
# Volumétrie
# ---------------------------------------------------------------------------

def compute_repartition_periode_actif(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Répartition des gouvernements par `periode.actif`.

    Un `periode` absent, non-dict, ou `actif` non booléen compte comme
    "indetermine" — jamais assimilé à `False` (AGENTS.md §2.5 : donnée
    manquante n'est jamais un défaut à 0/faux).
    """
    actifs = 0
    inactifs = 0
    indetermines = 0

    for gouvernement in gouvernements:
        periode = gouvernement.get("periode")
        actif = periode.get("actif") if isinstance(periode, dict) else None
        if actif is True:
            actifs += 1
        elif actif is False:
            inactifs += 1
        else:
            indetermines += 1

    return {
        "total_gouvernements": len(gouvernements),
        "actifs": actifs,
        "inactifs": inactifs,
        "indetermines": indetermines,
    }


def compute_distribution_membres_textes(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribution du nombre de `membres` et de `textes` par gouvernement.

    Min/max/médiane/moyenne sur `len(membres)` et `len(textes)` — un champ
    absent ou `null` compte pour 0 (ces listes sont toujours calculables,
    jamais "non calculées" comme `effectif.min_historique` côté groupe).
    """
    tailles_membres = [_taille_liste(gouvernement, "membres") for gouvernement in gouvernements]
    tailles_textes = [_taille_liste(gouvernement, "textes") for gouvernement in gouvernements]

    return {
        "membres": _stats_entiers(tailles_membres),
        "textes": _stats_entiers(tailles_textes),
    }


def compute_comptages_agreges(gouvernements: list[dict[str, Any]]) -> dict[str, int]:
    """Agrège `comptages.par_statut` de tous les gouvernements.

    Un bloc `comptages`/`par_statut` absent ou invalide est simplement
    ignoré (jamais compté comme une répartition à 0). Résultat : entiers
    bruts uniquement (AGENTS.md §2.1) — aucun taux, pourcentage ou
    classement.
    """
    agregats = make_empty_comptages_statuts()

    for gouvernement in gouvernements:
        comptages = gouvernement.get("comptages")
        par_statut = comptages.get("par_statut") if isinstance(comptages, dict) else None
        if not isinstance(par_statut, dict):
            continue
        for statut, valeur in par_statut.items():
            if statut in agregats and isinstance(valeur, int) and not isinstance(valeur, bool):
                agregats[statut] += valeur

    return agregats


# ---------------------------------------------------------------------------
# Complétude
# ---------------------------------------------------------------------------

def compute_presence_premier_ministre(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Taux de gouvernements avec un `premier_ministre` renseigné (non `null`)."""
    total = len(gouvernements)
    renseignes = sum(1 for g in gouvernements if _est_renseigne(g.get("premier_ministre")))

    return {
        "renseignes": renseignes,
        "total": total,
        "taux_pct": round(100 * renseignes / total, 2) if total else 0.0,
    }


def compute_taux_portefeuille_renseigne(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Taux de `membres[].portefeuille` renseigné, agrégé tous gouvernements confondus.

    Compte tous les ministres recensés (tous gouvernements confondus) : un
    `membres[]` vide ne contribue à aucun des deux compteurs — ce taux ne
    porte que sur les ministres effectivement présents dans le corpus.
    """
    total_membres = 0
    membres_avec_portefeuille = 0

    for gouvernement in gouvernements:
        membres = gouvernement.get("membres")
        if not isinstance(membres, list):
            continue
        for membre in membres:
            if not isinstance(membre, dict):
                continue
            total_membres += 1
            if _est_renseigne(membre.get("portefeuille")):
                membres_avec_portefeuille += 1

    return {
        "renseignes": membres_avec_portefeuille,
        "total": total_membres,
        "taux_pct": (
            round(100 * membres_avec_portefeuille / total_membres, 2) if total_membres else 0.0
        ),
    }


def compute_presence_meta(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Taux de gouvernements avec un bloc `meta` renseigné (dict non vide)."""
    total = len(gouvernements)
    renseignes = sum(1 for g in gouvernements if isinstance(g.get("meta"), dict) and g.get("meta"))

    return {
        "renseignes": renseignes,
        "total": total,
        "taux_pct": round(100 * renseignes / total, 2) if total else 0.0,
    }


# ---------------------------------------------------------------------------
# Cohérence
# ---------------------------------------------------------------------------

def compute_validation_schema(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Agrège les résultats de `schema_gouvernement.validate_profil_gouvernement` sur le corpus.

    Couvre déjà l'invariant du 49.3 (`statut`/`sort_49_3` non collapsés,
    voir `schema_gouvernement.validate_profil_gouvernement`) : ces erreurs
    remontent ici, sans indicateur dédié dupliqué.

    Returns:
        `{"total_gouvernements": int, "nb_gouvernements_invalides": int,
        "gouvernements_invalides": [{"gouvernement_id":..., "erreurs": [str,
        ...]}, ...]}`, triés par `gouvernement_id` pour un résultat
        déterministe.
    """
    gouvernements_invalides = [
        {"gouvernement_id": gouvernement.get("gouvernement_id"), "erreurs": erreurs}
        for gouvernement in gouvernements
        for erreurs in [validate_profil_gouvernement(gouvernement)]
        if erreurs
    ]
    gouvernements_invalides.sort(
        key=lambda entree: (entree["gouvernement_id"] is None, entree["gouvernement_id"])
    )

    return {
        "total_gouvernements": len(gouvernements),
        "nb_gouvernements_invalides": len(gouvernements_invalides),
        "gouvernements_invalides": gouvernements_invalides,
    }


def compute_coherence_schema_version(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare `schema_version` (racine) et `meta.schema_version`.

    Les deux champs doivent porter la même valeur : une divergence signale
    un profil de gouvernement partiellement régénéré.

    Returns:
        `{"gouvernements_incoherents": [{"gouvernement_id":...,
        "schema_version":..., "meta_schema_version":...}, ...]}`.
    """
    gouvernements_incoherents: list[dict[str, Any]] = []

    for gouvernement in gouvernements:
        schema_version = gouvernement.get("schema_version")
        meta = gouvernement.get("meta")
        meta_schema_version = meta.get("schema_version") if isinstance(meta, dict) else None

        if schema_version != meta_schema_version:
            gouvernements_incoherents.append({
                "gouvernement_id": gouvernement.get("gouvernement_id"),
                "schema_version": schema_version,
                "meta_schema_version": meta_schema_version,
            })

    return {"gouvernements_incoherents": gouvernements_incoherents}


def compute_doublons_gouvernement_id(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Détecte les `gouvernement_id` présents plusieurs fois dans le corpus.

    Le `gouvernement_id` (`"gouvernement:<libelle_abrege_an>"`) doit être
    unique : un doublon signale une erreur amont de génération. Les
    gouvernements sans `gouvernement_id` (absent ou vide) sont ignorés — ce
    défaut relève de la validation structurelle
    (`validate_profil_gouvernement`), pas de la cohérence inter-gouvernements.

    Returns:
        `{"doublons": [{"gouvernement_id": str, "occurrences": int}, ...]}`,
        trié par `gouvernement_id` pour un résultat déterministe ; liste
        vide si aucun doublon.
    """
    occurrences_par_id: dict[str, int] = {}
    for gouvernement in gouvernements:
        gouvernement_id = gouvernement.get("gouvernement_id")
        if not gouvernement_id:
            continue
        occurrences_par_id[gouvernement_id] = occurrences_par_id.get(gouvernement_id, 0) + 1

    return {
        "doublons": [
            {"gouvernement_id": gouvernement_id, "occurrences": occurrences}
            for gouvernement_id, occurrences in sorted(occurrences_par_id.items())
            if occurrences > 1
        ]
    }


# ---------------------------------------------------------------------------
# Couverture des textes portés
# ---------------------------------------------------------------------------

def _nb_textes_ou_none(gouvernement: dict[str, Any]) -> int | None:
    """Nombre de textes portés, `None` si le champ `textes` est absent ou `null`.

    Distinction volontairement conservée jusque dans le rapport : `[]` est un
    zéro observé, un champ absent est une donnée manquante — jamais rendue
    par un `0` (AGENTS.md §2.5).
    """
    textes = gouvernement.get("textes")
    if not isinstance(textes, list):
        return None
    return len(textes)


def compute_couverture_textes(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Couverture de chaque gouvernement par les archives de dossiers ingérées.

    Répond à #399 : un `textes[]` vide ne veut pas dire la même chose selon
    que la période du gouvernement tombe ou non dans le périmètre
    effectivement ingéré (`couverture_dossiers.AN_DOSSIERS_ARCHIVES`). Hors
    couverture, c'est une absence de source ; dans la couverture, c'est un
    zéro réellement constaté — et seul ce second cas mérite d'être signalé
    comme un défaut de données.

    La classification part des **législatures ingérées**, pas de la seule
    présence de `periode` : c'est la borne réelle de la source.

    Returns:
        `{"borne_couverture": "YYYY-MM-DD"|None, "legislatures_ingerees": [...],
        "libelle_couverture": str, "par_statut": {<statut>: n, ...},
        "lignes": [{"gouvernement_id":..., "nom":..., "periode_debut":...,
        "periode_fin":..., "statut_couverture":..., "nb_textes": int|None},
        ...], "sans_texte_hors_couverture": [...],
        "sans_texte_dans_couverture": [...]}`.

        `nb_textes` vaut `None` (et non `0`) quand le champ `textes` est
        absent ou `null`. `lignes` est trié par `nom` puis `gouvernement_id`,
        comme `compute_plage_dates_gouvernements`.
    """
    par_statut: dict[str, int] = {
        COUVERTURE_COUVERTE: 0,
        COUVERTURE_PARTIELLE: 0,
        COUVERTURE_HORS: 0,
        COUVERTURE_INDETERMINEE: 0,
    }
    lignes: list[dict[str, Any]] = []
    sans_texte_hors_couverture: list[str] = []
    sans_texte_dans_couverture: list[str] = []

    for gouvernement in gouvernements:
        periode = gouvernement.get("periode")
        periode = periode if isinstance(periode, dict) else {}
        debut = periode.get("debut")
        fin = periode.get("fin")

        statut = statut_couverture_textes(debut, fin)
        par_statut[statut] = par_statut.get(statut, 0) + 1

        nb_textes = _nb_textes_ou_none(gouvernement)
        gouvernement_id = gouvernement.get("gouvernement_id")

        if not nb_textes:  # 0 texte observé, ou champ absent
            if statut == COUVERTURE_COUVERTE:
                sans_texte_dans_couverture.append(gouvernement_id)
            elif statut in (COUVERTURE_HORS, COUVERTURE_PARTIELLE):
                sans_texte_hors_couverture.append(gouvernement_id)

        lignes.append({
            "gouvernement_id": gouvernement_id,
            "nom": gouvernement.get("nom"),
            "periode_debut": debut,
            "periode_fin": fin,
            "statut_couverture": statut,
            "nb_textes": nb_textes,
        })

    lignes.sort(key=lambda ligne: (ligne["nom"] or "", ligne["gouvernement_id"] or ""))

    return {
        "borne_couverture": borne_couverture_textes(),
        "legislatures_ingerees": list(legislatures_ingerees()),
        "libelle_couverture": libelle_couverture_textes(),
        "par_statut": par_statut,
        "lignes": lignes,
        "sans_texte_hors_couverture": sorted(i for i in sans_texte_hors_couverture if i),
        "sans_texte_dans_couverture": sorted(i for i in sans_texte_dans_couverture if i),
    }


# ---------------------------------------------------------------------------
# Tableau croisé des plages temporelles
# ---------------------------------------------------------------------------

def _parse_date_gouvernement(valeur: Any) -> date | None:
    """Parse une date ISO-8601 `"YYYY-MM-DD"` (sous-préfixe accepté), `None` si absente/invalide."""
    if not isinstance(valeur, str) or not valeur:
        return None
    try:
        return date.fromisoformat(valeur[:10])
    except ValueError:
        return None


def _plage_dates_membres(
    gouvernement: dict[str, Any], dates_invalides: list[dict[str, Any]]
) -> dict[str, str] | None:
    """Plage `{"min":..., "max":...}` de `membres[].debut`/`.fin`, `None` si aucune date exploitable.

    `fin` peut être `null` (mandat en cours) : exclu du calcul sans être
    compté comme une date invalide (absence légitime, jamais substituée par
    la date du jour, AGENTS.md §2.5). Un `debut` absent ou invalide, ou un
    `fin` présent mais invalide, est ajouté à `dates_invalides` (muté en
    place) plutôt qu'ignoré silencieusement.
    """
    membres = gouvernement.get("membres")
    if not isinstance(membres, list):
        return None

    gouvernement_id = gouvernement.get("gouvernement_id")
    dates_valides: list[date] = []

    for i, membre in enumerate(membres):
        debut = membre.get("debut") if isinstance(membre, dict) else None
        date_debut = _parse_date_gouvernement(debut)
        if date_debut is not None:
            dates_valides.append(date_debut)
        else:
            dates_invalides.append({
                "gouvernement_id": gouvernement_id, "champ": f"membres[{i}].debut", "valeur": debut,
            })

        fin = membre.get("fin") if isinstance(membre, dict) else None
        if fin is None:
            continue

        date_fin = _parse_date_gouvernement(fin)
        if date_fin is not None:
            dates_valides.append(date_fin)
        else:
            dates_invalides.append({
                "gouvernement_id": gouvernement_id, "champ": f"membres[{i}].fin", "valeur": fin,
            })

    if not dates_valides:
        return None

    return {"min": min(dates_valides).isoformat(), "max": max(dates_valides).isoformat()}


def _plage_dates_textes(
    gouvernement: dict[str, Any], dates_invalides: list[dict[str, Any]]
) -> dict[str, str] | None:
    """Plage `{"min":..., "max":...}` de `textes[].date_depot`/`.date_dernier_evenement`.

    `None` si aucune date exploitable. Chaque champ absent ou invalide est
    ajouté à `dates_invalides` (muté en place) plutôt qu'ignoré
    silencieusement — contrairement à `membres[].fin`, ces deux champs
    n'ont pas de cas `null` légitime documenté dans `schema_gouvernement.py`.
    """
    textes = gouvernement.get("textes")
    if not isinstance(textes, list):
        return None

    gouvernement_id = gouvernement.get("gouvernement_id")
    dates_valides: list[date] = []

    for i, texte in enumerate(textes):
        for champ in ("date_depot", "date_dernier_evenement"):
            valeur = texte.get(champ) if isinstance(texte, dict) else None
            date_parsee = _parse_date_gouvernement(valeur)
            if date_parsee is not None:
                dates_valides.append(date_parsee)
            else:
                dates_invalides.append({
                    "gouvernement_id": gouvernement_id, "champ": f"textes[{i}].{champ}", "valeur": valeur,
                })

    if not dates_valides:
        return None

    return {"min": min(dates_valides).isoformat(), "max": max(dates_valides).isoformat()}


def compute_plage_dates_gouvernements(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Tableau croisé des plages temporelles par gouvernement.

    Une ligne par gouvernement, avec deux cellules `{"min": "YYYY-MM-DD",
    "max": "YYYY-MM-DD"}` (ou `None` si aucune date exploitable) :
    `mandats_membres` (via `membres[].debut`/`.fin`) et `textes` (via
    `textes[].date_depot`/`.date_dernier_evenement`).

    Une date invalide (ou une entrée sans date exploitable) est exclue du
    calcul min/max (jamais traitée comme une date par défaut, AGENTS.md
    §2.5), mais comptée et recensée dans `dates_invalides` plutôt
    qu'ignorée silencieusement — sauf `membres[].fin = null`, qui signale
    légitimement un mandat en cours et n'est jamais compté comme invalide.

    Returns:
        `{"lignes": [{"gouvernement_id":..., "nom":...,
        "mandats_membres": {"min":..., "max":...} | None,
        "textes": {"min":..., "max":...} | None}, ...], "dates_invalides":
        [{"gouvernement_id":..., "champ": "membres[i].debut"|"membres[i].fin"|
        "textes[i].date_depot"|"textes[i].date_dernier_evenement",
        "valeur":...}, ...]}`. `lignes` trié par `nom` puis `gouvernement_id`
        (ordre déterministe en cas d'égalité ou de `nom` absent) ;
        `dates_invalides` trié par `gouvernement_id` puis `champ`.
    """
    dates_invalides: list[dict[str, Any]] = []

    lignes = [
        {
            "gouvernement_id": gouvernement.get("gouvernement_id"),
            "nom": gouvernement.get("nom"),
            "mandats_membres": _plage_dates_membres(gouvernement, dates_invalides),
            "textes": _plage_dates_textes(gouvernement, dates_invalides),
        }
        for gouvernement in gouvernements
    ]

    lignes.sort(key=lambda ligne: (ligne["nom"] or "", ligne["gouvernement_id"] or ""))
    dates_invalides.sort(
        key=lambda entree: (entree["gouvernement_id"] is None, entree["gouvernement_id"], entree["champ"])
    )

    return {"lignes": lignes, "dates_invalides": dates_invalides}


# ---------------------------------------------------------------------------
# Fraîcheur
# ---------------------------------------------------------------------------

def _parse_synchro_le(valeur: Any) -> datetime | None:
    """Parse une date ISO-8601 `sources[].synchro_le`, `None` si absente/invalide.

    Une date naïve (sans fuseau) est supposée UTC.
    """
    if not isinstance(valeur, str) or not valeur:
        return None

    texte = valeur[:-1] + "+00:00" if valeur.endswith("Z") else valeur
    try:
        date_synchro = datetime.fromisoformat(texte)
    except ValueError:
        return None

    return date_synchro if date_synchro.tzinfo is not None else date_synchro.replace(tzinfo=timezone.utc)


def _anciennete_jours(date_synchro: datetime, reference_date: datetime) -> int:
    """Nombre de jours écoulés entre `date_synchro` et `reference_date`."""
    return (reference_date - date_synchro).days


def compute_fraicheur_sources(
    gouvernements: list[dict[str, Any]], reference_date: datetime | None = None
) -> dict[str, Any]:
    """Ancienneté des sources (`sources[].synchro_le`) par type de source.

    Pour chaque type de source rencontré (`sources[].type`, `"null"` si
    absent), distribution en jours écoulés depuis la dernière synchro : min,
    max, médiane, moyenne. Les sources sans `synchro_le` valide sont
    ignorées.

    Args:
        gouvernements: liste de profils de gouvernement.
        reference_date: date de référence pour le calcul de l'ancienneté,
            injectable pour des tests déterministes (défaut :
            `datetime.now(timezone.utc)`).

    Returns:
        `{"total_sources_datees": int, "par_type_source": {type: {...}}}`.
        Un type de source absent de `gouvernements` n'apparaît pas dans le
        résultat.
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    anciennetes_par_type: dict[str, list[int]] = {}
    for gouvernement in gouvernements:
        for source in gouvernement.get("sources") or []:
            if not isinstance(source, dict):
                continue
            date_synchro = _parse_synchro_le(source.get("synchro_le"))
            if date_synchro is None:
                continue
            type_source = source.get("type") or "null"
            anciennetes_par_type.setdefault(type_source, []).append(
                _anciennete_jours(date_synchro, reference)
            )

    par_type_source: dict[str, Any] = {}
    for type_source in sorted(anciennetes_par_type):
        anciennetes = anciennetes_par_type[type_source]
        par_type_source[type_source] = {
            "nombre_sources": len(anciennetes),
            "min_jours": min(anciennetes),
            "max_jours": max(anciennetes),
            "mediane_jours": statistics.median(anciennetes),
            "moyenne_jours": round(statistics.mean(anciennetes), 2),
        }

    return {
        "total_sources_datees": sum(len(v) for v in anciennetes_par_type.values()),
        "par_type_source": par_type_source,
    }


def _anciennetes_sources_jours(gouvernement: dict[str, Any], reference_date: datetime) -> list[int]:
    """Anciennetés (en jours) des sources du gouvernement dont `synchro_le` est valide."""
    anciennetes: list[int] = []
    for source in gouvernement.get("sources") or []:
        if not isinstance(source, dict):
            continue
        date_synchro = _parse_synchro_le(source.get("synchro_le"))
        if date_synchro is not None:
            anciennetes.append(_anciennete_jours(date_synchro, reference_date))
    return anciennetes


def compute_gouvernements_perimes(
    gouvernements: list[dict[str, Any]],
    staleness_days: int,
    reference_date: datetime | None = None,
) -> list[str]:
    """`gouvernement_id` des gouvernements dont **toutes** les sources ont plus de `staleness_days` jours.

    Un gouvernement sans aucune source dont `synchro_le` est exploitable
    n'est jamais considéré comme périmé (il n'y a rien à mesurer) : seuls
    les gouvernements ayant au moins une source datée, et dont la source la
    plus fraîche dépasse tout de même le seuil, sont retournés.

    Args:
        gouvernements: liste de profils de gouvernement.
        staleness_days: seuil d'ancienneté (en jours) au-delà duquel une
            source est considérée périmée.
        reference_date: date de référence injectable (voir
            `compute_fraicheur_sources`).

    Returns:
        Liste triée des `gouvernement_id` de gouvernements périmés.
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    perimes = []
    for gouvernement in gouvernements:
        anciennetes = _anciennetes_sources_jours(gouvernement, reference)
        if anciennetes and min(anciennetes) > staleness_days:
            perimes.append(gouvernement.get("gouvernement_id"))

    return sorted(perimes)


# ---------------------------------------------------------------------------
# Agrégation des warnings
# ---------------------------------------------------------------------------

def _type_warning(warning: str) -> str:
    """Type d'un warning : préfixe avant le premier ':', message complet sinon."""
    prefixe, separateur, _ = warning.partition(":")
    return prefixe.strip() if separateur else warning.strip()


def compute_agregation_warnings(gouvernements: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile tous les `meta.warnings[]` des gouvernements par type.

    Le "type" d'un warning est déterminé par `_type_warning` (préfixe avant
    le premier ':'). Même contrat que `audit_groupe_dataset.compute_agregation_warnings`.

    Returns:
        `{"total_warnings": int, "par_type": {type: {"frequence": int,
        "gouvernement_ids": [str, ...]}}}`. `frequence` compte chaque
        occurrence (un gouvernement avec deux warnings du même type compte
        pour 2) ; `gouvernement_ids` liste sans doublon les gouvernements
        concernés par ce type, triés.
    """
    par_type: dict[str, dict[str, Any]] = {}
    total_warnings = 0

    for gouvernement in gouvernements:
        meta = gouvernement.get("meta") or {}
        warnings = meta.get("warnings") or []
        gouvernement_id = gouvernement.get("gouvernement_id")

        for warning in warnings:
            if not isinstance(warning, str) or not warning:
                continue
            total_warnings += 1
            type_warning = _type_warning(warning)
            entree = par_type.setdefault(type_warning, {"frequence": 0, "gouvernement_ids": set()})
            entree["frequence"] += 1
            entree["gouvernement_ids"].add(gouvernement_id)

    return {
        "total_warnings": total_warnings,
        "par_type": {
            type_warning: {
                "frequence": entree["frequence"],
                "gouvernement_ids": sorted(entree["gouvernement_ids"]),
            }
            for type_warning, entree in sorted(par_type.items())
        },
    }


# ---------------------------------------------------------------------------
# Assemblage du rapport
# ---------------------------------------------------------------------------

def build_report(
    gouvernements: list[dict[str, Any]],
    erreurs_lecture: list[dict[str, Any]],
    staleness_days: int = 30,
    reference_date: datetime | None = None,
) -> dict[str, Any]:
    """Assemble tous les indicateurs `compute_*` en un rapport structuré unique.

    Args:
        gouvernements: profils de gouvernement valides (sortie de
            `load_gouvernement_directory`).
        erreurs_lecture: erreurs de lecture (sortie de
            `load_gouvernement_directory`).
        staleness_days: seuil d'ancienneté en jours pour
            `compute_gouvernements_perimes` (défaut : 30).
        reference_date: date de référence injectable pour les indicateurs de
            fraîcheur, voir `compute_fraicheur_sources` (défaut :
            `datetime.now(timezone.utc)`).

    Returns:
        Dict sérialisable JSON, une section par catégorie d'indicateur
        (`volumetrie`, `completude`, `coherence`, `fraicheur`, `warnings`)
        plus `couverture_textes`, `plage_dates_gouvernements`, `meta` et
        `erreurs_lecture`. Outil
        de qualité interne : ce rapport ne doit jamais introduire de
        jugement de valeur, de score ou de classement (AGENTS.md §2.1).
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    return {
        "meta": {
            "genere_le": reference.isoformat(),
            "total_gouvernements": len(gouvernements),
            "total_erreurs_lecture": len(erreurs_lecture),
            "staleness_days": staleness_days,
        },
        "volumetrie": {
            "repartition_periode_actif": compute_repartition_periode_actif(gouvernements),
            "distribution_membres_textes": compute_distribution_membres_textes(gouvernements),
            "comptages_agreges": compute_comptages_agreges(gouvernements),
        },
        "completude": {
            "presence_premier_ministre": compute_presence_premier_ministre(gouvernements),
            "taux_portefeuille_renseigne": compute_taux_portefeuille_renseigne(gouvernements),
            "presence_meta": compute_presence_meta(gouvernements),
        },
        "coherence": {
            "validation_schema": compute_validation_schema(gouvernements),
            "coherence_schema_version": compute_coherence_schema_version(gouvernements),
            "doublons_gouvernement_id": compute_doublons_gouvernement_id(gouvernements),
        },
        "fraicheur": {
            "fraicheur_sources": compute_fraicheur_sources(gouvernements, reference_date=reference),
            "gouvernements_perimes": compute_gouvernements_perimes(
                gouvernements, staleness_days=staleness_days, reference_date=reference
            ),
        },
        "couverture_textes": compute_couverture_textes(gouvernements),
        "plage_dates_gouvernements": compute_plage_dates_gouvernements(gouvernements),
        "warnings": compute_agregation_warnings(gouvernements),
        "erreurs_lecture": erreurs_lecture,
    }


# ---------------------------------------------------------------------------
# Génération du rapport Markdown
# ---------------------------------------------------------------------------

def _md_escape(valeur: Any) -> str:
    """Neutralise les caractères cassant une cellule de tableau Markdown."""
    texte = "" if valeur is None else str(valeur)
    return texte.replace("|", "\\|").replace("\n", " ")


def _md_table(en_tetes: list[str], lignes: list[list[Any]], si_vide: str) -> str:
    """Construit un tableau Markdown, ou renvoie `si_vide` si `lignes` est vide."""
    if not lignes:
        return si_vide + "\n"

    entete = "| " + " | ".join(en_tetes) + " |"
    separateur = "| " + " | ".join("---" for _ in en_tetes) + " |"
    corps = "\n".join(
        "| " + " | ".join(_md_escape(cellule) for cellule in ligne) + " |" for ligne in lignes
    )
    return f"{entete}\n{separateur}\n{corps}\n"


def _md_section_volumetrie(volumetrie: dict[str, Any]) -> str:
    periode = volumetrie["repartition_periode_actif"]
    distribution = volumetrie["distribution_membres_textes"]
    lignes_distribution = [
        [champ, stats["min"], stats["max"], stats["mediane"], stats["moyenne"]]
        for champ, stats in distribution.items()
    ]
    lignes_comptages = sorted(volumetrie["comptages_agreges"].items())

    return (
        "## Volumétrie\n\n"
        "### Répartition par `periode.actif`\n\n"
        + _md_table(
            ["Total", "Actifs", "Inactifs", "Indéterminés"],
            [[
                periode["total_gouvernements"], periode["actifs"],
                periode["inactifs"], periode["indetermines"],
            ]],
            "Aucun gouvernement.",
        )
        + "\n### Distribution du nombre de `membres` / `textes` par gouvernement\n\n"
        + _md_table(
            ["Champ", "Min", "Max", "Médiane", "Moyenne"],
            lignes_distribution, "Aucun gouvernement.",
        )
        + "\n### Comptages agrégés par statut de texte (`comptages.par_statut`)\n\n"
        + _md_table(["Statut", "Total"], lignes_comptages, "Aucun gouvernement.")
    )


def _md_section_completude(completude: dict[str, Any]) -> str:
    pm = completude["presence_premier_ministre"]
    portefeuille = completude["taux_portefeuille_renseigne"]
    meta = completude["presence_meta"]

    return (
        "## Complétude\n\n"
        "### Présence d'un `premier_ministre` renseigné\n\n"
        + _md_table(
            ["Renseignés", "Total", "Taux (%)"],
            [[pm["renseignes"], pm["total"], pm["taux_pct"]]],
            "Aucun gouvernement.",
        )
        + "\n### Taux de `membres[].portefeuille` renseigné\n\n"
        + _md_table(
            ["Renseignés", "Total", "Taux (%)"],
            [[portefeuille["renseignes"], portefeuille["total"], portefeuille["taux_pct"]]],
            "Aucun membre.",
        )
        + "\n### Présence d'un bloc `meta` renseigné\n\n"
        + _md_table(
            ["Renseignés", "Total", "Taux (%)"],
            [[meta["renseignes"], meta["total"], meta["taux_pct"]]],
            "Aucun gouvernement.",
        )
    )


def _md_section_coherence(coherence: dict[str, Any]) -> str:
    lignes_validation = [
        [g["gouvernement_id"], "; ".join(g["erreurs"])]
        for g in coherence["validation_schema"]["gouvernements_invalides"]
    ]
    lignes_schema = [
        [g["gouvernement_id"], g["schema_version"], g["meta_schema_version"]]
        for g in coherence["coherence_schema_version"]["gouvernements_incoherents"]
    ]
    lignes_doublons = [
        [d["gouvernement_id"], d["occurrences"]] for d in coherence["doublons_gouvernement_id"]["doublons"]
    ]

    return (
        "## Cohérence\n\n"
        "### Validation du schéma (`validate_profil_gouvernement`)\n\n"
        + _md_table(
            ["gouvernement_id", "Erreurs"], lignes_validation, "Aucun gouvernement invalide détecté.",
        )
        + "\n### Divergence `schema_version` / `meta.schema_version`\n\n"
        + _md_table(
            ["gouvernement_id", "schema_version", "meta.schema_version"],
            lignes_schema, "Aucune divergence détectée.",
        )
        + "\n### Doublons de `gouvernement_id`\n\n"
        + _md_table(["gouvernement_id", "Occurrences"], lignes_doublons, "Aucun doublon détecté.")
    )


def _md_section_fraicheur(fraicheur: dict[str, Any], staleness_days: int) -> str:
    lignes_fraicheur = [
        [
            type_source, stats["nombre_sources"],
            stats["min_jours"], stats["max_jours"], stats["mediane_jours"], stats["moyenne_jours"],
        ]
        for type_source, stats in fraicheur["fraicheur_sources"]["par_type_source"].items()
    ]

    lignes_perimes = [[gouvernement_id] for gouvernement_id in fraicheur["gouvernements_perimes"]]

    return (
        "## Fraîcheur\n\n"
        "### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)\n\n"
        + _md_table(
            ["Type de source", "Nombre de sources", "Min", "Max", "Médiane", "Moyenne"],
            lignes_fraicheur, "Aucune source datée.",
        )
        + f"\n### Gouvernements périmés (toutes sources > {staleness_days} jours)\n\n"
        + _md_table(["gouvernement_id"], lignes_perimes, "Aucun gouvernement périmé.")
    )


def _fmt_couverture_cellule(statut: str | None) -> str:
    """Libellé lisible d'un statut de couverture (`hors couverture`, ...)."""
    return LIBELLES_COUVERTURE.get(statut or "", "indéterminée")


def _md_section_couverture_textes(couverture: dict[str, Any]) -> str:
    """Section « Couverture des textes portés » (#399).

    Sépare explicitement « hors couverture de la source » de « réellement à
    zéro » : sans cette distinction, un `textes[]` vide se lit comme un fait
    mesuré alors qu'il peut n'être qu'une absence d'archive (AGENTS.md §2.5).
    """
    par_statut = couverture["par_statut"]

    lignes = [
        [
            ligne["gouvernement_id"], ligne["nom"],
            f"{ligne['periode_debut'] or 'N/D'} → {ligne['periode_fin'] or 'en cours'}",
            _fmt_couverture_cellule(ligne["statut_couverture"]),
            "N/D" if ligne["nb_textes"] is None else ligne["nb_textes"],
        ]
        for ligne in couverture["lignes"]
    ]

    sans_texte_hors = couverture["sans_texte_hors_couverture"]
    sans_texte_dans = couverture["sans_texte_dans_couverture"]

    return (
        "## Couverture des textes portés\n\n"
        f"Archives de dossiers ingérées : **{couverture['libelle_couverture']}**.\n\n"
        "Un gouvernement dont la période est antérieure à cette borne n'a pas "
        "« zéro texte porté » : la source ne le couvre pas. Les deux cas sont "
        "distingués ci-dessous et ne doivent jamais être confondus "
        "(AGENTS.md §2.5). `Textes = N/D` signale un champ `textes` absent ou "
        "`null`, jamais transformé en `0`.\n\n"
        f"Couverte : {par_statut[COUVERTURE_COUVERTE]} · "
        f"partielle : {par_statut[COUVERTURE_PARTIELLE]} · "
        f"hors couverture : {par_statut[COUVERTURE_HORS]} · "
        f"indéterminée : {par_statut[COUVERTURE_INDETERMINEE]}\n\n"
        + _md_table(
            ["gouvernement_id", "Nom", "Période", "Couverture source", "Textes"],
            lignes, "Aucun gouvernement.",
        )
        + f"\n### Sans texte, dans la couverture ({len(sans_texte_dans)})\n\n"
        "Zéro réellement constaté : la source couvre la période et n'y "
        "rattache aucun texte — anomalie à instruire.\n\n"
        + _md_table(
            ["gouvernement_id"], [[i] for i in sans_texte_dans],
            "Aucun gouvernement sans texte dans la couverture.",
        )
        + f"\n### Sans texte, hors couverture ({len(sans_texte_hors)})\n\n"
        "Absence de source, pas un fait mesuré : aucune conclusion ne peut "
        "en être tirée, et rien ne doit être publié comme un zéro.\n\n"
        + _md_table(
            ["gouvernement_id"], [[i] for i in sans_texte_hors],
            "Aucun gouvernement sans texte hors couverture.",
        )
    )


def _fmt_plage_cellule(cellule: dict[str, str] | None, statut_couverture: str | None = None) -> str:
    """`"min → max"` si la cellule est renseignée, sinon `"N/D"` (donnée manquante).

    Quand l'absence s'explique par le périmètre de la source (`statut_couverture`
    hors/partiel), le `N/D` est qualifié plutôt que laissé nu : sans cela, il se
    lit comme un défaut de données (#399).
    """
    if cellule is not None:
        return f"{cellule['min']} → {cellule['max']}"
    if statut_couverture in (COUVERTURE_HORS, COUVERTURE_PARTIELLE):
        return f"N/D ({LIBELLES_COUVERTURE[statut_couverture]})"
    return "N/D"


def _md_section_plage_dates_gouvernements(
    plage: dict[str, Any], couverture: dict[str, Any]
) -> str:
    couverture_par_id = {
        ligne["gouvernement_id"]: ligne["statut_couverture"] for ligne in couverture["lignes"]
    }

    lignes = [
        [
            ligne["gouvernement_id"], ligne["nom"],
            _fmt_plage_cellule(ligne["mandats_membres"]),
            _fmt_plage_cellule(
                ligne["textes"], couverture_par_id.get(ligne["gouvernement_id"])
            ),
        ]
        for ligne in plage["lignes"]
    ]

    lignes_dates_invalides = [
        [e["gouvernement_id"], e["champ"], e["valeur"]] for e in plage["dates_invalides"]
    ]

    return (
        "## Tableau croisé des plages temporelles par gouvernement\n\n"
        "Pour chaque gouvernement, la période couverte par les dates "
        "disponibles (min → max) des mandats de ses membres et des textes "
        "qu'il a portés.\n\n"
        + _md_table(
            [
                "gouvernement_id", "Nom",
                "Mandats membres (min → max)", "Textes (min → max)",
            ],
            lignes, "Aucun gouvernement.",
        )
        + "\n> **`Textes`** : un `N/D (hors couverture)` signale une période "
        "hors du périmètre des archives ingérées, pas une absence de texte "
        "constatée — voir la section « Couverture des textes portés ».\n\n"
        + "> **`mandats_membres`** : calculée sur `membres[].debut`/`.fin`. "
        "Un `fin = null` signale un mandat en cours — exclu du calcul sans "
        "jamais être remplacé par la date du jour (AGENTS.md §2.5).\n\n"
        + f"### Dates `membres[]`/`textes[]` invalides ignorées pour le calcul "
        f"({len(plage['dates_invalides'])})\n\n"
        + _md_table(
            ["gouvernement_id", "Champ", "Valeur"],
            lignes_dates_invalides, "Aucune date invalide détectée.",
        )
    )


def _md_section_warnings(warnings: dict[str, Any]) -> str:
    lignes = [
        [type_warning, entree["frequence"], ", ".join(entree["gouvernement_ids"])]
        for type_warning, entree in warnings["par_type"].items()
    ]

    return (
        "## Warnings\n\n"
        f"Total : {warnings['total_warnings']}\n\n"
        + _md_table(["Type", "Fréquence", "Gouvernements concernés"], lignes, "Aucun warning.")
    )


def _md_section_erreurs_lecture(erreurs_lecture: list[dict[str, Any]]) -> str:
    lignes = [[e["fichier"], e["erreur"]] for e in erreurs_lecture]

    return (
        "## Erreurs de lecture\n\n"
        + _md_table(["Fichier", "Erreur"], lignes, "Aucune erreur de lecture.")
    )


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    """Génère un rapport Markdown lisible par un humain à partir du dict `build_report`.

    Une section par catégorie d'indicateur, sous forme de tableaux synthétiques.
    Aucun score ni classement n'est calculé : ce rapport présente les chiffres
    bruts produits par les fonctions `compute_*` (AGENTS.md §2.1).
    """
    meta = rapport["meta"]
    couverture = rapport["couverture_textes"]

    sections = [
        (
            "# Rapport d'audit du jeu de données gouvernements\n\n"
            f"Généré le {meta['genere_le']}. "
            f"{meta['total_gouvernements']} gouvernement(s) analysé(s), "
            f"{meta['total_erreurs_lecture']} erreur(s) de lecture. "
            f"Seuil de péremption des sources : {meta['staleness_days']} jour(s).\n\n"
            "Couverture des textes portés : "
            f"**{couverture['libelle_couverture']}** — au-delà de cette borne, "
            "un `textes[]` vide est une absence de source, pas un zéro "
            "constaté (#399).\n\n"
            "Ce rapport est un outil de qualité interne : il présente des "
            "indicateurs bruts, sans jugement de valeur ni classement.\n"
        ),
        _md_section_volumetrie(rapport["volumetrie"]),
        _md_section_couverture_textes(couverture),
        _md_section_plage_dates_gouvernements(
            rapport["plage_dates_gouvernements"], couverture
        ),
        _md_section_completude(rapport["completude"]),
        _md_section_coherence(rapport["coherence"]),
        _md_section_fraicheur(rapport["fraicheur"], meta["staleness_days"]),
        _md_section_warnings(rapport["warnings"]),
        _md_section_erreurs_lecture(rapport["erreurs_lecture"]),
    ]

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit_gouvernement_dataset.py",
        description=(
            "Audite un jeu de données de profils de gouvernement : volumétrie, "
            "complétude, cohérence, fraîcheur des sources, plages temporelles "
            "par gouvernement et warnings agrégés. Outil de qualité interne, "
            "ne produit aucun score ni classement."
        ),
    )
    parser.add_argument(
        "--input-dir",
        default="pivot_data/gouvernements",
        metavar="DOSSIER",
        help=(
            "Dossier contenant les fichiers gouvernement-*.json à auditer "
            "(scan récursif, défaut : pivot_data/gouvernements)."
        ),
    )
    parser.add_argument(
        "--output-json",
        default=None,
        metavar="FICHIER",
        help="Chemin du rapport JSON (défaut : affiché sur stdout).",
    )
    parser.add_argument(
        "--output-md",
        default=None,
        metavar="FICHIER",
        help="Chemin du rapport Markdown (défaut : non généré).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DOSSIER",
        help=(
            "Écrit JSON et Markdown sous ce dossier avec un nom horodaté "
            "(audit_gouvernement_<horodatage-UTC>.json/.md) au lieu de nommer "
            "chaque fichier — incompatible avec --output-json/--output-md."
        ),
    )
    parser.add_argument(
        "--staleness-days",
        type=int,
        default=30,
        metavar="JOURS",
        help="Seuil d'ancienneté (jours) au-delà duquel un gouvernement est périmé (défaut : 30).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.output_dir and (args.output_json or args.output_md):
        print(
            "[!] --output-dir est incompatible avec --output-json/--output-md.",
            file=sys.stderr,
        )
        return 1

    output_json_path = args.output_json
    output_md_path = args.output_md
    if args.output_dir:
        horodatage = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_json_path = str(Path(args.output_dir) / f"audit_gouvernement_{horodatage}.json")
        output_md_path = str(Path(args.output_dir) / f"audit_gouvernement_{horodatage}.md")

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"[!] Dossier introuvable : {input_dir}", file=sys.stderr)
        return 1

    gouvernements, erreurs_lecture = load_gouvernement_directory(input_dir)
    print(
        f"→ {len(gouvernements)} gouvernement(s) chargé(s), {len(erreurs_lecture)} erreur(s) de lecture.",
        file=sys.stderr,
    )

    rapport = build_report(gouvernements, erreurs_lecture, staleness_days=args.staleness_days)
    output_json = json.dumps(rapport, ensure_ascii=False, indent=2)

    if output_json_path:
        out_path = Path(output_json_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")
        print(f"  ✓ Rapport JSON écrit : {out_path}", file=sys.stderr)
    else:
        print(output_json)

    if output_md_path:
        md_path = Path(output_md_path)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(generate_markdown_report(rapport), encoding="utf-8")
        print(f"  ✓ Rapport Markdown écrit : {md_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
