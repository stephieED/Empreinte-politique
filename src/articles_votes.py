#!/usr/bin/env python3
"""articles_votes.py — Sur quoi porte un article soumis au vote (#1264).

LE BESOIN. Un scrutin sur un article (« l'article 5 de la proposition de loi
apportant une réponse intégrale… ») ne dit rien de ce que l'article contient.
Ce module publie, pour chaque scrutin d'article, le titre, le chapitre et la
section sous lesquels l'article est rangé, et un extrait de son texte, depuis le
texte officiel de l'Assemblée.

LA CHAÎNE, ENTIÈREMENT PAR IDENTIFIANTS DE LA SOURCE. Un scrutin ne porte aucune
référence législative exploitable (`objet.referenceLegislative` est nul partout,
`scrutins_dossiers_an.py`). Mais il porte sa séance (`seanceRef`), et chaque
acte « discussion en séance publique » d'un dossier législatif porte la séance
où il a eu lieu (`reunionRef`). D'où, sans aucune ressemblance de titre (la
classification par libellé que `regrouper-nest-pas-joindre-639` interdit) :

    scrutin.seanceRef → acte AN?-DEBATS-SEANCE.reunionRef → dossier et lecture
      → texte discuté : `texteAdopte` du rapport de la commission saisie au fond
        de cette lecture, à défaut `texteAssocie` de son dépôt
      → l'article, dans le texte HTML de l'open data (`dyn/opendata/<uid>.html`)

À la XVIIe, le scrutin porte en plus `objet.dossierLegislatif.dossierRef` sur
275 des 902 scrutins d'article (archives du 08/10/2026). Il départage une
séance où plusieurs dossiers sont discutés ; il n'en remplace jamais la chaîne.

CE QUI N'EST PAS RATTACHÉ SE DÉCLARE (§2 règle 5), avec son motif : une séance
où plusieurs dossiers sont discutés et que le scrutin ne départage pas, un
article absent du texte, un texte sans version HTML (la XIVe n'en a aucune).

LE TEXTE HTML. Ses paragraphes portent des classes de structure : `assnat4Titre*`,
`assnat5Chapitre*`, `assnat6Section*`, `assnat9ArticleNum`, `assnatLoiTexte`.
Mesuré le 08/10/2026 sur 32 textes (8 par législature, XIV à XVII) : XIVe 0/8,
XVe-XVIIe 23/24 balisés, dont 5 seulement portent des titres ou chapitres. Un
texte publié ne change plus : il est téléchargé une fois et gardé en cache.
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import re
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable, Iterator, Optional

from schema_pivot import extrait_de_texte

SCHEMA_VERSION = "articles-votes-v1"
LICENCE = "Licence Ouverte / Open Licence (Etalab) — Assemblée nationale"

URL_TEXTE_HTML = "https://www.assemblee-nationale.fr/dyn/opendata/{uid}.html"
#: Le cache garde la STRUCTURE extraite, pas le HTML : 252 textes pèsent 199 Mo
#: en HTML (les lois de finances, 7,7 Mo chacune), quelques Ko en structure.
#: Le répertoire porte la version de la lecture : une lecture corrigée ne relit
#: jamais une structure écrite par l'ancienne (un cache porte le code qui l'a
#: écrit). Un texte absent (404) n'est pas mis en cache : il peut paraître.
VERSION_STRUCTURE = "v1"
CACHE_TEXTES = Path(".cache") / "textes_an_structure"
DEFAULT_OUT = Path("pivot_data") / "articles_votes.json"

#: Les législatures lues. La XIVe n'a aucun texte HTML (mesuré : 0/8).
LEGISLATURES = ("15", "16", "17")
#: Closes : leurs archives ne changent plus, gardées en cache pour de bon.
LEGISLATURES_CLOSES = frozenset({"15", "16"})
CACHE_SOURCES = Path(".cache") / "articles_votes"
_BASE = "https://data.assemblee-nationale.fr/static/openData/repository"
#: Noms des archives par législature, tels que l'Assemblée les publie.
ARCHIVES = {
    "scrutins": {"15": "loi/scrutins/Scrutins_XV.json.zip", "16": "loi/scrutins/Scrutins.json.zip",
                 "17": "loi/scrutins/Scrutins.json.zip"},
    "dossiers": {"15": "loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip",
                 "16": "loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip",
                 "17": "loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip"},
    # L'ordre du jour des réunions : la liste complète des dossiers d'une séance.
    "agenda": {"15": "vp/reunions/Agenda_XV.json.zip", "16": "vp/reunions/Agenda.json.zip",
               "17": "vp/reunions/Agenda.json.zip"},
}


class SourceIndisponible(RuntimeError):
    """Une archive n'a pas pu être lue : rien n'est écrit plutôt qu'un fichier amputé."""


