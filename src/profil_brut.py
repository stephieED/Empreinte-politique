#!/usr/bin/env python3
"""profil_brut.py — Lecture/écriture d'un profil brut PARTITIONNÉ par
législature (#580, sous-issue de l'épic volumétrie #429).

Les trois décisions à lire avant de toucher ce module :

- `docs/decisions/partition-profils-legislature-580.md` — pourquoi un profil
  n'est plus un fichier, et pourquoi une tranche annoncée et absente **lève**
  au lieu de rendre une liste vide ;
- `docs/decisions/reconstruction-tranches-depuis-archive-691.md` — une tranche
  de législature close se reconstruit **exactement** depuis
  `raw_data/amendements_an_figes/` (120 profils, 568 771 amendements, zéro
  écart) ;
- `docs/decisions/tranches-derivees-lecteur-691.md` — d'où la marque `derivee`
  du manifeste, et la règle qui la gouverne : **le manifeste doit le dire, et
  le silence reste une panne**.

Le problème, mesuré le 29/08/2026
---------------------------------
`amendements` fait **96,7 % du plus gros profil brut** — 54,15 Mo sur 56,00.
Huit profils dépassent 50 Mo, et **cinquante-quatre** dépassent 45 : les mêmes
députés cosignent les mêmes amendements, donc ils franchissent la ligne *en
bloc* à chaque correction de collecte. La marge jusqu'à la limite dure de
GitHub (100 Mo, un push refusé) n'est que de **× 1,79**, et l'achèvement des
archives figées — × 1,5 restant sur la XV, × 1,3 sur la XVI — la consommerait.

Ce que fait ce module, et ce qu'il ne fait PAS
----------------------------------------------
Il **partitionne un fichier sur un champ déjà présent**. Chaque amendement
porte son `legislature` depuis la collecte ; on écrit une tranche par valeur.

Ce n'est **pas** la normalisation écartée par #434. Celle-là déduplique les
cosignatures et transforme la donnée. Ici :

  - aucun champ n'est retiré, réécrit ni dédupliqué ;
  - `raw_data/profiles` reste la couche *source-near*, aux mêmes octets près ;
  - `recomposer(partitionner(p)) == p`, **liste d'amendements dans son ordre
    d'origine comprise** — c'est ce que verrouille
    `tests/test_profil_brut_partition_580.py`.

Disposition
-----------
::

    raw_data/profiles/
    ├── mathilde-panot.json          ← le socle : le profil SAUF `amendements`
    └── mathilde-panot/              ← les tranches, un fichier par législature
        ├── 15.json
        ├── 16.json
        └── 17.json

Pourquoi cette disposition plutôt qu'un répertoire par profil
(`mathilde-panot/profil.json` + `mathilde-panot/amendements-15.json`) :

1. **Le slug reste énumérable au même endroit.** Les quinze `glob("*.json")`
   du dépôt qui listent les profils bruts continuent de rendre exactement les
   481 mêmes noms — `glob` n'est pas récursif, et le répertoire de tranches
   n'est pas un `.json`. Un répertoire par profil aurait fait rendre **zéro**
   à chacun de ces appels : une population vide, donc un audit qui conclut
   « aucun écart » sans avoir rien rapproché (AGENTS.md §2.5).
2. **La découvrabilité humaine.** Qui parcourt `raw_data/profiles/` voit la
   même liste de personnes qu'avant, et à côté de chaque nom un répertoire du
   même nom dont le contenu se lit sans documentation : `16.json`, ce sont les
   amendements de la 16e législature.
3. **Le socle reste un document autonome et complet** pour tout ce qui n'est
   pas amendement — identité, mandats, votes, interventions. Il pèse 1,85 Mo
   là où le profil monolithique en pesait 56 : `iter_votes_du_repertoire`
   lisait 7,5 Go pour n'y chercher que des votes, il en lira ~0,9.

Absent, jamais vide
-------------------
Le socle **omet** la clé `amendements` ; il ne la met pas à `[]`. C'est la
règle §2.5 du dépôt appliquée à la partition : une donnée absente est absente,
jamais un `0` mesuré. Un lecteur qui n'aurait pas été adapté lit donc « pas de
clé », et le manifeste `amendements_partitionnes` lui dit où elle est passée.

Le filet qui rend un tel lecteur VISIBLE est déjà en place et n'a pas eu à
être inventé : `audit_collecte_vs_publie.py` compare, liste par liste, ce que
`raw_data/profiles` porte et ce que `pivot_data/profiles` publie, et **annule
le commit** dès qu'une liste publiée est en déficit. Il est adapté ici pour
compter les tranches ; à partir de là, tout lecteur oublié en aval se déclare
de lui-même en CI, avec le slug et les deux comptes.

Transition
----------
La bascule n'est **pas** atomique — elle ne peut pas l'être : l'ancienne forme
monolithique est committée dans le dépôt, et la migration des 481 profils est
une réécriture de ~600 Mo qui se décide, pas qui se glisse dans une PR de
code. **Tous les lecteurs acceptent donc les deux formes**, et c'est le sens
de `charger_profil_brut` : un fichier monolithique se lit tel quel, un socle se
recompose depuis ses tranches. L'écriture, elle, ne produit plus que la forme
partitionnée — un profil relu puis réécrit migre de lui-même, sans perdre
d'octet.
"""

