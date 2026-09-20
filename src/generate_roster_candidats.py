#!/usr/bin/env python3
"""
generate_roster_candidats.py — Construit une liste de "candidats" à partir du
roster réel des groupes parlementaires configurés dans raw_data/groupes_reels.json,
au lieu de la liste éditoriale raw_data/candidats.json.

Contexte : raw_data/candidats.json est une liste éditoriale maintenue à la
main (candidats déclarés/pressentis à la présidentielle). Ce script produit
une liste alternative, au même format d'entrée que celui accepté par
generate_all_profiles.py --candidats, mais pilotée par la composition réelle
des groupes parlementaires — utile pour extraire des profils individuels pour
tou·te·s les membres d'un groupe, pas seulement les candidats déclarés.

Comme generate_group_profiles.py, ce script ne fait qu'UN SEUL fetch réseau
par (roster_chambre, legislature) distinct, partagé entre tous les groupes de
la config (voir group_roster.fetch_full_roster / filter_roster_by_sigle).

## Le roster n'est JAMAIS écrit sur une collecte incomplète (#511)

Le 20/08/2026, un `Read timed out` sur les DEUX fetchs a fait écrire ici un
roster de **0 candidat**, avec un code de sortie 0. La passe suivante
(`generate_all_profiles.py --pivot-only --candidats raw_data/roster_candidats.json`)
a donc itéré sur le vide : les 20 membres que ce run venait de collecter n'ont
reçu aucun pivot et ne sont publiés nulle part — run `32405297873`, conclu en
**succès**, 229 profils bruts pour 209 pivots au commit `68bc094`.

La fonction refusait déjà d'écrire sur une ENTRÉE vide (« aucun groupe à
agréger ») trois lignes plus haut. C'est le même raisonnement, appliqué au même
fichier : une donnée non résolue ne reçoit pas de valeur par défaut, elle
échoue bruyamment (AGENTS.md §2 règle 5).

**Trois anomalies bloquent l'écriture**, et aucune n'est un seuil chiffré :

1. **un fetch en échec** — `fetch_rosters_bruts` le sait déjà (`None` pour la
   clé), l'information était simplement jetée. C'est aussi la réponse au
   rétrécissement : la granularité d'une panne est la clé de fetch entière, donc
   un échec partiel n'enlève pas « quelques » membres mais **452 ou 300** sur
   les 752 de `raw_data/groupes_reels.json` (mesuré au 19/08/2026 : 452 AN
   + 300 Sénat). Un test de vacuité ne verrait rien ; celui-ci nomme la clé ;
2. **un groupe configuré qui rend 0 membre** alors que son fetch a réussi —
   le seul mécanisme de rétrécissement restant (sigle renommé en amont). Les 7
   groupes configurés rendent aujourd'hui entre 31 et 235 membres ;
3. **un roster total vide** — le filet de dernier recours, celui de l'incident.

Un seuil de rétrécissement chiffré a été écarté, pas oublié : voir
docs/decisions/collecte-non-publiee.md#roster-jamais-ecrit-vide.

## Un groupe à l'extraction suspendue n'est pas interrogé (#516)

Une entrée de `groupes_reels.json` portant `extraction_suspendue` sort des
trois étages ci-dessus : sa clé de fetch n'est pas construite, ses membres ne
sont pas collectés, et son absence n'est **pas** une anomalie — ce n'est pas
une panne, c'est une décision écrite. Les deux entrées Sénat le sont depuis le
24/08/2026 (certificat TLS expiré sur `archive.nossenateurs.fr`), ce qui
faisait échouer tout le run, collecte AN comprise. Voir `groupes_config.py` et
docs/decisions/extraction-groupe-suspendue-516.md.

## Une seule construction par run en CI, et des anomalies annotées (#518)

Ce script était appelé par les **9 invocations** d'un run `generate-data`
(8 shards + `merge-and-pivot`), donc 9 fetchs de la même liste. Il n'est plus
appelé qu'une fois, par `prepare-roster-matrix`, et son résultat transite par
l'artifact `roster-candidats` ; les consommateurs ne le rappellent qu'en repli,
si l'artifact manque. Ce n'était pas qu'une affaire de coût : les shards se
partagent le roster **par position**, et `merge-and-pivot` normalise en pivot
**sa** liste — deux listes qui divergent laissent un membre collecté sans
aucune passe pivot, sans qu'aucune étape n'échoue.

Chaque anomalie ci-dessus part aussi en annotation GitHub Actions
(`::error::`, voir `gha.py`) : trois runs sont morts ici en une semaine, et la
seule trace qu'en gardait l'onglet de résumé était
`Process completed with exit code 1`. Voir
docs/decisions/roster-unique-par-run-518.md.

## Une anomalie nomme sa cause, et la suspension totale n'en est pas une (#524)

Deux corrections, toutes deux sur ce qui se lit APRÈS coup :

1. **l'exception voyage jusqu'à l'annotation**. `fetch_rosters_bruts` la
   jetait après l'avoir affichée sur `stderr` ; `anomalies_roster`
   reconstruisait ensuite son message depuis la seule clé. L'annotation disait
   donc « en échec », jamais `HTTP 500`, jamais `SSLError`, jamais
   `Read timed out` — et il fallait sonder l'endpoint à la main pour retrouver
   ce que le run savait déjà (run `32876863499`, 3 jobs rouges sur un 500
   immédiat et déterministe). Elle transite désormais dans le second membre
   rendu par `fetch_rosters_bruts` ;
2. **« tous les groupes suspendus » rend `EXIT_ROSTER_INDISPONIBLE` (2)**, pas
   1. Suspendre les entrées AN comme les 2 entrées Sénat le sont depuis #516
   est le remède documenté à une source en panne ; tant que ce cas sortait en
   1, ce remède reproduisait l'échec qu'il devait éteindre, et il n'existait
   aucun moyen de conclure un run vert pendant que NosDéputés répondait 500.
   Les trois appelants du workflow tolèrent ce code et sautent la branche
   roster. **Aucun roster à 0 candidat n'est jamais écrit** pour autant : ce
   chemin n'écrit rien du tout, ce qui reste exactement l'interdit de #511.

Le roster BRUT peut être publié avec (`--rosters-bruts-out`) : c'est ce qui
supprime le DERNIER fetch de la même liste dans un run, celui de
`generate_group_profiles.py`. Voir la section correspondante de
`group_roster.py`.

## La clé `deputes` vient d'AMO30, et ses membres sans slug sont NOMMÉS (#527)

Ce script est inchangé sur la clé `senateurs`. Sur `deputes`,
`group_roster.fetch_full_roster` dérive désormais la composition d'AMO30 : une
seule source AN, la même que les scrutins et les amendements, et plus le miroir
tiers dont trois lots consécutifs ont amorti les pannes (#518, #524).

Une conséquence de la bascule tombe **ici** et pas ailleurs : AMO30 publie un
`PA######`, pas un slug, et le slug vient de la table committée du lot 2
(#525). Un membre qui n'y a pas d'entrée traversait l'aplatissement sans un mot
— `build_roster_candidats_detaille` ignore un membre sans slug depuis toujours,
mais NosDéputés n'en produisait aucun. `membres_sans_slug` les compte et les
nomme (4 à la bascule, tous déclarés dans `raw_data/groupes_reels.json`), en
`warning` : ils ne bloquent pas, ils cessent d'être invisibles.

## Compter n'était pas ouvrir la porte (#708)

Le compteur de #527 a fait son travail : il a nommé 4 écarts sur la 16e, puis
**156 sur les 461 entrées des 5 rosters de la 17e** — 33,8 %, `SOC-17` le plus
touché avec **41 écartées sur 70** (mesuré le 02/09/2026). La cause n'était pas une table incomplète mais une
**circularité** : la table est construite depuis les profils publiés, donc il
fallait un profil pour avoir un slug et un slug pour avoir un profil.

`an_roster.resoudre_slugs` ouvre la porte — `slugify(état civil AMO30)`, la
fonction qui fabrique déjà tous les autres slugs du dépôt — et n'attribue
**jamais** en silence un slug que quelqu'un d'autre porte. Ce qui arrive ici :

- `membres_sans_slug` compte désormais ce qui reste **réellement** écarté, les
  collisions non tranchées, et **pas zéro par construction**. Sur les 1 662
  acteurs de l'index GP sans entrée de table — dont les 160 des 10 groupes
  configurés — : **0 collision** mesurée le 02/09/2026 ; le compteur passe à 0
  parce que le corpus n'en a pas, pas parce qu'on a retiré le compteur ;
- `membres_slug_fabrique` compte l'inverse : ce qui entre par une porte que
  personne n'a relue. En `notice` — ce n'est pas une panne, c'est un fait à
  déclarer (AGENTS §2 règle 2), et la §5b du contrôle qualité bloquera de toute
  façon le commit tant que leur entrée de correspondance n'aura pas été relue.

Usage (depuis la racine du dépôt) :
    python src/generate_roster_candidats.py \\
        --config raw_data/groupes_reels.json \\
        --out raw_data/roster_candidats.json \\
        --rosters-bruts-out raw_data/rosters_bruts.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Optional

import gha
from candidate_profile import acteur_ref_to_pseudo_url
from gouvernement_roster_an import CLE_ROSTER as CLE_ROSTER_GOUVERNEMENTS
from population_profils import ROSTER_GOUVERNEMENT
from group_roster import (
    ERREURS_ROSTER,
    ecrire_rosters_bruts,
    fetch_full_roster,
    filter_roster_by_sigle,
)
from groupes_config import (
    libelle_groupe,
    partitionner_groupes,
    resume_suspension,
)


# Code de retour distinct d'un échec ordinaire (1) : il n'y avait RIEN à
# collecter, et c'est une décision écrite — pas une panne. Même valeur et même
# sémantique que `generate_group_profiles.EXIT_ROSTER_INDISPONIBLE` et que
# `generate_gouvernement_profiles.EXIT_COLLECTE_INCOMPLETE` (#427), pour que le
# workflow les traite pareil : dégradé-mais-sûr, jamais une régression du code.
#
# #524 : sans lui, le remède documenté d'une source AN en panne — suspendre les
# entrées AN de `groupes_reels.json` comme les 2 entrées Sénat le sont depuis
# #516 — REPRODUISAIT l'échec qu'il est censé éteindre, puisque suspendre les 5
# dernières entrées actives sortait ici en 1. Il n'existait alors aucun moyen
# d'obtenir un run vert pendant que NosDéputés répondait 500.
#
# Ce que ce code ne dit JAMAIS : « écris un roster vide ». Rien n'est écrit sur
# ce chemin, et l'appelant saute la branche roster au lieu de la nourrir avec 0
# candidat — ce que #511 interdit.
EXIT_ROSTER_INDISPONIBLE = 2

#: Longueur au-delà de laquelle le message d'une exception est tronqué dans
#: une anomalie. Une annotation GitHub Actions tient sur UNE ligne, dans une
#: liste : un `HTTPError` porte l'URL complète et déborderait sur ce qui suit.
_LONGUEUR_MAX_EXCEPTION = 200

#: Nombre de membres sans slug nommés dans l'annotation. Même contrainte qu'au
#: dessus : une annotation tient sur une ligne. 4 aujourd'hui, tous nommés ; la
#: borne existe pour que ce ne soit pas le jour où ils seront 200 qu'on
#: découvre que l'annotation est illisible.
_MAX_MEMBRES_NOMMES = 12


def resume_exception(exc: BaseException) -> str:
    """`"HTTPError: 500 Server Error: … for url: …"` — type ET message (#524).

    Le type seul ne distingue pas un 500 d'un 404 ; le message seul ne dit pas
    qu'il s'agit d'un `SSLError` quand `requests` le formate en une phrase de
    certificat. Les deux, aplatis sur une ligne et bornés, parce que la
    destination est une annotation.
    """
    message = " ".join(str(exc).split()) or "aucun message"
    if len(message) > _LONGUEUR_MAX_EXCEPTION:
        message = message[: _LONGUEUR_MAX_EXCEPTION - 1] + "…"
    return f"{type(exc).__name__}: {message}"


def _roster_key(groupe: dict[str, Any]) -> tuple[str, Optional[str]]:
    """Clé (roster_chambre, legislature) identifiant un fetch réseau partageable."""
    legislature = groupe.get("legislature") if groupe["roster_chambre"] == "deputes" else None
    return (groupe["roster_chambre"], legislature)


def _actifs(groupes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Les groupes dont l'extraction n'est pas suspendue (#516).

    Appliqué aux TROIS étages (fetch, aplatissement, anomalies) et pas
    seulement dans `main()` : un groupe suspendu qui resterait visible d'un
    seul d'entre eux rouvrirait sa clé de fetch (étage 1) ou déclencherait un
    « 0 membre retenu » sur un roster qu'on n'a délibérément pas récupéré
    (étage 3). La suspension n'a de sens que si les trois la voient.
    """
    actifs, _ = partitionner_groupes(groupes)
    return actifs


def membres_des_gouvernements(
    zip_path: Optional[Path] = None,
    chemin_correspondance: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Les membres des gouvernements d'AMO30, au format des rosters bruts (#996).

    Mesuré le 17/09/2026 : 311 personnes sur 17 gouvernements, 106 slugs repris
    de la table de correspondance, **205 fabriqués**, aucun acteur sans slug.
    L'union avec les acteurs de l'index GP est ce qui garantit qu'un ministre et
    un député homonymes ne reçoivent pas le même slug.
    """
    from an_roster import _telecharger_archive, charger_index_gp  # noqa: PLC0415
    from gouvernement_roster_an import (  # noqa: PLC0415
        construire_index_gouvernements,
        deriver_membres,
        resoudre_slugs_des_membres,
    )

    index = construire_index_gouvernements(Path(zip_path) if zip_path else _telecharger_archive())
    slugs, origines, _ = resoudre_slugs_des_membres(
        index, charger_index_gp(), chemin_correspondance)
    return deriver_membres(index, slugs, origines)


def candidats_des_gouvernements(
    membres_gouv: list[dict[str, Any]],
    deja_pris: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Les membres de gouvernement au format `roster_candidats.json` (#996 lot 3).

    `deja_pris` porte les slugs que le roster des groupes a déjà retenus, et
    **ils gagnent** : une personne à la fois députée et ministre entre par son
    groupe, avec `statut: "roster_groupe"`. Ce n'est pas un détail de tri —
    `group_profile.py` agrège sur la provenance, et rétrograder un membre de
    groupe en membre de gouvernement le retirerait de la cohésion de son
    groupe. Le rattachement au gouvernement, lui, ne passe pas par la
    provenance : il se fait sur `acteur_ref` (lot 4), donc rien n'est perdu.

    Le `statut` écrit ici est repris **tel quel** comme `meta.provenance` par
    `generate_all_profiles` : c'est la seule raison pour laquelle il vaut
    exactement `roster_gouvernement`, valeur de `KNOWN_PROVENANCES`.
    """
    connus = set(deja_pris)
    candidats: list[dict[str, Any]] = []
    for membre in membres_gouv:
        slug = membre.get("slug")
        if not slug or slug in connus:
            continue
        connus.add(slug)
        # Les libellés d'organe des gouvernements où la personne a siégé, sans
        # doublon et dans l'ordre des périodes. `notes` est du texte libre : il
        # nomme d'où le membre vient, il n'est pas relu par la collecte.
        libelles = []
        for periode in membre.get("mandat_periodes") or []:
            libelle = periode.get("libelle_an")
            if libelle and libelle not in libelles:
                libelles.append(libelle)
        candidats.append({
            "nom": membre.get("nom"),
            "slug": slug,
            # Un membre de gouvernement n'a pas de parti collecté : AMO30 ne
            # publie aucune étiquette politique sur un mandat de gouvernement.
            # `None` dit « non porté », jamais « sans parti » (§2 règle 5).
            "parti": None,
            "famille_politique": None,
            "statut": ROSTER_GOUVERNEMENT,
            "date_declaration": None,
            # Même forme que pour un membre de groupe : la fiche AN de l'acteur,
            # vérifiable (§2 règle 2). `None` si AMO30 n'a pas rendu d'acteur —
            # jamais une URL inventée (§2 règle 5).
            "source": (
                acteur_ref_to_pseudo_url(membre["acteur_ref"])
                if membre.get("acteur_ref")
                else None
            ),
            "notes": (
                "Membre du gouvernement " + ", ".join(libelles)
                + ", issu du roster réel AMO30."
            ) if libelles else "Membre de gouvernement, issu du roster réel AMO30.",
            # #850, et il compte plus encore ici : 124 des membres de
            # gouvernement n'ont jamais été députés, donc aucune recherche par
            # nom ne les retrouve dans AMO30. Sans cet identifiant, leur
            # collecte ne pourrait pas partir.
            "acteur_ref": membre.get("acteur_ref"),
        })
    return candidats


def fetch_rosters_bruts(
    groupes: list[dict[str, Any]],
) -> tuple[
    dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
    dict[tuple[str, Optional[str]], Exception],
]:
    """Récupère le roster complet (non filtré) de chaque (roster_chambre, legislature)
    distinct présent dans `groupes`, un seul fetch réseau par clé.

    Returns:
        `(rosters_bruts, echecs)`. Dans `rosters_bruts`, une valeur `None`
        signale un échec de récupération pour cette clé ; `echecs` porte, pour
        chacune de ces clés, **l'exception qui l'a causé**.

    Depuis #527 la clé `deputes` ne fait plus d'appel réseau vers NosDéputés :
    `fetch_full_roster` la dérive d'AMO30. Les échecs interceptés sont donc
    ceux de `group_roster.ERREURS_ROSTER` — archive indisponible ou table de
    sigles incomplète autant que timeout HTTP. Ce qu'ils deviennent ensuite est
    inchangé : `None` pour la clé, l'exception dans `echecs`, une anomalie
    nommée, aucun roster écrit (#511).

    Le second membre est la correction de #524 : jusque-là l'exception était
    affichée sur `stderr` puis JETÉE, et `anomalies_roster` reconstruisait son
    message à partir de la seule clé. L'annotation `::error::` de #518 disait
    donc « en échec » — jamais `HTTP 500`, jamais `SSLError`, jamais
    `Read timed out`. Quatre runs sont morts là en une semaine, et il a fallu
    sonder l'endpoint à la main pour retrouver la cause que le run
    connaissait : l'annotation existe précisément pour éviter ce
    téléchargement de log.
    """
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]] = {}
    echecs: dict[tuple[str, Optional[str]], Exception] = {}
    for groupe in _actifs(groupes):
        key = _roster_key(groupe)
        if key in rosters_bruts:
            continue
        roster_chambre, legislature = key
        print(f"→ Récupération du roster complet ({roster_chambre}, législature={legislature or 'courante'})…", file=sys.stderr)
        try:
            rosters_bruts[key] = fetch_full_roster(roster_chambre, legislature=legislature)
        except ERREURS_ROSTER as exc:
            print(f"  [!] Récupération du roster impossible pour {key} : {resume_exception(exc)}", file=sys.stderr)
            rosters_bruts[key] = None
            echecs[key] = exc
    return rosters_bruts, echecs


