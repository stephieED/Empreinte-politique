#!/usr/bin/env python3
"""
normalize_europarl.py — Adaptateur Open Data Portal du Parlement européen → schéma pivot v1.

Convertit la sortie brute de `candidate_profile_ue.build_profile_ue()` en un
profil pivot v1 (défini dans `schema_pivot.py`).

Usage :
    from normalize_europarl import normalize_europarl
    pivot = normalize_europarl(raw_ue_profile, parti="Rassemblement National")
"""

import time
from typing import Any, Optional

from licences import appliquer_licence_donnees
from schema_pivot import appliquer_chambres, make_empty_profil, poser_identifiant

# Correspondance entre le type brut de l'API EP et la catégorie pivot.
_CATEGORIE_MAP: dict[str, str] = {
    "EU_INSTITUTION": "mandat_electif",
    "COMMITTEE_PARLIAMENTARY_STANDING": "commission",
    "COMMITTEE_PARLIAMENTARY_TEMPORARY": "commission",
    "COMMITTEE_PARLIAMENTARY_SUB": "commission",
    "DELEGATION_PARLIAMENTARY": "autre",
    "DELEGATION_PARLIAMENTARY_ASSEMBLY": "autre",
    "WORKING_GROUP": "commission",
    "EU_POLITICAL_GROUP": "autre",
    "NATIONAL_POLITICAL_GROUP": "autre",
    "GOVERNING_BODY": "autre",
}

#: #863 — la nature de l'organe **telle que le portail européen la classe**,
#: traduite dans la nomenclature fermée de `schema_pivot`. `categorie` dit
#: comment le pivot range l'entrée ; ceci dit ce que la source en dit, et c'est
#: ce qui permet à l'interface de reconnaître un groupe politique européen sans
#: lire son intitulé. Un `type` que la source ne classe pas (`AUTRE`) n'entre
#: pas dans cette table : la clé reste alors **absente**, ce qui est un sens.
_TYPE_ORGANE_SOURCE: dict[str, str] = {
    "EU_POLITICAL_GROUP": "groupe_politique_europeen",
    "NATIONAL_POLITICAL_GROUP": "parti_national_au_parlement_europeen",
    "COMMITTEE_PARLIAMENTARY_STANDING": "commission_parlementaire_europeenne",
    "COMMITTEE_PARLIAMENTARY_TEMPORARY": "commission_parlementaire_europeenne",
    "COMMITTEE_PARLIAMENTARY_SUB": "commission_parlementaire_europeenne",
    "DELEGATION_PARLIAMENTARY": "delegation_parlementaire_europeenne",
    "DELEGATION_PARLIAMENTARY_ASSEMBLY": "delegation_parlementaire_europeenne",
    "WORKING_GROUP": "groupe_de_travail_europeen",
    "GOVERNING_BODY": "organe_dirigeant_europeen",
    "EU_INSTITUTION": "mandat_parlementaire_europeen",
}

#: Un sigle publié par le portail est parfois l'identifiant d'organisation que
#: la résolution n'a pas su résoudre — mesuré : `"2953"` sur `stephane-le-foll`,
#: avec `organisation_nom` à `null`. Un identifiant n'est pas un sigle, et le
#: publier comme tel inventerait une donnée (§2 règle 5).
def _sigle_publiable(mandat_source: dict[str, Any]) -> tuple[Optional[str], Optional[dict[str, Any]]]:
    """Rend (sigle, non_resolu). L'un des deux est toujours `None`."""
    sigle = (mandat_source.get("organisation_sigle") or "").strip()
    if not sigle:
        return None, {"raison": "aucun sigle publié par la source"}
    if not mandat_source.get("organisation_nom"):
        return None, {
            "raison": "organisation non résolue : le portail n'a rendu qu'un identifiant",
            "valeur_source": sigle,
        }
    return sigle, None


#: Le type que le portail européen emploie quand il ne classe pas l'appartenance.
TYPE_NON_CLASSE = "AUTRE"


