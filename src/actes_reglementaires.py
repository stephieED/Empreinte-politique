#!/usr/bin/env python3
"""actes_reglementaires.py — les décrets, arrêtés et ordonnances du Journal
officiel, et un index de mots pour les retrouver (#1029, voie 1).

## Le besoin

Extraire d'un mot-clé ce que le corpus porte sur un sujet. Une mesure peut
passer par trois voies (#1029) ; la première est l'**acte réglementaire**, ce
que l'exécutif prend seul — et le corpus n'en voyait aucun. « Carburant »
rendait 0 texte porté, alors que le décret n° 2026-333 crée une indemnité
carburant et que trois arrêtés en fixent les dates.

## Ce qui est collecté, et ce qui ne l'est pas

La DILA publie le fonds du Journal officiel (`echanges.dila.gouv.fr`, Licence
Ouverte) : un **dump global** livré une seule fois le 13/07/2025, qui remonte à
1861, puis une **livraison par jour**. On retient les natures `DECRET`,
`ARRETE` et `ORDONNANCE` publiées depuis le 01/01/2007 — la borne basse des
fiches de gouvernement publiées, arbitrée le 22/09/2026.

**Rien n'est rattaché à une personne.** `<AUTORITE>` — le signataire — est vide
sur les 380 décrets de la fenêtre mesurée par #664 : la source ne le publie
pas. Un acte se rattache à un gouvernement par sa **date de publication** et à
un ministère par `<MINISTERE>`, l'organe et jamais la personne. « N décrets
signés » n'est donc pas constructible, et c'est la source qui ferme ce piège.

## Ce qui est publié : un index de mots, pas le texte des actes

Même fabrique que la voie 2 (`amendements_contenu`) : les mots du titre et de
tous les articles, minuscules, sans accents, 4 lettres ou plus, ramenés à leur
forme de base quand elle existe dans l'index, et écartés au-delà de
`SEUIL_FREQUENCE` des actes du mois. Le texte entier reste chez Légifrance, que
l'`ID_ELI` de chaque acte permet d'ouvrir.

Mesuré le 22/09/2026 sur le dump global et les 800 livraisons du 13/07/2025 au
22/09/2026 : **389 397 actes** depuis 2007 (311 727 arrêtés, 76 664 décrets,
1 006 ordonnances), 2 368 125 articles lus. Découpé par mois : ~124 Mo d'index
de mots et ~86 Mo de métadonnées. 1 184 actes portent « carbur… ».

## Le lien vers une loi, et pourquoi il se corrige après coup

Chaque acte publie, quand la source les pose, les lois qu'il **applique** et
celles qu'il **cite** (`liens_lois`, par identifiant `JORFTEXT`) : la source
distingue les deux, et un décret qui cite une loi en visa n'en est pas un décret
d'application (§2 règle 2). Un acte sans lien n'est **pas** un acte pris sans
loi : la qualification est un travail éditorial différé chez Légifrance.

C'est ce différé qui impose `corriger_les_liens` : un mois clos n'est jamais
reconstruit, mais la source **redélivre** un acte quand ses liens changent, et
cette redélivrance arrive dans les livraisons que le run lit déjà. Seuls les
liens de l'acte sont alors repris dans le fichier de son mois — jamais le reste
de sa ligne, dont l'index de mots ne serait plus d'accord avec un titre relu.
Sans ce chemin, un acte de 2026 resterait « aucun lien déclaré » pour toujours,
et la figure qui le lit mesurerait la chaîne de publication au lieu de l'action
publique. Arbitré le 23/09/2026.

## Un fichier par MOIS de publication, et pourquoi

`pivot_data/actes_reglementaires/<AAAA-MM>.json`. Un mois clos ne change plus :
un run ne relit que les livraisons des `MOIS_RELUS` derniers mois, et ne
réécrit que ces fichiers-là. C'est ce qui borne à la fois le temps du run et la
croissance de l'historique git. Un découpage par année pèserait 40 Mo de moins,
mais un run de décembre relirait 1,8 Go de livraisons pour reconstruire l'année
en cours (arbitré le 22/09/2026).

Le fichier :

```
{schema_version, mois, genere_le, licence_donnees, borne_basse,
 seuil_frequence, fusion_des_formes, derniere_livraison, liens_revus_le,
 prefixe_ids: "JORFTEXT", natures: [...], ministeres: [...],
 liens_lois: {"000054861441": [[lois appliquées], [lois citées]], ...},
 ids: ["000054861441", ...],
 actes: [[rang de nature, titre, date_publi, rang de ministère | null, nor, num | null], ...],
 mots: {mot: "<renvois>"}}
```

`liens_lois` ne porte que les actes qui ont au moins un lien : une clé absente
est un acte **sans lien déclaré**, pas un acte sans loi. `liens_revus_le` dit le
jour où une redélivrance a corrigé ces liens.

`ids` fixe la numérotation, `actes` lui est aligné, et un renvoi est la
POSITION d'un acte dans `ids`, en écarts base 36 — la forme de
`amendements_contenu`, dont `decoder` et `forme_indexee` sont importés plutôt
que recopiés : une seule fabrique, un seul contrat de lecture.

Les actes que la source date de `2999-…` — sa date bouche-trou — ne sont rangés
dans aucun mois : ils vont dans `sans-date.json`, `mois: null`, avec leur
`date_publi` telle que la source l'écrit (§2 règle 5).

## La mémoire, et pourquoi un étalement sur disque

Les articles d'un acte sont dispersés dans le flux : les regrouper en mémoire a
coûté 4,3 Go sur les 389 397 actes, et le processus a été tué. Chaque article
est donc écrit dans l'un des `NB_SEAUX` seaux temporaires, choisi par son
identifiant d'acte — un acte tombe toujours dans le même —, puis chaque seau
est regroupé à son tour. Le pic mesuré retombe à 1 Go, et le temporaire vit
hors du dépôt et hors de `.cache/`.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import tarfile
import tempfile
import time
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from amendements_contenu import (  # noqa: E402
    NB_SEAUX,
    SEUIL_AVANT_FUSION,
    SEUIL_FREQUENCE,
    FUSION_DES_FORMES,
    _encoder,
    forme_indexee,
    hash_seau,
    mots_du_texte,
)
from json_io import ecrire_index_json  # noqa: E402
from licences import LICENCE_JORF  # noqa: E402
import lois_jorf  # noqa: E402

SCHEMA_VERSION = "actes-reglementaires-v1"

#: Le listing des livraisons DILA. Le dump global y est une entrée comme une
#: autre, sous un nom qui porte sa date de livraison.
SOURCE_LISTING = "https://echanges.dila.gouv.fr/OPENDATA/JORF/"
MOTIF_LIVRAISON = re.compile(r'href="(JORF_(\d{8})-\d+\.tar\.gz)"')
MOTIF_DUMP_GLOBAL = re.compile(r'href="(Freemium_jorf_global_\d{8}-\d+\.tar\.gz)"')

#: Les natures retenues : ce que l'exécutif prend seul. `LOI` est déjà dans le
#: corpus par l'Assemblée ; `AVIS`, `DECISION`, `ANNONCES` et les autres ne sont
#: pas des actes réglementaires.
NATURES_RETENUES: tuple[str, ...] = ("ARRETE", "DECRET", "ORDONNANCE")

#: 01/01/2007 : la borne basse des fiches de gouvernement publiées (`FILLON_2`
#: commence le 19/06/2007). Arbitré le 22/09/2026.
BORNE_BASSE = "2007-01-01"

#: La date bouche-trou de la DILA — 386 actes la portent sur le fonds depuis
#: 2007. Elle n'est pas un mois, et n'en reçoit donc pas.
ANNEE_SENTINELLE = "2999"
MOIS_SANS_DATE = "sans-date"

#: Nombre de mois relus à chaque run : le mois en cours et le précédent. Un
#: acte paraît dans la livraison du jour de sa parution au JO ou de la veille ;
#: deux mois couvrent donc tout acte qu'un mois publié pourrait encore gagner,
#: et `verifier_sans_perte` refuse de publier si ce n'était pas le cas.
MOIS_RELUS = 2

#: Marge avant le premier jour du plus ancien mois relu : une livraison de fin
#: de mois porte des actes publiés le lendemain.
MARGE_JOURS = 7

PREFIXE_IDS = "JORFTEXT"
REPERTOIRE_PUBLIE = Path("pivot_data") / "actes_reglementaires"
GABARIT_PUBLIE = "{mois}.json"

_CHAMP = {
    tag: re.compile(rf"<{tag}>(.*?)</{tag}>", re.S)
    for tag in ("ID", "CID", "NATURE", "TITREFULL", "DATE_PUBLI", "MINISTERE", "NOR", "NUM")
}
_CONTEXTE = re.compile(r'<TEXTE cid="(JORFTEXT\d+)" date_publi="([\d-]*)"[^>]*nature="([A-Z_]*)"')
_LIEN = re.compile(r"<LIEN\b[^>]*>")


def _attribut(balise: str, cle: str) -> Optional[str]:
    m = re.search(rf'{cle}="([^"]*)"', balise)
    return m.group(1) or None if m else None


def liens_vers_une_loi(xml: str) -> tuple[list[str], list[str]]:
    """`(lois appliquées, lois citées)` d'un acte, par identifiant `JORFTEXT`.

    Deux états, que la source distingue elle-même et qu'on ne confond pas :
    `typelien="APPLICATION"` — le texte d'application d'une loi —, et
    `typelien="CITATION"` — la loi est citée, en visa le plus souvent. Un décret
    qui cite une loi n'en est pas un décret d'application (§2 règle 2).

    **Un acte sans lien n'est pas un acte pris sans loi** : la source pose la
    qualification par un travail éditorial différé, et ne l'a posée sur AUCUNE
    loi promulguée depuis 2024 (`docs/sources/jorf-dila.md`). L'absence est donc
    publiée comme une absence de lien déclaré, jamais comme un fait sur l'acte.
    """
    appliquees: list[str] = []
    citees: list[str] = []
    for balise in _LIEN.findall(xml):
        if _attribut(balise, "naturetexte") not in ("LOI", "LOI_ORGANIQUE"):
            continue
        cible = _attribut(balise, "cidtexte")
        if not cible:
            continue
        typelien = _attribut(balise, "typelien")
        if typelien == "APPLICATION":
            appliquees.append(cible)
        elif typelien == "CITATION":
            citees.append(cible)
    return sorted(set(appliquees)), sorted(set(citees))
_BLOC_TEXTUEL = re.compile(r"<BLOC_TEXTUEL>(.*?)</BLOC_TEXTUEL>", re.S)


class SourceIndisponible(RuntimeError):
    """La DILA n'a pas répondu. Un index vide se lirait « aucun acte » (#510)."""


