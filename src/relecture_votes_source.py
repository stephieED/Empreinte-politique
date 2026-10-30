#!/usr/bin/env python3
"""Relire à la source quelques positions de vote publiées, par une autre route (#1248).

Pourquoi ce module existe
-------------------------
Les seize audits du dépôt comparent les données entre elles ; aucun ne
retournait à la source (#1248, mesuré le 07/10/2026). Celui-ci part de ce qui
est publié (`pivot_data/`) et le relit sur la **page publique** de l'Assemblée,
celle que `source_url` donne au lecteur : la collecte, elle, lit les archives
open data. Deux routes ; si elles divergent, l'une a tort, et le run le dit.

Le tirage, arbitré par la propriétaire le 30/10/2026
---------------------------------------------------
**Dix scrutins par run : sept des trente derniers jours, trois sur tout le
corpus.** Au hasard sur tout le corpus, dix tirages donnaient 0,4 scrutin
récent par run (768 des 19 078 scrutins publiés dataient des trente derniers
jours, le 30/10/2026), alors que c'est là qu'une panne de collecte frappe
d'abord. Les trois autres gardent sous contrôle les législatures closes, dont
une erreur ne se corrigerait jamais seule. Moins de sept scrutins récents
(vacances parlementaires) : le reste est pris sur tout le corpus.

La graine est le numéro du run : un tirage se rejoue à l'identique.

La comparaison se fait personne par personne
--------------------------------------------
Jamais sur les totaux. Le 30/10/2026, sur le scrutin 8705, la page comptait 503
« pour » et nos profils 501 : les deux manquants étaient les deux non-inscrits
qui ont voté, et que le corpus ne collecte pas (aucun profil). Un total aurait
signalé un écart qui n'en est pas un, et en aurait masqué un vrai qui le
compenserait.

| Cas | Verdict |
| --- | --- |
| même position des deux côtés | concordant |
| positions différentes | **écart** |
| la page nomme un député qui a un profil, sans position chez nous | **écart** |
| nous publions une position que la page ne nomme pas | **écart** |
| la page nomme un député sans profil chez nous (non-inscrit…) | hors périmètre |
| la page nomme un **non-votant** qui a un profil, sans position chez nous | divergence entre sources |
| la page ne répond pas, ou sa forme a changé | non vérifié — jamais un écart (§2 règle 5) |

**La divergence entre sources, arbitrée le 30/10/2026 (option B).** Les
archives open data de l'Assemblée ne citent pas toujours les non-votants que la
page nomme : celle de la XVIe ne cite Yaël Braun-Pivet, présidente, que dans 357
de ses 4 106 scrutins, et la page la nomme « non votant » partout. La collecte
reproduit fidèlement l'archive : ce n'est pas une erreur de notre côté, et le
compter comme écart aurait ouvert une issue un run sur deux pour une cause
connue. Le cas est listé à part, sans issue. **Il ne vaut que pour les
non-votants** : un « pour », un « contre » ou une abstention absents chez nous
restent des écarts.

Les positions `absent` et `excuse` ne se comparent pas : la page ne liste pas
les absents, et aucune page de présence n'est lue ici (§2 règle 3).

Ce que ce contrôle ne fait pas
------------------------------
Il ne bloque rien : il signale, comme `validate_profil` (#1223). Un tirage au
sort qui bloquerait rendrait les runs imprévisibles.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

#: Le tirage arbitré le 30/10/2026.
NB_RECENTS = 7
NB_TOTAL = 10
FENETRE_JOURS = 30

#: Les intitulés des listes nominatives sur la page de scrutin, et la position
#: publiée qui leur répond. Un intitulé absent de cette table rend la page
#: « non vérifiée » : sa forme a changé, et deviner serait inventer.
POSITIONS_PAGE = {
    "Pour": "pour",
    "Contre": "contre",
    "Abstention": "abstention",
    "Non votant": "non_votant",
    "Non votants": "non_votant",
    "Non-votant": "non_votant",
    "Non-votants": "non_votant",
}

#: Les positions que la page ne liste jamais : elles ne se comparent pas.
POSITIONS_NON_COMPAREES = frozenset({"absent", "excuse"})

#: La section qui suit les listes nominatives. Ce qu'elle nomme (les votes que
#: des députés disent avoir voulu émettre) n'est pas le vote enregistré : la
#: lecture s'arrête avant elle.
_MISES_AU_POINT = re.compile(r"<h2[^>]*>\s*Mises au point\s*</h2>")
_JETONS = re.compile(
    r'<span class="h6[^"]*">\s*([^<]+?)\s*</span>'
    r'|data-acteur-id="(PA\d+)[^"]*"\s*>\s*<(?:a|span)[^>]*>\s*([^<]*?)\s*</(?:a|span)>'
)
# Le nom d'un votant est un lien vers sa fiche, ou un simple texte quand la
# page n'en donne pas (mesuré le 30/10/2026 sur le scrutin 3305 : Manon
# Bouquin, `<span class="_small">`). Ne lire que les liens comptait ces votants
# comme « non nommés », donc comme des écarts.

DELAI_ENTRE_PAGES = 1.0
TIMEOUT = 30
ENTETES = {"User-Agent": "Empreinte-politique (relecture des votes publiés, #1248)"}

CONCORDANT = "concordant"
DIVERGENCE = "divergence"
ECART = "ecart"
HORS_PERIMETRE = "hors_perimetre"


class PageIllisible(ValueError):
    """La page a répondu, mais pas sous la forme connue."""


def lire_page(html: str) -> dict[str, tuple[str, str]]:
    """Les votants nommés par la page : `{PA…: (position, nom)}`.

    Lève `PageIllisible` sur un intitulé de liste inconnu, sur un nom qui ne
    suit aucun intitulé, ou sur une page sans aucun votant nommé.
    """
    coupure = _MISES_AU_POINT.search(html)
    if coupure:
        html = html[: coupure.start()]
    position: Optional[str] = None
    votants: dict[str, tuple[str, str]] = {}
    for jeton in _JETONS.finditer(html):
        intitule, acteur, nom = jeton.groups()
        if intitule is not None:
            if intitule not in POSITIONS_PAGE:
                raise PageIllisible(f"intitulé de liste inconnu : {intitule!r}")
            position = POSITIONS_PAGE[intitule]
            continue
        if position is None:
            raise PageIllisible(f"{acteur} nommé avant tout intitulé de liste")
        votants[acteur] = (position, nom)
    if not votants:
        raise PageIllisible("aucun votant nommé")
    return votants


def tirer(
    scrutins: list[dict[str, Any]],
    aujourd_hui: dt.date,
    graine: int,
    nb_recents: int = NB_RECENTS,
    nb_total: int = NB_TOTAL,
    fenetre_jours: int = FENETRE_JOURS,
) -> list[dict[str, Any]]:
    """Le tirage du run, récents d'abord. Seuls les scrutins qui portent une
    `source_url` sont tirables : c'est elle qu'on relit."""
    tirables = sorted(
        (s for s in scrutins if s.get("source_url") and s.get("id")), key=lambda s: s["id"]
    )
    borne = (aujourd_hui - dt.timedelta(days=fenetre_jours)).isoformat()
    recents = [s for s in tirables if (s.get("date") or "") >= borne]
    hasard = random.Random(graine)
    choisis = hasard.sample(recents, min(nb_recents, len(recents)))
    deja = {s["id"] for s in choisis}
    reste = [s for s in tirables if s["id"] not in deja]
    choisis += hasard.sample(reste, min(nb_total - len(choisis), len(reste)))
    return choisis


def positions_publiees(
    chemins_profils: Iterable[Path], ids: set[str]
) -> tuple[dict[str, dict[str, str]], set[str]]:
    """Ce que nos profils publient pour les scrutins tirés.

    Rend `{scrutin_id: {PA…: position}}` et l'ensemble des identifiants de
    député qui ont un profil. Lecture un profil à la fois, réduit aussitôt
    (#628) : rien d'autre n'est gardé.
    """
    par_scrutin: dict[str, dict[str, str]] = {i: {} for i in ids}
    avec_profil: set[str] = set()
    for chemin in chemins_profils:
        with open(chemin, encoding="utf-8") as f:
            profil = json.load(f)
        acteur = (profil.get("identifiants") or {}).get("an")
        if not acteur:
            continue
        avec_profil.add(acteur)
        for vote in profil.get("votes") or []:
            sid = vote.get("scrutin_id")
            if sid in par_scrutin and vote.get("position") is not None:
                par_scrutin[sid][acteur] = vote["position"]
    return par_scrutin, avec_profil


@dataclass
class Resultat:
    scrutin_id: str
    source_url: str
    date: Optional[str]
    recent: bool
    non_verifie: Optional[str] = None
    concordants: int = 0
    hors_perimetre: list[str] = field(default_factory=list)
    divergences: list[dict[str, Any]] = field(default_factory=list)
    ecarts: list[dict[str, Any]] = field(default_factory=list)


def comparer(
    page: dict[str, tuple[str, str]],
    publiees: dict[str, str],
    avec_profil: set[str],
) -> tuple[int, list[str], list[dict[str, Any]], list[dict[str, Any]]]:
    """Compare personne par personne.

    Rend (concordants, hors périmètre, divergences entre sources, écarts).
    """
    concordants, hors, divergences, ecarts = 0, [], [], []
    for acteur, (position_page, nom) in sorted(page.items()):
        notre = publiees.get(acteur)
        if notre is None:
            if acteur in avec_profil and position_page == "non_votant":
                divergences.append({"acteur": acteur, "nom": nom, "page": position_page, "publie": None})
            elif acteur in avec_profil:
                ecarts.append({"acteur": acteur, "nom": nom, "page": position_page, "publie": None})
            else:
                hors.append(f"{nom} ({acteur})")
        elif notre in POSITIONS_NON_COMPAREES or notre != position_page:
            ecarts.append({"acteur": acteur, "nom": nom, "page": position_page, "publie": notre})
        else:
            concordants += 1
    for acteur, notre in sorted(publiees.items()):
        if acteur not in page and notre not in POSITIONS_NON_COMPAREES:
            ecarts.append({"acteur": acteur, "nom": None, "page": None, "publie": notre})
    return concordants, hors, divergences, ecarts


def telecharger(url: str) -> str:
    import requests  # noqa: PLC0415 — seul appel réseau du module

    reponse = requests.get(url, headers=ENTETES, timeout=TIMEOUT)
    reponse.raise_for_status()
    return reponse.text


def relire(
    tirage: list[dict[str, Any]],
    publiees: dict[str, dict[str, str]],
    avec_profil: set[str],
    borne_recente: str,
    obtenir: Callable[[str], str] = telecharger,
    delai: float = DELAI_ENTRE_PAGES,
) -> list[Resultat]:
    resultats = []
    for rang, scrutin in enumerate(tirage):
        if rang and delai:
            time.sleep(delai)
        res = Resultat(
            scrutin_id=scrutin["id"],
            source_url=scrutin["source_url"],
            date=scrutin.get("date"),
            recent=(scrutin.get("date") or "") >= borne_recente,
        )
        try:
            page = lire_page(obtenir(scrutin["source_url"]))
        except PageIllisible as exc:
            res.non_verifie = f"page illisible : {exc}"
        except Exception as exc:  # noqa: BLE001 — une source muette n'est pas un écart
            res.non_verifie = f"page injoignable : {type(exc).__name__}: {exc}"
        else:
            res.concordants, res.hors_perimetre, res.divergences, res.ecarts = comparer(
                page, publiees.get(scrutin["id"], {}), avec_profil
            )
        resultats.append(res)
    return resultats


def rapport(resultats: list[Resultat], graine: int) -> tuple[str, dict[str, Any]]:
    verifies = [r for r in resultats if r.non_verifie is None]
    nb_ecarts = sum(len(r.ecarts) for r in verifies)
    resume = {
        "graine": graine,
        "scrutins_tires": len(resultats),
        "scrutins_verifies": len(verifies),
        "scrutins_non_verifies": len(resultats) - len(verifies),
        "positions_concordantes": sum(r.concordants for r in verifies),
        "positions_en_ecart": nb_ecarts,
        "scrutins_avec_ecart": sum(1 for r in verifies if r.ecarts),
        "votants_hors_perimetre": sum(len(r.hors_perimetre) for r in verifies),
        "divergences_entre_sources": sum(len(r.divergences) for r in verifies),
        "resultats": [r.__dict__ for r in resultats],
    }
    lignes = [
        f"Tirage de {len(resultats)} scrutins (graine {graine}) : "
        f"{len(verifies)} relus à la source, {resume['scrutins_non_verifies']} non vérifiés.",
        "",
        f"- Positions concordantes : **{resume['positions_concordantes']}**",
        f"- Positions en écart : **{nb_ecarts}**, sur {resume['scrutins_avec_ecart']} scrutin(s)",
        f"- Votants sans profil dans le corpus (hors périmètre) : {resume['votants_hors_perimetre']}",
        f"- Non-votants nommés par la page et absents de l'open data (divergence entre "
        f"sources, sans issue) : {resume['divergences_entre_sources']}",
        "",
        "| Scrutin | Date | Tirage | Concordantes | Écarts | Divergences | Hors périmètre | État |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in resultats:
        etat = r.non_verifie or ("écart" if r.ecarts else "concordant")
        lignes.append(
            f"| [{r.scrutin_id}]({r.source_url}) | {r.date or '—'} | "
            f"{'30 derniers jours' if r.recent else 'tout le corpus'} | {r.concordants} | "
            f"{len(r.ecarts)} | {len(r.divergences)} | {len(r.hors_perimetre)} | {etat} |"
        )
    detail = [r for r in verifies if r.ecarts]
    if detail:
        lignes += ["", "### Écarts", "", "| Scrutin | Député | Page de l'Assemblée | Publié |",
                   "| --- | --- | --- | --- |"]
        for r in detail:
            for e in r.ecarts:
                qui = f"{e['nom']} ({e['acteur']})" if e["nom"] else e["acteur"]
                lignes.append(
                    f"| {r.scrutin_id} | {qui} | {e['page'] or 'non nommé'} | {e['publie'] or 'aucune position'} |"
                )
    avec_divergence = [r for r in verifies if r.divergences]
    if avec_divergence:
        lignes += ["", "### Divergences entre sources (sans issue)", "",
                   "| Scrutin | Député | Page de l'Assemblée | Publié |", "| --- | --- | --- | --- |"]
        for r in avec_divergence:
            for e in r.divergences:
                lignes.append(f"| {r.scrutin_id} | {e['nom']} ({e['acteur']}) | {e['page']} | aucune position |")
    return "\n".join(lignes) + "\n", resume


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--scrutins", type=Path, default=Path("pivot_data/scrutins.json"))
    parseur.add_argument("--profils-dir", type=Path, default=Path("pivot_data/profiles"))
    parseur.add_argument("--graine", type=int, required=True, help="le numéro du run, en CI")
    parseur.add_argument("--date", help="jour du tirage, AAAA-MM-JJ (défaut : aujourd'hui)")
    parseur.add_argument("--out", type=Path, required=True)
    parseur.add_argument("--out-json", type=Path, required=True)
    args = parseur.parse_args(argv)

    aujourd_hui = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    borne = (aujourd_hui - dt.timedelta(days=FENETRE_JOURS)).isoformat()
    with open(args.scrutins, encoding="utf-8") as f:
        scrutins = json.load(f)["scrutins"]
    tirage = tirer(scrutins, aujourd_hui, args.graine)
    publiees, avec_profil = positions_publiees(
        sorted(args.profils_dir.glob("*.pivot.json")), {s["id"] for s in tirage}
    )
    resultats = relire(tirage, publiees, avec_profil, borne)
    texte, resume = rapport(resultats, args.graine)
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
