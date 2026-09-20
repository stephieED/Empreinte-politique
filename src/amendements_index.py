#!/usr/bin/env python3
"""amendements_index.py — Liste dédupliquée des amendements, partagée (#431).

Un amendement est **identique pour tous ses signataires** : `texte_vise`,
`sort`, `date`, `numero`, `type_deposant`, `premier_signataire`,
`co_signataires`… Seul le `role_signataire` est propre au membre. Pourtant
`_parse_amendement_entry` produit un enregistrement complet **par signataire**,
chacun portant sa propre copie de la liste des cosignataires : pour un
amendement à N cosignataires, N copies d'une liste de N éléments.

Mesuré sur les 209 profils pivot committés au 19/08/2026 (`ff3639b`) :

| | paires | distincts | duplication |
| --- | --- | --- | --- |
| `amendements` | 810 552 | 207 238 | × 3,9 |
| `amendements[].co_signataires` | 77 666 854 | 4 957 807 | **× 15,7** |

Le vrai coût n'est donc pas l'amendement mais **sa liste de cosignataires** :
23,9 cosignataires en moyenne, recopiée dans le profil de chacun d'eux. C'est
1 083,9 Mo des 1 342,4 Mo qu'`amendements[]` pèse dans les profils pivot.

CE QUI RESTE DANS LE PROFIL. Le mapping `{amendement_id, role_signataire}` —
exactement ce qui est propre au membre. Principe directeur de l'épic #429 :
normaliser, jamais supprimer.

L'IDENTIFIANT. `an:<uid>` — convention `<source>:<identifiant_source>` du dépôt.
L'`uid` AN est la **seule** clé unique d'un amendement : le `numero`
(`numeroLong`) repart à chaque texte, et keyer par lui écrase 74,9 % des
amendements (#440, [[amendements-cle-uid]]). Sa couverture est de 100 % sur les
810 552 paires committées — c'est ce qui débloque cette normalisation.

OÙ VIT LA LISTE. Un fichier **par législature**, plus un fichier compagnon pour
les cosignatures :

    pivot_data/amendements/<legislature>.json               (méta)
    pivot_data/amendements/<legislature>.cosignatures.json  (cosignatures)

Ce n'est pas une préférence, c'est une contrainte mesurée — voir
docs/decisions/normalisation-amendements.md. Un fichier global
unique pèserait **128,8 Mo** sur les seuls 209 profils actuels, au-delà de la
limite GitHub de 100 Mo par blob ; et un fichier par législature contenant
aussi les cosignatures atteindrait ~166 Mo pour la XVe à couverture complète
des archives AN (746 000 amendements pour les législatures 14-17).

POURQUOI LES COSIGNATURES À PART. Elles pèsent 75,7 Mo des 128,8 Mo (59 %) et
**aucun consommateur ne les lit** aujourd'hui : ni `group_profile`, ni l'UI, ni
les audits. Les isoler leur évite de télécharger 59 % d'un index dont ils
n'utilisent rien, tout en les gardant accessibles — un réseau de cosignatures
est de la matière première d'analyse (#324). Elles ne sont **jamais** supprimées.

LE DOSSIER LÉGISLATIF, UNE FOIS PAR TEXTE (#639). `texte_vise` porte l'uid du
**document** amendé (`PRJLANR5L15B1088`), et la table `textes` du fichier le
joint à son **dossier** (`DLR5L15N36030`) et au titre lisible de celui-ci. Elle
est une table, pas un champ par amendement : les 484 132 amendements publiés ne
visent que 2 248 textes distincts, et recopier le `dossier_id` dans chacun
coûterait 5,7 Mio là où la table en coûte 0,10 — le raisonnement de #431 pour
les cosignataires, un cran plus loin. Un amendement dont le texte n'est pas dans
la table reste **sans dossier**, et il s'en compte : voir `resoudre_textes`.

CE QUI N'EST PAS NORMALISÉ. `raw_data/profiles` garde ses amendements
dénormalisés : c'est la couche source-near, et c'est **d'elle** que l'index est
reconstruit. Même décision que pour les votes ([[normalisation-votes]]).

NE JAMAIS RE-MATÉRIALISER LA FORME PLATE. Aucune fonction de ce module ne
reconstruit un enregistrement complet par signataire, et `get()` rend
**l'objet partagé lui-même**, jamais une copie. C'est l'erreur qu'avait faite
`_load_frozen_amendement_index` en appelant `_expand_aggregated_amendements_index`
« pour que le reste du pipeline n'ait pas à distinguer les deux origines » :
facteur ~21 et un OOM (#377, [[cache-amendements-forme-dedupliquee]]).
Verrouillé par `tests/test_amendements_index.py`.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Optional

from json_io import ecrire_profil_json
from licences import LICENCE_AN
from profil_brut import iter_amendements_du_profil
from textes_vises_figes import est_uid_texte

SCHEMA_VERSION = "amendements-v1"
COSIGNATURES_SCHEMA_VERSION = "amendements-cosignatures-v1"
SOURCE_AN = "an"

DEFAULT_AMENDEMENTS_DIR = Path("pivot_data") / "amendements"

#: Alias du libellé canonique, qui vit dans `licences` depuis #530 (lot 6) :
#: une seule fabrique pour toutes les mentions d'attribution du pipeline.
LICENCE_DONNEES = LICENCE_AN

# Champs de l'amendement, communs à tous ses signataires. Le mapping du profil
# n'en porte aucun : les y laisser, c'est la duplication que #431 supprime.
#
# `co_signataires` n'y figure pas : il vit dans le fichier compagnon, pour que
# les consommateurs qui ne le lisent pas (tous, aujourd'hui) n'en chargent pas
# les 75,7 Mo.
CHAMPS_AMENDEMENT = (
    "texte_vise",
    "sort",
    "base_juridique_irrecevabilite",
    "premier_signataire",
    "type_deposant",
    "date",
    "numero",
    "source_url",
)

# Bucket des amendements dont l'`uid` ne porte pas de législature reconnaissable.
# Zéro cas sur les données actuelles ; le bucket existe pour que le jour où il
# s'en présente un, il soit rangé quelque part de nommé plutôt que doté d'une
# législature devinée (AGENTS.md §2.5).
LEGISLATURE_INCONNUE = "inconnue"

_RE_LEGISLATURE_UID = re.compile(r"^AMANR5L(\d+)")

_SUFFIXE_COSIGNATURES = ".cosignatures.json"


def cle_amendement(uid: Any) -> Optional[str]:
    """`AMANR5L17PO59051B2464P0D1N000312` → `an:AMANR5L17PO59051B2464P0D1N000312`.

    `None` si l'`uid` est absent : un amendement sans `uid` n'a **pas** de clé,
    et on ne lui en invente pas (AGENTS.md §2.5). Son enregistrement complet est
    alors conservé côté profil sous `amendement_non_resolu`.
    """
    if not isinstance(uid, str) or not uid:
        return None
    return f"{SOURCE_AN}:{uid}"


def decomposer_id(amendement_id: Any) -> Optional[str]:
    """`"an:AMANR5L17…"` → `"AMANR5L17…"`. `None` si la forme n'est pas
    reconnue — un identifiant mal formé ne doit pas se faire deviner."""
    if not isinstance(amendement_id, str):
        return None
    prefixe = f"{SOURCE_AN}:"
    if not amendement_id.startswith(prefixe):
        return None
    uid = amendement_id[len(prefixe):]
    return uid or None


def legislature_de_uid(uid: Any) -> Optional[str]:
    """Législature portée par l'`uid` AN (`AMANR5L17…` → `"17"`).

    Lecture structurelle de l'identifiant, pas une déduction depuis la date :
    c'est l'AN qui l'y écrit. `None` si l'`uid` ne suit pas la forme connue —
    l'appelant range alors l'amendement dans `LEGISLATURE_INCONNUE` plutôt que
    de lui attribuer une législature par défaut.
    """
    if not isinstance(uid, str):
        return None
    m = _RE_LEGISLATURE_UID.match(uid)
    return m.group(1) if m else None


def legislature_de_id(amendement_id: Any) -> Optional[str]:
    """Législature d'un identifiant pivot `an:<uid>`."""
    return legislature_de_uid(decomposer_id(amendement_id))