import json
import re
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from json_io import ecrire_profil_json

#: Version du manifeste posé dans le socle. Un lecteur qui rencontre une
#: version qu'il ne connaît pas doit refuser bruyamment plutôt que rendre une
#: liste vide.
SCHEMA_PARTITION = "profil-brut-partitionne-v1"

#: Version portée par chaque tranche. Une tranche est un document autonome :
#: elle se lit et se comprend sans le socle.
SCHEMA_TRANCHE = "profil-brut-amendements-v1"

#: Clé du manifeste dans le socle. Elle prend la place de `amendements`, qui
#: est **retirée** du socle (absent ≠ vide).
CLE_MANIFESTE = "amendements_partitionnes"

#: La clé partitionnée. Une seule aujourd'hui : elle fait 96,7 % du poids, et
#: `votes` — le deuxième — n'en fait que 3,3 % (1,83 Mo sur 56,00). Découper
#: `votes` coûterait la même complexité pour un trentième du gain.
CLE_PARTITIONNEE = "amendements"

#: Nom de la tranche des amendements dont `legislature` est absent ou vide.
#: Ils ne sont **pas** rangés d'office dans une législature : c'est une donnée
#: manquante, elle reste manquante et visible sous ce nom.
NOM_SANS_LEGISLATURE = "sans-legislature"

#: Un nom de tranche sûr : ni séparateur de chemin, ni `..`, ni nom caché.
_NOM_SUR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")

#: Marque d'une tranche **dérivée** : le manifeste la déclare sans fichier, et
#: elle se relit dans `raw_data/amendements_an_figes/` (#691).
#:
#: POURQUOI UNE MARQUE, ET PAS UNE DEVINETTE. Une tranche absente d'un profil
#: dont le manifeste l'annonce est aujourd'hui une **panne**
#: (`PartitionIllisible`), et c'est ce qui protège d'un profil republié amputé.
#: Aller chercher l'archive « au cas où le fichier manquerait » effacerait
#: cette distinction : une tranche perdue se lirait comme une tranche dérivée.
#: Le manifeste doit donc le DIRE, et le silence reste une panne.
CLE_TRANCHE_DERIVEE = "derivee"

#: L'acteur dont la tranche se dérive. Porté par le manifeste lui-même, et non
#: résolu par une jointure : `profil_brut` ne connaît pas
#: `raw_data/correspondance_acteurs_an.json` et n'a pas à l'apprendre pour
#: relire un profil.
CLE_ACTEUR_TRANCHE = "acteur_ref"


class PartitionIllisible(RuntimeError):
    """Le socle annonce des tranches qui manquent, sont illisibles ou ne
    portent pas le compte annoncé.

    Levée plutôt que rendue en liste vide : un profil dont les amendements ne
    se relisent pas est un profil qu'on ne doit **pas** republier amputé.
    """


# ---------------------------------------------------------------------------
# Un artifact = les CHAMPS qu'un job a collectés (#997, après #450)
# ---------------------------------------------------------------------------
#
# #450 a rétabli « un artifact = les SLUGS d'un job » : un job ne publie plus
# que les profils qu'il a écrits. Il restait l'autre moitié, et elle a coûté un
# run : un job publie le profil **entier**, donc tous les champs qu'il n'a pas
# collectés, recopiés de la baseline de son checkout.
#
# Mesuré le 19/09/2026 sur le run 35430469408, artifact contre baseline : la
# contribution réelle de ces deux jobs est **un seul champ**.
#
#     extract-mandats-locaux   `mandats_locaux`      33 profils
#     extract-senat            `mandat_senatorial`    2 profils
#
# Tout le reste — `dossiers_legislatifs`, `votes`, `interventions` — partait
# avec, figé au run précédent. Tant que `merge_raw_profile` fusionnait
# `dossiers_legislatifs[]` en additif pur, cette copie périmée ne pouvait rien
# écraser. Depuis que la neuve gagne (#997), **la dernière source l'emporte** :
# `_artifacts/mandats-locaux` est la dernière de `--dirs`, et il a reposé les
# vieux stades sur les 17 candidats déclarés qui portent des textes portés,
# après que l'extraction AN eut publié les bons (Édouard Philippe : 9 en
# artifact, 127 committés).
#
# → `docs/decisions/contribution-par-champs-997.md`

