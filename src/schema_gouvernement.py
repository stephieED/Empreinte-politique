#!/usr/bin/env python3
"""
schema_gouvernement.py — Schéma pivot du profil de gouvernement v1.

Ce module définit le contrat de structure du « profil de gouvernement »,
document agrégé calculé à partir de plusieurs profils pivot individuels
(schéma pivot v1, `schema_pivot.py`) partageant une appartenance à un même
gouvernement (mandats de catégorie `fonction_gouvernementale`) ainsi que des
dossiers législatifs déposés à l'initiative de ce gouvernement.

Entité séparée, pas un enrichissement de `schema_pivot.py` : un gouvernement
est un agrégat calculé à partir de plusieurs profils pivot, au même niveau
conceptuel que `schema_groupe.py` (profil de groupe parlementaire), pas un
enrichissement du pivot individuel. Décision actée dans le plan
d'implémentation de #184 (issue #208).

Il ne contient aucune logique de collecte ni de calcul : c'est un contrat de
structure (constantes, fabrique, validateur). La logique d'agrégation revient
à un futur `gouvernement_profile.py` (hors périmètre de cette issue).

Principe directeur : faits chiffrés uniquement, aucune interprétation.

Format d'un profil de gouvernement v1 :
{
    "schema_version": "1",
    "type_document": "profil_gouvernement",
    "gouvernement_id": "gouvernement:LECORNU",  # "gouvernement:<libelle_abrege_an>"
    "nom": "Gouvernement Lecornu",

    "premier_ministre": {                    # null si non renseigné
        "nom": "Sébastien Lecornu",
        "acteur_ref": "PA607469",            # identifiant du référentiel AN (acteurRef), si connu
        "source_url": "https://www.assemblee-nationale.fr/dyn/...",
    },

    "periode": {
        "debut": "2025-09-09",
        "fin": None,
        "actif": True,
    },

    "membres": [                             # un enregistrement par ministre (et par période
                                              # si changement de portefeuille)
        {
            "membre_id": "bruno-le-maire",       # id pivot individuel (= son slug, #487), si connu
            "nom": "Bruno Le Maire",
            "portefeuille": None,            # jamais de placeholder textuel : null tant que la
                                              # source primaire n'a pas été vérifiée (voir
                                              # docs/decisions/hors-perimetre.md,
                                              # § "Ministerial function")
            "debut": "2025-09-09",
            "fin": None,
            "actif": True,
            "source_url": None,              # obligatoire dès que 'portefeuille' est renseigné
        }
    ],

    "textes": [                              # dossiers législatifs déposés à l'initiative de
                                              # ce gouvernement
        {
            "dossier_id": "DLR5L17N50588",
            "titre": "Projet de loi de financement de la sécurité sociale 2025",
            "statut": "adopte_49_3",         # cf. KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL
            "chambre_depot_initial": "AN",   # "AN" | "Senat" — un gouvernement n'est pas
                                              # rattaché à une chambre ; c'est chaque texte qui
                                              # l'est, individuellement
            "date_depot": "2024-10-10",
            "date_dernier_evenement": "2024-12-04",
            "sort_49_3": True,               # engagement de la responsabilité du gouvernement
                                              # (art. 49.3) : bool, jamais fusionné avec une
                                              # position de vote (règle AGENTS.md §2.4)
            "initiateurs": [                 # ministre(s) ayant déposé le texte, tels que
                {                            # déclarés par `initiateur.acteurs.acteur[]` du
                                              # dump AN — un texte en porte souvent plusieurs
                    "acteur_ref": "PA643210",  # référence AN brute, toujours conservée
                    "membre_id": "sebastien-lecornu",  # null si l'acteur ne figure
                },                             # pas dans membres[] (couverture partielle)
            ],                               # null (jamais []) si la source n'en déclare aucun
            "source_url": None,
            # #689 — la commission saisie AU FOND du dossier, lue dans
            # `pivot_data/commissions_dossiers.json` par `dossier_id`. C'est ce
            # qui permet de lire les lois d'un gouvernement par matière sans
            # inventer de taxonomie : l'Assemblée renvoie elle-même chaque
            # dossier à une commission.
            "commission_saisie_au_fond": {
                "organe_ref": "PO420120",
                "sigle": "Affaires sociales",
                "nom": "Commission des affaires sociales",
                "type": "COMPER",   # verbatim de l'organe : `COMPER` permanente,
                                    # `CNPS` spéciale — créée pour CE texte. Le
                                    # partage vient de l'Assemblée, pas d'un seuil
                                    # que nous choisirions (§2 règle 1).
            },
            # Présent SEULEMENT quand la précédente est `null`, et il l'explique.
            # Une absence de cause connue se déclare, elle ne se comble pas
            # (AGENTS.md §2 règle 5) : les 174 textes déposés au Sénat n'ont pas
            # de commission au fond dans un référentiel qui est celui de l'AN,
            # et le Sénat est hors périmètre (#528).
            "commission_non_resolue": {"motif": "depot_senat"},
        }
    ],

    # #1020 — SUR QUOI LES MEMBRES ONT PRIS LA PAROLE, pendant leur passage.
    #
    # Une étiquette compte UNE FOIS PAR MEMBRE : l'agrégat dit combien de
    # personnes ont parlé d'un sujet, jamais combien de fois — un compte
    # d'occurrences serait un indice d'activité (§2 règle 1). Et il ne porte
    # AUCUN ratio : son dénominateur est `comptages.membres_avec_interventions`,
    # publié à côté plutôt que pré-divisé (§2.7).
    #
    # Les étiquettes sont celles de `tags_thematiques` du pivot — les intitulés
    # des points de séance (`theme_officiel`), donc des aides à la lecture et
    # jamais des positions déclarées (§2 règle 8).
    #
    # Le filtre est la fenêtre de passage DU MEMBRE, pas la période du
    # gouvernement : voir `gouvernement_profile.agreger_tags_thematiques`, et
    # ce qu'il retire (Yaël Braun-Pivet, 8 968 entrées → 0).
    "tags_thematiques_agreges": [
        {"tag": "projet de loi de finances pour 2026", "nb_membres_porteurs": 12},
    ],

    "comptages": {                           # entiers bruts uniquement — aucun taux, pourcentage
                                              # ou classement (règle AGENTS.md §2.1)
        # #996 : combien de PERSONNES l'AN recense dans ce gouvernement,
        # qu'elles aient un profil chez nous ou non. `null` quand la liste des
        # gouvernements ne le porte pas.
        "membres_recenses": 21,
        # #996 lot 4 : combien de personnes DISTINCTES `membres[]` porte.
        #
        # Les deux nombres existent parce que `membres[]` ne compte pas des
        # personnes : il porte une entrée par PÉRIODE — un ministre qui change
        # de portefeuille en cours de gouvernement en a plusieurs (#398).
        # Mesuré le 18/09/2026 sur les 17 fiches : 770 entrées pour 650
        # personnes, et Fillon II à lui seul 89 entrées pour 52 personnes.
        #
        # Sans ce compteur, `len(membres)` et `membres_recenses` sont deux
        # nombres de populations différentes posés côte à côte, et « 89 des 52
        # membres recensés » est ce qu'on lit. Le rapprochement qui a un sens
        # est `membres_distincts` / `membres_recenses` — et il reste deux
        # entiers, jamais un taux (§2 règle 7, et le commentaire ci-dessus).
        "membres_distincts": 19,
        # #1020 : combien de membres portent au moins une intervention DANS
        # leur fenêtre de passage. C'est le dénominateur de
        # `tags_thematiques_agreges[].nb_membres_porteurs`, publié plutôt que
        # pré-divisé (§2.7) — et il rend la couverture lisible : tant que tous
        # les membres n'ont pas leurs interventions collectées, il est plus
        # petit que `membres_distincts`, et l'écart se VOIT au lieu d'être
        # dilué dans un pourcentage.
        "membres_avec_interventions": 12,
        "par_statut": {
            "depose": 0,
            "navette_en_cours": 0,
            "adopte": 0,
            "adopte_49_3": 1,
            "rejete": 0,
            "rejete_49_3": 0,
            "retire": 0,
        }
    },

    "sources": [                             # traçabilité des sources individuelles agrégées
        {
            "type": "assemblee_nationale",
            "url": "https://data.assemblee-nationale.fr/...",
            "synchro_le": "2026-07-29T10:00:00+0000",
        }
    ],

    "meta": {
        "schema_version": "1",
        "genere_le": "2026-07-29T10:00:00+0000",
        "licence_donnees": "",
        "warnings": [],
    },
}

Cas limites gérés :
- Ministre sans portefeuille confirmé par une source primaire :
  `portefeuille` reste `null` (jamais une chaîne placeholder du type
  "Ministre" ou "À déterminer") ; dès que `portefeuille` est renseigné,
  `source_url` devient obligatoire (même logique que
  `mandats[].position_dans_hemicycle` du pivot individuel, voir
  `schema_pivot.py`).
- Texte adopté via l'article 49.3 : `statut = "adopte_49_3"` **et**
  `sort_49_3 = True` sont exigés ensemble ; il est interdit de renseigner
  `sort_49_3 = True` avec `statut = "adopte"` (collapse silencieux vers une
  adoption « normale », interdit par la règle AGENTS.md §2.4), et interdit de
  renseigner `statut = "adopte_49_3"` sans `sort_49_3 = True`.
- Texte rejeté via l'article 49.3 (motion de censure adoptée) : même logique,
  symétrique, avec `statut = "rejete_49_3"` — `sort_49_3 = True` est exigé
  avec ce statut, et interdit de le renseigner avec `statut = "rejete"`
  (même collapse silencieux interdit que pour `adopte`).
- Texte dont la source ne déclare aucun initiateur : `initiateurs = null`,
  jamais `[]` ni un membre choisi par défaut (règle AGENTS.md §2.5) — une
  liste vide affirmerait qu'aucun ministre n'a porté le texte, ce que la
  source ne dit pas. Constaté sur 2 des 725 textes rattachés à un
  gouvernement (#435).
- Initiateur absent de `membres[]` : `acteur_ref` est conservé et
  `membre_id` reste `null` — la couverture des profils pivot est partielle
  (7 Premiers ministres n'en ont aucun), et un `membre_id` reconstruit serait
  une invention. Un `membre_id` renseigné doit correspondre à une entrée de
  `membres[]` (vérifié par `validate_profil_gouvernement`).
- Gouvernement encore en fonction : `periode.fin = null`, `periode.actif = true`.

Hors périmètre de ce schéma (volontairement) :
- Aucun champ de type "chambre(s) couvertes" au niveau racine : un
  gouvernement n'est pas rattaché à une chambre, contrairement à un groupe
  parlementaire (`schema_groupe.py`) — seul `textes[].chambre_depot_initial`
  porte cette information, par texte.
- Aucun taux, pourcentage ou ratio nulle part dans ce schéma : `comptages`
  n'expose que des entiers bruts (règle AGENTS.md §2.1). Si un futur besoin
  éditorial réclame un taux (ex. part des textes adoptés via 49.3), il devra
  être calculé côté présentation (`web/`), jamais stocké ici.
- `KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL` est définie ici, pas dans
  `schema_pivot.py` : ce concept d'« issue » d'un dossier (résultat final)
  n'existe pas encore côté pivot individuel, et est distinct de
  `KNOWN_STADES_PROCEDURAUX` (`schema_pivot.py`), qui encode une progression
  procédurale, pas une issue.
- Pas de collecte de données réelle ni d'intégration à
  `check_quality_gate.py` : schéma et validation uniquement (sous-issues #3,
  #4, #6 de #184).

Usage :
    from schema_gouvernement import (
        SCHEMA_GOUVERNEMENT_VERSION,
        make_empty_profil_gouvernement,
        validate_profil_gouvernement,
    )
"""

