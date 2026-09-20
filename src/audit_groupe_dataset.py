#!/usr/bin/env python3
"""
audit_groupe_dataset.py — Audit du jeu de données groupes (pivot_data/groupes).

Miroir de `audit_pivot_dataset.py` (issue #137) pour les profils de groupe
agrégés (`schema_groupe.py`), voir issue #176 (plan #174). Couche de
chargement (`load_groupe_directory`) volontairement séparée de la logique de
calcul des indicateurs, pour rester testable indépendamment : un fichier
JSON malformé ne doit jamais interrompre le scan du répertoire.

Indicateurs sous forme de fonctions pures (liste de profils de groupe ->
dict sérialisable JSON), sans aucune I/O :
  - volumétrie : effectifs, nombre de `cohesion_votes`, distribution des
    `amendements_agreges` (global + `par_type_deposant`) ;
  - complétude : présence de `tags_thematiques_agreges`, groupes avec des
    membres mais 0 `cohesion_votes` ;
  - cohérence : validation `schema_groupe.validate_profil_groupe`, divergence
    `schema_version`/`meta.schema_version`, écart
    `couverture_roster.profils_disponibles`/`roster_total`, doublons de
    `groupe_id` ;
  - fraîcheur : ancienneté de `sources[].synchro_le`, groupes périmés
    (`compute_groupes_perimes`, seuil `staleness_days` injectable) ;
  - agrégation des `meta.warnings[]` par fichier ;
  - tableau croisé par groupe (`compute_tableau_croise_groupes`) : une ligne
    par groupe avec le nombre de `membres`, `cohesion_votes`,
    `tags_thematiques_agreges` et `amendements_agreges.nb_amendements`
    (bloc global), sur le même principe que
    `audit_pivot_dataset.compute_tableau_croise_candidats` (issue #174) ;
  - tableau croisé des plages temporelles par groupe
    (`compute_plage_dates_groupes`, issue #318, sous-issue 2/6 de #316) :
    symétrique du tableau ci-dessus, min/max de `cohesion_votes[].date` par
    groupe. `amendements_agreges` n'a pas de cellule calculée (aucune date
    au niveau de l'agrégat dans `schema_groupe.py`, voir #316 Hors
    périmètre).

`build_report()` assemble tous ces indicateurs en un rapport structuré
unique, et `generate_markdown_report()` en dérive un rendu Markdown lisible
par un humain, sur le même modèle que `audit_pivot_dataset.py` (issue #177,
plan #174). La CLI (`main()` / `_build_arg_parser()`) partage le même
contrat d'options — un `id` manquant, une donnée absente ou vide n'est
jamais comptée comme renseignée (AGENTS.md §2.5 : "missing data means
missing data, never default 0").

Aucune dépendance lourde : stdlib uniquement.
"""

import argparse
import json
import statistics
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from schema_groupe import (
    AMENDEMENTS_TYPES_DEPOSANT,
    valeur_borne_effectif,
    validate_profil_groupe,
)
# `charger` rend un `ScrutinsIndex` vide sur un fichier absent, jamais une
# exception : un index manquant est un trou déclaré par le rapport (#726), pas
# une panne de l'audit.
from scrutins_index import charger as charger_scrutins

# Sous-champs de `effectif` dont on mesure la distribution.
# `a_la_date_de_reference` remplace `actuel` (#653). Les deux sont lus : les 2
# fiches `groupe-Senat-*` gelées par #516 portent encore `actuel`, et un audit
# qui cesserait de les lire publierait « 2 groupes non renseignés » au lieu de
# leur valeur.
CHAMPS_EFFECTIF: tuple[str, ...] = (
    "a_la_date_de_reference", "actuel", "min_historique", "max_historique",
)

# Compteurs de `amendements_agreges` (bloc global et chaque bloc de
# `par_type_deposant`) dont on mesure la distribution.
CHAMPS_AMENDEMENTS: tuple[str, ...] = (
    "nb_amendements", "nb_adoptes", "nb_rejetes", "nb_irrecevables", "nb_retires_ou_tombes",
)


def load_groupe_directory(input_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Scanne récursivement `input_dir` à la recherche de fichiers `*.json`.

    Args:
        input_dir: répertoire racine à scanner (récursif).

    Returns:
        Tuple (groupes_valides, erreurs_lecture) :
          - groupes_valides : liste des profils de groupe chargés avec
            succès, triés par chemin de fichier pour un résultat
            déterministe.
          - erreurs_lecture : liste de {"fichier": str, "erreur": str} pour
            chaque fichier n'ayant pas pu être chargé (JSON invalide, objet
            racine non-dict, erreur de lecture...). Un fichier problématique
            n'interrompt jamais le scan des suivants.
    """
    groupes_valides: list[dict[str, Any]] = []
    erreurs_lecture: list[dict[str, Any]] = []

    for path in sorted(input_dir.rglob("*.json")):
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

        groupes_valides.append(data)

    return groupes_valides, erreurs_lecture


def _taille_liste(groupe: dict[str, Any], champ: str) -> int:
    """Longueur de `groupe[champ]`, `0` si absent ou `null` (donnée manquante)."""
    valeur = groupe.get(champ)
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

def compute_effectifs(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribution de `effectif.a_la_date_de_reference`/`actuel`/`min_historique`/`max_historique`.

    Pour chaque sous-champ, min/max/médiane/moyenne sur les groupes où la
    valeur est un entier renseigné. Un `null` est exclu du calcul, jamais
    compté comme `0` (AGENTS.md §2.5) : `min_historique`/`max_historique`
    restent `null` sur toute fiche dont une entrée `membres[]` n'a pas de date
    d'appartenance (#702).

    Ces deux champs se lisent sous **deux formes** : l'objet `{valeur, date}`
    du lot #702, et l'entier nu hérité. `valeur_borne_effectif` rend l'entier
    des deux — un audit qui n'aurait suivi que la nouvelle forme publierait
    « 0 groupe renseigné » là où la donnée existe, sans que rien ne le dise.

    Returns:
        `{champ: {"nombre_groupes_renseignes": int, "min":..., "max":...,
        "mediane":..., "moyenne":...}}` pour chaque champ de
        `CHAMPS_EFFECTIF`.
    """
    resultat: dict[str, Any] = {}

    for champ in CHAMPS_EFFECTIF:
        valeurs = []
        for groupe in groupes:
            effectif = groupe.get("effectif")
            if not isinstance(effectif, dict):
                continue
            valeur = valeur_borne_effectif(effectif.get(champ))
            if valeur is not None:
                valeurs.append(valeur)

        resultat[champ] = {
            "nombre_groupes_renseignes": len(valeurs),
            **_stats_entiers(valeurs),
        }

    return resultat


