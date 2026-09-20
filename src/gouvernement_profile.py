#!/usr/bin/env python3
"""
gouvernement_profile.py — Agrégation d'un profil de gouvernement complet à
partir de la composition ministérielle (`gouvernement_roster.py`) et des
textes législatifs d'origine gouvernementale (`gouvernement_textes.py`).

Miroir de `group_profile.build_groupe_profile` au niveau conceptuel
(agrégation locale pure, aucun appel réseau ici), mais pour un gouvernement :
combine `membres[]` (composition ministérielle) et `textes[]` (dossiers
législatifs) en un objet conforme à `schema_gouvernement.py`.

Sources en entrée :
  - `profils` : l'ensemble des profils pivot individuels déjà collectés
    (`pivot_data/profiles/*.pivot.json`) — passés à
    `gouvernement_roster.build_gouvernement_roster` pour dériver `membres[]`
    (portefeuille ministériel compris, #398) et à
    `gouvernement_roster.build_premier_ministre` pour `premier_ministre`.
    Ces deux champs restent `null` quand aucun profil local ne porte le
    mandat correspondant — jamais une valeur déduite du nom du gouvernement
    (règle AGENTS.md §2.5) ; c'est le cas des 7 Premiers ministres qui n'ont
    pas de profil pivot dans le dépôt.
  - `dossiers_gouvernementaux` : la sortie *non filtrée* de
    `gouvernement_textes.collect_dossiers_gouvernementaux`/
    `fetch_dossiers_gouvernementaux` (tous les dossiers d'origine
    gouvernementale, tous gouvernements confondus). Le rattachement à CE
    gouvernement est explicitement hors périmètre de `gouvernement_textes.py`
    (voir sa docstring) : c'est ce module qui filtre par recouvrement de
    `date_depot` avec `periode`, jamais par date de conclusion — un texte
    déposé sous un gouvernement A puis conclu sous un gouvernement B reste
    crédité à A.

Lien ministre → texte (#435) : `textes[].initiateurs` porte les initiateurs
déclarés par la source (`initiateur.acteurs.acteur[].acteurRef`, extraits par
`gouvernement_textes.py`), résolus vers un `membre_id` quand l'`acteurRef`
correspond à un membre retenu dans `membres[]` — c'est ce module qui peut le
faire, lui seul connaissant la composition du gouvernement. La couverture est
partielle par construction (un initiateur peut n'avoir aucun profil pivot dans
le dépôt, cas des 7 Premiers ministres sans profil) : l'`acteurRef` brut est
alors conservé avec `membre_id = null`, jamais rattaché à un profil approchant
(AGENTS.md §2.5). Un texte sans initiateur déclaré porte `initiateurs = null`,
pas `[]` — voir `_initiateurs_texte`.

Comptages (`comptages.par_statut`) : simple dénombrement des `textes[]`
retenus par statut, aucun taux ni pourcentage calculé nulle part dans ce
module (règle AGENTS.md §2.1) — voir `_select_textes_gouvernement`.

Anti double-comptage : un dossier est identifié par `dossier_id`, dédoublonné
au sein d'un même appel (protège contre un même dossier présent deux fois
dans `dossiers_gouvernementaux`, ex. fetch dupliqué en amont). Comme chaque
appel à `build_gouvernement_profile` ne traite qu'un seul gouvernement, un
même dossier ne peut être compté deux fois pour deux gouvernements
différents QUE s'il a été déposé sous ces deux périodes à la fois, ce qui
n'arrive jamais pour des périodes de gouvernement non chevauchantes.
`generate_gouvernement_profiles.py` ne fetch les dossiers et ne charge les
profils qu'UNE SEULE FOIS, partagés entre tous les gouvernements du batch —
voir sa docstring.

Cas limites gérés :
  - Dossier avec `statut = None` (fam_code inconnu, voir
    `gouvernement_textes._determine_statut`) : exclu de `textes[]` (le
    schéma n'admet pas de statut `null`, jamais de valeur par défaut
    inventée — règle AGENTS.md §2.5), avertissement conservé dans
    `meta.warnings`.
  - Dossier avec `chambre_depot_initial = None` (aucun acte `-DEPOT`
    identifiable) : exclu de `textes[]` pour la même raison.
  - Dossier avec `date_depot = None` : ne peut être rattaché à aucune
    période de gouvernement de façon fiable → exclu silencieusement (pas un
    warning, cas attendu pour un dossier sans dépôt identifiable, symétrique
    au traitement dans `gouvernement_textes.py`).
  - `periode.fin = None` : gouvernement toujours en fonction, tout dossier
    dont `date_depot >= periode.debut` est retenu (borne haute ouverte).

Usage (depuis la racine du dépôt) :
    python src/gouvernement_profile.py \\
        --config raw_data/gouvernements_reels.json \\
        --gouvernement-id "gouvernement:BAYROU" \\
        --profiles-dir pivot_data/profiles \\
        --out pivot_data/gouvernements/gouvernement-BAYROU.json \\
        --validate

    Pour générer tous les gouvernements de `raw_data/gouvernements_reels.json`
    en un seul run (un seul fetch réseau des dossiers, un seul chargement des
    profils), voir `generate_gouvernement_profiles.py`.
"""

