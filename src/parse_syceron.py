#!/usr/bin/env python3
"""
parse_syceron.py — Parseur XML Syceron (comptes rendus de séance AN).

Extrait les interventions, la date, le numéro de séance, l'orateur, le texte
et les signaux de contexte (titre de point/thème) depuis les fichiers XML
produits par le système Syceron de l'Assemblée nationale.

Format source :
    ZIP par législature disponible sur data.assemblee-nationale.fr
    (voir docs/sources/an-opendata.md, section Syceron, pour URLs et structure détaillée).

Usage :
    from parse_syceron import parse_syceron_xml

    with open("CRSANR5L17S2025O1N037.xml", "rb") as f:
        result = parse_syceron_xml(f.read())

    result["seance"]         # métadonnées de la séance
    result["interventions"]  # liste d'interventions (format compatible pivot)

Principes :
    - Champs manquants → None (jamais "" ni 0).
    - Pas d'appel réseau, pas de dépendance externe (xml.etree uniquement).
    - Robuste aux fichiers incomplets ou provisoires.
"""

import re
import xml.etree.ElementTree as ET
from typing import Any, Optional, Union

# Namespace XML des fichiers Syceron AN.
_NS = "http://schemas.assemblee-nationale.fr/referentiel"
_NSP = f"{{{_NS}}}"

# Seuil (en mots) pour distinguer une réaction courte d'une prise développée.
_FORMAT_SEUIL_MOTS = 50

# Préfixes de type_detail inférés depuis le titre de point.
_TYPE_DETAIL_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"question.*gouvernement", re.I), "question_gouvernement"),
    (re.compile(r"question.*orale", re.I), "question_orale"),
    (re.compile(r"question", re.I), "question"),
    (re.compile(r"motion de censure", re.I), "motion_censure"),
    (re.compile(r"explication.*vote", re.I), "explication_vote"),
    (re.compile(r"projet de loi|proposition de loi|PLFSS|PLF", re.I), "loi"),
]

