#!/usr/bin/env python3
"""
audit_collecte_vs_publie.py — Rapproche, **liste par liste**, ce que la collecte
a rendu de ce que la publication porte (#545).

**Quatrième angle**, et c'est pourquoi c'est un contrôle à part et non une
option de l'un des trois autres :

  - `audit_diff_profils` (#460/#470) surveille les **pertes** entre une
    référence git et le disque. Une publication qui *augmente* n'est pas une
    perte : les deux compteurs montent, et il ne bloque pas ;
  - `audit_collecte_non_publiee` (#511) vérifie qu'un profil collecté a un
    pivot. Il raisonne sur des **profils**, jamais sur le contenu de leurs
    listes : un pivot présent mais vidé de ses interventions lui est
    irréprochable ;
  - `audit_integrite_referentielle` (#485) vérifie qu'une clé résout dans son
    index partagé. Il ne **compte** rien : 891 clés qui résolvent toutes valent
    pour lui autant que 16 242.

Aucun des trois n'est en défaut. C'est l'espace **entre** eux qui n'était pas
couvert, et c'est cet espace qui a laissé passer #540.

## L'incident

#540 : la clé de fusion pivot des interventions prenait l'URL d'archive Syceron
pour un identifiant, ce qui écrasait toutes les interventions d'un même débat
sur une seule entrée. **7 767 interventions collectées, 891 publiées.** Le run
`33100214165` (27/08/2026) a conclu vert, les trois garde-fous ont passé, le
commit est parti. Le défaut n'a été vu qu'à la relecture manuelle.

## Le piège de conception, et ce que ce contrôle encode

Un contrôle naïf « le pivot doit porter autant d'entrées que le brut »
**crierait à tort sur deux champs sur cinq**. Mesuré sur les 476 profils du
corpus régénéré (`3104e37`, run `33110395663` du 27/08/2026) :

| Liste publiée | Ce que le pivot doit égaler | Mesuré |
| --- | --- | ---: |
| `votes` | `votes` du brut | 1 312 828 = 1 312 828 |
| `amendements` | `amendements` du brut | 3 074 378 = 3 074 378 |
| `interventions` | `interventions` du brut | 16 242 = 16 242 |
| `textes_portes` | **`dossiers_legislatifs`** du brut | 472 = 472 |
| `mandats` | `mandats` **+** `mandat_europeen.mandats_europeens` | 40 432 = 40 154 + 278 |

Comparer les champs de **même nom** rendrait −472 sur `dossiers_legislatifs` et
+472 sur `textes_portes` — deux faux positifs pour un simple renommage
(`normalize_profil.py:447`). Et `mandats` porterait un +278 inexpliqué, qui est
en réalité l'apport des mandats européens que `generate_all_profiles.py:779` et
`:989` versent dans `mandats[]` du pivot alors que le brut les range sous
`mandat_europeen.mandats_europeens`.

D'où la table `RELATIONS` ci-dessous : chaque liste publiée déclare **les
chemins du brut dont elle est la somme**. Un renommage s'écrit en donnant un
chemin de nom différent ; un enrichissement s'écrit en déclarant sa **source**,
pas une marge. C'est ce qui permet de garder le seuil à **0** partout, sans
tolérance arbitraire : l'apport européen n'est pas « du bruit toléré », c'est
une deuxième liste collectée, nommée, et comptée.

Écrire ces relations, c'est écrire ce que la normalisation a le droit de faire.

## La réduction nommée, troisième chose qu'une relation sait écrire (#888)

Une somme de longueurs suppose que **chaque entrée collectée est une entrée
distincte**. Le portail européen la dément : depuis #879 la normalisation sait
que la même appartenance y arrive **en paire** — l'une classée, l'autre non — et
`normalize_europarl.dedupliquer_appartenances` la réduit à une. Le brut garde
les deux, parce que le brut dit ce que la source a rendu ; le pivot en publie
une, parce que c'est **un** fait.

Face à ça, une somme de longueurs crie un déficit qui n'existe pas : le run
`34712936188` a bloqué sur **29 profils, 45 entrées**, toutes sur `mandats`,
tous les profils nommés portant un mandat européen. Rien n'était perdu — 45
entrées avaient été reconnues comme les doublons de 45 autres.

Une relation peut donc déclarer, à côté de ses sources, une **réduction
nommée** : la fonction que la normalisation applique, rejouée sur le brut par ce
contrôle. Ce n'est ni une marge ni une tolérance — c'est la même fonction, au
même endroit de la chaîne, appelée par son nom. Le seuil reste **0**, et le jour
où cette fonction cesse de réduire quoi que ce soit, la soustraction vaut 0
d'elle-même.

**Elle est rejouée, jamais recalculée.** Un contrôle qui réimplémenterait le
critère de #879 de son côté dériverait du jour où ce critère bouge — c'est le
mode de défaillance que `merge_profile._repli_texte_key` décrit pour les clés de
repli. `allow_declared_losses` était l'autre geste possible, et c'est le mauvais :
`nettoyage-sediment-839` §5 interdit de déclarer un écart plutôt que de
l'expliquer.

## Ce qui bloque, et ce qui est seulement rapporté

**Bloque — le déficit** : une liste publiée qui porte **moins** d'entrées que
la somme de ses sources collectées. C'est exactement #540, et c'est la seule
forme de « collecté puis jamais publié » qu'un compteur peut établir.

**Rapporté sans bloquer — l'excédent** : une liste publiée qui en porte
**plus**. L'arbitrage est explicite, et c'est le même que celui d'`audit_diff_profils`
sur les changements de valeur — *faux négatif assumé, faux positif refusé* :

  - la fusion pivot est **additive** (`merge_profile.merge_pivot_profile`) : un
    pivot conserve les entrées d'un run précédent que la collecte du jour n'a
    pas rendues. Le brut baisse, le pivot non, et c'est le comportement voulu
    (AGENTS.md §3) ;
  - `purge_mandats_dupliques.py --apply` retire des entrées du **brut seul** ;
  - un excédent ne perd rien : la donnée publiée est toujours là. La perte, si
    elle existe, est du côté du brut — et c'est le contrôle de perte qui
    regarde les variations dans le temps.

Mesuré : **0 excédent** sur les 476 profils × 5 relations du corpus actuel.
La catégorie est donc vide aujourd'hui ; elle existe pour rester un compteur de
dérive, jamais un verdict — même raisonnement que « publiés sans brut » de #511
et que les entrées d'index jamais référencées de #485.

**Rapporté sans bloquer — une liste collectée sans relation déclarée** : un
champ liste du profil brut qui ne figure dans aucune entrée de `RELATIONS`.
C'est le cas de la **prochaine source branchée** : elle ne doit pas rester
muette, mais elle ne doit pas non plus annuler un commit au seul motif que
personne n'a encore écrit sa relation. Nommée en annotation `warning`, jamais
bloquante. Mesuré : 0 sur le corpus actuel — les cinq listes du brut sont
toutes couvertes.

## Seuil 0, mesuré et non arrondi

Population : les 476 profils de `3104e37`, produits par le run `33110395663`
du 27/08/2026 — le premier run complet postérieur au correctif de #540.
Relevé profil par profil, pas en agrégat : **0 déficit et 0 excédent sur les
2 380 couples (profil, relation)**. Ce n'est pas une valeur basse, c'est une
invariance, et elle tient sur les cinq relations à la fois.

L'état d'**avant** le correctif (`deb28a7`, mêmes 476 profils, rejoué en
lecture seule hors de l'arbre de travail) donne 7 767 collectées pour 891
publiées : le contrôle y sort en erreur, annonce 6 876 entrées collectées et
publiées nulle part, et nomme les **cinq** profils en déficit — `gabriel-attal`
(3 351 → 17), `marine-le-pen` (2 247 → 384), `jerome-guedj` (1 083 → 396),
`laurent-wauquiez` (535 → 23), `bruno-retailleau` (486 → 6). Les deux autres
porteurs d'interventions de cet état, `jean-luc-melenchon` (15) et
`edouard-philippe` (50), avaient un pivot égal à leur brut : ils ne sont pas
nommés, et c'est correct. Les quatre autres relations y sont vertes, sur les
mêmes 476 profils — la même invariance tient donc sur **deux** états du corpus.
Les chiffres des deux états sont dans
`docs/decisions/collecte-vs-publie-545.md`.

## Dimensionnement

Ce script tourne AVANT le commit : s'il meurt, rien n'est publié (#460). Il
doit donc lire les 4,3 Go de `raw_data/profiles` — 476 fichiers, le plus lourd
à 28,6 Mo — sans jamais matérialiser un profil.

`json.load(..., object_pairs_hook=...)` avec un crochet qui **ne retient que
les clés de la table** : chaque objet imbriqué est remplacé par `None` dès sa
lecture, si bien que le décodeur ne construit ni les 36 154 amendements d'un
profil ni leurs cosignataires. Mesuré sur `veronique-louwagie.json` (28,6 Mo,
le plus lourd du corpus), `/usr/bin/time`, médiane de trois exécutions : un
`json.load` ordinaire coûte **186,3 Mio** et 0,62 s, le même avec ce crochet
**96,0 Mio** et 0,38 s.

Sur le corpus entier — 476 profils bruts (4,3 Go) et 476 pivots (360 Mo) :
**58,7 s / 158,2 Mio** (deux exécutions, 58,7 s et 61,1 s, RSS identique à 3 ko
près). Sous les 236 Mio actés par #460, et processus séparé des trois autres
contrôles, donc le pic du job reste celui du plus coûteux.

Usage :
    python3 src/audit_collecte_vs_publie.py
    python3 src/audit_collecte_vs_publie.py --raw-dir raw_data/profiles \\
        --pivot-dir pivot_data/profiles --out audit/collecte-vs-publie.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

import gha
# #888 — la réduction que ce contrôle rejoue sur le brut est **importée**, pas
# réécrite : rejouer la fonction de la normalisation est ce qui garantit que les
# deux étages disent la même chose d'un doublon de source le jour où le critère
# de #879 bouge.
from normalize_europarl import dedupliquer_appartenances
from profil_brut import (
    CLE_ACTEUR_TRANCHE,
    CLE_MANIFESTE,
    CLE_PARTITIONNEE,
    CLE_TRANCHE_DERIVEE,
)
# Les deux populations de `pivot_data/profiles/` (#630) : « 476 profils
# rapprochés » ne dit pas si le déficit porte sur les 13 fiches publiées ou sur
# les 468 membres de roster, et ce n'est pas la même suite. La ventilation est
# relue sur le répertoire pivot — `compter_listes` réduit chaque objet à ses
# clés surveillées et ne rend donc jamais la chaîne `meta.provenance`, et
# élargir ce crochet pour une chaîne toucherait la borne mémoire qu'il tient.
from population_profils import (
    CANDIDAT_DECLARE,
    Ventilation,
    lire_provenances,
    ventiler_provenances,
)

#: Suffixes des deux couches. Mêmes conventions que `audit_collecte_non_publiee` :
#: le suffixe pivot contient le suffixe brut, donc le dépouillement se fait par
#: découpe du suffixe attendu et jamais par `Path.stem`.
SUFFIXE_BRUT = ".json"
SUFFIXE_PIVOT = ".pivot.json"


@dataclass(frozen=True)
class Relation:
    """Ce qu'une liste **publiée** doit égaler dans les profils **bruts**.

    `sources` porte des chemins dans le profil brut (un tuple de segments, pour
    les champs imbriqués). Le nombre attendu est la **somme** de leurs
    longueurs. Trois cas, un seul mécanisme :

      - **égalité** — un chemin, de même nom que le champ pivot (`votes`) ;
      - **renommage** — un chemin, de nom différent (`dossiers_legislatifs`
        → `textes_portes`) ;
      - **enrichissement attribué** — plusieurs chemins (`mandats` +
        `mandat_europeen.mandats_europeens`). L'apport n'est pas une marge de
        tolérance : c'est une seconde liste collectée, nommée et comptée.

    Il n'y a volontairement **pas** de quatrième cas « enrichissement borné ».
    Une marge non attribuée serait un trou de la taille de la marge — et c'est
    dans un trou de cette nature que #540 a vécu.

    ## Ce que #683 ajoute, et pourquoi ça ne fait pas un quatrième cas

    Depuis #683, quatre listes du pivot portent aussi du matériau du **Parlement
    européen**, versé par `normalize_parltrack_dumps` depuis les dumps
    ParlTrack. Ce matériau n'a **aucune** contrepartie dans `raw_data/` : il ne
    transite pas par un profil brut, il vient de `.cache/parltrack`.

    Les 7 candidats déclarés à identifiant européen sortent donc en **excédent**
    sur `votes`, `amendements`, `interventions` et `textes_portes`. C'est
    attendu, et ce n'est pas de la dérive de fusion.

    Ce n'est pas non plus un quatrième cas de cette table : `sources` porte des
    chemins **dans le profil brut**, et il n'y en a pas à porter. L'attribution
    exacte — soustraire les entrées marquées `institution: "parlement_europeen"`
    — demanderait d'examiner chaque entrée, alors que `compter_listes` compte en
    flux, sans jamais matérialiser un document. Le rapport nomme donc la cause
    au lieu de la déduire, et le **déficit** — le seul verdict bloquant — reste
    inchangé.
    """

    #: Nom du champ dans `pivot_data/profiles/<slug>.pivot.json`.
    champ_pivot: str
    #: Chemins du profil brut dont la somme des longueurs est le compte attendu.
    sources: tuple[tuple[str, ...], ...]
    #: Pourquoi cette relation, en une phrase. Reprise telle quelle dans le
    #: rapport : un garde-fou qui bloque doit dire de quoi il tient sa règle.
    justification: str = ""
    #: Ce que la normalisation retire au brut avant de publier, quand elle le
    #: fait par une fonction nommée. `None` — le cas de quatre relations sur
    #: cinq — dit « rien n'est retiré », pas « on ne sait pas ».
    reduction: Optional["Reduction"] = None

    @property
    def libelle_sources(self) -> str:
        libelle = " + ".join(".".join(chemin) for chemin in self.sources)
        if self.reduction is not None:
            libelle += f" − {self.reduction.libelle}"
        return libelle

    @property
    def est_renommage(self) -> bool:
        return len(self.sources) == 1 and self.sources[0][-1] != self.champ_pivot

    @property
    def est_enrichissement(self) -> bool:
        return len(self.sources) > 1


@dataclass(frozen=True)
class Reduction:
    """Des entrées collectées que la normalisation reconnaît comme une seule.

    Ce n'est pas une tolérance : c'est la **même fonction** que la normalisation
    applique, rejouée ici sur le brut, appelée par son nom. Le compte qu'elle
    rend se soustrait au compte collecté, et le seuil du déficit reste 0.

    `compter` reçoit le répertoire brut et un slug, et rend le nombre d'entrées
    que la normalisation écarte pour ce profil. Elle lit le disque parce que le
    relevé en flux ne porte que des longueurs — c'est le seul endroit du module
    où un fragment de document est matérialisé, et il est borné au bloc
    `mandat_europeen` d'un profil (26 entrées sur le plus gros socle du corpus,
    8,3 Mo, mesuré le 13/09/2026).
    """

    #: Comment la réduction s'écrit dans le libellé de la relation.
    libelle: str
    #: Pourquoi la source publie ces entrées en double, en une phrase.
    justification: str
    #: `(raw_dir, slug) -> nombre d'entrées écartées`.
    compter: Callable[[Path, str], int]


#: Les seules clés dont `dedupliquer_appartenances` a besoin pour trancher :
#: l'organisation, la période, la classification de la source, le rôle. Le
#: crochet ci-dessous ne garde qu'elles, ce qui borne la mémoire comme le fait
#: `_crochet` pour le reste du module.
CLES_APPARTENANCE_EUROPEENNE = frozenset({
    "mandat_europeen",
    "mandats_europeens",
    "organisation_nom",
    "organisation_sigle",
    "debut",
    "fin",
    "type",
    "role",
    "role_label",
})


def _crochet_appartenances(pairs: list[tuple[str, Any]]) -> Optional[dict[str, Any]]:
    """Crochet qui garde le bloc européen **en entier**, et rien d'autre.

    `_crochet` réduit toute liste à sa longueur : il est fait pour compter. Ici
    il faut les entrées elles-mêmes, parce que c'est `dedupliquer_appartenances`
    qui décide lesquelles sont des doublons — et ce module ne réimplémente pas
    ce critère (#888).

    Les autres objets du socle — mandats de l'Assemblée, votes, interventions —
    traversent aussi ce crochet et n'en gardent que les clés ci-dessus, soit
    quelques chaînes chacun. `None` pour ceux qui n'en portent aucune.
    """
    garde: dict[str, Any] = {}
    for cle, valeur in pairs:
        if cle not in CLES_APPARTENANCE_EUROPEENNE:
            continue
        if cle == "mandats_europeens":
            garde[cle] = valeur if isinstance(valeur, list) else []
        elif isinstance(valeur, (dict, str)):
            garde[cle] = valeur
    return garde or None


def compter_doublons_europeens(raw_dir: Path, slug: str) -> int:
    """Combien d'appartenances européennes la normalisation écarte, pour ce profil.

    Rend 0 pour un profil sans bloc européen — l'écrasante majorité — et pour un
    socle illisible : l'appelant relève déjà l'illisibilité comme un
    rapprochement qui n'a pas eu lieu, et la compter deux fois brouillerait le
    verdict. Une entrée que le crochet a vidée (`None`) n'est jamais appariée :
    elle compte pour une entrée distincte, ce qui va dans le sens du contrôle.
    """
    chemin = raw_dir / f"{slug}{SUFFIXE_BRUT}"
    try:
        with chemin.open(encoding="utf-8") as flux:
            racine = json.load(flux, object_pairs_hook=_crochet_appartenances)
    except (OSError, ValueError):
        return 0
    if not isinstance(racine, dict):
        return 0
    bloc = racine.get("mandat_europeen")
    entrees = bloc.get("mandats_europeens") if isinstance(bloc, dict) else None
    if not isinstance(entrees, list):
        return 0
    _, ecartes = dedupliquer_appartenances([m for m in entrees if isinstance(m, dict)])
    return len(ecartes)


#: La seule réduction nommée du corpus à ce jour (#879, mesurée par #888).
REDUCTION_DOUBLONS_EUROPEENS = Reduction(
    libelle="doublons du portail européen (#879)",
    justification=(
        "Le portail européen publie la même appartenance **deux fois** — l'une "
        "classée, l'autre non — et `normalize_europarl.dedupliquer_appartenances` "
        "n'en publie qu'une (#879). Le brut garde les deux parce qu'il dit ce que "
        "la source a rendu ; le pivot en publie une parce que c'est **un** fait. "
        "Sans cette soustraction, le contrôle lit un déficit là où rien n'est "
        "perdu : 29 profils et 45 entrées au run `34712936188`, tous sur des "
        "profils à mandat européen (#888)."
    ),
    compter=compter_doublons_europeens,
)


#: La table. Une entrée par liste métier publiée, chacune avec sa justification.
#: Documentée dans `docs/decisions/collecte-vs-publie-545.md`, avec
#: les chiffres qui l'établissent.
RELATIONS: tuple[Relation, ...] = (
    Relation(
        champ_pivot="votes",
        sources=(("votes",),),
        justification=(
            "Égalité stricte. `normalize_profil.py:446` mappe un vote brut sur "
            "un vote pivot, un pour un ; la clé de fusion pivot "
            "(`_pivot_vote_key`) est le `scrutin_id`, aussi distinctif que la "
            "clé brute. Mesuré : 1 312 828 des deux côtés, 0 profil en écart. Depuis #683 le pivot porte **en plus** les votes du Parlement européen sur l'ensemble d'un texte, qui n'ont aucune contrepartie brute : les 7 profils européens sont en excédent, et c'est attendu."
        ),
    ),
    Relation(
        champ_pivot="amendements",
        sources=(("amendements",),),
        justification=(
            "Égalité stricte. `normalize_profil.py:449`, un pour un. C'est la "
            "liste la plus volumineuse du corpus (3 074 378 entrées) et donc "
            "celle où un effondrement de clé coûterait le plus cher. Mesuré : "
            "0 profil en écart. Depuis #683 s'y ajoutent les amendements du Parlement européen, sans contrepartie brute."
        ),
    ),
    Relation(
        champ_pivot="interventions",
        sources=(("interventions",),),
        justification=(
            "Égalité stricte — **c'est la relation que #540 violait**. "
            "`normalize_profil.py:448` mappe un pour un ; c'est la clé de "
            "FUSION pivot qui écrasait un débat entier sur une entrée. Mesuré "
            "avant correctif (`deb28a7`) : 7 767 collectées, 891 publiées. "
            "Après (`3104e37`) : 16 242 des deux côtés, 0 profil en écart. Depuis #683 s'y ajoutent les interventions, questions et explications de vote du Parlement européen, sans contrepartie brute."
        ),
    ),
    Relation(
        champ_pivot="textes_portes",
        sources=(("dossiers_legislatifs",),),
        justification=(
            "**Renommage**, pas une égalité de nom : le brut porte "
            "`dossiers_legislatifs`, le pivot `textes_portes` "
            "(`normalize_profil.py:447`). Comparer les champs de même nom "
            "rendrait −472 sur l'un et +472 sur l'autre — deux faux positifs "
            "pour zéro défaut. Mesuré : 472 des deux côtés, 0 profil en écart. Depuis #683 s'y ajoutent les rapports, avis et propositions de résolution du Parlement européen, sans contrepartie brute."
        ),
    ),
    Relation(
        champ_pivot="mandats",
        sources=(("mandats",), ("mandat_europeen", "mandats_europeens"),
                 ("mandat_senatorial", "mandats_senatoriaux")),
        justification=(
            "**Enrichissement attribué.** Le pivot porte 278 mandats de plus "
            "que `mandats[]` du brut, et ce n'est pas une marge : "
            "`generate_all_profiles.py:779` et `:989` versent les mandats "
            "européens dans `mandats[]` du pivot, là où le brut les range sous "
            "`mandat_europeen.mandats_europeens`. Mesuré : l'écart pivot−brut "
            "égale **exactement** ce compte sur les 476 profils, sans "
            "exception (40 432 = 40 154 + 278). D'où une somme, et un seuil qui "
            "reste 0 — jamais une tolérance. **Moins la réduction de #879** : le "
            "portail européen publie certaines appartenances deux fois, et la "
            "normalisation n'en publie qu'une. **Plus le bloc sénatorial depuis "
            "#885** : `mandat_senatorial.mandats_senatoriaux`, versé dans "
            "`mandats[]` par `generate_all_profiles` exactement comme l'européen. "
            "Le déclarer ici est ce qui distingue un apport d'une perte — sans "
            "cette ligne, la garde lirait un déficit de la taille du bloc et "
            "bloquerait le commit, ce qui est précisément ce qu'elle a fait au "
            "run `34712936188` pour la raison inverse (#888)."
        ),
        reduction=REDUCTION_DOUBLONS_EUROPEENS,
    ),
)

#: Champs du pivot qui n'ont **aucune** source collectée, et n'en attendent pas.
#: Ils sont dérivés d'autres champs du pivot lui-même, ou de sources qui ne sont
#: pas des profils bruts. Les nommer ici est ce qui rend l'absence de relation
#: un choix documenté plutôt qu'un oubli.
CHAMPS_PIVOT_DERIVES: dict[str, str] = {
    "chambres": "dérivé de `mandats[]` par `deriver_chambres()` (#493) — un "
                "compte de chambres distinctes, pas une liste collectée.",
    "tags_thematiques": "dérivé des `interventions[]` et des `textes_portes[]` "
                        "du pivot (`normalize_profil.py:482`). Aide à la "
                        "lecture, jamais une donnée collectée (AGENTS.md §2.8).",
    "sources": "journal des sources consultées par le run, construit à la "
               "normalisation ; aucun équivalent dans le brut.",
}

#: Écarts tolérés avant blocage. **0**, et la valeur est mesurée : 0 déficit sur
#: les 2 380 couples (profil, relation) du corpus de `3104e37`.
SEUIL_DEFICIT = 0

#: Nombre d'écarts nommés dans le rapport et sur stderr. Même plafond que
#: `audit_collecte_non_publiee` : le total et quelques noms rendent le constat
#: vérifiable à la main, 476 lignes identiques n'aideraient personne.
PLAFOND_EXEMPLES = 20


# ---------------------------------------------------------------------------
# Lecture à mémoire bornée
# ---------------------------------------------------------------------------

def _cles_surveillees() -> frozenset[str]:
    """Tout segment de chemin cité par la table, plus les champs pivot.

    Le crochet de décodage ne retient que ces clés-là. Tout le reste — les
    36 154 amendements d'un profil, leurs cosignataires — est jeté à la lecture.
    """
    cles: set[str] = {relation.champ_pivot for relation in RELATIONS}
    for relation in RELATIONS:
        for chemin in relation.sources:
            cles.update(chemin)
    return frozenset(cles)


CLES_SURVEILLEES = _cles_surveillees()


def _crochet(cles: frozenset[str], dernier: list):
    """Crochet `object_pairs_hook` qui réduit chaque objet à ses clés utiles.

    Rend `None` pour un objet sans clé utile — le cas de l'écrasante majorité
    (chaque amendement, chaque vote). C'est ce `None` qui borne la mémoire : le
    décodeur construit bien une liste de 36 154 éléments, mais de 36 154
    `None`, et les chaînes de chaque entrée sont libérées dès l'objet refermé.

    Une liste devient sa **longueur**, un objet imbriqué reste un objet réduit :
    la navigation par chemin se fait ensuite sur cette structure minuscule.

    `dernier` retient les paires du **dernier** objet lu. Un décodeur récursif
    referme l'objet le plus extérieur en dernier : ce sont donc les paires de la
    racine, et c'est ainsi qu'on connaît les listes de premier niveau **que la
    table ne déclare pas** — celles de la prochaine source branchée. Une seule
    référence est gardée à la fois (`del dernier[:-1]`), et ses valeurs sont
    déjà réduites : le coût est celui d'un `append`, pas d'un parcours.
    """

    def crochet(pairs: list[tuple[str, Any]]) -> Optional[dict[str, Any]]:
        dernier.append(pairs)
        del dernier[:-1]
        garde: dict[str, Any] = {}
        for cle, valeur in pairs:
            if cle not in cles:
                continue
            if isinstance(valeur, list):
                garde[cle] = len(valeur)
            elif isinstance(valeur, dict):
                garde[cle] = valeur
        return garde or None

    return crochet


def compter_listes(chemin: Path, cles: frozenset[str] = CLES_SURVEILLEES) -> dict[str, Any]:
    """Relevé d'un document, sans jamais le matérialiser.

    Rend un dict qui porte :

      - la **longueur de toute liste de premier niveau**, déclarée dans la table
        ou non. Les listes non déclarées sont ce qui permet de repérer une
        source branchée dont personne n'a encore écrit la relation ;
      - les objets imbriqués réduits aux seules clés surveillées, pour que
        `mandat_europeen.mandats_europeens` reste atteignable.

    Lève `ValueError` si le document n'est pas un objet JSON lisible : ici, un
    fichier illisible n'est pas « 0 entrée », c'est un rapprochement qui n'a pas
    eu lieu (AGENTS.md §2.5). L'appelant le compte à part.
    """
    dernier: list = []
    with chemin.open(encoding="utf-8") as flux:
        racine = json.load(flux, object_pairs_hook=_crochet(cles, dernier))
    if racine is not None and not isinstance(racine, dict):
        raise ValueError("document JSON qui n'est pas un objet")
    if not dernier:
        # Document JSON valide qui n'est pas un objet (une liste, un scalaire).
        raise ValueError("document JSON qui n'est pas un objet")
    releve: dict[str, Any] = dict(racine or {})
    releve.update({cle: len(valeur) for cle, valeur in dernier[0]
                   if isinstance(valeur, list)})
    return releve


def compter_listes_profil_brut(
    raw_dir: Path, slug: str, cles: frozenset[str] = CLES_SURVEILLEES
) -> dict[str, Any]:
    """Relevé d'un profil brut, **partition par législature comprise** (#580).

    Depuis #580 le socle `<slug>.json` ne porte plus `amendements` : la liste
    vit en tranches sous `<slug>/<legislature>.json`. Sans cette fonction, ce
    contrôle lirait « 0 amendement collecté » face à 6 millions publiés — il ne
    signalerait aucun déficit et deviendrait aveugle sur 96,7 % du volume, ce
    qui est exactement le genre de vert sans mesure que #545 traque.

    Le compte est **mesuré**, tranche par tranche, jamais recopié du `total`
    annoncé par le manifeste : un contrôle qui lit sa conclusion dans le
    document qu'il contrôle ne contrôle rien (#576, #579). Chaque tranche passe
    par le même `compter_listes`, donc la mémoire reste bornée comme avant —
    aucune liste n'est matérialisée.

    Un profil encore monolithique est relevé tel quel : les deux formes
    cohabitent tant que le dépôt n'est pas migré.
    """
    releve = compter_listes(raw_dir / f"{slug}{SUFFIXE_BRUT}", cles)

    # La forme se lit sur le DISQUE, pas dans le manifeste : `compter_listes`
    # réduit délibérément les objets imbriqués, donc le manifeste n'arrive pas
    # jusqu'ici — et surtout, le répertoire de tranches est un fait observable
    # là où le manifeste est une déclaration.
    #
    # SAUF POUR UNE TRANCHE DÉRIVÉE (#691), qui n'a pas de disque à observer.
    # Le principe tient quand même, et c'est ce qui autorise l'exception : ce
    # qui est interdit ici, c'est de recopier le `nombre` que le manifeste
    # ANNONCE — un contrôle qui lit sa conclusion dans le document qu'il
    # contrôle ne contrôle rien (#576, #579). L'archive figée n'est pas ce
    # document : elle est versionnée, close, et le compte y est **mesuré**
    # exactement comme il l'est dans une tranche sur disque. Le manifeste ne
    # sert qu'à dire OÙ compter.
    #
    # Sans ce chemin, ce contrôle lirait « 0 amendement collecté » face à des
    # millions publiés dès la première tranche dérivée — le défaut que son
    # propre docstring donne comme celui à éviter.
    derivees = _tranches_derivees(raw_dir / f"{slug}{SUFFIXE_BRUT}")
    dossier = raw_dir / slug
    if not dossier.is_dir() and not derivees:
        return releve

    if CLE_PARTITIONNEE in releve:
        raise ValueError(
            f"{slug} : le socle porte encore `{CLE_PARTITIONNEE}` alors qu'une "
            f"partition existe ({dossier}). La donnée serait comptée deux fois."
        )
    tranches = sorted(dossier.glob("*.json")) if dossier.is_dir() else []
    if not tranches and not derivees:
        raise ValueError(f"{slug} : répertoire de tranches vide ({dossier})")
    releve[CLE_PARTITIONNEE] = sum(
        _longueur(compter_listes(tranche, cles), (CLE_PARTITIONNEE,))
        for tranche in tranches
    ) + _compter_derivees(slug, derivees)
    return releve


def _tranches_derivees(chemin_socle: Path) -> list[dict[str, Any]]:
    """Les tranches que le manifeste déclare dérivables (#691).

    Un socle illisible rend une liste vide plutôt que de lever : ce module
    relève, il ne valide pas la partition — c'est `profil_brut` qui refuse un
    manifeste malformé, à la lecture, et là où l'erreur est actionnable.
    """
    try:
        with open(chemin_socle, encoding="utf-8") as fichier:
            socle = json.load(fichier)
    except (OSError, json.JSONDecodeError):
        return []
    manifeste = socle.get(CLE_MANIFESTE) if isinstance(socle, dict) else None
    if not isinstance(manifeste, dict):
        return []
    return [
        t for t in (manifeste.get("tranches") or [])
        if isinstance(t, dict) and t.get(CLE_TRANCHE_DERIVEE)
    ]


def _compter_derivees(slug: str, derivees: list[dict[str, Any]]) -> int:
    """Compte les amendements des tranches dérivées, **dans l'archive**.

    `signatures()` et non `reconstruire_tranche()` : compter n'a besoin que de
    l'index par acteur, pas du store des amendements — 10,5 Mo au lieu de
    plusieurs centaines, sur un contrôle qui boucle sur tout le corpus.

    Une tranche déclarée dérivée et non dérivable lève : c'est un profil dont
    les amendements ne se relisent pas, et le taire ferait passer un déficit
    pour une absence (#511).
    """
    if not derivees:
        return 0
    import tranches_amendements_figees as figees

    total = 0
    for declaree in derivees:
        entrees = figees.signatures(
            declaree.get(CLE_ACTEUR_TRANCHE), str(declaree.get("legislature") or "")
        )
        if entrees is None:
            raise ValueError(
                f"{slug} : tranche dérivée non dérivable "
                f"(législature {declaree.get('legislature')!r}, "
                f"acteur {declaree.get(CLE_ACTEUR_TRANCHE)!r}) — "
                "le compte collecté serait faux."
            )
        total += len(entrees)
    return total


def _longueur(releve: dict[str, Any], chemin: tuple[str, ...]) -> int:
    """Longueur de la liste au bout d'un chemin, 0 si la route casse.

    Un champ absent vaut 0 — indistinct d'une liste vide, et c'est voulu : dans
    les deux cas le document ne porte aucune entrée.
    """
    courant: Any = releve
    for segment in chemin:
        if not isinstance(courant, dict):
            return 0
        courant = courant.get(segment)
    return courant if isinstance(courant, int) else 0


def _listes_du_brut(releve: dict[str, Any]) -> set[str]:
    """Clés de premier niveau du brut qui portent une liste (longueur relevée)."""
    return {cle for cle, valeur in releve.items() if isinstance(valeur, int)}


# ---------------------------------------------------------------------------
# Rapprochement
# ---------------------------------------------------------------------------

@dataclass
class Ecart:
    """Un couple (profil, relation) dont les deux comptes ne coïncident pas."""

    slug: str
    champ_pivot: str
    libelle_sources: str
    collecte: int
    publie: int

    @property
    def delta(self) -> int:
        return self.publie - self.collecte

    def as_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "champ_pivot": self.champ_pivot,
            "sources": self.libelle_sources,
            "collecte": self.collecte,
            "publie": self.publie,
            "delta": self.delta,
        }


def _phrase(ecart: dict[str, Any]) -> str:
    """Un écart en une phrase, pour stderr et pour l'annotation.

    Prend le **dict** du rapport et non l'objet : le rapport est ce qui sort en
    JSON, et faire dire la même phrase aux deux garantit qu'un lecteur d'annotation
    et un lecteur de rapport lisent le même chiffre.
    """
    return (f"{ecart['slug']} — {ecart['champ_pivot']} : "
            f"{ecart['collecte']} collectée(s) ({ecart['sources']}), "
            f"{ecart['publie']} publiée(s) ({ecart['delta']:+})")


@dataclass
class Totaux:
    """Compteurs agrégés d'une relation, sur toute la population lue."""

    collecte: int = 0
    publie: int = 0
    profils_en_deficit: int = 0
    profils_en_excedent: int = 0


def _slugs_bruts(raw_dir: Path) -> list[str]:
    """Slugs des profils bruts, d'après les seuls noms de fichiers.

    Mêmes exclusions que `audit_collecte_non_publiee._slugs` et pour la même
    raison : `slugify` ne produit que `[a-z0-9-]`, donc écarter les fichiers
    cachés n'écarte aucun profil et rend le contrôle indépendant des fichiers de
    service (`.generation_checkpoint.json`).
    """
    if not raw_dir.is_dir():
        return []
    slugs = []
    for chemin in sorted(raw_dir.iterdir()):
        nom = chemin.name
        if not chemin.is_file() or not nom.endswith(SUFFIXE_BRUT):
            continue
        if nom.startswith(".") or nom.endswith(SUFFIXE_PIVOT):
            continue
        slugs.append(nom[: -len(SUFFIXE_BRUT)])
    return slugs


def auditer(
    raw_dir: Path,
    pivot_dir: Path,
    *,
    relations: tuple[Relation, ...] = RELATIONS,
    seuil: int = SEUIL_DEFICIT,
    plafond_exemples: int = PLAFOND_EXEMPLES,
) -> dict[str, Any]:
    """Rapproche les deux couches telles qu'elles sont sur le disque.

    Pas de git, comme `audit_collecte_non_publiee` et `audit_integrite_referentielle` :
    ce contrôle porte sur **un** état — les deux étages du pipeline dans le même
    run — et n'a pas de point de comparaison dans le temps. C'est précisément ce
    qui le distingue d'`audit_diff_profils`.
    """
    repertoire_brut_absent = not raw_dir.is_dir()
    repertoire_pivot_absent = not pivot_dir.is_dir()

    deficits: list[Ecart] = []
    excedents: list[Ecart] = []
    totaux: dict[str, Totaux] = {r.champ_pivot: Totaux() for r in relations}
    illisibles: list[str] = []
    sans_pivot: list[str] = []
    listes_non_declarees: dict[str, set[str]] = {}

    declarees = {segment
                 for relation in relations
                 for chemin in relation.sources
                 for segment in chemin[:1]}

    provenances, _ = lire_provenances(pivot_dir)

    nb_compares = 0
    slugs_compares: list[str] = []
    for slug in _slugs_bruts(raw_dir):
        chemin_pivot = pivot_dir / f"{slug}{SUFFIXE_PIVOT}"
        if not chemin_pivot.is_file():
            # #511 traite ce cas et bloque dessus. Le compter ici sans le
            # bloquer évite de doubler l'alerte, et évite surtout de rapporter
            # un déficit de 100 % qui décrirait un autre défaut que le nôtre.
            sans_pivot.append(slug)
            continue
        try:
            releve_brut = compter_listes_profil_brut(raw_dir, slug)
            releve_pivot = compter_listes(chemin_pivot)
        except (OSError, ValueError):
            # Un profil illisible n'est pas « 0 entrée » : c'est un
            # rapprochement qui n'a pas eu lieu. Il bloque, parce que le taire
            # rendrait vert exactement ce que ce contrôle traque.
            illisibles.append(slug)
            continue

        nb_compares += 1
        slugs_compares.append(slug)
        non_declarees = _listes_du_brut(releve_brut) - declarees
        if non_declarees:
            listes_non_declarees[slug] = non_declarees

        for relation in relations:
            collecte = sum(_longueur(releve_brut, c) for c in relation.sources)
            if relation.reduction is not None:
                # Le compte collecté est celui des entrées **distinctes** : une
                # appartenance que la source publie deux fois n'en fait qu'une
                # (#888). Jamais en dessous de 0 — une réduction qui dépasserait
                # son propre chemin serait un défaut de ce module, pas un
                # excédent du corpus.
                collecte = max(0, collecte - relation.reduction.compter(raw_dir, slug))
            publie = _longueur(releve_pivot, (relation.champ_pivot,))
            total = totaux[relation.champ_pivot]
            total.collecte += collecte
            total.publie += publie
            if publie < collecte:
                total.profils_en_deficit += 1
                deficits.append(Ecart(slug, relation.champ_pivot,
                                      relation.libelle_sources, collecte, publie))
            elif publie > collecte:
                total.profils_en_excedent += 1
                excedents.append(Ecart(slug, relation.champ_pivot,
                                       relation.libelle_sources, collecte, publie))

    # Les plus gros écarts d'abord : c'est le tri qui rend les 20 exemples
    # informatifs. #540 aurait nommé `gabriel-attal` en tête, pas un profil
    # à 1 entrée d'écart.
    deficits.sort(key=lambda e: (e.delta, e.slug, e.champ_pivot))
    excedents.sort(key=lambda e: (-e.delta, e.slug, e.champ_pivot))

    champs_non_declares = sorted({c for cs in listes_non_declarees.values() for c in cs})

    return {
        "raw_dir": str(raw_dir),
        "pivot_dir": str(pivot_dir),
        "repertoire_brut_absent": repertoire_brut_absent,
        "repertoire_pivot_absent": repertoire_pivot_absent,
        "nb_profils_compares": nb_compares,
        "ventilation_provenance": ventiler_provenances(
            provenances.get(slug, CANDIDAT_DECLARE) for slug in slugs_compares
        ).as_dict(),
        "nb_sans_pivot": len(sans_pivot),
        "sans_pivot": sans_pivot[:plafond_exemples],
        "nb_illisibles": len(illisibles),
        "illisibles": illisibles[:plafond_exemples],
        "relations": [
            {
                "champ_pivot": r.champ_pivot,
                "sources": r.libelle_sources,
                "nature": ("enrichissement attribué" if r.est_enrichissement
                           else "renommage" if r.est_renommage else "égalité"),
                "justification": (
                    r.justification if r.reduction is None
                    else f"{r.justification} {r.reduction.justification}"
                ),
                "collecte": totaux[r.champ_pivot].collecte,
                "publie": totaux[r.champ_pivot].publie,
                "delta": (totaux[r.champ_pivot].publie
                          - totaux[r.champ_pivot].collecte),
                "profils_en_deficit": totaux[r.champ_pivot].profils_en_deficit,
                "profils_en_excedent": totaux[r.champ_pivot].profils_en_excedent,
            }
            for r in relations
        ],
        "nb_deficits": len(deficits),
        "deficits": [e.as_dict() for e in deficits[:plafond_exemples]],
        "nb_excedents": len(excedents),
        "excedents": [e.as_dict() for e in excedents[:plafond_exemples]],
        "champs_bruts_non_declares": champs_non_declares,
        "nb_profils_champs_non_declares": len(listes_non_declarees),
        "plafond_exemples": plafond_exemples,
        "seuil": seuil,
        "bloquant": (
            len(deficits) > seuil
            or bool(illisibles)
            or repertoire_brut_absent
            or repertoire_pivot_absent
        ),
    }


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def _fr(nombre: int, signe: bool = False) -> str:
    """Entier en écriture française : espace fine comme séparateur de milliers.

    Sur les seuls nombres, jamais sur la ligne entière : un `str.replace(",", " ")`
    appliqué à la ligne de tableau réécrirait aussi les virgules d'un libellé.
    """
    gabarit = f"{nombre:+,}" if signe else f"{nombre:,}"
    return gabarit.replace(",", " ")


def generate_markdown_report(rapport: dict[str, Any]) -> str:
    """Rapport Markdown, joint au résumé de job à chaque run."""
    lignes = [
        "# Collecté vs publié, liste par liste",
        "",
        "> Ce que la collecte a rendu, comparé à ce que la publication porte, "
        "**pour chaque liste métier** (#545). Quatrième angle : le contrôle de "
        "perte (#460/#470) compare deux états publiés dans le temps, "
        "celui-ci compare deux **étages du pipeline dans le même run**. "
        "#511 raisonne sur des profils, #485 ne compte rien.",
        "",
        f"Population : **{rapport['nb_profils_compares']} profil(s)** "
        f"{Ventilation.depuis_dict(rapport.get('ventilation_provenance')).detail()} "
        f"rapproché(s) entre `{rapport['raw_dir']}` et `{rapport['pivot_dir']}`.",
        "",
        "## Relations attendues",
        "",
        "| Liste publiée | Doit égaler, dans le brut | Nature | Collecté | Publié | Écart |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for relation in rapport["relations"]:
        delta = relation["delta"]
        marque = "**" if delta else ""
        lignes.append(
            f"| `{relation['champ_pivot']}` | `{relation['sources']}` | "
            f"{relation['nature']} | {_fr(relation['collecte'])} | "
            f"{_fr(relation['publie'])} | {marque}{_fr(delta, signe=True)}{marque} |"
        )
    lignes.append("")

    if rapport["repertoire_brut_absent"] or rapport["repertoire_pivot_absent"]:
        manquant = ("répertoire des profils bruts"
                    if rapport["repertoire_brut_absent"]
                    else "répertoire des pivots")
        lignes += [
            f"**Le {manquant} est absent.** Un rapprochement qui n'a rien lu "
            "n'est pas un rapprochement vert.",
            "",
        ]
    elif rapport["nb_deficits"] > rapport["seuil"]:
        lignes += [
            f"**{rapport['nb_deficits']} couple(s) (profil, liste) publient "
            f"moins que ce que la collecte a rendu** (seuil : "
            f"{rapport['seuil']}). La donnée est sur le disque, dans "
            f"`{rapport['raw_dir']}`, et n'atteint aucune vue.",
            "",
        ]
    elif rapport["nb_profils_compares"] == 0:
        lignes += [
            "**Aucun profil rapproché.** Ce n'est pas un état sain : c'est un "
            "contrôle qui n'a rien lu.",
            "",
        ]
    else:
        lignes += [
            f"**Chaque liste publiée porte ce que la collecte a rendu**, sur "
            f"les {rapport['nb_profils_compares']} profil(s) "
            f"{Ventilation.depuis_dict(rapport.get('ventilation_provenance')).detail()} "
            f"rapproché(s) et "
            f"les {len(rapport['relations'])} relations déclarées.",
            "",
        ]

    if rapport["deficits"]:
        lignes += [
            "## Déficits — collecté, jamais publié (bloquant)",
            "",
            "| Profil | Liste | Collecté | Publié | Écart |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
        for ecart in rapport["deficits"]:
            lignes.append(
                f"| `{ecart['slug']}` | `{ecart['champ_pivot']}` | "
                f"{ecart['collecte']} | {ecart['publie']} | {ecart['delta']:+} |"
            )
        reste = rapport["nb_deficits"] - len(rapport["deficits"])
        if reste > 0:
            lignes.append(f"| … | … et {reste} autre(s), non détaillé(s) | | | |")
        lignes.append("")

    if rapport["excedents"]:
        lignes += [
            "## Excédents — publié plus que collecté (non bloquant)",
            "",
            "**Deux causes, et elles ne se lisent pas pareil.** (1) La fusion "
            "pivot est additive : un pivot conserve les entrées d'un run "
            "précédent que la collecte du jour n'a pas rendues (AGENTS.md §3) "
            "— c'est de la dérive. (2) Depuis #683, quatre listes portent du "
            "matériau du Parlement européen versé depuis les dumps ParlTrack, "
            "qui n'a aucune contrepartie dans `raw_data/` — les 7 candidats "
            "déclarés à identifiant européen sont donc attendus ici, sur "
            "`votes`, `amendements`, `interventions` et `textes_portes`. "
            "Compteur, jamais un verdict.",
            "",
            "| Profil | Liste | Collecté | Publié | Écart |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
        for ecart in rapport["excedents"]:
            lignes.append(
                f"| `{ecart['slug']}` | `{ecart['champ_pivot']}` | "
                f"{ecart['collecte']} | {ecart['publie']} | {ecart['delta']:+} |"
            )
        reste = rapport["nb_excedents"] - len(rapport["excedents"])
        if reste > 0:
            lignes.append(f"| … | … et {reste} autre(s), non détaillé(s) | | | |")
        lignes.append("")

    if rapport["champs_bruts_non_declares"]:
        champs = ", ".join(f"`{c}`" for c in rapport["champs_bruts_non_declares"])
        lignes += [
            "## Listes collectées sans relation déclarée (non bloquant)",
            "",
            f"{champs} — présent(s) dans "
            f"{rapport['nb_profils_champs_non_declares']} profil(s) brut(s) et "
            "dans aucune entrée de la table. C'est le cas de la **prochaine "
            "source branchée** : tant que sa relation n'est pas écrite, rien ne "
            "vérifie qu'elle est publiée. Signalé, jamais bloquant — personne "
            "ne doit voir un commit annulé au motif qu'une relation reste à "
            "écrire.",
            "",
        ]

    if rapport["nb_illisibles"]:
        lignes += [
            "## Profils illisibles (bloquant)",
            "",
            "Un profil qu'on n'a pas pu lire n'est pas un profil à 0 entrée : "
            "c'est un rapprochement qui n'a pas eu lieu (AGENTS.md §2.5).",
            "",
        ]
        lignes += [f"- `{slug}`" for slug in rapport["illisibles"]]
        reste = rapport["nb_illisibles"] - len(rapport["illisibles"])
        if reste > 0:
            lignes.append(f"- … et {reste} autre(s), non détaillé(s).")
        lignes.append("")

    if rapport["nb_sans_pivot"]:
        lignes += [
            "## Bruts sans pivot (hors périmètre de ce contrôle)",
            "",
            f"{rapport['nb_sans_pivot']} profil(s) brut(s) sans pivot : c'est "
            "le périmètre d'`audit_collecte_non_publiee` (#511), qui bloque "
            "dessus. Compté ici pour que la population du rapprochement soit "
            "lisible, jamais rapporté en déficit — ce serait décrire un autre "
            "défaut que le nôtre.",
            "",
        ]

    lignes += [
        "## Hors périmètre de ce contrôle",
        "",
        "- les champs **dérivés** du pivot, qui n'ont aucune source collectée : ",
    ]
    lignes += [f"  - `{champ}` : {raison}"
               for champ, raison in sorted(CHAMPS_PIVOT_DERIVES.items())]
    lignes += [
        "- le **contenu** des entrées : ce contrôle compte, il ne compare pas "
        "les valeurs. Une entrée publiée vide compte pour une ;",
        "- les couches agrégées (`groupes/`, `partis/`, `gouvernements/`), qui "
        "n'ont pas de brut à rapprocher un pour un ;",
        "- la **variation dans le temps** : c'est `audit_diff_profils` (#460/#470).",
        "",
    ]
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--raw-dir", default="raw_data/profiles", metavar="REP",
                        help="Répertoire des profils bruts (défaut : raw_data/profiles).")
    parser.add_argument("--pivot-dir", default="pivot_data/profiles", metavar="REP",
                        help="Répertoire des profils pivots (défaut : pivot_data/profiles).")
    parser.add_argument("--out", metavar="FICHIER", help="Rapport Markdown.")
    parser.add_argument("--out-json", metavar="FICHIER", help="Rapport JSON.")
    parser.add_argument(
        "--seuil", type=int, default=SEUIL_DEFICIT, metavar="N",
        help=f"Couples (profil, liste) en déficit tolérés (défaut : {SEUIL_DEFICIT}). "
             "La valeur par défaut est mesurée, pas arrondie : 0 déficit sur les "
             "2 380 couples (profil, relation) du corpus de `3104e37`.",
    )
    parser.add_argument(
        "--tolerer-ecarts", action="store_true",
        help="Ne pas sortir en erreur malgré des listes publiées en déficit. "
             "DISTINCT de --tolerer-pertes (audit_diff_profils), "
             "--tolerer-orphelins (audit_integrite_referentielle) et "
             "--tolerer-non-publies (audit_collecte_non_publiee) : les quatre "
             "tolérances restent cloisonnées, désarmer l'une ne doit jamais "
             "désarmer les autres (#470).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    raw_dir = Path(args.raw_dir)
    pivot_dir = Path(args.pivot_dir)

    print(f"→ collecté/publié, liste par liste : {raw_dir} ↔ {pivot_dir}…",
          file=sys.stderr)
    rapport = auditer(raw_dir, pivot_dir, seuil=args.seuil)
    markdown = generate_markdown_report(rapport)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(markdown, encoding="utf-8")
        print(f"→ Rapport écrit : {args.out}", file=sys.stderr)
    else:
        print(markdown)
    if args.out_json:
        Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out_json).write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    if rapport["repertoire_brut_absent"]:
        print(f"[!] {raw_dir} est absent : rien n'a été rapproché.", file=sys.stderr)
        gha.annoter("error", f"COLLECTE_VS_PUBLIE — {raw_dir} est absent : "
                             "rien n'a été rapproché.")
    if rapport["repertoire_pivot_absent"]:
        print(f"[!] {pivot_dir} est absent : rien n'a été rapproché.", file=sys.stderr)
        gha.annoter("error", f"COLLECTE_VS_PUBLIE — {pivot_dir} est absent : "
                             "rien n'a été rapproché.")

    if rapport["nb_sans_pivot"]:
        print(f"  {rapport['nb_sans_pivot']} profil(s) brut(s) sans pivot : "
              "hors périmètre ici, c'est #511 qui bloque dessus.", file=sys.stderr)

    if rapport["nb_excedents"]:
        for ecart in rapport["excedents"]:
            print(f"  {_phrase(ecart)} — excédent, non bloquant.", file=sys.stderr)

    # #518 : ce qui n'a pas de relation déclarée part en annotation. Sans elle,
    # une source branchée sans relation resterait invisible jusqu'à la prochaine
    # relecture manuelle — c'est-à-dire exactement le régime qui a laissé #540
    # vivre un run entier.
    if rapport["champs_bruts_non_declares"]:
        champs = ", ".join(rapport["champs_bruts_non_declares"])
        message = (f"COLLECTE_VS_PUBLIE — liste(s) collectée(s) sans relation "
                   f"déclarée dans RELATIONS : {champs} "
                   f"({rapport['nb_profils_champs_non_declares']} profil(s)). "
                   "Rien ne vérifie qu'elles sont publiées (#545).")
        print(f"[!] {message}", file=sys.stderr)
        gha.annoter("warning", message)

    if rapport["nb_illisibles"]:
        for slug in rapport["illisibles"]:
            print(f"[!] {slug} : profil illisible, rapprochement impossible.",
                  file=sys.stderr)

    if rapport["bloquant"]:
        exemples_lisibles = []
        for ecart in rapport["deficits"]:
            phrase = _phrase(ecart)
            print(f"[!] {phrase}", file=sys.stderr)
            exemples_lisibles.append(phrase)
        reste = rapport["nb_deficits"] - len(rapport["deficits"])
        if reste > 0:
            print(f"[!] … et {reste} autre(s), non détaillé(s).", file=sys.stderr)

        manque = sum(max(0, -r["delta"]) for r in rapport["relations"])
        resume = (f"{rapport['nb_deficits']} couple(s) (profil, liste) publient "
                  f"moins que ce que la collecte a rendu, soit {manque} entrée(s) "
                  f"collectée(s) et publiée(s) nulle part "
                  f"(seuil : {rapport['seuil']}).")
        if rapport["nb_illisibles"]:
            resume += f" {rapport['nb_illisibles']} profil(s) illisible(s)."
        print(f"[!] {resume}", file=sys.stderr)

        exemples = " ; ".join(exemples_lisibles)
        if reste > 0:
            exemples += f" ; … (+{reste})"
        gha.annoter(
            "error" if not args.tolerer_ecarts else "warning",
            f"COLLECTE_VS_PUBLIE — {resume}"
            + (f" Profil(s) : {exemples}" if exemples else ""),
        )
        return 0 if args.tolerer_ecarts else 1

    print(f"✓ {rapport['nb_profils_compares']} profil(s) "
          f"{Ventilation.depuis_dict(rapport.get('ventilation_provenance')).detail()} "
          f"rapproché(s) sur {len(rapport['relations'])} relation(s) : chaque liste "
          "publiée porte ce que la collecte a rendu.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
