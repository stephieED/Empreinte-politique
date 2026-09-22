#!/usr/bin/env python3
"""
merge_profile.py — Fusion additive de profils (brut ou pivot).

Objectif : quand un profil est régénéré à partir des API publiques (souvent
sujettes à des variations transitoires : pagination de recherche qui bouge,
requête HTML supplémentaire qui échoue ponctuellement...), on ne veut pas
perdre les données déjà obtenues lors d'une régénération précédente.

Principe : "une simple addition, jamais une suppression". Pour chaque liste
(votes, mandats, dossiers législatifs, interventions...), les entrées déjà
présentes dans le fichier existant sont conservées telles quelles ; seules
les entrées réellement nouvelles (dont la clé d'unicité n'apparaît pas déjà)
sont ajoutées. Aucune entrée existante n'est modifiée ni supprimée.

Pour les champs scalaires (identité, source des votes, synthèse d'activité...),
on garde la nouvelle valeur si elle est renseignée, sinon on retombe sur
l'ancienne (pour ne pas régresser vers `null` suite à un échec transitoire).

Le bloc `meta` est **composé clé par clé** (`fusionner_meta`, #600), et non pris
au dernier écrivain : `warnings` est l'union par famille des deux côtés,
`synchro_sources` est fusionné par source à la valeur la plus récente,
`genere_le` est le plus récent des deux, et chaque autre clé a une règle nommée
dans `REGLES_META`. Sans cela, l'ordre des jobs du workflow décidait quels
avertissements étaient publiés — et `meta.warnings[]` est le véhicule de la
règle « donnée manquante = donnée manquante » (AGENTS.md §2.5).

Les trois décisions à relire avant de toucher à une règle de fusion
--------------------------------------------------------------------
Trente-neuf décisions nomment une fonction de ce module ; la liste complète et à
jour est dans `docs/decisions-par-module.md`. Ces trois-là portent la politique,
pas un cas :

- `docs/decisions/bloc-sans-fond-484.md` — **« vide » n'est pas « sans fond ».**
  `_prefer_non_empty` ne testait que la vacuité : un squelette à huit clés dont
  sept valent `null` était « renseigné », donc il gagnait, et un job d'extraction
  a publié `identite: null` par-dessus une identité collectée. D'où
  `bloc_sans_fond` et `BLOCS_PROTEGES_DU_VIDE`.
- `docs/decisions/cle-fusion-interventions-540.md` — **une URL de source n'est pas
  un identifiant.** `merge_lists_by_key` est purement additive et ne peut rien
  perdre, sauf par sa clé : une clé qui colle fusionne des entrées distinctes
  sans qu'aucun garde-fou réagisse (7 767 interventions collectées, 891
  publiées). Ce qu'une clé `_pivot_*_key` a le droit d'être se lit là.
- `docs/decisions/couverture-listes-539.md` (décision 4) — **la seule exception à
  la règle additive.** `couverture` décrit le run, pas la personne : l'unir
  ferait survivre un `couvert` d'hier à côté de la panne d'aujourd'hui. Elle est
  remplacée, à la maille de la liste métier depuis
  `docs/decisions/couverture-remplacee-par-liste-602.md` (`fusionner_couverture`).

Usage :
    from merge_profile import merge_raw_profile, merge_pivot_profile
    profile = merge_raw_profile(old_profile, new_profile)
    pivot = merge_pivot_profile(old_pivot, new_pivot)

CLI (fusion de répertoires d'extraction parallèles) :
    python src/merge_profile.py --dirs artifacts/an artifacts/senat artifacts/ue \\
                                 --out raw_data/profiles
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from avertissements import (
    DESTINATAIRE_INTERNE,
    avertissement,
    deriver_avertissements,
    unir_tables_avertissements,
)
from candidate_profile import (
    WARNING_AUCUN_MANDAT_FR,
    WARNING_PREFIX_IDENTITE_INTROUVABLE,
    WARNING_PREFIX_MANDATS_INTROUVABLES,
    WARNING_PREFIX_VOTES_INTROUVABLES,
    WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
    WARNING_PREFIX_BUDGET_COLLECTE,
    WARNING_PREFIX_BUDGET_INTERVENTIONS,
    WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE,
    WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES,
    WARNING_PREFIX_QUESTIONS_INDISPONIBLES,
    WARNING_PREFIX_DEFAUT_COLLECTE,
)
from licences import appliquer_licence_donnees
from normalize_profil import (
    WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE,
    WARNING_PREFIX_CHAMBRES_NON_CORROBOREE,
    _profession_publiable,
)
from profil_brut import (
    CLE_ACTEUR_TRANCHE,
    CLE_CONTRIBUTION_PARTIELLE,
    CLE_MANIFESTE,
    CLE_TRANCHE_DERIVEE,
    PartitionIllisible,
    charger_profil_brut,
    chemin_socle,
    ecrire_profil_brut,
)
from schema_pivot import (
    COLLECTE_EXTRAIT,
    COLLECTE_THEME_SEUL,
    CAUSE_DEFAUT_COLLECTE,
    CAUSE_PANNE,
    ETAT_COUVERT,
    ETAT_FAIT_ETABLI,
    ETAT_HORS_COUVERTURE,
    ETAT_NON_COLLECTE,
    LISTES_COUVERTES,
    appliquer_chambres,
    deriver_tags_thematiques,
    rattacher_parole_aux_questions,
)
from titres_europeens import titre_sans_boutons

Key = Any


#: Rang d'une forme de collecte d'intervention : plus il est haut, plus
#: l'entrée porte de la prise de parole. L'absence de `collecte` est la forme
#: complète (#657) ; `sans_verbatim_source` n'a pas de rang — c'est un fait sur
#: la source, qu'aucune collecte ne changera.
_RANG_FORME = {COLLECTE_THEME_SEUL: 0, COLLECTE_EXTRAIT: 1, None: 2}


def _rang_forme(item: dict[str, Any]) -> Optional[int]:
    return _RANG_FORME.get(item.get("collecte"))


def promouvoir_forme_complete(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Remplace une intervention publiée sous une forme PLUS PAUVRE par celle,
    plus riche, que la collecte neuve apporte (#1029).

    Trois formes, dans cet ordre : réduite au thème (#657), extrait (#1029),
    complète. La fusion est additive : l'entrée ancienne gagne, et une entrée
    réduite le resterait pour toujours — c'est pourquoi #657 exemptait les
    candidats déclarés de la réduction. Quand les membres de roster passent à
    l'extrait, leurs 1 183 561 entrées publiées réduites au thème (22/09/2026,
    groupes et gouvernement) ne changeraient jamais sans ce report.

    **Dans un seul sens.** Une forme n'est jamais remplacée par une plus pauvre :
    un candidat déclaré, publié complet, qui entre dans un roster ne perd pas
    son verbatim.
    """
    neuves = {
        key_fn(item): item for item in (new_list or [])
        if isinstance(item, dict) and _rang_forme(item) is not None
    }
    if not neuves:
        return merged
    resultat = []
    for item in merged:
        neuve = neuves.get(key_fn(item)) if isinstance(item, dict) else None
        rang = _rang_forme(item) if isinstance(item, dict) else None
        if neuve is not None and rang is not None and _rang_forme(neuve) > rang:
            resultat.append(neuve)
        else:
            resultat.append(item)
    return resultat


def aligner_collecte_reduite(profil: dict[str, Any]) -> dict[str, Any]:
    """Aligne `meta.collecte_reduite.interventions` sur les entrées publiées
    (#1029).

    La déclaration suit `_declaration_du_run` : elle dit la forme du DERNIER
    run, et garde celle du précédent quand un run complet ne pose pas la clé.
    Après `promouvoir_forme_complete`, elle peut contredire les entrées. Elle
    dit désormais la forme LA PLUS PAUVRE encore publiée — `theme_seul` tant
    qu'une entrée l'est, sinon `extrait` —, et disparaît quand toutes sont
    complètes.
    """
    meta = profil.get("meta")
    reduite = meta.get("collecte_reduite") if isinstance(meta, dict) else None
    if not isinstance(reduite, dict) or "interventions" not in reduite:
        return profil
    formes = {i.get("collecte") for i in profil.get("interventions") or [] if isinstance(i, dict)}
    for forme in (COLLECTE_THEME_SEUL, COLLECTE_EXTRAIT):
        if forme in formes:
            reduite["interventions"] = forme
            return profil
    reste = {k: v for k, v in reduite.items() if k != "interventions"}
    if reste:
        meta["collecte_reduite"] = reste
    else:
        meta.pop("collecte_reduite")
    return profil


