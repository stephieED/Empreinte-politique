#!/usr/bin/env python3
"""
couverture_dossiers.py — Périmètre réellement couvert par les archives de
dossiers législatifs ingérées (#399).

Source unique de vérité pour deux faits liés, jusqu'ici implicites dans
`gouvernement_textes.py` :

  1. **quelles archives sont ingérées** (`AN_DOSSIERS_ARCHIVES`, une par
     législature) — déplacé ici depuis `gouvernement_textes.py` (#400), qui
     le ré-exporte pour ne rien casser ;
  2. **quelle borne temporelle cela implique** — un gouvernement antérieur à
     la plus ancienne législature ingérée n'a pas « zéro texte porté », il
     est **hors couverture de la source**. Confondre les deux publierait une
     absence de source comme un fait mesuré (AGENTS.md §2.5).

Ce module est volontairement sans I/O ni dépendance non-stdlib : il est
importé par `audit_gouvernement_dataset.py` et `check_quality_gate.py`, qui
ne doivent jamais tirer `requests` ni toucher au réseau.

Concrètement, avec les archives **XIV** à XVII ingérées (#1019), la borne
recule au 2012-06-20 (première séance de la XIV) :

  - Fillon I, II et III (2007→2012, XII/XIII) restent **définitivement** hors
    couverture : leurs archives répondent 404, revérifié le 18/09/2026 ;
  - Ayrault II, Valls, Valls II, Cazeneuve et Philippe I relèvent de la XIV et
    sont désormais **couverts** — mesuré : 573 dossiers gouvernementaux, dont
    187 pour Ayrault II, 254 pour Valls II, 81 pour Cazeneuve, 44 pour Valls
    et 7 pour Philippe I ;
  - **Ayrault I reste HORS COUVERTURE**, et son `textes[]` vide ne doit pas se
    lire comme « aucun texte porté » : sa fenêtre (16/05 → 18/06/2012) se
    termine AVANT l'ouverture de la XIV, donc elle relève de la XIIIe, dont
    l'archive répond 404. C'est une absence de source (§2 règle 5), pas un
    zéro mesuré — l'erreur que ce module entier existe pour empêcher.

`statut_couverture_textes()` ne dit donc pas « il n'y a pas de texte », mais
« la source ne permet pas de l'affirmer » — la distinction que #399 demande
de rendre lisible dans les rapports et dans l'UI.

Les décisions qui gouvernent ce module
--------------------------------------
Cinq le nomment ; la liste complète et à jour est dans
`docs/decisions-par-module.md`. Ces trois-là portent le contrat :

- `docs/decisions/couverture-dossiers-hors-couverture-vs-zero.md` (#399) — la
  décision fondatrice : dériver la borne des législatures **ingérées**, pour que
  `borne_couverture_textes` / `statut_couverture_textes` cessent de publier une
  limite de source comme un « 0 texte porté » mesuré (AGENTS.md §2.5).
- `docs/decisions/dossiers-multi-archives-origine-document.md` (#400) — d'où
  vient `AN_DOSSIERS_ARCHIVES` : l'inventaire des archives, les deux conventions
  de nommage de l'AN, et pourquoi une archive multi-législature ne couvre pas
  les législatures dont elle ne garde qu'une traîne résiduelle.
- `docs/decisions/couverture-listes-539.md` — le vocabulaire voisin, côté
  profils. Le cinquième état `partielle` de ce module n'y a **volontairement**
  pas été repris ; les deux modèles doivent rester distincts.
"""

from datetime import date
from typing import Any, Optional

AN_OPENDATA_BASE = "https://data.assemblee-nationale.fr/static/openData/repository"

# Archives de dossiers législatifs, par législature (#400).
#
# Deux conventions de nommage coexistent chez l'AN — suffixe romain jusqu'à la
# XV, sans suffixe ensuite. Vérifié par requêtes réelles sur les index 11 à 18
# le 2026-08-18 : le listing de répertoire est désactivé (404 même sur les
# chemins valides), donc l'inventaire ne peut pas être découvert dynamiquement
# et doit être tenu à jour ici.
#
# La XIV est LUE depuis #1019. Ce qui était écrit ici — « structure
# incompatible, aucun `dossierParlementaire` » — était faux sur le second
# point : l'archive porte **3 432 dossiers**, chacun sous la clé
# `dossierParlementaire`, exactement comme dans le format par fichier. Ce qui
# change est l'EMBALLAGE, pas le contenu : un seul JSON de 36 Mo décompressés
# au lieu d'un fichier par objet. `gouvernement_textes._entrees_monolithiques`
# lit cette forme, et `parse_dossier_gouvernemental` traite les 3 432 sans une
# exception.
#
# Les XII et XIII, elles, restent hors d'atteinte : leurs archives répondent
# 404, revérifié le 18/09/2026. **Les gouvernements Fillon I, II et III le
# restent donc aussi** — une absence de source, déclarée et non comblée.
AN_DOSSIERS_ARCHIVES: dict[int, str] = {
    14: f"{AN_OPENDATA_BASE}/14/loi/dossiers_legislatifs/Dossiers_Legislatifs_XIV.json.zip",
    15: f"{AN_OPENDATA_BASE}/15/loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip",
    16: f"{AN_OPENDATA_BASE}/16/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip",
    17: f"{AN_OPENDATA_BASE}/17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip",
}

