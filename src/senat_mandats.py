#!/usr/bin/env python3
"""
senat_mandats.py — Composer les appartenances sénatoriales d'une personne (#885).

Ce que ce module rend, et ce qu'il ne rend pas
----------------------------------------------
Les **appartenances** : le mandat parlementaire lui-même, le groupe politique,
les commissions et missions, les groupes d'études, d'amitié et de liaison. Pas
l'activité en séance — le jeu du Sénat ne porte ni scrutins ni comptes rendus,
et la condition 2 du §7 de #528 reste **déclarée non remplie**.

Le nom d'un organe **à la date**, et pourquoi c'est tout l'enjeu
----------------------------------------------------------------
C'est ce qui a fait échouer #878. Le référentiel de l'Assemblée ne porte qu'un
libellé par organe sénatorial — **l'actuel** — et un code interne resté à
l'ancien nom : `PO286005` publie « Les Républicains » depuis le 11/12/2002 avec
`libelleAbrev = UMPPO`. Dix-neuf organes sénatoriaux pour soixante-trois ans.

Le Sénat, lui, publie la table : `libgrppol`, `libcom` et `libgrpsen` bornent
chaque libellé par ses dates. Le nom à la date est donc une **jointure sur
recouvrement de périodes**, pas un choix de notre part.

Mesuré sur les deux candidats déclarés concernés :

| Fiche | Période | Le Sénat dit | L'AN dirait |
| --- | --- | --- | --- |
| `jean-luc-melenchon` | 28/11/2008 → 07/01/2010 | **Groupe CRC-SPG** | Groupe CRCE - Kanaky |
| `bruno-retailleau` | 07/11/2012 → 21/10/2024 | **Groupe UMP**, puis **Les Républicains** | Les Républicains, sur toute la période |

**Un renommage coupe l'appartenance en deux entrées**, chacune bornée à
l'intersection de la période d'appartenance et de celle du libellé — c'est ainsi
que le Sénat modélise le fait, et publier une entrée unique sous le nom le plus
récent perdrait ce que la source sait (§2 règle 2, et #885 §5.3).

Ce que le module refuse de faire
---------------------------------
**Il n'invente aucune date.** Un tiers des appartenances de groupe — **1 064 sur
3 213** — n'a pas de date de début, et les sentinelles `1899-12-31` /
`1900-01-01` en portent une fausse. Les deux ressortent `None` : une borne
absente se publie absente (§2 règle 5). Le recouvrement, lui, traite une borne
absente comme ouverte — mais cette ouverture sert à **comparer**, elle ne sort
jamais dans le résultat.

**Il ne compose rien pour un matricule inconnu** : il rend une liste vide, et
c'est l'appelant qui décide si c'est un fait ou un défaut d'appariement.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from senat_opendata import date_publiable, periodes_se_recouvrent

#: L'URL d'une fiche de sénateur. `sendaiurl` la porte parfois ; sinon on la
#: compose à partir du matricule, comme senat.fr le fait lui-même.
GABARIT_FICHE = "https://www.senat.fr/senateur/{matricule_minuscule}.html"

#: Les quatre familles composées, et la catégorie pivot qu'elles visent. La
#: catégorie définitive est posée par la normalisation, jamais ici : ce module
#: reste **source-near** (§3 : `raw_data/` dit ce que la source a rendu).
FAMILLES = ("mandat_parlementaire", "groupe_politique", "commission",
            "groupe_senatorial", "extra_parlementaire")


def _libelle_fonction(ligne: dict[str, Any], prefixe: str) -> Optional[str]:
    """Le libellé d'une fonction, nettoyé.

    La source remplit certains libellés d'espaces plutôt que de les laisser
    nuls — `fongrppollib` vaut 43 espaces pour `MEMBREPOL`. Une chaîne d'espaces
    n'est pas un libellé : elle ressort `None`, et le repli court (`…lic`) prend
    le relais.
    """
    for suffixe in ("lib", "lic", "lil"):
        valeur = (ligne.get(f"{prefixe}{suffixe}") or "").strip()
        if valeur:
            return valeur
    return None


def _premier_libelle(ligne: dict[str, Any]) -> Optional[str]:
    """Le nom d'un organe, quelle que soit la colonne où la table le range.

    Le jeu du Sénat n'est pas régulier : `libgrppol` remplit `evelib`, `orgext`
    remplit `evelil` et laisse `evelib` vide sur ses 447 lignes. Lire une seule
    colonne publierait `None` sans que rien ne le signale — l'entrée existerait,
    sans nom, et passerait pour une donnée manquante à la source.
    """
    for colonne in ("evelib", "evelil", "evelic"):
        valeur = (ligne.get(colonne) or "").strip()
        if valeur:
            return valeur
    return None


def _libelle_le_plus_complet(ligne: dict[str, Any], colonnes: tuple[str, ...]) -> Optional[str]:
    """Le premier libellé rempli, dans l'ordre de complétude donné.

    L'ordre est celui de l'appelant, et il n'est pas cosmétique : `libcom` porte
    l'abrégé (`evelib`, « Culture ») à côté du complet (`libcomlilmin`,
    « commission de la culture, de l'éducation, de la communication et du
    sport »), et lire l'abrégé publiait trois fois le même mot là où le
    découpage sur renommage avait correctement produit trois périodes (#912).

    La source normalise `libcomlilmin` en minuscules ; seule l'initiale est
    relevée. Le reste n'est pas touché — recapitaliser un intitulé abîmerait les
    sigles et les noms propres qu'il contient.
    """
    for colonne in colonnes:
        # Les espaces multiples sont une scorie de saisie — « Aucune  (Président
        # du Sénat) », « diffusion et  protection » — et non une information.
        valeur = " ".join((ligne.get(colonne) or "").split())
        if valeur:
            return valeur[0].upper() + valeur[1:]
    return None


def _index_libelles(lignes: list[dict[str, Any]], cle: str,
                    debut: str, fin: str, *libelles: str) -> dict[str, list[dict[str, Any]]]:
    """Les libellés d'un organe, groupés par code, avec leurs bornes publiables.

    `libelles` se lit dans l'ordre : la première colonne remplie gagne.
    """
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ligne in lignes:
        code = ligne.get(cle)
        if not code:
            continue
        index[code].append({
            "libelle": _libelle_le_plus_complet(ligne, libelles),
            "debut": date_publiable(ligne.get(debut)),
            "fin": date_publiable(ligne.get(fin)),
        })
    for entrees in index.values():
        entrees.sort(key=lambda e: e["debut"] or "")
    return index


def _index_fonctions(lignes: list[dict[str, Any]], cle_appartenance: str,
                     cle_fonction: str, libelles: dict[str, Optional[str]],
                     debut: str, fin: str) -> dict[str, list[dict[str, Any]]]:
    """Les fonctions tenues, groupées par identifiant d'appartenance."""
    index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ligne in lignes:
        ident = ligne.get(cle_appartenance)
        if not ident:
            continue
        index[ident].append({
            "code": ligne.get(cle_fonction),
            "libelle": libelles.get(ligne.get(cle_fonction) or ""),
            "debut": date_publiable(ligne.get(debut)),
            "fin": date_publiable(ligne.get(fin)),
        })
    return index


def decouper_sur_renommages(
    debut: Optional[str], fin: Optional[str],
    libelles: list[dict[str, Any]],
    libelle_courant: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Une appartenance devient **une entrée par libellé qu'elle traverse**.

    Chaque entrée est bornée à l'**intersection** : elle commence au plus tard
    des deux débuts, finit au plus tôt des deux fins. C'est ainsi que le Sénat
    modélise le fait, et c'est ce qui distingue « Groupe UMP jusqu'en 2015, puis
    Les Républicains » de « Les Républicains depuis 2012 » — la seconde forme
    est fausse, et c'est celle que l'Assemblée publierait.

    **Une borne du libellé ne devient jamais une borne du mandat par défaut.**
    Elle ne s'applique que dans deux cas : quand elle **resserre** une borne
    déjà connue de l'appartenance, ou quand elle marque un **renommage établi**
    — c'est-à-dire quand un autre libellé recouvrant la précède. Premier libellé
    et appartenance sans date : la borne reste `None`.

    La distinction n'est pas théorique. « Groupe socialiste » existe depuis
    1995 ; une appartenance à ce groupe dont le début est inconnu ne commence
    pas en 1995 pour autant, et la publier ainsi ferait lire « membre depuis
    1995 » là où la source ne dit que « ce nom existe depuis 1995 ». Un tiers
    des appartenances de groupe — 1 064 sur 3 213 — sont dans ce cas
    (§2 règle 5).

    **Quand aucun libellé borné ne recouvre**, le nom ne se jette pas pour
    autant. Mesuré sur `bruno-retailleau` : **17 organes** de groupe d'études ou
    d'amitié n'ont aucune ligne dans `libgrpsen`, alors que `grpsenami` porte
    leur libellé — « Groupe d'études Monde combattant et mémoire ». C'est un nom
    **courant**, non daté, et l'entrée le dit : `libelle_date: False`. Publier
    un nom en déclarant qu'il n'est pas daté vaut mieux que publier `null`, et
    mieux que le publier en laissant croire qu'il l'est (§2 règle 2).

    Sans libellé du tout, rend **une** entrée sans nom plutôt que rien :
    l'appartenance est un fait même quand son nom est introuvable, et une entrée
    nommée `None` se voit, là où une entrée absente ne se voit pas.
    """
    recouvrants = [
        lib for lib in libelles
        if periodes_se_recouvrent(debut, fin, lib["debut"], lib["fin"])
    ]
    if not recouvrants:
        if libelle_courant:
            return [{"libelle": libelle_courant, "debut": debut, "fin": fin,
                     "libelle_date": False}]
        return [{"libelle": None, "debut": debut, "fin": fin, "libelle_non_resolu": True}]

    entrees = []
    for rang, lib in enumerate(recouvrants):
        entrees.append({
            "libelle": lib["libelle"],
            # Le début du libellé ne borne l'entrée que s'il RESSERRE une borne
            # connue, ou s'il marque un renommage déjà établi — c'est-à-dire
            # quand un autre libellé recouvrant le précède. Premier libellé et
            # appartenance sans début : la borne reste absente. Prendre celle du
            # libellé ferait lire « membre depuis 1995 » là où la source ne dit
            # que « ce nom existe depuis 1995 » (§2 règle 5).
            "debut": (max(debut, lib["debut"]) if debut and lib["debut"]
                      else debut or (lib["debut"] if rang else None)),
            "fin": (min(fin, lib["fin"]) if fin and lib["fin"]
                    else fin or (lib["fin"] if rang < len(recouvrants) - 1 else None)),
        })
    return entrees


def _fonctions_pendant(fonctions: list[dict[str, Any]],
                       debut: Optional[str], fin: Optional[str]) -> list[dict[str, Any]]:
    """Les fonctions dont la période recouvre celle de l'entrée découpée.

    Une fonction tenue sous l'ancien nom d'un groupe n'a pas à ressortir sous le
    nouveau : le découpage du §`decouper_sur_renommages` s'applique aussi à
    elles.
    """
    return [f for f in fonctions
            if periodes_se_recouvrent(debut, fin, f["debut"], f["fin"])]


def _marqueurs_libelle(entree: dict[str, Any]) -> dict[str, Any]:
    """Ce que l'entrée dit de son propre nom, et rien quand il n'y a rien à dire.

    Un libellé daté est le cas normal : il ne porte aucun marqueur. Les deux
    autres se déclarent — `libelle_date: False` pour un nom courant servi en
    repli, `libelle_non_resolu: True` quand la source n'en porte aucun. Une
    absence déclarée est une donnée ; une absence muette est un trou (§2 règle 5).
    """
    marqueurs: dict[str, Any] = {}
    if entree.get("libelle_non_resolu"):
        marqueurs["libelle_non_resolu"] = True
    if entree.get("libelle_date") is False:
        marqueurs["libelle_date"] = False
    return marqueurs


def composer_mandats(tables: dict[str, list[dict[str, Any]]], senmat: str) -> list[dict[str, Any]]:
    """Toutes les appartenances d'un matricule, découpées sur les renommages.

    Args:
        tables: ce que rend `senat_opendata.lire_tables`.
        senmat: le matricule du sénateur (`sen.senmat`).

    Returns:
        Une liste de dicts **source-near**, triés par date de début. Un
        matricule inconnu rend `[]` — c'est l'appelant qui décide si c'est un
        fait ou un défaut d'appariement.
    """
    mandats: list[dict[str, Any]] = []
    url = GABARIT_FICHE.format(matricule_minuscule=senmat.lower())

    types_app = {t["typapppolcod"]: _libelle_fonction(t, "typapppol")
                 for t in tables.get("typapppol", [])}
    types_grpsen = {t["typgrpsencod"]: (t.get("evelic") or "").strip() or None
                    for t in tables.get("typgrpsen", [])}
    type_par_organe = {g["orgcod"]: g.get("typgrpsencod")
                       for g in tables.get("grpsenami", []) if g.get("orgcod")}
    # Libellés COURANTS, repli quand aucun libellé borné ne recouvre la période.
    # Non datés, et l'entrée produite le déclare.
    courant_grpsen = {g["orgcod"]: (g.get("evelib") or "").strip() or None
                      for g in tables.get("grpsenami", []) if g.get("orgcod")}
    # Même ordre de complétude que `lib_com` : `com` porte `comlilmin` à côté de
    # l'abrégé, et c'est ce nom-là qui sert de repli non daté (#912).
    courant_com = {c["orgcod"]: _libelle_le_plus_complet(c, ("comlilmin", "evelib", "evelil"))
                   for c in tables.get("com", []) if c.get("orgcod")}
    courant_grppol = {g["grppolcod"]: (g.get("grppollibcou") or "").strip() or None
                      for g in tables.get("grppol", []) if g.get("grppolcod")}

    lib_grppol = _index_libelles(tables.get("libgrppol", []), "grppolcod",
                                 "libgrppoldatdeb", "libgrppoldatfin", "evelib")
    # `libcom` porte trois libellés et ils ne disent pas la même chose : `evelib`
    # est l'abrégé (« Culture », coupé à 60 caractères sur les commissions
    # spéciales), `evelil` le complet mais en MAJUSCULES et vide sur 109 des 571
    # lignes, `libcomlilmin` le complet en casse normalisée — rempli sur 568.
    # 420 lignes portent un abrégé différent du complet. Même piège que celui
    # payé sur `orgext` juste en dessous : les colonnes `eve*` ne portent pas la
    # même chose d'une table à l'autre du même jeu (#912).
    lib_com = _index_libelles(tables.get("libcom", []), "orgcod",
                              "libcomdatdeb", "libcomdatfin",
                              "libcomlilmin", "evelib", "evelil")
    lib_grpsen = _index_libelles(tables.get("libgrpsen", []), "orgcod",
                                 "libgrpsendatautbur", "libgrpsendatfin", "libgrpsenlib")

    fon_grppol = _index_fonctions(
        tables.get("fonmemgrppol", []), "memgrppolid", "fongrppolcod",
        {f["fongrppolcod"]: _libelle_fonction(f, "fongrppol") for f in tables.get("fongrppol", [])},
        "fonmemgrppoldatdeb", "fonmemgrppoldatfin")
    fon_com = _index_fonctions(
        tables.get("fonmemcom", []), "memcomid", "foncomcod",
        {f["foncomcod"]: _libelle_fonction(f, "foncom") for f in tables.get("foncom", [])},
        "fonmemcomdatdeb", "fonmemcomdatfin")
    # `liborg` borne les libellés d'organisme comme `libgrppol` borne ceux des
    # groupes ; `orgext` porte le nom courant, en repli.
    lib_extpar = _index_libelles(tables.get("liborg", []), "orgcod",
                                 "liborgdatdeb", "liborgdatfin", "evelib")
    # `orgext` range le nom dans `evelil` — `evelib` y est vide sur les 447
    # lignes. Les colonnes `eve*` ne portent pas la même chose d'une table à
    # l'autre du même jeu, et le supposer publie `None` sans rien signaler.
    courant_extpar = {e["orgcod"]: _premier_libelle(e)
                      for e in tables.get("orgext", []) if e.get("orgcod")}
    designateurs = {d["designcod"]: (d.get("evelib") or d.get("evelic") or "").strip() or None
                    for d in tables.get("designoep", []) if d.get("designcod")}
    fon_extpar = _index_fonctions(
        tables.get("fonmemextpar", []), "memextparid", "fonmemextparcod", {},
        "fonmemextpardatdeb", "fonmemextpardatfin")

    fon_grpsen = _index_fonctions(
        tables.get("fonmemgrpsen", []), "memgrpsenid", "fongrpsencod",
        {f["fongrpsencod"]: _libelle_fonction(f, "fongrpsen") for f in tables.get("fongrpsen", [])},
        "fonmemgrpsendatdeb", "fonmemgrpsendatfin")

    # --- 1. Le mandat parlementaire lui-même. Pas de renommage à traverser :
    # c'est le seul organe dont le nom ne bouge pas. Les motifs de début et de
    # fin sont publiés tels que la source les code — « CESDEPUTEEUR » dit
    # pourquoi un mandat s'arrête, et c'est un fait que rien d'autre ne porte.
    for ligne in tables.get("elusen", []):
        if ligne.get("senmat") != senmat:
            continue
        mandats.append({
            "famille": "mandat_parlementaire",
            "label": "Mandat de sénateur",
            "debut": date_publiable(ligne.get("eludatdeb")),
            "fin": date_publiable(ligne.get("eludatfin")),
            "motif_debut": ligne.get("etadebmancod"),
            "motif_fin": ligne.get("etafinmancod"),
            "departement_code": ligne.get("dptnum"),
            "source_url": url,
        })

    # --- 2. Le groupe politique. C'est ici que le renommage coupe.
    for ligne in tables.get("memgrppol", []):
        if ligne.get("senmat") != senmat:
            continue
        debut = date_publiable(ligne.get("memgrppoldatdeb"))
        fin = date_publiable(ligne.get("memgrppoldatfin"))
        fonctions = fon_grppol.get(ligne.get("memgrppolid") or "", [])
        organe = ligne.get("grppolcod") or ""
        for entree in decouper_sur_renommages(debut, fin, lib_grppol.get(organe, []),
                                              courant_grppol.get(organe)):
            mandats.append({
                "famille": "groupe_politique",
                "label": entree["libelle"],
                "debut": entree["debut"],
                "fin": entree["fin"],
                # N / R / A : membre, rattaché, apparenté. Le type d'appartenance
                # est un fait publié par la source, et il change ce que le
                # mandat veut dire.
                "type_appartenance": types_app.get(ligne.get("typapppolcod") or ""),
                "type_appartenance_code": ligne.get("typapppolcod"),
                "fonctions": _fonctions_pendant(fonctions, entree["debut"], entree["fin"]),
                "organe_code": organe,
                "source_url": url,
                **_marqueurs_libelle(entree),
            })

    # --- 3. Les commissions et missions, même mécanique de renommage : la
    # commission de la culture a gagné « et du sport » le 12/12/2023.
    for ligne in tables.get("memcom", []):
        if ligne.get("senmat") != senmat:
            continue
        debut = date_publiable(ligne.get("memcomdatdeb"))
        fin = date_publiable(ligne.get("memcomdatfin"))
        fonctions = fon_com.get(ligne.get("memcomid") or "", [])
        organe = ligne.get("orgcod") or ""
        for entree in decouper_sur_renommages(debut, fin, lib_com.get(organe, []),
                                              courant_com.get(organe)):
            mandats.append({
                "famille": "commission",
                "label": entree["libelle"],
                "debut": entree["debut"],
                "fin": entree["fin"],
                "titulaire_ou_suppleant": ligne.get("memcomtitsup"),
                "fonctions": _fonctions_pendant(fonctions, entree["debut"], entree["fin"]),
                "organe_code": organe,
                "source_url": url,
                **_marqueurs_libelle(entree),
            })

    # --- 4. Groupes d'études, d'amitié, de liaison. C'est ici que vit le cas le
    # plus fuyant de #878 — « Chrétiens d'Orient », absent des extraits CSV, est
    # un groupe de LIAISON créé le 04/06/2015.
    for ligne in tables.get("memgrpsen", []):
        if ligne.get("senmat") != senmat:
            continue
        debut = date_publiable(ligne.get("memgrpsendatent"))
        fin = date_publiable(ligne.get("memgrpsendatsor"))
        organe = ligne.get("orgcod") or ""
        fonctions = fon_grpsen.get(ligne.get("memgrpsenid") or "", [])
        for entree in decouper_sur_renommages(debut, fin, lib_grpsen.get(organe, []),
                                              courant_grpsen.get(organe)):
            mandats.append({
                "famille": "groupe_senatorial",
                "label": entree["libelle"],
                "debut": entree["debut"],
                "fin": entree["fin"],
                "type_groupe": types_grpsen.get(type_par_organe.get(organe) or ""),
                "type_groupe_code": type_par_organe.get(organe),
                "fonctions": _fonctions_pendant(fonctions, entree["debut"], entree["fin"]),
                "organe_code": organe,
                "source_url": url,
                **_marqueurs_libelle(entree),
            })

    # --- 5. Organismes extra-parlementaires. L'Assemblée en publie aussi, mais
    # **sans date** — 3 entrées pour `bruno-retailleau` contre 13 ici. Le Sénat
    # ajoute la période, le rang (titulaire ou suppléant) et **qui a désigné** :
    # `designcod` vaut par exemple `SENCOMECON`, la commission des affaires
    # économiques. Une désignation sans son désignateur perd ce qui en fait un
    # fait institutionnel.
    #
    # La table porte AUSSI toute la procédure de l'article 13 — avis des deux
    # assemblées, dates d'audition, publication au JO. Rien n'en est repris :
    # c'est une autre matière que l'appartenance, et le corpus n'a rien qui lui
    # ressemble. L'instruire est un lot en soi, pas un sous-produit.
    for ligne in tables.get("memextpar", []):
        if ligne.get("senmat") != senmat:
            continue
        organe = ligne.get("orgcod") or ""
        debut = date_publiable(ligne.get("memextpardatdeb"))
        fin = date_publiable(ligne.get("memextpardatfin"))
        for entree in decouper_sur_renommages(debut, fin, lib_extpar.get(organe, []),
                                              courant_extpar.get(organe)):
            mandats.append({
                "famille": "extra_parlementaire",
                "label": entree["libelle"],
                "debut": entree["debut"],
                "fin": entree["fin"],
                "titulaire_ou_suppleant": ligne.get("memextpartitsup"),
                "designe_par": designateurs.get(ligne.get("designcod") or "")
                               or ligne.get("designcod"),
                "fonctions": _fonctions_pendant(
                    fon_extpar.get(ligne.get("memextparid") or "", []),
                    entree["debut"], entree["fin"]),
                "organe_code": organe,
                "source_url": url,
                **_marqueurs_libelle(entree),
            })

    # Une date absente trie en dernier : elle n'est pas « avant tout », elle est
    # inconnue, et la mettre en tête ferait lire un ordre qui n'existe pas.
    mandats.sort(key=lambda m: (m["debut"] is None, m["debut"] or "", m["famille"]))
    return mandats
