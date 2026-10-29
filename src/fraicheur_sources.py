#!/usr/bin/env python3
"""À quelle date chaque famille de données a été relue à sa source (#1389).

Le site termine chaque bulle de section des fiches agrégées (lignée,
gouvernement, législature) par « <source> · à jour au JJ/MM/AAAA ». Cette date
n'est pas `sources[].synchro_le` des profils : celle-là dit quand la donnée a
**changé** (#343, gardée telle quelle pour le débogage et l'audit) ; celle-ci
dit quand un run l'a **relue avec succès**. Arbitré le 29/10/2026.

## Une date par famille, pas par source

Un run ne relit pas une source en entier : un run manuel laisse « interventions »
et « dossiers législatifs » décochés par défaut, un run limité (`test_slugs`,
`roster_limit`) ne relit pas tous les profils. Une famille (`an.votes`,
`an.interventions`…) n'avance donc que si :

1. les jobs qui la lisent ont tous réussi (`needs.<job>.result`) ;
2. le run couvrait tout le périmètre ;
3. sa case était cochée, pour les familles qui en dépendent ;
4. sa date a pu être relevée.

Sinon elle garde sa date précédente. Une famille jamais relevée vaut `null`,
avec sa raison (§2 règle 5) — jamais la date du run par défaut.

## L'état de la collecte, famille par famille

Chaque famille porte aussi un `etat` (arbitré le 29/10/2026) : `a_jour`
(relue à ce run), `en_echec` avec `en_echec_depuis` (le premier run en échec
depuis la dernière réussite), ou `non_relue` (par choix : case décochée, run
limité, job sauté). Un run qui ne relit pas une famille ne dit rien de sa santé :
un échec reste en place jusqu'à la prochaine réussite. « En échec » et non
« cassée » : l'état d'un job ne dit pas qui est en faute, la source ou notre
code.

## La date d'une famille lue à travers un cache

Les caches d'Actions restaurent les fichiers avec leur date d'écriture
(`tar -xf` sans `-m`), et leurs clés de repli peuvent restaurer une entrée de
plusieurs jours. La date d'une famille est donc celle de son **fichier témoin**
— l'archive téléchargée, ou l'index construit à partir d'elle —, la plus
ancienne entre les jobs qui l'ont relevée. Même raisonnement que la date de
l'état des places (`candidate_profile._etat_au_archive_courante`, #1317).

Une famille que son job retélécharge à chaque run (actes du Journal officiel,
ordre du jour, budgets) prend la date du run.

Usage :

    python3 src/fraicheur_sources.py relever --job extract-an --sortie _fraicheur/extract-an-x.json
    python3 src/fraicheur_sources.py composer --releves _fraicheur --needs "$NEEDS_JSON" \\
        --interventions true --dossiers true --perimetre-complet true
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable, Optional
from zoneinfo import ZoneInfo

CHEMIN_PAR_DEFAUT = Path("pivot_data") / "fraicheur_sources.json"
SCHEMA_VERSION = "fraicheur-sources-v1"
FUSEAU = ZoneInfo("Europe/Paris")

#: Les cases du formulaire dont dépend une famille.
CASE_INTERVENTIONS = "interventions"
CASE_DOSSIERS = "dossiers"

# Les fichiers témoins, relatifs à la racine. Écrits ici plutôt qu'importés de
# `candidate_profile` (qui tire `requests` et tout le pipeline) ; un test
# vérifie qu'ils restent égaux aux constantes des modules qui les écrivent.
TEMOIN_AMO30 = Path(".cache/acteurs_historique_an/acteurs_historique.zip")
TEMOIN_SCRUTINS = Path(".cache/scrutins_an/17/scrutins.json")
TEMOINS_SYCERON = (Path(".cache/syceron_an/17/index_par_acteur_extrait"),
                   Path(".cache/syceron_an/17/index_par_acteur"))
TEMOIN_QUESTIONS = Path(".cache/questions_an/17/index_par_acteur.json")
TEMOIN_DOSSIERS = Path(".cache/dossiers_an/dossiers.zip")
TEMOIN_AMENDEMENTS = Path(".cache/amendements_an/17/fraicheur.json")
# Fiche candidat (#1391), demandées par la session interface le 29/10/2026.
# L'archive du Sénat est gardée à côté du dump qu'on en extrait : le dump porte
# la date de l'export, l'archive celle du téléchargement (`curl`).
TEMOIN_SENAT = Path(".cache/senat/export_sens.zip")
TEMOINS_PE_MANDATS = (Path(".cache/europarl/meps_FR.json"), Path(".cache/europarl/organisations.json"))
_PARLTRACK = Path(".cache/parltrack")
TEMOIN_PT_VOTES = _PARLTRACK / "ep_votes.json.zst"
TEMOINS_PT_AMENDEMENTS = (_PARLTRACK / "ep_plenary_amendments.json.zst", _PARLTRACK / "ep_amendments.json.zst")
TEMOIN_PT_INTERVENTIONS = _PARLTRACK / "ep_mep_activities.json.zst"
TEMOIN_PT_TEXTES = _PARLTRACK / "ep_dossiers.json.zst"


@dataclass(frozen=True)
class Famille:
    source: str                          # id de `schemaSources.js`, ou clé propre (budgets)
    jobs: tuple[str, ...]                # jobs dont la réussite est exigée
    temoins: tuple[Path, ...] = ()       # vide : la date du run
    releve_par: tuple[str, ...] = ()     # jobs qui relèvent les témoins
    case: Optional[str] = None


_AN = ("extract-an", "extract-roster-groupes")

FAMILLES: dict[str, Famille] = {
    "an.mandats": Famille("an", _AN, (TEMOIN_AMO30,), _AN),
    "an.gouvernements": Famille("an", ("extract-gouvernements",)),
    "an.votes": Famille("an", _AN, (TEMOIN_SCRUTINS,), _AN),
    "an.interventions": Famille("an", _AN, TEMOINS_SYCERON, _AN, CASE_INTERVENTIONS),
    "an.questions": Famille("an", _AN, (TEMOIN_QUESTIONS,), _AN, CASE_INTERVENTIONS),
    "an.dossiers": Famille("an", _AN, (TEMOIN_DOSSIERS,), _AN, CASE_DOSSIERS),
    # `extract-amendements-an` n'est pas dans les `needs` du job de fusion :
    # son relevé n'est publié que s'il a réussi.
    "an.amendements": Famille("an", (), (TEMOIN_AMENDEMENTS,), ("extract-amendements-an",)),
    "an.ordre_du_jour": Famille("an", ("extract-articles-votes",)),
    "an.articles_votes": Famille("an", ("extract-articles-votes",)),
    "jo.actes": Famille("jo", ("extract-actes-jo",)),
    "budget_etat": Famille("budget_etat", ("extract-finances-etat",)),
    "drees": Famille("drees", ("extract-finances-etat",)),
    "unedic": Famille("unedic", ("extract-finances-etat",)),
    # Les sources de la fiche candidat. Leurs jobs sont `continue-on-error` :
    # le relevé porte l'état réel du job, `needs` n'y suffit pas.
    "sen.mandats": Famille("sen", (), (TEMOIN_SENAT,), ("extract-senat",)),
    "pe.mandats": Famille("pe", (), TEMOINS_PE_MANDATS, ("extract-ue-officiel",)),
    # Les titres français des documents : relus dans le job de fusion, sans
    # fichier témoin (le cache cumule des documents de dates différentes).
    "pe.documents": Famille("pe", (), (), ("merge-and-pivot",)),
    "pt.votes": Famille("pt", (), (TEMOIN_PT_VOTES,), ("extract-parltrack",)),
    "pt.amendements": Famille("pt", (), TEMOINS_PT_AMENDEMENTS, ("extract-parltrack",)),
    "pt.interventions": Famille("pt", (), (TEMOIN_PT_INTERVENTIONS,), ("extract-parltrack",)),
    "pt.textes": Famille("pt", (), (TEMOIN_PT_TEXTES,), ("extract-parltrack",)),
    # Sans cache : la date du run, si le job a réussi.
    "rne.mandats_locaux": Famille("rne", (), (), ("extract-mandats-locaux",)),
}


# ── Relever, dans le job qui a le cache ─────────────────────────────────────

def _jour(horodatage: float) -> str:
    return datetime.fromtimestamp(horodatage, tz=FUSEAU).date().isoformat()


def date_du_temoin(chemin: Path) -> Optional[str]:
    """La date (heure de Paris) d'un témoin, ou None s'il n'existe pas.

    L'indicateur des amendements porte sa propre date, et dit si la dernière
    construction a réussi : un index conservé après un échec n'est pas relu.
    """
    if not chemin.exists():
        return None
    if chemin.name == "fraicheur.json":
        try:
            contenu = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if contenu.get("derniere_construction_reussie") is not True:
            return None
        try:
            return datetime.strptime(contenu["horodatage"], "%Y-%m-%dT%H:%M:%S%z") \
                .astimezone(FUSEAU).date().isoformat()
        except (KeyError, TypeError, ValueError):
            return None
    return _jour(chemin.stat().st_mtime)


def relever(job: str, racine: Path = Path(".")) -> dict[str, Optional[str]]:
    """Les dates des familles que `job` relève, une par famille."""
    releve: dict[str, Optional[str]] = {}
    for nom, famille in FAMILLES.items():
        if job not in famille.releve_par:
            continue
        dates = [d for d in (date_du_temoin(racine / t) for t in famille.temoins) if d]
        releve[nom] = min(dates) if dates else None
    return releve


# ── Composer, dans le job de fusion ─────────────────────────────────────────

def lire_releves(dossier: Path) -> dict[str, list[dict[str, Any]]]:
    """Tous les relevés publiés, regroupés par famille : `{date, reussi, job}`.

    `reussi` est l'état du job au moment du relevé (`job.status`). Il ne se lit
    pas dans `needs` : `extract-an` et `extract-roster-groupes` portent
    `continue-on-error`, et un relevé d'un job en échec ne doit rien dater.
    """
    par_famille: dict[str, list[dict[str, Any]]] = {}
    if not dossier.is_dir():
        return par_famille
    for chemin in sorted(dossier.glob("*.json")):
        try:
            releve = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        reussi = releve.get("reussi") is True
        for famille, jour in (releve.get("familles") or {}).items():
            par_famille.setdefault(famille, []).append(
                {"date": jour, "reussi": reussi, "job": releve.get("job")})
    return par_famille


#: L'état d'une famille au dernier run, vocabulaire fermé (#1389, 29/10/2026).
ETAT_A_JOUR = "a_jour"          # relue avec succès à ce run
ETAT_EN_ECHEC = "en_echec"      # un job qui la lit a échoué ; persiste jusqu'à la prochaine réussite
ETAT_NON_RELUE = "non_relue"    # pas relue par choix : case décochée, run limité, job sauté
KNOWN_ETATS: frozenset[str] = frozenset({ETAT_A_JOUR, ETAT_EN_ECHEC, ETAT_NON_RELUE})

# « En échec » et non « cassée » : l'état d'un job ne dit pas si la source est
# tombée ou si notre code est en faute (même distinction que #562).


def _issue(famille: Famille, resultats: dict[str, str], cases: dict[str, bool],
           perimetre_complet: bool, releves: list[dict[str, Any]]) -> Optional[tuple[str, str]]:
    """`(état, motif)` quand la famille n'avance pas à ce run, None si elle avance."""
    echecs = [j for j in famille.jobs if resultats.get(j) == "failure"]
    if echecs:
        return ETAT_EN_ECHEC, "job en échec : " + ", ".join(echecs)
    # Un job sauté ou annulé n'a rien tenté : ce n'est pas une panne.
    autres = [j for j in famille.jobs if resultats.get(j) != "success"]
    if autres:
        return ETAT_NON_RELUE, "job " + ", ".join(f"{j} : {resultats.get(j) or 'absent'}" for j in autres)
    if not perimetre_complet:
        return ETAT_NON_RELUE, "run limité à une partie des profils"
    if famille.case and not cases.get(famille.case):
        return ETAT_NON_RELUE, f"case « {famille.case} » non cochée"
    en_echec = sorted({r["job"] or "?" for r in releves if not r["reussi"]})
    if en_echec:
        return ETAT_EN_ECHEC, "job en échec au moment du relevé : " + ", ".join(en_echec)
    # Un shard sans le fichier témoin n'a pas lu cette source (un candidat qui
    # n'a jamais siégé n'ouvre pas les scrutins) : il ne date rien, et ne
    # bloque rien. Mais un job réussi dont AUCUN shard n'a le témoin n'a rien
    # lu de ce qu'il devait lire : c'est un échec, pas un choix.
    if famille.temoins and not any(r["date"] for r in releves):
        return ETAT_EN_ECHEC, "aucun fichier témoin relevé"
    # Une famille sans témoin, datée par son relevé : sans relevé, le job n'a
    # rien dit de lui-même (arrêté avant, ou sauté par une condition).
    if famille.releve_par and not releves:
        return ETAT_EN_ECHEC, "aucun relevé publié par " + ", ".join(famille.releve_par)
    return None


