#!/usr/bin/env python3
"""
purger_doublons_textes_europeens_901.py — Retire les textes portés européens
publiés deux fois dans un même profil (#901).

Ce que la clé a fait
--------------------
Un texte porté européen n'a pas de `dossier_id`. `_pivot_texte_key` le rangeait
donc sur le **repli** `(titre, date_min, legislature)`, qui contient le titre.
#938 a retiré des titres les libellés des boutons de téléchargement — « … PDF
(181 KB) DOC (45 KB) » —, le repli a changé, et la fusion additive a ajouté au
lieu de reconnaître.

Résultat publié, mesuré le 16/09/2026 sur `origin/main` `c6990c688` : **311
textes en double**, l'exemplaire au titre sale puis le même au titre propre.

| Profil | Doublons | Textes européens publiés → réels |
| --- | ---: | --- |
| `florian-philippot` | 250 | 502 → 252 |
| `marine-le-pen` | 57 | 115 → 58 |
| `jean-luc-melenchon` | 4 | 8 → 4 |

Les 311 paires ne diffèrent que par `titre` et `titre_langue`, et la copie
propre suit toujours la sale dans la liste.

La clé est corrigée dans le même lot : un texte européen est désormais identifié
par son document `doceo`, lu dans `source_url` quel que soit le schéma. Cela
empêche la récidive — mais la fusion additive ne retirera **jamais** ce qui est
déjà publié, et le contrôle de perte bloquerait le run qui essaierait. D'où ce
script, à passer une fois.

Un seul étage, et c'est mesuré
------------------------------
#729 exige qu'une correction qui retire s'applique au brut et au pivot. Ici le
brut n'a rien : ces textes sont posés par `enrich_pivot_with_parltrack`, sur le
profil **pivot**. Vérifié sur les trois profils : aucune adresse `doceo` dans
`raw_data/profiles/`.

Lequel des deux garder
----------------------
**Le dernier rencontré**, qui est le titre propre sur les 311 paires. Ce n'est
pas un choix fait ici : c'est `merge_dossier_records` appelée avec la nouvelle
clé — exactement ce que la fusion fera au prochain run. La reprise avance la
date ; elle ne crée pas un second chemin.

Ce que ce script NE touche pas
------------------------------
- Les textes de l'**Assemblée** : ils portent un `dossier_id`, leur clé ne
  change pas. Mesuré : 0 retiré.
- Les **13** textes européens sans document `doceo` (fiches OEIL, avis sans
  lien) : leur clé ne change pas.
- **Trois titres encore sales, qui ne sont pas des doublons** : chez Philippot
  `B-8-2016-0621` et `B-8-2015-1183`, chez Le Pen `B-8-2016-0621`. Chacun est
  seul sous sa clé — la collecte ne les rend plus, la fusion additive les garde.
  Les nettoyer est un autre geste que retirer un doublon.

Usage
-----
    python3 scripts/purger_doublons_textes_europeens_901.py            # mesure seule
    python3 scripts/purger_doublons_textes_europeens_901.py --ecrire   # applique
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))

from json_io import ecrire_profil_json  # noqa: E402
from merge_profile import _pivot_texte_key, merge_dossier_records  # noqa: E402

PROFILS_PAR_DEFAUT = RACINE / "pivot_data" / "profiles"


def purger(profil: dict) -> tuple[int, int]:
    """Réapplique la fusion par clé sur `textes_portes`. Modifie en place.

    Returns:
        `(retires, restants)`.
    """
    textes = profil.get("textes_portes")
    if not isinstance(textes, list) or not textes:
        return 0, len(textes or [])
    dedoublonnes = merge_dossier_records([], textes, _pivot_texte_key)
    retires = len(textes) - len(dedoublonnes)
    if retires:
        profil["textes_portes"] = dedoublonnes
    return retires, len(dedoublonnes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-dir", type=Path, default=PROFILS_PAR_DEFAUT)
    parser.add_argument("--ecrire", action="store_true",
                        help="applique la purge ; sans ce drapeau, mesure seule")
    args = parser.parse_args(argv)

    total = 0
    touches = 0
    for chemin in sorted(args.profiles_dir.glob("*.json")):
        try:
            with open(chemin, encoding="utf-8") as fh:
                profil = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  [!] {chemin.name} illisible : {exc}")
            continue
        retires, restants = purger(profil)
        if not retires:
            continue
        touches += 1
        total += retires
        print(f"  {chemin.name:34s} {retires:5d} doublon(s) retiré(s), "
              f"{restants} texte(s) porté(s) restant(s)")
        if args.ecrire:
            ecrire_profil_json(chemin, profil)

    verbe = "retirés" if args.ecrire else "à retirer (mesure seule)"
    print(f"\n{total} doublon(s) {verbe}, sur {touches} profil(s).")
    if not args.ecrire and total:
        print("Relancer avec --ecrire pour appliquer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
