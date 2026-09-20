#!/usr/bin/env python3
"""
groupes_config.py — Lecture partagée de `raw_data/groupes_reels.json`, et
**suspension temporaire** de l'extraction d'un groupe configuré (#516).

## Pourquoi une suspension plutôt qu'une suppression

`raw_data/groupes_reels.json` pilote trois choses à la fois : les fetchs de
roster (`generate_roster_candidats.py`), la génération des fiches de groupe
(`generate_group_profiles.py`) et la liste des fichiers attendus par le
quality gate (`check_quality_gate._report_groupes`). Retirer une entrée les
coupe toutes les trois **et** fait disparaître un fichier publié — ce que
`audit_diff_profils` traite, à raison, comme une perte bloquante (#460/#470).

Une suspension coupe la **collecte** sans toucher au **publié** : le fichier
de groupe déjà committé reste en place, servi par l'onglet Groupes, gelé à sa
dernière génération réussie. C'est une position réversible d'une ligne, ce
qu'une suppression n'est pas.

## Le bloc de suspension se documente, sinon il ne vaut rien

    "extraction_suspendue": {
      "depuis": "2026-08-24",
      "motif": "…",
      "references": ["#516", "run 32548486495"],
      "condition_reprise": "…"
    }

Les quatre champs sont **exigés** (`anomalies_suspension`), et le quality gate
en fait une erreur dure. Une suspension sans motif, sans date, sans référence
et sans condition de reprise est un assouplissement silencieux qui devient
permanent par oubli — exactement ce contre quoi #511 a été écrit. La condition
de reprise est le champ qui empêche le « temporaire » de durer : c'est elle
qu'on relit pour savoir si on peut réactiver.

Une valeur fausse (`false`, `null`, absente) = groupe actif. Le groupe n'est
jamais « à moitié » suspendu : la granularité est l'entrée de config entière.

Les trois décisions à relire avant de toucher à ce fichier
----------------------------------------------------------
Cinq décisions nomment un symbole de ce module ; la liste complète et à jour est
dans `docs/decisions-par-module.md`. Ces trois-là portent ce que la
configuration **autorise à publier** :

- `docs/decisions/extraction-groupe-suspendue-516.md` — suspendre n'est pas
  retirer : retirer une entrée supprime un fichier publié, ce que
  `audit_diff_profils` bloque. Les quatre champs de `extraction_suspendue` sont
  exigés, et le portail de qualité en fait une erreur dure.
- `docs/decisions/position-politique-groupes-686.md` — la qualification d'un
  groupe est celle que l'Assemblée déclare, recopiée depuis la table committée
  et **jamais déduite d'une ressemblance de sigle** (`RE` ne se déduit pas de
  `REN`). `position` est le résumé dérivé de `organes[]`, jamais un choix.
- `docs/decisions/fiches-groupe-17e-legislature-700.md` — `succede_a` est
  **notre affirmation, pas un champ de l'AN** : le bloc publié porte
  `etabli_par` et **refuse** un `source_url`, miroir exact du précédent. Une
  succession qui ne résout pas est refusée, et la validation se fait **après**
  la boucle pour que le verdict ne dépende pas de l'ordre des entrées.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from schema_groupe import (
    ETABLI_PAR_RELECTURE_HUMAINE,
    POSITIONS_POLITIQUES_GROUPE,
    resumer_position_politique,
)
from schema_pivot import POSITION_POLITIQUE_AN_VERS_PIVOT

#: Clé portant la suspension dans une entrée de `groupes_reels.json`.
#: Nommée `extraction_suspendue` et non `suspendu` : c'est l'**extraction**
#: qui s'arrête, pas le groupe parlementaire — et `suspendu` est déjà pris,
#: dans un tout autre sens, par `mandats[].suspendu_pour_fonction_gouvernementale`
#: (AGENTS.md §5).
CLE_SUSPENSION = "extraction_suspendue"

#: Les quatre champs qui font d'une suspension une décision documentée.
CHAMPS_SUSPENSION_REQUIS: tuple[str, ...] = (
    "depuis",
    "motif",
    "references",
    "condition_reprise",
)


def libelle_groupe(groupe: dict[str, Any]) -> str:
    """Nom d'un groupe dans les messages, stable et sans ambiguïté.

    `groupe_id` distingue les deux `LR` (`AN:LR` et `Senat:LR`), ce que le seul
    sigle ne ferait pas. Repli sur `<chambre>:<sigle>` pour une config plus
    ancienne, `?` en dernier recours (un libellé n'est jamais un motif d'échec :
    l'anomalie qu'il nomme, elle, l'est).
    """
    if groupe.get("groupe_id"):
        return str(groupe["groupe_id"])
    return f"{groupe.get('chambre') or '?'}:{groupe.get('groupe_sigle') or '?'}"


def est_suspendu(groupe: dict[str, Any]) -> bool:
    """`True` si l'extraction de ce groupe est suspendue (#516)."""
    return bool(groupe.get(CLE_SUSPENSION))


def partitionner_groupes(
    groupes: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Sépare `(groupes actifs, groupes suspendus)`, dans l'ordre de la config."""
    actifs = [groupe for groupe in groupes if not est_suspendu(groupe)]
    suspendus = [groupe for groupe in groupes if est_suspendu(groupe)]
    return actifs, suspendus


def anomalies_suspension(groupe: dict[str, Any]) -> list[str]:
    """Les raisons pour lesquelles une suspension n'est pas documentée.

    Liste vide = suspension en règle, ou groupe actif. Fonction pure.
    """
    if not est_suspendu(groupe):
        return []

    libelle = libelle_groupe(groupe)
    bloc = groupe.get(CLE_SUSPENSION)
    if not isinstance(bloc, dict):
        return [
            f"{libelle} : '{CLE_SUSPENSION}' doit être un objet documenté "
            f"({', '.join(CHAMPS_SUSPENSION_REQUIS)}), pas {type(bloc).__name__}."
        ]

    manquants = [champ for champ in CHAMPS_SUSPENSION_REQUIS if not bloc.get(champ)]
    if manquants:
        return [
            f"{libelle} : suspension d'extraction non documentée — "
            f"champ(s) manquant(s) : {', '.join(manquants)}. Une suspension sans "
            "motif ni condition de reprise devient permanente par oubli (#516)."
        ]
    return []


#: Fichier de configuration des groupes. Il vit ICI depuis #558, et non plus
#: dans `an_roster` : ce module est celui qui dit ce que `groupes_reels.json`
#: pilote, et trois consommateurs le lisent sans avoir la moindre raison de
#: dépendre du dérivateur de roster AN. `an_roster` le réexporte pour ses
#: propres appelants.
CHEMIN_CONFIG_GROUPES = Path("raw_data") / "groupes_reels.json"

#: Répertoire des fiches de groupe publiées.
GROUPES_PUBLIES_DIR = Path("pivot_data") / "groupes"


def index_membres_de_groupes_suspendus(
    groupes: list[dict[str, Any]],
    groupes_dir: Optional[Path] = None,
) -> dict[str, dict[str, Any]]:
    """`membre_id` → entrée de config du groupe **suspendu** qui l'explique.

    ## Pourquoi la fiche publiée, et pas le roster

    Un groupe suspendu n'est plus interrogé : `generate_roster_candidats.py` ne
    construit même pas sa clé de fetch (#516). Sa composition n'existe donc plus
    nulle part **sauf** dans la fiche déjà publiée et gelée,
    `pivot_data/groupes/<fichier>` — qui est précisément la source sur laquelle
    #558 a mesuré sa population. Lire ailleurs reviendrait à ne rien lire.

    ## Pourquoi pas la provenance, et pourquoi pas `chambre`

    Deux pièges, tous deux mesurés le 29/08/2026 sur les 481 profils publiés :

    1. **`chambre` ne dit pas la chambre.** Les 20 membres des deux fiches
       `groupe-Senat-*` publient `chambre: "AN"` (défaut distinct, tenu par
       #486). Compter les sénateurs par ce champ en rend **zéro**, et fait
       conclure que la population a disparu.
    2. **La provenance ne recouvre pas la population.** 19 des 20 sont
       `roster_groupe` ; le vingtième est `bruno-retailleau`, de provenance
       `candidat_declare` — et c'est le plus visible des vingt. Un correctif
       branché sur la provenance seule l'aurait manqué.

    L'appartenance, elle, se lit sans ambiguïté et pour les vingt.

    Une fiche absente ou illisible ne lève pas : un groupe suspendu dont la
    fiche a disparu ne rend simplement aucun membre, et les profils concernés
    retombent sur la dérivation générale. Ce module n'est pas le garde-fou du
    fichier publié — `audit_diff_profils` l'est déjà (#460/#470).
    """
    racine = Path(groupes_dir) if groupes_dir is not None else GROUPES_PUBLIES_DIR
    index: dict[str, dict[str, Any]] = {}
    for groupe in groupes:
        if not est_suspendu(groupe):
            continue
        fichier = groupe.get("fichier")
        if not fichier:
            continue
        chemin = racine / str(fichier)
        try:
            fiche = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        if not isinstance(fiche, dict):
            continue
        for membre in fiche.get("membres") or ():
            if not isinstance(membre, dict):
                continue
            membre_id = membre.get("membre_id")
            if isinstance(membre_id, str) and membre_id:
                index.setdefault(membre_id, groupe)
    return index


def resume_suspension(groupe: dict[str, Any]) -> str:
    """Une ligne lisible en log : libellé, motif, date, références."""
    bloc = groupe.get(CLE_SUSPENSION)
    if not isinstance(bloc, dict):
        return f"{libelle_groupe(groupe)} : extraction suspendue (non documentée)"

    references = bloc.get("references") or []
    if isinstance(references, str):
        references = [references]
    suffixe = f" [{', '.join(str(r) for r in references)}]" if references else ""
    return (
        f"{libelle_groupe(groupe)} : extraction suspendue depuis "
        f"{bloc.get('depuis') or '?'} — {bloc.get('motif') or '?'}{suffixe}"
    )


# ── La table de correspondance des sigles, committée (#526, portée ici #686) ──
#: Clé portant la table dans `raw_data/groupes_reels.json`. Un sigle publié et
#: sa correspondance AN sont deux faces du même choix éditorial : les séparer
#: en deux fichiers garantirait qu'un jour l'un bouge sans l'autre.
CLE_CORRESPONDANCE_SIGLES = "correspondance_sigles_an"

#: Clé portant, dans une entrée de cette table, la qualification que
#: l'Assemblée nationale donne elle-même au groupe (#686).
CLE_POSITION_POLITIQUE = "position_politique_an"

#: Clé portant, dans une entrée de cette table, le `groupe_id` du groupe de la
#: législature précédente dont celui-ci prend la suite (#700). **Optionnelle** :
#: les 5 entrées de la XVIe n'ont pas de prédécesseur dans le périmètre du
#: dépôt, et une clé absente dit exactement cela — jamais « succession
#: inconnue ». Présente, elle doit résoudre : voir `_valider_succession`.
CLE_SUCCESSION = "succede_a"

#: Clé portant, dans une entrée de cette table, les organes successifs du
#: groupe DANS sa législature, avec leur libellé et leurs bornes (#815) — ce
#: que la fiche publie en `historique_noms`. Mesurée sur AMO30 et committée,
#: comme la position politique (#686) : l'étape groupe du run ne lit aucune
#: archive. **Optionnelle** ; présente, elle doit coïncider organe pour organe
#: avec `organes_an`, sans quoi deux écritures du même fait divergeraient en
#: silence — le défaut que #815 a payé sur les deux listes du fichier.
CLE_HISTORIQUE_ORGANES = "historique_organes_an"


class CorrespondanceSiglesInvalide(ValueError):
    """La table sigle publié → sigle(s) AN est absente ou viole un invariant."""


def _valider_position_politique_an(
    entree: dict[str, Any],
    libelle: str,
) -> dict[str, Any]:
    """Valide `position_politique_an` d'une entrée, et la rend.

    Le champ est **obligatoire** (#686), contrairement au champ publié qui,
    lui, reste optionnel sur une fiche non régénérée. La dissymétrie est
    voulue : une fiche déjà publiée ne se réécrit pas rétroactivement, mais une
    entrée de table sans qualification relue laisserait le générateur choisir
    tout seul ce qu'il publie — et c'est précisément ce que la table existe
    pour lui interdire.

    Trois invariants, en plus du vocabulaire :

    1. chaque organe cité est un organe **de la table** (`organes_an`) : la
       preuve et le fil-piège décrivent le même groupe, ou l'un des deux est
       périmé ;
    2. `valeur_source` est présente sur chaque organe — c'est la chaîne du
       référentiel, verbatim, et sans elle la traduction n'est plus vérifiable ;
    3. `position` est **exactement** le résumé des déclarations
       (`resumer_position_politique`), jamais un choix.
    """
    bloc = entree.get(CLE_POSITION_POLITIQUE)
    if not isinstance(bloc, dict):
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : '{CLE_POSITION_POLITIQUE}' absent ou non-objet. "
            "L'Assemblée qualifie elle-même ses groupes "
            "(organe.positionPolitique) : cette qualification se recopie, "
            "relue et datée, elle ne se devine pas au moment de publier (#686). "
            "python3 src/an_roster.py --positions la remesure sur l'archive."
        )
    position = bloc.get("position")
    if position not in POSITIONS_POLITIQUES_GROUPE:
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : position politique {position!r} hors vocabulaire "
            f"{list(POSITIONS_POLITIQUES_GROUPE)}."
        )
    if not bloc.get("verifie_le"):
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : '{CLE_POSITION_POLITIQUE}.verifie_le' absent — une "
            "qualification non datée n'est pas relisible (#526)."
        )
    organes = bloc.get("organes")
    if not isinstance(organes, list) or not organes:
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : '{CLE_POSITION_POLITIQUE}.organes' doit lister les "
            "organes MESURÉS et ce que chacun déclare — c'est la preuve."
        )
    connus = list(entree.get("organes_an") or ())
    for organe in organes:
        if not isinstance(organe, dict):
            raise CorrespondanceSiglesInvalide(f"{libelle} : organe non-objet.")
        organe_an = organe.get("organe_an")
        if organe_an not in connus:
            raise CorrespondanceSiglesInvalide(
                f"{libelle} : l'organe {organe_an!r} déclare une position mais "
                f"n'est pas dans 'organes_an' ({connus}). La preuve et le "
                "fil-piège doivent décrire le même groupe (#526)."
            )
        if "valeur_source" not in organe:
            raise CorrespondanceSiglesInvalide(
                f"{libelle} : organe {organe_an} sans 'valeur_source' — la "
                "chaîne du référentiel, verbatim, est ce qui rend la "
                "traduction vérifiable."
            )
        attendu = POSITION_POLITIQUE_AN_VERS_PIVOT.get(organe.get("valeur_source"))
        if organe.get("position") != attendu:
            raise CorrespondanceSiglesInvalide(
                f"{libelle} : organe {organe_an} — "
                f"{organe.get('valeur_source')!r} ne se traduit pas en "
                f"{organe.get('position')!r} (POSITION_POLITIQUE_AN_VERS_PIVOT)."
            )
    resume = resumer_position_politique(organes)
    if position != resume:
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : position {position!r} alors que les organes déclarent "
            f"{resume!r}. Le résumé se dérive des déclarations, il ne se "
            "choisit pas — deux organes successifs qui divergent se publient "
            "'divergente', jamais repliés sur l'un des deux (#686)."
        )
    return bloc


