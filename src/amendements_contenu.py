#!/usr/bin/env python3
"""amendements_contenu.py — l'article visé et les mots de l'exposé de chaque
amendement, lus dans l'archive AN (#1029, voie 2).

## Ce qui gouverne ce module

Cinq décisions le touchent ; trois se lisent avant d'y changer quoi que ce soit
(les deux autres ne font qu'emprunter `forme_indexee` et `mots_du_texte`) :

- `docs/decisions/index-de-mots-des-amendements-1029.md` — **pourquoi un index
  de mots et pas l'exposé**, et les seuils qui le rendent tenable ;
- `docs/decisions/etalement-disque-index-de-mots-1121.md` — **pourquoi deux
  fabriques**, `document` en référence et `document_depuis_archive` en
  production, et pourquoi le vocabulaire doit être arrêté avant l'inversion ;
- `docs/decisions/identifiants-an-pris-pour-des-jetons-1119.md` — l'uid publié
  amputé de son préfixe fait 24 caractères, que le scanner de secrets de GitHub
  prend pour un jeton. Avant de toucher à `prefixe_ids`, lire cette page.

## Le besoin

Retrouver les amendements d'un sujet — « carburant » : TICPE, ticket
carburant… Ni l'index publié (`pivot_data/amendements/<lég>.json`), ni les
profils ne portaient autre chose que le dossier, dont l'intitulé nomme le
véhicule (« projet de loi de finances ») et jamais le sujet. L'archive AN
porte les deux faits qui manquaient :

- `pointeurFragmentTexte.division` — l'**article visé** (`titre` : « Article 3 »,
  « ÉTAT B »…) et sa **position** (`avant_A_Apres` : « A », « Après », « Avant ») ;
- `corps.contenuAuteur.exposeSommaire` — l'**exposé sommaire**, en HTML.

## Ce qui est publié : un index de mots, pas le texte

L'exposé entier ne se publie pas — ≈ 100 Mo pour la seule XVIIe. On publie la
liste de ses MOTS, et pour chaque mot les amendements qui le contiennent : un
index de livre. Arbitré le 22/09/2026 pour toutes les législatures. Un mot :

- minuscules, sans accents, 4 lettres ou plus (`[a-z]{4,}`) ;
- ramené à sa **forme de base** quand elle existe dans l'index
  (`forme_indexee`) : `carburants` → `carburant`, `fiscale`, `fiscales`,
  `fiscaux` → `fiscal`. Une forme absente n'est jamais devinée ;
- présent dans au plus `SEUIL_FREQUENCE` des amendements de la législature : un
  mot plus fréquent (« amendement », « article », « pour ») ne sert à aucune
  recherche — il en renverrait des milliers.

Mesuré le 22/09/2026 sur les quatre archives (#1029) : 120,3 Mo et 31,6 M de
renvois sans fusion ni seuil de 3 % ; **93,0 Mo** et 23,1 M avec, 29,4 Mo une
fois compressés — et les 624 amendements « carbur* / TICPE » de la XVIIe
toujours tous trouvés. Rattacher un mot seulement s'il revient deux fois dans
l'exposé a été mesuré et écarté : ÷ 7 sur les renvois, mais 182 amendements
« carburant » sur 624.

Aucun mot n'est rangé sous un thème : sa présence dans l'exposé est un fait de
la source, pas une lecture (§2 règle 8). Le texte entier se lit chez l'AN :
`https://www.assemblee-nationale.fr/dyn/<lég>/amendements/<uid>`.

## La mémoire, et pourquoi un étalement sur disque

`lire_archive` rend `{uid: (article, mots)}` pour TOUS les amendements à la
fois : 3,9 Go sur les 311 934 de la XVe, et un premier essai tué par le noyau à
2,87 Go (24/09/2026). `document_depuis_archive` fait le même document sans
jamais tenir l'archive — **315 Mo de pic sur la XVe, 197 sur la XVIe**, pour
157 s au lieu de 131. Le temps payé, la mémoire divisée par douze, et une
construction qui ne dépend plus de ce qui tourne à côté. C'est elle que la CI
et la ligne de commande empruntent ; `document` reste la fabrique de référence,
celle contre laquelle un test compare archive en main.

## Le fichier, un par législature

`{schema_version, legislature, genere_le, licence_donnees, seuil_frequence,
  fusion_des_formes, prefixe_ids, ids: [fin d'uid…],
  articles: [[titre, position] | null…], mots: {mot: "<renvois>"}}`

`ids` porte l'uid AN **sans** `prefixe_ids`, commun à toute la législature
(`AMANR5L17`) : l'uid est `prefixe_ids + ids[i]` (−6,6 Mo sur les quatre).
`ids` fixe la numérotation : un renvoi est la POSITION d'un amendement dans
`ids`. Les renvois d'un mot sont croissants, écrits en ÉCARTS successifs, en
base 36, séparés par une virgule — « 3,a,1 » renvoie aux positions 3, 13, 14.
C'est ce qui ramène un renvoi à ~3 octets.

**Chercher un mot** : le normaliser comme un exposé (`mots_du_texte`), le
ramener à sa forme indexée (`forme_indexee`, contre les clés de `mots`), puis
décoder ses renvois (`decoder`). `fusion_des_formes` publie la règle, pour que
tout lecteur du fichier l'applique à l'identique.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from licences import LICENCE_AN  # noqa: E402

SCHEMA_VERSION = "amendements-contenu-v1"

#: Un mot (déjà ramené à sa forme de base) présent dans plus de cette part des
#: amendements n'est pas indexé. Un premier tri à `SEUIL_AVANT_FUSION` écarte
#: les mots-outils avant la fusion, qui ne les rattache donc à rien.
SEUIL_FREQUENCE = 0.03
SEUIL_AVANT_FUSION = 0.05
#: Les terminaisons retirées pour ramener un mot à sa forme de base, dans cet
#: ordre : `[terminaison, remplacement]`. Appliquées seulement si la forme
#: obtenue existe dans l'index (`forme_indexee`).
FUSION_DES_FORMES: tuple[tuple[str, str], ...] = (("aux", "al"), ("es", ""), ("s", ""), ("x", ""), ("e", ""))
LONGUEUR_MIN_MOT = 4
_MOT = re.compile(r"[a-z]{%d,}" % LONGUEUR_MIN_MOT)
_BALISE = re.compile(r"<[^>]+>")
_CHIFFRES36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def mots_du_texte(texte_html: Any) -> set[str]:
    """Les mots d'un exposé : HTML retiré, minuscules, sans accents, ≥ 4 lettres."""
    if not isinstance(texte_html, str) or not texte_html:
        return set()
    texte = _BALISE.sub(" ", html.unescape(texte_html)).lower()
    texte = "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")
    return set(_MOT.findall(texte))


