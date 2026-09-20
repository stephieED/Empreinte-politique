#!/usr/bin/env python3
"""textes_vises_figes.py — Le `texte_vise` sourcé d'un amendement, relu des
archives figées (#696).

LE DÉFAUT. #639 a corrigé la **collecte** : elle écrasait le code sourcé du
document amendé (`PRJLANR5L15B2623`) par le titre du dossier
(« Système universel de retraite ») avant d'écrire le profil brut. Elle ne le
fait plus. Mais `pivot_data/amendements/` est **fusionné additivement** avec
l'index déjà publié, et une entrée écrite avant #639 y garde son intitulé à
chaque reconstruction : c'est la quatrième occurrence de la famille nommée par
AGENTS.md §3a (#492 `mandats[].chambre`, #639 `type_scrutin`, #641
`identite.profession`), et le remède est le même — un **report nommé**, jamais
une fusion plus permissive.

MESURÉ LE 01/09/2026, sur `origin/main` à `f635cb60` :

| Population | Mesure |
| --- | ---: |
| amendements publiés (`pivot_data/amendements/{14,15,16,17}.json`) | 484 132 |
| dont `texte_vise` n'est pas un uid de document AN | **2 500** (tous en XVe) |
| intitulés distincts en cause | 5 |
| réparables depuis `raw_data/amendements_an_figes/15/` | **2 500 / 2 500** |
| paires amendement × signataire dans les 481 profils bruts | 6 091 732 |
| dont `texte_vise` est un intitulé | 13 399, **dans un seul profil** (`jean-luc-melenchon`) |

LA SOURCE A RAISON, L'INDEX PUBLIÉ A TORT. Les trois archives figées portent
2 086 `texte_vise` distincts (781 en XIVe, 855 en XVe, 450 en XVIe) et **aucun
n'est un intitulé** : la valeur juste était disponible tout du long. C'est
d'elle qu'on relit, jamais d'une reconstruction depuis le titre et jamais d'un
appariement de libellé, même exact (#639, AGENTS.md §2 règle 2). Le préfixe du
document (`PRJL`/`PION`/`PNRE`/`RAPP`) n'est d'ailleurs pas dans l'uid de
l'amendement : le déduire serait l'inventer.

LE CRITÈRE, ÉCRIT ET MESURÉ. `est_uid_texte` reconnaît la grammaire de l'uid de
document AN — un préfixe capitalisé, l'infixe `ANR5L` que l'Assemblée écrit dans
chacun de ses identifiants, la législature, la série, le numéro. Mesuré sur les
**2 387 valeurs distinctes publiées** : 2 382 acceptées, 5 refusées, et ce sont
exactement les 5 intitulés. Mesuré sur les **2 086 valeurs distinctes des trois
archives figées** : 2 086 acceptées, 0 refusée.

Le critère « contient une espace » de l'issue donne aujourd'hui le **même
verdict** sur ces deux populations — aucun contre-exemple relevé, ni un intitulé
sans espace, ni un uid en portant une. Il n'est pas retenu pour autant : il ne
dit que ce qu'un identifiant n'est pas, là où la grammaire dit ce qu'il est, et
il laisserait passer un intitulé d'un seul mot (« Bioéthique » est un titre de
dossier réel de la XVe). La grammaire est strictement plus stricte que lui sur
les deux populations mesurées.

CE QUE LA LECTURE COÛTE. L'archive figée de la XVe pèse 134 Mio décompressés
pour 307 644 enregistrements ; la charger telle quelle coûte 610 Mio de RSS
(mesuré). Elle est donc lue **par projection**, via un `object_pairs_hook` qui
ne retient d'un enregistrement que son `texte_vise` et n'en garde que les uid
demandés : 280 Mio de pic et 1,9 s (mesuré), et rien de retenu ensuite —
AGENTS.md §3a, « lire par projection, ne jamais garder un document ».

CE QU'ELLE NE PEUT PAS RÉPARER. Une législature **sans archive figée** : la
XVIIe est en cours, elle n'en a pas, et un amendement de la XVIIe portant un
intitulé resterait donc tel quel. Le cas est aujourd'hui vide (0 des 96 893
amendements publiés de la XVIIe), et il l'est par construction : la XVIIe est
recollectée à chaque run, donc la correction de #639 l'a déjà traversée. Le
report le **compte et le nomme** plutôt que de retomber sur une seconde source
en silence — c'est ce silence-là qui a rendu #510 invisible.
"""

import gzip
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

