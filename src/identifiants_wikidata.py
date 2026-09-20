#!/usr/bin/env python3
"""
identifiants_wikidata.py — Résout l'acteur AN d'un candidat par un identifiant
externe, jamais par son nom (#757).

## Pourquoi pas la correspondance par nom

`candidate_profile._resolve_acteur_ref_par_slug` sait déjà retomber sur une
correspondance **par nom** contre le référentiel AMO30 : elle normalise le slug
(`jean-luc-melenchon` → `jean luc melenchon`) et cherche l'acteur qui porte ce
nom complet. Elle refuse l'homonymie *interne* à AMO30 — deux acteurs pour une
clé, elle renonce — mais elle ne peut rien contre l'homonymie qui compte ici :
un candidat qui n'a jamais siégé et qui porte le nom d'un ancien député. Elle
rapprocherait les deux, et la fiche du candidat publierait les votes, les
amendements et les interventions de quelqu'un d'autre. C'est la pire erreur que
ce produit puisse commettre (§2 règle 2).

La chaîne d'ici passe donc par un **identifiant**, et le nom n'y sert jamais de
clé de rapprochement :

    article Wikipédia → pageprops.wikibase_item → P4123 → "PA" + valeur

`P4123` est l'identifiant Assemblée nationale porté par Wikidata, et sa valeur
est le numéro de l'acteur AMO30. **Validé 12/12 le 07/09/2026** contre les
entrées relues à la main de `raw_data/correspondance_acteurs_an.json` : les 9
candidats déclarés qui ont un acteur, plus les 3 déjà collectés par la voie du
roster (Ruffin `PA722142`, Brun `PA793624`, Faure `PA609332`). Aucune
divergence.

## Trois issues, et « indéterminé » n'est pas « hors AN »

| Issue | Ce qu'on sait | Ce qu'on en fait |
| --- | --- | --- |
| `ACTEUR` | `P4123` porte une valeur | l'`acteur_ref`, avec l'élément Wikidata pour preuve |
| `HORS_AN` | l'élément existe et ne porte **pas** `P4123` | un fait négatif **à corroborer** avant d'être écrit |
| `INDETERMINE` | pas d'article, ou pas d'élément | rien du tout — et le candidat reste sans slug, nommé |

La distinction entre les deux derniers est tout l'intérêt du module. « Wikidata
ne dit rien de cette personne » et « Wikidata décrit cette personne et ne lui
connaît aucun mandat AN » sont deux affirmations différentes, et une seule est
un fait (§2 règle 5).

## Une panne n'est jamais un fait négatif

Toute défaillance — réseau, HTTP, JSON illisible, réponse d'API en erreur —
lève `ResolutionIndisponible`. Aucun chemin ne rend `HORS_AN` par défaut : un
timeout qui se lirait « cette personne n'a jamais siégé » écrirait une entrée
`hors_an` fausse dans un artefact relu, et la publierait. C'est le patron de
#511, appliqué à une affirmation au lieu d'une liste.

## Ce module ne parle qu'au réseau, et il ne tourne jamais dans `merge-and-pivot`

Il est appelé par le job de tête, qui publie son résultat dans l'artifact. La
passe qui écrit les entrées de correspondance, elle, est **hors ligne** : une
panne de source tierce ne doit pas coûter le commit d'un run dont la donnée est
bonne, ce que #524 interdit et que #715 a inscrit dans la forme de sa propre
passe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Optional
from urllib.parse import quote

import requests

#: L'API des articles, pour l'étape article → élément.
API_WIKIPEDIA = "https://fr.wikipedia.org/w/api.php"

#: Le point SPARQL, pour l'étape élément → identifiant AN. Un `wbgetentities`
#: rendrait la même chose en **186 Ko pour 3 personnes** (mesuré le
#: 07/09/2026) : il n'a pas de filtre par propriété et sert l'élément entier.
#: La même question en SPARQL tient en **914 octets pour 5**.
SPARQL_WIKIDATA = "https://query.wikidata.org/sparql"

#: `P4123` — identifiant Assemblée nationale. Sa valeur est le numéro de
#: l'acteur AMO30, sans le préfixe.
PROPRIETE_ACTEUR_AN = "P4123"

PREFIXE_ACTEUR_AN = "PA"

HEADERS = {
    "User-Agent": (
        "EmpreintePolitique/1.0 "
        "(https://github.com/stephieED/Empreinte-politique-src) "
        "python-requests"
    )
}

TIMEOUT = 30

#: Les deux API acceptent des lots. 50 est la limite des clients anonymes de
#: l'API MediaWiki ; on s'y tient aussi côté SPARQL, où rien ne l'impose mais
#: où un lot plus gros allongerait la requête sans rien gagner.
TAILLE_LOT = 50


class ResolutionIndisponible(Exception):
    """La source n'a pas répondu. Ne jamais lire comme un fait négatif."""


