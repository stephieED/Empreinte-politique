"""Garde-fou #529 (lot 5) : NosDéputés ne rentre pas par la fenêtre.

L'épic « une seule source AN » se termine par un lot de **retrait**. Ce fichier
est le verrou qui l'impose, sur le même patron que
`tests/test_retrait_senat_528.py` : il ne teste pas un comportement de collecte
— il n'y a plus rien à collecter là-bas — mais l'**absence** des chemins et la
**présence** de ce qui les remplace.

## Le critère est le code EXÉCUTÉ, pas la prose

`grep -ri nosdeputes src/` renvoie encore beaucoup de lignes, et c'est voulu :
le « pourquoi » de #516, #518, #522, #524, #526, #527 reste vrai et doit rester
lisible. Ce test applique donc le critère de l'issue — il lit les **chaînes de
caractères et les identifiants** du code, jamais les commentaires ni les
docstrings.

## Les exceptions, et pourquoi ce ne sont pas des oublis

Six modules portent encore la plateforme dans du code exécuté, en trois
familles. Aucun ne COLLECTE.

**(a) Ceux qui LISENT le corpus déjà publié.** Les retirer casserait ce corpus
plutôt que de le nettoyer, et leur sort est le **lot 6** — avec les mentions
d'attribution ODbL :

1. `schema_pivot.KNOWN_SOURCE_TYPES` — 476 profils publiés portent
   `sources[].type in {nosdeputes, nossenateurs}` ; les en retirer ferait
   refuser par `validate_profil()` ce qu'on vient de publier ;
2. `audit_pivot_dataset.MAPPING_CHAMBRE_SOURCES` (`AN` et `Senat`) — même
   population, vue par l'audit : sans elles, il déclarerait « incohérence
   chambre/sources » sur des profils parfaitement valides ;
3. `normalize_profil` relit `meta.synchro_sources.nosdeputes` en repli — les
   profils bruts collectés avant ce lot ne portent que cette clé, et la fusion
   additive les garde.

**(c) Celui qui l'ATTRIBUE.** `licences` (#530, lot 6) reconnaît les
`sources[].type` et les `source_url` de Regards Citoyens pour en dériver la
mention ODbL que le corpus publié doit encore. Retirer ces motifs ne
retirerait pas la donnée : il retirerait l'attribution qui lui est due
(AGENTS.md §2 règle 2). Sa condition de retrait s'exécute d'elle-même — la
clause disparaît d'un profil dès qu'il ne porte plus rien de Regards Citoyens.

**(b) Ceux qui la NOMMENT dans un message, au passé.** Un texte destiné à un
lecteur, pas une URL qu'on appelle :

4. `group_profile._avertissement_fraicheur_an` — c'est un `meta.warnings`
   **publié**, et #527 a décidé qu'il devait dire « et non plus de
   www.nosdeputes.fr » : deux versions successives d'une même fiche doivent se
   relire l'une contre l'autre (AGENTS.md §2 règle 2) ;
5. `group_roster.fetch_full_roster` — le refus d'une chambre hors périmètre
   nomme `archive.nossenateurs.fr` parce que c'est la panne qui a motivé #528.
   Un « chambre inconnue » générique se lit comme une faute de frappe.

Cette liste est fermée et vérifiée ici : une septième occurrence fait échouer
la suite.
"""

import ast
import re
import sys
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
SRC = RACINE / "src"

sys.path.insert(0, str(SRC))

import candidate_profile  # noqa: E402
import group_roster  # noqa: E402
import normalize_profil  # noqa: E402
import schema_pivot  # noqa: E402

#: L'ancre de la décision. Un refus qui ne la cite pas oblige son lecteur à
#: deviner s'il regarde une panne ou un choix.
ANCRE = "retrait-nosdeputes-529"

