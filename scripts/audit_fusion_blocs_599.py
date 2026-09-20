#!/usr/bin/env python3
"""
audit_fusion_blocs_599.py — Combien de profils publiés portent une identité ou
un `meta` venu d'un écrivain qui n'avait pas la donnée (#599, lot 0 de #598).

**Ce script ne modifie rien.** Il mesure, sur le corpus déjà committé, l'ampleur
du défaut décrit par #598 : `src/merge_profile.py` ne compose pas les blocs
structurés (`identite`, `meta`, `couverture`), il en **choisit un entier** —
`merged = dict(new)` pour `meta`, `_prefer_non_empty` / `_preferer_bloc_avec_fond`
pour `identite`. Le gagnant est donc décidé par l'ordre des jobs du workflow
(`--dirs _artifacts/an _artifacts/ue _artifacts/roster`), pas par une règle sur
la donnée.

Il est écrit pour être **rejoué** : c'est lui qui fournira la mesure « après »
au critère de sortie de #598. Il ne prend aucune décision et n'écrit dans aucun
répertoire de données ; sa seule sortie est un rapport.

Ce qu'il sait lire, et pourquoi c'est suffisant
-----------------------------------------------
Les artifacts des jobs d'extraction ne sont pas conservés : on ne peut pas
rejouer la fusion. Mais **le résultat en porte les empreintes**, et elles sont
vérifiables sur le corpus committé :

1. `generate_all_profiles.build_minimal_profile` écrit un `identite` d'une forme
   très reconnaissable — huit clés exactement, dont seules `nom_complet` et
   `groupe_nom` sont renseignées, et **ni `lieu_naissance` ni `uri_hatvp`**, que
   l'écrivain AN produit toujours. Un profil brut qui porte cette forme **et**
   des données parlementaires est un profil dont l'identité vient d'un écrivain
   qui n'avait rien collecté.
2. Le même chemin minimal écrit un `meta` à trois clés — `genere_le`,
   `licence_donnees`, `warnings` — sans `collecte_ecartee` (que l'écrivain AN
   pose depuis #539) et sans `synchro_sources`. Son unique warning est celui du
   chemin minimal. Un profil qui porte des données parlementaires et **ce seul
   warning** a perdu tous les avertissements de l'autre écrivain.
3. Une source n'est interrogée qu'une fois par run : la synchro la plus récente
   d'une source **sur tout le corpus** date le moment où le run l'a réellement
   interrogée. Un profil régénéré par ce run et portant, pour cette source, une
   synchro plus ancienne publie une fraîcheur que le run dément — c'est un
   `synchro_sources` recopié en bloc, pas une source non interrogée.

Les trois lectures sont indépendantes de tout réseau et de tout cache.

Population, toujours nommée
---------------------------
Le rapport ne publie jamais un compteur sans sa population. Quatre profils sont
**comptés à part** et jamais dans le défaut :

- `nathalie-arthaud`, `marine-tondelier`, `david-lisnard` — non-parlementaires
  de #539, dont l'identité nulle est attendue ;
- `jordan-bardella` — un seul mandat, européen : aucun écrivain AN ne le décrit.

Usage :
    python3 scripts/audit_fusion_blocs_599.py
    python3 scripts/audit_fusion_blocs_599.py --json audit/fusion_blocs_599.json \\
                                              --markdown audit/fusion_blocs_599.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RACINE / "src"))

from migrer_absences_publiees_556_558_560 import nettoyer_valeur  # noqa: E402
from profil_brut import charger_socle, slugs_du_repertoire  # noqa: E402

SUFFIXE_PIVOT = ".pivot.json"

#: Les quatre profils dont l'absence d'identité AN est un fait, pas un défaut.
#: Comptés à part dans chaque mesure, jamais dans le défaut (#539, #484).
HORS_DEFAUT: frozenset[str] = frozenset({
    "nathalie-arthaud",
    "marine-tondelier",
    "david-lisnard",
    "jordan-bardella",
})

#: Les clés qu'écrit `generate_all_profiles.build_minimal_profile` dans
#: `identite`. La forme EST la signature : l'écrivain AN produit dix clés
#: (`lieu_naissance` et `uri_hatvp` en plus), le chemin minimal huit.
CLES_IDENTITE_MINIMALE: frozenset[str] = frozenset({
    "nom_complet", "groupe_sigle", "groupe_nom", "profession",
    "date_naissance", "num_circo", "nb_mandats", "url_an_ou_senat",
})

#: Les deux champs qu'un profil minimal remplit **sans avoir rien demandé à
#: personne** : ils viennent de `raw_data/candidats.json`. Même liste que
#: `merge_profile.BLOCS_PROTEGES_DU_VIDE["identite"]`.
CHAMPS_SANS_SOURCE: frozenset[str] = frozenset({"nom_complet", "groupe_nom"})

#: Le préfixe du warning du chemin minimal (`candidate_profile.WARNING_AUCUN_MANDAT_FR`).
#: Recopié ici plutôt qu'importé : l'audit doit continuer de reconnaître le
#: texte **déjà publié** même si la constante bouge.
WARNING_CHEMIN_MINIMAL = "aucun mandat français connu"

#: Listes métier dont la présence prouve qu'un écrivain parlementaire a travaillé
#: sur ce profil. `amendements` est exclu : il est partitionné (#580) et sa
#: lecture coûte 600 Mo pour une information que les quatre autres portent déjà.
#: De ces listes l'audit ne lit que **deux choses** : « y a-t-il quelque
#: chose ? » et « combien ? ». Jamais une entrée. C'est ce qui rend la
#: projection ci-dessous possible sans changer un seul chiffre du rapport.
LISTES_PARLEMENTAIRES: tuple[str, ...] = (
    "votes", "mandats", "interventions", "dossiers_legislatifs",
)

#: Les blocs du profil **pivot** que les mesures lisent, et rien d'autre —
#: relevés dans le code, pas dans l'énoncé : `identite` (mesure 1),
#: `identifiants.hatvp` (mesure 1) et `meta.warnings` (mesure 2). #628 citait
#: aussi `couverture` : **aucune mesure ne l'ouvre**, il n'est donc pas retenu.
#: Ajouter une mesure qui lirait un autre bloc, c'est ajouter ce bloc ici.
BLOCS_PIVOT_LUS: tuple[str, ...] = ("identite", "identifiants", "meta")

#: Idem côté **brut**, hors les listes ci-dessus : `identite` (mesure 1),
#: `meta` (mesures 2 et 3).
BLOCS_BRUT_LUS: tuple[str, ...] = ("identite", "meta")

#: Ce que pèsent, sur le corpus committé du 30/08/2026, les blocs qu'on retient
#: et ceux qu'on relâche — mesuré bloc par bloc, pas estimé :
#:
#:   `amendements`  577,3 Mo    relâché
#:   `votes`         67,1 Mo    relâché
#:   `interventions` 22,2 Mo    relâché
#:   `mandats`       12,6 Mo    relâché
#:   `couverture`     1,6 Mo    relâché (aucune mesure ne l'ouvre)
#:   `meta`           0,21 Mo   **retenu**
#:   `identite`       0,13 Mo   **retenu**
#:   `identifiants`   0,05 Mo   **retenu**
#:
#: Soit 0,39 Mo retenus sur 681,6 Mo — 0,06 %.

#: `identite` brut -> `identite` pivot (`normalize_profil`, lignes 488-494).
#: `source_url` a deux origines possibles côté pivot ; il est traité à part.
CHAMPS_IDENTITE_BRUT_VERS_PIVOT: tuple[tuple[str, str], ...] = (
    ("profession", "profession"),
    ("date_naissance", "date_naissance"),
    ("lieu_naissance", "lieu_naissance"),
    ("num_circo", "num_circo"),
    ("uri_hatvp", "uri_hatvp"),
)

#: Au-delà de ce délai, un écart entre deux horodatages n'est plus un artefact
#: d'ordonnancement des jobs d'un même run mais un vrai décalage de fraîcheur.
SEUIL_ECART_JOURS = 0.5


# ---------------------------------------------------------------------------
# Lecture des valeurs : un marqueur d'absence n'est pas une valeur
# ---------------------------------------------------------------------------

def valeur_de_fond(valeur: Any) -> Any:
    """La valeur si elle en est une, `None` sinon.

    Trois formes d'absence sont ramenées à `None` : le vide littéral, le
    marqueur XML `xsi:nil` d'AMO30 et la chaîne qui l'a interpolé (#556). Les
    compter comme renseignés a déjà produit une mesure fausse — « 465 profils
    portent `uri_hatvp` » alors que 186 portaient le marqueur (#539).
    """
    valeur = nettoyer_valeur(valeur)
    if valeur in (None, "", [], {}):
        return None
    return valeur


def nombre_d_entrees(valeur: Any) -> int:
    """Combien d'entrées porte cette liste — liste réelle **ou** décompte.

    Les profils chargés par `charger_corpus` ne portent plus les listes métier
    mais leur seul cardinal (voir `projeter_socle`) : c'est tout ce que l'audit
    en lit, et les retenir coûtait 1,3 Gio. Les tests, eux, construisent des
    corpus minuscules avec les vraies listes. Cette fonction accepte les deux
    formes, pour que la mesure ne dépende pas de la façon dont on l'a nourrie.
    """
    if isinstance(valeur, bool):
        return 0
    if isinstance(valeur, int):
        return valeur
    try:
        return len(valeur)
    except TypeError:
        return 0


def instant(valeur: Any) -> Optional[datetime]:
    """Horodatage ISO -> instant UTC, ou `None` s'il est illisible.

    Même repli que `merge_profile._instant_synchro` : une chaîne illisible ne
    fait pas lever l'audit, elle sort de la comparaison.
    """
    if not isinstance(valeur, str) or not valeur:
        return None
    try:
        return datetime.fromisoformat(valeur).astimezone(timezone.utc)
    except ValueError:
        return None


def ecart_jours(recent: datetime, ancien: datetime) -> float:
    return (recent - ancien).total_seconds() / 86400.0


# ---------------------------------------------------------------------------
# Chargement du corpus
# ---------------------------------------------------------------------------

def projeter_socle(socle: dict[str, Any]) -> dict[str, Any]:
    """Le socle brut réduit à ce que les mesures en lisent.

    Deux blocs (`identite`, `meta`) et, des quatre listes parlementaires, leur
    seul **cardinal** — `porte_des_donnees_parlementaires` teste « non vide »
    et les constats publient « combien ». Aucune entrée n'est jamais lue.
    """
    projection: dict[str, Any] = {
        bloc: socle[bloc] for bloc in BLOCS_BRUT_LUS if bloc in socle
    }
    for champ in LISTES_PARLEMENTAIRES:
        if champ in socle:
            projection[champ] = nombre_d_entrees(socle[champ])
    return projection


def projeter_pivot(document: dict[str, Any]) -> dict[str, Any]:
    """Le pivot publié réduit à ses trois blocs lus (`BLOCS_PIVOT_LUS`).

    Le document complet ne vit que le temps de l'appel ; les listes qui font
    99,94 % de son poids meurent avec lui, à la sortie.
    """
    return {bloc: document[bloc] for bloc in BLOCS_PIVOT_LUS if bloc in document}


def _lire_pivot(chemin: Path) -> Optional[dict[str, Any]]:
    """Lit **un** pivot et n'en rend que la projection.

    Le `json.loads` complet reste nécessaire — un profil est écrit compact, sur
    une seule ligne (#433), il n'y a pas de lecture incrémentale possible sans
    dépendance nouvelle. Ce qui change, c'est la **durée de vie** : le document
    entier est local à cette fonction et relâché à son retour, au lieu d'être
    rangé dans un dictionnaire indexé par slug pour tout le reste du run.
    """
    document = json.loads(chemin.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        return None
    return projeter_pivot(document)


def charger_corpus(
    profils_bruts: Path, profils_pivot: Path
) -> tuple[dict[str, dict], dict[str, dict], list[str]]:
    """Charge les socles bruts et les pivots publiés, **projetés**, par slug.

    Les bruts passent par `profil_brut.charger_socle` — jamais `json.load` sur
    `<slug>.json` : le profil est partitionné par législature depuis #580, et
    seul ce module sait le lire. Le socle suffit ici : aucune mesure ne porte
    sur les amendements.

    **Aucun document n'est conservé entier (#628).** Un profil est lu, projeté
    sur les blocs que les mesures ouvrent (`BLOCS_BRUT_LUS`, `BLOCS_PIVOT_LUS`,
    et le cardinal des listes), puis relâché. Conserver les documents entiers
    coûtait ~3,9 Gio de pic sur le corpus committé — 1,3 Gio pour les socles,
    2,6 Gio pour les pivots — et l'audit était tué par l'OOM avant de rendre son
    rapport : livré « rejouable » par #599, il ne l'était que sur une machine
    reposée. C'est le motif de
    `docs/decisions/oom-lecture-amendements-par-candidat.md`, ici sur un chemin
    neuf : 623 Mo de JSON sur disque valent 3 à 10 fois plus une fois
    désérialisés en objets Python, chaque dict et chaque chaîne portant son
    en-tête (facteur mesuré ici : × 4,2).

    La projection ne change **aucun chiffre** : elle retire ce qu'aucune mesure
    n'ouvre. `tests/test_audit_fusion_blocs_599.py` le verrouille des deux côtés
    — le rapport est identique à celui tiré des documents entiers, et le pic
    mémoire reste sous un plafond déclaré.

    Les fichiers de service (nom commençant par un point) sont écartés des deux
    côtés : `.generation_checkpoint.json` n'est pas un profil.
    """
    bruts: dict[str, dict] = {}
    illisibles: list[str] = []
    for slug in slugs_du_repertoire(profils_bruts):
        try:
            socle = charger_socle(profils_bruts / f"{slug}.json")
        except (OSError, json.JSONDecodeError) as exc:
            illisibles.append(f"brut {slug} : {exc}")
            continue
        if isinstance(socle, dict):
            bruts[slug] = projeter_socle(socle)
        del socle

    pivots: dict[str, dict] = {}
    for chemin in sorted(profils_pivot.glob(f"*{SUFFIXE_PIVOT}")):
        if chemin.name.startswith("."):
            continue
        try:
            projection = _lire_pivot(chemin)
        except (OSError, json.JSONDecodeError) as exc:
            illisibles.append(f"pivot {chemin.name} : {exc}")
            continue
        if projection is not None:
            pivots[chemin.name[: -len(SUFFIXE_PIVOT)]] = projection

    return bruts, pivots, illisibles


def porte_des_donnees_parlementaires(profil: dict[str, Any]) -> bool:
    """Vrai si un écrivain parlementaire a travaillé sur ce profil.

    C'est le contrefactuel de toute la mesure : sans donnée parlementaire, un
    bloc pauvre n'a écrasé personne — il est le seul qui existe.
    """
    return any(profil.get(champ) for champ in LISTES_PARLEMENTAIRES)


# ---------------------------------------------------------------------------
# Mesure 1 — `identite` venue d'un écrivain qui n'avait pas la donnée
# ---------------------------------------------------------------------------

def identite_du_chemin_minimal(identite: Any) -> bool:
    """Vrai si ce bloc `identite` EST celui de `build_minimal_profile`.

    Deux conditions, et il faut les deux : la **forme** (les huit clés exactes
    du squelette, ni `lieu_naissance` ni `uri_hatvp`) et le **fond** (rien de
    renseigné hors `nom_complet`/`groupe_nom`, les deux champs que le squelette
    recopie de `raw_data/candidats.json`).

    La forme seule confondrait un profil ancien avec un profil minimal ; le fond
    seul confondrait une collecte AN entièrement en échec — qui est un autre
    défaut, et pas celui-ci.
    """
    if not isinstance(identite, dict):
        return False
    if set(identite) != CLES_IDENTITE_MINIMALE:
        return False
    return not any(
        valeur_de_fond(valeur) is not None
        for champ, valeur in identite.items()
        if champ not in CHAMPS_SANS_SOURCE
    )


def mesurer_identite(
    bruts: dict[str, dict], pivots: dict[str, dict]
) -> dict[str, Any]:
    """Mesure 1 : les identités publiées qu'un écrivain sans donnée a posées.

    Quatre constats distincts, jamais additionnés entre eux — un même profil
    peut en porter plusieurs, et le rapport publie l'union nominative :

    - `brut_squelette_minimal` : le brut porte l'identité du chemin minimal
      alors que le profil porte des données parlementaires. C'est #484 tel
      quel : le bloc d'un écrivain qui n'avait rien a gagné sur celui qui avait
      tout.
    - `pivot_identite_absente` : le pivot ne publie **aucun** bloc `identite`
      alors que le brut du même slug en porte un de fond.
    - `pivot_champ_perdu` : un champ du pivot est `null` alors que le brut du
      même slug porte une valeur pour ce champ.
    - `hatvp_incoherent` : `identite.uri_hatvp` est `null` alors que
      `identifiants.hatvp` du **même profil** porte l'URI. Une source du profil
      pouvait renseigner le champ, et c'est le profil lui-même.
    """
    constats: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hors_defaut: dict[str, list[str]] = defaultdict(list)

    for slug, brut in sorted(bruts.items()):
        cible = hors_defaut if slug in HORS_DEFAUT else None

        identite_brute = brut.get("identite")
        if identite_du_chemin_minimal(identite_brute) and porte_des_donnees_parlementaires(brut):
            if cible is not None:
                cible["brut_squelette_minimal"].append(slug)
            else:
                constats["brut_squelette_minimal"].append({
                    "slug": slug,
                    "listes_non_vides": {
                        champ: nombre_d_entrees(brut.get(champ))
                        for champ in LISTES_PARLEMENTAIRES
                        if brut.get(champ)
                    },
                })

        pivot = pivots.get(slug)
        if pivot is None:
            continue

        identite_pivot = pivot.get("identite")
        champs_de_fond_bruts = {
            champ_pivot: valeur_de_fond((identite_brute or {}).get(champ_brut))
            for champ_brut, champ_pivot in CHAMPS_IDENTITE_BRUT_VERS_PIVOT
        }
        champs_de_fond_bruts = {k: v for k, v in champs_de_fond_bruts.items() if v is not None}

        if not isinstance(identite_pivot, dict):
            if champs_de_fond_bruts:
                if cible is not None:
                    cible["pivot_identite_absente"].append(slug)
                else:
                    constats["pivot_identite_absente"].append({
                        "slug": slug,
                        "champs_connus_du_brut": sorted(champs_de_fond_bruts),
                    })
            continue

        perdus = sorted(
            champ for champ, _ in champs_de_fond_bruts.items()
            if valeur_de_fond(identite_pivot.get(champ)) is None
        )
        if perdus:
            if cible is not None:
                cible["pivot_champ_perdu"].append(slug)
            else:
                constats["pivot_champ_perdu"].append({"slug": slug, "champs": perdus})

        hatvp = valeur_de_fond((pivot.get("identifiants") or {}).get("hatvp"))
        if hatvp is not None and valeur_de_fond(identite_pivot.get("uri_hatvp")) is None:
            if cible is not None:
                cible["hatvp_incoherent"].append(slug)
            else:
                constats["hatvp_incoherent"].append({"slug": slug, "identifiants_hatvp": hatvp})

    touches = sorted({
        entree["slug"] for liste in constats.values() for entree in liste
    })
    return {
        "population_bruts": len(bruts),
        "population_pivots": len(pivots),
        "population_mesuree": len(bruts) - len(HORS_DEFAUT & set(bruts)),
        "hors_defaut_attendu": {k: sorted(v) for k, v in sorted(hors_defaut.items())},
        "constats": {k: v for k, v in sorted(constats.items())},
        "profils_touches": touches,
        "nb_profils_touches": len(touches),
    }


# ---------------------------------------------------------------------------
# Mesure 2 — `meta.warnings` amputé par le meta d'un autre écrivain
# ---------------------------------------------------------------------------

def mesurer_warnings(
    bruts: dict[str, dict], pivots: dict[str, dict], dernier_run: Optional[str]
) -> dict[str, Any]:
    """Mesure 2 : les `meta` pris au dernier écrivain, et ce qu'ils ont effacé.

    Deux constats, tous deux lisibles sur le seul corpus committé :

    - `warnings_reduits_au_chemin_minimal` : le profil porte des données
      parlementaires et son `meta.warnings` **se réduit** au warning du chemin
      minimal. Ce warning affirme « slug absent du référentiel AN, ou identité
      introuvable » ; les votes, mandats et interventions du même fichier le
      démentent. Tous les avertissements de l'écrivain qui les a collectés ont
      disparu avec son `meta`.
    - `collecte_ecartee_absente` : le profil a été **régénéré par le dernier
      run** et porte des données parlementaires, mais pas la clé
      `meta.collecte_ecartee` que l'écrivain AN pose depuis #539. La restriction
      au dernier run n'est pas cosmétique : dix-neuf sénateurs ne sont plus
      régénérés depuis #528 et leur `meta` est légitimement d'avant cette clé —
      les compter serait une mesure juste sur la mauvaise population.
    """
    constats: dict[str, list[dict[str, Any]]] = defaultdict(list)
    hors_defaut: dict[str, list[str]] = defaultdict(list)
    non_regeneres: list[str] = []

    for slug, brut in sorted(bruts.items()):
        cible = hors_defaut if slug in HORS_DEFAUT else None
        meta = brut.get("meta") if isinstance(brut.get("meta"), dict) else {}
        warnings = [w for w in (meta.get("warnings") or []) if isinstance(w, str)]
        parlementaire = porte_des_donnees_parlementaires(brut)

        if parlementaire and warnings and all(
            w.startswith(WARNING_CHEMIN_MINIMAL) for w in warnings
        ):
            if cible is not None:
                cible["warnings_reduits_au_chemin_minimal"].append(slug)
            else:
                constats["warnings_reduits_au_chemin_minimal"].append({
                    "slug": slug,
                    "warnings_publies": warnings,
                    "listes_non_vides": {
                        champ: nombre_d_entrees(brut.get(champ))
                        for champ in LISTES_PARLEMENTAIRES
                        if brut.get(champ)
                    },
                })

        genere_le = (meta.get("genere_le") or "")[:10]
        if dernier_run and genere_le != dernier_run:
            non_regeneres.append(slug)
        elif parlementaire and "collecte_ecartee" not in meta:
            if cible is not None:
                cible["collecte_ecartee_absente"].append(slug)
            else:
                constats["collecte_ecartee_absente"].append({
                    "slug": slug,
                    "cles_meta": sorted(meta),
                })

    # Les warnings que le brut porte et que le pivot ne publie pas. Le pivot en
    # AJOUTE (synchro, chambres, ParlTrack), il n'est pas censé en retirer hors
    # des extinctions explicites de `merge_pivot_profile`.
    non_propages: list[dict[str, Any]] = []
    for slug, brut in sorted(bruts.items()):
        pivot = pivots.get(slug)
        if pivot is None:
            continue
        w_brut = {w for w in ((brut.get("meta") or {}).get("warnings") or []) if isinstance(w, str)}
        w_pivot = {w for w in ((pivot.get("meta") or {}).get("warnings") or []) if isinstance(w, str)}
        manquants = sorted(w_brut - w_pivot)
        if manquants:
            non_propages.append({"slug": slug, "warnings": manquants})

    touches = sorted({
        entree["slug"] for liste in constats.values() for entree in liste
    })
    return {
        "population_bruts": len(bruts),
        "population_mesuree": len(bruts) - len(HORS_DEFAUT & set(bruts)),
        "dernier_run": dernier_run,
        "nb_non_regeneres_par_le_dernier_run": len(non_regeneres),
        "non_regeneres_par_le_dernier_run": non_regeneres,
        "hors_defaut_attendu": {k: sorted(v) for k, v in sorted(hors_defaut.items())},
        "constats": {k: v for k, v in sorted(constats.items())},
        "warnings_du_brut_non_publies_au_pivot": non_propages,
        "profils_touches": touches,
        "nb_profils_touches": len(touches),
    }


# ---------------------------------------------------------------------------
# Mesure 3 — `synchro_sources` recopié en bloc
# ---------------------------------------------------------------------------

#: Sources encore horodatées par le pipeline. `nosdeputes` n'en est plus :
#: #529 l'a retirée de `synchro_sources`, plus aucune requête ne peut la
#: renseigner, et les valeurs encore publiées sont des reliquats que la fusion
#: additive conserve. Une synchro `nosdeputes` périmée est donc un **fait
#: déclaré**, pas un défaut — l'y compter serait un chiffre juste sur la
#: mauvaise population.
SOURCES_ENCORE_ECRITES: frozenset[str] = frozenset({
    "assemblee_nationale",
    "assemblee_nationale_syceron",
    "assemblee_nationale_questions",
})


def mesurer_synchro(bruts: dict[str, dict]) -> dict[str, Any]:
    """Mesure 3 : les fraîcheurs publiées qui sont antérieures au profil.

    **Chaque horodatage de `synchro_sources` est posé par profil**, au moment où
    ce profil-là a interrogé cette source-là (`candidate_profile`, lignes
    4896-5121) — jamais une fois pour tout le corpus. On ne peut donc pas
    prendre le maximum du corpus pour « le moment où le run a interrogé la
    source » : ce serait une inférence fausse, et elle accuserait des profils
    simplement collectés plus tôt dans le même run.

    Ce qui reste mesurable, et qui suffit à #599, c'est l'écart **interne à un
    profil** : `synchro_sources.<source>` antérieure au `genere_le` du même
    fichier. Un horodatage de synchro est posé quelques instants avant le
    `genere_le` du profil qui le porte ; un écart de plusieurs jours ne peut
    venir que d'une valeur **reprise d'un run précédent**.

    Le rapport sépare ensuite ce que cette reprise vaut, parce que les deux cas
    ne se corrigent pas de la même façon :

    - `dont_source_retiree_seulement` — `nosdeputes`, que #529 n'écrit plus : la
      valeur est un reliquat conservé par la fusion additive, et la publier est
      exact.
    - `dont_source_encore_ecrite` — les trois sources AN : le run n'a pas obtenu
      de réponse de cette source **pour ce profil**, et la valeur reprise décrit
      la dernière fois qu'il en a eu une. C'est ce que `_synchro_la_plus_recente`
      publie depuis #597, et c'est **cohérent** — à une condition, qui est
      l'arbitrage à rendre : que le champ signifie « dernière synchro réussie »
      et non « synchro de ce run ».
    - `meta_sans_synchro_sources` — le profil ne porte **aucun** bloc
      `synchro_sources` alors qu'il porte des données parlementaires : ce n'est
      pas une reprise, c'est le `meta` d'un écrivain qui n'a jamais interrogé de
      source, pris en entier. C'est le défaut que #600 corrige.
    """
    dernier_run = None
    genere_le_max = None
    for brut in bruts.values():
        moment = instant((brut.get("meta") or {}).get("genere_le"))
        if moment is not None and (genere_le_max is None or moment > genere_le_max):
            genere_le_max = moment
    if genere_le_max is not None:
        dernier_run = genere_le_max.date().isoformat()

    anterieures: list[dict[str, Any]] = []
    sans_bloc: list[str] = []
    par_source_profils: Counter = Counter()
    par_source_retard_max: dict[str, float] = {}
    porteurs = 0

    for slug, brut in sorted(bruts.items()):
        meta = brut.get("meta") if isinstance(brut.get("meta"), dict) else {}
        synchro = meta.get("synchro_sources")
        if not isinstance(synchro, dict):
            if porte_des_donnees_parlementaires(brut) and slug not in HORS_DEFAUT:
                sans_bloc.append(slug)
            continue
        porteurs += 1
        genere_le = instant(meta.get("genere_le"))
        if genere_le is None:
            continue

        ecarts: dict[str, float] = {}
        for source, valeur in sorted(synchro.items()):
            moment = instant(valeur)
            if moment is None:
                continue
            delta = ecart_jours(genere_le, moment)
            if delta > SEUIL_ECART_JOURS:
                ecarts[source] = round(delta, 2)

        if not ecarts:
            continue
        for source, retard in ecarts.items():
            par_source_profils[source] += 1
            par_source_retard_max[source] = max(par_source_retard_max.get(source, 0.0), retard)
        anterieures.append({
            "slug": slug,
            "genere_le": meta.get("genere_le"),
            "regenere_par_le_dernier_run": (
                dernier_run is not None and genere_le.date().isoformat() == dernier_run
            ),
            "ecarts_jours": ecarts,
            "synchro_publiee": {s: synchro.get(s) for s in ecarts},
            "sources_encore_ecrites": sorted(set(ecarts) & SOURCES_ENCORE_ECRITES),
            "sources_retirees": sorted(set(ecarts) - SOURCES_ENCORE_ECRITES),
        })

    encore_ecrites = [e for e in anterieures if e["sources_encore_ecrites"]]
    retirees_seules = [e for e in anterieures if not e["sources_encore_ecrites"]]
    return {
        "population_bruts": len(bruts),
        "population_porteuse_de_synchro_sources": porteurs,
        "dernier_run": dernier_run,
        "seuil_ecart_jours": SEUIL_ECART_JOURS,
        "anterieure_au_genere_le": anterieures,
        "nb_anterieure_au_genere_le": len(anterieures),
        "dont_source_encore_ecrite": encore_ecrites,
        "nb_dont_source_encore_ecrite": len(encore_ecrites),
        "dont_source_retiree_seulement": [e["slug"] for e in retirees_seules],
        "nb_dont_source_retiree_seulement": len(retirees_seules),
        "meta_sans_synchro_sources": sans_bloc,
        "nb_meta_sans_synchro_sources": len(sans_bloc),
        "profils_par_source": dict(sorted(par_source_profils.items())),
        "retard_max_jours_par_source": {
            s: round(v, 2) for s, v in sorted(par_source_retard_max.items())
        },
    }


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------

def construire_rapport(profils_bruts: Path, profils_pivot: Path) -> dict[str, Any]:
    bruts, pivots, illisibles = charger_corpus(profils_bruts, profils_pivot)
    synchro = mesurer_synchro(bruts)
    return {
        "mesure": "#599 — blocs structurés pris au dernier écrivain",
        "epic": "#598",
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repertoires": {
            "bruts": str(profils_bruts),
            "pivots": str(profils_pivot),
        },
        "fichiers_illisibles": illisibles,
        "hors_defaut": sorted(HORS_DEFAUT),
        "mesure_1_identite": mesurer_identite(bruts, pivots),
        "mesure_2_warnings": mesurer_warnings(bruts, pivots, synchro["dernier_run"]),
        "mesure_3_synchro": synchro,
    }


def _ligne_slugs(entrees: list[dict[str, Any]], limite: int = 30) -> str:
    slugs = [e["slug"] for e in entrees]
    if not slugs:
        return "—"
    if len(slugs) > limite:
        return ", ".join(f"`{s}`" for s in slugs[:limite]) + f", … (+{len(slugs) - limite})"
    return ", ".join(f"`{s}`" for s in slugs)


def rendre_markdown(rapport: dict[str, Any]) -> str:
    m1 = rapport["mesure_1_identite"]
    m2 = rapport["mesure_2_warnings"]
    m3 = rapport["mesure_3_synchro"]
    lignes: list[str] = []
    a = lignes.append

    a("# Lot 0 (#599) — ampleur des blocs pris au dernier écrivain")
    a("")
    a(f"Mesuré le {rapport['genere_le']} sur le corpus committé.")
    a("")
    a("## Populations")
    a("")
    a("| Population | Effectif |")
    a("| --- | ---: |")
    a(f"| Profils bruts lus (`{rapport['repertoires']['bruts']}`) | {m1['population_bruts']} |")
    a(f"| Profils pivot publiés (`{rapport['repertoires']['pivots']}`) | {m1['population_pivots']} |")
    a(f"| Profils comptés à part (identité AN absente **attendue**) | {len(rapport['hors_defaut'])} |")
    a(f"| **Population du défaut** (bruts moins ces quatre) | **{m1['population_mesuree']}** |")
    a(f"| Profils non régénérés par le run du {m2['dernier_run']} | {m2['nb_non_regeneres_par_le_dernier_run']} |")
    a("")
    a(f"Comptés à part : {', '.join('`' + s + '`' for s in rapport['hors_defaut'])}.")
    a("")

    a("## Mesure 1 — `identite` venue d'un écrivain qui n'avait pas la donnée")
    a("")
    a(f"Population : les **{m1['population_mesuree']}** profils bruts hors les quatre comptés à part.")
    a("")
    a("| Constat | Profils | Lesquels |")
    a("| --- | ---: | --- |")
    for cle, libelle in (
        ("brut_squelette_minimal", "Le brut porte l'identité du chemin minimal **et** des données parlementaires"),
        ("pivot_identite_absente", "Le pivot ne publie aucun bloc `identite` alors que le brut en porte un de fond"),
        ("pivot_champ_perdu", "Un champ du pivot est `null` alors que le brut du même slug le renseigne"),
        ("hatvp_incoherent", "`identite.uri_hatvp` est `null` alors qu'`identifiants.hatvp` du même profil porte l'URI"),
    ):
        entrees = m1["constats"].get(cle, [])
        a(f"| {libelle} | {len(entrees)} | {_ligne_slugs(entrees)} |")
    a(f"| **Union nominative** | **{m1['nb_profils_touches']}** | {', '.join('`' + s + '`' for s in m1['profils_touches']) or '—'} |")
    a("")
    if m1["hors_defaut_attendu"]:
        a("Parmi les quatre comptés à part, et **attendus** :")
        a("")
        for cle, slugs in m1["hors_defaut_attendu"].items():
            a(f"- `{cle}` : {', '.join('`' + s + '`' for s in slugs)}")
        a("")

    a("## Mesure 2 — `meta` pris au dernier écrivain")
    a("")
    a(f"Population : les **{m2['population_mesuree']}** profils bruts hors les quatre comptés à part.")
    a("")
    a("| Constat | Profils | Lesquels |")
    a("| --- | ---: | --- |")
    for cle, libelle in (
        ("warnings_reduits_au_chemin_minimal", "`meta.warnings` réduit au seul warning du chemin minimal, sur un profil qui porte des données parlementaires"),
        ("collecte_ecartee_absente", "Régénéré par le dernier run, données parlementaires, mais pas de `meta.collecte_ecartee`"),
    ):
        entrees = m2["constats"].get(cle, [])
        a(f"| {libelle} | {len(entrees)} | {_ligne_slugs(entrees)} |")
    a(f"| **Union nominative** | **{m2['nb_profils_touches']}** | {', '.join('`' + s + '`' for s in m2['profils_touches']) or '—'} |")
    a("")
    non_propages = m2["warnings_du_brut_non_publies_au_pivot"]
    a(f"Warnings portés par un brut et absents de son pivot : **{len(non_propages)}** profils"
      f" sur les {m1['population_pivots']} pivots publiés"
      f"{' — ' + _ligne_slugs(non_propages) if non_propages else ''}.")
    a("")

    a("## Mesure 3 — `synchro_sources` antérieur au profil qui le publie")
    a("")
    a(f"Population : les **{m3['population_porteuse_de_synchro_sources']}** profils bruts"
      f" qui portent un bloc `meta.synchro_sources`, sur {m3['population_bruts']}.")
    a("")
    a("| Lecture | Profils | Lesquels |")
    a("| --- | ---: | --- |")
    a(f"| Au moins une synchro antérieure de plus de {m3['seuil_ecart_jours']} j au `genere_le`"
      f" du même profil (lecture littérale de #599) | {m3['nb_anterieure_au_genere_le']}"
      f" | {_ligne_slugs(m3['anterieure_au_genere_le'])} |")
    a(f"| … dont l'écart ne porte que sur `nosdeputes`, source retirée par #529 :"
      f" un reliquat exact, **pas un défaut** | {m3['nb_dont_source_retiree_seulement']}"
      f" | {', '.join('`' + s + '`' for s in m3['dont_source_retiree_seulement']) or '—'} |")
    a(f"| … dont l'écart porte sur une source **encore écrite** par le pipeline"
      f" | {m3['nb_dont_source_encore_ecrite']} | {_ligne_slugs(m3['dont_source_encore_ecrite'])} |")
    a(f"| Aucun bloc `synchro_sources` du tout, sur un profil qui porte des données"
      f" parlementaires (**le `meta` d'un écrivain sans source, pris entier**)"
      f" | {m3['nb_meta_sans_synchro_sources']}"
      f" | {', '.join('`' + s + '`' for s in m3['meta_sans_synchro_sources']) or '—'} |")
    a("")
    a("| Source | Profils dont la synchro précède leur `genere_le` | Retard max | Encore écrite ? |")
    a("| --- | ---: | ---: | --- |")
    for source, nb in m3["profils_par_source"].items():
        ecrite = "oui" if source in SOURCES_ENCORE_ECRITES else "non (#529)"
        a(f"| `{source}` | {nb} | {m3['retard_max_jours_par_source'][source]} j | {ecrite} |")
    a("")
    if m3["dont_source_encore_ecrite"]:
        a("Détail, sources encore écrites :")
        a("")
        a("| Profil | `genere_le` | Régénéré par le dernier run | Source | Synchro publiée | Écart |")
        a("| --- | --- | --- | --- | --- | ---: |")
        for entree in m3["dont_source_encore_ecrite"]:
            for source in entree["sources_encore_ecrites"]:
                a(f"| `{entree['slug']}` | {entree['genere_le']}"
                  f" | {'oui' if entree['regenere_par_le_dernier_run'] else 'non'}"
                  f" | `{source}` | {entree['synchro_publiee'][source]}"
                  f" | {entree['ecarts_jours'][source]} j |")
        a("")
    if rapport["fichiers_illisibles"]:
        a("## Fichiers illisibles")
        a("")
        for ligne in rapport["fichiers_illisibles"]:
            a(f"- {ligne}")
        a("")
    return "\n".join(lignes)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--profils-bruts", default="raw_data/profiles", type=Path)
    parser.add_argument("--profils-pivot", default="pivot_data/profiles", type=Path)
    parser.add_argument("--json", type=Path, help="Chemin du rapport JSON à écrire.")
    parser.add_argument("--markdown", type=Path, help="Chemin du rapport Markdown à écrire.")
    args = parser.parse_args(argv)

    rapport = construire_rapport(args.profils_bruts, args.profils_pivot)
    markdown = rendre_markdown(rapport)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(markdown + "\n", encoding="utf-8")

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
