#!/usr/bin/env python3
"""
migrer_absences_publiees_556_558_560.py — Remet le corpus publié en accord avec
ce que les sources ont réellement dit (#556, #558, #560).

Script de maintenance, pas une étape du pipeline : il s'exécute une fois, son
résultat est committé par la propriétaire du dépôt, et il reste ici pour être
**relu** — comme `migrer_identite_couverture_539.py` (#539) et
`build_correspondance_acteurs_an.py` (#525). **Aucun appel réseau.**

## Les trois défauts ont la même forme

Une absence produite par une décision, une frontière de source ou un marqueur
XML était publiée comme un **fait**. C'est le contresens que #539 existe pour
empêcher, et c'est pourquoi les trois se réparent d'une seule passe : ils
touchent les mêmes fichiers, et deux d'entre eux les mêmes lignes.

| Issue | Ce qui était publié | Ce qui est vrai |
| --- | --- | --- |
| #556 | `identite.uri_hatvp` = `{"@xsi:nil": "true"}`, sur 191 profils | AMO30 dit « pas de déclaration HATVP » : c'est `null` |
| #558 | « couvert » sur les listes vides de 20 sénateurs | l'extraction de leur groupe est gelée (#516/#528) |
| #560 | `non_collecte` / `panne` sur les interventions de 2 profils | Syceron commence à la XVe, leurs mandats sont antérieurs |

## Pourquoi une migration ET une correction en amont

La correction de #556 vit dans l'**extraction**
(`candidate_profile._champ_identite_an`), pas dans la normalisation : réparer
dans le pivot laisserait `raw_data/profiles` — la couche *source-near* — porter
une valeur qui n'a jamais existé chez la source. Ce script applique donc la
même règle **aux deux couches**, et il le fait sans réseau parce qu'il n'y en a
pas besoin : ramener un marqueur d'absence à `null` est une lecture du fichier
déjà collecté, pas une re-collecte.

C'est aussi ce qui distingue cette passe d'un run : un run télécharge AMO30,
recollecte 481 profils et coûte des heures ; celle-ci relit ce qui est déjà
committé. Le run reste nécessaire pour **tout le reste** de ce que la
correction d'extraction changera (les champs qu'aucun profil publié ne porte
encore au marqueur), mais il n'est pas nécessaire pour éteindre les trois
défauts mesurés.

## Le cas `lieu_naissance`, qui n'est pas réparable comme les deux autres

`identite.uri_hatvp` et `identite.profession` portent l'objet marqueur : les
reconnaître est un test de forme. `identite.lieu_naissance`, lui, porte le
`repr` **Python** du marqueur, interpolé dans une chaîne par
`_format_lieu_naissance` — `"Chauny ({'@xmlns:xsi': …, '@xsi:nil': 'true'})"`,
ou entièrement fait de plomberie sur 18 profils. Il se répare par motif, et le
motif est ancré sur la forme exacte que produit ce `repr` : rien d'autre dans
un lieu de naissance ne peut y ressembler.

## Ce qu'il ne fait pas

- **Il ne recolle rien.** Une liste vide reste vide ; ce qui change est ce que
  le profil **dit** de ce vide.
- **Il ne touche pas à `chambre`.** Les 20 sénateurs publient `chambre: "AN"` :
  défaut réel, distinct, tenu par #486.
- **Il ne lève pas la suspension** des deux groupes Sénat, et ne réécrit pas
  leurs `membres` : il ajoute à `meta.couverture_roster` l'état qui dit ce que
  le ratio 15/235 veut dire.

## Usage

    python src/migrer_absences_publiees_556_558_560.py --verifier   # ne réécrit rien
    python src/migrer_absences_publiees_556_558_560.py              # écrit

Idempotent : une seconde passe ne modifie plus aucun fichier, hors
`constate_le` de la couverture si le jour a changé (`--constate-le` le fige).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import argparse
import json
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import correspondance_acteurs_an  # noqa: E402
import couverture_profil  # noqa: E402
from candidate_profile import nb_acteurs_referentiel_charge  # noqa: E402
from groupes_config import (  # noqa: E402
    CLE_SUSPENSION,
    est_suspendu,
    index_membres_de_groupes_suspendus,
    libelle_groupe,
    resume_suspension,
)
from json_io import ecrire_profil_json  # noqa: E402
from normalize_profil import _uri_hatvp_publiable  # noqa: E402
from profil_brut import (  # noqa: E402
    charger_profil_brut,
    ecrire_profil_brut,
    slugs_du_repertoire,
)
from schema_groupe import (  # noqa: E402
    ETAT_ROSTER_HORS_PERIMETRE,
    validate_profil_groupe,
)
from schema_pivot import poser_identifiant, validate_profil  # noqa: E402

SUFFIXE_PIVOT = ".pivot.json"

#: Le `repr` Python du marqueur `xsi:nil`, tel que `_format_lieu_naissance` l'a
#: interpolé. L'ordre des clés est celui du dict source, stable depuis Python
#: 3.7 (ordre d'insertion) et identique sur les 28 profils mesurés.
_REPR_MARQUEUR = re.compile(
    r"\{'@xmlns:xsi': 'http://www\.w3\.org/2001/XMLSchema-instance', "
    r"'@xsi:nil': 'true'\}"
)


def est_marqueur_nil(valeur: Any) -> bool:
    """`True` si la valeur EST le marqueur d'absence XML d'AMO30.

    Le test porte sur `@xsi:nil`, pas sur l'égalité au dict complet : le
    namespace peut être déclaré ailleurs dans le document, auquel cas le
    convertisseur ne le recopie pas sur l'élément.
    """
    return isinstance(valeur, dict) and str(valeur.get("@xsi:nil", "")).lower() == "true"


def nettoyer_valeur(valeur: Any) -> Any:
    """Un marqueur d'absence redevient `null`. Tout le reste est rendu tel quel.

    Trois formes, dont la troisième est la raison d'être de cette fonction :

    1. l'objet marqueur → `None` ;
    2. une chaîne **entièrement** faite d'un ou deux `repr` de marqueur (avec
       la parenthèse de `_format_lieu_naissance` autour du second) → `None` ;
    3. une chaîne qui porte une vraie valeur ET un `repr` de marqueur —
       `"Chauny ({…})"` → `"Chauny"`. La donnée réelle est conservée : c'est le
       complément absent qu'on retire, pas la ville.
    """
    if est_marqueur_nil(valeur):
        return None
    if not isinstance(valeur, str) or "@xsi:nil" not in valeur:
        return valeur
    # `"Ville (Dép)"` : on retire d'abord le complément entre parenthèses quand
    # c'est lui qui est nil, puis un éventuel reste de marqueur.
    nettoye = re.sub(r"\s*\(" + _REPR_MARQUEUR.pattern + r"\)", "", valeur)
    nettoye = _REPR_MARQUEUR.sub("", nettoye).strip(" ()")
    return nettoye or None


def _nettoyer_identite(profil: dict[str, Any]) -> dict[str, int]:
    """Applique `nettoyer_valeur` à tous les champs d'un bloc `identite`.

    Rend `{champ: 1}` pour les champs effectivement changés. Le bloc entier est
    parcouru, pas seulement les trois champs mesurés : le convertisseur XML ne
    connaît pas le nom du champ, donc la règle ne doit pas le connaître non plus.
    """
    identite = profil.get("identite")
    if not isinstance(identite, dict):
        return {}
    changes: dict[str, int] = {}
    for cle, valeur in list(identite.items()):
        propre = nettoyer_valeur(valeur)
        if propre != valeur:
            identite[cle] = propre
            changes[cle] = 1
    return changes


def migrer_bruts(profils_dir: Path, *, ecrire: bool) -> dict[str, Any]:
    """Ramène les marqueurs `xsi:nil` de `raw_data/profiles` à `null` (#556).

    Passe par `profil_brut` — jamais par un `json.load` direct sur
    `<slug>.json` : depuis #580 un profil brut est un socle **plus** ses
    tranches d'amendements, et le lire à la main rendrait un document amputé
    qu'on réécrirait ensuite tel quel. `charger_profil_brut` accepte les deux
    formes ; `ecrire_profil_brut` n'écrit que la partitionnée, donc un profil
    touché ici migre au passage, sans perdre un octet.
    """
    mesures: dict[str, Any] = {"profils": 0, "modifies": 0, "champs": {}, "slugs": []}
    if not profils_dir.is_dir():
        return mesures

    for slug in slugs_du_repertoire(profils_dir):
        mesures["profils"] += 1
        chemin = profils_dir / f"{slug}.json"
        profil = charger_profil_brut(chemin)
        changes = _nettoyer_identite(profil)
        if not changes:
            continue
        mesures["modifies"] += 1
        mesures["slugs"].append(slug)
        for champ in changes:
            mesures["champs"][champ] = mesures["champs"].get(champ, 0) + 1
        if ecrire:
            ecrire_profil_brut(profils_dir, slug, profil)
    return mesures


def migrer_pivots(
    profiles_dir: Path,
    table: dict[str, dict[str, Any]],
    membres_suspendus: dict[str, dict[str, Any]],
    *,
    constate_le: Optional[str],
    ecrire: bool,
    forcer_sans_referentiel: bool = False,
) -> dict[str, Any]:
    """Nettoie l'identité (#556) et redérive la couverture (#558, #560).

    La couverture n'est jamais fusionnée : elle décrit le run, pas la personne
    (`merge_profile.merge_pivot_profile`). La redériver ici est donc la même
    opération que celle du pipeline, sur les mêmes entrées.
    """
    sante = couverture_profil.SanteReferentiel(nb_acteurs_referentiel_charge())
    # **Le référentiel doit être prouvé chargé, sinon on ne réécrit rien.**
    #
    # `etablir_fait_hors_an` rend une PANNE quand AMO30 n'est pas mesuré
    # (condition C1, #484), et `deriver` publie alors `non_collecte`/`panne` sur
    # les cinq listes. Sur les 4 profils qui publient aujourd'hui `fait_etabli`
    # — `nathalie-arthaud`, `marine-tondelier`, `david-lisnard`,
    # `jordan-bardella` —, une migration lancée sans `.cache/` remplacerait donc
    # « jamais élue à l'Assemblée nationale », qui est un fait établi, par
    # « nous n'avons pas réussi à collecter ».
    #
    # Ce serait le défaut que ce lot corrige, produit par le script qui le
    # corrige. La passe s'arrête plutôt que de le commettre — `--forcer` existe
    # pour le cas, réel, où on veut mesurer le reste avec `--verifier`.
    if not sante.prouve_charge and not forcer_sans_referentiel:
        raise SystemExit(
            "Refus de migrer : le référentiel AMO30 n'est pas prouvé chargé "
            f"({sante.preuve}). Sans lui, les profils qui publient 'fait_etabli' "
            "basculeraient en 'non_collecte'/'panne' — le contresens même que ce "
            "lot corrige. Lancer d'abord une passe qui remplit "
            "`.cache/acteurs_historique_an/`, ou passer --forcer-sans-referentiel "
            "pour une mesure à blanc."
        )
    mesures: dict[str, Any] = {
        "profils": 0, "modifies": 0, "identite_nettoyee": 0, "champs": {},
        "hatvp_retires": 0, "couverture_changee": 0, "invalides": [],
        "groupes_suspendus": 0, "sante_referentiel": sante.preuve,
        "etats_apres": {},
    }

    for chemin in sorted(
        c for c in profiles_dir.glob(f"*{SUFFIXE_PIVOT}") if not c.name.startswith(".")
    ):
        slug = chemin.name[: -len(SUFFIXE_PIVOT)]
        profil = json.loads(chemin.read_text(encoding="utf-8"))
        mesures["profils"] += 1
        avant = json.dumps(profil, ensure_ascii=False, sort_keys=True)
        couverture_avant = json.dumps(
            profil.get("couverture"), ensure_ascii=False, sort_keys=True
        )

        changes = _nettoyer_identite(profil)
        if changes:
            mesures["identite_nettoyee"] += 1
            for champ in changes:
                mesures["champs"][champ] = mesures["champs"].get(champ, 0) + 1

        # `identifiants.hatvp` est la RECOPIE de `identite.uri_hatvp` : les deux
        # sortent de la même fabrique, donc ils se recalculent ensemble. Sur les
        # 191 profils du marqueur il valait déjà `null` — `poser_identifiant`
        # levait sur une valeur non-chaîne, ce qui a empêché le marqueur d'y
        # entrer (#539). La recopie est refaite quand même : c'est ce qui rend
        # la passe idempotente et vérifiable par `validate_profil`.
        identite = profil.get("identite")
        if isinstance(identite, dict) and isinstance(profil.get("identifiants"), dict):
            publiable = _uri_hatvp_publiable(identite.get("uri_hatvp"))
            if profil["identifiants"].get("hatvp") and not publiable:
                profil["identifiants"]["hatvp"] = None
                mesures["hatvp_retires"] += 1
            poser_identifiant(profil, "hatvp", publiable)

        groupe = membres_suspendus.get(slug)
        if groupe is not None:
            mesures["groupes_suspendus"] += 1
        couverture_profil.appliquer(
            profil,
            constate_le=constate_le,
            fait_hors_an=couverture_profil.etablir_fait_hors_an(table.get(slug), sante),
            groupe_suspendu=(
                couverture_profil.groupe_suspendu_depuis_config(groupe)
                if groupe is not None else None
            ),
        )
        if json.dumps(profil.get("couverture"), ensure_ascii=False,
                      sort_keys=True) != couverture_avant:
            mesures["couverture_changee"] += 1
        for liste, entrees in (profil.get("couverture") or {}).items():
            for entree in entrees:
                cle = f"{liste}/{entree.get('etat')}"
                if entree.get("cause"):
                    cle += f"/{entree['cause']}"
                mesures["etats_apres"][cle] = mesures["etats_apres"].get(cle, 0) + 1

        erreurs = validate_profil(profil)
        if erreurs:
            mesures["invalides"].append((slug, erreurs[:3]))
            continue

        if json.dumps(profil, ensure_ascii=False, sort_keys=True) == avant:
            continue
        mesures["modifies"] += 1
        if ecrire:
            ecrire_profil_json(chemin, profil)

    return mesures


def migrer_groupes(
    groupes_dir: Path, groupes_config: list[dict[str, Any]], *, ecrire: bool
) -> dict[str, Any]:
    """Pose `meta.couverture_roster.etat` sur les fiches de groupe (#558).

    `hors_perimetre` sur un groupe dont l'extraction est suspendue, et la preuve
    est la **suspension elle-même**, relue dans la config — jamais une phrase
    écrite ici, qui divergerait le jour où la suspension serait levée.

    Les autres fiches ne sont pas touchées : `group_profile` écrit désormais
    `dans_le_perimetre` à chaque génération, et un groupe activement collecté
    est régénéré à chaque run. Poser l'état à leur place ici ferait deux
    écrivains pour un même champ.
    """
    mesures: dict[str, Any] = {"fichiers": 0, "modifies": 0, "detail": {}, "invalides": []}
    for groupe in groupes_config:
        if not est_suspendu(groupe):
            continue
        fichier = groupe.get("fichier")
        if not fichier:
            continue
        chemin = groupes_dir / str(fichier)
        if not chemin.is_file():
            continue
        mesures["fichiers"] += 1
        fiche = json.loads(chemin.read_text(encoding="utf-8"))
        meta = fiche.setdefault("meta", {})
        couverture = meta.get("couverture_roster")
        if not isinstance(couverture, dict):
            # Pas de ratio publié : rien à qualifier. On n'en invente pas un.
            continue
        avant = json.dumps(couverture, ensure_ascii=False, sort_keys=True)
        bloc = groupe.get(CLE_SUSPENSION)
        bloc = bloc if isinstance(bloc, dict) else {}
        couverture["etat"] = ETAT_ROSTER_HORS_PERIMETRE
        couverture["preuve"] = (
            f"{resume_suspension(groupe)}. Les membres non publiés le sont par "
            "cette décision, pas par un défaut de collecte : "
            f"{couverture.get('profils_disponibles')} profils sur "
            f"{couverture.get('roster_total')} est un périmètre, pas une perte. "
            f"Condition de reprise : {bloc.get('condition_reprise') or 'non documentée'}"
        )
        if json.dumps(couverture, ensure_ascii=False, sort_keys=True) == avant:
            continue
        erreurs = validate_profil_groupe(fiche)
        if erreurs:
            mesures["invalides"].append((chemin.name, erreurs[:3]))
            continue
        mesures["modifies"] += 1
        mesures["detail"][chemin.name] = libelle_groupe(groupe)
        if ecrire:
            # `indent=2`, sans saut de ligne final : la forme exacte qu'écrit
            # `group_profile.py`. Un `\n` ajouté ici ferait voir à git une
            # différence de plus qu'il n'y en a.
            chemin.write_text(
                json.dumps(fiche, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    return mesures


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--profiles-dir", default="pivot_data/profiles", type=Path)
    parser.add_argument("--raw-profiles-dir", default="raw_data/profiles", type=Path)
    parser.add_argument("--groupes-dir", default="pivot_data/groupes", type=Path)
    parser.add_argument("--config-groupes", default="raw_data/groupes_reels.json", type=Path)
    parser.add_argument("--correspondance", default=None, type=Path)
    parser.add_argument(
        "--constate-le", default=None,
        help="Date ISO écrite dans `couverture[].constate_le` (défaut : aujourd'hui). "
             "La figer rend la passe reproductible.",
    )
    parser.add_argument(
        "--sauter-bruts", action="store_true",
        help="Ne touche pas à raw_data/profiles. Utile pour rejouer la seule "
             "passe pivot, qui est mille fois plus rapide (622 Mo contre 7,5 Go).",
    )
    parser.add_argument(
        "--forcer-sans-referentiel", action="store_true",
        help="Autorise la passe pivot alors que le référentiel AMO30 n'est pas "
             "chargé. À n'utiliser qu'avec --verifier : sans référentiel, les "
             "profils 'fait_etabli' basculeraient en 'panne'.",
    )
    parser.add_argument(
        "--verifier", action="store_true",
        help="N'écrit rien : mesure ce que la migration changerait.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    ecrire = not args.verifier

    config = json.loads(args.config_groupes.read_text(encoding="utf-8"))
    groupes_config = config.get("groupes") if isinstance(config, dict) else config
    groupes_config = groupes_config if isinstance(groupes_config, list) else []
    membres_suspendus = index_membres_de_groupes_suspendus(
        groupes_config, args.groupes_dir
    )
    table = correspondance_acteurs_an.charger_correspondance(args.correspondance)

    mode = "écrit" if ecrire else "simulé (--verifier)"
    print(f"Migration #556 / #558 / #560 — {mode}")
    print(f"  Membres de groupes suspendus : {len(membres_suspendus)}")

    if not args.sauter_bruts:
        bruts = migrer_bruts(args.raw_profiles_dir, ecrire=ecrire)
        print(f"\n[#556] Profils bruts lus  : {bruts['profils']}")
        print(f"       Profils modifiés   : {bruts['modifies']}")
        for champ, n in sorted(bruts["champs"].items(), key=lambda kv: -kv[1]):
            print(f"         identite.{champ} : {n}")
    else:
        print("\n[#556] raw_data/profiles sauté (--sauter-bruts)")

    pivots = migrer_pivots(
        args.profiles_dir, table, membres_suspendus,
        constate_le=args.constate_le, ecrire=ecrire,
        forcer_sans_referentiel=args.forcer_sans_referentiel,
    )
    print(f"\n[pivot] Profils lus            : {pivots['profils']}")
    print(f"        Identités nettoyées    : {pivots['identite_nettoyee']}")
    for champ, n in sorted(pivots["champs"].items(), key=lambda kv: -kv[1]):
        print(f"          identite.{champ} : {n}")
    print(f"        identifiants.hatvp retirés : {pivots['hatvp_retires']}")
    print(f"        Couvertures changées   : {pivots['couverture_changee']}")
    print(f"        dont profils de groupe gelé : {pivots['groupes_suspendus']}")
    print(f"        Profils réécrits       : {pivots['modifies']}")
    print(f"        Référentiel AMO30      : {pivots['sante_referentiel']}")
    if pivots["invalides"]:
        print(f"  [!] {len(pivots['invalides'])} profil(s) INVALIDE(S), non réécrits :")
        for slug, erreurs in pivots["invalides"][:10]:
            print(f"        - {slug} : {erreurs}")

    groupes = migrer_groupes(args.groupes_dir, groupes_config, ecrire=ecrire)
    print(f"\n[#558] Fiches de groupe suspendues : {groupes['fichiers']}")
    print(f"       Fiches modifiées           : {groupes['modifies']}")
    for fichier, libelle in sorted(groupes["detail"].items()):
        print(f"         {fichier} → {ETAT_ROSTER_HORS_PERIMETRE} ({libelle})")
    if groupes["invalides"]:
        print(f"  [!] {len(groupes['invalides'])} fiche(s) INVALIDE(S), non réécrite(s) :")
        for fichier, erreurs in groupes["invalides"]:
            print(f"        - {fichier} : {erreurs}")

    return 1 if (pivots["invalides"] or groupes["invalides"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
