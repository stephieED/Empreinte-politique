#!/usr/bin/env python3
"""legislatures_an.py — Construit `pivot_data/legislatures.json` (#1314).

CE QUE LE FICHIER PORTE. Une entrée par législature du corpus (XIVe à XVIIe) :
ses bornes, la façon dont elle a fini, la date à laquelle elle aurait dû finir,
et l'ordre de ses groupes dans l'hémicycle. C'est ce qu'une fiche de
législature (#1314) ne peut pas calculer seule sans charger les 600 profils
d'une législature ; tout le reste, elle le lit dans les fichiers par objet
(`dossiers_an/`, `textes_promulgues.json`, `commissions_dossiers.json`).

LES BORNES SONT CELLES DE L'ORGANE. AMO30 publie un organe `ASSEMBLEE` par
législature, daté (`viMoDe.dateDebut`, `dateFin`) : elles sont recopiées
verbatim, jamais déduites d'un premier ou d'un dernier scrutin.

LE MODE DE FIN SE LIT, IL NE SE DÉDUIT PAS D'UNE DATE.

- `dissolution` — un décret « portant dissolution de l'Assemblée nationale »
  paraît au Journal officiel dans les jours qui suivent la fin de l'organe. Il
  est lu dans les actes réglementaires que le dépôt collecte déjà
  (`pivot_data/actes_reglementaires/`, #1029), par son titre — ce que fait
  déjà `liens_lois` (AGENTS.md §6) —, et publié avec son identifiant.
- `terme` — la législature a fini le jour que le Code électoral fixe.
- Sinon `null`, avec son motif : `en_cours`, ou `fin_non_expliquee` quand ni
  l'un ni l'autre ne tient — jamais un mode choisi par défaut (§2 règle 5).

LE TERME PRÉVU EST UNE RÈGLE DE DROIT, APPLIQUÉE. Code électoral, art. LO 121 :
les pouvoirs de l'Assemblée expirent le troisième mardi de juin de la
cinquième année qui suit son élection. Aucun fichier de l'Assemblée ne publie
cette date ; elle est calculée, et la règle est publiée à côté. Vérifiée sur
les deux législatures allées à leur terme : le 20/06/2017 (XIVe) et le
21/06/2022 (XVe) sont les fins que l'organe publie.

L'ORDRE DES GROUPES EST CELUI DES SIÈGES. Pour chaque groupe (`GP`) de la
législature, le siège médian de ses membres, lu dans l'archive de la
législature (`candidate_profile._build_index_places_hemicycle`, #1317). Les
membres sont ceux du groupe au **jour de référence** : la fin de la
législature quand elle est close, la date de l'archive lue quand elle est en
cours — le jour même que décrivent les places. L'Assemblée numérote les sièges
de la droite vers la gauche de la présidence : le fichier publie la médiane, et
l'interface choisit le sens. La XIVe n'a pas d'archive de sa législature
(404) : ses sièges se lisent dans le fichier des places du site de l'Assemblée,
à l'état du 20/06/2017 (#1326, `candidate_profile.FICHIERS_PLACES_SITE_AN`) —
jamais dans l'archive d'une autre législature. Une législature dont la source
des places n'est pas lue ce run garde ses groupes avec leurs membres et sans
siège, motif dans `places_non_resolues` ; leur ordre dans la liste n'a alors
aucune signification.

Aucun appel réseau propre : l'archive AMO30 courante, les archives figées et le
fichier des places de la XIVe sont ceux que le pipeline télécharge déjà.

Usage :
    python3 src/legislatures_an.py
    python3 src/legislatures_an.py --out pivot_data/legislatures.json
"""
from __future__ import annotations

import argparse
import calendar
import json
import statistics
import sys
import time
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from couverture_dossiers import AN_DOSSIERS_ARCHIVES  # noqa: E402
from json_io import dumps_indente, ecrire_index_json  # noqa: E402
from licences import LICENCE_AN  # noqa: E402

SCHEMA_VERSION = "legislatures-v1"

DEFAUT_SORTIE = Path("pivot_data") / "legislatures.json"
DEFAUT_ACTES = Path("pivot_data") / "actes_reglementaires"

#: Les législatures publiées : celles dont le pipeline lit les dossiers. Dérivé,
#: jamais tenu en double.
LEGISLATURES_PUBLIEES: tuple[str, ...] = tuple(str(n) for n in sorted(AN_DOSSIERS_ARCHIVES))