def archive(famille: str, legislature: str, cache_dir: Path = CACHE_SOURCES) -> Path:
    """Le chemin local d'une archive, téléchargée si besoin.

    Une législature close se télécharge une fois ; la 17e à chaque appel. Les
    transferts de l'Assemblée se coupent en route (mesuré le 08/10/2026 sur la
    XVe) : reprises par `Range`, et un fichier incomplet n'est jamais gardé.
    """
    from download_watchdog import download_with_watchdog  # noqa: PLC0415

    chemin = cache_dir / legislature / Path(ARCHIVES[famille][legislature]).name.replace(
        ".json.zip", f".{famille}.json.zip")
    if chemin.is_file() and legislature in LEGISLATURES_CLOSES:
        return chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    url = f"{_BASE}/{legislature}/{ARCHIVES[famille][legislature]}"
    try:
        download_with_watchdog(url, chemin, headers={"User-Agent": "empreinte-politique/articles-votes"},
                               timeout=(15, 600), hard_timeout_seconds=1200, reprises=8)
        zipfile.ZipFile(chemin).close()
    except Exception as exc:  # noqa: BLE001 — toute panne de source arrête l'écriture
        chemin.unlink(missing_ok=True)
        raise SourceIndisponible(f"{famille} {legislature} : {url} — {exc}") from exc
    return chemin

#: Motifs d'un scrutin d'article non rattaché, vocabulaire fermé.
MOTIF_SEANCE_INCONNUE = "seance_sans_acte_de_dossier"
MOTIF_PLUSIEURS_DOSSIERS = "plusieurs_dossiers_en_seance"
MOTIF_TEXTE_INCONNU = "texte_discute_non_publie_par_le_dossier"
MOTIF_TEXTE_SANS_HTML = "texte_sans_version_html"
MOTIF_ARTICLE_ABSENT = "article_absent_du_texte"
MOTIF_ARTICLE_ILLISIBLE = "designation_d_article_illisible"
#: Un HTML publié dont aucun paragraphe ne porte la classe d'article : les lois
#: de finances ont leur propre gabarit (`assnatFPF*`, `assnatFAR*`), non lu ici.
MOTIF_GABARIT_NON_LU = "texte_a_gabarit_non_lu"
MOTIFS = frozenset({
    MOTIF_SEANCE_INCONNUE, MOTIF_PLUSIEURS_DOSSIERS, MOTIF_TEXTE_INCONNU,
    MOTIF_TEXTE_SANS_HTML, MOTIF_ARTICLE_ABSENT, MOTIF_ARTICLE_ILLISIBLE,
    MOTIF_GABARIT_NON_LU,
})

RATTACHEMENT_SEANCE = "seance_du_scrutin"
RATTACHEMENT_DOSSIER = "seance_et_dossier_du_scrutin"
#: Arbitrage de la propriétaire, 08/10/2026 (option A) : dans une séance où
#: plusieurs dossiers sont discutés, le texte retenu est le SEUL des textes
#: discutés qui porte l'article voté. Une élimination sur le texte officiel,
#: jamais une comparaison de titres ; 277 scrutins sur 568 mesurés.
RATTACHEMENT_ARTICLE = "seance_et_seul_texte_portant_l_article"


# ---------------------------------------------------------------------------
# La désignation d'un article
# ---------------------------------------------------------------------------

_RX_ARTICLE_LIBELLE = re.compile(
    r"^l'article\s+(.+?)\s*(?:\([^)]*\)\s*)?(?:de la |du |de l'|des )", re.IGNORECASE
)


