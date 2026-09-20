#!/usr/bin/env python3
"""
gouvernement_textes.py — Collecte des dossiers législatifs d'origine
gouvernementale et extraction de leur statut, depuis le dump bulk
`Dossiers_Legislatifs.json.zip` de l'Assemblée nationale.

Suit le même principe que `syceron_debates.py`/`parse_syceron.py`
(téléchargement/cache réseau séparé du parsing pur, pour un parseur testable
sans réseau — voir docs/decisions/syceron.md), mais dans un seul
fichier : `ensure_dossiers_zip_downloaded()` est la seule fonction de ce
module à toucher le réseau ou le disque ; le reste opère sur un
`zipfile.ZipFile` déjà ouvert (fixture locale possible pour les tests).

Réutilisation de l'infrastructure existante (issue #210) : `candidate_profile.py`
téléchargeait/cachait déjà `Dossiers_Legislatifs.json.zip` (deux fois, de
façon dupliquée, dans `_build_texte_titre_index` — retirée par #639 — et
`_build_acteur_textes_portes_index`) sous les mêmes `AN_DOSSIERS_ZIP_URL`/
`DOSSIERS_CACHE_DIR`. Ce module en devient la source canonique :
`candidate_profile.py` importe désormais ces constantes et
`ensure_dossiers_zip_downloaded()` depuis ici plutôt que de dupliquer le
téléchargement — un seul cache, un seul verrou, pas de second téléchargement
du même fichier ~10 Mo.

Archives (#400) : `AN_DOSSIERS_ARCHIVES` (défini dans `couverture_dossiers.py`
depuis #399, ré-exporté ici) liste une archive par législature (15, 16, 17). Chacune est déjà multi-législature mais ne garde des
précédentes qu'une traîne résiduelle — la seule archive 17 ne contient aucun
projet de loi antérieur à la XVI. Les dossiers vus dans plusieurs archives
sont dédupliqués par uid, la législature la plus élevée faisant foi (état le
plus à jour des actes, donc du statut) : voir `iter_dossiers_bruts`.

Origine gouvernementale (art. 39 de la Constitution) — signal primaire depuis
#400 : le **type du document déposé**, préfixe de l'uid du `texteAssocie` de
l'acte `*-DEPOT` le plus ancien (`PRJL` = projet de loi, `PION` = proposition,
`PNRE` = résolution, donc hors champ). Le préfixe de `titreDossier.titre`
retenu jusque-là (spike #207) ne fonctionne que sur les XVI/XVII : sur la XV
les titres sont descriptifs (« Taxe sur les services numériques »,
« Démocratie plus représentative, responsable, efficace ») et le filtre y
retenait **zéro** projet de loi déposé entre 2017 et 2019. Sur le corpus
complet, il ne voyait que 271 des 726 dossiers gouvernementaux.

`procedureParlementaire.code` sert de repli quand aucun document de dépôt
n'est résolvable, et seulement pour les codes univoques : les codes 5 et 7
(« Projet **ou** proposition de loi organique/constitutionnelle ») sont exclus
du repli, car deviner violerait AGENTS.md §2.5. Le document prime sur la
procédure quand les deux divergent — 8 dossiers de règlement du budget sont
typés « Proposition de loi ordinaire » à la source alors que le document
déposé est bien un `PRJL`.

Statut (nomenclature fermée `schema_gouvernement.KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL`) :
porté par `statutConclusion.fam_code` d'un acte de décision de séance
(`codeActe` contenant `-DEBATS-` et se terminant par `-DEC` — voir
`_est_decision_de_seance` : AN1-DEBATS-DEC, SN1-DEBATS-DEC,
CMP-DEBATS-{AN,SN}-DEC, {AN,SN}NLEC-DEBATS-DEC constatés — un simple
`endswith("-DEBATS-DEC")` manquerait les codes de commission mixte
paritaire), PAS par `codeActe` seul (qui ne distingue pas les issues, voir
spike #207). Seule la décision de séance chronologiquement la plus récente
détermine le statut courant du dossier : un dossier peut accumuler
plusieurs décisions de séance au fil des lectures (ex. adopté en 1ère
lecture puis modifié par la seconde chambre — la navette continue, ce n'est
pas un statut final ; c'est le cas de `TSORTF05`, « modifié »). 10 `fam_code`
sont mappés : 4 confirmés par le spike #207, 3 ajoutés en #397 après
constat que leur absence excluait 45 dossiers sur 106 du jeu de données, 3
ajoutés en #402 après l'ingestion des archives XV/XVI (#400).
Tout autre `fam_code` rencontré sur la décision de séance la plus récente
produit un warning explicite et `statut = None` — jamais un statut par
défaut (règle AGENTS.md §2.5). Les décisions du Conseil
constitutionnel (`CC-CONCLUSION`) et les constats d'accord/désaccord de CMP
(`CMP-DEC`) portent aussi un `statutConclusion` mais ne sont pas des
décisions de séance sur le texte : ils sont volontairement exclus du calcul
du statut. `fam_code == "TSORTFnull"` est un artefact du dataset source signalant
l'absence de statut réel (constaté sur un acte de « décision » sans issue
tranchée) : traité comme absence d'événement, jamais comme un `fam_code`
inconnu à signaler.

Initiateurs (#435) : `initiateur.acteurs.acteur[].acteurRef` est extrait tel
quel dans `initiateurs_acteur_refs` — le lien membre → texte, pendant de
`role_signataire` pour les amendements. Aucune résolution vers un `membre_id`
ici : elle demande la composition du gouvernement, connue de
`gouvernement_profile.py` seulement. `acteurRef` n'est PAS utilisé comme
signal d'origine (la chaîne `acteurRef -> mandat GOUVERNEMENT -> organeRef` a
été écartée pour cela, ~15 % de faux positifs mesurés par le spike #207, voir
docs/decisions/gouvernement-textes-statut-210-version-initiale.md#gouvernement-textes-statut) : ici la source dit
qui a déposé, pas de quelle origine est le texte.

Retrait : `codeActe` dédié (`AN1-RTRINI`/`ANLUNI-RTRINI`), sans
`statutConclusion` associé (spike #207).

Promulgation (#400) : un `codeActe` `PROM`/`PROM-PUB` (publication au Journal
officiel) est le fait le plus avancé et le plus vérifiable du parcours. Il
corrige les statuts qu'il rend factuellement faux — `navette_en_cours`,
`depose`, `rejete`, `rejete_49_3`, ou statut indéterminé — en `promulgue`. Il
n'écrase JAMAIS `adopte_cmp`/`adopte_49_3` : ces statuts portent la voie
procédurale suivie, que `promulgue` ne dit pas, et les écraser ferait
disparaître le fait CMP ou 49.3 de 116 textes (collapse interdit par §2.4).
`retire` n'est pas écrasé non plus : retrait puis promulgation est
contradictoire, et trancher n'est pas notre rôle. Le warning d'un `fam_code`
non mappé est conservé même quand la promulgation détermine le statut : le
code reste inconnu et mérite d'être signalé.

`TSORTF24` (« rejeté via 49.3, motion de censure adoptée », ex. le budget
2025 sous le gouvernement Barnier) est mappé à `statut = "rejete_49_3"` avec
`sort_49_3 = True`, symétrique d'`adopte_49_3` — le 49.3 reste un fait
procédural distinct de l'issue du vote, jamais fusionné avec elle (règle
AGENTS.md §2.4). `rejete_49_3` a été ajouté à la nomenclature fermée de #208
après coup (docs/decisions/gouvernement-textes-statut-49-3-rejete.md),
donc cette combinaison est représentable par
`schema_gouvernement.validate_profil_gouvernement` sans warning.

`TSORTF18` (« adopté, dans les conditions prévues à l'article 45, alinéa 3,
de la Constitution » : approbation du texte élaboré en commission mixte
paritaire, sur demande du Gouvernement) suit la même logique et est mappé à
un statut dédié `adopte_cmp`, avec `sort_49_3 = False`. L'issue est bien une
adoption, mais la voie procédurale est distincte et n'est pas fondue dans
`adopte` — arbitrage tranché en #397, symétrique de celui de #208 sur le
49.3. Un texte de CMP sur lequel le Gouvernement engagerait ensuite sa
responsabilité relève de `TSORTF06`/`TSORTF24`, pas de `TSORTF18` : seule la
décision de séance la plus récente compte, il n'y a donc pas de cumul
possible entre `adopte_cmp` et les statuts 49.3.

`TSORTF02` (« adopté avec modifications ») décrit le **même fait procédural**
que `TSORTF05` (« modifié ») — une chambre adopte un texte qu'elle a modifié,
donc la navette continue — et est mappé au même `navette_en_cours`. Ce n'est
pas une supposition : sur les 53 occurrences des trois archives, les 29 qui ne
sont pas la dernière décision du dossier sont **toutes** suivies d'une lecture
dans l'autre chambre (« modifié » ×17, « adopté sans modification » ×8, CMP,
rejet). Le libellé pouvait laisser croire à une adoption effective, mais parmi
les 24 occurrences terminales, 7 ne sont jamais promulguées (ex. la réforme de
l'audiovisuel public, `DLR5L16N47697`) : les traiter en `adopte` affirmerait
une adoption que rien n'établit (§2.5). Les 17 autres portent un acte de
promulgation, qui détermine alors le statut (`promulgue`) par le mécanisme
de #400 — plus fort et plus vérifiable que la décision de séance elle-même.

`TSORTF14` (« voté par les deux assemblées du Parlement en termes
identiques ») est mappé à `adopte` : le vote conforme des deux chambres est
une adoption parlementaire achevée. Unique occurrence : le projet de loi
constitutionnelle sur le corps électoral calédonien (`DLR5L16N49373`, AN le
14/05/2024), jamais promulgué faute de Congrès — d'où `adopte` et non
`promulgue`, la distinction étant précisément ce que le statut doit préserver.

`TSORTF13` (« rejeté définitivement ») est mappé à `rejete`, avec
`sort_49_3 = False` : le rejet est prononcé par un vote, pas par le rejet
d'un engagement de responsabilité (`TSORTF24`). Unique occurrence : le
règlement du budget 2021 (`DLR5L16N45929`), rejeté en lecture définitive à
l'AN le 03/08/2022 après deux rejets du Sénat.

Rattachement à un gouvernement (hors périmètre de ce module, implémenté dans
`gouvernement_profile.py` — #211) : par date de dépôt initial (`date_depot`,
calculée ici), jamais par date de statut final — décision actée dans le plan
d'implémentation de #184 (issue #210) : un texte déposé sous un gouvernement A
puis conclu sous un gouvernement B reste crédité au gouvernement A, qui l'a
initié. Voir `docs/decisions/gouvernement-profile-rattachement.md`.

Hors périmètre : couverture Sénat comme chambre de dépôt *primaire* d'un
dossier (le Sénat n'a pas de dataset équivalent exploitable — voir
docs/decisions/hors-perimetre.md) ; seuls les dossiers du dump AN
sont vus ici, y compris ceux transmis en 2e lecture au Sénat (`chambre_depot_initial`
peut valoir `"Senat"` si un dossier AN a été déposé au Sénat en 1ère lecture).
"""

