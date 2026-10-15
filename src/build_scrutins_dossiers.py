#!/usr/bin/env python3
"""build_scrutins_dossiers.py — Construit `pivot_data/scrutins_dossiers.json` (#758).

CE QUE LE FICHIER PORTE, ET POURQUOI RIEN NE LE PORTAIT. Un scrutin de
l'Assemblée ne nomme pas le texte qu'il tranche : `objet.referenceLegislative`
et `demandeur.referenceLegislative` sont nuls sur 0/18 311 scrutins bruts des
législatures 14 à 17. Le lien n'existe qu'en sens inverse, dans le dossier —
`actesLegislatifs[].voteRefs`. Ce fichier le publie, et publie avec lui l'issue
du dossier :

    {"scrutins": {"an:17:960": "DLR5L17N51481"},
     "dossiers": {"DLR5L17N51481": {"statut": "adopte", "sort_49_3": false}}}

Ce qu'il débloque : d'un vote publié, la **commission saisie au fond** (par
jointure dans `commissions_dossiers.json`) et le **sort du dossier** — ni l'une
ni l'autre n'étaient atteignables. Le sort du *scrutin* ne disait que si CE
scrutin-là avait adopté : 17 non-adoptés sur les 697 textes en dernière
lecture, contre 32 rejetés côté dossier.

POURQUOI UN FICHIER À PART, ET PAS UN CHAMP SUR `scrutins.json`. Les deux
tables ne se collectent pas au même endroit : les scrutins viennent de
`Scrutins.json.zip`, le rattachement des dossiers de `dossiers*.zip`. Poser le
champ sur le scrutin coupleait la construction des scrutins aux archives de
dossiers, et rendrait un `dossier_id: null` indistinguable d'un run qui n'a pas
lu les dossiers. Un fichier à part se lit — ou ne se lit pas —, et son absence
est alors visible. Même précédent que `commissions_dossiers.json` (#328).

ADDITIF, JAMAIS DESTRUCTEUR. Un run sans archives lisibles rend une table vide,
et le fichier déjà publié est **conservé** : une collecte vide n'écrase jamais
une collecte non vide (AGENTS.md §3a, #465). `--no-merge` force la
reconstruction complète, à réserver à un run qui a bien lu toutes les archives.

LA CASCADE DE #1289. Un vote que l'Assemblée ne pose dans aucun dossier (265
des 934 votes sur l'ensemble, 15/10/2026) reçoit le sien, dans cet ordre : la
source, puis la déduction de `rattachement_deduit`, puis — en dernier, pour ce
que ni l'une ni l'autre ne rattache — la table relue à la main
(`config/rattachements_scrutins_dossiers.json`). Ce qui ne vient pas de la
source est nommé dans une troisième table, `provenance` (`table_relue`,
`deduit_date_et_titre`). → `docs/decisions/rattachement-deduit-votes-sans-dossier-1289.md`

Usage :
    python3 src/build_scrutins_dossiers.py
    python3 src/build_scrutins_dossiers.py --out pivot_data/scrutins_dossiers.json
    python3 src/build_scrutins_dossiers.py --no-merge
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from json_io import dumps_indente, ecrire_index_json  # noqa: E402
from licences import LICENCE_AN  # noqa: E402
import rattachement_deduit as rd  # noqa: E402
from gouvernement_textes import ensure_dossiers_zips_downloaded  # noqa: E402
from scrutins_dossiers_an import SCHEMA_VERSION, charger_table  # noqa: E402
from scrutins_index import DEFAULT_SCRUTINS_PATH, charger as charger_scrutins  # noqa: E402

DEFAUT_SORTIE = Path("pivot_data") / "scrutins_dossiers.json"


def _lire_existant(chemin: Path) -> dict[str, dict]:
    """Tables déjà publiées, ou vides — un fichier illisible ne fait pas échouer."""
    vide: dict[str, dict] = {"scrutins": {}, "dossiers": {}, "provenance": {}}
    if not chemin.is_file():
        return vide
    try:
        with open(chemin, encoding="utf-8") as f:
            publie = json.load(f)
    except (json.JSONDecodeError, OSError):
        return vide
    if not isinstance(publie, dict):
        return vide
    return {
        cle: (publie.get(cle) if isinstance(publie.get(cle), dict) else {})
        for cle in ("scrutins", "dossiers", "provenance")
    }


def _decisions_des_archives() -> dict:
    """Les décisions de séance des archives — déjà téléchargées par
    `charger_table`, relues ici sans réseau supplémentaire."""
    archives = ensure_dossiers_zips_downloaded()
    if not archives:
        return {"decisions": {}, "dossiers": {}}
    return rd.indexer_decisions(archives)


def composer(
    ancienne: dict[str, dict],
    collectee: dict[str, dict],
    scrutins_publies: list[dict],
    decisions: dict | None,
    table: dict,
) -> dict[str, dict]:
    """La cascade de #1289 : source, puis déduction, puis table relue.

    La table relue ne comble que ce qui reste : une de ses lignes n'écrase
    jamais un rattachement de la source ni une déduction (arbitrage de la
    propriétaire, 15/10/2026). Une ligne devenue inutile est comptée, pour
    qu'on la retire.

    `decisions` à `None` veut dire « archives non lues à ce run » : les
    rattachements déduits d'un run précédent sont alors gardés tels quels,
    jamais recalculés à vide (§3a, #465). Lues, ils sont recalculés en entier —
    une déduction que la source rend inutile, ou qu'une décision prise entre-
    temps rend ambiguë, disparaît.
    """
    provenance_avant = ancienne.get("provenance") or {}
    source = {
        cle: uid for cle, uid in (ancienne.get("scrutins") or {}).items()
        if cle not in provenance_avant
    }
    source.update(collectee.get("scrutins") or {})
    dossiers = dict(ancienne.get("dossiers") or {})
    dossiers.update(collectee.get("dossiers") or {})

    if decisions is None:
        deduits = {
            cle: ancienne["scrutins"][cle]
            for cle, origine in provenance_avant.items()
            if origine == rd.PROVENANCE_DEDUITE and cle in (ancienne.get("scrutins") or {})
            and cle not in source
        }
    else:
        deduits = rd.deduire(scrutins_publies, set(source), decisions)

    manuels = {cle: ligne["dossier"] for cle, ligne in table["rattachements"].items()}

    scrutins = dict(source)
    provenance: dict[str, str] = {}
    for cle, uid in deduits.items():
        scrutins[cle] = uid
        provenance[cle] = rd.PROVENANCE_DEDUITE
    inutiles = []
    for cle, uid in manuels.items():
        if cle in scrutins:
            inutiles.append(cle)
            continue
        scrutins[cle] = uid
        provenance[cle] = rd.PROVENANCE_TABLE

    connus = (decisions or {}).get("dossiers") or {}
    for cle in provenance:
        uid = scrutins[cle]
        if uid not in dossiers:
            info = connus.get(uid) or {}
            dossiers[uid] = {"statut": info.get("statut"), "sort_49_3": info.get("sort_49_3")}
    return {
        "scrutins": scrutins, "dossiers": dossiers, "provenance": provenance,
        "lignes_inutiles": sorted(inutiles),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--out",
        default=str(DEFAUT_SORTIE),
        help=f"Fichier à écrire (défaut : {DEFAUT_SORTIE}).",
    )
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Reconstruction complète au lieu d'une fusion additive avec ce qui "
             "est publié. À réserver à un run qui a lu toutes les archives : sur "
             "un run partiel, les rattachements non revus disparaîtraient.",
    )
    parser.add_argument(
        "--scrutins",
        default=str(DEFAULT_SCRUTINS_PATH),
        help="Index des scrutins publiés, dont les votes sans dossier reçoivent "
             f"une déduction (défaut : {DEFAULT_SCRUTINS_PATH}).",
    )
    parser.add_argument(
        "--table",
        default=str(rd.TABLE_MANUELLE),
        help=f"Table relue à la main (défaut : {rd.TABLE_MANUELLE}).",
    )
    args = parser.parse_args(argv)

    chemin = Path(args.out)
    collectee = charger_table()
    if not collectee.get("scrutins"):
        # Nommer l'absence plutôt que de publier une table muette.
        print("  [!] Archives de dossiers indisponibles : aucun rattachement "
              "scrutin → dossier collecté à ce run.")

    ancienne = (
        {"scrutins": {}, "dossiers": {}, "provenance": {}}
        if args.no_merge else _lire_existant(chemin)
    )
    lue = bool(collectee.get("scrutins"))
    publies = list(charger_scrutins(Path(args.scrutins)).par_id.values()) if lue else []
    composee = composer(
        ancienne,
        collectee,
        publies,
        _decisions_des_archives() if lue else None,
        rd.charger_table_manuelle(Path(args.table)),
    )
    scrutins, dossiers, provenance = (
        composee["scrutins"], composee["dossiers"], composee["provenance"]
    )

    if not scrutins:
        print("  [!] Table vide et rien de publié : aucun fichier écrit.")
        return 0

    ecrire_index_json(
        chemin,
        {
            "schema_version": SCHEMA_VERSION,
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": LICENCE_AN,
            "scrutins": scrutins,
            "dossiers": dossiers,
            # Absent d'ici, un rattachement est celui que l'Assemblée publie (#1289).
            "provenance": provenance,
        },
        dumps_indente,
    )
    lus = collectee.get("scrutins") or {}
    conservees = sum(1 for cle in scrutins if cle not in lus and cle not in provenance)
    sans_statut = sum(1 for d in dossiers.values() if not d.get("statut"))
    print(f"  ✓ {len(scrutins)} scrutin(s) rattaché(s) à {len(dossiers)} dossier(s) → {chemin}")
    if sans_statut:
        print(f"      dont {sans_statut} dossier(s) sans statut résolu (absence déclarée)")
    for origine, libelle in (
        (rd.PROVENANCE_DEDUITE, "déduit(s) par la date et le titre"),
        (rd.PROVENANCE_TABLE, "pris dans la table relue à la main"),
    ):
        nombre = sum(1 for p in provenance.values() if p == origine)
        if nombre:
            print(f"      dont {nombre} rattachement(s) {libelle} (#1289)")
    if composee["lignes_inutiles"]:
        print(
            f"  [!] {len(composee['lignes_inutiles'])} ligne(s) de {args.table} sans effet : "
            f"la source ou la déduction rattache déjà ces votes — à retirer de la table : "
            + ", ".join(composee["lignes_inutiles"])
        )
    if conservees > 0:
        print(f"      dont {conservees} rattachement(s) conservé(s) d'un run précédent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