class ActesPerdus(RuntimeError):
    """Des actes déjà publiés ne sont pas dans la relecture : on ne publie pas."""


def _lire(tag: str, xml: str) -> Optional[str]:
    m = _CHAMP[tag].search(xml)
    if not m:
        return None
    valeur = m.group(1).strip()
    return valeur or None


def mois_de(date_publi: Optional[str]) -> str:
    """Le fichier où va un acte : son mois de publication, ou `sans-date`."""
    if not date_publi or date_publi[:4] == ANNEE_SENTINELLE:
        return MOIS_SANS_DATE
    return date_publi[:7]


def retenu(nature: Optional[str], date_publi: Optional[str]) -> bool:
    """Un acte réglementaire publié depuis la borne basse. Une date sentinelle
    est retenue : c'est une absence de date, pas une date hors bornes."""
    if nature not in NATURES_RETENUES:
        return False
    if not date_publi:
        return False
    return date_publi[:4] == ANNEE_SENTINELLE or date_publi >= BORNE_BASSE


def livraisons_disponibles(listing: str) -> tuple[Optional[str], list[tuple[str, str]]]:
    """`(dump global, [(nom de livraison, date AAAAMMJJ)…])`, du listing DILA."""
    dump = MOTIF_DUMP_GLOBAL.search(listing)
    vues: dict[str, str] = {}
    for nom, jour in MOTIF_LIVRAISON.findall(listing):
        vues[nom] = jour
    return (dump.group(1) if dump else None), sorted(vues.items(), key=lambda x: x[0])


