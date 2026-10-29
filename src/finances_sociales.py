#!/usr/bin/env python3
"""D'où viennent les fonds des caisses sociales, et ce qu'elles versent (#1053).

Le budget de l'État, que lit `finances_etat.py`, ne porte ni la Sécurité
sociale, ni les retraites, ni l'assurance chômage : elles ont leurs propres
comptes. Ce module lit ce que deux portails en publient sous **Licence Ouverte
2.0**, et l'écrit tel quel sous `raw_data/finances_sociales.json`. Rien n'y est
agrégé par gouvernement : l'unité est **l'année civile**, et tout est annuel.

## Ce que ce module lit

Trois parties, lues et gardées séparément :

- `protection_sociale` — le classeur des comptes de la protection sociale du
  service statistique du ministère de la Santé (Drees) : pour l'ensemble des
  régimes depuis 1959, et sur les dernières années pour chacun des quatre
  blocs qui le composent (administrations de sécurité sociale, administrations
  publiques centrales et locales, sociétés, instituts sans but lucratif), les
  emplois et les ressources par nature
  (cotisations d'employeurs, de salariés, impôts et taxes affectés,
  contributions publiques…) ;
- `prestations_par_regime` — le même jeu, par son API : le total des
  prestations que verse chaque régime (caisses nationales, Unédic, retraites
  complémentaires…), par année ;
- `assurance_chomage` — le jeu de l'Unédic : ses recettes par origine et ses
  dépenses par poste, depuis 2011.

Les montants sont en **millions d'euros**, comme les deux sources les donnent.
Les libellés sont ceux de la source, mot pour mot.

## Ce que la source ne donne pas

**Les ressources caisse par caisse** — vieillesse, maladie, famille, retraites
complémentaires — ne sont dans aucun des trois : le classeur les donne par bloc,
et son bloc des caisses les réunit toutes sans les séparer, l'API ne porte que des prestations. Seule l'assurance
chômage a les deux côtés. Mesuré le 12/10/2026 ; rien n'est déduit pour combler.

## Les pièges, payés en mesurant

1. **Le classeur change de nom à chaque édition** (« … de 1959 à 2024.xlsx »),
   et son identifiant de pièce jointe avec lui. Il est donc retrouvé dans la
   fiche du jeu, par son type, jamais par une adresse écrite ici ; ses feuilles
   le sont par la forme de leur nom.
2. **La dernière année est provisoire et moins détaillée.** En 2024 les trois
   cotisations effectives tiennent sur la seule ligne « employeurs », les deux
   autres sont vides. Le statut de chaque année (« DEF », « SD », « PROV ») est
   gardé à côté des valeurs ; une cellule vide reste `null` (§2 règle 5).
3. **Les prestations par régime ne sont complètes que depuis 1990.** Avant
   1981 la source ne donne que l'ensemble ; de 1981 à 1989 la somme de ses
   régimes est en dessous de son total. Rien n'est corrigé : les lignes sont
   gardées telles quelles, et c'est au lecteur de ce fichier de ne pas
   additionner des régimes avant 1990.
4. **Le serveur compresse sans le dire**, comme celui du ministère de
   l'Économie : `decoder()` et `_octets()` regardent les premiers octets.

Usage :

    python3 src/finances_sociales.py
"""

from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from finances_etat import FinancesIndisponibles, _appel_reseau, charger, decoder  # noqa: E402
from licences import LICENCE_FINANCES_SOCIALES  # noqa: E402

CHEMIN_PAR_DEFAUT = Path("raw_data") / "finances_sociales.json"
SCHEMA_VERSION = "finances-sociales-v1"
UNITE = "millions d'euros"

PORTAIL_DREES = "https://data.drees.solidarites-sante.gouv.fr"
JEU_DREES = "305_les-comptes-de-la-protection-sociale"
PORTAIL_UNEDIC = "https://data.unedic.org"
JEU_UNEDIC = "financement-de-l-assurance-chomage"

_API = "{portail}/api/explore/v2.1/catalog/datasets/{jeu}"
_FICHE = "{portail}/explore/dataset/{jeu}/"