# ── Quelles archives peuvent encore changer (#762) ───────────────────────────
#
# Une législature DISSOUTE ne produit plus d'acte : son archive de dossiers est
# définitivement close et la retélécharger est un coût pur. La 17e, elle, est en
# cours — un texte adopté cette semaine n'apparaît que dans une archive fraîche.
#
# Cet ensemble est déclaré ICI, à côté des archives dont il parle, et non
# emprunté à `AN_SCRUTINS_LEGISLATURES_FIGEES` : les deux disent aujourd'hui la
# même chose, mais ils répondent à deux questions (quelles archives de SCRUTINS
# sont committées sous `raw_data/scrutins_an_figes/`, quelles archives de
# DOSSIERS ne bougent plus) et rien ne garantit qu'ils resteront alignés.
#
# À l'ouverture de la 18e : ajouter 17 ici, et son URL au dictionnaire ci-dessus.
# C'est la seule édition à faire — le reste s'en déduit.
#
# La 14 y entre avec #1019 : elle est dissoute depuis 2017, son archive ne
# changera plus. Un run n'a donc aucune raison de la rafraîchir.
AN_DOSSIERS_LEGISLATURES_FIGEES: frozenset[int] = frozenset({14, 15, 16})

#: Les archives qu'un run doit pouvoir rafraîchir. Dérivé, jamais écrit à la
#: main : une liste tenue en double se désaligne au premier changement.
AN_DOSSIERS_LEGISLATURES_ACTIVES: frozenset[int] = frozenset(
    AN_DOSSIERS_ARCHIVES
) - AN_DOSSIERS_LEGISLATURES_FIGEES


# Date de première séance de chaque législature ingérée — borne basse de ce
# que son archive couvre. Dates d'ouverture officielles de l'Assemblée
# nationale, déjà utilisées ailleurs dans le dépôt pour la XVI
# (`schema_groupe.py` : 2022-06-22).
#
# Ne contient que les législatures pour lesquelles une archive est ingérée :
# ajouter une entrée à `AN_DOSSIERS_ARCHIVES` sans l'ajouter ici est une
# erreur, signalée par `verifier_coherence_inventaire()`.
LEGISLATURES_DEBUT: dict[int, str] = {
    # #1019 — relue dans l'organe `ASSEMBLEE` de la 14e législature d'AMO30 le
    # 18/09/2026 (`viMoDe.dateDebut`), pas de mémoire. La même lecture
    # confirme les trois dates ci-dessous au jour près.
    14: "2012-06-20",
    15: "2017-06-21",
    16: "2022-06-22",
    17: "2024-07-18",
}

# Chiffres romains des législatures, pour les libellés lisibles.
_ROMAIN: dict[int, str] = {13: "XIII", 14: "XIV", 15: "XV", 16: "XVI", 17: "XVII", 18: "XVIII"}

# Statuts de couverture d'un gouvernement vis-à-vis des archives ingérées.
# Nomenclature fermée : toute autre valeur est un bug d'appelant.
COUVERTURE_COUVERTE = "couverte"          # période entièrement dans le périmètre
COUVERTURE_PARTIELLE = "partielle"        # période à cheval sur la borne
COUVERTURE_HORS = "hors_couverture"       # période entièrement antérieure
COUVERTURE_INDETERMINEE = "indeterminee"  # `periode.debut` absent ou illisible

# Libellés courts, pour les rapports et l'UI.
LIBELLES_COUVERTURE: dict[str, str] = {
    COUVERTURE_COUVERTE: "couverte",
    COUVERTURE_PARTIELLE: "partielle",
    COUVERTURE_HORS: "hors couverture",
    COUVERTURE_INDETERMINEE: "indéterminée",
}