def telecharger_listing(base: str = SOURCE_LISTING, *, timeout: int = 120) -> str:
    try:
        with urllib.request.urlopen(base, timeout=timeout) as reponse:
            return reponse.read().decode("utf-8", "replace")
    except OSError as exc:  # pragma: no cover - dépend du réseau
        raise SourceIndisponible(f"listing DILA injoignable : {exc}") from exc


def parcourir_archive(url: str, *, timeout: int = 300) -> Iterator[tuple[str, str]]:
    """`(nom de membre, XML)` pour chaque texte et article d'une archive, EN FLUX.

    `tarfile` en mode flux garde la fiche de chaque membre lu : sur le dump
    global (des millions de fichiers) le processus atteignait 1,5 Go avant
    d'avoir rien produit. La liste est donc vidée à chaque tour.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as reponse, \
                tarfile.open(fileobj=reponse, mode="r|gz") as archive:
            for membre in archive:
                archive.members.clear()
                if not membre.isfile() or not membre.name.endswith(".xml"):
                    continue
                if "/texte/version/" not in membre.name and "/article/" not in membre.name:
                    continue
                flux = archive.extractfile(membre)
                if flux is None:
                    continue
                yield membre.name, flux.read().decode("utf-8", "replace")
    except (OSError, tarfile.TarError) as exc:
        raise SourceIndisponible(f"{url} illisible : {exc}") from exc


class Moisson:
    """Les actes d'une collecte, et les mots de leurs articles.

    Les métadonnées tiennent en mémoire (une entrée par acte) ; les mots des
    articles passent par des seaux sur disque, parce qu'un article arrive dans
    le flux loin de l'acte auquel il appartient.
    """

    def __init__(self, repertoire: Path, *, mois_retenus: Optional[set[str]] = None) -> None:
        self.repertoire = Path(repertoire)
        self.repertoire.mkdir(parents=True, exist_ok=True)
        self.mois_retenus = mois_retenus
        self.actes: dict[str, dict[str, Any]] = {}
        #: Actes d'un mois déjà clos, redélivrés par la source : seuls leurs
        #: liens sont repris, dans les fichiers déjà publiés.
        self.redelivres: dict[str, dict[str, Any]] = {}
        #: `numéro de loi → identifiants JORFTEXT`, relevée en chemin : une loi
        #: paraît dans les mêmes livraisons que les actes, et c'est ce qui rend
        #: la table de `lois_jorf` tenable sans appel réseau de plus.
        self.lois: dict[str, list[list[str]]] = {}
        self._seaux = [open(self.repertoire / f"seau-{i:03d}.tsv", "w", encoding="utf-8")
                       for i in range(NB_SEAUX)]
        self.articles = 0

    def _garde_le_mois(self, date_publi: Optional[str]) -> bool:
        return self.mois_retenus is None or mois_de(date_publi) in self.mois_retenus

    def ajouter(self, nom: str, xml: str) -> None:
        if "/texte/version/" in nom:
            nature, date_publi = _lire("NATURE", xml), _lire("DATE_PUBLI", xml)
            if nature in lois_jorf.NATURES:
                # Une loi n'est pas un acte réglementaire : elle n'entre pas dans
                # les fichiers mensuels. Son identifiant sert à joindre les liens
                # des actes aux textes promulgués, qui ne le publient pas.
                lois_jorf.depuis_meta(self.lois, nature, _lire("NUM", xml),
                                      _lire("CID", xml) or _lire("ID", xml), date_publi)
                return
            if not retenu(nature, date_publi):
                return
            cid = _lire("CID", xml) or _lire("ID", xml)
            if not cid:
                return
            appliquees, citees = liens_vers_une_loi(xml)
            # La livraison la plus récente gagne : la DILA redélivre un texte
            # quand ses liens ou son titre changent.
            acte = {
                "nature": nature, "titre": _lire("TITREFULL", xml), "date_publi": date_publi,
                "ministere": _lire("MINISTERE", xml), "nor": _lire("NOR", xml), "num": _lire("NUM", xml),
                "lois_appliquees": appliquees, "lois_citees": citees,
            }
            if self.mois_retenus is not None and mois_de(date_publi) not in self.mois_retenus:
                # Redélivrance d'un acte d'un mois clos : on ne reconstruit pas
                # son mois — ses articles ne sont pas relus —, mais ses LIENS
                # sont à reprendre. C'est par là que la qualification tardive de
                # la source atteint le corpus.
                self.redelivres[cid] = acte
                return
            self.actes[cid] = acte
            return
        contexte = _CONTEXTE.search(xml)
        if not contexte:
            return
        cid, date_publi, nature = contexte.groups()
        if not retenu(nature, date_publi) or not self._garde_le_mois(date_publi):
            return
        bloc = _BLOC_TEXTUEL.search(xml)
        if not bloc:
            return
        mots = mots_du_texte(bloc.group(1))
        if not mots:
            return
        self._seaux[hash_seau(cid)].write(cid + "\t" + " ".join(sorted(mots)) + "\n")
        self.articles += 1

    def mots_par_acte(self) -> Iterator[tuple[str, set[str]]]:
        """`(cid, mots des articles)`, un seau à la fois."""
        for flux in self._seaux:
            flux.close()
        for i in range(NB_SEAUX):
            groupes: dict[str, set[str]] = defaultdict(set)
            with open(self.repertoire / f"seau-{i:03d}.tsv", encoding="utf-8") as flux:
                for ligne in flux:
                    cid, _, mots = ligne.rstrip("\n").partition("\t")
                    groupes[cid].update(mots.split())
            yield from groupes.items()

    def _repartir_par_mois(self) -> set[str]:
        """Range les mots de chaque acte dans le fichier de SON mois.

        Deuxième étalement, et il a la même raison que le premier : garder en
        mémoire les mots des 389 397 actes du fonds coûte 4,3 Go. Après cette
        passe, un mois se construit seul.
        """
        flux: dict[str, Any] = {}
        for cid, mots in self.mots_par_acte():
            acte = self.actes.get(cid)
            if acte is None:
                continue
            mois = mois_de(acte["date_publi"])
            if mois not in flux:
                flux[mois] = open(self.repertoire / f"mois-{mois}.tsv", "w", encoding="utf-8")
            flux[mois].write(cid + "\t" + " ".join(sorted(mots)) + "\n")
        for sortie in flux.values():
            sortie.close()
        return {mois_de(acte["date_publi"]) for acte in self.actes.values()}

    def par_mois(self) -> Iterator[tuple[str, dict[str, dict[str, Any]]]]:
        """`(mois, {cid: acte + mots})`, UN MOIS À LA FOIS.

        Un acte sans article existe — son titre porte alors seuls ses mots ; et
        un acte dont aucun mot ne passe les seuils reste publié, avec ses
        métadonnées : c'est un acte, pas une absence.
        """
        mois_vus = self._repartir_par_mois()
        par_mois: dict[str, list[str]] = defaultdict(list)
        for cid, acte in self.actes.items():
            par_mois[mois_de(acte["date_publi"])].append(cid)
        for mois in sorted(mois_vus):
            mots_lus: dict[str, set[str]] = {}
            fichier = self.repertoire / f"mois-{mois}.tsv"
            if fichier.exists():
                with open(fichier, encoding="utf-8") as flux:
                    for ligne in flux:
                        cid, _, mots = ligne.rstrip("\n").partition("\t")
                        mots_lus[cid] = set(mots.split())
            actes = {}
            for cid in par_mois[mois]:
                acte = dict(self.actes[cid])
                acte["mots"] = mots_lus.get(cid, set()) | mots_du_texte(acte.get("titre"))
                actes[cid] = acte
            yield mois, actes


def document(
    mois: str,
    actes: dict[str, dict[str, Any]],
    *,
    derniere_livraison: Optional[str] = None,
    genere_le: Optional[str] = None,
) -> dict[str, Any]:
    """Le fichier publié d'un mois (voir la docstring du module).

    Trois temps, ceux de `amendements_contenu.document` : les mots présents
    dans plus de `SEUIL_AVANT_FUSION` des actes du mois sont écartés, les
    autres sont ramenés à leur forme de base, et les formes au-delà de
    `SEUIL_FREQUENCE` sont écartées à leur tour.
    """
    ids = sorted(actes)
    total = len(ids) or 1
    brut: dict[str, set[int]] = defaultdict(set)
    for position, cid in enumerate(ids):
        for mot in actes[cid].get("mots") or ():
            brut[mot].add(position)
    vocabulaire = {mot for mot, pos in brut.items() if len(pos) <= SEUIL_AVANT_FUSION * total}
    fusion: dict[str, set[int]] = defaultdict(set)
    for mot in vocabulaire:
        fusion[forme_indexee(mot, vocabulaire)] |= brut[mot]

    ministeres = sorted({a["ministere"] for a in actes.values() if a.get("ministere")})
    rang_ministere = {m: i for i, m in enumerate(ministeres)}
    return {
        "schema_version": SCHEMA_VERSION,
        "mois": None if mois == MOIS_SANS_DATE else mois,
        "genere_le": genere_le or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "licence_donnees": LICENCE_JORF,
        "borne_basse": BORNE_BASSE,
        "seuil_frequence": SEUIL_FREQUENCE,
        "fusion_des_formes": [list(r) for r in FUSION_DES_FORMES],
        "derniere_livraison": derniere_livraison,
        "prefixe_ids": PREFIXE_IDS,
        "natures": list(NATURES_RETENUES),
        "ministeres": ministeres,
        "liens_lois": {
            cid[len(PREFIXE_IDS):]: [actes[cid].get("lois_appliquees") or [],
                                     actes[cid].get("lois_citees") or []]
            for cid in ids
            if actes[cid].get("lois_appliquees") or actes[cid].get("lois_citees")
        },
        "ids": [cid[len(PREFIXE_IDS):] for cid in ids],
        "actes": [
            [
                NATURES_RETENUES.index(actes[cid]["nature"]),
                actes[cid].get("titre"),
                actes[cid].get("date_publi"),
                rang_ministere.get(actes[cid].get("ministere")),
                actes[cid].get("nor"),
                actes[cid].get("num"),
            ]
            for cid in ids
        ],
        "mots": {
            mot: _encoder(sorted(pos)) for mot, pos in sorted(fusion.items())
            if len(pos) <= SEUIL_FREQUENCE * total
        },
    }


def corriger_les_liens(
    redelivres: dict[str, dict[str, Any]],
    repertoire: Path = REPERTOIRE_PUBLIE,
    *,
    journal=sys.stdout,
) -> list[str]:
    """Reprend les liens des actes qu'un mois CLOS a vus redélivrés.

    **Pourquoi une correction ciblée, et pas une reconstruction du mois.** La
    source pose `typelien="APPLICATION"` par un travail éditorial différé —
    aucune des 188 lois du fonds promulguées depuis 2024 n'en portait au
    23/09/2026, alors que 56 % d'entre elles étaient déjà citées par un acte.
    Un statut écrit le mois de la parution resterait donc « aucun lien déclaré »
    pour toujours, et la figure qui le lit mesurerait la chaîne de publication
    de Légifrance au lieu de l'action publique.

    Seuls les **liens** sont repris. Le reste de la ligne ne l'est pas : les
    articles de l'acte ne sont pas relus, et son index de mots ne doit pas se
    retrouver en désaccord avec un titre qui aurait changé.

    Rend les mois réécrits.
    """
    par_mois: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for cid, acte in redelivres.items():
        par_mois[mois_de(acte.get("date_publi"))][cid] = acte

    ecrits = []
    for mois, actes in sorted(par_mois.items()):
        chemin = chemin_publie(mois, repertoire)
        try:
            doc = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Un mois qu'on n'a jamais publié n'est pas corrigé : il sera
            # construit entier le jour où on le relira.
            continue
        prefixe = doc.get("prefixe_ids") or ""
        connus = set(doc.get("ids") or [])
        liens = dict(doc.get("liens_lois") or {})
        change = 0
        for cid, acte in actes.items():
            court = cid[len(prefixe):]
            if court not in connus:
                continue
            nouveaux = [acte.get("lois_appliquees") or [], acte.get("lois_citees") or []]
            ancien = liens.get(court)
            if not any(nouveaux):
                if ancien is not None:
                    # La source a RETIRÉ un lien : on le retire aussi, sans quoi
                    # le corpus publierait une qualification qu'elle ne fait plus.
                    liens.pop(court)
                    change += 1
                continue
            if ancien != nouveaux:
                liens[court] = nouveaux
                change += 1
        if not change:
            continue
        doc["liens_lois"] = dict(sorted(liens.items()))
        doc["liens_revus_le"] = time.strftime("%Y-%m-%d")
        if ecrire_index_json(chemin, doc):
            ecrits.append(mois)
            print(f"-> {chemin} : {change} acte(s) dont les liens ont changé", file=journal)
    return ecrits


def chemin_publie(mois: str, repertoire: Path = REPERTOIRE_PUBLIE) -> Path:
    return Path(repertoire) / GABARIT_PUBLIE.format(mois=mois)


def ids_publies(chemin: Path) -> set[str]:
    """Les identifiants d'un fichier déjà publié ; vide s'il n'existe pas."""
    try:
        doc = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    prefixe = doc.get("prefixe_ids") or ""
    return {prefixe + i for i in doc.get("ids") or []}


