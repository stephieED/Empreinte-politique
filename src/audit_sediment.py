#!/usr/bin/env python3
"""
audit_sediment.py — Compte, famille par famille, ce que le corpus publié garde
d'une source que le pipeline n'interroge plus (#839, lot A).

Pourquoi
--------
La fusion est **additive aux deux étages** : une entrée écrite une fois reste
publiée, même quand le code qui l'a produite a disparu. #529 a changé de source
pour les débats, #528 a retiré le Sénat, #718 a marqué les catégories de mandat
que plus personne n'établit — et à chaque fois le corpus a gardé l'ancien.

Personne ne savait **où**. Ce script répond à cette question et à elle seule :
il **ne retire rien**, il ne juge pas, il compte. Les verdicts de
reproductibilité sont le lot B ; les retraits, le lot D.

Il se relance après chaque run : une famille revenue à zéro qui remonte est une
régression, et c'est la seule façon de la voir.

Les familles, et leur signature
-------------------------------
Chaque famille est une **signature de forme**, jamais un nom de source : ce que
le pipeline vivant produit se reconnaît, ce qu'il ne produit plus aussi.

  1. `interventions[]` — identifiant **entier**. Syceron rend `syceron_…`, les
     questions officielles `question_…`, le Parlement européen `europarl_…` :
     aucune source vivante ne rend d'entier (#839).
  2. `interventions[]` — `source_url` portant un motif de Regards Citoyens,
     lus dans `licences.MOTIFS_URL_REGARDS_CITOYENS`. Recoupe la famille 1
     sans s'y réduire : les deux sont comptées.
  3. `mandats[]` — `categorie_source` **absente** : « personne n'a établi cette
     catégorie » (#718). Ce n'est pas une accusation, c'est un fait sur le
     champ.
  4. `mandats[]` — **aucune date et `actif: true`** : la fiche publie une
     appartenance en cours que rien ne date. Sous-ensemble attendu de la
     famille 3, compté à part parce qu'il ne coûte pas le même arbitrage.
  5. `sources[]` — un `type` dont la licence est celle de Regards Citoyens,
     lus dans `licences.LICENCE_PAR_TYPE_SOURCE`. C'est le marqueur qui porte
     la clause ODbL (§7), pas une donnée.
  6. `meta.avertissements[]` / `meta.warnings[]` — un message hérité, reconnu
     par les tables `AVERTISSEMENTS_HERITES` / `PREFIXES_HERITES` que
     `avertissements.py` tient déjà, ou portant un motif d'URL.
  7. `couverture[].preuve` — une preuve de couverture qui cite la source
     retirée. Texte publié, lu par un humain.

Ce que le compte 3 mélange, et qu'il faut savoir avant d'en tirer un verdict
-----------------------------------------------------------------------------
Un mandat sans `categorie_source` n'est pas forcément d'origine française :
mesuré le 12/09/2026, **21 des 406 sont des organes du Parlement européen**, sur
**2 profils** (commissions parlementaires, délégations, groupe politique
européen, portés par `mandat_europeen` côté brut). Les confronter au référentiel
AMO30 les déclarerait « introuvables » alors qu'ils le sont ailleurs. Le verdict
de reproductibilité (lot B) doit donc interroger **les deux** référentiels.

Usage (depuis la racine du dépôt) :
    python3 src/audit_sediment.py                          # les deux couches
    python3 src/audit_sediment.py --profiles-dir pivot_data/profiles
    python3 src/audit_sediment.py --json rapport.json
    python3 src/audit_sediment.py --par-profil              # le détail, profil par profil
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from avertissements import AVERTISSEMENTS_HERITES, PREFIXES_HERITES
from licences import LICENCE_PAR_TYPE_SOURCE, LICENCE_REGARDS_CITOYENS, MOTIFS_URL_REGARDS_CITOYENS
from population_profils import Ventilation, provenance_du_profil, ventiler_provenances

COUCHES_PAR_DEFAUT = (Path("raw_data") / "profiles", Path("pivot_data") / "profiles")

#: Types de `sources[]` dont la licence est celle de Regards Citoyens. Dérivé,
#: jamais recopié : le jour où un type change de licence, l'audit suit.
TYPES_SOURCE_RETIRES = frozenset(
    type_source
    for type_source, licence in LICENCE_PAR_TYPE_SOURCE.items()
    if licence == LICENCE_REGARDS_CITOYENS
)


def _identifiant(entree: dict[str, Any]) -> Any:
    """Le brut nomme la clé `id`, le pivot `intervention_id`."""
    return entree.get("intervention_id", entree.get("id"))


def _url_de_l_entree(entree: dict[str, Any]) -> Any:
    """Le pivot publie `source_url` ; le brut garde `url`, l'adresse d'API
    d'origine. Ne lire que l'un des deux rend 0 sur une couche qui en porte 511.
    """
    return entree.get("source_url") or entree.get("url")


def _porte_un_motif(valeur: Any) -> bool:
    return isinstance(valeur, str) and any(m in valeur for m in MOTIFS_URL_REGARDS_CITOYENS)


def _liste(profil: dict[str, Any], cle: str) -> list[Any]:
    valeur = profil.get(cle)
    return valeur if isinstance(valeur, list) else []


# ---------------------------------------------------------------------------
# Les sept détecteurs. Chacun rend les entrées de SON profil, jamais un compte.
# ---------------------------------------------------------------------------

def interventions_a_identifiant_entier(profil: dict[str, Any]) -> list[Any]:
    return [
        e for e in _liste(profil, "interventions")
        if isinstance(e, dict)
        and isinstance(_identifiant(e), int)
        and not isinstance(_identifiant(e), bool)
    ]


def interventions_liees_a_la_source_retiree(profil: dict[str, Any]) -> list[Any]:
    return [
        e for e in _liste(profil, "interventions")
        if isinstance(e, dict) and _porte_un_motif(_url_de_l_entree(e))
    ]


def mandats_sans_categorie_source(profil: dict[str, Any]) -> list[Any]:
    return [
        m for m in _liste(profil, "mandats")
        if isinstance(m, dict) and m.get("categorie_source") is None
    ]


def mandats_actifs_sans_dates(profil: dict[str, Any]) -> list[Any]:
    return [
        m for m in _liste(profil, "mandats")
        if isinstance(m, dict) and m.get("actif") is True
        and not m.get("debut") and not m.get("fin")
    ]


def sources_retirees(profil: dict[str, Any]) -> list[Any]:
    return [
        s for s in _liste(profil, "sources")
        if isinstance(s, dict) and s.get("type") in TYPES_SOURCE_RETIRES
    ]


def _est_herite(message: str) -> bool:
    """Le message est-il une formulation qu'aucun code n'écrit plus ?

    Les deux tables vivent dans `avertissements.py`, qui les tient pour donner
    un destinataire aux avertissements publiés d'avant (#642) : les recopier ici
    en ferait une seconde vérité.
    """
    return message in AVERTISSEMENTS_HERITES or any(
        message.startswith(prefixe) for prefixe, _ in PREFIXES_HERITES
    )


def avertissements_herites(profil: dict[str, Any]) -> list[Any]:
    meta = profil.get("meta")
    if not isinstance(meta, dict):
        return []
    messages = _liste(meta, "avertissements") + _liste(meta, "warnings")
    trouves = []
    for message in messages:
        texte = message.get("message") if isinstance(message, dict) else message
        if not isinstance(texte, str):
            continue
        if _est_herite(texte) or _porte_un_motif(texte):
            trouves.append(message)
    return trouves


def preuves_de_couverture_citant_la_source(profil: dict[str, Any]) -> list[Any]:
    couverture = profil.get("couverture")
    if not isinstance(couverture, dict):
        return []
    trouves = []
    for entrees in couverture.values():
        for entree in entrees if isinstance(entrees, list) else []:
            if isinstance(entree, dict) and _porte_un_motif(entree.get("preuve")):
                trouves.append(entree)
    return trouves


@dataclass(frozen=True)
class Famille:
    cle: str
    libelle: str
    detecte: Callable[[dict[str, Any]], list[Any]]
    #: Clés de premier niveau que la famille lit. Une couche qui n'en porte
    #: aucune n'a pas « zéro entrée » : elle n'a pas le champ, et un `0` s'y
    #: lirait comme un constat (§2 règle 5).
    cles_lues: tuple[str, ...] = ()


FAMILLES: tuple[Famille, ...] = (
    Famille("interventions_id_entier", "`interventions[]` à identifiant entier",
            interventions_a_identifiant_entier, ("interventions",)),
    Famille("interventions_url_source_retiree", "`interventions[]` dont l'URL cite la source retirée",
            interventions_liees_a_la_source_retiree, ("interventions",)),
    Famille("mandats_sans_categorie_source", "`mandats[]` sans `categorie_source`",
            mandats_sans_categorie_source, ("mandats",)),
    Famille("mandats_actifs_sans_dates", "`mandats[]` actifs et sans aucune date",
            mandats_actifs_sans_dates, ("mandats",)),
    Famille("sources_retirees", "`sources[]` sous licence Regards Citoyens",
            sources_retirees, ("sources",)),
    Famille("avertissements_herites", "`meta` — avertissement hérité",
            avertissements_herites, ("meta",)),
    Famille("preuves_couverture", "`couverture[].preuve` citant la source retirée",
            preuves_de_couverture_citant_la_source, ("couverture",)),
)


@dataclass
class Compte:
    entrees: int = 0
    provenances: list[str] = field(default_factory=list)

    @property
    def ventilation(self) -> Ventilation:
        return ventiler_provenances(self.provenances)

    def as_dict(self) -> dict[str, Any]:
        return {"entrees": self.entrees, "profils": self.ventilation.as_dict()}


def auditer_profil(profil: dict[str, Any]) -> dict[str, list[Any]]:
    """Les entrées sédimentées d'un profil, famille par famille."""
    return {famille.cle: famille.detecte(profil) for famille in FAMILLES}