def dedupliquer_appartenances(
    mandats_europeens: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Rend (appartenances conservées, doublons écartés).

    **Le portail européen publie deux fois la même appartenance** : mesuré le
    12/09/2026 sur le corpus, **42 mandats de député européen sur 29 profils**
    arrivent en paire pour la même législature — l'un `role: MEMBER_PARLIAMENT`
    et `type: "AUTRE"`, l'autre `role: MEMBER` et `type: "EU_INSTITUTION"`. La
    normalisation les rendait fidèlement tous les deux, et la fiche publiait le
    même mandat deux fois, une fois en `autre`, une fois en `mandat_electif`.
    C'est visible : la frise du parcours compte des segments.

    **Le critère est étroit, et c'est délibéré.** Une paire n'est réduite que si
    elle porte la même organisation et **exactement** la même période, et que
    l'un des deux membres est **non classé** par la source. Deux entrées de même
    organisation et même période mais toutes deux classées sont conservées : ce
    sont deux fonctions distinctes (membre et vice-président d'une commission),
    et les confondre perdrait un fait (§2 règle 2).

    L'entrée gardée est celle que la source **classe** — jamais un choix de
    notre part sur laquelle est la bonne. Mais la classification et le libellé
    de rôle ne sont pas portés par la même entrée : `EU_INSTITUTION` dit le
    **type** (« Mandat de député européen ») sous un rôle générique
    (`MEMBER`/« Membre »), tandis que l'entrée non classée porte le rôle
    explicite (`MEMBER_PARLIAMENT`/« Membre du Parlement européen »). Les deux
    décrivent la **même** appartenance : on garde la classification de l'une et
    le libellé de rôle de l'autre, tous deux lus dans la source.

    Mesuré le 12/09/2026 sur les profils bruts : les deux formes valent **42
    occurrences chacune**, toujours appariées, et la seule organisation
    concernée est « Mandat de député européen ». Aucune entrée `EU_INSTITUTION`
    ne porte un autre rôle que `MEMBER` — c'est ce qui permet de dire que le
    rôle générique désigne bien ici le mandat, et non l'inverse.
    """
    rang = {id(m): i for i, m in enumerate(mandats_europeens)}
    par_appartenance: dict[tuple, list[dict[str, Any]]] = {}
    for m in mandats_europeens:
        cle = (
            (m.get("organisation_nom") or m.get("organisation_sigle") or "").strip(),
            m.get("debut"),
            m.get("fin"),
        )
        par_appartenance.setdefault(cle, []).append(m)

    # L'ordre d'origine est celui du portail (du plus récent au plus ancien) et
    # `_extract_groupe` s'en sert : chaque entrée conservée garde le rang de
    # l'entrée dont elle provient, y compris quand c'est une copie enrichie.
    conserves_rangs: list[tuple[int, dict[str, Any]]] = []
    ecartes: list[dict[str, Any]] = []
    for entrees in par_appartenance.values():
        non_classes = [m for m in entrees if (m.get("type") or "") == TYPE_NON_CLASSE]
        classes = [m for m in entrees if (m.get("type") or "") != TYPE_NON_CLASSE]
        if len(entrees) > 1 and non_classes and classes:
            garde = dict(classes[0])
            explicite = next(
                (m for m in non_classes if (m.get("role") or "") == "MEMBER_PARLIAMENT"), None
            )
            if explicite and (garde.get("role") or "") == "MEMBER":
                # Le rôle explicite de la source ne se perd pas parce que c'est
                # l'autre entrée de la paire qui le porte.
                garde["role"] = explicite.get("role") or garde.get("role")
                garde["role_label"] = explicite.get("role_label") or garde.get("role_label")
            conserves_rangs.append((rang[id(classes[0])], garde))
            conserves_rangs.extend((rang[id(m)], m) for m in classes[1:])
            ecartes.extend(non_classes)
        else:
            conserves_rangs.extend((rang[id(m)], m) for m in entrees)

    conserves = [m for _, m in sorted(conserves_rangs, key=lambda couple: couple[0])]
    return conserves, ecartes


def _extract_groupe(mandats_europeens: list[dict[str, Any]]) -> Optional[str]:
    """Retourne le nom du groupe politique européen le plus récent (actif en priorité)."""
    # La liste est déjà triée du plus récent au plus ancien par candidate_profile_ue.
    for m in mandats_europeens:
        if m.get("type") == "EU_POLITICAL_GROUP" and m.get("actif"):
            return m.get("organisation_nom") or m.get("organisation_sigle")
    for m in mandats_europeens:
        if m.get("type") == "EU_POLITICAL_GROUP":
            return m.get("organisation_nom") or m.get("organisation_sigle")
    return None


def normalize_europarl(
    ue_profile: dict[str, Any],
    parti: Optional[str] = None,
    provenance: str = "candidat_declare",
    slug: Optional[str] = None,
) -> dict[str, Any]:
    """Convertit un profil Open Data Portal Parlement européen en pivot v1.

    Args:
        ue_profile: sortie de `candidate_profile_ue.build_profile_ue()`.
        parti: parti politique issu de raw_data/candidats.json (optionnel).
        provenance: "candidat_declare" (défaut) ou "roster_groupe" — voir
                    schema_pivot.KNOWN_PROVENANCES. Propagé tel quel vers
                    meta.provenance du profil pivot.
        slug: slug du profil, c'est-à-dire son identifiant (#487, épic #486).
              Fourni, il devient l'`id` tel quel — même convention que
              `normalize_profil`, pour que l'espace d'identifiants pivot
              n'ait qu'une seule forme.
              Absent, l'`id` retombe sur `europarl:<identifiant_pe>`. Ce repli
              n'est pas une exception de confort : `ue_profile` ne porte pas de
              slug, et le seul candidat qu'on pourrait en tirer serait dérivé
              de `nom_complet`, donc d'une donnée de collecte — exactement le
              défaut que #487 retire. Mieux vaut un identifiant de source
              explicite qu'un slug inventé.

    Returns:
        Profil pivot v1 dict (chambre: "PE").
    """
    mep_id = str(ue_profile["identifiant_pe"]) if ue_profile.get("identifiant_pe") is not None else ""
    nom = ue_profile.get("nom_complet") or None
    url_source = ue_profile.get("url_source") or None
    meta_ue = ue_profile.get("meta") or {}
    synchro_le = meta_ue.get("genere_le") or time.strftime("%Y-%m-%dT%H:%M:%S%z")

    profil_id = slug if slug else f"europarl:{mep_id}"
    profil = make_empty_profil(id_=profil_id, nom=nom, provenance=provenance)
    # #539 : l'identifiant PE est publié **nommé**, dans `identifiants`. C'est lui
    # qui préfixait l'`id` de `jordan-bardella` (`europarl:131580`) — le seul du
    # corpus dont l'identité portait encore une source. Le retirer de l'`id` ne
    # coûte donc rien en traçabilité : il est ici, et il est dit.
    poser_identifiant(profil, "europarl", mep_id)
    # `chambres`/`chambre` sont dérivées en fin de fonction, une fois `mandats[]`
    # construit (#493) : une seule fabrique pour les deux champs.
    profil["parti"] = parti
    profil["sources"] = [
        {
            "type": "europarl",
            "url": url_source,
            "synchro_le": synchro_le,
        }
    ]
    # `licence_donnees` est DÉRIVÉ de `sources[]` (#530, lot 6) : une seule
    # fabrique pour tout le corpus, au lieu d'un libellé propagé depuis le profil
    # brut. Sur les données réelles la valeur est identique — `candidate_profile_ue`
    # écrivait déjà `licences.LICENCE_EUROPARL` mot pour mot ; ce qui change, c'est
    # qu'un profil AN + PE cesse de publier la seule licence de sa branche AN.
    appliquer_licence_donnees(profil)
    profil["meta"]["genere_le"] = synchro_le

    # --- Identité (#922) ----------------------------------------------------
    #
    # Ce normaliseur ne posait AUCUN bloc `identite`, et la conséquence ne se
    # voyait pas ici : elle se voyait dans l'appariement au Répertoire national
    # des élus, dont la clé praticable est (nom, prénom, date de naissance).
    # Les quatre candidats déclarés dont tout le parcours est européen —
    # Bardella, Philippot, Massard, Glucksmann — ressortaient « sans date de
    # naissance », donc non appariables automatiquement, alors que le portail
    # européen la publie et que le profil BRUT la portait déjà sous
    # `mandat_europeen.date_naissance`. Elle s'arrêtait à la normalisation.
    #
    # Recopiés **verbatim**, et `null` quand la source ne donne rien (§2 règle 5).
    # Le portail écrit parfois un lieu mal espacé — « Saint- Brieuc » — et ce
    # n'est pas corrigé : c'est ce que la source publie, et le réparer
    # supposerait de savoir où le mot se coupe.
    identite_ue = {
        "date_naissance": ue_profile.get("date_naissance") or None,
        "lieu_naissance": ue_profile.get("lieu_naissance") or None,
        "source_url": url_source,
    }
    if any(v for k, v in identite_ue.items() if k != "source_url"):
        profil["identite"] = identite_ue

    mandats_europeens, doublons_source = dedupliquer_appartenances(
        ue_profile.get("mandats_europeens") or []
    )
    if doublons_source:
        # Constat sur la source, pas sur la personne : il se compte, il ne
        # s'invente pas (§2 règle 5).
        profil["meta"].setdefault("avertissements", []).append(
            f"mandats européens : {len(doublons_source)} appartenance(s) publiée(s) deux fois "
            "par le portail européen, la non classée a été écartée"
        )
    profil["groupe"] = _extract_groupe(mandats_europeens)

    for m in mandats_europeens:
        categorie = _CATEGORIE_MAP.get(m.get("type") or "", "autre")
        label = m.get("organisation_nom") or m.get("organisation_sigle") or ""
        fonction = m.get("role_label") or m.get("role") or ""
        sigle, sigle_non_resolu = _sigle_publiable(m)
        type_organe = _TYPE_ORGANE_SOURCE.get(m.get("type") or "")
        mandat: dict[str, Any] = {
            "label": label,
            "categorie": categorie,
            # #718 — la catégorie vient de `_CATEGORIE_MAP`, donc du `type`
            # d'organisation publié par le Parlement européen. Un `autre` de
            # repli est estampillé lui aussi : ce qui est établi, c'est QUI a
            # classé, pas la finesse du classement.
            "categorie_source": "europarl",
            "fonction": fonction,
            "debut": m.get("debut"),
            "fin": m.get("fin"),
            "actif": bool(m.get("actif")),
            "source_url": url_source,
            "sigle_organe": sigle,
        }
        if sigle_non_resolu:
            mandat["sigle_organe_non_resolu"] = sigle_non_resolu
        if type_organe:
            # Absente quand la source ne classe pas l'appartenance (`AUTRE`) :
            # l'absence dit « la source ne l'a pas classée », jamais « autre ».
            mandat["type_organe_source"] = type_organe
        if categorie == "mandat_electif":
            # #492 : seul cas où la chambre est établie sans ambiguïté par la
            # source elle-même — le mandat vient du Parlement européen, et son
            # `source_url` pointe déjà sur europarl.europa.eu. C'est aussi le
            # seul `mandat_electif` du corpus qui porte une `source_url` (14 sur
            # 228, mesuré sur `f5a828b`).
            mandat["chambre"] = "PE"
        profil["mandats"].append(mandat)

    # #493 : `chambres` dérivée des mandats estampillés ci-dessus. Le repli
    # `"PE"` couvre le seul cas restant — un profil européen sans aucun
    # `mandat_electif` (`mandats_europeens` ne portant que des groupes/commissions) :
    # la chambre reste alors une donnée de source, le Parlement européen étant la
    # seule chambre que ce normaliseur sache lire.
    profil["chambre"] = "PE"                 # repli, consommé par appliquer_chambres
    appliquer_chambres(profil)

    return profil
