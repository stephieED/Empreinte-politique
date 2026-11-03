#!/usr/bin/env python3
"""Confronter nos effectifs de groupe à ceux que l'Assemblée publie à chaque scrutin (#1248, lot 5).

Pourquoi ce module existe
-------------------------
Les lots 1 à 4 relisent à la source un échantillon de ce que nous publions :
ils disent si ce que nous avons est **juste**. Celui-ci dit si nous l'avons
**en entier**, pour la composition de l'Assemblée. Chaque scrutin de l'archive
open data porte, groupe par groupe, le nombre de membres que l'Assemblée compte
ce jour-là (`ventilationVotes…groupe[].nombreMembresGroupe`), non-inscrits
compris. Nos fiches de groupe et `raw_data/non_inscrits.json` donnent, pour la
même date, les membres dont une période d'appartenance couvre le jour. Les deux
comptes viennent de deux jeux différents de l'Assemblée — les scrutins d'un
côté, le référentiel AMO30 des appartenances de l'autre.

Aucun tirage : tous les scrutins
--------------------------------
Le chiffre est dans l'archive, pas dans une page : le contrôle ne coûte pas une
requête par scrutin, et tous les scrutins sont relus à chaque run (7 s et
60 Mo pour les 9 578 de la XVIIe, mesuré le 03/11/2026). Un premier passage
complet, puis le contrôle des seuls scrutins nouveaux, a été écarté (arbitré le
03/11/2026) : nos fiches de groupe sont recomposées à chaque run, un correctif
ou une correction de l'Assemblée réécrit le passé, et le contrôle de perte ne
compare que des cardinalités, pas des dates.

Ce qui n'est pas signalé
------------------------
- **Le jour d'un changement.** Un écart sur un groupe dont un membre entre ou
  sort ce jour-là est toléré : l'heure du scrutin et celle du changement ne sont
  pas publiées, et nos périodes sont inclusives. 577 des 791 scrutins en écart
  de la XVIIe étaient dans ce cas, sur 20 jours (mesuré le 03/11/2026).
- **Un écart validé**, consigné à la main dans `config/ecarts_effectifs_valides.json`
  après examen. Il ne l'est que tant que les deux comptes restent ceux qui ont
  été validés : un compte qui bouge redevient un écart.
- **Les scrutins d'avant la constitution des groupes**, où tous les députés
  transitent par l'organe des non-inscrits et où `non_inscrits.json` ne dit pas
  qui l'était (#1265).

Une archive injoignable rend sa législature « non vérifiée », jamais un écart
(§2 règle 5). Rien ne bloque.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

LEGISLATURES: tuple[str, ...] = ("14", "15", "16", "17")
CLE_NON_INSCRITS = "NI"
TIMEOUT = 120
ENTETES = {"User-Agent": "Empreinte-politique (effectifs des groupes, #1248)"}


@dataclass
class Scrutin:
    numero: int
    date: str
    effectifs: dict[str, int]
    legislature: Optional[str] = None
    #: pourquoi la ventilation ne se compare pas, ou `None`
    hors_comparaison: Optional[str] = None


def _liste(valeur: Any) -> list:
    """Un élément seul est publié comme un objet, plusieurs comme une liste."""
    if valeur is None:
        return []
    return valeur if isinstance(valeur, list) else [valeur]


def _scrutin(brut: dict[str, Any]) -> Optional[Scrutin]:
    try:
        groupes = _liste(brut["ventilationVotes"]["organe"]["groupes"]["groupe"])
        scrutin = Scrutin(int(brut["numero"]), brut["dateScrutin"][:10],
                          {g["organeRef"]: int(g["nombreMembresGroupe"]) for g in groupes},
                          str(brut.get("legislature") or "") or None)
    except (KeyError, TypeError, ValueError):
        return None
    type_vote = ((brut.get("typeVote") or {}).get("libelleTypeVote") or "").lower()
    if "congrès" in type_vote:
        # Le Congrès vote avec les groupes du Sénat : l'archive de la XVIe en
        # range un (n° 1, 04/03/2024), qui ne dit rien de l'Assemblée seule.
        scrutin.hors_comparaison = "scrutin du Congrès"
    elif any(not str(g.get("organeRef") or "").startswith("PO") or g.get("organeRef") == "PO0" for g in groupes):
        # 13 scrutins de la XVIIe publient leurs groupes sous « PO0 » (mesuré
        # le 03/11/2026) : la source ne dit pas quel groupe compte combien.
        scrutin.hors_comparaison = "groupe non identifié par la source"
    return scrutin


def scrutins_de_l_archive(chemin: Path) -> Iterator[Scrutin]:
    """Les scrutins d'une archive, sous ses deux formes : un fichier par
    scrutin (XVe-XVIIe), ou un seul fichier pour toute la législature (XIVe)."""
    with zipfile.ZipFile(chemin) as archive:
        for nom in archive.namelist():
            if not nom.endswith(".json"):
                continue
            with archive.open(nom) as f:
                document = json.load(f)
            if "scrutin" in document:
                bruts = [document["scrutin"]]
            else:
                bruts = _liste((document.get("scrutins") or {}).get("scrutin"))
            for brut in bruts:
                scrutin = _scrutin(brut)
                if scrutin is not None:
                    yield scrutin


@dataclass
class Unite:
    """Un groupe (une fiche) ou les non-inscrits d'une législature."""
    cle: str
    organes: set[str]
    periodes: list[list[dict[str, Any]]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.bornes: set[str] = {
            j for periodes in self.periodes for p in periodes for j in (p.get("debut"), p.get("fin")) if j
        }

    def pres_d_un_changement(self, jour: str) -> bool:
        """Le jour d'un changement, la veille ou le lendemain. Un ministre
        quitte son groupe le 21/10/2024 et son suppléant y entre le 23 : le 22,
        l'Assemblée compte l'un ou l'autre, nous aucun des deux."""
        d = dt.date.fromisoformat(jour)
        return any((d + dt.timedelta(days=k)).isoformat() in self.bornes for k in (-1, 0, 1))

    def effectif(self, jour: str) -> int:
        return sum(
            1 for periodes in self.periodes
            if any((p.get("debut") or "9999") <= jour and (p.get("fin") is None or p["fin"] >= jour)
                   for p in periodes)
        )


def unites_de_la_legislature(legislature: str, groupes_dir: Path,
                             non_inscrits: dict[str, Any]) -> tuple[list[Unite], Optional[str]]:
    """Nos fiches de groupe de la législature, plus ses non-inscrits, et la date
    de constitution des groupes (avant elle, rien n'est comparable)."""
    unites = []
    for chemin in sorted(groupes_dir.glob(f"groupe-AN-*-{legislature}.json")):
        with open(chemin, encoding="utf-8") as f:
            fiche = json.load(f)
        organes = {h["organe_an"] for h in fiche.get("historique_noms") or [] if h.get("organe_an")}
        unites.append(Unite(fiche.get("groupe_id") or chemin.stem, organes,
                            [m.get("periodes") or [] for m in fiche.get("membres") or []]))
    constitution = None
    for entree in non_inscrits.get("legislatures") or []:
        if str(entree.get("legislature")) == legislature:
            constitution = entree.get("date_constitution_groupes")
            unites.append(Unite(CLE_NON_INSCRITS, {entree.get("organe_ref")} - {None},
                                [m.get("periodes") or [] for m in entree.get("membres") or []]))
    return unites, constitution


def comparer(scrutin: Scrutin, unites: list[Unite]) -> list[dict[str, Any]]:
    """Les écarts d'un scrutin, unité par unité ; vide s'il concorde. Un organe
    que l'Assemblée compte et qu'aucune de nos unités ne porte est un écart."""
    vers_unite = {organe: u.cle for u in unites for organe in u.organes}
    selon_l_an: dict[str, int] = defaultdict(int)
    ecarts = []
    for organe, nombre in scrutin.effectifs.items():
        cle = vers_unite.get(organe)
        if cle is None:
            ecarts.append({"unite": f"organe {organe}", "an": nombre, "nous": None, "jour_de_changement": False})
        else:
            selon_l_an[cle] += nombre
    for unite in unites:
        an, nous = selon_l_an.get(unite.cle, 0), unite.effectif(scrutin.date)
        if an != nous:
            ecarts.append({"unite": unite.cle, "an": an, "nous": nous,
                           "jour_de_changement": unite.pres_d_un_changement(scrutin.date),
                           # La ventilation omet parfois un groupe entier : le
                           # MoDem manque à 9 scrutins de la XVe (mesuré le 03/11/2026).
                           "absent_de_la_source": not (unite.organes & scrutin.effectifs.keys())})
    return ecarts


def charger_valides(chemin: Optional[Path]) -> set[tuple[str, str, str, int, Optional[int]]]:
    if chemin is None or not chemin.is_file():
        return set()
    with open(chemin, encoding="utf-8") as f:
        document = json.load(f)
    return {(str(e["legislature"]), e["date"], e["unite"], int(e["an"]), e.get("nous"))
            for e in document.get("ecarts") or []}


@dataclass
class Bilan:
    legislature: str
    non_verifie: Optional[str] = None
    scrutins: int = 0
    avant_constitution: int = 0
    hors_comparaison: dict[str, int] = field(default_factory=dict)
    groupe_absent_de_la_source: int = 0
    concordants: int = 0
    seulement_jours_de_changement: int = 0
    seulement_valides: int = 0
    en_ecart: int = 0
    #: (jour, unité, AN, nous) -> numéros des scrutins
    ecarts: dict[tuple[str, str, int, Optional[int]], list[int]] = field(default_factory=dict)


def controler(legislature: str, scrutins: Iterable[Scrutin], unites: list[Unite],
              constitution: Optional[str], valides: set) -> Bilan:
    bilan = Bilan(legislature)
    for scrutin in scrutins:
        if scrutin.legislature and scrutin.legislature != legislature:
            continue
        bilan.scrutins += 1
        if constitution and scrutin.date < constitution:
            bilan.avant_constitution += 1
            continue
        if scrutin.hors_comparaison:
            bilan.hors_comparaison[scrutin.hors_comparaison] = bilan.hors_comparaison.get(scrutin.hors_comparaison, 0) + 1
            continue
        ecarts = comparer(scrutin, unites)
        if any(e.get("absent_de_la_source") for e in ecarts):
            bilan.groupe_absent_de_la_source += 1
            continue
        restants = [e for e in ecarts if not e["jour_de_changement"]]
        hors_valides = [e for e in restants
                        if (legislature, scrutin.date, e["unite"], e["an"], e["nous"]) not in valides]
        if not ecarts:
            bilan.concordants += 1
        elif not restants:
            bilan.seulement_jours_de_changement += 1
        elif not hors_valides:
            bilan.seulement_valides += 1
        else:
            bilan.en_ecart += 1
            for e in hors_valides:
                bilan.ecarts.setdefault((scrutin.date, e["unite"], e["an"], e["nous"]), []).append(scrutin.numero)
    return bilan


def rapport(bilans: list[Bilan]) -> tuple[str, dict[str, Any]]:
    verifies = [b for b in bilans if b.non_verifie is None]
    jours = sorted({(b.legislature, cle[0]) for b in verifies for cle in b.ecarts})
    resume = {
        "legislatures_verifiees": [b.legislature for b in verifies],
        "legislatures_non_verifiees": {b.legislature: b.non_verifie for b in bilans if b.non_verifie},
        "scrutins": sum(b.scrutins for b in verifies),
        "scrutins_en_ecart": sum(b.en_ecart for b in verifies),
        "jours_en_ecart": len(jours),
        "ecarts": [
            {"legislature": b.legislature, "date": cle[0], "unite": cle[1], "an": cle[2], "nous": cle[3],
             "scrutins": len(nums), "premier_scrutin": min(nums)}
            for b in verifies for cle, nums in sorted(b.ecarts.items())
        ],
        "par_legislature": [
            {k: v for k, v in b.__dict__.items() if k != "ecarts"} for b in bilans
        ],
    }
    lignes = [
        f"{resume['scrutins']} scrutins relus ({', '.join(b.legislature for b in verifies) or 'aucune législature'}) : "
        f"**{resume['scrutins_en_ecart']}** en écart, sur **{resume['jours_en_ecart']}** jour(s).",
        "",
        "| Législature | Scrutins | Concordants | Écart un jour de changement (toléré) | Écart validé | "
        "Avant la constitution des groupes | **En écart** |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for b in bilans:
        if b.non_verifie:
            lignes.append(f"| {b.legislature} | non vérifiée : {b.non_verifie} | | | | | |")
            continue
        lignes.append(f"| {b.legislature} | {b.scrutins} | {b.concordants} | {b.seulement_jours_de_changement} | "
                      f"{b.seulement_valides} | {b.avant_constitution} | **{b.en_ecart}** |")
    if resume["ecarts"]:
        lignes += ["", "### Écarts", "",
                   "Un écart validé après examen se consigne dans `config/ecarts_effectifs_valides.json` "
                   "(législature, date, unité, les deux comptes) et ne revient plus tant que les comptes ne bougent pas.",
                   "", "| Législature | Jour | Groupe | Assemblée | Nous | Scrutins | Premier |",
                   "| --- | --- | --- | ---: | ---: | ---: | ---: |"]
        for e in resume["ecarts"]:
            nous = "—" if e["nous"] is None else e["nous"]
            lignes.append(f"| {e['legislature']} | {e['date']} | {e['unite']} | {e['an']} | {nous} | "
                          f"{e['scrutins']} | {e['premier_scrutin']} |")
    return "\n".join(lignes) + "\n", resume


def telecharger(legislature: str, dossier: Path) -> Path:
    import requests  # noqa: PLC0415 — seul appel réseau du module

    from candidate_profile import _scrutins_zip_url  # noqa: PLC0415 — l'adresse a une seule source

    url = _scrutins_zip_url(legislature)
    if url is None:
        raise ValueError("pas d'archive de scrutins publiée")
    reponse = requests.get(url, headers=ENTETES, timeout=TIMEOUT)
    reponse.raise_for_status()
    chemin = dossier / f"scrutins-{legislature}.zip"
    chemin.write_bytes(reponse.content)
    return chemin


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--groupes-dir", type=Path, default=Path("pivot_data/groupes"))
    parseur.add_argument("--non-inscrits", type=Path, default=Path("raw_data/non_inscrits.json"))
    parseur.add_argument("--valides", type=Path, default=Path("config/ecarts_effectifs_valides.json"))
    parseur.add_argument("--archive", action="append", default=[], metavar="LEG=CHEMIN",
                         help="archive déjà téléchargée, au lieu du réseau (répétable)")
    parseur.add_argument("--legislature", action="append", choices=LEGISLATURES,
                         help="ne relire que cette législature (répétable ; défaut : toutes)")
    parseur.add_argument("--out", type=Path, required=True)
    parseur.add_argument("--out-json", type=Path, required=True)
    args = parseur.parse_args(argv)

    locales = dict(a.split("=", 1) for a in args.archive)
    non_inscrits = None
    if args.non_inscrits.is_file():
        with open(args.non_inscrits, encoding="utf-8") as f:
            non_inscrits = json.load(f)
    valides = charger_valides(args.valides)
    bilans = []
    with tempfile.TemporaryDirectory() as tmp:
        for legislature in args.legislature or LEGISLATURES:
            if non_inscrits is None:
                # Sans eux, l'organe des non-inscrits serait un écart à chaque scrutin.
                bilans.append(Bilan(legislature, non_verifie="liste des non-inscrits absente"))
                continue
            try:
                chemin = Path(locales[legislature]) if legislature in locales else telecharger(legislature, Path(tmp))
                scrutins = list(scrutins_de_l_archive(chemin))
            except Exception as exc:  # noqa: BLE001 — une source muette n'est pas un écart
                bilans.append(Bilan(legislature, non_verifie=f"{type(exc).__name__}: {exc}"))
                continue
            unites, constitution = unites_de_la_legislature(legislature, args.groupes_dir, non_inscrits)
            bilans.append(controler(legislature, scrutins, unites, constitution, valides))
    texte, resume = rapport(bilans)
    resume["releve_le"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