#: Ce qu'une contribution garde toujours, quels que soient les champs déclarés :
#: `slug` est la clé de `merge_raw_dirs`, et sans lui le fichier n'identifie rien.
CHAMPS_IDENTIFIANTS_CONTRIBUTION: tuple[str, ...] = ("slug",)

#: Marque une contribution réduite, et porte les champs qu'elle déclare.
#:
#: **Sans ce marqueur, une contribution réduite est indistinguable d'un profil
#: qui aurait tout perdu.** `merge_raw_dirs` écrit l'union des SOURCES et
#: `ecrire_profil_brut` écrase : un slug dont SEUL un job d'enrichissement
#: parle — parce que son extraction complète a échoué, `continue-on-error`
#: étant la règle — serait republié amputé de tout le reste.
#:
#: La baseline ne peut pas servir de filet ici : la remettre en première source
#: réinjecte ce que #450 a supprimé, et `test_publication_scopee_laisse_aboutir_la_correction_de_cle`
#: le fait tomber — une correction de clé d'amendement cesse d'aboutir.
#: Le marqueur fait donc l'inverse : une contribution réduite seule ne réécrit
#: RIEN, et le profil committé reste, comme pour un slug qu'aucun job n'a
#: touché (#450). L'apport du run est perdu, il est **dit**, et le run suivant
#: le reprend.
CLE_CONTRIBUTION_PARTIELLE = "contribution_partielle"


def projeter_contribution(profil: dict[str, Any], champs: Iterable[str]) -> dict[str, Any]:
    """Le profil réduit aux champs que le job déclare avoir collectés.

    Ce que la fusion fait du reste est déjà écrit et n'a pas à changer : un
    champ absent d'une contribution laisse en place celui de la source
    précédente (`_prefer_non_empty`, `CHAMPS_PROTEGES_DU_VIDE`). C'est la
    fusion additive telle qu'elle a toujours été décrite — elle n'avait
    simplement jamais reçu de contribution partielle.

    **Le manifeste de partition part avec les amendements.** `charger_profil_brut`
    refuse, bruyamment, un socle qui annonce une tranche absente : une
    contribution qui ne porte pas `amendements` ne doit pas porter le manifeste
    qui les annonce, sans quoi elle serait illisible plutôt que partielle.
    """
    declares = sorted(set(champs))
    gardes = set(declares) | set(CHAMPS_IDENTIFIANTS_CONTRIBUTION)
    projete = {c: v for c, v in profil.items() if c in gardes}
    if CLE_PARTITIONNEE not in gardes:
        projete.pop(CLE_MANIFESTE, None)
    projete[CLE_CONTRIBUTION_PARTIELLE] = declares
    return projete


# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

def chemin_socle(profils_dir: Path, slug: str) -> Path:
    """`raw_data/profiles/<slug>.json` — le fichier qui porte le slug."""
    return Path(profils_dir) / f"{slug}.json"


def dossier_tranches(profils_dir: Path, slug: str) -> Path:
    """`raw_data/profiles/<slug>/` — le répertoire frère du socle."""
    return Path(profils_dir) / slug


def dossier_tranches_du_socle(chemin: Path) -> Path:
    """Répertoire de tranches associé à un chemin de socle."""
    chemin = Path(chemin)
    return chemin.parent / chemin.name[: -len(".json")]


def nom_tranche(legislature: Any) -> str:
    """Nom de fichier d'une tranche, à partir d'une valeur de `legislature`.

    Le nom est **indicatif** : c'est le manifeste qui fait foi côté lecture,
    jamais une dérivation refaite depuis la valeur. Cette fonction n'a donc
    qu'un travail, produire un nom lisible et sûr ; une valeur exotique tombe
    sur un nom neutre, et le manifeste garde la valeur exacte.
    """
    if legislature is None:
        return NOM_SANS_LEGISLATURE
    texte = str(legislature).strip()
    if not texte:
        return NOM_SANS_LEGISLATURE
    if _NOM_SUR.match(texte):
        return texte
    assaini = re.sub(r"[^A-Za-z0-9_-]", "_", texte).strip("_-")
    return f"legislature-{assaini}" if assaini else NOM_SANS_LEGISLATURE


# ---------------------------------------------------------------------------
# Découpe / recomposition — fonctions pures, sans I/O
# ---------------------------------------------------------------------------

def _sequence(valeurs: Iterable[Any]) -> list[list[Any]]:
    """Codage par plages de la suite des tranches d'origine.

    `[0, 0, 0, 1, 1, 0]` → `[[0, 3], [1, 2], [0, 1]]`.

    C'est ce qui rend la recomposition **exacte pour n'importe quel ordre**, et
    pas seulement pour un profil dont les amendements seraient déjà groupés par
    législature. Sur le corpus du 29/08/2026 les profils *sont* groupés, donc
    la séquence tient en une entrée par tranche — quelques dizaines d'octets.
    Elle ne le suppose pas pour autant : un profil interfolié se recompose
    aussi, à sa place près.
    """
    plages: list[list[Any]] = []
    for valeur in valeurs:
        if plages and plages[-1][0] == valeur:
            plages[-1][1] += 1
        else:
            plages.append([valeur, 1])
    return plages