URL_JEU_DREES = _API.format(portail=PORTAIL_DREES, jeu=JEU_DREES)
#: Le total de chaque régime, toutes prestations confondues : le niveau 0 de la
#: nomenclature des prestations. Les niveaux plus fins ne sont pas lus.
URL_REGIMES = URL_JEU_DREES + "/exports/json?where=ps_niveau%3D%220%22"

#: La colonne qui nomme le régime. Elle s'appelait `nom_regime` jusqu'au
#: 22/10/2026 ; la Drees l'a renommée en retraitant le jeu le 23/10 (#1362).
COL_REGIME = "regime_nom"
URL_UNEDIC = _API.format(portail=PORTAIL_UNEDIC, jeu=JEU_UNEDIC) + "/exports/json"

TYPE_CLASSEUR = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

#: Les cinq feuilles lues, reconnues à la forme de leur nom : la première porte
#: ses bornes (« opérations_1959_2024 ») et les change à chaque édition.
FEUILLES = {
    "ensemble_des_regimes": re.compile(r"^opérations_\d{4}_\d{4}$"),
    "administrations_de_securite_sociale": re.compile(r"^opérations_ASSO$"),
    "administrations_publiques_centrales_et_locales": re.compile(r"^opérations_APUC_APUL$"),
    "societes_financieres_et_non_financieres": re.compile(r"^opérations_SF_SNF$"),
    "instituts_sans_but_lucratif": re.compile(r"^opérations_ISBLSM$"),
}
#: Le champ qui vaut la somme des quatre autres, les blocs de la comptabilité
#: nationale : c'est ce qui relie chaque ressource au bloc qui la reçoit.
ENSEMBLE = "ensemble_des_regimes"
TOTAL_RESSOURCES = "TOTAL DES RESSOURCES HORS TRANSFERTS"
TOTAL_EMPLOIS = "TOTAL DES EMPLOIS HORS TRANSFERTS"

#: Écart toléré, en millions d'euros, entre un total et la somme de ses lignes :
#: la source arrondit chaque ligne.
TOLERANCE = 2.0

#: Sous ces nombres, la réponse n'est pas le jeu : un champ déplacé rendrait une
#: liste courte, qui se publierait comme un constat (§2 règle 5).
PLANCHER_REGIMES = 1000
PLANCHER_CHOMAGE = 10

PARTIES = ("protection_sociale", "prestations_par_regime", "assurance_chomage")


# ── Le classeur ─────────────────────────────────────────────────────────────

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _octets(contenu: bytes) -> bytes:
    """Les octets du fichier, décompressés si le serveur les a rendus en gzip."""
    return gzip.decompress(contenu) if contenu[:2] == b"\x1f\x8b" else contenu


def lire_classeur(contenu: bytes) -> dict[str, list[dict[str, Optional[str]]]]:
    """Les feuilles d'un `.xlsx`, chacune en liste de lignes `{colonne: texte}`.

    Bibliothèque standard seule : le classeur est une archive de XML, et il n'y
    a ici ni formule ni date à interpréter.
    """
    try:
        archive = zipfile.ZipFile(io.BytesIO(_octets(contenu)))
    except zipfile.BadZipFile as erreur:
        raise FinancesIndisponibles(f"classeur illisible : {erreur}") from erreur
    noms = set(archive.namelist())
    chaines: list[str] = []
    if "xl/sharedStrings.xml" in noms:
        racine = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
        chaines = ["".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t"))
                   for si in racine.findall("m:si", _NS)]
    liens = {rel.get("Id"): rel.get("Target") for rel in ElementTree.fromstring(
        archive.read("xl/_rels/workbook.xml.rels")).findall("p:Relationship", _NS)}
    feuilles: dict[str, list[dict[str, Optional[str]]]] = {}
    for feuille in ElementTree.fromstring(archive.read("xl/workbook.xml")).iter(f"{{{_NS['m']}}}sheet"):
        cible = liens.get(feuille.get(f"{{{_NS['r']}}}id")) or ""
        chemin = cible.lstrip("/") if cible.startswith("/") else "xl/" + cible
        if chemin not in noms:
            continue
        lignes = []
        for rang in ElementTree.fromstring(archive.read(chemin)).iter(f"{{{_NS['m']}}}row"):
            ligne: dict[str, Optional[str]] = {}
            for cellule in rang.findall("m:c", _NS):
                colonne = re.sub(r"\d", "", cellule.get("r") or "")
                valeur = cellule.find("m:v", _NS)
                if valeur is not None and valeur.text is not None:
                    texte = chaines[int(valeur.text)] if cellule.get("t") == "s" else valeur.text
                else:
                    texte = "".join(t.text or "" for t in cellule.iter(f"{{{_NS['m']}}}t")) or None
                ligne[colonne] = texte
            lignes.append(ligne)
        feuilles[feuille.get("name") or ""] = lignes
    return feuilles


