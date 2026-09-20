#!/usr/bin/env python3
"""
audit_pivot_dataset.py — Audit du jeu de données pivot.

Sous-tâche 1/6 de l'issue #137 : couche de chargement des fichiers pivot,
volontairement séparée de la logique de calcul des indicateurs afin de
rester testable indépendamment : un fichier JSON malformé ne doit jamais
interrompre le scan du répertoire.

Sous-tâche 2/6 : indicateurs de volumétrie, sous forme de fonctions pures
(liste de profils pivot -> dict sérialisable JSON), sans aucune I/O. Le
rapport JSON/Markdown et la CLI sont ajoutés par une sous-issue dédiée.

Sous-tâche 5/6 : fraîcheur des données (ancienneté de `sources[].synchro_le`)
et agrégation des `meta.warnings[]`, toujours sous forme de fonctions pures
avec une date de référence injectable (jamais de `datetime.now()` en dur)
pour rendre les tests déterministes.
Sous-tâche 4/6 : indicateurs de cohérence (mêmes contraintes de pureté) —
doublons d'`id`, divergence `schema_version`/`meta.schema_version`, dates de
traçabilité invalides ou futures, et cohérence `chambre`/`sources[].type`.
Sous-tâche 3/6 : indicateurs de complétude (taux de remplissage, profils
sans activité, présence des métadonnées `meta`). Mêmes contraintes :
fonctions pures, sans I/O. Une donnée absente ou vide n'est jamais
comptée comme renseignée (AGENTS.md §2.5 : "missing data means missing
data, never default 0").

Sous-tâche 6/6 : CLI (`main()` / `_build_arg_parser()`), assemblage de tous
les indicateurs ci-dessus dans `build_report()` et génération d'un rapport
Markdown lisible par un humain (`generate_markdown_report()`). Ce rapport est
un outil de qualité interne : il ne doit jamais introduire de jugement de
valeur, de score ou de classement (AGENTS.md §2.1).

Sous-issue 1/6 de #316 : `compute_plage_dates_candidats`, symétrique de
`compute_tableau_croise_candidats` (#175) mais pour la plage temporelle
(min/max) de chaque type de donnée plutôt que son volume.

Allègement du rapport (2026-08-18) : les deux tableaux croisés ne détaillent
que les candidats déclarés et n'exposent les profils de roster qu'agrégés par
groupe ; les indicateurs « distribution des listes métier » et « sources
déclarées », qui mélangeaient ces deux populations, ont été retirés — voir
`docs/decisions/audit-rapport-perimetre-candidats.md`.

Aucune dépendance lourde : stdlib uniquement.
"""

import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from schema_pivot import (
    KNOWN_CHAMBRES,
    KNOWN_PROVENANCES,
    libelle_chambres,
    lire_chambres,
)
from amendements_index import (
    DEFAULT_AMENDEMENTS_DIR,
    charger as charger_amendements,
)
from scrutins_index import DEFAULT_SCRUTINS_PATH, charger as charger_scrutins
# Les deux populations de `pivot_data/profiles/` (#630). Ce module CALCULAIT
# déjà la répartition par provenance ; ce qu'il ne faisait pas, c'est la rendre
# visible à côté des comptes que l'on recopie — « → 481 profil(s) chargé(s) »
# sur la console, « Total profils : 481 » en tête du rapport. Une ventilation
# calculée deux sections plus bas n'empêche personne d'écrire « 481 profils ».
from population_profils import Ventilation, ventiler

# Types de sources attendus par chambre pour compute_coherence_chambre_sources :
# chaque chambre doit avoir déclaré au moins une source de l'un de ces types.
# "PE" utilise "parltrack" (dumps croisés Parltrack/Wikidata, voir
# normalize_parltrack_dumps.py / mep_profile.py) et "europarl" (Open Data
# Portal du Parlement européen, voir normalize_europarl.py) — pas
# "assemblee_nationale", qui désigne le référentiel officiel des acteurs de
# l'Assemblée nationale (chambre "AN" uniquement). "mairie" n'a pas de type de
# source dédié dans KNOWN_SOURCE_TYPES à ce stade et n'est donc jamais
# signalée en incohérence par cette fonction.
# `nosdeputes`/`nossenateurs` restent listés après #529 : cette table LIT le
# corpus publié, elle ne décrit pas ce que la collecte produit. 476 profils
# portent encore l'un de ces deux types ; les retirer ferait déclarer
# « incohérence chambre/sources » sur des profils parfaitement valides — un
# audit qui signale une panne inventée est pire qu'un audit qui se tait.
MAPPING_CHAMBRE_SOURCES: dict[str, frozenset[str]] = {
    "AN": frozenset({"nosdeputes", "assemblee_nationale"}),
    "Senat": frozenset({"nossenateurs"}),
    "PE": frozenset({"parltrack", "europarl"}),
}

# Listes du schéma pivot dont on mesure la volumétrie par profil.
CHAMPS_LISTES_VOLUMETRIE: tuple[str, ...] = (
    "votes", "textes_portes", "amendements", "interventions",
)

# Champs dont on mesure le taux de remplissage (complétude).
CHAMPS_COMPLETUDE: tuple[str, ...] = ("parti", "groupe", "tags_thematiques", "mandats")

# Listes d'activité : un profil sans aucun élément dans ces trois champs est
# un candidat à un enrichissement manquant.
CHAMPS_ACTIVITE: tuple[str, ...] = ("votes", "amendements", "interventions")


#: Les blocs du profil pivot que les indicateurs lisent **entiers** — relevés
#: dans le code des quinze `compute_*`, pas dans l'énoncé (#635) :
#:
#:   `id`               presque tous les indicateurs (c'est la clé publiée)
#:   `nom`              les deux tableaux croisés
#:   `parti`, `groupe`  `compute_taux_remplissage`, `_cle_groupe`
#:   `schema_version`   `compute_coherence_schema_version`
#:   `chambres`,        `schema_pivot.lire_chambres` — les deux, le scalaire
#:   `chambre`          étant le repli déclaré de #493
#:   `sources`          fraîcheur, validité des dates, cohérence chambre/sources
#:   `meta`             provenance, warnings, schema_version, genere_le, licence
#:
#: Ce que personne n'ouvre : `identite`, `identifiants`, `couverture`.
BLOCS_LUS_AUDIT: tuple[str, ...] = (
    "id", "nom", "parti", "groupe", "schema_version",
    "chambres", "chambre", "sources", "meta",
)

#: Listes métier dont l'audit ne lit que le **cardinal** — `_est_renseigne`
#: n'y teste que « y a-t-il quelque chose ? ». `mandats` pèse 12,6 Mo sur le
#: corpus committé du 30/08/2026 pour cette seule question.
LISTES_REDUITES_AU_CARDINAL: tuple[str, ...] = ("mandats", "tags_thematiques")

#: Listes métier que l'audit parcourt **réellement** — mais dont il ne tire que
#: deux choses : leur cardinal (`_taille_liste`) et la plage de dates de leurs
#: entrées (`compute_plage_dates_candidats`). Ce sont ces deux résultats qui
#: sont retenus, pas les entrées : `amendements` seul pèse 577,3 Mo sur le
#: corpus committé, et 6,09 millions de mappings à deux clés ne tiennent dans
#: aucune projection par clés — seule leur **réduction** tient.
LISTES_REDUITES_A_LEUR_PLAGE: tuple[str, ...] = CHAMPS_LISTES_VOLUMETRIE


@dataclass(frozen=True)
class ListeReduite:
    """Ce qu'une liste métier laisse derrière elle une fois relâchée (#635).

    Exactement ce que les indicateurs en lisent : son cardinal, la plage de
    dates de ses entrées, et le nombre de dates présentes mais illisibles.
    `__len__` la rend interchangeable avec la liste elle-même pour
    `_taille_liste` et `_est_renseigne`, comme `nombre_d_entrees` accepte les
    deux formes dans l'audit de #628.
    """

    nb: int
    date_min: str | None = None
    date_max: str | None = None
    dates_ignorees: int = 0

    def __len__(self) -> int:
        return self.nb