import time
from typing import Any

# Version du schéma de gouvernement ; indépendante de SCHEMA_VERSION du pivot
# individuel et de SCHEMA_GROUPE_VERSION du profil de groupe parlementaire.
SCHEMA_GOUVERNEMENT_VERSION = "1"

#: Pourquoi un texte ne porte pas sa commission saisie au fond (#689). Fermé, et
#: chaque motif se répare ailleurs : `depot_senat` est une limite de PÉRIMÈTRE
#: (#528) et ne se réparera pas, `absente_de_l_index` est un trou de l'index AN,
#: `index_indisponible` est une panne du run. Les confondre ferait passer une
#: décision éditoriale pour une panne.
KNOWN_MOTIFS_COMMISSION_NON_RESOLUE: frozenset[str] = frozenset({
    "depot_senat",
    "absente_de_l_index",
    "index_indisponible",
})

# Nomenclature fermée de l'issue d'un texte porté par le gouvernement.
# Distincte de KNOWN_STADES_PROCEDURAUX (schema_pivot.py) qui encode une
# progression procédurale, pas une issue. adopte_49_3/rejete_49_3 restent des
# statuts séparés d'adopte/rejete : le 49.3 est un fait procédural, jamais une
# position de vote ni un "blocage" (règle AGENTS.md §2.4) — voir
# validate_profil_gouvernement pour le refus explicite de tout collapse
# silencieux. rejete_49_3 (fam_code AN `TSORTF24` : motion de censure adoptée
# après engagement de l'article 49.3, ex. le budget 2025 sous le gouvernement
# Barnier) a été ajouté après coup : la nomenclature initiale (#208) n'avait
# anticipé le 49.3 que comme voie d'adoption, pas de rejet — gap découvert
# lors de la collecte réelle en #210, cf. docs/technical_decisions.md
# #gouvernement-textes-statut.
#
# adopte_cmp (fam_code AN `TSORTF18` : « adopté, dans les conditions prévues à
# l'article 45, alinéa 3, de la Constitution » — approbation du texte élaboré
# en commission mixte paritaire, sur demande du Gouvernement) suit la même
# logique que les statuts 49.3 : l'issue est bien une adoption, mais la voie
# procédurale est distincte et ne doit pas être fondue dans `adopte`
# (AGENTS.md §2.4). Ajouté en #397, où son absence excluait 16 textes du jeu
# de données — dont le PLF 2025. Voir docs/technical_decisions.md
# #gouvernement-textes-fam-codes-manquants.
#
# promulgue (acte AN `PROM`/`PROM-PUB` : publication au Journal officiel) est
# le fait le plus avancé et le plus vérifiable du parcours d'un texte. Ajouté
# en #400 : l'ingestion des archives XV/XVI a fait remonter 62 textes dont la
# dernière décision de séance était « modifié » (donc `navette_en_cours`) et 3
# marqués `rejete`, alors qu'ils étaient promulgués — des statuts
# factuellement faux (ex. convention sur les infractions à bord des aéronefs,
# « modifié » au Sénat le 2021-01-28, promulguée le 2021-02-03).
#
# La promulgation ne remplace JAMAIS `adopte_cmp`/`adopte_49_3` : ces statuts
# portent la voie procédurale, que `promulgue` ne dit pas. L'écrasement ferait
# disparaître le fait 49.3 ou CMP de 116 textes, exactement le collapse que
# refuse AGENTS.md §2.4.
KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL: frozenset[str] = frozenset({
    "depose", "navette_en_cours", "adopte", "adopte_49_3", "adopte_cmp",
    "promulgue", "rejete", "rejete_49_3", "retire",
})

