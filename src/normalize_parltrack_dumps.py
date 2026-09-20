#!/usr/bin/env python3
"""
normalize_parltrack_dumps.py — Adaptateur dumps ParlTrack → schéma pivot v1.

Convertit les données extraites par `parltrack_dumps` (dossiers rapporteur
et amendements) en entrées pivot v1 (`textes_portes[]` et `amendements[]`).

Usage :
    from normalize_parltrack_dumps import enrich_pivot_with_parltrack
    enrich_pivot_with_parltrack(profil_pivot, mep_id=131580)

Cinq décisions gouvernent ce module ; les trois qui se lisent avant d'y
toucher :

- `docs/decisions/lecture-dumps-parltrack-683.md` — pourquoi `role_signataire`
  se lit sur `authors` au lieu de valoir `auteur_principal` pour tout le monde,
  et pourquoi 44 dates du corpus sont publiées `null` avec leur valeur brute.
- `docs/decisions/destinataire-avertissements-642.md` — pourquoi le constat
  « aucune donnée » s'écrit deux fois, une par destinataire.
- `docs/decisions/licence-lot-6-530.md` — pourquoi `meta.licence_donnees` est
  recomposée ici et jamais écrite en dur.

La table complète : `docs/decisions-par-module.md`.
"""

import datetime
import re
import time
import unicodedata
from typing import Any, Optional

from europarl_documents import ResolveurDocuments, document_doceo_de_url, reference_doceo
from avertissements import (
    DESTINATAIRE_INTERNE,
    DESTINATAIRE_LECTEUR,
    avertissement,
    deriver_avertissements,
)
from licences import LICENCE_PARLTRACK, appliquer_licence_donnees
from schema_pivot import COLLECTE_SANS_VERBATIM_SOURCE
from parltrack_dumps import (
    build_stades_dossiers_index,
    get_activities_for_mep,
    get_amendments_for_mep,
    get_dossiers_for_mep,
    get_votes_for_mep,
)

#: #642 — les deux familles du constat ParlTrack, une par destinataire.
#: Aucune n'est le préfixe de l'autre : sans quoi l'union par famille (#600)
#: n'en publierait qu'une, et le lot aurait retiré un avertissement au lieu
#: d'en typer deux.
#:
#: Le préfixe lecteur est **volontairement un préfixe du message publié avant
#: le lot** (« ParlTrack: aucune donnée trouvée pour le MEP ID … ») : les deux
#: sont donc une seule famille, et la nouvelle forme remplace l'ancienne au
#: lieu de cohabiter avec elle. Même geste qu'au #510 pour
#: `WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES`.
WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE = "ParlTrack: aucune donnée"
WARNING_PREFIX_PARLTRACK_DIAGNOSTIC = "ParlTrack (diagnostic) :"

#: #683 — deux constats de couverture, adressés au lecteur. Ils disent ce que la
#: fiche NE porte pas et pourquoi, ce qui est la condition pour qu'un compte
#: partiel ne se lise pas comme un compte total (§2 règle 7).
WARNING_PREFIX_PARLTRACK_VOTES_ECARTES = "Parlement européen — votes non publiés :"
WARNING_PREFIX_PARLTRACK_EXPLICATIONS_SANS_LIEN = "Parlement européen — explications de vote :"

#: Alias historique. Le libellé vit dans `licences` depuis #530 (lot 6) : les
#: mentions d'attribution du pipeline n'ont qu'une seule fabrique.
_PARLTRACK_LICENCE = LICENCE_PARLTRACK
_PARLTRACK_SOURCE_URL = "https://parltrack.org/dumps"


#: Bornes de plausibilité d'une date d'amendement européen. Basse : la première
#: élection du Parlement européen au suffrage universel (juin 1979) — rien
#: d'antérieur ne peut être l'acte d'un député européen élu. Haute : l'année
#: suivante, pour ne pas rejeter un dépôt légitimement postérieur au dump.
#:
#: **Ce n'est pas de l'hygiène de données, c'est la règle 5.** Mesuré le
#: 09/09/2026 sur les 20 937 amendements de nos profils européens : **44**
#: portent une date impossible — année 0302, année 2068. Republiée telle
#: quelle, elle range un amendement de 2020 dans un siècle qui n'existe pas ;
#: corrigée en silence, elle invente. Elle est donc publiée `null`, avec la
#: valeur brute conservée à côté sous `date_non_resolue`.
_ANNEE_MIN_PE = 1979


