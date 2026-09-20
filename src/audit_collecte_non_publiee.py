#!/usr/bin/env python3
"""
audit_collecte_non_publiee.py — Rapproche ce qui a été COLLECTÉ de ce qui est
PUBLIÉ : tout profil brut de `raw_data/profiles/` doit avoir son pivot dans
`pivot_data/profiles/` (#511).

**Un troisième angle**, distinct des deux garde-fous déjà branchés avant le
commit, et c'est pourquoi il est un contrôle à part et non une option de l'un
d'eux :

  - `audit_diff_profils` (#460/#470) compare un **avant** et un **après**. Il ne
    voit pas qu'un profil brut n'a jamais eu de pivot : rien n'a été *perdu*,
    les deux compteurs montent, la correspondance seule est absente ;
  - `audit_integrite_referentielle` (#485) vérifie que les clés **publiées**
    résolvent. Il ne dit rien de ce qui a été collecté et n'a jamais été publié :
    ce qui manque ne porte, par définition, aucune clé.

Ce contrôle-ci ne regarde ni la variation ni les clés : il rapproche **deux
comptes** que personne ne rapprochait.

## L'incident

Run `32405297873` (20/08/2026), conclusion **`success`**, commit `68bc094`.
`generate_roster_candidats.py` a écrit un roster de 0 candidat après un
`Read timed out`, et la passe
`generate_all_profiles.py --pivot-only --candidats raw_data/roster_candidats.json`
a itéré sur le vide.

Mesuré sur `68bc094` : **229 profils bruts, 209 pivots**. Les 20 membres
collectés par ce run — jusqu'à 3 536 votes et 124 mandats chacun — ne sont
publiés nulle part. Aucun signal.

`generate_roster_candidats.py` a été corrigé (#511) et ne peut plus écrire un
roster incomplet. Ce contrôle-ci existe parce que la correction ne protège que
**ce chemin** : la classe entière — « une passe qui itère sur moins que ce que
le run a collecté » — reste ouverte partout ailleurs. `--limit` mal propagé,
liste de candidats tronquée, shard de pivot en échec produisent le même silence.

## Ce qui bloque, et pourquoi le seuil est 0

**Bloque** : tout `raw_data/profiles/<slug>.json` sans
`pivot_data/profiles/<slug>.pivot.json`.

Un profil brut est toujours normalisable, et ce n'est pas une hypothèse :
`generate_all_profiles.process_candidat` **n'écrit rien** quand la collecte ne
rend ni identité française ni mandat européen (statut `introuvable`, retour
avant `ecrire_profil_json`). Et un brut à `chambre: null` porte forcément un
`mandat_europeen` — c'est la seule branche qui produit ce cas
(`build_minimal_profile`) — donc `normalize_europarl` lui rend un pivot. Un
brut sans pivot ne signifie donc jamais « rien à publier » : il signifie
**« jamais présenté à une passe pivot »**.

Seuil **0**, mesuré et non arrondi. Population : les 12 commits produits par un
run `generate-data` entre `604c8d6` (16/08/2026) et `e82406a` (20/08/2026),
relevés par `git ls-tree` sur les deux répertoires.

| Commit | Bruts | Pivots | Bruts sans pivot |
| --- | ---: | ---: | ---: |
| `604c8d6` → `e82406a` (12 commits) | 48 → 209 | 48 → 209 | **0** |
| `68bc094` (l'incident) | 229 | 209 | **20** |

Le corpus a triplé sur la période (48 → 209 profils, +20 par run pendant le
rollout roster) sans jamais produire un seul écart : ce n'est pas une valeur
basse, c'est une **invariance**. Un seuil non nul n'aurait donc aucune mesure
pour le fonder — et laisserait passer, à pleine échelle, la perte de plusieurs
centaines de membres.

Un treizième commit de la période, `acfc0a4`, montre 42 écarts : ce n'est **pas**
un run CI mais un commit local intermédiaire (`scripts/generate_data_local.sh`
interrompu entre l'extraction et le pivot). Il ne fait pas partie de la
population que ce contrôle surveille — il tourne dans `merge-and-pivot`, après
les deux passes pivot — et les 42 avaient bien leur pivot au commit suivant.

**Rapporté sans bloquer** : un pivot sans profil brut. À 0 aujourd'hui, mais
légitime — rien ne supprime un pivot dont le brut aurait été retiré du dépôt.
Compteur de dérive, jamais un verdict (même raisonnement que les entrées
d'index jamais référencées de #485).

## Dimensionnement

Ce contrôle **ne parse aucun profil**. Il compare deux listes de noms de
fichiers, et c'est la seule façon de le faire à mémoire bornée : les profils
bruts pèsent 1 642 Mo à 229 profils (médiane 7,4 Mo, maximum 26,5 Mo), et
parser le plus gros coûterait à lui seul plus que le plafond de 236 Mio acté par
#460. Une classification par contenu — « ce brut était-il normalisable ? » —
aurait exigé cette lecture ; la propriété démontrée plus haut la rend inutile.

Conséquence : la RSS ne dépend ni du volume des profils ni de leur nombre, et
le passage à 752 membres ne multiplie que la longueur de deux listes de chaînes.
Mesures dans docs/decisions/collecte-non-publiee.md.

Usage :
    python3 src/audit_collecte_non_publiee.py
    python3 src/audit_collecte_non_publiee.py --raw-dir raw_data/profiles \\
        --pivot-dir pivot_data/profiles --out audit/collecte.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import gha

#: Suffixe d'un profil brut et d'un profil pivot. Le second est plus long et
#: contient le premier : c'est pourquoi le dépouillement se fait par `removesuffix`
#: sur le suffixe attendu du répertoire lu, et jamais par `Path.stem`, qui
#: rendrait `<slug>.pivot` pour un pivot.
SUFFIXE_BRUT = ".json"
SUFFIXE_PIVOT = ".pivot.json"

#: Écarts tolérés avant blocage. **0**, et la valeur est justifiée par la mesure
#: du docstring de module, pas choisie ronde : sur les 12 commits de run de la
#: période 16-20/08/2026, l'écart observé est 0 à chaque fois, pendant que le
#: corpus passait de 48 à 209 profils.
SEUIL_NON_PUBLIES = 0

#: Nombre de slugs nommés dans le rapport et sur stderr. Au-delà, les compteurs
#: suffisent : 543 lignes identiques n'aideraient personne, là où le total et
#: quelques noms rendent le constat vérifiable à la main.
PLAFOND_EXEMPLES = 20


def _slugs(repertoire: Path, suffixe: str) -> set[str]:
    """Slugs présents dans un répertoire, d'après les seuls NOMS de fichiers.

    Aucun fichier n'est ouvert. C'est ce qui rend ce contrôle indépendant du
    volume du corpus — 1 642 Mo de profils bruts aujourd'hui — et donc utilisable
    avant le commit, là où un contrôle qui meurt est pire qu'un contrôle absent.
    """
    if not repertoire.is_dir():
        return set()
    slugs = set()
    for chemin in repertoire.iterdir():
        nom = chemin.name
        if not chemin.is_file() or not nom.endswith(suffixe):
            continue
        # Un fichier de service n'est pas un profil. `slugify` ne produit que
        # `[a-z0-9-]` puis `.strip("-")` : un slug ne peut pas commencer par un
        # point, donc écarter les fichiers cachés n'écarte aucun profil — c'est
        # une propriété du générateur de noms, pas une liste d'exceptions à
        # tenir à jour. Sans cela, `raw_data/profiles/.generation_checkpoint.json`
        # — le point de sauvegarde de `generate_all_profiles.py`, écrit dans le
        # répertoire des profils — se présentait ici comme un brut sans pivot et
        # annulait le commit : run `32773067295` (24/08/2026), 22 jobs verts,
        # `Slug(s) : .generation_checkpoint`. La cause est traitée à part
        # (`--no-checkpoint` sur les passes `--pivot-only`) ; ce filtre-ci rend
        # le contrôle indépendant de tout fichier de service futur.
        if nom.startswith("."):
            continue
        # Un brut ne doit pas être confondu avec un pivot égaré dans le même
        # répertoire : `.pivot.json` se termine aussi par `.json`.
        if suffixe == SUFFIXE_BRUT and nom.endswith(SUFFIXE_PIVOT):
            continue
        slugs.add(nom[: -len(suffixe)])
    return slugs


def auditer(
    raw_dir: Path,
    pivot_dir: Path,
    *,
    seuil: int = SEUIL_NON_PUBLIES,
    plafond_exemples: int = PLAFOND_EXEMPLES,
) -> dict[str, Any]:
    """Rapproche les deux répertoires tels qu'ils sont sur le disque.

    Pas de git ici, comme dans `audit_integrite_referentielle` et contrairement
    à `audit_diff_profils` : ce contrôle porte sur UN état, celui qu'on
    s'apprête à committer, et n'a pas de point de comparaison dans le temps.
    """
    bruts = _slugs(raw_dir, SUFFIXE_BRUT)
    pivots = _slugs(pivot_dir, SUFFIXE_PIVOT)

    non_publies = sorted(bruts - pivots)
    publies_sans_brut = sorted(pivots - bruts)

    # `raw_dir` absent : ce n'est pas « 0 écart », c'est un contrôle qui n'a rien
    # regardé. Le distinguer plutôt que rendre un rapport vert (AGENTS.md §2
    # règle 5) — c'est précisément la faute que ce contrôle traque.
    repertoire_brut_absent = not raw_dir.is_dir()
    repertoire_pivot_absent = not pivot_dir.is_dir()

    return {
        "raw_dir": str(raw_dir),
        "pivot_dir": str(pivot_dir),
        "repertoire_brut_absent": repertoire_brut_absent,
        "repertoire_pivot_absent": repertoire_pivot_absent,
        "nb_bruts": len(bruts),
        "nb_pivots": len(pivots),
        "nb_non_publies": len(non_publies),
        "non_publies": non_publies[:plafond_exemples],
        "non_publies_complets": non_publies,
        "nb_publies_sans_brut": len(publies_sans_brut),
        "publies_sans_brut": publies_sans_brut[:plafond_exemples],
        "plafond_exemples": plafond_exemples,
        "seuil": seuil,
        "bloquant": (
            len(non_publies) > seuil
            or repertoire_brut_absent
            or repertoire_pivot_absent
        ),
    }


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    """Rapport Markdown, joint au résumé de job à chaque run."""
    lignes = [
        "# Collecté mais non publié",
        "",
        "> Tout profil brut a-t-il son pivot ? Troisième angle, distinct du "
        "contrôle de perte (#460/#470 — un avant et un après) et de l'intégrité "
        "référentielle (#485 — les clés publiées résolvent-elles). Ni l'un ni "
        "l'autre ne voit un profil collecté qui n'a **jamais** été publié.",
        "",
        "| Population | Nombre |",
        "| --- | ---: |",
        f"| Profils bruts (`{rapport['raw_dir']}`) | {rapport['nb_bruts']} |",
        f"| Profils pivots (`{rapport['pivot_dir']}`) | {rapport['nb_pivots']} |",
        f"| **Collectés mais non publiés** | **{rapport['nb_non_publies']}** |",
        f"| Publiés sans brut (non bloquant) | {rapport['nb_publies_sans_brut']} |",
        "",
    ]

    if rapport["repertoire_brut_absent"] or rapport["repertoire_pivot_absent"]:
        manquant = ("répertoire des profils bruts"
                    if rapport["repertoire_brut_absent"]
                    else "répertoire des pivots")
        lignes += [
            f"**Le {manquant} est absent.** Un rapprochement qui n'a rien lu "
            "n'est pas un rapprochement vert.",
            "",
        ]
    elif rapport["nb_non_publies"] > rapport["seuil"]:
        lignes += [
            f"**{rapport['nb_non_publies']} profil(s) collecté(s) et publié(s) "
            f"nulle part** (seuil : {rapport['seuil']}). Chacun a un profil brut "
            "complet — identité, mandats, votes — et aucun pivot : la donnée "
            "existe sur le disque et n'atteint aucune vue.",
            "",
        ]
    else:
        lignes += [
            f"**Tout ce qui est collecté est publié** : {rapport['nb_bruts']} "
            "profil(s) brut(s), autant de pivots.",
            "",
        ]

    if rapport["non_publies"]:
        lignes += ["## Collectés mais non publiés", ""]
        lignes += [f"- `{slug}`" for slug in rapport["non_publies"]]
        reste = rapport["nb_non_publies"] - len(rapport["non_publies"])
        if reste > 0:
            lignes.append(f"- … et {reste} autre(s), non détaillé(s).")
        lignes.append("")

    if rapport["publies_sans_brut"]:
        lignes += [
            "## Publiés sans profil brut (non bloquant)",
            "",
            "Légitime : rien ne supprime un pivot dont le brut aurait été retiré "
            "du dépôt. Compteur de dérive, jamais un verdict.",
            "",
        ]
        lignes += [f"- `{slug}`" for slug in rapport["publies_sans_brut"]]
        reste = rapport["nb_publies_sans_brut"] - len(rapport["publies_sans_brut"])
        if reste > 0:
            lignes.append(f"- … et {reste} autre(s), non détaillé(s).")
        lignes.append("")

    lignes += [
        "## Hors périmètre de ce contrôle",
        "",
        "- le **contenu** d'un pivot : seule son existence est rapprochée. Un "
        "pivot vide résout ici, et c'est le contrôle de perte qui le voit ;",
        "- les couches agrégées (`groupes/`, `partis/`, `gouvernements/`), qui "
        "n'ont pas de brut à rapprocher un pour un ;",
        "- la **raison** pour laquelle un profil n'a pas été publié : le contrôle "
        "nomme les slugs, le journal de la passe pivot dit ce qu'elle a itéré.",
        "",
    ]
    return "\n".join(lignes)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--raw-dir", default="raw_data/profiles", metavar="REP",
                        help="Répertoire des profils bruts (défaut : raw_data/profiles).")
    parser.add_argument("--pivot-dir", default="pivot_data/profiles", metavar="REP",
                        help="Répertoire des profils pivots (défaut : pivot_data/profiles).")
    parser.add_argument("--out", metavar="FICHIER", help="Rapport Markdown.")
    parser.add_argument("--out-json", metavar="FICHIER", help="Rapport JSON.")
    parser.add_argument(
        "--seuil", type=int, default=SEUIL_NON_PUBLIES, metavar="N",
        help=f"Profils collectés et non publiés tolérés (défaut : {SEUIL_NON_PUBLIES}). "
             "La valeur par défaut est mesurée, pas arrondie : 0 écart sur les 12 "
             "commits de run du 16 au 20/08/2026, pendant que le corpus passait de "
             "48 à 209 profils.",
    )
    parser.add_argument(
        "--tolerer-non-publies", action="store_true",
        help="Ne pas sortir en erreur malgré des profils non publiés. DISTINCT "
             "de --tolerer-pertes (audit_diff_profils) et de --tolerer-orphelins "
             "(audit_integrite_referentielle) : les trois tolérances restent "
             "cloisonnées, désarmer l'une ne doit jamais désarmer les autres (#470).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    raw_dir = Path(args.raw_dir)
    pivot_dir = Path(args.pivot_dir)

    print(f"→ collecté/publié : {raw_dir} ↔ {pivot_dir}…", file=sys.stderr)
    rapport = auditer(raw_dir, pivot_dir, seuil=args.seuil)
    markdown = generate_markdown_report(rapport)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"→ Rapport écrit : {args.out}", file=sys.stderr)
    else:
        print(markdown)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if rapport["repertoire_brut_absent"]:
        print(f"[!] {raw_dir} est absent : rien n'a été rapproché.", file=sys.stderr)
        gha.annoter("error", f"COLLECTE_NON_PUBLIEE — {raw_dir} est absent : "
                             "rien n'a été rapproché.")
    if rapport["repertoire_pivot_absent"]:
        print(f"[!] {pivot_dir} est absent : rien n'a été rapproché.", file=sys.stderr)
        gha.annoter("error", f"COLLECTE_NON_PUBLIEE — {pivot_dir} est absent : "
                             "rien n'a été rapproché.")

    if rapport["nb_publies_sans_brut"]:
        print(f"  {rapport['nb_publies_sans_brut']} pivot(s) sans profil brut "
              "(non bloquant).", file=sys.stderr)

    if rapport["bloquant"]:
        for slug in rapport["non_publies"]:
            print(f"[!] {slug} : profil brut collecté, aucun pivot publié.",
                  file=sys.stderr)
        reste = rapport["nb_non_publies"] - len(rapport["non_publies"])
        if reste > 0:
            print(f"[!] … et {reste} autre(s), non détaillé(s).", file=sys.stderr)
        resume = (f"{rapport['nb_non_publies']} profil(s) collecté(s) sur "
                  f"{rapport['nb_bruts']} ne sont publiés nulle part "
                  f"(seuil : {rapport['seuil']}).")
        print(f"[!] {resume}", file=sys.stderr)
        # #518 : les slugs partent en annotation, pas seulement en stderr et
        # dans le rapport. Le run 32738726729 (24/08/2026) est mort ici, et
        # `::error::COLLECTE_NON_PUBLIEE` du step ne nommait personne : le
        # Markdown qui les nomme n'existe que dans l'onglet « Summary » du job
        # et dans un artifact — l'un et l'autre invisibles depuis la liste des
        # annotations, et l'artifact expire. UNE annotation, plafonnée par
        # `PLAFOND_EXEMPLES` comme le rapport : 543 annotations identiques
        # noieraient l'onglet au lieu de le renseigner.
        exemples = ", ".join(rapport["non_publies"])
        if reste > 0:
            exemples += f", … (+{reste})"
        # `bloquant` sans aucun slug, c'est le cas « répertoire absent » : il a
        # déjà son annotation ci-dessus, et « Slug(s) : » y serait vide.
        gha.annoter(
            "error" if not args.tolerer_non_publies else "warning",
            f"COLLECTE_NON_PUBLIEE — {resume}"
            + (f" Slug(s) : {exemples}" if exemples else ""),
        )
        return 0 if args.tolerer_non_publies else 1

    print(f"✓ {rapport['nb_bruts']} profil(s) brut(s) collecté(s), "
          f"{rapport['nb_pivots']} pivot(s) publié(s) : rien de collecté ne "
          "reste non publié.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
