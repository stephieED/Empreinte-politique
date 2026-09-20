#!/usr/bin/env python3
"""
group_profile.py — Agrégation de profils individuels en profil de groupe politique.

Ce module calcule, à partir d'une liste de profils pivot v1 (schéma_pivot.py),
un profil de groupe conforme au schéma_groupe.py. Il ne fait aucun appel réseau :
il agrège uniquement les données déjà présentes dans les profils individuels.

Calculs produits :
  1. Cohésion de vote : par scrutin, position majoritaire du groupe + taux
     d'alignement. « Absent » (aucune trace de vote) est distingué de
     « non_votant » et « excusé ».
  2. Thèmes dominants : agrégation des tags_thematiques de tous les membres.
  3. Membres : liste avec dates d'entrée/sortie DU GROUPE, lues sur le mandat
     de groupe politique (`GP`) de la législature de la fiche que rend le
     roster AMO30 — transit écarté, organes successifs recollés (#526/#653).
     Elles ne sont plus dérivées des mandats électifs : depuis #647 un profil
     porte toute sa carrière, et « premier mandat électif » datait l'entrée
     dans un groupe de la XVIe législature à 2002.
  4. Amendements agrégés (amendements_agreges) : les amendements **distincts**
     portés par au moins un membre — un amendement cosigné par trois d'entre eux
     en est un (#643) —, leur ventilation par sort et par type de déposant, et
     le taux d'adoption qui en découle. Les **signatures** apposées par les
     membres sont une autre grandeur, tout aussi réelle : elles vivent sous
     `signatures`, sous leur nom. Le total tous déposants confondus ne sert
     jamais de comparateur direct, seul le sous-total "depute" est de même
     nature que les amendements d'un⋅e élu⋅e (AGENTS.md §6).
  5. Mandats agrégés (mandats_agreges) : agrégation catégorielle sur mandats[]
     (commission, groupe_amitie, extra_parlementaire — voir
     MANDATS_AGREGES_CATEGORIES), par (categorie, label). Éligibilité par
     chevauchement d'intervalles avec les mandats électifs du membre.
  6. Écarts de cohésion/participation individuels (compute_ecarts_cohesion_internes) :
     donnée de CONTRÔLE INTERNE uniquement, volontairement absente du schéma de
     groupe public — accessible via --rapport-interne, jamais via --out.

Cas limites gérés :
  - Élu qui change de groupe en cours de mandat : seuls les membres dont la
    période de mandat électif inclut la date du scrutin sont comptés comme
    éligibles. Les mandats multiples (sur plusieurs législatures) sont tous
    examinés.
  - Groupe dissous/renommé : le groupe_id et groupe_nom sont des paramètres
    explicites ; `historique_noms` recopie les organes successifs du groupe
    dans sa législature, mesurés sur AMO30 et committés (#815).
  - Scrutin sans quorum : quorum_atteint = False, cohésion toujours calculée.
  - tags_thematiques vides sur les profils individuels : fallback automatique
    sur les mots-clés des interventions (loggé dans meta.warnings).
  - mandats_agreges : doublon (categorie, label) pour un même membre (ex.
    réélu·e à la même commission) → une seule entrée retenue, priorité à
    actif=true sinon la plus récente par date de fin.
  - mandats_agreges : adhésion d'une journée ou moins (43 % des adhésions de
    commission publiées) → comptée dans nb_membres_cumul_historique, absente de
    nb_membres_a_la_date_de_reference. Distinguée, jamais filtrée (#656).
  - effectif : `min_historique`/`max_historique` sont l'amplitude sur la
    période, `{valeur, date}` chacun (#702). Une seule entrée `membres[]` sans
    `debut_dans_groupe` les laisse à `null` — seuil 0, motif en clair dans
    meta.warnings. Un départ suivi d'un retour reste invisible : `membres[]` ne
    porte qu'un intervalle par membre (périodes recollées, #526).

Les trois décisions à relire avant de toucher à une agrégation
--------------------------------------------------------------
Quinze décisions nomment une fonction de ce module ; la liste complète et à jour
est dans `docs/decisions-par-module.md`. Ces trois-là portent l'éligibilité, donc
les dénominateurs publiés (AGENTS.md §2.7) :

- `docs/decisions/mandat-electif-perdu-fausse-le-denominateur.md` — un
  `mandats[].categorie == "mandat_electif"` perdu ne manque pas seulement sur la
  fiche : `_member_eligibility_intervals` en dérive la période d'éligibilité, et
  le membre sort du **dénominateur** d'un ratio publié. Mesuré : `groupe-AN-SOC-16`
  publiait 0 scrutin de cohésion sur 814, sans qu'aucune donnée manque.
- `docs/decisions/mandats-agreges-famille-1.md` — le périmètre de
  `MANDATS_AGREGES_CATEGORIES` et ce qui en est **exclu exprès** (`mandat_electif`
  serait circulaire, `groupe_politique` redondant), plus la règle de chevauchement
  d'intervalles de `_intervals_overlap`.
- `docs/decisions/chambre-par-mandat-electif.md` — la chambre est un fait du
  **mandat**, jamais du profil. Un agrégat qui la relit sur le profil mélange les
  chambres d'un membre passé d'une assemblée à l'autre.

Usage (depuis la racine du dépôt) :
    python src/group_profile.py \\
        --groupe-id "AN:SOC" \\
        --groupe-sigle SOC \\
        --groupe-nom "Socialistes et apparentés" \\
        --chambre AN \\
        --legislature 16 \\
        pivot_data/profiles/jerome-guedj.pivot.json \\
        pivot_data/profiles/boris-vallaud.pivot.json \\
        --out pivot_data/groupes/groupe-SOC-16.json

    Les profils en entrée peuvent être au format brut (candidate_profile.py)
    ou au format pivot v1 (normalize_profil.py). Le script détecte automatiquement
    le format et normalise si nécessaire.

Mode --from-roster (composition réelle du groupe, via group_roster.py) :
    Récupère la vraie liste des membres du groupe parlementaire depuis le
    référentiel AMO30 de l'Assemblée nationale (voir group_roster.py et
    an_roster.py) puis charge le pivot local de chaque membre trouvé dans
    --profiles-dir (pivot_data/profiles/<slug>.pivot.json).
    Les membres du roster sans pivot local sont ignorés et signalés dans
    meta.warnings ; la couverture réelle (roster_total / profils_disponibles)
    est inscrite dans meta.couverture_roster, jamais confondue avec l'effectif.

    python src/group_profile.py \\
        --from-roster --roster-chambre deputes \\
        --groupe-id "AN:LR" --groupe-sigle LR --groupe-nom "Les Républicains" \\
        --chambre AN --legislature 16 \\
        --out pivot_data/groupes/groupe-AN-LR-16.json

    NB : distinct de parti_profile.py, qui agrège les candidats présidentiels
    déclarés partageant un même label de parti (raw_data/candidats.json) — un
    échantillon éditorial, pas un groupe parlementaire.
"""

import argparse
import json
from collections import Counter, defaultdict
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Optional

from avertissements import DESTINATAIRE_LECTEUR, avertissement
from licences import appliquer_licence_donnees
from schema_groupe import (
    SCHEMA_GROUPE_VERSION,
    ORIGINE_DATE_REFERENCE_CLOTURE,
    ORIGINE_DATE_REFERENCE_GENERATION,
    AMENDEMENTS_TYPES_DEPOSANT,
    ETAT_ROSTER_DANS_LE_PERIMETRE,
    make_empty_profil_groupe,
    make_empty_amendements_stats,
    validate_profil_groupe,
)
from groupes_config import (
    historique_noms_publie,
    position_politique_publiee,
    succession_publiee,
)
from merge_profile import load_existing_document, preserve_stable_freshness_timestamps
from normalize_profil import normalize_profil
from amendements_index import (
    AmendementsIndex,
    DEFAULT_AMENDEMENTS_DIR,
    charger as charger_amendements,
    joindre as joindre_amendements,
    legislature_de_id,
)
from schema_pivot import (
    cle_tag_thematique,
    deriver_tags_thematiques,
    forme_publiee,
    legislature_de_intervention,
)
from scrutins_index import ScrutinsIndex, charger as charger_scrutins, decomposer_id, DEFAULT_SCRUTINS_PATH


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


# ---------------------------------------------------------------------------
# Eligibilité d'un membre à un scrutin
# ---------------------------------------------------------------------------

def _mandats_electifs(
    mandats: list[dict[str, Any]], chambre: Optional[str] = None
) -> list[dict[str, Any]]:
    """Mandats électifs d'un membre, restreints à la chambre du groupe (#492).

    ``_member_eligibility_intervals`` prenait l'**union** de tous les
    `mandat_electif`, sans distinction de chambre. Un mandat sénatorial ne peut
    pas chevaucher un mandat AN (incompatibilité constitutionnelle), donc dans
    le cas général l'union est inoffensive ; le cas dangereux est le
    **changement de chambre en cours de législature**, qui prolongerait la
    fenêtre d'éligibilité au-delà du départ de l'Assemblée et compterait le
    membre absent sur des scrutins qu'il ne pouvait plus voter — un dénominateur
    de cohésion faux (§2.7). Le filtre n'était pas écrivable avant #492 : la
    chambre n'était portée par aucun mandat.

    **Un mandat à `chambre: null` est conservé**, jamais écarté. L'écarter
    réduirait un dénominateur publié sur la foi d'une donnée absente, ce qui est
    l'erreur exactement symétrique de celle qu'on corrige. Conséquence directe :
    sur un corpus entièrement non estampillé — celui d'aujourd'hui, 214 des 228
    `mandat_electif` mesurés sur `f5a828b` — ce filtre ne change **aucun**
    dénominateur publié. La correction entre en vigueur au fil de la collecte,
    mandat par mandat, jamais d'un coup.

    ``chambre=None`` (groupe sans chambre, ou appel hors contexte de groupe) ne
    filtre rien.
    """
    electif = [m for m in mandats if m.get("categorie") == "mandat_electif"]
    if chambre is None:
        return electif
    return [m for m in electif if m.get("chambre") in (None, chambre)]


def _member_eligibility_intervals(
    mandats: list[dict[str, Any]], chambre: Optional[str] = None
) -> Optional[list[tuple[Optional[date], Optional[date]]]]:
    """Pré-analyse les mandats électifs d'un membre en intervalles (début, fin).

    Évite de refiltrer ``mandats`` et de reparser les dates de mandat à chaque
    scrutin dans ``_compute_cohesion_votes`` (le même membre est testé pour des
    milliers de scrutins). Retourne None si aucun mandat électif n'est renseigné
    (éligibilité par défaut, cf. ``_member_eligible_at``).

    ``chambre`` : chambre du groupe, voir ``_mandats_electifs`` (#492). Deux
    absences y sont distinguées, et elles n'ont pas le même sens :

    - **aucun mandat électif du tout** → ``None``, éligibilité par défaut :
      absence d'information, on ne peut pas exclure (comportement historique) ;
    - **des mandats électifs, mais aucun dans cette chambre** → ``[]``, donc
      jamais éligible : ce n'est pas une absence d'information, c'est
      l'information que ce membre ne siège pas dans cette chambre. Le compter au
      dénominateur d'une cohésion qu'il ne pouvait pas voter serait précisément
      le défaut que #492 corrige. Cas impossible tant qu'aucun mandat n'est
      estampillé — un mandat à ``null`` est conservé par ``_mandats_electifs``.
    """
    if not any(m.get("categorie") == "mandat_electif" for m in mandats):
        return None
    return [
        (_parse_date(m.get("debut")), _parse_date(m.get("fin")))
        for m in _mandats_electifs(mandats, chambre)
    ]


def _is_eligible_at(intervals: Optional[list[tuple[Optional[date], Optional[date]]]], d: Optional[date]) -> bool:
    """Vérifie l'éligibilité à partir d'une date et d'intervalles déjà parsés."""
    if d is None or intervals is None:
        return True  # date/mandats inconnus → on ne peut pas exclure
    for debut, fin in intervals:
        if debut is not None and d < debut:
            continue
        if fin is not None and d > fin:
            continue
        return True  # le membre était en mandat à cette date
    return False


def _intervals_overlap(
    a_debut: Optional[date],
    a_fin: Optional[date],
    b_debut: Optional[date],
    b_fin: Optional[date],
) -> bool:
    """Teste le chevauchement de deux intervalles [a_debut, a_fin] et [b_debut, b_fin].

    Bornes ``None`` traitées comme non bornées, même sémantique que ``_is_eligible_at``.
    """
    if a_debut is not None and b_fin is not None and a_debut > b_fin:
        return False
    if a_fin is not None and b_debut is not None and a_fin < b_debut:
        return False
    return True


def _member_eligible_at(
    mandats: list[dict[str, Any]], vote_date: Optional[str], chambre: Optional[str] = None
) -> bool:
    """Détermine si un membre était en mandat (éligible à voter) à la date du scrutin.

    Un membre est éligible si au moins un de ses mandats électifs est actif à
    ``vote_date``. Si la date est absente ou non parseable, le membre est
    considéré éligible par défaut (approche conservatrice).

    Args:
        mandats: liste des mandats du profil pivot (champ ``mandats[]``).
        vote_date: date du scrutin au format "YYYY-MM-DD", ou None.
        chambre: chambre du groupe, voir ``_mandats_electifs`` (#492).

    Returns:
        True si le membre est éligible pour ce scrutin.
    """
    return _is_eligible_at(
        _member_eligibility_intervals(mandats, chambre), _parse_date(vote_date)
    )


# ---------------------------------------------------------------------------
# Construction de l'entrée membre
# ---------------------------------------------------------------------------

