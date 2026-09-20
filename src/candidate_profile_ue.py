#!/usr/bin/env python3
"""
candidate_profile_ue.py

Récupère le volet "mandat européen" du CV politique d'un candidat, à partir
de l'Open Data Portal officiel du Parlement européen :
    https://data.europarl.europa.eu/api/v2/

Cette API est publiée par le Parlement européen sous licence ouverte
CC BY 4.0 (Creative Commons Attribution 4.0 International) : sa réutilisation
est explicitement autorisée, y compris à des fins commerciales, à condition
de créditer la source (voir la licence dans le champ `info.license` du
document OpenAPI exposé par l'API elle-même, et le README du dépôt).
Elle impose en revanche deux règles techniques à respecter :
  - un en-tête HTTP `User-Agent` identifiant le projet réutilisateur
    (voir la constante HEADERS ci-dessous) ;
  - une limite de 500 requêtes / 5 minutes par appelant.

Ce script ne cherche PAS à deviner si un candidat a été eurodéputé : il
interroge la liste complète (et publique) des députés européens ayant
représenté la France depuis l'origine du Parlement européen, et ne retient
que les correspondances exactes de nom. Un candidat non trouvé n'est pas
une erreur : il n'a simplement jamais été membre du Parlement européen.

Usage (depuis la racine du dépôt) :
    python src/candidate_profile_ue.py "Jordan Bardella"
    python src/candidate_profile_ue.py "Jordan Bardella" --out raw_data/profiles/jordan-bardella.ue.json

Docs API (spécification OpenAPI complète) : https://data.europarl.europa.eu/api/v2/
"""

import argparse
import json
import re
import threading
import time
import unicodedata
from pathlib import Path
from typing import Any, Optional

import requests

EP_API_BASE = "https://data.europarl.europa.eu/api/v2"

# Le Parlement européen recommande explicitement d'identifier le projet
# réutilisateur dans le User-Agent (voir doc du paramètre "User-Agent" de
# l'API), sans y inclure de données personnelles.
HEADERS = {
    "User-Agent": "CV-CandidatFR-dev-1.0.0 (https://github.com/, usage personnel / non commercial)"
}

TIMEOUT = 20
CACHE_DIR = Path(".cache") / "europarl"

# Verrou global pour les accès au cache disque des organisations (lecture + écriture).
# En mode parallèle, chaque thread charge une copie indépendante du cache en entrée,
# travaille localement, puis fusionne-et-sauvegarde sous ce verrou de façon à ne pas
# écraser les nouvelles entrées ajoutées par un thread concurrent entre-temps.
_ORG_CACHE_LOCK = threading.Lock()

# Libellés FR lisibles pour les classifications d'organisation rencontrées dans
# `hasMembership[].membershipClassification` (valeurs brutes = URI de type
# "def/ep-entities/XXX", non documentées sous forme d'enum dans la spec OpenAPI :
# établi par observation des données réelles).
CLASSIFICATION_LABELS = {
    "def/ep-entities/COMMITTEE_PARLIAMENTARY_STANDING": "Commission parlementaire permanente",
    "def/ep-entities/COMMITTEE_PARLIAMENTARY_TEMPORARY": "Commission parlementaire spéciale/temporaire",
    "def/ep-entities/COMMITTEE_PARLIAMENTARY_SUB": "Sous-commission parlementaire",
    "def/ep-entities/DELEGATION_PARLIAMENTARY": "Délégation interparlementaire",
    "def/ep-entities/DELEGATION_PARLIAMENTARY_ASSEMBLY": "Délégation à une assemblée parlementaire",
    "def/ep-entities/WORKING_GROUP": "Groupe de travail",
    "def/ep-entities/EU_POLITICAL_GROUP": "Groupe politique européen",
    "def/ep-entities/NATIONAL_POLITICAL_GROUP": "Parti national (au sein du groupe européen)",
    "def/ep-entities/GOVERNING_BODY": "Organe de direction du Parlement européen",
    "def/ep-entities/EU_INSTITUTION": "Mandat de député européen",
}

# Idem pour `hasMembership[].role` (valeurs brutes "def/ep-roles/XXX").
ROLE_LABELS = {
    "def/ep-roles/MEMBER": "Membre",
    "def/ep-roles/MEMBER_SUBSTITUTE": "Membre suppléant(e)",
    "def/ep-roles/MEMBER_PARLIAMENT": "Membre du Parlement européen",
    "def/ep-roles/CHAIR": "Président(e)",
    "def/ep-roles/CHAIR_CO": "Coprésident(e)",
    "def/ep-roles/VICE_CHAIR": "Vice-président(e)",
    "def/ep-roles/TREASURER": "Trésorier(ère)",
    "def/ep-roles/TREASURER_CO": "Co-trésorier(ère)",
}


def _prettify_uri(value: Optional[str]) -> Optional[str]:
    """Filet de secours pour un rôle/classification non présent dans les tables
    de libellés ci-dessus : transforme "def/ep-roles/SOME_NEW_ROLE" en
    "Some new role" plutôt que d'afficher l'URI brute."""
    if not value:
        return None
    tail = value.rsplit("/", 1)[-1]
    return tail.replace("_", " ").capitalize()