def composer(
    precedent: Optional[dict[str, Any]],
    releves: dict[str, list[dict[str, Any]]],
    resultats: dict[str, str],
    cases: dict[str, bool],
    perimetre_complet: bool,
    date_du_run: str,
) -> dict[str, Any]:
    """Le document, famille par famille, à partir du précédent.

    L'état suit le dernier run qui a TENTÉ la famille : un run qui ne la relit
    pas par choix ne dit rien de sa santé, et laisse donc un échec en place
    (avec sa date de début) jusqu'à la prochaine réussite.
    """
    anciennes = (precedent or {}).get("familles") or {}
    familles: dict[str, Any] = {}
    for nom, famille in FAMILLES.items():
        releves_famille = releves.get(nom, [])
        issue = _issue(famille, resultats, cases, perimetre_complet, releves_famille)
        ancienne = anciennes.get(nom) or {}
        if issue is None:
            jour = (min(r["date"] for r in releves_famille if r["date"])
                    if famille.temoins else date_du_run)
            familles[nom] = {"source": famille.source, "a_jour_au": jour, "raison": None,
                             "etat": ETAT_A_JOUR, "en_echec_depuis": None, "motif_dernier_run": None}
            continue
        etat, motif = issue
        if etat == ETAT_NON_RELUE and ancienne.get("etat") == ETAT_EN_ECHEC:
            etat = ETAT_EN_ECHEC                       # rien ne dit qu'elle est réparée
        depuis = None
        if etat == ETAT_EN_ECHEC:
            depuis = (ancienne.get("en_echec_depuis") if ancienne.get("etat") == ETAT_EN_ECHEC
                      else None) or date_du_run
        jour = ancienne.get("a_jour_au")
        familles[nom] = {
            "source": famille.source,
            # Elle garde sa date : la donnée publiée est celle de la dernière
            # relecture réussie.
            "a_jour_au": jour,
            "raison": None if jour else
                f"jamais relue avec succès depuis l'ouverture de ce fichier ({motif})",
            "etat": etat,
            "en_echec_depuis": depuis,
            "motif_dernier_run": motif,
        }
    return {"schema_version": SCHEMA_VERSION, "genere_le": date_du_run, "familles": familles}


