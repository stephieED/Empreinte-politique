#!/usr/bin/env python3
"""
perimetre_candidats.py — Qui le run collecte, et qui il a cessé de collecter (#760).

## Le défaut

`prepare-an-matrix` retenait tout candidat **à slug résolvable**, et rien
d'autre : `[c["slug"] for c in data["candidats"] if c.get("slug")]`. Une
candidature déclinée gardait donc son shard. Au 07/09/2026 c'était 2 shards sur
29 — Wauquiez et Bardella, passés `decline` par #753 — et cette part ne fait que
croître : l'article des candidatures compte déjà **24** personnes sous
« Candidats pressentis ayant décliné », et la campagne les multipliera à mesure
qu'elle tranche.

Collecter quelqu'un qui a renoncé, c'est payer un shard en série
(`max-parallel: 1`) pour rafraîchir une fiche que plus rien ne fait bouger.

## Ce que « geler » veut dire, et ce que ça ne veut pas dire

**Le profil n'est pas supprimé.** Il reste publié, avec les données de sa
dernière collecte. Supprimer un fichier publié est une disparition
qu'`audit_diff_profils` bloque (#460/#470), et ce n'est pas ce qu'on cherche :
ce que la personne a fait au Parlement reste vrai, seule sa candidature a cessé.
C'est le régime des deux fiches de groupe Sénat de #528 — gardées, gelées,
déclarées.

**Rien n'est perdu à la fusion non plus** : ne pas collecter ne produit pas une
collecte vide, ça ne produit *aucune* collecte. La fusion additive n'a rien à
écraser, le contrôle de perte ne voit aucune perte, et la §5b garde son entrée de
correspondance intacte.

**Le gel se lève tout seul.** Si la personne redéclare, `statut` repasse à
`declare` au job de tête et son shard revient au run suivant. Aucune intervention.

## Un statut inconnu est COLLECTÉ, jamais écarté

`STATUTS_GELES` est fermé, et c'est le seul ensemble fermé ici :
`est_a_collecter` rend vrai pour tout ce qui n'y est pas, y compris une valeur
que ce module ne connaît pas encore. Le défaut penche donc vers **collecter de
trop** plutôt que vers **écarter en silence** — parce que les deux erreurs ne
coûtent pas la même chose. Une collecte en trop coûte un shard ; un candidat
écarté par une valeur de statut ajoutée ailleurs disparaît du périmètre sans que
rien ne le dise, et c'est le patron de #510.

## Le gel se DÉCLARE

`slugs_geles()` existe pour ça, et ses appelants l'impriment : un candidat qui
sort du périmètre doit être nommé à l'endroit où le périmètre est calculé. Un
trou muet se lit comme un constat (#510, #501).
"""

from __future__ import annotations

import json
from typing import Any, Iterable

#: Les statuts dont la collecte est **gelée**. Fermé, et volontairement petit :
#: tout le reste est collecté. `decline` est entré avec #753, quand le fichier a
#: reçu de quoi dire qu'une candidature est abandonnée.
STATUTS_GELES = frozenset({"decline"})


def est_a_collecter(candidat: Any) -> bool:
    """Vrai si ce candidat doit recevoir un shard de collecte.

    Deux conditions, et une seule est un filtre de périmètre :

    1. il a un **slug** — sans lui il n'y a pas de profil à écrire, c'est la
       règle de `prepare-an-matrix` depuis #344 et elle ne change pas ;
    2. son statut n'est **pas gelé**.
    """
    if not isinstance(candidat, dict):
        return False
    slug = candidat.get("slug")
    if not isinstance(slug, str) or not slug:
        return False
    return candidat.get("statut") not in STATUTS_GELES


def slugs_a_collecter(candidats: Iterable[Any]) -> list[str]:
    """Les slugs du périmètre de collecte, dans l'ordre du fichier."""
    return [c["slug"] for c in candidats if est_a_collecter(c)]


def slugs_geles(candidats: Iterable[Any]) -> list[tuple[str, str]]:
    """`(slug, statut)` des candidats à slug dont la collecte est gelée.

    Rendu pour être **imprimé**, pas seulement compté : c'est ce qui distingue
    un périmètre réduit d'un périmètre amputé.
    """
    return [
        (c["slug"], c.get("statut"))
        for c in candidats
        if isinstance(c, dict)
        and isinstance(c.get("slug"), str)
        and c["slug"]
        and c.get("statut") in STATUTS_GELES
    ]


#: Fichier de résolutions d'identifiants du run, écrit par le job de tête
#: (#757) et lu ici **en lecture seule**. Défaut aligné sur le nom que
#: `generate-data.yml` publie dans l'artifact `candidats-a-jour`.
RESOLUTIONS_PAR_DEFAUT = "raw_data/resolutions_candidats.json"

#: Mémo de lecture : ce fichier est relu une fois par candidat dans un shard,
#: et il ne change pas pendant un run.
_MEMO_RESOLUTIONS: dict[str, dict[str, Any]] = {}