def lire_operations(lignes: list[dict[str, Optional[str]]], quoi: str) -> dict[str, Any]:
    """Une feuille « opérations » : ses lignes, et le statut de chaque année.

    L'en-tête porte l'année collée à son statut (« 2023SD », « 2024PROV »). Les
    lignes de note (« * … », « Source : … ») ne sont pas des données.
    """
    entete = next((l for l in lignes
                   if sum(bool(re.fullmatch(r"\d{4}[A-Z]*", v or "")) for v in l.values()) >= 3), None)
    if entete is None:
        raise FinancesIndisponibles(f"{quoi} : aucune ligne d'années")
    annees = {c: re.fullmatch(r"(\d{4})([A-Z]*)", v).groups()
              for c, v in entete.items() if v and re.fullmatch(r"\d{4}[A-Z]*", v)}
    sortie = []
    for ligne in lignes[lignes.index(entete) + 1:]:
        libelle = (ligne.get("A") or "").strip()
        if not libelle or libelle.startswith(("*", "Source")):
            continue
        valeurs = {}
        for colonne, (an, _) in annees.items():
            brut = ligne.get(colonne)
            valeurs[an] = round(float(brut), 2) if brut not in (None, "") else None
        sortie.append({"libelle": libelle.rstrip(" *"), "valeurs": valeurs})
    _verifier_totaux(sortie, quoi)
    return {"statuts": {an: statut or None for an, statut in sorted(annees.values())},
            "lignes": sortie}


def _verifier_totaux(lignes: list[dict[str, Any]], quoi: str) -> None:
    """Le total des ressources vaut la somme des lignes qui le suivent.

    C'est ce qui dit que la feuille est bien celle qu'on croit lire : une ligne
    ajoutée, retirée ou déplacée par la source rompt l'égalité.
    """
    libelles = [l["libelle"] for l in lignes]
    if TOTAL_RESSOURCES not in libelles or TOTAL_EMPLOIS not in libelles:
        raise FinancesIndisponibles(f"{quoi} : ligne de total introuvable")
    rang = libelles.index(TOTAL_RESSOURCES)
    for an, total in lignes[rang]["valeurs"].items():
        if total is None:
            continue
        somme = sum(l["valeurs"][an] or 0 for l in lignes[rang + 1:])
        if abs(total - somme) > TOLERANCE:
            raise FinancesIndisponibles(
                f"{quoi} {an} : total des ressources {total}, somme des lignes {somme:.2f}")


def _verifier_blocs(champs: dict[str, dict[str, Any]]) -> None:
    """Les quatre blocs font l'ensemble, année par année.

    La garde porte sur le total des ressources, pas sur chaque ligne : en année
    provisoire la source ne range pas les cotisations sur les mêmes lignes dans
    l'ensemble et dans les blocs (7 537 M€ en 2024, mesuré le 13/10/2026), et
    les deux écarts s'annulent.
    """
    def total(champ: str) -> dict[str, Optional[float]]:
        return next(l["valeurs"] for l in champs[champ]["lignes"] if l["libelle"] == TOTAL_RESSOURCES)

    ensemble = total(ENSEMBLE)
    blocs = [total(c) for c in champs if c != ENSEMBLE]
    for an in sorted(set.intersection(*(set(b) for b in blocs))):
        somme = sum(b[an] or 0 for b in blocs)
        if ensemble.get(an) is None or abs(ensemble[an] - somme) > TOLERANCE:
            raise FinancesIndisponibles(
                f"{an} : ensemble des régimes {ensemble.get(an)}, somme des blocs {somme:.2f}")