def verifier_sans_perte(mois: str, actes: dict[str, dict[str, Any]], repertoire: Path) -> None:
    """Un acte publié qui n'est pas dans la relecture ferait une perte muette.

    C'est le contrôle « collecté = publié » d'AGENTS.md §3c, appliqué ici : le
    fichier d'un mois est RÉÉCRIT, pas fusionné, donc rien ne rattraperait un
    acte que la fenêtre de relecture n'aurait pas couvert.
    """
    manquants = ids_publies(chemin_publie(mois, repertoire)) - set(actes)
    if manquants:
        raise ActesPerdus(
            f"{mois} : {len(manquants)} actes déjà publiés absents de la relecture "
            f"(ex. {sorted(manquants)[0]}) — élargir la fenêtre de livraisons."
        )


def mois_a_relire(aujourdhui: date, nb: int = MOIS_RELUS) -> list[str]:
    """Le mois en cours et les `nb - 1` précédents, du plus ancien au plus récent."""
    mois = []
    curseur = aujourdhui.replace(day=1)
    for _ in range(nb):
        mois.append(curseur.strftime("%Y-%m"))
        curseur = (curseur - timedelta(days=1)).replace(day=1)
    return sorted(mois)


def premiere_livraison_utile(mois: list[str]) -> str:
    """La date `AAAAMMJJ` à partir de laquelle relire les livraisons."""
    debut = date.fromisoformat(min(mois) + "-01") - timedelta(days=MARGE_JOURS)
    return debut.strftime("%Y%m%d")


