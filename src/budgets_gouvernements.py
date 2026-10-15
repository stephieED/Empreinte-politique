#!/usr/bin/env python3
"""Les budgets que chaque gouvernement a fait voter (`pivot_data/budgets_gouvernements.json`, #1053).

La fiche de gouvernement montre deux choses : ce que l'État reçoit et dépense,
et ce que les caisses de sécurité sociale reçoivent et versent. Ce module les
compose, gouvernement par gouvernement, à partir de ce que deux collectes ont
déjà écrit — `raw_data/finances_etat.json` et `raw_data/finances_sociales.json`.
Il ne lit aucun réseau.

## La règle de période

**Une année revient au gouvernement sous lequel sa loi de finances initiale a
été promulguée** (arbitré le 13/10/2026). La date est celle de
`pivot_data/textes_promulgues.json`. Rien n'est réparti entre gouvernements, et
aucune année ne figure sur deux fiches : un budget voté sous un gouvernement et
exécuté sous un autre reste sur la fiche du premier.

La sécurité sociale suit la même année **par analogie** : son budget est voté
par une autre loi, celle du financement de la Sécurité sociale, dont les dates
ne sont pas lues ici.

## Ce qui est publié, et ce qui ne l'est pas

Les montants sont **ceux réellement encaissés et dépensés**, tels que la source
les donne ; aucun montant voté n'est repris (arbitré le 13/10/2026). Une partie
que la source ne donne pas pour une année est `null`, à côté de son
`*_non_resolu` (§2 règle 5) — les missions avant 2023, les caisses avant 2020 ou
après la dernière année publiée.

Usage :

    python3 src/budgets_gouvernements.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from licences import LICENCE_FINANCES_ETAT, LICENCE_FINANCES_SOCIALES  # noqa: E402

CHEMIN_PAR_DEFAUT = Path("pivot_data") / "budgets_gouvernements.json"
SCHEMA_VERSION = "budgets-gouvernements-v1"

#: Le titre d'une loi de finances initiale, sous les trois formes que le
#: fichier des textes promulgués lui donne selon la législature.
_LFI = re.compile(r"loi de finances (?:pour )?(\d{4})\s*$", re.IGNORECASE)

#: Les lignes du jeu mensuel de la DGFiP reprises, par leur libellé exact.
RECETTES = (
    "Impôt sur le revenu", "Impôt sur les sociétés", "Taxe sur la valeur ajoutée",
    "Taxe intérieure de consommation sur les produits énergétiques",
    "Autres recettes fiscales", "Total recettes non fiscales",
    "Fonds de concours et attribution de produits",
)
TOTAL_RECETTES = "Total recettes nettes du budget général"
TOTAL_DEPENSES = "Total dépenses nettes du budget général"
REVERSE = ("PSR au profit des collectivités territoriales", "PSR au profit de l'Union européenne")
COMPTES_A_PART = ("Solde des comptes spéciaux", "Solde des Budgets annexes")
SOLDE = "Solde budgétaire"
#: Comptés dans les dépenses nettes du budget général, mais dans aucune des
#: missions gardées : c'est ce qui sépare les deux fichiers (5,1 Md€ en 2023).
DEGREVEMENTS_LOCAUX = "Remboursements et dégrèvements d'impôts locaux"
MISSION_ECARTEE = "Remboursements et dégrèvements"

#: Les caisses : le bloc des administrations de sécurité sociale, ses deux
#: secteurs dans les prestations par régime.
CHAMP_CAISSES = "administrations_de_securite_sociale"
SECTEURS_CAISSES = ("S13141", "S13142")
TOTAL_RESSOURCES = "TOTAL DES RESSOURCES HORS TRANSFERTS"
TOTAL_EMPLOIS = "TOTAL DES EMPLOIS HORS TRANSFERTS"


def exercices_votes(textes: dict[str, Any]) -> dict[str, str]:
    """Exercice → date de promulgation de sa loi de finances initiale."""
    dates: dict[str, str] = {}
    for texte in (textes.get("textes") or {}).values():
        if not isinstance(texte, dict):
            continue
        titre = texte.get("titre") or ""
        trouve = _LFI.search(titre)
        if not trouve or "rectificative" in titre.lower() or not texte.get("date_promulgation"):
            continue
        an = trouve.group(1)
        if an in dates and dates[an] != texte["date_promulgation"]:
            raise ValueError(f"deux lois de finances initiales pour {an}")
        dates[an] = texte["date_promulgation"]
    return dict(sorted(dates.items()))


def budget_de_l_etat(finances: dict[str, Any], an: str) -> Optional[dict[str, Any]]:
    """Les recettes, les dépenses et le solde d'un exercice, au dernier mois publié."""
    lignes = {l["ligne"]: l["mensuel"] for l in (finances.get("grandes_lignes") or {}).get("lignes") or []}
    mois = sorted(m for m in lignes.get(TOTAL_DEPENSES, {}) if m.startswith(an + "-"))
    if not mois:
        return None
    dernier = mois[-1]

    def valeur(nom: str) -> float:
        return lignes[nom][dernier]

    bloc: dict[str, Any] = {
        "dernier_mois": dernier,
        "exercice_complet": dernier.endswith("-12"),
        "recettes": [{"ligne": nom, "montant": valeur(nom)} for nom in RECETTES],
        "recettes_nettes": valeur(TOTAL_RECETTES),
        "depenses_nettes": valeur(TOTAL_DEPENSES),
        "reverse": [{"ligne": nom, "montant": valeur(nom)} for nom in REVERSE],
        "comptes_a_part": sum(valeur(nom) for nom in COMPTES_A_PART),
        "solde": valeur(SOLDE),
    }
    programmes = (((finances.get("exercices") or {}).get(an) or {}).get("realise") or {}).get("programmes")
    if bloc["exercice_complet"] and programmes and all("mission" in p for p in programmes):
        par_mission: dict[str, list[dict[str, Any]]] = {}
        for p in programmes:
            par_mission.setdefault(p["mission"], []).append(
                {"programme": p["programme"], "libelle": p.get("libelle_programme"),
                 "montant": p["cp"]})
        par_mission.pop(MISSION_ECARTEE, None)
        # Le montant de la mission est la somme de ses programmes, ceux-là
        # mêmes qui sont publiés sous elle : l'interface les additionne et doit
        # retomber dessus. Un nom de programme que la source ne donne pas est
        # `null`, jamais déduit du numéro (§2 règle 5).
        bloc["missions"] = [
            {"mission": m, "montant": round(sum(p["montant"] for p in progs), 2),
             "programmes": progs}
            for m, progs in sorted(par_mission.items())]
        bloc["degrevements_d_impots_locaux"] = valeur(DEGREVEMENTS_LOCAUX)
    else:
        bloc["missions"] = None
        bloc["missions_non_resolu"] = {
            "raison": "la source ne publie les dépenses par mission, en données, que pour "
                      "les exercices clos de 2023 à 2025"}
    return bloc