def lire_protection_sociale(appel: Callable[[str], bytes]) -> dict[str, Any]:
    """Le classeur, retrouvé dans la fiche du jeu, et ses cinq feuilles."""
    fiche = json.loads(decoder(appel(URL_JEU_DREES)))
    pieces = [p for p in fiche.get("attachments") or [] if p.get("mimetype") == TYPE_CLASSEUR]
    if len(pieces) != 1:
        raise FinancesIndisponibles(f"{len(pieces)} classeur(s) joint(s) au jeu, un seul attendu")
    feuilles = lire_classeur(appel(pieces[0]["url"]))
    champs = {}
    for champ, motif in FEUILLES.items():
        noms = [n for n in feuilles if motif.match(n)]
        if len(noms) != 1:
            raise FinancesIndisponibles(f"{champ} : {len(noms)} feuille(s) reconnue(s)")
        champs[champ] = {"feuille": noms[0], **lire_operations(feuilles[noms[0]], champ)}
    _verifier_blocs(champs)
    return {"source_urls": [pieces[0]["url"]], "classeur": pieces[0].get("title"),
            "fiche": _FICHE.format(portail=PORTAIL_DREES, jeu=JEU_DREES), "champs": champs}


# ── Les deux API ────────────────────────────────────────────────────────────

def lire_prestations_par_regime(appel: Callable[[str], bytes]) -> dict[str, Any]:
    """Le total des prestations de chaque régime, par année.

    Trois niveaux, gardés tous les trois : l'ensemble (0), le secteur (1), le
    régime (2). Ils se recoupent et ne s'additionnent donc pas entre eux.

    La garde porte sur les secteurs, pas sur les régimes : la source ne
    détaille rien avant 1981, et de 1981 à 1989 ses régimes ne font pas son
    total (594 à 1 282 M€ d'écart, mesuré le 12/10/2026). Depuis 1990 les trois
    niveaux se recoupent.
    """
    rangs = json.loads(decoder(appel(URL_REGIMES)))
    if not isinstance(rangs, list) or len(rangs) < PLANCHER_REGIMES:
        raise FinancesIndisponibles(
            f"prestations par régime : {len(rangs) if isinstance(rangs, list) else 0} lignes lues")
    if COL_REGIME not in rangs[0]:
        raise FinancesIndisponibles(
            f"prestations par régime : colonne {COL_REGIME!r} absente, colonnes lues "
            f"{sorted(rangs[0])}")
    annees: dict[str, list[dict[str, Any]]] = {}
    for rang in rangs:
        if rang.get("ps_niveau") != "0":
            raise FinancesIndisponibles("prestations par régime : le filtre de niveau n'a pas été appliqué")
        annees.setdefault(str(rang["annee"]), []).append({
            "niveau": int(rang["si_niveau"]), "secteur_code": rang["si_code"],
            "secteur": rang["si_nom"], "regime": rang[COL_REGIME], "montant": rang.get("val")})
    for an, liste in annees.items():
        liste.sort(key=lambda r: (r["secteur_code"], r["niveau"], r["regime"]))
        ensemble = [r["montant"] for r in liste if r["niveau"] == 0]
        secteurs = [r["montant"] or 0 for r in liste if r["niveau"] == 1]
        if len(ensemble) != 1 or (secteurs and abs(ensemble[0] - sum(secteurs)) > TOLERANCE):
            raise FinancesIndisponibles(
                f"prestations par régime {an} : ensemble {ensemble}, somme des secteurs {sum(secteurs):.2f}")
    return {"source_urls": [URL_REGIMES],
            "fiche": _FICHE.format(portail=PORTAIL_DREES, jeu=JEU_DREES),
            "annees": dict(sorted(annees.items()))}