def _marquer_derivables(
    manifeste_tranches: list[dict[str, Any]],
    tranches: dict[str, list[Any]],
    acteur_ref: Optional[str],
) -> set[str]:
    """Marque les tranches de législature close que l'archive couvre (#691).

    Rend les noms marqués. **Modifie `manifeste_tranches` en place** : une
    entrée marquée perd son `fichier` — elle n'en a plus — et gagne `derivee`,
    `acteur_ref` et un `nombre` qui est **celui de l'archive**.

    ## Pourquoi le `nombre` vient de l'archive, et pas de la collecte

    Arbitrage rendu par la propriétaire le 09/09/2026. Les deux comptes
    coïncident aujourd'hui — 854 tranches sur 854, 568 771 amendements sans
    écart —, la question portait sur le jour où ils divergeront :

    - `nombre` = **la collecte** : `recomposer` lève, et le profil devient
      **illisible**. L'erreur apparaît alors à la relecture, très loin de sa
      cause — le patron que #771 a payé 1 h 18 ;
    - `nombre` = **l'archive** : la lecture tient toujours, et l'écart se
      déclare **là où il naît**, à l'écriture.

    D'où `nombre_collecte`, écrit **uniquement** en cas d'écart : un champ qui
    n'apparaît que quand quelque chose ne va pas se remarque, quand un champ
    toujours présent et presque toujours égal ne se lit plus (#510).

    ## Ce qui n'est jamais marqué

    Une législature vivante, un acteur inconnu, une archive absente ou
    illisible : dans les trois cas, la tranche reste un fichier. **Ne rien
    marquer est le défaut**, et il est sûr — la tranche continue d'être écrite
    exactement comme avant.
    """
    if not acteur_ref:
        return set()
    import tranches_amendements_figees as figees

    marques: set[str] = set()
    for declaree in manifeste_tranches:
        legislature = str(declaree.get("legislature") or "")
        if legislature not in figees.LEGISLATURES_FIGEES:
            continue
        try:
            entrees = figees.signatures(acteur_ref, legislature)
        except (OSError, json.JSONDecodeError):
            # Archive absente ou illisible : on n'a rien à dériver, la tranche
            # reste un fichier. Une panne d'archive ne doit pas amputer un
            # profil (#484).
            continue
        if entrees is None:
            continue
        nom = str(declaree.get("fichier", ""))[: -len(".json")]
        collecte = len(tranches.get(nom) or [])
        declaree.pop("fichier", None)
        declaree[CLE_TRANCHE_DERIVEE] = True
        declaree[CLE_ACTEUR_TRANCHE] = acteur_ref
        declaree["nombre"] = len(entrees)
        if collecte != len(entrees):
            declaree["nombre_collecte"] = collecte
        marques.add(nom)
    return marques


