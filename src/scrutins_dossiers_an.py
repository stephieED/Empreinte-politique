"""Quel texte un scrutin tranche, et ce que ce texte est devenu (#758).

LE PROBLÈME EST DANS LA SOURCE, PAS DANS NOTRE COLLECTE. Un scrutin de
l'Assemblée ne porte **aucune** référence législative : `objet.
referenceLegislative` et `demandeur.referenceLegislative` sont nuls sur
0/18 311 scrutins bruts des législatures 14 à 17 (relevé du 31/08/2026, écrit
dans `scrutins_index.MOTIF_TEXTE_LIE_NON_SOURCE`). D'un vote publié, on connaît
le titre, la date et la position — jamais la commission saisie au fond, jamais
le sort du dossier.

LE LIEN EXISTE EN SENS INVERSE. Le dossier législatif, lui, nomme les scrutins
qui l'ont tranché : `actesLegislatifs[].voteRefs`. Ce module marche cet arbre —
**le même** que `commissions_dossiers_an.py` pour la commission et que
`gouvernement_textes.py` pour le statut, sur **les mêmes archives déjà
téléchargées** — et en tire deux choses que rien ne publiait :

  1. `scrutins` : `{clé de scrutin: uid de dossier}`, le rattachement lui-même ;
  2. `dossiers` : `{uid: {statut, sort_49_3}}`, l'issue du dossier.

POURQUOI LE STATUT EST REPUBLIÉ ICI. Il n'existait que sur les fiches de
gouvernement, et pour les seuls textes du gouvernement (725). Les dossiers
tranchés par un scrutin débordent ce périmètre — 556 dossiers visés, dont une
partie n'est d'aucun gouvernement. Il est calculé par `_determine_statut()`,
**la même fonction**, sur le même arbre : les deux publications ne peuvent pas
diverger, parce qu'il n'y a qu'un seul calcul.

CE QUE CE MODULE NE FAIT PAS. Il ne devine aucun rattachement : un scrutin
qu'aucun dossier ne nomme n'a pas d'entrée, et c'est une absence déclarée
(§2 règle 5), jamais comblée par une ressemblance de titre — la classification
par libellé que `regrouper-nest-pas-joindre-639` interdit. Mesuré au
07/09/2026 : 719 scrutins rattachés, soit 424 des 697 textes en dernière
lecture (61 %). Les 39 % restants sont un trou à déclarer, pas à remplir.

`texte_lie_id` reste réservé aux motions de censure (AGENTS.md §5) et n'est ni
recouvert ni remplacé : il répond à une autre question — quel texte une motion
vise —, et il est nul partout ailleurs.
"""

from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Optional

from gouvernement_textes import (
    _determine_statut,
    ensure_dossiers_zips_downloaded,
    iter_dossiers_bruts,
)
from scrutins_index import SOURCE_AN, cle_scrutin

SCHEMA_VERSION = "scrutins-dossiers-v1"

#: PAS DE CACHE DISQUE, ET C'EST LA LEÇON DE #749.
#:
#: Le réflexe était d'écrire l'index dérivé à côté des archives dont il dérive,
#: comme le fait `commissions_dossiers_an.NOM_CACHE`. Or `.cache/dossiers_an`
#: est RESTAURÉ ENTRE RUNS en CI (`actions/cache`, clé hebdomadaire avec
#: `restore-keys`) : un index posé là serait servi depuis le cache de la
#: semaine précédente et ne se reconstruirait jamais — exactement le défaut de
#: #749, où un repli de cache désamorçait la rotation qu'il devait servir.
#:
#: Le parcours complet des trois archives coûte **1,7 s** (mesuré le
#: 07/09/2026, 10 967 dossiers). Un cache disque achèterait ces 1,7 s au prix
#: d'une donnée qui vieillit en silence. Le mémo en process reste, lui : il
#: protège du cas où trois consommateurs du même run refont le parcours.
_MEMO: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()

DEFAULT_TABLE_PATH = Path("pivot_data") / "scrutins_dossiers.json"

#: `VTANR5L17V960` — préfixe, législature, numéro. Le préfixe `VTCGR` (Congrès)
#: partage l'espace de numérotation de l'AN et est exclu par la collecte des
#: scrutins (`AN_SCRUTIN_UID_PREFIXE`) : le reconnaître ici fabriquerait une
#: clé qui ne désigne aucun scrutin publié.
RX_UID_SCRUTIN = re.compile(r"^VTANR5L(\d+)V(\d+)$")