def _fichier_meta(dossier: Path, legislature: str) -> Path:
    return Path(dossier) / f"{legislature}.json"


def _fichier_cosignatures(dossier: Path, legislature: str) -> Path:
    return Path(dossier) / f"{legislature}{_SUFFIXE_COSIGNATURES}"


class CosignaturesNonChargees(RuntimeError):
    """Écrire un index chargé sans ses cosignatures les effacerait.

    Levée par `ecrire()` plutôt que de publier silencieusement des fichiers de
    cosignatures vides : le principe de l'épic #429 est « normaliser, jamais
    supprimer », et une perte muette est le contraire d'une normalisation.
    """


class AmendementsIndex:
    """Liste dédupliquée des amendements + leurs cosignatures.

    Deux dictionnaires séparés, exactement comme les deux fichiers : un
    consommateur qui n'a besoin que du `sort` ne paie pas les cosignatures.

    `get()` rend **l'objet partagé**, jamais une copie : c'est la propriété qui
    empêche la re-matérialisation de la forme plate (#377).
    """

    def __init__(
        self,
        amendements: Optional[dict[str, dict[str, Any]]] = None,
        cosignatures: Optional[dict[str, list[str]]] = None,
        *,
        cosignatures_chargees: bool = True,
        textes: Optional[dict[str, dict[str, Any]]] = None,
    ) -> None:
        self.par_id: dict[str, dict[str, Any]] = dict(amendements or {})
        self.par_id_cosignatures: dict[str, list[str]] = dict(cosignatures or {})
        #: `texte_vise` -> `{dossier_id, titre}` (#639). Table de FICHIER, pas
        #: de champ par amendement : 484 132 amendements ne visent que 2 248
        #: textes distincts, et recopier le `dossier_id` dans chacun coûterait
        #: 5,7 Mio de plus là où la table en coûte 0,10. Même raisonnement que
        #: #431 pour les cosignataires, un cran plus loin.
        self.par_texte: dict[str, dict[str, Any]] = dict(textes or {})
        # Distingue « chargé sans les cosignatures » de « chargé, aucun
        # cosignataire ». Sans ce drapeau, `co_signataires()` rendrait `[]` dans
        # les deux cas et un appelant conclurait à tort à une absence de
        # cosignataires.
        self.cosignatures_chargees = bool(cosignatures_chargees)

    def __len__(self) -> int:
        return len(self.par_id)

    def __contains__(self, amendement_id: object) -> bool:
        return amendement_id in self.par_id

    def get(self, amendement_id: Optional[str]) -> Optional[dict[str, Any]]:
        """Amendement d'un identifiant, `None` s'il est inconnu.

        `None` et pas une exception : un profil peut référencer un amendement
        qu'un index partiel ne connaît pas encore. Aux appelants d'en faire une
        donnée manquante — jamais une valeur inventée.

        Rend l'objet stocké, **sans copie** : 810 552 copies d'un
        enregistrement, c'est précisément la forme plate qu'on vient de
        supprimer.
        """
        return self.par_id.get(amendement_id) if amendement_id else None

    def co_signataires(self, amendement_id: Optional[str]) -> Optional[list[str]]:
        """Cosignataires d'un amendement.

        `[]` si l'amendement est connu et n'en a pas ; `None` si l'amendement
        est inconnu **ou** si les cosignatures n'ont pas été chargées — deux
        situations où répondre `[]` serait affirmer une absence non constatée.
        """
        if not self.cosignatures_chargees or not amendement_id:
            return None
        if amendement_id not in self.par_id:
            return None
        return self.par_id_cosignatures.get(amendement_id, [])

    def texte(self, texte_vise: Optional[str]) -> Optional[dict[str, Any]]:
        """Entrée de la table des textes, `None` si le texte n'y est pas.

        Rend l'objet stocké, **sans copie** — même règle que `get()`.
        """
        return self.par_texte.get(texte_vise) if texte_vise else None

    def dossier_de(self, amendement: Optional[dict[str, Any]]) -> Optional[str]:
        """Identifiant de dossier législatif d'un amendement, `None` s'il est
        inconnu.

        `None` couvre trois situations distinctes et volontairement non
        confondues à l'écriture — mais indiscernables ici, faute d'être des
        faits différents pour l'appelant : l'amendement est absent, son
        `texte_vise` est un libellé et non un code (état du corpus d'avant
        #639), ou son code n'est dans aucune archive de dossiers ingérée
        (toute la XIVe législature). Jamais un rattachement par défaut.
        """
        if not isinstance(amendement, dict):
            return None
        entree = self.texte(amendement.get("texte_vise"))
        return entree.get("dossier_id") if isinstance(entree, dict) else None

    def legislatures(self) -> list[str]:
        """Législatures représentées, triées. `LEGISLATURE_INCONNUE` en dernier."""
        vues = {
            legislature_de_id(amendement_id) or LEGISLATURE_INCONNUE
            for amendement_id in self.par_id
        }
        connues = sorted(v for v in vues if v != LEGISLATURE_INCONNUE)
        return connues + ([LEGISLATURE_INCONNUE] if LEGISLATURE_INCONNUE in vues else [])

    def ids_de_legislature(self, legislature: str) -> list[str]:
        """Identifiants d'une législature, triés — ordre stable d'un run à
        l'autre, pour que git ne voie que les vraies différences."""
        return sorted(
            amendement_id
            for amendement_id in self.par_id
            if (legislature_de_id(amendement_id) or LEGISLATURE_INCONNUE) == legislature
        )


