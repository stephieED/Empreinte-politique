#!/usr/bin/env python3
"""
paroles_d_une_autre_personne.py — le retrait nommé de #1177 : les prises de
parole que l'Assemblée rattache à un député alors que leur libellé nomme une
autre personne.

## Pourquoi un retrait, en plus de la règle de collecte

`candidate_profile.libelle_designe_une_autre_personne` empêche désormais ces
paroles d'entrer dans l'index des débats. Mais la fusion est additive : celles
qu'un run précédent a publiées resteraient. Ce module en tient la LISTE —
relevée sur les trois archives, `config/paroles_d_une_autre_personne.json` — et
`retirer_paroles_d_une_autre_personne` les retire d'un profil fusionné. La
liste est committée : le job qui fusionne n'a pas les archives sous la main,
et un retrait doit pouvoir se relire.

`main` la régénère depuis des archives Syceron téléchargées.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Optional

RACINE = Path(__file__).resolve().parents[1]
CHEMIN_TABLE = RACINE / "config" / "paroles_d_une_autre_personne.json"


def charger_table(chemin: Optional[Path] = None) -> dict[str, dict[str, Any]]:
    """`id_syceron → {legislature, compte_rendu, libelle, acteur}`. Fichier
    absent ou illisible : table vide — on ne retire rien de ce qu'on n'a pas lu."""
    chemin = Path(chemin) if chemin is not None else CHEMIN_TABLE
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    paroles = document.get("paroles") if isinstance(document, dict) else None
    return paroles if isinstance(paroles, dict) else {}


def retirer_paroles_d_une_autre_personne(
    profil: dict[str, Any], table: dict[str, dict[str, Any]]
) -> int:
    """Retire d'un profil les prises de parole de la table QUI LUI SONT
    attribuées. Rend le nombre retiré.

    Le critère est double : l'`id_syceron` du paragraphe, et l'acteur que la
    table nomme — une parole n'est retirée que de la fiche à laquelle la source
    l'avait rattachée à tort.
    """
    interventions = profil.get("interventions")
    if not table or not isinstance(interventions, list):
        return 0
    acteur = ((profil.get("identifiants") or {}).get("an")) or None
    gardees = []
    for entree in interventions:
        ligne = table.get(str(entree.get("id_syceron"))) if isinstance(entree, dict) else None
        if ligne is not None and acteur is not None and ligne.get("acteur") == acteur:
            continue
        gardees.append(entree)
    retirees = len(interventions) - len(gardees)
    if retirees:
        profil["interventions"] = gardees
    return retirees


def relever(archives: Iterable[tuple[str, Path]], identites: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Parcourt les comptes rendus et relève chaque paragraphe que la règle de
    #1177 refuse, avec l'acteur auquel la source l'attribuait."""
    from candidate_profile import _normaliser_orateur_id_syceron  # noqa: PLC0415
    from parse_syceron import parse_syceron_xml  # noqa: PLC0415

    releve: dict[str, dict[str, Any]] = {}
    for legislature, chemin in archives:
        with zipfile.ZipFile(chemin) as archive:
            for nom in archive.namelist():
                if "compteRendu" not in nom or not nom.endswith(".xml"):
                    continue
                parse = parse_syceron_xml(archive.read(nom), avec_texte=False)
                for paragraphe in parse.get("interventions") or []:
                    sans, _ = _normaliser_orateur_id_syceron(
                        paragraphe.get("orateur_id_source"),
                        paragraphe.get("orateur_id_acteur"),
                        paragraphe.get("orateur_nom"),
                    )
                    avec, motif = _normaliser_orateur_id_syceron(
                        paragraphe.get("orateur_id_source"),
                        paragraphe.get("orateur_id_acteur"),
                        paragraphe.get("orateur_nom"),
                        identites=identites,
                    )
                    if sans is None or motif != "libelle_d_une_autre_personne":
                        continue
                    releve[str(paragraphe.get("id_syceron"))] = {
                        "legislature": legislature,
                        "compte_rendu": paragraphe.get("source_id"),
                        "libelle": (paragraphe.get("orateur_nom") or "").strip(),
                        "acteur": sans,
                    }
    return dict(sorted(releve.items()))


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--archive", action="append", default=[], metavar="LEG=CHEMIN",
                        help="Une archive Syceron par législature, ex. 17=syseron.xml.zip.")
    parser.add_argument("--identites", type=Path, required=True,
                        help="L'index d'identité des acteurs (acteurRef → prénom, nom).")
    parser.add_argument("--out", type=Path, default=CHEMIN_TABLE)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    archives = []
    for valeur in args.archive:
        legislature, _, chemin = valeur.partition("=")
        archives.append((legislature, Path(chemin)))
    identites = json.loads(args.identites.read_text(encoding="utf-8"))
    releve = relever(archives, identites)
    document = {
        "_meta": {
            "description": (
                "Prises de parole que l'Assemblée rattache à un député alors que "
                "leur libellé nomme une autre personne — le plus souvent l'invité "
                "d'un débat (#1177). Retirées des fiches après la fusion ; la "
                "collecte ne les indexe plus."),
            "archives": {leg: str(ch.name) for leg, ch in archives},
            "regle": "candidate_profile.libelle_designe_une_autre_personne",
        },
        "paroles": releve,
    }
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(releve)} prise(s) de parole relevée(s) → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
