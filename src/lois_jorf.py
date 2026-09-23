#!/usr/bin/env python3
"""lois_jorf.py — la table `numéro de loi → identifiant JORFTEXT`.

POURQUOI ELLE EXISTE. Les actes réglementaires publient les lois qu'ils
appliquent ou citent par leur identifiant `JORFTEXT`
(`actes_reglementaires.liens_lois`). Les textes promulgués, eux, viennent des
archives de l'Assemblée, qui ne publient **pas** cet identifiant : elles donnent
le numéro de la loi (`2013-595`) et, quand elles l'ont, son NOR — absent sur 412
des 1 015 textes promulgués, toute la XIVe. Joindre par le NOR laisserait donc
40 % des textes sans leurs actes. Cette table fait le pont par le **numéro**,
que les deux sources publient.

CE QU'ELLE EST, ET CE QU'ELLE N'EST PAS. Un référentiel dérivé, committé sous
`raw_data/` comme les index de législatures figées : construit une fois sur le
fonds entier (13 267 lois lues le 23/09/2026, 1 754 numérotées depuis 2007),
puis **tenu à jour par les livraisons que le run lit déjà** — une loi promulguée
paraît dans la livraison du jour, que `actes_reglementaires` parcourt pour les
actes. Aucun appel réseau de plus.

UN NUMÉRO PEUT DÉSIGNER DEUX ENREGISTREMENTS. 106 des 1 754 numéros depuis 2007
apparaissent deux fois dans le fonds : la publication d'origine et un
rectificatif, avec deux `JORFTEXT` et deux dates (`2007-1544` → 30/10/2007 et
10/11/2007). La table garde **les deux**, la plus ancienne d'abord, et le
consommateur qui n'en veut qu'un prend la première : un acte peut citer l'une ou
l'autre, et n'en garder qu'une ferait échouer la jointure sans le dire.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

CHEMIN_PAR_DEFAUT = Path("raw_data") / "lois_jorf.json"
SCHEMA_VERSION = "lois-jorf-v1"

#: Les natures qui entrent dans la table. Une ordonnance n'est pas une loi : elle
#: est un acte, et vit dans `pivot_data/actes_reglementaires/`.
NATURES = ("LOI", "LOI_ORGANIQUE")


def charger(chemin: Path = CHEMIN_PAR_DEFAUT) -> dict[str, list[list[str]]]:
    """La table publiée, ou `{}` — un fichier illisible ne fait pas échouer."""
    try:
        publie = json.loads(Path(chemin).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    lois = publie.get("lois") if isinstance(publie, dict) else None
    return lois if isinstance(lois, dict) else {}


def noter(table: dict[str, list[list[str]]], numero: Optional[str], cid: Optional[str],
          date_publi: Optional[str]) -> bool:
    """Ajoute `(cid, date)` sous ce numéro. Rend `True` si la table a changé.

    Idempotent : une loi relue par une redélivrance ne se dédouble pas. Les
    entrées restent triées par date, la publication d'origine en tête.
    """
    if not numero or not cid:
        return False
    entrees = table.setdefault(numero, [])
    if any(e[0] == cid for e in entrees):
        return False
    entrees.append([cid, date_publi or ""])
    entrees.sort(key=lambda e: (e[1], e[0]))
    return True


def resoudre(table: dict[str, list[list[str]]], numero: Optional[str]) -> list[str]:
    """Les identifiants `JORFTEXT` d'un numéro de loi, la plus ancienne d'abord."""
    if not numero:
        return []
    return [cid for cid, _date in table.get(numero) or []]


def ecrire(table: dict[str, list[list[str]]], chemin: Path = CHEMIN_PAR_DEFAUT,
           *, genere_le: Optional[str] = None) -> None:
    """Écrit la table, triée, en JSON indenté — elle se relit à la main."""
    from json_io import dumps_indente, ecrire_index_json  # import tardif : évite un cycle

    ecrire_index_json(
        Path(chemin),
        {
            "schema_version": SCHEMA_VERSION,
            "genere_le": genere_le or __import__("time").strftime("%Y-%m-%dT%H:%M:%S%z"),
            "lois": {numero: table[numero] for numero in sorted(table)},
        },
        dumps_indente,
    )


def depuis_meta(table: dict[str, list[list[str]]], nature: Optional[str], numero: Optional[str],
                cid: Optional[str], date_publi: Optional[str]) -> bool:
    """`noter`, mais seulement si la nature lue est une loi."""
    if nature not in NATURES:
        return False
    return noter(table, numero, cid, date_publi)