import argparse
import json
from collections import Counter, defaultdict
import sys
from datetime import date
from pathlib import Path
from typing import Any, Callable, Optional

from licences import appliquer_licence_donnees
from schema_pivot import cle_tag_thematique, deriver_tags_thematiques, forme_publiee
from schema_gouvernement import (
    KNOWN_CHAMBRES_DEPOT_TEXTE,
    KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL,
    make_empty_comptages_statuts,
    make_empty_profil_gouvernement,
    validate_profil_gouvernement,
)
from gouvernement_roster import (
    acteur_ref_depuis_profil,
    build_gouvernement_roster,
    slugs_du_gouvernement,
    build_premier_ministre,
    charger_profils_et_chemins,
    lecteur_interventions,
    load_gouvernement_config,
    load_profils_from_dir,
)


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


def _texte_dans_periode(date_depot: Optional[date], g_debut: Optional[date], g_fin: Optional[date]) -> bool:
    """Un texte appartient au gouvernement si sa date de dépôt initial se
    situe dans `[g_debut, g_fin]` (`g_fin = None` → gouvernement toujours en
    fonction, borne haute ouverte). Rattachement par date de dépôt
    uniquement, jamais par date de conclusion (voir docstring du module) :
    une date de dépôt inconnue n'est jamais rattachée par défaut.
    """
    if date_depot is None or g_debut is None:
        return False
    if date_depot < g_debut:
        return False
    if g_fin is not None and date_depot > g_fin:
        return False
    return True


# ---------------------------------------------------------------------------
# Résolution des initiateurs de texte vers les membres du gouvernement (#435)
# ---------------------------------------------------------------------------

def _index_acteur_ref_vers_membre(
    profils: list[dict[str, Any]],
    membre_ids: set[str],
    warnings: list[str],
) -> dict[str, str]:
    """Index `acteurRef` AN -> `membre_id` pivot, restreint aux membres retenus
    dans `membres[]`.

    Restreint volontairement aux membres de CE gouvernement : la source déclare
    les initiateurs d'un texte par référence nue, et un `acteurRef` peut
    désigner quelqu'un qui n'est pas membre du gouvernement auquel le texte est
    rattaché (co-signataire, ex-ministre — 15 % de faux positifs mesurés par le
    spike #207 quand cette chaîne servait de signal d'origine, voir
    `gouvernement_textes.py`). Hors de `membres[]`, l'`acteurRef` brut est
    conservé sans `membre_id` plutôt que rattaché à un profil quelconque.

    Deux profils différents portant le même `acteurRef` sont un conflit
    d'identité que ce module ne tranche pas : aucun des deux n'est indexé et un
    warning est émis (AGENTS.md §2.5).
    """
    refs_vers_ids: dict[str, set[str]] = {}
    for profil in profils:
        profil_id = profil.get("id")
        if not profil_id or profil_id not in membre_ids:
            continue
        acteur_ref = acteur_ref_depuis_profil(profil)
        if acteur_ref:
            refs_vers_ids.setdefault(acteur_ref, set()).add(profil_id)

    index: dict[str, str] = {}
    for acteur_ref, ids in refs_vers_ids.items():
        if len(ids) > 1:
            warnings.append(
                f"gouvernement_profile: acteurRef {acteur_ref!r} porté par plusieurs "
                f"profils ({sorted(ids)}) — aucun membre_id résolu pour cet initiateur."
            )
            continue
        index[acteur_ref] = next(iter(ids))
    return index