def article_vise(amendement: dict[str, Any]) -> Optional[list[str]]:
    """`[titre, position]` de la division visée, tels que la source les écrit ;
    `None` quand l'archive n'en publie pas."""
    division = (amendement.get("pointeurFragmentTexte") or {}).get("division")
    if not isinstance(division, dict):
        return None
    titre = division.get("titre")
    if not isinstance(titre, str) or not titre.strip():
        return None
    position = division.get("avant_A_Apres")
    return [titre.strip(), position if isinstance(position, str) else None]


def forme_indexee(mot: str, vocabulaire: Any) -> str:
    """La forme sous laquelle `mot` est indexé : la plus courte que la règle
    `FUSION_DES_FORMES` atteint DANS `vocabulaire`, sinon `mot` lui-même.

    `fiscaux` → `fiscal` si `fiscal` est dans l'index ; `publiques` reste
    `publiques` quand `public` n'y est pas. Jamais une forme devinée.
    """
    for terminaison, remplacement in FUSION_DES_FORMES:
        if not mot.endswith(terminaison):
            continue
        base = mot[: len(mot) - len(terminaison)] + remplacement
        if len(base) >= LONGUEUR_MIN_MOT and base != mot and base in vocabulaire:
            return forme_indexee(base, vocabulaire)
    return mot


def _en_liste(valeur: Any) -> list[Any]:
    return valeur if isinstance(valeur, list) else [valeur]


def _amendements_de_l_archive(zip_path: Path) -> Iterator[dict[str, Any]]:
    """Les `amendement` de l'archive, un à la fois.

    Deux formes, comme `candidate_profile` les lit déjà : un fichier par
    amendement (XVe à XVIIe), ou, pour la XIVe, un seul JSON de 677 Mo —
    `textesEtAmendements.texteleg[].amendements.amendement[]` (#299).
    """
    with zipfile.ZipFile(zip_path) as z:
        for nom in z.namelist():
            if not nom.endswith(".json"):
                continue
            try:
                document = json.loads(z.read(nom))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(document, dict):
                continue
            racine = document.get("textesEtAmendements")
            if isinstance(racine, dict):
                for texteleg in _en_liste(racine.get("texteleg")):
                    if not isinstance(texteleg, dict):
                        continue
                    for amendement in _en_liste((texteleg.get("amendements") or {}).get("amendement")):
                        if isinstance(amendement, dict) and amendement.get("uid"):
                            yield amendement
                continue
            amendement = document.get("amendement")
            if isinstance(amendement, dict) and amendement.get("uid"):
                yield amendement