def legislatures_ingerees() -> tuple[int, ...]:
    """Législatures dont l'archive de dossiers est ingérée, croissantes."""
    return tuple(sorted(AN_DOSSIERS_ARCHIVES))


def borne_couverture_textes() -> Optional[str]:
    """Date ISO à partir de laquelle les dossiers sont couverts, `None` si aucune archive.

    C'est le début de la plus ancienne législature ingérée. Rien avant cette
    date n'est garanti présent : les archives gardent une traîne résiduelle
    des législatures précédentes (voir `gouvernement_textes.py`), mais une
    absence y est ininterprétable — jamais un zéro constaté.
    """
    debuts = [
        LEGISLATURES_DEBUT[leg] for leg in legislatures_ingerees() if leg in LEGISLATURES_DEBUT
    ]
    return min(debuts) if debuts else None


def libelle_legislatures_ingerees() -> str:
    """`"XV–XVII"` (ou `"XV, XVII"` si l'inventaire a un trou), `"aucune"` si vide."""
    legislatures = legislatures_ingerees()
    if not legislatures:
        return "aucune"

    noms = [_ROMAIN.get(leg, str(leg)) for leg in legislatures]
    contigues = list(legislatures) == list(range(legislatures[0], legislatures[-1] + 1))
    if contigues and len(noms) > 1:
        return f"{noms[0]}–{noms[-1]}"
    return ", ".join(noms)


def libelle_couverture_textes() -> str:
    """Phrase d'en-tête décrivant le périmètre réellement couvert."""
    borne = borne_couverture_textes()
    if borne is None:
        return "aucune archive de dossiers législatifs ingérée"
    return (
        f"législatures {libelle_legislatures_ingerees()} "
        f"(dossiers déposés à partir du {borne})"
    )


def _parse_date(valeur: Any) -> Optional[date]:
    """Parse une date ISO `YYYY-MM-DD`, `None` si absente ou illisible."""
    if not isinstance(valeur, str) or not valeur:
        return None
    try:
        return date.fromisoformat(valeur[:10])
    except ValueError:
        return None


def statut_couverture_textes(periode_debut: Any, periode_fin: Any) -> str:
    """Classe la période d'un gouvernement vis-à-vis des archives ingérées.

    Args:
        periode_debut: `periode.debut` du profil (ISO `YYYY-MM-DD`).
        periode_fin: `periode.fin`. `None` (gouvernement en cours) est une
            absence légitime, jamais remplacée par la date du jour
            (AGENTS.md §2.5) : la période est alors traitée comme ouverte,
            donc atteignant le périmètre couvert.

    Returns:
        Une des constantes `COUVERTURE_*` :
          - `COUVERTURE_COUVERTE` : période entièrement à partir de la borne —
            un `textes[]` vide y est un zéro réellement constaté ;
          - `COUVERTURE_PARTIELLE` : période commencée avant la borne et se
            prolongeant après — un `textes[]` vide y reste ininterprétable ;
          - `COUVERTURE_HORS` : période entièrement antérieure à la borne —
            l'absence de texte est une absence de source, pas un fait ;
          - `COUVERTURE_INDETERMINEE` : `periode.debut` absent ou illisible,
            rien ne peut être affirmé.
    """
    borne = _parse_date(borne_couverture_textes())
    debut = _parse_date(periode_debut)

    if debut is None or borne is None:
        return COUVERTURE_INDETERMINEE
    if debut >= borne:
        return COUVERTURE_COUVERTE

    fin = _parse_date(periode_fin)
    if periode_fin is not None and fin is None:
        # `fin` présent mais illisible : on ne devine pas (AGENTS.md §2.5).
        return COUVERTURE_INDETERMINEE
    if fin is None:
        # Gouvernement en cours, commencé avant la borne : à cheval.
        return COUVERTURE_PARTIELLE
    return COUVERTURE_HORS if fin < borne else COUVERTURE_PARTIELLE


def verifier_coherence_inventaire() -> list[str]:
    """Erreurs d'inventaire : archive ingérée sans date de début connue.

    Garde-fou pour les tests — ajouter une législature à
    `AN_DOSSIERS_ARCHIVES` sans l'ajouter à `LEGISLATURES_DEBUT` fausserait
    silencieusement la borne de couverture.
    """
    return [
        f"législature {leg} ingérée mais absente de LEGISLATURES_DEBUT."
        for leg in legislatures_ingerees()
        if leg not in LEGISLATURES_DEBUT
    ]
