#!/usr/bin/env python3
"""scrutins_legislature.py — Résoudre la `legislature` d'un vote (#432).

`votes[].numero_scrutin` repart à 1 à chaque législature : il n'est jamais une
clé à lui seul (AGENTS.md §5). Toute normalisation des votes a donc besoin de
`(legislature, numero_scrutin)` — or **22,5 % des votes collectés ne portent
aucune législature** (89 687 sur 398 085, 83 profils, mesuré au 19/08/2026) :
ils viennent d'un chemin de collecte antérieur qui ne renseignait pas le champ.

Sans comblement, la clé compterait 21 520 scrutins « distincts » là où il n'y en
a que 17 422 — 23 % de sur-comptage, et 4 098 scrutins stockés deux fois dans la
liste dédupliquée que #432 introduit.

DEUX MÉCANISMES DISTINCTS, JAMAIS UN SEUL. Ils ne sont pas de même nature et
n'ont pas la même force, donc ils ne sont ni confondus ni tracés pareil :

1. **Jointure sur un jumeau étiqueté** (`PROVENANCE_JUMEAU`). Le même scrutin —
   même `(numero_scrutin, date)` — apparaît ailleurs dans le corpus AVEC sa
   législature. Ce n'est pas une inférence, c'est une **résolution** : la donnée
   existe déjà, étiquetée, dans un autre profil. Résout 4 098 des 4 104 paires,
   sans une seule ambiguïté (aucune paire ne porte deux législatures
   différentes).

2. **Calendrier des législatures** (`PROVENANCE_CALENDRIER`), pour ce que le
   premier ne couvre pas. Les 6 paires restantes sont datées du 25/11/2022 au
   16/12/2023 : en plein XVI, à plus de six mois de la dissolution de juin 2024,
   donc sans zone grise. C'est une **dérivation**, et elle est tracée comme
   telle — jamais présentée comme collectée.

3. **Tout le reste échoue bruyamment** (`LegislatureIrresoluble`). Une donnée
   absente reste absente : aucune valeur par défaut, aucun repli sur « la
   législature la plus probable » (AGENTS.md §2.5). Sont irrésolubles : une date
   hors de tout intervalle connu (l'entre-deux du 10/06 au 17/07/2024, par ex.),
   une date absente ou malformée, un jumeau contradictoire, et une législature
   collectée que le calendrier ne connaît pas — ce dernier cas signalant un
   calendrier à étendre, pas une donnée à corriger.

Le calendrier ci-dessous a été validé contre les 308 398 votes qui portent DÉJÀ
leur législature : **aucun** ne tombe hors de l'intervalle de la sienne.
"""

from datetime import datetime
from typing import Iterable, NamedTuple, Optional

# Bornes officielles des législatures de l'Assemblée nationale, incluses.
# `fin=None` = législature en cours.
#
# La XVI se termine à la dissolution du 09/06/2024, et la XVII ouvre le
# 18/07/2024 : les cinq semaines qui les séparent n'appartiennent à AUCUNE
# législature. Un vote qui y serait daté doit échouer, pas être rattaché au
# voisin le plus proche — c'est précisément le genre de trou qu'un repli
# silencieux comblerait en inventant une donnée.
#
# La XVII est délibérément ouverte (`None`) plutôt que bornée à une date
# lointaine : une borne factice se périmerait sans bruit le jour d'une
# dissolution, et rattacherait alors des votes de la XVIII à la XVII.
LEGISLATURES_AN: dict[str, tuple[str, Optional[str]]] = {
    "14": ("2012-06-20", "2017-06-20"),
    "15": ("2017-06-21", "2022-06-21"),
    "16": ("2022-06-22", "2024-06-09"),
    "17": ("2024-07-18", None),
}

