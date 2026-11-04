#!/usr/bin/env python3
"""Retrait nommé des signatures de cosignataire que la source ne porte plus (#1429).

Le défaut
---------
Un cosignataire qui retire sa signature après notre collecte restait publié comme
cosignataire. La collecte ne lui rend plus l'amendement, et la fusion additive
des profils — aux deux étages, brut et pivot — ne retire jamais rien : son entrée
`role_signataire: cosignataire` survivait indéfiniment, sur sa fiche et dans les
signatures de son groupe. Mesuré le 04/11/2026 sur les tranches de la XVIIe :
**10 518** des 3 550 610 signatures de cosignataire, sur **505** profils et
1 247 amendements ; vérifié contre l'archive sur le profil le plus touché
(Estelle Youssouffa : 394 signatures retirées dans l'archive, 394 désignées ici).

La preuve
---------
L'absence d'un amendement dans la collecte d'un député ne prouve rien : une
collecte peut être partielle, et c'est ce que la fusion additive protège. La
preuve est **positive** : la liste de cosignataires de la copie du **premier
signataire**, celle qui fait foi dans l'index depuis #1431
(`AmendementsIndex.listes_du_premier_signataire`). Tant que la source porte
l'amendement, cette copie est rafraîchie — et elle égalait l'archive pour
142 393 des 142 434 amendements de la XVIIe (04/11/2026). Une signature de
cosignataire que cette liste ne porte pas est retirée ; un amendement sans copie
du premier signataire n'est jamais touché.

Les deux étages
---------------
La fusion additive protège le brut ET le pivot (`docs/regles/fusion-et-index.md`) :
le retrait s'écrit aux deux, sinon le pivot réintroduirait l'entrée au run
suivant. Le profil pivot ne porte que `{amendement_id, role_signataire}` : aucun
champ dérivé n'est à recomposer. Les fiches de groupe, qui sont des agrégats, se
recomposent d'elles-mêmes à l'étape suivante.

Le contrôle de perte relève la baisse sans bloquer : `amendements` est une liste
« signalée » de `audit_diff_profils`, pas une liste stable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

from amendements_index import AmendementsIndex, cle_amendement
from json_io import ecrire_profil_json
from profil_brut import (
    chemin_socle,
    charger_profil_brut,
    ecrire_profil_brut,
    iter_amendements_du_profil,
    slugs_du_repertoire,
)

ROLE_COSIGNATAIRE = "cosignataire"


def listes_qui_font_foi(index: AmendementsIndex) -> dict[str, frozenset[str]]:
    """`{amendement_id: cosignataires}` pour les seuls amendements dont la liste
    vient de la copie du premier signataire (vide comprise)."""
    return {
        amendement_id: frozenset(index.par_id_cosignatures.get(amendement_id) or ())
        for amendement_id in index.listes_du_premier_signataire
    }


def uids_a_retirer(amendements: Iterable[Any], acteur_ref: str,
                   listes: dict[str, frozenset[str]]) -> set[str]:
    """Les `uid` des signatures de cosignataire de cet acteur que la liste du
    premier signataire ne porte plus."""
    ref = f"an:{acteur_ref}"
    retires = set()
    for brut in amendements:
        if not isinstance(brut, dict) or brut.get("role_signataire") != ROLE_COSIGNATAIRE:
            continue
        liste = listes.get(cle_amendement(brut.get("uid")))
        if liste is not None and ref not in liste:
            retires.add(brut["uid"])
    return retires


def _est_retiree(entree: Any, cles: set[str], cle: str) -> bool:
    return (isinstance(entree, dict) and entree.get("role_signataire") == ROLE_COSIGNATAIRE
            and entree.get(cle) in cles)


@dataclass
class Releve:
    profils_lus: int = 0
    profils_sans_acteur: int = 0
    #: slug -> nombre de signatures retirées
    retraits: dict[str, int] = field(default_factory=dict)
    pivots_corriges: int = 0

    @property
    def signatures(self) -> int:
        return sum(self.retraits.values())


def retirer(profils_dir: Path, pivot_dir: Path, index: AmendementsIndex,
            acteur_de: Callable[[str], Optional[str]]) -> Releve:
    """Applique le retrait aux profils bruts de `profils_dir` et à leurs pivots."""
    listes = listes_qui_font_foi(index)
    releve = Releve()
    if not listes:
        return releve
    for slug in slugs_du_repertoire(profils_dir):
        releve.profils_lus += 1
        acteur = acteur_de(slug)
        if not acteur:
            releve.profils_sans_acteur += 1
            continue
        chemin = chemin_socle(profils_dir, slug)
        uids = uids_a_retirer(iter_amendements_du_profil(chemin), acteur, listes)
        if not uids:
            continue
        profil = charger_profil_brut(chemin)
        profil["amendements"] = [a for a in profil.get("amendements") or [] if not _est_retiree(a, uids, "uid")]
        ecrire_profil_brut(profils_dir, slug, profil, acteur_ref=acteur)
        releve.retraits[slug] = len(uids)

        pivot = Path(pivot_dir) / f"{slug}.pivot.json"
        if pivot.is_file():
            with open(pivot, encoding="utf-8") as f:
                document = json.load(f)
            ids = {f"an:{uid}" for uid in uids}
            avant = len(document.get("amendements") or [])
            document["amendements"] = [
                a for a in document.get("amendements") or [] if not _est_retiree(a, ids, "amendement_id")
            ]
            if len(document["amendements"]) != avant:
                ecrire_profil_json(pivot, document)
                releve.pivots_corriges += 1
    return releve


def resume(releve: Releve) -> str:
    plus = sorted(releve.retraits.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return (
        f"Signatures de cosignataire retirées à la source (#1429) : {releve.signatures} "
        f"retirée(s) sur {len(releve.retraits)} profil(s) brut(s) "
        f"({releve.pivots_corriges} pivot(s) corrigé(s)), sur {releve.profils_lus} profil(s) lu(s)"
        + (f", dont {releve.profils_sans_acteur} sans acteur AN" if releve.profils_sans_acteur else "")
        + (". Les plus touchés : " + ", ".join(f"{s} ({n})" for s, n in plus) if plus else ".")
    )