def _valider_successions(
    entrees: list[dict[str, Any]],
    chemin: Path,
) -> None:
    """Vérifie que chaque `succede_a` de la table atteint une entrée qui existe.

    Une succession qui ne résout pas est une **référence orpheline** : le même
    défaut que #485 traite sur les clés publiées, à ceci près qu'ici il se
    corrige dans le fichier de configuration plutôt que dans un index. Un
    `succede_a` pointant sur un `groupe_id` absent publierait sur la fiche un
    `fichier` qu'aucun document ne porte — la vue empilée n'aurait rien à
    empiler, et rien ne le dirait.

    Trois refus, tous à seuil 0 :

    - le prédécesseur n'est pas dans la table ;
    - il n'a pas de `fichier` — l'affirmation n'atteindrait aucun document ;
    - il est l'entrée elle-même : un groupe ne se succède pas.

    Ce que cette fonction ne vérifie **pas** : que le fichier existe sur le
    disque. Cette table ne connaît pas `pivot_data/groupes/`, et c'est le §4 du
    portail de qualité qui tient ce contrôle-là, avec le répertoire sous la
    main.

    Raises:
        CorrespondanceSiglesInvalide: la première succession qui ne résout pas,
            **nommée** avec l'identifiant qu'elle cherchait.
    """
    par_groupe_id: dict[str, dict[str, Any]] = {
        str(entree["groupe_id"]): entree
        for entree in entrees
        if entree.get("groupe_id")
    }
    for entree in entrees:
        cibles = entree.get(CLE_SUCCESSION)
        if cibles is None:
            continue
        libelle = f"{entree['groupe_sigle']}-{entree['legislature']}"
        # #815 — UNE LISTE, ET RIEN D'AUTRE. Une chaîne nue est refusée
        # explicitement plutôt que tolérée : c'est l'ancienne forme, et
        # l'accepter en silence ferait cohabiter deux écritures du même fait
        # dans un fichier relu à la main.
        if not isinstance(cibles, list) or not cibles:
            raise CorrespondanceSiglesInvalide(
                f"{libelle} : '{CLE_SUCCESSION}' doit être une LISTE non vide de "
                f"`groupe_id`, reçu : {cibles!r}. Un groupe peut succéder à "
                "plusieurs — une fusion en a deux — et la forme unique ne "
                "savait pas l'écrire (#815)."
            )
        if len(cibles) != len(set(cibles)):
            raise CorrespondanceSiglesInvalide(
                f"{libelle} : '{CLE_SUCCESSION}' nomme deux fois le même "
                f"prédécesseur : {cibles!r}."
            )
        for cible in cibles:
            if not isinstance(cible, str) or not cible.strip():
                raise CorrespondanceSiglesInvalide(
                    f"{libelle} : '{CLE_SUCCESSION}' doit ne porter que des "
                    f"`groupe_id`, reçu : {cible!r}."
                )
            if cible == entree.get("groupe_id"):
                raise CorrespondanceSiglesInvalide(
                    f"{libelle} : '{CLE_SUCCESSION}' vaut son propre `groupe_id` "
                    f"({cible!r}) — un groupe ne se succède pas à lui-même."
                )
            predecesseur = par_groupe_id.get(cible)
            if predecesseur is None:
                raise CorrespondanceSiglesInvalide(
                    f"{libelle} : '{CLE_SUCCESSION}' nomme {cible!r}, qui n'est le "
                    f"`groupe_id` d'aucune entrée de {chemin}. Une succession qui "
                    "ne résout pas publierait une fiche renvoyant vers un document "
                    "inexistant (#700)."
                )
            if not predecesseur.get("fichier"):
                raise CorrespondanceSiglesInvalide(
                    f"{libelle} : le prédécesseur {cible!r} n'a pas de 'fichier' — "
                    "l'affirmation de succession n'atteindrait aucune fiche "
                    "publiée (#700)."
                )