def joindre(
    mapping: Optional[Iterable[dict[str, Any]]], index: Optional[AmendementsIndex]
) -> Iterator[tuple[dict[str, Any], Optional[dict[str, Any]]]]:
    """Itère `(entrée du mapping, amendement partagé)` — **un générateur**.

    C'est le seul chemin de lecture offert aux consommateurs, et il est
    volontairement paresseux : rendre une liste de 810 552 enregistrements
    joints reconstruirait exactement la forme plate que #431 supprime, avec le
    facteur ~21 et l'OOM de #377. `tests/test_amendements_index.py` verrouille
    à la fois la paresse et l'identité (`is`) de l'objet rendu.

    L'amendement vaut `None` quand l'index ne le connaît pas (index partiel) ou
    quand l'entrée n'a pas d'identifiant. L'appelant en fait une donnée
    manquante **comptée**, jamais une exclusion muette (AGENTS.md §2.7).
    """
    for entree in (mapping or ()):
        if not isinstance(entree, dict):
            continue
        amendement_id = entree.get("amendement_id")
        yield entree, (index.get(amendement_id) if index is not None else None)


def _valeur_amendement(champ: str, brut: dict[str, Any], courant: Any) -> Any:
    """Valeur partagée d'un champ, en lisant indifféremment un amendement brut
    ou une entrée pivot d'avant #431.

    Un seul champ demande un arbitrage : `premier_signataire`.
    `normalize_profil._normalize_amendement` le réécrivait à l'identifiant
    pivot du profil courant quand celui-ci était l'auteur — c'est la **seule**
    divergence entre les copies d'un même amendement (44 139 cas sur 207 238
    amendements distincts ; les 8 autres champs et `co_signataires` sont
    strictement identiques sur les 810 552 paires, mesuré le 19/08/2026).

    Une valeur propre au profil lecteur n'a rien à faire dans une liste
    partagée : on retient la référence AN (`an:PA…`), qui est celle que la
    collecte produit et la seule indépendante du lecteur. L'information n'est
    pas perdue pour autant : `role_signataire`, resté dans le mapping, dit déjà
    que le membre est l'auteur principal.
    """
    valeur = brut.get(champ)
    if champ == "premier_signataire":
        if isinstance(valeur, str) and valeur.startswith(f"{SOURCE_AN}:"):
            return valeur
        return courant if courant is not None else valeur
    return valeur if valeur is not None else courant