# `code_grammaire` des `<point>` dont le TITRE porte le sujet du débat (#510).
#
# La hiérarchie des points est décrite par deux mécanismes que la source emploie
# ensemble, et c'est la raison pour laquelle le parcours ci-dessous n'est ni un
# simple `findall` ni une simple récursion :
#
#   - l'attribut `nivpoint` (1, 2, 3) désigne les niveaux du sommaire, et ces
#     points-là sont des FRÈRES en XML, pas des descendants — mesuré sur la 17e :
#     1 749 + 5 085 + 4 831 points, tous à la profondeur XML 1, tous titrés ;
#   - l'imbrication XML porte les niveaux 4 et 5 (16 300 + 1 347 points sur la
#     17e, profondeur 2 à 9), qui ne sont JAMAIS titrés : ce sont les points
#     d'amendement, et ils héritent du titre de leur ancêtre.
#
# Un paragraphe de niveau 4 ne se rattache donc à son sujet ni par ses ancêtres
# XML seuls ni par `nivpoint` seul. Il faut une pile de titres alimentée en ordre
# de document, à laquelle l'imbrication XML se superpose.
#
# Le titre du point le plus proche n'est pas pour autant un thème : mesurés sur
# la 17e, les plus fréquents sont « suspension et reprise de la séance » (1 009),
# « rappel au règlement » (788), « ordre du jour de la prochaine séance » (594),
# « article 1er » (155) — de la PROCÉDURE. Publier cela dans `sujet`, d'où
# `normalize_profil` dérive `theme_officiel` puis `tags_thematiques`,
# fabriquerait des tags thématiques à partir d'intitulés de procédure (§2 règle 8).
#
# Le discriminant est structurel, pas lexical : c'est le `code_grammaire` du
# point, vocabulaire contrôlé de la source. Mesuré sur les 30 322 points de la
# 17e législature, seuls trois codes portent un titre de matière —
# `TITRE_TEXTE_DISCUSSION` (1 093 : « droit à l'aide à mourir », « projet de loi
# de finances pour 2026 »), `QG_1_1` (1 804 : « crise agricole », « prix des
# carburants ») et `QOSD_1_1` (815 : « permis de conduire », « zéro
# artificialisation nette »). Tous les autres codes titrés sont procéduraux :
# `DISC_ARTICLES_*`, `SUSP_SEANCE_1_1`, `RAP_REGLEMENT_1_1`, `DISC_GENERALE_1`,
# `PRESENTATION_1_0`, `VOTE_ENS_*`, `FIN_SEAN_1_2`, `SOUS_TITRE_TEXTE_DISCUSSION`.
#
# Le `<sommaire>` de `<metadonnees>` n'apporte rien de plus, contrairement à ce
# que supposait #510 : mesuré sur la 17e, l'`<intitule>` du sommaire est
# rigoureusement le `<point><texte>` du point qu'il référence sur **12 035 des
# 12 038** jointures par `id_syceron`. Il n'est donc pas lu.
#
# **Mais `TITRE_TEXTE_DISCUSSION` n'est pas homogène (#710).** C'est le titre du
# POINT D'ORDRE DU JOUR, et l'ordre du jour inscrit tantôt un texte — « Droit à
# l'aide à mourir » —, tantôt un CRÉNEAU de séance : « Questions au
# gouvernement », « Questions orales sans débat », « Questions au Premier
# ministre ». Le créneau n'est pas un sujet, et le publier dans `sujet` fabrique
# un faux thème (§2 règle 8) — mesuré sur les 481 profils publiés le 02/09/2026 :
# 69 d'entre eux portaient le tag « questions au premier ministre ».
#
# Le discriminant reste STRUCTUREL : un point d'ordre du jour sous lequel la
# source range des points de la grammaire des questions
# (`_CODE_GRAMMAIRE_QUESTION`) est un créneau — c'est la source elle-même qui
# dit que le sujet vit un cran plus bas. Voir `_creneaux_de_questions`.
#
# **Aucune liste de libellés**, et ce n'est pas une précaution de style : la
# source publie « Questions au gouvernement », « Questions au Gouvernement »,
# « Questions au premier ministre » et « Questions au Gouvernement (suite) » —
# quatre variantes du même créneau sur les seules législatures 16 et 17. Un
# filtre lexical en manquerait trois ; le critère structurel les prend toutes,
# sans en connaître aucune. C'est le défaut de #672 (sélection par sous-chaîne)
# et celui de #639 (clé tirée d'un libellé, qui rouille en silence).
#
# **Ce que ce critère NE tranche pas, et il faut le dire** : un point d'ordre du
# jour qui est un moment de séance SANS grammaire plus fine en dessous. « Motion
# de censure » (32 points, 11 665 paragraphes sur les législatures 16-17) et
# « Déclaration du Gouvernement et débat » en sont ; la source ne porte, pour
# eux, aucune marque structurelle — ni `@valeur` (1 335 des 2 138 points titrés
# la remplissent, textes et créneaux confondus), ni `<sommaire><sousIntitule>`
# (« 0 » sur les 2 138). Ils restent publiés, et c'est un trou déclaré, pas un
# trou comblé par un libellé (§2 règle 5).
#
# **Et un code absent ou inconnu ne devient jamais procédural par défaut** : le
# critère est POSITIF des deux côtés — un point ne porte un sujet que si son code
# est dans `_CODE_GRAMMAIRE_SUJET`, et n'est écarté que si la source range sous
# lui des points de question. Un code qu'on ne connaît pas ne fait donc ni l'un
# ni l'autre.
_CODE_GRAMMAIRE_SUJET = frozenset({
    "TITRE_TEXTE_DISCUSSION",   # texte inscrit à l'ordre du jour
    "QG_1_1",                   # question au Gouvernement
    "QOSD_1_1",                 # question orale sans débat
    "QPM_1_1",                  # question au Premier ministre (#710)
})

# Grammaire des QUESTIONS : ces points portent le sujet d'UNE question, et la
# source les range sous un point d'ordre du jour qui, lui, nomme le créneau
# (#710). `QPM_1_1` manquait au jeu ci-dessus : 35 points sur les législatures
# 16 et 17, 629 paragraphes qui héritaient donc de « Questions au Premier
# ministre » au lieu de « Parcoursup ».
_CODE_GRAMMAIRE_QUESTION = frozenset({
    "QG_1_1",
    "QOSD_1_1",
    "QPM_1_1",
})

