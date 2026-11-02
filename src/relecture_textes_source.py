#!/usr/bin/env python3
"""Relire à la source le stade et les dates de quelques textes portés publiés (#1248, lot 4).

Pourquoi ce module existe
-------------------------
Les lots 1 à 3 relisent les votes, les mandats et les signatures d'amendement.
Celui-ci relit **les textes portés** — la ligne de chaque texte sur une fiche :
jusqu'où il est allé, et quand. Pour chaque dossier tiré, chaque profil qui le
publie est confronté à la page du dossier législatif sur le site de
l'Assemblée (son `source_url`), qui donne la chronologie des étapes datées. La
collecte, elle, lit les archives open data des dossiers.

Le périmètre, validé par la propriétaire le 02/11/2026 : **le stade et les
dates, pas le rôle de la personne**. La page du dossier ne nomme aucun député ;
le rôle demanderait une seconde page par texte.

Le tirage
---------
Dix dossiers par run : sept dont la dernière date publiée tombe dans les trente
derniers jours, trois sur tout le corpus — le partage des lots 1 et 3. La
graine est le numéro du run.

Les quatre règles, et pourquoi elles sont des inégalités
--------------------------------------------------------
`date_min` n'est **pas** la date de dépôt : c'est la plus ancienne date de tous
les actes du dossier (`candidate_profile._collect_acteur_roles`), et un
rapporteur est parfois nommé avant le dépôt — le budget de la Sécurité sociale
2026 a un `date_min` au 02/07/2025 pour un dépôt au 14/10/2025. Et la page ne
date que le **début** de chaque étape, pas ses actes. D'où :

| Règle | Écart quand |
| --- | --- |
| dépôt | `date_min` est postérieure à la date de dépôt de la page |
| fraîcheur | une étape de la page commence après notre `date_max`, **et avant la date à laquelle nos dossiers sont à jour** (`an.dossiers` dans `pivot_data/fraicheur_sources.json`, #1389) : les archives de dossiers ne sont renouvelées qu'une fois par semaine, et une étape plus récente qu'elles est une étape pas encore relue, pas une erreur — la deuxième lecture du projet de loi constitutionnelle sur la Corse, commencée le 28/10/2026 pour des dossiers à jour au 26/10, l'a montré au premier essai |
| promulgation | la page a une promulgation et notre stade n'est pas `promulgue`, ou l'inverse |
| adoption définitive | la page dit « adopté définitivement » et notre `sort` n'est pas une adoption — un `sort` non résolu compris (147 des 10 882 dossiers publiés portent `fam_code_inconnu`, mesuré le 02/11/2026) |

Mesurées le 02/11/2026 sur 40 dossiers tirés au hasard : 40 concordants sur les
quatre règles. La règle « `date_min` égale au dépôt » en aurait signalé un à
tort, le budget de la Sécurité sociale ci-dessus.

Une page injoignable, ou dont ni le dépôt ni aucune étape ne se lit, rend le
dossier « non vérifié » — jamais un écart (§2 règle 5). Rien ne bloque.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html as html_lib
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

DELAI_ENTRE_PAGES = 1.0
TIMEOUT = 30
ENTETES = {"User-Agent": "Empreinte-politique (relecture des textes portés, #1248)"}

STADE_PROMULGUE = "promulgue"
#: Les `sort` qui disent une adoption.
SORTS_ADOPTES = frozenset({"adopte", "adopte_cmp", "adopte_49_3", "promulgue"})

MOIS = {
    nom: rang
    for rang, nom in enumerate(
        "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
        1,
    )
}
_DATE = re.compile(r"(\d{1,2})(?:er)? (\w+) (\d{4})")
_ETAPE = re.compile(
    r'data-id="([^"]*?) / Bloc de style \'21\'".*?<span class="_bold _colored-primary">(.*?)</span>'
    r'.*?(?:<span class="_colored-grey _small">(.*?)</span>|<button)',
    re.S,
)
_DEPOSE_LE = re.compile(r"déposée? le \w+ (\d{1,2})(?:er)? (\w+) (\d{4})")


class PageIllisible(ValueError):
    """La page a répondu, mais rien ne s'y lit sous la forme connue."""


def _iso(jour: str, mois: str, annee: str) -> str:
    rang = MOIS.get(mois.lower())
    if rang is None:
        raise PageIllisible(f"mois inconnu : {mois!r}")
    return f"{annee}-{rang:02d}-{int(jour):02d}"


def _texte(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html_lib.unescape(fragment or ""))).strip()


@dataclass
class Chronologie:
    depot: Optional[str]
    dates: list[str]
    promulgation: Optional[str]
    adopte_definitivement: bool


