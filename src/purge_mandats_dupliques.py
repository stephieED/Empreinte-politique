#!/usr/bin/env python3
"""
purge_mandats_dupliques.py — Retire des profils bruts les mandats hérités de
l'ère NosDéputés dont l'équivalent officiel AN est désormais présent (#387,
sous-issue de l'épic taxonomie #382).

Contexte
--------
Avant #382/#384, `_extract_mandats` (candidate_profile.py) mappait **toutes**
les `responsabilites` NosDéputés en dur vers la catégorie `commission` —
groupes d'études, missions d'information, commissions d'enquête et
délégations comprises. Depuis #384, le référentiel officiel AN fournit ces
mêmes mandats correctement catégorisés. Les deux coexistent dans les profils,
car la fusion additive (`merge_profile`) ne remplace jamais une entrée
existante : le même organe apparaît donc deux fois, une fois sous une
étiquette fausse.

Mesuré sur `gabriel-attal` : 10 doublons, p. ex.
    [commission]    "Groupe d'études trufficulture"   (hérité NosDéputés)
    [groupe_etudes] "Trufficulture"                   (AN, #384)

Difficulté centrale : les deux référentiels ne nomment pas les organes de la
même façon — l'AN nomme par le seul thème, NosDéputés préfixe la nature. Un
appariement par libellé exact ne rapproche aucun doublon.

Principe de prudence (arbitrage de #387)
----------------------------------------
Une entrée n'est retirée QUE si son équivalent AN est effectivement présent
dans le profil. En l'absence de correspondance, l'entrée est **conservée** :
elle correspond alors à un mandat réel que l'AN n'expose pas (profil non
résolu AN, ou `typeOrgane` volontairement hors périmètre comme `CMP` /
`PARPOL`). Un faux négatif laisse un doublon visible — bénin ; un faux
positif supprimerait un mandat réel — irréversible hors git.

Garde-fous :
- `--dry-run` par défaut : n'écrit rien sans `--apply` explicite.
- Un profil sans acteurRef résolu est ignoré (aucune source autoritative).
- Une extraction AN vide ou en échec est ignorée (jamais de purge sur une
  absence — résilience #241 : un échec transitoire ne doit rien effacer).
- Idempotent : une seconde exécution ne retire plus rien.

Usage (depuis la racine du dépôt) :
    python3 src/purge_mandats_dupliques.py                 # rapport seul
    python3 src/purge_mandats_dupliques.py --apply         # applique
"""

from __future__ import annotations

import argparse
import json
from functools import lru_cache
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Optional

from candidate_profile import (
    _TYPE_ORGANE_TO_CATEGORIE,
    _extract_acteur_ref,
    _extract_mandats_officiels,
)
from json_io import ecrire_profil_json
from profil_brut import charger_socle

DEFAULT_PROFILES_DIR = Path("raw_data") / "profiles"

# Préfixes de nature ajoutés par NosDéputés devant le libellé de l'organe,
# absents côté AN qui nomme par le seul thème ("Groupe d'études trufficulture"
# vs "Trufficulture"). Liste établie par mesure sur les profils réels, pas a
# priori : un préfixe non listé produit simplement une non-correspondance,
# donc une entrée conservée — jamais une suppression à tort.
_PREFIXES_NATURE: tuple[str, ...] = (
    "groupe d'etudes a vocation internationale sur les",
    "groupe d'etudes a vocation internationale sur la",
    "groupe d'etudes a vocation internationale sur",
    "groupe d'etudes",
    "groupe d'etude",
    "mission d'information commune relative a",
    "mission d'information commune sur",
    "mission d'information sur",
    "mission d'information",
    "commission d'enquete relative a",
    "commission d'enquete sur",
    "commission d'enquete",
    "commission speciale chargee d'examiner",
    "commission speciale",
    "groupe d'amitie",
    "office parlementaire d'evaluation",
    "office parlementaire",
    "section francaise de",
    "section francaise",
    "groupe francais de",
    "groupe francais",
    "delegation de l'assemblee nationale",
    "delegation francaise a",
    "delegation aux",
    "delegation",
)


def _normalize_label(label: Any) -> str:
    """Normalise un libellé d'organe pour l'appariement inter-référentiels :
    accents dépliés, casse et ponctuation de fin neutralisées, préfixe de
    nature retiré. Volontairement conservatrice — elle ne rapproche que des
    libellés qui désignent manifestement le même organe."""
    if not isinstance(label, str):
        return ""
    decomposed = unicodedata.normalize("NFKD", label)
    s = "".join(c for c in decomposed if not unicodedata.combining(c)).lower()
    s = " ".join(s.split())
    for prefixe in _PREFIXES_NATURE:
        if s.startswith(prefixe):
            s = s[len(prefixe):].strip(" :-—–'")
            break
    return s.strip(" .:-—–").strip()


