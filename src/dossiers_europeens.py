#!/usr/bin/env python3
"""
dossiers_europeens.py — L'index des dossiers du Parlement européen (#901).

Ce que cet index résout
------------------------
Un amendement européen publie son `texte_vise` — `"2021/0136(COD)"` — sur
**100 %** des 7 303 entrées, et l'interface le lit déjà. Mais une référence de
procédure n'est pas un titre : `resolveDossier` la cherche dans l'index
français, ne l'y trouve pas, et la fiche affiche « 590 amendements · **0
dossiers** ». Au mieux, l'écran pourrait rendre le code brut, qui ne dit rien à
un lecteur.

Ce qui manquait n'était donc ni une collecte ni une lecture, mais un
**référentiel** : code de procédure → intitulé. Le dump `ep_dossiers` le porte.

Mesuré le 14/09/2026, contre les références réellement visées par les
amendements des 7 candidats déclarés à mandat européen :

  · 367 références distinctes ;
  · **355 résolues** (96,7 %), avec titre, stade et type de procédure ;
  · couvrant **6 925 amendements sur 7 303** (94,8 %).

Les 12 non résolues sont toutes de 2024-2025 : le dump des dossiers est plus
ancien que celui des amendements. C'est une absence **datée**, pas un trou — et
elle se déclare plutôt que de se combler (§2 règle 5).

Les titres sont en anglais
---------------------------
C'est ce que la source publie, et rien ici ne les traduit : une traduction
automatique d'un intitulé législatif produirait un titre que personne n'a écrit
et qu'aucune source ne confirme (§2 règle 2). L'interface affiche ce que le
Parlement européen a publié.

Chaque dossier dit ses familles OEIL (17/09/2026)
-------------------------------------------------
La famille est le premier niveau du code de matière (`6.40.10` → `6`). Son
libellé est **lu dans le dump**, là où la source publie le premier niveau, sur
tout le dump et pas sur les seuls dossiers visés : `familles = [{"code": "6",
"libelle": "External relations of the Union"}]`. En anglais, comme les
matières : le site OEIL en français ne répond pas à une requête simple, et le
libellé anglais a été arbitré le 17/09/2026. Une famille sans libellé est
déclarée dans `familles_non_resolu`.

Le stade est repris de la même table que `textes_portes[]`
-----------------------------------------------------------
`normalize_parltrack_dumps.STADE_UE_PAR_LIBELLE_SOURCE` est la seule fabrique de
cette correspondance (#901, lot du stade). La recopier ici ferait diverger deux
tables le jour où la source ajoute une valeur.

Usage :
    python3 src/dossiers_europeens.py \\
        --profils-dir pivot_data/profiles \\
        --out pivot_data/dossiers_europeens.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

from documents_europeens import (  # noqa: E402
    LICENCE as LICENCE_PORTAIL_ET_EUROVOC,
    LibellesEurovocIndisponibles,
    resoudre_domaines,
)
from licences import LICENCE_PARLTRACK  # noqa: E402
from normalize_parltrack_dumps import _stade_procedural_ue  # noqa: E402
from parltrack_dumps import ensure_dump, iter_dump_zst  # noqa: E402

#: Le dump que ce module lit. Déjà téléchargé par `extract-parltrack`.
DUMP_DOSSIERS = "ep_dossiers.json.zst"

#: v2 depuis le 16/09/2026 : chaque entrée publie ses `matieres` (#901). Un
#: champ ajouté change ce qu'un lecteur peut attendre du fichier, et la version
#: est le seul endroit où il peut le constater sans relire le code.
#: v3 depuis le 17/09/2026 : chaque entrée publie ses `familles` OEIL (#901).
#: v4 depuis le 17/09/2026 : chaque entrée publie ses `domaines` EuroVoc (#901).
SCHEMA_VERSION = "dossiers-europeens-v4"
DEFAULT_PROFILS_DIR = Path("pivot_data/profiles")
DEFAULT_SORTIE = Path("pivot_data/dossiers_europeens.json")

#: Préfixe de l'identifiant, pendant de `an:` et de `pe:` pour les scrutins.
PREFIXE_ID = "pe-dossier"


class DumpDossiersIndisponible(RuntimeError):
    """Le dump n'a pas pu être obtenu. Levée, jamais avalée : un index vide se
    lirait comme « aucun dossier européen » (#510)."""


def identifiant(reference: str) -> str:
    """`pe-dossier:2021/0136(COD)` — l'identifiant publié d'un dossier."""
    return f"{PREFIXE_ID}:{reference}"


#: Ce qui, dans `committees[].type`, désigne une commission saisie **au fond**.
#: La source emploie quatre libellés qui le contiennent — « Responsible
#: Committee », « Former Responsible Committee », « Joint Responsible
#: Committee », « Former Joint Committee Responsible » — contre « Committee
#: Opinion » et ses variantes pour une saisine pour avis.
MARQUEUR_AU_FOND = "responsible"

#: Le champ que la source renseigne vraiment. `responsible: true` existe aussi,
#: et c'est un piège : il n'est renseigné que sur **521 des 18 242** entrées
#: (2,9 %), là où `type` l'est sur 97 %. S'y fier aurait rendu une commission
#: au fond pour 1,2 % des dossiers au lieu de 97,7 %.
CHAMP_TYPE = "type"

#: Le libellé de la source → ce qu'il affirme, en vocabulaire fermé.
#:
#: Les quatre libellés sont **conservés verbatim** dans `type_source` ; ce statut
#: est ce qui permet de les lire sans refaire, chez chaque consommateur, une
#: reconnaissance de chaîne sur de l'anglais. Deux axes s'y croisent : la saisine
#: est-elle **en vigueur** (« Former … » ne l'est plus), est-elle **partagée**
#: (« Joint … »).
#:
#: Les fondre publierait comme compétente une commission dessaisie, et effacerait
#: qu'une saisine est partagée — une compétence que la source n'établit pas
#: (§2 règle 2). L'arbitrage du 14/09/2026 tient à sa réversibilité : fondre plus
#: tard à l'affichage reste possible, re-séparer ce qu'on a écrasé à la collecte
#: ne l'est pas.
#:
#: Relevé le 14/09/2026 sur les 355 dossiers de cet index. Deux populations, à
#: ne pas confondre — les entrées `committees[]` **de la source** : 326
#: « Responsible Committee », 40 « Former Responsible Committee », 34 « Joint
#: Responsible Committee », 2 « Former Joint Committee Responsible » ; et les
#: entrées **publiées**, après aplatissement des sigles, une entrée pouvant en
#: porter zéro ou plusieurs : 326 `au_fond`, 40 `ancienne_au_fond`, 31
#: `au_fond_conjointe`, 4 `ancienne_au_fond_conjointe`.
STATUT_PAR_LIBELLE: dict[str, str] = {
    "responsible committee": "au_fond",
    "joint responsible committee": "au_fond_conjointe",
    "former responsible committee": "ancienne_au_fond",
    "former joint committee responsible": "ancienne_au_fond_conjointe",
}

#: Vocabulaire fermé, comme les `KNOWN_*` du schéma pivot (`AGENTS.md` §4) :
#: l'étendre est un geste délibéré, jamais un effet de bord d'une valeur reçue.
KNOWN_STATUTS_COMMISSION_AU_FOND = frozenset(STATUT_PAR_LIBELLE.values())

#: Pourquoi un dossier ne publie AUCUNE commission au fond. Non nul si et
#: seulement si `commissions_au_fond` est vide — même contrat que
#: `sort_non_resolu` (#747) : ni les deux, ni aucun des deux.
#:
#: Un dossier **absent de l'index** est un troisième cas, et il se lit à son
#: absence : la référence était citée mais introuvable dans le dump. Rien n'est
#: fabriqué pour lui (§2 règle 5).
MOTIF_SANS_COMMISSION = "source_sans_commission_au_fond"
MOTIF_CONJOINTE_SANS_NOM = "saisine_conjointe_sans_commission_nommee"


def _sigles_et_noms(commission: dict[str, Any]) -> list[tuple[str, Optional[str]]]:
    """Les couples `(sigle, nom)` d'une entrée `committees[]`.

    Une saisine **conjointe** porte plusieurs commissions, et la source le dit
    en mettant des **listes** dans `committee` et `committee_full` : 36 des 402
    entrées au fond de notre population. Les aplatir ici plutôt que de publier
    une liste dans un champ scalaire évite à chaque consommateur de gérer les
    deux formes.
    """
    sigles = commission.get("committee")
    noms = commission.get("committee_full")
    if isinstance(sigles, str):
        sigles, noms = [sigles], [noms if isinstance(noms, str) else None]
    if not isinstance(sigles, list):
        return []
    if not isinstance(noms, list):
        noms = [None] * len(sigles)
    couples = []
    for rang, sigle in enumerate(sigles):
        if isinstance(sigle, str) and sigle:
            nom = noms[rang] if rang < len(noms) else None
            couples.append((sigle, nom if isinstance(nom, str) and nom else None))
    return couples


#: Séparateur entre le code OEIL et son libellé, quand la source les colle dans
#: une chaîne unique : `"6.20.03 Bilateral economic and trade agreements"`.
_CODE_MATIERE = re.compile(r"^\s*(?P<code>\d+(?:\.\d+)*)\s+(?P<libelle>.+?)\s*$")


def matieres(dossier: dict[str, Any]) -> list[dict[str, Any]]:
    """Les matières OEIL d'un dossier — `procedure.subject`, normalisé.

    POURQUOI CE CHAMP, ALORS QUE LA COMMISSION AU FOND EXISTE DÉJÀ. Parce
    qu'elle ne couvre pas ce corpus. Mesuré le 16/09/2026 sur les 389 dossiers
    que les profils citent : la commission au fond en nomme 345, mais **aucune**
    des 40 résolutions d'actualité (`RSP`) — une résolution d'actualité n'est
    pas renvoyée en commission, donc la source n'a rien à publier. `subject`,
    lui, est rempli sur les **389**, RSP comprises.

    DEUX FORMES DANS LA SOURCE, et la seconde surprend. Un dict
    `{"6.20.03": "Bilateral economic…"}` sur 387 dossiers ; une **liste de
    chaînes** où le code et le libellé sont collés — `"6.20.03 Bilateral
    economic…"` — sur 2. Les deux disent la même chose, et un lecteur qui n'en
    connaîtrait qu'une perdrait deux dossiers sans erreur visible.

    CE N'EST PAS UN VOCABULAIRE FERMÉ, et c'est délibéré : 244 valeurs
    distinctes sur ce seul corpus, une nomenclature hiérarchique que le
    Parlement fait vivre. Un `frozenset KNOWN_*` la fossiliserait et refuserait
    la première matière ajoutée en amont. Le code est publié tel quel, avec son
    libellé, et l'interface le replie si elle veut (`6.20.03` → `6.20` → `6`).

    Les libellés sont en anglais : c'est ce que la source publie, comme les
    titres, et rien ici ne les traduit.
    """
    brut = (dossier.get("procedure") or {}).get("subject")
    trouvees: dict[str, Optional[str]] = {}
    if isinstance(brut, dict):
        for code, libelle in brut.items():
            code = str(code).strip()
            if code:
                trouvees[code] = str(libelle).strip() or None
    elif isinstance(brut, list):
        for entree in brut:
            m = _CODE_MATIERE.match(str(entree))
            if m:
                trouvees[m.group("code")] = m.group("libelle")
            elif str(entree).strip():
                # Une entrée sans code lisible n'est pas jetée : elle est
                # publiée sans code plutôt que perdue en silence (§2 règle 5).
                trouvees[str(entree).strip()] = None
    return [{"code": c, "libelle": trouvees[c]} for c in sorted(trouvees)]


def libelles_de_famille(dossier: dict[str, Any]) -> dict[str, str]:
    """Les libellés de PREMIER niveau que ce dossier publie : `{"6": "External
    relations of the Union"}`.

    Un dossier ne porte d'ordinaire que des codes profonds (`6.40.10`) ; le
    premier niveau n'apparaît que sur une minorité — mesuré le 17/09/2026 sur
    le dump du 17/08 : 437 occurrences sur 23 885 dossiers, qui nomment les huit
    familles. On les lit donc sur **tout** le dump, pas sur les seuls dossiers
    visés. Trois formes : la clé d'un dict (`"6"`), une clé qui colle code et
    libellé (`"3 Community policies"`), une chaîne de liste.
    """
    brut = (dossier.get("procedure") or {}).get("subject")
    paires: list[tuple[str, Optional[str]]] = []
    if isinstance(brut, dict):
        paires = [(str(k).strip(), str(v).strip() if v else None) for k, v in brut.items()]
    elif isinstance(brut, list):
        paires = [(str(e).strip(), None) for e in brut]
    familles: dict[str, str] = {}
    for cle, libelle in paires:
        if cle.isdigit() and libelle:
            familles[cle] = libelle
            continue
        m = _CODE_MATIERE.match(cle)
        if m and "." not in m.group("code"):
            familles[m.group("code")] = m.group("libelle")
    return familles


def choisir_libelles_de_famille(
    vus: dict[str, dict[str, str]]
) -> dict[str, str]:
    """`famille → libellé` : le libellé du dossier mis à jour le plus récemment.

    La nomenclature a changé de mots avec le temps — « Internal market, SLIM »
    en 2013, « Internal market, single market » depuis. Le plus récent est celui
    que le Parlement emploie aujourd'hui. `vus` : `famille → {libellé → date
    la plus récente}` ; à date égale ou absente, l'ordre alphabétique départage,
    pour que l'index ne change pas d'un run à l'autre.
    """
    return {
        code: max(libelles.items(), key=lambda kv: (kv[1], kv[0]))[0]
        for code, libelles in vus.items() if libelles
    }


def familles(
    sujets: list[dict[str, Any]], libelles: dict[str, str]
) -> tuple[list[dict[str, Any]], Optional[dict[str, Any]]]:
    """Les familles OEIL d'un dossier — le premier segment du code de chaque
    matière —, et la déclaration de celles dont le libellé manque."""
    codes = sorted({
        str(s["code"]).split(".", 1)[0] for s in sujets
        if isinstance(s.get("code"), str) and str(s["code"]).split(".", 1)[0].isdigit()
    }, key=int)
    publiees = [{"code": c, "libelle": libelles[c]} for c in codes if c in libelles]
    manquantes = [c for c in codes if c not in libelles]
    non_resolu = ({"motif": "libelle_famille_oeil_introuvable", "codes": manquantes}
                  if manquantes else None)
    return publiees, non_resolu


def matieres_non_resolu(
    dossier: dict[str, Any], trouvees: list[dict[str, Any]]
) -> Optional[dict[str, str]]:
    """Pourquoi un dossier ne publie aucune matière — jamais une liste vide nue."""
    if trouvees:
        return None
    return {"motif": "source_sans_matiere"}


def commissions_au_fond(dossier: dict[str, Any]) -> list[dict[str, Any]]:
    """Les commissions saisies au fond d'un dossier, une entrée par sigle.

    C'est le fait équivalent, côté européen, à la commission saisie au fond d'un
    dossier de l'Assemblée — ce que l'interface appelle la « matière » d'un vote
    (`commissions_dossiers.json`, #328). Besoin remonté le 14/09/2026 : aucun
    objet européen n'en portait, et c'est ce qui bloquait deux figures.

    Mesuré sur les 355 dossiers de cet index : **347 en portent au moins une**
    (97,7 %) — 299 une seule, 41 deux, 7 trois.

    **Le libellé de type est conservé tel quel**, dans `type_source`. La source
    distingue quatre états — saisine au fond, ancienne saisine, saisine
    conjointe, ancienne saisine conjointe — et les fondre publierait une
    compétence qu'elle sépare. Traduire le sigle ou le nom ne serait pas mieux :
    « JURI » et « Legal Affairs » sont ce que le Parlement publie.

    **`statut` est ce verbatim lu**, en vocabulaire fermé
    (`STATUT_PAR_LIBELLE`) : sans lui, chaque consommateur referait une
    reconnaissance de chaîne sur de l'anglais pour savoir si la commission est
    compétente aujourd'hui. Un libellé que la table ne connaît pas sort
    `statut: None` **avec** `statut_non_resolu`, portant la valeur reçue : ni
    deviné, ni jeté (§2 règle 5).
    """
    entrees: list[dict[str, Any]] = []
    for commission in dossier.get("committees") or []:
        if not isinstance(commission, dict):
            continue
        type_source = commission.get(CHAMP_TYPE)
        if not isinstance(type_source, str) or MARQUEUR_AU_FOND not in type_source.lower():
            continue
        statut = STATUT_PAR_LIBELLE.get(type_source.strip().lower())
        for sigle, nom in _sigles_et_noms(commission):
            entree = {
                "sigle": sigle,
                "nom": nom,
                "type_source": type_source,
                "statut": statut,
            }
            if statut is None:
                entree["statut_non_resolu"] = {
                    "motif": "libelle_inconnu",
                    "valeur": type_source,
                }
            entrees.append(entree)
    return entrees


def commissions_au_fond_non_resolu(
    dossier: dict[str, Any], publiees: list[dict[str, Any]]
) -> Optional[dict[str, str]]:
    """Pourquoi ce dossier ne publie aucune commission au fond, ou `None`.

    Deux causes, qui ne se réparent pas au même endroit et qu'une liste vide
    confondrait — mesurées le 14/09/2026 sur les 355 dossiers de l'index :

    - `source_sans_commission_au_fond` — **8 dossiers** : le dump ne porte
      aucune entrée `committees[]` au fond. C'est un fait de la source ;
    - `saisine_conjointe_sans_commission_nommee` — **6 dossiers** : la source
      *affirme* une saisine conjointe (« Joint Responsible Committee ») et laisse
      `committee` et `committee_full` à la **liste vide**. L'affirmation existe,
      son contenu manque — publier `[]` sans le dire ferait lire ces 6 comme les
      8 précédents.

    341 + 6 + 8 = 355. Le chiffre de 347 qui circule est celui des dossiers dont
    le **dump** porte une entrée au fond ; 341 est celui des dossiers dont
    l'**index publié** nomme au moins une commission. Deux populations, deux
    chiffres, tous deux justes.
    """
    if publiees:
        return None
    for commission in dossier.get("committees") or []:
        if not isinstance(commission, dict):
            continue
        type_source = commission.get(CHAMP_TYPE)
        if isinstance(type_source, str) and MARQUEUR_AU_FOND in type_source.lower():
            return {"motif": MOTIF_CONJOINTE_SANS_NOM}
    return {"motif": MOTIF_SANS_COMMISSION}


def references_visees(profils_dir: Path, *, amendees: Optional[set[str]] = None) -> set[str]:
    """Les références de dossier européen que les profils publiés citent.

    DEUX sources, et la seconde manquait (#901, 16/09/2026).

    Les **amendements** publient leur `texte_vise` dans `amendement_non_resolu`,
    où il vit : `amendement_id` reste `null` pour un amendement européen, et
    c'est voulu (#431).

    Les **textes portés** publient `reference_dossier`, et l'index les ignorait.
    Conséquence mesurée sur `origin/main` `80a24ecf6` : 34 références citées par
    un `textes_portes[]` européen n'étaient dans aucun index, soit **54
    occurrences** sur les fiches — un identifiant publié qui ne résout nulle
    part. Les 10 dossiers `RSP` déjà présents y étaient entrés par la bande,
    parce qu'un amendement les visait.

    Ce n'était donc pas un filtre par type de procédure — il n'y en a aucun —
    mais un périmètre de lecture trop étroit.

    TROISIÈME source depuis le 17/09/2026 : les **votes**. Un vote européen
    publie `reference_dossier` dans `scrutin_non_resolu`. Mesuré sur `origin/main`
    `789537af5` : les 11 013 positions de vote des 6 candidats déclarés concernés
    citent **4 630** références distinctes, dont **296** seulement étaient dans
    l'index — les 4 334 autres n'avaient ni titre, ni type, ni famille, et
    l'interface n'avait que l'intitulé du scrutin. Le dump déjà téléchargé en
    porte 4 253 : l'extension ne coûte aucune requête.

    Comme pour les scrutins, l'index suit le corpus : les références servies,
    pas les 23 885 dossiers du dump.
    """
    refs: set[str] = set()
    for chemin in sorted(profils_dir.glob("*.pivot.json")):
        try:
            profil = json.loads(chemin.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for amendement in profil.get("amendements") or []:
            if not isinstance(amendement, dict):
                continue
            non_resolu = amendement.get("amendement_non_resolu")
            if not isinstance(non_resolu, dict):
                continue
            if non_resolu.get("institution") != "parlement_europeen":
                continue
            vise = non_resolu.get("texte_vise")
            if isinstance(vise, str) and vise:
                refs.add(vise)
                if amendees is not None:
                    amendees.add(vise)
        for texte in profil.get("textes_portes") or []:
            if not isinstance(texte, dict):
                continue
            if texte.get("institution") != "parlement_europeen":
                continue
            reference = texte.get("reference_dossier")
            if isinstance(reference, str) and reference:
                refs.add(reference)
        for vote in profil.get("votes") or []:
            if not isinstance(vote, dict):
                continue
            non_resolu = vote.get("scrutin_non_resolu")
            if not isinstance(non_resolu, dict):
                continue
            if non_resolu.get("institution") != "parlement_europeen":
                continue
            reference = non_resolu.get("reference_dossier")
            if isinstance(reference, str) and reference:
                refs.add(reference)
    return refs


#: Plafond de requêtes NOUVELLES au portail du Parlement, par run, pour les
#: domaines des dossiers (#901, arbitré le 17/09/2026). Les réponses déjà en
#: cache ne comptent pas : le cache `.cache/europarl` se cumule d'un run à
#: l'autre, et la couverture complète s'atteint en quelques runs sans jamais
#: presser le portail.
#:
#: **C'est le budget en TEMPS qui borne la passe, pas ce plafond.** Le run
#: `35231390627` (17/09/2026) a consommé ses 1 500 requêtes en **88 minutes**,
#: soit 3,5 s par requête en CI (0,9 s mesurée depuis un poste) : le job
#: `merge-and-pivot` a dépassé ses 120 minutes, a été annulé, et n'a rien
#: commité — ni le corpus, ni le cache, qui ne s'enregistre qu'en cas de succès.
#: Un débit ne se prévoit pas ; une durée, si.
PLAFOND_REQUETES_PAR_RUN = 1500

#: Durée maximale de la passe des domaines, en secondes. Au débit mesuré en CI,
#: ~340 requêtes : de quoi couvrir les dossiers amendés au premier run, puis
#: avancer sur les votés run après run.
BUDGET_SECONDES_PAR_RUN = 1200

_REFERENCE_SEANCE = re.compile(r"^(?:(?P<rc>RC-B)|(?P<type>[ABT]))(?P<terme>\d+)-(?P<num>\d{4})/(?P<annee>\d{4})")


def documents_de_seance(dossier: dict[str, Any]) -> list[str]:
    """Les documents de séance d'un dossier, en identifiants `doceo`, dans
    l'ordre où les interroger.

    EuroVoc est attaché à un DOCUMENT, jamais à une procédure : ni le dump
    ParlTrack (0 dossier sur 23 885), ni la fiche « procédure » du portail ne le
    publient. Le dossier le reçoit donc de ses documents de séance, lus dans
    `docs[]` et `events[]` du dump.

    L'ordre vient de l'essai du 17/09/2026 sur les 367 dossiers amendés par les
    candidats déclarés : le portail classe le **texte adopté** (`T8-0286/2018` →
    `TA-8-2018-0286`, 281 dossiers), presque jamais le rapport de commission
    (`A8-…`, 11). Texte adopté d'abord, puis proposition de résolution, puis
    rapport.
    """
    titres: list[str] = []
    for bloc in list(dossier.get("docs") or []) + list(dossier.get("events") or []):
        if isinstance(bloc, dict):
            titres += [str(d.get("title")) for d in bloc.get("docs") or [] if isinstance(d, dict)]
    identifiants: list[str] = []
    for titre in titres:
        m = _REFERENCE_SEANCE.match(titre.strip())
        if not m:
            continue
        prefixe = "RC" if m.group("rc") else {"A": "A", "B": "B", "T": "TA"}[m.group("type")]
        doceo = f"{prefixe}-{m.group('terme')}-{m.group('annee')}-{m.group('num')}"
        if doceo not in identifiants:
            identifiants.append(doceo)
    rang = {"TA": 0, "B": 1, "RC": 1, "A": 2}
    return sorted(identifiants, key=lambda d: rang[d.split("-", 1)[0]])


#: Documents essayés par dossier. Au-delà, la mesure n'a rien trouvé de plus.
ESSAIS_PAR_DOSSIER = 2


def domaines_des_dossiers(
    entrees: list[dict[str, Any]],
    documents: dict[str, list[str]],
    resolveur: Any,
    session: Any,
    *,
    prioritaires: Iterable[str] = (),
    plafond: int = PLAFOND_REQUETES_PAR_RUN,
    budget_secondes: float = BUDGET_SECONDES_PAR_RUN,
    horloge: Callable[[], float] = time.monotonic,
) -> dict[str, int]:
    """Pose `domaines` sur chaque entrée, en place, et rend les compteurs.

    `domaines = [{code, libelle, concepts}]`, triés par nombre de concepts puis
    par code, et `domaines_document` nomme le document qui les porte. Le poids
    est un fait de la source : combien de concepts du document tombent dans le
    domaine. Aucun domaine n'est « le » domaine du dossier : le choisir est une
    lecture, qui appartient à l'interface.

    Les dossiers `prioritaires` (ceux que les amendements visent) passent
    d'abord : quand le plafond coupe la passe, ce sont les votes qui attendent
    le run suivant.

    Motifs d'absence, qui ne se confondent pas (§2 règle 5) :
      aucun_document_de_seance    : le dump ne cite aucun document de séance
      documents_non_classes       : le portail a répondu, sans concept EuroVoc
      question_non_posee          : budget ou plafond atteint, portail muet, hors ligne
      eurovoc_injoignable         : les concepts sont là, EuroVoc n'a pas répondu
      domaine_eurovoc_introuvable : les concepts sont là, sans domaine
    """
    prioritaires = set(prioritaires)
    ordre = sorted(entrees, key=lambda e: (e["reference"] not in prioritaires, e["reference"]))
    depart = resolveur.statistiques.get("requetes", 0)
    debut = horloge()
    hors_ligne_initial = getattr(resolveur, "hors_ligne", False)
    concepts_par_doc: dict[str, list[str]] = {}
    etat: dict[str, Any] = {}
    for entree in ordre:
        candidats = documents.get(entree["reference"]) or []
        if not candidats:
            etat[entree["reference"]] = "aucun_document_de_seance"
            continue
        if (resolveur.statistiques.get("requetes", 0) - depart >= plafond
                or horloge() - debut >= budget_secondes):
            # Au-delà du budget, le cache répond encore ; rien d'autre.
            resolveur.hors_ligne = True
        trouve, non_pose = None, False
        for doceo in candidats[:ESSAIS_PAR_DOSSIER]:
            concepts = resolveur.concepts_eurovoc(doceo)
            if concepts is None:
                non_pose = True
                continue
            if concepts:
                trouve = doceo
                concepts_par_doc[doceo] = concepts
                break
        etat[entree["reference"]] = trouve or ("question_non_posee" if non_pose else "documents_non_classes")
    resolveur.hors_ligne = hors_ligne_initial

    tous = {c for concepts in concepts_par_doc.values() for c in concepts}
    domaines: Optional[dict[str, dict[str, str]]] = {}
    if tous:
        try:
            domaines = resoudre_domaines(tous, session)
        except LibellesEurovocIndisponibles as exc:
            print(f"  ⚠ domaines EuroVoc des dossiers non publiés : {exc}", file=sys.stderr)
            domaines = None

    compteurs: dict[str, int] = {}
    for entree in entrees:
        resultat = etat.get(entree["reference"], "aucun_document_de_seance")
        entree["domaines"] = []
        if resultat not in concepts_par_doc:
            motif = resultat
        elif domaines is None:
            motif = "eurovoc_injoignable"
        else:
            poids: dict[str, int] = {}
            for concept in concepts_par_doc[resultat]:
                if concept in domaines:
                    code = domaines[concept]["code"]
                    poids[code] = poids.get(code, 0) + 1
            libelles = {d["code"]: d["libelle"] for d in domaines.values()}
            entree["domaines"] = [
                {"code": c, "libelle": libelles[c], "concepts": n}
                for c, n in sorted(poids.items(), key=lambda kv: (-kv[1], kv[0]))
            ]
            motif = None if entree["domaines"] else "domaine_eurovoc_introuvable"
        if entree["domaines"]:
            entree["domaines_document"] = resultat
            compteurs["avec_domaines"] = compteurs.get("avec_domaines", 0) + 1
        else:
            entree["domaines_non_resolu"] = {"motif": motif}
            compteurs[motif] = compteurs.get(motif, 0) + 1
    compteurs["requetes"] = resolveur.statistiques.get("requetes", 0) - depart
    compteurs["secondes"] = int(horloge() - debut)
    return compteurs


def construire(
    references: Iterable[str],
    force_download: bool = False,
    dump_path: Optional[Path] = None,
    documents: Optional[dict[str, list[str]]] = None,
) -> list[dict[str, Any]]:
    """Les entrées d'index pour les références visées, triées par référence."""
    voulues = {r for r in references if r}
    if not voulues:
        return []
    chemin = dump_path or ensure_dump(DUMP_DOSSIERS, force_download)
    if chemin is None:
        raise DumpDossiersIndisponible(
            f"{DUMP_DOSSIERS} indisponible : un index vide se lirait comme "
            "« aucun dossier européen » (#510).")

    entrees: list[dict[str, Any]] = []
    vues: set[str] = set()
    libelles_vus: dict[str, dict[str, str]] = {}
    if documents is None:
        documents = {}
    for dossier in iter_dump_zst(Path(chemin)):
        procedure = dossier.get("procedure")
        if not isinstance(procedure, dict):
            continue
        meta = dossier.get("meta") or {}
        # Les fiches anciennes du dump n'ont que `created` (2012) : sans ce
        # repli, « Internal market, SLIM » n'aurait pas de date et perdrait
        # quand même, mais par hasard.
        mise_a_jour = str(meta.get("updated") or meta.get("created") or "")
        for code, libelle in libelles_de_famille(dossier).items():
            dates = libelles_vus.setdefault(code, {})
            dates[libelle] = max(dates.get(libelle, ""), mise_a_jour)
        reference = procedure.get("reference")
        if reference not in voulues or reference in vues:
            continue
        vues.add(reference)
        # Rempli pour l'appelant qui en a besoin : les domaines se cherchent
        # ensuite, par le réseau, et le dump ne se relit pas pour autant.
        documents[reference] = documents_de_seance(dossier)
        # Le stade passe par la table de `textes_portes[]` — une seule fabrique
        # de cette correspondance, sans quoi les deux divergeraient le jour où
        # la source ajoute une valeur.
        stade, stade_non_resolu = _stade_procedural_ue(
            {"stade_source": procedure.get("stage_reached")})
        au_fond = commissions_au_fond(dossier)
        sujets = matieres(dossier)
        entree: dict[str, Any] = {
            "id": identifiant(reference),
            "reference": reference,
            "titre": procedure.get("title") or None,
            "type_procedure": procedure.get("type") or None,
            "stade_procedural": stade,
            "commissions_au_fond": au_fond,
            "matieres": sujets,
            "source_url": (dossier.get("meta") or {}).get("source")
            or f"https://parltrack.org/dossier/{reference}",
        }
        if stade_non_resolu:
            entree["stade_procedural_non_resolu"] = stade_non_resolu
        non_resolu = commissions_au_fond_non_resolu(dossier, au_fond)
        if non_resolu:
            entree["commissions_au_fond_non_resolu"] = non_resolu
        sans_matiere = matieres_non_resolu(dossier, sujets)
        if sans_matiere:
            entree["matieres_non_resolu"] = sans_matiere
        entrees.append(entree)
    libelles = choisir_libelles_de_famille(libelles_vus)
    for entree in entrees:
        publiees, non_resolu = familles(entree["matieres"], libelles)
        entree["familles"] = publiees
        if non_resolu:
            entree["familles_non_resolu"] = non_resolu
    entrees.sort(key=lambda e: e["reference"])
    return entrees


def document(entrees: list[dict[str, Any]]) -> dict[str, Any]:
    """L'index complet, entête comprise — même forme que `scrutins.json`."""
    return {
        "schema_version": SCHEMA_VERSION,
        "genere_le": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "licence_donnees": f"{LICENCE_PARLTRACK} ; {LICENCE_PORTAIL_ET_EUROVOC}",
        "dossiers": entrees,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--profils-dir", type=Path, default=DEFAULT_PROFILS_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_SORTIE)
    parser.add_argument("--force-download", action="store_true",
                        help="re-télécharger le dump même si un cache existe")
    parser.add_argument("--budget-secondes", type=int, default=BUDGET_SECONDES_PAR_RUN,
                        help="durée maximale de la passe des domaines EuroVoc, par run")
    parser.add_argument("--plafond-requetes", type=int, default=PLAFOND_REQUETES_PAR_RUN,
                        help="requêtes nouvelles au portail du Parlement pour les domaines EuroVoc, par run")
    parser.add_argument("--sans-domaines", action="store_true",
                        help="ne pas chercher les domaines EuroVoc (aucune requête réseau)")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    amendees: set[str] = set()
    refs = references_visees(args.profils_dir, amendees=amendees)
    print(f"→ {len(refs)} référence(s) de dossier citée(s) par les amendements, textes portés et votes publiés")
    documents: dict[str, list[str]] = {}
    entrees = construire(refs, force_download=args.force_download, documents=documents)
    if not args.sans_domaines:
        import requests  # noqa: PLC0415
        from europarl_documents import resolveur_par_defaut  # noqa: PLC0415

        resolveur = resolveur_par_defaut()
        compteurs = domaines_des_dossiers(
            entrees, documents, resolveur, requests.Session(),
            prioritaires=amendees, plafond=args.plafond_requetes,
            budget_secondes=args.budget_secondes)
        resolveur.enregistrer()
        print(f"  domaines EuroVoc : {compteurs}")
        if resolveur.statistiques.get("disjoncte"):
            print("  ⚠ le portail s'est tu : la passe des domaines s'est ARRÊTÉE en route.")
    manquantes = sorted(refs - {e["reference"] for e in entrees})
    if manquantes:
        print(f"  [!] {len(manquantes)} non résolue(s) dans le dump — déclarées "
              "absentes, jamais fabriquées (§2 règle 5) :", file=sys.stderr)
        for reference in manquantes[:10]:
            print(f"        {reference}", file=sys.stderr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(document(entrees), ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")
    poids = args.out.stat().st_size / 1024
    print(f"  ✓ {len(entrees)} dossier(s) écrit(s) dans {args.out} ({poids:.0f} Ko)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