def securite_sociale(sociales: dict[str, Any], an: str) -> Optional[dict[str, Any]]:
    """Ce que les caisses reçoivent, par origine, et ce que chaque régime verse."""
    champ = (((sociales.get("protection_sociale") or {}).get("champs") or {}).get(CHAMP_CAISSES) or {})
    lignes = champ.get("lignes") or []
    libelles = [l["libelle"] for l in lignes]
    regimes = ((sociales.get("prestations_par_regime") or {}).get("annees") or {}).get(an)
    if TOTAL_RESSOURCES not in libelles or an not in (champ.get("statuts") or {}) or not regimes:
        return None
    rang = libelles.index(TOTAL_RESSOURCES)
    prestations = [{"regime": r["regime"], "montant": r["montant"]} for r in regimes
                   if r["niveau"] == 2 and r["secteur_code"] in SECTEURS_CAISSES and r["montant"]]
    verse = sum(p["montant"] for p in prestations)
    recu = lignes[rang]["valeurs"][an]
    emplois = lignes[libelles.index(TOTAL_EMPLOIS)]["valeurs"][an]
    return {
        "statut": champ["statuts"][an],
        "ressources": [{"origine": l["libelle"], "montant": l["valeurs"][an]}
                       for l in lignes[rang + 1:] if l["valeurs"].get(an) is not None],
        "ressources_total": recu,
        "prestations": sorted(prestations, key=lambda p: p["regime"]),
        "autres_emplois": round(emplois - verse, 2),
        "emplois_total": emplois,
    }


def composer(gouvernements: dict[str, Any], textes: dict[str, Any],
             finances: dict[str, Any], sociales: dict[str, Any]) -> dict[str, Any]:
    """Le document : une entrée par gouvernement, vide s'il n'a fait voter aucun budget."""
    dates = exercices_votes(textes)
    sortie: dict[str, Any] = {}
    for gouv in gouvernements.get("gouvernements") or []:
        debut, fin = gouv["periode"]["debut"], gouv["periode"].get("fin") or "9999-12-31"
        exercices = []
        for an, date in dates.items():
            if not debut <= date <= fin:
                continue
            etat, caisses = budget_de_l_etat(finances, an), securite_sociale(sociales, an)
            entree: dict[str, Any] = {"exercice": an, "loi_de_finances_promulguee_le": date,
                                      "budget_de_l_etat": etat, "securite_sociale": caisses}
            if etat is None:
                entree["budget_de_l_etat_non_resolu"] = {
                    "raison": "la source ne publie les recettes et les dépenses mois par mois "
                              "que depuis janvier 2013"}
            if caisses is None:
                entree["securite_sociale_non_resolu"] = {
                    "raison": "la source ne détaille pas les ressources des administrations de "
                              "sécurité sociale pour cette année"}
            exercices.append(entree)
        sortie[gouv["gouvernement_id"]] = {"exercices": exercices}
    return {
        "schema_version": SCHEMA_VERSION,
        "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "licence_donnees": f"{LICENCE_FINANCES_ETAT} ; {LICENCE_FINANCES_SOCIALES}",
        "unites": {"budget_de_l_etat": "euros", "securite_sociale": "millions d'euros"},
        "gouvernements": sortie,
    }


def _lire(chemin: Path) -> dict[str, Any]:
    try:
        return json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def main(argv: Optional[list[str]] = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analyseur.add_argument("--sortie", type=Path, default=CHEMIN_PAR_DEFAUT)
    analyseur.add_argument("--racine", type=Path, default=Path("."))
    args = analyseur.parse_args(argv)

    from json_io import dumps_indente, ecrire_index_json

    racine = args.racine
    document = composer(_lire(racine / "raw_data" / "gouvernements_reels.json"),
                        _lire(racine / "pivot_data" / "textes_promulgues.json"),
                        _lire(racine / "raw_data" / "finances_etat.json"),
                        _lire(racine / "raw_data" / "finances_sociales.json"))
    ecrit = ecrire_index_json(args.sortie, document, dumps_indente)
    for ident, bloc in document["gouvernements"].items():
        if bloc["exercices"]:
            print(f"{ident} : " + ", ".join(
                e["exercice"] + ("" if e["budget_de_l_etat"] else " (sans budget)")
                + ("" if e["securite_sociale"] else " (sans caisses)") for e in bloc["exercices"]))
    print(f"{args.sortie} : {'écrit' if ecrit else 'inchangé'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