def normaliser_article(designation: str) -> str:
    """« Article 1 er », « premier », « 4 bis » → « 1er », « 1er », « 4 bis »."""
    s = html_lib.unescape(designation or "").replace(" ", " ").lower()
    s = re.sub(r"^articles?\s+", "", s.strip())
    s = re.sub(r"\bpremier\b", "1er", s)
    s = re.sub(r"\b1\s+er\b", "1er", s)
    s = re.sub(r"\s+", " ", s).strip(" .,:;")
    # « 4 (nouveau) », « 14 (supprimé) » : une mention de la navette, pas la désignation.
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)
    return s


def article_du_libelle(libelle: str) -> Optional[str]:
    """La désignation d'article d'un libellé de scrutin, normalisée, ou None."""
    m = _RX_ARTICLE_LIBELLE.match((libelle or "").strip())
    return normaliser_article(m.group(1)) if m else None


def _deplier(designation: str) -> list[str]:
    """« 1er à 3 » → [« 1er », « 2 », « 3 »] ; une plage non numérique reste entière."""
    m = re.match(r"^(1er|\d+)\s+à\s+(\d+)$", designation)
    if not m:
        return [designation]
    debut = 1 if m.group(1) == "1er" else int(m.group(1))
    fin = int(m.group(2))
    if fin < debut or fin - debut > 50:
        return [designation]
    return ["1er" if n == 1 else str(n) for n in range(debut, fin + 1)]


# ---------------------------------------------------------------------------
# La structure d'un texte HTML
# ---------------------------------------------------------------------------

_RX_PARAGRAPHE = re.compile(r'<p[^>]*class="([^"]+)"[^>]*>(.*?)</p>', re.S)


def _texte(fragment: str) -> str:
    sans = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html_lib.unescape(sans).replace(" ", " ")).strip()


def _niveau(classe: str) -> Optional[tuple[str, str]]:
    """`(niveau, partie)` d'une classe de structure, ou None."""
    c = classe.lower()
    for niveau, motif in (("titre", "assnat4titre"), ("chapitre", "assnat5chapitre"),
                          ("section", "assnat6section")):
        if c.startswith(motif):
            if "num" in c:
                return niveau, "numero"
            if "intit" in c:
                return niveau, "intitule"
    if c.startswith("assnat9articlenum"):
        return "article", "numero"
    return None


def structure_du_texte(page: str) -> dict[str, dict[str, Any]]:
    """`article normalisé → {titre, chapitre, section, texte}` d'un texte HTML.

    Les divisions sont lues dans l'ordre du document : un nouveau titre efface
    chapitre et section, un nouveau chapitre efface la section. Le texte d'un
    article est la suite de ses paragraphes jusqu'à la division suivante.
    """
    courant: dict[str, Optional[dict[str, Optional[str]]]] = {
        "titre": None, "chapitre": None, "section": None}
    articles: dict[str, dict[str, Any]] = {}
    en_cours: list[str] = []
    corps: list[str] = []

    def clore() -> None:
        if en_cours:
            texte = " ".join(corps).strip() or None
            for designation in en_cours:
                articles[designation]["texte"] = texte
        en_cours.clear()
        corps.clear()

    for classe, fragment in _RX_PARAGRAPHE.findall(page):
        texte = _texte(fragment)
        niveau = _niveau(classe)
        if niveau is None:
            if en_cours and texte and classe.lower().startswith("assnat"):
                corps.append(texte)
            continue
        nom, partie = niveau
        if nom == "article":
            clore()
            brut = normaliser_article(texte)
            for designation in _deplier(brut):
                articles[designation] = {
                    "titre": dict(courant["titre"]) if courant["titre"] else None,
                    "chapitre": dict(courant["chapitre"]) if courant["chapitre"] else None,
                    "section": dict(courant["section"]) if courant["section"] else None,
                    "regroupe": brut if brut != designation else None,
                }
                en_cours.append(designation)
            continue
        clore()
        if partie == "numero":
            courant[nom] = {"numero": texte or None, "intitule": None}
            if nom == "titre":
                courant["chapitre"] = courant["section"] = None
            elif nom == "chapitre":
                courant["section"] = None
        else:
            if courant[nom] is None:
                courant[nom] = {"numero": None, "intitule": texte or None}
            else:
                precedent = courant[nom].get("intitule")
                courant[nom]["intitule"] = f"{precedent} {texte}".strip() if precedent else (texte or None)
    clore()
    return articles