def reduire_liste(
    champ: str, entrees: Any, scrutins_index: Any = None,
    amendements_index: Any = None,
) -> Any:
    """Réduit une liste métier à ce que les indicateurs en lisent.

    La réduction **appelle les mesures elles-mêmes** (`_plage_dates_*`) plutôt
    que de les réimplémenter : c'est ce qui garantit, par construction, que le
    rapport tiré des listes réduites est celui qu'on aurait tiré des listes
    entières. Une valeur qui n'est pas une liste est rendue telle quelle — la
    projection ne doit rien inventer sur une donnée malformée.
    """
    if not isinstance(entrees, list):
        return entrees
    ignorees = {champ: 0}
    if champ in LISTES_REDUITES_A_LEUR_PLAGE:
        if champ == "textes_portes":
            plage = _plage_dates_textes_portes({champ: entrees}, ignorees)
        else:
            plage = _plage_dates_champ_simple(
                {champ: entrees}, champ, ignorees, scrutins_index, amendements_index
            )
        return ListeReduite(len(entrees), plage["min"], plage["max"], ignorees[champ])
    return ListeReduite(len(entrees))


def projeter_profil(
    document: dict[str, Any], scrutins_index: Any = None,
    amendements_index: Any = None,
) -> dict[str, Any]:
    """Le profil pivot réduit à ce que les indicateurs en lisent."""
    projection: dict[str, Any] = {
        bloc: document[bloc] for bloc in BLOCS_LUS_AUDIT if bloc in document
    }
    for champ in (*LISTES_REDUITES_AU_CARDINAL, *LISTES_REDUITES_A_LEUR_PLAGE):
        if champ in document:
            projection[champ] = reduire_liste(
                champ, document[champ], scrutins_index, amendements_index
            )
    return projection


