#!/usr/bin/env python3
"""migrer_profils_partitionnes_580.py — Convertit `raw_data/profiles` de la
forme monolithique à la forme partitionnée par législature (#580).

Ce que fait ce script
---------------------
Pour chaque `<slug>.json` encore monolithique :

  1. il le lit et le **partitionne en mémoire** ;
  2. il **recompose** immédiatement, en mémoire, et exige l'égalité stricte
     avec le document d'origine — même liste, même ordre, mêmes champs ;
  3. il compare le **nombre d'amendements** et le **multi-ensemble des `uid`**
     avant/après ;
  4. **seulement alors** il écrit : les tranches d'abord, le socle en dernier ;
  5. il relit depuis le disque et refait les trois comparaisons, cette fois à
     travers un aller-retour JSON réel.

Si la moindre comparaison échoue, l'octet d'origine est remis en place et le
script s'arrête. Aucune étape ne supprime avant d'avoir vérifié.

Ce qu'il ne fait PAS
--------------------
Il ne transforme rien. Pas de déduplication, pas de dénormalisation, pas de
champ retiré ni réordonné. `raw_data/` reste la couche source-near, aux mêmes
octets près — c'est la différence entre ce lot et la normalisation écartée
par #434.

Idempotence
-----------
Un profil déjà partitionné est **vérifié** (les tranches se relisent, les
comptes tombent) puis compté comme tel. Relancer le script sur un corpus déjà
migré ne réécrit rien et rend 0 modification : c'est ce qui rend sûr de le
relancer après une interruption.

Usage
-----
::

    # 1. Constat, sans rien écrire — c'est le mode par défaut.
    python3 src/migrer_profils_partitionnes_580.py --profils-dir raw_data/profiles

    # 2. Migration réelle.
    python3 src/migrer_profils_partitionnes_580.py \\
        --profils-dir raw_data/profiles --apply

    # 3. Vérification seule d'un corpus déjà migré (ne réécrit jamais).
    python3 src/migrer_profils_partitionnes_580.py \\
        --profils-dir raw_data/profiles --verifier-seulement
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from json_io import dumps_profil_json
from profil_brut import (
    CLE_PARTITIONNEE,
    PartitionIllisible,
    charger_profil_brut,
    dossier_tranches,
    ecrire_profil_brut,
    est_partitionne,
    partitionner,
    recomposer,
    slugs_du_repertoire,
)


class MigrationRefusee(RuntimeError):
    """Une comparaison avant/après n'est pas tombée juste.

    Le script s'arrête sur cette exception plutôt que de passer au profil
    suivant : une découpe qui perd sur un profil perdra sur les autres, et
    continuer transformerait un défaut en 481.
    """


def _empreinte_uids(amendements: list[Any]) -> Counter:
    """Multi-ensemble des `uid`, et non un ensemble.

    Un `set` masquerait la disparition d'un doublon. Il n'y en a aucun sur le
    corpus du 29/08/2026 (mesuré : 0 uid dupliqué à l'intérieur d'un profil,
    sur 6 091 732 amendements), mais un contrôle qui ne tient que sous une
    hypothèse non écrite n'est pas un contrôle.
    """
    return Counter(
        a.get("uid") if isinstance(a, dict) else None for a in amendements
    )


def _comparer(avant: dict[str, Any], apres: dict[str, Any], slug: str, etape: str) -> None:
    """Trois comparaisons, de la plus fine à la plus large."""
    ams_avant = avant.get(CLE_PARTITIONNEE) or []
    ams_apres = apres.get(CLE_PARTITIONNEE) or []

    if len(ams_avant) != len(ams_apres):
        raise MigrationRefusee(
            f"{slug} ({etape}) : {len(ams_avant)} amendement(s) avant, "
            f"{len(ams_apres)} après."
        )

    uids_avant = _empreinte_uids(ams_avant)
    uids_apres = _empreinte_uids(ams_apres)
    if uids_avant != uids_apres:
        perdus = uids_avant - uids_apres
        gagnes = uids_apres - uids_avant
        raise MigrationRefusee(
            f"{slug} ({etape}) : l'ensemble des uid diffère — "
            f"{sum(perdus.values())} perdu(s), {sum(gagnes.values())} apparu(s). "
            f"Exemples perdus : {list(perdus)[:3]}"
        )

    if avant != apres:
        # L'égalité stricte couvre l'ordre de la liste ET tout champ hors
        # amendements. Le message nomme ce qui diffère, sinon il n'aide pas.
        cles_avant, cles_apres = set(avant), set(apres)
        diff_cles = (cles_avant ^ cles_apres) or {
            c for c in cles_avant & cles_apres if avant[c] != apres[c]
        }
        raise MigrationRefusee(
            f"{slug} ({etape}) : le document recomposé diffère de l'original "
            f"sur : {sorted(diff_cles)}"
        )


def _digest(profil: dict[str, Any]) -> str:
    """Empreinte stable d'un profil, pour un contrôle global bon marché."""
    return hashlib.sha256(dumps_profil_json(profil).encode("utf-8")).hexdigest()


