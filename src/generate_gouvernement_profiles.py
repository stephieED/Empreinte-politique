#!/usr/bin/env python3
"""
generate_gouvernement_profiles.py — Génère tous les profils de gouvernement
en un seul run, en ne récupérant/chargeant qu'UNE SEULE FOIS le dump des
dossiers législatifs gouvernementaux (réseau) et les profils pivot
individuels (disque), partagés entre tous les gouvernements de
`raw_data/gouvernements_reels.json`.

Miroir de `generate_group_profiles.py` : ce dernier mutualise un fetch réseau
par (chambre, législature) ; ici il n'existe qu'UNE seule source de dossiers
législatifs (le dump AN complet, indépendant de tout gouvernement précis), et
qu'UN seul dossier de profils pivot individuels — donc un seul fetch et un
seul chargement disque pour l'ensemble du batch, quel que soit le nombre de
gouvernements à générer. Ceci évite aussi tout double-comptage d'un texte
entre deux gouvernements requêtés séparément (le même dump filtré par date
serait re-téléchargé et re-parsé à chaque appel autrement) — voir aussi la
note anti double-comptage dans `gouvernement_profile.py`.

La liste des gouvernements à générer est lue depuis un fichier de config JSON
(par défaut `raw_data/gouvernements_reels.json`), validée manuellement.

Usage (depuis la racine du dépôt) :
    python src/generate_gouvernement_profiles.py \\
        --config raw_data/gouvernements_reels.json \\
        --profiles-dir pivot_data/profiles \\
        --out-dir pivot_data/gouvernements \\
        --validate

Les décisions qui gouvernent ce module
--------------------------------------
Cinq le nomment ; la liste complète et à jour est dans
`docs/decisions-par-module.md`. Ces trois-là portent le contrat :

- `docs/decisions/gouvernement-textes-non-ecrasement.md` (#427) — **ne jamais
  réécrire un profil sur une collecte incomplète.** `fetch_dossiers_gouvernementaux`
  est non-fatal et rend `{"dossiers": []}` en cas de coupure ; sans la sentinelle
  `COLLECTE_INCOMPLETE`, l'écriture publiait ce vide comme un fait.
- `docs/decisions/plafond-roster-et-commit-518.md` — pourquoi l'incomplétude
  sort par un **code de retour dédié** (`EXIT_COLLECTE_INCOMPLETE`) et non par un
  échec : le workflow doit pouvoir distinguer « rien à publier » de « le job a
  cassé ».
- `docs/decisions/cloisonnement-branche-roster-524.md` — le même code 2, vu
  depuis la CI : toléré là où il doit l'être, pour qu'une panne de source ne
  transforme pas un run entier en perte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from gouvernement_profile import build_gouvernement_profile
from gouvernement_roster_an import CLE_ROSTER as CLE_ROSTER_GOUVERNEMENTS
from group_roster import charger_rosters_bruts
from gouvernement_roster import charger_profils_et_chemins, lecteur_interventions
from gouvernement_textes import AN_DOSSIERS_ARCHIVES, fetch_dossiers_gouvernementaux
from merge_profile import load_existing_document, preserve_stable_freshness_timestamps
from schema_gouvernement import validate_profil_gouvernement


# Code de retour distinct d'un échec de génération ordinaire (1) : la collecte
# réseau est incomplète, aucun profil n'a été touché. Permet au workflow de
# traiter ce cas comme dégradé-mais-sûr plutôt que comme une régression du
# code (#427).
EXIT_COLLECTE_INCOMPLETE = 2

# Sentinelle retournée par generate_all() quand la collecte est incomplète.
# Un objet dédié, et non l'entier 2 : `generate_all` retourne un COMPTE
# d'échecs, et exactement deux gouvernements en échec aurait été confondu avec
# ce cas.
COLLECTE_INCOMPLETE = object()


def generate_all(
    gouvernements: list[dict[str, Any]],
    profiles_dir: Path,
    out_dir: Path,
    validate: bool = False,
    commissions_par_dossier: Optional[dict[str, Any]] = None,
    membres_roster: Optional[list[dict[str, Any]]] = None,
) -> Any:
    """Génère tous les profils de gouvernement de `gouvernements`, un seul
    chargement des profils pivot et un seul fetch des dossiers législatifs
    gouvernementaux, partagés entre tous les gouvernements. Retourne le
    nombre d'échecs, ou la sentinelle `COLLECTE_INCOMPLETE` si les archives
    de dossiers n'ont pas toutes pu être lues — auquel cas AUCUN profil n'est
    réécrit (#427).

    `membres_roster` (#996 lot 4) : la clé `gouvernements` de
    `rosters_bruts.json`, lue UNE fois pour les 17 fiches. `None` rebranche le
    rattachement par libellé, et les fiches sont produites quand même."""
    # Les profils sont PROJETÉS sur cinq blocs (#635) : `interventions` n'y est
    # pas. `chemins_profils` est ce qui permet de l'aller chercher à la demande,
    # une personne à la fois, pour `tags_thematiques_agreges` (#1020).
    profils, chemins_profils = charger_profils_et_chemins(profiles_dir)
    lire_interventions = lecteur_interventions(chemins_profils)
    print(f"→ {len(profils)} profil(s) pivot chargé(s).", file=sys.stderr)

    print("→ Récupération des dossiers législatifs gouvernementaux…", file=sys.stderr)
    dossiers_result = fetch_dossiers_gouvernementaux()
    dossiers = dossiers_result["dossiers"]
    print(f"→ {len(dossiers)} dossier(s) d'origine gouvernementale récupéré(s).", file=sys.stderr)

    # PROTECTION #427 — ne jamais réécrire les profils sur une collecte
    # incomplète.
    #
    # Ce script ÉCRASE les profils (`write_text` plus bas), il ne les fusionne
    # pas comme `merge_profile.py` le fait pour les profils individuels. Or
    # `fetch_dossiers_gouvernementaux()` est non-fatal en cas de coupure réseau
    # : il rend `dossiers = []` avec un warning. Sans ce garde-fou,
    # `data.assemblee-nationale.fr` indisponible une minute suffisait à
    # réécrire les 10 gouvernements avec `textes: []`, à faire passer le
    # quality gate (qui ne traite ce cas qu'en avertissement), puis à committer
    # et publier la perte — 725 textes au moment de l'écriture de ce garde-fou.
    #
    # Un zéro qui n'a pas été mesuré n'est pas une donnée (AGENTS.md §2.5) : on
    # préfère ne rien réécrire. Les profils déjà committés restent alors en
    # place, intacts, et le run continue pour tout le reste.
    legislatures_attendues = set(AN_DOSSIERS_ARCHIVES)
    legislatures_ingerees = set(dossiers_result.get("legislatures_ingerees") or [])
    manquantes = sorted(legislatures_attendues - legislatures_ingerees)
    if manquantes:
        print(
            f"  [!] Collecte incomplète : archive(s) de dossiers manquante(s) pour "
            f"la ou les législature(s) {manquantes}.",
            file=sys.stderr,
        )
        print(
            "  [!] Aucun profil de gouvernement réécrit — les profils existants "
            "sont conservés tels quels (#427). Relancer une fois la source "
            "de nouveau disponible.",
            file=sys.stderr,
        )
        return COLLECTE_INCOMPLETE

    echecs = 0
    for gouvernement in gouvernements:
        gouvernement_id = gouvernement.get("gouvernement_id")
        periode = gouvernement.get("periode") or {}

        try:
            profil = build_gouvernement_profile(
                gouvernement_id=gouvernement_id,
                nom=gouvernement.get("nom"),
                libelle_an=gouvernement.get("libelle_an") or "",
                periode_debut=periode.get("debut"),
                periode_fin=periode.get("fin"),
                membres_recenses=gouvernement.get("membres_recenses"),
                profils=profils,
                dossiers_gouvernementaux=dossiers,
                commissions_par_dossier=commissions_par_dossier,
                membres_roster=membres_roster,
                organe_ref=gouvernement.get("organe_ref"),
                lire_interventions=lire_interventions,
            )
        except Exception as exc:  # noqa: BLE001 - un échec sur un gouvernement ne doit pas arrêter les autres
            print(f"  [!] Échec de génération pour {gouvernement_id} : {exc}", file=sys.stderr)
            echecs += 1
            continue

        if dossiers_result["warnings"]:
            # Warnings globaux du fetch (téléchargement/parsing), partagés
            # entre tous les gouvernements du batch, pas spécifiques à celui-ci.
            profil["meta"]["warnings"].extend(dossiers_result["warnings"])

        if validate:
            errors = validate_profil_gouvernement(profil)
            if errors:
                print(f"  [!] {len(errors)} erreur(s) de validation pour {gouvernement_id} :", file=sys.stderr)
                for e in errors:
                    print(f"      - {e}", file=sys.stderr)
            else:
                print(f"  ✓ {gouvernement_id} valide selon le schéma.", file=sys.stderr)

        out_path = out_dir / gouvernement["fichier"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # #343 : ne pas faire avancer meta.genere_le / sources[].synchro_le
        # quand le profil régénéré est identique en contenu. Ce script
        # reconstruit sa sortie à chaque exécution sans jamais comparer à la
        # version précédente — sans ça, chaque run produit un diff sur les 10
        # fichiers gouvernement alors que rien n'a changé, ce qui bruite les
        # commits et fausse toute lecture de fraîcheur (AGENTS.md §2).
        profil = preserve_stable_freshness_timestamps(load_existing_document(out_path), profil)
        out_path.write_text(json.dumps(profil, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Profil de gouvernement écrit : {out_path}", file=sys.stderr)

    return echecs


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--config",
        default="raw_data/gouvernements_reels.json",
        metavar="FICHIER",
        help="Fichier JSON listant les gouvernements à générer (défaut : raw_data/gouvernements_reels.json).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Dossier des profils pivot individuels (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--out-dir",
        default="pivot_data/gouvernements",
        metavar="DOSSIER",
        help="Dossier de sortie des profils de gouvernement (défaut : pivot_data/gouvernements).",
    )
    parser.add_argument(
        "--commissions-dossiers",
        default="pivot_data/commissions_dossiers.json",
        metavar="FICHIER",
        help=(
            "Index dossier_id -> commission saisie au fond (#689), d'où les textes "
            "tirent leur matière. Absent, illisible ou vide : chaque texte publie "
            "`commission_non_resolue.motif = index_indisponible` — jamais un silence."
        ),
    )
    parser.add_argument(
        "--rosters-bruts",
        default=None,
        metavar="FICHIER",
        help=(
            "raw_data/rosters_bruts.json du run (#996 lot 4). Sa clé "
            "`gouvernements` rattache les membres par `organe_ref`, au lieu de "
            "comparer `mandats[].label` au libellé de la config — une jointure "
            "de chaînes entre deux sources. Absent ou illisible : le repli par "
            "libellé s'applique et les fiches sont produites quand même."
        ),
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valide chaque profil de gouvernement produit et affiche les erreurs éventuelles.",
    )
    return parser


def charger_membres_roster(chemin: Optional[Path]) -> Optional[list[dict[str, Any]]]:
    """Les membres de gouvernement du roster brut du run, ou `None` (#996 lot 4).

    `None` a un sens précis et un seul : **pas de roster, applique le repli par
    libellé**. Il couvre les quatre façons de ne pas en avoir — option absente,
    fichier absent, fichier illisible, clé `gouvernements` non écrite par ce
    run. Aucune ne fait échouer la génération : la fiche produite par la voie
    fragile vaut mieux que pas de fiche (§2 règle 5, même arbitrage que #427).

    Chaque échec est **dit sur stderr**, jamais absorbé en silence : c'est la
    seule trace qu'un run aura de ce qu'il a rattaché par libellé plutôt que
    par `organe_ref`.
    """
    if chemin is None:
        return None
    try:
        rosters = charger_rosters_bruts(chemin)
    except (OSError, ValueError) as exc:
        print(
            f"  [!] Roster brut illisible ({chemin}) : {exc} — rattachement des "
            "membres par libellé (repli).",
            file=sys.stderr,
        )
        return None
    membres = rosters.get(CLE_ROSTER_GOUVERNEMENTS)
    if not membres:
        print(
            f"  [!] {chemin} ne porte pas de roster de gouvernements — "
            "rattachement des membres par libellé (repli).",
            file=sys.stderr,
        )
        return None
    print(
        f"→ {len(membres)} membre(s) de gouvernement lus dans {chemin} : "
        "rattachement par organe_ref.",
        file=sys.stderr,
    )
    return membres


def charger_commissions_dossiers(chemin: Optional[Path]) -> Optional[dict[str, Any]]:
    """Index `dossier_id` → commission saisie au fond, ou `None` (#689).

    `None` n'est pas une erreur : c'est ce qui fait publier
    `commission_non_resolue.motif = "index_indisponible"` sur chaque texte, au
    lieu d'un silence. Une panne du run et une limite de périmètre ne doivent pas
    se lire pareil — la leçon de #726, où un audit rendait 62 705 lignes parce
    qu'il lisait un champ déplacé.

    Un index **vide** vaut un index absent : le croire disponible ferait passer
    « le fichier manquait » pour « aucun texte n'a de commission » (#510).
    """
    if chemin is None:
        return None
    try:
        with open(chemin, encoding="utf-8") as f:
            charge = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"  [!] Index des commissions saisies au fond illisible ({chemin}) : {exc}. "
            "Les textes porteront `commission_non_resolue.motif = index_indisponible`.",
            file=sys.stderr,
        )
        return None
    commissions = (charge or {}).get("commissions")
    if not isinstance(commissions, dict) or not commissions:
        print(
            f"  [!] Index des commissions saisies au fond vide ({chemin}) : traité comme "
            "absent, et les textes le déclarent (#689).",
            file=sys.stderr,
        )
        return None
    return commissions


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[!] Lecture de {config_path} impossible : {exc}", file=sys.stderr)
        return 1

    gouvernements = config.get("gouvernements") or []
    if not gouvernements:
        print(f"[!] Aucun gouvernement à générer dans {config_path}.", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # #689 — chargé UNE fois pour les dix fiches : l'index pèse 1,2 Mo et
    # 6 024 dossiers, et le relire par gouvernement serait le coût que
    # #392/#403/#467 ont déjà payé trois fois au même endroit.
    commissions_par_dossier = charger_commissions_dossiers(
        Path(args.commissions_dossiers) if args.commissions_dossiers else None
    )
    if commissions_par_dossier is not None:
        print(
            f"  -> Commissions saisies au fond : {len(commissions_par_dossier)} "
            "dossier(s) indexé(s)."
        )

    echecs = generate_all(
        gouvernements,
        profiles_dir=Path(args.profiles_dir),
        out_dir=out_dir,
        validate=args.validate,
        commissions_par_dossier=commissions_par_dossier,
        membres_roster=charger_membres_roster(
            Path(args.rosters_bruts) if args.rosters_bruts else None),
    )

    # Collecte incomplète : aucun profil n'a été écrit, le compteur d'échecs
    # par gouvernement n'a donc aucun sens ici (#427).
    if echecs is COLLECTE_INCOMPLETE:
        print("→ 0 profil de gouvernement réécrit (collecte incomplète).", file=sys.stderr)
        return EXIT_COLLECTE_INCOMPLETE

    print(f"→ {len(gouvernements) - echecs}/{len(gouvernements)} profil(s) de gouvernement généré(s).", file=sys.stderr)
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
