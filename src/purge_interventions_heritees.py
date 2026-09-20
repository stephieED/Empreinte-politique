#!/usr/bin/env python3
"""
purge_interventions_heritees.py — Retire les interventions héritées de l'ère
NosDéputés dont l'équivalent Syceron est déjà publié dans le même profil (#839).

Contexte
--------
#529 a fait de Syceron la source unique des débats. La fusion additive
(`merge_profile`, `merge_pivot_profile`) ne remplace jamais une entrée
existante, et la clé a changé avec la source : identifiant **entier**
NosDéputés (`249506`) d'un côté, `syceron_CRSANR5L16S2023O1N091_000160` de
l'autre. Les deux coexistent donc, et la **même prise de parole est publiée
deux fois**.

Mesuré le 12/09/2026 sur `origin/main` (`2299b0e8`) : **511** entrées à
identifiant entier, sur **5 profils de candidats déclarés** (`marine-le-pen`
246, `jerome-guedj` 200, `edouard-philippe` 50, `gabriel-attal` 10,
`bruno-retailleau` 5), sur 1 017 574 interventions publiées. **492** ont leur
jumelle Syceron dans le même profil, au même jour, au texte contenu ou
identique — 415 au texte strictement identique.

Le témoin le confirme par la collecte : `marine-le-pen` recollectée à blanc le
12/09/2026 rend **1 866 interventions Syceron et 135 questions officielles, à
l'entrée près**, et **zéro** entrée à identifiant entier.

Principe de prudence (repris de #387)
-------------------------------------
Une entrée n'est retirée QUE si sa jumelle Syceron est **présente dans le
profil**. Sans jumelle, elle est **conservée** : 19 entrées sont dans ce cas
(Congrès de 2018, réunions de commission, interpellations que Syceron attribue
à un orateur collectif ou à un autre député). Un faux négatif laisse un doublon
visible — bénin ; un faux positif supprime une prise de parole — irréversible
hors git.

Limite connue et mesurée : 204 des 492 jumelages portent sur un texte de trois
mots ou moins (« C'est vrai ! »). Si la même personne a prononcé deux fois la
même interjection le même jour, le rapprochement en confond les occurrences et
le corpus en perd une. Le choix est assumé : l'entrée retirée reste celle dont
aucune source primaire ne porte l'identifiant.

Les deux étages (#729, #730)
----------------------------
La fusion est additive **aux deux étages** : un retrait appliqué au seul brut
ne descend jamais dans `pivot_data/`. Ce script prend donc `--profiles-dir` et
se lance deux fois, une fois par couche. Le prochain run bloquera au contrôle
de perte sur `interventions`, liste stable : la perte est voulue et nommée
d'avance, à déclarer par `allow_declared_losses` après comparaison au rapport.

Usage (depuis la racine du dépôt) :
    python3 src/purge_interventions_heritees.py                        # rapport seul
    python3 src/purge_interventions_heritees.py --apply                # applique au brut
    python3 src/purge_interventions_heritees.py \
        --profiles-dir pivot_data/profiles --apply                       # applique au pivot
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

from json_io import ecrire_profil_json
from licences import appliquer_licence_donnees
from profil_brut import charger_socle
from schema_pivot import deriver_tags_thematiques

DEFAULT_PROFILES_DIR = Path("raw_data") / "profiles"

_BALISE = re.compile(r"<[^>]+>")
_NON_MOT = re.compile(r"\W+", re.UNICODE)
_DATE_FR = re.compile(r"^(\d{2})/(\d{2})/(\d{4})")


def _normalize_texte(texte: Any) -> str:
    """Texte comparable : balises retirées, entités résolues, ponctuation
    neutralisée. NosDéputés sert du HTML (`<p>…</p>`), Syceron du texte nu ;
    sans cette réduction, aucune jumelle ne se rapproche."""
    if not isinstance(texte, str):
        return ""
    return _NON_MOT.sub(" ", html.unescape(_BALISE.sub("", texte))).strip().lower()


def _normalize_date(valeur: Any) -> str:
    """Les deux formats coexistent dans le corpus : `2023-05-02` (Syceron) et
    `30/06/2020` (questions officielles). Comparer sans les accorder ferait
    conclure « aucune intervention ce jour-là »."""
    if not isinstance(valeur, str):
        return ""
    fr = _DATE_FR.match(valeur)
    if fr:
        return f"{fr.group(3)}-{fr.group(2)}-{fr.group(1)}"
    return valeur[:10]


def _identifiant(entree: dict[str, Any]) -> Any:
    """Le brut nomme la clé `id`, le pivot `intervention_id`."""
    return entree.get("intervention_id", entree.get("id"))


def est_heritee(entree: dict[str, Any]) -> bool:
    """Signature de l'ère NosDéputés : un identifiant **entier**.

    Syceron rend `syceron_…`, les questions officielles `question_…`, le
    Parlement européen `europarl_…`. Aucune source vivante ne rend d'entier —
    vérifié sur les 1 017 574 interventions publiées : 511 entiers, tous liés
    à `www.nosdeputes.fr` ou `2017-2022.nosdeputes.fr`.
    """
    identifiant = _identifiant(entree)
    return isinstance(identifiant, int) and not isinstance(identifiant, bool)


def _est_syceron(entree: dict[str, Any]) -> bool:
    identifiant = _identifiant(entree)
    return isinstance(identifiant, str) and identifiant.startswith("syceron")


def purge_profil(
    profil: dict[str, Any], *, retirer_sans_jumelle: bool = False
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retourne (profil_modifié, entrées_retirées).

    Une entrée héritée n'est retirée que si le profil porte, **le même jour**,
    une entrée Syceron dont le texte normalisé contient le sien ou lui est
    égal. L'inclusion vaut dans les deux sens : NosDéputés coupe parfois une
    prise de parole que le compte rendu définitif rend d'un bloc.

    `retirer_sans_jumelle` étend le retrait aux entrées **sans** jumelle — les
    19 mesurées le 12/09/2026. Ce n'est pas un relâchement de la prudence de
    #387 mais un arbitrage adossé à la source, rendu par la propriétaire le
    12/09/2026 après vérification des 19 dans les archives de l'AN :

      - 6 n'y figurent pas du tout ;
      - 4 y sont attribuées à **quelqu'un d'autre** (Sébastien Chenu, Christine
        Arrighi, Grégoire de Fournas) ;
      - 3 à un **orateur collectif** que #510 refuse de découper ;
      - 6 à la personne nommément, mais sous `id_acteur="PA0"` ou sous un
        identifiant **négatif** — et sur 200 comptes rendus de la XVIe, 118 033
        paragraphes, ces deux formes portent **toutes** `id_mandat="-1"`, les
        `PA0` avec un `code_parole` vide. L'AN ne rattache donc ces propos à
        aucun mandat : les publier sous le nom de la personne ajouterait un lien
        que la source ne fait pas.

    Le drapeau reste **explicite**, et la valeur par défaut prudente : un outil
    qui retire sans jumelle par défaut contredirait la règle qu'il applique.
    """
    interventions = profil.get("interventions") or []
    if not isinstance(interventions, list):
        return profil, []

    syceron_par_jour: dict[str, list[str]] = {}
    for entree in interventions:
        if isinstance(entree, dict) and _est_syceron(entree):
            texte = _normalize_texte(entree.get("texte"))
            if texte:
                syceron_par_jour.setdefault(_normalize_date(entree.get("date")), []).append(texte)

    conserves: list[dict[str, Any]] = []
    retires: list[dict[str, Any]] = []
    for entree in interventions:
        if not isinstance(entree, dict) or not est_heritee(entree):
            conserves.append(entree)
            continue
        texte = _normalize_texte(entree.get("texte"))
        jumelles = syceron_par_jour.get(_normalize_date(entree.get("date")), [])
        jumelee = bool(texte) and any(texte in autre or autre in texte for autre in jumelles)
        if jumelee or retirer_sans_jumelle:
            retires.append(entree)
        else:
            conserves.append(entree)

    if retires:
        profil["interventions"] = conserves
    return profil, retires