class Issue(str, Enum):
    ACTEUR = "acteur"
    HORS_AN = "hors_an"
    INDETERMINE = "indetermine"


@dataclass(frozen=True)
class Resolution:
    """Ce qu'on sait d'un candidat après la chaîne, et d'où on le sait."""

    nom: str
    issue: Issue
    acteur_ref: Optional[str] = None
    qid: Optional[str] = None
    #: L'URL de l'élément Wikidata — la `preuve` que portera l'entrée de table.
    preuve: Optional[str] = None

    def en_dict(self) -> dict[str, Any]:
        return {
            "nom": self.nom,
            "issue": self.issue.value,
            "acteur_ref": self.acteur_ref,
            "qid": self.qid,
            "preuve": self.preuve,
        }


def url_element(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/{quote(qid)}"


def _lots(valeurs: list[Any], taille: int = TAILLE_LOT) -> Iterable[list[Any]]:
    for debut in range(0, len(valeurs), taille):
        yield valeurs[debut : debut + taille]


def _titre_depuis_url(url: Optional[str]) -> Optional[str]:
    """Le titre d'article porté par une URL `…/wiki/<titre>`, ou `None`.

    Une URL de **section** (`…#Candidats_déclarés`) n'est pas un article : c'est
    le repli que `fetch_candidats_declares` écrit quand la personne n'a pas de
    page, et la traiter comme un titre interrogerait l'article des candidatures
    une fois par candidat sans article.
    """
    if not url or "/wiki/" not in url:
        return None
    fragment = url.split("/wiki/", 1)[1]
    if "#" in fragment:
        return None
    from urllib.parse import unquote

    return unquote(fragment).replace("_", " ") or None


def resoudre_elements(titres: list[str], session: Any = None) -> dict[str, Optional[str]]:
    """`titre d'article → identifiant d'élément Wikidata` (ou `None`).

    Les redirections sont suivies (`redirects=1`) et **réécrites vers le titre
    demandé** : sans quoi un candidat dont l'article a été renommé sortirait de
    la correspondance sans un mot.

    Raises:
        ResolutionIndisponible: la source n'a pas répondu.
    """
    get = (session or requests).get
    resultats: dict[str, Optional[str]] = {titre: None for titre in titres}

    for lot in _lots([t for t in titres if t]):
        params = {
            "action": "query",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "redirects": "1",
            "format": "json",
            "titles": "|".join(lot),
        }
        try:
            reponse = get(API_WIKIPEDIA, params=params, headers=HEADERS, timeout=TIMEOUT)
            reponse.raise_for_status()
            charge = reponse.json()
        except requests.RequestException as exc:
            raise ResolutionIndisponible(f"Wikipédia (pageprops) : {exc}") from exc
        except ValueError as exc:
            raise ResolutionIndisponible(f"Wikipédia (pageprops) : réponse non JSON ({exc})") from exc

        requete = charge.get("query") or {}
        # `normalized` et `redirects` disent sous quel titre la réponse revient.
        alias: dict[str, str] = {}
        for etape in ("normalized", "redirects"):
            for saut in requete.get(etape) or []:
                alias[saut["to"]] = alias.get(saut["from"], saut["from"])

        for page in (requete.get("pages") or {}).values():
            titre_rendu = page.get("title")
            demande = alias.get(titre_rendu, titre_rendu)
            if demande in resultats:
                resultats[demande] = (page.get("pageprops") or {}).get("wikibase_item")

    return resultats


def resoudre_acteurs_an(qids: list[str], session: Any = None) -> dict[str, Optional[str]]:
    """`identifiant d'élément → acteur_ref AN` (ou `None` si l'élément n'en porte pas).

    Raises:
        ResolutionIndisponible: la source n'a pas répondu.
    """
    get = (session or requests).get
    resultats: dict[str, Optional[str]] = {qid: None for qid in qids}

    for lot in _lots([q for q in qids if q]):
        valeurs = " ".join(f"wd:{qid}" for qid in lot)
        requete = (
            f"SELECT ?item ?an WHERE {{ VALUES ?item {{ {valeurs} }} "
            f"OPTIONAL {{ ?item wdt:{PROPRIETE_ACTEUR_AN} ?an }} }}"
        )
        try:
            reponse = get(
                SPARQL_WIKIDATA,
                params={"query": requete, "format": "json"},
                headers={**HEADERS, "Accept": "application/sparql-results+json"},
                timeout=TIMEOUT,
            )
            reponse.raise_for_status()
            charge = reponse.json()
        except requests.RequestException as exc:
            raise ResolutionIndisponible(f"Wikidata (SPARQL) : {exc}") from exc
        except ValueError as exc:
            raise ResolutionIndisponible(f"Wikidata (SPARQL) : réponse non JSON ({exc})") from exc

        for ligne in ((charge.get("results") or {}).get("bindings") or []):
            qid = (ligne.get("item") or {}).get("value", "").rsplit("/", 1)[-1]
            valeur = (ligne.get("an") or {}).get("value")
            if qid in resultats and valeur:
                resultats[qid] = f"{PREFIXE_ACTEUR_AN}{valeur}"

    return resultats


def resoudre(
    candidats: list[dict[str, Any]], session: Any = None
) -> dict[str, Resolution]:
    """`nom → Resolution` pour une liste d'entrées de `candidats.json`.

    L'article se lit dans le champ `source` que `fetch_candidats_declares`
    écrit — l'URL de la page de la personne quand elle en a une, l'URL de la
    section sinon.

    Raises:
        ResolutionIndisponible: la source n'a pas répondu. Aucune résolution
            partielle n'est rendue : un lot à moitié résolu ferait écrire des
            `hors_an` pour les candidats du lot manquant.
    """
    titres = {}
    for candidat in candidats:
        titre = _titre_depuis_url(candidat.get("source"))
        if titre:
            titres[candidat["nom"]] = titre

    elements = resoudre_elements(sorted(set(titres.values())), session=session)
    qids = sorted({q for q in elements.values() if q})
    acteurs = resoudre_acteurs_an(qids, session=session) if qids else {}

    resolutions: dict[str, Resolution] = {}
    for candidat in candidats:
        nom = candidat["nom"]
        qid = elements.get(titres.get(nom, ""), None)
        if not qid:
            resolutions[nom] = Resolution(nom=nom, issue=Issue.INDETERMINE)
            continue
        acteur = acteurs.get(qid)
        resolutions[nom] = Resolution(
            nom=nom,
            issue=Issue.ACTEUR if acteur else Issue.HORS_AN,
            acteur_ref=acteur,
            qid=qid,
            preuve=url_element(qid),
        )
    return resolutions


def ecrire_resolutions(chemin, resolutions: dict[str, Resolution], le_jour: str) -> None:
    """Écrit le fichier que la passe hors ligne de `merge-and-pivot` relira."""
    document = {
        "schema_version": "resolutions-candidats-v1",
        "genere_le": le_jour,
        "propriete": PROPRIETE_ACTEUR_AN,
        "resolutions": {
            nom: resolution.en_dict() for nom, resolution in sorted(resolutions.items())
        },
    }
    chemin.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
