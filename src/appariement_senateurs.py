#!/usr/bin/env python3
"""
appariement_senateurs.py — Relier un profil publié à son matricule sénatorial (#885).

Pourquoi il n'y a pas de second référentiel
--------------------------------------------
`raw_data/correspondance_acteurs_an.json` porte déjà, pour chacune de ses
**1 196** entrées, un champ `identifiants.senat` — **nul sur les 1 196**. Il
attendait une source. Ce module la lui donne, et n'écrit **que** ce champ.

Créer une seconde table aurait fabriqué un référentiel concurrent, avec sa
propre notion de slug et sa propre dérive. Le dépôt a déjà réglé ce débat pour
les licences (`src/licences.py`) et pour les acteurs de l'Assemblée : une clé,
un endroit.

Le nom ne fait pas la personne
------------------------------
L'appariement porte sur **l'état civil ET la date de naissance**, et c'est la
date qui fait le travail. Le nom seul produisait **2 faux positifs sur 38** —
5 %, mesuré le 13/09/2026 :

| Profil publié | Ce que le nom seul appariait | L'écart |
| --- | --- | ---: |
| `beatrice-descamps`, députée du Nord, née le 24/04/1961 | une sénatrice homonyme née le 22/06/1951 | **10 ans** |
| `jean-louis-masson`, député 2017-2020, né le 05/02/1954 | `PA2116`, Mosellan né le 25/03/1947, député **puis** sénateur | **7 ans** |

Aucun des deux n'était « ambigu » au sens d'un doublon dans la table du Sénat :
chaque nom y est unique. C'est le **corpus publié** qui porte l'homonyme, et
seule la date de naissance le montre. Le second cas est le plus instructif : le
sénateur existe et a sa place au corpus, mais sous **un autre profil** —
`PA2116` n'est pas publié aujourd'hui, et le jour où il le sera, `01060R` sera
son appariement légitime. Un `senat: null` sur `PA346218` ne dit donc pas « ce
nom n'a pas de sénateur » : il dit « **celui-ci** n'en est pas un ».

Les dates le disaient déjà sans qu'on les lise : un mandat de député 2017-2020
qui chevauche un mandat de sénateur 2017-2023 est impossible. Le critère ne
vérifie pas cette cohérence-là — il n'en a pas besoin, la date de naissance
suffit — mais elle reste la preuve à regarder en cas de doute.

Le nom, lui, doit encore être apparié finement : la source range « Dominique de
Legge » en `senprenomuse = "Dominique"` + `sennomuse = "de Legge"`, et un
découpage du nom publié sur son dernier mot manquerait tous les noms à
particule. D'où l'essai de **tous les découpages**.

**Il refuse d'apparier ce qui est ambigu.** Deux sénateurs pour un même état
civil **et** la même date rendent `AppariementAmbigu`, jamais un choix :
`build_correspondance_acteurs_an.py` « refuse d'inventer » depuis #525, et un
identifiant faux est pire qu'un identifiant absent.

**Une date de naissance absente d'un côté ou de l'autre refuse aussi
l'appariement** — sans elle, il ne reste que le nom, et le nom vient d'échouer
deux fois sur trente-huit. Un appariement qu'on ne peut pas prouver ne se fait
pas (§2 règle 5).

Mesuré le 13/09/2026 sur les 1 196 profils publiés et les 1 951 lignes de `sen` :
**36 appariements, 2 homonymes écartés, 0 ambigu**.

Ce qu'un appariement automatique n'est pas
-------------------------------------------
Une **preuve**. L'entrée écrite est estampillée `origine: "derivee"` — le même
régime que les 699 entrées dérivées de #715 : elle **gèle** l'identifiant, elle
ne l'établit pas. La faire passer à `relue` demande qu'un humain la regarde, et
la §5b du portail publie le compte de ce qui reste à relire précisément pour que
la file se voie.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from typing import Any, Iterable, Optional

from senat_opendata import date_publiable

#: Ce qu'un appariement automatique vaut, dans le vocabulaire de
#: `correspondance_acteurs_an.json` : il gèle, il ne prouve pas (#715).
ORIGINE_APPARIEMENT = "derivee"


class AppariementAmbigu(ValueError):
    """Deux sénateurs répondent au même état civil **et** à la même date.

    Levée plutôt que résolue : un identifiant faux rattacherait la carrière de
    quelqu'un d'autre à une fiche publiée, et rien dans le corpus ne le
    signalerait ensuite.
    """


def normaliser(valeur: Optional[str]) -> str:
    """L'état civil réduit à ce qui compare : lettres minuscules, sans accents.

    Les espaces et les traits d'union disparaissent aussi — « Jean-Luc » et
    « Jean Luc » sont la même personne, et la source n'est pas régulière
    là-dessus.
    """
    sans_accents = unicodedata.normalize("NFD", valeur or "")
    sans_accents = sans_accents.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", sans_accents.lower())


def indexer_senateurs(lignes: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Les sénateurs indexés par `(état civil normalisé, date de naissance)`.

    La date est **dans la clé**, pas dans un contrôle d'après-coup : c'est ce
    qui empêche un homonyme de s'apparier, et non de s'apparier puis d'être
    rattrapé. Un sénateur sans date de naissance n'entre pas dans l'index — il
    ne serait appariable que par son nom, et le nom ne suffit pas.

    La valeur est une **liste** : c'est elle qui rend l'ambiguïté visible, là où
    un dict l'écraserait en silence.
    """
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ligne in lignes:
        naissance = date_publiable(ligne.get("sendatnai"))
        if not naissance:
            continue
        cle = normaliser(ligne.get("senprenomuse")) + normaliser(ligne.get("sennomuse"))
        if cle:
            index[f"{cle}|{naissance}"].append(ligne)
    return index