def partitionner(
    profil: dict[str, Any], *, acteur_ref: Optional[str] = None
) -> tuple[dict[str, Any], dict[str, list[Any]]]:
    """Sépare un profil brut en (socle, {nom de tranche: amendements}).

    `acteur_ref` déclenche le marquage des tranches dérivables (#691) : les
    législatures closes que l'archive couvre pour cet acteur sortent du
    dictionnaire rendu — elles ne sont plus écrites — et leur entrée de
    manifeste porte `derivee`. Sans `acteur_ref`, rien n'est marqué et le
    comportement est celui d'avant, à l'octet près.

    Le socle est une **copie de surface** : le profil d'entrée n'est pas
    modifié, et les objets amendements ne sont ni copiés ni retouchés — ce sont
    les mêmes objets, déplacés.

    Un profil qui ne porte pas `amendements` (profil UE, profil sans dépôt)
    rend un socle sans manifeste et aucune tranche : on ne pose pas un
    manifeste vide sur un profil qui n'a jamais rien eu à ranger.
    """
    amendements = profil.get(CLE_PARTITIONNEE)

    if amendements is None or amendements == []:
        # Rien à ranger : ni manifeste, ni répertoire. Une liste VIDE reste
        # une liste vide dans le socle — c'est un fait collecté (« ce profil
        # n'a déposé aucun amendement »), et le remplacer par un manifeste à
        # zéro le rendrait indistinct d'un profil dont la clé est absente.
        socle = {c: v for c, v in profil.items() if c != CLE_MANIFESTE}
        return socle, {}
    if not isinstance(amendements, list):
        raise PartitionIllisible(
            f"`{CLE_PARTITIONNEE}` n'est pas une liste "
            f"({type(amendements).__name__}) : profil non partitionnable."
        )

    tranches: dict[str, list[Any]] = {}
    legislature_du_nom: dict[str, Any] = {}
    suite: list[str] = []
    for amendement in amendements:
        legislature = (
            amendement.get("legislature") if isinstance(amendement, dict) else None
        )
        # « Absent » et « vide » sont la MÊME absence, et vont dans la même
        # tranche. Les distinguer produirait `sans-legislature` et
        # `sans-legislature-2`, deux noms pour un seul fait. L'amendement, lui,
        # garde son champ tel qu'il est collecté : c'est le regroupement qui
        # normalise, jamais la donnée.
        if legislature is None or (isinstance(legislature, str) and not legislature.strip()):
            legislature = None
        nom = nom_tranche(legislature)
        # Deux valeurs distinctes qui retomberaient sur le même nom de fichier
        # se confondraient à la recomposition. On garde la première et on
        # désambiguïse la suivante — le manifeste porte la valeur exacte.
        if nom in legislature_du_nom and legislature_du_nom[nom] != legislature:
            base, n = nom, 2
            while nom in legislature_du_nom and legislature_du_nom[nom] != legislature:
                nom = f"{base}-{n}"
                n += 1
        legislature_du_nom.setdefault(nom, legislature)
        tranches.setdefault(nom, []).append(amendement)
        suite.append(nom)

    noms_ordonnes = sorted(tranches, key=lambda n: (n == NOM_SANS_LEGISLATURE, n))
    index_du_nom = {nom: i for i, nom in enumerate(noms_ordonnes)}

    manifeste = {
        "schema": SCHEMA_PARTITION,
        "total": len(amendements),
        "tranches": [
            {
                "legislature": legislature_du_nom[nom],
                "fichier": f"{nom}.json",
                "nombre": len(tranches[nom]),
            }
            for nom in noms_ordonnes
        ],
        # Ordre d'origine, par plages sur l'index de tranche.
        "ordre": _sequence(index_du_nom[nom] for nom in suite),
    }

    # Le marquage vient APRÈS la construction du manifeste, et il en corrige
    # deux choses : l'entrée de la tranche, et la séquence.
    marques = _marquer_derivables(manifeste["tranches"], tranches, acteur_ref)
    if marques:
        # L'ORDRE D'ORIGINE N'EST PLUS RESTITUABLE, et il est donc remplacé par
        # un ordre par blocs — chaque tranche d'un seul tenant, dans l'ordre du
        # manifeste. La raison n'est pas un renoncement : la tranche dérivée
        # sera relue dans l'ordre de l'archive, qui n'est pas celui de la
        # collecte (mesuré : sur `mathilde-panot/16.json`, ensemble identique et
        # 16 915 positions sur 16 915 différentes). Garder la séquence
        # d'origine ferait lever `recomposer` dès que le compte de l'archive
        # diffère de celui de la collecte, c'est-à-dire précisément le cas que
        # `nombre_collecte` existe pour déclarer.
        #
        # Ce que ça coûte : rien de publié. Aucun consommateur ne lit l'ordre —
        # `audit_diff_profils` relève une liste par un **entier**, et le site
        # trie ce qu'il affiche. Ce que ça préserve : la propriété d'aller-retour
        # identique reste vraie pour tout profil SANS tranche dérivée, qui est
        # le seul cas où elle était testée et le seul où elle a un sens.
        manifeste["ordre"] = [
            [i, declaree["nombre"]]
            for i, declaree in enumerate(manifeste["tranches"])
        ]
        manifeste["total"] = sum(t["nombre"] for t in manifeste["tranches"])
        for nom in marques:
            tranches.pop(nom, None)

    # Le manifeste prend la PLACE EXACTE de `amendements` dans l'ordre des
    # clés, et `recomposer` fait l'inverse. Ce n'est pas de la coquetterie :
    # c'est ce qui rend l'aller-retour identique **octet pour octet**, et donc
    # ce qui permet à la migration de comparer deux empreintes plutôt que deux
    # structures. Un dict Python conserve son ordre d'insertion, et
    # `json.dumps` le recopie.
    socle: dict[str, Any] = {}
    for cle, valeur in profil.items():
        if cle == CLE_MANIFESTE:
            continue
        socle[CLE_MANIFESTE if cle == CLE_PARTITIONNEE else cle] = (
            manifeste if cle == CLE_PARTITIONNEE else valeur
        )
    # Les tranches marquées `derivee` ne sont PAS rendues : elles n'ont plus de
    # fichier à écrire, et `ecrire_profil_brut` supprimera celui qui existait —
    # par le nettoyage des « non attendus » qui était déjà là (#691).
    return socle, {nom: tranches[nom] for nom in noms_ordonnes if nom in tranches}


def est_partitionne(socle: Any) -> bool:
    """Vrai si ce document est un socle, faux si c'est un profil monolithique."""
    return isinstance(socle, dict) and isinstance(socle.get(CLE_MANIFESTE), dict)


