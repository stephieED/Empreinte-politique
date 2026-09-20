#!/usr/bin/env python3
"""tranches_amendements_figees.py — la tranche d'un membre, depuis l'archive (#691).

## Ce que ce module prépare

`raw_data/profiles/` pèse **9,7 Go, dont 8,6 Go (89 %) de tranches
d'amendements**, et ces tranches recopient l'amendement complet **chez chacun de
ses signataires**. Un amendement à 74 cosignataires est écrit dans **75
fichiers**, chacun portant la liste des 75 identifiants : 5 625 identifiants
stockés pour une information qui en compte 75. `co_signataires` représente à lui
seul **79,5 %** du poids d'une tranche.

C'est la duplication que #431 a supprimée au niveau **pivot** — chaque profil
publié n'y garde qu'un `{amendement_id, role_signataire}` — et qui n'a jamais
été touchée au niveau **brut**.

## La donnée est déjà là, deux fois

`raw_data/amendements_an_figes/` porte les **624 180** amendements des trois
législatures closes en **38 Mo** gzippés, et — c'est ce qui rend ce module
court — il porte **aussi l'inversion par acteur**, déjà faite :

    amendements.json.gz        uid → l'amendement, une seule fois
    index_par_acteur.json.gz   acteur → [{uid, role_signataire}, …]

Reconstruire la tranche d'un membre est donc une jointure, pas un calcul.

## Ce qui a été mesuré avant d'écrire ce module

**568 771 amendements, 120 profils, trois législatures : aucun écart**, champ
par champ, entre la tranche committée et sa reconstruction — à une condition,
celle du paragraphe suivant.

## Les nils XML : 8 entrées sur 624 180, et elles auraient suffi

L'archive garde un résidu de la conversion XML → JSON que la collecte, elle,
normalise :

    "date": {"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
             "@xsi:nil": "true"}

Huit entrées sur 624 180, toutes sur `date`, toutes dans les législatures 15 et
16. Sans `_normaliser_nil`, huit profils auraient porté un objet XML là où le
corpus porte `null` — un écart trop rare pour être vu à l'œil, et trop réel pour
être ignoré (§2 règle 5 : une absence est `null`, jamais autre chose).

## Ce que ce module NE fait PAS, et pourquoi

**Il ne supprime rien, et rien ne l'appelle encore.** #691 est découpé pour que
la suppression n'arrive qu'après que le lot suivant a prouvé savoir reconstruire
— sept consommateurs lisent aujourd'hui le champ `amendements` d'un profil brut,
dont un qui n'est pas une source de données mais un **garde-fou** :
`merge_profile` relit `old["amendements"]` pour qu'une collecte vide n'efface
pas ce qu'un run précédent avait collecté (`collecte-vide-necrase-jamais.md`).
Ce garde-fou-là demande une décision, pas une traduction.

**L'ordre n'est pas reproductible.** L'index par acteur range les amendements
autrement que la collecte : sur `mathilde-panot/16.json`, l'ensemble est
identique et **les 16 915 positions diffèrent**. Le contenu est le même, la
séquence non — et le manifeste de #580 porte un `ordre` qui entrelace les
tranches à la recomposition. Basculer sans traiter ce point produirait un diff
sur tous les profils au premier run, que le contrôle de perte lirait comme un
changement. C'est la question ouverte du lot suivant.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any, Optional

#: Les législatures dont l'archive est matérialisée et committée. Une
#: législature vivante n'en a pas : ses amendements bougent encore.
LEGISLATURES_FIGEES: tuple[str, ...] = ("14", "15", "16")

#: Racine des archives figées. Même chemin que
#: `candidate_profile.AN_AMENDEMENTS_FIGEES_DIR` — relatif, comme les onze
#: constantes de cache du dépôt, pour que `monkeypatch.chdir` isole les tests
#: (#721).
DIR_ARCHIVES = Path("raw_data") / "amendements_an_figes"

NOM_STORE = "amendements.json.gz"
NOM_INDEX_ACTEUR = "index_par_acteur.json.gz"

#: Mémos par législature, **et séparés par fichier**. Deux raisons, dont une
#: mesurée à la dure :
#:
#: - par législature et libérables, jamais globaux — l'archive de la XVIe pèse
#:   4,7 Go en clair et une relecture entière a déjà déclenché l'OOM killer sur
#:   un run réel (`docs/decisions/amendements-legislatures-figees.md`) ;
#: - **séparés**, parce que `signatures()` n'a besoin que de l'index par acteur
#:   (10,5 Mo pour la XVe) quand `reconstruire_tranche()` a besoin du store
#:   (5,7 Mo gzippés, plusieurs centaines en clair). Les charger ensemble
#:   faisait payer le store à tout appelant qui ne fait que compter — et un
#:   essai de marquage sur `mathilde-panot`, qui touche les législatures 15 et
#:   16, s'est fait tuer par l'OOM killer sur une machine à 7 Go.
_MEMO_STORE: dict[str, dict[str, Any]] = {}
_MEMO_ACTEURS: dict[str, dict[str, Any]] = {}


def vider_memo() -> None:
    """Libère les archives chargées — pour les tests, et pour un appelant qui
    a fini une législature avant d'attaquer la suivante."""
    _MEMO_STORE.clear()
    _MEMO_ACTEURS.clear()