def vider_memo_resolutions() -> None:
    """Vide le mémo — pour les tests, qui changent de fichier entre deux cas."""
    _MEMO_RESOLUTIONS.clear()


def declare_hors_an_par_identifiant(
    nom: str, chemin: Any = RESOLUTIONS_PAR_DEFAUT
) -> bool:
    """Vrai si un identifiant externe déclare que cette personne n'a aucun mandat AN.

    C'est la **seconde déclaration** admise par #775, à côté de l'entrée relue de
    la table (#539). Elle existe pour ouvrir un verrou que rien d'autre ne
    pouvait ouvrir : sans profil publié, pas d'entrée de table (filtre 2 de
    #715) ; sans entrée de table, pas de profil. Cinq candidats déclarés y sont
    restés, et aucun run futur ne les aurait débloqués.

    **`indetermine` ne vaut PAS déclaration.** « Wikidata ne décrit pas cette
    personne » et « Wikidata la décrit et ne lui connaît aucun mandat AN » sont
    deux affirmations différentes, et une seule est un fait (#757). Un fichier
    absent, illisible ou muet sur ce nom rend `False` : l'absence de preuve
    n'est pas une preuve d'absence, et l'appelant retombe alors sur son
    comportement d'avant.

    Ce qui protège du faux constat n'est pas cette fonction mais la garde
    `en_echec` de son appelant : une collecte en panne rend le même vide qu'une
    absence, et le squelette n'est jamais écrit dessus (#484).
    """
    if not chemin:
        return False
    cle = str(chemin)
    if cle not in _MEMO_RESOLUTIONS:
        try:
            with open(cle, encoding="utf-8") as fichier:
                document = json.load(fichier)
            _MEMO_RESOLUTIONS[cle] = document.get("resolutions") or {}
        except (OSError, json.JSONDecodeError):
            _MEMO_RESOLUTIONS[cle] = {}
    resolution = _MEMO_RESOLUTIONS[cle].get(nom)
    return bool(resolution) and resolution.get("issue") == "hors_an"


# ---------------------------------------------------------------------------
# Le run de test : le même workflow, sur quelques slugs, sans commit
# ---------------------------------------------------------------------------
#
# POURQUOI CETTE FONCTION EXISTE. Un défaut d'orchestration se paie
# aujourd'hui **1 h 15** : c'est le temps qu'a mis le run `34264027824` pour
# révéler qu'un nom n'était pas transmis (#788). Un test unitaire l'aurait vu en
# une demi-seconde, et c'est le bon remède pour ce défaut-là — mais tout n'est
# pas testable hors CI : le transport des artifacts (#786) ne se voit que dans
# un run réel, et il n'a rien à faire de la taille du périmètre.
#
# Le mode de test ne change donc **ni le workflow, ni le code, ni l'ordre des
# jobs** : il réduit la matrice, et rien d'autre. Un mode qui divergerait du
# mode réel ne prouverait rien de ce qu'on lui demande de prouver.


def slugs_demandes(saisie: Any) -> list[str]:
    """Les slugs saisis dans le formulaire, séparés par des virgules.

    Tolère les espaces, les points-virgules et les retours à la ligne : une
    liste se colle depuis un log ou un tableau aussi souvent qu'elle se tape.
    """
    if not isinstance(saisie, str):
        return []
    brut = saisie.replace(";", ",").replace("\n", ",")
    return [morceau.strip() for morceau in brut.split(",") if morceau.strip()]


def restreindre_au_test(
    slugs: Iterable[str], saisie: Any
) -> tuple[list[str], list[str]]:
    """`(retenus, introuvables)` — la matrice réduite, et ce qui n'a pas matché.

    Les retenus gardent l'ordre du **périmètre**, pas celui de la saisie : le
    run doit se comporter comme un run ordinaire amputé, pas comme une liste
    rejouée dans un autre ordre.

    **Les introuvables sont rendus pour être nommés.** Un slug mal tapé, ou
    gelé par #760, disparaît sans bruit d'une intersection — et un run de test
    qui collecte zéro profil parce qu'on a écrit `marine-lepen` se lit comme un
    run qui n'a rien trouvé. C'est le patron de #510, sur une troisième
    population.
    """
    voulus = slugs_demandes(saisie)
    if not voulus:
        return list(slugs), []
    disponibles = list(slugs)
    ensemble = set(voulus)
    retenus = [s for s in disponibles if s in ensemble]
    introuvables = [s for s in voulus if s not in set(disponibles)]
    return retenus, introuvables


def est_run_de_test(saisie: Any) -> bool:
    """Vrai dès qu'un slug est demandé — c'est ce qui désarme le commit.

    Un seul champ porte les deux effets, et c'est délibéré : deux cases à
    cocher indépendantes autoriseraient la combinaison « périmètre réduit ET
    commit », c'est-à-dire publier un corpus dont on sait qu'il est partiel.
    """
    return bool(slugs_demandes(saisie))