def telecharger_texte_html(uid: str) -> Optional[str]:
    """Le texte HTML d'un document chez la source, ou None s'il n'existe pas."""
    import requests  # noqa: PLC0415

    for essai in range(3):
        try:
            reponse = requests.get(URL_TEXTE_HTML.format(uid=uid), timeout=(15, 120),
                                   headers={"User-Agent": "empreinte-politique/articles-votes"})
        except requests.RequestException:
            time.sleep(2 * (essai + 1))
            continue
        if reponse.status_code == 404:
            return None
        if reponse.ok:
            return reponse.text
        time.sleep(2 * (essai + 1))
    return None


# ---------------------------------------------------------------------------
# Les séances des dossiers
# ---------------------------------------------------------------------------

def _actes(noeud: Any) -> Iterator[dict[str, Any]]:
    if isinstance(noeud, dict):
        if "codeActe" in noeud:
            yield noeud
        for valeur in noeud.values():
            if isinstance(valeur, (dict, list)):
                yield from _actes(valeur)
    elif isinstance(noeud, list):
        for x in noeud:
            yield from _actes(x)


def _lectures(dossier: dict[str, Any]) -> Iterator[list[dict[str, Any]]]:
    """Les blocs de lecture d'un dossier : les actes de premier niveau et leurs descendants."""
    racine = (dossier.get("actesLegislatifs") or {}).get("acteLegislatif") or []
    if isinstance(racine, dict):
        racine = [racine]
    for bloc in racine:
        if isinstance(bloc, dict):
            yield list(_actes(bloc))


def _texte_discute(actes: list[dict[str, Any]], date: str) -> Optional[str]:
    """Le texte discuté en séance dans une lecture, au jour `date`."""
    rapports = sorted(
        (a.get("dateActe") or "", a["texteAdopte"]) for a in actes
        if str(a.get("codeActe", "")).endswith("-COM-FOND-RAPPORT") and a.get("texteAdopte")
        and (a.get("dateActe") or "")[:10] <= date
    )
    if rapports:
        return rapports[-1][1]
    depots = sorted(
        (a.get("dateActe") or "", a["texteAssocie"]) for a in actes
        if str(a.get("codeActe", "")).endswith("-DEPOT") and a.get("texteAssocie")
    )
    return depots[-1][1] if depots else None


class IndexDossiers:
    """Les séances et les lectures des dossiers législatifs.

    `seances` : `reunionRef → {dossier: actes de la lecture}`, depuis les actes
    « discussion en séance publique ». `lectures` : `dossier → [actes de chaque
    lecture]`, pour retrouver la lecture d'un dossier que l'ordre du jour nomme
    mais dont l'acte de séance ne porte pas la réunion.
    """

    def __init__(self, dossiers: Iterable[dict[str, Any]]) -> None:
        self.seances: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self.lectures: dict[str, list[list[dict[str, Any]]]] = {}
        for dossier in dossiers:
            uid = dossier.get("uid")
            if not uid:
                continue
            for actes in _lectures(dossier):
                self.lectures.setdefault(uid, []).append(actes)
                for acte in actes:
                    if str(acte.get("codeActe", "")).endswith("-DEBATS-SEANCE") and acte.get("reunionRef"):
                        self.seances.setdefault(acte["reunionRef"], {})[uid] = actes

    def textes(self, dossier: str) -> list[str]:
        """Toutes les versions de texte qu'un dossier nomme : déposées, adoptées."""
        vus: list[str] = []
        for actes in self.lectures.get(dossier, []):
            for acte in actes:
                for cle in ("texteAssocie", "texteAdopte"):
                    uid = acte.get(cle)
                    if isinstance(uid, str) and re.match(r"^(PRJL|PION|PNRE|PPR)", uid) and uid not in vus:
                        vus.append(uid)
        return vus

    def lecture_du_jour(self, dossier: str, seance: Optional[str], date: str) -> Optional[list[dict[str, Any]]]:
        """La lecture d'un dossier discutée à cette séance, ou ce jour-là."""
        par_seance = (self.seances.get(seance or "") or {}).get(dossier)
        if par_seance is not None:
            return par_seance
        du_jour = [
            actes for actes in self.lectures.get(dossier, [])
            if any(str(a.get("codeActe", "")).endswith("-DEBATS-SEANCE")
                   and (a.get("dateActe") or "")[:10] == date for a in actes)
        ]
        return du_jour[0] if len(du_jour) == 1 else None


