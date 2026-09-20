#!/usr/bin/env python3
"""
gouvernements_amo30.py — La liste des gouvernements, lue dans le référentiel
AMO30 de l'Assemblée nationale au lieu d'être écrite à la main (#996, lot 1).

## Pourquoi

`raw_data/gouvernements_reels.json` a été écrite à la main le 14/08/2026 (#209),
avec les seuls gouvernements dont un ministre avait déjà un profil, et n'a
jamais été reprise. Constat du 17/09/2026 : 7 gouvernements portés par des
profils n'avaient pas de fiche — Lecornu I (15 profils), Valls II (8), Ayrault II
(6), Valls (6), Cazeneuve (6), Ayrault I (5), Fillon I (2).

AMO30 publie chaque gouvernement comme un organe `codeType == "GOUVERNEMENT"`.
Mesuré sur l'archive du 17/08/2026 : **17** organes, de `FILLON 1` (17/05/2007)
à `LECORNU II`. Rien avant 2007 : Raffarin et Villepin n'y sont pas. C'est la
borne de disponibilité, et elle est déclarée dans l'entête du fichier produit.

## Ce qui est lu, et ce qui est écrit

Par organe : `uid` (→ `organe_ref`), `libelleAbrege` (→ `libelle_an`, le libellé
que la collecte écrit dans `mandats[].label` : `"Gouvernement (<libelle_an>)"`),
`viMoDe.dateDebut` et `viMoDe.dateFin` (→ `periode`), **verbatim**. La liste
manuelle déduisait ses dates des mandats observés dans les profils ; la source
les publie. Sur les 10 gouvernements déjà listés, les dates d'AMO30 élargissent
les périodes, sans jamais les rétrécir.

`gouvernement_id`, `fichier` et `nom` reprennent la forme de la liste manuelle,
pour que les 10 fiches existantes gardent leur identifiant et leur fichier :
`FILLON 2` → `gouvernement:FILLON_2`, `gouvernement-FILLON_2.json`,
« Gouvernement Fillon II ». Le `nom` est une mise en forme du libellé de la
source (casse, chiffre romain), pas une information ajoutée : un libellé sans
numéro reçoit « I » seulement si un successeur numéroté existe (`PHILIPPE` →
« Philippe I », `CAZENEUVE` → « Cazeneuve »).

Usage :
    python3 src/gouvernements_amo30.py --out raw_data/gouvernements_reels.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

CODE_TYPE_GOUVERNEMENT = "GOUVERNEMENT"
DEFAULT_SORTIE = Path("raw_data/gouvernements_reels.json")

_ROMAINS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}
_LIBELLE = re.compile(r"^(?P<base>.+?)(?:\s+(?P<num>\d+|[IVX]+))?$")


class GouvernementsIndisponibles(RuntimeError):
    """L'archive AMO30 n'a pas pu être lue : la liste est INCONNUE, pas vide.
    Levée avant toute écriture, pour que la liste committée reste en place."""


def compter_membres(zip_path: Path) -> dict[str, int]:
    """`organe_ref → nombre de personnes distinctes ayant siégé" (#996).

    Le dénominateur de `membres[]` : une fiche peut alors écrire « 2 des 21
    membres recensés » au lieu de « 2 membres ». Personnes distinctes, sur toute
    la vie du gouvernement — un ministre qui change de portefeuille compte une
    fois. Mesuré le 17/09/2026 : 311 personnes sur les 17 gouvernements, de 19
    (Lecornu I) à 55 (Borne).
    """
    from gouvernement_roster_an import construire_index_gouvernements  # noqa: PLC0415

    index = construire_index_gouvernements(zip_path)
    return {
        organe_ref: len({acteur for acteur, _debut, _fin in entrees})
        for organe_ref, entrees in (index.get("mandats") or {}).items()
    }


def lire_organes_gouvernement(zip_path: Path) -> list[dict[str, Any]]:
    """Les organes `GOUVERNEMENT` de l'archive, triés par date de début."""
    organes: list[dict[str, Any]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for nom in zf.namelist():
            if not nom.startswith("json/organe/") or not nom.endswith(".json"):
                continue
            try:
                with zf.open(nom) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, KeyError):
                continue
            organe = data.get("organe") if isinstance(data, dict) else None
            if not isinstance(organe, dict) or organe.get("codeType") != CODE_TYPE_GOUVERNEMENT:
                continue
            uid = organe.get("uid")
            uid = uid.get("#text") if isinstance(uid, dict) else uid
            libelle = (organe.get("libelleAbrege") or "").strip()
            vie = organe.get("viMoDe") or {}
            if not uid or not libelle or not vie.get("dateDebut"):
                continue
            organes.append({
                "organe_ref": uid,
                "libelle_an": libelle,
                "debut": vie.get("dateDebut"),
                "fin": vie.get("dateFin") or None,
            })
    return sorted(organes, key=lambda o: (o["debut"], o["libelle_an"]))


def _decouper(libelle_an: str) -> tuple[str, Optional[int]]:
    m = _LIBELLE.match(libelle_an.strip())
    base, num = m.group("base"), m.group("num")
    if num is None:
        return base, None
    if num.isdigit():
        return base, int(num)
    romains = {v: k for k, v in _ROMAINS.items()}
    return base, romains.get(num)


def nom_gouvernement(libelle_an: str, libelles: Iterable[str]) -> str:
    """« Gouvernement Fillon II » depuis `FILLON 2`, dans le contexte des autres
    libellés (voir la docstring du module pour la règle du « I »)."""
    base, num = _decouper(libelle_an)
    nom = " ".join(p.capitalize() for p in base.split())
    if num is None:
        successeur = any(
            _decouper(autre)[0] == base and _decouper(autre)[1] for autre in libelles
        )
        return f"Gouvernement {nom} I" if successeur else f"Gouvernement {nom}"
    return f"Gouvernement {nom} {_ROMAINS.get(num, str(num))}"


def construire(
    organes: list[dict[str, Any]], membres_recenses: Optional[dict[str, int]] = None
) -> dict[str, Any]:
    """Le document `gouvernements_reels.json`, entête comprise."""
    libelles = [o["libelle_an"] for o in organes]
    entrees = []
    for organe in organes:
        identifiant = organe["libelle_an"].replace(" ", "_")
        entrees.append({
            "gouvernement_id": f"gouvernement:{identifiant}",
            "nom": nom_gouvernement(organe["libelle_an"], libelles),
            "libelle_an": organe["libelle_an"],
            "organe_ref": organe["organe_ref"],
            "periode": {"debut": organe["debut"], "fin": organe["fin"]},
            # Le dénominateur que la fiche publie : combien de personnes l'AN
            # recense dans ce gouvernement, qu'elles aient un profil ou non.
            "membres_recenses": (membres_recenses or {}).get(organe["organe_ref"]),
            "fichier": f"gouvernement-{identifiant}.json",
        })
    return {
        "_meta": {
            "description": (
                "Produit à chaque run par src/gouvernements_amo30.py (#996) : un "
                "gouvernement par organe `GOUVERNEMENT` du référentiel AMO30 de "
                "l'Assemblée nationale. `libelle_an` est `libelleAbrege`, tel que "
                "la collecte l'écrit dans mandats[].label (\"Gouvernement "
                "(<libelle_an>)\") ; `periode` recopie `viMoDe` ; `nom` met le "
                "libellé en forme. Ne pas éditer à la main : le prochain run "
                "réécrit ce fichier."
            ),
            "avertissement": (
                "Couverture : les gouvernements qu'AMO30 publie, soit depuis "
                f"{organes[0]['libelle_an']} ({organes[0]['debut']}) dans l'archive "
                "qui a produit ce fichier. Les gouvernements antérieurs n'y "
                "figurent pas : leur absence ne dit pas qu'ils n'ont pas existé."
            ) if organes else "Aucun organe GOUVERNEMENT lu.",
            "source": "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip",
        },
        "gouvernements": entrees,
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--out", type=Path, default=DEFAULT_SORTIE)
    parser.add_argument("--zip", type=Path, default=None,
                        help="archive AMO30 locale (défaut : cache du pipeline, téléchargée si absente)")
    args = parser.parse_args(argv)

    zip_path = args.zip
    if zip_path is None:
        import candidate_profile  # noqa: PLC0415 — tire requests, comme an_roster

        zip_path = candidate_profile._ensure_acteurs_historique_zip_downloaded()
    if zip_path is None or not Path(zip_path).is_file():
        raise GouvernementsIndisponibles(
            "Archive AMO30 indisponible : la liste des gouvernements est INCONNUE, "
            "pas vide. Le fichier committé est laissé en place.")
    organes = lire_organes_gouvernement(Path(zip_path))
    if not organes:
        raise GouvernementsIndisponibles(
            f"Aucun organe GOUVERNEMENT dans {zip_path} : archive tronquée ou format changé.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(construire(organes, compter_membres(Path(zip_path))),
                   ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"→ {len(organes)} gouvernement(s) écrit(s) dans {args.out}, "
          f"de {organes[0]['libelle_an']} ({organes[0]['debut']}) "
          f"à {organes[-1]['libelle_an']} ({organes[-1]['debut']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