def auditer_repertoire(repertoire: Path) -> tuple[dict[str, Compte], Ventilation, list[Path], set[str], bool]:
    """Parcourt une couche. Rend (comptes, population, illisibles, clés vues, provenance portée).

    Les tranches d'amendements (`<slug>/<legislature>.json`) et les fichiers de
    cosignatures ne sont pas ouverts : aucune famille n'y vit, et ils pèsent
    l'essentiel du répertoire (#580).
    """
    comptes = {famille.cle: Compte() for famille in FAMILLES}
    provenances: list[str] = []
    illisibles: list[Path] = []
    cles_vues: set[str] = set()
    provenance_portee = False
    for chemin in sorted(repertoire.glob("*.json")):
        if chemin.name.endswith(".cosignatures.json"):
            continue
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            illisibles.append(chemin)
            continue
        if not isinstance(profil, dict):
            illisibles.append(chemin)
            continue
        cles_vues.update(k for k in profil if isinstance(k, str))
        meta = profil.get("meta")
        if isinstance(meta, dict) and meta.get("provenance") is not None:
            provenance_portee = True
        provenance = provenance_du_profil(profil)
        provenances.append(provenance)
        for cle, entrees in auditer_profil(profil).items():
            if entrees:
                comptes[cle].entrees += len(entrees)
                comptes[cle].provenances.append(provenance)
    return (comptes, ventiler_provenances(provenances, illisibles=len(illisibles)),
            illisibles, cles_vues, provenance_portee)


