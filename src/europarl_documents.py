#!/usr/bin/env python3
"""
europarl_documents.py — De la référence citée dans un intitulé de vote à
l'adresse vérifiée du document qu'elle désigne (#827).

## Les trois décisions à relire avant de toucher à ce module

Cinq décisions nomment ce module ; la liste complète est dans
`docs/decisions-par-module.md`. Ces trois-là portent ce qui casse en silence :

- `docs/decisions/urls-explications-vote-europeennes-827.md` — **l'adresse est
  dérivée, l'existence est prouvée** au portail, jamais supposée.
- `docs/decisions/disjoncteur-portail-europeen-901.md` — **un portail muet n'est
  pas un `429`** : après cinq silences, la passe s'arrête et le dit.
- `docs/decisions/titre-francais-lu-dans-source-url-901.md` — **le document se lit
  dans `source_url`, jamais dans le titre**, et une entrée d'un lecteur plus ancien
  est réinterrogée une fois : trois défauts qui ont publié 0 titre français.

## Le problème

Les explications de vote du Parlement européen sont la seule matière du corpus
européen où le candidat écrit lui-même pourquoi il a voté ainsi. ParlTrack en
transcrit le texte, mais **ne donne aucun lien** : mesuré le 10/09/2026 sur les
7 candidats déclarés ayant un mandat européen, **0 des 1 801 entrées `WEXP`**
porte une `url` ou un `formats[]`, alors que les neuf autres types d'activité
en portent **100 %**. Le trou est d'un seul type, pas de la source.

## Ce que l'intitulé donne, et ce qu'il ne donne pas

L'intitulé cite le document entre parenthèses :

    Mobilisation of the EGF: application EGF/2016/008 FI/Nokia (A8-0196/2017 - Petri Sarvamaa) FR

**1 530 des 1 801** entrées (85 %) en portent une. Les 271 autres n'en portent
aucune — leur intitulé est en prose (« Allocation of slots at Community
airports: common rules ») — et n'auront donc **jamais** de lien : c'est un fait
sur la source, pas une lacune de la collecte (§2 règle 5).

## Pourquoi l'adresse est dérivée mais l'existence prouvée

L'adresse publique se déduit de la référence. **Sa validité, non** :
`www.europarl.europa.eu` est derrière un pare-feu anti-robot AWS qui répond
`HTTP 202`, 0 octet, `x-amzn-waf-action: challenge` — *identiquement* pour une
URL vraie et pour une URL inventée, même avec un User-Agent de navigateur.
Aucun job ne peut donc vérifier ces adresses, ni à la collecte, ni au contrôle
qualité, ni jamais.

Publier une URL dérivée sans preuve fabriquerait des liens morts indétectables
— **22 sont déjà connus**, dont 17 documents transmis par une autre institution
(type `C`) et une coquille de la source (`A9-0390/2017` annonce le terme 9 pour
2017, alors qu'il commence en 2019). Ce serait contraire à §2 règle 2.

D'où la règle : **l'existence est établie sur `data.europarl.europa.eu`**, qui
n'a pas de pare-feu et répond `200` ou `404`, puis l'adresse publique est écrite
pour le lecteur.

Éprouvé le 10/09/2026 sur **18 URL** ouvertes une à une dans un navigateur —
seule façon de franchir le défi anti-robot : les **13** documents que le portail
confirme s'ouvrent, les **5** contrôles négatifs échouent. **Zéro divergence.**
L'échantillon couvre 2015→2024, les types `A`, `B` et `RC`, et six documents
dont le portail n'expose qu'un PDF — le format servi par le portail n'a aucune
incidence sur l'existence de la page publique.

**Cette équivalence est éprouvée, jamais surveillée.** 18 URL, pas 1 508, et le
pare-feu interdit tout contrôle continu : si le Parlement change sa chaîne de
publication, rien ne nous en avertira.

## Le débit du portail se déclare en le dépassant

Aucune réponse `200` ne porte d'en-tête de limite. Une première passe sans
pause a rendu **1 320 réponses `429` sur 1 424** — mesure entièrement perdue.
La limite ne s'annonce qu'une fois franchie, par `HTTP 429` + `Retry-After: 60`.
Reprise à une requête toutes les 0,6 s : 47 minutes, **13 blocages de 60 s**
malgré la pause. D'où le cache disque, qui rend la seconde passe gratuite, et le
respect du `Retry-After`, sans lequel un job perd son heure comme la première
passe a perdu la sienne.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Optional

import requests

#: Le portail open data — pas de pare-feu, répond 200 ou 404.
PORTAIL_API = "https://data.europarl.europa.eu/api/v2"

#: Le site public — lisible par un humain, invérifiable par un job.
DOCEO_BASE = "https://www.europarl.europa.eu/doceo/document"

CACHE_DIR = Path(".cache") / "europarl"
CACHE_DOCUMENTS = CACHE_DIR / "documents_doceo.json"

#: Une requête toutes les 0,6 s — le débit que le portail tolère avant de
#: répondre 429. Mesuré : il en reste 13 sur 1 320 requêtes, d'où le respect
#: du `Retry-After` en plus de la pause.
PAUSE_ENTRE_REQUETES = 0.6
DELAI_REPLI_429 = 60
MAX_ESSAIS = 4

#: Échecs réseau CONSÉCUTIFS après lesquels la passe cesse d'interroger (#901).
#:
#: Le 16/09/2026, le portail a cessé de répondre sur `/documents` — pas un
#: `429` avec son `Retry-After`, que ce module sait attendre, mais un **silence**
#: de 30 s par requête. Les autres ressources du même portail répondaient encore
#: (`/meps` en 12 s), et la même URL servie depuis un autre réseau rendait 200 :
#: la limitation visait notre adresse, sur cette ressource.
#:
#: Sans disjoncteur, une passe sur 279 documents paie `TIMEOUT` pour chacun —
#: **2 h 20** — pour finir sans un seul titre, et sans que rien ne dise
#: pourquoi. Le seuil est bas exprès : cinq silences d'affilée ne sont plus un
#: aléa, et la donnée manquante se déclare aussi bien après 5 échecs qu'après
#: 279.
MAX_ECHECS_CONSECUTIFS = 5
TIMEOUT = 30

#: La référence telle que l'intitulé la cite, entre parenthèses.
#: `(A8-0196/2017 - Petri Sarvamaa)` ou `(RC-B8-0292/2018)`.
_RE_REFERENCE = re.compile(r"\((RC-)?([ABC])(\d{1,2})-(\d{4})/(\d{4})")


def reference_doceo(intitule: Any) -> Optional[str]:
    """La référence de document citée dans un intitulé, en forme `doceo`.

    Deux formes, et la seconde n'est pas une variante de la première :

    - `B8-0240/2017`     → `B-8-2017-0240`
    - `RC-B8-0292/2018`  → `RC-8-2018-0292`  — **la lettre disparaît**

    Vérifié sur 79 785 paires du corpus européen, 0 divergence, puis éprouvé
    dans un navigateur sur deux `RC-` : c'est la conversion la plus risquée du
    lot, parce qu'une lettre gardée par erreur produirait une URL fausse et
    silencieuse.

    `None` si l'intitulé ne cite aucun document — 271 des 1 801 explications.
    """
    if not isinstance(intitule, str):
        return None
    m = _RE_REFERENCE.search(intitule)
    if not m:
        return None
    resolution_commune, lettre, legislature, numero, annee = m.groups()
    if resolution_commune:
        return f"RC-{legislature}-{annee}-{numero}"
    return f"{lettre}-{legislature}-{annee}-{numero}"


#: Le nom d'un document dans son adresse publique, schéma ignoré : 625
#: `source_url` du corpus sont en `http://`, 56 en `https://` (16/09/2026).
_DOCEO_DANS_URL = re.compile(r"doceo/document/([A-Z]+-\d+-\d{4}-\d{4})")


def document_doceo_de_url(url: Any) -> Optional[str]:
    """`…/doceo/document/B-8-2017-0240_EN.html` → `B-8-2017-0240` (#901).

    La même lecture que la clé de fusion des textes portés européens
    (`merge_profile._document_doceo`) : un document est identifié par son
    adresse, jamais par son titre, qui ne le cite pas.
    """
    if not isinstance(url, str):
        return None
    m = _DOCEO_DANS_URL.search(url)
    return m.group(1) if m else None


def url_doceo(doceo: str) -> str:
    """L'adresse publique du document, celle qu'un lecteur peut ouvrir.

    Fonction **pure** : elle écrit une adresse, elle ne prouve rien. Son
    résultat ne se publie qu'après `ResolveurDocuments.existe()`.
    """
    return f"{DOCEO_BASE}/{doceo}_FR.html"


class ResolveurDocuments:
    """Dit si un document existe, en interrogeant le portail open data.

    Le cache disque est la pièce maîtresse, pas une optimisation : sans lui,
    chaque run repaie 47 minutes pour un corpus qui ne bouge pas. Une entrée
    négative (404) est mise en cache **comme les autres** — c'est un fait établi
    sur le document, pas un échec de collecte.

    `session` est injectable pour que les tests n'aient jamais besoin du réseau,
    que `tests/conftest.py` refuse depuis #473.
    """

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        session: Optional[Any] = None,
        hors_ligne: bool = False,
    ) -> None:
        self.cache_path = Path(cache_path) if cache_path else CACHE_DOCUMENTS
        self.session = session
        self.hors_ligne = hors_ligne
        self._cache: dict[str, dict[str, Any]] = self._charger()
        self._interroges = 0
        self._refuses = 0
        self._echecs_consecutifs = 0
        self._disjoncte = False

    def _charger(self) -> dict[str, dict[str, Any]]:
        """Le cache, dans sa forme courante ou dans celle d'avant (#901).

        `documents-doceo-v1` mappait un doceo sur un **booléen** ; v2 le mappe
        sur `{"existe": bool, "titre_fr": str | None}`, parce que la réponse du
        portail portait déjà le titre français et qu'on le jetait. Un cache v1
        se relit sans être invalidé : ses entrées valent « existe, titre
        inconnu », et le titre se remplira à la prochaine interrogation.
        """
        try:
            with open(self.cache_path, encoding="utf-8") as fh:
                document = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}
        entrees = document.get("documents") if isinstance(document, dict) else None
        if not isinstance(entrees, dict):
            return {}
        cache: dict[str, dict[str, Any]] = {}
        for doceo, valeur in entrees.items():
            if isinstance(valeur, dict):
                concepts = valeur.get("concepts")
                cache[doceo] = {
                    "existe": bool(valeur.get("existe")),
                    "titre_fr": valeur.get("titre_fr") or None,
                    # `None` ≠ `[]` : v2 ne connaissait pas les concepts, et une
                    # liste vide dirait « ce document n'en a aucun ». Une entrée
                    # v2 est donc « concepts inconnus », et se remplira à la
                    # prochaine interrogation (#901).
                    "concepts": list(concepts) if isinstance(concepts, list) else None,
                }
            else:
                cache[doceo] = {"existe": bool(valeur), "titre_fr": None, "concepts": None}
        return cache

    def enregistrer(self) -> None:
        """Écrit le cache. À appeler une fois, en fin de passe."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as fh:
            json.dump(
                {"schema_version": "documents-doceo-v3", "documents": self._cache},
                fh, ensure_ascii=False,
            )

    def existe(self, doceo: str) -> Optional[bool]:
        """`True` si le document existe, `False` s'il est introuvable.

        `None` quand la question n'a pas pu être posée — hors ligne, ou portail
        injoignable. **Ce n'est pas `False`** : une ignorance publiée comme un
        fait négatif est exactement ce que §2 règle 5 interdit, et l'appelant
        doit pouvoir distinguer « ce document n'existe pas » de « nous n'avons
        pas pu demander ».
        """
        entree = self._entree(doceo)
        return None if entree is None else entree["existe"]

    def _entree(self, doceo: str, complete: bool = False) -> Optional[dict[str, Any]]:
        """L'entrée de cache d'un document, interrogée au besoin.

        Le cache répond toujours, disjoncteur ou non : ce qui a été obtenu reste
        acquis. Seule l'interrogation s'arrête.

        `complete` : l'appelant a besoin du titre ou des concepts, pas seulement
        de l'existence. Une entrée écrite par un lecteur plus ancien — un
        booléen v1, un `{existe, titre_fr}` v2 — connaît l'existence mais
        **ignore** le reste, et se reconnaît à `concepts is None` : le lecteur
        courant écrit toujours une liste, vide ou non. Elle est alors
        réinterrogée une fois.

        C'était le troisième défaut du run 35087127267 : la docstring de
        `_charger` promettait que le titre « se remplirait à la prochaine
        interrogation », et **aucune n'avait lieu** — une entrée en cache
        n'était jamais redemandée. La réinterrogation reste réservée à ce
        besoin : `existe()` seul ne la déclenche pas, sans quoi les ~1 500
        explications de vote déjà connues seraient toutes redemandées.
        """
        connue = self._cache.get(doceo)
        if connue is not None and not (
            complete and connue.get("existe") and connue.get("concepts") is None
        ):
            return connue
        if self.hors_ligne or self.session is None or self._disjoncte:
            return connue
        resultat = self._interroger(doceo)
        if resultat is None:
            self._echecs_consecutifs += 1
            if self._echecs_consecutifs >= MAX_ECHECS_CONSECUTIFS:
                # Le reste de la passe se déclare « question non posée » sans
                # payer un TIMEOUT par document. Ce n'est PAS « n'existe pas » :
                # l'appelant reçoit None, comme hors ligne (§2 règle 5).
                self._disjoncte = True
            return connue
        self._echecs_consecutifs = 0
        self._cache[doceo] = resultat
        return resultat

    def titre_francais(self, doceo: str) -> Optional[str]:
        """Le titre FRANÇAIS que le portail publie pour ce document (#901).

        Il était déjà téléchargé et jeté : `_interroger` lisait la réponse pour
        en tirer un booléen, alors que `title_dcterms` y porte le titre en 22 à
        23 langues. Mesuré le 16/09/2026 sur 20 des 628 résolutions sans
        dossier : **20 sur 20** ont un titre français, 19 un titre anglais.

        `None` quand le portail n'en publie pas, ou quand la question n'a pas pu
        être posée — l'appelant garde alors le titre anglais du dump ParlTrack
        plutôt que de publier un vide (§2 règle 5).
        """
        entree = self._entree(doceo, complete=True)
        return None if entree is None else entree.get("titre_fr")

    def concepts_eurovoc(self, doceo: str) -> Optional[list[str]]:
        """Les identifiants EuroVoc du document — `None` si la question n'a pas
        pu être posée, `[]` si le portail n'en publie aucun (#901).

        La distinction est la même que partout ailleurs : ne pas savoir n'est
        pas savoir qu'il n'y a rien (§2 règle 5). Elle vaut aussi pour un cache
        écrit avant ce lot, qui rend `None` plutôt qu'une liste vide.
        """
        entree = self._entree(doceo, complete=True)
        if entree is None:
            return None
        concepts = entree.get("concepts")
        return list(concepts) if isinstance(concepts, list) else None

    @staticmethod
    def _data(charge: Any) -> Optional[dict[str, Any]]:
        """`data`, que le portail rend tantôt en objet, tantôt en liste d'un."""
        if not isinstance(charge, dict):
            return None
        data = charge.get("data")
        if isinstance(data, list):
            data = data[0] if data else None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _concepts(charge: Any) -> list[str]:
        """Les concepts EuroVoc du document — `data.is_about` (#901).

        La source rend des URI (`http://eurovoc.europa.eu/2155`) ; seul
        l'identifiant est conservé, l'URI se reconstruisant. Leurs libellés
        vivent ailleurs : `documents_europeens.py` les résout chez l'Office des
        publications, qui publie EuroVoc sous CC BY 4.0.
        """
        data = ResolveurDocuments._data(charge)
        if data is None:
            return []
        brut = data.get("is_about")
        if isinstance(brut, str):
            brut = [brut]
        if not isinstance(brut, list):
            return []
        codes: list[str] = []
        for uri in brut:
            code = str(uri).rstrip("/").rsplit("/", 1)[-1].strip()
            if code and code not in codes:
                codes.append(code)
        return codes

    @staticmethod
    def _titre_fr(charge: Any) -> Optional[str]:
        """`data.title_dcterms.fr`, quelle que soit la forme du conteneur.

        Le portail rend `data` tantôt comme objet, tantôt comme liste d'un seul
        élément — les deux se rencontrent sur ce corpus.
        """
        data = ResolveurDocuments._data(charge)
        if data is None:
            return None
        titres = data.get("title_dcterms")
        if not isinstance(titres, dict):
            return None
        titre = titres.get("fr")
        if isinstance(titre, list):
            titre = titre[0] if titre else None
        titre = (titre or "").strip() if isinstance(titre, str) else None
        return titre or None

    def _interroger(self, doceo: str) -> Optional[dict[str, Any]]:
        url = f"{PORTAIL_API}/documents/{doceo}"
        params = {"language": "fr", "format": "application/ld+json"}
        for _ in range(MAX_ESSAIS):
            try:
                reponse = self.session.get(url, params=params, timeout=TIMEOUT)
            except Exception:
                return None
            self._interroges += 1
            if reponse.status_code == 429:
                self._refuses += 1
                attente = reponse.headers.get("Retry-After")
                try:
                    delai = int(attente)
                except (TypeError, ValueError):
                    delai = DELAI_REPLI_429
                time.sleep(delai + 1)
                continue
            time.sleep(PAUSE_ENTRE_REQUETES)
            if reponse.status_code == 404:
                return {"existe": False, "titre_fr": None, "concepts": []}
            if reponse.status_code == 200:
                try:
                    charge = reponse.json()
                except Exception:
                    charge = None
                return {"existe": True,
                        "titre_fr": self._titre_fr(charge),
                        "concepts": self._concepts(charge)}
            return None
        return None

    def url_verifiee(self, intitule: Any) -> Optional[str]:
        """L'adresse du document cité par cet intitulé, si et seulement si il existe.

        `None` dans les trois cas où rien ne peut être publié : aucune référence
        citée, document introuvable, ou question non posée. Les trois se
        comptent séparément chez l'appelant — ils ne disent pas la même chose.
        """
        doceo = reference_doceo(intitule)
        if doceo is None:
            return None
        return url_doceo(doceo) if self.existe(doceo) else None

    @property
    def disjoncte(self) -> bool:
        """Vrai quand la passe a cessé d'interroger le portail (#901)."""
        return self._disjoncte

    @property
    def statistiques(self) -> dict[str, Any]:
        return {
            "documents_connus": len(self._cache),
            "requetes": self._interroges,
            "refus_429": self._refuses,
            "echecs_consecutifs": self._echecs_consecutifs,
            # Publié même à False : un appelant qui ne lit que les compteurs ne
            # verrait pas qu'une passe s'est arrêtée en route, et lirait une
            # couverture faible comme un fait sur la source.
            "disjoncte": self._disjoncte,
        }


def resolveur_par_defaut(hors_ligne: bool = False) -> ResolveurDocuments:
    """Le résolveur du pipeline : cache du dépôt, session `requests` réelle."""
    return ResolveurDocuments(
        session=None if hors_ligne else requests.Session(),
        hors_ligne=hors_ligne,
    )