# Chambre de dépôt initial d'un texte gouvernemental : un gouvernement n'est
# rattaché à aucune chambre, mais chaque texte l'est individuellement, et
# uniquement à AN ou Senat (jamais PE/mairie, hors périmètre institutionnel
# d'un gouvernement français).
KNOWN_CHAMBRES_DEPOT_TEXTE: frozenset[str] = frozenset({"AN", "Senat"})

# Clés obligatoires au niveau racine du profil de gouvernement.
REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
    "schema_version",
    "type_document",
    "gouvernement_id",
    "nom",
    "premier_ministre",
    "periode",
    "membres",
    "textes",
    "comptages",
    "sources",
    "meta",
})

# Clés obligatoires dans le bloc "meta".
REQUIRED_META_KEYS: frozenset[str] = frozenset({
    "schema_version",
    "genere_le",
    "licence_donnees",
    "warnings",
})

# Clés obligatoires d'une entrée premier_ministre (si non null).
REQUIRED_PREMIER_MINISTRE_KEYS: frozenset[str] = frozenset({
    "nom", "acteur_ref", "source_url",
})

# Clés obligatoires d'une entrée membres[].
REQUIRED_MEMBRE_KEYS: frozenset[str] = frozenset({
    "membre_id", "nom", "portefeuille", "debut", "fin", "actif", "source_url",
})

