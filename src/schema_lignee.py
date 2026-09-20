#!/usr/bin/env python3
"""
schema_lignee.py — Contrat de la fiche de LIGNÉE de groupe parlementaire (#836).

## Ce qu'une lignée est, et ce qu'elle n'est pas

Une lignée est la suite des fiches qu'un même groupe a portées au fil des
législatures : `NG:15 → SOC:15 → SOC:16 → SOC:17`. Elle se lit sur `succede_a`,
qui est **une relecture humaine datée** — l'Assemblée ouvre et ferme des
organes, elle ne les chaîne pas (#700).

La propriétaire a tranché le 10/09/2026 : **l'interface ne publie qu'une fiche
par lignée**. Le corpus, lui, porte **les deux étages** — les maillons et la
lignée. Les maillons restent la matière : `position_politique` est publiée par
législature et ne se réunit pas, `effectif` et `periode` sont des plages par
fiche, `comparaison-<leg>.json` les consomme, et les retirer produirait 13
fichiers disparus au contrôle d'avant-commit.

## Pourquoi on ne peut pas additionner les maillons

Mesuré sur la lignée socialiste, corpus du 11/09/2026 :

| | Somme des 4 maillons | Union réelle |
| --- | ---: | ---: |
| `membres` | 170 | **96** |
| `cohesion_votes` | 20 524 | union par `scrutin_id` |
| `amendements_agreges` | 88 709 | **recalcul obligatoire** |

Un membre présent sous trois maillons y est compté trois fois. Les amendements
ne se dédoublonnent pas au niveau des fiches : il faut repasser par
`profiles[].amendements`.

## L'identifiant est DÉCLARÉ, jamais dérivé

`lignee_id` vient de `raw_data/groupes_reels.json`, comme `succede_a`. Les deux
dérivations possibles bougent :

- **par la racine** — change le jour où un maillon **antérieur** est déclaré, et
  c'est prévu : MoDem, Horizons, LIOT et UDR restent à ajouter (#815) ;
- **par le maillon le plus récent** — change à chaque législature.

Un identifiant qu'une collecte peut déplacer est un identifiant qui casse les
liens du site. Celui-ci est un jugement que nous portons, et il se relit.
"""

from __future__ import annotations

from typing import Any, Optional

SCHEMA_LIGNEE_VERSION = "1"
TYPE_DOCUMENT_LIGNEE = "profil_lignee"

#: Où les fiches de lignée sont publiées. **Un répertoire à part**, et non
#: `pivot_data/groupes/` : le contrôle de perte raisonne par collection, et deux
#: types de documents dans un même répertoire est le défaut que #630 a payé sur
#: `pivot_data/profiles/` — « 481 files, one directory, one naming pattern, a
#: glob returns 481 ».
SOUS_CHEMIN_LIGNEES = "lignees"

#: Forme d'une fiche de lignée.
#:
#: {
#:     "schema_version": "1",
#:     "type_document": "profil_lignee",
#:     "lignee_id": "AN:LIGNEE:SOC",      # DÉCLARÉ (voir le module)
#:     "lignee_nom": "Socialistes",       # libellé de lecture d'aujourd'hui
#:     "chambre": "AN",
#:     "maillons": [                      # du plus ancien au plus récent
#:         {"groupe_id": "AN:NG:15", "groupe_sigle": "NG",
#:          "groupe_nom": "Nouvelle Gauche", "legislature": "15",
#:          "fichier": "groupe-AN-NG-15.json",
#:          "periode": {"debut": "...", "fin": "..."},
#:          "position_politique": {...}}  # RECOPIÉE, jamais réunie
#:     ],
#:     "periode": {"debut": "...", "fin": "..."},   # de la lignée entière
#:     "membres": [...],                  # UNION sur `membre_id`
#:     "effectif": {"cumul_historique": 96},
#:     "cohesion_votes": [...],           # UNION sur `scrutin_id`
#:     "mandats_agreges": [...],          # fusion par (categorie, label)
#:     "tags_thematiques_agreges": [...], # RECALCUL depuis les profils
#:     "amendements_agreges": {...},      # RECALCUL depuis les profils
#:     "sources": [...],
#:     "meta": {...},
#: }

REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
    "schema_version", "type_document", "lignee_id", "lignee_nom", "chambre",
    "maillons", "periode", "membres", "effectif", "cohesion_votes",
    "mandats_agreges", "tags_thematiques_agreges", "amendements_agreges",
    "sources", "meta",
})

_LIST_KEYS: tuple[str, ...] = (
    "maillons", "membres", "cohesion_votes", "mandats_agreges",
    "tags_thematiques_agreges", "sources",
)


def make_empty_profil_lignee(
    lignee_id: str, lignee_nom: str, chambre: str
) -> dict[str, Any]:
    """Le squelette d'une fiche de lignée, tous agrégats vides."""
    return {
        "schema_version": SCHEMA_LIGNEE_VERSION,
        "type_document": TYPE_DOCUMENT_LIGNEE,
        "lignee_id": lignee_id,
        "lignee_nom": lignee_nom,
        "chambre": chambre,
        "maillons": [],
        "periode": {"debut": None, "fin": None},
        "membres": [],
        "effectif": {"cumul_historique": 0},
        "cohesion_votes": [],
        "mandats_agreges": [],
        "tags_thematiques_agreges": [],
        "amendements_agreges": {},
        "sources": [],
        "meta": {},
    }


def validate_profil_lignee(profil: Any) -> list[str]:
    """Invariants de la fiche de lignée. Liste vide = valide.

    Deux contrôles de contenu, et seulement deux, pour la même raison qu'en
    #809 : ils portent sur des **contradictions internes** qu'aucune étape en
    aval ne rattraperait.

    - une lignée sans maillon ne décrit rien ;
    - `effectif.cumul_historique` est le cardinal de l'union des membres, jamais
      une somme : les deux sont publiés côte à côte, et le compteur est ce que
      l'interface affiche quand la liste, elle, ne tient pas à l'écran.

    La rédaction d'origine annonçait un encadrement de l'union par les
    maillons — « ni plus que leur somme, ni moins que le plus grand ». Il n'a
    jamais été écrit, et il ne pouvait pas l'être : `maillons[]` ne porte aucun
    effectif. Un contrat qui décrit un contrôle absent est plus coûteux qu'un
    contrat court (#726).
    """
    errors: list[str] = []
    if not isinstance(profil, dict):
        return [f"Le profil de lignée doit être un dict, reçu : {type(profil).__name__}."]

    manquantes = REQUIRED_TOP_LEVEL_KEYS - set(profil)
    if manquantes:
        errors.append(f"Clés manquantes au niveau racine : {sorted(manquantes)}.")

    if profil.get("schema_version") != SCHEMA_LIGNEE_VERSION:
        errors.append(
            f"schema_version attendu {SCHEMA_LIGNEE_VERSION!r}, "
            f"reçu {profil.get('schema_version')!r}."
        )
    if profil.get("type_document") != TYPE_DOCUMENT_LIGNEE:
        errors.append(
            f"type_document attendu {TYPE_DOCUMENT_LIGNEE!r}, "
            f"reçu {profil.get('type_document')!r}."
        )
    for cle in _LIST_KEYS:
        if cle in profil and not isinstance(profil[cle], list):
            errors.append(f"'{cle}' doit être une liste.")

    maillons = profil.get("maillons")
    if isinstance(maillons, list) and not maillons:
        errors.append(
            "'maillons' est vide : une lignée sans maillon ne décrit rien. "
            "Une fiche de groupe isolée en est une à un seul maillon."
        )

    membres = profil.get("membres")
    cumul = (profil.get("effectif") or {}).get("cumul_historique")
    if isinstance(membres, list) and isinstance(cumul, int):
        if cumul != len(membres):
            errors.append(
                f"'effectif.cumul_historique' vaut {cumul} pour {len(membres)} "
                "membre(s) publiés : le compteur est le CARDINAL de l'union, "
                "jamais une somme de maillons (#836)."
            )
    return errors
