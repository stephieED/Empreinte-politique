#!/usr/bin/env python3
"""textes_promulgues.py — Construit `pivot_data/textes_promulgues.json`.

CE QUE LE FICHIER PORTE. Une entrée par dossier législatif **promulgué**, lue
dans les archives de dossiers de l'Assemblée : la date de promulgation, le
numéro de la loi, son intitulé, la nature de la procédure (projet ou
proposition), la commission saisie au fond et la chambre de première lecture.
607 dossiers sur les 10 967 des archives XIV à XVII (mesuré le 23/09/2026).

POURQUOI CETTE POPULATION, ET PAS UNE AUTRE. Remonté par l'interface le
23/09/2026 : mettre en regard, sur une fiche de gouvernement, les textes
promulgués et les actes parus au Journal officiel. Les deux populations
lisibles jusqu'ici ne le permettaient pas —

- les `textes[]` d'une fiche de gouvernement sont ceux qu'un de ses membres a
  **initiés** : 1 seul promulgué sur la fenêtre de LECORNU_II ;
- l'union des `textes_portes` des profils collectés est **ce que nos rosters
  portent**, pas ce que le Parlement a promulgué : 13 dossiers sur la même
  fenêtre, et l'écart avec la réalité n'est pas mesurable de l'intérieur.

Une loi promulguée n'appartient à personne : elle est un fait du Parlement. Ce
fichier la publie donc pour elle-même, et le rattachement à un gouvernement se
fait par la **date de promulgation** contre la période de la fiche — jamais par
l'initiative, qui attribuerait au gouvernement le travail du Parlement.

CE QU'IL NE PORTE PAS. Aucun lien vers les décrets d'application : la source ne
qualifie plus ce lien depuis 2024 (0 des 188 lois du fonds promulguées depuis le
01/01/2024, voir `docs/sources/jorf-dila.md`), et une colonne à moitié vide se
lirait comme un manquement de l'exécutif.

LA CHAMBRE DE PREMIÈRE LECTURE EST DÉRIVÉE DES DATES DE DÉPÔT, et c'est à
déclarer : **tout** dossier promulgué porte un `AN1-DEPOT` et un `SN1-DEPOT`
(607 sur 607), le second étant la transmission quand le texte vient de
l'Assemblée. C'est donc le dépôt le **plus ancien** qui dit l'origine, et deux
dates égales ou absentes rendent `null` plutôt qu'un choix arbitraire
(§2 règle 5). Mesuré sur les 607 : 242 dossiers de première lecture au Sénat.

ADDITIF, JAMAIS DESTRUCTEUR. Même règle que `build_commissions_dossiers.py` : un
run sans archives lisibles rend une table vide, et le fichier publié est
conservé (AGENTS.md §3a). `--no-merge` force la reconstruction complète.

Usage :
    python3 src/textes_promulgues.py
    python3 src/textes_promulgues.py --out pivot_data/textes_promulgues.json
    python3 src/textes_promulgues.py --no-merge
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gouvernement_textes import ensure_dossiers_zips_downloaded, iter_dossiers_bruts  # noqa: E402
from json_io import dumps_indente, ecrire_index_json  # noqa: E402
import lois_jorf  # noqa: E402
from licences import LICENCE_AN  # noqa: E402

SCHEMA_VERSION = "textes-promulgues-v1"

DEFAUT_SORTIE = Path("pivot_data") / "textes_promulgues.json"
DEFAUT_COMMISSIONS = Path("pivot_data") / "commissions_dossiers.json"

#: L'acte qui fait qu'une loi est promulguée, tel que la source le code.
CODE_PROMULGATION = "PROM-PUB"

#: Les deux dépôts de première lecture, et la chambre qu'ils désignent. Les
#: valeurs sont celles de `schema_pivot.KNOWN_CHAMBRES`.
CHAMBRE_PAR_DEPOT = {"AN1-DEPOT": "assemblee_nationale", "SN1-DEPOT": "senat"}


def iter_actes(noeud: Any) -> Iterator[dict[str, Any]]:
    """Tous les actes législatifs d'un dossier, à tous les étages.

    Les actes s'imbriquent (`actesLegislatifs.acteLegislatif.actesLegislatifs`…)
    et la source alterne entre un objet et une liste au même endroit : le
    parcours ne suppose ni l'un ni l'autre.
    """
    if isinstance(noeud, dict):
        if noeud.get("codeActe"):
            yield noeud
        for valeur in noeud.values():
            yield from iter_actes(valeur)
    elif isinstance(noeud, list):
        for element in noeud:
            yield from iter_actes(element)


def _jour(valeur: Any) -> Optional[str]:
    """`AAAA-MM-JJ` d'une date de la source, qui l'écrit avec son fuseau."""
    if not isinstance(valeur, str) or len(valeur) < 10:
        return None
    return valeur[:10]


def promulgation(dossier: dict[str, Any]) -> Optional[dict[str, Any]]:
    """L'acte de promulgation d'un dossier, ou `None` s'il n'en porte pas."""
    for acte in iter_actes(dossier.get("actesLegislatifs")):
        if acte.get("codeActe") == CODE_PROMULGATION:
            return acte
    return None


def chambre_premiere_lecture(dossier: dict[str, Any]) -> Optional[str]:
    """La chambre du dépôt le plus ancien, ou `None` si rien ne la départage."""
    dates: dict[str, str] = {}
    for acte in iter_actes(dossier.get("actesLegislatifs")):
        chambre = CHAMBRE_PAR_DEPOT.get(acte.get("codeActe") or "")
        jour = _jour(acte.get("dateActe"))
        if chambre and jour:
            dates.setdefault(chambre, jour)
    if len(dates) < 2:
        # Un seul dépôt daté : il dit la chambre. Aucun : rien à dire.
        return next(iter(dates), None)
    (premiere, jour_premier), (_, jour_second) = sorted(dates.items(), key=lambda x: x[1])
    return premiere if jour_premier < jour_second else None


def entree(dossier: dict[str, Any], commission: Optional[dict[str, Any]],
           lois: Optional[dict[str, list[list[str]]]] = None) -> Optional[dict[str, Any]]:
    """L'enregistrement publié d'un dossier promulgué, ou `None`.

    `commission` vient de `pivot_data/commissions_dossiers.json`, construit juste
    avant : son absence est publiée `null`, jamais rattrapée depuis l'intitulé —
    c'est la matière de la ligne, et une matière devinée est une matière fausse
    (§2 règle 8).
    """
    acte = promulgation(dossier)
    if acte is None:
        return None
    info_jo = acte.get("infoJO") or {}
    jorftext = lois_jorf.resoudre(lois or {}, acte.get("codeLoi"))
    titre_dossier = dossier.get("titreDossier") or {}
    procedure = dossier.get("procedureParlementaire") or {}
    return {
        "date_promulgation": _jour(info_jo.get("dateJO")) or _jour(acte.get("dateActe")),
        "numero_loi": acte.get("codeLoi"),
        "nor": info_jo.get("referenceNOR"),
        "titre": titre_dossier.get("titre"),
        "nature_procedure": procedure.get("libelle") or procedure.get("code"),
        "commission": commission,
        "chambre_premiere_lecture": chambre_premiere_lecture(dossier),
        # L'identifiant de la loi au Journal officiel, par où se joignent les
        # `liens_lois` des actes réglementaires (`lois_jorf`). Les archives de
        # l'Assemblée ne le publient pas ; le NOR ne suffirait pas, absent sur
        # 412 des 1 015 textes. `null` quand la table ne le résout pas, et une
        # liste quand la source a publié la loi deux fois (rectificatif).
        "jorftext": (jorftext[0] if jorftext else None),
        "jorftext_autres": (jorftext[1:] or None),
    }


def construire_table(
    archives: list[tuple[int, Path]],
    commissions: dict[str, dict[str, Any]],
    lois: Optional[dict[str, list[list[str]]]] = None,
) -> dict[str, dict[str, Any]]:
    """`{uid de dossier: entrée}` pour les seuls dossiers promulgués."""
    table: dict[str, dict[str, Any]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if not isinstance(uid, str) or not uid:
            continue
        ligne = entree(dossier, commissions.get(uid), lois)
        if ligne is not None:
            table[uid] = ligne
    return table


def charger_commissions(chemin: Path) -> dict[str, dict[str, Any]]:
    """La table `dossier → commission au fond` déjà publiée, ou `{}`."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    commissions = publie.get("commissions") if isinstance(publie, dict) else None
    return commissions if isinstance(commissions, dict) else {}