def apparier(nom_publie: str, naissance: Optional[str],
             index: dict[str, list[dict[str, Any]]]) -> Optional[str]:
    """Le matricule d'une personne publiée, ou `None`.

    Essaie **tous les découpages** prénom/nom : la source range les particules
    dans le nom (« Dominique » + « de Legge »), et le corpus publie un nom
    complet. Un découpage sur le dernier mot manquerait tous les noms à
    particule.

    **Sans date de naissance, rend `None` sans rien chercher** : il ne resterait
    que le nom, et le nom a produit 2 faux positifs sur 38.

    Rend `None` plutôt que de lever quand rien ne correspond : un profil sans
    passé sénatorial est le cas normal — **1 158 des 1 196**.
    """
    naissance = (str(naissance)[:10] if naissance else None)
    if not naissance:
        return None
    mots = (nom_publie or "").split()
    candidats: dict[str, dict[str, Any]] = {}
    for coupe in range(1, len(mots)):
        cle = normaliser(" ".join(mots[:coupe])) + normaliser(" ".join(mots[coupe:]))
        for ligne in index.get(f"{cle}|{naissance}", []):
            candidats[ligne["senmat"]] = ligne
    if not candidats:
        return None
    if len(candidats) > 1:
        raise AppariementAmbigu(
            f"{nom_publie!r} correspond à {len(candidats)} sénateurs "
            f"({', '.join(sorted(candidats))}). Aucun n'est retenu : un "
            "identifiant faux rattacherait la carrière de quelqu'un d'autre. "
            "Trancher à la main dans raw_data/correspondance_acteurs_an.json."
        )
    return next(iter(candidats))


def proposer_appariements(
    correspondances: dict[str, dict[str, Any]],
    senateurs: Iterable[dict[str, Any]],
) -> tuple[dict[str, str], list[str], list[str]]:
    """Rend `(appariements, ambigus, deja_renseignes)`.

    Ne modifie rien : la proposition se lit avant de s'écrire. Une entrée dont
    `identifiants.senat` est **déjà** renseigné n'est jamais recalculée — elle a
    pu être relue par un humain, et un appariement automatique qui écrase une
    relecture défait précisément le travail qu'il faut protéger (#715).
    """
    index = indexer_senateurs(senateurs)
    appariements: dict[str, str] = {}
    ambigus: list[str] = []
    deja: list[str] = []
    for slug, entree in correspondances.items():
        identifiants = entree.get("identifiants") or {}
        if identifiants.get("senat"):
            deja.append(slug)
            continue
        etat_civil = entree.get("etat_civil") or {}
        nom = etat_civil.get("nom_complet") or ""
        try:
            matricule = apparier(nom, etat_civil.get("date_naissance"), index)
        except AppariementAmbigu:
            ambigus.append(slug)
            continue
        if matricule:
            appariements[slug] = matricule
    return appariements, sorted(ambigus), sorted(deja)


def ecrire_appariements(
    document: dict[str, Any],
    appariements: dict[str, str],
    horodatage: str,
) -> int:
    """Pose `identifiants.senat` et l'estampille, **sans toucher au reste**.

    Ce fichier porte du travail relu à la main sur d'autres champs : y réécrire
    quoi que ce soit d'autre défait ce travail sans qu'aucun test ne le voie
    (#715). D'où un écrivain qui ne connaît qu'une clé.

    `origine` ne passe à `derivee` que si l'entrée n'en portait pas de meilleure :
    une entrée `relue` ou `sourcee` garde la sienne — elle a été établie par
    quelqu'un, et un appariement automatique ne la déclasse pas.
    """
    ecrites = 0
    for slug, matricule in appariements.items():
        entree = document["correspondances"][slug]
        entree.setdefault("identifiants", {})["senat"] = matricule
        if entree.get("origine") not in ("relue", "sourcee"):
            entree["origine"] = ORIGINE_APPARIEMENT
        entree["senat_apparie_le"] = horodatage
        ecrites += 1
    return ecrites
