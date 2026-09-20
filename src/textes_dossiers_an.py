#!/usr/bin/env python3
"""textes_dossiers_an.py — Table `texte AN → dossier législatif` (#639, rang 3).

LA BRIQUE MANQUANTE. Un amendement AN porte `texteLegislatifRef`, l'uid du
**document** qu'il amende (`PRJLANR5L15B1088`). Un document porte `dossierRef`,
l'uid de son **dossier** (`DLR5L15N36030`). Les deux vivent dans les archives
déjà téléchargées par le pipeline (`.cache/dossiers_an/`) — mais la seconde
famille de fichiers, `json/document/*.json`, n'avait jamais été ouverte : elle
était décrite comme « sans rapport, à filtrer » depuis le spike #207.

Mesuré le 31/08/2026 sur les trois archives XV/XVI/XVII :

| | Mesure |
| --- | ---: |
| documents lus | 23 709 |
| uid distincts | 21 937 |
| portant un `dossierRef` | **21 936** |
| uid dont le `dossierRef` diverge d'une archive à l'autre | **0** |

CE QUE LA TABLE PORTE, ET CE QU'ELLE NE PORTE PAS. Une entrée par uid de
document : `dossier_id` (l'uid du dossier, verbatim) et `titre` (le titre du
dossier, pour que le libellé lisible ne soit pas perdu — il vivait jusqu'ici
recopié dans le `texte_vise` de chaque amendement). Un document dont le dossier
n'est pas dans les archives lues n'a **pas** d'entrée : ni titre inventé, ni
`dossier_id` deviné (AGENTS.md §2 règle 5).

PAS DE JOINTURE PAR LIBELLÉ. La table est construite d'uid à uid. Rapprocher un
amendement de son dossier par ressemblance — ou même par égalité — de titre
serait une clé dérivée d'une chaîne, ce qu'interdit AGENTS.md §2 règle 2, et
resterait faux au cas où deux dossiers partagent un intitulé.

LA COUVERTURE EST CELLE DES ARCHIVES INGÉRÉES. `AN_DOSSIERS_ARCHIVES` couvre les
législatures XV, XVI et XVII. Les documents de la XIVe n'y sont pas : les
59 263 amendements de la XIVe portant un code de texte restent sans dossier, et
c'est déclaré comme tel plutôt que rattrapé par un rapprochement de titre.

OÙ VIT LE CACHE. `.cache/dossiers_an/index_texte_dossier_v1.json`, dans le
répertoire des archives dont il dérive : les deux vieillissent ensemble, sous la
même clé de cache CI hebdomadaire. Un index dérivé qui survivrait à la
correction de sa source est le piège de #580 ; ici il ne peut pas, il est rangé
avec elle.
"""

import json
import threading
from pathlib import Path
from typing import Any, Optional

from gouvernement_textes import (
    DOSSIERS_CACHE_DIR,
    ensure_dossiers_zips_downloaded,
    iter_documents_bruts,
    iter_dossiers_bruts,
)

#: Nom du fichier de cache. Suffixé par une version : le jour où le contenu de
#: la table change de forme, un cache CI existant ne doit pas servir l'ancienne
#: en silence (leçon de `index_texte_titre_v2`, #400).
#: **#1019 — version incrémentée avec l'ajout de l'archive XIV.** Le contenu
#: de cet index change (3 402 dossiers de plus), et un cache porte le code ET
#: les sources qui l'ont écrit. Ce n'est pas théorique : sur #997, un
#: correctif publié n'a rien changé pendant un run entier parce que l'index
#: était relu tel quel — `.cache/dossiers_an` est restauré d'une semaine sur
#: l'autre par les `restore-keys` du workflow.
NOM_CACHE = "index_texte_dossier_v2.json"

_LOCK = threading.Lock()

#: Mémo en process, keyé sur le **chemin** du cache et jamais sur un nom
#: logique : les tests remplacent le répertoire de cache par cas, et un mémo
#: global ferait fuir la table d'un test dans le suivant (le piège qui a fait
#: revenir #377).
_MEMO: dict[str, dict[str, dict[str, Any]]] = {}


def construire_table(archives: list[tuple[int, Path]]) -> dict[str, dict[str, Any]]:
    """Construit `{uid de document: {"dossier_id", "titre"}}` depuis les archives.

    Deux passes de générateur, jamais deux archives en mémoire : les titres de
    dossiers d'abord (10 967 entrées), les documents ensuite. Un document sans
    `dossierRef` n'entre pas dans la table.
    """
    titres: dict[str, Optional[str]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if isinstance(uid, str) and uid:
            titre = (dossier.get("titreDossier") or {}).get("titre")
            titres[uid] = titre if isinstance(titre, str) and titre else None

    table: dict[str, dict[str, Any]] = {}
    for _legislature, document in iter_documents_bruts(archives):
        uid = document.get("uid")
        dossier_ref = document.get("dossierRef")
        if not isinstance(uid, str) or not uid:
            continue
        if not isinstance(dossier_ref, str) or not dossier_ref:
            # Un document sans dossier déclaré ne se voit pas en attribuer un.
            continue
        table[uid] = {"dossier_id": dossier_ref, "titre": titres.get(dossier_ref)}
    return table


def charger_table(
    *, cache_dir: Optional[Path] = None, telecharger: bool = True
) -> dict[str, dict[str, Any]]:
    """Table `texte → dossier`, depuis le cache disque ou reconstruite.

    Retourne `{}` — jamais une exception — si les archives sont indisponibles :
    l'appelant en fait alors une absence de rattachement **comptée**, jamais une
    suppression de ce qui est déjà publié.
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

        archives = ensure_dossiers_zips_downloaded()
        if not archives:
            return {}

        table = construire_table(archives)
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