import json
import threading
import zipfile
from pathlib import Path
from collections.abc import Iterator
from typing import Any, Optional

import requests

from download_watchdog import download_with_watchdog
from schema_gouvernement import KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL

# Inventaire des archives ingérées : déplacé dans `couverture_dossiers.py`
# (#399), qui n'a aucune dépendance réseau et peut donc être importé par
# l'audit et le quality gate pour en déduire la borne de couverture
# temporelle. Ré-exporté ici, où le reste du dépôt le référence déjà.
from couverture_dossiers import (  # noqa: F401
    AN_DOSSIERS_ARCHIVES,
    AN_DOSSIERS_LEGISLATURES_ACTIVES,
    AN_OPENDATA_BASE,
)

# Législature dont l'archive garde le nom de cache historique `dossiers.zip` :
# la renommer invaliderait le cache CI existant et forcerait un
# re-téléchargement de ~10 Mo sans bénéfice.
_LEGISLATURE_CACHE_HISTORIQUE = 17

DOSSIERS_CACHE_DIR = Path(".cache") / "dossiers_an"

HEADERS = {
    "User-Agent": "cv-politique-gouvernement-textes/0.1 (usage personnel / non commercial)"
}
TIMEOUT = (15, 600)

_ZIP_DOWNLOAD_LOCK = threading.Lock()

# Origine (art. 39 de la Constitution) — voir docstring du module.
#
# Signal primaire : préfixe de l'uid du document déposé en premier
# (`texteAssocie` de l'acte `*-DEPOT` le plus ancien). C'est le type du texte
# réellement déposé, encodé par l'AN elle-même.
_DOC_PREFIX_GOUVERNEMENTAL = "PRJL"   # projet de loi
_DOC_PREFIX_PARLEMENTAIRE = "PION"    # proposition de loi
# PNRE (proposition de résolution) et les dossiers sans document de dépôt ne
# sont pas des textes de loi : ni gouvernementaux, ni parlementaires.

# Nature du texte déposé (#689) : la MÊME lecture de la même source, rendue une
# valeur plus fine que l'origine. `_origine` en dérive (voir `_origine`), pour
# qu'un seul endroit du dépôt lise ce que l'archive encode.
#
# `PNRE` y gagne une valeur propre, là où `_origine` le range avec l'inconnu.
# Pour une fiche de gouvernement c'est sans effet (une résolution n'est pas un
# texte du Gouvernement, donc hors périmètre dans les deux cas) ; pour un texte
# porté par un·e parlementaire c'est un fait distinct et sourcé — une
# proposition de résolution est une initiative personnelle, et la confondre
# avec « nature non établie » perdrait 31 des 472 entrées publiées (relevé du
# 01/09/2026).
_NATURE_PAR_PREFIXE_DOCUMENT: dict[str, str] = {
    _DOC_PREFIX_GOUVERNEMENTAL: "projet_de_loi",
    _DOC_PREFIX_PARLEMENTAIRE: "proposition_de_loi",
    "PNRE": "proposition_de_resolution",
}

