#!/usr/bin/env python3
"""dossiers_an.py — Construit `pivot_data/dossiers_an/<législature>.json` (#1314).

CE QUE LE FICHIER PORTE. Une ligne par dossier législatif des archives de
l'Assemblée (XIVe à XVIIe, plus la traîne des législatures antérieures que ces
archives contiennent), avec ce qu'aucun autre fichier du pivot ne publiait :
son titre, sa nature, son dépôt, ses auteurs, son sort, l'étape que
l'Assemblée a atteinte à chaque législature, ses scrutins et ses 49.3.

POURQUOI UN FICHIER PAR OBJET, ET NON PAR LÉGISLATURE. Arbitré le 22/10/2026
(option B) : la fiche d'une législature (#1314) filtre ce fichier, elle n'en
reçoit pas une copie. Ce que d'autres fichiers publient déjà par dossier ne
s'y recopie pas — la commission saisie au fond (`commissions_dossiers.json`),
la promulgation (`textes_promulgues.json`). Ils se joignent par l'uid du
dossier, comme l'interface le fait déjà. Une seule exception, dite :
`derniere_adoption_an` est calculée ici pour **tous** les dossiers par la
fonction même de `textes_promulgues.py` (#1320), qui ne la publie que pour les
lois promulguées — un texte adopté par l'Assemblée et pas encore loi n'avait
nulle part où la porter.

L'ÉTAPE À L'ASSEMBLÉE EST PAR LÉGISLATURE, ET LA LÉGISLATURE EST CELLE DE
L'ACTE. Chaque acte porte son uid, préfixé de la législature où il a eu lieu
(`L16-VD…`) — 119 431 des 119 444 actes des quatre archives (mesuré le
22/10/2026). Un dossier ouvert en XVe et débattu en XVIe a donc deux étapes,
et aucune date de législature n'est rapprochée de la date d'un acte pour le
dire. Trois valeurs, la règle de #997 pour la commission :

- `depose` — l'Assemblée n'a fait que l'enregistrer (dépôt, transmission,
  saisie automatique de la commission) ;
- `examine_en_commission` — une réunion ou un rapport de commission
  (`gouvernement_textes.est_examen_en_commission`) ;
- `debattu_en_seance` — un acte de séance (`AN…-DEBATS…`).

Un dossier sans aucun acte de l'Assemblée — un texte resté au Sénat — a un
`etape_an` vide : toutes ses étapes ont été lues, aucune n'est à l'Assemblée.

LES AUTEURS SONT LUS DANS LE MANDAT QUE LE DOSSIER CITE. `initiateur.acteurs`
donne, pour chaque auteur, son `acteurRef` et le `mandatRef` au titre duquel il
dépose. C'est ce mandat, résolu dans AMO30, qui dit la qualité — député,
sénateur, membre du gouvernement, président de la République —, jamais le
préfixe du texte (`PIONAN`, `PRJLAN`), faux pour 30 des 218 textes XVIe relus
par l'interface. Mesuré le 22/10/2026 : 23 948 des 23 955 références résolues.
Le groupe est celui du jour du dépôt : un mandat `GP` (député) ou
`GROUPESENAT` (sénateur) ouvert ce jour-là.

UN FICHIER PAR LÉGISLATURE, PARCE QU'UN SEUL PÈSE 16 MO. Les 14 377 dossiers
d'un seul tenant faisaient 16,6 Mo (1,6 Mo compressé) ; une fiche de
législature n'en lit qu'un quart. Découpés, 3 à 4,8 Mo chacun (270 à 430 Ko
compressés), et les noms des auteurs et des organes une fois par fichier
(`acteurs`, `organes`) au lieu d'une fois par ligne.

LES DÉCISIONS QUI LE GOUVERNENT. `docs/decisions/legislatures-et-dossiers-par-objet-1314.md`
(la forme, arbitrée), `docs/decisions/examen-en-commission-997.md` (ce qui fait
un examen en commission), `docs/decisions/adoption-an-lois-promulguees-1320.md`
(la dernière adoption).

ADDITIF, JAMAIS DESTRUCTEUR. Même règle que `textes_promulgues.py` : un run
sans archive lisible conserve le fichier publié (AGENTS.md §3a). `--no-merge`
force la reconstruction complète.

Usage :
    python3 src/dossiers_an.py
    python3 src/dossiers_an.py --out pivot_data/dossiers_an --no-merge
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gouvernement_textes import (  # noqa: E402
    _determine_statut,
    _source_url,
    ensure_dossiers_zips_downloaded,
    est_examen_en_commission,
    iter_dossiers_bruts,
    nature_texte_depose,
)
from json_io import dumps_ligne, ecrire_index_json  # noqa: E402
from licences import LICENCE_AN  # noqa: E402
from scrutins_dossiers_an import cle_depuis_uid  # noqa: E402
from textes_promulgues import (  # noqa: E402
    FAM_CODE_49_3,
    _fam_code,
    _jour,
    _vote_refs,
    chambre_premiere_lecture,
    derniere_adoption_an,
    iter_actes,
)

SCHEMA_VERSION = "dossiers-an-v1"

DEFAUT_REPERTOIRE = Path("pivot_data") / "dossiers_an"
DEFAUT_SCRUTINS = Path("pivot_data") / "scrutins.json"

# ── Les vocabulaires fermés (AGENTS.md §4 : on étend, on ne contourne pas) ────

ETAPE_DEPOSE = "depose"
ETAPE_COMMISSION = "examine_en_commission"
ETAPE_SEANCE = "debattu_en_seance"
#: Rangées dans l'ordre du parcours : l'étape d'une législature est la plus
#: avancée de ses actes.
ETAPES_AN: tuple[str, ...] = (ETAPE_DEPOSE, ETAPE_COMMISSION, ETAPE_SEANCE)
KNOWN_ETAPES_AN: frozenset[str] = frozenset(ETAPES_AN)

#: La qualité d'un auteur, par le `typeOrgane` du mandat que le dossier cite.
QUALITE_PAR_TYPE_MANDAT: dict[str, str] = {
    "ASSEMBLEE": "depute",
    "SENAT": "senateur",
    "MINISTERE": "membre_du_gouvernement",
    "GOUVERNEMENT": "membre_du_gouvernement",
    "PRESREP": "president_de_la_republique",
}
KNOWN_QUALITES_INITIATEUR: frozenset[str] = frozenset(QUALITE_PAR_TYPE_MANDAT.values())

#: Le mandat d'appartenance à un groupe, par qualité. Un membre du gouvernement
#: ou le président de la République ne siège dans aucun groupe : la question
#: ne se pose pas (`qualite_sans_groupe`).
TYPE_GROUPE_PAR_QUALITE: dict[str, str] = {"depute": "GP", "senateur": "GROUPESENAT"}

#: Pourquoi `qualite` est `null`.
KNOWN_MOTIFS_QUALITE_NON_RESOLUE: frozenset[str] = frozenset({
    "sans_mandat_ref",       # le dossier nomme l'acteur sans le mandat
    "mandat_introuvable",    # AMO30 ne porte pas ce mandat
    "type_mandat_inconnu",   # le mandat existe, d'un type que la table ne nomme pas
    "referentiel_indisponible",  # AMO30 n'a pas pu être lu ce run
})
#: Pourquoi `groupe` est `null`.
KNOWN_MOTIFS_GROUPE_NON_RESOLU: frozenset[str] = frozenset({
    "qualite_sans_groupe",   # gouvernement, présidence : aucun groupe à avoir
    "qualite_non_resolue",   # rien à quoi rattacher un groupe
    "date_depot_absente",    # aucun jour auquel lire l'appartenance
    "aucun_groupe_a_la_date",  # aucun mandat de groupe ouvert ce jour-là
    "organe_introuvable",    # le mandat vise un organe absent du référentiel
})
#: Pourquoi `initiateurs` est `null`.
KNOWN_MOTIFS_INITIATEURS_NON_RESOLUS: frozenset[str] = frozenset({
    "sans_initiateur",       # le dossier ne porte aucun bloc `initiateur`
    "initiative_d_organe",   # seul un organe est nommé (`organes_initiateurs`)
})
#: Pourquoi `statut` est `null` : `_determine_statut` a rencontré un statut de
#: décision que sa table ne connaît pas.
KNOWN_MOTIFS_STATUT_NON_RESOLU: frozenset[str] = frozenset({"fam_code_inconnu"})

#: L'issue d'un engagement de responsabilité (art. 49, al. 3), lue sur la
#: décision de l'Assemblée : `TSORTF06` « considéré comme adopté », `TSORTF24`
#: « considéré comme rejeté » (une motion de censure a été adoptée).
FAM_CODE_49_3_REJETE = "TSORTF24"
ISSUE_49_3_PAR_FAM_CODE: dict[str, str] = {
    FAM_CODE_49_3: "considere_adopte",
    FAM_CODE_49_3_REJETE: "considere_rejete",
}
KNOWN_ISSUES_49_3: frozenset[str] = frozenset(ISSUE_49_3_PAR_FAM_CODE.values())

#: `type_scrutin` d'un vote solennel dans `pivot_data/scrutins.json`.
TYPE_SCRUTIN_SOLENNEL = "solennel"

_RX_LEGISLATURE_ACTE = re.compile(r"^L(\d+)-")


# ── Les actes de l'Assemblée ──────────────────────────────────────────────────

def est_acte_an(code_acte: Any) -> bool:
    """Un acte de l'Assemblée : son code commence par `AN`, ou c'est la lecture
    des conclusions d'une CMP devant elle (`CMP-DEBATS-AN-…`). La CMP elle-même
    est une commission des deux chambres : elle n'est rangée d'aucun côté."""
    if not isinstance(code_acte, str):
        return False
    return code_acte.startswith("AN") or code_acte.startswith("CMP-DEBATS-AN")


def etape_de_l_acte(code_acte: str) -> str:
    """L'étape qu'un acte de l'Assemblée atteste."""
    if "-DEBATS" in code_acte:
        return ETAPE_SEANCE
    if est_examen_en_commission(code_acte):
        return ETAPE_COMMISSION
    return ETAPE_DEPOSE