def cle_depuis_uid(uid: Any) -> Optional[str]:
    """`VTANR5L17V960` -> `an:17:960`, ou `None` si l'uid n'est pas un scrutin AN.

    La clé produite est celle de `scrutins_index.cle_scrutin` : les deux
    doivent rester la même, sinon la table ne joint rien.
    """
    if not isinstance(uid, str):
        return None
    trouve = RX_UID_SCRUTIN.match(uid.strip())
    if not trouve:
        return None
    return cle_scrutin(trouve.group(1), trouve.group(2))


def _collecter_vote_refs(noeud: Any, trouves: set[str]) -> None:
    """Ramasse tous les `voteRefs` de l'arbre, quelle que soit sa forme.

    `actesLegislatifs` est irrégulier — un acte unique est un objet, deux actes
    sont une liste — et `voteRefs` l'est autant : une chaîne, une liste de
    chaînes, ou un objet `{"voteRef": …}`. Marcher l'arbre entier plutôt que
    suivre un chemin fixe est ce qui rend la lecture indifférente à la forme,
    comme le fait déjà `_organes_saisis_au_fond`.
    """
    if isinstance(noeud, dict):
        for cle, valeur in noeud.items():
            if cle == "voteRefs":
                _ajouter_refs(valeur, trouves)
            else:
                _collecter_vote_refs(valeur, trouves)
    elif isinstance(noeud, list):
        for element in noeud:
            _collecter_vote_refs(element, trouves)


def _ajouter_refs(valeur: Any, trouves: set[str]) -> None:
    if isinstance(valeur, str):
        trouves.add(valeur)
    elif isinstance(valeur, dict):
        _ajouter_refs(valeur.get("voteRef"), trouves)
    elif isinstance(valeur, list):
        for element in valeur:
            _ajouter_refs(element, trouves)


def construire_table(archives: list[tuple[int, Path]]) -> dict[str, Any]:
    """Construit `{"scrutins": {clé: uid}, "dossiers": {uid: {...}}}`.

    UN SCRUTIN N'EST RATTACHÉ QU'À UN DOSSIER. Si deux dossiers le nomment —
    cas non observé sur les trois archives —, le dernier vu gagne, et
    `iter_dossiers_bruts` garantit que c'est celui de la législature la plus
    élevée, donc l'état le plus à jour.
    """
    scrutins: dict[str, str] = {}
    dossiers: dict[str, dict[str, Any]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if not isinstance(uid, str) or not uid:
            continue
        refs: set[str] = set()
        _collecter_vote_refs(dossier.get("actesLegislatifs"), refs)
        cles = [c for c in (cle_depuis_uid(r) for r in refs) if c]
        if not cles:
            continue
        statut, sort_49_3, _avertissement = _determine_statut(
            uid, dossier.get("actesLegislatifs")
        )
        # Un dossier sans statut résolu garde son entrée : le rattachement est
        # un fait, même quand l'issue ne l'est pas. `statut: null` se lit comme
        # une absence, jamais comme « en navette » (§2 règle 5).
        dossiers[uid] = {"statut": statut, "sort_49_3": sort_49_3}
        for cle in cles:
            scrutins[cle] = uid
    return {"scrutins": scrutins, "dossiers": dossiers}


def charger_table(
    *,
    cache_dir: Optional[Path] = None,
    telecharger: bool = True,
) -> dict[str, Any]:
    """Table `scrutin → dossier` + `dossier → issue`, du cache ou reconstruite.

    Retourne `{"scrutins": {}, "dossiers": {}}` — **jamais une exception** — si
    les archives sont indisponibles : l'appelant en fait une absence comptée, et
    surtout jamais une suppression de ce qui est déjà publié (§3a, #465).

    Le mémo est en PROCESS et rien n'est écrit sur disque — voir `_MEMO`.
    """
    del cache_dir  # accepté pour la symétrie d'appel ; aucun cache disque ici
    with _LOCK:
        memo = _MEMO.get("table")
        if memo is not None:
            return memo
        if not telecharger:
            return {"scrutins": {}, "dossiers": {}}
        archives = ensure_dossiers_zips_downloaded()
        if not archives:
            return {"scrutins": {}, "dossiers": {}}
        table = construire_table(archives)
        _MEMO["table"] = table
        return table


def vider_memo() -> None:
    """Vide le mémo en process (tests, et scripts qui rejouent une construction)."""
    with _LOCK:
        _MEMO.clear()


__all__ = [
    "DEFAULT_TABLE_PATH",
    "SCHEMA_VERSION",
    "SOURCE_AN",
    "charger_table",
    "cle_depuis_uid",
    "construire_table",
    "ensure_dossiers_zips_downloaded",
    "vider_memo",
]
