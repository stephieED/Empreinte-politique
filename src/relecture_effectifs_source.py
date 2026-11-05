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

Deux comptes de l'Assemblée, et lequel juge notre collecte
---------------------------------------------------------
Le compte d'un scrutin n'est pas la vérité : c'est un instantané du système de
vote, qui contredit parfois le référentiel AMO30 lui-même — le 01/10/2014,
AMO30 compte 9 non-inscrits et le scrutin 11 ; Patrice Prat est compté
non-inscrit deux jours AVANT sa date AMO30, Alix Fruchon reste comptée à DR
deux jours APRÈS. Nos fiches de groupe et `non_inscrits.json` sont tirés
d'AMO30. D'où le critère, arrêté avec la propriétaire le 03/11/2026 :

| Nous contre AMO30 | Nous contre le scrutin | Ce que c'est |
| --- | --- | --- |
| égaux | égaux | concordant |
| égaux | différents | **désaccord interne à l'Assemblée** : relevé, jamais signalé |
| différents | — | **écart de notre collecte** : signalé |

Le référentiel est lu par `an_roster.charger_index_gp`, l'index que le roster
construit déjà. S'il ne se lit pas, le contrôle se replie sur le compte du
scrutin et sa tolérance de trois jours autour d'un changement.

Un député en mandat qui n'est enregistré ni dans un groupe ni chez les
non-inscrits n'est compté nulle part, et ce n'est pas un écart : AMO30 ne
l'enregistre pas davantage. C'est un troisième état, « sans groupe
enregistré » — 25 députés sur les quatre législatures, presque toujours le
seul jour de leur arrivée (mesuré le 03/11/2026). Il n'est pas déduit en
non-inscrit : ces jours-là sont un délai d'enregistrement, pas un choix.

Ce qui n'est pas signalé
------------------------
- **Les scrutins que la collecte n'a pas encore pu voir.** Plus récents que le
  dernier scrutin de notre index, et datés de moins de
  `DELAI_DE_COLLECTE_JOURS` jours : l'archive relue en fin de run peut être plus
  récente que celle de la collecte. Même règle que les lois « publiées après nos
  dossiers » de `relecture_lois_promulguees`. Au-delà du délai, l'absence est
  signalée.
- **Sans référentiel lu, les jours autour d'un changement.** Un écart sur un groupe dont un membre
  entre ou sort dans les trois jours, avant ou après, est toléré
  (`TOLERANCE_JOURS`). Le compte d'un scrutin suit le changement avec un
  décalage : Alix Fruchon passe de DR à LIOT le 31/10/2026 dans AMO30, et le
  scrutin du 02/11 la compte encore à DR. Les 13 jours restés en écart avec un
  jour de tolérance ont été examinés le 03/11/2026 : 8 étaient de ce type, à
  2 ou 3 jours. La page « fonctions » du député donne les dates d'AMO30 : c'est
  une convention de l'Assemblée, pas une erreur à corriger.
- **Un écart validé**, consigné à la main dans `config/ecarts_effectifs_valides.json`
  après examen. Il ne l'est que tant que les deux comptes restent ceux qui ont
  été validés : un compte qui bouge redevient un écart.
- **Les scrutins d'avant la constitution des groupes**, où tous les députés
  transitent par l'organe des non-inscrits et où `non_inscrits.json` ne dit pas
  qui l'était (#1265).

Les scrutins eux-mêmes
----------------------
La même archive sert un second contrôle, demandé le 03/11/2026 : ses numéros
de scrutin contre ceux de notre index (`pivot_data/scrutins.json`). Un numéro
de l'archive absent de l'index est un scrutin perdu ; l'inverse, un scrutin
publié que la source ne porte plus. Les numéros que l'archive elle-même saute
sont relevés à part : un trou de la source, pas de notre collecte — les n° 3781
et 3782 de la XVe manquent ainsi à l'archive comme à l'index. Mesuré le
03/11/2026 : 19 454 scrutins des deux côtés, aucun absent.

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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

LEGISLATURES: tuple[str, ...] = ("14", "15", "16", "17")
#: Les jours, de part et d'autre d'un changement d'appartenance, où un écart
#: est toléré. Un jour ne suffisait pas : 8 des 13 jours en écart restants
#: suivaient un changement daté 2 ou 3 jours plus tôt ou plus tard (03/11/2026).
TOLERANCE_JOURS = 3