def legislature_de_l_acte(acte: dict[str, Any]) -> Optional[str]:
    """`"16"` pour un acte `L16-…`, `None` si l'uid ne la porte pas."""
    uid = acte.get("uid")
    trouve = _RX_LEGISLATURE_ACTE.match(uid) if isinstance(uid, str) else None
    return trouve.group(1) if trouve else None


def etapes_an(dossier: dict[str, Any]) -> tuple[dict[str, str], int]:
    """`({législature: étape la plus avancée}, actes AN sans législature)`.

    Un conteneur d'étape (`AN1`, `AN1-COM`) porte lui aussi un uid daté de sa
    législature, et dit « déposé » : il n'avance jamais l'étape au-delà de ce
    que ses actes attestent.
    """
    etapes: dict[str, str] = {}
    sans_legislature = 0
    for acte in iter_actes(dossier.get("actesLegislatifs")):
        code = acte.get("codeActe")
        if not est_acte_an(code):
            continue
        legislature = legislature_de_l_acte(acte)
        if legislature is None:
            sans_legislature += 1
            continue
        etape = etape_de_l_acte(code)
        actuelle = etapes.get(legislature)
        if actuelle is None or ETAPES_AN.index(etape) > ETAPES_AN.index(actuelle):
            etapes[legislature] = etape
    return dict(sorted(etapes.items(), key=lambda kv: int(kv[0]))), sans_legislature


