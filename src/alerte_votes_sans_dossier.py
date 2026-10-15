#!/usr/bin/env python3
"""alerte_votes_sans_dossier.py — Les doublons possibles qu'aucun rattachement ne règle (#1289).

Après la cascade de `build_scrutins_dossiers.py` (source, déduction, puis
table relue), un vote sur l'ensemble d'un texte peut rester sans dossier.
L'interface regroupe alors ses lectures par l'intitulé, et un texte dont
l'Assemblée a reformulé le titre s'affiche deux fois.

Ce script ne corrige rien : il **signale**. Il relève chaque paire de textes
d'une même législature, l'un au moins sans dossier, dont les intitulés
partagent au moins la moitié de leurs mots (`SEUIL_PAIRE`) — la mesure de
l'issue, qui a trouvé 21 doublons en relisant 41 paires. Une paire déjà jugée
dans `config/rattachements_scrutins_dossiers.json` (`textes_distincts`) n'est
plus signalée.

**Il ne fait jamais échouer le run** : le run publie, puis une étape tient à
jour une issue de suivi sur le dépôt de développement, comme pour les fiches
hors schéma (#1223). Borne basse : un intitulé très reformulé lui échappe.

Usage :
    python3 src/alerte_votes_sans_dossier.py
    python3 src/alerte_votes_sans_dossier.py --md alerte.md --json alerte.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rattachement_deduit as rd  # noqa: E402
from scrutins_index import DEFAULT_SCRUTINS_PATH, charger as charger_scrutins  # noqa: E402

DEFAUT_TABLE_DOSSIERS = Path("pivot_data") / "scrutins_dossiers.json"

#: Part de mots communs (Jaccard) au-delà de laquelle deux textes sans clé
#: commune sont présentés à la relecture. 0,5 : 41 paires relues le
#: 15/10/2026, dont 21 doublons réels.
SEUIL_PAIRE = 0.5

RX_TETE = re.compile(r"^(?:sur )?l'ensemble (?:du |de la |de l'|des )?")
RX_LECTURE = re.compile(r"\s*\([^()]*\)\s*\.?\s*$")


def intitule_du_texte(libelle: str) -> str:
    """L'intitulé du vote sans « l'ensemble du » ni la mention de lecture."""
    texte = RX_TETE.sub("", rd.normaliser(libelle))
    while True:
        court = RX_LECTURE.sub("", texte)
        if court == texte:
            break
        texte = court
    return texte.strip(" .")


def relever(
    scrutins: list[dict], rattaches: dict[str, str], distincts: list[list[str]]
) -> list[dict]:
    """Les paires suspectes, chaque côté décrit par ses votes."""
    groupes: dict[tuple[str, str], dict] = {}
    for scrutin in scrutins:
        cle = scrutin.get("id")
        if not isinstance(cle, str) or not cle.startswith("an:"):
            continue
        if not rd.est_vote_sur_l_ensemble(scrutin):
            continue
        legislature = str(scrutin.get("legislature") or cle.split(":")[1])
        dossier = rattaches.get(cle)
        cle_groupe = ("dossier:" + dossier) if dossier else ("titre:" + intitule_du_texte(scrutin.get("texte") or ""))
        groupe = groupes.setdefault(
            (legislature, cle_groupe),
            {"legislature": legislature, "dossier": dossier, "intitule": intitule_du_texte(scrutin.get("texte") or ""), "votes": []},
        )
        groupe["votes"].append(cle)
    deja_juges = [set(groupe) for groupe in distincts]
    paires = []
    cles = sorted(groupes)
    for i, a in enumerate(cles):
        for b in cles[i + 1:]:
            ga, gb = groupes[a], groupes[b]
            if ga["legislature"] != gb["legislature"]:
                continue
            if ga["dossier"] and gb["dossier"]:
                continue
            ma, mb = rd.mots(ga["intitule"]), rd.mots(gb["intitule"])
            if not ma or not mb or len(ma & mb) / len(ma | mb) < SEUIL_PAIRE:
                continue
            ensemble = set(ga["votes"]) | set(gb["votes"])
            if any(ensemble <= juge for juge in deja_juges):
                continue
            paires.append({"a": ga, "b": gb, "jaccard": round(len(ma & mb) / len(ma | mb), 2)})
    return paires


def en_markdown(paires: list[dict], sans_dossier: int) -> str:
    lignes = [
        f"**{len(paires)} paire(s) de textes à relire**, sur {sans_dossier} vote(s) sur "
        "l'ensemble d'un texte restés sans dossier après la cascade (table relue, "
        "source, déduction).",
        "",
        "Pour chaque paire : même texte → une ligne par vote sans dossier dans "
        "`config/rattachements_scrutins_dossiers.json` (`rattachements`) ; textes "
        "différents → les votes des deux côtés dans `textes_distincts`.",
        "",
    ]
    if paires:
        lignes += ["| Votes | Dossier | Votes | Dossier | Mots communs | Intitulé |", "| --- | --- | --- | --- | --- | --- |"]
        for p in paires:
            a, b = p["a"], p["b"]
            lignes.append(
                f"| {', '.join(a['votes'])} | {a['dossier'] or '—'} | {', '.join(b['votes'])} "
                f"| {b['dossier'] or '—'} | {p['jaccard']} | {a['intitule'][:90]} |"
            )
    return "\n".join(lignes) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scrutins", default=str(DEFAULT_SCRUTINS_PATH))
    parser.add_argument("--dossiers", default=str(DEFAUT_TABLE_DOSSIERS))
    parser.add_argument("--table", default=str(rd.TABLE_MANUELLE))
    parser.add_argument("--md", default="alerte-votes-sans-dossier.md")
    parser.add_argument("--json", default="alerte-votes-sans-dossier.json")
    args = parser.parse_args(argv)

    scrutins = list(charger_scrutins(Path(args.scrutins)).par_id.values())
    try:
        with open(args.dossiers, encoding="utf-8") as f:
            rattaches = json.load(f).get("scrutins") or {}
    except (OSError, json.JSONDecodeError):
        rattaches = {}
    table = rd.charger_table_manuelle(Path(args.table))
    paires = relever(scrutins, rattaches, table["textes_distincts"])
    sans_dossier = sum(
        1 for s in scrutins
        if str(s.get("id", "")).startswith("an:") and rd.est_vote_sur_l_ensemble(s)
        and s.get("id") not in rattaches
    )
    Path(args.md).write_text(en_markdown(paires, sans_dossier), encoding="utf-8")
    Path(args.json).write_text(
        json.dumps({"paires": paires, "sans_dossier": sans_dossier}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(f"  {len(paires)} paire(s) à relire ; {sans_dossier} vote(s) sur l'ensemble sans dossier")
    return 0


if __name__ == "__main__":
    sys.exit(main())
