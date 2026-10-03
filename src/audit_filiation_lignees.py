#!/usr/bin/env python3
"""
audit_filiation_lignees.py — Comparer les liens `succede_a` écrits à la main à
ce que dit la composition des groupes (#1168).

Pourquoi
--------
Une fiche de lignée réunit les groupes successifs d'une même formation. Les
liens qui les relient sont **déclarés** dans `config/groupes_reels.json`
(`correspondance_sigles_an.groupes[].succede_a`), et aucune source ne les porte :
l'Assemblée ouvre et ferme des organes, elle ne les chaîne pas (#700). Jusqu'ici
rien ne signalait qu'un lien déclaré ne tenait plus, qu'un lien manquait, ou que
l'Assemblée avait ouvert un groupe que la table ignore.

Cet audit **propose et signale ; il n'écrit rien et ne publie rien**. La table
reste la seule chose que les fiches lisent, et `etabli_par` reste vrai.

Le critère
----------
Arbitré par la propriétaire le 02/10/2026 : pour deux groupes de deux
législatures consécutives, les personnes communes, divisées par l'effectif du
**plus petit des deux**, et le lien est retenu à partir de la moitié. **Tous**
les couples qui passent le seuil sont retenus, pas seulement le meilleur.

Prendre le plus petit des deux règle à la racine le défaut d'un pourcentage
quand l'effectif bouge d'une législature à l'autre : quand un groupe s'effondre,
c'est l'arrivée qui devient la base, et l'arrivée ne contient que des élus.

Trois précisions que la mesure a imposées
-----------------------------------------
- **L'unité est le GROUPE, pas l'organe.** Un groupe renommé en cours de
  législature tient en plusieurs organes (`SOC` puis `SOC-A`, `MODEM` puis
  `DEM`) : ses membres sont l'union, comme pour le roster. Un organe que la
  table ne connaît pas est comparé seul.
- **Les non-inscrits sont exclus.** Presque tous les députés passent par `NI` à
  l'ouverture d'une législature : l'organe recouvre tout le monde, et le garder
  fait passer le seuil à des dizaines de couples qui ne disent rien.
- **Un groupe sans membre connu n'est pas mesuré.** Ni retrouvé, ni manqué :
  `non_mesurable` (`AGENTS.md` §2 règle 5).

Ce que le rapport nomme
-----------------------
| Rubrique | Ce qu'elle dit | Écart ? |
| --- | --- | --- |
| `liens_declares` | chaque lien de la table, avec son décompte | oui s'il n'atteint pas le seuil |
| `candidats_non_declares` | couples qui atteignent le seuil sans être dans la table | oui |
| `ecartes_les_plus_proches` | les couples non déclarés les plus près du seuil, pour lire la marge | non |
| `organes_sans_entree` | organes de groupe de l'Assemblée qu'aucune entrée ne couvre | non — nommés |
| `non_mesurables` | liens déclarés dont un côté n'a aucun membre connu | non — nommés |

Un lien déclaré **dans une même législature** (`NG → SOC`, XVe) est mesuré comme
les autres et marqué `meme_legislature` : c'est un renommage écrit comme une
succession, et l'audit le dit sans le trancher.

Le sigle est un **signal de lecture**, jamais une exemption : un lien à sigle
publié identique qui rate le seuil est listé en premier.

Aucun taux n'est imprimé sans son numérateur et son dénominateur (§2 règle 7).
Outil interne : rien de ce qu'il rend n'est publiable.

Usage (depuis la racine du dépôt) :
    python3 src/audit_filiation_lignees.py
    python3 src/audit_filiation_lignees.py --proches 10
    python3 src/audit_filiation_lignees.py --json

Sortie : 0 si la table et la composition disent la même chose, 1 s'il y a un
écart, 2 si la table ou l'archive est illisible.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import an_roster  # noqa: E402
from groupes_config import (  # noqa: E402
    CHEMIN_CONFIG_GROUPES,
    CLE_SUCCESSION,
    CorrespondanceSiglesInvalide,
    charger_correspondance_sigles,
)

#: Le seuil, en fraction exacte : `communs / base >= 1/2`. Arbitré le
#: 02/10/2026, et délibérément PAS une option de la ligne de commande — une
#: option invite à le rouvrir à chaque lecture. Comparé en entiers
#: (`communs * DENOMINATEUR >= base * NUMERATEUR`) : 9 sur 18 fait la moitié,
#: sans qu'un arrondi flottant en décide.
SEUIL_NUMERATEUR = 1
SEUIL_DENOMINATEUR = 2

#: Combien de couples écartés le rapport montre par défaut. Ils ne sont pas des
#: écarts : ils donnent la marge sous le seuil, sans laquelle « aucun candidat »
#: ne se lit pas.
PROCHES_PAR_DEFAUT = 5


def atteint_le_seuil(communs: int, base: int) -> Optional[bool]:
    """Le couple atteint-il la moitié du plus petit des deux ? `None` sans base.

    Une base nulle n'est pas « 0 % » : c'est un groupe dont on ne connaît aucun
    membre, et la question ne se pose pas (§2 règle 5).
    """
    if base <= 0:
        return None
    return communs * SEUIL_DENOMINATEUR >= base * SEUIL_NUMERATEUR


def unites_de_comparaison(
    index: dict[str, Any],
    entrees: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Ce que l'audit compare : `(unites, organes_sans_entree)`.

    Une unité par entrée de la table — ses organes résolus par sigle, comme le
    roster, donc leur union —, puis une par organe `GP` que **aucune** entrée
    n'atteint, dans les seules législatures que la table couvre et hors `NI`.
    Hors de ces législatures la règle n'a pas été éprouvée, et un organe de la
    XIVe ne peut succéder à rien que le dépôt publie.
    """
    organes = index["organes"]
    mandats = index["mandats"]

    def membres(refs: list[str]) -> set[str]:
        return {m[0] for ref in refs for m in mandats.get(ref, [])}

    unites: list[dict[str, Any]] = []
    couverts: set[str] = set()
    for entree in entrees:
        refs = an_roster.organes_du_groupe(
            index, entree["legislature"], entree["sigles_an"]
        )
        couverts.update(refs)
        unites.append({
            "id": entree.get("groupe_id") or f"{entree['groupe_sigle']}-{entree['legislature']}",
            "groupe_sigle": entree["groupe_sigle"],
            "legislature": str(entree["legislature"]),
            "organes_an": refs,
            "sigles_an": [organes[ref].get("sigle") for ref in refs],
            "dans_la_table": True,
            "membres": membres(refs),
        })

    legislatures = {unite["legislature"] for unite in unites}
    sans_entree: list[dict[str, Any]] = []
    for ref, organe in sorted(
        organes.items(), key=lambda item: (item[1].get("debut") or "", item[0])
    ):
        if ref in couverts or organe.get("sigle") == an_roster.SIGLE_NON_INSCRIT:
            continue
        if organe.get("legislature") not in legislatures:
            continue
        unite = {
            "id": ref,
            "groupe_sigle": None,
            "legislature": str(organe.get("legislature")),
            "organes_an": [ref],
            "sigles_an": [organe.get("sigle")],
            "dans_la_table": False,
            "membres": membres([ref]),
        }
        unites.append(unite)
        sans_entree.append({
            "organe_an": ref,
            "sigle_an": organe.get("sigle"),
            "nom": organe.get("libelle"),
            "legislature": unite["legislature"],
            "debut": organe.get("debut"),
            "fin": organe.get("fin"),
            "effectif": len(unite["membres"]),
        })
    return unites, sans_entree


