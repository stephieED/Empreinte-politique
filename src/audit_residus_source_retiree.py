#!/usr/bin/env python3
"""
audit_residus_source_retiree.py — Ce que chaque profil devrait encore à la
source retirée **après** le nettoyage, et pourquoi (#839, lot C).

Pourquoi ce lot existe
----------------------
Les lots A et B ont compté le sédiment et jugé les mandats. Restent les résidus
qui ne sont **pas** des données : le marqueur `sources[]`, les avertissements
publiés d'avant, les preuves de couverture qui citent la source. Ils ne se
nettoient pas comme une liste : chacun a un destinataire ou un effet juridique.

La question que ce script rend décidable est celle que §7 pose déjà :
**`meta.licence_donnees` est un champ dérivé dont la condition de retrait
« court d'elle-même »** — le jour où un profil cesse de porter quoi que ce soit
de Regards Citoyens, la clause ODbL le quitte. Encore faut-il savoir, profil par
profil, **ce qui la retient** : une donnée publiée, ou le seul marqueur.

Ce que le script fait, et ne fait pas
-------------------------------------
Il **simule** le retrait des interventions héritées — celui de
`purge_interventions_heritees.py`, appliqué en mémoire, sur une copie — puis
recompose la licence due avec `licences.licences_du_profil()`, la fonction de
production. Rien n'est écrit, aucun profil n'est modifié.

Il ne décide pas du retrait du marqueur : **c'est une décision éditoriale à
effet juridique**, et elle reste à la propriétaire (§7, `docs/decisions/licence-lot-6-530.md`).

Les trois familles qu'il éclaire
--------------------------------
1. **Le marqueur `sources[]`** — ce qui retient la clause. Trois états par
   profil : retenue par une donnée encore publiée, retenue par le seul
   marqueur, ou plus due du tout.
2. **Les entrées sans date** — les intitulés de navigation de l'ancien site,
   publiés comme des organes. Le script vérifie ce qui en fait des non-faits :
   aucune date, aucun `source_url`, et `actif` à `true` sur un profil dont le
   mandat est terminé.
3. **Les avertissements hérités et les preuves de couverture** — du texte
   publié, adressé à un lecteur (#642). Ils sont comptés et donnés à lire,
   jamais proposés au retrait par un compte.

Usage (depuis la racine du dépôt) :
    python3 src/audit_residus_source_retiree.py
    python3 src/audit_residus_source_retiree.py --par-profil
    python3 src/audit_residus_source_retiree.py --retirer-orphelines   # hypothèse : les 19 partent aussi
    python3 src/audit_residus_source_retiree.py --json residus.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from audit_sediment import (
    avertissements_herites,
    interventions_a_identifiant_entier,
    mandats_actifs_sans_dates,
    mandats_sans_categorie_source,
    preuves_de_couverture_citant_la_source,
    sources_retirees,
)
from licences import LICENCE_REGARDS_CITOYENS, licences_du_profil
from population_profils import provenance_du_profil, ventiler_provenances
from purge_interventions_heritees import purge_profil

PIVOT_PAR_DEFAUT = Path("pivot_data") / "profiles"
SUFFIXE_PIVOT = ".pivot.json"

RETENUE_PAR_UNE_DONNEE = "retenue_par_une_donnee"
RETENUE_PAR_LE_MARQUEUR = "retenue_par_le_marqueur_seul"
PLUS_DUE = "plus_due"

ORDRE_ETATS = (RETENUE_PAR_UNE_DONNEE, RETENUE_PAR_LE_MARQUEUR, PLUS_DUE)
LIBELLES_ETATS = {
    RETENUE_PAR_UNE_DONNEE: "clause retenue par une donnée encore publiée",
    RETENUE_PAR_LE_MARQUEUR: "clause retenue par le seul marqueur `sources[]`",
    PLUS_DUE: "clause plus due (aucun marqueur, aucune donnée)",
}


def _sans_marqueur(profil: dict[str, Any]) -> dict[str, Any]:
    """Le même profil, marqueur de source retiré. Sert à distinguer « une
    donnée retient la clause » de « le marqueur la retient »."""
    # Copie de **surface** : `purge_profil` et cette fonction ne remplacent que
    # des listes, jamais une entrée. Un `deepcopy` recopiait jusqu'à 8 Mio par
    # profil, 1 180 fois — l'audit ne rendait pas la main.
    copie = dict(profil)
    retires = {id(s) for s in sources_retirees(copie)}
    copie["sources"] = [s for s in (copie.get("sources") or []) if id(s) not in retires]
    return copie


def etat_de_la_clause(profil: dict[str, Any], *, retirer_orphelines: bool = False) -> str:
    """L'état de la clause ODbL de ce profil **après** nettoyage simulé.

    `retirer_orphelines` pose l'hypothèse haute : les interventions héritées
    sans jumelle Syceron partent aussi. Sans elle, seules les jumelées partent —
    c'est le périmètre décidé du lot D.
    """
    nettoye, _ = purge_profil(dict(profil))
    if retirer_orphelines:
        restantes = {id(e) for e in interventions_a_identifiant_entier(nettoye)}
        nettoye["interventions"] = [
            e for e in (nettoye.get("interventions") or []) if id(e) not in restantes
        ]

    if LICENCE_REGARDS_CITOYENS in licences_du_profil(_sans_marqueur(nettoye)):
        return RETENUE_PAR_UNE_DONNEE
    if LICENCE_REGARDS_CITOYENS in licences_du_profil(nettoye):
        return RETENUE_PAR_LE_MARQUEUR
    return PLUS_DUE


def residus_du_profil(profil: dict[str, Any], *, retirer_orphelines: bool = False) -> dict[str, Any]:
    """Ce qui reste, famille par famille, après le nettoyage simulé."""
    nettoye, retirees = purge_profil(dict(profil))
    return {
        "etat_clause": etat_de_la_clause(profil, retirer_orphelines=retirer_orphelines),
        "interventions_retirees": len(retirees),
        "interventions_orphelines": len(interventions_a_identifiant_entier(nettoye)),
        "mandats_sans_estampille": len(mandats_sans_categorie_source(profil)),
        "mandats_sans_date": len(mandats_actifs_sans_dates(profil)),
        "avertissements_herites": len(avertissements_herites(profil)),
        "preuves_couverture": len(preuves_de_couverture_citant_la_source(profil)),
        "porte_le_marqueur": bool(sources_retirees(profil)),
    }


def verifier_entrees_sans_date(profil: dict[str, Any]) -> list[dict[str, Any]]:
    """Ce qui fait d'une entrée sans date un non-fait, entrée par entrée.

    Trois propriétés, vérifiées et non supposées : aucune date, aucun
    `source_url`, `actif` à `true`. La troisième est celle qui se voit à
    l'écran — la fiche publie une appartenance en cours.
    """
    constats = []
    for mandat in mandats_actifs_sans_dates(profil):
        constats.append({
            "label": mandat.get("label"),
            "categorie": mandat.get("categorie"),
            "sans_date": not mandat.get("debut") and not mandat.get("fin"),
            "sans_source_url": not mandat.get("source_url"),
            "publie_comme_actif": mandat.get("actif") is True,
        })
    return constats


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pivot-dir", default=str(PIVOT_PAR_DEFAUT), metavar="DOSSIER")
    parser.add_argument("--retirer-orphelines", action="store_true",
                        help="Pose l'hypothèse que les interventions héritées sans jumelle partent aussi.")
    parser.add_argument("--par-profil", action="store_true", help="Le détail, profil par profil.")
    parser.add_argument("--json", metavar="FICHIER")
    args = parser.parse_args(argv)

    pivot_dir = Path(args.pivot_dir)
    if not pivot_dir.is_dir():
        print(f"[!] Répertoire introuvable : {pivot_dir}", file=sys.stderr)
        return 2

    etats: Counter[str] = Counter()
    provenances: dict[str, list[str]] = {etat: [] for etat in ORDRE_ETATS}
    rapport: dict[str, Any] = {"profils": {}, "entrees_sans_date": []}
    totaux: Counter[str] = Counter()

    for chemin in sorted(pivot_dir.glob("*" + SUFFIXE_PIVOT)):
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(profil, dict):
            continue
        if not sources_retirees(profil) and not interventions_a_identifiant_entier(profil) \
                and not mandats_sans_categorie_source(profil) \
                and not avertissements_herites(profil) \
                and not preuves_de_couverture_citant_la_source(profil):
            continue  # aucun lien avec la source retirée : rien à simuler
        residus = residus_du_profil(profil, retirer_orphelines=args.retirer_orphelines)
        if residus["etat_clause"] == PLUS_DUE and not residus["porte_le_marqueur"]:
            continue  # profil sans aucun lien, ni donnée ni marqueur

        slug = chemin.name[: -len(SUFFIXE_PIVOT)]
        etats[residus["etat_clause"]] += 1
        provenances[residus["etat_clause"]].append(provenance_du_profil(profil))
        for cle in ("interventions_retirees", "interventions_orphelines", "mandats_sans_estampille",
                    "mandats_sans_date", "avertissements_herites", "preuves_couverture"):
            totaux[cle] += residus[cle]
        rapport["profils"][slug] = residus
        for constat in verifier_entrees_sans_date(profil):
            rapport["entrees_sans_date"].append({"slug": slug, **constat})

    hypothese = "les 19 sans jumelle partent aussi" if args.retirer_orphelines else \
                "seules les interventions jumelées partent"
    print("## Ce que les profils devraient encore à la source retirée, après nettoyage\n")
    print(f"Hypothèse : **{hypothese}**.\n")
    print("| État de la clause ODbL | Profils |")
    print("| --- | --- |")
    for etat in ORDRE_ETATS:
        if etats[etat]:
            print(f"| {LIBELLES_ETATS[etat]} | {ventiler_provenances(provenances[etat]).cellule_markdown()} |")

    print("\n| Ce qui reste | Entrées |")
    print("| --- | ---: |")
    print(f"| interventions retirées par la purge | {totaux['interventions_retirees']} |")
    print(f"| interventions héritées restantes (sans jumelle) | {totaux['interventions_orphelines']} |")
    print(f"| mandats sans `categorie_source` (hors périmètre, #718) | {totaux['mandats_sans_estampille']} |")
    print(f"| mandats publiés actifs et sans aucune date | {totaux['mandats_sans_date']} |")
    print(f"| avertissements hérités, adressés à un lecteur (#642) | {totaux['avertissements_herites']} |")
    print(f"| preuves de couverture citant la source | {totaux['preuves_couverture']} |")

    sans_date = rapport["entrees_sans_date"]
    if sans_date:
        non_faits = [c for c in sans_date if c["sans_date"] and c["sans_source_url"]]
        actifs = [c for c in non_faits if c["publie_comme_actif"]]
        print(f"\n### Les {len(sans_date)} entrées sans date\n")
        print(f"**{len(non_faits)}** n'ont ni date ni `source_url`, et **{len(actifs)}** sont publiées "
              f"comme des appartenances **en cours**.\n")
        print("| Profil | Catégorie | Libellé |")
        print("| --- | --- | --- |")
        for constat in sans_date:
            print(f"| `{constat['slug']}` | {constat['categorie']} | {constat['label']} |")

    print("\nAucun profil n'a été modifié : le nettoyage est simulé, et le retrait du marqueur "
          "reste une décision éditoriale à effet juridique (§7).")

    if args.json:
        rapport["etats"] = dict(etats)
        rapport["totaux"] = dict(totaux)
        Path(args.json).write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"→ Rapport JSON : {args.json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