def _manifeste(socle: dict[str, Any]) -> dict[str, Any]:
    manifeste = socle.get(CLE_MANIFESTE)
    if not isinstance(manifeste, dict):
        raise PartitionIllisible(f"`{CLE_MANIFESTE}` absent ou malformé.")
    schema = manifeste.get("schema")
    if schema != SCHEMA_PARTITION:
        raise PartitionIllisible(
            f"schéma de partition inconnu : {schema!r} (attendu {SCHEMA_PARTITION!r}). "
            "Refus de recomposer un profil dont on ne sait pas lire la découpe."
        )
    return manifeste


def recomposer(socle: dict[str, Any], tranches: dict[str, list[Any]]) -> dict[str, Any]:
    """Reconstitue le profil monolithique depuis son socle et ses tranches.

    L'ordre d'origine de `amendements` est restitué par la séquence du
    manifeste. Toute incohérence — tranche absente, compte qui ne tombe pas —
    lève `PartitionIllisible` : c'est le contraire d'un `get(..., [])`, qui
    republierait un profil amputé sans que rien ne le dise.
    """
    manifeste = _manifeste(socle)
    declarees = manifeste.get("tranches") or []
    noms = [_nom_declaree(t) for t in declarees]

    restes: list[list[Any]] = []
    for nom, declaree in zip(noms, declarees):
        contenu = tranches.get(nom)
        if contenu is None:
            raise PartitionIllisible(
                f"tranche annoncée mais absente : {nom}.json "
                f"({declaree.get('nombre')} amendement(s) attendus)."
            )
        attendu = declaree.get("nombre")
        if isinstance(attendu, int) and len(contenu) != attendu:
            raise PartitionIllisible(
                f"tranche {nom}.json : {len(contenu)} amendement(s) lus pour "
                f"{attendu} annoncé(s)."
            )
        restes.append(list(contenu))

    curseurs = [0] * len(restes)
    amendements: list[Any] = []
    for index, nombre in (manifeste.get("ordre") or []):
        if not isinstance(index, int) or not 0 <= index < len(restes):
            raise PartitionIllisible(f"séquence : index de tranche hors bornes ({index!r}).")
        debut = curseurs[index]
        fin = debut + int(nombre)
        if fin > len(restes[index]):
            raise PartitionIllisible(
                f"séquence : la tranche {noms[index]}.json est épuisée "
                f"({fin} demandés, {len(restes[index])} disponibles)."
            )
        amendements.extend(restes[index][debut:fin])
        curseurs[index] = fin

    for i, curseur in enumerate(curseurs):
        if curseur != len(restes[i]):
            raise PartitionIllisible(
                f"séquence : {len(restes[i]) - curseur} amendement(s) de "
                f"{noms[i]}.json ne sont pas replacés."
            )

    total = manifeste.get("total")
    if isinstance(total, int) and len(amendements) != total:
        raise PartitionIllisible(
            f"{len(amendements)} amendement(s) recomposés pour {total} annoncé(s)."
        )

    # `amendements` reprend la place du manifeste — l'inverse exact de
    # `partitionner`, y compris dans l'ordre des clés.
    profil: dict[str, Any] = {}
    for cle, valeur in socle.items():
        if cle == CLE_MANIFESTE:
            profil[CLE_PARTITIONNEE] = amendements
        else:
            profil[cle] = valeur
    if CLE_PARTITIONNEE not in profil:
        profil[CLE_PARTITIONNEE] = amendements
    return profil


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def ecrire_profil_brut(
    profils_dir: Path, slug: str, profil: dict[str, Any],
    acteur_ref: Optional[str] = None,
) -> list[Path]:
    """Écrit un profil brut sous sa forme partitionnée. Rend les chemins écrits.

    Les tranches devenues sans objet — une législature qui disparaîtrait d'un
    profil — sont retirées du répertoire : les laisser ferait recomposer des
    amendements que le profil ne porte plus. Rien d'autre n'est supprimé, et
    seuls les fichiers du répertoire de tranches sont touchés.

    **Une tranche qui devient dérivée (#691) emprunte ce même chemin** : elle
    sort du dictionnaire rendu par `partitionner`, donc elle n'est pas dans les
    « attendus », donc son fichier est supprimé. Rien n'a été ajouté ici pour
    ça — c'est le nettoyage qui existait déjà, appliqué à une tranche qui n'a
    plus lieu d'être écrite.
    """
    profils_dir = Path(profils_dir)
    socle_path = chemin_socle(profils_dir, slug)
    dossier = dossier_tranches(profils_dir, slug)

    socle, tranches = partitionner(profil, acteur_ref=acteur_ref)

    ecrits: list[Path] = []
    if tranches:
        dossier.mkdir(parents=True, exist_ok=True)
        attendus = set()
        for nom, contenu in tranches.items():
            chemin = dossier / f"{nom}.json"
            ecrire_profil_json(chemin, {
                "schema": SCHEMA_TRANCHE,
                "slug": slug,
                "legislature": next(
                    (t["legislature"] for t in socle[CLE_MANIFESTE]["tranches"]
                     if t.get("fichier") == f"{nom}.json"),
                    None,
                ),
                CLE_PARTITIONNEE: contenu,
            })
            attendus.add(chemin.name)
            ecrits.append(chemin)
        for obsolete in dossier.glob("*.json"):
            if obsolete.name not in attendus:
                obsolete.unlink()
    elif dossier.is_dir():
        # Le profil ne porte plus d'amendements du tout : le répertoire ne doit
        # pas survivre à sa raison d'être.
        for obsolete in dossier.glob("*.json"):
            obsolete.unlink()
        try:
            dossier.rmdir()
        except OSError:
            pass

    # Le socle en DERNIER : c'est lui qui déclare les tranches. Écrit avant,
    # une interruption laisserait un manifeste pointant sur des fichiers non
    # encore écrits — `recomposer` lèverait, ce qui est correct mais évitable.
    ecrire_profil_json(socle_path, socle)
    ecrits.append(socle_path)
    return ecrits


