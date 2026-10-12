#!/usr/bin/env python3
"""
non_inscrits_amo30.py — La liste des députés non inscrits, avec leurs périodes,
lue dans le référentiel AMO30 de l'Assemblée nationale (#1265).

## Pourquoi

Le dépôt ne publie que des fiches de groupe. Un député qui n'appartient à aucun
groupe à une date donnée n'a donc sa place dans aucune figure : ni part, ni
siège. Mesuré le 08/10/2026 pour l'article « violences sexuelles et sexistes » :
64 amendements ne se rattachaient à aucun groupe à leur date de dépôt, et les
hémicycles comptaient 558 députés au lieu de l'Assemblée entière.

AMO30 publie les non-inscrits comme un organe `GP` de sigle `NI`, un par
législature. Le roster des groupes et la dérivation des lignées l'écartent
volontairement : **les non-inscrits ne sont pas un groupe**. Ce module le lit
pour ce qu'il est — une liste de personnes et de dates.

## Ce n'est pas une fiche de groupe

Rien de ce qu'une fiche de groupe publie ne s'applique à un ensemble qui n'en
est pas un : ni cohésion, ni ratio, ni empreinte thématique (AGENTS §2 règle 7
s'y appliquerait à tort). Le fichier ne porte donc que des appartenances.

## Il n'est pas destiné au site

Arbitré le 12/10/2026 : ces données complètent des articles, elles n'entrent
dans aucune page. Le fichier vit donc dans `raw_data/` et non dans
`pivot_data/`, la seule couche que le site lit — c'est le rangement de
`gouvernements_reels.json`, dérivé de la même archive par le même job.

## Le transit d'ouverture est écarté, et il est compté

`NI` ouvre avec la législature, avant que les groupes se constituent. Tout le
monde y transite entre les deux dates : 577 mandats sur la XVIIe. Un mandat qui
se termine au plus tard le jour de constitution des groupes est un passage
administratif, pas une appartenance — la règle est celle du roster
(`an_roster.est_mandat_de_transit`), et elle n'est pas réécrite ici.

Ce qui est écarté est **compté et daté** dans `transit_d_ouverture` : un trou
muet se lirait comme « personne n'était non inscrit en juillet 2024 ».

## Un passage court reste publié

Hors transit d'ouverture, la plupart des passages durent quelques jours : un
député qui arrive en cours de législature est non inscrit avant de rejoindre
son groupe. Ils sont publiés tels que la source les donne. Un seuil de durée
serait un jugement de notre part, sans fondement dans la source ; c'est au
lecteur du fichier de compter à la date qui l'intéresse.

## Rien n'est écrit sur une lecture en échec (#511)

Archive indisponible, aucun organe `NI`, table de correspondance absente : le
script lève, et le fichier committé reste en place. Une liste vide écrite avec
un code de sortie 0 se lirait comme « aucun non-inscrit ».

Usage :
    python3 src/non_inscrits_amo30.py --out raw_data/non_inscrits.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import an_roster  # noqa: E402
import correspondance_acteurs_an  # noqa: E402
from licences import LICENCE_AN  # noqa: E402

DEFAULT_SORTIE = Path("raw_data/non_inscrits.json")

TYPE_DOCUMENT = "non_inscrits"
SCHEMA_VERSION = 1

#: Première législature publiée. Une **borne déclarée**, pas une limite de la
#: source : AMO30 porte un organe `NI` depuis la XIIe, mais le corpus du dépôt
#: commence avec la XIVe (20/06/2012) et rien n'y rattacherait une liste
#: antérieure.
PREMIERE_LEGISLATURE = 14


class NonInscritsIndisponibles(RuntimeError):
    """La liste est INCONNUE, pas vide : rien ne doit être écrit."""


def organes_non_inscrits(index: dict[str, Any]) -> dict[str, str]:
    """`{législature: organe_ref}` des organes `NI` publiés, par législature.

    Lève si une législature en porte deux : la règle « un organe `NI` par
    législature » est mesurée (XIIe à XVIIe), pas garantie, et deux organes
    fusionnés en silence feraient une liste qui a l'air complète.
    """
    trouves: dict[str, str] = {}
    for ref, organe in index["organes"].items():
        legislature = organe.get("legislature")
        if organe.get("sigle") != an_roster.SIGLE_NON_INSCRIT or not legislature:
            continue
        if int(legislature) < PREMIERE_LEGISLATURE:
            continue
        if legislature in trouves:
            raise NonInscritsIndisponibles(
                f"Deux organes `{an_roster.SIGLE_NON_INSCRIT}` pour la législature "
                f"{legislature} ({trouves[legislature]}, {ref}) : à relire avant de publier."
            )
        trouves[legislature] = ref
    return dict(sorted(trouves.items(), key=lambda item: int(item[0])))


def deriver_legislature(
    index: dict[str, Any],
    legislature: str,
    organe_ref: str,
    slug_par_acteur: dict[str, str],
) -> dict[str, Any]:
    """Le bloc d'une législature : l'organe, le transit écarté, les membres."""
    organe = index["organes"][organe_ref]
    constitution = an_roster.date_constitution_groupes(index, legislature)
    mandats = index["mandats"].get(organe_ref, [])
    transits = [m for m in mandats if an_roster.est_mandat_de_transit(m[2], constitution)]

    membres = [
        {
            # Le slug de la fiche, ou `null` : la table de correspondance n'a
            # pas d'entrée pour cet acteur, donc aucune fiche n'a été
            # collectée. `acteur_ref` reste la clé, toujours présente.
            "membre_id": membre["slug"],
            "acteur_ref": membre["acteur_ref"],
            "nom": membre["nom"],
            "periodes": membre["mandat_periodes"],
        }
        for membre in an_roster.deriver_membres_organes(
            index, [organe_ref], legislature, slug_par_acteur, an_roster.SIGLE_NON_INSCRIT
        )
    ]
    return {
        "legislature": str(legislature),
        "organe_ref": organe_ref,
        "periode": {"debut": organe.get("debut"), "fin": organe.get("fin")},
        "date_constitution_groupes": constitution,
        "transit_d_ouverture": {
            "mandats_ecartes": len(transits),
            "personnes": len({m[0] for m in transits}),
        },
        "membres": membres,
    }


def construire(index: dict[str, Any], slug_par_acteur: dict[str, str]) -> dict[str, Any]:
    """Le document `non_inscrits.json`, entête comprise."""
    organes = organes_non_inscrits(index)
    if not organes:
        raise NonInscritsIndisponibles(
            f"Aucun organe `{an_roster.SIGLE_NON_INSCRIT}` depuis la législature "
            f"{PREMIERE_LEGISLATURE} : archive tronquée ou format changé."
        )
    legislatures = [
        deriver_legislature(index, legislature, organe_ref, slug_par_acteur)
        for legislature, organe_ref in organes.items()
    ]
    if not any(bloc["membres"] for bloc in legislatures):
        raise NonInscritsIndisponibles(
            "Les organes `NI` existent mais aucun mandat n'en sort : les mandats "
            "de l'archive n'ont pas été lus."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "type_document": TYPE_DOCUMENT,
        "meta": {
            "description": (
                "Produit à chaque run par src/non_inscrits_amo30.py (#1265) : les "
                "députés de l'Assemblée nationale qui n'appartiennent à aucun groupe, par législature, avec "
                "leurs périodes. Lu dans l'organe « Non inscrit » du référentiel "
                "AMO30 de l'Assemblée nationale. Ce n'est pas une fiche de groupe : "
                "les non-inscrits ne sont pas un groupe. Ne pas éditer à la main : "
                "le prochain run réécrit ce fichier."
            ),
            "avertissements": [
                "Une période ouverte (`fin` : null) l'était dans l'archive lue par "
                "le run qui a produit ce fichier.",
                "Le transit d'ouverture est écarté : en début de législature, tous "
                "les députés passent par cet organe avant que les groupes se "
                "constituent. `transit_d_ouverture` compte ce qui est écarté ; "
                "avant `date_constitution_groupes`, la liste ne dit donc pas qui "
                "était non inscrit.",
                "Hors transit d'ouverture, un passage de quelques jours est publié "
                "tel que la source le donne.",
                "`membre_id` : null signifie qu'aucune fiche n'a été collectée pour "
                "cette personne, pas qu'elle n'a rien fait.",
            ],
            "source": "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip",
            "licence_donnees": LICENCE_AN,
        },
        "legislatures": legislatures,
    }


def valider(document: dict[str, Any]) -> list[str]:
    """Ce que le document doit tenir pour être publié. Liste vide = conforme."""
    erreurs: list[str] = []
    vues: set[str] = set()
    for bloc in document.get("legislatures") or []:
        legislature = bloc.get("legislature")
        if legislature in vues:
            erreurs.append(f"législature {legislature} : publiée deux fois.")
        vues.add(legislature)
        acteurs: set[str] = set()
        for membre in bloc.get("membres") or []:
            qui = f"législature {legislature}, {membre.get('acteur_ref') or membre.get('nom')}"
            acteur_ref = membre.get("acteur_ref")
            if not acteur_ref:
                erreurs.append(f"{qui} : pas d'`acteur_ref`, donc pas de clé.")
            elif acteur_ref in acteurs:
                erreurs.append(f"{qui} : présent deux fois.")
            acteurs.add(acteur_ref)
            periodes = membre.get("periodes")
            if not isinstance(periodes, list) or not periodes:
                erreurs.append(f"{qui} : 'periodes' doit être une liste non vide.")
                continue
            debuts = [p.get("debut") for p in periodes]
            if any(d is None for d in debuts):
                erreurs.append(f"{qui} : une période sans début n'est pas datable.")
                continue
            if debuts != sorted(debuts):
                erreurs.append(f"{qui} : 'periodes[]' doit être triée par début croissant.")
            constitution = bloc.get("date_constitution_groupes")
            if any(an_roster.est_mandat_de_transit(p.get("fin"), constitution) for p in periodes):
                erreurs.append(f"{qui} : une période de transit d'ouverture est publiée.")
    return erreurs


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--out", type=Path, default=DEFAULT_SORTIE)
    parser.add_argument("--zip", type=Path, default=None,
                        help="archive AMO30 locale (défaut : cache du pipeline, téléchargée si absente)")
    parser.add_argument("--correspondance", type=Path,
                        default=correspondance_acteurs_an.CHEMIN_PAR_DEFAUT,
                        help="table slug ↔ acteur AN, lue pour rattacher une fiche à chaque personne")
    args = parser.parse_args(argv)

    if not args.correspondance.is_file():
        raise NonInscritsIndisponibles(
            f"Table de correspondance absente ({args.correspondance}) : sans elle, "
            "chaque personne serait publiée « sans fiche ». Le fichier committé est "
            "laissé en place.")
    try:
        index = an_roster.charger_index_gp(args.zip)
    except an_roster.RosterAnIndisponible as exc:
        raise NonInscritsIndisponibles(
            f"Archive AMO30 indisponible : la liste des non-inscrits est INCONNUE, "
            f"pas vide. Le fichier committé est laissé en place. ({exc})") from exc

    document = construire(index, an_roster._index_slug_par_acteur(args.correspondance))
    erreurs = valider(document)
    if erreurs:
        raise NonInscritsIndisponibles(
            "Document non conforme, rien n'est écrit :\n  " + "\n  ".join(erreurs[:20]))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for bloc in document["legislatures"]:
        membres = bloc["membres"]
        en_cours = sum(1 for m in membres if m["periodes"][-1]["fin"] is None)
        sans_fiche = sum(1 for m in membres if not m["membre_id"])
        print(f"→ législature {bloc['legislature']} : {len(membres)} personne(s), "
              f"dont {en_cours} en cours et {sans_fiche} sans fiche ; "
              f"transit d'ouverture écarté : {bloc['transit_d_ouverture']['mandats_ecartes']} mandat(s)")
    print(f"→ écrit dans {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