def lire_archive(zip_path: Path) -> dict[str, tuple[Optional[list[str]], set[str]]]:
    """`{uid: (article, mots)}` pour chaque amendement de l'archive."""
    contenu: dict[str, tuple[Optional[list[str]], set[str]]] = {}
    for amendement in _amendements_de_l_archive(zip_path):
        corps = amendement.get("corps") or {}
        auteur = corps.get("contenuAuteur") if isinstance(corps, dict) else None
        # XVe-XVIIe : sous `contenuAuteur` ; XIVe : directement sous `corps`.
        expose = (auteur.get("exposeSommaire") if isinstance(auteur, dict)
                  else corps.get("exposeSommaire") if isinstance(corps, dict) else None)
        contenu[str(amendement["uid"])] = (article_vise(amendement), mots_du_texte(expose))
    return contenu


def _encoder(positions: Iterable[int]) -> str:
    """Positions croissantes → écarts successifs en base 36, séparés par des virgules."""
    morceaux, precedent = [], 0
    for p in positions:
        ecart, precedent = p - precedent, p
        chiffres = ""
        while True:
            ecart, reste = divmod(ecart, 36)
            chiffres = _CHIFFRES36[reste] + chiffres
            if not ecart:
                break
        morceaux.append(chiffres)
    return ",".join(morceaux)


def decoder(renvois: str) -> list[int]:
    """L'inverse d'`_encoder` — la règle que l'interface applique."""
    positions, courant = [], 0
    for morceau in renvois.split(",") if renvois else []:
        courant += int(morceau, 36)
        positions.append(courant)
    return positions


def document(
    legislature: str,
    contenu: dict[str, tuple[Optional[list[str]], set[str]]],
    *,
    genere_le: Optional[str] = None,
) -> dict[str, Any]:
    """Le fichier publié d'une législature (voir la docstring du module).

    Trois temps, dans l'ordre de la mesure : les mots de plus de
    `SEUIL_AVANT_FUSION` des amendements sont écartés ; les autres sont ramenés
    à leur forme de base (`forme_indexee`) ; les formes présentes dans plus de
    `SEUIL_FREQUENCE` des amendements sont écartées à leur tour.
    """
    ids = sorted(contenu)
    total = len(ids) or 1
    brut: dict[str, set[int]] = defaultdict(set)
    for position, uid in enumerate(ids):
        for mot in contenu[uid][1]:
            brut[mot].add(position)
    vocabulaire = {mot for mot, pos in brut.items() if len(pos) <= SEUIL_AVANT_FUSION * total}
    fusion: dict[str, set[int]] = defaultdict(set)
    for mot in vocabulaire:
        fusion[forme_indexee(mot, vocabulaire)] |= brut[mot]
    prefixe = f"AMANR5L{legislature}"
    if not all(uid.startswith(prefixe) for uid in ids):
        prefixe = ""
    return {
        "schema_version": SCHEMA_VERSION,
        "legislature": legislature,
        "genere_le": genere_le or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "licence_donnees": LICENCE_AN,
        "seuil_frequence": SEUIL_FREQUENCE,
        "fusion_des_formes": [list(r) for r in FUSION_DES_FORMES],
        "prefixe_ids": prefixe,
        "ids": [uid[len(prefixe):] for uid in ids],
        "articles": [contenu[uid][0] for uid in ids],
        "mots": {
            mot: _encoder(sorted(pos)) for mot, pos in sorted(fusion.items())
            if len(pos) <= SEUIL_FREQUENCE * total
        },
    }


#: Seaux temporaires d'un étalement sur disque. **Défini ici et importé par
#: `actes_reglementaires`**, qui applique le même remède à son propre index de
#: mots : deux définitions du même nom dans `src/` rendent le symbole ambigu
#: pour `scripts/generer_decisions_par_module.py`, qui le laisse alors tomber
#: de la table — une décision qui le nommerait serait silencieusement amputée.
NB_SEAUX = 256


def hash_seau(cle: str) -> int:
    """Le seau d'une clé — une forme indexée ici, un identifiant d'acte chez
    `actes_reglementaires` : stable d'un processus à l'autre, contrairement à
    `hash()` d'une chaîne, que Python randomise."""
    return sum(cle.encode()) % NB_SEAUX