def migrer_profil(
    profils_dir: Path, slug: str, *, ecrire: bool
) -> dict[str, Any]:
    """Migre (ou vérifie) un profil. Rend un compte rendu sérialisable."""
    socle_path = profils_dir / f"{slug}.json"
    brut = socle_path.read_bytes()
    document = json.loads(brut)
    if not isinstance(document, dict):
        raise MigrationRefusee(f"{slug} : document JSON qui n'est pas un objet.")

    # ── Déjà partitionné : on vérifie, on ne réécrit pas ────────────────────
    if est_partitionne(document):
        profil = charger_profil_brut(socle_path)
        return {
            "slug": slug,
            "etat": "deja_partitionne",
            "amendements": len(profil.get(CLE_PARTITIONNEE) or []),
            "tranches": len(list(dossier_tranches(profils_dir, slug).glob("*.json")))
            if dossier_tranches(profils_dir, slug).is_dir() else 0,
            "digest": _digest(profil),
        }

    nb_amendements = len(document.get(CLE_PARTITIONNEE) or [])
    digest = _digest(document)

    # ── Vérification EN MÉMOIRE, avant toute écriture ───────────────────────
    socle, tranches = partitionner(document)
    _comparer(
        document,
        recomposer(socle, tranches) if est_partitionne(socle) else socle,
        slug,
        "en mémoire",
    )

    # Un profil sans amendement n'a rien à ranger : il n'est ni découpé ni
    # réécrit. Le toucher ferait un diff git sur 481 profils là où seuls les
    # profils porteurs ont changé.
    if not tranches:
        return {
            "slug": slug,
            "etat": "sans_amendement",
            "amendements": nb_amendements,
            "tranches": 0,
            "digest": digest,
        }

    if not ecrire:
        return {
            "slug": slug,
            "etat": "a_migrer",
            "amendements": nb_amendements,
            "tranches": len(tranches),
            "digest": digest,
        }

    dossier = dossier_tranches(profils_dir, slug)
    deja_la = dossier.exists()
    try:
        ecrire_profil_brut(profils_dir, slug, document)
        relu = charger_profil_brut(socle_path)
        _comparer(document, relu, slug, "relu du disque")
        if _digest(relu) != digest:
            raise MigrationRefusee(f"{slug} : empreinte du profil relu différente.")
    except Exception:
        # RESTAURATION. L'original est encore en mémoire (`brut`) : on le
        # réécrit tel quel et on retire ce qu'on venait de créer. Le profil
        # ressort exactement comme il est entré, y compris son horodatage de
        # contenu — c'est du même octet qu'il s'agit.
        socle_path.write_bytes(brut)
        if not deja_la and dossier.is_dir():
            shutil.rmtree(dossier)
        raise

    return {
        "slug": slug,
        "etat": "migre",
        "amendements": nb_amendements,
        "tranches": len(tranches),
        "digest": digest,
    }