def ordre_du_jour(zip_path: Path) -> dict[str, list[str]]:
    """`uid de réunion → dossiers à son ordre du jour`, depuis l'open data Agenda."""
    resultat: dict[str, list[str]] = {}
    with zipfile.ZipFile(zip_path) as archive:
        for nom in archive.namelist():
            if not nom.endswith(".json"):
                continue
            reunion = json.loads(archive.read(nom)).get("reunion") or {}
            points = ((reunion.get("ODJ") or {}).get("pointsODJ") or {}).get("pointODJ") or []
            if isinstance(points, dict):
                points = [points]
            dossiers: list[str] = []
            for point in points:
                ref = (point.get("dossiersLegislatifsRefs") or {}).get("dossierRef") if isinstance(point, dict) else None
                for d in ([ref] if isinstance(ref, str) else (ref or [])):
                    if d not in dossiers:
                        dossiers.append(d)
            if reunion.get("uid"):
                resultat[reunion["uid"]] = dossiers
    return resultat


# ---------------------------------------------------------------------------
# Les scrutins d'article
# ---------------------------------------------------------------------------

def scrutins_d_article(zip_path: Path, legislature: str) -> Iterator[dict[str, Any]]:
    """Les scrutins d'article d'une archive brute `Scrutins*.json.zip`."""
    with zipfile.ZipFile(zip_path) as archive:
        for nom in archive.namelist():
            if not nom.endswith(".json"):
                continue
            scrutin = json.loads(archive.read(nom)).get("scrutin") or {}
            uid = str(scrutin.get("uid") or "")
            m = re.match(r"^VTANR5L(\d+)V(\d+)$", uid)
            if not m:
                continue
            objet = scrutin.get("objet") or {}
            libelle = objet.get("libelle") or ""
            if not libelle.lower().startswith("l'article "):
                continue
            dossier = objet.get("dossierLegislatif")
            yield {
                "scrutin_id": f"an:{m.group(1)}:{m.group(2)}",
                "date": (scrutin.get("dateScrutin") or "")[:10],
                "libelle": libelle,
                "seance_ref": scrutin.get("seanceRef"),
                "dossier_ref": dossier.get("dossierRef") if isinstance(dossier, dict) else None,
            }