def _valider_historique_organes(entree: dict[str, Any], libelle: str) -> None:
    """`historique_organes_an`, s'il est présent, redit `organes_an` sans le contredire.

    Raises:
        CorrespondanceSiglesInvalide: forme invalide, ou organes dans un autre
            ordre, en plus ou en moins que `organes_an`.
    """
    historique = entree.get(CLE_HISTORIQUE_ORGANES)
    if historique is None:
        return
    if not isinstance(historique, list) or not historique:
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : '{CLE_HISTORIQUE_ORGANES}' doit être une liste non vide."
        )
    for bloc in historique:
        if not isinstance(bloc, dict) or not all(
            bloc.get(cle) for cle in ("organe_an", "sigle_an", "nom", "debut")
        ) or "fin" not in bloc:
            raise CorrespondanceSiglesInvalide(
                f"{libelle} : chaque entrée de '{CLE_HISTORIQUE_ORGANES}' porte "
                f"organe_an, sigle_an, nom, debut et fin (null si ouvert) — reçu {bloc!r}."
            )
    if [b["organe_an"] for b in historique] != list(entree.get("organes_an") or []):
        raise CorrespondanceSiglesInvalide(
            f"{libelle} : '{CLE_HISTORIQUE_ORGANES}' nomme "
            f"{[b['organe_an'] for b in historique]} quand 'organes_an' nomme "
            f"{entree.get('organes_an')}. Les deux listes disent le même fait : "
            "l'une a bougé sans l'autre (#815)."
        )