#: Archives figées committées, écrites par `build_amendements_index_figees.py`
#: pour les législatures closes (`AN_AMENDEMENTS_LEGISLATURES_FIGEES` : 14, 15,
#: 16). Même chemin que `candidate_profile.AN_AMENDEMENTS_FIGEES_DIR` ; il est
#: redéclaré ici pour ne pas importer les 3 000 lignes de la collecte dans un
#: lecteur de 100.
DIR_ARCHIVES_FIGEES = Path("raw_data") / "amendements_an_figes"

#: Nom du fichier d'amendements dédupliqués de l'archive figée. Miroir de
#: `candidate_profile.AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME`.
NOM_ARCHIVE_AMENDEMENTS = "amendements.json.gz"

#: Grammaire de l'uid d'un **document** AN, tel que `texteLegislatifRef` le
#: porte : `PRJLANR5L15B2623`, `PIONANR5L17BTC0699`, `PRJLANR5L15BTA0749`.
#:
#: L'ancre est `ANR5L`, l'infixe que l'Assemblée écrit dans tous ses
#: identifiants ; les parties variables (préfixe, série) sont volontairement
#: larges, parce que le rôle du critère est de reconnaître un identifiant, pas
#: d'énumérer les quatre préfixes observés — un préfixe inédit doit être accepté,
#: pas requalifié en intitulé. Mesures et contre-mesures : docstring du module.
_RE_UID_TEXTE = re.compile(r"^[A-Z]{2,8}ANR5L\d{1,2}[A-Z]{0,4}\d+$")

#: Clés qui, ensemble, identifient un **enregistrement d'amendement** dans
#: l'archive — par opposition au dictionnaire racine, dont les clés sont des
#: uid d'amendement. Sert à `_projeter`, qui doit distinguer les deux sans
#: dépendre de l'ordre d'écriture des champs.
_CLES_ENREGISTREMENT = frozenset({"uid", "texte_vise"})


def est_uid_texte(valeur: Any) -> bool:
    """`True` si `valeur` est un uid de document AN, `False` sinon.

    `False` couvre trois situations que l'appelant traite de la même façon —
    il faut relire la source — mais qu'il **compte séparément** : l'absence
    (`None`), la chaîne vide, et l'intitulé écrit à la place du code.
    """
    return isinstance(valeur, str) and bool(_RE_UID_TEXTE.match(valeur))


def chemin_archive(legislature: str, dir_archives: Optional[Path] = None) -> Path:
    """Chemin de l'archive figée d'une législature."""
    racine = Path(dir_archives) if dir_archives is not None else DIR_ARCHIVES_FIGEES
    return racine / str(legislature) / NOM_ARCHIVE_AMENDEMENTS


def lire_textes_vises(
    legislature: str,
    uids: Iterable[str],
    *,
    dir_archives: Optional[Path] = None,
) -> dict[str, str]:
    """`{uid d'amendement: texte_vise sourcé}`, pour les seuls `uids` demandés.

    Rend `{}` — jamais une exception — si l'archive est absente ou illisible :
    l'appelant en fait alors une réparation **impossible et comptée**, jamais
    une suppression de ce qui est publié. C'est la même convention que
    `textes_dossiers_an.charger_table`.

    N'entrent dans le résultat que les valeurs qui sont **elles-mêmes** des uid
    de document : substituer un intitulé de l'archive à un intitulé de l'index
    ne réparerait rien, et l'archive n'en porte aucun (0 sur les 2 086 valeurs
    distinctes des trois archives, mesuré le 01/09/2026).

    Lecture par projection : voir la docstring du module pour les deux mesures
    de RSS qui l'imposent.
    """
    demandes = {u for u in uids if isinstance(u, str) and u}
    if not demandes:
        return {}

    chemin = chemin_archive(legislature, dir_archives)
    if not chemin.is_file():
        return {}

    def _projeter(paires: list[tuple[str, Any]]) -> Any:
        cles = {cle for cle, _ in paires}
        if _CLES_ENREGISTREMENT <= cles:
            # Enregistrement d'amendement : on n'en retient que le texte visé.
            # Le reste (jusqu'à 500 cosignataires) est relâché aussitôt.
            for cle, valeur in paires:
                if cle == "texte_vise":
                    return sys.intern(valeur) if isinstance(valeur, str) else None
            return None
        # Le dictionnaire racine : uid d'amendement -> texte visé projeté.
        return {
            cle: valeur for cle, valeur in paires
            if cle in demandes and est_uid_texte(valeur)
        }

    try:
        with gzip.open(chemin, "rt", encoding="utf-8") as f:
            projete = json.load(f, object_pairs_hook=_projeter)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        print(f"  [!] Archive figée illisible ({chemin}), aucun texte visé relu : {exc}")
        return {}

    return projete if isinstance(projete, dict) else {}