def construire_index(amendements: Iterable[dict[str, Any]]) -> AmendementsIndex:
    """Construit l'index à partir d'un **flux** d'amendements plats.

    Un flux, et une seule passe : accumuler les profils pour les reparcourir
    coûterait 1,5 Go de JSON et se ferait tuer par l'OOM killer — le mode
    d'échec de #377 et #392, puis de la première version de
    `scrutins_index.construire_index`. Ici seuls les 207 238 amendements
    distincts sont retenus, jamais les 810 552 paires.

    Les chaînes sont **internées** : les 4,96 M références de cosignataires ne
    portent que quelques milliers de valeurs distinctes, et les `texte_vise`
    1 976. Sans internement, la construction pèse plusieurs Go ; avec, elle
    tient en ~330 Mio de RSS sur le corpus complet.
    """
    par_id: dict[str, dict[str, Any]] = {}
    cosignatures: dict[str, list[str]] = {}
    intern = sys.intern

    for brut in amendements:
        if not isinstance(brut, dict):
            continue
        amendement_id = cle_amendement(brut.get("uid"))
        if amendement_id is None:
            # Sans `uid`, pas de clé : l'enregistrement reste côté profil, dans
            # `amendement_non_resolu`. Ni supprimé, ni doté d'une clé inventée.
            continue
        amendement_id = intern(amendement_id)
        courant = par_id.get(amendement_id)
        if courant is None:
            courant = {}
            par_id[amendement_id] = courant
        liste_cosign = brut.get("co_signataires")
        if isinstance(liste_cosign, list) and liste_cosign:
            # Chaque copie plate porte la liste COMPLÈTE des cosignataires (0
            # divergence mesurée sur les 810 552 paires) : la dernière vue vaut
            # la première. Une liste vide, elle, ne remplace jamais une liste
            # renseignée — ce serait une régression vers l'absence.
            cosignatures[amendement_id] = [
                intern(ref) for ref in liste_cosign if isinstance(ref, str)
            ]
        for champ in CHAMPS_AMENDEMENT:
            valeur = _valeur_amendement(champ, brut, courant.get(champ))
            courant[champ] = intern(valeur) if isinstance(valeur, str) else valeur

    return AmendementsIndex(par_id, cosignatures)


#: Champ que le report de #696 rétablit, nommé en **un seul endroit** —
#: reporter tout ce qui paraît fautif ferait de la fusion additive une fusion
#: champ par champ, ce qu'elle n'est pas (même règle que
#: `CHAMPS_QUALIFICATION_VOTE` de #639 et `CHAMPS_QUALIFICATION_DOSSIER` de
#: #689, qui sont des tuples parce qu'ils portent plusieurs champs ; ici il n'y
#: en a qu'un, et un tuple d'un élément se lirait comme une invitation à en
#: ajouter).
CHAMP_REPORT_TEXTE_VISE = "texte_vise"

#: Lecteur de la valeur sourcée : `(législature, uid d'amendement) -> {uid:
#: texte_vise}`. Injecté plutôt qu'importé, exactement comme `table_textes` de
#: #639 : `backfill_texte_vise` ne doit connaître ni le disque, ni le format des
#: archives figées — c'est ce qui le rend testable sans que rien ne lise
#: `raw_data/` (AGENTS.md §3b).
LecteurTextesVises = Callable[[str, set[str]], dict[str, str]]