def collecter(
    urls: list[str],
    repertoire_temporaire: Path,
    *,
    mois_retenus: Optional[set[str]] = None,
    budget_secondes: Optional[float] = None,
    base: str = SOURCE_LISTING,
    journal=sys.stderr,
) -> tuple[Moisson, Optional[str]]:
    """Lit les archives dans l'ordre donné ; la dernière lue gagne en cas de
    redélivrance. Rend la moisson et le nom de la dernière archive lue."""
    moisson = Moisson(repertoire_temporaire, mois_retenus=mois_retenus)
    depart = time.monotonic()
    derniere: Optional[str] = None
    for rang, nom in enumerate(urls):
        if budget_secondes is not None and time.monotonic() - depart > budget_secondes:
            print(f"  [!] budget de {budget_secondes:.0f} s atteint : {len(urls) - rang} "
                  "livraisons non lues", file=journal)
            break
        for membre, xml in parcourir_archive(base + nom):
            moisson.ajouter(membre, xml)
        derniere = nom
        if rang % 50 == 0:
            print(f"  {rang + 1}/{len(urls)} — {len(moisson.actes)} actes, "
                  f"{moisson.articles} articles", file=journal, flush=True)
    return moisson, derniere


def publier(
    par_mois: Any,
    repertoire: Path,
    *,
    derniere_livraison: Optional[str],
    controler_les_pertes: bool = True,
    journal=sys.stdout,
) -> list[str]:
    """Écrit un fichier par mois moissonné. Rend les mois effectivement écrits.

    `par_mois` est l'itérateur de `Moisson.par_mois` : un mois est construit,
    publié, puis relâché.
    """
    ecrits = []
    for mois, actes in par_mois:
        if not actes:
            # Un mois relu sans aucun acte n'écrase rien : ce serait publier
            # « aucun acte ce mois-ci » sur une lecture incomplète (§2 règle 5).
            continue
        if controler_les_pertes:
            verifier_sans_perte(mois, actes, repertoire)
        doc = document(mois, actes, derniere_livraison=derniere_livraison)
        if ecrire_index_json(chemin_publie(mois, repertoire), doc):
            ecrits.append(mois)
            print(f"-> {chemin_publie(mois, repertoire)} : {len(actes)} actes, "
                  f"{len(doc['mots'])} mots", file=journal)
    return ecrits


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--depuis-dump", action="store_true",
                         help="remplissage complet depuis le dump global DILA (une seule fois : "
                              "la DILA ne le renouvelle pas)")
    parseur.add_argument("--mois", action="append",
                         help="forcer un mois à relire (AAAA-MM), répétable")
    parseur.add_argument("--budget-secondes", type=float, default=None,
                         help="borne le temps de lecture des livraisons")
    parseur.add_argument("--repertoire", type=Path, default=REPERTOIRE_PUBLIE)
    parseur.add_argument("--base", default=SOURCE_LISTING)
    parseur.add_argument("--table-lois", type=Path, default=lois_jorf.CHEMIN_PAR_DEFAUT,
                         help="Table `numéro de loi → identifiant JORFTEXT`, tenue à jour "
                              f"en chemin (défaut : {lois_jorf.CHEMIN_PAR_DEFAUT}).")
    args = parseur.parse_args(argv)

    listing = telecharger_listing(args.base)
    dump, livraisons = livraisons_disponibles(listing)
    if args.depuis_dump:
        if not dump:
            print("[!] dump global absent du listing DILA", file=sys.stderr)
            return 1
        urls = [dump] + [nom for nom, _ in livraisons]
        mois_retenus = None
    else:
        mois = sorted(set(args.mois or mois_a_relire(date.today())))
        depuis = premiere_livraison_utile(mois)
        urls = [nom for nom, jour in livraisons if jour >= depuis]
        mois_retenus = set(mois)
        print(f"-> {len(urls)} livraisons depuis {depuis} pour {', '.join(mois)}")

    temporaire = Path(tempfile.mkdtemp(prefix="actes-reglementaires-"))
    try:
        moisson, derniere = collecter(urls, temporaire, mois_retenus=mois_retenus,
                                      budget_secondes=args.budget_secondes, base=args.base)
        ecrits = publier(moisson.par_mois(), args.repertoire, derniere_livraison=derniere,
                         controler_les_pertes=not args.depuis_dump)
        # La table des lois croisées en chemin, fusionnée avec celle déjà
        # committée : un run qui ne lit que deux mois de livraisons n'y voit que
        # les lois de ces deux mois, et n'a pas à perdre les autres.
        table = lois_jorf.charger(Path(args.table_lois))
        neuves = sum(lois_jorf.noter(table, numero, cid, date)
                     for numero, entrees in moisson.lois.items() for cid, date in entrees)
        if neuves:
            lois_jorf.ecrire(table, Path(args.table_lois))
        print(f"-> {args.table_lois} : {len(table)} numéro(s) de loi, {neuves} neuf/neuve(s)")
        # Option B (#1029 voie 1, arbitré le 23/09/2026) : la qualification
        # tardive d'un lien atteint le corpus par les redélivrances.
        corriges = corriger_les_liens(moisson.redelivres, args.repertoire)
    finally:
        shutil.rmtree(temporaire, ignore_errors=True)
    print(f"{len(moisson.actes)} actes, {len(ecrits)} mois réécrits, "
          f"{len(moisson.redelivres)} acte(s) redélivré(s) d'un mois clos "
          f"({len(corriges)} mois corrigé(s) sur leurs liens).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