def reporter_id_syceron(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte `id_syceron` d'une intervention neuve sur l'entrée publiée qui ne
    l'a pas (#1087).

    La fusion est additive et l'entrée ancienne gagne : sans ce report, aucune
    des interventions publiées avant #1087 ne recevrait jamais son ancre. Le
    report ne touche QUE cette clé, et seulement quand elle manque : c'est un
    fait de la source (l'identifiant du paragraphe), pas une correction.
    """
    ancres = {
        key_fn(item): item["id_syceron"] for item in (new_list or [])
        if isinstance(item, dict) and item.get("id_syceron")
    }
    if not ancres:
        return merged
    for item in merged:
        if isinstance(item, dict) and not item.get("id_syceron"):
            ancre = ancres.get(key_fn(item))
            if ancre:
                item["id_syceron"] = ancre
    return merged


def merge_lists_by_key(
    old_list: Optional[list[dict[str, Any]]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Fusionne deux listes de dicts par clé d'unicité, en mode additif pur :
    les entrées de `old_list` sont toutes conservées inchangées ; seules les
    entrées de `new_list` dont la clé n'apparaît pas déjà dans `old_list`
    sont ajoutées (à la suite, dans leur ordre d'apparition)."""
    old_list = old_list or []
    new_list = new_list or []
    seen_keys = {key_fn(item) for item in old_list if isinstance(item, dict)}
    merged = list(old_list)
    for item in new_list:
        if not isinstance(item, dict):
            continue
        k = key_fn(item)
        if k in seen_keys:
            continue
        seen_keys.add(k)
        merged.append(item)
    return merged


#: Qualification sourcée d'un scrutin, telle que `_parse_scrutins_zip` la lit et
#: que `scrutins_index.CHAMPS_SCRUTIN` la republie (#639). Ce sont exactement les
#: champs que le rang 1 a fait entrer dans le parseur d'archives et dans les
#: index figés, et que le vote déjà collecté ne porte pas.
CHAMPS_QUALIFICATION_VOTE: tuple[str, ...] = ("type_scrutin", "type_vote", "demandeur")


def backfill_vote_qualification(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte la qualification d'un vote neuf sur l'entrée ancienne de même clé (#639).

    **Le maillon où la qualification se perdait.** Le rang 1 avait traité les
    deux bouts qu'il possédait — le parseur d'archives et les index figés — et
    `candidate_profile` recopie bien `type_scrutin`, `type_vote` et `demandeur`
    dans le vote qu'il écrit. Mais `merge_raw_profile` fusionne `votes[]` en
    additif pur : les 1 016 votes déjà collectés de `jean-luc-melenchon` portent
    la même clé `(numero_scrutin, date)` que les votes neufs, donc les anciens
    gagnent — tous les 1 016 sans `type_scrutin`, relevé à `4dda4d52`. Le profil
    brut n'acquérant jamais les champs, `build_scrutins_index.py`, qui le lit, ne
    pouvait que publier `type_scrutin: null` sur les 17 748 scrutins.

    Ni la collecte, ni la fusion, ni la construction d'index n'a échoué : chaque
    étape a fait ce qu'elle promet. C'est la transition qui perdait la donnée —
    même motif que #641, constaté le même jour, et **même trou que #492** sur
    `mandats[].chambre`, dont `backfill_mandat_chambre` ci-dessous est le jumeau.
    Les deux gardent leur copie de la mécanique : `tests/test_garde_fou_chambre.py`
    inventorie tout usage de la clé `"chambre"` par la fonction qui l'écrit, et un
    champ passé en tuple d'appel disparaîtrait de cet inventaire.

    Strictement croissant en information — ne remplit qu'un champ absent, vide ou
    nul, n'écrase rien, ne touche aucun autre champ, ne réordonne rien, ne crée
    aucune entrée. Et **la liste des champs est nommée** : reporter tout ce qui
    manque ferait de la fusion additive une fusion champ par champ, ce qu'elle
    n'est pas.

    **La clé de fusion ne change pas** : `_vote_key` reste
    `(numero_scrutin, date)`, `_pivot_vote_key` reste `scrutin_id`. Ajouter des
    champs à un vote sans toucher à sa clé est ce qui distingue ce report du
    défaut de #668, où c'est la clé elle-même qui avait changé de branche —
    468 doublons sur 940 entrées de `textes_portes`.
    """
    if not new_list:
        return merged

    qualifications_neuves: dict[Key, dict[str, Any]] = {}
    for v in new_list:
        if not isinstance(v, dict):
            continue
        renseignes = {c: v[c] for c in CHAMPS_QUALIFICATION_VOTE if v.get(c)}
        if renseignes:
            deja = qualifications_neuves.setdefault(key_fn(v), {})
            for champ, valeur in renseignes.items():
                deja.setdefault(champ, valeur)

    if not qualifications_neuves:
        return merged

    result: list[dict[str, Any]] = []
    for v in merged:
        if isinstance(v, dict):
            neuves = qualifications_neuves.get(key_fn(v))
            if neuves:
                manquants = {c: n for c, n in neuves.items() if not v.get(c)}
                if manquants:
                    v = {**v, **manquants}
        result.append(v)
    return result


#: Qualification sourcée d'un dossier législatif porté (#689) : la nature du
#: texte réellement déposé, lue par `gouvernement_textes.nature_texte_depose`.
#: Un seul champ, nommé — reporter tout ce qui manque ferait de la fusion
#: additive une fusion champ par champ, ce qu'elle n'est pas.
CHAMPS_QUALIFICATION_DOSSIER: tuple[str, ...] = ("nature_texte",)


def backfill_dossier_nature(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte la nature d'un dossier neuf sur l'entrée ancienne de même clé (#689).

    **Le maillon où la qualification se perdrait, pour la troisième fois.**
    `merge_raw_profile` fusionne `dossiers_legislatifs[]` en additif pur : les
    423 textes portés déjà collectés des 13 candidats déclarés portent la même
    clé `_dossier_key` que ceux d'une nouvelle collecte, donc les anciens
    gagnent — tous sans `nature_texte`. Le profil brut n'acquérant jamais le
    champ, `normalize_profil` ne pourrait que republier `role: "auteur"` sur les
    316 projets de loi du corpus, sans qu'aucune étape n'échoue. C'est le trou
    de #639 (`backfill_vote_qualification`) et celui de #492
    (`backfill_mandat_chambre`), au même endroit et pour la même raison : un
    filtre posé avant la fusion additive ne filtre rien.

    Strictement croissant en information — ne remplit qu'un champ absent, vide
    ou nul, n'écrase rien, ne touche aucun autre champ, ne réordonne rien, ne
    crée aucune entrée. **La clé de fusion ne change pas** : `_dossier_key`
    reste ce qu'elle était, et c'est ce qui distingue ce report du défaut de
    #668, où la clé elle-même avait changé de branche.

    Ce que ce report ne peut pas faire : requalifier un dossier qu'une nouvelle
    collecte ne rend pas. Un texte porté dont l'AN ne sert plus le dossier garde
    `nature_texte: null` et son `role: "auteur"` — un trou déclaré, pas un trou
    comblé (AGENTS.md §2 règle 5).
    """
    if not new_list:
        return merged

    qualifications_neuves: dict[Key, dict[str, Any]] = {}
    for d in new_list:
        if not isinstance(d, dict):
            continue
        renseignes = {c: d[c] for c in CHAMPS_QUALIFICATION_DOSSIER if d.get(c)}
        if renseignes:
            deja = qualifications_neuves.setdefault(key_fn(d), {})
            for champ, valeur in renseignes.items():
                deja.setdefault(champ, valeur)

    if not qualifications_neuves:
        return merged

    result: list[dict[str, Any]] = []
    for d in merged:
        if isinstance(d, dict):
            neuves = qualifications_neuves.get(key_fn(d))
            if neuves:
                manquants = {c: n for c, n in neuves.items() if not d.get(c)}
                if manquants:
                    d = {**d, **manquants}
        result.append(d)
    return result


#: Sujet d'une intervention et ses deux dérivés immédiats (#710). Trois champs,
#: nommés — reporter tout ce qui manque ferait de la fusion additive une fusion
#: champ par champ, ce qu'elle n'est pas. Seuls ceux que l'entrée neuve PORTE
#: sont reportés : l'étage brut n'a pas de `theme_officiel`, et une entrée pivot
#: réduite au thème (#657) n'a pas de `sujet`.
CHAMPS_SUJET_INTERVENTION: tuple[str, ...] = (
    "sujet",
    "theme_officiel",
    "sujet_code_grammaire",
)

#: Clé dont la PRÉSENCE, fût-elle à `None`, prouve qu'une entrée BRUTE sort du
#: parseur corrigé de #710. Une entrée écrite avant lui ne la porte pas du tout.
CLE_PREUVE_SUJET: str = "sujet_code_grammaire"


def _entree_syceron_publiee(i: dict[str, Any]) -> bool:
    """L'entrée pivot déclare-t-elle venir d'un compte rendu Syceron ? (#710)

    C'est la preuve dont dispose l'étage pivot, et elle est déjà publiée :
    `source.type`, que `normalize_profil` écrit sur les deux formes d'entrée, la
    réduite au thème comprise. Republier `sujet_code_grammaire` ici pour disposer
    du même critère qu'au brut coûterait ~48 octets sur chacune des 380 800
    entrées réduites du corpus, exactement le budget que #657 est allé chercher.
    """
    source = i.get("source")
    return isinstance(source, dict) and source.get("type") == "syceron"


#: `JJ/MM/AAAA`, la seule forme non-ISO que la collecte des questions a
#: publiée (#1044).
_DATE_JOUR_MOIS_AN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def normaliser_dates_interventions(entrees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reformate en ISO les dates d'intervention déjà publiées (#1044).

    **Pourquoi une passe, et pas un correctif de collecte seul.** Les
    interventions se fusionnent par `merge_lists_by_key` — additif pur,
    l'entrée ancienne gagne — aux deux étages, brut et pivot. Une date publiée
    une fois en `JJ/MM/AAAA` n'aurait donc **jamais** été corrigée par une
    régénération : c'est le défaut de #997, au même endroit et pour la même
    raison.

    Mesuré le 20/09/2026 sur les 1 217 384 interventions publiées : **715**
    entrées en `JJ/MM/AAAA`, sur 12 profils `candidat_declare`, toutes des
    questions. Les filtres par période comparent des chaînes ISO : ces entrées
    ne tombaient dans aucune fenêtre et disparaissaient sans être comptées
    comme écartées.

    **Ce n'est pas un backfill.** Les `backfill_*` reportent une information
    que la collecte neuve apporte ; ici rien n'est apporté, une valeur est
    **reformatée** — le jour désigné ne change pas, et la transformation se
    vérifie à l'œil. C'est pourquoi elle s'applique sans regarder `new`.

    **Les 167 dates vides étaient des questions au gouvernement** (mesuré le
    22/09/2026, toutes `sous_type: "QG"`) : la source ne publie jamais le texte
    d'une QG, posée à l'oral, et la date se lisait là. Elles reçoivent la date
    de parution au Journal officiel de leur compte rendu — `date_reponse`, que
    la source publie pour la question et la réponse à la fois (arbitré le
    22/09/2026). Une autre question sans date reste une absence (§2 règle 5).
    """
    for entree in entrees:
        if not isinstance(entree, dict):
            continue
        for champ in ("date", "date_reponse"):
            m = _DATE_JOUR_MOIS_AN.match(str(entree.get(champ) or ""))
            if m:
                jour, mois, annee = m.groups()
                entree[champ] = f"{annee}-{mois}-{jour}"
        if not entree.get("date") and entree.get("sous_type") == "QG" and entree.get("date_reponse"):
            entree["date"] = entree["date_reponse"]
    return entrees


def backfill_sujet_question(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte le sujet d'une question neuve sur la question publiée sans sujet (#1094).

    La XVe législature range le sujet d'une question sous `ANALYSE.ANA`, que le
    parseur ne lisait pas : ses questions ont été publiées `sujet: null`, et la
    fusion additive, où l'entrée ancienne gagne, les y aurait laissées. Le
    report ne remplit qu'un sujet ABSENT, et seulement sur une question
    officielle (`type_detail == "question"`) : il n'a rien à dire d'une
    intervention de séance, dont le sujet relève de `backfill_sujet_seance`.
    """
    sujets = {
        key_fn(i): i["sujet"] for i in (new_list or [])
        if isinstance(i, dict) and i.get("type_detail") == "question" and i.get("sujet")
    }
    if not sujets:
        return merged
    resultat: list[dict[str, Any]] = []
    for i in merged:
        if isinstance(i, dict) and i.get("type_detail") == "question" and not i.get("sujet"):
            sujet = sujets.get(key_fn(i))
            if sujet:
                i = {**i, "sujet": sujet}
        resultat.append(i)
    return resultat


def backfill_sujet_seance(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
    *,
    preuve: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    """Reporte le sujet d'une intervention neuve sur l'entrée ancienne (#710).

    **Cinquième occurrence de la même famille** — #492 (`mandats[].chambre`),
    #639 (`votes[]`), #641 (`identite.profession`), #696 (`texte_vise`) : un
    champ corrigé n'atteint jamais une entrée déjà collectée tout seul.
    `merge_lists_by_key` est additif pur et `_intervention_key` repose sur `id`,
    que la correction ne touche pas : sans ce report, les entrées déjà publiées
    garderaient indéfiniment le nom d'un créneau de séance en guise de sujet, et
    `tags_thematiques` en garderait le faux thème.

    **Ce report n'est pas monotone au sens des quatre précédents, et c'est le
    fait à déclarer.** Les autres ne remplissaient qu'un champ absent ; celui-ci
    RETIRE une valeur — 765 des 652 703 interventions publiées mesurées sur les
    législatures 16 et 17 le 02/09/2026, dont 310 perdent leur sujet et 455 le
    voient remplacé par celui de la question réellement posée. C'est une perte
    sur `tags_thematiques`, liste surveillée bloquante : elle se déclare par
    `allow_declared_losses`, jamais en désarmant le contrôle (AGENTS.md §3c).

    **Son critère est sourcé, pas « la nouvelle valeur gagne »** — comme
    `backfill_texte_vise` (#696), qui ne reporte que ce qui satisfait la grammaire
    des uid AN. La preuve est passée en argument parce qu'elle n'est pas la même
    aux deux étages, et qu'aucune des deux n'est un choix de commodité :

    - au BRUT, la présence de la clé `sujet_code_grammaire` — fût-elle à `None` :
      elle n'existe que depuis le parseur corrigé ;
    - au PIVOT, `source.type == "syceron"`, déjà publié sur les deux formes
      d'entrée (`_entree_syceron_publiee`). Y republier le code de point pour
      unifier le critère coûterait le budget que #657 est allé chercher.

    Une entrée neuve venue d'un autre chemin de collecte — questions de l'open
    data AN, entrées héritées de NosDéputés — ne satisfait ni l'une ni l'autre et
    n'est donc jamais touchée. C'est voulu : le critère structurel de #710 lit la
    grammaire des points d'un compte rendu, il n'a rien à dire d'une source qui
    n'en publie pas.

    **La clé de fusion ne change pas** : `_intervention_key` et
    `_pivot_intervention_key` restent ce qu'elles étaient, ce qui distingue ce
    report du défaut de #668, où la clé elle-même avait changé de branche.

    Ce que ce report ne peut pas faire : corriger une entrée qu'un run ne
    recollecte pas. Une législature non rejouée garde son sujet de créneau — un
    trou déclaré, pas un trou comblé (§2 règle 5).
    """
    if not new_list:
        return merged

    sujets_neufs: dict[Key, dict[str, Any]] = {}
    for i in new_list:
        if not isinstance(i, dict) or not preuve(i):
            continue
        # Seuls les champs que l'entrée neuve PORTE : une entrée réduite au thème
        # n'a pas de `sujet`, et lui en reporter un absent effacerait celui de
        # l'entrée complète qu'elle remplace (#657).
        sujets_neufs.setdefault(
            key_fn(i), {c: i[c] for c in CHAMPS_SUJET_INTERVENTION if c in i}
        )

    if not sujets_neufs:
        return merged

    result: list[dict[str, Any]] = []
    for i in merged:
        if isinstance(i, dict):
            neufs = sujets_neufs.get(key_fn(i))
            if neufs and any(i.get(c) != v for c, v in neufs.items()):
                i = {**i, **neufs}
        result.append(i)
    return result


def backfill_sujet_europeen(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Optional[Callable[[dict[str, Any]], Key]] = None,
) -> list[dict[str, Any]]:
    """Reporte sur une intervention européenne publiée le sujet que #938 a
    nettoyé (#980).

    #938 retire les boutons « PDF (… KB) DOC (… KB) » à l'indexation du dump :
    l'entrée neuve est propre. Mais `merge_lists_by_key` garde l'ancienne à
    identifiant égal, et `backfill_sujet_seance` ne vaut que pour Syceron.
    Mesuré le 16/09/2026 sur `origin/main` `966dd18a3`, après un run complet :
    **313** questions européennes des candidats déclarés gardaient leur sujet
    sale (Le Pen 147, Philippot 128, Mélenchon 38). Les textes portés, fusionnés
    par `merge_dossier_records` où l'entrée neuve gagne, s'étaient corrigés seuls.

    **Le critère est la règle de #938, pas « le neuf gagne »** : le sujet neuf
    remplace l'ancien seulement s'il est exactement `titre_sans_boutons(ancien)`.
    Un intitulé que la source aurait réécrit n'est pas touché. Seul `sujet`
    change, la clé de fusion ne bouge pas, et le nettoyage reste à l'entrée du
    corpus : ce report ne fait que laisser passer l'entrée qu'il a produite.

    Rien ne change au brut : les interventions européennes n'entrent qu'au pivot,
    par `enrich_pivot_with_parltrack`. `tags_thematiques` non plus : il dérive de
    `theme_officiel`, `null` sur toute entrée européenne.
    """
    if not new_list:
        return merged
    key_fn = key_fn or _pivot_intervention_key

    def _europeenne(i: Any) -> bool:
        source = i.get("source") if isinstance(i, dict) else None
        return isinstance(source, dict) and source.get("institution") == "parlement_europeen"

    sujets_neufs: dict[Key, str] = {}
    for i in new_list:
        if _europeenne(i) and isinstance(i.get("sujet"), str):
            sujets_neufs.setdefault(key_fn(i), i["sujet"])
    if not sujets_neufs:
        return merged

    result: list[dict[str, Any]] = []
    for i in merged:
        if _europeenne(i):
            neuf = sujets_neufs.get(key_fn(i))
            ancien = i.get("sujet")
            if neuf is not None and ancien != neuf and titre_sans_boutons(ancien) == neuf:
                i = {**i, "sujet": neuf}
        result.append(i)
    return result


def backfill_mandat_chambre(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte la `chambre` d'un mandat neuf sur l'entrée ancienne de même clé (#492).

    `merge_lists_by_key` est additif pur : l'entrée ancienne gagne, et sa clé
    (`categorie`, `fonction`, `label`, `debut`) ne contient pas la chambre.
    Sans ce report, un mandat déjà présent dans le corpus n'acquerrait **jamais**
    son estampille de chambre : la version neuve, estampillée, porte la même clé
    et serait écartée à chaque régénération. Le champ resterait à `null` pour
    toujours en fusion additive, et ne se remplirait qu'en `cold_start`/
    `--no-merge`.

    Le report est strictement croissant en information : il ne remplit qu'un
    champ **absent ou nul**, n'écrase jamais une chambre déjà déterminée, ne
    touche aucun autre champ et ne réordonne rien. C'est le même principe que
    `_prefer_non_empty` sur les scalaires, appliqué à un champ d'entrée de liste.
    Il est volontairement limité à `chambre` : généraliser le report ferait de la
    fusion additive une fusion par champ, ce qu'elle n'est pas.

    **Il ne délègue pas à `_reporter_champs_nommes`, et c'est délibéré.** La
    mécanique est la même que celle de `backfill_vote_qualification` (#639) —
    même trou, deux fois — mais `tests/test_garde_fou_chambre.py` inventorie
    tout usage de la clé `"chambre"` par la fonction qui l'écrit, et un champ
    passé en tuple d'appel disparaît de cet inventaire : le garde-fou de #494
    cesserait de voir l'endroit où la chambre d'un mandat est réellement posée.
    Vingt lignes en double coûtent moins qu'un inventaire qui ment.
    """
    if not new_list:
        return merged

    chambres_neuves: dict[Key, str] = {}
    for m in new_list:
        if not isinstance(m, dict):
            continue
        chambre = m.get("chambre")
        if chambre:
            chambres_neuves.setdefault(key_fn(m), chambre)

    if not chambres_neuves:
        return merged

    result: list[dict[str, Any]] = []
    for m in merged:
        if isinstance(m, dict) and not m.get("chambre"):
            chambre = chambres_neuves.get(key_fn(m))
            if chambre:
                m = {**m, "chambre": chambre}
        result.append(m)
    return result


def backfill_sort_texte_porte(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte le sort d'un dossier neuf sur l'entrée ancienne de même clé (#743).

    **Septième occurrence de la même famille** — #492, #639, #641, #696, #710,
    #718 : un champ ajouté au schéma n'atteint jamais une entrée déjà collectée
    tout seul. Ni `_dossier_key` (brut) ni `_pivot_texte_key` (pivot) ne
    contiennent le sort, donc l'entrée neuve qui le porte a la même clé que
    l'ancienne et serait écartée à chaque régénération.

    **Câblé au BRUT seulement, et c'est une mesure, pas une intuition.** La
    leçon de #729/#730 — « une correction doit passer les deux étages » — ne
    s'applique pas ici, parce que `textes_portes` ne se fusionne pas comme les
    autres listes : `merge_dossier_records` fait gagner l'entrée **neuve** en cas
    de collision de clé, là où `merge_lists_by_key` fait gagner l'ancienne. Le
    sort atteint donc le pivot de lui-même. Vérifié par mutation : décâbler ce
    report du brut fait échouer un test, le décâbler du pivot n'en fait échouer
    aucun — c'est ce qui a fait retirer le second, qui aurait été du code mort
    justifié par un raisonnement faux.

    Le report est strictement croissant : il ne remplit qu'un sort **absent**,
    n'écrase jamais un sort déjà posé, ne touche aucun autre champ et ne
    réordonne rien. `sort_non_resolu` suit le sort qu'il explique — les deux
    voyagent ensemble, sinon une entrée porterait un motif sans absence.
    """
    if not new_list:
        return merged

    sorts_neufs: dict[Key, dict[str, Any]] = {}
    for t in new_list:
        if not isinstance(t, dict):
            continue
        # Une entrée neuve DIT quelque chose du sort dès qu'elle porte l'un des
        # deux champs : un sort résolu, ou le motif de son absence. Exiger le
        # seul `sort` laisserait sans explication les dossiers sans décision.
        if t.get("sort") or t.get("sort_non_resolu"):
            sorts_neufs.setdefault(key_fn(t), {
                "sort": t.get("sort"),
                "sort_non_resolu": t.get("sort_non_resolu"),
            })

    if not sorts_neufs:
        return merged

    result: list[dict[str, Any]] = []
    for t in merged:
        if isinstance(t, dict) and not t.get("sort") and not t.get("sort_non_resolu"):
            neufs = sorts_neufs.get(key_fn(t))
            if neufs:
                t = {**t, **neufs}
        result.append(t)
    return result


def backfill_mandat_categorie_source(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte `categorie_source` d'un mandat neuf sur l'entrée ancienne (#718).

    **Sixième occurrence de la même famille** — #492 (`mandats[].chambre`), #639
    (`votes[]`), #641 (`identite.profession`), #696 (`texte_vise`), #710
    (`interventions[].sujet`) : un champ ajouté au schéma n'atteint jamais une
    entrée déjà collectée tout seul, et le remède est un report **nommé**, jamais
    une fusion plus permissive. `_mandat_key` ne contient pas le nouveau champ,
    donc l'entrée neuve estampillée porte la même clé que l'ancienne et serait
    écartée à chaque régénération.

    **Ce report est strictement monotone, et il n'écrit JAMAIS le contraire.**
    Il n'existe pas de valeur « héritée » : une entrée absente de la collecte
    neuve reste **sans clé**, ce qui dit « personne n'a établi sa catégorie » et
    non « sa catégorie est fausse ». La nuance est celle que #486 a payée — 29
    des 511 `mandat_electif` publiés sont des entrées que la source ne sert
    plus, et les accuser aurait été un fait faux de plus.

    Mesuré le 03/09/2026 sur 40 profils, contre l'archive AMO30 en cache :
    **3 188 mandats re-estampillés, 30 non** — dont 8 `fonction_gouvernementale`
    écrits par l'autre chemin sourcé (estampillés depuis) et 22 qui sont
    exactement le résidu NosDéputés que #718 cherche à sortir du dénominateur.
    """
    if not new_list:
        return merged

    sources_neuves: dict[Key, str] = {}
    for m in new_list:
        if not isinstance(m, dict):
            continue
        source_categorie = m.get("categorie_source")
        if source_categorie:
            sources_neuves.setdefault(key_fn(m), source_categorie)

    if not sources_neuves:
        return merged

    result: list[dict[str, Any]] = []
    for m in merged:
        if isinstance(m, dict) and not m.get("categorie_source"):
            source_categorie = sources_neuves.get(key_fn(m))
            if source_categorie:
                m = {**m, "categorie_source": source_categorie}
        result.append(m)
    return result


def backfill_mandat_organe_source(
    merged: list[dict[str, Any]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Reporte `sigle_organe` et `type_organe_source` d'un mandat neuf sur
    l'entrée ancienne (#863).

    **Septième occurrence de la famille** — #492, #639, #641, #696, #710, #718 :
    `_mandat_key` ne contient aucun des deux champs, donc l'entrée neuve qui les
    porte a la même clé que l'ancienne et serait écartée à chaque régénération.
    Le remède reste un report **nommé**, jamais une clé élargie (défaut de #668).

    **Monotone, et muet sur ce que la collecte neuve ne dit pas.** Un champ n'est
    posé que s'il est absent, et seule une valeur renseignée est reportée : une
    entrée qu'aucune collecte neuve ne couvre reste sans sigle et sans type, ce
    qui dit « la source ne l'a pas classée », jamais « elle n'a pas de sigle ».
    `sigle_organe_non_resolu` suit le même chemin : c'est le motif qui accompagne
    un sigle absent (§2 règle 5), pas une valeur de repli.
    """
    if not new_list:
        return merged

    neufs: dict[Key, dict[str, Any]] = {}
    for m in new_list:
        if not isinstance(m, dict):
            continue
        apports = {
            cle: m[cle]
            for cle in ("sigle_organe", "type_organe_source", "sigle_organe_non_resolu")
            if m.get(cle)
        }
        if apports:
            neufs.setdefault(key_fn(m), apports)

    if not neufs:
        return merged

    result: list[dict[str, Any]] = []
    for m in merged:
        if isinstance(m, dict):
            apports = neufs.get(key_fn(m))
            if apports:
                manquants = {k: v for k, v in apports.items() if not m.get(k)}
                if manquants:
                    m = {**m, **manquants}
        result.append(m)
    return result


def _prefer_non_empty(new_value: Any, old_value: Any) -> Any:
    """Garde `new_value` si elle est renseignée (non vide/non nulle), sinon
    retombe sur `old_value` (évite qu'un échec transitoire de collecte fasse
    régresser un champ scalaire vers `null`)."""
    if new_value not in (None, "", [], {}):
        return new_value
    return old_value


# --- Clés d'unicité, format brut (candidate_profile.py / candidate_profile_ue.py) ---

def _vote_key(v: dict[str, Any]) -> Key:
    return (v.get("numero_scrutin"), v.get("date"))


def _dossier_key(d: dict[str, Any]) -> Key:
    return (d.get("legislature"), d.get("id"))


def _mandat_key(m: dict[str, Any]) -> Key:
    return (m.get("categorie"), m.get("type"), m.get("label"), m.get("debut"))


def _intervention_key(i: dict[str, Any]) -> Key:
    return (i.get("id"), i.get("url") or i.get("url_detail"))


def _amendement_key(a: dict[str, Any]) -> Key:
    # `uid` d'abord : c'est le seul identifiant unique d'un amendement AN. Les
    # replis restent pour les entrées collectées avant son extraction (#431,
    # correction de clé du 18/08/2026) — `numero` seul ne distingue pas deux
    # amendements de textes différents, et `texte_vise` est tantôt un code
    # source, tantôt un titre résolu, ce qui fait passer le même amendement pour
    # deux entrées distinctes à la fusion.
    return a.get("uid") or a.get("source_url") or (a.get("numero"), a.get("texte_vise"), a.get("date"))


def _mandat_ue_key(m: dict[str, Any]) -> Key:
    return (m.get("type"), m.get("organisation_sigle"), m.get("role"), m.get("debut"))


#: Liste métier nommée par un warning `WARNING_PREFIX_DEFAUT_COLLECTE` (#562) ->
#: champ(s) du profil qui la portent. Les deux schémas sont couverts :
#: `dossiers_legislatifs` côté brut, `textes_portes` côté pivot.
_CHAMPS_PAR_LISTE_DEFAUT_COLLECTE: dict[str, tuple[str, ...]] = {
    "amendements": ("amendements",),
    "interventions": ("interventions",),
    "textes_portes": ("textes_portes", "dossiers_legislatifs"),
    "votes": ("votes",),
    "mandats": ("mandats",),
}


def _defaut_collecte_dementi_par_les_donnees(profile: dict[str, Any], warning: str) -> bool:
    """Un défaut de collecte que la fusion a démenti (#562).

    Même règle que pour « amendements indisponibles » juste en dessous, et pour
    la même raison : la fusion additive peut avoir restauré la liste depuis le
    fichier déjà publié. Continuer à la déclarer non collectée serait faux, et
    `couverture_profil` publierait un `non_collecte` sur une liste pleine.

    Le patron est celui du préfixe de panne, pas celui de
    `WARNING_PREFIX_BUDGET_*` (jamais retiré) : une troncature par budget décrit
    une liste dont le compte est incertain, un défaut de collecte décrit une
    étape qui n'a rien rendu du tout.
    """
    for liste, champs in _CHAMPS_PAR_LISTE_DEFAUT_COLLECTE.items():
        if warning.startswith(f"{WARNING_PREFIX_DEFAUT_COLLECTE} ({liste})"):
            return any(profile.get(champ) for champ in champs)
    return False


def _aucun_mandat_fr_dementi(profile: dict[str, Any], warning: str) -> bool:
    """Le profil minimal de #484, démenti par l'identité que la fusion a gardée.

    `WARNING_AUCUN_MANDAT_FR` n'est pas une trace de ce qu'un run n'a pas
    collecté (comme les préfixes de budget, jamais retirés) : c'est une
    AFFIRMATION sur la personne — « slug absent du référentiel Assemblée
    nationale, ou identité introuvable ». Une identité AN présente dans le
    profil fusionné dément ses deux membres à la fois.

    Le critère est l'identité, jamais `mandats` : un profil PE en publie
    (`jordan-bardella`, 22 mandats européens après normalisation) sans qu'aucun
    mandat FRANÇAIS soit connu. Purger sur `mandats` retirerait un avertissement
    vrai.
    """
    if not warning.startswith(WARNING_AUCUN_MANDAT_FR):
        return False
    identite = profile.get("identite")
    return isinstance(identite, dict) and not bloc_sans_fond(
        identite, BLOCS_PROTEGES_DU_VIDE["identite"]
    )


def _interventions_syceron_dementies(profile: dict[str, Any], warning: str) -> bool:
    """Les deux avertissements Syceron, démentis par les interventions publiées.

    L'union des warnings (#600) peut faire **ressusciter** l'avertissement d'un
    écrivain qui n'a pas obtenu l'archive Syceron, sur un profil où l'autre
    écrivain — ou la fusion additive — a rendu les interventions. Le laisser
    passer publierait une panne que le fichier dément, exactement ce que
    `_defaut_collecte_dementi_par_les_donnees` évite déjà pour les autres listes.
    C'est donc l'extension du mécanisme existant, pas un second mécanisme.

    Les deux familles de #560 sont couvertes ensemble, et le critère les
    distingue sans avoir à les séparer : `..._INDISPONIBLES` est une **panne**
    (l'archive n'a pas répondu), `..._AUCUNE` est un **constat de zéro**
    (l'archive a répondu, rien pour cet acteurRef) ; une intervention Syceron
    publiée dément l'un comme l'autre.

    Le critère est « une intervention qui n'est PAS une question », et non « des
    interventions » : les questions parlementaires viennent de l'open data AN,
    pas de Syceron (#510). Les compter éteindrait le constat Syceron avec la
    preuve d'une autre source — c'est le symétrique exact du critère que
    `_prune_stale_warnings` applique déjà à `WARNING_PREFIX_QUESTIONS_INDISPONIBLES`.
    """
    if not (
        warning.startswith(WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES)
        or warning.startswith(WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE)
    ):
        return False
    return any(
        isinstance(i, dict) and i.get("type_detail") != "question"
        for i in (profile.get("interventions") or [])
    )


def _prune_stale_warnings(profile: dict[str, Any]) -> None:
    """Retire les avertissements devenus obsolètes après fusion (ex. "votes
    introuvables" alors que les votes ont en fait été restaurés depuis
    l'ancien fichier)."""
    meta = profile.get("meta")
    if not isinstance(meta, dict) or not meta.get("warnings"):
        return
    filtered = []
    for w in meta["warnings"]:
        if w.startswith(WARNING_PREFIX_VOTES_INTROUVABLES) and profile.get("votes"):
            continue
        if w.startswith(WARNING_PREFIX_IDENTITE_INTROUVABLE) and profile.get("identite"):
            continue
        if w.startswith(WARNING_PREFIX_MANDATS_INTROUVABLES) and profile.get("mandats"):
            continue
        if w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES) and profile.get("amendements"):
            continue
        if _defaut_collecte_dementi_par_les_donnees(profile, w):
            continue
        if _aucun_mandat_fr_dementi(profile, w):
            continue
        if _interventions_syceron_dementies(profile, w):
            continue
        if (
            w.startswith(WARNING_PREFIX_QUESTIONS_INDISPONIBLES)
            and any(i.get("type_detail") == "question" for i in profile.get("interventions", []))
        ):
            continue
        filtered.append(w)
    meta["warnings"] = filtered


# Champs dont une collecte vide, en mode écrasement, détruirait des données
# acquises. Couvre les deux schémas : `dossiers_legislatifs` côté brut,
# `textes_portes` côté pivot.
CHAMPS_PROTEGES_DU_VIDE: tuple[str, ...] = (
    "votes", "mandats", "amendements", "dossiers_legislatifs",
    "interventions", "textes_portes",
)


# Même décision que ci-dessus (#465), étendue aux BLOCS STRUCTURÉS (#484).
#
# `CHAMPS_PROTEGES_DU_VIDE` ne couvrait que des listes, et une liste vide se
# reconnaît : `[]` est falsy. Un bloc, lui, peut être **vide de fond et truthy
# en même temps** — c'est le trou par lequel l'identité de `jean-luc-melenchon`
# a été écrasée le 29/08/2026 (run 33262372122). Le squelette écrit par
# `generate_all_profiles.build_minimal_profile` porte deux champs, et ces deux
# champs viennent de `raw_data/candidats.json`, pas d'une source parlementaire :
# `nom_complet` et `groupe_nom` (recopié de `parti`). Tout le reste est `null`.
# `_prefer_non_empty` voyait un dict non vide, donc « renseigné », et il gagnait
# sur un bloc collecté à l'AN.
#
# Un bloc n'a donc de « fond » que hors de ces champs-là : la valeur est la
# liste des champs qu'un profil minimal sait remplir **sans avoir rien demandé
# à personne**. Le jour où `build_minimal_profile` en remplit un de plus, il
# s'ajoute ici — et le test `test_merge_profile` le fait tomber sinon.
#
# La règle reste celle de #465, et pas une seconde règle en parallèle : seul le
# passage à **rien** est refusé. Un bloc qui apporte ne serait-ce qu'un champ de
# fond écrase normalement, ce qui laisse une correction aboutir.
BLOCS_PROTEGES_DU_VIDE: dict[str, tuple[str, ...]] = {
    "identite": ("nom_complet", "groupe_nom"),
}


def bloc_sans_fond(bloc: Any, champs_sans_source: tuple[str, ...]) -> bool:
    """Vrai si `bloc` est un dict dont aucun champ HORS `champs_sans_source`
    n'est renseigné — c'est-à-dire un bloc qui n'a rien appris d'une source.

    Un bloc absent (`None`) n'est pas « sans fond » : il est absent, et
    `_prefer_non_empty` sait déjà quoi en faire. La distinction compte, sinon
    ce prédicat répondrait la même chose à deux situations différentes.
    """
    if not isinstance(bloc, dict) or not bloc:
        return False
    return not any(
        valeur not in (None, "", [], {})
        for champ, valeur in bloc.items()
        if champ not in champs_sans_source
    )


def _est_marqueur_nil(valeur: Any) -> bool:
    """Le marqueur d'absence XML d'AMO30, sous ses deux formes publiées (#556).

    L'objet — `{"@xmlns:xsi": …, "@xsi:nil": "true"}` — et la **chaîne** dans
    laquelle `_format_lieu_naissance` l'a interpolé : la seconde est la pire des
    deux, parce qu'un `isinstance(..., str)` la laisse passer pour une donnée.

    La définition canonique vit dans
    `migrer_absences_publiees_556_558_560.est_marqueur_nil` / `nettoyer_valeur`.
    Elle est recopiée ici plutôt qu'importée : ce module est dans le chemin
    chaud du pipeline et n'a pas à dépendre d'un script de migration ponctuel.
    `test_merge_identite_601` vérifie que les deux lectures n'ont pas divergé.
    """
    if isinstance(valeur, dict):
        return str(valeur.get("@xsi:nil", "")).lower() == "true"
    return isinstance(valeur, str) and "@xsi:nil" in valeur


def valeur_de_source(valeur: Any) -> Any:
    """La valeur si une source l'a dite, `None` sinon.

    Trois formes d'absence, une seule réponse : le vide littéral, le marqueur
    XML d'AMO30 et la chaîne qui l'a interpolé. « Donnée manquante = donnée
    manquante » (§2.5) — et un marqueur n'est pas une donnée, c'est la façon
    dont AMO30 dit qu'il n'y en a pas.
    """
    if valeur in (None, "", [], {}):
        return None
    if _est_marqueur_nil(valeur):
        return None
    return valeur


def fusionner_identite(
    old_bloc: Any, new_bloc: Any, nom_bloc: str = "identite"
) -> Any:
    """`identite` composée **champ par champ**, jamais choisie en bloc (#601).

    Absorbe le palliatif de #597 (`_preferer_bloc_avec_fond`), qui rendait le
    *choix du gagnant* plus fin — « a du fond » plutôt que « n'est pas vide » —
    sans en changer la forme : un seul des deux blocs survivait. Si le job AN
    connaissait la `profession` et le job UE le `groupe_nom`, l'une des deux
    contributions était perdue. Le patron appliqué ici est celui qu'`identifiants`
    suit déjà depuis #539 : une règle de scalaire, par champ.

    Deux règles, et la seconde est ce qui reste de #484 :

    1. **Une absence n'écrase jamais une valeur connue** (§2.5). Un champ que le
       nouvel écrivain ne renseigne pas garde la valeur de l'ancien. Un marqueur
       `xsi:nil` compte comme une absence des deux côtés — s'il ressurgissait, il
       ne gagnerait pas, et un champ dont c'est le seul candidat est publié
       `null` plutôt que republié en plomberie XML.
    2. **Un bloc sans fond n'écrase pas les champs qu'il remplit sans source.**
       `BLOCS_PROTEGES_DU_VIDE` les nomme — `nom_complet`, `groupe_nom` — parce
       qu'ils viennent de `raw_data/candidats.json` chez l'écrivain minimal, pas
       d'une source parlementaire. Composer sans cette réserve laisserait le
       `groupe_nom` éditorial (« La France Insoumise (LFI) ») écraser le groupe
       parlementaire déclaré à l'AN, sur le seul motif que le job UE passe en
       dernier.

       La réserve ne s'applique **que** si l'ancien bloc, lui, a du fond : deux
       blocs pauvres face à face, il n'y a rien de mieux à protéger, et c'est le
       neuf qui parle. C'est exactement la condition de #597
       (`bloc_sans_fond(new) and not bloc_sans_fond(old)`), portée du bloc au
       champ.

    C'est cette seconde règle qui remplace le « choix » : elle dit ce qu'un bloc
    pauvre n'a pas le droit d'écraser, au lieu de dire lequel des deux gagne.
    """
    return _composer_identite(old_bloc, new_bloc, nom_bloc)[0]


#: Origine d'un champ composé, telle que `_composer_identite` la rend. Ce sont
#: les seuls verdicts possibles, et ils ne décrivent pas une source : ils disent
#: **de quel côté de la fusion** la valeur publiée vient. Nommer la source est le
#: travail de `deriver_provenance_champs`, qui lit ces verdicts (#603).
ORIGINE_NOUVELLE = "nouvelle"
ORIGINE_ANCIENNE = "ancienne"


def _composer_identite(
    old_bloc: Any, new_bloc: Any, nom_bloc: str = "identite"
) -> tuple[Any, dict[str, str]]:
    """La composition de #601, qui dit **en plus** d'où vient chaque champ.

    Une seule implémentation des trois branches : la provenance par champ (#603)
    ne peut pas être un second calcul qui rejoue les mêmes règles à côté. Deux
    lectures d'une même décision divergent — c'est exactement le piège que
    `_accorder_hatvp` a dû rattraper au #601, et il ne se rattrape que parce
    qu'un invariant le rendait détectable. Ici, rien ne le rendrait détectable :
    une provenance fausse est une provenance, et elle se lit comme une preuve.

    `fusionner_identite` reste la porte d'entrée pour qui n'a besoin que du bloc.
    """
    if not isinstance(new_bloc, dict):
        if isinstance(old_bloc, dict) and old_bloc:
            return old_bloc, {c: ORIGINE_ANCIENNE for c in old_bloc}
        return new_bloc, {}
    if not isinstance(old_bloc, dict) or not old_bloc:
        return dict(new_bloc), {c: ORIGINE_NOUVELLE for c in new_bloc}

    champs_sans_source = BLOCS_PROTEGES_DU_VIDE.get(nom_bloc, ())
    reserve = bloc_sans_fond(new_bloc, champs_sans_source) and not bloc_sans_fond(
        old_bloc, champs_sans_source
    )

    cles = list(new_bloc) + [c for c in old_bloc if c not in new_bloc]
    fusionne: dict[str, Any] = {}
    origines: dict[str, str] = {}
    for cle in cles:
        neuve = valeur_de_source(new_bloc.get(cle))
        ancienne = valeur_de_source(old_bloc.get(cle))
        if neuve is None:
            fusionne[cle] = ancienne
            origines[cle] = ORIGINE_ANCIENNE
        elif reserve and cle in champs_sans_source and ancienne is not None:
            fusionne[cle] = ancienne
            origines[cle] = ORIGINE_ANCIENNE
        else:
            fusionne[cle] = neuve
            origines[cle] = ORIGINE_NOUVELLE
    return fusionne, origines


#: Filtres de PUBLICATION du bloc `identite`, appliqués au bloc **composé**
#: (#641, réouverture du 31/08/2026).
#:
#: `normalize_profil` filtre déjà ce qu'il produit. Cela ne suffit pas : le bloc
#: publié n'est pas celui que la normalisation rend, c'est celui que
#: `_composer_identite` compose, et sa première règle est qu'« une absence
#: n'écrase jamais une valeur connue » (#601). Un champ que la collecte corrigée
#: ramène à `None` reprend donc la valeur DÉJÀ PUBLIÉE — c'est-à-dire exactement
#: celle que le filtre refuse.
#:
#: C'est ce qui sépare les deux volets de #641, tous deux verts en test et
#: mesurés sur le run 33395056902 :
#:
#: | Cas | Valeur neuve | Composition | Résultat avant ce correctif |
#: | --- | --- | --- | --- |
#: | préfixe parasite, 3 profils | `"Cadre de la fonction publique"` | renseignée → elle gagne | **réparé** |
#: | énoncé d'absence, 5 profils | `None` | absence → l'ancienne gagne | **inchangé** |
#:
#: Le filtre est donc posé APRÈS la composition, sur ce qui part au fichier, et
#: non sur l'un des deux côtés : c'est la seule position d'où il voit la valeur
#: réellement publiée, d'où qu'elle vienne. Il ne s'applique qu'à l'étage pivot
#: — `raw_data/` est source-proche (AGENTS.md §3), et le libellé y est
#: authentique : c'est sa publication comme profession qui ne l'est pas.
#:
#: La table est nommée champ par champ, jamais générale : `identite` porte des
#: libellés recopiés d'AMO30 (`schema_pivot.CHAMPS_IDENTITE_TEXTE_LIBRE`), et un filtre
#: s'appliquant à tous en inventerait la sémantique.
FILTRES_PUBLICATION_IDENTITE: dict[str, Callable[[Any], Any]] = {
    "profession": _profession_publiable,
}


def filtrer_identite_publiee(bloc: Any) -> Any:
    """Applique `FILTRES_PUBLICATION_IDENTITE` au bloc `identite` composé (#641).

    Strictement décroissant en information : ne peut que ramener un champ à
    `None`, n'ajoute aucune clé, n'invente aucune valeur de remplacement
    (AGENTS.md §2 règle 5 — la page dira « profession non renseignée »).
    Idempotent, donc sans effet sur un bloc que la normalisation vient de
    filtrer.
    """
    if not isinstance(bloc, dict):
        return bloc
    for champ, filtre in FILTRES_PUBLICATION_IDENTITE.items():
        if champ in bloc:
            bloc[champ] = filtre(bloc[champ])
    return bloc


def _accorder_hatvp(profil: dict[str, Any]) -> None:
    """`identite.uri_hatvp` et `identifiants.hatvp` disent la même chose (#601).

    Le second est la **recopie** du premier, jamais une seconde collecte : c'est
    l'invariant que `validate_profil` fait respecter, et deux valeurs différentes
    voudraient dire qu'une des deux est fausse sans dire laquelle. Or ce sont
    désormais deux compositions indépendantes — `identite` champ par champ,
    `identifiants` clé par clé — et rien ne garantissait qu'elles retiennent la
    même valeur.

    L'accord se fait dans les deux sens, parce que chacun peut être le seul à
    savoir : la composition d'`identite` peut restaurer une URI qu'`identifiants`
    n'a pas, et l'inverse est vrai depuis que `identifiants` existe (#539). Rien
    n'est inventé — les deux champs sortent de la même fabrique, et l'accord ne
    fait que le republier.
    """
    identite = profil.get("identite")
    identifiants = profil.get("identifiants")
    if not isinstance(identite, dict) or not isinstance(identifiants, dict):
        return
    uri = valeur_de_source(identite.get("uri_hatvp"))
    publie = valeur_de_source(identifiants.get("hatvp"))
    if uri is not None:
        identifiants["hatvp"] = uri
    elif publie is not None and "uri_hatvp" in identite:
        identite["uri_hatvp"] = publie


def preserver_collectes_non_vides(
    ancien: Optional[dict[str, Any]], nouveau: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """**Une collecte vide n'écrase jamais une collecte non vide** (#465).

    S'applique en mode écrasement (`--no-merge`), là où la fusion additive ne
    protège plus rien. Ce n'est pas une demi-fusion : un champ dont la collecte
    a rendu des entrées écrase normalement — c'est ce qui permet à une
    correction de clé d'aboutir (#440 : 2 018 amendements remplacés par 944).
    Seul le passage à **zéro** est refusé.

    Le motif est celui de #427 sur les gouvernements, où il est déjà énoncé :
    *distinguer « zéro constaté » de « collecte incomplète »*. Un `[]` rendu par
    une API en panne n'est pas un fait mesuré, et le publier violerait AGENTS.md
    §2.5. Les profils étaient le seul endroit qui ne l'appliquait pas.

    Ce que ça aurait évité, le 19/08/2026 (run `32302557156`, mode écrasement) :

    - `jean-luc-melenchon` — recherche d'identité en échec, profil minimal
      écrit : 18 721 amendements, 1 016 votes et 33 textes portés à zéro ;
    - `bruno-retailleau` — « votes introuvables » : 36 textes portés à zéro ;
    - `marine-le-pen` — **aucun avertissement**, amendements et votes intacts,
      23 textes portés à zéro.

    Le troisième cas est le plus instructif : rien, dans le profil écrit, ne
    signalait l'échec. Un garde-fou conditionné à la présence d'un avertissement
    ne l'aurait pas vu ; celui-ci ne regarde que le résultat.

    Renvoie `(profil, champs_preserves)` — la liste sert à le **dire**, jamais à
    corriger en silence.
    """
    if not ancien:
        return nouveau, []

    preserves: list[str] = []
    resultat = dict(nouveau)
    for champ in CHAMPS_PROTEGES_DU_VIDE:
        anciennes = ancien.get(champ)
        if not isinstance(anciennes, list) or not anciennes:
            continue
        if resultat.get(champ):
            continue
        resultat[champ] = anciennes
        preserves.append(champ)
    # Les BLOCS structurés, même règle (#484). Deux vides à couvrir, et le
    # second est celui qui a coûté l'identité de `jean-luc-melenchon` : le bloc
    # ABSENT (`identite: None`, collecte d'identité en échec) et le bloc SANS
    # FOND (le squelette du profil minimal, truthy). Le premier était déjà un
    # trou de #465 — sa propre mesure du 19/08/2026 le cite —, il n'était
    # simplement pas couvert par une boucle qui n'acceptait que des listes.
    for bloc, champs_sans_source in BLOCS_PROTEGES_DU_VIDE.items():
        ancien_bloc = ancien.get(bloc)
        if not isinstance(ancien_bloc, dict) or not ancien_bloc:
            continue
        if bloc_sans_fond(ancien_bloc, champs_sans_source):
            continue
        nouveau_bloc = resultat.get(bloc)
        if nouveau_bloc and not bloc_sans_fond(nouveau_bloc, champs_sans_source):
            continue
        resultat[bloc] = ancien_bloc
        preserves.append(bloc)
    return resultat, preserves


def _instant_synchro(valeur: str) -> tuple[int, str]:
    """Ordonne deux horodatages de synchro, offset compris.

    Le repli lexicographique n'est pas une commodité : le corpus publié porte
    des horodatages écrits par `time.strftime('%Y-%m-%dT%H:%M:%S%z')`, que
    `fromisoformat` accepte depuis 3.11 mais qui n'a pas toujours été le cas.
    Une chaîne illisible ne doit pas faire lever une fusion — elle passe
    derrière tout ce qui se parse.
    """
    try:
        return (1, datetime.fromisoformat(valeur).astimezone(timezone.utc).isoformat())
    except (TypeError, ValueError):
        return (0, valeur)


def _synchro_la_plus_recente(new_value: Any, old_value: Any) -> Any:
    """Un horodatage de synchro est une BORNE HAUTE, pas un scalaire (#484).

    `_prefer_non_empty` prend la valeur NEUVE dès qu'elle est renseignée. Sur
    `synchro_sources`, cette règle est à l'envers : le champ dit « la dernière
    fois que cette source a répondu », et un profil fusionné porte les données
    des DEUX côtés. Le run 33262372122 en donne la démonstration exacte — le job
    `extract-an` a resynchronisé AMO30 le 29/08 à 16:22, l'artifact du job
    `extract-ue-officiel`, fusionné après lui, portait le 19/08 recopié du
    profil committé, et c'est le 19/08 qui a été publié. La date publiée
    affirmait une panne de collecte que le run démentait.

    Prendre le plus récent des deux est la seule règle qui décrive le fichier
    écrit, quel que soit l'ordre de fusion — et l'ordre de fusion est un détail
    de la CI (`--dirs an ue roster`), pas un fait sur la donnée.
    """
    candidats = [v for v in (new_value, old_value) if isinstance(v, str) and v]
    if not candidats:
        return _prefer_non_empty(new_value, old_value)
    return max(candidats, key=_instant_synchro)


# ---------------------------------------------------------------------------
# `meta` : composé clé par clé, jamais pris au dernier écrivain (#600)
# ---------------------------------------------------------------------------
#
# Aux deux étages, `meta` était `dict(new)` : le bloc du DERNIER écrivain, pris
# entier. Conséquence mesurée par #599 sur le corpus committé — un profil sur les
# 477 de la population du défaut, `jean-luc-melenchon`, publie pour tout `meta`
# celui de `build_minimal_profile` : un `warnings` réduit à « aucun mandat
# français connu », pas de `collecte_ecartee`, et une synchro AN antérieure de
# 9,9 jours à son propre `genere_le`. Les avertissements de l'écrivain qui a
# collecté ses 1 016 votes ont disparu **sans trace**, et `meta.warnings[]` est
# le véhicule de la règle §2.5.
#
# La forme retenue est celle qui existait déjà pour `identifiants` (#539) : une
# règle par clé, et **aucune clé au hasard**. La règle par défaut n'est pas
# « prendre le nouveau » mais `_prefer_non_empty`, qui ne régresse jamais vers
# `null` — c'est la même règle que pour les scalaires du profil.

#: Le préfixe de `generate_all_profiles.WARNING_PREFIX_CHAMBRE_EN_ECHEC`,
#: recopié plutôt qu'importé : `generate_all_profiles` importe ce module, donc
#: l'importer d'ici serait circulaire. `test_merge_meta_600` vérifie que les
#: deux chaînes n'ont pas divergé — c'est le prix de la recopie, et il est payé.
_PREFIXE_CHAMBRE_EN_ECHEC = "collecte de chambre en échec"
_PREFIXE_DEUX_CHAMBRES = "carrière sur deux chambres"

#: Les deux familles ParlTrack de #642, recopiées de `normalize_parltrack_dumps`
#: plutôt qu'importées — même geste, et même prix, que les deux constantes
#: ci-dessus. Ici la raison n'est pas la circularité mais le poids : ce module
#: est importé par le portail de qualité et par tous les audits, et
#: `normalize_parltrack_dumps` tire `parltrack_dumps`, donc `zstandard` et les
#: dumps européens. `test_destinataire_avertissements_642` vérifie que les deux
#: chaînes n'ont pas divergé.
_PREFIXE_PARLTRACK_AUCUNE_DONNEE = "ParlTrack: aucune donnée"
_PREFIXE_PARLTRACK_DIAGNOSTIC = "ParlTrack (diagnostic) :"

#: Déclaré quand deux écrivains constatent LE MÊME JOUR, au même rang
#: d'interrogation de la source, des couvertures différentes pour une même liste
#: métier. Le cas n'est tranchable par aucune règle sur la donnée : il se
#: déclare, plutôt que de se choisir en silence sur l'ordre des jobs (#602).
#: Il est défini ici, et non dans la section `couverture` qui l'émet, parce que
#: `FAMILLES_WARNINGS` juste en dessous doit le connaître.
WARNING_PREFIX_COUVERTURE_DIVERGENTE = "couverture divergente non tranchée"

#: #683 — les deux constats de couverture européens. Recopiés ici plutôt
#: qu'importés de `normalize_parltrack_dumps`, comme les deux préfixes ParlTrack
#: juste au-dessus : ce module ne dépend d'aucun normaliseur.
#: #683 — le troisième constat ParlTrack, et celui que la première reprise
#: avait manqué : il affirme que les dumps étaient absents. Sur le run
#: `34377413730`, **les 6 profils enrichis le portaient encore**, hérité d'un run
#: où il était vrai, à côté de 1 977 votes qui viennent de ces mêmes dumps.
_PREFIXE_PARLTRACK_FALLBACK = "ParlTrack (fallback)"

_PREFIXE_PE_VOTES_ECARTES = "Parlement européen — votes non publiés :"
_PREFIXE_PE_EXPLICATIONS = "Parlement européen — explications de vote :"

#: Familles d'avertissements. Un warning appartient à la famille dont il porte
#: le préfixe ; à défaut, **il est sa propre famille** (dédoublonnage exact).
#:
#: La famille compte parce que l'union est par famille, pas par texte : plusieurs
#: de ces messages portent des COMPTEURS calculés sur le profil qui les émet
#: (« 2 mandat(s) électif(s) sans chambre », « chambres=['AN', 'Senat'] »). Une
#: union par texte publierait les deux comptes côte à côte, dont un faux — et
#: c'est exactement pour l'éviter que `merge_pivot_profile` teste déjà
#: `startswith` avant d'ajouter le warning de non-corroboration.
FAMILLES_WARNINGS: tuple[str, ...] = (
    WARNING_PREFIX_IDENTITE_INTROUVABLE,
    WARNING_PREFIX_MANDATS_INTROUVABLES,
    WARNING_PREFIX_VOTES_INTROUVABLES,
    WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
    WARNING_PREFIX_DEFAUT_COLLECTE,
    WARNING_PREFIX_QUESTIONS_INDISPONIBLES,
    WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE,
    WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES,
    WARNING_PREFIX_BUDGET_INTERVENTIONS,
    WARNING_PREFIX_BUDGET_COLLECTE,
    WARNING_AUCUN_MANDAT_FR,
    WARNING_PREFIX_CHAMBRES_NON_CORROBOREE,
    # #486 : porte un compteur de mandats, donc une famille, pour la même
    # raison que celui de #493 juste au-dessus — sans elle, deux écrivains qui
    # comptent sur des `mandats[]` différents publient leurs deux comptes côte
    # à côte, dont un faux. Cette famille manquait depuis #600.
    WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE,
    # #602 : porte la liste des listes divergentes, donc un compteur. Sans sa
    # famille, deux fusions successives publieraient deux énumérations côte à
    # côte, dont une périmée — le cas exact que cette table existe pour éviter.
    WARNING_PREFIX_COUVERTURE_DIVERGENTE,
    # #642 : le constat ParlTrack, scindé en deux familles — une par
    # destinataire. Elles entrent ici parce qu'elles portent un identifiant
    # (`MEP ID`), donc un compteur au sens de cette table : sans elles, deux
    # fusions successives publieraient deux identifiants côte à côte.
    _PREFIXE_PARLTRACK_AUCUNE_DONNEE,
    _PREFIXE_PARLTRACK_DIAGNOSTIC,
    # #683 : les deux constats de couverture européens portent des COMPTEURS
    # (« 18 709 scrutin(s) », « 179 explication(s) »). Sans leur famille, deux
    # fusions successives publient deux comptes côte à côte, dont un faux —
    # vérifié : 12 000 et 18 709 sur le même profil. C'est la raison d'être de
    # cette table, et l'oubli reproduisait exactement ce qu'elle prévient.
    _PREFIXE_PE_VOTES_ECARTES,
    _PREFIXE_PE_EXPLICATIONS,
    _PREFIXE_CHAMBRE_EN_ECHEC,
    _PREFIXE_DEUX_CHAMBRES,
)


def _famille_warning(warning: str) -> str:
    """La famille d'un avertissement, ou son texte s'il n'en a pas de connue.

    L'ordre de `FAMILLES_WARNINGS` compte : `WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE`
    et `..._INDISPONIBLES` sont deux préfixes distincts (#560) et aucun n'est le
    préfixe de l'autre, mais la recherche est faite du plus long au plus court
    pour qu'un futur préfixe emboîté ne rattache pas un message à la mauvaise
    famille.
    """
    for prefixe in sorted(FAMILLES_WARNINGS, key=len, reverse=True):
        if warning.startswith(prefixe):
            return prefixe
    return warning


def unir_warnings(
    new_warnings: Optional[list[Any]], old_warnings: Optional[list[Any]]
) -> list[str]:
    """**Union par famille** des avertissements des deux écrivains (#600).

    Le nouvel écrivain passe en premier et garde l'ordre dans lequel il a écrit
    ses messages ; ceux de l'ancien dont la famille n'est pas déjà représentée
    sont ajoutés à la suite. Deux propriétés en découlent, et ce sont les deux
    qu'on veut :

    1. **Rien ne disparaît sans être remplacé.** Un avertissement du job AN
       survit au passage du job UE, qui n'en sait rien. C'est le défaut de #600.
    2. **Rien n'est publié en double.** Un message à compteur — « 2 mandat(s)
       électif(s) sans chambre » — n'apparaît qu'une fois, dans la version du
       dernier écrivain, qui est celle calculée sur le profil le plus complet.

    Ce que cette fonction NE fait pas : décider si un avertissement est encore
    vrai. C'est le rôle de `_prune_stale_warnings` (étage brut) et du filtre de
    `merge_pivot_profile`, qui tournent **après** et que ce lot étend — un
    warning ressuscité de l'ancien fichier doit pouvoir s'éteindre comme les
    autres.
    """
    unis: list[str] = []
    familles: set[str] = set()
    for source in (new_warnings or [], old_warnings or []):
        for warning in source:
            if not isinstance(warning, str):
                continue
            famille = _famille_warning(warning)
            if famille in familles:
                continue
            familles.add(famille)
            unis.append(warning)
    return unis


def _horodatage_le_plus_recent(new_value: Any, old_value: Any) -> Any:
    """Le plus récent des deux horodatages, jamais celui du dernier écrivain.

    Même raison que `_synchro_la_plus_recente` : `genere_le` dit quand le travail
    publié a été fait, et le profil fusionné porte le travail des DEUX côtés.
    Prendre celui de `new` publierait la date d'un écrivain minimal sur un profil
    dont l'essentiel vient d'un autre — ou, dans l'autre sens, ferait *reculer*
    la date quand l'artifact fusionné est plus vieux que le fichier committé.
    """
    return _synchro_la_plus_recente(new_value, old_value)


def _fusionner_synchro_sources(new_value: Any, old_value: Any) -> Any:
    """`synchro_sources` fusionné **par source**, jamais recopié en bloc (#600).

    Le bloc était repris entier quand le nouveau profil n'en avait pas, et
    fusionné par clé sinon (#484/PR #597) : deux comportements pour une même
    clé, dont un qui recopie une fraîcheur qu'aucune source n'a confirmée. Ici,
    une seule règle — l'union des sources connues des deux côtés, chacune à sa
    valeur la plus récente. Une source qu'un seul écrivain connaît est donc
    conservée, et aucune ne régresse.
    """
    if not isinstance(new_value, dict):
        return dict(old_value) if isinstance(old_value, dict) else new_value
    if not isinstance(old_value, dict):
        return dict(new_value)
    return {
        source: _synchro_la_plus_recente(new_value.get(source), old_value.get(source))
        for source in sorted(set(old_value) | set(new_value))
    }


#: Sentinelle : la clé n'existe pas chez cet écrivain. Distincte de `None`, qui
#: est une valeur publiée (§2.5 : `null` dit « pas de déclaration », l'absence de
#: clé dit « ce producteur n'en parle pas »).
_ABSENTE = object()


def _declaration_du_run(new_value: Any, old_value: Any) -> Any:
    """La déclaration du nouvel écrivain **dès qu'il en fait une**, même vide.

    C'est la règle de `collecte_ecartee` (#539), et elle ne peut pas être
    `_prefer_non_empty` : une liste `[]` y signifie « ce run n'a rien écarté »,
    ce qui est une **affirmation**, pas une absence. `_prefer_non_empty` la
    prendrait pour un vide et rendrait la déclaration d'un run précédent — une
    liste écartée survivrait au run qui l'a collectée, et `couverture_profil`
    publierait `non_collecte` sur une liste pleine.

    L'ancienne valeur n'est rendue que si le nouvel écrivain **n'a pas la clé**,
    c'est-à-dire s'il n'a rien décidé qu'on sache : c'est le cas du chemin
    minimal, qui n'écrit pas `collecte_ecartee` du tout.
    """
    if new_value is _ABSENTE:
        return old_value
    return new_value


def _du_producteur_courant(new_value: Any, old_value: Any) -> Any:
    """La valeur du nouvel écrivain dès qu'il la porte, sans regarder l'ancienne.

    Pour `schema_version` : elle décrit le FORMAT qu'on écrit maintenant, pas la
    donnée. Retomber sur l'ancienne au motif que la nouvelle serait « vide »
    publierait une version de schéma que le fichier ne respecte pas.
    """
    if new_value is _ABSENTE:
        return old_value
    return new_value


def _regle_par_defaut(new_value: Any, old_value: Any) -> Any:
    """La règle des scalaires : la valeur neuve si elle est renseignée, l'ancienne
    sinon. Jamais une régression vers `null` (§2.5).

    C'est la règle de toute clé de `meta` que `REGLES_META` ne nomme pas — donc
    d'aucune clé du schéma publié aujourd'hui, mais de celles qu'un producteur
    ajouterait demain. Le défaut n'est **pas** « prendre le nouveau » : c'est
    précisément ce défaut-là que #600 corrige.
    """
    if new_value is _ABSENTE:
        return old_value
    if old_value is _ABSENTE:
        return new_value
    return _prefer_non_empty(new_value, old_value)


#: Une règle par clé de `meta`, et la raison de chacune. Le tableau couvre les
#: deux étages : `synchro_sources`/`collecte_ecartee` côté brut,
#: `schema_version`/`provenance` côté pivot, le reste des deux côtés.
#:
#: `provenance` n'est pas ici : elle a sa propre règle, plus forte que toutes
#: celles-ci (#189 — un `candidat_declare` n'est jamais rétrogradé), appliquée
#: par `merge_pivot_profile` APRÈS la composition. Le défaut la protège déjà
#: d'une régression vers `null`, ce qui est ce que surveille `audit_diff_profils`.
REGLES_META: dict[str, Callable[[Any, Any], Any]] = {
    "genere_le": _horodatage_le_plus_recent,
    "warnings": lambda new, old: unir_warnings(
        None if new is _ABSENTE else new, None if old is _ABSENTE else old
    ),
    "synchro_sources": lambda new, old: _fusionner_synchro_sources(
        None if new is _ABSENTE else new, None if old is _ABSENTE else old
    ),
    "collecte_ecartee": _declaration_du_run,
    # `collecte_reduite` (#657) : même règle, et pour la même raison. Elle dit la
    # FORME de ce que ce run a collecté ; la déclaration d'un run précédent ne
    # décrit pas celui-ci. La clé est ABSENTE quand la collecte est complète —
    # `_declaration_du_run` rend alors l'ancienne, ce qui est correct au sens
    # inverse aussi : un run qui n'a pas collecté d'interventions du tout
    # (`--skip-interventions`, donc pas de clé) ne doit pas effacer la forme des
    # entrées que la fusion additive conserve.
    "collecte_reduite": _declaration_du_run,
    "schema_version": _du_producteur_courant,
    # `licence_donnees` : la règle des scalaires, et rien de plus — elle est
    # RECALCULÉE après la fusion par `appliquer_licence_donnees` à l'étage pivot
    # (#530), qui a le dernier mot. La composer ici ne sert qu'à ne pas publier
    # un `null` transitoire à l'étage brut, où plus personne ne la relit depuis
    # que `normalize_profil` la dérive de `sources[]`.
    "licence_donnees": _regle_par_defaut,
    "provenance": _regle_par_defaut,
    # `provenance_champs` (#603) : même statut que `licence_donnees` ci-dessus —
    # la règle des scalaires ici, et RECALCULÉE après la fusion à l'étage pivot
    # par `deriver_provenance_champs`, qui a le dernier mot. Elle est nommée
    # quand même, parce que #600 refuse qu'une clé de `meta` soit prise « au
    # hasard » : le jour où un producteur en écrit une à l'étage brut, elle doit
    # avoir une règle plutôt qu'hériter du défaut sans que personne l'ait choisi.
    "provenance_champs": _regle_par_defaut,
    # `avertissements` (#642) : l'union des deux tables de destinataires, et
    # non la règle des scalaires. `warnings` est uni par famille juste
    # au-dessus, donc un avertissement peut venir de l'écrivain que la fusion
    # n'a pas retenu ; sans cette union, il reparaîtrait sans destinataire.
    # Le bloc est de toute façon RÉALIGNÉ après la fusion par
    # `deriver_avertissements`, qui a le dernier mot — même statut que
    # `licence_donnees` et `provenance_champs`.
    "avertissements": lambda new, old: unir_tables_avertissements(
        None if new is _ABSENTE else new, None if old is _ABSENTE else old
    ),
}


def fusionner_meta(
    old_meta: Optional[dict[str, Any]], new_meta: Optional[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    """Compose deux blocs `meta` clé par clé (#600).

    Aucune clé n'est prise « parce que son écrivain est passé en dernier » :
    chaque clé de l'union des deux blocs passe par la règle que `REGLES_META` lui
    donne, ou par `_regle_par_defaut` qui ne régresse jamais vers `null`.

    L'ordre des clés est celui du nouvel écrivain, complété par les clés que lui
    seul l'ancien portait : le diff git d'un profil publié ne bouge donc pas
    quand rien ne change.
    """
    if not isinstance(new_meta, dict):
        return dict(old_meta) if isinstance(old_meta, dict) else new_meta
    if not isinstance(old_meta, dict):
        return dict(new_meta)

    cles = list(new_meta) + [c for c in old_meta if c not in new_meta]
    fusionne: dict[str, Any] = {}
    for cle in cles:
        regle = REGLES_META.get(cle, _regle_par_defaut)
        fusionne[cle] = regle(
            new_meta.get(cle, _ABSENTE), old_meta.get(cle, _ABSENTE)
        )
    return fusionne


def merge_raw_profile(old: Optional[dict[str, Any]], new: dict[str, Any]) -> dict[str, Any]:
    """Fusionne un profil brut nouvellement généré (`new`) avec la version
    déjà présente sur disque (`old`, ou None si aucun fichier existant).
    Additif uniquement : ne supprime ni ne modifie aucune entrée déjà connue."""
    if not old:
        return new

    # #997 — ON PART DE `old`, ET `new` ÉCRIT PAR-DESSUS.
    #
    # Cette ligne était `dict(new)`, et elle effaçait tout champ que `new` ne
    # porte pas. Le défaut est resté invisible tant que chaque artifact
    # publiait le profil ENTIER : `new` portait toujours tous les champs.
    # Depuis qu'un job d'enrichissement ne publie que ce qu'il collecte
    # (`profil_brut.projeter_contribution`), une contribution réduite efface
    # les champs qu'aucune ligne ci-dessous ne rattrape.
    #
    # Mesuré sur le run 35442990475, corpus entier : **`mandat_senatorial`
    # perdu sur 2 profils** — Bruno Retailleau et Jean-Luc Mélenchon. Deux
    # champs seulement échappent au traitement explicite qui suit,
    # `mandats_locaux` et `mandat_senatorial` ; le premier n'a survécu que
    # parce que sa source passe en DERNIER dans `--dirs`. C'est de la chance,
    # pas un contrat.
    #
    # Ce que cela ne change pas : un champ que `new` porte gagne, **y compris
    # vide** — vider délibérément reste possible, et les protections du vide
    # (`CHAMPS_PROTEGES_DU_VIDE`, `_prefer_non_empty`) sont ailleurs. Seuls les
    # champs ABSENTS de `new` sont désormais conservés.
    merged = {**old, **new}

    # `meta` composé clé par clé (#600), là où c'était `dict(new)` : le bloc du
    # dernier écrivain, warnings compris. Le rattrapage de `synchro_sources` qui
    # vivait ici est absorbé par `_fusionner_synchro_sources`, qui applique la
    # même règle que le bloc soit présent des deux côtés ou d'un seul.
    meta_fusionne = fusionner_meta(old.get("meta"), new.get("meta"))
    if meta_fusionne is not None:
        merged["meta"] = meta_fusionne

    merged["identite"] = fusionner_identite(old.get("identite"), new.get("identite"))
    merged["chambre"] = _prefer_non_empty(new.get("chambre"), old.get("chambre"))
    merged["source"] = _prefer_non_empty(new.get("source"), old.get("source"))
    merged["votes_source"] = _prefer_non_empty(new.get("votes_source"), old.get("votes_source"))
    merged["mandats"] = backfill_mandat_chambre(
        backfill_mandat_organe_source(
            backfill_mandat_categorie_source(
                merge_lists_by_key(old.get("mandats"), new.get("mandats"), _mandat_key),
                new.get("mandats"),
                _mandat_key,
            ),
            new.get("mandats"),
            _mandat_key,
        ),
        new.get("mandats"),
        _mandat_key,
    )
    # #639 : la qualification (`type_scrutin`/`type_vote`/`demandeur`) est
    # reportée sur les votes déjà collectés. Sans elle, l'entrée ancienne gagne
    # et le profil brut n'acquiert jamais les trois champs — donc
    # `pivot_data/scrutins.json`, qui est construit depuis les profils bruts,
    # publie `type_scrutin: null` indéfiniment.
    merged["votes"] = sorted(
        backfill_vote_qualification(
            merge_lists_by_key(old.get("votes"), new.get("votes"), _vote_key),
            new.get("votes"),
            _vote_key,
        ),
        key=lambda v: v.get("date") or "",
        reverse=True,
    )
    # #997 — LA NEUVE GAGNE ICI AUSSI, comme au pivot depuis toujours.
    #
    # Cette liste se fusionnait en **additif pur** (`merge_lists_by_key`) :
    # l'entrée ancienne était conservée INCHANGÉE, et une entrée neuve de même
    # `_dossier_key` était simplement ignorée. Un dossier déjà collecté ne
    # pouvait donc plus rien apprendre d'une régénération — ni sa nature (#689),
    # ni son sort (#743), ni **son stade**.
    #
    # C'est ce qui a fait traverser QUATRE runs au correctif de #997 sans qu'il
    # atteigne le corpus. Le pivot, lui, fusionne par `merge_dossier_records`
    # (la neuve gagne) — mais il normalise depuis le brut, donc il recevait la
    # vieille valeur et n'avait rien à écraser. Les deux étages étaient
    # d'accord, sur une donnée périmée.
    #
    # Mesuré le 18/09/2026 sur Édouard Philippe, collecte réelle contre brut
    # publié : **290 dossiers de part et d'autre, exactement les mêmes clés,
    # aucun champ perdu**, et **118 transitions `examine_commission` →
    # `depose`** — `examine_commission` tombe de 127 à 9. C'est cette mesure,
    # et non un raisonnement, qui autorise le remplacement : la collecte ne
    # rend pas moins que ce qu'elle a rendu la fois d'avant.
    #
    # Le vide reste protégé en amont par `CHAMPS_PROTEGES_DU_VIDE` : une
    # collecte qui ne rend RIEN ne remplace rien, et un dossier que l'AN ne sert
    # plus reste publié tel quel (§2 règle 5).
    #
    # #689 et #743 : les deux reports restent en place. Sur le chemin nominal
    # ils n'ont plus rien à faire — la neuve porte déjà sa nature et son sort —
    # mais les retirer est un autre lot, avec sa propre mesure : ils sont la
    # seule chose qui rattrape une entrée que la fusion n'a pas remplacée.
    merged["dossiers_legislatifs"] = sorted(
        (
            d for d in backfill_sort_texte_porte(
                backfill_dossier_nature(
                    merge_dossier_records(old.get("dossiers_legislatifs"), new.get("dossiers_legislatifs"), _dossier_key),
                    new.get("dossiers_legislatifs"),
                    _dossier_key,
                ),
                new.get("dossiers_legislatifs"),
                _dossier_key,
            )
            if d.get("role")  # écarte la liste globale héritée de NosDéputés (mêmes dossiers
                              # pour tout le monde sur une législature, role toujours absent/null
                              # — voir candidate_profile.fetch_textes_portes_officiels)
        ),
        key=lambda d: (d.get("date_max") or "", d.get("titre") or ""),
        reverse=True,
    )
    # #710 : le sujet corrigé est reporté sur les interventions déjà collectées.
    # Sans lui, l'entrée ancienne gagne et le profil brut garderait indéfiniment
    # le nom d'un créneau de séance — donc `normalize_profil` republierait le faux
    # thème dans `theme_officiel` puis dans `tags_thematiques`.
    merged["interventions"] = normaliser_dates_interventions(backfill_sujet_question(backfill_sujet_seance(
        reporter_id_syceron(promouvoir_forme_complete(
            merge_lists_by_key(old.get("interventions"), new.get("interventions"), _intervention_key),
            new.get("interventions"),
            _intervention_key,
        ), new.get("interventions"), _intervention_key),
        new.get("interventions"),
        _intervention_key,
        preuve=lambda i: CLE_PREUVE_SUJET in i,
    ), new.get("interventions"), _intervention_key))
    # merge_dossier_records (nouvelle valeur gagne en cas de collision, aucune perte
    # sinon) : un echec/vide transitoire de l'open data amendements ne doit pas
    # effacer des amendements deja collectes lors d'une regeneration precedente.
    merged["amendements"] = merge_dossier_records(old.get("amendements"), new.get("amendements"), _amendement_key)

    old_ue = old.get("mandat_europeen")
    new_ue = new.get("mandat_europeen")
    if old_ue or new_ue:
        merged_ue = dict(new_ue or old_ue or {})
        merged_ue["mandats_europeens"] = sorted(
            merge_lists_by_key(
                (old_ue or {}).get("mandats_europeens"),
                (new_ue or {}).get("mandats_europeens"),
                _mandat_ue_key,
            ),
            key=lambda m: m.get("debut") or "",
            reverse=True,
        )
        merged["mandat_europeen"] = merged_ue

    _prune_stale_warnings(merged)
    # #642 : étage brut aussi — le profil brut est écrit sur disque, et c'est ce
    # bloc qui fait franchir au destinataire l'aller-retour JSON jusqu'à la
    # passe pivot.
    deriver_avertissements(merged.get("meta"))
    aligner_collecte_reduite(merged)  # #1029 voie 3 : la déclaration suit les entrées
    return merged


# --- Clés d'unicité, format pivot v1 (schema_pivot.py) ---


def retirer_constats_parltrack_perimes(profil: dict[str, Any]) -> None:
    """Retire le constat « ParlTrack : aucune donnée » d'un profil qui en porte (#683).

    ## Le défaut

    `unir_warnings` garde un avertissement de l'ancien écrivain **dont la
    famille n'est pas représentée par le nouveau**. C'est ce qui protège un
    constat que le run du jour n'a pas eu l'occasion de refaire. Mais un run qui
    trouve des données n'émet aucun message de la famille « aucune donnée » — et
    l'ancien survit donc, intact.

    Mesuré avant correction : le profil de `jordan-bardella` aurait publié
    « ParlTrack : aucune donnée trouvée pour le député européen 131580 » à côté
    de **1 926 votes, 525 amendements et 255 interventions** du Parlement
    européen. Le constat était vrai le jour où il a été écrit ; il devient faux
    le jour où la lecture est réparée, et rien ne l'aurait retiré.

    **Trois familles, et la première version n'en visait que deux.** Le run
    `34377413730` a publié le troisième constat — « ParlTrack (fallback) : dumps
    absents ce run » — sur **les 6 profils enrichis**, à côté des votes qui
    viennent précisément de ces dumps. Même mécanisme, même correctif : c'est
    l'énumération qui était incomplète, pas la règle.

    ## Pourquoi une reprise, et pas une famille de plus

    Même patron que `clean_stale_interventions` et `clean_stale_textes_portes` :
    une entrée écrite sous un régime révolu ne se corrige pas en changeant la
    règle de fusion, elle se retire sur **preuve**. La preuve ici est le corpus
    lui-même — une entrée européenne dans une des quatre listes — et non le
    succès d'un appel, qui ne survivrait pas au prochain run.

    Une absence qui redeviendrait vraie se réécrira d'elle-même : l'enrichissement
    republie le constat dès qu'il ne trouve rien (§2 règle 5).
    """
    meta = profil.get("meta")
    if not isinstance(meta, dict):
        return
    warnings = meta.get("warnings")
    if not isinstance(warnings, list) or not warnings:
        return
    if not _porte_du_materiau_europeen(profil):
        return
    meta["warnings"] = [
        w for w in warnings
        if not (
            isinstance(w, str)
            and w.startswith((
                _PREFIXE_PARLTRACK_AUCUNE_DONNEE,
                _PREFIXE_PARLTRACK_DIAGNOSTIC,
                _PREFIXE_PARLTRACK_FALLBACK,
            ))
        )
    ]


#: Où l'institution se lit, liste par liste — même table que
#: `couverture_profil._CHEMINS_INSTITUTION`, et pour la même raison : le marqueur
#: est porté par l'entrée, jamais deviné depuis une URL.
_CHEMINS_INSTITUTION_PE: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("votes", ("scrutin_non_resolu", "institution")),
    ("amendements", ("amendement_non_resolu", "institution")),
    ("textes_portes", ("institution",)),
    ("interventions", ("source", "institution")),
)


def _porte_du_materiau_europeen(profil: dict[str, Any]) -> bool:
    """Au moins une entrée publiée vient du Parlement européen."""
    for liste, chemin in _CHEMINS_INSTITUTION_PE:
        for entree in profil.get(liste) or ():
            valeur: Any = entree
            for cle in chemin:
                if not isinstance(valeur, dict):
                    valeur = None
                    break
                valeur = valeur.get(cle)
            if valeur == "parlement_europeen":
                return True
    return False


def _pivot_vote_key(v: dict[str, Any]) -> Key:
    """Identité d'un vote pivot depuis sa normalisation (#432).

    `scrutin_id` porte déjà `(legislature, numero_scrutin)` : il identifie le
    scrutin sans ambiguïté, là où `numero_scrutin` seul confondrait deux
    législatures. Le repli sur l'enregistrement complet couvre les votes non
    résolus, qui n'ont pas d'identifiant : les traiter tous comme la même clé
    `None` les fusionnerait en un seul — une perte silencieuse.
    """
    scrutin_id = v.get("scrutin_id")
    if scrutin_id:
        return scrutin_id
    non_resolu = v.get("scrutin_non_resolu") or {}
    return ("non_resolu", non_resolu.get("numero_scrutin"), non_resolu.get("date"))


def _pivot_mandat_key(m: dict[str, Any]) -> Key:
    return (m.get("label"), m.get("categorie"), m.get("fonction"), m.get("debut"))


def _repli_texte_key(t: dict[str, Any]) -> Key:
    """Le repli d'identité d'un texte porté : titre + date_min + législature.

    Extrait de `_pivot_texte_key` pour que la reprise `clean_stale_textes_portes`
    interroge **exactement** la branche sur laquelle les entrées héritées sont
    keyées — une reprise qui recalcule le repli de son côté dérive de la clé
    qu'elle est censée réconcilier.

    `date_max` en est volontairement absent : c'est un agrégat qui avance au fil
    de la procédure, et l'inclure ferait apparaître le même dossier comme neuf à
    chaque étape franchie.
    """
    return ("repli", t.get("titre"), t.get("date_min"), t.get("legislature"))


def _pivot_texte_key(t: dict[str, Any]) -> Key:
    """Identité d'un dossier législatif porté : son `dossier_id` AN (#668).

    `role`/`type_rapport`/`stade_procedural` sont hors de la clé : les inclure
    ferait fusionner en double une même entrée dès qu'une régénération produit
    une valeur différente (ex. données historiques erronées conservées
    indéfiniment).

    **`source_url` en est sorti, et c'est la correction de #668.** La clé était
    `source_url or (titre, date_min, legislature)`. Le rang 2 de #639 a réparé
    `_normalize_texte_porte`, qui publiait `source_url: null` sur 472 / 472
    entrées ; au run suivant, les entrées déjà publiées étaient keyées sur le
    **repli** et leurs jumelles renormalisées sur **`source_url`**. Deux clés
    incomparables pour un même dossier : `merge_dossier_records` a conservé les
    deux, et le corpus a publié 940 entrées pour 472 dossiers réels — 468
    doublons sur 22 profils, en ligne. C'est le mode de défaillance que #540
    décrit déjà pour les interventions, à ceci près qu'ici la clé n'est pas
    *collante* mais **volatile** : ce n'est pas la donnée qui a changé, c'est la
    branche du `or` que l'objet emprunte.

    **Une URL n'est de toute façon pas un identifiant** (#540). `dossier_id`
    (`DLR5L15N37607`, publié depuis #639) est l'identifiant AN du dossier, le
    même que `dossiers_legislatifs[].id` au brut — les deux étages disent donc
    la même chose de ce qu'est un dossier, la seule forme qui garantisse qu'une
    entrée collectée arrive publiée une fois et une seule. Mesuré sur
    `origin/main` le 31/08/2026 : 472 / 472 entrées issues du brut le portent,
    et `source_url` ne discrimine rien de plus (0 repli portant deux
    `dossier_id` distincts sur les 940 entrées publiées).

    **Ce que deviennent les entrées sans `dossier_id`** : elles gardent le
    repli. Le `or` — donc le risque de bascule — subsiste, parce qu'aucune clé
    ne peut lire un identifiant qu'une entrée ne porte pas ; le supprimer
    reviendrait à réduire toutes ces entrées à une seule clé `None`, la perte
    silencieuse que `_pivot_vote_key` décrit (#432). Ce qui neutralise la
    bascule n'est pas la clé, c'est la **reprise** : voir
    `clean_stale_textes_portes`, qui réconcilie une entrée sans identifiant avec
    sa jumelle identifiée au lieu de laisser les deux cohabiter.

    **Alternative écartée : keyer *toujours* sur le repli**, ce qui supprimerait
    le `or` par construction. Mesuré discriminant aujourd'hui (0 collision),
    mais il rend l'identité du dossier otage de son libellé : une correction
    typographique du titre à l'AN, ou un `date_min` qui recule d'un document
    versé après coup, republierait le dossier comme une entrée neuve — le même
    doublon, sans identifiant pour le rattraper cette fois.
    """
    dossier_id = t.get("dossier_id")
    if dossier_id:
        return ("dossier_id", dossier_id)
    doceo = _document_doceo(t)
    if doceo:
        return ("doceo", doceo)
    return _repli_texte_key(t)


#: Le nom d'un document du Parlement européen dans son adresse publique :
#: `…/doceo/document/B-8-2015-0293_EN.html` → `B-8-2015-0293`. Le schéma n'est
#: pas lu — 625 `source_url` du corpus sont en `http://` et 56 en `https://`
#: (mesuré le 16/09/2026), et une clé qui les distinguerait rejouerait la bascule
#: de #668 le jour où la collecte changera de forme.
_DOCEO = re.compile(r"doceo/document/([A-Z]+-\d+-\d{4}-\d{4})")


def _document_doceo(t: dict[str, Any]) -> Optional[str]:
    """L'identité d'un texte porté EUROPÉEN : le document qu'il est (#901).

    **Le défaut que cette branche corrige, mesuré le 16/09/2026** : 311 textes
    portés européens publiés deux fois dans le même profil — Philippot 250,
    Le Pen 57, Mélenchon 4. Un texte européen n'a pas de `dossier_id` : il était
    donc keyé sur le **repli**, qui contient le titre. #938 a retiré des titres
    les libellés des boutons de téléchargement (« … PDF (181 KB) DOC (45 KB) »),
    le repli a changé, et chaque texte est revenu comme une entrée neuve à côté
    de l'ancienne. C'est exactement l'« alternative écartée » que la docstring
    de `_pivot_texte_key` décrit : une identité otage de son libellé.

    Le document `doceo` est un identifiant, pas un libellé : `B-8-2015-0293`
    désigne un document déposé et un seul. Mesuré sur les 694 entrées
    européennes publiées : 681 en portent un, et **aucun** n'est partagé par deux
    textes réellement différents d'un même profil.

    **Pourquoi pas `reference_dossier`**, qui existait déjà : elle désigne une
    PROCÉDURE, et plusieurs textes vivent dans la même. Chez Emmanuel Maurel,
    l'avis (« OPINION on the role of EU development policy… », sans URL) et la
    fiche du dossier dont il est rapporteur (URL OEIL) partagent `2023/2031(INI)`
    — une clé sur la référence en aurait supprimé un.

    Les 13 entrées sans document `doceo` (fiches OEIL, avis sans lien) gardent
    leur clé : rien ne change pour elles.
    """
    if t.get("institution") != "parlement_europeen":
        return None
    m = _DOCEO.search(t.get("source_url") or "")
    return m.group(1) if m else None


def _acteur_du_socle(profils_dir: Path, slug: str) -> Optional[str]:
    """L'acteur déclaré par une tranche dérivée du socle déjà écrit (#691).

    Rend `None` si le profil n'est pas partitionné, n'a aucune tranche
    dérivée, ou n'est pas relisible. **`None` ne marque rien**, donc la
    fusion réécrit alors la partition telle qu'elle l'a trouvée : ne pas
    savoir n'est jamais une raison de changer de forme.
    """
    try:
        with open(chemin_socle(profils_dir, slug), encoding="utf-8") as fichier:
            socle = json.load(fichier)
    except (OSError, json.JSONDecodeError):
        return None
    manifeste = socle.get(CLE_MANIFESTE) if isinstance(socle, dict) else None
    if not isinstance(manifeste, dict):
        return None
    for declaree in (manifeste.get("tranches") or []):
        if isinstance(declaree, dict) and declaree.get(CLE_TRANCHE_DERIVEE):
            acteur = declaree.get(CLE_ACTEUR_TRANCHE)
            if acteur:
                return str(acteur)
    return None


def merge_dossier_records(
    old_list: Optional[list[dict[str, Any]]],
    new_list: Optional[list[dict[str, Any]]],
    key_fn: Callable[[dict[str, Any]], Key],
) -> list[dict[str, Any]]:
    """Fusionne deux listes de dossiers par identité : contrairement à
    `merge_lists_by_key`, la nouvelle entrée remplace l'ancienne en cas de
    collision de clé (le rôle/stade procédural peut être corrigé d'une
    régénération à l'autre) ; les dossiers absents de `new_list` restent
    conservés."""
    old_list = old_list or []
    new_list = new_list or []
    by_key: dict[Key, dict[str, Any]] = {}
    order: list[Key] = []
    for item in old_list + new_list:
        if not isinstance(item, dict):
            continue
        k = key_fn(item)
        if k not in by_key:
            order.append(k)
        by_key[k] = item
    return [by_key[k] for k in order]


def clean_stale_textes_portes(
    textes: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Reprise des entrées écrites avant #639, sur le patron de
    `clean_stale_interventions` (#540).

    **La fonction existait déjà, sous ce nom, pour le même motif** — les
    doublons hérités d'une clé incluant `role`, avant que `type_rapport` et
    `stade_procedural` rejoignent le schéma. Deux choses ont changé avec #668.

    D'abord son critère de départage : « conserver l'entrée la plus complète au
    sens du schéma » (`type_rapport` et `stade_procedural` présents) **ne
    discrimine plus rien**. Mesuré sur `origin/main` le 31/08/2026, les 940
    entrées publiées portent toutes les deux clés ; les deux versions d'un même
    dossier auraient été départagées au hasard de l'ordre de la liste. Le
    départage se fait donc sur l'**identifiant** : `dossier_id`, et avec lui
    `source_url`, que porte la seule version renormalisée.

    Ensuite son appel : elle n'était **appelée nulle part** — ni par
    `merge_pivot_profile`, ni par la passe pivot, ni par un script. Un
    nettoyage que rien n'exécute n'a jamais nettoyé quoi que ce soit ; c'est la
    seconde moitié de la régression, et pourquoi les 468 doublons ont survécu à
    chaque run depuis. `merge_pivot_profile` l'appelle désormais, à
    l'emplacement exact où il appelle `clean_stale_interventions`.

    Règle appliquée : une entrée **sans** `dossier_id` est écartée quand au
    moins une entrée **avec** `dossier_id` porte le même repli d'identité
    `(titre, date_min, legislature)`. Elle est alors, par construction, la même
    entrée avant sa renormalisation : c'est exactement la clé sur laquelle la
    fusion l'avait rangée.

    Elle ne peut donc rien perdre. Sans jumelle identifiée sur ce repli —
    collecte en échec, dossier disparu de l'open data AN, entrée héritée d'une
    source qui ne publiait pas d'identifiant — rien n'est écarté et l'ancienne
    entrée reste publiée (`docs/decisions/collecte-vide-necrase-jamais.md`). Et
    elle ne confond pas un doublon avec un texte réellement porté deux fois :
    deux dossiers de même titre à des dates ou législatures différentes ont des
    replis différents, et deux `dossier_id` distincts n'ont jamais été mesurés
    sur un même repli (0 sur les 940 entrées publiées).

    Effet mesuré sur les 22 profils qui publient des textes portés : 940 → 472
    entrées, soit exactement les 472 dossiers que porte le brut, 468 retirées.
    C'est une perte sur une liste **stable** au sens d'`audit_diff_profils` :
    elle se déclare par `allow_declared_losses`, jamais en désarmant le
    contrôle (AGENTS.md §3c).
    """
    replis_repris = {
        _repli_texte_key(t)
        for t in textes or []
        if isinstance(t, dict) and t.get("dossier_id")
    }
    if not replis_repris:
        return list(textes or [])
    return [
        t
        for t in textes or []
        if not (
            isinstance(t, dict)
            and not t.get("dossier_id")
            and _repli_texte_key(t) in replis_repris
        )
    ]


def _pivot_amendement_key(a: dict[str, Any]) -> Key:
    # Depuis #431 le pivot ne porte plus que le mapping : `amendement_id`
    # (`an:<uid>`) EST la clé, et elle est la même donnée que l'`uid` du brut,
    # préfixée. Les replis suivants ne servent qu'aux entrées écrites avant la
    # normalisation, que la fusion additive fait cohabiter avec les nouvelles
    # le temps d'une régénération.
    #
    # Pour une entrée non résolue (`amendement_id` à null), la clé est lue dans
    # `amendement_non_resolu` : sans cela, toutes les entrées non résolues d'un
    # profil se réduiraient à une seule à la fusion.
    amendement_id = a.get("amendement_id")
    if amendement_id:
        return amendement_id
    non_resolu = a.get("amendement_non_resolu")
    if isinstance(non_resolu, dict):
        a = non_resolu
    return a.get("uid") or a.get("source_url") or (a.get("numero"), a.get("texte_vise"), a.get("date"))


def _pivot_intervention_key(i: dict[str, Any]) -> Key:
    """Identité d'une intervention pivot (#540).

    **Une URL de source n'est pas un identifiant.** La clé d'origine —
    `source_url or (date, sujet, texte[:50])` — court-circuitait sur le `or` :
    le repli discriminant n'était jamais atteint dès que `source_url` était
    renseignée. Elle a été écrite pour une source qui publiait un permalien par
    intervention (l'ancre `#inter_<hash>` de NosDéputés) ; Syceron publie l'URL
    de **l'archive de la législature**, identique pour toutes les interventions
    de cette législature. `merge_lists_by_key` étant purement additif, il n'a
    ajouté que les clés inédites : 3 351 entrées collectées pour gabriel-attal
    se réduisaient à 17 publiées, et 7 767 collectées à 891 sur tout le corpus.
    C'est le mode de défaillance que `_pivot_vote_key` décrit déjà pour les
    votes non résolus (#432), à ceci près que la clé collante n'est pas `None`
    mais une URL — donc qu'elle *ressemble* à un identifiant.

    `intervention_id` (propagé verbatim depuis le brut par
    `normalize_profil._normalize_intervention`) est **la même identité que
    celle de la fusion brute** `_intervention_key`, qui repose sur `id` et n'a
    jamais souffert du défaut. Les deux étages disent donc la même chose de ce
    qu'est une intervention : c'est la seule forme qui garantisse qu'une entrée
    collectée arrive publiée, une fois et une seule.

    **Alternative écartée : la clé composite `(source_url, date, sujet,
    texte[:80])`** proposée par #540. Elle rend 3 127 entrées pour
    gabriel-attal, pas 3 351 — elle fusionne 224 prises de parole réelles.
    Mesuré : « Même avis, pour les mêmes raisons. » est prononcé 13 fois dans
    la même séance du 08/11/2022, sur 13 amendements successifs. Ce ne sont pas
    des doublons d'archive, ce sont 13 interventions distinctes ; les absorber
    serait une perte silencieuse, exactement celle qu'on corrige. Une clé qui
    dépend du texte est en outre à la merci d'une correction typographique du
    compte rendu — le même paragraphe reviendrait alors comme une entrée neuve.

    Les replis restent pour les entrées écrites avant #540, que la fusion
    additive fait cohabiter avec les nouvelles : `source_url` d'abord (un
    permalien par entrée pour les interventions héritées de NosDéputés), puis
    le contenu. Voir `clean_stale_interventions` pour leur reprise.
    """
    intervention_id = i.get("intervention_id")
    if intervention_id not in (None, ""):
        return ("intervention_id", intervention_id)
    source_url = i.get("source_url")
    if source_url:
        return ("source_url", source_url)
    return ("contenu", i.get("date"), i.get("sujet"), (i.get("texte") or "")[:50])


def clean_stale_interventions(
    interventions: Optional[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Reprise des entrées écrites avant #540, sur le patron de
    `clean_stale_textes_portes`.

    Les 891 interventions publiées avant le correctif ne portent pas
    d'`intervention_id` : leur clé est leur `source_url`. Les mêmes
    interventions, renormalisées, en portent un. Sans reprise, la fusion
    additive publierait **les deux** — l'ancienne entrée sous sa clé d'URL, la
    neuve sous sa clé d'identifiant — et le corpus se dédoublerait au lieu de
    se compléter.

    Règle appliquée : une entrée **sans** `intervention_id` est écartée quand
    au moins une entrée **avec** `intervention_id` porte la même `source_url`.
    Elle est alors, par construction, l'une de ces entrées-là — soit la même
    intervention renormalisée (permalien NosDéputés, URL de question : une
    entrée par URL), soit l'unique rescapée de l'effondrement Syceron (URL
    d'archive : la première entrée collectée de cette archive, que la liste
    neuve contient aussi).

    Elle ne peut donc rien perdre : sans entrée identifiée sur cette
    `source_url` — collecte en échec, législature non recollectée, archive
    indisponible — rien n'est écarté et l'ancienne entrée reste publiée. Une
    entrée sans `source_url` n'est jamais écartée non plus.
    """
    urls_reprises = {
        i.get("source_url")
        for i in interventions or []
        if isinstance(i, dict)
        and i.get("intervention_id") not in (None, "")
        and i.get("source_url")
    }
    if not urls_reprises:
        return list(interventions or [])
    return [
        i
        for i in interventions or []
        if not (
            isinstance(i, dict)
            and i.get("intervention_id") in (None, "")
            and i.get("source_url") in urls_reprises
        )
    ]


def _merge_pivot_sources(old_sources: Optional[list[dict[str, Any]]], new_sources: Optional[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Fusionne les blocs `sources[]` par `type` : contrairement aux autres
    listes, on garde ici l'entrée dont la synchro est la plus récente (simple
    métadonnée de fraîcheur, pas une donnée métier à préserver telle quelle)."""
    by_type: dict[Any, dict[str, Any]] = {}
    order: list[Any] = []
    for item in (old_sources or []) + (new_sources or []):
        if not isinstance(item, dict):
            continue
        t = item.get("type")
        if t not in by_type:
            order.append(t)
            by_type[t] = item
        else:
            current = by_type[t]
            if (item.get("synchro_le") or "") > (current.get("synchro_le") or ""):
                by_type[t] = item
    return [by_type[t] for t in order]


# ---------------------------------------------------------------------------
# `meta.provenance_champs` : quelle source a rempli quel champ, et quand (#603)
# ---------------------------------------------------------------------------
#
# AGENTS.md §2.2 demande qu'un fait publié remonte à sa source primaire. Sur les
# listes, c'est acquis : une entrée porte son `source_url`, et la fusion est
# additive — personne n'écrase personne. Sur `identite`, non : depuis #601 le
# bloc est composé CHAMP PAR CHAMP à partir de deux écrivains, et rien dans le
# fichier publié ne dit lequel a rempli quoi.
#
# Portée de ce lot, et c'est une décision (voir `BLOCS_PROVENANCE_CHAMPS`) :
# **`identite` seule**. La provenance par champ ne répond à une question que là
# où plusieurs sources écrivent le même champ ; sur un membre de roster alimenté
# par l'AN seule, il n'y a rien à départager.
#
# Où vit le bloc : **à côté d'`identite`, pas dedans.** Trois raisons, dans
# l'ordre où elles pèsent :
#
#   1. `identite` est un dictionnaire champ → VALEUR, et l'interface l'itère
#      comme tel. Y ajouter des clés qui ne sont pas des valeurs publiables
#      obligerait chaque lecteur à connaître la liste des clés à sauter.
#   2. `fusionner_identite` compose le bloc champ par champ : une clé de
#      provenance rangée dedans passerait par la règle des valeurs, et une
#      provenance obsolète survivrait à la valeur qu'elle décrit — la règle « une
#      absence n'écrase pas » (#601) est faite pour des valeurs, pas pour des
#      métadonnées qui doivent au contraire suivre.
#   3. `meta` est déjà l'endroit où vit la traçabilité de ce run
#      (`synchro_sources`, `collecte_ecartee`, `warnings`), et depuis #600 c'est
#      le seul bloc dont chaque clé est OBLIGÉE de nommer sa règle de fusion.
#      Une clé posée ailleurs n'aurait rien à déclarer.
#
# Ce que le bloc n'est PAS : `couverture` (#539) dit *pourquoi cette liste est
# vide*, à la maille de la liste métier ; celui-ci dit *d'où vient cette valeur*,
# à la maille du champ. Les deux coexistent et ne se remplacent pas.


def source_ecrivain(profil: Any) -> tuple[Optional[str], Optional[str]]:
    """La source que ce profil déclare comme la sienne, `(None, None)` sinon.

    **Une seule lecture, et elle est stricte : `sources[]` doit ne nommer qu'un
    seul `type`.** Un profil frais, tel qu'un normaliseur le rend, en nomme un
    seul — `assemblee_nationale` pour `normalize_profil` (y compris quand il
    ajoute une seconde entrée pour la source des votes, du même type),
    `europarl` pour `normalize_europarl`. Un profil déjà fusionné en nomme
    plusieurs : `_merge_pivot_sources` unit par type, et 475 des 481 profils
    publiés portent encore une entrée `nosdeputes` que #529 n'a pas retirée.

    C'est la strictesse qui fait la valeur du champ. `sources[0]` aurait
    « marché » — et aurait attribué 2 597 des 2 612 champs d'identité des 481
    profils publiés à `nosdeputes`, source retirée du pipeline depuis #529, sur
    la seule foi de l'ordre d'une liste. Une provenance fausse ne se distingue
    pas d'une provenance vraie : elle se lit comme une preuve. Mesure faite le
    30/08/2026 en rejouant la fusion sur le corpus committé.

    Rien n'est deviné : sources vides, illisibles, sans `type`, ou de plusieurs
    types → l'inconnu, qui se publie tel quel (§2.5).
    """
    sources = profil.get("sources") if isinstance(profil, dict) else None
    if not isinstance(sources, list) or not sources:
        return None, None
    entrees = [s for s in sources if isinstance(s, dict)]
    if len(entrees) != len(sources):
        return None, None
    types = {s.get("type") for s in entrees}
    if len(types) != 1:
        return None, None
    type_source = types.pop()
    if not isinstance(type_source, str) or not type_source:
        return None, None
    synchros = [
        s.get("synchro_le") for s in entrees
        if s.get("type") == type_source
        and isinstance(s.get("synchro_le"), str) and s.get("synchro_le")
    ]
    if not synchros:
        return type_source, None
    return type_source, max(synchros, key=_instant_synchro)


def _entree_provenance(source: Optional[str], synchro_le: Optional[str]) -> dict[str, Any]:
    return {"source": source, "synchro_le": synchro_le if source else None}


def deriver_provenance_champs(
    bloc_fusionne: Any,
    origines: dict[str, str],
    provenance_ancienne: Any,
    profil_neuf: Any,
    nom_bloc: str = "identite",
) -> dict[str, Any]:
    """Nomme la source de chaque champ publié de `bloc_fusionne` (#603).

    Le verdict vient de `_composer_identite`, qui a réellement pris la décision —
    il n'est pas rejoué ici. Deux cas, et un seul repli :

    - champ retenu du **nouvel** écrivain → sa source déclarée
      (`source_ecrivain`), avec l'horodatage de cette synchro ;
    - champ retenu de l'**ancien** profil → la provenance que l'ancien profil
      consignait déjà pour ce champ. C'est ce qui fait tenir la chaîne : la
      valeur et son origine traversent les runs ensemble.
    - à défaut — un profil publié avant ce lot, qui ne consigne rien — la
      provenance est **inconnue**, et se publie `{"source": null}`. Elle ne se
      devine pas depuis `sources[]` de l'ancien profil : celui-ci est un
      surensemble des sources des deux côtés (`_merge_pivot_sources`), et lui
      attribuer un champ serait inventer une preuve. §2.5, appliqué à la
      traçabilité elle-même.

    Un champ nul n'a pas d'entrée : il n'y a pas de valeur dont nommer l'origine.
    """
    if not isinstance(bloc_fusionne, dict):
        return {}
    ancienne = {}
    if isinstance(provenance_ancienne, dict):
        candidat = provenance_ancienne.get(nom_bloc)
        if isinstance(candidat, dict):
            ancienne = candidat

    source, synchro = source_ecrivain(profil_neuf)
    entrees: dict[str, Any] = {}
    for champ, valeur in bloc_fusionne.items():
        if valeur in (None, "", [], {}):
            continue
        if origines.get(champ) == ORIGINE_NOUVELLE:
            entrees[champ] = _entree_provenance(source, synchro)
            continue
        heritee = ancienne.get(champ)
        if isinstance(heritee, dict) and "source" in heritee:
            entrees[champ] = _entree_provenance(
                heritee.get("source"), heritee.get("synchro_le")
            )
        else:
            entrees[champ] = _entree_provenance(None, None)
    return {nom_bloc: entrees} if entrees else {}


def _poser_provenance_champs(profil: dict[str, Any], provenance: dict[str, Any]) -> None:
    """Écrit — ou retire — `meta.provenance_champs` sur un profil pivot.

    Retirer plutôt que publier un bloc vide : un `{}` dirait « aucun champ n'a de
    provenance » là où la vérité est « ce profil n'a pas d'identité publiée ».
    """
    meta = profil.get("meta")
    if not isinstance(meta, dict):
        return
    if provenance:
        meta["provenance_champs"] = provenance
    else:
        meta.pop("provenance_champs", None)


# ---------------------------------------------------------------------------
# `couverture` : fusionnée PAR LISTE MÉTIER (#602)
# ---------------------------------------------------------------------------
#
# `couverture` était pris en BLOC — `_prefer_non_empty(new, old)` — sur un modèle
# que #539 a organisé **par liste métier**. Un écrivain qui ne sait rien dire
# d'`interventions` mais qui publie une couverture de `votes` remplaçait les cinq
# listes, et les états établis par l'autre écrivain disparaissaient sans trace.
# C'est le défaut de #484, sur le bloc dont la raison d'être est précisément de
# ne pas publier un silence comme un fait.
#
# La maille de #539 fait autorité et n'est pas réinventée : la fusion se fait
# **par liste**, et l'unité échangée est le **jeu d'entrées entier** de cette
# liste, jamais une entrée recomposée. C'est ce qui fait que la `cause` et la
# `portee` suivent l'état auquel elles se rapportent : la forme générale de #539
# est à deux entrées (`couvert` sur la fenêtre couverte, `hors_couverture`
# avant), et prendre l'état d'un écrivain avec la portée de l'autre publierait
# une frontière que personne n'a constatée.
#
# Ce que ce lot NE change PAS : `couverture` reste **remplacée**, jamais fusionnée
# additivement (#539, décision 4). Une entrée de couverture décrit le RUN, pas la
# personne ; l'unir aux anciennes ferait survivre indéfiniment un `couvert` à
# côté d'un `non_collecte` d'aujourd'hui — la panne masquée par son propre
# historique. Le remplacement descend d'un cran, du bloc à la liste.

#: Ce que le jeu d'entrées d'une liste dit de **ce que son écrivain a demandé à
#: la source**, et non de ce qu'il y a trouvé. C'est la règle qui gouverne tout
#: `couverture_profil` — « la condition porte sur la santé de la source, jamais
#: sur l'absence de résultat » (#539) — relue au moment de la fusion.
#:
#: L'ordre entre les deux causes de `non_collecte` est celui de #562, déjà rendu :
#: elles disent toutes deux que la source a été interrogée, et se valent donc ici.
#: Ce qui les sépare de `par_decision`, c'est qu'on n'a rien demandé du tout.
_RANGS_INTERROGATION: dict[tuple[Any, Any], int] = {
    (ETAT_COUVERT, None): 3,          # la source a répondu
    (ETAT_FAIT_ETABLI, None): 3,      # idem, et le référentiel étaye un fait négatif
    (ETAT_HORS_COUVERTURE, None): 2,  # la source ne couvre pas : frontière connue
    (ETAT_NON_COLLECTE, CAUSE_DEFAUT_COLLECTE): 1,  # demandé, notre code a échoué
    (ETAT_NON_COLLECTE, CAUSE_PANNE): 1,            # demandé, la source n'a pas répondu
}


def _rang_interrogation(entrees: Any) -> int:
    """Le rang le plus haut atteint par les entrées d'une liste.

    Un `non_collecte`/`par_decision` — « nous n'avons rien demandé » — vaut 0 :
    cet écrivain ne sait rien de la liste, donc il ne peut rien y écraser. Une
    entrée illisible vaut 0 aussi : elle n'atteste d'aucune interrogation.
    """
    rang = 0
    for entree in entrees if isinstance(entrees, list) else ():
        if not isinstance(entree, dict):
            continue
        etat = entree.get("etat")
        cle = (etat, entree.get("cause") if etat == ETAT_NON_COLLECTE else None)
        rang = max(rang, _RANGS_INTERROGATION.get(cle, 0))
    return rang


#: Ce que porte une entrée de couverture qui ne nomme pas sa source : la
#: couverture de l'Assemblée nationale. C'est le cas de 100 % des entrées
#: écrites avant #683, et l'absence de clé le dit sans backfill.
_SOURCE_IMPLICITE = "assemblee_nationale"


def _sources_couvertes(entrees: Any) -> frozenset[str]:
    """Les institutions dont ce jeu d'entrées décrit la couverture (#683).

    ## Pourquoi une règle de plus, et pourquoi celle-là

    Deux écrivains d'un même run constatent le même jour, au même rang : la
    règle 4 refusait alors de trancher et gardait la couverture déjà publiée.
    C'est le bon geste quand les deux se contredisent — mais pas quand l'un
    **couvre une source que l'autre n'a pas interrogée**.

    Mesuré sur le run `34377413730` : `extract-ue-officiel` écrit une couverture
    sans volet européen, `merge-and-pivot` en écrit une avec. Même jour, même
    rang, contenus différents. Résultat : **3 profils sur 6** — Glucksmann,
    Philippot, Massard — publiaient leurs votes du Parlement européen **sans la
    borne de fraîcheur** qui les date, et le profil le déclarait sous
    « couverture divergente non tranchée ». Le garde-fou de #602 faisait
    exactement son travail ; c'est la règle qui manquait un cas.

    Un sur-ensemble strict n'est pas une contradiction : il dit tout ce que
    l'autre dit, plus une source de plus. Le préférer ne choisit pas entre deux
    vérités, il retient la plus complète — et l'égalité, comme les deux
    ensembles simplement différents, restent non tranchables.
    """
    sources: set[str] = set()
    for entree in entrees if isinstance(entrees, list) else ():
        if not isinstance(entree, dict):
            continue
        source = entree.get("source")
        sources.add(source if isinstance(source, str) and source else _SOURCE_IMPLICITE)
    return frozenset(sources)


def _dernier_constat(entrees: Any) -> str:
    """La date de constat la plus récente du jeu d'entrées, `""` si aucune.

    Les dates sont ISO — `schema_pivot._valider_entree_couverture` le fait
    respecter —, donc l'ordre lexicographique est l'ordre chronologique. Une
    valeur illisible passe derrière tout ce qui se lit, comme dans
    `_instant_synchro`.
    """
    dates = [
        e.get("constate_le")
        for e in (entrees if isinstance(entrees, list) else ())
        if isinstance(e, dict) and isinstance(e.get("constate_le"), str)
    ]
    return max(dates) if dates else ""


def _entrees_presentes(bloc: Any, liste: str) -> Optional[list[Any]]:
    """Le jeu d'entrées de `liste` chez cet écrivain, ou `None` s'il n'en a pas.

    Une liste absente et une liste vide disent la même chose — cet écrivain n'a
    rien à dire de cette liste — et `schema_pivot` refuse déjà une liste vide.
    Les confondre ici est ce qui empêche un `[]` d'écraser un état établi.
    """
    if not isinstance(bloc, dict):
        return None
    entrees = bloc.get(liste)
    if not isinstance(entrees, list) or not entrees:
        return None
    return entrees


def fusionner_couverture(
    old_bloc: Any, new_bloc: Any
) -> tuple[Optional[dict[str, Any]], list[str]]:
    """`couverture` composée **liste par liste** (#602).

    Renvoie `(bloc, listes_non_tranchees)`. La seconde valeur nomme les listes
    sur lesquelles aucune règle n'a départagé les deux écrivains : l'appelant en
    fait une déclaration, parce qu'un cas non tranchable qui se choisit en
    silence est exactement ce que ce lot retire.

    Quatre règles, dans cet ordre, et chacune porte sur la donnée — jamais sur
    l'ordre des jobs de `generate-data.yml`, qui est un détail de la CI :

    1. **Une liste dont un écrivain ne dit rien garde ce que l'autre en dit.**
       C'est la règle de #465 et de #484, descendue à la maille de #539.
    2. **Le constat le plus récent l'emporte.** C'est la garde de #539 décision
       4 : une couverture décrit le run, et un `couvert` d'hier ne masque pas un
       `non_collecte` d'aujourd'hui. Elle passe donc AVANT le rang, sans quoi une
       collecte réussie hier enterrerait la panne de ce matin.
    3. **À date de constat égale, l'écrivain qui a interrogé la source
       l'emporte** sur celui qui ne l'a pas fait (`_rang_interrogation`). Dans un
       même run les deux écrivains constatent le même jour : c'est cette règle-là
       qui travaille. Le job roster porte `--skip-interventions` en dur (#357) et
       publie donc `non_collecte`/`par_decision` sur une liste que le job AN a
       réellement collectée ; sans ce rang, l'ordre `--dirs an ue roster`
       décidait laquelle des deux vérités était publiée.
    4. **À date et rang égaux, contenus différents : non tranchable.** La
       couverture DÉJÀ PUBLIÉE est conservée — ne rien changer est le seul geste
       qui ne prétende pas avoir tranché — et la liste est déclarée à l'appelant.
    """
    if not isinstance(new_bloc, dict) or not new_bloc:
        return (old_bloc if isinstance(old_bloc, dict) and old_bloc else None), []
    if not isinstance(old_bloc, dict) or not old_bloc:
        return dict(new_bloc), []

    # L'ordre de #539 d'abord, puis toute clé hors nomenclature : la fusion ne
    # doit pas être ce qui fait disparaître une liste inconnue, sans quoi
    # `valider_couverture` cesserait de la signaler.
    cles: list[str] = list(LISTES_COUVERTES)
    cles += [c for c in list(new_bloc) + list(old_bloc) if c not in LISTES_COUVERTES]

    vues: set[str] = set()
    fusionne: dict[str, Any] = {}
    non_tranchees: list[str] = []
    for liste in cles:
        if liste in vues:
            continue
        vues.add(liste)
        ancien = _entrees_presentes(old_bloc, liste)
        neuf = _entrees_presentes(new_bloc, liste)
        if neuf is None and ancien is None:
            continue
        if neuf is None:
            fusionne[liste] = ancien
            continue
        if ancien is None or ancien == neuf:
            fusionne[liste] = neuf
            continue

        constat_neuf, constat_ancien = _dernier_constat(neuf), _dernier_constat(ancien)
        if constat_neuf != constat_ancien:
            fusionne[liste] = neuf if constat_neuf > constat_ancien else ancien
            continue

        rang_neuf, rang_ancien = _rang_interrogation(neuf), _rang_interrogation(ancien)
        if rang_neuf != rang_ancien:
            fusionne[liste] = neuf if rang_neuf > rang_ancien else ancien
            continue

        # 4. À rang égal, l'écrivain qui couvre STRICTEMENT PLUS DE SOURCES
        #    l'emporte (#683). Ce n'est pas trancher entre deux affirmations
        #    contradictoires — c'est préférer celle qui en dit strictement plus.
        sources_neuf, sources_ancien = _sources_couvertes(neuf), _sources_couvertes(ancien)
        if sources_neuf > sources_ancien or sources_neuf < sources_ancien:
            fusionne[liste] = neuf if sources_neuf > sources_ancien else ancien
            continue

        fusionne[liste] = ancien
        non_tranchees.append(liste)
    return (fusionne or None), non_tranchees


def merge_pivot_profile(old: Optional[dict[str, Any]], new: dict[str, Any]) -> dict[str, Any]:
    """Équivalent de `merge_raw_profile` pour le format pivot v1."""
    if not old:
        # Même recalcul que sur le chemin fusionné : `licence_donnees` dérive de
        # `sources[]`, et un premier pivot doit publier la même chaîne qu'un
        # pivot régénéré au même contenu (#530).
        appliquer_licence_donnees(new)
        # #642 : même raison encore — un premier pivot doit publier le même
        # bloc `avertissements` qu'un pivot régénéré au même contenu.
        deriver_avertissements(new.get("meta"))
        # #1094 : même raison — `question_ref` est dérivé.
        if new.get("interventions"):
            new["interventions"] = rattacher_parole_aux_questions(new["interventions"])
        # #603 : même raison. Un profil écrit pour la première fois a une
        # provenance — celle de son unique écrivain — et la lui refuser
        # publierait deux profils de même contenu dont un seul est traçable.
        # #641 : même filtre de publication que sur le chemin fusionné. Sans
        # lui, un profil écrit pour la première fois et un profil régénéré au
        # même contenu ne publieraient pas la même `profession`.
        identite_neuve = filtrer_identite_publiee(new.get("identite"))
        _poser_provenance_champs(new, deriver_provenance_champs(
            identite_neuve,
            {c: ORIGINE_NOUVELLE for c in identite_neuve} if isinstance(identite_neuve, dict) else {},
            None,
            new,
        ))
        return new

    merged = dict(new)

    # `meta` composé clé par clé (#600) — même règle qu'à l'étage brut, et pour
    # la même raison : sans elle, `merged["meta"]` est celui du dernier écrivain,
    # et les avertissements de l'autre disparaissent sans trace.
    meta_fusionne = fusionner_meta(old.get("meta"), new.get("meta"))
    if meta_fusionne is not None:
        merged["meta"] = meta_fusionne

    merged["parti"] = _prefer_non_empty(new.get("parti"), old.get("parti"))
    merged["groupe"] = _prefer_non_empty(new.get("groupe"), old.get("groupe"))
    merged["chambre"] = _prefer_non_empty(new.get("chambre"), old.get("chambre"))
    # `_composer_identite` plutôt que `fusionner_identite` : la provenance par
    # champ (#603) est déduite du verdict que la composition VIENT de rendre, pas
    # d'un second calcul qui rejouerait les mêmes règles à côté.
    merged["identite"], origines_identite = _composer_identite(
        old.get("identite"), new.get("identite")
    )
    # #641 : le filtre de publication mord sur le bloc COMPOSÉ, pas sur l'un
    # des deux côtés. La composition venait de restaurer les cinq libellés que
    # la collecte corrigée avait ramenés à `None` — voir
    # `FILTRES_PUBLICATION_IDENTITE`. Posé avant la provenance : un champ nul
    # n'a pas d'origine à nommer.
    filtrer_identite_publiee(merged["identite"])

    # --- identifiants : fusionnés CLÉ PAR CLÉ (#539) -------------------------
    #
    # `_prefer_non_empty` sur le bloc entier ferait perdre un identifiant qu'un
    # run précédent avait résolu et que celui-ci n'a pas : un profil AN + PE
    # passe par deux normaliseurs, et une passe `--source an` ne rend pas
    # l'`europarl`. La règle des scalaires, appliquée à chaque clé — la nouvelle
    # valeur si elle est renseignée, l'ancienne sinon, jamais une régression
    # vers `null` (AGENTS.md §2 règle 5).
    identifiants = dict(old.get("identifiants") or {})
    for cle, valeur in (new.get("identifiants") or {}).items():
        identifiants[cle] = _prefer_non_empty(valeur, identifiants.get(cle))
    if identifiants:
        merged["identifiants"] = identifiants

    # `identite.uri_hatvp` et `identifiants.hatvp` sont deux noms d'une même
    # valeur, et depuis #601 ce sont deux compositions distinctes : sans cet
    # accord, elles peuvent retenir chacune la sienne, et `validate_profil`
    # refuse la divergence. Il est posé ICI, après les deux, parce qu'il ne
    # décrit ni l'une ni l'autre — il décrit leur invariant.
    _accorder_hatvp(merged)

    # --- provenance par champ : DÉRIVÉE, jamais fusionnée (#603) -------------
    #
    # Même patron que `chambres` (#493) et `licence_donnees` (#530) : un champ
    # dérivé se recalcule après la fusion de ce dont il dérive, il ne se fusionne
    # pas. Fusionner `provenance_champs` clé par clé publierait la provenance
    # d'un écrivain à côté de la valeur d'un autre — soit exactement l'inverse de
    # ce que ce bloc existe pour dire.
    #
    # Posée ICI, après `_accorder_hatvp` : cet accord peut encore renseigner
    # `identite.uri_hatvp` depuis `identifiants`, et un champ publié sans entrée
    # de provenance est refusé par `valider_provenance_champs`.
    _poser_provenance_champs(merged, deriver_provenance_champs(
        merged.get("identite"),
        origines_identite,
        (old.get("meta") or {}).get("provenance_champs"),
        new,
    ))

    # --- couverture : REMPLACÉE liste par liste, jamais en bloc (#539, #602) --
    #
    # Le remplacement reste la règle — une couverture décrit le run, pas la
    # personne (#539 décision 4) — mais il descend du bloc à la **liste métier**,
    # la maille à laquelle #539 publie. Prendre le bloc entier faisait
    # disparaître les cinq listes d'un écrivain dès qu'un autre en décrivait une.
    # Voir `fusionner_couverture` pour les quatre règles et leur ordre.
    couverture, couverture_non_tranchee = fusionner_couverture(
        old.get("couverture"), new.get("couverture")
    )
    if couverture is not None:
        merged["couverture"] = couverture
    else:
        merged.pop("couverture", None)

    merged["sources"] = _merge_pivot_sources(old.get("sources"), new.get("sources"))
    # #718 — le report vaut aux DEUX étages, et pour la même raison qu'au brut :
    # `_pivot_mandat_key` ne contient pas `categorie_source`, donc l'entrée
    # ancienne gagne et n'acquiert jamais l'estampille. L'oublier ici laisserait
    # le champ arriver dans le profil brut sans jamais atteindre le pivot, qui
    # est la seule couche que `web/` lit — un correctif vrai et sans effet.
    merged["mandats"] = backfill_mandat_chambre(
        backfill_mandat_organe_source(
            backfill_mandat_categorie_source(
                merge_lists_by_key(old.get("mandats"), new.get("mandats"), _pivot_mandat_key),
                new.get("mandats"),
                _pivot_mandat_key,
            ),
            new.get("mandats"),
            _pivot_mandat_key,
        ),
        new.get("mandats"),
        _pivot_mandat_key,
    )

    # --- chambres / chambre : RECALCULÉS, jamais fusionnés (#493) -----------
    #
    # `merge_lists_by_key` est additif : `merged["mandats"]` est un **surensemble**
    # des mandats de `new` comme de ceux de `old`. Un `chambres` fusionné —
    # `_prefer_non_empty(new, old)` ou une union de listes — décrirait donc un
    # ensemble de mandats qui n'existe dans aucun des deux profils. C'est le
    # symétrique du piège que #492 a rencontré sur `backfill_mandat_chambre` :
    # un champ dérivé ne se fusionne pas, il se recalcule après la fusion de ce
    # dont il dérive.
    #
    # Le recalcul est monotone : les mandats ne peuvent qu'augmenter, donc
    # `chambres` ne peut que gagner des entrées. Le repli reste `merged["chambre"]`
    # — la valeur qu'on aurait publiée sans #493 : c'est ce qui garantit qu'aucun
    # scalaire publié ne régresse vers `null` (un `chambre` renseigné → `null` est
    # une perte bloquante pour `audit_diff_profils`).
    derivation = appliquer_chambres(merged)
    # Tri par identifiant, plus par date : depuis #432 la date du scrutin n'est
    # plus dans le profil. L'ordre n'a donc plus de sens chronologique, il n'a
    # qu'à être STABLE d'un run à l'autre pour que git ne voie que les vraies
    # différences. Les consommateurs qui ont besoin de l'ordre chronologique
    # joignent l'index et trient eux-mêmes (c'est déjà ce que fait l'UI).
    merged["votes"] = sorted(
        merge_lists_by_key(old.get("votes"), new.get("votes"), _pivot_vote_key),
        key=lambda v: str(v.get("scrutin_id") or ""),
    )
    # `clean_stale_textes_portes` : reprise des entrées d'avant #639, qui n'ont
    # pas de `dossier_id` et sont republiées EN DOUBLE à côté de leur
    # renormalisation identifiée — la clé de fusion a changé de branche sous
    # elles (#668). Voir sa docstring pour la preuve de non-perte.
    merged["textes_portes"] = sorted(
        (
            # #743 — PAS de report du sort ici, et c'est mesuré, pas supposé :
            # `merge_dossier_records` fait gagner l'entrée NEUVE en cas de
            # collision de clé, contrairement à `merge_lists_by_key` qui régit la
            # fusion brute. Le sort arrive donc de lui-même à cet étage. Un report
            # y serait du code mort justifié par un raisonnement faux — celui de
            # #729/#730 appliqué à une liste qui ne se fusionne pas pareil.
            t for t in clean_stale_textes_portes(
                merge_dossier_records(
                    old.get("textes_portes"), new.get("textes_portes"), _pivot_texte_key
                )
            )
            if t.get("role")  # écarte la liste globale héritée de NosDéputés (role toujours
                              # null) — voir candidate_profile.fetch_textes_portes_officiels
        ),
        key=lambda t: (t.get("date_max") or "", t.get("titre") or ""),
        reverse=True,
    )
    # `clean_stale_interventions` : reprise des entrées d'avant #540, qui n'ont
    # pas d'`intervention_id` et seraient republiées EN DOUBLE à côté de leur
    # renormalisation identifiée. Voir sa docstring pour la preuve de non-perte.
    merged["interventions"] = normaliser_dates_interventions(clean_stale_interventions(
        backfill_sujet_europeen(
            backfill_sujet_question(backfill_sujet_seance(
                reporter_id_syceron(promouvoir_forme_complete(
                    merge_lists_by_key(old.get("interventions"), new.get("interventions"),
                                       _pivot_intervention_key),
                    new.get("interventions"),
                    _pivot_intervention_key,
                ), new.get("interventions"), _pivot_intervention_key),
                new.get("interventions"),
                _pivot_intervention_key,
                preuve=_entree_syceron_publiee,
            ), new.get("interventions"), _pivot_intervention_key),
            new.get("interventions"),
            _pivot_intervention_key,
        )
    ))
    # merge_dossier_records (nouvelle valeur gagne en cas de collision, aucune perte
    # sinon) : un echec/vide transitoire de l'open data amendements (voir
    # candidate_profile.fetch_amendements_officiels) ne doit pas effacer des
    # amendements deja collectes lors d'une regeneration precedente.
    merged["amendements"] = merge_dossier_records(old.get("amendements"), new.get("amendements"), _pivot_amendement_key)

    # #710 — `tags_thematiques` est DÉRIVÉ des interventions fusionnées, comme
    # `chambres` l'est des mandats fusionnés : on le recalcule ici, on ne
    # l'unit plus. L'union ancienne+neuve rendait le champ MONOTONE CROISSANT —
    # un tag publié une fois y restait pour toujours, et aucune correction de
    # `theme_officiel` ne pouvait l'en déloger, pas même celle qui vient d'être
    # reportée par `backfill_sujet_seance` deux lignes plus haut.
    #
    # Le recalcul ne perd rien par lui-même : mesuré le 02/09/2026, les 39 782
    # couples (profil, tag) publiés sont exactement ceux que la fabrique rend
    # depuis les `interventions[]` des 481 profils publiés, 0 profil d'écart. Et
    # la fusion des interventions est additive : un run qui n'en collecte
    # aucune (`--skip-interventions`) laisse `merged["interventions"]` égal à
    # l'ancien, donc les tags aussi.
    merged["tags_thematiques"] = deriver_tags_thematiques(merged.get("interventions"))
    # #1094 — `question_ref` est dérivé des interventions fusionnées, même règle.
    if merged.get("interventions"):
        merged["interventions"] = rattacher_parole_aux_questions(merged["interventions"])

    if isinstance(merged.get("meta"), dict):
        # Politique de fusion provenance (#189) : un profil déjà enrichi via
        # raw_data/candidats.json (provenance="candidat_declare", source éditoriale
        # de vérité) ne doit JAMAIS être rétrogradé vers provenance="roster_groupe"
        # par une régénération roster-driven (#188) du même slug — même si le
        # nouveau run produit provenance="roster_groupe". Un ancien pivot sans
        # meta.provenance (pré-#189) est traité comme "candidat_declare" par défaut,
        # pour rester rétro-compatible. Les autres champs éditoriaux (ex. `parti`)
        # sont déjà protégés plus haut par `_prefer_non_empty` : un run roster-driven
        # ne les renseigne jamais (valeur None côté generate_roster_candidats.py),
        # donc l'ancienne valeur est conservée automatiquement.
        old_meta = old.get("meta") if isinstance(old.get("meta"), dict) else {}
        if old_meta.get("provenance", "candidat_declare") == "candidat_declare":
            merged["meta"]["provenance"] = "candidat_declare"

    # #493 : la déclaration d'une `chambres` non corroborée doit survivre à la
    # fusion **dans les deux sens**. Le filtre ci-dessous ne sait que retirer un
    # warning devenu faux ; il faut aussi pouvoir en ajouter un devenu vrai.
    # Le cas se produit dès qu'un run recollecte proprement un mandat pendant
    # que la fusion additive en conserve un ancien, non estampillé : le profil
    # neuf ne porte alors aucun warning, le profil fusionné le mérite. Sans ce
    # rattrapage, la seule chose qui empêche `chambres` d'être trompeuse
    # disparaîtrait précisément sur les profils mixtes — ceux de la migration.
    if isinstance(merged.get("meta"), dict) and not derivation.corroboree:
        warnings_merged = merged["meta"].setdefault("warnings", [])
        # Le texte est recalculé sur le profil FUSIONNÉ, jamais repris de
        # l'ancien : ses compteurs porteraient sur un autre ensemble de mandats.
        if not any(w.startswith(WARNING_PREFIX_CHAMBRES_NON_CORROBOREE)
                   for w in warnings_merged if isinstance(w, str)):
            warnings_merged.append(avertissement(
                f"{WARNING_PREFIX_CHAMBRES_NON_CORROBOREE} : "
                f"chambres={derivation.chambres}, dont "
                f"{derivation.chambres_non_corroborees} sans mandat électif "
                "estampillé pour l'étayer, après fusion additive (#493). "
                "Une chambre non corroborée est celle de la collecte : elle dit quel jeu "
                "de données a répondu, pas où la personne a siégé.",
                DESTINATAIRE_INTERNE,
            ))

    # #486 : le warning de #492 est désormais le SEUL à déclarer qu'un
    # `mandat_electif` n'a pas de chambre — celui de #493 a cessé de le
    # redéclarer. Il doit donc survivre à la fusion dans les deux sens, comme
    # celui de #493 juste au-dessus, et pour la même raison : `normalize_profil`
    # le calcule sur les seuls mandats du profil NEUF, quand la fusion additive
    # publie un surensemble des deux côtés.
    #
    # Le trou n'est pas théorique : mesuré sur les 481 profils pivot publiés du
    # 30/08/2026, **1 profil** (`yannick-vaugrenard`) publie un `mandat_electif`
    # à `chambre: null` sans aucun warning pour le dire — son pivot est
    # antérieur à #492, et la fusion a conservé son mandat sans jamais
    # reconstruire l'avertissement qui l'accompagne. Les 27 autres portaient un
    # compte juste, par coïncidence de périmètre et non par construction.
    n_sans_chambre_fusion = sum(
        1 for m in merged.get("mandats") or []
        if isinstance(m, dict) and m.get("categorie") == "mandat_electif"
        and not m.get("chambre")
    )
    texte_mandat_sans_chambre = (
        f"{WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE} : "
        f"{n_sans_chambre_fusion} mandat(s) électif(s) sans chambre déterminée, "
        "publiés à null, après fusion additive (#492). La chambre est estampillée "
        "à la collecte ; un mandat conservé par la fusion et que la source ne rend "
        "plus n'en portera jamais, et elle n'est pas reconstituable a posteriori — "
        "ni depuis `source_url` (jamais renseignée sur un mandat électif AN/Sénat), "
        "ni depuis la chambre du profil."
    ) if n_sans_chambre_fusion else None
    if texte_mandat_sans_chambre is not None:
        texte_mandat_sans_chambre = avertissement(
            texte_mandat_sans_chambre, DESTINATAIRE_INTERNE
        )
    if isinstance(merged.get("meta"), dict) and texte_mandat_sans_chambre:
        warnings_merged = merged["meta"].setdefault("warnings", [])
        if texte_mandat_sans_chambre not in warnings_merged:
            warnings_merged.append(texte_mandat_sans_chambre)

    # #602 : une couverture que deux écrivains constatent le même jour, au même
    # rang d'interrogation, et différemment, n'est tranchée par aucune règle. Le
    # lot refuse de la choisir en silence sur l'ordre des jobs : il conserve la
    # couverture déjà publiée et le DIT. Le texte est recalculé à chaque fusion,
    # jamais repris de l'ancien profil — il nomme les listes de CE constat.
    if isinstance(merged.get("meta"), dict) and couverture_non_tranchee:
        warnings_merged = merged["meta"].setdefault("warnings", [])
        if not any(w.startswith(WARNING_PREFIX_COUVERTURE_DIVERGENTE)
                   for w in warnings_merged if isinstance(w, str)):
            warnings_merged.append(avertissement(
                f"{WARNING_PREFIX_COUVERTURE_DIVERGENTE} : deux écrivains constatent "
                f"le même jour des couvertures différentes pour "
                f"{', '.join(couverture_non_tranchee)}, sans que l'un ait interrogé "
                "la source plus que l'autre. La couverture déjà publiée est "
                "conservée : aucune règle ne départage ces constats, et l'ordre des "
                "jobs n'en est pas une (#602).",
                DESTINATAIRE_INTERNE,
            ))

    if isinstance(merged.get("meta"), dict) and merged["meta"].get("warnings"):
        filtered = []
        for w in merged["meta"]["warnings"]:
            if w.startswith(WARNING_PREFIX_VOTES_INTROUVABLES) and merged.get("votes"):
                continue
            if w.startswith(WARNING_PREFIX_MANDATS_INTROUVABLES) and merged.get("mandats"):
                continue
            if w.startswith(WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES) and merged.get("amendements"):
                continue
            if _defaut_collecte_dementi_par_les_donnees(merged, w):
                continue
            if _aucun_mandat_fr_dementi(merged, w):
                continue
            if _interventions_syceron_dementies(merged, w):
                continue
            # #493 : le warning de non-corroboration est calculé par
            # `normalize_profil` sur les seuls mandats du profil neuf. La
            # fusion peut avoir ramené des mandats estampillés que le run neuf
            # n'a pas recollectés : la liste est alors corroborée, et le dire
            # encore serait faux.
            if w.startswith(WARNING_PREFIX_CHAMBRES_NON_CORROBOREE) and derivation.corroboree:
                continue
            # #486, symétrique et pour la même raison : le warning de #492 est
            # calculé sur les mandats du profil NEUF. Un warning ramené de
            # l'ancien profil compte sur un autre `mandats[]` — il s'éteint
            # quand la fusion n'a plus aucun mandat électif sans chambre, et il
            # cède la place au texte recalculé ci-dessus quand il en reste. Un
            # compte faux est aussi trompeur qu'un compte absent : le premier
            # fait croire la migration plus avancée qu'elle n'est.
            if (w.startswith(WARNING_PREFIX_CHAMBRE_MANDAT_NON_RESOLUE)
                    and w != texte_mandat_sans_chambre):
                continue
            # #602, même patron : la divergence est un fait sur CETTE fusion. Un
            # warning ramené de l'ancien profil par `unir_warnings` décrirait un
            # constat que la fusion courante ne retrouve pas — donc il s'éteint.
            if (w.startswith(WARNING_PREFIX_COUVERTURE_DIVERGENTE)
                    and not couverture_non_tranchee):
                continue
            filtered.append(w)
        merged["meta"]["warnings"] = filtered

    # `licence_donnees` : RECALCULÉ, jamais fusionné (#530, même patron que
    # `chambres` au #493). `_merge_pivot_sources` fusionne `sources[]` par
    # `type` : le profil fusionné est un **surensemble** des sources des deux
    # côtés, et une entrée `nosdeputes` déjà publiée survit donc à une collecte
    # AN. Reprendre la licence de `new` publierait « Licence Ouverte » sur un
    # profil qui porte encore une source ODbL ; reprendre celle de `old`
    # gèlerait l'inverse. Seul le recalcul post-fusion décrit ce qui est
    # réellement publié, et c'est lui qui fera disparaître la clause ODbL le
    # jour où la dernière source Regards Citoyens quittera le profil.
    appliquer_licence_donnees(merged)

    # #642 : le jumeau typé est réaligné sur les `warnings` FUSIONNÉS, en
    # dernier — après l'union, après le filtre d'extinction, après les trois
    # rattrapages ci-dessus. Un avertissement éteint perd son entrée avec lui ;
    # un avertissement ressuscité de l'ancien profil retrouve la sienne par la
    # table unie par `REGLES_META`.
    deriver_avertissements(merged.get("meta"))

    # #683 — le constat « ParlTrack : aucune donnée » ne survit pas à l'arrivée
    # de données. `unir_warnings` garde un message dont la famille n'est pas
    # représentée par le nouvel écrivain, et un run qui TROUVE n'émet rien dans
    # cette famille : sans cette reprise, la fiche publierait « aucune donnée
    # trouvée » à côté de 1 926 votes.
    retirer_constats_parltrack_perimes(merged)
    aligner_collecte_reduite(merged)  # #1029 voie 3 : la déclaration suit les entrées
    return merged


def _pivot_content_fingerprint(pivot: Optional[dict[str, Any]]) -> Any:
    """Sérialise un profil pivot en ignorant les horodatages de fraîcheur
    (`meta.genere_le`, `sources[].synchro_le`) : deux profils dont seuls ces
    champs diffèrent ont la même empreinte."""
    if not isinstance(pivot, dict):
        return None
    stripped = {k: v for k, v in pivot.items() if k not in ("meta", "sources")}
    meta = pivot.get("meta")
    if isinstance(meta, dict):
        stripped["meta"] = {k: v for k, v in meta.items() if k != "genere_le"}
    sources = pivot.get("sources")
    if isinstance(sources, list):
        stripped["sources"] = [
            {k: v for k, v in s.items() if k != "synchro_le"} if isinstance(s, dict) else s
            for s in sources
        ]
    return json.dumps(stripped, sort_keys=True, ensure_ascii=False)


def load_existing_document(path: Any) -> Optional[dict[str, Any]]:
    """Relit un document JSON déjà écrit sur disque, ou `None` s'il est absent
    ou illisible — pensé comme entrée de `preserve_stable_freshness_timestamps`
    (#343) pour les générateurs qui reconstruisent leur sortie à chaque
    exécution (groupes, gouvernements, partis).

    Un fichier illisible est traité comme absent plutôt que comme une erreur :
    la conséquence est seulement un re-tamponnage des horodatages, jamais une
    perte de donnée — le document régénéré est écrit dans tous les cas."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def preserve_stable_freshness_timestamps(
    old_pivot: Optional[dict[str, Any]], new_pivot: dict[str, Any]
) -> dict[str, Any]:
    """Empêche `meta.genere_le`/`sources[].synchro_le` d'avancer quand le
    document régénéré est identique à `old_pivot` en contenu (#343) : les
    générateurs re-dérivent systématiquement leur sortie depuis les données
    déjà présentes sur disque (aucun appel réseau pour `--pivot-only`) et
    re-tamponnaient ces deux champs à chaque exécution, même quand la donnée
    sous-jacente n'avait pas bougé — trompeur pour un audit de fraîcheur
    (règle de traçabilité, AGENTS.md §2).

    Si le contenu (hors ces deux champs) est identique, restaure les anciens
    horodatages sur `new_pivot` ; sinon le laisse tel quel (changement réel =
    re-tamponnage légitime). Modifie et renvoie `new_pivot`.

    S'applique à tout document portant la forme `meta.genere_le` +
    `sources[].synchro_le` : pivots candidats, mais aussi profils de groupe,
    de gouvernement et de parti, qui partagent exactement cette structure de
    fraîcheur (extension du périmètre initial, #343).

    Les sources sont appariées par `(type, url)` et non par `type` seul : un
    profil de groupe/gouvernement/parti porte une source par membre, donc
    plusieurs dizaines d'entrées partageant le même `type` (mesuré : 63
    sources pour 3 types distincts sur un groupe) — une clé sur le seul
    `type` les écraserait toutes sur la dernière. L'appariement reste
    exact : `url` fait partie de l'empreinte comparée ci-dessus, donc si les
    empreintes sont égales, les couples `(type, url)` le sont aussi.
    """
    if not isinstance(old_pivot, dict):
        return new_pivot
    if _pivot_content_fingerprint(old_pivot) != _pivot_content_fingerprint(new_pivot):
        return new_pivot

    old_meta = old_pivot.get("meta")
    new_meta = new_pivot.get("meta")
    if isinstance(old_meta, dict) and isinstance(new_meta, dict) and "genere_le" in old_meta:
        new_meta["genere_le"] = old_meta["genere_le"]

    old_sources_by_key = {
        (s.get("type"), s.get("url")): s
        for s in (old_pivot.get("sources") or [])
        if isinstance(s, dict)
    }
    for s in new_pivot.get("sources") or []:
        if not isinstance(s, dict):
            continue
        old_s = old_sources_by_key.get((s.get("type"), s.get("url")))
        if old_s and "synchro_le" in old_s:
            s["synchro_le"] = old_s["synchro_le"]

    return new_pivot


# ---------------------------------------------------------------------------
# CLI : fusion de répertoires d'extraction parallèles → merge-and-pivot
# ---------------------------------------------------------------------------

def _tranches_du_socle(profils_dir: Path, slug: str) -> tuple[int, int]:
    """`(dérivées, fichiers)` déclarées par le socle écrit. `(0, 0)` s'il n'y
    en a pas — un profil sans partition, ou illisible."""
    try:
        with open(chemin_socle(profils_dir, slug), encoding="utf-8") as fichier:
            socle = json.load(fichier)
    except (OSError, json.JSONDecodeError):
        return (0, 0)
    manifeste = socle.get(CLE_MANIFESTE) if isinstance(socle, dict) else None
    if not isinstance(manifeste, dict):
        return (0, 0)
    declarees = [t for t in (manifeste.get("tranches") or []) if isinstance(t, dict)]
    derivees = sum(1 for t in declarees if t.get(CLE_TRANCHE_DERIVEE))
    return (derivees, len(declarees) - derivees)


def merge_raw_dirs(source_dirs: list[Path], out_dir: Path) -> int:
    """Fusionne les profils bruts (*.json) de plusieurs répertoires sources
    (jobs d'extraction parallèles AN / Sénat / UE) vers un répertoire cible,
    en appliquant merge_raw_profile de façon additive pour chaque slug.

    Les fichiers de checkpoint (nom commençant par '.') sont ignorés.

    Partition par législature (#580) : chaque source est lue par
    `charger_profil_brut`, qui accepte indifféremment un profil monolithique
    (l'ancienne forme, encore committée) et un socle + ses tranches. La fusion
    travaille donc sur le profil **complet**, exactement comme avant — la
    découpe est une affaire de fichiers, pas de sémantique. La sortie, elle, est
    toujours écrite partitionnée : c'est ici que la migration se fait d'elle-même
    à chaque run.

    Args:
        source_dirs: liste de répertoires sources (certains peuvent être absents).
        out_dir: répertoire de sortie, créé si nécessaire.

    Returns:
        Nombre de profils écrits dans out_dir.
    """
    slug_paths: dict[str, list[Path]] = defaultdict(list)
    for src_dir in source_dirs:
        if not src_dir.is_dir():
            print(f"  [!] Répertoire source absent, ignoré : {src_dir}")
            continue
        for path in sorted(src_dir.glob("*.json")):
            if path.name.startswith("."):
                continue
            slug_paths[path.name].append(path)

    out_dir.mkdir(parents=True, exist_ok=True)
    n_written = 0
    # CE QUE LA FUSION A FAIT AUX TRANCHES, compté pour être IMPRIMÉ (#691).
    #
    # Le run `34329085168` est passé vert en ne basculant rien, et le run de
    # TEST qui le précédait portait déjà le même défaut sans pouvoir le
    # montrer : l'effet vit dans le commit, et un run de test ne committe pas.
    # Le seul endroit observable était l'artifact d'un shard.
    #
    # Un mode de test ne vaut que ce que le log donne à voir. « ✓ N profil(s)
    # écrits » ne disait rien de la bascule ; ces trois nombres, si.
    n_derivees = n_fichiers = n_supprimees = 0
    n_partiels_seuls = 0
    for filename, paths in sorted(slug_paths.items()):
        merged: Optional[dict[str, Any]] = None
        acteur: Optional[str] = None
        # #997 — une contribution RÉDUITE ne peut pas écrire un profil à elle
        # seule. Elle ne porte que ce que son job a collecté (cf.
        # `profil_brut.projeter_contribution`) : si aucune collecte complète ne
        # parle de ce slug — extraction en échec, `continue-on-error` étant la
        # règle —, l'écrire republierait un profil amputé de tout le reste.
        # On laisse alors le profil committé en place, comme pour un slug
        # qu'aucun job n'a touché (#450), et on le DIT.
        complet = False
        for path in paths:
            try:
                profile = charger_profil_brut(path)
            except (json.JSONDecodeError, OSError, PartitionIllisible) as exc:
                print(f"  [!] Lecture impossible de {path}, ignoré : {exc}")
                continue
            partielle = profile.pop(CLE_CONTRIBUTION_PARTIELLE, None)
            complet = complet or partielle is None
            # L'acteur se relit dans le manifeste des profils SOURCES (#691) —
            # ceux que les shards viennent d'écrire —, jamais dans celui de la
            # destination.
            #
            # POURQUOI CETTE PRÉCISION EST TOUT LE CORRECTIF. Le principe était
            # juste — « la fusion ne résout pas d'identité, elle reconduit ce
            # que la collecte a déclaré » — et l'implémentation lisait le
            # mauvais fichier : le socle COMMITTÉ, jamais marqué, donc `None`,
            # donc aucun marquage, donc les tranches réécrites. Le run
            # `34329085168` est passé vert en ne basculant rien : les shards
            # avaient bien marqué leurs socles (vérifié dans l'artifact de
            # `gabriel-attal`), et la fusion les a défaits.
            acteur = acteur or _acteur_du_socle(path.parent, path.stem)
            merged = merge_raw_profile(merged, profile)
        if merged is not None and not complet:
            n_partiels_seuls += 1
            print(
                f"  [!] {filename} : seules des contributions réduites ont parlé "
                "de ce profil — rien réécrit, la version committée reste (#997). "
                "L'apport de ce run est perdu pour ce slug ; le prochain run le reprend."
            )
            continue
        if merged is not None:
            slug = filename[: -len(".json")]
            avant_derivees, avant_fichiers = _tranches_du_socle(out_dir, slug)
            ecrire_profil_brut(out_dir, slug, merged, acteur_ref=acteur)
            apres_derivees, apres_fichiers = _tranches_du_socle(out_dir, slug)
            n_derivees += apres_derivees
            n_fichiers += apres_fichiers
            # Une tranche qui était un fichier et ne l'est plus : le gain de ce
            # profil, mesuré et non déduit du nombre de dérivées — un profil
            # déjà basculé au run précédent ne supprime plus rien.
            n_supprimees += max(0, (avant_fichiers - apres_fichiers))
            n_written += 1

    if n_partiels_seuls:
        print(f"  · {n_partiels_seuls} profil(s) non réécrits : contribution réduite seule (#997).")
    if n_derivees or n_supprimees:
        print(
            f"  · tranches d'amendements : {n_derivees} dérivée(s) de l'archive, "
            f"{n_fichiers} en fichier, {n_supprimees} fichier(s) retiré(s) ce run."
        )
    return n_written


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description=(
            "Fusionne les profils bruts (*.json) de plusieurs répertoires "
            "d'extraction parallèles vers un répertoire cible unique. "
            "Usage typique : job merge-and-pivot après extract-an / "
            "extract-senat / extract-ue-officiel dans le workflow GitHub Actions."
        )
    )
    parser.add_argument(
        "--dirs",
        nargs="+",
        required=True,
        metavar="DIR",
        help="Répertoires sources à fusionner (au moins un requis).",
    )
    parser.add_argument(
        "--out",
        required=True,
        metavar="DIR",
        help="Répertoire de sortie pour les profils fusionnés.",
    )
    _args = parser.parse_args()

    _source_dirs = [Path(d) for d in _args.dirs]
    _out_dir = Path(_args.out)

    print(f"Fusion de {len(_source_dirs)} répertoire(s) → {_out_dir}")
    _n = merge_raw_dirs(_source_dirs, _out_dir)
    print(f"  ✓ {_n} profil(s) écrits dans {_out_dir}")
    sys.exit(0)