def backfill_texte_vise(
    index: AmendementsIndex,
    lire: Optional[LecteurTextesVises],
) -> dict[str, int]:
    """Rétablit le `texte_vise` sourcé des entrées qui n'en portent pas un (#696).

    **Le maillon où la correction de #639 n'arrivait pas.** #639 a corrigé la
    collecte, qui écrasait le code du document amendé par le titre du dossier.
    Mais l'index publié est fusionné additivement avec le précédent, et
    `merge_amendements_index` laisse gagner « la nouvelle valeur si elle est
    renseignée » : un intitulé **est** renseigné. Une entrée écrite avant #639
    gardait donc son intitulé à chaque reconstruction — et, mesuré le
    01/09/2026, un amendement dont trois profils bruts portent le code correct
    (`an:AMANR5L15PO59051B4857P0D1N000045`) était **malgré tout** publié avec
    l'intitulé, parce que le quatrième signataire l'emporte par l'ordre des
    fichiers. La fusion ne se contentait pas de conserver le défaut, elle
    pouvait le réintroduire.

    Strictement monotone. Ne touche **que** les entrées dont le `texte_vise`
    n'est pas un uid de document AN (`est_uid_texte`), ne substitue **que** des
    valeurs qui en sont un, n'écrase jamais un uid déjà en place, ne vide rien,
    ne touche aucun autre champ, ne crée ni ne supprime aucune entrée, et ne
    réordonne rien.

    **La clé de fusion ne change pas** : `amendement_id` reste `an:<uid AN>`.
    L'élargir pour y porter le texte visé serait le défaut de #668 — 468
    doublons sur 940 entrées de `textes_portes`.

    Ce que ce report ne peut pas faire : réparer un amendement dont l'archive
    figée n'a pas non plus l'uid, et réparer une législature qui n'a pas
    d'archive figée (la XVIIe, en cours). Les deux sont **comptés et nommés**
    dans le relevé rendu, jamais comblés par une seconde source silencieuse.

    Retourne le relevé, pour que l'appelant le publie plutôt que de le taire :
    `entrees_a_reparer`, `entrees_sans_texte_vise`, `entrees_corrigees`,
    `entrees_sans_source`, `legislatures_lues`, `legislatures_sans_source`.
    """
    releve = {
        "entrees_a_reparer": 0,
        "entrees_sans_texte_vise": 0,
        "entrees_corrigees": 0,
        "entrees_sans_source": 0,
        "legislatures_lues": 0,
        "legislatures_sans_source": 0,
    }

    # Relève d'abord, lit ensuite : l'archive d'une législature sans entrée
    # fautive n'est jamais ouverte, et le coût du report est nul sur un index
    # sain (610 Mio de RSS évités par législature, mesuré).
    a_reparer: dict[str, dict[str, str]] = {}
    for amendement_id, amendement in index.par_id.items():
        valeur = amendement.get(CHAMP_REPORT_TEXTE_VISE)
        if est_uid_texte(valeur):
            continue
        releve["entrees_a_reparer"] += 1
        if valeur is None or valeur == "":
            releve["entrees_sans_texte_vise"] += 1
        uid = decomposer_id(amendement_id)
        if uid is None:
            # Pas d'uid AN : rien à relire dans une archive keyée par uid.
            releve["entrees_sans_source"] += 1
            continue
        legislature = legislature_de_uid(uid) or LEGISLATURE_INCONNUE
        a_reparer.setdefault(legislature, {})[uid] = amendement_id

    if not a_reparer:
        return releve
    if lire is None:
        # Aucun lecteur déclaré : rien n'est relu, rien n'est perdu, et le
        # compte le dit — même convention que `table_textes=None` (#639).
        releve["entrees_sans_source"] += sum(len(v) for v in a_reparer.values())
        releve["legislatures_sans_source"] += len(a_reparer)
        return releve

    for legislature, par_uid in sorted(a_reparer.items()):
        sources = lire(legislature, set(par_uid)) or {}
        if sources:
            releve["legislatures_lues"] += 1
        else:
            releve["legislatures_sans_source"] += 1
        for uid, amendement_id in par_uid.items():
            sourcee = sources.get(uid)
            if not est_uid_texte(sourcee):
                releve["entrees_sans_source"] += 1
                continue
            index.par_id[amendement_id][CHAMP_REPORT_TEXTE_VISE] = sys.intern(sourcee)
            releve["entrees_corrigees"] += 1

    return releve


