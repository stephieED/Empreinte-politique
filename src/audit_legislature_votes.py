#!/usr/bin/env python3
"""audit_legislature_votes.py — La `legislature` des votes est-elle résoluble ? (#432)

Passe de corpus préalable à la normalisation des votes : elle dit si
`(legislature, numero_scrutin)` peut servir de clé sur l'ensemble des profils,
et par quel mécanisme chaque scrutin y arrive.

Séparée de la normalisation elle-même, et volontairement : elle ne modifie
aucun fichier. Un chantier qui découvrirait ses cas irrésolubles au milieu
d'une migration de schéma devrait la défaire ; ici on le sait avant.

Usage :
    python3 src/audit_legislature_votes.py
    python3 src/audit_legislature_votes.py --profils-dir pivot_data/profiles
    python3 src/audit_legislature_votes.py --out audit/legislature_votes.md

Code de sortie : 0 si tout est résoluble, 1 sinon — un scrutin irrésoluble ne
recevra JAMAIS de valeur par défaut (AGENTS.md §2.5), donc il bloque.
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scrutins_legislature import (  # noqa: E402
    LEGISLATURES_AN,
    PROVENANCE_CALENDRIER,
    PROVENANCE_COLLECTEE,
    PROVENANCE_JUMEAU,
    CleScrutin,
    provenance_par_occurrence,
    resoudre_legislatures,
)

DEFAUT_PROFILS_DIR = Path("raw_data") / "profiles"


def lire_votes(profils_dir: Path) -> Iterator[tuple[Path, dict[str, Any]]]:
    """Itère `(fichier, vote)` sur tous les profils d'un répertoire.

    Accepte indifféremment `raw_data/profiles/*.json` et
    `pivot_data/profiles/*.pivot.json` : le triplet lu (`numero_scrutin`,
    `date`, `legislature`) porte le même nom dans les deux schémas.
    """
    if not profils_dir.is_dir():
        return
    for chemin in sorted(profils_dir.glob("*.json")):
        if chemin.name.startswith("."):
            continue
        try:
            with open(chemin, encoding="utf-8") as f:
                profil = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            print(f"  [!] Lecture impossible de {chemin}, ignoré : {exc}")
            continue
        for vote in (profil.get("votes") or []):
            if isinstance(vote, dict):
                yield chemin, vote


def analyser(profils_dir: Path) -> dict[str, Any]:
    occurrences: list[tuple[Any, Any, Any]] = []
    votes_bruts: list[tuple[Path, CleScrutin, Any]] = []
    for chemin, vote in lire_votes(profils_dir):
        cle = CleScrutin(vote.get("numero_scrutin"), vote.get("date"))
        legislature = vote.get("legislature")
        occurrences.append((cle.numero_scrutin, cle.date, legislature))
        votes_bruts.append((chemin, cle, legislature))

    resolutions, echecs = resoudre_legislatures(occurrences)

    # Provenance côté scrutin (une entrée par scrutin distinct) et côté paire
    # (membre, vote) : la première dit combien de faits sont dérivés, la seconde
    # combien d'enregistrements en dépendent. Les deux comptent.
    par_scrutin = Counter(r.provenance for r in resolutions.values())
    par_occurrence: Counter[str] = Counter()
    profils_touches: dict[str, set[str]] = {PROVENANCE_JUMEAU: set(), PROVENANCE_CALENDRIER: set()}
    for chemin, cle, legislature in votes_bruts:
        resolution = resolutions.get(cle)
        if resolution is None:
            par_occurrence["irresoluble"] += 1
            continue
        provenance = provenance_par_occurrence(legislature, resolution)
        par_occurrence[provenance] += 1
        if provenance in profils_touches:
            profils_touches[provenance].add(chemin.stem)

    legislatures = Counter(r.legislature for r in resolutions.values())

    return {
        "profils_dir": str(profils_dir),
        "n_paires": len(votes_bruts),
        "n_scrutins": len(resolutions) + len(echecs),
        "par_scrutin": par_scrutin,
        "par_occurrence": par_occurrence,
        "profils_touches": {k: len(v) for k, v in profils_touches.items()},
        "legislatures": legislatures,
        "echecs": echecs,
    }


def _rendre(rapport: dict[str, Any]) -> str:
    n_paires = rapport["n_paires"]
    n_scrutins = rapport["n_scrutins"]
    par_scrutin = rapport["par_scrutin"]
    par_occurrence = rapport["par_occurrence"]
    echecs = rapport["echecs"]

    lignes = [
        f"# Résolution de `legislature` sur les votes — `{rapport['profils_dir']}`",
        "",
        f"- paires (membre, vote) : **{n_paires}**",
        f"- scrutins distincts `(numero_scrutin, date)` : **{n_scrutins}**",
    ]
    if n_scrutins:
        lignes.append(f"- facteur de duplication : **{n_paires / n_scrutins:.1f} ×**")
    lignes += ["", "## Par scrutin", "", "| Provenance | Scrutins |", "|---|---|"]
    for provenance, libelle in (
        (PROVENANCE_COLLECTEE, "collectée (portée par au moins une occurrence)"),
        (PROVENANCE_CALENDRIER, "dérivée du calendrier des législatures"),
    ):
        lignes.append(f"| {libelle} | {par_scrutin.get(provenance, 0)} |")
    lignes.append(f"| **irrésoluble** | **{len(echecs)}** |")

    lignes += ["", "## Par paire (membre, vote)", "", "| Provenance | Paires |", "|---|---|"]
    for provenance, libelle in (
        (PROVENANCE_COLLECTEE, "collectée"),
        (PROVENANCE_JUMEAU, "résolue par jumeau étiqueté"),
        (PROVENANCE_CALENDRIER, "dérivée du calendrier"),
    ):
        lignes.append(f"| {libelle} | {par_occurrence.get(provenance, 0)} |")
    lignes.append(f"| **irrésoluble** | **{par_occurrence.get('irresoluble', 0)}** |")

    lignes += [
        "",
        f"Profils concernés par une résolution par jumeau : "
        f"{rapport['profils_touches'].get(PROVENANCE_JUMEAU, 0)} · "
        f"par une dérivation calendaire : "
        f"{rapport['profils_touches'].get(PROVENANCE_CALENDRIER, 0)}",
        "",
        "## Législatures résolues",
        "",
        "| Législature | Période | Scrutins |",
        "|---|---|---|",
    ]
    for legislature in sorted(rapport["legislatures"]):
        debut, fin = LEGISLATURES_AN.get(legislature, ("?", "?"))
        lignes.append(
            f"| {legislature} | {debut} → {fin or 'en cours'} | {rapport['legislatures'][legislature]} |"
        )

    if echecs:
        lignes += [
            "",
            "## ⛔ Scrutins irrésolubles",
            "",
            "Aucune valeur par défaut n'est posée (AGENTS.md §2.5) : ces scrutins bloquent",
            "la normalisation tant que la collecte n'est pas corrigée, ou `LEGISLATURES_AN`",
            "étendue si une nouvelle législature a commencé.",
            "",
            "| Scrutin | Date | Motif | Détail |",
            "|---|---|---|---|",
        ]
        for echec in echecs[:50]:
            lignes.append(
                f"| {echec.cle.numero_scrutin} | {echec.cle.date} | {echec.motif} | {echec.detail} |"
            )
        if len(echecs) > 50:
            lignes.append(f"| … | | {len(echecs) - 50} autre(s) non listé(s) | |")
    else:
        lignes += ["", "✅ Tous les scrutins sont résolus — la clé `(legislature, numero_scrutin)` est utilisable."]

    return "\n".join(lignes) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profils-dir", default=str(DEFAUT_PROFILS_DIR),
                        help=f"Répertoire de profils à analyser (défaut : {DEFAUT_PROFILS_DIR})")
    parser.add_argument("--out", default=None, metavar="FICHIER",
                        help="Écrire aussi le rapport Markdown dans ce fichier.")
    args = parser.parse_args()

    rapport = analyser(Path(args.profils_dir))
    rendu = _rendre(rapport)
    print(rendu)

    if args.out:
        chemin = Path(args.out)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(rendu, encoding="utf-8")
        print(f"Rapport → {chemin}")

    return 1 if rapport["echecs"] else 0


if __name__ == "__main__":
    sys.exit(main())
