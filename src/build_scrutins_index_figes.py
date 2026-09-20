#!/usr/bin/env python3
"""
build_scrutins_index_figes.py

Construit et committe l'index des scrutins (votes nominatifs) d'une législature
AN définitivement close (`AN_SCRUTINS_LEGISLATURES_FIGEES`, candidate_profile.py)
à partir de l'archive open data de l'Assemblée nationale.

Usage (depuis la racine du dépôt) :
    # Téléchargement + construction pour une législature :
    python3 src/build_scrutins_index_figes.py --legislature 16

    # Ou à partir d'une archive déjà téléchargée :
    python3 src/build_scrutins_index_figes.py --legislature 14 --zip /tmp/Scrutins_XIV.json.zip

    # Toutes les législatures figées d'un coup :
    python3 src/build_scrutins_index_figes.py --toutes

Écrit `raw_data/scrutins_an_figes/<legislature>/{scrutins.json.gz,
index_par_acteur.json.gz}` — à committer dans le dépôt. L'archive brute n'est
jamais committée (voir `.gitignore`).

Pourquoi figer (#403) : les scrutins des législatures 14/15/16 ne changeront
plus (Last-Modified vérifié le 18/08/2026 : 2018-03-21, 2022-06-09,
2024-06-28). Les recompter à chaque run de CI coûte, pour chaque shard,
20 Mo de téléchargement et ~13 s d'indexation, pour un résultat identique à
l'octet près. Contrairement aux amendements (#377 : archives de 283-618 Mo,
IncompleteRead chroniques), ce n'est pas un remède à un échec réseau mais une
économie : le chemin réseau reste fonctionnel si le fallback committé manque.

La forme écrite est la forme dédupliquée décrite dans `_parse_scrutins_zip` :
le meta de chaque scrutin une seule fois (`scrutins.json`, clé `uid`) et un
index par acteur réduit à des références `[uid, position]`. Committer la forme
plate (le meta recopié pour chaque votant) représenterait 741 Mo pour les
quatre législatures, contre 68 Mo dédupliqués et 2,75 Mo une fois gzippés pour
les trois figées.

À REGÉNÉRER APRÈS #639. Les index figés committés portent la projection à cinq
champs d'avant #639, sans la qualification `type_scrutin`/`type_vote`/
`demandeur`. `_load_frozen_scrutins_index` les REFUSE désormais et retélécharge
l'archive : tant que les trois n'ont pas été régénérés par ce script, chaque run
paie 20,0 Mo de téléchargement supplémentaire. Un index figé accepté tel quel
aurait publié 43 des 66 motions de censure sous `type_vote: "vote_texte"`.
"""

import argparse
import gzip
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).parent))

from candidate_profile import (  # noqa: E402
    AN_SCRUTINS_FIGES_DIR,
    AN_SCRUTINS_LEGISLATURES_FIGEES,
    HEADERS,
    SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME,
    SCRUTINS_FIGES_SCRUTINS_FILENAME,
    _parse_scrutins_zip,
    _scrutins_zip_url,
)


def _charger_archive(legislature: str, zip_path: Path | None) -> Any:  # noqa: ANN401
    """Retourne un objet lisible par `zipfile.ZipFile` pour cette législature."""
    if zip_path is not None:
        return zip_path
    url = _scrutins_zip_url(legislature)
    if not url:
        raise SystemExit(f"Aucune archive open data de scrutins pour la législature {legislature}.")
    print(f"-> Téléchargement : {url}")
    resp = requests.get(url, headers=HEADERS, timeout=300)
    resp.raise_for_status()
    print(f"   {len(resp.content) / (1024 * 1024):.1f} Mo téléchargés")
    return io.BytesIO(resp.content)


def construire(legislature: str, zip_path: Path | None) -> int:
    if legislature not in AN_SCRUTINS_LEGISLATURES_FIGEES:
        print(
            f"[!] Législature {legislature} non figée "
            f"(figées : {sorted(AN_SCRUTINS_LEGISLATURES_FIGEES)}). "
            "Une législature en cours est reconstruite à chaque run, pas committée.",
            file=sys.stderr,
        )
        return 1

    source = _charger_archive(legislature, zip_path)
    try:
        scrutins, index = _parse_scrutins_zip(source, legislature)
    except zipfile.BadZipFile as exc:
        print(f"[!] Archive invalide : {exc}", file=sys.stderr)
        return 1

    if not scrutins:
        print(f"[!] Aucun scrutin extrait pour la législature {legislature}.", file=sys.stderr)
        return 1

    liens = sum(len(v) for v in index.values())
    out_dir = AN_SCRUTINS_FIGES_DIR / legislature
    out_dir.mkdir(parents=True, exist_ok=True)
    for nom, contenu in (
        (SCRUTINS_FIGES_SCRUTINS_FILENAME, scrutins),
        (SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME, index),
    ):
        chemin = out_dir / nom
        with gzip.open(chemin, "wt", encoding="utf-8") as f:
            json.dump(contenu, f, ensure_ascii=False)
        print(f"   {chemin} : {chemin.stat().st_size / (1024 * 1024):.2f} Mo")

    print(
        f"✓ Législature {legislature} : {len(scrutins)} scrutins, "
        f"{len(index)} acteurs, {liens} votes nominatifs."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--legislature", help="Législature figée à construire (ex. 16).")
    parser.add_argument(
        "--zip",
        type=Path,
        default=None,
        help="Archive déjà téléchargée (sinon téléchargement depuis data.assemblee-nationale.fr).",
    )
    parser.add_argument(
        "--toutes",
        action="store_true",
        help="Construit toutes les législatures figées (AN_SCRUTINS_LEGISLATURES_FIGEES).",
    )
    args = parser.parse_args()

    if args.toutes:
        if args.zip is not None:
            parser.error("--zip ne peut pas être combiné à --toutes (une archive par législature).")
        codes = [construire(leg, None) for leg in sorted(AN_SCRUTINS_LEGISLATURES_FIGEES)]
        return max(codes)

    if not args.legislature:
        parser.error("Préciser --legislature ou --toutes.")
    return construire(args.legislature, args.zip)


if __name__ == "__main__":
    raise SystemExit(main())