def rattacher(
    scrutin: dict[str, Any],
    index: IndexDossiers,
    agenda: dict[str, list[str]],
    textes: "LecteurDeTextes",
) -> dict[str, Any]:
    """Une entrée publiée, ou un non-rattachement avec son motif.

    Les dossiers candidats sont ceux de l'ORDRE DU JOUR de la séance, unis à
    ceux dont un acte de séance porte la réunion : un dossier discuté dont
    l'acte manque ne doit pas disparaître des candidats (mesuré le 08/10/2026 :
    sans l'ordre du jour, 30 rattachements sur 1 564 désignaient le mauvais
    dossier — l'article 6 d'une loi sur le sport attribué à celle sur le marché
    de l'art, faute du dossier du sport parmi les candidats).
    """
    article = article_du_libelle(scrutin["libelle"])
    if article is None:
        return {"motif": MOTIF_ARTICLE_ILLISIBLE}
    seance = scrutin.get("seance_ref")
    if scrutin.get("dossier_ref"):
        dossiers = [scrutin["dossier_ref"]]
    else:
        dossiers = list(dict.fromkeys(
            list(agenda.get(seance or "") or []) + list((index.seances.get(seance or "") or {}))))
    if not dossiers:
        return {"motif": MOTIF_SEANCE_INCONNUE, "seance_ref": seance}
    lectures = set()
    for dossier in dossiers:
        actes = index.lecture_du_jour(dossier, seance, scrutin["date"])
        lectures.add((dossier, _texte_discute(actes, scrutin["date"]) if actes else None))
    rattachement = RATTACHEMENT_DOSSIER if scrutin.get("dossier_ref") else RATTACHEMENT_SEANCE
    if len(lectures) > 1:
        # L'élimination n'est sûre que si CHAQUE texte candidat a été lu : un
        # texte inconnu pourrait porter l'article.
        structures = {t: (textes.structure(t) if t else None) for _, t in lectures}
        lisibles = all(structures[t] for _, t in lectures)
        porteurs = [(d, t) for d, t in lectures if t and (structures[t] or {}).get(article) is not None]
        if not lisibles or len(porteurs) != 1:
            return {"motif": MOTIF_PLUSIEURS_DOSSIERS, "dossiers": sorted(dossiers)}
        # Un dossier concurrent n'est écarté que si AUCUNE version de son texte
        # ne porte l'article, et que toutes ont été lues : la version retenue
        # pour lui peut être la mauvaise (une version d'avant les articles
        # ajoutés), et l'écarter sur elle seule attribuait l'article au voisin.
        retenu = porteurs[0][0]
        for autre in {d for d, _ in lectures} - {retenu}:
            versions = [textes.structure(t) for t in index.textes(autre)]
            if not versions or any(v is None or not v or article in v for v in versions):
                return {"motif": MOTIF_PLUSIEURS_DOSSIERS, "dossiers": sorted(dossiers)}
        lectures = set(porteurs)
        rattachement = RATTACHEMENT_ARTICLE
    ((dossier, texte_id),) = lectures
    if texte_id is None:
        return {"motif": MOTIF_TEXTE_INCONNU, "dossier_id": dossier}
    structure = textes.structure(texte_id)
    if structure is None:
        return {"motif": MOTIF_TEXTE_SANS_HTML, "dossier_id": dossier, "texte_id": texte_id}
    if not structure:
        return {"motif": MOTIF_GABARIT_NON_LU, "dossier_id": dossier, "texte_id": texte_id}
    fiche = structure.get(article)
    if fiche is None:
        return {"motif": MOTIF_ARTICLE_ABSENT, "dossier_id": dossier, "texte_id": texte_id,
                "article": article}
    extrait, tronque = extrait_de_texte(fiche.get("texte"))
    return {
        "dossier_id": dossier,
        "texte_id": texte_id,
        "rattachement": rattachement,
        "article": article,
        "regroupe": fiche.get("regroupe"),
        "titre": fiche.get("titre"),
        "chapitre": fiche.get("chapitre"),
        "section": fiche.get("section"),
        "extrait": extrait,
        "texte_tronque": tronque,
        "source_url": URL_TEXTE_HTML.format(uid=texte_id),
    }


class LecteurDeTextes:
    """Mémo des structures de texte d'un run : un texte lu une fois."""

    def __init__(self, cache_dir: Path = CACHE_TEXTES, *, reseau: bool = True) -> None:
        self.cache_dir = cache_dir
        self.reseau = reseau
        self._memo: dict[str, Optional[dict[str, dict[str, Any]]]] = {}

    def structure(self, uid: str) -> Optional[dict[str, dict[str, Any]]]:
        """La structure d'un texte ; `{}` pour un gabarit non lu, None sans texte."""
        if uid in self._memo:
            return self._memo[uid]
        chemin = self.cache_dir / VERSION_STRUCTURE / f"{uid}.json"
        structure: Optional[dict[str, dict[str, Any]]] = None
        if chemin.is_file():
            structure = json.loads(chemin.read_text(encoding="utf-8"))
        elif self.reseau:
            page = telecharger_texte_html(uid)
            if page is not None:
                structure = structure_du_texte(page)
                # Le cache ne garde que ce que la publication lit : un extrait.
                for fiche in structure.values():
                    if fiche.get("texte"):
                        fiche["texte"] = fiche["texte"][:1000]
                chemin.parent.mkdir(parents=True, exist_ok=True)
                chemin.write_text(json.dumps(structure, ensure_ascii=False), encoding="utf-8")
        self._memo[uid] = structure
        return structure