def lire_chronologie(html: str) -> Chronologie:
    """Les étapes datées de la page d'un dossier législatif."""
    depot, dates, promulgation, definitif = None, [], None, False
    for code, titre, date_brute in _ETAPE.findall(html):
        titre, libelle = _texte(titre), _texte(date_brute)
        trouve = _DATE.search(libelle)
        date = _iso(*trouve.groups()) if trouve else None
        if date:
            dates.append(date)
        if depot is None and titre.startswith("Dépôt") and date:
            depot = date
        if "-PROM-" in code and date:
            promulgation = date
        if "adopté définitivement" in libelle:
            definitif = True
    if depot is None:
        # Un texte seulement déposé n'a pas de chronologie : la page l'écrit
        # en une phrase (« déposée le jeudi 23 juillet 2026 »).
        trouve = _DEPOSE_LE.search(_texte(html))
        if trouve:
            depot = _iso(*trouve.groups())
            dates.append(depot)
    if depot is None and not dates:
        raise PageIllisible("ni date de dépôt ni étape lisible")
    return Chronologie(depot, dates, promulgation, definitif)


@dataclass
class Publication:
    """Un texte porté, tel qu'un profil le publie."""
    slug: str
    stade: Optional[str]
    sort: Optional[str]
    date_min: Optional[str]
    date_max: Optional[str]


@dataclass
class Dossier:
    dossier_id: str
    source_url: str
    date_max: Optional[str]
    publications: list[Publication] = field(default_factory=list)


def dossiers_publies(chemins: Iterable[Path]) -> list[Dossier]:
    """Les dossiers que les profils publient, avec chaque publication réduite à
    ce que ce contrôle compare (#628). Les textes européens n'ont pas de page de
    dossier de l'Assemblée : ils sont écartés par leur adresse."""
    dossiers: dict[str, Dossier] = {}
    for chemin in chemins:
        with open(chemin, encoding="utf-8") as f:
            profil = json.load(f)
        slug = profil.get("id") or chemin.stem
        for texte in profil.get("textes_portes") or []:
            if not isinstance(texte, dict):
                continue
            ident, url = texte.get("dossier_id"), texte.get("source_url") or ""
            if not ident or "assemblee-nationale.fr/dyn/" not in url or "/dossiers/" not in url:
                continue
            dossier = dossiers.setdefault(ident, Dossier(ident, url, texte.get("date_max")))
            dossier.date_max = max(filter(None, (dossier.date_max, texte.get("date_max"))), default=None)
            dossier.publications.append(Publication(
                slug, texte.get("stade_procedural"), texte.get("sort"),
                texte.get("date_min"), texte.get("date_max"),
            ))
    return sorted(dossiers.values(), key=lambda d: d.dossier_id)


def tirer(dossiers: list[Dossier], aujourd_hui: dt.date, graine: int,
          nb_recents: int = NB_RECENTS, nb_total: int = NB_TOTAL) -> list[Dossier]:
    borne = (aujourd_hui - dt.timedelta(days=FENETRE_JOURS)).isoformat()
    tirables = sorted(dossiers, key=lambda d: d.dossier_id)
    recents = [d for d in tirables if (d.date_max or "") >= borne]
    hasard = random.Random(graine)
    choisis = hasard.sample(recents, min(nb_recents, len(recents)))
    pris = {d.dossier_id for d in choisis}
    reste = [d for d in tirables if d.dossier_id not in pris]
    return choisis + hasard.sample(reste, min(nb_total - len(choisis), len(reste)))


def a_jour_au(fraicheur: Optional[Path]) -> Optional[str]:
    """La date à laquelle nos dossiers sont à jour, ou `None` sans fichier de
    fraîcheur — et alors aucune étape n'est excusée."""
    if fraicheur is None or not fraicheur.is_file():
        return None
    with open(fraicheur, encoding="utf-8") as f:
        document = json.load(f)
    familles = document.get("familles") or document
    return ((familles.get("an.dossiers") or {}).get("a_jour_au")) if isinstance(familles, dict) else None


def comparer(chronologie: Chronologie, publication: Publication,
             dossiers_a_jour_au: Optional[str] = None) -> list[dict[str, Any]]:
    """Les écarts d'une publication avec la page ; vide si elle concorde."""
    ecarts = []
    if chronologie.depot and publication.date_min and publication.date_min > chronologie.depot:
        ecarts.append({"regle": "dépôt", "page": chronologie.depot, "publie": publication.date_min})
    relues = [d for d in chronologie.dates if dossiers_a_jour_au is None or d <= dossiers_a_jour_au]
    derniere = max(relues) if relues else None
    if derniere and (publication.date_max or "") < derniere:
        ecarts.append({"regle": "fraîcheur", "page": derniere, "publie": publication.date_max})
    if bool(chronologie.promulgation) != (publication.stade == STADE_PROMULGUE):
        ecarts.append({"regle": "promulgation", "page": chronologie.promulgation or "aucune",
                       "publie": publication.stade})
    if chronologie.adopte_definitivement and publication.sort not in SORTS_ADOPTES:
        ecarts.append({"regle": "adoption définitive", "page": "adopté définitivement",
                       "publie": publication.sort})
    return ecarts