def _lire_existant(chemin: Path) -> dict[str, dict[str, Any]]:
    """Table déjà publiée, ou `{}` — un fichier illisible ne fait pas échouer."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    textes = publie.get("textes") if isinstance(publie, dict) else None
    return textes if isinstance(textes, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--out", default=str(DEFAUT_SORTIE),
                        help=f"Fichier à écrire (défaut : {DEFAUT_SORTIE}).")
    parser.add_argument("--commissions", default=str(DEFAUT_COMMISSIONS),
                        help="Table des commissions saisies au fond, pour la matière "
                             f"de chaque ligne (défaut : {DEFAUT_COMMISSIONS}).")
    parser.add_argument("--table-lois", default=str(lois_jorf.CHEMIN_PAR_DEFAUT),
                        help="Table `numéro de loi → identifiant JORFTEXT` (défaut : "
                             f"{lois_jorf.CHEMIN_PAR_DEFAUT}), tenue à jour par "
                             "`actes_reglementaires.py`.")
    parser.add_argument("--no-merge", action="store_true",
                        help="Reconstruction complète au lieu d'une fusion additive. "
                             "À réserver à un run qui a lu toutes les archives : sur un "
                             "run partiel, les dossiers non revus disparaîtraient.")
    args = parser.parse_args(argv)

    chemin = Path(args.out)
    commissions = charger_commissions(Path(args.commissions))
    if not commissions:
        print(f"  [!] {args.commissions} illisible ou absent : aucune matière sur les "
              "lignes de ce run (la commission reste `null`, jamais devinée).")
    try:
        archives = ensure_dossiers_zips_downloaded()
    except Exception as exc:  # noqa: BLE001 — une source absente est nommée, pas fatale
        print(f"  [!] Archives de dossiers indisponibles ({exc}) : aucun texte promulgué "
              "collecté à ce run.")
        archives = []

    lois = lois_jorf.charger(Path(args.table_lois))
    if not lois:
        print(f"  [!] {args.table_lois} illisible ou absente : aucun identifiant JORFTEXT "
              "sur les textes de ce run (`jorftext` reste `null`).")
    collectee = construire_table(archives, commissions, lois) if archives else {}
    if not collectee:
        print("  [!] Aucun texte promulgué collecté à ce run.")

    table = dict({} if args.no_merge else _lire_existant(chemin))
    table.update(collectee)
    if not table:
        print("  [!] Table vide et rien de publié : aucun fichier écrit.")
        return 0

    ecrire_index_json(
        chemin,
        {
            "schema_version": SCHEMA_VERSION,
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": LICENCE_AN,
            "textes": table,
        },
        dumps_indente,
    )
    sans_commission = sum(1 for v in table.values() if not v.get("commission"))
    conservees = len(table) - len(collectee)
    print(f"  ✓ {len(table)} texte(s) promulgué(s) → {chemin}")
    print(f"      sans commission au fond : {sans_commission} (absence déclarée)")
    if conservees > 0:
        print(f"      dont {conservees} conservé(s) d'un run précédent (non revus par celui-ci)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