#: Un scrutin plus récent que le dernier de notre index, et daté de moins de
#: tant de jours avant le contrôle, est « pas encore collecté », pas absent.
#: L'archive est retéléchargée en fin de run, la collecte a lu celle du début :
#: le run 41932814357 a démarré le 05/11/2026 à 00 h 19, l'Assemblée a publié
#: la sienne à 00 h 26, et 119 scrutins des 03 et 04/11 ont été signalés
#: absents. Au-delà de ce délai, l'absence est signalée : une collecte
#: arrêtée ne doit pas se cacher derrière cette règle.
DELAI_DE_COLLECTE_JOURS = 3
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
class ArchiveLue:
    """Ce que le contrôle a lu, pour qu'un écart se rapporte à une version.

    Le 05/11/2026, deux runs ont lu une archive de la XVIIe de 9 697 scrutins
    à la même adresse où la collecte, et une lecture locale, en trouvaient
    9 759 : 62 « absents de l'archive » que rien ne permettait d'expliquer
    (#1441). La date que l'Assemblée donne au fichier, sa taille et son
    nombre de fichiers disent ensuite quelle version a été servie."""
    octets: int
    fichiers: int
    #: l'en-tête `Last-Modified` de la réponse ; `None` pour une archive locale
    modifiee_le: Optional[str] = None
    source: str = "téléchargée"


def decrire_archive(chemin: Path, modifiee_le: Optional[str] = None,
                    source: str = "téléchargée") -> ArchiveLue:
    with zipfile.ZipFile(chemin) as archive:
        fichiers = sum(1 for nom in archive.namelist() if nom.endswith(".json"))
    return ArchiveLue(Path(chemin).stat().st_size, fichiers, modifiee_le, source)


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
        """À `TOLERANCE_JOURS` jours au plus d'un changement. Un ministre
        quitte son groupe le 21/10/2024 et son suppléant y entre le 23 : le 22,
        l'Assemblée compte l'un ou l'autre, nous aucun des deux."""
        d = dt.date.fromisoformat(jour)
        return any((d + dt.timedelta(days=k)).isoformat() in self.bornes
                   for k in range(-TOLERANCE_JOURS, TOLERANCE_JOURS + 1))

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


class ReferenceAmo30:
    """Les effectifs d'AMO30 à une date, organe par organe, depuis l'index que
    le roster construit (`an_roster.charger_index_gp`) : `{organeRef:
    [[acteurRef, début, fin], …]}`, non-inscrits compris."""

    def __init__(self, mandats: dict[str, list[list[Optional[str]]]]) -> None:
        self.mandats = mandats
        self._memo: dict[tuple[frozenset[str], str], int] = {}

    def effectif(self, organes: Iterable[str], jour: str) -> int:
        cle = (frozenset(organes), jour)
        if cle not in self._memo:
            self._memo[cle] = len({
                acteur for organe in cle[0] for acteur, debut, fin in self.mandats.get(organe) or []
                if (debut or "9999")[:10] <= jour and (fin is None or fin[:10] >= jour)
            })
        return self._memo[cle]