def _initiateurs_texte(
    acteur_refs: Optional[list[str]],
    acteur_ref_vers_membre: dict[str, str],
) -> Optional[list[dict[str, Any]]]:
    """Normalise les `acteurRef` d'un dossier en entrées
    `textes[].initiateurs` (#435), ou `None` si la source n'en déclare aucun.

    `None` et non `[]` : une liste vide affirmerait qu'aucun ministre n'a porté
    le texte, alors que le fait constaté est que la source ne le dit pas
    (AGENTS.md §2.5). `membre_id` reste `null` quand l'`acteurRef` n'est pas
    résolvable — la référence brute, elle, est toujours conservée.
    """
    if not acteur_refs:
        return None
    return [
        {
            "acteur_ref": acteur_ref,
            "membre_id": acteur_ref_vers_membre.get(acteur_ref),
        }
        for acteur_ref in acteur_refs
    ]


# ---------------------------------------------------------------------------
# Sélection et normalisation des textes du gouvernement
# ---------------------------------------------------------------------------

def _commission_du_texte(
    dossier_id: Optional[str],
    chambre: Optional[str],
    commissions_par_dossier: Optional[dict[str, Any]],
) -> tuple[Optional[dict[str, Any]], Optional[dict[str, str]]]:
    """La commission saisie au fond d'un texte, ou le motif de son absence (#689).

    Rend `(commission, non_resolue)` dont **exactement un** membre est non nul.
    Lire les lois d'un gouvernement par matière suppose une matière ; l'Assemblée
    en fournit une sans que nous ayons à en inventer — elle renvoie chaque
    dossier à une commission. La jointure se fait sur `dossier_id`, jamais sur le
    titre : c'est la règle de `regrouper-nest-pas-joindre-639`.

    **Les trois motifs d'absence ne se confondent pas**, et c'est tout l'objet du
    vocabulaire fermé :

    - `depot_senat` — le texte est déposé au Sénat, et l'index est celui de
      l'**AN**. Mesuré le 04/09/2026 sur les 725 textes publiés : **381 des 381**
      dossiers déposés à l'AN résolvent, **0 des 174** non résolus n'est un dépôt
      AN. Ce n'est pas un trou de collecte, c'est le périmètre (#528), et il ne
      se comblera pas ;
    - `absente_de_l_index` — dépôt AN, dossier absent de l'index : là, c'est un
      vrai trou. Il vaut **0** aujourd'hui, ce qui en fait un compteur-témoin ;
    - `index_indisponible` — l'index n'a pas été fourni au run. Le distinguer
      évite de lire une panne comme une décision, la leçon de #726.
    """
    if commissions_par_dossier is None:
        return None, {"motif": "index_indisponible"}
    commission = commissions_par_dossier.get(dossier_id) if dossier_id else None
    if isinstance(commission, dict):
        # Projection explicite, `type` compris — et il n'est PAS une propriété du
        # seul référentiel, contrairement à ce que ce commentaire affirmait
        # d'abord. Une `CNPS` est une commission **spéciale, créée pour ce
        # texte-là** ; une `COMPER` est permanente et couvre une matière. Le type
        # est donc ce qui sépare « la commission des lois a examiné 50 textes »
        # de « une commission a été créée pour celui-ci ».
        #
        # Sans lui, distinguer les matières principales de la traîne n'a d'autre
        # règle qu'un seuil — « les 8 premières », « au moins 5 % » —, c'est-à-dire
        # l'arbitrage éditorial déguisé en mesure que §2 règle 1 refuse. Avec lui,
        # il n'y a aucun seuil : l'Assemblée a déjà fait le partage. Mesuré sur
        # les 725 textes publiés : COMPER 532, CNPS 19 — et sur le gouvernement
        # Philippe II, 8 organes permanents pour 218 textes contre 8 spéciales
        # pour 10, à une ou deux occurrences chacune.
        return {
            "organe_ref": commission.get("organe_ref"),
            "sigle": commission.get("sigle"),
            "nom": commission.get("nom"),
            "type": commission.get("type"),
        }, None
    motif = "depot_senat" if chambre == "Senat" else "absente_de_l_index"
    return None, {"motif": motif}