def resoudre_textes(
    index: AmendementsIndex, table: dict[str, dict[str, Any]]
) -> dict[str, int]:
    """Renseigne `index.par_texte` pour les textes que l'index référence.

    `table` est celle de `textes_dossiers_an.charger_table()` : uid de document
    AN -> `{dossier_id, titre}`, construite d'identifiant à identifiant depuis
    les archives de dossiers.

    **Additif, jamais destructeur** : une table vide (archives indisponibles) ne
    retire rien de ce qui est déjà publié — c'est la règle « une collecte vide
    n'écrase jamais » appliquée à un index dérivé.

    Ne retient que les textes réellement visés par un amendement de l'index :
    écrire les 21 936 documents des archives dans chaque fichier de législature
    y ajouterait 20 000 entrées que personne ne référence.

    Retourne le compte, pour que l'appelant le publie plutôt que de le taire :
    `textes_resolus`, `textes_sans_dossier`, `amendements_rattaches`,
    `amendements_sans_dossier`.
    """
    resolus = 0
    sans_dossier = 0
    rattaches = 0
    orphelins = 0
    intern = sys.intern
    vus: dict[str, bool] = {}

    for amendement in index.par_id.values():
        texte_vise = amendement.get("texte_vise")
        if not isinstance(texte_vise, str) or not texte_vise:
            orphelins += 1
            continue
        connu = vus.get(texte_vise)
        if connu is None:
            entree = table.get(texte_vise)
            connu = isinstance(entree, dict) and bool(entree.get("dossier_id"))
            if connu:
                index.par_texte[intern(texte_vise)] = {
                    "dossier_id": intern(str(entree["dossier_id"])),
                    "titre": entree.get("titre"),
                }
                resolus += 1
            elif texte_vise not in index.par_texte:
                sans_dossier += 1
            else:
                # Déjà rattaché par un run précédent : la table de ce run-ci ne
                # le connaît pas (archive absente), on garde l'acquis.
                connu = True
            vus[texte_vise] = connu
        if connu:
            rattaches += 1
        else:
            orphelins += 1

    return {
        "textes_resolus": resolus,
        "textes_sans_dossier": sans_dossier,
        "amendements_rattaches": rattaches,
        "amendements_sans_dossier": orphelins,
    }


def merge_amendements_index(
    ancien: AmendementsIndex, nouveau: AmendementsIndex
) -> AmendementsIndex:
    """Fusion additive de deux index : jamais une suppression.

    Un run qui ne régénère qu'une tranche de profils ne voit qu'une partie des
    amendements. Écraser l'index par ce qu'il vient de voir effacerait ceux des
    profils non retraités, et leurs mappings pointeraient dans le vide — la
    panne exacte que #450 a traitée à l'échelle des profils, transposée à
    l'index comme elle l'a été pour les scrutins.

    Sur les champs, la nouvelle valeur gagne si elle est renseignée, sinon
    l'ancienne est conservée (jamais de régression vers `null`) — même règle que
    `merge_dossier_records`, qui pour les amendements laisse la nouvelle entrée
    gagner afin de permettre une correction de sort.

    Sur les cosignatures, la nouvelle liste gagne dès que l'amendement est
    présent dans le nouvel index : chaque copie plate porte la liste **complète**
    (0 divergence mesurée sur 810 552 paires), donc une liste vue par un run
    partiel n'est jamais une liste tronquée. Une liste absente du nouvel index
    ne touche pas l'ancienne.
    """
    if ancien.cosignatures_chargees and nouveau.cosignatures_chargees:
        cosignatures_chargees = True
    else:
        # Fusionner un index amputé de ses cosignatures produirait un index
        # amputé : on le dit plutôt que de le publier.
        cosignatures_chargees = False

    fusionnes: dict[str, dict[str, Any]] = {k: dict(v) for k, v in ancien.par_id.items()}
    for amendement_id, amendement in nouveau.par_id.items():
        existant = fusionnes.get(amendement_id)
        if existant is None:
            fusionnes[amendement_id] = dict(amendement)
            continue
        for champ, valeur in amendement.items():
            if valeur is not None:
                existant[champ] = valeur

    cosignatures = dict(ancien.par_id_cosignatures)
    if nouveau.cosignatures_chargees:
        for amendement_id in nouveau.par_id:
            liste = nouveau.par_id_cosignatures.get(amendement_id)
            if liste:
                cosignatures[amendement_id] = list(liste)

    # Union additive des tables de textes : la nouvelle entrée gagne si elle
    # est renseignée, l'ancienne survit sinon. Un run partiel ne voit qu'une
    # partie des textes ; effacer les autres laisserait des amendements publiés
    # sans dossier alors que leur rattachement était acquis.
    textes = dict(ancien.par_texte)
    for texte_vise, entree in nouveau.par_texte.items():
        if isinstance(entree, dict) and entree.get("dossier_id"):
            textes[texte_vise] = dict(entree)

    return AmendementsIndex(
        fusionnes,
        cosignatures,
        cosignatures_chargees=cosignatures_chargees,
        textes=textes,
    )