def load_pivot_directory(
    input_dir: Path, scrutins_index: Any = None, amendements_index: Any = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scanne récursivement `input_dir` à la recherche de fichiers `*.pivot.json`.

    **Aucun document n'est conservé entier (#635).** Un profil est lu, projeté
    sur `BLOCS_LUS_AUDIT` et sur la réduction de ses listes métier, puis
    relâché. Les garder entiers coûtait ~2,7 Gio sur les 481 profils committés
    du 30/08/2026 (651,5 Mo) : sous un plafond `RLIMIT_AS` de 2,0 Gio, la même
    boucle `json.loads` accumulée n'atteignait pas le 300e profil (293e et 304e
    sur deux exécutions) — facteur de gonflement mesuré × 3,6 à × 4,0. C'est le motif de
    `docs/decisions/oom-lecture-amendements-par-candidat.md`, et le patron de
    `docs/decisions/audit-599-projection-blocs-lus-628.md`.

    **Les index sont demandés ici parce que la réduction résout des dates.**
    Depuis #431 et #432 un amendement et un vote ne portent plus la leur : elle
    vit dans l'index partagé. Passer ici les index qui seront passés à
    `build_report` est donc la condition pour que le rapport soit celui des
    listes entières ; ne rien passer des deux côtés est également cohérent
    (c'est ce que font les tests), passer l'un et pas l'autre ne l'est pas.

    Args:
        input_dir: répertoire racine à scanner (récursif).
        scrutins_index: index des scrutins (#432), pour dater les votes.
        amendements_index: index des amendements (#431), pour dater les
            amendements.

    Returns:
        Tuple (profils_valides, erreurs_lecture) :
          - profils_valides : liste des profils pivot **projetés** chargés avec
            succès, triés par chemin de fichier pour un résultat déterministe.
          - erreurs_lecture : liste de {"fichier": str, "erreur": str} pour
            chaque fichier n'ayant pas pu être chargé (JSON invalide, objet
            racine non-dict, erreur de lecture...). Un fichier problématique
            n'interrompt jamais le scan des suivants.
    """
    profils_valides: list[dict[str, Any]] = []
    erreurs_lecture: list[dict[str, Any]] = []

    for path in sorted(input_dir.rglob("*.pivot.json")):
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

        profils_valides.append(
            projeter_profil(data, scrutins_index, amendements_index))
        del data

    return profils_valides, erreurs_lecture


def _taille_liste(profil: dict[str, Any], champ: str) -> int:
    """Longueur de `profil[champ]`, `0` si absent ou `null` (donnée manquante).

    Accepte indifféremment la liste réelle et sa `ListeReduite` (#635) : les
    tests nourrissent les mesures avec de vraies listes, le chargeur avec leur
    réduction, et le chiffre lu doit être le même des deux formes.
    """
    valeur = profil.get(champ)
    return len(valeur) if valeur else 0


def compute_repartition_chambre(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Nombre total de profils et répartition par chambre (`chambres`, #494).

    **Ce n'est plus une partition.** Depuis #493 un profil porte la *liste* des
    chambres où il a siégé, et il est donc compté dans **chacune** — un
    bicaméral AN + PE compte pour un dans `AN` et pour un dans `PE`. La somme de
    `par_chambre` peut donc dépasser `total_profils`, et `total_attributions` la
    donne explicitement : publier un dénominateur sans dire ce qu'il dénombre est
    précisément ce qu'AGENTS.md §2.7 interdit. `total_profils` reste le nombre de
    profils, inchangé.

    Un profil dont la chambre n'est pas déterminée (`chambres` vide, ou scalaire
    absent/inconnu avant régénération) est compté sous la clé `"null"` — donnée
    manquante, jamais chambre par défaut (§2.5).
    """
    repartition: dict[str, int] = {chambre: 0 for chambre in sorted(KNOWN_CHAMBRES)}
    repartition["null"] = 0
    total_attributions = 0

    for profil in profils:
        chambres = lire_chambres(profil)
        if not chambres:
            repartition["null"] += 1
            total_attributions += 1
            continue
        for chambre in chambres:
            repartition[chambre] += 1
            total_attributions += 1

    return {
        "total_profils": len(profils),
        "total_attributions": total_attributions,
        "par_chambre": repartition,
    }


def compute_repartition_provenance(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Nombre total de profils et répartition par `meta.provenance`.

    Un profil sans `meta.provenance` (pivot généré avant #189) est compté
    sous `"candidat_declare"`, la valeur de repli rétro-compatible retenue
    par `validate_profil()` (voir
    `docs/decisions/provenance-pivot.md`). Les valeurs hors
    `KNOWN_PROVENANCES` sont comptées sous la clé `"null"`, pour garantir un
    rapport toujours sérialisable en JSON quelle que soit la donnée.
    """
    repartition: dict[str, int] = {provenance: 0 for provenance in sorted(KNOWN_PROVENANCES)}
    repartition["null"] = 0

    for profil in profils:
        meta = profil.get("meta")
        provenance = meta.get("provenance") if isinstance(meta, dict) else None

        if provenance is None:
            cle = "candidat_declare"
        elif provenance in KNOWN_PROVENANCES:
            cle = provenance
        else:
            cle = "null"

        repartition[cle] += 1

    return {
        "total_profils": len(profils),
        "par_provenance": repartition,
    }


def _stats_volumes(tailles: list[int]) -> dict[str, Any]:
    """Min/max/médiane/moyenne d'une série de volumes.

    Sur une série vide, toutes les statistiques valent `null` : il n'y a
    rien à mesurer, et on ne substitue jamais 0 à une statistique absente
    (AGENTS.md §2.5).
    """
    if not tailles:
        return {"min": None, "max": None, "mediane": None, "moyenne": None}

    return {
        "min": min(tailles),
        "max": max(tailles),
        "mediane": statistics.median(tailles),
        "moyenne": round(statistics.mean(tailles), 2),
    }


def _parse_synchro_le(valeur: Any) -> datetime | None:
    """Parse une date ISO-8601 `sources[].synchro_le`, `None` si absente/invalide.

    Les dates invalides sont normalement déjà filtrées en amont (#156) ;
    cette fonction reste défensive pour ne jamais lever d'exception ici. Une
    date naïve (sans fuseau) est supposée UTC.
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


def _anciennetes_sources_jours(profil: dict[str, Any], reference_date: datetime) -> list[int]:
    """Anciennetés (en jours) des sources du profil dont `synchro_le` est valide."""
    anciennetes: list[int] = []
    for source in profil.get("sources") or []:
        if not isinstance(source, dict):
            continue
        date_synchro = _parse_synchro_le(source.get("synchro_le"))
        if date_synchro is not None:
            anciennetes.append(_anciennete_jours(date_synchro, reference_date))
    return anciennetes


def compute_fraicheur_sources(
    profils: list[dict[str, Any]], reference_date: datetime | None = None
) -> dict[str, Any]:
    """Ancienneté des sources (`sources[].synchro_le`) par type de source.

    Pour chaque type de source rencontré (`sources[].type`, `"null"` si
    absent), distribution en jours écoulés depuis la dernière synchro : min,
    max, médiane, moyenne. Les sources sans `synchro_le` valide sont ignorées
    (dates déjà filtrées en amont par #156).

    Args:
        profils: liste de profils pivot.
        reference_date: date de référence pour le calcul de l'ancienneté,
            injectable pour des tests déterministes (défaut :
            `datetime.now(timezone.utc)`).

    Returns:
        `{"total_sources_datees": int, "par_type_source": {type: {...}}}`.
        Un type de source absent de `profils` n'apparaît pas dans le résultat.
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    anciennetes_par_type: dict[str, list[int]] = {}
    for profil in profils:
        for source in profil.get("sources") or []:
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


def compute_profils_perimes(
    profils: list[dict[str, Any]],
    staleness_days: int,
    reference_date: datetime | None = None,
) -> list[str]:
    """`id` des profils dont **toutes** les sources ont plus de `staleness_days` jours.

    Un profil sans aucune source dont `synchro_le` est exploitable n'est
    jamais considéré comme périmé (il n'y a rien à mesurer) : seuls les
    profils ayant au moins une source datée, et dont la source la plus
    fraîche dépasse tout de même le seuil, sont retournés.

    Args:
        profils: liste de profils pivot.
        staleness_days: seuil d'ancienneté (en jours) au-delà duquel une
            source est considérée périmée.
        reference_date: date de référence injectable (voir
            `compute_fraicheur_sources`).

    Returns:
        Liste triée des `id` de profils périmés.
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    perimes = []
    for profil in profils:
        anciennetes = _anciennetes_sources_jours(profil, reference)
        if anciennetes and min(anciennetes) > staleness_days:
            perimes.append(profil.get("id"))

    return sorted(perimes)


def _type_warning(warning: str) -> str:
    """Type d'un warning : préfixe avant le premier ':', message complet sinon.

    Convention déjà utilisée dans le dépôt pour les warnings de
    `meta.warnings[]` (voir les constantes `WARNING_PREFIX_*` de
    `candidate_profile.py`, ex. `"identité introuvable : ..."`).
    """
    prefixe, separateur, _ = warning.partition(":")
    return prefixe.strip() if separateur else warning.strip()


def compute_agregation_warnings(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile tous les `meta.warnings[]` des profils par type.

    Le "type" d'un warning est déterminé par `_type_warning` (préfixe avant
    le premier ':').

    Returns:
        `{"total_warnings": int, "par_type": {type: {"frequence": int,
        "ids": [str, ...]}}}`. `frequence` compte chaque occurrence (un
        profil avec deux warnings du même type compte pour 2) ; `ids` liste
        sans doublon les profils concernés par ce type, triés.
    """
    par_type: dict[str, dict[str, Any]] = {}
    total_warnings = 0

    for profil in profils:
        meta = profil.get("meta") or {}
        warnings = meta.get("warnings") or []
        profil_id = profil.get("id")

        for warning in warnings:
            if not isinstance(warning, str) or not warning:
                continue
            total_warnings += 1
            type_warning = _type_warning(warning)
            entree = par_type.setdefault(type_warning, {"frequence": 0, "ids": set()})
            entree["frequence"] += 1
            entree["ids"].add(profil_id)

    return {
        "total_warnings": total_warnings,
        "par_type": {
            type_warning: {
                "frequence": entree["frequence"],
                "ids": sorted(entree["ids"]),
            }
            for type_warning, entree in sorted(par_type.items())
        },
    }


def compute_doublons_id(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Détecte les `id` présents plusieurs fois dans le corpus pivot.

    L'`id` pivot est le slug du profil depuis #487 — donc son nom de fichier —
    et doit être unique : un doublon signale une erreur amont de génération ou
    de fusion. Les profils sans `id` (absent ou vide) sont ignorés — ce défaut
    relève de la validation structurelle (`validate_profil`), pas de la
    cohérence inter-profils.

    Returns:
        {"doublons": [{"id": str, "occurrences": int}, ...]}, trié par `id`
        pour un résultat déterministe ; liste vide si aucun doublon.
    """
    occurrences_par_id: dict[str, int] = {}
    for profil in profils:
        id_ = profil.get("id")
        if not id_:
            continue
        occurrences_par_id[id_] = occurrences_par_id.get(id_, 0) + 1

    return {
        "doublons": [
            {"id": id_, "occurrences": occurrences}
            for id_, occurrences in sorted(occurrences_par_id.items())
            if occurrences > 1
        ]
    }


def compute_coherence_schema_version(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare `schema_version` (racine) et `meta.schema_version`.

    Les deux champs doivent porter la même valeur : une divergence signale un
    profil partiellement régénéré (ex. `meta` reconstruit sans mettre à jour
    la racine, ou l'inverse).

    Returns:
        {"profils_incoherents": [{"id":..., "schema_version":...,
                                   "meta_schema_version":...}, ...]}
    """
    profils_incoherents: list[dict[str, Any]] = []

    for profil in profils:
        schema_version = profil.get("schema_version")
        meta = profil.get("meta")
        meta_schema_version = meta.get("schema_version") if isinstance(meta, dict) else None

        if schema_version != meta_schema_version:
            profils_incoherents.append({
                "id": profil.get("id"),
                "schema_version": schema_version,
                "meta_schema_version": meta_schema_version,
            })

    return {"profils_incoherents": profils_incoherents}


def _erreur_date(valeur: Any, maintenant: datetime) -> str | None:
    """Code d'erreur pour `valeur` si ce n'est pas une date ISO-8601 passée valide, sinon `None`.

    **`non_renseigne` n'est pas `format_invalide` (#726).** La prémisse d'origine
    — « ces champs sont générés par le pipeline lui-même, une valeur absente
    signale toujours une anomalie amont » — était vraie et ne l'est plus : depuis
    #529, les entrées `sources[].type == "nosdeputes"` sont **conservées sans
    être recollectées**, parce que la clause ODbL en dépend (`AGENTS.md` §7).
    Rien ne peut plus leur donner de date, et elles sont **464 sur les 1 115**
    entrées `sources[]` publiées au 03/09/2026. Les ranger sous « format
    invalide » confond une donnée absente avec une donnée fautive — la
    distinction même que §2 règle 5 impose, ici dans l'outil chargé de la faire
    respecter.

    Une valeur non-chaîne reste `format_invalide` : ce n'est pas une absence,
    c'est une valeur d'un type que le champ n'admet pas.
    """
    if valeur is None or (isinstance(valeur, str) and not valeur.strip()):
        return "non_renseigne"
    if not isinstance(valeur, str):
        return "format_invalide"

    try:
        parsed = datetime.fromisoformat(valeur.replace("Z", "+00:00"))
    except ValueError:
        return "format_invalide"

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return "date_future" if parsed > maintenant else None


def compute_validite_dates(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Valide les dates de traçabilité `sources[].synchro_le` et `meta.genere_le`.

    Une date est en défaut si elle est absente, si elle n'est pas une chaîne
    ISO-8601 parseable (`datetime.fromisoformat`, suffixe `Z` accepté comme UTC),
    ou si elle est postérieure à l'instant de l'audit.

    **Les trois cas ne se lisent pas de la même façon (#726).** Une valeur future
    signale toujours une anomalie amont, et une valeur illisible aussi ; une
    valeur ABSENTE, depuis #529, peut décrire une source retirée du pipeline et
    conservée pour la clause ODbL (`AGENTS.md` §7). D'où `non_renseigne`, séparé
    de `format_invalide` : le rendu Markdown agrège le premier et énumère les
    seconds.

    Returns:
        {"dates_invalides": [{"id":..., "champ": "meta.genere_le" |
                               "sources[i].synchro_le", "valeur":...,
                               "erreur": "non_renseigne" | "format_invalide"
                                          | "date_future"}, ...]}
    """
    maintenant = datetime.now(timezone.utc)
    dates_invalides: list[dict[str, Any]] = []

    for profil in profils:
        id_ = profil.get("id")

        meta = profil.get("meta")
        meta = meta if isinstance(meta, dict) else {}
        valeur_meta = meta.get("genere_le")
        erreur_meta = _erreur_date(valeur_meta, maintenant)
        if erreur_meta:
            dates_invalides.append({
                "id": id_, "champ": "meta.genere_le", "valeur": valeur_meta, "erreur": erreur_meta,
            })

        sources = profil.get("sources")
        if isinstance(sources, list):
            for i, source in enumerate(sources):
                if not isinstance(source, dict):
                    continue
                valeur_source = source.get("synchro_le")
                erreur_source = _erreur_date(valeur_source, maintenant)
                if erreur_source:
                    dates_invalides.append({
                        "id": id_,
                        "champ": f"sources[{i}].synchro_le",
                        "valeur": valeur_source,
                        "erreur": erreur_source,
                    })

    return {"dates_invalides": dates_invalides}


def compute_coherence_chambre_sources(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Vérifie la cohérence entre `chambres` et les types de `sources[]` déclarés.

    Chaque chambre attend au moins une source d'un type de référence, voir
    `MAPPING_CHAMBRE_SOURCES` : `"AN"` -> `nosdeputes`/`assemblee_nationale`,
    `"Senat"` -> `nossenateurs`, `"PE"` -> `parltrack`/`europarl`. `"mairie"`
    et une chambre absente/inconnue n'ont pas de mapping de référence à ce
    stade et ne sont jamais signalées en incohérence par cette fonction.

    #494 — le contrôle porte sur **chaque** chambre de `chambres`, ce que le
    docstring d'origine promettait déjà (« chaque chambre attend ») sans que le
    scalaire puisse le tenir : il n'en portait qu'une, donc un profil AN + PE
    n'était contrôlé que sur celle des deux qui l'avait emporté. C'est un
    contrôle **élargi**, pas déplacé : un profil déjà signalé le reste.

    Returns:
        {"profils_incoherents": [{"id":..., "chambres": [...],
                                   "chambres_sans_source": [...],
                                   "types_sources": [...]}, ...]}
        `chambres_sans_source` nomme celles des chambres qu'aucune source
        attendue n'étaye — sans elle, un profil bicaméral signalé ne dirait pas
        laquelle de ses deux chambres est en cause.
    """
    profils_incoherents: list[dict[str, Any]] = []

    for profil in profils:
        chambres = lire_chambres(profil)
        controlees = [c for c in chambres if c in MAPPING_CHAMBRE_SOURCES]
        if not controlees:
            continue

        sources = profil.get("sources")
        types_sources = (
            [s.get("type") for s in sources if isinstance(s, dict)]
            if isinstance(sources, list) else []
        )

        sans_source = [
            c for c in controlees
            if not MAPPING_CHAMBRE_SOURCES[c].intersection(types_sources)
        ]
        if sans_source:
            profils_incoherents.append({
                "id": profil.get("id"),
                "chambres": chambres,
                "chambres_sans_source": sans_source,
                "types_sources": types_sources,
            })

    return {"profils_incoherents": profils_incoherents}

def _est_renseigne(valeur: Any) -> bool:
    """True si `valeur` est une donnée renseignée.

    `None`, chaîne vide et liste vide comptent comme non renseignés — une
    chaîne/liste vide est une absence de donnée déguisée, jamais un
    remplissage valide (AGENTS.md §2.5).
    """
    if valeur is None:
        return False
    if isinstance(valeur, (str, list, ListeReduite)):
        # `ListeReduite` (#635) : une liste relâchée dont il ne reste que le
        # cardinal répond la même chose que la liste elle-même.
        return len(valeur) > 0
    return True


def compute_taux_remplissage(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Taux de remplissage de `parti`, `groupe`, `tags_thematiques`, `mandats`.

    Pour chaque champ : nombre de profils où il est renseigné (ni absent,
    ni `null`, ni chaîne/liste vide), sur le total de profils. Sur une
    liste de profils vide, `taux_pct` vaut `0.0` (rien à mesurer).
    """
    total = len(profils)
    resultat: dict[str, Any] = {}

    for champ in CHAMPS_COMPLETUDE:
        renseignes = sum(1 for profil in profils if _est_renseigne(profil.get(champ)))
        resultat[champ] = {
            "renseignes": renseignes,
            "total": total,
            "taux_pct": round(100 * renseignes / total, 2) if total else 0.0,
        }

    return resultat


def compute_profils_sans_activite(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Profils sans aucun élément dans `votes`, `amendements` ou `interventions`.

    Ces profils sont des candidats à un enrichissement manquant. Un champ
    absent ou `null` compte comme "aucun élément", au même titre qu'une
    liste vide.
    """
    sans_activite = [
        profil
        for profil in profils
        if all(_taille_liste(profil, champ) == 0 for champ in CHAMPS_ACTIVITE)
    ]
    ids = [profil.get("id") for profil in sans_activite]

    return {
        "total_profils": len(profils),
        "nb_profils_sans_activite": len(ids),
        "profils_sans_activite": ids,
        # #630 — « 12 / 481 » ne dit pas si le trou est sur les 13 fiches
        # publiées ou sur les 468 membres de roster, et les deux appellent des
        # suites différentes : la première est une fiche vide en ligne, la
        # seconde un agrégat de groupe amputé de son numérateur.
        "ventilation_provenance": ventiler(sans_activite).as_dict(),
        "ventilation_provenance_total": ventiler(profils).as_dict(),
    }


def _est_candidat(profil: dict[str, Any]) -> bool:
    """Vrai si le profil est un candidat déclaré, faux pour un membre de roster.

    `meta.provenance` absente vaut `"candidat_declare"` (rétro-compatibilité,
    voir `compute_repartition_provenance`). Toute autre valeur — `"roster_groupe"`,
    `"roster_gouvernement"` (#996) comme une provenance inconnue — désigne un
    profil collecté via un roster, qui n'est pas un candidat déclaré.
    """
    meta = profil.get("meta")
    provenance = meta.get("provenance") if isinstance(meta, dict) else None
    return provenance is None or provenance == "candidat_declare"


def _cle_groupe(profil: dict[str, Any]) -> str:
    """Clé de regroupement des profils non candidats : `groupe` ou `"null"` si absent."""
    groupe = profil.get("groupe")
    return groupe if isinstance(groupe, str) and groupe.strip() else "null"


def compute_tableau_croise_candidats(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Tableau croisé du volume d'entrées par candidat et par type d'activité.

    Le détail ligne à ligne est réservé aux **candidats déclarés**
    (`_est_candidat`) : c'est le périmètre éditorial du produit. Les profils
    issus d'un roster (`meta.provenance` dans `PROVENANCES_ROSTER`) sont
    présents pour alimenter un agrégat, pas pour un affichage individuel ;
    ils ne sont donc restitués qu'agrégés par groupe (min/max/médiane/moyenne),
    jamais membre par membre.

    Un champ absent ou `null` compte pour 0 élément.

    Returns:
        `{"lignes": [{"id":..., "nom":..., "chambres": [...], "votes": int,
        "textes_portes": int, "amendements": int, "interventions": int}, ...],
        "non_candidats": {"total_profils": int, "par_groupe": [{"groupe":...,
        "nb_profils": int, <champ>: {"min","max","mediane","moyenne"}}, ...],
        "ensemble": {<champ>: {...}}}}`. `lignes` est triée par `nom` puis
        `id`, `par_groupe` par nom de groupe (ordre déterministe).
    """
    candidats = [profil for profil in profils if _est_candidat(profil)]
    non_candidats = [profil for profil in profils if not _est_candidat(profil)]

    lignes = [
        {
            "id": profil.get("id"),
            "nom": profil.get("nom"),
            "chambres": lire_chambres(profil),   # #494 — liste, plus le scalaire
            **{champ: _taille_liste(profil, champ) for champ in CHAMPS_LISTES_VOLUMETRIE},
        }
        for profil in candidats
    ]
    lignes.sort(key=lambda ligne: (ligne["nom"] or "", ligne["id"] or ""))

    par_groupe: dict[str, list[dict[str, Any]]] = {}
    for profil in non_candidats:
        par_groupe.setdefault(_cle_groupe(profil), []).append(profil)

    lignes_groupes = [
        {
            "groupe": groupe,
            "nb_profils": len(membres),
            **{
                champ: _stats_volumes([_taille_liste(membre, champ) for membre in membres])
                for champ in CHAMPS_LISTES_VOLUMETRIE
            },
        }
        for groupe, membres in sorted(par_groupe.items())
    ]

    return {
        "lignes": lignes,
        "non_candidats": {
            "total_profils": len(non_candidats),
            "par_groupe": lignes_groupes,
            "ensemble": {
                champ: _stats_volumes(
                    [_taille_liste(profil, champ) for profil in non_candidats]
                )
                for champ in CHAMPS_LISTES_VOLUMETRIE
            },
        },
    }


def _parse_date_seule(valeur: Any) -> date | None:
    """Parse une date ISO-8601 (date seule ou horodatage), `None` si absente/invalide.

    Accepte aussi bien `"2024-06-12"` qu'un horodatage complet (dont on ne
    garde que la partie date) — mêmes tolérances que `_parse_synchro_le`
    (suffixe `Z` accepté comme UTC), jamais d'exception levée ici.
    """
    if not isinstance(valeur, str) or not valeur:
        return None

    texte = valeur[:-1] + "+00:00" if valeur.endswith("Z") else valeur
    try:
        return datetime.fromisoformat(texte).date()
    except ValueError:
        return None


def _date_entree(
    entree: dict[str, Any], champ: str, scrutins_index: Any = None,
    amendements_index: Any = None,
) -> Any:
    """Date d'une entrée de liste, `None` si elle n'en a pas.

    Depuis #432 un vote ne porte plus sa date, et depuis #431 un amendement non
    plus : c'est un champ de l'entité partagée, qui vit dans son index. Sans
    cette résolution, la plage de dates tomberait silencieusement à `null` pour
    tous les profils — et c'est précisément elle qui avait montré que le corpus
    s'arrêtait en juin 2024 ([[votes-multi-legislature]]). Un audit qui perd sa
    mesure sans le dire est pire que pas d'audit.

    Repli sur l'enregistrement non résolu (`scrutin_non_resolu`,
    `amendement_non_resolu`) pour les entrées qu'aucun identifiant ne rattache :
    leur enregistrement complet y est conservé. Repli supplémentaire sur
    l'entrée elle-même pour les profils d'avant la normalisation, qui portaient
    encore leur date.
    """
    if champ == "votes":
        scrutin = None
        if scrutins_index is not None:
            scrutin = scrutins_index.get(entree.get("scrutin_id"))
        if scrutin is None:
            scrutin = entree.get("scrutin_non_resolu") or {}
        return scrutin.get("date")
    if champ == "amendements":
        amendement = None
        if amendements_index is not None:
            amendement = amendements_index.get(entree.get("amendement_id"))
        if amendement is None:
            amendement = entree.get("amendement_non_resolu") or entree
        return amendement.get("date")
    return entree.get("date")


def _plage_dates_champ_simple(
    profil: dict[str, Any], champ: str, dates_ignorees: dict[str, int],
    scrutins_index: Any = None, amendements_index: Any = None,
) -> dict[str, str | None]:
    """Min/max de la date de chaque entrée, en ignorant les dates invalides.

    Chaque valeur présente mais non parseable incrémente
    `dates_ignorees[champ]` (traçabilité, AGENTS.md §2.5) sans jamais faire
    échouer le calcul.
    """
    entrees = profil.get(champ)
    if isinstance(entrees, ListeReduite):
        # La liste a été relâchée au chargement (#635) : sa plage a été calculée
        # par cette fonction même, sur les entrées, avant qu'elles ne meurent.
        dates_ignorees[champ] += entrees.dates_ignorees
        return {"min": entrees.date_min, "max": entrees.date_max}

    dates: list[date] = []

    if isinstance(entrees, list):
        for entree in entrees:
            if not isinstance(entree, dict):
                continue
            valeur = _date_entree(entree, champ, scrutins_index, amendements_index)
            if valeur is None:
                continue
            date_parsee = _parse_date_seule(valeur)
            if date_parsee is not None:
                dates.append(date_parsee)
            else:
                dates_ignorees[champ] += 1

    return {
        "min": min(dates).isoformat() if dates else None,
        "max": max(dates).isoformat() if dates else None,
    }


def _plage_dates_textes_portes(
    profil: dict[str, Any], dates_ignorees: dict[str, int]
) -> dict[str, str | None]:
    """Min de `date_min` / max de `date_max` sur toutes les entrées de `textes_portes`.

    `textes_portes[]` porte `date_min`/`date_max` par entrée (pas un champ
    `date` unique, voir `schema_pivot.py`) : la cellule agrège séparément le
    plus petit `date_min` et le plus grand `date_max` du corpus. Dates
    invalides ignorées et comptabilisées dans `dates_ignorees["textes_portes"]`.
    """
    entrees = profil.get("textes_portes")
    if isinstance(entrees, ListeReduite):
        dates_ignorees["textes_portes"] += entrees.dates_ignorees
        return {"min": entrees.date_min, "max": entrees.date_max}

    dates_min: list[date] = []
    dates_max: list[date] = []

    if isinstance(entrees, list):
        for entree in entrees:
            if not isinstance(entree, dict):
                continue

            valeur_min = entree.get("date_min")
            if valeur_min is not None:
                date_min_parsee = _parse_date_seule(valeur_min)
                if date_min_parsee is not None:
                    dates_min.append(date_min_parsee)
                else:
                    dates_ignorees["textes_portes"] += 1

            valeur_max = entree.get("date_max")
            if valeur_max is not None:
                date_max_parsee = _parse_date_seule(valeur_max)
                if date_max_parsee is not None:
                    dates_max.append(date_max_parsee)
                else:
                    dates_ignorees["textes_portes"] += 1

    return {
        "min": min(dates_min).isoformat() if dates_min else None,
        "max": max(dates_max).isoformat() if dates_max else None,
    }


def _fusionne_plages(plages: list[dict[str, str | None]]) -> dict[str, str | None]:
    """Plage englobante d'une liste de cellules `{"min":..., "max":...}`.

    `min` = plus petite borne basse non nulle, `max` = plus grande borne
    haute non nulle ; `null` si aucune borne exploitable (jamais de date par
    défaut, AGENTS.md §2.5).
    """
    debuts = [plage["min"] for plage in plages if plage["min"] is not None]
    fins = [plage["max"] for plage in plages if plage["max"] is not None]

    return {
        "min": min(debuts) if debuts else None,
        "max": max(fins) if fins else None,
    }


def compute_plage_dates_candidats(
    profils: list[dict[str, Any]], scrutins_index: Any = None,
    amendements_index: Any = None,
) -> dict[str, Any]:
    """Plage temporelle par candidat et par type d'activité.

    Symétrique de `compute_tableau_croise_candidats` (volumes) : détail ligne
    à ligne pour les **candidats déclarés** uniquement, et agrégat par groupe
    pour les profils issus des rosters (`_est_candidat`), jamais membre par
    membre.

    Chaque cellule est un `{"min": ..., "max": ...}` de dates ISO-8601, `null`
    si la liste est vide ou sans aucune date exploitable — jamais de date par
    défaut (AGENTS.md §2.5). `votes`/`amendements`/`interventions` utilisent le
    champ `date` de chaque entrée ; `textes_portes` agrège `date_min`/`date_max`
    (voir `_plage_dates_textes_portes`). L'agrégat non candidats fusionne les
    plages des membres d'un même groupe (plus petit `min`, plus grand `max`).

    Returns:
        `{"lignes": [{"id":..., "nom":..., "chambres": [...], <champ>: {"min","max"}},
        ...], "non_candidats": {"total_profils": int, "par_groupe":
        [{"groupe":..., "nb_profils": int, <champ>: {"min","max"}}, ...],
        "ensemble": {<champ>: {"min","max"}}}, "dates_ignorees": {champ: int}}`.
        `dates_ignorees` compte, par champ et sur l'ensemble des profils, les
        dates présentes mais non parseables : ignorées du calcul, jamais
        masquées sans indicateur.
    """
    dates_ignorees = {champ: 0 for champ in CHAMPS_LISTES_VOLUMETRIE}

    def plages_profil(profil: dict[str, Any]) -> dict[str, dict[str, str | None]]:
        return {
            champ: (
                _plage_dates_textes_portes(profil, dates_ignorees)
                if champ == "textes_portes"
                else _plage_dates_champ_simple(
                    profil, champ, dates_ignorees, scrutins_index, amendements_index
                )
            )
            for champ in CHAMPS_LISTES_VOLUMETRIE
        }

    lignes = []
    plages_non_candidats: list[tuple[str, dict[str, dict[str, str | None]]]] = []

    for profil in profils:
        plages = plages_profil(profil)
        if _est_candidat(profil):
            lignes.append({
                "id": profil.get("id"),
                "nom": profil.get("nom"),
                "chambres": lire_chambres(profil),   # #494 — liste, plus le scalaire
                **plages,
            })
        else:
            plages_non_candidats.append((_cle_groupe(profil), plages))

    lignes.sort(key=lambda ligne: (ligne["nom"] or "", ligne["id"] or ""))

    par_groupe: dict[str, list[dict[str, dict[str, str | None]]]] = {}
    for groupe, plages in plages_non_candidats:
        par_groupe.setdefault(groupe, []).append(plages)

    lignes_groupes = [
        {
            "groupe": groupe,
            "nb_profils": len(membres),
            **{
                champ: _fusionne_plages([plages[champ] for plages in membres])
                for champ in CHAMPS_LISTES_VOLUMETRIE
            },
        }
        for groupe, membres in sorted(par_groupe.items())
    ]

    return {
        "lignes": lignes,
        "non_candidats": {
            "total_profils": len(plages_non_candidats),
            "par_groupe": lignes_groupes,
            "ensemble": {
                champ: _fusionne_plages(
                    [plages[champ] for _, plages in plages_non_candidats]
                )
                for champ in CHAMPS_LISTES_VOLUMETRIE
            },
        },
        "dates_ignorees": dates_ignorees,
    }


def compute_presence_meta(profils: list[dict[str, Any]]) -> dict[str, Any]:
    """Présence et non-vacuité de `meta.licence_donnees` et `meta.genere_le`.

    Un `meta` absent ou de mauvais type compte comme un défaut pour les
    deux champs. Retourne la liste des `id` en défaut pour chaque critère,
    afin de cibler précisément les profils à corriger.
    """
    ids_meta_absente: list[Any] = []
    ids_licence_manquante: list[Any] = []
    ids_genere_le_manquant: list[Any] = []

    for profil in profils:
        identifiant = profil.get("id")
        meta = profil.get("meta")

        if not isinstance(meta, dict):
            ids_meta_absente.append(identifiant)
            ids_licence_manquante.append(identifiant)
            ids_genere_le_manquant.append(identifiant)
            continue

        if not _est_renseigne(meta.get("licence_donnees")):
            ids_licence_manquante.append(identifiant)

        if not _est_renseigne(meta.get("genere_le")):
            ids_genere_le_manquant.append(identifiant)

    return {
        "total_profils": len(profils),
        "meta_absente": ids_meta_absente,
        "licence_donnees_manquante": ids_licence_manquante,
        "genere_le_manquant": ids_genere_le_manquant,
    }


# ---------------------------------------------------------------------------
# Assemblage du rapport (sous-tâche 6/6)
# ---------------------------------------------------------------------------

def build_report(
    profils: list[dict[str, Any]],
    erreurs_lecture: list[dict[str, Any]],
    staleness_days: int = 30,
    reference_date: datetime | None = None,
    scrutins_index: Any = None,
    amendements_index: Any = None,
) -> dict[str, Any]:
    """Assemble tous les indicateurs `compute_*` en un rapport structuré unique.

    Args:
        profils: profils pivot valides (sortie de `load_pivot_directory`).
        erreurs_lecture: erreurs de lecture (sortie de `load_pivot_directory`).
        staleness_days: seuil d'ancienneté en jours pour `compute_profils_perimes`
            (défaut : 30).
        reference_date: date de référence injectable pour les indicateurs de
            fraîcheur, voir `compute_fraicheur_sources` (défaut :
            `datetime.now(timezone.utc)`).

    Returns:
        Dict sérialisable JSON, une section par catégorie d'indicateur
        (`volumetrie`, `completude`, `coherence`, `fraicheur`, `warnings`,
        `tableau_croise_candidats`, `plage_dates_candidats`) plus `meta` et
        `erreurs_lecture`. Un outil de qualité interne : ce rapport ne doit
        jamais introduire de jugement de valeur, de score ou de classement
        (AGENTS.md §2.1).
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    return {
        "meta": {
            "genere_le": reference.isoformat(),
            "total_profils": len(profils),
            "ventilation_provenance": ventiler(profils).as_dict(),
            "total_erreurs_lecture": len(erreurs_lecture),
            "staleness_days": staleness_days,
        },
        "volumetrie": {
            "repartition_chambre": compute_repartition_chambre(profils),
            "repartition_provenance": compute_repartition_provenance(profils),
        },
        "completude": {
            "taux_remplissage": compute_taux_remplissage(profils),
            "profils_sans_activite": compute_profils_sans_activite(profils),
            "presence_meta": compute_presence_meta(profils),
        },
        "coherence": {
            "doublons_id": compute_doublons_id(profils),
            "coherence_schema_version": compute_coherence_schema_version(profils),
            "validite_dates": compute_validite_dates(profils),
            "coherence_chambre_sources": compute_coherence_chambre_sources(profils),
        },
        "fraicheur": {
            "fraicheur_sources": compute_fraicheur_sources(profils, reference_date=reference),
            "profils_perimes": compute_profils_perimes(
                profils, staleness_days=staleness_days, reference_date=reference
            ),
        },
        "warnings": compute_agregation_warnings(profils),
        "tableau_croise_candidats": compute_tableau_croise_candidats(profils),
        "plage_dates_candidats": compute_plage_dates_candidats(
            profils, scrutins_index, amendements_index
        ),
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
    par_chambre = volumetrie["repartition_chambre"]["par_chambre"]
    lignes_chambre = [[chambre, effectif] for chambre, effectif in par_chambre.items()]

    par_provenance = volumetrie["repartition_provenance"]["par_provenance"]
    lignes_provenance = [[provenance, effectif] for provenance, effectif in par_provenance.items()]
    # #630 — la table de provenance existait déjà, mais deux sections plus bas
    # que le total. Le total la porte désormais lui-même.
    ventilation = Ventilation(
        candidats_declares=par_provenance.get("candidat_declare", 0),
        membres_roster=par_provenance.get("roster_groupe", 0),
        membres_gouvernement=par_provenance.get("roster_gouvernement", 0),
        provenance_autre=par_provenance.get("null", 0),
    )

    repartition = volumetrie["repartition_chambre"]
    # #494 — la répartition n'est plus une partition : un profil bicaméral est
    # compté dans chacune de ses chambres. Le total des attributions est donc
    # affiché à côté du nombre de profils, jamais à sa place (§2.7).
    return (
        "## Volumétrie\n\n"
        f"Total profils : {ventilation.cellule_markdown()}\n\n"
        "### Répartition par chambre\n\n"
        "Un profil est compté dans **chacune** des chambres où il a siégé "
        f"(`chambres`, #493) : {repartition['total_attributions']} attributions "
        f"pour {repartition['total_profils']} profils.\n\n"
        + _md_table(["Chambre", "Profils"], lignes_chambre, "Aucun profil.")
        + "\n### Répartition par provenance (`meta.provenance`)\n\n"
        + _md_table(["Provenance", "Profils"], lignes_provenance, "Aucun profil.")
    )


def _md_section_completude(completude: dict[str, Any]) -> str:
    lignes_remplissage = [
        [champ, stats["renseignes"], stats["total"], stats["taux_pct"]]
        for champ, stats in completude["taux_remplissage"].items()
    ]

    sans_activite = completude["profils_sans_activite"]
    presence_meta = completude["presence_meta"]
    lignes_presence_meta = [
        ["meta absente", len(presence_meta["meta_absente"])],
        ["licence_donnees manquante", len(presence_meta["licence_donnees_manquante"])],
        ["genere_le manquant", len(presence_meta["genere_le_manquant"])],
    ]

    return (
        "## Complétude\n\n"
        "### Taux de remplissage\n\n"
        + _md_table(
            ["Champ", "Renseignés", "Total", "Taux (%)"],
            lignes_remplissage, "Aucun profil.",
        )
        + "\n### Profils sans activité (aucun vote, amendement ni intervention)\n\n"
        f"{Ventilation.depuis_dict(sans_activite.get('ventilation_provenance')).cellule_markdown()}"
        " sur "
        f"{Ventilation.depuis_dict(sans_activite.get('ventilation_provenance_total')).cellule_markdown()}"
        " profil(s).\n\n"
        "### Présence des métadonnées\n\n"
        + _md_table(
            ["Critère", f"Profils en défaut (sur {presence_meta['total_profils']})"],
            lignes_presence_meta, "Aucun profil.",
        )
    )


def _md_section_coherence(coherence: dict[str, Any]) -> str:
    lignes_doublons = [
        [d["id"], d["occurrences"]] for d in coherence["doublons_id"]["doublons"]
    ]
    lignes_schema = [
        [p["id"], p["schema_version"], p["meta_schema_version"]]
        for p in coherence["coherence_schema_version"]["profils_incoherents"]
    ]
    # #726 — `non_renseigne` est AGRÉGÉ, les anomalies sont ÉNUMÉRÉES. 464 lignes
    # identiques disant « cette source retirée du pipeline n'a pas de date » ne
    # sont pas de l'information : elles enterrent la ligne qui en serait une. Le
    # compte par champ, lui, se lit — et il reste visible, ce qui est la
    # différence avec le fait de ne rien afficher du tout (§2 règle 5).
    dates_en_defaut = coherence["validite_dates"]["dates_invalides"]
    lignes_dates = [
        [d["id"], d["champ"], d["valeur"], d["erreur"]]
        for d in dates_en_defaut if d["erreur"] != "non_renseigne"
    ]
    non_renseignees: dict[str, int] = {}
    for d in dates_en_defaut:
        if d["erreur"] != "non_renseigne":
            continue
        # `sources[3].synchro_le` -> `sources[].synchro_le` : l'indice désigne
        # une position dans une liste, pas un champ distinct.
        champ = re.sub(r"\[\d+\]", "[]", d["champ"])
        non_renseignees[champ] = non_renseignees.get(champ, 0) + 1
    lignes_non_renseignees = [[champ, n] for champ, n in sorted(non_renseignees.items())]
    lignes_chambre_sources = [
        [
            p["id"],
            libelle_chambres(p["chambres"]),
            libelle_chambres(p["chambres_sans_source"], vide="—"),
            ", ".join(t or "null" for t in p["types_sources"]) or "—",
        ]
        for p in coherence["coherence_chambre_sources"]["profils_incoherents"]
    ]

    return (
        "## Cohérence\n\n"
        "### Doublons d'`id`\n\n"
        + _md_table(["id", "Occurrences"], lignes_doublons, "Aucun doublon détecté.")
        + "\n### Divergence `schema_version` / `meta.schema_version`\n\n"
        + _md_table(
            ["id", "schema_version", "meta.schema_version"],
            lignes_schema, "Aucune divergence détectée.",
        )
        + "\n### Dates de traçabilité invalides ou futures\n\n"
        + _md_table(["id", "Champ", "Valeur", "Erreur"], lignes_dates, "Aucune date invalide détectée.")
        + "\n### Dates de traçabilité non renseignées\n\n"
        + "> Un champ vide n'est pas un champ fautif (#726) : depuis #529 les entrées "
        "`sources[].type == \"nosdeputes\"` sont conservées sans être recollectées, la clause "
        "ODbL en dépendant (`AGENTS.md` §7), et plus rien ne peut les dater. Compté par champ "
        "plutôt qu'énuméré profil par profil — la liste ne dirait rien de plus et cacherait "
        "les anomalies ci-dessus.\n\n"
        + _md_table(
            ["Champ", "Profils concernés"], lignes_non_renseignees,
            "Aucune date de traçabilité non renseignée.",
        )
        + "\n### Cohérence `chambres` / types de `sources[]`\n\n"
        + _md_table(
            ["id", "Chambres", "Sans source attendue", "Types de sources déclarés"],
            lignes_chambre_sources, "Aucune incohérence détectée.",
        )
    )


def _md_section_fraicheur(fraicheur: dict[str, Any], staleness_days: int) -> str:
    lignes_fraicheur = [
        [
            type_source, stats["nombre_sources"],
            stats["min_jours"], stats["max_jours"], stats["mediane_jours"], stats["moyenne_jours"],
        ]
        for type_source, stats in fraicheur["fraicheur_sources"]["par_type_source"].items()
    ]

    profils_perimes = fraicheur["profils_perimes"]
    lignes_perimes = [[id_] for id_ in profils_perimes]

    return (
        "## Fraîcheur\n\n"
        "### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)\n\n"
        + _md_table(
            ["Type de source", "Nombre de sources", "Min", "Max", "Médiane", "Moyenne"],
            lignes_fraicheur, "Aucune source datée.",
        )
        + f"\n### Profils périmés (toutes sources > {staleness_days} jours)\n\n"
        + _md_table(["id"], lignes_perimes, "Aucun profil périmé.")
    )


def _md_section_tableau_croise_candidats(tableau: dict[str, Any]) -> str:
    lignes = [
        [
            ligne["id"], ligne["nom"], libelle_chambres(ligne["chambres"]),
            ligne["votes"], ligne["textes_portes"], ligne["amendements"], ligne["interventions"],
        ]
        for ligne in tableau["lignes"]
    ]

    non_candidats = tableau["non_candidats"]
    lignes_non_candidats = [
        [
            ligne["groupe"], ligne["nb_profils"], champ,
            ligne[champ]["min"], ligne[champ]["max"],
            ligne[champ]["mediane"], ligne[champ]["moyenne"],
        ]
        for ligne in non_candidats["par_groupe"]
        for champ in CHAMPS_LISTES_VOLUMETRIE
    ] + [
        [
            "Ensemble", non_candidats["total_profils"], champ,
            stats["min"], stats["max"], stats["mediane"], stats["moyenne"],
        ]
        for champ, stats in non_candidats["ensemble"].items()
    ]

    return (
        "## Tableau croisé des volumes par candidat\n\n"
        "Candidats déclarés uniquement (`meta.provenance` = `candidat_declare`).\n\n"
        + _md_table(
            ["id", "Nom", "Chambres", "Votes", "Textes portés", "Amendements", "Interventions"],
            lignes, "Aucun profil.",
        )
        + "\n### Membres de groupe non candidats (agrégé par groupe)\n\n"
        f"{non_candidats['total_profils']} profil(s) issus des rosters de groupes "
        "(`meta.provenance` = `roster_groupe`) : volumes agrégés, sans détail par membre.\n\n"
        + _md_table(
            ["Groupe", "Profils", "Champ", "Min", "Max", "Médiane", "Moyenne"],
            lignes_non_candidats, "Aucun profil non candidat.",
        )
    )


def _md_format_plage(plage: dict[str, str | None]) -> str:
    """Formatte une cellule `{"min":..., "max":...}` en `"min → max"`, `"—"` si les deux sont `null`."""
    debut = plage["min"] if plage["min"] is not None else "—"
    fin = plage["max"] if plage["max"] is not None else "—"
    return "—" if debut == "—" and fin == "—" else f"{debut} → {fin}"


def _md_section_plage_dates_candidats(plage_dates: dict[str, Any]) -> str:
    lignes = [
        [
            ligne["id"], ligne["nom"], libelle_chambres(ligne["chambres"]),
            _md_format_plage(ligne["votes"]), _md_format_plage(ligne["textes_portes"]),
            _md_format_plage(ligne["amendements"]), _md_format_plage(ligne["interventions"]),
        ]
        for ligne in plage_dates["lignes"]
    ]

    non_candidats = plage_dates["non_candidats"]
    lignes_non_candidats = [
        [
            ligne["groupe"], ligne["nb_profils"],
            _md_format_plage(ligne["votes"]), _md_format_plage(ligne["textes_portes"]),
            _md_format_plage(ligne["amendements"]), _md_format_plage(ligne["interventions"]),
        ]
        for ligne in non_candidats["par_groupe"]
    ] + [
        [
            "Ensemble", non_candidats["total_profils"],
            _md_format_plage(non_candidats["ensemble"]["votes"]),
            _md_format_plage(non_candidats["ensemble"]["textes_portes"]),
            _md_format_plage(non_candidats["ensemble"]["amendements"]),
            _md_format_plage(non_candidats["ensemble"]["interventions"]),
        ]
    ]

    lignes_ignorees = [
        [champ, nombre] for champ, nombre in plage_dates["dates_ignorees"].items() if nombre > 0
    ]

    return (
        "## Plages temporelles par candidat\n\n"
        "Candidats déclarés uniquement (`meta.provenance` = `candidat_declare`).\n\n"
        + _md_table(
            ["id", "Nom", "Chambres", "Votes", "Textes portés", "Amendements", "Interventions"],
            lignes, "Aucun profil.",
        )
        + "\n### Membres de groupe non candidats (agrégé par groupe)\n\n"
        f"{non_candidats['total_profils']} profil(s) issus des rosters de groupes "
        "(`meta.provenance` = `roster_groupe`) : plage englobante du groupe, "
        "sans détail par membre.\n\n"
        + _md_table(
            ["Groupe", "Profils", "Votes", "Textes portés", "Amendements", "Interventions"],
            lignes_non_candidats, "Aucun profil non candidat.",
        )
        + "\n### Dates ignorées (invalides ou non parseables)\n\n"
        + _md_table(["Champ", "Dates ignorées"], lignes_ignorees, "Aucune date ignorée.")
    )


def _md_section_warnings(warnings: dict[str, Any]) -> str:
    lignes = [
        [type_warning, entree["frequence"], ", ".join(entree["ids"])]
        for type_warning, entree in warnings["par_type"].items()
    ]

    return (
        "## Warnings\n\n"
        f"Total : {warnings['total_warnings']}\n\n"
        + _md_table(["Type", "Fréquence", "Profils concernés"], lignes, "Aucun warning.")
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

    sections = [
        (
            "# Rapport d'audit du jeu de données pivot\n\n"
            f"Généré le {meta['genere_le']}. "
            f"{Ventilation.depuis_dict(meta.get('ventilation_provenance')).cellule_markdown()}"
            " profil(s) analysé(s), "
            f"{meta['total_erreurs_lecture']} erreur(s) de lecture. "
            f"Seuil de péremption des sources : {meta['staleness_days']} jour(s).\n\n"
            "Ce rapport est un outil de qualité interne : il présente des "
            "indicateurs bruts, sans jugement de valeur ni classement.\n"
        ),
        _md_section_volumetrie(rapport["volumetrie"]),
        _md_section_tableau_croise_candidats(rapport["tableau_croise_candidats"]),
        _md_section_plage_dates_candidats(rapport["plage_dates_candidats"]),
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
        prog="audit_pivot_dataset.py",
        description=(
            "Audite un jeu de données pivot : volumétrie, complétude, cohérence, "
            "fraîcheur des sources et warnings agrégés. Outil de qualité interne, "
            "ne produit aucun score ni classement."
        ),
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        metavar="DOSSIER",
        help="Dossier contenant les fichiers *.pivot.json à auditer (scan récursif).",
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
            "(audit_pivot_<horodatage-UTC>.json/.md) au lieu de nommer chaque "
            "fichier — incompatible avec --output-json/--output-md."
        ),
    )
    parser.add_argument(
        "--staleness-days",
        type=int,
        default=30,
        metavar="JOURS",
        help="Seuil d'ancienneté (jours) au-delà duquel un profil est périmé (défaut : 30).",
    )
    parser.add_argument(
        "--scrutins",
        default=str(DEFAULT_SCRUTINS_PATH),
        metavar="FICHIER",
        help=(
            f"Index partagé des scrutins (#432, défaut : {DEFAULT_SCRUTINS_PATH}). "
            "Un vote ne porte plus sa date : sans l'index, la plage de dates des "
            "votes ne peut pas être calculée."
        ),
    )
    parser.add_argument(
        "--amendements",
        default=str(DEFAULT_AMENDEMENTS_DIR),
        metavar="DOSSIER",
        help=(
            f"Index partagé des amendements (#431, défaut : {DEFAULT_AMENDEMENTS_DIR}). "
            "Un amendement ne porte plus sa date dans le profil : sans l'index, la "
            "plage de dates des amendements ne peut pas être calculée."
        ),
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
        output_json_path = str(Path(args.output_dir) / f"audit_pivot_{horodatage}.json")
        output_md_path = str(Path(args.output_dir) / f"audit_pivot_{horodatage}.md")

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"[!] Dossier introuvable : {input_dir}", file=sys.stderr)
        return 1

    # Les index sont chargés AVANT le corpus depuis #635 : c'est eux qui datent
    # un vote et un amendement, et la lecture du corpus réduit chaque liste à sa
    # plage de dates au lieu d'en garder les entrées. Les mêmes index sont
    # ensuite passés à `build_report` — les passer ici et pas là (ou l'inverse)
    # ferait diverger le rapport de ce que les listes entières auraient donné.
    #
    # Index des scrutins (#432) : sans lui, la plage de dates des votes
    # tomberait à `null` partout, silencieusement — un audit qui perd une mesure
    # sans le dire est pire que pas d'audit.
    scrutins_index = charger_scrutins(Path(args.scrutins))
    if len(scrutins_index) == 0:
        # sur stderr : sans --output-json, ce script écrit le rapport JSON sur
        # STDOUT, et un avertissement s'y mêlant le rendrait illisible.
        print(f"  [!] Index des scrutins vide ou absent ({args.scrutins}) : "
              "la plage de dates des votes ne sera pas calculée (#432).",
              file=sys.stderr)
    # Index des amendements (#431), même raison. `avec_cosignatures=False` :
    # l'audit ne lit que des dates, et les cosignatures pèsent 59 % de l'index.
    amendements_index = charger_amendements(
        Path(args.amendements), avec_cosignatures=False
    )
    if len(amendements_index) == 0:
        print(f"  [!] Index des amendements vide ou absent ({args.amendements}) : "
              "la plage de dates des amendements ne sera calculée que sur les entrées "
              "portant encore leur enregistrement (#431).",
              file=sys.stderr)

    profils, erreurs_lecture = load_pivot_directory(
        input_dir, scrutins_index, amendements_index)
    # La ligne lue avant toute mesure : elle porte la ventilation, sans quoi
    # « 481 » repart seul dans le rapport de qui la lit (#630).
    print(
        f"→ {len(profils)} profil(s) chargé(s) "
        f"{ventiler(profils).detail()}, "
        f"{len(erreurs_lecture)} erreur(s) de lecture.",
        file=sys.stderr,
    )

    rapport = build_report(
        profils, erreurs_lecture, staleness_days=args.staleness_days,
        scrutins_index=scrutins_index,
        amendements_index=amendements_index,
    )
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