MODE_DISSOLUTION = "dissolution"
MODE_TERME = "terme"
KNOWN_MODES_FIN: frozenset[str] = frozenset({MODE_DISSOLUTION, MODE_TERME})
KNOWN_MOTIFS_MODE_FIN_NON_RESOLU: frozenset[str] = frozenset({
    "en_cours",            # l'organe n'a pas de date de fin
    "fin_non_expliquee",   # ni décret de dissolution lu, ni fin au terme
})
#: Pourquoi `groupes` est `null`.
KNOWN_MOTIFS_GROUPES_NON_RESOLUS: frozenset[str] = frozenset({
    "referentiel_indisponible",   # AMO30 courant illisible : ni groupes ni membres
    "jour_de_reference_absent",   # ni fin de législature ni date d'archive
})
#: Pourquoi les groupes sont publiés sans siège (`place_mediane` à `null`).
KNOWN_MOTIFS_PLACES_NON_RESOLUES: frozenset[str] = frozenset({
    "legislature_sans_archive_figee",  # aucune source des places de la législature
    "archive_indisponible",            # l'archive n'a pas pu être lue ce run
})

#: Ce que le titre du décret dit, tel que le Journal officiel l'écrit
#: (« Décret du 9 juin 2024 portant dissolution de l'Assemblée nationale »).
TITRE_DISSOLUTION = "portant dissolution de l'Assemblée nationale"
#: Le décret paraît au Journal officiel le lendemain de sa signature : la
#: fenêtre de lecture après la fin de l'organe.
JOURS_APRES_LA_FIN = 7

REGLE_TERME = (
    "Code électoral, art. LO 121 : les pouvoirs de l'Assemblée nationale expirent "
    "le troisième mardi de juin de la cinquième année qui suit son élection."
)
#: Le Code électoral sur Légifrance. L'article n'est pas lié directement : son
#: identifiant n'a pas pu être relu (Légifrance refuse les requêtes non
#: interactives), et un lien deviné serait une source inventée.
SOURCE_TERME = "https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006070239"
URL_JORF = "https://www.legifrance.gouv.fr/jorf/id/{jorftext}"


# ── Le terme prévu ────────────────────────────────────────────────────────────

def troisieme_mardi_de_juin(annee: int) -> date:
    """Le troisième mardi de juin d'une année."""
    premier = date(annee, 6, 1)
    decalage = (calendar.TUESDAY - premier.weekday()) % 7
    return premier + timedelta(days=decalage + 14)


def terme_prevu(debut: Optional[str]) -> Optional[dict[str, str]]:
    """Le terme que l'art. LO 121 fixe à une législature ouverte le `debut`."""
    if not debut or len(debut) < 4 or not debut[:4].isdigit():
        return None
    return {
        "date": troisieme_mardi_de_juin(int(debut[:4]) + 5).isoformat(),
        "regle": REGLE_TERME,
        "source_url": SOURCE_TERME,
    }


# ── La dissolution, lue au Journal officiel ───────────────────────────────────

def _mois_suivant(mois: str) -> str:
    annee, numero = int(mois[:4]), int(mois[5:7])
    return f"{annee + numero // 12}-{numero % 12 + 1:02d}"