def _libelle_groupe(groupe: dict[str, Any]) -> str:
    """Nom d'un groupe dans les messages d'anomalie, stable et sans ambiguïté.

    `groupe_id` est renseigné sur les 7 groupes de `raw_data/groupes_reels.json`
    et distingue les deux `LR` (`AN:LR` et `Senat:LR`), ce que le seul sigle ne
    ferait pas. Repli sur `chambre:sigle` pour une config plus ancienne.

    Délègue à `groupes_config.libelle_groupe` depuis #516 : les trois
    consommateurs de la config nomment désormais un groupe de la même façon.
    """
    return libelle_groupe(groupe)


def build_roster_candidats_detaille(
    groupes: list[dict[str, Any]],
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """`build_roster_candidats`, plus le décompte de membres retenus PAR GROUPE.

    Le décompte est relevé pendant l'aplatissement et non recalculé après coup :
    le total seul ne distingue pas « 300 membres manquants » de « ces 300-là
    manquent », et c'est cette distinction qui rend l'anomalie actionnable.

    Attention à ce que ce décompte mesure : le nombre de membres **retenus**,
    donc après déduplication par slug. Un groupe dont tous les membres seraient
    déjà venus d'un autre groupe compterait 0 ici — cas que la déduplication
    qualifie elle-même de config mal renseignée, et qu'on veut voir signalé.
    """
    candidats_par_slug: dict[str, dict[str, Any]] = {}
    membres_par_groupe: dict[str, int] = {}

    for groupe in _actifs(groupes):
        libelle = _libelle_groupe(groupe)
        membres_par_groupe.setdefault(libelle, 0)
        key = _roster_key(groupe)
        raw_members = rosters_bruts.get(key)
        if not raw_members:
            continue

        roster = filter_roster_by_sigle(
            raw_members,
            groupe["roster_chambre"],
            groupe["groupe_sigle"],
        )

        for membre in roster:
            slug = membre.get("slug")
            if not slug or slug in candidats_par_slug:
                continue
            candidats_par_slug[slug] = {
                "nom": membre.get("nom"),
                "slug": slug,
                "parti": None,
                "famille_politique": None,
                "statut": "roster_groupe",
                "date_declaration": None,
                # `source` était `<domaine NosDéputés>/<slug>`, construit par
                # `group_roster._base_url_for` depuis la législature. Les deux
                # sont partis avec la plateforme (#529). La fiche AN de
                # l'acteur la remplace : c'est la source dont le membre vient
                # réellement, et elle est vérifiable (règle 2). `None` quand
                # AMO30 n'a pas rendu d'`acteur_ref` — jamais une URL inventée
                # (règle 5).
                "source": (
                    acteur_ref_to_pseudo_url(membre["acteur_ref"])
                    if membre.get("acteur_ref")
                    else None
                ),
                "notes": f"Membre du groupe {groupe['groupe_sigle']} ({groupe['groupe_nom']}), issu du roster réel {groupe['chambre']}.",
                # #850 — l'acteur que l'organe AMO30 désigne, EN CLAIR : la
                # collecte le reçoit tel quel au lieu de le re-deviner depuis
                # le slug. `source` en portait déjà l'identifiant, mais encodé
                # dans une URL que rien ne relisait. `None` quand AMO30 ne l'a
                # pas rendu — la collecte retombe alors sur la table.
                "acteur_ref": membre.get("acteur_ref"),
            }
            membres_par_groupe[libelle] += 1

    return list(candidats_par_slug.values()), membres_par_groupe


def membres_sans_slug(
    groupes: list[dict[str, Any]],
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Les membres que `build_roster_candidats_detaille` laisse tomber (#527).

    Un membre sans `slug` ne peut alimenter aucun profil : `<slug>.pivot.json`
    **est** le nom du fichier (#487). L'aplatissement l'ignore donc, et
    l'ignorait jusqu'ici **sans un mot** — la forme exacte du trou muet de #510
    et #501.

    Ça ne coûtait rien tant que la source était NosDéputés, qui n'a pas d'autre
    identifiant que le slug : il n'y avait pas de membre sans slug. AMO30 en a,
    par construction — il publie un `PA######` et l'état civil.

    **Ce que compte cette fonction a changé de nature avec #708.** Jusque-là
    elle comptait « pas d'entrée dans la table du lot 2 », et c'était une
    circularité : la table se construit depuis les profils publiés, donc aucun
    membre nouveau ne pouvait entrer — 156 des 461 entrées des 5 rosters de la
    17e, 33,8 %. Depuis #708 un membre sans entrée reçoit
    `slugify(état civil AMO30)`, et **ne reste ici que ce qui n'a pas pu être
    attribué** : le slug visé appartient déjà à quelqu'un d'autre, deux acteurs
    AMO30 le visent ensemble, ou l'état civil ne donne rien à slugifier
    (`an_roster.MOTIFS_SLUG_NON_ATTRIBUE`).

    Le compteur reste donc **vrai** : il dit ce qui est réellement écarté, et
    il n'est pas ramené à zéro par construction. Mesuré le 02/09/2026 sur les
    1 662 acteurs de l'index GP sans entrée de table, dont les 160 des 10
    groupes configurés : **0**. Ce zéro
    est une mesure du corpus, pas une propriété du code — le jour où une
    deuxième *Alexandra Martin* est élue, il vaut 2 et l'annotation les nomme.

    Non bloquant, et c'est le même choix qu'à #527 : une collision se tranche à
    la main dans `raw_data/correspondance_acteurs_an.json`, elle n'arrête pas un
    run. Ce qui doit rester bruyant, c'est son **nombre s'il bouge**.

    Fonction pure : elle ne lit que ce que la collecte a déjà rendu.
    """
    sans_slug: list[dict[str, Any]] = []
    for groupe in _actifs(groupes):
        raw_members = rosters_bruts.get(_roster_key(groupe))
        if not raw_members:
            continue
        roster = filter_roster_by_sigle(
            raw_members,
            groupe["roster_chambre"],
            groupe["groupe_sigle"],
        )
        for membre in roster:
            if membre.get("slug"):
                continue
            sans_slug.append(
                {
                    "groupe": _libelle_groupe(groupe),
                    "nom": membre.get("nom"),
                    "mandat_debut": membre.get("mandat_debut"),
                    "mandat_fin": membre.get("mandat_fin"),
                }
            )
    return sans_slug


def resume_membres_sans_slug(sans_slug: list[dict[str, Any]]) -> str:
    """Une ligne, nommant chaque membre écarté — destination : une annotation.

    Bornée à `_MAX_MEMBRES_NOMMES` noms parce qu'une annotation GitHub Actions
    tient sur une ligne ; le **décompte**, lui, n'est jamais tronqué, et le
    reste se relit avec `python3 src/an_roster.py --divergence`.
    """
    noms = [
        f"{m['groupe']}/{m['nom'] or '?'} ({m['mandat_debut']} → {m['mandat_fin']})"
        for m in sans_slug
    ]
    suffixe = ""
    if len(noms) > _MAX_MEMBRES_NOMMES:
        suffixe = f" (+{len(noms) - _MAX_MEMBRES_NOMMES} autre(s))"
        noms = noms[:_MAX_MEMBRES_NOMMES]
    return (
        f"ROSTER_SANS_SLUG — {len(sans_slug)} membre(s) du roster n'ont pas de slug "
        "et ne seront donc pas collectés ni publiés : "
        + "; ".join(noms)
        + suffixe
        + ". Depuis #708 un membre sans entrée de correspondance reçoit "
        "slugify(état civil AMO30) : ceux-ci restent dehors parce que le slug "
        "visé est DÉJÀ PORTÉ par quelqu'un d'autre, ou visé par deux acteurs à "
        "la fois. Ça se tranche à la main dans "
        "raw_data/correspondance_acteurs_an.json ; motif entrée par entrée : "
        "python3 src/an_roster.py --divergence."
    )


def membres_slug_fabrique(
    groupes: list[dict[str, Any]],
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Les membres qui entrent par un slug **fabriqué**, jamais relu (#708).

    Le miroir de `membres_sans_slug`, et il est aussi nécessaire qu'elle : une
    porte qui s'ouvre sans qu'aucun compteur ne le dise est le trou muet de
    #510, simplement retourné. Un slug fabriqué est un identifiant que
    `slugify` a déduit d'un état civil, pas une correspondance prouvée (#525) —
    et le run qui publiera ces profils sera arrêté par la §5b du contrôle
    qualité tant que leur entrée n'aura pas été relue et committée.

    Fonction pure : elle ne lit que ce que la collecte a déjà rendu.
    """
    fabriques: list[dict[str, Any]] = []
    for groupe in _actifs(groupes):
        raw_members = rosters_bruts.get(_roster_key(groupe))
        if not raw_members:
            continue
        roster = filter_roster_by_sigle(
            raw_members,
            groupe["roster_chambre"],
            groupe["groupe_sigle"],
        )
        for membre in roster:
            if membre.get("slug") and membre.get("slug_origine") == "fabrique":
                fabriques.append(
                    {
                        "groupe": _libelle_groupe(groupe),
                        "nom": membre.get("nom"),
                        "slug": membre.get("slug"),
                    }
                )
    return fabriques


def resume_membres_slug_fabrique(fabriques: list[dict[str, Any]]) -> str:
    """Une ligne, bornée comme `resume_membres_sans_slug` — même destination.

    Le **décompte** n'est jamais tronqué ; les noms le sont, parce qu'une
    annotation GitHub Actions tient sur une ligne.
    """
    noms = [f"{m['groupe']}/{m['slug']}" for m in fabriques]
    suffixe = ""
    if len(noms) > _MAX_MEMBRES_NOMMES:
        suffixe = f" (+{len(noms) - _MAX_MEMBRES_NOMMES} autre(s))"
        noms = noms[:_MAX_MEMBRES_NOMMES]
    return (
        f"ROSTER_SLUG_FABRIQUE — {len(fabriques)} membre(s) entrent avec un slug "
        "fabriqué par slugify(état civil AMO30), sans correspondance relue "
        f"(#708, #525) : {'; '.join(noms)}{suffixe}. "
        "Leur entrée de raw_data/correspondance_acteurs_an.json reste à relire : "
        "python3 src/build_correspondance_acteurs_an.py la propose, et la §5b du "
        "contrôle qualité bloque le commit tant qu'elle manque."
    )


def anomalies_roster(
    groupes: list[dict[str, Any]],
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
    membres_par_groupe: dict[str, int],
    candidats: list[dict[str, Any]],
    echecs: Optional[dict[tuple[str, Optional[str]], Exception]] = None,
) -> list[str]:
    """Les raisons de NE PAS écrire le roster. Liste vide = écriture sûre.

    Fonction pure : elle ne lit que ce que la collecte a déjà relevé. Les trois
    motifs sont ceux du docstring de module (#511), dans cet ordre — du plus
    causal au plus symptomatique, pour que le premier message affiché soit celui
    qui explique les autres.

    `echecs` (#524) porte l'exception de chaque clé tombée, telle que
    `fetch_rosters_bruts` l'a interceptée : c'est ce qui fait dire à
    l'annotation `HTTPError: 500 …` plutôt qu'« en échec ». Optionnel — une
    clé sans exception connue garde le message d'origine plutôt que d'inventer
    une cause (AGENTS.md §2 règle 5).
    """
    anomalies: list[str] = []
    echecs = echecs or {}

    cles_en_echec = {cle for cle, roster in rosters_bruts.items() if roster is None}
    for cle in sorted(cles_en_echec, key=lambda c: (c[0], c[1] or "")):
        chambre, legislature = cle
        cause = echecs.get(cle)
        precision = f" ({resume_exception(cause)})" if cause is not None else ""
        anomalies.append(
            f"récupération du roster ({chambre}, législature={legislature or 'courante'}) "
            f"en échec{precision} : la composition de ses groupes est INCONNUE, pas vide."
        )

    for groupe in _actifs(groupes):
        if _roster_key(groupe) in cles_en_echec:
            # Déjà expliqué par la ligne ci-dessus ; le répéter par groupe
            # noierait la cause sous ses conséquences.
            continue
        libelle = _libelle_groupe(groupe)
        if membres_par_groupe.get(libelle, 0) == 0:
            anomalies.append(
                f"groupe {libelle} ({groupe.get('groupe_sigle')}) : 0 membre retenu "
                "alors que son roster a bien été récupéré — sigle renommé en amont, "
                "ou groupe dissous à retirer de la config."
            )

    if not candidats:
        anomalies.append("roster total vide : aucun candidat à écrire.")

    return anomalies


def build_roster_candidats(
    groupes: list[dict[str, Any]],
    rosters_bruts: dict[tuple[str, Optional[str]], Optional[list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Aplatit le roster de chaque groupe en une liste unique de candidats, au format
    attendu par generate_all_profiles.load_candidats() (shape {"candidats": [...]}).

    Fonction pure (aucun accès réseau) : `rosters_bruts` doit déjà contenir, pour
    chaque (roster_chambre, legislature) référencée par `groupes`, le roster brut
    (non filtré) issu de `fetch_full_roster`, ou `None` en cas d'échec réseau (le
    groupe correspondant est alors ignoré).

    Un membre ne peut appartenir qu'à un seul groupe par fetch (`groupe_sigle` est
    un champ mono-valué côté API), donc aucune fusion cross-groupe n'est attendue en
    conditions normales. On déduplique malgré tout par `slug` (garde-fou), au cas où
    deux entrées de la config pointeraient vers le même (chambre, legislature) avec
    un sigle mal renseigné : la première occurrence rencontrée est conservée.

    Reste la façon normale d'obtenir la liste seule. `main()` passe par
    `build_roster_candidats_detaille` parce qu'il a besoin, en plus, du décompte
    par groupe pour décider s'il a le droit d'écrire (#511).
    """
    candidats, _ = build_roster_candidats_detaille(groupes, rosters_bruts)
    return candidats


def generate_roster_candidats(groupes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Récupère les rosters réseau nécessaires puis construit la liste aplatie de candidats."""
    rosters_bruts, _ = fetch_rosters_bruts(groupes)
    return build_roster_candidats(groupes, rosters_bruts)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--config",
        default="raw_data/groupes_reels.json",
        metavar="FICHIER",
        help="Fichier JSON listant les groupes à agréger (défaut : raw_data/groupes_reels.json).",
    )
    parser.add_argument(
        "--out",
        default="raw_data/roster_candidats.json",
        metavar="FICHIER",
        help="Fichier JSON de sortie (défaut : raw_data/roster_candidats.json).",
    )
    parser.add_argument(
        "--rosters-bruts-out",
        default=None,
        metavar="FICHIER",
        help="Écrire AUSSI les rosters bruts (non filtrés, tels que rendus par "
             "fetch_full_roster) dans ce fichier, pour que les autres étages du "
             "run les réutilisent au lieu de refetcher la même liste — voir "
             "generate_group_profiles.py --rosters-bruts (#518). Non écrit par "
             "défaut : seul le run CI en a besoin.",
    )
    parser.add_argument(
        "--sans-gouvernements",
        action="store_true",
        help="Ne pas ajouter les membres des gouvernements, ni au roster brut ni "
             "au roster de candidats (#996). Débranche donc leur collecte. "
             "Le roster des groupes est inchangé.",
    )
    parser.add_argument(
        "--autoriser-roster-incomplet",
        action="store_true",
        help="Écrire le roster MALGRÉ une collecte incomplète (fetch en échec, "
             "groupe à 0 membre, roster vide). Les anomalies restent affichées. "
             "N'est câblé sur aucun input de generate-data.yml, délibérément : "
             "le remède d'une source en timeout est de relancer, pas de publier "
             "quand même (#511). Existe pour le travail local et pour qu'une "
             "panne de ce garde-fou ne bloque pas indéfiniment.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    config_path = Path(args.config)
    out_path = Path(args.out)
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"[!] Lecture de {config_path} impossible : {exc}", file=sys.stderr)
        return 1

    groupes = config.get("groupes") or []
    if not groupes:
        print(f"[!] Aucun groupe à agréger dans {config_path}.", file=sys.stderr)
        return 1

    # Une suspension se voit dans les logs du run qui la subit, jamais seulement
    # dans la config (#516) : sans cette ligne, un roster amputé de 300 membres
    # ressemble à un roster complet.
    groupes_actifs, groupes_suspendus = partitionner_groupes(groupes)
    for groupe in groupes_suspendus:
        print(f"⏸  {resume_suspension(groupe)}", file=sys.stderr)
    if not groupes_actifs:
        # #524 : « tous les groupes suspendus » est une DÉCISION, pas une
        # anomalie — chacune de ces entrées porte `depuis`/`motif`/
        # `references`/`condition_reprise`, que la gate de #516 exige en dur.
        # Sortir en 1 faisait échouer le run pour cette décision, donc
        # interdisait le seul remède documenté à une source en panne. Le code
        # 2 dit à l'appelant de SAUTER la branche roster : rien n'est écrit,
        # et surtout pas un roster à 0 candidat (#511).
        message = (
            f"ROSTER_SUSPENDU — les {len(groupes_suspendus)} groupe(s) de {config_path} "
            "ont tous leur extraction suspendue : il n'y a rien à agréger, "
            f"{out_path} n'est pas écrit et la branche roster du run est "
            f"sautée (sortie {EXIT_ROSTER_INDISPONIBLE}). Réactiver au moins une entrée "
            "pour la rouvrir."
        )
        print(f"[!] {message}", file=sys.stderr)
        # `warning` et non `error` : un run qui saute une branche délibérément
        # suspendue n'a pas de défaut à signaler, mais l'onglet de résumé doit
        # dire POURQUOI il ne publie aucun profil de roster — sans quoi la
        # suspension devient invisible au bout de deux runs (#516).
        gha.annoter("warning", message)
        return EXIT_ROSTER_INDISPONIBLE

    # Le fetch et l'aplatissement sont appelés séparément (et non via
    # `generate_roster_candidats`) pour garder sous la main ce que chacun sait :
    # quelles clés ont échoué, et combien de membres chaque groupe a rendus.
    # C'est exactement l'information que la version jusqu'à #511 jetait avant
    # d'écrire son résultat vide.
    # `echecs` porte l'exception de chaque clé tombée (#524) : c'est elle que
    # l'annotation nomme, et sans elle « en échec » était tout ce qu'un run
    # mort laissait derrière lui.
    rosters_bruts, echecs = fetch_rosters_bruts(groupes)
    candidats, membres_par_groupe = build_roster_candidats_detaille(groupes, rosters_bruts)

    # Avant les anomalies, et séparément d'elles : un membre sans slug n'est
    # pas une panne, c'est une lacune de la table du lot 2 (#525). Il ne doit
    # donc bloquer aucune écriture — mais il ne doit pas non plus disparaître
    # sans laisser de trace, ce qu'il faisait jusqu'à #527.
    sans_slug = membres_sans_slug(groupes, rosters_bruts)
    if sans_slug:
        resume = resume_membres_sans_slug(sans_slug)
        print(f"[i] {resume}", file=sys.stderr)
        gha.annoter("warning", resume)

    # Le miroir (#708). En `notice` et pas en `warning` : ce n'est pas une
    # anomalie, c'est un fait — des membres entrent par un identifiant que
    # personne n'a relu. Le taire ferait de l'ouverture de la porte le
    # symétrique exact du trou que #527 avait bouché.
    fabriques = membres_slug_fabrique(groupes, rosters_bruts)
    if fabriques:
        resume = resume_membres_slug_fabrique(fabriques)
        print(f"[i] {resume}", file=sys.stderr)
        gha.annoter("notice", resume)

    anomalies = anomalies_roster(groupes, rosters_bruts, membres_par_groupe, candidats, echecs)
    if anomalies:
        for anomalie in anomalies:
            print(f"[!] {anomalie}", file=sys.stderr)
            # #518 : chaque anomalie est aussi une annotation. Les runs des 21,
            # 22 et 24/08/2026 sont morts ici, et la seule trace qu'un lecteur
            # de l'onglet « Summary » en gardait était
            # `Process completed with exit code 1` — la cause (quelle clé de
            # fetch, quel groupe) restait dans un log de step à télécharger.
            # C'est le motif exact du garde-fou : une donnée non résolue doit
            # échouer BRUYAMMENT, et un log qu'il faut aller chercher n'est pas
            # du bruit (ROADMAP.md, #516).
            gha.annoter("error", f"ROSTER — {anomalie}")
        if not args.autoriser_roster_incomplet:
            message = (
                f"ROSTER_INCOMPLET — {out_path} N'A PAS été écrit : "
                f"{len(candidats)} candidat(s) collecté(s) sur une collecte incomplète. "
                "L'écrire publierait une composition de groupe non mesurée, et la passe "
                "pivot suivante itérerait sur ce qu'il en reste (AGENTS.md §2 règle 5, "
                "#511). Relancer, ou --autoriser-roster-incomplet en connaissance de cause."
            )
            print(f"[!] {message}", file=sys.stderr)
            gha.annoter("error", message)
            return 1
        print("[!] --autoriser-roster-incomplet : écriture forcée malgré les anomalies "
              "ci-dessus.", file=sys.stderr)
        # Écriture forcée : l'annotation reste, en `warning`. Le run continue,
        # donc rien d'autre ne dira que ce qu'il publie a été mesuré partiellement.
        gha.annoter(
            "warning",
            f"ROSTER_INCOMPLET toléré (--autoriser-roster-incomplet) : {out_path} est "
            f"écrit avec {len(candidats)} candidat(s) malgré {len(anomalies)} anomalie(s).",
        )

    # #996 lot 2 — les membres des gouvernements entrent dans le roster BRUT,
    # sous leur propre clé, pour que la passe de correspondance dérive leurs
    # entrées. #996 lot 3 — ils entrent AUSSI dans `roster_candidats.json`,
    # sous `statut: "roster_gouvernement"` : c'est ce fichier que les shards
    # lisent, donc c'est par lui que leur collecte part.
    #
    # APRÈS le portail d'anomalies, et AVANT l'écriture : après, parce qu'un
    # roster de groupe incomplet ne doit pas déclencher un téléchargement
    # d'AMO30 de plus ; avant, parce que les deux fichiers doivent décrire la
    # même collecte à la même seconde (#518).
    #
    # Un échec de lecture de l'archive est non fatal : le roster des groupes
    # est déjà constitué, et une clé absente vaut mieux qu'une liste vide
    # (§2 règle 5). Conséquence assumée — ce run ne collecte alors aucun
    # membre de gouvernement, et la fusion additive garde ceux du run
    # précédent ; il ne publie pas une composition amputée.
    if not args.sans_gouvernements:
        try:
            membres_gouv = membres_des_gouvernements()
        except Exception as exc:  # noqa: BLE001 — voir le commentaire ci-dessus
            print(f"  [!] Roster des gouvernements indisponible : {exc}", file=sys.stderr)
        else:
            rosters_bruts[CLE_ROSTER_GOUVERNEMENTS] = membres_gouv
            fabriques_gouv = sum(1 for m in membres_gouv if m["slug_origine"] == "fabrique")
            # `deja_pris` : les slugs du roster des groupes gagnent. Une
            # personne à la fois députée et ministre reste `roster_groupe`,
            # sans quoi elle sortirait de la cohésion de son groupe.
            candidats_gouv = candidats_des_gouvernements(
                membres_gouv, deja_pris=(c["slug"] for c in candidats))
            candidats.extend(candidats_gouv)
            print(
                f"→ {len(membres_gouv)} membre(s) de gouvernement, dont "
                f"{fabriques_gouv} slug(s) fabriqué(s) ; "
                f"{len(candidats_gouv)} ajouté(s) au roster de candidats, "
                f"{len(membres_gouv) - len(candidats_gouv)} déjà porté(s) par un groupe.",
                file=sys.stderr,
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"candidats": candidats}, ensure_ascii=False, indent=2), encoding="utf-8")

    # Le roster BRUT part avec le roster de candidats, et sous la MÊME
    # autorisation d'écriture (#518) : les deux décrivent la même collecte, à
    # la même seconde. Publier l'un sans l'autre rendrait au consommateur une
    # composition de groupe qui n'est pas celle sur laquelle les profils ont
    # été collectés — le défaut même que ce transit ferme.
    if args.rosters_bruts_out:
        chemin_bruts = Path(args.rosters_bruts_out)
        cles_ecrites = ecrire_rosters_bruts(chemin_bruts, rosters_bruts)
        print(
            f"→ {cles_ecrites} roster(s) brut(s) écrit(s) dans {chemin_bruts}.",
            file=sys.stderr,
        )

    # Le compte nomme sa population (#630, §9) : depuis #996 lot 3 ce fichier
    # porte deux rosters, et « 1 350 candidats » n'aurait dit lequel.
    nb_gouv = sum(1 for c in candidats if c["statut"] == ROSTER_GOUVERNEMENT)
    detail = f" ({len(candidats) - nb_gouv} de groupe · {nb_gouv} de gouvernement)" if nb_gouv else ""
    print(
        f"→ {len(candidats)} entrée(s) de roster écrite(s){detail} dans {out_path}.",
        file=sys.stderr,
    )
    for libelle, nombre in sorted(membres_par_groupe.items()):
        print(f"   · {libelle} : {nombre} membre(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
