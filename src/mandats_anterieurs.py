#!/usr/bin/env python3
"""
mandats_anterieurs.py — Les mandats nationaux d'un candidat ANTÉRIEURS à la
couverture de l'Assemblée, depuis une table committée et relue (#860).

## Pourquoi une table, et pas une collecte

Les données de l'Assemblée commencent le 19/06/2002 (XIIe législature). Avant,
une carrière existe — 5 des 16 candidats déclarés qui ont un acteur AN en ont
une, mesuré le 11/09/2026 — et le corpus n'en dit rien : le seul critère qu'il
permet, « premier mandat lu », s'est trompé 3 fois sur 5.

Les sources primaires sont hétérogènes — Sycomore pour les députés, décrets au
Journal officiel pour le Gouvernement — et la population est de 11 lignes pour
5 personnes. Trois collecteurs pour cela seraient trois sources hors AGENTS §7
à maintenir ; une table relue, dont chaque ligne porte sa source primaire, suit
le modèle de la correspondance slug ↔ acteur (#525). Arbitrage de la
propriétaire, 11/09/2026.

## Relu, ou pas relu

Un slug présent dans la table a été relu : sa liste, vide ou non, est complète.
Un slug absent ne l'a pas été, et la fiche le dit — `mandats_anterieurs: null`
et `mandats_anterieurs_non_resolu.motif = "non_relu"` —, parce qu'absent n'est
pas « aucun » (AGENTS §2 règle 5).

## Ce qu'une liste vide ne disait pas : sur quoi elle se fonde

Une liste vide affirme quelque chose — « cette personne n'a exercé aucun mandat
national avant le 19/06/2002 » — et §2 règle 2 veut qu'un fait publié renvoie à
sa source primaire. Quand la liste porte des mandats, chaque ligne porte la
sienne ; quand elle est vide, il n'y avait rien à montrer. Une entrée vide
exige donc un `constat` : l'URL consultée, la date, et **la méthode** — qui a
regardé. `lecture_fiche_sycomore` est une lecture de la source primaire par le
pipeline, reproductible ; `relecture_humaine` est une signature, que rien
d'automatique ne pose à la place de quelqu'un.

## Le trou APRÈS la borne (#859)

La table refusait toute ligne se terminant dans la couverture : « un trou après
la borne est un autre défaut ». Ce défaut a été instruit le 05/10/2026 sur la
fiche de Xavier Bertrand, et il a deux causes qui ne se confondent pas :

- **le référentiel ne porte aucun gouvernement avant le 17/05/2007** (659
  mandats `GOUVERNEMENT`, le plus ancien dans Fillon I) : la borne du 19/06/2002
  ne vaut que pour les mandats de député. Une fonction gouvernementale de
  2002-2007 est donc antérieure à ce que la source couvre, comme celles de
  Ségolène Royal le sont à 2002 ;
- **le référentiel ne porte pas son mandat de député de la XIIe** (19/06/2002 →
  30/04/2004), que Sycomore établit : la période est couverte, CE mandat manque.

Arbitrage de la propriétaire, 06/10/2026 : les trois sont cités à la main. Ils
vivent dans le bloc `absents_de_la_source` du même fichier, et sur la fiche dans
`mandats_absents_de_la_source` — un champ À PART de `mandats_anterieurs`, parce
que l'interface publie de celui-ci « exercés avant le 19 juin 2002 », ce qui
serait faux de ces lignes. Chaque ligne nomme son motif.

Le garde-fou de ce bloc est l'inverse de l'autre : une ligne que le corpus
finit par porter n'est plus publiée (`appliquer_mandats_absents_de_la_source`),
sinon la fiche citerait à la main ce qu'elle lit déjà à la source.

## Un champ dérivé, recalculé à l'écriture

Comme `chambres` (#493) ou `meta.licence_donnees` (#530), le champ ne se
fusionne pas : `appliquer_mandats_anterieurs` le repose depuis la table juste
avant l'écriture du pivot, si bien qu'une ligne corrigée dans la table se
corrige sur la fiche au run suivant, et qu'une ligne retirée en disparaît.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from schema_pivot import (
    KNOWN_INSTITUTIONS_ANTERIEURES,
    KNOWN_METHODES_CONSTAT_ANTERIEUR,
    KNOWN_MOTIFS_MANDAT_ABSENT_DE_LA_SOURCE,
    KNOWN_MOTIFS_MANDAT_ANTERIEUR_NON_RESOLU,
)

CHEMIN_TABLE = Path("config") / "mandats_anterieurs.json"

#: Premier jour des données de l'Assemblée : la XIIe législature.
BORNE_COUVERTURE_AN = "2002-06-19"

#: Plus ancien gouvernement que porte le référentiel de l'Assemblée : Fillon I.
#: Mesuré le 05/10/2026 et remesuré le 06/10 sur `acteurs_historique.zip` — 659
#: mandats `GOUVERNEMENT`, le plus ancien du 17/05/2007 ; un seul des 1 162
#: mandats `MINISTERE` est antérieur (24/12/2002), ce qui ne fait pas une
#: couverture. La borne du 19/06/2002 ne vaut PAS pour le Gouvernement (#859).
BORNE_COUVERTURE_GOUVERNEMENT = "2007-05-17"

#: Clé du bloc de la table qui porte les mandats postérieurs au 19/06/2002.
CLE_ABSENTS = "absents_de_la_source"

#: Institution de la table → catégorie du mandat que le corpus porterait.
_CATEGORIE_DU_CORPUS = {
    "assemblee_nationale": "mandat_electif",
    "gouvernement": "fonction_gouvernementale",
}

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TableMandatsAnterieursInvalide(ValueError):
    """La table des mandats antérieurs est illisible ou viole un invariant."""


def _valider_ligne(slug: str, i: int, ligne: Any) -> None:
    libelle = f"{slug}[{i}]"
    if not isinstance(ligne, dict):
        raise TableMandatsAnterieursInvalide(f"{libelle} : ligne non-objet.")
    if ligne.get("institution") not in KNOWN_INSTITUTIONS_ANTERIEURES:
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : institution {ligne.get('institution')!r} hors de "
            f"{sorted(KNOWN_INSTITUTIONS_ANTERIEURES)} — étendre le frozenset, "
            "jamais le contourner (le Sénat attend la reprise de #528)."
        )
    for cle in ("libelle", "debut", "source_url", "verifie_le"):
        if not ligne.get(cle):
            raise TableMandatsAnterieursInvalide(f"{libelle} : '{cle}' absent.")
    if not _DATE.match(ligne["debut"]):
        raise TableMandatsAnterieursInvalide(f"{libelle} : debut {ligne['debut']!r} non ISO.")
    if not str(ligne["source_url"]).startswith("https://"):
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : source_url doit être une URL https — chaque fait porte "
            "sa source primaire (§2 règle 2)."
        )
    fin = ligne.get("fin")
    if fin is None:
        motif = (ligne.get("fin_non_resolue") or {}).get("motif")
        if motif not in KNOWN_MOTIFS_MANDAT_ANTERIEUR_NON_RESOLU:
            raise TableMandatsAnterieursInvalide(
                f"{libelle} : une fin nulle exige 'fin_non_resolue.motif' dans "
                f"{sorted(KNOWN_MOTIFS_MANDAT_ANTERIEUR_NON_RESOLU)} — une absence "
                "sans cause est refusée (§2 règle 5)."
            )
        borne = ligne["debut"]
    else:
        if not _DATE.match(str(fin)) or fin < ligne["debut"]:
            raise TableMandatsAnterieursInvalide(f"{libelle} : fin {fin!r} invalide.")
        if "fin_non_resolue" in ligne:
            raise TableMandatsAnterieursInvalide(
                f"{libelle} : 'fin_non_resolue' sur une fin renseignée."
            )
        borne = fin
    if borne >= BORNE_COUVERTURE_AN:
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : se termine le {borne}, dans la couverture de l'Assemblée "
            f"(depuis le {BORNE_COUVERTURE_AN}). Cette table ne porte que ce que "
            "le corpus ne peut pas porter ; un trou après la borne est un autre "
            "défaut (#859)."
        )


def _valider_constat(slug: str, constat: Any) -> None:
    """Un constat d'absence porte son URL, sa date et sa méthode — les trois."""
    if not isinstance(constat, dict):
        raise TableMandatsAnterieursInvalide(f"{slug} : 'constat' non-objet.")
    url = constat.get("source_url")
    if not url or not str(url).startswith("https://"):
        raise TableMandatsAnterieursInvalide(
            f"{slug} : constat.source_url doit être une URL https — une absence "
            "constatée dit sur quoi elle se fonde (§2 règle 2)."
        )
    date = constat.get("constate_le")
    if not date or not _DATE.match(str(date)):
        raise TableMandatsAnterieursInvalide(
            f"{slug} : constat.constate_le {date!r} absent ou non ISO."
        )
    methode = constat.get("methode")
    if methode not in KNOWN_METHODES_CONSTAT_ANTERIEUR:
        raise TableMandatsAnterieursInvalide(
            f"{slug} : constat.methode {methode!r} hors de "
            f"{sorted(KNOWN_METHODES_CONSTAT_ANTERIEUR)} — étendre le frozenset, "
            "jamais le contourner."
        )


