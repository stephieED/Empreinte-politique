#!/usr/bin/env python3
"""
audit_pipeline.py — Point d'entrée manuel compilant les audits profils + groupes
+ gouvernements.

Outil manuel de qualité interne (issue #178, plan #174 ; intégration
gouvernement issue #321, sous-issue 5/6 de #316), distinct de
`check_quality_gate.py` (seul gate bloquant en CI) : n'est appelé nulle part
dans `.github/workflows/`, usage manuel uniquement.

Appelle directement les fonctions de `audit_pivot_dataset.py`,
`audit_groupe_dataset.py` et `audit_gouvernement_dataset.py` (pas de
sous-processus) et compose leurs trois rapports en un seul, avec une section
"vue d'ensemble" ajoutée en plus des trois rapports détaillés : totaux
profils/groupes/gouvernements audités, erreurs de lecture agrégées, warnings
agrégés tous documents confondus. Pure composition à partir des rapports déjà
assemblés par les modules `audit_*` — aucune nouvelle logique de calcul
métier n'est introduite ici (AGENTS.md §2.1 : pas de score, pas de
classement).

Aucune dépendance lourde : stdlib uniquement.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import audit_gouvernement_dataset
import audit_rattachements
import audit_groupe_dataset
import audit_pivot_dataset


def compute_vue_ensemble(
    rapport_profils: dict[str, Any],
    rapport_groupes: dict[str, Any],
    rapport_gouvernements: dict[str, Any],
    rapport_rattachements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile une vue d'ensemble à partir des trois rapports d'audit déjà assemblés.

    Pure composition : additionne/regroupe les totaux et warnings déjà
    calculés par `audit_pivot_dataset.build_report`,
    `audit_groupe_dataset.build_report` et
    `audit_gouvernement_dataset.build_report`, sans recalculer aucun
    indicateur à partir des profils/groupes/gouvernements bruts.

    Returns:
        `{"total_profils_audites": int, "total_groupes_audites": int,
        "total_gouvernements_audites": int, "total_erreurs_lecture": int,
        "erreurs_lecture": {"profils": [...], "groupes": [...],
        "gouvernements": [...]}, "warnings": {"total_warnings": int,
        "par_type": {type: {"frequence": int, "profils_ids": [...],
        "groupe_ids": [...], "gouvernement_ids": [...]}}}}`. `par_type`
        couvre l'union des types rencontrés côté profils, groupes et
        gouvernements ; un type absent d'un des trois audits a une liste
        d'`ids` vide pour ce côté.
    """
    warnings_profils = rapport_profils["warnings"]["par_type"]
    warnings_groupes = rapport_groupes["warnings"]["par_type"]
    warnings_gouvernements = rapport_gouvernements["warnings"]["par_type"]

    par_type: dict[str, Any] = {}
    for type_warning in sorted(
        set(warnings_profils) | set(warnings_groupes) | set(warnings_gouvernements)
    ):
        entree_profils = warnings_profils.get(type_warning)
        entree_groupes = warnings_groupes.get(type_warning)
        entree_gouvernements = warnings_gouvernements.get(type_warning)
        par_type[type_warning] = {
            "frequence": (
                (entree_profils["frequence"] if entree_profils else 0)
                + (entree_groupes["frequence"] if entree_groupes else 0)
                + (entree_gouvernements["frequence"] if entree_gouvernements else 0)
            ),
            "profils_ids": entree_profils["ids"] if entree_profils else [],
            "groupe_ids": entree_groupes["groupe_ids"] if entree_groupes else [],
            "gouvernement_ids": (
                entree_gouvernements["gouvernement_ids"] if entree_gouvernements else []
            ),
        }

    return {
        "total_profils_audites": rapport_profils["meta"]["total_profils"],
        "total_groupes_audites": rapport_groupes["meta"]["total_groupes"],
        "total_gouvernements_audites": rapport_gouvernements["meta"]["total_gouvernements"],
        "total_erreurs_lecture": (
            rapport_profils["meta"]["total_erreurs_lecture"]
            + rapport_groupes["meta"]["total_erreurs_lecture"]
            + rapport_gouvernements["meta"]["total_erreurs_lecture"]
        ),
        "erreurs_lecture": {
            "profils": rapport_profils["erreurs_lecture"],
            "groupes": rapport_groupes["erreurs_lecture"],
            "gouvernements": rapport_gouvernements["erreurs_lecture"],
        },
        "warnings": {
            "total_warnings": (
                rapport_profils["warnings"]["total_warnings"]
                + rapport_groupes["warnings"]["total_warnings"]
                + rapport_gouvernements["warnings"]["total_warnings"]
            ),
            "par_type": par_type,
        },
    }