def charger_correspondance_sigles(
    chemin: Optional[Path] = None,
) -> list[dict[str, Any]]:
    """Charge et valide la table `correspondance_sigles_an`.

    Chaque entrée doit porter `groupe_sigle` (le sigle **publié**),
    `legislature`, `sigles_an` (liste non vide), `organes_an` (liste des
    organes **mesurés** au moment de la relecture), `verifie_le` et
    `position_politique_an` (#686).

    `organes_an` n'est pas ce qui sert à construire le roster — c'est un
    **fil-piège** : si l'union des organes portant `sigles_an` cesse de
    coïncider avec cette liste, l'AN a ouvert ou fermé un organe et la table
    doit être relue. Le roster, lui, se construit par sigle, pour qu'un organe
    successif nouvellement ouvert entre quand même dans l'union plutôt que
    d'être perdu en silence.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_CONFIG_GROUPES
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CorrespondanceSiglesInvalide(
            f"Configuration des groupes illisible ({chemin}) : {exc}"
        ) from exc
    except ValueError as exc:
        raise CorrespondanceSiglesInvalide(f"{chemin} : JSON invalide — {exc}") from exc

    bloc = document.get(CLE_CORRESPONDANCE_SIGLES)
    if not isinstance(bloc, dict):
        raise CorrespondanceSiglesInvalide(
            f"{chemin} : clé '{CLE_CORRESPONDANCE_SIGLES}' absente ou non-objet. "
            "La correspondance des sigles est un artefact committé, pas une "
            "heuristique (#526)."
        )
    entrees = bloc.get("groupes")
    if not isinstance(entrees, list) or not entrees:
        raise CorrespondanceSiglesInvalide(
            f"{chemin} : '{CLE_CORRESPONDANCE_SIGLES}.groupes' absent ou vide."
        )

    vues: set[tuple[str, str]] = set()
    valides: list[dict[str, Any]] = []
    for entree in entrees:
        if not isinstance(entree, dict):
            raise CorrespondanceSiglesInvalide(f"{chemin} : entrée non-objet.")
        sigle = entree.get("groupe_sigle")
        legislature = entree.get("legislature")
        sigles_an = entree.get("sigles_an")
        organes_an = entree.get("organes_an")
        if not isinstance(sigle, str) or not sigle:
            raise CorrespondanceSiglesInvalide(f"{chemin} : 'groupe_sigle' absent.")
        if not isinstance(legislature, str) or not legislature:
            raise CorrespondanceSiglesInvalide(f"{sigle} : 'legislature' absente.")
        if not isinstance(sigles_an, list) or not sigles_an or not all(
            isinstance(s, str) and s for s in sigles_an
        ):
            raise CorrespondanceSiglesInvalide(
                f"{sigle}-{legislature} : 'sigles_an' doit être une liste non "
                "vide de sigles AN (organe.libelleAbrev)."
            )
        if not isinstance(organes_an, list) or not organes_an or not all(
            isinstance(o, str) and o.startswith("PO") for o in organes_an
        ):
            raise CorrespondanceSiglesInvalide(
                f"{sigle}-{legislature} : 'organes_an' doit lister les organes "
                "mesurés (PO######) — c'est le fil-piège de la table."
            )
        if not entree.get("verifie_le"):
            raise CorrespondanceSiglesInvalide(
                f"{sigle}-{legislature} : 'verifie_le' absent — une "
                "correspondance non datée n'est pas relisible."
            )
        _valider_position_politique_an(entree, f"{sigle}-{legislature}")
        _valider_historique_organes(entree, f"{sigle}-{legislature}")
        cle = (sigle, legislature)
        if cle in vues:
            raise CorrespondanceSiglesInvalide(
                f"{sigle}-{legislature} : deux entrées pour le même "
                "(groupe_sigle, législature)."
            )
        vues.add(cle)
        valides.append(entree)

    # La succession se valide APRÈS la boucle, et pas dedans : elle est le seul
    # invariant de cette table qui parle d'une AUTRE entrée. La vérifier au fil
    # de l'eau ferait dépendre le verdict de l'ordre des entrées dans le
    # fichier — un prédécesseur écrit plus bas passerait pour introuvable.
    _valider_successions(valides, chemin)
    return valides


def entree_correspondance(
    groupe_sigle: str,
    legislature: str,
    chemin: Optional[Path] = None,
) -> dict[str, Any]:
    """Entrée de la table pour ce `(sigle publié, législature)`.

    Raises:
        CorrespondanceSiglesInvalide: aucune entrée. Le message **nomme** le
            couple : deviner le sigle AN est précisément ce que ce lot refuse.
    """
    for entree in charger_correspondance_sigles(chemin):
        if entree["groupe_sigle"] == groupe_sigle and entree["legislature"] == str(legislature):
            return entree
    raise CorrespondanceSiglesInvalide(
        f"Aucune correspondance de sigle AN pour ({groupe_sigle!r}, "
        f"législature {legislature!r}) dans {chemin or CHEMIN_CONFIG_GROUPES}. "
        "Ajouter l'entrée avec ses organes et son effectif mesurés (#526)."
    )


def url_source_correspondance(chemin: Optional[Path] = None) -> str:
    """`correspondance_sigles_an.source` — l'archive AMO30 dont tout sort.

    Une seule fois dans le fichier, et non recopiée dans les dix entrées : une
    URL répétée dix fois se corrige neuf fois. C'est elle qui devient le
    `source_url` publié de chaque fiche.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_CONFIG_GROUPES
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise CorrespondanceSiglesInvalide(
            f"Configuration des groupes illisible ({chemin}) : {exc}"
        ) from exc
    source = ((document.get(CLE_CORRESPONDANCE_SIGLES) or {}).get("source"))
    if not (isinstance(source, str) and source.strip()):
        raise CorrespondanceSiglesInvalide(
            f"{chemin} : '{CLE_CORRESPONDANCE_SIGLES}.source' absente. C'est "
            "l'URL du référentiel qui porte la qualification : sans elle, la "
            "fiche publierait une posture sans source (AGENTS.md §2 règle 2)."
        )
    return source