def _derive_membre_entry(
    profil: dict[str, Any],
    chambre: Optional[str] = None,
    appartenance: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Dérive une entrée ``membres[]`` du profil de groupe à partir d'un profil pivot.

    Les dates viennent du **mandat de groupe politique** (`typeOrgane == "GP"`)
    de la législature de la fiche, tel que `an_roster.deriver_membres_organes`
    le rend : organes successifs recollés, mandats de transit écartés (#526).
    Elles sont passées par ``appartenance`` (`{"debut", "fin"}`), jamais
    recalculées ici — la fiche et le roster doivent lire la même chose.

    Ce que ce champ **n'est plus** (#653) : le début du premier mandat électif.
    C'était l'approximation d'origine, correcte tant qu'un profil ne portait
    qu'un mandat — le plus récent. #647 a reconstruit la carrière complète (613
    périodes nouvelles sur 393 profils) et l'approximation est devenue fausse
    dans l'autre sens : Vincent Rolland, membre du groupe LR de la XVIe depuis
    le 2022-06-29, était publié « depuis 2002-06-19 ». Avant #647 la date était
    trop récente, après trop ancienne ; dans les deux cas elle ne mesurait pas
    ce que son nom annonce.

    Sans ``appartenance`` — aucun roster fourni, ou membre absent de celui-ci —
    les deux dates sont ``None`` et ``actif`` est ``False`` : **appartenance non
    établie**, jamais un repli sur le mandat électif, qui remettrait la date
    fausse en place sous un nom exact (AGENTS.md §2 règle 5). L'appelant compte
    ces membres et le publie.

    ``chambre`` n'entre plus dans le calcul des dates (le mandat GP est par
    construction celui de la chambre du groupe) ; il reste dans la signature
    parce qu'il est la clé de lecture de tous les autres agrégats de ce module
    et qu'un paramètre retiré d'une signature publique casse ses appelants.
    Le défaut qu'il corrigeait (#492 : la date d'un bicaméral remontant à
    l'autre chambre) s'éteint avec la source de la date.

    Args:
        profil: profil pivot v1.
        chambre: chambre du groupe, conservée pour la cohérence de signature.
        appartenance: `{"debut", "fin"}` lus sur le mandat GP de la
            législature de la fiche, ou ``None`` si aucun n'est identifiable.

    Returns:
        Dict conformant à la structure membres[] du schéma de groupe.
    """
    del chambre  # cf. docstring : plus lue ici depuis #653.

    debut: Optional[str] = None
    fin: Optional[str] = None
    periodes: Optional[list[dict[str, Any]]] = None
    if appartenance is not None:
        debut = appartenance.get("debut")
        fin = appartenance.get("fin")
        brutes = appartenance.get("periodes")
        if isinstance(brutes, list) and brutes:
            periodes = [
                {"debut": p.get("debut"), "fin": p.get("fin")}
                for p in brutes if isinstance(p, dict)
            ]

    membre: dict[str, Any] = {
        "membre_id": profil.get("id") or "",
        "nom": profil.get("nom") or "",
        "debut_dans_groupe": debut,
        "fin_dans_groupe": fin,
        # `present_a_la_date_de_reference` est posé par `_stamper_presences`, une
        # fois la date de référence connue : elle se dérive des dates de TOUS
        # les membres, donc aucune entrée ne peut la calculer seule (#653).
    }
    # #809 — la clé n'apparaît QUE si la source l'a donnée. L'écrire à `null`
    # dirait « aucune période connue » sur un membre dont on connaît les
    # bornes ; l'omettre dit « ce roster ne les portait pas », ce qui est le
    # fait (§2 règle 5).
    if periodes:
        membre["periodes"] = periodes
    return membre


def _appartenance_couvre(membre: dict[str, Any], date_reference: Optional[str]) -> bool:
    """Le membre appartenait-il au groupe à `date_reference` ? (#653)

    `debut_dans_groupe` à `None` rend **False** : l'appartenance n'est pas
    établie, et « pas établie » ne se compte pas comme « présent ». Une fin à
    `None` est une appartenance encore ouverte, donc couvrante — c'est la même
    convention que `_is_eligible_at` pour une borne absente, mais elle n'est
    appliquée qu'à la borne haute, jamais aux deux : un membre sans aucune date
    serait sinon présent à toutes.

    La borne de fin est **inclusive**. Un mandat de groupe qui se termine le
    jour de la clôture de la législature couvre ce jour : l'exclure viderait la
    fiche de ses 452 membres d'un coup, sur une convention d'intervalle.

    ## #809 — les périodes priment sur l'enveloppe

    Depuis #809, un membre porte `periodes[]`, et c'est **là** que la question
    se pose : l'enveloppe recouvrait les interruptions, si bien qu'un ministre
    absent 571 jours de son groupe était compté présent dans ce trou.

    Le compteur n'était pourtant faux **sur aucune fiche** — vérifié sur les 18
    groupes, 0 membre mal compté. Mais par coïncidence de dates : les dates de
    référence ne tombaient dans aucun des trous. Un défaut qui ne se voit pas
    parce que les dates s'y prêtent est exactement ce que #653 corrigeait un
    cran plus haut, et il ne se corrige pas en espérant que ça continue.

    L'enveloppe reste le repli, pour les fiches publiées avant ce lot : elles
    ne portent pas `periodes[]`, et exiger la clé ferait sortir des compteurs à
    zéro sur des données qui n'ont pas changé.
    """
    if not date_reference or not membre.get("debut_dans_groupe"):
        return False
    periodes = membre.get("periodes")
    if isinstance(periodes, list) and periodes:
        return any(
            p.get("debut") is not None
            and p["debut"] <= date_reference
            and (p.get("fin") is None or p["fin"] >= date_reference)
            for p in periodes
            if isinstance(p, dict)
        )
    if membre["debut_dans_groupe"] > date_reference:
        return False
    fin = membre.get("fin_dans_groupe")
    return fin is None or fin >= date_reference


def _deriver_date_reference(
    membres: list[dict[str, Any]], genere_le: Optional[str]
) -> Optional[dict[str, Any]]:
    """La date à laquelle tous les comptes de la fiche se rapportent (#653).

    Dérivée, jamais devinée, et selon un seul critère — l'état des
    appartenances publiées :

    - **toutes refermées** → la fiche décrit une législature close, et la date
      est la **plus tardive des fins** (`2024-06-09` pour la XVIe). C'est
      `periode.fin`, calculée sur la même liste.
    - **au moins une ouverte** → la législature court encore, et la date est
      celle de la génération : c'est le seul instant où « qui siège » a un sens.

    Aucune appartenance connue du tout rend la date de génération elle aussi,
    et tous les compteurs sortent à 0 — l'avertissement d'appartenance non
    établie dit déjà pourquoi. Rendre `None` serait publier des compteurs que
    rien ne date, ce que ce lot existe pour supprimer.
    """
    datees = [m for m in membres if m.get("debut_dans_groupe")]
    fins = [m.get("fin_dans_groupe") for m in datees]
    if datees and all(f is not None for f in fins):
        return {
            "date": max(fins),
            "origine": ORIGINE_DATE_REFERENCE_CLOTURE,
        }
    return {
        "date": (genere_le or "")[:10] or None,
        "origine": ORIGINE_DATE_REFERENCE_GENERATION,
    }


def _stamper_presences(
    membres: list[dict[str, Any]], date_reference: Optional[str]
) -> None:
    """Pose `present_a_la_date_de_reference` sur chaque entrée, en place.

    En place et non par reconstruction : l'ordre des clés d'une entrée
    `membres[]` est celui du fichier publié, et le champ doit rester le dernier,
    là où `actif` était.
    """
    for membre in membres:
        membre["present_a_la_date_de_reference"] = _appartenance_couvre(
            membre, date_reference
        )


# ---------------------------------------------------------------------------
# Amplitude d'effectif sur la période de la fiche (#702)
# ---------------------------------------------------------------------------

#: Motifs de non-publication de `effectif.min_historique`/`max_historique`.
#: Ils ne sont pas publiés dans la fiche — ils nomment l'avertissement lecteur
#: qui l'est. Un `null` sans motif dit « on n'a pas calculé » ; un `null` avec
#: son motif dit ce que la donnée ne permet pas d'établir (AGENTS.md §2 règle 5).
MOTIF_AMPLITUDE_FENETRE_NON_BORNEE = "fenetre_non_bornee"
MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE = "appartenance_non_etablie"


def _fenetre_de_la_fiche(
    periode_debut: Optional[str],
    periode_fin: Optional[str],
    date_reference: Optional[str],
) -> Optional[tuple[str, str]]:
    """La fenêtre sur laquelle l'effectif est balayé : `[debut, fin]`, incluse.

    C'est **la période de la fiche, jamais au-delà** : `periode.debut` →
    `periode.fin`. Quand la période est encore ouverte (`periode.fin` à `None`,
    au moins une appartenance sans fin), la borne haute est
    `date_reference.date` — la date de génération, seul instant où « qui siège »
    a un sens sur une législature qui court (#653). Le lecteur peut donc
    reconstituer la fenêtre depuis la fiche : `periode.fin` sinon
    `date_reference.date`.

    Rend `None` dès qu'une borne manque — une fenêtre non bornée couvrirait
    toutes les dates, ce qui est exactement l'inverse de la règle de
    `_appartenance_couvre` sur une borne absente. C'est le cas des 2 fiches
    `groupe-Senat-*` gelées (#516) : période ouverte et pas de `date_reference`.
    """
    if not periode_debut:
        return None
    fin = periode_fin or date_reference
    if not fin or fin < periode_debut:
        return None
    return (periode_debut, fin)


def _dates_de_reevaluation(
    membres: list[dict[str, Any]], fenetre: tuple[str, str]
) -> list[str]:
    """Les dates auxquelles l'effectif peut changer, dans la fenêtre.

    L'effectif est une fonction en escalier du temps : il **monte** le jour
    d'un `debut_dans_groupe`, et **descend le lendemain** d'un
    `fin_dans_groupe` — la borne de fin est inclusive (`_appartenance_couvre`),
    donc un membre dont l'appartenance s'achève le 20 est encore compté ce
    jour-là et ne l'est plus le 21.

    Balayer ces dates-là suffit : tout palier de la fonction commence à l'une
    d'elles, et `periode.debut` ouvre le premier. Une date hors fenêtre est
    écartée — la fiche ne décrit pas ce qui se passe après sa période.
    """
    debut, fin = fenetre
    dates: set[str] = {debut}
    for membre in membres:
        d = membre.get("debut_dans_groupe")
        if d and debut <= d <= fin:
            dates.add(d)
        f = _parse_date(membre.get("fin_dans_groupe"))
        if f is not None:
            lendemain = str(f + timedelta(days=1))
            if debut <= lendemain <= fin:
                dates.add(lendemain)
    return sorted(dates)


def _effectif_sur_la_periode(
    membres: list[dict[str, Any]],
    periode_debut: Optional[str],
    periode_fin: Optional[str],
    date_reference: Optional[str],
) -> tuple[Optional[dict[str, Any]], Optional[dict[str, Any]], Optional[str]]:
    """Minimum et maximum d'effectif sur la période de la fiche (#702).

    Un groupe parlementaire n'a pas un effectif, il en a une trajectoire :
    `a_la_date_de_reference` est exact et daté (#653), mais c'est un
    instantané présenté pour décrire deux ans. Cette fonction rend les deux
    bornes de la trajectoire, **chacune avec la date où elle est atteinte** :
    un minimum sans sa date est un nombre sans fait.

    La règle, en trois points :

    1. **Qui est présent à une date** est décidé par `_appartenance_couvre`, la
       même fonction que `present_a_la_date_de_reference` — jamais une seconde
       implémentation de la même règle. Une **borne de début absente rend
       l'appartenance ouverte à aucune date**, jamais à toutes (#653) : une
       donnée manquante ne peut pas couvrir tout l'axe du temps
       (AGENTS.md §2 règle 5).
    2. **Les dates évaluées** sont celles où l'effectif peut changer
       (`_dates_de_reevaluation`), dans la **fenêtre de la fiche**
       (`_fenetre_de_la_fiche`), jamais au-delà.
    3. **Une entrée sans `debut_dans_groupe` interdit la publication**, seuil
       **0**. Ce membre n'est comptable à aucune date : le minimum et le
       maximum obtenus sans lui sont des **bornes inférieures**, et une borne
       inférieure publiée sous le nom « minimum » est un chiffre faux. `null`
       est une réponse, pas un chiffre faux. Mesuré au 01/09/2026 : 0 entrée
       sans date sur les 452 des 5 fiches AN, 14 sur 15 et 4 sur 5 sur les 2
       fiches Sénat gelées (#516) — la règle sépare exactement les deux
       populations.

    Ce que ce calcul **ne peut pas** établir : `membres[]` ne porte qu'un
    intervalle par membre, `mandat_debut`/`mandat_fin` recollés par
    `an_roster._fusionner_periodes` (#526). Un membre parti puis revenu est
    publié comme présent en continu, et son absence n'apparaît dans aucune
    borne. Le calcul lit ce que la fiche publie — le corriger demanderait de
    changer le contrat du roster, pas cette fonction.

    Args:
        membres: entrées `membres[]` déjà dérivées (dates d'appartenance).
        periode_debut: `periode.debut` de la fiche.
        periode_fin: `periode.fin` de la fiche (`None` si encore ouverte).
        date_reference: `date_reference.date`, borne haute de repli.

    Returns:
        `(min_historique, max_historique, motif)` — les deux bornes sous la
        forme `{"valeur": int, "date": "YYYY-MM-DD"}`, ou `(None, None, motif)`
        avec le motif de non-publication.
    """
    # Une fiche sans aucune entrée n'a pas de fenêtre non plus (`periode.debut`
    # se dérive des mêmes dates) ; c'est le motif de fenêtre qui est rendu, dire
    # « 0 des 0 entrées ne sont datées » n'apprendrait rien.
    if not membres:
        return None, None, MOTIF_AMPLITUDE_FENETRE_NON_BORNEE
    # L'ordre compte : quand les deux motifs sont vrais, c'est le nombre
    # d'entrées non datées qui apprend quelque chose au lecteur, pas la borne
    # manquante qui en découle.
    if any(not m.get("debut_dans_groupe") for m in membres):
        return None, None, MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE

    fenetre = _fenetre_de_la_fiche(periode_debut, periode_fin, date_reference)
    if fenetre is None:
        return None, None, MOTIF_AMPLITUDE_FENETRE_NON_BORNEE

    # Ordre croissant : à valeur égale, la PREMIÈRE date où l'effectif atteint
    # la borne est retenue. Convention arbitraire mais fixe, et écrite : sans
    # elle, deux runs sur la même donnée pourraient dater différemment la même
    # valeur.
    serie = [
        (d, sum(1 for m in membres if _appartenance_couvre(m, d)))
        for d in _dates_de_reevaluation(membres, fenetre)
    ]
    valeur_min = min(n for _, n in serie)
    valeur_max = max(n for _, n in serie)
    date_min = next(d for d, n in serie if n == valeur_min)
    date_max = next(d for d, n in serie if n == valeur_max)
    return (
        {"valeur": valeur_min, "date": date_min},
        {"valeur": valeur_max, "date": date_max},
        None,
    )


def appartenances_depuis_roster(
    roster: Iterable[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """`slug → {debut, fin}` : les dates d'appartenance au groupe, par membre.

    Le roster est la seule source de ces dates (#653). Il les porte sous
    `mandat_debut`/`mandat_fin` — le nom du contrat de
    `group_roster.fetch_full_roster` —, elles sont renommées ici une fois pour
    toutes, à la frontière, plutôt qu'à chaque lecture.

    Un membre sans slug n'entre pas dans la table : il n'a pas de profil pivot,
    donc pas d'entrée `membres[]` non plus. `an_roster` le compte et le nomme
    déjà (`membres_sans_slug`, #526).
    """
    return {
        membre["slug"]: {
            "debut": membre.get("mandat_debut"),
            "fin": membre.get("mandat_fin"),
            # #809 — le détail que l'enveloppe recouvrait. Absent d'un roster
            # d'avant ce lot : l'appelant retombe alors sur les deux bornes.
            "periodes": membre.get("mandat_periodes"),
        }
        for membre in roster
        if membre.get("slug")
    }


# ---------------------------------------------------------------------------
# Index de votes par membre
# ---------------------------------------------------------------------------

def _votes_de_legislature(
    profil: dict[str, Any], legislature: Optional[str]
) -> list[dict[str, Any]]:
    """Votes d'un profil restreints à la législature du groupe.

    Depuis #403, un profil individuel porte les votes de **toutes** les
    législatures où l'élu a siégé (14 à 17), alors qu'un profil de groupe en
    couvre exactement une. Sans ce filtre, la cohésion d'un groupe de la 16e
    agrégerait les scrutins de la 17e dès qu'un membre y siège encore — un
    scrutin serait attribué à un groupe qui n'existait pas au moment du vote.

    Depuis #432 la législature se lit dans `scrutin_id` (`an:16:4084`), et le
    filtre est **exact**. Il l'était mal avant : un vote sans `legislature`
    était conservé pour n'importe quelle législature de groupe
    (`v.get("legislature") or legislature`), ce qui était juste tant que tous
    les groupes étaient de la 16e — les 89 687 votes concernés en venaient tous
    — mais aurait fait absorber ces mêmes votes par un groupe de la 17e. Le
    repli n'est levé qu'ici, une fois la législature effectivement résolue sur
    les données : le lever plus tôt aurait retiré ces 89 687 votes de la
    cohésion de la 16e, ce qui aurait été une régression, pas une correction.

    Un vote sans `scrutin_id` (scrutin non résolu, `scrutin_non_resolu`) est
    **écarté** : il n'est rattachable à aucune législature. L'appelant en
    compte le nombre et le remonte en warning — écarté, jamais silencieux.

    Un groupe sans législature (Sénat) ne filtre rien.
    """
    votes = profil.get("votes") or []
    if not legislature:
        return list(votes)
    retenus = []
    for v in votes:
        legislature_vote, _ = decomposer_id(v.get("scrutin_id"))
        if legislature_vote == str(legislature):
            retenus.append(v)
    return retenus


def _votes_non_resolus(profils: list[dict[str, Any]]) -> int:
    """Nombre de votes qu'aucun identifiant ne rattache à une législature.

    Zéro sur les données mesurées au 19/08/2026. Compté quand même, et remonté :
    c'est exactement le genre d'exclusion qui, muette, transformerait un
    dénominateur en donnée fausse (AGENTS.md §2.7)."""
    return sum(
        1
        for profil in profils
        for v in (profil.get("votes") or [])
        if not v.get("scrutin_id")
    )


def _build_vote_index(
    profil: dict[str, Any], legislature: Optional[str] = None
) -> dict[str, dict[str, Any]]:
    """Construit un index {scrutin_id → vote_dict} pour un profil individuel.

    Permet une recherche O(1) lors du calcul de cohésion. La clé est
    `scrutin_id` depuis #432 : elle porte déjà la législature, là où
    `numero_scrutin` seul faisait écraser le scrutin n° 1000 de la 16e par celui
    de la 17e — deux textes sans rapport. `legislature` reste appliqué en amont
    pour ne retenir que les scrutins du groupe.
    """
    index: dict[str, dict[str, Any]] = {}
    for v in _votes_de_legislature(profil, legislature):
        scrutin_id = v.get("scrutin_id")
        if scrutin_id:
            index[str(scrutin_id)] = v
    return index


# ---------------------------------------------------------------------------
# Calcul de cohésion
# ---------------------------------------------------------------------------

def _compute_cohesion_votes(
    profils: list[dict[str, Any]],
    seuil_quorum: float = 0.5,
    legislature: Optional[str] = None,
    scrutins_index: Optional[ScrutinsIndex] = None,
    chambre: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Calcule la cohésion de vote pour chaque scrutin couvert par les membres.

    Algorithme :
      1. Collecte tous les scrutins distincts (par numero_scrutin) rencontrés
         dans les profils membres.
      2. Pour chaque scrutin, détermine les membres éligibles (en mandat à la
         date du scrutin).
      3. Comptabilise les positions : pour / contre / abstention / non_votant /
         excusé / absent (implicite = pas de vote trouvé pour ce scrutin).
      4. Calcule la position majoritaire sur les votes exprimés, les taux de
         participation et de cohérence.

    Args:
        profils: liste de profils pivot v1 des membres du groupe.
        seuil_quorum: seuil de taux_participation au-delà duquel quorum_atteint
                      est True (défaut : 0.5).
        legislature: législature du groupe (ex. "16"), qui restreint les
                     scrutins retenus — voir ``_votes_de_legislature``. None
                     (Sénat, ou groupe sans législature) ne filtre rien.
        scrutins_index: index partagé (#432). La `date` d'un scrutin n'est plus
                     dans le profil : elle est nécessaire à l'éligibilité des
                     membres, donc un scrutin absent de l'index est écarté du
                     calcul plutôt que compté sur une date inventée.
        chambre: chambre du groupe ("AN" | "Senat" | …). Restreint les mandats
                     électifs qui ouvrent la fenêtre d'éligibilité à ceux de
                     cette chambre — un dénominateur publié (§2.7) ne doit pas
                     être élargi par un mandat d'une autre chambre. Voir
                     ``_mandats_electifs`` (#492).

    Returns:
        Liste de dicts conformes à la structure cohesion_votes[], triée par date
        décroissante. Les entrées ne portent plus `date`/`texte`/`sort` : ces
        champs sont ceux du scrutin, ils vivent dans l'index (#432).
    """
    # --- 1. Collecte de tous les scrutins ---
    # Clé : scrutin_id → date du scrutin, lue dans l'index partagé. Un scrutin
    # inconnu de l'index n'est pas datable, donc ses membres ne sont pas
    # éligibles de façon vérifiable : il est écarté, et compté comme tel.
    scrutins: dict[str, Optional[str]] = {}
    scrutins_hors_index: set[str] = set()
    for profil in profils:
        for v in _votes_de_legislature(profil, legislature):
            scrutin_id = v.get("scrutin_id")
            if not scrutin_id or scrutin_id in scrutins or scrutin_id in scrutins_hors_index:
                continue
            scrutin = scrutins_index.get(scrutin_id) if scrutins_index is not None else None
            if scrutin is None:
                scrutins_hors_index.add(scrutin_id)
                continue
            scrutins[scrutin_id] = scrutin.get("date")

    if scrutins_hors_index:
        print(
            f"  [!] {len(scrutins_hors_index)} scrutin(s) référencés par les membres mais "
            f"absents de l'index partagé, écartés de la cohésion : "
            f"{sorted(scrutins_hors_index)[:5]}"
        )

    if not scrutins:
        return []

    # --- 2. Index de votes par membre + intervalles d'éligibilité pré-analysés ---
    # Précalculés une seule fois (au lieu de reparser les dates de mandat à chaque
    # scrutin) : un groupe de N membres et M scrutins ferait sinon O(M x N) reparsing
    # de dates au lieu de O(N) ici + une comparaison de dates déjà parsées par scrutin.
    vote_indexes = [_build_vote_index(p, legislature) for p in profils]
    eligibility_intervals = [
        _member_eligibility_intervals(p.get("mandats") or [], chambre) for p in profils
    ]

    # --- 3. Calcul par scrutin ---
    _EXPRESSED = ("pour", "contre", "abstention")

    cohesion: list[dict[str, Any]] = []
    for scrutin_id, vote_date in scrutins.items():
        parsed_vote_date = _parse_date(vote_date)

        compteurs: dict[str, int] = {
            "pour": 0, "contre": 0, "abstention": 0,
            "non_votant": 0, "absent": 0, "excuse": 0,
        }
        n_eligible = 0

        for v_index, intervals in zip(vote_indexes, eligibility_intervals):
            if not _is_eligible_at(intervals, parsed_vote_date):
                continue
            n_eligible += 1

            vote = v_index.get(scrutin_id)
            if vote is None:
                compteurs["absent"] += 1
            else:
                pos = vote.get("position") or "absent"
                compteurs[pos] = compteurs.get(pos, 0) + 1

        if n_eligible == 0:
            continue

        # Position majoritaire sur les votes exprimés (pour/contre/abstention).
        # Note : en cas d'égalité stricte entre deux positions (ex. 10 pour /
        # 10 contre), max() retourne conventionnellement la première position
        # de _EXPRESSED à égalité de score, soit l'ordre "pour" > "contre" >
        # "abstention". Ce choix arbitraire mais déterministe est documenté ici
        # plutôt que de renvoyer None sur égalité, ce qui casserait la lecture
        # simple du taux de cohérence pour ces scrutins (rares en pratique).
        votes_exprimes = sum(compteurs[p] for p in _EXPRESSED)
        if votes_exprimes == 0:
            position_majoritaire = None
        else:
            position_majoritaire = max(_EXPRESSED, key=lambda p: compteurs[p])

        # Taux de participation (éligibles ayant une trace de vote)
        n_absent = compteurs["absent"] + compteurs["excuse"]
        taux_participation = (n_eligible - n_absent) / n_eligible

        # Taux de cohérence
        if position_majoritaire is not None:
            alignes = compteurs[position_majoritaire]
            taux_coherence: Optional[float] = alignes / n_eligible
            voted = n_eligible - n_absent
            taux_coherence_hors_absents: Optional[float] = (
                alignes / voted if voted > 0 else None
            )
        else:
            taux_coherence = None
            taux_coherence_hors_absents = None

        cohesion.append({
            # `date`, `texte` et `sort` ont migré vers l'index partagé (#432) :
            # ce sont des champs du SCRUTIN, recopiés jusque-là dans chacun des
            # 5 groupes qui l'ont voté (12 546 entrées pour 4 104 scrutins,
            # 3,15 Mo de méta répété ramenés à 1,04 Mo une seule fois).
            "scrutin_id": scrutin_id,
            "membres_eligibles": n_eligible,
            "position_majoritaire": position_majoritaire,
            "pour": compteurs["pour"],
            "contre": compteurs["contre"],
            "abstention": compteurs["abstention"],
            "non_votant": compteurs["non_votant"],
            "absents": compteurs["absent"],
            "excuses": compteurs["excuse"],
            "taux_participation": round(taux_participation, 4),
            "taux_coherence": (
                round(taux_coherence, 4) if taux_coherence is not None else None
            ),
            "taux_coherence_hors_absents": (
                round(taux_coherence_hors_absents, 4)
                if taux_coherence_hors_absents is not None
                else None
            ),
            "quorum_atteint": taux_participation >= seuil_quorum,
        })

    # Tri par date décroissante (scrutins récents en premier). La date n'étant
    # plus dans l'entrée, elle est relue dans l'index — l'ordre publié reste
    # celui qu'attendent les consommateurs.
    cohesion.sort(key=lambda x: scrutins.get(x["scrutin_id"]) or "", reverse=True)
    return cohesion


# ---------------------------------------------------------------------------
# Agrégation des tags thématiques
# ---------------------------------------------------------------------------

@dataclass
class TagsAgreges:
    """L'empreinte thématique d'une fiche, et ce que son calcul a écarté."""

    #: Une entrée par étiquette : `tag`, `nb_membres_porteurs`, `poids_relatif`.
    tags: list[dict[str, Any]]
    #: D'où viennent les étiquettes retenues — voir `aggregate_tags_thematiques`.
    source: Optional[str]
    #: Interventions écartées parce que leur identifiant porte une AUTRE
    #: législature que celle de la fiche. Comptées, jamais tues : une exclusion
    #: muette transforme un dénominateur en donnée fausse (§2 règle 7).
    hors_periode: int = 0
    #: Interventions dont l'identifiant ne porte aucune législature lisible.
    #: **Conservées** — rien ne prouve qu'elles soient hors période, et les
    #: écarter ferait passer une ignorance pour un fait (§2 règle 5).
    sans_legislature: int = 0


def _tags_du_membre(
    profil: dict[str, Any], legislature: Optional[str]
) -> tuple[list[str], Optional[str], int, int]:
    """Les étiquettes d'UN membre, restreintes à la législature de la fiche.

    ## Pourquoi la liste publiée ne suffit pas, et pourquoi rien n'est dupliqué

    #825 constatait que `tags_thematiques` est « une liste de chaînes, sans
    provenance : il n'y a rien à filtrer ». C'est vrai de la **liste**, et faux
    du **champ** : depuis #710, `tags_thematiques` est DÉRIVÉ des
    `interventions[]` par une fabrique unique, `deriver_tags_thematiques`. Il
    suffit donc de la rappeler sur les interventions retenues — la provenance
    n'a pas à être portée, elle est encore là au moment du calcul.

    Vérifié le 10/09/2026 sur les **1 035 profils publiés** : la liste publiée
    est exactement ce que la fabrique rend depuis les interventions de ces
    mêmes profils, **0 écart**. Le repli documenté (`theme_officiel`, puis
    `mots_cles`) ne se rouvre pas non plus : il est DANS la fabrique.

    ## Le filtre

    La législature se lit sur l'identifiant (`syceron_CRSANR5L16S…`,
    `question_QANR5L15QE…`), donnée structurelle écrite par l'Assemblée, jamais
    déduite d'une date — même règle que les votes depuis #403, que les
    amendements depuis #821. Mesuré sur les 40 premiers membres de `REN-16` :
    **26 %** seulement de leurs interventions relèvent de la XVIe.

    Une intervention du Parlement européen n'est PAS triée à part, et ce n'est
    pas un oubli : mesuré sur le corpus publié, **0 des 5 329** entrées
    européennes porte un `theme_officiel` ou des `mots_cles`. Elles n'apportent
    aucune étiquette, donc elles n'en retirent aucune ; elles sont comptées
    parmi les entrées sans législature, ce qu'elles sont pour l'Assemblée.
    """
    if not legislature:
        return list(profil.get("tags_thematiques") or []), "tags_thematiques", 0, 0

    retenues: list[dict[str, Any]] = []
    hors_periode = 0
    sans_legislature = 0
    for interv in (profil.get("interventions") or []):
        if not isinstance(interv, dict):
            continue
        leg = legislature_de_intervention(interv.get("intervention_id"))
        if leg is None:
            sans_legislature += 1
        elif leg != str(legislature):
            hors_periode += 1
            continue
        retenues.append(interv)
    return (
        deriver_tags_thematiques(retenues),
        "interventions_de_la_legislature",
        hors_periode,
        sans_legislature,
    )


def aggregate_tags_thematiques(
    profils: list[dict[str, Any]],
    legislature: Optional[str] = None,
) -> TagsAgreges:
    """Agrège les tags thématiques de tous les profils membres.

    **Avec `legislature`** — le cas d'une fiche de groupe — les étiquettes de
    chaque membre sont recalculées sur ses seules interventions de cette
    législature (`_tags_du_membre`), et `source` vaut
    `"interventions_de_la_legislature"`.

    **Sans** — le cas d'une fiche de parti, qui ne couvre aucune législature en
    particulier — le comportement d'origine tient : `tags_thematiques` de
    chaque profil, et à défaut ses interventions, d'abord par `theme_officiel`
    puis par `mots_cles`. Le filtre ne s'arme que si l'appelant nomme une
    législature (#821, même règle).

    Ce repli-là est **mort sur le corpus publié** et n'est gardé que parce que
    rien ne prouve qu'il le reste : mesuré le 10/09/2026, **0 des 1 035
    profils** publiés a un `tags_thematiques` vide et des interventions
    thématisées.

    Args:
        profils: liste de profils pivot v1.
        legislature: législature de la fiche (ex. "16"), ou None.

    Returns:
        Un `TagsAgreges` : les étiquettes triées par `nb_membres_porteurs`
        décroissant, leur `source`, et les deux comptes d'interventions que le
        filtre a écartées ou retenues sans preuve.
    """
    n = len(profils)
    if n == 0:
        return TagsAgreges([], None)

    # #1042 — on compte par CLÉ (pluriel simple), on publie une FORME observée.
    # Sans ça, deux membres qui écrivent « motion » et « motions de censure »
    # font deux lignes du même sujet sur la fiche.
    porteurs_par_cle: dict[str, int] = {}
    formes_par_cle: dict[str, Counter] = defaultdict(Counter)
    sources_used: set[str] = set()
    hors_periode = 0
    sans_legislature = 0

    for profil in profils:
        tags, source, n_hors, n_sans = _tags_du_membre(profil, legislature)
        hors_periode += n_hors
        sans_legislature += n_sans
        if tags:
            sources_used.add(source)
        elif not legislature:
            # Fallback : thèmes officiels Syceron en priorité, mots-clés scraping sinon
            kw_set: set[str] = set()
            theme_set: set[str] = set()
            for interv in (profil.get("interventions") or []):
                theme = interv.get("theme_officiel")
                if theme and isinstance(theme, str):
                    cleaned = theme.strip().lower()
                    if cleaned:
                        theme_set.add(cleaned)
                else:
                    for kw in (interv.get("mots_cles") or []):
                        cleaned = kw.strip().lower() if isinstance(kw, str) else ""
                        if cleaned:
                            kw_set.add(cleaned)
            if theme_set:
                tags = list(theme_set)
                sources_used.add("theme_officiel")
            elif kw_set:
                tags = list(kw_set)
                sources_used.add("mots_cles_interventions")

        # Un tag compte une seule fois par membre (même s'il est répété)
        cles_du_membre: set[str] = set()
        for tag in set(tags):
            if tag:
                cle = cle_tag_thematique(tag)
                formes_par_cle[cle][tag] += 1
                cles_du_membre.add(cle)
        for cle in cles_du_membre:
            porteurs_par_cle[cle] = porteurs_par_cle.get(cle, 0) + 1

    if not porteurs_par_cle:
        return TagsAgreges([], None, hors_periode, sans_legislature)

    tag_source: Optional[str] = None
    if len(sources_used) == 1:
        (tag_source,) = sources_used
    elif len(sources_used) > 1:
        tag_source = "mixed"

    result = sorted(
        [
            {
                "tag": forme_publiee(formes_par_cle[cle]),
                "nb_membres_porteurs": count,
                "poids_relatif": round(count / n, 4),
            }
            for cle, count in porteurs_par_cle.items()
        ],
        key=lambda x: (-x["nb_membres_porteurs"], x["tag"]),
    )
    return TagsAgreges(result, tag_source, hors_periode, sans_legislature)


# ---------------------------------------------------------------------------
# Agrégation catégorielle des mandats (mandats_agreges)
#
# Périmètre v1 volontairement restreint : mandat_electif (définit déjà
# l'appartenance au groupe — l'agréger serait circulaire), groupe_politique
# (redondant avec groupe_id/periode dans un profil déjà scopé à un seul
# groupe), fonction_gouvernementale (plus sensible éditorialement, recoupe
# mandats[].suspendu_pour_fonction_gouvernementale — AGENTS.md §5) et autre
# (filet de secours quasi jamais peuplé) sont exclus. Voir la conception
# validée dans #349/#361.
# ---------------------------------------------------------------------------

# Catégories de mandats agrégées au niveau groupe. Élargi par #382/#385 aux
# 4 catégories introduites par la nouvelle taxonomie : ce sont des instances
# de travail collectives auxquelles plusieurs membres d'un même groupe
# appartiennent, donc exactement ce que l'agrégation cherche à montrer.
#
# Restent volontairement hors agrégat, comme avant :
# - `mandat_electif`, `groupe_politique` : structurels, identiques pour tous
#   les membres d'un groupe — agréger n'apprendrait rien.
# - `fonction_gouvernementale` : individuelle par nature (et désormais
#   enrichie du portefeuille précis, #383) ; sa place est sur la fiche
#   individuelle, pas dans un agrégat de groupe.
# - `autre` : fourre-tout (Bureau, Conférence des Présidents) sans unité
#   éditoriale — agréger des natures hétérogènes sous une même étiquette
#   irait contre AGENTS.md §2.8.
MANDATS_AGREGES_CATEGORIES: tuple[str, ...] = (
    "commission",
    "commission_enquete",
    "mission_information",
    "groupe_etudes",
    "delegation",
    "groupe_amitie",
    "extra_parlementaire",
)


def _normalize_fonction_mandat(fonction: Any) -> str:
    """Normalise un libellé de fonction pour le comptage `par_fonction` (#379).

    Depuis #369, les mandats proviennent de deux référentiels aux conventions
    typographiques différentes — NosDéputés écrit `"membre"`, l'Assemblée
    nationale `"Membre"` — et le comptage brut éclatait le même rôle en deux
    entrées (mesuré : `'membre': 521` **et** `'Membre': 312`), donnant à lire
    deux rôles distincts là où il n'y en a qu'un.

    Normalise la casse et les espaces superflus, **sans** toucher aux accents
    ni au genre : `président` et `présidente` (comme `co-rapporteur`/
    `co-rapporteure`) sont des libellés institutionnels réellement distincts,
    les fusionner effacerait une information portée par la source. Un
    dépliage accent-insensible n'apporterait rien ici et dégraderait
    l'affichage.

    Une fonction absente devient `"non_precise"` (inchangé) : distinguer
    « rôle non renseigné par la source » de « simple membre » relève de la
    règle « donnée manquante ≠ valeur par défaut » (AGENTS.md §2.5).
    """
    if not isinstance(fonction, str):
        return "non_precise"
    normalisee = " ".join(fonction.split()).lower()
    return normalisee or "non_precise"


def _select_mandat_entree_unique(mandats: list[dict[str, Any]]) -> dict[str, Any]:
    """Sélectionne une entrée unique parmi des mandats en doublon pour un même
    membre et un même (categorie, label) (ex. réélu·e à la même commission sur
    deux périodes) : priorité à l'entrée ``actif=true``, sinon la plus récente
    par date de fin. Même esprit que le tie-break de ``position_majoritaire``
    en cas d'égalité (voir ``_compute_cohesion_votes``).
    """
    actifs = [m for m in mandats if m.get("actif")]
    if actifs:
        return actifs[0]
    avec_fin = [m for m in mandats if _parse_date(m.get("fin")) is not None]
    if avec_fin:
        return max(avec_fin, key=lambda m: _parse_date(m.get("fin")))
    return mandats[0]


def _mandat_couvre(mandat: dict[str, Any], reference: Optional[date]) -> bool:
    """Ce mandat était-il ouvert à la date de référence de la fiche ? (#653)

    Un mandat **sans début** rend `False` : « ouvert à une date » se démontre,
    et `_intervals_overlap` traite une borne absente comme non bornée, ce qui
    ferait couvrir toutes les dates à un mandat qu'aucune ne situe (AGENTS.md
    §2 règle 5). Mesuré sur `AN:LFI-16` et `AN:LR-16` : 0 des 7 249 entrées
    retenues est dans ce cas, donc le garde-fou ne retire rien aujourd'hui — il
    empêche seulement une donnée manquante de se compter comme un siège.
    """
    if reference is None or not mandat.get("debut"):
        return False
    return _intervals_overlap(
        _parse_date(mandat.get("debut")), _parse_date(mandat.get("fin")),
        reference, reference,
    )


def _select_mandat_a_la_date(
    mandats: list[dict[str, Any]], reference: Optional[date]
) -> dict[str, Any]:
    """L'entrée à publier pour un `(categorie, label)` en doublon (#653).

    Priorité à un mandat **ouvert à la date de référence**, puis, à défaut, la
    règle inchangée de `_select_mandat_entree_unique` (actif d'abord, sinon la
    fin la plus récente).

    Ce préalable n'est pas cosmétique, il est ce qui rend le compteur juste.
    `_select_mandat_entree_unique` privilégie le mandat `actif`, donc — pour
    un⋅e réélu⋅e — sa commission de la législature **suivante**, qui ne couvre
    pas la clôture de celle que la fiche décrit. Mesuré sur `AN:LFI-16`, 1 000
    des 2 384 entrées ayant plusieurs candidats : sans ce préalable, la
    commission des affaires sociales tombe de 9 à 3 membres siégeant, celle des
    lois de 8 à 1. Le mandat publié serait de surcroît celui d'une autre
    législature que le drapeau qui l'accompagne.
    """
    couvrants = [m for m in mandats if _mandat_couvre(m, reference)]
    return _select_mandat_entree_unique(couvrants or mandats)


def _aggregate_mandats(
    profils: list[dict[str, Any]],
    membres: list[dict[str, Any]],
    chambre: Optional[str] = None,
    date_reference: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Agrège les mandats catégoriels (``MANDATS_AGREGES_CATEGORIES``) de tous
    les membres du groupe, par ``(categorie, label)``.

    Éligibilité temporelle : un mandat catégoriel (commission/groupe_amitie/
    extra_parlementaire) compte pour le groupe si sa période chevauche au
    moins un intervalle de mandat électif du membre (``_intervals_overlap``).
    Si le membre n'a aucun mandat électif renseigné, il est considéré éligible
    par défaut (même approche conservatrice que ``_is_eligible_at``).

    Args:
        profils: liste de profils pivot v1 des membres du groupe.
        membres: sortie de ``[_derive_membre_entry(p) for p in profils]``
                 (même ordre que ``profils``), après ``_stamper_presences`` :
                 c'est ``present_a_la_date_de_reference`` qui est lu.
        date_reference: la date de la fiche (``date_reference.date``), à
                 laquelle l'ouverture de chaque mandat est évaluée. ``None``
                 ne compte personne comme siégeant — un mandat qu'aucune date
                 ne situe n'est pas un mandat ouvert.

    Deux grandeurs distinctes, jamais un seul nombre (#656) :

    - ``nb_membres_a_la_date_de_reference`` — **qui y siège** : membres dont le
      mandat est ouvert *et* qui appartiennent au groupe **à la date de
      référence de la fiche** (#653). C'est la réponse à « ce groupe travaille
      sur quoi ». Le champ s'appelait ``nb_membres_actifs`` et se lisait
      « aujourd'hui » : sur une fiche de législature close — les 7 publiées le
      sont — cette lecture ne compte personne, puisque tous les mandats de
      groupe de la XVIe se referment le 2024-06-09.
    - ``nb_membres_cumul_historique`` — **qui y est passé** : membres distincts
      ayant occupé ce mandat au moins une fois, si brièvement que ce soit.
      Cumul, jamais un effectif.

    L'écart n'est pas du bruit, et il est concentré sur ``commission`` : 1 165
    des 2 708 adhésions de commission publiées par les 7 fiches (43 %) durent
    une journée ou moins, contre 0 à 5 % dans les six autres catégories. La
    cause est institutionnelle : un⋅e député⋅e
    n'appartient qu'à **une** commission permanente à la fois, si bien que
    l'AN modélise tout passage temporaire dans une autre commission comme la
    fin d'un mandat et le début d'un autre. Mesuré sur les 452 acteurs AN des
    7 fiches (10 562 mandats ``COMPER`` du référentiel AMO30, dont 3 389 de
    durée ≤ 1 jour, soit 32 %) : 93,2 % des paires de mandats ``COMPER``
    consécutifs d'un même acteur sont **contiguës** (fin + 1 jour = début du
    suivant), et 440 des 452 acteurs n'ont jamais deux commissions permanentes
    ouvertes le même jour. Rien dans AMO30 ne distingue le passage du siège :
    ni ``nominPrincipale`` (à 1 dans les deux cas), ni
    ``infosQualite.codeQualite`` (``Membre`` dans les deux cas). Seule la durée
    le dit — d'où deux compteurs, et non un filtre.

    Les adhésions courtes ne sont donc **jamais retirées** du décompte : les
    écarter en silence recréerait le problème dans l'autre sens. Leur durée
    reste lisible entrée par entrée dans ``membres[].debut``/``fin``. Aucun
    taux de rotation n'en est dérivé : ce serait un indice comparable entre
    groupes (AGENTS.md §2.1).

    ``effectif_reference`` est le dénominateur des deux compteurs
    (``len(profils)``, la couverture disponible du groupe) : il est publié
    plutôt que pré-divisé, pour que le lecteur voie « 5 / 76 » et non un
    pourcentage seul (AGENTS.md §2.7). Il remplace l'ancien ``poids_relatif``,
    qui valait ``nb_membres / len(membres)`` et ne disait pas de quelle des
    deux grandeurs il était le poids.

    Returns:
        Liste de dicts conformes à la structure ``mandats_agreges`` du schéma
        de groupe, triée par ``nb_membres_a_la_date_de_reference`` décroissant,
        puis ``nb_membres_cumul_historique`` décroissant, puis ``(categorie,
        label)`` croissant.
    """
    n = len(profils)
    if n == 0:
        return []

    membre_present_par_id = {
        m["membre_id"]: m.get("present_a_la_date_de_reference", False) for m in membres
    }
    ref = _parse_date(date_reference)

    buckets: dict[tuple[str, str], list[dict[str, Any]]] = {}

    for profil in profils:
        membre_id = profil.get("id") or ""
        nom = profil.get("nom") or ""
        mandats = profil.get("mandats") or []
        eligibility_intervals = _member_eligibility_intervals(mandats, chambre)

        # Regroupe les mandats catégoriels éligibles de CE membre par (categorie, label)
        candidats_par_cle: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for m in mandats:
            categorie = m.get("categorie")
            if categorie not in MANDATS_AGREGES_CATEGORIES:
                continue
            label = m.get("label")
            if not label:
                continue

            m_debut = _parse_date(m.get("debut"))
            m_fin = _parse_date(m.get("fin"))
            if eligibility_intervals is not None and not any(
                _intervals_overlap(m_debut, m_fin, e_debut, e_fin)
                for e_debut, e_fin in eligibility_intervals
            ):
                continue

            candidats_par_cle.setdefault((categorie, label), []).append(m)

        for cle, candidats in candidats_par_cle.items():
            chosen = _select_mandat_a_la_date(candidats, ref)
            # « Ouvert à la date de référence », et non « `actif` » (#653) :
            # `actif` est posé à la collecte et se lit « au jour du run ». Sur
            # une fiche de législature close il désigne les mandats de la
            # législature SUIVANTE — le compteur de tête de chaque carte de
            # commission comptait donc les commissions d'aujourd'hui des
            # membres d'hier.
            entree_actif = _mandat_couvre(chosen, ref) and bool(
                membre_present_par_id.get(membre_id)
            )
            buckets.setdefault(cle, []).append({
                "membre_id": membre_id,
                "nom": nom,
                "fonction": chosen.get("fonction"),
                "debut": chosen.get("debut"),
                "fin": chosen.get("fin"),
                "actif": entree_actif,
            })

    result: list[dict[str, Any]] = []
    for (categorie, label), entries in buckets.items():
        par_fonction: dict[str, int] = {}
        for e in entries:
            fonction = _normalize_fonction_mandat(e.get("fonction"))
            par_fonction[fonction] = par_fonction.get(fonction, 0) + 1

        result.append({
            "categorie": categorie,
            "label": label,
            "nb_membres_a_la_date_de_reference": sum(1 for e in entries if e["actif"]),
            "nb_membres_cumul_historique": len(entries),
            "effectif_reference": n,
            "par_fonction": par_fonction,
            "membres": entries,
        })

    # Tri : « qui y siège » d'abord (#656). Trier par le cumul faisait remonter
    # une commission que 44 membres ont traversée un jour au-dessus d'une
    # commission où 9 siègent réellement — le cumul ne départage plus qu'à
    # égalité de membres siégeant.
    result.sort(key=lambda x: (
        -x["nb_membres_a_la_date_de_reference"],
        -x["nb_membres_cumul_historique"],
        x["categorie"],
        x["label"],
    ))
    return result


# ---------------------------------------------------------------------------
# Agrégation des amendements (comparateur du taux d'adoption individuel)
# ---------------------------------------------------------------------------

def _normalize_sort_amendement(sort: Any) -> str:
    """Normalise un statut d'amendement en minuscules sans accent, pour comparaison.

    Les sources primaires peuvent fournir des libellés accentués ("adopté")
    ou non ("adopte") ; cette normalisation évite de dupliquer les catégories.
    """
    if not isinstance(sort, str):
        return ""
    s = unicodedata.normalize("NFKD", sort.strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


_SORTS_ADOPTES = frozenset({"adopte"})
_SORTS_IRRECEVABLES = frozenset({"irrecevable"})
_SORTS_REJETES = frozenset({"rejete"})
_SORTS_RETIRES_OU_TOMBES = frozenset({"retire", "tombe", "non_soutenu", "non soutenu"})

#: Le compteur qu'incrémente un `sort` normalisé. Deux bandes de plus que les
#: quatre historiques, et elles ne disent pas la même chose (#643) :
#:
#:   `nb_sort_non_renseigne`  le `sort` est **absent**. 44 243 des 132 960
#:                            amendements distincts d'`AN:LFI`, soit 33,3 %
#:                            (mesuré le 31/08/2026 sur `f50a9439`). Les taire
#:                            publierait un tiers d'absences comme des zéros —
#:                            AGENTS.md §2 règle 5 ;
#:   `nb_sort_non_reconnu`    le `sort` est **présent** mais hors nomenclature.
#:                            Structurellement à 0 : les 484 132 amendements de
#:                            l'index ne portent que sept libellés, tous
#:                            rangés ci-dessus. Compteur **sous surveillance**
#:                            (AGENTS.md §3d) et non donnée : le jour où l'AN
#:                            en ajoute un, le ranger sous « non renseigné »
#:                            publierait une valeur présente comme une absence,
#:                            l'erreur exactement symétrique.
#:
#: Avec elles, les six bandes somment à `nb_amendements` — un invariant
#: vérifiable, et ce qui rend une barre empilée honnête.
BANDE_SORT_ABSENT = "nb_sort_non_renseigne"
BANDE_SORT_INCONNU = "nb_sort_non_reconnu"

_BANDE_PAR_SORT: dict[str, str] = {
    **{s: "nb_adoptes" for s in _SORTS_ADOPTES},
    **{s: "nb_irrecevables" for s in _SORTS_IRRECEVABLES},
    **{s: "nb_rejetes" for s in _SORTS_REJETES},
    **{s: "nb_retires_ou_tombes" for s in _SORTS_RETIRES_OU_TOMBES},
}

#: Les six bandes, dans l'ordre publié.
BANDES_DE_SORT: tuple[str, ...] = (
    "nb_adoptes", "nb_rejetes", "nb_irrecevables", "nb_retires_ou_tombes",
    BANDE_SORT_ABSENT, BANDE_SORT_INCONNU,
)


def _bande_de_sort(sort: Any) -> str:
    """Le compteur qu'un `sort` d'amendement incrémente. Jamais aucun."""
    norm = _normalize_sort_amendement(sort)
    if not norm:
        return BANDE_SORT_ABSENT
    return _BANDE_PAR_SORT.get(norm, BANDE_SORT_INCONNU)


def _seau_de_type_deposant(type_deposant: Any) -> str:
    """Le seau de `par_type_deposant` d'un `type_deposant` collecté.

    Un type absent ou hors nomenclature va dans `inconnu`, jamais sous
    `depute` par défaut : ce serait ranger une donnée manquante dans le seul
    seau qui sert de comparateur (AGENTS.md §6).
    """
    return type_deposant if type_deposant in AMENDEMENTS_TYPES_DEPOSANT else "inconnu"


def _stats_amendements_vides() -> dict[str, Any]:
    """`make_empty_amendements_stats()` plus les deux bandes de #643.

    Composée depuis la fabrique du schéma plutôt que réécrite : les quatre
    compteurs historiques n'ont qu'une définition. `taux_adoption` est remis en
    dernier — il n'est pas un compteur mais leur quotient.
    """
    stats = make_empty_amendements_stats()
    taux = stats.pop("taux_adoption")
    stats[BANDE_SORT_ABSENT] = 0
    stats[BANDE_SORT_INCONNU] = 0
    stats["taux_adoption"] = taux
    return stats


#: Les couples (bande, seau) publiés, partagés. 24 au plus : les deux membres
#: viennent d'ensembles fermés, seul le tuple serait neuf à chaque amendement.
_COUPLES: dict[tuple[str, str], tuple[str, str]] = {}


def _couple(bande: str, seau: str) -> tuple[str, str]:
    couple = (bande, seau)
    return _COUPLES.setdefault(couple, couple)


class CumulAmendementsDistincts:
    """Les amendements **distincts** d'une fiche, dédupliqués sur `amendement_id` (#643).

    ## Pourquoi un état partagé, et pas un compteur de plus

    `ContributionAmendements` est additive : agréger membre par membre puis
    sommer rend les mêmes compteurs que parcourir la liste concaténée. La
    déduplication ne l'est pas — deux membres qui cosignent le même amendement
    doivent le compter **une** fois —, elle demande donc un état commun aux
    membres d'une même fiche. Cet objet ne porte que ça.

    C'est ce qui manquait à `_aggregate_amendements`, qui faisait
    `nb_amendements += 1` par entrée de profil, donc une fois par signataire :
    92,2 % des entrées du corpus sont des cosignatures, et `AN:LFI` publiait
    « 2 600 765 amendements déposés » pour 76 députés (#643).

    ## Ce qu'il retient d'un amendement, et pourquoi si peu

    Une bande de sort et un seau de type de déposant, l'un et l'autre pris dans
    un ensemble fermé : les deux chaînes sont partagées et le couple aussi,
    seule l'entrée de dictionnaire est neuve. La plus grosse fiche mesurée
    (`AN:LR`, 159 143 amendements distincts) tient dans ~25 Mo, quand ses
    928 832 signatures — ou un ensemble d'identifiants **par membre** — en
    coûteraient la mémoire que #635 vient tout juste de rendre.

    ## Une entrée sans identifiant n'est pas dédoublonnable

    Elle est comptée **telle quelle**, une fois par signataire, dans
    `sans_identifiant` : la fusionner avec une autre demanderait une clé, et on
    n'en invente pas (AGENTS.md §2 règle 5). Le compte est publié
    (`nb_sans_identifiant`) et remonté en `meta.warnings` dès qu'il n'est pas
    nul, faute de quoi `nb_amendements` mélangerait en silence des amendements
    dédoublonnés et des signatures. Zéro cas sur les 7 fiches publiées au
    31/08/2026 ; c'est en revanche la forme normale des amendements du
    Parlement européen, que ParlTrack livre sans `uid` AN, et celle de toute
    entrée d'avant #431 restée autoportante.
    """

    __slots__ = ("par_id", "sans_identifiant")

    def __init__(self) -> None:
        self.par_id: dict[str, tuple[str, str]] = {}
        self.sans_identifiant: dict[tuple[str, str], int] = {}

    def retenir(self, amendement_id: Optional[str], sort: Any, type_deposant: Any) -> None:
        """Retient un amendement vu chez un membre.

        Le dernier lu l'emporte sur la clé : deux copies d'un même amendement
        portent les mêmes champs partagés depuis #431 (`sort` et
        `type_deposant` vivent dans l'index, pas dans le profil). Le seul cas
        où elles pourraient diverger est celui d'entrées d'avant #431 restées
        autoportantes chez deux signataires — et il n'y a alors pas de clé pour
        les rapprocher, donc pas d'écrasement possible.
        """
        couple = _couple(_bande_de_sort(sort), _seau_de_type_deposant(type_deposant))
        if amendement_id is None:
            self.sans_identifiant[couple] = self.sans_identifiant.get(couple, 0) + 1
            return
        self.par_id[amendement_id] = couple

    def fusionner(self, autre: "CumulAmendementsDistincts") -> None:
        """Absorbe un autre cumul. Idempotent sur les identifiants, additif sur
        ce qui n'en a pas — les deux propriétés que la déduplication demande."""
        self.par_id.update(autre.par_id)
        for couple, n in autre.sans_identifiant.items():
            self.sans_identifiant[couple] = self.sans_identifiant.get(couple, 0) + n

    @property
    def nb_sans_identifiant(self) -> int:
        return sum(self.sans_identifiant.values())

    def __len__(self) -> int:
        return len(self.par_id) + self.nb_sans_identifiant

    def __eq__(self, autre: object) -> bool:
        if not isinstance(autre, CumulAmendementsDistincts):
            return NotImplemented
        return (self.par_id == autre.par_id
                and self.sans_identifiant == autre.sans_identifiant)

    def compter(self) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        """`(total, par_type_deposant)` sur les amendements distincts.

        `taux_adoption` n'est pas posé ici : c'est un quotient, et il n'a de
        sens qu'une fois tous les cumuls fusionnés.
        """
        total = _stats_amendements_vides()
        par_type = {t: _stats_amendements_vides() for t in AMENDEMENTS_TYPES_DEPOSANT}
        occurrences: list[tuple[tuple[str, str], int]] = [
            (couple, 1) for couple in self.par_id.values()
        ]
        occurrences += list(self.sans_identifiant.items())
        for (bande, seau), n in occurrences:
            for stats in (total, par_type[seau]):
                stats["nb_amendements"] += n
                stats[bande] += n
        return total, par_type


@dataclass(frozen=True)
class ContributionAmendements:
    """Ce qu'un `amendements[]` de membre laisse derrière lui, relâché (#635).

    Exactement ce que `_aggregate_amendements` en tire. Deux natures, et c'est
    #643 qui les a séparées :

    - des **compteurs de signatures**, additifs : agréger membre par membre
      puis sommer donne les mêmes valeurs que parcourir la liste concaténée ;
    - le **cumul des amendements distincts**, qui ne l'est pas — un amendement
      cosigné par trois membres ne se compte qu'une fois. Il est porté par
      référence, et le chargeur en partage **un seul** entre tous les membres
      d'une fiche : c'est ce qui empêche la déduplication de racheter la
      mémoire que #635 vient de rendre.

    Le cardinal est conservé pour que `len()` rende la même valeur que sur la
    liste elle-même, comme `nombre_d_entrees` accepte les deux formes dans
    l'audit de #628.
    """

    nb: int
    total: dict[str, Any]
    par_type: dict[str, dict[str, Any]]
    non_resolus: int
    distincts: CumulAmendementsDistincts
    #: #821 — **SIGNATURES** écartées parce que portant sur un amendement déposé
    #: sous une AUTRE législature que celle de la fiche. Une par entrée
    #: d'`amendements[]`, donc une par signataire : 657 996 sur `LR-16` pour
    #: 126 997 amendements distincts. Comptées, jamais tues — une exclusion
    #: muette transforme un dénominateur en donnée fausse (§2 règle 7) — et
    #: nommées « signatures », jamais « amendements » (§6, #643).
    hors_periode: int = 0
    #: Signatures dont l'identifiant d'amendement ne porte pas de législature.
    #: **Conservées** — rien ne prouve qu'elles soient hors période, et les
    #: écarter ferait passer une ignorance pour un fait (§2 règle 5).
    sans_legislature: int = 0

    def __len__(self) -> int:
        return self.nb


#: Les compteurs de signatures que `ContributionAmendements` additionne.
#: `taux_adoption` n'en est **pas** : c'est un quotient, il ne se somme pas —
#: et depuis #643 il ne se calcule plus sur les signatures du tout.
_COMPTEURS_AMENDEMENTS: tuple[str, ...] = ("nb_amendements", *BANDES_DE_SORT)


def contribution_amendements(
    amendements: Any,
    amendements_index: Optional[AmendementsIndex] = None,
    distincts: Optional[CumulAmendementsDistincts] = None,
    legislature: Optional[str] = None,
) -> ContributionAmendements:
    """Réduit l'`amendements[]` d'UN membre à ce que l'agrégat en tire.

    C'est le seul endroit qui lit une entrée d'amendement, et il ne la lit
    qu'une fois : appelé au chargement (#635), il permet de relâcher les
    entrées au lieu de les garder pour les 76 membres du plus gros groupe
    publié — 253,5 Mo sur disque, 0,9 à 1,1 Gio de mémoire selon l'exécution.

    `distincts` est le cumul **de la fiche** (#643). En passer un partagé entre
    tous ses membres est ce qui garde la déduplication au prix des amendements
    distincts (159 143 au plus haut) plutôt qu'à celui des signatures
    (2 647 601). Ne rien passer reste **correct** — `_aggregate_amendements`
    fusionne les cumuls qu'il trouve —, seulement plus coûteux : c'est le
    chemin des tests et d'un appelant qui charge un profil isolé.

    Repli de lecture transitoire : une entrée d'avant #431 porte encore ses
    champs, une entrée non résolue les porte sous `amendement_non_resolu`. Les
    deux sont lues sur place — sans quoi tout l'agrégat tomberait à zéro entre
    le déploiement du code et la régénération des données.
    """
    total = _stats_amendements_vides()
    par_type = {t: _stats_amendements_vides() for t in AMENDEMENTS_TYPES_DEPOSANT}
    cumul = distincts if distincts is not None else CumulAmendementsDistincts()
    non_resolus = 0
    hors_periode = 0
    sans_legislature = 0

    for entree, amendement in joindre_amendements(amendements, amendements_index):
        # #821 — UN AMENDEMENT DÉPOSÉ AILLEURS N'EST PAS L'ACTIVITÉ DE CE
        # GROUPE. Le filtre est celui que #403 a posé sur les votes, transposé
        # mot pour mot : « un scrutin serait attribué à un groupe qui n'existait
        # pas au moment du vote ». Mesuré avant correctif sur `LR-16` : 159 274
        # amendements publiés dont **32 277 seulement** déposés sous la XVIe —
        # 20 501 venaient de la XVIIe, c'est-à-dire d'après la dissolution du
        # 9 juin 2024, sous un groupe qui n'existait plus.
        #
        # La législature se lit sur l'identifiant (`AMANR5L16…`), donnée
        # structurelle écrite par l'Assemblée, jamais déduite d'une date.
        # Un identifiant qui ne la porte pas n'est PAS écarté : rien ne prouve
        # qu'il soit hors période, et l'écarter ferait passer une ignorance pour
        # un fait (§2 règle 5). Il est compté, et le compte est déclaré.
        if legislature:
            leg = legislature_de_id(entree.get("amendement_id"))
            if leg is None:
                sans_legislature += 1
            elif leg != str(legislature):
                hors_periode += 1
                continue
        if amendement is None:
            amendement = entree.get("amendement_non_resolu")
        if amendement is None and "sort" in entree:
            # Entrée d'avant #431, encore autoportante.
            amendement = entree
        if not isinstance(amendement, dict):
            non_resolus += 1
            continue
        sort = amendement.get("sort")
        type_deposant = amendement.get("type_deposant")
        cumul.retenir(entree.get("amendement_id"), sort, type_deposant)
        bande = _bande_de_sort(sort)
        bucket = par_type[_seau_de_type_deposant(type_deposant)]
        for stats in (total, bucket):
            stats["nb_amendements"] += 1
            stats[bande] += 1

    nb = len(amendements) if isinstance(amendements, list) else 0
    return ContributionAmendements(
        nb, total, par_type, non_resolus, cumul,
        hors_periode=hors_periode, sans_legislature=sans_legislature,
    )


def _aggregate_amendements(
    profils: list[dict[str, Any]],
    amendements_index: Optional[AmendementsIndex] = None,
) -> tuple[dict[str, Any], int]:
    """Agrège les amendements de tous les profils membres pour servir de comparateur.

    ## Deux grandeurs, deux noms (#643)

    `amendements_agreges` compte des **amendements distincts** : un amendement
    cosigné par trois membres du groupe en est **un**. Il en comptait un par
    signataire, ce qui publiait « 2 600 765 amendements déposés » pour les 76
    députés d'`AN:LFI` — et le facteur allait de × 5,0 à × 31,7 selon la
    fiche, si bien que les chiffres publiés n'étaient même pas comparables
    entre eux.

    Les signatures ne sont pas perdues pour autant : elles décrivent une
    activité réelle du groupe, et vivent sous `signatures`, à côté. Ce qui
    était faux, c'était de les nommer « amendements ».

    `taux_adoption` se calcule sur les **distincts**, jamais sur les
    signatures : un taux dont le numérateur et le dénominateur sont gonflés par
    des nombres de cosignataires différents ne décrit rien, et il bougeait dans
    les deux sens (`AN:SOC` 7,24 % → 14,54 %, `AN:LFI` 5,01 % → 2,99 %,
    mesuré le 31/08/2026 sur le seau `depute`). C'est ce que la §2 règle 7
    protège.

    ## Le total ne compare rien

    Le total (tous types de déposants confondus) sert de vue d'ensemble mais ne
    doit PAS être utilisé comme comparateur direct du taux d'adoption d'un⋅e
    élu⋅e : les amendements gouvernementaux ou du rapporteur sont adoptés quasi
    systématiquement par construction (ils portent le texte), ce qui gonflerait
    artificiellement la référence. Comparer un⋅e élu⋅e à
    ``par_type_deposant["depute"]``, seule catégorie de même nature que les
    amendements qu'un⋅e député⋅e dépose en son nom propre (AGENTS.md §6).

    ## Comment la donnée arrive ici

    Depuis #431, `sort` et `type_deposant` vivent dans l'index partagé et non
    dans le profil : l'agrégation est une **jointure**, faite entrée par entrée
    via `joindre_amendements`, un générateur. Ne jamais matérialiser la liste
    jointe : ce serait reconstruire la forme plate que la normalisation vient de
    supprimer, avec le facteur ~21 et l'OOM de #377.

    Depuis #635 l'agrégation est la **somme de contributions par membre**, et le
    profil chargé peut porter directement la sienne (`ContributionAmendements`)
    au lieu de ses entrées. Les deux formes sont acceptées : les tests
    nourrissent la mesure avec de vraies listes, le chargeur avec leur
    réduction. Les compteurs de signatures sont additifs, donc identiques ; les
    distincts sont fusionnés, et un cumul partagé n'est absorbé qu'une fois.

    Args:
        profils: liste de profils pivot v1 des membres du groupe.
        amendements_index: index partagé (#431). Sans lui, seuls les
            enregistrements encore portés par le profil sont exploitables.
            Ignoré pour un profil qui porte déjà sa contribution : elle a été
            calculée au chargement, avec l'index d'alors.

    Returns:
        `(amendements_agreges, nb_non_resolus)`. `nb_non_resolus` compte les
        entrées qu'aucune source ne renseigne : elles sont **exclues** des
        décomptes, et ce nombre est remonté en `meta.warnings` — une exclusion
        muette transformerait un dénominateur en donnée fausse (AGENTS.md §2.7).
    """
    signatures = _stats_amendements_vides()
    signatures_par_type = {t: _stats_amendements_vides() for t in AMENDEMENTS_TYPES_DEPOSANT}
    cumul = CumulAmendementsDistincts()
    # Cumuls déjà absorbés : le chargeur en partage **un** entre tous les
    # membres d'une fiche, et le fusionner une fois par membre serait sans
    # effet mais trompeur à lire.
    #
    # Le dictionnaire **retient l'objet**, pas seulement son `id()` : un profil
    # qui porte encore ses entrées voit sa contribution calculée ici même, et
    # relâchée à l'itération suivante — CPython réattribue alors l'adresse, et
    # un `set` d'entiers déclarerait « déjà absorbé » un cumul jamais vu. Mesuré
    # : trois membres portant chacun un amendement sans identifiant en
    # publiaient deux.
    cumuls_absorbes: dict[int, CumulAmendementsDistincts] = {}
    non_resolus = 0
    hors_periode = 0
    sans_legislature = 0

    for profil in profils:
        amendements = profil.get("amendements")
        contribution = (
            amendements if isinstance(amendements, ContributionAmendements)
            else contribution_amendements(amendements, amendements_index)
        )
        non_resolus += contribution.non_resolus
        hors_periode += contribution.hors_periode
        sans_legislature += contribution.sans_legislature
        for compteur in _COMPTEURS_AMENDEMENTS:
            signatures[compteur] += contribution.total[compteur]
            for type_deposant, stats in signatures_par_type.items():
                stats[compteur] += contribution.par_type[type_deposant][compteur]
        if id(contribution.distincts) not in cumuls_absorbes:
            cumuls_absorbes[id(contribution.distincts)] = contribution.distincts
            cumul.fusionner(contribution.distincts)

    total, par_type = cumul.compter()
    for stats in (total, *par_type.values()):
        stats["taux_adoption"] = (
            round(stats["nb_adoptes"] / stats["nb_amendements"], 4)
            if stats["nb_amendements"] else None
        )

    total["nb_sans_identifiant"] = cumul.nb_sans_identifiant
    total["par_type_deposant"] = par_type
    # Les signatures ne portent que leur compte. Un `nb_adoptes` de signatures
    # inviterait exactement le taux que #643 retire : le sort est une propriété
    # de l'amendement, pas de la signature.
    total["signatures"] = {
        "nb_signatures": signatures["nb_amendements"],
        "par_type_deposant": {
            type_deposant: {"nb_signatures": stats["nb_amendements"]}
            for type_deposant, stats in signatures_par_type.items()
        },
    }
    # #821 — CE QUI A ÉTÉ ÉCARTÉ SE PUBLIE. Sans ces deux comptes, la fiche
    # afficherait un chiffre plus petit qu'avant sans que rien ne dise pourquoi,
    # et une exclusion muette transforme un dénominateur en donnée fausse
    # (§2 règle 7).
    total["nb_signatures_hors_periode_ecartees"] = hors_periode
    total["nb_signatures_sans_legislature_retenues"] = sans_legislature
    return total, non_resolus


# ---------------------------------------------------------------------------
# Contrôle interne : écart de cohésion/participation individuel vs groupe
#
# Donnée de contrôle interne uniquement — volontairement absente du schéma
# de groupe public (schema_groupe.py). Ne pas inclure le résultat de
# `compute_ecarts_cohesion_internes` dans un profil de groupe publié tant que
# ce comparateur n'a pas été validé comme sortie publique.
# ---------------------------------------------------------------------------

def compute_ecarts_cohesion_internes(
    profils: list[dict[str, Any]],
    cohesion_votes: list[dict[str, Any]],
    legislature: Optional[str] = None,
    scrutins_index: Optional[ScrutinsIndex] = None,
    chambre: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Calcule, pour chaque membre, son écart de participation/cohérence vs le groupe.

    Le ratio individuel est calculé sur exactement les mêmes scrutins que ceux
    couverts par ``cohesion_votes`` (donc sur les mêmes membres éligibles par
    scrutin), puis comparé à la moyenne du groupe sur ces mêmes scrutins.

    Args:
        profils: liste de profils pivot v1 des membres du groupe.
        cohesion_votes: sortie de ``_compute_cohesion_votes`` pour ce même groupe.
        legislature: législature du groupe, à passer telle qu'utilisée pour
                     ``_compute_cohesion_votes`` — les numéros de scrutin ne
                     sont comparables qu'à législature égale (#403).

    Returns:
        Liste de dicts {membre_id, nom, nb_scrutins_eligibles,
        taux_participation_individuel, taux_coherence_individuel,
        ecart_participation_vs_groupe, ecart_coherence_vs_groupe}.
        Destinée à un usage de contrôle interne, pas à publication.
    """
    if not cohesion_votes:
        return []

    # Moyennes du groupe sur les mêmes scrutins (celles déjà calculées par scrutin).
    participations = [c["taux_participation"] for c in cohesion_votes if c.get("taux_participation") is not None]
    coherences = [c["taux_coherence"] for c in cohesion_votes if c.get("taux_coherence") is not None]
    moyenne_participation_groupe = sum(participations) / len(participations) if participations else None
    moyenne_coherence_groupe = sum(coherences) / len(coherences) if coherences else None

    coh_by_scrutin = {c["scrutin_id"]: c for c in cohesion_votes}

    resultats: list[dict[str, Any]] = []
    for profil in profils:
        mandats = profil.get("mandats") or []
        v_index = _build_vote_index(profil, legislature)

        n_eligible = 0
        n_present = 0
        n_alignes = 0

        for scrutin_id, c in coh_by_scrutin.items():
            # La date du scrutin vient de l'index partagé depuis #432 : sans
            # elle, l'éligibilité n'est pas vérifiable, et compter le membre
            # comme éligible « par défaut » fausserait le dénominateur.
            scrutin = scrutins_index.get(scrutin_id) if scrutins_index is not None else None
            if scrutin is None:
                continue
            if not _member_eligible_at(mandats, scrutin.get("date"), chambre):
                continue
            n_eligible += 1

            vote = v_index.get(scrutin_id)
            if vote is None:
                continue
            pos = vote.get("position")
            if pos in ("pour", "contre", "abstention"):
                n_present += 1
            if pos is not None and pos == c.get("position_majoritaire"):
                n_alignes += 1

        taux_participation_individuel = n_present / n_eligible if n_eligible else None
        taux_coherence_individuel = n_alignes / n_eligible if n_eligible else None

        resultats.append({
            "membre_id": profil.get("id") or "",
            "nom": profil.get("nom") or "",
            "nb_scrutins_eligibles": n_eligible,
            "taux_participation_individuel": (
                round(taux_participation_individuel, 4)
                if taux_participation_individuel is not None else None
            ),
            "taux_coherence_individuel": (
                round(taux_coherence_individuel, 4)
                if taux_coherence_individuel is not None else None
            ),
            "ecart_participation_vs_groupe": (
                round(taux_participation_individuel - moyenne_participation_groupe, 4)
                if taux_participation_individuel is not None and moyenne_participation_groupe is not None
                else None
            ),
            "ecart_coherence_vs_groupe": (
                round(taux_coherence_individuel - moyenne_coherence_groupe, 4)
                if taux_coherence_individuel is not None and moyenne_coherence_groupe is not None
                else None
            ),
        })

    return resultats


# ---------------------------------------------------------------------------
# Chargement et détection de format
# ---------------------------------------------------------------------------

def _is_pivot_v1(profil: dict[str, Any]) -> bool:
    """Retourne True si le profil est déjà au format pivot v1 (schema_version présent)."""
    return "schema_version" in profil and "id" in profil


#: Les blocs du profil d'un membre que la fiche de groupe lit, et rien d'autre —
#: relevés dans le code de `build_groupe_profile` et de
#: `compute_ecarts_cohesion_internes`, pas dans l'énoncé (#635) :
#:
#:   `id`, `nom`         `_derive_membre_entry`, `_aggregate_mandats`,
#:                       `meta.profils_sources`, le rapport interne
#:   `mandats`           **parcouru** — éligibilité (§2 règle 7), mandats agrégés
#:   `votes`             **parcouru** — cohésion, dénominateurs publiés
#:   `interventions`     **parcouru** — repli de `tags_thematiques`
#:   `amendements`       **parcouru**, mais réduit à sa contribution (voir plus bas)
#:   `tags_thematiques`  `aggregate_tags_thematiques`
#:   `sources`           recopiées **telles quelles** dans la fiche publiée, donc
#:                       jamais projetées par clés : ce sont des données publiées
#:
#: Ce que personne n'ouvre — et ce que CLAUDE.md §3 annonçait déjà pour
#: `identite` : `identite`, `identifiants`, `couverture`, `meta`,
#: `textes_portes`, `chambres`, `chambre`, `parti`, `groupe`. `schema_version`
#: est lu **avant** la projection, par `_is_pivot_v1`, et personne après.
BLOCS_LUS_MEMBRE: tuple[str, ...] = (
    "id", "nom", "tags_thematiques", "sources",
    "mandats", "votes", "interventions", "amendements",
)

#: Les clés que la fiche de groupe lit dans les entrées de chaque liste
#: parcourue. Une liste réellement parcourue n'est jamais réduite à son
#: cardinal — mais ses entrées n'ont pas à porter ce que personne n'ouvre :
#: `interventions[].texte` pèse 9,8 des 22,2 Mo du bloc sur le corpus committé
#: du 30/08/2026, et aucune ligne d'ici ne le lit.
CLES_LUES_PAR_ENTREE: dict[str, tuple[str, ...]] = {
    "mandats": ("categorie", "chambre", "debut", "fin", "actif", "label", "fonction"),
    "votes": ("scrutin_id", "position"),
    # `intervention_id` depuis #825 : c'est lui qui porte la législature
    # (`syceron_CRSANR5L16S…`), et sans elle l'empreinte thématique d'une
    # fiche compte la carrière entière de ses membres.
    "interventions": ("intervention_id", "theme_officiel", "mots_cles"),
}


def projeter_profil_membre(
    document: dict[str, Any],
    amendements_index: Optional[AmendementsIndex] = None,
    distincts: Optional[CumulAmendementsDistincts] = None,
    legislature: Optional[str] = None,
) -> dict[str, Any]:
    """Le profil d'un membre réduit à ce que la fiche de groupe en lit.

    `amendements[]` est **réduit** et non projeté : c'est le bloc qui pèse
    577,3 des 651,5 Mo du corpus, et 6,09 millions de mappings à deux clés ne
    tiennent dans aucune projection par clés (184 octets de `dict` par entrée).
    Ce que l'agrégat en tire — des compteurs additifs — est calculé ici, une
    fois, puis les entrées meurent.

    `amendements_index` doit être celui qui sera passé à
    `build_groupe_profile` : c'est lui qui résout `sort` et `type_deposant`.
    Ne rien passer des deux côtés est également cohérent ; passer l'un et pas
    l'autre ne l'est pas.

    `distincts` (#643) est le cumul **de la fiche**, partagé par tous ses
    membres : c'est lui qui rend la déduplication possible une fois les entrées
    relâchées, et le partager la fait tenir dans les amendements distincts
    plutôt que dans les signatures. L'omettre reste correct — chaque membre
    reçoit alors le sien et `_aggregate_amendements` les fusionne —, mais
    ramène le coût mémoire à ce que #635 venait d'écarter.
    """
    projection: dict[str, Any] = {}
    for bloc in BLOCS_LUS_MEMBRE:
        if bloc not in document:
            continue
        valeur = document[bloc]
        cles = CLES_LUES_PAR_ENTREE.get(bloc)
        if cles is not None and isinstance(valeur, list):
            projection[bloc] = [
                {c: e[c] for c in cles if c in e} if isinstance(e, dict) else e
                for e in valeur
            ]
        elif bloc == "amendements":
            projection[bloc] = contribution_amendements(
                valeur, amendements_index, distincts, legislature
            )
        else:
            projection[bloc] = valeur
    return projection


def load_profil_from_file(
    path: Path,
    amendements_index: Optional[AmendementsIndex] = None,
    projeter: bool = True,
    distincts: Optional[CumulAmendementsDistincts] = None,
    legislature: Optional[str] = None,
) -> dict[str, Any]:
    """Charge un profil depuis un fichier JSON et le normalise en pivot v1 si nécessaire.

    Les profils au format brut (produits par candidate_profile.py) sont
    convertis automatiquement via normalize_profil.

    **Le document entier ne survit pas à cet appel (#635)** : il est projeté sur
    `BLOCS_LUS_MEMBRE`, ses entrées réduites aux clés lues, son `amendements[]`
    réduit à sa contribution — puis relâché. Garder les documents entiers
    coûtait 0,9 à 1,1 Gio pour la seule fiche du plus gros groupe publié (LFI,
    76 profils, 253,5 Mo sur disque, facteur de gonflement mesuré × 3,7 à
    × 4,5 selon l'exécution), et il y a sept fiches. `projeter=False` rend le document entier, pour un appelant
    qui a besoin d'autre chose que d'une fiche de groupe.

    Args:
        path: chemin vers le fichier JSON.
        amendements_index: index partagé (#431), voir `projeter_profil_membre`.
        projeter: réduire le document à ce que la fiche de groupe en lit.
        distincts: cumul des amendements distincts de la fiche (#643), voir
            `projeter_profil_membre`. Un seul pour tous les membres d'une même
            fiche, sans quoi rien ne dédoublonne entre eux à peu de frais.

    Returns:
        Profil pivot v1 (dict), projeté sauf demande contraire.

    Raises:
        FileNotFoundError: si le fichier n'existe pas.
        ValueError: si le fichier n'est pas un JSON valide ou si le format est inconnu.
    """
    with open(path, encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON invalide dans {path} : {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Attendu un dict JSON, reçu {type(data).__name__} dans {path}.")

    if _is_pivot_v1(data):
        profil = data
    elif "slug" in data:
        # Format brut de collecte (champ "slug" présent, pas de "schema_version")
        profil = normalize_profil(data)
    else:
        raise ValueError(
            f"Format non reconnu dans {path} : ni pivot v1 (schema_version + id) "
            "ni format brut de collecte (slug)."
        )

    return (
        projeter_profil_membre(profil, amendements_index, distincts, legislature)
        if projeter else profil
    )


# ---------------------------------------------------------------------------
# Fonction principale d'agrégation
# ---------------------------------------------------------------------------

def build_groupe_profile(
    groupe_id: str,
    groupe_sigle: str,
    groupe_nom: str,
    chambre: Optional[str],
    legislature: Optional[str],
    profils: list[dict[str, Any]],
    seuil_quorum: float = 0.5,
    licence_donnees: str = "",
    scrutins_index: Optional[ScrutinsIndex] = None,
    amendements_index: Optional[AmendementsIndex] = None,
    appartenances: Optional[dict[str, dict[str, Any]]] = None,
    position_politique: Optional[dict[str, Any]] = None,
    succede_a: Optional[list[dict[str, Any]]] = None,
    historique_noms: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Construit un profil de groupe à partir d'une liste de profils individuels pivot v1.

    Args:
        groupe_id: identifiant du groupe, ex. "AN:SOC".
        groupe_sigle: sigle court, ex. "SOC".
        groupe_nom: nom complet, ex. "Socialistes et apparentés".
        chambre: "AN" | "Senat" | "PE" | "mairie" | None.
        legislature: ex. "16" | None.
        profils: liste de profils pivot v1 des membres du groupe.
        seuil_quorum: seuil de taux de participation pour quorum_atteint (défaut : 0.5).
        licence_donnees: texte de licence à inscrire dans meta.
        scrutins_index: index partagé des scrutins (#432). Nécessaire au calcul
                    de cohésion : la date d'un scrutin, qui détermine quels
                    membres étaient éligibles, n'est plus dans les profils.
                    Absent, la cohésion est vide plutôt que fausse.
        amendements_index: index partagé des amendements (#431). Le `sort` et le
                    `type_deposant` d'un amendement n'étant plus dans les
                    profils, l'agrégat est une jointure : sans index, les seules
                    entrées exploitables sont celles qui portent encore leur
                    enregistrement, et les autres sont comptées puis remontées
                    en `meta.warnings` plutôt qu'ignorées en silence.
        appartenances: `slug → {debut, fin}` d'appartenance AU GROUPE, pour la
                    législature de la fiche (#653). Construit par
                    `appartenances_depuis_roster` sur le roster AMO30, seule
                    source de ces dates. Absent — ou membre absent de la table
                    —, `membres[].debut_dans_groupe` est publié `null` et le
                    nombre de membres concernés est remonté en
                    `meta.warnings` : le repli sur le mandat électif, qui
                    datait l'entrée dans le groupe au début de la carrière,
                    est ce que ce lot retire.
        position_politique: bloc `position_politique` déjà composé par
                    `groupes_config.position_politique_publiee` (#686) — la
                    qualification que l'Assemblée donne elle-même au groupe,
                    recopiée depuis la table committée. `None` = non renseignée
                    (le champ sort `null`), ce qui est le cas de toute fiche
                    hors Assemblée nationale : AMO30 ne qualifie que ses
                    propres organes. **Jamais calculée ici** : cette fonction
                    ne lit aucune archive, et déduire une posture des votes
                    agrégés serait le jugement que ce dépôt refuse de porter
                    (AGENTS.md §2 règle 1).
        succede_a: bloc `succede_a` déjà composé par
                    `groupes_config.succession_publiee` (#700) — le groupe de la
                    législature précédente dont celui-ci prend la suite. `None`
                    = pas de prédécesseur dans le périmètre du dépôt (les 5
                    fiches de la XVIe). **Jamais dérivé ici** : c'est une
                    relecture humaine committée, et aucun calcul sur les
                    membres ne la produirait — l'Assemblée ne chaîne pas ses
                    organes.

    Returns:
        Profil de groupe dict conforme au schéma de groupe v1.
    """
    warnings: list[str] = []
    # La date de génération est lue AVANT l'assemblage : c'est le repli de la
    # date de référence quand la législature court encore, et
    # `make_empty_profil_groupe` la pose plus bas, trop tard pour les comptes.
    genere_le = time.strftime("%Y-%m-%dT%H:%M:%S%z")

    # --- Membres ---
    # Les dates d'appartenance viennent du mandat GP de la législature de la
    # fiche (#653), jamais des mandats électifs du profil. Un membre que la
    # table ne couvre pas garde des dates `null` : il est compté et nommé
    # juste en dessous, pas daté par défaut (AGENTS.md §2 règle 5).
    membres = [
        _derive_membre_entry(
            p, chambre, (appartenances or {}).get(p.get("id") or "")
        )
        for p in profils
    ]
    sans_appartenance = [m["membre_id"] for m in membres if m["debut_dans_groupe"] is None]
    if sans_appartenance:
        if appartenances is None:
            warnings.append(avertissement(
                f"appartenance_au_groupe : aucun roster fourni à cette agrégation, donc "
                f"aucune date d'appartenance dérivable pour les {len(sans_appartenance)} "
                "membre(s) de la fiche. `debut_dans_groupe`/`fin_dans_groupe` sont publiés "
                "`null` et `present_a_la_date_de_reference` vaut `false` : appartenance non "
                "établie, jamais datée depuis le mandat électif — ce qui daterait l'entrée "
                "dans le groupe au début de la carrière (#653).",
                DESTINATAIRE_LECTEUR,
            ))
        else:
            warnings.append(avertissement(
                f"appartenance_au_groupe : {len(sans_appartenance)} membre(s) sans mandat de "
                "groupe politique identifiable dans le roster de cette législature — dates "
                f"publiées `null`, appartenance non établie (#653) : "
                f"{', '.join(sorted(sans_appartenance))}.",
                DESTINATAIRE_LECTEUR,
            ))

    # --- Période du groupe ---
    all_debuts = [_parse_date(m["debut_dans_groupe"]) for m in membres]
    all_fins = [_parse_date(m["fin_dans_groupe"]) for m in membres]
    parsed_debuts = [d for d in all_debuts if d is not None]

    periode_debut = str(min(parsed_debuts)) if parsed_debuts else None
    # Le groupe est ouvert tant qu'une appartenance datée n'a pas de fin.
    # `periode.actif` reste ce qu'il dit — une propriété de la PÉRIODE, pas un
    # compteur ancré sur le présent : `false` sur une législature close est
    # exact, et c'est pour ça qu'il n'est pas rapporté à la date de référence.
    groupe_actif = any(
        m["debut_dans_groupe"] and m["fin_dans_groupe"] is None for m in membres
    )
    if groupe_actif:
        periode_fin = None
    else:
        parsed_fins = [f for f in all_fins if f is not None]
        periode_fin = str(max(parsed_fins)) if parsed_fins else None

    # --- Date de référence, puis les comptes qui s'y rapportent (#653) ---
    # L'ordre est contraint : la date se dérive des dates de TOUS les membres,
    # et c'est elle qui décide ensuite qui est compté. Aucun compteur de cette
    # fiche ne se calcule avant elle.
    date_reference = _deriver_date_reference(membres, genere_le)
    date_ref = (date_reference or {}).get("date")
    _stamper_presences(membres, date_ref)

    # --- Effectif ---
    n_presents = sum(1 for m in membres if m["present_a_la_date_de_reference"])
    # L'amplitude est calculée ICI, sur la même liste `membres[]` et par la même
    # fonction de présence (`_appartenance_couvre`) que le compteur ci-dessus
    # (#702). Un agrégat pré-calculé ailleurs survivrait à la correction de sa
    # source : ce qui rendrait cette amplitude fausse, ce sont les dates
    # d'appartenance, et elles sont lues au même instant que le reste de la fiche.
    min_historique, max_historique, motif_amplitude = _effectif_sur_la_periode(
        membres, periode_debut, periode_fin, date_ref
    )
    effectif: dict[str, Any] = {
        "a_la_date_de_reference": n_presents,
        "min_historique": min_historique,
        "max_historique": max_historique,
    }
    if (date_reference or {}).get("origine") == ORIGINE_DATE_REFERENCE_CLOTURE:
        warnings.append(avertissement(
            f"date_reference : tous les comptes de cette fiche se rapportent au "
            f"{date_ref}, jour de la dernière appartenance close — "
            f"`effectif.a_la_date_de_reference` "
            f"({n_presents} sur les {len(membres)} entrées de `membres[]`), "
            "`mandats_agreges[].nb_membres_a_la_date_de_reference` et "
            "`membres[].present_a_la_date_de_reference`. Cette date est celle où le "
            "dernier membre a quitté le groupe, qui n'est pas toujours la clôture de la "
            "législature — `NG-15` s'arrête au 11/09/2018, la XVe au 21/06/2022 (#808). "
            "Une fiche dont toutes les appartenances sont closes est un objet "
            "historique : aucun de ses compteurs ne dit « aujourd'hui » (#653).",
            DESTINATAIRE_LECTEUR,
        ))
    else:
        warnings.append(avertissement(
            f"date_reference : tous les comptes de cette fiche se rapportent au "
            f"{date_ref}, date de génération — au moins une appartenance au groupe est "
            "encore ouverte, la législature court. La valeur bougera au prochain run "
            "(#653).",
            DESTINATAIRE_LECTEUR,
        ))

    # --- Ce que l'amplitude d'effectif dit, et ce qu'elle ne dit pas (#702) ---
    if motif_amplitude == MOTIF_AMPLITUDE_APPARTENANCE_NON_ETABLIE:
        n_sans_date = sum(1 for m in membres if not m.get("debut_dans_groupe"))
        warnings.append(avertissement(
            f"effectif_sur_la_periode : `min_historique` et `max_historique` sont publiés "
            f"`null` — {n_sans_date} des {len(membres)} entrées de `membres[]` n'ont pas de "
            "`debut_dans_groupe`, donc ne sont comptables à aucune date. Un minimum calculé "
            "sans elles serait une borne inférieure publiée sous le nom « minimum » (#702).",
            DESTINATAIRE_LECTEUR,
        ))
    elif motif_amplitude == MOTIF_AMPLITUDE_FENETRE_NON_BORNEE:
        warnings.append(avertissement(
            "effectif_sur_la_periode : `min_historique` et `max_historique` sont publiés "
            "`null` — la période de la fiche n'est pas bornée : `periode.debut` est absent, "
            "ou `periode.fin` et `date_reference.date` le sont toutes les deux. Une fenêtre "
            "non bornée couvrirait toutes les dates (#702).",
            DESTINATAIRE_LECTEUR,
        ))
    elif min_historique and max_historique:
        borne_haute = periode_fin or date_ref
        warnings.append(avertissement(
            f"effectif_sur_la_periode : entre {periode_debut} et {borne_haute}, le groupe a "
            f"compté au minimum {min_historique['valeur']} membres "
            f"({min_historique['date']}) et au maximum {max_historique['valeur']} "
            f"({max_historique['date']}) — première date à laquelle chaque borne est "
            "atteinte. L'effectif est réévalué à chaque entrée et à chaque lendemain de "
            "sortie, jamais hors de cette fenêtre. `membres[]` ne porte qu'un intervalle "
            "par membre (périodes recollées, #526) : un départ suivi d'un retour n'y "
            "apparaît pas, et aucune de ces deux bornes ne le voit (#702).",
            DESTINATAIRE_LECTEUR,
        ))

    # --- Cohésion de vote ---
    cohesion_votes = _compute_cohesion_votes(
        profils, seuil_quorum=seuil_quorum, legislature=legislature,
        scrutins_index=scrutins_index, chambre=chambre,
    )
    n_non_resolus = _votes_non_resolus(profils)
    if n_non_resolus:
        warnings.append(
            f"cohesion_votes : {n_non_resolus} vote(s) sans scrutin_id écarté(s) — "
            "aucun rattachement de législature possible, donc aucun scrutin identifiable "
            "(#432). Le dénominateur publié ne les compte pas."
        )

    # --- Tags thématiques ---
    agregat_tags = aggregate_tags_thematiques(profils, legislature=legislature)
    tags_agreges, tag_source = agregat_tags.tags, agregat_tags.source
    # #825 — L'EMPREINTE THÉMATIQUE D'UNE FICHE EST CELLE DE SA LÉGISLATURE.
    # Quatrième occurrence du même motif après #657, #817 et #821 : un agrégat
    # de fiche parcourait la carrière entière de ses membres. Mesuré avant
    # correctif sur les 40 premiers membres de `REN-16` : 36 264 interventions
    # de la XVe et 5 477 de la XVIIe pour 14 172 de la XVIe, soit **26 %**.
    if agregat_tags.hors_periode:
        warnings.append(
            f"tags_thematiques_agreges : {agregat_tags.hors_periode} intervention(s) "
            f"tenue(s) sous une autre législature que la {legislature or '?'}e n'ont pas "
            "nourri l'empreinte thématique — elles appartiennent à la carrière de leurs "
            "auteurs, pas à l'activité de ce groupe (#825, même règle que les votes "
            "depuis #403 et que les amendements depuis #821)."
        )
    if agregat_tags.sans_legislature:
        warnings.append(
            f"tags_thematiques_agreges : {agregat_tags.sans_legislature} intervention(s) "
            "dont l'identifiant ne porte pas de législature sont CONSERVÉES — rien ne "
            "prouve qu'elles soient hors période, et les écarter ferait passer une "
            "ignorance pour un fait (§2 règle 5)."
        )
    if tag_source == "theme_officiel":
        warnings.append(
            "tags_thematiques_agreges : source=theme_officiel "
            "(tags_thematiques individuels absents ou vides ; thèmes officiels "
            "Syceron des interventions utilisés en fallback)."
        )
    elif tag_source == "mots_cles_interventions":
        warnings.append(
            "tags_thematiques_agreges : source=mots_cles_interventions "
            "(tags_thematiques individuels absents ou vides ; mots-clés des "
            "interventions utilisés en fallback)."
        )
    elif tag_source == "mixed":
        warnings.append(
            "tags_thematiques_agreges : source=mixed (certains profils utilisent "
            "tags_thematiques, d'autres utilisent mots_cles_interventions)."
        )

    # --- Sources uniques (dédoublonnées par type + url) ---
    seen_sources: set[tuple[str, str]] = set()
    sources: list[dict[str, Any]] = []
    for p in profils:
        for s in (p.get("sources") or []):
            key = (s.get("type") or "", s.get("url") or "")
            if key not in seen_sources:
                seen_sources.add(key)
                sources.append(s)

    # --- Mandats agrégés (agrégation catégorielle sur mandats[]) ---
    mandats_agreges = _aggregate_mandats(profils, membres, chambre, date_ref)

    # --- Amendements agrégés (comparateur du taux d'adoption individuel) ---
    amendements_agreges, n_amendements_non_resolus = _aggregate_amendements(
        profils, amendements_index
    )
    # #821 — CE QUI EST COMPTÉ ICI EST UNE SIGNATURE, ET LE MESSAGE LE DIT.
    # Le compteur s'incrémente une fois par ENTRÉE d'`amendements[]`, donc une
    # fois par signataire : 657 996 signatures écartées sur `LR-16` pour
    # 126 997 amendements distincts. Les nommer « amendements » reproduirait
    # exactement la confusion que #643 a corrigée (§6 : les signatures se
    # publient sous leur nom, jamais sous celui des amendements).
    n_hors_periode = amendements_agreges.get("nb_signatures_hors_periode_ecartees") or 0
    if n_hors_periode:
        warnings.append(
            f"amendements_agreges : {n_hors_periode} signature(s) portant sur des "
            f"amendements déposés sous une autre législature que la "
            f"{legislature or '?'}e ont été écartées — ils appartiennent à la "
            "carrière de leurs auteurs, pas à l'activité de ce groupe (#821, même "
            "règle que les votes depuis #403)."
        )
    n_sans_leg = amendements_agreges.get("nb_signatures_sans_legislature_retenues") or 0
    if n_sans_leg:
        warnings.append(
            f"amendements_agreges : {n_sans_leg} signature(s) dont l'identifiant "
            "d'amendement ne porte pas de législature sont CONSERVÉES — rien ne "
            "prouve qu'elles soient hors période, et les écarter ferait passer une "
            "ignorance pour un fait (§2 règle 5)."
        )
    if n_amendements_non_resolus:
        warnings.append(
            f"amendements_agreges : {n_amendements_non_resolus} amendement(s) "
            "introuvable(s) dans l'index partagé et sans enregistrement de repli, "
            "écarté(s) (#431). Le dénominateur publié ne les compte pas."
        )
    # Sans identifiant, pas de déduplication (#643) : ces entrées sont comptées
    # une fois par signataire au milieu d'amendements qui, eux, ne le sont
    # qu'une. Le taire ferait de `nb_amendements` un mélange des deux natures,
    # exactement le défaut que ce lot corrige (AGENTS.md §2.5).
    n_sans_identifiant = amendements_agreges.get("nb_sans_identifiant") or 0
    if n_sans_identifiant:
        warnings.append(
            f"amendements_agreges : {n_sans_identifiant} amendement(s) sans "
            "`amendement_id`, donc non dédoublonnables entre membres — comptés une "
            "fois par signataire (#643). Aucune clé ne s'invente (AGENTS.md §2 "
            "règle 5) ; `nb_amendements` les compte tels quels."
        )

    # --- Assemblage ---
    profil_groupe = make_empty_profil_groupe(
        groupe_id=groupe_id,
        groupe_sigle=groupe_sigle,
        groupe_nom=groupe_nom,
        chambre=chambre,
        legislature=legislature,
    )

    profil_groupe["periode"] = {
        "debut": periode_debut,
        "fin": periode_fin,
        "actif": groupe_actif,
    }
    profil_groupe["membres"] = membres
    # Recopiée telle quelle, jamais recalculée sur les compteurs de la fiche
    # (#686). `None` reste `None` : un champ absent dit « non renseigné », là
    # où `non_declaree` dit « la source n'a rien déclaré » — deux constats
    # distincts, et les confondre ferait passer une fiche sénatoriale pour un
    # groupe que l'Assemblée aurait omis de qualifier.
    profil_groupe["position_politique"] = position_politique
    # Recopié tel quel, jamais dérivé des membres (#700). `None` reste `None` :
    # ne pas succéder à un groupe couvert par ce dépôt est un périmètre, pas
    # une donnée manquante.
    profil_groupe["succede_a"] = succede_a
    # Les organes successifs du groupe dans sa législature (#815), recopiés de
    # la table committée. `None` — l'historique n'a pas été mesuré — garde la
    # liste vide que le schéma exige : l'absence de mesure n'y devient pas un
    # historique inventé.
    profil_groupe["historique_noms"] = list(historique_noms) if historique_noms else []
    profil_groupe["date_reference"] = date_reference
    profil_groupe["effectif"] = effectif
    profil_groupe["cohesion_votes"] = cohesion_votes
    profil_groupe["tags_thematiques_agreges"] = tags_agreges
    profil_groupe["mandats_agreges"] = mandats_agreges
    profil_groupe["amendements_agreges"] = amendements_agreges
    profil_groupe["sources"] = sources

    # `licence_donnees` : dérivée de `sources[]` quand l'appelant n'impose rien
    # (#530, lot 6). Le pipeline ne passe pas `--licence`, et les 7 fiches
    # publiées portaient donc une attribution **vide** — un manque, sur des
    # documents dérivés de données ouvertes qui en exigent une (AGENTS.md §7).
    # La dérivation, et non une constante : `groupe-Senat-LR` et `groupe-Senat-SER` dérivent de NosSénateurs (ODbL)
    # quand les 5 fiches AN dérivent d'AMO30 (Licence Ouverte). L'argument explicite reste
    # prioritaire, c'est lui qui permet d'annoter une fiche hors pipeline.
    if licence_donnees:
        profil_groupe["meta"]["licence_donnees"] = licence_donnees
    else:
        appliquer_licence_donnees(profil_groupe)
    profil_groupe["meta"]["profils_sources"] = [
        p.get("id") or "" for p in profils
    ]
    profil_groupe["meta"]["seuil_quorum"] = seuil_quorum
    profil_groupe["meta"]["warnings"] = warnings

    return profil_groupe


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="group_profile.py",
        description=(
            "Agrège des profils individuels (pivot v1 ou brut de collecte) "
            "en un profil de groupe politique."
        ),
    )
    parser.add_argument(
        "profils",
        nargs="*",
        metavar="PROFIL.json",
        help="Fichiers JSON des profils individuels des membres du groupe (ignoré avec --from-roster).",
    )
    parser.add_argument(
        "--from-roster",
        action="store_true",
        help=(
            "Récupère la composition réelle du groupe via group_roster.py "
            "(référentiel AMO30 de l'Assemblée nationale) au lieu des fichiers "
            "PROFIL.json."
        ),
    )
    parser.add_argument(
        "--roster-chambre",
        choices=["deputes"],
        default=None,
        help=(
            "Requis avec --from-roster : chambre interrogée pour la composition du "
            "groupe. Seule valeur depuis #528 — le Sénat est hors périmètre."
        ),
    )
    parser.add_argument(
        "--profiles-dir",
        default="pivot_data/profiles",
        metavar="DOSSIER",
        help="Avec --from-roster : dossier des pivots *.pivot.json (défaut : pivot_data/profiles).",
    )
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help=(
            "Avec --from-roster --out FICHIER : si FICHIER existe déjà, réintègre les "
            "membres qui y figuraient mais sont absents du roster récupéré cette "
            "exécution (protège contre un échec partiel de récupération du roster live). "
            "Sans cette option, --out écrase entièrement le fichier existant à chaque exécution."
        ),
    )
    parser.add_argument("--groupe-id", required=True, help="Ex. AN:SOC")
    parser.add_argument("--groupe-sigle", required=True, help="Ex. SOC")
    parser.add_argument("--groupe-nom", required=True, help="Ex. 'Socialistes et apparentés'")
    parser.add_argument(
        "--chambre",
        choices=["AN", "Senat", "PE", "mairie"],
        default=None,
        help="Chambre parlementaire.",
    )
    parser.add_argument("--legislature", default=None, help="Ex. 16")
    parser.add_argument(
        "--scrutins", default=str(DEFAULT_SCRUTINS_PATH), metavar="FICHIER",
        help=(
            "Index partagé des scrutins (#432, défaut : "
            f"{DEFAULT_SCRUTINS_PATH}). La cohésion en dépend : la date d'un scrutin, "
            "qui détermine les membres éligibles, n'est plus dans les profils."
        ),
    )
    parser.add_argument(
        "--amendements", default=str(DEFAULT_AMENDEMENTS_DIR), metavar="DOSSIER",
        help=(
            "Index partagé des amendements (#431, défaut : "
            f"{DEFAULT_AMENDEMENTS_DIR}). `amendements_agreges` en dépend : le "
            "`sort` et le `type_deposant` d'un amendement ne sont plus dans les profils."
        ),
    )
    parser.add_argument(
        "--seuil-quorum",
        type=float,
        default=0.5,
        metavar="FLOAT",
        help="Seuil de participation pour quorum_atteint (défaut : 0.5).",
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
        help="Valide le profil de groupe produit et affiche les erreurs éventuelles.",
    )
    parser.add_argument(
        "--rapport-interne",
        default=None,
        metavar="FICHIER",
        help=(
            "Écrit dans FICHIER un rapport interne (écarts de cohésion/participation "
            "individuels vs moyenne du groupe). Donnée de contrôle interne : jamais "
            "incluse dans le profil de groupe public écrit via --out."
        ),
    )
    return parser


def _avertissement_fraicheur_an() -> str:
    """`meta.warnings` de fraîcheur d'une fiche AN — il doit NOMMER sa source.

    C'est un champ **publié**, et la règle 2 d'AGENTS §2 (traçabilité totale)
    ne souffre pas qu'il nomme une source dont la composition ne vient pas.
    Jusqu'à #529 il avait DEUX rédactions, choisies sur
    `an_roster.AN_ROSTER_ACTIF` : celle d'AMO30 et celle de NosDéputés, qui
    était le repli du drapeau. Ce repli est retiré — le drapeau baissé ne rend
    plus la lecture à personne, il refuse (`RosterAnInactif`) — donc il n'y a
    plus qu'une source à nommer, et une seule rédaction.

    AMO30 est le référentiel de l'Assemblée elle-même : une législature close y
    est complète, y compris les mandats terminés en cours de législature, ce
    que le miroir — qui ne publiait que la dernière appartenance connue —
    perdait (4 acteurs mesurés, #526 §2).
    """
    return (
        "fraicheur_donnees : composition dérivée du référentiel AMO30 de "
        "l'Assemblée nationale (data.assemblee-nationale.fr, Licence "
        "Ouverte), et non plus de www.nosdeputes.fr depuis #527. Une "
        "législature close y est complète : les mandats terminés en cours "
        "de législature y figurent, alors que la dernière composition "
        "connue d'un miroir les perd. La fiche reflète donc l'appartenance "
        "au groupe telle que l'Assemblée la publie à la date de "
        "meta.genere_le ; un membre sans profil publié n'y apparaît pas "
        "(voir meta.couverture_roster)."
    )


def generate_groupe_profile_from_roster(
    *,
    roster: list[dict[str, Any]],
    groupe_id: str,
    groupe_sigle: str,
    groupe_nom: str,
    chambre: Optional[str],
    legislature: Optional[str],
    roster_chambre: str,
    profiles_dir: Path,
    out_path: Optional[Path] = None,
    merge_existing: bool = False,
    seuil_quorum: float = 0.5,
    licence_donnees: str = "",
    validate: bool = False,
    rapport_interne_path: Optional[Path] = None,
    scrutins_index: Optional[ScrutinsIndex] = None,
    amendements_index: Optional[AmendementsIndex] = None,
    position_politique: Optional[dict[str, Any]] = None,
    succede_a: Optional[list[dict[str, Any]]] = None,
    historique_noms: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Construit (et écrit si `out_path` fourni) un profil de groupe à partir d'un
    roster déjà récupéré (voir `fetch_group_roster`, ou `fetch_full_roster` +
    `filter_roster_by_sigle` pour partager un même fetch réseau entre plusieurs
    sigles d'une même chambre/législature — voir generate_group_profiles.py).

    Factorise la logique partagée entre le CLI `--from-roster` de `main()` et
    `generate_group_profiles.py`.
    """
    print(f"→ {len(roster)} membre(s) réel(s) trouvé(s) pour {groupe_sigle!r}.", file=sys.stderr)

    # --merge-existing : réintègre les membres du fichier --out précédent
    # absents du roster récupéré cette exécution (protège contre un échec
    # partiel de récupération du roster live). Sans cette option, --out
    # écrase entièrement le fichier existant à chaque exécution.
    recovered_slugs: list[str] = []
    if merge_existing and out_path and out_path.exists():
        try:
            old_profil = json.loads(out_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            print(f"  [!] --merge-existing : lecture de {out_path} impossible ({exc}), ignoré.", file=sys.stderr)
            old_profil = None
        if old_profil:
            roster_slugs = {m.get("slug") for m in roster if m.get("slug")}
            old_slugs = {
                membre_id.split(":", 1)[1] if ":" in membre_id else membre_id
                for membre_id in (m.get("membre_id") for m in old_profil.get("membres", []))
                if membre_id
            }
            recovered_slugs = sorted(old_slugs - roster_slugs)
            if recovered_slugs:
                print(
                    f"  [i] --merge-existing : {len(recovered_slugs)} membre(s) de {out_path} "
                    f"absent(s) du roster récupéré cette exécution, réintégré(s) : "
                    f"{', '.join(recovered_slugs)}",
                    file=sys.stderr,
                )

    # Un seul cumul pour toute la fiche (#643) : c'est lui qui dédoublonne les
    # amendements entre membres, et le partager le fait tenir dans les
    # amendements distincts (159 143 au plus haut) plutôt que dans leurs
    # signatures (2 647 601).
    distincts = CumulAmendementsDistincts()
    profils: list[dict[str, Any]] = []
    missing_slugs: list[str] = []
    # Les dates d'appartenance sont indexées sur l'`id` du pivot **chargé**, pas
    # sur le slug du roster : les deux coïncident depuis #487, et les indexer
    # sur le slug rendrait le rapprochement muet le jour où ils divergent — ce
    # qui, sur des dates publiées, se lirait comme « appartenance non établie »
    # plutôt que comme un bug.
    table_roster = appartenances_depuis_roster(roster)
    appartenances: dict[str, dict[str, Any]] = {}
    for member in roster:
        slug = member.get("slug")
        pivot_path = profiles_dir / f"{slug}.pivot.json" if slug else None
        if pivot_path is None or not pivot_path.exists():
            missing_slugs.append(slug or member.get("nom") or "?")
            continue
        try:
            profil = load_profil_from_file(
                pivot_path, amendements_index, distincts=distincts,
                legislature=legislature,
            )
        except (FileNotFoundError, ValueError) as exc:
            print(f"  [!] {exc}", file=sys.stderr)
            missing_slugs.append(slug)
            continue
        profils.append(profil)
        appartenances[profil.get("id") or slug] = table_roster[slug]

    for slug in recovered_slugs:
        pivot_path = profiles_dir / f"{slug}.pivot.json"
        if not pivot_path.exists():
            continue
        try:
            profils.append(load_profil_from_file(
                pivot_path, amendements_index, distincts=distincts,
                legislature=legislature,
            ))
        except (FileNotFoundError, ValueError) as exc:
            print(f"  [!] {exc}", file=sys.stderr)

    # `etat` (#558) — ce que le ratio veut dire. Toujours `dans_le_perimetre`
    # ici, et ce n'est pas un défaut par défaut : ce chemin ne s'exécute QUE
    # pour un groupe activement collecté. `generate_group_profiles.py` écarte
    # les entrées `extraction_suspendue` (#516), donc une fiche gelée n'est
    # jamais réécrite — le `hors_perimetre` des deux fiches `groupe-Senat-*` est
    # posé une fois, par migration, et rien ici ne peut le reprendre en silence.
    couverture_roster = {
        "roster_total": len(roster),
        "profils_disponibles": len(profils),
        "etat": ETAT_ROSTER_DANS_LE_PERIMETRE,
    }
    if missing_slugs:
        print(
            f"  [!] {len(missing_slugs)} membre(s) du roster sans profil pivot local "
            f"dans {profiles_dir} : {', '.join(missing_slugs)}",
            file=sys.stderr,
        )

    print(f"→ {len(profils)} profil(s) chargé(s). Calcul en cours…", file=sys.stderr)

    profil_groupe = build_groupe_profile(
        groupe_id=groupe_id,
        groupe_sigle=groupe_sigle,
        groupe_nom=groupe_nom,
        chambre=chambre,
        legislature=legislature,
        profils=profils,
        seuil_quorum=seuil_quorum,
        licence_donnees=licence_donnees,
        scrutins_index=scrutins_index,
        amendements_index=amendements_index,
        # Les dates d'appartenance sortent du roster, pas des profils (#653).
        # Les `recovered_slugs` de `--merge-existing` n'y sont par définition
        # pas : leurs dates sortent `null`, et `build_groupe_profile` les
        # compte — un membre réintégré parce que le roster ne l'a pas rendu
        # n'a pas de mandat de groupe lisible, et lui en inventer un serait
        # exactement ce que ce lot retire.
        appartenances=appartenances,
        position_politique=position_politique,
        succede_a=succede_a,
        historique_noms=historique_noms,
    )

    profil_groupe["meta"]["couverture_roster"] = couverture_roster
    if recovered_slugs:
        profil_groupe["meta"]["warnings"].append(
            f"fusion_avec_existant : {len(recovered_slugs)} membre(s) présent(s) dans "
            f"{out_path} avant cette exécution mais absent(s) du roster récupéré cette "
            f"fois-ci ont été réintégré(s) (probable échec partiel de récupération du "
            f"roster live, ou départ réel du groupe non distinguable automatiquement ici) : "
            f"{', '.join(recovered_slugs)}. meta.couverture_roster.roster_total ne reflète "
            f"que le roster récupéré cette exécution, pas ces membres réintégrés."
        )
    # #528 : la branche `roster_chambre == "senateurs"` a été retirée. Elle
    # posait deux avertissements publiés (`fraicheur_donnees` sur
    # archive.nossenateurs.fr, `couverture_roster_senat` sur l'impossibilité de
    # distinguer les sénateurs en fonction des anciens) sur les deux fiches
    # `groupe-Senat-*.json`. Ces fiches restent PUBLIÉES et FIGÉES, avec leurs
    # avertissements : la suspension d'extraction de #516 les empêche d'être
    # régénérées, et les retirer supprimerait un fichier publié — ce que
    # `audit_diff_profils` bloque (#460/#470). Voir
    # docs/decisions/retrait-senat-528.md.
    if roster_chambre == "deputes":
        profil_groupe["meta"]["warnings"].append(_avertissement_fraicheur_an())

    if validate:
        errors = validate_profil_groupe(profil_groupe)
        if errors:
            print(f"  [!] {len(errors)} erreur(s) de validation :", file=sys.stderr)
            for e in errors:
                print(f"      - {e}", file=sys.stderr)
        else:
            print("  ✓ Profil de groupe valide selon le schéma.", file=sys.stderr)

    if rapport_interne_path:
        rapport = compute_ecarts_cohesion_internes(
            profils, profil_groupe["cohesion_votes"], profil_groupe.get("legislature"),
            scrutins_index=scrutins_index, chambre=profil_groupe.get("chambre"),
        )
        rapport_interne_path.parent.mkdir(parents=True, exist_ok=True)
        rapport_interne_path.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  ✓ Rapport interne (non public) écrit : {rapport_interne_path}", file=sys.stderr)

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        # #343 : ne pas faire avancer meta.genere_le / sources[].synchro_le
        # quand le profil régénéré est identique en contenu. Ce script
        # reconstruit sa sortie à chaque exécution sans comparer à la version
        # précédente — sans ça, chaque run produit un diff sur les 7 fichiers
        # groupe alors que rien n'a changé, ce qui bruite les commits et
        # fausse toute lecture de fraîcheur (AGENTS.md §2).
        profil_groupe = preserve_stable_freshness_timestamps(
            load_existing_document(out_path), profil_groupe
        )
        out_path.write_text(json.dumps(profil_groupe, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  ✓ Profil de groupe écrit : {out_path}", file=sys.stderr)

    return profil_groupe


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.from_roster:
        if not args.roster_chambre:
            print("[!] --from-roster requiert --roster-chambre (deputes).", file=sys.stderr)
            return 1
        from group_roster import fetch_group_roster  # import tardif : requests non requis hors ce mode
        import requests

        legislature = args.legislature if args.roster_chambre == "deputes" else None
        try:
            roster = fetch_group_roster(
                chambre=args.roster_chambre,
                groupe_sigle=args.groupe_sigle,
                legislature=legislature,
            )
        except (ValueError, requests.RequestException) as exc:
            print(f"[!] Récupération du roster impossible : {exc}", file=sys.stderr)
            return 1

        # La posture déclarée sort de la table committée, jamais d'une
        # mesure faite ici (#686) : ce chemin CLI doit publier exactement ce
        # que publie `generate_group_profiles.py`, sans quoi régénérer une
        # fiche à la main la ferait discrètement régresser sur ce champ.
        position_politique = None
        succede_a = None
        historique_noms = None
        if args.chambre == "AN":
            position_politique = position_politique_publiee(
                args.groupe_sigle, args.legislature
            )
            succede_a = succession_publiee(args.groupe_sigle, args.legislature)
            historique_noms = historique_noms_publie(args.groupe_sigle, args.legislature)

        out_path = Path(args.out) if args.out else None
        profil_groupe = generate_groupe_profile_from_roster(
            roster=roster,
            groupe_id=args.groupe_id,
            groupe_sigle=args.groupe_sigle,
            groupe_nom=args.groupe_nom,
            chambre=args.chambre,
            legislature=args.legislature,
            roster_chambre=args.roster_chambre,
            profiles_dir=Path(args.profiles_dir),
            out_path=out_path,
            merge_existing=args.merge_existing,
            seuil_quorum=args.seuil_quorum,
            licence_donnees=args.licence,
            validate=args.validate,
            rapport_interne_path=Path(args.rapport_interne) if args.rapport_interne else None,
            position_politique=position_politique,
            succede_a=succede_a,
            historique_noms=historique_noms,
        )
        if not out_path:
            print(json.dumps(profil_groupe, ensure_ascii=False, indent=2))
        return 0

    # Les index sont chargés AVANT les profils depuis #635 : c'est l'index des
    # amendements qui résout `sort` et `type_deposant`, et la lecture d'un
    # profil réduit désormais son `amendements[]` à sa contribution au lieu d'en
    # garder les entrées. Le même index est passé ici et à
    # `build_groupe_profile` — l'un sans l'autre ferait diverger l'agrégat.
    scrutins_index = charger_scrutins(Path(args.scrutins))
    if len(scrutins_index) == 0:
        # Sans index, la cohésion sort vide plutôt que fausse : mieux vaut le
        # dire ici que laisser lire un `cohesion_votes: []` comme un fait.
        print(
            f"  [!] Index des scrutins vide ou absent ({args.scrutins}) : la cohésion "
            "de vote ne pourra pas être calculée (#432). Construire l'index avec "
            "`python3 src/build_scrutins_index.py`.",
            file=sys.stderr,
        )
    else:
        print(f"→ Index des scrutins : {len(scrutins_index)} scrutin(s).", file=sys.stderr)

    # `avec_cosignatures=False` : l'agrégat ne lit que `sort` et `type_deposant`.
    # Charger les cosignatures coûterait 59 % de l'index pour rien (#431).
    amendements_index = charger_amendements(
        Path(args.amendements), avec_cosignatures=False
    )
    if len(amendements_index) == 0:
        print(
            f"  [!] Index des amendements vide ou absent ({args.amendements}) : "
            "`amendements_agreges` ne comptera que les entrées portant encore leur "
            "enregistrement (#431). Construire l'index avec "
            "`python3 src/build_amendements_index_pivot.py`.",
            file=sys.stderr,
        )
    else:
        print(f"→ Index des amendements : {len(amendements_index)} amendement(s).", file=sys.stderr)

    distincts = CumulAmendementsDistincts()
    profils: list[dict[str, Any]] = []
    for path_str in args.profils:
        path = Path(path_str)
        print(f"→ Chargement : {path}", file=sys.stderr)
        try:
            profils.append(load_profil_from_file(
                path, amendements_index, distincts=distincts,
                legislature=args.legislature,
            ))
        except (FileNotFoundError, ValueError) as exc:
            print(f"  [!] {exc}", file=sys.stderr)
            return 1

    print(
        f"→ {len(profils)} profil(s) chargé(s). Calcul en cours…",
        file=sys.stderr,
    )

    profil_groupe = build_groupe_profile(
        groupe_id=args.groupe_id,
        groupe_sigle=args.groupe_sigle,
        groupe_nom=args.groupe_nom,
        chambre=args.chambre,
        legislature=args.legislature,
        profils=profils,
        seuil_quorum=args.seuil_quorum,
        licence_donnees=args.licence,
        scrutins_index=scrutins_index,
        amendements_index=amendements_index,
    )

    if args.validate:
        errors = validate_profil_groupe(profil_groupe)
        if errors:
            print(f"  [!] {len(errors)} erreur(s) de validation :", file=sys.stderr)
            for e in errors:
                print(f"      - {e}", file=sys.stderr)
        else:
            print("  ✓ Profil de groupe valide selon le schéma.", file=sys.stderr)

    if args.rapport_interne:
        rapport = compute_ecarts_cohesion_internes(
            profils, profil_groupe["cohesion_votes"], profil_groupe.get("legislature"),
            scrutins_index=scrutins_index, chambre=profil_groupe.get("chambre"),
        )
        rapport_path = Path(args.rapport_interne)
        rapport_path.parent.mkdir(parents=True, exist_ok=True)
        rapport_path.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  ✓ Rapport interne (non public) écrit : {rapport_path}", file=sys.stderr)

    output_json = json.dumps(profil_groupe, ensure_ascii=False, indent=2)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")
        print(f"  ✓ Profil de groupe écrit : {out_path}", file=sys.stderr)
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
