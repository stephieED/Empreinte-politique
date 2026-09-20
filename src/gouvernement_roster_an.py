#!/usr/bin/env python3
"""
gouvernement_roster_an.py — Le roster d'un gouvernement, lu dans AMO30 (#996, lot 2).

## Pourquoi un roster, et pas les profils

`gouvernement_roster.py` retrouve les membres d'un gouvernement **dans les
profils déjà collectés**, par le libellé de leurs mandats. Une fiche ne liste
donc que les ministres qui ont un profil chez nous : Attal en publiait 25, AMO30
en connaît 35. La même logique que les groupes parlementaires (#526) veut
l'inverse : le roster vient de la **source**, et c'est lui qui dit qui collecter.

Mesuré le 17/09/2026 sur l'archive du 17/08 : **17** gouvernements, **311**
personnes, dont 106 ont déjà un profil et **205** n'en ont pas — 124 n'ont
jamais été députées, et aucun module ne pouvait leur donner d'identifiant.

## Ce que ce module fait

1. Il lit les organes `GOUVERNEMENT` et les mandats qui les visent, comme
   `an_roster.construire_index_gp` le fait pour les groupes politiques.
2. Il demande les slugs à `an_roster.resoudre_slugs`, **sur l'union des acteurs
   des deux index**. La table de correspondance passe devant (#525) ; un slug
   n'est fabriqué que pour un acteur que personne n'a encore relu, et l'univers
   de collision reste entier — sans l'union, un ministre et un député
   homonymes pourraient recevoir le même slug le même jour.
3. Il rend des membres au format des rosters bruts (`slug`, `slug_origine`,
   `acteur_ref`, `mandat_periodes`), pour que la passe de correspondance dérive
   leurs entrées (§5b du portail, seuil 0) et que la collecte puisse suivre.

Mesure du 17/09/2026 : **205 slugs fabriqués, 106 repris de la table, aucun
acteur sans slug** — ni homonymie, ni état civil manquant.

Ce module ne collecte aucun profil : c'est le lot suivant de #996.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Optional

from an_roster import resoudre_slugs

CODE_TYPE_GOUVERNEMENT = "GOUVERNEMENT"
TYPE_ORGANE_GOUVERNEMENT = "GOUVERNEMENT"

#: Clé du roster des gouvernements dans `rosters_bruts.json`, à côté des
#: `deputes:<legislature>` des groupes.
CLE_ROSTER = ("gouvernements", None)


class RosterGouvernementIndisponible(RuntimeError):
    """L'archive ne rend aucun organe `GOUVERNEMENT` : la composition est
    INCONNUE, pas vide (#510)."""


def _texte(valeur: Any) -> Optional[str]:
    if isinstance(valeur, dict):
        valeur = valeur.get("#text")
    return valeur if isinstance(valeur, str) and valeur else None


def _mandats_de(acteur: dict[str, Any]) -> list[dict[str, Any]]:
    mandats = (acteur.get("mandats") or {}).get("mandat") or []
    return mandats if isinstance(mandats, list) else [mandats]


def construire_index_gouvernements(zip_path: Path) -> dict[str, Any]:
    """`{organes, mandats, acteurs}` pour les seuls organes `GOUVERNEMENT`.

    Même forme que l'index GP, pour que `resoudre_slugs` s'applique tel quel :
    `organes` porte le sigle et les dates, `mandats` les couples acteur/période,
    `acteurs` le nom — qui sert à fabriquer un slug et à **nommer** un écart.
    """
    organes: dict[str, dict[str, Any]] = {}
    mandats: dict[str, list[list[Optional[str]]]] = {}
    acteurs: dict[str, str] = {}

    with zipfile.ZipFile(zip_path) as zf:
        noms = zf.namelist()
        for nom in noms:
            if not nom.startswith("json/organe/") or not nom.endswith(".json"):
                continue
            try:
                with zf.open(nom) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, KeyError):
                continue
            organe = data.get("organe") if isinstance(data, dict) else None
            if not isinstance(organe, dict) or organe.get("codeType") != CODE_TYPE_GOUVERNEMENT:
                continue
            organe_ref = _texte(organe.get("uid"))
            if organe_ref is None:
                continue
            vie = organe.get("viMoDe") or {}
            organes[organe_ref] = {
                "libelle_an": organe.get("libelleAbrege"),
                "debut": vie.get("dateDebut"),
                "fin": vie.get("dateFin"),
            }

        for nom in noms:
            if not nom.startswith("json/acteur/") or not nom.endswith(".json"):
                continue
            try:
                with zf.open(nom) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, KeyError):
                continue
            acteur = data.get("acteur") if isinstance(data, dict) else None
            if not isinstance(acteur, dict):
                continue
            acteur_ref = _texte(acteur.get("uid"))
            if acteur_ref is None:
                continue
            for mandat in _mandats_de(acteur):
                if mandat.get("typeOrgane") != TYPE_ORGANE_GOUVERNEMENT:
                    continue
                organe_ref = (mandat.get("organes") or {}).get("organeRef")
                if organe_ref not in organes:
                    continue
                mandats.setdefault(organe_ref, []).append(
                    [acteur_ref, mandat.get("dateDebut"), mandat.get("dateFin")]
                )
                if acteur_ref not in acteurs:
                    ident = (acteur.get("etatCivil") or {}).get("ident") or {}
                    acteurs[acteur_ref] = " ".join(
                        p for p in (ident.get("prenom"), ident.get("nom")) if p
                    )

    if not organes:
        raise RosterGouvernementIndisponible(
            f"Aucun organe GOUVERNEMENT dans {zip_path} : la composition des "
            "gouvernements est INCONNUE, pas vide.")
    return {"organes": organes, "mandats": mandats, "acteurs": acteurs}