def document_depuis_archive(
    legislature: str,
    zip_path: Path,
    *,
    repertoire: Optional[Path] = None,
    genere_le: Optional[str] = None,
) -> dict[str, Any]:
    """Le même document que `document`, construit **sans tenir l'archive en
    mémoire** (#1121).

    `lire_archive` rend `{uid: (article, mots)}` pour tous les amendements à la
    fois : mesuré le 24/09/2026, 3,9 Go pour les 311 934 amendements de la XVe,
    et un premier essai tué par le noyau à 2,87 Go sur une machine de 7,8 Go.
    La construction ne tenait donc que si la machine était par ailleurs au
    repos — ce n'est pas une propriété qu'on peut supposer, et la CI ne l'a
    jamais.

    Trois passes, et ce qui reste en mémoire est nommé à chaque fois :

    1. **Lire l'archive une fois.** On garde les uid et leur article — les
       seuls faits qu'on ne peut pas recalculer — et un simple COMPTE par mot.
       Les mots de chaque exposé partent sur disque, une ligne par amendement.
    2. **Arrêter le vocabulaire**, puis relire ces lignes pour ranger chaque
       `(forme indexée, position)` dans l'un des `NB_SEAUX` seaux. La fusion
       des formes exige le vocabulaire ENTIER — `fiscaux` ne devient `fiscal`
       que si `fiscal` existe —, d'où une passe qui ne peut pas commencer
       avant que la première soit finie.
    3. **Regrouper seau par seau.** Un seau tient seul en mémoire, et les
       positions d'une forme sont toutes dans le même : c'est ce que garantit
       `hash_seau`.

    Le document rendu est **identique** à `document(lire_archive(zip))`, ce
    qu'un test compare archive en main. Le temporaire vit hors du dépôt et hors
    de `.cache/`, et disparaît même en cas d'erreur.

    Un uid vu deux fois n'est compté qu'une fois, sa première occurrence
    faisant foi. Aucune archive n'en présente : mesuré le 24/09/2026, 311 934
    uid distincts pour 311 934 fichiers sur la XVe.
    """
    import shutil  # noqa: PLC0415
    import tempfile  # noqa: PLC0415

    propre = repertoire is None
    racine = Path(repertoire) if repertoire else Path(tempfile.mkdtemp(prefix="amendements-contenu-"))
    racine.mkdir(parents=True, exist_ok=True)
    try:
        articles: dict[str, Optional[list[str]]] = {}
        compte: dict[str, int] = defaultdict(int)
        exposes = racine / "exposes.tsv"

        # ── 1. l'archive, une fois ───────────────────────────────────────
        with open(exposes, "w", encoding="utf-8") as flux:
            for amendement in _amendements_de_l_archive(zip_path):
                uid = str(amendement["uid"])
                if uid in articles:
                    continue
                corps = amendement.get("corps") or {}
                auteur = corps.get("contenuAuteur") if isinstance(corps, dict) else None
                expose = (auteur.get("exposeSommaire") if isinstance(auteur, dict)
                          else corps.get("exposeSommaire") if isinstance(corps, dict) else None)
                articles[uid] = article_vise(amendement)
                mots = mots_du_texte(expose)
                for mot in mots:
                    compte[mot] += 1
                flux.write(uid + "\t" + " ".join(sorted(mots)) + "\n")

        ids = sorted(articles)
        total = len(ids) or 1
        position = {uid: rang for rang, uid in enumerate(ids)}

        # ── 2. le vocabulaire, puis les seaux ────────────────────────────
        vocabulaire = {mot for mot, n in compte.items() if n <= SEUIL_AVANT_FUSION * total}
        compte.clear()
        retenue: dict[str, str] = {}
        seaux = [open(racine / f"seau-{i:03d}.tsv", "w", encoding="utf-8") for i in range(NB_SEAUX)]
        try:
            with open(exposes, encoding="utf-8") as flux:
                for ligne in flux:
                    uid, _, mots = ligne.rstrip("\n").partition("\t")
                    rang = position.get(uid)
                    if rang is None:
                        continue
                    for mot in mots.split():
                        if mot not in vocabulaire:
                            continue
                        forme = retenue.get(mot)
                        if forme is None:
                            forme = retenue[mot] = forme_indexee(mot, vocabulaire)
                        seaux[hash_seau(forme)].write(f"{forme}\t{rang}\n")
        finally:
            for flux in seaux:
                flux.close()
        exposes.unlink(missing_ok=True)
        vocabulaire.clear()
        retenue.clear()

        # ── 3. un seau à la fois ─────────────────────────────────────────
        plafond = SEUIL_FREQUENCE * total
        mots_publies: dict[str, str] = {}
        for i in range(NB_SEAUX):
            groupes: dict[str, set[int]] = defaultdict(set)
            chemin = racine / f"seau-{i:03d}.tsv"
            with open(chemin, encoding="utf-8") as flux:
                for ligne in flux:
                    forme, _, rang = ligne.rstrip("\n").partition("\t")
                    groupes[forme].add(int(rang))
            chemin.unlink(missing_ok=True)
            for forme, positions in groupes.items():
                if len(positions) <= plafond:
                    mots_publies[forme] = _encoder(sorted(positions))

        prefixe = f"AMANR5L{legislature}"
        if not all(uid.startswith(prefixe) for uid in ids):
            prefixe = ""
        return {
            "schema_version": SCHEMA_VERSION,
            "legislature": legislature,
            "genere_le": genere_le or time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": LICENCE_AN,
            "seuil_frequence": SEUIL_FREQUENCE,
            "fusion_des_formes": [list(r) for r in FUSION_DES_FORMES],
            "prefixe_ids": prefixe,
            "ids": [uid[len(prefixe):] for uid in ids],
            "articles": [articles[uid] for uid in ids],
            "mots": {forme: mots_publies[forme] for forme in sorted(mots_publies)},
        }
    finally:
        if propre:
            shutil.rmtree(racine, ignore_errors=True)