# Clés obligatoires d'une entrée textes[].
REQUIRED_TEXTE_KEYS: frozenset[str] = frozenset({
    "dossier_id", "titre", "statut", "chambre_depot_initial",
    "date_depot", "date_dernier_evenement", "sort_49_3", "initiateurs",
    "source_url",
})

# Clés obligatoires d'une entrée textes[].initiateurs[] (#435). `acteur_ref` est
# la référence AN brute (toujours présente) ; `membre_id` est sa résolution vers
# un membre du gouvernement, `null` quand elle n'est pas possible.
REQUIRED_INITIATEUR_TEXTE_KEYS: frozenset[str] = frozenset({
    "acteur_ref", "membre_id",
})

# Champs dont la valeur doit être une liste.
_LIST_KEYS: tuple[str, ...] = ("membres", "textes", "sources")


def make_empty_comptages_statuts() -> dict[str, int]:
    """Structure vide de la ventilation `comptages.par_statut` (entiers à 0)."""
    return {statut: 0 for statut in sorted(KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL)}


def make_empty_profil_gouvernement(gouvernement_id: str, nom: str) -> dict[str, Any]:
    """Crée un profil de gouvernement v1 vide avec des valeurs par défaut.

    Args:
        gouvernement_id: identifiant unique de la forme
                         "gouvernement:<libelle_abrege_an>", ex. "gouvernement:LECORNU".
        nom: nom complet du gouvernement, ex. "Gouvernement Lecornu".

    Returns:
        Profil de gouvernement dict initialisé, prêt à être enrichi par un
        futur script d'agrégation (analogue à group_profile.py).
    """
    return {
        "schema_version": SCHEMA_GOUVERNEMENT_VERSION,
        "type_document": "profil_gouvernement",
        "gouvernement_id": gouvernement_id,
        "nom": nom,
        "premier_ministre": None,
        "periode": {
            "debut": None,
            "fin": None,
            "actif": True,
        },
        "membres": [],
        "textes": [],
        "tags_thematiques_agreges": [],
        "comptages": {
            "membres_recenses": None,
            "membres_distincts": 0,
            "membres_avec_interventions": 0,
            "par_statut": make_empty_comptages_statuts(),
        },
        "sources": [],
        "meta": {
            "schema_version": SCHEMA_GOUVERNEMENT_VERSION,
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "licence_donnees": "",
            "warnings": [],
        },
    }


