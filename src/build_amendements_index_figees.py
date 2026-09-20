#!/usr/bin/env python3
"""
build_amendements_index_figees.py

Construit et committe l'index amendements d'une législature AN définitivement
close (`AN_AMENDEMENTS_LEGISLATURES_FIGEES`, candidate_profile.py) à partir
d'une archive téléchargée localement (manuellement ou via `--download`), hors
du budget réseau/temps de la CI qui échoue de façon récurrente sur ces deux
archives (350-650 Mo, IncompleteRead / HTTP2 PROTOCOL_ERROR répétés — voir
docs/decisions/amendements-legislatures-figees.md).

Usage (depuis la racine du dépôt) :
    # Téléchargement automatique (segments HTTP Range, retries — même logique
    # que le job CI réseau) dans .cache/amendements_an/ (gitignored, jamais committé) :
    python3 src/build_amendements_index_figees.py --legislature 16 --download

    # Ré-invoquer la même commande après une interruption reprend le
    # téléchargement là où il s'est arrêté (`_download_amendements_zip`, sonde
    # HEAD + reprise par octet) au lieu de repartir de zéro — le CDN AN coupe
    # aléatoirement en cours de segment sur ces deux grosses archives, souvent
    # plusieurs fois avant d'aboutir.

    # Ou à partir d'une archive déjà téléchargée manuellement (ex. curl --http1.1
    # avec resume, quand le téléchargement automatique échoue aussi) :
    python3 src/build_amendements_index_figees.py --legislature 15 --zip /tmp/Amendements_XV.json.zip

Écrit raw_data/amendements_an_figes/<legislature>/{amendements.json.gz,
index_par_acteur.json.gz, fraicheur.json} — à committer dans le dépôt.
L'archive brute (283-618 Mo) n'est elle-même jamais committée : voir
`.gitignore` (`.cache/`).

`_parse_amendements_zip` produit un enregistrement complet par signataire
(auteur + chaque cosignataire), donc N+1 copies dupliquées d'un même
amendement à N cosignataires. Committer cette forme brute est infaisable —
mesuré à 3,86 Go décompressés pour la seule législature 16, très au-delà de
la limite GitHub de 100 Mo par blob. `_aggregate_amendements_index` compacte
donc le résultat avant écriture : chaque amendement une seule fois
(`amendements.json`, clé `uid`), `index_par_acteur.json` réduit à une
référence légère (`uid` + `role_signataire`) par lien acteur/amendement.
Même dédupliqué, `index_par_acteur.json` mesure encore 177 Mo en clair pour
la législature 16 — toujours au-delà de la limite de 100 Mo — d'où l'écriture
gzip (10,4 Mo mesurés, la structure très répétitive {uid, role_signataire}
compressant très bien). Voir la révision de
docs/decisions/amendements-legislatures-figees.md.

**Un index construit avant le 18/08/2026 doit être reconstruit** : il référence
les amendements par `numero`, qui n'est pas unique (le `numeroLong` repart à
chaque texte), ce qui écrasait 74,9 % des amendements et attribuait les autres
au mauvais texte. `_load_frozen_amendement_index` refuse désormais ces index
hérités plutôt que de les servir — voir
docs/decisions/amendements-cle-uid.md.

`fraicheur.json` porte un marqueur `figee: true`, lu par `check_quality_gate.py`
(section 3d) pour ne jamais signaler ces législatures comme périmées :
elles ne seront plus jamais reconstruites, l'archive source AN étant close.
"""

import argparse
import gzip
import json
import sys
import time
import zipfile
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))