#: Où le job `extract-amendements-an` dépose le contenu d'une législature, à
#: côté de son index : l'artifact `amendements-index-an` emporte tout
#: `.cache/amendements_an/`, donc `merge-and-pivot` le reçoit sans rien changer
#: au workflow.
NOM_CACHE = "contenu.json"
#: Le fichier publié, à côté de `<lég>.json` et `<lég>.cosignatures.json`.
GABARIT_PUBLIE = "{legislature}.contenu.json"


def chemin_cache(legislature: str, cache_dir: Path) -> Path:
    return Path(cache_dir) / legislature / NOM_CACHE


def chemin_publie(legislature: str, amendements_dir: Path) -> Path:
    return Path(amendements_dir) / GABARIT_PUBLIE.format(legislature=legislature)


def ecrire_contenu_cache(legislature: str, zip_path: Path, cache_dir: Path) -> Path:
    """Lit l'archive et dépose le document de la législature dans le cache.

    Passe par `document_depuis_archive` : c'est ici que la mémoire comptait, la
    XIVe et la XVIIe se construisant dans le même job que la XVe.
    """
    from json_io import dumps_ligne, ecrire_index_json  # noqa: PLC0415

    doc = document_depuis_archive(legislature, zip_path)
    chemin = chemin_cache(legislature, cache_dir)
    ecrire_index_json(chemin, doc, dumps_ligne)
    print(f"  ✓ contenu des amendements, législature {legislature} : {len(doc['ids'])} "
          f"amendement(s), {len(doc['mots'])} mot(s) indexé(s) → {chemin}")
    return chemin


def charger(chemin: Path) -> Optional[dict[str, Any]]:
    """Un document de contenu, ou `None` s'il est absent ou illisible."""
    try:
        with open(chemin, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict) or doc.get("schema_version") != SCHEMA_VERSION:
        return None
    return doc


def uid_complet(doc: dict[str, Any], position: int) -> str:
    """L'uid AN de l'amendement à cette position : `prefixe_ids + ids[position]`."""
    return (doc.get("prefixe_ids") or "") + doc["ids"][position]


def articles_du_document(doc: dict[str, Any]) -> dict[str, list[Any]]:
    """`{uid: [titre, position]}` — pour poser l'article sur l'index publié."""
    prefixe = doc.get("prefixe_ids") or ""
    return {prefixe + fin: art for fin, art in zip(doc.get("ids") or [], doc.get("articles") or []) if art}


def main(argv: Optional[list[str]] = None) -> int:
    import argparse  # noqa: PLC0415

    from json_io import dumps_ligne, ecrire_index_json  # noqa: PLC0415

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--legislature", required=True)
    parser.add_argument("--zip", type=Path, required=True, help="archive Amendements*.json.zip de l'AN")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    debut = time.monotonic()
    doc = document_depuis_archive(args.legislature, args.zip)
    ecrit = ecrire_index_json(args.out, doc, dumps_ligne)
    poids = args.out.stat().st_size / 1048576 if args.out.exists() else 0
    print(f"  ✓ {len(doc['ids'])} amendement(s), {len(doc['mots'])} mot(s) indexé(s), "
          f"{sum(1 for a in doc['articles'] if a)} article(s) visé(s) → {args.out} "
          f"({poids:.1f} Mo{'' if ecrit else ', inchangé'}) en {time.monotonic() - debut:.0f} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