def mesurer_couple(depart: dict[str, Any], arrivee: dict[str, Any]) -> dict[str, Any]:
    """Le décompte d'un couple, numérateur et dénominateur toujours ensemble."""
    effectif_depart = len(depart["membres"])
    effectif_arrivee = len(arrivee["membres"])
    communs = len(depart["membres"] & arrivee["membres"])
    base = min(effectif_depart, effectif_arrivee)
    return {
        "depart": depart["id"],
        "arrivee": arrivee["id"],
        "sigles_an_depart": depart["sigles_an"],
        "sigles_an_arrivee": arrivee["sigles_an"],
        "communs": communs,
        "base": base,
        "base_prise_sur": "depart" if effectif_depart <= effectif_arrivee else "arrivee",
        "effectif_depart": effectif_depart,
        "effectif_arrivee": effectif_arrivee,
        "atteint_le_seuil": atteint_le_seuil(communs, base),
    }


def _plus_proche_du_seuil(mesure: dict[str, Any]) -> tuple[float, str, str]:
    """Clé de tri : le rapport décroissant, puis les identifiants, pour un ordre stable."""
    return (-mesure["communs"] / mesure["base"], mesure["depart"], mesure["arrivee"])


def auditer_filiation(
    index: dict[str, Any],
    entrees: list[dict[str, Any]],
    *,
    proches: int = PROCHES_PAR_DEFAUT,
) -> dict[str, Any]:
    """Compare la table à la composition. Fonction pure : ni disque, ni réseau."""
    unites, sans_entree = unites_de_comparaison(index, entrees)
    par_id = {unite["id"]: unite for unite in unites}

    declares: set[tuple[str, str]] = set()
    liens: list[dict[str, Any]] = []
    for entree in entrees:
        arrivee = par_id[entree.get("groupe_id") or f"{entree['groupe_sigle']}-{entree['legislature']}"]
        for cible in entree.get(CLE_SUCCESSION) or []:
            depart = par_id[cible]
            declares.add((depart["id"], arrivee["id"]))
            mesure = mesurer_couple(depart, arrivee)
            mesure["meme_legislature"] = depart["legislature"] == arrivee["legislature"]
            mesure["sigle_publie_identique"] = (
                depart["groupe_sigle"] == arrivee["groupe_sigle"]
            )
            liens.append(mesure)

    non_declares: list[dict[str, Any]] = []
    for depart in unites:
        for arrivee in unites:
            if int(arrivee["legislature"]) != int(depart["legislature"]) + 1:
                continue
            if (depart["id"], arrivee["id"]) in declares:
                continue
            mesure = mesurer_couple(depart, arrivee)
            if mesure["atteint_le_seuil"] is not None and mesure["communs"]:
                non_declares.append(mesure)
    non_declares.sort(key=_plus_proche_du_seuil)

    non_retrouves = [lien for lien in liens if lien["atteint_le_seuil"] is False]
    # Le sigle comme signal de lecture : un lien que personne ne songerait à
    # rouvrir (`RN → RN`) et qui rate le seuil passe devant les autres.
    non_retrouves.sort(
        key=lambda lien: (not lien["sigle_publie_identique"],) + _plus_proche_du_seuil(lien)
    )
    candidats = [m for m in non_declares if m["atteint_le_seuil"]]

    return {
        "seuil": f"{SEUIL_NUMERATEUR}/{SEUIL_DENOMINATEUR}",
        "legislatures": sorted({unite["legislature"] for unite in unites}, key=int),
        "liens_declares": liens,
        "liens_non_retrouves": non_retrouves,
        "candidats_non_declares": candidats,
        "ecartes_les_plus_proches": [
            m for m in non_declares if not m["atteint_le_seuil"]
        ][:max(proches, 0)],
        "organes_sans_entree": sans_entree,
        "non_mesurables": [lien for lien in liens if lien["atteint_le_seuil"] is None],
        "ecarts": len(non_retrouves) + len(candidats),
    }