# Provenance de la législature d'un scrutin. Nomenclature fermée : toute autre
# valeur est un bug d'appelant. Tracée sur l'enregistrement de scrutin (une
# fois), jamais sur chaque paire (membre, vote) — le même fait n'a pas à être
# répété 74 fois.
PROVENANCE_COLLECTEE = "collectee"
PROVENANCE_JUMEAU = "resolue_par_jumeau"
PROVENANCE_CALENDRIER = "derivee_du_calendrier"

PROVENANCES_CONNUES = frozenset({
    PROVENANCE_COLLECTEE, PROVENANCE_JUMEAU, PROVENANCE_CALENDRIER,
})

# Motifs d'échec, pour que le rapport dise *pourquoi* et pas seulement *que*.
MOTIF_DATE_ABSENTE = "date absente"
MOTIF_DATE_ILLISIBLE = "date illisible"
MOTIF_HORS_CALENDRIER = "date hors de toute législature connue"
MOTIF_JUMEAU_CONTRADICTOIRE = "jumeaux étiquetés de législatures différentes"
MOTIF_LEGISLATURE_INCONNUE = "législature collectée absente du calendrier"


class CleScrutin(NamedTuple):
    """Identité d'un scrutin indépendante de sa législature — c'est justement
    ce qu'on cherche à retrouver. `(numero_scrutin, date)` : 0 collision sur
    398 085 paires mesurées, et c'est déjà la clé de fusion de
    `merge_profile._vote_key`."""
    numero_scrutin: Optional[str]
    date: Optional[str]


class Resolution(NamedTuple):
    legislature: str
    provenance: str


class EchecResolution(NamedTuple):
    cle: CleScrutin
    motif: str
    detail: str = ""


class LegislatureIrresoluble(Exception):
    """Au moins un scrutin n'a pu être résolu par aucun des deux mécanismes.

    Porte la liste complète des échecs plutôt que le premier : un appelant qui
    corrige au coup par coup relancerait le corpus entier à chaque fois.
    """

    def __init__(self, echecs: list[EchecResolution]) -> None:
        self.echecs = echecs
        apercu = ", ".join(f"n°{e.cle.numero_scrutin} du {e.cle.date} ({e.motif})" for e in echecs[:3])
        suite = f" … et {len(echecs) - 3} autre(s)" if len(echecs) > 3 else ""
        super().__init__(
            f"{len(echecs)} scrutin(s) sans législature résoluble : {apercu}{suite}. "
            "Aucune valeur par défaut n'est posée (AGENTS.md §2.5) : corriger la collecte, "
            "ou étendre LEGISLATURES_AN si une nouvelle législature a commencé."
        )


def _date_valide(date: Optional[str]) -> bool:
    if not date:
        return False
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return False
    return True


def legislature_du_calendrier(date: Optional[str]) -> Optional[str]:
    """Législature dont l'intervalle contient `date`, `None` si aucune.

    Comparaison sur les chaînes ISO, valide parce que le format est vérifié
    d'abord : `"2024-06-10" > "2024-06-09"` lexicographiquement comme
    chronologiquement. Une date malformée renvoie `None` plutôt que de se faire
    comparer au petit bonheur.
    """
    if not _date_valide(date):
        return None
    for legislature, (debut, fin) in LEGISLATURES_AN.items():
        if date >= debut and (fin is None or date <= fin):
            return legislature
    return None