def _normalize_name(name: str) -> str:
    """Normalise un nom de personne pour comparaison insensible aux accents,
    à la casse, à la ponctuation et à l'ordre des mots (le libellé de l'API
    est "PRÉNOM NOM", alors que raw_data/candidats.json utilise "Prénom Nom")."""
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    tokens = re.findall(r"[A-Za-z0-9]+", ascii_only.upper())
    return " ".join(sorted(tokens))


def _get_json(path: str, params: Optional[dict[str, Any]] = None) -> Optional[dict]:
    """Effectue un GET sur l'API Open Data du Parlement européen et renvoie le
    JSON décodé, ou None si l'API répond "204 No Content" (aucun résultat)."""
    request_params = {"format": "application/ld+json"}
    if params:
        request_params.update(params)
    response = requests.get(
        f"{EP_API_BASE}{path}", params=request_params, headers=HEADERS, timeout=TIMEOUT
    )
    if response.status_code == 204:
        return None
    response.raise_for_status()
    return response.json()


def fetch_all_meps_by_country(country: str = "FR", use_cache: bool = True) -> list[dict[str, Any]]:
    """Récupère la liste complète (toutes législatures confondues, depuis
    l'origine du Parlement européen) des député⋅e⋅s européen⋅ne⋅s ayant
    représenté `country` (code ISO 3166-1 alpha-2, ex. "FR").

    Le résultat est mis en cache sur disque (.cache/europarl/meps_<pays>.json)
    car cette liste est volumineuse (plusieurs centaines d'entrées) et ne
    change quasiment jamais pour les législatures passées.
    """
    cache_path = CACHE_DIR / f"meps_{country}.json"
    if use_cache and cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)

    meps: list[dict[str, Any]] = []
    offset = 0
    limit = 100
    while True:
        payload = _get_json(
            "/meps",
            {"country-of-representation": country, "limit": limit, "offset": offset},
        )
        items = (payload or {}).get("data", [])
        if not items:
            break
        meps.extend(items)
        offset += limit
        time.sleep(0.2)  # on reste courtois avec l'API (limite : 500 req / 5 min)

    if use_cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(meps, f, ensure_ascii=False, indent=2)

    return meps


def find_mep_by_name(nom: str, country: str = "FR", use_cache: bool = True) -> Optional[dict[str, Any]]:
    """Cherche, par correspondance exacte de nom (normalisée), un⋅e
    député⋅e européen⋅ne parmi ceux ayant représenté `country`.

    Renvoie l'entrée brute de l'API (avec au moins `identifier` et `label`),
    ou None si le nom ne correspond à aucun eurodéputé connu.
    """
    target = _normalize_name(nom)
    for mep in fetch_all_meps_by_country(country, use_cache=use_cache):
        if _normalize_name(mep.get("label", "")) == target:
            return mep
    return None


def fetch_mep_detail(mep_id: str) -> Optional[dict[str, Any]]:
    """Récupère la fiche complète d'un⋅e député⋅e européen⋅ne (identité,
    et historique complet des mandats/fonctions via `hasMembership`)."""
    payload = _get_json(f"/meps/{mep_id}")
    items = (payload or {}).get("data", [])
    return items[0] if items else None


def resolve_organization(org_id: str, cache: dict[str, Any]) -> dict[str, Any]:
    """Résout l'identifiant d'une organisation (commission, groupe politique,
    délégation...) en un nom lisible, avec mise en cache mémoire+disque
    (beaucoup de mandats différents référencent la même organisation).

    `org_id` est de la forme "org/6364" ou parfois "org/ep-7" (législature :
    non résolvable via /corporate-bodies, traité à part par l'appelant).
    """
    if org_id in cache:
        return cache[org_id]

    identifier = org_id.split("/", 1)[-1]
    resolved: dict[str, Any] = {"sigle": identifier, "nom_complet": None}
    for attempt in range(2):  # une nouvelle tentative en cas de timeout/erreur réseau transitoire
        try:
            payload = _get_json(f"/corporate-bodies/{identifier}")
            items = (payload or {}).get("data", [])
            if items:
                item = items[0]
                resolved["sigle"] = item.get("label") or identifier
                pref_label = item.get("prefLabel") or {}
                alt_label = item.get("altLabel") or {}
                resolved["nom_complet"] = pref_label.get("fr") or alt_label.get("fr") or resolved["sigle"]
            break
        except requests.RequestException:
            if attempt == 0:
                time.sleep(1)
                continue
            pass  # organisation non résolvable après 2 tentatives : on garde le sigle brut

    time.sleep(0.15)  # on reste courtois avec l'API (limite : 500 req / 5 min)
    cache[org_id] = resolved
    return resolved