# Signal de repli : `procedureParlementaire.code`, quand aucun document de
# dépôt n'est résolvable. Ne couvre que les procédures législatives dont
# l'origine est univoque — les codes 5 et 7 (« Projet **ou** proposition de loi
# organique/constitutionnelle ») sont volontairement absents : leur libellé ne
# tranche pas, et deviner violerait AGENTS.md §2.5.
_PROCEDURE_CODES_GOUVERNEMENTAUX = frozenset({
    "1",   # Projet de loi ordinaire
    "3",   # Projet de loi de finances de l'année
    "4",   # Projet de loi de financement de la sécurité sociale
    "6",   # Projet de ratification des traités et conventions
    "21",  # Projet de loi de finances rectificative
    "33",  # Projet de loi relative aux résultats de la gestion et au budget
})
_PROCEDURE_CODES_PARLEMENTAIRES = frozenset({
    "2",   # Proposition de loi ordinaire
    "23",  # Proposition de loi présentée en application de l'article 11
})
# Même critère d'univocité, pour la nature seulement (#689) : ces deux libellés
# ne désignent qu'une proposition de résolution. Aucune incidence sur `_origine`,
# qui ne connaît que les textes de loi. Ne se déclenche aujourd'hui sur AUCUNE
# des 472 entrées publiées : les 31 résolutions du corpus portent toutes leur
# document `PNRE`, et le repli ne sert qu'aux dossiers qui n'en ont pas.
_PROCEDURE_CODES_RESOLUTION = frozenset({
    "8",   # Résolution
    "22",  # Résolution Article 34-1
})

# Nature -> origine (art. 39). Une proposition de résolution n'est ni un texte
# gouvernemental ni un texte de loi parlementaire : absente de la table, elle
# rend `None`, exactement ce que `_origine` rendait avant #689.
_ORIGINE_PAR_NATURE: dict[str, str] = {
    "projet_de_loi": "gouvernemental",
    "proposition_de_loi": "parlementaire",
}

# fam_code -> (statut, sort_49_3). Toute autre valeur produit un warning et
# `statut = None` (voir docstring du module) : la nomenclature reste fermée.
#
# Le libellé cité en commentaire est celui porté par le dataset AN lui-même
# (`statutConclusion.libelle`), pas une interprétation de notre part — c'est
# la seule justification acceptable d'un mapping, et elle est vérifiable en
# relisant l'archive.
_FAM_CODE_STATUT_MAP: dict[str, tuple[str, bool]] = {
    # Confirmés par le spike #207 (docs/sources/an-opendata.md).
    "TSORTF01": ("adopte", False),           # « adopté » / « adoptée »
    "TSORTF07": ("rejete", False),           # « rejeté » / « rejetée »
    "TSORTF06": ("adopte_49_3", True),       # « considéré comme adopté […] 49 al. 3 »
    "TSORTF24": ("rejete_49_3", True),       # « considéré comme rejeté […] 49 al. 3 »
    # Ajoutés en #397 : non mappés, ils excluaient 45 dossiers sur 106 du jeu
    # de données (42 %), dont le PLF 2025.
    "TSORTF03": ("adopte", False),           # « adopté sans modification »
    "TSORTF18": ("adopte_cmp", False),       # « adopté […] art. 45 al. 3 » (texte de CMP)
    "TSORTF05": ("navette_en_cours", False), # « modifié » — la navette continue
    # Ajoutés en #402, apparus avec l'ingestion des archives XV/XVI (#400).
    "TSORTF02": ("navette_en_cours", False), # « adopté avec modifications » — idem TSORTF05
    "TSORTF14": ("adopte", False),           # « voté par les deux assemblées […] termes identiques »
    "TSORTF13": ("rejete", False),           # « rejeté définitivement »
}

# Sentinelle du dataset source : absence de statut réel, pas un fam_code
# inconnu (voir docstring du module).
_FAM_CODE_SENTINEL_VIDE = "TSORTFnull"

# codeActe dédiés au retrait, sans statutConclusion associé (spike #207).
_CODE_ACTE_RETRAIT = frozenset({"AN1-RTRINI", "ANLUNI-RTRINI"})

# Promulgation (publication au Journal officiel) : `PROM` et `PROM-PUB`.
_CODE_ACTE_PROMULGATION_PREFIXE = "PROM"

# Statuts qu'un acte de promulgation corrige (#400). La promulgation est le
# fait le plus avancé du parcours, donc ces statuts sont factuellement faux
# dès qu'elle existe : un texte promulgué n'est ni en navette, ni rejeté.
#
# `adopte`, `adopte_cmp` et `adopte_49_3` sont volontairement ABSENTS : ils
# portent la voie procédurale suivie, que `promulgue` ne dit pas. Les écraser
# ferait disparaître le fait CMP ou 49.3 de 116 textes — le collapse
# qu'interdit AGENTS.md §2.4. `retire` l'est aussi : un texte retiré puis
# promulgué serait contradictoire, et deviner lequel des deux actes fait foi
# n'est pas notre rôle.
_STATUTS_CORRIGES_PAR_PROMULGATION = frozenset({
    None, "depose", "navette_en_cours", "rejete", "rejete_49_3",
})


def _est_decision_de_seance(code_acte: str) -> bool:
    """Décision de séance sur le texte lui-même (adoption/rejet/49.3), par
    opposition à un simple constat (`CMP-DEC`, accord/désaccord de la
    commission mixte paritaire) ou à une conclusion hors séance (`CC-CONCLUSION`,
    Conseil constitutionnel) — les deux portent aussi un `statutConclusion`
    mais ne tranchent pas le sort du texte. Constaté sur : `AN1-DEBATS-DEC`,
    `SN1-DEBATS-DEC`, `CMP-DEBATS-AN-DEC`, `CMP-DEBATS-SN-DEC`,
    `ANNLEC-DEBATS-DEC`, `SNNLEC-DEBATS-DEC` (spike #207) — d'où un motif
    `-DEBATS-` + suffixe `-DEC` plutôt qu'un simple `endswith("-DEBATS-DEC")`,
    qui manquerait les codes de commission mixte paritaire (`CMP-DEBATS-{AN,SN}-DEC`)."""
    return "-DEBATS-" in code_acte and code_acte.endswith("-DEC")