def _lire_json(chemin: Path) -> Any:
    with open(chemin, encoding="utf-8") as flux:
        return json.load(flux)


def charger_socle(chemin: Path) -> Optional[dict[str, Any]]:
    """Lit le seul fichier `<slug>.json`, sans recomposer.

    À utiliser quand la question ne porte pas sur les amendements — identité,
    mandats, votes, interventions. C'est le gain de la découpe : 1,85 Mo lus
    au lieu de 56.
    """
    document = _lire_json(chemin)
    return document if isinstance(document, dict) else None


def _nom_declaree(declaree: dict[str, Any]) -> str:
    """Le nom sous lequel une tranche déclarée est rangée.

    **Une seule définition**, partagée par `charger_tranches`, `recomposer` et
    `iter_amendements_du_profil` : ces trois-là indexaient le même manifeste par
    le même calcul recopié, et une tranche dérivée — qui n'a pas de `fichier` —
    aurait divergé chez l'un des trois sans que rien ne le dise.
    """
    if declaree.get(CLE_TRANCHE_DERIVEE):
        return nom_tranche(declaree.get("legislature"))
    fichier = str(declaree.get("fichier") or "")
    if not fichier.endswith(".json") or not _NOM_SUR.match(fichier[: -len(".json")]):
        raise PartitionIllisible(f"nom de tranche refusé : {fichier!r}.")
    return fichier[: -len(".json")]


def _amendements_derives(declaree: dict[str, Any]) -> list[Any]:
    """La tranche que le manifeste déclare dérivable de l'archive figée (#691).

    Import différé : `tranches_amendements_figees` ouvre des archives de
    plusieurs centaines de Mo, et la très grande majorité des lecteurs de ce
    module n'a aucune tranche dérivée à relire.

    Toute impossibilité lève `PartitionIllisible`, comme pour un fichier
    manquant : une tranche annoncée et non relisible est une panne, jamais une
    liste vide. C'est la même règle qu'ailleurs dans ce module, et c'est elle
    qui empêche de republier un profil amputé.
    """
    import tranches_amendements_figees as figees

    legislature = str(declaree.get("legislature") or "")
    acteur = declaree.get(CLE_ACTEUR_TRANCHE)
    if not legislature:
        raise PartitionIllisible(
            "tranche dérivée sans `legislature` : rien ne dit quelle archive lire."
        )
    if not acteur:
        raise PartitionIllisible(
            f"tranche dérivée sans `{CLE_ACTEUR_TRANCHE}` (législature {legislature}) : "
            "l'archive s'interroge par acteur, et ce module ne résout pas les slugs."
        )
    try:
        amendements = figees.reconstruire_tranche(acteur, legislature)
    except (OSError, json.JSONDecodeError) as exc:
        raise PartitionIllisible(
            f"archive figée illisible pour la législature {legislature} ({exc})."
        ) from exc
    if amendements is None:
        raise PartitionIllisible(
            f"acteur {acteur} inconnu de l'archive de la législature {legislature} : "
            "une tranche déclarée dérivée doit être dérivable."
        )
    return amendements


def charger_tranches(chemin_socle_: Path, socle: dict[str, Any]) -> dict[str, list[Any]]:
    """Charge les tranches déclarées par un socle.

    Une tranche marquée `derivee` ne vient pas du disque : elle se reconstruit
    depuis `raw_data/amendements_an_figes/` (#691). Le `nombre` que le manifeste
    annonce n'est pas repris — c'est `recomposer` qui le confronte au compte
    obtenu, et un contrôle qui lirait sa conclusion dans le document contrôlé ne
    contrôlerait rien (#576, #579).
    """
    dossier = dossier_tranches_du_socle(chemin_socle_)
    manifeste = _manifeste(socle)
    tranches: dict[str, list[Any]] = {}
    for declaree in (manifeste.get("tranches") or []):
        nom = _nom_declaree(declaree)
        if declaree.get(CLE_TRANCHE_DERIVEE):
            tranches[nom] = _amendements_derives(declaree)
            continue
        chemin = dossier / f"{nom}.json"
        try:
            contenu = _lire_json(chemin)
        except (OSError, json.JSONDecodeError) as exc:
            raise PartitionIllisible(f"tranche illisible : {chemin} ({exc}).") from exc
        if isinstance(contenu, dict):
            contenu = contenu.get(CLE_PARTITIONNEE)
        if not isinstance(contenu, list):
            raise PartitionIllisible(f"tranche sans liste `{CLE_PARTITIONNEE}` : {chemin}.")
        tranches[nom] = contenu
    return tranches