def position_politique_publiee(
    groupe_sigle: str,
    legislature: Optional[str],
    chemin: Optional[Path] = None,
) -> dict[str, Any]:
    """Le bloc `position_politique` à publier sur une fiche de groupe (#686).

    Composé de la table committée — jamais mesuré ici : ce module ne lit pas
    l'archive AMO30, et une fiche de groupe se génère dans un job qui n'a
    aucune raison de la télécharger. La mesure vit dans
    `an_roster.positions_politiques_mesurees`, et sert à **écrire** la table et
    à la relire (`--positions`), pas à publier.

    Raises:
        CorrespondanceSiglesInvalide: pas d'entrée pour ce couple, ou table
            invalide. Jamais un repli silencieux : un groupe publié sans
            qualification relue est exactement ce que le §4b du portail de
            qualité refuse.
    """
    if not legislature:
        raise CorrespondanceSiglesInvalide(
            f"{groupe_sigle} : la position politique déclarée se lit PAR "
            "législature (l'AN qualifie ses groupes législature par "
            "législature) ; aucune ne peut être publiée sans elle."
        )
    entree = entree_correspondance(groupe_sigle, legislature, chemin)
    bloc = entree[CLE_POSITION_POLITIQUE]
    return {
        "position": bloc["position"],
        "source_url": url_source_correspondance(chemin),
        "verifie_le": bloc["verifie_le"],
        "organes": [dict(organe) for organe in bloc["organes"]],
    }