def migrer(
    profils_dir: Path, *, ecrire: bool, verifier_seulement: bool = False,
    seulement: Optional[str] = None,
) -> dict[str, Any]:
    """Parcourt le répertoire. Rend le rapport agrégé."""
    slugs = slugs_du_repertoire(profils_dir)
    if seulement:
        slugs = [s for s in slugs if s == seulement]

    comptes: Counter = Counter()
    total_amendements = 0
    total_tranches = 0
    digests: list[str] = []
    details: list[dict[str, Any]] = []

    for i, slug in enumerate(slugs, start=1):
        compte_rendu = migrer_profil(
            profils_dir, slug, ecrire=ecrire and not verifier_seulement
        )
        comptes[compte_rendu["etat"]] += 1
        total_amendements += compte_rendu["amendements"]
        total_tranches += compte_rendu["tranches"]
        digests.append(compte_rendu["digest"])
        details.append(compte_rendu)
        print(
            f"  [{i:>4}/{len(slugs)}] {slug:<40} {compte_rendu['etat']:<18} "
            f"{compte_rendu['amendements']:>8} amendement(s), "
            f"{compte_rendu['tranches']} tranche(s)",
            flush=True,
        )

    return {
        "profils_dir": str(profils_dir),
        "nb_profils": len(slugs),
        "par_etat": dict(comptes),
        "total_amendements": total_amendements,
        "total_tranches": total_tranches,
        # Empreinte du corpus entier : elle ne doit PAS bouger entre un run à
        # blanc et le run réel. C'est la preuve, en un chiffre, que la
        # migration n'a rien changé au contenu.
        "empreinte_corpus": hashlib.sha256(
            "".join(sorted(digests)).encode("utf-8")
        ).hexdigest(),
        "details": details,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--profils-dir", type=Path, default=Path("raw_data/profiles"), metavar="REP",
        help="Répertoire des profils bruts (défaut : raw_data/profiles).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Écrire réellement. Sans ce drapeau, le script ne fait que constater.",
    )
    parser.add_argument(
        "--verifier-seulement", action="store_true",
        help="Ne rien écrire, même avec --apply : relire et vérifier un corpus "
             "déjà migré.",
    )
    parser.add_argument("--only", metavar="SLUG", help="Un seul profil.")
    parser.add_argument("--out-json", type=Path, metavar="FICHIER",
                        help="Rapport JSON (les détails par profil).")
    args = parser.parse_args(argv)

    if not args.profils_dir.is_dir():
        print(f"[!] Répertoire introuvable : {args.profils_dir}", file=sys.stderr)
        return 2

    mode = (
        "VÉRIFICATION" if args.verifier_seulement
        else ("APPLIQUÉ" if args.apply else "SIMULATION (--apply pour écrire)")
    )
    print(f"=== Migration #580 — {mode} — {args.profils_dir} ===\n")

    try:
        rapport = migrer(
            args.profils_dir, ecrire=args.apply,
            verifier_seulement=args.verifier_seulement, seulement=args.only,
        )
    except (MigrationRefusee, PartitionIllisible) as exc:
        print(f"\n[!] MIGRATION INTERROMPUE : {exc}", file=sys.stderr)
        print(
            "    Rien n'est perdu : le profil fautif a été remis dans son état "
            "d'origine, et les profils déjà migrés l'ont été après vérification.",
            file=sys.stderr,
        )
        return 1

    print(f"\n=== {mode} ===")
    print(f"  Profils parcourus     : {rapport['nb_profils']}")
    for etat, n in sorted(rapport["par_etat"].items()):
        print(f"    {etat:<20}: {n}")
    print(f"  Amendements           : {rapport['total_amendements']}")
    print(f"  Tranches              : {rapport['total_tranches']}")
    print(f"  Empreinte du corpus   : {rapport['empreinte_corpus']}")
    print(
        "\n  L'empreinte du corpus doit être IDENTIQUE entre le run à blanc et "
        "le run --apply.\n  C'est la preuve que la migration n'a rien changé au "
        "contenu."
    )

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  Rapport JSON → {args.out_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