def _select_textes_gouvernement(
    dossiers_gouvernementaux: list[dict[str, Any]],
    g_debut: Optional[date],
    g_fin: Optional[date],
    acteur_ref_vers_membre: Optional[dict[str, str]] = None,
    commissions_par_dossier: Optional[dict[str, Any]] = None,
) -> tuple[list[dict[str, Any]], dict[str, int], list[str]]:
    """Filtre `dossiers_gouvernementaux` (sortie non filtrée de
    `gouvernement_textes`) sur la période du gouvernement, normalise chaque
    dossier retenu en entrée `textes[]` du schéma, et dénombre les statuts.

    `acteur_ref_vers_membre` (voir `_index_acteur_ref_vers_membre`) résout les
    initiateurs déclarés par la source vers un `membre_id`. Absent, les
    initiateurs sont conservés avec leur seul `acteurRef` : c'est une couverture
    réduite, jamais un lien deviné.

    Returns:
        Tuple (textes retenus, comptages.par_statut, warnings). Aucun taux
        calculé : `comptages` ne contient que des entiers bruts (règle
        AGENTS.md §2.1).
    """
    acteur_ref_vers_membre = acteur_ref_vers_membre or {}
    seen_ids: set[str] = set()
    textes: list[dict[str, Any]] = []
    par_statut = make_empty_comptages_statuts()
    warnings: list[str] = []

    for dossier in dossiers_gouvernementaux:
        dossier_id = dossier.get("dossier_id")
        if dossier_id:
            if dossier_id in seen_ids:
                continue  # anti double-comptage : dossier déjà traité dans cet appel
            seen_ids.add(dossier_id)

        parsed_date_depot = _parse_date(dossier.get("date_depot"))
        if not _texte_dans_periode(parsed_date_depot, g_debut, g_fin):
            continue

        for w in dossier.get("warnings") or []:
            warnings.append(w)

        statut = dossier.get("statut")
        chambre = dossier.get("chambre_depot_initial")

        if statut is None or statut not in KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL:
            warnings.append(
                f"gouvernement_profile: dossier {dossier_id!r} exclu de textes[] : "
                f"statut indéterminé ou inconnu ({statut!r})."
            )
            continue
        if chambre not in KNOWN_CHAMBRES_DEPOT_TEXTE:
            warnings.append(
                f"gouvernement_profile: dossier {dossier_id!r} exclu de textes[] : "
                f"chambre_depot_initial indéterminée ({chambre!r})."
            )
            continue

        textes.append({
            "dossier_id": dossier_id,
            "titre": dossier.get("titre"),
            "statut": statut,
            "chambre_depot_initial": chambre,
            "date_depot": dossier.get("date_depot"),
            "date_dernier_evenement": dossier.get("date_dernier_evenement"),
            "sort_49_3": dossier.get("sort_49_3"),
            "initiateurs": _initiateurs_texte(
                dossier.get("initiateurs_acteur_refs"), acteur_ref_vers_membre
            ),
            "source_url": dossier.get("source_url"),
        })
        commission, non_resolue = _commission_du_texte(
            dossier_id, chambre, commissions_par_dossier
        )
        textes[-1]["commission_saisie_au_fond"] = commission
        if non_resolue is not None:
            textes[-1]["commission_non_resolue"] = non_resolue
        par_statut[statut] += 1

    return textes, par_statut, warnings


# ---------------------------------------------------------------------------
# Sur quoi les membres ont pris la parole (#1020)
# ---------------------------------------------------------------------------
#
# Même logique que la fiche de groupe (`group_profile.aggregate_tags_thematiques`),
# à UNE différence près, et elle est mesurée.
#
# **Le groupe filtre par LÉGISLATURE, lue dans l'identifiant de l'intervention
# et jamais déduite d'une date (#403). Un gouvernement ne peut pas.** Sa période
# n'est pas une législature : Borne court du 17/05/2022 au 09/01/2024, à cheval
# sur la XVe et la XVIe. Retenir ses deux législatures garderait 68 524 des
# 97 898 interventions de ses membres — sept ans de parole attribués à un
# gouvernement qui a duré vingt mois.
#
# Le filtre est donc la période, sur la date publiée de l'intervention. Ce n'est
# pas une entorse à #403, qui interdit de DÉDUIRE une législature d'une date :
# ici rien n'est déduit, un fait daté est retenu dans une période que le
# référentiel déclare. La source porte la date à 99,99 % — 97 893 des 97 898.
#
# **Et la période retenue est celle DU MEMBRE, pas celle du gouvernement.** Une
# personne n'y siège souvent qu'un moment, et l'écart n'est pas de bord :
#
#     Borne        25 704 → 15 750 entrées   (−39 %)
#     Philippe II  40 719 → 25 264 entrées   (−38 %)
#
# Le cas qui le rend évident : **Yaël Braun-Pivet, 8 968 → 0**. Ministre trois
# jours (24 → 27 juin 2022), puis présidente de l'Assemblée. Ses 8 968
# interventions dans la fenêtre Borne sont celles d'une présidente de séance.
# François de Rugy, 11 310 → 1 058, pour la même raison. Sans ce filtre, « la
# parole du gouvernement » serait dominée par deux personnes qui parlaient EN
# FACE du banc.
# → `docs/decisions/agregat-parole-gouvernement-1020.md`


