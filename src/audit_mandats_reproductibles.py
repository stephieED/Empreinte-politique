#!/usr/bin/env python3
"""
audit_mandats_reproductibles.py — Pour chaque mandat publié sans
`categorie_source`, dire si le référentiel vivant le porte encore (#839, lot B).

Pourquoi
--------
Le lot A compte : **406 mandats sans `categorie_source`, sur 45 profils**. Le
champ absent dit « personne n'a établi cette catégorie » (#718), et rien de
plus. Avant de parler de retrait, il faut savoir **lequel de ces mandats existe
encore dans une source** — et le savoir sans confondre deux choses :

  - « l'entrée ne revient pas telle quelle », qui est vrai de presque toutes,
    l'AN nommant l'organe autrement que l'ancienne source ;
  - « le fait n'est plus disponible », qui seul justifierait de le publier
    comme une perte, ou de le retirer.

Cette distinction a été confondue une fois, le 12/09/2026, dans un rapport à la
propriétaire : la mesure portait sur les libellés à l'intérieur du profil, et le
mot employé était « non reproductible ».

Deux référentiels, jamais un seul
---------------------------------
**AMO30** (`.cache/acteurs_historique_an/`, via
`candidate_profile._extract_mandats_officiels`) porte les organes de
l'Assemblée. Il ne porte **pas** les organes du Parlement européen : mesuré au
lot A, **21 des 406 entrées sont des organes européens** (2 profils). Les juger
sur AMO30 seul les déclarerait introuvables — donc retirables. Le second
référentiel est le bloc `mandat_europeen` du profil brut.

Aucun appel réseau : les deux lisent des fichiers déjà là. Vérifié le
12/09/2026 — 36 mandats AMO30 rendus pour `PA2150` en quelques secondes.

Les verdicts
------------
| Verdict | Ce qu'il dit |
| --- | --- |
| `reproduit_meme_periode` | le référentiel porte cet organe, sur une période qui recouvre celle publiée |
| `reproduit_autre_periode` | il porte l'organe, mais pas cette période : le **fait** existe, ce découpage-là non |
| `reproduit_referentiel_europeen` | l'organe est un organe du Parlement européen du profil |
| `periode_couverte_autrement` | aucun référentiel ne porte cet organe, mais un mandat **sourcé** du profil couvre la période : à lire à la main |
| `introuvable` | ni AMO30, ni l'européen, ni une période couverte |
| `sans_date` | l'entrée ne porte **aucune** date : rien ne permet de la situer, donc aucun verdict (§2 règle 5) |
| `acteur_non_resolu` | le slug n'est pas dans la table `raw_data/correspondance_acteurs_an.json` (#525) |
| `referentiel_indisponible` | l'extraction AMO30 n'a rien rendu : **jamais un verdict sur une absence** (résilience #241) |

Les trois derniers ne sont pas des jugements : ils déclarent ce que la mesure
n'a pas pu établir. Un lot de retrait ne doit toucher aucun d'eux.

L'appariement des libellés
--------------------------
`purge_mandats_dupliques._normalize_label` est réutilisé tel quel : il retire
les préfixes de nature que l'ancienne source ajoutait (« Groupe d'études
trufficulture » ↔ « Trufficulture »), obstacle central de #387. Le recopier ici
en ferait une seconde vérité.

Usage (depuis la racine du dépôt) :
    python3 src/audit_mandats_reproductibles.py
    python3 src/audit_mandats_reproductibles.py --introuvables     # la liste à relire à la main
    python3 src/audit_mandats_reproductibles.py --json verdicts.json
    python3 src/audit_mandats_reproductibles.py --only jean-luc-melenchon
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from candidate_profile import _extract_mandats_officiels
from population_profils import provenance_du_profil, ventiler_provenances
from purge_mandats_dupliques import (
    _acteur_du_slug,
    _normalize_label,
    _periodes_se_chevauchent,
)

PIVOT_PAR_DEFAUT = Path("pivot_data") / "profiles"
BRUT_PAR_DEFAUT = Path("raw_data") / "profiles"
SUFFIXE_PIVOT = ".pivot.json"

REPRODUIT_MEME_PERIODE = "reproduit_meme_periode"
REPRODUIT_LIBELLE_APPROCHE = "reproduit_libelle_approche"
REPRODUIT_AUTRE_PERIODE = "reproduit_autre_periode"
REPRODUIT_EUROPEEN = "reproduit_referentiel_europeen"
PERIODE_COUVERTE_AUTREMENT = "periode_couverte_autrement"
INTROUVABLE = "introuvable"
SANS_DATE = "sans_date"
ACTEUR_NON_RESOLU = "acteur_non_resolu"
REFERENTIEL_INDISPONIBLE = "referentiel_indisponible"

#: Ordre d'affichage : du plus établi au plus douteux, puis ce qui n'est pas un
#: verdict.
ORDRE_VERDICTS = (
    REPRODUIT_MEME_PERIODE,
    REPRODUIT_LIBELLE_APPROCHE,
    REPRODUIT_AUTRE_PERIODE,
    REPRODUIT_EUROPEEN,
    PERIODE_COUVERTE_AUTREMENT,
    INTROUVABLE,
    SANS_DATE,
    ACTEUR_NON_RESOLU,
    REFERENTIEL_INDISPONIBLE,
)

LIBELLES = {
    REPRODUIT_MEME_PERIODE: "reproduit — même organe, période recouvrante",
    REPRODUIT_LIBELLE_APPROCHE: "reproduit — libellé approché, période recouvrante",
    REPRODUIT_AUTRE_PERIODE: "reproduit — même organe, autre période",
    REPRODUIT_EUROPEEN: "reproduit — organe du Parlement européen du profil",
    PERIODE_COUVERTE_AUTREMENT: "période couverte par un mandat sourcé, organe absent — à relire",
    INTROUVABLE: "introuvable dans les deux référentiels — à relire",
    SANS_DATE: "aucune date : rien à situer, aucun verdict",
    ACTEUR_NON_RESOLU: "acteur non résolu (#525) — aucun verdict",
    REFERENTIEL_INDISPONIBLE: "référentiel AMO30 vide — aucun verdict (#241)",
}

#: Catégories d'un mandat sourcé qui peuvent couvrir la période d'une entrée
#: dont l'organe reste introuvable : appartenance de groupe, fonction
#: gouvernementale, mandat parlementaire. Le fait est alors porté ailleurs, sous
#: un autre nom — c'est ce que #718 a constaté, et ça se relit à la main.
CATEGORIES_COUVRANTES = frozenset({"groupe_politique", "fonction_gouvernementale", "mandat_electif"})

#: Nombre minimal de mots significatifs pour qu'un appariement approché soit
#: accepté. Deux mots rapprocheraient « les transports » de « les transports et
#: le tourisme » ; le seuil est mesuré sur les deux témoins, pas choisi a priori.
MOTS_SIGNIFICATIFS_MINIMUM = 3

#: Mots vides d'un libellé d'organe. Les garder ferait passer le seuil à des
#: appariements portés par « de la sur ».
_MOTS_VIDES = frozenset({"de", "du", "des", "la", "le", "les", "l", "d", "et", "a", "au", "aux",
                         "en", "sur", "pour", "dans", "par", "un", "une", "ou", "the", "of"})


def _mots_comparables(label: Any) -> frozenset[str]:
    """Les mots significatifs d'un libellé, apostrophes et ponctuation unifiées.

    `_normalize_label` (#387) déplie les accents et retire le préfixe de nature,
    mais **garde les apostrophes** : `l'impact` et `l\u2019impact` y restent
    distincts, et c'est ce qui faisait manquer la mission covid au calibrage du
    12/09/2026. Le normaliseur de #387 n'est pas modifié pour autant — il sert
    une purge, et l'élargir élargirait ses retraits.
    """
    if not isinstance(label, str):
        return frozenset()
    # L'apostrophe typographique est unifiée AVANT `_normalize_label`, sinon son
    # retrait de préfixe ne reconnaît pas « Mission d\u2019information sur … » et
    # les deux libellés gardent chacun des mots que l'autre n'a pas : aucune
    # inclusion, donc aucun appariement. C'est ce qui faisait manquer la mission
    # covid au calibrage du 12/09/2026.
    base = _normalize_label(label.replace("\u2019", "'").replace("\u02bc", "'"))
    if not base:
        return frozenset()
    mots = "".join(c if c.isalnum() else " " for c in base).split()
    return frozenset(m for m in mots if m not in _MOTS_VIDES)


def _libelles_approches(mandat_mots: frozenset[str], autre_mots: frozenset[str]) -> bool:
    """Vrai si l'un des deux jeux de mots contient l'autre, et qu'il pèse assez.

    L'inclusion vaut dans les deux sens : un référentiel ajoute un suffixe
    (« … de la francophonie a.p.f ») là où l'autre s'arrête.
    """
    if len(mandat_mots) < MOTS_SIGNIFICATIFS_MINIMUM or len(autre_mots) < MOTS_SIGNIFICATIFS_MINIMUM:
        return False
    return mandat_mots <= autre_mots or autre_mots <= mandat_mots


def organes_europeens(profil_brut: dict[str, Any] | None) -> set[str]:
    """Libellés normalisés des organes européens portés par le profil brut.

    `mandat_europeen.mandats_europeens[]` nomme la commission, la délégation ou
    le groupe politique par `organisation_nom`. Le mandat lui-même n'y figure
    pas sous ce nom : on ajoute la forme publiée par la normalisation.
    """
    if not isinstance(profil_brut, dict):
        return set()
    bloc = profil_brut.get("mandat_europeen")
    entrees = (bloc or {}).get("mandats_europeens") if isinstance(bloc, dict) else None
    organes = {
        _normalize_label(m.get("organisation_nom"))
        for m in entrees or []
        if isinstance(m, dict) and m.get("organisation_nom")
    }
    if bloc:
        # Le mandat lui-même n'a pas d'`organisation_nom` : la normalisation le
        # publie sous ce libellé. Ajouté **seulement** si le profil porte un
        # volet européen — sinon un profil strictement français verrait un
        # « Mandat de député européen » sans source déclaré reproduit.
        organes.add(_normalize_label("Mandat de député européen"))
    return {o for o in organes if o}


def classer_mandat(
    mandat: dict[str, Any],
    mandats_reference: list[dict[str, Any]],
    organes_ue: set[str],
    mandats_sources_du_profil: list[dict[str, Any]],
) -> str:
    """Le verdict d'une entrée, sans jamais deviner.

    L'ordre des tests est lui-même une décision : une entrée sans date n'est pas
    « introuvable », elle est **insituable**, et la ranger parmi les introuvables
    autoriserait un retrait sur une absence de mesure.
    """
    if not mandat.get("debut") and not mandat.get("fin"):
        return SANS_DATE

    libelle = _normalize_label(mandat.get("label"))
    homonymes = [m for m in mandats_reference if _normalize_label(m.get("label")) == libelle]
    if homonymes:
        if any(
            _periodes_se_chevauchent(mandat.get("debut"), mandat.get("fin"), m.get("debut"), m.get("fin"))
            for m in homonymes
        ):
            return REPRODUIT_MEME_PERIODE
        return REPRODUIT_AUTRE_PERIODE

    mots = _mots_comparables(mandat.get("label"))
    approches = [m for m in mandats_reference if _libelles_approches(mots, _mots_comparables(m.get("label")))]
    if approches and any(
        _periodes_se_chevauchent(mandat.get("debut"), mandat.get("fin"), m.get("debut"), m.get("fin"))
        for m in approches
    ):
        return REPRODUIT_LIBELLE_APPROCHE
    if approches:
        return REPRODUIT_AUTRE_PERIODE

    if libelle and libelle in organes_ue:
        return REPRODUIT_EUROPEEN
    if any(_libelles_approches(mots, _mots_comparables(o)) for o in organes_ue):
        return REPRODUIT_EUROPEEN

    if any(
        m.get("categorie") in CATEGORIES_COUVRANTES
        and _periodes_se_chevauchent(mandat.get("debut"), mandat.get("fin"), m.get("debut"), m.get("fin"))
        for m in mandats_sources_du_profil
    ):
        return PERIODE_COUVERTE_AUTREMENT

    return INTROUVABLE


def auditer_profil(
    profil: dict[str, Any],
    mandats_reference: list[dict[str, Any]] | None,
    organes_ue: set[str],
    acteur_resolu: bool,
) -> list[tuple[dict[str, Any], str]]:
    """Les entrées sans `categorie_source` de ce profil, chacune avec son verdict."""
    sans_estampille = [
        m for m in (profil.get("mandats") or [])
        if isinstance(m, dict) and m.get("categorie_source") is None
    ]
    if not sans_estampille:
        return []
    if not acteur_resolu:
        return [(m, ACTEUR_NON_RESOLU) for m in sans_estampille]
    if not mandats_reference:
        return [(m, REFERENTIEL_INDISPONIBLE) for m in sans_estampille]

    sources_du_profil = [
        m for m in (profil.get("mandats") or [])
        if isinstance(m, dict) and m.get("categorie_source")
    ]
    return [
        (m, classer_mandat(m, mandats_reference, organes_ue, sources_du_profil))
        for m in sans_estampille
    ]


def _lire(chemin: Path) -> Optional[dict[str, Any]]:
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return document if isinstance(document, dict) else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pivot-dir", default=str(PIVOT_PAR_DEFAUT), metavar="DOSSIER")
    parser.add_argument("--brut-dir", default=str(BRUT_PAR_DEFAUT), metavar="DOSSIER",
                        help="Le référentiel européen y est lu (`mandat_europeen`), absent du pivot.")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic, calibrage).")
    parser.add_argument("--introuvables", action="store_true",
                        help="Liste chaque entrée sans verdict favorable : c'est la matière du travail à la main.")
    parser.add_argument("--json", metavar="FICHIER", help="Écrit tous les verdicts, entrée par entrée.")
    args = parser.parse_args(argv)

    pivot_dir, brut_dir = Path(args.pivot_dir), Path(args.brut_dir)
    if not pivot_dir.is_dir():
        print(f"[!] Répertoire introuvable : {pivot_dir}", file=sys.stderr)
        return 2

    comptes: Counter[str] = Counter()
    provenances_par_verdict: dict[str, list[str]] = {v: [] for v in ORDRE_VERDICTS}
    a_relire: list[dict[str, Any]] = []
    rapport: dict[str, Any] = {"profils": {}}

    for chemin in sorted(pivot_dir.glob("*" + SUFFIXE_PIVOT)):
        slug = chemin.name[: -len(SUFFIXE_PIVOT)]
        if args.only and slug != args.only:
            continue
        profil = _lire(chemin)
        if profil is None:
            continue
        if not any(m.get("categorie_source") is None for m in (profil.get("mandats") or []) if isinstance(m, dict)):
            continue

        acteur = _acteur_du_slug(slug)
        reference = _extract_mandats_officiels(acteur) if acteur else None
        verdicts = auditer_profil(profil, reference, organes_europeens(_lire(brut_dir / f"{slug}.json")), bool(acteur))
        provenance = provenance_du_profil(profil)

        vus: Counter[str] = Counter()
        for mandat, verdict in verdicts:
            comptes[verdict] += 1
            vus[verdict] += 1
            if verdict in (PERIODE_COUVERTE_AUTREMENT, INTROUVABLE, SANS_DATE):
                a_relire.append({
                    "slug": slug, "verdict": verdict, "categorie": mandat.get("categorie"),
                    "label": mandat.get("label"), "debut": mandat.get("debut"), "fin": mandat.get("fin"),
                })
        for verdict in vus:
            provenances_par_verdict[verdict].append(provenance)
        rapport["profils"][slug] = {
            "provenance": provenance, "acteur_an": acteur,
            "verdicts": dict(vus),
            "entrees": [{"verdict": v, **{k: m.get(k) for k in ("categorie", "label", "debut", "fin")}}
                        for m, v in verdicts],
        }

    total = sum(comptes.values())
    print("## Reproductibilité des mandats sans `categorie_source`\n")
    print(f"{total} entrée(s) jugée(s) sur {len(rapport['profils'])} profil(s).\n")
    print("| Verdict | Entrées | Profils |")
    print("| --- | ---: | --- |")
    for verdict in ORDRE_VERDICTS:
        if not comptes[verdict]:
            continue
        ventilation = ventiler_provenances(provenances_par_verdict[verdict])
        print(f"| {LIBELLES[verdict]} | {comptes[verdict]} | {ventilation.cellule_markdown()} |")

    etablis = sum(comptes[v] for v in (REPRODUIT_MEME_PERIODE, REPRODUIT_LIBELLE_APPROCHE,
                                       REPRODUIT_AUTRE_PERIODE, REPRODUIT_EUROPEEN))
    print(f"\n**{etablis} entrée(s) sur {total} sont portées par un référentiel vivant.** "
          f"{len(a_relire)} demandent une relecture à la main : aucun retrait ne s'en déduit.")

    if args.introuvables:
        print("\n### À relire à la main\n")
        print("| Profil | Verdict | Catégorie | Libellé | Début | Fin |")
        print("| --- | --- | --- | --- | --- | --- |")
        for entree in a_relire:
            print(f"| `{entree['slug']}` | {entree['verdict']} | {entree['categorie']} | "
                  f"{entree['label']} | {entree['debut'] or '—'} | {entree['fin'] or '—'} |")

    if args.json:
        rapport["totaux"] = dict(comptes)
        Path(args.json).write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n→ Verdicts détaillés : {args.json}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