def charger_profil_brut(chemin: Path) -> dict[str, Any]:
    """Charge un profil brut COMPLET depuis son chemin `<slug>.json`.

    **Accepte les deux formes** : un fichier monolithique (l'ancienne, encore
    committée) est rendu tel quel ; un socle est recomposé depuis ses tranches.
    C'est la porte unique des lecteurs qui ont besoin des amendements.
    """
    document = _lire_json(chemin)
    if not isinstance(document, dict):
        raise PartitionIllisible(f"{chemin} : document JSON qui n'est pas un objet.")
    if not est_partitionne(document):
        return document
    return recomposer(document, charger_tranches(Path(chemin), document))


def iter_amendements_du_profil(chemin: Path) -> Iterator[dict[str, Any]]:
    """Itère les amendements d'un profil, **une tranche à la fois**.

    Pour les index, qui n'ont besoin ni du socle ni de l'ordre : la tranche est
    relâchée avant d'ouvrir la suivante, donc le pic mémoire tombe du profil
    entier (56 Mo) à sa plus grosse tranche (23,4 Mo). La forme monolithique
    reste acceptée, au même pic qu'avant.
    """
    document = _lire_json(chemin)
    if not isinstance(document, dict):
        return
    if not est_partitionne(document):
        for amendement in (document.get(CLE_PARTITIONNEE) or []):
            if isinstance(amendement, dict):
                yield amendement
        return

    dossier = dossier_tranches_du_socle(Path(chemin))
    manifeste = _manifeste(document)
    del document
    for declaree in (manifeste.get("tranches") or []):
        nom = _nom_declaree(declaree)
        if declaree.get(CLE_TRANCHE_DERIVEE):
            derivee = _amendements_derives(declaree)
            for amendement in derivee:
                if isinstance(amendement, dict):
                    yield amendement
            del derivee
            continue
        chemin_tranche = dossier / f"{nom}.json"
        try:
            contenu = _lire_json(chemin_tranche)
        except (OSError, json.JSONDecodeError) as exc:
            raise PartitionIllisible(f"tranche illisible : {chemin_tranche} ({exc}).") from exc
        if isinstance(contenu, dict):
            contenu = contenu.get(CLE_PARTITIONNEE)
        if not isinstance(contenu, list):
            raise PartitionIllisible(
                f"tranche sans liste `{CLE_PARTITIONNEE}` : {chemin_tranche}."
            )
        for amendement in contenu:
            if isinstance(amendement, dict):
                yield amendement
        del contenu


def compter_amendements(chemin: Path) -> int:
    """Nombre d'amendements d'un profil, **mesuré** et non lu au manifeste.

    Le total du manifeste n'est pas la mesure : un contrôle qui recopie un
    chiffre déclaré écrit sa conclusion sans la vérifier (#576, #579). Les
    tranches sont donc réellement ouvertes et comptées.
    """
    return sum(1 for _ in iter_amendements_du_profil(chemin))


def fichiers_du_profil(profils_dir: Path, slug: str) -> list[Path]:
    """Tous les fichiers d'un profil : socle + tranches existantes.

    Sert au transport (artifacts CI) et à la migration : un profil n'est plus
    un fichier, et tout ce qui le déplaçait fichier par fichier doit passer
    par ici.
    """
    profils_dir = Path(profils_dir)
    chemins = []
    socle = chemin_socle(profils_dir, slug)
    if socle.is_file():
        chemins.append(socle)
    dossier = dossier_tranches(profils_dir, slug)
    if dossier.is_dir():
        chemins.extend(sorted(dossier.glob("*.json")))
    return chemins


def slugs_du_repertoire(profils_dir: Path) -> list[str]:
    """Slugs des profils bruts d'un répertoire, ordre stable.

    Les fichiers de service (`.generation_checkpoint.json`) et les répertoires
    de tranches sont écartés : un slug est un `<slug>.json` de premier niveau.
    """
    profils_dir = Path(profils_dir)
    if not profils_dir.is_dir():
        return []
    return sorted(
        chemin.name[: -len(".json")]
        for chemin in profils_dir.glob("*.json")
        if chemin.is_file() and not chemin.name.startswith(".")
    )
