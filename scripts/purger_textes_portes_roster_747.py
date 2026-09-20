#!/usr/bin/env python3
"""
purger_textes_portes_roster_747.py — Retire les `textes_portes` résiduels des
profils de roster dont la collecte déclare ne pas demander cette liste (#747).

Le résidu et sa date
--------------------
Les 15 profils concernés sont **tous les 15** présents dans le snapshot du
16/08/2026 07:55 UTC, quand le corpus comptait 48 profils : ils ont été
collectés par `extract-roster-groupes` en mode plein. Le commit `a9f24d66`
(16/08 13:16 UTC, #357) a ensuite posé `--skip-dossiers-legislatifs` **en dur**
sur ce job. Depuis, aucun profil de roster écrit ne porte une seule entrée, et
613 des 628 membres de roster publient `textes_portes: []`.

La fusion additive (« une collecte vide n'écrase jamais ») les a conservés :
la liste neuve est **vide**, pas incomplète, donc les reports de #689
(`nature_texte`) et #743 (`sort`) n'ont aucune clé sur quoi se poser. Les 49
entrées portent donc `sort: null` ET `sort_non_resolu: null` — une absence sans
cause déclarée, que §2 règle 5 refuse.

Pourquoi purger et non réparer
------------------------------
Réparer produirait un `sort` qu'aucun run ne rafraîchirait jamais, la collecte
de cette liste étant coupée en dur sur ce job : sur un dossier
`navette_en_cours`, ce sort figé deviendrait faux en silence à mesure que le
texte avance. Rien n'est perdu du corpus — 9 des 44 dossiers sont déjà publiés
avec un `statut` résolu sur une fiche de gouvernement, calculé par la même
`_determine_statut()`, et 34 sont dans `commissions_dossiers.json`.

Les deux étages, pas le seul brut
---------------------------------
Leçon de #729/#730 : une suppression qui ne passe qu'un étage se fait rejouer
par l'autre. `normalize_profil` dérive `textes_portes` de
`dossiers_legislatifs` côté brut ; purger le seul pivot laisserait la prochaine
passe `--pivot-only` les réécrire. Les deux étages sont donc traités ici, et
c'est ce que `--verifier` recompte.

**Mais le critère ne se transpose pas d'un étage à l'autre**, et l'appliquer
tel quel au brut détruirait de la donnée publiée. `meta.provenance` est un
champ du PIVOT : le brut ne le porte pas. Reste `meta.collecte_ecartee`, que le
brut porte bien — et qui ne discrimine rien ici, parce qu'un candidat déclaré
est aussi un membre de roster : le job roster réécrit son `meta`, et 4 des 13
candidats déclarés publient donc `collecte_ecartee: ["textes_portes"]` tout en
portant des `textes_portes` pleinement qualifiés, collectés par `extract-an`.
Le critère brut seul aurait purgé **71 dossiers sur 4 fiches candidats
publiées** (gabriel-attal 34, marine-le-pen 23, laurent-wauquiez 9,
jerome-guedj 5).

D'où la forme retenue : les slugs cibles sont établis **une fois**, sur le
pivot, seul étage qui sache dire de quelle population relève un profil ; les
deux étages sont ensuite purgés sur cette liste. Un étage ne redécide jamais
seul de ce qu'il supprime.

Cible : la **liste vide**, jamais la clé retirée — c'est la forme que portent
déjà les 613 autres membres de roster, et une clé absente dirait « jamais
collecté » là où `[]` dit « rien à publier ».

Un seul passage suffit : la fusion étant additive sur une liste neuve vide,
rien ne recrée ces entrées au run suivant.

Usage
-----
    python3 scripts/purger_textes_portes_roster_747.py --dry-run
    python3 scripts/purger_textes_portes_roster_747.py
    python3 scripts/purger_textes_portes_roster_747.py --verifier
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from json_io import ecrire_profil_json  # noqa: E402

#: La liste métier, et son nom à chaque étage. `normalize_profil` fait la
#: correspondance ; la purge doit la refaire, sinon elle ne passe qu'un étage.
LISTE_PIVOT = "textes_portes"
LISTE_BRUTE = "dossiers_legislatifs"

#: Le critère de sélection, et rien d'autre : un profil de roster dont la
#: collecte a DÉCLARÉ ne pas demander cette liste (`meta.collecte_ecartee`,
#: #539) n'a pas à la porter. Cibler « les entrées sans sort » aurait décrit le
#: symptôme du jour ; celui-ci décrit la contradiction, et vaudra encore si un
#: résidu réapparaît par un autre chemin.
PROVENANCE_CIBLE = "roster_groupe"


def _slugs_cibles(racine: Path) -> list[str]:
    """Les slugs à purger, établis sur le PIVOT et sur lui seul.

    Le pivot est le seul étage qui porte `meta.provenance` — voir le
    docstring du module pour ce que coûterait de laisser le brut décider.
    """
    cibles: list[str] = []
    for chemin in sorted((racine / "pivot_data" / "profiles").glob("*.pivot.json")):
        document = json.loads(chemin.read_text(encoding="utf-8"))
        meta = document.get("meta") or {}
        if meta.get("provenance") != PROVENANCE_CIBLE:
            continue
        if LISTE_PIVOT not in (meta.get("collecte_ecartee") or ()):
            continue
        if not document.get(LISTE_PIVOT):
            continue
        cibles.append(chemin.name.removesuffix(".pivot.json"))
    return cibles


def purger(racine: Path, ecrire: bool) -> dict[str, dict[str, int]]:
    """Vide la liste sur les deux étages. Renvoie le compte par étage."""
    slugs = _slugs_cibles(racine)
    rapport: dict[str, dict[str, int]] = {}
    for etage, chemin_de, liste in (
        ("pivot", lambda s: racine / "pivot_data" / "profiles" / f"{s}.pivot.json",
         LISTE_PIVOT),
        ("brut", lambda s: racine / "raw_data" / "profiles" / f"{s}.json",
         LISTE_BRUTE),
    ):
        fichiers = 0
        entrees = 0
        for slug in slugs:
            chemin = chemin_de(slug)
            if not chemin.exists():
                continue
            document = json.loads(chemin.read_text(encoding="utf-8"))
            if not document.get(liste):
                continue
            fichiers += 1
            entrees += len(document[liste])
            if ecrire:
                document[liste] = []
                ecrire_profil_json(chemin, document)
        rapport[etage] = {"fichiers": fichiers, "entrees": entrees}
    return rapport


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--racine", type=Path, default=RACINE,
                        help="racine du dépôt (défaut : celle du script)")
    parser.add_argument("--dry-run", action="store_true",
                        help="compte sans écrire")
    parser.add_argument("--verifier", action="store_true",
                        help="échoue s'il reste un résidu — c'est le mode du test")
    args = parser.parse_args()

    ecrire = not (args.dry_run or args.verifier)
    rapport = purger(args.racine, ecrire=ecrire)

    total = sum(e["entrees"] for e in rapport.values())
    for etage, compte in rapport.items():
        verbe = "à purger" if not ecrire else "purgé(s)"
        print(f"  {etage:6} : {compte['fichiers']} fichier(s) {verbe}, "
              f"{compte['entrees']} entrée(s)")

    if args.verifier:
        if total:
            print(f"✗ {total} entrée(s) résiduelle(s) sur un profil de roster qui "
                  f"déclare `{LISTE_PIVOT}` écarté (#747).")
            return 1
        print(f"✓ Aucun résidu : tout profil de roster qui déclare `{LISTE_PIVOT}` "
              "écarté publie une liste vide.")
        return 0

    if ecrire:
        # Le total des deux étages compterait chaque fait deux fois : ce sont
        # les mêmes entrées, vues au brut puis au pivot.
        print(f"✓ {rapport['pivot']['entrees']} entrée(s) retirée(s), "
              "sur chacun des deux étages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
