#!/usr/bin/env python3
"""
migrer_identite_couverture_539.py — Met le corpus publié à la forme de #539.

Script de maintenance, pas une étape du pipeline : il s'exécute une fois, son
résultat est committé, et il reste dans le dépôt pour être **relu** — comme
`build_correspondance_acteurs_an.py` (#525). Aucun appel réseau.

## Pourquoi une migration, et pas une simple régénération

Les 20 `id` divergents appartiennent à des profils que le pipeline ne
régénère plus. 19 sont des sénateurs, sans source depuis #528 ; le vingtième
(`jordan-bardella`) repartait à chaque run avec `europarl:131580` parce que
`generate_all_profiles` appelait `normalize_europarl` sans lui passer le slug —
corrigé dans le même lot, mais la correction ne réécrit que les profils qu'un
run touche. Attendre une régénération laisserait le corpus incohérent
indéfiniment.

Trois écritures, et pas une de plus :

1. **`id` = nom de fichier**, sans préfixe de source (#487, #539). 20 profils
   sur 476 — 19 en `nosdeputes:<slug>`, 1 en `europarl:131580`.
2. **`identifiants`** — le bloc de #539, alimenté par la table committée
   `raw_data/correspondance_acteurs_an.json` pour `an`/`senat`/`europarl` et
   par `identite.uri_hatvp` du profil lui-même pour `hatvp`.
3. **`couverture`** — dérivée par `couverture_profil`, jamais fusionnée.

Plus une quatrième, dans les fiches de groupe, et elle est **indissociable** :
`group_profile.py:286` recopie `membre_id` depuis l'`id` du profil. Réécrire
les `id` sans réécrire les 19 `membre_id` correspondants laisserait
`groupe-Senat-LR.json` et `groupe-Senat-SER.json` pointer sur des identités qui
n'existent plus. Les deux se font dans la même passe, ou pas du tout.

## Ce qu'il ne fait pas

- **Aucun fichier n'est renommé.** La régularisation porte sur le champ `id`,
  jamais sur un nom de fichier : renommer un fichier publié est une
  suppression, que `audit_diff_profils` bloque (#460/#470).
- **Aucun slug n'est re-dérivé.** La règle de fabrication vaut à la première
  publication seulement. Re-dériver depuis l'état civil AN renommerait 7
  fichiers — les 7 `ecart` de la table — pour zéro gain.
- **`identite.uri_hatvp` n'est pas réparé.** 186 des 476 profils y portent le
  marqueur XML brut d'AMO30 (`{"@xsi:nil": "true"}`) au lieu d'un `null` :
  c'est un défaut de la collecte d'identité, en amont, et sa correction est un
  autre lot. Ce script ne recopie dans `identifiants.hatvp` que les **279**
  vraies URI.

## Usage

    python src/migrer_identite_couverture_539.py --verifier   # ne réécrit rien
    python src/migrer_identite_couverture_539.py              # écrit

Idempotent : une seconde passe ne modifie plus aucun fichier, hors
`constate_le` de la couverture si le jour a changé (`--constate-le` le fige).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import correspondance_acteurs_an  # noqa: E402
import couverture_profil  # noqa: E402
from candidate_profile import nb_acteurs_referentiel_charge  # noqa: E402
from json_io import ecrire_profil_json  # noqa: E402
from normalize_profil import _uri_hatvp_publiable  # noqa: E402
from schema_pivot import ORDRE_IDENTIFIANTS, validate_profil  # noqa: E402

SUFFIXE_PIVOT = ".pivot.json"


def _profils_publies(profiles_dir: Path) -> list[Path]:
    """Profils pivot publiés, dotfiles exclus.

    `Path.glob` renvoie les fichiers cachés, contrairement au module `glob` :
    c'est ce qui a fait lire `.generation_checkpoint.json` comme un profil et
    bloqué un commit de 476 profils corrects (#518).
    """
    return sorted(
        chemin for chemin in profiles_dir.glob(f"*{SUFFIXE_PIVOT}")
        if not chemin.name.startswith(".")
    )


def _identifiants_pour(
    slug: str, profil: dict[str, Any], table: dict[str, dict[str, Any]]
) -> dict[str, Optional[str]]:
    """Bloc `identifiants` d'un profil publié.

    La table committée fait autorité pour `an`, `senat` et `europarl` : c'est
    elle qui est relue et prouvée. `hatvp` est repris du profil quand la table
    ne le porte pas — même source (le référentiel AN), et ne pas le publier
    quand on le connaît serait une donnée perdue, pas une donnée manquante.
    """
    entree = table.get(slug) or {}
    depuis_table = dict(entree.get("identifiants") or {})
    identifiants: dict[str, Optional[str]] = {}
    for cle in ORDRE_IDENTIFIANTS:
        identifiants[cle] = depuis_table.get(cle)
    if identifiants["hatvp"] is None:
        identifiants["hatvp"] = _uri_hatvp_publiable(
            (profil.get("identite") or {}).get("uri_hatvp")
        )
    return identifiants


def migrer_profils(
    profiles_dir: Path,
    table: dict[str, dict[str, Any]],
    *,
    constate_le: Optional[str],
    ecrire: bool,
) -> dict[str, Any]:
    """Applique les trois écritures aux profils publiés et renvoie les mesures."""
    sante = couverture_profil.SanteReferentiel(nb_acteurs_referentiel_charge())
    mesures: dict[str, Any] = {
        "profils": 0, "id_reecrits": [], "identifiants_ajoutes": 0,
        "couverture_ajoutee": 0, "modifies": 0, "invalides": [],
        "identifiants_renseignes": {cle: 0 for cle in ORDRE_IDENTIFIANTS},
        "sante_referentiel": sante.preuve,
    }

    for chemin in _profils_publies(profiles_dir):
        slug = chemin.name[: -len(SUFFIXE_PIVOT)]
        profil = json.loads(chemin.read_text(encoding="utf-8"))
        mesures["profils"] += 1
        avant = json.dumps(profil, ensure_ascii=False, sort_keys=True)

        if profil.get("id") != slug:
            mesures["id_reecrits"].append((slug, profil.get("id")))
            profil["id"] = slug

        if "identifiants" not in profil:
            mesures["identifiants_ajoutes"] += 1
        profil["identifiants"] = _identifiants_pour(slug, profil, table)
        for cle, valeur in profil["identifiants"].items():
            if valeur is not None:
                mesures["identifiants_renseignes"][cle] += 1

        if "couverture" not in profil:
            mesures["couverture_ajoutee"] += 1
        couverture_profil.appliquer(
            profil,
            constate_le=constate_le,
            fait_hors_an=couverture_profil.etablir_fait_hors_an(table.get(slug), sante),
        )

        erreurs = validate_profil(profil)
        if erreurs:
            mesures["invalides"].append((slug, erreurs))
            continue

        if json.dumps(profil, ensure_ascii=False, sort_keys=True) == avant:
            continue
        mesures["modifies"] += 1
        if ecrire:
            ecrire_profil_json(chemin, profil)

    return mesures


def migrer_groupes(groupes_dir: Path, *, ecrire: bool) -> dict[str, Any]:
    """Réécrit les `membre_id` préfixés des fiches de groupe.

    Indissociable de la réécriture des `id` : `group_profile.py:286` recopie
    `membre_id` depuis l'`id` du profil, donc les deux décrivent la même
    identité. Le préfixe est retiré exactement comme le fait déjà, sans le
    dire, le seul lecteur qui l'ait jamais lu (`group_profile.py:1400`).
    """
    mesures: dict[str, Any] = {"fichiers": 0, "membre_id_reecrits": 0, "detail": {}}
    for chemin in sorted(groupes_dir.glob("*.json")):
        if chemin.name.startswith("."):
            continue
        groupe = json.loads(chemin.read_text(encoding="utf-8"))
        reecrits = 0
        for membre in groupe.get("membres") or []:
            membre_id = membre.get("membre_id")
            if isinstance(membre_id, str) and ":" in membre_id:
                membre["membre_id"] = membre_id.split(":", 1)[1]
                reecrits += 1
        premier = (groupe.get("premier_ministre") or {}) if isinstance(
            groupe.get("premier_ministre"), dict) else {}
        membre_id = premier.get("membre_id")
        if isinstance(membre_id, str) and ":" in membre_id:
            premier["membre_id"] = membre_id.split(":", 1)[1]
            reecrits += 1
        if not reecrits:
            continue
        mesures["fichiers"] += 1
        mesures["membre_id_reecrits"] += reecrits
        mesures["detail"][chemin.name] = reecrits
        if ecrire:
            # `indent=2`, sans saut de ligne final : la forme exacte
            # qu'écrit `group_profile.py:1512`. Un `\n` ajouté ici ferait voir à
            # git une différence de plus qu'il n'y en a.
            chemin.write_text(
                json.dumps(groupe, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    return mesures


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--profiles-dir", default="pivot_data/profiles", type=Path)
    parser.add_argument("--groupes-dir", default="pivot_data/groupes", type=Path)
    parser.add_argument("--correspondance", default=None, type=Path)
    parser.add_argument(
        "--constate-le", default=None,
        help="Date ISO écrite dans `couverture[].constate_le` (défaut : aujourd'hui). "
             "La figer rend la passe reproductible.",
    )
    parser.add_argument(
        "--verifier", action="store_true",
        help="N'écrit rien : mesure ce que la migration changerait.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    ecrire = not args.verifier

    table = correspondance_acteurs_an.charger_correspondance(args.correspondance)
    profils = migrer_profils(
        args.profiles_dir, table, constate_le=args.constate_le, ecrire=ecrire
    )
    groupes = migrer_groupes(args.groupes_dir, ecrire=ecrire)

    mode = "écrit" if ecrire else "simulé (--verifier)"
    print(f"Migration #539 — {mode}")
    print(f"  Profils lus            : {profils['profils']}")
    print(f"  `id` réécrits          : {len(profils['id_reecrits'])}")
    for slug, ancien in profils["id_reecrits"]:
        print(f"      {ancien}  →  {slug}")
    print(f"  Bloc `identifiants` posé : {profils['identifiants_ajoutes']} nouveau(x)")
    for cle, nb in profils["identifiants_renseignes"].items():
        print(f"      {cle:<9}: {nb} renseigné(s)")
    print(f"  Bloc `couverture` posé   : {profils['couverture_ajoutee']} nouveau(x)")
    print(f"  Profils modifiés         : {profils['modifies']}")
    print(f"  Santé du référentiel     : {profils['sante_referentiel']}")
    print(f"  Fiches de groupe         : {groupes['fichiers']} fichier(s), "
          f"{groupes['membre_id_reecrits']} `membre_id` réécrit(s)")
    for nom, nb in groupes["detail"].items():
        print(f"      {nom} : {nb}")

    if profils["invalides"]:
        print(f"\n[!] {len(profils['invalides'])} profil(s) invalide(s) APRÈS migration, "
              "non écrit(s) :", file=sys.stderr)
        for slug, erreurs in profils["invalides"][:10]:
            print(f"    {slug} : {erreurs[0]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
