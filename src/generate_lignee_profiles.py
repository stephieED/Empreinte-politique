#!/usr/bin/env python3
"""
generate_lignee_profiles.py — Écrit les fiches de LIGNÉE dans `pivot_data/lignees/`
(#836).

## Ce que ce script lit, et ce qu'il ne refetch pas

Rien du réseau. Il lit les fiches de groupe **déjà publiées**
(`pivot_data/groupes/`), la déclaration des lignées
(`raw_data/groupes_reels.json`), les profils pivot des membres et l'index des
amendements. C'est pourquoi il tourne APRÈS `generate_group_profiles.py` et
survit à son code 2 : un roster indisponible laisse les fiches committées en
place, et une lignée bâtie dessus reste juste — simplement inchangée.

## Pourquoi un script à part, et non un dernier tour dans `generate_group_profiles`

Le partager économiserait le rechargement de l'index des amendements —
**4,3 s et 745 Mio** mesurés. Ce n'est pas le bon échange : la génération de
groupe sort en 2 quand un roster tombe, et il faudrait alors décider, au milieu
d'une fonction, si la lignée se calcule quand même. Deux sorties dans deux
répertoires, deux scripts, deux codes de retour — c'est déjà la règle que
`generate_gouvernement_profiles.py` applique.

## Les deux contradictions que ce script REFUSE

1. **La partition déclarée contre la chaîne écrite.** `lignee_id` est déclaré
   sur chaque entrée de `groupes[]` ; `succede_a` est écrit une seule fois dans
   `correspondance_sigles_an`. Si un maillon succède à un maillon d'une AUTRE
   lignée, l'un des deux se trompe, et publier l'un des deux reviendrait à
   choisir en silence. La lignée est alors refusée, nommément.

   C'est cette porte qui tient une **scission** tant que sa forme n'est pas
   tranchée : une déclaration bancale échoue au lieu de publier une lignée qui
   absorberait un groupe qui n'a succédé à personne. #815 et #836 en croyaient
   tenir un cas, « `AD` quitte `DR` » ; mesuré le 11/09/2026, aucun des 16
   membres d'`AD` n'a siégé dans `DR`, et UDR est entrée comme lignée à elle
   seule, sans prédécesseur. Le corpus ne porte aucune scission à ce jour.

2. **Un maillon déclaré dont la fiche n'est pas sur le disque.** La lignée est
   refusée plutôt que publiée amputée : une union à qui il manque un maillon
   sort des chiffres plus petits sans que rien ne le dise, et c'est exactement
   ce que le contrôle de perte d'avant-commit ne peut plus rattraper une fois
   le fichier écrit.

## Le coût, mesuré et non supposé

Corpus du 11/09/2026, 23 fiches, 10 lignées : **104 s** et **1 453 Mio de RSS
maximum**, index des amendements compris (4,3 s, 745 Mio à lui seul). La lignée
la plus chère est la macroniste — 660 couples (membre, législature) pour 446
personnes. Les profils sont chargés **un à la fois** et projetés (#635) : les
garder entiers coûtait 0,9 à 1,1 Gio pour une seule fiche de groupe.

Usage (depuis la racine du dépôt) :
    python3 src/generate_lignee_profiles.py \\
        --config raw_data/groupes_reels.json \\
        --groupes-dir pivot_data/groupes \\
        --profiles-dir pivot_data/profiles \\
        --out-dir pivot_data/lignees \\
        --validate
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, NamedTuple, Optional

import gha
from amendements_index import DEFAULT_AMENDEMENTS_DIR, charger as charger_amendements
from json_io import ecrire_profil_json
from groupes_config import (
    CHEMIN_CONFIG_GROUPES,
    CLE_LIGNEE_ID,
    LigneeConfigInvalide,
    charger_lignees,
)
from licences import appliquer_licence_donnees
from lignee_profile import composer_lignee, ordonner_maillons, recalculer_agregats
from schema_lignee import SCHEMA_LIGNEE_VERSION, validate_profil_lignee


class LigneeIncoherente(ValueError):
    """La lignée déclarée contredit la chaîne `succede_a`, ou un maillon manque."""


class ResultatLignees(NamedTuple):
    """Ce que le run a produit, lignée par lignée — pas un compte agrégé.

    Même raison qu'en #518 : un compte ne dit pas LAQUELLE a échoué, et c'est
    le seul renseignement dont dispose qui relit l'onglet d'un run mort.
    """

    ecrites: list[str]
    echecs: list[tuple[str, str]]

    def code_sortie(self) -> int:
        return 1 if self.echecs else 0


def charger_fiches_groupes(dossier: Path) -> dict[str, dict[str, Any]]:
    """Les fiches de groupe publiées, indexées par `groupe_id`.

    Un fichier illisible **lève** : il n'y a pas de lecture partielle utile
    d'un répertoire dont chaque document est un maillon possible.
    """
    fiches: dict[str, dict[str, Any]] = {}
    for chemin in sorted(dossier.glob("*.json")):
        try:
            fiche = json.loads(chemin.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ValueError(f"{chemin} : JSON invalide — {exc}") from exc
        groupe_id = fiche.get("groupe_id")
        if groupe_id:
            fiches[str(groupe_id)] = fiche
    return fiches


def appartenances_declarees(chemin_config: Path) -> dict[str, str]:
    """`groupe_id` → `lignee_id`, tels que la configuration les déclare."""
    document = json.loads(Path(chemin_config).read_text(encoding="utf-8"))
    return {
        str(groupe["groupe_id"]): str(groupe[CLE_LIGNEE_ID])
        for groupe in document.get("groupes") or []
        if groupe.get("groupe_id") and groupe.get(CLE_LIGNEE_ID)
    }


def verifier_partition(
    fiches: dict[str, dict[str, Any]], appartenances: dict[str, str]
) -> None:
    """Refuse une chaîne `succede_a` qui traverse deux lignées déclarées.

    L'appartenance est déclarée, l'ordre est écrit : les deux disent le même
    fait par deux chemins, et rien ne garantit qu'ils s'accordent — sinon ce
    contrôle. Un prédécesseur hors du corpus publié n'est pas une faute : c'est
    le périmètre du dépôt (§2 règle 5).

    Raises:
        LigneeIncoherente: la première contradiction, nommée des deux côtés.
    """
    for groupe_id, fiche in sorted(fiches.items()):
        lignee = appartenances.get(groupe_id)
        if lignee is None:
            continue
        for bloc in fiche.get("succede_a") or []:
            cible = bloc.get("groupe_id")
            if not cible or cible not in fiches:
                continue
            lignee_cible = appartenances.get(str(cible))
            if lignee_cible is not None and lignee_cible != lignee:
                raise LigneeIncoherente(
                    f"{groupe_id} est déclaré dans {lignee!r} et succède à "
                    f"{cible}, déclaré dans {lignee_cible!r}. Une succession ne "
                    "traverse pas deux lignées : l'une des deux déclarations est "
                    "fausse, et une SCISSION ne s'écrit pas avec `succede_a` "
                    "(#815, #836)."
                )


def generer_une_lignee(
    declaration: dict[str, Any],
    groupe_ids: list[str],
    fiches: dict[str, dict[str, Any]],
    profiles_dir: Path,
    amendements_index: Any,
) -> dict[str, Any]:
    """Compose la fiche d'UNE lignée, profils chargés un à un.

    Raises:
        LigneeIncoherente: un maillon déclaré n'a pas de fiche publiée.
    """
    from group_profile import (  # noqa: PLC0415 — import tardif : group_profile est lourd
        CumulAmendementsDistincts,
        load_profil_from_file,
    )

    absents = [g for g in groupe_ids if g not in fiches]
    if absents:
        raise LigneeIncoherente(
            f"maillon(s) déclaré(s) sans fiche publiée : {absents}. Une lignée "
            "amputée publierait des chiffres plus petits sans que rien ne le dise."
        )

    ordre = ordonner_maillons(fiches, groupe_ids)
    fiches_ordonnees = [fiches[g] for g in ordre]

    # Un couple (membre, législature) par lecture : deux maillons d'une MÊME
    # législature — `NG:15` et `SOC:15` — ne doivent pas faire lire deux fois
    # les mêmes amendements, et deux maillons de législatures différentes
    # doivent au contraire être lus deux fois, chacun avec SA législature
    # (#821).
    couples: list[tuple[str, Optional[str]]] = []
    vus: set[tuple[str, Optional[str]]] = set()
    for fiche in fiches_ordonnees:
        legislature = fiche.get("legislature")
        for membre in fiche.get("membres") or []:
            membre_id = membre.get("membre_id")
            if not membre_id:
                continue
            cle = (str(membre_id), legislature)
            if cle not in vus:
                vus.add(cle)
                couples.append(cle)

    # UN cumul pour toute la lignée : c'est lui qui rend le compte en
    # amendements DISTINCTS et non en signatures (#643).
    cumul = CumulAmendementsDistincts()
    profils_projetes: list[tuple[Optional[str], dict[str, Any]]] = []
    profils_absents: list[str] = []
    for membre_id, legislature in couples:
        chemin = profiles_dir / f"{membre_id}.pivot.json"
        if not chemin.exists():
            if membre_id not in profils_absents:
                profils_absents.append(membre_id)
            continue
        profils_projetes.append((
            legislature,
            load_profil_from_file(
                chemin, amendements_index, distincts=cumul, legislature=legislature
            ),
        ))

    agregats = recalculer_agregats(profils_projetes, amendements_index)
    non_resolus = agregats.pop("nb_amendements_non_resolus", 0)

    profil = composer_lignee(
        lignee_id=str(declaration["lignee_id"]),
        lignee_nom=str(declaration["lignee_nom"]),
        chambre=str(declaration["chambre"]),
        fiches_ordonnees=fiches_ordonnees,
        agregats_recalcules=agregats,
    )

    lus = sorted({p.get("id") for _, p in profils_projetes if p.get("id")})
    avertissements: list[str] = []
    if profils_absents:
        avertissements.append(
            f"{len(profils_absents)} membre(s) de la lignée n'ont pas de profil "
            f"publié : leurs amendements et leurs étiquettes ne sont pas comptés "
            f"— {', '.join(profils_absents[:10])}"
            + (" …" if len(profils_absents) > 10 else "")
        )
    if non_resolus:
        avertissements.append(
            f"{non_resolus} entrée(s) d'amendement qu'aucune source ne renseigne, "
            "exclues des décomptes (§2 règle 7)."
        )
    profil["meta"] = {
        "schema_version": SCHEMA_LIGNEE_VERSION,
        "genere_le": date.today().isoformat(),
        "maillons": ordre,
        "couverture_profils": {
            "couples_membre_legislature": len(couples),
            "profils_lus": len(lus),
            "membres_sans_profil": len(profils_absents),
        },
        "profils_sources": lus,
        "warnings": avertissements,
    }
    # Dérivée de `sources[]`, jamais constante (#530) : l'union des maillons
    # porte encore des entrées `nosdeputes`, et la clause ODbL tient tant
    # qu'elles sont publiées (AGENTS.md §7).
    appliquer_licence_donnees(profil)
    return profil


def generate_all(
    groupes_dir: Path,
    profiles_dir: Path,
    out_dir: Path,
    chemin_config: Path = CHEMIN_CONFIG_GROUPES,
    amendements_path: Path = DEFAULT_AMENDEMENTS_DIR,
    validate: bool = False,
) -> ResultatLignees:
    """Écrit une fiche par lignée déclarée. Une lignée en échec n'arrête pas les autres."""
    declarations = charger_lignees(chemin_config)
    appartenances = appartenances_declarees(chemin_config)
    fiches = charger_fiches_groupes(groupes_dir)
    print(
        f"→ {len(fiches)} fiche(s) de groupe publiée(s) lue(s) dans {groupes_dir}, "
        f"{len(declarations)} lignée(s) déclarée(s).",
        file=sys.stderr,
    )
    verifier_partition(fiches, appartenances)

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
        print(
            f"→ Index des amendements : {len(amendements_index)} amendement(s).",
            file=sys.stderr,
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    ecrites: list[str] = []
    echecs: list[tuple[str, str]] = []
    for declaration in declarations:
        lignee_id = str(declaration["lignee_id"])
        groupe_ids = sorted(g for g, l in appartenances.items() if l == lignee_id)
        try:
            profil = generer_une_lignee(
                declaration, groupe_ids, fiches, profiles_dir, amendements_index
            )
            if validate:
                erreurs = validate_profil_lignee(profil)
                if erreurs:
                    raise LigneeIncoherente(f"fiche invalide — {erreurs}")
            # Compact, et non indenté comme `pivot_data/groupes` : le
            # critère de #433 est « relu à la main », et une fiche de lignée
            # pèse jusqu'à 11,5 Mo — 53 Mo pour les dix, 36 en compact. Voir
            # `json_io`, qui porte la mesure.
            chemin = out_dir / str(declaration["fichier"])
            ecrire_profil_json(chemin, profil)
            ecrites.append(lignee_id)
            print(
                f"✓ {lignee_id} — {len(profil['maillons'])} maillon(s), "
                f"{profil['effectif']['cumul_historique']} membre(s), "
                f"{len(profil['cohesion_votes'])} scrutin(s) de cohésion, "
                f"{profil['amendements_agreges'].get('nb_amendements', 0)} amendement(s) "
                f"distinct(s) → {chemin}",
                file=sys.stderr,
            )
        except Exception as exc:  # noqa: BLE001 - une lignée en échec n'arrête pas les autres
            echecs.append((lignee_id, f"{type(exc).__name__}: {exc}"))
            print(f"  [!] {lignee_id} en échec : {exc}", file=sys.stderr)
            gha.annoter("error", f"LIGNEE_EN_ECHEC — {lignee_id} : {type(exc).__name__}: {exc}")
    return ResultatLignees(ecrites=ecrites, echecs=echecs)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--config",
        default=str(CHEMIN_CONFIG_GROUPES),
        metavar="FICHIER",
        help="Configuration déclarant les lignées et l'appartenance de chaque "
             "groupe (défaut : raw_data/groupes_reels.json).",
    )
    parser.add_argument(
        "--groupes-dir",
        default="pivot_data/groupes",
        metavar="DOSSIER",
        help="Dossier des fiches de groupe publiées (défaut : pivot_data/groupes).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Dossier des profils pivot individuels (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--out-dir",
        default="pivot_data/lignees",
        metavar="DOSSIER",
        help="Dossier de sortie des fiches de lignée (défaut : pivot_data/lignees).",
    )
    parser.add_argument(
        "--amendements-dir",
        default=str(DEFAULT_AMENDEMENTS_DIR),
        metavar="DOSSIER",
        help=f"Index des amendements (défaut : {DEFAULT_AMENDEMENTS_DIR}).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valide chaque fiche produite ; une fiche invalide n'est pas écrite.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    try:
        resultat = generate_all(
            groupes_dir=Path(args.groupes_dir),
            profiles_dir=Path(args.profiles_dir),
            out_dir=Path(args.out_dir),
            chemin_config=Path(args.config),
            amendements_path=Path(args.amendements_dir),
            validate=args.validate,
        )
    except (LigneeConfigInvalide, LigneeIncoherente, ValueError, OSError) as exc:
        # Une configuration ou une partition fausse ne produit AUCUNE fiche :
        # ce n'est pas une lignée qui tombe, c'est la déclaration qui est à
        # relire, et écrire les neuf autres laisserait croire le contraire.
        print(f"[!] {type(exc).__name__}: {exc}", file=sys.stderr)
        gha.annoter("error", f"LIGNEES_CONFIG — {type(exc).__name__}: {exc}")
        return 1

    print(
        f"→ {len(resultat.ecrites)}/{len(resultat.ecrites) + len(resultat.echecs)} "
        "fiche(s) de lignée écrite(s).",
        file=sys.stderr,
    )
    return resultat.code_sortie()


if __name__ == "__main__":
    sys.exit(main())
