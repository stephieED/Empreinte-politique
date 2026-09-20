#!/usr/bin/env python3
"""
generate_group_profiles.py — Génère plusieurs profils de groupe parlementaire
réel en un seul run, en ne récupérant qu'UNE SEULE FOIS le roster complet de
chaque chambre/législature (au lieu d'un fetch réseau par groupe).

Contexte : la source d'un roster n'expose qu'un seul point d'accès « liste
complète de la chambre » (pas de endpoint par groupe). Générer les 7 groupes
réels validés (5 AN + 2 Sénat) via group_profile.py --from-roster, appelé une
fois par groupe, referait donc 5 fois la même récupération du roster AN (16e
législature) et 2 fois le même roster Sénat. Ce script récupère une fois par
(chambre, législature) distincte puis filtre localement par sigle pour chaque
groupe (voir group_roster.fetch_full_roster / filter_roster_by_sigle).

Depuis #527, la clé `deputes` est dérivée d'AMO30 ; depuis #529, la lecture
NosDéputés qu'elle remplaçait n'existe plus du tout — tout est dans
`group_roster.fetch_full_roster`, rien ici n'a eu à changer pour cela hormis la
liste des erreurs interceptées
(`ERREURS_ROSTER`) : une archive AMO30 absente doit rester un « roster
indisponible » nommé, donc un `exit 2` qui laisse les fiches publiées en
place, et non une trace de pile qui annule le commit du run (#518).

La liste des groupes à générer est lue depuis un fichier de config JSON (par
défaut raw_data/groupes_reels.json), validée manuellement (voir README §6).

Une entrée portant `extraction_suspendue` est ignorée, sans compter comme un
échec : sa fiche de groupe déjà publiée reste en place, gelée à sa dernière
génération réussie (#516, voir groupes_config.py et
docs/decisions/extraction-groupe-suspendue-516.md).

## Le roster du run est réutilisé, pas refetché (#518, second incident)

`--rosters-bruts FICHIER` lit les rosters bruts que `generate_roster_candidats.py
--rosters-bruts-out` a écrits **au début du même run** (transités par l'artifact
`roster-candidats`), au lieu d'en refetcher un pour ce script. Ce n'était pas
qu'une requête de trop : la fiche de groupe était bâtie sur une composition lue
~7 min après celle qui a servi à collecter les profils. Une entrée ou une sortie
de groupe entre les deux, et la composition publiée diverge du corpus collecté,
**sans qu'aucune étape n'échoue**. Une clé absente du fichier retombe sur le
fetch, en le disant.

## Un roster indisponible ne coûte plus le commit du run (#518)

Le run `32750929942` est mort ici : un fetch de roster en timeout, 5 groupes AN
comptés en échec, `exit 1`, et donc `Committer et pousser` skippé — alors
qu'**aucune fiche de groupe n'avait été touchée** et que les ~452 profils de
candidats du run, eux, étaient corrects. Les deux échecs sont désormais
distingués par le code de sortie : `EXIT_ROSTER_INDISPONIBLE` (2) quand tous les
échecs sont « roster indisponible » — rien d'écrit, les fiches committées
restent en place — et `1` quand une génération de groupe a réellement planté.
Même arbitrage que le step gouvernement (#427) : refuser qu'une donnée NON
écrite annule la publication d'une donnée écrite. Ce n'est pas une tolérance :
la section 4 du quality gate continue de hard-failer sur une fiche de groupe
absente ou invalide, et chaque échec part en annotation `::error::` (gha.py).

Usage (depuis la racine du dépôt) :
    python src/generate_group_profiles.py \\
        --config raw_data/groupes_reels.json \\
        --profiles-dir pivot_data/profiles \\
        --out-dir pivot_data/groupes \\
        --rosters-bruts raw_data/rosters_bruts.json \\
        --validate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NamedTuple, Optional

import gha
from group_profile import generate_groupe_profile_from_roster
from group_roster import (
    ERREURS_ROSTER,
    charger_rosters_bruts,
    fetch_full_roster,
    filter_roster_by_sigle,
)
from groupes_config import (
    CHEMIN_CONFIG_GROUPES,
    CorrespondanceSiglesInvalide,
    partitionner_groupes,
    historique_noms_publie,
    position_politique_publiee,
    resume_suspension,
    succession_publiee,
)
from amendements_index import (
    DEFAULT_AMENDEMENTS_DIR,
    charger as charger_amendements,
)
from scrutins_index import DEFAULT_SCRUTINS_PATH, charger as charger_scrutins


# Code de retour distinct d'un échec de génération ordinaire (1) : le roster
# d'au moins une chambre/législature n'a pas pu être obtenu, donc AUCUNE fiche
# de groupe de cette clé n'a été touchée. Même sémantique et même valeur que
# `generate_gouvernement_profiles.EXIT_COLLECTE_INCOMPLETE` (#427), pour que le
# workflow les traite pareil : dégradé-mais-sûr, jamais une régression du code.
EXIT_ROSTER_INDISPONIBLE = 2


class ResultatGeneration(NamedTuple):
    """Ce que `generate_all` a produit, échec par échec — pas un compte agrégé.

    Le compte seul ne distingue pas « le réseau n'a rien rendu » de « le code
    a planté sur ce groupe », et c'est exactement la distinction dont dépendent
    le code de sortie (#518) et le texte de l'annotation.
    """

    #: Groupes dont la génération a levé — un vrai défaut, `exit 1`.
    echecs_generation: list[str]
    #: Clés (chambre, législature) dont le roster n'a pas pu être obtenu.
    cles_indisponibles: list[tuple[str, Optional[str]]]
    #: `groupe_id` sautés faute de roster, par clé indisponible.
    groupes_sautes: dict[tuple[str, Optional[str]], list[str]]

    @property
    def echecs(self) -> int:
        """Nombre total de groupes non régénérés, toutes causes confondues."""
        return len(self.echecs_generation) + sum(len(g) for g in self.groupes_sautes.values())

    def code_sortie(self) -> int:
        """0 si tout est passé, 2 si les seuls échecs sont « roster indisponible ».

        Un échec de génération l'emporte sur un roster indisponible : mélangés,
        le run a un vrai défaut à signaler, et `2` le ferait passer pour un
        simple aléa de source.
        """
        if self.echecs_generation:
            return 1
        return EXIT_ROSTER_INDISPONIBLE if self.groupes_sautes else 0


def _roster_key(groupe: dict[str, Any]) -> tuple[str, Optional[str]]:
    """Clé (roster_chambre, legislature) identifiant un fetch réseau partageable."""
    legislature = groupe.get("legislature") if groupe["roster_chambre"] == "deputes" else None
    return (groupe["roster_chambre"], legislature)


def _libelle_cle(cle: tuple[str, Optional[str]]) -> str:
    chambre, legislature = cle
    return f"{chambre}, législature={legislature or 'courante'}"


def _charger_rosters_du_run(chemin: Optional[Path]) -> dict[tuple[str, Optional[str]], list[dict[str, Any]]]:
    """Rosters bruts déjà collectés par ce run, ou dict vide (chaque clé sera fetchée).

    Un fichier annoncé mais illisible ne fait PAS échouer : il fait retomber
    sur le fetch, en le disant. Le mode dégradé est déjà celui du repli côté
    workflow, et il est préférable à un job rouge — mais il ne doit pas être
    silencieux, sans quoi le transit d'artifact pourrait cesser de fonctionner
    sans que rien ne le signale (#518).
    """
    if chemin is None:
        return {}
    try:
        rosters = charger_rosters_bruts(chemin)
    except (OSError, ValueError) as exc:
        print(
            f"  [!] Rosters bruts du run illisibles ({chemin}) : {exc}. "
            "Ce script refetche pour son propre compte — la composition publiée "
            "peut différer de celle sur laquelle les profils ont été collectés (#518).",
            file=sys.stderr,
        )
        gha.annoter(
            "warning",
            f"ROSTER_BRUT — {chemin} illisible ({exc}) : generate_group_profiles.py "
            "refetche le roster, la composition publiée peut diverger du corpus collecté (#518).",
        )
        return {}
    print(
        f"→ {len(rosters)} roster(s) brut(s) du run réutilisé(s) depuis {chemin} "
        "(aucun fetch pour ces clés).",
        file=sys.stderr,
    )
    return rosters


def generate_all(
    groupes: list[dict[str, Any]],
    profiles_dir: Path,
    out_dir: Path,
    merge_existing: bool = False,
    validate: bool = False,
    scrutins_path: Path = DEFAULT_SCRUTINS_PATH,
    amendements_path: Path = DEFAULT_AMENDEMENTS_DIR,
    rosters_bruts_path: Optional[Path] = None,
    chemin_config: Path = CHEMIN_CONFIG_GROUPES,
) -> ResultatGeneration:
    """Génère tous les profils de groupe de `groupes`, au plus un fetch réseau
    par (roster_chambre, legislature) distincte — et zéro si `rosters_bruts_path`
    porte déjà la clé (#518).

    Retourne un `ResultatGeneration` : le compte seul ne dirait pas si le run a
    manqué de réseau ou de code, et c'est de cette distinction que dépend le
    code de sortie."""
    # Index des scrutins chargé UNE fois pour tous les groupes (#432) : 17 422
    # scrutins, ~8,7 Mo — le relire par groupe multiplierait la lecture par 7
    # pour un contenu identique. Même logique que le fetch de roster partagé
    # ci-dessous.
    scrutins_index = charger_scrutins(Path(scrutins_path))
    if len(scrutins_index) == 0:
        print(
            f"  [!] Index des scrutins vide ou absent ({scrutins_path}) : la cohésion de "
            "vote sortira vide pour tous les groupes (#432).",
            file=sys.stderr,
        )
    else:
        print(f"→ Index des scrutins : {len(scrutins_index)} scrutin(s).", file=sys.stderr)

    # Idem pour l'index des amendements (#431), chargé UNE fois et **sans les
    # cosignatures** : l'agrégat ne lit que `sort` et `type_deposant`, et les
    # cosignatures pèsent 59 % de l'index sans qu'aucun consommateur les lise.
    amendements_index = charger_amendements(
        Path(amendements_path), avec_cosignatures=False
    )
    if len(amendements_index) == 0:
        print(
            f"  [!] Index des amendements vide ou absent ({amendements_path}) : "
            "`amendements_agreges` ne comptera que les entrées portant encore leur "
            "enregistrement (#431).",
            file=sys.stderr,
        )
    else:
        print(f"→ Index des amendements : {len(amendements_index)} amendement(s).", file=sys.stderr)

    # Les rosters déjà collectés par ce run (artifact `roster-candidats`, #518)
    # préremplissent le cache par clé : la boucle ci-dessous ne fetche donc que
    # ce qui manque, sans branche supplémentaire.
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]] = dict(
        _charger_rosters_du_run(rosters_bruts_path)
    )
    echecs_generation: list[str] = []
    groupes_sautes: dict[tuple[str, Optional[str]], list[str]] = {}
    cles_indisponibles: list[tuple[str, Optional[str]]] = []

    # Un groupe à l'extraction suspendue (#516) n'est ni fetché ni régénéré, et
    # ce n'est PAS un échec : sa fiche déjà publiée reste sur le disque, gelée à
    # sa dernière génération réussie. La compter en échec ferait sortir ce
    # script en 1 à chaque run, donc échouer le job pour une décision écrite.
    groupes_actifs, groupes_suspendus = partitionner_groupes(groupes)
    for groupe in groupes_suspendus:
        print(
            f"⏸  {resume_suspension(groupe)} — fiche publiée laissée en l'état.",
            file=sys.stderr,
        )

    for groupe in groupes_actifs:
        key = _roster_key(groupe)
        if key not in rosters_bruts:
            roster_chambre, legislature = key
            print(f"→ Récupération du roster complet ({roster_chambre}, législature={legislature or 'courante'})…", file=sys.stderr)
            try:
                rosters_bruts[key] = fetch_full_roster(roster_chambre, legislature=legislature)
            except ERREURS_ROSTER as exc:
                print(f"  [!] Récupération du roster impossible pour {key} : {exc}", file=sys.stderr)
                rosters_bruts[key] = None
                cles_indisponibles.append(key)
                # L'annotation nomme la CLÉ ici et les groupes sautés en fin de
                # boucle : la cause tient en une ligne, ses conséquences se
                # comptent, et les mêler noierait la première (#518).
                gha.annoter(
                    "error",
                    f"ROSTER_INDISPONIBLE — récupération du roster ({_libelle_cle(key)}) "
                    f"en échec après reprises : {type(exc).__name__}: {exc}",
                )

        raw_members = rosters_bruts[key]
        if raw_members is None:
            print(f"  [!] {groupe['groupe_id']} ignoré (roster {key} indisponible).", file=sys.stderr)
            groupes_sautes.setdefault(key, []).append(groupe["groupe_id"])
            continue

        roster = filter_roster_by_sigle(
            raw_members,
            groupe["roster_chambre"],
            groupe["groupe_sigle"],
        )

        # La qualification que l'Assemblée donne au groupe (#686) sort de la
        # table committée `correspondance_sigles_an`, jamais d'une ressemblance
        # de sigle : nos fiches disent `REN` et `LFI`, le référentiel dit `RE`
        # et `LFI-NUPES`, et l'appariement direct rendait `None` sur deux
        # fiches sur cinq — dont la seule majoritaire du corpus. Aucune archive
        # n'est lue ici : la valeur est relue et datée dans le dépôt.
        #
        # Une entrée manquante lève, et l'exception est traitée comme un échec
        # de génération : publier une fiche de groupe sans sa posture, ou avec
        # une posture devinée, est précisément ce que ce lot corrige.
        out_path = out_dir / groupe["fichier"]
        try:
            position_politique = None
            succede_a = None
            historique_noms = None
            if groupe.get("chambre") == "AN":
                position_politique = position_politique_publiee(
                    groupe["groupe_sigle"], groupe.get("legislature"), chemin_config
                )
                # La succession sort de la même table et lève de la même façon
                # (#700) : `None` veut dire « pas de prédécesseur dans le
                # périmètre » — les 5 fiches de la XVIe —, jamais « je n'ai pas
                # su ». Une cible qui ne résout pas a déjà fait lever
                # `charger_correspondance_sigles`.
                succede_a = succession_publiee(
                    groupe["groupe_sigle"], groupe.get("legislature"), chemin_config
                )
                # Les organes successifs du groupe dans sa législature (#815),
                # de la même table et par le même chemin : aucune archive lue.
                historique_noms = historique_noms_publie(
                    groupe["groupe_sigle"], groupe.get("legislature"), chemin_config
                )
            generate_groupe_profile_from_roster(
                roster=roster,
                groupe_id=groupe["groupe_id"],
                groupe_sigle=groupe["groupe_sigle"],
                groupe_nom=groupe["groupe_nom"],
                chambre=groupe["chambre"],
                legislature=groupe.get("legislature"),
                roster_chambre=groupe["roster_chambre"],
                profiles_dir=profiles_dir,
                out_path=out_path,
                merge_existing=merge_existing,
                validate=validate,
                scrutins_index=scrutins_index,
                amendements_index=amendements_index,
                position_politique=position_politique,
                succede_a=succede_a,
                historique_noms=historique_noms,
            )
        except CorrespondanceSiglesInvalide as exc:
            # Nommée à part de l'échec générique : ce n'est ni le réseau ni un
            # défaut de calcul, c'est une table à relire — et le message dit
            # lequel des dix couples (sigle publié, législature) manque.
            print(
                f"  [!] {groupe['groupe_id']} : position politique déclarée "
                f"introuvable dans la table committée — {exc}",
                file=sys.stderr,
            )
            echecs_generation.append(groupe["groupe_id"])
            gha.annoter(
                "error",
                f"POSITION_POLITIQUE_ABSENTE — {groupe['groupe_id']} : {exc}",
            )
            continue
        except Exception as exc:  # noqa: BLE001 - un échec sur un groupe ne doit pas arrêter les autres
            print(f"  [!] Échec de génération pour {groupe['groupe_id']} : {exc}", file=sys.stderr)
            echecs_generation.append(groupe["groupe_id"])
            gha.annoter(
                "error",
                f"GROUPE_EN_ECHEC — {groupe['groupe_id']} : {type(exc).__name__}: {exc}",
            )

    # Une annotation par clé indisponible, NOMMANT les groupes sautés. Sans
    # elle, l'onglet de résumé d'un run mort ici ne gardait que
    # `Process completed with exit code 1` — c'est ce qui a obligé à rejouer le
    # script localement pour diagnostiquer le run 32750929942 (#518).
    for key in cles_indisponibles:
        sautes = groupes_sautes.get(key) or []
        gha.annoter(
            "error",
            f"ROSTER_INDISPONIBLE — {len(sautes)} fiche(s) de groupe non régénérée(s) "
            f"faute du roster ({_libelle_cle(key)}) : {', '.join(sautes) or 'aucune'}. "
            "Les fiches déjà publiées restent en place, inchangées.",
        )

    return ResultatGeneration(
        echecs_generation=echecs_generation,
        cles_indisponibles=cles_indisponibles,
        groupes_sautes=groupes_sautes,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--config",
        default="raw_data/groupes_reels.json",
        metavar="FICHIER",
        help="Fichier JSON listant les groupes à générer (défaut : raw_data/groupes_reels.json).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Dossier des profils pivot individuels (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--out-dir",
        default="pivot_data/groupes",
        metavar="DOSSIER",
        help="Dossier de sortie des profils de groupe (défaut : pivot_data/groupes).",
    )
    parser.add_argument(
        "--rosters-bruts",
        default=None,
        metavar="FICHIER",
        help="Réutiliser les rosters bruts déjà collectés par ce run "
             "(generate_roster_candidats.py --rosters-bruts-out) au lieu de les "
             "refetcher. Une clé absente du fichier est fetchée normalement ; un "
             "fichier illisible fait retomber sur le fetch, en le disant (#518).",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help=(
            "Réintègre, pour chaque groupe, les membres du fichier de sortie "
            "précédent absents du roster récupéré cette exécution (voir "
            "group_profile.py --merge-existing)."
        ),
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valide chaque profil de groupe produit et affiche les erreurs éventuelles.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[!] Lecture de {config_path} impossible : {exc}", file=sys.stderr)
        return 1

    groupes = config.get("groupes") or []
    if not groupes:
        print(f"[!] Aucun groupe à générer dans {config_path}.", file=sys.stderr)
        return 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    resultat = generate_all(
        groupes,
        profiles_dir=Path(args.profiles_dir),
        out_dir=out_dir,
        merge_existing=args.merge_existing,
        validate=args.validate,
        rosters_bruts_path=Path(args.rosters_bruts) if args.rosters_bruts else None,
        chemin_config=config_path,
    )

    # Le dénominateur est le nombre de groupes ACTIFS : rapporter 5/7 quand 2
    # sont suspendus donnerait à lire un run à moitié raté (#516).
    groupes_actifs, groupes_suspendus = partitionner_groupes(groupes)
    suffixe = f" ({len(groupes_suspendus)} suspendu(s))" if groupes_suspendus else ""
    print(
        f"→ {len(groupes_actifs) - resultat.echecs}/{len(groupes_actifs)} profil(s) de groupe "
        f"généré(s){suffixe}.",
        file=sys.stderr,
    )

    code = resultat.code_sortie()
    if code == EXIT_ROSTER_INDISPONIBLE:
        print(
            "  [!] Aucune fiche de groupe réécrite pour "
            f"{len(resultat.cles_indisponibles)} roster(s) indisponible(s) — les "
            "fiches déjà publiées restent en place, intactes (#518). Sortie "
            f"{EXIT_ROSTER_INDISPONIBLE} : collecte incomplète, pas un défaut de "
            "génération.",
            file=sys.stderr,
        )
    return code


if __name__ == "__main__":
    sys.exit(main())