# `type_detail` déduit du `code_grammaire` plutôt que d'une regex sur le titre :
# le code est un vocabulaire contrôlé de la source, le titre est de la prose.
_TYPE_DETAIL_PAR_CODE_GRAMMAIRE: dict[str, str] = {
    "QG_1_1": "question_gouvernement",
    "QOSD_1_1": "question_orale",
    "QPM_1_1": "question_gouvernement",
}

# Sous-arbres dans lesquels le parcours ne descend pas : `<ouvertureSeance>` et
# `<finSeance>` par contrat historique (hors périmètre des interventions), les
# deux autres parce qu'ils ne peuvent contenir aucun `<paragraphe>` et que les
# traverser coûterait un parcours de tout le texte des débats.
_TAGS_IGNORES = frozenset({
    f"{_NSP}ouvertureSeance",
    f"{_NSP}finSeance",
    f"{_NSP}texte",
    f"{_NSP}orateurs",
})


def _tag(local: str) -> str:
    """Retourne le nom de tag qualifié avec le namespace Syceron."""
    return f"{_NSP}{local}"


def _text(element: Optional[ET.Element], path: str) -> Optional[str]:
    """Retourne le texte d'un sous-élément, ou None si absent/vide."""
    if element is None:
        return None
    found = element.find(path)
    if found is None or not (found.text or "").strip():
        return None
    return found.text.strip()


def _a_un_texte(paragraphe: ET.Element) -> bool:
    """Le `<paragraphe>` porte-t-il un `<texte>` ? (#657)

    Test de PRÉSENCE, pas d'extraction : c'est la seule chose dont la condition
    de rétention de `_parse_interventions` ait besoin, et `_extract_texte` — qui
    sérialise l'arbre puis applique deux `re.sub` — pèse 53,8 % du parcours
    (mesuré sur la 17e législature, 601 comptes rendus). En mode `avec_texte=
    False` la rétention passe donc par ici.

    L'écart avec `_extract_texte(...) is not None` est un `<texte/>` vide, que ce
    test retient et que l'extraction rejetait : un tel paragraphe n'a ni orateur
    ni contenu, il est écarté à l'indexation faute d'`acteurRef` — l'index sort
    identique dans les deux modes, et `tests/test_parse_syceron_theme_seul.py`
    le vérifie sur l'archive réelle plutôt que de le supposer.
    """
    return paragraphe.find(_tag("texte")) is not None


