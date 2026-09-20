#!/usr/bin/env python3
"""
gouvernement_roster.py — Composition ministérielle d'un gouvernement, dérivée
des profils pivot individuels déjà collectés.

Aucun appel réseau : ce module ne fait que parcourir les pivots individuels
(`pivot_data/profiles/*.pivot.json`) déjà présents sur disque et en extraire
les mandats `categorie == "fonction_gouvernementale"` (peuplés depuis
`AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`, voir
`candidate_profile.py`) qui appartiennent au gouvernement demandé.

Désambiguïsation : l'AN n'expose que `organe.libelleAbrege` (ex. "BORNE",
"LECORNU II") dans `mandats[].label` ("Gouvernement (<libelleAbrege>)"), ce
qui peut être ambigu entre deux gouvernements homonymes lors d'un
remaniement. La sélection d'un membre requiert donc :
  1. une correspondance exacte du libellé (`libelle_an`, tel que renseigné
     manuellement dans `raw_data/gouvernements_reels.json` — même principe de
     désambiguïsation éditoriale humaine que `groupes_reels.json`) ;
  2. un chevauchement de la période du mandat avec la période du gouvernement
     (garde-fou supplémentaire contre une anomalie de données, pas le critère
     principal — voir `_mandate_matches_gouvernement`).
Un mandat dont le libellé correspond mais dont la période ne chevauche pas du
tout celle du gouvernement est exclu (anomalie de données jugée plus sûre à
ignorer qu'à inclure) ; symétriquement, un mandat dont la période chevauche
mais dont le libellé diffère (autre gouvernement) est exclu — c'est
précisément le cas qui justifie de ne pas se fier à la seule période.

Même pattern que `group_profile._derive_membre_entry` (`src/group_profile.py`)
pour la dérivation des champs (nom, dates, statut actif) : un enregistrement
par mandat correspondant, donc potentiellement plusieurs entrées pour un même
membre si son mandat a été scindé en plusieurs périodes (changement de
portefeuille en cours de gouvernement) — cf. `schema_gouvernement.py`, qui
documente ce même principe pour `membres[]`.

`portefeuille` (#398) vient des mandats `typeOrgane == "MINISTERE"` exposés
par le même zip AMO30 et mappés en `fonction_gouvernementale` depuis #382/#383
(« Ministère de l'éducation nationale et de la jeunesse », « Secrétariat
d'État auprès du Premier ministre… »). Le label sépare ces mandats de ceux
d'appartenance (`_est_mandat_appartenance_gouvernement`), mais il ne suffit
**pas** à établir qu'il s'agit d'un maroquin : un *parlementaire en mission*
(art. LO144) porte lui aussi un mandat `MINISTERE`, dont le label est
l'intitulé du ministère **auprès duquel** il est missionné. Seule
`mandats[].fonction` les sépare — d'où `_qualite_portefeuille` et la liste
blanche `FONCTIONS_MINISTERIELLES` (#474). Un portefeuille n'est donc retenu
que s'il porte une qualité ministérielle connue **et** qu'il chevauche à la
fois le mandat d'appartenance du membre et la période du gouvernement ; tous
les portefeuilles ainsi retenus le sont : un ministre qui change de
portefeuille en cours de gouvernement produit une entrée `membres[]` par
période, jamais un portefeuille choisi arbitrairement parmi les siens.
`portefeuille` retombe à `null` (avec un warning) si aucune `source_url`
n'est traçable, le schéma l'exigeant dès que l'intitulé est renseigné. La
limite inverse est levée : `docs/decisions/hors-perimetre.md`
§ "Ministerial function" est marquée RÉSOLU.

`premier_ministre` (#398, `build_premier_ministre`) se dérive du même
matériau : le membre du gouvernement dont un mandat `MINISTERE` porte un
libellé d'organe de chef du gouvernement **et** la qualité « Premier
ministre » (le label seul ne suffit pas : une mission auprès du Premier
ministre porte le même — #474). Les deux champs viennent d'endroits
différents de la source et **ne s'accordent pas en genre** : le libellé
d'organe s'accorde (« Première ministre » pour Élisabeth Borne), la qualité
non (« Premier ministre » au masculin dans les 1 162 mandats `MINISTERE` de
l'archive). D'où une liste fermée et datée côté libellé,
`LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES`, et jamais une règle de genre
(#658). Aucun appariement par la seule période, aucune déduction depuis le nom
du gouvernement — voir la docstring de la fonction.

Hors périmètre de ce module (sous-issue #5 de #184) :
  - Collecte des textes législatifs portés par le gouvernement.
  - Écriture d'un fichier `pivot_data/gouvernements/*.json` conforme au
    schéma complet `schema_gouvernement.py` (textes, comptages...) : ce module
    ne produit que `membres[]` et l'entrée `premier_ministre`.

Usage (depuis la racine du dépôt) :
    python src/gouvernement_roster.py \\
        --config raw_data/gouvernements_reels.json \\
        --gouvernement-id "gouvernement:LECORNU_II" \\
        --profiles-dir pivot_data/profiles
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Helpers de dates
# ---------------------------------------------------------------------------

def _parse_date(s: Any) -> Optional[date]:
    """Parse une chaîne ISO-8601 (YYYY-MM-DD ou sous-préfixe) en date, sans lever."""
    if not s or not isinstance(s, str):
        return None
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _periods_overlap(
    m_debut: Optional[date],
    m_fin: Optional[date],
    g_debut: Optional[date],
    g_fin: Optional[date],
) -> bool:
    """Teste le chevauchement de deux intervalles [debut, fin], bornes ouvertes si None.

    None en fin signifie « toujours en cours » ; None en début signifie
    « origine inconnue ». Une date manquante d'un côté ne permet jamais
    d'exclure : seule une incompatibilité explicite (une borne connue qui
    précède/suit strictement l'autre intervalle) exclut le chevauchement.
    """
    if m_debut is not None and g_fin is not None and m_debut > g_fin:
        return False
    if m_fin is not None and g_debut is not None and m_fin < g_debut:
        return False
    return True


# ---------------------------------------------------------------------------
# Sélection des mandats fonction_gouvernementale
# ---------------------------------------------------------------------------

def _expected_label(libelle_an: str) -> str:
    """Reconstruit le libellé attendu de mandats[].label pour un gouvernement.

    Miroir exact de la construction faite côté collecte
    (`candidate_profile.py`, § positions dans l'hémicycle) : `"Gouvernement
    (<libelleAbrege>)"`, ou `"Gouvernement"` seul si le sigle est absent.
    """
    return f"Gouvernement ({libelle_an})" if libelle_an else "Gouvernement"


def _est_mandat_appartenance_gouvernement(label: str) -> bool:
    """Distingue les deux `typeOrgane` réunis dans `fonction_gouvernementale`.

    La catégorie en mélange deux, issues du même zip AMO30 mais de deux
    `typeOrgane` différents (voir `candidate_profile._TYPE_ORGANE_TO_CATEGORIE`) :
      - `GOUVERNEMENT` : l'appartenance au gouvernement, label « Gouvernement
        (<libelleAbrege>) » — c'est le mandat qui rattache un membre à CE
        gouvernement (`_mandate_matches_gouvernement`) ;
      - `MINISTERE` : un mandat rattaché à un ministère, label « Ministère
        de… », « Secrétariat d'État… », « Premier ministre » (#382/#383).

    Pour cette séparation-là, le label est bien le seul discriminant :
    `categorie` est identique pour les deux, et `position_dans_hemicycle`
    n'est renseigné que sur les premiers.

    Ce que le label ne dit **pas** (#474) : qu'un mandat `MINISTERE` soit un
    portefeuille. Un parlementaire en mission (art. LO144) porte le même type
    de mandat, avec pour label l'intitulé du ministère **auprès duquel** il
    est missionné — strictement indiscernable d'un maroquin sur ce seul
    critère. Cette seconde distinction se lit dans `mandats[].fonction` :
    voir `_qualite_portefeuille`.
    """
    return label == "Gouvernement" or (
        label.startswith("Gouvernement (") and label.endswith(")")
    )


# ---------------------------------------------------------------------------
# Qualité du mandat MINISTERE : maroquin ou mission ? (#474)
# ---------------------------------------------------------------------------

# `mandats[].fonction` reprend `infosQualite.libQualite` du zip AMO30
# (`candidate_profile._build_acteur_mandats_index`, renommé `type` →
# `fonction` par `normalize_profil`). C'est le seul champ qui sépare un
# portefeuille ministériel d'un mandat de parlementaire en mission.
#
# Liste BLANCHE, pas liste noire de « en mission » (#474, AGENTS.md §2.5) :
# une liste noire laisserait passer silencieusement toute qualité non prévue
# et la publierait comme un maroquin. La liste blanche, elle, fait retomber
# l'inconnu sur « portefeuille non renseigné » **avec un warning** — une
# donnée manquante, jamais une donnée par défaut.
#
# Les valeurs ci-dessous sont celles observées sur les 209 profils du dépôt au
# 2026-08-20 (`pivot_data/profiles/`) ; le corpus cible en compte ~752, donc
# d'autres qualités apparaîtront. Le geste de maintenance attendu est alors
# d'ajouter la valeur ici après vérification humaine — même principe éditorial
# que `raw_data/gouvernements_reels.json` — en s'appuyant sur le warning, qui
# nomme la personne, l'intitulé et la qualité rencontrée.
#
# Balayage exhaustif du 2026-08-31 (#658), sur la source elle-même plutôt que
# sur les profils publiés : `.cache/acteurs_historique_an/acteurs_historique.zip`,
# 3 117 fiches acteur, 1 162 mandats `typeOrgane == "MINISTERE"`. Il porte
# **9 valeurs distinctes de `libQualite`, et pas une seule au féminin** — la
# liste ci-dessous les couvre toutes sauf une, `FONCTIONS_NON_MINISTERIELLES_OBSERVEES`
# prenant la dernière (« en mission », 396 mandats). La conclusion qui compte
# pour #658 : le genre ne se joue **jamais** sur `libQualite` — une ministre
# déléguée y porte « Ministre délégué » — mais sur le libellé d'organe, voir
# `LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES`.
#
# « Haut-commissaire » est la seule valeur que ce balayage a ajoutée à la
# liste. Le motif est une **lecture du référentiel, pas une appréciation
# institutionnelle** : ses 4 mandats (2 personnes) sont rangés par AMO30 sous
# `typeOrgane == "MINISTERE"`, aux côtés des ministres et secrétaires d'État,
# et l'organe de rattachement porte lui aussi `codeType == "MINISTERE"` dans
# les quatre cas. Celui de Jean-Paul Delevoye est même littéralement intitulé
# « Ministère ». Ce n'est donc pas nous qui qualifions ces mandats de
# maroquins, c'est l'Assemblée nationale — ce qui satisfait §2 règle 2 là où
# un avis extérieur ne l'aurait pas fait.
#
#   PA1051    Jean-Paul Delevoye  PO766969  « Ministère des solidarités et de
#                                 la santé – Retraites »  2019-09-04 → 2019-12-17
#   PA387853  Martin Hirsch       PO383001  « Haut-commissariat aux solidarités
#                                 actives contre la pauvreté »  2007-05-18 → 2007-06-18
#   PA387853  Martin Hirsch       PO388139  (même intitulé)  2007-06-19 → 2009-01-12
#   PA387853  Martin Hirsch       PO418119  « … et Haut-commissariat à la
#                                 jeunesse »  2009-01-12 → 2010-03-22
#
# Effet mesuré à l'ajout : **0 mandat et 0 personne** changent de classement
# sur les 481 profils publiés (aucun des deux acteurs n'a de profil pivot),
# donc **0 fiche de gouvernement** bouge. L'ajout est un pré-positionnement :
# le jour où l'un des deux obtient un profil, son portefeuille sera publié au
# lieu de retomber `null` avec un warning.
FONCTIONS_MINISTERIELLES_OBSERVEES: tuple[str, ...] = (
    "Premier ministre",
    "Ministre",
    "Ministre délégué",
    "Secrétaire d'État",
    "Ministre d'État, ministre",
    "Garde des sceaux, ministre de la justice",
    "Ministre d'État, Garde des Sceaux, ministre de la justice",
    "Haut-commissaire",
)

# Qualités connues qui ne sont PAS un portefeuille : exclues sans warning,
# leur exclusion étant le comportement attendu et non une anomalie. 92 des
# 209 profils portent au moins un mandat « en mission ».
FONCTIONS_NON_MINISTERIELLES_OBSERVEES: tuple[str, ...] = (
    "en mission",
)

# Qualité exacte du chef du gouvernement (`build_premier_ministre`).
FONCTION_PREMIER_MINISTRE = "Premier ministre"


def _normalise_typographique(valeur: Any) -> str:
    r"""Casse et espaces, rien d'autre — le socle commun des deux normalisations.

    Purement typographique, jamais sémantique. Les espaces incluent
    l'insécable (`\xa0`), que la source AN pose dans certains libellés
    d'organe (« Ministère\xa0de\xa0l'économie… », 6 mandats `MINISTERE` de
    l'archive AMO30 au 2026-08-31) : `\s` le couvre en mode Unicode.
    """
    if not isinstance(valeur, str):
        return ""
    return re.sub(r"\s+", " ", valeur).strip().casefold()


def _normalise_fonction(fonction: Any) -> str:
    """Normalise une `mandats[].fonction` pour comparaison : casse et espaces.

    Purement typographique, jamais sémantique — la source mélange déjà « Garde
    des sceaux » et « Garde des Sceaux » sur la même qualité. Aucune
    troncature, aucun rapprochement par préfixe : deux libellés distincts
    restent distincts. En particulier, **aucun rapprochement de genre** : le
    balayage de #658 a montré que `libQualite` ne porte de toute façon jamais
    de forme féminine (9 valeurs distinctes sur les 1 162 mandats `MINISTERE`
    de l'archive, toutes au masculin — c'est le *libellé d'organe* qui
    s'accorde, voir `LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES`).
    """
    return _normalise_typographique(fonction)


def _normalise_libelle_organe(libelle: Any) -> str:
    """Même normalisation, appliquée à un `mandats[].label` (libellé d'organe).

    Deux fonctions et non une seule appliquée partout : les deux champs
    viennent d'endroits différents de la source (`infosQualite.libQualite`
    d'un côté, `organe.libelle` de l'autre) et ne s'accordent pas en genre
    (#658). Les nommer séparément rend cette asymétrie lisible au lieu de la
    laisser se deviner à l'appel.
    """
    return _normalise_typographique(libelle)


FONCTIONS_MINISTERIELLES: frozenset[str] = frozenset(
    _normalise_fonction(f) for f in FONCTIONS_MINISTERIELLES_OBSERVEES
)
FONCTIONS_NON_MINISTERIELLES: frozenset[str] = frozenset(
    _normalise_fonction(f) for f in FONCTIONS_NON_MINISTERIELLES_OBSERVEES
)

QUALITE_MINISTERIELLE = "ministerielle"
QUALITE_NON_MINISTERIELLE = "non_ministerielle"
QUALITE_INCONNUE = "inconnue"


def _qualite_portefeuille(fonction: Any) -> str:
    """Classe la `fonction` d'un mandat `MINISTERE` en trois états (#474).

    Trois états et non deux : « inconnue » n'est ni un portefeuille ni une
    exclusion de routine, c'est une donnée non résolue qui doit se voir et se
    corriger (§2.5). Un `fonction` absent (`None`) est traité comme inconnu —
    `normalize_profil` le remplace par « membre » quand la source ne
    renseigne pas `libQualite`, ce qui, sur un mandat `MINISTERE`, est
    précisément une lacune de source, pas une qualité.
    """
    normalisee = _normalise_fonction(fonction)
    if normalisee in FONCTIONS_MINISTERIELLES:
        return QUALITE_MINISTERIELLE
    if normalisee in FONCTIONS_NON_MINISTERIELLES:
        return QUALITE_NON_MINISTERIELLE
    return QUALITE_INCONNUE


def _ajouter_warning(warnings: Optional[list[str]], message: str) -> None:
    """Consigne un warning sans doublon.

    Le même mandat est réexaminé une fois par mandat d'appartenance du même
    profil (un membre peut en porter plusieurs pour un même gouvernement, cf.
    #474) et une seconde fois par `build_premier_ministre`, qui partage la
    liste de warnings du roster : sans déduplication, le même fait serait
    consigné trois ou quatre fois dans `meta.warnings`.
    """
    if warnings is None or message in warnings:
        return
    warnings.append(message)


def _mandats_portefeuille(profil: dict[str, Any]) -> list[dict[str, Any]]:
    """Mandats `MINISTERE` d'un profil : les mandats `fonction_gouvernementale`
    dont le label n'est pas celui d'une appartenance.

    Filtre de `typeOrgane` uniquement : ces mandats ne sont pas encore des
    portefeuilles (un parlementaire en mission en porte aussi). Le tri
    maroquin/mission se fait dans `_portefeuilles_du_mandat`, sur `fonction`.
    """
    return [
        mandat
        for mandat in (profil.get("mandats") or [])
        if mandat.get("categorie") == "fonction_gouvernementale"
        and not _est_mandat_appartenance_gouvernement(mandat.get("label") or "")
    ]


def _portefeuilles_du_mandat(
    profil: dict[str, Any],
    mandat_gouvernemental: dict[str, Any],
    g_debut: Optional[date],
    g_fin: Optional[date],
    warnings: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Portefeuilles ministériels rattachables à un mandat d'appartenance donné,
    triés par date de début (l'ordre chronologique de la source).

    Trois conditions cumulatives, toutes nécessaires :

    1. chevauchement avec la période du **mandat** du membre — un ministre
       entré en cours de mandature ne doit pas se voir attribuer le
       portefeuille qu'il occupait avant ;
    2. chevauchement avec la période du **gouvernement** (#474). La condition 1
       ne suffit pas : une source peut laisser ouvert (`fin: null`) un mandat
       d'appartenance à un gouvernement pourtant clos, et ce mandat sans fin
       accroche alors n'importe quel mandat ministériel postérieur. C'est
       exactement ce qui a publié un portefeuille daté du 2026-02-04 dans un
       gouvernement achevé le 2025-09-09. Cette condition ne fait que
       restreindre : elle ne peut pas rattraper un portefeuille que la
       condition 1 écarte, donc le garde-fou de #398 reste entier.
    3. qualité ministérielle connue (`_qualite_portefeuille`) — un mandat de
       parlementaire en mission porte le nom du ministère auprès duquel la
       personne est missionnée, il n'est pas un maroquin.
    """
    m_debut = _parse_date(mandat_gouvernemental.get("debut"))
    m_fin = _parse_date(mandat_gouvernemental.get("fin"))

    retenus: list[dict[str, Any]] = []
    for portefeuille in _mandats_portefeuille(profil):
        p_debut = _parse_date(portefeuille.get("debut"))
        p_fin = _parse_date(portefeuille.get("fin"))
        if not _periods_overlap(p_debut, p_fin, m_debut, m_fin):
            continue
        if not _periods_overlap(p_debut, p_fin, g_debut, g_fin):
            continue

        qualite = _qualite_portefeuille(portefeuille.get("fonction"))
        if qualite == QUALITE_MINISTERIELLE:
            retenus.append(portefeuille)
        elif qualite == QUALITE_INCONNUE:
            _ajouter_warning(
                warnings,
                f"gouvernement_roster: {profil.get('nom') or profil.get('id')} : "
                f"qualité de mandat {portefeuille.get('fonction')!r} inconnue sur "
                f"{portefeuille.get('label')!r} — ni ministérielle connue, ni "
                f"mission : portefeuille non renseigné. Compléter "
                f"FONCTIONS_MINISTERIELLES_OBSERVEES après vérification (#474).",
            )

    return sorted(retenus, key=lambda p: p.get("debut") or "")


def _mandate_matches_gouvernement(
    mandat: dict[str, Any],
    libelle_an: str,
    g_debut: Optional[date],
    g_fin: Optional[date],
    est_membre_declare: Optional[bool] = None,
) -> bool:
    """Détermine si un mandat individuel appartient au gouvernement ciblé.

    **Deux voies, et la première est celle qu'on veut (#996 lot 4).**

    `est_membre_declare` fourni — le roster AMO30 a déjà tranché
    l'appartenance, sur `organe_ref`. Il reste à retenir les mandats
    d'appartenance du profil, et **la période du gouvernement** les départage :
    un ministre reconduit porte un mandat par gouvernement, et la période de
    l'organe est bornée.

    **Pourquoi le garde temporel est la période DU GOUVERNEMENT et non celle
    que le roster déclare.** AMO30 publie des périodes d'appartenance non
    bornées : Amélie de Montchalin porte deux périodes `BAYROU`, dont une
    `2024-12-24 → None` (relevé le 18/09/2026). Cette borne ouverte recouvre
    ses mandats `LECORNU` et `LECORNU II` suivants, et lui attribuait 4 entrées
    de Lecornu sur la fiche Bayrou. La période de l'organe, elle, est bornée
    par le référentiel — c'est elle qui fait foi.

    `est_membre_declare` absent — repli historique : correspondance exacte du
    libellé, puis chevauchement de période. Conservé pour qu'un run sans
    artifact de roster continue de produire les fiches (§2 règle 5 : mieux vaut
    la voie fragile que pas de fiche), et **seulement** pour ça.

    Pourquoi la première voie existe : le repli compare deux chaînes qui
    viennent de **deux sources différentes** — `libelle_an` de l'organe AMO30
    (`gouvernements_amo30.py`), `mandats[].label` de l'endpoint « positions
    dans l'hémicycle » (`candidate_profile.py`). Elles s'accordent au
    18/09/2026, écart `+0` sur les 650 personnes des 17 fiches, mais rien ne
    l'impose : une divergence retirerait des membres sans qu'aucune étape
    n'échoue. La voie roster joint sur un identifiant, dans une seule source.
    → `docs/decisions/rattachement-des-membres-par-organe-996.md`
    """
    if mandat.get("categorie") != "fonction_gouvernementale":
        return False

    m_debut = _parse_date(mandat.get("debut"))
    m_fin = _parse_date(mandat.get("fin"))

    if est_membre_declare is not None:
        if not est_membre_declare:
            return False
        # Le mandat doit être celui d'APPARTENANCE, pas un `MINISTERE` : les
        # deux portent `fonction_gouvernementale`, et c'est le portefeuille
        # qu'on irait chercher deux fois sinon. Le libellé sert ici à séparer
        # les DEUX TYPES D'ORGANE, pas à identifier le gouvernement — et il
        # accepte donc `"Gouvernement"` nu, que l'égalité stricte du repli
        # rejette : Damien Abad et Yaël Braun-Pivet en portent un sous Borne.
        label = mandat.get("label") or ""
        if not _est_mandat_appartenance_gouvernement(label):
            return False
        # Le libellé garde UN rôle, et un seul : départager les mandats
        # d'appartenance DE CETTE PERSONNE. Un `Gouvernement (<autre sigle>)`
        # est le mandat d'un autre gouvernement et se rejette ici — sans quoi
        # deux gouvernements qui se touchent d'un jour (`FILLON 1` finit le
        # 2007-06-18, `FILLON 2` commence le 2007-06-18) se volent leurs
        # entrées : +19 sur Fillon II et +27 sur Valls II, mesuré le
        # 18/09/2026. Le chevauchement de période ne peut pas les séparer,
        # puisqu'ils se chevauchent réellement, d'un jour.
        #
        # Ce n'est PAS la jointure inter-sources que ce lot retire : elle
        # décidait de l'APPARTENANCE — un libellé divergent faisait disparaître
        # la personne. Ici la personne est déjà retenue par le roster, et le
        # libellé ne trie que ses propres mandats, tous issus du même endpoint.
        # Si aucun ne porte le sigle attendu, le repli ci-dessous la garde.
        if label != "Gouvernement" and label != _expected_label(libelle_an):
            return False
        # `"Gouvernement"` nu : la source n'a pas donné de sigle. Le roster
        # déclare la personne membre de CE gouvernement, la période le
        # confirme — l'égalité stricte du repli, elle, le jetait. Damien Abad
        # et Yaël Braun-Pivet en portent un sous Borne.
        return _periods_overlap(m_debut, m_fin, g_debut, g_fin)

    if (mandat.get("label") or "") != _expected_label(libelle_an):
        return False
    return _periods_overlap(m_debut, m_fin, g_debut, g_fin)


def slugs_du_gouvernement(
    membres_roster: Optional[list[dict[str, Any]]], organe_ref: Optional[str]
) -> Optional[set[str]]:
    """Les slugs que le roster AMO30 déclare membres de CE gouvernement.

    Entrée : la valeur de la clé `gouvernements` de `rosters_bruts.json`, telle
    que `gouvernement_roster_an.deriver_membres` la rend — une entrée par
    personne, avec `mandat_periodes[]` portant chacune son `organe_ref`.

    Rend `None` — et non un ensemble vide — quand le roster ou l'`organe_ref`
    manque : `None` dit « pas de roster, prends le repli », un ensemble vide
    dirait « ce gouvernement n'a aucun membre », ce qui viderait la fiche
    (§2 règle 5). La distinction est la raison d'être de ce type de retour.

    **Seules les appartenances sont rendues, pas leurs dates** : les dates que
    le roster déclare ne sont pas toutes bornées (voir
    `_mandate_matches_gouvernement`), et c'est la période de l'organe qui sert
    de garde temporel.
    """
    if not membres_roster or not organe_ref:
        return None
    return {
        membre["slug"]
        for membre in membres_roster
        if membre.get("slug")
        and any((p or {}).get("organe_ref") == organe_ref
                for p in (membre.get("mandat_periodes") or []))
    }


# ---------------------------------------------------------------------------
# Construction du roster
# ---------------------------------------------------------------------------

def _source_url_portefeuille(
    portefeuille: dict[str, Any], mandat_gouvernemental: dict[str, Any]
) -> Optional[str]:
    """URL traçant l'intitulé du portefeuille, ou None si aucune n'est
    disponible — auquel cas le portefeuille n'est pas renseigné du tout.

    Les mandats `MINISTERE` sortent de `candidate_profile._extract_mandats_officiels`
    sans `source_url` (aucun mandat de ce chemin n'en porte). Le repli est le
    `source_url` du mandat d'appartenance du même membre : les deux mandats
    proviennent du **même** zip AMO30 (`AN_ACTEURS_HISTORIQUE_ZIP_URL`), le
    second se contentant de le porter explicitement. Ce n'est donc pas une URL
    inventée pour satisfaire le validateur, c'est la source réelle de l'intitulé.
    """
    return portefeuille.get("source_url") or mandat_gouvernemental.get("source_url")


# Champs qui *identifient* un fait publié dans `membres[]` : qui, quel
# portefeuille, sur quelle période, encore en cours ou non. `nom` et
# `source_url` n'en font pas partie — le premier se déduit de `membre_id`, le
# second trace le fait sans le définir (#480).
CHAMPS_IDENTITE_MEMBRE: tuple[str, ...] = (
    "membre_id", "portefeuille", "debut", "fin", "actif",
)


def _dedupliquer_membres(
    membres: list[dict[str, Any]], warnings: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    """Retire les entrées `membres[]` strictement identiques à une précédente,
    en conservant l'ordre d'apparition (#480).

    Même raisonnement que la déduplication des candidats de
    `build_premier_ministre` : un même profil peut porter **plusieurs mandats
    d'appartenance au même gouvernement**, et un portefeuille qui chevauche les
    deux est alors émis deux fois. Ce sont des doublons, pas deux faits.

    La déduplication est volontairement **stricte** — l'entrée entière, pas la
    seule identité. `membres[]` compte un enregistrement « par ministre et par
    période si changement de portefeuille » (`schema_gouvernement.py`) : deux
    entrées d'une même personne sur des portefeuilles ou des périodes distincts
    sont deux faits vérifiables, que fondre effacerait (AGENTS.md §2.2). Sur le
    corpus au 20/08/2026, 18 des 20 entrées surnuméraires sont de cette nature ;
    seules 2 sont des répétitions.

    Cas non résolu, jamais tranché en silence (§2.5) : deux entrées identiques
    sur `CHAMPS_IDENTITE_MEMBRE` mais divergentes ailleurs — typiquement deux
    `source_url` différentes. Aucune des deux n'est plus traçable que l'autre :
    en choisir une serait arbitraire, et les fondre perdrait une source. Les
    deux sont donc conservées, avec un warning. Le cas ne se présente pas sur le
    corpus actuel (les deux mandats scindés portent la même URL AMO30) ; le
    warning est là pour qu'il ne passe pas inaperçu s'il apparaissait.
    """
    uniques: list[dict[str, Any]] = []
    for membre in membres:
        if membre in uniques:
            continue
        identite = tuple(membre.get(champ) for champ in CHAMPS_IDENTITE_MEMBRE)
        jumeau = next(
            (
                autre for autre in uniques
                if tuple(autre.get(champ) for champ in CHAMPS_IDENTITE_MEMBRE) == identite
            ),
            None,
        )
        if jumeau is not None:
            _ajouter_warning(
                warnings,
                f"gouvernement_roster: {membre.get('nom') or membre.get('membre_id')} : "
                f"deux entrées de même identité ({membre.get('portefeuille')!r}, "
                f"{membre.get('debut')} → {membre.get('fin')}) divergent hors identité "
                f"(source_url {jumeau.get('source_url')!r} vs {membre.get('source_url')!r}) "
                f"— les deux sont conservées, aucune n'étant plus traçable que l'autre (#480).",
            )
        uniques.append(membre)
    return uniques


def _derive_membre_entry(
    profil: dict[str, Any],
    mandat: dict[str, Any],
    portefeuille: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Dérive une entrée `membres[]` (schéma `schema_gouvernement.py`) à partir
    d'un profil pivot et d'un mandat `fonction_gouvernementale` déjà sélectionné.

    Avec un `portefeuille` (mandat `MINISTERE` chevauchant, #398), l'entrée
    porte l'intitulé précis et **les dates du portefeuille**, pas celles du
    mandat d'appartenance : c'est ce que décrit `schema_gouvernement.py` par
    « un enregistrement par ministre et par période si changement de
    portefeuille ». Sans portefeuille, le comportement d'origine est conservé
    (dates du mandat d'appartenance, `portefeuille`/`source_url` à `null`).
    """
    if portefeuille is None:
        return {
            "membre_id": profil.get("id") or "",
            "nom": profil.get("nom") or "",
            "portefeuille": None,
            "debut": mandat.get("debut"),
            "fin": mandat.get("fin"),
            "actif": bool(mandat.get("actif")),
            "source_url": None,
        }

    return {
        "membre_id": profil.get("id") or "",
        "nom": profil.get("nom") or "",
        "portefeuille": portefeuille.get("label"),
        "debut": portefeuille.get("debut"),
        "fin": portefeuille.get("fin"),
        "actif": bool(portefeuille.get("actif")),
        "source_url": _source_url_portefeuille(portefeuille, mandat),
    }


def build_gouvernement_roster(
    libelle_an: str,
    periode_debut: Optional[str],
    periode_fin: Optional[str],
    profils: list[dict[str, Any]],
    warnings: Optional[list[str]] = None,
    slugs_roster: Optional[set[str]] = None,
) -> list[dict[str, Any]]:
    """Construit la liste `membres[]` d'un gouvernement à partir de profils pivot.

    Args:
        libelle_an: `organe.libelleAbrege` du gouvernement tel qu'il apparaît
                    dans `mandats[].label` (ex. "LECORNU II", "BAYROU"), tel
                    que renseigné dans `raw_data/gouvernements_reels.json`.
        periode_debut: début de la période du gouvernement (YYYY-MM-DD), ou None.
        periode_fin: fin de la période du gouvernement (YYYY-MM-DD), ou None
                     si le gouvernement est toujours en fonction.
        profils: liste de profils pivot v1 (déjà chargés depuis
                 `pivot_data/profiles/*.pivot.json`).
        warnings: liste optionnelle où consigner les anomalies : portefeuille
                  trouvé mais non traçable, qualité de mandat inconnue (#474),
                  et deux entrées de même identité divergentes hors identité
                  (#480, voir `_dedupliquer_membres`). Même motif que
                  `candidate_profile.fetch_amendements_officiels` ; remontée
                  dans `meta.warnings` du profil de gouvernement par
                  `gouvernement_profile.build_gouvernement_profile`, donc
                  visible dans le jeu de données publié.
        slugs_roster: les slugs que `slugs_du_gouvernement` tire du roster
                  AMO30 pour CE gouvernement (#996 lot 4). Fourni, il
                  **remplace** la correspondance de libellé : l'appartenance
                  est jointe sur `organe_ref`, dans une seule source. `None` —
                  et non un ensemble vide — rebranche le repli historique ; la
                  distinction compte, un ensemble vide viderait la fiche au
                  lieu de la laisser telle quelle.

    Returns:
        Liste de dicts conformes à la structure `membres[]` de
        `schema_gouvernement.py`, un enregistrement par mandat correspondant —
        et, depuis #398, un enregistrement par **période de portefeuille** dès
        qu'un mandat d'appartenance en chevauche plusieurs (un ministre qui
        change de portefeuille en cours de gouvernement).

        Dédupliquée depuis #480 : une entrée strictement identique à une
        précédente est retirée. Un même profil peut porter plusieurs mandats
        d'appartenance au même gouvernement, et le portefeuille qui les
        chevauche tous les deux est alors produit deux fois — voir
        `_dedupliquer_membres`, qui dit aussi pourquoi la déduplication ne
        porte **pas** sur `membre_id` seul.
    """
    g_debut = _parse_date(periode_debut)
    g_fin = _parse_date(periode_fin)

    membres: list[dict[str, Any]] = []
    for profil in profils:
        # #996 lot 4 — quand le roster est là, il dit QUI appartient à ce
        # gouvernement, sur `organe_ref`. Un profil qu'il ne nomme pas n'est
        # pas examiné : c'est la jointure de chaînes inter-sources qui saute.
        est_membre_declare = None
        if slugs_roster is not None:
            est_membre_declare = (profil.get("id") or "") in slugs_roster
            if not est_membre_declare:
                continue
        for mandat in profil.get("mandats") or []:
            if not _mandate_matches_gouvernement(
                mandat, libelle_an, g_debut, g_fin, est_membre_declare
            ):
                continue

            # Tous les portefeuilles chevauchants sont retenus, jamais un seul
            # choisi arbitrairement (#398) : quand un ministre en change en
            # cours de gouvernement, les périodes se succèdent et pavent le
            # mandat d'appartenance — les fondre en une entrée effacerait un
            # des deux portefeuilles réellement occupés.
            portefeuilles: list[dict[str, Any]] = []
            for portefeuille in _portefeuilles_du_mandat(
                profil, mandat, g_debut, g_fin, warnings
            ):
                if _source_url_portefeuille(portefeuille, mandat):
                    portefeuilles.append(portefeuille)
                elif warnings is not None:
                    # Le schéma exige `source_url` dès que `portefeuille` est
                    # renseigné : sans traçabilité, on retombe sur `null`
                    # plutôt que de publier un intitulé invérifiable (§2.3).
                    warnings.append(
                        f"gouvernement_roster: {profil.get('nom') or profil.get('id')} : "
                        f"portefeuille {portefeuille.get('label')!r} sans source_url "
                        f"traçable — portefeuille non renseigné."
                    )

            if not portefeuilles:
                membres.append(_derive_membre_entry(profil, mandat))
                continue
            for portefeuille in portefeuilles:
                membres.append(_derive_membre_entry(profil, mandat, portefeuille))

    # Un mandat d'appartenance scindé fait émettre deux fois le portefeuille
    # qui chevauche ses deux moitiés : ce sont des doublons, pas deux faits
    # (#480). Déduplication en sortie, jamais pendant la sélection — le tri
    # entre répétition et changement de portefeuille se fait sur l'entrée
    # produite, pas sur le mandat dont elle vient.
    return _dedupliquer_membres(membres, warnings)


# ---------------------------------------------------------------------------
# Premier ministre
# ---------------------------------------------------------------------------

# Libellés d'organe du mandat `MINISTERE` correspondant au chef du
# gouvernement. Ce sont des libellés de la source AN, pas une convention de
# notre part — d'où le pluriel : la source accorde ce libellé-là en genre.
#
# Liste FERMÉE, relue et datée (#658), jamais une règle de genre. Un
# rapprochement automatique du masculin et du féminin serait sémantique, et
# `_normalise_fonction` s'interdit explicitement le sémantique. Ce patron —
# énumérer ce qui a été vu, après vérification humaine — est celui de
# `FONCTIONS_MINISTERIELLES_OBSERVEES` juste au-dessus et de
# `correspondance_sigles_an` dans `raw_data/groupes_reels.json`.
#
# Relevé le 2026-08-31 sur `.cache/acteurs_historique_an/acteurs_historique.zip`
# (3 117 fiches acteur, 1 162 mandats `typeOrgane == "MINISTERE"`) : les deux
# formes ci-dessous sont les **seules** que porte un mandat `MINISTERE` de
# qualité « Premier ministre ». La forme féminine vient d'un unique organe,
# `PO791580` (gouvernement Borne, 2022-05-17 → 2024-01-09).
#
# Ajouter une forme ici ne relâche pas le double verrou de #474 : la qualité
# doit toujours valoir exactement `FONCTION_PREMIER_MINISTRE`. Le même organe
# `PO791580` porte d'ailleurs aussi un mandat de qualité « en mission » — une
# mission parlementaire auprès de Matignon, écartée par ce second verrou
# exactement comme au masculin.
LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES: tuple[str, ...] = (
    "Premier ministre",
    "Première ministre",
)

LABELS_PORTEFEUILLE_PREMIER_MINISTRE: frozenset[str] = frozenset(
    _normalise_libelle_organe(libelle)
    for libelle in LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES
)


def _est_libelle_chef_du_gouvernement(label: Any) -> bool:
    """Le libellé d'organe est-il l'un des intitulés relevés du chef du
    gouvernement ? Appartenance à une liste fermée, jamais une heuristique."""
    return _normalise_libelle_organe(label) in LABELS_PORTEFEUILLE_PREMIER_MINISTRE


def acteur_ref_depuis_profil(profil: dict[str, Any]) -> Optional[str]:
    """Extrait l'`acteurRef` AN (ex. `PA722190`) de l'URL de fiche du profil.

    `schema_pivot` n'expose pas l'identifiant du référentiel AN en tant que
    champ : il n'est présent que dans `identite.source_url`
    (`.../deputes/fiche/OMC_PA722190`). L'extraction est un simple motif, pas
    une déduction — absent ou d'une autre forme (fiche Sénat), on retourne
    None plutôt qu'un identifiant reconstruit.
    """
    source_url = (profil.get("identite") or {}).get("source_url") or ""
    correspondance = re.search(r"(PA\d+)", source_url)
    return correspondance.group(1) if correspondance else None


def build_premier_ministre(
    libelle_an: str,
    periode_debut: Optional[str],
    periode_fin: Optional[str],
    profils: list[dict[str, Any]],
    warnings: Optional[list[str]] = None,
) -> Optional[dict[str, Any]]:
    """Détermine le `premier_ministre` d'un gouvernement, ou None (#398).

    Le critère est le **cumul** de deux faits, jamais l'un des deux seul :
      1. être membre de CE gouvernement — même sélection désambiguïsée que
         `build_gouvernement_roster` (libellé exact + chevauchement) ;
      2. porter un mandat `MINISTERE` dont le **libellé d'organe** figure
         dans `LABELS_PORTEFEUILLE_PREMIER_MINISTRE_OBSERVES` (« Premier
         ministre », « Première ministre » — la source accorde ce libellé en
         genre, #658) **et de qualité « Premier ministre »** — celle-là ne
         s'accorde jamais, elle vient d'un autre champ — chevauchant ce
         mandat d'appartenance.

    Le label seul ne suffit pas (#474) : une mission parlementaire auprès de
    Matignon porte exactement le même, avec `fonction: "en mission"`. Un tel
    mandat est déjà écarté en amont par `_portefeuilles_du_mandat` ; la
    vérification de qualité ci-dessous est un second verrou, motivé par le
    fait que l'erreur ne se limiterait pas à publier un faux Premier ministre
    — deux candidats font retourner `None`, donc un missionné pourrait
    *effacer* le vrai.

    Le seul appariement de période serait insuffisant : deux gouvernements
    successifs se suivent d'un jour, et un même Premier ministre peut en
    diriger deux (Philippe I et II). Passer par le mandat d'appartenance
    hérite de la désambiguïsation déjà éprouvée du roster.

    Retourne None — jamais une valeur déduite du nom du gouvernement — si
    aucun profil ne remplit les deux conditions (cas attendu : le Premier
    ministre n'a pas de profil pivot local), et None **avec un warning** si
    plusieurs les remplissent : trancher entre deux candidats serait un choix
    arbitraire (AGENTS.md §2.5).
    """
    g_debut = _parse_date(periode_debut)
    g_fin = _parse_date(periode_fin)

    candidats: list[dict[str, Any]] = []
    for profil in profils:
        for mandat in profil.get("mandats") or []:
            if not _mandate_matches_gouvernement(mandat, libelle_an, g_debut, g_fin):
                continue
            for portefeuille in _portefeuilles_du_mandat(
                profil, mandat, g_debut, g_fin, warnings
            ):
                if not _est_libelle_chef_du_gouvernement(portefeuille.get("label")):
                    continue
                # Second verrou, indépendant de la liste blanche amont (#474) :
                # le label « Premier ministre » est aussi celui d'une mission
                # auprès de Matignon. Exiger en plus la qualité exacte évite
                # qu'un desserrement futur de `FONCTIONS_MINISTERIELLES` ne
                # rouvre le chemin ici — où le dégât n'est pas seulement
                # d'inventer un Premier ministre, mais d'en *effacer* un vrai :
                # deux candidats ⇒ `None` + warning d'ambiguïté (ci-dessous).
                if _normalise_fonction(portefeuille.get("fonction")) != _normalise_fonction(
                    FONCTION_PREMIER_MINISTRE
                ):
                    _ajouter_warning(
                        warnings,
                        f"gouvernement_roster: {profil.get('nom') or profil.get('id')} : "
                        f"mandat de label {portefeuille.get('label')!r} (chef du "
                        f"gouvernement) mais de qualité "
                        f"{portefeuille.get('fonction')!r} — non retenu comme "
                        f"Premier ministre (#474).",
                    )
                    continue
                candidats.append({
                    "nom": profil.get("nom") or "",
                    "acteur_ref": acteur_ref_depuis_profil(profil),
                    "source_url": _source_url_portefeuille(portefeuille, mandat),
                })

    # Un même profil peut porter plusieurs mandats d'appartenance au même
    # gouvernement (mandat scindé) : ce sont des doublons, pas une ambiguïté.
    uniques: list[dict[str, Any]] = []
    for candidat in candidats:
        if candidat not in uniques:
            uniques.append(candidat)

    if not uniques:
        return None
    if len(uniques) > 1:
        if warnings is not None:
            noms = sorted(candidat["nom"] for candidat in uniques)
            warnings.append(
                f"gouvernement_roster: {len(uniques)} Premiers ministres possibles "
                f"pour le gouvernement {libelle_an!r} ({', '.join(noms)}) — "
                f"premier_ministre non renseigné."
            )
        return None
    return uniques[0]


# ---------------------------------------------------------------------------
# Chargement des pivots
# ---------------------------------------------------------------------------

#: Les blocs du profil pivot que la composition ministérielle lit, et rien
#: d'autre — relevés dans le code des **trois** consommateurs de cette liste,
#: pas dans l'énoncé (#635) :
#:
#:   `id`        `_derive_membre_entry` (membre_id), `build_premier_ministre`,
#:               `gouvernement_profile._index_acteur_ref_vers_membre`
#:   `nom`       les mêmes, plus les warnings qui nomment le profil en cause
#:   `mandats`   **parcouru** : c'est lui qui porte les `fonction_gouvernementale`
#:               et les `MINISTERE` — jamais réduit à son cardinal
#:   `identite`  `acteur_ref_depuis_profil`, qui n'y lit que `source_url`
#:   `sources`   `gouvernement_profile.build_gouvernement_profile`, qui agrège
#:               celles des membres retenus
#:
#: Ce que personne n'ouvre : `amendements` (577,3 Mo sur le corpus committé du
#: 30/08/2026), `votes` (67,1), `interventions` (22,2), `couverture` (1,6),
#: `meta`, `textes_portes`, `identifiants`, `tags_thematiques`, `chambres`,
#: `parti`, `groupe`. Soit 12,9 Mo retenus sur 651,5 — 2,0 %.
#:
#: Ajouter une lecture qui ouvre un autre bloc, c'est ajouter ce bloc ici.
BLOCS_LUS_COMPOSITION: tuple[str, ...] = ("id", "nom", "identite", "mandats", "sources")


def projeter_profil(document: dict[str, Any]) -> dict[str, Any]:
    """Le profil pivot réduit à ses cinq blocs lus (`BLOCS_LUS_COMPOSITION`)."""
    return {bloc: document[bloc] for bloc in BLOCS_LUS_COMPOSITION if bloc in document}


def _lire_profil_projete(path: Path) -> Optional[dict[str, Any]]:
    """Lit **un** pivot et n'en rend que la projection.

    Le `json.load` complet reste nécessaire — un profil est écrit compact, sur
    une seule ligne (#433), il n'y a pas de lecture incrémentale sans
    dépendance nouvelle. Ce qui change est la **durée de vie** : le document
    entier est local à cette fonction et meurt à son retour.
    """
    with open(path, encoding="utf-8") as f:
        document = json.load(f)
    if not isinstance(document, dict):
        return None
    return projeter_profil(document)


def load_profils_from_dir(profiles_dir: Path) -> list[dict[str, Any]]:
    """Charge tous les profils pivot v1 (`*.pivot.json`) d'un dossier, **projetés**.

    Un fichier illisible ou invalide est ignoré (signalé sur stderr), sans
    interrompre le chargement des autres profils. Un document dont la racine
    n'est pas un objet JSON est traité comme illisible : la composition
    ministérielle n'a rien à y lire, et le laisser passer faisait lever un
    `AttributeError` au premier `profil.get(...)`.

    **Aucun document n'est conservé entier (#635).** Un profil est lu, projeté
    sur `BLOCS_LUS_COMPOSITION`, puis relâché. Les garder entiers coûtait 2,4 à
    2,7 Gio extrapolés sur les 481 profils committés du 30/08/2026 — mesuré
    sous un plafond `RLIMIT_AS` de 2,0 Gio, atteint autour du 370e profil
    (362e, 381e et 383e sur trois exécutions : le rang dépend de l'empreinte
    de départ du processus, pas de la lecture), facteur × 3,8 à × 4,2.
    C'est le motif de `docs/decisions/oom-lecture-amendements-par-candidat.md`
    sur un chemin de plus, et le même patron que #628 :
    `docs/decisions/audit-599-projection-blocs-lus-628.md`.

    La projection ne change **aucune sortie** : elle retire ce qu'aucun des
    trois consommateurs n'ouvre. `tests/test_gouvernement_roster.py` le
    verrouille des deux côtés — ce qui est retenu, et un plafond de mémoire
    déduit du poids des blocs relâchés.
    """
    profils: list[dict[str, Any]] = []
    for path in sorted(profiles_dir.glob("*.pivot.json")):
        try:
            profil = _lire_profil_projete(path)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  [!] {path} : {exc}", file=sys.stderr)
            continue
        if profil is None:
            print(f"  [!] {path} : racine JSON non-objet, ignoré.", file=sys.stderr)
            continue
        profils.append(profil)
    return profils


# ---------------------------------------------------------------------------
# Lire un bloc que la projection a retiré, sans le rapatrier dans la liste
# ---------------------------------------------------------------------------
#
# La projection ci-dessus n'est pas négociable : `interventions` pèse 38,1 % du
# corpus (mesuré le 18/09/2026 sur 35 profils échantillonnés — 17,3 Mo sur
# 45,4 —, soit ~560 Mo extrapolés aux 1 478,9 Mo des 1 383 profils publiés).
# L'ajouter à `BLOCS_LUS_COMPOSITION` ramène le mur de #635 : les profils
# entiers coûtaient 2,4 à 2,7 Gio sous un plafond de 2,0.
#
# Mais un consommateur en a besoin — `gouvernement_profile.agreger_tags_thematiques`
# (#1020). Il le lit donc À LA DEMANDE, une personne à la fois, et le document
# meurt au retour de la fonction comme dans `_lire_profil_projete`.
#
# Le coût est mesuré, et il est plus bas que celui d'une passe complète :
# 650 lectures pour les 17 fiches (311 personnes distinctes, relues autant de
# fois qu'elles ont servi dans plusieurs gouvernements), soit ~700 Mo à
# 61 Mo/s ≈ 11 s, contre ~24 s pour relire le corpus entier une fois.


def charger_profils_et_chemins(
    profiles_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Path]]:
    """`(profils projetés, {id: chemin})` — une seule passe sur le dossier.

    L'index des chemins est ce qui rend `lecteur_interventions` possible sans
    supposer la convention de nommage : il est construit sur l'`id` que le
    document porte, pas sur le nom du fichier.
    """
    profils = load_profils_from_dir(profiles_dir)
    chemins: dict[str, Path] = {}
    for path in sorted(profiles_dir.glob("*.pivot.json")):
        # Le nom de fichier est le slug, et `id` l'est aussi (#487) — mais
        # c'est une convention, pas un contrat de lecture. On la vérifie en
        # relisant l'index depuis les profils déjà chargés.
        chemins[path.name[: -len(".pivot.json")]] = path
    par_id: dict[str, Path] = {}
    for profil in profils:
        profil_id = profil.get("id")
        if not profil_id:
            continue
        chemin = chemins.get(profil_id)
        if chemin is not None:
            par_id[profil_id] = chemin
    return profils, par_id


def lecteur_interventions(
    chemins_par_id: dict[str, Path],
) -> Callable[[str], list[dict[str, Any]]]:
    """Rend `lire(profil_id) -> interventions[]`, lues sur disque à la demande.

    Un profil inconnu, illisible ou sans bloc `interventions` rend `[]` : c'est
    « rien à agréger pour cette personne », et l'appelant le distingue de
    « personne n'a pu lire », qui est l'absence de lecteur (`None`).
    """

    def lire(profil_id: str) -> list[dict[str, Any]]:
        chemin = chemins_par_id.get(profil_id)
        if chemin is None:
            return []
        try:
            with open(chemin, encoding="utf-8") as f:
                document = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            print(f"  [!] {chemin} : {exc}", file=sys.stderr)
            return []
        if not isinstance(document, dict):
            return []
        interventions = document.get("interventions")
        return interventions if isinstance(interventions, list) else []

    return lire


def load_gouvernement_config(config_path: Path, gouvernement_id: str) -> dict[str, Any]:
    """Charge l'entrée d'un gouvernement depuis `raw_data/gouvernements_reels.json`.

    Raises:
        ValueError: fichier de config invalide ou `gouvernement_id` absent.
    """
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    for entry in payload.get("gouvernements") or []:
        if entry.get("gouvernement_id") == gouvernement_id:
            return entry
    raise ValueError(f"gouvernement_id {gouvernement_id!r} absent de {config_path}.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gouvernement_roster.py",
        description=(
            "Extrait la composition ministérielle d'un gouvernement à partir des "
            "profils pivot individuels déjà collectés. Aucun appel réseau."
        ),
    )
    parser.add_argument(
        "--config",
        default="raw_data/gouvernements_reels.json",
        metavar="FICHIER",
        help="Fichier de référence des gouvernements (défaut : raw_data/gouvernements_reels.json).",
    )
    parser.add_argument(
        "--gouvernement-id",
        required=True,
        metavar="ID",
        help="Ex. 'gouvernement:LECORNU_II' (doit exister dans --config).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Dossier des pivots *.pivot.json (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--out",
        default=None,
        metavar="FICHIER",
        help="Fichier de sortie JSON (défaut : stdout).",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    try:
        entry = load_gouvernement_config(config_path, args.gouvernement_id)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 1

    profils = load_profils_from_dir(Path(args.profiles_dir))
    print(f"→ {len(profils)} profil(s) pivot chargé(s). Extraction en cours…", file=sys.stderr)

    periode = entry.get("periode") or {}
    membres = build_gouvernement_roster(
        libelle_an=entry.get("libelle_an") or "",
        periode_debut=periode.get("debut"),
        periode_fin=periode.get("fin"),
        profils=profils,
    )
    print(f"→ {len(membres)} entrée(s) membres[] extraite(s).", file=sys.stderr)

    roster = {
        "gouvernement_id": entry.get("gouvernement_id"),
        "libelle_an": entry.get("libelle_an"),
        "periode": periode,
        "membres": membres,
    }
    output_json = json.dumps(roster, ensure_ascii=False, indent=2)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")
        print(f"  ✓ Roster écrit : {out_path}", file=sys.stderr)
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