#: Les seuls modules de `src/` autorisés à porter la plateforme dans du code
#: exécuté, et la raison de chacun (voir l'en-tête). Une entrée s'ajoute par
#: décision écrite, pas parce que la suite est rouge.
OCCURRENCES_ADMISES = {
    # (a) lecture du corpus publié — retrait au lot 6
    "schema_pivot.py": "KNOWN_SOURCE_TYPES — 476 profils publiés en portent un",
    "audit_pivot_dataset.py": "MAPPING_CHAMBRE_SOURCES — l'audit lit ce corpus",
    "normalize_profil.py": "repli de lecture sur synchro_sources.nosdeputes",
    "avertissements.py": (
        "AVERTISSEMENTS_HERITES — le message `synchro_sources.nosdeputes` "
        "qu'aucun code n'écrit plus mais que 19 des 115 avertissements publiés "
        "portent encore : sans lui, ces 19-là n'auraient jamais de destinataire "
        "(#642)"
    ),
    # (c) attribution due au corpus publié — le lot 6 lui-même (#530)
    "licences.py": (
        "LICENCE_PAR_TYPE_SOURCE et _MOTIFS_URL_REGARDS_CITOYENS : c'est la "
        "mention d'attribution ODbL qui reste due aux 475 profils et aux 511 "
        "interventions publiées qui en dérivent encore"
    ),
    # (d) retrait du marqueur — le lot qui fait sortir la source du corpus (#890)
    "purge_marqueur_regards_citoyens.py": (
        "TYPES_RETIRES et CLE_JOURNAL_BRUT : pour retirer un marqueur il faut "
        "le nommer. C'est le seul module dont l'occurrence est destinée à "
        "disparaître avec le corpus qu'elle vise — quand les 21 profils que "
        "#885 couvre auront quitté Regards Citoyens, ce module n'aura plus rien "
        "à retirer"
    ),
    # (e) juger une provenance — le lot qui retire ce qui ment (#885 point 5)
    "retrait_heritage_senat.py": (
        "TYPES_REGARDS_CITOYENS : pour dire qu'une entrée `sources[]` ment sur "
        "sa provenance, il faut nommer la provenance qu'elle prétend. Le "
        "référentiel des URL reste `licences.MOTIFS_URL_REGARDS_CITOYENS` — ce "
        "module ne recopie que les deux TYPES"
    ),
    # (b) message destiné à un lecteur, au passé
    "group_profile.py": "meta.warnings publié : nomme la source d'avant #527",
    "group_roster.py": "refus de chambre : nomme la panne qui a motivé #528",
}

MOTIF = re.compile(r"nosdeputes|nossenateurs", re.I)


# ---------------------------------------------------------------------------
# Le code exécuté ne nomme plus la plateforme, sauf pour relire le publié
# ---------------------------------------------------------------------------

def _chaines_et_noms_executes(chemin: Path) -> list[str]:
    """Les littéraux texte et les identifiants d'un module, sans sa prose.

    Les docstrings sont des `ast.Constant` en tête de module/classe/fonction :
    on les écarte explicitement, sinon l'historique — qu'on veut garder — ferait
    échouer le test. Les commentaires, eux, n'entrent jamais dans l'AST.
    """
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    docstrings = set()
    for noeud in ast.walk(arbre):
        if isinstance(noeud, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            corps = getattr(noeud, "body", None) or []
            if (
                corps
                and isinstance(corps[0], ast.Expr)
                and isinstance(corps[0].value, ast.Constant)
                and isinstance(corps[0].value.value, str)
            ):
                docstrings.add(id(corps[0].value))

    trouves: list[str] = []
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.Constant) and isinstance(noeud.value, str):
            if id(noeud) not in docstrings:
                trouves.append(noeud.value)
        elif isinstance(noeud, ast.Name):
            trouves.append(noeud.id)
        elif isinstance(noeud, ast.Attribute):
            trouves.append(noeud.attr)
        elif isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            trouves.append(noeud.name)
    return trouves


def test_le_code_execute_ne_nomme_plus_la_plateforme():
    """Le critère d'acceptation du lot, appliqué au code et non à la prose."""
    porteurs: dict[str, list[str]] = {}
    for chemin in sorted(SRC.glob("*.py")):
        occurrences = [c for c in _chaines_et_noms_executes(chemin) if MOTIF.search(c)]
        if occurrences:
            porteurs[chemin.name] = occurrences

    inattendus = {
        nom: occ for nom, occ in porteurs.items() if nom not in OCCURRENCES_ADMISES
    }
    assert not inattendus, (
        "Ces modules nomment NosDéputés/NosSénateurs dans du code EXÉCUTÉ "
        f"(chaînes ou identifiants) : { {k: sorted(set(v)) for k, v in inattendus.items()} }. "
        "L'historique en commentaire est le bienvenu ; un chemin de collecte, "
        f"non. Voir docs/decisions/{ANCRE}.md."
    )
    manquants = set(OCCURRENCES_ADMISES) - set(porteurs)
    assert not manquants, (
        f"Ces emplacements ont perdu leur occurrence : {sorted(manquants)}. Ce "
        "n'est pas forcément un progrès — sur les lecteurs du corpus publié, "
        "`validate_profil()` refuserait alors les 476 profils qui portent encore "
        "ce type de source (lot 6) ; sur les messages, un avertissement publié "
        "perdrait la source d'avant. Retirer une entrée est une décision, pas un "
        "nettoyage."
    )


def test_les_deux_types_de_source_historiques_restent_valides():
    """Le corpus publié doit continuer de se valider (AGENTS.md §2 règle 5)."""
    assert {"nosdeputes", "nossenateurs"} <= schema_pivot.KNOWN_SOURCE_TYPES


def test_la_collecte_ne_produit_plus_que_la_source_officielle():
    """Ce que la normalisation ÉCRIT, par opposition à ce qu'elle sait relire."""
    pivot = normalize_profil.normalize_profil({"slug": "x", "chambre": "deputes"})
    assert [s["type"] for s in pivot["sources"]] == ["assemblee_nationale"]