def _extract_texte(paragraphe: ET.Element) -> Optional[str]:
    """Extrait le texte d'un <paragraphe> en normalisant les balises inline.

    Balises inline gérées :
    - <br/> et ses variantes avec namespace (ex. <ns0:br/>) → espace
    - <italique>, <sup>, etc. → contenu texte conservé, balise supprimée
    """
    texte_el = paragraphe.find(_tag("texte"))
    if texte_el is None:
        return None
    # Sérialise l'arbre sous-jacent avec les éventuels préfixes de namespace.
    raw = ET.tostring(texte_el, encoding="unicode", method="xml")
    # Remplace toutes les variantes de <br> (avec ou sans préfixe namespace) par un espace.
    raw = re.sub(r"<[^>]*\bbr\b[^>]*/?>", " ", raw)
    # Retire toutes les balises restantes (dont l'élément racine texte lui-même).
    text = re.sub(r"<[^>]+>", "", raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def _titre_point(point: ET.Element) -> Optional[str]:
    """Titre d'un `<point>`, lu dans son `<texte>` enfant direct (#510).

    C'est là que la source le publie — et nulle part ailleurs : `<titreStruct>`
    sous `<contenu>` compte **0 occurrence** sur les 162 073 points des trois
    législatures Syceron (15, 16, 17), alors que le parseur le lisait là.

    `find` ne regarde que les enfants directs : le `<texte>` d'un point imbriqué
    ne peut donc pas être pris pour celui de son parent.
    """
    texte = point.find(_tag("texte"))
    if texte is None:
        return None
    titre = " ".join("".join(texte.itertext()).split())
    return titre or None


def _niveau_point(point: ET.Element) -> Optional[int]:
    """Niveau de sommaire déclaré par l'attribut `nivpoint`, ou `None` s'il est
    absent ou non numérique — auquel cas seule l'imbrication XML fait foi."""
    try:
        return int(point.get("nivpoint"))
    except (TypeError, ValueError):
        return None


def _creneaux_de_questions(element: ET.Element) -> frozenset[str]:
    """`id_syceron` des points d'ordre du jour que la source déclare créneau de
    questions (#710).

    Un `TITRE_TEXTE_DISCUSSION` sous lequel la source range des points de
    `_CODE_GRAMMAIRE_QUESTION` nomme le CRÉNEAU, pas le sujet : c'est la source
    elle-même qui publie le sujet un cran plus bas, un par question. Son titre ne
    doit donc jamais devenir un `sujet` — il reste lisible dans
    `point_ordre_du_jour`, qui est du contexte, pas un thème.

    La passe est séparée de `_iter_paragraphes` parce qu'elle doit AVOIR LIEU
    AVANT lui : les points de question sont des FRÈRES XML du point d'ordre du
    jour (`nivpoint` 2 contre 1), donc ils viennent APRÈS lui en ordre de
    document — un parcours en une passe aurait déjà émis les paragraphes du
    créneau quand il les découvre. Elle applique exactement la même discipline de
    pile que `_iter_paragraphes`, pour que « sous » veuille dire la même chose des
    deux côtés.

    Mesuré sur les archives 16 et 17 : 279 points d'ordre du jour sur 2 138
    titrés, portant quatre variantes typographiques du même créneau — le critère
    n'en connaît aucune.

    Son coût est mesuré, pas supposé : **+3,3 %** du parcours complet sur
    60 comptes rendus de la XVIIe (0,120 s ajoutées à 3,66 s). Elle ne descend ni
    dans les `<paragraphe>` ni dans les `<texte>`, qui portent tout le volume.
    """
    creneaux: set[str] = set()

    def _descendre(courant: list[tuple[Optional[int], Optional[str], Optional[str]]], noeud: ET.Element) -> None:
        pile = list(courant)
        for enfant in noeud:
            if enfant.tag in _TAGS_IGNORES or enfant.tag == _tag("paragraphe"):
                continue
            if enfant.tag == _tag("point"):
                if _titre_point(enfant):
                    niveau = _niveau_point(enfant)
                    if niveau is not None:
                        while pile and pile[-1][0] is not None and pile[-1][0] >= niveau:
                            pile.pop()
                    pile.append((niveau, enfant.get("code_grammaire"), enfant.get("id_syceron")))
                    if enfant.get("code_grammaire") in _CODE_GRAMMAIRE_QUESTION:
                        for _niv, code, id_syceron in reversed(pile[:-1]):
                            if code == "TITRE_TEXTE_DISCUSSION" and id_syceron:
                                creneaux.add(id_syceron)
                                break
            _descendre(pile, enfant)

    _descendre([], element)
    return frozenset(creneaux)


def _point_porteur_du_sujet(
    chaine: tuple[tuple[Optional[int], Optional[str], str, Optional[str]], ...],
    creneaux: frozenset[str],
) -> tuple[Optional[str], Optional[str]]:
    """`(sujet, code_grammaire du point qui le porte)`, ou `(None, None)`.

    `None` est un résultat, pas un défaut : un paragraphe prononcé sous « article
    1er » n'a pas de sujet publié par la source, et lui en inventer un depuis
    l'intitulé de procédure alimenterait `tags_thematiques` de faux thèmes
    (§2 règle 5 et règle 8). Depuis #710, un point d'ordre du jour déclaré
    créneau de questions est sauté pour la même raison : il nomme un moment de
    séance.

    Le code est rendu à côté du titre parce que c'est LUI le fait sourcé — le
    vocabulaire contrôlé de l'Assemblée. Il voyage jusqu'au profil brut, où
    `merge_profile.backfill_sujet_seance` en fait le critère du report sur les
    entrées déjà collectées.
    """
    for _niveau, code_grammaire, titre, id_syceron in reversed(chaine):
        if code_grammaire not in _CODE_GRAMMAIRE_SUJET:
            continue
        if code_grammaire == "TITRE_TEXTE_DISCUSSION" and id_syceron in creneaux:
            continue
        return titre, code_grammaire
    return None, None


def _infer_type_detail(chaine: tuple[tuple[Optional[int], Optional[str], str, Optional[str]], ...]) -> str:
    """Infère le `type_detail` depuis la chaîne des points englobants.

    Le `code_grammaire` prime — vocabulaire contrôlé de la source — et la regex
    sur les titres ne sert que de repli, du point le plus profond au plus haut.
    """
    for _niveau, code_grammaire, _titre, _id in reversed(chaine):
        type_detail = _TYPE_DETAIL_PAR_CODE_GRAMMAIRE.get(code_grammaire or "")
        if type_detail:
            return type_detail
    for _niveau, _code_grammaire, titre, _id in reversed(chaine):
        for pattern, type_detail in _TYPE_DETAIL_MAP:
            if pattern.search(titre):
                return type_detail
    return "debat"


def _infer_format(texte: Optional[str]) -> str:
    """Déduit le format d'une intervention depuis son volume."""
    if not texte:
        return "reaction_courte"
    nb_mots = len(texte.split())
    return "reaction_courte" if nb_mots < _FORMAT_SEUIL_MOTS else "prise_de_parole_developpee"


def _parse_date_seance(raw: Optional[str]) -> Optional[str]:
    """Convertit le format compact Syceron (YYYYMMDD...) en date ISO YYYY-MM-DD."""
    if not raw or len(raw) < 8:
        return None
    return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"


def _parse_metadonnees(root: ET.Element) -> dict[str, Any]:
    """Extrait les métadonnées de séance depuis <metadonnees>."""
    meta = root.find(_tag("metadonnees"))

    def m(local: str) -> Optional[str]:
        return _text(meta, _tag(local)) if meta is not None else None

    date_raw = m("dateSeance")
    return {
        "uid": (_text(root, _tag("uid"))),
        "seance_ref": (_text(root, _tag("seanceRef"))),
        "session_ref": (_text(root, _tag("sessionRef"))),
        "date": _parse_date_seance(date_raw),
        "legislature": m("legislature"),
        "numero_seance": m("numSeance"),
        "etat": m("etat"),
        "version": m("version"),
    }


def _parse_orateur(paragraphe: ET.Element) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extrait (id_source, nom, qualite) de l'orateur du paragraphe.

    Retourne (None, None, None) si aucun orateur n'est renseigné, ou si
    plusieurs orateurs distincts sont présents dans le même paragraphe
    (correspondance ambiguë : on préfère ne rien attribuer).
    """
    orateurs_el = paragraphe.find(_tag("orateurs"))
    if orateurs_el is None:
        return None, None, None

    orateurs = []
    for orateur_el in orateurs_el.findall(_tag("orateur")):
        oid = _text(orateur_el, _tag("id"))
        nom = _text(orateur_el, _tag("nom"))
        qualite = _text(orateur_el, _tag("qualite"))
        if oid or nom:
            orateurs.append((oid, nom, qualite))

    if not orateurs:
        return None, None, None

    distincts = {(oid, nom) for oid, nom, _ in orateurs}
    if len(distincts) > 1:
        return None, None, None

    oid, nom, qualite = orateurs[0]
    return oid, nom, qualite


def _iter_paragraphes(
    element: ET.Element,
    chaine: tuple[tuple[Optional[int], Optional[str], str, Optional[str]], ...],
    dans_point: bool = False,
):
    """Parcourt les `<paragraphe>` sous les `<point>`, à TOUTE profondeur (#510).

    Rend `(paragraphe, chaine)`, où `chaine` est la suite des points englobants
    du plus haut au plus profond, sous forme
    `(nivpoint, code_grammaire, titre, id_syceron)`. L'`id_syceron` est le seul
    ajout de #710 : c'est ce qui permet à `_point_porteur_du_sujet` de
    reconnaître un point d'ordre du jour que `_creneaux_de_questions` a déclaré
    créneau, sans jamais regarder son libellé.

    Le parcours d'origine était `contenu.findall("point")` puis
    `point.findall("paragraphe")` — deux niveaux, en enfants directs. Mesuré sur
    les trois archives, il ne voyait que **180 755 des 1 444 564** paragraphes
    (12,5 %) : 29 194 / 788 095 sur la 15e, 41 933 / 335 800 sur la 16e,
    109 628 / 320 669 sur la 17e. Les deux tiers à sept huitièmes du débat
    étaient donc invisibles, pour la même raison que #510 lui-même : la fixture
    sur laquelle le parseur avait été validé ne décrivait pas la source.

    La pile de titres se dépile sur `nivpoint` — les points de niveau 1 à 3 sont
    des frères en XML — et se transmet par l'imbrication pour les niveaux 4 et 5.
    Un point sans titre (les 17 647 points de niveau 4 et 5 de la 17e) n'empile
    rien : ses paragraphes gardent le titre de l'ancêtre.

    Les `<paragraphe>` ne sont pas non plus tous enfants d'un `<point>` : la
    source les regroupe dans des conteneurs intermédiaires — `<interExtraction>`
    (un échange rattaché à un orateur) porte **86 163 des 103 213** paragraphes
    d'un échantillon de 200 comptes rendus de la 15e législature, et
    `<changementPresidence>` en porte d'autres. Ces conteneurs n'ont pas de
    titre : on les traverse sans rien empiler.

    `<ouvertureSeance>` et `<finSeance>` restent ignorés, et le périmètre reste
    « sous un `<point>` » : ce parcours corrige la profondeur atteinte, il
    n'élargit pas la portion du compte rendu retenue.
    """
    courant = list(chaine)
    for enfant in element:
        if enfant.tag in _TAGS_IGNORES:
            continue
        if enfant.tag == _tag("point"):
            titre = _titre_point(enfant)
            if titre:
                niveau = _niveau_point(enfant)
                if niveau is not None:
                    while courant and courant[-1][0] is not None and courant[-1][0] >= niveau:
                        courant.pop()
                courant.append((niveau, enfant.get("code_grammaire"), titre, enfant.get("id_syceron")))
            yield from _iter_paragraphes(enfant, tuple(courant), True)
        elif enfant.tag == _tag("paragraphe"):
            if dans_point:
                yield enfant, tuple(courant)
        elif dans_point:
            # Conteneur intermédiaire SANS titre à l'intérieur d'un point
            # (`<interExtraction>`, `<changementPresidence>`…) : traversé.
            yield from _iter_paragraphes(enfant, tuple(courant), True)


def _parse_interventions(
    root: ET.Element,
    seance: dict[str, Any],
    *,
    avec_texte: bool = True,
) -> list[dict[str, Any]]:
    """Extrait toutes les interventions (paragraphes avec orateur+texte) du contenu.

    Un paragraphe est retenu comme intervention dès qu'il possède au moins un
    orateur identifié (id ou nom) ou un texte non-vide.  Les éléments
    <ouvertureSeance> et <finSeance> sont ignorés.

    Clé de déduplication recommandée pour les consommateurs :
        source_id + index(point) + index(paragraphe) + orateur_id_source

    `avec_texte=False` (#657) : le verbatim n'est pas extrait. `texte` sort
    `None`, et `format` AUSSI — il se déduit du nombre de mots du verbatim, donc
    sans lui la valeur « reaction_courte » serait un défaut déguisé en mesure
    (AGENTS.md §2 règle 5). Tout le reste est identique : `sujet` et
    `type_detail` viennent du titre de point (`_titre_point`), jamais du texte,
    donc la matière thématique est intacte — c'est la propriété qui rend le mode
    utilisable pour les 468 membres de roster.
    """
    contenu = root.find(_tag("contenu"))
    if contenu is None:
        return []

    date_seance = seance.get("date")
    uid = seance.get("uid")
    seance_ref = seance.get("seance_ref")
    session_ref = seance.get("session_ref")
    etat = seance.get("etat")
    version = seance.get("version")

    interventions: list[dict[str, Any]] = []

    # #710 — passe préalable : quels points d'ordre du jour la source déclare-t-elle
    # créneaux de questions ? Elle doit précéder le parcours des paragraphes.
    creneaux = _creneaux_de_questions(contenu)

    for paragraphe, chaine in _iter_paragraphes(contenu, ()):
        texte = _extract_texte(paragraphe) if avec_texte else None
        oid, nom_orateur, qualite = _parse_orateur(paragraphe)

        # On retient le paragraphe s'il a un orateur identifié ou un texte.
        # Sans extraction (#657), la présence du `<texte>` tient lieu de test.
        a_du_texte = bool(texte) if avec_texte else _a_un_texte(paragraphe)
        if not oid and not nom_orateur and not a_du_texte:
            continue

        chemin = " > ".join(titre for _niveau, _code, titre, _id in chaine) or None
        sujet, sujet_code_grammaire = _point_porteur_du_sujet(chaine, creneaux)
        interventions.append({
            # Champs compatibles avec le format pivot interventions[]
            "date": date_seance,
            "type_detail": _infer_type_detail(chaine),
            "sujet": sujet,
            # #710 — le code du point qui a fourni le sujet, ou `None`. C'est le
            # fait sourcé derrière `sujet`, et le critère que lit le report
            # `merge_profile.backfill_sujet_seance` : sa PRÉSENCE, fût-elle à
            # `None`, prouve que l'entrée est sortie du parseur corrigé.
            "sujet_code_grammaire": sujet_code_grammaire,
            "texte": texte,
            "fonction": qualite,
            "format": _infer_format(texte) if avec_texte else None,
            "mots_cles": [],
            "source_url": None,
            # Champs contextuels Syceron (traçabilité et audit qualité)
            "source_id": uid,
            "seance_ref": seance_ref,
            "session_ref": session_ref,
            "orateur_id_source": oid,
            # Attribution que la source porte elle-même, en attribut du
            # `<paragraphe>`, à côté de l'identifiant nu de `<orateur><id>`.
            # C'est la preuve du préfixage de #510 — et, quand les deux se
            # contredisent, le refus d'attribution de la source elle-même.
            "orateur_id_acteur": paragraphe.get("id_acteur") or None,
            "orateur_nom": nom_orateur,
            "point_ordre_du_jour": chemin,
            "point_code_grammaire": (chaine[-1][1] if chaine else None),
            "etat_compte_rendu": etat,
            "version_compte_rendu": version,
        })

    return interventions


def parse_syceron_xml(
    xml_content: Union[str, bytes], *, avec_texte: bool = True
) -> dict[str, Any]:
    """Parse un fichier XML Syceron et retourne séance + interventions.

    Args:
        xml_content: contenu XML brut (str ou bytes).
        avec_texte: `False` pour ne pas extraire le verbatim (#657). `texte` et
            `format` sortent alors `None` ; l'arbre XML est construit de toute
            façon (la source n'offre aucune lecture par champ), mais les deux
            `re.sub` par paragraphe d'`_extract_texte` — 53,8 % du parcours —
            ne sont pas payés. Le reste de la sortie est inchangé.

    Returns:
        {
            "seance": {
                "uid": str | None,
                "seance_ref": str | None,
                "session_ref": str | None,
                "date": str | None,          # YYYY-MM-DD
                "legislature": str | None,
                "numero_seance": str | None,
                "etat": str | None,          # "complet" | "provisoire"
                "version": str | None,       # "JO" | "avant_JO"
            },
            "interventions": [
                {
                    # Champs pivot interventions[]
                    "date": str | None,
                    "type_detail": str,
                    "sujet": str | None,
                    "sujet_code_grammaire": str | None,
                    "texte": str | None,     # None si avec_texte=False (#657)
                    "fonction": str | None,
                    "format": str | None,    # "reaction_courte" | "prise_de_parole_developpee"
                                             # None si avec_texte=False (#657)
                    "mots_cles": list,
                    "source_url": None,
                    # Champs contextuels Syceron
                    "source_id": str | None,
                    "seance_ref": str | None,
                    "session_ref": str | None,
                    "orateur_id_source": str | None,   # NU, tel que publié
                    "orateur_id_acteur": str | None,   # attribut id_acteur du paragraphe
                    "orateur_nom": str | None,
                    "point_ordre_du_jour": str | None, # chaîne des titres, " > "
                    "point_code_grammaire": str | None,
                    "etat_compte_rendu": str | None,
                    "version_compte_rendu": str | None,
                },
                ...
            ],
        }

    Raises:
        ET.ParseError: si le XML est malformé (pas intercepté — l'appelant décide).
    """
    if isinstance(xml_content, str):
        xml_content = xml_content.encode("utf-8")

    root = ET.fromstring(xml_content)

    seance = _parse_metadonnees(root)
    interventions = _parse_interventions(root, seance, avec_texte=avec_texte)

    return {"seance": seance, "interventions": interventions}
