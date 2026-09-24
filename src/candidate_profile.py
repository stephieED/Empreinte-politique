#!/usr/bin/env python3
"""
candidate_profile.py

Construit un profil JSON structuré ("CV politique") d'un parlementaire
à partir des **données ouvertes officielles de l'Assemblée nationale**
(data.assemblee-nationale.fr et questions.assemblee-nationale.fr, Licence
Ouverte / Etalab) : référentiel des acteurs et organes (AMO30), scrutins,
amendements, dossiers législatifs, comptes rendus Syceron, questions écrites
et orales.

**Source unique depuis #529 (lot 5).** NosDéputés.fr/NosSénateurs.fr ne sont
plus interrogés : l'identité, les mandats, les votes, les amendements, les
textes portés et les interventions viennent tous de l'AN. Le retrait n'a rien
d'un basculement de source — chacun de ces chemins avait déjà migré, lot après
lot (#369 l'identité, #392/#403 les votes et amendements, #400 les textes
portés, #526/#527 le roster de groupe, #528 le Sénat), et ce qui restait ici
était la dernière branche encore appelée : la recherche d'interventions.
Motivation, mesures et conséquence déclarée :
docs/decisions/retrait-nosdeputes-529.md.

Le Sénat est HORS PÉRIMÈTRE depuis #528 : `chambre` ne connaît plus que
"deputes", et toute autre valeur est refusée bruyamment (voir `build_profile`).
Décision éditoriale et condition de réouverture :
docs/decisions/retrait-senat-528.md.

Usage (depuis la racine du dépôt) :
    python src/candidate_profile.py jean-luc-melenchon --chambre deputes
    python src/candidate_profile.py jean-luc-melenchon --chambre deputes --out raw_data/profiles/jean-luc-melenchon.json

Le script ne fait AUCUNE interprétation ni jugement de valeur : il se
contente d'agréger les faits bruts (mandats, responsabilités, votes,
interventions) tels que fournis par les API, avec des liens vers les sources.
"""

import argparse
import gzip
import io
import json
import os
import re
import shutil
import sys
import threading
import time
import traceback
import unicodedata
import zipfile
import zlib
from collections import Counter
from pathlib import Path
from typing import Any, NamedTuple, Optional
from xml.etree import ElementTree as ET

import requests
import urllib3
from avertissements import (
    DESTINATAIRE_INTERNE,
    DESTINATAIRE_LECTEUR,
    avertissement,
    deriver_avertissements,
)
from budget_collecte import (
    BudgetCollecte,
    annoncer_troncature,
    epuise as budget_epuise,
    ignorer as budget_ignorer,
    section as budget_section,
)
import correspondance_acteurs_an
from download_watchdog import download_with_watchdog
from gouvernement_textes import (
    _determine_statut,
    DOSSIERS_CACHE_DIR,
    ensure_dossiers_zips_downloaded,
    est_examen_en_commission,
    iter_dossiers_bruts,
    nature_texte_depose,
)
from profil_brut import ecrire_profil_brut
from licences import LICENCE_AN
from parse_syceron import parse_syceron_xml
from schema_pivot import COLLECTE_EXTRAIT, COLLECTE_THEME_SEUL, POSITION_POLITIQUE_AN_VERS_PIVOT, extrait_de_texte
from syceron_debates import (
    SYCERON_AVAILABLE_LEGISLATURES,
    SYCERON_CACHE_DIR,
    iter_syceron_xml_files,
    syceron_zip_url,
)

# Chambres collectees. `BASE_URLS` (la liste des domaines NosDeputes interroges
# par chambre) a ete RETIREE par #529 : plus aucune collecte ne part vers cette
# plateforme, et un dictionnaire d'URLs n'avait plus qu'un role de garde-fou de
# chambre. Ce qu'il gardait est conserve ici, sous un nom qui dit ce que c'est.
#
# La cle "senateurs" avait deja disparu avec #528 : www.nossenateurs.fr a
# definitivement ferme, son archive sert un certificat TLS expire depuis le
# 24/08/2026, et le Senat est sorti du perimetre editorial du produit.
#
# #885 (13/09/2026) : UNE SOURCE DE REMPLACEMENT EST DESORMAIS ETABLIE.
# `data.senat.fr`, producteur Senat, sous Licence Ouverte, porte l'historique
# date des appartenances. La phrase qui tenait ici — « aucune source de
# remplacement (data.senat.fr / www.senat.fr) n'est etablie a ce jour » — a
# cesse d'etre vraie, et une condition de reouverture qu'on laisse affirmer le
# contraire referme le sujet toute seule.
#
# Ce que ca ne change pas : la chambre reste hors de CE tuple tant que la voie
# de collecte n'est pas cablee, parce qu'ouvrir une cle sans collecte derriere
# rendrait un profil vide qui passerait pour un constat (#501, #510) — le
# defaut exact que #528 a ferme. Lire docs/decisions/reouverture-partielle-senat-885.md
# pour ce qui rentre (les appartenances) et ce qui reste dehors (les scrutins).
CHAMBRES_COLLECTEES: tuple[str, ...] = ("deputes",)

HEADERS = {
    "User-Agent": "candidate-profile-script/0.1 (usage personnel / non commercial)"
}

TIMEOUT = 15

# Donnees ouvertes officielles de l'Assemblee nationale (scrutins avec detail
# nominatif des votes par depute). Utilisees en remplacement de l'endpoint
# /votes de NosDeputes.fr, qui renvoie systematiquement une erreur HTTP 500
# (verifie y compris sur l'exemple de leur propre documentation, sur tous les
# domaines/legislatures disponibles).
AN_OPENDATA_BASE = "https://data.assemblee-nationale.fr/static/openData/repository"
AN_SCRUTINS_ZIP_NAME = {
    "17": "Scrutins.json.zip",
    "16": "Scrutins.json.zip",
    "15": "Scrutins_XV.json.zip",
    "14": "Scrutins_XIV.json.zip",
    # Pas de donnees ouvertes de scrutins disponibles pour la 13e legislature
    # (2007-2012) sur data.assemblee-nationale.fr.
}
# Legislatures interrogees pour les votes nominatifs, dans l'ordre decroissant
# (la plus recente d'abord). Remplace depuis #403 le mapping domaine
# NosDeputes.fr -> legislature qui servait ici : il figeait chaque profil sur
# UNE seule legislature, celle du domaine ou l'identite avait ete trouvee, donc
# en pratique toujours la 16e depuis l'etape 4 de #369 (identity_base_url vaut
# None pour tout depute resolu via l'AN, et le domaine principal de
# NosDeputes.fr y etait code en dur comme "16"). Un depute peut sieger sur
# plusieurs legislatures successives : ses votes sont desormais agreges sur
# toutes celles disponibles, comme les amendements (AN_AMENDEMENTS_PATH) et les
# dossiers legislatifs (#400).
AN_SCRUTINS_LEGISLATURES: tuple[str, ...] = ("17", "16", "15", "14")
SCRUTINS_CACHE_DIR = Path(".cache") / "scrutins_an"
# Legislatures dont les scrutins ne bougeront plus (dossier legislatif clos ;
# Last-Modified verifie le 18/08/2026 : 2018-03-21 pour la 14e, 2022-06-09 pour
# la 15e, 2024-06-28 pour la 16e). Leur index est construit une fois pour
# toutes hors CI (build_scrutins_index_figes.py) et committe gzippe dans
# AN_SCRUTINS_FIGES_DIR : la CI n'a donc plus a telecharger que la 17e
# (legislature en cours). Meme remede que pour les amendements
# (AN_AMENDEMENTS_LEGISLATURES_FIGEES), a une nuance pres : les archives de
# scrutins sont petites (0,7 a 26 Mo, toutes "Cacheable" par le CDN AN) et ne
# souffrent pas des IncompleteRead chroniques des archives d'amendements
# (283-618 Mo) — le gel evite ici un cout repete inutilement par chaque shard
# CI, pas un echec de telechargement. Voir
# docs/decisions/votes-multi-legislature.md.
AN_SCRUTINS_LEGISLATURES_FIGEES: frozenset[str] = frozenset({"14", "15", "16"})
AN_SCRUTINS_FIGES_DIR = Path("raw_data") / "scrutins_an_figes"
# Forme dedupliquee du cache de votes (#403, remede repris de #377) : le meta
# de chaque scrutin (titre surtout) est stocke UNE fois dans `scrutins.json`
# (uid -> meta), et l'index par acteur ne porte que des references
# [uid, position]. Mesure sur les 4 legislatures : 68 Mo au total contre 741 Mo
# pour la forme plate ou le meta etait recopie pour chaque votant (x11), et
# 138 Mio de RSS au pic de construction (17e, la plus lourde) contre ~660 Mio.
SCRUTINS_CACHE_SCRUTINS_FILENAME = "scrutins.json"
# Une tranche par acteurRef (#403, remede repris de #392) : `fetch_votes_officiels`
# n'a besoin que de la tranche du candidat courant (~55 Ko) au lieu des 357 Mo
# d'index complets de la 17e legislature, relus a chaque candidat.
SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME = "index_par_acteur"
# Ancien fichier unique (forme plate, avant #403), conserve pour pouvoir le
# supprimer lors de la migration vers les tranches — il pesait a lui seul
# 132 a 357 Mo par legislature.
SCRUTINS_CACHE_INDEX_PAR_ACTEUR_FILENAME_LEGACY = "index_par_acteur.json"
# Fichiers committes pour une legislature figee (memes formats que le cache,
# gzippes : 0,13 / 1,14 / 1,48 Mo pour les legislatures 14 / 15 / 16).
SCRUTINS_FIGES_SCRUTINS_FILENAME = "scrutins.json.gz"
SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME = "index_par_acteur.json.gz"
# Memo process du store `uid -> scrutin` par legislature. Volontairement limite
# au store dedupliqué (2,5 Mo au plus, pour la 17e) : memoiser les index par
# acteur complets rouvrirait l'OOM traite par #377/#392.
_SCRUTINS_STORE_MEMO: dict[str, Optional[dict[str, dict[str, Any]]]] = {}
# Page publique d'un scrutin sur assemblee-nationale.fr, par legislature et
# numero : source primaire de chaque vote (regle 2, tracabilite). Verifiee le
# 18/08/2026 sur les legislatures 14, 15 et 17.
AN_SCRUTIN_PAGE_URL = "https://www.assemblee-nationale.fr/dyn/{legislature}/scrutins/{numero}"
# Prefixe d'uid des scrutins de l'Assemblee nationale proprement dits. Les
# archives de scrutins AN contiennent aussi, marginalement, des scrutins du
# CONGRES (prefixe VTCGR) : une seule occurrence sur les quatre legislatures,
# le vote de constitutionnalisation de l'IVG du 04/03/2024 (VTCGR5L16V1).
# Ils sont ecartes, faute de pouvoir les publier correctement : le Congres est
# une assemblee distincte (Assemblee + Senat reunis a Versailles, d'ou les 24
# senateurs qui apparaissent dans sa ventilation nominative), et sa numerotation
# repart de 1 en partageant l'espace de numeros de l'AN — VTCGR5L16V1 porte le
# numero 1, deja pris par la motion de censure du 11/07/2022. Le publier
# donnerait donc une source primaire fausse (verifie le 18/08/2026 :
# /dyn/16/scrutins/1 renvoie bien la motion de censure) et le confondrait avec
# elle dans la cohesion de groupe, qui indexe par numero a legislature donnee.
# Voir docs/decisions/votes-multi-legislature.md et ROADMAP.
AN_SCRUTIN_UID_PREFIXE = "VTANR"

# codeTypeVote de l'open data AN -> (type_scrutin, type_vote) du schema pivot.
#
# POURQUOI CETTE TABLE (#639). `typeVote` est renseigne sur 18 311 / 18 311
# scrutins des quatre legislatures (releve du 31/08/2026 sur les archives
# reelles), et il etait lu puis jete par `_parse_scrutins_zip`. Les 66 motions
# de censure (14e : 4, 15e : 5, 16e : 34, 17e : 23) etaient donc publiees sous
# le meme `type_vote: "vote_texte"` que les 17 682 autres — la valeur que
# `KNOWN_TYPES_VOTE` attend et qu'aucune donnee ne portait, ce qui rendait
# l'invariant du schema (AGENTS.md §5) vacuement satisfait.
#
# LA TABLE EST FERMEE ET SANS DEFAUT. Un code inconnu rend (None, None) : un
# scrutin non qualifie reste non qualifie, jamais range d'office dans SPO, qui
# est pourtant 97,5 % des scrutins publies — 17 312 / 17 748 (AGENTS.md §2 regle 5).
#
# `type_scrutin` est l'image 1:1 du code source, `type_vote` la seule
# distinction dont les regles editoriales ont besoin : une motion de censure
# est un FAIT PROCEDURAL, jamais une position sur le texte vise (regle 4). Les
# deux coincident sur MOC et divergent sur les trois autres codes ; c'est
# assume, la redondance vaut mieux qu'une repartition inferee.
#
# SSG (« scrutin solennel du Congres ») est volontairement absent : la seule
# occurrence des quatre archives (VTCGR5L16V1, IVG, 04/03/2024) porte un uid
# de Congres et est ecartee en amont par AN_SCRUTIN_UID_PREFIXE. L'inscrire
# ici serait du code mort qui laisserait croire que le Congres est publie.
_SCRUTINS_TYPE_PAR_CODE: dict[str, tuple[str, str]] = {
    "SPO": ("public_ordinaire", "vote_texte"),   # 17 312 publies
    "SPS": ("solennel", "vote_texte"),           #    361 publies
    "SAT": ("tribune", "vote_texte"),            #      9 publies, tous 14e
    "MOC": ("motion_censure", "motion_censure"), #     66 publies
}

# Donnees ouvertes officielles des amendements (Assemblee nationale). Le nom du
# sous-repertoire et du zip differe selon la legislature : "amendements_div_legis"
# / "Amendements.json.zip" pour les legislatures 16/17, "amendements_legis" /
# "Amendements_XV.json.zip" pour la 15e, "amendements_legis_XIV" /
# "Amendements_XIV.json.zip" pour la 14e. Cette similitude de nommage entre
# 14e et 15e (suffixe numero romain) ne reflete PAS le contenu : verifie le
# 15/08/2026 (#301) via lecture partielle en HTTP Range de l'archive 15e
# (en-tetes locaux ZIP a l'offset 0 et vers 5 Mo) que son zip contient, comme
# les 16e/17e, un fichier JSON par amendement de racine `{"amendement": {...}}`
# (`_parse_amendement_entry`) — pas le schema legacy "fichier unique" /
# `{"textesEtAmendements": {...}}` de la 14e (#299, `_parse_amendement_entry_legacy`).
# Verifie manuellement (HTTP 200) pour chaque entree ci-dessous. La 14e a ete
# trouvee le 15/08/2026 via la page d'archives dediee
# (data.assemblee-nationale.fr/archives-anterieures/archives-14e/amendements),
# pas via le repertoire openData standard qui ne la liste pas directement ;
# aucun equivalent trouve pour la 13e (aucune page d'archives ni chemin
# openData ne repond, contrairement a la 14e/15e qui en ont une).
AN_AMENDEMENTS_PATH: dict[str, tuple[str, str]] = {
    "17": ("amendements_div_legis", "Amendements.json.zip"),
    "16": ("amendements_div_legis", "Amendements.json.zip"),
    "15": ("amendements_legis", "Amendements_XV.json.zip"),
    "14": ("amendements_legis_XIV", "Amendements_XIV.json.zip"),
}
AMENDEMENTS_CACHE_DIR = Path(".cache") / "amendements_an"
# Legislatures dont le dossier legislatif est definitivement clos : l'archive
# amendements AN correspondante (Last-Modified verifie le 13/08/2026 :
# 2022-06-09 pour la 15e, 2024-06-28 pour la 16e ; 2018-03-21 pour la 14e,
# verifie le 15/08/2026) ne sera plus jamais modifiee par l'Assemblee
# nationale. Le telechargement en CI de ces archives (350-650 Mo pour la
# 15e/16e) echoue de facon recurrente dans le budget reseau/temps disponible
# (IncompleteRead/HTTP2 PROTOCOL_ERROR repetes, meme en dehors de la CI - voir
# docs/decisions/amendements-legislatures-figees.md) : leur index
# est construit une fois pour toutes hors CI (build_amendements_index_figees.py)
# et committe dans AN_AMENDEMENTS_FIGEES_DIR, lu par _load_frozen_amendement_index
# au lieu d'un nouveau telechargement reseau. La 14e (~99 Mo, marquee
# "Cacheable" par le CDN contrairement a la 15e/16e/17e) est nettement moins
# a risque de reseau mais reste figee au meme titre : son dossier legislatif
# est clos, donc jamais reconstruite. La 17e reste active (legislature en
# cours) et continue d'etre reconstruite par le job CI dedie
# extract-amendements-an.
AN_AMENDEMENTS_LEGISLATURES_FIGEES: frozenset[str] = frozenset({"14", "15", "16"})
AN_AMENDEMENTS_FIGEES_DIR = Path("raw_data") / "amendements_an_figes"
# Nom du fichier d'indicateur de fraîcheur écrit à côté de `index_par_acteur.json`
# (issue #253, sous-issue 5/6 de #248) : permet à un futur consommateur (quality
# gate, sous-issue 6) de distinguer un index frais d'un index conservé faute de
# mieux après un échec définitif de reconstruction — voir
# `_write_amendements_fraicheur`.
AMENDEMENTS_FRAICHEUR_FILENAME = "fraicheur.json"
# Noms des fichiers committés pour une législature figée (compressés gzip :
# mesuré le 15/08/2026 sur la législature 16, `index_par_acteur.json` allégé
# pèse malgré tout 177 Mo en clair — au-delà de la limite GitHub de 100 Mo par
# blob — contre 10,4 Mo une fois gzippé, la structure très répétitive
# {uid, role_signataire} compressant très bien). `amendements.json`
# regroupe les enregistrements dédupliqués (voir `_aggregate_amendements_index`
# et docs/decisions/amendements-legislatures-figees.md) ; le
# contenu JSON est identique, seule la compression change.
AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME = "amendements.json.gz"
AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME = "index_par_acteur.json.gz"
# Noms des fichiers du cache disque (`AMENDEMENTS_CACHE_DIR/<legislature>/`),
# depuis #377 : le cache stocke la MEME forme dedupliquee que le fallback
# committe ci-dessus (simplement non compressee), au lieu de la forme plate
# ou chaque amendement etait recopie integralement pour chacun de ses
# signataires. Mesure sur la legislature 16 : 210 Mo (34 + 176) contre
# 4,67 Go pour la forme plate, soit ~21x — la forme plate approchait a elle
# seule la RAM totale d'un runner GitHub Actions standard (~7 Gio) comme
# d'une machine de developpement modeste, et a declenche l'OOM killer en
# pratique (voir docs/decisions/oom-lecture-amendements-par-candidat.md).
# Un cache ecrit avant #377 ne contient que `index_par_acteur.json` sous
# forme plate, sans `amendements.json` : les deux fichiers sont donc exiges
# ensemble pour qu'un cache soit considere valide (voir
# `_read_cached_amendements_agreges`), ce qui rend l'ancien format
# indiscernable d'un cache absent et force sa reconstruction — jamais sa
# relecture en memoire.
AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME = "amendements.json"
# Depuis #392, l'index par acteur du CACHE RUNTIME est un RÉPERTOIRE d'une
# tranche par acteurRef (`index_par_acteur/PA1567.json`) et non plus un fichier
# unique : `fetch_amendements_officiels` n'a besoin que de la tranche du
# candidat courant, et relire les 673 Mo d'index complets à chaque candidat
# représentait 93 % du coût d'extraction du roster (mesuré en #376).
# Le format COMMITTÉ des législatures figées (AN_AMENDEMENTS_FIGEES_DIR,
# gzippé, fichier unique) est inchangé — il n'est lu qu'une fois, à la
# matérialisation du cache.
AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME = "index_par_acteur"
# Nom du fichier unique hérité de #377, conservé pour pouvoir le supprimer
# lors de la migration vers les tranches.
AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_FILENAME_LEGACY = "index_par_acteur.json"

# Mémo process du store `numero -> amendement` par législature (#392).
# Volontairement limité au store dédupliqué (426 Mo résidents pour les 4
# législatures, mesuré) : mémoïser les index par acteur complets coûterait
# 3,84 Go et rouvrirait l'OOM traité par #377.
_AMENDEMENTS_STORE_MEMO: dict[str, Optional[dict[str, dict[str, Any]]]] = {}
# Le fichier Amendements.json.zip pese 283-618 Mo selon la legislature : un
# alea reseau transitoire sur un telechargement de cette taille (deja observe
# en pratique : IncompleteRead en cours de stream) ne doit pas declencher un
# warning permanent si une tentative suivante aboutit. Borne volontairement
# basse (budget CI) : 3 tentatives, backoff court et fixe (pas d'exponentiel,
# le fichier est deja volumineux a re-telecharger).
AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS = 3
AMENDEMENTS_DOWNLOAD_BACKOFF_SECONDS = 5
# Timeout de lecture (par tentative). Les deux plus grosses archives
# (legislatures 15/16, 363-618 Mo) ne sont pas cacheables par le CDN AN
# (verifie : "x-cacheable: Not cacheable: too big") et frappent donc toujours
# l'origine — un blocage en cours de stream (deja observe : IncompleteRead) y
# est plus probable que sur un petit fichier. 600s etait beaucoup trop large :
# un pire cas de 3 tentatives x 600s (30 min) par legislature, repete pour
# chaque candidat ayant besoin de cette meme legislature (aucun cache
# d'echec avant #239), a suffi a declencher des "runner shutdown signal" en
# CI. Borne desormais a une valeur coherente avec le budget CI du job (cf.
# PARLTRACK_TIMEOUT_MINUTES=30 dans generate-data.yml comme reference) : un
# blocage de plus de 2 min sur un flux CI sain est deja le signe qu'il faut
# abandonner la tentative plutot que d'attendre.
AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS = 120

# Taille de segment pour le telechargement par plages (requetes HTTP Range) des
# archives d'amendements (issue #241). Le CDN devant data.assemblee-nationale.fr
# supporte fonctionnellement les requetes par plage (verifie : reponse 206 +
# Content-Range, le 13/08/2026) ; decouper le flux permet de ne retenter que le
# segment en echec (AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS/BACKOFF_SECONDS
# s'appliquent desormais par segment) au lieu de tout le fichier sur un
# IncompleteRead survenant a un point variable du flux. Valeur choisie comme
# compromis : assez grande pour ne pas multiplier le nombre de requetes sur un
# flux par ailleurs sain (~10-20 segments pour les plus grosses archives,
# 283-618 Mo), assez petite pour qu'un retry de segment reste marginal.
AMENDEMENTS_DOWNLOAD_CHUNK_BYTES = 32 * 1024 * 1024

# 0 = plage SANS BORNE (`bytes=<offset>-`), pour les archives figees. Mesure le
# 24/09/2026 sur Amendements_XV.json.zip depuis un poste : la source coupe
# CHAQUE reponse par une erreur de flux HTTP/2, a n'importe quel decalage, mais
# ce qu'elle delivre avant de couper va de 0 a 211 Mo. Un segment borne a 32 Mo
# plafonne donc les reponses chanceuses, et chaque segment suivant est un
# nouveau tirage qui peut rendre zero. Sur 46 plages ouvertes : 577 Mo cumules,
# 12,6 Mo par tentative ; l'archive entiere est venue en 352 tentatives dont 6
# productives, quand le job de CI en segments bornes plafonnait a 35 Mo en
# 1 300 s.
#
# Ne s'applique QU'AUX ARCHIVES FIGEES. La 17e passe par le meme telechargeur
# dans un job qui n'a pas le meme budget, et son archive n'a jamais pose ce
# probleme : lui changer sa forme de requete sans mesure serait un pari.
AMENDEMENTS_DOWNLOAD_CHUNK_BYTES_FIGEES = 0

# Nombre de segments ayant necessite au moins un retry au-dela duquel un
# warning "doux" est journalise (jamais ajoute a meta.warnings : ceci est un
# signal de qualite de flux, pas un echec de collecte) — permet de distinguer
# en CI un alea reseau ponctuel absorbe d'une degradation plus large.
AMENDEMENTS_SEGMENT_RETRY_WARNING_THRESHOLD = 3

# Etat 3 de #443 : ni les plages Range ni le GET sequentiel ne delivrent le
# moindre octet nouveau. Aucun repli reseau ne fonctionne alors — seule
# l'attente le peut. On attend donc entre deux cycles au lieu de marteler la
# source (relancer immediatement ne fait que consommer du budget CI et de la
# bande passante chez l'AN pour zero octet), puis on abandonne en signalant la
# SOURCE indisponible et non le telechargement en echec. Bornes volontairement
# basses ici, calees sur le budget du job CI extract-amendements-an ; l'outil
# manuel build_amendements_index_figees.py les expose en CLI, car hors CI
# l'attente longue est precisement le seul remede qui marche.
# Granularite de lecture socket des telechargements d'archives. Lue sur
# `resp.raw` et non via `resp.iter_content()` : mesure du 19/08/2026 sur un
# corps tronque a 40 000 octets pour 100 000 annonces, `iter_content` rend 0
# octet des 64 Kio de granularite (le tampon de decodage d'urllib3 est jete
# quand la lecture suivante leve IncompleteRead) la ou `raw.read` rend les
# 40 000. Voir `_telecharger_flux`.
AMENDEMENTS_DOWNLOAD_READ_BUFFER_BYTES = 1024 * 1024

AMENDEMENTS_SOURCE_STALL_MAX_CYCLES = 3
AMENDEMENTS_SOURCE_STALL_WAIT_SECONDS = 30

# #1050 : data.assemblee-nationale.fr sert DEUX versions de la meme URL selon le
# backend qui repond — mesure du 21/09/2026, 10 requetes HEAD sur l'archive de
# la 17e legislature, 8 fois l'ETag "11e77868-65bee362fa5cb" (300 382 312
# octets) et 2 fois "11e807a3-65befe27af972" (300 418 979). Recoller neuf
# segments Range preleves au hasard sur l'une ou l'autre produit un fichier de
# la taille annoncee, mais illisible. Un redemarrage depuis zero est donc
# parfois inevitable ; borne ici, car au-dela c'est la source qui est
# incoherente, pas le transfert qui a eu la malchance.
AMENDEMENTS_DOWNLOAD_MAX_REDEMARRAGES_VERSION = 3

# Legislatures dont le telechargement de l'archive amendements a echoue de
# facon definitive (toutes les tentatives de _download_and_build_amendement_index
# epuisees) pour le run (process) courant. Verifie en tete de cette fonction
# avant toute tentative reseau : sans ce cache, chaque candidat suivant ayant
# besoin de la meme legislature repayait l'integralite du cycle de retry
# (issue #239). Raccourci intra-process uniquement : deux jobs CI du meme run
# (ex. extract-an puis extract-roster-groupes, sequences par #222) sont deux
# process Python distincts, donc deux instances vides de ce set — voir
# _amendements_failed_marker_path ci-dessous pour la source de verite
# inter-jobs (issue #246).
_amendements_failed_legislatures: set[str] = set()


def _amendements_failed_marker_path(legislature: str) -> Path:
    """Chemin du marqueur disque d'echec definitif pour une legislature, sur le
    cache disque partage `.cache/amendements_an/` (restaure/sauvegarde par
    chaque job CI grace au sequencement de #222 sur la meme cle de cache,
    voir [[concurrence-ci-roster]]). Contrairement a l'index lui-meme, ce
    marqueur ne contient aucune donnee : juste le `GITHUB_RUN_ID` du run
    l'ayant ecrit, pour distinguer un echec du run courant (a respecter) d'un
    residu d'une semaine ISO precedente via `restore-keys` (a ignorer, issue
    #246)."""
    return AMENDEMENTS_CACHE_DIR / legislature / "failed_run_id"


def _mark_amendements_legislature_failed(legislature: str) -> None:
    """Memorise l'echec definitif d'une legislature : en memoire process
    (raccourci intra-process, #239) et sur le marqueur disque partage entre
    jobs CI du meme run (#246). `GITHUB_RUN_ID` est absent hors CI (ex. tests,
    usage local) : dans ce cas, seul le cache memoire est utilise, comme avant
    #246."""
    _amendements_failed_legislatures.add(legislature)
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not run_id:
        return
    marker_path = _amendements_failed_marker_path(legislature)
    try:
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        marker_path.write_text(run_id, encoding="utf-8")
    except OSError:
        pass  # marqueur best-effort : une legislature non marquee est simplement retentee


def _amendements_legislature_failed_this_run(legislature: str) -> bool:
    """Determine si une legislature a deja echoue definitivement durant le run
    courant, en consultant d'abord le cache memoire intra-process (#239) puis,
    a defaut, le marqueur disque inter-jobs (#246). Un marqueur disque
    referencant un `GITHUB_RUN_ID` different du run courant est ignore (residu
    perime) : comportement de #239 volontairement preserve pour les runs
    suivants, sans TTL explicite a maintenir."""
    if legislature in _amendements_failed_legislatures:
        return True
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not run_id:
        return False
    try:
        marker_run_id = _amendements_failed_marker_path(legislature).read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if marker_run_id != run_id:
        return False
    _amendements_failed_legislatures.add(legislature)  # raccourci pour les prochains appels intra-process
    return True

# Dossiers legislatifs (Assemblee nationale) : plusieurs archives bulk, une par
# legislature (15/16/17 — voir AN_DOSSIERS_ARCHIVES), chacune deja
# multi-legislatures mais ne gardant des precedentes qu'une traine residuelle,
# d'ou l'ingestion des trois (#400). Utilise ici pour resoudre le code source
# d'un texte (texteLegislatifRef d'un amendement, ex. "PIONANR5L17B0904") vers
# son titre lisible, et pour construire l'index acteur -> textes portes.
# DOSSIERS_CACHE_DIR/ensure_dossiers_zips_downloaded/iter_dossiers_bruts sont
# importés depuis gouvernement_textes.py, qui en est la source canonique
# (téléchargement/cache partagé avec la collecte des dossiers gouvernementaux,
# voir issue #210 : un seul cache pour ces archives).
# iter_dossiers_bruts deduplique par uid entre archives : sans cela un dossier
# present dans deux archives serait compte deux fois.

# Acteurs/mandats/organes historique complet (Assemblee nationale) : un seul
# fichier bulk, couvrant TOUTES les legislatures depuis la XIe (3117 acteurs
# constates, contre 577 deputes ACTIFS de la seule legislature en cours pour
# l'ancien jeu de donnees AMO10 "deputes_actifs_mandats_actifs_organes", plus
# utilise depuis l'issue #354 - voir docs/technical_decisions.md pour le choix
# AMO30 plutot que combiner AMO20 par legislature comme envisage initialement).
# Utilise pour :
# - enrichir schema_pivot.identite (nom complet/profession/date+lieu de
#   naissance/uri_hatvp/contact/circonscription/place hemicycle) au-dela de ce
#   que fournit nosdeputes.fr, y compris pour les elus dont le mandat est
#   termine (_build_acteur_identite_index, issue #354) ;
# - reconstituer l'historique date d'appartenance a un groupe politique
#   (acteur.mandats.mandat[].typeOrgane == "GP") et sa qualification officielle
#   organe.positionPolitique ("Majoritaire"/"Minoritaire"/"Opposition"/null).
#   Constat empirique : positionPolitique n'est renseigne par l'AN qu'une fois
#   la legislature terminee (toujours null sur la 17e, en cours, y compris
#   pour les groupes du socle commun) - cette qualification ne couvre donc que
#   les legislatures achevees (jusqu'a la 16e comprise) ;
# - resoudre mandats[].organes.organeRef vers un nom lisible (_build_organe_index,
#   issue #353), a partir des 7126+ organes historiques du meme zip
#   (json/organe/*.json, tous codeType confondus : commissions, groupes
#   d'amitie, engagements extra-parlementaires...).
AN_ACTEURS_HISTORIQUE_ZIP_URL = (
    f"{AN_OPENDATA_BASE}/17/amo/tous_acteurs_mandats_organes_xi_legislature/"
    "AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip"
)
ACTEURS_HISTORIQUE_CACHE_DIR = Path(".cache") / "acteurs_historique_an"

# Noms des index dérivés du zip AMO30, **versionnés** (#556). Le suffixe n'est
# pas cosmétique : ces index sont mis en cache sur disque ET restaurés d'un run
# à l'autre par le cache GitHub Actions (#550/#555). Un correctif portant sur ce
# qui est *écrit* dans l'index — ici le filtrage du marqueur `xsi:nil` par
# `_champ_identite_an` — reste donc sans effet tant que l'ancien fichier est
# relu : le code corrigé ne s'exécute jamais. Changer le nom force la
# reconstruction, une fois, et laisse une trace lisible de la raison.
#
# Règle : **on incrémente le suffixe dès que le CONTENU écrit change**, jamais
# pour un changement de lecture. `v3` porte deux changements de contenu livrés
# ensemble : `mandats_assemblee` (#640) et la profession lue par `_profession_an`
# (#641). `v4` en porte deux autres : `famille_socioprofessionnelle` et
# `categorie_socioprofessionnelle`, les deux niveaux de la nomenclature PCS de
# l'INSEE qu'AMO30 publie et que le pipeline traversait sans rien en garder
# (#659). `civilite` était déjà écrite dans l'index — c'est en AVAL qu'elle se
# perdait — mais elle voyage avec eux jusqu'au profil brut.
NOM_INDEX_IDENTITE = "index_identite_v4.json"
NOM_INDEX_ORGANES = "index_organes_v2.json"

# Questions parlementaires (écrites, au gouvernement, orales sans débat).
# Même pattern d'URL que scrutins/amendements. Un seul parseur générique suffit
# pour les 3 types (seul @xsi:type diffère). URLs confirmées pour les 16e et 17e
# législatures ; les noms pour 14/15 suivent la convention _XIV/_XV des autres jeux
# (inférés — échoueront silencieusement si le fichier n'existe pas côté AN).
AN_QUESTIONS_PATH: dict[str, dict[str, tuple[str, str]]] = {
    "17": {
        "QE":   ("questions_ecrites",           "Questions_ecrites.json.zip"),
        "QG":   ("questions_gouvernement",      "Questions_gouvernement.json.zip"),
        "QOSD": ("questions_orales_sans_debat", "Questions_orales_sans_debat.json.zip"),
    },
    "16": {
        "QE":   ("questions_ecrites",           "Questions_ecrites.json.zip"),
        "QG":   ("questions_gouvernement",      "Questions_gouvernement.json.zip"),
        "QOSD": ("questions_orales_sans_debat", "Questions_orales_sans_debat.json.zip"),
    },
    "15": {
        "QE":   ("questions_ecrites",           "Questions_ecrites_XV.json.zip"),
        "QG":   ("questions_gouvernement",      "Questions_gouvernement_XV.json.zip"),
        "QOSD": ("questions_orales_sans_debat", "Questions_orales_sans_debat_XV.json.zip"),
    },
    "14": {
        "QE":   ("questions_ecrites",           "Questions_ecrites_XIV.json.zip"),
        "QG":   ("questions_gouvernement",      "Questions_gouvernement_XIV.json.zip"),
        "QOSD": ("questions_orales_sans_debat", "Questions_orales_sans_debat_XIV.json.zip"),
    },
}
QUESTIONS_CACHE_DIR = Path(".cache") / "questions_an"

# #1094 — la marque de format de `index_par_acteur.json`. Un cache porte le code
# qui l'a écrit, et les législatures closes ne sont jamais périmées (#555) :
# sans elle, l'index de la XVe écrit avant la lecture de `ANALYSE.ANA` serait
# servi indéfiniment, sujets à `null` compris. Le NOM du fichier ne change pas,
# parce que `generate-data.yml` le cite et se publie à la main. À changer dès
# que ce que l'index CONTIENT change.
CLE_FORMAT_INDEX_QUESTIONS = "_format"
FORMAT_INDEX_QUESTIONS = "sujet-xve-1094"

# Verrous par législature pour `_build_acteur_vote_index` : plusieurs threads peuvent
# appeler cette fonction simultanément pour des législatures différentes (pas de blocage
# entre eux), mais on sérialise les accès pour une même législature afin d'éviter un
# double téléchargement de l'archive zip et une écriture concurrente du cache disque.
_SCRUTINS_LOCKS: dict[str, threading.Lock] = {}
_SCRUTINS_LOCKS_META = threading.Lock()

# Même principe que _SCRUTINS_LOCKS, pour l'index des amendements officiels.
_AMENDEMENTS_LOCKS: dict[str, threading.Lock] = {}
_AMENDEMENTS_LOCKS_META = threading.Lock()

# Même principe que _SCRUTINS_LOCKS, pour l'index des questions officielles.
_QUESTIONS_LOCKS: dict[str, threading.Lock] = {}
_QUESTIONS_LOCKS_META = threading.Lock()

# Même principe que _SCRUTINS_LOCKS, pour l'index des débats Syceron — mais
# RÉENTRANT (#510) : la lecture d'une tranche d'acteur prend le verrou, et
# retombe sur la construction de l'index quand la tranche manque, qui le reprend.
# Un `Lock` simple s'auto-bloquerait sur ce chemin.
_SYCERON_LOCKS: dict[str, threading.RLock] = {}
_SYCERON_LOCKS_META = threading.Lock()

# #510 : mémo PROCESS des index construits mais NON publiés (archive illisible,
# ou aucun acteur résolu sur une archive lisible). Rien n'est écrit sur disque
# dans ces cas-là — c'est délibéré, un `{}` figé sous la clé de cache de la
# semaine rendrait le défaut invisible à tous les shards suivants (§2.5). Sans
# ce mémo, chaque candidat reparcourrait les 601 à 1 562 comptes rendus.
#
# Clé = le CHEMIN du répertoire de cache, jamais la seule législature : les
# tests déplacent le cache d'un cas à l'autre, et un mémo logique ferait fuir
# l'index d'un cas dans le suivant — le piège qui a fait revert #377,
# explicitement nommé dans AGENTS.md.
_SYCERON_INDEX_NON_PUBLIE: dict[str, dict[str, list[dict[str, Any]]]] = {}

# Un seul verrou pour l'index identite des acteurs (un seul fichier, pas de
# decoupage par legislature), construit depuis le meme fichier bulk historique
# que _ACTEURS_HEMICYCLE_LOCK/_ACTEURS_ORGANES_LOCK (issue #354).
_ACTEURS_IDENTITE_LOCK = threading.Lock()

# Un seul verrou pour l'index des positions dans l'hemicycle (construit depuis
# le fichier bulk historique des acteurs/mandats/organes).
_ACTEURS_HEMICYCLE_LOCK = threading.Lock()

# Verrou dedie au telechargement/cache disque de l'archive bulk historique
# elle-meme (AN_ACTEURS_HISTORIQUE_ZIP_URL) : plusieurs index se construisent
# a partir du meme zip (_build_acteur_identite_index, _build_acteur_positions_hemicycle_index,
# _build_organe_index) sans se marcher dessus ni le retelecharger chacun de
# leur cote (voir _ensure_acteurs_historique_zip_downloaded).
_ACTEURS_HISTORIQUE_ZIP_LOCK = threading.Lock()

# Un seul verrou pour l'index des organes (organeRef -> sigle/nom/type),
# construit depuis le meme fichier bulk historique (issue #353).
_ACTEURS_ORGANES_LOCK = threading.Lock()

# Un seul verrou pour l'index des mandats (commissions/groupes d'amitie/
# engagements extra-parlementaires), construit depuis le meme fichier bulk
# historique (issue #369 - complete #353 pour peupler profile["mandats"]).
_ACTEURS_MANDATS_LOCK = threading.Lock()

# Un seul verrou pour l'index des textes portés (auteur/rapporteur), construit
# depuis le même fichier bulk que l'index titre (dossiers legislatifs).
_DOSSIERS_TEXTES_PORTES_LOCK = threading.Lock()

# ── Memo intra-process des index derives du zip historique AMO30 (#467) ──────
# Les quatre builders ci-dessous (identite, mandats, organes, positions dans
# l'hemicycle) relisaient leur fichier `.cache/acteurs_historique_an/index_*.json`
# a CHAQUE appel. Le cache disque evitait le retelechargement, jamais le
# reparsing : mesure sur les 24 membres du shard 0 du run 32288588518,
# `fetch_organe` etait appele 2 255 fois et relisait index_organes.json autant
# de fois — 43,4 s sur 74,1 s de temps mur. Meme pathologie que celle corrigee
# pour les amendements en #392 (93 % du cout par membre) et pour les scrutins
# en #403, au meme endroit : un index partage relu par candidat.
#
# Memo indexe par CHEMIN de l'index, pas par nom logique : les tests patchent
# `ACTEURS_HISTORIQUE_CACHE_DIR` vers un `tmp_path` different a chaque cas, et
# un memo global les ferait lire l'index du test precedent — c'est exactement
# le piege qui avait fait reverter la memoisation de #377 (voir la fixture
# `_purge_memo_store_amendements`). Une fixture autouse purge quand meme le
# memo, ceinture et bretelles.
#
# L'objet rendu est PARTAGE, jamais copie (meme regle que l'index amendements,
# AGENTS.md §5) : aucun appelant ne le mute, tous font `.get(...)` en lecture.
_ACTEURS_HISTORIQUE_INDEX_MEMO: dict[str, Any] = {}
_ACTEURS_HISTORIQUE_MEMO_LOCK = threading.Lock()


def _index_historique_memoise(index_path: Path) -> Optional[Any]:
    """Index deja materialise en memoire pour ce chemin, ou None."""
    with _ACTEURS_HISTORIQUE_MEMO_LOCK:
        return _ACTEURS_HISTORIQUE_INDEX_MEMO.get(str(index_path))


def _memoiser_index_historique(index_path: Path, index: Any) -> Any:
    """Memorise `index` pour ce chemin et le renvoie tel quel (jamais copie)."""
    with _ACTEURS_HISTORIQUE_MEMO_LOCK:
        _ACTEURS_HISTORIQUE_INDEX_MEMO[str(index_path)] = index
    return index


def _clear_acteurs_historique_index_memo() -> None:
    """Purge le memo — usage test uniquement (cf. fixture autouse)."""
    with _ACTEURS_HISTORIQUE_MEMO_LOCK:
        _ACTEURS_HISTORIQUE_INDEX_MEMO.clear()


def nb_acteurs_referentiel_charge() -> Optional[int]:
    """Nombre d'acteurs AMO30 **déjà** chargés, sans jamais rien télécharger (#539).

    C'est la mesure de la condition C1 : « jamais élu·e à l'Assemblée
    nationale » n'est dérivable que d'un référentiel *prouvé chargé*. La
    fonction rend `None` quand personne ne l'a chargé — et `None` n'est pas
    zéro : `couverture_profil` en tire « non collecté — panne », pas « jamais
    élu ». C'est exactement l'inversion qui a produit #484, où un échec réseau
    a été lu comme une donnée.

    Ne déclenche AUCUN téléchargement, volontairement : appelée depuis un
    chemin `--pivot-only` ou depuis un script de migration, elle doit constater
    l'état du cache, pas le fabriquer. Un référentiel non chargé est un fait sur
    le run, et le run a le droit de le dire.
    """
    index_path = ACTEURS_HISTORIQUE_CACHE_DIR / NOM_INDEX_IDENTITE
    memoise = _index_historique_memoise(index_path)
    if isinstance(memoise, dict):
        return len(memoise)
    if index_path.is_file():
        try:
            with open(index_path, encoding="utf-8") as f:
                index = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
        if isinstance(index, dict):
            return len(index)
    return None


# Nomenclature officielle des types de rapport (typeRapporteur, dossiers
# legislatifs Assemblee nationale) -> nomenclature du schema pivot.
TYPE_RAPPORTEUR_MAP = {
    "rapporteur": "rapporteur_fond",
    "rapporteur pour avis": "rapporteur_avis",
    "rapporteur spécial": "rapporteur_special_budget",
    "rapporteur général": "rapporteur_general",
}

# Préfixes des messages d'avertissement (warnings) ajoutés à profile["meta"]["warnings"].
# Exposés en constantes (plutôt qu'en texte libre dupliqué) pour que merge_profile.py
# puisse détecter de façon fiable les warnings devenus obsolètes après fusion
# (cf. _prune_stale_warnings), sans risquer de désynchronisation si le libellé
# complet du message venait à changer ici.
WARNING_PREFIX_IDENTITE_INTROUVABLE = "identité introuvable"
WARNING_PREFIX_MANDATS_INTROUVABLES = "mandats introuvables"
WARNING_PREFIX_VOTES_INTROUVABLES = "votes introuvables"
WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES = "amendements indisponibles"
# #562 : « la source n'a pas répondu » et « notre code a échoué » sont deux
# faits différents, et un seul des deux parle de l'Assemblée nationale. Le
# préfixe ci-dessus dit le premier ; celui-ci dit le second, et il est
# volontairement DISTINCT pour que `couverture_profil` ne puisse pas le mapper
# vers `panne` — publier « panne » sur un défaut de collecte accuse la source
# d'une faute qui est la nôtre. Mesure qui a motivé la séparation : 99 profils
# publiés sur 481 portaient `amendements: []` avec, pour preuve, le texte d'un
# `TypeError` du dépôt (voir `_texte_an`).
WARNING_PREFIX_DEFAUT_COLLECTE = "défaut de collecte interne"
WARNING_PREFIX_QUESTIONS_INDISPONIBLES = "questions indisponibles"
# #510 : le libellé portait « (fallback nosdeputes) » tant qu'un repli existait.
# Le repli a été RETIRÉ le 27/08/2026 : Syceron est désormais la seule source du
# chemin interventions (avec les questions officielles, qui ne l'ont jamais
# doublé mais complété). Le préfixe conservé est un PRÉFIXE de l'ancien, ce qui
# laisse `_prune_stale_warnings` reconnaître les warnings déjà écrits dans le
# corpus publié.
WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES = "interventions syceron indisponibles"
# #560 : le préfixe ci-dessus recouvrait DEUX états du modèle de #539, et le
# code choisissait le pire des deux. Il était écrit par les deux branches de
# l'étape 9 :
#
#   - l'archive n'a pas répondu (exception, `_tracer_echec_collecte`) — une
#     **panne**, un incident dont un prochain run peut sortir ;
#   - l'archive a répondu et ne contient rien pour cet acteurRef — un **constat**
#     de zéro, publiable tel quel (AGENTS.md §2.5).
#
# La preuve publiée l'avouait elle-même : « identifiant absent des trois
# archives, **ou** archive indisponible ». C'est la leçon déjà tirée pour
# `WARNING_PREFIX_VOTES_INTROUVABLES` pendant #539, dont la table de causes a dû
# être indexée par motif parce qu'un préfixe couvrait une panne *et* un constat.
# Ici on ne contourne pas le préfixe : on le scinde, pour qu'aucune table n'ait
# à rattraper une ambiguïté qu'on aurait pu ne pas écrire.
WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE = "aucune intervention syceron"
# #498 : collecte d'interventions interrompue par son budget de temps mur. JAMAIS
# retiré par _prune_stale_warnings : contrairement à « votes introuvables », que
# la fusion peut démentir en restaurant les votes de l'ancien fichier, celui-ci
# décrit ce que CE run n'a pas collecté. Une liste tronquée qui a l'air complète
# après fusion reste une liste dont on ne sait pas si elle est complète.
WARNING_PREFIX_BUDGET_INTERVENTIONS = "collecte d'interventions tronquée (budget de temps)"
# #514 : collecte du candidat (identité, votes, dossiers, interventions)
# interrompue par le budget de temps mur du candidat. Même raison qu'au-dessus
# de n'être jamais retiré par _prune_stale_warnings.
WARNING_PREFIX_BUDGET_COLLECTE = "collecte tronquée (budget de temps)"
# #484 : phrase du profil MINIMAL, écrit par
# `generate_all_profiles.build_minimal_profile` pour un candidat sans mandat
# français connu — sans aucune source parlementaire, depuis
# `raw_data/candidats.json` seul. Elle vit ici, avec les autres, parce que
# `candidate_profile` est le module que l'émetteur ET `merge_profile` importent
# déjà (l'inverse serait un import circulaire).
#
# Contrairement aux préfixes de budget juste au-dessus, celui-ci EST retiré par
# `_prune_stale_warnings` : il ne décrit pas ce que le run n'a pas collecté, il
# affirme un FAIT sur la carrière — « aucun mandat français connu ». Un profil
# qui, après fusion, porte des mandats ou une identité collectée le dément.
# `jean-luc-melenchon` publie 86 mandats sous cette phrase depuis le run
# 33262372122 (29/08/2026).
WARNING_AUCUN_MANDAT_FR = "aucun mandat français connu"
# `WARNING_PREFIX_SOURCE_INJOIGNABLE` (#514) a été RETIRÉ par #529. Il
# distinguait « la source a répondu qu'il n'y a rien » de « la source n'a rien
# dit », sur les seules requêtes qui passaient par `_get_payload` —
# c'est-à-dire NosDéputés/NosSénateurs, et rien d'autre. Ce chemin réseau
# n'existe plus : l'identité se résout dans une archive AMO30 déjà en cache, et
# une archive absente ou illisible lève une exception, qui est nommée dans
# `meta.warnings`. Un warning qui ne peut plus se déclencher est un garde-fou
# désarmé qu'on croit armé.

# `--max-pages` a été retiré du code (#510) ET de generate-data.yml : il
# plafonnait la recherche d'interventions NosDéputés, qui n'existe plus.
# Le garde-fou « accepter mais signaler » écrit par #529 est devenu sans
# objet — plus aucun appelant ne passe le drapeau.

# #510 : l'archive Syceron publie l'identifiant d'orateur NU (`<orateur><id>847629
# </id>`), et le code lui appliquait `re.fullmatch(r"PA\d+")` — donc l'index de la
# source PRIMAIRE des interventions était vide depuis toujours.
#
# La résolution est ACTIVE depuis le 27/08/2026, sans drapeau : c'est le
# comportement de collecte, et le repli NosDéputés qui comblait le silence a été
# retiré du chemin interventions dans le même mouvement (décision d'opérateur
# prise sur les mesures ci-dessous, cf. docs/decisions/syceron-actif-510.md).
#
# Les deux défauts de parseur qui bloquaient l'activation sont corrigés depuis le
# 26/08/2026 (parcours récursif des `<point>`, sujet lu là où la source le publie)
# et les trois archives ont été téléchargées, ce que #510 n'avait pas pu faire —
# la forme de l'identifiant est donc vérifiée sur TOUTES les législatures
# collectées, pas seulement la 17e. Mesuré sur les trois archives complètes
# (`content-length` vérifié : 148 954 869 / 57 553 703 / 55 772 428 octets) :
#
#   | Législature | Comptes rendus | Interventions indexables | Acteurs | `sujet` |
#   | --- | ---: | ---: | ---: | ---: |
#   | 15 | 1 562 | 633 764 | 687 | 84,8 % |
#   | 16 |   605 | 305 862 | 656 | 93,9 % |
#   | 17 |   601 | 287 789 | 675 | 88,9 % |
#   | **total** | **2 768** | **1 227 415** | — | **88,0 %** |
#
# `forme_inattendue` — le compteur-témoin — est à **0 sur les trois**, et
# `id_acteur == "PA" + <orateur><id>` sur **1 232 692 des 1 235 317** paragraphes
# qui portent les deux. Le préfixage vaut donc pour les trois archives.
#
# Ce que l'activation coûte a été multiplié par la correction du parseur, pas
# réduit : là où #510 mesurait 104 239 interventions et 136,8 Mio d'index pour la
# seule 17e, il y en a **1 227 415 pour les trois**, soit ~7,5 fois plus, et
# 1 664,8 Mio d'index sur disque. C'est ce qui rend la TRANCHE PAR ACTEUR
# obligatoire, et non plus « à écrire un jour » : l'index était relu ENTIER, à
# chaque candidat et pour chaque législature (12,5 s et 3,8 Gio de RSS de pic
# mesurés le 26/08/2026 sur les trois archives), face au budget de 240 s de
# #498/#500. Un candidat ne lit désormais que sa propre tranche — même patron que
# #392 (amendements) et #403 (scrutins), et la même règle d'AGENTS.md : « un cache
# disque évite un re-téléchargement, jamais un re-parsing ».
#
# Ce qui N'A PAS été remesuré ici, faute de pouvoir télécharger les archives dans
# cet environnement : le coût par candidat et le pic de RSS de la nouvelle forme.
# Ils sont bornés par CONSTRUCTION (une tranche d'acteur lue, jamais l'index),
# pas par une mesure — la mesure reste à faire au premier run réel, et c'est
# écrit tel quel dans docs/decisions/syceron-actif-510.md.
SYCERON_INDEX_PAR_ACTEUR_DIRNAME = "index_par_acteur"

# Index RÉDUIT AU THÈME (#657), sous un NOM DISTINCT — jamais le même répertoire
# que l'index complet, et ce n'est pas de la prudence : les deux formes se
# distinguent par ce qu'elles ne contiennent PAS, donc un lecteur qui trouve un
# répertoire présent le lit comme complet. C'est mot pour mot le défaut de #447
# (« un répertoire qui existe n'est pas la preuve de ce qu'il contient »),
# transposé au contenu d'une entrée au lieu du format d'une clé.
#
# Le sens de lecture est asymétrique, et c'est ce qui rend les deux formes
# compatibles : le mode réduit sait lire l'index COMPLET (il en jette les champs
# lourds à la lecture), l'inverse est impossible. Un run réduit n'a donc rien à
# reconstruire quand `extract-an` a déjà publié l'index complet — le cas nominal
# en CI, où le job roster est derrière lui par `needs:`.
# #1029 — renommé quand la forme réduite a gagné l'EXTRAIT du verbatim : un
# index au nom inchangé servirait, d'un cache, des entrées sans extrait.
SYCERON_INDEX_PAR_ACTEUR_THEME_DIRNAME = "index_par_acteur_extrait"

#: Valeur publiée dans `interventions[].collecte` pour une entrée réduite au
#: thème (#657). Une entrée sans cette clé est une entrée complète : l'absence
#: de verbatim y est un constat, alors qu'elle est une DÉCISION ici, et les deux
#: ne peuvent pas se lire de la même façon (AGENTS.md §2 règle 5).
#: Importée de `schema_pivot`, jamais recopiée : c'est une valeur fermée du
#: contrat de structure, validée par `validate_profil`.
COLLECTE_INTERVENTION_THEME_SEUL = COLLECTE_THEME_SEUL

# Index plats hérités, supprimés dès qu'une tranche par acteur est publiée. Le
# premier est l'index du mode `PA\d+` — 2 octets (`{}`) construits sur 380 Mo
# d'archive, le défaut même de #510 ; le second est l'index du mode actif d'avant
# le tranchage. Aucun des deux n'est plus JAMAIS relu : servir un index de 2
# octets à un run qui, lui, sait résoudre les identifiants nus est exactement le
# défaut de cache que #505 a corrigé.
SYCERON_INDEX_FILENAMES_HERITES = (
    "index_par_acteur.json",
    "index_par_acteur_acteurs_nus.json",
)

_AIDE_REFUS_DRAPEAU_SYCERON = (
    "--activer-interventions-syceron a été RETIRÉ (#510, 27/08/2026) : la "
    "résolution des identifiants d'orateur que Syceron publie nus est désormais "
    "le comportement de collecte, et le repli NosDéputés du chemin interventions "
    "a été retiré avec le drapeau. Il n'y a plus rien à activer — retirer "
    "l'option. Pour ne pas collecter d'interventions du tout : "
    "--skip-interventions. Voir docs/decisions/syceron-actif-510.md."
)


class RefusDrapeauInterventionsSyceron(argparse.Action):
    """Refus BRUYANT de l'ancien drapeau `--activer-interventions-syceron` (#510).

    Un `unrecognized arguments` dirait que l'option n'existe pas, pas qu'elle a
    été retirée parce que son contenu est devenu le défaut. La différence
    compte : un script ou un workflow qui la passe encore doit lire la décision,
    et surtout ne pas conclure que la collecte Syceron a été désactivée. Même
    forme de refus que `--source senat` (#528).
    """

    def __init__(self, option_strings, dest, **kwargs):
        kwargs["nargs"] = 0
        kwargs.setdefault("help", argparse.SUPPRESS)
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.error(_AIDE_REFUS_DRAPEAU_SYCERON)


def _get_scrutins_lock(legislature: str) -> threading.Lock:
    """Retourne (ou crée) le verrou associé à une législature donnée."""
    with _SCRUTINS_LOCKS_META:
        if legislature not in _SCRUTINS_LOCKS:
            _SCRUTINS_LOCKS[legislature] = threading.Lock()
        return _SCRUTINS_LOCKS[legislature]


def _get_amendements_lock(legislature: str) -> threading.Lock:
    """Retourne (ou crée) le verrou associé à une législature donnée (amendements)."""
    with _AMENDEMENTS_LOCKS_META:
        if legislature not in _AMENDEMENTS_LOCKS:
            _AMENDEMENTS_LOCKS[legislature] = threading.Lock()
        return _AMENDEMENTS_LOCKS[legislature]


def _get_questions_lock(legislature: str) -> threading.Lock:
    """Retourne (ou crée) le verrou associé à une législature donnée (questions)."""
    with _QUESTIONS_LOCKS_META:
        if legislature not in _QUESTIONS_LOCKS:
            _QUESTIONS_LOCKS[legislature] = threading.Lock()
        return _QUESTIONS_LOCKS[legislature]


def _get_syceron_lock(legislature: str) -> threading.RLock:
    """Retourne (ou crée) le verrou RÉENTRANT associé à une législature (débats Syceron)."""
    with _SYCERON_LOCKS_META:
        if legislature not in _SYCERON_LOCKS:
            _SYCERON_LOCKS[legislature] = threading.RLock()
        return _SYCERON_LOCKS[legislature]


def _is_empty_payload(value: Any) -> bool:
    """Vérifie si une valeur de réponse API est vide ou absente."""
    if value is None:
        return True
    if isinstance(value, (dict, list, tuple, set)):
        return len(value) == 0
    if isinstance(value, str):
        return value.strip() == ""
    return False


# ── Ce qui parlait à NosDéputés vivait ici, et n'y est plus (#529, lot 5) ────
# Retirés ensemble parce qu'ils formaient UNE seule chaîne, du transport au
# résultat : `_get_with_watchdog` (le `requests.get` protégé par un budget mur,
# #443) et `_get_payload` (le chokepoint JSON/XML avec ses trois tentatives),
# puis `_try_urls` / `fetch_identity` (l'identité brute, quatre domaines × deux
# formats), `_normalize_search_query` / `fetch_recherche` /
# `fetch_all_intervention_results*` (le moteur de recherche d'interventions),
# `_extract_parlementaire` et `_xml_to_data`. Aucun n'avait d'autre appelant :
# l'open data AN passe par `requests.get` / `download_with_watchdog` /
# `_telecharger_flux` en direct, jamais par ici — c'est ce qui rendait le
# compteur d'appels exact, et c'est ce qui rend ce retrait total.
#
# `_normalize_search_query` est la SEULE rescapée du lot, et elle a changé de
# métier : elle normalisait la requête envoyée au moteur de recherche, elle
# normalise désormais un nom pour la correspondance slug ↔ acteur AN
# (`_build_acteur_nom_index`, `_resolve_acteur_ref_par_slug`). Elle vit
# maintenant à côté de ces deux-là, pas ici.
#
# Sont partis avec eux les DEUX compteurs de #467 et #514
# (`compteur_appels_nosdeputes`, `compteur_requetes_sans_reponse`) et le warning
# `source injoignable` qu'ils alimentaient : ils mesuraient les requêtes émises
# vers cette plateforme et celles restées sans réponse. Sur une source qui n'est
# plus interrogée, ils ne peuvent plus rendre que 0 — et un compteur
# structurellement à zéro qu'on garde sous surveillance est exactement le
# défaut que #510 a payé (une mesure muette qui se lit comme un constat).
#
# La temporisation de courtoisie de `process_candidat` qu'ils pilotaient part
# aussi : elle ménageait une API publique tierce, pas le CDN de l'Assemblée.
#
# Voir docs/decisions/retrait-nosdeputes-529.md.


def _extract_acteur_ref(url_an_ou_senat: Optional[str]) -> Optional[str]:
    """Extrait l'identifiant officiel Assemblée nationale (ex: PA2150) depuis une URL de fiche."""
    if not url_an_ou_senat:
        return None
    match = re.search(r"PA\d+", url_an_ou_senat)
    return match.group(0) if match else None


def _scrutins_shard_path_acteur(legislature: str, acteur_ref: str) -> Optional[Path]:
    """Chemin de la tranche d'index de votes d'UN acteur (#403, reprise de #392).

    Retourne `None` si `acteur_ref` n'a pas la forme attendue d'un identifiant
    AN (`PA` suivi de chiffres) : le nom de fichier en étant dérivé, on refuse
    tout ce qui pourrait sortir du répertoire de cache plutôt que d'assainir
    approximativement."""
    if not isinstance(acteur_ref, str) or not re.fullmatch(r"PA\d+", acteur_ref):
        return None
    return (
        SCRUTINS_CACHE_DIR
        / legislature
        / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
        / f"{acteur_ref}.json"
    )


def _scrutins_zip_url(legislature: str) -> Optional[str]:
    """URL de l'archive open data des scrutins d'une législature, ou `None` si
    l'Assemblée nationale n'en publie pas (13e et antérieures)."""
    zip_name = AN_SCRUTINS_ZIP_NAME.get(legislature)
    if not zip_name:
        return None
    return f"{AN_OPENDATA_BASE}/{legislature}/loi/scrutins/{zip_name}"


def _iter_votants(decompte_nominatif: dict, position: str, list_keys: tuple[str, ...]):
    """Parcourt la liste nominative des votants pour une position donnée.

    `list_keys` énumère les noms de clé possibles pour cette position, les deux
    schémas cohabitant dans les archives réelles (relevé exhaustif du
    18/08/2026 sur les quatre législatures) :
    - pluriel `pours`/`contres`/`abstentions`/`nonVotants` : schéma moderne,
      toute la 15e/17e et 4 105 des 4 106 scrutins de la 16e ;
    - singulier `pour`/`contre` : toute la 14e (avec `abstentions`/`nonVotants`
      au pluriel) ;
    - singulier `pour`/`contre`/`abstention`/`nonVotant` : le scrutin du
      Congrès `VTCGR5L16V1` (4 mars 2024), seule occurrence.

    Ce dernier cas n'est pas théorique : l'indexeur d'avant #403 n'acceptait
    que le pluriel et perdait donc ce scrutin en silence pour tout le jeu de
    données."""
    for list_key in list_keys:
        block = decompte_nominatif.get(list_key)
        if not isinstance(block, dict):
            continue
        votants = block.get("votant")
        if votants is None:
            continue
        if isinstance(votants, dict):
            votants = [votants]
        for v in votants:
            if isinstance(v, dict) and v.get("acteurRef"):
                yield v["acteurRef"], position


# Position du schema pivot -> noms de cle possibles dans decompteNominatif
# (voir `_iter_votants` pour la difference de schema entre la 14e et les
# legislatures suivantes).
_SCRUTINS_POSITION_KEYS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pour", ("pours", "pour")),
    ("contre", ("contres", "contre")),
    ("abstention", ("abstentions", "abstention")),
    ("non_votant", ("nonVotants", "nonVotant")),
)


def _iter_scrutins_bruts(data: Any):
    """Parcourt les scrutins d'une entrée d'archive, quel que soit son conditionnement.

    Deux conditionnements coexistent chez l'Assemblée nationale (constaté le
    18/08/2026 sur les archives réelles) :
    - légis 15/16/17 : une arborescence `json/`, **un fichier par scrutin**,
      racine `{"scrutin": {...}}` ;
    - légis 14 : un JSON **monolithique** `Scrutins_XIV.json`, racine
      `{"scrutins": {"scrutin": [...]}}`, avec la même structure de scrutin.

    C'est le même changement d'architecture AN entre la 14e et la 15e que pour
    les dossiers législatifs (#400) et les amendements — mais ici les données
    de la 14e sont bien présentes, seul le conditionnement diffère : les
    ignorer perdrait 1 354 scrutins réels. Le conditionnement est détecté par
    la clé racine, jamais par le nom de fichier."""
    if not isinstance(data, dict):
        return
    unitaire = data.get("scrutin")
    if isinstance(unitaire, dict):
        yield unitaire
        return
    groupe = data.get("scrutins")
    if isinstance(groupe, dict):
        scrutins = groupe.get("scrutin")
        if isinstance(scrutins, dict):
            scrutins = [scrutins]
        for scrutin in scrutins or []:
            if isinstance(scrutin, dict):
                yield scrutin


def _parse_scrutins_zip(
    zip_path_or_bytes: Any, legislature: str
) -> tuple[dict[str, dict[str, Any]], dict[str, list[list[str]]]]:
    """Parse une archive de scrutins AN en `(scrutins, index_par_acteur)` dédupliqués.

    Lu directement depuis le zip, sans extraction sur disque : l'arborescence
    décompressée pèse 64 à 182 Mo par législature alors que seul l'index en est
    tiré (extrait de la construction pour être réutilisable par
    `build_scrutins_index_figes.py`, qui parse une archive téléchargée hors CI).

    - `scrutins` : `uid -> {numero, date, titre, sort, legislature,
      type_scrutin, type_vote, demandeur}`, le meta stocké UNE seule fois
      (forme dédupliquée, #377). Les trois derniers champs sont la
      qualification sourcée ajoutée par #639 : voir `_SCRUTINS_TYPE_PAR_CODE`
      et `_scrutins_store_qualifie`, qui refuse un cache antérieur ;
    - `index_par_acteur` : `acteurRef -> [[uid, position], ...]`, référence
      minimale par lien acteur/scrutin.

    L'`uid` (ex. `VTANR5L17V1000`) porte la législature : il est unique toutes
    législatures confondues, contrairement au `numero` qui repart de 1 à chaque
    législature — c'est lui qui sert de clé de déduplication inter-législatures
    dans `fetch_votes_officiels`.

    Lève `zipfile.BadZipFile` si l'archive est invalide (laissé à l'appelant)."""
    scrutins: dict[str, dict[str, Any]] = {}
    index: dict[str, list[list[str]]] = {}
    ignores_hors_an = 0

    with zipfile.ZipFile(zip_path_or_bytes) as zf:
        membres = [m for m in zf.namelist() if m.endswith(".json")]
        for membre in membres:
            try:
                with zf.open(membre) as f:
                    data = json.load(io.TextIOWrapper(f, encoding="utf-8"))
            except (json.JSONDecodeError, OSError, KeyError):
                continue
            for scrutin in _iter_scrutins_bruts(data):
                uid = scrutin.get("uid")
                organe = (scrutin.get("ventilationVotes") or {}).get("organe") or {}
                groupes = (organe.get("groupes") or {}).get("groupe")
                if not uid or groupes is None:
                    continue
                if not str(uid).startswith(AN_SCRUTIN_UID_PREFIXE):
                    # Scrutin du Congrès : hors périmètre, voir AN_SCRUTIN_UID_PREFIXE.
                    ignores_hors_an += 1
                    continue
                if isinstance(groupes, dict):
                    groupes = [groupes]
                type_vote_brut = scrutin.get("typeVote")
                code_type = (
                    type_vote_brut.get("codeTypeVote") if isinstance(type_vote_brut, dict) else None
                )
                type_scrutin, type_vote = _SCRUTINS_TYPE_PAR_CODE.get(code_type, (None, None))
                demandeur_brut = scrutin.get("demandeur")
                demandeur = (
                    demandeur_brut.get("texte") if isinstance(demandeur_brut, dict) else None
                )
                scrutins[uid] = {
                    "numero": scrutin.get("numero"),
                    "date": scrutin.get("dateScrutin"),
                    "titre": scrutin.get("titre"),
                    "sort": (scrutin.get("sort") or {}).get("libelle"),
                    "legislature": scrutin.get("legislature") or legislature,
                    # Qualification sourcee du scrutin (#639), cf.
                    # _SCRUTINS_TYPE_PAR_CODE. None quand la source ne qualifie
                    # pas : l'absence est publiee comme absence.
                    "type_scrutin": type_scrutin,
                    "type_vote": type_vote,
                    # Qui a demande le scrutin public : « President du groupe
                    # ... », « Conference des presidents ». Renseigne sur
                    # 18 226 / 18 311 scrutins bruts, `null` sur 85 (releve du
                    # 31/08/2026) — toujours un objet, `texte` str ou None.
                    "demandeur": demandeur if isinstance(demandeur, str) and demandeur else None,
                }
                for groupe in groupes:
                    if not isinstance(groupe, dict):
                        continue
                    decompte = (groupe.get("vote") or {}).get("decompteNominatif") or {}
                    for position, list_keys in _SCRUTINS_POSITION_KEYS:
                        for acteur_ref, pos in _iter_votants(decompte, position, list_keys):
                            index.setdefault(acteur_ref, []).append([uid, pos])

    if ignores_hors_an:
        print(
            f"  [i] {ignores_hors_an} scrutin(s) hors Assemblée nationale (Congrès) "
            f"écarté(s) pour la législature {legislature} — voir AN_SCRUTIN_UID_PREFIXE"
        )
    return scrutins, index


def _write_cached_scrutins(
    legislature: str,
    scrutins: dict[str, dict[str, Any]],
    index_par_acteur: dict[str, list[list[str]]],
) -> None:
    """Écrit (best-effort) le cache disque d'une législature sous forme
    dédupliquée et shardée : `scrutins.json` puis une tranche par acteur.

    `scrutins.json` est écrit en premier et le répertoire de tranches n'est
    considéré valide en lecture que s'il existe : une écriture interrompue
    laisse donc un cache traité comme absent (reconstruit au run suivant),
    jamais un couple incohérent. Écrase au passage l'`index_par_acteur.json`
    plat hérité d'avant #403 et l'arborescence `json/` décompressée, qui
    pesaient ensemble jusqu'à 538 Mo pour la seule 17e législature — la
    migration d'un ancien cache libère donc cette place au premier run."""
    cache_dir = SCRUTINS_CACHE_DIR / legislature
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_dir / SCRUTINS_CACHE_SCRUTINS_FILENAME, "w", encoding="utf-8") as f:
        json.dump(scrutins, f, ensure_ascii=False)

    index_dir = cache_dir / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    # Répertoire reconstruit de zéro : un acteur disparu d'une reconstruction
    # ne doit pas laisser sa tranche périmée derrière lui.
    shutil.rmtree(index_dir, ignore_errors=True)
    index_dir.mkdir(parents=True, exist_ok=True)
    for acteur_ref, refs in index_par_acteur.items():
        shard = _scrutins_shard_path_acteur(legislature, acteur_ref)
        if shard is None:
            continue  # acteurRef hors forme attendue : ignoré plutôt qu'écrit
        with open(shard, "w", encoding="utf-8") as f:
            json.dump(refs, f, ensure_ascii=False)

    (cache_dir / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_FILENAME_LEGACY).unlink(missing_ok=True)
    shutil.rmtree(cache_dir / "json", ignore_errors=True)


def _read_cached_scrutins_store(legislature: str) -> Optional[dict[str, dict[str, Any]]]:
    """Store dédupliqué `uid -> scrutin` d'une législature, mémoïsé en mémoire process.

    Sûr à mémoïser, contrairement aux index par acteur complets : mesuré sur le
    cache réel, les quatre stores réunis pèsent 5,5 Mo (2,5 Mo pour la 17e, la
    plus lourde) là où les quatre index par acteur pèsent 68 Mo — et 741 Mo
    une fois expansés en forme plate, ce qui est exactement le chemin qui a
    déclenché deux OOM sur les amendements (#377, #392).

    Le cache disque n'est jamais réécrit pendant la vie d'un process de collecte
    au-delà de sa première matérialisation, donc mémoïser ne peut pas servir une
    version périmée. La lecture prend le même verrou par législature que cette
    matérialisation : sans lui, un thread pouvant mémoïser un `None` lu avant
    l'écriture du cache juste après que le thread écrivain a purgé le mémo, la
    législature resterait « indisponible » pour tout le reste du process."""
    with _get_scrutins_lock(legislature):
        if legislature in _SCRUTINS_STORE_MEMO:
            return _SCRUTINS_STORE_MEMO[legislature]
        path = SCRUTINS_CACHE_DIR / legislature / SCRUTINS_CACHE_SCRUTINS_FILENAME
        store: Optional[dict[str, dict[str, Any]]] = None
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    charge = json.load(f)
                if isinstance(charge, dict):
                    store = charge
            except (json.JSONDecodeError, OSError):
                store = None  # cache corrompu : traité comme absent
        _SCRUTINS_STORE_MEMO[legislature] = store
        return store


def _clear_scrutins_store_memo() -> None:
    """Vide le mémo du store (tests uniquement : un process de collecte ne voit
    jamais le cache disque changer sous lui après matérialisation)."""
    _SCRUTINS_STORE_MEMO.clear()


# Champ dont la présence atteste qu'un store de scrutins a été produit APRÈS
# #639. Un store écrit avant ne porte que cinq champs, et il est indiscernable
# d'un store complet dont la source n'aurait rien qualifié — sauf qu'ici la
# source qualifie tout : `typeVote` est renseigné sur 18 311 / 18 311 scrutins
# bruts. Un store où AUCUNE entrée ne porte la clé est donc périmé, jamais
# « une législature sans qualification ».
SCRUTINS_CHAMP_QUALIFICATION = "type_scrutin"


def _scrutins_store_qualifie(store: Any) -> bool:
    """True si un store `uid -> scrutin` porte la qualification de #639.

    « Un répertoire qui existe n'est pas la preuve de ce qu'il contient »
    (AGENTS.md §5, leçon du cache d'amendements) : un cache présent mais écrit
    sous l'ancienne projection à cinq champs republierait 17 748 scrutins sans
    `type_scrutin` et sans les 66 motions de censure, sans que rien ne le dise.

    Le test porte sur la **clé**, pas sur sa valeur : `type_scrutin` peut
    légitimement valoir `None` sur un code inconnu, et exiger une valeur
    reviendrait à refuser un store correct. Un store vide est déclaré non
    qualifié — il n'y a rien à en tirer, et le reconstruire ne coûte rien.
    """
    if not isinstance(store, dict) or not store:
        return False
    return any(
        isinstance(scrutin, dict) and SCRUTINS_CHAMP_QUALIFICATION in scrutin
        for scrutin in store.values()
    )


def _lire_store_scrutins_disque(legislature: str) -> Optional[dict[str, Any]]:
    """Store de scrutins lu sur disque, sans mémo ni verrou. `None` si absent
    ou illisible."""
    path = SCRUTINS_CACHE_DIR / legislature / SCRUTINS_CACHE_SCRUTINS_FILENAME
    if not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            charge = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    return charge if isinstance(charge, dict) else None


def _scrutins_cache_present(legislature: str) -> bool:
    """True si le cache disque d'une législature est déjà matérialisé sous la
    forme dédupliquée + shardée (#403) ET qualifiée (#639). Un cache écrit
    avant #403 (fichier unique, forme plate) est indiscernable d'un cache
    absent, donc reconstruit — jamais relu en mémoire, ce qui est précisément
    ce qu'il fallait éviter. Un cache écrit avant #639 est refusé pour la même
    raison : l'existence n'est pas la conformité."""
    cache_dir = SCRUTINS_CACHE_DIR / legislature
    if not (
        (cache_dir / SCRUTINS_CACHE_SCRUTINS_FILENAME).is_file()
        and (cache_dir / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME).is_dir()
    ):
        return False
    if not _scrutins_store_qualifie(_lire_store_scrutins_disque(legislature)):
        print(
            f"  [i] Cache de scrutins de la législature {legislature} antérieur à #639 "
            "(aucune qualification `type_scrutin`) : reconstruit."
        )
        return False
    return True


def _load_frozen_scrutins_index(legislature: str) -> bool:
    """Matérialise dans le cache disque l'index committé d'une législature figée
    (`AN_SCRUTINS_LEGISLATURES_FIGEES`), construit hors CI par
    `build_scrutins_index_figes.py` sous forme dédupliquée et gzippée.

    Retourne False si le fallback committé est absent, illisible **ou antérieur
    à #639** : l'appelant retombe alors sur le chemin réseau standard (l'archive
    reste téléchargeable, le gel n'est ici qu'une économie de CI — voir
    docs/decisions/votes-multi-legislature.md).

    Le refus d'un index figé non qualifié est délibéré (#639). L'alternative —
    l'accepter en avertissant — laisserait les législatures 14, 15 et 16
    publier 9 314 scrutins sans `type_scrutin` et 43 motions de censure
    étiquetées `vote_texte`, c'est-à-dire un fait faux, jusqu'à ce que
    quelqu'un pense à relancer `build_scrutins_index_figes.py`. Le coût du
    refus est borné et transitoire : trois archives retéléchargées (20,0 Mo au
    total — 0,7 + 9,2 + 10,1 Mo, mesurés le 31/08/2026) tant que les index figés
    n'ont pas été régénérés."""
    frozen_dir = AN_SCRUTINS_FIGES_DIR / legislature
    frozen_scrutins_path = frozen_dir / SCRUTINS_FIGES_SCRUTINS_FILENAME
    frozen_index_path = frozen_dir / SCRUTINS_FIGES_INDEX_PAR_ACTEUR_FILENAME
    if not frozen_scrutins_path.is_file() or not frozen_index_path.is_file():
        return False
    try:
        with gzip.open(frozen_scrutins_path, "rt", encoding="utf-8") as f:
            scrutins = json.load(f)
        with gzip.open(frozen_index_path, "rt", encoding="utf-8") as f:
            index_par_acteur = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(scrutins, dict) or not isinstance(index_par_acteur, dict):
        return False
    if not _scrutins_store_qualifie(scrutins):
        print(
            f"  [!] Index de scrutins figé de la législature {legislature} antérieur à #639 "
            "(projection à cinq champs, aucune qualification `type_scrutin`) : ignoré, "
            "l'archive open data est retéléchargée. Régénérer avec "
            f"`python3 src/build_scrutins_index_figes.py --legislature {legislature}` "
            "pour supprimer ce téléchargement."
        )
        return False

    try:
        _write_cached_scrutins(legislature, scrutins, index_par_acteur)
    except OSError:
        return False
    return True


def _ensure_scrutins_index(legislature: str) -> bool:
    """Garantit la présence du cache d'index de votes d'une législature.

    Ordre : cache déjà matérialisé → index committé si la législature est figée
    → téléchargement + parsing de l'archive AN. Retourne False si aucune de ces
    voies n'aboutit (législature sans open data, réseau indisponible, archive
    invalide) — chaque législature étant tentée indépendamment, un échec ici
    n'empêche jamais les autres d'être agrégées.

    Thread-safe : un verrou par législature garantit qu'un seul thread à la fois
    télécharge et écrit le cache d'une législature donnée ; des législatures
    différentes sont traitées sans blocage mutuel."""
    with _get_scrutins_lock(legislature):
        if _scrutins_cache_present(legislature):
            return True

        if legislature in AN_SCRUTINS_LEGISLATURES_FIGEES and _load_frozen_scrutins_index(legislature):
            print(f"-> Index de scrutins figé réutilisé (législature {legislature}, aucun téléchargement)")
            return True

        url = _scrutins_zip_url(legislature)
        if not url:
            return False

        print(f"-> Téléchargement des scrutins officiels (Assemblée nationale) : {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=60)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"  [!] Échec du téléchargement des scrutins officiels : {exc}")
            return False

        try:
            scrutins, index = _parse_scrutins_zip(io.BytesIO(resp.content), legislature)
        except zipfile.BadZipFile as exc:
            print(f"  [!] Archive de scrutins invalide : {exc}")
            return False

        if not scrutins:
            return False

        print(f"-> Indexation de {len(scrutins)} scrutins officiels (législature {legislature})...")
        try:
            _write_cached_scrutins(legislature, scrutins, index)
        except OSError:
            return False
        _SCRUTINS_STORE_MEMO.pop(legislature, None)
        return True


def _read_cached_votes_acteur(legislature: str, acteur_ref: str) -> Optional[list[dict[str, Any]]]:
    """Votes d'UN acteur pour une législature, résolus depuis le cache dédupliqué
    et shardé. Retourne `None` si le cache est absent/illisible, une liste
    éventuellement vide si l'acteur n'y figure pas — distinguer « n'a pas voté
    sous cette législature » de « index indisponible » est ce qui pilote le
    warning côté `fetch_votes_officiels` (règle 5 : une donnée manquante n'est
    jamais un 0).

    Coût : une tranche d'acteur (~55 Ko) plus le store mémoïsé, au lieu des
    132 à 357 Mo d'index complets que la forme d'avant #403 relisait pour
    chaque candidat."""
    store = _read_cached_scrutins_store(legislature)
    if store is None:
        return None

    index_dir = SCRUTINS_CACHE_DIR / legislature / SCRUTINS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    if not index_dir.is_dir():
        return None

    shard_path = _scrutins_shard_path_acteur(legislature, acteur_ref)
    if shard_path is None or not shard_path.is_file():
        return []

    try:
        with open(shard_path, encoding="utf-8") as f:
            refs = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(refs, list):
        return None

    votes: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, (list, tuple)) or len(ref) != 2:
            continue
        uid, position = ref
        base = store.get(uid)
        if base is None:
            continue
        votes.append({**base, "uid": uid, "position": position})
    return votes


def fetch_votes_officiels(
    url_an_ou_senat: Optional[str], warnings: Optional[list[str]] = None
) -> tuple[list[dict[str, Any]], list[str]]:
    """Récupère les votes nominatifs officiels d'un député via l'open data de l'Assemblée nationale.

    L'endpoint /votes de NosDéputés.fr est en panne (HTTP 500 systématique, y
    compris sur l'exemple officiel de leur propre documentation, testé sur tous
    les domaines et législatures disponibles). On utilise donc directement les
    données ouvertes de data.assemblee-nationale.fr, qui contiennent le détail
    nominatif (pour/contre/abstention/non-votant) de chaque scrutin, identifié
    par l'acteurRef (ex: PA2150) du parlementaire.

    Agrège **toutes** les législatures publiées (`AN_SCRUTINS_LEGISLATURES`),
    comme le font déjà les amendements et les dossiers législatifs : jusqu'à
    #403, une seule législature était interrogée — celle déduite du domaine
    NosDéputés où l'identité avait été trouvée, donc en pratique toujours la
    16e, ce qui arrêtait les votes de tout le jeu de données en juin 2024 et en
    perdait 2,7x.

    Chaque législature est tentée indépendamment : une archive indisponible
    n'interrompt jamais l'agrégation des autres (même précaution qu'en #241 sur
    les amendements) ; si `warnings` est fourni, l'absence y est tracée par
    législature.

    Retourne `(votes, legislatures_couvertes)`, les votes triés du plus récent
    au plus ancien et dédupliqués par `uid` de scrutin — jamais par `numero`,
    qui repart de 1 à chaque législature (#400 : un fait ne doit jamais être
    compté deux fois)."""
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        return [], []

    votes: list[dict[str, Any]] = []
    vus: set[str] = set()
    legislatures_couvertes: list[str] = []
    for legislature in AN_SCRUTINS_LEGISLATURES:
        if not _ensure_scrutins_index(legislature):
            if warnings is not None:
                warnings.append(avertissement(
                    f"{WARNING_PREFIX_VOTES_INTROUVABLES} (législature {legislature}) : "
                    "index des scrutins indisponible (archive open data non téléchargée ou invalide).",
                    # Une panne de NOTRE cache, que `couverture` publie déjà au
                    # lecteur sous `panne` avec sa preuve : ici c'est le
                    # diagnostic, pas l'explication (#642).
                    DESTINATAIRE_INTERNE,
                ))
            continue
        records = _read_cached_votes_acteur(legislature, acteur_ref)
        if records is None:
            if warnings is not None:
                warnings.append(avertissement(
                    f"{WARNING_PREFIX_VOTES_INTROUVABLES} (législature {legislature}) : "
                    "cache d'index des scrutins illisible.",
                    DESTINATAIRE_INTERNE,
                ))
            continue
        retenus = 0
        for record in records:
            uid = record.get("uid")
            if uid in vus:
                continue
            vus.add(uid)
            votes.append(record)
            retenus += 1
        if retenus:
            legislatures_couvertes.append(legislature)

    votes.sort(key=lambda v: v.get("date") or "", reverse=True)
    return votes, sorted(legislatures_couvertes)


# Type d'auteur (open data amendements) -> type_deposant du schema pivot.
_AMENDEMENT_TYPE_AUTEUR_MAP: dict[str, str] = {
    "Député": "depute",
    # "Depute" (sans accent) : forme observée dans le schéma legacy de la 14e
    # législature (archive réelle, 15/08/2026) — jamais produite par le
    # schéma moderne (15/16/17), ajoutée sans risque de collision.
    "Depute": "depute",
    "Gouvernement": "gouvernement",
    "Rapporteur": "commission_rapporteur",
    "Commission": "commission_rapporteur",
}

# (etat.libelle, sousEtat.libelle) -> sort du schema pivot. Determine
# empiriquement sur ~3000 amendements de la 17e legislature : "En traitement"
# et "A discuter" (sousEtat souvent absent) signifient que le sort n'est pas
# encore connu, et sont volontairement absents de cette table (sort reste
# None). Les etats "Irrecevable"/"Irrecevable 40" sont traites a part (voir
# _derive_amendement_sort) car leurs sousEtat ne sont pas des sorts mais des
# motifs d'irrecevabilite.
_AMENDEMENT_SORT_MAP: dict[tuple[Optional[str], Optional[str]], str] = {
    ("Discuté", "Rejeté"): "rejeté",
    ("Discuté", "Adopté"): "adopté",
    ("Discuté", "Tombé"): "tombé",
    ("Discuté", "Non soutenu"): "non_soutenu",
    ("Discuté", "Retiré"): "retiré",
    ("Retiré", "Retiré après publication"): "retiré",
    ("Retiré", "Retiré avant publication"): "retiré",
}


def _derive_amendement_sort(etat_libelle: Optional[str], sousetat_libelle: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Déduit (sort, base_juridique_irrecevabilite) depuis les libellés d'état officiels.

    L'open data amendements distingue "Irrecevable 40" (irrecevabilité
    financière, art. 40) d'"Irrecevable" tout court (les nombreux autres motifs
    observés — cavalier art. 45, sous-amendement art. 98, hors délais, etc. —
    ne correspondent pas tous littéralement à l'art. 45, mais le schéma pivot
    ne distingue que "art. 40" | "art. 45" : "art. 45" est donc utilisé comme
    catégorie par défaut pour tout motif d'irrecevabilité non financier).
    """
    if etat_libelle in ("Irrecevable", "Irrecevable 40"):
        base = "art. 40" if etat_libelle == "Irrecevable 40" else "art. 45"
        return "irrecevable", base
    return _AMENDEMENT_SORT_MAP.get((etat_libelle, sousetat_libelle)), None


def _extract_cosignataire_refs(cosignataires_bloc: Any) -> list[str]:
    """Normalise les différentes formes de `signataires.cosignataires`.

    Le bulk AN expose selon les jeux soit `{"acteurRef": ...}`, soit
    `{"acteur": {"acteurRef": ...}}` / `{"acteur": [{"acteurRef": ...}, ...]}`.
    """
    if not isinstance(cosignataires_bloc, dict):
        return []

    refs: list[str] = []

    direct_refs = cosignataires_bloc.get("acteurRef")
    if isinstance(direct_refs, str) and direct_refs:
        refs.append(direct_refs)
    elif isinstance(direct_refs, list):
        refs.extend(ref for ref in direct_refs if isinstance(ref, str) and ref)

    acteurs = cosignataires_bloc.get("acteur")
    items = acteurs if isinstance(acteurs, list) else [acteurs]
    for item in items:
        if isinstance(item, dict):
            acteur_ref = item.get("acteurRef")
            if isinstance(acteur_ref, str) and acteur_ref:
                refs.append(acteur_ref)

    # Déduplication en conservant l'ordre de lecture du payload source.
    return list(dict.fromkeys(refs))


def _texte_an(valeur: Any) -> Optional[str]:
    """Chaîne de l'open data AN, ou `None` quand la source ne publie rien.

    L'open data AN est du XML converti en JSON, et un élément vide y arrive
    sous la forme d'un **objet**, pas d'un `null` :
    `{"@xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "@xsi:nil": "true"}`. Recopié tel quel dans un enregistrement pivot, ce
    marqueur fait passer un `dict` là où tout l'aval attend une chaîne — il ne
    se voit pas à l'écriture, il casse à la lecture.

    C'est la **quatrième** fois que cet idiome mord dans ce dépôt : #539 l'a
    trouvé dans `identite.uri_hatvp` (186 profils sur 476 portaient le marqueur
    au lieu d'une URI, voir `normalize_profil._uri_hatvp_publiable`), #562 dans
    `cycleDeVie.dateDepot` des amendements — 8 amendements sur les 624 180 des
    trois législatures figées, mais **99 profils publiés sur 481** privés de
    tous leurs amendements par le `TypeError` que le tri par date en tirait —,
    et #556 dans **trois** champs d'identité à la fois (voir
    `_champ_identite_an`). Une valeur nil n'est pas une donnée : c'est une
    donnée manquante, et le pivot l'écrit `null` (AGENTS.md §2.5).
    """
    return valeur if isinstance(valeur, str) and valeur else None


#: Alias de lecture pour les champs d'identité d'AMO30 (#556). Même fonction que
#: `_texte_an` — le nom dit seulement *où* elle s'applique, et il est le seul
#: point de lecture autorisé sur `json/acteur/*.json`.
#:
#: ## Pourquoi un passage systématique, et pas un correctif champ par champ
#:
#: Le convertisseur XML → JSON d'AMO30 **ne connaît pas le nom du champ** : il
#: rend `{"@xmlns:xsi": …, "@xsi:nil": "true"}` pour *n'importe quel* élément
#: déclaré vide. Corriger `uri_hatvp` seul aurait donc réparé le champ mesuré et
#: laissé les autres — ce qu'a montré la mesure du 29/08/2026 sur les 481
#: profils publiés, en croisant `raw_data/profiles` et `pivot_data/profiles` :
#:
#: | Champ publié | Profils touchés | Forme publiée |
#: | --- | ---: | --- |
#: | `identite.uri_hatvp` | **191** | l'objet marqueur, tel quel |
#: | `identite.profession` | **20** | l'objet marqueur, tel quel |
#: | `identite.lieu_naissance` | **28** | le `repr` Python du marqueur, **en chaîne** |
#:
#: Le troisième est le pire des trois, et c'est lui qui justifie la règle plutôt
#: que trois correctifs : `_format_lieu_naissance` **interpole** ses arguments,
#: donc le marqueur y devient une chaîne. Aucun `isinstance(..., str)` en aval
#: ne peut plus le rattraper, et 18 profils publient un lieu de naissance qui
#: est intégralement de la plomberie XML —
#: `"{'@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance', …} ({…})"`.
#: Un dict truthy se repère ; une chaîne non vide se lit comme une donnée.
_champ_identite_an = _texte_an


#: Code de catégorie socioprofessionnelle en tête du libellé de profession
#: d'AMO30 : `"(33) - Cadre de la fonction publique"` (#641).
_PREFIXE_CODE_CSP_AN = re.compile(r"^\(\s*(\d+)\s*\)\s*-\s*")

#: Le libellé d'un code de la famille 8x qui **énonce une absence** de
#: profession. Le critère est en deux parties, et les deux sont nécessaires :
#: la **famille du code** (8x, « personnes sans activité professionnelle » dans
#: la nomenclature socioprofessionnelle) et le **libellé de la source
#: elle-même**. La famille seule nullerait `"(84) - Elève, étudiant"`, qui nomme
#: une situation et non une absence ; le libellé seul s'appuierait sur des mots
#: là où la nomenclature offre une structure.
_MARQUEUR_ABSENCE_PROFESSION = "sans activité professionnelle"


def _profession_an(valeur: Any) -> Optional[str]:
    """Profession publiable d'un acteur AMO30, ou `None` — jamais un code de
    nomenclature, jamais l'énoncé d'une absence de profession (#641).

    ## Ce que la source publie réellement

    `acteur.profession.libelleCourant` porte deux formes. La plupart du temps
    un libellé nu (`"Avocat"`). **128 fois sur les 3 117 acteurs** de l'archive,
    le libellé est préfixé du code de catégorie socioprofessionnelle :
    `"(33) - Cadre de la fonction publique"`. Le motif n'apparaît **nulle part
    ailleurs** dans `json/acteur/*.json` — mesuré champ par champ sur l'archive
    entière au 31/08/2026, 128 occurrences, toutes sur ce seul champ. C'est ce
    qui rend légitime de traiter la profession et elle seule, là où #556 devait
    traiter tous les champs : le marqueur `xsi:nil` vient du **convertisseur
    XML**, qui ne connaît pas le nom du champ ; ce préfixe-ci vient d'une
    **nomenclature**, qui n'existe que pour ce champ.

    ## Deux cas sous un même motif, et ils ne se traitent pas pareil

    Mesuré sur les 481 profils publiés : 8 des 457 qui renseignent
    `identite.profession` publient un code brut.

    | Cas | Corpus | Traitement |
    | --- | ---: | --- |
    | `"(33) - Cadre de la fonction publique"` | 3 profils | le préfixe est du bruit, le libellé est bon : on retire le préfixe |
    | `"(85) - Personne diverse sans activité professionnelle de moins de 60 ans…"` | 5 profils | **ce n'est pas une profession**, c'est l'énoncé d'une absence : `None` |

    Le second est le vrai sujet, et c'est l'idiome de #556 : une valeur
    technique de la source recopiée là où une valeur métier était attendue, qui
    passe le seul contrôle existant — « chaîne non vide ». Une absence n'est pas
    une donnée (AGENTS.md §2 règle 5), et la page dit « profession non
    renseignée » plutôt que de la nommer.

    Aucune profession de remplacement n'est inventée : le libellé nulle ici est
    perdu, pas remplacé.
    """
    texte = _champ_identite_an(valeur)
    if texte is None or not texte.strip():
        return None
    texte = texte.strip()
    trouve = _PREFIXE_CODE_CSP_AN.match(texte)
    if trouve is None:
        return texte
    code = trouve.group(1)
    libelle = texte[trouve.end():].strip()
    if not libelle:
        # Un code sans libellé ne dit rien de publiable, et le code seul n'est
        # pas une profession.
        return None
    if code.startswith("8") and _MARQUEUR_ABSENCE_PROFESSION in libelle.lower():
        return None
    return libelle


#: Les deux niveaux de `acteur.profession.socProcINSEE` (#659), dans l'ordre où
#: ils sont publiés : la famille puis la catégorie.
CHAMPS_SOCPROC_INSEE_AN: tuple[str, str] = ("famSocPro", "catSocPro")


def _socproc_insee_an(profession: Any) -> tuple[Optional[str], Optional[str]]:
    """Les deux niveaux de la nomenclature PCS de l'INSEE portés par AMO30, ou
    `(None, None)` — jamais le marqueur d'absence (#659).

    ## Ce que la source publie, mesuré

    `acteur.profession.socProcINSEE` existe sur **les 3 117 fiches** de
    l'archive, avec exactement ses deux clés, et les deux niveaux sont
    **toujours renseignés ou absents ensemble** : 2 177 fiches portent un
    couple de libellés (70 %), 940 portent le marqueur `xsi:nil` **aux deux
    niveaux à la fois** (mesure du 31/08/2026 sur
    `AMO30_tous_acteurs_tous_mandats_tous_organes_historique.json.zip`). Aucune
    fiche ne renseigne un niveau sans l'autre.

    ## Pourquoi ce champ et pas `libelleCourant`

    `libelleCourant` est du texte libre, et #641 a montré ce qu'il peut
    contenir. `socProcINSEE` porte la **nomenclature des professions et
    catégories socioprofessionnelles de l'INSEE**, appliquée par l'Assemblée
    nationale elle-même et publiée sous Licence Ouverte. C'est le point qui
    décide : une catégorisation socioprofessionnelle construite par ce dépôt
    serait un acte éditorial contestable (AGENTS.md §2 règle 1) ; reprendre
    celle de la source ne l'est pas.

    Les deux champs coexistent et ne disent pas la même chose. `PA794778` le
    montre en un seul acteur : `libelleCourant` y vaut `"(85) - Personne
    diverse sans activité professionnelle de moins de 60 ans…"`, que
    `_profession_an` refuse de publier comme une profession, tandis que
    `famSocPro` vaut `"Sans profession déclarée"` — la même situation, dite par
    la nomenclature au lieu d'être devinée dans une phrase.

    ## `nil` n'est PAS « sans profession déclarée »

    Les deux existent séparément dans la source : 940 fiches au marqueur, et
    **85 dont la famille EST `"Sans profession déclarée"`**, une famille à part
    entière de la nomenclature. Les confondre publierait un fait — « cette
    personne n'a pas déclaré de profession » — là où la source dit seulement
    qu'elle ne l'a pas classée. C'est le contresens exact de #556, et le
    filtrage passe donc par `_champ_identite_an`, comme tout ce qui est lu dans
    `json/acteur/*.json`.

    Aucune normalisation typographique n'est appliquée ici : les libellés sont
    publiés tels que la source les écrit, variantes comprises (« Professions
    Intermédiaires » 107 et « Professions intermédiaires » 58). Le regroupement
    est l'affaire de qui agrège, pas de qui publie un fait individuel — voir
    `docs/decisions/civilite-et-pcs-insee-659.md`.
    """
    socproc = (profession or {}).get("socProcINSEE") if isinstance(profession, dict) else None
    if not isinstance(socproc, dict):
        return None, None
    famille, categorie = (
        _champ_identite_an(socproc.get(cle)) for cle in CHAMPS_SOCPROC_INSEE_AN
    )
    return famille, categorie


def _parse_amendement_entry(data: Any) -> Optional[list[tuple[str, dict[str, Any]]]]:
    """Extrait les enregistrements indexés par acteurRef d'un amendement brut.

    Construit une entrée pour l'auteur principal et une entrée par cosignataire,
    avec un champ `role_signataire` permettant de distinguer les deux cas dans
    les usages avals.

    Gère le schéma « moderne » des archives amendements AN (légis 15/16/17,
    un fichier JSON par amendement, racine `{"amendement": {...}}`). La
    législature 14 utilise un schéma « legacy » distinct (un unique fichier
    JSON agrégeant tous les amendements, racine `{"textesEtAmendements":
    {...}}`), géré par `_parse_amendement_entry_legacy` — voir #299,
    docs/decisions/amendements-legislatures-figees.md. Le choix
    entre les deux se fait dans `_parse_amendements_zip`, par entrée, selon
    la clé racine du contenu.
    """
    amendement = data.get("amendement") if isinstance(data, dict) else None
    if not isinstance(amendement, dict):
        return None

    signataires = amendement.get("signataires") or {}
    auteur = signataires.get("auteur") or {}
    acteur_ref = auteur.get("acteurRef")
    if not isinstance(acteur_ref, str) or not acteur_ref:
        return None

    cosignataires_bloc = signataires.get("cosignataires") or {}
    cosign_refs = _extract_cosignataire_refs(cosignataires_bloc)

    cycle_de_vie = amendement.get("cycleDeVie") or {}
    etat = cycle_de_vie.get("etatDesTraitements") or {}
    etat_libelle = (etat.get("etat") or {}).get("libelle") if isinstance(etat.get("etat"), dict) else None
    sousetat_libelle = (etat.get("sousEtat") or {}).get("libelle") if isinstance(etat.get("sousEtat"), dict) else None
    sort, base_juridique = _derive_amendement_sort(etat_libelle, sousetat_libelle)

    record_base = {
        # Identifiant AN de l'amendement (ex. "AMANR5L17PO59047BTC1376P0D1N000012").
        # C'est la SEULE cle unique : `numero`/`numeroLong` repart a chaque texte
        # (mesure du 18/08/2026 sur l'archive legis 17 : 121 805 amendements pour
        # 30 616 numeroLong distincts, "AE12" porte par 7 textes), et keyer un
        # store par numero ecrase 74,9 % des amendements. Meme role que l'uid de
        # scrutin, unique toutes legislatures confondues — voir
        # docs/decisions/amendements-cle-uid.md.
        "uid": amendement.get("uid"),
        # texteLegislatifRef est l'uid du DOCUMENT amende (ex.
        # "PRJLANR5L17B0324"), et c'est une cle sourcee : elle est conservee
        # telle quelle jusqu'a l'index pivot, qui la joint a son dossier
        # legislatif (textes_dossiers_an.py, #639). Elle a ete ecrasee par le
        # titre du dossier jusqu'a #639 — 293 582 amendements publies en sont
        # restes sans cle.
        "texte_vise": _texte_an(amendement.get("texteLegislatifRef")),
        "sort": sort,
        "base_juridique_irrecevabilite": base_juridique,
        # Prefixe "an:" : ce sont des identifiants Assemblee nationale bruts, pas
        # des identifiants pivot (le slug du profil depuis #487) — la resolution
        # vers un candidat suivi par ce projet n'est pas faite ici.
        "premier_signataire": f"an:{acteur_ref}",
        "co_signataires": [f"an:{ref}" for ref in cosign_refs if isinstance(ref, str)],
        "type_deposant": _AMENDEMENT_TYPE_AUTEUR_MAP.get(auteur.get("typeAuteur")),
        # `_texte_an` et pas `.get()` nu : `dateDepot` est publié `xsi:nil` par
        # l'AN quand la date de dépôt manque, ce qui arrive en pratique (#562).
        "date": _texte_an(cycle_de_vie.get("dateDepot")),
        "numero": _texte_an((amendement.get("identification") or {}).get("numeroLong")),
        "source_url": None,
    }

    out: list[tuple[str, dict[str, Any]]] = [
        (acteur_ref, {**record_base, "role_signataire": "auteur_principal"})
    ]

    for cosign_ref in cosign_refs:
        if not isinstance(cosign_ref, str) or not cosign_ref or cosign_ref == acteur_ref:
            continue
        out.append((cosign_ref, {**record_base, "role_signataire": "cosignataire"}))

    return out


# sortEnSeance (schéma legacy légis 14, racine `textesEtAmendements`) -> sort du
# schéma pivot. Contrairement à `_AMENDEMENT_SORT_MAP` (paire etat/sousEtat
# ambiguë selon le contexte), `sort.sortEnSeance` porte déjà sans ambiguïté
# l'issue en séance : simple normalisation de casse/accentuation, pas de
# dérivation heuristique. Voir issue #299.
_LEGACY_AMENDEMENT_SORT_EN_SEANCE_MAP: dict[str, str] = {
    "Adopté": "adopté",
    "Rejeté": "rejeté",
    "Tombé": "tombé",
    "Non soutenu": "non_soutenu",
    "Retiré": "retiré",
}


def _derive_amendement_sort_legacy(
    etat: Optional[str], sort_en_seance: Optional[str]
) -> tuple[Optional[str], Optional[str]]:
    """Équivalent de `_derive_amendement_sort` pour le schéma legacy légis 14.

    Même logique d'irrecevabilité (`etat` "Irrecevable"/"Irrecevable 40",
    identique à `_derive_amendement_sort`), mais l'issue en séance est portée
    directement par `sort.sortEnSeance` côté AN : pas de table (etat, sousEtat)
    à interpréter, une simple normalisation suffit.
    """
    if etat in ("Irrecevable", "Irrecevable 40"):
        base = "art. 40" if etat == "Irrecevable 40" else "art. 45"
        return "irrecevable", base
    return _LEGACY_AMENDEMENT_SORT_EN_SEANCE_MAP.get(sort_en_seance), None


def _parse_amendement_legacy_single(
    amendement: dict[str, Any], texte_ref: Optional[str]
) -> list[tuple[str, dict[str, Any]]]:
    """Extrait les enregistrements indexés par acteurRef d'un amendement au
    format legacy (légis 14, déjà déballé d'un `texteleg`). `texte_ref` est
    porté par le `texteleg` parent, pas par l'amendement lui-même."""
    signataires = amendement.get("signataires") or {}
    auteur = signataires.get("auteur") or {}
    acteur_ref = auteur.get("acteurRef")
    if not isinstance(acteur_ref, str) or not acteur_ref:
        return []

    cosignataires_bloc = signataires.get("cosignataires") or {}
    cosign_refs = _extract_cosignataire_refs(cosignataires_bloc)

    identifiant = amendement.get("identifiant") or {}
    sort_bloc = amendement.get("sort") or {}
    sort, base_juridique = _derive_amendement_sort_legacy(
        amendement.get("etat"), sort_bloc.get("sortEnSeance")
    )

    record_base = {
        # Identifiant AN, present aussi dans le schema legacy (ex.
        # "AMANR5L14SEA644420B0013P0D1N7") : verifie sur l'archive XIV du
        # 18/08/2026, 167 420 amendements pour 167 420 uid distincts — mais
        # seulement 22 159 `numeroLong` distincts. Meme cle que le schema
        # moderne, voir `_parse_amendement_entry`.
        "uid": amendement.get("uid"),
        "texte_vise": _texte_an(texte_ref),
        "sort": sort,
        "base_juridique_irrecevabilite": base_juridique,
        "premier_signataire": f"an:{acteur_ref}",
        "co_signataires": [f"an:{ref}" for ref in cosign_refs if isinstance(ref, str)],
        "type_deposant": _AMENDEMENT_TYPE_AUTEUR_MAP.get(auteur.get("typeAuteur")),
        "date": _texte_an(amendement.get("dateDepot")),
        # `numeroLong` (ex. "7 (Rect)") est à la racine de l'amendement, pas
        # imbriqué sous `identifiant` (qui ne porte que le numéro nu "7" —
        # vérifié sur l'archive réelle le 15/08/2026 : lire depuis
        # `identifiant` ici perdait silencieusement le suffixe de
        # rectification sur tout amendement rectifié).
        "numero": _texte_an(amendement.get("numeroLong")) or _texte_an(identifiant.get("numero")),
        "source_url": None,
    }

    out: list[tuple[str, dict[str, Any]]] = [
        (acteur_ref, {**record_base, "role_signataire": "auteur_principal"})
    ]
    for cosign_ref in cosign_refs:
        if not isinstance(cosign_ref, str) or not cosign_ref or cosign_ref == acteur_ref:
            continue
        out.append((cosign_ref, {**record_base, "role_signataire": "cosignataire"}))

    return out


def _parse_amendement_entry_legacy(data: Any) -> Optional[list[tuple[str, dict[str, Any]]]]:
    """Variante de `_parse_amendement_entry` pour le schéma legacy de la 14e
    législature (clé racine `textesEtAmendements`, voir issue #299) : une
    seule entrée JSON regroupe tous les `texteleg`, chacun listant ses
    amendements (`texteleg[].amendements.amendement[]`), au lieu d'un fichier
    par amendement. Produit les mêmes clés de sortie que
    `_parse_amendement_entry`. Retourne `None` seulement si la clé racine
    `textesEtAmendements` elle-même est absente/mal formée ; une liste vide
    est un résultat légitime (aucun amendement exploitable dans l'entrée).
    """
    root = data.get("textesEtAmendements") if isinstance(data, dict) else None
    if not isinstance(root, dict):
        return None

    texteleg_bloc = root.get("texteleg")
    textelegs = texteleg_bloc if isinstance(texteleg_bloc, list) else [texteleg_bloc]

    out: list[tuple[str, dict[str, Any]]] = []
    for texteleg in textelegs:
        if not isinstance(texteleg, dict):
            continue
        texte_ref = texteleg.get("refTexteLegislatif")
        amendement_bloc = (texteleg.get("amendements") or {}).get("amendement")
        amendements = amendement_bloc if isinstance(amendement_bloc, list) else [amendement_bloc]

        for amendement in amendements:
            if not isinstance(amendement, dict):
                continue
            out.extend(_parse_amendement_legacy_single(amendement, texte_ref))

    return out


def _amendements_zip_url(legislature: str) -> Optional[str]:
    entry = AN_AMENDEMENTS_PATH.get(legislature)
    if not entry:
        return None
    path_segment, zip_name = entry
    return f"{AN_OPENDATA_BASE}/{legislature}/loi/{path_segment}/{zip_name}"


class AmendementsIndexError(Exception):
    """Levée quand la construction de l'index amendements échoue (téléchargement ou
    parsing de l'archive AN). Distincte d'un index vide légitime (pas de dataset
    pour cette législature) : ne doit jamais être avalée silencieusement, pour que
    `fetch_amendements_officiels` (et le warning meta.warnings à l'appel) reflète
    l'échec au lieu d'un simple "aucun amendement"."""


#: Exceptions qui disent « la source n'a pas répondu » — les SEULES qu'une étape
#: de collecte a le droit de convertir en indisponibilité de source (#562).
#: `requests.RequestException` et `TimeoutError` dérivent déjà d'`OSError`, mais
#: sont nommées : cette liste est un contrat de lecture, pas une optimisation.
ERREURS_SOURCE: tuple[type[BaseException], ...] = (
    AmendementsIndexError,
    OSError,
    TimeoutError,
    zipfile.BadZipFile,
    json.JSONDecodeError,
    requests.RequestException,
)


def _tracer_echec_collecte(
    warnings: list[str],
    exc: BaseException,
    *,
    liste: str,
    etape: str,
    prefixe_panne: str,
) -> None:
    """Trace l'échec d'une étape de collecte **en disant de qui est la faute**.

    Avant #562, chaque étape de `build_profile` était encadrée d'un
    `except Exception` nu dont la branche unique écrivait « <source>
    indisponible : <exception> ». Deux faits sans rapport y étaient confondus :

    - la SOURCE n'a pas répondu (réseau, archive absente, ZIP corrompu) — un
      fait sur l'Assemblée nationale, que `couverture_profil` publie en
      `non_collecte`/`panne` ;
    - NOTRE code a échoué — un fait sur ce dépôt, qui n'autorise à rien dire de
      la source.

    Coût mesuré de la confusion : un `TypeError` du dépôt (tri d'amendements sur
    une date `xsi:nil`, voir `_texte_an`) a privé **99 profils publiés sur 481**
    de tous leurs amendements, sous une preuve de couverture qui accusait l'AN
    d'une panne — et qui n'était que le texte de l'exception.

    Les deux branches restent distinguées ici, et une seule fois : le préfixe de
    panne ne peut plus être écrit sur un défaut interne, et le message de défaut
    interne n'est mappé vers aucune panne (`couverture_profil.MOTIFS_PANNE`).
    Le détail technique reste dans `meta.warnings` et sur la sortie d'erreur du
    run — jamais dans une `preuve` publiée (`schema_pivot.valider_couverture`).
    """
    # #642 : les deux branches sont internes, et pour deux raisons distinctes.
    # La panne porte le texte brut de l'exception ; le défaut de collecte
    # accuse notre code. Ni l'un ni l'autre ne se lit sur une page publique, et
    # `couverture` dit déjà au lecteur, avec sa preuve, ce que la liste vaut.
    if isinstance(exc, ERREURS_SOURCE):
        warnings.append(avertissement(f"{prefixe_panne} : {exc}", DESTINATAIRE_INTERNE))
        return
    traceback.print_exc()
    warnings.append(avertissement(
        f"{WARNING_PREFIX_DEFAUT_COLLECTE} ({liste}) : {etape} a échoué sur une "
        f"anomalie de ce dépôt ({type(exc).__name__}) — aucune source de "
        "l'Assemblée nationale n'est en cause. Trace complète au journal de run.",
        DESTINATAIRE_INTERNE,
    ))


def _content_range_total(resp: "requests.Response") -> Optional[int]:
    """Extrait la taille totale de la ressource depuis l'en-tête `Content-Range`
    d'une réponse HTTP 206 (ex. "bytes 100000000-101048575/363306362" -> 363306362).
    Retourne `None` si l'en-tête est absent ou mal formé."""
    content_range = resp.headers.get("Content-Range")
    if not content_range or "/" not in content_range:
        return None
    try:
        return int(content_range.rsplit("/", 1)[-1])
    except ValueError:
        return None


def _probe_amendements_total_size(url: str) -> Optional[int]:
    """Sonde légère (HEAD) pour connaître la taille totale de l'archive avant de
    décider de reprendre un téléchargement partiel préexistant. Best-effort :
    toute erreur réseau ou en-tête `Content-Length` absent/invalide retourne
    `None`, auquel cas l'appelant de `_download_amendements_zip` ne prend pas
    le risque de reprendre un fichier partiel et redémarre proprement depuis
    le début plutôt que de deviner."""
    try:
        resp = requests.head(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        content_length = resp.headers.get("Content-Length")
        return int(content_length) if content_length is not None else None
    except (requests.RequestException, TypeError, ValueError):
        return None


class SourceAmendementsIndisponibleError(OSError):
    """Levée quand la source AN ne délivre plus **aucun octet nouveau**, par
    aucun des deux modes de transfert (plages `Range` et GET séquentiel) — #443.

    Distincte d'un échec de téléchargement, et le mot compte : la personne qui
    lit le log n'en fait pas la même chose. « Téléchargement en échec » invite à
    relancer ; or dans cet état relancer ne change rien, aucun repli réseau ne
    fonctionne. Seule l'attente fonctionne, ou le recours à un index déjà figé.

    Sous-classe d'`OSError` pour rester attrapée par les appelants existants
    (`except (requests.RequestException, OSError)`), qui n'ont donc pas à
    connaître ce type pour rester corrects.
    """


class SourceAmendementsIncoherenteError(OSError):
    """Levée quand la source sert durablement plusieurs versions de la même URL
    et qu'aucun téléchargement complet n'a pu être obtenu d'une seule d'entre
    elles — #1050.

    Distincte de `SourceAmendementsIndisponibleError`, et le mot compte comme
    en #443 : ici la source délivre parfaitement, elle est seulement
    incohérente avec elle-même. Relancer peut réussir — c'est un tirage — mais
    le log doit dire que ce n'est pas le réseau qui a flanché, sans quoi la
    personne qui le lit cherchera une panne qui n'existe pas.
    """


class ArchiveAmendementsChangeeError(OSError):
    """Levée quand la version servie n'est plus celle du préfixe déjà écrit —
    #1050.

    Ce n'est ni un échec de téléchargement ni une source indisponible : les
    octets arrivent normalement, ils appartiennent simplement à une autre
    archive. Les recoller produirait un fichier de la taille annoncée et
    illisible, ce qui est le pire des trois états — une corruption qu'aucune
    garde de taille ne voit. L'appelant redémarre donc depuis zéro plutôt que
    d'écrire quoi que ce soit.

    Sous-classe d'`OSError` pour rester attrapée par les appelants existants
    (`except (requests.RequestException, OSError)`), qui n'ont pas à connaître
    ce type pour rester corrects.
    """


def _identite_archive(resp: "requests.Response") -> Optional[str]:
    """Identité de la version servie : l'`ETag` si le serveur en rend une,
    sinon `Last-Modified`. `None` si le serveur ne rend ni l'une ni l'autre —
    auquel cas aucun contrôle de cohérence n'est possible et rien n'est
    supposé.

    Les deux en-têtes sont rendus par `data.assemblee-nationale.fr` (vérifié le
    21/09/2026), et `ETag` est préféré parce qu'il distingue deux versions
    publiées dans la même seconde, ce que `Last-Modified` ne fait pas."""
    for entete in ("ETag", "Last-Modified"):
        valeur = (resp.headers.get(entete) or "").strip()
        if valeur:
            return valeur
    return None


class _ResultatFlux(NamedTuple):
    """Issue d'une tentative de transfert.

    `octets_ecrits` prime sur `erreur` : un flux coupé en cours de route laisse
    malgré tout sur disque un préfixe valide du même fichier, qu'il ne faut
    jamais jeter (#443).

    `identite` porte l'`ETag` (ou le `Last-Modified`) de la réponse : c'est ce
    qui permet à l'appelant de savoir de QUELLE version viennent les octets
    reçus, et donc de refuser d'en recoller deux (#1050).
    """

    octets_ecrits: int
    status_code: Optional[int]
    total_distant: Optional[int]
    erreur: Optional[Exception]
    identite: Optional[str] = None


def _content_length_total(resp: "requests.Response") -> Optional[int]:
    """Taille totale annoncée par `Content-Length` sur une réponse HTTP 200.
    `None` si l'en-tête est absent ou illisible — jamais de valeur devinée."""
    try:
        return int(resp.headers.get("Content-Length"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _telecharger_flux(
    url: str, headers: dict[str, str], dest: Path, mode: str,
    identite_attendue: Optional[str] = None,
    session: Optional["requests.Session"] = None,
) -> _ResultatFlux:
    """Écrit le corps de la réponse dans `dest` **au fil de l'eau**, et rend ce
    qui a réellement été écrit — y compris quand le flux se coupe en cours.

    C'est le correctif central de #443. Le code d'origine faisait
    `b"".join(resp.iter_content(...))` : tout le segment était matérialisé avant
    d'être écrit, si bien qu'une coupure en cours propageait l'exception depuis
    `iter_content` et que l'intégralité des octets déjà reçus était perdue, le
    segment étant relancé depuis son offset de départ. Sous un mode de
    défaillance où la coupure tombe à un point aléatoire — le cas réel sur ces
    archives — cela annulait l'essentiel de ce qui arrivait.

    La lecture se fait sur `resp.raw` et non via `resp.iter_content()`, pour la
    même raison. Mesuré le 19/08/2026 sur un corps tronqué à 40 000 octets pour
    100 000 annoncés : `iter_content(chunk_size=N)` rend 0 octet dès que
    N >= 64 Kio et 39 936 octets pour N = 1 Kio, tandis que `raw.read()` rend
    les 40 000. En cause, le tampon de décodage d'urllib3 : `read(amt,
    decode_content=True)` accumule jusqu'à `amt` octets avant de rendre, et
    `_raw_read` lève `IncompleteRead` sur la lecture *suivante* — celle qui rend
    zéro octet — ce qui jette le tampon partiel. `raw.read(amt,
    decode_content=False)` rend au contraire chaque lecture courte telle quelle.
    Le corps devant donc rester non décodé, la requête demande explicitement
    `Accept-Encoding: identity` et un `Content-Encoding` autre est refusé
    bruyamment plutôt qu'écrit tel quel (une archive silencieusement compressée
    serait indétectable jusqu'au parsing).

    `identite_attendue` (#1050) fait refuser le corps — sans écrire un seul
    octet — quand la réponse porte une autre version que celle du préfixe déjà
    obtenu. Le contrôle a lieu AVANT l'ouverture du fichier : une fois les
    octets écrits, plus rien ne distingue les deux versions.

    `session` sert à enchaîner tous les segments sur la MÊME connexion. Ce
    n'est pas une optimisation : la source répartit les requêtes entre deux
    backends qui ne portent pas la même archive, et l'affinité de connexion est
    ce qui rend le cas d'incohérence rare plutôt que majoritaire (mesuré le
    21/09/2026 : 7 plages sur une connexion keep-alive rendent la même `ETag`,
    là où 10 requêtes séparées en rendent deux différentes).

    Ne lève pas : l'exception rencontrée est rendue à l'appelant avec le nombre
    d'octets écrits, pour qu'il reprenne à l'octet réellement obtenu et non au
    début du segment.
    """
    octets = 0
    status_code: Optional[int] = None
    total_distant: Optional[int] = None
    erreur: Optional[Exception] = None
    identite: Optional[str] = None
    headers = {**headers, "Accept-Encoding": "identity"}
    try:
        with (session or requests).get(
            url, headers=headers,
            timeout=(TIMEOUT, AMENDEMENTS_DOWNLOAD_READ_TIMEOUT_SECONDS),
            stream=True,
        ) as resp:
            resp.raise_for_status()
            status_code = resp.status_code
            identite = _identite_archive(resp)
            total_distant = (
                _content_range_total(resp) if status_code == 206 else _content_length_total(resp)
            )
            if (
                identite_attendue is not None
                and identite is not None
                and identite != identite_attendue
            ):
                # Rien n'est écrit : ces octets appartiennent à une autre
                # archive que le préfixe déjà sur disque.
                raise ArchiveAmendementsChangeeError(
                    f"version distante changée en cours de téléchargement "
                    f"(attendue {identite_attendue}, servie {identite})"
                )
            if status_code == 200 and mode == "ab":
                # Le serveur a ignoré l'en-tête Range alors qu'une reprise à un
                # offset non nul était attendue : écrire ce flux à la suite
                # dupliquerait le début du fichier. On rend la main sans rien
                # écrire, l'appelant décide (et lève).
                return _ResultatFlux(0, status_code, total_distant, None, identite)
            encodage = (resp.headers.get("Content-Encoding") or "identity").strip().lower()
            if encodage != "identity":
                raise OSError(
                    f"corps compressé ({encodage}) alors que `Accept-Encoding: identity` "
                    "a été demandé : écriture annulée pour ne pas déposer des octets "
                    "compressés dans l'archive"
                )
            with open(dest, mode) as out:
                while True:
                    morceau = resp.raw.read(
                        AMENDEMENTS_DOWNLOAD_READ_BUFFER_BYTES, decode_content=False
                    )
                    if not morceau:
                        break
                    out.write(morceau)
                    octets += len(morceau)
    except (requests.RequestException, urllib3.exceptions.HTTPError, OSError) as exc:
        erreur = exc
    return _ResultatFlux(octets, status_code, total_distant, erreur, identite)


def _est_erreur_http_definitive(exc: Optional[Exception]) -> bool:
    """Vrai pour une réponse HTTP qui ne changera pas en réessayant : 4xx hors
    408/429 (URL fausse, ressource retirée, accès refusé, plage invalide).

    Sert à ne pas confondre ce cas avec une source indisponible. Les deux ne
    rendent aucun octet, mais annoncer « la source est indisponible » sur un 404
    enverrait la personne qui lit le log attendre un rétablissement qui
    n'arrivera jamais — exactement la confusion que #443 cherche à supprimer.
    """
    reponse = getattr(exc, "response", None)
    code = getattr(reponse, "status_code", None)
    return isinstance(code, int) and 400 <= code < 500 and code not in (408, 429)


class _ResultatSegments(NamedTuple):
    """Issue d'un cycle de segments `Range`, rendue à `_download_amendements_zip`.

    `identite` est celle de la version réellement servie : l'appelant s'en sert
    pour épingler la version au premier segment, puis la redemande à chaque
    segment suivant via `If-Range` (#1050).
    """

    gagne: int
    total: Optional[int]
    tentatives: int
    derniere_erreur: Optional[Exception]
    fichier_entier: bool
    identite: Optional[str] = None


def _tenter_segments_range(
    url: str, zip_path: Path, legislature: str, offset: int, chunk_bytes: int,
    max_attempts: int, identite_attendue: Optional[str] = None,
    session: Optional["requests.Session"] = None,
) -> _ResultatSegments:
    """Un segment par plage `Range` à partir de `offset`, retenté jusqu'à
    `max_attempts` fois.

    `identite_attendue` est envoyée en `If-Range` et vérifiée sur la réponse
    (#1050). Les deux gardes sont complémentaires et aucune ne remplace
    l'autre : `If-Range` fait répondre le serveur 200 + fichier entier quand le
    validateur ne correspond plus — vérifié le 21/09/2026 sur la source réelle
    — mais un backend qui ne connaît pas notre `ETag` répond de même, et seule
    la comparaison de l'`ETag` rendue dit laquelle des deux versions on a sous
    la main.

    Ne lève **pas** sur épuisement des tentatives : rendre 0 octet est
    précisément le signal qui fait basculer l'appelant sur le mode suivant —
    dans les fenêtres où le `Range` est mort, insister sur la taille de segment
    ne sert à rien (8 Kio échouent autant que 32 Mio, mesuré le 18/08/2026).
    Lève en revanche `ArchiveAmendementsChangeeError` dès qu'une autre version
    est servie : réessayer le même segment ne ferait que retomber au hasard sur
    l'un ou l'autre backend, la décision appartient à l'appelant.
    """
    gagne = 0
    total: Optional[int] = None
    derniere_erreur: Optional[Exception] = None
    tentatives = 0
    fichier_entier = False
    identite = identite_attendue
    for tentative in range(1, max_attempts + 1):
        tentatives = tentative
        debut = offset + gagne
        # `chunk_bytes = 0` demande une plage SANS BORNE : on ne plafonne pas ce
        # qu'une reponse chanceuse delivre. La source coupe de toute facon
        # chaque reponse, et `_telecharger_flux` ecrit au fil de l'eau — une
        # plage ouverte tronquee se traite exactement comme un segment tronque.
        fin = debut + chunk_bytes - 1 if chunk_bytes else ""
        entetes = {**HEADERS, "Range": f"bytes={debut}-{fin}"}
        if identite_attendue is not None:
            entetes["If-Range"] = identite_attendue
        res = _telecharger_flux(
            url, entetes, zip_path, "wb" if debut == 0 else "ab",
            identite_attendue=identite_attendue, session=session,
        )
        if res.identite is not None:
            identite = res.identite
        if isinstance(res.erreur, ArchiveAmendementsChangeeError):
            raise res.erreur
        if res.total_distant is not None:
            # Renseigné même quand le corps est vide : dans l'état où le CDN
            # annonce un 206 correct puis ne délivre rien, l'en-tête reste la
            # seule source fiable de la taille totale.
            total = res.total_distant
        if res.status_code == 200 and debut != 0:
            if identite_attendue is not None:
                # `If-Range` a été envoyée et le serveur a refusé la plage : le
                # validateur ne correspond plus, donc l'archive distante n'est
                # plus celle du préfixe. Rien n'a été écrit (`_telecharger_flux`
                # rend la main sur un 200 en mode "ab"), l'appelant redémarre.
                raise ArchiveAmendementsChangeeError(
                    f"plage refusée à l'offset {debut} pour la législature {legislature} "
                    f"(If-Range {identite_attendue} périmée, version servie "
                    f"{res.identite or 'inconnue'})"
                )
            raise OSError(
                f"réponse HTTP 200 inattendue (en-tête Range ignoré) pour le segment "
                f"amendements législature {legislature} à l'offset {debut} : écriture "
                "annulée pour ne pas corrompre l'archive déjà partiellement écrite"
            )
        gagne += res.octets_ecrits
        if res.erreur is None:
            derniere_erreur = None
            # Réponse 200 achevée sans erreur : le serveur a ignoré l'en-tête
            # Range et rendu le fichier entier. Le flux s'est terminé
            # proprement, ce n'est donc pas une supposition — un corps tronqué
            # aurait levé et laissé `erreur` renseignée.
            fichier_entier = res.status_code == 200
            break
        derniere_erreur = res.erreur
        if tentative < max_attempts:
            recu = (
                f" ({res.octets_ecrits} octets reçus et conservés)" if res.octets_ecrits else ""
            )
            print(
                f"  [!] Échec du téléchargement du segment amendements législature "
                f"{legislature} (offset {debut}, tentative "
                f"{tentative}/{max_attempts}) : {res.erreur}{recu} — nouvel essai du segment seul"
            )
            time.sleep(AMENDEMENTS_DOWNLOAD_BACKOFF_SECONDS)
    return _ResultatSegments(gagne, total, tentatives, derniere_erreur, fichier_entier, identite)


def _tenter_get_sequentiel(
    url: str, zip_path: Path, legislature: str, prefixe_courant: int,
    session: Optional["requests.Session"] = None,
) -> tuple[int, Optional[int], bool, Optional[str]]:
    """Repli GET séquentiel (sans en-tête `Range`), conservé comme préfixe.

    Retourne `(taille_du_préfixe_retenu, total_distant, flux_acheve,
    identite)`, l'avant-dernier drapeau indiquant un flux terminé sans erreur —
    donc un fichier complet, et non un préfixe de plus — et le dernier la
    version servie, que l'appelant épingle pour les segments suivants (#1050).

    Le flux est écrit dans un fichier voisin `.seq`, adopté **seulement s'il est
    plus long** que le préfixe déjà détenu. C'est l'application du principe de
    #241 au flux plutôt qu'au segment : un `Range` partiel, un GET séquentiel
    interrompu et une reprise réussie produisent tous des préfixes du *même*
    fichier, le plus long doit gagner quelle que soit sa provenance. Adopter le
    fichier entier plutôt que d'en recoller la fin sur le préfixe existant évite
    par construction tout risque de raccord entre deux versions distinctes de
    l'archive distante.

    Ce repli redémarre à l'octet 0 : quand le `Range` est mort, aucune reprise
    n'est possible, donc son utilité décroît à mesure que le préfixe grandit.
    C'est la raison de fond pour laquelle l'état 3 (les deux modes morts) reste
    sans remède réseau sur une archive de plusieurs centaines de Mo.
    """
    seq_path = zip_path.with_name(zip_path.name + ".seq")
    try:
        res = _telecharger_flux(url, dict(HEADERS), seq_path, "wb", session=session)
        obtenu = res.octets_ecrits
        if res.erreur is not None:
            print(
                f"  [!] Législature {legislature} : GET séquentiel interrompu après "
                f"{obtenu} octets ({res.erreur})"
            )
        if obtenu > prefixe_courant:
            os.replace(seq_path, zip_path)
            print(
                f"  -> Législature {legislature} : préfixe séquentiel de {obtenu} octets "
                f"retenu (plus long que les {prefixe_courant} octets déjà obtenus)"
            )
            return obtenu, res.total_distant, res.erreur is None, res.identite
        if obtenu:
            print(
                f"  -> Législature {legislature} : préfixe séquentiel de {obtenu} octets "
                f"écarté (le préfixe déjà obtenu, {prefixe_courant} octets, est plus long)"
            )
        return prefixe_courant, res.total_distant, False, None
    finally:
        try:
            seq_path.unlink(missing_ok=True)
        except OSError:
            pass  # best-effort, comme le reste du nettoyage de cache


def _download_amendements_zip(
    url: str, zip_path: Path, legislature: str, chunk_bytes: Optional[int] = None,
    max_attempts: Optional[int] = None, stall_max_cycles: Optional[int] = None,
    stall_wait_seconds: Optional[int] = None, budget_secondes: Optional[float] = None,
) -> None:
    """Télécharge l'archive zip des amendements en arbitrant **à l'exécution**
    entre deux modes de transfert, sans jamais jeter un préfixe valide.

    `data.assemblee-nationale.fr` ne tombe pas en panne : il change de mode de
    défaillance, et assez vite pour qu'une mesure de quelques minutes induise en
    erreur (relevé du 18/08/2026, confirmé le 19/08). Trois états observés, qui
    appellent trois réponses différentes — d'où un arbitrage en cours de
    téléchargement plutôt qu'un réglage par configuration :

    1. `Range` fonctionne -> reprise par segments, le mode nominal (#241).
    2. `Range` ne rend rien quelle que soit la taille de segment -> repli sur un
       GET séquentiel, dont le résultat est conservé comme préfixe.
    3. `Range` mort **et** GET séquentiel coupé à quelques dizaines de Mo ->
       aucun repli réseau ne fonctionne : on attend entre deux cycles au lieu de
       marteler la source, puis on échoue en disant que la **source est
       indisponible** (`SourceAmendementsIndisponibleError`), pas que le
       téléchargement a échoué.
    4. La source sert **deux versions de la même URL** selon le backend qui
       répond (#1050) -> tous les segments passent par une seule connexion, et
       chacun redemande explicitement la version du préfixe (`If-Range` +
       contrôle de l'`ETag` rendue). Une version qui change fait redémarrer le
       téléchargement depuis zéro, jamais recoller ; au-delà de
       `AMENDEMENTS_DOWNLOAD_MAX_REDEMARRAGES_VERSION`, on échoue en disant que
       la **source est incohérente** (`SourceAmendementsIncoherenteError`).
       C'est le seul des quatre états qui ne se voit pas à la taille finale :
       le fichier recollé fait exactement le nombre d'octets annoncé.

    Le serveur annonce `Accept-Ranges: bytes` et un `Content-Length` correct
    dans les trois états : aucune sonde `HEAD` ne permet de les distinguer, seul
    le transfert lui-même le peut. L'arbitrage porte de plus sur le décalage
    courant et non sur le fichier : mesuré le 19/08/2026, une plage à l'octet 0
    ou à 4 Mio est servie normalement pendant que la même plage à 64 Mio ne rend
    rien — sonder le `Range` en tête de fichier conclurait donc à tort qu'il
    fonctionne.

    Principe directeur, valable pour les trois modes : **ne jamais jeter un
    préfixe valide, d'où qu'il vienne.** Les octets reçus sont écrits au fil de
    l'eau (`_telecharger_flux`), une coupure en cours de segment reprend à
    l'octet réellement obtenu, et un préfixe séquentiel ne remplace l'existant
    que s'il est plus long (`_tenter_get_sequentiel`).

    Reprend aussi un téléchargement interrompu **entre deux invocations** du
    script : si `zip_path` existe déjà non vide, `_probe_amendements_total_size`
    détermine la taille distante avant de décider — fichier déjà complet ->
    aucune requête ; fichier partiel -> reprise en mode ajout ; sonde en échec
    ou taille locale incohérente -> redémarrage depuis le début plutôt que de
    deviner un offset.

    **`chunk_bytes = 0` demande une plage SANS BORNE** (`bytes=<offset>-`), et
    c'est ce que les archives figées passent depuis #1123. Ce n'est pas en
    contradiction avec ce qui précède : l'observation « 8 Kio échouent autant
    que 32 Mio » porte sur les ÉCHECS, celle-ci sur le rendement quand ça
    passe. Mesuré le 24/09/2026 sur la XVe depuis un poste, la même plage rend
    0 ou 211 Mo selon la tentative — un segment borné tronque donc le bon cas,
    et chaque segment suivant est un nouveau tirage qui peut rendre zéro. Sur
    46 plages ouvertes : 12,6 Mo par tentative, et l'archive entière en 352
    tentatives dont 6 productives, quand la CI en segments bornés plafonnait à
    35 Mo en 1 300 s.

    `chunk_bytes` / `max_attempts` (défauts `AMENDEMENTS_DOWNLOAD_CHUNK_BYTES`,
    32 Mo, et `AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS`, 3) restent réglables pour ne
    pas toucher au chemin réseau partagé de la législature 17, qui garde le
    segment borné : son archive n'a jamais posé ce problème, et lui changer sa
    forme de requête sans mesure serait un pari. `stall_max_cycles` / `stall_wait_seconds` (défauts
    `AMENDEMENTS_SOURCE_STALL_MAX_CYCLES` / `_WAIT_SECONDS`) bornent l'attente de
    l'état 3, volontairement courte en CI et augmentable hors CI, où attendre est
    le seul remède qui fonctionne.

    **`budget_secondes` borne l'état 3 EN TEMPS, et remplace alors le compte de
    cycles** (#1100). La source ne tombe pas : elle coupe par intermittence.
    Mesuré le 22/09/2026 sur la plage qui avait fait échouer le run
    `35767700159` (offset 12 224 778, 4 194 192 octets) : 722 945 octets à la
    première tentative, 2 892 049 à la deuxième, **la plage entière à la
    troisième**. En CI, trois cycles de trois tentatives ont abandonné en
    5 minutes sur un job qui en a 30 — 25 minutes inutilisées. Tant qu'il reste
    du budget, on réessaie ; épuisé, on déclare la source indisponible pour ce
    run, sans rien inventer (§2 règle 5). Même principe que le budget réseau du
    portail européen (#1064) : en temps, parce que c'est le job qui est borné en
    temps.

    Lève `SourceAmendementsIndisponibleError` (sous-classe d'`OSError`) quand
    plus aucun octet nouveau n'est obtenu, ou `OSError` si la taille finale ne
    correspond pas à la taille annoncée — jamais d'archive tronquée rendue
    silencieusement pour complète.
    """
    # `or` ecraserait 0, qui est une valeur demandee (plage sans borne) et non
    # une absence : la distinction se fait sur None.
    chunk_bytes = AMENDEMENTS_DOWNLOAD_CHUNK_BYTES if chunk_bytes is None else chunk_bytes
    max_attempts = max_attempts or AMENDEMENTS_DOWNLOAD_MAX_ATTEMPTS
    stall_max_cycles = stall_max_cycles or AMENDEMENTS_SOURCE_STALL_MAX_CYCLES
    stall_wait_seconds = (
        AMENDEMENTS_SOURCE_STALL_WAIT_SECONDS if stall_wait_seconds is None else stall_wait_seconds
    )
    zip_path.parent.mkdir(parents=True, exist_ok=True)

    offset = 0
    total_size: Optional[int] = None

    existing_size = zip_path.stat().st_size if zip_path.is_file() else 0
    if existing_size > 0:
        remote_total_size = _probe_amendements_total_size(url)
        if remote_total_size is None:
            print(
                f"  -> Législature {legislature} : impossible de sonder la taille distante, "
                "redémarrage du téléchargement depuis le début (fichier partiel existant ignoré)."
            )
        elif existing_size == remote_total_size:
            print(
                f"  -> Législature {legislature} : archive déjà complète en local "
                f"({existing_size} octets), téléchargement sauté."
            )
            return
        elif existing_size > remote_total_size:
            print(
                f"  -> Législature {legislature} : fichier local ({existing_size} octets) plus "
                f"gros que l'archive distante ({remote_total_size} octets), incohérent — "
                "redémarrage du téléchargement depuis le début."
            )
        else:
            offset = existing_size
            total_size = remote_total_size
            print(
                f"  -> Législature {legislature} : reprise du téléchargement à partir de "
                f"l'octet {offset}/{total_size} (tentative précédente interrompue)."
            )

    segments_total = 0
    segments_retried = 0
    cycles_sans_progres = 0
    depart = time.monotonic()
    identite_archive: Optional[str] = None
    redemarrages_version = 0

    # Tous les segments sur la MÊME connexion : la source répartit les requêtes
    # entre deux backends qui ne portent pas la même archive, et l'affinité de
    # connexion est ce qui rend l'incohérence rare au lieu de majoritaire
    # (#1050). La garde `If-Range` reste nécessaire : une connexion peut être
    # rouverte à tout moment, par le serveur comme par un retry.
    session = requests.Session()
    try:
        while total_size is None or offset < total_size:
            offset_debut_cycle = offset

            # --- Mode 1 : reprise par segments (HTTP Range) ---
            segments_total += 1
            try:
                res_segments = _tenter_segments_range(
                    url, zip_path, legislature, offset, chunk_bytes, max_attempts,
                    identite_attendue=identite_archive, session=session,
                )
            except ArchiveAmendementsChangeeError as exc:
                redemarrages_version += 1
                if redemarrages_version > AMENDEMENTS_DOWNLOAD_MAX_REDEMARRAGES_VERSION:
                    raise SourceAmendementsIncoherenteError(
                        f"source data.assemblee-nationale.fr incohérente pour l'archive "
                        f"amendements législature {legislature} : la version servie a changé "
                        f"{redemarrages_version} fois en cours de téléchargement ({exc}). "
                        "Ce n'est pas un échec de transfert à relancer : la source publie "
                        "plusieurs versions de la même URL, et un préfixe déjà obtenu ne peut "
                        "pas être complété tant que c'est le cas."
                    ) from exc
                print(
                    f"  [!] Législature {legislature} : {exc} — redémarrage du téléchargement "
                    f"depuis le début (tentative {redemarrages_version}/"
                    f"{AMENDEMENTS_DOWNLOAD_MAX_REDEMARRAGES_VERSION}). Recoller deux versions "
                    "produirait une archive de la taille attendue et illisible."
                )
                # Le préfixe est jeté SCIEMMENT, à rebours du principe de #443 :
                # il est valide pour une archive qui n'est plus celle que la source
                # sert, donc il ne peut plus être complété.
                try:
                    zip_path.unlink(missing_ok=True)
                except OSError:
                    pass
                offset = 0
                total_size = None
                identite_archive = None
                session.close()
                session = requests.Session()
                continue
            gagne = res_segments.gagne
            total_annonce = res_segments.total
            tentatives = res_segments.tentatives
            derniere_erreur = res_segments.derniere_erreur
            fichier_entier = res_segments.fichier_entier
            if identite_archive is None and res_segments.identite is not None:
                # Épinglée au premier segment servi : c'est la version dont le
                # préfixe sur disque provient, et celle que tous les segments
                # suivants devront porter.
                identite_archive = res_segments.identite
            if total_annonce is not None and total_size is None:
                total_size = total_annonce
            offset += gagne
            if gagne and tentatives > 1:
                segments_retried += 1
            if fichier_entier and total_size is None:
                # Fichier entier délivré et flux achevé proprement, sans
                # Content-Length exploitable : la taille obtenue *est* la taille
                # totale. Rien n'est deviné — un corps tronqué aurait levé.
                total_size = offset

            if gagne:
                if total_size:
                    percent = offset / total_size * 100
                    print(
                        f"  -> Législature {legislature} : {offset}/{total_size} octets "
                        f"({percent:.1f}%) — segment {segments_total} écrit"
                    )
                else:
                    print(
                        f"  -> Législature {legislature} : {offset} octets — segment "
                        f"{segments_total} écrit"
                    )
                cycles_sans_progres = 0
                continue

            if _est_erreur_http_definitive(derniere_erreur):
                # Ni un mode de transfert en cause, ni une source indisponible :
                # réessayer ou attendre ne changerait rien. Remonte tel quel.
                raise derniere_erreur  # type: ignore[misc]

            # --- Mode 2 : repli GET séquentiel, conservé comme préfixe ---
            # Atteint uniquement quand le `Range` n'a rien rendu du tout après
            # épuisement des tentatives : ni exception, ni corps vide (le CDN AN
            # répond alors 206 + Content-Range correct puis ne délivre rien).
            motif = f" ({derniere_erreur})" if derniere_erreur is not None else " (corps vide)"
            print(
                f"  [!] Législature {legislature} : plage à l'offset {offset} sans effet après "
                f"{max_attempts} tentative(s){motif} — repli sur un GET séquentiel"
            )
            offset, total_annonce, flux_acheve, identite_seq = _tenter_get_sequentiel(
                url, zip_path, legislature, offset, session=session,
            )
            if identite_seq is not None:
                # Le préfixe séquentiel REMPLACE le fichier : la version à
                # exiger des segments suivants est la sienne, pas celle qui
                # était épinglée avant (#1050).
                identite_archive = identite_seq
            if total_annonce is not None and total_size is None:
                total_size = total_annonce
            if flux_acheve and total_size is None:
                total_size = offset
            if offset > offset_debut_cycle:
                cycles_sans_progres = 0
                continue

            # --- Mode 3 : aucun des deux modes ne délivre quoi que ce soit ---
            cycles_sans_progres += 1
            ecoule = time.monotonic() - depart
            if budget_secondes is None:
                reste = None
                epuise = cycles_sans_progres >= stall_max_cycles
            else:
                reste = budget_secondes - ecoule
                epuise = reste <= 0
            if epuise:
                attendu = f" sur {total_size}" if total_size is not None else ""
                borne = (f"budget de {budget_secondes:.0f}s épuisé" if budget_secondes is not None
                         else f"{cycles_sans_progres} cycle(s) sans progrès")
                raise SourceAmendementsIndisponibleError(
                    f"archive amendements législature {legislature} : {offset} octet(s) obtenu(s)"
                    f"{attendu} en {ecoule:.0f}s, puis plus aucun octet nouveau ni par plages HTTP "
                    f"Range ni par GET séquentiel ({borne}). La source COUPE par intermittence, "
                    "elle ne répond pas « indisponible » : réessayer plus tard, avec un budget plus "
                    "large, ou utiliser un index figé déjà committé."
                )
            # L'attente ne dépasse jamais ce qui reste : sinon la dernière sieste
            # ferait dépasser le budget, et le job serait tué au lieu d'échouer.
            attente = stall_wait_seconds if reste is None else max(0, min(stall_wait_seconds, reste))
            reste_dit = "" if reste is None else f", {reste:.0f}s de budget restant"
            print(
                f"  [!] Législature {legislature} : aucun octet obtenu par aucun mode "
                f"(cycle {cycles_sans_progres}, {offset} octet(s) obtenu(s) en {ecoule:.0f}s"
                f"{reste_dit}) — la source coupe, attente de {attente:.0f}s avant un nouveau "
                "cycle (inutile de marteler : aucun repli réseau ne fonctionne dans cet état)"
            )
            time.sleep(attente)
    finally:
        session.close()

    if segments_retried >= AMENDEMENTS_SEGMENT_RETRY_WARNING_THRESHOLD:
        print(
            f"  [!] Législature {legislature} : {segments_retried}/{segments_total} segment(s) ont "
            "nécessité un retry — instabilité réseau notable sur cette archive"
        )
    elif segments_retried:
        print(f"  -> Législature {legislature} : {segments_retried}/{segments_total} segment(s) retenté(s) avec succès")

    final_size = zip_path.stat().st_size
    if total_size is not None and final_size != total_size:
        raise OSError(
            f"taille finale incohérente pour l'archive amendements législature {legislature} : "
            f"{final_size} octets écrits, {total_size} attendus"
        )


def _shard_path_acteur(legislature: str, acteur_ref: str) -> Optional[Path]:
    """Chemin de la tranche d'index d'UN acteur (#392).

    Retourne `None` si `acteur_ref` n'a pas la forme attendue d'un
    identifiant AN (`PA` suivi de chiffres) : le nom de fichier étant dérivé
    de cette valeur, on refuse tout ce qui pourrait sortir du répertoire de
    cache plutôt que d'assainir approximativement."""
    if not isinstance(acteur_ref, str) or not re.fullmatch(r"PA\d+", acteur_ref):
        return None
    return (
        AMENDEMENTS_CACHE_DIR
        / legislature
        / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
        / f"{acteur_ref}.json"
    )


def _read_cached_amendements_store(legislature: str) -> Optional[dict[str, dict[str, Any]]]:
    """Store dédupliqué `numero -> amendement` d'une législature, mémoïsé en
    mémoire process (#392).

    Cette mémoïsation-ci est sûre, contrairement à celle tentée puis revertée
    en #377 — la différence tient à ce qui est gardé résident. Mesuré sur le
    cache réel :
    - les 4 `index_par_acteur` complets résidents : **3,84 Go** (rejeté, c'est
      ce qui avait provoqué l'OOM) ;
    - les 4 `amendements.json` seuls résidents : **426 Mo** (retenu).

    Le store est petit parce qu'il est dédupliqué (89 Mo sur disque pour les 4
    législatures, ~178 000 amendements uniques) ; c'est `index_par_acteur` qui
    pèse (580 Mo), et lui n'est plus jamais chargé en entier depuis #392 —
    seule la tranche de l'acteur demandé est lue.

    Le cache disque n'est jamais réécrit pendant la vie d'un process de
    collecte (seul `build_amendements_index.py`, exécuté avant, le produit),
    donc mémoïser ne peut pas servir une version périmée."""
    with _get_amendements_lock(legislature):
        if legislature in _AMENDEMENTS_STORE_MEMO:
            return _AMENDEMENTS_STORE_MEMO[legislature]
        path = AMENDEMENTS_CACHE_DIR / legislature / AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME
        store: Optional[dict[str, dict[str, Any]]] = None
        if path.is_file():
            try:
                with open(path, encoding="utf-8") as f:
                    charge = json.load(f)
                if isinstance(charge, dict):
                    store = charge
            except (json.JSONDecodeError, OSError):
                store = None  # cache corrompu : traité comme absent
        _AMENDEMENTS_STORE_MEMO[legislature] = store
        return store


def _clear_amendements_store_memo() -> None:
    """Vide le mémo du store (tests uniquement : un process de collecte ne voit
    jamais le cache disque changer sous lui)."""
    _AMENDEMENTS_STORE_MEMO.clear()


def _read_cached_amendements_acteur(
    legislature: str, acteur_ref: str
) -> Optional[list[dict[str, Any]]]:
    """Amendements d'UN acteur pour une législature, résolus depuis le cache
    dédupliqué et **shardé par acteur** (#392). Retourne `None` si le cache
    est absent/illisible (l'appelant trace alors un warning), une liste
    éventuellement vide si l'acteur n'y figure pas.

    Coût : une tranche d'acteur (~285 Ko) au lieu des 673 Mo d'index complets
    que la version #377 relisait à chaque candidat — 93 % du temps
    d'extraction du roster y passait (mesuré en #376, ~10,9 s sur 11,7 s par
    membre, soit ~500 Go de JSON reparsé sur un run complet).

    Le store `amendements.json` est mémoïsé (voir
    `_read_cached_amendements_store`) : c'est lui qui rend la résolution des
    références possible sans relire quoi que ce soit après le premier appel."""
    store = _read_cached_amendements_store(legislature)
    if store is None:
        return None

    shard_path = _shard_path_acteur(legislature, acteur_ref)
    # Répertoire de tranches absent = cache hérité (#377, fichier unique) ou
    # jamais construit : indiscernables, et dans les deux cas il faut le
    # reconstruire plutôt que relire l'ancien format.
    index_dir = AMENDEMENTS_CACHE_DIR / legislature / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    if not index_dir.is_dir():
        return None
    if shard_path is None or not shard_path.is_file():
        # Acteur simplement absent de cette législature : liste vide, pas None
        # — distinguer « pas d'amendement » de « index indisponible » est ce
        # qui pilote le warning côté fetch_amendements_officiels.
        return []

    try:
        with open(shard_path, encoding="utf-8") as f:
            refs = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(refs, list):
        return None

    # Tranche héritée du format `{numero, role_signataire}` (avant la
    # correction du 18/08/2026) : traitée comme un cache absent, jamais relue.
    # Ses références résolvent vers un autre amendement que le leur dans 40,5 %
    # des cas — voir `_aggregate_amendements_index` et
    # docs/decisions/amendements-cle-uid.md.
    if not _index_par_acteur_au_format_uid({acteur_ref: refs}):
        return None

    entries: list[dict[str, Any]] = []
    for ref in refs:
        if not isinstance(ref, dict):
            continue
        base = store.get(ref.get("uid"))
        if base is None:
            continue
        entries.append({**base, "role_signataire": ref.get("role_signataire")})
    return entries


def _write_amendements_fraicheur(index_path: Path, reussi: bool) -> None:
    """Écrit (best-effort, comme l'index lui-même) le fichier d'indicateur de
    fraîcheur à côté de `index_par_acteur.json` : `derniere_construction_reussie`
    reflète l'issue de la tentative courante, `horodatage` son moment. N'est
    appelée en cas d'échec que lorsqu'un index existe déjà à préserver (issue
    #253) — pas d'indicateur de fraîcheur sans index à qualifier."""
    fraicheur_path = index_path.with_name(AMENDEMENTS_FRAICHEUR_FILENAME)
    try:
        with open(fraicheur_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "derniere_construction_reussie": reussi,
                    "horodatage": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                },
                f,
                ensure_ascii=False,
            )
    except OSError:
        pass


def amendements_index_deja_figee(legislature: str) -> bool:
    """True si le cache disque d'une législature figée
    (`AN_AMENDEMENTS_LEGISLATURES_FIGEES`) est déjà matérialisé
    (`amendements.json` + répertoire de tranches présents, `fraicheur.json`
    portant `figee: true`, et tranches au format `uid`), sans jamais charger
    l'index entier en mémoire pour le vérifier — seuls `fraicheur.json`
    (quelques dizaines d'octets) et UNE tranche d'acteur (~285 Ko) sont lus. Une législature
    figée ne change plus jamais une fois matérialisée : un appelant qui
    boucle sur plusieurs législatures (`build_amendements_index.py`) doit
    pouvoir sauter celles déjà figées sans recharger un index potentiellement
    volumineux (mesuré : 4,7 Go en clair pour la législature 16) juste pour
    confirmer sa présence — un run réel a déclenché l'OOM killer du système
    sur cette seule relecture, empêchant toute législature suivante d'être
    ne serait-ce que tentée (voir docs/technical_decisions.md
    #amendements-legislatures-figees)."""
    if legislature not in AN_AMENDEMENTS_LEGISLATURES_FIGEES:
        return False
    cache_dir = AMENDEMENTS_CACHE_DIR / legislature
    amendements_path = cache_dir / AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME
    index_dir = cache_dir / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    fraicheur_path = cache_dir / AMENDEMENTS_FRAICHEUR_FILENAME
    # `amendements.json` exigé aussi (#377), et le répertoire de tranches
    # depuis #392 : un cache écrit avant l'un ou l'autre de ces formats doit
    # être reconstruit, pas considéré comme déjà figé — sinon il resterait en
    # place indéfiniment sans jamais migrer.
    if not amendements_path.is_file() or not index_dir.is_dir() or not fraicheur_path.is_file():
        return False
    try:
        with open(fraicheur_path, encoding="utf-8") as f:
            fraicheur = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    if not (isinstance(fraicheur, dict) and fraicheur.get("figee")):
        return False

    # Et le format de l'index doit être celui de la clé `uid` (#447). Sans ce
    # contrôle, un cache figé écrit AVANT la correction du 18/08/2026
    # (références par `numero`) est déclaré « déjà matérialisé » et jamais
    # reconstruit par build_amendements_index.py, pendant que
    # `_read_cached_amendements_acteur` le REFUSE à la lecture — la législature
    # n'est alors ni reconstruite ni lue, et ses amendements disparaissent
    # entièrement, avec pour seul signe un warning soft « index en cache
    # absent ». Constaté sur le cache local du 19/08/2026 : les législatures
    # 14, 15 et 16 étaient simultanément `deja_figee=True` et illisibles.
    # Coût : l'ouverture d'UNE tranche (~285 Ko) — la contrainte qui a fait
    # naître cette fonction (ne jamais charger l'index entier, plusieurs Go en
    # clair, sous peine d'OOM) reste respectée.
    if not _cache_amendements_au_format_uid(sorted(index_dir.glob("*.json"))):
        print(
            f"  [!] Cache figé législature {legislature} au format hérité "
            "(références par 'numero') : non considéré comme figé, reconstruction requise.",
            file=sys.stderr,
        )
        return False
    return True


def _write_cached_amendements_agreges(
    legislature: str,
    amendements: dict[str, dict[str, Any]],
    index_par_acteur: dict[str, list[dict[str, Any]]],
) -> None:
    """Écrit (best-effort) le cache disque d'une législature sous forme
    dédupliquée : `amendements.json` + `index_par_acteur.json` (#377).

    Les deux fichiers sont écrits ensemble, `amendements.json` en premier :
    `_read_cached_amendements_agreges` exige les deux, donc une écriture
    interrompue entre les deux laisse un cache considéré comme absent
    (reconstruit au prochain run) plutôt qu'un couple incohérent. Écrase au
    passage un éventuel `index_par_acteur.json` plat hérité d'avant #377 —
    la migration d'un ancien cache est donc automatique et libère les
    plusieurs Go qu'il occupait."""
    cache_dir = AMENDEMENTS_CACHE_DIR / legislature
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_dir / AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME, "w", encoding="utf-8") as f:
        json.dump(amendements, f, ensure_ascii=False)

    # Une tranche par acteur (#392). Le répertoire est reconstruit de zéro :
    # un acteur disparu d'une reconstruction ne doit pas laisser sa tranche
    # périmée derrière lui. Écrit APRÈS amendements.json, et publié d'un seul
    # `os.replace` depuis un répertoire temporaire — une écriture interrompue
    # laisse donc un cache traité comme absent, jamais un cache incohérent.
    # C'est cette propriété, et elle seule, qui rend légitime le contrôle sur
    # une tranche unique de `_cache_amendements_au_format_uid`.
    index_dir = cache_dir / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    # Écrit dans un répertoire temporaire, puis basculé d'un seul `os.replace`
    # (#447). Remplir `index_par_acteur/` en place laissait, pendant toute la
    # boucle, un répertoire qui EXISTE et qui est INCOMPLET : le contrôle de
    # cache-hit de `_download_and_build_amendement_index` (`index_dir.is_dir()`)
    # l'accepte, donc il n'est jamais reconstruit, et chaque acteur dont la
    # tranche manque encore est lu comme « aucun amendement » (liste vide) au
    # lieu de « index indisponible » (None) — un zéro silencieux, exactement ce
    # que ce dépôt traite comme un défaut à part entière. Le cas est atteignable :
    # le step `Upload artifact amendements AN` de generate-data.yml est en
    # `if: always()`, donc un job interrompu publie l'état partiel du disque, que
    # les jobs consommateurs téléchargent ensuite.
    tmp_dir = cache_dir / f"{AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME}.partiel"
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for acteur_ref, refs in index_par_acteur.items():
        shard = _shard_path_acteur(legislature, acteur_ref)
        if shard is None:
            continue  # acteurRef hors forme attendue : ignoré plutôt qu'écrit
        with open(tmp_dir / shard.name, "w", encoding="utf-8") as f:
            json.dump(refs, f, ensure_ascii=False)
    shutil.rmtree(index_dir, ignore_errors=True)
    os.replace(tmp_dir, index_dir)
    # Ancien fichier unique hérité (#377) : supprimé une fois les tranches en
    # place, pour libérer les centaines de Mo qu'il occupait.
    (cache_dir / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_FILENAME_LEGACY).unlink(missing_ok=True)


def _load_frozen_amendement_index(legislature: str) -> Optional[dict[str, list[dict[str, Any]]]]:
    """Charge l'index amendements committé pour une législature figée
    (`AN_AMENDEMENTS_LEGISLATURES_FIGEES`), construit hors CI une fois pour
    toutes par `build_amendements_index_figees.py` sous forme dédupliquée et
    compressée gzip (`amendements.json.gz` + `index_par_acteur.json.gz`
    allégé, voir `_aggregate_amendements_index` — nécessaire pour rester sous
    la limite GitHub de 100 Mo par blob, voir la révision du 15/08/2026 de
    docs/decisions/amendements-legislatures-figees.md), et le
    matérialise dans le cache disque (`AMENDEMENTS_CACHE_DIR`) en clair, sous
    la MEME forme dédupliquée (`amendements.json` + `index_par_acteur.json`,
    seule la compression change) — depuis #377, plus aucune expansion vers la
    forme plate n'a lieu ici : c'est elle qui faisait passer la législature 16
    de 210 Mo à 4,67 Go et déclenchait l'OOM killer. `fraicheur.json` est
    copié tel quel avec son marqueur `figee: true`.

    Retourne l'index compact acteurRef -> références (`{numero,
    role_signataire}`), ou `None` si le fallback committé est absent ou
    incomplet (ne devrait pas arriver pour une législature figée, mais ne
    lève jamais : l'appelant retombe alors sur le chemin réseau standard)."""
    frozen_dir = AN_AMENDEMENTS_FIGEES_DIR / legislature
    frozen_amendements_path = frozen_dir / AMENDEMENTS_FIGEES_AMENDEMENTS_FILENAME
    frozen_index_path = frozen_dir / AMENDEMENTS_FIGEES_INDEX_PAR_ACTEUR_FILENAME
    if not frozen_amendements_path.is_file() or not frozen_index_path.is_file():
        return None
    try:
        with gzip.open(frozen_amendements_path, "rt", encoding="utf-8") as f:
            amendements = json.load(f)
        with gzip.open(frozen_index_path, "rt", encoding="utf-8") as f:
            index_par_acteur = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    # Index figé hérité (références par `numero`) : refusé plutôt que
    # matérialisé dans le cache. L'appelant retombe sur le chemin réseau, qui
    # reconstruit un index correct — mieux vaut re-télécharger une archive que
    # servir des amendements attribués au mauvais texte (voir
    # `_aggregate_amendements_index` et
    # docs/decisions/amendements-cle-uid.md).
    if not _index_par_acteur_au_format_uid(index_par_acteur):
        print(
            f"  [!] Index figé législature {legislature} au format hérité "
            "(références par 'numero') : ignoré, reconstruction requise "
            "(python src/build_amendements_index_figees.py --legislature "
            f"{legislature})",
            file=sys.stderr,
        )
        return None

    try:
        _write_cached_amendements_agreges(legislature, amendements, index_par_acteur)
        frozen_fraicheur_path = frozen_dir / AMENDEMENTS_FRAICHEUR_FILENAME
        if frozen_fraicheur_path.is_file():
            shutil.copyfile(
                frozen_fraicheur_path,
                AMENDEMENTS_CACHE_DIR / legislature / AMENDEMENTS_FRAICHEUR_FILENAME,
            )
    except OSError:
        pass

    return index_par_acteur


def _parse_amendements_zip(zip_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Parse une archive amendements AN déjà téléchargée en index acteurRef ->
    liste d'amendements (extrait de `_download_and_build_amendement_index`
    pour être réutilisable par `build_amendements_index_figees.py`, qui parse
    une archive téléchargée manuellement hors CI). Lève `zipfile.BadZipFile`
    si l'archive est invalide — laissé à l'appelant à traiter.

    Détecte le schéma de chaque entrée par sa clé racine : `"amendement"`
    (schéma 15/16/17, un amendement par entrée) ou `"textesEtAmendements"`
    (schéma legacy légis 14, une seule entrée regroupant tous les
    texteleg/amendements — voir issue #299). Un schéma ni l'un ni l'autre
    produit toujours un index vide pour cette entrée, mais avec un warning
    explicite au lieu d'un échec silencieux."""
    index: dict[str, list[dict[str, Any]]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        noms = [n for n in zf.namelist() if n.endswith(".json")]
        for nom in noms:
            try:
                with zf.open(nom) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, KeyError):
                continue

            if isinstance(data, dict) and "amendement" in data:
                parsed_entries = _parse_amendement_entry(data)
            elif isinstance(data, dict) and "textesEtAmendements" in data:
                parsed_entries = _parse_amendement_entry_legacy(data)
            else:
                print(
                    f"  [!] Entrée '{nom}' au format inconnu (ni 'amendement' ni "
                    "'textesEtAmendements'), ignorée",
                    file=sys.stderr,
                )
                continue

            if parsed_entries is None:
                continue
            for acteur_ref, record in parsed_entries:
                index.setdefault(acteur_ref, []).append(record)
    return index


def _aggregate_amendements_index(
    index: dict[str, list[dict[str, Any]]],
) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Compacte un index acteurRef -> amendements (format `_parse_amendements_zip`)
    pour le committer sans duplication, pour une législature figée
    (`build_amendements_index_figees.py`).

    `_parse_amendement_entry` construit un enregistrement par signataire
    (auteur + chaque cosignataire), chacun portant sa propre copie complète du
    même amendement — `co_signataires` compris. Pour un amendement à N
    cosignataires, le même contenu est donc dupliqué N+1 fois dans `index`
    (mesuré : 3,86 Go décompressés pour la législature 16, committable
    uniquement une fois dédupliqué — voir la révision de
    docs/decisions/amendements-legislatures-figees.md).

    Retourne (amendements, index_par_acteur) :
    - `amendements` : chaque amendement stocké une seule fois, sous la clé
      `uid` (identifiant AN, partagé par toutes les copies d'un même amendement
      en entrée puisqu'elles dérivent du même `record_base`).
    - `index_par_acteur` : acteurRef -> liste de `{uid, role_signataire}`,
      une référence légère vers `amendements` au lieu d'une copie complète.

    **La clé est l'`uid`, jamais le `numero`** (corrigé le 18/08/2026, voir
    docs/decisions/amendements-cle-uid.md). Le `numeroLong` de l'AN
    repart à chaque texte : sur l'archive de la législature 17, 121 805
    amendements ne portent que 30 616 `numeroLong` distincts (`AE12` est porté
    par 7 textes sans rapport). Keyer par `numero` écrasait donc 74,9 % des
    amendements et faisait résoudre 40,5 % des paires (acteur, amendement) vers
    un AUTRE amendement que le leur — un fait faux, pas seulement une perte.
    L'`uid` est unique toutes législatures confondues, comme celui des scrutins
    (voir `_build_scrutins_index`), et présent dans les deux schémas AN
    (moderne et legacy XIV).

    Les enregistrements sans `uid` (non observés : les archives XIV à XVII en
    portent un sur chaque amendement) reçoivent une clé synthétique non
    partagée, pour ne jamais être perdus ni dédupliqués à tort avec un autre
    amendement. Inverse : `_expand_aggregated_amendements_index`.
    """
    amendements: dict[str, dict[str, Any]] = {}
    index_par_acteur: dict[str, list[dict[str, Any]]] = {}
    sans_uid_compteur = 0

    for acteur_ref, records in index.items():
        refs: list[dict[str, Any]] = []
        for record in records:
            uid = record.get("uid")
            if not uid:
                uid = f"_sans_uid_{sans_uid_compteur}"
                sans_uid_compteur += 1
            refs.append({"uid": uid, "role_signataire": record.get("role_signataire")})
            if uid not in amendements:
                amendements[uid] = {k: v for k, v in record.items() if k != "role_signataire"}
        index_par_acteur[acteur_ref] = refs

    return amendements, index_par_acteur


def _cache_amendements_au_format_uid(tranches: list[Path]) -> bool:
    """Le cache disque shardé est-il au format `uid` ? Décidé sur la PREMIÈRE
    tranche lisible (~285 Ko), pas sur l'index entier : les tranches sont
    toutes écrites d'un bloc par `_write_cached_amendements_agreges`, donc
    toujours dans le même format.

    Un cache sans aucune tranche lisible est déclaré conforme : il n'en sortira
    aucune référence périmée, et c'est le contrôle d'existence appelant qui
    décide de le reconstruire ou non.
    """
    for tranche in tranches:
        try:
            with open(tranche, encoding="utf-8") as f:
                refs = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        return _index_par_acteur_au_format_uid({"_": refs})
    return True


def _index_par_acteur_au_format_uid(index_par_acteur: Any) -> bool:
    """Un `index_par_acteur` est-il au format `{uid, role_signataire}` (et non
    au format `{numero, role_signataire}` d'avant la correction du 18/08/2026) ?

    Sert de garde-fou à la lecture des caches et des index figés : un index
    hérité doit être reconstruit, jamais relu — ses références par `numero`
    résolvent vers le mauvais amendement une fois sur deux et sont
    indistinguables de références correctes à l'usage. Vérifié sur la première
    référence rencontrée : les deux formats ne se mélangent pas, un index étant
    toujours écrit d'un bloc par `_aggregate_amendements_index`.
    """
    if not isinstance(index_par_acteur, dict):
        return False
    for refs in index_par_acteur.values():
        if not isinstance(refs, list):
            return False
        for ref in refs:
            if not isinstance(ref, dict):
                return False
            return bool(ref.get("uid"))
    # Index vide (aucun acteur, ou aucun amendement) : rien à reconstruire,
    # aucune référence périmée ne peut en sortir.
    return True


def _expand_aggregated_amendements_index(
    amendements: dict[str, dict[str, Any]],
    index_par_acteur: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    """Inverse de `_aggregate_amendements_index` : reconstruit la forme plate
    acteurRef -> amendements (avec le contenu de chaque amendement à nouveau
    dupliqué par entrée, `role_signataire` réinjecté) attendue par le reste du
    pipeline — `fetch_amendements_officiels` lit exclusivement cette forme
    depuis le cache disque standard, quelle que soit l'origine (réseau ou
    fallback figé). Une référence dont l'`uid` est absent de `amendements`
    (ne devrait pas arriver, les deux fichiers étant committés ensemble) est
    ignorée plutôt que de lever."""
    expanded: dict[str, list[dict[str, Any]]] = {}
    for acteur_ref, refs in index_par_acteur.items():
        entries: list[dict[str, Any]] = []
        for ref in refs:
            base = amendements.get(ref.get("uid"))
            if base is None:
                continue
            entries.append({**base, "role_signataire": ref.get("role_signataire")})
        expanded[acteur_ref] = entries
    return expanded


def amendements_index_en_cache_utilisable(legislature: str) -> Optional[list[Path]]:
    """Les tranches d'un cache d'amendements servable, ou `None` s'il faut construire.

    Extrait du court-circuit de `_download_and_build_amendement_index` (#749),
    qui le garde comme unique condition de cache-hit. Il est exposé parce que
    `build_amendements_index.py` doit pouvoir DIRE, dans son log, s'il a
    construit un index ou servi celui du cache : jusqu'ici il imprimait
    « Construction de l'index amendements » puis un compte d'acteurs pour une
    exécution de 0,28 s qui ne téléchargeait rien, et ce log est ce qui a rendu
    invisible pendant 18 jours l'absence totale de reconstruction.

    La liste des acteurs se déduit des NOMS des tranches, sans en ouvrir
    aucune (#392) — matérialiser leur contenu coûterait des centaines de Mo
    pour une information dont le seul consommateur fait `len()`.

    `None` couvre trois cas distincts, et c'est voulu qu'ils se rejoignent :
    cache absent, cache illisible, et cache au format HÉRITÉ (références par
    `numero` plutôt que par `uid`). Ce dernier doit être reconstruit et non
    servi : sans ce contrôle, un cache CI restauré à l'ancien format serait un
    hit ici — donc jamais reconstruit — pendant que
    `_read_cached_amendements_acteur` le refuserait à la lecture, et les
    amendements de la législature disparaîtraient silencieusement jusqu'à
    expiration du cache. Coût du contrôle : l'ouverture d'UNE tranche
    (~285 Ko).
    """
    cache_dir = AMENDEMENTS_CACHE_DIR / legislature
    amendements_path = cache_dir / AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME
    index_dir = cache_dir / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
    if not amendements_path.is_file() or not index_dir.is_dir():
        return None
    try:
        tranches = list(index_dir.glob("*.json"))
        if _cache_amendements_au_format_uid(tranches):
            return tranches
        print(
            f"  [!] Cache amendements législature {legislature} au format hérité "
            "(références par 'numero') : reconstruction depuis l'archive AN.",
            file=sys.stderr,
        )
    except OSError:
        pass  # cache illisible : on reconstruit
    return None


def purger_cache_amendements_legislature(legislature: str) -> bool:
    """Supprime le cache disque d'une législature, pour forcer sa reconstruction (#749).

    Appelée par `build_amendements_index.py --reconstruire-actives` quand la CI
    a changé de semaine ISO sans que la clé exacte ait été touchée. Ne vise que
    les législatures ACTIVES : une législature figée n'a pas de fraîcheur à
    rafraîchir, et re-matérialiser son index committé chaque semaine coûterait
    la mémoire décrite dans `docs/decisions/oom-reconstruction-amendements-figees.md`
    pour une donnée qui ne change plus jamais.

    Retourne True si quelque chose a été supprimé.
    """
    cache_dir = AMENDEMENTS_CACHE_DIR / legislature
    if not cache_dir.is_dir():
        return False
    shutil.rmtree(cache_dir)
    return True


def _download_and_build_amendement_index(legislature: str) -> dict[str, list[dict[str, Any]]]:
    """Télécharge l'archive AN et construit (en la mettant en cache sur disque) un
    index acteurRef -> liste d'amendements. Reprend telle quelle la logique réseau
    précédemment inline dans l'ex-`_build_acteur_amendement_index` (issue #250).

    Seul point d'entrée réseau restant pour les amendements officiels, appelé
    exclusivement par le job CI dédié `extract-amendements-an`
    (`src/build_amendements_index.py`, #251) : `fetch_amendements_officiels`
    ne l'appelle plus depuis #252 (sous-issue 4/6 de #248), elle lit
    uniquement `_read_cached_amendements_acteur`.

    Pour une législature figée (`AN_AMENDEMENTS_LEGISLATURES_FIGEES`), aucun
    appel réseau n'a lieu : l'index committé est chargé par
    `_load_frozen_amendement_index` (voir aussi
    `docs/decisions/amendements-legislatures-figees.md`).

    Contrairement à `_build_acteur_vote_index`, les ~120k fichiers individuels de
    l'archive ne sont jamais extraits sur disque (uniquement lus en mémoire un par
    un depuis le zip) : seul l'index final (acteurRef -> amendements) est mis en
    cache, pour éviter d'écrire des dizaines de milliers de petits fichiers.
    L'archive téléchargée elle-même est supprimée en fin de tentative, succès
    comme échec (#264) : elle n'est jamais relue ensuite, et la conserver
    gonflait l'artifact et le cache partagé de 283-618 Mo par législature.
    Thread-safe (verrou par législature), même principe que pour les scrutins.

    Lève `AmendementsIndexError` en cas d'échec de téléchargement ou de parsing de
    l'archive (au lieu de retourner un {} indiscernable d'un index vide légitime),
    pour que l'appelant puisse le distinguer et le tracer.

    Un échec définitif (tentatives épuisées) est mémorisé à la fois en mémoire
    process (`_amendements_failed_legislatures`, #239) et sur un marqueur disque
    partagé entre jobs CI du même run (`_mark_amendements_legislature_failed`,
    #246) : les candidats suivants du même job, ou le premier candidat d'un job
    CI suivant (ex. `extract-roster-groupes` après `extract-an`) ayant besoin de
    la même législature durant ce run, lèvent immédiatement
    `AmendementsIndexError` sans nouvelle tentative réseau.

    Un index déjà en cache n'est jamais écrasé par un échec (`index_path` n'est
    ouvert en écriture qu'après succès complet du téléchargement et du parsing
    ci-dessous) : un échec définitif laisse le fichier existant tel quel, s'il y
    en a un (issue #253). Un indicateur de fraîcheur (`fraicheur.json`, voir
    `_write_amendements_fraicheur`) est écrit à côté de l'index à chaque
    tentative qui en concerne un — succès (index remplacé) ou échec définitif
    sur un index préexistant conservé — pour qu'un futur consommateur puisse
    distinguer les deux.
    """
    with _get_amendements_lock(legislature):
        cache_dir = AMENDEMENTS_CACHE_DIR / legislature
        index_dir = cache_dir / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_DIRNAME
        amendements_path = cache_dir / AMENDEMENTS_CACHE_AMENDEMENTS_FILENAME
        index_path = cache_dir / AMENDEMENTS_CACHE_INDEX_PAR_ACTEUR_FILENAME_LEGACY
        # Cache-hit : la liste des acteurs indexés se déduit des NOMS des
        # tranches, sans en ouvrir aucune (#392). Le seul consommateur de
        # cette valeur de retour en fait `len()` (build_amendements_index.py),
        # d'où des listes vides en valeurs : matérialiser le contenu coûterait
        # des centaines de Mo pour une information dont personne ne se sert.
        # #749 — le prédicat est NOMMÉ et partagé avec `build_amendements_index.py`,
        # qui doit dire dans son log s'il a construit ou servi le cache. Le
        # dupliquer là-bas aurait laissé les deux dériver, et c'est exactement
        # un log faux qui a rendu cette panne invisible 18 jours.
        tranches = amendements_index_en_cache_utilisable(legislature)
        if tranches is not None:
            return {p.stem: [] for p in tranches}

        if legislature in AN_AMENDEMENTS_LEGISLATURES_FIGEES:
            frozen_index = _load_frozen_amendement_index(legislature)
            if frozen_index is not None:
                return frozen_index

        if _amendements_legislature_failed_this_run(legislature):
            if index_path.is_file():
                _write_amendements_fraicheur(index_path, reussi=False)
            raise AmendementsIndexError(
                f"téléchargement déjà en échec pour la législature {legislature} durant ce run (non retenté)"
            )

        url = _amendements_zip_url(legislature)
        if not url:
            return {}

        print(f"-> Téléchargement des amendements officiels (Assemblée nationale) : {url}")
        zip_path = AMENDEMENTS_CACHE_DIR / legislature / "amendements.zip"
        # try/finally (#264) : l'archive brute (283-618 Mo selon la
        # législature) n'a plus aucune utilité une fois l'index construit —
        # elle n'est jamais relue, ni par la lecture cache-only
        # (`_read_cached_amendements_acteur`), ni pour reprendre un
        # téléchargement entre deux tentatives (`_download_amendements_zip`
        # réécrit toujours depuis zéro). La conserver gonflait l'artifact
        # `amendements-index-an` et le cache hebdomadaire partagé
        # `public-data-cache-an-*` d'autant, pour rien. Supprimée dans TOUS
        # les cas (succès, échec réseau, archive invalide) : un fichier
        # partiel ou invalide n'a pas plus d'utilité qu'une archive
        # correctement parsée.
        try:
            try:
                _download_amendements_zip(url, zip_path, legislature)
            except SourceAmendementsIndisponibleError as exc:
                # Journalisé distinctement d'un échec de téléchargement (#443) :
                # ici, relancer le job ne sert à rien tant que la source ne
                # revient pas. Le log doit le dire, sinon la personne qui le lit
                # relance en boucle un traitement qui ne peut pas aboutir.
                print(f"  [!] Source AN indisponible pour les amendements : {exc}")
                _mark_amendements_legislature_failed(legislature)
                if index_path.is_file():
                    _write_amendements_fraicheur(index_path, reussi=False)
                raise AmendementsIndexError(f"source indisponible ({exc})") from exc
            except SourceAmendementsIncoherenteError as exc:
                # Journalisé distinctement lui aussi (#1050) : ni le réseau ni
                # la disponibilité de la source ne sont en cause, c'est la
                # source qui publie plusieurs versions de la même URL.
                # Relancer est un tirage, pas une réparation — le log doit le
                # dire, sinon on cherche une panne qui n'existe pas.
                print(f"  [!] Source AN incohérente pour les amendements : {exc}")
                _mark_amendements_legislature_failed(legislature)
                if index_path.is_file():
                    _write_amendements_fraicheur(index_path, reussi=False)
                raise AmendementsIndexError(f"source incohérente ({exc})") from exc
            except (requests.RequestException, OSError) as exc:
                print(f"  [!] Échec du téléchargement des amendements officiels : {exc}")
                _mark_amendements_legislature_failed(legislature)
                if index_path.is_file():
                    _write_amendements_fraicheur(index_path, reussi=False)
                raise AmendementsIndexError(f"échec du téléchargement ({exc})") from exc

            try:
                index = _parse_amendements_zip(zip_path)
                # #1029 voie 2 — l'article visé et les mots de l'exposé, lus dans
                # la MÊME archive avant qu'elle ne soit supprimée. Non bloquant :
                # un contenu manquant se reconstruit au run suivant, l'index des
                # amendements, lui, ne doit jamais être perdu pour autant.
                try:
                    from amendements_contenu import ecrire_contenu_cache  # noqa: PLC0415

                    ecrire_contenu_cache(legislature, zip_path, AMENDEMENTS_CACHE_DIR)
                except (MemoryError, OSError, ValueError, zipfile.BadZipFile, zlib.error) as exc:
                    print(f"  [!] Contenu des amendements non construit ({legislature}) : {exc}")
            except (zipfile.BadZipFile, zlib.error) as exc:
                # `zlib.error` et non seulement `BadZipFile` (#1050) : une
                # archive recollée à partir de deux versions s'OUVRE
                # normalement — l'en-tête et le répertoire central sont
                # valides — et ne déraille qu'à la décompression d'un membre.
                # Attraper le seul `BadZipFile` laissait cette erreur sortir
                # de la boucle par législature de `build_amendements_index.py`,
                # là où le contrat est « une législature perdue, jamais les
                # autres ». Le run, lui, survivait : le job porte
                # `continue-on-error: true` (mesuré sur le run 35531938588 du
                # 20/09/2026, où il a échoué à 21h23 sans interrompre la suite).
                print(f"  [!] Archive d'amendements invalide : {exc}")
                _mark_amendements_legislature_failed(legislature)
                if index_path.is_file():
                    _write_amendements_fraicheur(index_path, reussi=False)
                raise AmendementsIndexError(f"archive invalide ({exc})") from exc
        finally:
            try:
                zip_path.unlink(missing_ok=True)
            except OSError:
                pass  # best-effort, comme l'écriture du cache elle-même

        # Déduplication avant écriture (#377) : `_parse_amendements_zip`
        # produit un enregistrement complet par signataire, donc N+1 copies du
        # même amendement pour N cosignataires. Écrire cette forme plate telle
        # quelle produisait un cache de plusieurs Go, relu intégralement par
        # candidat côté `fetch_amendements_officiels` — cause de l'OOM
        # documenté dans #oom-lecture-amendements-par-candidat.
        amendements_dedup, index_par_acteur = _aggregate_amendements_index(index)
        try:
            _write_cached_amendements_agreges(legislature, amendements_dedup, index_par_acteur)
            _write_amendements_fraicheur(index_path, reussi=True)
        except OSError:
            pass

        return index_par_acteur


# `_build_texte_titre_index` vivait ici (#639). Elle construisait un index
# `code de texte -> titre du dossier`, et son unique appelant s'en servait pour
# ÉCRASER le `texte_vise` des amendements — le code source AN
# (`PRJLANR5L14B1057`) remplacé par un libellé (« Système universel de
# retraite ») avant même l'écriture du profil brut. 293 582 des 484 132
# amendements publiés n'ont plus de clé pour cette raison : la perte est
# infligée par le pipeline, pas subie de la source.
#
# Le libellé lisible n'est pas perdu pour autant : il vit désormais une fois par
# texte dans la table `textes` de `pivot_data/amendements/<leg>.json`, à côté du
# `dossier_id` que ce même code permet enfin de résoudre
# (`textes_dossiers_an.py`). Voir docs/decisions/dossier-des-amendements-639.md.


# Stades procéduraux, du moins au plus avancé : sert à déterminer le stade le
# plus avancé réellement atteint par un dossier (un seul stade par dossier,
# pas par acte).
_STADE_RANKS = {
    "depose": 1,
    "examine_commission": 2,
    "discute_seance": 3,
    "adopte": 4,
    "promulgue": 5,
}


def _stade_from_code_acte(code_acte: Optional[str], statut_libelle: Optional[str]) -> Optional[str]:
    """Déduit un stade procédural (nomenclature du schéma pivot) à partir du
    code d'acte officiel (`codeActe`) d'un dossier législatif. Volontairement
    conservateur : ne retient que des signaux non ambigus (voir
    docs/sources/an-opendata.md, section dossiers législatifs)."""
    if not code_acte:
        return None
    if "PROM" in code_acte:
        return "promulgue"
    if code_acte.endswith("-DEBATS-DEC"):
        if statut_libelle and statut_libelle.strip().lower().startswith("adopt"):
            return "adopte"
        return "discute_seance"
    if "DEBATS" in code_acte:
        return "discute_seance"
    # #997 — `"COM" in code_acte` rendait `examine_commission` pour la saisine
    # de commission, qui est AUTOMATIQUE au dépôt : 6 808 des 10 764 dossiers
    # des archives XV à XVII étaient qualifiés « examiné » sans l'avoir été, et
    # la branche `DEPOT` ci-dessous était morte. `est_examen_en_commission`
    # porte l'arbitrage (réunion ou rapport) — voir `gouvernement_textes.py`.
    if "COM" in code_acte:
        if est_examen_en_commission(code_acte):
            return "examine_commission"
        # Saisine, nomination de rapporteur, conteneur : le texte a été
        # RENVOYÉ en commission, pas examiné. Le dépôt reste à qualifier par
        # l'acte `-DEPOT` du même dossier, d'où `None` plutôt que `"depose"` —
        # `_collect_dossier_facts` retient le stade le plus avancé de tous les
        # actes, et c'est lui qui conclura.
        return None
    if "DEPOT" in code_acte:
        return "depose"
    return None


def _collect_initiateurs(dossier: dict, acteur_roles: dict[str, tuple[str, Optional[str]]]) -> None:
    """Ajoute à `acteur_roles` chaque acteur cité comme initiateur (auteur) du
    dossier (`initiateur.acteurs.acteur`, dict unique ou liste selon les cas)."""
    initiateur = dossier.get("initiateur")
    if not isinstance(initiateur, dict):
        return
    acteurs = (initiateur.get("acteurs") or {}).get("acteur")
    items = acteurs if isinstance(acteurs, list) else [acteurs]
    for item in items:
        if isinstance(item, dict):
            acteur_ref = item.get("acteurRef")
            if isinstance(acteur_ref, str) and acteur_ref:
                acteur_roles.setdefault(acteur_ref, ("auteur", None))


def _collect_dossier_facts(
    node: Any,
    acteur_roles: dict[str, tuple[str, Optional[str]]],
    dates: list[str],
    stades: list[str],
) -> None:
    """Parcourt récursivement l'arbre `actesLegislatifs` d'un dossier et
    collecte : le rôle factuel de chaque rapporteur (`rapporteurs`, plusieurs
    rapporteurs sur un même acte -> "co-rapporteur"), les dates d'acte
    (`dateActe`) et les stades procéduraux atteints (`codeActe`/`statutConclusion`)."""
    if isinstance(node, dict):
        date_acte = node.get("dateActe")
        if isinstance(date_acte, str) and date_acte:
            dates.append(date_acte[:10])

        code_acte = node.get("codeActe")
        if isinstance(code_acte, str):
            statut = node.get("statutConclusion")
            statut_libelle = statut.get("libelle") if isinstance(statut, dict) else None
            stade = _stade_from_code_acte(code_acte, statut_libelle)
            if stade:
                stades.append(stade)

        rapporteurs = node.get("rapporteurs")
        if isinstance(rapporteurs, dict):
            entries = rapporteurs.get("rapporteur")
            items = [it for it in (entries if isinstance(entries, list) else [entries]) if isinstance(it, dict)]
            role = "co-rapporteur" if len(items) > 1 else "rapporteur"
            for item in items:
                acteur_ref = item.get("acteurRef")
                if isinstance(acteur_ref, str) and acteur_ref:
                    type_rapport = TYPE_RAPPORTEUR_MAP.get((item.get("typeRapporteur") or "").strip().lower())
                    acteur_roles.setdefault(acteur_ref, (role, type_rapport))

        for key, value in node.items():
            if key != "rapporteurs":
                _collect_dossier_facts(value, acteur_roles, dates, stades)
    elif isinstance(node, list):
        for item in node:
            _collect_dossier_facts(item, acteur_roles, dates, stades)


def _collect_acteur_roles(dossier: dict) -> tuple[dict[str, tuple[str, Optional[str]]], Optional[str], Optional[str], Optional[str]]:
    """Combine initiateurs et rapporteurs d'un dossier en un seul mapping
    acteurRef -> (role, type_rapport), et calcule le stade procédural le plus
    avancé et les dates min/max de l'ensemble du dossier."""
    acteur_roles: dict[str, tuple[str, Optional[str]]] = {}
    _collect_initiateurs(dossier, acteur_roles)
    dates: list[str] = []
    stades: list[str] = []
    _collect_dossier_facts(dossier.get("actesLegislatifs"), acteur_roles, dates, stades)
    date_min = min(dates) if dates else None
    date_max = max(dates) if dates else None
    stade = max(stades, key=lambda s: _STADE_RANKS[s]) if stades else None
    return acteur_roles, stade, date_min, date_max


def _tprint_textes_portes(message: str) -> None:
    """Trace du chemin des textes portés, sur stderr (#997).

    **Pourquoi une trace et pas une exception.** Ce chemin est non fatal par
    construction, et il doit le rester : une panne d'archive ne doit pas faire
    échouer un run dont tout le reste est bon (#524). Mais « non fatal » avait
    dérivé en « silencieux », et un chemin qui rend `[]` sans un mot est
    indistinguable d'un chemin qui n'a rien trouvé — la fusion garde alors
    l'ancien, le profil ne bouge pas, et aucune étape n'échoue.

    Mesuré : le correctif de stade de #997 a traversé **trois runs** sans
    atteindre le corpus, et aucun log ne permet de dire lequel des quatre
    chemins muets a été pris. C'est la forme exacte du trou de #510 et #501,
    et le remède est le même — rendre bruyant avant de reboucher.
    """
    print(f"  [textes portés] {message}", file=sys.stderr)


def _build_acteur_textes_portes_index() -> dict[str, list[dict[str, Any]]]:
    """Construit (et met en cache sur disque) un index acteurRef -> liste de
    dossiers législatifs où l'acteur a un rôle factuel connu (auteur,
    rapporteur ou co-rapporteur), à partir du jeu de données bulk des dossiers
    législatifs (même archive que `textes_dossiers_an.construire_table`).

    Contrairement à la liste NosDéputés `dossiers/nom/json` — retirée par #528
    avec le Sénat, seule chambre qui l'appelait — qui renvoyait l'intégralité
    des dossiers d'une législature identiquement pour tous les élus (role
    toujours null, voir docs/sources/an-opendata.md), cet index est réellement propre à
    chaque acteur. Non-fatal en cas d'échec (retourne {})."""
    with _DOSSIERS_TEXTES_PORTES_LOCK:
        # `_v3` depuis #689 : un index construit avant lui ne porte pas
        # `nature_texte`, et l'existence d'un cache n'est pas la preuve de sa
        # conformité (même règle que pour les caches d'amendements et de
        # scrutins). Le relire ferait republier « auteur » sur les 316 projets
        # de loi du corpus, sans qu'aucune étape n'échoue.
        #
        # `_v4` depuis #997, et EXACTEMENT pour la même raison. Le `stade` est
        # calculé ICI, par `_collect_acteur_roles`, puis figé dans le fichier :
        # le correctif qui a retiré `examine_commission` à 6 808 dossiers
        # n'atteint donc rien tant que l'ancien index est relu. Et il l'est :
        # `.cache/dossiers_an` est restauré en CI par une clé hebdomadaire dont
        # les `restore-keys` acceptent la semaine précédente
        # (`public-data-cache-dossiers-`). Mesuré le 18/09/2026 — le run
        # 35324142500 portait le correctif et a republié les 21
        # `examine_commission` de Marine Le Pen à l'identique.
        #
        # La règle, une fois de plus : **un cache porte le code qui l'a écrit.**
        # Un correctif qui change ce qu'un index CONTIENT change sa clé, sans
        # quoi il ne change rien.
        # `_v5` depuis #1019 : l'archive XIV entre dans la couverture, donc
        # l'index gagne 3 402 dossiers. Même règle, quatrième fois.
        index_path = DOSSIERS_CACHE_DIR / "index_acteur_textes_v5.json"  # cf. #400, #689, #997, #1019
        if index_path.is_file():
            try:
                with open(index_path, encoding="utf-8") as f:
                    index_cache = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                _tprint_textes_portes(
                    f"cache {index_path.name} illisible ({exc}) — reconstruction.")
            else:
                _tprint_textes_portes(
                    f"index relu depuis {index_path.name} "
                    f"({len(index_cache)} acteurs) — AUCUNE reconstruction.")
                return index_cache

        archives = ensure_dossiers_zips_downloaded()
        if not archives:
            # #997 — LA sortie muette. Sans archive, l'index est vide, donc
            # `fetch_textes_portes_officiels` rend `[]`, donc la fusion garde
            # intégralement les entrées du run précédent : le profil ne bouge
            # pas d'un octet et rien ne dit pourquoi. Trois runs ont passé
            # ainsi, les 18/09 à 10h23, 12h04 et après.
            _tprint_textes_portes(
                "AUCUNE archive de dossiers disponible — index vide. Les textes "
                "portés publiés restent ceux du run précédent, inchangés.")
            return {}

        index: dict[str, list[dict[str, Any]]] = {}
        # Multi-archives dédupliqué par uid (#400) : sans déduplication, un
        # dossier présent dans deux archives serait compté deux fois dans les
        # textes portés de chaque acteur.
        for _legislature, dossier in iter_dossiers_bruts(archives):
            titre_dossier = dossier.get("titreDossier") or {}
            titre = titre_dossier.get("titre")
            titre_chemin = titre_dossier.get("titreChemin")
            if not titre:
                continue
            acteur_roles, stade, date_min, date_max = _collect_acteur_roles(dossier)
            if not acteur_roles:
                continue
            # #689 : la nature du texte déposé, lue dans la MÊME archive et par
            # la MÊME fonction que les fiches de gouvernement (#435). Sans elle,
            # un projet de loi porté au nom de l'exécutif et une proposition de
            # loi déposée comme parlementaire sortaient d'ici sous le seul
            # `role: "auteur"` — 316 des 472 entrées publiées, dont les 282
            # d'`edouard-philippe`, tous déposés alors qu'il était Premier
            # ministre. L'information n'était pas perdue à la source : elle
            # était jetée ici.
            nature = nature_texte_depose(dossier)
            # #743 : l'ISSUE du dossier, lue dans la MÊME archive et par la MÊME
            # fonction que les fiches de gouvernement — `_determine_statut` ne
            # dépend pas de l'origine du dossier, c'est `parse_dossier_gouvernemental`
            # qui filtre l'origine AVANT de l'appeler. Sans elle, `textes_portes[]`
            # publiait dix champs dont aucun ne disait ce qu'était devenu le texte :
            # ni rejeté, ni retiré, ni en navette. `stade_procedural` encode une
            # PROGRESSION, et l'absence du cran suivant est un fait de la source à
            # sa date, jamais un sort.
            sort, _sort_49_3, avertissement_sort = _determine_statut(
                dossier.get("uid"), dossier.get("actesLegislatifs")
            )
            # `sort_49_3` est volontairement NON republié ici : `adopte_49_3` et
            # `rejete_49_3` le portent déjà, et le dupliquer ferait deux faits là
            # où il n'y en a qu'un.
            sort_non_resolu = None
            if sort is None:
                # Deux absences qui ne se réparent pas au même endroit : un code
                # que la table ne connaît pas est un trou à combler, un dossier
                # sans décision de séance est un état légitime.
                sort_non_resolu = {
                    "motif": "fam_code_inconnu" if avertissement_sort else "sans_decision"
                }
            legislature = dossier.get("legislature")
            source_url = (
                f"https://www.assemblee-nationale.fr/dyn/{legislature}/dossiers/{titre_chemin}"
                if legislature and titre_chemin else None
            )
            for acteur_ref, (role, type_rapport) in acteur_roles.items():
                index.setdefault(acteur_ref, []).append({
                    "id": dossier.get("uid"),
                    "titre": titre,
                    "role": role,
                    "nature_texte": nature,
                    "type_rapport": type_rapport,
                    "stade_procedural": stade,
                    "sort": sort,
                    "sort_non_resolu": sort_non_resolu,
                    "date_min": date_min,
                    "date_max": date_max,
                    "legislature": legislature,
                    "source_url": source_url,
                })

        _tprint_textes_portes(
            f"index reconstruit depuis {len(archives)} archive(s) : "
            f"{len(index)} acteurs.")
        if not index:
            # Des archives lisibles qui ne rendent AUCUN acteur : ce n'est pas
            # un corpus vide, c'est un défaut de lecture. Même conséquence que
            # ci-dessus, et même invisibilité jusqu'à #997.
            _tprint_textes_portes(
                "l'index est VIDE alors que les archives ont été lues — les "
                "textes portés publiés resteront ceux du run précédent.")

        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False)
        except OSError as exc:
            # Non fatal, mais plus muet : un index non écrit est reconstruit à
            # chaque appel, ce qui coûte sans qu'on le voie.
            _tprint_textes_portes(f"index NON écrit dans {index_path} ({exc}).")

        return index


def fetch_textes_portes_officiels(url_an_ou_senat: Optional[str]) -> list[dict[str, Any]]:
    """Récupère les dossiers législatifs où l'élu a un rôle factuel connu
    (auteur, rapporteur ou co-rapporteur), depuis le jeu de données officiel
    des dossiers législatifs (Assemblée nationale). SEULE source de
    `dossiers_legislatifs` depuis #528 : elle a remplacé la liste NosDéputés
    `dossiers/nom/json`, qui n'était pas propre à l'élu et n'était plus appelée
    que pour le Sénat."""
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        # Quatrième sortie muette (#997) : sans acteur résolu, la collecte rend
        # `[]` et la fusion conserve tout l'ancien. Le profil déclare pourtant
        # `textes_portes` COLLECTÉE, puisque le drapeau ne l'avait pas écartée.
        _tprint_textes_portes(
            f"aucun acteur AN résolu depuis {url_an_ou_senat!r} — les textes "
            "portés publiés restent ceux du run précédent.")
        return []
    index = _build_acteur_textes_portes_index()
    entries = index.get(acteur_ref, [])
    if not entries:
        _tprint_textes_portes(
            f"{acteur_ref} absent de l'index ({len(index)} acteurs) — aucun "
            "texte porté collecté pour ce profil.")
    return sorted(entries, key=lambda t: (t.get("date_max") or "", t.get("titre") or ""), reverse=True)


def _format_lieu_naissance(ville: Optional[str], departement: Optional[str], pays: Optional[str]) -> Optional[str]:
    """Formate ville/département/pays de naissance en un texte lisible.

    Le département n'est pertinent que pour une naissance en France : pour un
    pays étranger, on l'omet au profit du pays (ex. "Alger (Algérie)" plutôt
    que d'ignorer l'information géographique disponible).

    **Les trois arguments repassent par `_champ_identite_an`** (#556) bien que
    l'appelant les filtre déjà. Ce n'est pas une redondance : cette fonction
    **interpole** ses arguments, donc un marqueur `xsi:nil` qui l'atteint ne
    ressort pas en `dict` repérable mais en **chaîne** — 28 profils publiés
    portaient un lieu de naissance fait de plomberie XML, dont 18 entièrement.
    La garde vit ici parce que c'est ici que le dict devient indétectable.
    """
    ville = _texte_an(ville)
    departement = _texte_an(departement)
    pays = _texte_an(pays)
    if pays and pays != "France":
        complement = pays
    else:
        complement = departement
    if ville and complement:
        return f"{ville} ({complement})"
    return ville or complement or None


_CONTACT_TYPE_LIBELLE_MAP: dict[str, str] = {
    "Mèl": "email",
    "Twitter": "twitter",
    "Facebook": "facebook",
    "Site internet": "site_web",
}


def _extract_contact(adresses: list[Any]) -> dict[str, Optional[str]]:
    """Extrait les coordonnées de contact publiques (email, Twitter, Facebook,
    site web) depuis `acteur.adresses.adresse[]`. Ignore volontairement les
    autres types présents dans ce bloc (adresses postales, téléphone,
    Instagram, Linkedin...) — hors périmètre de cette extraction."""
    contact: dict[str, Optional[str]] = {key: None for key in _CONTACT_TYPE_LIBELLE_MAP.values()}
    for adresse in adresses:
        if not isinstance(adresse, dict):
            continue
        key = _CONTACT_TYPE_LIBELLE_MAP.get(_champ_identite_an(adresse.get("typeLibelle")))
        if key and not contact[key]:
            # #556 : une adresse déclarée vide rend le marqueur `xsi:nil`, et un
            # `valElec` non filtré publierait un dict là où l'interface fait un
            # `mailto:`.
            contact[key] = _champ_identite_an(adresse.get("valElec"))
    return contact


def _format_nom_complet(prenom: Optional[str], nom: Optional[str]) -> Optional[str]:
    """Formate prénom/nom (etatCivil.ident) en un nom complet lisible.

    Même garde que `_format_lieu_naissance`, pour la même raison : elle
    interpole (#556).
    """
    prenom = _texte_an(prenom)
    nom = _texte_an(nom)
    if prenom and nom:
        return f"{prenom} {nom}"
    return prenom or nom or None


def _select_mandat_par_type_courant(mandats: list[Any], type_organe: str) -> Optional[dict[str, Any]]:
    """Sélectionne, parmi les mandats d'un acteur dont `typeOrgane ==
    type_organe`, celui correspondant à la période la plus pertinente : le
    mandat en cours (`dateFin` absent) s'il en existe un, sinon celui dont
    `dateDebut` est le plus récent (mandat terminé). Généralisé (issue #369)
    à partir de la logique déjà en place pour `typeOrgane == "ASSEMBLEE"`
    (voir `_select_mandat_assemblee_courant`) — même besoin pour `"GP"`
    (groupe politique actuel, quand plusieurs périodes d'appartenance
    successives existent)."""
    best: Optional[dict[str, Any]] = None
    for mandat in mandats:
        if not isinstance(mandat, dict) or mandat.get("typeOrgane") != type_organe:
            continue
        if best is None:
            best = mandat
            continue
        best_en_cours = best.get("dateFin") is None
        mandat_en_cours = mandat.get("dateFin") is None
        if mandat_en_cours and not best_en_cours:
            best = mandat
        elif mandat_en_cours == best_en_cours and (mandat.get("dateDebut") or "") > (best.get("dateDebut") or ""):
            best = mandat
    return best


def _select_mandat_assemblee_courant(mandats: list[Any]) -> Optional[dict[str, Any]]:
    """Sélectionne, parmi les mandats `typeOrgane == "ASSEMBLEE"` d'un acteur,
    celui correspondant à l'élection la plus pertinente pour la circonscription/
    place hémicycle à afficher. Nécessaire depuis le passage à
    `AN_ACTEURS_HISTORIQUE_ZIP_URL` (issue #354) : contrairement à l'ancien
    jeu de données `AMO10` (limité aux mandats actifs, un seul mandat
    ASSEMBLEE possible par acteur), un acteur peut désormais avoir plusieurs
    mandats ASSEMBLEE successifs (réélections sur plusieurs législatures).
    Voir `_select_mandat_par_type_courant` pour la logique de sélection."""
    return _select_mandat_par_type_courant(mandats, "ASSEMBLEE")


def _groupe_du_mandat(
    mandats: list[Any],
    organe_index: dict[str, dict[str, Any]],
    debut: Optional[str],
    fin: Optional[str],
) -> tuple[Optional[str], Optional[str]]:
    """Groupe parlementaire à retenir pour un mandat électif donné : le
    **dernier rejoint pendant ce mandat**.

    Un député en change en cours de législature (scission, renommage — Wauquiez
    est UMP jusqu'en juin 2015 puis Les Républicains), et surtout **tout le
    monde commence non inscrit** : les groupes ne sont constitués qu'après
    l'ouverture de la législature, si bien qu'AMO30 porte pour chaque élu un
    mandat `GP` de quelques jours vers `NI`. C'est le même transit que
    `docs/decisions/roster-an-derive-amo30-526.md` a mesuré sur les rosters, et
    il piège exactement de la même façon : « le groupe au début du mandat »
    rendrait « Non inscrit » pour la quasi-totalité du corpus.

    Prendre le **dernier** groupe rejoint pendant le mandat écarte le transit
    par construction — il est premier, jamais dernier — et rend, pour un député
    qui n'a pas changé de groupe, le seul qu'il ait eu. Même logique de
    sélection que `_select_mandat_par_type_courant`, appliquée à une fenêtre
    au lieu de la carrière entière.

    Rend `(None, None)` quand aucun mandat `GP` ne commence dans la fenêtre :
    une absence reste une absence, et le libellé s'écrit alors sans
    parenthèse (AGENTS.md §2 règle 5).
    """
    if not debut:
        return None, None
    fin_bornee = fin or "9999-12-31"
    meilleur: Optional[dict[str, Any]] = None
    for mandat in mandats:
        if not isinstance(mandat, dict) or mandat.get("typeOrgane") != "GP":
            continue
        debut_gp = _champ_identite_an(mandat.get("dateDebut"))
        if not debut_gp or not (debut <= debut_gp < fin_bornee):
            continue
        if meilleur is None or debut_gp > (meilleur.get("dateDebut") or ""):
            meilleur = mandat
    if meilleur is None:
        return None, None
    organe = organe_index.get((meilleur.get("organes") or {}).get("organeRef") or "")
    if not organe:
        return None, None
    return organe.get("sigle"), organe.get("nom")


def _periodes_mandats_assemblee(
    mandats: list[Any], organe_index: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Toutes les périodes de mandat de député d'un acteur, la plus récente
    d'abord — et non plus le seul couple de dates du mandat courant (#640).

    ## Pourquoi la liste, et pourquoi c'est AMO30 qui la porte

    `AMO30_tous_acteurs_tous_mandats_tous_organes_historique` porte bien
    l'historique complet : Marine Le Pen (`PA720614`) y a trois mandats
    `typeOrgane == "ASSEMBLEE"` — 15e, 16e, 17e législatures —, et le corpus
    en compte **3 954 pour 3 117 acteurs**. Le profil n'en publiait qu'un,
    parce qu'`identite_an` ne portait qu'un `mandat_debut`/`mandat_fin` : celui
    du mandat courant. Mesuré sur `b684304f`, **379 profils sur les 457 qui
    portent `identite.nb_mandats` publiaient moins de `mandat_electif` que ce
    nombre**, 612 manquants — le compteur et la liste vivaient dans le même
    objet sans s'accorder.

    ## La clé de regroupement : `(legislature, dateDebut)`, pas la législature

    AMO30 scinde un même siège en plusieurs enregistrements quand il est
    interrompu puis repris — Xavier Bertrand (`PA267080`) a **trois**
    enregistrements de 13e législature, tous ouverts au 2007-06-20, fermés au
    2007-07-19, 2010-12-15 et 2012-06-19, chaque fois sur `causeFin =
    "Nomination comme membre du Gouvernement"`. C'est un siège, pas trois
    mandats : ils sont recollés en union de périodes, le geste que
    `docs/decisions/roster-an-derive-amo30-526.md` applique déjà aux organes
    successifs d'un groupe.

    Regrouper sur la **seule** législature serait faux, et la donnée le dit :
    Bertrand Petit (`PA344201`) a deux mandats de 16e législature — 2022-06-19
    → 2022-12-02, *élection annulée par le Conseil constitutionnel*, puis
    2023-01-29 → 2024-06-09 après une partielle. Les unir publierait un mandat
    couvrant deux mois pendant lesquels il n'était pas député : un fait
    fabriqué, ce qu'interdit la règle 2. La date d'ouverture sépare les deux
    cas sans arbitrage.

    ## `dateDebut`, pas `datePriseFonction`

    Les deux diffèrent (`2022-06-19` contre `2022-06-22` pour la 16e). Le
    corpus publié porte les deux conventions — les mandats collectés du temps
    de NosDéputés ont la seconde —, et la mesure tranche : sur les 477 profils
    dont l'acteur AN est résolu, `dateDebut` reproduit **457** entrées déjà
    publiées à l'identique contre **13** pour `datePriseFonction`. C'est aussi
    le champ que `_select_mandat_assemblee_courant` lit depuis toujours.

    Chaque période porte `segments`, le nombre d'enregistrements AMO30
    recollés : un mandat interrompu par une nomination au gouvernement en a
    plus d'un, et le compte reste lisible plutôt que d'être perdu au
    regroupement.
    """
    par_siege: dict[tuple[Any, Any], dict[str, Any]] = {}
    for mandat in mandats:
        if not isinstance(mandat, dict) or mandat.get("typeOrgane") != "ASSEMBLEE":
            continue
        debut = _champ_identite_an(mandat.get("dateDebut"))
        if not debut:
            # Sans date d'ouverture, la période n'est plaçable sur aucune
            # chronologie et aucune date ne s'invente (AGENTS.md §2 règle 5).
            # Aucun des 3 954 mandats ASSEMBLEE du référentiel n'est dans ce
            # cas au 31/08/2026 ; la branche existe pour que ça reste vrai.
            continue
        fin = _champ_identite_an(mandat.get("dateFin"))
        cle = (mandat.get("legislature"), debut)
        periode = par_siege.get(cle)
        if periode is None:
            par_siege[cle] = {
                "legislature": mandat.get("legislature"),
                "debut": debut,
                "fin": fin,
                "segments": 1,
            }
            continue
        # Union des périodes : un segment encore ouvert (`fin` absente) absorbe
        # les autres — le siège n'est pas terminé.
        periode["fin"] = (
            None if periode["fin"] is None or fin is None else max(periode["fin"], fin)
        )
        periode["segments"] += 1

    periodes = sorted(par_siege.values(), key=lambda p: p["debut"], reverse=True)
    for periode in periodes:
        sigle, nom = _groupe_du_mandat(
            mandats, organe_index, periode["debut"], periode["fin"]
        )
        periode["groupe_sigle"] = sigle
        periode["groupe_nom"] = nom
    return periodes


def _build_acteur_identite_index() -> dict[str, dict[str, Any]]:
    """Construit (et met en cache sur disque) un index acteurRef -> champs
    d'identité (civilité, nom complet, profession et ses deux niveaux de
    nomenclature PCS de l'INSEE, date/lieu de naissance, lien HATVP, contact,
    circonscription, place hémicycle, groupe politique actuel, dates/nombre de
    mandats), à partir du jeu de données bulk historique des
    acteurs de l'Assemblée nationale (`AN_ACTEURS_HISTORIQUE_ZIP_URL`,
    partagé avec `_build_organe_index` / `_build_acteur_positions_hemicycle_index`
    via `_ensure_acteurs_historique_zip_downloaded`).

    `groupe_sigle`/`groupe_nom` (issue #369) proviennent du mandat `typeOrgane
    == "GP"` le plus actuel (voir `_select_mandat_par_type_courant`), résolu
    en sigle/nom lisible via `_build_organe_index` (#353) — nécessaire pour
    que ce référentiel puisse remplacer NosDéputés en source primaire
    d'identité sans perdre le groupe politique déclaré.

    Couvre tous les élu⋅e⋅s référencés depuis la XIe législature, actifs ou
    non (issue #354) — contrairement à l'ancien jeu de données `AMO10`
    ("deputes_actifs_mandats_actifs_organes"), limité aux ~577 député⋅e⋅s
    actifs de la législature en cours. Voir docs/technical_decisions.md pour
    le choix de réutiliser ce zip déjà exploité par #353 plutôt que combiner
    les archives `AMO20` par législature comme envisagé initialement dans
    l'issue.

    Circonscription et place hémicycle proviennent du mandat le plus pertinent
    parmi ceux `typeOrgane == "ASSEMBLEE"` (voir _select_mandat_assemblee_courant) :
    `election.lieu.numDepartement/numCirco` et `mandature.placeHemicycle`.

    `mandats_assemblee` (#640) porte, lui, **toutes** les périodes de mandat de
    député, une par siège — voir `_periodes_mandats_assemblee`. Il vit à côté de
    `mandat_debut`/`mandat_fin`, qui restent le couple du mandat courant (ce
    sont eux qui datent la circonscription ci-dessus), et de `nb_mandats`, qui
    reste le compte d'enregistrements AMO30 : c'est leur désaccord silencieux
    qui a produit #640, et c'est lui que la liste rend mesurable.

    Non-fatal en cas d'échec (retourne {})."""
    with _ACTEURS_IDENTITE_LOCK:
        index_path = ACTEURS_HISTORIQUE_CACHE_DIR / NOM_INDEX_IDENTITE
        memoise = _index_historique_memoise(index_path)
        if memoise is not None:
            return memoise
        if index_path.is_file():
            try:
                with open(index_path, encoding="utf-8") as f:
                    return _memoiser_index_historique(index_path, json.load(f))
            except (json.JSONDecodeError, OSError):
                pass  # cache corrompu : on reconstruit

        zip_path = _ensure_acteurs_historique_zip_downloaded()
        if zip_path is None:
            return {}

        # Résolution du groupe politique actuel (organeRef -> sigle/nom, #353)
        # depuis le même zip déjà en cache disque après le premier appel —
        # aucun nouveau téléchargement (issue #369, voir aussi
        # _select_mandat_par_type_courant ci-dessus).
        organe_index = _build_organe_index()

        index: dict[str, dict[str, Any]] = {}
        try:
            with zipfile.ZipFile(zip_path) as zf:
                noms = [n for n in zf.namelist() if n.startswith("json/acteur/") and n.endswith(".json")]
                for nom in noms:
                    try:
                        with zf.open(nom) as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, KeyError):
                        continue
                    acteur = data.get("acteur") if isinstance(data, dict) else None
                    if not isinstance(acteur, dict):
                        continue
                    uid = acteur.get("uid")
                    acteur_ref = uid.get("#text") if isinstance(uid, dict) else uid
                    if not isinstance(acteur_ref, str) or not acteur_ref:
                        continue

                    # #556 — TOUT champ lu ici passe par `_champ_identite_an` :
                    # le convertisseur XML → JSON d'AMO30 ne connaît pas le nom
                    # du champ, donc aucun n'est à l'abri du marqueur `xsi:nil`.
                    # Trois l'ont porté jusqu'au corpus publié (`uri_hatvp` 191,
                    # `profession` 20, `lieu_naissance` 28 profils sur 481) ;
                    # rien ne disait que ce seraient les trois derniers.
                    etat_civil = acteur.get("etatCivil") or {}
                    ident = etat_civil.get("ident") or {}
                    info_naissance = etat_civil.get("infoNaissance") or {}
                    # #641 — la profession passe par SON lecteur, qui retire le
                    # code de nomenclature et refuse de publier l'énoncé d'une
                    # absence de profession comme s'il en était une.
                    bloc_profession = acteur.get("profession") or {}
                    profession = _profession_an(bloc_profession.get("libelleCourant"))
                    # #659 — la nomenclature PCS de l'INSEE, à côté du texte
                    # libre et jamais à sa place : la source classe, on recopie.
                    famille_socpro, categorie_socpro = _socproc_insee_an(bloc_profession)

                    adresses = (acteur.get("adresses") or {}).get("adresse")
                    if isinstance(adresses, dict):
                        adresses = [adresses]
                    contact = _extract_contact(adresses if isinstance(adresses, list) else [])

                    mandats = (acteur.get("mandats") or {}).get("mandat")
                    if isinstance(mandats, dict):
                        mandats = [mandats]
                    mandats = mandats if isinstance(mandats, list) else []

                    numero_departement = numero_circo = place_hemicycle = None
                    mandat_debut = mandat_fin = None
                    mandat_assemblee = _select_mandat_assemblee_courant(mandats)
                    if mandat_assemblee is not None:
                        lieu = (mandat_assemblee.get("election") or {}).get("lieu") or {}
                        numero_departement = _champ_identite_an(lieu.get("numDepartement"))
                        numero_circo = _champ_identite_an(lieu.get("numCirco"))
                        place_hemicycle = _champ_identite_an(
                            (mandat_assemblee.get("mandature") or {}).get("placeHemicycle")
                        )
                        mandat_debut = _champ_identite_an(mandat_assemblee.get("dateDebut"))
                        mandat_fin = _champ_identite_an(mandat_assemblee.get("dateFin"))
                    nb_mandats = sum(1 for m in mandats if isinstance(m, dict) and m.get("typeOrgane") == "ASSEMBLEE")

                    # Groupe politique actuel (#369) : sans ça, le seul champ
                    # groupe_sigle/groupe_nom du profil resterait NosDéputés
                    # uniquement, empêchant de rendre fetch_identity
                    # conditionnel (étape 4 de #369) sans perdre cette donnée.
                    groupe_sigle = groupe_nom = None
                    mandat_gp = _select_mandat_par_type_courant(mandats, "GP")
                    if mandat_gp is not None:
                        organe_gp = organe_index.get((mandat_gp.get("organes") or {}).get("organeRef") or "")
                        if organe_gp:
                            groupe_sigle = organe_gp.get("sigle")
                            groupe_nom = organe_gp.get("nom")

                    # #640 — la LISTE des mandats de député, à côté du couple
                    # unique ci-dessus. `mandat_debut`/`mandat_fin`/`nb_mandats`
                    # sont inchangés : ils portent la circonscription et la
                    # place hémicycle courantes, et `nb_mandats` reste le compte
                    # d'enregistrements AMO30, donc le témoin de couverture avec
                    # lequel `mandats_assemblee` se compare.
                    mandats_assemblee = _periodes_mandats_assemblee(mandats, organe_index)
                    for periode in mandats_assemblee:
                        if periode["debut"] != mandat_debut:
                            continue
                        # La période courante reprend le groupe COURANT plutôt
                        # que celui résolu sur sa fenêtre, pour deux raisons qui
                        # vont dans le même sens : c'est le groupe vrai
                        # aujourd'hui, et c'est la valeur déjà publiée. La clé de
                        # fusion d'un mandat est `(label, categorie, fonction,
                        # debut)` (`merge_profile._pivot_mandat_key`) : un
                        # libellé qui bouge ferait apparaître un DOUBLON de
                        # période au lieu de retrouver l'entrée existante, la
                        # fusion additive ne retirant jamais l'ancienne.
                        periode["groupe_sigle"] = groupe_sigle
                        periode["groupe_nom"] = groupe_nom

                    prenom = _champ_identite_an(ident.get("prenom"))
                    nom_famille = _champ_identite_an(ident.get("nom"))
                    index[acteur_ref] = {
                        "civilite": _champ_identite_an(ident.get("civ")),
                        "prenom": prenom,
                        "nom": nom_famille,
                        "nom_complet": _format_nom_complet(prenom, nom_famille),
                        "profession": profession,
                        "famille_socioprofessionnelle": famille_socpro,
                        "categorie_socioprofessionnelle": categorie_socpro,
                        "groupe_sigle": groupe_sigle,
                        "groupe_nom": groupe_nom,
                        "mandat_debut": mandat_debut,
                        "mandat_fin": mandat_fin,
                        "nb_mandats": nb_mandats,
                        "mandats_assemblee": mandats_assemblee,
                        "date_naissance": _champ_identite_an(info_naissance.get("dateNais")),
                        "lieu_naissance": _format_lieu_naissance(
                            _champ_identite_an(info_naissance.get("villeNais")),
                            _champ_identite_an(info_naissance.get("depNais")),
                            _champ_identite_an(info_naissance.get("paysNais")),
                        ),
                        "uri_hatvp": _champ_identite_an(acteur.get("uri_hatvp")),
                        "contact": contact,
                        "numero_departement": numero_departement,
                        "numero_circo": numero_circo,
                        "place_hemicycle": place_hemicycle,
                    }
        except zipfile.BadZipFile as exc:
            print(f"  [!] Archive de l'historique des acteurs invalide : {exc}")
            return {}

        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False)
        except OSError:
            pass

        return _memoiser_index_historique(index_path, index)


def fetch_identite_officielle(url_an_ou_senat: Optional[str]) -> Optional[dict[str, Any]]:
    """Récupère les champs d'identité officiels (Assemblée nationale) pour un
    député, actif ou non (voir _build_acteur_identite_index, issue #354).
    Retourne None si non trouvé/non applicable (ex. sénateur, ou acteur absent
    du référentiel historique de l'AN)."""
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        return None
    index = _build_acteur_identite_index()
    return index.get(acteur_ref)


def _normalize_search_query(text: str) -> str:
    """Normalise un nom pour la correspondance (minuscules, sans accents).

    Écrite pour le moteur de recherche NosDéputés — qui renvoyait 0 résultat
    sur une requête multi-mots commençant par une majuscule accentuée
    ("Élisabeth Borne") — elle a survécu au retrait de ce moteur (#529) parce
    que les deux index de correspondance slug ↔ acteur AN
    (`_build_acteur_nom_index`, `_resolve_acteur_ref_par_slug`) l'utilisent
    pour aplatir casse et accents des DEUX côtés de la comparaison. Le nom est
    resté le sien : le renommer changerait la seule chose que ce nom garde
    lisible, l'origine de la règle.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return without_accents.lower()


def _build_acteur_nom_index() -> dict[str, list[str]]:
    """Index nom complet normalisé (sans accents/casse, voir
    _normalize_search_query) -> liste des acteur_ref partageant ce nom, à
    partir de `_build_acteur_identite_index`. Permet de résoudre un acteur_ref
    depuis le slug d'un profil (voir fetch_identite_officielle_par_slug, issue
    #355). Une liste de plus d'un acteur_ref pour une même clé signale une
    homonymie dans le référentiel historique AN.

    Les tirets de `nom_complet` sont remplacés par des espaces avant
    normalisation, au même titre que ceux du slug côté appelant
    (`_resolve_acteur_ref_par_slug`) : un prénom composé (ex. "Jean-Luc"
    Mélenchon) garde son tiret dans `nom_complet` mais le slug
    ("jean-luc-melenchon") le remplace par un espace au même titre que le
    séparateur prénom/nom — sans ce traitement symétrique, la clé normalisée
    ne matche jamais ("jean-luc melenchon" vs "jean luc melenchon"), et la
    résolution échoue silencieusement pour tout prénom/nom composé."""
    # Memoise comme les index dont il derive (#467) : purement derive de
    # `_build_acteur_identite_index`, il etait sinon reconstruit — ~7 000
    # acteurs parcourus — a chaque resolution de slug, donc a chaque candidat.
    cle_memo = ACTEURS_HISTORIQUE_CACHE_DIR / "index_nom.derive"
    memoise = _index_historique_memoise(cle_memo)
    if memoise is not None:
        return memoise
    index: dict[str, list[str]] = {}
    for acteur_ref, fiche in _build_acteur_identite_index().items():
        nom_complet = fiche.get("nom_complet")
        if not nom_complet:
            continue
        cle = _normalize_search_query(nom_complet.replace("-", " "))
        index.setdefault(cle, []).append(acteur_ref)
    return _memoiser_index_historique(cle_memo, index)


#: Mémo du repli déclaré ci-dessous : la table absente ne se signale qu'une
#: fois par processus, pas une fois par candidat.
_CORRESPONDANCE_INDISPONIBLE_SIGNALEE = False


def _correspondance_committee() -> Optional[dict[str, Any]]:
    """Table `raw_data/correspondance_acteurs_an.json` (#525), ou None.

    Le repli est **déclaré, jamais muet** : une table introuvable ou invalide
    imprime une ligne nommant le fichier et la cause, une seule fois par
    processus, puis la résolution retombe sur la correspondance par nom. La
    couverture du corpus publié, elle, est un échec dur — mais il appartient
    au quality gate, pas au chemin de collecte : un membre de roster
    nouvellement élu n'a par construction aucune entrée relue.
    """
    global _CORRESPONDANCE_INDISPONIBLE_SIGNALEE
    try:
        return correspondance_acteurs_an.charger_correspondance()
    except correspondance_acteurs_an.CorrespondanceInvalide as exc:
        if not _CORRESPONDANCE_INDISPONIBLE_SIGNALEE:
            print(f"  [!] Correspondance slug ↔ acteur AN indisponible : {exc}")
            print("      Repli sur la correspondance par nom (#525).")
            _CORRESPONDANCE_INDISPONIBLE_SIGNALEE = True
        return None


def _resolve_acteur_ref_par_slug(slug: str, *, utiliser_table: bool = True) -> Optional[str]:
    """Résout un acteur_ref AN (ex. "PA2150") depuis un slug NosDéputés.fr
    (ex. "jean-luc-melenchon").

    Deux sources, dans cet ordre (#525) :

      1. la **table committée** `raw_data/correspondance_acteurs_an.json`, qui
         porte pour chaque slug publié son `acteur_ref`, l'état civil retenu,
         la preuve et la date de vérification. Une entrée déclarée sans acteur
         AN (`jordan-bardella`, député européen) renvoie None **sans** repli :
         c'est un fait vérifié, pas une absence à combler ;
      2. à défaut d'entrée, la correspondance par nom sur
         `_build_acteur_nom_index` (nom normalisé "jean luc melenchon"), sans
         appel réseau préalable à NosDéputés. Elle renvoie None si le slug ne
         correspond à aucun acteur du référentiel, ou à plusieurs (homonymie :
         on renonce plutôt que de risquer une mauvaise attribution).

    La table passe devant parce qu'elle tranche ce que la normalisation ne
    peut pas trancher : apostrophe (`loic-prud-homme`), nom d'usage
    (`sabrina-agresti-roubache`), changement de nom (`guillaume-gouffier-cha`)
    et surtout homonymie réelle (`alexandra-martin` / `alexandra-martin-1`,
    deux députées que l'AN ne distingue que par leur département).

    `utiliser_table=False` court-circuite l'étape 1 — c'est ce dont
    `build_correspondance_acteurs_an.py` a besoin pour construire la table
    sans la relire.
    """
    if utiliser_table:
        table = _correspondance_committee()
        if table is not None:
            entree = table.get(slug)
            if entree is not None:
                return entree["acteur_ref"]

    nom_index = _build_acteur_nom_index()
    matches = nom_index.get(_normalize_search_query(slug.replace("-", " ")))
    if not matches or len(matches) != 1:
        return None
    return matches[0]


class ActeurContreditParLaTable(ValueError):
    """Le roster et la table committée nomment deux acteurs AN pour un même slug (#850)."""


def fetch_identite_officielle_par_slug(
    slug: str, acteur_ref: Optional[str] = None
) -> tuple[Optional[dict[str, Any]], Optional[str]]:
    """Résout l'identité officielle AN directement depuis le slug NosDéputés.fr,
    sans appel réseau préalable à NosDéputés pour en extraire l'URL AN —
    permet d'utiliser le référentiel historique AN comme source primaire de
    `fetch_identity` pour les députés (issue #355). Renvoie (fiche, acteur_ref)
    si trouvé, (None, None) sinon (absent du référentiel, ou homonymie — voir
    _resolve_acteur_ref_par_slug).

    ## `acteur_ref` : l'acteur que l'appelant CONNAÎT déjà (#850)

    Un membre de roster arrive avec son acteur AN : c'est l'organe de groupe
    d'AMO30 qui l'a désigné. Le re-résoudre depuis le slug revenait à le
    **deviner** par son nom, et la correspondance par nom échoue là où le slug a
    perdu de l'information — l'apostrophe de `claire o'petit`, la barre
    d'`emeline k/bidi` — ou renonce, à raison, devant deux homonymes
    (`beatrice-descamps` : PA392736 et PA720696). Six membres de roster étaient
    ainsi « introuvables » au run `34575181245`, alors que le roster les
    nommait. Fourni, l'acteur passe donc devant toute résolution.

    **Sauf s'il contredit la table committée**, qui a tranché ce slug par une
    relecture ou une dérivation : alors rien n'est collecté, et l'exception
    nomme les deux acteurs. Un désaccord ne se tranche pas en silence — c'est la
    règle que #757 applique déjà à l'écriture d'une entrée. Mesuré le
    11/09/2026 : **0** contradiction sur les 1 174 entrées de la table.
    """
    if acteur_ref:
        table = _correspondance_committee()
        entree = table.get(slug) if table else None
        if entree is not None and entree.get("acteur_ref") not in (None, acteur_ref):
            raise ActeurContreditParLaTable(
                f"{slug} : le roster nomme {acteur_ref}, la table committée "
                f"{entree.get('acteur_ref')}. Aucune collecte sous ce slug tant "
                "que les deux ne s'accordent pas (#850, #757)."
            )
        return _build_acteur_identite_index().get(acteur_ref), acteur_ref
    acteur_ref = _resolve_acteur_ref_par_slug(slug)
    if not acteur_ref:
        return None, None
    return _build_acteur_identite_index().get(acteur_ref), acteur_ref


def acteur_ref_to_pseudo_url(acteur_ref: str) -> str:
    """URL de la fiche AN d'un acteur, construite depuis son `acteur_ref`
    (ex. "PA2150") : `https://www2.assemblee-nationale.fr/deputes/fiche/OMC_PA2150`.

    Le format vient du champ `url_an` que NosDéputés publiait ; il est
    aujourd'hui la seule URL de fiche du pipeline, et il reste **vérifiable** —
    c'est ce que la règle 2 demande d'une `source_url`. Tous les appels
    officiels AN (votes, amendements, textes, questions, positions hémicycle,
    interventions) n'ont besoin que d'en réextraire l'acteur_ref via
    `_extract_acteur_ref`, peu importe la forme exacte de l'URL.

    Publique (sans underscore) depuis #529 : `generate_roster_candidats` en a
    besoin pour la `source` d'une entrée de roster, qui pointait jusque-là vers
    `www.nosdeputes.fr/<slug>`.
    """
    return f"https://www2.assemblee-nationale.fr/deputes/fiche/OMC_{acteur_ref}"


#: Alias interne historique. Conservé parce qu'il est appelé une quinzaine de
#: fois dans le module et dans les tests, et qu'un renommage de plus n'apporte
#: rien ici.
_acteur_ref_to_pseudo_url = acteur_ref_to_pseudo_url


# Correspondance organe.positionPolitique (référentiel officiel Assemblée
# nationale) -> valeur du schéma pivot.
#
# Canonique dans `schema_pivot` depuis #686 : la fiche de groupe publie la même
# qualification, tirée du même champ de la même archive. Deux copies de cette
# table auraient dérivé le jour où l'AN ajoute une quatrième valeur.
_POSITION_POLITIQUE_MAP: dict[str, str] = POSITION_POLITIQUE_AN_VERS_PIVOT


def _build_organe_positions_index(zf: zipfile.ZipFile) -> dict[str, dict[str, Any]]:
    """Construit un index organeRef -> {groupe_sigle, position} à partir des
    organes de type "GP" (groupe politique) et "GOUVERNEMENT" (fonction
    ministérielle) du zip acteurs historique.

    Pour un organe "GP", ne conserve que ceux dont positionPolitique est
    qualifié par l'AN (jamais le cas pour la législature en cours, voir
    AN_ACTEURS_HISTORIQUE_ZIP_URL). Pour un organe "GOUVERNEMENT" (ex. libellé
    "BORNE", "CASTEX"), la position est toujours "gouvernement" : l'AN ne
    qualifie pas ces organes par positionPolitique, mais leur codeType suffit
    à identifier sans ambiguïté une période d'appartenance à l'exécutif
    (voir KNOWN_POSITIONS_HEMICYCLE, schema_pivot.py). Note : le référentiel
    AN ne distingue pas le portefeuille ministériel précis (ex. "Ministre de
    l'Intérieur") au sein d'un même gouvernement, seulement le gouvernement
    d'appartenance (libelleAbrege)."""
    index: dict[str, dict[str, Any]] = {}
    noms = [n for n in zf.namelist() if n.startswith("json/organe/") and n.endswith(".json")]
    for nom in noms:
        try:
            with zf.open(nom) as f:
                data = json.load(f)
        except (json.JSONDecodeError, KeyError):
            continue
        organe = data.get("organe") if isinstance(data, dict) else None
        if not isinstance(organe, dict):
            continue
        code_type = organe.get("codeType")
        if code_type == "GOUVERNEMENT":
            position = "gouvernement"
        elif code_type == "GP":
            position = _POSITION_POLITIQUE_MAP.get(organe.get("positionPolitique"))
            if position is None:
                continue
        else:
            continue
        organe_ref = organe.get("uid")
        if not isinstance(organe_ref, str) or not organe_ref:
            continue
        index[organe_ref] = {
            "groupe_sigle": organe.get("libelleAbrege"),
            "position": position,
        }
    return index


def _ensure_acteurs_historique_zip_downloaded() -> Optional[Path]:
    """Télécharge (si absente du cache disque) l'archive bulk historique des
    acteurs/mandats/organes de l'Assemblée nationale (AN_ACTEURS_HISTORIQUE_ZIP_URL)
    et retourne son chemin local. Partagée entre plusieurs index construits à
    partir du même zip (_build_acteur_positions_hemicycle_index,
    _build_organe_index) : un seul téléchargement, jamais deux en parallèle.
    Retourne None en cas d'échec (non-fatal pour l'appelant)."""
    with _ACTEURS_HISTORIQUE_ZIP_LOCK:
        zip_path = ACTEURS_HISTORIQUE_CACHE_DIR / "acteurs_historique.zip"
        if zip_path.is_file():
            return zip_path

        print(f"-> Téléchargement de l'historique des acteurs (Assemblée nationale) : {AN_ACTEURS_HISTORIQUE_ZIP_URL}")
        try:
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            download_with_watchdog(AN_ACTEURS_HISTORIQUE_ZIP_URL, zip_path, headers=HEADERS, timeout=TIMEOUT)
        except (requests.RequestException, OSError, TimeoutError) as exc:
            print(f"  [!] Échec du téléchargement de l'historique des acteurs : {exc}")
            return None
        return zip_path


def _build_acteur_positions_hemicycle_index() -> dict[str, list[dict[str, Any]]]:
    """Construit (et met en cache sur disque) un index acteurRef -> liste de
    périodes datées d'appartenance à un groupe politique qualifié majorité/
    opposition/minoritaire par le référentiel officiel de l'Assemblée nationale,
    ainsi que les périodes d'appartenance à un gouvernement (fonction
    ministérielle, position "gouvernement").

    Limitation connue : la qualification majorité/opposition/minoritaire ne
    couvre que les législatures achevées (positionPolitique n'est jamais
    renseigné par l'AN pour la législature en cours, voir
    AN_ACTEURS_HISTORIQUE_ZIP_URL) ; les périodes gouvernementales n'ont pas
    cette limitation (codeType == "GOUVERNEMENT" est toujours renseigné).
    Non-fatal en cas d'échec (retourne {})."""
    with _ACTEURS_HEMICYCLE_LOCK:
        index_path = ACTEURS_HISTORIQUE_CACHE_DIR / "index_positions_hemicycle.json"
        memoise = _index_historique_memoise(index_path)
        if memoise is not None:
            return memoise
        if index_path.is_file():
            try:
                with open(index_path, encoding="utf-8") as f:
                    return _memoiser_index_historique(index_path, json.load(f))
            except (json.JSONDecodeError, OSError):
                pass  # cache corrompu : on reconstruit

        zip_path = _ensure_acteurs_historique_zip_downloaded()
        if zip_path is None:
            return {}

        index: dict[str, list[dict[str, Any]]] = {}
        try:
            with zipfile.ZipFile(zip_path) as zf:
                organe_positions = _build_organe_positions_index(zf)
                if not organe_positions:
                    return {}

                noms = [n for n in zf.namelist() if n.startswith("json/acteur/") and n.endswith(".json")]
                for nom in noms:
                    try:
                        with zf.open(nom) as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, KeyError):
                        continue
                    acteur = data.get("acteur") if isinstance(data, dict) else None
                    if not isinstance(acteur, dict):
                        continue
                    uid = acteur.get("uid")
                    acteur_ref = uid.get("#text") if isinstance(uid, dict) else uid
                    if not isinstance(acteur_ref, str) or not acteur_ref:
                        continue

                    mandats = (acteur.get("mandats") or {}).get("mandat")
                    if isinstance(mandats, dict):
                        mandats = [mandats]
                    if not isinstance(mandats, list):
                        continue

                    for mandat in mandats:
                        if not isinstance(mandat, dict) or mandat.get("typeOrgane") not in ("GP", "GOUVERNEMENT"):
                            continue
                        organe_ref = (mandat.get("organes") or {}).get("organeRef")
                        organe = organe_positions.get(organe_ref)
                        if not organe:
                            continue
                        index.setdefault(acteur_ref, []).append({
                            "legislature": mandat.get("legislature"),
                            "groupe_sigle": organe["groupe_sigle"],
                            "position": organe["position"],
                            "debut": mandat.get("dateDebut"),
                            "fin": mandat.get("dateFin"),
                        })
        except zipfile.BadZipFile as exc:
            print(f"  [!] Archive de l'historique des acteurs invalide : {exc}")
            return {}

        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False)
        except OSError:
            pass

        return _memoiser_index_historique(index_path, index)


def fetch_positions_hemicycle_officielles(url_an_ou_senat: Optional[str]) -> list[dict[str, Any]]:
    """Récupère les périodes d'appartenance à un groupe politique qualifiées
    majorité/opposition/minoritaire, ainsi que les périodes d'appartenance à
    un gouvernement (position "gouvernement"), par le référentiel officiel de
    l'Assemblée nationale (voir _build_acteur_positions_hemicycle_index). La
    qualification majorité/opposition/minoritaire ne couvre que les législatures
    achevées : retourne [] si aucune période qualifiée n'existe (législature en
    cours sans fonction gouvernementale, sénateur, ou acteur absent du
    référentiel)."""
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        return []
    index = _build_acteur_positions_hemicycle_index()
    return index.get(acteur_ref, [])


def _build_organe_index() -> dict[str, dict[str, Any]]:
    """Construit (et met en cache sur disque) un index organeRef -> {sigle,
    nom, type} pour TOUS les organes (commissions permanentes/spéciales,
    groupes politiques, groupes d'amitié, missions d'information, engagements
    extra-parlementaires, gouvernements...) du référentiel historique de
    l'Assemblée nationale, à partir du même zip que
    _build_acteur_positions_hemicycle_index (json/organe/*.json).

    Contrairement à _build_organe_positions_index (limité aux organes de type
    "GP"/"GOUVERNEMENT" qualifiés majorité/opposition/minoritaire), cet index
    couvre tous les codeType sans filtrage : prérequis générique pour
    résoudre mandats[].organes.organeRef (ex. "PO59048" -> commission des
    finances) vers un nom lisible, quel que soit le type d'organe (issue #353).

    "sigle" = organe.libelleAbrege (nom court, ex. "Finances"), "nom" =
    organe.libelle (nom complet, ex. "Commission des finances, de l'économie
    générale et du contrôle budgétaire"), "type" = organe.codeType (ex.
    "COMPER", "GP", "GA", "MISINFO", "GOUVERNEMENT"...). Non-fatal en cas
    d'échec (retourne {})."""
    with _ACTEURS_ORGANES_LOCK:
        index_path = ACTEURS_HISTORIQUE_CACHE_DIR / NOM_INDEX_ORGANES
        memoise = _index_historique_memoise(index_path)
        if memoise is not None:
            return memoise
        if index_path.is_file():
            try:
                with open(index_path, encoding="utf-8") as f:
                    return _memoiser_index_historique(index_path, json.load(f))
            except (json.JSONDecodeError, OSError):
                pass  # cache corrompu : on reconstruit

        zip_path = _ensure_acteurs_historique_zip_downloaded()
        if zip_path is None:
            return {}

        index: dict[str, dict[str, Any]] = {}
        try:
            with zipfile.ZipFile(zip_path) as zf:
                noms = [n for n in zf.namelist() if n.startswith("json/organe/") and n.endswith(".json")]
                for nom in noms:
                    try:
                        with zf.open(nom) as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, KeyError):
                        continue
                    organe = data.get("organe") if isinstance(data, dict) else None
                    if not isinstance(organe, dict):
                        continue
                    organe_ref = organe.get("uid")
                    if not isinstance(organe_ref, str) or not organe_ref:
                        continue
                    # `_champ_identite_an` sur les trois : un organe dont le
                    # libellé abrégé est déclaré vide rend le marqueur `xsi:nil`
                    # comme partout ailleurs, et ce sigle finit dans le libellé
                    # d'un mandat publié (#556).
                    index[organe_ref] = {
                        "sigle": _champ_identite_an(organe.get("libelleAbrege")),
                        "nom": _champ_identite_an(organe.get("libelle")),
                        "type": _champ_identite_an(organe.get("codeType")),
                    }
        except zipfile.BadZipFile as exc:
            print(f"  [!] Archive de l'historique des acteurs invalide : {exc}")
            return {}

        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False)
        except OSError:
            pass

        return _memoiser_index_historique(index_path, index)


def fetch_organe(organe_ref: Optional[str]) -> Optional[dict[str, Any]]:
    """Résout un organeRef (ex. mandats[].organes.organeRef, "PO59048") vers
    {sigle, nom, type} via le référentiel historique de l'Assemblée nationale
    (voir _build_organe_index). Retourne None si organe_ref est vide/absent
    ou introuvable dans le référentiel."""
    if not organe_ref:
        return None
    index = _build_organe_index()
    return index.get(organe_ref)


# Mapping typeOrgane (AN, mandats[].typeOrgane) -> categorie du schema pivot
# (schema_pivot.KNOWN_CATEGORIES), pour que _extract_mandats_officiels
# produise la meme forme de sortie quelle que soit la source (issue #369).
#
# Perimetre elargi par #382/#383 (option "mixte") : le perimetre initial de
# #369 se limitait aux 3 categories deja couvertes par nosdeputes.fr, ce qui
# laissait de cote ~3150 mandats sur 6423 mesures (65 profils resolus AN) -
# presque la moitie du referentiel. Ces mandats existaient malgre tout dans
# les profils, mais uniquement parce que la fusion additive preservait des
# entrees heritees de l'ere NosDeputes, ou _extract_mandats les mappait
# TOUTES en dur vers "commission" : d'ou 197 libelles sur 246 classes
# "Commission" sans en etre (voir #379 et
# docs/decisions/taxonomie-mandats-typeorgane-an.md).
#
# Granularite retenue : une categorie par nature institutionnelle reellement
# distincte pour le lecteur, pas une par typeOrgane - les variantes internes
# sont regroupees (MISINFO/MISINFOCOM/MISINFOPRE, CNPE/CNPS, GE/GEVI,
# DELEG/API/OFFPAR).
#: Valeur de `mandats[].categorie_source` pour tout mandat dont la catégorie
#: est établie par le référentiel de l'Assemblée nationale (#718). Importée du
#: schéma pour qu'une seule fabrique porte le vocabulaire.
CATEGORIE_SOURCE_AN = "an"

_TYPE_ORGANE_TO_CATEGORIE: dict[str, str] = {
    # Commissions permanentes et assimilees.
    "COMPER": "commission",
    "COMNL": "commission",          # commissions non legislatives (affaires europeennes...)
    # Commissions temporaires d'investigation : distinctes d'une commission
    # permanente, c'est tout l'objet de la nouvelle categorie.
    "CNPE": "commission_enquete",   # commissions d'enquete
    "CNPS": "commission_enquete",   # commissions speciales
    # Missions d'information (3 variantes AN, meme nature editoriale).
    "MISINFO": "mission_information",
    "MISINFOCOM": "mission_information",
    "MISINFOPRE": "mission_information",
    # Groupes d'etudes, thematiques (GE) et a vocation internationale (GEVI).
    "GE": "groupe_etudes",
    "GEVI": "groupe_etudes",
    # Delegations permanentes de l'AN, delegations aux assemblees
    # parlementaires internationales, offices parlementaires.
    "DELEG": "delegation",
    "DELEGBUREAU": "delegation",
    "API": "delegation",
    "OFFPAR": "delegation",
    # Groupes d'amitie et organismes extra-parlementaires (perimetre #369).
    "GA": "groupe_amitie",
    "ORGEXTPARL": "extra_parlementaire",
    # Instances de direction de l'assemblee : reelles mais sans categorie
    # dediee justifiee par le volume (35 mandats), rangees dans "autre"
    # plutot que de creer une categorie pour deux organes.
    "BUREAU": "autre",
    "CONFPT": "autre",
    # Portefeuille ministeriel precis (#383) : "Ministere de la cohesion des
    # territoires", "Secretariat d'Etat aupres du ministre de...", 52
    # intitules distincts. Complete (sans le remplacer) le rattachement au
    # gouvernement produit par fetch_positions_hemicycle_officielles, qui ne
    # donne que le gouvernement d'appartenance ("Gouvernement (BORNE)").
    # Leve la limitation documentee dans #hors-perimetre, qui affirmait
    # qu'aucune source open data n'exposait ce niveau de detail.
    "MINISTERE": "fonction_gouvernementale",
}

# typeOrgane volontairement NON mappes, avec la raison - explicites plutot
# qu'omis, pour que ce perimetre reste reevaluable (le silence de #369 sur
# ces types avait rendu son propre perimetre difficile a rediscuter) :
#
# - "ASSEMBLEE"    : c'est le mandat electif lui-meme, deja produit ailleurs
#                    (voir _build_acteur_identite_index / mandat_electif).
# - "GP"           : groupe politique parlementaire, deja collecte par
#                    fetch_positions_hemicycle_officielles -> groupe_politique.
# - "GOUVERNEMENT" : rattachement gouvernemental, deja collecte par la meme
#                    fonction -> fonction_gouvernementale. Le mapper ici
#                    creerait un doublon (MINISTERE ci-dessus apporte le
#                    detail manquant, pas une redite).
# - "CMP"          : commissions mixtes paritaires (616 mandats) - organe
#                    temporaire cree par texte de loi, une entree par texte.
#                    Les agreger au niveau groupe noierait les instances
#                    permanentes sous des centaines d'entrees a membre unique
#                    (#383).
# - "PARPOL"       : partis politiques (222). Recoupe conceptuellement le
#                    champ `parti` du pivot et la categorie groupe_politique ;
#                    l'exposer comme mandat mele appartenance partisane et
#                    mandat institutionnel. Arbitrage distinct, hors #382.
# - types Senat    : DELEGSENAT/COMSENAT/GROUPESENAT/SENAT (4 mandats) -
#                    volume negligeable, et le Senat n'a pas d'equivalent de
#                    ce referentiel cote collecte.
# - "CJR"          : Cour de justice de la Republique (1 mandat).
_TYPE_ORGANE_NON_MAPPES: frozenset[str] = frozenset({
    "ASSEMBLEE", "GP", "GOUVERNEMENT", "CMP", "PARPOL",
    "DELEGSENAT", "COMSENAT", "GROUPESENAT", "SENAT", "CJR",
})


def _build_acteur_mandats_index() -> dict[str, list[dict[str, Any]]]:
    """Construit (et met en cache sur disque) un index acteurRef -> liste de
    mandats (commissions, groupes d'amitié, engagements extra-parlementaires),
    à partir du même zip que `_build_acteur_identite_index`/`_build_organe_index`
    (issue #369 — complète #353 : l'organeRef de chaque mandat était déjà
    résolvable en nom lisible via `fetch_organe`, mais rien ne l'exploitait
    encore pour peupler `profile["mandats"]`, qui restait entièrement sourcé
    depuis NosDéputés).

    Périmètre : `typeOrgane` ∈ `_TYPE_ORGANE_TO_CATEGORIE` uniquement — le
    mandat électif de base (`ASSEMBLEE`) et le groupe politique/fonction
    gouvernementale (`GP`/`GOUVERNEMENT`) restent gérés séparément (étapes 5
    et 5bis de `build_profile`), pas dupliqués ici.

    Non-fatal en cas d'échec (retourne {})."""
    with _ACTEURS_MANDATS_LOCK:
        index_path = ACTEURS_HISTORIQUE_CACHE_DIR / "index_mandats.json"
        memoise = _index_historique_memoise(index_path)
        if memoise is not None:
            return memoise
        if index_path.is_file():
            try:
                with open(index_path, encoding="utf-8") as f:
                    return _memoiser_index_historique(index_path, json.load(f))
            except (json.JSONDecodeError, OSError):
                pass  # cache corrompu : on reconstruit

        zip_path = _ensure_acteurs_historique_zip_downloaded()
        if zip_path is None:
            return {}

        index: dict[str, list[dict[str, Any]]] = {}
        try:
            with zipfile.ZipFile(zip_path) as zf:
                noms = [n for n in zf.namelist() if n.startswith("json/acteur/") and n.endswith(".json")]
                for nom in noms:
                    try:
                        with zf.open(nom) as f:
                            data = json.load(f)
                    except (json.JSONDecodeError, KeyError):
                        continue
                    acteur = data.get("acteur") if isinstance(data, dict) else None
                    if not isinstance(acteur, dict):
                        continue
                    uid = acteur.get("uid")
                    acteur_ref = uid.get("#text") if isinstance(uid, dict) else uid
                    if not isinstance(acteur_ref, str) or not acteur_ref:
                        continue

                    mandats = (acteur.get("mandats") or {}).get("mandat")
                    if isinstance(mandats, dict):
                        mandats = [mandats]
                    if not isinstance(mandats, list):
                        continue

                    entries: list[dict[str, Any]] = []
                    for mandat in mandats:
                        if not isinstance(mandat, dict):
                            continue
                        type_organe = mandat.get("typeOrgane")
                        if type_organe not in _TYPE_ORGANE_TO_CATEGORIE:
                            continue
                        organe_ref = (mandat.get("organes") or {}).get("organeRef")
                        # `organeRef` est parfois une LISTE dans le dataset AN
                        # (un mandat rattaché à plusieurs organes) : cas absent
                        # des 3 typeOrgane du périmètre initial (#369), révélé
                        # par l'élargissement de #382. Sans ce garde-fou,
                        # `fetch_organe` lève `TypeError: unhashable type` sur
                        # un lookup de dict par liste. On retient le premier
                        # organe : le libellé du mandat lui vient de toute
                        # façon d'un seul organe, et un mandat sans organe
                        # résolvable serait ignoré juste après.
                        if isinstance(organe_ref, list):
                            organe_ref = organe_ref[0] if organe_ref else None
                        if not organe_ref or not isinstance(organe_ref, str):
                            continue
                        fin = mandat.get("dateFin")
                        entries.append({
                            "categorie": _TYPE_ORGANE_TO_CATEGORIE[type_organe],
                            "organe_ref": organe_ref,
                            "fonction": (mandat.get("infosQualite") or {}).get("libQualite"),
                            "debut": mandat.get("dateDebut"),
                            "fin": fin,
                            "actif": not fin,
                        })
                    if entries:
                        index[acteur_ref] = entries
        except zipfile.BadZipFile as exc:
            print(f"  [!] Archive de l'historique des acteurs invalide : {exc}")
            return {}

        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump(index, f, ensure_ascii=False)
        except OSError:
            pass

        return _memoiser_index_historique(index_path, index)


def _extract_mandats_officiels(acteur_ref: str) -> list[dict[str, Any]]:
    """Équivalent de `_extract_mandats`, sourcé depuis le référentiel officiel
    de l'Assemblée nationale plutôt que NosDéputés (issue #369) : commissions,
    groupes d'amitié, engagements extra-parlementaires, avec `organeRef`
    résolu en nom lisible via `fetch_organe` (#353).

    Ne couvre pas le mandat électif de base ni le groupe politique/fonction
    gouvernementale — traités séparément (étapes 5/5bis de `build_profile`),
    pour rester équivalent à `_extract_mandats` qui construit son mandat
    électif à part des responsabilités."""
    mandats: list[dict[str, Any]] = []
    for entry in _build_acteur_mandats_index().get(acteur_ref, []):
        organe = fetch_organe(entry.get("organe_ref"))
        label = (organe or {}).get("nom") or (organe or {}).get("sigle")
        if not label:
            continue
        mandats.append({
            "categorie": entry["categorie"],
            "type": entry.get("fonction") or "membre",
            "label": label,
            "debut": entry.get("debut"),
            "fin": entry.get("fin"),
            "actif": entry.get("actif", False),
            # #718 — la catégorie vient du `codeType` de l'organe, via
            # `_TYPE_ORGANE_TO_CATEGORIE`. L'estampiller ici est ce qui permet
            # de distinguer, dans un corpus où la fusion est additive, un mandat
            # dont un référentiel a établi la nature d'un mandat hérité de
            # NosDéputés que rien ne qualifie plus.
            "categorie_source": CATEGORIE_SOURCE_AN,
        })
    return mandats


def fetch_amendements_officiels(
    url_an_ou_senat: Optional[str], warnings: Optional[list[str]] = None
) -> list[dict[str, Any]]:
    """Récupère les amendements officiels dont le parlementaire est l'auteur principal.

    Agrège sur toutes les législatures pour lesquelles l'Assemblée nationale
    publie ces données en open data (voir AN_AMENDEMENTS_PATH), pas seulement
    celle de la source d'identité : un même élu peut avoir déposé des
    amendements sous plusieurs législatures successives.

    Chaque législature est tentée indépendamment : l'absence de cache pour une
    législature (ex. légis 16, chroniquement instable côté téléchargement)
    n'interrompt plus l'agrégation des autres — corrige un défaut où la
    première législature en échec empêchait même d'essayer les suivantes,
    faisant perdre par exemple une légis 17 pourtant disponible (issue #241).
    Si `warnings` est fourni, un message `WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES`
    précisant la législature concernée y est ajouté pour chaque absence, au
    lieu d'un échec binaire global.

    Lecture cache-only exclusivement (`_read_cached_amendements_acteur`, #250) :
    ne déclenche jamais de téléchargement depuis ce chemin. La construction de
    l'index (téléchargement + parsing de l'archive AN) est désormais la seule
    responsabilité du job CI dédié `extract-amendements-an`
    (`src/build_amendements_index.py`, #251) — sous-issue 4/6 de #248, pour
    que le coût réseau ne soit plus payé indépendamment par chaque job
    consommateur (`extract-an`/`extract-roster-groupes`, issues #239/#245/#246).

    Depuis #377, seules les entrées de `acteur_ref` sont matérialisées sous
    forme complète, à partir du cache dédupliqué — l'index entier de la
    législature n'est plus expansé en mémoire pour n'en lire qu'une fraction.

    Un `url_an_ou_senat` absent ou non parsable produit une liste vide AVEC un
    warning (#265, fix 5) : cet appel n'a lieu que pour `chambre ==
    "deputes"` (voir `build_profile`), donc l'impossibilité d'en extraire un
    acteurRef est toujours une anomalie — jamais le cas normal d'un sénateur
    ou d'un MEP, qui n'atteignent pas ce chemin. Sans ce warning, le résultat
    était un zéro parfaitement silencieux, indiscernable d'une absence
    légitime d'amendements : constaté en pratique sur des profils dont
    l'identité avait été écrite partiellement par un run interrompu.
    """
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        if warnings is not None:
            warnings.append(avertissement(
                f"{WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES} : identifiant Assemblée nationale "
                f"introuvable pour ce profil (url_an_ou_senat={url_an_ou_senat!r}) — "
                "aucun amendement ne peut être collecté",
                # Nomme une variable du dépôt : c'est un diagnostic (#642).
                DESTINATAIRE_INTERNE,
            ))
        return []

    amendements: list[dict[str, Any]] = []
    for legislature in AN_AMENDEMENTS_PATH:
        records = _read_cached_amendements_acteur(legislature, acteur_ref)
        if records is None:
            if warnings is not None:
                warnings.append(avertissement(
                    f"{WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES} (législature {legislature}) : "
                    "index en cache absent (job extract-amendements-an non exécuté ou en échec pour cette législature)",
                    # Nomme un job de CI : diagnostic (#642).
                    DESTINATAIRE_INTERNE,
                ))
            continue
        for record in records:
            # Normalisation À LA LECTURE, et pas seulement au parsing : les
            # index des trois législatures figées sont COMMITTÉS
            # (`AN_AMENDEMENTS_FIGEES_DIR`) et ne sont pas reconstruits par la
            # CI — 8 d'entre eux portent déjà le marqueur `xsi:nil` en `date`,
            # et il faudrait rejouer `build_amendements_index_figees.py` sur
            # 350-650 Mo d'archives hors CI pour les en purger. Corriger la
            # seule écriture laisserait donc les 99 profils de #562 cassés.
            amendements.append({
                **record,
                "date": _texte_an(record.get("date")),
                "texte_vise": _texte_an(record.get("texte_vise")),
                "legislature": legislature,
            })

    # Tri sûr parce que `date` vient d'être normalisée en `str | None` juste
    # au-dessus : c'est CE tri qui levait
    # `'<' not supported between instances of 'dict' and 'str'` sur 99 profils
    # publiés sur 481 (#562), pour 8 amendements portant un `dateDepot` nil.
    amendements.sort(key=lambda a: a.get("date") or "", reverse=True)
    return amendements


#: `JJ/MM/AAAA`, la seule forme non-ISO que `dateJO` publie (#1044).
_DATE_JO_JOUR_MOIS_AN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def normaliser_date_jo(valeur: Any) -> Optional[str]:
    """`dateJO` en ISO, ou `None` — jamais une date devinée (#1044).

    **Le reste du corpus est en ISO ; cette collecte ne l'était pas.** La
    source publie `infoJO.dateJO` tantôt en `AAAA-MM-JJ`, tantôt en
    `JJ/MM/AAAA`, et l'entrée était recopiée telle quelle. Mesuré le
    20/09/2026 sur les 1 217 384 interventions publiées : **715 en
    `JJ/MM/AAAA`**, sur 12 profils `candidat_declare`, toutes des questions.

    Ce que ça coûtait : les filtres par période comparent des chaînes ISO, donc
    ces entrées ne tombaient dans **aucune** fenêtre et disparaissaient sans
    être comptées comme écartées.

    **Reformater n'est pas deviner** : le jour désigné ne change pas. Une
    valeur vide ou d'une forme inconnue rend `None` — les 167 entrées sans
    `dateJO` restent une absence, à déclarer et non à combler (§2 règle 5).
    """
    if not isinstance(valeur, str):
        return None
    valeur = valeur.strip()
    if not valeur:
        return None
    m = _DATE_JO_JOUR_MOIS_AN.match(valeur)
    if m:
        jour, mois, annee = m.groups()
        return f"{annee}-{mois}-{jour}"
    return valeur


def _parse_question_entry(data: dict, sous_type: str) -> Optional[tuple[str, dict[str, Any]]]:
    """Parse une entrée de question AN (QE/QG/QOSD) et retourne (acteur_ref, record) ou None.

    `data` est un dict issu du JSON d'une question (contenant une clé "question").
    `sous_type` est "QE", "QG" ou "QOSD" (dérivé du dossier/fichier de provenance).
    """
    question = data.get("question")
    if not isinstance(question, dict):
        return None

    auteur = question.get("auteur") or {}
    identite_auteur = auteur.get("identite") or {}
    acteur_ref = identite_auteur.get("acteurRef")
    if not acteur_ref:
        return None

    uid = question.get("uid")

    # Sujet court (indexation AN — peut être une chaîne ou une liste de chaînes).
    # #1094 — la XVe législature le range sous `ANALYSE.ANA`, en capitales, et
    # jamais sous `analyses.analyse` : 52 213 questions sur 52 213 (QE, QG,
    # QOSD, mesuré le 22/09/2026 sur les archives AN). Lu à la seule clé des
    # XVIe et XVIIe, leur sujet était publié `null`.
    indexation = question.get("indexationAN") or {}
    analyses = indexation.get("analyses") or indexation.get("ANALYSE") or {}
    analyse = analyses.get("analyse") or analyses.get("ANA")
    if isinstance(analyse, list):
        analyse = " ; ".join(str(a) for a in analyse if a)
    elif not isinstance(analyse, str):
        analyse = None

    # Texte de la question + date JO (texteQuestion peut être un dict ou une liste de dicts).
    textes_question = question.get("textesQuestion") or {}
    texte_q_block = textes_question.get("texteQuestion")
    if isinstance(texte_q_block, list):
        texte_q_block = texte_q_block[-1] if texte_q_block else {}
    if not isinstance(texte_q_block, dict):
        texte_q_block = {}
    texte_question = texte_q_block.get("texte") if isinstance(texte_q_block.get("texte"), str) else None
    info_jo_q = texte_q_block.get("infoJO") or {}
    date_question = normaliser_date_jo(info_jo_q.get("dateJO"))

    # Texte de la réponse + date JO (optionnel, absent si la question n'a pas encore reçu de réponse).
    textes_reponse = question.get("textesReponse") or {}
    texte_r_block = textes_reponse.get("texteReponse")
    if isinstance(texte_r_block, list):
        texte_r_block = texte_r_block[-1] if texte_r_block else None
    reponse: Optional[str] = None
    date_reponse: Optional[str] = None
    if isinstance(texte_r_block, dict):
        reponse = texte_r_block.get("texte") if isinstance(texte_r_block.get("texte"), str) else None
        info_jo_r = texte_r_block.get("infoJO") or {}
        date_reponse = normaliser_date_jo(info_jo_r.get("dateJO"))

    # Une question au gouvernement est posée à l'oral : la source ne publie
    # jamais son `textesQuestion` (8 574 QG sur 8 574, législatures 15 à 17,
    # mesuré le 22/09/2026). La question paraît au Journal officiel dans le
    # même compte rendu que la réponse : sa date de parution est celle-là, écrite
    # par la source — arbitré le 22/09/2026 (#1044). Sans elle, les 167 QG des
    # candidats déclarés ne tombaient dans aucun filtre par période.
    if date_question is None and sous_type == "QG":
        date_question = date_reponse

    # Ministère interrogé.
    min_int = question.get("minInt") or {}
    ministere = min_int.get("developpe") if isinstance(min_int.get("developpe"), str) else None

    # Groupe parlementaire au moment du dépôt.
    groupe = auteur.get("groupe") or {}
    groupe_sigle = groupe.get("abrege") if isinstance(groupe.get("abrege"), str) else None

    return acteur_ref, {
        "uid": uid,
        "sous_type": sous_type,
        "sujet": analyse,
        "texte": texte_question,
        "reponse": reponse,
        "ministere": ministere,
        "date": date_question,
        "date_reponse": date_reponse,
        "groupe_sigle": groupe_sigle,
    }


def _build_acteur_questions_index(legislature: str) -> dict[str, list[dict[str, Any]]]:
    """Construit (et met en cache sur disque) un index acteurRef -> liste de questions.

    Agrège les 3 types (QE/QG/QOSD) en un seul index par législature. Les ZIPs
    ne sont jamais extraits sur disque : seul l'index final est mis en cache.
    Thread-safe (verrou par législature), même principe que pour les amendements.
    """
    with _get_questions_lock(legislature):
        index_path = QUESTIONS_CACHE_DIR / legislature / "index_par_acteur.json"
        if index_path.is_file():
            try:
                with open(index_path, encoding="utf-8") as f:
                    en_cache = json.load(f)
                # #1094 — un index écrit par un parseur plus ancien ne porte pas
                # la marque : il est reconstruit, jamais servi.
                if isinstance(en_cache, dict) and en_cache.pop(CLE_FORMAT_INDEX_QUESTIONS, None) == FORMAT_INDEX_QUESTIONS:
                    return en_cache
            except (json.JSONDecodeError, OSError):
                pass  # cache corrompu : on reconstruit

        question_types = AN_QUESTIONS_PATH.get(legislature)
        if not question_types:
            return {}

        index: dict[str, list[dict[str, Any]]] = {}
        complet = True

        for sous_type, (dossier, fichier) in question_types.items():
            url = f"{AN_OPENDATA_BASE}/{legislature}/questions/{dossier}/{fichier}"
            print(f"-> Téléchargement des questions {sous_type} (Assemblée nationale, législature {legislature}) : {url}")
            zip_path = QUESTIONS_CACHE_DIR / legislature / f"{sous_type.lower()}.zip"
            try:
                zip_path.parent.mkdir(parents=True, exist_ok=True)
                download_with_watchdog(url, zip_path, headers=HEADERS, timeout=TIMEOUT)
            except (requests.RequestException, OSError, TimeoutError) as exc:
                print(f"  [!] Questions {sous_type} législature {legislature} indisponibles : {exc}")
                complet = False
                continue

            try:
                with zipfile.ZipFile(zip_path) as zf:
                    noms = [n for n in zf.namelist() if n.endswith(".json")]
                    for nom in noms:
                        try:
                            with zf.open(nom) as f:
                                data = json.load(f)
                        except (json.JSONDecodeError, KeyError):
                            continue
                        parsed = _parse_question_entry(data, sous_type)
                        if parsed is None:
                            continue
                        acteur_ref, record = parsed
                        index.setdefault(acteur_ref, []).append(record)
            except zipfile.BadZipFile as exc:
                print(f"  [!] Archive de questions {sous_type} législature {legislature} invalide : {exc}")
                complet = False

        # #505 : l'index n'est mis en cache QUE s'il est complet. Le
        # commentaire de `fetch_questions_officielles` affirmait déjà que
        # « l'index par acteur n'est écrit en cache qu'une fois la législature
        # entièrement lue » — ce n'était pas vrai : il était écrit même après
        # l'échec d'une des trois archives. Mesuré le 20/08/2026 sur la
        # législature 17 (QE en `IncompleteRead`) : un index de 16,8 Mo mis en
        # cache avec les seules QG/QOSD, 2 611 questions au lieu du compte
        # réel. Tant que cet index vivait dans le seul runner qui l'avait
        # construit, le défaut se limitait à ce shard. Depuis que la clé de
        # cache le partage entre tous les shards (#505), une seule coupure
        # réseau figerait pour la semaine une collecte tronquée présentée comme
        # faite — un « 0 » qui n'est pas une absence mesurée (§2.5).
        if not complet:
            print(
                f"  [!] Index des questions (législature {legislature}) NON mis en cache : "
                "au moins une archive n'a pas pu être lue."
            )
            return index

        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                json.dump({CLE_FORMAT_INDEX_QUESTIONS: FORMAT_INDEX_QUESTIONS, **index}, f, ensure_ascii=False)
        except OSError:
            pass

        return index


def fetch_questions_officielles(
    url_an_ou_senat: Optional[str],
    budget: Optional[BudgetCollecte] = None,
) -> list[dict[str, Any]]:
    """Récupère les questions parlementaires officielles (QE/QG/QOSD) d'un député.

    Source : open data Assemblée nationale (data.assemblee-nationale.fr). Agrège
    sur toutes les législatures pour lesquelles ces données sont disponibles (voir
    AN_QUESTIONS_PATH). Retourne une liste d'entrées au format brut interventions[],
    prêtes à être fusionnées dans profile["interventions"] avec type_detail="question".

    Chaque entrée inclut les champs supplémentaires sous_type (QE/QG/QOSD),
    ministere (ministère interrogé) et reponse (texte de la réponse si disponible).
    """
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        return []

    questions: list[dict[str, Any]] = []
    legislatures = list(AN_QUESTIONS_PATH)
    for rang, legislature in enumerate(legislatures):
        # #498 : une législature = jusqu'à 3 archives (QE/QG/QOSD) de plusieurs
        # dizaines de Mo. Le budget est vérifié AVANT d'en engager une, jamais au
        # milieu, pour qu'un index partiel ne fasse pas passer une collecte
        # incomplète pour une collecte faite.
        # Le budget seul n'y suffisait pas : jusqu'à #505 l'index était écrit en
        # cache même quand une des trois archives avait échoué en cours de
        # législature. C'est `_build_acteur_questions_index` qui refuse
        # désormais de le mettre en cache dans ce cas.
        if budget_epuise(budget):
            budget_ignorer(budget, "législature(s) de questions officielles", len(legislatures) - rang)
            break
        index = _build_acteur_questions_index(legislature)
        for record in index.get(acteur_ref, []):
            uid = record.get("uid") or ""
            source_url = (
                f"https://questions.assemblee-nationale.fr/q{legislature}/{uid}.htm"
                if uid else None
            )
            questions.append({
                "id": f"question_{uid}" if uid else None,
                "date": record.get("date"),
                "type_detail": "question",
                "sous_type": record.get("sous_type"),
                "sujet": record.get("sujet"),
                "texte": record.get("texte"),
                "reponse": record.get("reponse"),
                "date_reponse": record.get("date_reponse"),
                "ministere": record.get("ministere"),
                "groupe_sigle": record.get("groupe_sigle"),
                "fonction": None,
                "format": "prise_de_parole_developpee",
                "mots_cles": [],
                "url": source_url,
                "url_detail": source_url,
                "legislature": legislature,
            })

    questions.sort(key=lambda q: q.get("date") or "", reverse=True)
    return questions


def _normaliser_orateur_id_syceron(
    valeur: Any,
    id_acteur: Any = None,
) -> tuple[Optional[str], str]:
    """Résout l'identifiant d'orateur Syceron en `acteurRef` AN (#510).

    Retourne `(acteur_ref, motif)`. `acteur_ref` est `None` dès que la valeur
    n'est pas rattachable à un acteur du référentiel AN ; `motif` nomme alors
    laquelle des formes observées a été rencontrée, pour que le rejet
    soit **compté** et non muet (§2.5).

    `id_acteur` est l'attribut que le `<paragraphe>` porte à côté de l'orateur.
    Quand il est présent et qu'il **contredit** le préfixage, c'est la source
    elle-même qui refuse l'attribution, et on la suit. Mesuré sur les trois
    archives, 2 625 paragraphes sont dans ce cas, et 2 592 portent
    `id_acteur="PA0"` — l'orateur collectif : **2 524** d'entre eux ont un
    `<nom>` qui cite *deux* orateurs (« M. André Chassaigne et M. Jean-Paul
    Lecoq ») alors que `<orateur><id>` ne porte que le premier ; les 68 autres
    sont des interruptions que la source neutralise sans dire pourquoi. Retenir
    l'identifiant présent fabriquerait une prise de parole (§2 règle 2) ; c'est
    le même arbitrage que `parse_syceron._parse_orateur` sur orateurs multiples.

    **L'archive publie l'identifiant nu**, jamais préfixé : `<orateur><id>847629
    </id>`. Le motif `PA\\d+` appliqué à cette valeur échouait donc sur 100 % des
    entrées, et l'index de la source *primaire* des interventions se construisait
    vide depuis toujours — 0 des 789 interventions publiées à `f1fff09` venaient
    de Syceron.

    Le préfixage n'est pas une inférence, il est **écrit dans la source** : le
    même `<paragraphe>` porte l'attribut `id_acteur="PA847629"` à côté de
    `<orateur><id>847629</id>`. Mesuré sur les **trois** archives complètes
    (2 768 comptes rendus, téléchargées le 26/08/2026) : `id_acteur ==
    "PA" + orateur/id` sur **1 232 692 des 1 235 317** paragraphes portant les
    deux — 636 594/638 901 sur la 15e, 307 086/307 403 sur la 16e, 289 015/289 016
    sur la 17e. Les 673 des 673 identifiants nus distincts de la 17e se résolvent
    par ailleurs dans le référentiel `acteurs_historique_an` (3 117 acteurs), dont
    662 avec concordance de nom — les 11 autres étant nommés par leur fonction
    (« Mme la présidente »), et correctement identifiés.

    Quatre formes ne sont **pas** des acteurs et sont écartées par construction,
    définitivement et sans warning individuel — même raisonnement que #474, où
    les 92 parlementaires en mission sont écartés sans trace parce que leur
    exclusion est le comportement attendu et permanent :

    - `0` : orateur **collectif anonyme** (« Un député du groupe RN », 7 580
      occurrences sur les trois archives). L'indexer fabriquerait un acteur `PA0`
      inexistant ;
    - un identifiant **négatif** : pseudo-acteur de rôle, absent du référentiel
      AN (977 occurrences ; l'archive écrit alors `id_acteur="PA-125799"`, une
      valeur syntaxiquement formée mais qui ne résout rien) ;
    - **absent** : paragraphe sans orateur (didascalie, applaudissements) ;
    - `attribution_refusee_par_la_source` : `id_acteur` contredit le préfixage
      (2 625 occurrences, toutes des prises de parole à deux orateurs).

    Reste `forme_inattendue`, à **0 mesuré sur les trois législatures** : c'est le
    compteur-témoin. Une valeur non nulle signifierait que la forme de
    l'identifiant a de nouveau bougé sous le code — exactement le défaut que
    cette fonction corrige.
    """
    if not isinstance(valeur, str) or not valeur.strip():
        return None, "absent"
    valeur = valeur.strip()
    if re.fullmatch(r"PA[1-9]\d*", valeur):
        # Forme déjà préfixée : jamais observée sur les trois archives, acceptée
        # par tolérance au cas où une archive ultérieure la publie ainsi.
        acteur_ref, motif = valeur, "prefixe_deja_present"
    elif re.fullmatch(r"0+", valeur):
        return None, "orateur_collectif_anonyme"
    elif re.fullmatch(r"[1-9]\d*", valeur):
        acteur_ref, motif = "PA" + valeur, "identifiant_nu_prefixe"
    elif re.fullmatch(r"-\d+", valeur):
        return None, "pseudo_acteur_hors_referentiel"
    else:
        return None, "forme_inattendue"

    if isinstance(id_acteur, str) and id_acteur.strip() and id_acteur.strip() != acteur_ref:
        return None, "attribution_refusee_par_la_source"
    return acteur_ref, motif


def _reduire_a_l_extrait(record: dict[str, Any]) -> dict[str, Any]:
    """La forme des membres de roster depuis #1029 : la forme réduite au thème,
    plus un extrait du verbatim (`schema_pivot.extrait_de_texte`) et
    `texte_tronque`. Une entrée déjà réduite reste telle quelle : réduite au
    thème, on n'invente pas un extrait qu'on n'a pas lu ; déjà un extrait, le
    recouper perdrait `texte_tronque`.
    """
    if record.get("collecte") in (COLLECTE_EXTRAIT, COLLECTE_THEME_SEUL):
        return dict(record)
    extrait, tronque = extrait_de_texte(record.get("texte"))
    reduite = _reduire_au_theme(record)
    if extrait is None:
        return reduite
    return {**reduite, "texte": extrait, "texte_tronque": tronque, "collecte": COLLECTE_EXTRAIT}


def _reduire_au_theme(record: dict[str, Any]) -> dict[str, Any]:
    """Réduit une entrée brute Syceron à ce qui porte le thème (#657).

    Les clés absentes ne sont pas mises à `null` : elles sont RETIRÉES, et
    `collecte` déclare pourquoi. Un `"texte": null` se lirait « cette prise de
    parole n'a pas de verbatim » ; ici le verbatim n'a pas été demandé, ce qui
    est un fait sur le run et pas sur la personne (AGENTS.md §2 règle 5).
    Mesuré : 90 octets de `null` par entrée × 380 800 entrées, pour une phrase
    fausse.

    Ce qui reste, et pourquoi :

    - `id` — la clé de fusion, aux deux étages (#540). Sans elle, 3 351 entrées
      collectées se republient à 17 ;
    - `date`, `type_detail` — les deux faits que la fiche affiche ;
    - `sujet` + `session_ref` — `normalize_profil` en dérive `theme_officiel`,
      qui est TOUT l'objet du mode ; `sujet_code_grammaire` les suit (#710),
      parce que c'est le critère du report `backfill_sujet_seance` : sans lui,
      une entrée réduite ne pourrait jamais corriger un créneau de séance déjà
      publié, et le mode « thème seul » serait le seul à ne pas guérir ;
    - `url` + `legislature` — la traçabilité (AGENTS.md §2 règle 2). L'entrée
      complète porte l'URL de l'archive TROIS fois (`source`, `source_url`,
      `url`) parce que trois chemins de normalisation historiques la lisent sous
      trois noms ; ici on n'en garde qu'un, celui que
      `normalize_profil._normalize_intervention` lit réellement. Mesuré : 330 o
      par entrée d'index économisés sur les 593 651 entrées des législatures 16
      et 17.

    `seance_ref` part avec `seance`, et `source_id` avec lui : l'uid du compte
    rendu est déjà DANS `id`, dont il est le préfixe. `orateur_id_source` part
    aussi — c'est le nom du fichier de tranche.
    """
    return {
        "id": record.get("id"),
        "date": record.get("date"),
        "type_detail": record.get("type_detail"),
        "sujet": record.get("sujet"),
        "sujet_code_grammaire": record.get("sujet_code_grammaire"),
        "session_ref": record.get("session_ref"),
        "url": record.get("url"),
        "legislature": record.get("legislature"),
        # #1087 — une entrée réduite garde le lien vers le texte entier : c'est
        # lui qui rend l'extrait vérifiable. La clé n'est posée que si l'entrée
        # la porte : posée à `None` sur l'entrée d'un index d'avant #1087, elle
        # ferait passer l'index réduit pour conforme (`_syceron_index_qualifie`).
        **({"id_syceron": record["id_syceron"]} if "id_syceron" in record else {}),
        "collecte": COLLECTE_INTERVENTION_THEME_SEUL,
    }


def _parse_syceron_intervention_entry(
    intervention: Any,
    legislature: str,
    index_in_source: int,
    *,
    theme_seul: bool = False,
) -> Optional[tuple[str, dict[str, Any]]]:
    """Convertit une intervention Syceron en entrée d'index acteurRef -> interventions.

    Seules les interventions dont l'orateur est relié sans ambiguïté à un acteur
    du référentiel officiel Assemblée nationale sont indexées ; la résolution de
    l'identifiant publié vers l'`acteurRef` est celle de
    `_normaliser_orateur_id_syceron` (#510).

    Elle s'applique SANS condition depuis le 27/08/2026. Le mode historique — le
    `re.fullmatch(r"PA\\d+")` appliqué à un identifiant que l'archive publie nu —
    n'existe plus : il ne rendait pas « moins » d'interventions, il en rendait
    **zéro**, sur les trois archives.
    """
    if not isinstance(intervention, dict):
        return None

    acteur_ref, _motif = _normaliser_orateur_id_syceron(
        intervention.get("orateur_id_source"), intervention.get("orateur_id_acteur")
    )
    if acteur_ref is None:
        return None

    source_id = intervention.get("source_id")
    suffix = f"{index_in_source:06d}"
    source_url = syceron_zip_url(legislature)
    record = {
        "id": f"syceron_{source_id or 'inconnu'}_{suffix}",
        "date": intervention.get("date"),
        "type_detail": intervention.get("type_detail"),
        "sujet": intervention.get("sujet"),
        # #710 — le code du point d'ordre du jour qui a fourni le sujet. Sa
        # PRÉSENCE prouve que l'entrée sort du parseur corrigé ; c'est le critère
        # que lit `merge_profile.backfill_sujet_seance`.
        "sujet_code_grammaire": intervention.get("sujet_code_grammaire"),
        # #1087 — l'ancre de la prise de parole sur la page de séance de l'AN.
        # Posée seulement si le parseur l'a lue (même raison que ci-dessous).
        **({"id_syceron": intervention["id_syceron"]} if "id_syceron" in intervention else {}),
        "texte": intervention.get("texte"),
        "fonction": intervention.get("fonction"),
        "format": intervention.get("format"),
        "mots_cles": intervention.get("mots_cles") or [],
        # Compatibilité avec les autres formats bruts d'interventions : `source`
        # est consommé par certains helpers existants, tandis que `url`/`url_detail`
        # restent les clés attendues par le chemin de normalisation NosDéputés.
        "source": source_url,
        "source_url": source_url,
        "url": source_url,
        "url_detail": None,
        "source_id": source_id,
        "seance_ref": intervention.get("seance_ref"),
        "session_ref": intervention.get("session_ref"),
        "orateur_id_source": acteur_ref,
        "orateur_nom": intervention.get("orateur_nom"),
        "point_ordre_du_jour": intervention.get("point_ordre_du_jour"),
        "point_code_grammaire": intervention.get("point_code_grammaire"),
        "etat_compte_rendu": intervention.get("etat_compte_rendu"),
        "version_compte_rendu": intervention.get("version_compte_rendu"),
        "legislature": legislature,
    }
    if theme_seul:
        record = _reduire_a_l_extrait(record)
    return acteur_ref, record


def _syceron_index_dirname(theme_seul: bool) -> str:
    """Nom du répertoire d'index par acteur, selon la forme des entrées (#657)."""
    return (
        SYCERON_INDEX_PAR_ACTEUR_THEME_DIRNAME
        if theme_seul
        else SYCERON_INDEX_PAR_ACTEUR_DIRNAME
    )


def _syceron_memo_key(legislature: str, theme_seul: bool = False) -> str:
    """Clé du mémo process : le chemin ABSOLU du cache de la législature (#510).

    La FORME y entre depuis #657 : le mémo garde un index non publié, et servir
    un index réduit à un appelant qui a demandé le verbatim rendrait le champ
    `texte` définitivement vide pour le reste du process, sans un mot.
    """
    return str((SYCERON_CACHE_DIR / legislature / _syceron_index_dirname(theme_seul)).resolve())


def _syceron_shard_path_acteur(
    legislature: str, acteur_ref: str, *, theme_seul: bool = False
) -> Optional[Path]:
    """Chemin de la tranche d'index d'UN acteur (#510, patron de #392/#403).

    Retourne `None` si `acteur_ref` n'a pas la forme attendue d'un identifiant AN
    (`PA` suivi de chiffres) : le nom de fichier en étant dérivé, on refuse tout
    ce qui pourrait sortir du répertoire de cache plutôt que d'assainir
    approximativement.
    """
    if not isinstance(acteur_ref, str) or not re.fullmatch(r"PA\d+", acteur_ref):
        return None
    return (
        SYCERON_CACHE_DIR
        / legislature
        / _syceron_index_dirname(theme_seul)
        / f"{acteur_ref}.json"
    )


# Champ dont la présence atteste qu'un index Syceron par acteur a été produit
# APRÈS #710. Le parseur corrigé l'écrit sur CHAQUE entrée (`parse_syceron.py`,
# `_reduire_au_theme` le reconduit) : un index où aucune entrée ne porte la clé
# est donc périmé, jamais « une législature dont la source ne qualifie rien ».
# #1087 — `id_syceron` remplace `sujet_code_grammaire` (#710) : un index écrit
# avant #1087 n'a pas l'ancre, et se relirait sans elle. Tout index qui la
# porte porte aussi la clé de #710 — le parseur les écrit ensemble.
SYCERON_CHAMP_QUALIFICATION = "id_syceron"

#: Mémo du verdict de conformité, indexé par CHEMIN absolu du répertoire
#: d'index — jamais par un nom logique : les tests règlent leur propre cache par
#: cas, et un mémo global ferait fuiter le verdict d'un test dans le suivant
#: (le piège qui a fait revenir #377, AGENTS.md §5).
_SYCERON_INDEX_QUALIFIE: dict[str, bool] = {}


def vider_memo_qualification_syceron() -> None:
    """Oublie les verdicts de conformité déjà rendus. Usage test."""
    _SYCERON_INDEX_QUALIFIE.clear()


def _syceron_index_qualifie(index_dir: Path) -> bool:
    """True si les tranches d'un index Syceron portent la qualification de #710.

    « Un répertoire qui existe n'est pas la preuve de ce qu'il contient »
    (AGENTS.md §5, leçon du cache d'amendements ; #639 l'a appliquée au cache de
    scrutins). Ici l'index N'EST PAS une archive brute mise de côté : **c'est le
    produit de `parse_syceron`**, donc un index en cache est un *parsage* en
    cache. Sa clé — `public-data-cache-an-<semaine>-interv-<empreinte>` — dit
    quand, dans quel mode et sur quelles archives il a été écrit (#550), jamais
    avec quel parseur. Mesuré le 02/09/2026 sur le run `33652389393` : lancé
    avec `collect_interventions=true` pour appliquer #710, il a restauré un index
    d'avant le correctif et publié **0** entrée portant la clé sur les 3 963 de
    `gabriel-attal` — les 2 041 sujets de créneau sont restés intacts, et
    `backfill_sujet_seance`, dont c'est la **preuve**, ne s'est appliqué à rien.

    Le test porte sur la **clé**, pas sur sa valeur : `sujet_code_grammaire` vaut
    légitimement `None` sur un point dont la grammaire ne porte pas de sujet, et
    exiger une valeur refuserait un index correct. Même règle que
    `_scrutins_store_qualifie` (#639).

    **Une seule tranche est lue, et c'est la plus petite.** Toute entrée produite
    par le parseur corrigé porte la clé et aucune de l'ancien ne la porte : un
    échantillon d'une entrée tranche. La plus petite est le témoin le moins cher
    — une tranche d'acteur bavard pèse plusieurs Mio, et #628 interdit de charger
    ce qu'on n'a pas besoin de garder. Un répertoire vide est déclaré non
    qualifié : il n'y a rien à en tirer et le reconstruire ne coûte rien.
    """
    cle = str(index_dir.resolve())
    memoise = _SYCERON_INDEX_QUALIFIE.get(cle)
    if memoise is not None:
        return memoise

    verdict = False
    try:
        tranches = [p for p in index_dir.glob("PA*.json") if p.is_file()]
    except OSError:
        tranches = []
    if tranches:
        try:
            with open(min(tranches, key=lambda p: p.stat().st_size), encoding="utf-8") as f:
                entrees = json.load(f)
        except (json.JSONDecodeError, OSError):
            entrees = None
        if isinstance(entrees, list):
            verdict = any(
                isinstance(e, dict) and SYCERON_CHAMP_QUALIFICATION in e for e in entrees
            )

    _SYCERON_INDEX_QUALIFIE[cle] = verdict
    return verdict


def _read_cached_interventions_syceron_acteur(
    legislature: str, acteur_ref: str, *, theme_seul: bool = False
) -> Optional[list[dict[str, Any]]]:
    """Interventions Syceron d'UN acteur, lues depuis la tranche en cache (#510).

    Retourne `None` si l'index n'est pas disponible (répertoire de tranches
    absent, ou tranche illisible) — l'appelant reconstruit alors —, et une liste
    éventuellement vide si l'acteur n'y figure pas. Distinguer « cet acteur n'a
    pas parlé sous cette législature » de « index indisponible » est la même
    règle que sur les votes et les amendements (règle 5 : une donnée manquante
    n'est jamais un 0).

    Coût : une tranche d'acteur, là où la forme d'avant relisait l'index ENTIER
    à chaque candidat et pour chaque législature — 1 664,8 Mio et 12,5 s pour les
    trois archives, mesurés le 26/08/2026.
    """
    # #657 — L'INDEX COMPLET SERT LES DEUX MODES, jamais l'inverse. Un run
    # réduit qui trouve l'index complet le lit et jette les champs lourds : rien
    # à reconstruire, et c'est le cas nominal en CI, où `extract-an` publie
    # l'index complet avant que la matrice roster ne démarre (`needs:`). Un run
    # complet, lui, ne regarde JAMAIS l'index réduit — il en sortirait des
    # `texte` vides qui passeraient pour un constat (#510, §2.5).
    formes: tuple[bool, ...] = (False, True) if theme_seul else (False,)
    for forme_theme in formes:
        index_dir = SYCERON_CACHE_DIR / legislature / _syceron_index_dirname(forme_theme)
        if not index_dir.is_dir():
            continue
        # #719 — l'existence n'est pas la conformité. Un index d'avant #710 est
        # traité comme ABSENT : l'appelant reconstruit, et le parseur corrigé
        # écrit enfin `sujet_code_grammaire`. Le `continue` plutôt qu'un `return
        # None` laisse un run réduit se rabattre sur l'autre forme, qui peut,
        # elle, être conforme.
        if not _syceron_index_qualifie(index_dir):
            print(
                f"  [i] Index des débats Syceron (législature {legislature}"
                f"{', réduit au thème' if forme_theme else ''}) antérieur à #710 "
                "(aucune qualification `sujet_code_grammaire`) : reconstruit."
            )
            continue
        shard_path = _syceron_shard_path_acteur(
            legislature, acteur_ref, theme_seul=forme_theme
        )
        if shard_path is None or not shard_path.is_file():
            return []
        try:
            with open(shard_path, encoding="utf-8") as f:
                entrees = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None
        if not isinstance(entrees, list):
            return None
        if theme_seul and not forme_theme:
            entrees = [_reduire_a_l_extrait(e) for e in entrees if isinstance(e, dict)]
        return entrees
    return None


def _write_syceron_index_par_acteur(
    legislature: str, index: dict[str, list[dict[str, Any]]], *, theme_seul: bool = False
) -> None:
    """Publie l'index Syceron en tranches par acteur, d'un seul `os.replace` (#510).

    Le répertoire est écrit à côté puis basculé : remplir `index_par_acteur/` en
    place laisserait, pendant toute la boucle, un répertoire qui EXISTE et qui
    est INCOMPLET — et `_read_cached_interventions_syceron_acteur` lit un
    répertoire présent comme un index complet, donc chaque acteur dont la tranche
    manque encore serait lu « n'a pas parlé » au lieu de « index indisponible ».
    C'est mot pour mot le défaut de #447 sur les amendements, et le cas est
    atteignable ici aussi : le cache est partagé entre les shards par la clé de
    #505.
    """
    cache_dir = SYCERON_CACHE_DIR / legislature
    dirname = _syceron_index_dirname(theme_seul)
    index_dir = cache_dir / dirname
    tmp_dir = cache_dir / f"{dirname}.partiel"
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for acteur_ref, entrees in index.items():
        shard_path = _syceron_shard_path_acteur(
            legislature, acteur_ref, theme_seul=theme_seul
        )
        if shard_path is None:
            continue  # acteurRef hors forme attendue : ignoré plutôt qu'écrit
        with open(tmp_dir / shard_path.name, "w", encoding="utf-8") as f:
            json.dump(entrees, f, ensure_ascii=False)
    shutil.rmtree(index_dir, ignore_errors=True)
    os.replace(tmp_dir, index_dir)
    # #719 — le verdict de conformité porte sur un CONTENU, pas sur un chemin :
    # le garder après réécriture ferait refuser l'index qu'on vient de produire,
    # et chaque acteur suivant reparcourrait l'archive (12,5 s et 3,8 Gio de pic
    # mesurés en #510). L'oubli est ici, dans la seule fonction qui publie.
    _SYCERON_INDEX_QUALIFIE.pop(str(index_dir.resolve()), None)
    if theme_seul:
        # Les index plats hérités appartiennent à la forme COMPLÈTE : les
        # supprimer depuis un run réduit ferait payer à l'autre forme une
        # décision qui n'est pas la sienne.
        return
    for nom in SYCERON_INDEX_FILENAMES_HERITES:
        (cache_dir / nom).unlink(missing_ok=True)


def _build_acteur_interventions_syceron_index(
    legislature: str, *, theme_seul: bool = False
) -> dict[str, list[dict[str, Any]]]:
    """Construit (et publie en tranches par acteur) l'index acteurRef -> interventions.

    Les XML Syceron sont déjà téléchargés/extraits par `syceron_debates.py` ;
    ici on ne sérialise que l'index final des interventions rattachables sans
    ambiguïté à un `acteurRef` officiel.

    **Cette fonction ne lit jamais le cache** : c'est le CONSTRUCTEUR. La lecture
    passe par `_read_cached_interventions_syceron_acteur`, une tranche à la fois
    (#510) — relire l'index entier par candidat coûtait 12,5 s et 3,8 Gio de RSS
    de pic sur les trois archives.

    **Un index vide construit sur une archive LISIBLE n'est jamais publié en
    silence (#510, §2.5).** C'est le trou par lequel le défaut est passé : la
    garde de #505 ne couvrait que le cas « aucun fichier lisible », et un `{}`
    produit à partir de 601 comptes rendus lus passait, lui, pour un résultat.
    Une source primaire qui rend zéro sur une archive présente est une donnée
    manquante, pas un zéro mesuré ; le repli NosDéputés comblait le silence, donc
    rien ne le signalait. Le repli est parti, mais la garde reste : sans elle,
    c'est un profil publié sans interventions qui passerait pour un constat.

    Les rejets sont **agrégés**, une ligne par législature, jamais un warning par
    entrée : ils se comptent en dizaines de milliers (mesuré sur la 17e, parseur
    corrigé : 28 592 paragraphes sans orateur, 2 154 orateurs collectifs
    anonymes, 312 pseudo-acteurs hors référentiel, 1 attribution refusée par la
    source, 0 forme inattendue). Un warning par entrée serait pire que le
    silence — même arbitrage que #492, où un warning par mandat aurait fait 214
    occurrences là qu'un agrégat par profil dit la même chose.
    """
    with _get_syceron_lock(legislature):
        memo_key = _syceron_memo_key(legislature, theme_seul)
        non_publie = _SYCERON_INDEX_NON_PUBLIE.get(memo_key)
        if non_publie is not None:
            return non_publie

        index: dict[str, list[dict[str, Any]]] = {}
        motifs: Counter[str] = Counter()
        fichiers_lus = 0
        indexees_sans_sujet = 0
        for xml_path in iter_syceron_xml_files(legislature):
            try:
                parsed = parse_syceron_xml(
                    xml_path.read_bytes(), avec_texte=not theme_seul
                )
            except (ET.ParseError, OSError):
                continue
            fichiers_lus += 1
            for idx, intervention in enumerate(parsed.get("interventions") or []):
                if isinstance(intervention, dict):
                    _, motif = _normaliser_orateur_id_syceron(
                        intervention.get("orateur_id_source"),
                        intervention.get("orateur_id_acteur"),
                    )
                    motifs[motif] += 1
                parsed_entry = _parse_syceron_intervention_entry(
                    intervention, legislature, idx, theme_seul=theme_seul
                )
                if parsed_entry is None:
                    continue
                acteur_ref, record = parsed_entry
                if not record.get("sujet"):
                    indexees_sans_sujet += 1
                index.setdefault(acteur_ref, []).append(record)

        # #505, même règle que pour les questions officielles : ne jamais mettre
        # en cache un index construit sur une archive absente. `iter_syceron_xml_files`
        # rend un itérateur VIDE quand le téléchargement échoue — indiscernable,
        # une fois l'index écrit, d'une législature réellement sans débats.
        # L'index étant désormais partagé entre les shards par la clé de cache,
        # un tel `{}` se propagerait à toute la semaine (§2.5).
        if fichiers_lus == 0:
            print(
                f"  [!] Index des débats Syceron (législature {legislature}) NON mis en "
                "cache : aucun compte rendu lisible (archive indisponible ?)."
            )
            _SYCERON_INDEX_NON_PUBLIE[memo_key] = index
            return index

        detail = ", ".join(f"{motif}={n}" for motif, n in sorted(motifs.items())) or "aucune entrée"
        forme = " [réduit au thème, #657]" if theme_seul else ""
        print(
            f"  -> Index des débats Syceron (législature {legislature}){forme} : "
            f"{fichiers_lus} compte(s) rendu(s) lu(s), {len(index)} acteur(s), "
            f"{sum(len(v) for v in index.values())} intervention(s) — orateurs : {detail}"
        )
        if motifs.get("forme_inattendue"):
            # Compteur-témoin : à 0 sur les trois législatures. Non nul, il dit
            # que la forme de l'identifiant a de nouveau bougé sous le code (#510).
            print(
                f"  [!] Débats Syceron (législature {legislature}) : "
                f"{motifs['forme_inattendue']} identifiant(s) d'orateur d'une forme "
                "non reconnue — la forme publiée par l'archive a changé (#510)."
            )

        # Second compteur-témoin, sur l'autre moitié de #510 : le sujet. Il est
        # renseigné sur 88,0 % des 1 227 415 interventions indexables des trois
        # archives (84,8 / 93,9 / 88,9 % par législature). À 100 % de vides, c'est
        # que `code_grammaire` ou l'emplacement du titre ont bougé sous le code —
        # et un `sujet` universellement `None` est précisément l'état que #510
        # avait laissé, invisible parce que rien ne le disait (§2.5).
        indexees = sum(len(v) for v in index.values())
        if indexees and not indexees - indexees_sans_sujet:
            print(
                f"  [!] Débats Syceron (législature {legislature}) : AUCUNE des "
                f"{indexees} interventions indexées ne porte de sujet. Le titre de "
                "point n'est plus lu là où la source le publie (#510) — les tags "
                "thématiques dérivés seraient vides."
            )

        if not index:
            # #510, §2.5 : une source primaire qui rend zéro sur une archive
            # lisible est une donnée manquante, pas un zéro mesuré. Ne rien
            # publier — un index vide figé sous la clé de la semaine (#505)
            # rendrait le défaut invisible pour tous les shards suivants, et
            # c'est très exactement ainsi que #510 a survécu.
            #
            # Depuis le retrait du repli, plus rien ne comble ce silence : les
            # profils de ce run sortiraient SANS interventions. Le warning de
            # profil (`interventions syceron indisponibles`) le dit candidat par
            # candidat, cette ligne-ci le dit une fois par législature.
            print(
                f"  [!] Index des débats Syceron (législature {legislature}) NON mis en "
                f"cache : {fichiers_lus} compte(s) rendu(s) lu(s) mais AUCUN acteur résolu. "
                "La source primaire des interventions ne rend rien alors que l'archive est "
                "présente — et le repli NosDéputés a été retiré (#510) : les profils de ce "
                "run n'auront pas d'interventions de débat."
            )
            _SYCERON_INDEX_NON_PUBLIE[memo_key] = index
            return index

        try:
            _write_syceron_index_par_acteur(legislature, index, theme_seul=theme_seul)
        except OSError as exc:
            # L'index reste valide pour CE candidat, mais rien n'est publié : le
            # suivant reparcourra l'archive. Dit à voix haute plutôt que mémoïsé
            # — garder 866 Mio d'index résidents pour contourner un cache
            # inaccessible échangerait un défaut lent contre un OOM.
            print(
                f"  [!] Index des débats Syceron (législature {legislature}) NON publié "
                f"en tranches : {exc}. Chaque candidat reparcourra l'archive."
            )

        return index


def _interventions_syceron_acteur(
    legislature: str, acteur_ref: str, *, theme_seul: bool = False
) -> list[dict[str, Any]]:
    """Interventions Syceron d'un acteur pour une législature (#510).

    Lit la tranche d'acteur si l'index est publié, et ne reconstruit — donc ne
    reparcourt l'archive — que s'il ne l'est pas. Le verrou est pris ici, et non
    seulement dans le constructeur : sans lui, N candidats qui trouvent l'index
    absent le construisent N fois.
    """
    with _get_syceron_lock(legislature):
        entrees = _read_cached_interventions_syceron_acteur(
            legislature, acteur_ref, theme_seul=theme_seul
        )
        if entrees is not None:
            return entrees
        index = _build_acteur_interventions_syceron_index(
            legislature, theme_seul=theme_seul
        )
        return list(index.get(acteur_ref) or [])


def fetch_interventions_syceron(
    url_an_ou_senat: Optional[str],
    budget: Optional[BudgetCollecte] = None,
    *,
    theme_seul: bool = False,
) -> list[dict[str, Any]]:
    """Récupère les débats Syceron d'un député via son `acteurRef` officiel AN.

    Source PRIMAIRE et désormais unique des interventions de débat : le repli
    NosDéputés a été retiré du chemin par #510. Une liste vide est donc un
    résultat publié tel quel, et déclaré par `build_profile` dans
    `meta.warnings[]` — jamais comblé par une autre source.
    """
    acteur_ref = _extract_acteur_ref(url_an_ou_senat)
    if not acteur_ref:
        return []

    interventions: list[dict[str, Any]] = []
    legislatures = sorted(SYCERON_AVAILABLE_LEGISLATURES, key=int, reverse=True)
    for rang, legislature in enumerate(legislatures):
        # #498 : même garde que pour les questions officielles — une législature
        # Syceron, c'est une archive de 50 à 150 Mo. Vérifié entre deux
        # législatures, jamais au milieu de l'une d'elles. Les législatures sont
        # parcourues de la plus récente à la plus ancienne : ce qui tombe en
        # premier sous le budget est donc le plus ancien, pas le plus consulté.
        #
        # COÛT RÉEL, remesuré par #546 sur le run 33110395663 (27/08), 7 shards
        # porteurs — le premier où les trois archives ont répondu. Les 22-55 s
        # écrites ici jusque-là dataient de runs où Syceron rendait ZÉRO
        # intervention (défaut #510) : téléchargement + indexation valent
        # 34-55 s pour la 16e législature et **79-166 s pour la 15e**. C'est le
        # poste le plus cher de la collecte, et cette garde ne peut rien pour
        # lui : à l'horloge 41-63 s quand la 15e est engagée, le budget n'est
        # jamais épuisé, donc jamais celle-ci qui est sautée.
        if budget_epuise(budget):
            budget_ignorer(budget, "législature(s) de débats Syceron", len(legislatures) - rang)
            break
        interventions.extend(
            _interventions_syceron_acteur(legislature, acteur_ref, theme_seul=theme_seul)
        )

    interventions.sort(key=lambda entry: (entry.get("date") or "", entry.get("id") or ""), reverse=True)
    return interventions


# `fetch_votes` a été RETIRÉE par #528. Elle lisait `/<slug>/votes/{json,xml}`
# sur NosDéputés/NosSénateurs, et n'était appelée que pour la chambre
# "senateurs" : côté députés l'endpoint est en panne systématique (HTTP 500 sur
# tous les domaines, voir `fetch_votes_officiels`) et l'appel avait été retiré
# de longue date. Le Sénat sorti du périmètre, il ne restait aucun appelant, et
# la branche de repli « utiliser votes_raw » de l'étape 6 est devenue
# inatteignable — elle a été retirée avec.
# Voir docs/decisions/retrait-senat-528.md.


# ── La lecture du profil brut NosDéputés vivait ici (#529, lot 5) ───────────
# `_groupe_label`, `_extract_responsabilite_entries` et `_extract_mandats`
# lisaient les champs `responsabilites` / `historique_responsabilites` /
# `groupes_parlementaires` / `responsabilites_extra_parlementaires` d'un profil
# NosDéputés. Depuis #369 (étape 4) ils n'étaient plus atteints que pour un
# député absent du référentiel AN combiné ; ce repli est parti avec la source.
# Les mandats commission / groupe d'amitié / extra-parlementaire viennent
# désormais tous d'`_extract_mandats_officiels`, et les mandats électifs
# d'`identite_an` — la LISTE complète depuis #640, plus le seul mandat courant
# (voir `_periodes_mandats_assemblee`).
#
# Sont partis avec eux la chaîne d'interventions scrapées :
# `fetch_intervention_details`, `fetch_seance_context`,
# `_extract_speaker_identity_from_html`, `_classify_intervention`,
# `_classify_intervention_format` (et son seuil `REACTION_COURTE_NB_MOTS_MAX`),
# `_to_int`, `_process_search_result` et `_extract_search_results`. Elles
# alimentaient les 496 interventions publiées portant une URL `nosdeputes` —
# **conservées telles quelles dans le corpus**, la fusion additive ne retirant
# rien (AGENTS.md §3). Ce qui disparaît est la capacité à en collecter de
# NOUVELLES par ce chemin, pas ce qui l'a été.
#
# La source primaire des interventions reste Syceron
# (`fetch_interventions_syceron`), complétée par les questions officielles
# (`fetch_questions_officielles`). Voir
# docs/decisions/retrait-nosdeputes-529.md.


def build_profile(
    chambre: str,
    slug: str,
    skip_interventions: bool = False,
    interventions_theme_seul: bool = False,
    skip_dossiers_legislatifs: bool = False,
    budget_interventions: Optional[BudgetCollecte] = None,
    budget_collecte: Optional[BudgetCollecte] = None,
    acteur_ref: Optional[str] = None,
) -> dict:
    """Construit le profil complet d'un parlementaire (identité, mandats/responsabilités,
    votes, dossiers législatifs, interventions) à partir des données ouvertes
    officielles de l'Assemblée nationale — **seule source depuis #529**.

    Aucune source indisponible ne fait échouer l'appel : chaque section manquante reste
    simplement vide, avec un message explicatif ajouté à `profile["meta"]["warnings"]`.

    **`chambre` ne vaut plus que `"deputes"` (#528).** Toute autre valeur lève
    un `ValueError` : le Sénat est sorti du périmètre, et un appel qui aurait
    silencieusement rendu un profil vide est exactement le défaut que #501 et
    #510 ont payé — une collecte qui rend zéro par construction, sans le dire.

    **Un slug introuvable dans le référentiel AN ne produit plus d'identité
    (#529).** Le repli NosDéputés qui la comblait est retiré ; le profil sort
    alors avec `identite: None` et un `WARNING_PREFIX_IDENTITE_INTROUVABLE`
    nommant la seule source consultée. C'est un constat de l'AN, pas un
    silence : `raw_data/correspondance_acteurs_an.json` (#525) est la table qui
    résout le couple slug ↔ acteur, et §5b du garde-fou qualité échoue déjà sur
    tout slug publié qui n'y a pas d'entrée.

    Args:
        chambre: "deputes" (seule valeur acceptée depuis #528).
        slug: identifiant du parlementaire, qui est aussi le nom de son fichier
            de profil (ex. "jean-luc-melenchon"). Résolu en `acteur_ref` AN par
            `_resolve_acteur_ref_par_slug` (#525) — sauf si `acteur_ref` est fourni.
        acteur_ref: l'acteur AN déjà connu de l'appelant — celui que le roster
            désigne pour un membre de groupe (#850). Fourni, il n'est jamais
            re-deviné par le nom ; voir `fetch_identite_officielle_par_slug`.
        skip_dossiers_legislatifs: si True, ne fait aucun appel réseau pour les dossiers
            législatifs (`profile["dossiers_legislatifs"]` reste vide). Voir mode
            d'extraction léger (#357) : utilisé quand seuls identité/mandats/votes/
            amendements sont exploités en aval (agrégats de groupe, #349).
        interventions_theme_seul: collecte RÉDUITE AU THÈME (#657). Les débats
            Syceron sont collectés sans leur verbatim ; les questions
            officielles ne le sont PAS DU TOUT — elles ne portent ni
            `seance_ref` ni `session_ref`, donc `theme_officiel` y est `None` et
            `mots_cles` vide : elles n'apportent pas une étiquette thématique,
            et leur collecte est le seul poste réseau du chemin interventions
            qui soit proportionnel au nombre de membres. Sans effet sous
            `skip_interventions`, qui prime.
        budget_interventions: budget de temps mur (`BudgetCollecte`) pour la SEULE
            collecte d'interventions — débats Syceron et questions officielles.
            None = aucun budget, le comportement historique. Épuisé, il arrête la
            collecte entre deux unités, conserve ce qui est déjà collecté et
            ajoute un `WARNING_PREFIX_BUDGET_INTERVENTIONS` à `meta.warnings[]`
            (#498). Le budget est destiné à être PARTAGÉ entre les chambres d'un
            même candidat (voir `generate_all_profiles.build_profile_any_chambre`) :
            le plafond porte sur le candidat, pas sur chaque interrogation de chambre.
        budget_collecte: budget de temps mur (`BudgetCollecte`) pour la
            collecte ENTIÈRE du candidat — identité, votes, dossiers,
            interventions comprises (#514). Contrairement au précédent, il
            **n'est jamais conditionné à un mode** : c'est précisément un
            budget qui ne couvrait qu'une phase, désactivé par
            `--skip-interventions`, qui a laissé `extract-senat` consommer ses
            15 minutes de `timeout-minutes` pour un seul profil écrit
            (run 32421439590, 20/08/2026). Partagé entre les chambres d'un
            même candidat, comme `budget_interventions`.

    Returns:
        Le dict de profil, sérialisable en JSON tel quel.
    """
    # #528 : le refus existait déjà (`chambre invalide`), mais il ne disait pas
    # POURQUOI "senateurs" n'est plus une chambre. Un appelant qui la demande
    # encore doit lire la décision, pas déduire une panne — et surtout pas
    # obtenir un profil vide qui passerait pour un constat (#501, #510).
    if chambre not in CHAMBRES_COLLECTEES:
        raise ValueError(
            f"chambre invalide : {chambre} (attendu: {list(CHAMBRES_COLLECTEES)}). "
            "Le Sénat a été retiré du périmètre par #528 — source morte ; voir "
            "docs/decisions/retrait-senat-528.md. Une source de remplacement EST "
            "établie depuis #885 (data.senat.fr, Licence Ouverte), mais sa voie "
            "de collecte n'est pas encore câblée : cette chambre reste refusée "
            "ici tant qu'elle n'a rien derrière, plutôt que de rendre un profil "
            "vide qui passerait pour un constat ; voir "
            "docs/decisions/reouverture-partielle-senat-885.md."
        )

    # #514 : la phase d'interventions est bornée par SON budget quand il existe
    # (#500, qui le veut étanche aux autres phases), et par celui du candidat
    # sinon. Jamais par rien : c'est cette troisième possibilité, laissée
    # ouverte par le `and not skip_interventions` de #500, qui a produit #514.
    # Quand les deux existent, `budget_interventions` a le budget du candidat
    # pour parent : le temps est facturé aux deux, et l'épuisement de l'un
    # arrête l'autre.
    budget_phase_interventions = budget_interventions or budget_collecte

    # --- 0. Identité/mandats officiels (Assemblée nationale). Résolue en tout
    # premier depuis #369 (étape 4) parce qu'elle permettait alors de sauter
    # l'appel NosDéputés ; depuis #529 elle est simplement la SEULE identité.
    # Le compteur de requêtes sans réponse (#514) qui encadrait ce bloc est
    # parti avec elles : cette résolution ne fait aucun appel réseau propre —
    # elle lit l'archive AMO30 déjà téléchargée et mise en cache. ---
    pre_profile_warnings: list[str] = []
    identite_an: Optional[dict[str, Any]] = None
    acteur_ref_an: Optional[str] = None
    with budget_section(budget_collecte, "identité Assemblée nationale"):
        try:
            identite_an, acteur_ref_an = fetch_identite_officielle_par_slug(
                slug, acteur_ref=acteur_ref
            )
        except ActeurContreditParLaTable as exc:
            # Imprimé ET consigné : le profil sans identité n'est pas écrit, et
            # un avertissement porté par un profil jeté ne se lirait nulle part.
            print(f"  [!] {exc}")
            pre_profile_warnings.append(avertissement(str(exc), DESTINATAIRE_INTERNE))
        except Exception as exc:
            pre_profile_warnings.append(avertissement(
                f"identité officielle (Assemblée nationale) indisponible : {exc}",
                DESTINATAIRE_INTERNE,
            ))

    # --- 4. Structure de base du profil, valeurs par défaut si une source manque. ---
    profile: dict[str, Any] = {
        "slug": slug,
        "chambre": chambre,
        # Source primaire du profil (règle 2) : la fiche AN de l'acteur.
        # C'était l'URL NosDéputés du slug jusqu'à #529 — une URL de plateforme
        # tierce présentée comme la source d'un profil dont plus une seule
        # section ne venait d'elle. `None` quand le slug n'est pas résolu :
        # inventer une URL de fiche pour un acteur qu'on n'a pas trouvé serait
        # une source qui ne mène nulle part (AGENTS.md §2 règles 2 et 5).
        "source": _acteur_ref_to_pseudo_url(acteur_ref_an) if acteur_ref_an else None,
        "identite": None,
        "mandats": [],
        "votes": [],
        "votes_source": None,
        "dossiers_legislatifs": [],
        "amendements": [],
        "interventions": [],
        "meta": {
            "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            # Licence Ouverte depuis #530 (lot 6) : ce collecteur n'appelle plus
            # que data.assemblee-nationale.fr (#529). La constante d'avant —
            # « ODbL (Regards Citoyens, …) » — attribuait à une plateforme tierce
            # un profil brut dont plus une seule section ne venait d'elle.
            "licence_donnees": LICENCE_AN,
            # Traçabilité de fraîcheur : horodatage ISO-8601 de la dernière synchro
            # réussie pour chaque source (None = source non contactée ou indisponible).
            # `nosdeputes` a été retirée de ce dict par #529 : plus aucune
            # requête ne peut la renseigner, et un horodatage de synchro
            # définitivement `None` se lit comme « source en panne » alors
            # qu'elle n'est plus interrogée. Les profils bruts déjà collectés
            # la portent encore ; `normalize_profil` sait la relire (repli
            # explicite), il ne l'écrit plus.
            "synchro_sources": {
                "assemblee_nationale": None,
                "assemblee_nationale_questions": None,
                "assemblee_nationale_syceron": None,
            },
            "warnings": [],
            # #539 — listes métier que CE run a délibérément écartées, et le
            # drapeau qui l'a décidé. Écrit à la collecte parce que c'est le
            # seul endroit qui le sache : la passe pivot de la CI est un
            # `--pivot-only` sans drapeau (`generate-data.yml:1903`), et sans
            # cette trace elle publierait « couvert » sur une liste que
            # personne n'a demandée. Une liste vide par décision et une liste
            # vide par panne sont deux faits différents (AGENTS.md §2.5) ; le
            # premier n'est lisible que si la décision est consignée.
            "collecte_ecartee": sorted(
                liste
                for liste, ecarte in (
                    ("interventions", skip_interventions),
                    ("textes_portes", skip_dossiers_legislatifs),
                )
                if ecarte
            ),
            # #657 — la FORME de la collecte d'interventions, quand elle n'est
            # pas la forme pleine. `collecte_ecartee` dit ce qui n'a pas été
            # demandé ; cette clé-ci dit ce qui l'a été à moitié, et la passe
            # pivot de la CI (`--pivot-only`, sans drapeau) n'a aucun autre
            # moyen de le savoir. Absente quand la collecte est complète : une
            # clé toujours présente ne distinguerait plus les deux runs.
            **(
                {"collecte_reduite": {"interventions": COLLECTE_EXTRAIT}}
                if interventions_theme_seul and not skip_interventions
                else {}
            ),
        },
    }

    warnings = profile["meta"]["warnings"]
    warnings.extend(pre_profile_warnings)

    # --- 5. Identité + mandats/responsabilités (commissions, missions, groupes
    # d'amitié...). Depuis #355 l'identité (infos biographiques) des députés est
    # résolue depuis le référentiel historique officiel de l'Assemblée
    # nationale, par correspondance sur le slug (voir
    # fetch_identite_officielle_par_slug, résolu dès l'étape 0). Depuis #529
    # c'est la seule : les mandats commission/groupe_amitie/extra_parlementaire
    # viennent d'`_extract_mandats_officiels` (organeRef résolu par #353), et
    # les mandats électifs ainsi que le groupe parlementaire déclaré sont
    # reconstruits ci-dessous depuis `identite_an` (groupe_sigle/groupe_nom/
    # mandats_assemblee/nb_mandats, voir _build_acteur_identite_index).
    # Le repli NosDéputés — un député absent des archives AN combinées — est
    # parti avec la source. ---
    if identite_an is None:
        warnings.append(avertissement(
            f"{WARNING_PREFIX_IDENTITE_INTROUVABLE} : le référentiel officiel "
            "Assemblée nationale ne renvoie pas de profil exploitable pour ce "
            "slug (seule source depuis #529).",
            # Explique un bloc `identite` vide, que `couverture` ne couvre pas
            # (elle porte les cinq listes métier, pas l'identité) : c'est au
            # lecteur que ce constat manque (#642).
            DESTINATAIRE_LECTEUR,
        ))
    else:
        profile["meta"]["synchro_sources"]["assemblee_nationale"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")

        profile["identite"] = {
            "nom_complet": identite_an.get("nom_complet"),
            # #659 — `civilite` était lue par l'index d'identité depuis #556 et
            # s'arrêtait là : elle n'a jamais été recopiée dans le profil brut,
            # donc jamais publiée. C'est le motif du `dossier_id` de #639 — un
            # champ traversé puis perdu à l'assemblage, sans qu'aucun contrôle
            # ne le voie, `identite` n'étant surveillé que sur sa PRÉSENCE.
            "civilite": identite_an.get("civilite"),
            "groupe_sigle": identite_an.get("groupe_sigle"),
            "groupe_nom": identite_an.get("groupe_nom"),
            "profession": identite_an.get("profession"),
            # #659 — la nomenclature PCS de l'INSEE telle que l'AN l'applique,
            # à côté du texte libre de `profession`, jamais à sa place.
            "famille_socioprofessionnelle": identite_an.get("famille_socioprofessionnelle"),
            "categorie_socioprofessionnelle": identite_an.get("categorie_socioprofessionnelle"),
            "date_naissance": identite_an.get("date_naissance"),
            "lieu_naissance": identite_an.get("lieu_naissance"),
            "num_circo": identite_an.get("numero_circo"),
            "nb_mandats": identite_an.get("nb_mandats"),
            "uri_hatvp": identite_an.get("uri_hatvp"),
            "url_an_ou_senat": _acteur_ref_to_pseudo_url(acteur_ref_an) if acteur_ref_an else None,
        }

        # Mandats commission/groupe_amitie/extra_parlementaire, sourcés depuis
        # l'AN (#369). Le complément NosDéputés — limité, depuis #369, aux seules
        # catégories que l'AN ne couvre pas — est parti avec la source (#529).
        mandats_an = _extract_mandats_officiels(acteur_ref_an) if acteur_ref_an else []
        # Les mandats électifs ne sont pas dans `_extract_mandats_officiels`
        # (qui ne parcourt que les organes) : ils sont reconstruits depuis
        # `identite_an`, où `_periodes_mandats_assemblee` publie désormais la
        # LISTE complète et non plus le seul couple `mandat_debut`/`mandat_fin`
        # du mandat courant (#640).
        periodes_an = identite_an.get("mandats_assemblee")
        if not isinstance(periodes_an, list):
            # Repli : une identité qui ne porte pas la liste. C'est le cas d'un
            # index d'identité construit avant #640 et restauré depuis le cache
            # disque — le nom du fichier est versionné (`NOM_INDEX_IDENTITE`)
            # précisément pour que ça n'arrive pas, mais le repli publie le
            # mandat courant plutôt que rien, ce qui reste l'état d'avant.
            groupe_label_an = identite_an.get("groupe_nom") or identite_an.get("groupe_sigle")
            periodes_an = [{
                "debut": identite_an.get("mandat_debut"),
                "fin": identite_an.get("mandat_fin"),
                "groupe_sigle": identite_an.get("groupe_sigle"),
                "groupe_nom": identite_an.get("groupe_nom"),
            }] if identite_an.get("mandat_debut") else []
        for periode in periodes_an:
            if not periode.get("debut"):
                continue
            groupe_label_an = periode.get("groupe_nom") or periode.get("groupe_sigle")
            mandats_an.append({
                "categorie": "mandat_electif",
                "categorie_source": CATEGORIE_SOURCE_AN,  # #718
                "type": "mandat",
                "label": "Mandat parlementaire" + (f" ({groupe_label_an})" if groupe_label_an else ""),
                "debut": periode.get("debut"),
                "fin": periode.get("fin"),
                "actif": not periode.get("fin"),
                # Traçabilité (AGENTS.md §2 règle 2) : l'archive qui a rendu la
                # période, la même que celle des mandats `groupe_politique`
                # ajoutés plus bas. Les mandats déjà publiés gardent leur
                # `source_url` à `null` — la fusion additive conserve l'entrée
                # ancienne —, mais aucune des périodes reconstruites ici n'est
                # publiée sans dire d'où elle vient.
                "source_url": AN_ACTEURS_HISTORIQUE_ZIP_URL,
                # Ce chemin n'est atteignable que pour `chambre == "deputes"`
                # (`identite_an` n'est résolue que là), mais la valeur est lue
                # sur la variable et non écrite en dur : une constante ici
                # serait une chambre inventée le jour où le garde-fou bouge.
                # #492 : la chambre est celle du jeu de données qui a rendu le
                # mandat, y compris pour une période reconstruite
                # rétrospectivement — AMO30 est l'Assemblée nationale.
                "chambre": chambre,
            })
        profile["mandats"] = mandats_an

        if _is_empty_payload(profile["mandats"]):
            warnings.append(avertissement(
                f"{WARNING_PREFIX_MANDATS_INTROUVABLES} : aucun mandat/responsabilité "
                "trouvé dans le référentiel officiel Assemblée nationale.",
                # Un constat de la source, qui nomme sa source (§2 règle 2) et
                # explique une liste vide plus précisément que `couverture`.
                DESTINATAIRE_LECTEUR,
            ))

        # --- 5bis. Positions dans l'hémicycle (Assemblée nationale, référentiel
        # officiel des organes — voir fetch_positions_hemicycle_officielles). Ne
        # couvre que les législatures achevées (positionPolitique jamais qualifié
        # par l'AN pour la législature en cours) pour majorité/opposition/
        # minoritaire : ajoute une entrée de mandat "groupe_politique" par période
        # qualifiée, jamais sans source_url. Ajoute également une entrée de mandat
        # "fonction_gouvernementale" par période d'appartenance à un gouvernement
        # (position "gouvernement"), non limitée aux législatures achevées. ---
        try:
            positions_hemicycle = fetch_positions_hemicycle_officielles(profile["identite"].get("url_an_ou_senat"))
        except Exception as exc:
            warnings.append(avertissement(
                f"positions dans l'hémicycle (Assemblée nationale) indisponibles : {exc}",
                DESTINATAIRE_INTERNE,
            ))
            positions_hemicycle = []
        for periode in positions_hemicycle:
            sigle = periode.get("groupe_sigle")
            position = periode.get("position")
            if position == "gouvernement":
                categorie = "fonction_gouvernementale"
                label = f"Gouvernement ({sigle})" if sigle else "Gouvernement"
            else:
                categorie = "groupe_politique"
                label = f"Groupe politique ({sigle})" if sigle else "Groupe politique"
            profile["mandats"].append({
                "categorie": categorie,
                # #718 — même archive que les mandats catégoriels
                # (AN_ACTEURS_HISTORIQUE_ZIP_URL) : la catégorie est établie par
                # la `positionPolitique` que l'Assemblée publie, pas par nous.
                "categorie_source": CATEGORIE_SOURCE_AN,
                "type": "membre",
                "label": label,
                "debut": periode.get("debut"),
                "fin": periode.get("fin"),
                "actif": not periode.get("fin"),
                "source_url": AN_ACTEURS_HISTORIQUE_ZIP_URL,
                "position_dans_hemicycle": position,
            })

    # --- 6. Votes : open data officiel de l'Assemblée nationale, SEULE source
    # depuis #528. Le repli sur les champs bruts NosSénateurs (`votes_raw`) est
    # parti avec le Sénat : il n'était atteignable que pour cette chambre. ---
    official_votes: list[dict[str, Any]] = []
    official_legislatures: list[str] = []
    if profile.get("identite"):
        try:
            official_votes, official_legislatures = fetch_votes_officiels(
                profile["identite"].get("url_an_ou_senat"), warnings
            )
        except Exception as exc:
            warnings.append(avertissement(
                f"votes officiels (Assemblée nationale) indisponibles : {exc}",
                DESTINATAIRE_INTERNE,
            ))

    if official_votes:
        profile["votes"] = [
            {
                "date": v.get("date"),
                "titre": v.get("titre"),
                "position": v.get("position"),
                "numero_scrutin": v.get("numero"),
                "sort": v.get("sort"),
                "legislature": v.get("legislature"),
                # Qualification sourcée du scrutin (#639) : recopiée telle
                # quelle depuis l'archive, jamais déduite du libellé. Absente
                # des votes collectés avant #639 — `scrutins_index` conserve
                # alors la valeur déjà publiée plutôt que de régresser.
                "type_scrutin": v.get("type_scrutin"),
                "type_vote": v.get("type_vote"),
                "demandeur": v.get("demandeur"),
                # Source primaire du scrutin (règle 2). Portée par le vote
                # lui-même et non déduite de `votes_source` : celui-ci couvre
                # désormais plusieurs législatures, dont aucune ne vaut pour
                # tous les votes du profil.
                "url_source": (
                    AN_SCRUTIN_PAGE_URL.format(
                        legislature=v.get("legislature"), numero=v.get("numero")
                    )
                    if v.get("legislature") and v.get("numero")
                    else None
                ),
            }
            for v in official_votes
        ]
        # Reflète l'ENSEMBLE des législatures agrégées : afficher « législature 16 »
        # au singulier alors que plusieurs sont couvertes rendrait la limite du
        # jeu de données illisible (AGENTS.md §2.8).
        libelle_legislatures = (
            f"législature {official_legislatures[0]}"
            if len(official_legislatures) == 1
            else f"législatures {', '.join(official_legislatures)}"
        )
        profile["votes_source"] = (
            f"open data Assemblée nationale (data.assemblee-nationale.fr, {libelle_legislatures})"
        )
        profile["meta"]["synchro_sources"]["assemblee_nationale"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    else:
        warnings.append(avertissement(
            f"{WARNING_PREFIX_VOTES_INTROUVABLES} : aucune correspondance officielle "
            "Assemblée nationale n'a été trouvée pour ce parlementaire/cette "
            "législature (voir fetch_votes_officiels).",
            # Le cas qui a motivé #642 : sur /candidats/bruno-retailleau, c'est
            # la seule phrase qui dise POURQUOI la page est vide, et elle est
            # plus précise que `couverture`, qui n'en dit que `non_collecte`.
            DESTINATAIRE_LECTEUR,
        ))

    # --- 6bis. Amendements officiels (Assemblée nationale, auteur principal uniquement,
    # toutes législatures disponibles — voir fetch_amendements_officiels). ---
    if profile.get("identite"):
        try:
            profile["amendements"] = fetch_amendements_officiels(
                profile["identite"].get("url_an_ou_senat"), warnings
            )
        except Exception as exc:
            _tracer_echec_collecte(
                warnings, exc,
                liste="amendements",
                etape="fetch_amendements_officiels",
                prefixe_panne=WARNING_PREFIX_AMENDEMENTS_INDISPONIBLES,
            )

    # --- 8. Textes portés officiels (Assemblée nationale, rôle factuel
    # auteur/rapporteur/co-rapporteur réel — voir fetch_textes_portes_officiels).
    # SEULE source de `dossiers_legislatifs` depuis #528 : l'étape 8 historique,
    # qui triait la liste NosDéputés collectée pour les sénateurs, est partie
    # avec le Sénat. ---
    if profile.get("identite") and not skip_dossiers_legislatifs:
        try:
            profile["dossiers_legislatifs"] = fetch_textes_portes_officiels(profile["identite"].get("url_an_ou_senat"))
        except Exception as exc:
            _tracer_echec_collecte(
                warnings, exc,
                liste="textes_portes",
                etape="fetch_textes_portes_officiels",
                prefixe_panne="textes portés officiels (Assemblée nationale) indisponibles",
            )

    # --- 9. Interventions : Syceron (débats officiels AN), SEULE source depuis
    # #510. Le repli NosDéputés a été retiré : il ne complétait pas la source
    # primaire, il la remplaçait intégralement — 789 interventions publiées, dont
    # **0** de Syceron, sur un chemin dont Syceron est la source déclarée. C'est
    # ce repli qui a rendu le défaut invisible pendant toute sa durée de vie : le
    # chemin RENDAIT quelque chose, donc rien ne signalait que la source primaire
    # était muette.
    #
    # Une collecte vide reste donc vide, et le dit (§2.5) — c'est le seul état
    # dans lequel la panne d'une source se lit. Elle n'efface rien pour autant :
    # la fusion additive conserve les interventions déjà acquises, et #465
    # interdit à une collecte vide d'écraser une liste non vide même en
    # --no-merge.
    #
    # Le garde `chambre == "deputes"` est tombé avec #528 : c'est désormais la
    # seule chambre collectée. ---
    if not skip_interventions and profile.get("identite"):
        syceron_interventions: list[dict[str, Any]] = []
        try:
            with budget_section(budget_phase_interventions, "débats Syceron"):
                syceron_interventions = fetch_interventions_syceron(
                    profile["identite"].get("url_an_ou_senat"),
                    budget_phase_interventions,
                    theme_seul=interventions_theme_seul,
                )
        except Exception as exc:
            syceron_interventions = []
            _tracer_echec_collecte(
                warnings, exc,
                liste="interventions",
                etape="fetch_interventions_syceron",
                prefixe_panne=WARNING_PREFIX_INTERVENTIONS_SYCERON_INDISPONIBLES,
            )
        if syceron_interventions:
            profile["interventions"] = syceron_interventions
            profile["meta"]["synchro_sources"]["assemblee_nationale_syceron"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        else:
            # #560 — CE chemin n'est pas une panne : la collecte est allée au
            # bout sans lever, donc les archives ont répondu. Ce qu'on constate
            # est un zéro, et un zéro constaté est publiable. La disjonction que
            # portait l'ancien message (« absent des archives, OU archive
            # indisponible ») n'a plus lieu d'être : l'autre terme a son propre
            # préfixe, écrit par la branche `except` ci-dessus.
            warnings.append(avertissement(
                f"{WARNING_PREFIX_INTERVENTIONS_SYCERON_AUCUNE} : les archives "
                "Syceron ont répondu et ne portent aucune intervention pour cet "
                "acteurRef. Ce n'est pas une panne : c'est un zéro constaté dans "
                "le périmètre de la source. Le repli NosDéputés a été retiré "
                "(#510) : aucune autre source ne comble ce silence.",
                # Un zéro constaté, qui nomme sa source et sa borne — même
                # registre que « votes introuvables ». Le texte porte encore
                # `acteurRef` et un numéro d'issue : c'est la dette nommée dans
                # `docs/decisions/destinataire-avertissements-642.md`, à traiter
                # par le lot d'affichage, pas par une réécriture silencieuse.
                DESTINATAIRE_LECTEUR,
            ))

    # --- 9bis. Questions parlementaires officielles (QE/QG/QOSD, Assemblée nationale,
    # auteur uniquement, toutes législatures disponibles). Ajoutées aux interventions
    # déjà collectées (type_detail="question", source AN structurée). ---
    # #657 : `interventions_theme_seul` les écarte. Elles ne portent ni
    # `seance_ref` ni `session_ref`, donc `normalize_profil` en dérive
    # `theme_officiel = None`, et leur `mots_cles` est vide par construction :
    # elles ne rendent PAS UNE étiquette thématique. Elles sont en revanche le
    # seul poste réseau du chemin interventions qui grandisse avec le nombre de
    # membres — l'index Syceron, lui, se construit une fois par législature.
    if not skip_interventions and not interventions_theme_seul and profile.get("identite"):
        try:
            with budget_section(budget_phase_interventions, "questions officielles"):
                official_questions = fetch_questions_officielles(
                    profile["identite"].get("url_an_ou_senat"), budget_phase_interventions
                )
            if official_questions:
                profile["interventions"].extend(official_questions)
                profile["meta"]["synchro_sources"]["assemblee_nationale_questions"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        except Exception as exc:
            _tracer_echec_collecte(
                warnings, exc,
                liste="interventions",
                etape="fetch_questions_officielles",
                prefixe_panne=WARNING_PREFIX_QUESTIONS_INDISPONIBLES,
            )

    # --- 9ter. Le budget a-t-il tronqué la collecte ? (#498) Consigné en tout
    # dernier, une fois toutes les sections passées, pour que le décompte porte
    # sur l'ensemble et non sur une seule d'entre elles. Un profil tronqué reste
    # un profil écrit et publié : c'est tout l'intérêt d'un budget interne face à
    # un `timeout-minutes` qui, lui, tue le process avant l'écriture.
    message_budget = annoncer_troncature(budget_interventions, f"{chambre}/{slug}")
    if message_budget:
        warnings.append(avertissement(
            f"{WARNING_PREFIX_BUDGET_INTERVENTIONS} : {message_budget}",
            # Troncature de CE run, que `couverture` publie déjà en `panne`.
            DESTINATAIRE_INTERNE,
        ))

    # L'étape 9quater de #514 (« la source a-t-elle répondu ? ») et le canal
    # `journal` qui la remontait à `build_profile_any_chambre` sont partis avec
    # les compteurs qu'ils lisaient (#529). Ils distinguaient « NosDéputés dit
    # que ce slug n'existe pas » de « NosDéputés n'a rien dit » ; l'identité ne
    # part plus sur le réseau du tout — elle se résout dans une archive AMO30
    # déjà en cache — et il n'y a donc plus de silence à qualifier. Une archive
    # absente ou illisible, elle, lève : c'est l'exception de l'étape 0, qui est
    # nommée dans `meta.warnings`, pas un compteur.

    # #642 : le jumeau typé de `meta.warnings`, écrit en dernier — c'est un
    # champ DÉRIVÉ, comme `chambres` (#493) et `licence_donnees` (#530), et il
    # doit être recomposé après la dernière mutation de la liste, pas avant.
    # Ici, il fait franchir au typage l'aller-retour JSON du profil brut : la
    # passe pivot relit des chaînes nues, ce bloc est ce qui les retype.
    deriver_avertissements(profile["meta"])

    return profile


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug", help="Identifiant du parlementaire, ex: jean-luc-melenchon")
    parser.add_argument(
        "--chambre",
        choices=["deputes"],
        default="deputes",
        help="Chambre concernée (seule valeur : deputes — le Sénat est hors périmètre depuis #528)",
    )
    parser.add_argument(
        "--out",
        help="Chemin du fichier JSON de sortie (défaut: raw_data/profiles/<slug>.json)",
    )
    # `--max-pages` a été retiré avec la recherche NosDéputés qu'il bornait
    # (#510) : plus aucune page de résultats n'est parcourue.
    parser.add_argument(
        "--activer-interventions-syceron",
        action=RefusDrapeauInterventionsSyceron,
    )
    args = parser.parse_args()


    profile = build_profile(args.chambre, args.slug)

    out_path = Path(args.out) if args.out else Path("raw_data/profiles") / f"{args.slug}.json"
    # #580 : écriture partitionnée — socle `<slug>.json` + `<slug>/<legislature>.json`.
    # `--out` reste un chemin de SOCLE, comme avant : c'est le nom qui porte le
    # slug, et les tranches sont son répertoire frère.
    if out_path.suffix != ".json":
        raise SystemExit(
            f"--out doit désigner un fichier `.json` (socle du profil) : {out_path}"
        )
    ecrire_profil_brut(out_path.parent, out_path.stem, profile)

    nb_votes = len(profile["votes"])
    print(f"\n✓ Profil écrit dans {out_path}")
    print(f"  - Identité récupérée : {'oui' if profile['identite'] else 'non'}")
    print(f"  - Votes récupérés : {nb_votes}")
    if profile["meta"].get("warnings"):
        print("  [!] " + " | ".join(profile["meta"]["warnings"]))
    elif nb_votes == 0:
        print("  [!] Aucun vote récupéré : vérifie le slug, la chambre, ou la structure JSON renvoyée par l'API (peut avoir changé).")


if __name__ == "__main__":
    main()
