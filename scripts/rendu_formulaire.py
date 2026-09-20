#!/usr/bin/env python3
"""Rend le formulaire `workflow_dispatch` de generate-data.yml tel que GitHub
l'affiche, à sa largeur de coupe réelle.

POURQUOI CE SCRIPT EXISTE
    Les descriptions d'inputs sont les LIBELLÉS du formulaire : GitHub montre
    la description et cache le nom du champ. Lire le YAML donne donc une image
    fausse — une description de trente mots y tient sur une ligne, alors que le
    formulaire la coupe en cinq lignes dans une colonne étroite, au moment
    précis où l'on configure un run.

    Le défaut a été introduit deux fois avant que ce script existe, et découvert
    les deux fois par capture d'écran. La règle qui le prévient est simple :
    UN LIBELLÉ EST UN TITRE, PAS DE LA DOCUMENTATION. Elle est verrouillée par
    `test_un_libelle_tient_sur_une_ligne`, et se VOIT ici.

LARGEUR
    65 colonnes, relevée sur le rendu réel de GitHub le 29/08/2026. Ce n'est pas
    une préférence : c'est la mesure.

USAGE
    python3 scripts/rendu_formulaire.py
"""
from __future__ import annotations

import pathlib
import re
import sys
import textwrap

LARGEUR = 65

RACINE = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = RACINE / ".github" / "workflows" / "generate-data.yml"


def _inputs(chemin: pathlib.Path) -> dict:
    """Rend les inputs de workflow_dispatch, dans l'ordre du fichier.

    Analyse par expression régulière et NON par PyYAML : cet outil doit
    tourner sur une machine nue, et la suite de tests du dépôt s'en sert. Une
    dépendance de plus pour afficher dix libellés, ce serait la garantie qu'on
    ne l'exécute pas.
    """
    contenu = chemin.read_text(encoding="utf-8")
    bloc = contenu[contenu.index("  workflow_dispatch:"):contenu.index("\npermissions:")]

    inputs: dict[str, dict] = {}
    courant: str | None = None
    dans_options = False
    for ligne in bloc.splitlines():
        nu = ligne.strip()
        if nu.startswith("#") or not nu:
            continue

        entete = re.fullmatch(r"([a-z_]+):", nu)
        if entete and ligne.startswith("      ") and not ligne.startswith("       "):
            courant = entete.group(1)
            inputs[courant] = {}
            dans_options = False
            continue
        if courant is None:
            continue

        if nu == "options:":
            dans_options = True
            inputs[courant]["options"] = []
            continue
        if dans_options and nu.startswith("- "):
            inputs[courant]["options"].append(nu[2:].strip())
            continue
        dans_options = False

        cle, _, valeur = nu.partition(":")
        valeur = valeur.strip()
        if cle == "description":
            inputs[courant]["description"] = valeur.strip('"')
        elif cle == "type":
            inputs[courant]["type"] = valeur
        elif cle == "default":
            inputs[courant]["default"] = {"true": True, "false": False}.get(valeur, valeur)
    return inputs


def rendre(inputs: dict, largeur: int = LARGEUR) -> tuple[str, int]:
    lignes_totales = 0
    sortie: list[str] = []
    for nom, champ in inputs.items():
        desc = str(champ.get("description", ""))
        enveloppe = textwrap.wrap(desc, largeur) or [""]
        lignes_totales += len(enveloppe)

        if champ.get("type") == "choice":
            controle = "[ " + "  ▾ ".join(str(o) for o in champ["options"]) + " ]"
        elif champ.get("type") == "boolean":
            coche = "x" if champ.get("default") is True else " "
            controle = f"[{coche}] {nom}"
        else:
            controle = f"[ {champ.get('default', '')} ]"

        sortie.append("┌" + "─" * largeur + "┐")
        for ligne in enveloppe:
            sortie.append("│" + ligne.ljust(largeur) + "│")
        sortie.append("│" + controle.ljust(largeur) + "│")
        sortie.append("└" + "─" * largeur + "┘")
    return "\n".join(sortie), lignes_totales


def main() -> int:
    inputs = _inputs(WORKFLOW)
    rendu, lignes = rendre(inputs)
    print(rendu)
    print()
    print(f"{lignes} ligne(s) de libellé pour {len(inputs)} champ(s), coupe à {LARGEUR} colonnes.")
    trop_longs = [n for n, c in inputs.items()
                  if len(textwrap.wrap(str(c.get("description", "")), LARGEUR)) > 1]
    if trop_longs:
        print()
        print("Ces libellés débordent sur plusieurs lignes — ce sont des phrases,")
        print("il faut des titres : " + ", ".join(trop_longs))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