def comparer(scrutin: Scrutin, unites: list[Unite],
             reference: Optional[ReferenceAmo30] = None) -> list[dict[str, Any]]:
    """Les écarts d'un scrutin, unité par unité ; vide s'il concorde. Un organe
    que l'Assemblée compte et qu'aucune de nos unités ne porte est un écart.
    Avec le référentiel, chaque écart dit ce qu'AMO30 compte ce jour-là, et
    s'il est `interne` à l'Assemblée (nous comptons comme AMO30)."""
    vers_unite = {organe: u.cle for u in unites for organe in u.organes}
    selon_l_an: dict[str, int] = defaultdict(int)
    ecarts = []
    for organe, nombre in scrutin.effectifs.items():
        cle = vers_unite.get(organe)
        if cle is None:
            amo = reference.effectif({organe}, scrutin.date) if reference else None
            ecarts.append({"unite": f"organe {organe}", "an": nombre, "nous": None, "jour_de_changement": False,
                           "amo30": amo, "interne": False})
        else:
            selon_l_an[cle] += nombre
    for unite in unites:
        an, nous = selon_l_an.get(unite.cle, 0), unite.effectif(scrutin.date)
        if an != nous:
            amo = reference.effectif(unite.organes, scrutin.date) if reference else None
            ecarts.append({"unite": unite.cle, "an": an, "nous": nous,
                           "jour_de_changement": unite.pres_d_un_changement(scrutin.date),
                           "amo30": amo, "interne": amo is not None and amo == nous,
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
    #: nous comptons comme AMO30, et le scrutin autrement
    desaccords_internes: int = 0
    en_ecart: int = 0
    #: (jour, unité, AN, nous) -> numéros des scrutins
    ecarts: dict[tuple[str, str, int, Optional[int]], list[int]] = field(default_factory=dict)
    effectifs_non_verifies: Optional[str] = None
    #: la couverture de l'index ; `None` quand l'index n'a pas pu être lu
    scrutins_de_l_archive: Optional[int] = None
    absents_de_l_index: list[int] = field(default_factory=list)
    absents_de_l_archive: list[int] = field(default_factory=list)
    trous_de_l_archive: list[int] = field(default_factory=list)
    #: la date du dernier scrutin de notre index pour cette législature
    index_a_jour_au: Optional[str] = None
    #: absents de l'index, mais postérieurs à son dernier scrutin et récents
    pas_encore_collectes: list[int] = field(default_factory=list)
    #: l'archive lue (`ArchiveLue`, en dictionnaire pour le JSON)
    archive: Optional[dict[str, Any]] = None


def numeros_publies(chemin: Path) -> dict[str, set[int]]:
    """Les numéros de scrutin de notre index, par législature."""
    with open(chemin, encoding="utf-8") as f:
        document = json.load(f)
    numeros: dict[str, set[int]] = defaultdict(set)
    for scrutin in document.get("scrutins") or []:
        try:
            numeros[str(scrutin["legislature"])].add(int(scrutin["numero_scrutin"]))
        except (KeyError, TypeError, ValueError):
            continue
    return numeros


def dates_publiees(chemin: Path) -> dict[str, str]:
    """La date du dernier scrutin de notre index, par législature."""
    with open(chemin, encoding="utf-8") as f:
        document = json.load(f)
    dates: dict[str, str] = {}
    for scrutin in document.get("scrutins") or []:
        legislature, date = scrutin.get("legislature"), scrutin.get("date")
        if legislature and isinstance(date, str) and date > dates.get(str(legislature), ""):
            dates[str(legislature)] = date
    return dates


def couvrir(bilan: Bilan, scrutins: Iterable[Scrutin], publies: set[int],
            a_jour_au: Optional[str] = None, aujourd_hui: Optional[dt.date] = None) -> None:
    """Les numéros de l'archive contre ceux de l'index. Le Congrès a sa propre
    numérotation (son n° 1 du 04/03/2024 double le n° 1 de la XVIe) : il n'en
    fait pas partie.

    `a_jour_au` (le dernier scrutin de l'index) et `aujourd_hui` mettent à part
    les scrutins que la collecte n'a pas encore pu voir : postérieurs à
    `a_jour_au`, et datés de moins de `DELAI_DE_COLLECTE_JOURS` jours."""
    dates = {s.numero: s.date for s in scrutins
             if (s.legislature or bilan.legislature) == bilan.legislature
             and s.hors_comparaison != "scrutin du Congrès"}
    archive = set(dates)
    bilan.scrutins_de_l_archive = len(archive)
    bilan.index_a_jour_au = a_jour_au
    absents = sorted(archive - publies)
    if a_jour_au and aujourd_hui:
        borne = (aujourd_hui - dt.timedelta(days=DELAI_DE_COLLECTE_JOURS)).isoformat()
        bilan.pas_encore_collectes = [n for n in absents
                                      if dates[n] > a_jour_au and dates[n] >= borne]
        attendus = set(bilan.pas_encore_collectes)
        absents = [n for n in absents if n not in attendus]
    bilan.absents_de_l_index = absents
    bilan.absents_de_l_archive = sorted(publies - archive)
    bilan.trous_de_l_archive = sorted(set(range(1, max(archive, default=0) + 1)) - archive)


def controler(legislature: str, scrutins: Iterable[Scrutin], unites: list[Unite],
              constitution: Optional[str], valides: set,
              reference: Optional[ReferenceAmo30] = None) -> Bilan:
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
        ecarts = comparer(scrutin, unites, reference)
        if any(e.get("absent_de_la_source") for e in ecarts):
            bilan.groupe_absent_de_la_source += 1
            continue
        if ecarts and all(e["interne"] for e in ecarts):
            bilan.desaccords_internes += 1
            continue
        if reference is not None:
            # Ce qui reste diffère d'AMO30 : aucune tolérance, c'est notre lecture.
            restants = [e for e in ecarts if not e["interne"]]
        else:
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


def rapport(bilans: list[Bilan], reference_lue: Optional[str] = None) -> tuple[str, dict[str, Any]]:
    """`reference_lue` : `None` si AMO30 a été lu, sinon pourquoi il ne l'a pas été."""
    verifies = [b for b in bilans if b.non_verifie is None]
    jours = sorted({(b.legislature, cle[0]) for b in verifies for cle in b.ecarts})
    absents = sum(len(b.absents_de_l_index) + len(b.absents_de_l_archive) for b in verifies)
    resume = {
        #: ce que l'issue de suivi compte : les jours d'effectif en écart, plus
        #: les scrutins absents d'un côté ou de l'autre
        "a_signaler": len(jours) + absents,
        "scrutins_absents": absents,
        #: relevés, jamais signalés (`DELAI_DE_COLLECTE_JOURS`)
        "scrutins_pas_encore_collectes": sum(len(b.pas_encore_collectes) for b in verifies),
        "legislatures_verifiees": [b.legislature for b in verifies],
        "legislatures_non_verifiees": {b.legislature: b.non_verifie for b in bilans if b.non_verifie},
        "scrutins": sum(b.scrutins for b in verifies),
        "scrutins_en_ecart": sum(b.en_ecart for b in verifies),
        "reference_amo30": reference_lue is None,
        "reference_amo30_non_lue": reference_lue,
        "desaccords_internes": sum(b.desaccords_internes for b in verifies),
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
    couverts = [b for b in verifies if b.scrutins_de_l_archive is not None]
    referentiel = (
        "Écart de notre collecte = nos effectifs diffèrent de ceux du référentiel AMO30 ce jour-là. "
        "Quand nous comptons comme AMO30 et que le scrutin compte autrement, c'est un désaccord interne "
        "à l'Assemblée : relevé, pas signalé."
        if reference_lue is None else
        f"**Référentiel AMO30 non lu ({reference_lue})** : repli sur le compte du scrutin, avec "
        f"{TOLERANCE_JOURS} jours de tolérance autour d'un changement."
    )
    lignes = [
        referentiel,
        "",
        f"{resume['scrutins']} scrutins relus ({', '.join(b.legislature for b in verifies) or 'aucune législature'}) : "
        f"**{resume['scrutins_en_ecart']}** en écart, sur **{resume['jours_en_ecart']}** jour(s).",
        "",
        "| Législature | Scrutins | Concordants | Désaccord interne à l'Assemblée (nous = AMO30) | "
        "Écart près d'un changement (toléré sans AMO30) | Écart validé | Avant la constitution des groupes | "
        "**En écart** |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for b in bilans:
        if b.non_verifie or b.effectifs_non_verifies:
            lignes.append(f"| {b.legislature} | non vérifiée : {b.non_verifie or b.effectifs_non_verifies} | | | | | | |")
            continue
        lignes.append(f"| {b.legislature} | {b.scrutins} | {b.concordants} | {b.desaccords_internes} | "
                      f"{b.seulement_jours_de_changement} | {b.seulement_valides} | {b.avant_constitution} | "
                      f"**{b.en_ecart}** |")
    lignes += ["", "### Les scrutins de l'archive et ceux de notre index", "",
               f"**{absents}** scrutin(s) absent(s) d'un côté ou de l'autre.", "",
               f"Un scrutin plus récent que le dernier de notre index, et de moins de {DELAI_DE_COLLECTE_JOURS} "
               "jours, est « pas encore collecté » : l'archive relue ici peut être plus récente que celle "
               "que la collecte a lue. Relevé, pas signalé.", "",
               "| Législature | Archive | Archive lue | Notre index à jour au | Pas encore collectés | "
               "**Absents de notre index** | **Absents de l'archive** | "
               "Numéros que l'archive saute (la source) |",
               "| --- | ---: | --- | --- | ---: | ---: | ---: | --- |"]
    for b in bilans:
        if b.non_verifie or b.scrutins_de_l_archive is None:
            lignes.append(f"| {b.legislature} | non vérifiée : {b.non_verifie or 'index illisible'} | | | | | | |")
            continue
        trous = ", ".join(map(str, b.trous_de_l_archive[:20])) or "aucun"
        lignes.append(f"| {b.legislature} | {b.scrutins_de_l_archive} | {_archive_lue(b.archive)} | "
                      f"{b.index_a_jour_au or '—'} | "
                      f"{len(b.pas_encore_collectes)} | **{len(b.absents_de_l_index)}** | "
                      f"**{len(b.absents_de_l_archive)}** | {trous} |")
    for b in couverts:
        for libelle, numeros in (("absents de notre index", b.absents_de_l_index),
                                 ("absents de l'archive", b.absents_de_l_archive),
                                 ("pas encore collectés", b.pas_encore_collectes)):
            if numeros:
                lignes.append(f"\n{b.legislature}e, {libelle} : {', '.join(map(str, numeros[:50]))}"
                              + (" …" if len(numeros) > 50 else ""))
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


def _archive_lue(archive: Optional[dict[str, Any]]) -> str:
    if not archive:
        return "—"
    date = archive.get("modifiee_le") or archive.get("source") or "—"
    octets, fichiers = (f"{archive[k]:,}".replace(",", " ") for k in ("octets", "fichiers"))
    return f"{date} ; {octets} octets ; {fichiers} fichiers"


def telecharger(legislature: str, dossier: Path) -> tuple[Path, Optional[str]]:
    """L'archive, et la date que l'Assemblée lui donne (`Last-Modified`)."""
    import requests  # noqa: PLC0415 — seul appel réseau du module

    from candidate_profile import _scrutins_zip_url  # noqa: PLC0415 — l'adresse a une seule source

    url = _scrutins_zip_url(legislature)
    if url is None:
        raise ValueError("pas d'archive de scrutins publiée")
    reponse = requests.get(url, headers=ENTETES, timeout=TIMEOUT)
    reponse.raise_for_status()
    chemin = dossier / f"scrutins-{legislature}.zip"
    chemin.write_bytes(reponse.content)
    return chemin, reponse.headers.get("Last-Modified")


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--groupes-dir", type=Path, default=Path("pivot_data/groupes"))
    parseur.add_argument("--non-inscrits", type=Path, default=Path("raw_data/non_inscrits.json"))
    parseur.add_argument("--valides", type=Path, default=Path("config/ecarts_effectifs_valides.json"))
    parseur.add_argument("--index-scrutins", type=Path, default=Path("pivot_data/scrutins.json"))
    parseur.add_argument("--amo30", type=Path,
                         help="archive AMO30 déjà téléchargée (défaut : celle du cache partagé, téléchargée au besoin)")
    parseur.add_argument("--sans-amo30", action="store_true",
                         help="ne pas lire le référentiel : comparer au seul compte des scrutins")
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
    publies = numeros_publies(args.index_scrutins) if args.index_scrutins.is_file() else None
    a_jour_au = dates_publiees(args.index_scrutins) if publies is not None else {}
    aujourd_hui = dt.datetime.now(dt.timezone.utc).date()
    reference, reference_lue = None, "désactivé (--sans-amo30)"
    if not args.sans_amo30:
        try:
            import an_roster  # noqa: PLC0415 — tire le téléchargement d'AMO30 au besoin

            reference, reference_lue = ReferenceAmo30(an_roster.charger_index_gp(args.amo30)["mandats"]), None
        except Exception as exc:  # noqa: BLE001 — un référentiel muet n'est pas un écart
            reference_lue = f"{type(exc).__name__}: {exc}"
    bilans = []
    with tempfile.TemporaryDirectory() as tmp:
        for legislature in args.legislature or LEGISLATURES:
            try:
                if legislature in locales:
                    chemin, modifiee_le, source = Path(locales[legislature]), None, "locale"
                else:
                    (chemin, modifiee_le), source = telecharger(legislature, Path(tmp)), "téléchargée"
                scrutins = list(scrutins_de_l_archive(chemin))
                archive_lue = asdict(decrire_archive(chemin, modifiee_le, source))
            except Exception as exc:  # noqa: BLE001 — une source muette n'est pas un écart
                bilans.append(Bilan(legislature, non_verifie=f"{type(exc).__name__}: {exc}"))
                continue
            if non_inscrits is None:
                # Sans eux, l'organe des non-inscrits serait un écart à chaque scrutin.
                bilan = Bilan(legislature, effectifs_non_verifies="liste des non-inscrits absente")
            else:
                unites, constitution = unites_de_la_legislature(legislature, args.groupes_dir, non_inscrits)
                bilan = controler(legislature, scrutins, unites, constitution, valides, reference)
            bilan.archive = archive_lue
            if publies is not None:
                couvrir(bilan, scrutins, publies.get(legislature, set()),
                        a_jour_au.get(legislature), aujourd_hui)
            bilans.append(bilan)
    texte, resume = rapport(bilans, reference_lue)
    resume["releve_le"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    args.out.write_text(texte, encoding="utf-8")
    args.out_json.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(texte)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