def valider(document: dict[str, Any]) -> list[str]:
    """Le contrat du fichier : une entrée par famille connue, une date OU une raison."""
    erreurs = []
    if document.get("schema_version") != SCHEMA_VERSION:
        erreurs.append(f"schema_version attendu {SCHEMA_VERSION!r}")
    familles = document.get("familles") or {}
    if set(familles) != set(FAMILLES):
        erreurs.append(f"familles inattendues : {sorted(set(familles) ^ set(FAMILLES))}")
    for nom, entree in familles.items():
        jour, raison = entree.get("a_jour_au"), entree.get("raison")
        if (jour is None) == (raison is None):
            erreurs.append(f"{nom} : une date ou une raison, exactement une")
        etat, depuis = entree.get("etat"), entree.get("en_echec_depuis")
        if etat not in KNOWN_ETATS:
            erreurs.append(f"{nom} : état inconnu {etat!r}")
        if (etat == ETAT_EN_ECHEC) != (depuis is not None):
            erreurs.append(f"{nom} : 'en_echec_depuis' si et seulement si l'état est en échec")
        if (etat == ETAT_A_JOUR) == (entree.get("motif_dernier_run") is not None):
            erreurs.append(f"{nom} : un motif si et seulement si la famille n'est pas à jour")
        for champ in ("a_jour_au", "en_echec_depuis"):
            valeur = entree.get(champ)
            if valeur is not None:
                try:
                    date.fromisoformat(valeur)
                except (TypeError, ValueError):
                    erreurs.append(f"{nom} : {champ} illisible {valeur!r}")
    return erreurs