# ── Ce qui atteste un EXAMEN en commission, et ce qui n'est qu'un dépôt (#997)
#
# `_determine_statut` et `candidate_profile._stade_from_code_acte` posaient
# chacun la même question — « ce dossier a-t-il dépassé le dépôt ? » — et y
# répondaient tous deux par « il existe un acte qui n'est pas un dépôt », donc
# par oui, toujours. Deux conséquences mesurées le 18/09/2026 sur les archives
# XV à XVII (10 764 dossiers) :
#
#   - `"depose"` était INATTEIGNABLE : un texte seulement déposé sortait
#     `navette_en_cours` (279 des 728 dossiers d'origine gouvernementale) ;
#   - **6 808 dossiers étaient qualifiés `examine_commission` sans avoir été
#     examinés**, dont 5 219 entrées de `textes_portes[]` publiées.
#
# La cause est dans la nomenclature de la source : la saisine de la commission
# est AUTOMATIQUE au dépôt, et elle porte un code contenant `COM`. Relevé sur
# les trois archives, un dossier déposé et rien de plus porte :
#
#     AN1                       (l'étape de lecture, sans date)
#     AN1-DEPOT                 2024-01-25
#     AN1-COM                   (conteneur, sans date)
#     AN1-COM-FOND              (conteneur, sans date)
#     AN1-COM-FOND-SAISIE       2024-01-25   ← même jour que le dépôt
#
# Vérifié à la main sur `DLR5L16N49329`, `DLR5L16N49108`, `DLR5L16N48166`
# (propositions de loi de Marine Le Pen) : 14 nœuds d'actes, aucun autre code.
#
# Les codes qui attestent un examen RÉEL, et leur effectif sur les trois
# archives : `-COM-FOND-REUNION` (3 672 AN + les variantes SN/ANLUNI/ANNLEC),
# `-COM-FOND-RAPPORT` (1 095 AN, 997 SN), `-COM-AVIS-REUNION` (703),
# `-COM-AVIS-RAPPORT` (129), `CMP-COM-RAPPORT-{AN,SN}` (285 + 281).
#
# ARBITRÉ LE 18/09/2026, option B : c'est la **réunion de commission ou le
# dépôt du rapport** qui fait passer un texte de « déposé » à « examiné ».
# Écartées : la nomination d'un rapporteur (`-NOMIN`, 1 133 AN + 1 003 SN),
# qui dit que la commission s'organise et non qu'elle a examiné ; la discussion
# en séance (`-DEBATS`), qui ferait redescendre à « déposé » les textes
# réellement examinés en commission mais jamais venus en séance.
#
# `-AVIS` est retenu à côté de `-FOND` : une commission saisie pour avis qui se
# réunit a examiné le texte. L'arbitrage porte sur l'acte, pas sur la
# commission qui le pose.
#
# **Ce que cette règle NE fait pas** : elle ne retire rien du corpus. Un texte
# seulement déposé est collecté et publié comme avant, sous `stade_procedural:
# "depose"` — 1 355 entrées le portaient déjà au 18/09/2026. Elle corrige une
# ÉTIQUETTE. Ce que l'interface montre en deçà du seuil d'AGENTS.md §6 est une
# règle d'affichage, et elle vit dans `web/UI_finale`.
# → `docs/decisions/examen-en-commission-997.md`
_MARQUEURS_EXAMEN_COMMISSION: tuple[str, ...] = ("REUNION", "RAPPORT")

#: Les codes SANS tiret sont des conteneurs : l'étape de lecture (`AN1`, `SN1`,
#: `ANLUNI`, `AN20`, `CMP`, `CC`, `ANLDEF`…) ou la phase (`PROM`), qui portent
#: les actes datés de cette étape. Mesuré le 18/09/2026 sur les archives XV à
#: XVII : **sur les 17 codes sans tiret, 16 ne portent JAMAIS de date** — 6 418
#: `AN1`, 603 `PROM`, 284 `CMP`, aucune date. Un conteneur existe dès le dépôt,
#: donc il n'atteste rien.
#:
#: `MOTION` est le seul qui en porte une (8 occurrences, 8 datées) : c'est un
#: acte réel, pas un conteneur. Il est nommé ici plutôt que déduit, et la limite
#: est dite : un code nu et daté qu'une archive future ajouterait serait compté
#: comme conteneur jusqu'à ce qu'il soit ajouté ici. Le relevé se refait avec
#: `scripts/` ou la mesure de la décision — c'est déclaré, pas présumé.
_CODES_NUS_DATES: frozenset[str] = frozenset({"MOTION"})


def est_examen_en_commission(code_acte: str) -> bool:
    """Vrai si ce `codeActe` atteste un examen en commission (#997, option B).

    Un code de commission qui n'est ni une réunion ni un rapport — la saisine
    automatique du dépôt, la nomination d'un rapporteur, les conteneurs `-COM`
    et `-COM-FOND` sans date — rend `False` : il dit que le texte a été
    *renvoyé*, pas qu'il a été *examiné*.
    """
    return "COM" in code_acte and any(
        marqueur in code_acte for marqueur in _MARQUEURS_EXAMEN_COMMISSION
    )


def est_acte_au_dela_du_depot(code_acte: str) -> bool:
    """Vrai si ce `codeActe` atteste que le dossier a dépassé le simple dépôt.

    C'est la question de `_determine_statut` : sans décision de séance, un
    dossier est `navette_en_cours` s'il a bougé, `depose` sinon.

    Trois familles rendent `False`, et chacune pour la même raison — elles
    existent dès le dépôt et n'attestent aucune étape franchie :

    1. le dépôt lui-même (`-DEPOT`) ;
    2. l'étape de lecture nue (`AN1`, `SN1`, `CMP`, `ANLUNI`…), un conteneur
       sans date qui porte les actes de cette lecture ;
    3. un acte de commission qui n'est pas un examen (`est_examen_en_commission`).
    """
    if code_acte.endswith("-DEPOT"):
        return False
    if "COM" in code_acte:
        return est_examen_en_commission(code_acte)
    if "-" in code_acte:
        return True
    return code_acte in _CODES_NUS_DATES



assert set(statut for statut, _ in _FAM_CODE_STATUT_MAP.values()) <= KNOWN_STATUTS_TEXTE_GOUVERNEMENTAL


def _chemin_cache_archive(legislature: int) -> Path:
    nom = (
        "dossiers.zip"
        if legislature == _LEGISLATURE_CACHE_HISTORIQUE
        else f"dossiers_{legislature}.zip"
    )
    return DOSSIERS_CACHE_DIR / nom


def ensure_dossiers_zip_downloaded(
    legislature: int = _LEGISLATURE_CACHE_HISTORIQUE, *, force_download: bool = False
) -> Optional[Path]:
    """Télécharge (si nécessaire) et met en cache l'archive d'une législature.

    Fonction réseau canonique pour ces dumps : réutilisée par
    `candidate_profile.py` (index titre/acteur) et par la collecte des
    dossiers gouvernementaux de ce module, pour éviter un second
    téléchargement/cache indépendant des mêmes fichiers (voir issue #210).
    `download_with_watchdog` (#370) assure l'écriture atomique, pour ne jamais
    laisser un cache partiellement écrit en cas d'échec réseau.

    Returns:
        Chemin local de l'archive, ou None si le téléchargement échoue.
    """
    url = AN_DOSSIERS_ARCHIVES.get(legislature)
    if url is None:
        return None

    with _ZIP_DOWNLOAD_LOCK:
        zip_path = _chemin_cache_archive(legislature)
        if not force_download and zip_path.is_file():
            return zip_path

        print(f"-> Téléchargement des dossiers législatifs (législature {legislature}) : {url}")
        try:
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            download_with_watchdog(url, zip_path, headers=HEADERS, timeout=TIMEOUT)
        except (requests.RequestException, OSError, TimeoutError) as exc:
            print(f"  [!] Échec du téléchargement des dossiers législatifs "
                  f"(législature {legislature}) : {exc}")
            return None
        return zip_path


