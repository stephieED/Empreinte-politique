#!/usr/bin/env python3
"""commissions_dossiers_an.py — Table `dossier législatif → commission saisie au fond` (#328).

POURQUOI ELLE EXISTE. La fiche candidat publie, sous « L'essentiel », la
répartition des dossiers amendés par **commission saisie au fond**. Cette
commission ne se déduit PAS d'un intitulé : « Lois » couvre l'immigration, la
justice et les institutions, et bâtir la correspondance intitulé → thème serait
une classification construite par ce dépôt, c'est-à-dire un acte éditorial
(AGENTS.md §2 règle 1, exactement le raisonnement des catégories PCS en §4).

ELLE SE LIT DANS LA SOURCE. Chaque `dossierParlementaire` des archives déjà en
cache (`.cache/dossiers_an/`) porte un acte `codeActe: "AN1-COM-FOND-SAISIE"`
(« Renvoi en commission au fond »), dont l'`organeRef` (`PO######`) est résolu
par le référentiel des organes (`index_organes_v2.json`, #353) en commission
permanente ou spéciale. Rien n'est inféré : l'uid de l'organe est copié verbatim.

Mesuré le 01/09/2026 sur les trois archives XV/XVI/XVII :

| | Mesure |
| --- | ---: |
| dossiers portant une saisie au fond AN | **6 024** |
| saisies sans `organeRef` | **0** |
| `organeRef` que le référentiel ne résout pas | **0** |
| dossiers où deux saisies au fond désignent des organes différents | **0** |
| types d'organe rencontrés | `COMPER` 6 257, `CNPS` 28 |

`AN1` est la PREMIÈRE LECTURE à l'Assemblée, et c'est délibéré : c'est la
saisine qui range le dossier, celles des lectures suivantes la répètent. Les
`SN1-COM-FOND-SAISIE` (Sénat) ne sont pas lus — le Sénat est hors périmètre
(#528) et une commission sénatoriale ne décrit pas le travail d'un⋅e député⋅e.

CE QUE LA TABLE NE PORTE PAS. Un dossier sans acte de saisie au fond n'a **pas**
d'entrée : ni commission devinée, ni entrée vide (§2 règle 5). La couverture est
celle des archives ingérées — les dossiers de la XIVe législature n'y sont pas,
et les 62 dépôts de Xavier Bertrand comme les 6 d'Édouard Philippe restent donc
sans commission, déclarés comme tels par la page.

OÙ VIT LE CACHE. `.cache/dossiers_an/index_dossier_commission_v1.json`, dans le
répertoire des archives dont il dérive — même règle que `textes_dossiers_an.py` :
un index dérivé qui survivrait à la correction de sa source est le piège de #580.
Le suffixe de version s'incrémente dès que le CONTENU écrit change, jamais pour
un changement de lecture.
"""

import json
import threading
from pathlib import Path
from typing import Any, Optional

from gouvernement_textes import (
    DOSSIERS_CACHE_DIR,
    ensure_dossiers_zips_downloaded,
    iter_dossiers_bruts,
)

#: Le seul `codeActe` lu. « Renvoi en commission au fond », première lecture AN.
CODE_ACTE_SAISIE_FOND = "AN1-COM-FOND-SAISIE"

#: Nom du fichier de cache disque, versionné (voir docstring du module).
#: **#1019 — version incrémentée avec l'ajout de l'archive XIV.** Le contenu
#: de cet index change (3 402 dossiers de plus), et un cache porte le code ET
#: les sources qui l'ont écrit. Ce n'est pas théorique : sur #997, un
#: correctif publié n'a rien changé pendant un run entier parce que l'index
#: était relu tel quel — `.cache/dossiers_an` est restauré d'une semaine sur
#: l'autre par les `restore-keys` du workflow.
NOM_CACHE = "index_dossier_commission_v2.json"

_LOCK = threading.Lock()

#: Mémo en process keyé sur le **chemin** du cache, jamais sur un nom logique :
#: les tests remplacent le répertoire de cache par cas, et un mémo global ferait
#: fuir la table d'un test dans le suivant (le piège qui a fait revenir #377).
_MEMO: dict[str, dict[str, dict[str, Any]]] = {}