def recomposer_champs_derives(profil: dict[str, Any]) -> list[str]:
    """Recalcule les champs **dérivés** d'`interventions[]`, et rend leurs noms.

    §4 : un champ dérivé est recomposé après chaque étape qui le déplace, jamais
    fusionné. Un retrait d'interventions en déplace deux :

      - `tags_thematiques`, qui en dérive entièrement (#710) — `marine-le-pen`
        publiait **470** tags, dont 318 mots-clés de l'ancienne source, et n'en
        garde que 152 une fois recollectée ;
      - `meta.licence_donnees`, que `licences.py` recompose depuis `sources[]`
        **et** les URL d'interventions (#530).

    Sans cette recomposition, le corpus committé publierait des tags dérivés
    d'entrées qui n'y sont plus — et il faudrait attendre un run pour que la
    couche que `web/` lit redevienne cohérente.

    Ne touche au profil que s'il porte déjà le champ : le socle brut n'a ni
    `tags_thematiques` ni `meta.licence_donnees`, et les lui fabriquer ici
    changerait sa nature de couche source-near.
    """
    recomposes = []
    if "tags_thematiques" in profil:
        profil["tags_thematiques"] = deriver_tags_thematiques(profil.get("interventions"))
        recomposes.append("tags_thematiques")
    meta = profil.get("meta")
    if isinstance(meta, dict) and "licence_donnees" in meta:
        appliquer_licence_donnees(profil)
        recomposes.append("meta.licence_donnees")
    return recomposes