def fenetres_des_membres(
    membres: list[dict[str, Any]],
    periode_debut: Optional[str],
    periode_fin: Optional[str],
) -> dict[str, list[tuple[str, str]]]:
    """`{membre_id: [(début, fin), …]}` — le passage réel de chaque personne.

    Une personne peut avoir PLUSIEURS entrées dans `membres[]` : une par
    période de portefeuille (#398). L'union de ses entrées décrit son passage,
    et c'est elle qui fait fenêtre — pas la première trouvée.

    Une borne absente sur l'entrée retombe sur celle du gouvernement : `fin`
    nulle veut dire « toujours en fonction » et non « fin inconnue », et le
    gouvernement, lui, porte toujours sa période. Un gouvernement en cours a
    une `periode_fin` nulle : la fenêtre reste alors ouverte, ce qui est le
    fait (§2 règle 5, jamais la date du jour).
    """
    fin_gouv = periode_fin or "9999-12-31"
    fenetres: dict[str, list[tuple[str, str]]] = {}
    for membre in membres:
        membre_id = membre.get("membre_id")
        if not membre_id:
            continue
        debut = membre.get("debut") or periode_debut
        if not debut:
            # Sans borne basse ni sur l'entrée ni sur le gouvernement, la
            # fenêtre n'est pas définissable. On ne la remplace pas par une
            # borne ouverte, qui retiendrait toute la carrière.
            continue
        fenetres.setdefault(membre_id, []).append((debut[:10], (membre.get("fin") or fin_gouv)[:10]))
    return fenetres


def agreger_tags_thematiques(
    fenetres: dict[str, list[tuple[str, str]]],
    lire_interventions: Callable[[str], list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], int, int, int]:
    """`(tags_agreges, membres_porteurs, hors_fenetre, sans_date)`.

    **`lire_interventions` et non des profils, parce que les profils n'en
    portent pas.** Les trois lectures du corpus passent par la projection de
    #635, qui retire `interventions` (38,1 % du volume) : cette fonction a
    publié `[]` sur les 17 fiches pendant un run entier, sans rien dire, parce
    qu'elle recevait des profils projetés et lisait un bloc absent. Le lecteur
    la force à dire d'où vient la matière, et `gouvernement_roster.lecteur_interventions`
    la lit sur disque, une personne à la fois.

    Le test qui n'a pas vu le défaut appelait cette fonction avec des profils
    fabriqués portant leurs `interventions` : il prouvait l'agrégation, jamais
    le chemin. La garde est désormais dans
    `tests/test_generate_gouvernement_profiles.py`, sur des profils écrits sur
    disque et lus par `generate_all`.

    Une étiquette compte **une fois par membre**, comme sur la fiche de groupe :
    l'agrégat dit combien de personnes ont parlé d'un sujet, jamais combien de
    fois elles en ont parlé — un compte d'occurrences serait un indice
    d'activité (§2 règle 1).

    **Aucun ratio n'est publié.** `nb_membres_porteurs` est rendu seul, et son
    dénominateur est `comptages.membres_avec_interventions`, publié à côté.
    C'est l'arbitrage que `mandats_agreges` a déjà rendu sur la fiche de
    groupe : « il est publié plutôt que pré-divisé, pour que le lecteur voie
    "5 / 76" et non un pourcentage seul (§2.7) ». `tags_thematiques_agreges`
    du groupe porte encore un `poids_relatif` et n'a pas suivi ; le nouvel
    agrégat ne reproduit pas ce retard.

    **Une intervention sans date est écartée, et comptée.** C'est la seconde
    divergence d'avec le groupe, qui retient ses entrées sans législature
    plutôt que de les exclure. La raison n'est pas la même de part et d'autre :
    une législature dure cinq ans et une entrée non datée y tombe
    probablement ; un gouvernement dure quelques mois, et rien ne permet de
    l'y placer. Mesuré sur Borne : **5 entrées sur 97 898**, soit un choix sans
    conséquence de volume — mais qui, pris dans l'autre sens, affirmerait sans
    source (§2 règle 5).
    """
    # #1042 — compté par CLÉ (pluriel simple), publié sous une FORME observée.
    porteurs_par_cle: dict[str, int] = {}
    formes_par_cle: dict[str, Counter] = defaultdict(Counter)
    membres_porteurs = 0
    hors_fenetre = 0
    sans_date = 0

    for membre_id, fenetres_membre in sorted(fenetres.items()):
        retenues: list[dict[str, Any]] = []
        for interv in lire_interventions(membre_id) or []:
            if not isinstance(interv, dict):
                continue
            jour = (interv.get("date") or "")[:10]
            if not jour:
                sans_date += 1
                continue
            if not any(debut <= jour <= fin for debut, fin in fenetres_membre):
                hors_fenetre += 1
                continue
            retenues.append(interv)
        if not retenues:
            continue
        membres_porteurs += 1
        # `deriver_tags_thematiques` est la fabrique UNIQUE des étiquettes
        # (#710) : la rappeler sur les interventions retenues donne exactement
        # ce que `tags_thematiques` porterait si le profil n'avait que
        # celles-là. Rien n'est dupliqué, et le repli `theme_officiel` puis
        # `mots_cles` est dedans.
        cles_du_membre: set[str] = set()
        for tag in set(deriver_tags_thematiques(retenues)):
            if tag:
                cle = cle_tag_thematique(tag)
                formes_par_cle[cle][tag] += 1
                cles_du_membre.add(cle)
        for cle in cles_du_membre:
            porteurs_par_cle[cle] = porteurs_par_cle.get(cle, 0) + 1

    agreges = sorted(
        ({"tag": forme_publiee(formes_par_cle[cle]), "nb_membres_porteurs": n}
         for cle, n in porteurs_par_cle.items()),
        key=lambda x: (-x["nb_membres_porteurs"], x["tag"]),
    )
    return agreges, membres_porteurs, hors_fenetre, sans_date