def _load_org_cache() -> dict[str, Any]:
    cache_path = CACHE_DIR / "organisations.json"
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_org_cache(cache: dict[str, Any]) -> None:
    cache_path = CACHE_DIR / "organisations.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _extract_mandats_europeens(mep_detail: dict[str, Any], org_cache: dict[str, Any]) -> list[dict[str, Any]]:
    """Transforme `hasMembership` (liste brute de l'API) en une liste de
    mandats/fonctions triée du plus récent au plus ancien, avec libellés FR
    et noms d'organisation résolus."""
    mandats = []
    for membership in mep_detail.get("hasMembership") or []:
        period = membership.get("memberDuring") or {}
        debut = period.get("startDate")
        fin = period.get("endDate")
        classification = membership.get("membershipClassification")
        org_id = membership.get("organization")

        if org_id and str(org_id).split("/", 1)[-1].startswith("ep-"):
            # Entrée "législature" (org/ep-7, org/ep-8...) : pas une vraie
            # organisation, pas de fiche /corporate-bodies associée.
            legislature = str(org_id).split("-", 1)[-1]
            organisation = {"sigle": f"{legislature}e législature", "nom_complet": "Mandat de député européen"}
        else:
            organisation = resolve_organization(org_id, org_cache) if org_id else {"sigle": None, "nom_complet": None}

        mandats.append({
            "type": (classification or "AUTRE").rsplit("/", 1)[-1],
            "type_label": CLASSIFICATION_LABELS.get(classification) or _prettify_uri(classification) or "Autre",
            "organisation_sigle": organisation.get("sigle"),
            "organisation_nom": organisation.get("nom_complet"),
            "role": (membership.get("role") or "").rsplit("/", 1)[-1] or None,
            "role_label": ROLE_LABELS.get(membership.get("role")) or _prettify_uri(membership.get("role")),
            "debut": debut,
            "fin": fin,
            "actif": fin is None,
        })

    mandats.sort(key=lambda m: m.get("debut") or "", reverse=True)
    return mandats


def build_profile_ue(nom: str, country: str = "FR", use_cache: bool = True) -> Optional[dict[str, Any]]:
    """Construit le volet "mandat européen" du CV politique d'un candidat.

    Args:
        nom: nom complet du candidat tel qu'il apparaît dans raw_data/candidats.json.
            (ex. "Jordan Bardella"). La correspondance se fait par égalité
            exacte du nom normalisé (accents/casse/ordre des mots ignorés).
        country: code pays (ISO 3166-1 alpha-2) parmi lequel chercher le
            candidat (défaut : "FR").
        use_cache: réutiliser le cache disque de la liste des eurodéputés
            (.cache/europarl/) plutôt que de la re-télécharger à chaque appel.

    Returns:
        None si le candidat n'a jamais été eurodéputé (aucune correspondance
        trouvée), sinon un dict directement sérialisable en JSON.
    """
    mep_entry = find_mep_by_name(nom, country=country, use_cache=use_cache)
    if mep_entry is None:
        return None

    mep_id = mep_entry.get("identifier")
    detail = fetch_mep_detail(mep_id) or mep_entry

    # Chargement du cache organisations sous verrou (copie locale pour ne pas
    # bloquer les autres threads pendant les appels réseau de résolution).
    with _ORG_CACHE_LOCK:
        org_cache = dict(_load_org_cache())
    mandats = _extract_mandats_europeens(detail, org_cache)
    # Sauvegarde avec fusion : on recharge le cache courant sous verrou et on y
    # ajoute uniquement les nouvelles entrées (évite d'écraser le travail d'un
    # thread concurrent qui aurait ajouté des entrées entre-temps).
    with _ORG_CACHE_LOCK:
        current = _load_org_cache()
        current.update(org_cache)
        _save_org_cache(current)

    return {
        "identifiant_pe": mep_id,
        "nom_complet": detail.get("label"),
        "date_naissance": detail.get("bday"),
        "lieu_naissance": detail.get("placeOfBirth"),
        "photo": detail.get("img") or f"https://www.europarl.europa.eu/mepphoto/{mep_id}.jpg",
        "url_source": f"https://www.europarl.europa.eu/meps/fr/{mep_id}",
        "mandats_europeens": mandats,
        "meta": {
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": "CC BY 4.0 (Parlement européen, Open Data Portal - data.europarl.europa.eu)",
            "source_api": EP_API_BASE,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("nom", help='Nom complet du candidat, ex: "Jordan Bardella"')
    parser.add_argument("--country", default="FR", help="Code pays ISO 3166-1 alpha-2 (défaut: FR)")
    parser.add_argument("--out", help="Chemin du fichier JSON de sortie (défaut: affichage sur stdout)")
    parser.add_argument("--no-cache", action="store_true", help="Ignorer le cache disque de la liste des eurodéputés")
    args = parser.parse_args()

    profile_ue = build_profile_ue(args.nom, country=args.country, use_cache=not args.no_cache)

    if profile_ue is None:
        print(f"— {args.nom} : aucune correspondance trouvée parmi les eurodéputé⋅e⋅s représentant {args.country}.")
        return

    output = json.dumps(profile_ue, ensure_ascii=False, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        nb = len(profile_ue["mandats_europeens"])
        print(f"✓ {args.nom} : {nb} mandat(s)/fonction(s) européen(s) écrit(s) dans {out_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