def _lire_entree(slug: str, valeur: Any) -> tuple[list[dict[str, Any]], Optional[dict]]:
    """Rend `(mandats, constat)` pour une entrée de la table.

    Deux formes vivent dans le fichier, et c'est voulu : une LISTE quand des
    mandats ont été trouvés — chaque ligne porte alors sa propre source —, un
    OBJET `{"mandats": [], "constat": {…}}` quand il n'y en a aucun, parce
    qu'une liste vide n'a rien à quoi accrocher sa source.
    """
    if isinstance(valeur, list):
        if not valeur:
            raise TableMandatsAnterieursInvalide(
                f"{slug} : liste vide sans constat. Une absence relue se déclare "
                'en objet — {"mandats": [], "constat": {…}} — sinon rien ne dit '
                "sur quelle source elle repose (§2 règle 2)."
            )
        return valeur, None
    if not isinstance(valeur, dict):
        raise TableMandatsAnterieursInvalide(
            f"{slug} : liste ou objet attendu, {type(valeur).__name__} reçu."
        )
    mandats = valeur.get("mandats")
    if not isinstance(mandats, list):
        raise TableMandatsAnterieursInvalide(f"{slug} : 'mandats' absent ou non-liste.")
    constat = valeur.get("constat")
    if mandats and constat is not None:
        raise TableMandatsAnterieursInvalide(
            f"{slug} : 'constat' sur une liste non vide — la source vit alors sur "
            "chaque ligne, et deux endroits pour un même fait finissent par diverger."
        )
    if not mandats:
        _valider_constat(slug, constat)
    return mandats, constat