def decret_de_dissolution(fin: str, repertoire_actes: Path) -> Optional[dict[str, Any]]:
    """Le décret de dissolution paru dans les jours qui suivent `fin`, ou `None`.

    Lu dans les fichiers mensuels publiés par `actes_reglementaires.py`, lignes
    `[nature, titre, date_publi, ministère, NOR, numéro]` alignées sur `ids`.
    """
    borne = (date.fromisoformat(fin[:10]) + timedelta(days=JOURS_APRES_LA_FIN)).isoformat()
    for mois in (fin[:7], _mois_suivant(fin[:7])):
        try:
            publie = json.loads((Path(repertoire_actes) / f"{mois}.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        prefixe = publie.get("prefixe_ids") or "JORFTEXT"
        for ident, acte in zip(publie.get("ids") or [], publie.get("actes") or []):
            titre, date_publi, nor = acte[1], acte[2], acte[4]
            if (isinstance(titre, str) and TITRE_DISSOLUTION in titre
                    and isinstance(date_publi, str) and fin[:10] <= date_publi <= borne):
                jorftext = f"{prefixe}{ident}"
                return {
                    "jorftext": jorftext,
                    "titre": titre,
                    "date_publication": date_publi,
                    "nor": nor,
                    "source_url": URL_JORF.format(jorftext=jorftext),
                }
    return None


def mode_de_fin(fin: Optional[str], terme: Optional[dict[str, str]],
                decret: Optional[dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    """`(mode, None)` ou `(None, motif)`."""
    if not fin:
        return None, "en_cours"
    if decret:
        return MODE_DISSOLUTION, None
    if terme and fin[:10] == terme["date"]:
        return MODE_TERME, None
    return None, "fin_non_expliquee"


# ── Les groupes, par leurs sièges ─────────────────────────────────────────────

def organes_assemblee(zip_path: Path) -> dict[str, dict[str, Optional[str]]]:
    """`{législature: {organe_ref, debut, fin}}` des organes `ASSEMBLEE` d'AMO30."""
    trouves: dict[str, dict[str, Optional[str]]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for nom in zf.namelist():
            if not (nom.startswith("json/organe/") and nom.endswith(".json")):
                continue
            try:
                with zf.open(nom) as f:
                    organe = (json.load(f) or {}).get("organe") or {}
            except (json.JSONDecodeError, KeyError, OSError):
                continue
            if organe.get("codeType") != "ASSEMBLEE" or not organe.get("legislature"):
                continue
            vie = organe.get("viMoDe") or {}
            trouves[str(organe["legislature"])] = {
                "organe_ref": organe.get("uid"),
                "debut": vie.get("dateDebut"),
                "fin": vie.get("dateFin"),
            }
    return trouves


def _place(numero: Any) -> Optional[int]:
    return int(numero) if isinstance(numero, str) and numero.strip().isdigit() else None


def place_de(places_acteur: dict[str, Optional[str]], jour: str) -> Optional[int]:
    """La place du mandat de député le plus récent ouvert au plus tard le `jour`."""
    ouverts = sorted(d for d, p in places_acteur.items() if d and d[:10] <= jour and _place(p) is not None)
    return _place(places_acteur[ouverts[-1]]) if ouverts else None


def groupes_par_siege(index_gp: dict[str, Any], legislature: str, jour: str,
                      places: dict[str, dict[str, Optional[str]]]) -> list[dict[str, Any]]:
    """Les groupes `GP` de la législature, chacun avec la médiane des sièges de
    ses membres au `jour`, rangés par médiane croissante (numérotation de la
    source). Un groupe sans membre ce jour-là — dissous ou renommé avant — n'est
    pas dans la liste : il ne siégeait plus."""
    resultat = []
    for organe_ref, organe in (index_gp.get("organes") or {}).items():
        if str(organe.get("legislature")) != legislature:
            continue
        membres = {
            acteur for acteur, debut, fin in (index_gp.get("mandats") or {}).get(organe_ref, [])
            if debut and debut[:10] <= jour and (not fin or fin[:10] >= jour)
        }
        if not membres:
            continue
        sieges = [p for a in membres if (p := place_de(places.get(a) or {}, jour)) is not None]
        resultat.append({
            "organe_ref": organe_ref,
            "sigle": organe.get("sigle"),
            "libelle_abrege": organe.get("sigle_abrege"),
            "nom": organe.get("libelle"),
            "membres_au_jour": len(membres),
            "membres_avec_place": len(sieges),
            "place_mediane": statistics.median(sieges) if sieges else None,
            "place_min": min(sieges) if sieges else None,
            "place_max": max(sieges) if sieges else None,
        })
    return sorted(resultat, key=lambda g: (g["place_mediane"] is None, g["place_mediane"] or 0, g["organe_ref"]))


# ── La table ──────────────────────────────────────────────────────────────────

def entree(legislature: str, organe: dict[str, Optional[str]], *, source_url: str,
           repertoire_actes: Path, index_gp: Optional[dict[str, Any]],
           index_places: Optional[dict[str, Any]], motif_places: Optional[str]) -> dict[str, Any]:
    """L'entrée publiée d'une législature."""
    debut, fin = organe.get("debut"), organe.get("fin")
    terme = terme_prevu(debut)
    decret = decret_de_dissolution(fin, repertoire_actes) if fin else None
    mode, motif_mode = mode_de_fin(fin, terme, decret)

    groupes = motif_groupes = motif_sieges = jour_reference = None
    if index_gp is None:
        motif_groupes = "referentiel_indisponible"
    else:
        # Sans archive de la législature, les groupes restent publiés — leurs
        # membres se lisent dans l'archive courante —, mais sans un siège.
        motif_sieges = motif_places if index_places is None else None
        jour_reference = (fin or (index_places or {}).get("etat_au") or "")[:10] or None
        if jour_reference:
            groupes = groupes_par_siege(index_gp, legislature, jour_reference,
                                        (index_places or {}).get("places") or {})
        else:
            motif_groupes = "jour_de_reference_absent"
    return {
        "numero": int(legislature),
        "organe_ref": organe.get("organe_ref"),
        "debut": debut,
        "fin": fin,
        "source_url": source_url,
        "mode_fin": mode,
        "mode_fin_non_resolu": {"motif": motif_mode} if motif_mode else None,
        "decret_dissolution": decret,
        "terme_prevu": terme,
        "groupes": groupes,
        "groupes_non_resolus": {"motif": motif_groupes} if motif_groupes else None,
        "places_non_resolues": {"motif": motif_sieges} if motif_sieges else None,
        "groupes_jour_reference": jour_reference,
        "places_source_url": (index_places or {}).get("source_url"),
        "places_etat_au": (index_places or {}).get("etat_au"),
    }


def construire_table(repertoire_actes: Path) -> dict[str, dict[str, Any]]:
    """`{législature: entrée}`, ou `{}` si l'archive AMO30 n'est pas lisible."""
    import an_roster  # noqa: PLC0415 — imports tardifs : ils tirent le pipeline
    import candidate_profile  # noqa: PLC0415

    zip_path = candidate_profile._ensure_acteurs_historique_zip_downloaded()
    if zip_path is None:
        print("  [!] Archive AMO30 indisponible : aucune législature construite à ce run.")
        return {}
    try:
        organes = organes_assemblee(Path(zip_path))
    except (zipfile.BadZipFile, OSError) as exc:
        print(f"  [!] Archive AMO30 illisible ({exc}) : aucune législature construite à ce run.")
        return {}
    try:
        index_gp: Optional[dict[str, Any]] = an_roster.charger_index_gp(Path(zip_path))
    except an_roster.RosterAnIndisponible as exc:
        print(f"  [!] Groupes illisibles ({exc}) : législatures publiées sans groupes.")
        index_gp = None

    table: dict[str, dict[str, Any]] = {}
    for legislature in LEGISLATURES_PUBLIEES:
        organe = organes.get(legislature)
        if organe is None:
            print(f"  [!] Aucun organe ASSEMBLEE pour la {legislature}e législature dans AMO30.")
            continue
        index_places = motif_places = None
        if legislature not in candidate_profile.legislatures_avec_places_hemicycle():
            motif_places = "legislature_sans_archive_figee"
        else:
            index_places = candidate_profile._build_index_places_hemicycle(legislature)
            if index_places is None:
                motif_places = "archive_indisponible"
        table[legislature] = entree(
            legislature, organe, source_url=candidate_profile.AN_ACTEURS_HISTORIQUE_ZIP_URL,
            repertoire_actes=repertoire_actes, index_gp=index_gp,
            index_places=index_places, motif_places=motif_places,
        )
    return table


def _lire_existant(chemin: Path) -> dict[str, dict[str, Any]]:
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    legislatures = publie.get("legislatures") if isinstance(publie, dict) else None
    return legislatures if isinstance(legislatures, dict) else {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--out", default=str(DEFAUT_SORTIE),
                        help=f"Fichier à écrire (défaut : {DEFAUT_SORTIE}).")
    parser.add_argument("--actes", default=str(DEFAUT_ACTES),
                        help="Actes réglementaires publiés, où se lit un décret de dissolution "
                             f"(défaut : {DEFAUT_ACTES}).")
    args = parser.parse_args(argv)

    chemin = Path(args.out)
    collectee = construire_table(Path(args.actes))
    table = _lire_existant(chemin)
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
            "legislatures": dict(sorted(table.items(), key=lambda kv: int(kv[0]))),
        },
        dumps_indente,
    )
    for legislature, ligne in sorted(table.items(), key=lambda kv: int(kv[0])):
        groupes = ligne.get("groupes")
        print(f"  ✓ {legislature}e : {ligne['debut']} → {ligne['fin'] or 'en cours'}, "
              f"fin : {ligne['mode_fin'] or (ligne['mode_fin_non_resolu'] or {}).get('motif')}, "
              f"{len(groupes) if groupes is not None else 'aucun'} groupe(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