def _mandat_identite(mandat: dict[str, Any]) -> tuple:
    """Identité exacte d'un mandat, pour reconnaître une entrée provenant
    telle quelle de l'extraction AN courante (à conserver absolument)."""
    return (mandat.get("categorie"), mandat.get("label"), mandat.get("debut"))


def _parse_date(valeur: Any) -> Optional[date]:
    if not isinstance(valeur, str) or len(valeur) < 10:
        return None
    try:
        return date.fromisoformat(valeur[:10])
    except ValueError:
        return None


def _periodes_se_chevauchent(
    debut_a: Any, fin_a: Any, debut_b: Any, fin_b: Any
) -> bool:
    """Deux périodes de mandat se recouvrent-elles ?

    Condition indispensable pour conclure au doublon : les deux référentiels
    ne datent PAS un même mandat de façon identique (mesuré — l'écart va de
    quelques jours à plusieurs semaines sur le même organe), donc un
    appariement par date exacte ne rapprocherait rien. Mais un même organe
    peut aussi héberger plusieurs périodes réellement distinctes (entrée,
    sortie, remplacement) : sans test de recouvrement, retirer l'entrée
    héritée effacerait une période que l'AN ne couvre pas.

    Une borne absente est traitée comme ouverte (mandat en cours ou début
    inconnu) — jamais comme aujourd'hui (AGENTS.md §2.5)."""
    da, fa = _parse_date(debut_a), _parse_date(fin_a)
    db, fb = _parse_date(debut_b), _parse_date(fin_b)
    if da is not None and fb is not None and da > fb:
        return False
    if db is not None and fa is not None and db > fa:
        return False
    return True


@lru_cache(maxsize=1)
def _table_correspondance() -> dict[str, Any]:
    """La table slug ↔ acteur AN (#525), lue une fois. Vide si absente."""
    try:
        with open(Path("raw_data") / "correspondance_acteurs_an.json", encoding="utf-8") as f:
            return (json.load(f) or {}).get("correspondances") or {}
    except (OSError, json.JSONDecodeError):
        return {}


def _acteur_du_slug(slug: str) -> Optional[str]:
    """`acteur_an` d'un slug, ou `None`. Jamais une devinette : un slug absent
    de la table rend `None`, et le profil est ignoré plutôt que purgé sur une
    référence approchante (#525 §6)."""
    entree = _table_correspondance().get(slug)
    if not isinstance(entree, dict):
        return None
    return entree.get("acteur_an") or (entree.get("identifiants") or {}).get("an")


