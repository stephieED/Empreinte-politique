#!/usr/bin/env python3
"""Relire à la source quelques mandats de député publiés (#1248, lot 2).

Pourquoi ce module existe
-------------------------
Le lot 1 (`relecture_votes_source.py`) relit les positions de vote. Celui-ci
relit les **mandats de député**, ce que dessine la frise d'une fiche : pour
chaque député tiré, les périodes publiées dans son profil sont confrontées à
la page « fonctions » de l'Assemblée (`/dyn/deputes/<PA>/fonctions`, et
`?archive=oui` pour les législatures passées). La collecte, elle, lit
l'archive AMO30. Deux routes ; si elles divergent, l'une a tort.

Son premier essai, le 02/11/2026 sur les 18 candidats déclarés qui ont été
députés, a trouvé que le corpus effaçait les passages au gouvernement et
datait les suppléants du jour de l'élection : corrigé par #1412 avant que ce
contrôle n'entre dans le run.

Le tirage, arbitré par la propriétaire le 02/11/2026
----------------------------------------------------
**Cinq députés par run : 1 candidat déclaré, 3 députés de la XVIIe
législature, 1 député des législatures précédentes** — c'est-à-dire qui n'a
pas siégé dans la XVIIe. Les trois groupes sont disjoints : le candidat tiré
ne l'est pas une seconde fois. La graine est le numéro du run.

La comparaison se fait période par période
------------------------------------------
Une période de la page, c'est une ligne « <n>e législature : Élu le … – Mandat
du … (cause) au … (cause) ». Sa date de début est celle de l'élection quand la
cause est une élection, celle de l'entrée en fonction sinon (reprise après le
gouvernement, suppléance) : la convention que #1412 a donnée au corpus. Les
deux côtés sont comparés comme deux ensembles de couples (début, fin).

| Cas | Verdict |
| --- | --- |
| même période des deux côtés | concordante |
| période de la page absente du profil | **écart** |
| période du profil absente de la page | **écart** |
| page injoignable, ou aucune période lue alors que le profil en publie | non vérifié — jamais un écart (§2 règle 5) |

Seules les législatures à partir de la XIIe sont comparées : l'archive AMO30
ne remonte pas avant le 19/06/2002, et les mandats plus anciens viennent d'une
autre source, citée à la main (`config/mandats_anterieurs.json`, #860).

Ce que ce contrôle ne fait pas
------------------------------
Il ne bloque rien : il signale, comme le lot 1. Les commissions, que la page
liste aussi, ne sont pas relues : elles se comptent par dizaines de courtes
périodes (des remplacements), et demandent leur propre règle.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import random
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

#: Le tirage arbitré le 02/11/2026.
NB_CANDIDATS = 1
NB_XVIIE = 3
NB_PRECEDENTES = 1

#: Premier jour de la XVIIe législature côté corpus : le premier tour du
#: 30/06/2024, où quelques députés ont été élus. Un mandat qui s'ouvre ce
#: jour-là ou après est un mandat de la XVIIe.
DEBUT_XVIIE = "2024-06-30"

#: Borne basse d'AMO30 (#640) : la XIIe législature.
LEGISLATURE_MIN = 12

PROVENANCE_CANDIDAT = "candidat_declare"
CHAMBRE_AN = "AN"

URL_FONCTIONS = "https://www.assemblee-nationale.fr/dyn/deputes/{acteur}/fonctions"
DELAI_ENTRE_PAGES = 1.0
TIMEOUT = 30
ENTETES = {"User-Agent": "Empreinte-politique (relecture des mandats publiés, #1248)"}

MOIS = {
    nom: rang
    for rang, nom in enumerate(
        "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(),
        1,
    )
}
_DATE = r"(\d{1,2})(?:er)? (\w+) (\d{4})"
_PERIODE = re.compile(r'<span data-id="PM\d+"[^>]*>(.*?)</span>', re.S)
_LIGNE = re.compile(r"(\d+)\s*e législature : (.*)")
_ELU = re.compile(r"(?:Élu|Élue|Réélu|Réélue)\w* le " + _DATE)
_DEBUT = re.compile(r"(?:Mandat du|Début de mandat le) " + _DATE + r" \(([^)]*)\)")
_FIN = re.compile(r"\) au " + _DATE)


class PageIllisible(ValueError):
    """La page a répondu, mais une période ne se lit pas sous la forme connue."""


def _iso(jour: str, mois: str, annee: str) -> str:
    rang = MOIS.get(mois.lower())
    if rang is None:
        raise PageIllisible(f"mois inconnu : {mois!r}")
    return f"{annee}-{rang:02d}-{int(jour):02d}"


def lire_periodes(pages: Iterable[str]) -> set[tuple[str, Optional[str]]]:
    """Les périodes de mandat de député que les pages nomment, à partir de la
    XIIe législature : un ensemble de couples (début, fin)."""
    periodes: set[tuple[str, Optional[str]]] = set()
    for page in pages:
        for brut in _PERIODE.findall(page):
            texte = re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", "", brut))).strip()
            ligne = _LIGNE.match(texte)
            if not ligne:
                continue  # présidence, commissions : pas des périodes de mandat
            legislature, reste = int(ligne.group(1)), ligne.group(2)
            if legislature < LEGISLATURE_MIN:
                continue
            elu, debut, fin = _ELU.search(reste), _DEBUT.search(reste), _FIN.search(reste)
            if debut is None:
                raise PageIllisible(f"période sans début lisible : {texte!r}")
            cause = debut.group(4).strip().lower()
            if cause.startswith("élection") and elu is not None:
                date_debut = _iso(*elu.groups())
            else:
                date_debut = _iso(*debut.groups()[:3])
            periodes.add((date_debut, _iso(*fin.groups()) if fin else None))
    return periodes


def periodes_publiees(profil: dict[str, Any]) -> set[tuple[str, Optional[str]]]:
    """Les périodes de mandat de député du profil, depuis la XIIe législature."""
    return {
        (m.get("debut"), m.get("fin"))
        for m in profil.get("mandats") or []
        if isinstance(m, dict)
        and m.get("categorie") == "mandat_electif"
        and m.get("chambre") == CHAMBRE_AN
        and (m.get("debut") or "") >= "2002-06-19"
    }


@dataclass
class Depute:
    slug: str
    acteur: str
    provenance: Optional[str]
    periodes: set[tuple[str, Optional[str]]]

    @property
    def siege_dans_la_xviie(self) -> bool:
        return any(
            (debut or "") >= DEBUT_XVIIE or fin is None or fin >= DEBUT_XVIIE
            for debut, fin in self.periodes
        )


def deputes_publies(chemins: Iterable[Path]) -> list[Depute]:
    """Les profils qui publient au moins un mandat de député. Un profil à la
    fois, réduit aussitôt (#628)."""
    deputes = []
    for chemin in chemins:
        with open(chemin, encoding="utf-8") as f:
            profil = json.load(f)
        acteur = (profil.get("identifiants") or {}).get("an")
        periodes = periodes_publiees(profil)
        if acteur and periodes:
            deputes.append(Depute(
                slug=profil.get("id") or chemin.stem,
                acteur=acteur,
                provenance=(profil.get("meta") or {}).get("provenance"),
                periodes=periodes,
            ))
    return sorted(deputes, key=lambda d: d.slug)


def tirer(deputes: list[Depute], graine: int) -> list[tuple[str, Depute]]:
    """Le tirage du run : (groupe, député), candidat d'abord."""
    hasard = random.Random(graine)
    deputes = sorted(deputes, key=lambda d: d.slug)  # le tirage ne dépend pas de l'ordre lu
    tirage: list[tuple[str, Depute]] = []
    pris: set[str] = set()

    def prendre(groupe: str, population: list[Depute], nombre: int) -> None:
        restants = [d for d in population if d.slug not in pris]
        for depute in hasard.sample(restants, min(nombre, len(restants))):
            tirage.append((groupe, depute))
            pris.add(depute.slug)

    prendre("candidat déclaré", [d for d in deputes if d.provenance == PROVENANCE_CANDIDAT], NB_CANDIDATS)
    prendre("XVIIe législature", [d for d in deputes if d.siege_dans_la_xviie], NB_XVIIE)
    prendre("législatures précédentes", [d for d in deputes if not d.siege_dans_la_xviie], NB_PRECEDENTES)
    return tirage


@dataclass
class Resultat:
    groupe: str
    slug: str
    acteur: str
    non_verifie: Optional[str] = None
    concordantes: int = 0
    ecarts: list[dict[str, Any]] = field(default_factory=list)


def comparer(page: set, publiees: set) -> tuple[int, list[dict[str, Any]]]:
    ecarts = [{"page": [d, f], "publie": None} for d, f in sorted(page - publiees, key=str)]
    ecarts += [{"page": None, "publie": [d, f]} for d, f in sorted(publiees - page, key=str)]
    return len(page & publiees), ecarts


def telecharger(url: str) -> Optional[str]:
    """La page, ou `None` si l'Assemblée répond qu'elle n'existe pas (la page
    du mandat en cours d'un ancien député)."""
    import requests  # noqa: PLC0415 — seul appel réseau du module

    reponse = requests.get(url, headers=ENTETES, timeout=TIMEOUT)
    if reponse.status_code == 404:
        return None
    reponse.raise_for_status()
    return reponse.text


def relire(
    tirage: list[tuple[str, Depute]],
    obtenir: Callable[[str], Optional[str]] = telecharger,
    delai: float = DELAI_ENTRE_PAGES,
) -> list[Resultat]:
    resultats = []
    for rang, (groupe, depute) in enumerate(tirage):
        res = Resultat(groupe=groupe, slug=depute.slug, acteur=depute.acteur)
        url = URL_FONCTIONS.format(acteur=depute.acteur)
        try:
            pages = []
            for adresse in (url, url + "?archive=oui"):
                if rang or pages:
                    time.sleep(delai)
                pages.append(obtenir(adresse) or "")
            page = lire_periodes(pages)
        except PageIllisible as exc:
            res.non_verifie = f"page illisible : {exc}"
        except Exception as exc:  # noqa: BLE001 — une source muette n'est pas un écart
            res.non_verifie = f"page injoignable : {type(exc).__name__}: {exc}"
        else:
            if not page:
                res.non_verifie = "page illisible : aucune période de mandat lue"
            else:
                res.concordantes, res.ecarts = comparer(page, depute.periodes)
        resultats.append(res)
    return resultats


def _periode(couple: Optional[list]) -> str:
    if not couple:
        return "—"
    debut, fin = couple
    return f"{debut} → {fin or 'en cours'}"


def rapport(resultats: list[Resultat], graine: int) -> tuple[str, dict[str, Any]]:
    verifies = [r for r in resultats if r.non_verifie is None]
    nb_ecarts = sum(len(r.ecarts) for r in verifies)
    resume = {
        "graine": graine,
        "deputes_tires": len(resultats),
        "deputes_verifies": len(verifies),
        "deputes_non_verifies": len(resultats) - len(verifies),
        "periodes_concordantes": sum(r.concordantes for r in verifies),
        "periodes_en_ecart": nb_ecarts,
        "deputes_avec_ecart": sum(1 for r in verifies if r.ecarts),
        "resultats": [r.__dict__ for r in resultats],
    }
    lignes = [
        f"Tirage de {len(resultats)} députés (graine {graine}) : "
        f"{len(verifies)} relus à la source, {resume['deputes_non_verifies']} non vérifiés.",
        "",
        f"- Périodes de mandat concordantes : **{resume['periodes_concordantes']}**",
        f"- Périodes en écart : **{nb_ecarts}**, chez {resume['deputes_avec_ecart']} député(s)",
        "",
        "| Député | Tirage | Concordantes | Écarts | État |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for r in resultats:
        etat = r.non_verifie or ("écart" if r.ecarts else "concordant")
        lignes.append(
            f"| [{r.slug}]({URL_FONCTIONS.format(acteur=r.acteur)}?archive=oui) | {r.groupe} | "
            f"{r.concordantes} | {len(r.ecarts)} | {etat} |"
        )
    avec_ecart = [r for r in verifies if r.ecarts]
    if avec_ecart:
        lignes += ["", "### Écarts", "", "| Député | Page de l'Assemblée | Publié |", "| --- | --- | --- |"]
        for r in avec_ecart:
            for e in r.ecarts:
                lignes.append(f"| {r.slug} | {_periode(e['page'])} | {_periode(e['publie'])} |")
    return "\n".join(lignes) + "\n", resume


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--profils-dir", type=Path, default=Path("pivot_data/profiles"))
    parseur.add_argument("--graine", type=int, required=True, help="le numéro du run, en CI")
    parseur.add_argument("--out", type=Path, required=True)
    parseur.add_argument("--out-json", type=Path, required=True)
    args = parseur.parse_args(argv)

    tirage = tirer(deputes_publies(sorted(args.profils_dir.glob("*.pivot.json"))), args.graine)
    texte, resume = rapport(relire(tirage), args.graine)
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