# ---------------------------------------------------------------------------
# Les chemins de collecte n'ont plus de définition
# ---------------------------------------------------------------------------

#: La chaîne complète, du transport au résultat. Elle est nommée en entier —
#: pas seulement son entrée — parce que c'est la somme qui rendait le retour
#: possible sans décision : un `_get_payload` seul se rebranche en trois lignes.
CHEMINS_RETIRES_CANDIDATE_PROFILE = (
    "BASE_URLS",
    "_get_with_watchdog",
    "_get_payload",
    "_try_urls",
    "_TERMINAL_FAILURE",
    "fetch_identity",
    "fetch_recherche",
    "fetch_all_intervention_results",
    "fetch_all_intervention_results_from_domains",
    "fetch_intervention_details",
    "fetch_seance_context",
    "_extract_speaker_identity_from_html",
    "_classify_intervention",
    "_classify_intervention_format",
    "REACTION_COURTE_NB_MOTS_MAX",
    "_process_search_result",
    "_extract_search_results",
    "_extract_mandats",
    "_extract_responsabilite_entries",
    "_groupe_label",
    "_extract_parlementaire",
    "_xml_to_data",
    "compteur_appels_nosdeputes",
    "compteur_requetes_sans_reponse",
    "_incrementer_appels_nosdeputes",
    "WARNING_PREFIX_SOURCE_INJOIGNABLE",
)

CHEMINS_RETIRES_GROUP_ROSTER = (
    "fetch_full_roster_nosdeputes",
    "_base_url_for",
    "_BASE_URL_BY_LEGISLATURE_AN",
    "_LIST_ENDPOINT",
    "_erreur_retentable",
    "_ROSTER_MAX_ATTEMPTS",
    "_ROSTER_RETRY_BACKOFF_SECONDS",
    "_ROSTER_TIMEOUT",
    "_STATUTS_5XX_RETENTABLES",
)


@pytest.mark.parametrize("nom", CHEMINS_RETIRES_CANDIDATE_PROFILE)
def test_candidate_profile_na_plus_de_chemin_nosdeputes(nom):
    assert not hasattr(candidate_profile, nom), (
        f"`candidate_profile.{nom}` est de retour. Voir "
        f"docs/decisions/{ANCRE}.md."
    )


@pytest.mark.parametrize("nom", CHEMINS_RETIRES_GROUP_ROSTER)
def test_group_roster_na_plus_de_chemin_nosdeputes(nom):
    assert not hasattr(group_roster, nom), (
        f"`group_roster.{nom}` est de retour. Voir "
        f"docs/decisions/{ANCRE}.md."
    )


def test_le_module_de_normalisation_a_ete_renomme():
    """`normalize_nosdeputes.py` s'appelle `normalize_profil.py`.

    Le renommage n'est pas cosmétique : le fichier documenté par le diagramme
    d'AGENTS.md §3 portait le nom d'une source dont plus rien ne venait. Un
    module resté sous les deux noms serait pire — deux points d'entrée pour un
    même adaptateur.
    """
    assert (SRC / "normalize_profil.py").exists()
    assert not (SRC / "normalize_nosdeputes.py").exists()
    assert callable(normalize_profil.normalize_profil)
    assert not hasattr(normalize_profil, "normalize_nosdeputes")
    assert not hasattr(normalize_profil, "_SOURCE_TYPE_MAP")


# ---------------------------------------------------------------------------
# Ce qui remplace le repli : un vide DÉCLARÉ, jamais muet
# ---------------------------------------------------------------------------

def test_l_absence_d_interventions_a_un_prefixe_de_warning():
    """Le repli NosDéputés a produit 496 des 789 interventions publiées. Le
    retirer sans rien dire ferait lire « cette personne n'a jamais parlé » là
    où il faut lire « cette source ne rend rien » (AGENTS.md §2.5)."""
    assert candidate_profile.WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES == (
        "interventions syceron indisponibles"
    )


def test_le_prefixe_de_warning_couvre_les_warnings_deja_publies():
    """Le libellé publié jusqu'ici — « interventions syceron indisponibles
    (fallback nosdeputes) » — commence par le nouveau préfixe.

    C'est délibéré : `audit_pivot_dataset.compute_agregation_warnings` agrège
    par préfixe, et un renommage complet aurait scindé en deux une même
    population sans que rien ne le dise.
    """
    ancien = "interventions syceron indisponibles (fallback nosdeputes) : ..."
    assert ancien.startswith(
        candidate_profile.WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES
    )


# `test_max_pages_est_accepte_mais_annonce_son_inutilite` est RETIRÉ au rebasage
# sur #510. Il figeait le compromis « accepter --max-pages mais le signaler »,
# écrit parce que ce lot ne pouvait pas modifier `.github/workflows/`. #510 a
# retiré le drapeau de generate-data.yml ET du code : plus aucun appelant ne le
# passe, il n'y a donc plus rien à accepter ni à signaler.