def _load(path: Path) -> Optional[dict[str, Any]]:
    """Lit le SOCLE, et lui seul (#580) : les interventions y vivent, le
    manifeste `amendements_partitionnes` est round-trippé tel quel et les
    tranches ne sont jamais ouvertes."""
    try:
        data = charger_socle(path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [!] Lecture impossible ({path.name}) : {exc}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES_DIR), metavar="DOSSIER",
                        help="Couche à traiter : raw_data/profiles (défaut) ou pivot_data/profiles. "
                             "La fusion étant additive aux deux étages, un retrait doit être appliqué aux deux.")
    parser.add_argument("--apply", action="store_true",
                        help="Écrit les profils. Sans cette option, rapport seul.")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic).")
    parser.add_argument("--retirer-sans-jumelle", action="store_true",
                        help="Retire aussi les entrées héritées sans jumelle Syceron — les 19 vérifiées "
                             "une par une dans les archives de l'AN, qui ne les rattache à aucun mandat "
                             "(arbitrage du 12/09/2026).")
    args = parser.parse_args(argv)

    repertoire = Path(args.profiles_dir)
    if not repertoire.is_dir():
        print(f"[!] Répertoire introuvable : {repertoire}", file=sys.stderr)
        return 2

    fichiers = sorted(p for p in repertoire.glob("*.json") if not p.name.endswith(".cosignatures.json"))
    total_retires = 0
    profils_touches = 0
    conserves_sans_jumelle = 0

    for chemin in fichiers:
        slug = chemin.name.replace(".pivot.json", "").replace(".json", "")
        if args.only and slug != args.only:
            continue
        profil = _load(chemin)
        if profil is None:
            continue
        heritees = [e for e in (profil.get("interventions") or []) if isinstance(e, dict) and est_heritee(e)]
        if not heritees:
            continue
        profil, retires = purge_profil(profil, retirer_sans_jumelle=args.retirer_sans_jumelle)
        conserves_sans_jumelle += len(heritees) - len(retires)
        if not retires:
            print(f"  {slug} : {len(heritees)} héritée(s), aucune jumelle Syceron — rien retiré")
            continue
        profils_touches += 1
        total_retires += len(retires)
        recomposes = recomposer_champs_derives(profil)
        detail = f" ; dérivés recomposés : {', '.join(recomposes)}" if recomposes else ""
        print(f"  {slug} : {len(retires)} retirée(s) sur {len(heritees)} héritée(s){detail}")
        if args.apply:
            ecrire_profil_json(chemin, profil)

    mode = "APPLIQUÉ" if args.apply else "SIMULATION (--apply pour écrire)"
    reste = (f"{conserves_sans_jumelle} conservée(s) faute de jumelle."
             if not args.retirer_sans_jumelle
             else "aucune conservée : les entrées sans jumelle sont retirées aussi.")
    print(f"\n[{mode}] {repertoire} — {total_retires} intervention(s) retirée(s) "
          f"sur {profils_touches} profil(s) ; {reste}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