def _normaliser_nil(valeur: Any) -> Any:
    """`null` XML → `None`. Voir le docstring du module : 8 entrées sur 624 180.

    Le test porte sur `@xsi:nil` et non sur la présence d'un `@xmlns:*` : c'est
    l'attribut qui **déclare** l'absence, l'autre ne fait que nommer son espace
    de noms.
    """
    if isinstance(valeur, dict) and valeur.get("@xsi:nil") == "true":
        return None
    return valeur


def chemin_archive(legislature: str, dir_archives: Optional[Path] = None) -> Path:
    return (dir_archives or DIR_ARCHIVES) / str(legislature)


def archive_disponible(legislature: str, dir_archives: Optional[Path] = None) -> bool:
    """Vrai si les deux fichiers de cette législature sont là.

    Les **deux** : le store sans l'index ne dit pas qui a signé quoi, et
    l'index sans le store ne rend que des uids. Une archive à moitié présente
    est une archive absente, et la traiter autrement produirait des tranches
    vides là où il n'y a qu'un fichier manquant (#484).
    """
    base = chemin_archive(legislature, dir_archives)
    return (base / NOM_STORE).is_file() and (base / NOM_INDEX_ACTEUR).is_file()


def _charger(
    memo: dict[str, dict[str, Any]], nom: str, legislature: str,
    dir_archives: Optional[Path],
) -> dict[str, Any]:
    cle = str(legislature)
    if cle not in memo:
        chemin = chemin_archive(cle, dir_archives) / nom
        with gzip.open(chemin, "rt", encoding="utf-8") as fichier:
            memo[cle] = json.load(fichier)
    return memo[cle]


def charger_index_acteurs(
    legislature: str, dir_archives: Optional[Path] = None
) -> dict[str, Any]:
    """`acteur → [{uid, role_signataire}, …]`. Le petit fichier.

    C'est celui-ci, et lui seul, dont a besoin quiconque veut **compter** ou
    **marquer** — pas le store des amendements.
    """
    return _charger(_MEMO_ACTEURS, NOM_INDEX_ACTEUR, legislature, dir_archives)


def charger_store(
    legislature: str, dir_archives: Optional[Path] = None
) -> dict[str, Any]:
    """`uid → l'amendement`. Le gros fichier, à ne charger que pour reconstruire."""
    return _charger(_MEMO_STORE, NOM_STORE, legislature, dir_archives)