def _rendre(repertoire: Path, comptes: dict[str, Compte], population: Ventilation,
            cles_vues: set[str], provenance_portee: bool) -> str:
    """Un tableau par couche. Deux refus délibérés :

    - une couche qui ne porte pas `meta.provenance` n'est **pas ventilée** : le
      brut rendrait « 1 181 candidats déclarés », ce qui est faux (#630) ;
    - une famille dont le champ est absent de la couche affiche `champ absent`,
      jamais `0` — l'absence de champ n'est pas l'absence de sédiment.
    """
    if provenance_portee:
        entete = population.ligne("Profils lus")
    else:
        entete = (f"Profils lus : {population.total} — couche sans `meta.provenance`, "
                  "non ventilée : la ventilation par population se lit au pivot (#630).")
    lignes = [f"### `{repertoire}`", "", entete, "",
              "| Famille | Entrées | Profils |", "| --- | ---: | --- |"]
    for famille in FAMILLES:
        compte = comptes[famille.cle]
        if not any(cle in cles_vues for cle in famille.cles_lues):
            lignes.append(f"| {famille.libelle} | *champ absent de cette couche* | — |")
            continue
        if not compte.entrees:
            profils = "—"
        elif provenance_portee:
            profils = compte.ventilation.cellule_markdown()
        else:
            profils = f"{compte.ventilation.total}"
        lignes.append(f"| {famille.libelle} | {compte.entrees} | {profils} |")
    return "\n".join(lignes)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profiles-dir", action="append", metavar="DOSSIER",
                        help="Couche à auditer. Répétable. Par défaut, les deux : "
                             "un sédiment retiré du seul brut ne descend jamais au pivot (#729).")
    parser.add_argument("--json", metavar="FICHIER", help="Écrit le rapport complet en JSON.")
    parser.add_argument("--par-profil", action="store_true",
                        help="Ajoute le détail profil par profil, pour les familles non vides.")
    args = parser.parse_args(argv)

    couches = [Path(d) for d in args.profiles_dir] if args.profiles_dir else list(COUCHES_PAR_DEFAUT)
    manquantes = [c for c in couches if not c.is_dir()]
    if manquantes:
        print(f"[!] Répertoire introuvable : {', '.join(str(c) for c in manquantes)}", file=sys.stderr)
        return 2

    rapport: dict[str, Any] = {"couches": {}}
    sections = []
    for couche in couches:
        comptes, population, illisibles, cles_vues, provenance_portee = auditer_repertoire(couche)
        sections.append(_rendre(couche, comptes, population, cles_vues, provenance_portee))
        rapport["couches"][str(couche)] = {
            "profils": population.as_dict() if provenance_portee else {"total": population.total},
            "provenance_portee": provenance_portee,
            "illisibles": [str(p) for p in illisibles],
            "familles": {cle: compte.as_dict() for cle, compte in comptes.items()},
        }
        if args.par_profil:
            sections.append(_detailler(couche))

    print("## Sédiment du corpus, par couche et par famille\n")
    print("\n\n".join(sections))
    print("\nAucune entrée n'a été retirée : cet audit compte, il ne juge pas.")

    if args.json:
        Path(args.json).write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"→ Rapport JSON : {args.json}")
    return 0


def _detailler(repertoire: Path) -> str:
    """Le détail par profil, réservé aux familles non vides."""
    lignes = ["", f"#### Détail — `{repertoire}`", "", "| Profil | Famille | Entrées |", "| --- | --- | ---: |"]
    for chemin in sorted(repertoire.glob("*.json")):
        if chemin.name.endswith(".cosignatures.json"):
            continue
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(profil, dict):
            continue
        slug = chemin.name.replace(".pivot.json", "").replace(".json", "")
        for famille in FAMILLES:
            entrees = famille.detecte(profil)
            if entrees:
                lignes.append(f"| `{slug}` | {famille.libelle} | {len(entrees)} |")
    return "\n".join(lignes)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
