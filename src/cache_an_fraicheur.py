#!/usr/bin/env python3
"""Fraîcheur du cache AN restauré, et péremption de ce qui périme (#555).

Pourquoi ce fichier existe
--------------------------
La clé hebdomadaire `public-data-cache-an-<semaine>[-interv-<empreinte>]` est le
**seul** mécanisme de fraîcheur des index AN : aucun constructeur d'index ne
regarde l'âge de ce qu'il trouve sur le disque.
`_ensure_acteurs_historique_zip_downloaded` rend l'archive dès que
`zip_path.is_file()`, `_build_acteur_questions_index` rend l'index dès que
`index_path.is_file()`, `_read_cached_interventions_syceron_acteur` rend la
tranche dès que le répertoire d'index existe. Aucun `mtime`, aucun TTL, nulle
part.

Or la dernière ligne des `restore-keys` est un **préfixe nu**,
`public-data-cache-an-`, sans borne de semaine. Sur un miss de la clé exacte,
`actions/cache` remonte les `restore-keys` et sert l'entrée la plus récente qui
commence par le préfixe — celle de la semaine précédente, ou d'avant.

MESURÉ, run `32738726729` du 24/08/2026 (lundi, première exécution de la
semaine W35), shard `jean-luc-melenchon`, job `97468417763` :

    14:28:54  Cache hit for restore-key: public-data-cache-an-2026-W34
    14:28:54  Cache Size: ~21 MB (21880744 B)
    14:28:54  Cache restored from key: public-data-cache-an-2026-W34
    14:28:58  Extraction AN — début
    14:29:09  Elapsed (wall clock) time: 0:10.12   ← aucune archive rouverte
    14:29:12  Cache saved with key: public-data-cache-an-2026-W35

Dix-huit secondes entre la restauration d'une entrée du **20/08** et sa
sauvegarde sous la clé du **24/08**, sans qu'une seule archive ait été
retéléchargée. La semaine ne périme donc rien : chaque semaine blanchit le
contenu de la précédente sous son propre nom, indéfiniment, sur une 17e
législature qui, elle, continue de siéger.

Ce que ce module refuse de faire
--------------------------------
**Retirer le préfixe nu.** Il n'est pas là par accident : il sert le
réchauffement de #424 — sans lui, le premier run d'une semaine repart d'un cache
vide et retélécharge tout. Et il porte, avec les archives vivantes, les index des
législatures **closes**, dont le réchauffement inter-semaines est parfaitement
légitime : la 15e coûte 147 s à réindexer, la 16e 55 s, la 17e 42 s (mesures
#550). Périmer l'entrée entière chaque semaine coûterait 244 s de réindexation
là où 42 s suffisent.

Ce que ce module fait
---------------------
Il lit le **marqueur de fraîcheur qui existe déjà** : la clé effectivement
restaurée, rendue par `actions/cache/restore` dans `cache-matched-key`. Elle
porte la semaine de l'entrée servie. Aucun fichier sentinelle à écrire, donc
aucun ajout au `path:` du step de cache — donc aucun changement de *version*
d'entrée, donc aucune semaine de cache perdue à le déployer.

Comparée à la semaine courante, elle donne un verdict, et deux usages :

- ``--perimer`` (job **producteur**, `extract-an`) : les chemins qui PÉRIMENT
  sont supprimés, les chemins figés sont laissés en place. Le job réindexe donc
  la seule législature en cours et sauvegarde une entrée réellement datée de la
  semaine.
- déclaration seule (job **consommateur**, `extract-roster-groupes`) : un
  `::warning::` nomme la semaine servie, et rien n'est supprimé. Ce job est en
  `actions/cache/restore` depuis #505 — il ne sauvegarde rien. Y périmer le
  cache ferait retélécharger les archives par chacun de ses 8 shards sans que
  rien ne soit persisté en retour : ce serait #424 recréé, pas corrigé.

Ce qui périme, et ce qui ne périme pas
--------------------------------------
La frontière est la **clôture de la législature**, pas le répertoire. Elle est
DÉRIVÉE des deux référentiels de gel du code
(`AN_SCRUTINS_LEGISLATURES_FIGEES`, `AN_AMENDEMENTS_LEGISLATURES_FIGEES`),
jamais recopiée — même règle que l'empreinte de #550, et pour la même raison :
recopiée, la liste deviendrait fausse le jour où la 17e se clôt ou la 18e
s'ouvre, et le cache se remettrait à périmer (ou à ne plus périmer) au mauvais
endroit sans que rien ne le dise.

`.cache/acteurs_historique_an` périme **en entier** : le référentiel des acteurs
n'a pas de structure par législature, l'AN le republie en continu, et c'est de
lui que viennent identité, mandats et positions dans l'hémicycle.
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import candidate_profile as _cp
import gha

#: Préfixe des clés de cache AN. Le workflow le porte à l'identique ;
#: `tests/test_ci_cache_fraicheur_555.py` compare les deux — une clé renommée
#: d'un côté seulement rendrait toute clé illisible ici, donc toute semaine
#: suspecte, donc une péremption hebdomadaire silencieuse.
PREFIXE_CLE_AN = "public-data-cache-an-"

#: `public-data-cache-an-2026-W35`, `…-W35-interv`, `…-W35-interv-syc17-q16.17`.
#: La semaine est le premier champ après le préfixe, et le seul qu'on lise.
_CLE_AN = re.compile(rf"^{re.escape(PREFIXE_CLE_AN)}(\d{{4}}-W\d{{2}})(?:-.*)?$")

#: Un répertoire de législature dans `.cache` : `17`, `16`…
_LEGISLATURE = re.compile(r"^\d+$")

#: Verdicts possibles, en clair dans les journaux du run.
FRAIS = "frais"
PERIME = "périmé"
CACHE_FROID = "cache froid"
INDECIDABLE = "indécidable"


def legislatures_figees() -> frozenset[str]:
    """Les législatures que l'Assemblée nationale ne modifie plus.

    **Intersection** des deux référentiels de gel du code, jamais une liste
    recopiée. Intersection et non union : une législature n'est traitée comme
    figée que si les DEUX le disent. S'ils divergeaient, la divergence ferait
    périmer une législature de trop — un coût de réindexation, jamais une donnée
    conservée à tort. Le sens de l'erreur est choisi, pas subi.
    """
    return frozenset(_cp.AN_SCRUTINS_LEGISLATURES_FIGEES) & frozenset(
        _cp.AN_AMENDEMENTS_LEGISLATURES_FIGEES
    )


def semaine_de_la_cle(cle: Optional[str]) -> Optional[str]:
    """La semaine ISO portée par une clé de cache AN, ou `None`.

    `None` couvre trois cas que l'appelant distingue : clé vide (aucune entrée
    restaurée), clé d'une autre famille, clé dont le format a changé.
    """
    if not cle:
        return None
    trouve = _CLE_AN.match(cle.strip())
    return trouve.group(1) if trouve else None


def chemins_perissables(
    cache_acteurs: Optional[Path] = None,
    cache_scrutins: Optional[Path] = None,
    cache_questions: Optional[Path] = None,
    cache_syceron: Optional[Path] = None,
) -> list[Path]:
    """Les chemins du cache AN dont le contenu vieillit, **et qui existent**.

    Les répertoires par législature ne sont retenus que pour les législatures
    non figées ; les figées restent en place, c'est tout l'intérêt de ne pas
    périmer l'entrée en bloc. Les chemins sont rendus triés, pour que le journal
    du run soit lisible et le test déterministe.
    """
    figees = legislatures_figees()
    acteurs = Path(cache_acteurs) if cache_acteurs is not None else _cp.ACTEURS_HISTORIQUE_CACHE_DIR
    par_legislature = [
        Path(chemin) if chemin is not None else defaut
        for chemin, defaut in (
            (cache_scrutins, _cp.SCRUTINS_CACHE_DIR),
            (cache_questions, _cp.QUESTIONS_CACHE_DIR),
            (cache_syceron, _cp.SYCERON_CACHE_DIR),
        )
    ]

    trouves: list[Path] = []
    if acteurs.is_dir():
        trouves.append(acteurs)
    for base in par_legislature:
        if not base.is_dir():
            continue
        for entree in base.iterdir():
            if not entree.is_dir() or not _LEGISLATURE.match(entree.name):
                continue
            if entree.name in figees:
                continue
            trouves.append(entree)
    return sorted(trouves, key=str)


@dataclass(frozen=True)
class Verdict:
    """Ce que la clé restaurée dit de l'âge du contenu qu'elle a servi."""

    etat: str
    semaine_courante: str
    semaine_restauree: Optional[str]
    cle_restauree: Optional[str]

    @property
    def perimee(self) -> bool:
        """Vrai quand le contenu restauré doit être rafraîchi.

        `INDECIDABLE` en fait partie **délibérément** : une clé dont on ne sait
        pas lire la semaine ne peut pas être déclarée fraîche. Le coût est une
        réindexation de la législature en cours ; le silence, lui, coûterait la
        fraîcheur de toutes les suivantes.
        """
        return self.etat in (PERIME, INDECIDABLE)

    def message(self) -> str:
        if self.etat == FRAIS:
            return (
                f"Cache AN restauré de la semaine courante ({self.semaine_courante}) : "
                "aucune péremption."
            )
        if self.etat == CACHE_FROID:
            return (
                f"Aucune entrée de cache AN restaurée (semaine {self.semaine_courante}) : "
                "rien à périmer, tout sera reconstruit."
            )
        if self.etat == INDECIDABLE:
            return (
                f"Clé de cache AN restaurée illisible ({self.cle_restauree!r}) : semaine "
                f"indéterminable, le contenu vivant est périmé par précaution (#555)."
            )
        return (
            f"Cache AN restauré de la semaine {self.semaine_restauree}, "
            f"or nous sommes en {self.semaine_courante} : le contenu vivant est périmé "
            "(#555). Les législatures closes sont conservées."
        )

    def niveau(self) -> str:
        return "notice" if self.etat in (FRAIS, CACHE_FROID) else "warning"


def evaluer(semaine_courante: str, cle_restauree: Optional[str]) -> Verdict:
    """Compare la semaine de la clé restaurée à la semaine courante."""
    semaine = semaine_de_la_cle(cle_restauree)
    if not (cle_restauree or "").strip():
        etat = CACHE_FROID
    elif semaine is None:
        etat = INDECIDABLE
    elif semaine == semaine_courante:
        etat = FRAIS
    else:
        etat = PERIME
    return Verdict(
        etat=etat,
        semaine_courante=semaine_courante,
        semaine_restauree=semaine,
        cle_restauree=cle_restauree or None,
    )


def perimer(chemins: Iterable[Path]) -> list[Path]:
    """Supprime les chemins passés ; rend ceux réellement supprimés.

    `ignore_errors=True` et `missing_ok=True` : la péremption est un
    rafraîchissement, jamais une raison de faire échouer un shard qui a des
    profils à publier. Un chemin qui résiste sera simplement réutilisé tel quel
    — l'état d'avant #555, pas pire.
    """
    supprimes = []
    for chemin in chemins:
        if chemin.is_dir():
            shutil.rmtree(chemin, ignore_errors=True)
        elif chemin.exists():
            chemin.unlink(missing_ok=True)
        else:
            continue
        if not chemin.exists():
            supprimes.append(chemin)
    return supprimes


def main(argv: Optional[list[str]] = None) -> int:
    parseur = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parseur.add_argument("--semaine", required=True, help="semaine ISO courante (%%G-W%%V)")
    parseur.add_argument(
        "--cle-restauree",
        default="",
        help="`cache-matched-key` du step actions/cache/restore (vide si cache froid)",
    )
    parseur.add_argument(
        "--perimer",
        action="store_true",
        help="supprime réellement les chemins périmés (job producteur uniquement)",
    )
    args = parseur.parse_args(argv)

    verdict = evaluer(args.semaine, args.cle_restauree)
    print(verdict.message())
    gha.annoter(verdict.niveau(), verdict.message())

    if not verdict.perimee:
        return 0
    if not args.perimer:
        print(
            "  Déclaration seule : ce job ne sauvegarde aucun cache AN (#505), "
            "périmer ici ferait retélécharger sans rien persister."
        )
        return 0

    chemins = chemins_perissables()
    if not chemins:
        print("  Aucun chemin périssable présent sur le disque.")
        return 0
    for chemin in perimer(chemins):
        print(f"  Périmé : {chemin}")
    print(f"  Législatures conservées (closes) : {sorted(legislatures_figees(), key=int)}")
    return 0


if __name__ == "__main__":  # pragma: no cover - point d'entrée CLI
    raise SystemExit(main())