def resoudre_legislatures(
    occurrences: Iterable[tuple[Optional[str], Optional[str], Optional[str]]],
) -> tuple[dict[CleScrutin, Resolution], list[EchecResolution]]:
    """Résout la législature de chaque scrutin d'un corpus de votes.

    `occurrences` : `(numero_scrutin, date, legislature_ou_None)`, dans
    n'importe quel ordre et avec autant de répétitions que de votants. La
    résolution est **globale au corpus** et ne peut pas être faite profil par
    profil : le jumeau étiqueté d'un scrutin vit dans un AUTRE profil (un profil
    est soit entièrement sur l'ancien chemin de collecte, soit entièrement sur
    le nouveau — les deux formes ne coexistent jamais dans le même fichier).

    Renvoie `({clé: Resolution}, [échecs])`. Ne lève pas : c'est à l'appelant de
    décider quoi faire des échecs — les compter dans un rapport, ou lever
    `LegislatureIrresoluble`. Rien n'est résolu partiellement : une clé en échec
    est absente du dictionnaire, jamais présente avec une valeur approximative.
    """
    etiquetees: dict[CleScrutin, set[str]] = {}
    toutes: set[CleScrutin] = set()

    for numero, date, legislature in occurrences:
        cle = CleScrutin(numero, date)
        toutes.add(cle)
        if legislature:
            etiquetees.setdefault(cle, set()).add(str(legislature))

    resolutions: dict[CleScrutin, Resolution] = {}
    echecs: list[EchecResolution] = []

    for cle in sorted(toutes, key=lambda c: (c.date or "", c.numero_scrutin or "")):
        legislatures = etiquetees.get(cle) or set()

        # ── Mécanisme 1 : jointure sur un jumeau étiqueté ────────────────────
        if legislatures:
            if len(legislatures) > 1:
                echecs.append(EchecResolution(
                    cle, MOTIF_JUMEAU_CONTRADICTOIRE, f"législatures vues : {sorted(legislatures)}",
                ))
                continue
            legislature = next(iter(legislatures))
            if legislature not in LEGISLATURES_AN:
                # Ne pas laisser passer : soit la collecte a produit une valeur
                # aberrante, soit une législature a commencé et le calendrier
                # n'a pas suivi. Les deux demandent une décision humaine.
                echecs.append(EchecResolution(
                    cle, MOTIF_LEGISLATURE_INCONNUE, f"législature {legislature!r}",
                ))
                continue
            # `PROVENANCE_COLLECTEE` quand ce scrutin portait lui-même sa
            # législature ; `PROVENANCE_JUMEAU` est posée par l'appelant qui
            # sait, pour UNE occurrence donnée, si elle l'avait ou pas. Ici, au
            # niveau du scrutin, les deux se confondent : la valeur vient d'une
            # occurrence étiquetée, dans les deux cas.
            resolutions[cle] = Resolution(legislature, PROVENANCE_COLLECTEE)
            continue

        # ── Mécanisme 2 : calendrier ─────────────────────────────────────────
        if not cle.date:
            echecs.append(EchecResolution(cle, MOTIF_DATE_ABSENTE))
            continue
        if not _date_valide(cle.date):
            echecs.append(EchecResolution(cle, MOTIF_DATE_ILLISIBLE, f"date {cle.date!r}"))
            continue
        legislature = legislature_du_calendrier(cle.date)
        if legislature is None:
            # Typiquement l'entre-deux dissolution/ouverture : aucune
            # législature ne couvre la date. Rattacher au voisin le plus proche
            # inventerait une donnée.
            echecs.append(EchecResolution(cle, MOTIF_HORS_CALENDRIER, f"date {cle.date}"))
            continue
        resolutions[cle] = Resolution(legislature, PROVENANCE_CALENDRIER)

    return resolutions, echecs


def provenance_par_occurrence(
    legislature_collectee: Optional[str], resolution: Resolution,
) -> str:
    """Provenance du point de vue d'UNE occurrence de vote.

    Le scrutin porte une provenance unique (`resoudre_legislatures`), mais une
    même valeur peut être « collectée » pour le vote qui l'avait et « résolue
    par jumeau » pour celui qui ne l'avait pas. C'est cette distinction que le
    mécanisme 1 rend explicite : la donnée n'a pas été devinée, elle a été
    reprise d'une occurrence qui la portait.
    """
    if legislature_collectee:
        return PROVENANCE_COLLECTEE
    if resolution.provenance == PROVENANCE_COLLECTEE:
        return PROVENANCE_JUMEAU
    return resolution.provenance