def _erreurs_initiateurs(
    index_texte: int,
    initiateurs: Any,
    membres_connus: set[Any],
) -> list[str]:
    """Valide `textes[].initiateurs` (#435) : `null` ou liste **non vide**
    d'entrées `{acteur_ref, membre_id}`.

    Trois invariants, tous des cas de traçabilité (AGENTS.md §2.2/§2.5) :
      - `[]` est refusé : l'absence d'initiateur déclaré se dit `null`, une
        liste vide affirmerait qu'aucun ministre n'a porté le texte.
      - `acteur_ref` est obligatoire et non vide, même quand la résolution vers
        un membre échoue : c'est la référence brute qui rend le lien vérifiable
        dans la source.
      - un `membre_id` renseigné doit désigner une entrée de `membres[]` — un
        identifiant qui ne correspond à aucun membre du profil serait un lien
        inventé.
    """
    if initiateurs is None:
        return []

    if not isinstance(initiateurs, list):
        return [
            f"textes[{index_texte}].initiateurs doit être une liste ou null, "
            f"reçu : {type(initiateurs).__name__}."
        ]
    if not initiateurs:
        return [
            f"textes[{index_texte}].initiateurs est une liste vide — utiliser null "
            f"quand la source ne déclare aucun initiateur (règle AGENTS.md §2.5)."
        ]

    errors: list[str] = []
    for j, initiateur in enumerate(initiateurs):
        prefixe = f"textes[{index_texte}].initiateurs[{j}]"
        if not isinstance(initiateur, dict):
            errors.append(f"{prefixe} doit être un dict.")
            continue
        missing = REQUIRED_INITIATEUR_TEXTE_KEYS - set(initiateur.keys())
        if missing:
            errors.append(f"{prefixe} : clés manquantes : {sorted(missing)}.")
            continue

        acteur_ref = initiateur["acteur_ref"]
        if not isinstance(acteur_ref, str) or not acteur_ref:
            errors.append(
                f"{prefixe}.acteur_ref doit être une chaîne non vide "
                f"(reçu : {acteur_ref!r}) : la référence AN brute est conservée "
                f"même quand aucun membre_id n'est résolu."
            )

        membre_id = initiateur["membre_id"]
        if membre_id is None:
            continue
        if not isinstance(membre_id, str) or not membre_id:
            errors.append(
                f"{prefixe}.membre_id doit être une chaîne non vide ou null "
                f"(reçu : {membre_id!r})."
            )
        elif membre_id not in membres_connus:
            errors.append(
                f"{prefixe}.membre_id {membre_id!r} ne correspond à aucune entrée "
                f"de membres[] — un lien membre → texte doit pointer vers un "
                f"membre du profil."
            )

    return errors


