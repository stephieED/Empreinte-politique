#!/usr/bin/env python3
"""Relire à la source les signataires de quelques amendements publiés (#1248, lot 3).

Pourquoi ce module existe
-------------------------
Les lots 1 et 2 relisent les votes et les mandats. Celui-ci relit **qui a signé
un amendement** : pour chaque amendement tiré, les signataires publiés sont
confrontés à la page de l'amendement sur le site de l'Assemblée
(`/dyn/<législature>/amendements/<uid>`, qui redirige vers l'adresse lisible).
La collecte, elle, lit les archives open data des amendements.

Deux faits publiés sont relus, et ce sont deux lectures du site :

- **l'index de la législature** (`pivot_data/amendements/<n>.json` et
  `<n>.cosignatures.json`) : le premier signataire, et les cosignataires ;
- **les profils des signataires** : chaque député nommé par la page, et qui a
  un profil, doit porter l'amendement avec le bon rôle (`auteur_principal` ou
  `cosignataire`). C'est ce que lit la section amendements d'une fiche.

Le tirage
---------
Dix amendements par run : sept des trente derniers jours, trois sur tout le
corpus — le partage que la propriétaire a arbitré pour les votes le
30/10/2026, repris ici. La XIVe législature est exclue du tirage : la page
d'un de ses amendements, demandée par son identifiant, répond 404 (mesuré le
02/11/2026). La graine est le numéro du run.

La lecture de la page
---------------------
Les signataires sont dans le bloc « Déposé par », dans l'ordre : le premier
signataire d'abord, puis les cosignataires, chacun avec le lien vers sa fiche
(`/dyn/deputes/PA…`). Le bloc s'arrête à la première section du texte de
l'amendement.

| Cas | Verdict |
| --- | --- |
| même premier signataire, mêmes cosignataires, mêmes rôles dans les profils | concordant |
| premier signataire différent ; cosignataire présent d'un seul côté ; profil sans l'amendement, ou avec un autre rôle ; profil qui le porte sans que la page le nomme | **écart** |
| signataire sans profil dans le corpus | hors périmètre |
| page injoignable, ou sans bloc « Déposé par » lisible | non vérifié — jamais un écart (§2 règle 5) |

Il ne bloque rien : il signale, comme les lots 1 et 2.
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

NB_RECENTS = 7
NB_TOTAL = 10
FENETRE_JOURS = 30

#: Les législatures dont la page d'amendement répond par identifiant.
LEGISLATURES = ("15", "16", "17")

URL_AMENDEMENT = "https://www.assemblee-nationale.fr/dyn/{legislature}/amendements/{uid}"
DELAI_ENTRE_PAGES = 1.0
TIMEOUT = 30
ENTETES = {"User-Agent": "Empreinte-politique (relecture des amendements publiés, #1248)"}

AUTEUR = "auteur_principal"
COSIGNATAIRE = "cosignataire"

_DEPOSE_PAR = "Déposé par"
_FIN_DU_BLOC = '<div class="amendement-section"'
_ACTEUR = re.compile(r'href="/dyn/deputes/(PA\d+)"')


class PageIllisible(ValueError):
    """La page a répondu, mais pas sous la forme connue."""


def lire_signataires(html: str) -> tuple[str, list[str]]:
    """(premier signataire, cosignataires dans l'ordre de la page), en `an:PA…`."""
    debut = html.find(_DEPOSE_PAR)
    if debut < 0:
        raise PageIllisible("aucun bloc « Déposé par »")
    fin = html.find(_FIN_DU_BLOC, debut)
    bloc = html[debut: fin if fin > 0 else None]
    acteurs: list[str] = []
    for acteur in _ACTEUR.findall(bloc):
        if f"an:{acteur}" not in acteurs:
            acteurs.append(f"an:{acteur}")
    if not acteurs:
        raise PageIllisible("bloc « Déposé par » sans aucun député nommé")
    return acteurs[0], acteurs[1:]


@dataclass
class Amendement:
    uid: str                    # `an:AMANR5L17…`
    legislature: str
    date: Optional[str]
    premier: Optional[str]
    cosignataires: list[str]

    @property
    def url(self) -> str:
        return URL_AMENDEMENT.format(legislature=self.legislature, uid=self.uid.removeprefix("an:"))


def amendements_publies(dossier: Path, legislatures: Iterable[str] = LEGISLATURES) -> list[Amendement]:
    """Les amendements des index publiés, sans leurs cosignataires : le tirage
    n'en a pas besoin, et `cosignataires_des_tires` les lit ensuite pour les
    seuls tirés. Garder les 107 000 listes de la XVIIe pour en relire dix
    coûtait un gigaoctet de mémoire (#628)."""
    tous = []
    for legislature in legislatures:
        index = dossier / f"{legislature}.json"
        if not index.is_file():
            continue
        with open(index, encoding="utf-8") as f:
            amendements = json.load(f).get("amendements") or {}
        for uid, entree in amendements.items():
            tous.append(Amendement(
                uid=uid, legislature=legislature, date=entree.get("date"),
                premier=entree.get("premier_signataire"), cosignataires=[],
            ))
        del amendements
    return sorted(tous, key=lambda a: a.uid)


def cosignataires_des_tires(dossier: Path, tirage: list[Amendement]) -> None:
    """Complète les amendements tirés de leurs cosignataires publiés."""
    for legislature in sorted({a.legislature for a in tirage}):
        chemin = dossier / f"{legislature}.cosignatures.json"
        if not chemin.is_file():
            continue
        with open(chemin, encoding="utf-8") as f:
            cosignatures = json.load(f).get("co_signataires") or {}
        for amendement in tirage:
            if amendement.legislature == legislature:
                amendement.cosignataires = list(cosignatures.get(amendement.uid) or [])
        del cosignatures


def tirer(amendements: list[Amendement], aujourd_hui: dt.date, graine: int,
          nb_recents: int = NB_RECENTS, nb_total: int = NB_TOTAL) -> list[Amendement]:
    borne = (aujourd_hui - dt.timedelta(days=FENETRE_JOURS)).isoformat()
    tirables = sorted(amendements, key=lambda a: a.uid)
    recents = [a for a in tirables if (a.date or "") >= borne]
    hasard = random.Random(graine)
    choisis = hasard.sample(recents, min(nb_recents, len(recents)))
    pris = {a.uid for a in choisis}
    reste = [a for a in tirables if a.uid not in pris]
    return choisis + hasard.sample(reste, min(nb_total - len(choisis), len(reste)))


def slugs_par_acteur(correspondance: Path) -> dict[str, str]:
    """`an:PA…` → slug de profil, d'après la table de correspondance (#525)."""
    with open(correspondance, encoding="utf-8") as f:
        table = json.load(f).get("correspondances") or {}
    return {
        f"an:{(entree.get('identifiants') or {}).get('an')}": slug
        for slug, entree in table.items()
        if (entree.get("identifiants") or {}).get("an")
    }


def roles_publies(profils_dir: Path, slugs: Iterable[str], uids: set[str]) -> dict[str, dict[str, str]]:
    """{slug: {uid: rôle}} pour les profils demandés, réduits aux amendements
    tirés (#628). Un slug sans fichier de profil est absent du résultat."""
    roles: dict[str, dict[str, str]] = {}
    for slug in sorted(set(slugs)):
        chemin = profils_dir / f"{slug}.pivot.json"
        if not chemin.is_file():
            continue
        with open(chemin, encoding="utf-8") as f:
            profil = json.load(f)
        roles[slug] = {
            a["amendement_id"]: a.get("role_signataire")
            for a in profil.get("amendements") or []
            if isinstance(a, dict) and a.get("amendement_id") in uids
        }
    return roles


@dataclass
class Resultat:
    uid: str
    url: str
    date: Optional[str]
    non_verifie: Optional[str] = None
    signataires: int = 0
    concordants: int = 0
    hors_perimetre: list[str] = field(default_factory=list)
    ecarts: list[dict[str, Any]] = field(default_factory=list)


def comparer(
    amendement: Amendement,
    premier_page: str,
    cosignataires_page: list[str],
    slugs: dict[str, str],
    roles: dict[str, dict[str, str]],
) -> tuple[int, list[str], list[dict[str, Any]]]:
    """Rend (signataires concordants, hors périmètre, écarts)."""
    ecarts: list[dict[str, Any]] = []
    if amendement.premier != premier_page:
        ecarts.append({"quoi": "premier signataire", "page": premier_page, "publie": amendement.premier})
    page_co, index_co = set(cosignataires_page), set(amendement.cosignataires)
    for acteur in sorted(page_co - index_co):
        ecarts.append({"quoi": "cosignataire absent de l'index", "page": acteur, "publie": None})
    for acteur in sorted(index_co - page_co):
        ecarts.append({"quoi": "cosignataire que la page ne nomme pas", "page": None, "publie": acteur})

    attendus = {premier_page: AUTEUR, **{a: COSIGNATAIRE for a in cosignataires_page}}
    concordants, hors = 0, []
    for acteur, role in attendus.items():
        slug = slugs.get(acteur)
        if slug is None or slug not in roles:
            hors.append(acteur)
            continue
        publie = roles[slug].get(amendement.uid)
        if publie == role:
            concordants += 1
        else:
            ecarts.append({"quoi": "rôle sur le profil", "page": f"{slug} : {role}", "publie": publie})
    for slug, par_uid in sorted(roles.items()):
        acteur = next((a for a, s in slugs.items() if s == slug), None)
        if amendement.uid in par_uid and acteur not in attendus:
            ecarts.append({"quoi": "profil qui porte l'amendement sans que la page le nomme",
                           "page": None, "publie": f"{slug} : {par_uid[amendement.uid]}"})
    return concordants, hors, ecarts


def telecharger(url: str) -> str:
    import requests  # noqa: PLC0415 — seul appel réseau du module

    reponse = requests.get(url, headers=ENTETES, timeout=TIMEOUT)
    reponse.raise_for_status()
    return reponse.text


def relire(
    tirage: list[Amendement],
    slugs: dict[str, str],
    profils_dir: Path,
    obtenir: Callable[[str], str] = telecharger,
    delai: float = DELAI_ENTRE_PAGES,
) -> list[Resultat]:
    lus: list[tuple[Amendement, Resultat, Optional[tuple[str, list[str]]]]] = []
    for rang, amendement in enumerate(tirage):
        if rang and delai:
            time.sleep(delai)
        res = Resultat(uid=amendement.uid, url=amendement.url, date=amendement.date)
        signataires = None
        try:
            signataires = lire_signataires(obtenir(amendement.url))
        except PageIllisible as exc:
            res.non_verifie = f"page illisible : {exc}"
        except Exception as exc:  # noqa: BLE001 — une source muette n'est pas un écart
            res.non_verifie = f"page injoignable : {type(exc).__name__}: {exc}"
        lus.append((amendement, res, signataires))

    # Les profils à lire : tous ceux qu'une page ou un index nomme.
    acteurs = {a for amendement, _r, s in lus if s for a in (s[0], *s[1], amendement.premier, *amendement.cosignataires) if a}
    roles = roles_publies(profils_dir, (slugs[a] for a in acteurs if a in slugs), {a.uid for a in tirage})
    resultats = []
    for amendement, res, signataires in lus:
        if signataires is not None:
            premier, cosignataires = signataires
            res.signataires = 1 + len(cosignataires)
            res.concordants, res.hors_perimetre, res.ecarts = comparer(
                amendement, premier, cosignataires, slugs, roles
            )
        resultats.append(res)
    return resultats


def rapport(resultats: list[Resultat], graine: int) -> tuple[str, dict[str, Any]]:
    verifies = [r for r in resultats if r.non_verifie is None]
    nb_ecarts = sum(len(r.ecarts) for r in verifies)
    resume = {
        "graine": graine,
        "amendements_tires": len(resultats),
        "amendements_verifies": len(verifies),
        "amendements_non_verifies": len(resultats) - len(verifies),
        "signataires_lus": sum(r.signataires for r in verifies),
        "signatures_concordantes": sum(r.concordants for r in verifies),
        "ecarts": nb_ecarts,
        "amendements_avec_ecart": sum(1 for r in verifies if r.ecarts),
        "signataires_hors_perimetre": sum(len(r.hors_perimetre) for r in verifies),
        "resultats": [r.__dict__ for r in resultats],
    }
    lignes = [
        f"Tirage de {len(resultats)} amendements (graine {graine}) : "
        f"{len(verifies)} relus à la source, {resume['amendements_non_verifies']} non vérifiés.",
        "",
        f"- Signataires lus sur les pages : {resume['signataires_lus']}",
        f"- Signatures concordantes (index et profil) : **{resume['signatures_concordantes']}**",
        f"- Écarts : **{nb_ecarts}**, sur {resume['amendements_avec_ecart']} amendement(s)",
        f"- Signataires sans profil dans le corpus (hors périmètre) : {resume['signataires_hors_perimetre']}",
        "",
        "| Amendement | Date | Signataires | Concordants | Écarts | Hors périmètre | État |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in resultats:
        etat = r.non_verifie or ("écart" if r.ecarts else "concordant")
        lignes.append(
            f"| [{r.uid.removeprefix('an:')}]({r.url}) | {r.date or '—'} | {r.signataires} | "
            f"{r.concordants} | {len(r.ecarts)} | {len(r.hors_perimetre)} | {etat} |"
        )
    avec_ecart = [r for r in verifies if r.ecarts]
    if avec_ecart:
        lignes += ["", "### Écarts", "", "| Amendement | Quoi | Page de l'Assemblée | Publié |",
                   "| --- | --- | --- | --- |"]
        for r in avec_ecart:
            for e in r.ecarts:
                lignes.append(f"| {r.uid.removeprefix('an:')} | {e['quoi']} | {e['page'] or '—'} | {e['publie'] or '—'} |")
    return "\n".join(lignes) + "\n", resume


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--amendements-dir", type=Path, default=Path("pivot_data/amendements"))
    parseur.add_argument("--profils-dir", type=Path, default=Path("pivot_data/profiles"))
    parseur.add_argument("--correspondance", type=Path, default=Path("raw_data/correspondance_acteurs_an.json"))
    parseur.add_argument("--graine", type=int, required=True, help="le numéro du run, en CI")
    parseur.add_argument("--date", help="jour du tirage, AAAA-MM-JJ (défaut : aujourd'hui)")
    parseur.add_argument("--out", type=Path, required=True)
    parseur.add_argument("--out-json", type=Path, required=True)
    args = parseur.parse_args(argv)

    aujourd_hui = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    tirage = tirer(amendements_publies(args.amendements_dir), aujourd_hui, args.graine)
    cosignataires_des_tires(args.amendements_dir, tirage)
    resultats = relire(tirage, slugs_par_acteur(args.correspondance), args.profils_dir)
    texte, resume = rapport(resultats, args.graine)
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