def succession_publiee(
    groupe_sigle: str,
    legislature: Optional[str],
    chemin: Optional[Path] = None,
) -> Optional[list[dict[str, Any]]]:
    """Les blocs `succede_a` à publier sur une fiche de groupe (#700), ou `None`.

    **Une liste depuis #815**, parce qu'un groupe peut succéder à plusieurs.
    La forme unique décrivait bien la succession simple (`LR-16` → `DR-17`) et
    ne savait écrire ni une **fusion** — deux groupes qui n'en font qu'un —, ni
    une **scission**, où le sortant continue d'exister et où aucun des deux ne
    succède à l'autre au sens d'un remplacement. #815 croyait en tenir un cas,
    « `AD` quitte `DR` le 11/09/2024 » ; la mesure l'a infirmé le 11/09/2026 —
    0 des 16 membres d'`AD` n'a siégé dans `DR`, les deux groupes naissent le
    même jour —, et le corpus n'en porte aucun à ce jour.

    `None` quand l'entrée ne déclare pas de prédécesseur — les 5 groupes de la
    XVIe, dont la XVe n'est pas couverte par ce dépôt. C'est un périmètre, pas
    un trou : le champ sort `null`, et un champ absent ne prétend rien.

    Composé de la table committée, comme `position_politique_publiee` — et pour
    une raison de plus : ce que la table porte est une **relecture humaine**,
    et rien dans une archive ne pourrait la remplacer. `sigles_an` et
    `organes_an` du prédécesseur sont recopiés verbatim ; ils sont la preuve de
    ce que la lecture rapproche, jamais sa source.

    Le bloc ne porte **pas** de `source_url`, et `validate_profil_groupe` le
    refuse s'il en apparaît une : l'Assemblée ouvre et ferme des organes, elle
    ne les chaîne pas.

    Raises:
        CorrespondanceSiglesInvalide: pas d'entrée pour ce couple, table
            invalide, ou succession qui ne résout pas. Jamais un repli
            silencieux.
    """
    if not legislature:
        raise CorrespondanceSiglesInvalide(
            f"{groupe_sigle} : la succession se lit PAR législature ; aucune ne "
            "peut être publiée sans elle."
        )
    entrees = charger_correspondance_sigles(chemin)
    entree = entree_correspondance(groupe_sigle, legislature, chemin)
    cibles = entree.get(CLE_SUCCESSION)
    if not cibles:
        return None
    # `_valider_successions` a déjà refusé une cible qui ne résout pas : la
    # recherche ci-dessous ne peut donc pas rendre `None`.
    blocs = []
    for cible in cibles:
        predecesseur = next(e for e in entrees if e.get("groupe_id") == cible)
        blocs.append({
            "groupe_id": str(cible),
            "fichier": predecesseur["fichier"],
            "legislature": predecesseur["legislature"],
            "sigles_an": list(predecesseur["sigles_an"]),
            "organes_an": list(predecesseur["organes_an"]),
            "etabli_par": ETABLI_PAR_RELECTURE_HUMAINE,
            "verifie_le": entree["verifie_le"],
        })
    return blocs