def charger_archive(
    legislature: str, dir_archives: Optional[Path] = None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """`(store, index_par_acteur)` d'une législature figée.

    Charge **les deux**. Préférer `charger_index_acteurs` quand il ne s'agit
    que de compter : le store coûte plusieurs centaines de Mo en clair.

    Lève `FileNotFoundError` si l'archive manque : ce module ne rend jamais un
    couple vide, qui se lirait comme « ce membre n'a signé aucun amendement ».
    """
    return (
        charger_store(legislature, dir_archives),
        charger_index_acteurs(legislature, dir_archives),
    )


def _cle_acteur(acteur_ref: Any) -> Optional[str]:
    """`an:PA720892` → `PA720892`. L'index d'archive est nu, la table préfixe."""
    if not isinstance(acteur_ref, str) or not acteur_ref:
        return None
    return acteur_ref.split(":")[-1]


def signatures(
    acteur_ref: Any, legislature: str, dir_archives: Optional[Path] = None
) -> Optional[list[dict[str, str]]]:
    """`[{uid, role_signataire}, …]` de cet acteur, ou `None` s'il est inconnu.

    **`None` et `[]` ne disent pas la même chose**, et c'est tout l'intérêt du
    type de retour : `[]` est un fait — cet acteur figure dans l'archive et n'y
    a signé aucun amendement — quand `None` dit qu'on ne sait pas. Les
    confondre écrirait « aucun amendement » sur un membre simplement absent de
    l'index (§2 règle 5).
    """
    cle = _cle_acteur(acteur_ref)
    if cle is None:
        return None
    par_acteur = charger_index_acteurs(legislature, dir_archives)
    entrees = par_acteur.get(cle)
    if entrees is None:
        return None
    return [
        {"uid": e["uid"], "role_signataire": e["role_signataire"]} for e in entrees
    ]


def reconstruire_tranche(
    acteur_ref: Any, legislature: str, dir_archives: Optional[Path] = None
) -> Optional[list[dict[str, Any]]]:
    """La tranche d'amendements de ce membre, au format que la collecte écrit.

    Deux champs sont **dérivés** et non stockés dans l'archive, exactement les
    deux que #691 avait identifiés : `role_signataire`, qui vient de l'index
    par acteur, et `legislature`, que porte déjà le nom du fichier.

    Rend `None` — jamais `[]` — quand l'acteur est inconnu de l'archive.
    """
    entrees = signatures(acteur_ref, legislature, dir_archives)
    if entrees is None:
        return None
    store = charger_store(legislature, dir_archives)
    tranche: list[dict[str, Any]] = []
    for entree in entrees:
        brut = store.get(entree["uid"])
        if brut is None:
            # L'index nomme un amendement que le store ne porte pas : une
            # archive incohérente, pas un membre sans amendement. On saute
            # l'entrée plutôt que d'écrire une ligne vide, et l'appelant
            # constatera l'écart de compte.
            continue
        amendement = {champ: _normaliser_nil(valeur) for champ, valeur in brut.items()}
        amendement["role_signataire"] = entree["role_signataire"]
        amendement["legislature"] = str(legislature)
        tranche.append(amendement)
    return tranche


def mapping_pivot(
    acteur_ref: Any, legislature: str, prefixe: str = "an:",
    dir_archives: Optional[Path] = None,
) -> Optional[list[dict[str, str]]]:
    """Ce que le profil PIVOT garde d'un amendement : `{amendement_id, role_signataire}`.

    C'est la forme de #431, et l'archive la porte déjà — d'où l'existence de
    cette fonction à côté de `reconstruire_tranche` : alimenter le pivot n'a pas
    besoin de passer par la tranche. Reconstruire une liste dupliquée pour la
    dédupliquer trois lignes plus loin serait payer la duplication en calcul
    après l'avoir supprimée du disque.
    """
    entrees = signatures(acteur_ref, legislature, dir_archives)
    if entrees is None:
        return None
    return [
        {"amendement_id": f"{prefixe}{e['uid']}", "role_signataire": e["role_signataire"]}
        for e in entrees
    ]