def construire(
    scrutins: Iterable[dict[str, Any]],
    dossiers: Iterable[dict[str, Any]],
    textes: LecteurDeTextes,
    *,
    agenda: dict[str, list[str]],
    genere_le: str,
) -> dict[str, Any]:
    index = IndexDossiers(dossiers)
    publies: dict[str, dict[str, Any]] = {}
    non_rattaches: dict[str, dict[str, Any]] = {}
    for scrutin in scrutins:
        entree = rattacher(scrutin, index, agenda, textes)
        (non_rattaches if "motif" in entree else publies)[scrutin["scrutin_id"]] = entree
    return {
        "schema_version": SCHEMA_VERSION,
        "genere_le": genere_le,
        "licence_donnees": LICENCE,
        "scrutins": dict(sorted(publies.items())),
        "non_rattaches": dict(sorted(non_rattaches.items())),
    }


def _dossiers_de_l_archive(zip_path: Path) -> Iterator[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        for nom in archive.namelist():
            if "/dossierParlementaire/" in nom and nom.endswith(".json"):
                yield (json.loads(archive.read(nom)).get("dossierParlementaire") or {})


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scrutins", action="append", default=[], metavar="LEG:ZIP",
                        help="archive brute des scrutins d'une législature (répétable)")
    parser.add_argument("--dossiers", action="append", default=[], metavar="ZIP",
                        help="archive des dossiers législatifs (répétable)")
    parser.add_argument("--agenda", action="append", default=[], metavar="ZIP",
                        help="archive Agenda (ordre du jour des réunions) d'une législature (répétable)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache-textes", type=Path, default=CACHE_TEXTES)
    parser.add_argument("--hors-ligne", action="store_true", help="ne lire que le cache des textes")
    parser.add_argument("--telecharger", action="store_true",
                        help="télécharger les archives des XVe-XVIIe (au lieu de --scrutins/--dossiers/--agenda)")
    parser.add_argument("--cache-sources", type=Path, default=CACHE_SOURCES)
    args = parser.parse_args(argv)

    if args.telecharger:
        try:
            for legislature in LEGISLATURES:
                args.scrutins.append(f"{legislature}:{archive('scrutins', legislature, args.cache_sources)}")
                args.dossiers.append(str(archive("dossiers", legislature, args.cache_sources)))
                args.agenda.append(str(archive("agenda", legislature, args.cache_sources)))
        except SourceIndisponible as exc:
            print(f"::error::ARTICLES_VOTES_SOURCE_INDISPONIBLE — {exc}. Rien n'est écrit : "
                  "le fichier publié reste celui du run précédent.")
            return 1

    scrutins: list[dict[str, Any]] = []
    for valeur in args.scrutins:
        legislature, chemin = valeur.split(":", 1)
        scrutins.extend(scrutins_d_article(Path(chemin), legislature))
    dossiers = [d for chemin in args.dossiers for d in _dossiers_de_l_archive(Path(chemin))]
    agenda: dict[str, list[str]] = {}
    for chemin in args.agenda:
        agenda.update(ordre_du_jour(Path(chemin)))
    resultat = construire(scrutins, dossiers, LecteurDeTextes(args.cache_textes, reseau=not args.hors_ligne),
                          agenda=agenda, genere_le=time.strftime("%Y-%m-%d"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Un index partagé ne se réécrit que si son contenu change : `genere_le`
    # seul ne fait pas un commit (#1075).
    if args.out.is_file():
        try:
            ancien = json.loads(args.out.read_text(encoding="utf-8"))
        except ValueError:
            ancien = None
        if isinstance(ancien, dict) and {k: v for k, v in ancien.items() if k != "genere_le"} == {
                k: v for k, v in resultat.items() if k != "genere_le"}:
            resultat["genere_le"] = ancien.get("genere_le", resultat["genere_le"])
    args.out.write_text(json.dumps(resultat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    motifs: dict[str, int] = {}
    for entree in resultat["non_rattaches"].values():
        motifs[entree["motif"]] = motifs.get(entree["motif"], 0) + 1
    print(f"{len(resultat['scrutins'])} scrutin(s) d'article rattaché(s), "
          f"{len(resultat['non_rattaches'])} non rattaché(s) : {motifs}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