def _organes_saisis_au_fond(noeud: Any, trouves: list[str]) -> None:
    """Collecte les `organeRef` des actes `AN1-COM-FOND-SAISIE` sous `noeud`.

    L'arbre `actesLegislatifs` est irrégulier — un acte unique est un objet, deux
    actes une liste — donc le parcours est récursif et ne présume d'aucune
    profondeur.
    """
    if isinstance(noeud, dict):
        if noeud.get("codeActe") == CODE_ACTE_SAISIE_FOND:
            organe_ref = noeud.get("organeRef")
            if isinstance(organe_ref, str) and organe_ref:
                trouves.append(organe_ref)
        for valeur in noeud.values():
            _organes_saisis_au_fond(valeur, trouves)
    elif isinstance(noeud, list):
        for valeur in noeud:
            _organes_saisis_au_fond(valeur, trouves)


def construire_table(
    archives: list[tuple[int, Path]], organes: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Construit `{uid de dossier: {"organe_ref", "sigle", "nom", "type"}}`.

    `organes` est l'index `organeRef -> {sigle, nom, type}` de
    `candidate_profile._build_organe_index()` (#353), passé en argument plutôt
    qu'importé : ce module reste lisible sans tirer les 4 500 lignes de la
    collecte, et les tests fournissent leur propre référentiel.

    Un dossier dont l'`organeRef` n'est pas dans le référentiel n'a **pas**
    d'entrée : publier un `PO######` brut donnerait au lecteur un identifiant à
    la place d'une commission.
    """
    table: dict[str, dict[str, Any]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if not isinstance(uid, str) or not uid:
            continue
        trouves: list[str] = []
        _organes_saisis_au_fond(dossier.get("actesLegislatifs"), trouves)
        if not trouves:
            continue
        organe_ref = trouves[0]
        organe = organes.get(organe_ref)
        if not isinstance(organe, dict):
            continue
        sigle = organe.get("sigle")
        nom = organe.get("nom")
        if not sigle and not nom:
            # Un organe dont le référentiel ne publie ni sigle ni nom ne se
            # remplace pas par son uid (§2 règle 5).
            continue
        table[uid] = {
            "organe_ref": organe_ref,
            "sigle": sigle,
            "nom": nom,
            "type": organe.get("type"),
        }
    return table


def charger_table(
    *,
    organes: Optional[dict[str, dict[str, Any]]] = None,
    cache_dir: Optional[Path] = None,
    telecharger: bool = True,
) -> dict[str, dict[str, Any]]:
    """Table `dossier → commission au fond`, depuis le cache disque ou reconstruite.

    Retourne `{}` — jamais une exception — si les archives ou le référentiel des
    organes sont indisponibles : l'appelant en fait alors une absence **comptée**,
    jamais une suppression de ce qui est déjà publié.
    """
    repertoire = Path(cache_dir) if cache_dir is not None else DOSSIERS_CACHE_DIR
    chemin = repertoire / NOM_CACHE
    cle = str(chemin.resolve() if chemin.parent.exists() else chemin)

    with _LOCK:
        memo = _MEMO.get(cle)
        if memo is not None:
            return memo

        if chemin.is_file():
            try:
                with open(chemin, encoding="utf-8") as f:
                    table = json.load(f)
                if isinstance(table, dict):
                    _MEMO[cle] = table
                    return table
            except (json.JSONDecodeError, OSError):
                pass  # cache corrompu : on reconstruit

        if not telecharger:
            return {}

        if organes is None:
            # Import tardif : `candidate_profile` importe `gouvernement_textes`,
            # qui n'importe pas ce module — la boucle n'existe pas, mais la
            # collecte pèse lourd et n'a pas à être chargée pour une lecture de
            # cache.
            from candidate_profile import _build_organe_index

            organes = _build_organe_index()
        if not organes:
            return {}

        archives = ensure_dossiers_zips_downloaded()
        if not archives:
            return {}

        table = construire_table(archives, organes)
        try:
            chemin.parent.mkdir(parents=True, exist_ok=True)
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(table, f, ensure_ascii=False)
        except OSError:
            pass
        _MEMO[cle] = table
        return table


def vider_memo() -> None:
    """Vide le mémo en process (tests, et scripts qui rejouent une construction)."""
    with _LOCK:
        _MEMO.clear()