def rafraichir_dossiers_actifs() -> list[int]:
    """Retélécharge les archives des législatures ENCORE EN COURS, et elles seules.

    POURQUOI CETTE FONCTION EXISTE (#762). `ensure_dossiers_zip_downloaded`
    court-circuite sur `zip_path.is_file()` : une archive déjà en cache n'est
    jamais reprise. En CI, `.cache/dossiers_an` porte une clé HEBDOMADAIRE
    doublée d'un `restore-keys` de préfixe — au changement de semaine, la clé
    exacte manque, le préfixe restaure le répertoire de la semaine précédente,
    le test d'existence passe, et le répertoire inchangé est resauvegardé sous
    la clé neuve. **La rotation se désamorce elle-même**, exactement comme dans
    #749 pour l'index des amendements.

    ET ELLES SEULES, PARCE QUE LES AUTRES NE PEUVENT PLUS CHANGER. Une
    législature dissoute ne produit plus d'acte : reprendre `dossiers_15.zip`
    (14,5 Mo) et `dossiers_16.zip` (8,7 Mo) chaque semaine serait 23 Mo de
    téléchargement pour un contenu identique. Seule la 17e est vivante — 9,8 Mo.
    La liste vient de `AN_DOSSIERS_LEGISLATURES_ACTIVES`, dérivée des archives
    déclarées : rien à tenir en double.

    Non-fatal : une archive qui échoue est omise, le run continue sur ce qu'il a
    — un rafraîchissement raté vaut mieux qu'un run perdu, et la donnée déjà en
    cache reste exploitable. Retourne les législatures effectivement reprises.
    """
    reprises: list[int] = []
    for legislature in sorted(AN_DOSSIERS_LEGISLATURES_ACTIVES):
        if ensure_dossiers_zip_downloaded(legislature, force_download=True):
            reprises.append(legislature)
    return reprises


def ensure_dossiers_zips_downloaded(
    *, force_download: bool = False
) -> list[tuple[int, Path]]:
    """Télécharge toutes les archives connues, retournées par législature
    **croissante** (l'ordre dont dépend l'arbitrage de `iter_dossiers_bruts`).

    Non-fatal par archive : celles qui échouent sont omises, les autres restent
    exploitables. Un échec total donne une liste vide, que les appelants
    traitent comme l'ancien `None`.
    """
    resultats: list[tuple[int, Path]] = []
    for legislature in sorted(AN_DOSSIERS_ARCHIVES):
        chemin = ensure_dossiers_zip_downloaded(
            legislature, force_download=force_download
        )
        if chemin is not None:
            resultats.append((legislature, chemin))
    return resultats


def _uid_depuis_nom(nom: str) -> str:
    """`json/dossierParlementaire/DLR5L17N52956.json` -> `DLR5L17N52956`.

    Le nom de fichier porte l'uid du dossier — vérifié sans exception sur les
    10 967 dossiers des trois archives. C'est ce qui permet d'arbitrer les
    doublons inter-archives à partir des seuls `namelist()`, sans désérialiser
    quoi que ce soit : charger les trois archives en mémoire pour comparer
    coûterait plusieurs centaines de Mo, sur un pipeline qui a déjà connu deux
    OOM (#377, #392).
    """
    return nom.rsplit("/", 1)[-1][: -len(".json")]


# ── La XIV est monolithique, et c'est sa seule différence (#1019) ────────────
#
# Les archives XV et suivantes portent UN FICHIER PAR OBJET
# (`json/dossierParlementaire/DLR5L17N52956.json`). La XIV porte **un seul
# fichier JSON** de 36 Mo décompressés, dans lequel les objets sont deux
# tableaux. Relevé le 18/09/2026 sur `Dossiers_Legislatifs_XIV.json.zip`
# (2,5 Mo) : 3 432 dossiers, 7 120 documents.
#
# `couverture_dossiers.py` disait « aucun `dossierParlementaire` ». C'était
# faux : il y en a 3 432, chacun sous cette clé exactement comme dans le format
# par fichier. Seul l'EMBALLAGE change, pas le contenu — mesuré,
# `parse_dossier_gouvernemental` traite les 3 432 sans une exception, et rend
# 573 dossiers d'origine gouvernementale avec **un seul warning** et aucun
# `fam_code` inconnu.
#
# Les deux collections ne s'emballent pas pareil, et c'est la seule subtilité :
# un dossier est `{"dossierParlementaire": {…}}`, un document est l'objet nu.
_COLLECTIONS_MONOLITHE: dict[str, tuple[tuple[str, str], bool]] = {
    # cle_racine : ((clé de section, clé de tableau), objet enveloppé ?)
    "dossierParlementaire": (("dossiersLegislatifs", "dossier"), True),
    "document": (("textesLegislatifs", "document"), False),
}


def _entrees_monolithiques(chemin: Path, cle_racine: str) -> dict[str, dict[str, Any]]:
    """`{uid: objet}` d'une archive monolithique, ou `{}` si ce n'en est pas une.

    **Cette fonction charge l'archive entière en mémoire**, contrairement au
    format par fichier qui arbitre les doublons sur les seuls `namelist()`. Il
    n'y a pas d'autre choix : sans nom de fichier, l'uid ne se lit que dans
    l'objet, donc il faut désérialiser pour savoir ce que l'archive contient.

    Le coût est mesuré et borné : 36 Mo décompressés pour la XIV, contre les
    « plusieurs centaines de Mo » que `_uid_depuis_nom` évite sur les trois
    archives par fichier. Le pipeline a déjà connu deux OOM (#377, #392), donc
    ce n'est pas une licence générale — c'est une exception pour UNE archive
    dont la structure ne laisse pas le choix, et elle est rendue sous forme de
    dict pour n'être parcourue qu'une fois.
    """
    section = _COLLECTIONS_MONOLITHE.get(cle_racine)
    if section is None:
        return {}
    (cle_section, cle_tableau), enveloppe = section
    try:
        with zipfile.ZipFile(chemin) as zf:
            noms = [n for n in zf.namelist() if n.endswith(".json")]
            if len(noms) != 1:
                return {}
            with zf.open(noms[0]) as flux:
                racine = json.load(flux)
    except (zipfile.BadZipFile, OSError, ValueError):
        return {}

    export = racine.get("export") if isinstance(racine, dict) else None
    entrees = ((export or {}).get(cle_section) or {}).get(cle_tableau)
    if not isinstance(entrees, list):
        return {}

    resultat: dict[str, dict[str, Any]] = {}
    for entree in entrees:
        if not isinstance(entree, dict):
            continue
        objet = entree.get(cle_racine) if enveloppe else entree
        if not isinstance(objet, dict):
            continue
        uid = objet.get("uid")
        if isinstance(uid, str) and uid:
            resultat[uid] = objet
    return resultat