def index_des_groupes(zip_path: Optional[Path] = None) -> dict[str, Any]:
    """L'index des groupes d'AMO30, sans jamais réécrire le cache partagé.

    Une archive **nommée** est lue sans passer par le cache : `charger_index_gp`
    écrit son index dans `.cache/acteurs_historique_an/`, partagé entre les
    sessions, et le réécrirait à la taille de l'archive passée. Payé le
    02/10/2026 en essayant l'audit sur l'archive réduite des tests — l'index
    partagé est tombé de 2 119 acteurs à 833, sans un mot.

    Raises:
        an_roster.RosterAnIndisponible: archive illisible, ou sans organe de groupe.
    """
    if zip_path is None:
        return an_roster.charger_index_gp()
    try:
        index = an_roster.construire_index_gp(Path(zip_path))
    except (zipfile.BadZipFile, OSError) as exc:
        raise an_roster.RosterAnIndisponible(
            f"Archive AMO30 illisible ({zip_path}) : {exc}"
        ) from exc
    if not index["organes"]:
        raise an_roster.RosterAnIndisponible(
            f"{zip_path} est lisible mais ne porte aucun organe de groupe."
        )
    return index


def rapport_filiation(
    *,
    zip_path: Optional[Path] = None,
    chemin_config: Optional[Path] = None,
    proches: int = PROCHES_PAR_DEFAUT,
) -> dict[str, Any]:
    """Charge la table committée et l'index AMO30, puis audite."""
    entrees = charger_correspondance_sigles(chemin_config)
    return auditer_filiation(index_des_groupes(zip_path), entrees, proches=proches)


# ── L'affichage ──────────────────────────────────────────────────────────────