def resoudre_slugs_des_membres(
    index_gouvernements: dict[str, Any],
    index_gp: Optional[dict[str, Any]] = None,
    chemin_correspondance: Optional[Path] = None,
) -> tuple[dict[str, str], dict[str, str], list[dict[str, Any]]]:
    """`resoudre_slugs` sur l'**union** des acteurs des deux index.

    Rendu filtré aux seuls membres de gouvernement : les slugs des députés sont
    ceux du roster des groupes, et ce module ne les republie pas. L'union sert
    à l'univers de collision, pas à la sortie.
    """
    acteurs = dict((index_gp or {}).get("acteurs") or {})
    acteurs.update(index_gouvernements.get("acteurs") or {})
    slugs, origines, non_attribues = resoudre_slugs({"acteurs": acteurs}, chemin_correspondance)
    membres = set(index_gouvernements.get("acteurs") or {})
    return (
        {ref: slug for ref, slug in slugs.items() if ref in membres},
        {ref: origine for ref, origine in origines.items() if ref in membres},
        [x for x in non_attribues if x.get("acteur_ref") in membres],
    )


def deriver_membres(
    index_gouvernements: dict[str, Any],
    slugs: dict[str, str],
    origines: dict[str, str],
) -> list[dict[str, Any]]:
    """Les membres, au format des rosters bruts, triés par slug.

    Un acteur qui siège dans plusieurs gouvernements n'apparaît **qu'une fois**,
    avec autant de `mandat_periodes` : c'est une personne à collecter, pas une
    par gouvernement. Le rattachement gouvernement par gouvernement se fait
    ailleurs, sur `acteur_ref`.
    """
    periodes: dict[str, list[dict[str, Any]]] = {}
    for organe_ref, entrees in (index_gouvernements.get("mandats") or {}).items():
        libelle = (index_gouvernements["organes"].get(organe_ref) or {}).get("libelle_an")
        for acteur_ref, debut, fin in entrees:
            periodes.setdefault(acteur_ref, []).append(
                {"organe_ref": organe_ref, "libelle_an": libelle, "debut": debut, "fin": fin}
            )
    membres = []
    for acteur_ref, mandat_periodes in periodes.items():
        slug = slugs.get(acteur_ref)
        if not slug:
            continue
        membres.append({
            "slug": slug,
            "slug_origine": origines.get(acteur_ref),
            "acteur_ref": acteur_ref,
            "nom": (index_gouvernements.get("acteurs") or {}).get(acteur_ref),
            "mandat_periodes": sorted(
                mandat_periodes, key=lambda p: (p["debut"] or "", p["libelle_an"] or "")),
        })
    return sorted(membres, key=lambda m: m["slug"])