def compute_nombre_cohesion_votes(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribution du nombre de `cohesion_votes` par groupe.

    Min, max, médiane, moyenne du nombre de scrutins recensés par groupe, et
    pourcentage de groupes sans aucun scrutin. Sur une liste de groupes
    vide, toutes les statistiques valent `null` sauf `pct_groupes_a_zero`
    qui vaut `0.0`.
    """
    tailles = [_taille_liste(groupe, "cohesion_votes") for groupe in groupes]

    if not tailles:
        return {"min": None, "max": None, "mediane": None, "moyenne": None, "pct_groupes_a_zero": 0.0}

    return {
        **_stats_entiers(tailles),
        "pct_groupes_a_zero": round(100 * sum(1 for taille in tailles if taille == 0) / len(tailles), 2),
    }


def _valeurs_champ_amendements(groupes: list[dict[str, Any]], champ: str, type_deposant: str | None) -> list[int]:
    """Valeurs entières de `champ` dans `amendements_agreges` (globales ou par type de déposant)."""
    valeurs = []
    for groupe in groupes:
        amendements = groupe.get("amendements_agreges")
        if not isinstance(amendements, dict):
            continue

        bloc = amendements
        if type_deposant is not None:
            par_type = amendements.get("par_type_deposant")
            bloc = par_type.get(type_deposant) if isinstance(par_type, dict) else None

        if not isinstance(bloc, dict):
            continue

        valeur = bloc.get(champ)
        if isinstance(valeur, int) and not isinstance(valeur, bool):
            valeurs.append(valeur)

    return valeurs


def compute_distribution_amendements(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Distribution des compteurs de `amendements_agreges`, global et par type de déposant.

    Pour chaque compteur de `CHAMPS_AMENDEMENTS` (`nb_amendements`,
    `nb_adoptes`, `nb_rejetes`, `nb_irrecevables`, `nb_retires_ou_tombes`) :
    min/max/médiane/moyenne sur l'ensemble des groupes, à la fois pour le
    bloc global et pour chaque type de déposant connu
    (`schema_groupe.AMENDEMENTS_TYPES_DEPOSANT`, incluant `"inconnu"`) —
    ne jamais agréger les taux d'adoption entre types de déposants
    (AGENTS.md §5 : `type_deposant`).

    Returns:
        `{"global": {champ: {...}}, "par_type_deposant": {type: {champ: {...}}}}`.
    """
    return {
        "global": {
            champ: _stats_entiers(_valeurs_champ_amendements(groupes, champ, None))
            for champ in CHAMPS_AMENDEMENTS
        },
        "par_type_deposant": {
            type_deposant: {
                champ: _stats_entiers(_valeurs_champ_amendements(groupes, champ, type_deposant))
                for champ in CHAMPS_AMENDEMENTS
            }
            for type_deposant in sorted(AMENDEMENTS_TYPES_DEPOSANT)
        },
    }


# ---------------------------------------------------------------------------
# Complétude
# ---------------------------------------------------------------------------

def compute_presence_tags_thematiques(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Taux de remplissage de `tags_thematiques_agreges`.

    Nombre de groupes où le champ est renseigné (ni absent, ni `null`, ni
    liste vide), sur le total de groupes. `taux_pct` vaut `0.0` sur une
    liste de groupes vide (rien à mesurer).
    """
    total = len(groupes)
    renseignes = sum(1 for groupe in groupes if _est_renseigne(groupe.get("tags_thematiques_agreges")))

    return {
        "renseignes": renseignes,
        "total": total,
        "taux_pct": round(100 * renseignes / total, 2) if total else 0.0,
    }


def compute_groupes_membres_sans_cohesion(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Groupes ayant au moins un membre mais aucun `cohesion_votes`.

    Ces groupes sont des candidats à un enrichissement manquant (agrégation
    de cohésion non calculée alors que des profils individuels sont
    disponibles).
    """
    ids = [
        groupe.get("groupe_id")
        for groupe in groupes
        if _taille_liste(groupe, "membres") > 0 and _taille_liste(groupe, "cohesion_votes") == 0
    ]

    return {
        "total_groupes": len(groupes),
        "nb_groupes_membres_sans_cohesion": len(ids),
        "groupes_membres_sans_cohesion": ids,
    }


def _nb_amendements_global(groupe: dict[str, Any]) -> int:
    """`amendements_agreges.nb_amendements` (bloc global), `0` si absent ou invalide."""
    amendements = groupe.get("amendements_agreges")
    if not isinstance(amendements, dict):
        return 0
    valeur = amendements.get("nb_amendements")
    return valeur if isinstance(valeur, int) and not isinstance(valeur, bool) else 0


def compute_tableau_croise_groupes(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Tableau croisé du volume d'entrées par groupe et par type d'activité agrégée.

    Une ligne par groupe : `groupe_id`, `groupe_nom`, `chambre`, et le nombre
    d'éléments dans `membres`, `cohesion_votes`, `tags_thematiques_agreges`,
    ainsi que `amendements_agreges.nb_amendements` (bloc global, tous types de
    déposants confondus — voir `compute_distribution_amendements` pour la
    ventilation par type de déposant). Un champ absent ou `null` compte pour
    0, comme dans `compute_nombre_cohesion_votes`.

    Returns:
        `{"lignes": [{"groupe_id":..., "groupe_nom":..., "chambre":...,
        "membres": int, "cohesion_votes": int, "tags_thematiques_agreges": int,
        "amendements": int}, ...]}`, trié par `groupe_nom` puis `groupe_id`
        (ordre déterministe en cas d'égalité ou de `groupe_nom` absent).
    """
    lignes = [
        {
            "groupe_id": groupe.get("groupe_id"),
            "groupe_nom": groupe.get("groupe_nom"),
            "chambre": groupe.get("chambre"),
            "membres": _taille_liste(groupe, "membres"),
            "cohesion_votes": _taille_liste(groupe, "cohesion_votes"),
            "tags_thematiques_agreges": _taille_liste(groupe, "tags_thematiques_agreges"),
            "amendements": _nb_amendements_global(groupe),
        }
        for groupe in groupes
    ]

    lignes.sort(key=lambda ligne: (ligne["groupe_nom"] or "", ligne["groupe_id"] or ""))

    return {"lignes": lignes}


def _parse_date_cohesion(valeur: Any) -> date | None:
    """Parse une date de scrutin (`"YYYY-MM-DD"`, sous-préfixe accepté), `None` si invalide."""
    if not isinstance(valeur, str) or not valeur:
        return None
    try:
        return date.fromisoformat(valeur[:10])
    except ValueError:
        return None


#: Pourquoi une entrée de `cohesion_votes` ne rend aucune date. Fermé, et chacun
#: compté séparément (#726) : « le scrutin n'est pas dans l'index » et « sa date
#: est illisible » ne se réparent pas au même endroit.
MOTIFS_DATE_NON_RESOLUE = frozenset({
    "scrutin_id_absent",   # l'entrée ne porte pas de référence de scrutin
    "scrutin_inconnu",     # la référence ne résout dans aucun scrutin de l'index
    "date_invalide",       # le scrutin existe, sa date n'est pas lisible
})


def _plage_cohesion_votes(
    groupe: dict[str, Any],
    scrutins_index: Any,
    non_resolues: dict[str, int],
) -> dict[str, str] | None:
    """Plage `{"min":..., "max":...}` des scrutins d'un groupe, `None` si aucune.

    **La date vient de l'index partagé, pas de l'entrée (#726).** `schema_groupe`
    le dit depuis #432 : `cohesion_votes[]` porte un `scrutin_id`, et « `date`,
    `texte` et `sort` vivent » dans `pivot_data/scrutins.json`. Cette fonction
    lisait `entree["date"]` — une clé qu'**aucune** des 61 596 entrées publiées ne
    porte, ce qui rendait ce tableau vide par construction et produisait 61 596
    lignes de « date invalide » qui noyaient le reste du rapport.

    `non_resolues` est muté en place : un compte par motif de
    `MOTIFS_DATE_NON_RESOLUE`, jamais une ligne par entrée — le volume est de
    l'ordre du corpus de scrutins, pas de celui d'une anomalie.
    """
    cohesion_votes = groupe.get("cohesion_votes")
    if not isinstance(cohesion_votes, list):
        return None

    dates_valides: list[date] = []

    for entree in cohesion_votes:
        scrutin_id = entree.get("scrutin_id") if isinstance(entree, dict) else None
        if not scrutin_id:
            non_resolues["scrutin_id_absent"] = non_resolues.get("scrutin_id_absent", 0) + 1
            continue
        scrutin = scrutins_index.get(scrutin_id) if scrutins_index is not None else None
        if scrutin is None:
            non_resolues["scrutin_inconnu"] = non_resolues.get("scrutin_inconnu", 0) + 1
            continue
        date_parsee = _parse_date_cohesion(scrutin.get("date"))
        if date_parsee is None:
            non_resolues["date_invalide"] = non_resolues.get("date_invalide", 0) + 1
            continue
        dates_valides.append(date_parsee)

    if not dates_valides:
        return None

    return {"min": min(dates_valides).isoformat(), "max": max(dates_valides).isoformat()}


def compute_plage_dates_groupes(
    groupes: list[dict[str, Any]], scrutins_index: Any = None
) -> dict[str, Any]:
    """Tableau croisé des plages temporelles par groupe, symétrique de `compute_tableau_croise_groupes`.

    Là où `compute_tableau_croise_groupes` répond à « combien d'entrées ? »,
    cette fonction répond à « sur quelle période ? » : une ligne par groupe,
    avec une cellule `{"min": "YYYY-MM-DD", "max": "YYYY-MM-DD"}` pour
    `cohesion_votes` (via `cohesion_votes[].date`).

    `amendements_agreges` vaut toujours `None` : `schema_groupe.py` ne
    stocke que des compteurs au niveau de l'agrégat, aucune date — une
    limite structurelle du schéma actuel, pas une donnée manquante à
    corriger (issue #316, section Hors périmètre). La cellule est
    documentée comme telle dans le rapport Markdown, jamais laissée vide
    sans explication.

    **La date est résolue par `scrutins_index`, pas lue dans l'entrée (#726).**
    `scrutin_id` est la seule clé que `cohesion_votes[]` porte depuis #432. Un
    index absent (`scrutins_index=None`) rend donc toutes les cellules `None` —
    et ce trou est **déclaré** par `index_disponible: False`, jamais présenté
    comme « ce groupe n'a pas de scrutin » (AGENTS.md §2 règle 5).

    Une entrée dont la date ne se résout pas est exclue du calcul min/max et
    **comptée par motif** (`MOTIFS_DATE_NON_RESOLUE`), jamais énumérée : elle se
    compte à l'échelle du corpus de scrutins — 61 596 entrées sur 12 fiches —,
    pas à celle d'une anomalie.

    Returns:
        `{"lignes": [{"groupe_id":..., "groupe_nom":..., "chambre":...,
        "cohesion_votes": {"min":..., "max":...} | None,
        "amendements_agreges": None}, ...], "index_disponible": bool,
        "dates_non_resolues": {motif: n, ...}}`. `lignes` trié par `groupe_nom`
        puis `groupe_id`, même ordre que `compute_tableau_croise_groupes`.
    """
    # Un index VIDE ne résout rien : le traiter comme disponible ferait passer
    # « le fichier était absent » pour « ces groupes n'ont pas de scrutin ».
    # `scrutins_index.charger()` rend un index vide sur un fichier absent, donc
    # le cas est atteignable par la CLI — c'est la règle de #510, un index qui ne
    # résout rien n'est jamais rendu en silence.
    if scrutins_index is not None and not len(scrutins_index):
        scrutins_index = None

    non_resolues: dict[str, int] = {}

    lignes = [
        {
            "groupe_id": groupe.get("groupe_id"),
            "groupe_nom": groupe.get("groupe_nom"),
            "chambre": groupe.get("chambre"),
            "cohesion_votes": _plage_cohesion_votes(groupe, scrutins_index, non_resolues),
            "amendements_agreges": None,
        }
        for groupe in groupes
    ]

    lignes.sort(key=lambda ligne: (ligne["groupe_nom"] or "", ligne["groupe_id"] or ""))
    return {
        "lignes": lignes,
        "index_disponible": scrutins_index is not None,
        "dates_non_resolues": dict(sorted(non_resolues.items())),
    }


# ---------------------------------------------------------------------------
# Cohérence
# ---------------------------------------------------------------------------

def compute_validation_schema(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Agrège les résultats de `schema_groupe.validate_profil_groupe` sur le corpus.

    Returns:
        `{"total_groupes": int, "nb_groupes_invalides": int,
        "groupes_invalides": [{"groupe_id":..., "erreurs": [str, ...]}, ...]}`,
        triés par `groupe_id` pour un résultat déterministe.
    """
    groupes_invalides = [
        {"groupe_id": groupe.get("groupe_id"), "erreurs": erreurs}
        for groupe in groupes
        for erreurs in [validate_profil_groupe(groupe)]
        if erreurs
    ]
    groupes_invalides.sort(key=lambda entree: (entree["groupe_id"] is None, entree["groupe_id"]))

    return {
        "total_groupes": len(groupes),
        "nb_groupes_invalides": len(groupes_invalides),
        "groupes_invalides": groupes_invalides,
    }


def compute_coherence_schema_version(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare `schema_version` (racine) et `meta.schema_version`.

    Les deux champs doivent porter la même valeur : une divergence signale
    un profil de groupe partiellement régénéré (ex. `meta` reconstruit sans
    mettre à jour la racine, ou l'inverse).

    Returns:
        `{"groupes_incoherents": [{"groupe_id":..., "schema_version":...,
        "meta_schema_version":...}, ...]}`
    """
    groupes_incoherents: list[dict[str, Any]] = []

    for groupe in groupes:
        schema_version = groupe.get("schema_version")
        meta = groupe.get("meta")
        meta_schema_version = meta.get("schema_version") if isinstance(meta, dict) else None

        if schema_version != meta_schema_version:
            groupes_incoherents.append({
                "groupe_id": groupe.get("groupe_id"),
                "schema_version": schema_version,
                "meta_schema_version": meta_schema_version,
            })

    return {"groupes_incoherents": groupes_incoherents}


def compute_ecart_couverture_roster(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Écart entre `meta.couverture_roster.profils_disponibles` et `roster_total`.

    `couverture_roster` est optionnel — présent seulement pour les groupes
    construits via `group_profile.py --from-roster` (voir `schema_groupe.py`).
    Un groupe sans ce bloc, ou avec des valeurs non entières, n'est jamais
    inclus : il n'y a rien à mesurer.

    Returns:
        `{"groupes": [{"groupe_id":..., "roster_total":...,
        "profils_disponibles":..., "ecart": int,
        "taux_couverture_pct": float}, ...]}`, `ecart` =
        `roster_total - profils_disponibles`, `taux_couverture_pct` =
        `100 * profils_disponibles / roster_total` (arrondi à 2 décimales ;
        `0.0` si `roster_total` vaut `0`, pour ne jamais diviser par zéro).
        Triés par `groupe_id`. Ce taux rend visible, dans le temps, la
        progression de la couverture roster (avant/après activation de
        l'extraction roster-driven, voir
        `docs/decisions/provenance-pivot.md`).
    """
    resultat: list[dict[str, Any]] = []

    for groupe in groupes:
        meta = groupe.get("meta")
        couverture = meta.get("couverture_roster") if isinstance(meta, dict) else None
        if not isinstance(couverture, dict):
            continue

        roster_total = couverture.get("roster_total")
        profils_disponibles = couverture.get("profils_disponibles")
        if not isinstance(roster_total, int) or not isinstance(profils_disponibles, int):
            continue
        if isinstance(roster_total, bool) or isinstance(profils_disponibles, bool):
            continue

        taux_couverture_pct = (
            round(100 * profils_disponibles / roster_total, 2) if roster_total > 0 else 0.0
        )

        resultat.append({
            "groupe_id": groupe.get("groupe_id"),
            "roster_total": roster_total,
            "profils_disponibles": profils_disponibles,
            "ecart": roster_total - profils_disponibles,
            "taux_couverture_pct": taux_couverture_pct,
        })

    resultat.sort(key=lambda entree: (entree["groupe_id"] is None, entree["groupe_id"]))
    return {"groupes": resultat}


def compute_doublons_groupe_id(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Détecte les `groupe_id` présents plusieurs fois dans le corpus.

    Le `groupe_id` (`"<chambre>:<sigle>"`) doit être unique : un doublon
    signale une erreur amont de génération. Les groupes sans `groupe_id`
    (absent ou vide) sont ignorés — ce défaut relève de la validation
    structurelle (`validate_profil_groupe`), pas de la cohérence
    inter-groupes.

    Returns:
        `{"doublons": [{"groupe_id": str, "occurrences": int}, ...]}`, trié
        par `groupe_id` pour un résultat déterministe ; liste vide si aucun
        doublon.
    """
    occurrences_par_id: dict[str, int] = {}
    for groupe in groupes:
        groupe_id = groupe.get("groupe_id")
        if not groupe_id:
            continue
        occurrences_par_id[groupe_id] = occurrences_par_id.get(groupe_id, 0) + 1

    return {
        "doublons": [
            {"groupe_id": groupe_id, "occurrences": occurrences}
            for groupe_id, occurrences in sorted(occurrences_par_id.items())
            if occurrences > 1
        ]
    }


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
    groupes: list[dict[str, Any]], reference_date: datetime | None = None
) -> dict[str, Any]:
    """Ancienneté des sources (`sources[].synchro_le`) par type de source.

    Pour chaque type de source rencontré (`sources[].type`, `"null"` si
    absent), distribution en jours écoulés depuis la dernière synchro : min,
    max, médiane, moyenne. Les sources sans `synchro_le` valide sont
    ignorées.

    Args:
        groupes: liste de profils de groupe.
        reference_date: date de référence pour le calcul de l'ancienneté,
            injectable pour des tests déterministes (défaut :
            `datetime.now(timezone.utc)`).

    Returns:
        `{"total_sources_datees": int, "par_type_source": {type: {...}}}`.
        Un type de source absent de `groupes` n'apparaît pas dans le résultat.
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    anciennetes_par_type: dict[str, list[int]] = {}
    for groupe in groupes:
        for source in groupe.get("sources") or []:
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


def _anciennetes_sources_jours(groupe: dict[str, Any], reference_date: datetime) -> list[int]:
    """Anciennetés (en jours) des sources du groupe dont `synchro_le` est valide."""
    anciennetes: list[int] = []
    for source in groupe.get("sources") or []:
        if not isinstance(source, dict):
            continue
        date_synchro = _parse_synchro_le(source.get("synchro_le"))
        if date_synchro is not None:
            anciennetes.append(_anciennete_jours(date_synchro, reference_date))
    return anciennetes


def compute_groupes_perimes(
    groupes: list[dict[str, Any]],
    staleness_days: int,
    reference_date: datetime | None = None,
) -> list[str]:
    """`groupe_id` des groupes dont **toutes** les sources ont plus de `staleness_days` jours.

    Un groupe sans aucune source dont `synchro_le` est exploitable n'est
    jamais considéré comme périmé (il n'y a rien à mesurer) : seuls les
    groupes ayant au moins une source datée, et dont la source la plus
    fraîche dépasse tout de même le seuil, sont retournés.

    Args:
        groupes: liste de profils de groupe.
        staleness_days: seuil d'ancienneté (en jours) au-delà duquel une
            source est considérée périmée.
        reference_date: date de référence injectable (voir
            `compute_fraicheur_sources`).

    Returns:
        Liste triée des `groupe_id` de groupes périmés.
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    perimes = []
    for groupe in groupes:
        anciennetes = _anciennetes_sources_jours(groupe, reference)
        if anciennetes and min(anciennetes) > staleness_days:
            perimes.append(groupe.get("groupe_id"))

    return sorted(perimes)


# ---------------------------------------------------------------------------
# Agrégation des warnings
# ---------------------------------------------------------------------------

def _type_warning(warning: str) -> str:
    """Type d'un warning : préfixe avant le premier ':', message complet sinon."""
    prefixe, separateur, _ = warning.partition(":")
    return prefixe.strip() if separateur else warning.strip()


def compute_agregation_warnings(groupes: list[dict[str, Any]]) -> dict[str, Any]:
    """Compile tous les `meta.warnings[]` des groupes par type.

    Le "type" d'un warning est déterminé par `_type_warning` (préfixe avant
    le premier ':').

    Returns:
        `{"total_warnings": int, "par_type": {type: {"frequence": int,
        "groupe_ids": [str, ...]}}}`. `frequence` compte chaque occurrence
        (un groupe avec deux warnings du même type compte pour 2) ;
        `groupe_ids` liste sans doublon les groupes concernés par ce type,
        triés.
    """
    par_type: dict[str, dict[str, Any]] = {}
    total_warnings = 0

    for groupe in groupes:
        meta = groupe.get("meta") or {}
        warnings = meta.get("warnings") or []
        groupe_id = groupe.get("groupe_id")

        for warning in warnings:
            if not isinstance(warning, str) or not warning:
                continue
            total_warnings += 1
            type_warning = _type_warning(warning)
            entree = par_type.setdefault(type_warning, {"frequence": 0, "groupe_ids": set()})
            entree["frequence"] += 1
            entree["groupe_ids"].add(groupe_id)

    return {
        "total_warnings": total_warnings,
        "par_type": {
            type_warning: {
                "frequence": entree["frequence"],
                "groupe_ids": sorted(entree["groupe_ids"]),
            }
            for type_warning, entree in sorted(par_type.items())
        },
    }


# ---------------------------------------------------------------------------
# Assemblage du rapport
# ---------------------------------------------------------------------------

def build_report(
    groupes: list[dict[str, Any]],
    erreurs_lecture: list[dict[str, Any]],
    staleness_days: int = 30,
    reference_date: datetime | None = None,
    scrutins_index: Any = None,
) -> dict[str, Any]:
    """Assemble tous les indicateurs `compute_*` en un rapport structuré unique.

    Args:
        groupes: profils de groupe valides (sortie de `load_groupe_directory`).
        erreurs_lecture: erreurs de lecture (sortie de `load_groupe_directory`).
        scrutins_index: index partagé des scrutins (#432), d'où vient la date de
            chaque scrutin de cohésion (#726). Le défaut est `None` et **non un
            chemin du dépôt** : la valeur par défaut d'une fonction qui pointe
            dans l'arbre est le piège de `AGENTS.md` §3b. La CLI, elle, le charge
            depuis `--scrutins`.
        staleness_days: seuil d'ancienneté en jours pour `compute_groupes_perimes`
            (défaut : 30).
        reference_date: date de référence injectable pour les indicateurs de
            fraîcheur, voir `compute_fraicheur_sources` (défaut :
            `datetime.now(timezone.utc)`).

    Returns:
        Dict sérialisable JSON, une section par catégorie d'indicateur
        (`volumetrie`, `completude`, `coherence`, `fraicheur`, `warnings`,
        `tableau_croise_groupes`, `plage_dates_groupes`) plus `meta` et
        `erreurs_lecture`. Un outil de qualité interne : ce rapport ne doit
        jamais introduire de jugement de valeur, de score ou de classement
        (AGENTS.md §2.1).
    """
    reference = reference_date if reference_date is not None else datetime.now(timezone.utc)

    return {
        "meta": {
            "genere_le": reference.isoformat(),
            "total_groupes": len(groupes),
            "total_erreurs_lecture": len(erreurs_lecture),
            "staleness_days": staleness_days,
        },
        "volumetrie": {
            "effectifs": compute_effectifs(groupes),
            "nombre_cohesion_votes": compute_nombre_cohesion_votes(groupes),
            "distribution_amendements": compute_distribution_amendements(groupes),
        },
        "completude": {
            "presence_tags_thematiques": compute_presence_tags_thematiques(groupes),
            "groupes_membres_sans_cohesion": compute_groupes_membres_sans_cohesion(groupes),
        },
        "coherence": {
            "validation_schema": compute_validation_schema(groupes),
            "coherence_schema_version": compute_coherence_schema_version(groupes),
            "ecart_couverture_roster": compute_ecart_couverture_roster(groupes),
            "doublons_groupe_id": compute_doublons_groupe_id(groupes),
        },
        "fraicheur": {
            "fraicheur_sources": compute_fraicheur_sources(groupes, reference_date=reference),
            "groupes_perimes": compute_groupes_perimes(
                groupes, staleness_days=staleness_days, reference_date=reference
            ),
        },
        "warnings": compute_agregation_warnings(groupes),
        "tableau_croise_groupes": compute_tableau_croise_groupes(groupes),
        "plage_dates_groupes": compute_plage_dates_groupes(groupes, scrutins_index),
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
    lignes_effectifs = [
        [
            champ, stats["nombre_groupes_renseignes"],
            stats["min"], stats["max"], stats["mediane"], stats["moyenne"],
        ]
        for champ, stats in volumetrie["effectifs"].items()
    ]

    cohesion = volumetrie["nombre_cohesion_votes"]

    amendements = volumetrie["distribution_amendements"]
    lignes_amendements_global = [
        [champ, stats["min"], stats["max"], stats["mediane"], stats["moyenne"]]
        for champ, stats in amendements["global"].items()
    ]

    sections_par_type_deposant = "".join(
        f"\n#### {type_deposant}\n\n"
        + _md_table(
            ["Compteur", "Min", "Max", "Médiane", "Moyenne"],
            [
                [champ, stats["min"], stats["max"], stats["mediane"], stats["moyenne"]]
                for champ, stats in amendements["par_type_deposant"][type_deposant].items()
            ],
            "Aucun groupe.",
        )
        for type_deposant in sorted(amendements["par_type_deposant"])
    )

    return (
        "## Volumétrie\n\n"
        "### Effectifs (`effectif.a_la_date_de_reference` / `actuel` / `min_historique` / `max_historique`)\n\n"
        + _md_table(
            ["Champ", "Groupes renseignés", "Min", "Max", "Médiane", "Moyenne"],
            lignes_effectifs, "Aucun groupe.",
        )
        + "\n### Cohésion de vote (nombre de scrutins recensés par groupe)\n\n"
        + _md_table(
            ["Min", "Max", "Médiane", "Moyenne", "% groupes à 0"],
            [[
                cohesion["min"], cohesion["max"], cohesion["mediane"], cohesion["moyenne"],
                cohesion["pct_groupes_a_zero"],
            ]],
            "Aucun groupe.",
        )
        + "\n### Amendements agrégés (tous types de déposants confondus)\n\n"
        + _md_table(
            ["Compteur", "Min", "Max", "Médiane", "Moyenne"],
            lignes_amendements_global, "Aucun groupe.",
        )
        + "\n### Amendements agrégés par type de déposant\n"
        + sections_par_type_deposant
    )


def _md_section_completude(completude: dict[str, Any]) -> str:
    tags = completude["presence_tags_thematiques"]
    sans_cohesion = completude["groupes_membres_sans_cohesion"]

    return (
        "## Complétude\n\n"
        "### Présence des tags thématiques agrégés\n\n"
        + _md_table(
            ["Renseignés", "Total", "Taux (%)"],
            [[tags["renseignes"], tags["total"], tags["taux_pct"]]],
            "Aucun groupe.",
        )
        + "\n### Groupes avec des membres mais sans `cohesion_votes`\n\n"
        f"{sans_cohesion['nb_groupes_membres_sans_cohesion']} / "
        f"{sans_cohesion['total_groupes']} groupe(s).\n"
    )


def _md_section_coherence(coherence: dict[str, Any]) -> str:
    lignes_validation = [
        [g["groupe_id"], "; ".join(g["erreurs"])]
        for g in coherence["validation_schema"]["groupes_invalides"]
    ]
    lignes_schema = [
        [g["groupe_id"], g["schema_version"], g["meta_schema_version"]]
        for g in coherence["coherence_schema_version"]["groupes_incoherents"]
    ]
    lignes_roster = [
        [g["groupe_id"], g["roster_total"], g["profils_disponibles"], g["ecart"], g["taux_couverture_pct"]]
        for g in coherence["ecart_couverture_roster"]["groupes"]
    ]
    lignes_doublons = [
        [d["groupe_id"], d["occurrences"]] for d in coherence["doublons_groupe_id"]["doublons"]
    ]

    return (
        "## Cohérence\n\n"
        "### Validation du schéma (`validate_profil_groupe`)\n\n"
        + _md_table(["groupe_id", "Erreurs"], lignes_validation, "Aucun groupe invalide détecté.")
        + "\n### Divergence `schema_version` / `meta.schema_version`\n\n"
        + _md_table(
            ["groupe_id", "schema_version", "meta.schema_version"],
            lignes_schema, "Aucune divergence détectée.",
        )
        + "\n### Écart de couverture du roster\n\n"
        + _md_table(
            ["groupe_id", "Roster total", "Profils disponibles", "Écart", "Taux de couverture (%)"],
            lignes_roster, "Aucune donnée de couverture roster (`meta.couverture_roster`).",
        )
        + "\n### Doublons de `groupe_id`\n\n"
        + _md_table(["groupe_id", "Occurrences"], lignes_doublons, "Aucun doublon détecté.")
    )


def _md_section_fraicheur(fraicheur: dict[str, Any], staleness_days: int) -> str:
    lignes_fraicheur = [
        [
            type_source, stats["nombre_sources"],
            stats["min_jours"], stats["max_jours"], stats["mediane_jours"], stats["moyenne_jours"],
        ]
        for type_source, stats in fraicheur["fraicheur_sources"]["par_type_source"].items()
    ]

    lignes_perimes = [[groupe_id] for groupe_id in fraicheur["groupes_perimes"]]

    return (
        "## Fraîcheur\n\n"
        "### Ancienneté des sources par type (jours écoulés depuis `synchro_le`)\n\n"
        + _md_table(
            ["Type de source", "Nombre de sources", "Min", "Max", "Médiane", "Moyenne"],
            lignes_fraicheur, "Aucune source datée.",
        )
        + f"\n### Groupes périmés (toutes sources > {staleness_days} jours)\n\n"
        + _md_table(["groupe_id"], lignes_perimes, "Aucun groupe périmé.")
    )


def _md_section_tableau_croise_groupes(tableau: dict[str, Any]) -> str:
    lignes = [
        [
            ligne["groupe_id"], ligne["groupe_nom"], ligne["chambre"],
            ligne["membres"], ligne["cohesion_votes"],
            ligne["tags_thematiques_agreges"], ligne["amendements"],
        ]
        for ligne in tableau["lignes"]
    ]

    return (
        "## Tableau croisé des volumes par groupe\n\n"
        + _md_table(
            [
                "groupe_id", "Nom", "Chambre", "Membres",
                "Cohésion de vote", "Tags thématiques", "Amendements",
            ],
            lignes, "Aucun groupe.",
        )
    )


def _fmt_plage_cellule(cellule: dict[str, str] | None) -> str:
    """`"min → max"` si la cellule est renseignée, `"N/D"` sinon (donnée manquante)."""
    return "N/D" if cellule is None else f"{cellule['min']} → {cellule['max']}"


def _md_section_plage_dates_groupes(plage: dict[str, Any]) -> str:
    lignes = [
        [
            ligne["groupe_id"], ligne["groupe_nom"], ligne["chambre"],
            _fmt_plage_cellule(ligne["cohesion_votes"]), "N/A (non applicable)",
        ]
        for ligne in plage["lignes"]
    ]

    lignes_non_resolues = [[motif, n] for motif, n in plage["dates_non_resolues"].items()]

    return (
        "## Tableau croisé des plages temporelles par groupe\n\n"
        "Complète (sans le remplacer) le tableau croisé des volumes ci-dessus : "
        "pour chaque groupe, la période couverte par les dates disponibles "
        "(min → max), plutôt que le nombre d'entrées.\n\n"
        + _md_table(
            [
                "groupe_id", "Nom", "Chambre",
                "Cohésion de vote (min → max)", "Amendements agrégés",
            ],
            lignes, "Aucun groupe.",
        )
        + "\n> **`amendements_agreges`** : colonne marquée **N/A (non "
        "applicable)**, jamais une cellule vide silencieuse. "
        "`schema_groupe.py` ne stocke que des compteurs au niveau de "
        "l'agrégat (`nb_amendements`, `nb_adoptes`...), aucune date : c'est "
        "une limite structurelle du schéma actuel, pas une donnée "
        "manquante à corriger. Voir la section Hors périmètre de l'issue "
        "#316.\n\n"
        + (
            ""
            if plage["index_disponible"]
            else "> **Index des scrutins non fourni** : la colonne « Cohésion de vote » est "
            "vide pour tous les groupes, et c'est un trou déclaré, jamais « ce groupe n'a "
            "pas de scrutin » (AGENTS.md §2 règle 5). La date d'un scrutin vit dans "
            "`pivot_data/scrutins.json` depuis #432 ; passer `--scrutins CHEMIN` la "
            "résout.\n\n"
        )
        + "### Scrutins de cohésion dont la date ne se résout pas\n\n"
        + "> Compté par motif, jamais énuméré (#726) : ces entrées se comptent à l'échelle "
        "du corpus de scrutins, pas à celle d'une anomalie.\n\n"
        + _md_table(
            ["Motif", "Entrées"],
            lignes_non_resolues, "Toutes les dates de scrutin se résolvent.",
        )
    )


def _md_section_warnings(warnings: dict[str, Any]) -> str:
    lignes = [
        [type_warning, entree["frequence"], ", ".join(entree["groupe_ids"])]
        for type_warning, entree in warnings["par_type"].items()
    ]

    return (
        "## Warnings\n\n"
        f"Total : {warnings['total_warnings']}\n\n"
        + _md_table(["Type", "Fréquence", "Groupes concernés"], lignes, "Aucun warning.")
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
            "# Rapport d'audit du jeu de données groupes\n\n"
            f"Généré le {meta['genere_le']}. "
            f"{meta['total_groupes']} groupe(s) analysé(s), "
            f"{meta['total_erreurs_lecture']} erreur(s) de lecture. "
            f"Seuil de péremption des sources : {meta['staleness_days']} jour(s).\n\n"
            "Ce rapport est un outil de qualité interne : il présente des "
            "indicateurs bruts, sans jugement de valeur ni classement.\n"
        ),
        _md_section_volumetrie(rapport["volumetrie"]),
        _md_section_tableau_croise_groupes(rapport["tableau_croise_groupes"]),
        _md_section_plage_dates_groupes(rapport["plage_dates_groupes"]),
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
        prog="audit_groupe_dataset.py",
        description=(
            "Audite un jeu de données de profils de groupe : volumétrie, "
            "complétude, cohérence, fraîcheur des sources et warnings agrégés. "
            "Outil de qualité interne, ne produit aucun score ni classement."
        ),
    )
    parser.add_argument(
        "--input-dir",
        default="pivot_data/groupes",
        metavar="DOSSIER",
        help=(
            "Dossier contenant les fichiers *.json à auditer (scan récursif, "
            "défaut : pivot_data/groupes)."
        ),
    )
    parser.add_argument(
        "--scrutins",
        default="pivot_data/scrutins.json",
        metavar="FICHIER",
        help=(
            "Index partagé des scrutins (#432), d'où vient la date de chaque "
            "scrutin de cohésion. Absent ou illisible : la colonne des plages "
            "est vide et le rapport le DÉCLARE (#726)."
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
            "(audit_groupe_<horodatage-UTC>.json/.md) au lieu de nommer chaque "
            "fichier — incompatible avec --output-json/--output-md."
        ),
    )
    parser.add_argument(
        "--staleness-days",
        type=int,
        default=30,
        metavar="JOURS",
        help="Seuil d'ancienneté (jours) au-delà duquel un groupe est périmé (défaut : 30).",
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
        output_json_path = str(Path(args.output_dir) / f"audit_groupe_{horodatage}.json")
        output_md_path = str(Path(args.output_dir) / f"audit_groupe_{horodatage}.md")

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"[!] Dossier introuvable : {input_dir}", file=sys.stderr)
        return 1

    groupes, erreurs_lecture = load_groupe_directory(input_dir)
    print(
        f"→ {len(groupes)} groupe(s) chargé(s), {len(erreurs_lecture)} erreur(s) de lecture.",
        file=sys.stderr,
    )

    index_scrutins = charger_scrutins(Path(args.scrutins)) if args.scrutins else None
    if args.scrutins and not len(index_scrutins or ()):
        print(
            f"[!] Index des scrutins vide ou introuvable ({args.scrutins}) : les plages "
            "temporelles par groupe seront vides, et le rapport le déclare (#726).",
            file=sys.stderr,
        )
    rapport = build_report(
        groupes, erreurs_lecture,
        staleness_days=args.staleness_days,
        scrutins_index=index_scrutins,
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
