#!/usr/bin/env python3
"""
groupes_amo30.py — Les groupes de l'Assemblée et leurs lignées, dérivés du
référentiel AMO30 au lieu d'être écrits à la main (#1168, lot 1).

Pourquoi
--------
`config/groupes_reels.json` est écrite à la main : la liste des groupes, leurs
organes successifs, leurs noms, leur position, leurs liens d'une législature à
l'autre. Mesuré le 02/10/2026 : trois groupes de la XVe n'y étaient pas, et
personne ne l'avait décidé. Aux législatives de 2027 une dizaine de groupes
apparaîtront d'un coup.

AMO30 publie chaque groupe comme un organe `codeType == "GP"`, avec ses membres.
Tout ce que la table porte s'en déduit — sauf ce qui est un **nom** : le sigle
publié, l'identifiant de lignée. Ce module dérive le reste.

**Ce lot ne change rien à ce qui est publié.** Aucun job ne lit ce module ; la
table committée reste ce que les fiches lisent. Il dérive, et il compare.

La même règle, deux fois
------------------------
Arbitrée par la propriétaire le 02/10/2026 : les personnes communes, sur
l'effectif du **plus petit** des deux, à partir de la moitié
(`audit_filiation_lignees.atteint_le_seuil`).

1. **Dans une législature : le renommage.** Un groupe renommé ferme un organe et
   en ouvre un autre le lendemain (`SOC` puis `SOC-A`, `MODEM` puis `DEM`). Deux
   organes sont **le même groupe** quand le second ouvre au plus tard le
   lendemain de la fermeture du premier (`an_roster._contigus`) et que la règle
   passe. Une scission ne passe pas : `UDI-A-I → AGIR-E`, 10 sur 23.
2. **D'une législature à la suivante : la filiation.** Entre deux groupes — leurs
   organes réunis —, tous les couples qui passent.

Une **lignée** est ce que ces filiations relient.

Les décisions qui gouvernent ce module
--------------------------------------
Les trois qui comptent ; la liste complète et à jour est dans
`docs/decisions-par-module.md`.

- `docs/decisions/derivation-des-groupes-depuis-amo30-1168.md` — la règle
  appliquée deux fois, et ce que le calcul retrouve de la table ;
- `docs/decisions/table-des-groupes-du-run-1168.md` — la table du run, sa
  composition, et l'empreinte qui dit si elle est à jour ;
- `docs/decisions/lien-etabli-par-comparaison-1168.md` — pourquoi chaque lien
  est mesuré, et ce que la fiche en dit.

Ce qui n'est pas tranché n'est pas deviné
-----------------------------------------
- Un organe qui a **deux** successeurs contigus au-dessus du seuil — ou deux
  prédécesseurs — n'est pas un renommage : c'est une scission ou une fusion, et
  la règle ne dit pas lequel des deux est « le même groupe ». Aucun n'est réuni,
  et le cas est nommé dans `renommages_ambigus` (`AGENTS.md` §2 règle 5).
- Un groupe sans membre connu n'entre dans aucune comparaison.
- Les non-inscrits ne sont pas un groupe.
- Les législatures antérieures à `PREMIERE_LEGISLATURE` ne sont pas dérivées : la
  règle n'y a pas été éprouvée.

Mettre la table à jour (#1168, lot 2a)
--------------------------------------
`mettre_a_jour_table()` rapporte la dérivation à une table existante et rend la
table **complétée**. Trois règles, dans cet ordre :

1. **Ce qu'un humain ou un run précédent a nommé ne se réécrit jamais** : sigle
   publié, `groupe_id`, `lignee_id`, `succede_a`, `fichier`. Un lien entre
   législatures se calcule **une fois**, à l'entrée du groupe dans la table.
2. **Ce que la source dit se rafraîchit** : noms successifs et leurs dates,
   position, effectif.
3. **Un organe que la table ignore y entre** — dans le groupe dont il est le
   renommage, ou comme groupe nouveau, relié à sa lignée par la règle ou
   ouvrant la sienne.

Et ce qui ne se tranche pas reste dehors, nommé dans le journal : un groupe dont
aucun mandat n'a commencé (`en_attente`), un groupe qui succéderait à deux
lignées ou dont l'identifiant est déjà pris (`non_tranches`), deux entrées de la
table que la règle dit être un seul groupe (`a_fusionner`).

La table du run (#1168, lot 2c)
-------------------------------
Le run ne peut rien garder dans `config/`, recopié du dépôt privé à chaque run.
La table qu'il tient à jour vit donc dans `raw_data/groupes_du_run.json`, et
`composer_table()` la refait **à chaque run** de trois choses :

1. la **table écrite à la main** (`config/groupes_reels.json`), qui a toujours
   raison sur ce qu'elle porte ;
2. ce que les **runs précédents** ont ajouté et qu'elle ne porte pas — repris tel
   quel de la table du run précédente : c'est ce qui fige un lien et une adresse ;
3. ce que la **source** apporte de neuf (`mettre_a_jour_table`).

Elle consigne l'empreinte de la table écrite dont elle part, pour que les
lecteurs sachent si elle est encore à jour (`groupes_config.chemin_table_groupes`).

Un prédécesseur que la table écrite a **renommé ou réuni** depuis — mêmes
organes, autre identifiant — est retrouvé par ses organes : le lien repris le
suit, sans que personne ait à le réécrire.

Trois cas arrêtent la composition, et rien n'est alors écrit — la table du run
précédente reste, et les lecteurs retombent sur la table écrite : une lignée
que la table écrite **déplacerait** (#836), un identifiant qu'elle **reprend**
pour un autre groupe, un lien repris dont le **prédécesseur a disparu**.

Usage (depuis la racine du dépôt) :
    python3 src/groupes_amo30.py
    python3 src/groupes_amo30.py --comparer
    python3 src/groupes_amo30.py --json
    python3 src/groupes_amo30.py --mettre-a-jour                 # dit ce qui changerait
    python3 src/groupes_amo30.py --mettre-a-jour --out FICHIER   # et l'écrit
    python3 src/groupes_amo30.py --mettre-a-jour \
        --precedent raw_data/groupes_du_run.json --out raw_data/groupes_du_run.json   # ce que fait le run

Sortie : 0 ; avec `--comparer`, 1 si la dérivation et la table diffèrent ; avec
`--mettre-a-jour`, 1 si un cas n'a pas pu être tranché ; 2 si la table ou
l'archive est illisible.
"""

from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import an_roster  # noqa: E402
import gha  # noqa: E402
from audit_filiation_lignees import atteint_le_seuil, index_des_groupes  # noqa: E402
from groupes_config import (  # noqa: E402
    CHEMIN_CONFIG_GROUPES,
    CLE_MESURES_SUCCESSION,
    CHEMIN_TABLE_DU_RUN,
    CHEMIN_TABLE_ECRITE,
    CLE_EMPREINTE_TABLE_ECRITE,
    CLE_LIGNEE_ID,
    CLE_SUCCESSION,
    CorrespondanceSiglesInvalide,
    charger_correspondance_sigles,
    empreinte_table,
    mesure_soutient_le_lien,
)
from schema_groupe import (  # noqa: E402
    POSITION_POLITIQUE_AN_VERS_PIVOT,
    resumer_position_politique,
)

#: Première législature dérivée. Une **borne déclarée**, pas une limite de la
#: source : AMO30 porte les groupes depuis la XIIe, mais la règle n'a été
#: éprouvée que de la XVe à la XVIIe, et le dépôt ne publie rien avant.
PREMIERE_LEGISLATURE = 15


def _membres(index: dict[str, Any], organe_ref: str) -> set[str]:
    return {mandat[0] for mandat in index["mandats"].get(organe_ref, [])}