def _date_plausible(brut: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """`(date publiable, date brute écartée)` — l'un des deux est toujours `None`."""
    if not brut:
        return None, None
    date = str(brut)[:10]
    annee = date[:4]
    if not annee.isdigit():
        return None, str(brut)
    if _ANNEE_MIN_PE <= int(annee) <= datetime.date.today().year + 1:
        return date, None
    return None, str(brut)


def _normaliser_nom(nom: Optional[str]) -> str:
    """Nom réduit à un ensemble de mots, sans accents ni casse ni ordre.

    ParlTrack écrit « France Jamet », le pivot « Jordan BARDELLA » : ni la
    casse, ni l'ordre prénom/nom ne sont garantis. La comparaison porte donc
    sur l'ensemble des mots, ce que ni l'un ni l'autre ne change.
    """
    sans_accents = "".join(
        c for c in unicodedata.normalize("NFKD", nom or "") if not unicodedata.combining(c)
    )
    return " ".join(sorted(m for m in sans_accents.lower().replace("-", " ").split() if m))


def _role_signataire(amendment: dict[str, Any], nom_profil: Optional[str]) -> Optional[str]:
    """Le rôle de cette personne sur cet amendement — ou `None` si la source ne le dit pas.

    ## Pourquoi ce n'est pas « auteur_principal » pour tout le monde

    Le module écrivait `auteur_principal` sur chaque entrée. C'est faux, et
    mesurablement : l'amendement `A9-0183/2023-18` de Jordan Bardella compte
    **30 signataires**, et la médiane sur nos profils est de 3 (maximum 127).
    Personne ne s'en apercevait — le lecteur des dumps ne rendait aucune ligne.

    ## Trois cas, et un quatrième qui reste muet

    1. **un seul signataire** → `auteur_principal`, sans avoir à lire un nom :
       s'il n'y en a qu'un, c'est lui ;
    2. le nom en **tête** de `authors` est le sien → `auteur_principal` ;
    3. la source nomme quelqu'un d'autre en tête → `cosignataire` ;
    4. `authors` est absent ou illisible → **`None`**.

    Le quatrième cas est le seul honnête quand la source se tait, et il n'est
    pas rare : l'ordre de `meps` reproduit celui de `authors` dans **91 %** des
    1 257 735 amendements vérifiables, ce qui est trop pour l'ignorer et bien
    trop peu pour en faire une règle. Le schéma admet `role_signataire: null`
    (`KNOWN_ROLES_SIGNATAIRE_AMENDEMENT` n'est vérifié que sur une valeur
    présente) : une place cosignataire supposée serait une affirmation que rien
    ne source (§2 règle 2).
    """
    if amendment.get("nb_signataires") == 1:
        return "auteur_principal"
    premier = _normaliser_nom(amendment.get("premier_auteur"))
    if not premier:
        return None
    return "auteur_principal" if premier == _normaliser_nom(nom_profil) else "cosignataire"


#: `procedure.stage_reached` → la valeur pivot, une par une (#901).
#:
#: Le sens est conservé mot pour mot, jamais rapproché d'un stade français : la
#: table est plate et explicite pour qu'une lecture suffise à vérifier qu'aucune
#: ligne n'invente. Une valeur que la source ajouterait un jour n'est pas
#: devinée — elle ressort `stade_procedural: null` avec son motif, ce qui est un
#: fait déclaré et non un trou (§2 règle 5).
STADE_UE_PAR_LIBELLE_SOURCE: dict[str, str] = {
    "Procedure completed": "ue_procedure_achevee",
    "Procedure completed - delegated act enters into force":
        "ue_procedure_achevee_acte_delegue_en_vigueur",
    "Procedure completed - delegated act rejected":
        "ue_procedure_achevee_acte_delegue_rejete",
    "Procedure completed, awaiting publication in Official Journal":
        "ue_procedure_achevee_attente_publication_jo",
    "Procedure lapsed or withdrawn": "ue_procedure_caduque_ou_retiree",
    "Procedure rejected": "ue_procedure_rejetee",
    "Preparatory phase in Parliament": "ue_phase_preparatoire_parlement",
    "Awaiting committee decision": "ue_attente_decision_commission",
    "Awaiting final decision": "ue_attente_decision_finale",
    "Awaiting Parliament's position in 1st reading":
        "ue_attente_position_parlement_1re_lecture",
    "Awaiting Parliament 1st reading / single reading / budget 1st stage":
        "ue_attente_parlement_1re_lecture",
    "Awaiting Parliament 2nd reading": "ue_attente_parlement_2e_lecture",
    "Awaiting Parliament's vote": "ue_attente_vote_parlement",
    "Awaiting plenary debate/vote": "ue_attente_debat_vote_pleniere",
    "Awaiting Council's 1st reading position":
        "ue_attente_position_conseil_1re_lecture",
    "Awaiting Council decision, 2nd reading":
        "ue_attente_decision_conseil_2e_lecture",
}


def _stade_procedural_ue(dossier: dict[str, Any]) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """Le stade pivot d'un dossier européen, et le motif quand il n'y en a pas.

    Trois cas, et chacun se déclare :

      - la source publie un libellé connu → la valeur pivot ;
      - elle n'en publie aucun → `source_sans_stade`. C'est **14,4 %** des
        dossiers du dump, mesuré le 13/09/2026 : une absence de la source, pas
        une nôtre ;
      - elle en publie un que la table ne connaît pas → `stade_source_inconnu`,
        **avec le libellé reçu**. Deviner reviendrait à ranger un fait sous une
        étiquette choisie par ressemblance ; échouer ferait tomber un run entier
        sur un libellé ajouté en amont.
    """
    brut = dossier.get("stade_source")
    if not brut:
        return None, {"motif": "source_sans_stade"}
    connu = STADE_UE_PAR_LIBELLE_SOURCE.get(brut)
    if connu:
        return connu, None
    return None, {"motif": "stade_source_inconnu", "valeur_source": brut}


def _make_texte_porte(dossier: dict[str, Any]) -> dict[str, Any]:
    """Convertit un enregistrement dossier ParlTrack en entrée pivot `textes_portes`.

    Args:
        dossier: dict retourné par `parltrack_dumps.get_dossiers_for_mep`.

    Returns:
        Dict conforme au schéma `textes_portes[]`.
    """
    stade, stade_non_resolu = _stade_procedural_ue(dossier)
    reference = dossier.get("reference") or None
    titre = dossier.get("titre") or dossier.get("reference") or ""
    return {
        "titre": titre,
        # Le titre d'un DOSSIER vient du dump ParlTrack, qui le publie en
        # anglais, et aucun document `doceo` ne s'y rattache pour aller chercher
        # la version française (#901). Le champ est posé quand même : les deux
        # fabriques portent les mêmes clés, sans quoi une fiche distinguerait
        # deux textes selon le chemin qui les a produits — ce que
        # `test_les_deux_fabriques_portent_les_memes_cles` interdit.
        "titre_langue": "en" if titre else None,
        "institution": "parlement_europeen",
        "role": "rapporteur",
        "type_rapport": None,
        # La référence de procédure que l'activité vise. Publiée sous le même
        # nom que sur un vote (`scrutin_non_resolu.reference_dossier`) : c'est
        # le même espace de références, et lui donner deux noms obligerait
        # chaque consommateur à connaître le chemin qui a produit l'entrée.
        # Sans elle, les 383 textes portés européens ne rejoignaient aucun
        # index — besoin remonté par l'interface le 14/09/2026.
        "reference_dossier": reference,
        "stade_procedural": stade,
        **({"stade_procedural_non_resolu": stade_non_resolu} if stade_non_resolu else {}),
        # #747 — ce chemin publiait une entrée qui ne disait RIEN du sort : ni
        # le champ, ni le motif de son absence. #743 n'avait instruit que le
        # chemin AN, et le contrôle du couple ne voyait pas le cas parce qu'il
        # ne s'armait que sur un motif NON nul. Le dump ParlTrack ne porte
        # aucune issue de dossier : l'absence est un fait de la source.
        "sort": None,
        "sort_non_resolu": {"motif": "source_sans_sort"},
        "date_min": _date_plausible(dossier.get("date"))[0],
        "date_max": _date_plausible(dossier.get("date"))[0],
        "legislature": None,
        "source_url": dossier.get("source_url"),
    }


def _make_amendement(amendment: dict[str, Any], nom_profil: Optional[str] = None) -> dict[str, Any]:
    """Convertit un enregistrement amendement ParlTrack en entrée pivot `amendements`.

    Note : ParlTrack ne fournit pas de champ `sort` (outcome) fiable sur
    les dumps bruts d'amendements. On ne renseigne donc pas `sort` (null),
    conformément à la règle 5 (missing data = null, never default 0).

    **Toujours non résolu** (#431). L'index partagé `pivot_data/amendements/`
    est keyé par l'`uid` de l'Assemblée nationale (`an:<uid>`), et un amendement
    du Parlement européen n'en a pas : lui en fabriquer un serait inventer une
    clé (AGENTS.md §2.5), et le ranger dans un index dont l'identifiant annonce
    une autre source serait pire encore. Son enregistrement complet reste donc
    dans le profil sous `amendement_non_resolu` — la forme exacte que le schéma
    prévoit pour une entrée qu'on ne sait pas rattacher, ni supprimée ni devinée.

    Aucune duplication n'est perdue au passage : l'entrée décrit la signature
    de CETTE personne sur un amendement donné, et le dump publie l'amendement
    une seule fois quel que soit le nombre de signataires.

    **Correction de ce qui était écrit ici** : « ParlTrack ne fournit pas les
    cosignataires » était faux. Chaque amendement porte la liste complète de
    ses signataires (`meps`) et leurs noms dans l'ordre (`authors`) — c'est ce
    qui rend `_role_signataire` possible.

    Args:
        amendment: dict retourné par `parltrack_dumps.get_amendments_for_mep`.

    Returns:
        Dict conforme au schéma `amendements[]` (mapping + enregistrement).
    """
    date, date_ecartee = _date_plausible(amendment.get("date"))
    non_resolu: dict[str, Any] = {
        # #683 — l'institution est portée par l'entrée elle-même. C'est ce qui
        # permet à `couverture_profil` de dire quelle borne s'applique à quoi,
        # sans deviner à partir d'une URL.
        "institution": "parlement_europeen",
        "texte_vise": amendment.get("reference") or "",
        "sort": None,
        "base_juridique_irrecevabilite": None,
        # Reste `null` : le schéma attend ici un **slug** de notre corpus
        # (#487), pas un nom libre. Ce que ParlTrack nomme en tête d'`authors`
        # sert à qualifier `role_signataire`, il n'usurpe pas un champ dont le
        # contrat est un identifiant.
        "premier_signataire": None,
        "co_signataires": [],
        "type_deposant": None,
        "date": date,
        "numero": amendment.get("id"),
        "source_url": amendment.get("source_url"),
    }
    if date_ecartee is not None:
        non_resolu["date_non_resolue"] = {
            "motif": "date_hors_bornes",
            "valeur_source": date_ecartee,
        }
    return {
        "amendement_id": None,
        "role_signataire": _role_signataire(amendment, nom_profil),
        "amendement_non_resolu": non_resolu,
    }


# ---------------------------------------------------------------------------
# Les votes : ce qui se publie, et ce qui se compte (#683)
# ---------------------------------------------------------------------------

#: Les natures de scrutin qui portent sur **l'ensemble d'un texte**, telles que
#: le Parlement européen les nomme en queue d'intitulé. Vocabulaire **fermé**,
#: relevé sur les 44 648 scrutins du dump : on l'étend, on ne le contourne pas
#: (§4).
#:
#: ## Pourquoi une sélection, et pourquoi celle-là
#:
#: Un député européen vote des centaines de fois sur un même texte : Jordan
#: Bardella compte **607 scrutins sur le seul dossier `2018/0216(COD)`**, dont
#: 271 pour, 247 contre et 89 abstentions. Publier ces positions une à une ne
#: dit rien — **93 %** des intitulés sont procéduraux (« Am 1 », « § 13 »,
#: « Mardi - demande du groupe GUE/NGL »), et un chiffre dont le lecteur ne peut
#: rien tirer ne se publie pas (règle de forme 1, #326).
#:
#: Ce qui se publie est donc la position sur **l'ensemble du texte** — 375 pour
#: Bardella, dont **97 %** retrouvent le titre de leur dossier. C'est la
#: transposition exacte de « un texte, une position » (#711), et le seul
#: registre où le lecteur apprend ce qu'une personne a voté.
#:
#: ## Ce que cette sélection ne fait pas
#:
#: Elle n'efface rien. Les scrutins écartés sont **comptés** et le compte est
#: publié dans l'avertissement de couverture : une position d'amendement n'est
#: pas une position absente (§2 règle 5, #511).
NATURES_VOTE_SUR_ENSEMBLE: frozenset[str] = frozenset({
    # Xe législature et avant — la source écrivait en français.
    "resolution",
    "resolution legislative",
    "proposition de resolution",
    "proposition de resolution (ensemble du texte)",
    "vote unique",
    "ensemble du texte",
    "texte dans son ensemble",
    "proposition de la commission",
    "proposition modifiee",
    "decision",
    "decision (ensemble du texte)",
    "proposition de decision",
    "propositions de decision",
    "projet de decision du conseil",
    "approbation",
    "procedure d'approbation",
    # XIe législature (depuis juillet 2024) — la source écrit en anglais.
    # Ce n'est pas une variante de style : sans ces formes, la sélection perdait
    # **5 012 scrutins** de la seule législature en cours pour Jordan Bardella,
    # et sa fiche se serait arrêtée au 19/10/2023 sans que rien ne le dise.
    "motion for a resolution",
    "motion for a resolution (as a whole)",
    "motion for a resolution (text as a whole)",
    "text as a whole",
    "single vote",
    "legislative resolution",
    "commission proposal",
    "commission proposal to the council",
    "commission proposal and amendments",
    "draft council decision",
    "council draft",
    "proposal for a decision",
    "proposal for a decision (as a whole)",
    "proposal for a council decision",
    "joint text",
    "approval",
})

#: La queue d'intitulé porte la nature du scrutin, après le dernier tiret et
#: avant l'horodatage que la source colle parfois derrière.
#:
#: **Les trois tirets sont là exprès.** La source a changé de séparateur en même
#: temps que de langue : trait d'union jusqu'à la Xe législature, tiret demi-cadratin
#: (« – ») depuis la XIe. Un motif qui ne connaît que le premier ne rend aucune
#: nature sur la législature en cours — et une nature nulle est un scrutin écarté,
#: c'est-à-dire un trou muet (#510).
_QUEUE_INTITULE = re.compile(r"[-\u2013\u2014]\s*([^-\u2013\u2014]{2,45}?)\s*(?:\d{2}/\d{2}/\d{4}[\d:. ]*)?$")


def _normaliser_nature(brut: Optional[str]) -> str:
    """Minuscules, sans accents, espaces réduits — **l'ordre des mots est gardé**.

    Distinct de `_normaliser_nom`, qui trie les mots parce qu'un prénom et un nom
    s'écrivent dans les deux ordres. Une nature de scrutin, non : « proposition de
    decision » et « decision de proposition » ne sont pas la même chose, et trier
    les rapprocherait.
    """
    sans_accents = "".join(
        c for c in unicodedata.normalize("NFKD", brut or "") if not unicodedata.combining(c)
    )
    return " ".join(sans_accents.lower().split())


def _nature_scrutin(titre: Optional[str]) -> Optional[str]:
    """La nature d'un scrutin, normalisée, ou `None` si l'intitulé n'en porte pas."""
    if not titre:
        return None
    trouve = _QUEUE_INTITULE.search(titre.strip())
    if not trouve:
        return None
    return _normaliser_nature(trouve.group(1)) or None


def _porte_sur_ensemble(titre: Optional[str]) -> bool:
    """Ce scrutin porte-t-il sur l'ensemble d'un texte ?

    **Le seul signal disponible est l'intitulé**, et c'est une fragilité qu'il
    faut nommer : le dump ne porte aucun drapeau de nature. Un libellé qui
    change côté source fait maigrir le registre sans rien lever — c'est
    exactement ce qui s'est produit au passage à la XIe législature, où la
    source est passée au français à l'anglais et du trait d'union au tiret
    demi-cadratin. D'où le décompte des écartés, publié par l'appelant : un
    registre qui maigrit se voit alors dans le chiffre déclaré.
    """
    nature = _nature_scrutin(titre)
    return nature is not None and nature in NATURES_VOTE_SUR_ENSEMBLE


def _make_vote(scrutin: dict[str, Any]) -> dict[str, Any]:
    """Convertit un scrutin ParlTrack en entrée pivot `votes[]`.

    **`scrutin_id` est toujours `null`**, et pour la raison qui vaut déjà pour
    les amendements européens (#431) : l'index partagé `pivot_data/scrutins.json`
    est keyé `an:<législature>:<numéro>`, et `scrutins_index.decomposer_id`
    refuse tout ce qui ne commence pas par `an:`. Fabriquer une clé européenne
    dans cet espace de noms serait inventer un identifiant (§2 règle 5) ; la
    ranger sous un préfixe qui annonce l'Assemblée serait pire.

    L'enregistrement complet part donc dans `scrutin_non_resolu`, la forme que
    le schéma prévoit exactement pour ce cas, et il porte ce qui rend le vote
    vérifiable : le procès-verbal officiel du Parlement européen.
    """
    date, date_ecartee = _date_plausible(scrutin.get("date"))
    reference = scrutin.get("reference")
    if isinstance(reference, list):
        reference = reference[0] if reference else None
    non_resolu: dict[str, Any] = {
        "institution": "parlement_europeen",
        "titre": scrutin.get("titre") or "",
        "nature": _nature_scrutin(scrutin.get("titre")),
        "reference_dossier": reference,
        "date": date,
        "numero_scrutin": scrutin.get("scrutin_id"),
        "source_url": scrutin.get("source_url"),
    }
    if date_ecartee is not None:
        non_resolu["date_non_resolue"] = {
            "motif": "date_hors_bornes",
            "valeur_source": date_ecartee,
        }
    return {
        "scrutin_id": None,
        "position": scrutin.get("position"),
        "scrutin_non_resolu": non_resolu,
    }


# ---------------------------------------------------------------------------
# Les interventions : trois natures, une seule liste (#683)
# ---------------------------------------------------------------------------

#: `type_detail` par type d'activité ParlTrack. Les trois natures européennes
#: entrent dans `interventions[]` — la liste où l'Assemblée range déjà ses
#: débats **et** ses questions écrites (`type_detail: "question"`), ce qui rend
#: le rangement européen conforme et non inventé.
TYPE_DETAIL_PAR_ACTIVITE: dict[str, str] = {
    "intervention_seance": "debat",
    "question_ecrite": "question",
    "question_orale": "question",
    "interpellation_majeure": "question",
    "explication_de_vote_ecrite": "explication_de_vote",
}

#: `sous_type`, sur le modèle des `QE`/`QG`/`QOSD` de l'Assemblée.
SOUS_TYPE_PAR_ACTIVITE: dict[str, str] = {
    "question_ecrite": "QE",
    "question_orale": "QO",
    "interpellation_majeure": "IM",
}


def _make_intervention(
    activite: str,
    entree: dict[str, Any],
    resolveur: Optional[ResolveurDocuments] = None,
) -> dict[str, Any]:
    """Convertit une activité ParlTrack en entrée pivot `interventions[]`.

    ## Ce que la source donne, et ce qu'elle ne donne pas

    Le Parlement européen publie le **titre du point**, sa date et le lien vers
    le document officiel — jamais le compte rendu intégral, contrairement à
    Syceron. L'entrée porte donc `collecte: "sans_verbatim_source"`, valeur
    ajoutée pour ce cas : `theme_seul` dirait que **notre run** n'a pas demandé
    le verbatim, ce qui serait un fait faux sur nous et un fait faux sur la
    source (§2 règle 5, la distinction de #657).

    ## L'exception : les explications de vote

    Elles portent le texte **écrit par la personne**, en français, et c'est la
    seule matière du corpus européen où quelqu'un dit lui-même pourquoi il a
    voté ainsi. Elles ne portent donc PAS `collecte` — leur forme est complète.

    ParlTrack ne leur donne **aucun** lien : 0 des 1 801 entrées `WEXP` des 7
    candidats déclarés porte une `url`, contre 100 % des neuf autres types
    d'activité. Le `source_url` publié ici vient donc d'ailleurs (#827) — de la
    référence citée dans l'intitulé, `(A8-0196/2017 - Petri Sarvamaa)`, dont
    l'existence est **prouvée sur le portail open data** avant que l'adresse
    publique ne soit écrite. Sans résolveur, aucune adresse n'est publiée : une
    URL dérivée sans preuve est indétectablement fausse, le site public étant
    derrière un pare-feu qui répond pareil à une URL vraie et à une inventée.

    **Un chiffre a longtemps été cité de travers ici** : « la référence n'est
    dans l'intitulé qu'1 fois sur 190 ». C'est exact **pour Bardella**, dont 189
    des 190 explications n'en citent aucune. Ce n'est pas le taux du corpus, qui
    est de **1 530 sur 1 801 (85 %)** — Philippot n'en manque que 7 sur 766. La
    population d'un chiffre se nomme (§9).

    L'`intervention_id` reprend la **référence de la source** quand elle existe
    (`P10_CRE-REV(2024)07-17(2-020-0000)`), préfixée `europarl_`. Ce n'est pas
    un identifiant fabriqué : c'est celui du Parlement européen, préfixé pour ne
    pas entrer en collision avec l'espace `syceron_`/`question_` de l'Assemblée.
    """
    reference = entree.get("reference")
    date, _ = _date_plausible(entree.get("date"))
    intervention: dict[str, Any] = {
        "intervention_id": f"europarl_{reference}" if reference else None,
        "date": date,
        "type_detail": TYPE_DETAIL_PAR_ACTIVITE.get(activite, "debat"),
        "sujet": entree.get("titre") or "",
        "theme_officiel": None,
        "seance": None,
        "dossier": None,
        "source": {"institution": "parlement_europeen", "legislature": entree.get("legislature")},
        "fonction": None,
        "format": None,
        "mots_cles": [],
        "source_url": entree.get("source_url"),
    }
    # #827 — l'adresse est dérivée, l'existence est prouvée. Sans résolveur
    # (passe hors ligne, tests), rien n'est écrit : une URL non vérifiée est
    # indétectablement fausse, et §2 règle 2 interdit de la publier.
    if resolveur is not None and not intervention["source_url"]:
        intervention["source_url"] = resolveur.url_verifiee(entree.get("titre"))
    texte = entree.get("texte")
    if texte:
        intervention["texte"] = texte
    else:
        intervention["texte"] = None
        intervention["collecte"] = COLLECTE_SANS_VERBATIM_SOURCE
    sous_type = SOUS_TYPE_PAR_ACTIVITE.get(activite)
    if sous_type:
        intervention["sous_type"] = sous_type
    return intervention


# ---------------------------------------------------------------------------
# Les propositions de résolution (#683)
# ---------------------------------------------------------------------------

#: Les activités qui sont des **textes portés**, avec le rôle que le schéma
#: leur connaît déjà (`KNOWN_ROLES_TEXTE`). Rien de neuf : une proposition de
#: résolution européenne est portée comme une proposition de résolution
#: française.
#: `(nature_texte, role)`. Les deux vont **ensemble** : #689 refuse un rôle
#: d'initiateur qui ne serait pas dérivé de la nature du texte — « deux champs
#: qui disent la même chose ne valent que s'ils ne peuvent pas se contredire ».
#: Un rôle de rapport est hors table de natures, et sa nature reste `null` :
#: rapporter un texte est une fonction, pas une nature.
ROLE_PAR_ACTIVITE: dict[str, tuple[Optional[str], str]] = {
    "proposition_de_resolution": ("proposition_de_resolution", "auteur_proposition_de_resolution"),
    "proposition_de_resolution_individuelle": ("proposition_de_resolution", "auteur_proposition_de_resolution"),
    "rapport": (None, "rapporteur"),
    "avis_de_commission": (None, "rapporteur"),
}


def _reference_dossier_activite(entree: dict[str, Any]) -> Optional[str]:
    """La référence de procédure qu'une activité vise, s'il y en a une.

    La source la range sous `dossiers`, au pluriel et en liste. La **première**
    est retenue : une activité qui en vise plusieurs porte sur plusieurs
    dossiers, et en choisir un est déjà une approximation, mais publier le stade
    du premier reste plus juste que n'en publier aucun — et le cas est rare.

    ## `entree` n'est pas l'entrée du dump, et c'est ce qui a coûté un run

    Cette fonction a été écrite sur une mesure du **dump** — 144 des 146 entrées
    `REPORT` d'un échantillon de 300 MEP portaient `dossiers`. La mesure était
    juste ; elle portait sur le mauvais objet. Ce que la fonction reçoit vient
    de `build_activities_index`, qui **projette** chaque entrée sur six clés, et
    `dossiers` n'en faisait pas partie. Résultat mesuré sur le run `34853965676`
    (14/09/2026) : `activite_sans_dossier` sur **371 des 371** entrées de cette
    fabrique, soit 100 % — un taux unanime est un symptôme de projection, pas
    une propriété de la source.

    Ce que la source porte vraiment, mesuré le 14/09/2026 sur les 4 585 fiches
    MEP du dump `ep_mep_activities` (population : toutes, pas les 7 candidats
    déclarés à identifiant européen) : `REPORT` 9 593 / 9 935 (96,6 %),
    `MOTION` 44 684 / 60 362 (74,0 %), `COMPARL` 542 / 4 937 (11,0 %),
    `IMOTION` 1 / 3 862. Une absence reste donc un cas fréquent et légitime sur
    deux des quatre types — `activite_sans_dossier` ne disparaîtra pas, il
    cessera d'être unanime.
    """
    dossiers = entree.get("dossiers")
    if isinstance(dossiers, list) and dossiers:
        premier = dossiers[0]
        return premier if isinstance(premier, str) and premier else None
    if isinstance(dossiers, str) and dossiers:
        return dossiers
    return None


def _titre_publie(
    entree: dict[str, Any], resolveur: Optional[ResolveurDocuments]
) -> tuple[str, Optional[str]]:
    """Le titre à publier, et la langue dans laquelle il l'est (#901).

    Le dump ParlTrack donne le titre en ANGLAIS — « JOINT MOTION FOR A
    RESOLUTION on Azerbaijan… ». Le portail du Parlement publie le même
    document en 22 à 23 langues, français compris, et le résolveur téléchargeait
    déjà cette réponse pour en tirer un booléen d'existence.

    Ce n'est donc pas une traduction que nous fabriquerions : c'est la version
    française officielle, sous la même licence que le reste du portail (§7).

    Quand le portail n'a rien — pas de référence citée, document introuvable,
    question non posée — le titre anglais du dump est conservé, et
    `titre_langue` le dit. Publier un titre vide serait pire que le publier
    dans la mauvaise langue.
    """
    titre_source = entree.get("titre") or ""
    if resolveur is None:
        return titre_source, ("en" if titre_source else None)
    # Le document se lit dans `source_url`, JAMAIS dans le titre. La première
    # version cherchait une référence dans le titre : aucun des 694 titres
    # publiés n'en porte (« JOINT MOTION FOR A RESOLUTION on Azerbaijan… »), et
    # le run 35087127267 a publié 0 titre français. Le test l'avait laissé
    # passer parce qu'il inventait un titre « …(A9-0227/2024) » qui n'existe
    # nulle part dans le corpus (#901, 16/09/2026).
    doceo = document_doceo_de_url(entree.get("source_url"))
    if doceo is None:
        return titre_source, ("en" if titre_source else None)
    titre_fr = resolveur.titre_francais(doceo)
    if titre_fr:
        return titre_fr, "fr"
    return titre_source, ("en" if titre_source else None)


def _make_texte_porte_activite(
    activite: str,
    entree: dict[str, Any],
    stades_par_reference: Optional[dict[str, str]] = None,
    resolveur: Optional[ResolveurDocuments] = None,
) -> dict[str, Any]:
    """Convertit une activité portée (résolution, rapport) en `textes_portes[]`.

    ## Le stade, et pourquoi il n'était pas là

    Cette fabrique écrivait `stade_procedural: None` en dur. Le lot du stade
    (#901) n'avait corrigé que l'**autre** fabrique — celle des dossiers dont la
    personne est rapporteure — et le run du 14/09/2026 l'a montré : **12 des 383**
    textes portés européens portaient un stade, 3 %. Les 371 autres viennent
    d'ici.

    La source donne pourtant de quoi le résoudre : une activité cite la
    référence de procédure qu'elle vise, et `build_stades_dossiers_index` rend
    le stade de n'importe quelle référence.

    Trois cas, et chacun se déclare — mêmes motifs que l'autre fabrique, pour
    qu'une fiche ne distingue pas deux textes selon le chemin qui les a produits :
    `source_sans_stade` quand la source n'en publie pas, `stade_source_inconnu`
    avec la valeur reçue quand la table ne la connaît pas, et
    `activite_sans_dossier` quand l'activité ne vise aucune référence — il n'y a
    alors rien à interroger.
    """
    date, _ = _date_plausible(entree.get("date"))
    nature, role = ROLE_PAR_ACTIVITE[activite]
    reference = _reference_dossier_activite(entree)
    if reference is None:
        stade, stade_non_resolu = None, {"motif": "activite_sans_dossier"}
    else:
        stade, stade_non_resolu = _stade_procedural_ue(
            {"stade_source": (stades_par_reference or {}).get(reference)})
    titre, titre_langue = _titre_publie(entree, resolveur)
    return {
        "titre": titre,
        "titre_langue": titre_langue,
        "institution": "parlement_europeen",
        "nature_texte": nature,
        "role": role,
        "type_rapport": None,
        "reference_dossier": reference,
        "stade_procedural": stade,
        **({"stade_procedural_non_resolu": stade_non_resolu} if stade_non_resolu else {}),
        "sort": None,
        "sort_non_resolu": {"motif": "source_sans_sort"},
        "date_min": date,
        "date_max": date,
        "legislature": None,
        "source_url": entree.get("source_url"),
    }


def enrich_pivot_with_parltrack(
    profil: dict[str, Any],
    mep_id: int,
    force_download: bool = False,
    resolveur: Optional[ResolveurDocuments] = None,
) -> None:
    """Enrichit un profil pivot v1 en place avec les données ParlTrack.

    Ajoute les `textes_portes[]` (rôle rapporteur détecté) et
    `amendements[]` signés, en mode additif (n'écrase pas les entrées
    existantes).

    Les clés d'unicité utilisées pour la déduplication additive sont
    identiques à celles de `merge_profile._pivot_texte_key` et
    `merge_profile._pivot_amendement_key` :
    - `textes_portes` : source_url (si présent) sinon (titre, date_min, legislature)
    - `amendements`   : `amendement_id` si résolu, sinon, dans
      `amendement_non_resolu`, source_url (si présent) sinon
      (numero, texte_vise, date)

    Un warning est ajouté à `meta.warnings[]` si les dumps sont
    indisponibles.

    Args:
        profil: profil pivot v1 dict à enrichir (modifié en place).
        mep_id: UserID ParlTrack (entier).
        force_download: re-télécharger les dumps même si un cache existe.
    """
    meta = profil.setdefault("meta", {})
    warnings: list[str] = meta.setdefault("warnings", [])

    # --- textes_portes (rapporteur) ---
    dossiers = get_dossiers_for_mep(mep_id, force_download=force_download)
    def _tp_key(t: dict[str, Any]) -> Any:
        return t.get("source_url") or (t.get("titre"), t.get("date_min"), t.get("legislature"))

    existing_tp_keys = {
        _tp_key(t)
        for t in (profil.get("textes_portes") or [])
        if isinstance(t, dict)
    }
    new_tp = []
    for d in dossiers:
        entry = _make_texte_porte(d)
        key = _tp_key(entry)
        if key not in existing_tp_keys:
            existing_tp_keys.add(key)
            new_tp.append(entry)

    if profil.get("textes_portes") is None:
        profil["textes_portes"] = []
    profil["textes_portes"].extend(new_tp)

    # --- amendements ---
    amendments = get_amendments_for_mep(mep_id, force_download=force_download)

    def _amd_key(a: dict[str, Any]) -> Any:
        # Même clé que `merge_profile._pivot_amendement_key` : `amendement_id`
        # d'abord, puis l'enregistrement non résolu — sans quoi toutes les
        # entrées PE, qui ont toutes `amendement_id: None`, se réduiraient à une.
        if a.get("amendement_id"):
            return a["amendement_id"]
        non_resolu = a.get("amendement_non_resolu")
        if isinstance(non_resolu, dict):
            a = non_resolu
        return a.get("source_url") or (a.get("numero"), a.get("texte_vise"), a.get("date"))

    existing_amd_keys = {
        _amd_key(a)
        for a in (profil.get("amendements") or [])
        if isinstance(a, dict)
    }
    new_amds = []
    nom_profil = profil.get("nom")
    for a in amendments:
        entry = _make_amendement(a, nom_profil)
        key = _amd_key(entry)
        if key not in existing_amd_keys:
            existing_amd_keys.add(key)
            new_amds.append(entry)

    if profil.get("amendements") is None:
        profil["amendements"] = []
    profil["amendements"].extend(new_amds)

    # --- votes sur l'ensemble d'un texte (#683) ---
    scrutins = get_votes_for_mep(mep_id, force_download=force_download)
    retenus = [s for s in scrutins if _porte_sur_ensemble(s.get("titre"))]
    ecartes = len(scrutins) - len(retenus)

    def _vote_key(v: dict[str, Any]) -> Any:
        # Même clé que `merge_profile._pivot_vote_key`, branche « non résolu » :
        # une clé qui diverge de celle de la fusion republie tout à chaque run.
        if v.get("scrutin_id"):
            return v["scrutin_id"]
        non_resolu = v.get("scrutin_non_resolu") or {}
        return ("non_resolu", non_resolu.get("numero_scrutin"), non_resolu.get("date"))

    cles_votes = {
        _vote_key(v) for v in (profil.get("votes") or []) if isinstance(v, dict)
    }
    nouveaux_votes = []
    for scrutin in retenus:
        entree = _make_vote(scrutin)
        cle = _vote_key(entree)
        if cle not in cles_votes:
            cles_votes.add(cle)
            nouveaux_votes.append(entree)
    if profil.get("votes") is None:
        profil["votes"] = []
    profil["votes"].extend(nouveaux_votes)

    # --- interventions et textes portés, depuis les activités (#683) ---
    activites = get_activities_for_mep(mep_id, force_download=force_download)

    def _interv_key(i: dict[str, Any]) -> Any:
        """La clé de déduplication d'une intervention. **Elle ne doit dépendre
        d'aucun champ qui peut APPARAÎTRE.**

        C'est le défaut que #827 a introduit et que ce lot corrige. La cascade
        passait par `source_url` avant le contenu ; les explications de vote
        n'ayant pas d'`intervention_id`, leur clé était le contenu **avant**
        #827 et l'URL **après**. Deux clés pour la même entrée : la fusion
        additive a ajouté au lieu de reconnaître, et **1 462 explications ont
        été publiées deux fois** — l'exemplaire sans lien, puis le même avec.

        `source_url` est donc retiré de la cascade. Ce n'est pas une perte de
        pouvoir discriminant : mesuré sur les 1 019 036 interventions publiées,
        les **3 073** entrées sans `intervention_id` portent **toutes** un sujet
        ou un texte, donc la clé de contenu les sépare — et c'est exactement
        cette clé qui, appliquée, rend les 1 462 doublons comme doublons.

        **Le contenu ne peut pas non plus devenir une clé systématique**, et
        c'est ce qui interdit le correctif évident : **902 457** entrées à
        `intervention_id` DIFFÉRENTS partagent déjà une clé de contenu, les
        interventions collectées en mode thème-seul n'ayant ni sujet ni texte.
        Ajouter cette clé pour tout le monde fusionnerait 88 % du corpus.

        L'ordre est donc : l'identifiant quand il existe, le contenu sinon.
        Chacun est stable dans le temps ; ni l'un ni l'autre n'apparaît après
        coup.
        """
        if i.get("intervention_id"):
            return ("intervention_id", i["intervention_id"])
        return ("contenu", i.get("date"), i.get("sujet"), (i.get("texte") or "")[:50])

    cles_interv = {
        _interv_key(i) for i in (profil.get("interventions") or []) if isinstance(i, dict)
    }
    nouvelles_interv: list[dict[str, Any]] = []
    for activite, entrees in sorted(activites.items()):
        if activite not in TYPE_DETAIL_PAR_ACTIVITE:
            continue
        for brut in entrees:
            entree = _make_intervention(activite, brut, resolveur)
            cle = _interv_key(entree)
            if cle not in cles_interv:
                cles_interv.add(cle)
                nouvelles_interv.append(entree)
    if profil.get("interventions") is None:
        profil["interventions"] = []
    profil["interventions"].extend(nouvelles_interv)

    # L'index des stades n'est lu qu'une fois, et seulement si une activité
    # portée existe : le construire pour un profil qui n'en a aucune coûterait
    # un parcours de dump pour rien.
    stades_par_reference: Optional[dict[str, str]] = None
    if any(a in ROLE_PAR_ACTIVITE for a in activites):
        stades_par_reference = build_stades_dossiers_index(force_download)

    for activite, entrees in sorted(activites.items()):
        if activite not in ROLE_PAR_ACTIVITE:
            continue
        for brut in entrees:
            entree = _make_texte_porte_activite(
                activite, brut, stades_par_reference, resolveur)
            cle = _tp_key(entree)
            if cle not in existing_tp_keys:
                existing_tp_keys.add(cle)
                new_tp.append(entree)
                profil["textes_portes"].append(entree)

    # --- source ParlTrack dans sources[] ---
    has_parltrack_source = any(
        s.get("type") == "parltrack" and "dumps" in (s.get("url") or "")
        for s in (profil.get("sources") or [])
    )
    if not has_parltrack_source and (new_tp or new_amds):
        profil.setdefault("sources", []).append({
            "type": "parltrack",
            "url": _PARLTRACK_SOURCE_URL,
            "synchro_le": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })

    # --- licence ---
    # Recalculée depuis `sources[]`, qui vient de gagner (ou non) l'entrée
    # `parltrack` juste au-dessus : `licence_donnees` est un champ dérivé
    # depuis #530, et la composition « <licence AN/PE> + <licence ParlTrack> »
    # est désormais produite par `licences`, pour tout le corpus et pas
    # seulement ici. Le partage à l'identique ODbL de ParlTrack ne disparaît
    # donc que si la source disparaît du profil.
    appliquer_licence_donnees(profil)

    # Warning si aucune donnée retournée (dumps peut-être indisponibles)
    if not dossiers and not amendments and not retenus and not activites:
        # #642 — LE cas que l'issue nomme : un seul message disait deux
        # choses, à deux personnes différentes. « Vérifier la disponibilité des
        # dumps ou la validité du MEP ID » est une consigne qui nous est
        # adressée ; ce que le lecteur attend, c'est de savoir pourquoi la page
        # est vide, avec la source et la borne (§2 règle 2).
        #
        # Il n'existe pas de destinataire « mixte » : l'avertissement s'écrit
        # DEUX FOIS, dans les termes de chacun. Les deux préfixes sont
        # volontairement distincts — aucun n'est le préfixe de l'autre — pour
        # que l'union par famille de #600 les garde tous les deux. Le premier
        # reste un préfixe du message publié avant ce lot, ce qui range
        # l'ancienne forme dans la même famille et évite qu'elle survive à côté
        # de la nouvelle.
        warnings.append(avertissement(
            f"{WARNING_PREFIX_PARLTRACK_AUCUNE_DONNEE} trouvée pour le député européen "
            f"(identifiant ParlTrack {mep_id}) dans les dumps publiés sur "
            "parltrack.org/dumps.",
            DESTINATAIRE_LECTEUR,
        ))
        warnings.append(avertissement(
            f"{WARNING_PREFIX_PARLTRACK_DIAGNOSTIC} aucune donnée pour le MEP ID {mep_id}. "
            "Vérifier la disponibilité des dumps ou la validité du MEP ID.",
            DESTINATAIRE_INTERNE,
        ))

    # #683 — LE COMPTE DES SCRUTINS ÉCARTÉS SE PUBLIE. Un vote d'amendement
    # n'est pas un vote absent : sans ce décompte, un profil publierait 375
    # positions là où la source en porte 20 635, et la différence se lirait
    # comme une lacune de collecte (§2 règle 5, #511).
    if ecartes:
        warnings.append(avertissement(
            f"{WARNING_PREFIX_PARLTRACK_VOTES_ECARTES} {ecartes} scrutin(s) du Parlement "
            f"européen portent sur un amendement, un paragraphe ou un point de procédure : "
            f"seules les {len(retenus)} positions sur l'ensemble d'un texte sont publiées.",
            DESTINATAIRE_LECTEUR,
        ))

    # #683, puis #827 — LE DÉNOMINATEUR A CHANGÉ DE SENS. Il comptait « toutes
    # les explications », la source n'en liant aucune ; il compte désormais
    # celles qui restent sans lien une fois le document cherché. Deux causes,
    # que le message distingue parce qu'elles ne disent pas la même chose :
    # l'intitulé ne cite aucun document (271 des 1 801 mesurées, un fait sur la
    # source), ou le document cité n'existe pas (22, dont 17 transmis par une
    # autre institution).
    explications = [
        i for i in nouvelles_interv if i.get("type_detail") == "explication_de_vote"
    ]
    sans_lien = [i for i in explications if not i.get("source_url")]
    if sans_lien:
        sans_reference = sum(1 for i in sans_lien if reference_doceo(i.get("sujet")) is None)
        introuvables = len(sans_lien) - sans_reference
        detail = (
            f"{sans_reference} dont l'intitulé ne cite aucun document"
            if sans_reference else ""
        )
        if introuvables:
            detail += (", " if detail else "") + (
                f"{introuvables} dont le document cité est introuvable au Parlement"
            )
        warnings.append(avertissement(
            f"{WARNING_PREFIX_PARLTRACK_EXPLICATIONS_SANS_LIEN} {len(sans_lien)} des "
            f"{len(explications)} explication(s) de vote sont publiées sans lien vers le "
            f"document officiel ({detail}). Leur texte reste sourcé : ParlTrack transcrit "
            "l'annexe officielle de la séance.",
            DESTINATAIRE_LECTEUR,
        ))

    # #642 : jumeau typé recomposé en fin d'enrichissement — champ dérivé.
    deriver_avertissements(meta)