def _iter_entrees_brutes(
    archives: list[tuple[int, Path]], prefixe: str, cle_racine: str
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Itère `(legislature_archive, objet)` sur plusieurs archives,
    **dédupliqué par uid**, pour une famille de fichiers de l'archive.

    Un même objet figure dans plusieurs archives (traîne résiduelle des
    législatures antérieures). L'archive de législature la plus élevée fait
    foi : elle porte l'état le plus à jour. Lire d'abord la plus ancienne
    donnerait un état périmé — un texte « en navette » dans l'archive XVI peut
    être « adopté » dans la XVII.

    Générateur : un seul objet est désérialisé à la fois.
    """
    proprietaire: dict[str, int] = {}
    noms_par_archive: dict[int, list[str]] = {}
    # #1019 — les archives monolithiques, chargées une fois et gardées le temps
    # de l'itération. Il n'y en a qu'une aujourd'hui (la XIV) ; la détection
    # porte sur la FORME de l'archive, jamais sur son numéro de législature,
    # pour qu'une archive future de l'un ou l'autre format soit lue sans qu'on
    # y revienne.
    monolithes: dict[int, dict[str, dict[str, Any]]] = {}
    for legislature, chemin in archives:
        try:
            with zipfile.ZipFile(chemin) as zf:
                noms = [
                    n for n in zf.namelist()
                    if n.startswith(prefixe) and n.endswith(".json")
                ]
        except (zipfile.BadZipFile, OSError):
            continue
        if not noms:
            entrees = _entrees_monolithiques(chemin, cle_racine)
            if entrees:
                monolithes[legislature] = entrees
                for uid in entrees:
                    precedente = proprietaire.get(uid)
                    if precedente is None or legislature > precedente:
                        proprietaire[uid] = legislature
            continue
        noms_par_archive[legislature] = noms
        for nom in noms:
            uid = _uid_depuis_nom(nom)
            # max() explicite plutôt qu'écrasement dans l'ordre de parcours :
            # l'arbitrage ne doit pas dépendre de l'ordre d'appel.
            precedente = proprietaire.get(uid)
            if precedente is None or legislature > precedente:
                proprietaire[uid] = legislature

    for legislature, chemin in archives:
        entrees = monolithes.get(legislature)
        if entrees is not None:
            for uid, objet in entrees.items():
                if proprietaire.get(uid) == legislature:
                    yield legislature, objet
            continue
        noms = noms_par_archive.get(legislature)
        if not noms:
            continue
        try:
            with zipfile.ZipFile(chemin) as zf:
                for nom in noms:
                    if proprietaire.get(_uid_depuis_nom(nom)) != legislature:
                        continue
                    try:
                        with zf.open(nom) as f:
                            data = json.load(f)
                    except (OSError, ValueError):
                        continue
                    objet = data.get(cle_racine) if isinstance(data, dict) else None
                    if isinstance(objet, dict):
                        yield legislature, objet
        except (zipfile.BadZipFile, OSError):
            continue


def iter_dossiers_bruts(
    archives: list[tuple[int, Path]],
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Itère `(legislature_archive, dossierParlementaire)`, dédupliqué par uid.

    L'arbitrage inter-archives est celui de `_iter_entrees_brutes` : la
    législature la plus élevée fait foi, parce qu'elle porte l'état le plus à
    jour des `actesLegislatifs`, donc du statut.
    """
    yield from _iter_entrees_brutes(
        archives, "json/dossierParlementaire/", "dossierParlementaire"
    )


def iter_documents_bruts(
    archives: list[tuple[int, Path]],
) -> Iterator[tuple[int, dict[str, Any]]]:
    """Itère `(legislature_archive, document)`, dédupliqué par uid.

    `json/document/*.json` est la seconde famille de fichiers de ces archives —
    23 709 fichiers pour 21 937 uid distincts sur les trois archives XV/XVI/XVII
    (relevé du 31/08/2026). `docs/sources/an-opendata.md` les a décrits jusqu'à
    #639 comme « sans rapport, à filtrer » : c'est faux. Chaque document porte
    `dossierRef`, la seule clé sourcée qui rattache un texte déposé à son
    dossier législatif — celle dont le `texteLegislatifRef` d'un amendement a
    besoin. Voir `textes_dossiers_an.py`.
    """
    yield from _iter_entrees_brutes(archives, "json/document/", "document")


def _document_depot_initial(actes_legislatifs: Any) -> Optional[str]:
    """uid du document associé à l'acte de dépôt le plus ancien, ou None."""
    depots: list[tuple[str, str]] = []

    def parcours(noeud: Any) -> None:
        if isinstance(noeud, dict):
            code_acte = noeud.get("codeActe")
            texte_associe = noeud.get("texteAssocie")
            if (
                isinstance(code_acte, str)
                and code_acte.endswith("-DEPOT")
                and isinstance(texte_associe, str)
            ):
                depots.append((noeud.get("dateActe") or "", texte_associe))
            for valeur in noeud.values():
                parcours(valeur)
        elif isinstance(noeud, list):
            for valeur in noeud:
                parcours(valeur)

    parcours(actes_legislatifs)
    return min(depots)[1] if depots else None


def _initiateurs_acteur_refs(dossier: dict[str, Any]) -> Optional[list[str]]:
    """`acteurRef` de chaque initiateur déclaré par la source
    (`initiateur.acteurs.acteur[]`), dans l'ordre du dump et dédoublonnés, ou
    `None` si le dossier n'en porte aucun (#435).

    `acteur` est un objet quand le dossier a un seul initiateur et une liste
    quand il en a plusieurs — les deux formes coexistent dans les trois
    archives (2482 dossiers en objet, 293 en liste sur l'archive XVII), les
    deux sont donc acceptées. Sur les 725 textes rattachés à un gouvernement,
    723 portent au moins un `acteurRef` et 365 en portent plusieurs : le
    multi-initiateur est le cas courant, pas une bizarrerie à écarter.

    Retourne `None`, jamais `[]`, quand aucun `acteurRef` n'est lisible — y
    compris pour les dossiers dont `initiateur` ne porte qu'un `organes`
    (initiative d'un organe, sans acteur nommé) : une liste vide se lirait
    comme « aucun ministre n'a porté ce texte », alors que le fait constaté
    est « la source ne le dit pas » (AGENTS.md §2.5). La résolution vers un
    `membre_id` n'est pas faite ici : elle demande la composition du
    gouvernement, donc `gouvernement_profile.py`.
    """
    initiateur = dossier.get("initiateur")
    if not isinstance(initiateur, dict):
        return None
    acteurs = initiateur.get("acteurs")
    if not isinstance(acteurs, dict):
        return None
    acteur = acteurs.get("acteur")
    if isinstance(acteur, dict):
        acteur = [acteur]
    if not isinstance(acteur, list):
        return None

    refs: list[str] = []
    for entree in acteur:
        if not isinstance(entree, dict):
            continue
        ref = entree.get("acteurRef")
        if isinstance(ref, str) and ref and ref not in refs:
            refs.append(ref)
    return refs or None


def nature_texte_depose(dossier: dict[str, Any]) -> Optional[str]:
    """Nature du texte déposé, telle que la source l'encode (#689) :
    `"projet_de_loi"` / `"proposition_de_loi"` / `"proposition_de_resolution"`,
    ou `None` quand la source ne l'établit pas.

    **Un seul signal, celui du dépôt** : le préfixe de l'uid du document associé
    à l'acte `*-DEPOT` le plus ancien (`PRJL`/`PION`/`PNRE`). Jamais le libellé
    du dossier. Une clé tirée d'un libellé rouille et se tait en rouillant
    (#672) : sur la XV, où les intitulés sont descriptifs (« Bioéthique »,
    « CETA », « Coopération avec le Luxembourg »), un discriminant « commence
    par *Projet de loi* » manque **283 des 304** textes portés hors mandat des
    candidats déclarés, dont la totalité de ceux d'`edouard-philippe`.

    Un document présent mais d'un préfixe inconnu rend `None` **sans** repli :
    la source a dit ce qu'elle a déposé, ce n'est simplement pas un texte que
    cette nomenclature nomme. Le repli sur `procedureParlementaire.code` ne
    s'applique donc qu'aux dossiers **sans** document résolvable, et seulement
    pour les codes univoques — les codes 5 et 7 (« Projet **ou** proposition de
    loi organique/constitutionnelle ») en sont exclus, deviner violerait
    AGENTS.md §2.5.

    Fonction publique : c'est elle que lit `candidate_profile.py` pour qualifier
    `textes_portes[]`, sur le patron de #435 (le parseur extrait, l'appelant
    interprète). Les deux étages lisent ainsi le même champ de la même archive.
    """
    document = _document_depot_initial(dossier.get("actesLegislatifs"))
    if document:
        for prefixe, nature in _NATURE_PAR_PREFIXE_DOCUMENT.items():
            if document.startswith(prefixe):
                return nature
        return None

    procedure = dossier.get("procedureParlementaire") or {}
    code = procedure.get("code")
    code = str(code) if code is not None else None
    if code in _PROCEDURE_CODES_GOUVERNEMENTAUX:
        return "projet_de_loi"
    if code in _PROCEDURE_CODES_PARLEMENTAIRES:
        return "proposition_de_loi"
    if code in _PROCEDURE_CODES_RESOLUTION:
        return "proposition_de_resolution"
    return None


def _origine(dossier: dict[str, Any]) -> Optional[str]:
    """Classe un dossier en `"gouvernemental"` / `"parlementaire"` / `None`
    (non déterminable, donc exclu plutôt que deviné — AGENTS.md §2.5).

    **Dérivée de `nature_texte_depose` depuis #689**, et non plus lectrice de
    l'archive elle-même : l'origine d'un texte de loi EST sa nature, lue à
    travers l'article 39 de la Constitution. Deux lectures du même champ
    auraient fini par diverger ; une seule ne le peut pas. Le verdict est
    inchangé sur les trois archives — vérifié dossier à dossier avant/après sur
    les 10 674 dossiers des XV/XVI/XVII (01/09/2026) —, une proposition de
    résolution restant absente d'`_ORIGINE_PAR_NATURE`, donc `None` comme
    avant.

    Le signal primaire reste le **type du document déposé** (`PRJL`/`PION`), pas
    le préfixe du titre. Le titre ne porte l'origine que sur les XVI/XVII : sur
    la XV les titres sont descriptifs (« Taxe sur les services numériques »,
    « Démocratie plus représentative, responsable, efficace »), et le filtre par
    préfixe y retenait **zéro** projet de loi déposé entre 2017 et 2019 alors
    que le corpus en contient plusieurs centaines (#400).

    Le préfixe de document est aussi plus juste que `procedureParlementaire`
    là où les deux divergent : 8 dossiers de règlement du budget sont typés
    « Proposition de loi ordinaire » à la source alors que le document déposé
    est bien un `PRJL`. Le type du document réellement déposé fait donc foi, et
    la procédure ne sert que de repli quand aucun document n'est résolvable.
    """
    return _ORIGINE_PAR_NATURE.get(nature_texte_depose(dossier))


def _iter_actes(node: Any):
    """Parcourt récursivement l'arbre `actesLegislatifs` d'un dossier et
    produit chaque acte (dict) rencontré, à n'importe quelle profondeur."""
    if isinstance(node, dict):
        yield node
        for key, value in node.items():
            if key != "statutConclusion":
                yield from _iter_actes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_actes(item)


def _acte_dates(actes_legislatifs: Any) -> tuple[Optional[str], Optional[str]]:
    """Calcule `(date_depot, date_dernier_evenement)` : `date_depot` est la
    date minimale parmi les actes de premier dépôt (`codeActe` se terminant
    par `-DEPOT`) ; `date_dernier_evenement` est la date maximale parmi tous
    les actes du dossier, quel que soit leur type."""
    toutes_dates: list[str] = []
    dates_depot: list[str] = []
    for acte in _iter_actes(actes_legislatifs):
        date_acte = acte.get("dateActe")
        if not isinstance(date_acte, str) or not date_acte:
            continue
        date_courte = date_acte[:10]
        toutes_dates.append(date_courte)
        code_acte = acte.get("codeActe")
        if isinstance(code_acte, str) and code_acte.endswith("-DEPOT"):
            dates_depot.append(date_courte)
    date_depot = min(dates_depot) if dates_depot else (min(toutes_dates) if toutes_dates else None)
    date_dernier_evenement = max(toutes_dates) if toutes_dates else None
    return date_depot, date_dernier_evenement


def _chambre_depot_initial(actes_legislatifs: Any) -> Optional[str]:
    """Déduit la chambre de dépôt initial du dossier à partir du préfixe du
    `codeActe` du premier acte de dépôt chronologique (`AN...` -> `"AN"`,
    `SN...` -> `"Senat"`)."""
    meilleur: Optional[tuple[str, str]] = None  # (date, chambre)
    for acte in _iter_actes(actes_legislatifs):
        code_acte = acte.get("codeActe")
        date_acte = acte.get("dateActe")
        if not isinstance(code_acte, str) or not code_acte.endswith("-DEPOT"):
            continue
        if not isinstance(date_acte, str) or not date_acte:
            continue
        if code_acte.startswith("AN"):
            chambre = "AN"
        elif code_acte.startswith("SN"):
            chambre = "Senat"
        else:
            continue
        if meilleur is None or date_acte < meilleur[0]:
            meilleur = (date_acte, chambre)
    return meilleur[1] if meilleur else None


def _determine_statut(
    dossier_id: str, actes_legislatifs: Any
) -> tuple[Optional[str], Optional[bool], Optional[str]]:
    """Détermine `(statut, sort_49_3, warning)` du dossier à partir de la
    décision de séance (`_est_decision_de_seance`) ou de l'acte de retrait
    le plus récent. Voir docstring du module pour la justification du
    filtre et le traitement de la sentinelle `TSORTFnull`.

    Si aucun acte décisif n'est trouvé, le dossier est considéré `"depose"`
    (seul un dépôt existe) ou `"navette_en_cours"` (des actes existent
    au-delà du dépôt, sans décision de séance encore atteinte) — ce n'est
    pas un cas de warning : l'absence de conclusion est un état légitime,
    pas une donnée inconnue.
    """
    candidats: list[tuple[str, str, Optional[str]]] = []  # (date, kind, fam_code)
    a_acte_hors_depot = False
    a_promulgation = False
    for acte in _iter_actes(actes_legislatifs):
        code_acte = acte.get("codeActe")
        date_acte = acte.get("dateActe")
        if not isinstance(code_acte, str):
            continue
        # #997 — `not endswith("-DEPOT")` passait à True sur la saisine de
        # commission, automatique au dépôt, et sur les conteneurs d'étape :
        # `"depose"` était donc inatteignable.
        if est_acte_au_dela_du_depot(code_acte):
            a_acte_hors_depot = True
        if code_acte.startswith(_CODE_ACTE_PROMULGATION_PREFIXE):
            a_promulgation = True

        if code_acte in _CODE_ACTE_RETRAIT and isinstance(date_acte, str) and date_acte:
            candidats.append((date_acte, "retrait", None))
            continue

        if not _est_decision_de_seance(code_acte):
            continue
        statut_conclusion = acte.get("statutConclusion")
        if not isinstance(statut_conclusion, dict):
            continue
        fam_code = statut_conclusion.get("fam_code")
        if not fam_code or fam_code == _FAM_CODE_SENTINEL_VIDE:
            continue
        if not isinstance(date_acte, str) or not date_acte:
            continue
        candidats.append((date_acte, "statut", fam_code))

    statut, sort_49_3, warning = _statut_depuis_candidats(
        dossier_id, candidats, a_acte_hors_depot
    )

    # La promulgation prime sur une décision de séance non finale ou infirmée
    # par la suite : elle est postérieure et définitive. Le warning éventuel
    # (fam_code non mappé) est conservé — le code reste inconnu et mérite
    # toujours d'être signalé pour un mapping futur.
    if a_promulgation and statut in _STATUTS_CORRIGES_PAR_PROMULGATION:
        return "promulgue", False, warning

    return statut, sort_49_3, warning


def _statut_depuis_candidats(
    dossier_id: str,
    candidats: list[tuple[str, str, Optional[str]]],
    a_acte_hors_depot: bool,
) -> tuple[Optional[str], Optional[bool], Optional[str]]:
    if not candidats:
        return ("navette_en_cours" if a_acte_hors_depot else "depose"), None, None

    _date, kind, fam_code = max(candidats, key=lambda c: c[0])
    if kind == "retrait":
        return "retire", None, None

    mapping = _FAM_CODE_STATUT_MAP.get(fam_code)
    if mapping is None:
        warning = (
            f"gouvernement_textes: dossier {dossier_id} : fam_code inconnu "
            f"{fam_code!r} — statut non déterminé."
        )
        return None, None, warning

    statut, sort_49_3 = mapping
    return statut, sort_49_3, None


def _source_url(legislature: Optional[str], titre_chemin: Optional[str]) -> Optional[str]:
    if legislature and titre_chemin:
        return f"https://www.assemblee-nationale.fr/dyn/{legislature}/dossiers/{titre_chemin}"
    return None


def parse_dossier_gouvernemental(dossier: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Extrait un enregistrement de dossier gouvernemental à partir d'un
    `dossierParlementaire` brut (déjà désérialisé), ou `None` si son origine
    n'est pas gouvernementale (signal de préfixe de titre, voir docstring).

    Pure : aucun effet de bord, aucun accès réseau. `warnings` (liste, jamais
    absente) accompagne l'enregistrement pour tout `fam_code` non mappé ou
    toute combinaison non représentable en l'état par le schéma cible.
    """
    titre_dossier = dossier.get("titreDossier") or {}
    titre = titre_dossier.get("titre")
    if not titre or _origine(dossier) != "gouvernemental":
        return None

    dossier_id = dossier.get("uid")
    actes_legislatifs = dossier.get("actesLegislatifs")
    date_depot, date_dernier_evenement = _acte_dates(actes_legislatifs)
    chambre_depot_initial = _chambre_depot_initial(actes_legislatifs)
    statut, sort_49_3, warning = _determine_statut(dossier_id, actes_legislatifs)
    initiateurs_acteur_refs = _initiateurs_acteur_refs(dossier)
    legislature = dossier.get("legislature")

    return {
        "dossier_id": dossier_id,
        "titre": titre,
        "statut": statut,
        "sort_49_3": sort_49_3,
        "chambre_depot_initial": chambre_depot_initial,
        "date_depot": date_depot,
        "date_dernier_evenement": date_dernier_evenement,
        "initiateurs_acteur_refs": initiateurs_acteur_refs,
        "legislature": legislature,
        "source_url": _source_url(legislature, titre_dossier.get("titreChemin")),
        "warnings": [warning] if warning else [],
    }


def collect_dossiers_gouvernementaux(zf: zipfile.ZipFile) -> dict[str, Any]:
    """Parcourt un `Dossiers_Legislatifs.json.zip` déjà ouvert et retourne
    `{"dossiers": [...], "warnings": [...]}` : un enregistrement par dossier
    d'origine gouvernementale identifiable, plus la liste consolidée des
    warnings (fam_code non mappés, combinaisons non représentables). Pure
    (aucun accès réseau) : c'est la fonction testée par une fixture ZIP
    locale.
    """
    dossiers: list[dict[str, Any]] = []
    warnings: list[str] = []
    noms = [
        n for n in zf.namelist()
        if n.startswith("json/dossierParlementaire/") and n.endswith(".json")
    ]
    for nom in noms:
        try:
            with zf.open(nom) as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        dossier = data.get("dossierParlementaire") if isinstance(data, dict) else None
        if not isinstance(dossier, dict):
            continue
        record = parse_dossier_gouvernemental(dossier)
        if record is None:
            continue
        warnings.extend(record["warnings"])
        dossiers.append(record)

    dossiers.sort(key=lambda d: (d.get("date_depot") or "", d.get("titre") or ""), reverse=True)
    return {"dossiers": dossiers, "warnings": warnings}


def collect_dossiers_gouvernementaux_multi(
    archives: list[tuple[int, Path]],
) -> dict[str, Any]:
    """Équivalent de `collect_dossiers_gouvernementaux` sur plusieurs archives,
    dédupliquées par uid (voir `iter_dossiers_bruts`). Pure hors lecture
    disque : c'est la fonction testée par des fixtures ZIP locales."""
    dossiers: list[dict[str, Any]] = []
    warnings: list[str] = []
    for _legislature, dossier in iter_dossiers_bruts(archives):
        record = parse_dossier_gouvernemental(dossier)
        if record is None:
            continue
        warnings.extend(record["warnings"])
        dossiers.append(record)

    dossiers.sort(key=lambda d: (d.get("date_depot") or "", d.get("titre") or ""), reverse=True)
    return {"dossiers": dossiers, "warnings": warnings}


def fetch_dossiers_gouvernementaux() -> dict[str, Any]:
    """Point d'entrée réseau : télécharge (si nécessaire) les archives connues,
    puis collecte les dossiers d'origine gouvernementale.

    Retourne `{"dossiers": [...], "warnings": [...], "legislatures_ingerees": [...]}`.

    `legislatures_ingerees` est la liste des législatures dont l'archive a
    réellement pu être lue. **Elle n'est pas informative : elle sert à
    distinguer « zéro dossier constaté » de « collecte incomplète »** (#427).
    Sans elle, l'appelant ne peut pas faire la différence entre les deux, et
    `generate_gouvernement_profiles.py` écraserait des profils avec un
    `textes: []` qui n'a jamais été mesuré — AGENTS.md §2.5.
    """
    archives = ensure_dossiers_zips_downloaded()
    if not archives:
        return {
            "dossiers": [],
            "warnings": ["gouvernement_textes: téléchargement des dossiers législatifs impossible."],
            "legislatures_ingerees": [],
        }

    resultat = collect_dossiers_gouvernementaux_multi(archives)
    resultat["legislatures_ingerees"] = sorted(leg for leg, _ in archives)
    manquantes = sorted(set(AN_DOSSIERS_ARCHIVES) - {leg for leg, _ in archives})
    if manquantes:
        # Signalé explicitement : une archive absente réduit silencieusement la
        # couverture, ce qui se lirait comme « ce gouvernement n'a porté aucun
        # texte » (AGENTS.md §2.8).
        resultat["warnings"].append(
            "gouvernement_textes: archive(s) indisponible(s) pour la ou les "
            f"législature(s) {manquantes} — couverture réduite."
        )
    return resultat