def build_report(
    rapport_profils: dict[str, Any],
    rapport_groupes: dict[str, Any],
    rapport_gouvernements: dict[str, Any],
    rapport_rattachements: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble les rapports profils, groupes et gouvernements en un rapport combiné unique.

    Args:
        rapport_profils: sortie de `audit_pivot_dataset.build_report`.
        rapport_rattachements: sortie d'`audit_rattachements.audit_rattachements`,
            calculée par l'appelant. Absente, la section est simplement vide.
        rapport_groupes: sortie de `audit_groupe_dataset.build_report`.
        rapport_gouvernements: sortie de `audit_gouvernement_dataset.build_report`.

    Returns:
        `{"meta": {...}, "vue_ensemble": {...}, "audit_profils": {...},
        "audit_groupes": {...}, "audit_gouvernements": {...}}`. Les trois
        sous-rapports détaillés sont ceux produits tels quels par les
        modules `audit_*` — aucune donnée n'y est recalculée ni modifiée.
    """
    return {
        "meta": {
            "genere_le": rapport_profils["meta"]["genere_le"],
            "staleness_days": rapport_profils["meta"]["staleness_days"],
        },
        "vue_ensemble": compute_vue_ensemble(
            rapport_profils, rapport_groupes, rapport_gouvernements
        ),
        "audit_profils": rapport_profils,
        "audit_groupes": rapport_groupes,
        "audit_gouvernements": rapport_gouvernements,
        # Les rattachements que le dépôt a dû ÉTABLIR lui-même : aucun n'est
        # donné par la source, et c'est pour ça qu'ils méritent d'être suivis.
        # Jamais bloquant — voir l'en-tête d'`audit_rattachements`.
        #
        # PASSÉ EN ARGUMENT, JAMAIS CALCULÉ ICI. `build_report` assemble et ne
        # recalcule rien — c'est son contrat, écrit dans sa docstring. L'appeler
        # sans argument le faisait lire le corpus vivant, ce qu'AGENTS.md §3b
        # interdit aux tests : les trois appels de `test_audit_pipeline.py`
        # scannaient 509 744 amendements chacun, et la suite passait de 60 s à
        # 185 s. Le calcul appartient au CLI.
        "audit_rattachements": rapport_rattachements or {},
    }


# ---------------------------------------------------------------------------
# Génération du rapport Markdown
# ---------------------------------------------------------------------------

def _md_escape(valeur: Any) -> str:
    """Neutralise les caractères cassant une cellule de tableau Markdown."""
    texte = "" if valeur is None else str(valeur)
    return texte.replace("|", "\\|").replace("\n", " ")


def _md_table(en_tetes: list[str], lignes: list[list[Any]], si_vide: str) -> str:
    """Construit un tableau Markdown, ou renvoie `si_vide` si `lignes` est vide."""
    if not lignes:
        return si_vide + "\n"

    entete = "| " + " | ".join(en_tetes) + " |"
    separateur = "| " + " | ".join("---" for _ in en_tetes) + " |"
    corps = "\n".join(
        "| " + " | ".join(_md_escape(cellule) for cellule in ligne) + " |" for ligne in lignes
    )
    return f"{entete}\n{separateur}\n{corps}\n"


def _md_section_vue_ensemble(vue: dict[str, Any]) -> str:
    lignes_totaux = [
        ["Profils audités", vue["total_profils_audites"]],
        ["Groupes audités", vue["total_groupes_audites"]],
        ["Gouvernements audités", vue["total_gouvernements_audites"]],
        ["Erreurs de lecture (profils + groupes + gouvernements)", vue["total_erreurs_lecture"]],
        ["Warnings (profils + groupes + gouvernements)", vue["warnings"]["total_warnings"]],
    ]

    lignes_warnings = [
        [
            type_warning,
            entree["frequence"],
            ", ".join(entree["profils_ids"]) or "—",
            ", ".join(entree["groupe_ids"]) or "—",
            ", ".join(entree["gouvernement_ids"]) or "—",
        ]
        for type_warning, entree in vue["warnings"]["par_type"].items()
    ]

    lignes_erreurs = (
        [["profil", e["fichier"], e["erreur"]] for e in vue["erreurs_lecture"]["profils"]]
        + [["groupe", e["fichier"], e["erreur"]] for e in vue["erreurs_lecture"]["groupes"]]
        + [["gouvernement", e["fichier"], e["erreur"]] for e in vue["erreurs_lecture"]["gouvernements"]]
    )

    return (
        "## Vue d'ensemble\n\n"
        + _md_table(["Indicateur", "Valeur"], lignes_totaux, "Aucune donnée.")
        + "\n### Warnings agrégés (profils + groupes + gouvernements)\n\n"
        + _md_table(
            ["Type", "Fréquence", "Profils concernés", "Groupes concernés", "Gouvernements concernés"],
            lignes_warnings, "Aucun warning.",
        )
        + "\n### Erreurs de lecture agrégées\n\n"
        + _md_table(["Domaine", "Fichier", "Erreur"], lignes_erreurs, "Aucune erreur de lecture.")
    )


def _md_section_rattachements(audit: dict[str, Any]) -> str:
    """Les jointures reconstruites, chacune avec SA population.

    Le taux n'est jamais publié seul : le même rattachement vaut 4 % ou 61 %
    selon le dénominateur, et un taux sans sa population est une erreur, pas une
    approximation (AGENTS.md §9 ; §2 règle 7 pour le couple numérateur/
    dénominateur).
    """
    lignes = [
        [
            j["quoi"],
            j["population"],
            f"{j['resolus']} / {j['total']}",
            "—" if j["taux"] is None else f"{j['taux']} %",
            j["note"] or "",
        ]
        for j in audit.get("jointures") or []
    ]
    corps = _md_table(
        ["Rattachement", "Population", "Résolus", "Taux", "Note"],
        lignes,
        "_Aucune jointure mesurée._",
    )
    absents = audit.get("fichiers_absents") or []
    manque = (
        "\n**Fichiers absents, donc jointures non mesurées :** "
        + ", ".join(f"`{f}`" for f in absents)
        + "\n"
        if absents
        else ""
    )
    return (
        "## Rattachements reconstruits\n\n"
        "Aucun de ces liens n'est donné par la source : le dépôt les établit, "
        "et un taux qui décroche d'un run à l'autre est le signal. "
        "**Cette section ne bloque jamais** — un taux bas y est le plus souvent "
        "le silence de la source, pas une faute. Les références orphelines, "
        "elles, sont un bug et vivent dans `audit_integrite_referentielle`.\n\n"
        + corps
        + manque
    )


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    """Génère un rapport Markdown lisible par un humain à partir du dict `build_report`.

    Vue d'ensemble d'abord, puis les trois rapports détaillés tels que
    générés par `audit_pivot_dataset.generate_markdown_report`,
    `audit_groupe_dataset.generate_markdown_report` et
    `audit_gouvernement_dataset.generate_markdown_report` (aucune donnée
    recalculée). Outil de qualité interne : aucun score ni classement
    (AGENTS.md §2.1).
    """
    meta = rapport["meta"]

    entete = (
        "# Rapport d'audit pipeline (profils + groupes + gouvernements)\n\n"
        f"Généré le {meta['genere_le']}. Seuil de péremption des sources : "
        f"{meta['staleness_days']} jour(s).\n\n"
        "Outil manuel de qualité interne, distinct de `check_quality_gate.py` "
        "(seul gate bloquant en CI) : usage manuel uniquement, jamais appelé "
        "par la CI. Compile les rapports `audit_pivot_dataset.py`, "
        "`audit_groupe_dataset.py` et `audit_gouvernement_dataset.py` sans "
        "nouvelle logique de calcul métier, ni score ni classement.\n"
    )

    return "\n".join([
        entete,
        _md_section_vue_ensemble(rapport["vue_ensemble"]),
        _md_section_rattachements(rapport.get("audit_rattachements") or {}),
        "---\n\n" + audit_pivot_dataset.generate_markdown_report(rapport["audit_profils"]),
        "---\n\n" + audit_groupe_dataset.generate_markdown_report(rapport["audit_groupes"]),
        "---\n\n" + audit_gouvernement_dataset.generate_markdown_report(rapport["audit_gouvernements"]),
    ])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit_pipeline.py",
        description=(
            "Exécute les audits profils (audit_pivot_dataset.py), groupes "
            "(audit_groupe_dataset.py) et gouvernements "
            "(audit_gouvernement_dataset.py) et compile une vue d'ensemble. "
            "Outil manuel de qualité interne — usage manuel uniquement, "
            "jamais appelé par la CI. Ne produit aucun score ni classement."
        ),
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Dossier des fichiers *.pivot.json à auditer (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--groupes-dir",
        default="pivot_data/groupes",
        metavar="DOSSIER",
        help="Dossier des fichiers *.json de groupe à auditer (défaut : pivot_data/groupes).",
    )
    parser.add_argument(
        "--scrutins",
        default="pivot_data/scrutins.json",
        metavar="FICHIER",
        help=(
            "Index partagé des scrutins (#432), d'où l'audit des groupes tire la "
            "date de chaque scrutin de cohésion (défaut : pivot_data/scrutins.json). "
            "Absent ou vide : les plages temporelles sont vides et le rapport le "
            "DÉCLARE (#726)."
        ),
    )
    parser.add_argument(
        "--gouvernements-dir",
        default="pivot_data/gouvernements",
        metavar="DOSSIER",
        help=(
            "Dossier des fichiers gouvernement-*.json à auditer "
            "(défaut : pivot_data/gouvernements)."
        ),
    )
    parser.add_argument(
        "--output-json",
        default=None,
        metavar="FICHIER",
        help="Chemin du rapport JSON combiné (défaut : affiché sur stdout).",
    )
    parser.add_argument(
        "--output-md",
        default=None,
        metavar="FICHIER",
        help="Chemin du rapport Markdown combiné (défaut : non généré).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DOSSIER",
        help=(
            "Écrit JSON et Markdown sous ce dossier avec un nom horodaté "
            "(audit_pipeline_<horodatage-UTC>.json/.md) au lieu de nommer "
            "chaque fichier — incompatible avec --output-json/--output-md."
        ),
    )
    parser.add_argument(
        "--staleness-days",
        type=int,
        default=30,
        metavar="JOURS",
        help=(
            "Seuil d'ancienneté (jours) au-delà duquel un profil/groupe/"
            "gouvernement est périmé, répercuté vers les trois audits "
            "sous-jacents (défaut : 30)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.output_dir and (args.output_json or args.output_md):
        print(
            "[!] --output-dir est incompatible avec --output-json/--output-md.",
            file=sys.stderr,
        )
        return 1

    output_json_path = args.output_json
    output_md_path = args.output_md
    if args.output_dir:
        horodatage = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_json_path = str(Path(args.output_dir) / f"audit_pipeline_{horodatage}.json")
        output_md_path = str(Path(args.output_dir) / f"audit_pipeline_{horodatage}.md")

    profiles_dir = Path(args.profiles_dir)
    groupes_dir = Path(args.groupes_dir)
    gouvernements_dir = Path(args.gouvernements_dir)

    if not profiles_dir.is_dir():
        print(f"[!] Dossier profils introuvable : {profiles_dir}", file=sys.stderr)
        return 1
    if not groupes_dir.is_dir():
        print(f"[!] Dossier groupes introuvable : {groupes_dir}", file=sys.stderr)
        return 1
    if not gouvernements_dir.is_dir():
        print(f"[!] Dossier gouvernements introuvable : {gouvernements_dir}", file=sys.stderr)
        return 1

    reference = datetime.now(timezone.utc)

    profils, erreurs_profils = audit_pivot_dataset.load_pivot_directory(profiles_dir)
    rapport_profils = audit_pivot_dataset.build_report(
        profils, erreurs_profils, staleness_days=args.staleness_days, reference_date=reference,
    )
    print(
        f"→ profils : {len(profils)} chargé(s), {len(erreurs_profils)} erreur(s) de lecture.",
        file=sys.stderr,
    )

    groupes, erreurs_groupes = audit_groupe_dataset.load_groupe_directory(groupes_dir)
    index_scrutins = (
        audit_groupe_dataset.charger_scrutins(Path(args.scrutins)) if args.scrutins else None
    )
    if args.scrutins and not len(index_scrutins or ()):
        print(
            f"[!] Index des scrutins vide ou introuvable ({args.scrutins}) : les plages "
            "temporelles par groupe seront vides, et le rapport le déclare (#726).",
            file=sys.stderr,
        )
    rapport_groupes = audit_groupe_dataset.build_report(
        groupes, erreurs_groupes, staleness_days=args.staleness_days, reference_date=reference,
        scrutins_index=index_scrutins,
    )
    print(
        f"→ groupes : {len(groupes)} chargé(s), {len(erreurs_groupes)} erreur(s) de lecture.",
        file=sys.stderr,
    )

    gouvernements, erreurs_gouvernements = audit_gouvernement_dataset.load_gouvernement_directory(
        gouvernements_dir
    )
    rapport_gouvernements = audit_gouvernement_dataset.build_report(
        gouvernements, erreurs_gouvernements,
        staleness_days=args.staleness_days, reference_date=reference,
    )
    print(
        f"→ gouvernements : {len(gouvernements)} chargé(s), "
        f"{len(erreurs_gouvernements)} erreur(s) de lecture.",
        file=sys.stderr,
    )

    # Les rattachements sont mesurés ICI, dans le CLI, et passés à
    # `build_report` : lui les calculer le ferait lire le corpus vivant depuis
    # les tests (AGENTS.md §3b).
    rapport = build_report(
        rapport_profils,
        rapport_groupes,
        rapport_gouvernements,
        # Le dossier pivot est DÉRIVÉ de l'option existante : l'audit lit
        # `pivot_data/`, et un CLI pointé sur des fixtures doit lire les
        # fixtures — jamais le corpus vivant (§3b).
        audit_rattachements.audit_rattachements(profiles_dir.parent),
    )
    output_json = json.dumps(rapport, ensure_ascii=False, indent=2)

    if output_json_path:
        out_path = Path(output_json_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")
        print(f"  ✓ Rapport JSON écrit : {out_path}", file=sys.stderr)
    else:
        print(output_json)

    if output_md_path:
        md_path = Path(output_md_path)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(generate_markdown_report(rapport), encoding="utf-8")
        print(f"  ✓ Rapport Markdown écrit : {md_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
