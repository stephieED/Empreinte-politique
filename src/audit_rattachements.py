#!/usr/bin/env python3
"""audit_rattachements.py — Quelle part de chaque jointure se résout, et sur quelle population.

## Pourquoi ce module n'est PAS dans `audit_integrite_referentielle`

Celui-là vérifie une propriété **binaire** : une clé publiée résout, ou elle ne
résout pas. Une clé orpheline est un **bug**, il bloque, et il n'y a aucun seuil
à choisir — c'est ce qui lui donne zéro faux positif.

Ici, la propriété est un **taux**, et un taux bas n'est pas un bug. Un scrutin
sans dossier, c'est le **silence de la source** : l'Assemblée ne publie aucune
référence législative sur ses scrutins (0/18 311, #762). Un texte visé sans
titre en 14e législature, c'est un index historique incomplet. Ranger ces
absences à côté des références orphelines les ferait lire comme des fautes, et
inversement diluerait les fautes dans un tableau de taux.

**Ce module ne bloque donc jamais.** Il rapporte, et c'est sa dérive dans le
temps qui parle : un rattachement qui tombe de 61 % à 12 % d'un run à l'autre
est un signal, là où 61 % en soi n'en est pas un.

## La population est publiée avec le taux, toujours

Le MÊME rattachement vaut 4 % ou 61 % selon ce qu'on met au dénominateur :
714 scrutins sur 17 762 publiés, mais 423 sur les 697 textes en dernière
lecture. Un taux sans sa population est une erreur, pas une approximation
(AGENTS.md §9). Chaque entrée porte donc `resolus`, `total` **et** le nom de la
population — jamais un pourcentage seul (§2 règle 7).

## Ce que ce module NE calcule pas, et pourquoi

La population « votes sur l'ensemble d'un texte » (925 scrutins, dont 697
textes après repli sur la dernière lecture) est sélectionnée par
`isWholeTextVote` / `cleDuTexteVote`, et AGENTS.md §6 fixe que **le repli et la
sélection vivent UNIQUEMENT dans `web/UI_finale/src/utils/lecture.js`** (#711).
La redire ici en ferait une seconde source qui divergerait. L'audit rapporte
donc les populations que Python peut nommer sans dupliquer cette sélection, et
déclare celle qu'il ne couvre pas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "audit-rattachements-v1"


def _charger(chemin: Path) -> Any:
    """Lit un JSON, ou rend `None` — un fichier absent est un fait, pas une panne."""
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _entree(
    cle: str,
    quoi: str,
    population: str,
    resolus: int,
    total: int,
    note: str | None = None,
) -> dict[str, Any]:
    """Une jointure mesurée. `taux` n'est publié qu'accompagné de ses deux termes."""
    return {
        "cle": cle,
        "quoi": quoi,
        "population": population,
        "resolus": resolus,
        "total": total,
        "taux": round(resolus / total * 100, 1) if total else None,
        "note": note,
    }


def audit_rattachements(pivot: Path = Path("pivot_data")) -> dict[str, Any]:
    """Mesure les rattachements que le dépôt a dû établir lui-même.

    Aucun n'est garanti par la source : ils sont tous reconstruits, et c'est
    pour ça qu'ils méritent d'être suivis.

    `pivot` est le DOSSIER LU, pas une racine de dépôt : c'est ce qui permet à
    l'appelant de le faire pointer ailleurs — un jeu de fixtures, par exemple.
    Sans ce paramètre, les tests du CLI d'`audit_pipeline` scannaient le corpus
    vivant, ce qu'AGENTS.md §3b interdit, et la suite passait de 3 s à 50 s sur
    ce seul fichier.
    """
    pivot = Path(pivot)
    jointures: list[dict[str, Any]] = []
    absents: list[str] = []

    commissions = (_charger(pivot / "commissions_dossiers.json") or {}).get("commissions")
    if not isinstance(commissions, dict):
        commissions = {}
        absents.append("pivot_data/commissions_dossiers.json")

    scrutins_dossiers = _charger(pivot / "scrutins_dossiers.json") or {}
    rattachement_scrutins = scrutins_dossiers.get("scrutins")
    if not isinstance(rattachement_scrutins, dict):
        rattachement_scrutins = {}
        absents.append("pivot_data/scrutins_dossiers.json")

    # ── 1 & 2. L'index des amendements : dépôt → texte visé → dossier ────────
    #
    # Deux crans, et ils ne se confondent pas : un amendement peut viser un
    # texte que l'index ne nomme pas (le titre manque), et un texte nommé peut
    # n'être rattaché à aucun dossier. Les mesurer ensemble masquerait celui
    # des deux qui décroche.
    dossiers_vises: set[str] = set()
    for chemin in sorted(pivot.glob("amendements/*.json")):
        if chemin.name.endswith(".cosignatures.json"):
            continue
        index = _charger(chemin)
        if not isinstance(index, dict):
            continue
        legislature = index.get("legislature") or chemin.stem
        textes = index.get("textes") or {}
        amendements = index.get("amendements") or {}
        connus = sum(
            1
            for a in amendements.values()
            if isinstance(a, dict) and a.get("texte_vise") in textes
        )
        jointures.append(
            _entree(
                f"amendement_vers_texte_vise.{legislature}",
                "un amendement déposé → le texte qu'il vise",
                f"amendements publiés, législature {legislature}",
                connus,
                len(amendements),
            )
        )
        avec_dossier = {
            cle for cle, v in textes.items() if isinstance(v, dict) and v.get("dossier_id")
        }
        jointures.append(
            _entree(
                f"texte_vise_vers_dossier.{legislature}",
                "un texte visé → son dossier législatif",
                f"textes visés déclarés, législature {legislature}",
                len(avec_dossier),
                len(textes),
            )
        )
        for cle in avec_dossier:
            dossiers_vises.add(textes[cle]["dossier_id"])

    # ── 3. Dossier → commission saisie au fond ───────────────────────────────
    if dossiers_vises:
        jointures.append(
            _entree(
                "dossier_amende_vers_commission",
                "un dossier amendé → sa commission saisie au fond",
                "dossiers visés par au moins un amendement publié",
                len(dossiers_vises & set(commissions)),
                len(dossiers_vises),
                note="La commission est lue dans l'archive AN, jamais déduite d'un intitulé.",
            )
        )

    # ── 4. Scrutin → dossier (#758) ──────────────────────────────────────────
    #
    # Le taux global est BAS et ce n'est pas un défaut : la plupart des scrutins
    # portent sur un amendement ou un article, que le dossier ne nomme pas dans
    # `voteRefs`. La population qui compte pour la fiche — les votes sur
    # l'ensemble d'un texte — est sélectionnée dans la vue (§6), pas ici.
    scrutins = (_charger(pivot / "scrutins.json") or {}).get("scrutins")
    if isinstance(scrutins, list):
        resolus = sum(1 for s in scrutins if s.get("id") in rattachement_scrutins)
        jointures.append(
            _entree(
                "scrutin_vers_dossier",
                "un scrutin → le dossier qu'il tranche",
                "tous les scrutins publiés",
                resolus,
                len(scrutins),
                note=(
                    "Taux bas ATTENDU : la plupart des scrutins portent sur un amendement ou "
                    "un article, jamais nommé dans `voteRefs`. La population utile — les votes "
                    "sur l'ensemble d'un texte — est sélectionnée dans `lecture.js` (§6, #711) "
                    "et n'est pas recalculée ici."
                ),
            )
        )
    else:
        absents.append("pivot_data/scrutins.json")

    # ── 5. Texte porté → dossier, puis → commission ──────────────────────────
    portes = portes_avec_dossier = portes_avec_commission = 0
    for chemin in sorted(pivot.glob("profiles/*.pivot.json")):
        profil = _charger(chemin)
        if not isinstance(profil, dict):
            continue
        for texte in profil.get("textes_portes") or []:
            portes += 1
            dossier = texte.get("dossier_id")
            if dossier:
                portes_avec_dossier += 1
                if dossier in commissions:
                    portes_avec_commission += 1
    if portes:
        jointures.append(
            _entree(
                "texte_porte_vers_dossier",
                "un texte porté → son dossier législatif",
                "textes portés publiés",
                portes_avec_dossier,
                portes,
            )
        )
        jointures.append(
            _entree(
                "texte_porte_vers_commission",
                "un texte porté → sa commission saisie au fond",
                "textes portés publiés",
                portes_avec_commission,
                portes,
            )
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "jointures": jointures,
        "fichiers_absents": absents,
        # Rappel porté par la donnée elle-même : ce module ne bloque pas, et
        # un lecteur qui le découvre doit le savoir avant de lire un taux bas.
        "bloquant": False,
    }


__all__ = ["SCHEMA_VERSION", "audit_rattachements"]