def validate_profil_gouvernement(profil: dict[str, Any]) -> list[str]:
    """Vérifie les invariants de base du schéma de gouvernement v1.

    Validation structurelle : présence des clés obligatoires, types, valeur
    de schema_version et type_document, invariants de chaque entrée
    membres[]/textes[], nomenclature fermée des statuts, non-collapse du
    49.3 (règle AGENTS.md §2.4), et traçabilité des liens
    `textes[].initiateurs` (voir `_erreurs_initiateurs`).

    Args:
        profil: dict à valider.

    Returns:
        Liste d'erreurs (liste vide = profil valide).
    """
    errors: list[str] = []

    if not isinstance(profil, dict):
        return [f"Le profil de gouvernement doit être un dict, reçu : {type(profil).__name__}."]

    missing = REQUIRED_TOP_LEVEL_KEYS - set(profil.keys())
    if missing:
        errors.append(f"Clés manquantes au niveau racine : {sorted(missing)}.")

    version = profil.get("schema_version")
    if version != SCHEMA_GOUVERNEMENT_VERSION:
        errors.append(
            f"schema_version inattendu : {version!r} (attendu : {SCHEMA_GOUVERNEMENT_VERSION!r})."
        )

    if profil.get("type_document") != "profil_gouvernement":
        errors.append(
            f"'type_document' doit être 'profil_gouvernement', reçu : {profil.get('type_document')!r}."
        )

    gouvernement_id = profil.get("gouvernement_id")
    if not gouvernement_id:
        errors.append("'gouvernement_id' est vide ou absent.")
    elif not str(gouvernement_id).startswith("gouvernement:"):
        errors.append(
            f"'gouvernement_id' doit commencer par 'gouvernement:', reçu : {gouvernement_id!r}."
        )

    if not profil.get("nom"):
        errors.append("'nom' est vide ou absent.")

    for key in _LIST_KEYS:
        val = profil.get(key)
        if val is not None and not isinstance(val, list):
            errors.append(f"'{key}' doit être une liste, reçu : {type(val).__name__}.")

    periode = profil.get("periode")
    if not isinstance(periode, dict):
        errors.append("'periode' doit être un dict.")

    premier_ministre = profil.get("premier_ministre")
    if premier_ministre is not None:
        if not isinstance(premier_ministre, dict):
            errors.append("'premier_ministre' doit être un dict ou null.")
        else:
            missing_pm = REQUIRED_PREMIER_MINISTRE_KEYS - set(premier_ministre.keys())
            if missing_pm:
                errors.append(f"'premier_ministre' : clés manquantes : {sorted(missing_pm)}.")

    membres = profil.get("membres")
    if isinstance(membres, list):
        for i, membre in enumerate(membres):
            if not isinstance(membre, dict):
                errors.append(f"membres[{i}] doit être un dict.")
                continue
            missing_membre = REQUIRED_MEMBRE_KEYS - set(membre.keys())
            if missing_membre:
                errors.append(f"membres[{i}] : clés manquantes : {sorted(missing_membre)}.")
                continue
            if membre["portefeuille"] is not None and not membre["source_url"]:
                errors.append(
                    f"membres[{i}].portefeuille est renseigné sans 'source_url' associé."
                )
            if not isinstance(membre["actif"], bool):
                errors.append(f"membres[{i}].actif doit être un booléen.")

    membres_connus = {
        membre.get("membre_id")
        for membre in (profil.get("membres") or [])
        if isinstance(membre, dict) and membre.get("membre_id")
    }

    textes = profil.get("textes")
    if isinstance(textes, list):
        for i, texte in enumerate(textes):
            if not isinstance(texte, dict):
                errors.append(f"textes[{i}] doit être un dict.")
                continue
            missing_texte = REQUIRED_TEXTE_KEYS - set(texte.keys())
            if missing_texte:
                errors.append(f"textes[{i}] : clés manquantes : {sorted(missing_texte)}.")
                continue

            statut = texte["statut"]
            if statut not in KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL:
                errors.append(
                    f"textes[{i}].statut inconnu : {statut!r}. "
                    f"Valeurs connues : {sorted(KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL)}."
                )

            chambre_depot = texte["chambre_depot_initial"]
            if chambre_depot not in KNOWN_CHAMBRES_DEPOT_TEXTE:
                errors.append(
                    f"textes[{i}].chambre_depot_initial non reconnue : {chambre_depot!r}. "
                    f"Valeurs connues : {sorted(KNOWN_CHAMBRES_DEPOT_TEXTE)}."
                )

            sort_49_3 = texte["sort_49_3"]
            if sort_49_3 is not None and not isinstance(sort_49_3, bool):
                errors.append(f"textes[{i}].sort_49_3 doit être un booléen ou null.")

            if statut in ("adopte_49_3", "rejete_49_3") and sort_49_3 is not True:
                errors.append(
                    f"textes[{i}] : statut {statut!r} exige sort_49_3 = True "
                    f"(reçu : {sort_49_3!r})."
                )
            if sort_49_3 is True and statut not in ("adopte_49_3", "rejete_49_3"):
                errors.append(
                    f"textes[{i}] : sort_49_3 = True mais statut = {statut!r} — "
                    f"le 49.3 ne doit jamais être collapsé vers 'adopte'/'rejete' ou tout autre statut."
                )

            # #689 — la commission au fond et son motif d'absence sont deux
            # faces d'une seule information, et la contradiction est l'erreur
            # qui compte : un texte qui porte les deux dirait à la fois « voici
            # sa commission » et « voici pourquoi elle manque ».
            commission = texte.get("commission_saisie_au_fond")
            non_resolue = texte.get("commission_non_resolue")
            if commission is not None and not isinstance(commission, dict):
                errors.append(
                    f"textes[{i}].commission_saisie_au_fond doit être un dict ou null."
                )
            if commission is not None and non_resolue is not None:
                errors.append(
                    f"textes[{i}] porte à la fois commission_saisie_au_fond et "
                    "commission_non_resolue — une commission résolue n'a pas de motif "
                    "d'absence."
                )
            if non_resolue is not None:
                if not isinstance(non_resolue, dict):
                    errors.append(
                        f"textes[{i}].commission_non_resolue doit être un dict."
                    )
                else:
                    motif = non_resolue.get("motif")
                    if motif not in KNOWN_MOTIFS_COMMISSION_NON_RESOLUE:
                        errors.append(
                            f"textes[{i}].commission_non_resolue.motif inconnu : "
                            f"{motif!r}. Valeurs connues : "
                            f"{sorted(KNOWN_MOTIFS_COMMISSION_NON_RESOLUE)}."
                        )

            errors.extend(_erreurs_initiateurs(i, texte["initiateurs"], membres_connus))

    comptages = profil.get("comptages")
    if comptages is not None and not isinstance(comptages, dict):
        errors.append("'comptages' doit être un dict.")
    elif isinstance(comptages, dict):
        par_statut = comptages.get("par_statut")
        if not isinstance(par_statut, dict):
            errors.append("'comptages.par_statut' doit être un dict.")
        else:
            missing_statuts = KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL - set(par_statut.keys())
            if missing_statuts:
                errors.append(
                    f"'comptages.par_statut' : clés manquantes : {sorted(missing_statuts)}."
                )
            extra_statuts = set(par_statut.keys()) - KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL
            if extra_statuts:
                errors.append(
                    f"'comptages.par_statut' : clés inconnues : {sorted(extra_statuts)}."
                )
            for statut, valeur in par_statut.items():
                if statut not in KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL:
                    continue
                if not isinstance(valeur, int) or isinstance(valeur, bool):
                    errors.append(
                        f"'comptages.par_statut[{statut!r}]' doit être un entier brut, "
                        f"reçu : {type(valeur).__name__} ({valeur!r})."
                    )
                elif valeur < 0:
                    errors.append(f"'comptages.par_statut[{statut!r}]' ne peut pas être négatif.")

    meta = profil.get("meta")
    if not isinstance(meta, dict):
        errors.append("'meta' doit être un dict.")
    else:
        missing_meta = REQUIRED_META_KEYS - set(meta.keys())
        if missing_meta:
            errors.append(f"Clés manquantes dans 'meta' : {sorted(missing_meta)}.")
        if meta.get("schema_version") != SCHEMA_GOUVERNEMENT_VERSION:
            errors.append(
                f"meta.schema_version inattendu : {meta.get('schema_version')!r} "
                f"(attendu : {SCHEMA_GOUVERNEMENT_VERSION!r})."
            )
        if not isinstance(meta.get("warnings"), list):
            errors.append("'meta.warnings' doit être une liste.")

    return errors