def lire_assurance_chomage(appel: Callable[[str], bytes]) -> dict[str, Any]:
    """Les recettes et les dépenses de l'assurance chômage, champ par champ."""
    rangs = json.loads(decoder(appel(URL_UNEDIC)))
    if not isinstance(rangs, list) or len(rangs) < PLANCHER_CHOMAGE:
        raise FinancesIndisponibles(
            f"assurance chômage : {len(rangs) if isinstance(rangs, list) else 0} années lues")
    annees = {}
    for rang in rangs:
        an = str(rang.get("annee"))
        valeurs = {c: v for c, v in sorted(rang.items()) if c != "annee"}
        for cote in ("recettes", "depenses"):
            total = valeurs.get(cote + "_total")
            somme = sum(v or 0 for c, v in valeurs.items()
                        if c.startswith(cote + "_") and c != cote + "_total")
            if total is None or abs(total - somme) > TOLERANCE:
                raise FinancesIndisponibles(
                    f"assurance chômage {an} : {cote} {total}, somme des lignes {somme}")
        annees[an] = valeurs
    return {"source_urls": [URL_UNEDIC],
            "fiche": _FICHE.format(portail=PORTAIL_UNEDIC, jeu=JEU_UNEDIC),
            "annees": dict(sorted(annees.items()))}


LECTEURS: dict[str, Callable[[Callable[[str], bytes]], dict[str, Any]]] = {
    "protection_sociale": lire_protection_sociale,
    "prestations_par_regime": lire_prestations_par_regime,
    "assurance_chomage": lire_assurance_chomage,
}


# ── La collecte ─────────────────────────────────────────────────────────────

def collecter(existant: dict[str, Any], appel: Callable[[str], bytes]) -> dict[str, Any]:
    """Le document à écrire, composé de l'existant et de ce qui a été relu.

    Une partie en échec **n'écrase jamais** celle déjà publiée ; sans rien de
    publié elle vaut `null`, à côté de son `*_non_resolu` (§2 règle 5).
    """
    document: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "genere_le": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "licence_donnees": LICENCE_FINANCES_SOCIALES,
        "unite": UNITE,
    }
    echecs: list[str] = []
    for partie in PARTIES:
        try:
            document[partie] = LECTEURS[partie](appel)
        except (FinancesIndisponibles, OSError, ValueError, KeyError, IndexError,
                TypeError, AttributeError, ElementTree.ParseError) as erreur:
            echecs.append(f"{partie} : {erreur}")
            document[partie] = existant.get(partie)
            if document[partie] is None:
                document[partie + "_non_resolu"] = {"raison": str(erreur), "a_retenter": True}
    document["echecs"] = echecs
    return document


def resume(document: dict[str, Any]) -> list[str]:
    """Ce que le document porte, une ligne par partie — pour le journal du run."""
    lignes = []
    for champ, bloc in ((document.get("protection_sociale") or {}).get("champs") or {}).items():
        ans = sorted(bloc["statuts"])
        lignes.append(f"protection sociale, {champ} : {len(bloc['lignes'])} lignes, de {ans[0]} à {ans[-1]}")
    for partie in ("prestations_par_regime", "assurance_chomage"):
        ans = sorted((document.get(partie) or {}).get("annees") or {})
        if ans:
            lignes.append(f"{partie} : de {ans[0]} à {ans[-1]}")
    for partie in PARTIES:
        if document.get(partie) is None:
            lignes.append(f"{partie} : absent ({(document.get(partie + '_non_resolu') or {}).get('raison')})")
    return lignes


def main(argv: Optional[list[str]] = None) -> int:
    analyseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analyseur.add_argument("--sortie", type=Path, default=CHEMIN_PAR_DEFAUT)
    args = analyseur.parse_args(argv)

    from json_io import dumps_indente, ecrire_index_json

    document = collecter(charger(args.sortie), _appel_reseau)
    echecs = document.pop("echecs")
    ecrit = ecrire_index_json(args.sortie, document, dumps_indente)
    for ligne in resume(document):
        print(ligne)
    print(f"{args.sortie} : {'écrit' if ecrit else 'inchangé'}")
    for echec in echecs:
        print(f"ÉCHEC — {echec}", file=sys.stderr)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