# ---------------------------------------------------------------------------
# Fonction principale d'agrégation
# ---------------------------------------------------------------------------

def build_gouvernement_profile(
    gouvernement_id: str,
    nom: str,
    libelle_an: str,
    periode_debut: Optional[str],
    periode_fin: Optional[str],
    profils: list[dict[str, Any]],
    dossiers_gouvernementaux: list[dict[str, Any]],
    membres_recenses: Optional[int] = None,
    licence_donnees: str = "",
    commissions_par_dossier: Optional[dict[str, Any]] = None,
    membres_roster: Optional[list[dict[str, Any]]] = None,
    organe_ref: Optional[str] = None,
    lire_interventions: Optional[Callable[[str], list[dict[str, Any]]]] = None,
) -> dict[str, Any]:
    """Construit un profil de gouvernement à partir des profils pivot
    individuels déjà collectés et des dossiers législatifs d'origine
    gouvernementale déjà collectés (non filtrés par gouvernement).

    Args:
        gouvernement_id: ex. "gouvernement:BAYROU".
        nom: nom complet, ex. "Gouvernement Bayrou".
        libelle_an: `organe.libelleAbrege` AN du gouvernement (désambiguïsation,
                    voir `gouvernement_roster.py`), ex. "BAYROU".
        periode_debut: début de la période du gouvernement (YYYY-MM-DD).
        periode_fin: fin de la période (YYYY-MM-DD), ou None si toujours en fonction.
        profils: liste de profils pivot v1 (tous les profils disponibles, pas
                 seulement ceux du gouvernement — le filtrage par mandat
                 revient à `gouvernement_roster.build_gouvernement_roster`).
        dossiers_gouvernementaux: sortie non filtrée de
                 `gouvernement_textes.collect_dossiers_gouvernementaux`/
                 `fetch_dossiers_gouvernementaux` (`["dossiers"]`).
        licence_donnees: texte de licence à inscrire dans meta.
        membres_roster: la clé `gouvernements` de `rosters_bruts.json` (#996
                 lot 4) — le roster AMO30, non filtré. Avec `organe_ref`, il
                 remplace la correspondance de libellé pour rattacher les
                 membres. Absent, le repli historique s'applique.
        organe_ref: uid de l'organe `GOUVERNEMENT` (ex. "PO873418"), tel que
                 `raw_data/gouvernements_reels.json` le porte.
        lire_interventions: `lire(membre_id) -> interventions[]`, d'où
                 `tags_thematiques_agreges` tire sa matière (#1020). `profils`
                 ne peut pas la porter : il est projeté sur cinq blocs (#635).
                 `None` veut dire « personne ne peut lire les interventions » :
                 l'agrégat n'est alors pas calculé, `membres_avec_interventions`
                 est publié `null` — jamais `0`, qui affirmerait qu'aucun
                 membre n'a parlé (§2 règle 5) — et un warning le dit.

    Returns:
        Profil de gouvernement dict conforme à `schema_gouvernement.py`.
    """
    warnings: list[str] = []

    # #996 lot 4 — `None` quand le roster manque : le repli reste le libellé,
    # et la fiche est produite quand même. Un ensemble vide dirait « ce
    # gouvernement n'a aucun membre », ce qui n'est pas la même chose.
    slugs_roster = slugs_du_gouvernement(membres_roster, organe_ref)

    membres = build_gouvernement_roster(
        libelle_an=libelle_an,
        periode_debut=periode_debut,
        periode_fin=periode_fin,
        profils=profils,
        warnings=warnings,
        slugs_roster=slugs_roster,
    )
    premier_ministre = build_premier_ministre(
        libelle_an=libelle_an,
        periode_debut=periode_debut,
        periode_fin=periode_fin,
        profils=profils,
        warnings=warnings,
    )

    membre_ids = {m["membre_id"] for m in membres if m.get("membre_id")}

    g_debut = _parse_date(periode_debut)
    g_fin = _parse_date(periode_fin)
    acteur_ref_vers_membre = _index_acteur_ref_vers_membre(profils, membre_ids, warnings)
    textes, par_statut, textes_warnings = _select_textes_gouvernement(
        dossiers_gouvernementaux, g_debut, g_fin, acteur_ref_vers_membre,
        commissions_par_dossier=commissions_par_dossier,
    )
    warnings.extend(textes_warnings)

    # --- Sources (dédoublonnées) : uniquement celles des profils des membres
    # effectivement retenus dans membres[], pas de tous les profils passés en
    # entrée (qui couvrent potentiellement l'ensemble du dépôt).
    seen_sources: set[tuple[str, str]] = set()
    sources: list[dict[str, Any]] = []
    for p in profils:
        if p.get("id") not in membre_ids:
            continue
        for s in (p.get("sources") or []):
            key = (s.get("type") or "", s.get("url") or "")
            if key not in seen_sources:
                seen_sources.add(key)
                sources.append(s)

    profil_gouvernement = make_empty_profil_gouvernement(gouvernement_id=gouvernement_id, nom=nom)
    profil_gouvernement["periode"] = {
        "debut": periode_debut,
        "fin": periode_fin,
        "actif": periode_fin is None,
    }
    profil_gouvernement["premier_ministre"] = premier_ministre
    profil_gouvernement["membres"] = membres
    profil_gouvernement["textes"] = textes
    profil_gouvernement["comptages"]["par_statut"] = par_statut
    # #996 — le dénominateur de `membres[]` : ce que l'AN recense, profil ou
    # non. `None` quand la liste ne le porte pas : un dénominateur inventé
    # ferait lire « 2 des 2 membres » là où il en manque 19 (§2 règle 5).
    profil_gouvernement["comptages"]["membres_recenses"] = membres_recenses
    # #996 lot 4 — `membres[]` porte une entrée par PÉRIODE, pas par personne
    # (#398). Publier `len(membres)` à côté de `membres_recenses` revenait à
    # poser deux nombres de populations différentes côte à côte. Celui-ci se
    # rapproche du recensement, et lui seul.
    profil_gouvernement["comptages"]["membres_distincts"] = len(
        {m.get("membre_id") for m in membres if m.get("membre_id")}
    )

    # #1020 — sur quoi les membres ont pris la parole, PENDANT leur passage.
    fenetres = fenetres_des_membres(membres, periode_debut, periode_fin)
    if lire_interventions is None:
        # Pas de lecteur : l'agrégat n'est pas mesuré. Le dire, plutôt que de
        # publier un zéro qui se lit « aucun membre n'a pris la parole » —
        # c'est exactement ce que les 17 fiches ont publié pendant un run.
        tags_agreges, membres_porteurs, hors_fenetre, sans_date = [], None, 0, 0
        warnings.append(
            "gouvernement_profile: tags_thematiques_agreges non calculé — aucun "
            "lecteur d'interventions fourni (les profils sont projetés, #635)."
        )
    else:
        tags_agreges, membres_porteurs, hors_fenetre, sans_date = agreger_tags_thematiques(
            fenetres, lire_interventions)
    profil_gouvernement["tags_thematiques_agreges"] = tags_agreges
    # Le dénominateur de `nb_membres_porteurs`, publié plutôt que pré-divisé
    # (§2.7). Il rend la couverture LISIBLE : tant que les membres n'ont pas
    # tous leurs interventions collectées, il est plus petit que
    # `membres_distincts`, et l'écart se voit au lieu d'être dilué dans un
    # pourcentage.
    profil_gouvernement["comptages"]["membres_avec_interventions"] = membres_porteurs
    if hors_fenetre:
        warnings.append(
            f"gouvernement_profile: tags_thematiques_agreges — {hors_fenetre} "
            "intervention(s) écartée(s) : hors de la fenêtre de passage du membre "
            "dans ce gouvernement."
        )
    if sans_date:
        warnings.append(
            f"gouvernement_profile: tags_thematiques_agreges — {sans_date} "
            "intervention(s) écartée(s) : sans date, donc non plaçable dans la "
            "période (AGENTS.md §2 règle 5)."
        )
    profil_gouvernement["sources"] = sources
    # `licence_donnees` : dérivée de `sources[]` quand l'appelant n'impose rien
    # (#530, lot 6). Le pipeline ne passe pas `--licence`, et les 10 fiches
    # publiées portaient donc une attribution **vide** — un manque, sur des
    # documents dérivés de données ouvertes qui en exigent une (AGENTS.md §7).
    # La dérivation, et non une constante : `sources[]` agrège ici celles des profils membres, qui ne relèvent pas
    # toutes de la même licence. L'argument explicite reste
    # prioritaire, c'est lui qui permet d'annoter une fiche hors pipeline.
    if licence_donnees:
        profil_gouvernement["meta"]["licence_donnees"] = licence_donnees
    else:
        appliquer_licence_donnees(profil_gouvernement)
    profil_gouvernement["meta"]["warnings"] = warnings

    return profil_gouvernement


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gouvernement_profile.py",
        description=(
            "Combine la composition ministérielle (gouvernement_roster.py) et les "
            "textes législatifs (gouvernement_textes.py) en un profil de gouvernement "
            "complet, conforme à schema_gouvernement.py."
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
        help="Ex. 'gouvernement:BAYROU' (doit exister dans --config).",
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Dossier des pivots *.pivot.json (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--licence",
        default="",
        metavar="TEXTE",
        help="Texte de licence à inscrire dans meta.licence_donnees.",
    )
    parser.add_argument(
        "--out",
        default=None,
        metavar="FICHIER",
        help="Fichier de sortie JSON (défaut : stdout).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valide le profil de gouvernement produit et affiche les erreurs éventuelles.",
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

    profils, chemins_profils = charger_profils_et_chemins(Path(args.profiles_dir))
    print(f"→ {len(profils)} profil(s) pivot chargé(s).", file=sys.stderr)

    from gouvernement_textes import fetch_dossiers_gouvernementaux  # import tardif : réseau non requis hors CLI

    print("→ Récupération des dossiers législatifs gouvernementaux…", file=sys.stderr)
    dossiers_result = fetch_dossiers_gouvernementaux()
    print(f"→ {len(dossiers_result['dossiers'])} dossier(s) d'origine gouvernementale récupéré(s).", file=sys.stderr)

    periode = entry.get("periode") or {}
    profil_gouvernement = build_gouvernement_profile(
        gouvernement_id=entry.get("gouvernement_id"),
        nom=entry.get("nom"),
        libelle_an=entry.get("libelle_an") or "",
        periode_debut=periode.get("debut"),
        periode_fin=periode.get("fin"),
        membres_recenses=entry.get("membres_recenses"),
        profils=profils,
        dossiers_gouvernementaux=dossiers_result["dossiers"],
        licence_donnees=args.licence,
        lire_interventions=lecteur_interventions(chemins_profils),
    )
    if dossiers_result["warnings"]:
        profil_gouvernement["meta"]["warnings"].extend(dossiers_result["warnings"])

    if args.validate:
        errors = validate_profil_gouvernement(profil_gouvernement)
        if errors:
            print(f"  [!] {len(errors)} erreur(s) de validation :", file=sys.stderr)
            for e in errors:
                print(f"      - {e}", file=sys.stderr)
        else:
            print("  ✓ Profil de gouvernement valide selon le schéma.", file=sys.stderr)

    output_json = json.dumps(profil_gouvernement, ensure_ascii=False, indent=2)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")
        print(f"  ✓ Profil de gouvernement écrit : {out_path}", file=sys.stderr)
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