def historique_noms_publie(
    groupe_sigle: str,
    legislature: Optional[str],
    chemin: Optional[Path] = None,
) -> Optional[list[dict[str, Any]]]:
    """`historique_noms` à publier sur une fiche de groupe (#815), ou `None`.

    Une entrée par organe du groupe dans sa législature, dans l'ordre
    d'ouverture : `sigle` (le `libelleAbrev` de l'Assemblée), `nom`, `debut`,
    `fin` et `organe_an` — l'identifiant qui rend chaque ligne vérifiable
    (§2 règle 2). Recopié de la table committée, jamais recalculé.

    `None` quand l'entrée ne porte pas la clé : l'historique n'a pas été
    mesuré, ce qui n'est pas « aucun renommage » (§2 règle 5).
    """
    if not legislature:
        return None
    entree = entree_correspondance(groupe_sigle, legislature, chemin)
    historique = entree.get(CLE_HISTORIQUE_ORGANES)
    if not historique:
        return None
    return [
        {
            "sigle": bloc["sigle_an"],
            "nom": bloc["nom"],
            "debut": bloc["debut"],
            "fin": bloc["fin"],
            "organe_an": bloc["organe_an"],
        }
        for bloc in historique
    ]

# ── Les lignées de groupe, déclarées (#836) ──────────────────────────────────
#: Clé portant, dans `raw_data/groupes_reels.json`, la liste des LIGNÉES : la
#: suite des fiches qu'un même groupe a portées au fil des législatures.
#:
#: **L'identifiant est déclaré, jamais dérivé** (#836). Les deux dérivations
#: possibles bougent : par la racine, le jour où un maillon antérieur est
#: ajouté — et c'est prévu, MoDem, Horizons, LIOT et UDR restent à déclarer
#: (#815) ; par le maillon le plus récent, à chaque législature. Un identifiant
#: qu'une collecte déplace casse les liens du site.
#:
#: Ce que la déclaration ne fait PAS : redire la chaîne. L'ordre et
#: l'appartenance se lisent sur `succede_a`, écrit une seule fois, et
#: `_valider_partition_lignees` refuse que les deux se contredisent — c'est
#: #815 qui a payé deux écritures du même fait dans un fichier relu à la main.
CLE_LIGNEES = "lignees"

#: Clé portant, dans une entrée de `groupes[]`, la lignée à laquelle la fiche
#: appartient. **Exigée sur chaque entrée** : une fiche sans lignée ne serait
#: publiée par aucun bouton de l'interface, qui n'en porte qu'un par lignée
#: (décision de la propriétaire, 10/09/2026).
CLE_LIGNEE_ID = "lignee_id"