def _ligne(mesure: dict[str, Any]) -> str:
    """Un couple sur une ligne : le décompte d'abord, le pourcentage ensuite."""
    depart = f"{mesure['depart']} ({'/'.join(mesure['sigles_an_depart'])})"
    arrivee = f"{mesure['arrivee']} ({'/'.join(mesure['sigles_an_arrivee'])})"
    if not mesure["base"]:
        decompte = "aucun membre connu d'un côté"
    else:
        part = 100 * mesure["communs"] / mesure["base"]
        decompte = (
            f"{mesure['communs']} sur {mesure['base']} ({part:.0f} %), "
            f"base : {'le départ' if mesure['base_prise_sur'] == 'depart' else 'l’arrivée'}"
        )
    return (
        f"  {depart} → {arrivee} : {decompte} "
        f"[{mesure['effectif_depart']} → {mesure['effectif_arrivee']}]"
    )


def _afficher(rapport: dict[str, Any]) -> None:
    liens = rapport["liens_declares"]
    mesures = [lien for lien in liens if lien["atteint_le_seuil"] is not None]
    retrouves = [lien for lien in mesures if lien["atteint_le_seuil"]]
    print(
        f"Filiation des lignées — législatures {', '.join(rapport['legislatures'])}, "
        f"seuil : la moitié du plus petit des deux groupes, non-inscrits exclus."
    )
    print(
        f"\n{len(liens)} lien(s) déclaré(s) dans la table : "
        f"{len(retrouves)} retrouvé(s), {len(rapport['liens_non_retrouves'])} non "
        f"retrouvé(s), {len(rapport['non_mesurables'])} non mesurable(s)."
    )

    if rapport["liens_non_retrouves"]:
        print("\n[ÉCART] Liens déclarés que la composition ne soutient pas :")
        for lien in rapport["liens_non_retrouves"]:
            marque = "  ← sigle publié identique" if lien["sigle_publie_identique"] else ""
            print(_ligne(lien) + marque)

    if rapport["candidats_non_declares"]:
        print("\n[ÉCART] Couples qui atteignent le seuil sans être déclarés :")
        for mesure in rapport["candidats_non_declares"]:
            print(_ligne(mesure))

    if retrouves:
        print("\nLiens déclarés retrouvés, du plus bas au plus haut :")
        for lien in sorted(retrouves, key=_plus_proche_du_seuil, reverse=True):
            marque = (
                "  ← même législature : un renommage écrit comme une succession"
                if lien["meme_legislature"] else ""
            )
            print(_ligne(lien) + marque)

    if rapport["non_mesurables"]:
        print("\nLiens déclarés non mesurables (un côté sans membre connu) :")
        for lien in rapport["non_mesurables"]:
            print(_ligne(lien))

    if rapport["ecartes_les_plus_proches"]:
        print("\nCouples non déclarés les plus proches du seuil (pas des écarts) :")
        for mesure in rapport["ecartes_les_plus_proches"]:
            print(_ligne(mesure))

    if rapport["organes_sans_entree"]:
        print(
            f"\n{len(rapport['organes_sans_entree'])} organe(s) de groupe de "
            "l'Assemblée sans entrée dans la table (hors non-inscrits) :"
        )
        for organe in rapport["organes_sans_entree"]:
            print(
                f"  {organe['organe_an']} {organe['sigle_an']} — {organe['nom']}, "
                f"législature {organe['legislature']}, "
                f"{organe['debut']} → {organe['fin'] or 'ouvert'}, "
                f"{organe['effectif']} personne(s)"
            )

    print(
        f"\n→ {rapport['ecarts']} écart(s) entre la table et la composition."
        if rapport["ecarts"] else
        "\n→ Aucun écart : la table et la composition disent la même chose."
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare les liens `succede_a` de config/groupes_reels.json "
                    "à la composition des groupes lue dans AMO30 (#1168). "
                    "N'écrit rien.",
    )
    parser.add_argument(
        "--proches",
        type=int,
        default=PROCHES_PAR_DEFAUT,
        metavar="N",
        help="Combien de couples non déclarés, sous le seuil, montrer pour lire "
             f"la marge. Défaut : {PROCHES_PAR_DEFAUT}.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Rendre le rapport en JSON sur la sortie standard, au lieu du texte.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="FICHIER",
        help=f"Défaut : {CHEMIN_CONFIG_GROUPES}.",
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
    args = _build_arg_parser().parse_args(argv)
    try:
        rapport = rapport_filiation(
            zip_path=args.archive,
            chemin_config=args.config,
            proches=args.proches,
        )
    except (
        an_roster.RosterAnInactif,
        an_roster.RosterAnIndisponible,
        CorrespondanceSiglesInvalide,
    ) as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        _afficher(rapport)
    return 1 if rapport["ecarts"] else 0


if __name__ == "__main__":
    sys.exit(main())