def telecharger(url: str) -> str:
    import requests  # noqa: PLC0415 — seul appel réseau du module

    reponse = requests.get(url, headers=ENTETES, timeout=TIMEOUT)
    reponse.raise_for_status()
    return reponse.text


@dataclass
class Resultat:
    dossier_id: str
    source_url: str
    non_verifie: Optional[str] = None
    publications: int = 0
    concordantes: int = 0
    etapes_pas_encore_relues: int = 0
    ecarts: list[dict[str, Any]] = field(default_factory=list)


def relire(tirage: list[Dossier], obtenir: Callable[[str], str] = telecharger,
           delai: float = DELAI_ENTRE_PAGES,
           dossiers_a_jour_au: Optional[str] = None) -> list[Resultat]:
    resultats = []
    for rang, dossier in enumerate(tirage):
        if rang and delai:
            time.sleep(delai)
        res = Resultat(dossier.dossier_id, dossier.source_url)
        try:
            chronologie = lire_chronologie(obtenir(dossier.source_url))
        except PageIllisible as exc:
            res.non_verifie = f"page illisible : {exc}"
        except Exception as exc:  # noqa: BLE001 — une source muette n'est pas un écart
            res.non_verifie = f"page injoignable : {type(exc).__name__}: {exc}"
        else:
            res.publications = len(dossier.publications)
            if dossiers_a_jour_au:
                res.etapes_pas_encore_relues = sum(d > dossiers_a_jour_au for d in chronologie.dates)
            for publication in dossier.publications:
                ecarts = comparer(chronologie, publication, dossiers_a_jour_au)
                if ecarts:
                    res.ecarts += [{"profil": publication.slug, **e} for e in ecarts]
                else:
                    res.concordantes += 1
        resultats.append(res)
    return resultats


def rapport(resultats: list[Resultat], graine: int) -> tuple[str, dict[str, Any]]:
    verifies = [r for r in resultats if r.non_verifie is None]
    nb_ecarts = sum(len(r.ecarts) for r in verifies)
    resume = {
        "graine": graine,
        "dossiers_tires": len(resultats),
        "dossiers_verifies": len(verifies),
        "dossiers_non_verifies": len(resultats) - len(verifies),
        "publications_relues": sum(r.publications for r in verifies),
        "publications_concordantes": sum(r.concordantes for r in verifies),
        "ecarts": nb_ecarts,
        "dossiers_avec_ecart": sum(1 for r in verifies if r.ecarts),
        "etapes_pas_encore_relues": sum(r.etapes_pas_encore_relues for r in verifies),
        "resultats": [r.__dict__ for r in resultats],
    }
    lignes = [
        f"Tirage de {len(resultats)} dossiers (graine {graine}) : "
        f"{len(verifies)} relus à la source, {resume['dossiers_non_verifies']} non vérifiés.",
        "",
        f"- Textes portés relus (un par profil qui publie le dossier) : {resume['publications_relues']}",
        f"- Concordants : **{resume['publications_concordantes']}**",
        f"- Écarts : **{nb_ecarts}**, sur {resume['dossiers_avec_ecart']} dossier(s)",
        f"- Étapes plus récentes que nos dossiers (pas encore relues, pas un écart) : "
        f"{resume['etapes_pas_encore_relues']}",
        "",
        "| Dossier | Profils | Concordants | Écarts | État |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for r in resultats:
        etat = r.non_verifie or ("écart" if r.ecarts else "concordant")
        lignes.append(f"| [{r.dossier_id}]({r.source_url}) | {r.publications} | {r.concordantes} | "
                      f"{len(r.ecarts)} | {etat} |")
    avec_ecart = [r for r in verifies if r.ecarts]
    if avec_ecart:
        lignes += ["", "### Écarts", "", "| Dossier | Profil | Règle | Page de l'Assemblée | Publié |",
                   "| --- | --- | --- | --- | --- |"]
        for r in avec_ecart:
            for e in r.ecarts:
                lignes.append(f"| {r.dossier_id} | {e['profil']} | {e['regle']} | {e['page']} | {e['publie'] or '—'} |")
    return "\n".join(lignes) + "\n", resume


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--profils-dir", type=Path, default=Path("pivot_data/profiles"))
    parseur.add_argument("--fraicheur", type=Path, default=Path("pivot_data/fraicheur_sources.json"))
    parseur.add_argument("--graine", type=int, required=True, help="le numéro du run, en CI")
    parseur.add_argument("--date", help="jour du tirage, AAAA-MM-JJ (défaut : aujourd'hui)")
    parseur.add_argument("--out", type=Path, required=True)
    parseur.add_argument("--out-json", type=Path, required=True)
    args = parseur.parse_args(argv)

    aujourd_hui = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    tirage = tirer(dossiers_publies(sorted(args.profils_dir.glob("*.pivot.json"))), aujourd_hui, args.graine)
    texte, resume = rapport(relire(tirage, dossiers_a_jour_au=a_jour_au(args.fraicheur)), args.graine)
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