from candidate_profile import (  # noqa: E402
    AMENDEMENTS_CACHE_DIR,
    AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME,
    AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME,
    AMENDEMENTS_FRAICHEUR_FILENAME,
    AN_AMENDEMENTS_FIGEES_DIR,
    AN_AMENDEMENTS_LEGISLATURES_FIGEES,
    SourceAmendementsIndisponibleError,
    _aggregate_amendements_index,
    _amendements_zip_url,
    _download_amendements_zip,
    _parse_amendements_zip,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--legislature",
        required=True,
        choices=sorted(AN_AMENDEMENTS_LEGISLATURES_FIGEES),
        help="Législature figée à (re)construire.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--zip",
        type=Path,
        help="Archive amendements AN (Amendements.json.zip / Amendements_XV.json.zip) déjà téléchargée localement.",
    )
    source.add_argument(
        "--download",
        action="store_true",
        help=(
            "Télécharge l'archive AN localement avant de la parser (segments HTTP "
            "Range + retries, même logique que le job CI réseau), dans "
            ".cache/amendements_an/<legislature>/amendements.zip — jamais committé "
            "(voir .gitignore)."
        ),
    )
    parser.add_argument(
        "--chunk-size-mb",
        type=float,
        default=None,
        help=(
            "Taille de segment HTTP Range en Mo pour --download (défaut : 32, voir "
            "AMENDEMENTS_DOWNLOAD_CHUNK_BYTES). À réduire (ex. 1-2) quand le CDN AN "
            "traverse une fenêtre où même une requête de quelques Ko échoue "
            "systématiquement au-delà des tout premiers Mo du fichier (observé le "
            "14/08/2026) — un petit segment a une chance de passer là où un segment "
            "de 32 Mo n'en a quasiment aucune ; la reprise entre invocations garantit "
            "qu'aucun petit gain n'est perdu d'un essai à l'autre."
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=None,
        help=(
            "Nombre de tentatives par segment pour --download (défaut : 3, voir "
            "AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS). À augmenter quand le CDN AN "
            "traverse une fenêtre où un segment échoue systématiquement en 3 "
            "tentatives (IncompleteRead répété) — chaque tentative "
            "supplémentaire ne retente que le segment en échec, jamais le "
            "fichier entier, et la reprise entre invocations garantit qu'aucun "
            "gain n'est perdu même si le processus est interrompu en cours de "
            "route."
        ),
    )
    parser.add_argument(
        "--stall-cycles",
        type=int,
        default=None,
        help=(
            "Nombre de cycles « rien ne passe » avant d'abandonner pour --download "
            "(défaut : 3, voir AMENDEMENTS_SOURCE_STALL_MAX_CYCLES). Un cycle = les "
            "tentatives par plage HTTP Range, puis un GET séquentiel de repli. À "
            "augmenter ici : hors CI, attendre est le seul remède qui fonctionne "
            "quand les deux modes de transfert sont morts (#443)."
        ),
    )
    parser.add_argument(
        "--stall-wait-seconds",
        type=int,
        default=None,
        help=(
            "Attente entre deux cycles sans le moindre octet obtenu, pour --download "
            "(défaut : 30, voir AMENDEMENTS_SOURCE_STALL_WAIT_SECONDS). Attendre "
            "plutôt que marteler : dans cet état la source ne délivre rien, et les "
            "fenêtres de rétablissement observées se comptent en dizaines de minutes."
        ),
    )
    args = parser.parse_args()

    if args.download:
        url = _amendements_zip_url(args.legislature)
        if not url:
            print(f"Aucune URL connue pour la législature {args.legislature}", file=sys.stderr)
            return 1
        zip_path = AMENDEMENTS_CACHE_DIR / args.legislature / "amendements.zip"
        chunk_bytes = int(args.chunk_size_mb * 1024 * 1024) if args.chunk_size_mb else None
        print(f"-> Téléchargement de {url} vers {zip_path}...")
        try:
            # Toujours appelée, même si zip_path existe déjà : c'est
            # _download_amendements_zip elle-même qui décide (sonde HEAD) entre
            # sauter (déjà complet), reprendre (partiel, cas typique d'une
            # invocation précédente interrompue par l'instabilité du CDN AN) ou
            # redémarrer depuis le début (sonde en échec / fichier incohérent) —
            # ne jamais réutiliser aveuglément un fichier existant sans vérifier.
            _download_amendements_zip(
                url, zip_path, args.legislature,
                chunk_bytes=chunk_bytes, max_attempts=args.max_attempts,
                stall_max_cycles=args.stall_cycles,
                stall_wait_seconds=args.stall_wait_seconds,
            )
        except SourceAmendementsIndisponibleError as exc:
            # Distinct d'un échec de téléchargement (#443) : relancer la commande
            # tout de suite ne changera rien. Le préfixe déjà obtenu reste dans
            # zip_path et sera repris tel quel au prochain essai — c'est
            # précisément ce qui rend l'attente payante ici.
            print(f"Source AN indisponible : {exc}", file=sys.stderr)
            print(
                f"Le préfixe obtenu est conservé dans {zip_path} : relancer la même "
                "commande plus tard reprendra à cet octet.",
                file=sys.stderr,
            )
            return 1
        except (requests.RequestException, OSError) as exc:
            print(f"Échec du téléchargement : {exc}", file=sys.stderr)
            return 1
        zip_path_to_parse = zip_path
    else:
        if not args.zip.is_file():
            print(f"Archive introuvable : {args.zip}", file=sys.stderr)
            return 1
        zip_path_to_parse = args.zip

    print(f"-> Parsing de {zip_path_to_parse} (législature {args.legislature})...")
    try:
        index = _parse_amendements_zip(zip_path_to_parse)
    except zipfile.BadZipFile as exc:
        print(f"Archive invalide : {exc}", file=sys.stderr)
        return 1

    amendements, index_par_acteur = _aggregate_amendements_index(index)

    out_dir = AN_AMENDEMENTS_FIGEES_DIR / args.legislature
    out_dir.mkdir(parents=True, exist_ok=True)
    # Compressés gzip : `index_par_acteur.json` en clair mesure jusqu'à 177 Mo
    # pour la législature 16 (dépasse la limite GitHub de 100 Mo par blob),
    # 10,4 Mo une fois gzippé (voir docs/decisions/amendements-legislatures-figees.md).
    with gzip.open(out_dir / AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME, "wt", encoding="utf-8") as f:
        json.dump(amendements, f, ensure_ascii=False)
    with gzip.open(out_dir / AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME, "wt", encoding="utf-8") as f:
        json.dump(index_par_acteur, f, ensure_ascii=False)
    with open(out_dir / AMENDEMENTS_FRAICHEUR_FILENAME, "w", encoding="utf-8") as f:
        json.dump(
            {
                "derniere_construction_reussie": True,
                "horodatage": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "figee": True,
            },
            f,
            ensure_ascii=False,
        )

    liens = sum(len(refs) for refs in index_par_acteur.values())
    print(
        f"  -> {len(amendements)} amendement(s) unique(s), {len(index_par_acteur)} acteur(s), "
        f"{liens} lien(s) acteur/amendement — écrit dans {out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