_CLES_LIGNEE_EXIGEES: tuple[str, ...] = (
    "lignee_id", "lignee_nom", "chambre", "fichier", "verifie_le",
)


class LigneeConfigInvalide(ValueError):
    """La déclaration des lignées est absente ou viole un invariant."""


def charger_lignees(chemin: Optional[Path] = None) -> list[dict[str, Any]]:
    """Charge et valide `lignees[]`, et l'appariement de chaque groupe à la sienne.

    Cinq refus, tous à seuil 0 :

    - une entrée à qui il manque l'une des cinq clés exigées ;
    - deux lignées de même `lignee_id` — l'identifiant est la clé du site ;
    - un groupe sans `lignee_id`, ou dont la lignée n'est pas déclarée ;
    - un groupe dont la `chambre` diffère de celle de sa lignée ;
    - une lignée déclarée qu'aucun groupe ne nomme — une fiche vide serait
      produite, et une lignée sans maillon ne décrit rien (`schema_lignee`).

    Raises:
        LigneeConfigInvalide: le premier invariant rompu, nommé.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_CONFIG_GROUPES
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LigneeConfigInvalide(
            f"Configuration des groupes illisible ({chemin}) : {exc}"
        ) from exc
    except ValueError as exc:
        raise LigneeConfigInvalide(f"{chemin} : JSON invalide — {exc}") from exc

    entrees = document.get(CLE_LIGNEES)
    if not isinstance(entrees, list) or not entrees:
        raise LigneeConfigInvalide(
            f"{chemin} : '{CLE_LIGNEES}' absent ou vide. L'interface ne publie "
            "qu'une fiche par lignée, et cette liste est la seule à dire "
            "lesquelles (#836)."
        )

    par_id: dict[str, dict[str, Any]] = {}
    for entree in entrees:
        if not isinstance(entree, dict):
            raise LigneeConfigInvalide(f"{chemin} : entrée de '{CLE_LIGNEES}' non-objet.")
        manquantes = [cle for cle in _CLES_LIGNEE_EXIGEES if not entree.get(cle)]
        if manquantes:
            raise LigneeConfigInvalide(
                f"{chemin} : lignée {entree.get('lignee_id') or '(sans identifiant)'} — "
                f"clé(s) exigée(s) absente(s) : {manquantes}."
            )
        lignee_id = str(entree["lignee_id"])
        if lignee_id in par_id:
            raise LigneeConfigInvalide(
                f"{chemin} : '{lignee_id}' est déclaré deux fois. L'identifiant "
                "de lignée est la clé d'une page du site."
            )
        par_id[lignee_id] = entree

    nommees: set[str] = set()
    for groupe in document.get("groupes") or []:
        libelle = groupe.get("groupe_id") or "(sans groupe_id)"
        lignee_id = groupe.get(CLE_LIGNEE_ID)
        if not lignee_id:
            raise LigneeConfigInvalide(
                f"{chemin} : {libelle} ne déclare pas de '{CLE_LIGNEE_ID}'. "
                "Une fiche hors lignée n'est publiée par aucun bouton (#836)."
            )
        lignee = par_id.get(str(lignee_id))
        if lignee is None:
            raise LigneeConfigInvalide(
                f"{chemin} : {libelle} nomme la lignée {lignee_id!r}, qui n'est "
                f"déclarée dans aucune entrée de '{CLE_LIGNEES}'."
            )
        if groupe.get("chambre") and groupe["chambre"] != lignee["chambre"]:
            raise LigneeConfigInvalide(
                f"{chemin} : {libelle} est en chambre {groupe['chambre']!r} et sa "
                f"lignée {lignee_id!r} en chambre {lignee['chambre']!r}."
            )
        nommees.add(str(lignee_id))

    orphelines = sorted(set(par_id) - nommees)
    if orphelines:
        raise LigneeConfigInvalide(
            f"{chemin} : {orphelines} ne sont nommées par aucun groupe. Une "
            "lignée sans maillon ne décrit rien (schema_lignee)."
        )
    return list(entrees)


def lignee_publiee(
    groupe_id: str, chemin: Optional[Path] = None
) -> dict[str, Any]:
    """La lignée déclarée d'une fiche de groupe. Lève plutôt que de rendre `None`.

    Raises:
        LigneeConfigInvalide: le groupe n'est pas dans la configuration, ou sa
            lignée n'y est pas déclarée.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_CONFIG_GROUPES
    lignees = {str(l["lignee_id"]): l for l in charger_lignees(chemin)}
    document = json.loads(chemin.read_text(encoding="utf-8"))
    for groupe in document.get("groupes") or []:
        if groupe.get("groupe_id") == groupe_id:
            return lignees[str(groupe[CLE_LIGNEE_ID])]
    raise LigneeConfigInvalide(
        f"{chemin} : aucune entrée 'groupes[]' ne porte le `groupe_id` {groupe_id!r}."
    )