def _organes_derives(
    index: dict[str, Any],
    legislatures: Optional[Iterable[str]],
) -> dict[str, dict[str, Any]]:
    """Les organes de groupe à dériver, hors non-inscrits, par ordre d'ouverture."""
    voulues = {str(leg) for leg in legislatures} if legislatures is not None else None
    retenus = {}
    for ref, organe in index["organes"].items():
        legislature = organe.get("legislature")
        if organe.get("sigle") == an_roster.SIGLE_NON_INSCRIT or not legislature:
            continue
        if voulues is not None:
            if legislature not in voulues:
                continue
        elif int(legislature) < PREMIERE_LEGISLATURE:
            continue
        retenus[ref] = organe
    return dict(sorted(retenus.items(), key=lambda item: (item[1].get("debut") or "", item[0])))


def deriver_renommages(
    index: dict[str, Any],
    organes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Les couples d'organes contigus d'une même législature : `(couples, ambigus)`.

    Chaque couple porte son décompte et `renommage` — vrai quand la règle passe
    **et** que le couple est seul de son espèce des deux côtés.
    """
    couples: list[dict[str, Any]] = []
    for ref_a, a in organes.items():
        for ref_b, b in organes.items():
            if ref_a == ref_b or a.get("legislature") != b.get("legislature"):
                continue
            if not a.get("fin") or (b.get("debut") or "") <= a["fin"]:
                continue
            if not an_roster._contigus(a["fin"], b.get("debut")):
                continue
            membres_a, membres_b = _membres(index, ref_a), _membres(index, ref_b)
            communs = len(membres_a & membres_b)
            base = min(len(membres_a), len(membres_b))
            couples.append({
                "depart": ref_a,
                "arrivee": ref_b,
                "sigle_depart": a.get("sigle"),
                "sigle_arrivee": b.get("sigle"),
                "legislature": a.get("legislature"),
                "communs": communs,
                "base": base,
                "atteint_le_seuil": atteint_le_seuil(communs, base),
            })

    passent = [c for c in couples if c["atteint_le_seuil"]]
    successeurs: dict[str, int] = {}
    predecesseurs: dict[str, int] = {}
    for couple in passent:
        successeurs[couple["depart"]] = successeurs.get(couple["depart"], 0) + 1
        predecesseurs[couple["arrivee"]] = predecesseurs.get(couple["arrivee"], 0) + 1

    ambigus: list[dict[str, Any]] = []
    for couple in couples:
        seul = (
            successeurs.get(couple["depart"]) == 1
            and predecesseurs.get(couple["arrivee"]) == 1
        )
        couple["renommage"] = bool(couple["atteint_le_seuil"]) and seul
        if couple["atteint_le_seuil"] and not seul:
            ambigus.append(couple)
    return couples, ambigus


def deriver_groupes(
    index: dict[str, Any],
    legislatures: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    """Les groupes de l'Assemblée, organes renommés réunis. Fonction pure.

    Rend `{groupes, renommages, renommages_ambigus}`. Un groupe porte ce que la
    table écrit à la main — `organes_an`, `sigles_an`, `historique_organes_an`,
    `position_politique_an`, `effectif_amo30` — plus `membres`, l'ensemble sur
    lequel la filiation se mesure. Il n'a **pas** de `groupe_id` ni de sigle
    publié : ce sont des noms, et un nom ne se dérive pas.
    """
    organes = _organes_derives(index, legislatures)
    couples, ambigus = deriver_renommages(index, organes)

    suivant = {c["depart"]: c["arrivee"] for c in couples if c["renommage"]}
    a_un_precedent = set(suivant.values())
    constitution: dict[str, Optional[str]] = {}

    groupes: list[dict[str, Any]] = []
    for tete in organes:
        if tete in a_un_precedent:
            continue
        chaine = [tete]
        while chaine[-1] in suivant:
            chaine.append(suivant[chaine[-1]])
        legislature = organes[tete]["legislature"]
        if legislature not in constitution:
            constitution[legislature] = an_roster.date_constitution_groupes(index, legislature)

        declarations = [
            {
                "organe_an": ref,
                "sigle_an": organes[ref].get("sigle"),
                "valeur_source": organes[ref].get("position_politique"),
                "position": POSITION_POLITIQUE_AN_VERS_PIVOT.get(
                    organes[ref].get("position_politique")
                ),
            }
            for ref in chaine
        ]
        hors_transit = {
            mandat[0]
            for ref in chaine
            for mandat in index["mandats"].get(ref, [])
            if not an_roster.est_mandat_de_transit(mandat[2], constitution[legislature])
        }
        groupes.append({
            "legislature": legislature,
            "organes_an": chaine,
            "sigles_an": [organes[ref].get("sigle") for ref in chaine],
            "historique_organes_an": [
                {
                    "organe_an": ref,
                    "sigle_an": organes[ref].get("sigle"),
                    "nom": organes[ref].get("libelle"),
                    "debut": organes[ref].get("debut"),
                    "fin": organes[ref].get("fin"),
                }
                for ref in chaine
            ],
            "position_politique_an": {
                "position": resumer_position_politique(declarations),
                "organes": declarations,
            },
            "effectif_amo30": len(hors_transit),
            "membres": set().union(*(_membres(index, ref) for ref in chaine)),
        })
    return {"groupes": groupes, "renommages": couples, "renommages_ambigus": ambigus}


def deriver_filiations(groupes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Les liens d'une législature à la suivante : tous les couples qui passent.

    Chaque lien nomme ses deux groupes par leur **premier organe** — le seul
    identifiant qu'un groupe dérivé possède — et porte son décompte.
    """
    liens: list[dict[str, Any]] = []
    for depart in groupes:
        for arrivee in groupes:
            if int(arrivee["legislature"]) != int(depart["legislature"]) + 1:
                continue
            communs = len(depart["membres"] & arrivee["membres"])
            base = min(len(depart["membres"]), len(arrivee["membres"]))
            if atteint_le_seuil(communs, base):
                liens.append({
                    "depart": depart["organes_an"][0],
                    "arrivee": arrivee["organes_an"][0],
                    "communs": communs,
                    "base": base,
                })
    return liens


def deriver_lignees(
    groupes: list[dict[str, Any]],
    liens: list[dict[str, Any]],
) -> list[list[str]]:
    """Les lignées : ce que les filiations relient, chaque groupe nommé par son premier organe.

    Un groupe sans lien est une lignée d'un seul maillon. Triées par leur
    maillon le plus ancien, pour un ordre stable d'un run à l'autre.
    """
    racine = {groupe["organes_an"][0]: groupe["organes_an"][0] for groupe in groupes}

    def trouver(ref: str) -> str:
        while racine[ref] != ref:
            ref = racine[ref]
        return ref

    for lien in liens:
        racine[trouver(lien["arrivee"])] = trouver(lien["depart"])

    ordre = {groupe["organes_an"][0]: rang for rang, groupe in enumerate(groupes)}
    par_racine: dict[str, list[str]] = {}
    for ref in racine:
        par_racine.setdefault(trouver(ref), []).append(ref)
    lignees = [sorted(maillons, key=ordre.__getitem__) for maillons in par_racine.values()]
    return sorted(lignees, key=lambda maillons: ordre[maillons[0]])


def deriver(
    index: dict[str, Any],
    legislatures: Optional[Iterable[str]] = None,
) -> dict[str, Any]:
    """Groupes, filiations et lignées, d'un seul tenant."""
    derivation = deriver_groupes(index, legislatures)
    derivation["filiations"] = deriver_filiations(derivation["groupes"])
    derivation["lignees"] = deriver_lignees(derivation["groupes"], derivation["filiations"])
    return derivation


# ── La comparaison à la table écrite à la main ───────────────────────────────

def comparer_a_la_table(
    derivation: dict[str, Any],
    index: dict[str, Any],
    document: dict[str, Any],
    entrees: list[dict[str, Any]],
) -> dict[str, Any]:
    """Ce que la dérivation et `config/groupes_reels.json` disent de différent.

    Trois étages, du plus gros au plus fin : les **lignées** (quels organes sont
    sur la même page), les **groupes** (quels organes sont la même fiche), puis,
    pour chaque groupe identique des deux côtés, les **champs** que la table
    écrit à la main. Les entrées de la table hors des législatures dérivées sont
    laissées de côté, et comptées.
    """
    legislatures = {groupe["legislature"] for groupe in derivation["groupes"]}
    retenues = [e for e in entrees if str(e["legislature"]) in legislatures]

    def organes_de(entree: dict[str, Any]) -> frozenset[str]:
        return frozenset(
            an_roster.organes_du_groupe(index, entree["legislature"], entree["sigles_an"])
        )

    def libelle(organes: Iterable[str]) -> str:
        tries = sorted(organes, key=lambda ref: index["organes"][ref].get("debut") or "")
        return "+".join(
            f"{index['organes'][ref].get('sigle')}-{index['organes'][ref].get('legislature')}"
            for ref in tries
        )

    table = {organes_de(entree): entree for entree in retenues}
    calcules = {frozenset(g["organes_an"]): g for g in derivation["groupes"]}

    champs: list[dict[str, Any]] = []
    for organes in sorted(set(table) & set(calcules), key=libelle):
        entree, groupe = table[organes], calcules[organes]
        attendus = {
            "organes_an": entree.get("organes_an"),
            "historique_organes_an": entree.get("historique_organes_an"),
            "position": (entree.get("position_politique_an") or {}).get("position"),
            "effectif_amo30": entree.get("effectif_amo30"),
        }
        trouves = {
            "organes_an": groupe["organes_an"],
            "historique_organes_an": groupe["historique_organes_an"],
            "position": groupe["position_politique_an"]["position"],
            "effectif_amo30": groupe["effectif_amo30"],
        }
        for champ, attendu in attendus.items():
            if attendu is not None and attendu != trouves[champ]:
                champs.append({
                    "groupe_id": entree.get("groupe_id"),
                    "champ": champ,
                    "table": attendu,
                    "derive": trouves[champ],
                })

    lignee_de = {
        g.get("groupe_id"): g.get(CLE_LIGNEE_ID) for g in document.get("groupes") or []
    }
    lignees_table: dict[str, set[str]] = {}
    for organes, entree in table.items():
        lignees_table.setdefault(str(lignee_de.get(entree.get("groupe_id"))), set()).update(organes)
    par_tete = {g["organes_an"][0]: g["organes_an"] for g in derivation["groupes"]}
    lignees_calculees = {
        frozenset(ref for tete in maillons for ref in par_tete[tete])
        for maillons in derivation["lignees"]
    }
    lignees_ecrites = {frozenset(organes) for organes in lignees_table.values()}

    par_id = {e.get("groupe_id"): organes for organes, e in table.items()}
    liens_table = {
        (libelle(par_id[cible]), libelle(organes))
        for organes, entree in table.items()
        for cible in entree.get(CLE_SUCCESSION) or []
        if cible in par_id
        and index["organes"][next(iter(par_id[cible]))]["legislature"] != str(entree["legislature"])
    }
    liens_calcules = {
        (libelle(par_tete[lien["depart"]]), libelle(par_tete[lien["arrivee"]]))
        for lien in derivation["filiations"]
    }

    rapport = {
        "legislatures": sorted(legislatures, key=int),
        "entrees_hors_legislatures": len(entrees) - len(retenues),
        "lignees": {
            "derivees": len(lignees_calculees),
            "table": len(lignees_ecrites),
            "identiques": len(lignees_calculees & lignees_ecrites),
            "derivees_seulement": sorted(libelle(o) for o in lignees_calculees - lignees_ecrites),
            "table_seulement": sorted(libelle(o) for o in lignees_ecrites - lignees_calculees),
        },
        "groupes": {
            "derives": len(calcules),
            "table": len(table),
            "identiques": len(set(calcules) & set(table)),
            "derives_seulement": sorted(libelle(o) for o in set(calcules) - set(table)),
            "table_seulement": sorted(libelle(o) for o in set(table) - set(calcules)),
        },
        "filiations": {
            "derivees": len(liens_calcules),
            "table": len(liens_table),
            "identiques": len(liens_calcules & liens_table),
            "derivees_seulement": sorted(liens_calcules - liens_table),
            "table_seulement": sorted(liens_table - liens_calcules),
        },
        "champs_differents": champs,
        "renommages_ambigus": derivation["renommages_ambigus"],
    }
    rapport["differences"] = (
        len(rapport["lignees"]["derivees_seulement"])
        + len(rapport["lignees"]["table_seulement"])
        + len(rapport["groupes"]["derives_seulement"])
        + len(rapport["groupes"]["table_seulement"])
        + len(rapport["filiations"]["derivees_seulement"])
        + len(rapport["filiations"]["table_seulement"])
        + len(champs)
    )
    return rapport


# ── La mise à jour de la table (#1168, lot 2a) ──────────────────────────────

#: Les champs d'une entrée que la source dit, et qui se rafraîchissent. Tout le
#: reste — sigle publié, identifiants, `succede_a`, `fichier`, les notes écrites
#: à la main — est laissé tel quel.
CHAMPS_RAFRAICHIS = ("historique_organes_an", "position", "effectif_amo30")

CLE_TABLE = "correspondance_sigles_an"

#: Sur une entrée de `groupes[]` ou de `lignees[]` : qui l'a nommée. Posé à
#: `NOMME_PAR_LE_RUN` sur ce que `mettre_a_jour_table` ajoute, et sur rien
#: d'autre ; absent, l'entrée a été nommée à la main. C'est ce qui dit à
#: `suivre_le_dernier_nom` quels noms il peut faire suivre — un nom choisi par
#: un humain ne suit jamais, même quand la table écrite cesse de le porter.
CLE_NOMME_PAR = "nomme_par"
NOMME_PAR_LE_RUN = "run"


def _journal_vide() -> dict[str, list[Any]]:
    return {
        "noms_rafraichis": [],
        "liens_non_soutenus": [],
        "organes_rattaches": [],
        "groupes_ajoutes": [],
        "lignees_ajoutees": [],
        "champs_rafraichis": [],
        "en_attente": [],
        "non_tranches": [],
        "a_fusionner": [],
    }


def _rafraichir(
    entree: dict[str, Any],
    groupe: dict[str, Any],
    jour: str,
    journal: dict[str, list[Any]],
) -> None:
    """Recopie dans l'entrée ce que la source dit du groupe, et note ce qui a bougé."""
    position = entree.setdefault("position_politique_an", {})
    avant = {
        "historique_organes_an": entree.get("historique_organes_an"),
        "position": (position.get("position"), position.get("organes")),
        "effectif_amo30": entree.get("effectif_amo30"),
    }
    apres = {
        "historique_organes_an": groupe["historique_organes_an"],
        "position": (
            groupe["position_politique_an"]["position"],
            groupe["position_politique_an"]["organes"],
        ),
        "effectif_amo30": groupe["effectif_amo30"],
    }
    change = [champ for champ in CHAMPS_RAFRAICHIS if avant[champ] != apres[champ]]
    if not change:
        return
    entree["historique_organes_an"] = apres["historique_organes_an"]
    entree["effectif_amo30"] = apres["effectif_amo30"]
    if "position" in change:
        position["position"], position["organes"] = apres["position"]
        position["verifie_le"] = jour
    entree["verifie_le"] = jour
    for champ in change:
        journal["champs_rafraichis"].append({
            "groupe_id": entree.get("groupe_id"),
            "champ": champ,
            "avant": avant[champ] if champ != "position" else avant[champ][0],
            "apres": apres[champ] if champ != "position" else apres[champ][0],
        })


def _groupe_des_organes(index: dict[str, Any], organes: list[str]) -> dict[str, Any]:
    """Les champs dérivés d'une liste d'organes donnée — celle d'une entrée de la table.

    Sert à rafraîchir une entrée **sur ses propres organes**, sans redécider de
    sa composition : c'est `deriver_groupes` qui décide qu'un organe en rejoint
    un autre, pas le rafraîchissement.
    """
    tous = index["organes"]
    legislature = tous[organes[0]]["legislature"]
    constitution = an_roster.date_constitution_groupes(index, legislature)
    declarations = [
        {
            "organe_an": ref,
            "sigle_an": tous[ref].get("sigle"),
            "valeur_source": tous[ref].get("position_politique"),
            "position": POSITION_POLITIQUE_AN_VERS_PIVOT.get(tous[ref].get("position_politique")),
        }
        for ref in organes
    ]
    return {
        "historique_organes_an": [
            {
                "organe_an": ref,
                "sigle_an": tous[ref].get("sigle"),
                "nom": tous[ref].get("libelle"),
                "debut": tous[ref].get("debut"),
                "fin": tous[ref].get("fin"),
            }
            for ref in organes
        ],
        "position_politique_an": {
            "position": resumer_position_politique(declarations),
            "organes": declarations,
        },
        "effectif_amo30": len({
            mandat[0]
            for ref in organes
            for mandat in index["mandats"].get(ref, [])
            if not an_roster.est_mandat_de_transit(mandat[2], constitution)
        }),
    }


def mettre_a_jour_table(
    document: dict[str, Any],
    index: dict[str, Any],
    *,
    jour: Optional[str] = None,
    legislatures: Optional[Iterable[str]] = None,
) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    """Rend `(table complétée, journal)`. Fonction pure : `document` n'est pas modifié.

    Voir l'en-tête du module pour les trois règles. Idempotente : appliquée à sa
    propre sortie, elle ne change plus rien.
    """
    jour = jour or datetime.date.today().isoformat()
    nouveau = copy.deepcopy(document)
    entrees: list[dict[str, Any]] = nouveau[CLE_TABLE]["groupes"]
    groupes_config: list[dict[str, Any]] = nouveau["groupes"]
    lignees_config: list[dict[str, Any]] = nouveau["lignees"]
    journal = _journal_vide()
    organes = index["organes"]

    def ouverture(ref: str) -> str:
        return organes[ref].get("debut") or ""

    entree_de: dict[str, dict[str, Any]] = {}
    for entree in entrees:
        for ref in entree.get("organes_an") or []:
            entree_de[ref] = entree
    lignee_de = {g.get("groupe_id"): g.get(CLE_LIGNEE_ID) for g in groupes_config}

    derivation = deriver(index, legislatures)
    par_tete = {g["organes_an"][0]: g for g in derivation["groupes"]}
    nouveaux: list[dict[str, Any]] = []

    # 1. Chaque groupe dérivé trouve son entrée, ou n'en a pas.
    for groupe in derivation["groupes"]:
        touchees = []
        for ref in groupe["organes_an"]:
            entree = entree_de.get(ref)
            if entree is not None and all(entree is not t for t in touchees):
                touchees.append(entree)
        if not touchees:
            nouveaux.append(groupe)
            continue
        if len(touchees) > 1:
            journal["a_fusionner"].append({
                "groupes": [e.get("groupe_id") for e in touchees],
                "organes_an": groupe["organes_an"],
                "sigles_an": groupe["sigles_an"],
            })
            continue
        entree = touchees[0]
        inconnus = [ref for ref in groupe["organes_an"] if ref not in entree_de]
        if inconnus:
            if not all(_membres(index, ref) for ref in inconnus):
                journal["en_attente"].append({
                    "organes_an": inconnus,
                    "motif": "aucun mandat n'a encore commencé dans cet organe",
                })
            else:
                entree["organes_an"] = sorted(
                    set(entree["organes_an"]) | set(inconnus), key=ouverture
                )
                entree["sigles_an"] = list(dict.fromkeys(
                    organes[ref].get("sigle") for ref in entree["organes_an"]
                ))
                for ref in inconnus:
                    entree_de[ref] = entree
                    journal["organes_rattaches"].append({
                        "organe_an": ref,
                        "sigle_an": organes[ref].get("sigle"),
                        "groupe_id": entree.get("groupe_id"),
                    })

    # 2. Ce que la source dit des entrées existantes se rafraîchit, sur leurs
    #    propres organes. Un organe que l'archive ne porte pas laisse l'entrée
    #    intacte : une archive incomplète n'est pas une source qui se tait.
    for entree in entrees:
        refs = [ref for ref in entree.get("organes_an") or []]
        if not refs or any(ref not in organes for ref in refs):
            continue
        if not any(_membres(index, ref) for ref in refs):
            continue
        _rafraichir(entree, _groupe_des_organes(index, refs), jour, journal)

    # 3. Les groupes nouveaux entrent, du plus ancien au plus récent : un
    #    prédécesseur doit être dans la table avant son successeur.
    identifiants = {e.get("groupe_id") for e in entrees}
    lignees_prises = {l.get("lignee_id") for l in lignees_config}
    liens_vers: dict[str, list[dict[str, Any]]] = {}
    for lien in derivation["filiations"]:
        liens_vers.setdefault(lien["arrivee"], []).append(lien)

    for groupe in sorted(nouveaux, key=lambda g: (int(g["legislature"]), ouverture(g["organes_an"][0]))):
        tete = groupe["organes_an"][0]
        # Le PREMIER sigle, pas le dernier : c'est celui que le groupe portait à
        # sa naissance, donc celui qu'un run aurait vu en l'ajoutant ce jour-là.
        # L'identifiant ne dépend ainsi pas du moment où le groupe entre.
        sigle = groupe["sigles_an"][0]
        decrit = {"sigles_an": groupe["sigles_an"], "organes_an": groupe["organes_an"],
                  "legislature": groupe["legislature"]}
        if not groupe["membres"]:
            journal["en_attente"].append({
                **decrit, "motif": "aucun mandat n'a encore commencé dans ce groupe",
            })
            continue
        groupe_id = f"AN:{sigle}:{groupe['legislature']}"
        if groupe_id in identifiants:
            journal["non_tranches"].append({
                **decrit, "motif": f"l'identifiant {groupe_id} est déjà pris",
            })
            continue

        predecesseurs = []
        manquant = False
        for lien in liens_vers.get(tete, []):
            # L'entrée du prédécesseur se cherche par son organe le plus RÉCENT :
            # tant que deux entrées de la table décrivent un même groupe renommé
            # (`a_fusionner`), c'est la dernière qui précède la législature suivante.
            precedent = entree_de.get(par_tete[lien["depart"]]["organes_an"][-1])
            if precedent is None:
                manquant = True
                continue
            if all(precedent is not p for p, _ in predecesseurs):
                predecesseurs.append((precedent, lien))
        if manquant:
            journal["non_tranches"].append({
                **decrit, "motif": "son prédécesseur n'est pas entré dans la table",
            })
            continue
        lignees_amont = {lignee_de.get(p.get("groupe_id")) for p, _ in predecesseurs}
        if len(lignees_amont) > 1:
            journal["non_tranches"].append({
                **decrit,
                "motif": "succède à des groupes de plusieurs lignées : "
                         + ", ".join(sorted(str(l) for l in lignees_amont)),
            })
            continue

        nom = organes[groupe["organes_an"][-1]].get("libelle")
        if predecesseurs:
            lignee_id = next(iter(lignees_amont))
        else:
            lignee_id = f"AN:LIGNEE:{sigle}"
            if lignee_id in lignees_prises:
                journal["non_tranches"].append({
                    **decrit, "motif": f"l'identifiant de lignée {lignee_id} est déjà pris",
                })
                continue
            lignees_config.append({
                "lignee_id": lignee_id,
                "lignee_nom": nom,
                "chambre": "AN",
                "fichier": f"lignee-AN-{sigle}.json",
                "verifie_le": jour,
                CLE_NOMME_PAR: NOMME_PAR_LE_RUN,
            })
            lignees_prises.add(lignee_id)
            journal["lignees_ajoutees"].append({"lignee_id": lignee_id, "lignee_nom": nom})

        fichier = f"groupe-AN-{sigle}-{groupe['legislature']}.json"
        entree = {
            "groupe_sigle": sigle,
            "groupe_id": groupe_id,
            "legislature": groupe["legislature"],
            "fichier": fichier,
            "sigles_an": list(dict.fromkeys(groupe["sigles_an"])),
            "organes_an": groupe["organes_an"],
            "historique_organes_an": groupe["historique_organes_an"],
            "position_politique_an": {
                "position": groupe["position_politique_an"]["position"],
                "verifie_le": jour,
                "organes": groupe["position_politique_an"]["organes"],
            },
            "effectif_amo30": groupe["effectif_amo30"],
            "effectif_publie": None,
            "verifie_le": jour,
            "ecart_membres": [],
            "ecart_motif": (
                f"Entrée ajoutée par la dérivation AMO30 le {jour} (#1168) : le groupe "
                "n'était pas dans la table. Sigle et nom sont ceux de l'Assemblée, "
                "tels quels. `effectif_publie` reste null jusqu'à la parution."
            ),
        }
        if predecesseurs:
            entree[CLE_SUCCESSION] = [p.get("groupe_id") for p, _ in predecesseurs]
        entrees.append(entree)
        groupes_config.append({
            "roster_chambre": "deputes",
            "groupe_id": groupe_id,
            "lignee_id": lignee_id,
            "groupe_sigle": sigle,
            "groupe_nom": nom,
            "chambre": "AN",
            "legislature": groupe["legislature"],
            "fichier": fichier,
            CLE_NOMME_PAR: NOMME_PAR_LE_RUN,
        })
        identifiants.add(groupe_id)
        lignee_de[groupe_id] = lignee_id
        for ref in groupe["organes_an"]:
            entree_de[ref] = entree
        journal["groupes_ajoutes"].append({
            "groupe_id": groupe_id,
            "lignee_id": lignee_id,
            "sigles_an": groupe["sigles_an"],
            "effectif_amo30": groupe["effectif_amo30"],
            "succede_a": [
                {"groupe_id": p.get("groupe_id"), "communs": l["communs"], "base": l["base"]}
                for p, l in predecesseurs
            ],
        })
    journal["liens_non_soutenus"] = mesurer_liens(nouveau, index)
    return nouveau, journal


def suivre_le_dernier_nom(
    composee: dict[str, Any],
    ecrite: dict[str, Any],
    *,
    jour: str,
) -> list[dict[str, Any]]:
    """Le nom affiché d'un groupe que **seul un run** a ajouté suit le dernier nom de l'Assemblée.

    Arbitré par la propriétaire le 03/10/2026. **Modifie `composee` en place.**

    - `groupe_nom` : le libellé du dernier organe du groupe ;
    - `lignee_nom` d'une lignée que seul un run a ouverte : le nom de son
      groupe le plus récent — la convention des lignées écrites à la main
      (« Ensemble pour la République », « Droite Républicaine »).

    « Seul un run » se lit au marqueur `nomme_par: "run"`, posé à l'entrée du
    groupe : un groupe nommé à la main puis retiré de la table écrite garde le
    nom qu'un humain lui a donné.

    Ce qui ne bouge **jamais** : un nom que la table écrite porte, l'identifiant
    du groupe, celui de la lignée — donc l'adresse de la page (#836) —, et le
    sigle publié, que l'Assemblée donne tel quel à l'entrée du groupe.
    """
    noms_ecrits = {
        g.get("groupe_id") for g in ecrite.get("groupes") or []
    } | {
        g.get("groupe_id") for g in composee["groupes"]
        if g.get(CLE_NOMME_PAR) != NOMME_PAR_LE_RUN
    }
    lignees_ecrites = {
        l.get("lignee_id") for l in ecrite.get("lignees") or []
    } | {
        l.get("lignee_id") for l in composee["lignees"]
        if l.get(CLE_NOMME_PAR) != NOMME_PAR_LE_RUN
    }
    entree_de = {e.get("groupe_id"): e for e in composee[CLE_TABLE]["groupes"]}
    changes: list[dict[str, Any]] = []

    def dernier_nom(entree: dict[str, Any]) -> Optional[str]:
        historique = entree.get("historique_organes_an") or []
        return historique[-1].get("nom") if historique else None

    for groupe in composee["groupes"]:
        if groupe.get("groupe_id") in noms_ecrits:
            continue
        nom = dernier_nom(entree_de.get(groupe.get("groupe_id")) or {})
        if nom and nom != groupe.get("groupe_nom"):
            changes.append({"objet": groupe.get("groupe_id"), "avant": groupe.get("groupe_nom"), "apres": nom})
            groupe["groupe_nom"] = nom

    def recence(groupe: dict[str, Any]) -> tuple[int, str]:
        historique = (entree_de.get(groupe.get("groupe_id")) or {}).get("historique_organes_an") or []
        return (int(groupe.get("legislature") or 0), (historique[-1].get("debut") or "") if historique else "")

    for lignee in composee["lignees"]:
        if lignee.get("lignee_id") in lignees_ecrites:
            continue
        maillons = [g for g in composee["groupes"] if g.get(CLE_LIGNEE_ID) == lignee.get("lignee_id")]
        if not maillons:
            continue
        nom = max(maillons, key=recence).get("groupe_nom")
        if nom and nom != lignee.get("lignee_nom"):
            changes.append({"objet": lignee.get("lignee_id"), "avant": lignee.get("lignee_nom"), "apres": nom})
            lignee["lignee_nom"] = nom
            lignee["verifie_le"] = jour
    return changes


def composer_table(
    ecrite: dict[str, Any],
    precedente: Optional[dict[str, Any]],
    index: dict[str, Any],
    *,
    jour: Optional[str] = None,
    empreinte: Optional[str] = None,
    chemin_ecrite: Optional[Path] = None,
) -> tuple[Optional[dict[str, Any]], dict[str, list[Any]]]:
    """La table du run : `(table composée, journal)` — ou `(None, journal)` sur un conflit.

    Voir l'en-tête du module. Fonction pure : ni `ecrite` ni `precedente` ne
    sont modifiées.

    Ce qui est **repris** de la table précédente : toute entrée dont **aucun**
    organe n'est porté par la table écrite — un groupe que seul un run a ajouté.
    Une entrée dont la table écrite porte un organe ne se reprend pas : un humain
    l'a nommée depuis, et c'est sa version qui vaut.

    Une date de relecture (`verifie_le`) ne bouge que si le contenu a bougé : la
    table est refaite de la table écrite à chaque run, et sans cette précaution
    un effectif rafraîchi hier reprendrait la date du jour tous les jours.
    """
    jour = jour or datetime.date.today().isoformat()
    depart = copy.deepcopy(ecrite)
    conflits: list[dict[str, Any]] = []
    repris: list[str] = []
    renommes: dict[str, str] = {}

    if precedente:
        entrees = depart[CLE_TABLE]["groupes"]
        organe_vers = {
            ref: entree for entree in entrees for ref in entree.get("organes_an") or []
        }
        identifiants = {entree.get("groupe_id") for entree in entrees}
        lignee_ecrite = {g.get("groupe_id"): g.get(CLE_LIGNEE_ID) for g in depart["groupes"]}
        lignees_ecrites = {l.get("lignee_id") for l in depart["lignees"]}
        groupe_precedent = {g.get("groupe_id"): g for g in precedente.get("groupes") or []}
        lignee_precedente = {l.get("lignee_id"): l for l in precedente.get("lignees") or []}

        for entree in (precedente.get(CLE_TABLE) or {}).get("groupes") or []:
            groupe_id = entree.get("groupe_id")
            lignee_avant = (groupe_precedent.get(groupe_id) or {}).get(CLE_LIGNEE_ID)
            couvrantes = {
                organe_vers[ref]["groupe_id"]
                for ref in entree.get("organes_an") or [] if ref in organe_vers
            }
            if couvrantes:
                if len(couvrantes) == 1 and groupe_id not in identifiants:
                    # Mêmes organes, autre identifiant : la table écrite a renommé
                    # ou réuni ce groupe. Qui le nommait comme prédécesseur le
                    # retrouve sous son identifiant d'aujourd'hui — ce n'est pas
                    # un choix, ce sont les mêmes organes.
                    renommes[groupe_id] = next(iter(couvrantes))
                deplacees = sorted(
                    c for c in couvrantes
                    if lignee_avant and lignee_ecrite.get(c) != lignee_avant
                )
                if deplacees and groupe_id not in identifiants:
                    conflits.append({
                        "groupe_id": groupe_id,
                        "motif": (
                            f"publié dans la lignée {lignee_avant}, et la table écrite "
                            f"range ses organes dans {', '.join(deplacees)} "
                            f"({', '.join(sorted(str(lignee_ecrite.get(c)) for c in deplacees))}) : "
                            "l'adresse d'une page ne se déplace pas (#836)"
                        ),
                    })
                continue
            if groupe_id in identifiants:
                conflits.append({
                    "groupe_id": groupe_id,
                    "motif": "la table écrite reprend cet identifiant pour d'autres organes",
                })
                continue
            entrees.append(copy.deepcopy(entree))
            identifiants.add(groupe_id)
            for ref in entree.get("organes_an") or []:
                organe_vers[ref] = entree
            if groupe_id in groupe_precedent:
                depart["groupes"].append(copy.deepcopy(groupe_precedent[groupe_id]))
            if lignee_avant and lignee_avant not in lignees_ecrites and lignee_avant in lignee_precedente:
                depart["lignees"].append(copy.deepcopy(lignee_precedente[lignee_avant]))
                lignees_ecrites.add(lignee_avant)
            repris.append(groupe_id)

        for entree in entrees:
            if entree.get("groupe_id") not in repris or not entree.get(CLE_SUCCESSION):
                continue
            entree[CLE_SUCCESSION] = list(dict.fromkeys(
                renommes.get(cible, cible) for cible in entree[CLE_SUCCESSION]
            ))
            for cible in entree[CLE_SUCCESSION]:
                if cible not in identifiants:
                    conflits.append({
                        "groupe_id": entree.get("groupe_id"),
                        "motif": f"son prédécesseur {cible} n'est plus dans la table",
                    })

    if conflits:
        journal = _journal_vide()
        journal["conflits"] = conflits
        journal["groupes_repris"] = repris
        return None, journal

    composee, journal = mettre_a_jour_table(depart, index, jour=jour)
    journal["conflits"] = []
    journal["groupes_repris"] = repris
    journal["noms_rafraichis"] = suivre_le_dernier_nom(composee, ecrite, jour=jour)

    if precedente:
        avant = {
            e.get("groupe_id"): e
            for e in (precedente.get(CLE_TABLE) or {}).get("groupes") or []
        }
        for entree in composee[CLE_TABLE]["groupes"]:
            ancienne = avant.get(entree.get("groupe_id"))
            if ancienne is None:
                continue
            sans_dates = lambda e: {  # noqa: E731
                **{k: v for k, v in e.items() if k != "verifie_le"},
                "position_politique_an": {
                    k: v for k, v in (e.get("position_politique_an") or {}).items()
                    if k != "verifie_le"
                },
            }
            if sans_dates(entree) == sans_dates(ancienne):
                entree["verifie_le"] = ancienne.get("verifie_le")
                entree["position_politique_an"]["verifie_le"] = (
                    ancienne.get("position_politique_an") or {}
                ).get("verifie_le")

    if empreinte is not None:
        composee.setdefault("_meta", {})[CLE_EMPREINTE_TABLE_ECRITE] = {
            "fichier": str(chemin_ecrite or CHEMIN_TABLE_ECRITE),
            "sha256": empreinte,
        }
    return composee, journal


def mesurer_liens(
    document: dict[str, Any],
    index: dict[str, Any],
) -> list[dict[str, Any]]:
    """Écrit dans chaque entrée la mesure de ses liens `succede_a`, et rend ceux que la règle ne soutient pas.

    **Modifie `document` en place** — c'est la dernière étape de
    `mettre_a_jour_table`, qui travaille sur sa propre copie.

    Chaque lien reçoit `{groupe_id, communs, base}` sous `succede_a_mesures` :
    les personnes communes aux deux groupes (organes réunis), sur l'effectif du
    plus petit. Un lien dont un côté n'a aucun membre dans l'archive n'est pas
    mesuré — il ne reçoit rien, et se publiera `relecture_humaine`.

    C'est ce qui rend `etabli_par: comparaison_des_membres` vrai à la lettre :
    la fiche ne le dit que d'un lien dont la mesure est écrite et passe le seuil.
    Tous les liens sont mesurés, y compris ceux écrits à la main — sans quoi
    l'affirmation reposerait sur ce que la table écrite prétend.
    """
    entrees = document[CLE_TABLE]["groupes"]
    par_id = {e.get("groupe_id"): e for e in entrees}

    def membres(entree: dict[str, Any]) -> set[str]:
        return set().union(*(_membres(index, ref) for ref in entree.get("organes_an") or []))

    non_soutenus: list[dict[str, Any]] = []
    for entree in entrees:
        mesures = []
        for cible in entree.get(CLE_SUCCESSION) or []:
            precedent = par_id.get(cible)
            if precedent is None:
                continue
            avant, apres = membres(precedent), membres(entree)
            base = min(len(avant), len(apres))
            if base == 0:
                continue
            mesure = {"groupe_id": cible, "communs": len(avant & apres), "base": base}
            mesures.append(mesure)
            if not mesure_soutient_le_lien(mesure):
                non_soutenus.append({
                    "groupe_id": entree.get("groupe_id"),
                    "predecesseur": cible,
                    "communs": mesure["communs"],
                    "base": base,
                })
        if mesures:
            entree[CLE_MESURES_SUCCESSION] = mesures
        else:
            entree.pop(CLE_MESURES_SUCCESSION, None)
    return non_soutenus


def table_modifiee(journal: dict[str, list[Any]]) -> bool:
    """La mise à jour a-t-elle changé quelque chose à la table ?"""
    return any(
        journal.get(cle)
        for cle in ("organes_rattaches", "groupes_ajoutes", "lignees_ajoutees",
                    "champs_rafraichis", "noms_rafraichis")
    )


def _afficher_journal(journal: dict[str, list[Any]]) -> None:
    if not any(journal.values()):
        print("Rien à mettre à jour : la table porte déjà tout ce que la source dit.")
        return
    for ajout in journal["groupes_ajoutes"]:
        suite = " ; ".join(
            f"prend la suite de {s['groupe_id']} ({s['communs']} sur {s['base']})"
            for s in ajout["succede_a"]
        ) or "aucun prédécesseur au-dessus du seuil"
        print(
            f"  [groupe ajouté] {ajout['groupe_id']} — {'/'.join(ajout['sigles_an'])}, "
            f"{ajout['effectif_amo30']} pers., lignée {ajout['lignee_id']} ; {suite}"
        )
    for ajout in journal["lignees_ajoutees"]:
        print(f"  [lignée ajoutée] {ajout['lignee_id']} — {ajout['lignee_nom']}")
    for rattache in journal["organes_rattaches"]:
        print(
            f"  [renommage] {rattache['organe_an']} ({rattache['sigle_an']}) "
            f"rejoint {rattache['groupe_id']}"
        )
    for champ in journal["champs_rafraichis"]:
        if champ["champ"] == "historique_organes_an":
            print(f"  [rafraîchi] {champ['groupe_id']} · noms successifs et dates")
        else:
            print(
                f"  [rafraîchi] {champ['groupe_id']} · {champ['champ']} : "
                f"{champ['avant']!r} → {champ['apres']!r}"
            )
    for attente in journal["en_attente"]:
        print(f"  [en attente] {attente.get('sigles_an') or attente['organes_an']} : {attente['motif']}")
    for cas in journal["non_tranches"]:
        print(f"  [non tranché] {'/'.join(cas['sigles_an'])} ({cas['legislature']}e) : {cas['motif']}")
    for nom in journal.get("noms_rafraichis") or []:
        print(f"  [nom] {nom['objet']} : « {nom['avant']} » → « {nom['apres']} »")
    for lien in journal.get("liens_non_soutenus") or []:
        print(
            f"  [non soutenu] {lien['predecesseur']} → {lien['groupe_id']} : "
            f"{lien['communs']} sur {lien['base']}, sous la moitié — le lien reste "
            "publié, comme `relecture_humaine`"
        )
    for cas in journal.get("conflits") or []:
        print(f"  [CONFLIT] {cas['groupe_id']} : {cas['motif']}")
    if journal.get("groupes_repris"):
        print(
            f"  [repris] {len(journal['groupes_repris'])} groupe(s) ajouté(s) par un run "
            f"précédent : {', '.join(journal['groupes_repris'])}"
        )
    for cas in journal["a_fusionner"]:
        print(
            f"  [à fusionner] {' et '.join(str(g) for g in cas['groupes'])} : la règle en "
            f"fait un seul groupe renommé ({'/'.join(cas['sigles_an'])})"
        )


# ── L'affichage ──────────────────────────────────────────────────────────────

def _sans_membres(derivation: dict[str, Any]) -> dict[str, Any]:
    """La dérivation sans ses ensembles de membres : un `set` ne s'écrit pas en JSON."""
    return {
        **derivation,
        "groupes": [
            {cle: valeur for cle, valeur in groupe.items() if cle != "membres"}
            for groupe in derivation["groupes"]
        ],
    }


def _afficher_derivation(derivation: dict[str, Any]) -> None:
    groupes = derivation["groupes"]
    par_tete = {g["organes_an"][0]: g for g in groupes}
    print(
        f"{len(groupes)} groupe(s) dérivé(s) d'AMO30, {len(derivation['lignees'])} "
        f"lignée(s), {len(derivation['filiations'])} lien(s) entre législatures."
    )
    for maillons in derivation["lignees"]:
        print(
            "  "
            + "  →  ".join(
                f"{'/'.join(par_tete[tete]['sigles_an'])} ({par_tete[tete]['legislature']}e, "
                f"{par_tete[tete]['effectif_amo30']} pers.)"
                for tete in maillons
            )
        )
    for couple in derivation["renommages_ambigus"]:
        print(
            f"  [non tranché] {couple['sigle_depart']} → {couple['sigle_arrivee']} "
            f"({couple['legislature']}e) : {couple['communs']} sur {couple['base']}, "
            "mais pas seul de son espèce — ni renommage, ni rien d'autre."
        )


def _afficher_comparaison(rapport: dict[str, Any]) -> None:
    print(
        f"\nComparaison à la table — législatures {', '.join(rapport['legislatures'])} "
        f"({rapport['entrees_hors_legislatures']} entrée(s) de la table hors de ces législatures)."
    )
    for cle, nom in (("lignees", "Lignées"), ("groupes", "Groupes"), ("filiations", "Liens")):
        bloc = rapport[cle]
        derive = bloc.get("derivees", bloc.get("derives"))
        print(f"  {nom} : {derive} dérivé(e)s, {bloc['table']} dans la table, {bloc['identiques']} identiques.")
        for seul in bloc.get("derivees_seulement", bloc.get("derives_seulement")):
            print(f"    dérivé seulement : {seul}")
        for seul in bloc["table_seulement"]:
            print(f"    table seulement  : {seul}")
    for ecart in rapport["champs_differents"]:
        print(
            f"  {ecart['groupe_id']} · {ecart['champ']} : "
            f"table {ecart['table']!r}, dérivé {ecart['derive']!r}"
        )
    print(
        f"\n→ {rapport['differences']} différence(s) entre la dérivation et la table."
        if rapport["differences"] else
        "\n→ La dérivation reproduit la table."
    )


# ── Le résumé de run (#1168, lot 4) ──────────────────────────────────────────

def resume_de_run(journal: dict[str, list[Any]], *, ecrite: bool) -> str:
    """Ce que la composition a fait, en Markdown, pour le résumé du job.

    Le résumé d'un run du dépôt public est lisible par tous : il nomme les
    groupes et les liens, **jamais le décompte** d'un lien. La propriétaire a
    arbitré le 03/10/2026 que seule la règle se publie (« on ne publiera que la
    règle dans la méthodo ») ; le décompte reste dans la table, où il sert à
    choisir `etabli_par`.

    Une ligne quand rien n'a bougé : un run ordinaire ne doit pas noyer le
    résumé, mais son silence doit se distinguer d'une étape qui n'a pas tourné.
    """
    lignes = ["### Table des groupes du run (#1168)", ""]
    if not ecrite:
        lignes.append(
            "**Table non écrite** : la composition contredit ce qu'un run a déjà "
            "publié. Le run continue sur la table écrite à la main."
        )
        lignes.append("")
        for cas in journal.get("conflits") or []:
            lignes.append(f"- `{cas['groupe_id']}` : {cas['motif']}")
        return "\n".join(lignes) + "\n"

    rubriques = [
        ("Groupes ajoutés", [
            f"`{a['groupe_id']}` ({'/'.join(a['sigles_an'])}, {a['effectif_amo30']} personnes) — "
            + (
                "prend la suite de " + ", ".join(f"`{s['groupe_id']}`" for s in a["succede_a"])
                if a["succede_a"] else "aucun prédécesseur"
            )
            + f", lignée `{a['lignee_id']}`"
            for a in journal["groupes_ajoutes"]
        ]),
        ("Lignées ouvertes", [
            f"`{l['lignee_id']}` — {l['lignee_nom']}" for l in journal["lignees_ajoutees"]
        ]),
        ("Renommages rattachés à leur groupe", [
            f"`{r['organe_an']}` ({r['sigle_an']}) → `{r['groupe_id']}`"
            for r in journal["organes_rattaches"]
        ]),
        ("Noms suivis (groupes et lignées ajoutés par un run)", [
            f"`{n['objet']}` : « {n['avant']} » → « {n['apres']} »"
            for n in journal.get("noms_rafraichis") or []
        ]),
        ("Liens sous le seuil — publiés `relecture_humaine`", [
            f"`{l['predecesseur']}` → `{l['groupe_id']}`"
            for l in journal.get("liens_non_soutenus") or []
        ]),
        ("Non tranchés — à relire", [
            f"{'/'.join(c['sigles_an'])} ({c['legislature']}e) : {c['motif']}"
            for c in journal["non_tranches"]
        ]),
        ("En attente — aucun mandat commencé", [
            f"{'/'.join(c.get('sigles_an') or c['organes_an'])}" for c in journal["en_attente"]
        ]),
    ]
    rafraichis = sorted({c["groupe_id"] for c in journal["champs_rafraichis"]})
    if not any(contenu for _, contenu in rubriques):
        lignes.append(
            "Aucun groupe nouveau, aucun renommage, aucun lien à relire"
            + (f" ; champs rafraîchis depuis la source sur {len(rafraichis)} groupe(s)."
               if rafraichis else ".")
        )
        return "\n".join(lignes) + "\n"
    for titre, contenu in rubriques:
        if contenu:
            lignes.append(f"**{titre}**")
            lignes.append("")
            lignes.extend(f"- {ligne}" for ligne in contenu)
            lignes.append("")
    if rafraichis:
        lignes.append(f"Champs rafraîchis depuis la source : {', '.join(f'`{g}`' for g in rafraichis)}.")
    return "\n".join(lignes) + "\n"


def _publier_le_resume(journal: dict[str, list[Any]], *, ecrite: bool) -> None:
    """Résumé du job et annotations — sans effet hors d'un runner GitHub Actions."""
    chemin = os.getenv("GITHUB_STEP_SUMMARY")
    if chemin:
        try:
            with open(chemin, "a", encoding="utf-8") as f:
                f.write(resume_de_run(journal, ecrite=ecrite))
        except OSError as exc:
            print(f"  [!] Impossible d'écrire dans GITHUB_STEP_SUMMARY : {exc}", file=sys.stderr)
    for ajout in journal["groupes_ajoutes"]:
        gha.annoter(
            "notice",
            f"GROUPE_AJOUTE — {ajout['groupe_id']} ({'/'.join(ajout['sigles_an'])}) entre "
            f"dans la table du run, lignée {ajout['lignee_id']} (#1168).",
        )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dérive d'AMO30 les groupes de l'Assemblée, leurs renommages "
                    "et leurs lignées (#1168). N'écrit rien.",
    )
    parser.add_argument(
        "--comparer",
        action="store_true",
        help="Comparer la dérivation à config/groupes_reels.json : lignées, "
             "groupes, liens, puis champ par champ. Sortie 1 s'ils diffèrent.",
    )
    parser.add_argument(
        "--mettre-a-jour",
        action="store_true",
        help="Dire ce que la source ajouterait à la table : organes renommés, "
             "groupes et lignées nouveaux, champs rafraîchis. N'écrit que si "
             "--out est donné. Sortie 1 si un cas n'a pas pu être tranché.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        metavar="FICHIER",
        help="Avec --mettre-a-jour : où écrire la table complétée. Sans lui, "
             "rien n'est écrit.",
    )
    parser.add_argument(
        "--precedent",
        type=Path,
        default=None,
        metavar="FICHIER",
        help="Avec --mettre-a-jour : la table du run précédente, dont sont repris "
             "les groupes qu'un run a ajoutés et que la table écrite ne porte pas "
             f"(dans un run : {CHEMIN_TABLE_DU_RUN}). Absente, elle est ignorée.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Rendre la dérivation (et la comparaison, ou le journal de mise à "
             "jour) en JSON sur la sortie standard.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="FICHIER",
        help=f"Défaut : {CHEMIN_CONFIG_GROUPES} ; avec --mettre-a-jour, la table "
             f"écrite à la main, {CHEMIN_TABLE_ECRITE}.",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=None,
        metavar="FICHIER",
        help="Archive AMO30 locale, lue sans toucher au cache partagé. Défaut : "
             "celle de .cache/acteurs_historique_an/, téléchargée au besoin.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    if args.out and not args.mettre_a_jour:
        parser.error("--out n'a de sens qu'avec --mettre-a-jour.")

    if args.precedent and not args.mettre_a_jour:
        parser.error("--precedent n'a de sens qu'avec --mettre-a-jour.")

    if args.mettre_a_jour:
        # La table de départ est la table ÉCRITE, jamais celle du run : c'est
        # elle que la composition complète, et la relire d'elle-même ferait
        # d'un ajout d'hier une vérité d'aujourd'hui que plus rien ne corrige.
        ecrite_path = Path(args.config) if args.config else CHEMIN_TABLE_ECRITE
        try:
            index = index_des_groupes(args.archive)
            charger_correspondance_sigles(ecrite_path)  # la table de départ doit être valide
            ecrite = json.loads(ecrite_path.read_text(encoding="utf-8"))
        except (
            an_roster.RosterAnInactif,
            an_roster.RosterAnIndisponible,
            CorrespondanceSiglesInvalide,
        ) as exc:
            print(f"[!] {exc}", file=sys.stderr)
            return 2
        precedente = None
        if args.precedent and args.precedent.is_file():
            try:
                precedente = json.loads(args.precedent.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                print(
                    f"[!] Table précédente illisible ({args.precedent}) : {exc}. "
                    "Elle est ignorée : rien n'en est repris.",
                    file=sys.stderr,
                )
        nouveau, journal = composer_table(
            ecrite, precedente, index,
            empreinte=empreinte_table(ecrite_path), chemin_ecrite=ecrite_path,
        )
        if args.json:
            print(json.dumps(journal, ensure_ascii=False, indent=2))
        else:
            _afficher_journal(journal)
        _publier_le_resume(journal, ecrite=nouveau is not None)
        if nouveau is None:
            print(
                "[!] Table NON écrite : la composition contredit ce qu'un run a déjà "
                "publié. La table précédente reste en place.",
                file=sys.stderr,
            )
            return 1
        if args.out:
            contenu = json.dumps(nouveau, ensure_ascii=False, indent=2) + "\n"
            try:
                inchangee = args.out.read_text(encoding="utf-8") == contenu
            except OSError:
                inchangee = False
            if inchangee:
                print(f"→ {args.out} est déjà à jour : rien n'est réécrit.", file=sys.stderr)
            else:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(contenu, encoding="utf-8")
                print(f"→ Table écrite dans {args.out}.", file=sys.stderr)
        return 1 if journal["non_tranches"] or journal["liens_non_soutenus"] else 0

    chemin = Path(args.config) if args.config else CHEMIN_CONFIG_GROUPES
    try:
        index = index_des_groupes(args.archive)
        derivation = deriver(index)
        rapport = None
        if args.comparer:
            entrees = charger_correspondance_sigles(chemin)
            document = json.loads(chemin.read_text(encoding="utf-8"))
            rapport = comparer_a_la_table(derivation, index, document, entrees)
    except (
        an_roster.RosterAnInactif,
        an_roster.RosterAnIndisponible,
        CorrespondanceSiglesInvalide,
    ) as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2

    if args.json:
        sortie = _sans_membres(derivation)
        if rapport is not None:
            sortie["comparaison"] = rapport
        print(json.dumps(sortie, ensure_ascii=False, indent=2))
    else:
        _afficher_derivation(derivation)
        if rapport is not None:
            _afficher_comparaison(rapport)
    return 1 if rapport and rapport["differences"] else 0


if __name__ == "__main__":
    sys.exit(main())
