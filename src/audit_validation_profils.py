#!/usr/bin/env python3
"""
audit_validation_profils.py — `validate_profil()` passé sur chaque profil
publié, et un rapport qui nomme ceux qui ne le passent pas (#1223).

## Pourquoi ce contrôle existe

`validate_profil()` porte les invariants du schéma pivot — vocabulaires fermés,
source d'une position dans l'hémicycle, absences accompagnées de leur motif —,
et **aucun job ne l'exécutait**. Mesuré le 05/10/2026 : 16 des 34 fiches de
candidats déclarés publiées ne le passaient pas, 38 erreurs d'une seule
famille, écrites depuis trois semaines sans que rien le dise. Un vocabulaire
fermé que personne ne vérifie n'est pas fermé.

## Il signale, il ne bloque pas

Arbitrage de la propriétaire, 06/10/2026 : une fiche hors schéma **ne bloque
pas** le run — elle ouvre une issue de suivi sur le dépôt de développement, une
seule, tenue à jour à chaque run tant que le défaut dure et fermée par le run
qui ne le trouve plus. Le workflow s'en charge à partir du rapport JSON ; ce
module ne parle à personne.

D'où un code de sortie **toujours nul** quand le contrôle a pu tourner : le
signal est le rapport. Seul un répertoire illisible sort en erreur — un contrôle
qui n'a rien regardé ne doit pas passer pour un contrôle qui n'a rien trouvé.

## Ce qu'il ne vérifie pas

Les deux **jointures** de `validate_profil()` — un `scrutin_id` et un
`amendement_id` référencés existent, et la règle 4 sur le 49.3 — demandent les
index, et ne sont pas rejouées ici : `audit_integrite_referentielle.py` (#485)
les tient déjà, en bloquant. Le rapport le dit.

## Un profil à la fois

Les profils sont lus et validés un par un, jamais tous en mémoire : le corpus
pèse plusieurs gigaoctets et le job de fusion n'a pas cette marge.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from population_profils import SUFFIXE_PIVOT, provenance_du_profil, ventiler_provenances
from schema_pivot import validate_profil

#: Au-delà, les erreurs d'un profil sont comptées et non listées : une famille
#: d'erreurs répétée sur chaque mandat noierait les autres profils du rapport.
MAX_ERREURS_LISTEES = 8


def auditer(profils_dir: Path) -> dict[str, Any]:
    """Valide chaque `*.pivot.json` de `profils_dir`, un par un.

    Rend `{"controles": ventilation, "invalides": [...], "illisibles": [...]}`.
    Un fichier illisible n'est pas « valide » : il est nommé à part.
    """
    provenances: list[str] = []
    invalides: list[dict[str, Any]] = []
    illisibles: list[str] = []
    for chemin in sorted(profils_dir.glob("*" + SUFFIXE_PIVOT)):
        slug = chemin.name[: -len(SUFFIXE_PIVOT)]
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            illisibles.append(slug)
            continue
        provenance = provenance_du_profil(profil)
        provenances.append(provenance)
        erreurs = validate_profil(profil)
        if erreurs:
            invalides.append({"slug": slug, "provenance": provenance, "erreurs": erreurs})
        del profil
    return {
        "controles": ventiler_provenances(provenances, illisibles=len(illisibles)).as_dict(),
        "invalides_ventilation": ventiler_provenances(
            e["provenance"] for e in invalides
        ).as_dict(),
        "invalides": invalides,
        "illisibles": illisibles,
        "erreurs_total": sum(len(e["erreurs"]) for e in invalides),
    }


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    from population_profils import Ventilation

    controles = Ventilation.depuis_dict(rapport.get("controles"))
    invalides = rapport.get("invalides") or []
    lignes = [f"Profils contrôlés : {controles.cellule_markdown()}", ""]
    if rapport.get("illisibles"):
        lignes += [
            "**Fichiers illisibles, donc non contrôlés** : "
            + ", ".join(f"`{s}`" for s in rapport["illisibles"]),
            "",
        ]
    if not invalides:
        lignes.append("Tous passent `validate_profil()`.")
    else:
        ventilation = Ventilation.depuis_dict(rapport.get("invalides_ventilation"))
        lignes += [
            f"**Profils hors schéma : {ventilation.cellule_markdown()}** — "
            f"{rapport.get('erreurs_total', 0)} erreur(s).",
            "",
            "| Profil | Population | Erreurs |",
            "| --- | --- | --- |",
        ]
        for entree in invalides:
            erreurs = entree["erreurs"]
            listees = [e.replace("|", "\\|").replace("\n", " ") for e in erreurs[:MAX_ERREURS_LISTEES]]
            if len(erreurs) > MAX_ERREURS_LISTEES:
                listees.append(f"… et {len(erreurs) - MAX_ERREURS_LISTEES} autre(s)")
            lignes.append(
                f"| `{entree['slug']}` | {entree['provenance']} | "
                f"{len(erreurs)} — " + "<br>".join(listees) + " |"
            )
    lignes += [
        "",
        "Non rejoué ici : l'existence des scrutins et des amendements référencés, "
        "que tient le contrôle d'intégrité référentielle (#485).",
    ]
    return "\n".join(lignes) + "\n"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--profils-dir", type=Path, default=Path("pivot_data") / "profiles")
    parser.add_argument("--out", type=Path, default=None, help="Rapport Markdown.")
    parser.add_argument("--out-json", type=Path, default=None, help="Rapport JSON.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not args.profils_dir.is_dir():
        print(f"[!] {args.profils_dir} : répertoire introuvable.", file=sys.stderr)
        return 2
    rapport = auditer(args.profils_dir)
    markdown = generate_markdown_report(rapport)
    if args.out:
        args.out.write_text(markdown, encoding="utf-8")
    if args.out_json:
        args.out_json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(markdown)
    return 0


if __name__ == "__main__":
    sys.exit(main())