def jour_du_depot(dossier: dict[str, Any]) -> Optional[str]:
    """Le jour du dépôt le plus ancien (`…-DEPOT`), ou `None`."""
    jours = [
        j for a in iter_actes(dossier.get("actesLegislatifs"))
        if str(a.get("codeActe") or "").endswith("-DEPOT") and (j := _jour(a.get("dateActe")))
    ]
    return min(jours) if jours else None


def scrutins_et_49_3(dossier: dict[str, Any]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """`(scrutins AN, voteRefs non reconnus, engagements 49.3)` du dossier.

    Les scrutins sont ceux que la source rattache elle-même au dossier
    (`voteRefs` des actes de l'Assemblée), en clé du corpus. Jamais ceux qu'un
    rapprochement de date et de titre lui prête (`scrutins_dossiers.json`
    porte les deux, sous `provenance`).
    """
    cles: list[str] = []
    non_reconnus: list[str] = []
    engagements: list[dict[str, Any]] = []
    for acte in iter_actes(dossier.get("actesLegislatifs")):
        if not est_acte_an(acte.get("codeActe")):
            continue
        fam = _fam_code(acte)
        if fam in ISSUE_49_3_PAR_FAM_CODE:
            # §2 règle 4 : un fait de procédure, jamais un vote. Aucune
            # référence de scrutin ne lui est rattachée.
            engagements.append({
                "date": _jour(acte.get("dateActe")),
                "issue": ISSUE_49_3_PAR_FAM_CODE[fam],
                "acte_uid": acte.get("uid"),
                "code_acte": acte.get("codeActe"),
            })
            continue
        for ref in _vote_refs(acte):
            cle = cle_depuis_uid(ref)
            cible = cles if cle else non_reconnus
            valeur = cle or ref
            if valeur not in cible:
                cible.append(valeur)
    return cles, non_reconnus, engagements


# ── Les auteurs, lus dans AMO30 ───────────────────────────────────────────────

def _texte(valeur: Any) -> Optional[str]:
    if isinstance(valeur, dict):
        if valeur.get("@xsi:nil") in ("true", True):
            return None
        valeur = valeur.get("#text")
    return valeur if isinstance(valeur, str) and valeur.strip() else None


def construire_referentiel(zip_path: Path) -> dict[str, Any]:
    """Ce qu'il faut d'AMO30 pour nommer un auteur : `{acteurs, organes}`.

    - `acteurs` : `{acteurRef: {nom, mandats: {mandatRef: typeOrgane},
      groupes: [[typeOrgane, organeRef, debut, fin], …]}}` ;
    - `organes` : `{organeRef: {sigle, libelle_abrege, nom, type}}` pour tous
      les organes. Les deux abréviations de la source, parce qu'aucune ne
      suffit : `libelleAbrev` (`sigle`) distingue `SOC` de `SOC-A`
      (`an_roster.construire_index_gp`) mais code un groupe du Sénat en
      `UMPPO` ; `libelleAbrege` dit « Les Républicains » mais confond les deux
      `SOC` de la XVIe.

    Fonction pure vis-à-vis du réseau : elle ne lit qu'un fichier local.
    """
    acteurs: dict[str, dict[str, Any]] = {}
    organes: dict[str, dict[str, Optional[str]]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for nom in zf.namelist():
            if not nom.endswith(".json"):
                continue
            est_acteur = nom.startswith("json/acteur/")
            if not est_acteur and not nom.startswith("json/organe/"):
                continue
            try:
                with zf.open(nom) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, KeyError, OSError):
                continue
            if not est_acteur:
                organe = data.get("organe") if isinstance(data, dict) else None
                ref = _texte((organe or {}).get("uid"))
                if ref:
                    organes[ref] = {
                        "sigle": _texte(organe.get("libelleAbrev")),
                        "libelle_abrege": _texte(organe.get("libelleAbrege")),
                        "nom": _texte(organe.get("libelle")),
                        "type": _texte(organe.get("codeType")),
                    }
                continue
            acteur = data.get("acteur") if isinstance(data, dict) else None
            ref = _texte((acteur or {}).get("uid"))
            if not ref:
                continue
            ident = ((acteur.get("etatCivil") or {}).get("ident")) or {}
            mandats = (acteur.get("mandats") or {}).get("mandat")
            if isinstance(mandats, dict):
                mandats = [mandats]
            par_uid: dict[str, Optional[str]] = {}
            groupes: list[list[Optional[str]]] = []
            for mandat in mandats if isinstance(mandats, list) else []:
                if not isinstance(mandat, dict):
                    continue
                type_organe = mandat.get("typeOrgane")
                uid = _texte(mandat.get("uid"))
                if uid:
                    par_uid[uid] = type_organe
                if type_organe in TYPE_GROUPE_PAR_QUALITE.values():
                    organe_ref = (mandat.get("organes") or {}).get("organeRef")
                    if isinstance(organe_ref, list):
                        organe_ref = organe_ref[0] if organe_ref else None
                    groupes.append([type_organe, _texte(organe_ref),
                                    _texte(mandat.get("dateDebut")), _texte(mandat.get("dateFin"))])
            acteurs[ref] = {
                "nom": " ".join(p for p in (_texte(ident.get("prenom")), _texte(ident.get("nom"))) if p) or None,
                "mandats": par_uid,
                "groupes": groupes,
            }
    return {"acteurs": acteurs, "organes": organes}


def charger_referentiel() -> Optional[dict[str, Any]]:
    """Le référentiel de l'archive AMO30 courante, téléchargée au besoin par le
    seul point de téléchargement du dépôt. `None` si elle n'est pas lisible :
    les auteurs sont alors publiés sans qualité, motif `referentiel_indisponible`.

    Import tardif : `candidate_profile` tire `requests` et la moitié du pipeline.
    """
    import candidate_profile  # noqa: PLC0415 — voir docstring

    zip_path = candidate_profile._ensure_acteurs_historique_zip_downloaded()
    if zip_path is None:
        return None
    try:
        return construire_referentiel(Path(zip_path))
    except (zipfile.BadZipFile, OSError) as exc:
        print(f"  [!] Archive AMO30 illisible ({zip_path}) : {exc}")
        return None


def groupe_au(acteur: dict[str, Any], type_groupe: str, jour: str,
              organes: dict[str, dict[str, Optional[str]]]) -> tuple[Optional[str], Optional[str]]:
    """L'`organeRef` du groupe de l'acteur ouvert le `jour`, ou `(None, motif)`.

    Deux mandats ouverts le même jour (une bascule datée au jour près) : le
    plus récent fait foi, celui qui s'ouvre ce jour-là.
    """
    ouverts = [
        (debut, organe_ref) for t, organe_ref, debut, fin in acteur.get("groupes") or []
        if t == type_groupe and debut and debut[:10] <= jour and (not fin or fin[:10] >= jour)
    ]
    if not ouverts:
        return None, "aucun_groupe_a_la_date"
    _debut, organe_ref = max(ouverts, key=lambda x: x[0])
    if not organe_ref or organe_ref not in organes:
        return None, "organe_introuvable"
    return organe_ref, None


def _liste(valeur: Any) -> list[Any]:
    if isinstance(valeur, dict):
        return [valeur]
    return valeur if isinstance(valeur, list) else []


def _sous_liste(bloc: Any, cle: str) -> list[Any]:
    """`bloc[cle]` en liste, que la source écrive un objet ou une liste."""
    return _liste(bloc.get(cle)) if isinstance(bloc, dict) else []


def qualite_de(acteur: dict[str, Any], mandat_ref: Optional[str],
               referentiel: Optional[dict[str, Any]]) -> tuple[Optional[str], Optional[str]]:
    """`(qualité, None)` ou `(None, motif)` : ce que le mandat cité fait de l'auteur."""
    if referentiel is None:
        return None, "referentiel_indisponible"
    if not mandat_ref:
        return None, "sans_mandat_ref"
    mandats = acteur.get("mandats") or {}
    if mandat_ref not in mandats:
        return None, "mandat_introuvable"
    qualite = QUALITE_PAR_TYPE_MANDAT.get(mandats[mandat_ref] or "")
    return (qualite, None) if qualite else (None, "type_mandat_inconnu")


def auteurs(dossier: dict[str, Any], referentiel: Optional[dict[str, Any]],
            jour_depot: Optional[str]) -> dict[str, Any]:
    """`initiateurs`, `initiateurs_non_resolus` et `organes_initiateurs`.

    Un auteur est publié par ses références — `acteur_ref`, `mandat_ref`,
    `groupe_ref` —, et les noms une fois par fichier (`acteurs`, `organes`) :
    répétés sur chaque ligne, ils faisaient 6 des 16 Mo du fichier.
    `non_resolu` dit pourquoi `qualite` ou `groupe_ref` est `null`, et vaut
    `null` quand les deux sont résolus.
    """
    initiateur = dossier.get("initiateur")
    acteurs_ref = referentiel["acteurs"] if referentiel else {}
    organes = referentiel["organes"] if referentiel else {}

    organes_initiateurs: list[str] = []
    for entree_organe in _sous_liste((initiateur or {}).get("organes") if isinstance(initiateur, dict) else None, "organe"):
        organe_ref = entree_organe.get("organeRef") if isinstance(entree_organe, dict) else None
        ref = _texte(organe_ref.get("uid")) if isinstance(organe_ref, dict) else _texte(organe_ref)
        if ref and ref not in organes_initiateurs:
            organes_initiateurs.append(ref)

    lignes = []
    vus: set[str] = set()
    for entree_acteur in _sous_liste((initiateur or {}).get("acteurs") if isinstance(initiateur, dict) else None, "acteur"):
        if not isinstance(entree_acteur, dict):
            continue
        ref = _texte(entree_acteur.get("acteurRef"))
        if not ref or ref in vus:
            continue
        vus.add(ref)
        mandat_ref = _texte(entree_acteur.get("mandatRef"))
        acteur = acteurs_ref.get(ref) or {}
        qualite, motif_qualite = qualite_de(acteur, mandat_ref, referentiel)
        groupe_ref = motif_groupe = None
        if qualite is None:
            motif_groupe = "qualite_non_resolue"
        elif qualite not in TYPE_GROUPE_PAR_QUALITE:
            motif_groupe = "qualite_sans_groupe"
        elif not jour_depot:
            motif_groupe = "date_depot_absente"
        else:
            groupe_ref, motif_groupe = groupe_au(acteur, TYPE_GROUPE_PAR_QUALITE[qualite], jour_depot, organes)
        non_resolu = {k: v for k, v in (("qualite", motif_qualite), ("groupe", motif_groupe)) if v}
        lignes.append({
            "acteur_ref": ref,
            "mandat_ref": mandat_ref,
            "qualite": qualite,
            "groupe_ref": groupe_ref,
            "non_resolu": non_resolu or None,
        })

    if lignes:
        motif = None
    elif organes_initiateurs:
        motif = "initiative_d_organe"
    else:
        motif = "sans_initiateur"
    return {
        "initiateurs": lignes or None,
        "initiateurs_non_resolus": {"motif": motif} if motif else None,
        "organes_initiateurs": organes_initiateurs or None,
    }


# ── La ligne publiée ──────────────────────────────────────────────────────────

def entree(dossier: dict[str, Any], referentiel: Optional[dict[str, Any]],
           types_scrutin: dict[str, Optional[str]]) -> dict[str, Any]:
    """L'enregistrement publié d'un dossier."""
    titre_dossier = dossier.get("titreDossier") or {}
    procedure = dossier.get("procedureParlementaire") or {}
    jour_depot = jour_du_depot(dossier)
    statut, _sort_49_3, warning = _determine_statut(dossier.get("uid") or "", dossier.get("actesLegislatifs"))
    etapes, _sans = etapes_an(dossier)
    adoption, motif_adoption = derniere_adoption_an(dossier)
    scrutins, non_reconnus, engagements = scrutins_et_49_3(dossier)
    hors_corpus = [c for c in scrutins if c not in types_scrutin]
    ligne: dict[str, Any] = {
        "legislature": dossier.get("legislature"),
        "titre": titre_dossier.get("titre"),
        "source_url": _source_url(dossier.get("legislature"), titre_dossier.get("titreChemin")),
        "nature": nature_texte_depose(dossier),
        "procedure": procedure.get("libelle"),
        "date_depot": jour_depot,
        "chambre_depot": chambre_premiere_lecture(dossier),
    }
    ligne.update(auteurs(dossier, referentiel, jour_depot))
    ligne.update({
        # Le sort du texte aujourd'hui, `gouvernement_textes._determine_statut`
        # (`schema_gouvernement.KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`) : la même
        # lecture que celle des fiches de gouvernement et de `scrutins_dossiers`.
        "statut": statut,
        "statut_non_resolu": {"motif": "fam_code_inconnu"} if statut is None and warning else None,
        "etape_an": etapes,
        # #1320, même fonction que `textes_promulgues.py`.
        "derniere_adoption_an": adoption,
        "derniere_adoption_an_non_resolue": {"motif": motif_adoption} if motif_adoption else None,
        "scrutins_an": scrutins,
        "scrutins_solennels": [c for c in scrutins if types_scrutin.get(c) == TYPE_SCRUTIN_SOLENNEL],
        # Les scrutins que la source cite et que le corpus ne publie pas : leur
        # type n'est pas lu, donc « pas solennel » ne se dit pas pour eux.
        "scrutins_absents_du_corpus": hors_corpus or None,
        "vote_refs_non_reconnus": non_reconnus or None,
        "engagements_49_3": engagements,
    })
    return ligne


def construire_table(archives: list[tuple[int, Path]], referentiel: Optional[dict[str, Any]],
                     types_scrutin: dict[str, Optional[str]]) -> dict[str, dict[str, Any]]:
    """`{uid de dossier: entrée}` pour tous les dossiers des archives."""
    table: dict[str, dict[str, Any]] = {}
    for _legislature, dossier in iter_dossiers_bruts(archives):
        uid = dossier.get("uid")
        if isinstance(uid, str) and uid:
            table[uid] = entree(dossier, referentiel, types_scrutin)
    return dict(sorted(table.items()))


# ── Le découpage par législature ──────────────────────────────────────────────

def legislatures_du_dossier(ligne: dict[str, Any]) -> list[str]:
    """Les fichiers où la ligne paraît : sa législature, et chaque législature
    où l'Assemblée a agi sur elle (`etape_an`).

    UN DOSSIER PEUT PARAÎTRE DANS DEUX FICHIERS, ET C'EST VOULU. Un projet de
    loi déposé en XVe et débattu en XVIe appartient aux deux fiches de
    législature ; le ranger sous la seule XVe obligerait la fiche XVIe à charger
    tous les fichiers pour trouver ce qu'elle a débattu. Les deux copies sont
    écrites par le même run, depuis la même ligne : elles ne peuvent pas
    diverger. Mesuré le 22/10/2026 : 252 des 14 377 dossiers paraissent dans
    plus d'un fichier, la plupart des textes des législatures anciennes que
    l'Assemblée a continué d'enregistrer.
    """
    legislatures = {str(ligne["legislature"])} if ligne.get("legislature") else set()
    legislatures |= set(ligne.get("etape_an") or {})
    return sorted(legislatures, key=int)


def references_citees(lignes: Iterable[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """`(acteurs, organes)` que des lignes citent."""
    acteurs: set[str] = set()
    organes: set[str] = set()
    for ligne in lignes:
        for auteur in ligne.get("initiateurs") or []:
            acteurs.add(auteur["acteur_ref"])
            if auteur.get("groupe_ref"):
                organes.add(auteur["groupe_ref"])
        organes.update(ligne.get("organes_initiateurs") or [])
    return acteurs, organes


def chemin_fichier(repertoire: Path, legislature: str) -> Path:
    return Path(repertoire) / f"{legislature}.json"


def _lire_existant(chemin: Path) -> dict[str, Any]:
    """Le fichier publié, ou `{}` — un fichier illisible ne fait pas échouer."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return publie if isinstance(publie, dict) else {}


def ecrire(repertoire: Path, collectee: dict[str, dict[str, Any]],
           referentiel: Optional[dict[str, Any]], *, fusion: bool = True) -> dict[str, int]:
    """Écrit un fichier par législature, et rend `{législature: lignes}`.

    Additif : chaque fichier part de ce qu'il publiait, ses lignes revues ce run
    sont remplacées, les autres conservées — avec les noms qu'il portait pour
    elles.
    """
    par_legislature: dict[str, dict[str, dict[str, Any]]] = {}
    for uid, ligne in collectee.items():
        for legislature in legislatures_du_dossier(ligne):
            par_legislature.setdefault(legislature, {})[uid] = ligne
    if fusion and Path(repertoire).is_dir():
        for chemin in Path(repertoire).glob("*.json"):
            par_legislature.setdefault(chemin.stem, {})

    noms_acteurs = {r: a.get("nom") for r, a in (referentiel or {}).get("acteurs", {}).items()}
    noms_organes = (referentiel or {}).get("organes", {})
    comptes: dict[str, int] = {}
    for legislature, lignes in sorted(par_legislature.items(), key=lambda kv: int(kv[0])):
        chemin = chemin_fichier(repertoire, legislature)
        existant = _lire_existant(chemin) if fusion else {}
        dossiers = dict(existant.get("dossiers") or {})
        dossiers.update(lignes)
        if not dossiers:
            continue
        acteurs_cites, organes_cites = references_citees(dossiers.values())
        anciens_acteurs = existant.get("acteurs") or {}
        anciens_organes = existant.get("organes") or {}
        ecrire_index_json(
            chemin,
            {
                "schema_version": SCHEMA_VERSION,
                "legislature": legislature,
                "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "licence_donnees": LICENCE_AN,
                "source_url_acteurs": _url_amo30(),
                # Les noms, une fois par fichier. Un nom absent du référentiel
                # lu ce run garde celui que le fichier publiait.
                "acteurs": {r: noms_acteurs.get(r) or anciens_acteurs.get(r) for r in sorted(acteurs_cites)},
                "organes": {r: _organe_publie(noms_organes.get(r)) or anciens_organes.get(r)
                            for r in sorted(organes_cites)},
                "dossiers": dict(sorted(dossiers.items())),
            },
            dumps_ligne,
        )
        comptes[legislature] = len(dossiers)
    return comptes


def _organe_publie(organe: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not organe:
        return None
    return {"sigle": organe.get("sigle"), "libelle_abrege": organe.get("libelle_abrege"),
            "nom": organe.get("nom"), "type": organe.get("type")}


def _url_amo30() -> str:
    import candidate_profile  # noqa: PLC0415 — import tardif, voir charger_referentiel

    return candidate_profile.AN_ACTEURS_HISTORIQUE_ZIP_URL


def charger_types_scrutin(chemin: Path) -> dict[str, Optional[str]]:
    """`{clé de scrutin: type_scrutin}` du corpus publié, ou `{}`."""
    publie = _lire_existant(chemin)
    return {s["id"]: s.get("type_scrutin") for s in publie.get("scrutins") or []
            if isinstance(s, dict) and s.get("id")}


def resume(table: dict[str, dict[str, Any]]) -> Iterable[str]:
    """Les lignes du compte rendu, chaque compte avec sa population."""
    total = len(table)
    sans_titre = sum(1 for v in table.values() if not v.get("titre"))
    initiateurs = [i for v in table.values() for i in v.get("initiateurs") or []]
    sans_qualite = sum(1 for i in initiateurs if not i.get("qualite"))
    yield f"  ✓ {total} dossier(s) collecté(s) à ce run"
    yield f"      sans titre : {sans_titre} sur {total}"
    yield f"      auteurs nommés : {len(initiateurs)}, dont {sans_qualite} sans qualité résolue"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--out", default=str(DEFAUT_REPERTOIRE),
                        help=f"Répertoire à écrire, un fichier par législature (défaut : {DEFAUT_REPERTOIRE}).")
    parser.add_argument("--scrutins", default=str(DEFAUT_SCRUTINS),
                        help="Corpus des scrutins, pour reconnaître un vote solennel "
                             f"(défaut : {DEFAUT_SCRUTINS}).")
    parser.add_argument("--no-merge", action="store_true",
                        help="Reconstruction complète au lieu d'une fusion additive.")
    args = parser.parse_args(argv)

    types_scrutin = charger_types_scrutin(Path(args.scrutins))
    if not types_scrutin:
        print(f"  [!] {args.scrutins} illisible ou absent : tous les scrutins cités sont "
              "déclarés absents du corpus.")
    try:
        archives = ensure_dossiers_zips_downloaded()
    except Exception as exc:  # noqa: BLE001 — une source absente est nommée, pas fatale
        print(f"  [!] Archives de dossiers indisponibles ({exc}) : aucun dossier collecté.")
        archives = []
    referentiel = charger_referentiel() if archives else None
    if archives and referentiel is None:
        print("  [!] AMO30 indisponible : les auteurs sont publiés sans qualité ni groupe "
              "(`referentiel_indisponible`).")
    collectee = construire_table(archives, referentiel, types_scrutin) if archives else {}
    if not collectee:
        print("  [!] Aucun dossier collecté à ce run : les fichiers publiés sont conservés.")
        return 0
    for ligne in resume(collectee):
        print(ligne)
    comptes = ecrire(Path(args.out), collectee, referentiel, fusion=not args.no_merge)
    for legislature, n in comptes.items():
        print(f"      {chemin_fichier(Path(args.out), legislature)} : {n} dossier(s)")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