def charger(
    dossier: Path = DEFAULT_AMENDEMENTS_DIR,
    *,
    legislatures: Optional[Iterable[str]] = None,
    avec_cosignatures: bool = True,
) -> AmendementsIndex:
    """Charge l'index depuis son dossier. Index vide si le dossier est absent —
    un premier run n'a rien à charger.

    `legislatures` restreint la lecture aux fichiers utiles : un consommateur
    qui n'affiche qu'un profil de la XVIIe n'a aucune raison de charger les
    trois autres législatures.

    `avec_cosignatures=False` économise 59 % du volume, et c'est ce que font
    tous les consommateurs actuels — aucun ne lit `co_signataires`. Le défaut
    reste `True` : lire partiellement puis réécrire effacerait les cosignatures,
    et `ecrire()` refuse d'ailleurs de le faire.
    """
    dossier = Path(dossier)
    par_id: dict[str, dict[str, Any]] = {}
    cosignatures: dict[str, list[str]] = {}
    if not dossier.is_dir():
        return AmendementsIndex(cosignatures_chargees=avec_cosignatures)

    textes: dict[str, dict[str, Any]] = {}
    demandees = set(legislatures) if legislatures is not None else None
    for chemin in sorted(dossier.glob("*.json")):
        if chemin.name.endswith(_SUFFIXE_COSIGNATURES):
            continue
        legislature = chemin.stem
        if demandees is not None and legislature not in demandees:
            continue
        donnees = _lire_json(chemin)
        for amendement_id, amendement in (donnees.get("amendements") or {}).items():
            if isinstance(amendement, dict):
                par_id[amendement_id] = amendement
        # La table des textes est portée par chaque fichier, restreinte aux
        # textes que ses amendements visent : un même texte peut donc figurer
        # dans deux fichiers, avec la même valeur (l'uid du dossier est unique).
        for texte_vise, entree in (donnees.get("textes") or {}).items():
            if isinstance(entree, dict):
                textes[texte_vise] = entree
        if not avec_cosignatures:
            continue
        chemin_cosign = _fichier_cosignatures(dossier, legislature)
        if not chemin_cosign.exists():
            continue
        donnees_cosign = _lire_json(chemin_cosign)
        for amendement_id, refs in (donnees_cosign.get("co_signataires") or {}).items():
            if isinstance(refs, list):
                cosignatures[amendement_id] = refs

    return AmendementsIndex(
        par_id, cosignatures, cosignatures_chargees=avec_cosignatures, textes=textes
    )


def _lire_json(chemin: Path) -> dict[str, Any]:
    try:
        with open(chemin, encoding="utf-8") as f:
            donnees = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  [!] Lecture impossible de {chemin}, ignoré : {exc}")
        return {}
    return donnees if isinstance(donnees, dict) else {}


def ecrire(
    dossier: Path,
    index: AmendementsIndex,
    *,
    genere_le: Optional[str] = None,
) -> list[Path]:
    """Écrit un fichier de méta et un fichier de cosignatures **par
    législature**, en JSON compact (#433).

    Le découpage n'est pas cosmétique : un fichier global unique pèse 128,8 Mo
    sur les seuls profils actuels, au-delà de la limite GitHub de 100 Mo par
    blob. Voir docs/decisions/normalisation-amendements.md.

    Les amendements sont stockés **en dictionnaire** `{id: amendement}` et non
    en liste d'objets portant leur `id` (choix inverse de `scrutins-v1`) : à
    207 238 entrées, la liste imposerait à chaque consommateur une passe de
    réindexation, et l'`id` répété en clé de champ coûterait 1 Mo de plus. Le
    même choix a été fait pour les index figés de `raw_data/amendements_an_figes/`.

    La `legislature` est portée **une fois par fichier**, jamais par entrée :
    toutes les entrées d'un fichier ont la même, et la répéter coûterait 4 Mo.

    Même raison pour la table `textes` (#639) : le `dossier_id` recopié dans
    chaque amendement coûterait 5,7 Mio sur les quatre fichiers, la table 0,10.
    Elle est restreinte aux textes que le fichier vise réellement, pour qu'un
    fichier de législature se lise seul.
    """
    if not index.cosignatures_chargees:
        raise CosignaturesNonChargees(
            "Index chargé sans ses cosignatures : l'écrire les effacerait. "
            "Recharger avec avec_cosignatures=True avant toute écriture."
        )
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    ecrits: list[Path] = []
    for legislature in index.legislatures():
        ids = index.ids_de_legislature(legislature)
        chemin = _fichier_meta(dossier, legislature)
        # Table des textes restreinte à ceux que CE fichier vise (#639) : un
        # fichier doit se lire seul, et recopier les 21 936 documents des
        # archives dans chacun coûterait sans rien rattacher de plus.
        vises = {index.par_id[i].get("texte_vise") for i in ids}
        textes = {
            texte_vise: index.par_texte[texte_vise]
            for texte_vise in sorted(v for v in vises if isinstance(v, str) and v)
            if texte_vise in index.par_texte
        }
        ecrire_profil_json(chemin, {
            "schema_version": SCHEMA_VERSION,
            "legislature": legislature,
            "genere_le": genere_le,
            "licence_donnees": LICENCE_DONNEES,
            # `textes` avant `amendements` : un fichier de 51 Mio se lit en
            # streaming, et la table doit être atteignable sans traverser les
            # 206 771 entrées qui la référencent.
            "textes": textes,
            "amendements": {i: index.par_id[i] for i in ids},
        })
        ecrits.append(chemin)

        chemin_cosign = _fichier_cosignatures(dossier, legislature)
        ecrire_profil_json(chemin_cosign, {
            "schema_version": COSIGNATURES_SCHEMA_VERSION,
            "legislature": legislature,
            "genere_le": genere_le,
            "licence_donnees": LICENCE_DONNEES,
            # Les amendements sans cosignataire sont absents : leur écrire une
            # liste vide coûterait sans rien dire de plus. `co_signataires()`
            # rend `[]` pour un amendement connu et absent d'ici, `None` pour un
            # amendement inconnu — l'absence de cosignataire et l'absence
            # d'amendement ne se confondent pas.
            "co_signataires": {
                i: index.par_id_cosignatures[i]
                for i in ids
                if index.par_id_cosignatures.get(i)
            },
        })
        ecrits.append(chemin_cosign)
    return ecrits