def _booleen(texte: str) -> bool:
    return str(texte).strip().lower() == "true"


def main(argv: Optional[Iterable[str]] = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__,
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    sous = analyseur.add_subparsers(dest="commande", required=True)
    rel = sous.add_parser("relever", help="dans un job d'extraction, après son travail")
    rel.add_argument("--job", required=True)
    rel.add_argument("--racine", type=Path, default=Path("."))
    rel.add_argument("--sortie", type=Path, required=True)
    rel.add_argument("--reussi", required=True, help="${{ job.status == 'success' }}")
    com = sous.add_parser("composer", help="dans le job de fusion")
    com.add_argument("--releves", type=Path, required=True)
    com.add_argument("--needs", required=True, help="toJSON(needs)")
    com.add_argument("--interventions", required=True)
    com.add_argument("--dossiers", required=True)
    com.add_argument("--perimetre-complet", required=True)
    com.add_argument("--date-du-run", default=None)
    com.add_argument("--fichier", type=Path, default=CHEMIN_PAR_DEFAUT)
    args = analyseur.parse_args(list(argv) if argv is not None else None)

    if args.commande == "relever":
        releve = relever(args.job, args.racine)
        args.sortie.parent.mkdir(parents=True, exist_ok=True)
        args.sortie.write_text(json.dumps({"job": args.job, "reussi": _booleen(args.reussi), "familles": releve}, ensure_ascii=False),
                               encoding="utf-8")
        for nom, jour in releve.items():
            sans_temoin = not FAMILLES[nom].temoins
            print(f"{nom} : {jour or ('date du run' if sans_temoin else 'aucun fichier témoin')}")
        return 0

    needs = json.loads(args.needs or "{}")
    resultats = {job: (v or {}).get("result", "") for job, v in needs.items()}
    precedent = None
    if args.fichier.is_file():
        try:
            precedent = json.loads(args.fichier.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            precedent = None
    document = composer(
        precedent, lire_releves(args.releves), resultats,
        {CASE_INTERVENTIONS: _booleen(args.interventions), CASE_DOSSIERS: _booleen(args.dossiers)},
        _booleen(args.perimetre_complet),
        args.date_du_run or datetime.now(FUSEAU).date().isoformat(),
    )
    erreurs = valider(document)
    if erreurs:
        for e in erreurs:
            print(f"::error::FRAICHEUR_SOURCES — {e}", file=sys.stderr)
        return 1
    args.fichier.parent.mkdir(parents=True, exist_ok=True)
    args.fichier.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for nom, entree in document["familles"].items():
        print(f"{nom:<20} {entree['etat']:<10} {entree['a_jour_au'] or '—'}  "
              f"{('depuis ' + entree['en_echec_depuis']) if entree['en_echec_depuis'] else ''} "
              f"{entree.get('motif_dernier_run') or ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