def purge_profil(
    profil: dict[str, Any], mandats_an: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Retourne (profil_modifié, entrées_retirées).

    Ne retire une entrée que si TOUTES ces conditions sont réunies :
    1. sa catégorie fait partie de celles couvertes par le référentiel AN ;
    2. elle n'est pas elle-même une entrée AN présente dans le profil ;
    3. son libellé normalisé correspond à celui d'une entrée AN **présente
       dans le profil** ;
    4. sa période recouvre celle de cette entrée — sinon il s'agit d'une
       période distincte du même organe, que l'AN ne couvre pas, et la
       retirer effacerait une donnée réelle.

    Point critique de la condition 3 : la comparaison porte sur les entrées AN
    **effectivement présentes dans le profil**, jamais sur l'extraction AN
    fraîche. Un profil pas encore régénéré avec le mapping élargi (#384)
    contient les entrées héritées mais pas encore leurs équivalents AN :
    se fier à l'extraction ferait disparaître l'organe du profil au lieu de
    dédoublonner. Mesuré lors de la mise au point : 18 organes distincts
    perdus sur `benjamin-haddad` avec la comparaison naïve. Conséquence
    voulue : ce script n'a d'effet qu'après régénération, ce qui est
    exactement la garantie « ne jamais retirer avant que l'équivalent soit
    présent » posée par #387.
    """
    categories_an = set(_TYPE_ORGANE_TO_CATEGORIE.values())
    identites_an = {_mandat_identite(m) for m in mandats_an}

    # Entrées du profil qui proviennent de l'extraction AN courante : ce sont
    # elles, et elles seules, qui peuvent rendre une entrée héritée redondante.
    an_dans_profil = [
        m for m in (profil.get("mandats") or [])
        if _mandat_identite(m) in identites_an
    ]
    an_par_label: dict[str, list[dict[str, Any]]] = {}
    for m in an_dans_profil:
        cle = _normalize_label(m.get("label"))
        if cle:
            an_par_label.setdefault(cle, []).append(m)

    conserves: list[dict[str, Any]] = []
    retires: list[dict[str, Any]] = []
    for mandat in profil.get("mandats") or []:
        candidats = (
            an_par_label.get(_normalize_label(mandat.get("label")), [])
            if mandat.get("categorie") in categories_an
            and _mandat_identite(mandat) not in identites_an
            else []
        )
        doublon = any(
            _periodes_se_chevauchent(
                mandat.get("debut"), mandat.get("fin"), m.get("debut"), m.get("fin")
            )
            for m in candidats
        )
        if doublon:
            retires.append(mandat)
        else:
            conserves.append(mandat)

    if retires:
        profil["mandats"] = conserves
    return profil, retires


def _load(path: Path) -> Optional[dict[str, Any]]:
    """Lit le SOCLE `<slug>.json`, et lui seul (#580).

    Ce script ne touche que `mandats`, qui vit dans le socle. Recomposer les
    amendements pour les réécrire à l'identique coûterait 56 Mo de mémoire par
    profil sans rien changer. Le manifeste `amendements_partitionnes` est donc
    relu et réécrit **tel quel**, et les tranches ne sont pas ouvertes.

    Corollaire à ne pas casser : la lecture et l'écriture doivent rester
    accordées. Lire par `charger_profil_brut` en continuant d'écrire par
    `ecrire_profil_json` remettrait `amendements` dans le socle **à côté** du
    manifeste — la donnée serait présente deux fois, et le profil pèserait de
    nouveau ses 56 Mo.
    """
    try:
        data = charger_socle(path)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [!] Lecture impossible ({path.name}) : {exc}", file=sys.stderr)
        return None
    return data if isinstance(data, dict) else None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profiles-dir", default=str(DEFAULT_PROFILES_DIR), metavar="DOSSIER",
                        help=f"Dossier des profils bruts (défaut : {DEFAULT_PROFILES_DIR}).")
    parser.add_argument("--apply", action="store_true",
                        help="Écrit réellement les modifications (sinon : rapport seul, aucun fichier touché).")
    parser.add_argument("--only", metavar="SLUG", help="Ne traiter qu'un profil (diagnostic).")
    args = parser.parse_args(argv)

    profiles_dir = Path(args.profiles_dir)
    if not profiles_dir.is_dir():
        print(f"[!] Dossier introuvable : {profiles_dir}", file=sys.stderr)
        return 1

    # `Path.glob` remonte les fichiers cachés, contrairement au module `glob` :
    # sans ce filtre, `raw_data/profiles/.generation_checkpoint.json` gonflerait
    # le compteur « ignorés sans acteur » (#518). Même convention que
    # `merge_profile`, `scrutins_index`, `amendements_index`.
    chemins = sorted(
        c for c in profiles_dir.glob("*.json") if not c.name.startswith("."))
    if args.only:
        chemins = [p for p in chemins if p.stem == args.only]

    total_retires = 0
    profils_modifies = 0
    ignores_sans_acteur = 0
    ignores_an_vide = 0

    for chemin in chemins:
        profil = _load(chemin)
        if profil is None:
            continue

        acteur_ref = _extract_acteur_ref((profil.get("identite") or {}).get("url_an_ou_senat") or "")
        if not acteur_ref:
            # Un profil PIVOT ne porte ni `url_an_ou_senat` ni `identifiants` :
            # son acteur vit dans la table de correspondance, qui est
            # l'autorité du dépôt sur « ce slug, cet acteur AN » (#525). Sans ce
            # repli, la purge ne peut pas passer au pivot — et elle DOIT y
            # passer, `merge_pivot_profile` étant additif comme la fusion brute.
            acteur_ref = _acteur_du_slug(chemin.stem.removesuffix(".pivot"))
        if not acteur_ref:
            ignores_sans_acteur += 1
            continue

        mandats_an = _extract_mandats_officiels(acteur_ref)
        if not mandats_an:
            # Jamais de purge sur une extraction vide : indiscernable d'un
            # échec transitoire (résilience #241).
            ignores_an_vide += 1
            continue

        _, retires = purge_profil(profil, mandats_an)
        if not retires:
            continue

        profils_modifies += 1
        total_retires += len(retires)
        print(f"  {chemin.stem} : {len(retires)} doublon(s)")
        for m in retires[:3]:
            print(f"      - [{m.get('categorie')}] {str(m.get('label'))[:66]}")
        if len(retires) > 3:
            print(f"      … et {len(retires) - 3} autre(s)")

        if args.apply:
            ecrire_profil_json(chemin, profil)

    mode = "APPLIQUÉ" if args.apply else "SIMULATION (--apply pour écrire)"
    print(f"\n=== {mode} ===")
    print(f"  Profils analysés          : {len(chemins)}")
    print(f"  Profils modifiés          : {profils_modifies}")
    print(f"  Doublons retirés          : {total_retires}")
    print(f"  Ignorés (pas d'acteurRef) : {ignores_sans_acteur}")
    print(f"  Ignorés (AN vide/échec)   : {ignores_an_vide}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