def iter_amendements_du_repertoire(profils_dir: Path) -> Iterator[dict[str, Any]]:
    """Itère les amendements de tous les profils d'un répertoire, **une tranche
    de législature à la fois** (#580).

    Le profil est relâché avant d'ouvrir le suivant : `raw_data/profiles` pèse
    7,5 Go, et le charger d'un bloc fait tuer le process par l'OOM killer (#377,
    #392). Depuis la partition par législature, le pic n'est même plus le profil
    entier (56 Mo) mais sa plus grosse tranche (23,4 Mo) — `profil_brut` les
    ouvre l'une après l'autre. La forme monolithique reste lue telle quelle,
    au même pic qu'avant : les deux cohabitent tant que le dépôt n'est pas migré.

    Un fichier illisible est signalé et sauté — il ne doit pas priver l'index
    des amendements de tous les autres.
    """
    if not Path(profils_dir).is_dir():
        return
    for chemin in sorted(Path(profils_dir).glob("*.json")):
        if chemin.name.startswith("."):
            continue
        try:
            yield from iter_amendements_du_profil(chemin)
        except (json.JSONDecodeError, OSError, RuntimeError) as exc:
            print(f"  [!] Lecture impossible de {chemin}, ignoré : {exc}")
            continue


def rafraichir(
    profils_dir: Path,
    dossier: Path = DEFAULT_AMENDEMENTS_DIR,
    *,
    fusionner: bool = True,
    genere_le: Optional[str] = None,
    table_textes: Optional[dict[str, dict[str, Any]]] = None,
    lire_textes_vises: Optional[LecteurTextesVises] = None,
    comptes: Optional[dict[str, int]] = None,
) -> AmendementsIndex:
    """Reconstruit l'index depuis `profils_dir` et l'écrit, en fusionnant avec
    l'existant par défaut.

    `fusionner=True` est le défaut **et le mode sûr** : un run qui ne régénère
    qu'une tranche de profils ne voit qu'une partie des amendements, et écraser
    l'index laisserait les mappings des profils non retraités pointer dans le
    vide (leçon de #450, transposée à l'index).

    `fusionner=False` correspond à `--no-merge` : reconstruction complète, à
    n'utiliser que sur un corpus complet.

    `table_textes` (#639) est la table `texte AN -> dossier législatif` de
    `textes_dossiers_an.charger_table()`. `None` (le défaut) laisse l'index tel
    quel : les rattachements déjà publiés sont conservés, aucun n'est ajouté —
    un run sans archives de dossiers ne perd rien et n'invente rien.

    `lire_textes_vises` (#696) est le lecteur des archives figées de
    `textes_vises_figes.lire_textes_vises`. `None` (le défaut) suit la même
    convention : aucun `texte_vise` n'est relu, aucun n'est perdu, et le relevé
    de `backfill_texte_vise` le dit.
    """
    index = construire_index(iter_amendements_du_repertoire(profils_dir))
    if fusionner:
        index = merge_amendements_index(charger(dossier), index)
    # Report AVANT la résolution des dossiers (#696) : un `texte_vise` réparé
    # doit gagner son dossier dans le MÊME run, sinon la correction ne se voit
    # qu'à la reconstruction suivante. Et après la fusion, pour la raison qui
    # vaut pour la résolution : la fusion peut réintroduire un intitulé sur une
    # entrée qu'un profil brut portait correctement.
    releve_textes_vises = backfill_texte_vise(index, lire_textes_vises)
    if comptes is not None:
        comptes.update(releve_textes_vises)
    # Résolution APRÈS la fusion : les amendements des profils non retraités
    # sont déjà là, et ils ont autant droit à leur dossier que les nouveaux.
    if table_textes is not None:
        releve = resoudre_textes(index, table_textes)
        if comptes is not None:
            comptes.update(releve)
    ecrire(dossier, index, genere_le=genere_le)
    return index