def charger_table(
    chemin: Optional[Path] = None,
) -> dict[str, dict[str, Any]]:
    """`slug → {"mandats": [...], "constat": {...} | None}`, table validée.

    Lève plutôt que de rendre une table partielle.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_TABLE
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TableMandatsAnterieursInvalide(f"{chemin} illisible : {exc}") from exc
    except ValueError as exc:
        raise TableMandatsAnterieursInvalide(f"{chemin} : JSON invalide — {exc}") from exc
    candidats = document.get("candidats")
    if not isinstance(candidats, dict):
        raise TableMandatsAnterieursInvalide(f"{chemin} : 'candidats' absent ou non-objet.")
    table: dict[str, dict[str, Any]] = {}
    for slug, valeur in candidats.items():
        lignes, constat = _lire_entree(slug, valeur)
        for i, ligne in enumerate(lignes):
            _valider_ligne(slug, i, ligne)
        debuts = [l["debut"] for l in lignes]
        if debuts != sorted(debuts):
            raise TableMandatsAnterieursInvalide(f"{slug} : lignes non triées par début.")
        table[slug] = {"mandats": lignes, "constat": constat}
    return table


def appliquer_mandats_anterieurs(
    profil: dict[str, Any], table: dict[str, dict[str, Any]]
) -> None:
    """Repose `mandats_anterieurs` sur un pivot de CANDIDAT DÉCLARÉ, depuis la table.

    Sans effet sur un membre de roster : il n'est pas candidat, et ne publie pas
    de fiche. Relu : la liste (éventuellement vide). Non relu : `null` et le
    motif. Jamais fusionné — recalculé à chaque écriture.
    """
    if (profil.get("meta") or {}).get("provenance") != "candidat_declare":
        profil.pop("mandats_anterieurs", None)
        profil.pop("mandats_anterieurs_non_resolu", None)
        profil.pop("mandats_anterieurs_constat", None)
        return
    slug = profil.get("id")
    entree = table.get(slug)
    if entree is None:
        profil["mandats_anterieurs"] = None
        profil["mandats_anterieurs_non_resolu"] = {"motif": "non_relu"}
        profil.pop("mandats_anterieurs_constat", None)
        return
    profil["mandats_anterieurs"] = [dict(ligne) for ligne in entree["mandats"]]
    profil.pop("mandats_anterieurs_non_resolu", None)
    # Le constat ne voyage QUE sur une liste vide : c'est là, et seulement là,
    # que la fiche affirme une absence sans avoir de ligne pour la sourcer.
    if entree.get("constat"):
        profil["mandats_anterieurs_constat"] = dict(entree["constat"])
    else:
        profil.pop("mandats_anterieurs_constat", None)


# ---------------------------------------------------------------------------
# Les mandats POSTÉRIEURS à la borne que la source ne porte pas (#859)
# ---------------------------------------------------------------------------

def _valider_ligne_absente(slug: str, i: int, ligne: Any) -> None:
    libelle = f"{CLE_ABSENTS}.{slug}[{i}]"
    if not isinstance(ligne, dict):
        raise TableMandatsAnterieursInvalide(f"{libelle} : ligne non-objet.")
    if ligne.get("institution") not in KNOWN_INSTITUTIONS_ANTERIEURES:
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : institution {ligne.get('institution')!r} hors de "
            f"{sorted(KNOWN_INSTITUTIONS_ANTERIEURES)}."
        )
    for cle in ("libelle", "debut", "fin", "source_url", "verifie_le"):
        if not ligne.get(cle):
            raise TableMandatsAnterieursInvalide(
                f"{libelle} : '{cle}' absent — un mandat que la source devrait "
                "porter est clos et daté, sinon il n'est pas établi."
            )
    for cle in ("debut", "fin"):
        if not _DATE.match(str(ligne[cle])):
            raise TableMandatsAnterieursInvalide(f"{libelle} : {cle} {ligne[cle]!r} non ISO.")
    if ligne["fin"] < ligne["debut"]:
        raise TableMandatsAnterieursInvalide(f"{libelle} : fin antérieure au début.")
    if not str(ligne["source_url"]).startswith("https://"):
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : source_url doit être une URL https (§2 règle 2)."
        )
    if ligne["fin"] < BORNE_COUVERTURE_AN:
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : se termine le {ligne['fin']}, avant le "
            f"{BORNE_COUVERTURE_AN} — sa place est dans 'candidats', pas ici."
        )
    absence = ligne.get("absence")
    motif = absence.get("motif") if isinstance(absence, dict) else None
    if motif not in KNOWN_MOTIFS_MANDAT_ABSENT_DE_LA_SOURCE:
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : 'absence.motif' {motif!r} hors de "
            f"{sorted(KNOWN_MOTIFS_MANDAT_ABSENT_DE_LA_SOURCE)} — une ligne dit "
            "pourquoi la source ne la porte pas."
        )
    if not _DATE.match(str(absence.get("constate_le") or "")):
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : 'absence.constate_le' absent ou non ISO — l'absence "
            "est une mesure de la source, et une source bouge."
        )
    # Le motif n'est pas une étiquette libre : chacun se vérifie sur la ligne.
    gouvernemental = ligne["institution"] == "gouvernement"
    if motif == "gouvernement_anterieur_a_la_source":
        if not gouvernemental or ligne["fin"] >= BORNE_COUVERTURE_GOUVERNEMENT:
            raise TableMandatsAnterieursInvalide(
                f"{libelle} : 'gouvernement_anterieur_a_la_source' ne vaut que "
                "pour une fonction gouvernementale terminée avant le "
                f"{BORNE_COUVERTURE_GOUVERNEMENT}."
            )
    elif gouvernemental and ligne["fin"] < BORNE_COUVERTURE_GOUVERNEMENT:
        raise TableMandatsAnterieursInvalide(
            f"{libelle} : une fonction gouvernementale terminée avant le "
            f"{BORNE_COUVERTURE_GOUVERNEMENT} manque à la source pour tout le "
            "monde — son motif est 'gouvernement_anterieur_a_la_source'."
        )


def charger_absents(chemin: Optional[Path] = None) -> dict[str, list[dict[str, Any]]]:
    """`slug → lignes` du bloc `absents_de_la_source`, validé. Bloc absent : `{}`.

    Une entrée vide est refusée : elle affirmerait « la source porte tous ses
    mandats », ce qu'aucune relecture n'a établi pour personne.
    """
    chemin = Path(chemin) if chemin is not None else CHEMIN_TABLE
    try:
        document = json.loads(chemin.read_text(encoding="utf-8"))
    except OSError as exc:
        raise TableMandatsAnterieursInvalide(f"{chemin} illisible : {exc}") from exc
    except ValueError as exc:
        raise TableMandatsAnterieursInvalide(f"{chemin} : JSON invalide — {exc}") from exc
    bloc = document.get(CLE_ABSENTS, {})
    if not isinstance(bloc, dict):
        raise TableMandatsAnterieursInvalide(f"{chemin} : '{CLE_ABSENTS}' non-objet.")
    absents: dict[str, list[dict[str, Any]]] = {}
    for slug, lignes in bloc.items():
        if not isinstance(lignes, list) or not lignes:
            raise TableMandatsAnterieursInvalide(
                f"{CLE_ABSENTS}.{slug} : liste non vide attendue."
            )
        for i, ligne in enumerate(lignes):
            _valider_ligne_absente(slug, i, ligne)
        debuts = [l["debut"] for l in lignes]
        if debuts != sorted(debuts):
            raise TableMandatsAnterieursInvalide(
                f"{CLE_ABSENTS}.{slug} : lignes non triées par début."
            )
        absents[slug] = lignes
    return absents


def _porte_par_le_corpus(profil: dict[str, Any], ligne: dict[str, Any]) -> bool:
    """Vrai si la fiche lit déjà, à la source, un mandat qui recouvre la ligne.

    Même catégorie, périodes qui se chevauchent ; pour un mandat de député, la
    chambre est l'Assemblée — un mandat européen de la même période n'en est pas
    un. Un mandat du corpus sans début ne prouve rien et ne compte pas.
    """
    categorie = _CATEGORIE_DU_CORPUS[ligne["institution"]]
    for mandat in profil.get("mandats") or []:
        if not isinstance(mandat, dict) or mandat.get("categorie") != categorie:
            continue
        if categorie == "mandat_electif" and mandat.get("chambre") != "AN":
            continue
        debut = mandat.get("debut")
        if not debut:
            continue
        fin = mandat.get("fin") or "9999-12-31"
        if debut <= ligne["fin"] and fin >= ligne["debut"]:
            return True
    return False


def appliquer_mandats_absents_de_la_source(
    profil: dict[str, Any], absents: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Repose `mandats_absents_de_la_source` sur un pivot de CANDIDAT DÉCLARÉ.

    Dans le bloc : ses lignes, MOINS celles que le corpus porte désormais.
    Hors du bloc : `null` et `non_relu` — personne n'a comparé ses mandats à une
    source officielle, et absent n'est pas « aucun » (§2 règle 5). Jamais
    fusionné : recalculé à chaque écriture, après la fusion des `mandats`.

    Rend les lignes écartées parce que le corpus les porte : l'appelant les
    signale, pour que la table soit nettoyée plutôt que contournée en silence.
    """
    cle = "mandats_absents_de_la_source"
    if (profil.get("meta") or {}).get("provenance") != "candidat_declare":
        profil.pop(cle, None)
        profil.pop(f"{cle}_non_resolu", None)
        return []
    lignes = absents.get(profil.get("id"))
    if lignes is None:
        profil[cle] = None
        profil[f"{cle}_non_resolu"] = {"motif": "non_relu"}
        return []
    gardees = [dict(l) for l in lignes if not _porte_par_le_corpus(profil, l)]
    ecartees = [dict(l) for l in lignes if _porte_par_le_corpus(profil, l)]
    if gardees:
        profil[cle] = gardees
        profil.pop(f"{cle}_non_resolu", None)
    else:
        # Toutes ses lignes sont désormais lues à la source : la relecture a eu
        # lieu, mais elle ne vaut plus constat. Le champ se tait, il n'affirme
        # pas une liste vide.
        profil.pop(cle, None)
        profil.pop(f"{cle}_non_resolu", None)
    return ecartees
